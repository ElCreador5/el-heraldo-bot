"""Offline regression checks for main-only progress promotion.

No Discord Gateway, production token, database writes or live moderation calls.
"""
from __future__ import annotations

import ast
import unittest
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import AsyncMock, Mock

from operation_progress import compact_operation_status, compact_progress_bar, status_text


ROOT = Path(__file__).resolve().parents[1]
BOT_SOURCE = (ROOT / "bot.py").read_text(encoding="utf-8")
BOT_TREE = ast.parse(BOT_SOURCE)


def function(name):
    found = [node for node in BOT_TREE.body
             if isinstance(node, ast.AsyncFunctionDef) and node.name == name]
    if len(found) != 1:
        raise AssertionError(name)
    return found[0]


class MainProgressTests(unittest.IsolatedAsyncioTestCase):
    def test_compact_status_for_each_operation_and_locale(self):
        counters = {
            "purge_scan": dict(examined=100, found=6),
            "purge_delete": dict(deleted=18, failed=2),
            "fusion": dict(migrated=17, failed=3, attachments=1),
            "join_roles": dict(assigned=9, skipped=7, failed=4),
            "verification": dict(verified=5, expelled=2, failed=0),
        }
        for locale in ("es-419", "en-US", "pt-BR"):
            for operation, values in counters.items():
                result = compact_operation_status(
                    locale, operation, 20, 30, **values
                )
                self.assertIn("20 / 30", result)
                self.assertIn("66%", result)
                self.assertEqual(result.count("\n"), 3)
                self.assertLess(len(result), 220)
                unknown = compact_operation_status(
                    locale, operation, 20, None, **values
                )
                self.assertNotIn("%", unknown)
        self.assertEqual(compact_progress_bar(30, 30)[1], 99)
        self.assertIn("Discord", status_text("es-419", "template_running"))

    async def test_join_role_progress_counts_real_members_and_retains_return(self):
        target = function("sync_join_roles")
        module = ast.fix_missing_locations(ast.Module(
            body=[ast.ImportFrom(
                module="__future__", names=[ast.alias(name="annotations")],
                level=0
            ), target],
            type_ignores=[],
        ))
        guild = NS(id=901)
        members = [NS(id=i, bot=(i == 1)) for i in range(1, 5)]

        async def fetch_members(limit=None):
            for member in members:
                yield member

        guild.fetch_members = fetch_members
        assign = AsyncMock(side_effect=[
            (True, "Asignados 1"), (True, "No hay roles"),
            (False, "Permisos insuficientes"),
        ])
        done = Mock()
        namespace = {
            "_join_verify_pending_ids": lambda guild_id: set(),
            "_assign_join_roles_now": assign,
            "set_join_sync_last": done,
            "asyncio": NS(sleep=AsyncMock()),
        }
        exec(compile(module, "bot-progress.py", "exec"), namespace)
        updates = []

        async def progress(*counts):
            updates.append(counts)

        result = await namespace["sync_join_roles"](guild, progress=progress)
        self.assertEqual(result[0:2], (1, 1))
        self.assertEqual(len(result[2]), 1)
        self.assertEqual(updates, [
            (1, 0, 0, 0),
            (2, 1, 0, 0),
            (3, 1, 1, 0),
            (4, 1, 1, 1),
        ])
        done.assert_called_once_with(901)
        self.assertEqual(assign.await_count, 3)

    def test_fusion_preserves_its_existing_safety_and_audit(self):
        code = ast.get_source_segment(BOT_SOURCE, function("execute_channel_merge"))
        self.assertIn("await reporter.publish(merge_status())", code)
        self.assertIn("await interaction.edit_original_response(", code)
        self.assertNotIn("progress_message", code)
        self.assertIn("if failed == 0 and attachment_failures == 0 and eliminar_origen:", code)
        self.assertIn("await origen.delete(", code)
        self.assertIn("await log_embed(", code)

    def test_bulk_verification_keeps_actions_and_edits_original(self):
        code = ast.get_source_segment(BOT_SOURCE, function("heraldo_check_all"))
        self.assertIn("await member.kick(", code)
        self.assertIn("await reporter.publish(progress_status())", code)
        self.assertIn("await interaction.edit_original_response(", code)
        self.assertNotIn("interaction.followup.send(", code)

    def test_template_never_claims_a_fake_percentage(self):
        source = (ROOT / "server_structure_setup.py").read_text("utf-8")
        tree = ast.parse(source)
        node = next(
            item for item in tree.body
            if isinstance(item, ast.ClassDef) and item.name == "StructureSyncConfirmView"
        )
        method = next(item for item in node.body
                      if isinstance(item, ast.AsyncFunctionDef) and item.name == "execute")
        code = ast.get_source_segment(source, method)
        self.assertIn('"template_running"', code)
        self.assertIn("interaction.response.edit_message(", code)
        self.assertIn("interaction.edit_original_response(", code)
        self.assertIn('host["template_report_embed"](template, dirty, "manual")', code)
        self.assertNotIn("progress_bar(", code)


if __name__ == "__main__":
    unittest.main()
