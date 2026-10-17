"""Regresión de las tarjetas compactas de salida, expulsión y baneo, sin Gateway."""
from __future__ import annotations

import ast
import sqlite3
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import MagicMock

SOURCE = (Path(__file__).resolve().parents[1] / "bot.py").read_text(encoding="utf-8")
TREE = ast.parse(SOURCE)


def isolate(name: str, variables: dict):
    function = next(node for node in TREE.body
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                    and node.name == name)
    module = ast.Module(body=[
        ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0),
        function,
    ], type_ignores=[])
    namespace = dict(variables)
    exec(compile(ast.fix_missing_locations(module), "bot.py", "exec"), namespace)
    return namespace[name]


def sample_member():
    guild = NS(id=5, member_count=811, default_role=NS(id=1))
    return NS(guild=guild, id=12345, display_name="Usuario", mention="<@12345>",
              display_avatar=NS(url="https://example.org/avatar.png"),
              joined_at=datetime(2026, 10, 15, tzinfo=timezone.utc),
              roles=[NS(id=1, mention="@todos"), NS(id=2, mention="<@&2>")])


class DepartureCardTests(unittest.TestCase):
    def setUp(self):
        fake_discord = NS(utils=NS(
            format_dt=lambda value, style: "<t:recent:R>",
            escape_markdown=lambda value: value.replace("*", r"\*"),
        ), Color=NS(red=lambda: "red", dark_grey=lambda: "grey"))
        self.context = {"discord": fake_discord, "format_duration": lambda minutes: f"{minutes} minutos"}
        self.description = isolate("member_departure_description", self.context)
        self.member = sample_member()

    def test_leave_matches_sapphire_layout_without_punishment_reason(self):
        rendered = self.description(self.member, "member_leave")
        self.assertIn("> **Usuario:** Usuario (<@12345>)", rendered)
        self.assertIn("> **ID:** \u006012345\u0060", rendered)
        self.assertIn("> **Ingresó:** <t:recent:R>", rendered)
        self.assertIn("> **Roles:** <@&2>", rendered)
        self.assertIn("> **Miembros:** 811", rendered)
        self.assertNotIn("Motivo:", rendered)
        self.assertNotIn("Duración:", rendered)
        self.assertNotIn("Responsable:", rendered)
        self.assertNotIn("Kicked", rendered)

    def test_kick_includes_reason_and_actor(self):
        rendered = self.description(
            self.member, "member_kick",
            reason="Incumplimiento de las normas", moderator=NS(mention="<@7>"))
        self.assertIn("**Motivo:** Incumplimiento de las normas", rendered)
        self.assertIn("**Responsable:** <@7>", rendered)
        self.assertNotIn("Duración:", rendered)

    def test_ban_duration_and_expiration_only_when_known(self):
        end = datetime(2026, 10, 18, tzinfo=timezone.utc)
        temporary = self.description(self.member, "member_ban",
            ban_duration_known=True, ban_duration_minutes=60, ban_expires_at=end)
        self.assertIn("**Duración:** 60 minutos", temporary)
        self.assertIn("**Finaliza:** <t:recent:R>", temporary)
        permanent = self.description(self.member, "member_ban", ban_duration_known=True)
        self.assertIn("**Duración:** Permanente", permanent)
        unknown = self.description(self.member, "member_ban")
        self.assertIn("Duración:** No consta", unknown)
        self.assertNotIn("Permanente", unknown)

    def test_missing_values_and_role_limit(self):
        self.member.joined_at = None
        self.member.guild.member_count = None
        self.member.roles = [NS(id=1, mention="@todos")] + [
            NS(id=i + 100, mention=f"<@&{i + 100}>") for i in range(250)]
        text = self.description(self.member, "member_leave", uncertainty="No se pudo verificar auditoría")
        self.assertIn("**Ingresó:** No disponible", text)
        self.assertIn("**Miembros:** No disponible", text)
        self.assertIn(" más", text)
        self.assertIn("**Clasificación:**", text)
        self.assertLess(len(text), 3000)

    def test_orientation_details_are_kept(self):
        text = self.description(self.member, "member_kick",
            reason="No definió su orientación", extra=[
                ("Oportunidad", "Primera"), ("DM de recuperación", "No disponible"),
            ])
        self.assertIn("**Motivo:** No definió su orientación", text)
        self.assertIn("**Oportunidad:** Primera", text)
        self.assertIn("**DM de recuperación:** No disponible", text)

    def test_embed_uses_existing_template_and_avatar(self):
        built = NS(thumbnail=NS(url=None), set_thumbnail=MagicMock())
        renderer = MagicMock(return_value=built)
        fn = isolate("member_departure_embed", {
            **self.context,
            "member_departure_description": self.description,
            "LOG_EVENT_CATALOG": {"members": [
                ("member_leave", "Miembro abandonó el servidor"),
                ("member_kick", "Miembro expulsado"),
                ("member_ban", "Miembro baneado"),
            ]},
            "build_log_template_embed": renderer,
        })
        self.assertIs(fn(self.member, "member_ban", ban_duration_known=True), built)
        self.assertEqual(renderer.call_args.kwargs["category"], "members")
        self.assertEqual(renderer.call_args.kwargs["event_key"], "member_ban")
        built.set_thumbnail.assert_called_once_with(url=self.member.display_avatar.url)


class BanMetadataTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime.now(timezone.utc)
        self.data = []
        self.function = isolate("member_departure_ban_details", {
            "moderation_case_list": lambda gid, uid, case_type, limit: self.data,
            "datetime": datetime, "timezone": timezone, "sqlite3": sqlite3,
        })

    def test_matching_recent_ban_temporary(self):
        self.data = [{"created_at": self.now.isoformat(),
                      "reason": "Reglas", "duration_minutes": 120,
                      "expires_at": (self.now + timedelta(minutes=120)).isoformat()}]
        known, minutes, expires = self.function(1, 2, self.now, "Reglas")
        self.assertTrue(known)
        self.assertEqual(minutes, 120)
        self.assertIsNotNone(expires)

    def test_matching_recent_ban_permanent(self):
        self.data = [{"created_at": self.now.isoformat(),
                      "reason": "Reglas", "duration_minutes": None, "expires_at": None}]
        self.assertEqual(self.function(1, 2, self.now, "Reglas"), (True, None, None))

    def test_old_or_mismatched_case_does_not_invent_duration(self):
        self.data = [{"created_at": (self.now - timedelta(hours=3)).isoformat(),
                      "reason": "Reglas", "duration_minutes": None, "expires_at": None}]
        self.assertEqual(self.function(1, 2, self.now, "Reglas"), (False, None, None))
        self.data[0]["created_at"] = self.now.isoformat()
        self.assertEqual(self.function(1, 2, self.now, "Otra causa"), (False, None, None))

    def test_database_error_does_not_hide_departure(self):
        def broken(*args, **kwargs):
            raise sqlite3.OperationalError("database locked")
        fn = isolate("member_departure_ban_details", {
            "moderation_case_list": broken, "datetime": datetime,
            "timezone": timezone, "sqlite3": sqlite3,
        })
        self.assertEqual(fn(1, 2, self.now, "Reglas"), (False, None, None))


class WiringTests(unittest.TestCase):
    def test_departure_uses_configured_member_logs_and_orientation_dedupe(self):
        node = next(node for node in TREE.body if isinstance(node, ast.AsyncFunctionDef)
                    and node.name == "heraldo_member_departure")
        code = ast.get_source_segment(SOURCE, node)
        self.assertIn("orientation_departure_has_detailed_log(", code)
        self.assertIn("member_departure_description(member, kind", code)
        self.assertIn("member_departure_ban_details(", code)
        self.assertIn("log_member_event_enabled(guild.id, kind)", code)

    def test_orientation_uses_same_visual_design_and_keeps_existing_dedupe(self):
        node = next(node for node in TREE.body if isinstance(node, ast.AsyncFunctionDef)
                    and node.name == "expel")
        code = ast.get_source_segment(SOURCE, node)
        self.assertIn('member_departure_embed(', code)
        self.assertIn('_orientation_kick_log_sent[log_key]', code)
        self.assertIn('await channel.send(embed=embed)', code)


if __name__ == "__main__":
    unittest.main()
