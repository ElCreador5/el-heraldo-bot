"""Pruebas aisladas del borrador de los selectores de /setup, sin arrancar Discord."""
from i18n_source_helpers import source_text as _source_text
import ast
import asyncio
import copy
from pathlib import Path
from types import SimpleNamespace
import unittest


TREE = ast.parse(_source_text(Path(__file__).resolve().parents[1] / 'bot.py', encoding='utf-8'))


def isolated_method(class_name, method_name, env=None):
    """Compila solo el callback real del repositorio, suprimiendo las anotaciones."""
    node = next(c for c in TREE.body if isinstance(c, ast.ClassDef) and c.name == class_name)
    method = copy.deepcopy(next(
        n for n in node.body if isinstance(n, ast.AsyncFunctionDef) and n.name == method_name
    ))
    method.decorator_list = []
    method.returns = None
    for arg in method.args.posonlyargs + method.args.args + method.args.kwonlyargs:
        arg.annotation = None
    module = ast.fix_missing_locations(ast.Module(body=[method], type_ignores=[]))
    namespace = dict(env or {})
    exec(compile(module, str(Path(__file__)), "exec"), namespace)
    return namespace[method_name]


class Response:
    def __init__(self):
        self.edited = None
        self.sent = None

    async def edit_message(self, **kwargs):
        self.edited = kwargs

    async def send_message(self, content, **kwargs):
        self.sent = (content, kwargs)


class SelectorBehaviorTests(unittest.TestCase):
    def test_report_option_clears_purge_in_draft_only(self):
        original = [{"emoji": "x", "label": "Aviso", "action": "timeout",
                     "threshold": 2, "duration_minutes": 30, "purge_minutes": 15}]
        view = SimpleNamespace(selected_reaction_index=0, pending_reactions=None)
        view._working_reactions = lambda: view.pending_reactions if view.pending_reactions is not None else original
        view._rebuild_reaction_select = lambda: None
        view._content = lambda guild: "Resumen"
        response = Response()
        interaction = SimpleNamespace(data={"values": ["report"]}, guild=None, response=response)
        callback = isolated_method("HeraldoUserReportsSetupView", "select_action",
                                   {"MODERATION_REPORT_ACTIONS":
                                    {"report", "timeout", "condemn", "kick", "ban"}})
        asyncio.run(callback(view, interaction))
        self.assertEqual(original[0]["action"], "timeout")
        self.assertEqual(original[0]["purge_minutes"], 15)
        self.assertEqual(view.pending_reactions[0]["action"], "report")
        self.assertIsNone(view.pending_reactions[0]["purge_minutes"])
        self.assertIn("Solo reportar", response.edited["content"])

    def test_unknown_report_action_never_alters_draft(self):
        original = [{"action": "report", "purge_minutes": None}]
        view = SimpleNamespace(selected_reaction_index=0, pending_reactions=None)
        view._working_reactions = lambda: original
        response = Response()
        interaction = SimpleNamespace(data={"values": ["unexpected"]}, response=response)
        callback = isolated_method("HeraldoUserReportsSetupView", "select_action",
                                   {"MODERATION_REPORT_ACTIONS": {"report", "timeout", "condemn", "kick", "ban"}})
        asyncio.run(callback(view, interaction))
        self.assertIsNone(view.pending_reactions)
        self.assertIsNotNone(response.sent)

    def test_motw_day_selection_updates_only_preview(self):
        options = [SimpleNamespace(value=str(i), default=i == 1) for i in range(7)]
        view = SimpleNamespace(weekday=1, hour=18,
                               day_select=SimpleNamespace(options=options))
        def sync_controls():
            for option in view.day_select.options:
                option.default = option.value == str(view.weekday)
        view._sync_controls = sync_controls
        view._content = lambda guild: "Horario propuesto"
        response = Response()
        interaction = SimpleNamespace(data={"values": ["6"]}, guild=None, response=response)
        callback = isolated_method("HeraldoMotwSetupView", "select_day")
        asyncio.run(callback(view, interaction))
        self.assertEqual(view.weekday, 6)
        self.assertEqual([x.value for x in options if x.default], ["6"])
        self.assertEqual(response.edited["content"], "Horario propuesto")

    def test_invalid_motw_hour_does_not_change_selection(self):
        options = [SimpleNamespace(value=str(i), default=i == 9) for i in range(24)]
        view = SimpleNamespace(hour=9, hour_select=SimpleNamespace(options=options))
        response = Response()
        interaction = SimpleNamespace(data={"values": ["24"]}, response=response)
        callback = isolated_method("HeraldoMotwSetupView", "select_hour")
        asyncio.run(callback(view, interaction))
        self.assertEqual(view.hour, 9)
        self.assertIsNotNone(response.sent)


if __name__ == "__main__":
    unittest.main()
