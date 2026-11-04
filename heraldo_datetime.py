"""Reglas compartidas de entrada y presentación de fechas y horas de El Heraldo.

Las entradas aceptan 12 h (a. m./p. m., AM/PM) y 24 h; la presentación
respeta la preferencia explícita del servidor, con compatibilidad histórica.
Las fechas almacenadas conservan fecha ISO y zona horaria, sin ambigüedad.
"""
from __future__ import annotations

from datetime import datetime, time, timezone
import re
from zoneinfo import ZoneInfo

_CLOCK = re.compile(r"^(?P<hour>\d{1,2})(?::(?P<minute>\d{2}))?\s*(?P<ampm>AM|PM)?$", re.I)
_MERIDIEM = re.compile(r"(?i)(?<![a-z])([ap])\s*\.?\s*m\.?(?![a-z])")
_DATE_CLOCK = re.compile(r"^(?P<date>\d{4}-\d{1,2}-\d{1,2}|\d{1,2}/\d{1,2}/\d{4})[ T]+(?P<clock>.+)$")


def clock_style(date_mode: str = "discord", time_mode: str | None = None) -> str:
    """Conserva el estilo histórico cuando aún no existe preferencia horaria."""
    if time_mode in ("12h", "24h"):
        return time_mode
    return "12h" if date_mode == "mdy12" else "24h"


def parse_clock(value: str) -> time:
    """Acepta 18:00, 6:00 PM, 6 p. m., 12:00 a. m. y equivalentes."""
    cleaned = _MERIDIEM.sub(lambda match: match.group(1).upper() + "M", str(value).strip())
    match = _CLOCK.fullmatch(cleaned)
    if match is None or (match.group("minute") is None and match.group("ampm") is None):
        raise ValueError("invalid_clock")
    hour = int(match.group("hour"))
    minute = int(match.group("minute") or "0")
    meridiem = match.group("ampm")
    if minute > 59:
        raise ValueError("invalid_clock")
    if meridiem:
        if not 1 <= hour <= 12:
            raise ValueError("invalid_clock")
        hour = (hour % 12) + (12 if meridiem.upper() == "PM" else 0)
    elif not 0 <= hour <= 23:
        raise ValueError("invalid_clock")
    return time(hour, minute)


def format_clock(value: time | datetime, date_mode: str = "discord",
                 time_mode: str | None = None) -> str:
    if clock_style(date_mode, time_mode) == "12h":
        return value.strftime("%I:%M %p").lstrip("0")
    return value.strftime("%H:%M")


def date_pattern(date_mode: str = "discord", locale: str = "es-419") -> str:
    if date_mode == "iso":
        return "%Y-%m-%d"
    if date_mode == "mdy12" or (date_mode == "discord" and locale == "en-US"):
        return "%m/%d/%Y"
    return "%d/%m/%Y"


def format_date_time(value: datetime, *, date_mode: str = "discord",
                     time_mode: str | None = None, locale: str = "es-419",
                     zone: str = "America/Santo_Domingo") -> str:
    moment = value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)
    local = moment.astimezone(ZoneInfo(zone))
    return local.strftime(date_pattern(date_mode, locale)) + " " + format_clock(local, date_mode, time_mode)


def parse_date_time(value: str, *, date_mode: str = "discord",
                    locale: str = "es-419", zone: str = "America/Santo_Domingo") -> datetime:
    """Devuelve UTC: interpreta tanto entradas de 12 h como de 24 h."""
    match = _DATE_CLOCK.fullmatch(value.strip())
    if not match:
        raise ValueError("invalid_datetime")
    raw_date = match.group("date")
    pattern = "%Y-%m-%d" if "-" in raw_date else date_pattern(date_mode, locale)
    try:
        day = datetime.strptime(raw_date, pattern).date()
        clock = parse_clock(match.group("clock"))
    except ValueError as exc:
        raise ValueError("invalid_datetime") from exc
    local_naive = datetime.combine(day, clock)
    tz = ZoneInfo(zone)
    local = local_naive.replace(tzinfo=tz)
    if local.astimezone(timezone.utc).astimezone(tz).replace(tzinfo=None) != local_naive:
        raise ValueError("nonexistent_datetime")
    if local.utcoffset() != local_naive.replace(tzinfo=tz, fold=1).utcoffset():
        raise ValueError("ambiguous_datetime")
    return local.astimezone(timezone.utc)
