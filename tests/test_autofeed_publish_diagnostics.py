"""Pruebas sin conexión: diagnóstico exacto antes de publicar anuncios."""
import ast
from pathlib import Path
from types import SimpleNamespace as NS
import unittest


SOURCE = (Path(__file__).resolve().parents[1] / "autofeed_setup.py").read_text(encoding="utf-8")
TREE = ast.parse(SOURCE)
FUNC = next(x for x in TREE.body if isinstance(x, ast.FunctionDef)
            and x.name == "announcement_access_issue")
ROLES = ast.parse((Path(__file__).resolve().parents[1] / "message_autofeeds.py").read_text(encoding="utf-8"))
MENTION_FN = next(x for x in ROLES.body if isinstance(x, ast.FunctionDef)
                  and x.name == "can_mention_role")


class FakeMember:
    def __init__(self, moderator=True):
        self.moderator = moderator


class FakeTextChannel:
    def __init__(self):
        self.id = 100
        self.guild = NS(id=90)
        self.user_perms = NS(view_channel=True, send_messages=True)
        self.bot_perms = NS(view_channel=True, send_messages=True, embed_links=True,
                            mention_everyone=False)

    def permissions_for(self, member):
        return self.bot_perms if member == "bot" else self.user_perms


class AccessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ns = {
            "discord": NS(TextChannel=FakeTextChannel, Member=FakeMember),
            "feeds": NS(
                can_schedule=lambda member: member.moderator,
                is_ready=lambda interaction, host, channel, role: True,
            ),
        }
        mention_code = ast.fix_missing_locations(ast.Module(body=[MENTION_FN], type_ignores=[]))
        exec(compile(mention_code, "message_autofeeds.py", "exec"), cls.ns)
        cls.ns["feeds"].can_mention_role = cls.ns["can_mention_role"]
        code = ast.fix_missing_locations(ast.Module(body=[FUNC], type_ignores=[]))
        exec(compile(code, "autofeed_setup.py", "exec"), cls.ns)
        cls.validate = staticmethod(cls.ns["announcement_access_issue"])

    def setUp(self):
        self.channel = FakeTextChannel()
        self.member = FakeMember()
        self.role = NS(id=200, guild=NS(id=90), mentionable=True)
        self.guild = NS(
            id=90, me="bot",
            get_channel=lambda cid: self.channel if cid == 100 else None,
            get_role=lambda rid: self.role if rid == 200 else None,
        )
        self.interaction = NS(guild=self.guild, user=self.member)

    def check(self, channel_id=100, role_id=None):
        return self.validate(self.interaction, {}, channel_id, role_id)

    def test_valid_channel_and_no_optional_role(self):
        self.assertIsNone(self.check())
        self.assertIsNone(self.check(role_id=200))

    def test_missing_channel_and_missing_member_rights(self):
        self.assertEqual(self.check(999), "channel_missing")
        self.member.moderator = False
        self.assertEqual(self.check(), "moderator_required")
        self.member.moderator = True
        self.channel.user_perms.send_messages = False
        self.assertEqual(self.check(), "author_no_channel")

    def test_distinguishes_bot_permissions(self):
        for name, expected in (
            ("view_channel", "bot_no_view"),
            ("send_messages", "bot_no_send"),
            ("embed_links", "bot_no_embed"),
        ):
            with self.subTest(name=name):
                setattr(self.channel.bot_perms, name, False)
                self.assertEqual(self.check(), expected)
                setattr(self.channel.bot_perms, name, True)

    def test_role_missing_or_unmentionable(self):
        self.assertEqual(self.check(role_id=999), "role_missing")
        self.role.mentionable = False
        self.assertEqual(self.check(role_id=200), "role_unmentionable")
        self.channel.bot_perms.mention_everyone = True
        self.assertIsNone(self.check(role_id=200))
        self.channel.bot_perms.mention_everyone = False
        self.assertEqual(self.check(role_id=200), "role_unmentionable")

    def test_final_guard_is_not_bypassed(self):
        previous = self.ns["feeds"].is_ready
        try:
            self.ns["feeds"].is_ready = lambda *_: False
            self.assertEqual(self.check(), "unavailable")
        finally:
            self.ns["feeds"].is_ready = previous

    def test_editor_uses_specific_errors_without_saving(self):
        source = ast.unparse(next(x for x in TREE.body if isinstance(x, ast.ClassDef)
                                  and x.name == "AutofeedEditorView"))
        self.assertIn("announcement_access_issue(", source)
        self.assertIn('raise ValueError("embed_invalid")', source)
        self.assertIn('raise ValueError("references_invalid")', source)
        self.assertIn('t(str(exc)) if str(exc) in LANG', source)


if __name__ == "__main__":
    unittest.main()
