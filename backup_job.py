"""Ejecución aislada y puntual de respaldo H-03; no inicia Discord ni programa tareas.

El disparador periódico debe ser externo y explícitamente autorizado. Guarda
un recibo privado por día UTC para evitar subidas duplicadas ante incertidumbre.
"""
from contextlib import closing, contextmanager
from datetime import datetime, timezone
import argparse
import json
import os
from pathlib import Path
import re
import sqlite3
import stat
import sys
import hashlib
import shutil

from sqlite_recovery import create_backup, inspect_database, readonly, validate_backup
from supabase_backup import upload, download_verify

PRODUCTION_IDS = (
    "1edabae7-53ff-4a6c-ad55-a1dc0b865b4f",
    "a2ce7142-f315-4ab9-8d6e-ad058c1dc9fc",
    "78a0bdb2-95aa-41e0-8785-32ba17ffeb70",
)
PRODUCTION_VOLUME_NAME = "heraldo-data"
PRODUCTION_STATE_DIR = Path("/data/.heraldo-h03-daily")


class BackupJobError(RuntimeError):
    """Motivo seguro sin datos de SQLite ni detalles de credenciales."""


def _production_volume(source, state_root, environ=None):
    """Check runtime volume identity and a real kernel mount, not just /data."""
    env = os.environ if environ is None else environ
    mount = Path("/data")
    # Railway documents NAME and MOUNT_PATH; do not assume an injected ID.
    if (env.get("RAILWAY_VOLUME_NAME") != PRODUCTION_VOLUME_NAME or
            env.get("RAILWAY_VOLUME_MOUNT_PATH") != str(mount) or mount.is_symlink()):
        raise BackupJobError("production_volume_identity_mismatch")
    # ismount alone can miss a bind mount on the same device.
    mounted = os.path.ismount(mount)
    if not mounted:
        try:
            mounted = any(line.split()[4] == "/data" for line in
                          Path("/proc/self/mountinfo").read_text().splitlines())
        except (OSError, IndexError):
            mounted = False
    if not mounted:
        raise BackupJobError("production_volume_not_mounted")
    if (source.resolve() != Path(env.get("DB_PATH", "")).resolve() or
            not source.resolve().is_relative_to(mount) or
            state_root.resolve() != PRODUCTION_STATE_DIR):
        raise BackupJobError("production_path_mismatch")


def _guard(environment, source, state_root):
    if not re.fullmatch(r"[a-z][a-z0-9-]{0,30}", environment):
        raise BackupJobError("invalid_environment")
    if source.is_symlink() or not source.is_file():
        raise BackupJobError("invalid_source")
    if environment == "heraldo-production":
        observed = tuple(os.environ.get(k) for k in
                         ("RAILWAY_PROJECT_ID", "RAILWAY_ENVIRONMENT_ID", "RAILWAY_SERVICE_ID"))
        if (observed != PRODUCTION_IDS or
                os.environ.get("HERALDO_PRODUCTION_BACKUP_ENABLED") != "enabled-after-owner-approval"):
            raise BackupJobError("production_not_authorized")
        mount = Path("/data").resolve()
        if (not source.resolve().is_relative_to(mount) or
                not state_root.resolve().is_relative_to(mount)):
            raise BackupJobError("production_path_outside_volume")
        _production_volume(source, state_root)
    elif environment != "lab":
        raise BackupJobError("environment_not_allowed")
    elif os.environ.get("RAILWAY_PROJECT_ID") == PRODUCTION_IDS[0]:
        raise BackupJobError("laboratory_mode_on_production")


def _private_root(path):
    path = Path(path)
    if path.is_symlink():
        raise BackupJobError("state_directory_symlink")
    path.mkdir(mode=0o700, parents=True, exist_ok=True)
    info = path.stat()
    if os.name != "posix" or info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) & 0o077:
        raise BackupJobError("state_directory_not_private")
    return path


@contextmanager
def _exclusive_job_lock(root):
    import fcntl
    fd = os.open(root / ".job.lock",
                 os.O_CREAT | os.O_RDWR | getattr(os, "O_NOFOLLOW", 0), 0o600)
    try:
        info = os.fstat(fd)
        if info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) & 0o077:
            raise BackupJobError("job_lock_not_private")
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise BackupJobError("job_already_running") from exc
        yield
    finally:
        os.close(fd)


