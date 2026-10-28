"""Garantías contra publicaciones de idiomas incompletos."""
import ast
from pathlib import Path
import unittest
from heraldo_i18n import (
    CATALOGS, DEFAULT_LOCALE, SUPPORTED_LOCALES, TARGET_LOCALES,
    TranslationUnavailable, translate, verify_catalogs,
)

BOT = Path(__file__).resolve().parents[1] / "bot.py"


class I18nCatalogTests(unittest.TestCase):
    def test_same_keys_and_variables_in_three_catalogs(self):
        verify_catalogs()
        self.assertEqual(set(CATALOGS), set(TARGET_LOCALES))

    def test_partial_languages_are_available_with_explicit_status(self):
        from heraldo_i18n import PARTIAL_LOCALES
        self.assertEqual(SUPPORTED_LOCALES, frozenset(TARGET_LOCALES))
        self.assertEqual(PARTIAL_LOCALES, frozenset({"en-US", "pt-BR"}))
        for locale in PARTIAL_LOCALES:
            self.assertTrue(translate(locale, "language.title"))
            self.assertEqual(translate(locale, "language.help"), {
                "en-US": "Other bot features may appear in Spanish. In development.",
                "pt-BR": "Outras funções do bot podem aparecer em espanhol. Em desenvolvimento.",
            }[locale])


    def test_custom_messages_section_has_templates_name_in_every_language(self):
        names = {"es-419": ("Plantillas", "Mensajes personalizados"),
                 "en-US": ("Templates", "Custom messages"),
                 "pt-BR": ("Modelos", "Mensagens personalizadas")}
        for locale, (current, previous) in names.items():
            with self.subTest(locale=locale):
                self.assertEqual(translate(locale, "text.f4ea025e8c2221"), current)
                description = translate(locale, "text.685b989ce71932")
                panel = translate(locale, "text.6902f6b5d77eb7")
                self.assertIn(current.casefold(), description.casefold())
                self.assertIn(current, panel)
                self.assertNotIn(previous, panel)
                self.assertNotIn(previous.casefold(), description.casefold())


    def test_templates_panel_explains_its_controls_without_external_commands(self):
        labels = {"es-419": ("Seleccione una plantilla", "Publicar"),
                  "en-US": ("Select a template", "Publish"),
                  "pt-BR": ("Selecione um modelo", "Publicar")}
        for locale, (selection, publish) in labels.items():
            with self.subTest(locale=locale):
                content = translate(locale, "text.038abcdd85c82f")
                self.assertIn(selection, content)
                self.assertIn(publish, content)
                self.assertNotIn("/editar_plantilla", content)

    def test_missing_key_raises_instead_of_using_spanish(self):
        with self.assertRaises(TranslationUnavailable):
            translate("es-419", "nonexistent")

    def test_setup_and_language_use_same_per_guild_preference(self):
        tree = ast.parse(BOT.read_text(encoding="utf-8"))
        code = ast.unparse(tree)
        self.assertIn("guild_config_get(guild_id, 'language')", code)
        self.assertIn("HeraldoLanguageView", code)
        self.assertIn("LANGUAGE_READY", code)


if __name__ == "__main__":
    unittest.main()
