"""Seguridad de plantillas para acciones por tipo de regla."""
import unittest

from custodio_rule_actions import (
    SETTING_KEY, TEMPLATES, DEFAULT_ACTIONS, InvalidRuleActions,
    decode_actions, encode_actions, load_actions, preview_action,
    suggested_action, enforcement_permitted,
)


class RuleActionPolicyTests(unittest.TestCase):
    def test_default_rules_never_sanction(self):
        self.assertEqual(set(DEFAULT_ACTIONS.values()), {"report"})
        self.assertEqual(suggested_action("harassment"), "kick")
        self.assertEqual(suggested_action("scams"), "ban")
        self.assertEqual(suggested_action("threats"), "ban")
        self.assertEqual(len(TEMPLATES), 5)

    def test_roundtrip_inactive_and_local_to_guild(self):
        values = {}
        get = lambda guild, key: values.get((guild, key))
        self.assertFalse(load_actions(get, 1)[1])
        changed = DEFAULT_ACTIONS.copy()
        changed["scams"] = "ban"
        values[(1, SETTING_KEY)] = encode_actions(changed)
        self.assertEqual(load_actions(get, 1), (changed, True))
        self.assertEqual(load_actions(get, 2), (DEFAULT_ACTIONS, False))
        self.assertIn('"enforcement_enabled":false', values[(1, SETTING_KEY)])

    def test_corrupt_data_never_enables_enforcement(self):
        for raw in (
            "", "null", "{}", "{bad}", '{"version":1,"enforcement_enabled":true,"actions":{}}',
            '{"version":2,"enforcement_enabled":false,"actions":{}}',
            "x" * 5000,
        ):
            with self.subTest(raw=raw[:20]):
                self.assertEqual(decode_actions(raw), (DEFAULT_ACTIONS, False))

    def test_rejects_unknown_category_and_unknown_action(self):
        for bad in (
            {**DEFAULT_ACTIONS, "other": "ban"},
            {**DEFAULT_ACTIONS, "scams": "automatic"},
            {**DEFAULT_ACTIONS, "spam": "timeout"},
            {k: v for k, v in DEFAULT_ACTIONS.items() if k != "spam"},
        ):
            with self.assertRaises(InvalidRuleActions):
                encode_actions(bad)
        with self.assertRaises(InvalidRuleActions):
            preview_action(DEFAULT_ACTIONS, "made_up")

    def test_even_saved_ban_never_authorizes_execution(self):
        config = DEFAULT_ACTIONS.copy()
        config["threats"] = "ban"
        self.assertEqual(preview_action(config, "threats"), "ban")
        for kwargs in (
            dict(mode="observe", running=False, approved_rules=False, verified_incident=False, staff_exempt=False),
            dict(mode="enforce", running=True, approved_rules=True, verified_incident=True, staff_exempt=False),
        ):
            self.assertFalse(enforcement_permitted(**kwargs))


if __name__ == "__main__":
    unittest.main()
