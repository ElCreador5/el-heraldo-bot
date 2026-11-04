"""Pruebas sin Gateway de la promoción selectiva a main."""
import asyncio
import unittest
from datetime import datetime, timezone
from unittest.mock import AsyncMock
from zoneinfo import ZoneInfo

import discord
from heraldo_datetime import clock_style, format_clock, parse_clock
from server_structure_setup import (
    ServerStructureSetupView, StructureScheduleModal, ACTIVE_MODES,
    FIELDS, MARKERS, parse_weekday,
)
from date_time_setup import ServerDateTimeSetupView


class MainStructurePromotionTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.guild_id = 1234
        self.owner_id = 99
        self.settings = {
            "template_mode": "off",
            "template_hour": "4",
            "template_minute": "0",
            "template_weekday": "6",
            "template_monthday": "1",
        }

        def get(_guild_id, key):
            return self.settings.get(key)

        def number(key, default):
            return lambda guild_id: int(get(guild_id, key) or default)

        self.host = {
            "guild_config_get": get,
            "get_template_mode": lambda guild_id: get(guild_id, "template_mode") or "off",
            "get_template_hour": number("template_hour", 4),
            "get_template_minute": number("template_minute", 0),
            "get_template_weekday": number("template_weekday", 6),
            "get_template_monthday": number("template_monthday", 1),
            "template_config_summary": lambda guild_id, now: "Frecuencia: desactivada",
            "configuration_access": AsyncMock(return_value=True),
        }

    def structure(self, mode):
        self.settings["template_mode"] = mode
        return ServerStructureSetupView(self.host, self.guild_id, self.owner_id)

    async def test_daily_only_exact_clock(self):
        view = self.structure("daily")
        modal = StructureScheduleModal(view)
        self.assertEqual(len(modal.children), 1)
        self.assertFalse(hasattr(modal, "weekday"))
        self.assertFalse(hasattr(modal, "monthday"))
        self.assertFalse(hasattr(modal, "interval"))
        self.assertEqual(set(ACTIVE_MODES), {"off", "daily", "weekly", "monthly"})

    async def test_weekly_day_and_clock_only(self):
        view = self.structure("weekly")
        modal = StructureScheduleModal(view)
        self.assertEqual(len(modal.children), 2)
        self.assertTrue(hasattr(modal, "weekday"))
        self.assertFalse(hasattr(modal, "monthday"))
        self.assertEqual(parse_weekday("miércoles"), 2)
        self.assertEqual(parse_weekday("quarta-feira"), 2)

    async def test_monthly_monthday_and_clock_only(self):
        view = self.structure("monthly")
        modal = StructureScheduleModal(view)
        self.assertEqual(len(modal.children), 2)
        self.assertFalse(hasattr(modal, "weekday"))
        self.assertTrue(hasattr(modal, "monthday"))
        self.assertNotIn("template_interval_minutes", FIELDS)
        self.assertIn("template_interval_minutes", MARKERS)

    async def test_legacy_interval_is_read_only(self):
        view = self.structure("interval")
        self.assertTrue(view.schedule.disabled)
        self.assertTrue(view.save.disabled)
        self.assertIn("interval", {option.value for option in view.chooser.options})
        self.assertNotIn("template_interval_minutes", FIELDS)

    async def test_new_panel_never_offers_interval(self):
        view = self.structure("off")
        self.assertTrue(view.schedule.disabled)
        self.assertNotIn("interval", {option.value for option in view.chooser.options})

    async def test_global_format_has_separate_selections(self):
        view = ServerDateTimeSetupView(self.host, self.guild_id, self.owner_id)
        self.assertEqual({item.value for item in view.date_select.options},
                         {"discord", "dmy24", "mdy12", "iso"})
        self.assertEqual({item.value for item in view.time_select.options}, {"12h", "24h"})
        self.assertTrue(view.save.disabled)
        self.assertEqual(clock_style("dmy24", "12h"), "12h")
        self.assertEqual(format_clock(datetime(2026, 1, 1, 18, 15), "iso", "12h"), "6:15 PM")
        self.assertEqual(parse_clock("6:15 p. m."), datetime(2026, 1, 1, 18, 15).time())


if __name__ == "__main__":
    unittest.main()
