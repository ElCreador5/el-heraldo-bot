"""Railway Test GraphQL: contrato exacto de commit, sin peticiones reales."""
import os
import unittest
from unittest.mock import Mock, patch
from urllib.error import URLError

import h03_railway_test_api as api

SOURCE = "a" * 40
TARGET = "b" * 40
WRONG = "c" * 40
DEPLOYMENT = "49d6828a-b935-4a17-b442-76f4d0ddcb24"


def entry(id=DEPLOYMENT, status="SUCCESS", sha=SOURCE, branch="Pruebas",
          service=api.TEST_SERVICE, env=api.TEST_ENVIRONMENT):
    return {"id": id, "status": status, "serviceId": service,
            "environmentId": env, "meta": {"commitHash": sha, "branch": branch}}


class APIClientTests(unittest.TestCase):
    def setUp(self):
        self.rows = [entry()]
        self.single = entry(status="SUCCESS", sha=TARGET)
        self.calls = []
        self.fail = None
        def transport(query, variables, token):
            self.calls.append((query, variables, token))
            if self.fail:
                raise self.fail
            if query == api.QUERY_LIST:
                return {"data": {"deployments": {"edges": [{"node": row} for row in self.rows]}}}
            if query == api.MUTATION_DEPLOY:
                return {"data": {"serviceInstanceDeployV2": DEPLOYMENT}}
            if query == api.QUERY_ONE:
                return {"data": {"deployment": self.single}}
            raise AssertionError("Unexpected graphql")
        self.client = api.RailwayTestAPI(token="SENSITIVE_PROJECT_TOKEN", transport=transport)

    def test_read_live_test_revision(self):
        self.assertEqual(self.client.current_revision(), SOURCE)
        self.assertTrue(self.client.assert_source(SOURCE))
        args = self.calls[0][1]["input"]
        self.assertEqual(args, {"projectId": api.TEST_PROJECT,
                                "environmentId": api.TEST_ENVIRONMENT,
                                "serviceId": api.TEST_SERVICE})
        self.assertNotIn("SENSITIVE_PROJECT_TOKEN", repr(args))

    def test_exact_SHA_passed_to_supported_mutation(self):
        self.assertEqual(self.client.deploy_exact(TARGET), DEPLOYMENT)
        query, variables, token = self.calls[-1]
        self.assertEqual(query, api.MUTATION_DEPLOY)
        self.assertEqual(variables["commitSha"], TARGET)
        self.assertEqual(variables["serviceId"], api.TEST_SERVICE)
        self.assertEqual(token, "SENSITIVE_PROJECT_TOKEN")
        self.assertEqual(len(self.calls), 1)

    def test_final_success_requires_matching_current_deployment(self):
        self.rows = [entry(sha=TARGET)]
        self.assertTrue(self.client.deployment_final(DEPLOYMENT, TARGET))
        self.assertEqual(len(self.calls), 2)

    def test_status_in_progress_never_counts_as_finished(self):
        self.single["status"] = "DEPLOYING"
        self.assertFalse(self.client.deployment_final(DEPLOYMENT, TARGET))

    def test_false_success_if_another_commit_went_live(self):
        self.rows = [entry(sha=WRONG)]
        self.assertFalse(self.client.deployment_final(DEPLOYMENT, TARGET))

    def test_wrong_sha_is_blocked(self):
        self.single["meta"]["commitHash"] = WRONG
        with self.assertRaisesRegex(api.TestRailwayBlocked, "deployment_revision_mismatch"):
            self.client.deployment_final(DEPLOYMENT, TARGET)

    def test_terminal_failure_blocks(self):
        self.single["status"] = "FAILED"
        with self.assertRaisesRegex(api.TestRailwayBlocked, "deployment_failed"):
            self.client.deployment_final(DEPLOYMENT, TARGET)

    def test_service_and_environment_mismatch_are_blocked(self):
        self.rows = [entry(service="WRONG")]
        with self.assertRaisesRegex(api.TestRailwayBlocked, "unexpected_deployment_identity"):
            self.client.current_revision()
        self.single["serviceId"] = "WRONG"
        with self.assertRaisesRegex(api.TestRailwayBlocked, "unexpected_deployment_identity"):
            self.client.deployment_final(DEPLOYMENT, TARGET)

    def test_in_progress_and_unknown_branch_block_preflight(self):
        self.rows = [entry(status="BUILDING")]
        with self.assertRaisesRegex(api.TestRailwayBlocked, "current_deployment_not_ready"):
            self.client.assert_source(SOURCE)
        self.rows = [entry(branch="main")]
        with self.assertRaisesRegex(api.TestRailwayBlocked, "current_deployment_not_ready"):
            self.client.assert_source(SOURCE)

    def test_changed_source_cannot_dispatch(self):
        with self.assertRaisesRegex(api.TestRailwayBlocked, "source_revision_changed"):
            self.client.assert_source(TARGET)

    def test_invalid_identity_blocked_without_network(self):
        for bad in ("../main", TARGET[:8], "", None):
            with self.subTest(value=bad), self.assertRaises(api.TestRailwayBlocked):
                self.client.deploy_exact(bad)
        self.assertEqual(self.calls, [])

    def test_missing_token_and_production_identity_block(self):
        with patch.dict(os.environ, {"RAILWAY_PROJECT_ID": "1edabae7-53ff-4a6c-ad55-a1dc0b865b4f"}):
            with self.assertRaisesRegex(api.TestRailwayBlocked, "production_forbidden"):
                api.RailwayTestAPI(token="anything", transport=self.client._transport)
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(api.TestRailwayBlocked, "missing_test_railway_token"):
                api.RailwayTestAPI(transport=self.client._transport)

    def test_graphql_errors_and_ambiguous_write_no_retry(self):
        self.fail = URLError("SECRET_TOKEN_HERE")
        with self.assertRaisesRegex(api.TestRailwayBlocked, "provider_request_failed") as caught:
            self.client.deploy_exact(TARGET)
        self.assertNotIn("SECRET_TOKEN_HERE", str(caught.exception))
        self.assertEqual(len(self.calls), 1)
        self.fail = None
        self.client._transport = lambda *args: {"errors": [{"message": "SENSITIVE"}]}
        with self.assertRaisesRegex(api.TestRailwayBlocked, "provider_graphql_rejected") as caught:
            self.client.deploy_exact(TARGET)
        self.assertNotIn("SENSITIVE", str(caught.exception))

    def test_deployment_mutation_empty_is_not_confirmation(self):
        self.client._transport = lambda *args: {
            "data": {"serviceInstanceDeployV2": None}}
        with self.assertRaisesRegex(api.TestRailwayBlocked, "deployment_identifier_unconfirmed"):
            self.client.deploy_exact(TARGET)


if __name__ == "__main__":
    unittest.main()
