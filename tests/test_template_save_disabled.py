"""El guardado de plantillas no debe habilitarse con un borrador intacto."""
import ast
from pathlib import Path
from types import SimpleNamespace
import unittest


SOURCE = ast.parse((Path(__file__).resolve().parents[1] / "template_native_builder.py").read_text(encoding="utf-8"))
EDITOR = next(node for node in SOURCE.body
              if isinstance(node, ast.ClassDef) and node.name == "TemplateEditorView")
FUNCTION = next(node for node in EDITOR.body
                if isinstance(node, ast.FunctionDef) and node.name == "_template_has_changes")
MODULE = ast.fix_missing_locations(ast.Module(body=[FUNCTION], type_ignores=[]))
NS = {}
exec(compile(MODULE, "template_native_builder.py", "exec"), NS)
HAS_CHANGES = NS["_template_has_changes"]


class TestTemplateSaveDisabled(unittest.TestCase):
    def test_new_template_needs_content(self):
        editor = SimpleNamespace(original_template=None, name="", text="", embed=None, extra_embeds=[])
        self.assertFalse(HAS_CHANGES(editor))
        editor.name = "Aviso"
        self.assertTrue(HAS_CHANGES(editor))
        editor.name = ""
        editor.text = "Mensaje"
        self.assertTrue(HAS_CHANGES(editor))

    def test_existing_template_compares_saved_version(self):
        class Editor:
            original_template = {"name": "Aviso"}
            def __init__(self):
                self.saved = True
            def _is_saved(self):
                return self.saved
        editor = Editor()
        self.assertFalse(HAS_CHANGES(editor))
        editor.saved = False
        self.assertTrue(HAS_CHANGES(editor))
        editor.saved = True
        self.assertFalse(HAS_CHANGES(editor))

    def test_serialization_controls_button(self):
        rendered = ast.unparse(next(node for node in EDITOR.body
                                    if isinstance(node, ast.FunctionDef)
                                    and node.name == "to_components"))
        self.assertIn("self.save.disabled = not changed", rendered)
        self.assertIn("return super().to_components()", rendered)


if __name__ == "__main__":
    unittest.main()
