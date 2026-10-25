"""Synthetic SQLite/AES-GCM round trips; remote HTTP and release are simulated."""
from i18n_source_helpers import source_text as _source_text
from contextlib import redirect_stdout
from datetime import datetime, timedelta, timezone
from io import StringIO
import json
import os
from pathlib import Path
import shutil
import sqlite3
import tempfile
import unittest
from unittest.mock import Mock, patch
import uuid

import backup_job as job
import preupdate_gate as gate
import supabase_backup as cloud
from sqlite_recovery import validate_backup, RecoveryError


class PreupdateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.db, self.state = self.base / "live.sqlite", self.base / "state"
        with sqlite3.connect(self.db) as db:
            db.execute("CREATE TABLE parent(id INTEGER PRIMARY KEY)")
            db.execute("CREATE TABLE child(id INTEGER REFERENCES parent(id), value TEXT)")
            db.execute("INSERT INTO parent VALUES(1)")
            db.execute("INSERT INTO child VALUES(1,'SYNTHETIC')")
        self.started = datetime.now(timezone.utc)
        self.now = self.started + timedelta(seconds=5)
        self.request, self.source, self.target = "1" * 32, "a" * 40, "b" * 40
        self.key, self.objects = os.urandom(32), {}
        self.up = patch.object(job, "upload", side_effect=self.upload).start()
        patch.object(job, "download_verify", side_effect=self.download).start()
        self.down = patch.object(gate, "download_verify", side_effect=self.download).start()
        self.addCleanup(patch.stopall)
        self.apply = Mock(return_value=True)

    def upload(self, package, environment):
        blob, manifest = cloud._bundle(package, environment, self.key)
        name = environment + "/20261017/" + uuid.uuid4().hex + ".h03e"
        self.objects[name] = blob
        return {"object": name, "plaintext_sha256": manifest["sha256"]}

    def download(self, name, environment, destination):
        with cloud._unpack(self.objects[name], environment, self.key) as package:
            target = Path(destination) / uuid.uuid4().hex
            shutil.copytree(package, target)
            return {"local_package": str(target),
                    "plaintext_sha256": validate_backup(target, environment=environment)["sha256"]}

    def prepare(self, request=None):
        return job.run_once(self.db, self.state, environment="lab", revision=self.source,
                            now=self.started, purpose="preupdate", request_id=request or self.request,
                            target_revision=self.target)

    def publish(self, **overrides):
        args = dict(environment="lab", request_id=self.request, source_revision=self.source,
                    target_revision=self.target, now=self.now, apply_update=self.apply)
        args.update(overrides)
        return gate.guarded_update(self.db, self.state, **args)

    def receipt(self):
        return self.state / ("lab-preupdate-" + self.request + ".json")

    def change_receipt(self, **values):
        data = json.loads(_source_text(self.receipt()))
        data.update(values)
        self.receipt().write_text(json.dumps(data))

    def test_daily_and_each_update_are_independent_same_day(self):
        job.run_once(self.db, self.state, environment="lab", revision=self.source, now=self.started)
        self.prepare()
        self.prepare("2" * 32)
        self.assertEqual(len(self.objects), 3)
        self.assertEqual(len(list(self.state.glob("*.json"))), 3)
        self.assertIs(self.publish(), True)
        self.apply.assert_called_once_with()
        self.assertEqual(self.down.call_count, 1)
        self.assertEqual(self.receipt().stat().st_mode & 0o777, 0o600)

    def test_update_id_never_reused_even_tomorrow(self):
        self.prepare()
        with self.assertRaisesRegex(job.BackupJobError, "update_already_attempted"):
            job.run_once(self.db, self.state, environment="lab", revision=self.source,
                         now=self.started + timedelta(days=1), purpose="preupdate",
                         request_id=self.request, target_revision=self.target)
        self.assertEqual(self.up.call_count, 1)

    def test_consumption_survives_new_controller_invocation(self):
        self.prepare()
        self.publish()
        with self.assertRaisesRegex(job.BackupJobError, "already_consumed"):
            self.publish()
        self.apply.assert_called_once()

    def test_target_and_source_changes_block_before_controller(self):
        self.prepare()
        for args in ({"target_revision": "c" * 40}, {"source_revision": "c" * 40}):
            with self.subTest(args=args), self.assertRaisesRegex(job.BackupJobError, "binding_mismatch"):
                self.publish(**args)
        self.apply.assert_not_called()
        self.down.assert_not_called()

    def test_forged_local_receipt_cannot_authorize_daily_object(self):
        job.run_once(self.db, self.state, environment="lab", revision=self.source, now=self.started)
        data = json.loads(_source_text(next(self.state.glob('lab-*.json'))))
        data.update(version=2, operation=gate._binding(self.request, self.source, self.target))
        job._write_receipt(self.receipt(), data, initial=True)
        with self.assertRaisesRegex(job.BackupJobError, "remote_binding_mismatch"):
            self.publish()
        self.apply.assert_not_called()

    def test_ciphertext_tampering_blocks_controller(self):
        self.prepare()
        name = next(iter(self.objects))
        blob = self.objects[name]
        self.objects[name] = blob[:-1] + bytes([blob[-1] ^ 1])
        with self.assertRaises(cloud.CloudBackupError):
            self.publish()
        self.apply.assert_not_called()

    def test_missing_external_object_blocks_controller(self):
        self.prepare()
        self.objects.clear()
        with self.assertRaises(KeyError):
            self.publish()
        self.apply.assert_not_called()

    def test_failed_isolated_restore_blocks_controller(self):
        self.prepare()
        with patch.object(gate, "_isolated_restore", side_effect=job.BackupJobError("restore_failed")):
            with self.assertRaisesRegex(job.BackupJobError, "restore_failed"):
                self.publish()
        self.apply.assert_not_called()

    def test_slow_remote_recheck_expires_before_publication(self):
        self.prepare()
        with patch.object(gate, "datetime", wraps=datetime) as clock:
            clock.now.side_effect = [self.started + timedelta(minutes=14),
                                    self.started + timedelta(minutes=16)]
            with self.assertRaisesRegex(job.BackupJobError, "expired_or_invalid"):
                self.publish(now=None)
        self.apply.assert_not_called()

    def test_old_future_naive_and_slow_receipts_block_controller(self):
        self.prepare()
        original = json.loads(_source_text(self.receipt()))
        cases = [
            {"started_at": (self.started - timedelta(hours=1)).isoformat()},
            {"finished_at": (self.now + timedelta(seconds=1)).isoformat()},
            {"started_at": self.started.replace(tzinfo=None).isoformat()},
            {"started_at": (self.started - timedelta(minutes=11)).isoformat()},
            {"utc_day": "19000101"},
        ]
        for changes in cases:
            self.receipt().write_text(json.dumps({**original, **changes}))
            with self.subTest(changes=changes), self.assertRaises(job.BackupJobError):
                self.publish()
        self.apply.assert_not_called()

    def test_failed_update_is_uncertain_and_not_retried(self):
        self.prepare()
        self.apply.side_effect = RuntimeError("private-provider-error")
        with self.assertRaises(RuntimeError):
            self.publish()
        with self.assertRaisesRegex(job.BackupJobError, "already_consumed"):
            self.publish()
        self.apply.assert_called_once()
        authorization = next(self.state.glob("*.authorization.json"))
        self.assertIn("needs_manual_review", _source_text(authorization))
        self.assertNotIn("private-provider-error", _source_text(authorization))

    def test_same_lock_covers_verification_and_update(self):
        self.prepare()
        def update():
            with self.assertRaisesRegex(job.BackupJobError, "job_already_running"):
                job.run_once(self.db, self.state, environment="lab", revision=self.source)
            return True
        self.publish(apply_update=update)
        with job._exclusive_job_lock(self.state):
            with self.assertRaisesRegex(job.BackupJobError, "job_already_running"):
                self.prepare("3" * 32)

    def test_invalid_id_and_target_do_not_upload(self):
        for request, target in (("../escape", self.target), (self.request, "main")):
            with self.assertRaises(job.BackupJobError):
                job.run_once(self.db, self.state, environment="lab", revision=self.source,
                             purpose="preupdate", request_id=request, target_revision=target)
        self.up.assert_not_called()

    def test_unconfirmed_controller_result_is_not_success(self):
        self.prepare()
        self.apply.return_value = False
        with self.assertRaisesRegex(job.BackupJobError, "update_result_unconfirmed"):
            self.publish()
        with self.assertRaisesRegex(job.BackupJobError, "already_consumed"):
            self.publish()

    def test_foreign_key_corruption_never_uploads(self):
        with sqlite3.connect(self.db) as db:
            db.execute("INSERT INTO child VALUES (999,'SYNTHETIC_INVALID_FK')")
        with self.assertRaisesRegex(RecoveryError, "foreign_keys_failed"):
            self.prepare()
        self.up.assert_not_called()
        self.assertEqual(json.loads(_source_text(self.receipt()))["status"], "needs_manual_review")

    def test_ambiguous_preupdate_upload_never_retried(self):
        self.up.side_effect = TimeoutError("private-url")
        with self.assertRaises(TimeoutError):
            self.prepare()
        with self.assertRaisesRegex(job.BackupJobError, "previous_attempt_needs_review"):
            self.prepare()
        self.up.assert_called_once()

    def test_cli_logs_no_private_provider_detail(self):
        out = StringIO()
        with patch.object(gate, "run_once", side_effect=RuntimeError("private-url")), patch.dict(
                os.environ, {"DB_PATH": str(self.db)}), redirect_stdout(out):
            result = gate.main(["prepare", "--request-id", self.request,
                                "--source-revision", self.source, "--target-revision", self.target])
        self.assertEqual(result, 1)
        self.assertIn("status=BLOCKED", out.getvalue())
        self.assertNotIn("private-url", out.getvalue())


