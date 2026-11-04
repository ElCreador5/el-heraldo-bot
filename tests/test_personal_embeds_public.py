"""Regresiones de permisos y persistencia de embeds personales (sin Gateway)."""
import os
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import discord
from personal_embeds import can_publish, entries, get_entry, store, remove, PersonalPanel, PublishChannelView


class PersonalEmbedsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = patch.dict(os.environ, {"DB_PATH": os.path.join(self.tmp.name, "lab.sqlite")})
        self.db.start()

    def tearDown(self):
        self.db.stop()
        self.tmp.cleanup()

    def test_names_are_scoped_to_owner_and_persist_between_connections(self):
        store(101, "Aviso", {"title": "Propietario 1"})
        store(202, "Aviso", {"title": "Propietario 2"})
        self.assertEqual(get_entry(101, "Aviso")["title"], "Propietario 1")
        self.assertEqual(get_entry(202, "Aviso")["title"], "Propietario 2")
        self.assertEqual(len(entries(101)), 1)
        remove(101, "Aviso")
        self.assertIsNone(get_entry(101, "Aviso"))
        self.assertEqual(get_entry(202, "Aviso")["title"], "Propietario 2")

    def test_publish_requires_both_users_permissions(self):
        def p(view=True, send=True, embed=True):
            return SimpleNamespace(view_channel=view, send_messages=send, embed_links=embed)

        member = SimpleNamespace(id=101)
        bot = SimpleNamespace(id=303)
        guild = SimpleNamespace(id=5, me=bot, get_member=lambda uid: member if uid == 101 else None)
        class FakeChannel:
            def __init__(self):
                self.guild = guild
                self.permissions_for = lambda who: p()

        channel = FakeChannel()
        interaction = SimpleNamespace(guild=guild, user=member)
        with patch('personal_embeds.discord.TextChannel', FakeChannel):
            self.assertTrue(can_publish(interaction, channel))
            channel.permissions_for = lambda who: p(send=False) if who is member else p()
            self.assertFalse(can_publish(interaction, channel))
            channel.permissions_for = lambda who: p() if who is member else p(embed=False)
            self.assertFalse(can_publish(interaction, channel))

    def test_publish_always_requires_confirmation(self):
        panel = SimpleNamespace(owner_id=101, guild_id=5)
        view = PublishChannelView(panel)
        self.assertTrue(view.confirm.disabled)
        self.assertIsNone(view.channel_id)

    def test_publication_embed_renders_image_author_and_title(self):
        from personal_publications import publication_embed
        member = SimpleNamespace(
            display_name="Miembro creador",
            display_avatar=SimpleNamespace(url="https://example.com/avatar.png"),
        )
        stamp = lambda embed, guild: embed.set_footer(text="El Heraldo") or embed
        text_payload = {
            "kind": "text", "text": "Hola",
            "image_url": "https://example.com/imagen.png",
        }
        text_embed = publication_embed(text_payload, stamp, None, member, "Mi anuncio", None)
        self.assertEqual(text_embed.title, "Mi anuncio")
        self.assertEqual(text_embed.author.name, "Miembro creador")
        self.assertEqual(text_embed.image.url, text_payload["image_url"])
        self.assertEqual(text_embed.footer.text, "El Heraldo")

        visual = {"title": "Título original", "image_url": "https://example.com/foto.png"}
        def renderer(data, stamp_fn, guild):
            embed = discord.Embed(title=data["title"])
            embed.set_image(url=data["image_url"])
            return stamp_fn(embed, guild)
        rendered = publication_embed(visual, stamp, None, member, "Nombre interno", renderer)
        self.assertEqual(rendered.title, "Título original")
        self.assertEqual(rendered.author.name, "Miembro creador")
        self.assertEqual(rendered.image.url, visual["image_url"])

    def test_no_personal_scheduler(self):
        from pathlib import Path
        source = (Path(__file__).resolve().parents[1] / "personal_embeds.py").read_text(encoding="utf-8")
        self.assertNotIn("create_task(", source)
        self.assertNotIn("schedule_job(", source)
        self.assertIn("allowed_mentions=discord.AllowedMentions.none()", source)


if __name__ == "__main__":
    unittest.main()
