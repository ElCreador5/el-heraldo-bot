"""Recordatorios públicos de reportes: estado durable, idiomas e historial.

No crea tablas ni altera expedientes. Las publicaciones reconocidas se editan
en Discord; no se traducen etiquetas escritas por miembros.
"""
from __future__ import annotations

import asyncio
import calendar
import json
import re
import sqlite3
from datetime import datetime, timedelta, timezone

import discord
import heraldo_i18n as i18n
from production_report_labels import report_label

RD = timezone(timedelta(hours=-4))
DEFAULTS = {
    "report_reminder_enabled": "0",
    "report_reminder_channel": "0",
    "report_reminder_frequency": "weekly",
    "report_reminder_day": "0",
    "report_reminder_hour": "12",
    "report_reminder_interval": "7d",
    "report_reminder_start": "",
}
REFERENCE_KEY = "report_reminder_active_messages"
REFERENCE_LIMIT = 100
FREQUENCIES = frozenset({"daily", "weekly", "fortnightly", "monthly", "custom"})


def reminder_settings(guild_id, getter):
    result = {key: (getter(guild_id, key) or fallback)
              for key, fallback in DEFAULTS.items()}
    # Valores antiguos corruptos no pueden provocar publicaciones arbitrarias.
    if result["report_reminder_frequency"] not in FREQUENCIES:
        result["report_reminder_frequency"] = "weekly"
    return result


def reminder_preview(guild_id, host):
    """Texto de catálogo; preservar literalmente las etiquetas personalizadas."""
    lang = host["language"](guild_id)
    lines = []
    for item in host["reactions"](guild_id):
        if item.get("action") == "warn":
            continue
        label = discord.utils.escape_markdown(report_label(item, lang))
        lines.append(i18n.translate(
            lang, "text.a4b44b483f36fa",
            p0=str(item.get("emoji") or ""), p1=label,
            p2=str(item.get("threshold", 1)),
        ))
    return (
        i18n.translate(lang, "text.5d4decf366f299")
        + ("\n".join(lines) if lines else i18n.translate(lang, "text.fafc3fe984c376"))
        + i18n.translate(lang, "text.27ab166caf064d")
    )[:1900]


def _local_anchor(value, hour):
    try:
        if len(value) > 10:
            return datetime.strptime(value, "%Y-%m-%d %H:%M").replace(tzinfo=RD)
        if value:
            return datetime.strptime(value, "%Y-%m-%d").replace(
                hour=hour, tzinfo=RD)
    except ValueError:
        return None
    return None


def _advance_month(value):
    year = value.year + int(value.month == 12)
    month = value.month % 12 + 1
    day = min(value.day, calendar.monthrange(year, month)[1])
    return value.replace(year=year, month=month, day=day)


