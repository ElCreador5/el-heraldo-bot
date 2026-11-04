"""Actualiza mensajes institucionales al cambiar el idioma de un servidor.

Nunca traduce texto arbitrario ni usa traducción automática: solo identifica
fragmentos completos provenientes de los catálogos de El Heraldo. Los mensajes
personalizados quedan fuera del registro y de la conciliación retroactiva.
Sin tablas nuevas: el registro limitado utiliza guild_settings existente para
respetar la verificación de la SQLite restaurada en Enzonic.
"""
from __future__ import annotations

import asyncio
from collections import defaultdict
from contextlib import contextmanager
from contextvars import ContextVar
from functools import lru_cache
import re
from string import Formatter

import heraldo_i18n as i18n

_PREFIX = "i18npost."
_suspended = ContextVar("heraldo_locale_tracking_suspended", default=False)


@contextmanager
def suspend_tracking():
    """Usar para publicaciones provenientes de formularios y constructores."""
    token = _suspended.set(True)
    try:
        yield
    finally:
        _suspended.reset(token)


def is_suspended():
    return _suspended.get()


@lru_cache(maxsize=3)
def _templates(locale):
    """Índice por prefijo literal; nunca intenta adivinar el idioma del usuario."""
    by_prefix = defaultdict(list)
    fmt = Formatter()
    for key, template in i18n.CATALOGS[locale].messages.items():
        try:
            parts = list(fmt.parse(template))
        except ValueError:
            continue
        if not parts:
            continue
        leading = parts[0][0]
        # Excluir textos genéricos breves y plantillas que comienzan con datos.
        if len(leading) < 7 or sum(len(part[0]) for part in parts) < 7:
            continue
        pattern, fields = [], set()
        valid = True
        for literal, field, format_spec, conversion in parts:
            pattern.append(re.escape(literal))
            if field is not None:
                if not re.fullmatch(r"[a-zA-Z_][a-zA-Z_0-9]*", field) or format_spec or conversion:
                    valid = False
                    break
                if field in fields:
                    pattern.append("(?P=" + field + ")")
                else:
                    fields.add(field)
                    pattern.append("(?P<" + field + ">.*?)")
        if valid:
            try:
                regex = re.compile("".join(pattern) + r"\Z", re.DOTALL)
            except re.error:
                continue
            by_prefix[leading[:7]].append((key, regex))
    return dict(by_prefix)


def _translate_exact(value, original, target):
    if not isinstance(value, str) or len(value) < 7:
        return value, False
    group = _templates(original).get(value[:7], ())
    for key, matcher in group:
        matched = matcher.fullmatch(value)
        if matched is None:
            continue
        template = i18n.CATALOGS[target].messages.get(key)
        if template is None:
            continue
        try:
            translated = template.format(**matched.groupdict())
        except (KeyError, ValueError):
            continue
        if translated != value:
            return translated, True
        return value, False
    return value, False


def localize_text(value, original, target):
    """Solo campos completos o líneas completas; lo demás queda literalmente igual.

    Una razón, comentario, nombre, texto de formulario o enlace insertado dentro
    de una variable permanece idéntico. Nunca se traduce por semejanza.
    """
    if original not in i18n.SUPPORTED_LOCALES or target not in i18n.SUPPORTED_LOCALES:
        return value, False
    if original == target or not isinstance(value, str) or not value:
        return value, False
    translated, changed = _translate_exact(value, original, target)
    if changed:
        return translated, True
    if "\n" not in value:
        return value, False
    output = []
    changed_any = False
    for line in value.splitlines(keepends=True):
        body = line.rstrip("\r\n")
        suffix = line[len(body):]
        translated, changed = _translate_exact(body, original, target)
        output.append(translated + suffix)
        changed_any |= changed
    return "".join(output), changed_any


