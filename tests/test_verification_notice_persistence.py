"""Regresión: avisos de verificación idempotentes y aislamiento del bot Test."""
import ast
import copy
import hashlib
import json
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import AsyncMock

SOURCE = (Path(__file__).resolve().parents[1] / "bot.py").read_text(encoding="utf-8")
TREE = ast.parse(SOURCE)


def isolate_async(name, context):
    node = next(n for n in TREE.body if isinstance(n, ast.AsyncFunctionDef) and n.name == name)
    node = copy.deepcopy(node)
    node.decorator_list = []
    mod = ast.Module(body=[
        ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0),
        node,
    ], type_ignores=[])
    scope = dict(context)
    exec(compile(ast.fix_missing_locations(mod), "bot.py", "exec"), scope)
    return scope[name]


class NoticePersistenceTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.guild = NS(id=808)
        self.receipts = {}
        self.findings = ((), (11, 12), ())
        self.sent = AsyncMock(return_value=NS(id=100))
        self.reboot()

    def reboot(self):
        self.run = isolate_async("reconcile_untracked_verifications", {
            "bot": NS(guilds=[self.guild]),
            "db_meta_get": lambda key: self.receipts.get(key),
            "db_meta_set": lambda key, value: self.receipts.__setitem__(key, value),
            "reconcile_untracked_verifications_for_guild":
                AsyncMock(side_effect=lambda _: self.findings),
            "log_embed": self.sent,
            "hashlib": hashlib,
            "json": json,
            "discord": NS(Color=NS(orange=lambda: 7)),
        })

    async def test_identical_state_is_not_announced_again_after_restart(self):
        await self.run()
        self.assertEqual(self.sent.await_count, 1)
        self.assertEqual(len(self.receipts), 1)
        self.reboot()
        await self.run()
        self.assertEqual(self.sent.await_count, 1)

    async def test_changed_population_is_reported_once(self):
        await self.run()
        self.findings = ((), (11, 12, 13), ())
        await self.run()
        await self.run()
        self.assertEqual(self.sent.await_count, 2)

    async def test_resolved_then_reappearing_issue_is_reported(self):
        await self.run()
        self.findings = ((), (), ())
        await self.run()
        self.assertEqual(self.sent.await_count, 1)
        self.findings = ((), (11, 12), ())
        await self.run()
        self.assertEqual(self.sent.await_count, 2)

    async def test_no_receipt_when_discord_cannot_deliver(self):
        self.sent.return_value = None
        await self.run()
        self.assertFalse(self.receipts)
        self.sent.return_value = NS(id=102)
        await self.run()
        self.assertEqual(self.sent.await_count, 2)
        self.assertEqual(len(self.receipts), 1)

    async def test_newly_rearmed_member_is_reported(self):
        await self.run()
        self.findings = ((15,), (11, 12), ())
        await self.run()
        self.assertEqual(self.sent.await_count, 2)


class TestGuildIsolationTests(unittest.IsolatedAsyncioTestCase):
    async def test_test_bot_only_rearms_in_explicitly_allowed_lab(self):
        enrolled = []
        settings = {"lab": "other"}
        async def run():
            fn = isolate_async("reconcile_untracked_verifications_for_guild", {
                "get_sin_verificado_role_id": lambda _: 40,
                "get_verify_role_id": lambda _: 41,
                "get_eval_role_ids": lambda _: set(),
                "verify_enabled": lambda _: True,
                "heraldo_is_test": lambda: True,
                "os": NS(getenv=lambda name: settings["lab"]),
                "datetime": datetime, "timezone": timezone,
                "condemnation_get": lambda guild, user: None,
                "db_get": lambda guild, user: None,
                "db_set_verify_pending": lambda guild, user, at: enrolled.append(user),
            })
            recent = NS(id=99, bot=False, pending=False,
                        joined_at=datetime.now(timezone.utc)-timedelta(minutes=2),
                        roles=[NS(id=40)])
            class FakeGuild:
                id = 808
                def get_role(self, ident):
                    return NS(id=ident)
                async def fetch_members(self, *, limit):
                    assert limit is None
                    yield recent
            return await fn(FakeGuild())
        self.assertEqual(await run(), ((), (99,), ()))
        self.assertEqual(enrolled, [])
        settings["lab"] = "808"
        self.assertEqual(await run(), ((99,), (), ()))
        self.assertEqual(enrolled, [99])


if __name__ == "__main__":
    unittest.main()
