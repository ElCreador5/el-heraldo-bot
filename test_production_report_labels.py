"""Promoción selectiva: etiquetas propias de reportes sin traducir texto libre."""
from pathlib import Path
import unittest

from production_report_labels import report_label, DEFAULTS


class ReportLabelsMainTests(unittest.TestCase):
    def test_catalog_defaults_in_three_languages(self):
        expected = {
            "🚩": "Inappropriate content / not permitted",
            "🤓": "Suspect (possible fake account or fraud)",
            "🔞": "Possible minor",
            "📢": "Spam",
        }
        for emoji, name in expected.items():
            with self.subTest(emoji=emoji):
                self.assertEqual(
                    report_label({"emoji": emoji, "label": DEFAULTS[emoji]["es-419"]}, "en-US"),
                    name,
                )
        self.assertEqual(
            report_label({"emoji": "🔞", "label": "Posible menor de edad"}, "pt-BR"),
            "Possível menor de idade",
        )

    def test_user_authored_label_not_changed(self):
        item = {"emoji": "🚩", "label": "Mi motivo personal: spam"}
        for locale in ("es-419", "en-US", "pt-BR"):
            self.assertEqual(report_label(item, locale), item["label"])

    def test_wrong_emoji_never_classified_as_default(self):
        item = {"emoji": "🦋", "label": "Posible menor de edad"}
        self.assertEqual(report_label(item, "en-US"), item["label"])

    def test_main_language_reads_saved_setting_but_defaults_to_spanish(self):
        source = (Path(__file__).resolve().parent / "bot.py").read_text(encoding="utf-8")
        self.assertIn('configured = guild_config_get(guild_id, "language") or "es-419"', source)
        self.assertIn('production_report_labels.report_label(item, guild_language(guild.id))', source)


if __name__ == "__main__":
    unittest.main()
