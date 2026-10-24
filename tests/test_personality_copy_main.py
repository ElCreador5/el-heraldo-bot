"""Regression: cambios de texto de personalidad sin alterar datos de producción."""
import ast
import unittest
from pathlib import Path

SOURCE = (Path(__file__).resolve().parents[1] / "bot.py").read_text(encoding="utf-8")
TREE = ast.parse(SOURCE)

class PersonalityCopyMainTests(unittest.TestCase):
    def test_name_and_no_identity_claim(self):
        self.assertIn('ORIENTATION_EMBED_TITLE = "VERIFICACIÓN DE PERSONALIDAD"', SOURCE)
        self.assertNotIn("Esto certifica que eres una persona", SOURCE)
        self.assertIn("no constituye una", SOURCE)
        self.assertIn("verificación de edad", SOURCE)

    def test_config_persists_only_existing_functions(self):
        fn = next(n for n in TREE.body if isinstance(n, ast.FunctionDef)
                  and n.name == "normalize_personality_embed_text")
        namespace = {}
        exec(compile(ast.fix_missing_locations(ast.Module(body=[fn], type_ignores=[])),
                     "<isolated>", "exec"), namespace)
        normalize = namespace["normalize_personality_embed_text"]
        self.assertEqual(normalize(r"Texto\n\nSiguiente"), "Texto\n\nSiguiente")

    def test_dynamic_timeout_and_pre_expulsion_wording(self):
        fn = next(n for n in TREE.body if isinstance(n, ast.FunctionDef)
                  and n.name == "orientation_setup_summary")
        body = ast.get_source_segment(SOURCE, fn)
        self.assertIn("get_orientation_window(guild.id)", body)
        self.assertIn("antes de la expulsión", body)
        self.assertNotIn("temporizador de **10 minutos**", body)

if __name__ == "__main__":
    unittest.main()
