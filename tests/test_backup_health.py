from datetime import datetime, timezone
from pathlib import Path
import tempfile
import unittest
from backup_job import _write_receipt
from tools.backup_health import inspect


class HealthTests(unittest.TestCase):
    def test_missing_and_failed_periods(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            _write_receipt(root/'lab-20261011.json', {'status':'verified_and_restored'}, initial=True)
            _write_receipt(root/'lab-20261013.json', {'status':'verified_and_restored'}, initial=True)
            result = inspect(root, datetime(2026,10,14,1,tzinfo=timezone.utc))
            self.assertEqual(result['missing_periods'], 1)
            self.assertEqual(result['reason'], 'missing_period')
            _write_receipt(root/'lab-20261014.json', {'status':'needs_manual_review'}, initial=True)
            self.assertEqual(inspect(root)['reason'], 'attempt_needs_review')

    def test_no_attempt(self):
        with tempfile.TemporaryDirectory() as folder:
            self.assertEqual(inspect(Path(folder))['reason'], 'no_attempt')

    def test_stale_and_current(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            _write_receipt(root/'lab-20261013.json', {'status':'verified_and_restored'}, initial=True)
            self.assertEqual(inspect(root, datetime(2026,10,13,6,tzinfo=timezone.utc))['status'], 'OK')
            self.assertEqual(inspect(root, datetime(2026,10,14,13,tzinfo=timezone.utc))['reason'], 'stale')

    def test_invalid_receipt_sanitized(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'lab-20261013.json'
            path.write_text('private malformed payload')
            path.chmod(0o600)
            result = inspect(Path(folder))
            self.assertEqual(result['reason'], 'invalid_receipt')
            self.assertNotIn('private', str(result))
