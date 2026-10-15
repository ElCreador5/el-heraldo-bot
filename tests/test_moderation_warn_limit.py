"""Regresiones aisladas: máximo configurable de advertencias vigentes 1–5."""
import ast
from datetime import datetime, timezone, timedelta
from pathlib import Path
import sqlite3
import tempfile
import unittest

TREE = ast.parse((Path(__file__).resolve().parents[1] / "bot.py").read_text(encoding="utf-8"))


def isolate(name, context):
    func = next(n for n in TREE.body
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == name)
    func = ast.parse(ast.unparse(func)).body[0]
    func.decorator_list = []
    func.returns = None
    for arg in func.args.posonlyargs + func.args.args + func.args.kwonlyargs:
        arg.annotation = None
    scope = dict(context)
    exec(compile(ast.fix_missing_locations(ast.Module(body=[func], type_ignores=[])),
                 "<warn-limit>", "exec"), scope)
    return scope[name]


class WarningLimitTests(unittest.TestCase):
    def test_default_and_absolute_cap(self):
        limit = isolate("moderation_warning_limit", {
            "guild_setting_int": lambda guild, key, default: default,
            "MODERATION_WARN_MAX_DEFAULT": 3,
            "MODERATION_WARN_MAX_ALLOWED": 5,
        })
        self.assertEqual(limit(27), 3)
        def configurable(value):
            return isolate("moderation_warning_limit", {
                "guild_setting_int": lambda *args: value,
                "MODERATION_WARN_MAX_DEFAULT": 3, "MODERATION_WARN_MAX_ALLOWED": 5,
            })(27)
        for num in (1, 2, 3, 4, 5):
            self.assertEqual(configurable(num), num)
        self.assertEqual(configurable(19), 5)
        self.assertEqual(configurable(-3), 1)

    def test_active_warnings_capped_with_history_preserved(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "warn.sqlite"
            with sqlite3.connect(path) as db:
                db.execute(
                    "CREATE TABLE moderation_cases (guild_id INTEGER, case_number INTEGER, "
                    "type TEXT, user_id INTEGER, reason TEXT, duration_minutes INTEGER, "
                    "created_at TEXT, expires_at TEXT, author_id INTEGER, proof TEXT, "
                    "verified_proof TEXT, moderator_notes TEXT, message_history TEXT, "
                    "open INTEGER, UNIQUE(guild_id,case_number))"
                )
            connect = lambda: sqlite3.connect(path, isolation_level=None, timeout=2)
            max_limit = [3]
            class LimitReached(ValueError): pass
            common = {
                "db_connect": connect, "moderation_warning_limit": lambda guild: max_limit[0],
                "moderation_case_message_history": lambda guild, user: "{}",
                "moderation_case_code": lambda case, guild: "ABC1234",
                "ModerationWarningLimitReached": LimitReached,
                "datetime": datetime, "timezone": timezone, "timedelta": timedelta,
            }
            create = isolate("moderation_warning_create", common)
            count = isolate("moderation_warning_counts", common)
            self.assertEqual(count(1, 10), (0, 0))
            for number in range(1, 4):
                self.assertEqual(create(1, 10, "Reglas", author_id=20)[1:], (number, 3))
            self.assertEqual(count(1, 10), (3, 3))
            with self.assertRaises(LimitReached):
                create(1, 10, "No guardar este intento")
            self.assertEqual(count(1, 10), (3, 3))
            with sqlite3.connect(path) as db:
                db.execute("UPDATE moderation_cases SET open=0 WHERE guild_id=1 AND case_number=2")
            self.assertEqual(count(1, 10), (2, 3))
            self.assertEqual(create(1, 10, "Nueva", author_id=20)[1:], (3, 3))
            self.assertEqual(count(1, 10), (3, 4))
            max_limit[0] = 5
            self.assertEqual(create(1, 10, "Cuarta")[1:], (4, 5))
            self.assertEqual(create(1, 10, "Quinta")[1:], (5, 5))
            with self.assertRaises(LimitReached):
                create(1, 10, "Sexta")
            self.assertEqual(count(1, 10), (5, 6))
            self.assertEqual(create(2, 10, "Otro servidor")[1:], (1, 5))
            self.assertEqual(create(1, 11, "Otro miembro")[1:], (1, 5))

    def test_reaction_warning_limit_checks_new_case_not_idempotent_old_case(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "warn.sqlite"
            with sqlite3.connect(path) as db:
                db.execute(
                    "CREATE TABLE moderation_cases (guild_id INTEGER, case_number INTEGER, "
                    "type TEXT, user_id INTEGER, reason TEXT, duration_minutes INTEGER, "
                    "created_at TEXT, expires_at TEXT, author_id INTEGER, proof TEXT, "
                    "verified_proof TEXT, moderator_notes TEXT, message_history TEXT, "
                    "open INTEGER, UNIQUE(guild_id,case_number))"
                )
                db.execute(
                    "CREATE TABLE moderation_report_cases (guild_id INTEGER, message_id INTEGER, "
                    "target_id INTEGER, emoji_key TEXT, case_number INTEGER, "
                    "PRIMARY KEY (guild_id,message_id,target_id,emoji_key))"
                )
            class LimitReached(ValueError): pass
            args = {
                "db_connect": lambda: sqlite3.connect(path, isolation_level=None),
                "datetime": datetime, "timezone": timezone, "timedelta": timedelta,
                "moderation_warning_limit": lambda guild: 1,
                "ModerationWarningLimitReached": LimitReached,
                "moderation_case_message_history": lambda guild, user: "{}",
            }
            record = isolate("moderation_report_case_record", args)
            first = record(1, 99, 5, "❗", "WARN", "Reglas", duration_minutes=None,
                           proof="https://discord.com", return_created=True)
            self.assertEqual(first, (1, True))
            self.assertEqual(record(1, 99, 5, "❗", "WARN", "Reglas", duration_minutes=None,
                                    proof="https://discord.com", return_created=True), (1, False))
            with self.assertRaises(LimitReached):
                record(1, 101, 5, "❗", "WARN", "Reglas", duration_minutes=None,
                       proof="https://discord.com", return_created=True)
            with sqlite3.connect(path) as db:
                self.assertEqual(db.execute("SELECT COUNT(*) FROM moderation_cases").fetchone()[0], 1)

    def test_selector_requires_explicit_confirmation_and_no_auto_punishment(self):
        view = next(node for node in TREE.body
                    if isinstance(node, ast.ClassDef) and node.name == "HeraldoWarningLimitSelectView")
        code = ast.unparse(view)
        self.assertIn("range(1, MODERATION_WARN_MAX_ALLOWED + 1)", code)
        self.assertIn("configuration_access", code)
        self.assertIn("confirm_configuration", code)
        self.assertIn("moderation_warn_limit", code)
        self.assertIn("Cancelar", code)
        self.assertNotIn("guild_config_set", code)
        self.assertNotIn("kick(", code)
        self.assertNotIn("ban(", code)


if __name__ == "__main__":
    unittest.main()
