"""Regresión de las tarjetas compactas de salida, expulsión y baneo, sin Gateway."""
from __future__ import annotations

import ast
import sqlite3
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import MagicMock

SOURCE = (Path(__file__).resolve().parent / "bot.py").read_text(encoding="utf-8")
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
        built.set_thumbnail.reset_mock()
        fn(self.member, "member_leave")
        self.assertEqual(renderer.call_args.args[3], "red")


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


class OrientationDedupeBehaviorTests(unittest.IsolatedAsyncioTestCase):
    """Probar el consumo del marcador sin enviar mensajes a Discord."""

    async def test_special_log_suppresses_exactly_one_generic_duplicate(self):
        import asyncio
        member = sample_member()
        key = (member.guild.id, member.id, member.joined_at)
        sent = {key: 100.0}
        variables = {
            "asyncio": asyncio,
            "time": NS(monotonic=lambda: 101.0),
            "bot": NS(user=NS(id=9)),
            "_ORIENTATION_KICK_REASON": "No definió su orientación",
            "_ORIENTATION_LOG_WINDOW": 30.0,
            "_orientation_kick_log_pending": {},
            "_orientation_kick_log_sent": sent,
            "orientation_kick_log_key": lambda item: (item.guild.id, item.id, item.joined_at),
            "orientation_prune_kick_log_markers": lambda now: None,
        }
        check = isolate("orientation_departure_has_detailed_log", variables)
        bot_actor = NS(id=9)
        self.assertTrue(await check(member, "member_kick", bot_actor, "No definió su orientación"))
        self.assertNotIn(key, sent)
        # El mismo usuario y evento no puede ocultar una segunda salida.
        self.assertFalse(await check(member, "member_kick", bot_actor, "No definió su orientación"))

    async def test_missing_special_log_keeps_generic_departure(self):
        import asyncio
        member = sample_member()
        variables = {
            "asyncio": asyncio,
            "time": NS(monotonic=lambda: 101.0),
            "bot": NS(user=NS(id=9)),
            "_ORIENTATION_KICK_REASON": "No definió su orientación",
            "_ORIENTATION_LOG_WINDOW": 30.0,
            "_orientation_kick_log_pending": {},
            "_orientation_kick_log_sent": {},
            "orientation_kick_log_key": lambda item: (item.guild.id, item.id, item.joined_at),
            "orientation_prune_kick_log_markers": lambda now: None,
        }
        check = isolate("orientation_departure_has_detailed_log", variables)
        self.assertFalse(await check(member, "member_kick", NS(id=9), "No definió su orientación"))
        self.assertFalse(await check(member, "member_kick", NS(id=8), "No definió su orientación"))
        self.assertFalse(await check(member, "member_leave", None, None))




class UniqueRemovalLogPolicyTests(unittest.TestCase):
    """Una sanción confirmada produce su única tarjeta mediante on_member_remove."""

    def test_successful_role_fallback_does_not_publish_second_log(self):
        source = ast.get_source_segment(SOURCE, next(
            x for x in TREE.body if isinstance(x, ast.AsyncFunctionDef)
            and x.name == "evaluate_sin_verificado"))
        self.assertIn('await member.kick(', source)
        self.assertNotIn('"Expulsión por falta de verificación"', source)
        self.assertIn('"Advertencia: Error al expulsar"', source)

    def test_primary_timeout_does_not_publish_second_log(self):
        source = ast.get_source_segment(SOURCE, next(
            x for x in TREE.body if isinstance(x, ast.AsyncFunctionDef)
            and x.name == "evaluate_verify_timeout"))
        self.assertIn('await member.kick(', source)
        self.assertIn('await member.ban(', source)
        self.assertNotIn('"Expulsión por falta de verificación"', source)
        self.assertIn('"Expulsión permanente por falta de verificación"', source)
        self.assertIn('"Verificación vencida"', source)
        self.assertIn('"Advertencia: Error al aplicar el timeout', source)

    def test_generic_member_log_survives_and_uses_selected_event(self):
        source = ast.get_source_segment(SOURCE, next(
            x for x in TREE.body if isinstance(x, ast.AsyncFunctionDef)
            and x.name == "heraldo_member_departure"))
        self.assertIn('log_member_event_enabled(guild.id, kind)', source)
        self.assertIn('member_departure_description(member, kind', source)
        self.assertIn('await log_embed(', source)

if __name__ == "__main__":
    unittest.main()
