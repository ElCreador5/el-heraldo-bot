"""Contrato NH: controles de personalidad, borradores y conservación."""
from i18n_source_helpers import source_text as _source_text
import ast
import unittest
from pathlib import Path
SOURCE=_source_text(Path(__file__).resolve().parents[1] / 'bot.py', encoding='utf-8')
TREE=ast.parse(SOURCE)
def get(name,kind):
    return next(x for x in TREE.body if isinstance(x,kind) and x.name==name)
def code(n):
    return ast.get_source_segment(SOURCE,n)
class PersonalitySetupTests(unittest.TestCase):
    def test_disable_never_destroys_roles_or_panel(self):
        text=code(get("disable_orientation_system",ast.AsyncFunctionDef))
        self.assertIn("clear_personality_pending_for_guild",text)
        for wrong in ("message.delete(", "orientation_role_bindings", "DELETE FROM guild_resources"):
            self.assertNotIn(wrong,text)
        self.assertIn("message.edit(",text)
    def test_flags_gate_expulsions_and_keep_defaults(self):
        self.assertIn("personality_required(guild.id)",code(get("evaluate_member",ast.AsyncFunctionDef)))
        self.assertIn("personality_required(member.guild.id)",code(get("expel",ast.AsyncFunctionDef)))
        self.assertIn('!= "0"',code(get("personality_required",ast.FunctionDef)))
    def test_modals_only_stage(self):
        modal=get("PersonalityRecoveryDMModal",ast.ClassDef)
        submit=next(x for x in modal.body if isinstance(x,ast.AsyncFunctionDef) and x.name=="on_submit")
        self.assertIn("view.pending_dm_template = draft",code(submit))
        self.assertNotIn("guild_config_set(",code(submit))
        view=get("HeraldoOrientationSetupView",ast.ClassDef)
        methods={x.name:x for x in view.body if isinstance(x,ast.AsyncFunctionDef)}
        for name in ("toggle_required","toggle_change","edit_dm","discard_changes"):
            self.assertNotIn("guild_config_set(",code(methods[name]))
        save=code(methods["save_changes"])
        for key in ("personality_required","personality_allow_change","personality_recovery_dm_template"):
            self.assertIn(key,save)
        self.assertIn("self.pending_dm_template = None",code(methods["discard_changes"]))
if __name__=="__main__": unittest.main()
