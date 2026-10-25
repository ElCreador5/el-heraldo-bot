"""Structural regressions for case actions and live user status."""
from i18n_source_helpers import source_text as _source_text
import ast
import pathlib
import unittest

SOURCE = pathlib.Path(__file__).resolve().parents[1] / "bot.py"


class CaseActionsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tree = ast.parse(_source_text(SOURCE, encoding='utf-8'))
        cls.source = _source_text(SOURCE, encoding='utf-8')

    def function(self, name):
        return next(n for n in self.tree.body if isinstance(n, ast.AsyncFunctionDef) and n.name == name)

    def test_warn_and_ban_buttons_exist(self):
        cls = next(n for n in self.tree.body if isinstance(n, ast.ClassDef) and n.name == "ModerationCaseActionsView")
        names = {n.name for n in cls.body if isinstance(n, ast.AsyncFunctionDef)}
        self.assertIn("warn", names)
        self.assertIn("ban", names)
        self.assertIn("interaction_check", names)

    def test_actions_revalidate_and_use_existing_punishment(self):
        code = ast.unparse(self.function("moderation_case_live_status"))
        self.assertIn("fetch_ban", code)
        self.assertIn("moderation_warning_counts", code)
        action = next(n for n in self.tree.body if isinstance(n, ast.ClassDef) and n.name == "ModerationCaseActionModal")
        handler = next(n for n in action.body if isinstance(n, ast.AsyncFunctionDef) and n.name == "on_submit")
        src = ast.unparse(handler)
        for phrase in ("moderation_apply_case_punishment", "ban_members", "moderate_members", "not row['open']"):
            self.assertIn(phrase, src)

    def test_caseinfo_and_close_report_live_status(self):
        self.assertIn("Situación actual del usuario", ast.unparse(self.function("moderation_caseinfo")))
        self.assertIn("moderation_case_live_status", ast.unparse(self.function("moderation_caseclose")))


if __name__ == "__main__":
    unittest.main()
