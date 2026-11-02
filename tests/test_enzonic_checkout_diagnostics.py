"""Ensure that an incomplete Enzonic deployment fails closed with a useful diagnostic."""
import contextlib
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import enzonic_test_host as host
from backup_job import BackupJobError


class CheckoutDiagnosticsTests(unittest.TestCase):
    def test_missing_file_reports_reason_and_blocks(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(host, "ROOT", Path(tmp)):
                capture = io.StringIO()
                with contextlib.redirect_stdout(capture):
                    with self.assertRaises(BackupJobError):
                        host._git_blob_sha(Path(tmp) / "missing.py", 10)
                self.assertIn("reason=missing", capture.getvalue())
                self.assertIn("status=MISMATCH", capture.getvalue())

    def test_wrong_size_blocks(self):
        with tempfile.TemporaryDirectory() as tmp:
            file = Path(tmp) / "bot.py"
            file.write_bytes(b"123")
            with patch.object(host, "ROOT", Path(tmp)):
                capture = io.StringIO()
                with contextlib.redirect_stdout(capture):
                    with self.assertRaises(BackupJobError):
                        host._git_blob_sha(file, 5)
                self.assertIn("reason=size", capture.getvalue())


if __name__ == "__main__":
    unittest.main()
