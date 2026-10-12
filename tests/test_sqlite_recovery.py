"""H-03: SQLite real, WAL, concurrencia, errores y restauración aislada."""
from contextlib import closing
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import sqlite_recovery as recovery


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.db = self.root / "source.db"
        self.backups = self.root / "backups"
        with closing(sqlite3.connect(self.db)) as conn, conn:
            conn.executescript("""
                CREATE TABLE guild_cases (guild_id INTEGER,user_id INTEGER,
                    role_ids TEXT,active INTEGER, PRIMARY KEY(guild_id,user_id));
                CREATE TABLE guild_settings (guild_id INTEGER,key TEXT,value TEXT,
                    PRIMARY KEY(guild_id,key));
                CREATE TABLE evidence_archive_v1 (evidence_key TEXT PRIMARY KEY,
                    status TEXT NOT NULL, receipts TEXT NOT NULL);
                CREATE TABLE parent (id INTEGER PRIMARY KEY);
                CREATE TABLE child (parent_id INTEGER REFERENCES parent(id));
                INSERT INTO parent VALUES (1);
                INSERT INTO child VALUES (1);
                INSERT INTO guild_cases VALUES (11,5,'[7,8]',1),(12,5,'[9]',1);
                INSERT INTO guild_settings VALUES (11,'condemnation_pending_roles:5','[8]');
                INSERT INTO evidence_archive_v1 VALUES ('11:2:3:hash','pending','[]');
                INSERT INTO evidence_archive_v1 VALUES ('12:2:3:hash','complete','[{"sha256":"abc"}]');
            """)

    def backup(self, **kwargs):
        return recovery.create_backup(self.db, self.backups, environment="test",
                                      revision="synthetic-v1", **kwargs)

    def restore(self, package, target, **kwargs):
        return recovery.restore_backup(package, target, environment="test", schema_from=self.db,
                                       service_stopped=True, **kwargs)

    def test_integrity_metadata_permissions_and_unique_generations(self):
        first, second = self.backup(), self.backup()
        self.assertNotEqual(first, second)
        manifest = recovery.validate_backup(first, environment="test")
        self.assertEqual(manifest['rows']['guild_cases'], 2)
        self.assertFalse(manifest['evidence_files_included'])
        self.assertEqual(first.stat().st_mode & 0o777, 0o700)
        self.assertEqual((first / 'database.sqlite').stat().st_mode & 0o777, 0o600)
        self.assertEqual((first / 'manifest.json').stat().st_mode & 0o777, 0o600)

    def test_wal_committed_data_is_copied_without_checkpoint(self):
        with closing(sqlite3.connect(self.db)) as conn:
            conn.execute('PRAGMA journal_mode=WAL')
            conn.execute('PRAGMA wal_autocheckpoint=0')
            conn.execute("INSERT INTO guild_cases VALUES (13,5,'[10]',1)")
            conn.commit()
            self.assertTrue(Path(str(self.db) + '-wal').exists())
            package = self.backup()
            with closing(recovery.readonly(package / 'database.sqlite')) as copy:
                self.assertEqual(copy.execute('SELECT count(*) FROM guild_cases').fetchone()[0], 3)

    def test_concurrent_transaction_is_never_partially_copied(self):
        with closing(sqlite3.connect(self.db)) as conn:
            conn.execute('PRAGMA journal_mode=WAL')
        stop, ready = threading.Event(), threading.Event()
        errors = []
        def writer():
            try:
                with closing(sqlite3.connect(self.db)) as conn:
                    ready.set()
                    while not stop.is_set():
                        with conn:
                            conn.execute('UPDATE guild_cases SET active=1-active')
            except BaseException as exc:
                errors.append(exc)
        thread = threading.Thread(target=writer)
        thread.start()
        try:
            self.assertTrue(ready.wait(2))
            for _ in range(3):
                package = self.backup(timeout=10)
                with closing(recovery.readonly(package / 'database.sqlite')) as conn:
                    self.assertEqual(len(conn.execute('SELECT DISTINCT active FROM guild_cases').fetchall()), 1)
        finally:
            stop.set()
            thread.join(3)
        self.assertFalse(thread.is_alive())
        self.assertEqual(errors, [])

    def test_uncommitted_changes_not_included(self):
        with closing(sqlite3.connect(self.db)) as conn:
            conn.execute('PRAGMA journal_mode=WAL')
            conn.execute('UPDATE guild_cases SET active=0')
            package = self.backup()
            with closing(recovery.readonly(package / 'database.sqlite')) as copy:
                self.assertEqual(copy.execute('SELECT DISTINCT active FROM guild_cases').fetchall(), [(1,)])

    def test_low_storage_keeps_previous_backup(self):
        previous = self.backup()
        with patch.object(recovery.shutil, 'disk_usage', return_value=type('Disk', (), {'free': 0})()):
            with self.assertRaisesRegex(recovery.RecoveryError, 'insufficient_storage'):
                self.backup()
        recovery.validate_backup(previous, environment='test')
        self.assertEqual(list(self.backups.iterdir()), [previous])

    def test_write_failure_does_not_publish_partial(self):
        previous = self.backup()
        with patch.object(recovery, 'sync_path', side_effect=OSError('disk failure')):
            with self.assertRaises(OSError):
                self.backup()
        self.assertEqual(list(self.backups.iterdir()), [previous])

    def test_timeout_removes_partial_copy(self):
        with patch.object(recovery.time, 'monotonic', side_effect=[0, 31]):
            with self.assertRaisesRegex(recovery.RecoveryError, 'backup_timeout'):
                self.backup()
        self.assertEqual(list(self.backups.iterdir()), [])

    def test_process_interruption_and_restart(self):
        script = """
import os, sqlite_recovery as r, sys
r.inspect_database = lambda path: os._exit(23)
r.create_backup(sys.argv[1], sys.argv[2], environment='test', revision='crash')
"""
        result = subprocess.run([sys.executable, '-c', script, str(self.db), str(self.backups)],
                                cwd=Path(recovery.__file__).parent, capture_output=True)
        self.assertEqual(result.returncode, 23)
        partial = next(self.backups.iterdir())
        self.assertEqual(partial.stat().st_mode & 0o777, 0o700)
        with self.assertRaisesRegex(recovery.RecoveryError, 'incomplete_package'):
            recovery.validate_backup(partial, environment='test')
        recovery.validate_backup(self.backup(), environment='test')

    def test_restore_preserves_cases_roles_and_evidence_per_guild(self):
        package = self.backup()
        target = self.root / 'laboratory.db'
        self.restore(package, target)
        with closing(recovery.readonly(target)) as conn:
            self.assertEqual(conn.execute('SELECT guild_id,role_ids FROM guild_cases ORDER BY guild_id').fetchall(),
                             [(11, '[7,8]'), (12, '[9]')])
            self.assertEqual(conn.execute('SELECT value FROM guild_settings').fetchone()[0], '[8]')
            self.assertEqual(conn.execute('SELECT status FROM evidence_archive_v1 ORDER BY evidence_key').fetchall(),
                             [('pending',), ('complete',)])
            self.assertEqual(conn.execute('PRAGMA foreign_key_check').fetchall(), [])

    def test_existing_database_preserved_for_rollback(self):
        package = self.backup()
        target = self.root / 'lab.db'
        self.restore(package, target)
        with closing(sqlite3.connect(target)) as conn, conn:
            conn.execute('UPDATE guild_cases SET active=0')
        result = self.restore(package, target)
        previous = Path(result['previous_backup'])
        recovery.validate_backup(previous, environment='test')
        with closing(recovery.readonly(previous / 'database.sqlite')) as conn:
            self.assertEqual(conn.execute('SELECT DISTINCT active FROM guild_cases').fetchall(), [(0,)])
        self.restore(previous, target)
        with closing(recovery.readonly(target)) as conn:
            self.assertEqual(conn.execute('SELECT DISTINCT active FROM guild_cases').fetchall(), [(0,)])

    def test_active_service_lock_blocks_restore_cross_process(self):
        package = self.backup()
        target = self.root / 'lab.db'
        with recovery.service_lock(target):
            result = subprocess.run([sys.executable, '-m', 'sqlite_recovery', 'restore', str(package),
                                     '--db', str(target), '--environment', 'test', '--schema-from', str(self.db),
                                     '--service-stopped'], cwd=Path(recovery.__file__).parent,
                                    capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertIn('service_running_or_restore_active', result.stderr)
        self.assertFalse(target.exists())

    def test_offline_confirmation_required(self):
        with self.assertRaisesRegex(recovery.RecoveryError, 'stop_service_first'):
            recovery.restore_backup(self.backup(), self.root / 'lab.db', environment='test', schema_from=self.db)

    def test_unclean_wal_database_is_not_overwritten(self):
        package = self.backup()
        target = self.root / 'lab.db'
        self.restore(package, target)
        with closing(sqlite3.connect(target)) as conn:
            conn.execute('PRAGMA journal_mode=WAL')
            conn.execute('UPDATE guild_cases SET active=0')
            conn.commit()
            with self.assertRaisesRegex(recovery.RecoveryError, 'active_or_unclean_database'):
                self.restore(package, target)
            self.assertEqual(conn.execute('SELECT DISTINCT active FROM guild_cases').fetchall(), [(0,)])

    def test_schema_mismatch_rejected_before_replacement(self):
        package = self.backup()
        with closing(sqlite3.connect(self.db)) as conn:
            conn.execute('ALTER TABLE guild_cases ADD COLUMN future TEXT')
        with self.assertRaisesRegex(recovery.RecoveryError, 'schema_incompatible'):
            self.restore(package, self.root / 'lab.db')
        self.assertFalse((self.root / 'lab.db').exists())

    def test_environment_mismatch_rejected(self):
        package = self.backup()
        with self.assertRaisesRegex(recovery.RecoveryError, 'backup_identity_mismatch'):
            recovery.validate_backup(package, environment='production')

    def test_backup_sidecars_rejected(self):
        package = self.backup()
        (package / 'database.sqlite-wal').write_bytes(b'unclean')
        with self.assertRaisesRegex(recovery.RecoveryError, 'backup_has_sidecars'):
            self.restore(package, self.root / 'lab.db')

    def test_checksum_and_manifest_tampering_rejected(self):
        package = self.backup()
        with open(package / 'database.sqlite', 'ab') as stream:
            stream.write(b'corrupt')
        with self.assertRaisesRegex(recovery.RecoveryError, 'backup_checksum_failed'):
            self.restore(package, self.root / 'lab.db')
        other = self.backup()
        manifest = json.loads((other / 'manifest.json').read_text())
        manifest['rows']['guild_cases'] = 999
        (other / 'manifest.json').write_text(json.dumps(manifest))
        with self.assertRaisesRegex(recovery.RecoveryError, 'backup_metadata_mismatch'):
            recovery.validate_backup(other, environment='test')

    def test_foreign_key_violation_is_not_published(self):
        with closing(sqlite3.connect(self.db)) as conn, conn:
            conn.execute('INSERT INTO child VALUES (999)')
        with self.assertRaisesRegex(recovery.RecoveryError, 'foreign_keys_failed'):
            self.backup()
        self.assertEqual(list(self.backups.iterdir()), [])

    def test_insecure_directory_and_symlink_rejected(self):
        self.backups.mkdir(mode=0o755)
        self.backups.chmod(0o755)
        with self.assertRaisesRegex(recovery.RecoveryError, 'directory_not_private'):
            self.backup()
        alias = self.root / 'alias'
        alias.symlink_to(self.backups)
        with self.assertRaisesRegex(recovery.RecoveryError, 'symlink_directory'):
            recovery.create_backup(self.db, alias, environment='test', revision='v1')

    def test_replace_failure_preserves_original(self):
        package = self.backup()
        target = self.root / 'lab.db'
        self.restore(package, target)
        before = recovery.digest(target)
        with patch.object(recovery.os, 'replace', side_effect=OSError('replace failure')):
            with self.assertRaises(OSError):
                self.restore(package, target)
        self.assertEqual(recovery.digest(target), before)
        self.assertEqual(list(self.root.glob('.restore-*')), [])

    def test_real_bot_schema_round_trip_without_gateway(self):
        from test_safety_regressions import b
        actual = self.root / 'bot-schema.db'
        with patch.object(b, 'DB_PATH', str(actual)):
            b.db_init()
            b.honeypot_db_init()
            b.suggestion_db_init()
            b.condemnation_pending_roles_set(111, 5, [17, 18])
        package = recovery.create_backup(actual, self.backups, environment='test', revision='bot')
        target = self.root / 'restored-bot.db'
        recovery.restore_backup(package, target, environment='test', schema_from=actual, service_stopped=True)
        with patch.object(b, 'DB_PATH', str(target)):
            self.assertEqual(b.condemnation_pending_roles_get(111, 5), [17, 18])
            self.assertEqual(b.condemnation_pending_roles_get(112, 5), [])

    def test_retention_plan_keeps_last_copy_and_never_deletes(self):
        packages = [self.backup(), self.backup()]
        for package in packages:
            manifest = json.loads((package / 'manifest.json').read_text())
            manifest['created_at'] = '2020-01-01T00:00:00+00:00'
            (package / 'manifest.json').write_text(json.dumps(manifest))
        partial = self.backups / '.partial-crash'
        partial.mkdir(mode=0o700)
        plan = recovery.retention_plan(self.backups, environment='test', keep_min=1, max_age_days=1)
        self.assertEqual(len(plan['candidates']), 1)
        self.assertEqual(plan['unverified_preserved'], [str(partial)])
        self.assertEqual(set(self.backups.iterdir()), set(packages + [partial]))
        with self.assertRaises(recovery.RecoveryError):
            recovery.retention_plan(self.backups, environment='test', keep_min=0)

    def test_cli_backup_verify_restore_and_retention(self):
        def cli(*args):
            result = subprocess.run([sys.executable, '-m', 'sqlite_recovery', *args],
                                    cwd=Path(recovery.__file__).parent, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            return json.loads(result.stdout)
        created = cli('backup', '--db', str(self.db), '--destination', str(self.backups),
                      '--environment', 'test', '--revision', 'synthetic-cli')
        verified = cli('verify', created['package'], '--environment', 'test')
        self.assertEqual(verified['revision'], 'synthetic-cli')
        self.assertNotIn('rows', verified)
        restored = cli('restore', created['package'], '--db', str(self.root / 'cli.db'),
                       '--schema-from', str(self.db), '--environment', 'test', '--service-stopped')
        self.assertEqual(restored['sha256'], verified['sha256'])
        plan = cli('retention-plan', '--destination', str(self.backups), '--environment', 'test')
        self.assertEqual(plan['candidates'], [])
