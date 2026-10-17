"""Honeypot: expulsión/baneo explícitos, permisos y continuidad de casos."""
import unittest
from types import SimpleNamespace as NS
from unittest.mock import AsyncMock, patch

from test_safety_regressions import b, interaction


class HoneypotRemovalActionTests(unittest.IsolatedAsyncioTestCase):
    def make_member(self, *, kick=True, ban=True):
        guild = NS(
            id=901, owner_id=999,
            me=NS(
                top_role=100,
                guild_permissions=NS(kick_members=kick, ban_members=ban, administrator=False),
            ),
        )
        return NS(
            id=75, bot=False, guild=guild, top_role=10, mention="<@75>",
        )

    def test_old_sanction_values_never_become_automatic_bans_or_kicks(self):
        for value in ("kick", "ban", "", None, "unexpected"):
            with self.subTest(value=value), patch.object(b, "hp_setting_get", return_value=value):
                self.assertEqual(b.hp_action(901), "role")
        for value, action in (("kick_enabled", "kick"), ("ban_enabled", "ban")):
            with self.subTest(value=value), patch.object(b, "hp_setting_get", return_value=value):
                self.assertEqual(b.hp_action(901), action)
                self.assertEqual(b.hp_action_storage(action), value)

    def test_selection_includes_kick_and_ban_and_stays_a_draft(self):
        with (
            patch.object(b, "hp_traps", return_value={201: None}),
            patch.object(b, "honeypot_enabled", return_value=True),
            patch.object(b, "honeypot_paused", return_value=False),
            patch.object(b, "hp_action", return_value="role"),
        ):
            parent = b.HeraldoHoneypotSetupView(901, 10)
            view = b.HeraldoHoneypotActionView(parent)
            selector = next(c for c in view.children if isinstance(c, b.discord.ui.Select))
            self.assertEqual({x.value for x in selector.options}, {
                "role", "log", "timeout", "kick", "ban",
            })
            self.assertEqual(next(x.label for x in selector.options if x.value == "kick"), "Expulsar")
            self.assertEqual(next(x.label for x in selector.options if x.value == "ban"), "Banear")

    async def test_ban_choice_only_stages_and_discard_does_not_save(self):
        with (
            patch.object(b, "hp_traps", return_value={201: None}),
            patch.object(b, "honeypot_enabled", return_value=True),
            patch.object(b, "honeypot_paused", return_value=False),
            patch.object(b, "hp_action", return_value="role"),
            patch.object(b, "hp_setup_embed", return_value=b.discord.Embed()),
            patch.object(b, "hp_setting_set") as save,
        ):
            parent = b.HeraldoHoneypotSetupView(901, 10)
            editor = b.HeraldoHoneypotActionView(parent)
            i = interaction()
            i.data = {"values": ["ban"]}
            await editor.choose(i)
            self.assertEqual(parent.pending_action, "ban")
            save.assert_not_called()
            await parent.discard_changes.callback(interaction())
            self.assertIsNone(parent.pending_action)
            save.assert_not_called()

    async def test_panel_save_requires_admin_permission_for_ban(self):
        with (
            patch.object(b, "hp_traps", return_value={201: None}),
            patch.object(b, "honeypot_enabled", return_value=True),
            patch.object(b, "honeypot_paused", return_value=False),
            patch.object(b, "hp_action", return_value="role"),
            patch.object(b, "hp_setting_set") as save,
        ):
            view = b.HeraldoHoneypotSetupView(901, 10)
            view.pending_action = "ban"
            i = interaction()
            i.guild.me = self.make_member().guild.me
            await view.save_changes.callback(i)
            save.assert_not_called()
            self.assertIn("Banear miembros", i.response.send_message.call_args.args[0])

    async def test_panel_save_requires_bot_permission_for_kick(self):
        with (
            patch.object(b, "hp_traps", return_value={201: None}),
            patch.object(b, "honeypot_enabled", return_value=True),
            patch.object(b, "honeypot_paused", return_value=False),
            patch.object(b, "hp_action", return_value="role"),
            patch.object(b, "hp_setting_set") as save,
        ):
            view = b.HeraldoHoneypotSetupView(901, 10)
            view.pending_action = "kick"
            i = interaction()
            i.user.guild_permissions = b.discord.Permissions(manage_guild=True, kick_members=True)
            i.guild.me = self.make_member(kick=False).guild.me
            await view.save_changes.callback(i)
            save.assert_not_called()
            self.assertIn("El Heraldo necesita", i.response.send_message.call_args.args[0])

    async def test_explicit_save_serializes_new_action_safely(self):
        with (
            patch.object(b, "hp_traps", return_value={201: None}),
            patch.object(b, "honeypot_enabled", return_value=True),
            patch.object(b, "honeypot_paused", return_value=False),
            patch.object(b, "hp_action", return_value="role"),
            patch.object(b, "hp_setting_set") as save,
            patch.object(b, "hp_setup_embed", return_value=b.discord.Embed()),
        ):
            view = b.HeraldoHoneypotSetupView(901, 10)
            view.pending_action = "ban"
            i = interaction()
            i.user.guild_permissions = b.discord.Permissions(manage_guild=True, ban_members=True)
            i.guild.me = self.make_member().guild.me
            await view.save_changes.callback(i)
            save.assert_called_once_with(901, "honeypot_action", "ban_enabled")
            i.response.defer.assert_awaited_once()

    async def test_slash_setup_uses_explicit_action_and_confirmation(self):
        i = interaction()
        i.user.guild_permissions = b.discord.Permissions(manage_guild=True, ban_members=True)
        i.guild.me = self.make_member().guild.me
        choice = b.discord.app_commands.Choice(name="Banear", value="ban_enabled")
        with (
            patch.object(b, "hp_traps", return_value={201: None}),
            patch.object(b, "hp_action", return_value="role"),
            patch.object(b, "confirm_configuration", new=AsyncMock()) as proposal,
        ):
            await b.honeypot_config.callback(i, accion=choice)
        proposal.assert_awaited_once()
        self.assertEqual(proposal.await_args.args[2]["honeypot_action"], "ban_enabled")

    async def test_kick_executes_once_and_records_case(self):
        member = self.make_member()
        with (
            patch.object(b, "heraldo_kick", new=AsyncMock()) as kick,
            patch.object(b, "heraldo_ban", new=AsyncMock()) as ban,
            patch.object(b, "hp_start_kick_purge", return_value="purga solicitada en segundo plano (1 d)") as purge,
            patch.object(b, "moderation_case_create", return_value=7) as record,
            patch.object(b, "moderation_case_code", return_value="XY8ZD72"),
        ):
            ok, note = await b.hp_punish(member, "kick", 202)
        self.assertTrue(ok)
        self.assertIn("Expulsado", note)
        self.assertIn("XY8ZD72", note)
        kick.assert_awaited_once_with(member, reason="Honeypot: escribió en un canal trampa")
        ban.assert_not_awaited()
        purge.assert_called_once_with(member)
        self.assertIn("purga solicitada", note)
        args, opts = record.call_args
        self.assertEqual(args[:3], (901, "KICK", 75))
        self.assertIsNone(opts["author_id"])
        self.assertIn("202", opts["moderator_notes"])

    async def test_ban_uses_default_moderation_duration_and_no_bulk_purge(self):
        member = self.make_member()
        with (
            patch.object(b, "heraldo_kick", new=AsyncMock()) as kick,
            patch.object(b, "heraldo_ban", new=AsyncMock(return_value=5)) as ban,
            patch.object(b, "moderation_case_create", return_value=8) as record,
            patch.object(b, "moderation_case_code", return_value="XY8ZD73"),
            patch.object(b, "hp_start_purge") as purge,
        ):
            ok, note = await b.hp_punish(member, "ban", 203)
        self.assertTrue(ok)
        self.assertIn("Baneado", note)
        kick.assert_not_awaited()
        purge.assert_not_called()
        self.assertEqual(ban.await_args.kwargs["delete_message_seconds"], 0)
        self.assertEqual(ban.await_args.kwargs["record_case"], False)
        self.assertEqual(ban.await_args.kwargs["duration_minutes"], None)
        args, opts = record.call_args
        self.assertEqual(args[:3], (901, "BAN", 75))
        self.assertEqual(opts["duration_minutes"], 5)

    async def test_permission_revoked_at_trigger_blocks_destructive_action(self):
        member = self.make_member(ban=False)
        with (
            patch.object(b, "heraldo_ban", new=AsyncMock()) as ban,
            patch.object(b, "moderation_case_create") as record,
        ):
            ok, note = await b.hp_punish(member, "ban", 201)
        self.assertFalse(ok)
        self.assertIn("El Heraldo necesita", note)
        ban.assert_not_awaited()
        record.assert_not_called()

    async def test_hierarchy_and_guild_owner_are_protected(self):
        member = self.make_member()
        with patch.object(b, "heraldo_ban", new=AsyncMock()) as ban:
            member.id = member.guild.owner_id
            ok, _ = await b.hp_punish(member, "ban", 202)
            self.assertFalse(ok)
            member.id = 75
            member.top_role = 100
            ok, _ = await b.hp_punish(member, "ban", 202)
            self.assertFalse(ok)
            ban.assert_not_awaited()

    async def test_discord_failure_does_not_register_case(self):
        member = self.make_member()
        # Discord HTTPException es la clase base de Forbidden/NotFound.
        exc = b.discord.HTTPException(
            response=NS(status=403, reason="Forbidden", headers={}),
            message="No puede expulsar",
        )
        with (
            patch.object(b, "heraldo_kick", new=AsyncMock(side_effect=exc)) as kick,
            patch.object(b, "hp_start_kick_purge") as purge,
            patch.object(b, "moderation_case_create") as record,
        ):
            ok, note = await b.hp_punish(member, "kick", 202)
        self.assertFalse(ok)
        self.assertIn("Discord", note)
        kick.assert_awaited_once()
        purge.assert_not_called()
        record.assert_not_called()

    async def test_case_failure_does_not_retry_sanction_and_is_reported(self):
        member = self.make_member()
        with (
            patch.object(b, "heraldo_ban", new=AsyncMock(return_value=5)) as ban,
            patch.object(b, "moderation_case_create", side_effect=RuntimeError("SQLite unavailable")),
            patch.object(b.traceback, "print_exc"),
        ):
            ok, note = await b.hp_punish(member, "ban", 202)
        self.assertTrue(ok)
        self.assertIn("Requiere revisión", note)
        ban.assert_awaited_once()

    def test_embed_hides_role_and_shows_only_ban_duration(self):
        guild = NS(id=901)
        with (
            patch.object(b, "hp_traps", return_value={202: None}),
            patch.object(b, "hp_action", return_value="ban"),
            patch.object(b, "honeypot_enabled", return_value=True),
            patch.object(b, "honeypot_paused", return_value=False),
            patch.object(b, "moderation_default_ban_minutes", return_value=5),
            patch.object(b, "hp_warning_enabled", return_value=False),
            patch.object(b, "hp_exempt_ids", return_value=set()),
            patch.object(b, "hp_total_triggers", return_value=1),
            patch.object(b, "hp_retention_minutes", return_value=43200),
        ):
            embed = b.hp_setup_embed(guild)
        self.assertIn("Banear", embed.fields[1].value)
        self.assertIn("5 min", embed.fields[1].value)
        self.assertNotIn("Rol:", embed.fields[1].value)
        self.assertNotIn("Aislamiento:", embed.fields[1].value)


if __name__ == "__main__":
    unittest.main()
