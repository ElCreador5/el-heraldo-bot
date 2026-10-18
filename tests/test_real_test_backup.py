"""Offline failure/concurrency checks; real service evidence is documented separately."""
import asyncio
from contextlib import closing, redirect_stdout
from datetime import datetime, timezone
from io import StringIO
import json
import os
from pathlib import Path
import shutil
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

import backup_job as job
import supabase_backup as cloud
import test_backup_runtime as runtime
import test_backup_scheduler as scheduler
from sqlite_recovery import validate_backup


class RealTestBackupTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.db, self.state = self.root / 'live.sqlite', self.root / 'state'
        self.conn = sqlite3.connect(self.db)
        self.addCleanup(self.conn.close)
        self.conn.execute('PRAGMA journal_mode=WAL')
        self.conn.executescript('CREATE TABLE parent(id INTEGER PRIMARY KEY);'
                               'CREATE TABLE child(id INTEGER REFERENCES parent(id), value TEXT);'
                               "INSERT INTO parent VALUES(1); INSERT INTO child VALUES(1,'committed');")
        self.day = datetime(2026, 10, 18, 10, tzinfo=timezone.utc)
        self.env = {'RAILWAY_GIT_COMMIT_SHA': 'a'*40}
        patch.dict(os.environ, self.env).start()
        patch.object(job, '_test_volume').start()
        patch.object(runtime, 'TEST_STATE_DIR', self.state).start()
        self.addCleanup(patch.stopall)
        self.objects = {}
        self.encryption_key = os.urandom(32)

    def upload(self, package, environment, *, object_name):
        # Assert the reference survives even if the HTTP response is lost.
        receipt = json.loads((self.state / 'heraldo-test-20261018.json').read_text())
        self.assertEqual(receipt['object'], object_name)
        self.assertEqual(receipt['status'], 'upload_unconfirmed')
        self.assertNotIn(object_name, self.objects)
        blob, manifest = cloud._bundle(package, environment, self.encryption_key)
        self.objects[object_name] = blob
        return {'object': object_name, 'plaintext_sha256': manifest['sha256']}

    def download(self, name, environment, destination):
        with cloud._unpack(self.objects[name], environment, self.encryption_key) as package:
            target = Path(destination) / 'package'
            shutil.copytree(package, target)
            return {'local_package': str(target),
                    'plaintext_sha256': validate_backup(target, environment=environment)['sha256']}

    def run_backup(self):
        return job.run_once(self.db, self.state, environment='heraldo-test', revision='a'*40, now=self.day)

    def test_open_wal_and_uncommitted_writer_roundtrip(self):
        self.conn.execute("INSERT INTO child VALUES(1,'uncommitted')")
        with patch.object(job, 'upload', side_effect=self.upload), patch.object(job, 'download_verify', side_effect=self.download):
            self.assertEqual(self.run_backup(), 'verified_and_restored')
        restored = self.state / 'heraldo-test-20261018/restored.sqlite'
        with closing(sqlite3.connect(restored)) as db:
            self.assertEqual(db.execute('SELECT value FROM child').fetchall(), [('committed',)])
        self.assertEqual(self.conn.execute('SELECT count(*) FROM child').fetchone()[0], 2)
        self.conn.rollback()

    def test_lost_upload_response_recovers_without_reupload(self):
        def lose_response(*args, **kwargs):
            self.upload(*args, **kwargs)
            raise TimeoutError('PRIVATE_PROVIDER_DETAIL')
        with patch.object(job, 'upload', side_effect=lose_response) as uploader:
            with self.assertRaises(TimeoutError): self.run_backup()
            with self.assertRaisesRegex(job.BackupJobError, 'previous_attempt_needs_review'): self.run_backup()
        self.assertEqual(uploader.call_count, 1)
        with patch.object(runtime, 'download_verify', side_effect=self.download), patch.object(job, 'upload') as uploader:
            self.assertEqual(runtime.recover_day(self.db, '20261018'), 'verified_and_restored')
            uploader.assert_not_called()
        self.assertFalse(list(self.state.glob('recovery-*')))
        self.assertEqual(job.receipt_status(self.state / 'heraldo-test-20261018.json'), 'verified_and_restored')

    def test_uncertain_previous_day_blocks_new_generation(self):
        self.state.mkdir(mode=0o700)
        job._write_receipt(self.state / 'heraldo-test-20261017.json', {'status': 'needs_manual_review'}, initial=True)
        with patch.object(job, 'upload') as uploader:
            with self.assertRaisesRegex(job.BackupJobError, 'previous_attempt_needs_review'): self.run_backup()
        uploader.assert_not_called()

    def test_ciphertext_tampering_prevents_recovery_receipt(self):
        with patch.object(job, 'upload', side_effect=self.upload), patch.object(job, 'download_verify', side_effect=self.download):
            self.run_backup()
        name = next(iter(self.objects)); original = self.objects[name]
        self.objects[name] = original[:-1] + bytes([original[-1] ^ 1])
        receipt = self.state / 'heraldo-test-20261018.json'; before = receipt.read_bytes()
        with patch.object(runtime, 'download_verify', side_effect=self.download):
            with self.assertRaises(cloud.CloudBackupError): runtime.recover_day(self.db, '20261018')
        self.assertEqual(receipt.read_bytes(), before)

    def test_historical_recovery_keeps_newer_live_writes(self):
        with patch.object(job, 'upload', side_effect=self.upload), patch.object(job, 'download_verify', side_effect=self.download):
            self.run_backup()
        self.conn.execute("INSERT INTO child VALUES(1,'newer-live-data')"); self.conn.commit()
        with patch.object(runtime, 'download_verify', side_effect=self.download):
            runtime.recover_day(self.db, '20261018')
        self.assertEqual(self.conn.execute('SELECT count(*) FROM child').fetchone()[0], 2)
        self.assertEqual(len(self.objects), 1)

    def test_wrong_revision_rejected_before_creation(self):
        with self.assertRaisesRegex(job.BackupJobError, 'source_revision_mismatch'):
            job.run_once(self.db, self.state, environment='heraldo-test', revision='b'*40)
        self.assertFalse(self.state.exists())

    def test_simultaneous_job_blocked(self):
        self.state.mkdir(mode=0o700)
        with job._exclusive_job_lock(self.state):
            with self.assertRaisesRegex(job.BackupJobError, 'job_already_running'): self.run_backup()

    def test_active_restore_target_never_overwritten(self):
        with self.assertRaisesRegex(job.BackupJobError, 'restore_target_exists'):
            job._isolated_restore(self.root, self.db, {})
        self.assertEqual(self.conn.execute('SELECT count(*) FROM child').fetchone()[0], 1)

    def test_recovery_rejects_path_traversal(self):
        with self.assertRaisesRegex(job.BackupJobError, 'invalid_generation_day'):
            runtime.recover_day(self.db, '../20261018')

    def test_existing_day_deduplicated_without_upload(self):
        with patch.object(job, 'upload', side_effect=self.upload) as uploader, patch.object(job, 'download_verify', side_effect=self.download):
            self.run_backup()
            self.assertEqual(runtime.run_due(self.db, 'a'*40, self.day), 'already_verified')
        self.assertEqual(uploader.call_count, 1)

    def test_catchup_before_and_after_daily_cutoff(self):
        with patch.object(runtime, 'run_once', return_value='verified_and_restored') as run:
            self.assertEqual(runtime.run_due(self.db, 'a'*40, self.day.replace(hour=1)), 'verified_and_restored')
            self.state.mkdir(mode=0o700)
            job._write_receipt(self.state / 'heraldo-test-20261017.json', {'status':'verified_and_restored'}, initial=True)
            self.assertEqual(runtime.run_due(self.db, 'a'*40, self.day.replace(hour=1)), 'waiting')
            self.assertEqual(runtime.run_due(self.db, 'a'*40, self.day), 'verified_and_restored')
        self.assertEqual(run.call_count, 2)


