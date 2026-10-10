import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from types import SimpleNamespace as NS
from unittest.mock import AsyncMock, MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import discord
from message_automation import ScheduledMessages, parse_local, next_occurrence


class SchedulingTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.connect = lambda: sqlite3.connect(str(Path(self.temp.name) / 'schedule.db'), isolation_level=None)
        self.job = dict(id='job1', channel=5, template='Aviso', author=7,
                        start='2026-01-01T12:00:00+00:00', zone='UTC', repeat='ninguna')
        self.channel = MagicMock(spec=discord.TextChannel)
        self.channel.permissions_for.return_value = discord.Permissions(view_channel=True, send_messages=True, embed_links=True)
        self.channel.send = AsyncMock(return_value=NS(id=88))
        self.member = NS(guild_permissions=discord.Permissions(manage_guild=True))
        self.guild = NS(id=1, me=NS(id=2), get_channel=lambda _: self.channel,
                        fetch_member=AsyncMock(return_value=self.member))
        self.engine = ScheduledMessages(dict(db_connect=self.connect,
            guild_config_get=lambda *_: json.dumps([self.job]),
            heraldo_template_list=lambda _: [{'name': 'Aviso'}],
            heraldo_template_payload=lambda *_: {'content': 'Aviso'}))
        self.engine.initialize()

    def test_local_time_and_invalid_dst(self):
        self.assertEqual(parse_local('2026-01-01 08:00', 'America/Santo_Domingo').hour, 12)
        for value in ('2026-03-08 02:30', '2026-11-01 01:30'):
            with self.assertRaises(ValueError):
                parse_local(value, 'America/New_York')

    def test_daily_recurrence_preserves_local_hour_across_dst(self):
        job = dict(self.job, start='2026-03-07T17:00:00+00:00', zone='America/New_York', repeat='diaria')
        self.assertEqual(next_occurrence(job, datetime(2026, 3, 7, 18, tzinfo=timezone.utc)),
                         '2026-03-08T16:00:00+00:00')

    async def test_one_off_is_not_repeated(self):
        now = datetime.now(timezone.utc)
        await self.engine.execute(self.guild, self.job, now)
        await self.engine.execute(self.guild, self.job, now)
        self.channel.send.assert_awaited_once()
        self.assertEqual(self.engine.state(1, self.job)[1], 'done')

    async def test_permission_revocation_blocks_send(self):
        self.member.guild_permissions = discord.Permissions.none()
        await self.engine.execute(self.guild, self.job, datetime.now(timezone.utc))
        self.channel.send.assert_not_awaited()
        self.assertEqual(self.engine.state(1, self.job)[1], 'error')

    async def test_timeout_does_not_blindly_repeat(self):
        self.channel.send.side_effect = TimeoutError()
        await self.engine.execute(self.guild, self.job, datetime.now(timezone.utc))
        await self.engine.execute(self.guild, self.job, datetime.now(timezone.utc))
        self.channel.send.assert_awaited_once()
        self.assertEqual(self.engine.state(1, self.job)[1], 'uncertain')

    async def test_restart_preserves_pending_but_flags_inflight(self):
        self.engine.state(1, self.job)
        self.engine.initialize()
        self.assertEqual(self.engine.state(1, self.job)[1], 'pending')
        self.engine.finish(1, self.job, 'sending', next_run=self.job['start'])
        self.engine.initialize()
        await self.engine.execute(self.guild, self.job, datetime.now(timezone.utc))
        self.channel.send.assert_not_awaited()
        self.assertEqual(self.engine.state(1, self.job)[1], 'uncertain')

    async def test_claim_is_scoped_to_guild(self):
        await self.engine.execute(self.guild, self.job, datetime.now(timezone.utc))
        self.guild.id = 3
        await self.engine.execute(self.guild, self.job, datetime.now(timezone.utc))
        self.assertEqual(self.channel.send.await_count, 2)
