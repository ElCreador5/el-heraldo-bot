"""Canal privado y tarjeta de referencias para observaciones de Modo Custodio.

No se ejecuta automáticamente: crear el canal exige confirmación administrativa.
No contiene procesador de mensajes, sanciones, lectura de historiales ni copias
de material de canales restringidos. Se conservan metadatos mínimos solamente.
"""
from __future__ import annotations
from heraldo_i18n import text as _t, guild_context as _i18n_context, use_guild as _i18n_guild, variants as _i18n_variants
from heraldo_i18n import join_text as _i18n_join

import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
import re
from typing import Callable

import discord

CHANNEL_NAME = "reportes📢"
CHANNEL_TOPIC = "El Heraldo · Modo Custodio · Reportes privados"
SETTING_KEY = "custodio_reports_channel_id"

_channel_creation_locks: dict[int, asyncio.Lock] = {}


class ReportChannelError(RuntimeError):
    """El canal no pudo crearse o comprobarse de forma segura."""


def _has_staff_role_permissions(role: discord.Role) -> bool:
    perms = role.permissions
    return bool(
        perms.administrator or perms.manage_guild
        or perms.manage_messages or perms.moderate_members
    )


@_i18n_context
def _get_safe_existing(guild: discord.Guild, channel_id: int) -> discord.TextChannel:
    channel = guild.get_channel(channel_id)
    if not isinstance(channel, discord.TextChannel):
        raise ReportChannelError(_t('text.6706892064e584'))
    if channel.topic != CHANNEL_TOPIC or not private_report_channel(channel):
        raise ReportChannelError(_t('text.b49cbe741692d2'))
    me = guild.me
    if me is None:
        raise ReportChannelError(_t('text.1f8a4320668846'))
    permissions = channel.permissions_for(me)
    if not (permissions.view_channel and permissions.send_messages and
            permissions.embed_links and permissions.read_message_history):
        raise ReportChannelError(_t('text.33bf93ed9e1134'))
    return channel


@_i18n_context
def private_report_channel(channel: discord.TextChannel) -> bool:
    """Se exige denegación explícita del acceso de @everyone."""
    everyone = channel.guild.default_role
    overwrite = channel.overwrites_for(everyone)
    if overwrite.view_channel is not False:
        return False
    # En Discord, Administrator elude restricciones de canal; solo roles de
    # moderación aprobados por sus permisos pueden conservar acceso.
    for role in channel.guild.roles:
        if role.id == everyone.id or _has_staff_role_permissions(role):
            continue
        if channel.overwrites_for(role).view_channel is True:
            return False
    # También se prohíben excepciones directas a miembros ordinarios.
    for target, overwrite in channel.overwrites.items():
        if isinstance(target, discord.Member) and overwrite.view_channel is True:
            if target.id not in {channel.guild.owner_id, getattr(channel.guild.me, "id", None)}:
                return False
    return True


def compatible_evidence_access(source, destination):
    """Una copia no amplía el acceso ni rebaja la restricción de edad del origen."""
    if source.guild.id != destination.guild.id:
        return False
    if source.is_nsfw() and not destination.is_nsfw():
        return False
    guild = source.guild
    if source.permissions_for(guild.default_role).view_channel:
        return True
    # Si el origen restringe a un miembro individual, no copiar automáticamente.
    if any(isinstance(target, discord.Member) and overwrite.view_channel is False
           for target, overwrite in source.overwrites.items()):
        return False
    for role in guild.roles:
        if destination.permissions_for(role).view_channel and not source.permissions_for(role).view_channel:
            return False
    for target, overwrite in destination.overwrites.items():
        if isinstance(target, discord.Member) and overwrite.view_channel is True:
            if not source.permissions_for(target).view_channel:
                return False
    return True


