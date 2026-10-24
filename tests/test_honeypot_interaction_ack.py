"""Honeypot: reconocer interacciones antes de leer SQLite o editar Discord.

Estas pruebas inspeccionan métodos reales y simulan el descarte sin conectar al bot.
"""
import ast
import asyncio
import unittest
from honeypot_interactions import honeypot_operation
from pathlib import Path
from types import SimpleNamespace

SOURCE = (Path(__file__).resolve().parents[1] / "bot.py").read_text("utf-8")
TREE = ast.parse(SOURCE)


def method(klass, name):
    view = next(n for n in TREE.body if isinstance(n, ast.ClassDef) and n.name == klass)
    return next(n for n in view.body if isinstance(n, ast.AsyncFunctionDef) and n.name == name)


def code(klass, name):
    return ast.get_source_segment(SOURCE, method(klass, name))


class HoneypotAckTests(unittest.TestCase):
    ACK_FIRST = (
        ("HeraldoHoneypotSetupView", "select_trap"),
        ("HeraldoHoneypotSetupView", "toggle"),
        ("HeraldoHoneypotSetupView", "edit_action"),
        # edit_notice abre un modal inmediatamente; no debe deferir.
        ("HeraldoHoneypotSetupView", "details"),
        ("HeraldoHoneypotSetupView", "_save_pending_changes"),
        ("HeraldoHoneypotSetupView", "back"),
        ("HeraldoHoneypotSubView", "back"),
        ("HeraldoHoneypotDraftSubView", "discard_changes"),
        ("HeraldoHoneypotActionView", "choose"),
        ("HeraldoHoneypotActionView", "parameters"),
        ("HeraldoHoneypotParametersView", "select_kick_purge"),
        ("HeraldoHoneypotParametersView", "select_timeout"),
        ("HeraldoHoneypotParametersView", "select_ban_duration"),
        ("HeraldoHoneypotParametersView", "select_purge"),
        ("HeraldoHoneypotNoticeView", "publish_warning"),
        ("HoneypotTrapActionConfirmView", "confirm"),
    )

    def test_component_ack_is_first_before_db_or_api(self):
        for klass, name in self.ACK_FIRST:
            with self.subTest(klass=klass, method=name):
                node = method(klass, name)
                first = ast.get_source_segment(SOURCE, node.body[0]).strip()
                self.assertTrue(first.startswith("await interaction.response.defer("),
                                (klass, name, first))
                body = code(klass, name)
                self.assertNotIn("interaction.response.send_message(", body)
                self.assertNotIn("interaction.response.edit_message(", body)
                self.assertEqual(body.count("await interaction.response.defer("), 1)

    def test_notice_modal_is_first_response(self):
        source = code("HeraldoHoneypotSetupView", "edit_notice")
        self.assertIn("interaction.response.send_modal(", source)
        self.assertNotIn("interaction.response.defer(", source)
        self.assertNotIn("HeraldoHoneypotNoticeView(self)", source)

    def test_refresh_ack_on_first_non_deferred_call(self):
        node = method("HeraldoHoneypotSetupView", "_refresh")
        self.assertIn("interaction.response.is_done()", code("HeraldoHoneypotSetupView", "_refresh"))
        self.assertIn("await interaction.edit_original_response(", code("HeraldoHoneypotSetupView", "_refresh"))
        self.assertIsInstance(node.body[0], ast.If)

    def test_stage_never_sends_response_twice(self):
        snippet = code("HeraldoHoneypotParametersView", "_stage")
        self.assertIn("interaction.edit_original_response(", snippet)
        self.assertNotIn("interaction.response.edit_message(", snippet)
        self.assertNotIn("interaction.response.defer(", snippet)

    def test_empty_draft_ack_then_error_without_storage(self):
        node = method("HeraldoHoneypotSetupView", "_save_pending_changes")
        isolated = ast.Module(body=[
            ast.ImportFrom(module="__future__",
                           names=[ast.alias(name="annotations")], level=0),
            node,
        ], type_ignores=[])
        scope = {"honeypot_operation": honeypot_operation}
        exec(compile(ast.fix_missing_locations(isolated), "<isolated>", "exec"), scope)
        events = []
        class Response:
            async def defer(self):
                events.append("ack")
        class Followup:
            async def send(self, text, *, ephemeral=False):
                events.append(("feedback", text, ephemeral))
        interaction = SimpleNamespace(response=Response(), followup=Followup(), guild=SimpleNamespace())
        parent = SimpleNamespace(guild_id=901, _pending_lines=lambda guild: [])
        asyncio.run(scope["_save_pending_changes"](parent, interaction))
        self.assertEqual(events[0], "ack")
        self.assertEqual(events[1], ("feedback", "No hay cambios pendientes.", True))

    def test_honeypot_publish_and_trap_confirm_preserve_revalidation(self):
        publish = code("HeraldoHoneypotNoticeView", "publish_warning")
        confirm = code("HoneypotTrapActionConfirmView", "confirm")
        self.assertIn("self.parent._pending_lines", publish)
        self.assertIn("HoneypotPublishWarningConfirmView(", publish)
        self.assertIn("self.interaction_check(interaction)", confirm)
        self.assertIn("self.finished = True", confirm)
        self.assertIn("hp_protected_channel_reason", confirm)
        self.assertIn("self.action == \"create\"", confirm)

    def test_non_honeypot_footer_contract_remains(self):
        self.assertIn("def stamp_embed(", SOURCE)
        self.assertIn("server_footer_text(guild.name, detail)", SOURCE)


if __name__ == "__main__":
    unittest.main()
