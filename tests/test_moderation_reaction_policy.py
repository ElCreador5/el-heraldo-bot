"""Pruebas aisladas para política de reportes y escalamiento al máximo de WARN.

No importa bot.py ni se conecta a Discord. Las llamadas de sanción son simuladas.
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


def isolated_function(name, dependencies):
    function = next(item for item in TREE.body
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))
                    and item.name == name)
    function = ast.parse(ast.unparse(function)).body[0]
    function.decorator_list = []
    function.returns = None
    for argument in function.args.posonlyargs + function.args.args + function.args.kwonlyargs:
        argument.annotation = None
    env = dict(dependencies)
    exec(compile(ast.fix_missing_locations(ast.Module(body=[function], type_ignores=[])),
                 "<policy-tests>", "exec"), env)
    return env[name]


class PolicyTests(unittest.TestCase):
    def test_legacy_report_actions_enabled_by_default(self):
        getter = isolated_function("moderation_report_punishment_enabled", {
            "MODERATION_REPORT_TOGGLABLE_ACTIONS": ("warn", "timeout", "kick", "ban", "condemn"),
            "guild_config_get": lambda guild, key: None,
        })
        self.assertTrue(all(getter(10, item)
                            for item in ("report", "warn", "timeout", "kick", "ban", "condemn")))
        blocked = isolated_function("moderation_report_punishment_enabled", {
            "MODERATION_REPORT_TOGGLABLE_ACTIONS": ("warn", "timeout", "kick", "ban", "condemn"),
            "guild_config_get": lambda guild, key: "0",
        })
        self.assertFalse(blocked(10, "ban"))
        self.assertTrue(blocked(10, "report"))

    def test_default_escalation_is_only_report(self):
        action = isolated_function("moderation_warn_escalation_action", {
            "guild_config_get": lambda guild, key: None,
            "MODERATION_WARN_ESCALATION_ACTIONS": {"none", "timeout", "kick", "ban", "condemn"},
        })
        self.assertEqual(action(10), "none")

    def test_escalation_timeout_runs_only_once(self):
        with tempfile.TemporaryDirectory() as directory:
            db = Path(directory) / "warnings.sqlite"
            with sqlite3.connect(db) as conn:
                conn.execute(
                    "CREATE TABLE moderation_warn_escalations ("
                    "guild_id INTEGER, user_id INTEGER, warn_case_number INTEGER,"
                    "action TEXT, status TEXT, created_at TEXT,"
                    "PRIMARY KEY(guild_id,user_id,warn_case_number))"
                )
            calls = []
            async def timeout(until, reason):
                calls.append(("timeout", until, reason))
            async def report(*args, **kwargs):
                calls.append(("log",))
            def create_case(*args, **kwargs):
                calls.append(("case",))
                return 13
            guild = SimpleNamespace(id=10, me=SimpleNamespace(
                guild_permissions=SimpleNamespace(moderate_members=True),
                top_role=50,
            ))
            member = SimpleNamespace(id=7, bot=False, top_role=1, mention="@prueba",
                                     timeout=timeout)
            func = isolated_function("moderation_warning_escalation", {
                "moderation_warn_escalation_action": lambda guild: "timeout",
                "moderation_report_punishment_enabled": lambda guild, action: True,
                "moderation_warn_escalation_duration": lambda guild: 60,
                "condemnation_protection_reason": lambda member: None,
                "db_connect": lambda: sqlite3.connect(db, isolation_level=None),
                "datetime": datetime, "timezone": timezone, "timedelta": timedelta,
                "moderation_case_code": lambda number, guild: "ABC1234",
                "moderation_case_create": create_case,
                "moderation_action_label": lambda action: "Aislar",
                "discord": SimpleNamespace(Color=SimpleNamespace(orange=lambda: None)),
                "log_embed": report,
            })
            first = asyncio.run(func(guild, member, 22, 3, 3))
            second = asyncio.run(func(guild, member, 22, 3, 3))
            self.assertIn("Aislar", first)
            self.assertIn("no se repetirá", second)
            self.assertEqual(sum(1 for c in calls if c[0] == "timeout"), 1)
            self.assertEqual(sum(1 for c in calls if c[0] == "case"), 1)
            with sqlite3.connect(db) as conn:
                self.assertEqual(
                    conn.execute("SELECT status FROM moderation_warn_escalations").fetchone()[0],
                    "complete",
                )

    def test_escalation_disabled_cannot_sanction(self):
        func = isolated_function("moderation_warning_escalation", {
            "moderation_warn_escalation_action": lambda guild: "ban",
            "moderation_report_punishment_enabled": lambda guild, action: False,
        })
        outcome = asyncio.run(func(SimpleNamespace(id=10), SimpleNamespace(), 17, 3, 3))
        self.assertIn("desactivada", outcome)

    def test_report_executor_rejects_disabled_actions(self):
        fn = isolated_function("execute_moderation_report_action", {
            "moderation_report_punishment_enabled": lambda guild, action: False,
            "condemnation_protection_reason": lambda target: None,
        })
        guild = SimpleNamespace(id=10)
        target = SimpleNamespace()
        message = SimpleNamespace()
        for action in ("warn", "timeout", "kick", "ban", "condemn"):
            answer = asyncio.run(fn(guild, target, message, {"action": action}, 2))
            self.assertFalse(answer[0], action)
            self.assertIn("desactivada", answer[1])

    def test_confirmed_condemnation_uses_shared_motor_and_no_duplicate_case(self):
        code = ast.unparse(next(n for n in TREE.body
                                if isinstance(n, ast.AsyncFunctionDef)
                                and n.name == "execute_moderation_report_action"))
        self.assertIn("await condemn_member(", code)
        self.assertIn("origin='reaction_report'", code)
        self.assertIn("source_message_url=message.jump_url", code)
        self.assertIn("if action in {'timeout', 'kick', 'ban'}", code)

    def test_direct_reaction_checks_moderator_permission_and_role_hierarchy(self):
        helper = isolated_function("moderation_can_condemn", {
            "condemnation_protection_reason": lambda target: None,
        })
        owner = 99
        guild = SimpleNamespace(owner_id=owner)
        target = SimpleNamespace(top_role=10)
        actor = SimpleNamespace(id=8, guild=guild, top_role=5,
                                guild_permissions=SimpleNamespace(kick_members=True, administrator=False))
        self.assertFalse(helper(actor, target))
        actor.top_role = 12
        self.assertTrue(helper(actor, target))
        actor.guild_permissions.kick_members = False
        self.assertFalse(helper(actor, target))
        actor.id = owner
        actor.guild_permissions.administrator = True
        self.assertTrue(helper(actor, target))
        listener = ast.unparse(next(n for n in TREE.body
                                    if isinstance(n, ast.AsyncFunctionDef)
                                    and n.name == "moderation_reaction_add"))
        modal = ast.unparse(next(n for n in TREE.body
                                 if isinstance(n, ast.ClassDef)
                                 and n.name == "ReactionCondemnReasonModal"))
        self.assertIn("moderation_can_condemn(actor, target)", listener)
        self.assertIn("moderation_can_condemn(actor, target)", modal)

    def test_report_condemn_dispatches_to_existing_condemnation_motor(self):
        calls = []
        async def condemn(member, **kwargs):
            calls.append(kwargs)
            return True, "condena aplicada"
        def unexpected_case(*args, **kwargs):
            self.fail("La condena debe crear su propio expediente en su motor")
        fn = isolated_function("execute_moderation_report_action", {
            "condemnation_protection_reason": lambda member: None,
            "moderation_report_punishment_enabled": lambda guild_id, action: True,
            "condemn_member": condemn,
            "moderation_report_case_record": unexpected_case,
            "discord": SimpleNamespace(HTTPException=Exception),
        })
        permissions = SimpleNamespace(manage_roles=True)
        guild = SimpleNamespace(id=10, me=SimpleNamespace(
            guild_permissions=permissions, top_role=100,
        ))
        member = SimpleNamespace(id=5, top_role=3)
        message = SimpleNamespace(
            id=77, jump_url="https://discord.com/channels/10/20/77",
            channel=SimpleNamespace(id=20),
        )
        rule = {"emoji": "flag", "action": "condemn",
                "label": "Infracción", "duration_minutes": 60,
                "purge_minutes": None}
        success, note = asyncio.run(fn(guild, member, message, rule, 3))
        self.assertTrue(success)
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0]["origin"], "reaction_report")
        self.assertEqual(calls[0]["source_message_url"], message.jump_url)
        self.assertEqual(calls[0]["duration_minutes"], 60)
        self.assertIn("condena aplicada", note)

    def test_report_condemn_failure_does_not_announce_success(self):
        async def condemn(member, **kwargs):
            return False, "Rol de condena inaccesible"
        fn = isolated_function("execute_moderation_report_action", {
            "condemnation_protection_reason": lambda member: None,
            "moderation_report_punishment_enabled": lambda guild_id, action: True,
            "condemn_member": condemn,
            "discord": SimpleNamespace(HTTPException=Exception),
        })
        guild = SimpleNamespace(id=10, me=SimpleNamespace(
            guild_permissions=SimpleNamespace(manage_roles=True), top_role=30
        ))
        target = SimpleNamespace(top_role=1)
        message = SimpleNamespace(jump_url="https://discord.com/channels/10/20/30",
                                  channel=SimpleNamespace(id=20))
        success, note = asyncio.run(fn(
            guild, target, message, {"emoji": "flag", "action": "condemn"}, 2
        ))
        self.assertFalse(success)
        self.assertIn("inaccesible", note)

    def test_interface_actions_close_to_reaction_and_rows_are_valid(self):
        view = next(n for n in TREE.body
                    if isinstance(n, ast.ClassDef) and n.name == "HeraldoUserReportsSetupView")
        code = ast.unparse(view)
        self.assertIn("row=2", code)
        self.assertIn("label='Configurar condiciones'", code)
        self.assertIn("label='Sanciones y límite'", code)
        self.assertIn("row=4", code)
        policy = ast.unparse(next(n for n in TREE.body
                                  if isinstance(n, ast.ClassDef)
                                  and n.name == "HeraldoWarningLimitSelectView"))
        self.assertIn("confirm_configuration", policy)
        self.assertIn("moderation_reaction_", policy)
        self.assertIn("min_values=0", policy)
        self.assertNotIn("guild_config_set", policy)


if __name__ == "__main__":
    unittest.main()
