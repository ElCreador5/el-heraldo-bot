"""NH: los saltos reales de la tarjeta de personalidad se respetan siempre.

Se aísla el generador para no iniciar Discord ni conectar con el Gateway.
"""
import ast
import unittest
from pathlib import Path
from types import SimpleNamespace

SRC = (Path(__file__).resolve().parents[1] / "bot.py").read_text(encoding="utf-8")
TREE = ast.parse(SRC)


def constant(name):
    assign = next(n for n in TREE.body if isinstance(n, ast.Assign)
                  and any(isinstance(t, ast.Name) and t.id == name for t in n.targets))
    return ast.literal_eval(assign.value)


def isolated(name, env):
    fn = next(n for n in TREE.body
              if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
              and n.name == name)
    node = ast.Module(body=[
        ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0),
        fn,
    ], type_ignores=[])
    scope = dict(env)
    exec(compile(ast.fix_missing_locations(node), "<heraldo>", "exec"), scope)
    return scope[name]


class PersonalityEmbedLineBreakTests(unittest.TestCase):
    def helper(self):
        return isolated("normalize_personality_embed_text", {})

    def test_default_help_renders_real_line_breaks(self):
        details = constant("ORIENTATION_EMBED_DETAILS")
        self.assertIn("\n\n**¿Cómo funciona?**\n", details)
        self.assertNotIn("\\n", details)

    def test_legacy_persisted_escaped_text_is_normalized(self):
        normalize = self.helper()
        old = r"Introducción.\n\n**¿Cómo funciona?**\nElige tu rol."
        self.assertEqual(normalize(old),
                         "Introducción.\n\n**¿Cómo funciona?**\nElige tu rol.")
        self.assertEqual(normalize("Texto\n\nOtro apartado"), "Texto\n\nOtro apartado")

    def test_existing_custom_configuration_kept_as_source(self):
        normalize = self.helper()
        old = r"Texto propio\n\nInformación importante"
        values = {"orientation_embed_details": old, "orientation_embed_intro": "Texto inicial"}
        read = lambda guild_id, key: values.get(key)
        getter = isolated("get_orientation_embed_details", {
            "guild_config_get": read,
            "ORIENTATION_EMBED_DETAILS": constant("ORIENTATION_EMBED_DETAILS"),
            "normalize_personality_embed_text": normalize,
        })
        self.assertEqual(getter(9), "Texto propio\n\nInformación importante")
        self.assertEqual(values["orientation_embed_details"], old)

    def test_intro_escapes_also_normalized(self):
        normalize = self.helper()
        getter = isolated("get_orientation_embed_intro", {
            "guild_config_get": lambda _guild, _key: r"Elige uno\nPuedes cambiar después.",
            "ORIENTATION_EMBED_INTRO": constant("ORIENTATION_EMBED_INTRO"),
            "normalize_personality_embed_text": normalize,
        })
        self.assertEqual(getter(1), "Elige uno\nPuedes cambiar después.")


if __name__ == "__main__":
    unittest.main()
