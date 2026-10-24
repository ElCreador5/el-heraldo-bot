"""Clics y publicaciones concurrentes: sin escritura ni Discord reales."""
import asyncio
import unittest
from types import SimpleNamespace as NS
from unittest.mock import AsyncMock, MagicMock, patch

from test_safety_regressions import b, interaction


class HoneypotConcurrencyTests(unittest.IsolatedAsyncioTestCase):
    async def test_save_blocks_other_click_until_slow_warning_finishes(self):
        state = {"action": "log"}
        traps = {}
        entered, release = asyncio.Event(), asyncio.Event()
        channel = MagicMock(spec=b.discord.TextChannel)
        channel.id, channel.mention = 51, "<#51>"
        channel.permissions_for.return_value = NS(view_channel=True, send_messages=True,
                                                manage_messages=True)
        first, second = interaction(), interaction()
        first.guild.me = NS()
        first.guild.get_channel = lambda cid: channel
        async def warning(current):
            entered.set()
            await release.wait()
        def write(gid, name, value):
            if name == "honeypot_action":
                state["action"] = value
        with (
            patch.object(b, "hp_traps", side_effect=lambda gid: dict(traps)),
            patch.object(b, "hp_action", side_effect=lambda gid: state["action"]),
            patch.object(b, "honeypot_enabled", return_value=False),
            patch.object(b, "hp_protected_channel_reason", return_value=None),
            patch.object(b, "hp_add_trap", side_effect=lambda gid, cid: traps.update({cid: None})) as add,
            patch.object(b, "hp_setting_set", side_effect=write) as save,
            patch.object(b, "hp_sync_warning", side_effect=warning),
            patch.object(b, "hp_setup_embed", return_value=b.discord.Embed()),
        ):
            view = b.HeraldoHoneypotSetupView(901, 10)
            view.pending_trap_id, view.pending_action = 51, "timeout"
            task = asyncio.create_task(view._save_pending_changes(first))
            await entered.wait()
            await view._save_pending_changes(second)
            await view.discard_changes.callback(interaction())
            release.set()
            await task
            add.assert_called_once()
            save.assert_called_once_with(901, "honeypot_action", "timeout")
            self.assertIn("en curso", second.followup.send.call_args.args[0])

    async def test_concurrent_warning_sync_creates_one_message(self):
        entered, release = asyncio.Event(), asyncio.Event()
        traps = {51: None}
        channel = MagicMock(spec=b.discord.TextChannel)
        channel.guild, channel.id, channel.mention = NS(id=901), 51, "<#51>"
        message = NS(id=100, pinned=True, edit=AsyncMock(), pin=AsyncMock())
        async def send(**kwargs):
            entered.set()
            await release.wait()
            return message
        async def history(**kwargs):
            if False:
                yield None
        channel.send = AsyncMock(side_effect=send)
        channel.fetch_message = AsyncMock(return_value=message)
        channel.history = history
        with (
            patch.object(b, "hp_traps", side_effect=lambda gid: dict(traps)),
            patch.object(b, "hp_warning_enabled", return_value=True),
            patch.object(b, "hp_warning_embed", return_value=b.discord.Embed()),
            patch.object(b, "hp_set_warning_message", side_effect=lambda gid, cid, mid: traps.update({cid: mid})),
        ):
            first = asyncio.create_task(b.hp_sync_warning(channel))
            await entered.wait()
            second = asyncio.create_task(b.hp_sync_warning(channel))
            release.set()
            self.assertEqual(await asyncio.gather(first, second), [None, None])
        channel.send.assert_awaited_once()
        message.edit.assert_awaited_once()
        self.assertEqual(traps[51], 100)

    async def test_failed_pin_keeps_message_id_for_retry(self):
        traps = {51: None}
        channel = MagicMock(spec=b.discord.TextChannel)
        channel.guild, channel.id, channel.mention = NS(id=901), 51, "<#51>"
        error = b.discord.Forbidden(NS(status=403, reason="Forbidden"), "Missing permissions")
        message = NS(id=100, pinned=False, edit=AsyncMock(), pin=AsyncMock(side_effect=error))
        channel.send = AsyncMock(return_value=message)
        channel.fetch_message = AsyncMock(return_value=message)
        with (
            patch.object(b, "hp_traps", side_effect=lambda gid: dict(traps)),
            patch.object(b, "hp_warning_enabled", return_value=True),
            patch.object(b, "hp_warning_embed", return_value=b.discord.Embed()),
            patch.object(b, "hp_set_warning_message", side_effect=lambda gid, cid, mid: traps.update({cid: mid})),
        ):
            self.assertIn("permisos", await b.hp_sync_warning(channel))
            self.assertEqual(traps[51], 100)
            message.pin.side_effect = None
            self.assertIsNone(await b.hp_sync_warning(channel))
        channel.send.assert_awaited_once()


if __name__ == "__main__":
    unittest.main()
