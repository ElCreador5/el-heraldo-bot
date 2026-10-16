"""Regresiones Honeypot: aislamiento multiservidor, antifallos y acceso administrativo."""
import unittest
from types import SimpleNamespace as NS
from unittest.mock import AsyncMock, MagicMock, call, patch

from test_safety_regressions import b, interaction


class HoneypotIsolationTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        b._hp_busy.clear()
        b._hp_veteran_hits.clear()

    def tearDown(self):
        b._hp_busy.clear()
        b._hp_veteran_hits.clear()

    @staticmethod
    def veteran(guild_id, user_id):
        now = b.datetime.now(b.timezone.utc)
        return NS(
            guild=NS(id=guild_id), id=user_id, mention=f"<@{user_id}>",
            joined_at=now - b.timedelta(days=45),
        )

    @staticmethod
    def message(member, message_id):
        return NS(
            guild=member.guild, author=member, id=message_id,
            channel=NS(id=member.guild.id + 1000),
            content="Mensaje de prueba", attachments=[], webhook_id=None,
        )

    async def test_misfire_counts_only_distinct_veterans_of_same_guild(self):
        punish = AsyncMock(return_value=(True, "Registrado"))
        paused = MagicMock()
        with (
            patch.object(b, "hp_action", return_value="role"),
            patch.object(b, "delete_with_evidence", new=AsyncMock(return_value=True)),
            patch.object(b, "hp_punish", new=punish),
            patch.object(b, "hp_log_trigger"),
            patch.object(b, "hp_report", new=AsyncMock()),
            patch.object(b, "hp_setting_set", paused),
            patch.object(b, "log_embed", new=AsyncMock()),
        ):
            for guild_id, user_id in [(101, 11), (202, 21), (101, 12)]:
                member = self.veteran(guild_id, user_id)
                await b.hp_handle_trigger(self.message(member, user_id), member)
            paused.assert_not_called()
            self.assertEqual(punish.await_count, 3)

            # El tercer veterano del servidor 101 pausa solo ese servidor.
            member = self.veteran(101, 13)
            await b.hp_handle_trigger(self.message(member, 13), member)
            paused.assert_called_once_with(101, "honeypot_paused", "1")
            self.assertEqual(punish.await_count, 3)
            self.assertEqual({guild_id for _, guild_id, _ in b._hp_veteran_hits}, {202})

            # Las detecciones de 202 siguen contando; no se borran al pausar 101.
            for user_id in (22, 23):
                member = self.veteran(202, user_id)
                await b.hp_handle_trigger(self.message(member, user_id), member)
            self.assertEqual(paused.call_args_list, [
                call(101, "honeypot_paused", "1"),
                call(202, "honeypot_paused", "1"),
            ])
            self.assertEqual(punish.await_count, 4)
            self.assertEqual(b._hp_veteran_hits, [])

    async def test_busy_lock_isolated_by_guild_and_keeps_same_guild_dedup(self):
        first = MagicMock(spec=b.discord.Member)
        second = MagicMock(spec=b.discord.Member)
        for member, guild_id in ((first, 101), (second, 202)):
            member.id = 500
            member.guild = NS(id=guild_id)
            member.roles = []
            member.bot = False
        initial = self.message(first, 1101)
        same_guild_duplicate = self.message(first, 1102)
        second_guild = self.message(second, 2201)
        seen = []

        async def handle(message, member):
            seen.append((member.guild.id, member.id, message.id))
            if member.guild.id == 101:
                # Anidar eventos mientras 101 está ocupado reproduce la concurrencia.
                await b.honeypot_listener(same_guild_duplicate)
                await b.honeypot_listener(second_guild)

        deleted = AsyncMock(return_value=True)
        with (
            patch.object(b, "honeypot_enabled", return_value=True),
            patch.object(b, "honeypot_paused", return_value=False),
            patch.object(b, "hp_trap_ids", side_effect=lambda gid: {gid + 1000}),
            patch.object(b, "hp_is_exempt", return_value=False),
            patch.object(b, "hp_punish_role_id", return_value=0),
            patch.object(b, "hp_handle_trigger", new=handle),
            patch.object(b, "delete_with_evidence", new=deleted),
        ):
            await b.honeypot_listener(initial)
        self.assertEqual(seen, [(101, 500, 1101), (202, 500, 2201)])
        deleted.assert_awaited_once_with(same_guild_duplicate.channel, 1102)
        self.assertEqual(b._hp_busy, set())

    async def test_history_rechecks_permission_before_reading_private_events(self):
        denied = interaction(allowed=False)
        allowed = interaction(allowed=True)
        with patch.object(b, "hp_recent_triggers", return_value=[]) as fetch:
            await b.honeypot_history.callback(denied, cantidad=3)
            fetch.assert_not_called()
            denied.response.send_message.assert_awaited_once()
            self.assertIn("Acceso denegado", denied.response.send_message.call_args.args[0])

            await b.honeypot_history.callback(allowed, cantidad=3)
            fetch.assert_called_once_with(901, 3)
            self.assertIn("Aún no", allowed.response.send_message.call_args.args[0])

    async def test_misfire_prunes_expired_hits_without_pausing_other_guild(self):
        now = b.datetime.now(b.timezone.utc)
        b._hp_veteran_hits.extend([
            (now - b.timedelta(minutes=6), 101, 8),
            (now - b.timedelta(minutes=1), 202, 9),
        ])
        member = self.veteran(101, 11)
        with (
            patch.object(b, "hp_action", return_value="log"),
            patch.object(b, "delete_with_evidence", new=AsyncMock(return_value=True)),
            patch.object(b, "hp_punish", new=AsyncMock(return_value=(True, "Registro"))),
            patch.object(b, "hp_log_trigger"),
            patch.object(b, "hp_report", new=AsyncMock()),
            patch.object(b, "hp_setting_set") as pause,
        ):
            await b.hp_handle_trigger(self.message(member, 1011), member)
        pause.assert_not_called()
        self.assertEqual(
            {(guild_id, user_id) for _, guild_id, user_id in b._hp_veteran_hits},
            {(202, 9), (101, 11)},
        )


if __name__ == "__main__":
    unittest.main()
