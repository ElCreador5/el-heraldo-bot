"""Nested dropdown panels keep the originating server's language."""
from types import SimpleNamespace
from unittest.mock import patch
import unittest
import heraldo_i18n as i18n


class Panel:
    def __init__(self, guild_id):
        self.guild_id = guild_id


class NestedView:
    def __init__(self, panel):
        self.panel = panel

    @i18n.guild_context
    def title(self):
        return str(i18n.text("language.save"))


class I18nPanelContextTests(unittest.TestCase):
    def test_nested_panel_uses_own_server_not_user_locale(self):
        with patch.object(i18n, "_locale_resolver",
                          lambda guild_id: {10: "en-US", 20: "pt-BR"}[guild_id]):
            a = NestedView(Panel(10))
            b = NestedView(Panel(20))
            self.assertEqual(a.title(), "Save changes")
            self.assertEqual(b.title(), "Salvar alterações")
            self.assertIsNone(i18n.current_guild_id())

    def test_parent_panel_does_not_change_explicit_user_data(self):
        with patch.object(i18n, "_locale_resolver", lambda _: "en-US"):
            panel = NestedView(Panel(10))
            self.assertEqual(panel.title(), "Save changes")
            self.assertEqual(i18n.current_locale(), "es-419")


if __name__ == "__main__":
    unittest.main()
