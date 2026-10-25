"""Regresiones NH: seguridad del autoservicio de personalidad."""
from i18n_source_helpers import source_text as _source_text
import ast
import unittest
from pathlib import Path
src=_source_text(Path(__file__).resolve().parents[1] / 'bot.py', 'utf-8')
tree=ast.parse(src)
def code(name):
    n=next(n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)) and n.name==name)
    return ast.get_source_segment(src,n)
class PersonalitySafetyTests(unittest.TestCase):
    def test_no_reaction_before_verifying_age(self):
        s=code("orientation_reaction_add")
        for term in ("verify_enabled(guild.id)","get_verify_role_id(guild.id)","condemnation_get(guild.id, member.id)","verify_role_problem(target_role, guild)"):
            self.assertIn(term,s)
        self.assertLess(s.index("age_pending ="),s.index("member.add_roles("))
    def test_personality_roles_not_privileged(self):
        self.assertIn("verify_role_problem(role, guild)",code("ensure_orientation_system"))
        self.assertIn("verify_role_problem(role, guild)",code("HeraldoOrientationSetupView"))
    def test_removal_cannot_bypass_no_change(self):
        s=code("orientation_reaction_remove")
        self.assertLess(s.index("if not personality_allow_change(guild.id):"),s.index("member.remove_roles("))
    def test_personality_does_not_replace_age(self):
        self.assertNotIn("or role_ids & get_eval_role_ids",code("_evaluate_verify_timeout_inner"))
        self.assertNotIn("Ya completaste la selección de personalidad.",code("handle_verify_click"))
if __name__=="__main__": unittest.main()
