"""Pruebas aisladas de H-03: sin red, Discord ni SQLite de producción."""
from i18n_source_helpers import source_text as _source_text
import json
import os
import sys
from pathlib import Path
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import Mock, patch

import h03_publication_adapter as pub
import h03_startup_gate as gate

A, B, C = "a" * 40, "b" * 40, "c" * 40
REQUEST = "1" * 32


class PublicationContractTests(unittest.TestCase):
    def setUp(self):
        self.plan = pub.ReleasePlan("lab", A, B, REQUEST)
        self.source = A
        self.running = A
        self.approved = True
        self.backup = "verified_and_restored"
        self.deployment = "deploy_1"
        self.completed = True
        self.published = []
        self.guard_calls = 0

    def publish(self, plan):
        self.published.append(plan.target_revision)
        self.running = B
        return self.deployment

    def guarded(self, plan, fn):
        self.guard_calls += 1
        return fn()

    def execute(self, **kwargs):
        values = dict(
            read_source_revision=lambda: self.source,
            target_approved=lambda p: self.approved,
            prepare_and_restore=lambda p: self.backup,
            guarded_update=self.guarded,
            publish_exact=self.publish,
            confirm_final_deployment=lambda p, deployment: self.completed,
            read_running_revision=lambda: self.running)
        values.update(kwargs)
        return pub.run_lab_release(self.plan, **values)

    def test_success_only_after_final_revision(self):
        self.assertTrue(self.execute())
        self.assertEqual(self.published, [B])
        self.assertEqual(self.guard_calls, 1)

    def test_production_invalid_revision_and_request_block(self):
        for plan in (
            pub.ReleasePlan("heraldo-production", A, B, REQUEST),
            pub.ReleasePlan("lab", A, A, REQUEST),
            pub.ReleasePlan("lab", A, "wrong", REQUEST),
            pub.ReleasePlan("lab", A, B, "../../escape"),
        ):
            with self.subTest(plan=plan), self.assertRaises(pub.ReleaseBlocked):
                self.plan = plan
                self.execute()
        self.assertEqual(self.published, [])

    def test_target_not_approved_blocks(self):
        self.approved = False
        with self.assertRaisesRegex(pub.ReleaseBlocked, "target_not_approved"):
            self.execute()
        self.assertEqual(self.guard_calls, 0)

    def test_backup_not_restored_blocks(self):
        self.backup = "uploaded_unverified"
        with self.assertRaisesRegex(pub.ReleaseBlocked, "backup_not_verified"):
            self.execute()
        self.assertEqual(self.published, [])

    def test_source_changed_blocks(self):
        self.source = C
        with self.assertRaisesRegex(pub.ReleaseBlocked, "source_revision_changed"):
            self.execute()
        self.assertEqual(self.published, [])

    def test_missing_backend_blocks(self):
        with self.assertRaisesRegex(pub.ReleaseBlocked, "missing_trusted_adapter"):
            self.execute(publish_exact=None)

    def test_deployment_id_is_not_proof(self):
        self.completed = False
        with self.assertRaisesRegex(pub.ReleaseBlocked, "deployment_unconfirmed"):
            self.execute()

    def test_wrong_running_sha_blocks_after_publication(self):
        with self.assertRaisesRegex(pub.ReleaseBlocked, "running_revision_mismatch"):
            self.execute(publish_exact=lambda p: "deploy_1")

    def test_ambiguous_response_blocks(self):
        self.deployment = ""
        with self.assertRaisesRegex(pub.ReleaseBlocked, "deployment_unconfirmed"):
            self.execute()

    def test_guard_callback_once_mandatory(self):
        with self.assertRaisesRegex(pub.ReleaseBlocked, "guarded_update_unconfirmed"):
            self.execute(guarded_update=lambda p, fn: True)
        with self.assertRaisesRegex(pub.ReleaseBlocked, "callback_reused"):
            self.execute(guarded_update=lambda p, fn: (fn(), fn()))

    def test_provider_exception_has_no_automatic_retry(self):
        fn = Mock(side_effect=RuntimeError("provider_failure"))
        with self.assertRaises(RuntimeError):
            self.execute(publish_exact=fn)
        fn.assert_called_once()


