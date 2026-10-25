"""Puente Railway Test a respaldo H-03 y diario: SIN red ni SQLite viva."""
from i18n_source_helpers import source_text as _source_text
from contextlib import nullcontext
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from h03_publication_adapter import ReleasePlan
import h03_test_railway_release as bridge

SRC = "a" * 40
DST = "b" * 40
REQ = "1" * 32


class RailwayIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.db = Path(self.tmp.name) / "test.sqlite"
        self.db.write_bytes(b"synthetic")
        self.root = Path(self.tmp.name) / "backup"
        self.root.mkdir(mode=0o700)
        self.plan = ReleasePlan("lab", SRC, DST, REQ)

    def test_boot_guard_is_disabled_by_default(self):
        with patch.object(bridge, "admit_test_boot") as called:
            self.assertFalse(bridge.enforce_test_boot({}))
            called.assert_not_called()

    def test_boot_guard_requires_explicit_test_identity(self):
        with self.assertRaisesRegex(bridge.TestReleaseBlocked, "invalid_test_startup_flag"):
            bridge.enforce_test_boot({bridge.STARTUP_FLAG: "enabled"})
        with self.assertRaisesRegex(bridge.TestReleaseBlocked, "test_identity_required"):
            bridge.enforce_test_boot({bridge.STARTUP_FLAG: bridge.STARTUP_VALUE})

    def test_boot_opt_in_runs_admission(self):
        identity = dict(zip(("RAILWAY_PROJECT_ID","RAILWAY_ENVIRONMENT_ID",
                             "RAILWAY_SERVICE_ID"), bridge.TEST_IDS))
        identity[bridge.STARTUP_FLAG] = bridge.STARTUP_VALUE
        with patch.object(bridge, "check_test_environment", return_value=self.db), \
             patch.object(bridge, "admit_test_boot", return_value=True) as called:
            self.assertTrue(bridge.enforce_test_boot(identity))
            called.assert_called_once()

    def test_production_path_rejected_without_backup_or_provider(self):
        with patch.dict(os.environ, {"RAILWAY_PROJECT_ID":bridge.TEST_IDS[0],
                                      "RAILWAY_ENVIRONMENT_ID":"WRONG",
                                      "RAILWAY_SERVICE_ID":bridge.TEST_IDS[2]}):
            with self.assertRaisesRegex(bridge.TestReleaseBlocked, "test_identity_required"):
                bridge.prepare_release(self.plan)

    def test_backup_prepare_is_tied_to_both_commits_and_unique_request(self):
        with patch.object(bridge, "check_test_environment", return_value=self.db), \
             patch.object(bridge, "state_root", return_value=self.root), \
             patch.object(bridge, "run_once", return_value="verified_and_restored") as backup, \
             patch.object(bridge, "verify_preupdate", return_value="verified_and_restored") as verified, \
             patch.object(bridge, "prepare_handoff") as handoff, \
             patch.dict(os.environ, {"RAILWAY_GIT_COMMIT_SHA":SRC, bridge.APPROVED_TARGET:DST}):
            def perform(plan, **kwargs):
                self.assertEqual(kwargs["backup_verified"](plan), "verified_and_restored")
                return True
            handoff.side_effect=perform
            self.assertTrue(bridge.prepare_release(self.plan))
            backup.assert_called_once_with(
                self.db, bridge.TEST_STATE_DIR, environment="heraldo-test",
                revision=SRC, purpose="preupdate", request_id=REQ,
                target_revision=DST)
            self.assertEqual(verified.call_args.kwargs["target_revision"], DST)

    def test_unapproved_target_cannot_prepare(self):
        with patch.object(bridge, "check_test_environment", return_value=self.db), \
             patch.dict(os.environ, {"RAILWAY_GIT_COMMIT_SHA":SRC,
                                     bridge.APPROVED_TARGET:"c"*40}), \
             patch.object(bridge, "run_once") as backup:
            with self.assertRaisesRegex(bridge.TestReleaseBlocked, "test_revision_not_approved"):
                bridge.prepare_release(self.plan)
            backup.assert_not_called()

    def test_dispatch_calls_real_railway_provider_only_through_durable_gate(self):
        provider = Mock(unsafe=True)
        provider.assert_source.return_value = True
        provider.deploy_exact.return_value = "deploy_1"
        with patch.object(bridge, "check_test_environment", return_value=self.db), \
             patch.object(bridge, "state_root", return_value=self.root), \
             patch.object(bridge, "dispatch_once") as durable, \
             patch.dict(os.environ, {"RAILWAY_GIT_COMMIT_SHA":SRC,
                                     bridge.APPROVED_TARGET:DST}):
            def run(plan, **kwargs):
                self.assertEqual(kwargs["source_revision"](), SRC)
                self.assertTrue(kwargs["target_approved"](plan))
                return kwargs["publish_exact"](plan)
            durable.side_effect=run
            self.assertEqual(bridge.dispatch_release(self.plan, client=provider), "deploy_1")
            provider.deploy_exact.assert_called_once_with(DST)
            self.assertEqual(durable.call_count, 1)

    def test_changed_source_blocks_before_dispatch(self):
        with patch.object(bridge, "check_test_environment", return_value=self.db), \
             patch.dict(os.environ, {"RAILWAY_GIT_COMMIT_SHA":"c"*40}), \
             patch.object(bridge, "dispatch_once") as durable:
            with self.assertRaisesRegex(bridge.TestReleaseBlocked, "test_revision_changed"):
                bridge.dispatch_release(self.plan, client=Mock())
            durable.assert_not_called()

    def test_finalization_requires_provider_status_and_target_sha(self):
        provider=Mock()
        provider.deployment_final.return_value=True
        with patch.object(bridge, "check_test_environment", return_value=self.db), \
             patch.object(bridge, "load_active_plan", return_value=self.plan), \
             patch.object(bridge, "state_root", return_value=self.root), \
             patch.object(bridge, "finalize_handoff") as durable, \
             patch.dict(os.environ, {"RAILWAY_GIT_COMMIT_SHA":DST}):
            def run(plan, **kwargs):
                self.assertEqual(kwargs["running_revision"](), DST)
                self.assertTrue(kwargs["deployment_confirmed"](plan,"deploy_1"))
                return True
            durable.side_effect=run
            self.assertTrue(bridge.finalize_release(client=provider))
            provider.deployment_final.assert_called_once_with("deploy_1",DST)

    def test_cli_reports_submission_not_success(self):
        import io
        from contextlib import redirect_stdout
        output = io.StringIO()
        with patch.object(bridge, "make_plan", return_value=self.plan), \
             patch.object(bridge, "dispatch_release", return_value="deploy_123"), \
             redirect_stdout(output):
            result = bridge.main([
                "dispatch", "--request-id", REQ,
                "--source-revision", SRC,
                "--target-revision", DST])
        self.assertEqual(result, 0)
        self.assertIn("status=DEPLOYMENT_SUBMITTED", output.getvalue())
        self.assertNotIn("DEPLOYMENT_VERIFIED", output.getvalue())

    def test_finalization_never_uses_old_process(self):
        with patch.object(bridge, "check_test_environment", return_value=self.db), \
             patch.object(bridge, "load_active_plan", return_value=self.plan), \
             patch.dict(os.environ, {"RAILWAY_GIT_COMMIT_SHA":SRC}):
            with self.assertRaisesRegex(bridge.TestReleaseBlocked, "target_process_not_running"):
                bridge.finalize_release(client=Mock())

    def test_test_remote_backup_must_match_request_source_target_and_digest(self):
        operation={"purpose":"preupdate","request_id":REQ,
                   "source_revision":SRC,"target_revision":DST}
        receipt={"version":2,"environment":"heraldo-test","operation":operation,
                 "object":"heraldo-test/20261018/abc.h03e",
                 "sqlite_sha256":"d"*64}
        name="heraldo-test-preupdate-"+REQ+".json"
        (self.root/name).write_text(json.dumps(receipt))
        manifest={"operation":operation,"revision":SRC,"sha256":"d"*64}
        output={"local_package":str(self.root/"synthetic"),"plaintext_sha256":"d"*64}
        with patch.object(bridge, "TEST_STATE_DIR", self.root), \
             patch.object(bridge, "check_test_environment", return_value=self.db), \
             patch.object(bridge, "_private_root", side_effect=lambda p:Path(p)), \
             patch.object(bridge, "_exclusive_job_lock", return_value=nullcontext()), \
             patch.object(bridge, "receipt_status", return_value="verified_and_restored"), \
             patch.object(bridge, "_require_backup_headroom"), \
             patch.object(bridge, "download_verify", return_value=output), \
             patch.object(bridge, "validate_backup", return_value=manifest), \
             patch.object(bridge, "_isolated_restore") as restore:
            self.assertTrue(bridge.verified_test_backup(self.plan))
            restore.assert_called_once()
            manifest["sha256"]="c"*64
            with self.assertRaisesRegex(bridge.TestReleaseBlocked, "test_remote_binding_mismatch"):
                bridge.verified_test_backup(self.plan)


class BootOrderTest(unittest.TestCase):
    def test_test_gate_before_discord_creation(self):
        code=_source_text(Path(__file__).resolve().parents[1] / 'bot.py', encoding='utf-8')
        self.assertIn("_h03_test_enforce_boot()", code)
        self.assertLess(code.index("_h03_test_enforce_boot()"),
                        code.index("bot = commands.Bot("))


if __name__ == "__main__":
    unittest.main()
