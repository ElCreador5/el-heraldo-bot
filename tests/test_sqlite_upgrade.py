"""Regresiones del verificador: fallos inyectados solo en SQLite sintético."""
from contextlib import closing
from pathlib import Path
import sqlite3
import tempfile
import unittest

from tools.check_sqlite_upgrade import initialize_candidate, rehearse


DDL = '''
CREATE TABLE IF NOT EXISTS guild_settings(guild_id INTEGER, key TEXT, value TEXT);
CREATE TABLE IF NOT EXISTS guild_cases(guild_id INTEGER, user_id INTEGER,
    role_ids TEXT, reason TEXT, condemned_at TEXT, origin TEXT);
CREATE TABLE IF NOT EXISTS guild_members(guild_id INTEGER, user_id INTEGER,
    verify_pending_at TEXT, PRIMARY KEY(guild_id,user_id));
CREATE UNIQUE INDEX IF NOT EXISTS settings_guard ON guild_settings(guild_id,key);
CREATE VIEW IF NOT EXISTS settings_view AS SELECT * FROM guild_settings;
CREATE TRIGGER IF NOT EXISTS settings_trigger BEFORE DELETE ON guild_settings
    BEGIN SELECT RAISE(ABORT, 'protected'); END;
'''


def source(extra=''):
    # Misma interfaz que los cuatro inicializadores extraídos del bot.
    return f'''
def db_connect():
    return sqlite3.connect(DB_PATH, isolation_level=None)
def db_init():
    conn = db_connect()
    conn.executescript({(DDL + extra)!r})
    conn.close()
def honeypot_db_init():
    pass
def suggestion_db_init():
    pass
'''


class UpgradeTests(unittest.TestCase):
    def test_additive_upgrade_preserves_constraints_and_restores_snapshot(self):
        result = rehearse(source(), source('CREATE TABLE IF NOT EXISTS new_table(id);'))
        for key in ('existing_rows_preserved', 'existing_columns_unchanged',
                    'existing_schema_objects_preserved', 'schema_versions_unchanged',
                    'integrity_and_foreign_keys_ok', 'startup_idempotent',
                    'old_initializers_preserve_upgraded_db', 'snapshot_rollback_exact'):
            self.assertTrue(result[key], key)
        self.assertIn('new_table', result['added_tables'])

    def test_lost_index_trigger_or_view_blocks_even_when_rows_and_columns_match(self):
        for sql in ('DROP INDEX IF EXISTS settings_guard;',
                    'DROP TRIGGER IF EXISTS settings_trigger;',
                    'DROP VIEW IF EXISTS settings_view;'):
            with self.subTest(sql=sql), self.assertRaisesRegex(RuntimeError, 'compatibility_failed'):
                rehearse(source(), source(sql))

    def test_unreviewed_schema_version_or_application_id_change_blocks(self):
        for name in ('user_version', 'application_id'):
            with self.subTest(name=name), self.assertRaisesRegex(RuntimeError, 'compatibility_failed'):
                rehearse(source(), source(f'PRAGMA {name}=999;'))

    def test_invalid_foreign_key_in_new_table_blocks(self):
        # Idempotente y sin modificar filas previas; antes era aceptado.
        with self.assertRaisesRegex(RuntimeError, 'compatibility_failed'):
            rehearse(source(), source('''
                CREATE TABLE IF NOT EXISTS invalid_fk(id PRIMARY KEY REFERENCES missing(id));
                INSERT OR IGNORE INTO invalid_fk VALUES(42);
            '''))

    def test_data_loss_blocks(self):
        with self.assertRaisesRegex(RuntimeError, 'compatibility_failed'):
            rehearse(source(), source('DELETE FROM guild_cases;'))

    def test_module_startup_commits_uncertain_send_and_repeats_safely(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'synthetic.db'
            initialize_candidate(source(), path)
            with closing(sqlite3.connect(path)) as conn:
                conn.execute("INSERT INTO message_schedule_state(guild_id,job_id,status) VALUES(101,'job','sending')")
                conn.commit()
            initialize_candidate(source(), path)
            initialize_candidate(source(), path)
            with closing(sqlite3.connect(path)) as conn:
                self.assertEqual(conn.execute('SELECT status FROM message_schedule_state').fetchall(),
                                 [('uncertain',)])
                self.assertEqual(conn.execute('SELECT count(*) FROM evidence_archive_v1').fetchone(), (1,))
