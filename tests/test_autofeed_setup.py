"""Regresiones de /setup -> AutoFeeds independiente de Mensajes (sin Gateway)."""
from datetime import datetime, timedelta, timezone
import asyncio
import unittest
from types import SimpleNamespace as NS
from unittest.mock import AsyncMock, patch

from test_safety_regressions import b
import autofeed_setup as setup
import message_autofeeds as feeds
from message_automation import next_occurrence


class SetupNavigationTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.guild_id = 901
        self.owner_id = 10
        self.original = b.guild_config_get(self.guild_id, feeds.CONFIG_KEY)

    async def test_setup_messages_hides_create_message_and_preserves_editors(self):
        view = b.HeraldoMessagesSetupView(self.guild_id, self.owner_id)
        options = {option.value for option in view.panel_select.options}
        self.assertNotIn("create_message", options)
        self.assertTrue({"verification", "verify_dm", "suggestions",
                         "honeypot", "condemnation", "logs", "templates"}.issubset(options))
        interaction = NS(
            guild=NS(id=self.guild_id),
            user=NS(id=self.owner_id,
                    guild_permissions=b.discord.Permissions(manage_guild=True)),
            data={"values": ["create_message"]},
            response=NS(send_message=AsyncMock(), edit_message=AsyncMock()),
        )
        await view.open_editor(interaction)
        interaction.response.send_message.assert_awaited_once()
        interaction.response.edit_message.assert_not_awaited()
        self.assertEqual(b.guild_config_get(self.guild_id, feeds.CONFIG_KEY), self.original)

    async def test_create_message_has_single_editor_with_expected_controls(self):
        editor = setup.AutofeedEditorView(b.__dict__, self.guild_id, self.owner_id)
        labels = [getattr(item, "label", "") for item in editor.children]
        for key in ("message", "show_embed", "date_picker", "repeat_picker",
                    "insert_mention", "silent", "send", "back"):
            self.assertIn(setup.t(key), labels)
        self.assertEqual([x.row for x in editor.children if isinstance(x, (b.discord.ui.ChannelSelect, b.discord.ui.RoleSelect))], [0, 1])
        self.assertEqual(len(editor.children), 11)
        self.assertNotIn(setup.t("discard"), labels)
        self.assertIsNone(editor.start)
        self.assertIn(setup.t("notice"), editor.summary())
        self.assertIsInstance(setup.DateTimeModal(editor), b.discord.ui.Modal)
        self.assertIsInstance(setup.FrequencyPickerView(editor), b.discord.ui.View)
        self.assertEqual(b.guild_config_get(self.guild_id, feeds.CONFIG_KEY), self.original)

    def interaction(self):
        return NS(
            guild=NS(id=self.guild_id),
            user=NS(id=self.owner_id, guild_permissions=b.discord.Permissions(manage_guild=True)),
            response=NS(edit_message=AsyncMock(), send_message=AsyncMock()),
            data={"values": ["autofeeds"]},
        )

    async def test_autofeeds_is_a_separate_setup_module(self):
        root = b.HeraldoSetupView(self.guild_id, self.owner_id)
        self.assertIn("autofeeds", {opt.value for opt in root.module_select.options})
        messages = b.HeraldoMessagesSetupView(self.guild_id, self.owner_id)
        self.assertNotIn("autofeeds", {opt.value for opt in messages.panel_select.options})
        i = self.interaction()
        await root.select_module(i)
        self.assertIsInstance(i.response.edit_message.call_args.kwargs["view"], setup.AutoFeedsHomeView)
        self.assertEqual(b.guild_config_get(self.guild_id, feeds.CONFIG_KEY), self.original)

    async def test_autofeeds_home_is_not_the_message_editor(self):
        content, home = setup.setup_panel(b.__dict__, self.guild_id, self.owner_id)
        self.assertIsInstance(home, setup.AutoFeedsHomeView)
        self.assertIn(setup.t("hub_title"), content)
        self.assertEqual([c.label for c in home.children],
                         [setup.t(k) for k in ("new", "manage", "permissions", "back")])
        i = self.interaction()
        await home.create.callback(i)
        editor = i.response.edit_message.call_args.kwargs["view"]
        self.assertIsInstance(editor, setup.AutofeedEditorView)
        i.response.edit_message.reset_mock()
        await editor.back.callback(i)
        self.assertIsInstance(i.response.edit_message.call_args.kwargs["view"], setup.AutoFeedsHomeView)
        i.response.edit_message.reset_mock()
        await home.back.callback(i)
        self.assertIsInstance(i.response.edit_message.call_args.kwargs["view"], b.HeraldoSetupView)
        self.assertEqual(b.guild_config_get(self.guild_id, feeds.CONFIG_KEY), self.original)

    async def test_manage_and_permissions_return_to_autofeeds_without_writes(self):
        content, home = setup.setup_panel(b.__dict__, self.guild_id, self.owner_id)
        i = self.interaction()
        with patch.object(feeds, "get_jobs", return_value=[]):
            await home.manage.callback(i)
        self.assertIsInstance(i.response.edit_message.call_args.kwargs["view"], setup.AutoFeedsHomeView)
        self.assertIn(feeds.tr("no_jobs"), i.response.edit_message.call_args.kwargs["content"])
        i.response.edit_message.reset_mock()
        await home.permissions.callback(i)
        policy = i.response.edit_message.call_args.kwargs["view"]
        self.assertIsInstance(policy, feeds.PolicyView)
        self.assertTrue(policy.return_to_setup)
        i.response.edit_message.reset_mock()
        await policy.back.callback(i)
        self.assertIsInstance(i.response.edit_message.call_args.kwargs["view"], setup.AutoFeedsHomeView)
        # También /programar configurar conserva la independencia de Mensajes.
        i.response.edit_message.reset_mock()
        command_policy = feeds.PolicyView(b.__dict__, self.guild_id, self.owner_id)
        await command_policy.back.callback(i)
        self.assertIsInstance(i.response.edit_message.call_args.kwargs["view"], setup.AutoFeedsHomeView)
        self.assertEqual(b.guild_config_get(self.guild_id, feeds.CONFIG_KEY), self.original)


    async def test_editor_draft_requires_confirmation_not_persistence(self):
        editor = setup.AutofeedEditorView(b.__dict__, 901, 10)
        prior = b.guild_config_get(901, feeds.CONFIG_KEY)
        editor.text = "Ejemplo"
        editor.dirty = True
        self.assertIn(editor.discard, editor.children)
        self.assertEqual(b.guild_config_get(901, feeds.CONFIG_KEY), prior)
        editor.dirty = False
        self.assertNotIn(editor.discard, editor.children)

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

    def test_mention_picker_inserts_guild_mention_in_correct_field(self):
        editor = setup.AutofeedEditorView(b.__dict__, 901, 10)
        picker = setup.MentionPickerView(editor)
        picker.insert("<#123456789012345678>")
        self.assertEqual(editor.text, "<#123456789012345678>")
        picker.destination = "embed"
        picker.insert("<@&987654321012345678>")
        self.assertIn("<@&987654321012345678>", editor.embed["description"])
        self.assertNotIn("<@&987654321012345678>", editor.text)
        self.assertTrue(editor.dirty)

    def test_embed_editor_includes_direct_role_and_channel_selectors(self):
        editor = setup.AutofeedEditorView(b.__dict__, 901, 10)
        view = setup.EmbedEditorView(editor)
        self.assertEqual(len([
            v for v in view.children if isinstance(v, b.discord.ui.RoleSelect)]), 1)
        self.assertEqual(len([
            v for v in view.children if isinstance(v, b.discord.ui.ChannelSelect)]), 1)
        self.assertEqual(view.roles.row, 0)
        self.assertEqual(view.channels.row, 1)
        self.assertIn(setup.t("embed_text_design"),
                      [x.label for x in view.children if hasattr(x, "label")])
        self.assertEqual(b.guild_config_get(901, feeds.CONFIG_KEY), self.original_config())

    def original_config(self):
        return b.guild_config_get(901, feeds.CONFIG_KEY)

    def test_typed_embed_mentions_resolve_only_unique_guild_names(self):
        role = NS(id=987654321098765432, name="Avisos oficiales")
        duplicate_a = NS(id=123456789000000001, name="Noticias")
        duplicate_b = NS(id=123456789000000002, name="Noticias")
        channel = NS(id=123456789012345678, name="reglas")
        guild = NS(roles=[role, duplicate_a, duplicate_b], text_channels=[channel])
        result = setup.resolve_inline_embed_names(
            guild, "Lee #reglas y avisa a @Avisos oficiales; @Noticias no cambia.")
        self.assertIn("<#123456789012345678>", result)
        self.assertIn("<@&987654321098765432>", result)
        self.assertIn("@Noticias", result)
        self.assertEqual(setup.resolve_inline_embed_names(
            guild, "Correo a@ejemplo.com y @everyone"), "Correo a@ejemplo.com y @everyone")

    def test_frequency_preset_and_time_fields(self):
        editor = setup.AutofeedEditorView(b.__dict__, 901, 10)
        self.assertEqual(setup.PRESETS["daily"]["days"], 1)
        self.assertEqual(setup.PRESETS["monthly"]["months"], 1)
        modal = setup.DateTimeModal(editor)
        self.assertEqual(len(modal.children), 2)
        self.assertEqual(len(setup.CustomRepeatModal(editor).children), 4)

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
