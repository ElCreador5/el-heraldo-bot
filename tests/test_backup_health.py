"""Regresiones offline: el estado OK solo procede de recibos íntegros."""
from datetime import datetime, timezone
from pathlib import Path
import tempfile
import unittest

from backup_job import _write_receipt
from tools.backup_health import inspect


class HealthTests(unittest.TestCase):
    def _put(self, folder, day, status="verified_and_restored", **overrides):
        data = {
            "version": 1,
            "environment": "lab",
            "utc_day": day,
            "status": status,
            "started_at": f"{day[:4]}-{day[4:6]}-{day[6:]}T06:14:00+00:00",
        }
        if status == "verified_and_restored":
            data["finished_at"] = f"{day[:4]}-{day[4:6]}-{day[6:]}T06:15:00+00:00"
        data.update(overrides)
        path = Path(folder) / ("lab-" + day + ".json")
        _write_receipt(path, data, initial=True)
        return path

    def test_missing_and_failed_periods(self):
        with tempfile.TemporaryDirectory() as folder:
            self._put(folder, "20261011")
            self._put(folder, "20261013")
            at = datetime(2026, 10, 14, 7, tzinfo=timezone.utc)
            result = inspect(folder, at)
            self.assertEqual(result["missing_periods"], 1)
            self.assertEqual(result["reason"], "missing_period")
            self._put(folder, "20261014", "needs_manual_review")
            self.assertEqual(inspect(folder, at)["reason"], "attempt_needs_review")

    def test_no_attempt(self):
        with tempfile.TemporaryDirectory() as folder:
            self.assertEqual(inspect(Path(folder))["reason"], "no_attempt")

    def test_stale_and_current(self):
        with tempfile.TemporaryDirectory() as folder:
            self._put(folder, "20261013")
            self.assertEqual(inspect(folder, datetime(2026, 10, 13, 7, tzinfo=timezone.utc))["status"], "OK")
            self.assertEqual(inspect(folder, datetime(2026, 10, 14, 19, tzinfo=timezone.utc))["reason"], "stale")

    def test_invalid_receipt_sanitized(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "lab-20261013.json"
            path.write_text("private malformed payload")
            path.chmod(0o600)
            result = inspect(folder)
            self.assertEqual(result["reason"], "invalid_receipt")
            self.assertNotIn("private", str(result))

    def test_age_uses_completion_time_not_midnight(self):
        with tempfile.TemporaryDirectory() as folder:
            self._put(folder, "20261013")
            self.assertEqual(inspect(folder, datetime(2026, 10, 14, 13, tzinfo=timezone.utc))["status"], "OK")
            self.assertEqual(inspect(folder, datetime(2026, 10, 14, 19, tzinfo=timezone.utc))["reason"], "stale")

    def test_future_completion_is_invalid(self):
        with tempfile.TemporaryDirectory() as folder:
            self._put(folder, "20261013", finished_at="2026-10-15T06:15:00+00:00")
            self.assertEqual(inspect(folder, datetime(2026, 10, 14, tzinfo=timezone.utc))["reason"], "invalid_receipt")

    def test_invalid_completion_type_is_sanitized(self):
        with tempfile.TemporaryDirectory() as folder:
            self._put(folder, "20261013", finished_at=123)
            self.assertEqual(inspect(folder)["reason"], "invalid_receipt")

    def test_missing_completion_is_not_a_success(self):
        with tempfile.TemporaryDirectory() as folder:
            self._put(folder, "20261013", finished_at=None)
            self.assertEqual(inspect(folder)["reason"], "invalid_receipt")

    def test_wrong_period_or_environment_not_success(self):
        at = datetime(2026, 10, 14, 8, tzinfo=timezone.utc)
        for wrong in ({"utc_day": "20261012"}, {"environment": "heraldo-production"},
                      {"version": 3}, {"status": "invented_success"}):
            with self.subTest(wrong=wrong), tempfile.TemporaryDirectory() as folder:
                self._put(folder, "20261013", **wrong)
                self.assertEqual(inspect(folder, at)["reason"], "invalid_receipt")

    def test_future_receipt_day_does_not_mask_failure(self):
        with tempfile.TemporaryDirectory() as folder:
            self._put(folder, "20261016")
            self.assertEqual(inspect(folder, datetime(2026, 10, 14, 8, tzinfo=timezone.utc))["reason"], "invalid_receipt")

    def test_completion_before_start_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            self._put(folder, "20261013", finished_at="2026-10-13T06:13:59+00:00")
            self.assertEqual(inspect(folder)["reason"], "invalid_receipt")

    def test_completion_long_after_start_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            self._put(folder, "20261013", finished_at="2026-10-13T09:15:00+00:00")
            self.assertEqual(inspect(folder)["reason"], "invalid_receipt")

    def test_corrupt_filename_does_not_get_ignored(self):
        with tempfile.TemporaryDirectory() as folder:
            self._put(folder, "20261013")
            (Path(folder) / "lab-invalid-date.json").write_text("broken")
            self.assertEqual(inspect(folder)["reason"], "invalid_receipt")

    def test_non_private_receipt_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path = self._put(folder, "20261013")
            path.chmod(0o644)
            self.assertEqual(inspect(folder)["reason"], "invalid_receipt")


if __name__ == "__main__":
    unittest.main()
