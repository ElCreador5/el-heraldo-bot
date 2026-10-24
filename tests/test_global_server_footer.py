"""Regresiones transversales NH: todo embed con guild identifica su servidor.

No inicia Discord; prueba los generadores de tarjetas en aislamiento AST.
"""
from __future__ import annotations
import ast
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import message_payload

SOURCE = (Path(__file__).resolve().parents[1] / "bot.py").read_text("utf-8")
TREE = ast.parse(SOURCE)
FUNCS = {n.name: n for n in TREE.body
         if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}


def isolate(*names, env=None):
    scope = dict(env or {})
    tree = ast.fix_missing_locations(ast.Module(body=[
        ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0),
        *(FUNCS[n] for n in names),
    ], type_ignores=[]))
    exec(compile(tree, "<isolated>", "exec"), scope)
    return scope


class FakeEmbed:
    def __init__(self, values=None):
        self.title = values.get("title") if values else None
        self.description = values.get("description") if values else None
        footer = (values or {}).get("footer") or {}
        self.footer = SimpleNamespace(text=footer.get("text"), icon_url=footer.get("icon_url"))

    @classmethod
    def from_dict(cls, values):
        return cls(values)

    def set_footer(self, *, text, icon_url=None):
        self.footer = SimpleNamespace(text=text, icon_url=icon_url)


def server(name, icon=None, gid=1):
    return SimpleNamespace(id=gid, name=name,
                           icon=SimpleNamespace(url=icon) if icon else None)


class ServerFooterTests(unittest.TestCase):
    def test_existing_operational_footer_preserved_with_server_and_icon(self):
        env = isolate("server_footer_text", "stamp_embed",
                      env={"bot": SimpleNamespace(), "heraldo_footer": lambda g: ("El Heraldo", "")})
        guild = server("Heraldo's Lab", "https://example.org/icon.png")
        embed = FakeEmbed({"footer": {"text": "Resolución 42 · Guardado"}})
        stamped = env["stamp_embed"](embed, guild)
        self.assertIs(stamped, embed)
        self.assertEqual(stamped.footer.text,
                         "Heraldo's Lab · Resolución 42 · Guardado")
        self.assertEqual(stamped.footer.icon_url, "https://example.org/icon.png")
        self.assertIs(env["stamp_embed"](embed, guild), embed)
        self.assertEqual(stamped.footer.text.count("Heraldo's Lab"), 1)

    def test_no_footer_or_other_server_does_not_cross_brand(self):
        env = isolate("server_footer_text", "stamp_embed", env={
            "heraldo_footer": lambda _: ("El Heraldo", "")
        })
        plain = FakeEmbed()
        env["stamp_embed"](plain, server("Comunidad Alfa"))
        self.assertEqual(plain.footer.text, "Comunidad Alfa")
        other = FakeEmbed({"footer": {"text": "Advertencia activa", "icon_url": "https://x.test/icon"}})
        env["stamp_embed"](other, server("Comunidad Beta"))
        self.assertEqual(other.footer.text, "Comunidad Beta · Advertencia activa")
        self.assertEqual(other.footer.icon_url, "https://x.test/icon")
        # No hay servidor verificable: no tomar otro servidor al azar.
        unknown = FakeEmbed()
        env["stamp_embed"](unknown, None)
        self.assertEqual(unknown.footer.text, "El Heraldo")

    def test_no_repeated_name_existing_at_end_and_limit(self):
        f = isolate("server_footer_text")["server_footer_text"]
        self.assertEqual(f("Comunidad", "Expediente · Comunidad"), "Expediente · Comunidad")
        self.assertEqual(f("Comunidad", "Comunidad · Expediente"), "Comunidad · Expediente")
        text = f("Comunidad", "a" * 2048)
        self.assertEqual(len(text), 2048)
        self.assertTrue(text.startswith("Comunidad · "))
        self.assertIn("a", text)

    def test_message_templates_apply_brand_per_guild_before_discord(self):
        discord = SimpleNamespace(Embed=FakeEmbed,
                                  AllowedMentions=SimpleNamespace(none=lambda: None))
        env = isolate("server_footer_text", "heraldo_template_payload", env={
            "message_payload": message_payload,
            "discord": discord,
            "datetime": datetime,
            "timezone": timezone,
            "heraldo_template_view": lambda template: None,
        })
        template = {"embeds": [
            {"title": "Alerta", "footer": {"text": "Expediente 1"}},
            {"title": "Actualización"},
        ]}
        a = env["heraldo_template_payload"](template, server("Uno", "https://example.org/uno.png", 1))
        b = env["heraldo_template_payload"](template, server("Dos", None, 2))
        self.assertEqual([e.footer.text for e in a["embeds"]],
                         ["Uno · Expediente 1", "Uno"])
        self.assertEqual([e.footer.text for e in b["embeds"]],
                         ["Dos · Expediente 1", "Dos"])
        self.assertEqual(a["embeds"][0].footer.icon_url, "https://example.org/uno.png")
        self.assertEqual(template["embeds"][0]["footer"]["text"], "Expediente 1")
        self.assertNotIn("footer", template["embeds"][1])

    def test_template_limit_rejected_not_silently_truncated(self):
        discord = SimpleNamespace(Embed=FakeEmbed,
                                  AllowedMentions=SimpleNamespace(none=lambda: None))
        env = isolate("server_footer_text", "heraldo_template_payload", env={
            "message_payload": message_payload,
            "discord": discord,
            "datetime": datetime,
            "timezone": timezone,
            "heraldo_template_view": lambda template: None,
        })
        template = {"embeds": [{"title": "Uno", "description": "x" * 5995}]}
        with self.assertRaisesRegex(ValueError, "6000"):
            env["heraldo_template_payload"](template, server("Laboratorio"))
        self.assertNotIn("footer", template["embeds"][0])

    def test_no_lingering_hardcoded_brand_in_embed_footers(self):
        self.assertNotIn('set_footer(text="Paraíso Morboso 2026 · El Heraldo")', SOURCE)
        src = ast.get_source_segment(SOURCE, FUNCS["stamp_embed"])
        self.assertIn("server_footer_text(guild.name, detail)", src)
        source = ast.get_source_segment(SOURCE, FUNCS["heraldo_template_payload"])
        self.assertIn('message_payload.validate({"embeds": prepared})', source)


if __name__ == "__main__":
    unittest.main()
