"""Diagnóstico de lectura, sin filas, rutas, recuentos ni errores privados."""
import argparse
from contextlib import closing
import hashlib
import json
from pathlib import Path
import sqlite3


def inspect(path):
    path = Path(path).resolve(strict=True)
    with closing(sqlite3.connect(path.as_uri() + '?mode=ro', uri=True, timeout=2)) as conn:
        conn.execute('PRAGMA query_only=ON')
        conn.execute('BEGIN')
        integrity = conn.execute('PRAGMA integrity_check').fetchall() == [('ok',)]
        foreign_keys = conn.execute('PRAGMA foreign_key_check').fetchone() is None
        schema = conn.execute("SELECT type,name,tbl_name,sql FROM sqlite_master "
                              "WHERE sql IS NOT NULL ORDER BY type,name").fetchall()
        result = {
            'integrity_ok': integrity, 'foreign_keys_ok': foreign_keys,
            'schema_sha256': hashlib.sha256(json.dumps(schema).encode()).hexdigest(),
            'user_version': conn.execute('PRAGMA user_version').fetchone()[0],
            'application_id': conn.execute('PRAGMA application_id').fetchone()[0],
            'journal_mode': conn.execute('PRAGMA journal_mode').fetchone()[0],
            'wal_present': Path(str(path) + '-wal').exists(),
            'shm_present': Path(str(path) + '-shm').exists(),
            'empty_schema': not bool(schema),
        }
        conn.rollback()
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db', required=True)
    args = parser.parse_args(argv)
    try:
        result = inspect(args.db)
        valid = result['integrity_ok'] and result['foreign_keys_ok'] and not result['empty_schema']
        print(json.dumps({'status': 'ok' if valid else 'blocked', **result}, sort_keys=True))
        return 0 if valid else 1
    except (OSError, sqlite3.Error, ValueError):
        # SQLite puede incluir contenido corrupto o nombres privados en sus errores.
        print('{"status": "blocked", "reason": "database_unavailable_or_invalid"}')
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
