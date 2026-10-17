"""Regresión de verificación tras desconexión: revisión segura, sin Discord real."""
import ast
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace as NS

SOURCE = (Path(__file__).resolve().parents[1] / "bot.py").read_text(encoding="utf-8")
TREE = ast.parse(SOURCE)
FUNC = next(n for n in TREE.body if isinstance(n, ast.AsyncFunctionDef)
            and n.name == "reconcile_untracked_verifications_for_guild")


def isolate(env):
    module = ast.Module(body=[ast.ImportFrom(module="__future__",
        names=[ast.alias(name="annotations")], level=0), FUNC], type_ignores=[])
    ns = dict(env)
    exec(compile(ast.fix_missing_locations(module), "bot.py", "exec"), ns)
    return ns[FUNC.name]


class Guild:
    id = 501
    def __init__(self, members):
        self.members = members
    def get_role(self, rid):
        return NS(id=rid) if rid in (40, 41) else None
    async def fetch_members(self, *, limit):
        assert limit is None
        for m in self.members:
            yield m


def member(uid, roles=(40,), minutes=3, pending=False, is_bot=False):
    return NS(id=uid, roles=[NS(id=i) for i in roles],
              joined_at=datetime.now(timezone.utc)-timedelta(minutes=minutes),
              pending=pending, bot=is_bot)


class VerificationReconciliationTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.rows, self.enrolled, self.condemned = {}, [], set()
        self.enabled = True
        self.fn = isolate({
            "datetime":datetime, "timezone":timezone,
            "get_sin_verificado_role_id":lambda _:40,
            "get_verify_role_id":lambda _:41,
            "get_eval_role_ids":lambda _:{42},
            "verify_enabled":lambda _:self.enabled,
            "heraldo_is_test":lambda:False,
            "condemnation_get":lambda gid,uid:True if uid in self.condemned else None,
            "db_get":lambda gid,uid:self.rows.get((gid,uid)),
            "db_set_verify_pending":self.enroll
        })

    def enroll(self, gid, uid, dt):
        self.enrolled.append((gid,uid,dt))
        self.rows[(gid,uid)] = {
            "verify_pending_at":dt.isoformat(), "sin_verificado_at":None, "tentado_at":None
        }

    async def test_recent_role_gets_fresh_deadline_only_once(self):
        m = member(7)
        self.assertEqual(await self.fn(Guild([m])), ((7,),(),()))
        self.assertLess((datetime.now(timezone.utc)-self.enrolled[0][2]).total_seconds(),10)
        self.assertEqual(await self.fn(Guild([m])), ((),(),()))

    async def test_old_pending_future_and_bot_not_sanctioned(self):
        members = [member(1, minutes=60),member(2,pending=True),
                   member(3,minutes=-2),member(4,is_bot=True)]
        self.assertEqual(await self.fn(Guild(members)), ((),(1,2,3),()))
        self.assertFalse(self.enrolled)

    async def test_conflicting_verified_roles_never_enroll(self):
        self.assertEqual(await self.fn(Guild([
            member(1,roles=(40,41)),member(2,roles=(40,42))
        ])), ((),(),(1,2)))
        self.assertFalse(self.enrolled)

    async def test_existing_pending_and_condemnation_unchanged(self):
        self.rows[(501,1)] = {"verify_pending_at":None,
            "sin_verificado_at":"2026-01-01T00:00:00+00:00", "tentado_at":None}
        self.condemned.add(2)
        self.assertEqual(await self.fn(Guild([member(1),member(2)])), ((),(),()))
        self.assertFalse(self.enrolled)

    async def test_disabled_verification_not_rearmed(self):
        self.enabled = False
        self.assertEqual(await self.fn(Guild([member(1)])), ((),(1,),()))
        self.assertFalse(self.enrolled)

    async def test_batch_guard_and_no_remote_punishment(self):
        rearmed,review,both = await self.fn(Guild([member(i) for i in range(30)]))
        self.assertEqual((len(rearmed),len(review),len(both)),(25,5,0))
        source = ast.get_source_segment(SOURCE,FUNC)
        for forbidden in ("heraldo_kick(","heraldo_ban(",".kick(",".ban("):
            self.assertNotIn(forbidden,source)
        self.assertIn("fetch_members(limit=None)",source)


if __name__ == "__main__":
    unittest.main()
