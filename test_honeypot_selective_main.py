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
        self.assertIn('"ban_enabled"', SOURCE)
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


    def test_storage_values_are_safe_in_execution(self):
        code = compile(definition("hp_action"), "<isolated-honeypot-action>", "exec")
        for stored, wanted in (
            ("kick", "role"), ("ban", "role"), ("kick_enabled", "kick"),
            ("ban_enabled", "ban"), ("log", "log"), ("timeout", "timeout"),
            ("role", "role"), (None, "role"),
        ):
            namespace = {
                "hp_setting_get": lambda guild_id, name, value=stored: value,
                "HONEYPOT_DESTRUCTIVE_ACTION_STORAGE": {
                    "kick": "kick_enabled", "ban": "ban_enabled",
                },
            }
            exec(code, namespace)
            self.assertEqual(namespace["hp_action"](123), wanted)

    def test_setup_save_is_explicit_and_revalidated(self):
        panel = SOURCE[
            SOURCE.index("class HeraldoHoneypotSetupView("):
            SOURCE.index("class HoneypotPublishWarningConfirmView(")
        ]
        self.assertIn("Guardar cambios", panel)
        self.assertIn("Descartar cambios", panel)
        self.assertIn("pending_action", panel)
        self.assertIn("pending_ban_minutes", panel)
        self.assertIn("pending_kick_purge_minutes", panel)
        self.assertIn("self._snapshot() != self._original_config", panel)
        self.assertIn("hp_action_storage(self.pending_action)", panel)
        select = panel[panel.index("async def select_action"):panel.index("async def interaction_check")]
        self.assertNotIn("hp_setting_set(", select)

    def test_notice_publication_requires_confirmation_and_rechecks(self):
        code = SOURCE[
            SOURCE.index("class HoneypotPublishWarningConfirmView("):
            SOURCE.index("class HoneypotCreateChannelConfirmView(")
        ]
        self.assertIn("Confirmar publicación", code)
        self.assertIn("self.original_notice", code)
        self.assertIn("self.original_traps", code)
        self.assertIn("hp_sync_all_warnings(guild)", code)
        self.assertIn("self.finished = True", code)
        self.assertIn("read_message_history", code)
        self.assertIn("Cancelar", code)

    def test_new_channel_requires_confirmation_and_revalidates(self):
        code = SOURCE[
            SOURCE.index("class HoneypotCreateChannelConfirmView("):
            SOURCE.index("def heraldo_permissions_summary(")
        ]
        self.assertIn("Confirmar", code)
        self.assertIn("self.original_traps", code)
        self.assertIn("guild.create_text_channel(", code)
        self.assertIn("_setup_apply_system_channel(", code)
        self.assertIn("Cancelar", code)

    def test_notice_modals_only_prepare_confirmation(self):
        text = SOURCE[
            SOURCE.index("class HoneypotWarningModal("):
            SOURCE.index("@honeypot_group.command(name=\"setup\"")
        ]
        embed = SOURCE[
            SOURCE.index("class HoneypotWarningEmbedModal("):
            SOURCE.index("@honeypot_group.command(name=\"warning_embed\"")
        ]
        for modal in (text, embed):
            submit = modal[modal.index("async def on_submit"): ]
            self.assertIn("HoneypotNoticeEditConfirmView(", submit)
            self.assertNotIn("hp_setting_set(", submit)
            self.assertNotIn("hp_sync_all_warnings(", submit)
        confirm = SOURCE[
            SOURCE.index("class HoneypotNoticeEditConfirmView("):
            SOURCE.index("class HoneypotWarningModal(")
        ]
        self.assertIn("self.finished", confirm)
        self.assertIn("hp_setting_set(", confirm)
        self.assertIn("La configuración cambió", confirm)
        cancel = confirm[confirm.index("async def cancel"):]
        self.assertNotIn("hp_setting_set(", cancel)

if __name__ == "__main__":
    unittest.main()
