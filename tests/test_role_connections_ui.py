"""Pruebas de renderizado de paneles nativos sin conectar Discord."""
import os
import sqlite3
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace

import discord

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
        self.assertIn(f"{self.ctx.t('conditions_header')}: AND", labels)
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
        # This case tests the dirty draft only; a separate test checks
        # actual Discord role safety for the chosen target.
        with patch.object(role_connections, "target_safety_reason", return_value=None):
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
                if not isinstance(panel, ui.ConditionEditor):
                    self.assertIn("AND", visible)
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



    def test_protected_personality_main_role_is_explained_before_saving(self):
        class TargetRole(discord.Object):
            def __init__(self, guild, role_id):
                super().__init__(id=role_id, type=discord.Role)
                self.guild, self.managed = guild, False
                self.name = f"Role-{role_id}"
                self.mention = f"<@&{role_id}>"
                self.permissions = SimpleNamespace(**{
                    name: False for name in role_connections.PRIVILEGED
                })

            def is_default(self):
                return False

            def __ge__(self, other):
                return self.id >= other.id

        guild = SimpleNamespace(id=10)
        roles = {i: TargetRole(guild, i) for i in (11, 20, 21, 100)}
        guild.get_role = roles.get
        guild.me = SimpleNamespace(
            guild_permissions=SimpleNamespace(manage_roles=True),
            top_role=roles[100],
        )
        self.guild = guild
        self.host["bot"] = SimpleNamespace(get_guild=lambda gid: guild)
        self.host["get_eval_role_ids"] = lambda gid: {20}

        draft = ui.new_draft()
        draft["target_role_id"] = 20
        draft["name"] = "Personality"
        draft["groups"][0]["conditions"].append({"role_id": 11, "op": "has"})
        for language in ("es-419", "en-US", "pt-BR"):
            self.host["guild_language"] = lambda gid, language=language: language
            ctx = ui.Context(self.host, 10, 20)
            editor = ui.ConnectionEditor(ctx, draft)
            self.assertIn(ctx.t("unsafe_protected"), editor.summary(guild))
            save_button = next(
                item for item in editor.children
                if getattr(item, "label", None) == ctx.t("save")
            )
            self.assertTrue(save_button.disabled)
            self.assertFalse(ui.draft_can_save(
                draft, guild=guild, protected_ids=ctx.protected()
            ))

        # A regular, assignable destination role remains allowed; the
        # personality role can still be used as a *condition*.
        draft["target_role_id"] = 21
        draft["groups"][0]["conditions"][0]["role_id"] = 20
        ctx = ui.Context(self.host, 10, 20)
        editor = ui.ConnectionEditor(ctx, draft)
        self.assertIsNone(editor.target_warning)
        self.assertTrue(ui.draft_can_save(
            draft, guild=guild, protected_ids=ctx.protected()
        ))
        self.assertFalse(next(
            item.disabled for item in editor.children
            if getattr(item, "label", None) == ctx.t("save")
        ))


    def test_confirmation_colors_match_action(self):
        import discord

        for lang in ("es-419", "en-US", "pt-BR"):
            self.host["guild_language"] = lambda gid, lang=lang: lang
            ctx = ui.Context(self.host, 10, 20)
            for action, expected in (
                ("save", discord.ButtonStyle.success),
                ("sync", discord.ButtonStyle.success),
                ("delete", discord.ButtonStyle.danger),
            ):
                view = ui.Confirmation(ctx, action, ui.new_draft())
                button = next(
                    item for item in view.children
                    if getattr(item, "label", None) == ctx.t({
                        "save": "confirm_save",
                        "sync": "confirm_sync",
                        "delete": "confirm_delete",
                    }[action])
                )
                self.assertEqual(button.style, expected)
                self.assertEqual(
                    sum(getattr(item, "label", "") == ctx.t("close")
                        for item in view.children),
                    1,
                )



    def test_sapphire_inspired_discord_summary_hierarchy(self):
        for lang in ("es-419", "en-US", "pt-BR"):
            self.host["guild_language"] = lambda gid, lang=lang: lang
            ctx = ui.Context(self.host, 10, 20)
            draft = ui.new_draft()
            draft["name"] = "Chico + Hétero"
            draft["target_role_id"] = 40
            draft["groups"][0]["conditions"] = [
                {"role_id": 10, "op": "has"},
                {"role_id": 20, "op": "has"},
            ]
            editor = ui.ConnectionEditor(ctx, draft)
            text = editor.summary(self.guild)
            self.assertIn(ctx.t("main_role"), text)
            self.assertIn(ctx.t("conditions_header") + " · 2/10", text)
            self.assertIn("> 1. ", text)
            self.assertIn("> **AND** 2. ", text)
            self.assertIn("<@&40>", text)
            self.assertIn("<@&10>", text)
            self.assertIn("<@&20>", text)
            self.assertLessEqual(len(text), 3900)
            draft["groups"].append({
                "mode": "any",
                "conditions": [{"role_id": 30, "op": "lacks"}],
            })
            advanced = ui.AdvancedGroups(ctx, draft)
            text = advanced.summary(self.guild)
            self.assertIn(ctx.t("group_overview"), text)
            self.assertIn("**OR**", text)
            self.assertIn("> 1. ", text)

    def test_list_renders_active_paused_and_compact_conditions(self):
        first = role_connections.Rule(
            "one", "Chico + Hétero", 40,
            ({"mode": "all", "conditions": [
                {"role_id": 10, "op": "has"}, {"role_id": 20, "op": "has"}
            ]},),
            "any", True, "rev1",
        )
        second = role_connections.Rule(
            "two", "Chica + Hétero", 41,
            ({"mode": "all", "conditions": [{"role_id": 11, "op": "has"}]},),
            "any", False, "rev2",
        )
        with unittest.mock.patch.object(self.ctx, "rules", return_value=[first, second]):
            panel = ui.ConnectionsList(self.ctx)
            body = panel.summary(self.guild)
        self.assertIn(self.ctx.t("list_total", count=2, limit=20), body)
        self.assertIn(self.ctx.t("enabled"), body)
        self.assertIn(self.ctx.t("disabled"), body)
        self.assertIn("**AND**", body)
        self.assertIn("<@&40>", body)
        self.assertIn("<@&41>", body)
        self.assertLessEqual(len(body), 3900)



    def test_operators_precede_the_condition_they_connect(self):
        for lang in ("es-419", "en-US", "pt-BR"):
            self.host["guild_language"] = lambda gid, lang=lang: lang
            ctx = ui.Context(self.host, 10, 20)
            first = {"role_id": 10, "op": "has"}
            second = {"role_id": 20, "op": "lacks"}
            third = {"role_id": 30, "op": "has"}
            for mode, word in (("all", "AND"), ("any", "OR")):
                draft = ui.new_draft()
                draft["groups"][0] = {
                    "mode": mode, "conditions": [first, second, third]
                }
                output = ui._format_groups(
                    ctx, self.guild, draft["groups"], "any"
                )
                self.assertIn("> 1. ", output)
                self.assertNotIn("> **" + word + "** 1.", output)
                self.assertIn(f"> **{word}** 2. ", output)
                self.assertIn(f"> **{word}** 3. ", output)
                self.assertNotIn(f"{word} ·", output)
            draft["groups"] = [
                {"mode": "all", "conditions": [first, second]},
                {"mode": "all", "conditions": [third, first]},
            ]
            draft["groups_mode"] = "any"
            advanced = ui.AdvancedGroups(ctx, draft)
            summary = advanced.summary(self.guild)
            self.assertIn("> **AND** 2. ", summary)
            self.assertIn("> **OR** 1. ", summary)
            self.assertNotIn("\\n**OR**\\n", summary)
            self.assertLessEqual(len(summary), 3900)

    def test_list_places_operator_before_second_condition_not_first(self):
        for mode, op in (("all", "AND"), ("any", "OR")):
            rule = role_connections.Rule(
                "demo", "example", 40,
                ({"mode": mode, "conditions": [
                    {"role_id": 10, "op": "has"},
                    {"role_id": 20, "op": "has"},
                ]},),
                "any", True, "rev",
            )
            with unittest.mock.patch.object(
                self.ctx, "rules", return_value=[rule]
            ):
                summary = ui.ConnectionsList(self.ctx).summary(self.guild)
            self.assertIn("> Tiene el rol <@&10>", summary)
            self.assertIn(f"> **{op}** Tiene el rol <@&20>", summary)
            self.assertNotIn(f"> **{op}** ·", summary)



if __name__ == "__main__":
    unittest.main()
