"""Contrato NH UX-03D: etiquetas de interfaz redactadas por el bot en español."""
from i18n_source_helpers import source_text as _source_text
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
BOT = _source_text(ROOT / 'bot.py', 'utf-8')
CUSTODIO = _source_text(ROOT / 'custodio_setup.py', 'utf-8')
RULES = _source_text(ROOT / 'custodio_rule_actions_setup.py', 'utf-8')


class SpanishInterfaceTests(unittest.TestCase):
    def test_legacy_english_user_labels_absent(self):
        for old in (
            'label="Sync now"', 'label="Discord User ID"',
            'label="Definir User ID"', 'label="Footer"',
            "Remove user from list after join",
            "Assign Join Roles for bots",
            "Approx. missing Join Roles",
            "Sync now asigna",
        ):
            with self.subTest(label=old):
                self.assertNotIn(old, BOT)

    def test_join_roles_ui_is_translated_without_renaming_commands(self):
        self.assertIn('label="Sincronizar ahora"', BOT)
        self.assertIn("Roles de ingreso", BOT)
        self.assertIn('ID de usuario de Discord', BOT)
        self.assertIn("joinroles_group.command(name=", BOT)

    def test_custodio_displays_rules_in_spanish(self):
        self.assertNotIn('label="Consultar Server Rules"', CUSTODIO)
        self.assertIn('label="Reglas del servidor"', CUSTODIO)
        self.assertIn("reglas del servidor aprobadas", RULES)


if __name__ == "__main__":
    unittest.main()
