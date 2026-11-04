"""Pruebas de fechas y horas absolutas de /purge (sin conexiones a Discord)."""
import unittest
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from purge_period import PurgePeriodError, parse_purge_period


TZ = ZoneInfo("America/Santo_Domingo")
NOW = datetime(2026, 11, 3, 21, 0, tzinfo=TZ)


class PurgePeriodTests(unittest.TestCase):
    def parse(self, start, end="", mode="dmy24", locale="es-419"):
        return parse_purge_period(start, end, mode=mode, locale=locale, now=NOW)

    def test_only_from_date_keeps_open_end(self):
        period = self.parse("06/05/2026")
        self.assertEqual(period.display_from, datetime(2026, 5, 6, tzinfo=TZ))
        self.assertEqual(period.after, period.display_from - timedelta(microseconds=1))
        self.assertIsNone(period.before)

    def test_only_until_date_includes_full_day(self):
        period = self.parse("", "06/05/2026")
        self.assertIsNone(period.after)
        self.assertEqual(period.before, datetime(2026, 5, 7, tzinfo=TZ))
        self.assertEqual(period.display_to.date().isoformat(), "2026-05-06")

    def test_equal_dates_cover_a_whole_day(self):
        period = self.parse("06/05/2026", "06/05/2026")
        self.assertEqual(period.before - period.display_from, timedelta(days=1))

    def test_date_range_across_years(self):
        period = self.parse("06/05/2026", "05/01/2027")
        self.assertEqual(period.display_from.date().isoformat(), "2026-05-06")
        self.assertEqual(period.display_to.date().isoformat(), "2027-01-05")
        self.assertEqual(period.before.date().isoformat(), "2027-01-06")

    def test_hours_alone_use_today_and_accept_pm(self):
        period = self.parse("6:00 p. m.", "8:00 PM")
        self.assertEqual(period.display_from, datetime(2026, 11, 3, 18, 0, tzinfo=TZ))
        self.assertEqual(period.before, datetime(2026, 11, 3, 20, 0, tzinfo=TZ))

    def test_date_and_time_in_both_fields(self):
        period = self.parse("06/05/2026 6:00 PM", "06/05/2026 8:00 PM")
        self.assertEqual(period.display_from.hour, 18)
        self.assertEqual(period.before.hour, 20)
        self.assertEqual(period.display_from.date().isoformat(), "2026-05-06")

    def test_month_day_year_twelve_hour_mode(self):
        period = self.parse("05/06/2026 6:00 AM", "05/06/2026 6:00 PM", mode="mdy12")
        self.assertEqual(period.display_from.date().isoformat(), "2026-05-06")
        self.assertEqual(period.display_from.hour, 6)
        self.assertEqual(period.before.hour, 18)

    def test_iso_mode(self):
        period = self.parse("2026-05-06 06:00", "2026-05-06 20:00", mode="iso")
        self.assertEqual(period.display_from.hour, 6)
        self.assertEqual(period.before.hour, 20)

    def test_default_discord_uses_server_locale(self):
        period = self.parse("05/06/2026", mode="discord", locale="en-US")
        self.assertEqual(period.display_from.date().isoformat(), "2026-05-06")

    def test_reject_only_one_time(self):
        with self.assertRaises(PurgePeriodError):
            self.parse("18:00")

    def test_reject_mixed_clock_and_date(self):
        with self.assertRaises(PurgePeriodError):
            self.parse("06/05/2026", "18:00")

    def test_reject_reversed_same_day_hours(self):
        with self.assertRaises(PurgePeriodError):
            self.parse("20:00", "18:00")

    def test_reject_invalid_calendar_date(self):
        with self.assertRaises(PurgePeriodError):
            self.parse("31/02/2026")

    def test_reject_invalid_time(self):
        with self.assertRaises(PurgePeriodError):
            self.parse("06/05/2026 26:00")

    def test_utc_bounds_are_consistent_with_zone(self):
        period = self.parse("06/05/2026 18:00", "06/05/2026 20:00")
        self.assertEqual(period.display_from.astimezone(timezone.utc).hour, 22)
        self.assertEqual(period.before.astimezone(timezone.utc).hour, 0)


if __name__ == "__main__":
    unittest.main()