@_i18n_context
async def create_private_report_channel(
    guild: discord.Guild,
    get_setting: Callable[[int, str], str | None],
    set_setting: Callable[[int, str, str], None],
) -> tuple[discord.TextChannel, bool]:
    """Solo llamar desde botón Confirmar tras revalidar permisos del administrador.

    Idempotente dentro del proceso y recuperable tras caída entre Discord y
    SQLite gracias al marcador fijo en el topic. No reemplaza canales ajenos.
    """
    if guild is None or guild.me is None:
        raise ReportChannelError(_t('text.40b79b84a5c754'))
    lock = _channel_creation_locks.setdefault(guild.id, asyncio.Lock())
    async with lock:
        raw = get_setting(guild.id, SETTING_KEY)
        if raw:
            if not raw.isdecimal():
                raise ReportChannelError(_t('text.9d3604ce8d7e62'))
            return _get_safe_existing(guild, int(raw)), False

        # Recuperar únicamente el canal creado previamente por Custodio.
        for candidate in guild.text_channels:
            if candidate.topic == CHANNEL_TOPIC:
                channel = _get_safe_existing(guild, candidate.id)
                set_setting(guild.id, SETTING_KEY, str(channel.id))
                return channel, False

        perms = guild.me.guild_permissions
        if not (perms.manage_channels and perms.view_channel and
                perms.send_messages and perms.embed_links and
                perms.read_message_history):
            raise ReportChannelError(
                _t('text.6e7f7239c7d7d5')
            )

        everyone = guild.default_role
        if everyone is None:
            raise ReportChannelError(_t('text.ee730d9608b630'))
        overwrites = {
            everyone: discord.PermissionOverwrite(view_channel=False),
            guild.me: discord.PermissionOverwrite(
                view_channel=True, send_messages=True, read_message_history=True,
                embed_links=True, attach_files=False,
            ),
        }
        for role in guild.roles:
            if role.id != everyone.id and _has_staff_role_permissions(role):
                overwrites[role] = discord.PermissionOverwrite(
                    view_channel=True, read_message_history=True,
                    send_messages=True, embed_links=True,
                )
        if len(overwrites) > 90:
            raise ReportChannelError(_t('text.cf0f4a1430a6ae'))
        try:
            channel = await guild.create_text_channel(
                CHANNEL_NAME,
                topic=CHANNEL_TOPIC,
                overwrites=overwrites,
                nsfw=False,
                reason=_t('text.048c0bc061e066'),
            )
        except (discord.Forbidden, discord.HTTPException) as exc:
            raise ReportChannelError(_t('text.f9fd154c084353')) from exc

        # Fail closed: nunca vincular un canal que sea público.
        _get_safe_existing(guild, channel.id)
        set_setting(guild.id, SETTING_KEY, str(channel.id))
        return channel, True


@dataclass(frozen=True)
class ObservationEvidence:
    guild_id: int
    channel_id: int
    message_id: int
    rule_numbers: tuple[int, ...]
    rules_revision: str
    category: str
    classification: str
    timestamp: datetime
    content_sha256: str | None = None

    @_i18n_context
    def __post_init__(self) -> None:
        if any(type(n) is not int or n <= 0 for n in (
            self.guild_id, self.channel_id, self.message_id
        )):
            raise ValueError("invalid_message_reference")
        if not self.rule_numbers or any(type(n) is not int or n <= 0 for n in self.rule_numbers):
            raise ValueError("invalid_rule_reference")
        if not re.fullmatch(r"[0-9a-f]{64}", self.rules_revision):
            raise ValueError("invalid_rules_revision")
        if self.content_sha256 is not None and not re.fullmatch(r"[0-9a-f]{64}", self.content_sha256):
            raise ValueError("invalid_evidence_hash")
        if self.classification not in {"sfw", "age_restricted", "unknown"}:
            raise ValueError("invalid_classification")
        if self.category not in {"suspected", "ambiguous"}:
            raise ValueError("invalid_category")
        if self.timestamp.tzinfo is None:
            raise ValueError("timestamp_requires_timezone")


def observation_embed(evidence: ObservationEvidence) -> discord.Embed:
    """Referencia y huella sin contenido explícito ni identificadores privados extra."""
    link = (
        f"https://discord.com/channels/{evidence.guild_id}/"
        f"{evidence.channel_id}/{evidence.message_id}"
    )
    embed = discord.Embed(
        title=_t('text.5642273dfbf438'),
        description=_t('text.56eab2d5e86cdd'),
        color=discord.Color.orange(),
        timestamp=evidence.timestamp.astimezone(timezone.utc),
    )
    embed.add_field(name=_t('text.98e5acddb6c46a'), value={
        "suspected": _t('text.1611d0206d0da4'), "ambiguous": _t('text.83820656fe4267')
    }[evidence.category], inline=True)
    embed.add_field(name=_t('text.db8661d1e95a31'), value=_i18n_join(", ", map(str, sorted(set(evidence.rule_numbers))))[:100], inline=True)
    embed.add_field(name=_t('text.dbb654a486a5fc'), value={
        "sfw": _t('text.4126ef96750e46'), "age_restricted": _t('text.d7d3d194cdd9e0'),
        "unknown": _t('text.00c2263a2c37e6'),
    }[evidence.classification], inline=False)
    embed.add_field(
        name=_t('text.b5b41b06d9c08e'),
        value=_t('text.6c951aad14615d', p0=f'{link}', p1=f'{evidence.message_id}', p2=f'{evidence.rules_revision[:12]}', p3=f"{(evidence.content_sha256[:16] if evidence.content_sha256 else _t('text.a759af6e809102'))}"),
        inline=False,
    )
    embed.set_footer(text=_t('text.34745d9f1f2e4b'))
    return embed


