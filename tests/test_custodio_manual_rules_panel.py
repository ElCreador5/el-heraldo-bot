"""Contrato de presentación de Custodio sin ejecutar Discord ni sanciones."""
from i18n_source_helpers import source_text as _source_text
import ast
from pathlib import Path
import unittest

SOURCE = _source_text(Path(__file__).resolve().parents[1] / 'custodio_setup.py', encoding='utf-8')
TREE = ast.parse(SOURCE)


class CustodioManualRulesPanelTests(unittest.TestCase):
    def test_rules_button_has_agreed_name(self):
        self.assertIn('label="Reglas del servidor"', SOURCE)
        self.assertNotIn('label="Consultar reglas del servidor"', SOURCE)

    def test_intro_is_educational_and_mentions_server_rules_requirement(self):
        for text in ("educar cuando sea posible", "Server Rules", "deben estar activas",
                     "no activa IA ni sanciones", "inventa prohibiciones"):
            with self.subTest(text=text):
                self.assertIn(text, SOURCE)

    def test_manual_rules_button_is_separate_from_automatic_startup(self):
        setup = next(n for n in TREE.body if isinstance(n, ast.ClassDef) and n.name == "CustodioSetupView")
        ctor = next(n for n in setup.body if isinstance(n, ast.FunctionDef) and n.name == "__init__")
        self.assertFalse(any(isinstance(n, ast.Call) and
                         isinstance(n.func, ast.Attribute) and n.func.attr == "load_server_rules"
                         for n in ast.walk(ctor)))
        handler = next(n for n in setup.body if isinstance(n, ast.AsyncFunctionDef) and n.name == "check_rules")
        self.assertTrue(any(isinstance(n, ast.Call) and
                        isinstance(n.func, ast.Name) and n.func.id == "load_server_rules"
                        for n in ast.walk(handler)))

    def test_screen_does_not_claim_active_supervision(self):
        self.assertIn("todavía no están activadas", SOURCE)


if __name__ == "__main__":
    unittest.main()
