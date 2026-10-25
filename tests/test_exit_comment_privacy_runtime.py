"""Pruebas ejecutables de privacidad y auditoría, sin iniciar Discord."""
from __future__ import annotations
from i18n_source_helpers import source_text as _source_text

import ast
import asyncio
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace as NS

TEXT = _source_text(Path(__file__).resolve().parents[1] / 'bot.py', encoding='utf-8')
TREE = ast.parse(TEXT)


def extract(name, env):
    fn = next(node for node in TREE.body if isinstance(node, ast.AsyncFunctionDef if name == "exit_comment_audit_safe" else ast.FunctionDef) and node.name == name)
    module = ast.Module(body=[
        ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0),
        fn,
    ], type_ignores=[])
    scope = dict(env)
    exec(compile(ast.fix_missing_locations(module), "<heraldo-isolated>", "exec"), scope)
    return scope[name]


class FakeForbidden(Exception):
    pass


class FakeHttp(Exception):
    pass


class FakeRole:
    def __init__(self, *, default=False, staff=False):
        self.default = default
        self.permissions = NS(manage_messages=staff)

    def is_default(self):
        return self.default


class FakeMember:
    def __init__(self, *, staff=False):
        self.staff = staff


class PrivacyChecks(unittest.TestCase):
    def setup_channel(self, extra=None):
        everyone = FakeRole(default=True)
        moderator = FakeRole(staff=True)
        guild = NS(
            default_role=everyone,
            roles=[everyone, moderator],
            me=FakeMember(staff=True),
        )
        permissions = NS(
            view_channel=True, send_messages=True,
            embed_links=True, read_message_history=True,
        )

        class Channel:
            def permissions_for(self, target):
                return NS(view_channel=False) if target is everyone else permissions

        channel = Channel()
        channel.guild = guild
        channel.overwrites = extra or {}
        return channel

    def checker(self):
        return extract("exit_comment_private", {
            "discord": NS(Role=FakeRole, Member=FakeMember),
            "verification_is_exempt": lambda target: target.staff,
        })

    def test_moderator_only_channel_is_allowed(self):
        self.assertTrue(self.checker()(self.setup_channel()))

    def test_member_specific_access_is_rejected(self):
        user = FakeMember(staff=False)
        self.assertFalse(self.checker()(self.setup_channel({
            user: NS(view_channel=True),
        })))

    def test_unknown_direct_user_overwrite_is_rejected(self):
        unresolved = object()
        self.assertFalse(self.checker()(self.setup_channel({
            unresolved: NS(view_channel=True),
        })))

    def test_staff_specific_overwrite_is_allowed(self):
        mod = FakeMember(staff=True)
        self.assertTrue(self.checker()(self.setup_channel({
            mod: NS(view_channel=True),
        })))


class AuditChecks(unittest.TestCase):
    def checker(self):
        async def no_delay(_seconds):
            return None

        return extract("exit_comment_audit_safe", {
            "discord": NS(
                AuditLogAction=NS(kick="kick", ban="ban"),
                Forbidden=FakeForbidden, HTTPException=FakeHttp,
                Member=FakeMember,
            ),
            "asyncio": NS(sleep=no_delay),
            "datetime": datetime, "timezone": timezone, "timedelta": timedelta,
        })

    def member(self, entries=(), error=None, audit_permission=True):
        guild = NS(
            me=NS(guild_permissions=NS(view_audit_log=audit_permission)),
        )

        async def audit_logs(*, limit, action, after):
            if error:
                raise error()
            for event, user_id, timestamp in entries:
                if event == action:
                    yield NS(target=NS(id=user_id), created_at=timestamp)

        guild.audit_logs = audit_logs
        return NS(guild=guild, id=23)

    def test_confirmed_kick_prevents_feedback(self):
        member = self.member([("kick",23,datetime.now(timezone.utc))])
        self.assertFalse(asyncio.run(self.checker()(member)))

    def test_confirmed_ban_prevents_feedback(self):
        member = self.member([("ban",23,datetime.now(timezone.utc))])
        self.assertFalse(asyncio.run(self.checker()(member)))

    def test_audit_api_failure_prevents_feedback(self):
        self.assertFalse(asyncio.run(self.checker()(self.member(error=FakeHttp))))
        self.assertFalse(asyncio.run(self.checker()(self.member(error=FakeForbidden))))
        self.assertFalse(asyncio.run(self.checker()(self.member(audit_permission=False))))

    def test_absence_of_recent_sanction_allows_consideration(self):
        member = self.member([("kick",22,datetime.now(timezone.utc))])
        self.assertTrue(asyncio.run(self.checker()(member)))


if __name__ == "__main__":
    unittest.main()
