import unittest
from pathlib import Path
import activity_server

class TestActivityFiles(unittest.TestCase):
    def test_page_contains_carl_sections(self):
        html = (activity_server.ROOT / "index.html").read_text(encoding="utf-8")
        for section in ("Canal", "Mensaje", "Mostrar editor de embed", "Fecha",
                        "Rol para mencionar", "Repetir cada", "Crear mensaje"):
            self.assertIn(section, html)

    def test_assets_exist(self):
        for name in ("style.css", "main.js"):
            self.assertTrue((activity_server.ROOT / name).exists())

if __name__ == "__main__":
    unittest.main()
