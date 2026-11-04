"""Regresiones del panel de restauración y cupos de navegación de Discord."""
import unittest
from unittest.mock import AsyncMock, patch

import discord
import panel_navigation
from test_safety_regressions import b, interaction


class RejoinNavigationTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        b.guild_config_set(901, "verified_rejoin_restore_enabled", "0")

    def test_verification_hub_displays_third_option_and_saved_state(self):
        view = b.HeraldoVerificationHubView(901, 10)
        self.assertTrue(any("rejoin" in str(getattr(button, "callback", ""))
                            or getattr(button, "label", None) == b._t("personality.rejoin.toggle")
                            for button in view.children))
        summary = str(b.verification_hub_content(901))
        self.assertIn("Restaurar", summary)

    def test_age_panel_has_room_for_unique_back_and_close(self):
        view = b.HeraldoVerificationSetupView(901, 10)
        panel_navigation.ensure_navigation_controls(view)
        self.assertEqual(len([c for c in view.children
                              if isinstance(c, discord.ui.Button)
                              and c.label in panel_navigation.variants("text.aeccae342e4bd0")]), 1)
        self.assertEqual(len([c for c in view.children
                              if isinstance(c, discord.ui.Button)
                              and c.label in panel_navigation.variants("text.ab26ae7bca3621")]), 1)
        self.assertFalse(any(getattr(c, "label", None) == b._t("personality.rejoin.toggle")
                             for c in view.children))
        # Repeated rendering must not create duplicate navigation controls.
        panel_navigation.ensure_navigation_controls(view)

    def test_rejoin_settings_panel_has_unique_navigation(self):
        view = b.HeraldoRejoinSetupView(901, 10)
        panel_navigation.ensure_navigation_controls(view)
        self.assertEqual(sum(isinstance(c, panel_navigation.AdministrativeClose)
                             for c in view.children), 1)
        self.assertEqual(sum(getattr(c, "label", None) in panel_navigation.variants("text.ab26ae7bca3621")
                             for c in view.children), 1)

    async def test_rejoin_toggle_requires_confirm_before_persisting(self):
        view = b.HeraldoRejoinSetupView(901, 10)
        with patch.object(b, "configuration_access", new=AsyncMock(return_value=True)):
            await view.toggle.callback(interaction())
            self.assertEqual(b.guild_config_get(901, "verified_rejoin_restore_enabled"), "0")
            self.assertTrue(view.pending_enabled)
            req = interaction()
            await view.save_changes.callback(req)
            confirm = req.response.edit_message.call_args.kwargs["view"]
            self.assertIsInstance(confirm, b.HeraldoRejoinConfirmView)
            self.assertEqual(b.guild_config_get(901, "verified_rejoin_restore_enabled"), "0")
            await confirm.confirm.callback(interaction())
            self.assertEqual(b.guild_config_get(901, "verified_rejoin_restore_enabled"), "1")


if __name__ == "__main__":
    unittest.main()
