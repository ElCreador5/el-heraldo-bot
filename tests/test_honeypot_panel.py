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
        # En discord.py, response.is_done() pasa a True tras defer().
        # El mock de la interacción no cambia ese estado automáticamente.
        i.response.is_done = lambda: i.response.defer.await_count > 0
        with patch.object(b, "hp_setup_embed", return_value=b.discord.Embed(title="Prueba")):
            await view.toggle.callback(i)
        self.assertIsNone(view.pending_enabled)
        self.assertTrue(view.pending_paused)
        self.assertEqual(view.toggle.label, "Reanudar protección")
        self.assertEqual(view.toggle.style, b.discord.ButtonStyle.success)
        i.edit_original_response.assert_awaited_once()
        i.response.defer.assert_awaited_once()

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

    async def test_action_and_measure_have_explicit_save_and_discard(self):
        view = self.make_view(traps={123: None}, enabled=True, action="role")
        view.pending_action = "kick"
        for editor_type in (b.HeraldoHoneypotActionView, b.HeraldoHoneypotParametersView):
            editor = editor_type(view)
            self.assertFalse(editor.save_changes.disabled)
            self.assertFalse(editor.discard_changes.disabled)
            self.assertEqual(editor.save_changes.style, b.discord.ButtonStyle.success)
            self.assertEqual(editor.discard_changes.style, b.discord.ButtonStyle.danger)
            with patch.object(view, "_save_pending_changes", new_callable=AsyncMock) as save:
                await editor.save_changes.callback(interaction())
                save.assert_awaited_once()
            self.assertEqual(view.pending_action, "kick")

        editor = b.HeraldoHoneypotParametersView(view)
        with patch.object(b, "hp_setting_set") as database_write, \
             patch.object(b, "hp_setup_embed", return_value=b.discord.Embed()):
            i = interaction()
            await editor.discard_changes.callback(i)
            database_write.assert_not_called()
        self.assertIsNone(view.pending_action)
        i.edit_original_response.assert_awaited_once()
        i.response.defer.assert_awaited_once()
        self.assertIs(i.edit_original_response.call_args.kwargs["view"], view)

    def test_submenus_disable_save_without_pending_changes(self):
        view = self.make_view(traps={123: None}, enabled=True)
        for editor_type in (b.HeraldoHoneypotActionView, b.HeraldoHoneypotParametersView):
            editor = editor_type(view)
            self.assertTrue(editor.save_changes.disabled)
            self.assertTrue(editor.discard_changes.disabled)

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
        proposed = i.followup.send.call_args.kwargs["view"]
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

    async def test_existing_honeypot_channel_proposes_confirmed_system_link(self):
        view = self.make_view(traps={}, enabled=False)
        i = interaction()
        channel = MagicMock(spec=b.discord.TextChannel)
        channel.id, channel.mention, channel.name = 777, "<#777>", "honeypot"
        i.guild.text_channels = [channel]
        i.guild.get_channel = lambda _id: None
        with (
            patch.object(b, "get_guild_channel_id", return_value=0),
            patch.object(b, "hp_protected_channel_reason", return_value=None),
            patch.object(b, "_setup_apply_system_channel", new=AsyncMock()) as apply,
        ):
            await view.create_channel.callback(i)
            proposed = i.followup.send.call_args.kwargs["view"]
            self.assertEqual(proposed.action, "add")
            self.assertTrue(proposed.from_setup)
            apply.assert_not_awaited()
        self.assertEqual(proposed.channel_id, 777)

    async def test_old_draft_blocks_save_after_concurrent_setting_change(self):
        view = self.make_view(traps={123: None}, enabled=False, action="log")
        view.pending_action = "timeout"
        i = interaction()
        # La vista recibió su snapshot original, pero otro administrador cambió el estado.
        with patch.object(b, "hp_action", return_value="timeout"), \
             patch.object(b, "hp_setting_set") as save:
            await view.save_changes.callback(i)
        save.assert_not_called()
        self.assertIn("configuración cambió", i.followup.send.call_args.args[0])

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
        i1.response.send_modal = AsyncMock()
        i2.response.send_modal = AsyncMock()
        await notice.text_warning.callback(i1)
        await notice.visual_warning.callback(i2)
        self.assertIsInstance(i1.response.send_modal.call_args.args[0], b.HoneypotWarningModal)
        self.assertIsInstance(i2.response.send_modal.call_args.args[0], b.HoneypotWarningEmbedModal)


