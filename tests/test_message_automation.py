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
from message_automation import ScheduledMessages, parse_local, next_occurrence, keyword_matches, AUTORESPONSE_KEY, STICKY_KEY, WebhookTemplateConfirmView


class SchedulingFixture:
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


class SchedulingTests(SchedulingFixture, unittest.IsolatedAsyncioTestCase):
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


class AutoresponseTests(SchedulingFixture, unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        super().setUp()
        self.job.update(repeat='trigger', cooldown=60, keyword='ayuda', match='incluida')
        self.jobs = [self.job]
        self.engine.host['guild_config_get'] = lambda gid, key: json.dumps(self.jobs) if gid == 1 and key == AUTORESPONSE_KEY else '[]'
        self.engine.host['condemnation_get'] = lambda *_: None
        self.author = NS(id=9, bot=False)
        self.message = NS(guild=self.guild, channel=NS(id=5), author=self.author, webhook_id=None, content='Necesito AYUDA, por favor')

    def test_keyword_has_boundaries_and_is_not_regular_expression(self):
        self.assertTrue(keyword_matches('AYUDA, por favor', 'ayuda', 'incluida'))
        self.assertFalse(keyword_matches('ayudante', 'ayuda', 'incluida'))
        self.assertFalse(keyword_matches('ayuda, por favor', 'ayuda', 'exacta'))
        self.assertFalse(keyword_matches('cualquier texto', '.*', 'incluida'))

    async def test_response_context_and_persistent_cooldown(self):
        render = MagicMock(return_value={'content': 'Respuesta'})
        self.engine.host['heraldo_template_payload'] = render
        await self.engine.on_message(self.message)
        self.engine.initialize()
        await self.engine.on_message(self.message)
        self.channel.send.assert_awaited_once()
        self.assertIs(render.call_args.args[2], self.author)

    async def test_channel_limit_covers_different_rules(self):
        await self.engine.on_message(self.message)
        self.jobs.append(dict(self.job, id='job2', keyword='normas'))
        self.message.content = 'normas'
        await self.engine.on_message(self.message)
        self.channel.send.assert_awaited_once()

    async def test_bots_webhooks_and_condemnations_do_not_trigger(self):
        self.author.bot = True
        await self.engine.on_message(self.message)
        self.author.bot = False
        self.message.webhook_id = 20
        await self.engine.on_message(self.message)
        self.message.webhook_id = None
        self.engine.host['condemnation_get'] = lambda *_: {'active': True}
        await self.engine.on_message(self.message)
        self.channel.send.assert_not_awaited()


class StickyTests(SchedulingFixture, unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        super().setUp()
        self.job.update(repeat='sticky', cooldown=60)
        self.engine.host['guild_config_get'] = lambda gid, key: json.dumps([self.job]) if key == STICKY_KEY else '[]'
        self.engine.host['condemnation_get'] = lambda *_: None
        self.channel.permissions_for.return_value.read_message_history = True
        self.message = NS(guild=self.guild, channel=NS(id=5), author=NS(id=9, bot=False), webhook_id=None, content='Mensaje')
        self.old = NS(author=NS(id=2), delete=AsyncMock())
        self.channel.fetch_message = AsyncMock(return_value=self.old)

    async def test_sticky_waits_for_activity_and_deletes_only_previous_bot_message(self):
        await self.engine.execute(self.guild, self.job, datetime.now(timezone.utc), config_key=STICKY_KEY)
        self.assertEqual(self.engine.state(1, self.job)[1], 'waiting')
        await self.engine.execute(self.guild, self.job, datetime.now(timezone.utc), config_key=STICKY_KEY)
        self.channel.send.assert_awaited_once()
        await self.engine.on_message(self.message)
        self.assertEqual(self.engine.state(1, self.job)[1], 'pending')
        await self.engine.execute(self.guild, self.job, datetime(2099, 1, 1, tzinfo=timezone.utc), config_key=STICKY_KEY)
        self.old.delete.assert_awaited_once()
        self.channel.fetch_message.assert_awaited_once_with(88)
        self.assertEqual(self.channel.send.await_count, 2)

    async def test_sticky_never_deletes_someone_elses_message(self):
        self.engine.state(1, self.job)
        self.engine.finish(1, self.job, 'pending', next_run=self.job['start'], message_id=77)
        self.old.author.id = 99
        await self.engine.execute(self.guild, self.job, datetime.now(timezone.utc), config_key=STICKY_KEY)
        self.old.delete.assert_not_awaited()
        self.channel.send.assert_not_awaited()
        self.assertEqual(self.engine.state(1, self.job)[1], 'error')

    async def test_message_during_send_is_not_lost(self):
        async def send(**_):
            await self.engine.on_message(self.message)
            return NS(id=88)
        self.channel.send.side_effect = send
        await self.engine.execute(self.guild, self.job, datetime.now(timezone.utc), config_key=STICKY_KEY)
        self.assertEqual(self.engine.state(1, self.job)[1], 'pending')

    async def test_other_channel_does_not_trigger(self):
        self.message.channel.id = 55
        await self.engine.on_message(self.message)
        self.channel.send.assert_not_awaited()


class WebhookTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.channel = MagicMock(spec=discord.TextChannel)
        self.channel.id = 5
        self.channel.permissions_for.return_value = discord.Permissions(view_channel=True, send_messages=True, manage_webhooks=True)
        self.webhook = NS(user=NS(id=2), name='El Heraldo - Mensajes', channel_id=5,
                          send=AsyncMock(return_value=NS(id=88)))
        self.channel.webhooks = AsyncMock(return_value=[self.webhook])
        self.channel.create_webhook = AsyncMock(return_value=self.webhook)
        guild = NS(id=1, me=NS(id=2), get_channel=lambda _: self.channel)
        self.interaction = NS(guild=guild, user=NS(id=7),
            response=NS(send_message=AsyncMock(), edit_message=AsyncMock(), defer=AsyncMock()),
            edit_original_response=AsyncMock())
        self.item = {'name': 'Aviso', 'content': 'Texto'}
        self.host = dict(configuration_access=AsyncMock(return_value=True),
                         heraldo_template_list=lambda _: [self.item],
                         heraldo_template_payload=lambda *_: {'content': 'Texto', 'view': None})
        self.view = WebhookTemplateConfirmView(self.host, 1, 7, 5, self.item)

    async def test_cancel_never_contacts_webhooks(self):
        await self.view.cancel.callback(self.interaction)
        self.channel.webhooks.assert_not_awaited()
        self.channel.create_webhook.assert_not_awaited()

    async def test_confirm_reuses_only_owned_webhook_once(self):
        await self.view.publish.callback(self.interaction)
        await self.view.publish.callback(self.interaction)
        self.webhook.send.assert_awaited_once_with(content='Texto', wait=True)
        self.channel.create_webhook.assert_not_awaited()

    async def test_foreign_webhook_is_never_used(self):
        foreign = NS(user=NS(id=99), name='El Heraldo - Mensajes', channel_id=5, send=AsyncMock())
        self.channel.webhooks.return_value = [foreign]
        await self.view.publish.callback(self.interaction)
        foreign.send.assert_not_awaited()
        self.channel.create_webhook.assert_awaited_once()
        self.webhook.send.assert_awaited_once()

    async def test_revoked_channel_permission_blocks_creation(self):
        self.channel.permissions_for.return_value.manage_webhooks = False
        await self.view.publish.callback(self.interaction)
        self.channel.webhooks.assert_not_awaited()
        self.channel.create_webhook.assert_not_awaited()

    async def test_changed_template_requires_new_confirmation(self):
        self.item['content'] = 'Cambio concurrente'
        await self.view.publish.callback(self.interaction)
        self.channel.webhooks.assert_not_awaited()
        self.assertIn('cambió', self.interaction.response.send_message.call_args.args[0])
