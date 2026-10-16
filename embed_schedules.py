"""Persistencia y cálculo de publicaciones programadas de embeds (opt-in)."""
import calendar
import json
import re
from datetime import datetime, timedelta, timezone

RD = timezone(timedelta(hours=-4))
MODES = {"once", "interval", "daily", "weekly", "monthly", "messages"}
UNITS = {"m": 60, "h": 3600, "d": 86400}

def initialize(conn):
    conn.execute("""CREATE TABLE IF NOT EXISTS scheduled_embeds (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        guild_id INTEGER NOT NULL, embed_name TEXT NOT NULL, channel_id INTEGER NOT NULL,
        mode TEXT NOT NULL, config TEXT NOT NULL, enabled INTEGER NOT NULL DEFAULT 0,
        next_due TEXT, message_count INTEGER NOT NULL DEFAULT 0,
        created_at TEXT NOT NULL, updated_at TEXT NOT NULL)""")
    conn.execute("CREATE INDEX IF NOT EXISTS scheduled_embeds_due ON scheduled_embeds(enabled, next_due)")
    conn.commit()

def interval_seconds(value, is_test=False):
    m = re.fullmatch(r"([1-9][0-9]{0,7})([smhd])", value.strip().lower())
    if not m:
        raise ValueError("Use un intervalo como 2m, 1h o 14d.")
    unit = m.group(2)
    if unit == "s" and not is_test:
        raise ValueError("Los segundos solo están permitidos en Test.")
    sec = int(m.group(1)) * (1 if unit == "s" else UNITS[unit])
    if sec < (10 if is_test else 3600) or sec > 365 * 86400:
        raise ValueError("Intervalo fuera del rango permitido.")
    return sec

def validate(mode, config, is_test=False):
    if mode not in MODES:
        raise ValueError("Tipo de programación no admitido.")
    if mode == "once":
        datetime.fromisoformat(config["when"]).astimezone(RD)
    elif mode == "interval":
        interval_seconds(config["interval"], is_test)
    elif mode in {"daily", "weekly", "monthly"}:
        hh, mm = map(int, config["time"].split(":"))
        if not (0 <= hh <= 23 and 0 <= mm <= 59):
            raise ValueError("Hora inválida.")
        if mode == "weekly" and not (set(config["days"]) <= set(range(7)) and config["days"]):
            raise ValueError("Seleccione días de la semana.")
        if mode == "monthly" and not (set(config["days"]) <= set(range(1,32)) and config["days"]):
            raise ValueError("Seleccione días del mes.")
    elif mode == "messages":
        if not 10 <= int(config["count"]) <= 100000:
            raise ValueError("El contador debe estar entre 10 y 100000 mensajes.")

def next_due(mode, cfg, now, is_test=False):
    validate(mode, cfg, is_test)
    local = now.astimezone(RD)
    if mode == "messages":
        return None
    if mode == "once":
        when = datetime.fromisoformat(cfg["when"])
        if when.tzinfo is None:
            when = when.replace(tzinfo=RD)
        return when.astimezone(timezone.utc) if when > now else None
    if mode == "interval":
        secs = interval_seconds(cfg["interval"], is_test)
        # Anchor remains stable across deployments and missed intervals.
        anchor = datetime.fromisoformat(cfg["anchor"])
        if anchor.tzinfo is None:
            anchor = anchor.replace(tzinfo=timezone.utc)
        steps = max(0, int((now - anchor).total_seconds() // secs) + 1)
        return (anchor + timedelta(seconds=steps * secs)).astimezone(timezone.utc)
    hh, mm = map(int, cfg["time"].split(":"))
    candidate = local.replace(hour=hh, minute=mm, second=0, microsecond=0)
    for offset in range(0, 370):
        day = candidate + timedelta(days=offset)
        if day <= local:
            continue
        if mode == "daily" or (mode == "weekly" and day.weekday() in cfg["days"]) or (
            mode == "monthly" and day.day in cfg["days"]):
            return day.astimezone(timezone.utc)
    raise ValueError("No se encontró próxima fecha.")

def claim_due(conn, now, is_test=False):
    """Claim before send. Skipped messages aren't replayed after restart."""
    initialize(conn)
    conn.execute("BEGIN IMMEDIATE")
    rows = conn.execute("SELECT id,guild_id,embed_name,channel_id,mode,config FROM scheduled_embeds WHERE enabled=1 AND next_due IS NOT NULL AND next_due<=?", (now.isoformat(),)).fetchall()
    claims = []
    for row in rows:
        ident, gid, name, cid, mode, raw = row
        config = json.loads(raw)
        try:
            due = next_due(mode, config, now, is_test)
        except (ValueError, KeyError, TypeError):
            due = None
        conn.execute("UPDATE scheduled_embeds SET next_due=?,enabled=? WHERE id=?", (due.isoformat() if due else None, 1 if due else 0, ident))
        claims.append((ident, gid, name, cid))
    conn.commit()
    return claims

def advance_message(conn, guild_id, channel_id):
    """Count real user messages. Single process + SQLite transaction avoids duplicate triggers."""
    initialize(conn)
    conn.execute("BEGIN IMMEDIATE")
    rows = conn.execute("SELECT id,config,message_count,embed_name FROM scheduled_embeds WHERE guild_id=? AND channel_id=? AND mode='messages' AND enabled=1", (guild_id,channel_id)).fetchall()
    ready = []
    for ident, raw, count, name in rows:
        goal = int(json.loads(raw)["count"])
        count += 1
        if count >= goal:
            ready.append((ident,name))
            count = 0
        conn.execute("UPDATE scheduled_embeds SET message_count=? WHERE id=?", (count,ident))
    conn.commit()
    return ready
