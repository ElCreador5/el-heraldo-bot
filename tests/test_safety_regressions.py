"""Regresiones de moderación y configuración, sin Gateway ni datos reales."""
import importlib.util
import os
from pathlib import Path
import sys
import tempfile
import unittest
from types import SimpleNamespace as NS
from unittest.mock import AsyncMock, MagicMock, patch

_tmp = tempfile.TemporaryDirectory()
os.environ['DB_PATH'] = str(Path(_tmp.name) / 'safety.db')
spec = importlib.util.spec_from_file_location('heraldo_safety', Path(__file__).resolve().parents[1] / 'bot.py')
b = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = b
spec.loader.exec_module(b)
b.db_init()
b.honeypot_db_init()


def interaction(allowed=True, guild_id=901):
    return NS(guild=NS(id=guild_id), guild_id=guild_id,
              user=NS(id=10, guild_permissions=b.discord.Permissions(manage_guild=allowed)),
              response=NS(is_done=lambda: False, send_message=AsyncMock(), edit_message=AsyncMock()),
              followup=NS(send=AsyncMock()))


class SafetyTests(unittest.IsolatedAsyncioTestCase):
    async def test_departure_without_audit_does_not_claim_voluntary_exit(self):
        member = NS(guild=NS(me=NS(guild_permissions=NS(view_audit_log=False))))
        kind, _, _, uncertainty = await b.classify_member_departure(member)
        self.assertEqual(kind, 'member_leave')
        self.assertIn('No se pudo confirmar', uncertainty)

    async def test_departure_retries_delayed_audit(self):
        attempts = []
        async def audit(**kwargs):
            attempts.append(kwargs)
            if len(attempts) == 4:
                yield NS(target=NS(id=11), created_at=b.datetime.now(b.timezone.utc),
                         user='moderador', reason='motivo')
        member = NS(id=11, guild=NS(me=NS(guild_permissions=NS(view_audit_log=True)), audit_logs=audit))
        with patch.object(b.asyncio, 'sleep', new=AsyncMock()):
            result = await b.classify_member_departure(member)
        self.assertEqual(result, ('member_kick', 'moderador', 'motivo', None))
        self.assertEqual(len(attempts), 4)

    async def test_evidence_rejects_other_authors_before_fallback(self):
        with patch.object(b, 'condemnation_fetch_source_message', new=AsyncMock(return_value=NS(author=NS(id=22)))):
            result = await b.condemnation_archive_evidence(NS(id=901), NS(id=11),
                source_message_url='source', reason='Prueba', applied_by=None)
        self.assertEqual(result, (None, None))

    async def test_self_service_denies_administrative_roles(self):
        self.assertTrue(b.self_service_role_safe(NS(permissions=b.discord.Permissions.none())))
        for permission in ('administrator', 'manage_roles', 'manage_guild', 'ban_members', 'manage_webhooks'):
            self.assertFalse(b.self_service_role_safe(NS(permissions=b.discord.Permissions(**{permission: True}))))

    async def test_condemned_member_cannot_use_role_component(self):
        member = MagicMock(spec=b.discord.Member)
        member.id = 11
        role = MagicMock(spec=b.discord.Role)
        role.id = 12
        role.is_default.return_value = False
        role.managed = False
        role.__ge__.return_value = False
        role.permissions = b.discord.Permissions.none()
        guild = NS(id=901, get_role=lambda _: role, me=NS(top_role=role,
            guild_permissions=NS(manage_roles=True)))
        i = interaction()
        i.guild, i.user = guild, member
        with (patch.object(b, 'heraldo_message_role_config', return_value=[{'role_id': 12, 'action': 'añadir'}]),
              patch.object(b, 'condemnation_get', return_value={'active': 1})):
            await b.heraldo_message_role_action(i, 901, 12, 'añadir')
        member.add_roles.assert_not_called()
        self.assertIn('condena activa', i.response.send_message.call_args.args[0])

    async def asyncSetUp(self):
        b._condemn_inflight.clear()

    async def test_new_condemnation_persists_configured_role(self):
        guild = MagicMock(id=901)
        member = NS(id=11, guild=guild, roles=[], mention='<@11>')
        with (patch.object(b, 'condemnation_get', return_value=None),
              patch.object(b, 'hp_punish_role_id', return_value=456),
              patch.object(b, 'condemnation_sync_roles', new=AsyncMock(return_value=(True, [], 'OK'))),
              patch.object(b, 'condemnation_save') as save,
              patch.object(b, 'condemnation_archive_evidence', new=AsyncMock(return_value=(None, None))),
              patch.object(b, 'log_embed', new=AsyncMock())):
            await b._condemn_member_inner(member, reason='Prueba', duration_minutes=5, purge_spec=None,
                origin='manual', applied_by=None, preserve_role_ids=None, source_message_url=None,
                source_channel_id=None, send_dm=False, announce=False)
        self.assertEqual(save.call_args.args[2], 456)

    async def test_same_member_different_guild_does_not_block(self):
        member = NS(id=11, guild=NS(id=902), bot=False)
        b._condemn_inflight.add((901, 11))
        with (patch.object(b, 'condemnation_protection_reason', return_value=None),
              patch.object(b, '_condemn_member_inner', new=AsyncMock(return_value=(True, 'OK'))) as inner):
            result = await b.condemn_member(member, reason='Prueba', duration_minutes=1,
                purge_spec=None, origin='manual', applied_by=None)
        self.assertTrue(result[0])
        inner.assert_awaited_once()

    async def test_release_during_condemnation_is_rejected(self):
        member = NS(id=11, guild=NS(id=901))
        b._condemn_inflight.add((901, 11))
        with patch.object(b, '_release_condemned_member_inner', new=AsyncMock()) as inner:
            result = await b.release_condemned_member(member)
        self.assertFalse(result[0])
        inner.assert_not_awaited()

    async def test_release_lock_is_cleaned_after_failure(self):
        member = NS(id=11, guild=NS(id=901))
        with patch.object(b, '_release_condemned_member_inner', new=AsyncMock(side_effect=RuntimeError)):
            with self.assertRaises(RuntimeError):
                await b.release_condemned_member(member)
        self.assertNotIn((901, 11), b._condemn_inflight)

    async def test_configuration_cancel_and_save(self):
        b.guild_config_set(901, 'safety_test', 'old')
        view = b.ConfigurationConfirmView(901, 10, {'safety_test': 'new'})
        await view.cancel.callback(interaction())
        self.assertEqual(b.guild_config_get(901, 'safety_test'), 'old')
        view = b.ConfigurationConfirmView(901, 10, {'safety_test': 'new'})
        await view.save.callback(interaction())
        self.assertEqual(b.guild_config_get(901, 'safety_test'), 'new')

    async def test_configuration_rejects_stale_draft(self):
        b.guild_config_set(901, 'safety_test', 'old')
        view = b.ConfigurationConfirmView(901, 10, {'safety_test': 'new'})
        b.guild_config_set(901, 'safety_test', 'concurrent')
        await view.save.callback(interaction())
        self.assertEqual(b.guild_config_get(901, 'safety_test'), 'concurrent')

    async def test_lost_permission_blocks_confirm_and_join_panel(self):
        for view in (b.HeraldoMessageConfirmView(901, 10, 'kit', {'items': []}),
                     b._JoinRolesOwnedView(901, 10),
                     b.ConfigurationConfirmView(901, 10, {'safety_test': 'forbidden'})):
            self.assertFalse(await view.interaction_check(interaction(False)))

    async def test_other_guild_blocked(self):
        view = b._JoinRolesOwnedView(901, 10)
        self.assertFalse(await view.interaction_check(interaction(guild_id=902)))

    async def test_condemnation_design_modal_only_proposes(self):
        modal = b.CondemnationCoreModal(901)
        modal.title_input._value = 'Título pendiente'
        i = interaction()
        with patch.object(b, 'condemnation_template_set') as save:
            await modal.on_submit(i)
        save.assert_not_called()
        self.assertIsInstance(i.response.send_message.call_args.kwargs['view'], b.ConfigurationConfirmView)

    async def test_channel_selector_has_no_invalid_emoji(self):
        view = b.HeraldoChannelSetupView(901, 10)
        for child in view.children:
            for option in getattr(child, 'options', []):
                self.assertIsNone(option.emoji)

    async def test_expiry_fetches_member_when_cache_misses(self):
        b.condemnation_save(99, 901, 456, [], 'Prueba', 1, 'manual', None,
            condemned_at=b.datetime.now(b.timezone.utc) - b.timedelta(minutes=2))
        guild = MagicMock()
        guild.get_member.return_value = None
        guild.fetch_member = AsyncMock(return_value=NS(id=99))
        with (patch.object(b.bot, 'get_guild', return_value=guild),
              patch.object(b, 'release_condemned_member', new=AsyncMock()) as release):
            await b.check_expired_condemnations()
        guild.fetch_member.assert_awaited_with(99)
        release.assert_awaited()

    async def test_expiry_preserves_case_when_guild_unavailable(self):
        b.condemnation_save(99, 901, 456, [], 'Prueba', 1, 'manual', None,
            condemned_at=b.datetime.now(b.timezone.utc) - b.timedelta(minutes=2))
        with patch.object(b.bot, 'get_guild', return_value=None):
            await b.check_expired_condemnations()
        self.assertIsNotNone(b.condemnation_get(901, 99))


if __name__ == '__main__':
    unittest.main()
