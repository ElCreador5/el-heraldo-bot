"""Interpretación segura de fechas y horas para el panel /purge.

Las fechas siguen la configuración visible de /formato_fecha. El formato
Discord es local al cliente al mostrarse; para escribir se acepta el orden
numérico del idioma del servidor, o ISO 8601 sin ambigüedad.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
import re
from zoneinfo import ZoneInfo


class PurgePeriodError(ValueError):
    """El intervalo no es válido o mezcla horas y fechas ambiguas."""


@dataclass(frozen=True)
class PurgePeriod:
    # Los límites usados por Discord y por la revalidación son EXCLUSIVOS.
    after: datetime | None
    before: datetime | None
    display_from: datetime | None
    display_to: datetime | None


_DATE_AND_TIME = re.compile(
    r"^(?P<date>\d{4}-\d{1,2}-\d{1,2}|\d{1,2}/\d{1,2}/\d{4})(?:[ T]+(?P<clock>.+))?$"
)
_TIME = re.compile(r"^(?P<hour>\d{1,2})(?::(?P<minute>\d{2}))?\s*(?P<ampm>AM|PM)?$", re.I)
_MERIDIEM = re.compile(r"(?i)(?<![a-z])([ap])\s*\.?\s*m\.?(?![a-z])")


def _parse_clock(raw: str) -> time:
    cleaned = _MERIDIEM.sub(lambda match: match.group(1).upper() + "M", raw.strip())
    match = _TIME.fullmatch(cleaned)
    if match is None or (match.group("minute") is None and match.group("ampm") is None):
        raise PurgePeriodError("clock")
    hour = int(match.group("hour"))
    minute = int(match.group("minute") or "0")
    meridiem = match.group("ampm")
    if minute > 59:
        raise PurgePeriodError("clock")
    if meridiem:
        if not 1 <= hour <= 12:
            raise PurgePeriodError("clock")
        hour = (hour % 12) + (12 if meridiem.upper() == "PM" else 0)
    elif hour > 23:
        raise PurgePeriodError("clock")
    return time(hour, minute)


def _parse_date(raw: str, mode: str, locale: str) -> date:
    if "-" in raw:
        pattern = "%Y-%m-%d"
    elif mode == "mdy12" or (mode == "discord" and locale == "en-US"):
        pattern = "%m/%d/%Y"
    else:
        pattern = "%d/%m/%Y"
    try:
        return datetime.strptime(raw, pattern).date()
    except ValueError as exc:
        raise PurgePeriodError("date") from exc


def _boundary(raw: str, mode: str, locale: str, today: date, tz: ZoneInfo):
    if not raw.strip():
        return None, None
    text = raw.strip()
    match = _DATE_AND_TIME.fullmatch(text)
    if match:
        day = _parse_date(match.group("date"), mode, locale)
        if match.group("clock"):
            return datetime.combine(day, _parse_clock(match.group("clock")), tz), "datetime"
        return datetime.combine(day, time.min, tz), "date"
    return datetime.combine(today, _parse_clock(text), tz), "time"


def parse_purge_period(
    raw_from: str,
    raw_to: str,
    *,
    mode: str = "discord",
    locale: str = "es-419",
    now: datetime | None = None,
    tz_name: str = "America/Santo_Domingo",
) -> PurgePeriod:
    """Interpreta fecha, hora de hoy, o fecha+hora en los dos campos.

    - Solo una fecha en Desde: desde el comienzo de ese día en adelante.
    - Solo una fecha en Hasta: hasta finalizar ese día.
    - Solo horas: exige Desde y Hasta, ambas para el día actual.
    - Las fechas con horas pueden abarcar días diferentes.
    - Un rango inverso o mezcla de hora sola y fecha se rechaza.
    """
    tz = ZoneInfo(tz_name)
    instant = now or datetime.now(timezone.utc)
    if instant.tzinfo is None:
        raise ValueError("naive_now")
    today = instant.astimezone(tz).date()
    start, start_kind = _boundary(raw_from, mode, locale, today, tz)
    end, end_kind = _boundary(raw_to, mode, locale, today, tz)

    if start_kind == "time" or end_kind == "time":
        if start_kind != "time" or end_kind != "time":
            raise PurgePeriodError("time_pair")
    # Una fecha combinada con una hora sin fecha es ambigua.
    if end is not None and end_kind == "date":
        try:
            exclusive_end = end + timedelta(days=1)
        except OverflowError as exc:
            raise PurgePeriodError("date") from exc
        display_end = exclusive_end - timedelta(microseconds=1)
    else:
        exclusive_end = end
        display_end = end

    if start is not None:
        try:
            exclusive_start = start - timedelta(microseconds=1)
        except OverflowError as exc:
            raise PurgePeriodError("date") from exc
    else:
        exclusive_start = None

    if start is not None and exclusive_end is not None and start >= exclusive_end:
        raise PurgePeriodError("order")

    return PurgePeriod(exclusive_start, exclusive_end, start, display_end)
