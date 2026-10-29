"""H-03 Enzonic: SQLite real, recibos durables y recuperación sin Discord.

Inactivo sin bandera propia y ensayo real verificado. Nunca borra generaciones.
Las operaciones potencialmente lentas se ejecutan en un proceso auxiliar.
"""
import argparse
from datetime import datetime, timezone
from contextlib import closing
import json
import os
from pathlib import Path
import re
import tempfile

import enzonic_test_host as host
from backup_job import (BackupJobError, _exclusive_job_lock, _isolated_restore,
                        _require_backup_headroom, _write_receipt, run_once)
from sqlite_recovery import validate_backup, readonly
from supabase_backup import (_config, _http, _storage, _object_key,
                             download_verify, MAX_UPLOAD_BYTES, TEST_BUCKET)

# Una validación distinta de la copia diaria; mismo ID ante reintentos/reinicios.
VALIDATION_ID = "e0a6432ddbb6484b940199bfdebc48c1"
VALIDATION_NAME = "heraldo-test-validation-" + VALIDATION_ID + ".json"
REMOTE_BUDGET_BYTES = 100_000_000  # Tope conservador exclusivo de Test.
MAX_SOURCE_BYTES = 20_000_000  # Memoria acotada para contenedor de 512 MB.


def configure():
    host.guard(host.DATABASE, host.STATE)
    with closing(readonly(host.DATABASE)) as db:
        logical_size = db.execute("PRAGMA page_count").fetchone()[0] * db.execute("PRAGMA page_size").fetchone()[0]
    if max(logical_size, host.DATABASE.stat().st_size) > MAX_SOURCE_BYTES:
        raise BackupJobError("enzonic_source_exceeds_memory_budget")
    return host.revision()


def _list(prefix, headers):
    base = _config()[0]
    items = []
    for offset in range(0, 10000, 100):
        body = json.dumps({"prefix": prefix, "limit": 100, "offset": offset,
                           "sortBy": {"column": "name", "order": "asc"}}).encode()
        raw = _http(base + "/storage/v1/object/list/" + TEST_BUCKET, method="POST",
                    headers={**headers, "Content-Type": "application/json"},
                    payload=body, limit=262144)
        page = json.loads(raw)
        if not isinstance(page, list) or any(not isinstance(item, dict) for item in page):
            raise BackupJobError("test_storage_inventory_invalid")
        items.extend(page)
        if len(page) < 100:
            return items
    raise BackupJobError("test_storage_inventory_limit")


def remote_inventory():
    host.check_test_secrets()
    _, headers = _storage(host.ENVIRONMENT)
    days = _list("heraldo-test", headers)
    if len(days) > 1000:
        raise BackupJobError("test_storage_inventory_limit")
    objects, total = [], 0
    for day in days:
        name = day.get("name", "")
        if not re.fullmatch(r"[0-9]{8}", name) or day.get("id") is not None:
            raise BackupJobError("test_storage_inventory_invalid")
        for item in _list("heraldo-test/" + name, headers):
            key = _object_key("heraldo-test/" + name + "/" + item.get("name", ""), host.ENVIRONMENT)
            size = (item.get("metadata") or {}).get("size")
            if not isinstance(size, int) or size < 1 or size > MAX_UPLOAD_BYTES:
                raise BackupJobError("test_storage_inventory_invalid")
            total += size
            objects.append(key)
    return objects, total


def check_remote_budget():
    _, occupied = remote_inventory()
    # Reserva el máximo permitido por objeto antes de empezar una subida.
    if occupied + MAX_UPLOAD_BYTES > REMOTE_BUDGET_BYTES:
        raise BackupJobError("test_remote_storage_budget_exhausted")
    return occupied


def _recover_receipt(name):
    configure()
    root = host.private_state()
    with _exclusive_job_lock(root):
        receipt = host.read_receipt(name)
        if receipt.get("environment") != host.ENVIRONMENT:
            raise BackupJobError("receipt_identity_mismatch")
        obj = _object_key(receipt.get("object", ""), host.ENVIRONMENT)
        _require_backup_headroom(host.DATABASE, root)
        with tempfile.TemporaryDirectory(prefix="recovery-", dir=root) as directory:
            remote = download_verify(obj, host.ENVIRONMENT, destination=Path(directory) / "remote")
            manifest = validate_backup(remote["local_package"], environment=host.ENVIRONMENT)
            if (manifest["sha256"] != receipt.get("sqlite_sha256")
                    or remote["plaintext_sha256"] != manifest["sha256"]
                    or manifest.get("operation") != receipt.get("operation")):
                raise BackupJobError("remote_digest_or_operation_mismatch")
            _isolated_restore(remote["local_package"], Path(directory) / "restored.sqlite", manifest)
        receipt.update(status="verified_and_restored",
                       last_recovery_at=datetime.now(timezone.utc).isoformat())
        _write_receipt(root / name, receipt)
    return "verified_and_restored"


def require_validation():
    record = host.read_receipt(VALIDATION_NAME)
    if (record.get("status") != "verified_and_restored"
            or record.get("environment") != host.ENVIRONMENT
            or record.get("operation", {}).get("purpose") != "validation"
            or record.get("operation", {}).get("request_id") != VALIDATION_ID):
        raise BackupJobError("enzonic_backup_validation_missing")


