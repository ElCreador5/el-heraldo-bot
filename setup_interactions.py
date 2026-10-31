"""ACK y exclusión de clics para todas las sesiones administrativas de /setup.

Se instala en el despacho de View, antes de permisos, SQLite y renderizado.
Los callbacks directos y sus reglas de negocio conservan su interfaz.
"""
from __future__ import annotations
from heraldo_i18n import text as _t, guild_context as _i18n_context, use_guild as _i18n_guild, variants as _i18n_variants

import asyncio
from collections import OrderedDict
from contextvars import ContextVar
from functools import wraps
import inspect
import time

from setup_save_controls import refresh_save_button


ACK_KEY = "heraldo_setup_deferred"
STARTED_KEY = "heraldo_view_started"
_busy: set[tuple] = set()
_seen: OrderedDict = OrderedDict()
source_guild = ContextVar("heraldo_interaction_source_guild", default=None)


@_i18n_context
def _parent_of(view):
    for name in ("parent", "editor", "parent_view", "setup_view"):
        parent = getattr(view, name, None)
        if parent is not None:
            return parent
    return None


@_i18n_context
def is_setup_session(view):
    """Incluye subpaneles que conservan la sesión en parent/editor."""
    visited = set()
    while view is not None and id(view) not in visited:
        visited.add(id(view))
        if getattr(view, "guild_id", None) and getattr(view, "owner_id", None):
            return True
        view = _parent_of(view)
    return False


@_i18n_context
def may_open_modal(callback, view, visited=None):
    """Conservador: sigue ayudantes, métodos heredados y callbacks dinámicos.

    Un modal tiene que ser la respuesta inicial: nunca se difiere esa ruta.
    """
    callback = getattr(callback, "callback", callback)  # discord.py _ItemCallback
    callback = inspect.unwrap(getattr(callback, "__func__", callback))
    if getattr(callback, "__module__", "") == "heraldo_i18n":
        return False  # Renderizadores puros: no abren modales ni hacen IO de Discord.
    code = getattr(callback, "__code__", None)
    if code is None:
        return True  # Callable desconocido: no consumir su respuesta inicial.
    visited = set() if visited is None else visited
    key = (callback, id(view))
    if key in visited:
        return False
    visited.add(key)
    if "send_modal" in code.co_names:
        return True
    namespace = getattr(callback, "__globals__", {})
    for name in code.co_names:
        candidates = [(namespace.get(name), view)]
        owner = view
        ancestors = set()
        while owner is not None and id(owner) not in ancestors:
            ancestors.add(id(owner))
            candidates.append((getattr(owner, name, None), owner))
            owner = _parent_of(owner)
        for candidate, owner in candidates:
            candidate = getattr(candidate, "callback", candidate)
            if inspect.isroutine(candidate) and may_open_modal(candidate, owner, visited):
                return True
    return False



@_i18n_context
def needs_initial_response(view, item, interaction):
    """Never ACK before Discord-only first responses (modal or Activity).

    Only the explicitly selected route is exempt. Other /setup selections
    retain the fast defer/ACK protection and avoid 'Interaction failed'.
    """
    if may_open_modal(item.callback, view):
        return True
    values = (getattr(interaction, "data", None) or {}).get("values") or ()
    routes = getattr(view, "_no_defer_select_values", ())
    return bool(values and values[0] in routes)