def _payload_has_system_text(content, embeds, locale):
    """Verificar procedencia localizable antes de guardar una publicación."""
    candidates = [content]
    for embed in embeds:
        candidates.extend([getattr(embed, "title", None),
                           getattr(embed, "description", None)])
        for field in getattr(embed, "fields", ()):
            candidates.extend([field.name, field.value])
        author = getattr(embed, "author", None)
        if author:
            candidates.append(getattr(author, "name", None))
    # Verificar claves exactas en el mismo idioma; no cuenta el footer del bot.
    for value in candidates:
        if not isinstance(value, str):
            continue
        if _translate_exact(value, locale, _other_locale(locale))[1]:
            return True
        if any(_translate_exact(line, locale, _other_locale(locale))[1]
               for line in value.splitlines()):
            return True
    return False


def _other_locale(locale):
    return "en-US" if locale != "en-US" else "pt-BR"


def note_sent(message, guild, content, kwargs, db_connect):
    """Invocado después de confirmar un envío; nunca bloquea el envío original."""
    if is_suspended() or guild is None or message is None:
        return
    if getattr(getattr(message, "channel", None), "guild", None) is None:
        return  # DM y respuestas efímeras no son publicaciones públicas indexables.
    if getattr(message.guild, "id", None) != getattr(guild, "id", None):
        return
    import message_payload
    if isinstance(kwargs.get("embeds"), message_payload.TemplateEmbeds):
        return  # Anuncios, mensajes de formulario y plantillas personalizadas.
    embeds = ([kwargs["embed"]] if kwargs.get("embed") is not None else
              list(kwargs.get("embeds") or ()))
    locale = i18n._locale_resolver(guild.id)
    if not _payload_has_system_text(content, embeds, locale):
        return
    key = f"{_PREFIX}{message.channel.id}.{message.id}"
    conn = db_connect()
    try:
        conn.execute("INSERT INTO guild_settings(guild_id,key,value) VALUES (?,?,?) "
                     "ON CONFLICT(guild_id,key) DO UPDATE SET value=excluded.value",
                     (guild.id, key, locale))
    finally:
        conn.close()


def _tracked(guild_id, db_connect):
    conn = db_connect()
    try:
        rows = conn.execute(
            "SELECT key,value FROM guild_settings WHERE guild_id=? AND key LIKE 'i18npost.%'",
            (guild_id,),
        ).fetchall()
    finally:
        conn.close()
    result = []
    for key, locale in rows:
        match = re.fullmatch(r"i18npost\.(\d+)\.(\d+)", key)
        if match and locale in i18n.SUPPORTED_LOCALES:
            result.append((int(match[1]), int(match[2]), locale))
    return result


def _set_tracked(guild_id, channel_id, message_id, locale, db_connect):
    conn = db_connect()
    try:
        conn.execute(
            "INSERT INTO guild_settings(guild_id,key,value) VALUES (?,?,?) "
            "ON CONFLICT(guild_id,key) DO UPDATE SET value=excluded.value",
            (guild_id, f"{_PREFIX}{channel_id}.{message_id}", locale),
        )
    finally:
        conn.close()


def _forget(guild_id, channel_id, message_id, db_connect):
    conn = db_connect()
    try:
        conn.execute("DELETE FROM guild_settings WHERE guild_id=? AND key=?",
                     (guild_id, f"{_PREFIX}{channel_id}.{message_id}"))
    finally:
        conn.close()


def _personal_publication_ids(guild_id, db_connect):
    """Excluir también publicaciones personales antiguas, sin mirar su texto."""
    conn = db_connect()
    try:
        exists = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='personal_publications'"
        ).fetchone()
        if not exists:
            return set()
        return {(int(c), int(m)) for c, m in conn.execute(
            "SELECT channel_id,message_id FROM personal_publications WHERE guild_id=?",
            (guild_id,),
        )}
    finally:
        conn.close()


