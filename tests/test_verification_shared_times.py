"""NH: mismas opciones de tiempos desde ambos paneles y el centro de verificación."""
import ast
from pathlib import Path
import unittest

SRC=(Path(__file__).resolve().parents[1]/"bot.py").read_text(encoding="utf-8")
TREE=ast.parse(SRC)


def find(name):
    return next(n for n in TREE.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef))
                and n.name==name)


def snippet(name):
    return ast.get_source_segment(SRC,find(name))


class SharedVerificationTimeTests(unittest.TestCase):
    def test_age_personality_and_hub_use_same_editor(self):
        age=snippet("HeraldoVerificationSetupView")
        personality=snippet("HeraldoOrientationSetupView")
        hub=snippet("HeraldoVerificationHubView")
        for text in (age,personality,hub):
            self.assertIn("HeraldoGeneralConfigModal(self.guild_id)",text)
        self.assertIn('label="Configurar tiempos"',age)
        self.assertIn('label="Configurar tiempos"',personality)
        self.assertIn('label="Tiempos"',hub)

    def test_summaries_show_independent_existing_values(self):
        shared=snippet("verification_time_summary")
        for key in ("get_verify_timeout","get_orientation_window","get_sin_verificado_window"):
            self.assertIn(key,shared)
        self.assertIn("verification_time_summary(guild.id)",snippet("HeraldoVerificationSetupView"))
        self.assertIn("verification_time_summary(guild.id)",snippet("HeraldoOrientationSetupView"))
        self.assertIn("verification_time_summary(self.guild_id)",SRC)

    def test_modal_stages_changes_only_and_preserves_unedited_seconds(self):
        modal=snippet("HeraldoGeneralConfigModal")
        for key in ("verify_timeout","orientation_timeout_seconds","sin_verificado_timeout_seconds"):
            self.assertIn(key,modal)
        self.assertIn("if value != initial:",modal)
        self.assertIn("changes[key] = str(minutes * 60)",modal)
        self.assertIn("await confirm_configuration(",modal)
        self.assertNotIn("guild_config_set(",modal)
        self.assertIn("configuration_access(interaction",modal)

    def test_other_pending_changes_must_not_be_lost(self):
        for name in ("HeraldoVerificationSetupView","HeraldoOrientationSetupView"):
            s=snippet(name)
            self.assertIn("Guarda o descarta los cambios pendientes",s)

    def test_real_second_level_not_silently_rounded_in_summary(self):
        label=snippet("verification_duration_label")
        self.assertIn("minutes, rest = divmod(seconds, 60)",label)
        self.assertIn("if rest:",label)


if __name__=="__main__":
    unittest.main()
