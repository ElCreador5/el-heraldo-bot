"""Pruebas estructurales del flujo central de confirmación de /setup."""
import ast
from pathlib import Path
import unittest

SOURCE = Path(__file__).resolve().parents[1] / "bot.py"


def find_function(name):
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    return next(node for node in tree.body
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                and node.name == name)


class ConfigurationPreviewTests(unittest.TestCase):
    def test_no_json_attachment_in_confirmation(self):
        code = ast.unparse(find_function("confirm_configuration"))
        self.assertNotIn("propuesta.json", code)
        self.assertNotIn("discord.File", code)
        self.assertIn("discord.Embed", code)
        self.assertIn("configuration_review_value", code)
        self.assertIn("allowed_mentions=discord.AllowedMentions.none()", code)

    def test_unmodified_values_bypass_save(self):
        code = ast.unparse(find_function("confirm_configuration"))
        self.assertIn("guild_config_get", code)
        self.assertIn("if not changed:", code)
        self.assertIn("No hay cambios pendientes", code)
        self.assertIn("ConfigurationConfirmView(guild_id, interaction.user.id, changed)", code)

    def test_existing_confirmation_keeps_safety_checks(self):
        tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
        cls = next(node for node in tree.body
                   if isinstance(node, ast.ClassDef) and node.name == "ConfigurationConfirmView")
        code = ast.unparse(cls)
        self.assertIn("BEGIN IMMEDIATE", code)
        self.assertIn("self.original", code)
        self.assertIn("configuration_access", code)
        self.assertIn("Propuesta cancelada", code)
        self.assertIn("conn.commit()", code)

    def test_sensitive_ids_are_resolved_to_names(self):
        code = ast.unparse(find_function("configuration_review_value"))
        self.assertIn("guild.get_channel", code)
        self.assertIn("guild.get_role", code)
        self.assertIn("discord.utils.escape_mentions", code)
        self.assertIn("join_role_ids", code)


if __name__ == "__main__":
    unittest.main()
