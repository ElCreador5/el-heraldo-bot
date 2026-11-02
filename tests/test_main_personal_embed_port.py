"""Regresión estática de la integración selectiva de embeds a main."""
import ast
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]

class MainPersonalEmbedTests(unittest.TestCase):
    def test_required_modules_are_present(self):
        for name in ("personal_embeds.py", "autofeed_embed_builder.py", "personal_embed_support.py"):
            self.assertTrue((ROOT / name).is_file(), name)
            ast.parse((ROOT / name).read_text(encoding="utf-8"))

    def test_admin_embed_command_is_replaced_by_personal(self):
        source = (ROOT / "bot.py").read_text(encoding="utf-8")
        ast.parse(source)
        self.assertIn('bot.tree.remove_command("embed")', source)
        self.assertIn('_personal_embeds.install({"bot": bot, "stamp_embed": stamp_embed})', source)
        self.assertIn('{"embed", "profile"}', source)

    def test_personal_builder_does_not_depend_on_lab_modules(self):
        source = (ROOT / "autofeed_embed_builder.py").read_text(encoding="utf-8")
        for dependency in ("from message_autofeeds", "from autofeed_setup", "from heraldo_i18n"):
            self.assertNotIn(dependency, source)

if __name__ == "__main__":
    unittest.main()
