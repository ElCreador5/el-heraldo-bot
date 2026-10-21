"""Regresiones NH: guardados atómicos y sanciones de Verificación."""
import ast
import unittest
from pathlib import Path
SRC = (Path(__file__).resolve().parents[1] / "bot.py").read_text("utf-8")
TREE = ast.parse(SRC)
def block(name):
    node = next(n for n in TREE.body if isinstance(n, (ast.ClassDef,ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==name)
    return ast.get_source_segment(SRC, node)

class NHVerificationReviewTests(unittest.TestCase):
    def test_transaction_guards_and_rollback(self):
        s=block("verification_atomic_setup_save")
        for text in ("BEGIN IMMEDIATE", "conn.rollback()", "conn.commit()", "WHERE guild_id=?", "expected_settings"):
            self.assertIn(text,s)
        for view in ("HeraldoVerificationSetupView", "HeraldoOrientationSetupView"):
            s=block(view)
            self.assertIn("verification_atomic_setup_save(",s)
            self.assertIn("configuration_access(",s)

    def test_no_direct_unverified_kick_in_bulk_check(self):
        s=block("heraldo_check_all")
        self.assertNotIn('await heraldo_kick(member, reason="No se verificó")',s)
        self.assertIn("await evaluate_verify_timeout(guild.id, member.id)",s)

    def test_personality_kick_retains_pending_on_discord_failure(self):
        s=block("expel")
        self.assertLess(s.index('await heraldo_kick('),s.index('db_clear_tentado(member.guild.id, member.id)',s.index('await heraldo_kick(')))
        self.assertIn("return False",s)
        e=block("evaluate_member")
        self.assertIn('"expulsado" if kicked else "pendiente"',e)

    def test_age_no_partial_save_and_channel_permissions(self):
        s=block("HeraldoVerificationSetupView")
        self.assertLess(s.index('if self.pending_enabled is True and not guild_config_get'),
                        s.index('applied = verification_atomic_setup_save('))
        self.assertIn("perms.read_message_history",s)

if __name__=="__main__": unittest.main()