def reminder_next_due(settings, now):
    """Próxima ejecución futura, en hora de Santo Domingo y sin catch-up masivo."""
    local = now.astimezone(RD)
    hour = max(0, min(23, int(settings.get("report_reminder_hour", "12"))))
    day = max(0, min(28, int(settings.get("report_reminder_day", "0"))))
    frequency = settings.get("report_reminder_frequency", "weekly")
    start = _local_anchor(settings.get("report_reminder_start", ""), hour)
    today = local.replace(hour=hour, minute=0, second=0, microsecond=0)

    if frequency == "custom":
        raw = settings.get("report_reminder_interval", "7d")
        match = re.fullmatch(r"(\d+)(h|d)", raw)
        seconds = int(match.group(1)) * (3600 if match.group(2) == "h" else 86400) if match else 604800
        seconds = max(86400, min(365 * 86400, seconds))
        anchor = start or today
        if anchor > local:
            return anchor.astimezone(timezone.utc)
        steps = int((local - anchor).total_seconds() // seconds) + 1
        return (anchor + timedelta(seconds=steps * seconds)).astimezone(timezone.utc)

    if frequency == "weekly":
        weekday = day % 7
        candidate = today + timedelta(days=(weekday - today.weekday()) % 7)
        if candidate <= local:
            candidate += timedelta(days=7)
    elif frequency == "fortnightly":
        # Mantener el ancla original cuando existe para no cambiar el ciclo.
        anchor = start or (today + timedelta(days=(day % 7 - today.weekday()) % 7))
        if anchor > local:
            candidate = anchor
        else:
            steps = int((local - anchor).total_seconds() // (14 * 86400)) + 1
            candidate = anchor + timedelta(days=14 * steps)
    elif frequency == "monthly":
        target = max(1, min(28, day or 1))
        candidate = today.replace(day=target)
        if candidate <= local:
            candidate = _advance_month(candidate)
    else:
        candidate = today
        if candidate <= local:
            candidate += timedelta(days=1)

    # Un inicio futuro define el primer día de la programación.
    if start and candidate < start:
        if frequency == "monthly":
            while candidate < start:
                candidate = _advance_month(candidate)
        elif frequency == "weekly":
            candidate += timedelta(days=7 * (int((start - candidate).total_seconds() // (7*86400)) + 1))
        else:
            candidate = start
    return candidate.astimezone(timezone.utc)


def reminder_signature(settings):
    return json.dumps(settings, sort_keys=True, ensure_ascii=False)


def _load_refs(guild_id, getter):
    raw = getter(guild_id, REFERENCE_KEY)
    try:
        loaded = json.loads(raw) if raw else []
    except (TypeError, ValueError):
        return []
    refs = []
    for pair in loaded[-REFERENCE_LIMIT:]:
        if not isinstance(pair, (tuple, list)) or len(pair) != 2:
            continue
        try:
            ref = int(pair[0]), int(pair[1])
        except (ValueError, TypeError):
            continue
        if min(ref) > 0 and ref not in refs:
            refs.append(ref)
    return refs


def record_publication(guild_id, channel_id, message_id, host):
    refs = _load_refs(guild_id, host["get"])
    new = (int(channel_id), int(message_id))
    refs = [ref for ref in refs if ref != new] + [new]
    host["set"](guild_id, REFERENCE_KEY, json.dumps(refs[-REFERENCE_LIMIT:]))


def _is_reminder(message):
    """Reconocer únicamente recordatorios completos redactados por el sistema."""
    source = message.content
    if not source and len(message.embeds) == 1:
        source = message.embeds[0].description or ""
    if not isinstance(source, str):
        return False
    for locale in i18n.TARGET_LOCALES:
        intro = i18n.CATALOGS[locale].messages["text.5d4decf366f299"]
        outro = i18n.CATALOGS[locale].messages["text.27ab166caf064d"]
        if source.startswith(intro) and source.endswith(outro):
            return True
    return False


def _reminder_embed(guild, host):
    embed = discord.Embed(description=reminder_preview(guild.id, host))
    return host["stamp"](embed, guild)


async def refresh_report_reminders(guild, host, *, discover=True):
    """Actualizar mensajes existentes, preservando su ID, sin republicar."""
    if guild is None or guild.me is None:
        return (0, 0)
    refs = _load_refs(guild.id, host["get"])
    known = set(refs)
    if discover:
        configured = int(reminder_settings(guild.id, host["get"])["report_reminder_channel"])
        channel = guild.get_channel(configured)
        if isinstance(channel, discord.TextChannel):
            perms = channel.permissions_for(guild.me)
            if perms.view_channel and perms.read_message_history:
                try:
                    async for candidate in channel.history(limit=500):
                        if (candidate.author.id == guild.me.id
                                and _is_reminder(candidate)):
                            reference = (channel.id, candidate.id)
                            if reference not in known:
                                known.add(reference)
                                refs.append(reference)
                except discord.HTTPException:
                    pass
    changed, failed, live = 0, 0, []
    new_embed = _reminder_embed(guild, host)
    for channel_id, message_id in refs[-REFERENCE_LIMIT:]:
        channel = guild.get_channel(channel_id)
        if not isinstance(channel, discord.TextChannel):
            failed += 1
            live.append((channel_id, message_id))
            continue
        perms = channel.permissions_for(guild.me)
        if not (perms.view_channel and perms.read_message_history):
            failed += 1
            live.append((channel_id, message_id))
            continue
        try:
            message = await channel.fetch_message(message_id)
            if message.author.id != guild.me.id or not _is_reminder(message):
                continue
            # Conservar fecha y otros datos de mensajes del sistema ajenos al aviso.
            if message.content or len(message.embeds) != 1 or (
                    message.embeds[0].description != new_embed.description):
                await message.edit(
                    content=None, embed=new_embed,
                    allowed_mentions=discord.AllowedMentions.none(),
                )
                changed += 1
            live.append((channel_id, message_id))
        except discord.NotFound:
            continue
        except (discord.Forbidden, discord.HTTPException):
            failed += 1
            live.append((channel_id, message_id))
        if (changed + failed) and (changed + failed) % 20 == 0:
            await asyncio.sleep(0.75)
    if live != _load_refs(guild.id, host["get"]):
        host["set"](guild.id, REFERENCE_KEY, json.dumps(live[-REFERENCE_LIMIT:]))
    print(f"REMINDER_LOCALE_SYNC guild={guild.id} updated={changed} failed={failed}", flush=True)
    return changed, failed


def _due_claim(guild_id, settings, host, now):
    """Un solo reclamante: persiste el próximo vencimiento ANTES de enviar."""
    signature = reminder_signature(settings)
    conn = host["connect"]()
    try:
        conn.execute("BEGIN IMMEDIATE")
        rows = conn.execute(
            "SELECT key, value FROM guild_settings WHERE guild_id=? "
            "AND key IN ('report_reminder_signature','report_reminder_next_due')",
            (guild_id,),
        ).fetchall()
        values = dict(rows)
        if values.get("report_reminder_signature") != signature:
            due = reminder_next_due(settings, now)
            claim = False
        else:
            try:
                due = datetime.fromisoformat(values["report_reminder_next_due"])
                if due.tzinfo is None:
                    raise ValueError("missing timezone")
            except (ValueError, TypeError, KeyError):
                due = reminder_next_due(settings, now)
            claim = due <= now
            if claim:
                due = reminder_next_due(settings, now)
        for key, value in (
            ("report_reminder_signature", signature),
            ("report_reminder_next_due", due.isoformat()),
        ):
            conn.execute(
                "INSERT INTO guild_settings(guild_id,key,value) VALUES (?,?,?) "
                "ON CONFLICT(guild_id,key) DO UPDATE SET value=excluded.value",
                (guild_id, key, value),
            )
        conn.commit()
        return claim
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


async def publish_due_reminders(bot, host):
    """No publica salvo cuando el administrador activó explícitamente el módulo."""
    now = datetime.now(timezone.utc)
    for guild in bot.guilds:
        try:
            settings = reminder_settings(guild.id, host["get"])
            if settings["report_reminder_enabled"] != "1":
                continue
            channel = guild.get_channel(int(settings["report_reminder_channel"]))
            me = guild.me
            if not isinstance(channel, discord.TextChannel) or me is None:
                continue
            perms = channel.permissions_for(me)
            if not (perms.view_channel and perms.send_messages and perms.embed_links):
                continue
            if not _due_claim(guild.id, settings, host, now):
                continue
            sent = await channel.send(
                embed=_reminder_embed(guild, host),
                allowed_mentions=discord.AllowedMentions.none(),
            )
            if sent is not None:
                record_publication(guild.id, channel.id, sent.id, host)
        except (sqlite3.Error, discord.HTTPException, ValueError, TypeError) as exc:
            print(f"REMINDER_SCHEDULE status=FAILED guild={guild.id} "
                  f"error={type(exc).__name__}", flush=True)
