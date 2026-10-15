"""Regresiones aisladas: sanciones automáticas por reportes de Moderation."""
import ast
import asyncio
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sqlite3
import tempfile
from types import SimpleNamespace
import unittest

TREE = ast.parse((Path(__file__).resolve().parents[1] / "bot.py").read_text(encoding="utf-8"))


def isolated(name, namespace):
    node = next(n for n in TREE.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                and n.name == name)
    node = ast.FunctionDef(name=node.name, args=node.args, body=node.body, decorator_list=[],
                           returns=None, type_comment=None) if isinstance(node, ast.FunctionDef) else (
        ast.AsyncFunctionDef(name=node.name, args=node.args, body=node.body,
                             decorator_list=[], returns=None, type_comment=None))
    for arg in node.args.args + node.args.kwonlyargs + node.args.posonlyargs:
        arg.annotation = None
    module = ast.fix_missing_locations(ast.Module(body=[node], type_ignores=[]))
    env = dict(namespace)
    exec(compile(module, "<isolated-moderation>", "exec"), env)
    return env[name]


class DatabaseTests(unittest.TestCase):
    def test_one_administrative_case_per_reaction(self):
        with tempfile.TemporaryDirectory() as directory:
            path = str(Path(directory) / "cases.sqlite3")
            with sqlite3.connect(path) as con:
                con.execute(
                    "CREATE TABLE moderation_cases ("
                    "guild_id INTEGER, case_number INTEGER, type TEXT, user_id INTEGER, "
                    "reason TEXT, duration_minutes INTEGER, created_at TEXT, expires_at TEXT, "
                    "author_id INTEGER, proof TEXT, verified_proof TEXT, moderator_notes TEXT, "
                    "message_history TEXT, open INTEGER, UNIQUE(guild_id, case_number))"
                )
                con.execute(
                    "CREATE TABLE moderation_report_cases (guild_id INTEGER, message_id INTEGER, "
                    "target_id INTEGER, emoji_key TEXT, case_number INTEGER, "
                    "PRIMARY KEY(guild_id,message_id,target_id,emoji_key))"
                )
            def connect():
                return sqlite3.connect(path, timeout=2.0, isolation_level=None)
            record = isolated("moderation_report_case_record", {
                "db_connect": connect, "datetime": datetime, "timezone": timezone,
                "timedelta": timedelta, "moderation_case_message_history": lambda g, u: "{}"
            })
            args = (10, 200, 300, "flag", "BAN", "Motivo")
            one = record(*args, duration_minutes=None, proof="https://discord.com/example")
            two = record(*args, duration_minutes=None, proof="https://discord.com/example")
            other = record(11, 200, 300, "flag", "BAN", "Motivo",
                           duration_minutes=None, proof="https://discord.com/example")
            self.assertEqual(one, two)
            self.assertEqual(other, 1)
            with sqlite3.connect(path) as con:
                self.assertEqual(con.execute("SELECT COUNT(*) FROM moderation_cases").fetchone()[0], 2)
                self.assertEqual(con.execute("SELECT COUNT(*) FROM moderation_report_cases").fetchone()[0], 2)


class ExecutionTests(unittest.TestCase):
    def setup_action(self, *, permission=True, case_error=False):
        events = []
        async def sanction(**kwargs):
            events.append("sanción")
        async def purge(*args, **kwargs):
            events.append(("purga", kwargs.get("log_success")))
            return "resultado"
        def case(*args, **kwargs):
            events.append("expediente")
            if case_error:
                raise sqlite3.OperationalError("fallo controlado")
            return 7
        member_perms = SimpleNamespace(
            manage_roles=True, moderate_members=permission,
            kick_members=permission, ban_members=permission)
        guild = SimpleNamespace(
            id=10, me=SimpleNamespace(guild_permissions=member_perms, top_role=99))
        target = SimpleNamespace(id=300, top_role=3, timeout=sanction, kick=sanction, ban=sanction)
        message = SimpleNamespace(id=200, jump_url="https://discord.com/message",
                                  channel=SimpleNamespace(id=50))
        env = {
            "discord": SimpleNamespace(HTTPException=Exception),
            "datetime": datetime, "timedelta": timedelta, "timezone": timezone,
            "condemnation_protection_reason": lambda t: None,
            "format_duration": lambda m: str(m),
            "moderation_report_case_record": case,
            "moderation_report_punishment_enabled": lambda guild_id, action: True,
            "moderation_case_code": lambda number, guild_id: "A12B345",
            "_moderation_emoji_key": lambda s: s,
            "run_purge_job": purge, "purge_result_text": lambda x: "2 mensajes",
        }
        return isolated("execute_moderation_report_action", env), guild, target, message, events

    def test_single_log_on_successful_purge(self):
        execute, guild, target, message, events = self.setup_action()
        rule = dict(action="kick", emoji="flag", label="Spam", purge_minutes=15)
        success, result = asyncio.run(execute(guild, target, message, rule, 3))
        self.assertTrue(success)
        self.assertEqual(events, ["sanción", "expediente", ("purga", False)])
        self.assertIn("expediente A12B345", result)

    def test_case_failure_never_reapplies_sanction(self):
        execute, guild, target, message, events = self.setup_action(case_error=True)
        rule = dict(action="ban", emoji="flag", label="Spam", purge_minutes=None)
        success, result = asyncio.run(execute(guild, target, message, rule, 2))
        self.assertTrue(success)
        self.assertEqual(events, ["sanción", "expediente"])
        self.assertIn("no registrado", result)

    def test_missing_permission_blocks_execution(self):
        execute, guild, target, message, events = self.setup_action(permission=False)
        rule = dict(action="kick", emoji="flag", label="Spam", purge_minutes=20)
        success, message = asyncio.run(execute(guild, target, message, rule, 2))
        self.assertFalse(success)
        self.assertEqual(events, [])
        self.assertIn("permiso", message)

    def test_report_is_informational_only(self):
        execute, guild, target, message, events = self.setup_action()
        rule = dict(action="report", emoji="flag", label="Spam", purge_minutes=20)
        success, note = asyncio.run(execute(guild, target, message, rule, 2))
        self.assertTrue(success)
        self.assertEqual(events, [])
        self.assertEqual(note, "Reporte registrado")

    def test_timeout_without_duration_is_rejected(self):
        execute, guild, target, message, events = self.setup_action()
        rule = dict(action="timeout", emoji="flag", label="Spam", duration_minutes=None)
        success, note = asyncio.run(execute(guild, target, message, rule, 2))
        self.assertFalse(success)
        self.assertEqual(events, [])
        self.assertIn("duración", note)


if __name__ == "__main__":
    unittest.main()
