"""Regresiones: reacción ❗ de advertencia y compatibilidad con Moderation WARN.

No importa ni inicia el bot, no realiza acciones contra Discord.
"""
import ast
import asyncio
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sqlite3
import tempfile
from types import SimpleNamespace
import unittest

TREE = ast.parse((Path(__file__).resolve().parents[1] / "bot.py").read_text(encoding="utf-8"))


def isolated(name, values):
    node = next(n for n in TREE.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == name)
    # Compilar exclusivamente la función bajo prueba, no importar el bot real.
    node = ast.parse(ast.unparse(node)).body[0]
    node.decorator_list = []
    node.returns = None
    for argument in node.args.posonlyargs + node.args.args + node.args.kwonlyargs:
        argument.annotation = None
    namespace = dict(values)
    exec(compile(ast.fix_missing_locations(ast.Module(body=[node], type_ignores=[])),
                 "<aislado-warn>", "exec"), namespace)
    return namespace[name]


class WarningReactionTests(unittest.TestCase):
    def test_default_warn_rule_and_existing_warn_system(self):
        assignment = next(
            n for n in TREE.body if isinstance(n, ast.Assign)
            and any(isinstance(t, ast.Name) and t.id == "MODERATION_REPORT_REACTION_DEFAULTS"
                    for t in n.targets)
        )
        defaults = ast.literal_eval(assignment.value)
        warning = [item for item in defaults if item["emoji"] == "❗"]
        self.assertEqual(len(warning), 1)
        self.assertEqual(warning[0]["action"], "warn")
        self.assertEqual(warning[0]["threshold"], 1)
        self.assertIsNone(warning[0]["purge_minutes"])
        self.assertIsNone(warning[0]["duration_minutes"])
        self.assertIn("WARN", ast.unparse(TREE))
        self.assertIn("name='warn'", ast.unparse(TREE))
        self.assertIn("name='advertencias'", ast.unparse(TREE))

    def test_warn_rule_normalizes_as_nondestructive(self):
        normalize = isolated("_normalize_moderation_report_rule", {
            "MODERATION_REPORT_ACTIONS": {"report", "warn", "timeout", "condemn", "ban", "kick"},
            "PURGE_MAX_MINUTES": 10080,
        })
        rule = normalize(dict(emoji="❗", label="Reglas", action="warn",
                              threshold=5, purge_minutes=40, duration_minutes=90))
        self.assertEqual(rule["threshold"], 1)
        self.assertIsNone(rule["purge_minutes"])
        self.assertIsNone(rule["duration_minutes"])

    def test_case_reuses_existing_without_extra_record(self):
        with tempfile.TemporaryDirectory() as directory:
            path = str(Path(directory) / "warnings.sqlite3")
            with sqlite3.connect(path) as conn:
                conn.execute(
                    "CREATE TABLE moderation_cases (guild_id INTEGER, case_number INTEGER, "
                    "type TEXT, user_id INTEGER, reason TEXT, duration_minutes INTEGER, "
                    "created_at TEXT, expires_at TEXT, author_id INTEGER, proof TEXT, "
                    "verified_proof TEXT, moderator_notes TEXT, message_history TEXT, "
                    "open INTEGER, UNIQUE(guild_id,case_number))"
                )
                conn.execute(
                    "CREATE TABLE moderation_report_cases (guild_id INTEGER, message_id INTEGER, "
                    "target_id INTEGER, emoji_key TEXT, case_number INTEGER, "
                    "PRIMARY KEY(guild_id,message_id,target_id,emoji_key))"
                )
            case_fn = isolated("moderation_report_case_record", {
                "db_connect": lambda: sqlite3.connect(path, isolation_level=None),
                "datetime": datetime, "timezone": timezone, "timedelta": timedelta,
                "moderation_case_message_history": lambda guild, user: "{}",
                "moderation_warning_limit": lambda guild: 3,
                "ModerationWarningLimitReached": ValueError,
            })
            args = (25, 400, 500, "❗", "WARN", "Incumplimiento de reglas")
            first = case_fn(*args, duration_minutes=None, proof="https://discord.com", author_id=600, return_created=True)
            again = case_fn(*args, duration_minutes=None, proof="https://discord.com", author_id=600, return_created=True)
            self.assertEqual(first, (1, True))
            self.assertEqual(again, (1, False))
            with sqlite3.connect(path) as conn:
                self.assertEqual(conn.execute("SELECT COUNT(*) FROM moderation_cases").fetchone()[0], 1)
                self.assertEqual(conn.execute("SELECT type, author_id FROM moderation_cases").fetchone(), ("WARN", 600))

    def test_warn_executes_once_and_sends_dm_only_when_new(self):
        recorded, delivered = [], []
        async def notify(guild, user, number):
            delivered.append(number)
            return True
        def add_case(*args, **kwargs):
            recorded.append((args, kwargs))
            return (12, len(recorded) == 1)
        warning = isolated("execute_moderation_report_action", {
            "condemnation_protection_reason": lambda member: None,
            "moderation_can_warn": lambda member: True,
            "moderation_report_punishment_enabled": lambda guild_id, action: True,
            "moderation_report_case_record": add_case,
            "moderation_case_code": lambda num, guild: "AB1C234",
            "moderation_send_case_dm": notify,
            "moderation_warning_counts": lambda guild, user: (1, 1),
            "moderation_warning_limit": lambda guild: 3,
            "ModerationWarningLimitReached": ValueError,
            "_moderation_emoji_key": lambda s: s,
        })
        guild = SimpleNamespace(id=25, owner_id=20)
        member = SimpleNamespace(id=500, top_role=5)
        moderator = SimpleNamespace(id=600, top_role=15)
        message = SimpleNamespace(id=400, jump_url="https://discord.com", channel=SimpleNamespace(id=42))
        rule = {"action": "warn", "label": "Reglas", "emoji": "❗", "purge_minutes": 60}
        first = asyncio.run(warning(guild, member, message, rule, 1, actor=moderator))
        second = asyncio.run(warning(guild, member, message, rule, 1, actor=moderator))
        self.assertTrue(first[0])
        self.assertTrue(second[0])
        self.assertEqual(delivered, [12])
        self.assertEqual(recorded[0][1]["author_id"], moderator.id)
        self.assertIn("Advertencia existente", second[1])

    def test_unauthorized_warn_does_not_create_case(self):
        warn = isolated("execute_moderation_report_action", {
            "condemnation_protection_reason": lambda member: None,
            "moderation_can_warn": lambda member: False,
            "moderation_report_punishment_enabled": lambda guild_id, action: True,
        })
        success, message = asyncio.run(warn(
            SimpleNamespace(id=10, owner_id=1), SimpleNamespace(id=5),
            SimpleNamespace(), {"action": "warn"}, 1, actor=SimpleNamespace(id=2)))
        self.assertFalse(success)
        self.assertIn("permiso", message)

    def test_reaction_swap_requires_successful_record(self):
        listener = next(n for n in TREE.body if isinstance(n, ast.AsyncFunctionDef)
                        and n.name == "moderation_reaction_add")
        code = ast.unparse(listener)
        self.assertIn("moderation_can_warn(actor)", code)
        self.assertIn("moderation_report_mark_executed", code)
        self.assertIn("await message.add_reaction(emoji)", code)
        self.assertIn("await message.remove_reaction(emoji, actor)", code)
        self.assertLess(code.index("moderation_report_mark_executed"), code.index("await message.add_reaction(emoji)"))
        self.assertNotIn("await message.delete()", code)


if __name__ == "__main__":
    unittest.main()
