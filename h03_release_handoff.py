"""H-03: protocolo duradero de DOS FASES para pruebas aisladas.

NO PUBLICA NADA: todos los servicios se inyectan, sin red ni tokens. Es un
contrato de laboratorio, NO un controlador habilitado para Railway producción.
Cada cambio se escribe y fsync antes de ejecutar acciones externas. Un envío
ambiguo no se repite; el administrador deberá reconciliarlo manualmente.
"""
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
import fcntl
import json
import os
from pathlib import Path
import re
import stat
import uuid

from h03_publication_adapter import ReleasePlan, ReleaseBlocked

PRODUCTION_PROJECT_ID = "1edabae7-53ff-4a6c-ad55-a1dc0b865b4f"
_SHA = re.compile(r"[0-9a-f]{40}\Z")
_REQUEST = re.compile(r"[0-9a-f]{32}\Z")
_DEPLOYMENT = re.compile(r"[A-Za-z0-9_-]{1,128}\Z")
_VALID_PHASES = frozenset((
    "prepared", "dispatching", "submitted", "boot_admitted",
    "completed", "needs_manual_review"))
_PENDING_TTL = timedelta(minutes=15)
_INDEX = "h03-lab-active.json"


class HandoffBlocked(ReleaseBlocked):
    """Sólo códigos fijos; no interpolar secretos ni errores de proveedor."""


def _plan(plan):
    if not isinstance(plan, ReleasePlan):
        raise HandoffBlocked("invalid_plan")
    try:
        plan.validate_for_lab()
    except ReleaseBlocked:
        raise HandoffBlocked("laboratory_only_or_invalid_plan") from None
    if os.environ.get("RAILWAY_PROJECT_ID") == PRODUCTION_PROJECT_ID:
        raise HandoffBlocked("production_forbidden")
    return {"environment": "lab", "request_id": plan.request_id,
            "source_revision": plan.source_revision,
            "target_revision": plan.target_revision}


def _utc(now):
    value = now or datetime.now(timezone.utc)
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise HandoffBlocked("clock_not_utc_aware")
    return value.astimezone(timezone.utc)


def _root(root):
    root = Path(root)
    if (os.name != "posix" or root.is_symlink() or not root.is_dir()
            or not root.is_absolute()):
        raise HandoffBlocked("untrusted_state_directory")
    info = root.stat()
    if (info.st_uid != os.getuid() or
            stat.S_IMODE(info.st_mode) & 0o077):
        raise HandoffBlocked("untrusted_state_directory")
    return root


def _read(root, name):
    path = root / name
    if path.is_symlink() or not path.is_file():
        raise HandoffBlocked("missing_private_record")
    info = path.stat()
    if (info.st_uid != os.getuid() or
            stat.S_IMODE(info.st_mode) & 0o077 or info.st_size > 8192):
        raise HandoffBlocked("unsafe_private_record")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, UnicodeError):
        raise HandoffBlocked("corrupt_private_record") from None
    if not isinstance(value, dict):
        raise HandoffBlocked("corrupt_private_record")
    return value


def _durable_write(root, name, value, *, initial=False):
    """Atomic + fsync, private mode; nunca confiar en symlinks preexistentes."""
    target = root / name
    if target.is_symlink() or (initial and target.exists()):
        raise HandoffBlocked("record_already_exists_or_symlink")
    if target.exists():
        old = target.stat()
        if old.st_uid != os.getuid() or stat.S_IMODE(old.st_mode) & 0o077:
            raise HandoffBlocked("unsafe_private_record")
    temp = root / ("." + name + "." + uuid.uuid4().hex + ".pending")
    encoded = (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()
    if len(encoded) > 8192:
        raise HandoffBlocked("record_oversized")
    fd = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_EXCL |
                 getattr(os, "O_NOFOLLOW", 0), 0o600)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp, target)
        directory = os.open(root, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        temp.unlink(missing_ok=True)


@contextmanager
def _lock(root):
    root = _root(root)
    path = root / ".h03-lab-release.lock"
    if path.is_symlink():
        raise HandoffBlocked("unsafe_lock")
    fd = os.open(path, os.O_CREAT | os.O_RDWR |
                 getattr(os, "O_NOFOLLOW", 0), 0o600)
    try:
        info = os.fstat(fd)
        if info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) & 0o077:
            raise HandoffBlocked("unsafe_lock")
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise HandoffBlocked("release_already_locked") from None
        yield root
    finally:
        os.close(fd)


