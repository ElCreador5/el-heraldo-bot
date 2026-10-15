"""Regresiones estructurales de sincronización de paneles publicados."""
import ast
from pathlib import Path
import unittest

SOURCE = Path(__file__).resolve().parents[1] / "bot.py"


def function(name):
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    return next(node for node in tree.body
                if isinstance(node, ast.AsyncFunctionDef) and node.name == name)


class PublishedPanelSyncTests(unittest.TestCase):
    def test_startup_reconciles_registered_panels(self):
        code = ast.unparse(function("on_ready"))
        self.assertIn("await synchronize_published_panels(guild)", code)
        self.assertIn("await suggestions_startup()", code)

    def test_reconciler_only_edits_registered_modules(self):
        code = ast.unparse(function("synchronize_published_panels"))
        self.assertIn("verify_panel_ref", code)
        self.assertIn("await update_verify_panel(guild)", code)
        self.assertIn("suggestion_get_panel_message_id(guild.id)", code)
        self.assertIn("await suggestion_ensure_panel(guild)", code)
        self.assertIn("await ensure_orientation_system(guild)", code)
        self.assertNotIn("condemnation", code)
        self.assertNotIn("message.delete", code)

    def test_verification_updates_on_changes(self):
        tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
        cls = next(node for node in tree.body
                   if isinstance(node, ast.ClassDef) and node.name == "ConfigurationConfirmView")
        code = ast.unparse(cls)
        for key in ("verify_role_id", "verify_timeout", "verify_action",
                    "verify_panel_text", "verify_button_label"):
            self.assertIn(key, code)
        self.assertIn("await update_verify_panel(interaction.guild)", code)

    def test_report_summary_does_not_mention_obsolete_rule_button(self):
        code = ast.unparse(function("moderation_reports_summary"))
        self.assertNotIn("Pulsa **Regla**", code)


if __name__ == "__main__":
    unittest.main()
