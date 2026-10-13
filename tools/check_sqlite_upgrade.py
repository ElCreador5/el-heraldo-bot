"""Ensayo aislado de inicializadores reales y DDL literal; nunca usa una BD real.

Uso: python tools/check_sqlite_upgrade.py --main-source work/main-bot.py
El archivo de referencia debe obtenerse del SHA main revisado con git show.
No importa bot.py ni conecta a Discord. No acredita todas las rutas runtime.
"""
import argparse
import ast
from contextlib import closing
import json
from pathlib import Path
import sqlite3
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sqlite_recovery import create_backup, restore_backup


def initialize(source, path):
    tree = ast.parse(source)
    names = {'db_connect', 'db_init', 'honeypot_db_init', 'suggestion_db_init'}
    nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names]
    if {n.name for n in nodes} != names:
        raise RuntimeError('initializers_missing')
    namespace = {'sqlite3': sqlite3, 'DB_PATH': str(path)}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), '<reviewed-initializers>', 'exec'), namespace)
    for name in ('db_init', 'honeypot_db_init', 'suggestion_db_init'):
        namespace[name]()
    # Tablas opcionales creadas por rutas runtime: ejecutar su DDL literal real.
    with closing(sqlite3.connect(path)) as conn:
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == 'execute' and node.args:
                value = node.args[0]
                if isinstance(value, ast.Constant) and isinstance(value.value, str) and value.value.strip().upper().startswith('CREATE TABLE'):
                    conn.execute(value.value)
        conn.commit()


def rows(path):
    with closing(sqlite3.connect(path)) as c:
        return {name: c.execute('SELECT * FROM "' + name.replace('"', '""') + '"').fetchall()
                for (name,) in c.execute("SELECT name FROM sqlite_master WHERE type='table'")}


def schemas(path):
    with closing(sqlite3.connect(path)) as c:
        return {name: c.execute('PRAGMA table_info("' + name.replace('"', '""') + '")').fetchall()
                for (name,) in c.execute("SELECT name FROM sqlite_master WHERE type='table'")}


def rehearse(main_source, candidate_source):
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        db = root / 'synthetic.db'
        initialize(main_source, db)
        with closing(sqlite3.connect(db)) as c:
            c.execute("INSERT INTO guild_settings VALUES (101, 'pending_roles', '[700]')")
            c.execute("INSERT INTO guild_settings VALUES (102, 'pending_roles', '[800]')")
            c.execute("INSERT INTO guild_cases (guild_id,user_id,role_ids,reason,condemned_at,origin) "
                      "VALUES (101,1,'[700]','Sintético','2026-01-01','manual')")
            c.execute("INSERT INTO guild_cases (guild_id,user_id,role_ids,reason,condemned_at,origin) "
                      "VALUES (102,1,'[800]','Sintético','2026-01-01','manual')")
            c.execute("INSERT INTO guild_members (guild_id,user_id,verify_pending_at) VALUES (101,1,'2026-01-01')")
            c.commit()
        before, old_schema = rows(db), schemas(db)
        package = create_backup(db, root / 'backups', environment='synthetic', revision='reviewed-main')
        initialize(candidate_source, db)
        # Inicializadores del módulo nuevo también se ejecutan realmente.
        from message_automation import ScheduledMessages
        ScheduledMessages({'db_connect': lambda: sqlite3.connect(db)}).initialize()
        import evidence_archive
        evidence_archive.ledger(db, 'synthetic:101:1', 'claim')
        after, new_schema = rows(db), schemas(db)
        preserved = all(after.get(name) == value for name, value in before.items())
        unchanged = all(new_schema.get(name) == value for name, value in old_schema.items())
        initialize(candidate_source, db)
        idempotent = rows(db) == after
        # El código anterior puede abrir el esquema ampliado, pero ignora tareas nuevas.
        initialize(main_source, db)
        old_code_preserves = rows(db) == after
        # Restauración exacta del punto anterior en un destino detenido y aislado.
        schema = root / 'main-schema.db'
        initialize(main_source, schema)
        restored = root / 'restored.db'
        restore_backup(package, restored, schema_from=schema, environment='synthetic', service_stopped=True)
        rollback = rows(restored) == before
        result = {'existing_rows_preserved': preserved, 'existing_columns_unchanged': unchanged,
                  'startup_idempotent': idempotent, 'old_initializers_preserve_upgraded_db': old_code_preserves,
                  'snapshot_rollback_exact': rollback,
                  'added_tables': sorted(set(new_schema) - set(old_schema)),
                  'scope': 'startup_initializers_and_literal_optional_ddl_with_synthetic_cases'}
        if not all((preserved, unchanged, idempotent, old_code_preserves, rollback)):
            raise RuntimeError('compatibility_failed')
        return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--main-source', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(rehearse(args.main_source.read_text(), Path('bot.py').read_text()), indent=2))
