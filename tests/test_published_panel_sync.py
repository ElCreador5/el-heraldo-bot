"""Regresiones estructurales de sincronización de paneles publicados."""
import ast
from pathlib import Path
import unittest

SOURCE = Path(__file__).resolve().parents[1] / "bot.py"


def function(name):
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    return next(node for node in tree.body
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name)


class PublishedPanelSyncTests(unittest.TestCase):
    def test_startup_reconciles_registered_panels(self):
        code = ast.unparse(function("on_ready"))
        self.assertIn("await synchronize_published_panels(guild, suggestions_already_synced=True)", code)
        self.assertIn("await suggestions_startup()", code)

    def test_join_reconciles_existing_panels(self):
        code = ast.unparse(function("on_guild_join"))
        self.assertIn("await synchronize_published_panels(guild)", code)

    def test_reconciler_only_edits_registered_modules(self):
        code = ast.unparse(function("synchronize_published_panels"))
        self.assertIn("verify_panel_ref", code)
        self.assertIn("await update_verify_panel(guild)", code)
        self.assertIn("suggestions_already_synced", code)
        self.assertIn("suggestion_get_panel_message_id(guild.id)", code)
        self.assertIn("await suggestion_ensure_panel(guild)", code)
        self.assertIn("await ensure_orientation_system(guild)", code)
        self.assertIn("get_orientation_message_id(guild.id)", code)
        self.assertIn("get_orientation_message_channel_id(guild.id)", code)
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

    def test_report_helpers_have_synchronous_callers(self):
        self.assertIsInstance(function("moderation_report_reactions"), ast.FunctionDef)
        self.assertIsInstance(function("moderation_reports_summary"), ast.FunctionDef)
        tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Await) and isinstance(node.value, ast.Call):
                called = node.value.func
                self.assertFalse(isinstance(called, ast.Name) and called.id in {
                    "moderation_report_reactions", "moderation_reports_summary",
                }, "No debe esperarse una función síncrona")

    def test_legacy_defaults_gain_warn_without_overwriting_custom_rules(self):
        source = ast.unparse(function("moderation_report_reactions"))
        self.assertIn("old_defaults", source)
        self.assertIn("if result == old_defaults", source)
        self.assertIn("result.insert(0, warn_default)", source)
        self.assertNotIn("guild_config_set", source)

    def test_missing_warning_is_offered_without_saving(self):
        tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
        editor = next(node for node in tree.body
                      if isinstance(node, ast.ClassDef) and node.name == "ModerationReactionEditModal")
        source = ast.unparse(editor)
        self.assertIn("self.emoji.default", source)
        self.assertIn("❗", source)
        self.assertIn("is_default_warning", source)
        self.assertIn("warn", source)
        self.assertNotIn("guild_config_set", source)
        view = next(node for node in tree.body
                    if isinstance(node, ast.ClassDef) and node.name == "HeraldoUserReportsSetupView")
        overview = next(node for node in view.body
                        if isinstance(node, ast.FunctionDef) and node.name == "_content")
        self.assertIn("Advertencia ❗ no configurada", ast.unparse(overview))

    def test_report_editor_uses_compact_overview(self):
        source = (Path(__file__).resolve().parents[1] / "bot.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        cls = next(node for node in tree.body
                   if isinstance(node, ast.ClassDef) and node.name == "HeraldoUserReportsSetupView")
        content_method = next(node for node in cls.body
                              if isinstance(node, ast.FunctionDef) and node.name == "_content")
        code = ast.unparse(content_method)
        self.assertIn("Reacciones configuradas:", code)
        self.assertIn("Condena directa:", code)
        self.assertNotIn("moderation_reports_summary(", code)
        self.assertNotIn("Para reportar, reacciona al mensaje", code)

    def test_report_summary_does_not_mention_obsolete_rule_button(self):
        code = ast.unparse(function("moderation_reports_summary"))
        self.assertNotIn("Pulsa **Regla**", code)


if __name__ == "__main__":
    unittest.main()
