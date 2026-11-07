"""Production-only scheduler for confirmed /anuncios jobs.

No legacy /programar commands, auto-responses, sticky messages or template
automation is installed. Sending is at-most-once: a crash after a network
request is left 'uncertain' for manual inspection, never retried blindly.
"""
from __future__ import annotations

import calendar
from contextlib import closing
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import discord
from discord.ext import tasks

STATE_DDL = """
CREATE TABLE IF NOT EXISTS message_schedule_state (
    guild_id INTEGER NOT NULL, job_id TEXT NOT NULL, next_run TEXT,
    status TEXT NOT NULL DEFAULT 'pending', message_id INTEGER,
    detail TEXT, dirty INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (guild_id, job_id)
)
"""


def next_occurrence(job, now: datetime) -> str | None:
    """Calculate the next scheduled time after now, preserving local clock."""
    now = now.astimezone(timezone.utc)
    repeat = job.get("repeat", "ninguna")
    if repeat == "ninguna":
        return None
    origin = datetime.fromisoformat(job["start"]).astimezone(timezone.utc)
    zone = ZoneInfo(job.get("zone") or "America/Santo_Domingo")
    if repeat in {"custom", "intervalo"}:
        parts = job.get("repeat_parts") or {}
        if repeat == "intervalo":
            from message_autofeeds import interval_seconds
            interval = interval_seconds(job["interval"])
            months = 0
        else:
            months = int(parts.get("months") or 0)
            interval = (int(parts.get("days") or 0) * 86400
                        + int(parts.get("hours") or 0) * 3600
                        + int(parts.get("minutes") or 0) * 60)
        if months < 0 or months > 120 or interval < 0:
            raise ValueError("invalid_repeat")
        if months == 0:
            if interval < 3600:
                raise ValueError("repeat_below_production_minimum")
            steps = max(1, int((now - origin).total_seconds() // interval) + 1)
            return (origin + timedelta(seconds=steps * interval)).isoformat()
        original_local = origin.astimezone(zone)
        for step in range(1, 1201):
            month_index = original_local.month - 1 + step * months
            year = original_local.year + month_index // 12
            month = month_index % 12 + 1
            if year > 9999:
                raise ValueError("repeat_out_of_range")
            day = min(original_local.day, calendar.monthrange(year, month)[1])
            candidate = original_local.replace(year=year, month=month, day=day)
            candidate += timedelta(seconds=step * interval)
            if candidate.astimezone(timezone.utc) > now:
                return candidate.astimezone(timezone.utc).isoformat()
        raise ValueError("repeat_out_of_range")
    if repeat == "mensual":
        local_origin, local_now = origin.astimezone(zone), now.astimezone(zone)
        offset = max(0, (local_now.year - local_origin.year) * 12
                     + local_now.month - local_origin.month)
        for step in range(offset, offset + 14):
            month_index = local_origin.month - 1 + step
            year = local_origin.year + month_index // 12
            month = month_index % 12 + 1
            day = min(local_origin.day, calendar.monthrange(year, month)[1])
            candidate = local_origin.replace(year=year, month=month, day=day)
            if candidate.astimezone(timezone.utc) > now:
                return candidate.astimezone(timezone.utc).isoformat()
        raise ValueError("monthly_schedule_out_of_range")
    if repeat not in {"diaria", "semanal"}:
        raise ValueError("invalid_repeat")
    local_origin = origin.astimezone(zone)
    days = 1 if repeat == "diaria" else 7
    elapsed = max(0, (now.astimezone(zone).date() - local_origin.date()).days // days)
    candidate = local_origin + timedelta(days=elapsed * days)
    while candidate.astimezone(timezone.utc) <= now:
        candidate += timedelta(days=days)
    return candidate.astimezone(timezone.utc).isoformat()


class AnnouncementScheduler:
    def __init__(self, host):
        self.host = host

    def initialize(self):
        with closing(self.host["db_connect"]()) as conn:
            conn.execute(STATE_DDL)
            columns = {row[1] for row in conn.execute(
                "PRAGMA table_info(message_schedule_state)")}
            if "dirty" not in columns:
                conn.execute(
                    "ALTER TABLE message_schedule_state "
                    "ADD COLUMN dirty INTEGER NOT NULL DEFAULT 0")
            # Unknown delivery after a restart is never automatically retried.
            conn.execute(
                "UPDATE message_schedule_state SET status='uncertain',"
                " detail='Delivery interrupted; inspect destination before retry' "
                "WHERE status='sending'"
            )

    def start(self):
        if not self.worker.is_running():
            self.initialize()
            self.worker.start()

    def state(self, guild_id, job):
        with closing(self.host["db_connect"]()) as conn:
            conn.execute(
                "INSERT OR IGNORE INTO message_schedule_state"
                "(guild_id,job_id,next_run) VALUES (?,?,?)",
                (guild_id, job["id"], job["start"]),
            )
            return conn.execute(
                "SELECT next_run,status FROM message_schedule_state "
                "WHERE guild_id=? AND job_id=?",
                (guild_id, job["id"]),
            ).fetchone()

    def finish(self, guild_id, job_id, *, status, next_run=None, message_id=None):
        with closing(self.host["db_connect"]()) as conn:
            conn.execute(
                "UPDATE message_schedule_state SET status=?,next_run=?,"
                "message_id=?,dirty=0 WHERE guild_id=? AND job_id=?",
                (status, next_run, message_id, guild_id, job_id),
            )

    async def execute(self, guild, job, now):
        from message_autofeeds import can_deliver, get_jobs
        from message_publish import publish_message

        try:
            due, status = self.state(guild.id, job)
            if status != "pending" or not due or job.get("paused"):
                return
            if datetime.fromisoformat(due).astimezone(timezone.utc) > now:
                return
            with closing(self.host["db_connect"]()) as conn:
                claimed = conn.execute(
                    "UPDATE message_schedule_state SET status='sending',dirty=0 "
                    "WHERE guild_id=? AND job_id=? AND status='pending' "
                    "AND next_run=?",
                    (guild.id, job["id"], due),
                ).rowcount
            if not claimed:
                return
        except Exception as exc:
            print(f"ANNOUNCEMENTS status=STATE_ERROR guild={guild.id} "
                  f"error={type(exc).__name__}", flush=True)
            return

        attempted = False
        sent = None
        try:
            # A deleted/edited job never sends a queued, stale payload.
            latest = next((j for j in get_jobs(self.host, guild.id)
                           if j.get("id") == job["id"]), None)
            if latest is None or latest.get("paused") or latest != job:
                self.finish(guild.id, job["id"], status="cancelled")
                return
            channel = guild.get_channel(job["channel"])
            if not isinstance(channel, discord.TextChannel):
                raise ValueError("channel_missing")
            member = await guild.fetch_member(job["author"])
            if not can_deliver(self.host, guild, job, member, channel):
                raise ValueError("permissions_revoked")
            if not guild.me:
                raise ValueError("bot_member_missing")
            attempted = True
            import production_message_locale_sync as locale_sync
            with locale_sync.suspend_tracking():
                sent = await publish_message(self.host, guild, channel, job)
            next_run = next_occurrence(job, datetime.now(timezone.utc))
            self.finish(guild.id, job["id"], status="pending" if next_run else "done",
                        next_run=next_run, message_id=sent.id)
        except Exception as exc:
            try:
                self.finish(guild.id, job["id"],
                            status="uncertain" if attempted else "error",
                            message_id=getattr(sent, "id", None))
            except Exception:
                pass
            print(f"ANNOUNCEMENTS status={'UNCERTAIN' if attempted else 'ERROR'} "
                  f"guild={guild.id} job={job['id']} "
                  f"reason={type(exc).__name__}", flush=True)

    @tasks.loop(seconds=30)
    async def worker(self):
        from message_autofeeds import get_jobs
        now = datetime.now(timezone.utc)
        for guild in self.host["bot"].guilds:
            for job in get_jobs(self.host, guild.id):
                if not (job.get("autofeed") is True
                        and (job.get("text") or job.get("embed"))
                        and job.get("start") and not job.get("paused")):
                    continue
                try:
                    await self.execute(guild, job, now)
                except Exception as exc:
                    print(f"ANNOUNCEMENTS status=WORKER_FAILED guild={guild.id} "
                          f"error={type(exc).__name__}", flush=True)
