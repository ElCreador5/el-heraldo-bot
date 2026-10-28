"""Regression: /setup must reserve the initial Discord ACK to launch Activities."""
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

    def test_create_message_reserves_initial_response_for_activity(self):
        self.assertIn("create_message", self.view._no_defer_select_values)
        self.assertTrue(setup_interactions.needs_initial_response(
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

    def test_activity_launch_is_initial_response_in_handler(self):
        source = (Path(__file__).resolve().parents[1] / "bot.py").read_text(
            encoding="utf-8")
        self.assertIn('self._no_defer_select_values = frozenset(("create_message",))', source)
        self.assertIn("await interaction.response.launch_activity()", source)
        self.assertIn("ACTIVITY_LAUNCH status=FAILED", source)


if __name__ == "__main__":
    unittest.main()
