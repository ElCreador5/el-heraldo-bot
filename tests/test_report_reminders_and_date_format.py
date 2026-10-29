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

    def test_reminder_view_requires_confirmation(self):
        code = ast.unparse(ast.parse(_source_text(SOURCE, encoding='utf-8')))
        cls = code[code.index("class ReportReminderSetupView"):code.index("class HeraldoUserReportsSetupView")]
        self.assertIn("confirm_configuration(", cls)
        self.assertIn("configuration_access(", cls)
        self.assertIn("No hay cambios pendientes.", cls)
        self.assertIn("reminder_preview(", cls)

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

    def test_custom_schedule_skips_elapsed_intervals(self):
        """Old starts with 10-second cadence must not cause long catch-up loops."""
        src = source_function("reminder_next_due")
        self.assertIn("steps = int(elapsed // seconds) + 1", src)
        self.assertIn("candidate += timedelta(seconds=steps * seconds)", src)
        self.assertLess(src.index("steps = int("), src.index("while candidate <= local:"))

    def test_layout_includes_both_new_views(self):
        src = source_function("validate_setup_view_layouts")
        self.assertIn("ReportReminderSetupView", src)
        self.assertIn("HeraldoDateFormatSetupView", src)


if __name__ == "__main__":
    unittest.main()
