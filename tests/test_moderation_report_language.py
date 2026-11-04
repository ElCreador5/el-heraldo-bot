"""Regresión: recordatorios públicos sin categorías en español al elegir inglés."""
import ast
import unittest
from pathlib import Path

import heraldo_i18n as i18n
import moderation_report_labels
from test_safety_regressions import b


class ReportLabelsLocaleTests(unittest.TestCase):
    def _rules(self):
        return [
            {"emoji": emoji, "label": i18n.CATALOGS["es-419"].messages[key],
             "action": "report", "threshold": threshold}
            for emoji, key, threshold in [
                ("📢", "text.94a9eac404c8c6", 2),
                ("🚩", "text.ce9c8e559ad9fe", 3),
                ("🤓", "text.fa7c7004213f04", 2),
                ("🔞", "text.bdfac38f2af4cc", 2),
            ]
        ]

    def test_saved_spanish_default_labels_display_in_english(self):
        gid = 9937331
        b.guild_config_set(gid, "language", "en-US")
        b.set_moderation_report_reactions(gid, self._rules())
        preview = b.reminder_preview(gid)
        self.assertIn("**How to help with moderation**", preview)
        self.assertIn("📢 Spam: 2 reports from different people", preview)
        self.assertIn("🚩 Inappropriate content / not permitted: 3 reports from different people", preview)
        self.assertIn("🤓 Suspect (possible fake account or fraud): 2 reports", preview)
        self.assertIn("🔞 Possible minor: 2 reports", preview)
        self.assertNotIn("Contenido inapropiado", preview)
        self.assertNotIn("Sospechoso (posible", preview)
        self.assertNotIn("Posible menor de edad", preview)

    def test_switch_to_portuguese_without_modifying_saved_rules(self):
        gid = 9937332
        b.guild_config_set(gid, "language", "en-US")
        rules = self._rules()
        b.set_moderation_report_reactions(gid, rules)
        before = b.guild_config_get(gid, "moderation_report_reactions")
        b.guild_config_set(gid, "language", "pt-BR")
        preview = b.reminder_preview(gid)
        self.assertIn("Conteúdo inadequado / não permitido", preview)
        self.assertIn("Suspeito (possível conta falsa ou fraude)", preview)
        self.assertEqual(b.guild_config_get(gid, "moderation_report_reactions"), before)

    def test_manual_labels_survive_language_change(self):
        gid = 9937333
        b.guild_config_set(gid, "language", "en-US")
        rules = self._rules()
        rules[1]["label"] = "Mi categoría personalizada (no traducir)"
        b.set_moderation_report_reactions(gid, rules)
        preview = b.reminder_preview(gid)
        self.assertIn("Mi categoría personalizada (no traducir)", preview)
        self.assertIn("📢 Spam", preview)

    def test_renamed_emoji_never_triggers_default_translation(self):
        item = {"emoji": "🧩", "label": "Contenido inapropiado / no permitido"}
        self.assertEqual(
            moderation_report_labels.report_label(item, "en-US"),
            item["label"],
        )

    def test_existing_publications_refreshed_on_save_and_startup(self):
        source = (Path(__file__).resolve().parents[1] / "bot.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        ready = next(n for n in tree.body if isinstance(n, ast.AsyncFunctionDef) and n.name == "on_ready")
        view = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "HeraldoLanguageView")
        save = next(n for n in view.body if isinstance(n, ast.AsyncFunctionDef) and n.name == "save")
        refresh = next(n for n in tree.body if isinstance(n, ast.AsyncFunctionDef) and n.name == "refresh_report_reminder_publications")
        self.assertIn("await refresh_report_reminder_publications(guild)", ast.unparse(ready))
        self.assertIn("await refresh_report_reminder_publications(interaction.guild)", ast.unparse(save))
        self.assertIn("message.embeds[0].description", ast.unparse(refresh))
        self.assertIn("allowed_mentions=discord.AllowedMentions.none()", ast.unparse(refresh))


if __name__ == "__main__":
    unittest.main()
