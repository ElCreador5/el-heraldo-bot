"""Regresiones del acceso /setup -> Mensajes -> Programaciones (sin Discord real)."""
from datetime import datetime, timedelta, timezone
import asyncio
import unittest
from types import SimpleNamespace as NS
from unittest.mock import AsyncMock

from test_safety_regressions import b
import autofeed_setup as setup
import message_autofeeds as feeds
from message_automation import next_occurrence


class SetupNavigationTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.guild_id = 901
        self.owner_id = 10
        self.original = b.guild_config_get(self.guild_id, feeds.CONFIG_KEY)

    async def test_setup_messages_schedules_opens_hub_in_same_message(self):
        view = b.HeraldoMessagesSetupView(self.guild_id, self.owner_id)
        interaction = NS(
            guild=NS(id=self.guild_id),
            user=NS(id=self.owner_id,
                    guild_permissions=b.discord.Permissions(manage_guild=True)),
            data={"values": ["schedules"]},
            response=NS(send_message=AsyncMock(), edit_message=AsyncMock()),
        )
        await view.open_editor(interaction)
        interaction.response.send_message.assert_not_awaited()
        _, kwargs = interaction.response.edit_message.call_args
        self.assertIsInstance(kwargs["view"], setup.AutofeedHubView)
        self.assertEqual(kwargs["embed"], None)
        self.assertEqual(b.guild_config_get(self.guild_id, feeds.CONFIG_KEY), self.original)

    async def test_setup_hub_has_direct_editor_with_expected_controls(self):
        hub = setup.AutofeedHubView(b.__dict__, self.guild_id, self.owner_id)
        editor = setup.AutofeedEditorView(b.__dict__, self.guild_id, self.owner_id)
        self.assertTrue(any(getattr(item, "label", "") == setup.t("new") for item in hub.children))
        labels = [getattr(item, "label", "") for item in editor.children]
        for key in ("message", "embed", "schedule", "silent", "save", "discard", "back"):
            self.assertIn(setup.t(key), labels)
        self.assertEqual([x.row for x in editor.children if isinstance(x, (b.discord.ui.ChannelSelect, b.discord.ui.RoleSelect))], [0, 1])
        self.assertEqual(len(editor.children), 10)
        self.assertEqual(b.guild_config_get(self.guild_id, feeds.CONFIG_KEY), self.original)

    async def test_back_returns_exact_parent_from_setup(self):
        content, hub = setup.setup_panel(b.__dict__, self.guild_id, self.owner_id)
        interaction = NS(
            guild=NS(id=self.guild_id),
            user=NS(id=self.owner_id,
                    guild_permissions=b.discord.Permissions(manage_guild=True)),
            response=NS(edit_message=AsyncMock(), send_message=AsyncMock()),
        )
        await hub.back.callback(interaction)
        kwargs = interaction.response.edit_message.call_args.kwargs
        self.assertIsInstance(kwargs["view"], b.HeraldoMessagesSetupView)
        self.assertEqual(kwargs["content"], b.heraldo_messages_setup_content())


class CarlStyleFieldsTests(unittest.TestCase):
    def test_repeat_fields_and_limit(self):
        self.assertIsNone(setup.repeat_parts(0, 0, 0, 0))
        self.assertEqual(
            setup.repeat_parts(2, 3, 4, 5),
            {"months": 2, "days": 3, "hours": 4, "minutes": 5},
        )
        for values in [(-1, 0, 0, 0), (0, 0, 0, 59), (0, 0, 0, 1),
                       (0, 0, 0, -1), (121, 0, 0, 0)]:
            with self.subTest(values=values), self.assertRaises(ValueError):
                setup.repeat_parts(*values)

    def test_next_custom_months_and_intervals(self):
        start = "2027-01-31T10:00:00+00:00"
        job = dict(start=start, zone="UTC", repeat="custom",
                   repeat_parts=setup.repeat_parts(1, 0, 0, 0))
        next_time = next_occurrence(job, datetime(2027, 2, 1, tzinfo=timezone.utc))
        self.assertEqual(next_time, "2027-02-28T10:00:00+00:00")
        job["repeat_parts"] = setup.repeat_parts(0, 1, 2, 30)
        next_time = next_occurrence(job, datetime(2027, 1, 31, 11, tzinfo=timezone.utc))
        self.assertEqual(next_time, "2027-02-01T12:30:00+00:00")

    def test_draft_does_not_write_before_confirmation(self):
        host = b.__dict__
        start = b.guild_config_get(901, feeds.CONFIG_KEY)
        editor = setup.AutofeedEditorView(host, 901, 10)
        editor.channel_id = 11
        editor.text = "Recordatorio de prueba"
        editor.start = datetime.now(timezone.utc) + timedelta(days=3)
        editor.parts = setup.repeat_parts(0, 7, 0, 0)
        self.assertEqual(b.guild_config_get(901, feeds.CONFIG_KEY), start)


if __name__ == "__main__":
    unittest.main()
