"""Regresión sin Gateway: Solo reportar nunca puede activar una purga."""
from i18n_source_helpers import source_text as _source_text
import ast
from pathlib import Path
import unittest

SOURCE = _source_text(Path(__file__).resolve().parents[1].joinpath('bot.py'), encoding='utf-8')
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
        # Ejecutar la normalización real: la versión heredada también puede
        # traer delete_message=True. Ninguna ruta informativa debe purgar.
        node = function_named("_normalize_moderation_report_rule")
        module = ast.fix_missing_locations(ast.Module(body=[node], type_ignores=[]))
        env = {"MODERATION_REPORT_ACTIONS": {
            "report", "warn", "timeout", "condemn", "kick", "ban",
        }, "PURGE_MAX_MINUTES": 1440}
        exec(compile(module, "<normalized-report-safety>", "exec"), env)
        normalize = env["_normalize_moderation_report_rule"]
        for action, fields in (
            ("report", {"purge_minutes": 30}),
            ("report", {"delete_message": True}),
            ("warn", {"purge_minutes": 30}),
            ("unknown", {"delete_message": True}),
        ):
            with self.subTest(action=action, fields=fields):
                normalized = normalize({
                    "emoji": "🚩", "label": "Infracción", "action": action, **fields,
                })
                self.assertIsNotNone(normalized)
                self.assertEqual(normalized["action"], "report" if action == "unknown" else action)
                self.assertIsNone(normalized["purge_minutes"])
        # Evita convertir esta protección en una desactivación global de purgas.
        sanctioned = normalize({
            "emoji": "🚩", "label": "Infracción", "action": "kick",
            "purge_minutes": 30,
        })
        self.assertEqual(sanctioned["purge_minutes"], 30)

    def test_report_purge_not_allowed_in_modal(self):
        fn = next(node for node in ast.walk(TREE) if isinstance(node, ast.ClassDef) and node.name == "ModerationReactionRuleModal")
        submit = next(node for node in fn.body if isinstance(node, ast.AsyncFunctionDef) and node.name == "on_submit")
        self.assertTrue(any(isinstance(node, ast.If) and ast.unparse(node.test) == "action == 'report' and purge_minutes" and any(isinstance(stmt, ast.Return) for stmt in node.body) for node in ast.walk(submit)))

if __name__ == "__main__":
    unittest.main()
