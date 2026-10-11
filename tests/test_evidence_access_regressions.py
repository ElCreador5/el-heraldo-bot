"""Regresiones estáticas para los controles de archivado y restauración.

Estas comprobaciones no sustituyen pruebas interactivas en Discord.
"""
from pathlib import Path
import unittest
from types import SimpleNamespace as NS
from unittest.mock import AsyncMock, MagicMock, patch
from test_safety_regressions import b

SOURCE = Path(__file__).resolve().parents[1].joinpath("bot.py").read_text(encoding="utf-8")


class EvidenceAndRoleSafetyTests(unittest.TestCase):
    def test_evidence_archive_rejects_non_admin_role_access(self):
        start = SOURCE.index("async def condemnation_archive_evidence(")
        end = SOURCE.index("\nasync def ", start + 1)
        body = SOURCE[start:end]
        self.assertIn("for role in guild.roles:", body)
        self.assertIn("archive_channel.permissions_for(role).view_channel", body)
        self.assertIn("return None, None", body)

    def test_evidence_archive_rejects_member_overrides(self):
        start = SOURCE.index("async def condemnation_archive_evidence(")
        end = SOURCE.index("\nasync def ", start + 1)
        body = SOURCE[start:end]
        self.assertIn("archive_channel.overwrites.items()", body)
        self.assertIn("overwrite.view_channel is True", body)

    def test_partial_restoration_keeps_role_identifiers_for_private_log(self):
        start = SOURCE.index("async def _release_condemned_member_inner(")
        end = SOURCE.index("\nasync def ", start + 1)
        body = SOURCE[start:end]
        self.assertIn("missing_role_ids.append(rid)", body)
        self.assertIn("Roles sin restaurar (IDs):", body)


class EvidenceRuntimeTests(unittest.IsolatedAsyncioTestCase):
    def fixture(self):
        everyone = NS(is_default=lambda: True, permissions=b.discord.Permissions.none())
        moderator = NS(is_default=lambda: False, permissions=b.discord.Permissions(administrator=True))
        bot_member = NS(id=999)
        channel = MagicMock(spec=b.discord.TextChannel)
        channel.overwrites = {}
        channel.permissions_for.side_effect = lambda obj: b.discord.Permissions(
            view_channel=obj is bot_member, send_messages=True, embed_links=True, attach_files=True)
        channel.send = AsyncMock(return_value=NS(jump_url='https://discord.com/channels/901/2/3'))
        guild = NS(id=901, default_role=everyone, roles=[everyone, moderator], me=bot_member,
                   get_channel=lambda _: channel, filesize_limit=1024)
        member = NS(id=11, mention='<@11>')
        message = NS(id=991, author=member, content='Texto de prueba', attachments=[],
                     created_at=b.datetime.now(b.timezone.utc), channel=NS(mention='#prueba'))
        return guild, member, message, channel

    async def archive(self, guild, member, message):
        with patch.object(b, 'condemnation_fetch_source_message', new=AsyncMock(return_value=message)):
            return await b.condemnation_archive_evidence(guild, member,
                source_message_url='https://discord.com/channels/901/1/991', reason='Prueba', applied_by=None)

    async def test_ordinary_role_access_blocks_copy_before_send(self):
        guild, member, message, channel = self.fixture()
        role = NS(is_default=lambda: False, permissions=b.discord.Permissions.none())
        guild.roles.append(role)
        channel.permissions_for.side_effect = lambda obj: b.discord.Permissions(view_channel=obj is role)
        self.assertEqual(await self.archive(guild, member, message), (None, None))
        channel.send.assert_not_awaited()

    async def test_member_override_blocks_copy_before_send(self):
        guild, member, message, channel = self.fixture()
        outsider = MagicMock(spec=b.discord.Member)
        outsider.id = 1000
        channel.overwrites = {outsider: b.discord.PermissionOverwrite(view_channel=True)}
        self.assertEqual(await self.archive(guild, member, message), (None, None))
        channel.send.assert_not_awaited()

    async def test_incomplete_attachment_copy_never_authorizes_purge(self):
        guild, member, message, channel = self.fixture()
        message.attachments = [NS(size=2048, filename='large.txt', read=AsyncMock())]
        url, text = await self.archive(guild, member, message)
        self.assertIsNone(url)
        self.assertEqual(text, message.content)
        message.attachments[0].read.assert_not_awaited()
        channel.send.assert_awaited_once()

    async def test_complete_private_copy_returns_archive_reference(self):
        guild, member, message, channel = self.fixture()
        url, text = await self.archive(guild, member, message)
        self.assertEqual(url, 'https://discord.com/channels/901/2/3')
        self.assertEqual(text, message.content)
        channel.send.assert_awaited_once()


if __name__ == "__main__":
    unittest.main()
