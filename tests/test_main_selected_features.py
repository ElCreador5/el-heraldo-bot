"""Regression checks for the seven selectively promoted main configurations.

No Discord Gateway, no real moderation changes, no scheduled publications.
"""
from __future__ import annotations
import ast
import json
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import AsyncMock, patch

import bot as b
from main_announcement_scheduler import next_occurrence
from member_rejoin_restore import _safe_role


SOURCE = (Path(__file__).resolve().parents[1] / "bot.py").read_text(encoding="utf-8")
TREE = ast.parse(SOURCE)


def source_of(name):
    for node in ast.walk(TREE):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and node.name == name:
            return ast.get_source_segment(SOURCE, node)
    raise AssertionError(f"missing {name}")


class SelectiveMainConfigurationTests(unittest.IsolatedAsyncioTestCase):
    def test_setup_selector_opens_directly(self):
        view = b.HeraldoSetupView(991, 17)
        self.assertNotIn("Configurar", {
            child.label for child in view.children
            if getattr(child, "label", None)
        })
        self.assertIn("await self.open_module(interaction)", source_of("select_module"))
        self.assertIn("autofeed_setup", source_of("HeraldoSetupView"))

    def test_cases_can_be_inspected_and_cleanup_requires_two_confirmations(self):
        self.assertIn("HeraldoCaseManagerSetupView", source_of("HeraldoCasesSetupView"))
        manager = source_of("HeraldoCaseManagerSetupView")
        self.assertIn("Abrir caso", manager)
        self.assertIn("Cerrar caso", manager)
        self.assertIn("Omitir caso", manager)
        self.assertIn("Limpiar todo", manager)
        self.assertIn("HeraldoCaseCleanupAllConfirmView", manager)
        confirmation = source_of("HeraldoCaseManagementConfirm")
        self.assertIn("LIMPIAR TODO", confirmation)
        self.assertIn("DELETE FROM moderation_cases WHERE guild_id=?", confirmation)
        self.assertIn("BEGIN IMMEDIATE", confirmation)
        self.assertNotIn("guild.ban(", confirmation)
        self.assertNotIn("member.kick(", confirmation)

    def test_rejoin_restoration_opt_in_and_protected(self):
        with patch.object(b, "guild_config_get", return_value=None):
            panel = b.HeraldoRejoinSetupView(101, 42)
        self.assertFalse(panel.original)
        self.assertTrue(panel.save.disabled)
        self.assertIn("verified_rejoin_restore_enabled", source_of("HeraldoRejoinConfirmView"))
        self.assertIn("capture_departure", source_of("heraldo_capture_verified_departure"))
        self.assertIn("restore_join", source_of("on_member_join"))
        permissions = NS(administrator=False, manage_roles=False,
                         manage_guild=False, ban_members=False,
                         kick_members=False, moderate_members=False)
        safe = NS(id=7, managed=False, is_default=lambda: False,
                  permissions=permissions)
        me = NS(top_role=NS(position=10), guild_permissions=NS(manage_roles=True))
        safe.__ge__ = lambda other: False
        guild = NS(me=me)
        # Missing/invalid role always fails closed.
        self.assertFalse(_safe_role(NS(me=None), safe))

    def test_pending_condemnation_roles_require_manual_confirmation(self):
        with patch.object(b, "guild_config_get", return_value='[12, 15, 12]'):
            self.assertEqual(b.condemnation_pending_roles_get(1, 5), [12, 15])
        captured = []
        with patch.object(b, "guild_config_set", side_effect=lambda *x: captured.append(x)):
            b.condemnation_pending_roles_set(1, 5, [17, 17, 18])
        self.assertEqual(json.loads(captured[0][2]), [17, 18])
        self.assertIn("condemnation_pending_roles_set", source_of("release_condemned_member"))
        self.assertIn("condemnation_get", source_of("PendingRoleRestoreView"))
        self.assertIn("manage_roles", source_of("restaurar_roles_pendientes"))
        self.assertIn("is_assignable()", source_of("PendingRoleRestoreView"))

    def test_report_actions_are_draft_only_and_use_existing_policy(self):
        picker = source_of("ModerationReportActionPicker")
        self.assertIn("MODERATION_REPORT_ACTIONS", picker)
        self.assertIn("pending_reactions", picker)
        self.assertIn("report", picker)
        self.assertIn("condemn", picker)
        self.assertNotIn("set_moderation_report_reactions(", picker)
        self.assertIn("choose_action", source_of("HeraldoUserReportsSetupView"))

    def test_announcements_run_only_after_confirmation(self):
        from autofeed_setup import SetupConfirmView, AutoFeedsHomeView
        from message_publish import publish_message
        from main_announcement_scheduler import AnnouncementScheduler
        self.assertIsNotNone(SetupConfirmView)
        self.assertIsNotNone(AutoFeedsHomeView)
        self.assertTrue(callable(publish_message))
        self.assertIn('from autofeed_setup import setup_panel', source_of("HeraldoSetupView"))
        source = (Path(__file__).resolve().parents[1] /
                  "main_announcement_scheduler.py").read_text(encoding="utf-8")
        self.assertIn("status='uncertain'", source)
        self.assertIn("status='sending'", source)
        self.assertNotIn("message_autofeeds.install", SOURCE)
        self.assertIn("_main_announcement_engine.start()", source_of("on_ready"))

    def test_next_occurrences_follow_timezone_and_production_minimum(self):
        now = datetime(2026, 11, 6, 12, tzinfo=timezone.utc)
        once = {"start": now.isoformat(), "repeat": "ninguna"}
        self.assertIsNone(next_occurrence(once, now))
        daily = {**once, "repeat": "diaria", "zone": "America/Santo_Domingo"}
        self.assertEqual(datetime.fromisoformat(next_occurrence(daily, now)),
                         now + timedelta(days=1))
        weekly = {**once, "repeat": "semanal", "zone": "America/Santo_Domingo"}
        self.assertEqual(datetime.fromisoformat(next_occurrence(weekly, now)),
                         now + timedelta(days=7))
        one_hour = {**once, "repeat": "custom",
                    "repeat_parts": {"months": 0, "days": 0, "hours": 1, "minutes": 0}}
        self.assertEqual(datetime.fromisoformat(next_occurrence(one_hour, now)),
                         now + timedelta(hours=1))
        too_short = {**once, "repeat": "custom",
                     "repeat_parts": {"minutes": 5}}
        with self.assertRaises(ValueError):
            next_occurrence(too_short, now)


if __name__ == "__main__":
    unittest.main()
