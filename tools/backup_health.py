"""Read-only, sanitized H-03 health check for the dedicated laboratory cron.

A valid 'verified_and_restored' status is not enough: validate the receipt's
identity, UTC period and actual completion time before declaring it healthy.
No sensitive receipt fields are ever returned or printed.
"""
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import sys

from backup_job import receipt_status, BackupJobError


_ALLOWED = {
    "started", "upload_unconfirmed", "uploaded_unverified",
    "needs_manual_review", "verified_and_restored",
}


def _invalid_receipt():
    return {"status": "CRITICAL", "reason": "invalid_receipt",
            "incident_key": "lab:invalid_receipt"}


def inspect(root, now=None):
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise BackupJobError("naive_time")
    now = now.astimezone(timezone.utc)
    current_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    days = {}
    verified_at = []
    # A malformed lab receipt must not be silently ignored.
    for path in Path(root).glob("lab-*.json"):
        try:
            day = datetime.strptime(path.stem[4:], "%Y%m%d").replace(tzinfo=timezone.utc)
            if day > current_day:
                raise ValueError("future_period")
            status = receipt_status(path)  # Validates file type, ownership and permissions.
            data = json.loads(path.read_text(encoding="utf-8"))
            if (not isinstance(data, dict) or
                    data.get("version") != 1 or data.get("environment") != "lab" or
                    data.get("utc_day") != day.strftime("%Y%m%d") or
                    status not in _ALLOWED):
                raise ValueError("incorrect_receipt_identity")
            started = data.get("started_at")
            if not isinstance(started, str):
                raise ValueError("missing_start_time")
            start = datetime.fromisoformat(started)
            if (start.tzinfo is None or
                    start.astimezone(timezone.utc).date() != day.date() or
                    start > now):
                raise ValueError("invalid_start_time")
            if status == "verified_and_restored":
                finished = data.get("finished_at")
                if not isinstance(finished, str) or not finished:
                    raise ValueError("missing_completion_time")
                timestamp = datetime.fromisoformat(finished)
                if (timestamp.tzinfo is None or timestamp > now or timestamp < start or
                        timestamp.astimezone(timezone.utc) - start.astimezone(timezone.utc)
                        > timedelta(minutes=10)):
                    raise ValueError("invalid_completion_time")
                verified_at.append(timestamp)
            days[day] = status
        except (ValueError, TypeError, KeyError, BackupJobError, OSError, OverflowError):
            return _invalid_receipt()
    if not days:
        return {"status": "CRITICAL", "reason": "no_attempt", "incident_key": "lab:no_attempt"}
    latest = max(days)
    failed = sum(value != "verified_and_restored" for value in days.values())
    first = min(days)
    # Detect closed UTC days that have no receipt. Never delete or backfill one.
    missing = sum(first + timedelta(days=i) not in days
                  for i in range((current_day - first).days))
    stale = not verified_at or now - max(verified_at) > timedelta(hours=36)
    reason = "attempt_needs_review" if failed else "missing_period" if missing else "stale" if stale else "verified"
    return {"status": "OK" if reason == "verified" else "CRITICAL", "reason": reason,
            "failed_periods": failed, "missing_periods": missing,
            "latest_utc_day": latest.strftime("%Y%m%d"),
            "incident_key": "lab:" + reason}


if __name__ == "__main__":
    try:
        report = inspect(Path("/data/h03-daily-receipts"))
        print("H03_HEALTH " + json.dumps(report, sort_keys=True), flush=True)
        sys.exit(0 if report["status"] == "OK" else 1)
    except Exception:
        print('H03_HEALTH {"status":"CRITICAL","reason":"health_read_failed","incident_key":"lab:health_read_failed"}', flush=True)
        sys.exit(1)
