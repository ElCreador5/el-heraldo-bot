"""Regresiones de recordatorios optativos y formato de fechas."""
from i18n_source_helpers import source_text as _source_text
import ast
import unittest
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1] / "bot.py"


def source_function(name):
    tree = ast.parse(_source_text(SOURCE, encoding='utf-8'))
    node = next(node for node in tree.body
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name)
    return ast.unparse(node)


class ReminderAndDateFormatTests(unittest.TestCase):
    def test_defaults_do_not_publish(self):
        src = source_function("reminder_settings")
        self.assertIn("report_reminder_enabled", src)
        self.assertIn("'0'", src)

    def test_scheduled_delivery_claims_before_network(self):
        code = ast.unparse(ast.parse(_source_text(SOURCE, encoding='utf-8')))
        loop = code[code.index("async def report_reminders_loop"):code.index("async def before_report_reminders_loop")]
        self.assertLess(loop.index("conn.commit()"), loop.index("await channel.send("))
        self.assertIn("allowed_mentions=discord.AllowedMentions.none()", loop)
        self.assertIn("report_reminder_enabled", loop)
        self.assertIn("!= '1'", loop)

    def test_preview_excludes_staff_only_warning(self):
        src = source_function("reminder_preview")
        self.assertIn("item.get('action') == 'warn'", src)
        self.assertIn("moderation_report_reactions", src)
        self.assertNotIn("get_condemnation_emoji", src)

    def test_dates_do_not_modify_historical_cases(self):
        src = source_function("format_configured_datetime")
        self.assertIn("display_date_format", src)
        self.assertIn("America/Santo_Domingo", src)
        self.assertNotIn("db_connect", src)

    def test_reminder_view_saves_only_drafts_and_toggles_only_status(self):
        code = ast.unparse(ast.parse(_source_text(SOURCE, encoding='utf-8')))
        cls = code[code.index("class ReportReminderSetupView"):code.index("class HeraldoUserReportsSetupView")]
        self.assertIn("configuration_access(", cls)
        self.assertIn("verification_atomic_setup_save(", cls)
        self.assertNotIn("confirm_configuration(", cls)
        self.assertIn("reminder_preview(", cls)
        self.assertIn("report_reminder_enabled", cls)
        self.assertIn("self.original_raw", cls)
        self.assertIn("self.remove_item(day_select)", cls)

    def test_immediate_toggle_never_persists_uncommitted_frequency_or_channel(self):
        source = _source_text(SOURCE, encoding='utf-8')
        tree = ast.parse(source)
        cls = next(node for node in tree.body
                   if isinstance(node, ast.ClassDef) and node.name == "ReportReminderSetupView")
        handler = next(node for node in cls.body
                       if isinstance(node, ast.AsyncFunctionDef) and node.name == "toggle")
        code = ast.unparse(handler)
        self.assertIn("'report_reminder_enabled': next_state", code)
        self.assertNotIn("self.pending.items()", code)
        self.assertIn("self.original[", code)

    def test_save_never_changes_enabled_state_and_returns_to_editor(self):
        source = _source_text(SOURCE, encoding='utf-8')
        tree = ast.parse(source)
        cls = next(node for node in tree.body
                   if isinstance(node, ast.ClassDef) and node.name == "ReportReminderSetupView")
        handler = next(node for node in cls.body
                       if isinstance(node, ast.AsyncFunctionDef) and node.name == "confirm")
        code = ast.unparse(handler)
        self.assertIn("k != 'report_reminder_enabled'", code)
        self.assertIn("verification_atomic_setup_save(", code)
        self.assertIn("interaction.response.edit_message(", code)

    def test_custom_modal_refreshes_frequency_and_hides_unrelated_day(self):
        source = _source_text(SOURCE, encoding='utf-8')
        code = ast.unparse(ast.parse(source))
        modal = code[code.index("class ReportReminderOptionsModal"):code.index("class ReportReminderSetupView")]
        self.assertIn("self.parent._refresh_controls()", modal)
        view = code[code.index("class ReportReminderSetupView"):code.index("class HeraldoUserReportsSetupView")]
        self.assertIn("self.pending['report_reminder_frequency'] == 'weekly'", view)
        self.assertIn("self.remove_item(day_select)", view)

    def test_estimated_due_prefers_saved_scheduler_timestamp(self):
        source = _source_text(SOURCE, encoding='utf-8')
        code = ast.unparse(ast.parse(source))
        view = code[code.index("class ReportReminderSetupView"):code.index("class HeraldoUserReportsSetupView")]
        self.assertIn("guild_config_get(self.guild_id, 'report_reminder_next_due')", view)
        self.assertIn("guild_config_get(self.guild_id, 'report_reminder_signature')", view)

    def test_date_selector_only_updates_draft(self):
        source = _source_text(SOURCE, encoding='utf-8')
        tree = ast.parse(source)
        cls = next(node for node in tree.body if isinstance(node, ast.ClassDef)
                   and node.name == "HeraldoDateFormatSetupView")
        handler = next(node for node in cls.body if isinstance(node, ast.AsyncFunctionDef)
                       and node.name == "select_format")
        code = ast.unparse(handler)
        self.assertIn("self.pending = value", code)
        self.assertIn("Borrador SIN GUARDAR", code)
        self.assertNotIn("guild_config_set", code)
        self.assertNotIn("confirm_configuration(", code)

    def test_short_intervals_are_test_only(self):
        code = ast.unparse(ast.parse(_source_text(SOURCE, encoding='utf-8')))
        modal = code[code.index("class ReportReminderOptionsModal"):code.index("class ReportReminderSetupView")]
        self.assertIn("is_test = heraldo_is_test()", modal)
        self.assertIn("unit == 's' and (not is_test)", modal)
        self.assertIn("report_reminder_interval", modal)
        self.assertNotIn("guild_config_set", modal)

    def test_next_due_computes_time_without_an_undefined_minute(self):
        from datetime import datetime, timezone
        from test_safety_regressions import b

        schedule = {
            "report_reminder_hour": "12",
            "report_reminder_day": "1",
            "report_reminder_frequency": "daily",
            "report_reminder_interval": "7d",
            "report_reminder_start": "",
        }
        # 18:00 UTC = 14:00 Santo Domingo: next daily reminder is tomorrow noon.
        now = datetime(2026, 11, 3, 18, 0, tzinfo=timezone.utc)
        self.assertEqual(
            b.reminder_next_due(schedule, now),
            datetime(2026, 11, 4, 16, 0, tzinfo=timezone.utc),
        )
        # At the same time on Tuesday, a weekly Tuesday reminder is next week.
        schedule["report_reminder_frequency"] = "weekly"
        self.assertEqual(
            b.reminder_next_due(schedule, now),
            datetime(2026, 11, 10, 16, 0, tzinfo=timezone.utc),
        )

    def test_custom_schedule_skips_elapsed_intervals(self):
        """Old starts with 10-second cadence must not cause long catch-up loops."""
        src = source_function("reminder_next_due")
        self.assertIn("steps = int(elapsed // seconds) + 1", src)
        self.assertIn("candidate += timedelta(seconds=steps * seconds)", src)
        self.assertLess(src.index("steps = int("), src.index("while candidate <= local:"))

    def test_reminder_custom_start_respects_exact_minute_and_legacy_dates(self):
        from datetime import datetime, timezone
        from test_safety_regressions import b
        settings = {
            "report_reminder_frequency": "custom",
            "report_reminder_hour": "12",
            "report_reminder_day": "0",
            "report_reminder_interval": "2m",
            "report_reminder_start": "2026-11-04 22:30",
        }
        # El primer mensaje sale exactamente a las 22:30, hora dominicana.
        before = datetime(2026, 11, 5, 2, 29, tzinfo=timezone.utc)
        self.assertEqual(
            b.reminder_next_due(settings, before),
            datetime(2026, 11, 5, 2, 30, tzinfo=timezone.utc),
        )
        after = datetime(2026, 11, 5, 2, 35, tzinfo=timezone.utc)
        self.assertEqual(
            b.reminder_next_due(settings, after),
            datetime(2026, 11, 5, 2, 36, tzinfo=timezone.utc),
        )
        # Los horarios ya guardados como solo fecha siguen funcionando.
        settings.update(report_reminder_interval="7d", report_reminder_start="2026-11-04")
        self.assertEqual(
            b.reminder_next_due(settings, before),
            datetime(2026, 11, 11, 16, 0, tzinfo=timezone.utc),
        )

    def test_open_reminder_configuration_has_no_preselected_controls_or_modal_values(self):
        from test_safety_regressions import b
        guild = 3819929
        b.guild_config_set(guild, "report_reminder_frequency", "custom")
        b.guild_config_set(guild, "report_reminder_interval", "7h")
        b.guild_config_set(guild, "report_reminder_channel", "12345")
        b.guild_config_set(guild, "report_reminder_start", "2026-11-04 22:30")
        view = b.ReportReminderSetupView(guild, 10)
        self.assertEqual(view.selected_fields, set())
        self.assertEqual(view.channel_select.default_values, [])
        self.assertFalse(any(o.default for o in view.selectors["report_reminder_frequency"].options))
        self.assertFalse(any(o.default for o in view.selectors["report_reminder_hour"].options))
        modal = b.ReportReminderOptionsModal(view)
        self.assertFalse(modal.days.default)
        self.assertFalse(modal.date.default)
        self.assertFalse(modal.clock.default)
        self.assertEqual(view.pending["report_reminder_interval"], "7h")
        view.selected_fields.add("report_reminder_frequency")
        view._refresh_controls()
        self.assertEqual(sum(o.default for o in view.selectors["report_reminder_frequency"].options), 1)
        view.stop()

    def test_layout_includes_both_new_views(self):
        src = source_function("validate_setup_view_layouts")
        self.assertIn("ReportReminderSetupView", src)
        self.assertIn("HeraldoDateFormatSetupView", src)


if __name__ == "__main__":
    unittest.main()
