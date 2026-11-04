"""Pruebas globales: las horas exactas y las duraciones son conceptos distintos."""
from datetime import datetime, time, timedelta, timezone
import unittest
from zoneinfo import ZoneInfo

from heraldo_datetime import clock_style, format_clock, format_date_time, parse_clock, parse_date_time, parse_reminder_start
from test_safety_regressions import b


class GlobalDateTimeTests(unittest.TestCase):
    def test_twelve_and_twenty_four_are_the_same_instant(self):
        for text in ("6:15 PM", "6:15 p. m.", "18:15"):
            self.assertEqual(parse_clock(text), time(18, 15))
        self.assertEqual(parse_clock("12:00 AM"), time(0, 0))
        self.assertEqual(parse_clock("12:00 PM"), time(12, 0))
        self.assertEqual(parse_clock("6 a. m."), time(6, 0))

    def test_invalid_times_do_not_change_or_guess(self):
        for text in ("25:00", "13:00 PM", "6", "12:75", "18:30 AM", ""):
            with self.subTest(value=text), self.assertRaises(ValueError):
                parse_clock(text)

    def test_explicit_clock_style_overrides_date_order(self):
        self.assertEqual(clock_style("mdy12"), "12h")
        self.assertEqual(clock_style("dmy24"), "24h")
        self.assertEqual(clock_style("mdy12", "24h"), "24h")
        self.assertEqual(format_clock(time(18, 15), "dmy24", "12h"), "6:15 PM")
        self.assertEqual(format_clock(time(18, 15), "mdy12", "24h"), "18:15")

    def test_date_order_is_independent_of_time_style(self):
        instant = datetime(2026, 11, 4, 0, 15, tzinfo=timezone.utc)
        self.assertEqual(
            format_date_time(instant, date_mode="dmy24", time_mode="12h"),
            "03/11/2026 8:15 PM",
        )
        self.assertEqual(
            format_date_time(instant, date_mode="mdy12", time_mode="24h"),
            "11/03/2026 20:15",
        )
        self.assertEqual(
            parse_date_time("03/11/2026 8:15 p. m.", date_mode="dmy24"),
            instant,
        )

    def test_schedule_minute_is_preserved_and_legacy_defaults_to_zero(self):
        guild = 781293
        b.guild_config_set(guild, "template_mode", "weekly")
        b.guild_config_set(guild, "template_hour", "18")
        b.guild_config_set(guild, "template_minute", "15")
        b.guild_config_set(guild, "template_weekday", "1")
        now = datetime(2026, 11, 3, 19, 0, tzinfo=ZoneInfo("America/Santo_Domingo"))
        slot = b.template_last_slot(guild, "weekly", now)
        self.assertEqual((slot.hour, slot.minute), (18, 15))
        self.assertEqual(slot.weekday(), 1)
        b.guild_config_set(guild, "template_minute", "0")
        self.assertEqual(b.get_template_minute(guild), 0)

    def test_reminder_start_accepts_iso_and_configured_date_with_12_or_24h(self):
        now = datetime(2026, 11, 3, 23, 16, tzinfo=ZoneInfo("America/Santo_Domingo"))
        self.assertEqual(
            parse_reminder_start("11/04/2026", "10:30 PM", date_mode="mdy12", now=now),
            "2026-11-04 22:30",
        )
        self.assertEqual(
            parse_reminder_start("04/11/2026", "22:30", date_mode="dmy24", now=now),
            "2026-11-04 22:30",
        )
        self.assertEqual(
            parse_reminder_start("2026-11-04", "22:30", date_mode="mdy12", now=now),
            "2026-11-04 22:30",
        )
        self.assertEqual(parse_reminder_start("", "", now=now), "")
        self.assertEqual(parse_reminder_start("2026-11-04", "", now=now), "2026-11-04")

    def test_reminder_start_allows_clock_without_date_using_next_local_occurrence(self):
        now = datetime(2026, 11, 3, 23, 16, tzinfo=ZoneInfo("America/Santo_Domingo"))
        self.assertEqual(parse_reminder_start("", "10:30 PM", now=now), "2026-11-04 22:30")
        self.assertEqual(parse_reminder_start("", "23:30", now=now), "2026-11-03 23:30")
        for date, clock in (("2026-02-30", "10:30"), ("2026-11-04", "25:00"),
                            ("31/13/2026", "22:30")):
            with self.subTest(date=date, clock=clock), self.assertRaises(ValueError):
                parse_reminder_start(date, clock, now=now)

    def test_punishment_duration_is_not_a_clock(self):
        self.assertEqual(b.parse_duration("1d", 1, 10000), 1440)
        self.assertEqual(b.parse_duration("30m", 1, 10000), 30)


if __name__ == "__main__":
    unittest.main()
