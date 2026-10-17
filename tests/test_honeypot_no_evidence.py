"""Regresiones: solo Honeypot elimina sin conservar evidencias; otras causas no cambian."""
import unittest
from datetime import timedelta
from types import SimpleNamespace as NS
from unittest.mock import AsyncMock, MagicMock, patch

from test_safety_regressions import b


class HoneypotWithoutEvidenceTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        b._evidence_delete_inflight.clear()
        self.now = b.datetime.now(b.timezone.utc)
        self.guild = NS(id=901, me=NS(id=7))
        self.channel = MagicMock(spec=b.discord.TextChannel)
        self.channel.id, self.channel.guild = 200, self.guild
        self.channel.permissions_for.return_value = NS(
            view_channel=True, read_message_history=True, manage_messages=True,
        )
        self.message = NS(
            id=300, guild=self.guild, channel=self.channel, author=NS(id=20),
            created_at=self.now - timedelta(hours=1), delete=AsyncMock(),
        )
        self.channel.fetch_message = AsyncMock(return_value=self.message)

    def tearDown(self):
        b._evidence_delete_inflight.clear()

    async def test_only_trigger_author_is_deleted_and_nothing_is_archived(self):
        with (
            patch.object(b, "delete_with_evidence", new=AsyncMock()) as archive_delete,
            patch.object(b.evidence_archive, "preserve", new=AsyncMock()) as preserve,
        ):
            self.assertTrue(await b.delete_honeypot_message(self.channel, 300, 20))
        self.message.delete.assert_awaited_once()
        archive_delete.assert_not_awaited()
        preserve.assert_not_awaited()

    async def test_wrong_author_or_guild_never_deleted(self):
        self.assertFalse(await b.delete_honeypot_message(self.channel, 300, 21))
        self.message.delete.assert_not_awaited()
        other = NS(**vars(self.message))
        other.guild = NS(id=902)
        self.channel.fetch_message.return_value = other
        self.assertFalse(await b.delete_honeypot_message(self.channel, 300, 20))
        self.message.delete.assert_not_awaited()

    async def test_cutoff_and_revoked_permissions_block_removal(self):
        after = self.now - timedelta(minutes=30)
        self.assertFalse(await b.delete_honeypot_message(self.channel, 300, 20, after=after))
        self.message.delete.assert_not_awaited()
        self.channel.permissions_for.return_value.manage_messages = False
        self.assertFalse(await b.delete_honeypot_message(self.channel, 300, 20))
        self.message.delete.assert_not_awaited()

    async def test_concurrent_honeypot_deletion_does_not_duplicate(self):
        started = b.asyncio.Event()
        release = b.asyncio.Event()
        async def slow_delete():
            started.set()
            await release.wait()
        self.message.delete.side_effect = slow_delete
        first = b.asyncio.create_task(b.delete_honeypot_message(self.channel, 300, 20))
        await started.wait()
        self.assertFalse(await b.delete_honeypot_message(self.channel, 300, 20))
        release.set()
        self.assertTrue(await first)
        self.message.delete.assert_awaited_once()

    async def test_shared_normal_purge_still_uses_verified_archive(self):
        with (
            patch.object(b, "delete_with_evidence", new=AsyncMock(return_value=True)) as with_archive,
            patch.object(b, "delete_honeypot_message", new=AsyncMock()) as hp_only,
        ):
            self.assertEqual(await b._delete_ids(self.channel, [11, 11, 12]), (2, 0))
        self.assertEqual(with_archive.await_count, 2)
        hp_only.assert_not_awaited()

    async def test_honeypot_purge_never_deletes_another_users_message(self):
        second = MagicMock(spec=b.discord.TextChannel)
        second.id, second.guild = 201, self.guild
        second.permissions_for.return_value = NS(
            view_channel=True, read_message_history=True, manage_messages=True,
        )
        other_user = NS(
            id=401, guild=self.guild, channel=second, author=NS(id=44),
            created_at=self.now - timedelta(hours=1), delete=AsyncMock(),
        )
        second.fetch_message = AsyncMock(return_value=other_user)
        with (
            patch.object(b, "purge_targets", new=AsyncMock(return_value=[self.channel, second])),
            patch.object(b, "_collect_user_messages", new=AsyncMock(side_effect=[[300], [401]])),
            patch.object(b.evidence_archive, "preserve", new=AsyncMock()) as preserve,
            patch.object(b, "delete_with_evidence", new=AsyncMock()) as standard_delete,
        ):
            result = await b.purge_user_messages(
                self.guild, 20, after=self.now - timedelta(hours=24),
                purge_origin="honeypot",
            )
        self.assertEqual(result.deleted, 1)
        self.assertEqual(result.failed, 1)
        self.assertEqual(result.channels_scanned, 2)
        self.message.delete.assert_awaited_once()
        other_user.delete.assert_not_awaited()
        preserve.assert_not_awaited()
        standard_delete.assert_not_awaited()

    async def test_kick_and_timeout_propagate_honeypot_origin(self):
        member = NS(id=20, guild=self.guild, mention="<@20>")
        with (
            patch.object(b, "hp_kick_purge_minutes", return_value=1440),
            patch.object(b, "hp_purge_spec", return_value=("time", 1440)),
            patch.object(b, "run_purge_job", new=AsyncMock()) as run,
        ):
            b.hp_start_kick_purge(member)
            b.hp_start_purge(member)
            await b.asyncio.sleep(0)
        self.assertEqual(run.await_count, 2)
        for called in run.await_args_list:
            self.assertEqual(called.kwargs["purge_origin"], "honeypot")
            self.assertIs(called.args[1], member)

    async def test_honeypot_trigger_history_stores_no_content(self):
        member = NS(
            id=20, guild=self.guild, created_at=self.now,
            joined_at=self.now - timedelta(days=5),
        )
        db = MagicMock()
        with (
            patch.object(b, "db_connect", return_value=db),
            patch.object(b, "hp_prune_history") as prune,
        ):
            b.hp_log_trigger(member, 200, "kick", True, "Aplicada")
        args = db.execute.call_args.args[1]
        self.assertEqual(args[4], "")
        self.assertEqual(args[5], "kick")
        prune.assert_called_once_with(901)


if __name__ == "__main__":
    unittest.main()