class HoneypotRemovalBehaviorTests(unittest.IsolatedAsyncioTestCase):
    make_view = HoneypotPanelTests.make_view
    async def test_removal_is_draft_then_green_confirmation_on_same_panel(self):
        traps = {123: None}
        state = {"enabled": True}
        channel = MagicMock(spec=b.discord.TextChannel)
        channel.id, channel.mention = 123, "<#123>"
        async def access(*args, **kwargs):
            return True
        def setting(gid, key, value):
            if key == "honeypot_enabled":
                state["enabled"] = value == "1"
        with (
            patch.object(b, "hp_traps", side_effect=lambda gid: dict(traps)),
            patch.object(b, "honeypot_enabled", side_effect=lambda gid: state["enabled"]),
            patch.object(b, "hp_remove_trap", side_effect=lambda gid, cid: traps.pop(cid)),
            patch.object(b, "hp_setting_set", side_effect=setting) as save,
            patch.object(b, "configuration_access", side_effect=access),
            patch.object(b, "hp_setup_embed",
                         side_effect=lambda guild, pending=None: b.discord.Embed(description=f"Canales trampa: {len(traps)}")),
        ):
            view = b.HeraldoHoneypotSetupView(901, 10)
            select = interaction()
            select.data = {"values": ["123"]}
            select.guild.get_channel = lambda _id: channel
            select.response.is_done = lambda: select.response.defer.await_count > 0
            await view.select_trap(select)
            remove = interaction()
            remove.guild.get_channel = lambda _id: channel
            remove.response.is_done = lambda: remove.response.defer.await_count > 0
            await view.remove_channel.callback(remove)
            self.assertEqual(view.pending_remove_trap_id, 123)
            self.assertEqual(len(traps), 1, "Retirar canal antes de Guardar modificó SQLite")
            save.assert_not_called()
            remove.followup.send.assert_not_awaited()

            draft = interaction()
            draft.guild.get_channel = lambda _id: channel
            await view.save_changes.callback(draft)
            self.assertEqual(len(traps), 1)
            draft.followup.send.assert_not_awaited()
            confirmation = draft.edit_original_response.call_args.kwargs["view"]
            self.assertIsInstance(confirmation, b.HoneypotRemovalSaveConfirmView)
            self.assertEqual(confirmation.confirm.style, b.discord.ButtonStyle.success)

            accepted = interaction()
            accepted.guild.get_channel = lambda _id: channel
            accepted.response.is_done = lambda: accepted.response.defer.await_count > 0
            await confirmation.confirm.callback(accepted)
            self.assertEqual(traps, {})
            self.assertFalse(state["enabled"])
            save.assert_any_call(901, "honeypot_enabled", "0")
            accepted.followup.send.assert_not_awaited()
            rendered = accepted.edit_original_response.call_args.kwargs
            self.assertIs(rendered["view"], view)
            self.assertIn("Canales trampa: 0", rendered["embed"].description)
            self.assertIn("Canales trampa configurados: 0", rendered["content"])

    async def test_discard_trap_removal_leaves_original_configuration(self):
        view = self.make_view(traps={123: None}, enabled=True)
        channel = MagicMock(spec=b.discord.TextChannel)
        channel.id, channel.mention = 123, "<#123>"
        view.pending_remove_trap_id = 123
        with patch.object(b, "hp_remove_trap") as delete, patch.object(b, "hp_setting_set") as save, \
             patch.object(b, "hp_setup_embed", return_value=b.discord.Embed()):
            i = interaction()
            await view.discard_changes.callback(i)
        self.assertIsNone(view.pending_remove_trap_id)
        delete.assert_not_called()
        save.assert_not_called()

    def test_removal_cannot_reimport_legacy_channel_when_zero(self):
        import sqlite3
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as temp:
            database = Path(temp) / "honeypot.db"
            conn = sqlite3.connect(database)
            conn.executescript("""
                CREATE TABLE honeypot_channels (channel_id INTEGER PRIMARY KEY, warning_message_id INTEGER);
                CREATE TABLE guild_honeypot_channels (
                    guild_id INTEGER NOT NULL, channel_id INTEGER NOT NULL,
                    warning_message_id INTEGER, PRIMARY KEY(guild_id, channel_id));
                CREATE TABLE guild_settings (
                    guild_id INTEGER NOT NULL, key TEXT NOT NULL, value TEXT,
                    PRIMARY KEY(guild_id, key));
                INSERT INTO honeypot_channels VALUES (123, NULL);
            """)
            conn.commit()
            conn.close()
            with patch.object(b, "db_connect", side_effect=lambda: sqlite3.connect(database)), \
                 patch.object(b, "legacy_fallback_allowed", return_value=True):
                self.assertEqual(set(b.hp_traps(901)), {123})
                b.hp_remove_trap(901, 123)
                self.assertEqual(b.hp_traps(901), {}, "La última trampa fue importada de nuevo")
                self.assertEqual(b.hp_traps(901), {})
                read = sqlite3.connect(database)
                try:
                    self.assertEqual(read.execute(
                        "SELECT value FROM guild_settings WHERE guild_id = ? "
                        "AND key = 'honeypot_legacy_traps_migrated'", (901,)
                    ).fetchone()[0], "1")
                finally:
                    read.close()

    def test_panel_count_matches_saved_traps_for_zero_one_two_three(self):
        guild = NS(id=901)
        for quantity in range(4):
            with self.subTest(quantity=quantity):
                traps = {300 + j: None for j in range(quantity)}
                with (
                    patch.object(b, "hp_traps", return_value=traps),
                    patch.object(b, "honeypot_enabled", return_value=quantity > 0),
                    patch.object(b, "honeypot_paused", return_value=False),
                    patch.object(b, "hp_action", return_value="log"),
                    patch.object(b, "hp_warning_enabled", return_value=False),
                    patch.object(b, "hp_warning_style", return_value="text"),
                    patch.object(b, "hp_exempt_ids", return_value=set()),
                    patch.object(b, "hp_total_triggers", return_value=0),
                    patch.object(b, "hp_retention_minutes", return_value=43200),
                ):
                    embed = b.hp_setup_embed(guild)
                state = embed.fields[0].value
                self.assertIn(f"**Canales trampa:** {quantity}", state)
                for j in range(quantity):
                    self.assertIn(f"<#{300 + j}>", state)
                self.assertEqual(state.count("<#"), quantity)
                if quantity == 0:
                    self.assertIn("Ninguno configurado", state)
                    self.assertIn("Desactivado", state)


    def test_zero_traps_are_explicit_in_panel(self):
        guild = NS(id=901)
        with (
            patch.object(b, "hp_traps", return_value={}),
            patch.object(b, "honeypot_enabled", return_value=False),
            patch.object(b, "honeypot_paused", return_value=False),
            patch.object(b, "hp_action", return_value="log"),
            patch.object(b, "hp_warning_enabled", return_value=False),
            patch.object(b, "hp_exempt_ids", return_value=set()),
            patch.object(b, "hp_total_triggers", return_value=0),
            patch.object(b, "hp_retention_minutes", return_value=43200),
        ):
            embed = b.hp_setup_embed(guild)
        self.assertIn("**Canales trampa:** 0 · Ninguno configurado", embed.fields[0].value)
        self.assertNotIn("<#", embed.fields[0].value)



if __name__ == "__main__":
    unittest.main()
