"""Regresión del cambio de idioma retroactivo sin tocar texto de miembros."""
import sqlite3
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

import heraldo_i18n as i18n
import message_locale_sync as locale_sync
from message_payload import TemplateEmbeds


class LocaleHistoryTests(TestCase):
    def test_exact_system_phrase(self):
        value, changed = locale_sync.localize_text(
            "Guardar cambios", "es-419", "en-US")
        self.assertTrue(changed)
        self.assertEqual(value, "Save changes")

    def test_dynamic_value_is_preserved_verbatim(self):
        value, changed = locale_sync.localize_text(
            "Actual: No respetó las reglas del canal.",
            "es-419", "en-US")
        self.assertTrue(changed)
        self.assertEqual(value, "Current: No respetó las reglas del canal.")

    def test_unrecognized_member_text_is_not_translated(self):
        message = "El moderador escribió: Guardar cambios, por favor."
        self.assertEqual(
            locale_sync.localize_text(message, "es-419", "en-US"),
            (message, False),
        )

    def test_separate_system_line_only(self):
        value, changed = locale_sync.localize_text(
            "Guardar cambios\nMotivo: El usuario escribió algo privado.",
            "es-419", "en-US",
        )
        self.assertTrue(changed)
        self.assertEqual(
            value, "Save changes\nMotivo: El usuario escribió algo privado.")

    def test_no_changed_locale_never_rewrites(self):
        original = "Guardar cambios"
        self.assertEqual(
            locale_sync.localize_text(original, "es-419", "es-419"),
            (original, False),
        )

    def test_tracking_skips_personal_and_custom_templates(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "test.db"
            def connect():
                db = sqlite3.connect(path, isolation_level=None)
                db.execute("CREATE TABLE IF NOT EXISTS guild_settings "
                           "(guild_id INTEGER NOT NULL,key TEXT NOT NULL,"
                           "value TEXT,PRIMARY KEY(guild_id,key))")
                return db
            guild = SimpleNamespace(id=10)
            channel = SimpleNamespace(id=20, guild=guild)
            msg = SimpleNamespace(id=30, channel=channel, guild=guild)
            with patch.object(i18n, "_locale_resolver", lambda _: "es-419"):
                with locale_sync.suspend_tracking():
                    locale_sync.note_sent(msg, guild, "Guardar cambios", {}, connect)
                self.assertEqual(locale_sync._tracked(10, connect), [])
                locale_sync.note_sent(
                    msg, guild, "Guardar cambios",
                    {"embeds": TemplateEmbeds([])}, connect)
                self.assertEqual(locale_sync._tracked(10, connect), [])
                locale_sync.note_sent(msg, guild, "Guardar cambios", {}, connect)
                self.assertEqual(locale_sync._tracked(10, connect),
                                 [(20, 30, "es-419")])


if __name__ == "__main__":
    import unittest
    unittest.main()
