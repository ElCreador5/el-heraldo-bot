"""Checks for the shared progress renderer (no Discord gateway)."""
import unittest
from unittest.mock import AsyncMock

from operation_progress import ProgressReporter, status_text


class OperationProgressTests(unittest.IsolatedAsyncioTestCase):
    async def test_updates_are_throttled_and_forced_completion_is_visible(self):
        edit = AsyncMock()
        reporter = ProgressReporter(edit, interval=60)
        self.assertTrue(await reporter.publish("Started"))
        self.assertFalse(await reporter.publish("Still working"))
        self.assertEqual(edit.await_count, 1)
        self.assertTrue(await reporter.publish("Finished", force=True))
        self.assertEqual(edit.await_count, 2)
        self.assertEqual(edit.await_args.args[0], "Finished")

    async def test_statuses_are_localized_without_inventing_percentages(self):
        for locale in ("es-419", "en-US", "pt-BR"):
            scan = status_text(locale, "scan", channels=2, total=5, examined=100, found=8)
            deletion = status_text(locale, "delete", processed=3, total=7, deleted=2, failed=1)
            self.assertIn("2/5", scan)
            self.assertIn("100", scan)
            self.assertIn("3/7", deletion)
            self.assertNotIn("%", scan + deletion)


if __name__ == "__main__":
    unittest.main()