def custodio_literal_report(
    *, actor: str, guild_name: str, channel_name: str,
    occurred_at: datetime, verbatim: str, rule_text: str, rule_number: int,
    footer: str, icon_url: str | None = None,
    original_url: str | None = None, original_exists: bool = False,
    observed_description: str | None = None, conduct: str | None = None,
) -> list[discord.Embed]:
    """Adaptador NH sin persistencia ni envío: solo crea embeds para revisión.

    Un flujo de eventos futuro debe comprobar permisos, regla, privacidad y
    existencia del mensaje antes de utilizar este adaptador.
    """
    from heraldo_evidence import LiteralEvidence, make_evidence_embeds
    return make_evidence_embeds(
        LiteralEvidence(
            actor=actor, guild=guild_name, channel=channel_name,
            occurred_at=occurred_at, verbatim=verbatim or observed_description,
            rule_quote=rule_text, rule_number=rule_number,
            original_url=original_url, original_exists=original_exists,
            conduct=conduct or _t('text.3d57a85390b5c0'),
            outcome=_t('text.fb57b92cfc0723'),
            verbatim_is_description=not bool(verbatim),
        ),
        footer=footer, icon_url=icon_url,
    )


# Dedupe temporal por mensaje; evita guardar copias en SQLite/Supabase.
_published_evidence: dict[tuple[int, int], int] = {}
_publish_locks: dict[int, asyncio.Lock] = {}
MAX_RECENT_EVIDENCE = 2048


def delivery_state(db_path, key):
    import sqlite3
    from contextlib import closing
    with closing(sqlite3.connect(db_path, timeout=2)) as db:
        try:
            row = db.execute("SELECT status FROM evidence_archive_v1 WHERE evidence_key=?", (key,)).fetchone()
            return row[0] if row else None
        except sqlite3.OperationalError:
            return None


@_i18n_context
async def publish_literal_observation(
    *, guild: discord.Guild, report_channel_id: int,
    source_message: discord.Message, rule_text: str, rule_number: int,
    footer: str, icon_url: str | None = None,
    observed_description: str | None = None, conduct: str | None = None,
    rules_revision: str | None = None,
    review_view: discord.ui.View | None = None,
) -> discord.Message:
    """Publicar una copia literal autorizada exclusivamente en reportes privado.

    Debe llamarse solo después de confirmar una regla del servidor aprobada,
    una observación revisable y las exenciones. No sanciona, no crea canales,
    no archiva localmente y no consulta IA.
    """
    if source_message.guild is None or source_message.guild.id != guild.id:
        raise ReportChannelError(_t('text.ab2a51e5e3cf6e'))
    if source_message.author.bot or source_message.webhook_id:
        raise ReportChannelError(_t('text.bbc165288f8c22'))
    if not isinstance(source_message.channel, discord.TextChannel):
        raise ReportChannelError(_t('text.745b4b3080cb03'))
    if not isinstance(rule_text, str) or not rule_text.strip() or rule_number <= 0:
        raise ReportChannelError(_t('text.7cfb6c510e4124'))
    if not isinstance(source_message.content, str) or not (source_message.content or observed_description):
        raise ReportChannelError(_t('text.a951b5fa2dbce1'))
    lock = _publish_locks.setdefault(guild.id, asyncio.Lock())
    async with lock:
        channel = _get_safe_existing(guild, report_channel_id)
        if not compatible_evidence_access(source_message.channel, channel):
            raise ReportChannelError(_t('text.custodio.privacy_mismatch'))
        key = (guild.id, source_message.id)
        import os
        db_path = os.environ.get("DB_PATH")
        ledger_key = f"custodio-report:{guild.id}:{source_message.id}"
        if key not in _published_evidence:
            from custodio_evidence_index import find_reference, prepare_index
            import os
            db_path = os.environ.get("DB_PATH")
            if db_path:
                prepare_index(db_path)
                previous_id = find_reference(db_path, guild.id, source_message.id)
                if previous_id:
                    _published_evidence[key] = previous_id
        if key in _published_evidence:
            if db_path and await asyncio.to_thread(delivery_state, db_path, ledger_key) not in {None, "complete"}:
                raise ReportChannelError(_t('text.custodio.delivery_review'))
            try:
                return await channel.fetch_message(_published_evidence[key])
            except discord.NotFound as exc:
                raise ReportChannelError(_t('text.custodio.delivery_review')) from exc
            except discord.HTTPException as exc:
                raise ReportChannelError(_t('text.7fd3f44c21a889')) from exc
        original_exists = False
        try:
            current = await source_message.channel.fetch_message(source_message.id)
            original_exists = current.content == source_message.content
        except discord.NotFound:
            pass
        except discord.HTTPException as exc:
            raise ReportChannelError(_t('text.7fd3f44c21a889')) from exc
        embeds = custodio_literal_report(
            actor=f"{source_message.author} {source_message.author.id}", guild_name=guild.name,
            channel_name=source_message.channel.name,
            occurred_at=source_message.created_at, verbatim=source_message.content,
            rule_text=rule_text, rule_number=rule_number,
            footer=footer, icon_url=icon_url,
            original_url=source_message.jump_url, original_exists=original_exists,
            observed_description=observed_description, conduct=conduct,
        )
        from heraldo_evidence import evidence_batches
        batches = evidence_batches(embeds)
        from evidence_archive import ledger
        if not db_path:
            raise ReportChannelError(_t('text.custodio.delivery_review'))
        claimed, state, receipts = await asyncio.to_thread(ledger, db_path, ledger_key, "claim")
        if not claimed:
            if state == "complete" and receipts:
                return await channel.fetch_message(int(receipts[0]["message_id"]))
            raise ReportChannelError(_t('text.custodio.delivery_review'))
        try:
            # No permitir menciones en el reporte aunque la cita las contenga.
            report = None
            for batch in batches:
                _get_safe_existing(guild, report_channel_id)
                if not compatible_evidence_access(source_message.channel, channel):
                    raise ReportChannelError(_t('text.custodio.privacy_mismatch'))
                sent = await channel.send(embeds=batch, view=review_view if report is None else None,
                                          allowed_mentions=discord.AllowedMentions.none())
                report = report or sent
                if key not in _published_evidence:
                    _published_evidence[key] = sent.id
                    from custodio_evidence_index import save_reference
                    await asyncio.to_thread(save_reference, db_path, guild.id, source_message.id, sent.id)
                receipts.append({"message_id": sent.id, "channel_id": channel.id,
                                 "source_channel_id": source_message.channel.id,
                                 "source_message_id": source_message.id,
                                 "guild_id": guild.id, "actor_id": source_message.author.id,
                                 "rule_number": rule_number,
                                 "rules_revision": rules_revision})
                await asyncio.to_thread(ledger, db_path, ledger_key, "pending", receipts)
        except (discord.Forbidden, discord.HTTPException) as exc:
            raise ReportChannelError(_t('text.69f89336b1e086')) from exc
        if len(_published_evidence) >= MAX_RECENT_EVIDENCE:
            _published_evidence.pop(next(iter(_published_evidence)))
        _published_evidence[key] = report.id
        if db_path:
            from custodio_evidence_index import save_reference
            save_reference(db_path, guild.id, source_message.id, report.id)
            await asyncio.to_thread(ledger, db_path, ledger_key, "complete", receipts)
        return report


