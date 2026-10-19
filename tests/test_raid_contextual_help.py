"""Ayuda dentro de los selectores y campos de Raid Protection, sin mutar SQLite."""
import unittest
from unittest.mock import patch

from test_safety_regressions import b


class RaidContextualHelpTests(unittest.TestCase):
    def test_action_options_have_precise_help_within_discord_limits(self):
        view = b.HeraldoRaidSetupView(901, 10)
        opts = view.action_select.options
        self.assertEqual({op.value for op in opts}, set(b.RAID_ACTION_LABELS))
        self.assertIn("Guardar", view.action_select.placeholder)
        for option in opts:
            with self.subTest(action=option.value):
                self.assertTrue(option.description)
                self.assertLessEqual(len(option.label), 100)
                self.assertLessEqual(len(option.description), 100)
                self.assertIn(option.value, b.RAID_ACTION_HELP)
        self.assertIn("requiere rol Condenado", b.RAID_ACTION_HELP["condemn"])
        self.assertIn("podrían volver", b.RAID_ACTION_HELP["kick"])
        self.assertIn("desbaneo", b.RAID_ACTION_HELP["ban"])
        self.assertIn("aún puede pausar invitaciones", b.RAID_ACTION_HELP["log"])

    def test_role_select_has_contextual_placeholder_without_option_descriptions(self):
        view = b.HeraldoRaidSetupView(901, 10)
        role = next(x for x in view.children if isinstance(x, b.discord.ui.RoleSelect))
        self.assertIn("no es el rol Condenado", role.placeholder)

    def test_detection_inputs_explain_what_each_value_means(self):
        modal = b.HeraldoRaidDetectionModal(901)
        for field in (modal.threshold_input, modal.window_input, modal.age_input,
                      modal.ratio_input, modal.duration_input):
            with self.subTest(label=field.label):
                self.assertTrue(field.placeholder)
                self.assertLessEqual(len(field.placeholder), 100)
        self.assertIn("ingresos", modal.threshold_input.placeholder)
        self.assertIn("tiempo", modal.window_input.placeholder)
        self.assertIn("antigüedad", modal.age_input.placeholder)
        self.assertIn("proporción", modal.ratio_input.placeholder)
        self.assertIn("no duración de sanción", modal.duration_input.placeholder)

    def test_view_creation_does_not_save_configuration(self):
        with patch.object(b, "guild_config_set") as save:
            b.HeraldoRaidSetupView(901, 10)
            b.HeraldoRaidDetectionModal(901)
        save.assert_not_called()


if __name__ == "__main__":
    unittest.main()
