"""Conservación por mensaje, fallos y reanudación; Discord simulado."""
from i18n_source_helpers import source_text as _source_text
import asyncio
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import AsyncMock, MagicMock, patch
import evidence_archive as archive
from test_safety_regressions import b


class PurgeEvidenceTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.db = str(Path(self.tmp.name) / 'test.db')
        everyone = NS(is_default=lambda: True)
        self.guild = NS(id=1, me=NS(id=99), default_role=everyone, roles=[everyone], filesize_limit=8000000)
        self.channel = MagicMock(spec=b.discord.TextChannel)
        self.channel.id, self.channel.guild, self.channel.overwrites = 2, self.guild, {}
        self.channel.topic = archive.ARCHIVE_CHANNEL_TOPIC
        self.channel.is_nsfw.return_value = True
        self.channel.permissions_for.side_effect = lambda obj: b.discord.Permissions(
            view_channel=obj is self.guild.me, send_messages=True, attach_files=True, read_message_history=True)
        self.guild.get_channel = lambda _: self.channel
        self.copies = {}
        async def send(**kwargs):
            data = kwargs['file'].fp.read()
            mid = 100 + len(self.copies)
            self.copies[mid] = NS(author=self.guild.me, attachments=[
                NS(size=len(data), read=AsyncMock(return_value=data))])
            return NS(id=mid)
        self.channel.send = AsyncMock(side_effect=send)
        self.channel.fetch_message = AsyncMock(side_effect=lambda mid: self.copies[mid])
        self.source = NS(id=3, guild=self.guild, fetch_message=AsyncMock())
        self.message = NS(id=4, guild=self.guild, channel=self.source, author=NS(id=5),
            content='Texto íntegro' * 400, created_at=b.datetime.now(b.timezone.utc), edited_at=None,
            type=NS(value=0), flags=NS(value=0), embeds=[], components=[], attachments=[],
            stickers=[], poll=None, message_snapshots=[], delete=AsyncMock())
        self.source.fetch_message.return_value = self.message

    def attachment(self, data=b'abc', declared_size=None):
        return NS(id=6, filename='original.txt', size=len(data) if declared_size is None else declared_size,
                  content_type='text/plain', description=None, read=AsyncMock(return_value=data))

    async def preserve(self):
        return await archive.preserve(self.message, self.channel, self.db)

    async def delete(self):
        with patch.object(b, 'DB_PATH', self.db), patch.object(b, 'get_log_channel_id', return_value=2), \
                patch.object(archive, 'ensure_private_archive', new=AsyncMock(return_value=self.channel)), \
                patch.object(b.bot, '_connection', wraps=b.bot._connection):
            # Gateway no se inicia; el intent se habilita solo para esta prueba.
            with patch.object(type(b.bot), 'intents', new_callable=lambda: property(lambda _: NS(message_content=True))):
                return await b.delete_with_evidence(self.source, self.message.id)

    async def test_full_text_and_attachment_verified_before_delete(self):
        self.message.attachments = [self.attachment()]
        self.assertTrue(await self.delete())
        self.assertEqual(self.channel.send.await_count, 2)
        self.message.delete.assert_awaited_once()
        self.assertTrue(all(c.attachments[0].read.await_count for c in self.copies.values()))
        manifest = await self.copies[101].attachments[0].read()
        self.assertIn(self.message.content.encode(), manifest)

    async def test_previous_log_receipt_does_not_block_new_archive(self):
        import hashlib
        metadata = archive.snapshot(self.message)
        old_key = (
            f'{self.guild.id}:{self.source.id}:{self.message.id}:'
            f'{hashlib.sha256(archive.encoded(metadata)).hexdigest()}'
        )
        archive.ledger(self.db, old_key, 'claim')
        self.assertIsNotNone(await self.preserve())
        self.channel.send.assert_awaited_once()

    async def test_restart_reuses_complete_copy_but_reverifies_bytes(self):
        reference = await self.preserve()
        self.assertEqual(await self.preserve(), reference)
        self.channel.send.assert_awaited_once()
        self.copies[100].attachments[0].read.return_value = b'corrupt'
        self.assertIsNone(await self.preserve())
        self.assertFalse(await self.delete())
        self.message.delete.assert_not_awaited()

    async def test_partial_upload_remains_pending_after_restart(self):
        self.message.attachments = [self.attachment()]
        real_send = self.channel.send.side_effect
        async def fail_manifest(**kwargs):
            if self.copies:
                raise OSError('simulated failure')
            return await real_send(**kwargs)
        self.channel.send.side_effect = fail_manifest
        self.assertFalse(await self.delete())
        self.channel.send.side_effect = real_send
        self.assertIsNone(await self.preserve())
        self.assertEqual(len(self.copies), 1)
        self.message.delete.assert_not_awaited()

    async def test_large_attachment_blocks_without_download_or_delete(self):
        self.message.attachments = [self.attachment(declared_size=9000000)]
        self.assertFalse(await self.delete())
        self.message.attachments[0].read.assert_not_awaited()
        self.channel.send.assert_not_awaited()
        self.message.delete.assert_not_awaited()

    async def test_short_download_blocks_delete(self):
        self.message.attachments = [self.attachment(declared_size=9)]
        self.assertFalse(await self.delete())
        self.message.delete.assert_not_awaited()

    async def test_revoked_privacy_blocks_reuse(self):
        await self.preserve()
        self.channel.permissions_for.side_effect = lambda _: b.discord.Permissions.all()
        self.assertFalse(await self.delete())
        self.message.delete.assert_not_awaited()

    async def test_visible_ordinary_role_blocks_archive(self):
        ordinary = NS(is_default=lambda: False, permissions=b.discord.Permissions.none(), tags=None)
        self.guild.roles.append(ordinary)
        self.channel.permissions_for.side_effect = lambda obj: b.discord.Permissions(view_channel=obj is ordinary)
        self.assertIsNone(await self.preserve())
        self.channel.send.assert_not_awaited()

    async def test_member_override_blocks_archive(self):
        outsider = MagicMock(spec=b.discord.Member)
        outsider.id = 888
        outsider.guild_permissions = b.discord.Permissions.none()
        self.channel.overwrites = {outsider: b.discord.PermissionOverwrite(view_channel=True)}
        self.assertIsNone(await self.preserve())
        self.channel.send.assert_not_awaited()

    async def test_unsupported_resources_are_not_deleted(self):
        self.message.stickers = [NS(id=123)]
        self.assertFalse(await self.delete())
        self.message.delete.assert_not_awaited()

    async def test_concurrent_calls_send_one_copy(self):
        results = await asyncio.gather(self.preserve(), self.preserve())
        self.assertTrue(any(results))
        self.assertEqual(len({x for x in results if x is not None}), 1)
        self.channel.send.assert_awaited_once()

    async def test_one_failed_archive_does_not_delete_other_unarchived_ids(self):
        with patch.object(b, 'delete_with_evidence', new=AsyncMock(side_effect=[True, False, True])) as delete:
            self.assertEqual(await b._delete_ids(self.source, [10, 11, 12, 12]), (2, 1))
        self.assertEqual([c.args[1] for c in delete.await_args_list], [10, 11, 12])

    async def test_edit_during_archive_blocks_delete(self):
        edited = NS(**vars(self.message))
        edited.content = 'Cambio posterior'
        self.source.fetch_message.side_effect = [self.message, edited]
        self.assertFalse(await self.delete())
        self.message.delete.assert_not_awaited()

    async def test_in_place_edit_during_archive_blocks_delete(self):
        send = self.channel.send.side_effect
        async def mutate_source(**kwargs):
            copy = await send(**kwargs)
            self.message.content = 'Editado mientras se copiaba el objeto original'
            return copy
        self.channel.send.side_effect = mutate_source
        self.assertFalse(await self.delete())
        self.message.delete.assert_not_awaited()

    async def test_gateway_without_content_intent_never_copies_or_deletes(self):
        with patch.object(type(b.bot), 'intents', new_callable=lambda: property(lambda _: NS(message_content=False))):
            self.assertFalse(await b.delete_with_evidence(self.source, self.message.id))
        self.source.fetch_message.assert_not_awaited()
        self.message.delete.assert_not_awaited()

    async def test_missing_copy_after_restart_blocks_deletion(self):
        await self.preserve()
        self.channel.fetch_message.side_effect = b.discord.NotFound(NS(status=404, reason='Missing'), 'Missing')
        self.assertFalse(await self.delete())
        self.message.delete.assert_not_awaited()

    def test_no_ban_can_delete_without_archive(self):
        import ast
        tree = ast.parse(_source_text(Path(b.__file__), encoding='utf-8'))
        wrapper = next(n for n in tree.body if isinstance(n, ast.AsyncFunctionDef)
                       and n.name == "heraldo_ban")
        calls = [n for n in ast.walk(wrapper) if isinstance(n, ast.Call)
                 and isinstance(n.func, ast.Call)
                 and isinstance(n.func.func, ast.Name)
                 and n.func.func.id == "getattr"
                 and len(n.func.args) == 2
                 and isinstance(n.func.args[1], ast.Constant)
                 and n.func.args[1].value == "ban"]
        self.assertEqual(len(calls), 1)
        options = {kw.arg: kw.value for kw in calls[0].keywords}
        self.assertIsInstance(options["delete_message_seconds"], ast.Constant)
        self.assertEqual(options["delete_message_seconds"].value, 0)
