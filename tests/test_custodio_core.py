"""Contratos de seguridad sin Discord real ni proveedor externo de IA."""
import unittest

from custodio_core import RulesUnavailable, read_snapshot, plan_review


def make_snapshot(guild_id=123, rules=None, enabled=True, response_status=200):
    if rules is None:
        rules = ["Respeto entre miembros.", "Evitar mensajes repetitivos."]
    return read_snapshot(
        guild_id,
        200,
        {"features": ["MEMBER_VERIFICATION_GATE_ENABLED"] if enabled else []},
        response_status,
        {"form_fields": [
            {"field_type": "TEXT_INPUT", "values": ["No es una regla"]},
            {"field_type": "TERMS", "values": rules},
        ]},
    )


class RulesSnapshotTests(unittest.TestCase):
    def test_extracts_only_official_terms_and_metadata_is_private(self):
        snapshot = make_snapshot()
        self.assertEqual(snapshot.count, 2)
        self.assertEqual(snapshot.rules, ("Respeto entre miembros.", "Evitar mensajes repetitivos."))
        self.assertNotIn("Respeto", str(snapshot.metadata()))
        self.assertEqual(len(snapshot.revision), 64)

    def test_reordered_or_changed_rules_invalidate_approval(self):
        original = make_snapshot()
        changed = make_snapshot(rules=["Evitar mensajes repetitivos.", "Respeto entre miembros."])
        self.assertNotEqual(original.revision, changed.revision)
        self.assertEqual(plan_review(changed, original.revision, 456, "first", {"outcome": "clear"}).state, "paused")

    def test_each_guild_is_scoped_and_invalid_guild_is_rejected(self):
        self.assertEqual(make_snapshot(guild_id=456).guild_id, 456)
        with self.assertRaises(ValueError):
            make_snapshot(guild_id=0)

    def test_screening_is_mandatory(self):
        with self.assertRaises(RulesUnavailable) as caught:
            make_snapshot(enabled=False)
        self.assertEqual(caught.exception.reason, "screening_disabled")

    def test_undocumented_endpoint_failure_is_not_a_blank_policy(self):
        with self.assertRaises(RulesUnavailable) as caught:
            make_snapshot(response_status=403)
        self.assertEqual(caught.exception.reason, "verification_unavailable")
        self.assertEqual(caught.exception.http_status, 403)

    def test_invalid_api_payload_is_rejected(self):
        with self.assertRaises(RulesUnavailable):
            read_snapshot(1, 200, {"features": ["MEMBER_VERIFICATION_GATE_ENABLED"]}, 200, {"form_fields": None})

    def test_empty_and_oversized_policy_is_rejected(self):
        for rules in ([], [""], ["x" * 2049], ["test"] * 17):
            with self.subTest(rules_len=len(rules)), self.assertRaises(RulesUnavailable):
                make_snapshot(rules=rules)


class ReviewPlanTests(unittest.TestCase):
    def setUp(self):
        self.rules = make_snapshot()

    def test_no_approval_never_enables_supervision(self):
        plan = plan_review(self.rules, None, 456, "v1", {"outcome": "suspected", "rule_numbers": [1]})
        self.assertEqual(plan.state, "paused")
        self.assertEqual(plan.action, "none")

    def test_clear_is_ignored(self):
        plan = plan_review(self.rules, self.rules.revision, 456, "v1", {"outcome": "clear", "rule_numbers": []})
        self.assertEqual(plan.state, "ignore")
        self.assertEqual(plan.action, "none")

    def test_suspicious_case_uses_single_incident_for_multiple_rules(self):
        result = {"outcome": "suspected", "rule_numbers": [2, 1, 2], "severity": "high", "summary": "Contexto por revisar."}
        plan = plan_review(self.rules, self.rules.revision, 456, "v1", result, mode="assist")
        self.assertEqual(plan.state, "review")
        self.assertEqual(plan.rule_numbers, (1, 2))
        self.assertEqual(plan.action, "notify_staff")
        self.assertEqual(plan.dedupe_key, plan_review(self.rules, self.rules.revision, 456, "v1", result, mode="assist").dedupe_key)

    def test_observe_does_not_warn_member_or_sanction(self):
        plan = plan_review(self.rules, self.rules.revision, 456, "v1", {"outcome": "ambiguous", "rule_numbers": [1]})
        self.assertEqual(plan.state, "observe")
        self.assertEqual(plan.action, "record_only")

    def test_modified_message_gets_distinct_idempotency_key(self):
        result = {"outcome": "suspected", "rule_numbers": [1]}
        old = plan_review(self.rules, self.rules.revision, 456, "v1", result)
        new = plan_review(self.rules, self.rules.revision, 456, "v2", result)
        self.assertNotEqual(old.dedupe_key, new.dedupe_key)

    def test_invalid_classifier_result_must_be_reviewed_not_enforced(self):
        bad_results = [
            None,
            {"outcome": "suspected", "rule_numbers": [99]},
            {"outcome": "clear", "rule_numbers": [1]},
            {"outcome": "suspected", "rule_numbers": []},
            {"outcome": ["untrusted"], "rule_numbers": [1]},
            {"outcome": "suspected", "rule_numbers": ["1"]},
        ]
        for result in bad_results:
            with self.subTest(result=result):
                plan = plan_review(self.rules, self.rules.revision, 456, "v1", result, mode="assist")
                self.assertEqual(plan.state, "review")
                self.assertEqual(plan.action, "notify_staff")

    def test_invalid_mode_and_message_identity_are_rejected(self):
        with self.assertRaises(ValueError):
            plan_review(self.rules, self.rules.revision, 456, "v1", {}, mode="automatic")
        with self.assertRaises(ValueError):
            plan_review(self.rules, self.rules.revision, -1, "v1", {})


if __name__ == "__main__":
    unittest.main()
