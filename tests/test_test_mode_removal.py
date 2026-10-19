"""Regresiones aisladas del modo Test y los baneos temporales."""
import ast
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

SOURCE = (Path(__file__).resolve().parents[1] / "bot.py").read_text(encoding="utf-8")
TREE = ast.parse(SOURCE)

def node(name):
    nodes = [n for n in TREE.body
             if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
             and n.name == name]
    assert len(nodes) == 1, name
    return nodes[0]

def segment(name):
    return ast.get_source_segment(SOURCE, node(name))

def isolated(*names, ns=None):
    body = [ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0)]
    body.extend(node(name) for name in names)
    module = ast.fix_missing_locations(ast.Module(body=body, type_ignores=[]))
    context = {} if ns is None else dict(ns)
    exec(compile(module, "bot.py", "exec"), context)
    return context

class TestModeReasons(unittest.TestCase):
    def test_uniform_reason_at_engine_entry_and_resolution(self):
        self.assertIn("HERALDO_TEST_REASON if heraldo_is_test()", segment("condemn_member"))
        self.assertIn("HERALDO_TEST_REASON if heraldo_is_test()", segment("condemnation_update_pardoned_card"))

    def test_all_removals_use_wrappers(self):
        for verb in ("ban", "kick"):
            self.assertNotIn(f"await member.{verb}(", SOURCE)
            self.assertNotIn(f"await target.{verb}(", SOURCE)
        self.assertIn("max_uses=1", segment("send_test_removal_notice"))
        self.assertIn("max_age=0", segment("send_test_removal_notice"))
        self.assertLess(segment("heraldo_kick").index('getattr(member, "kick")'),
                        segment("heraldo_kick").index("send_test_removal_notice"))
        self.assertLess(segment("heraldo_ban").index('getattr(member, "ban")'),
                        segment("heraldo_ban").index("send_test_removal_notice"))

    def test_ui_requires_configuration_confirmation(self):
        self.assertIn("confirm_configuration(", segment("HeraldoBanDurationSetupView"))
        self.assertIn("confirm_configuration(", segment("HeraldoBanDurationModal"))
        self.assertIn("HeraldoBanDurationSetupView", segment("HeraldoModerationSetupView"))
        self.assertIn('duration_minutes if action in {"timeout", "ban"}',
                      segment("execute_moderation_report_action"))
        self.assertIn('explicit_permanent = case_type == "BAN" and duration_minutes == 0',
                      segment("moderation_apply_case_punishment"))

    def test_unban_failure_keeps_case_open(self):
        fragment = segment("moderation_case_expiry_loop")
        self.assertIn("Reintentar desbaneo", fragment)
        self.assertIn("Sustituido por un baneo posterior", fragment)
        self.assertIn("current.reason != row[", fragment)
        self.assertIn("continue", fragment)

class BanPolicyTests(unittest.IsolatedAsyncioTestCase):
    def test_config_default_explicit_and_permanent(self):
        state = {"test": True, "config": None}
        ns = isolated("moderation_default_ban_minutes",
                      "moderation_effective_ban_minutes", ns={
            "guild_config_get": lambda *args: state["config"],
            "heraldo_is_test": lambda: state["test"],
        })
        default = ns["moderation_default_ban_minutes"]
        effective = ns["moderation_effective_ban_minutes"]
        self.assertEqual(default(1), 5)
        state["test"] = False
        self.assertIsNone(default(1))
        state["config"] = "60"
        self.assertEqual(default(1), 60)
        self.assertEqual(effective(1, 2), 2)
        self.assertIsNone(effective(1, 0))
        state["config"] = "0"
        self.assertIsNone(default(1))

    async def test_notice_after_ban_with_expiring_case(self):
        order = []
        ban = AsyncMock(side_effect=lambda **kw: order.append("ban"))
        dm = AsyncMock(side_effect=lambda *a, **kw: order.append("dm"))
        create_case = MagicMock(side_effect=lambda *a, **kw: order.append("case"))
        fn = isolated("heraldo_ban", ns={
            "heraldo_is_test": lambda: True,
            "moderation_effective_ban_minutes": lambda *args: 5,
            "send_test_removal_notice": dm,
            "prepare_removal_dm": AsyncMock(return_value=None),
            "moderation_case_create": create_case,
        })["heraldo_ban"]
        member = SimpleNamespace(guild=SimpleNamespace(id=2), id=9, ban=ban)
        duration = await fn(member, reason="Prueba")
        self.assertEqual(duration, 5)
        self.assertEqual(order, ["ban", "case", "dm"])
        self.assertEqual(create_case.call_args.kwargs["duration_minutes"], 5)

    async def test_failed_kick_does_not_send_dm(self):
        class Refused(Exception):
            pass
        dm = AsyncMock()
        fn = isolated("heraldo_kick", ns={
            "heraldo_is_test": lambda: True,
            "prepare_removal_dm": AsyncMock(return_value=None),
            "send_test_removal_notice": dm,
        })["heraldo_kick"]
        with self.assertRaises(Refused):
            await fn(SimpleNamespace(kick=AsyncMock(side_effect=Refused())), reason="Prueba")
        dm.assert_not_awaited()

    async def test_successful_kick_notifies_after_action(self):
        order = []
        fn = isolated("heraldo_kick", ns={
            "heraldo_is_test": lambda: True,
            "prepare_removal_dm": AsyncMock(return_value=None),
            "send_test_removal_notice": AsyncMock(side_effect=lambda *a, **kw: order.append("dm")),
        })["heraldo_kick"]
        await fn(SimpleNamespace(kick=AsyncMock(side_effect=lambda **kw: order.append("kick"))), reason="Prueba")
        self.assertEqual(order, ["kick", "dm"])

    async def test_failed_ban_does_not_send_dm(self):
        class Refused(Exception):
            pass
        dm = AsyncMock()
        fn = isolated("heraldo_ban", ns={
            "heraldo_is_test": lambda: True,
            "moderation_effective_ban_minutes": lambda *a: 5,
            "prepare_removal_dm": AsyncMock(return_value=None),
            "send_test_removal_notice": dm,
            "moderation_case_create": MagicMock(),
        })["heraldo_ban"]
        with self.assertRaises(Refused):
            await fn(SimpleNamespace(guild=SimpleNamespace(id=1), id=2, ban=AsyncMock(side_effect=Refused())), reason="Prueba")
        dm.assert_not_awaited()

    async def test_case_record_not_duplicated(self):
        create_case = MagicMock()
        fn = isolated("heraldo_ban", ns={
            "heraldo_is_test": lambda: False,
            "moderation_effective_ban_minutes": lambda *args: 5,
            "send_test_removal_notice": AsyncMock(),
            "prepare_removal_dm": AsyncMock(return_value=None),
            "moderation_case_create": create_case,
        })["heraldo_ban"]
        member = SimpleNamespace(guild=SimpleNamespace(id=2), id=9, ban=AsyncMock())
        await fn(member, reason="Motivo", duration_minutes=5, record_case=False)
        create_case.assert_not_called()

if __name__ == "__main__":
    unittest.main()
