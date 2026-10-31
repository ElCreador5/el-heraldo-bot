"""Regression test: log category options must not send invalid emoji payloads."""
from i18n_source_helpers import source_text as _source_text
import ast
from pathlib import Path
import unittest


class LogCategorySelectTests(unittest.TestCase):
    def test_log_category_options_do_not_use_invalid_emoji(self):
        source = _source_text(Path(__file__).resolve().parents[1].joinpath('bot.py'), encoding='utf-8')
        module = ast.parse(source)
        categories = next(
            ast.literal_eval(node.value)
            for node in module.body
            if isinstance(node, ast.Assign)
            and any(isinstance(target, ast.Name) and target.id == "LOG_TEMPLATE_CATEGORIES"
                    for target in node.targets)
        )
        self.assertTrue(categories)
        self.assertTrue(all(0 < len(label) <= 100 for label, _ in categories.values()))

        editor = next(
            node for node in module.body
            if isinstance(node, ast.ClassDef) and node.name == "LogTemplateEditorView"
        )
        initializer = next(
            node for node in editor.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == "__init__"
        )
        category_options = [
            node for node in ast.walk(initializer)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "SelectOption"
            and any(keyword.arg == "description" for keyword in node.keywords)
            and any(keyword.arg == "default" for keyword in node.keywords)
        ]
        self.assertEqual(len(category_options), 1)
        option = category_options[0]
        self.assertNotIn("emoji", [keyword.arg for keyword in option.keywords])
        label = next(keyword.value for keyword in option.keywords if keyword.arg == "label")
        self.assertIsInstance(label, ast.Subscript)
        self.assertIsInstance(label.value, ast.Name)
        self.assertEqual(label.value.id, "label")


    def test_member_log_selection_stays_marked_until_save_or_discard(self):
        source = _source_text(Path(__file__).resolve().parents[1].joinpath('bot.py'), encoding='utf-8')
        module = ast.parse(source)
        view = next(node for node in module.body
                    if isinstance(node, ast.ClassDef) and node.name == "HeraldoMemberLogSetupView")
        initializer = next(node for node in view.body
                           if isinstance(node, ast.FunctionDef) and node.name == "__init__")
        callback = next(node for node in view.body
                        if isinstance(node, ast.AsyncFunctionDef) and node.name == "select_event")
        init_code = ast.unparse(initializer)
        callback_code = ast.unparse(callback)
        self.assertIn("self.event_select = discord.ui.Select(", init_code)
        self.assertIn("default=False", init_code)
        self.assertIn("option.default = option.value == self.event_key", callback_code)
        self.assertIn("view=self", callback_code)
        for method_name in ("save", "discard"):
            method = next(node for node in view.body
                          if isinstance(node, ast.AsyncFunctionDef) and node.name == method_name)
            code = ast.unparse(method)
            self.assertIn("option.default = False", code)
            self.assertIn("view=self", code)


if __name__ == "__main__":
    unittest.main()
