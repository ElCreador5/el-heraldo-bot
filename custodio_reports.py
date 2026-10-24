"""Canal privado y tarjeta de referencias para observaciones de Modo Custodio.

No se ejecuta automáticamente: crear el canal exige confirmación administrativa.
No contiene procesador de mensajes, sanciones, lectura de historiales ni copias
de material de canales restringidos. Se conservan metadatos mínimos solamente.
"""
from __future__ import annotations

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


def _get_safe_existing(guild: discord.Guild, channel_id: int) -> discord.TextChannel:
    channel = guild.get_channel(channel_id)
    if not isinstance(channel, discord.TextChannel):
        raise ReportChannelError("El canal vinculado no existe o no es de texto.")
    if channel.topic != CHANNEL_TOPIC or not private_report_channel(channel):
        raise ReportChannelError("El canal vinculado cambió o perdió privacidad; requiere revisión administrativa.")
    me = guild.me
    if me is None:
        raise ReportChannelError("No se puede verificar el acceso del bot.")
    permissions = channel.permissions_for(me)
    if not (permissions.view_channel and permissions.send_messages and
            permissions.embed_links and permissions.read_message_history):
        raise ReportChannelError("El bot no puede publicar registros en el canal.")
    return channel


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
    return True


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
        raise ReportChannelError("No está disponible la identidad del bot.")
    lock = _channel_creation_locks.setdefault(guild.id, asyncio.Lock())
    async with lock:
        raw = get_setting(guild.id, SETTING_KEY)
        if raw:
            if not raw.isdecimal():
                raise ReportChannelError("La referencia guardada del canal no es válida.")
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
                "El bot necesita Gestionar canales, Ver canal, Enviar mensajes, "
                "Insertar enlaces y Leer historial."
            )

        everyone = guild.default_role
        if everyone is None:
            raise ReportChannelError("No se pudo identificar @everyone.")
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
            raise ReportChannelError("Demasiados roles administrativos para crear el canal con seguridad.")
        try:
            channel = await guild.create_text_channel(
                CHANNEL_NAME,
                topic=CHANNEL_TOPIC,
                overwrites=overwrites,
                nsfw=False,
                reason="Modo Custodio: crear canal privado autorizado de observaciones",
            )
        except (discord.Forbidden, discord.HTTPException) as exc:
            raise ReportChannelError("Discord rechazó la creación del canal privado.") from exc

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
        title="Modo Custodio · Observación para revisión",
        description="Detección provisional. No constituye una sanción ni prueba concluyente.",
        color=discord.Color.orange(),
        timestamp=evidence.timestamp.astimezone(timezone.utc),
    )
    embed.add_field(name="Estado", value={
        "suspected": "Posible incumplimiento", "ambiguous": "Contexto insuficiente"
    }[evidence.category], inline=True)
    embed.add_field(name="Reglas", value=", ".join(map(str, sorted(set(evidence.rule_numbers))))[:100], inline=True)
    embed.add_field(name="Contexto", value={
        "sfw": "Canal ordinario", "age_restricted": "Canal o servidor restringido por edad",
        "unknown": "Sin clasificación concluyente",
    }[evidence.classification], inline=False)
    embed.add_field(
        name="Evidencia de referencia",
        value=f"[Ir al mensaje original]({link}) · Mensaje: \x60{evidence.message_id}\x60\n"
              f"Revisión del reglamento: \x60{evidence.rules_revision[:12]}\x60\n"
              f"Huella de contenido: \x60{evidence.content_sha256[:16] if evidence.content_sha256 else 'no disponible'}\x60",
        inline=False,
    )
    embed.set_footer(text="La referencia puede dejar de estar disponible si se elimina el mensaje. No se archivó su contenido.")
    return embed
