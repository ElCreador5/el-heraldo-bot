"""Real Test SQLite backup/recovery, run as a short-lived worker subprocess.

No destination argument, no Discord import, no write access to the live SQLite.
The worker has its own identity and key; Lab and production keep their keys.
"""
import argparse
import base64
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import tempfile

from backup_job import (BackupJobError, TEST_STATE_DIR, _guard, _private_root,
                        _exclusive_job_lock, _require_backup_headroom,
                        _write_receipt, _isolated_restore, receipt_status, run_once)
from sqlite_recovery import validate_backup
from supabase_backup import _key, _config, _object_key, download_verify

ENVIRONMENT = "heraldo-test"
SECRET_NAMES = ("SUPABASE_BACKUP_URL", "SUPABASE_BACKUP_PUBLISHABLE_KEY",
                "SUPABASE_BACKUP_EMAIL", "SUPABASE_BACKUP_PASSWORD",
                "SUPABASE_BACKUP_USER_ID", "HERALDO_BACKUP_ENCRYPTION_KEY")


def configure():
    source = Path(os.environ.get("DB_PATH", ""))
    _guard(ENVIRONMENT, source, TEST_STATE_DIR)
    revision = os.environ.get("RAILWAY_GIT_COMMIT_SHA", "")
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise BackupJobError("invalid_deployment_revision")
    # Worker credentials belong to the new Test-only bucket identity. The
    # synthetic cron keeps its original independent values and encryption key.
    for name in SECRET_NAMES:
        if not os.environ.get(name):
            raise BackupJobError("missing_test_secrets")
    _key()
    _, public_key, _, _, _ = _config()
    if not public_key.startswith("sb_publishable_"):
        try:
            encoded = public_key.split(".")[1]
            role = json.loads(base64.urlsafe_b64decode(encoded + "=" * (-len(encoded) % 4)))["role"]
        except (ValueError, KeyError, IndexError):
            raise BackupJobError("invalid_public_key") from None
        if role != "anon":
            raise BackupJobError("privileged_key_forbidden")
    return source, revision


def recover_day(source, day):
    """Authenticate an existing generation, also reconcile an uncertain upload.

    Recovery is always in a fresh private temporary directory on the Test volume.
    Failure retains the original receipt. This function never uploads anything.
    """
    if not re.fullmatch(r"[0-9]{8}", day):
        raise BackupJobError("invalid_generation_day")
    datetime.strptime(day, "%Y%m%d")
    _guard(ENVIRONMENT, source, TEST_STATE_DIR)
    root = _private_root(TEST_STATE_DIR)
    path = root / (ENVIRONMENT + "-" + day + ".json")
    with _exclusive_job_lock(root):
        receipt_status(path)
        receipt = json.loads(path.read_text())
        if receipt.get("environment") != ENVIRONMENT or receipt.get("utc_day") != day:
            raise BackupJobError("receipt_identity_mismatch")
        name = _object_key(receipt.get("object", ""), ENVIRONMENT)
        if name.split("/")[1] != day or not re.fullmatch(r"[0-9a-f]{64}", receipt.get("sqlite_sha256", "")):
            raise BackupJobError("receipt_identity_mismatch")
        _require_backup_headroom(source, root)
        with tempfile.TemporaryDirectory(prefix="recovery-", dir=root) as directory:
            workspace = Path(directory)
            remote = download_verify(name, ENVIRONMENT, destination=workspace / "remote")
            manifest = validate_backup(remote["local_package"], environment=ENVIRONMENT)
            if manifest["sha256"] != receipt["sqlite_sha256"] or remote["plaintext_sha256"] != manifest["sha256"]:
                raise BackupJobError("remote_digest_mismatch")
            _isolated_restore(remote["local_package"], workspace / "restored.sqlite", manifest)
        receipt["last_recovery_at"] = datetime.now(timezone.utc).isoformat()
        if receipt.get("status") != "verified_and_restored":
            receipt["status"] = "verified_and_restored"
            receipt["finished_at"] = receipt["last_recovery_at"]
            receipt["reconciled_download_only"] = True
        _write_receipt(path, receipt)
    return "verified_and_restored"


def run_due(source, revision, now=None):
    now = now or datetime.now(timezone.utc)
    # Run immediately on initial activation; thereafter at/after 06:15 UTC.
    root = TEST_STATE_DIR
    if now.hour * 60 + now.minute < 6 * 60 + 15 and root.exists() and any(root.glob("heraldo-test-*.json")):
        return "waiting"
    try:
        return run_once(source, root, environment=ENVIRONMENT, revision=revision, now=now)
    except BackupJobError as exc:
        if str(exc) == "already_attempted_today":
            return "already_verified"
        raise


def main(argv=None):
    parser = argparse.ArgumentParser(description="Respaldo real y recuperación aislada de Test")
    parser.add_argument("action", choices=("run", "due", "recover"))
    parser.add_argument("--day")
    args = parser.parse_args(argv)
    try:
        source, revision = configure()
        if args.action == "recover":
            result = recover_day(source, args.day or "")
        elif args.action == "due":
            result = run_due(source, revision)
        else:
            result = run_once(source, TEST_STATE_DIR, environment=ENVIRONMENT, revision=revision)
        if result not in ("waiting", "already_verified"):
            print("H03_TEST status=" + result.upper(), flush=True)
        return 0
    except Exception as exc:
        reason = str(exc) if type(exc) is BackupJobError else type(exc).__name__
        if not re.fullmatch(r"[A-Za-z0-9_]+", reason):
            reason = "operation_failed"
        print("H03_TEST status=BLOCKED reason=" + reason, flush=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
