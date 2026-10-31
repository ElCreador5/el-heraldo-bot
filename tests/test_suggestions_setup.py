"""Contrato sin red: /setup -> Moderación -> Sugerencias.
La selección es un borrador y solo Confirmar cambios puede persistirla.
"""
import ast
from pathlib import Path
from types import SimpleNamespace
import unittest


ROOT = Path(__file__).resolve().parents[1]
SUG = ast.parse((ROOT / "suggestions_setup.py").read_text(encoding="utf-8"))
BOT = ast.parse((ROOT / "bot.py").read_text(encoding="utf-8"))


def klass(name, tree=SUG):
    return next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == name)


def method(cls, name):
    return next(n for n in cls.body
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == name)


class SuggestionsSetupRegressionTests(unittest.TestCase):
    def test_configuration_is_accessible_from_moderation(self):
        view = klass("HeraldoModerationSetupView", BOT)
        action = ast.unparse(method(view, "suggestions"))
        self.assertIn("SuggestionsSetupView", action)
        self.assertIn("edit_message", action)
        self.assertIn("view=view", action)

    def test_both_selectors_and_buttons_have_separate_rows(self):
        view = klass("SuggestionsSetupView")
        init = ast.unparse(method(view, "__init__"))
        self.assertIn("discord.ui.ChannelSelect", init)
        self.assertIn("discord.ui.UserSelect", init)
        self.assertIn("self.pick_channel", init)
        self.assertIn("self.pick_user", init)
        self.assertIn("row=0", init)
        self.assertIn("row=1", init)
        self.assertIn("self._reset_channel_selection()", init)
        actions = {n.name for n in view.body if isinstance(n, ast.AsyncFunctionDef)}
        for action in ("pick_channel", "pick_user", "toggle_owner",
                       "remove_reviewer", "edit_panel", "publish_panel",
                       "save_changes", "discard_changes", "back"):
            self.assertIn(action, actions)

    def test_discord_five_width_limit_per_row(self):
        """ChannelSelect/UserSelect ocupan toda la fila; botones solo ancho 1."""
        view = klass("SuggestionsSetupView")
        occupation = {row: 0 for row in range(5)}
        initial = method(view, "__init__")
        selectors = []
        for node in ast.walk(initial):
            if (isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Attribute)
                    and node.func.attr in {"ChannelSelect", "UserSelect"}):
                selected_row = next(
                    ast.literal_eval(kw.value) for kw in node.keywords
                    if kw.arg == "row")
                selectors.append((node.func.attr, selected_row))
                occupation[selected_row] += 5
        self.assertEqual(selectors,
                         [("ChannelSelect", 0), ("UserSelect", 1)])
        for func in view.body:
            if not isinstance(func, ast.AsyncFunctionDef):
                continue
            for deco in func.decorator_list:
                if not (isinstance(deco, ast.Call)
                        and isinstance(deco.func, ast.Attribute)
                        and deco.func.attr == "button"):
                    continue
                button_row = next(
                    ast.literal_eval(kw.value) for kw in deco.keywords
                    if kw.arg == "row")
                self.assertIn(button_row, occupation)
                occupation[button_row] += 1
        self.assertEqual(occupation, {0: 5, 1: 5, 2: 2, 3: 2, 4: 3})
        for row, width in occupation.items():
            with self.subTest(row=row):
                self.assertLessEqual(width, 5)

    def test_draft_comparison_covers_channel_owner_and_reviewers(self):
        method_node = method(klass("SuggestionsSetupView"), "_dirty")
        module = ast.fix_missing_locations(ast.Module(body=[method_node], type_ignores=[]))
        ns = {}
        exec(compile(module, "suggestions_setup.py", "exec"), ns)
        obj = SimpleNamespace(
            pending_channel_id=None,
            original_owner=True, pending_owner=True,
            original_reviewers={101}, pending_reviewers={101})
        self.assertFalse(ns["_dirty"](obj))
        obj.pending_channel_id = 567
        self.assertTrue(ns["_dirty"](obj))
        obj.pending_channel_id = None
        obj.pending_owner = False
        self.assertTrue(ns["_dirty"](obj))
        obj.pending_owner = True
        obj.pending_reviewers = {101, 202}
        self.assertTrue(ns["_dirty"](obj))
        obj.pending_reviewers = {101}
        self.assertFalse(ns["_dirty"](obj))

    def test_channel_selection_never_saves_before_confirmation(self):
        view = klass("SuggestionsSetupView")
        select = ast.unparse(method(view, "pick_channel"))
        self.assertIn("pending_channel_id", select)
        self.assertIn("channel.permissions_for", select)
        self.assertIn("self._sync()", select)
        self.assertNotIn("suggestion_set_channel_id", select)
        self.assertNotIn("suggestion_publish_panel", select)
        self.assertIn("SuggestionsSetupConfirmView", ast.unparse(method(view, "save_changes")))
        discard = ast.unparse(method(view, "discard_changes"))
        self.assertIn("pending_channel_id = None", discard)
        self.assertIn("_reset_channel_selection()", discard)

    def test_confirmation_moves_panel_without_duplicate(self):
        confirm = ast.unparse(method(klass("SuggestionsSetupConfirmView"), "confirm"))
        self.assertIn("suggestion_get_channel_id", confirm)
        self.assertIn("suggestion_publish_panel", confirm)
        self.assertIn("previous.delete()", confirm)
        self.assertIn("suggestion_set_owner_enabled", confirm)
        self.assertIn("suggestion_add_reviewer", confirm)
        self.assertIn("suggestion_remove_reviewer", confirm)
        self.assertIn("editor.pending_channel_id = None", confirm)
        self.assertIn("interaction.edit_original_response", confirm)

    def test_republish_requires_saved_channel_and_confirmation(self):
        view = klass("SuggestionsSetupView")
        self.assertIn("self.publish_panel.disabled", ast.unparse(method(view, "_sync")))
        publish = ast.unparse(method(view, "publish_panel"))
        self.assertIn("SuggestionsSetupPublishConfirmView", publish)
        self.assertNotIn("suggestion_set_channel_id", publish)
        confirm = ast.unparse(method(klass("SuggestionsSetupPublishConfirmView"), "confirm"))
        self.assertIn("suggestion_ensure_panel", confirm)
        self.assertIn("channel.fetch_message", confirm)

    def test_message_editor_returns_to_same_setup_panel(self):
        view = klass("SuggestionsSetupView")
        text = ast.unparse(method(view, "edit_panel"))
        self.assertIn("suggestions_setup", text)
        studio = klass("DefaultMessageStudioView", BOT)
        back = ast.unparse(method(studio, "go_back"))
        self.assertIn("self.return_to", back)
        self.assertIn("suggestions_setup", back)
        self.assertIn("SuggestionsSetupView", back)

    def test_locales_have_same_keys(self):
        assignment = next(node for node in SUG.body
                          if isinstance(node, ast.Assign)
                          and any(isinstance(target, ast.Name) and target.id == "LANG"
                                  for target in node.targets))
        languages = ast.literal_eval(assignment.value)
        self.assertEqual(set(languages), {"es-419", "en-US", "pt-BR"})
        keys = [set(v) for v in languages.values()]
        self.assertTrue(all(keyset == keys[0] for keyset in keys[1:]))
        self.assertIn("channel_select", keys[0])
        self.assertIn("publish_panel", keys[0])
        self.assertIn("edit_panel", keys[0])


if __name__ == "__main__":
    unittest.main()
