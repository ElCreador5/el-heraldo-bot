"""Regresiones de reportes por reacción y navegación de /setup (sin Gateway)."""
import unittest
from types import SimpleNamespace as NS
from unittest.mock import AsyncMock, MagicMock, patch

from test_safety_regressions import b


class ReactionReportUxTests(unittest.IsolatedAsyncioTestCase):
    async def test_report_condemn_delegates_purge_to_evidence_safe_path(self):
        guild = NS(id=901)
        member = NS(id=20)
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
        guild = NS(id=901)
        member = NS(id=20)
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
