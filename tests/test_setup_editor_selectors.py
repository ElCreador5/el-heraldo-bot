"""Regresiones estructurales de los editores de configuración de /setup.

No se importa bot.py ni se conecta Discord durante estas pruebas.
"""
import ast
from pathlib import Path
import unittest

BOT = Path(__file__).resolve().parents[1] / "bot.py"
TREE = ast.parse(BOT.read_text(encoding="utf-8"))


def cls(name):
    return next(n for n in TREE.body if isinstance(n, ast.ClassDef) and n.name == name)


def method(name, item):
    return next(n for n in cls(name).body
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == item)


class MotwSelectorTests(unittest.TestCase):
    def test_day_and_hour_are_dropdowns_with_valid_ranges(self):
        node = cls("HeraldoMotwScheduleSelectView")
        init = ast.unparse(method(node.name, "__init__"))
        self.assertEqual(init.count("discord.ui.Select("), 2)
        self.assertIn("enumerate(MOTW_WEEKDAY_NAMES)", init)
        self.assertIn("range(24)", init)
        self.assertIn("row=0", init)
        self.assertIn("row=1", init)
        self.assertNotIn("discord.ui.TextInput", ast.unparse(node))

    def test_preview_cancel_and_explicit_confirmation(self):
        node = cls("HeraldoMotwScheduleSelectView")
        self.assertIn("original_weekday", ast.unparse(method(node.name, "_summary")))
        self.assertIn("get_motw_hour", ast.unparse(method(node.name, "review")))
        self.assertIn("confirm_configuration", ast.unparse(method(node.name, "review")))
        self.assertIn("self.stop()", ast.unparse(method(node.name, "cancel")))
        self.assertNotIn("guild_config_set", ast.unparse(node))
        self.assertNotIn("set_motw_channel_id", ast.unparse(node))
        self.assertIn("configuration_access", ast.unparse(method(node.name, "interaction_check")))

    def test_editor_opens_one_stateful_selector(self):
        schedule = ast.unparse(method("HeraldoMotwSetupView", "schedule"))
        self.assertIn("schedule_view = HeraldoMotwScheduleSelectView", schedule)
        self.assertIn("content=schedule_view._summary()", schedule)
        self.assertIn("view=schedule_view", schedule)
        self.assertNotIn("send_modal", schedule)


class ModerationRuleSelectorTests(unittest.TestCase):
    def test_action_is_whitelisted_selector_not_free_text(self):
        code = ast.unparse(method("HeraldoUserReportsSetupView", "_rebuild_action_select"))
        self.assertIn("discord.ui.Select(", code)
        for action in ("report", "warn", "timeout", "condemn", "kick", "ban"):
            self.assertIn(action, code)
        self.assertIn("disabled=selected is None", code)
        self.assertIn("row=2", code)
        modal = ast.unparse(cls("ModerationReactionRuleModal"))
        self.assertNotIn("self.action.default", modal)
        self.assertNotIn("¿Qué debe hacer el bot?", modal)
        self.assertIn("self.parent_view._working_reactions()", modal)

    def test_selection_only_updates_draft_and_removes_destructive_purge(self):
        code = ast.unparse(method("HeraldoUserReportsSetupView", "select_action"))
        self.assertIn("MODERATION_REPORT_ACTIONS", code)
        self.assertIn("self.pending_reactions = reactions", code)
        self.assertIn("reactions[index]['purge_minutes'] = None", code)
        self.assertNotIn("guild_config_set", code)
        self.assertNotIn("set_moderation_report_reactions", code)

    def test_save_revalidates_rules_and_channel(self):
        code = ast.unparse(method("HeraldoUserReportsSetupView", "save_changes"))
        self.assertIn('action == "timeout"', code.replace("'", '"'))
        self.assertIn('action in {"report", "warn"}', code.replace("'", '"'))
        self.assertIn("MODERATION_REPORT_ACTIONS", code)
        self.assertIn("channel.permissions_for(me)", code)
        self.assertIn("isinstance(channel, discord.TextChannel)", code)
        view = ast.unparse(cls("HeraldoUserReportsSetupView"))
        self.assertIn("style=discord.ButtonStyle.secondary, row=4", view)


    def test_report_modals_recheck_permissions_and_reject_stale_drafts(self):
        for name in ("ModerationReactionEditModal", "ModerationReactionRuleModal"):
            code = ast.unparse(cls(name))
            self.assertIn("original_item", code)
            submit = ast.unparse(method(name, "on_submit"))
            self.assertIn("self.parent_view.interaction_check(interaction)", submit)
            self.assertIn("current[self.index] != self.original_item", submit)
        emoji = ast.unparse(method("ModerationCondemnEmojiModal", "on_submit"))
        self.assertIn("self.parent_view.interaction_check(interaction)", emoji)


if __name__ == "__main__":
    unittest.main()
