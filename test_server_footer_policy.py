"""Regresiones aisladas de identidad del servidor en footers (NH UX-03C).

Ejercitan funciones reales extraídas por AST sin importar bot.py ni iniciar Discord,
sin SQLite productiva, tokens, Gateway o conexiones de red.
"""
import ast
import copy
from pathlib import Path
from types import SimpleNamespace
import unittest

SOURCE = Path(__file__).with_name("bot.py").read_text(encoding="utf-8")
TREE = ast.parse(SOURCE)


class FakeEmbed:
    def __init__(self, description=None, *, text=None, icon_url=None):
        self.description = description
        self.footer = SimpleNamespace(text=text, icon_url=icon_url)

    def set_footer(self, *, text, icon_url=None):
        self.footer = SimpleNamespace(text=text, icon_url=icon_url)
        return self

    def copy(self):
        return copy.deepcopy(self)


class FakeGuild:
    def __init__(self, name, icon=None):
        self.name = name
        self.icon = SimpleNamespace(url=icon) if icon else None


class ServerFooterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        def render_vars(value, ctx, limit=None, plain=False):
            guild = ctx.guild
            result = value.replace("{servidor}", guild.name if guild else "")
            result = result.replace("{servericon}", guild.icon.url if guild and guild.icon else "")
            return result[:limit] if limit is not None else result

        def render_url_var(value, ctx):
            return render_vars(value, ctx)

        env = {
            "discord": SimpleNamespace(Embed=FakeEmbed, Guild=FakeGuild),
            "bot": SimpleNamespace(guilds=[], user=SimpleNamespace(name="El Heraldo")),
            "VarContext": lambda guild: SimpleNamespace(guild=guild),
            "render_vars": render_vars,
            "render_url_var": render_url_var,
            "GLOBAL_FOOTER_TEXT": "{servidor}",
            "GLOBAL_FOOTER_ICON": "{servericon}",
            "_MISSING": object(),
            "_content_embed": lambda content: FakeEmbed(description=content),
        }
        wanted = {"heraldo_footer", "stamp_embed", "_embedify"}
        nodes = [node for node in TREE.body if isinstance(node, ast.FunctionDef) and node.name in wanted]
        assert {node.name for node in nodes} == wanted
        exec(compile(ast.Module(body=nodes, type_ignores=[]), "<footer-functions>", "exec"), env)
        cls.env = env

    def test_no_custom_footer_receives_identity_and_icon(self):
        guild = FakeGuild("Servidor Alfa", "https://example.org/alfa.png")
        embed = FakeEmbed()
        self.env["stamp_embed"](embed, guild)
        self.assertEqual(embed.footer.text, guild.name)
        self.assertEqual(embed.footer.icon_url, guild.icon.url)

    def test_custom_footer_keeps_note_but_cannot_replace_icon(self):
        guild = FakeGuild("Servidor Beta", "https://example.org/beta.png")
        embed = FakeEmbed(text="Operación pendiente", icon_url="https://example.org/otro.png")
        self.env["stamp_embed"](embed, guild)
        self.assertIn(guild.name, embed.footer.text)
        self.assertIn("Operación pendiente", embed.footer.text)
        self.assertEqual(embed.footer.icon_url, guild.icon.url)

    def test_custom_variables_are_rendered_and_name_not_duplicated(self):
        guild = FakeGuild("Servidor Gamma", "https://example.org/g.png")
        embed = FakeEmbed(text="El Heraldo · {servidor}")
        self.env["stamp_embed"](embed, guild)
        self.env["stamp_embed"](embed, guild)
        self.assertEqual(embed.footer.text, "El Heraldo · Servidor Gamma")
        self.assertEqual(embed.footer.icon_url, guild.icon.url)

    def test_footer_never_exceeds_discord_limit(self):
        guild = FakeGuild("Servidor Delta", "https://example.org/d.png")
        embed = FakeEmbed(text="x" * 2048)
        self.env["stamp_embed"](embed, guild)
        self.assertLessEqual(len(embed.footer.text), 2048)
        self.assertTrue(embed.footer.text.startswith(guild.name))

    def test_server_without_icon_does_not_invent_one(self):
        guild = FakeGuild("Servidor sin icono")
        embed = FakeEmbed(text="Registro")
        self.env["stamp_embed"](embed, guild)
        self.assertIn(guild.name, embed.footer.text)
        self.assertIsNone(embed.footer.icon_url)

    def test_embedify_copies_reusable_embed_across_servers(self):
        first = FakeGuild("Servidor Uno", "https://example.org/uno.png")
        second = FakeGuild("Servidor Dos", "https://example.org/dos.png")
        shared = FakeEmbed(text="Aviso importante")
        _, one_kw = self.env["_embedify"](None, {"embed": shared}, first, None)
        _, two_kw = self.env["_embedify"](None, {"embed": shared}, second, None)
        self.assertIsNone(shared.footer.icon_url)
        self.assertEqual(shared.footer.text, "Aviso importante")
        self.assertEqual(one_kw["embed"].footer.icon_url, first.icon.url)
        self.assertEqual(two_kw["embed"].footer.icon_url, second.icon.url)
        self.assertNotIn(first.name, two_kw["embed"].footer.text)

    def test_embedify_multi_embed_and_plain_text(self):
        guild = FakeGuild("Servidor Multi", "https://example.org/multi.png")
        _, kw = self.env["_embedify"](None, {"embeds": [FakeEmbed(), FakeEmbed(text="Detalle")]}, guild, None)
        self.assertEqual(len(kw["embeds"]), 2)
        for embed in kw["embeds"]:
            self.assertEqual(embed.footer.icon_url, guild.icon.url)
            self.assertIn(guild.name, embed.footer.text)
        content, kw = self.env["_embedify"]("Mensaje simple", {}, guild, None)
        self.assertIsNone(content)
        self.assertEqual(kw["embed"].description, "Mensaje simple")
        self.assertIn(guild.name, kw["embed"].footer.text)

    def test_no_guild_does_not_attribute_other_guild_identity(self):
        self.env["bot"].guilds = [
            FakeGuild("Uno", "https://example.org/a.png"),
            FakeGuild("Dos", "https://example.org/b.png"),
        ]
        try:
            embed = FakeEmbed(text="Un aviso privado")
            self.env["stamp_embed"](embed, None)
            self.assertEqual(embed.footer.text, "Un aviso privado")
            self.assertIsNone(embed.footer.icon_url)
        finally:
            self.env["bot"].guilds = []

    def test_direct_user_dm_with_known_server_is_stamped(self):
        for call in (
            "owner.send(embed=stamp_embed(embed.copy(), guild))",
            "owner.send(embed=stamp_embed(embed.copy(), interaction.guild))",
            "reviewer.send(",
            "requester.send(embed=stamp_embed(result_embed.copy(), guild))",
            "message.edit(embed=stamp_embed(final_embed.copy(), guild)",
        ):
            self.assertIn(call, SOURCE)

    def test_transversal_hooks_and_editor_help_present(self):
        self.assertIn('wrap_positional(discord.abc.Messageable, "send"', SOURCE)
        self.assertIn('wrap_positional(discord.Webhook, "send"', SOURCE)
        self.assertIn('wrap_edit(discord.Message, "edit"', SOURCE)
        self.assertIn('discord.Interaction, "edit_original_response"', SOURCE)
        self.assertGreaterEqual(SOURCE.count('placeholder="Nombre: {servidor}; icono: {servericon} (automáticos)"'), 6)


if __name__ == "__main__":
    unittest.main()
