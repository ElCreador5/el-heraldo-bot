"""Regresiones SQLite sin Gateway para comentarios de salida."""
import sqlite3
import unittest
from datetime import datetime, timedelta, timezone

import member_exit_comments as m


class ExitCommentsStoreTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(":memory:")
        m.init_storage(self.db)
        self.now = datetime(2026, 10, 20, tzinfo=timezone.utc)

    def tearDown(self):
        self.db.close()

    def create(self, *, guild=1, user=2, log=10):
        return m.create_pending(
            self.db, guild_id=guild, user_id=user, channel_id=5,
            log_message_id=log, created_at=self.now)

    def test_reversible_schema_and_per_server_isolation(self):
        self.assertTrue(self.create())
        self.assertTrue(self.create(guild=2))
        self.assertFalse(self.create())
        m.init_storage(self.db)
        self.assertEqual(self.db.execute(
            "SELECT COUNT(*) FROM member_exit_comments").fetchone()[0], 2)

    def test_one_dm_link_and_correct_user_only(self):
        self.create()
        self.assertTrue(m.attach_dm(self.db, guild_id=1, log_message_id=10, dm_message_id=20))
        self.assertFalse(m.attach_dm(self.db, guild_id=1, log_message_id=10, dm_message_id=21))
        self.assertIsNone(m.find_by_dm(self.db, dm_message_id=20, user_id=3, now=self.now))
        self.assertIsNotNone(m.find_by_dm(self.db, dm_message_id=20, user_id=2, now=self.now))

    def test_comment_once_then_pending_edit_and_acknowledge(self):
        self.create()
        m.attach_dm(self.db, guild_id=1, log_message_id=10, dm_message_id=20)
        self.assertTrue(m.submit_comment(self.db, dm_message_id=20, user_id=2,
                                         comment=" Motivo opcional ", now=self.now))
        self.assertFalse(m.submit_comment(self.db, dm_message_id=20, user_id=2,
                                          comment="Segundo", now=self.now))
        self.assertEqual(m.pending_edits(self.db)[0]["comment"], "Motivo opcional")
        self.assertTrue(m.mark_applied(self.db, guild_id=1, log_message_id=10))
        self.assertFalse(m.mark_applied(self.db, guild_id=1, log_message_id=10))
        self.assertFalse(m.pending_edits(self.db))

    def test_expired_or_invalid_text_cannot_be_submitted(self):
        self.create()
        m.attach_dm(self.db, guild_id=1, log_message_id=10, dm_message_id=20)
        self.assertFalse(m.submit_comment(self.db, dm_message_id=20, user_id=2,
                         comment="tarde", now=self.now + timedelta(days=8)))
        for value in (" ", "x" * 501):
            with self.assertRaises(ValueError):
                m.submit_comment(self.db, dm_message_id=20, user_id=2,
                                 comment=value, now=self.now)

    def test_purge_does_not_remove_submitted_evidence(self):
        self.create(log=10)
        self.create(log=11)
        m.attach_dm(self.db, guild_id=1, log_message_id=11, dm_message_id=21)
        m.submit_comment(self.db, dm_message_id=21, user_id=2, comment="Adiós", now=self.now)
        self.assertEqual(m.purge_expired(self.db, now=self.now + timedelta(days=39)), 1)
        self.assertEqual(len(m.pending_edits(self.db)), 1)


if __name__ == "__main__":
    unittest.main()
