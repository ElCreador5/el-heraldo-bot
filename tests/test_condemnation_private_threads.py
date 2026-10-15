"""Regresiones offline: hilo privado asociado a tarjeta de condena existente."""
from __future__ import annotations

import ast
import asyncio
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, MagicMock


SOURCE = Path(__file__).resolve().parents[1] / "bot.py"


class DiscordError(Exception):
    pass


class FakeThread:
    def __init__(self, parent_id=20, kind="private"):
        self.parent_id = parent_id
        self.type = kind
        self.id = 30
        self.jump_url = "https://discord.com/channels/10/30"
        self.archived = False
        self.add_user = AsyncMock()
        self.edit = AsyncMock()
        self.send = AsyncMock()


class FakeChannel:
    def __init__(self):
        self.id = 20
        self.perms = SimpleNamespace(
            view_channel=True, read_message_history=True, send_messages_in_threads=True,
            create_private_threads=True, manage_threads=False,
        )
        self.create_thread = AsyncMock(return_value=FakeThread())
        self.fetch_message = AsyncMock(return_value=SimpleNamespace(
            edit=AsyncMock(), jump_url="https://discord.com/channels/10/20/70"))
        self.permissions_for = lambda who: self.perms


def isolated(*names):
    tree = ast.parse(SOURCE.read_text("utf-8"), filename=str(SOURCE))
    selected = [n for n in tree.body if isinstance(n, (ast.AsyncFunctionDef, ast.FunctionDef))
                and n.name in names]
    assert len(selected) == len(names)
    code = ast.Module(body=[ast.ImportFrom(module="__future__", names=[
        ast.alias(name="annotations")], level=0), *selected], type_ignores=[])
    return compile(ast.fix_missing_locations(code), str(SOURCE), "exec")


class ThreadTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.ns = {}
        self.channel = FakeChannel()
        self.member = SimpleNamespace(id=40)
        self.me = SimpleNamespace(id=50)
        self.guild = SimpleNamespace(
            id=10, me=self.me, get_channel=lambda c: self.channel,
            get_thread=lambda c: None, fetch_channel=AsyncMock(return_value=FakeThread()),
            fetch_member=AsyncMock(return_value=self.member),
        )
        self.row = {"thread_requested": 1, "announcement_message_id": 70, "thread_id": None}
        self.ns.update(
            discord=SimpleNamespace(
                TextChannel=FakeChannel, Thread=FakeThread,
                ChannelType=SimpleNamespace(private_thread="private"),
                Forbidden=DiscordError, NotFound=DiscordError, HTTPException=DiscordError,
                Color=SimpleNamespace(orange=lambda: "orange"),
                AllowedMentions=SimpleNamespace(none=lambda: None),
            ),
            asyncio=asyncio,
            condensation_unneeded=None,
            condensation_token=None,
            condemnation_get=lambda guild_id, user_id: self.row,
            condemnation_channel_id=lambda guild_id: 20,
            condemnation_thread_save_id=MagicMock(return_value=True),
            condemnation_thread_view=MagicMock(return_value="view-with-thread-link"),
            condemnation_fetch_private_thread=AsyncMock(return_value=FakeThread()),
            log_embed=AsyncMock(),
            print=lambda *_: None,
            condemnation_list=lambda guild_id: [],
        )
        exec(isolated("condemnation_ensure_private_thread", "condemnation_close_private_thread"), self.ns)

    async def call_ensure(self):
        return await self.ns["condemnation_ensure_private_thread"](
            self.guild, self.member, 70, "X1Y2Z3A"
        )

    async def test_private_thread_only_after_existing_card(self):
        self.assertTrue(await self.call_ensure())
        kwargs = self.channel.create_thread.await_args.kwargs
        self.assertEqual(kwargs["type"], "private")
        self.assertFalse(kwargs["invitable"])
        self.assertNotIn("message", kwargs)
        self.channel.fetch_message.assert_awaited_once_with(70)
        self.ns["condemnation_thread_save_id"].assert_called_once()
        self.channel.create_thread.return_value.add_user.assert_awaited_once_with(self.member)
        self.channel.create_thread.return_value.send.assert_awaited_once()
        self.channel.fetch_message.return_value.edit.assert_awaited_once_with(
            view="view-with-thread-link"
        )

    async def test_existing_thread_reinvites_after_restart_without_creating_new(self):
        self.row["thread_id"] = 30
        self.assertTrue(await self.call_ensure())
        self.channel.create_thread.assert_not_awaited()
        self.ns["condemnation_fetch_private_thread"].assert_awaited_once_with(
            self.guild, 30
        )

    async def test_old_cards_are_not_migrated(self):
        self.row["thread_requested"] = 0
        self.assertFalse(await self.call_ensure())
        self.channel.create_thread.assert_not_awaited()

    async def test_no_thread_when_member_cannot_read_history(self):
        self.channel.perms.read_message_history = False
        self.assertFalse(await self.call_ensure())
        self.channel.create_thread.assert_not_awaited()
        self.ns["log_embed"].assert_awaited()

    async def test_staff_like_member_cannot_access_other_private_threads(self):
        self.channel.perms.manage_threads = True
        self.assertFalse(await self.call_ensure())
        self.channel.create_thread.assert_not_awaited()

    async def test_if_condemnation_replaced_new_thread_is_immediately_archived(self):
        self.ns["condemnation_thread_save_id"].return_value = False
        self.assertFalse(await self.call_ensure())
        self.channel.create_thread.return_value.edit.assert_awaited_once()
        self.assertTrue(self.channel.create_thread.return_value.edit.await_args.kwargs["archived"])

    async def test_denied_thread_api_does_not_cancel_condemnation(self):
        self.channel.create_thread.side_effect = DiscordError("sin permiso")
        self.assertFalse(await self.call_ensure())
        self.ns["log_embed"].assert_awaited_once()

    async def test_resolution_archives_without_deleting_history(self):
        thread = FakeThread()
        self.ns["condemnation_fetch_private_thread"].return_value = thread
        await self.ns["condemnation_close_private_thread"](self.guild, 30)
        thread.send.assert_awaited_once()
        thread.edit.assert_awaited_once()
        self.assertTrue(thread.edit.await_args.kwargs["archived"])
        self.assertTrue(thread.edit.await_args.kwargs["locked"])

    def test_setup_duration_presets_require_explicit_confirmation(self):
        src = SOURCE.read_text("utf-8")
        tree = ast.parse(src)
        view = next(n for n in tree.body if isinstance(n, ast.ClassDef)
                    and n.name == "HeraldoCondemnationSetupView")
        choice = next(n for n in view.body if isinstance(n, ast.AsyncFunctionDef)
                      and n.name == "select_duration")
        calls = [n.func.id for n in ast.walk(choice) if isinstance(n, ast.Call)
                 and isinstance(n.func, ast.Name)]
        self.assertIn("confirm_configuration", calls)
        self.assertNotIn("guild_config_set", calls)
        self.assertIn("row=4", src)
        self.assertIn('value="custom"', src)

    def test_channel_permissions_only_after_confirm(self):
        src = SOURCE.read_text("utf-8")
        tree = ast.parse(src)
        view = next(n for n in tree.body if isinstance(n, ast.ClassDef)
                    and n.name == "CondemnationChannelAccessConfirmView")
        funcs = {n.name: n for n in view.body if isinstance(n, ast.AsyncFunctionDef)}
        self.assertIn("confirm", funcs)
        self.assertIn("cancel", funcs)
        self.assertIn("set_permissions", ast.unparse(funcs["confirm"]))
        self.assertNotIn("set_permissions", ast.unparse(funcs["cancel"]))

    def test_embed_unchanged_and_ping_precedes_thread(self):
        src = SOURCE.read_text("utf-8")
        tree = ast.parse(src)
        func = next(n for n in tree.body if isinstance(n, ast.AsyncFunctionDef)
                    and n.name == "_condemn_member_inner")
        calls = [n.func.id for n in ast.walk(func) if isinstance(n, ast.Call)
                 and isinstance(n.func, ast.Name)]
        self.assertIn("condemnation_announce", calls)
        self.assertIn("condemnation_ensure_private_thread", calls)
        start = src.index("async def condemnation_announce(")
        end = src.index("async def condemnation_update_pardoned_card(", start)
        self.assertIn("content=member.mention, embed=embed, view=view", src[start:end])
        self.assertIn("AllowedMentions(users=[member]", src[start:end])
        self.assertIn("thread_requested INTEGER NOT NULL DEFAULT 0", src)

if __name__ == "__main__":
    unittest.main()
