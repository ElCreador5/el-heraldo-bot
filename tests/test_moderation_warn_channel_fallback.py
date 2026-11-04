"""Regression checks: WARN notices fall back to the originating channel."""
import ast
import json
import unittest
from pathlib import Path

from i18n_source_helpers import source_text

ROOT = Path(__file__).resolve().parents[1]
TREE = ast.parse(source_text(ROOT / "bot.py", encoding="utf-8"))


def function_source(name):
    node = next(
        node for node in TREE.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == name
    )
    return ast.unparse(node)


class WarningChannelFallbackTests(unittest.TestCase):
    def test_fallback_only_after_failed_manual_dm(self):
        code = function_source("moderation_apply_case_punishment")
        self.assertIn("moderation_warn_channel_fallback(interaction.channel, member, case_number)", code)
        self.assertIn("moderation_warn_channel_fallback(interaction.channel, member, case_number)", code)
        self.assertLess(code.index("moderation_warn_channel_fallback("), code.index("moderation_warning_escalation("))

    def test_reaction_warn_uses_message_channel(self):
        code = function_source("execute_moderation_report_action")
        self.assertIn("moderation_warn_channel_fallback(message.channel, target, case_number)", code)
        self.assertIn("if not sent:", code)

    def test_public_notice_is_minimal_and_mentions_only_member(self):
        code = function_source("moderation_warn_channel_fallback")
        self.assertIn("recibido una advertencia", code)
        self.assertIn("users=[member]", code)
        self.assertIn("everyone=False", code)
        self.assertNotIn("reason", code)
        self.assertNotIn("proof", code)

    def test_all_locales_have_matching_tokens(self):
        from string import Formatter
        signatures = []
        for locale in ("es-419", "en-US", "pt-BR"):
            catalog = json.loads((ROOT / "locales" / f"{locale}.json").read_text(encoding="utf-8"))
            message = catalog["moderation.warn.channel_fallback"]
            signatures.append({field for _, field, _, _ in Formatter().parse(message) if field})
        self.assertEqual(signatures, [{"p0", "p1"}] * 3)


if __name__ == "__main__":
    unittest.main()