@_i18n_context
async def unlink_deleted_original(*, guild: discord.Guild, deleted_message_id: int,
                                  report_channel_id: int) -> bool:
    """Quitar el enlace de un reporte existente sin tocar la copia literal.

    Recupera la referencia mínima persistida después de un reinicio. La copia
    literal permanece en Discord y nunca se vuelve a cargar desde SQLite.
    """
    key = (guild.id, deleted_message_id)
    report_id = _published_evidence.get(key)
    if report_id is None:
        import os
        from custodio_evidence_index import find_reference, prepare_index
        db_path = os.environ.get("DB_PATH")
        if db_path:
            prepare_index(db_path)
            report_id = find_reference(db_path, guild.id, deleted_message_id)
        if report_id is None:
            return False
        _published_evidence[key] = report_id
    lock = _publish_locks.setdefault(guild.id, asyncio.Lock())
    async with lock:
        report_id = _published_evidence.get(key)
        if report_id is None:
            return False
        channel = _get_safe_existing(guild, report_channel_id)
        try:
            message = await channel.fetch_message(report_id)
            embeds = list(message.embeds)
            for embed in embeds:
                fields = list(embed.fields)
                embed.clear_fields()
                for field in fields:
                    if field.name not in _i18n_variants('text.a376d1351c3f23'):
                        embed.add_field(name=field.name, value=field.value, inline=field.inline)
            await message.edit(embeds=embeds, allowed_mentions=discord.AllowedMentions.none())
        except discord.NotFound:
            _published_evidence.pop(key, None)
            return False
        except (discord.Forbidden, discord.HTTPException) as exc:
            raise ReportChannelError(_t('text.cdd5936f9eed18')) from exc
        _published_evidence.pop(key, None)
        import os
        db_path = os.environ.get("DB_PATH")
        if db_path:
            from custodio_evidence_index import remove_reference
            remove_reference(db_path, guild.id, deleted_message_id)
        return True
