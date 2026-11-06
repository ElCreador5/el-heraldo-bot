"""Offline smoke checks for selective main configuration promotion."""
from __future__ import annotations
import ast
import json
import sqlite3
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import AsyncMock, patch

import discord
import autofeed_setup
import main_case_management
import main_pending_roles
import main_rejoin_setup
import member_rejoin_restore
import message_autofeeds
import message_automation
import message_publish


SOURCE = (Path(__file__).resolve().parents[1] / "bot.py").read_text(encoding="utf-8")
TREE = ast.parse(SOURCE)


def function(name):
    nodes = [node for node in TREE.body
             if isinstance(node, ast.AsyncFunctionDef) and node.name == name]
    if len(nodes) != 1:
        raise AssertionError(name)
    return nodes[0]


class MainSelectedSettingsTests(unittest.IsolatedAsyncioTestCase):
    def test_modules_import_and_setup_directly_opens_selection(self):
        cls = next(node for node in TREE.body
                   if isinstance(node, ast.ClassDef) and node.name == "HeraldoSetupView")
        selected = next(node for node in cls.body
                        if isinstance(node, ast.AsyncFunctionDef)
                        and node.name == "select_module")
        code = ast.get_source_segment(SOURCE, selected)
        self.assertIn("await self.open_module(interaction)", code)
        self.assertNotIn("response.edit_message(view=self)", code)
        init = next(node for node in cls.body
                    if isinstance(node, ast.FunctionDef) and node.name == "__init__")
        self.assertIn("self.remove_item(self.configure)",
                      ast.get_source_segment(SOURCE, init))
        self.assertIn("announcements_setup_panel(", SOURCE)

    def test_scheduler_custom_recurrence(self):
        now = datetime(2026, 11, 6, 12, tzinfo=timezone.utc)
        job = {
            "repeat": "custom",
            "repeat_parts": {"months": 0, "days": 0, "hours": 6, "minutes": 0},
            "start": (now - timedelta(hours=2)).isoformat(),
            "zone": "America/Santo_Domingo",
        }
        next_run = datetime.fromisoformat(message_automation.next_occurrence(job, now))
        self.assertGreater(next_run, now)
        self.assertLessEqual(next_run, now + timedelta(hours=6))

    def test_case_cleanup_requires_coded_confirmation(self):
        self.assertIn("LIMPIAR TODO", main_case_management.CaseDeleteModal.__init__.__code__.co_consts)
        s = (Path(__file__).resolve().parents[1] / "main_case_management.py").read_text("utf-8")
        self.assertIn("DELETE FROM moderation_cases WHERE guild_id=?", s)
        self.assertIn("WHERE guild_id=? AND open=0", s)
        self.assertIn("BEGIN IMMEDIATE", s)
        self.assertNotIn("DELETE FROM guild_cases", s)

    def test_pending_roles_are_scoped_and_invalid_data_is_safe(self):
        storage = {}
        def get(gid, key):
            return storage.get((gid, key))
        def set_value(gid, key, value):
            storage[(gid, key)] = value
        host = {"guild_config_get": get, "guild_config_set": set_value}
        main_pending_roles.pending_set(host, 10, 25, [13, 7, 7])
        self.assertEqual(main_pending_roles.pending_get(host, 10, 25), [7, 13])
        self.assertEqual(main_pending_roles.pending_get(host, 11, 25), [])
        main_pending_roles.pending_set(host, 10, 25, [])
        self.assertEqual(main_pending_roles.pending_get(host, 10, 25), [])

    def test_rejoin_avoids_elevated_roles(self):
        perms = NS(administrator=False, manage_guild=False,
                   manage_roles=False, ban_members=False, kick_members=False,
                   moderate_members=False)
        class Role:
            id = 20
            managed = False
            permissions = perms
            def is_default(self):
                return False
            def __ge__(self, other):
                return False
        role = Role()
        guild = NS(me=NS(top_role=NS(position=50),
                          guild_permissions=NS(manage_roles=True)))
        self.assertTrue(member_rejoin_restore._safe_role(guild, role))
        role.permissions.administrator = True
        self.assertFalse(member_rejoin_restore._safe_role(guild, role))

    def test_configurable_reports_require_staff_for_warnings(self):
        code = ast.get_source_segment(SOURCE, function("execute_moderation_report_action"))
        self.assertIn('action == "warn"', code)
        self.assertIn("moderation_is_staff(actor)", code)
        self.assertIn("moderation_warning_limit(guild.id)", code)
        self.assertIn("actor=actor", SOURCE)
        self.assertIn("self._rebuild_action_select()", SOURCE)

    def test_rejoin_opt_in_and_role_pending_tracking_are_connected(self):
        self.assertIn('guild_config_get(member.guild.id, "verified_rejoin_restore_enabled") == "1"', SOURCE)
        self.assertIn("await restore_join(", SOURCE)
        self.assertIn("await capture_departure(", SOURCE)
        self.assertIn("from main_pending_roles import pending_get, pending_set", SOURCE)
        self.assertIn('name="restaurar_roles_pendientes"', SOURCE)


if __name__ == "__main__":
    unittest.main()
