"""H-03: diario de producción dentro del proceso propietario del volumen SQLite.

Inactivo por defecto. La primera activación solo se permite con identidad exacta
de Railway, clave/cuenta privada presentes y estado persistente bajo /data.
Nunca arranca un segundo bot ni restaura sobre la base original.
"""
import asyncio
from datetime import datetime, time, timezone
import os
from pathlib import Path
import re

from discord.ext import tasks
from backup_job import BackupJobError, PRODUCTION_IDS, _guard, run_once
from supabase_backup import _key, _envir

UTC_RUN_TIME = time(6, 15, tzinfo=timezone.utc)
STATE_DIR = Path("/data/.heraldo-h03-daily")
_REQUIRED_SECRETS = (
    "SUPABASE_BACKUP_URL",
    "SUPABASE_BACKUP_PUBLISHABLE_KEY",
    "SUPABASE_BACKUP_EMAIL",
    "SUPABASE_BACKUP_PASSWORD",
    "SUPABASE_BACKUP_USER_ID",
    "HERALDO_BACKUP_ENCRYPTION_KEY",
)
_source = None
_revision = None


def preflight(db_path, environ=None):
    """No escribe ni transmite datos. Nunca revela variables privadas."""
    env = environ if environ is not None else os.environ
    if env.get("HERALDO_PRODUCTION_BACKUP_ENABLED") != "enabled-after-owner-approval":
        raise BackupJobError("production_not_enabled")
    identity = tuple(env.get(key) for key in (
        "RAILWAY_PROJECT_ID", "RAILWAY_ENVIRONMENT_ID", "RAILWAY_SERVICE_ID"))
    if identity != PRODUCTION_IDS:
        raise BackupJobError("production_identity_mismatch")
    if not db_path:
        raise BackupJobError("missing_source")
    source = Path(db_path)
    if source.is_symlink() or not source.is_file():
        raise BackupJobError("invalid_source")
    mount = Path("/data").resolve()
    if not source.resolve().is_relative_to(mount) or STATE_DIR.is_symlink():
        raise BackupJobError("source_outside_volume")
    revision = env.get("RAILWAY_GIT_COMMIT_SHA", "")
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise BackupJobError("invalid_deployment_revision")
    if any(not env.get(secret) for secret in _REQUIRED_SECRETS):
        raise BackupJobError("missing_backup_secrets")
    # Decode and validate size but never print/store key material. This is a
    # fail-closed preflight before scheduling or writing any receipt.
    if environ is None:
        _key()
        _envir("heraldo-production")
    # A production quota must be supplied; Railway's filesystem free size
    # alone is not necessarily the effective volume quota.
    if env.get("HERALDO_BACKUP_VOLUME_CAP_MB") != "500":
        raise BackupJobError("unverified_volume_budget")
    return source, revision


def _perform_once():
    if _source is None or _revision is None:
        raise BackupJobError("scheduler_not_initialized")
    # Re-check activation/identity/secret availability before every run.
    source, revision = preflight(_source)
    return run_once(source, STATE_DIR, environment="heraldo-production",
                    revision=revision)


@tasks.loop(time=UTC_RUN_TIME, reconnect=True)
async def _daily_backup():
    """Time-based scheduler offloads all disk and network operations."""
    try:
        result = await asyncio.to_thread(_perform_once)
    except asyncio.CancelledError:
        raise
    except Exception as exc:
        # Log a fixed code; never log exception messages/tracebacks potentially
        # containing signed URLs, tokens, table names or personal information.
        if type(exc) is BackupJobError and str(exc) in (
            "already_attempted_today", "previous_attempt_needs_review",
            "insufficient_backup_headroom", "production_not_enabled",
            "production_identity_mismatch", "invalid_source",
            "missing_backup_secrets", "unverified_volume_budget"):
            reason = str(exc)
        else:
            reason = type(exc).__name__ if re.fullmatch(
                r"[A-Za-z][A-Za-z0-9_]*", type(exc).__name__) else "unknown_failure"
        print("H03_DAILY status=BLOCKED reason=" + reason, flush=True)
    else:
        if result == "verified_and_restored":
            print("H03_DAILY status=VERIFIED_AND_RESTORED", flush=True)
        else:
            print("H03_DAILY status=BLOCKED reason=unexpected_result", flush=True)


def start_if_authorized(db_path):
    """Call once after Discord's first successful on_ready.

    Never starts without the explicit production flag, even in Railway Test.
    """
    global _source, _revision
    if not os.environ.get("HERALDO_PRODUCTION_BACKUP_ENABLED"):
        return False
    source, revision = preflight(db_path)
    _guard("heraldo-production", source, STATE_DIR)
    if _daily_backup.is_running():
        return True
    _source, _revision = source, revision
    _daily_backup.start()
    print("H03_DAILY status=SCHEDULED utc=06:15", flush=True)
    return True


def is_running():
    return _daily_backup.is_running()
