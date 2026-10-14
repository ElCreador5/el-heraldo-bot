"""Regression: legacy 'Solo reportar' must never delete messages.

Offline only. Uses a disposable SQLite database and does not connect Discord.
"""
import ast
from pathlib import Path
from types import SimpleNamespace as NS
import unittest
from unittest.mock import AsyncMock, patch

from test_regressions import b


class ReportOnlyReleaseTests(unittest.IsolatedAsyncioTestCase):
    async def test_legacy_report_with_purge_never_deletes_or_sanctions(self):
        target = NS(timeout=AsyncMock(), kick=AsyncMock(), ban=AsyncMock())
        with patch.object(b, "condemnation_protection_reason", return_value=None), \
             patch.object(b, "run_purge_job", new=AsyncMock()) as purge, \
             patch.object(b, "condemn_member", new=AsyncMock()) as condemn:
            result = await b.execute_moderation_report_action(
                NS(id=1), target, NS(), {"action": "report", "purge_minutes": 1440}, 3,
            )
        self.assertEqual(result, (True, "Reporte registrado"))
        for operation in (purge, condemn, target.timeout, target.kick, target.ban):
            operation.assert_not_awaited()

    def test_report_branch_precedes_purge_for_future_regressions(self):
        tree = ast.parse(Path(__file__).with_name("bot.py").read_text(encoding="utf-8"))
        method = next(node for node in tree.body
                      if isinstance(node, ast.AsyncFunctionDef)
                      and node.name == "execute_moderation_report_action")
        branch = next(node for node in method.body
                      if isinstance(node, ast.If) and ast.unparse(node.test) == "action == 'report'")
        purges = [node for node in ast.walk(method)
                  if isinstance(node, ast.Call)
                  and isinstance(node.func, ast.Name)
                  and node.func.id == "run_purge_job"]
        self.assertEqual(len(purges), 1)
        self.assertLess(branch.lineno, purges[0].lineno)


if __name__ == "__main__":
    unittest.main()
