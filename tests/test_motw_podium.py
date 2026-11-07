"""Regresiones del podio de Miembro de la Semana (sin conectar a Discord)."""
import ast
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "bot.py").read_text(encoding="utf-8")
TREE = ast.parse(SOURCE)


def function(name):
    return next(node for node in TREE.body
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                and node.name == name)


class MemberOfTheWeekPodiumTests(unittest.TestCase):
    def test_weekly_ranking_uses_persisted_weekly_message_counts(self):
        source = ast.unparse(function("db_week_ranking"))
        self.assertIn("week_messages", source)
        self.assertIn("week_messages DESC", source)

    def test_podium_keeps_three_eligible_members(self):
        source = ast.unparse(function("announce_member_of_the_week"))
        self.assertIn("len(ranking) == 3", source)
        self.assertIn("not member.bot", source)
        self.assertIn("condemnation_get", source)
        self.assertIn("hp_punish_role_id", source)
        self.assertIn("enumerate(ranking)", source)
        self.assertIn("member.mention", source)
        self.assertIn("count:,", source)
        self.assertIn("motw.podium_title", source)

    def test_test_announcement_does_not_reset_week(self):
        source = ast.unparse(function("announce_member_of_the_week"))
        self.assertIn("if reset:\n        db_reset_week(guild.id)", source)
        test_source = ast.unparse(function("motw_test"))
        self.assertIn("reset=False", test_source)

    def test_ranking_labels_translated_for_every_supported_locale(self):
        import heraldo_i18n
        for locale in heraldo_i18n.TARGET_LOCALES:
            messages = heraldo_i18n.CATALOGS[locale].messages
            for key in ("motw.podium_title", "motw.first_place",
                        "motw.second_place", "motw.third_place"):
                with self.subTest(locale=locale, key=key):
                    self.assertTrue(messages.get(key))


if __name__ == "__main__":
    unittest.main()
