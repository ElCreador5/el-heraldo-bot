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


    def test_direct_conditions_and_advanced_group_navigation(self):
        draft = ui.new_draft()
        editor = ui.ConnectionEditor(self.ctx, draft)
        labels = [getattr(item, "label", "") for item in editor.children]
        self.assertIn(self.ctx.t("add_condition"), labels)
        self.assertIn(self.ctx.t("condition_operator"), labels)
        self.assertIn(self.ctx.t("advanced_groups"), labels)
        self.assertFalse(any(getattr(item, "placeholder", "") ==
                             self.ctx.t("group") for item in editor.children))
        advanced = ui.AdvancedGroups(self.ctx, draft)
        self.assertTrue(any(getattr(item, "placeholder", "") ==
                            self.ctx.t("group") for item in advanced.children))
        self.assertIn(self.ctx.t("group_overview"), advanced.summary(self.guild))
        for view in (editor, advanced):
            self.assertLessEqual(max(item.row for item in view.children), 4)
            self.assertEqual(
                1, sum(getattr(item, "label", "") == self.ctx.t("close")
                       for item in view.children)
            )

    def test_save_and_discard_only_enabled_for_valid_edits(self):
        draft = ui.new_draft()
        def disabled(view, key):
            return next(item.disabled for item in view.children
                        if getattr(item, "label", "") == self.ctx.t(key))
        self.assertTrue(disabled(ui.ConnectionEditor(self.ctx, draft), "save"))
        self.assertTrue(disabled(ui.ConnectionEditor(self.ctx, draft), "discard"))
        draft["target_role_id"] = 10
        self.assertTrue(disabled(ui.ConnectionEditor(self.ctx, draft), "save"))
        self.assertFalse(disabled(ui.ConnectionEditor(self.ctx, draft), "discard"))
        draft["groups"][0]["conditions"].append({"role_id": 11, "op": "has"})
        self.assertFalse(disabled(ui.ConnectionEditor(self.ctx, draft), "save"))
        self.assertIn(self.ctx.t("conditions_header"),
                      ui.ConnectionEditor(self.ctx, draft).summary(self.guild))
        self.assertIn("<@&11>", ui.ConnectionEditor(self.ctx, draft).summary(self.guild))
        draft["groups"][0]["conditions"].clear()
        draft["target_role_id"] = None
        self.assertFalse(ui.draft_changed(draft))
        self.assertTrue(disabled(ui.ConnectionEditor(self.ctx, draft), "discard"))

    def test_advanced_groups_preview_and_dirty_navigation(self):
        draft = ui.new_draft()
        draft["target_role_id"] = 20
        draft["groups"] = [
            {"mode": "all", "conditions": [
                {"role_id": 1, "op": "has"}, {"role_id": 2, "op": "lacks"}
            ]},
            {"mode": "any", "conditions": [{"role_id": 3, "op": "has"}]},
        ]
        draft["groups_mode"] = "any"
        panel = ui.AdvancedGroups(self.ctx, draft)
        self.assertIn("OR", panel.summary(self.guild))
        self.assertIn("<@&1>", panel.summary(self.guild))
        self.assertIn("<@&2>", panel.summary(self.guild))
        self.assertIn("<@&3>", panel.summary(self.guild))
        self.assertFalse(ui.draft_can_save(ui.new_draft()))
        self.assertTrue(ui.draft_can_save(draft))

    def test_open_panel_does_not_create_sqlite_table(self):
        ui.ConnectionEditor(self.ctx, ui.new_draft())
        ui.AdvancedGroups(self.ctx, ui.new_draft())
        with self.conn() as connection:
            tables = connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        self.assertNotIn(("heraldo_role_connections",), tables)


    def test_operator_labels_are_and_or_in_every_panel(self):
        for lang in ("es-419", "en-US", "pt-BR"):
            self.host["guild_language"] = lambda gid, code=lang: code
            ctx = ui.Context(self.host, 10, 20)
            draft = ui.new_draft()
            self.assertEqual(ui._operator("all"), "AND")
            self.assertEqual(ui._operator("any"), "OR")
            draft["groups"][0]["conditions"] = [{"role_id": 1, "op": "has"}]
            draft["groups"].append(
                {"mode": "any", "conditions": [{"role_id": 2, "op": "lacks"}]}
            )
            draft["groups_mode"] = "any"

            views = [
                ui.ConnectionEditor(ctx, draft),
                ui.AdvancedGroups(ctx, draft),
                ui.GroupEditor(ctx, draft),
                ui.ConditionEditor(ctx, draft, 0, 0),
            ]
            for panel in views:
                rendered = panel.summary(self.guild)
                labels = " ".join(
                    str(getattr(item, "label", "") or "") for item in panel.children
                )
                options = " ".join(
                    option.label
                    for item in panel.children
                    for option in getattr(item, "options", [])
                )
                visible = " ".join((rendered, labels, options))
                self.assertNotIn(" ALL", visible)
                self.assertNotIn(" ANY", visible)
                self.assertNotIn(" all ", visible)
                self.assertNotIn(" any ", visible)
                self.assertIn("AND", rendered)
            main = views[0]
            self.assertIn(
                f"{ctx.t('conditions_header')}: AND",
                [getattr(item, "label", "") for item in main.children],
            )
            advanced = views[1]
            self.assertIn(
                f"{ctx.t('group_operator')}: OR",
                [getattr(item, "label", "") for item in advanced.children],
            )
            group_editor = views[2]
            self.assertIn(
                f"{ctx.t('group_mode')}: AND",
                [getattr(item, "label", "") for item in group_editor.children],
            )
            draft["groups"][0]["mode"] = "any"
            self.assertIn("OR", ui.ConnectionEditor(ctx, draft).summary(self.guild))



if __name__ == "__main__":
    unittest.main()
