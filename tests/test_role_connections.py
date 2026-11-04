"""Regresiones del motor Role Connections sin Discord Gateway."""
import asyncio
from contextlib import closing
import os
import sqlite3
import tempfile
import unittest
from types import SimpleNamespace

import role_connections as rc


class FakeRole:
    def __init__(self, guild, role_id, *, privileged=False, managed=False):
        self.guild, self.id, self.managed = guild, role_id, managed
        self.permissions = SimpleNamespace(**{
            name: bool(privileged and name == "administrator") for name in rc.PRIVILEGED
        })
        self.name = f"Rol-{role_id}"

    def __ge__(self, other):
        return self.id >= other.id

    def is_default(self):
        return self.id == 0


class FakeMember:
    bot = False

    def __init__(self, guild, held=()):
        self.guild = guild
        self.id = 1000
        self.roles = [guild.get_role(x) for x in held]
        guild.members[self.id] = self

    async def add_roles(self, role, reason=None):
        self.roles.append(role)

    async def remove_roles(self, role, reason=None):
        self.roles.remove(role)


class FakeGuild:
    def __init__(self, guild_id=10):
        self.id, self.members = guild_id, {}
        self.roles = {i: FakeRole(self, i) for i in range(1, 101)}
        self.roles[90] = FakeRole(self, 90, privileged=True)
        self.me = SimpleNamespace(
            guild_permissions=SimpleNamespace(manage_roles=True),
            top_role=FakeRole(self, 200),
        )

    def get_role(self, role_id):
        return self.roles.get(role_id)

    def get_member(self, member_id):
        return self.members.get(member_id)

    async def fetch_members(self, limit=None):
        for member in self.members.values():
            yield member


def group(mode, *conditions):
    return {"mode": mode, "conditions": [
        {"op": op, "role_id": role_id} for op, role_id in conditions
    ]}


class ConnectionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        path = os.path.join(self.tmp.name, "roles.db")
        self.connect = lambda: sqlite3.connect(path, isolation_level=None, timeout=2)
        self.guild = FakeGuild()
        rc.ensure_schema(self.connect)

    def tearDown(self):
        self.tmp.cleanup()

    def save(self, target, groups, mode="all", **kwargs):
        return rc.save_rule(
            self.connect, self.guild, name=f"Grupo {target}", target_role_id=target,
            groups=groups, groups_mode=mode, **kwargs
        )

    def test_and_requires_both_and_removes_when_role_lost(self):
        self.save(20, [group("all", ("has", 1), ("has", 2))])
        member = FakeMember(self.guild, held=[1])
        self.assertEqual(asyncio.run(rc.reconcile_member(member, connect=self.connect)), (0, 0))
        member.roles.append(self.guild.get_role(2))
        self.assertEqual(asyncio.run(rc.reconcile_member(member, connect=self.connect)), (1, 0))
        self.assertIn(20, {r.id for r in member.roles})
        member.roles.remove(self.guild.get_role(1))
        self.assertEqual(asyncio.run(rc.reconcile_member(member, connect=self.connect)), (0, 1))
        self.assertNotIn(20, {r.id for r in member.roles})

    def test_groups_and_or_and_lacks(self):
        self.save(21, [
            group("all", ("has", 1), ("lacks", 2)),
            group("all", ("has", 3), ("has", 4)),
        ], mode="any")
        member = FakeMember(self.guild, held=[1])
        self.assertTrue(rc.matches(rc.list_rules(self.connect, self.guild.id)[0], {1}))
        self.assertEqual(asyncio.run(rc.reconcile_member(member, connect=self.connect)), (1, 0))
        member.roles.extend([self.guild.get_role(2), self.guild.get_role(3)])
        self.assertEqual(asyncio.run(rc.reconcile_member(member, connect=self.connect)), (0, 1))
        member.roles.append(self.guild.get_role(4))
        self.assertEqual(asyncio.run(rc.reconcile_member(member, connect=self.connect)), (1, 0))

    def test_no_unsafe_privileged_protected_or_cycles(self):
        with self.assertRaisesRegex(ValueError, "unsafe_target"):
            self.save(90, [group("all", ("has", 1))])
        with self.assertRaisesRegex(ValueError, "unsafe_target"):
            self.save(20, [group("all", ("has", 1))], protected_ids={20})
        with self.assertRaisesRegex(ValueError, "circular_rule"):
            self.save(20, [group("all", ("has", 20))])
        with self.assertRaisesRegex(ValueError, "contradictory_condition"):
            self.save(20, [group("all", ("has", 1), ("lacks", 1))])
        self.save(20, [group("all", ("has", 21))])
        with self.assertRaisesRegex(ValueError, "circular_rule"):
            self.save(21, [group("all", ("has", 20))])

    def test_rule_dependent_on_another_role(self):
        self.save(20, [group("all", ("has", 1))])
        self.save(21, [group("all", ("has", 20))])
        member = FakeMember(self.guild, held=[1])
        self.assertEqual(asyncio.run(rc.reconcile_member(member, connect=self.connect)), (2, 0))

    def test_revision_and_guild_separation(self):
        one = self.save(20, [group("all", ("has", 1))])
        other_guild = FakeGuild(11)
        self.assertEqual(rc.list_rules(self.connect, other_guild.id), [])
        with self.assertRaisesRegex(ValueError, "stale_rule"):
            rc.save_rule(
                self.connect, self.guild, name="Edited", target_role_id=20,
                groups=[group("all", ("has", 2))], rule_id=one.rule_id,
                expected_revision="stale"
            )
        self.assertFalse(rc.delete_rule(self.connect, self.guild.id, one.rule_id, "stale"))
        self.assertTrue(rc.delete_rule(self.connect, self.guild.id, one.rule_id, one.revision))
        self.assertEqual(rc.list_rules(self.connect, self.guild.id), [])

    def test_blocked_user_does_not_receive_roles(self):
        self.save(20, [group("all", ("has", 1))])
        member = FakeMember(self.guild, held=[1])
        self.assertEqual(asyncio.run(rc.reconcile_member(
            member, connect=self.connect, blocked=lambda _: True,
        )), (0, 0))

    def test_enzonic_schema_allowlist_matches_sqlite(self):
        with closing(self.connect()) as db:
            row = db.execute(
                "SELECT sql FROM sqlite_master WHERE name='heraldo_role_connections'"
            ).fetchone()
        self.assertEqual(
            row[0], rc.SCHEMA.strip().replace("IF NOT EXISTS ", "", 1)
        )

    def test_group_limits_and_manual_sync(self):
        with self.assertRaisesRegex(ValueError, "invalid_conditions"):
            self.save(20, [group("all")])
        self.save(20, [group("all", ("has", 1))])
        FakeMember(self.guild, held=[1])
        checked, added, removed, exceeded = asyncio.run(
            rc.synchronize(self.guild, connect=self.connect, limit=1000)
        )
        self.assertEqual((checked, added, removed, exceeded), (1, 1, 0, False))


if __name__ == "__main__":
    unittest.main()
