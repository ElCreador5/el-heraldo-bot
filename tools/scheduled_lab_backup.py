"""Entrada exclusiva para Railway Cron de laboratorio, nunca abre la BD del bot.

Cada ejecución fabrica una SQLite sintética temporal, solicita H-03 cifrado,
descarga, comprueba restauración y sale. Los recibos persistentes van a /data.
No lee DB_PATH ni necesita DISCORD_TOKEN.
"""
from contextlib import closing
import os
from pathlib import Path
import sqlite3
import sys
import tempfile
import signal
import json
from datetime import datetime, timezone

from backup_job import BackupJobError, run_once
from tools.backup_health import inspect as inspect_health

TEST_PROJECT = "747a1ee0-cdab-4ad5-8e45-a6ddfccc9b61"
TEST_ENVIRONMENT = "71b77daf-9092-4af0-913f-32c57367fff3"
TEST_SERVICE = "heraldo-h03-lab-cron"
STATE = Path("/data/h03-daily-receipts")


def run():
    if (os.environ.get("RAILWAY_PROJECT_ID") != TEST_PROJECT
            or os.environ.get("RAILWAY_ENVIRONMENT_ID") != TEST_ENVIRONMENT
            or os.environ.get("RAILWAY_SERVICE_NAME") != TEST_SERVICE):
        raise BackupJobError("not_railway_test_cron_service")
    if "DISCORD_TOKEN" in os.environ:
        raise BackupJobError("discord_token_must_not_be_present")
    if "DB_PATH" in os.environ:
        raise BackupJobError("bot_database_path_must_not_be_present")
    if not Path("/data").is_mount():
        raise BackupJobError("persistent_volume_not_mounted")
    os.umask(0o077)
    # One-time activation boundary permits proving a scheduler-triggered first run.
    boundary = os.environ.get("HERALDO_LAB_NOT_BEFORE_UTC")
    if boundary:
        try:
            activation = datetime.fromisoformat(boundary)
            if activation.tzinfo is None:
                raise ValueError
        except ValueError as exc:
            raise BackupJobError("invalid_activation_boundary") from exc
        if datetime.now(timezone.utc) < activation:
            print("H03_CRON status=WAITING_ACTIVATION source=synthetic", flush=True)
            return 0
    print("H03_CRON status=STARTED utc_day=" + datetime.now(timezone.utc).strftime("%Y%m%d"), flush=True)
    with tempfile.TemporaryDirectory(prefix="h03-cron-lab-") as work:
        source = Path(work) / "synthetic.sqlite"
        with closing(sqlite3.connect(source)) as conn:
            conn.execute("CREATE TABLE synthetic_probe (id INTEGER PRIMARY KEY, marker TEXT NOT NULL)")
            conn.execute("INSERT INTO synthetic_probe VALUES (1, 'LAB_CREDENTIAL_FREE')")
            conn.commit()
        try:
            result = run_once(source, STATE, environment="lab", revision="scheduled-lab")
        except BackupJobError as exc:
            if str(exc) == "already_attempted_today":
                print("H03_CRON status=ALREADY_ATTEMPTED no_retry=true", flush=True)
                print("H03_HEALTH " + json.dumps(inspect_health(STATE), sort_keys=True), flush=True)
                return 0
            raise
        if result != "verified_and_restored":
            raise BackupJobError("unverified_laboratory_result")
        print("H03_CRON status=VERIFIED_AND_RESTORED source=synthetic", flush=True)
        print("H03_HEALTH " + json.dumps(inspect_health(STATE), sort_keys=True), flush=True)
        return 0


if __name__ == "__main__":
    try:
        def deadline(_signum, _frame):
            raise BackupJobError("job_deadline_exceeded")
        signal.signal(signal.SIGALRM, deadline)
        signal.alarm(180)
        raise SystemExit(run())
    except Exception as exc:
        reason = str(exc) if type(exc) is BackupJobError else type(exc).__name__
        if not reason.replace("_", "").isalnum():
            reason = type(exc).__name__
        print("H03_CRON status=FAILED reason=" + reason, flush=True)
        raise SystemExit(1)
