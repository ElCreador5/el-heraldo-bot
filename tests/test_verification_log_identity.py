"""Regresión del nombre mostrado en el registro de verificación de edad."""
import ast
import unittest
from pathlib import Path
from types import SimpleNamespace

import discord

SOURCE = (Path(__file__).resolve().parents[1] / "bot.py").read_text(encoding="utf-8")


def completed_age_log_message_expression():
    tree = ast.parse(SOURCE)
    matches = [
        node.args[2]
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "log_embed"
        and len(node.args) >= 3
        and isinstance(node.args[1], ast.Constant)
        and node.args[1].value == "Verificación de edad completada"
    ]
    if len(matches) != 1:
        raise AssertionError(f"Se esperaba un registro de edad completada, encontrados: {len(matches)}")
    return matches[0]


class AgeVerificationIdentityLogTests(unittest.TestCase):
    def test_display_name_without_mention_or_discord_id(self):
        expression = completed_age_log_message_expression()
        source = ast.unparse(expression)
        self.assertIn("member.display_name", source)
        self.assertNotIn("member.mention", source)
        self.assertNotIn("member.id", source)
        self.assertIn("escape_mentions", source)
        self.assertIn("escape_markdown", source)

    def test_visible_name_is_escaped_without_notifying_members(self):
        expression = completed_age_log_message_expression()
        name = "Mod **Ejemplo** @everyone"
        member = SimpleNamespace(display_name=name, mention="<@987654321>", id=987654321)
        value = eval(
            compile(ast.fix_missing_locations(ast.Expression(body=expression)), "<age-verification-log>", "eval"),
            {"discord": discord, "member": member},
        )
        self.assertIn("Mod", value)
        self.assertIn("Ejemplo", value)
        self.assertIn("se verificó correctamente.", value)
        self.assertNotIn("987654321", value)
        self.assertNotIn("<@", value)
        self.assertNotIn("@everyone", value)
        self.assertNotIn("**Ejemplo**", value)


if __name__ == "__main__":
    unittest.main()