def _message_patch(message, source_locale, target_locale):
    """Conservar embeds, imágenes, colores, metadatos y variables."""
    updates = {}
    content, changed = localize_text(message.content, source_locale, target_locale)
    if changed:
        updates["content"] = content
    embeds = []
    embeds_changed = False
    for old in message.embeds:
        embed = old.copy()
        title, updated = localize_text(embed.title, source_locale, target_locale)
        if updated:
            embed.title = title
        embeds_changed |= updated
        desc, updated = localize_text(embed.description, source_locale, target_locale)
        if updated:
            embed.description = desc
        embeds_changed |= updated
        for idx, field in enumerate(embed.fields):
            name, changed_name = localize_text(field.name, source_locale, target_locale)
            value, changed_value = localize_text(field.value, source_locale, target_locale)
            if changed_name or changed_value:
                embed.set_field_at(idx, name=name, value=value, inline=field.inline)
                embeds_changed = True
        if embed.author and embed.author.name:
            author_name, updated = localize_text(embed.author.name, source_locale, target_locale)
            if updated:
                embed.set_author(name=author_name, url=embed.author.url or None,
                                 icon_url=embed.author.icon_url or None)
                embeds_changed = True
        # El footer identifica al bot/servidor y no se reescribe.
        embeds.append(embed)
    if embeds_changed:
        updates["embeds"] = embeds
    return updates


async def synchronize(guild, old_locale, new_locale, db_connect, *,
                      history_limit=300, max_channels=40):
    """Conciliación posterior al guardado; errores aislados por mensaje.

    Primer cambio: examinar un historial acotado y reconocer exclusivamente
    textos de catálogo. Cambios siguientes: revisar también los IDs registrados.
    No altera publicaciones personales, anuncios ni texto libre.
    """
    import discord

    if guild is None or old_locale == new_locale:
        return {"updated": 0, "skipped": 0, "failed": 0}
    counts = {"updated": 0, "skipped": 0, "failed": 0}
    personal = _personal_publication_ids(guild.id, db_connect)
    visited = set()

    async def check(message, source_locale):
        # Un segundo cambio de idioma invalida el trabajo anterior.
        if i18n._locale_resolver(guild.id) != new_locale:
            return
        key = (message.channel.id, message.id)
        if key in visited:
            return
        visited.add(key)
        if key in personal or message.author.id != guild.me.id:
            counts["skipped"] += 1
            return
        patch = _message_patch(message, source_locale, new_locale)
        if not patch:
            counts["skipped"] += 1
            return
        try:
            await message.edit(**patch, allowed_mentions=discord.AllowedMentions.none())
        except (discord.HTTPException, ValueError):
            counts["failed"] += 1
            return
        _set_tracked(guild.id, key[0], key[1], new_locale, db_connect)
        counts["updated"] += 1
        if counts["updated"] % 15 == 0:
            await asyncio.sleep(0.75)

    for channel_id, message_id, locale in _tracked(guild.id, db_connect):
        if locale == new_locale:
            continue
        channel = guild.get_channel_or_thread(channel_id)
        if channel is None:
            counts["skipped"] += 1
            continue
        try:
            message = await channel.fetch_message(message_id)
        except discord.NotFound:
            _forget(guild.id, channel_id, message_id, db_connect)
            continue
        except discord.HTTPException:
            counts["failed"] += 1
            continue
        await check(message, locale)

    # Solo se inspeccionan mensajes visibles del bot, en límites explícitos.
    # No existe traducción fiable de mensajes anteriores sin trazas del origen:
    # si no coinciden exactamente con el catálogo, no se modifican.
    if guild.me is not None:
        for channel in guild.text_channels[:max_channels]:
            perms = channel.permissions_for(guild.me)
            if not (perms.view_channel and perms.read_message_history):
                continue
            try:
                async for message in channel.history(limit=history_limit):
                    if message.author.id == guild.me.id:
                        await check(message, old_locale)
            except discord.HTTPException:
                counts["failed"] += 1

    print("LANGUAGE_HISTORY_SYNC "
          f"guild={guild.id} locale={new_locale} "
          f"updated={counts['updated']} skipped={counts['skipped']} failed={counts['failed']}",
          flush=True)
    return counts
