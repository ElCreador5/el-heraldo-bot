"""Regresiones de interfaz del editor de política de reportes."""
import ast
import unittest
from pathlib import Path
from i18n_source_helpers import source_text

SOURCE = Path(__file__).resolve().parents[1] / "bot.py"
TREE = ast.parse(source_text(SOURCE, encoding="utf-8"))
POLICY = next(n for n in TREE.body if isinstance(n, ast.ClassDef)
              and n.name == "HeraldoWarningLimitSelectView")


def member(name):
    return ast.unparse(next(n for n in POLICY.body if getattr(n, "name", None) == name))


class ModerationPolicyUITests(unittest.TestCase):
    def test_report_actions_are_distinguishable_from_escalation(self):
        setup = member("__init__")
        self.assertIn("self.punishment_select", setup)
        self.assertIn("default=False", setup)
        self.assertIn("label=f", setup)
        self.assertIn("text.d91694e8816537", setup)

    def test_only_timeout_shows_duration(self):
        controls = member("_refresh_controls")
        self.assertIn("self.escalation == 'timeout'", controls)
        self.assertIn("self.remove_item(self.duration_select)", controls)
        self.assertIn("self.review.disabled = not bool(self._changes())", controls)

    def test_back_returns_to_report_parent(self):
        back = member("back")
        self.assertIn("HeraldoUserReportsSetupView", back)
        self.assertIn("interaction.response.edit_message", back)

    def test_review_persists_only_real_changes(self):
        self.assertIn("self._changes()", member("review"))
        self.assertIn("confirm_configuration(", member("review"))


if __name__ == "__main__":
    unittest.main()
