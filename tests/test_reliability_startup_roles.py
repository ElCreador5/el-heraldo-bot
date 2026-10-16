"""Fiabilidad: recuperación tras reinicios, lectura SQLite y permisos revocados."""
from __future__ import annotations
import ast
import asyncio
import sqlite3
import unittest
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import AsyncMock, MagicMock

SOURCE = (Path(__file__).resolve().parents[1] / "bot.py").read_text(encoding="utf-8")
TREE = ast.parse(SOURCE)
def node(name):
    matches = [n for n in TREE.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
               and n.name == name]
    assert len(matches) == 1, name
    return matches[0]
def isolate(names, ns):
    body = [ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0)]
    body.extend(node(name) for name in names)
    module = ast.fix_missing_locations(ast.Module(body=body, type_ignores=[]))
    env = dict(ns)
    exec(compile(module, "bot.py", "exec"), env)
    return env
class Role:
    id = 7
    managed = False
    permissions = NS(administrator=False)
    def is_default(self): return False
    def __ge__(self, other): return self.id >= other.id

class ReliabilityAuditTests(unittest.IsolatedAsyncioTestCase):
    def test_db_read_error_blocks_perdon_until_review(self):
        conn = NS(execute=MagicMock(side_effect=sqlite3.OperationalError("database locked")),close=MagicMock())
        fn = isolate(["condemnation_case_action_in_progress"],
                     {"db_connect":lambda:conn, "sqlite3":sqlite3})["condemnation_case_action_in_progress"]
        with self.assertRaises(sqlite3.OperationalError):
            fn(1,2)
        conn.close.assert_called_once()

    def test_role_configuration_and_permissions_revocations_are_denied(self):
        config = [{"role_id":7, "action":"añadir"}]
        role = Role()
        me = NS(guild_permissions=NS(manage_roles=True),top_role=NS(id=15))
        guild = NS(id=1,get_role=lambda rid:role,me=me)
        member = NS(id=2)
        env = isolate(["heraldo_message_role_access"],{
            "heraldo_message_role_config":lambda gid:config,
            "self_service_role_safe":lambda role:True,
            "condemnation_get":lambda gid,uid:None,
        })
        fn=env["heraldo_message_role_access"]
        self.assertIs(fn(guild,member,7,"añadir")[0],role)
        me.guild_permissions.manage_roles=False
        self.assertIn("Gestionar roles",fn(guild,member,7,"añadir")[1])
        me.guild_permissions.manage_roles=True
        config.clear()
        self.assertIn("ya no está configurado",fn(guild,member,7,"añadir")[1])

    def test_role_hierarchy_is_revalidated(self):
        role=Role()
        me=NS(guild_permissions=NS(manage_roles=True),top_role=NS(id=8))
        guild=NS(id=1,get_role=lambda _:role,me=me)
        fn=isolate(["heraldo_message_role_access"],{
            "heraldo_message_role_config":lambda _: [{"role_id":7,"action":"alternar"}],
            "self_service_role_safe":lambda role:True,
            "condemnation_get":lambda gid,uid:None,
        })["heraldo_message_role_access"]
        self.assertIs(fn(guild,NS(id=2),7,"alternar")[0],role)
        me.top_role=NS(id=6)
        self.assertIn("por encima",fn(guild,NS(id=2),7,"alternar")[1])

    def test_role_dispatch_rechecks_after_network_fetch(self):
        fn = node("heraldo_message_role_action")
        src=ast.get_source_segment(SOURCE,fn)
        before=src.index("heraldo_message_role_access(guild, interaction.user")
        fetch=src.index("await guild.fetch_member(")
        after=src.index("heraldo_message_role_access(guild, member")
        self.assertLess(before,fetch)
        self.assertLess(fetch,after)
        self.assertLess(after,src.index("await member.add_roles("))
        self.assertLess(after,src.index("await member.remove_roles("))

    def test_boot_does_not_abort_for_one_guild(self):
        fn=next(n for n in TREE.body if isinstance(n,ast.AsyncFunctionDef) and n.name=="on_ready")
        code=ast.get_source_segment(SOURCE,fn)
        self.assertIn("await synchronize_published_panels(guild, suggestions_already_synced=True)",code)
        self.assertIn("caché de invitaciones pendiente",code)
        self.assertIn("await refresh_invite_cache(guild)",code)
        self.assertIn("for recovery in (condemnation_reconcile, condemnation_recover_private_threads)",code)
        self.assertIn("except Exception:",code)

if __name__ == "__main__":
    unittest.main()
