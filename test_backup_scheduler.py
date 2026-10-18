"""Daily real Test backup in the owner service, with startup catch-up."""
import asyncio
import os
import subprocess
import sys

from discord.ext import tasks
from backup_job import TEST_IDS, BackupJobError

_last_status = None


def _invoke():
    env = {k: v for k, v in os.environ.items() if k != "DISCORD_TOKEN"}
    result = subprocess.run([sys.executable, "-m", "test_backup_runtime", "due"],
                            env=env, capture_output=True, timeout=240)
    # Do not pass through provider output or an exception traceback.
    if result.returncode:
        return "BLOCKED"
    return "VERIFIED_AND_RESTORED" if b"status=VERIFIED_AND_RESTORED" in result.stdout else "IDLE"


@tasks.loop(seconds=60, reconnect=True)
async def _check_due():
    global _last_status
    try:
        status = await asyncio.to_thread(_invoke)
    except Exception:
        status = "BLOCKED"
    if status != "IDLE" and (status != _last_status or status == "VERIFIED_AND_RESTORED"):
        print("H03_TEST_SCHEDULE status=" + status, flush=True)
    if status != "IDLE":
        _last_status = status


def start_if_authorized():
    if not os.environ.get("HERALDO_TEST_BACKUP_ENABLED"):
        return False
    identity = tuple(os.environ.get(k) for k in
                     ("RAILWAY_PROJECT_ID", "RAILWAY_ENVIRONMENT_ID", "RAILWAY_SERVICE_ID"))
    if identity != TEST_IDS or os.environ.get("HERALDO_TEST_BACKUP_ENABLED") != "enabled":
        raise BackupJobError("test_not_authorized")
    if not _check_due.is_running():
        _check_due.start()
        print("H03_TEST_SCHEDULE status=SCHEDULED utc=06:15 startup_catchup=true", flush=True)
    return True
