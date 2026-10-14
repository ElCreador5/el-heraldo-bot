"""Regresiones offline del ejecutor H-03, sin tráfico ni credenciales reales."""
from datetime import datetime, timezone, timedelta
import json
import os
from pathlib import Path
import shutil
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

import backup_job


class BackupJobTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="heraldo-job-regression-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.db = self.root / "live.sqlite"
        self.state = self.root / "journal"
        with sqlite3.connect(self.db) as conn:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("CREATE TABLE lab_values (id INTEGER PRIMARY KEY, marker TEXT NOT NULL)")
            conn.execute("INSERT INTO lab_values VALUES (1, 'LAB_NON_SENSITIVE')")
            conn.commit()
        self.day = datetime(2026, 10, 13, tzinfo=timezone.utc)

    def _transport(self):
        remote = {}

        def upload(package, environment):
            self.assertEqual(environment, "lab")
            remote["package"] = Path(package)
            from sqlite_recovery import validate_backup
            sha = validate_backup(package, environment=environment)["sha256"]
            return {"object": "lab/20261013/" + "a" * 32 + ".h03e", "plaintext_sha256": sha}

        def download(name, environment, destination):
            self.assertTrue(name.startswith("lab/"))
            target = Path(destination) / "received"
            shutil.copytree(remote["package"], target)
            from sqlite_recovery import validate_backup
            return {"plaintext_sha256": validate_backup(target, environment=environment)["sha256"],
                    "local_package": str(target)}

        return upload, download

    def _run(self, now=None):
        return backup_job.run_once(self.db, self.state, environment="lab",
                                   revision="lab-test", now=now or self.day)

    def test_roundtrip_and_private_receipt(self):
        up, down = self._transport()
        with patch.object(backup_job, "upload", side_effect=up) as uploader, patch.object(
                backup_job, "download_verify", side_effect=down) as downloader:
            self.assertEqual(self._run(), "verified_and_restored")
        self.assertEqual(uploader.call_count, 1)
        self.assertEqual(downloader.call_count, 1)
        receipts = list(self.state.glob("lab-*.json"))
        self.assertEqual(len(receipts), 1)
        data = json.loads(receipts[0].read_text())
        self.assertEqual(data["status"], "verified_and_restored")
        self.assertEqual(receipts[0].stat().st_mode & 0o077, 0)
        self.assertEqual(self.state.stat().st_mode & 0o077, 0)
        self.assertNotIn("LAB_NON_SENSITIVE", receipts[0].read_text())
        with sqlite3.connect(self.db) as conn:
            self.assertEqual(conn.execute("SELECT count(*) FROM lab_values").fetchone()[0], 1)

    def test_duplicate_same_day_not_retried(self):
        up, down = self._transport()
        with patch.object(backup_job, "upload", side_effect=up) as uploader, patch.object(
                backup_job, "download_verify", side_effect=down):
            self._run()
            with self.assertRaisesRegex(backup_job.BackupJobError, "already_attempted_today"):
                self._run()
        self.assertEqual(uploader.call_count, 1)

    def test_ambiguous_failure_marks_review_not_retry(self):
        with patch.object(backup_job, "upload", side_effect=TimeoutError("sensitive-url")) as uploader:
            with self.assertRaises(TimeoutError):
                self._run()
            with self.assertRaisesRegex(backup_job.BackupJobError, "previous_attempt_needs_review"):
                self._run()
        self.assertEqual(uploader.call_count, 1)
        receipt = next(self.state.glob("lab-*.json")).read_text()
        self.assertIn("needs_manual_review", receipt)
        self.assertNotIn("sensitive-url", receipt)

    def test_production_requires_identity_and_explicit_switch(self):
        with patch.dict(os.environ, {"HERALDO_PRODUCTION_BACKUP_ENABLED": "enabled-after-owner-approval"}, clear=True):
            with self.assertRaisesRegex(backup_job.BackupJobError, "production_not_authorized"):
                backup_job.run_once(self.db, self.state,
                                    environment="heraldo-production", revision="main", now=self.day)
        self.assertFalse(self.state.exists())

    def test_lab_cannot_run_in_production_project(self):
        with patch.dict(os.environ, {"RAILWAY_PROJECT_ID": backup_job.PRODUCTION_IDS[0]}):
            with self.assertRaisesRegex(backup_job.BackupJobError, "laboratory_mode_on_production"):
                self._run()
        self.assertFalse(self.state.exists())

    def test_next_day_separate_attempt(self):
        up, down = self._transport()
        with patch.object(backup_job, "upload", side_effect=up), patch.object(
                backup_job, "download_verify", side_effect=down):
            self._run()
            self._run(now=self.day + timedelta(days=1))
        self.assertEqual(len(list(self.state.glob("lab-*.json"))), 2)


if __name__ == "__main__":
    unittest.main()
