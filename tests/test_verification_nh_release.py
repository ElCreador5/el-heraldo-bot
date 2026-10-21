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


from test_safety_regressions import b
from unittest.mock import patch, AsyncMock
from types import SimpleNamespace as NS


class NHVerificationAtomicRuntimeTests(unittest.IsolatedAsyncioTestCase):
    def test_success_and_stale_draft_cannot_overwrite(self):
        guild = 987651
        b.guild_config_set(guild, "verify_enabled", "0")
        expected = {"verify_enabled": "0", "verify_role_id": None}
        resources = {("role", "tentado"): None}
        self.assertTrue(b.verification_atomic_setup_save(
            guild, expected, {"verify_enabled": "1", "verify_role_id": "301"},
            resources, {("role", "tentado"): 301}))
        self.assertEqual(b.guild_config_get(guild, "verify_enabled"), "1")
        self.assertEqual(b.guild_resource_get(guild, "role", "tentado"), 301)
        self.assertFalse(b.verification_atomic_setup_save(
            guild, expected, {"verify_enabled": "0", "verify_role_id": "302"},
            resources, {("role", "tentado"): 302}))
        self.assertEqual(b.guild_config_get(guild, "verify_role_id"), "301")
        self.assertEqual(b.guild_resource_get(guild, "role", "tentado"), 301)

    def test_roll_back_failed_write_without_partial_config(self):
        guild = 987652
        b.guild_config_set(guild, "verify_enabled", "0")
        conn = b.db_connect()
        try:
            conn.execute("""CREATE TRIGGER IF NOT EXISTS nh_verify_reject_demo
              BEFORE UPDATE ON guild_settings
              WHEN NEW.guild_id = 987652 AND NEW.key = 'verify_enabled'
              BEGIN SELECT RAISE(ABORT, 'fallo inyectado'); END""")
        finally:
            conn.close()
        try:
            with self.assertRaises(b.sqlite3.IntegrityError):
                b.verification_atomic_setup_save(
                    guild, {"verify_enabled": "0"}, {"verify_enabled": "1"},
                    {}, {("role", "tentado"): 500})
            self.assertEqual(b.guild_config_get(guild, "verify_enabled"), "0")
            self.assertIsNone(b.guild_resource_get(guild, "role", "tentado"))
        finally:
            conn = b.db_connect()
            try:
                conn.execute("DROP TRIGGER IF EXISTS nh_verify_reject_demo")
            finally:
                conn.close()

    async def test_failed_personality_kick_keeps_tracking(self):
        guild_id, user_id = 987653, 9631
        b.db_upsert_join(guild_id, user_id, None)
        b.db_set_tentado(guild_id, user_id, b.datetime.now(b.timezone.utc))
        guild = NS(id=guild_id, owner_id=1)
        member = NS(id=user_id, guild=guild)
        rejection = b.discord.HTTPException(NS(status=403, reason="simulado"), "rechazado")
        with (patch.object(b, "orientation_enabled", return_value=True),
              patch.object(b, "personality_required", return_value=True),
              patch.object(b, "heraldo_is_test", return_value=False),
              patch.object(b, "prepare_removal_dm", new=AsyncMock(return_value=None)),
              patch.object(b, "send_recovery_dm", new=AsyncMock(return_value=True)),
              patch.object(b, "heraldo_kick", new=AsyncMock(side_effect=rejection))):
            kicked = await b.expel(member, report=False)
        self.assertFalse(kicked)
        self.assertIsNotNone(b.db_get(guild_id, user_id)["tentado_at"])

if __name__=="__main__": unittest.main()
