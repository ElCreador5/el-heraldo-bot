"""Contrato de {#ID_DEL_CANAL} en variables, anuncios y embeds.

Pruebas sin Discord Gateway ni datos del servidor.
"""
import ast
from pathlib import Path
from types import SimpleNamespace
import unittest

from channel_mentions import channel_mentions, embed_channel_mentions


ROOT = Path(__file__).resolve().parents[1]


def code(path):
    return (ROOT / path).read_text(encoding="utf-8")


class FakeGuild:
    id = 111

    def __init__(self):
        self.channels = {
            123456789012345678: SimpleNamespace(
                id=123456789012345678, guild=SimpleNamespace(id=111)),
            234567890123456789: SimpleNamespace(
                id=234567890123456789, guild=SimpleNamespace(id=111)),
        }

    def get_channel_or_thread(self, channel_id):
        return self.channels.get(channel_id)


class ChannelPlaceholderTests(unittest.TestCase):
    def setUp(self):
        self.guild = FakeGuild()

    def test_converts_existing_channels_by_id(self):
        value = "Mira {#123456789012345678} y {#234567890123456789}."
        self.assertEqual(
            channel_mentions(value, self.guild),
            "Mira <#123456789012345678> y <#234567890123456789>.")

    def test_keeps_unknown_cross_server_or_bad_syntax_unchanged(self):
        value = "{#999999999999999999} {#reglas} {#0} <#123456789012345678>"
        self.assertEqual(channel_mentions(value, self.guild), value)
        self.assertEqual(channel_mentions(value, None), value)

    def test_no_mutation_of_saved_embed_draft(self):
        original = {
            "title": "Consulta {#123456789012345678}",
            "description": "Visita {#234567890123456789}",
            "author": {"name": "Desde {#123456789012345678}"},
            "fields": [{"name": "Canal", "value": "{#123456789012345678}"}],
        }
        converted = embed_channel_mentions(original, self.guild)
        self.assertEqual(converted["description"], "Visita <#234567890123456789>")
        self.assertEqual(converted["fields"][0]["value"], "<#123456789012345678>")
        self.assertEqual(converted["author"]["name"], "Desde <#123456789012345678>")
        self.assertIn("{#123456789012345678}", original["title"])

    def test_announcement_renders_mention_at_delivery_and_preview(self):
        automation = code("message_automation.py")
        builder = code("autofeed_embed_builder.py")
        self.assertIn("channel_mentions(job.get('text') or None, guild)", automation)
        self.assertIn("embed_channel_mentions(data, guild)", builder)
        self.assertIn('f"{{#{channel.id}}}"', builder)
        self.assertIn("embed_channel_mentions", builder)

    def test_autofeed_validates_brace_ids_as_channel_references(self):
        af = code("message_autofeeds.py")
        self.assertIn('channel_ids.update(', af)
        self.assertIn(r'\\{#([1-9]\\d{0,19})\\}', af)

    def test_variable_autocomplete_uses_id(self):
        bot = code("bot.py")
        tree = ast.parse(bot)
        fn = next(x for x in tree.body if isinstance(x, ast.FunctionDef)
                  and x.name == "variable_suggestions")
        rendered = ast.unparse(fn)
        self.assertIn('c.id', rendered)
        self.assertIn('prefix', rendered)


if __name__ == "__main__":
    unittest.main()
