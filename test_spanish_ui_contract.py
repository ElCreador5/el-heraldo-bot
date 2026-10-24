"""Contrato de textos visibles redactados por El Heraldo en español."""
import unittest
from pathlib import Path

SOURCE = Path(__file__).with_name("bot.py").read_text("utf-8")


class SpanishInterfaceTests(unittest.TestCase):
    def test_english_labels_do_not_reappear(self):
        for text in (
            'label="Sync now"', 'label="Discord User ID"',
            'label="Definir User ID"', 'label="Footer"',
            "Remove user from list after join",
            "Assign Join Roles for bots",
            "Approx. missing Join Roles",
            "Sync now asigna",
        ):
            with self.subTest(text=text):
                self.assertNotIn(text, SOURCE)

    def test_roles_interface_uses_spanish_without_breaking_commands(self):
        self.assertIn('label="Sincronizar ahora"', SOURCE)
        self.assertIn("Roles de ingreso", SOURCE)
        self.assertIn('ID de usuario de Discord', SOURCE)
        self.assertIn("joinroles_group.command(name=", SOURCE)


if __name__ == "__main__":
    unittest.main()
