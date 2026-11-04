"""Regresiones de /purge manual: eliminación sin archivo duplicado."""
import asyncio
import inspect
import unittest
from datetime import timedelta
from types import SimpleNamespace as NS
from unittest.mock import AsyncMock, MagicMock, patch

from test_safety_regressions import b


class PurgeDirectDeletionTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        b._evidence_delete_inflight.clear()
        self.now = b.datetime.now(b.timezone.utc)
        self.guild = NS(id=901, me=NS(id=9))
        self.channel = MagicMock(spec=b.discord.TextChannel)
        self.channel.id, self.channel.guild = 110, self.guild
        self.channel.permissions_for.return_value = NS(
            view_channel=True, read_message_history=True, manage_messages=True,
        )
        self.message = NS(
            id=123, guild=self.guild, channel=self.channel,
            author=NS(id=50), created_at=self.now,
            content="mensaje de prueba", attachments=[], delete=AsyncMock(),
        )
        self.channel.fetch_message = AsyncMock(return_value=self.message)

    def tearDown(self):
        b._evidence_delete_inflight.clear()

    async def test_manual_purge_does_not_create_or_upload_evidence(self):
        with (
            patch.object(b.evidence_archive, "ensure_private_archive", new=AsyncMock()) as create,
            patch.object(b.evidence_archive, "preserve", new=AsyncMock()) as preserve,
        ):
            self.assertTrue(await b.delete_purge_panel_message(
                self.channel, 123, expected_author_id=50,
                after=self.now - timedelta(minutes=5),
                before=self.now + timedelta(minutes=5),
                content_type="all",
            ))
        self.message.delete.assert_awaited_once()
        create.assert_not_awaited()
        preserve.assert_not_awaited()

    async def test_wrong_author_or_time_never_deleted(self):
        self.assertFalse(await b.delete_purge_panel_message(
            self.channel, 123, expected_author_id=51))
        self.assertFalse(await b.delete_purge_panel_message(
            self.channel, 123, expected_author_id=50,
            after=self.now + timedelta(seconds=1)))
        self.assertFalse(await b.delete_purge_panel_message(
            self.channel, 123, expected_author_id=50,
            before=self.now - timedelta(seconds=1)))
        self.message.delete.assert_not_awaited()

    async def test_changed_message_type_no_longer_matches(self):
        self.assertFalse(await b.delete_purge_panel_message(
            self.channel, 123, expected_author_id=50, content_type="links"))
        self.message.delete.assert_not_awaited()
        self.message.content = "https://example.com"
        self.assertTrue(await b.delete_purge_panel_message(
            self.channel, 123, expected_author_id=50, content_type="links"))
        self.message.delete.assert_awaited_once()

    async def test_missing_bot_permissions_prevents_deletion(self):
        self.channel.permissions_for.return_value.manage_messages = False
        self.assertFalse(await b.delete_purge_panel_message(
            self.channel, 123, expected_author_id=50))
        self.channel.fetch_message.assert_not_awaited()
        self.message.delete.assert_not_awaited()

    async def test_guild_mismatch_prevents_deletion(self):
        self.message.guild = NS(id=902)
        self.assertFalse(await b.delete_purge_panel_message(
            self.channel, 123, expected_author_id=50))
        self.message.delete.assert_not_awaited()

    async def test_concurrent_confirmation_cannot_delete_twice(self):
        entered, release = asyncio.Event(), asyncio.Event()

        async def delete():
            entered.set()
            await release.wait()

        self.message.delete.side_effect = delete
        first = asyncio.create_task(b.delete_purge_panel_message(
            self.channel, 123, expected_author_id=50))
        await entered.wait()
        self.assertFalse(await b.delete_purge_panel_message(
            self.channel, 123, expected_author_id=50))
        release.set()
        self.assertTrue(await first)
        self.message.delete.assert_awaited_once()

    def test_only_panel_uses_direct_route_existing_moderation_keeps_archive(self):
        import ast
        from pathlib import Path
        tree = ast.parse(Path(b.__file__).read_text(encoding="utf-8"))
        fn = next(node for node in tree.body
                  if isinstance(node, ast.AsyncFunctionDef) and node.name == "purge_command")
        calls = [call for call in ast.walk(fn) if isinstance(call, ast.Call)
                 and isinstance(call.func, ast.Name) and call.func.id == "PurgePanel"]
        self.assertEqual(len(calls), 1)
        deletion = next(k.value for k in calls[0].keywords if k.arg == "delete")
        self.assertIsInstance(deletion, ast.Name)
        self.assertEqual(deletion.id, "delete_purge_panel_message")
        self.assertIn("ensure_private_archive", inspect.getsource(
            inspect.unwrap(b.delete_with_evidence)))


if __name__ == "__main__":
    unittest.main()
