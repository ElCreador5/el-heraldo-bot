"""Regresión: no presentar plantillas como normas oficiales."""
import unittest
from custodio_core import RulesSnapshot
from custodio_server_rule_actions_setup import decode, encode, CustodioServerRuleActionsView


class RealServerActionsTests(unittest.TestCase):
    def test_only_actual_rules_are_options(self):
        snapshot = RulesSnapshot(100, ("Saludar con respeto", "No compartir invitaciones"), "rev123")
        values = {}
        parent = type("Parent", (), {
            "guild_id": 100,
            "get_setting": lambda self, gid, key: values.get((gid, key)),
        })()
        view = CustodioServerRuleActionsView(parent, snapshot)
        self.assertEqual(len(view.rules_select.options), 2)
        self.assertIn("Saludar con respeto", view.rules_select.options[0].label)
        self.assertNotIn("Fraude y suplantación", str(view.rules_select.options))
        self.assertIn("Saludar con respeto", view.summary())

    def test_change_of_official_rules_invalidates_prior_draft(self):
        current = RulesSnapshot(100, ("No publicar enlaces",), "revisionA")
        changed = RulesSnapshot(100, ("No insultar",), "revisionB")
        payload = encode(current, ["warn"])
        self.assertEqual(decode(payload, current), ["warn"])
        self.assertEqual(decode(payload, changed), ["report"])
        self.assertIn('"enforcement_enabled":false', payload)

if __name__ == "__main__":
    unittest.main()
