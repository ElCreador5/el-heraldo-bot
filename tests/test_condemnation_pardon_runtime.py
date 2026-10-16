"""Ensayos aislados de la edición REAL del mensaje, sin iniciar bot ni tocar Discord."""
from __future__ import annotations

import ast
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
import traceback
import unittest
from unittest.mock import AsyncMock, MagicMock


SOURCE = Path(__file__).resolve().parents[1] / "bot.py"


def isolated_card():
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"), filename=str(SOURCE))
    selected = [node for node in tree.body if isinstance(node, ast.AsyncFunctionDef)
                and node.name == "condemnation_update_pardoned_card"]
    assert len(selected) == 1
    code = ast.Module(
        body=[ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0), *selected],
        type_ignores=[],
    )
    return compile(ast.fix_missing_locations(code), str(SOURCE), "exec")


class FakeDiscordHTTP(Exception):
    pass


class FakeEmbed:
    def __init__(self, *, title, description, color, timestamp):
        self.title = title
        self.description = description
        self.fields = []
    def add_field(self, *, name, value, inline):
        self.fields.append((name, value, inline))
    def set_thumbnail(self, *, url):
        self.thumbnail = url
    def set_footer(self, *, text):
        self.footer = text


class FakeChannel:
    def __init__(self):
        self.id = 21
        self.fetch_message = AsyncMock()


class PardonCardRuntimeTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.channel = FakeChannel()
        self.message = SimpleNamespace(channel=self.channel, edit=AsyncMock())
        self.channel.fetch_message.return_value = self.message
        self.guild = SimpleNamespace(
            id=10, name="Laboratorio",
            get_channel=MagicMock(return_value=self.channel),
            fetch_channel=AsyncMock(return_value=self.channel),
        )
        self.member = SimpleNamespace(
            id=7, guild=self.guild, mention="<@7>",
            display_avatar=SimpleNamespace(url="https://example.invalid/avatar.png"),
        )
        self.row = {
            "announcement_message_id": 71,
            "condemned_at": "2026-10-15T00:00:00+00:00",
            "moderation_case_number": 1,
            "reason": "Prueba aislada",
        }
        self.pardoner = SimpleNamespace(mention="<@8>")
        self.ns = dict(
            discord=SimpleNamespace(
                TextChannel=FakeChannel, HTTPException=FakeDiscordHTTP,
                NotFound=FakeDiscordHTTP, Forbidden=FakeDiscordHTTP,
                Embed=FakeEmbed, Color=SimpleNamespace(green=lambda: 1),
                AllowedMentions=SimpleNamespace(none=lambda: "none"),
                utils=SimpleNamespace(format_dt=lambda *args: "fecha"),
            ),
            condemnation_channel_id=lambda gid: 21,
            condemnation_case_id=lambda *args: "5L138ZJ",
            condemnation_duration_text=lambda row: "2 minutos",
            datetime=datetime, timezone=timezone, traceback=traceback,
        )
        exec(isolated_card(), self.ns)
        self.update = self.ns["condemnation_update_pardoned_card"]

    async def test_original_message_is_edited_not_reposted(self):
        ok = await self.update(self.member, self.row, self.pardoner, 6, 0, message=self.message)
        self.assertTrue(ok)
        self.message.edit.assert_awaited_once()
        options = self.message.edit.await_args.kwargs
        self.assertEqual(options["embed"].title, "CONDENA PERDONADA")
        self.assertIsNone(options["view"])
        self.assertIn(("Expediente", "`5L138ZJ`", True), options["embed"].fields)
        self.channel.fetch_message.assert_not_awaited()

    async def test_passed_message_succeeds_when_channel_is_not_cached(self):
        self.guild.get_channel.return_value = None
        ok = await self.update(self.member, self.row, self.pardoner, 6, 0, message=self.message)
        self.assertTrue(ok)
        self.guild.fetch_channel.assert_not_awaited()
        self.message.edit.assert_awaited_once()

    async def test_fetches_uncached_channel_when_message_not_provided(self):
        self.guild.get_channel.return_value = None
        ok = await self.update(self.member, self.row, self.pardoner, 6, 0)
        self.assertTrue(ok)
        self.guild.fetch_channel.assert_awaited_once_with(21)
        self.channel.fetch_message.assert_awaited_once_with(71)
        self.message.edit.assert_awaited_once()

    async def test_discord_edit_failure_is_reported_not_claimed_successful(self):
        self.message.edit.side_effect = FakeDiscordHTTP("access denied")
        ok = await self.update(self.member, self.row, self.pardoner, 6, 0, message=self.message)
        self.assertFalse(ok)

    async def test_wrong_channel_is_not_edited(self):
        self.message.channel = SimpleNamespace(id=99)
        ok = await self.update(self.member, self.row, self.pardoner, 6, 0, message=self.message)
        self.assertFalse(ok)
        self.message.edit.assert_not_awaited()

    def test_release_prioritizes_card_before_optional_thread_close(self):
        code = SOURCE.read_text(encoding="utf-8")
        block = code[code.index("async def _release_condemned_member_inner("):
                     code.index("async def check_expired_condemnations(", code.index("async def _release_condemned_member_inner("))]
        self.assertLess(block.index("card_ok = await condemnation_update_pardoned_card("),
                        block.index("await condemnation_close_private_thread("))
        self.assertIn('Condena perdonada — actualización visual pendiente', block)


if __name__ == "__main__":
    unittest.main()
