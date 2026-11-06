"""Validate manual batch progress without Discord Gateway or destructive actions."""
from __future__ import annotations

import ast
import asyncio
import unittest
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import AsyncMock, Mock

from i18n_source_helpers import source_text


SOURCE = source_text(Path(__file__).resolve().parents[1] / "bot.py", encoding="utf-8")
TREE = ast.parse(SOURCE)


def method(name):
    matches = [
        node for node in TREE.body
        if isinstance(node, ast.AsyncFunctionDef) and node.name == name
    ]
    if len(matches) != 1:
        raise AssertionError(name)
    return matches[0]


def isolated_sync(namespace):
    node = method("sync_join_roles")
    module = ast.fix_missing_locations(ast.Module(
        body=[
            ast.ImportFrom(
                module="__future__", names=[ast.alias(name="annotations")], level=0,
            ),
            node,
        ],
        type_ignores=[],
    ))
    exec(compile(module, "<join-role-progress>", "exec"), namespace)
    return namespace["sync_join_roles"]


class BulkProgressIntegrationTests(unittest.IsolatedAsyncioTestCase):
    async def test_join_role_progress_reports_real_counts_and_retains_return_contract(self):
        members = [NS(bot=bot, id=index) for index, bot in
                   enumerate((True, False, False, False), 1)]

        class Guild:
            id = 12

            async def fetch_members(self, limit=None):
                for member in members:
                    yield member

        assign = AsyncMock(side_effect=[
            (True, "Asignados 1"),
            (True, "Ninguno"),
            (False, "Sin permisos"),
        ])
        last = Mock()
        namespace = {
            "_join_verify_pending_ids": lambda gid: set(),
            "_assign_join_roles_now": assign,
            "set_join_sync_last": last,
            "asyncio": NS(sleep=AsyncMock()),
        }
        sync = isolated_sync(namespace)
        updates = []

        async def progress(*counts):
            updates.append(counts)

        result = await sync(Guild(), progress=progress)
        self.assertEqual(result, (1, 1, ["namespace(bot=False, id=4): Sin permisos"]))
        self.assertEqual(updates, [
            (1, 0, 0, 0),
            (2, 1, 0, 0),
            (3, 1, 1, 0),
            (4, 1, 1, 1),
        ])
        self.assertEqual(assign.await_count, 3)
        last.assert_called_once_with(12)

    def test_verification_manual_batch_updates_existing_panel(self):
        code = ast.get_source_segment(SOURCE, method("heraldo_check_all"))
        self.assertIn('"verification"', code)
        self.assertIn("await reporter.publish(progress_status())", code)
        self.assertIn("await interaction.edit_original_response(", code)
        self.assertNotIn("interaction.followup.send(", code)

    def test_entry_role_manual_batch_does_not_send_extra_cards(self):
        code = ast.get_source_segment(SOURCE, method("joinroles_sync_command"))
        self.assertIn("_JOIN_ROLES_MANUAL_ACTIVE", code)
        self.assertIn("progress=update_progress", code)
        self.assertIn("await interaction.edit_original_response(content=result)", code)
        self.assertNotIn("interaction.followup.send(", code)


if __name__ == "__main__":
    unittest.main()
