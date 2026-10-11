"""Dos temporizadores de verificación sobre el mismo ingreso, sin Gateway."""
import asyncio
import unittest
from contextlib import ExitStack
from types import SimpleNamespace as NS
from unittest.mock import AsyncMock, patch
from test_safety_regressions import b


class VerificationExpiryTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.guild_id, self.user_id = 908001, 20
        self.now = b.datetime.now(b.timezone.utc)
        b.db_set_verify_pending(self.guild_id, self.user_id, self.now - b.timedelta(minutes=10))
        b.db_set_sin_verificado(self.guild_id, self.user_id, self.now - b.timedelta(minutes=10))
        self.member = NS(id=self.user_id, mention='<@20>', roles=[NS(id=40)], kick=AsyncMock(), ban=AsyncMock())
        self.guild = NS(id=self.guild_id, get_member=lambda _: self.member)
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.stack.enter_context(patch.object(b.bot, 'get_guild', return_value=self.guild))
        self.stack.enter_context(patch.object(b, 'condemnation_get', return_value=None))
        self.stack.enter_context(patch.object(b, 'verify_enabled', return_value=True))
        self.stack.enter_context(patch.object(b, 'get_sin_verificado_role_id', return_value=40))
        self.stack.enter_context(patch.object(b, 'get_verify_role_id', return_value=41))
        self.stack.enter_context(patch.object(b, 'get_eval_role_ids', return_value={42}))
        self.stack.enter_context(patch.object(b, 'get_verify_timeout', return_value=300))
        self.stack.enter_context(patch.object(b, 'get_sin_verificado_window', return_value=b.timedelta(seconds=300)))
        self.action = self.stack.enter_context(patch.object(b, 'get_verify_action', return_value='kick'))
        self.log = self.stack.enter_context(patch.object(b, 'log_embed', new=AsyncMock()))

    def assert_resolved(self):
        row = b.db_get(self.guild_id, self.user_id)
        self.assertIsNone(row['verify_pending_at'])
        self.assertIsNone(row['sin_verificado_at'])

    async def test_primary_then_role_fallback_expels_and_logs_once(self):
        await b.evaluate_verify_timeout(self.guild_id, self.user_id)
        await b.evaluate_sin_verificado(self.guild_id, self.user_id)
        self.member.kick.assert_awaited_once()
        self.log.assert_awaited_once()
        self.assert_resolved()

    async def test_role_fallback_respects_configured_ban(self):
        self.action.return_value = 'ban'
        await b.evaluate_sin_verificado(self.guild_id, self.user_id)
        await b.evaluate_verify_timeout(self.guild_id, self.user_id)
        self.member.ban.assert_awaited_once()
        self.member.kick.assert_not_awaited()
        self.log.assert_awaited_once()
        self.assert_resolved()

    async def test_role_fallback_respects_log_only_action(self):
        self.action.return_value = 'none'
        await b.evaluate_sin_verificado(self.guild_id, self.user_id)
        await b.evaluate_verify_timeout(self.guild_id, self.user_id)
        self.member.kick.assert_not_awaited()
        self.member.ban.assert_not_awaited()
        self.log.assert_awaited_once()
        self.assert_resolved()

    async def test_role_fallback_does_not_shorten_extended_primary_deadline(self):
        b.db_set_verify_pending(self.guild_id, self.user_id, self.now)
        await b.evaluate_sin_verificado(self.guild_id, self.user_id)
        self.member.kick.assert_not_awaited()
        self.log.assert_not_awaited()

    async def test_stale_role_timer_cannot_expire_a_new_role_mark(self):
        b.db_clear_verify_pending(self.guild_id, self.user_id)
        b.db_set_sin_verificado(self.guild_id, self.user_id, self.now)
        await b.evaluate_sin_verificado(self.guild_id, self.user_id)
        self.member.kick.assert_not_awaited()

    async def test_standalone_role_fallback_still_expels_once(self):
        b.db_clear_verify_pending(self.guild_id, self.user_id)
        await b.evaluate_sin_verificado(self.guild_id, self.user_id)
        await b.evaluate_sin_verificado(self.guild_id, self.user_id)
        self.member.kick.assert_awaited_once()
        self.log.assert_awaited_once()
        self.assert_resolved()

    async def test_verified_member_is_not_expired_by_either_timer(self):
        self.member.roles.append(NS(id=41))
        await b.evaluate_sin_verificado(self.guild_id, self.user_id)
        await b.evaluate_verify_timeout(self.guild_id, self.user_id)
        self.member.kick.assert_not_awaited()
        self.log.assert_not_awaited()
        self.assert_resolved()

    async def test_concurrent_timers_share_one_remote_action(self):
        started, finish = asyncio.Event(), asyncio.Event()
        async def kick(**kwargs):
            started.set()
            await finish.wait()
        self.member.kick.side_effect = kick
        first = asyncio.create_task(b.evaluate_verify_timeout(self.guild_id, self.user_id))
        try:
            await asyncio.wait_for(started.wait(), 1)
            await asyncio.wait_for(b.evaluate_sin_verificado(self.guild_id, self.user_id), 1)
        finally:
            finish.set()
            await first
        self.member.kick.assert_awaited_once()
        self.log.assert_awaited_once()

    async def test_http_failure_preserves_pending_for_retry(self):
        self.member.kick.side_effect = b.discord.HTTPException(NS(status=500, reason='Simulado'), 'Fallo de prueba')
        await b.evaluate_verify_timeout(self.guild_id, self.user_id)
        row = b.db_get(self.guild_id, self.user_id)
        self.assertIsNotNone(row['verify_pending_at'])
        self.assertIsNotNone(row['sin_verificado_at'])
        self.assertNotIn('Expulsión por', self.log.call_args.args[1])
        self.member.kick.side_effect = None
        await b.evaluate_verify_timeout(self.guild_id, self.user_id)
        self.assertEqual(self.member.kick.await_count, 2)
        self.assert_resolved()

    async def test_standalone_fallback_failure_preserves_role_pending(self):
        b.db_clear_verify_pending(self.guild_id, self.user_id)
        self.member.kick.side_effect = b.discord.HTTPException(NS(status=500, reason='Simulado'), 'Fallo de prueba')
        await b.evaluate_sin_verificado(self.guild_id, self.user_id)
        self.assertIsNotNone(b.db_get(self.guild_id, self.user_id)['sin_verificado_at'])
        self.assertNotIn((self.guild_id, self.user_id), b._verification_expiry_inflight)
        self.assertNotIn('Expulsión por', self.log.call_args.args[1])

    async def test_same_member_in_other_guild_is_not_blocked(self):
        other_id = 908002
        b.db_set_verify_pending(other_id, self.user_id, self.now - b.timedelta(minutes=10))
        other_member = NS(id=self.user_id, mention='<@20>', roles=[], kick=AsyncMock(), ban=AsyncMock())
        other_guild = NS(id=other_id, get_member=lambda _: other_member)
        self.stack.enter_context(patch.object(b.bot, 'get_guild', return_value=other_guild))
        key = (self.guild_id, self.user_id)
        b._verification_expiry_inflight.add(key)
        try:
            await b.evaluate_verify_timeout(other_id, self.user_id)
        finally:
            b._verification_expiry_inflight.discard(key)
        other_member.kick.assert_awaited_once()
        self.member.kick.assert_not_awaited()
