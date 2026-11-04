"""Regression tests for the Discord warning pardon/delete UI."""
import ast
import json
import unittest
from pathlib import Path
from string import Formatter

from i18n_source_helpers import source_text

ROOT = Path(__file__).resolve().parents[1]
TREE = ast.parse(source_text(ROOT / "bot.py", encoding="utf-8"))


def method(classname, name):
    cls = next(
        n for n in TREE.body
        if isinstance(n, ast.ClassDef) and n.name == classname
    )
    node = next(
        n for n in cls.body
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == name
    )
    return ast.unparse(node)


class WarningManagementPanelTests(unittest.TestCase):
    def test_panel_has_selection_and_navigation(self):
        code = method("HeraldoCasesSetupView", "_rebuild_warning_select")
        self.assertIn("moderation_active_warning_cases", code)
        self.assertIn("default=int(row['case_number']) == self.selected_case", code)
        for action in ("pardon", "delete_warning", "refresh", "back", "close"):
            self.assertTrue(method("HeraldoCasesSetupView", action))

    def test_pardon_preserves_history_and_requires_reason(self):
        code = method("HeraldoWarningPardonModal", "on_submit")
        self.assertIn("guild_permissions.moderate_members", code)
        self.assertIn("moderation_case_close(", code)
        self.assertIn("closed_by=interaction.user.id", code)
        self.assertIn("resolution=reason", code)
        self.assertNotIn("moderation_case_delete(", code)

    def test_delete_is_admin_only_and_requires_exact_case_code(self):
        code = method("HeraldoWarningDeleteModal", "on_submit")
        self.assertIn("guild_permissions.administrator", code)
        self.assertIn("str(self.confirmation).strip() != code", code)
        self.assertIn("moderation_case_delete(", code)

    def test_expired_warnings_are_not_offered_for_pardon(self):
        func = next(n for n in TREE.body if isinstance(n, ast.FunctionDef)
                    and n.name == "moderation_active_warning_cases")
        self.assertIn("expires_at", ast.unparse(func))
        self.assertIn("datetime.now(timezone.utc)", ast.unparse(func))

    def test_pardon_notice_dm_then_channel_fallback(self):
        helper = next(n for n in TREE.body if isinstance(n, ast.AsyncFunctionDef)
                      and n.name == "moderation_notify_warning_pardon")
        source = ast.unparse(helper)
        self.assertIn("await member.send(", source)
        self.assertIn("await channel.send(", source)
        self.assertLess(source.index("await member.send("), source.index("await channel.send("))
        self.assertIn("Advertencia perdonada", source)
        self.assertIn("tu advertencia", source)
        self.assertIn("return 'failed'", source)
        submit = method("HeraldoWarningPardonModal", "on_submit")
        self.assertIn("await moderation_notify_warning_pardon(", submit)
        self.assertIn("Se notificó al miembro por DM", submit)
        self.assertIn("Se notificó en este canal", submit)
        self.assertIn("No se pudo entregar la notificación", submit)

    def test_all_translations_match_variables(self):
        messages = []
        for lang in ("es-419", "en-US", "pt-BR"):
            catalog = json.loads((ROOT / "locales" / f"{lang}.json").read_text(encoding="utf-8"))
            subset = {key: value for key, value in catalog.items()
                      if key.startswith("moderation.warning.")}
            messages.append({key: {
                field for _, field, _, _ in Formatter().parse(value) if field
            } for key, value in subset.items()})
        self.assertEqual(messages[0], messages[1])
        self.assertEqual(messages[0], messages[2])


if __name__ == "__main__":
    unittest.main()
