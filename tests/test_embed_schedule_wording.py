"""Regresiones editoriales del programador de embeds."""
from __future__ import annotations
import ast
import unittest
from pathlib import Path
from datetime import datetime, timezone, timedelta
from types import SimpleNamespace

SOURCE = (Path(__file__).resolve().parents[1] / "bot.py").read_text("utf-8")
TREE = ast.parse(SOURCE)
def get(name):
    matches = [n for n in TREE.body if isinstance(n, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == name]
    assert len(matches) == 1, name
    return matches[0]
def method(name, key):
    return next(n for n in get(name).body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == key)
def content(node):
    return ast.get_source_segment(SOURCE, node)

class ScheduleWordingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        block = ast.fix_missing_locations(ast.Module(body=[
            ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0),
            get("embed_schedule_human_details"),
        ], type_ignores=[]))
        env = {"datetime":datetime, "embed_schedule_engine": SimpleNamespace(RD=timezone(timedelta(hours=-4)))}
        exec(compile(block, "bot.py", "exec"), env)
        cls.describe = staticmethod(env["embed_schedule_human_details"])

    def test_counter_explained_without_json(self):
        value = self.describe("messages", {"count":10})
        self.assertIn("cada 10 mensajes",value)
        self.assertIn("bots",value)
        self.assertNotIn('"count"', value)

    def test_all_modes_describe_actual_behavior(self):
        examples = [
            ("once",{"when":"2026-12-03T18:00:00-04:00"},"03/12/2026"),
            ("interval",{"interval":"6h"},"cada 6h"),
            ("daily",{"time":"18:00"},"Cada día"),
            ("weekly",{"days":[0,2],"time":"18:00"},"lunes, miércoles"),
            ("monthly",{"days":[1,15],"time":"18:00"},"días 1, 15"),
        ]
        for mode,cfg,expect in examples:
            with self.subTest(mode=mode):
                value = self.describe(mode,cfg)
                self.assertIn(expect,value)
                self.assertNotIn("{",value)
        self.assertEqual(self.describe("messages",None),"Pendiente de configurar.")

    def test_state_and_review_labels_coherent(self):
        code = content(method("EmbedScheduleView","summary"))
        self.assertIn("if self.reviewed:",code)
        self.assertIn("if self.active else 'Desactivada'",code)
        self.assertIn("embed_schedule_human_details(",code)
        self.assertNotIn("json.dumps(",code)
        self.assertNotIn(r"\\n\\n",code)

    def test_option_changes_reset_confirmation(self):
        klass = "EmbedScheduleView"
        for m in ["select_channel","select_mode","toggle"]:
            self.assertIn("invalidate_review()",content(method(klass,m)))
        self.assertIn("self.reviewed = False",content(method(klass,"invalidate_review")))
        self.assertIn("if not self.reviewed:",content(method(klass,"save")))
        self.assertIn("invalidate_review()",content(method("EmbedScheduleOptionsModal","on_submit")))
        self.assertNotIn("conn.commit",content(method(klass,"cancel")))

    def test_no_literal_newline_sequences_in_confirmation(self):
        for klass,fn in [("EmbedScheduleView","save"),("EmbedScheduleEditView","save_existing"),("EmbedSchedulesManageView","edit_schedule")]:
            self.assertNotIn(r"\\n\\n",content(method(klass,fn)))

    def test_irrelevant_modal_field_removed(self):
        self.assertIn("self.remove_item(self.when)",content(method("EmbedScheduleOptionsModal","__init__")))

if __name__ == "__main__":
    unittest.main()
