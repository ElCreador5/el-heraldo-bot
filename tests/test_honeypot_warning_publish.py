"""Publicación de avisos Honeypot: confirmación, permisos y actualización idempotente."""
import unittest
from types import SimpleNamespace as NS
from unittest.mock import AsyncMock, MagicMock, patch

from test_safety_regressions import b, interaction


class HoneypotWarningPublicationTests(unittest.IsolatedAsyncioTestCase):
    def _setup(self, *, traps=None, enabled=True):
        channel_ids = {101: None} if traps is None else traps
        settings = {"active": enabled}
        resources = {101: self._channel(101)}
        i = interaction()
        i.guild.me = NS(id=3)
        i.guild.get_channel = resources.get
        def get_traps(_guild_id):
            return channel_ids
        def is_enabled(_guild_id):
            return settings["active"]
        def setting_set(_guild_id, name, value):
            if name == "honeypot_warning_enabled":
                settings["active"] = value == "1"
        return i, channel_ids, settings, resources, get_traps, is_enabled, setting_set

    @staticmethod
    def _channel(cid):
        channel = MagicMock(spec=b.discord.TextChannel)
        channel.id = cid
        channel.mention = f"<#{cid}>"
        channel.permissions_for.return_value = NS(
            view_channel=True, send_messages=True, manage_messages=True,
            read_message_history=True, embed_links=True,
        )
        return channel

    async def test_notice_has_publish_button_in_green(self):
        i, traps, settings, _, get_traps, enabled, _ = self._setup()
        with (
            patch.object(b, "hp_traps", side_effect=get_traps),
            patch.object(b, "hp_warning_enabled", side_effect=enabled),
        ):
            parent = b.HeraldoHoneypotSetupView(901, 10)
            notice = b.HeraldoHoneypotNoticeView(parent)
            self.assertEqual(notice.publish_warning.label, "Publicar aviso")
            self.assertEqual(notice.publish_warning.style, b.discord.ButtonStyle.success)
            self.assertFalse(any(item.label in ("Editar texto", "Editar diseño") for item in notice.children))
            await notice.publish_warning.callback(i)
            confirmation = i.followup.send.call_args.kwargs["view"]
            self.assertIsInstance(confirmation, b.HoneypotPublishWarningConfirmView)
            self.assertEqual(confirmation.confirm.style, b.discord.ButtonStyle.success)
            self.assertEqual(confirmation.cancel.style, b.discord.ButtonStyle.danger)
            i.response.defer.assert_awaited_once()
            self.assertTrue(i.followup.send.call_args.kwargs["ephemeral"])
            self.assertTrue(i.followup.send.call_args.kwargs["wait"])
            self.assertIs(confirmation.panel_interaction, i)
            self.assertIsInstance(confirmation.panel_view, b.HeraldoHoneypotNoticeView)

    async def test_direct_editor_submits_save_and_publish_with_original_fields(self):
        i = interaction()
        editor = b.HoneypotWarningEmbedModal(901, publish_from_setup=True)
        editor.title_input._value = "Aviso"
        editor.description_input._value = "No escribas aquí"
        editor.color_input._value = "F1C40F"
        editor.image_input._value = ""
        editor.footer_input._value = "Regla de la comunidad"
        with patch.object(b, "confirm_configuration", new=AsyncMock()) as confirm:
            await editor.on_submit(i)
        confirm.assert_awaited_once()
        args, kwargs = confirm.call_args
        self.assertIs(args[0], i)
        self.assertEqual(args[1], 901)
        self.assertEqual(args[2]["honeypot_warning_title"], "Aviso")
        self.assertEqual(args[2]["honeypot_warning_description"], "No escribas aquí")
        self.assertEqual(args[2]["honeypot_warning_style"], "custom")
        self.assertEqual(args[2]["honeypot_warning_enabled"], "1")
        self.assertTrue(kwargs["publish_honeypot_notice"])

    def test_existing_confirmation_reused_for_publication(self):
        with patch.object(b, "hp_notice_snapshot", return_value=("original",)), \
             patch.object(b, "hp_traps", return_value={101: None}):
            confirm = b.ConfigurationConfirmView(
                901, 10, {}, publish_honeypot_notice=True
            )
        self.assertEqual(confirm.save.label, "Guardar y publicar aviso")
        self.assertTrue(confirm.publish_honeypot_notice)
        self.assertEqual(confirm.notice_traps, {101})

    async def test_no_traps_does_not_offer_publication(self):
        i, traps, settings, _, get_traps, enabled, _ = self._setup(traps={})
        with (
            patch.object(b, "hp_traps", side_effect=get_traps),
            patch.object(b, "hp_warning_enabled", side_effect=enabled),
            patch.object(b, "hp_sync_all_warnings", new=AsyncMock()) as sync,
        ):
            parent = b.HeraldoHoneypotSetupView(901, 10)
            await b.HeraldoHoneypotNoticeView(parent).publish_warning.callback(i)
            self.assertNotIn("view", i.followup.send.call_args.kwargs)
            sync.assert_not_awaited()

    async def test_pending_draft_prevents_publication(self):
        i, traps, settings, _, get_traps, enabled, _ = self._setup()
        with (
            patch.object(b, "hp_traps", side_effect=get_traps),
            patch.object(b, "hp_warning_enabled", side_effect=enabled),
            patch.object(b, "hp_sync_all_warnings", new=AsyncMock()) as sync,
        ):
            parent = b.HeraldoHoneypotSetupView(901, 10)
            parent.pending_action = "log"
            await b.HeraldoHoneypotNoticeView(parent).publish_warning.callback(i)
            self.assertIn("cambios pendientes", i.followup.send.call_args.args[0].lower())
            sync.assert_not_awaited()

    async def test_cancel_does_not_publish_or_change_enabled(self):
        i, traps, settings, resources, get_traps, enabled, change = self._setup(enabled=False)
        with (
            patch.object(b, "hp_traps", side_effect=get_traps),
            patch.object(b, "hp_warning_enabled", side_effect=enabled),
            patch.object(b, "hp_sync_all_warnings", new=AsyncMock()) as sync,
            patch.object(b, "hp_setting_set", side_effect=change) as save,
        ):
            parent = b.HeraldoHoneypotSetupView(901, 10)
            await b.HeraldoHoneypotNoticeView(parent).publish_warning.callback(i)
            proposal = i.followup.send.call_args.kwargs["view"]
            cancelled = interaction()
            await proposal.cancel.callback(cancelled)
            cancelled.response.defer.assert_awaited_once()
            cancelled.delete_original_response.assert_awaited_once()
            save.assert_not_called()
            sync.assert_not_awaited()
            self.assertFalse(settings["active"])

    async def test_publishing_enables_and_calls_existing_sync_once(self):
        i, traps, settings, resources, get_traps, enabled, change = self._setup(enabled=False)
        with (
            patch.object(b, "hp_traps", side_effect=get_traps),
            patch.object(b, "hp_warning_enabled", side_effect=enabled),
            patch.object(b, "hp_setting_set", side_effect=change) as save,
            patch.object(b, "hp_sync_all_warnings", new=AsyncMock(return_value=[])) as sync,
            patch.object(b, "configuration_access", new=AsyncMock(return_value=True)),
        ):
            parent = b.HeraldoHoneypotSetupView(901, 10)
            await b.HeraldoHoneypotNoticeView(parent).publish_warning.callback(i)
            proposal = i.followup.send.call_args.kwargs["view"]
            confirm_interaction = interaction()
            confirm_interaction.guild = i.guild
            await proposal.confirm.callback(confirm_interaction)
            save.assert_called_once_with(901, "honeypot_warning_enabled", "1")
            sync.assert_awaited_once_with(i.guild)
            confirm_interaction.followup.send.assert_not_awaited()
            confirm_interaction.response.defer.assert_awaited_once()
            confirm_interaction.delete_original_response.assert_awaited_once()
            self.assertTrue(settings["active"])
            self.assertTrue(proposal.finished)
            i.edit_original_response.assert_awaited_once()
            self.assertIn("1 canal", i.edit_original_response.call_args.kwargs["embed"].description)
            self.assertEqual(i.edit_original_response.call_args.kwargs["view"], proposal.panel_view)

    async def test_permission_revocation_does_not_publish(self):
        i, traps, settings, resources, get_traps, enabled, _ = self._setup()
        with (
            patch.object(b, "hp_traps", side_effect=get_traps),
            patch.object(b, "hp_warning_enabled", side_effect=enabled),
            patch.object(b, "configuration_access", new=AsyncMock(return_value=False)),
            patch.object(b, "hp_sync_all_warnings", new=AsyncMock()) as sync,
        ):
            proposal = b.HoneypotPublishWarningConfirmView(901, 10)
            await proposal.confirm.callback(i)
            sync.assert_not_awaited()
            self.assertTrue(proposal.finished)
            i.delete_original_response.assert_awaited_once()

    async def test_missing_permissions_or_channel_aborts_before_change(self):
        for no_channel in (False, True):
            with self.subTest(no_channel=no_channel):
                i, traps, settings, resources, get_traps, enabled, change = self._setup(enabled=False)
                if no_channel:
                    resources.clear()
                else:
                    resources[101].permissions_for.return_value.manage_messages = False
                with (
                    patch.object(b, "hp_traps", side_effect=get_traps),
                    patch.object(b, "hp_warning_enabled", side_effect=enabled),
                    patch.object(b, "hp_setting_set", side_effect=change) as save,
                    patch.object(b, "configuration_access", new=AsyncMock(return_value=True)),
                    patch.object(b, "hp_sync_all_warnings", new=AsyncMock()) as sync,
                ):
                    proposal = b.HoneypotPublishWarningConfirmView(901, 10)
                    await proposal.confirm.callback(i)
                    i.delete_original_response.assert_awaited_once()
                    save.assert_not_called()
                    sync.assert_not_awaited()
                    self.assertTrue(proposal.finished)
                    i.delete_original_response.assert_awaited_once()

    async def test_trap_or_template_changes_invalidate_confirmation(self):
        for changed in ("trap", "template"):
            with self.subTest(changed=changed):
                i, traps, settings, resources, get_traps, enabled, _ = self._setup()
                templates = {"value": ("notice",)}
                with (
                    patch.object(b, "hp_traps", side_effect=get_traps),
                    patch.object(b, "hp_warning_enabled", side_effect=enabled),
                    patch.object(b, "hp_notice_snapshot", side_effect=lambda _id: templates["value"]),
                    patch.object(b, "configuration_access", new=AsyncMock(return_value=True)),
                    patch.object(b, "hp_sync_all_warnings", new=AsyncMock()) as sync,
                ):
                    proposal = b.HoneypotPublishWarningConfirmView(901, 10)
                    if changed == "trap":
                        traps[202] = None
                    else:
                        templates["value"] = ("new notice",)
                    await proposal.confirm.callback(i)
                    sync.assert_not_awaited()
                    self.assertIn("cambió", i.followup.send.call_args.args[0])
            i.delete_original_response.assert_awaited_once()

    async def test_partial_publish_not_reported_as_success(self):
        i, traps, settings, resources, get_traps, enabled, _ = self._setup()
        with (
            patch.object(b, "hp_traps", side_effect=get_traps),
            patch.object(b, "hp_warning_enabled", side_effect=enabled),
            patch.object(b, "configuration_access", new=AsyncMock(return_value=True)),
            patch.object(b, "hp_sync_all_warnings", new=AsyncMock(return_value=["<#101>: sin permisos"])),
        ):
            proposal = b.HoneypotPublishWarningConfirmView(901, 10)
            await proposal.confirm.callback(i)
            message = i.followup.send.call_args.args[0]
            self.assertIn("No se completó", message)
            self.assertNotIn("1 canal(es)", message)

    async def test_double_confirm_does_not_publish_again(self):
        i, traps, settings, _, get_traps, enabled, _ = self._setup()
        with (
            patch.object(b, "hp_traps", side_effect=get_traps),
            patch.object(b, "hp_warning_enabled", side_effect=enabled),
            patch.object(b, "hp_sync_all_warnings", new=AsyncMock(return_value=[])) as sync,
            patch.object(b, "configuration_access", new=AsyncMock(return_value=True)),
        ):
            parent = b.HeraldoHoneypotSetupView(901, 10)
            await b.HeraldoHoneypotNoticeView(parent).publish_warning.callback(i)
            proposal = i.followup.send.call_args.kwargs["view"]
            first = interaction()
            first.guild = i.guild
            await proposal.confirm.callback(first)
            second = interaction()
            second.guild = i.guild
            await proposal.confirm.callback(second)
        sync.assert_awaited_once()
        first.delete_original_response.assert_awaited_once()
        self.assertIn("ya se resolvió", second.followup.send.call_args.args[0])

    async def test_publication_refresh_failure_is_reported_without_second_success(self):
        i, traps, settings, _, get_traps, enabled, _ = self._setup()
        error = b.discord.Forbidden(NS(status=403, reason="Forbidden"), "Acceso revocado")
        i.edit_original_response.side_effect = error
        with (
            patch.object(b, "hp_traps", side_effect=get_traps),
            patch.object(b, "hp_warning_enabled", side_effect=enabled),
            patch.object(b, "hp_sync_all_warnings", new=AsyncMock(return_value=[])) as sync,
            patch.object(b, "configuration_access", new=AsyncMock(return_value=True)),
        ):
            parent = b.HeraldoHoneypotSetupView(901, 10)
            await b.HeraldoHoneypotNoticeView(parent).publish_warning.callback(i)
            proposal = i.followup.send.call_args.kwargs["view"]
            confirm_i = interaction()
            confirm_i.guild = i.guild
            await proposal.confirm.callback(confirm_i)
        sync.assert_awaited_once()
        self.assertIn("no se pudo refrescar", confirm_i.followup.send.call_args.args[0])
        confirm_i.delete_original_response.assert_awaited_once()

    async def test_delete_ephemeral_failure_removes_buttons(self):
        i, traps, settings, _, get_traps, enabled, _ = self._setup()
        cancelled = interaction()
        cancelled.delete_original_response.side_effect = b.discord.Forbidden(
            NS(status=403, reason="Forbidden"), "Error"
        )
        with patch.object(b, "hp_traps", side_effect=get_traps), \
             patch.object(b, "hp_warning_enabled", side_effect=enabled):
            proposal = b.HoneypotPublishWarningConfirmView(901, 10)
            await proposal.cancel.callback(cancelled)
        cancelled.edit_original_response.assert_awaited_once_with(
            content="Confirmación cerrada.", embed=None, view=None,
        )

    async def test_new_unsaved_draft_invalidates_confirmation(self):
        i, traps, settings, _, get_traps, enabled, _ = self._setup()
        with (
            patch.object(b, "hp_traps", side_effect=get_traps),
            patch.object(b, "hp_warning_enabled", side_effect=enabled),
            patch.object(b, "hp_sync_all_warnings", new=AsyncMock()) as sync,
            patch.object(b, "configuration_access", new=AsyncMock(return_value=True)),
        ):
            parent = b.HeraldoHoneypotSetupView(901, 10)
            await b.HeraldoHoneypotNoticeView(parent).publish_warning.callback(i)
            proposal = i.followup.send.call_args.kwargs["view"]
            parent.pending_action = "log"
            confirm_i = interaction()
            confirm_i.guild = i.guild
            await proposal.confirm.callback(confirm_i)
        sync.assert_not_awaited()
        self.assertIn("cambios pendientes", confirm_i.followup.send.call_args.args[0])
        confirm_i.delete_original_response.assert_awaited_once()

    async def test_cancel_wins_while_confirmation_is_checking_access(self):
        i, traps, settings, _, get_traps, enabled, _ = self._setup()
        waiting = b.asyncio.Event()
        released = b.asyncio.Event()
        confirm_i = interaction()
        confirm_i.guild = i.guild
        cancel_i = interaction()
        cancel_i.guild = i.guild

        async def check(current, *_):
            if current is confirm_i:
                waiting.set()
                await released.wait()
            return True

        with (
            patch.object(b, "hp_traps", side_effect=get_traps),
            patch.object(b, "hp_warning_enabled", side_effect=enabled),
            patch.object(b, "hp_sync_all_warnings", new=AsyncMock()) as sync,
            patch.object(b, "configuration_access", new=AsyncMock(side_effect=check)),
        ):
            parent = b.HeraldoHoneypotSetupView(901, 10)
            await b.HeraldoHoneypotNoticeView(parent).publish_warning.callback(i)
            proposal = i.followup.send.call_args.kwargs["view"]
            pending = b.asyncio.create_task(proposal.confirm.callback(confirm_i))
            await waiting.wait()
            await proposal.cancel.callback(cancel_i)
            released.set()
            await pending
        sync.assert_not_awaited()
        cancel_i.delete_original_response.assert_awaited_once()
        self.assertIn("ya se resolvió", confirm_i.followup.send.call_args.args[0])

    async def test_existing_warning_is_updated_without_creating_duplicate(self):
        guild = NS(id=901)
        channel = self._channel(101)
        channel.guild = guild
        existing = NS(
            pinned=True, edit=AsyncMock(), pin=AsyncMock(),
        )
        channel.fetch_message = AsyncMock(return_value=existing)
        channel.send = AsyncMock()
        with (
            patch.object(b, "hp_traps", return_value={101: 654}),
            patch.object(b, "hp_warning_enabled", return_value=True),
            patch.object(b, "hp_warning_embed", return_value=b.discord.Embed(title="Aviso")),
            patch.object(b, "hp_set_warning_message") as save,
        ):
            result = await b.hp_sync_warning(channel)
        self.assertIsNone(result)
        existing.edit.assert_awaited_once()
        channel.send.assert_not_awaited()
        save.assert_not_called()


if __name__ == "__main__":
    unittest.main()