def validate():
    rev = configure()
    if (host.STATE / VALIDATION_NAME).exists():
        # Autentica nuevamente el objeto; jamás vuelve a subir tras incertidumbre.
        return _recover_receipt(VALIDATION_NAME)
    check_remote_budget()
    return run_once(host.DATABASE, host.STATE, environment=host.ENVIRONMENT,
                    revision=rev, purpose="validation", request_id=VALIDATION_ID)


def _adopt_remote_day(day):
    """Conserva la copia diaria anterior al cambio de proveedor, sin duplicarla."""
    objects, _ = remote_inventory()
    candidates = [obj for obj in objects if obj.startswith("heraldo-test/" + day + "/")]
    root = host.private_state()
    with _exclusive_job_lock(root):
        path = root / ("heraldo-test-" + day + ".json")
        if path.exists():
            return False
        _require_backup_headroom(host.DATABASE, root)
        for obj in reversed(sorted(candidates)):
            with tempfile.TemporaryDirectory(prefix="adopt-", dir=root) as directory:
                remote = download_verify(obj, host.ENVIRONMENT, destination=Path(directory) / "remote")
                manifest = validate_backup(remote["local_package"], environment=host.ENVIRONMENT)
                if manifest.get("operation"):
                    continue  # Validaciones/preactualizaciones no son la copia diaria.
                if (manifest["created_at"][:10].replace("-", "") != day
                        or remote["plaintext_sha256"] != manifest["sha256"]):
                    raise BackupJobError("remote_generation_identity_mismatch")
                _isolated_restore(remote["local_package"], Path(directory) / "restored.sqlite", manifest)
                _write_receipt(path, {"version": 1, "environment": host.ENVIRONMENT,
                               "utc_day": day, "status": "verified_and_restored",
                               "object": obj, "sqlite_sha256": manifest["sha256"],
                               "started_at": manifest["created_at"],
                               "finished_at": datetime.now(timezone.utc).isoformat(),
                               "adopted_download_only": True}, initial=True)
                return True
    return False


def due(now=None):
    rev = configure()
    require_validation()
    if os.environ.get(host.FLAG) != host.FLAG_VALUE:
        raise BackupJobError("enzonic_scheduler_not_enabled")
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise BackupJobError("naive_time")
    now = now.astimezone(timezone.utc)
    if now.hour * 60 + now.minute < 375:
        return "waiting"
    if any(host.read_receipt(path.name).get("status") != "verified_and_restored"
           for path in host.STATE.glob("heraldo-test-*.json")):
        raise BackupJobError("previous_attempt_needs_review")
    day = now.strftime("%Y%m%d")
    receipt = host.STATE / ("heraldo-test-" + day + ".json")
    if receipt.exists() or receipt.is_symlink():
        if host.read_receipt(receipt.name).get("status") == "verified_and_restored":
            return "already_verified"
        raise BackupJobError("previous_attempt_needs_review")
    if _adopt_remote_day(day):
        return "verified_and_restored"
    check_remote_budget()
    return run_once(host.DATABASE, host.STATE, environment=host.ENVIRONMENT, revision=rev, now=now)


def scheduler_preflight():
    if os.environ.get(host.FLAG) != host.FLAG_VALUE:
        raise BackupJobError("enzonic_scheduler_not_enabled")
    configure()
    require_validation()


def main(argv=None):
    parser = argparse.ArgumentParser(description="Operaciones exclusivas de Enzonic Test; sin iniciar Discord")
    parser.add_argument("action", choices=("prepare-persistence", "verify-persistence", "verify-token",
                                           "inspect", "validate", "due", "recover"))
    parser.add_argument("--day")
    parser.add_argument("--validation", action="store_true")
    args = parser.parse_args(argv)
    try:
        # Reservar memoria/CPU para Discord; estos límites sólo afectan al worker.
        import resource
        resource.setrlimit(resource.RLIMIT_AS, (256 * 1024 * 1024, 256 * 1024 * 1024))
        os.nice(10)
        if args.action.endswith("persistence"):
            result = host.persistence_probe("prepare" if args.action.startswith("prepare") else "verify")
        elif args.action == "verify-token":
            host.verify_test_token()
            result = "TEST_IDENTITY_VERIFIED"
        elif args.action == "validate":
            result = validate()
        elif args.action == "due":
            result = due()
        elif args.action == "recover":
            if args.validation:
                name = VALIDATION_NAME
            else:
                if not re.fullmatch(r"[0-9]{8}", args.day or ""):
                    raise BackupJobError("invalid_generation_day")
                datetime.strptime(args.day, "%Y%m%d")
                name = "heraldo-test-" + args.day + ".json"
            result = _recover_receipt(name)
        else:
            configure()
            check_remote_budget()
            result = "PREFLIGHT_VERIFIED"
        print("H03_ENZONIC status=" + result.upper(), flush=True)
        return 0
    except Exception as exc:
        reason = str(exc) if type(exc) is BackupJobError else type(exc).__name__
        if not re.fullmatch(r"[A-Za-z0-9_]+", reason):
            reason = "operation_failed"
        print("H03_ENZONIC status=BLOCKED reason=" + reason, flush=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
