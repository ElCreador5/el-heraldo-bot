"""Contrato de configuración de idioma antes de liberar traducciones nuevas."""
import ast
from pathlib import Path
import unittest

SOURCE = Path(__file__).resolve().parents[1].joinpath("bot.py").read_text(encoding="utf-8")
TREE = ast.parse(SOURCE)


def function(name):
    return next(node for node in TREE.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                and node.name == name)


def klass(name):
    return next(node for node in TREE.body if isinstance(node, ast.ClassDef) and node.name == name)


class LanguageContract(unittest.TestCase):
    def test_shared_editor_and_command_exist(self):
        klass("HeraldoLanguageView")
        command = function("language")
        self.assertIn("configuration_access", ast.unparse(command))
        self.assertIn("ephemeral=True", ast.unparse(command))
        setup = ast.unparse(klass("HeraldoSetupView"))
        self.assertIn("selected == 'language'", setup)
        self.assertIn("HeraldoLanguageView", setup)

    def test_language_is_never_auto_saved_by_selection(self):
        view = klass("HeraldoLanguageView")
        handler = next(node for node in view.body if isinstance(node, ast.AsyncFunctionDef)
                       and node.name == "select_language")
        self.assertNotIn("guild_config_set", ast.unparse(handler))
        save = next(node for node in view.body if isinstance(node, ast.AsyncFunctionDef)
                    and node.name == "save")
        self.assertIn("guild_config_set", ast.unparse(save))
        self.assertIn("LANGUAGE_READY", ast.unparse(save))

    def test_only_complete_languages_are_enabled(self):
        assignments = [node for node in TREE.body if isinstance(node, ast.Assign)
                       and any(isinstance(t, ast.Name) and t.id == "LANGUAGE_READY"
                               for t in node.targets)]
        self.assertEqual(len(assignments), 1)
        self.assertIn("i18n.SUPPORTED_LOCALES", ast.unparse(assignments[0]))
        from heraldo_i18n import SUPPORTED_LOCALES
        self.assertEqual(SUPPORTED_LOCALES, frozenset({"es-419"}))

    def test_guild_isolation_and_fallback(self):
        getter = ast.unparse(function("guild_language"))
        self.assertIn("guild_id", getter)
        self.assertIn("guild_config_get(guild_id,", getter)
        self.assertIn("es-419", getter)


if __name__ == "__main__":
    unittest.main()
