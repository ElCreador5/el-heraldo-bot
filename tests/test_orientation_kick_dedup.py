"""No duplicar la expulsión por orientación ni suprimir acciones ajenas."""
from __future__ import annotations

import ast
import asyncio
import time
import unittest
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import AsyncMock

SOURCE = (Path(__file__).resolve().parents[1] / "bot.py").read_text(encoding="utf-8")
TREE = ast.parse(SOURCE)

def isolated(*names, namespace=None):
    available = [node for node in TREE.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                 and node.name in names]
    assert len(available) == len(names), names
    mod = ast.Module(body=[
        ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0),
        *available
    ], type_ignores=[])
    ctx = dict(namespace or {})
    exec(compile(ast.fix_missing_locations(mod), "bot.py", "exec"), ctx)
    return ctx

class OrientationKickDedupTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.clock = time.monotonic()
        self.sent, self.pending = {}, {}
        self.bot = NS(user=NS(id=50))
        self.ns = isolated("orientation_kick_log_key",
                           "orientation_prune_kick_log_markers",
                           "orientation_departure_has_detailed_log",
                           namespace={
                               "time": time, "asyncio": asyncio, "bot": self.bot,
                               "_ORIENTATION_KICK_REASON": "No definió su orientación",
                               "_ORIENTATION_LOG_WINDOW": 30.0,
                               "_orientation_kick_log_pending": self.pending,
                               "_orientation_kick_log_sent": self.sent,
                           })
        self.check = self.ns["orientation_departure_has_detailed_log"]
        self.member = NS(id=7, guild=NS(id=10), joined_at="ingreso1")
        self.key = self.ns["orientation_kick_log_key"](self.member)
        self.own_actor = NS(id=50)

    async def test_specific_verification_log_suppresses_one_generic_kick(self):
        self.sent[self.key] = time.monotonic()
        self.assertTrue(await self.check(self.member, "member_kick", self.own_actor,
                                         "No definió su orientación"))
        self.assertFalse(await self.check(self.member, "member_kick", self.own_actor,
                                          "No definió su orientación"))

    async def test_other_moderator_and_reason_keep_their_logs(self):
        self.sent[self.key] = time.monotonic()
        self.assertFalse(await self.check(self.member, "member_kick", NS(id=90),
                                          "No definió su orientación"))
        self.assertFalse(await self.check(self.member, "member_kick", self.own_actor,
                                          "Reglas del servidor"))
        self.assertIn(self.key, self.sent)

    async def test_without_detail_generic_log_is_preserved(self):
        self.assertFalse(await self.check(self.member, "member_kick", self.own_actor,
                                          "No definió su orientación"))
        self.assertFalse(await self.check(self.member, "member_leave", None, None))

    async def test_missing_audit_can_use_local_confirmation(self):
        self.sent[self.key] = time.monotonic()
        self.assertTrue(await self.check(self.member, "member_leave", None, None))

    async def test_rejoin_and_stale_records_cannot_hide_new_departures(self):
        self.sent[self.key] = time.monotonic() - 31
        self.assertFalse(await self.check(self.member, "member_kick", self.own_actor,
                                          "No definió su orientación"))
        self.sent[self.key] = time.monotonic()
        newer = NS(id=7, guild=self.member.guild, joined_at="ingreso2")
        self.assertFalse(await self.check(newer, "member_kick", self.own_actor,
                                          "No definió su orientación"))

    async def test_bans_are_never_suppressed(self):
        self.sent[self.key] = time.monotonic()
        self.assertFalse(await self.check(self.member, "member_ban", self.own_actor,
                                          "No definió su orientación"))

    async def test_wait_for_successful_detailed_log(self):
        event = asyncio.Event()
        self.pending[self.key] = event
        async def complete():
            await asyncio.sleep(0)
            self.sent[self.key] = time.monotonic()
            event.set()
        await asyncio.gather(complete(), self.check(self.member, "member_kick",
                                                     self.own_actor, "No definió su orientación"))
        self.assertNotIn(self.key, self.sent)

    def test_delegation_and_publication_only_after_success(self):
        listener = next(n for n in TREE.body if isinstance(n, ast.AsyncFunctionDef)
                        and n.name == "heraldo_member_departure")
        expel = next(n for n in TREE.body if isinstance(n, ast.AsyncFunctionDef)
                     and n.name == "expel")
        listener_source = ast.get_source_segment(SOURCE, listener)
        expel_source = ast.get_source_segment(SOURCE, expel)
        self.assertIn("orientation_departure_has_detailed_log(", listener_source)
        self.assertIn("_orientation_kick_log_sent[log_key] = time.monotonic()", expel_source)
        self.assertIn("except discord.HTTPException:", expel_source)
        self.assertIn("pending.set()", expel_source)
        self.assertLess(expel_source.index("await channel.send(embed=embed)"),
                        expel_source.index("_orientation_kick_log_sent[log_key]"))

if __name__ == "__main__":
    unittest.main()
