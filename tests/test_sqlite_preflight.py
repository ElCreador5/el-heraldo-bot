import contextlib
import io
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

import sqlite_preflight as p


class PreflightTests(unittest.TestCase):
    def test_wal_committed_data_is_checked_without_disclosing_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'private.db'
            with contextlib.closing(sqlite3.connect(path)) as c:
                c.execute('PRAGMA journal_mode=WAL')
                c.execute('CREATE TABLE private (secret TEXT)')
                c.execute("INSERT INTO private VALUES ('sensitive-content')")
                c.commit()
                before = c.execute('SELECT * FROM private').fetchall()
                output = io.StringIO()
                with contextlib.redirect_stdout(output):
                    self.assertEqual(p.main(['--db', str(path)]), 0)
                self.assertIn('"wal_present": true', output.getvalue())
                self.assertNotIn('sensitive-content', output.getvalue())
                self.assertNotIn(str(path), output.getvalue())
                self.assertEqual(before, c.execute('SELECT * FROM private').fetchall())

    def test_missing_database_is_not_created(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'absent.db'
            with contextlib.redirect_stdout(io.StringIO()) as out:
                self.assertEqual(p.main(['--db', str(path)]), 1)
            self.assertFalse(path.exists())
            self.assertNotIn(tmp, out.getvalue())

    def test_corrupt_or_empty_database_blocks_without_raw_errors(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'db'
            for content in (b'', b'private-corruption'):
                path.write_bytes(content)
                with contextlib.redirect_stdout(io.StringIO()) as out:
                    self.assertEqual(p.main(['--db', str(path)]), 1)
                self.assertNotIn('private-corruption', out.getvalue())

    def test_foreign_key_violation_blocks(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'db'
            with contextlib.closing(sqlite3.connect(path)) as c:
                c.executescript('CREATE TABLE parent(id PRIMARY KEY); '
                                'CREATE TABLE child(id REFERENCES parent(id)); '
                                'INSERT INTO child VALUES (1);')
            with contextlib.redirect_stdout(io.StringIO()) as out:
                self.assertEqual(p.main(['--db', str(path)]), 1)
            self.assertIn('"foreign_keys_ok": false', out.getvalue())

    def test_circular_symlink_blocks_without_private_path_or_traceback(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'private-name'
            path.symlink_to(path)
            with contextlib.redirect_stdout(io.StringIO()) as out:
                self.assertEqual(p.main(['--db', str(path)]), 1)
            self.assertEqual(json.loads(out.getvalue()), {
                'status': 'blocked', 'reason': 'database_unavailable_or_invalid'})

    def test_wal_only_violation_is_seen_but_uncommitted_write_is_not(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'db'
            with contextlib.closing(sqlite3.connect(path)) as c:
                c.execute('PRAGMA journal_mode=WAL')
                c.executescript('CREATE TABLE parent(id PRIMARY KEY); '
                                'CREATE TABLE child(id REFERENCES parent(id));')
                c.execute('PRAGMA wal_checkpoint(TRUNCATE)')
                original = path.read_bytes()
                c.execute('INSERT INTO child VALUES (42)')
                self.assertTrue(p.inspect(path)['foreign_keys_ok'])
                c.commit()
                before = {suffix: Path(str(path) + suffix).read_bytes()
                          for suffix in ('', '-wal')}
                self.assertEqual(original, before[''])  # Solo WAL contiene la infracción.
                with contextlib.redirect_stdout(io.StringIO()) as out:
                    self.assertEqual(p.main(['--db', str(path)]), 1)
                self.assertFalse(json.loads(out.getvalue())['foreign_keys_ok'])
                self.assertEqual(before, {suffix: Path(str(path) + suffix).read_bytes()
                                          for suffix in ('', '-wal')})
