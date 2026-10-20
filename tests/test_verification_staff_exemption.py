"""Exenciones de verificación para propietario y personal moderador (sin Discord real)."""
from __future__ import annotations

import ast
import unittest
from pathlib import Path
from types import SimpleNamespace as NS

SOURCE = (Path(__file__).resolve().parents[1] / "bot.py").read_text(encoding="utf-8")
TREE = ast.parse(SOURCE)
FUNCTIONS = {n.name:n for n in TREE.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}

def isolate(name):
    node = FUNCTIONS[name]
    module = ast.Module(body=[
        ast.ImportFrom(module="__future__",names=[ast.alias(name="annotations")],level=0),
        node,
    ],type_ignores=[])
    context = {}
    exec(compile(ast.fix_missing_locations(module),"bot.py","exec"),context)
    return context[name]

class StaffExemptionTests(unittest.TestCase):
    def test_permissions_all_recognized_without_role_names(self):
        checker = isolate("verification_is_exempt")
        guild = NS(owner_id=2)
        self.assertTrue(checker(NS(id=2,guild=guild)))
        for key in ("administrator","manage_guild","manage_messages",
                    "moderate_members","kick_members","ban_members"):
            self.assertTrue(checker(NS(id=5,guild=guild,
                guild_permissions=NS(**{key:True}))),key)
        self.assertFalse(checker(NS(id=5,guild=guild,
            guild_permissions=NS(manage_roles=True))))
        self.assertFalse(checker(NS(id=5,guild=guild)))

    def test_guards_all_expiry_paths(self):
        targets=("run_verification_expiry","evaluate_member","expel",
                 "reconcile_untracked_verifications_for_guild","on_member_join",
                 "on_member_update")
        for name in targets:
            self.assertIn("verification_is_exempt(",ast.get_source_segment(SOURCE,FUNCTIONS[name]),name)
        code=ast.get_source_segment(SOURCE,FUNCTIONS["on_member_update"])
        self.assertLess(code.index("verification_is_exempt(after)"),
                        code.index("db_set_sin_verificado("))
        self.assertIn("verification_is_exempt(before)",code)
        self.assertIn("db_set_verify_pending(",code)
        self.assertIn("clear_verification_expiry(",code)

    def test_owner_exemption_never_bypasses_moderation_event_handlers(self):
        node = FUNCTIONS["on_member_update"]
        owner = next(
            statement for statement in node.body
            if isinstance(statement, ast.If)
            and "owner_id" in ast.unparse(statement.test)
        )
        self.assertFalse(
            any(isinstance(step, (ast.Return, ast.Break, ast.Continue))
                for step in owner.body),
            "La exención del propietario no debe saltarse las condenas."
        )
        code = ast.get_source_segment(SOURCE, node)
        self.assertLess(code.index("owner_id"), code.index("condemnation_get("))
        self.assertIn("verification_is_exempt(after)", code)

if __name__=="__main__":
    unittest.main()
