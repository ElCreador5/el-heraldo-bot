"""Regresión sin Gateway: Solo reportar nunca puede activar una purga."""
import ast
from pathlib import Path
import unittest

SOURCE = Path(__file__).resolve().parents[1].joinpath("bot.py").read_text(encoding="utf-8")
TREE = ast.parse(SOURCE)

def function_named(name):
    return next(node for node in ast.walk(TREE) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name)

class ReportOnlySafety(unittest.TestCase):
    def test_report_returns_before_any_purge(self):
        fn = function_named("execute_moderation_report_action")
        report_branch = next(node for node in fn.body if isinstance(node, ast.If) and ast.unparse(node.test) == "action == 'report'")
        self.assertTrue(any(isinstance(node, ast.Return) for node in report_branch.body))
        purge_call = next(node for node in ast.walk(fn) if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "run_purge_job")
        self.assertLess(report_branch.lineno, purge_call.lineno)

    def test_legacy_normalization_discards_report_purge(self):
        fn = function_named("_normalize_moderation_report_rule")
        self.assertTrue(any(isinstance(node, ast.If) and ast.unparse(node.test) == "action == 'report'" and any(isinstance(stmt, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "purge_minutes" for t in stmt.targets) and isinstance(stmt.value, ast.Constant) and stmt.value.value is None for stmt in node.body) for node in ast.walk(fn)))

    def test_report_purge_not_allowed_in_modal(self):
        fn = next(node for node in ast.walk(TREE) if isinstance(node, ast.ClassDef) and node.name == "ModerationReactionRuleModal")
        submit = next(node for node in fn.body if isinstance(node, ast.AsyncFunctionDef) and node.name == "on_submit")
        self.assertTrue(any(isinstance(node, ast.If) and ast.unparse(node.test) == "action == 'report' and purge_minutes" and any(isinstance(stmt, ast.Return) for stmt in node.body) for node in ast.walk(submit)))

if __name__ == "__main__":
    unittest.main()
