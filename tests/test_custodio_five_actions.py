"""Contrato de las cinco acciones visibles de Custodio, sin sancionar."""
import unittest

from custodio_rule_actions import DEFAULT_ACTIONS, VALID_ACTIONS, encode_actions, decode_actions
from custodio_rule_actions_setup import ACTION_LABELS


class CustodioFiveActionsTests(unittest.TestCase):
    def test_all_five_actions_are_available(self):
        self.assertEqual(VALID_ACTIONS, {"report", "warn", "ban", "temp_ban", "kick"})
        self.assertEqual(set(ACTION_LABELS), VALID_ACTIONS)

    def test_drafts_never_enable_enforcement(self):
        for action in VALID_ACTIONS:
            with self.subTest(action=action):
                actions = {**DEFAULT_ACTIONS, "spam": action}
                raw = encode_actions(actions)
                saved, valid = decode_actions(raw)
                self.assertTrue(valid)
                self.assertEqual(saved, actions)
                self.assertIn('"enforcement_enabled":false', raw)

    def test_default_always_reports_only(self):
        self.assertEqual(set(DEFAULT_ACTIONS.values()), {"report"})


if __name__ == "__main__":
    unittest.main()
