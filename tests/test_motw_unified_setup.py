"""Contrato del panel unificado de Miembro de la Semana en /setup.

Evita regresiones de filas Discord y de escritura automática al seleccionar.
No importa bot.py ni requiere conexión a Discord.
"""
import ast
from pathlib import Path
from types import SimpleNamespace
import unittest


SOURCE = (Path(__file__).resolve().parents[1] / "bot.py").read_text(encoding="utf-8")
TREE = ast.parse(SOURCE)


def klass(name):
    return next(node for node in TREE.body
                if isinstance(node, ast.ClassDef) and node.name == name)


def method(view, name):
    return next(node for node in view.body
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                and node.name == name)


class MotwSinglePanelTests(unittest.TestCase):
    def test_legacy_second_screen_was_removed(self):
        names = {node.name for node in TREE.body if isinstance(node, ast.ClassDef)}
        self.assertIn("HeraldoMotwSetupView", names)
        self.assertIn("HeraldoMotwConfirmView", names)
        self.assertNotIn("HeraldoMotwScheduleSelectView", names)
        self.assertNotIn("schedule", {
            node.name for node in klass("HeraldoMotwSetupView").body
            if isinstance(node, ast.AsyncFunctionDef)
        })

    def test_one_panel_has_three_selectors_and_valid_discord_rows(self):
        editor = klass("HeraldoMotwSetupView")
        init = method(editor, "__init__")
        occupation = {i: 0 for i in range(5)}
        selection_rows = []
        for node in ast.walk(init):
            if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                    and node.func.attr in {"ChannelSelect", "Select"}):
                continue
            row = next(ast.literal_eval(kw.value) for kw in node.keywords
                       if kw.arg == "row")
            selection_rows.append(row)
            occupation[row] += 5
        self.assertEqual(selection_rows, [0, 1, 2])
        for function in editor.body:
            if not isinstance(function, ast.AsyncFunctionDef):
                continue
            for decorator in function.decorator_list:
                if not (isinstance(decorator, ast.Call)
                        and isinstance(decorator.func, ast.Attribute)
                        and decorator.func.attr == "button"):
                    continue
                row = next(ast.literal_eval(kw.value) for kw in decorator.keywords
                           if kw.arg == "row")
                occupation[row] += 1
        self.assertEqual(occupation, {0: 5, 1: 5, 2: 5, 3: 1, 4: 3})
        self.assertTrue(all(width <= 5 for width in occupation.values()))

    def test_all_three_fields_control_save_state(self):
        view = klass("HeraldoMotwSetupView")
        fn = method(view, "_has_pending_changes")
        compiled = ast.fix_missing_locations(ast.Module(body=[fn], type_ignores=[]))
        ns = {}
        exec(compile(compiled, "bot.py", "exec"), ns)
        instance = SimpleNamespace(
            pending_channel_id=None, original_weekday=4,
            original_hour=18, weekday=4, hour=18)
        self.assertFalse(ns["_has_pending_changes"](instance))
        instance.weekday = 5
        self.assertTrue(ns["_has_pending_changes"](instance))
        instance.weekday = 4
        self.assertFalse(ns["_has_pending_changes"](instance))
        instance.hour = 19
        self.assertTrue(ns["_has_pending_changes"](instance))
        instance.hour = 18
        self.assertFalse(ns["_has_pending_changes"](instance))
        instance.pending_channel_id = 123
        self.assertTrue(ns["_has_pending_changes"](instance))

    def test_selectors_only_update_draft(self):
        editor = klass("HeraldoMotwSetupView")
        for name in ("select_channel", "select_day", "select_hour"):
            with self.subTest(name=name):
                body = ast.unparse(method(editor, name))
                self.assertIn("edit_message", body)
                self.assertIn("_sync_controls", body)
                self.assertNotIn("set_motw_channel_id", body)
                self.assertNotIn("set_motw_schedule", body)
                self.assertNotIn("guild_config_set", body)

    def test_save_opens_confirmation_and_confirmation_persists(self):
        editor = klass("HeraldoMotwSetupView")
        save = ast.unparse(method(editor, "save_changes"))
        self.assertIn("HeraldoMotwConfirmView", save)
        self.assertNotIn("set_motw_channel_id", save)
        self.assertNotIn("set_motw_schedule", save)
        confirm = ast.unparse(method(klass("HeraldoMotwConfirmView"), "confirm"))
        self.assertIn("set_motw_channel_id", confirm)
        self.assertIn("set_motw_schedule", confirm)
        self.assertIn("get_motw_weekday", confirm)
        self.assertIn("get_motw_hour", confirm)
        self.assertIn("editor.pending_channel_id = None", confirm)
        self.assertIn("editor._sync_controls()", confirm)
        self.assertIn("view=editor", confirm)

    def test_discard_resets_every_field_and_testing_uses_saved_settings(self):
        editor = klass("HeraldoMotwSetupView")
        discard = ast.unparse(method(editor, "discard_changes"))
        self.assertIn("self.pending_channel_id = None", discard)
        self.assertIn("self.weekday = self.original_weekday", discard)
        self.assertIn("self.hour = self.original_hour", discard)
        testing = ast.unparse(method(editor, "test"))
        self.assertIn("_has_pending_changes", testing)
        self.assertIn("announce_member_of_the_week", testing)


if __name__ == "__main__":
    unittest.main()
