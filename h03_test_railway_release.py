"""Puente H-03 para Railway Test REAL: SQLite Test, cifrado y API Railway.

NO aplica a producción ni se ejecuta automáticamente. Operaciones
preparar, publicar, admitir arranque, finalizar; ningún reintento de mutación.
Para publicación se requiere token de PROYECTO TEST en memoria y autorización
de versión Test. No registrar tokens, nombres de objetos ni SQLite.
"""
import argparse
import json
import os
from pathlib import Path
import re
import tempfile

from backup_job import (TEST_IDS, TEST_STATE_DIR, BackupJobError, _guard,
                        _private_root, _exclusive_job_lock,
                        _require_backup_headroom, _isolated_restore,
                        receipt_status, run_once)
from h03_publication_adapter import ReleasePlan
from h03_release_handoff import (HandoffBlocked, prepare_handoff, dispatch_once,
                                 admit_boot, finalize_handoff, inspect_handoff,
                                 _lock, _read)
from h03_railway_test_api import RailwayTestAPI, TestRailwayBlocked
from preupdate_gate import verify_preupdate
from sqlite_recovery import validate_backup
from supabase_backup import download_verify

RELEASE_DIR = TEST_STATE_DIR / ".h03-railway-test-release"
STARTUP_FLAG = "HERALDO_H03_TEST_STARTUP_GATE"
STARTUP_VALUE = "enabled-after-test-owner-approval"
APPROVED_TARGET = "HERALDO_H03_TEST_APPROVED_TARGET_SHA"
ENVIRONMENT = "heraldo-test"
_SHA = re.compile(r"[0-9a-f]{40}\Z")
_REQUEST = re.compile(r"[0-9a-f]{32}\Z")


class TestReleaseBlocked(RuntimeError):
    """Sólo razones operativas fijas, nunca datos del proveedor."""


def check_test_environment(environ=None):
    env = os.environ if environ is None else environ
    ids = tuple(env.get(k) for k in
                ("RAILWAY_PROJECT_ID", "RAILWAY_ENVIRONMENT_ID", "RAILWAY_SERVICE_ID"))
    if ids != TEST_IDS:
        raise TestReleaseBlocked("test_identity_required")
    db_str = env.get("DB_PATH")
    if not db_str:
        raise TestReleaseBlocked("test_database_missing")
    source = Path(db_str)
    try:
        _guard(ENVIRONMENT, source, TEST_STATE_DIR)
    except Exception:
        raise TestReleaseBlocked("test_volume_not_verified") from None
    return source


def state_root():
    return _private_root(_private_root(TEST_STATE_DIR) / ".h03-railway-test-release")


def make_plan(request, source, target):
    if (not isinstance(request, str) or not _REQUEST.fullmatch(request)
            or not isinstance(source, str) or not _SHA.fullmatch(source)
            or not isinstance(target, str) or not _SHA.fullmatch(target)
            or source == target):
        raise TestReleaseBlocked("invalid_release_identity")
    return ReleasePlan("lab", source, target, request)


def _authorised(plan, environ=None):
    env = os.environ if environ is None else environ
    return env.get(APPROVED_TARGET) == plan.target_revision


def verified_test_backup(plan, *, require_fresh=True):
    """Verifica paquete cifrado externo y restaura SÓLO SQLite nueva."""
    source = check_test_environment()
    stem = ENVIRONMENT + "-preupdate-" + plan.request_id
    root = _private_root(TEST_STATE_DIR)
    receipt_file = root / (stem + ".json")
    with _exclusive_job_lock(root):
        if receipt_status(receipt_file) != "verified_and_restored":
            raise TestReleaseBlocked("test_backup_not_verified")
        receipt = json.loads(receipt_file.read_text(encoding="utf-8"))
        operation = {"purpose": "preupdate", "request_id": plan.request_id,
                     "source_revision": plan.source_revision,
                     "target_revision": plan.target_revision}
        if (receipt.get("version") != 2 or
                receipt.get("environment") != ENVIRONMENT or
                receipt.get("operation") != operation or
                not isinstance(receipt.get("object"), str)):
            raise TestReleaseBlocked("test_backup_binding_mismatch")
        _require_backup_headroom(source, root)
        with tempfile.TemporaryDirectory(prefix="test-release-check-", dir=root) as temp:
            remote = download_verify(receipt["object"], ENVIRONMENT,
                                     destination=Path(temp) / "remote")
            manifest = validate_backup(remote["local_package"], environment=ENVIRONMENT)
            if (manifest.get("operation") != operation or
                    manifest.get("revision") != plan.source_revision or
                    manifest.get("sha256") != receipt.get("sqlite_sha256") or
                    remote.get("plaintext_sha256") != manifest.get("sha256")):
                raise TestReleaseBlocked("test_remote_binding_mismatch")
            _isolated_restore(remote["local_package"], Path(temp) / "restored.sqlite",
                              manifest)
    return True


