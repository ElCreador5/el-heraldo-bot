"""Cinco acciones contra el sistema central real; Discord aislado."""
from dataclasses import replace
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace as NS
import unittest
from unittest.mock import AsyncMock, Mock, patch
import discord

from test_safety_regressions import b
from custodio_core import RulesSnapshot
from custodio_discipline import CustodioDiscipline, ReviewedIncident, DisciplineBlocked
from evidence_archive import ledger


class DisciplineTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.path=str(Path(self.tmp.name)/'isolated.db')
        p=patch.object(b,'DB_PATH',self.path);p.start();self.addCleanup(p.stop)
        b.db_init()
        self.snapshot=RulesSnapshot(765,("No repetir mensajes publicitarios.",),'a'*64)
        self.reviewer=NS(id=7,top_role=50,guild_permissions=discord.Permissions(administrator=True))
        self.guild=NS(id=765,owner_id=99,me=NS(id=8,top_role=100,guild_permissions=discord.Permissions(ban_members=True,kick_members=True)),
                      get_member=lambda uid:self.reviewer if uid==7 else None)
        self.member=NS(id=9,guild=self.guild,bot=False,top_role=1,guild_permissions=discord.Permissions.none())
        self.guild.fetch_member=AsyncMock(return_value=self.member)
        not_found=discord.NotFound(NS(status=404,reason='NotFound'),{'code':10026,'message':'Unknown Ban'})
        self.guild.fetch_ban=AsyncMock(side_effect=not_found)
        self.channel=NS(fetch_message=AsyncMock(return_value=NS(author=NS(id=8))))
        p=patch('custodio_reports._get_safe_existing',return_value=self.channel);p.start();self.addCleanup(p.stop)
        p=patch('custodio_source.load_server_rules',new=AsyncMock(return_value=self.snapshot));p.start();self.addCleanup(p.stop)
        self.kick,self.ban,self.escalate=AsyncMock(),AsyncMock(),AsyncMock()
        self.engine=CustodioDiscipline({'DB_PATH':self.path,'db_connect':b.db_connect,
            'moderation_warning_create':b.moderation_warning_create,'moderation_case_create':b.moderation_case_create,
            'moderation_case_close':b.moderation_case_close,'heraldo_kick':self.kick,'heraldo_ban':self.ban,
            'moderation_warning_escalation':self.escalate})

    def incident(self, mid=1001):
        incident=ReviewedIncident(765,mid,9,1,'a'*64,f'https://discord.com/channels/765/5/{mid+1}')
        key=f'custodio-report:765:{mid}'
        ledger(self.path,key,'claim')
        ledger(self.path,key,'complete',[{'channel_id':5,'message_id':mid+1,'actor_id':9,'rule_number':1,'rules_revision':'a'*64}])
        return incident

    async def execute(self, action, mid=1001, **changes):
        return await self.engine.execute(self.guild,self.incident(mid),self.snapshot,action=action,
            **{**dict(verified=True,administrator_confirmed=True,moderator_id=7,duration_minutes=15),**changes})

    async def test_report_is_default_and_does_not_create_a_case(self):
        result=await self.execute('report')
        self.assertEqual(result['status'],'observed')
        self.assertEqual(b.moderation_warning_counts(765,9),(0,0))
        self.kick.assert_not_awaited();self.ban.assert_not_awaited()

    async def test_custodio_origin_survives_edit_and_closure_in_central_history(self):
        result=await self.execute('warn')
        case=result['case_number']
        b.moderation_case_update(765,case,notes='Nota del administrador sin traducir.')
        b.moderation_case_close(765,case,closed_by=7,resolution='Revisión completada.')
        row=b.moderation_case_get(765,case)
        self.assertEqual(b.moderation_case_origin(row),'Modo Custodio')
        self.assertTrue(row['moderator_notes'].startswith('custodio:'))
        self.guild.name='Synthetic Lab'
        embed=b.moderation_case_embed(self.guild,row)
        self.assertIn('Modo Custodio',[field.value for field in embed.fields])
        self.assertIn('Nota del administrador sin traducir.',[field.value for field in embed.fields])
        self.assertFalse(any('custodio:' in field.value for field in embed.fields))
        manual=b.moderation_case_create(765,'WARN',9,'Motivo propio.',author_id=7,history_ref='')
        self.assertNotEqual(b.moderation_case_origin(b.moderation_case_get(765,manual)),'Modo Custodio')

    async def test_reaching_central_warning_limit_never_executes_an_automatic_secondary_measure(self):
        b.guild_config_set(765,'moderation_warn_limit','1')
        b.guild_config_set(765,'moderation_warn_limit_action','ban')
        result=await self.execute('warn')
        self.assertTrue(result['review_limit_reached'])
        self.escalate.assert_not_awaited();self.ban.assert_not_awaited();self.kick.assert_not_awaited()

    async def test_reviewer_revoked_during_io_cannot_execute_the_confirmed_measure(self):
        async def fetch(*args):
            self.reviewer.guild_permissions.administrator=False
            return self.snapshot
        with patch('custodio_source.load_server_rules',new=fetch):
            with self.assertRaises(DisciplineBlocked):await self.execute('ban')
        self.ban.assert_not_awaited()

    async def test_warn_uses_shared_limit_history_reference_and_month_without_repetition(self):
        with patch.object(b,'moderation_case_message_history',side_effect=AssertionError('must not duplicate message text')):
            first=await self.execute('warn')
            second=await self.execute('warn',mid=1003)
        self.assertEqual(b.moderation_warning_counts(765,9),(2,2))
        one=b.moderation_case_get(765,first['case_number']);two=b.moderation_case_get(765,second['case_number'])
        self.assertEqual(one['expires_at'],two['expires_at'])
        self.assertTrue(one['message_history'].startswith('https://discord.com/channels/'))
        self.assertTrue(one['moderator_notes'].startswith('custodio:'))
        self.escalate.assert_not_awaited()
        self.kick.assert_not_awaited();self.ban.assert_not_awaited()

    async def test_kick_and_both_bans_record_one_case_with_exact_duration(self):
        for action,mid in [('kick',1010),('temp_ban',1020),('ban',1030)]:
            result=await self.execute(action,mid=mid)
            row=b.moderation_case_get(765,result['case_number'])
            self.assertEqual(row['type'],'KICK' if action=='kick' else 'BAN')
            self.assertEqual(row['duration_minutes'],15 if action=='temp_ban' else None)
            self.assertEqual(row['expires_at'] is not None,action=='temp_ban')
        self.kick.assert_awaited_once()
        self.assertEqual(self.ban.await_count,2)
        self.assertEqual([call.kwargs['duration_minutes'] for call in self.ban.await_args_list],[15,0])
        self.assertTrue(all(call.kwargs['delete_message_seconds']==0 for call in self.ban.await_args_list))

    async def test_same_review_cannot_execute_twice_after_restarting_adapter(self):
        result=await self.execute('warn')
        restarted=CustodioDiscipline(self.engine.n)
        again=await restarted.execute(self.guild,self.incident(),self.snapshot,action='warn',verified=True,
                                      administrator_confirmed=True,moderator_id=7)
        self.assertEqual(again,result)
        self.assertEqual(b.moderation_warning_counts(765,9),(1,1))

    async def test_completed_measure_closes_only_warnings_for_the_same_custodio_conduct(self):
        manual,_,_=b.moderation_warning_create(765,9,'Manual warning outside Custodio')
        own=await self.execute('warn')
        await self.execute('kick',mid=1100)
        self.assertTrue(b.moderation_case_get(765,manual)['open'])
        self.assertFalse(b.moderation_case_get(765,own['case_number'])['open'])
        self.assertEqual(b.moderation_warning_counts(765,9),(1,2))

    async def test_automatic_owner_staff_and_unverified_requests_cannot_sanction(self):
        for changes in [dict(automatic=True),dict(verified=False),dict(administrator_confirmed=False),dict(moderator_id=None)]:
            with self.subTest(changes=changes),self.assertRaises(DisciplineBlocked):
                await self.execute('ban',**changes)
        self.member.guild_permissions.manage_messages=True
        with self.assertRaises(DisciplineBlocked):await self.execute('kick')
        self.kick.assert_not_awaited();self.ban.assert_not_awaited()

    async def test_uncertain_discord_action_stays_pending_and_is_never_retried(self):
        self.ban.side_effect=TimeoutError('uncertain response')
        with self.assertRaises(TimeoutError):await self.execute('temp_ban')
        self.ban.side_effect=None
        with self.assertRaises(DisciplineBlocked):await self.execute('temp_ban')
        self.ban.assert_awaited_once()

    async def test_incomplete_evidence_and_changed_rules_are_blocked(self):
        incident=self.incident()
        ledger(self.path,'custodio-report:765:1001','pending',[])
        with self.assertRaises(DisciplineBlocked):
            await self.engine.execute(self.guild,incident,self.snapshot,action='warn',verified=True,
                                       administrator_confirmed=True,moderator_id=7)
        self.escalate.assert_not_awaited()

    async def test_temp_ban_is_unbanned_by_real_expirer_only_after_discord_confirms(self):
        result=await self.execute('temp_ban')
        row=b.moderation_case_get(765,result['case_number'])
        with b.db_connect() as db:
            db.execute("UPDATE moderation_cases SET expires_at=? WHERE guild_id=765 AND case_number=?",
                       ('2020-01-01T00:00:00+00:00',result['case_number']))
        self.guild.fetch_ban=AsyncMock(return_value=NS(reason=row['reason']))
        self.guild.unban=AsyncMock()
        with patch.object(b.bot,'get_guild',return_value=self.guild),patch.object(b,'heraldo_is_test',return_value=False):
            await b.moderation_case_expiry_loop.coro()
        self.guild.unban.assert_awaited_once()
        self.assertFalse(b.moderation_case_get(765,result['case_number'])['open'])

    async def test_newer_unrelated_ban_is_preserved_even_outside_test_mode(self):
        result=await self.execute('temp_ban')
        with b.db_connect() as db:
            db.execute("UPDATE moderation_cases SET expires_at=? WHERE guild_id=765 AND case_number=?",
                       ('2020-01-01T00:00:00+00:00',result['case_number']))
        self.guild.fetch_ban=AsyncMock(return_value=NS(reason='A later administrative ban'))
        self.guild.unban=AsyncMock()
        with patch.object(b.bot,'get_guild',return_value=self.guild),patch.object(b,'heraldo_is_test',return_value=False):
            await b.moderation_case_expiry_loop.coro()
        self.guild.unban.assert_not_awaited()

    async def test_failed_unban_keeps_case_open_to_retry(self):
        result=await self.execute('temp_ban')
        row=b.moderation_case_get(765,result['case_number'])
        with b.db_connect() as db:
            db.execute("UPDATE moderation_cases SET expires_at=? WHERE guild_id=765 AND case_number=?",
                       ('2020-01-01T00:00:00+00:00',result['case_number']))
        self.guild.fetch_ban=AsyncMock(return_value=NS(reason=row['reason']))
        error=discord.Forbidden(NS(status=403,reason='Forbidden'),{'code':50013,'message':'Missing Permissions'})
        self.guild.unban=AsyncMock(side_effect=error)
        with patch.object(b.bot,'get_guild',return_value=self.guild),patch.object(b,'heraldo_is_test',return_value=False),\
             patch.object(b.traceback,'print_exc'):
            await b.moderation_case_expiry_loop.coro()
        self.assertTrue(b.moderation_case_get(765,result['case_number'])['open'])

    async def test_pending_ban_is_not_closed_before_a_delayed_discord_confirmation(self):
        self.ban.side_effect=TimeoutError('uncertain response')
        with self.assertRaises(TimeoutError):await self.execute('temp_ban')
        with b.db_connect() as db:
            row=db.execute("SELECT case_number FROM moderation_cases WHERE guild_id=765 AND type='BAN'").fetchone()
            number=row[0]
            db.execute("UPDATE moderation_cases SET expires_at=? WHERE guild_id=765 AND case_number=?",
                       ('2020-01-01T00:00:00+00:00',number))
        with patch.object(b.bot,'get_guild',return_value=self.guild):
            await b.moderation_case_expiry_loop.coro()
        self.assertTrue(b.moderation_case_get(765,number)['open'])


if __name__=='__main__':unittest.main()
