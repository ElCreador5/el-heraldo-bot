"""Regresión estática del registro y visibilidad de slash commands."""
import ast
from pathlib import Path
import unittest


class PublicCommandsPolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.code = (Path(__file__).resolve().parents[1] / "bot.py").read_text(encoding="utf-8")
        cls.tree = ast.parse(cls.code)

    def test_single_public_personal_embed_installation(self):
        source = self.code
        self.assertIn('bot.tree.remove_command("embed")', source)
        self.assertIn('personal_embeds.install({"bot": bot, "stamp_embed": stamp_embed})', source)
        self.assertIn('personal_embed_registration_not_unique', source)

    def test_private_commands_not_public_in_policy(self):
        source = self.code
        self.assertIn('public = {"embed", "profile"}', source)
        self.assertIn('discord.Permissions(**{permission: True})', source)
        self.assertIn('"ban": "ban_members"', source)
        self.assertIn('"kick": "kick_members"', source)
        self.assertIn('"purge": "manage_messages"', source)
        self.assertIn('"fusionar_canales": "manage_channels"', source)
        self.assertIn('_heraldo_apply_command_visibility()', source)
        self.assertLess(source.index('def _heraldo_apply_command_visibility'), source.index('# El trabajador de mensajes'))

    def test_personal_embed_is_private_and_owner_bound(self):
        code = (Path(__file__).resolve().parents[1] / "personal_embeds.py").read_text(encoding="utf-8")
        self.assertIn('ephemeral=True', code)
        self.assertIn('interaction.user.id != self.owner_id', code)
        self.assertIn('allowed_mentions=discord.AllowedMentions.none()', code)


if __name__ == "__main__":
    unittest.main()
