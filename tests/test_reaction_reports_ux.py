"""Regresiones de reportes por reacción y navegación de /setup (sin Gateway)."""
import unittest
from types import SimpleNamespace as NS
from unittest.mock import AsyncMock, MagicMock, patch

from test_safety_regressions import b


class ReactionReportUxTests(unittest.IsolatedAsyncioTestCase):
    async def test_all_visible_setup_sections_open_and_serialize(self):
        guild = MagicMock(spec=b.discord.Guild)
        guild.id, guild.name, guild.owner_id = 987610, 'Laboratorio aislado', 10
        guild.roles, guild.channels, guild.text_channels, guild.members = [], [], [], []
        guild.get_channel.return_value = None
        guild.get_role.return_value = None
        for option in b.HeraldoSetupView(guild.id, 10).module_select.options:
            with self.subTest(section=option.value):
                view = b.HeraldoSetupView(guild.id, 10)
                i = NS(data={'values': [option.value]}, guild=guild,
                       response=NS(edit_message=AsyncMock(), send_message=AsyncMock()))
                await view.select_module(i)
                i.response.edit_message.assert_awaited_once()
                result = i.response.edit_message.call_args.kwargs['view']
                self.assertTrue(result.to_components())

    async def test_report_ledger_survives_connection_changes_and_isolates_guilds(self):
        args = (987611, 987612, 20, 'flag')
        self.assertEqual(b.moderation_report_record(*args, 11), (1, False))
        self.assertEqual(b.moderation_report_record(*args, 11), (1, False))
        self.assertEqual(b.moderation_report_record(*args, 12), (2, False))
        b.moderation_report_mark_executed(*args)
        self.assertEqual(b.moderation_report_record(*args, 13), (3, True))
        self.assertEqual(b.moderation_report_record(987613, *args[1:], 11), (1, False))

    async def test_rule_default_labels_round_trip_for_every_action(self):
        # El selector define la acción; el modal actual solo ajusta condiciones.
        for action in b.MODERATION_REPORT_ACTIONS:
            with self.subTest(action=action):
                original = {'emoji': '🚩', 'label': 'Infracción', 'action': 'report',
                            'duration_minutes': 30, 'threshold': 2, 'purge_minutes': 30}
                parent = NS(pending_reactions=None, selected_reaction_index=0,
                            _rebuild_reaction_select=MagicMock(), _content=lambda _: 'Borrador',
                            interaction_check=AsyncMock(return_value=True))
                parent._working_reactions = lambda: (
                    parent.pending_reactions if parent.pending_reactions is not None else [original]
                )
                selection = NS(data={'values': [action]}, guild=NS(id=901),
                               response=NS(edit_message=AsyncMock(), send_message=AsyncMock()))
                with patch.object(b, 'set_moderation_report_reactions') as saved:
                    await b.HeraldoUserReportsSetupView.select_action(parent, selection)
                    saved.assert_not_called()
                self.assertEqual(parent.pending_reactions[0]['action'], action)
                modal = b.ModerationReactionRuleModal(parent, 0)
                self.assertFalse(hasattr(modal, 'action'))
                modal.duration._value = '30m'
                modal.threshold._value = '2'
                modal.purge._value = '30m'
                submit = NS(guild=NS(id=901),
                            response=NS(edit_message=AsyncMock(), send_message=AsyncMock()))
                with patch.object(b, 'set_moderation_report_reactions') as saved:
                    await modal.on_submit(submit)
                    saved.assert_not_called()
                submit.response.edit_message.assert_awaited_once()
                rule = parent.pending_reactions[0]
                self.assertEqual(rule['action'], action)
                self.assertEqual(rule['threshold'], 1 if action == 'warn' else 2)
                self.assertEqual(rule['duration_minutes'],
                                 None if action in {'report', 'warn', 'kick'} else 30)
                self.assertEqual(rule['purge_minutes'],
                                 None if action in {'report', 'warn'} else 30)

    async def test_rule_modal_revoked_permission_cannot_mutate_draft(self):
        parent = NS(_working_reactions=lambda: [{'action': 'report', 'threshold': 1}],
                    interaction_check=AsyncMock(return_value=False), pending_reactions=None,
                    _rebuild_reaction_select=MagicMock(), _content=lambda _: 'Borrador')
        modal = b.ModerationReactionRuleModal(parent, 0)
        for field in (modal.duration, modal.threshold, modal.purge):
            field._value = field.default or ''
        await modal.on_submit(NS(guild=NS(id=901), response=NS(send_message=AsyncMock(), edit_message=AsyncMock())))
        self.assertIsNone(parent.pending_reactions)

    async def test_setup_selection_executes_real_navigation_callback(self):
        view = b.HeraldoSetupView(901, 10)
        i = NS(data={'values': ['moderation']}, guild=NS(id=901),
               response=NS(edit_message=AsyncMock(), send_message=AsyncMock()))
        await view.select_module(i)
        i.response.edit_message.assert_awaited_once()
        self.assertIsInstance(i.response.edit_message.call_args.kwargs['view'], b.HeraldoModerationSetupView)

    async def test_report_condemn_delegates_purge_to_evidence_safe_path(self):
        guild = NS(id=901, me=NS(guild_permissions=NS(manage_roles=True), top_role=100))
        member = NS(id=20, top_role=1)
        message = NS(jump_url="https://discord.com/channels/901/42/100", channel=NS(id=42))
        rule = {"action": "condemn", "label": "Reporte", "duration_minutes": 60, "purge_minutes": 30}
        with (
            patch.object(b, "condemnation_protection_reason", return_value=None),
            patch.object(b, "condemn_member", new=AsyncMock(return_value=(True, "Aplicada"))) as condemn,
            patch.object(b, "run_purge_job", new=AsyncMock()) as purge,
        ):
            success, note = await b.execute_moderation_report_action(guild, member, message, rule, 3)
        self.assertTrue(success)
        self.assertIn("condena aplicada", note)
        self.assertEqual(condemn.await_args.kwargs["purge_spec"], ("time", 30))
        self.assertEqual(condemn.await_args.kwargs["source_message_url"], message.jump_url)
        purge.assert_not_awaited()

    async def test_failed_report_condemn_never_purges(self):
        guild = NS(id=901, me=NS(guild_permissions=NS(manage_roles=True), top_role=100))
        member = NS(id=20, top_role=1)
        message = NS(jump_url="https://discord.com/channels/901/42/100", channel=NS(id=42))
        rule = {"action": "condemn", "label": "Reporte", "purge_minutes": 30}
        with (
            patch.object(b, "condemnation_protection_reason", return_value=None),
            patch.object(b, "condemn_member", new=AsyncMock(return_value=(False, "Rol no asignable"))),
            patch.object(b, "run_purge_job", new=AsyncMock()) as purge,
        ):
            success, note = await b.execute_moderation_report_action(guild, member, message, rule, 2)
        self.assertFalse(success)
        self.assertIn("Rol no asignable", note)
        purge.assert_not_awaited()

    async def test_reaction_resolves_member_and_posts_single_result(self):
        target = NS(id=20, bot=False, mention="<@20>")
        actor = NS(id=14, bot=False, mention="<@14>")
        message = NS(
            id=100,
            author=NS(id=20, bot=False),  # fetch_message devuelve User sin roles
            channel=NS(id=42, mention="#general"),
            jump_url="https://discord.com/channels/901/42/100",
            content="Mensaje de prueba",
        )
        source = NS(fetch_message=AsyncMock(return_value=message))
        reports = MagicMock(spec=b.discord.TextChannel)
        reports.send = AsyncMock()
        guild = NS(
            id=901,
            get_member=lambda uid: target if uid == 20 else None,
            get_channel_or_thread=lambda cid: source,
            get_channel=lambda cid: reports,
        )
        payload = NS(
            guild_id=901, user_id=14, member=actor, channel_id=42,
            message_id=100, emoji="🚩",
        )
        rule = {"emoji": "🚩", "label": "Inapropiado", "action": "condemn", "threshold": 1}
        b._moderation_report_dedupe.clear()
        b._moderation_report_pending.clear()
        with (
            patch.object(b.bot, "get_guild", return_value=guild),
            patch.object(b, "moderation_report_rule_for_emoji", return_value=rule),
            patch.object(b, "moderation_report_channel_id", return_value=77),
            patch.object(b, "moderation_report_record", return_value=(1, False)),
            patch.object(b, "moderation_report_mark_executed") as mark,
            patch.object(b, "execute_moderation_report_action", new=AsyncMock(return_value=(True, "condena aplicada"))) as act,
            patch.object(b, "log_embed", new=AsyncMock()) as log,
        ):
            await b.moderation_reaction_add(payload)
        act.assert_awaited_once()
        self.assertEqual(act.await_args.args[1], target)
        mark.assert_called_once()
        reports.send.assert_awaited_once()
        log.assert_not_awaited()
        self.assertIn("Resultado", [field.name for field in reports.send.await_args.kwargs["embed"].fields])

    async def test_setup_navigates_on_selection_without_extra_button(self):
        view = b.HeraldoSetupView(901, 10)
        self.assertNotIn("Configurar", [getattr(item, "label", None) for item in view.children])
        response = NS()
        i = NS(data={"values": ["moderation"]}, response=response)
        view.configure = AsyncMock()
        await view.select_module(i)
        view.configure.assert_awaited_once_with(i, None)


if __name__ == "__main__":
    unittest.main()
