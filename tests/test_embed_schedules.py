"""Unit tests for the standalone scheduled embed engine."""
import sqlite3
import unittest
from datetime import datetime, timezone
import embed_schedules as schedules


class ScheduledEmbedTests(unittest.TestCase):
    def test_default_is_disabled(self):
        conn = sqlite3.connect(":memory:")
        schedules.initialize(conn)
        fields = conn.execute("PRAGMA table_info(scheduled_embeds)").fetchall()
        enabled = next(x for x in fields if x[1] == "enabled")
        self.assertEqual(enabled[4], "0")

    def test_modes(self):
        now = datetime(2026, 10, 15, 12, 0, tzinfo=timezone.utc)
        cases = [
            ("daily", {"time": "18:00"}),
            ("weekly", {"time": "18:00", "days": [0, 2]}),
            ("monthly", {"time": "18:00", "days": [1, 15]}),
            ("interval", {"interval": "6h", "anchor": now.isoformat()}),
            ("once", {"when": "2026-11-01T18:00:00-04:00"}),
        ]
        for mode, config in cases:
            with self.subTest(mode=mode):
                self.assertGreater(schedules.next_due(mode, config, now), now)

    def test_short_units_restricted_outside_test(self):
        with self.assertRaises(ValueError):
            schedules.interval_seconds("30s", False)
        self.assertEqual(schedules.interval_seconds("30s", True), 30)
        with self.assertRaises(ValueError):
            schedules.interval_seconds("2m", False)

    def test_messages_trigger_only_at_count(self):
        import json
        conn = sqlite3.connect(":memory:")
        schedules.initialize(conn)
        conn.execute("INSERT INTO scheduled_embeds(guild_id,embed_name,channel_id,mode,config,enabled,created_at,updated_at) VALUES (1,'sample',2,'messages',?,1,'now','now')", (json.dumps({"count": 10}),))
        conn.commit()
        for _ in range(9):
            self.assertEqual(schedules.advance_message(conn, 1, 2), [])
        self.assertEqual(schedules.advance_message(conn, 1, 2), [(1, "sample")])
        self.assertEqual(schedules.advance_message(conn, 1, 2), [])

    def test_claim_once_no_duplicate(self):
        import json
        conn = sqlite3.connect(":memory:")
        schedules.initialize(conn)
        due = "2026-10-15T12:00:00+00:00"
        conn.execute("INSERT INTO scheduled_embeds(guild_id,embed_name,channel_id,mode,config,enabled,next_due,created_at,updated_at) VALUES (1,'sample',2,'once',?,1,?,'now','now')", (json.dumps({"when": due}), due))
        conn.commit()
        now = datetime(2026, 10, 15, 12, 1, tzinfo=timezone.utc)
        self.assertEqual(len(schedules.claim_due(conn, now)), 1)
        self.assertEqual(schedules.claim_due(conn, now), [])


if __name__ == "__main__":
    unittest.main()
