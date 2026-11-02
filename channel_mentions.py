"""Resolver {#ID_DEL_CANAL} como mención visible de un canal del mismo servidor.

No permite nombres ambiguos ni transforma IDs ajenos o inexistentes.
No envía mensajes ni habilita notificaciones.
"""
from __future__ import annotations

import re

CHANNEL_PLACEHOLDER = re.compile(r"\{#([1-9][0-9]{0,19})\}")


def channel_mentions(text: str | None, guild) -> str | None:
    """Sustituye {#ID} por <#ID> únicamente si el canal está en este servidor."""
    if not isinstance(text, str) or guild is None:
        return text

    def replace(match):
        channel_id = int(match.group(1))
        channel = None
        find_channel = getattr(guild, "get_channel_or_thread", None)
        if callable(find_channel):
            channel = find_channel(channel_id)
        if channel is None:
            for getter in ("get_channel", "get_thread"):
                finder = getattr(guild, getter, None)
                if callable(finder):
                    channel = finder(channel_id)
                    if channel is not None:
                        break
        if channel is None or getattr(getattr(channel, "guild", guild), "id", None) != getattr(guild, "id", None):
            return match.group(0)
        return f"<#{channel_id}>"

    return CHANNEL_PLACEHOLDER.sub(replace, text)


def embed_channel_mentions(data, guild):
    """Copia campos de un embed para resolver referencias sin alterar el borrador."""
    if isinstance(data, str):
        return channel_mentions(data, guild)
    if isinstance(data, list):
        return [embed_channel_mentions(v, guild) for v in data]
    if isinstance(data, dict):
        return {k: embed_channel_mentions(v, guild) for k, v in data.items()}
    return data