def _name(plan):
    return "h03-lab-release-" + plan["request_id"] + ".json"


def _active(root, plan):
    index = _read(root, _INDEX)
    if index != {"version": 1, "request_id": plan["request_id"]}:
        raise HandoffBlocked("another_release_is_active")
    record = _read(root, _name(plan))
    if record.get("version") != 1 or record.get("plan") != plan:
        raise HandoffBlocked("release_binding_mismatch")
    if record.get("phase") not in _VALID_PHASES:
        raise HandoffBlocked("corrupt_release_phase")
    return record


def _expiry(record, now):
    try:
        started = datetime.fromisoformat(record["prepared_at"])
        return (started.tzinfo is not None and
                started <= now <= started + _PENDING_TTL)
    except (KeyError, ValueError, TypeError):
        return False


def _require_pending(record, now):
    if not _expiry(record, now):
        raise HandoffBlocked("release_window_expired")


def _updated(root, plan, record, phase, now, **changes):
    if record["phase"] == "completed":
        raise HandoffBlocked("release_already_completed")
    record = {**record, "phase": phase, "updated_at": now.isoformat(), **changes}
    _durable_write(root, _name(plan), record)
    return record


def prepare_handoff(plan, *, root, source_revision, target_approved,
                    backup_verified, now=None):
    """Fase A: prueba de respaldo y autorización; sin enviar un despliegue."""
    info, when = _plan(plan), _utc(now)
    if not all(callable(x) for x in (source_revision, target_approved, backup_verified)):
        raise HandoffBlocked("missing_trusted_adapter")
    with _lock(root) as directory:
        # Cada solicitud deja un archivo permanente. No aceptar huérfanos
        # resultantes de una caída entre guardar solicitud e índice.
        journal_files = list(directory.glob("h03-lab-release-*.json"))
        if (directory / _INDEX).is_file():
            index = _read(directory, _INDEX)
            if index.get("version") != 1 or not isinstance(index.get("request_id"), str):
                raise HandoffBlocked("corrupt_active_pointer")
            previous = _read(directory, "h03-lab-release-" + index["request_id"] + ".json")
            if previous.get("phase") != "completed":
                raise HandoffBlocked("previous_release_not_closed")
            if previous.get("plan", {}).get("target_revision") != info["source_revision"]:
                raise HandoffBlocked("release_history_diverged")
        elif journal_files:
            raise HandoffBlocked("unreconciled_orphan_release")
        if (directory / _name(info)).exists() or (directory / _name(info)).is_symlink():
            raise HandoffBlocked("request_id_reused")
        if source_revision() != info["source_revision"] or target_approved(plan) is not True:
            raise HandoffBlocked("source_or_approval_changed")
        if backup_verified(plan) != "verified_and_restored":
            raise HandoffBlocked("backup_not_verified")
        if source_revision() != info["source_revision"] or target_approved(plan) is not True:
            raise HandoffBlocked("source_or_approval_changed")
        record = {"version": 1, "plan": info, "phase": "prepared",
                  "prepared_at": when.isoformat(), "updated_at": when.isoformat(),
                  "deployment_id": None, "boot_at": None, "completed_at": None}
        _durable_write(directory, _name(info), record, initial=True)
        _durable_write(directory, _INDEX,
                       {"version": 1, "request_id": info["request_id"]})
        return True


def _review_if_pending(root, plan, when):
    with _lock(root) as directory:
        current = _active(directory, plan)
        if current["phase"] in {"dispatching", "submitted", "boot_admitted"}:
            _updated(directory, plan, current, "needs_manual_review", when)