class ProductionVolumeTests(unittest.TestCase):
    def setUp(self):
        self.env = {"RAILWAY_VOLUME_NAME": job.PRODUCTION_VOLUME_NAME,
                    "RAILWAY_VOLUME_MOUNT_PATH": "/data", "DB_PATH": "/data/heraldo.db"}

    def test_directory_named_data_is_not_a_volume(self):
        with patch.object(job.os.path, "ismount", return_value=False), patch.object(
                Path, "read_text", return_value="1 0 0:1 / / rw - overlay overlay rw"):
            with self.assertRaisesRegex(job.BackupJobError, "production_volume_not_mounted"):
                job._production_volume(Path("/data/heraldo.db"), job.PRODUCTION_STATE_DIR, self.env)

    def test_predeploy_without_volume_identity_is_blocked(self):
        with self.assertRaisesRegex(job.BackupJobError, "production_volume_identity_mismatch"):
            job._production_volume(Path("/data/heraldo.db"), job.PRODUCTION_STATE_DIR, {})

    def test_bind_mount_is_verified_from_kernel_mountinfo(self):
        with patch.object(job.os.path, "ismount", return_value=False), patch.object(
                Path, "read_text", return_value="2 1 0:1 /vol /data rw - ext4 /dev/x rw"):
            job._production_volume(Path("/data/heraldo.db"), job.PRODUCTION_STATE_DIR, self.env)

    def test_alternate_root_cannot_bypass_common_lock(self):
        with patch.object(job.os.path, "ismount", return_value=True):
            with self.assertRaisesRegex(job.BackupJobError, "production_path_mismatch"):
                job._production_volume(Path("/data/heraldo.db"), Path("/data/other-state"), self.env)

    def test_production_cannot_claim_different_source_revision(self):
        with patch.object(job, "_guard"), patch.dict(os.environ, {"RAILWAY_GIT_COMMIT_SHA": "a" * 40}):
            with self.assertRaisesRegex(job.BackupJobError, "source_revision_mismatch"):
                job.run_once(Path("/unused"), job.PRODUCTION_STATE_DIR,
                             environment="heraldo-production", revision="c" * 40)


if __name__ == "__main__":
    unittest.main()
