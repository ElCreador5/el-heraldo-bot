"""Cierre, permisos y normalización de respuestas de los paneles administrativos."""
from functools import wraps
from contextvars import ContextVar

from panel_navigation import ensure_close_control, ensure_navigation_controls, is_setup_home, lineage
from button_row_layout import balance_view_buttons, install as install_button_rows



_source_view = ContextVar("heraldo_navigation_source_view", default=None)
_source_interaction = ContextVar("heraldo_navigation_source_interaction", default=None)


def remember_previous_panel(view):
    """Record the actual parent while a Discord component opens a new panel."""
    previous = _source_view.get()
    if (view is None or previous is None or previous is view
            or is_setup_home(view) or view in tuple(lineage(previous))):
        return
    if getattr(view, "_heraldo_back_target", None) is not None:
        return
    owner = next((panel for panel in lineage(view)
                  if getattr(panel, "guild_id", None) and getattr(panel, "owner_id", None)), None)
    if owner is None:
        return
    view._heraldo_back_target = previous
    interaction = _source_interaction.get()
    message = getattr(interaction, "message", None)
    if message is not None:
        embeds = getattr(message, "embeds", ()) or ()
        view._heraldo_back_snapshot = {
            "content": getattr(message, "content", None),
            "embed": embeds[0] if embeds else None,
        }


def compact_reaction_editor(discord, view):
    """Liberar un lugar para Cerrar sin eliminar las herramientas existentes."""
    if type(view).__name__ != "HeraldoReactionRolesEditorView":
        raise ValueError("administrative_panel_has_no_close_slot")
    originals = [view.options, view.edit_message]
    for button in originals:
        view.remove_item(button)

    class MoreActions(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=600)
            self.parent = view
            for original in originals:
                proxy = discord.ui.Button(label=original.label, style=original.style,
                                          disabled=original.disabled, row=0)

                async def action(interaction, selected=original):
                    await selected.callback(interaction)

                proxy.callback = action
                self.add_item(proxy)
            back = discord.ui.Button(label="Volver", style=discord.ButtonStyle.secondary, row=1)

            async def go_back(interaction):
                await interaction.response.edit_message(view=view)

            back.callback = go_back
            self.add_item(back)

        async def interaction_check(self, interaction):
            return await self.parent.interaction_check(interaction)

    more = discord.ui.Button(label="Más acciones", style=discord.ButtonStyle.primary, row=4)

    async def open_more(interaction):
        await interaction.response.edit_message(view=MoreActions())

    more.callback = open_more
    view.add_item(more)


def install(discord):
    install_button_rows(discord)
    if getattr(discord.ui.View.to_components, "_heraldo_command_navigation", False):
        return
    original_components = discord.ui.View.to_components
    original_task = discord.ui.View._scheduled_task

    @wraps(original_components)
    def components(view):
        balance_view_buttons(view)
        remember_previous_panel(view)
        try:
            ensure_navigation_controls(view)
        except ValueError as error:
            if str(error) != "administrative_panel_has_no_close_slot":
                raise
            compact_reaction_editor(discord, view)
            ensure_navigation_controls(view)
        return original_components(view)

    @wraps(original_task)
    async def scheduled(view, item, interaction):
        owner = next((panel for panel in lineage(view)
                      if getattr(panel, "guild_id", None) and getattr(panel, "owner_id", None)), None)
        if owner is not None:
            permissions = getattr(interaction.user, "guild_permissions", None)
            if (interaction.guild is None or interaction.guild.id != owner.guild_id
                    or interaction.user.id != owner.owner_id or not getattr(permissions, "manage_guild", False)):
                await interaction.response.send_message("Acceso denegado. Se requiere Gestionar servidor y una sesión propia.", ephemeral=True)
                return
        view_token = _source_view.set(view)
        interaction_token = _source_interaction.set(interaction)
        try:
            return await original_task(view, item, interaction)
        finally:
            _source_view.reset(view_token)
            _source_interaction.reset(interaction_token)

    # Omitir None únicamente al ENVIAR. Al editar, None retira los controles.
    for cls, name in ((discord.InteractionResponse, "send_message"), (discord.Webhook, "send")):
        original = getattr(cls, name)

        @wraps(original)
        async def send(self, *args, _original=original, **kwargs):
            if kwargs.get("view", False) is None:
                kwargs.pop("view")
            ensure_close_control(kwargs.get("view"))
            return await _original(self, *args, **kwargs)

        setattr(cls, name, send)
    components._heraldo_command_navigation = True
    discord.ui.View.to_components = components
    discord.ui.View._scheduled_task = scheduled
