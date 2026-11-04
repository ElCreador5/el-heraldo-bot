"""Pruebas de renderizado de paneles nativos sin conectar Discord."""
import os
import sqlite3
import tempfile
import unittest
from types import SimpleNamespace

import role_connections
import role_connections_setup as ui


class RoleConnectionsUITests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        path = os.path.join(self.tmp.name, "test.db")
        self.conn = lambda: sqlite3.connect(path, isolation_level=None)
        self.guild = SimpleNamespace(id=10, get_role=lambda rid: None)
        self.host = {
            "db_connect": self.conn,
            "guild_language": lambda gid: "es-419",
            "bot": SimpleNamespace(get_guild=lambda gid: self.guild),
            "configuration_access": lambda *args: True,
            "get_eval_role_ids": lambda gid: set(),
            "get_verify_role_id": lambda gid: 0,
            "get_sin_verificado_role_id": lambda gid: 0,
            "get_tentado_role_id": lambda gid: 0,
            "condemnation_role_id": lambda row, gid: 0,
            "condemnation_get": lambda gid, uid: None,
        }
        self.ctx = ui.Context(self.host, 10, 20)

    def tearDown(self):
        self.tmp.cleanup()

    def test_catalogs_have_same_keys(self):
        base = set(ui.LABELS["es-419"])
        for code in ("en-US", "pt-BR"):
            self.assertEqual(base, set(ui.LABELS[code]))

    def test_full_creation_navigation_under_five_rows(self):
        views = (
            ui.ConnectionsList(self.ctx),
            ui.ConnectionEditor(self.ctx, ui.new_draft()),
            ui.GroupEditor(self.ctx, ui.new_draft()),
            ui.ConditionEditor(self.ctx, ui.new_draft(), 0, None),
            ui.Confirmation(self.ctx, "sync", None),
        )
        for view in views:
            for item in view.children:
                self.assertTrue(item.row is None or 0 <= item.row <= 4)
            self.assertLessEqual(len(view.children), 25)
            text = view.summary(self.guild)
            self.assertTrue(text)
            self.assertLessEqual(len(text), 4000)

    def test_new_draft_is_empty_and_edit_draft_copies_conditions(self):
        rule = role_connections.Rule(
            "r1", "Example", 100,
            ({"mode": "all", "conditions": [{"role_id": 1, "op": "has"}]},),
            "any", True, "rev",
        )
        opened = ui.new_draft(rule)
        opened["groups"][0]["conditions"][0]["role_id"] = 10
        self.assertEqual(rule.groups[0]["conditions"][0]["role_id"], 1)
        blank = ui.new_draft()
        self.assertIsNone(blank["target_role_id"])
        self.assertEqual(blank["groups"][0]["conditions"], [])


if __name__ == "__main__":
    unittest.main()
