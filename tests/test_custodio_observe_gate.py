"""Autorización obligatoria antes de evaluar observaciones."""
import unittest
from custodio_core import RulesSnapshot
from custodio_observe import ObserveBuffer
from custodio_observe_gate import ObserveAuthorization, evaluate_observation

class GateTests(unittest.TestCase):
    def setUp(self):
        self.rules = RulesSnapshot(22, ("No repetir mensajes",), "revA")
        self.buffer = ObserveBuffer()
        self.values = dict(rule_number=1, channel_id=3, actor_id=4,
                           timestamp=1, message_id=5, content="Mensaje reiterado")

    def test_disabled_and_unapproved_cannot_evaluate(self):
        self.assertIsNone(evaluate_observation(self.buffer, self.rules, None, **self.values))
        auth = ObserveAuthorization(22, "revA", frozenset({1}))
        self.assertIsNone(evaluate_observation(self.buffer, self.rules, auth, **self.values))
        self.assertEqual(len(self.buffer._events), 0)

    def test_rule_revision_and_exemption_fail_closed(self):
        for auth in (
            ObserveAuthorization(23, "revA", frozenset({1}), True),
            ObserveAuthorization(22, "revB", frozenset({1}), True),
            ObserveAuthorization(22, "revA", frozenset(), True),
        ):
            self.assertIsNone(evaluate_observation(self.buffer, self.rules, auth, **self.values))
        approved = ObserveAuthorization(22, "revA", frozenset({1}), True)
        self.assertIsNone(evaluate_observation(self.buffer, self.rules, approved, exempt=True, **self.values))
        self.assertEqual(len(self.buffer._events), 0)

    def test_authorized_observation_is_report_only(self):
        auth = ObserveAuthorization(22, "revA", frozenset({1}), True)
        for n in (5, 6):
            self.assertIsNone(evaluate_observation(self.buffer, self.rules, auth,
                **{**self.values, "message_id": n}))
        found = evaluate_observation(self.buffer, self.rules, auth,
            **{**self.values, "message_id": 7})
        self.assertEqual(found.action, "report_only")
        self.assertEqual(found.rule_number, 1)

if __name__ == "__main__":
    unittest.main()
