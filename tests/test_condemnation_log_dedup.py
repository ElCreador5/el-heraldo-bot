"""Regresiones del registro consolidado de condena y su purga.

Extrae solo las funciones necesarias: no importa el bot ni utiliza Discord/SQLite real.
"""
from i18n_source_helpers import source_text as _source_text
import ast
import asyncio
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock


BOT_SOURCE = Path(__file__).resolve().parents[1] / "bot.py"


class FakeDiscordError(Exception):
    pass


class FakeColor:
    @staticmethod
    def dark_red():
        return "dark_red"

    @staticmethod
    def green():
        return "green"

    @staticmethod
    def red():
        return "red"


def load_functions(*names):
    source = _source_text(BOT_SOURCE, encoding='utf-8')
    tree = ast.parse(source, filename=str(BOT_SOURCE))
    found = [node for node in tree.body if isinstance(node, ast.AsyncFunctionDef) and node.name in names]
    if {node.name for node in found} != set(names):
        raise AssertionError("Faltan funciones de condena/purga requeridas.")
    ns = {
        "discord": SimpleNamespace(
            Guild=object, Member=object, Message=object, abc=SimpleNamespace(User=object),
            HTTPException=FakeDiscordError,
            Color=FakeColor,
        ),
        "datetime": datetime,
        "PurgeResult": object,
        "run_purge_job": AsyncMock(),
        "log_embed": AsyncMock(),
        "purge_result_text": lambda result: f"{result.deleted} mensajes; {result.failed} fallidos",
        "build_log_template_embed": lambda guild, title, description, color: {
            "title": title, "description": description, "color": color,
        },
        "purge_user_messages": AsyncMock(),
        "_purge_running": set(),
        "traceback": SimpleNamespace(print_exc=lambda: None),
    }
    isolated = ast.Module(body=found, type_ignores=[])
    exec(compile(ast.fix_missing_locations(isolated), str(BOT_SOURCE), "exec"), ns)
    return ns


class ConsolidatedCondemnationLogTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.ns = load_functions("run_purge_job", "_complete_condemnation_purge_log")
        self.guild = SimpleNamespace(id=101)
        self.user = SimpleNamespace(id=202, mention="@miembro")
        self.message = SimpleNamespace(edit=AsyncMock())
        self.result = SimpleNamespace(deleted=5, failed=0, channels_scanned=2, channels_skipped=0)
        self.ns["purge_user_messages"].return_value = self.result

    async def run_condemnation_purge(self, message=None):
        return await self.ns["_complete_condemnation_purge_log"](
            self.guild, self.user, scope_text="última hora",
            requested_by="Condena (Reacción)",
            after=None, limit=5, base_description="Condena aplicada: motivo",
            log_message=message,
        )

    async def test_success_edits_original_log_once_without_second_embed(self):
        await self.run_condemnation_purge(self.message)
        self.message.edit.assert_awaited_once()
        embed = self.message.edit.await_args.kwargs["embed"]
        self.assertEqual(embed["title"], "Condena aplicada")
        self.assertIn("Purga: última hora", embed["description"])
        self.assertIn("5 mensajes", embed["description"])
        self.ns["log_embed"].assert_not_awaited()

    async def test_purge_remains_logged_when_initial_condemnation_log_is_unavailable(self):
        await self.run_condemnation_purge()
        self.ns["log_embed"].assert_awaited_once()
        self.assertEqual(self.ns["log_embed"].await_args.args[1], "Purga de condena completada")

    async def test_edited_message_failure_falls_back_to_auditable_purge_notice(self):
        self.message.edit.side_effect = FakeDiscordError("mensaje eliminado")
        await self.run_condemnation_purge(self.message)
        self.ns["log_embed"].assert_awaited_once()
        self.assertEqual(self.ns["log_embed"].await_args.args[1], "Purga de condena completada")

    async def test_failed_purge_updates_original_log_and_preserves_failure_log(self):
        self.ns["purge_user_messages"].side_effect = RuntimeError("simulación")
        await self.run_condemnation_purge(self.message)
        self.message.edit.assert_awaited_once()
        self.assertIn("Purga: fallida", self.message.edit.await_args.kwargs["embed"]["description"])
        self.assertEqual(self.ns["log_embed"].await_args.args[1], "Advertencia: Purga fallida")

    async def test_concurrent_purge_is_not_falsely_recorded_as_completed(self):
        self.ns["_purge_running"].add((self.guild.id, self.user.id))
        await self.run_condemnation_purge(self.message)
        self.message.edit.assert_awaited_once()
        self.assertIn("omitida", self.message.edit.await_args.kwargs["embed"]["description"])
        self.ns["purge_user_messages"].assert_not_awaited()
        self.ns["log_embed"].assert_not_awaited()

    async def test_unrelated_purge_still_generates_its_own_success_log(self):
        await self.ns["run_purge_job"](
            self.guild, self.user, scope_text="prueba", requested_by="Moderation"
        )
        self.ns["log_embed"].assert_awaited_once()
        self.assertEqual(self.ns["log_embed"].await_args.args[1], "Purga completada")

    def test_condemnation_handler_uses_consolidating_helper(self):
        source = _source_text(BOT_SOURCE, encoding='utf-8')
        tree = ast.parse(source)
        handler = next(
            n for n in tree.body
            if isinstance(n, ast.AsyncFunctionDef) and n.name == "_condemn_member_inner"
        )
        invoked = {
            n.func.id for n in ast.walk(handler)
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
        }
        self.assertIn("_complete_condemnation_purge_log", invoked)
        self.assertNotIn("run_purge_job", invoked)


if __name__ == "__main__":
    unittest.main()