def _write_receipt(path, payload, *, initial=False):
    """Diario privado durable; sin contenidos de tablas, contraseñas ni clave AES."""
    encoded = (json.dumps(payload, sort_keys=True) + "\n").encode("utf-8")
    if initial:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL |
                     getattr(os, "O_NOFOLLOW", 0), 0o600)
        with os.fdopen(fd, "wb") as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
    else:
        pending = path.with_name("." + path.name + ".new")
        fd = os.open(pending, os.O_WRONLY | os.O_CREAT | os.O_EXCL |
                     getattr(os, "O_NOFOLLOW", 0), 0o600)
        try:
            with os.fdopen(fd, "wb") as stream:
                stream.write(encoded)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(pending, path)
        finally:
            pending.unlink(missing_ok=True)
    fd = os.open(path.parent, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _isolated_restore(package, target, manifest):
    """Restaurar solamente sobre archivo nuevo; verificar esquema y recuentos."""
    if target.exists() or target.is_symlink():
        raise BackupJobError("restore_target_exists")
    # Production runs in a thread: never change the bot's process-wide umask.
    # Reserve the destination atomically and privately before SQLite opens it.
    try:
        fd = os.open(target, os.O_CREAT | os.O_EXCL | os.O_WRONLY |
                     getattr(os, "O_NOFOLLOW", 0), 0o600)
    except FileExistsError as exc:
        raise BackupJobError("restore_target_exists") from exc
    os.close(fd)
    with closing(readonly(Path(package) / "database.sqlite")) as src, closing(sqlite3.connect(target)) as dst:
        src.backup(dst, pages=128, sleep=0.01)
    expected = {key: manifest[key] for key in
                ("schema_sha256", "rows", "user_version", "application_id")}
    if inspect_database(target) != expected:
        raise BackupJobError("isolated_restore_mismatch")
    if _content_digest(Path(package) / "database.sqlite") != _content_digest(target):
        raise BackupJobError("isolated_restore_content_mismatch")


def _content_digest(path):
    """Compare every value without exposing it; preserve duplicate rows."""
    result = {}
    with closing(readonly(path)) as db:
        for (name,) in db.execute("SELECT name FROM sqlite_master WHERE type='table'"):
            quoted = '"' + name.replace('"', '""') + '"'
            rows = sorted(hashlib.sha256(repr(tuple(row)).encode()).digest()
                          for row in db.execute("SELECT * FROM " + quoted))
            result[name] = hashlib.sha256(b"".join(rows)).hexdigest()
    return result


def receipt_status(path):
    """Read only a private regular receipt; never print its private fields."""
    if path.is_symlink() or not path.is_file():
        raise BackupJobError("invalid_receipt")
    info = path.stat()
    if info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) & 0o077:
        raise BackupJobError("receipt_not_private")
    try:
        data = json.loads(path.read_text())
        return data["status"]
    except (ValueError, KeyError, TypeError) as exc:
        raise BackupJobError("invalid_receipt") from exc


def _remaining_backup_space(root):
    """Conservative free bytes, including optional Railway volume quota.

    Railway can expose a larger filesystem than the attached-volume quota.
    When HERALDO_BACKUP_VOLUME_CAP_MB is supplied, account for all existing
    files on that volume. Never remove files to make room.
    """
    available = shutil.disk_usage(root).free
    configured = os.environ.get("HERALDO_BACKUP_VOLUME_CAP_MB")
    if configured is None:
        return available
    if not configured.isdecimal() or not (100 <= int(configured) <= 100_000):
        raise BackupJobError("invalid_volume_budget")
    volume = Path(os.environ.get("RAILWAY_VOLUME_MOUNT_PATH", "/data"))
    if volume.is_symlink() or not volume.is_dir():
        raise BackupJobError("invalid_volume_mount")
    volume = volume.resolve()
    if not root.resolve().is_relative_to(volume):
        raise BackupJobError("state_outside_volume_budget")
    occupied = 0
    for path in volume.rglob("*"):
        if path.is_symlink():
            continue
        if path.is_file():
            occupied += path.stat().st_size
    return min(available, max(0, int(configured) * 1_000_000 - occupied))


def _require_backup_headroom(source, state_root):
    """Leave room for snapshot, authenticated download, isolated restore, logs."""
    with closing(readonly(source)) as db:
        size = db.execute("PRAGMA page_count").fetchone()[0] * db.execute(
            "PRAGMA page_size").fetchone()[0]
    size = max(size, source.stat().st_size)
    # The live source is never modified and at least 64 MiB remains unused.
    reserve = 3 * size + 64 * 1024 * 1024
    if _remaining_backup_space(state_root) < reserve:
        raise BackupJobError("insufficient_backup_headroom")


