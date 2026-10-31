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
                         "honeypot", "condemnation", "logs"}.issubset(options))
        self.assertNotIn("templates", options)
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
        for key in ("message", "show_embed", "repeat_picker",
                    "save", "send", "back"):
            self.assertIn(setup.t(key), labels)
        for key in ("insert_mention", "images_button", "embed_channel"):
            self.assertNotIn(setup.t(key), labels)
        self.assertEqual([x.row for x in editor.children if isinstance(x, (b.discord.ui.ChannelSelect, b.discord.ui.RoleSelect))], [0, 1])
        self.assertEqual(len(editor.children), 9)
        self.assertNotIn(setup.t("date_picker"), labels)
        self.assertNotIn(setup.t("silent"), labels)
        self.assertEqual({item.row for item in editor.children if hasattr(item, "callback")},
                         {0, 1, 2, 3, 4})
        self.assertIsNotNone(editor.panel_embed(None))
        self.assertIn("Crear anuncio", editor.panel_embed(None).title)
        self.assertNotIn("**Mensaje:**", editor.summary())
        frequency = setup.FrequencyPickerView(editor)
        self.assertIn(setup.t("date_picker"), [item.label for item in frequency.children if getattr(item, "label", None)])
        self.assertIn(setup.t("discard"), labels)
        self.assertTrue(editor.save.disabled)
        self.assertTrue(editor.discard.disabled)
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

    async def test_publish_label_and_embed_modal_open_without_extra_panel(self):
        from autofeed_embed_builder import SectionModal
        editor = setup.AutofeedEditorView(b.__dict__, self.guild_id, self.owner_id)
        self.assertEqual(editor.save.label, "Guardar cambios")
        self.assertEqual(editor.publish_button.label, "Publicar")
        before = b.guild_config_get(self.guild_id, feeds.CONFIG_KEY)
        i = self.interaction()
        i.response.send_modal = AsyncMock()
        await editor.embed_builder.callback(i)
        i.response.send_modal.assert_awaited_once()
        modal = i.response.send_modal.call_args.args[0]
        self.assertIsInstance(modal, SectionModal)
        self.assertEqual(modal.section, "main")
        self.assertEqual(len(modal.children), 3)
        self.assertIn("Guardar", modal.title)
        self.assertNotIn("url", modal.inputs)
        i.response.edit_message.assert_not_called()
        self.assertEqual(before, b.guild_config_get(self.guild_id, feeds.CONFIG_KEY))

    def test_custom_repeat_defaults_to_valid_one_hour(self):
        editor = setup.AutofeedEditorView(b.__dict__, self.guild_id, self.owner_id)
        modal = setup.CustomRepeatModal(editor)
        self.assertEqual([str(field.default) for field in modal.fields],
                         ["0", "0", "1", "0"])
        self.assertEqual(
            setup.repeat_parts(*(int(str(field.default)) for field in modal.fields)),
            {"months": 0, "days": 0, "hours": 1, "minutes": 0})
        editor.parts = {"months": 0, "days": 0, "hours": 3, "minutes": 15}
        reused = setup.CustomRepeatModal(editor)
        self.assertEqual([str(field.default) for field in reused.fields],
                         ["0", "0", "3", "15"])

    async def test_save_is_a_confirmed_persistent_draft_separate_from_publish(self):
        from unittest.mock import Mock
        writes = Mock()
        host = dict(b.__dict__)
        host["guild_config_get"] = lambda guild, key: None
        host["guild_config_set"] = writes
        editor = setup.AutofeedEditorView(host, self.guild_id, self.owner_id)
        editor.text = "Anuncio de prueba"
        editor.dirty = True
        i = self.interaction()
        i.response.defer = AsyncMock()
        i.edit_original_response = AsyncMock()
        await editor.save.callback(i)
        writes.assert_not_called()
        confirm = i.response.edit_message.call_args.kwargs["view"]
        self.assertIsInstance(confirm, setup.AnnouncementDraftConfirmView)
        i.response.edit_message.reset_mock()
        await confirm.confirm.callback(i)
        writes.assert_called_once()
        self.assertEqual(writes.call_args.args[1],
                         setup._draft_key(self.owner_id))
        self.assertEqual(editor.saved_draft["text"], "Anuncio de prueba")
        self.assertFalse(editor.dirty)
        i.response.send_message.reset_mock()
        editor.text = "Cambió después de guardar"
        editor.dirty = True
        await editor.publish_button.callback(i)
        i.response.send_message.assert_awaited_once()
        self.assertIn(setup.t("draft_first"),
                      i.response.send_message.call_args.args[0])

    async def test_embed_builder_concentrates_mentions_and_images(self):
        from autofeed_embed_builder import SectionModal, EmbedBuilderView
        editor = setup.AutofeedEditorView(b.__dict__, self.guild_id, self.owner_id)
        i = self.interaction()
        i.response.send_modal = AsyncMock()
        await editor.embed_builder.callback(i)
        modal = i.response.send_modal.call_args.args[0]
        self.assertIsInstance(modal, SectionModal)
        self.assertEqual(modal.section, "main")
        builder = EmbedBuilderView(editor)
        self.assertEqual(
            {opt.value for opt in builder.section_select.options},
            {"main", "author", "media", "fields", "date"})
        self.assertIsInstance(builder.roles, b.discord.ui.RoleSelect)
        self.assertIsInstance(builder.channels, b.discord.ui.ChannelSelect)
        media = SectionModal(editor, "media")
        self.assertEqual(set(media.inputs), {"image_url", "thumbnail_url"})

    async def test_autofeeds_is_a_separate_setup_module(self):
        root = b.HeraldoSetupView(self.guild_id, self.owner_id)
        self.assertIn("autofeeds", {opt.value for opt in root.module_select.options})
        self.assertEqual(next(opt.label for opt in root.module_select.options
                              if opt.value == "autofeeds"), "Anuncios")
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
                         [setup.t(k) for k in ("new", "manage", "member_week", "back")])
        self.assertIn(setup.t("staff_only"), content)
        self.assertNotIn(setup.t("permissions"), [c.label for c in home.children])
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

    async def test_manage_returns_to_announcements_without_writes(self):
        content, home = setup.setup_panel(b.__dict__, self.guild_id, self.owner_id)
        i = self.interaction()
        with patch.object(feeds, "get_jobs", return_value=[]):
            await home.manage.callback(i)
        self.assertIsInstance(i.response.edit_message.call_args.kwargs["view"], setup.AutoFeedsHomeView)
        self.assertIn(feeds.tr("no_jobs"), i.response.edit_message.call_args.kwargs["content"])
        self.assertEqual(b.guild_config_get(self.guild_id, feeds.CONFIG_KEY), self.original)

    def test_announcements_labels_in_three_languages(self):
        for locale, labels in (
            ("es-419", ("**Anuncios**", "Crear Anuncio", "Gestionar Anuncios")),
            ("en-US", ("**Announcements**", "Create Announcement", "Manage Announcements")),
            ("pt-BR", ("**Anúncios**", "Criar Anúncio", "Gerenciar Anúncios")),
        ):
            with self.subTest(locale=locale):
                self.assertEqual(tuple(setup.LANG[locale][key]
                                       for key in ("hub_title", "new", "manage")), labels)
                self.assertTrue(setup.LANG[locale]["staff_only"])


    async def test_editor_draft_requires_confirmation_not_persistence(self):
        host = dict(b.__dict__)
        host["guild_config_get"] = lambda guild, key: None
        editor = setup.AutofeedEditorView(host, 901, 10)
        self.assertIn(editor.discard, editor.children)
        self.assertTrue(editor.discard.disabled)
        self.assertTrue(editor.save.disabled)

        editor.text = "Ejemplo"
        editor.dirty = True
        self.assertFalse(editor.discard.disabled)
        self.assertFalse(editor.save.disabled)

        editor.text = ""
        editor.dirty = True
        self.assertTrue(editor.discard.disabled)
        self.assertTrue(editor.save.disabled)

        # Una vez confirmado el borrador, no quedan cambios que descartar.
        editor.text = "Aviso guardado"
        editor.dirty = True
        editor.saved_draft = editor.draft_data()
        editor.dirty = False
        self.assertTrue(editor.discard.disabled)
        self.assertTrue(editor.save.disabled)

        editor.role_id = 99
        editor.dirty = True
        self.assertFalse(editor.discard.disabled)
        self.assertFalse(editor.save.disabled)
        editor.role_id = None
        editor.dirty = True
        self.assertTrue(editor.discard.disabled)
        self.assertTrue(editor.save.disabled)

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

    def test_mention_controls_are_not_duplicated_in_main_editor(self):
        editor = setup.AutofeedEditorView(b.__dict__, 901, 10)
        controls = [x.label for x in editor.children if getattr(x, "label", None)]
        for key in ("insert_mention", "embed_channel", "images_button"):
            self.assertNotIn(setup.t(key), controls)
        self.assertEqual(sum(label == setup.t("show_embed") for label in controls), 1)
        self.assertFalse(editor.dirty)

    def test_embed_builder_is_the_only_active_role_and_channel_embed_editor(self):
        from autofeed_embed_builder import EmbedBuilderView
        editor = setup.AutofeedEditorView(b.__dict__, 901, 10)
        view = EmbedBuilderView(editor)
        self.assertEqual(len([
            v for v in view.children if isinstance(v, b.discord.ui.RoleSelect)]), 1)
        self.assertEqual(len([
            v for v in view.children if isinstance(v, b.discord.ui.ChannelSelect)]), 1)
        self.assertEqual(view.roles.row, 1)
        self.assertEqual(view.channels.row, 2)
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

    def test_five_minute_lab_repeat_and_scheduler_without_changing_production(self):
        with patch("enzonic_test_host.is_test", return_value=True):
            custom = setup.repeat_parts(0, 0, 0, 5)
            editor = setup.AutofeedEditorView(b.__dict__, 901, 10)
            modal = setup.CustomRepeatModal(editor)
            self.assertEqual([str(x.default) for x in modal.fields], ["0", "0", "0", "5"])
            now = datetime(2027, 2, 1, 12, 2, tzinfo=timezone.utc)
            job = dict(start="2027-02-01T12:00:00+00:00", repeat="custom",
                       repeat_parts=custom, zone="UTC")
            self.assertEqual(next_occurrence(job, now), "2027-02-01T12:05:00+00:00")
            self.assertEqual(feeds.interval_seconds("5m"), 300)
            with self.assertRaises(ValueError):
                setup.repeat_parts(0, 0, 0, 4)
        with patch("enzonic_test_host.is_test", return_value=False):
            with self.assertRaises(ValueError):
                setup.repeat_parts(0, 0, 0, 5)
            with self.assertRaises(ValueError):
                feeds.interval_seconds("5m")

    def test_channel_hash_reference_in_embed_description(self):
        channel = NS(id=123456789012345678, name="apoyo", mention="<#123456789012345678>")
        guild = NS(roles=[], text_channels=[], channels=[channel])
        description = setup.resolve_inline_embed_names(
            guild, "Pasa por #apoyo y usa /bump. También visita #desconocido.")
        self.assertIn("<#123456789012345678>", description)
        self.assertIn("#desconocido", description)

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
