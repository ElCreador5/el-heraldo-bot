"""Checks for the shared progress renderer (no Discord gateway)."""
import unittest
from unittest.mock import AsyncMock

from operation_progress import ProgressReporter, compact_progress_bar, progress_bar, status_text


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

    async def test_progress_bar_never_claims_completion_too_early(self):
        bar, percent = progress_bar(447, 1000)
        self.assertEqual(percent, 44)
        self.assertEqual(len(bar.strip("`")), 16)
        self.assertIn("█", bar)
        self.assertIn("░", bar)
        self.assertEqual(progress_bar(1000, 1000)[1], 99)
        self.assertEqual(progress_bar(1000, 1000, complete=True)[1], 100)
        self.assertNotIn("░", progress_bar(1000, 1000, complete=True)[0])

    async def test_progress_unknown_or_stale_total_is_indeterminate(self):
        for total in (None, 0, -1, 200):
            bar, percent = progress_bar(447, total)
            self.assertIsNone(percent)
            self.assertIn("█", bar)
            self.assertIn("░", bar)

    async def test_compact_progress_has_ten_blocks_and_no_false_completion(self):
        bar, percent = compact_progress_bar(575, 923)
        self.assertEqual((bar, percent), ("`██████▌···`", 62))
        self.assertEqual(compact_progress_bar(923, 923)[1], 99)
        self.assertEqual(compact_progress_bar(0, 923)[1], 0)

    async def test_compact_indeterminate_does_not_claim_percentage(self):
        for total in (None, 0, -1, 300):
            bar, percent = compact_progress_bar(575, total)
            self.assertIsNone(percent)
            self.assertEqual(len(bar.strip("`")), 10)
            self.assertIn("▌", bar)

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