@unittest.skipUnless(os.name == "posix", "Private receipts rely on POSIX ACLs")
class StartupGateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "private"
        self.root.mkdir(mode=0o700)
        self.now = datetime.now(timezone.utc)
        self.op = {"purpose": "preupdate", "request_id": REQUEST,
                   "source_revision": A, "target_revision": B}
        self.grant = {"version": 1, "operation": self.op, "status": "update_started"}
        self.receipt = {"version": 2, "environment": "heraldo-production",
                        "status": "verified_and_restored", "operation": self.op,
                        "started_at": (self.now-timedelta(minutes=3)).isoformat(),
                        "finished_at": (self.now-timedelta(minutes=2)).isoformat()}
        self.grant_path = self.root / f"heraldo-production-preupdate-{REQUEST}.authorization.json"
        self.receipt_path = self.root / f"heraldo-production-preupdate-{REQUEST}.json"
        self.write()

    def write(self):
        for path, data in ((self.grant_path, self.grant), (self.receipt_path, self.receipt)):
            path.write_text(json.dumps(data))
            path.chmod(0o600)

    def verify(self, auth=lambda receipt, op: True):
        return gate.validate_startup_receipts(
            request_id=REQUEST, target_revision=B, root=self.root,
            authenticate_remote=auth, now=self.now)

    def test_good_receipt_with_authenticated_remote(self):
        self.assertTrue(self.verify())

    def test_missing_authorization_and_wrong_target_block(self):
        self.grant_path.unlink()
        with self.assertRaises(gate.StartupBlocked):
            self.verify()
        self.write()
        with self.assertRaisesRegex(gate.StartupBlocked, "invalid_grant_binding"):
            gate.validate_startup_receipts(request_id=REQUEST, target_revision=C,
                root=self.root, authenticate_remote=lambda r,o: True, now=self.now)

    def test_path_traversal_request_rejected(self):
        with self.assertRaisesRegex(gate.StartupBlocked, "invalid_startup_identity"):
            gate.validate_startup_receipts(request_id="../../etc", target_revision=B,
                root=self.root, authenticate_remote=lambda r,o: True, now=self.now)

    def test_invalid_binding_and_no_verified_backup_block(self):
        self.receipt["operation"] = dict(self.op, source_revision=C)
        self.write()
        with self.assertRaisesRegex(gate.StartupBlocked, "invalid_backup_binding"):
            self.verify()
        self.receipt["operation"] = self.op
        self.receipt["status"] = "uploaded_unverified"
        self.write()
        with self.assertRaisesRegex(gate.StartupBlocked, "invalid_backup_binding"):
            self.verify()

    def test_remote_crypto_must_be_successful(self):
        with self.assertRaisesRegex(gate.StartupBlocked, "remote_backup_not_authenticated"):
            self.verify(lambda r,o: False)

    def test_provider_error_redacts_private_details(self):
        def broken(r,o):
            raise RuntimeError("provider-secret-url")
        with self.assertRaisesRegex(gate.StartupBlocked, "remote_backup_not_authenticated") as err:
            self.verify(broken)
        self.assertNotIn("provider-secret-url", str(err.exception))

    def test_expired_pending_release_blocked(self):
        self.receipt["started_at"] = (self.now-timedelta(minutes=20)).isoformat()
        self.receipt["finished_at"] = (self.now-timedelta(minutes=19)).isoformat()
        self.write()
        with self.assertRaisesRegex(gate.StartupBlocked, "stale_pending_release"):
            self.verify()

    def test_completed_release_can_restart_later(self):
        self.grant["status"] = "update_completed"
        self.receipt["started_at"] = (self.now-timedelta(days=2)).isoformat()
        self.receipt["finished_at"] = (self.now-timedelta(days=2, minutes=-1)).isoformat()
        self.write()
        self.assertTrue(self.verify())

    def test_file_permissions_and_symlink_rejected(self):
        self.grant_path.chmod(0o644)
        with self.assertRaisesRegex(gate.StartupBlocked, "authorization_not_private"):
            self.verify()
        self.grant_path.unlink()
        self.grant_path.symlink_to(self.receipt_path)
        with self.assertRaises(gate.StartupBlocked):
            self.verify()

    def test_untrusted_state_directory_rejected(self):
        self.root.chmod(0o755)
        with self.assertRaisesRegex(gate.StartupBlocked, "untrusted_volume_permissions"):
            self.verify()

    def test_invalid_json_rejected(self):
        self.grant_path.write_text("invalid")
        self.grant_path.chmod(0o600)
        with self.assertRaisesRegex(gate.StartupBlocked, "invalid_authorization"):
            self.verify()

    def test_opt_in_only_and_identity(self):
        self.assertFalse(gate.enforce_startup({}))
        with self.assertRaisesRegex(gate.StartupBlocked, "invalid_activation_flag"):
            gate.enforce_startup({gate.FLAG:"yes"})
        with self.assertRaisesRegex(gate.StartupBlocked, "production_identity_mismatch"):
            gate.enforce_startup({gate.FLAG:gate.FLAG_VALUE})

    def test_enabled_runtime_checks_exact_revision(self):
        env = dict(zip(("RAILWAY_PROJECT_ID", "RAILWAY_ENVIRONMENT_ID",
                        "RAILWAY_SERVICE_ID"), gate.PRODUCTION_IDS))
        env.update({gate.FLAG:gate.FLAG_VALUE, gate.REQUEST_VAR:REQUEST,
                    "RAILWAY_GIT_COMMIT_SHA":B, "DB_PATH":"/data/heraldo.db"})
        called = []
        fake = SimpleNamespace(_guard=lambda environment, db, root:
                               called.append((environment, str(db))))
        with patch.dict(sys.modules, {"backup_job":fake}):
            self.assertTrue(gate.enforce_startup(env, root=self.root,
                                                 authenticator=lambda r,o: True))
            env["RAILWAY_GIT_COMMIT_SHA"] = C
            with self.assertRaises(gate.StartupBlocked):
                gate.enforce_startup(env, root=self.root,
                                     authenticator=lambda r,o: True)
        self.assertEqual(called[0], ("heraldo-production", "/data/heraldo.db"))


class BootWiringTests(unittest.TestCase):
    def test_main_process_runs_gate_before_creating_bot(self):
        code = _source_text(Path(__file__).resolve().parent.parent / 'bot.py', encoding='utf-8')
        self.assertLess(code.index("_h03_enforce_startup()"), code.index("bot = commands.Bot("))
        self.assertIn('if __name__ == "__main__":\n    from h03_startup_gate', code)


if __name__ == "__main__":
    unittest.main()
