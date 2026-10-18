"""H-03: guardia de arranque opt-in, sin ejecutar Discord ni modificar SQLite.

No equivale a protección universal de Railway. Debe instalarse y gobernarse
un controlador externo de publicación antes de habilitar esta comprobación.
"""
from datetime import datetime, timezone, timedelta
import json
import os
from pathlib import Path
import re
import stat
import uuid

PRODUCTION_IDS = (
    "1edabae7-53ff-4a6c-ad55-a1dc0b865b4f",
    "a2ce7142-f315-4ab9-8d6e-ad058c1dc9fc",
    "78a0bdb2-95aa-41e0-8785-32ba17ffeb70",
)
FLAG = "HERALDO_H03_STARTUP_GATE"
FLAG_VALUE = "enabled-after-owner-approval"
REQUEST_VAR = "HERALDO_H03_RELEASE_REQUEST_ID"
STATE_ROOT = Path("/data/.heraldo-h03-daily")
_SHA = re.compile(r"[0-9a-f]{40}\Z")
_REQUEST = re.compile(r"[0-9a-f]{32}\Z")


class StartupBlocked(RuntimeError):
    """Error con código seguro: no filtrar rutas de objetos ni credenciales."""


def _read_private_json(path):
    if path.is_symlink() or not path.is_file():
        raise StartupBlocked("authorization_not_found")
    info = path.stat()
    if (os.name != "posix" or info.st_uid != os.getuid()
            or stat.S_IMODE(info.st_mode) & 0o077):
        raise StartupBlocked("authorization_not_private")
    if info.st_size > 8192:
        raise StartupBlocked("authorization_oversized")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, UnicodeError) as exc:
        raise StartupBlocked("invalid_authorization") from exc


def validate_startup_receipts(*, request_id, target_revision, root,
                              authenticate_remote, now=None):
    """Nunca confiar sólo en un recibo JSON; autenticar el objeto remoto.

    authenticate_remote debe verificar AES-GCM, SHA del manifiesto y una
    restauración SQLite aislada; sólo acepta resultado booleano True.
    """
    if (not isinstance(request_id, str) or not _REQUEST.fullmatch(request_id)
            or not isinstance(target_revision, str) or not _SHA.fullmatch(target_revision)
            or not callable(authenticate_remote)):
        raise StartupBlocked("invalid_startup_identity")
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise StartupBlocked("invalid_clock")
    root = Path(root)
    if root.is_symlink() or not root.is_dir():
        raise StartupBlocked("missing_trusted_volume")
    info = root.stat()
    if (os.name != "posix" or info.st_uid != os.getuid()
            or stat.S_IMODE(info.st_mode) & 0o077):
        raise StartupBlocked("untrusted_volume_permissions")
    stem = "heraldo-production-preupdate-" + request_id
    grant = _read_private_json(root / (stem + ".authorization.json"))
    receipt = _read_private_json(root / (stem + ".json"))
    op = grant.get("operation") if isinstance(grant, dict) else None
    if (not isinstance(op, dict) or op.get("request_id") != request_id
            or op.get("purpose") != "preupdate"
            or not isinstance(op.get("source_revision"), str)
            or not _SHA.fullmatch(op["source_revision"])
            or op.get("source_revision") == target_revision
            or op.get("target_revision") != target_revision
            or grant.get("version") != 1
            or grant.get("status") not in ("update_started", "update_completed")):
        raise StartupBlocked("invalid_grant_binding")
    if (not isinstance(receipt, dict) or receipt.get("version") != 2
            or receipt.get("status") != "verified_and_restored"
            or receipt.get("environment") != "heraldo-production"
            or receipt.get("operation") != op):
        raise StartupBlocked("invalid_backup_binding")
    try:
        started = datetime.fromisoformat(receipt["started_at"])
        finished = datetime.fromisoformat(receipt["finished_at"])
    except (TypeError, ValueError, KeyError) as exc:
        raise StartupBlocked("invalid_receipt_time") from exc
    if (started.tzinfo is None or finished.tzinfo is None
            or started > finished or finished > now
            or finished - started > timedelta(minutes=10)):
        raise StartupBlocked("invalid_receipt_time")
    if (grant["status"] == "update_started"
            and now - started > timedelta(minutes=15)):
        raise StartupBlocked("stale_pending_release")
    try:
        if authenticate_remote(receipt, op) is not True:
            raise StartupBlocked("remote_backup_not_authenticated")
    except StartupBlocked:
        raise
    except Exception:
        # Un error del proveedor puede incluir URLs firmadas en su texto.
        raise StartupBlocked("remote_backup_not_authenticated") from None
    return True


def authenticate_production_backup(receipt, operation):
    """Descarga y restaura sólo sobre un temporal privado dentro del volumen."""
    from backup_job import (_private_root, _exclusive_job_lock,
                            _isolated_restore, _require_backup_headroom)
    from sqlite_recovery import validate_backup
    from supabase_backup import download_verify
    import shutil

    root = STATE_ROOT
    db = Path(os.environ.get("DB_PATH", ""))
    if (not db.is_absolute() or not db.is_file()
            or not db.resolve().is_relative_to(Path("/data"))):
        raise StartupBlocked("invalid_live_database")
    with _exclusive_job_lock(root):
        _require_backup_headroom(db, root)
        work = _private_root(root / "startup-auth" / uuid.uuid4().hex)
        try:
            remote = download_verify(receipt["object"], "heraldo-production",
                                     destination=work / "remote")
            manifest = validate_backup(remote["local_package"], environment="heraldo-production")
            if (manifest.get("operation") != operation
                    or manifest.get("revision") != operation["source_revision"]
                    or manifest.get("sha256") != receipt.get("sqlite_sha256")
                    or remote.get("plaintext_sha256") != manifest.get("sha256")):
                raise StartupBlocked("remote_backup_binding_mismatch")
            _isolated_restore(remote["local_package"], work / "restored.sqlite", manifest)
            return True
        finally:
            shutil.rmtree(work, ignore_errors=True)


def enforce_startup(environ=None, *, root=STATE_ROOT, authenticator=None):
    """Cuando está activa: bloquear antes de crear el bot si no hay permiso."""
    env = os.environ if environ is None else environ
    flag = env.get(FLAG)
    if flag is None:
        return False  # Compatible con Test; NO una barrera productiva universal.
    if flag != FLAG_VALUE:
        raise StartupBlocked("invalid_activation_flag")
    identity = tuple(env.get(k) for k in (
        "RAILWAY_PROJECT_ID", "RAILWAY_ENVIRONMENT_ID", "RAILWAY_SERVICE_ID"))
    if identity != PRODUCTION_IDS:
        raise StartupBlocked("production_identity_mismatch")
    sha = env.get("RAILWAY_GIT_COMMIT_SHA")
    request = env.get(REQUEST_VAR)
    if not sha or not request:
        raise StartupBlocked("missing_release_binding")
    from backup_job import _guard
    source = Path(env.get("DB_PATH", ""))
    try:
        _guard("heraldo-production", source, Path(root))
    except Exception:
        raise StartupBlocked("production_volume_not_verified") from None
    return validate_startup_receipts(
        request_id=request, target_revision=sha, root=root,
        authenticate_remote=authenticator or authenticate_production_backup)
