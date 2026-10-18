"""H-03: máquina de estados durable, 100% aislada y sin publicación real."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock

import h03_release_handoff as h
from h03_publication_adapter import ReleasePlan

A, B, C = "a" * 40, "b" * 40, "c" * 40
ONE, TWO = "1" * 32, "2" * 32


@unittest.skipUnless(os.name == "posix", "Requires private POSIX state and flock")
class DurableHandoffTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "private"
        self.root.mkdir(mode=0o700)
        self.plan = ReleasePlan("lab", A, B, ONE)
        self.now = datetime.now(timezone.utc).replace(microsecond=0)
        self.source = A
        self.running = A
        self.approved = True
        self.backup = "verified_and_restored"
        self.deploy = Mock(return_value="deploy_123")
        self.confirmed = True
        self.authenticated = True

    def prepare(self, plan=None, at=None):
        return h.prepare_handoff(plan or self.plan, root=self.root,
                source_revision=lambda: self.source,
                target_approved=lambda p: self.approved,
                backup_verified=lambda p: self.backup, now=at or self.now)

    def dispatch(self, at=None):
        return h.dispatch_once(self.plan, root=self.root,
                source_revision=lambda: self.source,
                target_approved=lambda p: self.approved,
                publish_exact=self.deploy, now=at or self.now)

    def boot(self, at=None):
        return h.admit_boot(self.plan, root=self.root,
                running_revision=lambda: self.running,
                authenticate_backup=lambda p: self.authenticated,
                now=at or self.now)

    def finalize(self, at=None):
        return h.finalize_handoff(self.plan, root=self.root,
                running_revision=lambda: self.running,
                deployment_confirmed=lambda p, dep: self.confirmed,
                now=at or self.now)

    def test_complete_sequence_survives_persistent_restart(self):
        self.assertTrue(self.prepare())
        self.assertEqual(h.inspect_handoff(self.plan, root=self.root), "prepared")
        self.assertEqual(self.dispatch(), "deploy_123")
        self.running = B
        # Subproceso distinto: no hereda memoria ni referencias del controlador.
        program = ("from h03_publication_adapter import ReleasePlan\n"
                   "import h03_release_handoff as h\n"
                   "p=ReleasePlan('lab','" + A + "','" + B + "','" + ONE + "')\n"
                   "assert h.admit_boot(p,root='" + str(self.root) + "',"
                   "running_revision=lambda:'" + B + "',"
                   "authenticate_backup=lambda p:True)\n")
        child = subprocess.run([sys.executable, "-c", program],
                               cwd=Path(__file__).resolve().parents[1],
                               text=True, capture_output=True, timeout=10)
        self.assertEqual(child.returncode, 0, "Child failed to admit persisted handoff")
        self.assertEqual(h.inspect_handoff(self.plan, root=self.root), "boot_admitted")
        self.assertTrue(self.finalize())
        self.assertEqual(h.inspect_handoff(self.plan, root=self.root), "completed")
        # Reboot after success is allowed only with the same SHA and remote check.
        self.assertTrue(self.boot(at=self.now + timedelta(days=4)))
        self.assertTrue(self.finalize())
        self.deploy.assert_called_once()

    def test_dispatch_record_precedes_provider_call(self):
        self.prepare()
        self.deploy.side_effect = lambda p: (
            self.assertEqual(h.inspect_handoff(p, root=self.root), "dispatching")
            or "deploy_123")
        self.assertEqual(self.dispatch(), "deploy_123")
        self.assertEqual(self.deploy.call_count, 1)

    def test_ambiguous_provider_never_retries(self):
        self.prepare()
        self.deploy.side_effect = TimeoutError("sensitive_external_url")
        with self.assertRaisesRegex(h.HandoffBlocked, "ambiguous_deployment_requires_review") as caught:
            self.dispatch()
        self.assertNotIn("sensitive_external_url", str(caught.exception))
        self.assertEqual(h.inspect_handoff(self.plan, root=self.root), "needs_manual_review")
        with self.assertRaises(h.HandoffBlocked):
            self.dispatch()
        self.assertEqual(self.deploy.call_count, 1)

    def test_unconfirmed_provider_response_no_retry(self):
        self.prepare()
        self.deploy.return_value = ""
        with self.assertRaisesRegex(h.HandoffBlocked, "ambiguous_deployment_requires_review"):
            self.dispatch()
        with self.assertRaises(h.HandoffBlocked):
            self.dispatch()
        self.deploy.assert_called_once()

    def test_crash_before_provider_response_is_not_resent(self):
        self.prepare()
        with h._lock(self.root) as directory:
            info = h._plan(self.plan)
            record = h._active(directory, info)
            h._updated(directory, info, record, "dispatching", self.now)
        with self.assertRaisesRegex(h.HandoffBlocked, "dispatch_already_attempted"):
            self.dispatch()
        self.deploy.assert_not_called()

    def test_boot_can_arrive_before_dispatch_receipt(self):
        self.prepare()
        self.running = B
        def publication(plan):
            self.assertTrue(self.boot())
            return "deploy_123"
        self.deploy.side_effect = publication
        self.assertEqual(self.dispatch(), "deploy_123")
        self.assertEqual(h.inspect_handoff(self.plan, root=self.root), "boot_admitted")
        self.assertTrue(self.finalize())

    def test_cannot_boot_on_prepared_state(self):
        self.prepare()
        self.running = B
        with self.assertRaisesRegex(h.HandoffBlocked, "release_not_dispatched_or_blocked"):
            self.boot()

    def test_wrong_running_sha_blocks_before_backup(self):
        self.prepare()
        self.dispatch()
        with self.assertRaisesRegex(h.HandoffBlocked, "boot_revision_mismatch"):
            self.boot()
        self.assertEqual(h.inspect_handoff(self.plan, root=self.root), "submitted")

    def test_remote_backup_must_be_verified_in_new_process(self):
        self.prepare()
        self.dispatch()
        self.running = B
        self.authenticated = False
        with self.assertRaisesRegex(h.HandoffBlocked, "backup_not_authenticated"):
            self.boot()
        self.assertEqual(h.inspect_handoff(self.plan, root=self.root), "submitted")

    def test_boot_late_blocked_even_if_provider_dispatched(self):
        self.prepare()
        self.dispatch()
        self.running = B
        with self.assertRaisesRegex(h.HandoffBlocked, "release_window_expired"):
            self.boot(at=self.now + timedelta(minutes=16))

    def test_prepared_not_dispatched_after_timeout(self):
        self.prepare()
        with self.assertRaisesRegex(h.HandoffBlocked, "release_window_expired"):
            self.dispatch(at=self.now + timedelta(minutes=16))
        self.deploy.assert_not_called()

    def test_deployment_id_is_not_completed_status(self):
        self.prepare()
        self.dispatch()
        self.running = B
        self.boot()
        self.confirmed = False
        with self.assertRaisesRegex(h.HandoffBlocked, "deployment_not_final"):
            self.finalize()
        self.assertEqual(h.inspect_handoff(self.plan, root=self.root), "boot_admitted")
        self.confirmed = True
        self.assertTrue(self.finalize())

    def test_no_finalization_before_boot(self):
        self.prepare()
        self.dispatch()
        self.running = B
        with self.assertRaisesRegex(h.HandoffBlocked, "boot_not_admitted"):
            self.finalize()

    def test_no_finalization_when_running_sha_changes(self):
        self.prepare()
        self.dispatch()
        self.running = B
        self.boot()
        self.running = C
        with self.assertRaisesRegex(h.HandoffBlocked, "running_revision_mismatch"):
            self.finalize()

    def test_duplicate_request_never_reused(self):
        self.prepare()
        with self.assertRaisesRegex(h.HandoffBlocked, "previous_release_not_closed"):
            self.prepare()
        self.dispatch()
        self.running = B
        self.boot()
        self.finalize()
        self.source = B
        with self.assertRaisesRegex(h.HandoffBlocked, "request_id_reused"):
            self.prepare()

    def test_new_release_after_previous_completed(self):
        self.prepare()
        self.dispatch()
        self.running = B
        self.boot()
        self.finalize()
        self.source = B
        second = ReleasePlan("lab", B, C, TWO)
        self.assertTrue(self.prepare(second, self.now+timedelta(minutes=1)))
        self.assertEqual(h.inspect_handoff(second, root=self.root), "prepared")
        self.assertEqual(len(list(self.root.glob("h03-lab-release-*.json"))), 2)
        with self.assertRaisesRegex(h.HandoffBlocked, "another_release_is_active"):
            h.inspect_handoff(self.plan, root=self.root)

    def test_next_release_wrong_source_blocked(self):
        self.prepare()
        self.dispatch()
        self.running = B
        self.boot()
        self.finalize()
        self.source = A
        with self.assertRaisesRegex(h.HandoffBlocked, "release_history_diverged"):
            self.prepare(ReleasePlan("lab", A, C, TWO))

    def test_prepare_never_records_unverified_backup(self):
        self.backup = "uploaded_unverified"
        with self.assertRaisesRegex(h.HandoffBlocked, "backup_not_verified"):
            self.prepare()
        self.assertEqual(list(self.root.glob("*.json")), [])

    def test_missing_approval_and_changed_source_block_before_record(self):
        self.approved = False
        with self.assertRaisesRegex(h.HandoffBlocked, "source_or_approval_changed"):
            self.prepare()
        self.approved = True
        self.source = C
        with self.assertRaisesRegex(h.HandoffBlocked, "source_or_approval_changed"):
            self.prepare()
        self.assertEqual(list(self.root.glob("*.json")), [])

    def test_refuses_lab_plan_inside_real_production_identity(self):
        from unittest.mock import patch
        with patch.dict(os.environ, {"RAILWAY_PROJECT_ID":h.PRODUCTION_PROJECT_ID}):
            with self.assertRaisesRegex(h.HandoffBlocked, "production_forbidden"):
                self.prepare()

    def test_wrong_environment_and_request_rejected(self):
        for bad in (ReleasePlan("heraldo-production", A, B, ONE),
                    ReleasePlan("lab", A, B, "../../evil"),
                    ReleasePlan("lab", A, A, TWO)):
            with self.subTest(plan=bad), self.assertRaises(h.HandoffBlocked):
                self.prepare(bad)

    def test_rejects_public_directory_and_symlink(self):
        self.root.chmod(0o755)
        with self.assertRaisesRegex(h.HandoffBlocked, "untrusted_state_directory"):
            self.prepare()
        self.root.chmod(0o700)
        fake = Path(self.temp.name) / "link"
        fake.symlink_to(self.root, target_is_directory=True)
        with self.assertRaisesRegex(h.HandoffBlocked, "untrusted_state_directory"):
            h.prepare_handoff(self.plan, root=fake,
                source_revision=lambda:A, target_approved=lambda p:True,
                backup_verified=lambda p:"verified_and_restored")

    def test_corrupted_state_is_fail_closed(self):
        self.prepare()
        path = self.root / ("h03-lab-release-"+ONE+".json")
        path.write_text("{")
        with self.assertRaisesRegex(h.HandoffBlocked, "corrupt_private_record"):
            self.dispatch()

    def test_concurrent_lock_blocks_a_second_dispatch(self):
        self.prepare()
        with h._lock(self.root):
            with self.assertRaisesRegex(h.HandoffBlocked, "release_already_locked"):
                self.dispatch()
        self.deploy.assert_not_called()

    def test_unindexed_orphan_never_auto_accepted(self):
        (self.root / ("h03-lab-release-"+ONE+".json")).write_text("{}")
        with self.assertRaisesRegex(h.HandoffBlocked, "unreconciled_orphan_release"):
            self.prepare()


    def test_corrupted_active_pointer_is_rejected(self):
        self.prepare()
        self.dispatch()
        self.running = B
        self.boot()
        self.finalize()
        self.source = B
        index = self.root / "h03-lab-active.json"
        index.write_text('{"version":1,"request_id":"../../escape"}')
        index.chmod(0o600)
        with self.assertRaisesRegex(h.HandoffBlocked, "corrupt_active_pointer"):
            self.prepare(ReleasePlan("lab", B, C, TWO))

    def test_orphan_after_pointer_is_fail_closed(self):
        self.prepare()
        self.dispatch()
        self.running = B
        self.boot()
        self.finalize()
        self.source = B
        orphan = self.root / ("h03-lab-release-" + TWO + ".json")
        orphan.write_text('{"phase":"prepared"}')
        orphan.chmod(0o600)
        with self.assertRaisesRegex(h.HandoffBlocked, "unreconciled_orphan_release"):
            self.prepare(ReleasePlan("lab", B, C, "3" * 32))

    def test_failure_never_restores_live_sqlite(self):
        self.prepare()
        self.dispatch()
        # La función no tiene acceso a SQLite ni contiene restauración implícita.
        self.running = B
        self.boot()
        self.confirmed = False
        with self.assertRaises(h.HandoffBlocked):
            self.finalize()
        self.assertTrue((self.root / ("h03-lab-release-"+ONE+".json")).is_file())


if __name__ == "__main__":
    unittest.main()
