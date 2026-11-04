"""Regresiones aisladas para la promoción selectiva de idioma y recordatorios."""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock

import discord
import heraldo_i18n as locale
from production_language_panel import LanguageSettingsView
from production_report_reminder_ui import ReminderEditorView, ReminderHomeView
from production_report_reminders import (
    reminder_preview, reminder_next_due, reminder_settings, _is_reminder,
    _load_refs, record_publication, _due_claim,
)
from production_report_labels import DEFAULTS


class FakeSettings:
    def __init__(self):
        self.ctx = TemporaryDirectory()
        self.path = Path(self.ctx.name) / "test.db"
        with self.conn() as db:
            db.execute(
                "CREATE TABLE guild_settings (guild_id INTEGER NOT NULL,"
                "key TEXT NOT NULL,value TEXT,"
                "PRIMARY KEY(guild_id,key))"
            )
        self.rules = [
            {"emoji": emoji, "label": DEFAULTS[emoji]["es-419"],
             "action": "report", "threshold": threshold}
            for emoji, threshold in [
                ("📢", 2), ("🚩", 3), ("🤓", 2), ("🔞", 2),
            ]
        ]
        self.host = {
            "get": self.get, "set": self.set,
            "connect": self.conn, "language": self.language,
            "reactions": lambda guild_id: list(self.rules),
            "format_datetime": lambda guild_id, dt: dt.isoformat(),
            "stamp": lambda embed, guild: embed,
            "check_access": AsyncMock(return_value=True),
            "return_reports": AsyncMock(),
        }

    def conn(self):
        return sqlite3.connect(self.path, isolation_level=None)

    def get(self, guild_id, key):
        con = self.conn()
        try:
            row = con.execute(
                "SELECT value FROM guild_settings WHERE guild_id=? AND key=?",
                (guild_id, key),
            ).fetchone()
            return row[0] if row else None
        finally:
            con.close()

    def set(self, guild_id, key, value):
        with self.conn() as db:
            db.execute(
                "INSERT INTO guild_settings(guild_id,key,value) VALUES(?,?,?) "
                "ON CONFLICT(guild_id,key) DO UPDATE SET value=excluded.value",
                (guild_id, key, value),
            )

    def language(self, guild_id):
        return self.get(guild_id, "language") or "es-419"

    def close(self):
        self.ctx.cleanup()


