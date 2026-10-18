"""H-03 gate primitives for a trusted release controller, inactive on import.

No GitHub/Railway credentials or deployments are managed here. A protected
controller must invoke guarded_update; an ordinary successful CI is insufficient.
Never expose private receipts, object names, hashes or the recovered database.
"""
import argparse
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import re
import uuid

from backup_job import (BackupJobError, PRODUCTION_STATE_DIR, _guard, _private_root,
                        _exclusive_job_lock, _require_backup_headroom,
                        _write_receipt, _isolated_restore, receipt_status, run_once)
from sqlite_recovery import validate_backup
from supabase_backup import download_verify


def _binding(request_id, source_revision, target_revision):
    if not isinstance(request_id, str) or not re.fullmatch(r"[0-9a-f]{32}", request_id):
        raise BackupJobError("invalid_update_id")
    if any(not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{40}", value)
           for value in (source_revision, target_revision)):
        raise BackupJobError("invalid_update_revision")
    return {"purpose": "preupdate", "request_id": request_id,
            "source_revision": source_revision, "target_revision": target_revision}


def _verify_locked(source, root, environment, operation, now):
    """Caller holds the shared H-03 lock for verification and publication."""
    if now.tzinfo is None:
        raise BackupJobError("naive_time")
    if environment == "heraldo-production" and (
            operation["source_revision"] != os.environ.get("RAILWAY_GIT_COMMIT_SHA")):
        raise BackupJobError("source_revision_mismatch")
    stem = environment + "-preupdate-" + operation["request_id"]
    receipt_path = root / (stem + ".json")
    if receipt_status(receipt_path) != "verified_and_restored":
        raise BackupJobError("update_backup_not_verified")
    try:
        receipt = json.loads(receipt_path.read_text())
        if (receipt.get("version") != 2 or receipt.get("environment") != environment or
                receipt.get("operation") != operation):
            raise BackupJobError("update_receipt_binding_mismatch")
        start = datetime.fromisoformat(receipt["started_at"])
        finish = datetime.fromisoformat(receipt["finished_at"])
        if (start.tzinfo is None or finish.tzinfo is None or
                start > finish or finish > now or
                finish - start > timedelta(minutes=10) or
                now - start > timedelta(minutes=15)):
            raise BackupJobError("update_receipt_expired_or_invalid")
        if receipt.get("utc_day") != start.astimezone(timezone.utc).strftime("%Y%m%d"):
            raise BackupJobError("update_receipt_period_mismatch")
        object_name = receipt["object"]
    except (ValueError, TypeError, KeyError, AttributeError) as exc:
        raise BackupJobError("invalid_update_receipt") from exc
    # Do not trust a local JSON success marker: authenticate/download again and
    # require the operation bound inside the AES-GCM authenticated manifest.
    _require_backup_headroom(source, root)
    check = _private_root(root / stem / "rechecks" / uuid.uuid4().hex)
    downloaded = download_verify(object_name, environment, destination=check / "remote")
    manifest = validate_backup(downloaded["local_package"], environment=environment)
    if (manifest.get("operation") != operation or
            manifest.get("revision") != operation["source_revision"] or
            manifest["sha256"] != receipt.get("sqlite_sha256") or
            downloaded["plaintext_sha256"] != manifest["sha256"]):
        raise BackupJobError("update_remote_binding_mismatch")
    _isolated_restore(downloaded["local_package"], check / "restored.sqlite", manifest)
    return start


def verify_preupdate(source, state_root, *, environment, request_id,
                     source_revision, target_revision, now=None):
    """Read/recheck only; does not authorize a later unguarded publication."""
    operation = _binding(request_id, source_revision, target_revision)
    source, state_root = Path(source), Path(state_root)
    _guard(environment, source, state_root)
    root = _private_root(state_root)
    with _exclusive_job_lock(root):
        _verify_locked(source, root, environment, operation, now or datetime.now(timezone.utc))
    return "verified_and_restored"


def guarded_update(source, state_root, *, environment, request_id,
                   source_revision, target_revision, apply_update, now=None):
    """Invoke a trusted synchronous controller only after a fresh remote restore.

    One-shot durable authorization is reserved before the callback. Any failure
    or crash requires reconciliation. Keep the lock through the actual update;
    a controller must recheck its own main/candidate SHA and deploy exact content.
    It must return exactly True after confirmed completion, or raise on failure.
    This cooperative lock does not freeze Discord writes or protect bypass paths.
    """
    operation = _binding(request_id, source_revision, target_revision)
    if not callable(apply_update):
        raise BackupJobError("invalid_update_controller")
    source, state_root = Path(source), Path(state_root)
    _guard(environment, source, state_root)
    root = _private_root(state_root)
    with _exclusive_job_lock(root):
        authorization = root / (environment + "-preupdate-" + request_id + ".authorization.json")
        if authorization.exists() or authorization.is_symlink():
            raise BackupJobError("update_already_consumed_or_uncertain")
        started = _verify_locked(source, root, environment, operation, now or datetime.now(timezone.utc))
        # Download/restore may have consumed the freshness window.
        if (now or datetime.now(timezone.utc)) - started > timedelta(minutes=15):
            raise BackupJobError("update_receipt_expired_or_invalid")
        _guard(environment, source, state_root)
        if environment == "heraldo-production" and source_revision != os.environ.get("RAILWAY_GIT_COMMIT_SHA"):
            raise BackupJobError("source_revision_mismatch")
        record = {"version": 1, "operation": operation, "status": "update_started"}
        _write_receipt(authorization, record, initial=True)
        try:
            result = apply_update()
            if result is not True:
                raise BackupJobError("update_result_unconfirmed")
        except BaseException:
            record["status"] = "needs_manual_review"
            _write_receipt(authorization, record)
            raise
        record["status"] = "update_completed"
        _write_receipt(authorization, record)
        return result


def main(argv=None):
    parser = argparse.ArgumentParser(description="H-03 previo: ejecutar solo dentro del servicio dueño de /data")
    parser.add_argument("action", choices=("prepare", "verify"))
    parser.add_argument("--request-id", required=True)
    parser.add_argument("--source-revision", required=True)
    parser.add_argument("--target-revision", required=True)
    args = parser.parse_args(argv)
    try:
        _binding(args.request_id, args.source_revision, args.target_revision)
        source = os.environ.get("DB_PATH", "")
        if not source:
            raise BackupJobError("missing_source")
        if args.action == "prepare":
            run_once(source, PRODUCTION_STATE_DIR, environment="heraldo-production",
                     revision=args.source_revision, purpose="preupdate",
                     request_id=args.request_id, target_revision=args.target_revision)
        else:
            verify_preupdate(source, PRODUCTION_STATE_DIR, environment="heraldo-production",
                             request_id=args.request_id, source_revision=args.source_revision,
                             target_revision=args.target_revision)
        print("H03_PREUPDATE status=VERIFIED_AND_RESTORED", flush=True)
        return 0
    except BaseException as exc:
        reason = str(exc) if type(exc) is BackupJobError else type(exc).__name__
        if not re.fullmatch(r"[A-Za-z0-9_]+", reason):
            reason = "unexpected_error"
        print("H03_PREUPDATE status=BLOCKED reason=" + reason, flush=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
