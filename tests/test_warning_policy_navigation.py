"""Regression: warnings policy is linked from Moderation, not Reports extras."""
import ast
import unittest
from pathlib import Path
from i18n_source_helpers import source_text

TREE = ast.parse(source_text(Path(__file__).resolve().parents[1] / "bot.py", encoding="utf-8"))


def cls(name):
    return next(node for node in TREE.body if isinstance(node, ast.ClassDef) and node.name == name)


class WarningPolicyNavigationTests(unittest.TestCase):
    def test_warnings_in_moderation(self):
        hub = cls("HeraldoModerationSetupView")
        fun = next(x for x in hub.body if getattr(x, "name", None) == "warnings_policy")
        self.assertIn("HeraldoWarningLimitSelectView", ast.unparse(fun))

    def test_reports_extras_only_has_reminders_and_navigation(self):
        extra = cls("HeraldoUserReportsMoreOptionsView")
        names = {x.name for x in extra.body if isinstance(x, ast.AsyncFunctionDef)}
        self.assertIn("reminders", names)
        self.assertNotIn("configure_warn_limit", names)

    def test_warning_policy_back_to_moderation(self):
        view = cls("HeraldoWarningLimitSelectView")
        back = next(x for x in view.body if getattr(x, "name", None) == "back")
        self.assertIn("HeraldoModerationSetupView", ast.unparse(back))


if __name__ == "__main__":
    unittest.main()
