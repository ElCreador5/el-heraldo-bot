"""Reportes reales del adaptador, transporte aislado y registro durable mínimo."""
import asyncio
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sqlite3
import tempfile
from types import SimpleNamespace as NS
import unittest
from unittest.mock import AsyncMock, Mock, patch
import discord
import custodio_reports as reports


class DeliveryTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.db=str(Path(self.tmp.name)/'references.sqlite')
        p=patch.dict(os.environ,{'DB_PATH':self.db});p.start();self.addCleanup(p.stop)
        reports._published_evidence.clear();reports._publish_locks.clear()
        self.copies={}
        self.guild=NS(id=123,name='Laboratorio',default_role=NS(id=1))
        source_channel=Mock(spec=discord.TextChannel)
        source_channel.id,source_channel.name=25,'prueba'
        source_channel.guild=self.guild
        source_channel.permissions_for.return_value=discord.Permissions(view_channel=True)
        source_channel.is_nsfw.return_value=False
        self.source=NS(guild=self.guild,channel=source_channel,author=NS(id=77,bot=False),webhook_id=None,
                       id=88,content='TEXTO ÚNICO: «ñ» \\n literal\n@everyone [enlace](https://example.com)',
                       created_at=datetime.now(timezone.utc),jump_url='https://discord.com/channels/123/25/88')
        source_channel.fetch_message=AsyncMock(return_value=self.source)
        self.destination=NS(id=26,guild=self.guild,is_nsfw=lambda:False,send=AsyncMock(side_effect=self.send),
                            fetch_message=AsyncMock(side_effect=lambda mid:self.copies[mid]))
        p=patch.object(reports,'_get_safe_existing',return_value=self.destination);p.start();self.addCleanup(p.stop)

    async def send(self, **kwargs):
        mid=501+len(self.copies)
        copy=NS(id=mid,embeds=kwargs['embeds'],author=NS(id=9),edit=AsyncMock())
        self.copies[mid]=copy
        return copy

    async def publish(self):
        return await reports.publish_literal_observation(guild=self.guild,report_channel_id=26,
                source_message=self.source,rule_text='No enviar spam.',rule_number=1,
                rules_revision='a'*64,footer="El Heraldo's Labs 🧪")

    async def test_concurrent_delivery_and_restart_keep_one_report_without_sqlite_text(self):
        first,second=await asyncio.gather(self.publish(),self.publish())
        self.assertEqual(first.id,second.id)
        self.destination.send.assert_awaited_once()
        reports._published_evidence.clear()
        restored=await self.publish()
        self.assertEqual(restored.id,first.id)
        self.destination.send.assert_awaited_once()
        with sqlite3.connect(self.db) as db:
            stored=str(db.execute('SELECT * FROM evidence_archive_v1').fetchall())
        self.assertNotIn('TEXTO ÚNICO',stored)
        self.assertNotIn('No enviar spam',stored)
        self.assertTrue(self.destination.send.call_args.kwargs['allowed_mentions'].everyone is False)

    async def test_delete_after_restart_removes_link_and_preserves_exact_copy(self):
        copy=await self.publish()
        reports._published_evidence.clear()
        self.assertTrue(await reports.unlink_deleted_original(guild=self.guild,deleted_message_id=88,report_channel_id=26))
        embeds=copy.edit.call_args.kwargs['embeds']
        self.assertIn(self.source.content,[f.value for e in embeds for f in e.fields])
        self.assertFalse(any(f.name in reports._i18n_variants('text.a376d1351c3f23') for e in embeds for f in e.fields))
        reports._published_evidence.clear()
        await self.publish()
        self.destination.send.assert_awaited_once()

    async def test_timeout_before_confirmation_is_never_resent(self):
        self.destination.send.side_effect=TimeoutError('uncertain delivery')
        with self.assertRaises(TimeoutError):await self.publish()
        reports._published_evidence.clear()
        with self.assertRaises(reports.ReportChannelError):await self.publish()
        self.destination.send.assert_awaited_once()

    async def test_partial_multi_message_delivery_is_not_presented_as_complete(self):
        self.source.content='Texto largo exacto\n'*700
        sent=0
        async def fail_after_first(**kwargs):
            nonlocal sent
            sent+=1
            if sent==2:raise TimeoutError('uncertain second batch')
            return await self.send(**kwargs)
        self.destination.send.side_effect=fail_after_first
        with self.assertRaises(TimeoutError):await self.publish()
        with self.assertRaises(reports.ReportChannelError):await self.publish()
        self.assertEqual(self.destination.send.await_count,2)
        with sqlite3.connect(self.db) as db:
            state=db.execute('SELECT status FROM evidence_archive_v1').fetchone()[0]
        self.assertEqual(state,'pending')


class PrivacyCompatibilityTests(unittest.TestCase):
    def test_age_restriction_and_private_audience_cannot_be_widened(self):
        everyone,staff,ordinary=NS(id=1),NS(id=2),NS(id=3)
        guild=NS(id=123,default_role=everyone,roles=[everyone,staff,ordinary])
        source=NS(guild=guild,is_nsfw=lambda:True,overwrites={},
                  permissions_for=lambda role:discord.Permissions(view_channel=role.id==2))
        destination=NS(guild=guild,is_nsfw=lambda:False,overwrites={},
                       permissions_for=lambda role:discord.Permissions(view_channel=role.id==2))
        self.assertFalse(reports.compatible_evidence_access(source,destination))
        destination.is_nsfw=lambda:True
        self.assertTrue(reports.compatible_evidence_access(source,destination))
        destination.permissions_for=lambda role:discord.Permissions(view_channel=role.id in {2,3})
        self.assertFalse(reports.compatible_evidence_access(source,destination))
        destination.permissions_for=lambda role:discord.Permissions(view_channel=role.id==2)
        excluded=Mock(spec=discord.Member)
        source.overwrites={excluded:discord.PermissionOverwrite(view_channel=False)}
        self.assertFalse(reports.compatible_evidence_access(source,destination))


if __name__=='__main__':unittest.main()
