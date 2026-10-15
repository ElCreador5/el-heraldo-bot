"""Regresiones estructurales: opciones de Reaction Roles sin escritura manual."""

import ast
from pathlib import Path
import unittest

SRC = Path(__file__).resolve().parents[1] / "bot.py"


def find_class(name):
    tree = ast.parse(SRC.read_text(encoding="utf-8"))
    return next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == name)


def find_method(cls, method):
    return next(node for node in cls.body if isinstance(node, ast.AsyncFunctionDef) and node.name == method)


class ReactionOptionSelectTests(unittest.TestCase):
    def test_three_closed_options_are_selectors(self):
        node = find_class("HeraldoReactionOptionsSelectView")
        init = next(node for node in node.body if isinstance(node, ast.FunctionDef) and node.name == "__init__")
        code = ast.unparse(init)
        self.assertIn('placeholder="Acceso al panel de Reaction Roles"', code)
        self.assertIn('placeholder="Reacciones invertidas"', code)
        self.assertIn('placeholder="Máximo de reacciones por miembro"', code)
        self.assertIn("range(21)", code)
        self.assertIn("discord.ui.Select", code)

    def test_access_and_boolean_are_whitelisted(self):
        cls = find_class("HeraldoReactionOptionsSelectView")
        code = ast.unparse(find_method(cls, "select_access_mode"))
        for text in ("Todos", "Lista blanca", "Lista negra"):
            self.assertIn(text, code)
        self.assertIn("not in", ast.unparse(find_method(cls, "select_reversed")))
        self.assertIn("<= 20", ast.unparse(find_method(cls, "select_maximum")))

    def test_cancel_restores_original_snapshot_and_no_direct_persist(self):
        cls = find_class("HeraldoReactionOptionsSelectView")
        cancel = ast.unparse(find_method(cls, "cancel"))
        save = ast.unparse(find_method(cls, "apply"))
        self.assertIn("self.original_panel", cancel)
        self.assertIn("self.panel", save)
        self.assertNotIn("rr_panel_upsert", ast.unparse(cls))
        self.assertNotIn("guild_config_set", ast.unparse(cls))
        self.assertIn("configuration_access", ast.unparse(find_method(cls, "interaction_check")))

    def test_options_button_uses_selector_not_modal(self):
        cls = find_class("HeraldoReactionRolesEditorView")
        method = ast.unparse(find_method(cls, "options"))
        self.assertIn("HeraldoReactionOptionsSelectView", method)
        self.assertNotIn("HeraldoReactionOptionsModal", method)


if __name__ == "__main__":
    unittest.main()
