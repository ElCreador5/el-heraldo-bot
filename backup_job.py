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
import tempfile

from sqlite_recovery import create_backup, inspect_database, readonly, validate_backup
from supabase_backup import upload, download_verify

PRODUCTION_IDS = (
    "1edabae7-53ff-4a6c-ad55-a1dc0b865b4f",
    "a2ce7142-f315-4ab9-8d6e-ad058c1dc9fc",
    "78a0bdb2-95aa-41e0-8785-32ba17ffeb70",
)


class BackupJobError(RuntimeError):
    """Motivo seguro sin datos de SQLite ni detalles de credenciales."""


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
    with closing(readonly(Path(package) / "database.sqlite")) as src, closing(sqlite3.connect(target)) as dst:
        src.backup(dst, pages=128, sleep=0.01)
    expected = {key: manifest[key] for key in
                ("schema_sha256", "rows", "user_version", "application_id")}
    if inspect_database(target) != expected:
        raise BackupJobError("isolated_restore_mismatch")


def run_once(source, state_root, *, environment, revision, now=None):
    """Una única ejecución por día UTC; un error nunca produce reintento ciego."""
    source, state_root = Path(source), Path(state_root)
    _guard(environment, source, state_root)
    if not revision or len(revision) > 100 or not re.fullmatch(r"[A-Za-z0-9_.-]+", revision):
        raise BackupJobError("invalid_revision")
    root = _private_root(state_root)
    today = now or datetime.now(timezone.utc)
    if today.tzinfo is None:
        raise BackupJobError("naive_time")
    stamp = today.astimezone(timezone.utc).strftime("%Y%m%d")
    receipt_path = root / (environment + "-" + stamp + ".json")
    with _exclusive_job_lock(root):
        if receipt_path.is_symlink() or receipt_path.exists():
            raise BackupJobError("already_attempted_today")
        receipt = {"version": 1, "environment": environment, "utc_day": stamp,
                   "status": "started", "started_at": today.astimezone(timezone.utc).isoformat()}
        _write_receipt(receipt_path, receipt, initial=True)
        try:
            with tempfile.TemporaryDirectory(prefix="heraldo-job-") as directory:
                workspace = Path(directory)
                generation = create_backup(source, workspace / "generations",
                                           environment=environment, revision=revision, timeout=90)
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
                _isolated_restore(remote["local_package"], workspace / "restored.sqlite", manifest)
                receipt["status"] = "verified_and_restored"
                receipt["finished_at"] = datetime.now(timezone.utc).isoformat()
                _write_receipt(receipt_path, receipt)
                return "verified_and_restored"
        except BaseException:
            receipt["status"] = "needs_manual_review"
            _write_receipt(receipt_path, receipt)
            raise


def main(argv=None):
    parser = argparse.ArgumentParser(description="Ejecutar H-03 remoto una sola vez; sin Discord")
    parser.add_argument("--db", default=os.environ.get("DB_PATH", ""))
    parser.add_argument("--state-directory", default=os.environ.get("HERALDO_BACKUP_STATE_DIRECTORY", ""))
    parser.add_argument("--environment", default=os.environ.get("HERALDO_BACKUP_ENVIRONMENT", ""))
    parser.add_argument("--revision", default=os.environ.get("HERALDO_BACKUP_REVISION", ""))
    args = parser.parse_args(argv)
    if not args.db or not args.state_directory:
        print("H03_JOB status=BLOCKED reason=missing_paths", flush=True)
        return 1
    try:
        status = run_once(args.db, args.state_directory,
                          environment=args.environment, revision=args.revision)
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
