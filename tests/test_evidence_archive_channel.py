"""Pruebas del archivo de evidencias fuera de los canales de registros."""
import asyncio
import unittest
from types import SimpleNamespace as NS
from unittest.mock import AsyncMock, MagicMock

import discord
import evidence_archive as archive


class EvidenceArchiveIsolationTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        archive._archive_channel_locks.clear()
        self.everyone = MagicMock()
        self.everyone.id = 10
        self.everyone.is_default.return_value = True
        self.me = MagicMock()
        self.me.id = 20
        self.me.guild_permissions.manage_channels = True
        self.guild = NS(id=30, me=self.me, default_role=self.everyone,
                        roles=[self.everyone], text_channels=[])
        self.channel = MagicMock(spec=discord.TextChannel)
        self.channel.id = 40
        self.channel.guild = self.guild
        self.channel.topic = archive.ARCHIVE_CHANNEL_TOPIC
        self.channel.is_nsfw.return_value = True
        self.channel.overwrites = {}
        self.channel.overwrites_for.return_value = discord.PermissionOverwrite(view_channel=False)
        self.channel.permissions_for.side_effect = lambda member: discord.Permissions(
            view_channel=member is self.me,
            send_messages=True, attach_files=True, read_message_history=True,
        )

        async def create(name, **kwargs):
            self.assertEqual(name, archive.ARCHIVE_CHANNEL_NAME)
            self.assertTrue(kwargs['nsfw'])
            self.assertIs(kwargs['overwrites'][self.everyone].view_channel, False)
            self.assertIs(kwargs['overwrites'][self.me].attach_files, True)
            self.guild.text_channels.append(self.channel)
            return self.channel
        self.guild.create_text_channel = AsyncMock(side_effect=create)

    async def test_creates_single_private_archive_and_reuses_after_restart(self):
        first, second = await asyncio.gather(
            archive.ensure_private_archive(self.guild, log_channel_id=999),
            archive.ensure_private_archive(self.guild, log_channel_id=999))
        self.assertIs(first, self.channel)
        self.assertIs(second, self.channel)
        self.guild.create_text_channel.assert_awaited_once()
        archive._archive_channel_locks.clear()
        self.assertIs(await archive.ensure_private_archive(self.guild, log_channel_id=999), self.channel)
        self.guild.create_text_channel.assert_awaited_once()

    async def test_log_channel_cannot_be_used_as_archive(self):
        self.guild.text_channels.append(self.channel)
        self.assertIsNone(await archive.ensure_private_archive(self.guild, log_channel_id=40))
        self.guild.create_text_channel.assert_not_awaited()

    async def test_unsafe_or_ambiguous_archive_fails_closed(self):
        self.guild.text_channels.append(self.channel)
        self.channel.permissions_for.side_effect = lambda member: discord.Permissions(
            view_channel=True, send_messages=True, attach_files=True, read_message_history=True)
        self.assertIsNone(await archive.ensure_private_archive(self.guild, log_channel_id=999))
        self.channel.permissions_for.side_effect = lambda member: discord.Permissions(
            view_channel=member is self.me, send_messages=True,
            attach_files=True, read_message_history=True)
        other = MagicMock(spec=discord.TextChannel)
        other.topic = archive.ARCHIVE_CHANNEL_TOPIC
        self.guild.text_channels.append(other)
        self.assertIsNone(await archive.ensure_private_archive(self.guild, log_channel_id=999))
        self.guild.create_text_channel.assert_not_awaited()

    async def test_without_manage_channels_does_not_fallback_to_logs(self):
        self.me.guild_permissions.manage_channels = False
        self.assertIsNone(await archive.ensure_private_archive(self.guild, log_channel_id=999))
        self.guild.create_text_channel.assert_not_awaited()

    async def test_preserve_rejects_logs_before_writing(self):
        self.channel.topic = "Registros de El Heraldo"
        self.assertIsNone(await archive.preserve(
            NS(guild=self.guild, channel=NS(id=55)), self.channel, "/tmp/unrelated.sqlite"))

    async def test_receipt_requires_same_archive_channel(self):
        self.channel.fetch_message = AsyncMock()
        ok = await archive.verify(self.channel, [
            {'channel_id': 888, 'message_id': 42, 'size': 1, 'sha256': '0' * 64}])
        self.assertFalse(ok)
        self.channel.fetch_message.assert_not_awaited()


if __name__ == "__main__":
    unittest.main()