class LocaleReminderTests(unittest.TestCase):
    def setUp(self):
        self.db = FakeSettings()

    def tearDown(self):
        self.db.close()

    def test_loaded_catalogs_and_no_missing_translation(self):
        locale.verify_catalogs()
        self.assertEqual(set(locale.TARGET_LOCALES),
                         {"es-419", "en-US", "pt-BR"})

    def test_preview_english_translates_only_default_labels(self):
        self.db.set(10, "language", "en-US")
        preview = reminder_preview(10, self.db.host)
        self.assertIn("How to help with moderation", preview)
        self.assertIn("Inappropriate content / not permitted", preview)
        self.assertNotIn("Contenido inapropiado / no permitido", preview)
        self.db.rules[1]["label"] = "Comentario del administrador"
        self.assertIn("Comentario del administrador", reminder_preview(10, self.db.host))

    def test_preview_portuguese(self):
        self.db.set(10, "language", "pt-BR")
        preview = reminder_preview(10, self.db.host)
        self.assertIn("Como colaborar com a moderação", preview)
        self.assertIn("Suspeito (possível conta falsa ou fraude)", preview)

    def test_disabled_default_and_daily_schedule(self):
        settings = reminder_settings(10, self.db.get)
        self.assertEqual(settings["report_reminder_enabled"], "0")
        settings["report_reminder_frequency"] = "daily"
        settings["report_reminder_hour"] = "12"
        self.assertEqual(
            reminder_next_due(settings, datetime(2026, 11, 4, 18, tzinfo=timezone.utc)),
            datetime(2026, 11, 5, 16, tzinfo=timezone.utc),
        )

    def test_custom_interval_never_catches_up_multiple_messages(self):
        settings = reminder_settings(10, self.db.get)
        settings.update(report_reminder_frequency="custom",
                        report_reminder_interval="2d",
                        report_reminder_start="2026-10-01 12:00")
        due = reminder_next_due(settings, datetime(2026, 11, 4, 18, tzinfo=timezone.utc))
        self.assertGreater(due, datetime(2026, 11, 4, 18, tzinfo=timezone.utc))
        self.assertLessEqual(due, datetime(2026, 11, 6, 18, tzinfo=timezone.utc))

    def test_index_keeps_message_ids_and_filters_invalid_refs(self):
        record_publication(10, 20, 100, self.db.host)
        record_publication(10, 20, 100, self.db.host)
        record_publication(10, 20, 101, self.db.host)
        self.assertEqual(_load_refs(10, self.db.get), [(20, 100), (20, 101)])

    def test_claim_sends_never_on_first_check_and_only_once_when_due(self):
        cfg = reminder_settings(10, self.db.get)
        cfg["report_reminder_enabled"] = "1"
        now = datetime(2026, 11, 4, 18, tzinfo=timezone.utc)
        self.assertFalse(_due_claim(10, cfg, self.db.host, now))
        self.assertTrue(_due_claim(10, cfg, self.db.host, now.replace(day=17)))
        self.assertFalse(_due_claim(10, cfg, self.db.host, now.replace(day=17)))

    def test_recognition_never_touches_arbitrary_user_embeds(self):
        bad = SimpleNamespace(
            content="", embeds=[discord.Embed(description="Comentarios escritos por usuario.")],
        )
        self.assertFalse(_is_reminder(bad))
        self.db.set(10, "language", "en-US")
        known = SimpleNamespace(content=reminder_preview(10, self.db.host), embeds=[])
        self.assertTrue(_is_reminder(known))

    def test_selector_preserves_choice_and_bottom_navigation(self):
        host = self.db.host
        host.update({
            "get_language": self.db.language, "set_language": self.db.set,
            "return_home": AsyncMock(), "on_changed": AsyncMock(),
        })
        lang = LanguageSettingsView(10, 99, host)
        self.assertEqual([x.label for x in lang.children if isinstance(x, discord.ui.Button)],
                         ["Volver", "Cerrar"])
        editor = ReminderEditorView(10, 99, host)
        self.assertTrue(editor.save.disabled)
        self.assertEqual(len(editor.frequency_select.options), 5)
        self.assertEqual(editor.channel_select.row, 3)
        panel = ReminderHomeView(10, 99, host)
        self.assertEqual([x.label for x in panel.children if isinstance(x, discord.ui.Button)],
                         ["Volver", "Editar horario", "Vista previa", "Activar", "Cerrar"])


class LanguageSaveTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.db = FakeSettings()
        self.host = {
            "get_language": self.db.language, "set_language": self.db.set,
            "check_access": AsyncMock(return_value=True),
            "return_home": AsyncMock(), "on_changed": AsyncMock(),
        }

    async def asyncTearDown(self):
        self.db.close()

    async def test_selection_without_save_never_persists(self):
        panel = LanguageSettingsView(10, 99, self.host)
        interaction = SimpleNamespace(
            data={"values": ["en-US"]},
            response=SimpleNamespace(edit_message=AsyncMock(), send_message=AsyncMock()),
            guild=None,
        )
        await panel.select_language(interaction)
        self.assertEqual(self.db.language(10), "es-419")
        self.assertEqual(panel.pending, "en-US")
        await panel.discard.callback(interaction)
        self.assertEqual(panel.pending, "es-419")
        self.assertEqual(self.db.language(10), "es-419")

    async def test_language_saved_after_confirmation(self):
        panel = LanguageSettingsView(10, 99, self.host)
        interaction = SimpleNamespace(
            data={"values": ["pt-BR"]},
            response=SimpleNamespace(edit_message=AsyncMock(), send_message=AsyncMock()),
            guild=None,
        )
        await panel.select_language(interaction)
        await panel.save.callback(interaction)
        self.assertEqual(self.db.language(10), "pt-BR")


if __name__ == "__main__":
    unittest.main()
