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

    def test_manual_sync_reports_incremental_role_counts(self):
        self.save(20, [group("all", ("has", 1))])
        FakeMember(self.guild, held=[1])
        updates = []

        async def record(checked, added, removed):
            updates.append((checked, added, removed))

        result = asyncio.run(rc.synchronize(
            self.guild, connect=self.connect, progress=record
        ))
        self.assertEqual(result, (1, 1, 0, False))
        self.assertEqual(updates, [(1, 1, 0)])

    def test_manual_sync_tracks_roles_rejected_by_discord(self):
        self.save(20, [group("all", ("has", 1))])
        member = FakeMember(self.guild, held=[1])
        failures = []

        async def reject(*args, **kwargs):
            raise PermissionError("simulated Discord role denial")

        async def on_failure():
            failures.append(True)

        member.add_roles = reject
        result = asyncio.run(rc.synchronize(
            self.guild, connect=self.connect, on_failure=on_failure
        ))
        self.assertEqual(result, (1, 0, 0, False))
        self.assertEqual(len(failures), 1)

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
        with self.assertRaisesRegex(ValueError, "unsafe_privileged"):
            self.save(90, [group("all", ("has", 1))])
        with self.assertRaisesRegex(ValueError, "unsafe_protected"):
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


    def test_unsafe_target_diagnostics_are_specific(self):
        role = self.guild.get_role(20)
        self.assertIsNone(rc.target_safety_reason(self.guild, role))
        self.assertEqual(
            rc.target_safety_reason(self.guild, role, protected_ids={20}),
            "unsafe_protected"
        )
        self.assertEqual(
            rc.target_safety_reason(self.guild, self.guild.get_role(90)),
            "unsafe_privileged"
        )
        self.assertEqual(
            rc.target_safety_reason(self.guild, None), "missing_role"
        )
        role.managed = True
        self.assertEqual(rc.target_safety_reason(self.guild, role), "unsafe_managed")
        role.managed = False
        self.guild.me.top_role = self.guild.get_role(10)
        self.assertEqual(rc.target_safety_reason(self.guild, role), "unsafe_hierarchy")
        self.guild.me.top_role = FakeRole(self.guild, 200)
        self.guild.me.guild_permissions.manage_roles = False
        self.assertEqual(
            rc.target_safety_reason(self.guild, role), "unsafe_bot_permissions"
        )
        self.guild.me.guild_permissions.manage_roles = True
        self.guild.me = None
        self.assertEqual(rc.target_safety_reason(self.guild, role), "unsafe_bot_member")

    def test_unsafe_target_does_not_persist_or_override_existing_rule(self):
        rule = self.save(20, [group("all", ("has", 1))])
        with self.assertRaisesRegex(ValueError, "unsafe_protected"):
            self.save(
                20, [group("all", ("has", 2))], rule_id=rule.rule_id,
                expected_revision=rule.revision, protected_ids={20}
            )
        current = rc.get_rule(self.connect, self.guild.id, rule.rule_id)
        self.assertEqual(current.revision, rule.revision)
        self.assertEqual(current.groups[0]["conditions"][0]["role_id"], 1)


    def test_advanced_xor_exactly_one_and_not_negated_all(self):
        xor_rule = self.save(25, [group("xor", ("has", 1), ("has", 2), ("has", 3))])
        self.assertFalse(rc.matches(xor_rule, set()))
        self.assertTrue(rc.matches(xor_rule, {1}))
        self.assertTrue(rc.matches(xor_rule, {3}))
        self.assertFalse(rc.matches(xor_rule, {1, 2}))
        self.assertFalse(rc.matches(xor_rule, {1, 2, 3}))
        not_rule = self.save(26, [group("not", ("has", 1), ("has", 2))])
        self.assertTrue(rc.matches(not_rule, set()))
        self.assertTrue(rc.matches(not_rule, {1}))
        self.assertFalse(rc.matches(not_rule, {1, 2}))

    def test_advanced_minimum_validation_persistence_and_reconcile(self):
        grp = group("at_least", ("has", 1), ("has", 2), ("has", 3))
        grp["min_required"] = 2
        rule = self.save(27, [grp])
        loaded = rc.get_rule(self.connect, self.guild.id, rule.rule_id)
        self.assertEqual(loaded.groups[0]["min_required"], 2)
        self.assertFalse(rc.matches(loaded, {1}))
        self.assertTrue(rc.matches(loaded, {1, 2}))
        self.assertTrue(rc.matches(loaded, {1, 2, 3}))
        member = FakeMember(self.guild, held=[1])
        self.assertEqual(asyncio.run(rc.reconcile_member(
            member, connect=self.connect
        )), (0, 0))
        member.roles.append(self.guild.get_role(2))
        self.assertEqual(asyncio.run(rc.reconcile_member(
            member, connect=self.connect
        )), (1, 0))
        member.roles.remove(self.guild.get_role(1))
        self.assertEqual(asyncio.run(rc.reconcile_member(
            member, connect=self.connect
        )), (0, 1))

        for bad in (None, 0, -1, 4, True, 1.5, "2"):
            invalid = dict(grp, min_required=bad)
            with self.subTest(bad=bad), self.assertRaisesRegex(
                ValueError, "invalid_minimum"
            ):
                self.save(28, [invalid])
        with self.assertRaisesRegex(ValueError, "invalid_conditions"):
            self.save(28, [{"mode": "unknown", "conditions": grp["conditions"]}])

    def test_backward_compatibility_and_advanced_group_combination(self):
        self.assertEqual(rc.SCHEMA.count("groups_json TEXT NOT NULL"), 1)
        base = self.save(30, [group("all", ("has", 1), ("lacks", 2))])
        original = rc.get_rule(self.connect, self.guild.id, base.rule_id)
        self.assertEqual(original.groups[0], {
            "mode": "all", "conditions": [
                {"op": "has", "role_id": 1},
                {"op": "lacks", "role_id": 2},
            ]
        })
        xor_grp = group("xor", ("has", 1), ("has", 2))
        min_grp = group("at_least", ("has", 3), ("has", 4))
        min_grp["min_required"] = 2
        combined = self.save(31, [xor_grp, min_grp], mode="any")
        self.assertTrue(rc.matches(combined, {1}))
        self.assertTrue(rc.matches(combined, {3, 4}))
        self.assertFalse(rc.matches(combined, {1, 2, 3}))
        self.assertFalse(rc.matches(combined, set()))



if __name__ == "__main__":
    unittest.main()
