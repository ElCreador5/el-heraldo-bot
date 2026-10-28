"""Regression: hiding Create message must not break regular /setup interactions."""
import unittest
from pathlib import Path
from types import SimpleNamespace as NS

import setup_interactions
from test_safety_regressions import b


class ActivityLaunchAckTests(unittest.TestCase):
    def setUp(self):
        self.view = b.HeraldoMessagesSetupView(901, 10)
        self.item = self.view.panel_select

    def check(self, selection):
        return NS(data={"values": [selection]})

    def test_create_message_is_not_available_in_setup(self):
        self.assertNotIn(
            "create_message", {option.value for option in self.item.options})
        self.assertNotIn(
            "create_message", getattr(self.view, "_no_defer_select_values", ()))
        self.assertFalse(setup_interactions.needs_initial_response(
            self.view, self.item, self.check("create_message")))

    def test_other_setup_options_still_use_fast_auto_ack(self):
        for option in ("kits", "components", "templates", "verification",
                       "webhooks", "sticky", "autoresponses"):
            with self.subTest(option=option):
                self.assertFalse(setup_interactions.needs_initial_response(
                    self.view, self.item, self.check(option)))

    def test_unrelated_setup_views_do_not_bypass_guard(self):
        view = NS(guild_id=901, owner_id=10)
        item = NS(callback=lambda interaction: None)
        self.assertFalse(setup_interactions.needs_initial_response(
            view, item, self.check("create_message")))

    def test_messages_handler_does_not_launch_hidden_activity(self):
        source = (Path(__file__).resolve().parents[1] / "bot.py").read_text(
            encoding="utf-8")
        menu_source = source.split("class HeraldoMessagesSetupView(", 1)[1].split(
            "def validate_setup_view_layouts(", 1)[0]
        self.assertNotIn('"create_message"', menu_source)
        self.assertNotIn("launch_activity(", menu_source)


if __name__ == "__main__":
    unittest.main()
