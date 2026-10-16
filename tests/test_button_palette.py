"""Estándar semántico de botones de El Heraldo; verificación sin Gateway."""
from __future__ import annotations

import ast
from pathlib import Path
import unittest

CODE = (Path(__file__).resolve().parents[1] / "bot.py").read_text("utf-8")
TREE = ast.parse(CODE)

def decorators():
    for node in ast.walk(TREE):
        for decorator in getattr(node, "decorator_list", ()):
            if (isinstance(decorator, ast.Call)
                    and isinstance(decorator.func, ast.Attribute)
                    and decorator.func.attr == "button"):
                opts = {arg.arg: arg.value for arg in decorator.keywords}
                label = opts.get("label")
                style = opts.get("style")
                if isinstance(label, ast.Constant) and isinstance(label.value, str):
                    yield node, label.value, getattr(style, "attr", None)


class ButtonPaletteTests(unittest.TestCase):
    def test_destructive_actions_are_red(self):
        required = {"Eliminar", "Banear", "Expulsar", "Advertir",
                    "Descartar cambios", "Descartar", "Desactivar",
                    "Restaurar valores", "Confirmar eliminación"}
        seen = set()
        for _, label, style in decorators():
            if label in required:
                self.assertEqual(style, "danger", label)
                seen.add(label)
        self.assertTrue({"Descartar cambios", "Eliminar", "Banear"}.issubset(seen))

    def test_positive_actions_are_green(self):
        for _, label, style in decorators():
            if label.startswith("Guardar") or label in {
                "Publicar", "Confirmar acceso", "Confirmar edición",
                "Publicar / actualizar", "Activar", "Crear canal",
            }:
                self.assertEqual(style, "success", label)

    def test_editor_buttons_are_blue(self):
        for _, label, style in decorators():
            if label in {"Editar", "Condiciones", "Personalizar",
                         "Indicar razón", "Editar tarjeta", "Campo",
                         "Revisar programación", "Revisar cambios",
                         "Aplicar al borrador", "Baneo temporal"}:
                self.assertEqual(style, "primary", label)

    def test_navigation_is_grey(self):
        for _, label, style in decorators():
            if label.startswith("Cancelar") or label.startswith("Volver") or label == "Cerrar":
                self.assertEqual(style, "secondary", label)

    def test_runtime_buttons_follow_action_semantics(self):
        scope = next(x for x in TREE.body if isinstance(x, ast.ClassDef)
                     and x.name == "HoneypotTrapActionConfirmView")
        init = next(x for x in scope.body if isinstance(x, ast.FunctionDef) and x.name == "__init__")
        self.assertIn('action == "remove"', ast.unparse(init))
        self.assertIn("self.confirm.style", ast.unparse(init))
        scheduler = next(x for x in TREE.body if isinstance(x, ast.ClassDef)
                         and x.name == "EmbedScheduleView")
        toggle = next(x for x in scheduler.body
                      if isinstance(x, ast.AsyncFunctionDef) and x.name == "toggle")
        self.assertIn("self.toggle.style", ast.unparse(toggle))
        self.assertIn('discord.ButtonStyle.danger if self.active else discord.ButtonStyle.success',
                      CODE)
        self.assertIn('("WARN", "Advertir", discord.ButtonStyle.danger)', CODE)

if __name__ == "__main__":
    unittest.main()
