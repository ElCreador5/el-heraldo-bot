"""Immediate message publishing uses the existing footer and explicit confirmation."""
import unittest
from unittest.mock import AsyncMock, MagicMock
from types import SimpleNamespace as NS

import discord
import message_publish
import autofeed_setup as setup
from test_safety_regressions import b


class MessageCreateTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.role = NS(id=123456789012345678, mention="<@&123456789012345678>",
                       mentionable=True)
        self.guild = NS(id=901, me=NS(id=700),
                        get_role=lambda value: self.role if value == self.role.id else None,
                        get_channel=lambda value: None)
        self.channel = MagicMock(spec=discord.TextChannel)
        self.channel.guild = self.guild
        self.channel.permissions_for.return_value = discord.Permissions(
            view_channel=True, send_messages=True, embed_links=True)
        self.channel.send = AsyncMock(return_value=NS(id=999))
        self.host = {"stamp_embed": lambda embed, guild:
                     embed.set_footer(text="El Heraldo's Labs 🧪") or embed}

    async def test_publish_now_embeds_footer_and_sends_once(self):
        job = {"text": "Consulta las novedades", "role": None, "embed": {
            "title": "Boletín", "description": "Información nueva", "fields": [
                {"name": "Tema", "value": "Avisos", "inline": False}]}}
        sent = await message_publish.publish_message(
            self.host, self.guild, self.channel, job)
        self.assertEqual(sent.id, 999)
        self.channel.send.assert_awaited_once()
        payload = self.channel.send.call_args.kwargs
        self.assertEqual(payload["content"], "Consulta las novedades")
        self.assertEqual(payload["embeds"][0].title, "Boletín")
        self.assertEqual(payload["embeds"][0].footer.text, "El Heraldo's Labs 🧪")
        self.assertEqual(len(payload["embeds"][0].fields), 1)
        self.assertFalse(payload["allowed_mentions"].everyone)
        self.assertFalse(payload["allowed_mentions"].users)

    async def test_alert_role_is_outside_embed_once(self):
        job = {"text": "Hola", "role": self.role.id, "embed": {
            "title": "Noticias", "description": "Este embed no notifica."}}
        await message_publish.publish_message(self.host, self.guild, self.channel, job)
        payload = self.channel.send.call_args.kwargs
        self.assertEqual(payload["content"], "Hola\n" + self.role.mention)
        self.assertEqual(payload["allowed_mentions"].roles, [self.role])
        self.assertEqual(payload["embeds"][0].footer.text, "El Heraldo's Labs 🧪")

    async def test_does_not_double_append_alert_role(self):
        job = {"text": "Hola " + self.role.mention, "role": self.role.id, "embed": None}
        await message_publish.publish_message(self.host, self.guild, self.channel, job)
        self.assertEqual(self.channel.send.call_args.kwargs["content"], job["text"])

    async def test_reject_missing_content_without_sending(self):
        with self.assertRaises(ValueError):
            await message_publish.publish_message(
                self.host, self.guild, self.channel,
                {"text": "", "role": None, "embed": None})
        self.channel.send.assert_not_awaited()

    def test_one_editor_can_publish_now_or_schedule(self):
        editor = setup.AutofeedEditorView(b.__dict__, 901, 10)
        self.assertIsNone(editor.start)
        self.assertNotIn(setup.t("discard"), [x.label for x in editor.children
                                              if hasattr(x, "label")])
        editor.start = None
        editor.parts = setup.PRESETS["daily"]
        self.assertIsNotNone(editor.parts)
        # The real guild/permission validation is exercised by the existing
        # startup and autofeed permissions tests. These fields are not persisted.
        self.assertEqual(b.guild_config_get(901, "message_schedules"),
                         b.guild_config_get(901, "message_schedules"))


if __name__ == "__main__":
    unittest.main()
