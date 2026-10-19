"""Regresiones del contrato general UX; ejecutables sin Discord Gateway.

El control no certifica por sí solo todas las vistas: esas requieren tests específicos
y comprobaciones reales en Heraldo's Lab. Falla si se pierde el estándar o la cobertura CI.
"""
from __future__ import annotations

import ast
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
AGENTS = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
BOT = ast.parse((ROOT / "bot.py").read_text(encoding="utf-8"))


def button_decorators():
    for node in ast.walk(BOT):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for decorator in node.decorator_list:
            if not (isinstance(decorator, ast.Call) and
                    isinstance(decorator.func, ast.Attribute) and
                    decorator.func.attr == "button"):
                continue
            args = {kw.arg: kw.value for kw in decorator.keywords}
            label = args.get("label")
            style = args.get("style")
            if isinstance(label, ast.Constant) and isinstance(label.value, str):
                yield label.value, getattr(style, "attr", None)


class UxContractGate(unittest.TestCase):
    def test_agent_contract_is_unambiguous(self):
        required = ("UX-01", "UX-02", "UX-03", "UX-04", "UX-05",
                    "Cancelar", "Cerrar", "Volver", "Guardar cambios",
                    "sin guardar", "VERIFICADO EN DISCORD")
        for phrase in required:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, AGENTS)

    def test_cancel_close_and_back_decorators(self):
        found = {"cancel": 0, "back": 0}
        for label, style in button_decorators():
            if label.startswith(("Cancelar", "Cerrar")):
                self.assertEqual(style, "danger", label)
                found["cancel"] += 1
            if label.startswith("Volver") or label == "Vista previa":
                self.assertEqual(style, "secondary", label)
                found["back"] += 1
        self.assertGreater(found["cancel"], 0)
        self.assertGreater(found["back"], 0)

    def test_core_ux_regressions_are_run_by_existing_ci(self):
        workflow = (ROOT / ".github/workflows/heraldo-lab-checks.yml").read_text("utf-8")
        self.assertIn("unittest discover -s tests -p 'test_*.py'", workflow)
        for test in (
            "test_button_palette.py",
            "test_editor_drafts_behavior.py",
            "test_configuration_preview.py",
            "test_setup_editor_selectors.py",
            "test_honeypot_panel.py",
        ):
            with self.subTest(test=test):
                self.assertTrue((ROOT / "tests" / test).is_file())


if __name__ == "__main__":
    unittest.main()
