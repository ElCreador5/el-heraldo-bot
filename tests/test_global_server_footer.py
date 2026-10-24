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

LAB_NAME = "El Heraldo's Labs 🧪"

SOURCE = (Path(__file__).resolve().parents[1] / "bot.py").read_text("utf-8")
TREE = ast.parse(SOURCE)
FUNCS = {n.name: n for n in TREE.body
         if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}


def isolate(*names, env=None):
    scope = {"LAB_FOOTER_TEXT": LAB_NAME, **(env or {})}
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
                         "El Heraldo's Labs 🧪 · Resolución 42 · Guardado")
        self.assertEqual(stamped.footer.icon_url, "https://example.org/icon.png")
        self.assertIs(env["stamp_embed"](embed, guild), embed)
        self.assertEqual(stamped.footer.text.count(LAB_NAME), 1)

    def test_no_footer_or_other_server_does_not_cross_brand(self):
        env = isolate("server_footer_text", "stamp_embed", env={
            "heraldo_footer": lambda _: ("El Heraldo", "")
        })
        plain = FakeEmbed()
        env["stamp_embed"](plain, server("Comunidad Alfa"))
        self.assertEqual(plain.footer.text, LAB_NAME)
        other = FakeEmbed({"footer": {"text": "Advertencia activa", "icon_url": "https://x.test/icon"}})
        env["stamp_embed"](other, server("Comunidad Beta"))
        self.assertEqual(other.footer.text, LAB_NAME + " · Advertencia activa")
        self.assertIsNone(other.footer.icon_url)
        # No hay servidor verificable: no tomar otro servidor al azar.
        unknown = FakeEmbed()
        env["stamp_embed"](unknown, None)
        self.assertEqual(unknown.footer.text, LAB_NAME)

    def test_no_repeated_name_existing_at_end_and_limit(self):
        f = isolate("server_footer_text")["server_footer_text"]
        self.assertEqual(f("Comunidad", "Expediente · Comunidad"), LAB_NAME + " · Expediente")
        self.assertEqual(f("Comunidad", "Comunidad · Expediente"), LAB_NAME + " · Expediente")
        with self.assertRaisesRegex(ValueError, "2048"):
            f("Comunidad", "a" * 2048)
        self.assertEqual(f("Lab", "Colaboradores activos"), LAB_NAME + " · Colaboradores activos")

    def test_unknown_dm_does_not_borrow_even_the_only_cached_guild(self):
        env = isolate("heraldo_footer", env={
            "bot": SimpleNamespace(guilds=[server("Comunidad privada")],
                                   user=SimpleNamespace(name="El Heraldo")),
        })
        self.assertEqual(env["heraldo_footer"](None), (LAB_NAME, ""))

    def test_hook_copies_embeds_per_destination_and_preserves_limit_data(self):
        from test_safety_regressions import b
        embed = b.discord.Embed(description="Texto", color=123)
        embed.set_footer(text="Expediente 42")
        _, first = b._embedify(None, {"embed": embed}, server("Alfa"), None)
        _, second = b._embedify(None, {"embed": embed}, server("Beta"), None)
        self.assertEqual(first["embed"].footer.text, LAB_NAME + " · Expediente 42")
        self.assertEqual(second["embed"].footer.text, LAB_NAME + " · Expediente 42")
        self.assertEqual(embed.footer.text, "Expediente 42")
        full = b.discord.Embed(description="x" * 4000)
        full.add_field(name="Campo", value="y" * 1024)
        full.add_field(name="Campo", value="z" * 950)
        with self.assertRaisesRegex(ValueError, "6000"):
            b._embedify(None, {"embed": full}, server("Comunidad de laboratorio"), None)
        self.assertIsNone(full.footer.text)

    def test_text_editor_clearing_embeds_does_not_send_conflicting_arguments(self):
        from test_safety_regressions import b
        content, payload = b._embedify("Borrador preparado", {"embeds": []}, server("Lab"), None)
        self.assertIsNone(content)
        self.assertNotIn("embeds", payload)
        self.assertEqual(payload["embed"].description, "Borrador preparado")
        self.assertEqual(payload["embed"].footer.text, LAB_NAME)

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
                         [LAB_NAME + " · Expediente 1", LAB_NAME])
        self.assertEqual([e.footer.text for e in b["embeds"]],
                         [LAB_NAME + " · Expediente 1", LAB_NAME])
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
        template = {"embeds": [{"description": "x" * 4000}, {"description": "y" * 1998}]}
        with self.assertRaisesRegex(ValueError, "6000"):
            env["heraldo_template_payload"](template, server("Laboratorio"))
        self.assertNotIn("footer", template["embeds"][0])

    def test_templates_and_profiles_keep_their_real_guild_context(self):
        template_fn = FUNCS["template_report_embed"]
        self.assertEqual(template_fn.args.args[0].arg, "guild")
        scheduled = ast.get_source_segment(SOURCE, FUNCS["run_scheduled_template_backup"])
        manual = ast.get_source_segment(SOURCE, FUNCS["template_sync"])
        profile = ast.get_source_segment(SOURCE, FUNCS["profile"])
        self.assertIn('template_report_embed(guild, template,', scheduled)
        self.assertIn('template_report_embed(interaction.guild, template,', manual)
        self.assertIn("stamp_embed(embed, guild)", scheduled)
        self.assertIn("stamp_embed(embed, interaction.guild)", manual)
        self.assertIn('f"{interaction.guild.name} · El Heraldo"', profile)

    def test_dms_sent_through_user_or_dmchannel_keep_source_server(self):
        for name in ("send_recovery_dm", "send_test_removal_notice"):
            source = ast.get_source_segment(SOURCE, FUNCS[name])
            self.assertIn("stamp_embed(_content_embed(", source)
            self.assertIn("member.guild)", source)
            self.assertNotIn("await target.send(message,", source)

    def test_text_only_template_preserves_content_and_adds_lab_footer(self):
        from test_safety_regressions import b
        guild = server("Comunidad de texto", "https://example.org/text.png")
        payload = b.heraldo_template_payload(
            {"content": "Hola {servidor}"}, guild
        )
        content, result = b._embedify(payload.pop("content"), payload, guild, None)
        self.assertEqual(content, "Hola Comunidad de texto")
        self.assertEqual(len(result["embeds"]), 1)
        self.assertEqual(result["embeds"][0].footer.text, LAB_NAME)
        self.assertEqual(result["embeds"][0].footer.icon_url, "https://example.org/text.png")
        self.assertIsNone(result["embeds"][0].description)

    def test_media_only_delivery_has_branded_footer(self):
        from test_safety_regressions import b
        guild = server("Comunidad multimedia", "https://example.org/media.png")
        attachment = object()
        content, kw = b._embedify(None, {"files": [attachment]}, guild, None)
        self.assertIsNone(content)
        self.assertEqual(kw["files"], [attachment])
        self.assertEqual(kw["embed"].footer.text, LAB_NAME)
        self.assertEqual(kw["embed"].footer.icon_url, "https://example.org/media.png")

    def test_suggestion_direct_dms_and_edits_use_origin_guild(self):
        source = ast.get_source_segment(SOURCE, FUNCS["finalize_suggestion_decision"])
        created = SOURCE[SOURCE.index("class SuggestionModal("):SOURCE.index("class SuggestionReviewView(")]
        self.assertIn("embed=stamp_embed(embed.copy(), guild)", created)
        self.assertIn("embed=stamp_embed(result_embed.copy(), guild)", source)
        self.assertIn("embed=stamp_embed(final_embed.copy(), guild)", source)
        self.assertIn('interaction.extras["heraldo_source_guild"]', source)

    def test_no_lingering_hardcoded_brand_in_embed_footers(self):
        self.assertNotIn('set_footer(text="Paraíso Morboso 2026 · El Heraldo")', SOURCE)
        src = ast.get_source_segment(SOURCE, FUNCS["stamp_embed"])
        self.assertIn("server_footer_text(guild.name, detail)", src)
        self.assertIn('LAB_FOOTER_TEXT = "El Heraldo\'s Labs 🧪"', SOURCE)
        source = ast.get_source_segment(SOURCE, FUNCS["heraldo_template_payload"])
        self.assertIn('message_payload.validate({"embeds": prepared})', source)


if __name__ == "__main__":
    unittest.main()