def install(discord):
    """Compatibilidad probada con el despacho de discord.py en CI."""
    if getattr(discord.ui.View._scheduled_task, "_heraldo_setup_guard", False):
        return
    original_task = discord.ui.View._scheduled_task
    original_modal_task = discord.ui.Modal._scheduled_task
    original_send = discord.InteractionResponse.send_message
    original_edit = discord.InteractionResponse.edit_message
    original_defer = discord.InteractionResponse.defer
    original_original_edit = getattr(getattr(discord, "Interaction", None), "edit_original_response", None)
    original_message_edit = getattr(getattr(discord, "Message", None), "edit", None)
    original_error = discord.ui.View.on_error

    @wraps(original_send)
    async def send(response, *args, **kwargs):
        refresh_save_button(kwargs.get("view"))
        interaction = response._parent
        if interaction.extras.get(ACK_KEY) and response.is_done():
            return await interaction.followup.send(*args, **kwargs)
        return await original_send(response, *args, **kwargs)

    @wraps(original_edit)
    async def edit(response, **kwargs):
        refresh_save_button(kwargs.get("view"))
        interaction = response._parent
        if interaction.extras.get(ACK_KEY) and response.is_done():
            return await interaction.edit_original_response(**kwargs)
        return await original_edit(response, **kwargs)

    @wraps(original_original_edit)
    async def edit_original(interaction, **kwargs):
        refresh_save_button(kwargs.get("view"))
        return await original_original_edit(interaction, **kwargs)

    @wraps(original_message_edit)
    async def message_edit(message, **kwargs):
        refresh_save_button(kwargs.get("view"))
        return await original_message_edit(message, **kwargs)

    @wraps(original_defer)
    async def defer(response, **kwargs):
        if response._parent.extras.get(ACK_KEY) and response.is_done():
            return None
        return await original_defer(response, **kwargs)

    @wraps(original_error)
    @_i18n_context
    async def on_error(view, interaction, error, item):
        await original_error(view, interaction, error, item)
        if interaction.extras.get(ACK_KEY):
            text = str(error) if isinstance(error, ValueError) else (
                _t('text.6b8921f1c59e4e')
            )
            try:
                await interaction.followup.send(text[:1800], ephemeral=True)
            except discord.HTTPException:
                print("SETUP_INTERACTION status=ERROR_FEEDBACK_FAILED", flush=True)

    @wraps(original_task)
    @_i18n_context
    async def scheduled(view, item, interaction):
        interaction.extras[STARTED_KEY] = True
        if not is_setup_session(view):
            return await original_task(view, item, interaction)
        started = time.monotonic()
        message_id = getattr(interaction.message, "id", None)
        key = (interaction.guild_id, message_id or id(view))
        if interaction.id in _seen:
            return  # Redelivery del mismo evento: no repetir la operación.
        _seen[interaction.id] = None
        while len(_seen) > 2048:
            _seen.popitem(last=False)
        claimed = key not in _busy
        cancel_pending = (getattr(item, 'label', None) in _i18n_variants('text.bb9dbb406dcbd5')
                          and getattr(view, "finished", None) is False)
        if not claimed and not cancel_pending:
            try:
                await interaction.response.send_message(
                    _t('text.087da0212134bc'),
                    ephemeral=True,
                )
            except discord.HTTPException:
                print("SETUP_INTERACTION status=BUSY_ACK_FAILED", flush=True)
            return
        if claimed:
            _busy.add(key)
        try:
            if not needs_initial_response(view, item, interaction) and not interaction.response.is_done():
                try:
                    await interaction.response.defer()
                except discord.HTTPException as exc:
                    # No ejecutar una mutación después de perder la interacción.
                    print(f"SETUP_INTERACTION status=ACK_FAILED code={exc.code}", flush=True)
                    return
                interaction.extras[ACK_KEY] = True
            return await original_task(view, item, interaction)
        finally:
            if claimed:
                _busy.discard(key)
            elapsed = round((time.monotonic() - started) * 1000)
            if elapsed >= 2000:
                print(f"SETUP_INTERACTION status=SLOW view={type(view).__name__} elapsed_ms={elapsed}",
                      flush=True)

    @wraps(original_modal_task)
    @_i18n_context
    async def modal_scheduled(modal, interaction, *args, **kwargs):
        interaction.extras[STARTED_KEY] = True
        if (getattr(modal, "guild_id", None) or is_setup_session(modal)) and not interaction.response.is_done():
            try:
                await interaction.response.defer(
                    thinking=interaction.message is None, ephemeral=True,
                )
            except discord.HTTPException as exc:
                print(f"SETUP_INTERACTION status=MODAL_ACK_FAILED code={exc.code}", flush=True)
                return
            interaction.extras[ACK_KEY] = True
        return await original_modal_task(modal, interaction, *args, **kwargs)

    @wraps(scheduled)
    @_i18n_context
    async def contextual_scheduled(view, item, interaction):
        token = source_guild.set(getattr(interaction, "guild", None))
        try:
            return await scheduled(view, item, interaction)
        finally:
            source_guild.reset(token)

    contextual_scheduled._heraldo_setup_guard = True
    discord.InteractionResponse.send_message = send
    discord.InteractionResponse.edit_message = edit
    discord.InteractionResponse.defer = defer
    if original_original_edit is not None:
        discord.Interaction.edit_original_response = edit_original
    if original_message_edit is not None:
        discord.Message.edit = message_edit
    discord.ui.View._scheduled_task = contextual_scheduled
    discord.ui.Modal._scheduled_task = modal_scheduled
    discord.ui.View.on_error = on_error
