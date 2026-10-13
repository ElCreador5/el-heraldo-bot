"""Entrada cron H-03: pruebas sin Railway, secretos ni red."""
import os
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from backup_job import BackupJobError
from tools import scheduled_lab_backup as cron


class LabCronTests(unittest.TestCase):
    def setUp(self):
        self.env = {"RAILWAY_PROJECT_ID": cron.TEST_PROJECT,
                    "RAILWAY_ENVIRONMENT_ID": cron.TEST_ENVIRONMENT,
                    "RAILWAY_SERVICE_NAME": cron.TEST_SERVICE}

    def test_service_identity_is_required(self):
        with patch.dict(os.environ, {"RAILWAY_PROJECT_ID": "not-test"}, clear=True):
            with self.assertRaisesRegex(BackupJobError, "not_railway_test_cron_service"):
                cron.run()

    def test_discord_token_rejected(self):
        with patch.dict(os.environ, {**self.env, "DISCORD_TOKEN": "synthetic-never-real"}, clear=True):
            with self.assertRaisesRegex(BackupJobError, "discord_token_must_not_be_present"):
                cron.run()

    def test_persistent_mount_required(self):
        with patch.dict(os.environ, self.env, clear=True), patch.object(Path, "is_mount", return_value=False):
            with self.assertRaisesRegex(BackupJobError, "persistent_volume_not_mounted"):
                cron.run()

    def test_runs_once_with_synthetic_table(self):
        def inspect(source, state, *, environment, revision):
            self.assertEqual(environment, "lab")
            self.assertEqual(revision, "scheduled-lab")
            self.assertEqual(state, cron.STATE)
            with sqlite3.connect(source) as conn:
                self.assertEqual(conn.execute("SELECT count(*) FROM synthetic_probe").fetchone()[0], 1)
            return "verified_and_restored"

        with patch.dict(os.environ, self.env, clear=True), patch.object(
                Path, "is_mount", return_value=True), patch.object(cron, "run_once", side_effect=inspect) as runner:
            self.assertEqual(cron.run(), 0)
            self.assertEqual(runner.call_count, 1)

    def test_duplicate_is_successful_noop_without_retry(self):
        with patch.dict(os.environ, self.env, clear=True), patch.object(Path, "is_mount", return_value=True), patch.object(
                cron, "run_once", side_effect=BackupJobError("already_attempted_today")) as runner:
            self.assertEqual(cron.run(), 0)
            self.assertEqual(runner.call_count, 1)

    def test_other_failure_propagates_to_critical_exit(self):
        with patch.dict(os.environ, self.env, clear=True), patch.object(Path, "is_mount", return_value=True), patch.object(
                cron, "run_once", side_effect=BackupJobError("upload_failed")):
            with self.assertRaisesRegex(BackupJobError, "upload_failed"):
                cron.run()


if __name__ == "__main__":
    unittest.main()
