"""Lector asíncrono y exclusivo de las Server Rules oficiales de Discord.

La ruta de member-verification fue retirada de la documentación pública de
Discord. Si deja de funcionar, el módulo devuelve un error controlado y
NUNCA sustituye el reglamento por reglas inventadas.
"""
from __future__ import annotations
from heraldo_i18n import text as _t, guild_context as _i18n_context

import asyncio
import json
from collections.abc import Awaitable, Callable
from typing import Any

import aiohttp

from custodio_core import RulesSnapshot, RulesUnavailable, read_snapshot

API_ROOT = "https://discord.com/api/v10"
MAX_RESPONSE_BYTES = 65536
TIMEOUT_SECONDS = 12
Fetcher = Callable[[str], Awaitable[tuple[int, dict[str, Any]]]]


async def load_server_rules(
    guild_id: int,
    bot_token: str,
    *,
    fetcher: Fetcher | None = None,
) -> RulesSnapshot:
    """Lee únicamente dos rutas GET. No se guarda texto ni se realiza moderación.

    fetcher admite dobles de prueba, sin exponer un token real.
    El llamador debe guardar solo snapshots aprobados y no registrar su texto
    indiscriminadamente.
    """
    if not isinstance(guild_id, int) or isinstance(guild_id, bool) or guild_id <= 0:
        raise ValueError("invalid_guild_id")
    if not isinstance(bot_token, str) or not bot_token.strip():
        raise ValueError("bot_token_missing")

    async def run(get: Fetcher) -> RulesSnapshot:
        status, guild = await get(f'/guilds/{guild_id}')
        if status != 200:
            raise RulesUnavailable("guild_unavailable", status)
        features = guild.get("features") if isinstance(guild, dict) else None
        if not isinstance(features, list) or "MEMBER_VERIFICATION_GATE_ENABLED" not in features:
            raise RulesUnavailable("screening_disabled_or_unknown")
        verification_status, verification = await get(f'/guilds/{guild_id}/member-verification')
        return read_snapshot(guild_id, status, guild, verification_status, verification)

    if fetcher is not None:
        return await run(fetcher)

    headers = {
        "Authorization": _t('text.6ed95b9df34151', p0=f'{bot_token}'),
        "Accept": "application/json",
        "User-Agent": "ElHeraldo-Custodio/1.0",
    }
    timeout = aiohttp.ClientTimeout(total=TIMEOUT_SECONDS)
    async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
        async def get_json(path: str) -> tuple[int, dict[str, Any]]:
            try:
                async with session.get(API_ROOT + path) as response:
                    if response.status != 200:
                        return response.status, {}
                    raw = await response.content.read(MAX_RESPONSE_BYTES + 1)
                    if len(raw) > MAX_RESPONSE_BYTES:
                        raise RulesUnavailable("api_response_too_large")
                    payload = json.loads(raw)
                    if not isinstance(payload, dict):
                        raise RulesUnavailable("unexpected_verification_payload")
                    return response.status, payload
            except (aiohttp.ClientError, asyncio.TimeoutError):
                return 0, {}
            except (UnicodeDecodeError, json.JSONDecodeError):
                raise RulesUnavailable("invalid_api_json") from None
        return await run(get_json)
