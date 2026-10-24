"""Exclusión de operaciones Honeypot en el worker; no escribe datos ni difiere modales."""
from __future__ import annotations

import asyncio
from functools import wraps
from weakref import WeakValueDictionary


_operations: dict[int, asyncio.Task] = {}
_warning_locks: WeakValueDictionary = WeakValueDictionary()


def honeypot_operation(callback):
    """Rechaza otro clic mientras la operación de esa guild sigue pendiente.

    Las delegaciones del mismo callback son reentrantes. No se encolan clics
    antiguos para ejecutarlos después, ni se reconoce antes un botón de modal.
    El worker Test usa una réplica; esto no es un bloqueo distribuido.
    """
    @wraps(callback)
    async def guarded(self, interaction, *args, **kwargs):
        parent = getattr(self, "parent", self)
        guild_id = getattr(self, "guild_id", None) or parent.guild_id
        task = asyncio.current_task()
        owner = _operations.get(guild_id)
        if owner is not None and owner is not task:
            if not interaction.response.is_done():
                await interaction.response.defer()
            await interaction.followup.send(
                "Hay una operación de Honeypot en curso. Espere a que termine antes de continuar.",
                ephemeral=True,
            )
            return
        if owner is task:
            return await callback(self, interaction, *args, **kwargs)
        _operations[guild_id] = task
        try:
            return await callback(self, interaction, *args, **kwargs)
        finally:
            _operations.pop(guild_id, None)
    return guarded


def serialize_honeypot_warning(callback):
    """Relee el ID del aviso dentro del bloqueo compartido por canal."""
    @wraps(callback)
    async def guarded(channel):
        key = (channel.guild.id, channel.id)
        lock = _warning_locks.get(key)
        if lock is None:
            lock = asyncio.Lock()
            _warning_locks[key] = lock
        async with lock:
            return await callback(channel)
    return guarded
