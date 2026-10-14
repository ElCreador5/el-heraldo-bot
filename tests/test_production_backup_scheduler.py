"""Regresiones offline del planificador H-03 productivo (inactivo en Test)."""
import asyncio
from contextlib import redirect_stdout
from io import StringIO
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch, AsyncMock, Mock

from backup_job import BackupJobError, PRODUCTION_IDS
import production_backup_scheduler as service


class SchedulerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="h03-scheduler-offline-")
        self.addCleanup(self.temp.cleanup)
        self.source = Path(self.temp.name) / "fixture.sqlite"
        self.source.write_bytes(b"synthetic-and-not-a-real-db")
        self.env = {
            "HERALDO_PRODUCTION_BACKUP_ENABLED": "enabled-after-owner-approval",
            "RAILWAY_PROJECT_ID": PRODUCTION_IDS[0],
            "RAILWAY_ENVIRONMENT_ID": PRODUCTION_IDS[1],
            "RAILWAY_SERVICE_ID": PRODUCTION_IDS[2],
            "RAILWAY_GIT_COMMIT_SHA": "a" * 40,
        }
        self.env.update({key: "synthetic-placeholder" for key in service._REQUIRED_SECRETS})

    def test_disabled_does_not_start(self):
        with patch.dict(os.environ, {}, clear=True), patch.object(
                service, "preflight") as preflight, patch.object(
                service._daily_backup, "start") as starter:
            self.assertFalse(service.start_if_authorized(self.source))
            preflight.assert_not_called()
            starter.assert_not_called()

    def test_rejects_wrong_railway_project(self):
        variables = dict(self.env, RAILWAY_PROJECT_ID="not-production")
        with self.assertRaisesRegex(BackupJobError, "production_identity_mismatch"):
            service.preflight(self.source, variables)

    def test_rejects_wrong_railway_service(self):
        variables = dict(self.env, RAILWAY_SERVICE_ID="wrong-service")
        with self.assertRaisesRegex(BackupJobError, "production_identity_mismatch"):
            service.preflight(self.source, variables)

    def test_rejects_missing_explicit_flag(self):
        variables = dict(self.env, HERALDO_PRODUCTION_BACKUP_ENABLED="")
        with self.assertRaisesRegex(BackupJobError, "production_not_enabled"):
            service.preflight(self.source, variables)

    def test_rejects_invalid_revision(self):
        variables = dict(self.env, RAILWAY_GIT_COMMIT_SHA="not-a-commit")
        with self.assertRaisesRegex(BackupJobError, "invalid_deployment_revision"):
            # Source would otherwise be rejected by /data volume guard.
            with patch.object(service.Path, "resolve",
                              side_effect=lambda *args, **kwargs: Path("/data/fixture.sqlite")):
                service.preflight(self.source, variables)

    def test_rejects_missing_source(self):
        with self.assertRaisesRegex(BackupJobError, "invalid_source"):
            service.preflight(Path(self.temp.name) / "missing.sqlite", self.env)

    def test_production_start_rechecks_ownership_and_does_not_duplicate(self):
        with patch.dict(os.environ, self.env), patch.object(
                service, "preflight", return_value=(self.source, "a"*40)), patch.object(
                service, "_guard") as guard, patch.object(
                service._daily_backup, "is_running", side_effect=[False, True]), patch.object(
                service._daily_backup, "start") as starter, redirect_stdout(StringIO()):
            self.assertTrue(service.start_if_authorized(self.source))
            self.assertTrue(service.start_if_authorized(self.source))
        self.assertEqual(starter.call_count, 1)
        self.assertEqual(guard.call_count, 2)

    def test_runner_revalidates_before_sqlite_and_cloud(self):
        service._source, service._revision = self.source, "a"*40
        with patch.object(service, "preflight", return_value=(self.source, "a"*40)) as pre, patch.object(
                service, "run_once", return_value="verified_and_restored") as runner:
            result = service._perform_once()
        self.assertEqual(result, "verified_and_restored")
        self.assertEqual(pre.call_count, 1)
        self.assertEqual(runner.call_args.kwargs["environment"], "heraldo-production")
        self.assertEqual(runner.call_args.kwargs["revision"], "a"*40)

    def test_uncertain_upload_never_prints_secrets(self):
        secret = "signed-secret-url-would-leak"
        with patch.object(service, "_perform_once", side_effect=RuntimeError(secret)):
            out = StringIO()
            with redirect_stdout(out):
                asyncio.run(service._daily_backup.coro())
        self.assertIn("H03_DAILY status=BLOCKED", out.getvalue())
        self.assertNotIn(secret, out.getvalue())

    def test_coroutine_runs_blocking_io_off_thread(self):
        async def fake_to_thread(func):
            self.assertIs(func, service._perform_once)
            return "verified_and_restored"
        with patch.object(service.asyncio, "to_thread", side_effect=fake_to_thread) as executor:
            out = StringIO()
            with redirect_stdout(out):
                asyncio.run(service._daily_backup.coro())
        self.assertEqual(executor.call_count, 1)
        self.assertIn("VERIFIED_AND_RESTORED", out.getvalue())


if __name__ == "__main__":
    unittest.main()
