"""Regresiones reales del desplegable de acción de Raid Protection, sin Discord Gateway."""
import unittest
from unittest.mock import patch

from test_safety_regressions import b, interaction


class RaidActionSelectorTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.guild_id = 981245
        b.guild_config_set(self.guild_id, "raid_action", "condemn")

    def make_interaction(self):
        i = interaction(guild_id=self.guild_id)
        return i

    @staticmethod
    def selected(view):
        return [option.value for option in view.action_select.options if option.default]

    async def choose(self, view, value):
        i = self.make_interaction()
        view.action_select._values = [value]
        await view.select_action(i)
        return i

    async def test_action_remains_visibly_selected_without_implicit_save(self):
        view = b.HeraldoRaidSetupView(self.guild_id, 10)
        self.assertEqual(self.selected(view), ["condemn"])
        i = await self.choose(view, "kick")
        self.assertEqual(view.pending_action, "kick")
        self.assertEqual(self.selected(view), ["kick"])
        self.assertIs(i.response.edit_message.call_args.kwargs["view"], view)
        self.assertIn("Cambios pendientes", i.response.edit_message.call_args.kwargs["content"])
        self.assertEqual(b.raid_action(self.guild_id), "condemn")
        await self.choose(view, "ban")
        self.assertEqual(self.selected(view), ["ban"])
        self.assertEqual(b.raid_action(self.guild_id), "condemn")

    async def test_save_updates_visual_selection_and_new_panel(self):
        view = b.HeraldoRaidSetupView(self.guild_id, 10)
        await self.choose(view, "ban")
        i = self.make_interaction()
        await view.save_changes.callback(i)
        self.assertEqual(b.raid_action(self.guild_id), "ban")
        self.assertIsNone(view.pending_action)
        self.assertEqual(self.selected(view), ["ban"])
        self.assertEqual(self.selected(b.HeraldoRaidSetupView(self.guild_id, 10)), ["ban"])
        i.edit_original_response.assert_awaited_once()

    async def test_discard_restores_actual_setting_without_writing(self):
        view = b.HeraldoRaidSetupView(self.guild_id, 10)
        await self.choose(view, "log")
        i = self.make_interaction()
        with patch.object(b, "guild_config_set") as persist:
            await view.discard_changes.callback(i)
        persist.assert_not_called()
        self.assertIsNone(view.pending_action)
        self.assertEqual(self.selected(view), ["condemn"])
        self.assertEqual(b.raid_action(self.guild_id), "condemn")
        i.response.edit_message.assert_awaited_once()

    async def test_invalid_condemn_selection_does_not_replace_choice(self):
        b.guild_config_set(self.guild_id, "raid_action", "kick")
        view = b.HeraldoRaidSetupView(self.guild_id, 10)
        i = await self.choose(view, "condemn")
        self.assertIsNone(view.pending_action)
        self.assertEqual(self.selected(view), ["kick"])
        self.assertEqual(b.raid_action(self.guild_id), "kick")
        i.response.send_message.assert_awaited_once()
        i.response.edit_message.assert_not_awaited()

    async def test_other_pending_changes_keep_action_selection(self):
        view = b.HeraldoRaidSetupView(self.guild_id, 10)
        await self.choose(view, "log")
        await view.toggle_invites.callback(self.make_interaction())
        self.assertEqual(self.selected(view), ["log"])
        self.assertEqual(b.raid_action(self.guild_id), "condemn")


if __name__ == "__main__":
    unittest.main()
