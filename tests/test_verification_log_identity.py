"""Regresión del formato de la mención de usuario en verificación de edad."""
from i18n_source_helpers import source_text as _source_text
import ast
import unittest
from pathlib import Path
from types import SimpleNamespace

SOURCE = _source_text(Path(__file__).resolve().parents[1] / 'bot.py', encoding='utf-8')


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
        raise AssertionError(
            f"Se esperaba un registro de edad completada, encontrados: {len(matches)}"
        )
    return matches[0]


class AgeVerificationIdentityLogTests(unittest.TestCase):
    def test_native_mention_not_duplicate_id_or_plain_name(self):
        expression = completed_age_log_message_expression()
        source = ast.unparse(expression)
        self.assertIn("member.mention", source)
        self.assertNotIn("member.id", source)
        self.assertNotIn("member.display_name", source)

    def test_message_without_parentheses_or_repeated_identifier(self):
        expression = completed_age_log_message_expression()
        member = SimpleNamespace(
            display_name="Félix",
            mention="<@987654321>",
            id=987654321,
        )
        actual = eval(
            compile(
                ast.fix_missing_locations(ast.Expression(body=expression)),
                "<age-verification-log>",
                "eval",
            ),
            {"member": member},
        )
        self.assertEqual(actual, "<@987654321> se verificó correctamente.")
        self.assertEqual(actual.count(str(member.id)), 1)
        self.assertNotIn("(", actual)
        self.assertNotIn(")", actual)

    def test_log_sends_embed_not_content_mention(self):
        tree = ast.parse(SOURCE)
        functions = [
            node
            for node in tree.body
            if isinstance(node, ast.AsyncFunctionDef) and node.name == "log_embed"
        ]
        self.assertEqual(len(functions), 1)
        sends = [
            node
            for node in ast.walk(functions[0])
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "send"
        ]
        self.assertTrue(sends)
        for call in sends:
            keys = {keyword.arg for keyword in call.keywords}
            self.assertIn("embed", keys)
            self.assertNotIn("content", keys)


if __name__ == "__main__":
    unittest.main()