class TestIsolationTests(unittest.TestCase):
    def test_test_storage_uses_different_bucket(self):
        with patch.object(cloud, '_config', return_value=('https://x.supabase.co','pub','email','password','id')), patch.object(cloud, '_session', return_value={}):
            test, _ = cloud._storage('heraldo-test')
            prod, _ = cloud._storage('heraldo-production')
            lab, _ = cloud._storage('lab')
        self.assertNotEqual(test, prod)
        self.assertEqual(lab, prod)

    def test_wrong_service_rejected(self):
        for identity in (job.PRODUCTION_IDS, (job.TEST_IDS[0],job.TEST_IDS[1],'cron')):
            with patch.dict(os.environ, dict(zip(('RAILWAY_PROJECT_ID','RAILWAY_ENVIRONMENT_ID','RAILWAY_SERVICE_ID'),identity)), clear=True):
                with self.assertRaisesRegex(job.BackupJobError, 'test_not_authorized'):
                    job._test_volume(Path('/data/live.db'),job.TEST_STATE_DIR)

    def test_fake_mount_rejected(self):
        env=dict(zip(('RAILWAY_PROJECT_ID','RAILWAY_ENVIRONMENT_ID','RAILWAY_SERVICE_ID'),job.TEST_IDS))
        env.update(HERALDO_TEST_BACKUP_ENABLED='enabled',RAILWAY_VOLUME_NAME='worker-volume',RAILWAY_VOLUME_MOUNT_PATH='/data')
        with patch.dict(os.environ,env,clear=True),patch.object(Path,'is_mount',return_value=False):
            with self.assertRaisesRegex(job.BackupJobError,'test_volume_mismatch'):
                job._test_volume(Path('/data/live.db'),job.TEST_STATE_DIR)

    def test_disabled_scheduler_has_no_side_effect(self):
        with patch.dict(os.environ,{},clear=True),patch.object(scheduler._check_due,'start') as start:
            self.assertFalse(scheduler.start_if_authorized())
        start.assert_not_called()

    def test_scheduler_does_not_duplicate_on_ready(self):
        env=dict(zip(('RAILWAY_PROJECT_ID','RAILWAY_ENVIRONMENT_ID','RAILWAY_SERVICE_ID'),job.TEST_IDS))
        env['HERALDO_TEST_BACKUP_ENABLED']='enabled'
        with patch.dict(os.environ,env,clear=True),patch.object(scheduler._check_due,'is_running',side_effect=[False,True]),patch.object(scheduler._check_due,'start') as start,redirect_stdout(StringIO()):
            scheduler.start_if_authorized();scheduler.start_if_authorized()
        self.assertEqual(start.call_count,1)

    def test_scheduler_failure_is_sanitized_and_not_repeated_in_logs(self):
        scheduler._last_status=None
        out=StringIO()
        with patch.object(scheduler,'_invoke',side_effect=RuntimeError('PRIVATE')),redirect_stdout(out):
            asyncio.run(scheduler._check_due.coro());asyncio.run(scheduler._check_due.coro())
        self.assertNotIn('PRIVATE',out.getvalue())
        self.assertEqual(out.getvalue().count('BLOCKED'),1)

    def test_subprocess_has_no_discord_token(self):
        import subprocess
        with patch.dict(os.environ,{'DISCORD_TOKEN':'PRIVATE'}),patch.object(scheduler.subprocess,'run',return_value=subprocess.CompletedProcess([],0,b'',b'')) as run:
            self.assertEqual(scheduler._invoke(),'IDLE')
        self.assertNotIn('DISCORD_TOKEN',run.call_args.kwargs['env'])
