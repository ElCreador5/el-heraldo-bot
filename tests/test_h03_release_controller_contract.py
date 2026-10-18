"""Pruebas offline del contrato H-03; sin Railway, Discord ni secretos."""
import unittest
from unittest.mock import Mock

from tools.h03_release_controller_contract import (
    ReleaseContractBlocked, ReleasePlan, run_lab_contract,
)

OLD = "a" * 40
NEW = "b" * 40


class ReleaseControllerContractTests(unittest.TestCase):
    def setUp(self):
        self.live = OLD
        self.plan = ReleasePlan("lab", OLD, NEW, "1" * 32)
        self.prepare = Mock(return_value="verified_and_restored")
        self.publisher = Mock(side_effect=self.confirm)
        self.guard = Mock(side_effect=lambda plan, apply: apply())

    def confirm(self, plan):
        self.live = plan.target_revision
        return True

    def current(self):
        return self.live

    def perform(self, **overrides):
        params = dict(
            read_live_revision=self.current,
            prepare_and_restore=self.prepare,
            guarded_update=self.guard,
            publish_and_confirm=self.publisher,
        )
        params.update(overrides)
        return run_lab_contract(self.plan, **params)

    def test_happy_path_requires_confirmed_final_revision(self):
        self.assertIs(self.perform(), True)
        self.prepare.assert_called_once_with(self.plan)
        self.publisher.assert_called_once_with(self.plan)
        self.guard.assert_called_once()

    def test_production_is_never_authorized(self):
        self.plan = ReleasePlan("heraldo-production", OLD, NEW, "1" * 32)
        with self.assertRaisesRegex(ReleaseContractBlocked, "laboratory_only"):
            self.perform()
        self.prepare.assert_not_called()
        self.publisher.assert_not_called()

    def test_invalid_sha_and_id_fail_before_any_adapter(self):
        for plan in (
            ReleasePlan("lab", "short", NEW, "1" * 32),
            ReleasePlan("lab", OLD, "UPPER" * 8, "1" * 32),
            ReleasePlan("lab", OLD, NEW, "../illegal"),
            ReleasePlan("lab", OLD, OLD, "1" * 32),
        ):
            with self.subTest(plan=plan), self.assertRaises(ReleaseContractBlocked):
                self.plan = plan
                self.perform()
        self.prepare.assert_not_called()
        self.publisher.assert_not_called()

    def test_source_must_match_before_backup(self):
        self.live = "c" * 40
        with self.assertRaisesRegex(ReleaseContractBlocked, "source_revision_changed"):
            self.perform()
        self.prepare.assert_not_called()
        self.publisher.assert_not_called()

    def test_missing_adapter_fails_closed(self):
        with self.assertRaisesRegex(ReleaseContractBlocked, "missing_trusted_adapter"):
            self.perform(guarded_update=None)
        self.prepare.assert_not_called()
        self.publisher.assert_not_called()

    def test_nonverified_backup_prevents_publication(self):
        self.prepare.return_value = "uploaded_unverified"
        with self.assertRaisesRegex(ReleaseContractBlocked, "backup_not_verified"):
            self.perform()
        self.guard.assert_not_called()
        self.publisher.assert_not_called()

    def test_source_change_during_backup_blocks_guard(self):
        def change(_plan):
            self.live = "c" * 40
            return "verified_and_restored"
        self.prepare.side_effect = change
        with self.assertRaisesRegex(ReleaseContractBlocked, "source_revision_changed"):
            self.perform()
        self.guard.assert_not_called()

    def test_guard_cannot_claim_success_without_running_callback(self):
        self.guard.side_effect = lambda plan, apply: True
        with self.assertRaisesRegex(ReleaseContractBlocked, "guarded_update_unconfirmed"):
            self.perform()
        self.publisher.assert_not_called()

    def test_false_guard_result_blocks_success(self):
        self.guard.side_effect = lambda plan, apply: False
        with self.assertRaisesRegex(ReleaseContractBlocked, "guarded_update_unconfirmed"):
            self.perform()
        self.publisher.assert_not_called()

    def test_async_queue_ack_without_deployment_is_not_confirmation(self):
        self.publisher.side_effect = None
        self.publisher.return_value = True
        with self.assertRaisesRegex(ReleaseContractBlocked, "target_revision_unconfirmed"):
            self.perform()

    def test_publisher_must_return_exactly_true(self):
        self.publisher.side_effect = None
        self.publisher.return_value = 1
        with self.assertRaisesRegex(ReleaseContractBlocked, "deployment_unconfirmed"):
            self.perform()

    def test_guarded_callback_cannot_be_replayed(self):
        def twice(plan, apply):
            apply()
            return apply()
        self.guard.side_effect = twice
        with self.assertRaisesRegex(ReleaseContractBlocked, "callback_reused"):
            self.perform()
        self.publisher.assert_called_once()

    def test_source_change_while_waiting_for_guard_blocks_deployment(self):
        def mutate(plan, apply):
            self.live = "c" * 40
            return apply()
        self.guard.side_effect = mutate
        with self.assertRaisesRegex(ReleaseContractBlocked, "source_revision_changed"):
            self.perform()
        self.publisher.assert_not_called()

    def test_final_revision_must_remain_target_after_guard_returns(self):
        def lose_target(plan, apply):
            result = apply()
            self.live = "c" * 40
            return result
        self.guard.side_effect = lose_target
        with self.assertRaisesRegex(ReleaseContractBlocked, "target_revision_changed"):
            self.perform()

    def test_new_plan_ids_are_unique_and_lab_only(self):
        a, b = ReleasePlan.for_lab(OLD, NEW), ReleasePlan.for_lab(OLD, NEW)
        self.assertEqual((a.environment, b.environment), ("lab", "lab"))
        self.assertNotEqual(a.request_id, b.request_id)
        self.assertEqual(len(a.request_id), 32)


if __name__ == "__main__":
    unittest.main()
