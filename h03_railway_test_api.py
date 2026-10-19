"""Adaptador REAL de Railway GraphQL, estrictamente para el proyecto Test.

No envía peticiones en importación. La mutación sólo se ejecuta por llamada
explícita y con un SHA de 40 caracteres; nunca reintenta mutaciones inciertas.
El token está exclusivamente en memoria, no se registra en trazas ni recibos.
"""
import json
import os
import re
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

API = "https://backboard.railway.com/graphql/v2"
TEST_PROJECT = "747a1ee0-cdab-4ad5-8e45-a6ddfccc9b61"
TEST_ENVIRONMENT = "71b77daf-9092-4af0-913f-32c57367fff3"
TEST_SERVICE = "13a555fc-7ddd-4712-a9bc-e88509e18b2b"
REPOSITORY = "ElCreador5/el-heraldo-bot"
BRANCH = "Pruebas"
_SHA = re.compile(r"[0-9a-f]{40}\Z")
_ID = re.compile(r"[0-9A-Za-z_-]{1,128}\Z")
QUERY_LIST = """query($input:DeploymentListInput!, $first:Int){
  deployments(input:$input,first:$first){
    edges{node{id status serviceId environmentId meta}}
  }
}"""
QUERY_ONE = """query($id:String!){
  deployment(id:$id){id status serviceId environmentId meta}
}"""
MUTATION_DEPLOY = """mutation($serviceId:String!,$environmentId:String!,$commitSha:String!){
  serviceInstanceDeployV2(serviceId:$serviceId,environmentId:$environmentId,commitSha:$commitSha)
}"""


class TestRailwayBlocked(RuntimeError):
    """Sólo mensajes codificados, nunca respuestas ni URLs privadas del proveedor."""


def _require_sha(sha):
    if not isinstance(sha, str) or not _SHA.fullmatch(sha):
        raise TestRailwayBlocked("invalid_revision")
    return sha


def _default_transport(query, variables, token):
    request = Request(
        API,
        data=json.dumps({"query": query, "variables": variables}).encode("utf-8"),
        headers={"Content-Type": "application/json",
                 "Project-Access-Token": token},
        method="POST",
    )
    with urlopen(request, timeout=15) as answer:
        if answer.status != 200:
            raise TestRailwayBlocked("provider_http_error")
        data = answer.read(262145)
        if len(data) > 262144:
            raise TestRailwayBlocked("provider_response_too_large")
        return json.loads(data)


class RailwayTestAPI:
    def __init__(self, *, token=None, transport=None):
        if os.environ.get("RAILWAY_PROJECT_ID") == "1edabae7-53ff-4a6c-ad55-a1dc0b865b4f":
            raise TestRailwayBlocked("production_forbidden")
        self._transport = transport or _default_transport
        self._token = token if token is not None else os.environ.get("HERALDO_H03_TEST_RAILWAY_TOKEN")
        if not isinstance(self._token, str) or not self._token.strip():
            raise TestRailwayBlocked("missing_test_railway_token")

    def _call(self, query, variables):
        try:
            response = self._transport(query, variables, self._token)
        except (TestRailwayBlocked, URLError, HTTPError, TimeoutError, OSError,
                ValueError, TypeError, Exception):
            # Nunca propagar texto del proveedor, su URL ni credenciales.
            raise TestRailwayBlocked("provider_request_failed") from None
        if (not isinstance(response, dict) or response.get("errors") or
                not isinstance(response.get("data"), dict)):
            raise TestRailwayBlocked("provider_graphql_rejected")
        return response["data"]

    @staticmethod
    def _deployment(value):
        if (not isinstance(value, dict) or not isinstance(value.get("id"), str)
                or not _ID.fullmatch(value["id"]) or
                value.get("serviceId") != TEST_SERVICE or
                value.get("environmentId") != TEST_ENVIRONMENT or
                not isinstance(value.get("status"), str) or
                not isinstance(value.get("meta"), dict)):
            raise TestRailwayBlocked("unexpected_deployment_identity")
        revision = value["meta"].get("commitHash")
        if not isinstance(revision, str) or not _SHA.fullmatch(revision):
            raise TestRailwayBlocked("missing_deployment_revision")
        return {"id": value["id"], "status": value["status"],
                "revision": revision, "branch": value["meta"].get("branch")}

    def recent(self):
        raw = self._call(QUERY_LIST, {"input": {
            "projectId": TEST_PROJECT, "environmentId": TEST_ENVIRONMENT,
            "serviceId": TEST_SERVICE}, "first": 5}).get("deployments")
        if not isinstance(raw, dict) or not isinstance(raw.get("edges"), list):
            raise TestRailwayBlocked("deployment_list_unavailable")
        results = []
        for item in raw["edges"]:
            if not isinstance(item, dict):
                raise TestRailwayBlocked("invalid_deployment_list")
            results.append(self._deployment(item.get("node")))
        if not results:
            raise TestRailwayBlocked("deployment_list_empty")
        return results

    def current_revision(self):
        # Sólo el despliegue actual. Un despliegue en progreso no equivale a
        # seguir en el SHA anterior: evitar admitir una publicación concurrente.
        value = self.recent()[0]
        if value["status"] != "SUCCESS" or value["branch"] != BRANCH:
            raise TestRailwayBlocked("current_deployment_not_ready")
        return value["revision"]

    def assert_source(self, source_sha):
        if self.current_revision() != _require_sha(source_sha):
            raise TestRailwayBlocked("source_revision_changed")
        return True

    def deploy_exact(self, target_sha):
        sha = _require_sha(target_sha)
        # No retry: si esta llamada se interrumpe, el diario queda incierto.
        deployment_id = self._call(MUTATION_DEPLOY, {
            "serviceId": TEST_SERVICE, "environmentId": TEST_ENVIRONMENT,
            "commitSha": sha}).get("serviceInstanceDeployV2")
        if not isinstance(deployment_id, str) or not _ID.fullmatch(deployment_id):
            raise TestRailwayBlocked("deployment_identifier_unconfirmed")
        return deployment_id

    def deployment_final(self, deployment_id, target_sha):
        if not isinstance(deployment_id, str) or not _ID.fullmatch(deployment_id):
            raise TestRailwayBlocked("invalid_deployment_id")
        deployment = self._deployment(
            self._call(QUERY_ONE, {"id": deployment_id}).get("deployment"))
        if deployment["id"] != deployment_id or deployment["revision"] != _require_sha(target_sha):
            raise TestRailwayBlocked("deployment_revision_mismatch")
        if deployment["status"] in {"FAILED", "CRASHED", "REMOVED", "SKIPPED"}:
            raise TestRailwayBlocked("deployment_failed")
        if deployment["status"] != "SUCCESS":
            return False
        current = self.recent()[0]
        return (current["id"] == deployment_id and
                current["status"] == "SUCCESS" and
                current["revision"] == target_sha)
