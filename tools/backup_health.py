"""Read-only, sanitized H-03 health for a single shared alert owner."""
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import sys
from backup_job import receipt_status, BackupJobError


def inspect(root, now=None):
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise BackupJobError("naive_time")
    now = now.astimezone(timezone.utc)
    days = {}
    for path in Path(root).glob("lab-????????.json"):
        try:
            day = datetime.strptime(path.stem[4:], "%Y%m%d").replace(tzinfo=timezone.utc)
            days[day] = receipt_status(path)
        except (ValueError, BackupJobError, OSError):
            return {"status": "CRITICAL", "reason": "invalid_receipt", "incident_key": "lab:invalid_receipt"}
    if not days:
        return {"status": "CRITICAL", "reason": "no_attempt", "incident_key": "lab:no_attempt"}
    latest = max(days)
    failed = sum(value != "verified_and_restored" for value in days.values())
    first = min(days)
    # Closed UTC days with no receipt are missed; current day has a 36 h grace.
    missing = sum(first + timedelta(days=i) not in days
                  for i in range((now.replace(hour=0, minute=0, second=0, microsecond=0)-first).days))
    stale = now - latest > timedelta(hours=36)
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
