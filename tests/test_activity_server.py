import unittest
from pathlib import Path
import activity_server

class TestActivityFiles(unittest.TestCase):
    def test_page_contains_carl_sections(self):
        html = (activity_server.ROOT / "index.html").read_text(encoding="utf-8")
        for section in ("Canal", "Mensaje", "Mostrar editor de embed", "Fecha",
                        "Rol para mencionar", "Repetir cada", "Crear mensaje"):
            self.assertIn(section, html)

    def test_sdk_uses_mapped_same_origin(self):
        js = (activity_server.ROOT / "main.js").read_text(encoding="utf-8")
        self.assertIn("import('/sdk/@discord/embedded-app-sdk@2.5.0')", js)
        self.assertNotIn("import('https://esm.sh/", js)

    def test_no_browser_bot_secrets(self):
        for path in ("main.js", "index.html"):
            content = (activity_server.ROOT / path).read_text(encoding="utf-8")
            self.assertNotIn("DISCORD_TOKEN", content)
            self.assertNotIn("DISCORD_ACTIVITY_CLIENT_SECRET", content)

    def test_assets_exist(self):
        for name in ("style.css", "main.js"):
            self.assertTrue((activity_server.ROOT / name).exists())

if __name__ == "__main__":
    unittest.main()
