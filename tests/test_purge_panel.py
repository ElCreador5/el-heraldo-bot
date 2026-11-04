"""Regresiones aisladas para /purge sin conectar Discord ni eliminar mensajes reales."""
import unittest
from collections import Counter
from types import SimpleNamespace as NS
from unittest.mock import AsyncMock

import bot as b
from purge_panel import PurgePanel


class FakeChannel:
    def __init__(self, channel_id, messages=()):
        self.id = channel_id
        self.messages = list(messages)

    def permissions_for(self, _member):
        return NS(view_channel=True, read_message_history=True,
                  manage_messages=True, send_messages=True, embed_links=True)

    async def history(self, *, limit=None, after=None, before=None, oldest_first=None):
        for msg in sorted(self.messages, key=lambda msg: msg.id, reverse=not oldest_first):
            if after and msg.created_at <= after:
                continue
            if before and msg.created_at >= before:
                continue
            yield msg


class PurgePanelTests(unittest.IsolatedAsyncioTestCase):
    def make_panel(self):
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        def message(mid, uid):
            return NS(id=mid, author=NS(id=uid), created_at=now, content="hola", attachments=[])
        channels = {
            11: FakeChannel(11, [message(101, 1), message(98, 2), message(97, 1)]),
            12: FakeChannel(12, [message(110, 1), message(109, 2), message(108, 2)]),
            999: FakeChannel(999),
        }
        guild = NS(
            id=901, owner_id=50, me=NS(id=66),
            get_channel=lambda cid: channels.get(cid),
            get_thread=lambda cid: None,
        )
        user = NS(id=50, guild_permissions=NS(
            administrator=True, manage_messages=True, manage_guild=True,
        ))
        response = NS(
            defer=AsyncMock(), send_message=AsyncMock(), edit_message=AsyncMock(),
        )
        interaction = NS(
            guild=guild, user=user, response=response,
            followup=NS(send=AsyncMock()), edit_original_response=AsyncMock(),
        )
        async def targets(guild, only, after):
            return [only] if only else [channels[11], channels[12]]
        deleted = AsyncMock(return_value=True)
        logged = AsyncMock()
        running = set()
        panel = PurgePanel(
            interaction, language="es-419", footer=lambda g: ("El Heraldo's Labs 🧪", ""),
            targets=targets, matches=lambda msg, kind: True, delete=deleted, log=logged,
            parse_duration=lambda value, minimum, maximum: int(value),
            max_minutes=1000000, running=running, audit_channel_id=999,
        )
        return panel, interaction, channels, deleted, logged, running

    def test_purge_command_requires_no_slash_parameters(self):
        command = b.bot.tree.get_command("purge")
        self.assertIsNotNone(command)
        self.assertEqual(command.parameters, [])

    def test_selectors_and_close_exist_without_persistent_save(self):
        panel, _, _, _, _, _ = self.make_panel()
        self.assertEqual(len([x for x in panel.children if isinstance(x, b.discord.ui.UserSelect)]), 1)
        self.assertEqual(panel.user_select.max_values, 25)
        labels = [x.label for x in panel.children if isinstance(x, b.discord.ui.Button)]
        self.assertIn("Continuar", labels)
        self.assertIn("Cerrar", labels)
        self.assertNotIn("Guardar cambios", labels)

    async def test_preview_is_snapshot_with_per_user_global_limit(self):
        panel, interaction, channels, deleted, logged, running = self.make_panel()
        panel.user_ids = (1, 2)
        panel.limit = 1
        panel.invalidate()
        await panel.continue_scan(interaction)
        self.assertEqual(Counter(uid for _, _, uid in panel.snapshot), {1: 1, 2: 1})
        self.assertEqual({mid for _, mid, _ in panel.snapshot}, {110, 109})
        self.assertEqual(panel.scanned, 2)
        # A newly published message must never join a confirmed snapshot.
        channels[11].messages.append(NS(id=200, author=NS(id=1)))
        await panel.confirm(interaction)
        self.assertEqual({c.args[1] for c in deleted.await_args_list}, {110, 109})
        self.assertEqual(deleted.await_count, 2)
        self.assertEqual(logged.await_count, 1)
        self.assertFalse(running)
        self.assertTrue(panel.closed)

    async def test_changing_any_filter_invalidates_preview(self):
        panel, interaction, _, _, _, _ = self.make_panel()
        panel.user_ids = (1,)
        panel.limit = 2
        await panel.continue_scan(interaction)
        self.assertIsNotNone(panel.snapshot)
        panel.kind = "links"
        panel.invalidate()
        self.assertIsNone(panel.snapshot)

    async def test_no_users_cannot_preview_or_delete(self):
        panel, interaction, _, deleted, _, _ = self.make_panel()
        panel.limit = 2
        await panel.continue_scan(interaction)
        interaction.response.send_message.assert_awaited_once()
        self.assertIsNone(panel.snapshot)
        deleted.assert_not_awaited()

    async def test_existing_purge_job_blocks_simultaneous_confirmation(self):
        panel, interaction, _, deleted, logged, running = self.make_panel()
        panel.user_ids = (1,)
        panel.limit = 2
        await panel.continue_scan(interaction)
        running.add((901, 1))
        await panel.confirm(interaction)
        deleted.assert_not_awaited()
        logged.assert_not_awaited()
        self.assertFalse(panel.closed)


if __name__ == "__main__":
    unittest.main()
