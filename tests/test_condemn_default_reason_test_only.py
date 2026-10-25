"""Regresión: el motivo por defecto de /condenar solo funciona en Railway Test."""
from i18n_source_helpers import source_text as _source_text
import ast
from pathlib import Path
import unittest


class CondemnReasonTests(unittest.TestCase):
    def test_optional_reason_restricted_to_test_project(self):
        tree = ast.parse(_source_text(Path(__file__).resolve().parents[1] / 'bot.py', encoding='utf-8'))
        fn = next(n for n in tree.body if isinstance(n, ast.AsyncFunctionDef) and n.name == "condenar")
        source = ast.unparse(fn)
        self.assertIn("RAILWAY_PROJECT_ID", source)
        self.assertIn("747a1ee0-cdab-4ad5-8e45-a6ddfccc9b61", source)
        self.assertIn("Prueba funcional autorizada de El Heraldo Test.", source)
        self.assertIn("motivo de la condena es obligatorio", source)
        self.assertEqual(fn.args.defaults[0].value, None)


if __name__ == "__main__":
    unittest.main()
