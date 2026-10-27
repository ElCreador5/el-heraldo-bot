"""Regresión del subpanel de Server Rules, sin Gateway ni inferencia."""
from i18n_source_helpers import source_text as _source_text
import ast
from pathlib import Path
import unittest

SOURCE = _source_text(Path(__file__).resolve().parents[1] / 'custodio_setup.py', 'utf-8')
TREE = ast.parse(SOURCE)


class CustodioRulesNavigationTests(unittest.TestCase):
    def test_manual_rules_reader_only(self):
        cls = next(n for n in TREE.body if isinstance(n, ast.ClassDef) and n.name == "CustodioSetupView")
        constructor = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == "__init__")
        self.assertFalse(any(
            isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "load_server_rules"
            for n in ast.walk(constructor)
        ))
        self.assertIn('label="Reglas del servidor"', SOURCE)

    def test_subpanel_disallows_unconfigured_ai(self):
        self.assertIn("class CustodioRulesView", SOURCE)
        self.assertIn("from custodio_ai_runtime import analyze_rule, AIUnavailable", SOURCE)
        self.assertIn("free_provider_not_configured", SOURCE)
        self.assertIn("text.custodio.ai_unavailable", SOURCE)

    def test_subpanel_back_navigation(self):
        self.assertIn("view=self.parent, embed=None", SOURCE)

    def test_snapshot_is_not_saved_or_approved(self):
        cls = next(n for n in TREE.body if isinstance(n, ast.ClassDef) and n.name == "CustodioRulesView")
        methods = {n.name: n for n in cls.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
        self.assertTrue({"__init__", "interaction_check", "summary", "analyze_rules", "back",
                         "choose_rule", "fragments", "previous", "next", "sync"}.issubset(methods))
        self.assertNotIn("set_setting(", ast.get_source_segment(SOURCE, cls))


if __name__ == "__main__":
    unittest.main()
