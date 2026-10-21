"""NH: plazos separados y Volver al submenú Verificación."""
import ast
import unittest
from pathlib import Path

SRC=(Path(__file__).resolve().parents[1]/"bot.py").read_text("utf-8")
TREE=ast.parse(SRC)
def get(name):
    return next(n for n in TREE.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)) and n.name==name)
def snippet(name):
    return ast.get_source_segment(SRC,get(name))

class VerificationTimeNavigationTests(unittest.TestCase):
    def test_no_shared_editor(self):
        self.assertNotIn("HeraldoGeneralConfigModal",SRC)
        self.assertNotIn('label="Tiempos"',snippet("HeraldoVerificationHubView"))
        self.assertIn("AgeVerificationTimeModal(self.guild_id)",snippet("HeraldoVerificationSetupView"))
        self.assertIn("PersonalityVerificationTimeModal(self.guild_id)",snippet("HeraldoOrientationSetupView"))
    def test_plazos_separated_without_overwriting_other_settings(self):
        age=snippet("AgeVerificationTimeModal")
        personality=snippet("PersonalityVerificationTimeModal")
        self.assertIn('"verify_timeout"',age)
        self.assertIn('"sin_verificado_timeout_seconds"',age)
        self.assertNotIn("orientation_timeout_seconds",age)
        self.assertIn('"orientation_timeout_seconds"',personality)
        self.assertNotIn('"verify_timeout"',personality)
        for content in (age,personality):
            self.assertIn("confirm_configuration(",content)
            self.assertNotIn("guild_config_set(",content)
            self.assertIn("configuration_access(interaction",content)
        self.assertIn("if value != initial:",age)
        self.assertIn("if value == self.initial:",personality)
    def test_submenu_back_not_home(self):
        for name in ("HeraldoVerificationSetupView","HeraldoOrientationSetupView"):
            code=snippet(name)
            self.assertIn("verification_hub_content(self.guild_id)",code)
            self.assertIn("HeraldoVerificationHubView(self.guild_id, self.owner_id)",code)
            self.assertIn("Guarda o descarta los cambios pendientes antes de volver.",code)
        self.assertIn("heraldo_setup_go_home(",snippet("HeraldoVerificationHubView"))
    def test_individual_summaries(self):
        self.assertIn("age_time_summary(guild.id)",snippet("HeraldoVerificationSetupView"))
        self.assertIn("personality_time_summary(guild.id)",snippet("HeraldoOrientationSetupView"))
        self.assertIn("verification_duration_label(",snippet("age_time_summary"))
        self.assertIn("verification_duration_label(",snippet("personality_time_summary"))

if __name__=="__main__":unittest.main()
