"""Regresiones aisladas del modo Test y los baneos temporales."""
from i18n_source_helpers import source_text as _source_text
import ast
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

SOURCE = _source_text(Path(__file__).resolve().parents[1] / 'bot.py', encoding='utf-8')
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
    # Los casos de sanción aislados parten de personalidad activa y obligatoria.
    # Los controles de desactivación tienen sus propias regresiones.
    context.setdefault("orientation_enabled", lambda guild_id: True)
    context.setdefault("personality_required", lambda guild_id: True)
    # Incorporar la exención real en las evaluaciones aisladas, sin falsificar permisos.
    checker = next((n for n in TREE.body if isinstance(n, ast.FunctionDef)
                    and n.name == "verification_is_exempt"), None)
    assert checker is not None
    helper = ast.fix_missing_locations(ast.Module(body=[
        ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0),
        checker,
    ], type_ignores=[]))
    exec(compile(helper, "bot.py", "exec"), context)
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

    def test_test_removal_invites_are_restricted_to_personality(self):
        source = segment("send_test_removal_notice")
        self.assertIn("allow_reentry_invite: bool = False", source)
        self.assertIn('if allow_reentry_invite and action == "KICK":', source)
        self.assertIn("max_uses=1", source)
        self.assertIn("max_age=0", source)
        self.assertIn("allow_reentry_invite=True", segment("expel"))
        self.assertNotIn("allow_reentry_invite=True", segment("heraldo_kick"))
        self.assertNotIn("allow_reentry_invite=True", segment("heraldo_ban"))

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

    async def test_failed_personality_kick_sends_only_planned_dm_first(self):
        class Refused(Exception):
            pass
        dm = AsyncMock()
        notice = AsyncMock()
        mark = MagicMock()
        kick = AsyncMock(side_effect=Refused("Discord rechazó la expulsión"))
        fn = isolated("expel", ns={
            "discord": SimpleNamespace(HTTPException=Refused),
            "db_get": lambda *args: {"dm_sent": False},
            "db_clear_tentado": MagicMock(),
            "db_mark_dm_sent": mark,
            "clear_verification_expiry": MagicMock(),
            "heraldo_is_test": lambda: False,
            "prepare_removal_dm": AsyncMock(return_value=None),
            "heraldo_kick": kick,
            "send_test_removal_notice": notice,
            "send_recovery_dm": dm,
        })["expel"]
        member = SimpleNamespace(id=2, guild=SimpleNamespace(id=1, owner_id=9))
        await fn(member, report=False)
        kick.assert_awaited_once()
        dm.assert_awaited_once()
        notice.assert_not_awaited()
        mark.assert_called_once()

    async def test_successful_personality_kick_sends_planned_dm_first(self):
        events = []
        kick = AsyncMock(side_effect=lambda *args, **kw: events.append("kick"))
        dm = AsyncMock(side_effect=lambda *a, **kw: (events.append("dm"), True)[1])
        mark = MagicMock(side_effect=lambda *a: events.append("mark"))
        fn = isolated("expel", ns={
            "db_get": lambda *args: {"dm_sent": False},
            "db_clear_tentado": MagicMock(),
            "db_mark_dm_sent": mark,
            "clear_verification_expiry": MagicMock(),
            "heraldo_is_test": lambda: False,
            "prepare_removal_dm": AsyncMock(return_value=None),
            "heraldo_kick": kick,
            "send_test_removal_notice": AsyncMock(),
            "send_recovery_dm": dm,
        })["expel"]
        member = SimpleNamespace(id=2, guild=SimpleNamespace(id=1, owner_id=9))
        await fn(member, report=False)
        self.assertEqual(events, ["dm", "mark", "kick"])

    async def test_second_orientation_removal_keeps_test_notice(self):
        events = []
        fn = isolated("expel", ns={
            "db_get": lambda *args: {"dm_sent": True},
            "db_clear_tentado": MagicMock(),
            "db_mark_dm_sent": MagicMock(),
            "clear_verification_expiry": MagicMock(),
            "heraldo_is_test": lambda: True,
            "prepare_removal_dm": AsyncMock(return_value=None),
            "heraldo_kick": AsyncMock(side_effect=lambda *args, **kw: events.append("kick")),
            "send_test_removal_notice": AsyncMock(side_effect=lambda *a, **kw: events.append("dm")),
            "send_recovery_dm": AsyncMock(),
        })["expel"]
        await fn(SimpleNamespace(id=2, guild=SimpleNamespace(id=1, owner_id=9)), report=False)
        self.assertEqual(events, ["kick", "dm"])

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
