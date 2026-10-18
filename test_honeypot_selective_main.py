"""Regresiones de aislamiento y privacidad del backport Honeypot en main.

No importa bot.py ni conecta a Discord o SQLite productivos.
"""
import ast
from pathlib import Path
import unittest

SOURCE = Path(__file__).with_name("bot.py").read_text(encoding="utf-8")
TREE = ast.parse(SOURCE)


def definition(name):
    matches = [node for node in TREE.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name]
    assert len(matches) == 1, (name, len(matches))
    return ast.get_source_segment(SOURCE, matches[0])


class HoneypotSelectiveMainTests(unittest.TestCase):
    def test_misfire_guard_precedes_message_deletion(self):
        func = definition("hp_handle_trigger")
        self.assertLess(func.index("if len(affected) >= HONEYPOT_MISFIRE_THRESHOLD"), func.index("await message.delete()"))
        self.assertIn("item[1] != guild.id", func)
        self.assertIn("guild_id == guild.id", func)

    def test_report_only_never_deletes_disparador(self):
        self.assertIn('if action != "log":', definition("hp_handle_trigger"))
        self.assertIn('if hp_action(message.guild.id) != "log":', SOURCE)

    def test_history_and_logs_do_not_capture_message(self):
        func = definition("hp_log_trigger")
        self.assertIn('channel_id, "", action', func)
        report = definition("hp_report")
        self.assertNotIn("message.content", report)
        self.assertNotIn('name="Mensaje"', report)
        self.assertNotIn("attachments", report)

    def test_honeypot_skips_evidence_without_skipping_cases(self):
        func = definition("_condemn_member_inner")
        self.assertIn('if origin == "honeypot":', func)
        self.assertIn("evidence_url, evidence_text = None, None", func)
        self.assertIn('include_message_history=(origin != "honeypot")', func)
        self.assertIn("moderation_case_create(", func)

    def test_existing_moderation_retains_history(self):
        func = definition("moderation_case_create")
        self.assertIn("include_message_history: bool = True", func)
        self.assertIn("if include_message_history else None", func)

    def test_inflight_is_guild_scoped(self):
        self.assertIn("key = (message.guild.id, member.id)", definition("honeypot_listener"))
        self.assertIn("_hp_busy.add(key)", definition("honeypot_listener"))
        self.assertIn("_hp_busy.discard(key)", definition("honeypot_listener"))


    def test_sanctions_require_explicit_storage(self):
        value = definition("hp_action")
        self.assertIn('"kick_enabled"', value)
        self.assertIn('"ban_enabled"', value)
        self.assertIn('return "role"', value)

    def test_kick_purges_by_author_without_discord_delete_messages(self):
        fn = definition("hp_punish")
        self.assertIn("await member.kick(reason=reason)", fn)
        self.assertIn("run_purge_job(", fn)
        self.assertIn("hp_kick_purge_minutes(guild.id)", fn)
        self.assertNotIn("delete_message_days", fn)

    def test_ban_explicit_duration_and_case(self):
        fn = definition("hp_punish")
        self.assertIn("hp_ban_override_minutes(guild.id)", fn)
        self.assertIn("if duration is None:", fn)
        self.assertIn("delete_message_seconds=0", fn)
        self.assertIn("include_message_history=False", fn)

    def test_sanction_permissions_and_hierarchy(self):
        fn = definition("hp_punish")
        self.assertIn("hp_sanction_permission_problem", fn)
        self.assertIn("member.id == guild.owner_id", fn)
        self.assertIn("member.top_role >= me.top_role", fn)

    def test_kick_purge_minimum_is_one_day(self):
        fn = definition("hp_kick_purge_minutes")
        self.assertIn("minutes if 1440 <= minutes <= 30 * 1440 else 1440", fn)


if __name__ == "__main__":
    unittest.main()
