"""Regresiones para AutoFeeds (sin conexiones reales a Discord)."""
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace as NS

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import discord
import message_autofeeds as feeds
from message_automation import next_occurrence


class AutofeedTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = str(Path(self.tmp.name) / "feeds.db")
        with self.conn() as c:
            c.execute("CREATE TABLE guild_settings (guild_id INTEGER, key TEXT, value TEXT, PRIMARY KEY(guild_id,key))")
            c.execute("CREATE TABLE guild_config (guild_id INTEGER PRIMARY KEY, updated_at TEXT)")
            c.execute("INSERT INTO guild_config(guild_id) VALUES(1)")
            c.execute("""CREATE TABLE message_schedule_state(
                        guild_id INTEGER,job_id TEXT,next_run TEXT,status TEXT DEFAULT 'pending',
                        detail TEXT,PRIMARY KEY(guild_id,job_id))""")
        self.host = {"db_connect": self.conn, "guild_config_get": self.get,
                     "guild_config_set": self.set}
        self.actor = NS(id=7, guild_permissions=discord.Permissions(manage_guild=True))
        self.start = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
        self.job = {"id": "task01", "author": 7, "channel": 10, "autofeed": True,
                    "role": None, "paused": False, "text": "Comunicado",
                    "zone": "UTC", "start": self.start, "repeat": "diaria"}

    def conn(self):
        return sqlite3.connect(self.path, isolation_level=None)

    def get(self, guild_id, key):
        with self.conn() as c:
            row = c.execute("SELECT value FROM guild_settings WHERE guild_id=? AND key=?",
                            (guild_id, key)).fetchone()
            return row[0] if row else None

    def set(self, guild_id, key, value):
        with self.conn() as c:
            c.execute("INSERT INTO guild_settings(guild_id,key,value) VALUES(?,?,?) "
                      "ON CONFLICT(guild_id,key) DO UPDATE SET value=excluded.value",
                      (guild_id, key, value))

    def test_defaults_keep_member_access_off(self):
        self.assertEqual(feeds.policy(self.host, 1),
                         {"enabled": False, "channels": [], "roles": [], "max_per_member": 3})

    def test_message_interval_validation(self):
        for value in ("59m", "0h", "1000000d", "4seconds", "-2h"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                feeds.interval_seconds(value)
        self.assertEqual(feeds.interval_seconds("6h"), 21600)

    def test_disallowed_ambiguous_dst(self):
        for value in ("2027-03-14 02:30", "2027-11-07 01:30"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                feeds.start_from_form(value, "America/New_York")

    def test_atomic_create_and_conflict_do_not_discard_existing_jobs(self):
        self.set(1, feeds.CONFIG_KEY, json.dumps([{"id": "legacy", "author": 9}]))
        before = self.get(1, feeds.CONFIG_KEY)
        feeds.atomic_change(self.host, 1, lambda rows, _: (rows + [self.job], "task01"),
                            expected=before)
        self.assertEqual(len(feeds.get_jobs(self.host, 1)), 2)
        with self.assertRaisesRegex(ValueError, "conflict"):
            feeds.atomic_change(self.host, 1, lambda rows, _: ([], None), expected=before)
        self.assertEqual(len(feeds.get_jobs(self.host, 1)), 2)

    def test_pause_resume_updates_only_own_job_and_status(self):
        self.set(1, feeds.CONFIG_KEY, json.dumps([self.job]))
        feeds.set_paused(self.host, 1, "task01", self.actor, True)
        self.assertTrue(feeds.get_jobs(self.host, 1)[0]["paused"])
        feeds.set_paused(self.host, 1, "task01", self.actor, False)
        self.assertFalse(feeds.get_jobs(self.host, 1)[0]["paused"])
        with self.conn() as c:
            status, due = c.execute("SELECT status,next_run FROM message_schedule_state WHERE guild_id=1 AND job_id='task01'").fetchone()
        self.assertEqual(status, "pending")
        self.assertEqual(due, self.start)

    def test_legacy_job_does_not_become_autofeed(self):
        self.set(1, feeds.CONFIG_KEY, json.dumps([{"id": "legacy", "author": 7}]))
        with self.assertRaises(ValueError):
            feeds.set_paused(self.host, 1, "legacy", self.actor, True)

    def test_interval_and_monthly_next_due(self):
        start = "2027-01-31T10:00:00+00:00"
        monthly = dict(self.job, start=start, repeat="mensual")
        self.assertEqual(next_occurrence(monthly, datetime(2027, 2, 1, tzinfo=timezone.utc)),
                         "2027-02-28T10:00:00+00:00")
        by_hour = dict(self.job, start=start, repeat="intervalo", interval="6h")
        self.assertEqual(next_occurrence(by_hour, datetime(2027, 1, 31, 16, tzinfo=timezone.utc)),
                         "2027-01-31T22:00:00+00:00")

    def test_member_scope_and_revocation(self):
        member = NS(id=77, guild_permissions=discord.Permissions.none(),
                    roles=[NS(id=3)], guild=NS(id=1))
        channel = NS(id=10, permissions_for=lambda _: discord.Permissions(view_channel=True,send_messages=True))
        self.assertFalse(feeds.can_create(self.host, member, channel))
        self.set(1, feeds.POLICY_KEY, json.dumps({"enabled": True, "channels": [10],
                                                 "roles": [3]}))
        self.assertTrue(feeds.can_create(self.host, member, channel))
        channel.id = 11
        self.assertFalse(feeds.can_create(self.host, member, channel))
        self.assertFalse(feeds.can_manage(member, self.job))
        self.assertTrue(feeds.can_manage(self.actor, self.job))


if __name__ == "__main__":
    unittest.main()
