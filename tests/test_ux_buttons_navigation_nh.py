"""NH UX-03B: navegación inmediata y distribución de los botones de /setup.

Revisión estática de todas las vistas más ejecución aislada de los dos retornos
corregidos; no requiere conectar al Gateway de Discord.
"""
from i18n_source_helpers import source_text as _source_text
import ast
import unittest
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import AsyncMock, patch

CODE = _source_text(Path(__file__).resolve().parents[1] / 'bot.py', 'utf-8')
TREE = ast.parse(CODE)


def cls(name):
    return next(n for n in TREE.body if isinstance(n, ast.ClassDef) and n.name == name)


def fn(name, method):
    return next(n for n in cls(name).body if isinstance(n, ast.AsyncFunctionDef) and n.name == method)


def buttons(name):
    result = {}
    for f in cls(name).body:
        if not isinstance(f, ast.AsyncFunctionDef):
            continue
        for d in f.decorator_list:
            if not isinstance(d, ast.Call) or getattr(d.func, "attr", "") != "button":
                continue
            args = {v.arg: v.value for v in d.keywords}
            if "label" not in args:
                continue
            label = ast.literal_eval(args["label"])
            row = ast.literal_eval(args["row"]) if "row" in args else None
            result[f.name] = (label, row)
    return result


class NHButtonsNavigation(unittest.TestCase):
    def test_nh_is_mandatory_and_honest_about_discord_width(self):
        text = _source_text(Path(__file__).resolve().parents[1] / 'AGENTS.md', 'utf-8')
        policy = text.split("### UX-03B", 1)[1].split("### UX-04", 1)[0]
        for phrase in ("Volver", "submenú inmediatamente anterior", "ancho arbitrario",
                       "cinco botones", "filas", "futuros", "Heraldo's Lab"):
            self.assertIn(phrase, policy)

    def test_all_static_back_buttons_are_called_only_volver(self):
        count = 0
        for c in [n for n in TREE.body if isinstance(n, ast.ClassDef)]:
            for f in c.body:
                if not isinstance(f, ast.AsyncFunctionDef):
                    continue
                for d in f.decorator_list:
                    if not isinstance(d, ast.Call) or getattr(d.func, "attr", "") != "button":
                        continue
                    args = {k.arg: k.value for k in d.keywords}
                    val = args.get("label")
                    if f.name in ("back", "back_to_heraldo") and isinstance(val, ast.Constant):
                        self.assertEqual(val.value, "Volver", c.name)
                        count += 1
        self.assertGreaterEqual(count, 26)
        self.assertNotIn('label="Volver a /setup"', CODE)
        self.assertNotIn('label="Join Roles", style=discord.ButtonStyle.secondary', CODE)

    def test_immediate_parent_for_every_nested_return(self):
        targets = {
            "HeraldoHoneypotSetupView": "HeraldoAutomodSetupView",
            "HeraldoRaidSetupView": "HeraldoAutomodSetupView",
            "HeraldoOrientationSetupView": "HeraldoVerificationHubView",
            "HeraldoVerificationSetupView": "HeraldoVerificationHubView",
            "HeraldoMemberLogSetupView": "HeraldoLoggingSetupView",
            "ExitCommentSetupView": "HeraldoMemberLogSetupView",
            "HeraldoUserReportsSetupView": "HeraldoModerationSetupView",
            "HeraldoCondemnationSetupView": "HeraldoModerationSetupView",
            "HeraldoReactionRolesEditorView": "HeraldoReactionRolesSetupView",
        }
        for origin, parent in targets.items():
            with self.subTest(origin=origin):
                body = ast.get_source_segment(CODE, fn(origin, "back"))
                self.assertIn(parent + "(", body)
                self.assertNotIn("heraldo_setup_go_home(", body)

    def test_standardized_compact_grouping_and_discord_rows(self):
        expected = {
            "HeraldoOrientationSetupView": {2: 4, 3: 3, 4: 3},
            "HeraldoHoneypotSetupView": {1: 3, 2: 3, 3: 3},
            "HeraldoTemplateSetupView": {2: 3, 3: 3, 4: 3},
            "HeraldoVerificationSetupView": {3: 4, 4: 5},
            "HeraldoUserReportsSetupView": {3: 5, 4: 5},
        }
        for name, rows in expected.items():
            b = buttons(name)
            actual = {row: sum(1 for _, position in b.values() if position == row)
                      for row in rows}
            with self.subTest(view=name):
                self.assertEqual(actual, rows)
                self.assertTrue(all(count <= 5 for count in actual.values()))
        self.assertEqual(buttons("HeraldoRoleSetupView")["back"], ("Volver", 4))
        role_positions = buttons("HeraldoRoleSetupView")
        self.assertEqual(role_positions["save_changes"][1], 4)
        self.assertEqual(role_positions["discard_changes"][1], 4)
        self.assertEqual(buttons("HeraldoJoinRolesSetupView")["back"], ("Volver", 1))

    def test_other_labels_of_personality_preserved(self):
        old = {"back", "activate", "deactivate", "edit_card", "configure_times",
               "toggle_change", "toggle_required", "edit_dm", "save_changes", "discard_changes"}
        self.assertEqual(set(buttons("HeraldoOrientationSetupView")), old)
        self.assertEqual(buttons("HeraldoOrientationSetupView")["edit_dm"][0],
                         "Editar DM de recuperación")


class NHButtonRuntimeNavigation(unittest.IsolatedAsyncioTestCase):
    async def test_automod_children_return_without_writing_to_sqlite(self):
        from test_safety_regressions import b
        for view_type in (b.HeraldoHoneypotSetupView, b.HeraldoRaidSetupView):
            with self.subTest(view=view_type.__name__):
                view = view_type(998812, 10)
                interaction = NS(guild=NS(id=998812), response=NS(
                    edit_message=AsyncMock(), send_message=AsyncMock(), defer=AsyncMock()),
                    edit_original_response=AsyncMock())
                if isinstance(view, b.HeraldoHoneypotSetupView):
                    with patch.object(view, "_pending_lines", return_value=[]):
                        await view.back.callback(interaction)
                    interaction.response.defer.assert_awaited_once()
                    call = interaction.edit_original_response.call_args
                else:
                    await view.back.callback(interaction)
                    call = interaction.response.edit_message.call_args
                self.assertIsInstance(call.kwargs["view"], b.HeraldoAutomodSetupView)
                self.assertIsNone(call.kwargs.get("embed"))


if __name__ == "__main__":
    unittest.main()