def run_once(source, state_root, *, environment, revision, now=None,
             purpose="daily", request_id=None, target_revision=None):
    """Daily idempotence or an independent, candidate-bound preupdate copy."""
    source, state_root = Path(source), Path(state_root)
    _guard(environment, source, state_root)
    if not revision or len(revision) > 100 or not re.fullmatch(r"[A-Za-z0-9_.-]+", revision):
        raise BackupJobError("invalid_revision")
    if environment == "heraldo-production" and (
            not re.fullmatch(r"[0-9a-f]{40}", revision) or
            revision != os.environ.get("RAILWAY_GIT_COMMIT_SHA")):
        raise BackupJobError("source_revision_mismatch")
    operation = None
    if purpose == "preupdate":
        if not isinstance(request_id, str) or not re.fullmatch(r"[0-9a-f]{32}", request_id):
            raise BackupJobError("invalid_update_id")
        if not isinstance(target_revision, str) or not re.fullmatch(r"[0-9a-f]{40}", target_revision):
            raise BackupJobError("invalid_target_revision")
        operation = {"purpose": purpose, "request_id": request_id,
                     "source_revision": revision, "target_revision": target_revision}
    elif purpose != "daily" or request_id is not None or target_revision is not None:
        raise BackupJobError("invalid_backup_purpose")
    root = _private_root(state_root)
    today = now or datetime.now(timezone.utc)
    if today.tzinfo is None:
        raise BackupJobError("naive_time")
    stamp = today.astimezone(timezone.utc).strftime("%Y%m%d")
    basename = (environment + "-" + stamp if purpose == "daily" else
                environment + "-preupdate-" + request_id)
    receipt_path = root / (basename + ".json")
    with _exclusive_job_lock(root):
        if receipt_path.is_symlink() or receipt_path.exists():
            if receipt_status(receipt_path) == "verified_and_restored":
                raise BackupJobError("already_attempted_today" if purpose == "daily"
                                     else "update_already_attempted")
            raise BackupJobError("previous_attempt_needs_review")
        # All purposes share the same production root/lock and budget check.
        _require_backup_headroom(source, root)
        receipt = {"version": 1, "environment": environment, "utc_day": stamp,
                   "status": "started", "started_at": today.astimezone(timezone.utc).isoformat()}
        if operation:
            receipt.update(version=2, operation=operation)
        _write_receipt(receipt_path, receipt, initial=True)
        try:
            # Retain all generations and recovered files on the persistent volume.
            workspace = _private_root(root / basename)
            generation = create_backup(source, workspace / "generations",
                                       environment=environment, revision=revision, timeout=90,
                                       **({"operation": operation} if operation else {}))
            manifest = validate_backup(generation, environment=environment)
            receipt["sqlite_sha256"] = manifest["sha256"]
            receipt["status"] = "upload_unconfirmed"
            _write_receipt(receipt_path, receipt)
            published = upload(generation, environment)
            receipt["object"] = published["object"]
            receipt["status"] = "uploaded_unverified"
            _write_receipt(receipt_path, receipt)
            remote = download_verify(published["object"], environment,
                                     destination=workspace / "remote")
            if remote["plaintext_sha256"] != manifest["sha256"]:
                raise BackupJobError("remote_digest_mismatch")
            remote_manifest = validate_backup(remote["local_package"], environment=environment)
            if remote_manifest["sha256"] != manifest["sha256"]:
                raise BackupJobError("download_manifest_mismatch")
            if operation and remote_manifest.get("operation") != operation:
                raise BackupJobError("download_operation_mismatch")
            _isolated_restore(remote["local_package"], workspace / "restored.sqlite", manifest)
            receipt["status"] = "verified_and_restored"
            receipt["finished_at"] = datetime.now(timezone.utc).isoformat()
            _write_receipt(receipt_path, receipt)
            return "verified_and_restored"
        except BaseException:
            receipt["failed_stage"] = receipt["status"]
            receipt["status"] = "needs_manual_review"
            _write_receipt(receipt_path, receipt)
            raise


def main(argv=None):
    parser = argparse.ArgumentParser(description="Ejecutar H-03 remoto una sola vez; sin Discord")
    parser.add_argument("--db", default=os.environ.get("DB_PATH", ""))
    parser.add_argument("--state-directory", default=os.environ.get("HERALDO_BACKUP_STATE_DIRECTORY", ""))
    parser.add_argument("--environment", default=os.environ.get("HERALDO_BACKUP_ENVIRONMENT", ""))
    parser.add_argument("--revision", default=os.environ.get("HERALDO_BACKUP_REVISION", ""))
    parser.add_argument("--purpose", choices=("daily", "preupdate"), default="daily")
    parser.add_argument("--request-id")
    parser.add_argument("--target-revision")
    args = parser.parse_args(argv)
    if not args.db or not args.state_directory:
        print("H03_JOB status=BLOCKED reason=missing_paths", flush=True)
        return 1
    try:
        status = run_once(args.db, args.state_directory,
                          environment=args.environment, revision=args.revision,
                          purpose=args.purpose, request_id=args.request_id,
                          target_revision=args.target_revision)
        print("H03_JOB status=" + status, flush=True)
        return 0
    except BaseException as exc:
        reason = str(exc) if type(exc) is BackupJobError else type(exc).__name__
        if not re.fullmatch(r"[A-Za-z0-9_]+", reason):
            reason = "unexpected_error"
        print("H03_JOB status=BLOCKED reason=" + reason, flush=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
