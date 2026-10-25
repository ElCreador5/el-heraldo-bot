"""NH: pie de verificación identificado por servidor, sin campo manual ni SQLite.

Regresiones aisladas: no se inicia Discord ni se abre una base de datos real.
"""
from __future__ import annotations
from i18n_source_helpers import source_text as _source_text

import ast
import unittest
from pathlib import Path
from types import SimpleNamespace

SOURCE = _source_text(Path(__file__).resolve().parents[1] / 'bot.py', 'utf-8')
TREE = ast.parse(SOURCE)
NODES = {
    n.name: n for n in TREE.body
    if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
}
LAB_NAME = "El Heraldo's Labs 🧪"


def snippet(name):
    return ast.get_source_segment(SOURCE, NODES[name])


def isolate(name, **namespace):
    mod = ast.Module(body=[
        ast.ImportFrom(module="__future__",
                       names=[ast.alias(name="annotations")], level=0),
        NODES[name],
    ], type_ignores=[])
    namespace.setdefault("LAB_FOOTER_TEXT", LAB_NAME)
    exec(compile(ast.fix_missing_locations(mod), "<isolated>", "exec"),
         namespace)
    return namespace[name]


class FakeEmbed:
    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.footer = None
        self.fields = []

    def add_field(self, **kwargs):
        self.fields.append(kwargs)

    def set_footer(self, **kwargs):
        self.footer = kwargs


class ServerFooterTests(unittest.TestCase):
    def test_dm_footer_tracks_each_server_and_uses_server_icon(self):
        guild_a = SimpleNamespace(id=10, name="Laboratorio", icon=SimpleNamespace(url="https://example.org/a.png"))
        guild_b = SimpleNamespace(id=20, name="Comunidad", icon=SimpleNamespace(url="https://example.org/b.png"))
        discord = SimpleNamespace(Embed=FakeEmbed, Color=lambda value: value)
        builder = isolate(
            "build_verification_welcome_embed",
            discord=discord,
            VarContext=lambda guild, member: guild,
            get_verify_dm_color=lambda gid: "4F5BDC",
            VERIFY_DM_COLOR_DEFAULT="4F5BDC",
            render_vars=lambda text, ctx, limit: text,
            render_url_var=lambda value, ctx: (
                ctx.icon.url if value == "{servericon}" and ctx is not None and ctx.icon else ""
            ),
            get_verify_dm_title=lambda gid: "Verificado",
            get_verify_dm_field_name=lambda gid: "Mensaje",
            get_verify_dm_body=lambda gid: "Bienvenido",
            get_verify_dm_footer_icon=lambda gid: "{servericon}",
        )
        self.assertEqual(builder(guild=guild_a).footer, {
            "text": LAB_NAME, "icon_url": "https://example.org/a.png",
        })
        self.assertEqual(builder(guild=guild_b).footer, {
            "text": LAB_NAME, "icon_url": "https://example.org/b.png",
        })
        self.assertEqual(builder().footer["text"], LAB_NAME)
        self.assertNotIn("get_verify_dm_footer(", snippet("build_verification_welcome_embed"))

    def test_personality_footer_uses_actual_server_name_not_legacy_value(self):
        getter = isolate("get_orientation_embed_footer")
        self.assertEqual(getter(SimpleNamespace(id=1, name="Laboratorio")), LAB_NAME)
        self.assertEqual(getter(SimpleNamespace(id=2, name="Otro servidor")), LAB_NAME)
        self.assertNotIn("guild_config_get(", snippet("get_orientation_embed_footer"))

    def test_dm_legacy_footer_no_longer_controls_rendering(self):
        getter = isolate(
            "get_verify_dm_footer",
            bot=SimpleNamespace(
                get_guild=lambda gid: SimpleNamespace(name="Servidor nuevo")
                if gid == 123 else None
            ),
        )
        self.assertEqual(getter(123), LAB_NAME)
        self.assertEqual(getter(99), LAB_NAME)
        self.assertNotIn('"verify_dm_footer"', snippet("build_verification_welcome_embed"))

    def test_content_modal_does_not_demand_or_save_footer(self):
        source = snippet("VerifyDmEditorContentModal")
        self.assertNotIn("footer_input", source)
        self.assertNotIn('"verify_dm_footer":', source)
        self.assertIn("confirm_configuration(", source)
        self.assertIn('"verify_dm_color"', source)

    def test_personality_modal_keeps_four_editable_fields(self):
        source = snippet("OrientationEmbedModal")
        self.assertNotIn("footer_input", source)
        self.assertNotIn("orientation_embed_footer", source)
        self.assertIn("confirm_configuration(", source)
        self.assertIn("orientation_embed_color", source)

    def test_slash_editor_uses_confirm_not_legacy_direct_save(self):
        node = NODES["verify_dm_texts"]
        params = [arg.arg for arg in node.args.args]
        self.assertNotIn("footer", params)
        self.assertIn("icono_footer", params)
        source = snippet("verify_dm_texts")
        self.assertNotIn('"verify_dm_footer":', source)
        self.assertNotIn("guild_config_set(", source)
        self.assertIn("await confirm_configuration(", source)

    def test_removed_parameter_is_not_registered_for_autocomplete(self):
        self.assertIn('("titulo", "campo", "mensaje", "icono_footer")', SOURCE)
        self.assertNotIn('("titulo", "campo", "mensaje", "footer", "icono_footer")', SOURCE)

    def test_global_brand_footer_still_uses_server_and_preserves_informative_footer(self):
        self.assertIn('GLOBAL_FOOTER_TEXT = LAB_FOOTER_TEXT', SOURCE)
        self.assertIn('GLOBAL_FOOTER_ICON = "{servericon}"', SOURCE)
        self.assertIn("server_footer_text(guild.name, detail)", snippet("stamp_embed"))
        self.assertIn("if guild is None:", snippet("stamp_embed"))


if __name__ == "__main__":
    unittest.main()
