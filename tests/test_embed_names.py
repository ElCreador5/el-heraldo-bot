"""Pruebas aisladas: nombres naturales en /embed y compatibilidad SQLite."""
from __future__ import annotations
import ast
import json
import re
import sqlite3
import tempfile
import unicodedata
import unittest
from datetime import datetime, timezone
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1] / "bot.py"
CODE = SOURCE.read_text("utf-8")
TREE = ast.parse(CODE)
FUNCS = {n.name: n for n in TREE.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}

def isolate(*names, namespace=None):
    body = [ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0)]
    body.extend(FUNCS[n] for n in names)
    mod = ast.fix_missing_locations(ast.Module(body=body, type_ignores=[]))
    env = dict(namespace or {})
    exec(compile(mod, str(SOURCE), "exec"), env)
    return env

class EmbedNamesTests(unittest.TestCase):
    def setUp(self):
        ns = isolate("embed_normalize_name", "embed_name_is_valid", namespace={
            "unicodedata": unicodedata, "re": re,
            "EMBED_NAME_MAX_LENGTH": 64,
            "EMBED_NAME_PUNCTUATION": frozenset(" -_.(),!:;¿?¡+#&"),
        })
        self.normalize = ns["embed_normalize_name"]
        self.valid = ns["embed_name_is_valid"]

    def test_existing_names_and_natural_spanish_names(self):
        examples = {
            "reglas_2026": "reglas_2026",
            "  REGLAS  del Servidor ": "reglas del servidor",
            "INFORMACIÓN GENERAL": "información general",
            "Área de pruebas": "área de pruebas",
            "Bienvenida 🪽": "bienvenida 🪽",
            "Avisos (versión 2)": "avisos (versión 2)",
            "Noticias y mensajes!": "noticias y mensajes!",
        }
        for raw, normalized in examples.items():
            with self.subTest(raw=raw):
                result = self.normalize(raw)
                self.assertEqual(result, normalized)
                self.assertTrue(self.valid(result))
        self.assertTrue(self.valid("x"*64))

    def test_blocks_oversize_markdown_mentions_controls(self):
        invalid = ("", " "*5, "x"*65, "@everyone", "ver\nreglas", "ver\treglas",
                   chr(96)+"recurso"+chr(96), "<@1234>", "reglas/ayuda", "a\u200db")
        for raw in invalid:
            with self.subTest(raw=repr(raw)):
                self.assertFalse(self.valid(self.normalize(raw)))

    def test_same_key_for_case_and_spacing(self):
        self.assertEqual(self.normalize("  INFORMACIÓN   GENERAL "),
                         self.normalize("información general"))

    def test_commands_share_normalization(self):
        for name in ("embed_create", "embed_edit", "embed_send_command",
                     "embed_delete_command", "embed_name_autocomplete"):
            with self.subTest(command=name):
                code = ast.get_source_segment(CODE, FUNCS[name])
                self.assertIn("embed_normalize_name(", code)
        self.assertIn("embed_name_is_valid(name)", ast.get_source_segment(CODE, FUNCS["embed_create"]))
        self.assertNotIn("EMBED_NAME_RE", CODE)

    def test_unicode_name_persists_with_guild_isolation(self):
        with tempfile.TemporaryDirectory() as directory:
            db = str(Path(directory) / "test.db")
            ns = isolate("_embed_conn", "embed_get", "embed_save", "embed_names", "embed_delete",
                         namespace={"db_connect": lambda: sqlite3.connect(db),
                                    "json": json, "sqlite3": sqlite3,
                                    "datetime": datetime, "timezone": timezone})
            key = self.normalize("Guía de inicio 🪽")
            ns["embed_save"](10, key, {"title": "Prueba"})
            self.assertEqual(ns["embed_get"](10, key)[0]["title"], "Prueba")
            self.assertIsNone(ns["embed_get"](11, key))
            self.assertEqual(ns["embed_names"](10), [(key, 0)])
            self.assertTrue(ns["embed_delete"](10, key))
            self.assertIsNone(ns["embed_get"](10, key))

if __name__ == "__main__":
    unittest.main()
