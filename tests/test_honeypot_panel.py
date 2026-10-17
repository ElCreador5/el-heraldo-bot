"""Regresiones del panel Honeypot: claridad, colores, borradores y confirmación."""
import unittest
from types import SimpleNamespace as NS
from unittest.mock import AsyncMock, MagicMock, patch

from test_safety_regressions import b, interaction


class HoneypotPanelTests(unittest.IsolatedAsyncioTestCase):
    def make_view(self, traps=None, *, enabled=False, paused=False, action="role"):
        patches = [
            patch.object(b, "hp_traps", return_value=traps if traps is not None else {}),
            patch.object(b, "honeypot_enabled", return_value=enabled),
            patch.object(b, "honeypot_paused", return_value=paused),
            patch.object(b, "hp_action", return_value=action),
        ]
        for ctx in patches:
            ctx.start()
            self.addCleanup(ctx.stop)
        return b.HeraldoHoneypotSetupView(901, 10)

    async def test_button_colours_and_dynamic_toggle(self):
        view = self.make_view(traps={123: None}, enabled=True)
        self.assertEqual(view.toggle.label, "Pausar protección")
        self.assertEqual(view.toggle.style, b.discord.ButtonStyle.danger)
        self.assertEqual(view.create_channel.style, b.discord.ButtonStyle.primary)
        self.assertEqual(view.remove_channel.style, b.discord.ButtonStyle.danger)
        self.assertEqual(view.edit_action.style, b.discord.ButtonStyle.primary)
        self.assertEqual(view.edit_notice.style, b.discord.ButtonStyle.primary)
        self.assertEqual(view.details.style, b.discord.ButtonStyle.primary)
        self.assertEqual(view.save_changes.style, b.discord.ButtonStyle.success)
        self.assertEqual(view.discard_changes.style, b.discord.ButtonStyle.danger)
        self.assertEqual(view.back.style, b.discord.ButtonStyle.secondary)

        i = interaction()
        with patch.object(b, "hp_setup_embed", return_value=b.discord.Embed(title="Prueba")):
            await view.toggle.callback(i)
        self.assertIsNone(view.pending_enabled)
        self.assertTrue(view.pending_paused)
        self.assertEqual(view.toggle.label, "Reanudar protección")
        self.assertEqual(view.toggle.style, b.discord.ButtonStyle.success)
        i.response.edit_message.assert_awaited_once()

    async def test_paused_protection_can_be_resumed_as_draft_only(self):
        view = self.make_view(traps={123: None}, enabled=True, paused=True)
        self.assertEqual(view.toggle.label, "Reanudar protección")
        i = interaction()
        with patch.object(b, "hp_setup_embed", return_value=b.discord.Embed()), \
             patch.object(b, "hp_setting_set") as save:
            await view.toggle.callback(i)
        save.assert_not_called()
        self.assertFalse(view.pending_paused)
        self.assertEqual(view.toggle.label, "Pausar protección")

    async def test_selection_of_registered_channel_does_not_stage_duplicate(self):
        view = self.make_view(traps={123: None}, enabled=False)
        channel = MagicMock(spec=b.discord.TextChannel)
        channel.id, channel.mention = 123, "<#123>"
        i = interaction()
        i.data = {"values": ["123"]}
        i.guild.get_channel = lambda _id: channel
        with patch.object(b, "hp_add_trap") as save, \
             patch.object(b, "hp_setup_embed", return_value=b.discord.Embed()):
            await view.select_trap(i)
        save.assert_not_called()
        self.assertIsNone(view.pending_trap_id)
        self.assertEqual(view.selected_channel_id, 123)
        self.assertFalse(view.remove_channel.disabled)

    async def test_draft_action_requires_save_and_discard_does_not_persist(self):
        view = self.make_view(traps={123: None}, enabled=True)
        editor = b.HeraldoHoneypotActionView(view)
        i = interaction()
        i.data = {"values": ["log"]}
        with patch.object(b, "hp_setting_set") as save, \
             patch.object(b, "hp_setup_embed", return_value=b.discord.Embed()):
            await editor.choose(i)
            self.assertEqual(view.pending_action, "log")
            save.assert_not_called()
            await view.discard_changes.callback(interaction())
        self.assertIsNone(view.pending_action)
        save.assert_not_called()

    async def test_create_channel_only_opens_confirmation_and_rechecks_permissions(self):
        view = self.make_view(traps={123: None}, enabled=True)
        i = interaction()
        i.guild.text_channels = []
        i.guild.create_text_channel = AsyncMock()
        with patch.object(b, "get_guild_channel_id", return_value=0), \
             patch.object(b, "hp_add_trap") as add:
            await view.create_channel.callback(i)
        i.guild.create_text_channel.assert_not_awaited()
        add.assert_not_called()
        proposed = i.response.send_message.call_args.kwargs["view"]
        self.assertIsInstance(proposed, b.HoneypotTrapActionConfirmView)
        self.assertTrue(proposed.from_setup)
        self.assertEqual(proposed.confirm.style, b.discord.ButtonStyle.success)
        self.assertEqual(proposed.cancel.style, b.discord.ButtonStyle.danger)
        denied = interaction()
        denied.user.guild_permissions = b.discord.Permissions(manage_guild=True)
        denied.guild.me = NS(guild_permissions=NS(manage_channels=False))
        denied.guild.create_text_channel = AsyncMock()
        await proposed.confirm.callback(denied)
        denied.guild.create_text_channel.assert_not_awaited()

    async def test_old_draft_blocks_save_after_concurrent_setting_change(self):
        view = self.make_view(traps={123: None}, enabled=False, action="log")
        view.pending_action = "timeout"
        i = interaction()
        # La vista recibió su snapshot original, pero otro administrador cambió el estado.
        with patch.object(b, "hp_action", return_value="timeout"), \
             patch.object(b, "hp_setting_set") as save:
            await view.save_changes.callback(i)
        save.assert_not_called()
        self.assertIn("configuración cambió", i.response.send_message.call_args.args[0])

    def test_embed_only_shows_relevant_action_and_compact_followup(self):
        guild = NS(id=901)
        with (
            patch.object(b, "hp_traps", return_value={123: None}),
            patch.object(b, "honeypot_enabled", return_value=True),
            patch.object(b, "honeypot_paused", return_value=False),
            patch.object(b, "hp_action", return_value="role"),
            patch.object(b, "hp_punish_role_id", return_value=700),
            patch.object(b, "hp_purge_spec", return_value=("time", 1440)),
            patch.object(b, "hp_warning_enabled", return_value=True),
            patch.object(b, "hp_warning_style", return_value="text"),
            patch.object(b, "hp_setting_get", return_value=None),
            patch.object(b, "hp_exempt_ids", return_value=set()),
            patch.object(b, "hp_total_triggers", return_value=2),
            patch.object(b, "hp_retention_minutes", return_value=43200),
        ):
            embed = b.hp_setup_embed(guild, ["Añadir canal: <#456>"])
        self.assertEqual(embed.title, "AutoMod — Honeypot")
        self.assertEqual([x.name for x in embed.fields], [
            "Estado actual", "Medida aplicada", "Aviso y seguimiento", "Cambios pendientes",
        ])
        self.assertIn("<#123>", embed.fields[0].value)
        self.assertIn("<@&700>", embed.fields[1].value)
        self.assertNotIn("timeout", embed.fields[1].value.lower())
        self.assertIn("Exenciones:** Ninguna", embed.fields[2].value)
        self.assertIn("Añadir canal", embed.fields[3].value)
        self.assertNotIn("Miembros exentos: —", str(embed.to_dict()))

    async def test_notice_uses_one_entry_and_preserves_both_editors(self):
        view = self.make_view(traps={123: None}, enabled=True)
        notice = b.HeraldoHoneypotNoticeView(view)
        i1, i2 = interaction(), interaction()
        await notice.text_warning.callback(i1)
        await notice.visual_warning.callback(i2)
        self.assertIsInstance(i1.response.send_modal.call_args.args[0], b.HoneypotWarningModal)
        self.assertIsInstance(i2.response.send_modal.call_args.args[0], b.HoneypotWarningEmbedModal)


if __name__ == "__main__":
    unittest.main()