def dispatch_once(plan, *, root, source_revision, target_approved,
                  publish_exact, now=None):
    """Registrar intent irreversible ANTES de llamar al proveedor.

    Una caída deja dispatching: no repetir a ciegas. La nueva versión puede
    haber arrancado antes de recibir el ID de Railway; ese estado se conserva.
    """
    info, when = _plan(plan), _utc(now)
    if not all(callable(x) for x in (source_revision, target_approved, publish_exact)):
        raise HandoffBlocked("missing_trusted_adapter")
    with _lock(root) as directory:
        current = _active(directory, info)
        if current["phase"] != "prepared":
            raise HandoffBlocked("dispatch_already_attempted")
        _require_pending(current, when)
        if source_revision() != info["source_revision"] or target_approved(plan) is not True:
            raise HandoffBlocked("source_or_approval_changed")
        _updated(directory, info, current, "dispatching", when)
    try:
        deployment = publish_exact(plan)
        if (not isinstance(deployment, str) or
                not _DEPLOYMENT.fullmatch(deployment)):
            raise HandoffBlocked("unconfirmed_deployment_identifier")
    except Exception:
        _review_if_pending(root, info, when)
        raise HandoffBlocked("ambiguous_deployment_requires_review") from None
    with _lock(root) as directory:
        current = _active(directory, info)
        if current["phase"] not in {"dispatching", "boot_admitted"}:
            raise HandoffBlocked("uncertain_dispatch_result")
        _updated(directory, info, current,
                 "submitted" if current["phase"] == "dispatching"
                 else "boot_admitted", when, deployment_id=deployment)
    return deployment


def admit_boot(plan, *, root, running_revision, authenticate_backup, now=None):
    """Fase B: proceso NUEVO valida SHA y respaldo antes de iniciar Discord."""
    info, when = _plan(plan), _utc(now)
    if not all(callable(x) for x in (running_revision, authenticate_backup)):
        raise HandoffBlocked("missing_trusted_adapter")
    with _lock(root) as directory:
        current = _active(directory, info)
        if current["phase"] not in {
                "dispatching", "submitted", "boot_admitted", "completed"}:
            raise HandoffBlocked("release_not_dispatched_or_blocked")
        if current["phase"] != "completed":
            _require_pending(current, when)
        if running_revision() != info["target_revision"]:
            raise HandoffBlocked("boot_revision_mismatch")
        if authenticate_backup(plan) is not True:
            raise HandoffBlocked("backup_not_authenticated")
        if current["phase"] != "completed" and current["phase"] != "boot_admitted":
            _updated(directory, info, current, "boot_admitted", when,
                     boot_at=when.isoformat())
    return True


def finalize_handoff(plan, *, root, running_revision, deployment_confirmed,
                     now=None):
    """Controlador externo certifica resultado FINAL, nunca sólo un deploy ID."""
    info, when = _plan(plan), _utc(now)
    if not all(callable(x) for x in (running_revision, deployment_confirmed)):
        raise HandoffBlocked("missing_trusted_adapter")
    with _lock(root) as directory:
        current = _active(directory, info)
        if current["phase"] == "completed":
            if running_revision() != info["target_revision"]:
                raise HandoffBlocked("running_revision_changed")
            return True
        if current["phase"] != "boot_admitted":
            raise HandoffBlocked("boot_not_admitted")
        _require_pending(current, when)
        deployment_id = current["deployment_id"]
        if (not isinstance(deployment_id, str) or
                not _DEPLOYMENT.fullmatch(deployment_id)):
            raise HandoffBlocked("deployment_not_recorded")
        if running_revision() != info["target_revision"]:
            raise HandoffBlocked("running_revision_mismatch")
        if deployment_confirmed(plan, deployment_id) is not True:
            raise HandoffBlocked("deployment_not_final")
        if running_revision() != info["target_revision"]:
            raise HandoffBlocked("running_revision_changed")
        _updated(directory, info, current, "completed", when,
                 completed_at=when.isoformat())
    return True


def inspect_handoff(plan, *, root):
    """Vista de estado sin valores secretos, no muta el diario."""
    info = _plan(plan)
    with _lock(root) as directory:
        data = _active(directory, info)
        return data["phase"]
