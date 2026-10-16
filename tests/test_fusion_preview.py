"""Regresiones aisladas del flujo de fusión de canales y su seguridad."""
from __future__ import annotations

import ast
import re
import unittest
from pathlib import Path
from types import SimpleNamespace

SOURCE = (Path(__file__).resolve().parents[1] / "bot.py").read_text("utf-8")
TREE = ast.parse(SOURCE)
TOP = {node.name: node for node in TREE.body if isinstance(
    node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
)}


def fragment(cls, method):
    return next(node for node in TOP[cls].body
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                and node.name == method)


class FakeEmbed:
    def __init__(self, *, title, description, color):
        self.title, self.description, self.color = title, description, color
        self.fields = []
        self.footer = None

    def add_field(self, *, name, value, inline):
        self.fields.append(SimpleNamespace(name=name, value=value, inline=inline))

    def set_footer(self, *, text):
        self.footer = text


def make_preview():
    definitions = [TOP[name] for name in ("fusion_channel_label", "fusion_preview_embed")]
    module = ast.fix_missing_locations(ast.Module(
        body=[ast.ImportFrom(module="__future__",
            names=[ast.alias(name="annotations")], level=0), *definitions],
        type_ignores=[],
    ))
    globals_ = {"discord": SimpleNamespace(
        Embed=FakeEmbed, Color=SimpleNamespace(orange=lambda: "naranja"),
    )}
    exec(compile(module, "<fusion-preview>", "exec"), globals_)
    return globals_["fusion_preview_embed"]


class FusionPreviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.preview = staticmethod(make_preview())
        cls.origen = SimpleNamespace(name="general", mention="#general")
        cls.destino = SimpleNamespace(name="pruebas-heraldo", mention="#pruebas-heraldo")

    def fields(self, embed):
        return {field.name: field.value for field in embed.fields}

    def test_flow_is_explicit_and_chronological(self):
        embed = self.preview(self.origen, self.destino, "canal-final", True, 3)
        self.assertIn("#general", embed.description)
        self.assertIn("#pruebas-heraldo", embed.description)
        self.assertLess(embed.description.index("#general"), embed.description.index("#pruebas-heraldo"))
        self.assertIn("se conservan", embed.description)
        fields = self.fields(embed)
        self.assertIn("3", fields["Mensajes del origen"])
        self.assertIn("canal-final", fields["Nombre final del destino"])
        self.assertIn("solo si", fields["Canal origen al terminar"].lower())
        flow = fields["Orden de ejecución"]
        for n in range(1, 6):
            self.assertIn(f"**{n}.", flow)
        for a, b in zip(range(1, 5), range(2, 6)):
            self.assertLess(flow.index(f"**{a}."), flow.index(f"**{b}."))
        self.assertIn("más antiguo a más reciente", flow)
        self.assertIn("al final de", flow)
        self.assertIn("adjuntos", flow)
        self.assertIn("no aparecen mensajes nuevos", flow)
        self.assertIn("Volver", embed.footer)

    def test_retained_origin_and_name_without_rename(self):
        embed = self.preview(self.origen, self.destino, "pruebas-heraldo", False, 17)
        f = self.fields(embed)
        self.assertEqual(f["Canal origen al terminar"], "Conservar")
        self.assertIn("Conservar el nombre actual", f["Orden de ejecución"])
        self.assertIn("Conservarlo", f["Orden de ejecución"])
        self.assertIn("17", f["Mensajes del origen"])

    def test_buttons_match_semantic_palette_and_back_opens_draft(self):
        cls = TOP["FusionChannelsView"]
        styles = {}
        for node in cls.body:
            if not isinstance(node, ast.AsyncFunctionDef):
                continue
            for dec in node.decorator_list:
                if not isinstance(dec, ast.Call):
                    continue
                opts = {kw.arg: kw.value for kw in dec.keywords}
                label = opts.get("label")
                style = opts.get("style")
                if isinstance(label, ast.Constant):
                    styles[label.value] = getattr(style, "attr", None)
        self.assertEqual(styles.get("Confirmar fusión"), "success")
        self.assertEqual(styles.get("Volver"), "secondary")
        self.assertEqual(styles.get("Cancelar"), "danger")
        self.assertIn("FusionChannelsEditView(", ast.unparse(fragment("FusionChannelsView", "back")))

    def test_editing_is_a_draft_and_refreshes_the_count(self):
        editor = TOP["FusionChannelsEditView"]
        self.assertTrue(any(isinstance(n, ast.FunctionDef) and n.name == "summary"
                            for n in editor.body))
        for method in ("select_source", "select_destination", "select_name",
                       "edit_name", "toggle_source"):
            body = ast.unparse(fragment("FusionChannelsEditView", method))
            self.assertNotIn(".delete(", body)
            self.assertNotIn(".commit(", body)
            self.assertNotIn("execute_channel_merge(", body)
        submit = ast.unparse(fragment("FusionChannelsEditView", "preview"))
        self.assertIn("collect_fusion_messages(origen)", submit)
        self.assertIn("FusionChannelsView(", submit)
        self.assertIn("response.defer()", submit)

    def test_count_change_or_revoked_permissions_block_changes(self):
        fn = ast.unparse(TOP["execute_channel_merge"])
        self.assertIn("len(messages) != expected_count", fn)
        self.assertLess(fn.index("len(messages) != expected_count"),
                        fn.index("destino.edit("))
        self.assertIn("not interaction.user.guild_permissions.manage_channels", fn)
        self.assertIn("src_perms.read_message_history", fn)
        self.assertIn("dest_perms.send_messages", fn)
        self.assertIn("source_changed", fn)
        self.assertIn("getattr(m, 'edited_at', None)", fn)
        self.assertLess(fn.index("current_messages = await collect_fusion_messages(origen)"),
                        fn.index("await origen.delete("))

if __name__ == "__main__":
    unittest.main()
