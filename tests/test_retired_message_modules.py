"""Evita que los módulos retirados Componentes/Kits reaparezcan en /setup.

La compatibilidad de botones antiguos sigue activa para no romper plantillas
ni componentes publicados. No exige Gateway ni acceso a Discord.
"""
import ast
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "bot.py").read_text(encoding="utf-8")
TREE = ast.parse(SOURCE)


def cls(name):
    return next(n for n in TREE.body if isinstance(n, ast.ClassDef) and n.name == name)


class RetiredMessageModulesTests(unittest.TestCase):
    def test_options_and_navigation_do_not_expose_retired_modules(self):
        view = cls("HeraldoMessagesSetupView")
        options = [
            kw.value.value
            for node in ast.walk(view)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "SelectOption"
            for kw in node.keywords
            if kw.arg == "value" and isinstance(kw.value, ast.Constant)
        ]
        self.assertIn("templates", options)
        self.assertNotIn("components", options)
        self.assertNotIn("kits", options)
        editor = next(n for n in view.body if isinstance(n, ast.AsyncFunctionDef) and n.name == "open_editor")
        comparisons = [
            value.value for n in ast.walk(editor)
            if isinstance(n, ast.Compare)
            for value in n.comparators
            if isinstance(value, ast.Constant) and isinstance(value.value, str)
        ]
        self.assertNotIn("components", comparisons)
        self.assertNotIn("kits", comparisons)

    def test_no_administrative_views_or_importkit_command(self):
        classes = {node.name for node in TREE.body if isinstance(node, ast.ClassDef)}
        for retired in ("HeraldoMessageKitsView", "HeraldoMessageKitImportModal",
                        "HeraldoMessageComponentsSetupView", "HeraldoMessageRoleModal"):
            self.assertNotIn(retired, classes)
        self.assertNotIn('@bot.tree.command(name="importkit"', SOURCE)

    def test_existing_published_components_and_templates_remain_supported(self):
        self.assertIn("def heraldo_message_role_config", SOURCE)
        self.assertIn("message_components.install(globals())", SOURCE)
        self.assertIn("class HeraldoTemplateSetupView", SOURCE)
        self.assertIn('value="templates"', SOURCE)
        self.assertIn('@bot.tree.command(name="sendtemplate"', SOURCE)


if __name__ == "__main__":
    unittest.main()