def prepare_release(plan):
    source = check_test_environment()
    current = os.environ.get("RAILWAY_GIT_COMMIT_SHA")
    if current != plan.source_revision or not _authorised(plan):
        raise TestReleaseBlocked("test_revision_not_approved")
    def fresh_backup(_):
        # Copia íntegra desde /data actual, no utiliza snapshot de otra versión.
        run_once(source, TEST_STATE_DIR, environment=ENVIRONMENT,
                 revision=plan.source_revision, purpose="preupdate",
                 request_id=plan.request_id, target_revision=plan.target_revision)
        return verify_preupdate(
            source, TEST_STATE_DIR, environment=ENVIRONMENT,
            request_id=plan.request_id,
            source_revision=plan.source_revision,
            target_revision=plan.target_revision)
    return prepare_handoff(plan, root=state_root(),
                           source_revision=lambda: os.environ.get("RAILWAY_GIT_COMMIT_SHA"),
                           target_approved=lambda p: _authorised(p),
                           backup_verified=fresh_backup)


def dispatch_release(plan, *, client=None):
    check_test_environment()
    if os.environ.get("RAILWAY_GIT_COMMIT_SHA") != plan.source_revision:
        raise TestReleaseBlocked("test_revision_changed")
    client = client or RailwayTestAPI()
    return dispatch_once(
        plan, root=state_root(),
        source_revision=lambda: (client.assert_source(plan.source_revision)
                                 and plan.source_revision),
        target_approved=lambda p: _authorised(p),
        publish_exact=lambda p: client.deploy_exact(p.target_revision))


def load_active_plan():
    check_test_environment()
    with _lock(state_root()) as root:
        index = _read(root, "h03-lab-active.json")
        request = index.get("request_id")
        if not isinstance(request, str) or not _REQUEST.fullmatch(request):
            raise TestReleaseBlocked("invalid_active_pointer")
        record = _read(root, "h03-lab-release-" + request + ".json")
        raw = record.get("plan")
        if not isinstance(raw, dict):
            raise TestReleaseBlocked("invalid_release_record")
        plan = make_plan(request, raw.get("source_revision"),
                         raw.get("target_revision"))
        if raw.get("environment") != "lab" or raw.get("request_id") != request:
            raise TestReleaseBlocked("invalid_release_record")
    return plan


def admit_test_boot():
    check_test_environment()
    plan = load_active_plan()
    return admit_boot(plan, root=state_root(),
                      running_revision=lambda: os.environ.get("RAILWAY_GIT_COMMIT_SHA"),
                      authenticate_backup=lambda p: verified_test_backup(p))


def enforce_test_boot(environ=None):
    """Hook opt-in previo a crear Discord, sin invocar una publicación."""
    env = os.environ if environ is None else environ
    if STARTUP_FLAG not in env:
        return False
    if env.get(STARTUP_FLAG) != STARTUP_VALUE:
        raise TestReleaseBlocked("invalid_test_startup_flag")
    check_test_environment(env)
    return admit_test_boot()


def finalize_release(*, client=None):
    check_test_environment()
    plan = load_active_plan()
    if os.environ.get("RAILWAY_GIT_COMMIT_SHA") != plan.target_revision:
        raise TestReleaseBlocked("target_process_not_running")
    client = client or RailwayTestAPI()
    return finalize_handoff(
        plan, root=state_root(),
        running_revision=lambda: os.environ.get("RAILWAY_GIT_COMMIT_SHA"),
        deployment_confirmed=lambda p, deployment:
            client.deployment_final(deployment, p.target_revision))


def main(argv=None):
    parser = argparse.ArgumentParser(description="H-03 TEST: controlador Railway")
    parser.add_argument("action", choices=("prepare", "dispatch", "boot", "finalize", "status"))
    parser.add_argument("--request-id")
    parser.add_argument("--source-revision")
    parser.add_argument("--target-revision")
    args = parser.parse_args(argv)
    try:
        if args.action in ("prepare", "dispatch"):
            plan = make_plan(args.request_id, args.source_revision, args.target_revision)
            result = prepare_release(plan) if args.action == "prepare" else dispatch_release(plan)
        elif args.action == "boot":
            result = admit_test_boot()
        elif args.action == "finalize":
            result = finalize_release()
        else:
            result = inspect_handoff(load_active_plan(), root=state_root())
        if args.action == "prepare":
            status = "BACKUP_PREPARED_AND_RESTORED" if result is True else "BLOCKED"
        elif args.action == "dispatch":
            # Obtener un ID de Railway no certifica que el bot haya arrancado.
            status = "DEPLOYMENT_SUBMITTED" if isinstance(result, str) else "BLOCKED"
        elif args.action == "boot":
            status = "BOOT_ADMITTED" if result is True else "BLOCKED"
        elif args.action == "finalize":
            status = "DEPLOYMENT_VERIFIED" if result is True else "BLOCKED"
        else:
            status = "STATE_" + result.upper()
        print("H03_RAILWAY_TEST status=" + status, flush=True)
        return 0 if status != "BLOCKED" else 1
    except Exception as exc:
        reason = str(exc) if type(exc) in (
            TestReleaseBlocked, HandoffBlocked, TestRailwayBlocked, BackupJobError
        ) else type(exc).__name__
        if not re.fullmatch(r"[A-Za-z0-9_]+", reason):
            reason = "operation_failed"
        print("H03_RAILWAY_TEST status=BLOCKED reason=" + reason, flush=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
