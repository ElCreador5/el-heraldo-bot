"""Plazos y exclusión real entre edad y personalidad; SQLite sintética, sin Gateway."""
import asyncio
from contextlib import ExitStack
from types import SimpleNamespace as NS
from unittest.mock import AsyncMock, patch
import unittest

from test_safety_regressions import b


class PersonalityDeadlineTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.gid, self.uid = 987690, 72
        self.now = b.datetime.now(b.timezone.utc)
        self.member = NS(id=self.uid, roles=[], mention='<@72>')
        self.guild = NS(id=self.gid, owner_id=1, get_member=lambda _: self.member)
        self.member.guild = self.guild
        b.db_upsert_join(self.gid, self.uid, self.now)
        b.db_clear_tentado(self.gid, self.uid)
        b.db_clear_verify_pending(self.gid, self.uid)
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        for name, value in [('condemnation_get', None), ('hp_punish_role_id', None),
                            ('get_eval_role_ids', {91}), ('orientation_enabled', True),
                            ('personality_required', True), ('heraldo_is_test', False),
                            ('get_orientation_window', b.timedelta(minutes=10))]:
            self.stack.enter_context(patch.object(b, name, return_value=value))
        self.stack.enter_context(patch.object(b.bot, 'get_guild', return_value=self.guild))
        self.kick = self.stack.enter_context(patch.object(b, 'heraldo_kick', new=AsyncMock()))
        self.dm = self.stack.enter_context(patch.object(b, 'send_recovery_dm', new=AsyncMock(return_value=True)))
        self.stack.enter_context(patch.object(b, 'prepare_removal_dm', new=AsyncMock(return_value=None)))
        self.addCleanup(b._verification_expiry_inflight.discard, (self.gid, self.uid))

    def mark(self, minutes):
        b.db_set_tentado(self.gid, self.uid, self.now - b.timedelta(minutes=minutes))

    async def test_mass_check_cannot_expire_unfinished_window(self):
        self.mark(2)
        self.assertEqual(await b.evaluate_member(self.gid, self.uid, report=False), 'pendiente')
        self.kick.assert_not_awaited()
        self.dm.assert_not_awaited()

    async def test_old_timer_rechecks_extended_configuration(self):
        self.mark(11)
        with patch.object(b, 'get_orientation_window', return_value=b.timedelta(minutes=20)):
            await b.evaluate_member(self.gid, self.uid, report=False)
        self.kick.assert_not_awaited()
        self.assertIsNotNone(b.db_get(self.gid, self.uid)['tentado_at'])

    async def test_old_timer_cannot_expire_rearmed_mark(self):
        self.mark(0)
        await b.evaluate_member(self.gid, self.uid, report=False)
        self.kick.assert_not_awaited()

    async def test_role_without_persisted_clock_never_kicks(self):
        self.assertEqual(await b.evaluate_member(self.gid, self.uid, report=False), 'sin-plazo')
        self.kick.assert_not_awaited()

    async def test_age_sanction_inflight_blocks_personality(self):
        self.mark(11)
        b._verification_expiry_inflight.add((self.gid, self.uid))
        self.assertEqual(await b.evaluate_member(self.gid, self.uid, report=False), 'pendiente')
        self.kick.assert_not_awaited()

    async def test_two_personality_evaluations_only_kick_once(self):
        self.mark(11)
        b.db_set_verify_pending(self.gid, self.uid, self.now)
        entered, finish = asyncio.Event(), asyncio.Event()
        async def delayed_kick(*args, **kwargs):
            entered.set()
            await finish.wait()
        self.kick.side_effect = delayed_kick
        first = asyncio.create_task(b.evaluate_member(self.gid, self.uid, report=False))
        try:
            await asyncio.wait_for(entered.wait(), 2)
            self.assertEqual(await b.evaluate_member(self.gid, self.uid, report=False), 'pendiente')
        finally:
            finish.set()
            self.assertEqual(await first, 'expulsado')
        self.kick.assert_awaited_once()
        row = b.db_get(self.gid, self.uid)
        self.assertIsNone(row['tentado_at'])
        self.assertIsNone(row['verify_pending_at'])
        self.assertEqual(await b.evaluate_member(self.gid, self.uid, report=False), 'sin-plazo')

    async def test_failed_kick_preserves_both_clocks_and_releases_lock(self):
        self.mark(11)
        b.db_set_verify_pending(self.gid, self.uid, self.now)
        self.kick.side_effect = b.discord.HTTPException(NS(status=403, reason='simulado'), 'rechazado')
        self.assertEqual(await b.evaluate_member(self.gid, self.uid, report=False), 'pendiente')
        row = b.db_get(self.gid, self.uid)
        self.assertIsNotNone(row['tentado_at'])
        self.assertIsNotNone(row['verify_pending_at'])
        self.assertNotIn((self.gid, self.uid), b._verification_expiry_inflight)
        self.kick.side_effect = None
        self.assertEqual(await b.evaluate_member(self.gid, self.uid, report=False), 'expulsado')


class PersonalitySelectorConstructionTests(unittest.IsolatedAsyncioTestCase):
    async def test_both_selectors_and_current_flags_are_present_without_writes(self):
        guild_id = 987699
        b.guild_config_set(guild_id, 'personality_required', '0')
        b.guild_config_set(guild_id, 'personality_allow_change', '0')
        with patch.object(b, 'guild_config_set') as write:
            view = b.HeraldoOrientationSetupView(guild_id, 12)
        channels = [c for c in view.children if isinstance(c, b.discord.ui.ChannelSelect)]
        roles = [c for c in view.children if isinstance(c, b.discord.ui.RoleSelect)]
        self.assertEqual(len(channels), 1)
        self.assertEqual(len(roles), 1)
        self.assertEqual(channels[0].callback, view.select_channel)
        self.assertEqual(roles[0].callback, view.select_roles)
        self.assertEqual(view.toggle_required.label, 'Expulsar si no elige: No')
        self.assertEqual(view.toggle_change.label, 'Cambiar elección: No')
        self.assertEqual(view._snapshot()['personality_required'], '0')
        write.assert_not_called()


if __name__ == '__main__':
    unittest.main()
