"""Regresiones de reingreso voluntario sin conexiones reales a Discord."""
import asyncio
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
import sqlite3
from types import SimpleNamespace as NS
import unittest

from member_rejoin_restore import capture_departure, restore_join, saved_role, forget


class Role:
    managed = False
    def __init__(self, id, *, admin=False):
        self.id = id
        self.permissions = NS(
            administrator=admin, manage_guild=False, manage_roles=False,
            ban_members=False, kick_members=False, moderate_members=False)
    def is_default(self): return False
    def __ge__(self, other): return self.id >= other.id


class Member:
    bot = False
    def __init__(self, guild, roles, member_id=17):
        self.guild = guild
        self.roles = roles
        self.id = member_id
        self.added = []
    async def add_roles(self, role, **kwargs):
        self.added.append(role.id)
        self.roles.append(role)
    async def remove_roles(self, role, **kwargs):
        self.roles.remove(role)


class RejoinTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = str(Path(self.tmp.name) / "test.db")
        self.connect = lambda: sqlite3.connect(self.path, isolation_level=None)
        self.role = Role(10)
        self.provisional = Role(11)
        self.unsafe = Role(12, admin=True)
        self.me = NS(top_role=Role(100), guild_permissions=NS(
            manage_roles=True, view_audit_log=True))
        self.members = {}
        self.entries = []
        self.guild = NS(id=4, me=self.me, get_role=lambda id: {
            10:self.role, 11:self.provisional, 12:self.unsafe}.get(id),
            get_member=lambda id: self.members.get(id))
        async def audit_logs(*, limit, action, after):
            for item in self.entries:
                if item.action == action:
                    yield item
        self.guild.audit_logs = audit_logs
        self.audit = NS(kick="kick", ban="ban")

    async def departure(self, member):
        # Avoid a real delay in the tests with a small isolated patch.
        from unittest.mock import patch
        async def no_delay(_): pass
        with patch("member_rejoin_restore.asyncio.sleep", no_delay):
            await capture_departure(
                member, connect=self.connect, enabled=lambda gid:True,
                personality_ids=lambda gid:{10,12},
                verify_role_id=lambda gid:11, is_verified=lambda m: True,
                audit_action=self.audit)

    async def returning(self, member):
        from unittest.mock import patch
        async def no_delay(_): pass
        self.members[member.id] = member
        with patch("member_rejoin_restore.asyncio.sleep", no_delay):
            return await restore_join(
                member, connect=self.connect, enabled=lambda gid:True,
                personality_ids=lambda gid:{10,12},
                verify_role_id=lambda gid:11, sin_role_id=lambda gid:0)

    async def test_voluntary_return_restores_personality_only_once(self):
        original = Member(self.guild, [self.role])
        await self.departure(original)
        self.assertEqual(saved_role(self.connect, 4, 17), 10)
        returning = Member(self.guild, [])
        self.assertTrue(await self.returning(returning))
        self.assertEqual(returning.added, [10])
        self.assertFalse(await self.returning(returning))

    async def test_kick_never_creates_snapshot(self):
        member=Member(self.guild,[self.role])
        self.entries=[NS(action="kick",target=NS(id=17),
                         created_at=datetime.now(timezone.utc))]
        await self.departure(member)
        self.assertIsNone(saved_role(self.connect,4,17))

    async def test_privileged_role_never_restored(self):
        await self.departure(Member(self.guild,[self.unsafe]))
        self.assertIsNone(saved_role(self.connect,4,17))

    async def test_capture_requires_audit_permission(self):
        self.me.guild_permissions.view_audit_log=False
        await self.departure(Member(self.guild,[self.role]))
        self.assertIsNone(saved_role(self.connect,4,17))

    async def test_previous_snapshot_is_cleared_on_next_departure(self):
        await self.departure(Member(self.guild,[self.role]))
        await self.departure(Member(self.guild,[]))
        self.assertIsNone(saved_role(self.connect,4,17))


if __name__ == "__main__":
    unittest.main()
