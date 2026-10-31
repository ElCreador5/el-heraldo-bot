"""Evita que los módulos retirados Componentes/Kits reaparezcan en /setup.

Se preservan los botones de roles básicos ya publicados; no se mantienen\ninterfaces para crear plantillas. No exige Gateway ni acceso a Discord.
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
        self.assertNotIn("templates", options)
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

    def test_plantillas_retiradas_sin_ruptura_de_roles_heredados(self):
        # Los mensajes ya publicados no se borran ni pierden los roles básicos.
        self.assertIn("def heraldo_message_role_config", SOURCE)
        self.assertIn("def heraldo_message_role_action", SOURCE)
        self.assertNotIn("class HeraldoTemplateSetupView", SOURCE)
        self.assertNotIn("class HeraldoTemplateModal", SOURCE)
        self.assertNotIn("template_native_builder", SOURCE)
        self.assertNotIn("message_components.install(globals())", SOURCE)
        self.assertNotIn("message_editor.install(globals())", SOURCE)
        self.assertNotIn("message_automation.install(globals())", SOURCE)
        self.assertNotIn('value="templates"', SOURCE)
        self.assertNotIn('@bot.tree.command(name="sendtemplate"', SOURCE)
        self.assertIn("message_autofeeds.install(globals())", SOURCE)

    def test_motor_de_anuncios_no_ejecuta_trabajos_de_plantillas(self):
        worker = (ROOT / "message_automation.py").read_text(encoding="utf-8")
        announcements = (ROOT / "message_autofeeds.py").read_text(encoding="utf-8")
        self.assertIn("if not job.get('autofeed')", worker)
        self.assertNotIn("for config_key in (CONFIG_KEY, STICKY_KEY):", worker)
        self.assertNotIn('plantilla: str = None', announcements)
        self.assertNotIn('host["heraldo_template_list"]', announcements)
        self.assertFalse((ROOT / "template_native_builder.py").exists())


if __name__ == "__main__":
    unittest.main()
