"""Checks for the selective moderation warning promotion to main."""
import ast
import unittest
from pathlib import Path

TREE = ast.parse((Path(__file__).resolve().parents[1] / "bot.py").read_text(encoding="utf-8"))


def cls(name):
    return next(node for node in TREE.body if isinstance(node, ast.ClassDef) and node.name == name)


def method(name, parent):
    return ast.unparse(next(node for node in cls(parent).body
                            if getattr(node, "name", None) == name))


class ModerationWarningsMainTests(unittest.TestCase):
    def test_warning_navigation_is_in_moderation_hub_only(self):
        hub = cls("HeraldoModerationSetupView")
        self.assertIn("warnings", {node.name for node in hub.body if isinstance(node, ast.AsyncFunctionDef)})
        self.assertIn("warnings_policy", {node.name for node in hub.body if isinstance(node, ast.AsyncFunctionDef)})
        self.assertIn("HeraldoCasesSetupView", method("warnings", "HeraldoModerationSetupView"))
        self.assertIn("HeraldoWarningPolicyView", method("warnings_policy", "HeraldoModerationSetupView"))
        joins = [node for node in TREE.body if isinstance(node, ast.ClassDef)
                 and node.name.startswith("HeraldoJoinRoles")]
        self.assertTrue(all("warnings" not in {getattr(x, "name", "") for x in node.body}
                            for node in joins))

    def test_pardon_keeps_case_and_notifies_member(self):
        code = method("on_submit", "HeraldoWarningPardonModal")
        self.assertIn("moderation_case_close(", code)
        self.assertIn("resolution=reason", code)
        self.assertIn("await moderation_notify_warning_pardon(", code)
        self.assertNotIn("moderation_case_delete(", code)

    def test_deletion_requires_admin_and_exact_code(self):
        code = method("on_submit", "HeraldoWarningDeleteModal")
        self.assertIn("guild_permissions.administrator", code)
        self.assertIn("str(self.codigo).strip() != code", code)
        self.assertIn("moderation_case_delete(", code)

    def test_warning_limit_is_enforced_on_manual_warn(self):
        code = ast.unparse(next(node for node in TREE.body
                                if isinstance(node, ast.AsyncFunctionDef)
                                and node.name == "moderation_apply_case_punishment"))
        self.assertIn("moderation_warning_counts", code)
        self.assertIn("moderation_warning_limit", code)
        self.assertIn("moderation_warning_escalation", code)

    def test_warning_policy_requires_confirmation(self):
        code = method("review", "HeraldoWarningPolicyView")
        self.assertIn("HeraldoWarningPolicyConfirmView", code)
        code = method("confirm", "HeraldoWarningPolicyConfirmView")
        self.assertIn("guild_config_set", code)


if __name__ == "__main__":
    unittest.main()
