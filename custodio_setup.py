"""Vista de /setup de Modo Custodio, sin clasificador ni sanciones.

El modo Observar todavía no está en funcionamiento: estas preferencias no
activan supervisión. Todos los cambios requieren una segunda confirmación.
"""
from __future__ import annotations

import os
from typing import Callable, Any

import discord

from custodio_preferences import (
    DEFAULTS, DISPLAY, KEY_SENSITIVITY,
    CustodioPreferences, display_preferences, load_preferences, validate_settings,
)
from custodio_source import load_server_rules
from custodio_core import RulesUnavailable


class CustodioSetupView(discord.ui.View):
    def __init__(
        self, guild_id: int, owner_id: int, *,
        get_setting: Callable[[int, str], str | None],
        save_atomic: Callable[..., bool],
        access_check: Callable[..., Any],
        parent_factory: Callable[[], discord.ui.View],
    ):
        super().__init__(timeout=600)
        self.guild_id = guild_id
        self.owner_id = owner_id
        self.get_setting = get_setting
        self.save_atomic = save_atomic
        self.access_check = access_check
        self.parent_factory = parent_factory
        self.pending_sensitivity = load_preferences(get_setting, guild_id).sensitivity

        select = discord.ui.Select(
            placeholder="Sensibilidad del análisis (borrador)",
            row=0, min_values=1, max_values=1,
            options=[
                discord.SelectOption(label="Conservadora", value="conservative",
                    description="Priorizar la reducción de falsos positivos"),
                discord.SelectOption(label="Equilibrada", value="balanced",
                    description="Combinar análisis contextual y prevención"),
                discord.SelectOption(label="Estricta", value="strict",
                    description="Identificar más casos para revisión humana"),
            ],
        )
        select.callback = self.choose_sensitivity
        self.selector = select
        self.add_item(select)
        self._sync_controls()

        check_button = discord.ui.Button(
            label="Consultar Server Rules", style=discord.ButtonStyle.primary, row=1)
        check_button.callback = self.check_rules
        self.add_item(check_button)

        save_button = discord.ui.Button(
            label="Guardar cambios", style=discord.ButtonStyle.success, row=2)
        save_button.callback = self.save_changes
        self.add_item(save_button)

        discard_button = discord.ui.Button(
            label="Descartar cambios", style=discord.ButtonStyle.danger, row=2)
        discard_button.callback = self.discard_changes
        self.add_item(discard_button)

        back_button = discord.ui.Button(
            label="Volver", style=discord.ButtonStyle.secondary, row=2)
        back_button.callback = self.back
        self.add_item(back_button)

    def _sync_controls(self) -> None:
        for option in self.selector.options:
            option.default = option.value == self.pending_sensitivity
        current = load_preferences(self.get_setting, self.guild_id).sensitivity
        for item in self.children:
            if isinstance(item, discord.ui.Button) and item.label in ("Guardar cambios", "Descartar cambios"):
                item.disabled = (
                    not self._raw_changes()
                    if item.label == "Guardar cambios"
                    else self.pending_sensitivity == current
                )

    def _raw_changes(self) -> dict[str, str]:
        proposal = validate_settings(CustodioPreferences(
            sensitivity=self.pending_sensitivity).as_settings())
        return {k: v for k, v in proposal.items()
                if self.get_setting(self.guild_id, k) != v}

    def summary(self) -> str:
        existing = load_preferences(self.get_setting, self.guild_id)
        lines = [
            "**El Heraldo · AutoMod · Modo Custodio**",
            "",
            display_preferences(existing),
            "",
            "**Cambios pendientes:** " + (
                f"Sensibilidad → {DISPLAY[KEY_SENSITIVITY][self.pending_sensitivity]}"
                if self.pending_sensitivity != existing.sensitivity else "Ninguno."
            ),
            "",
            "Esta pantalla prepara preferencias. La lectura y supervisión continua de mensajes "
            "todavía no están activadas. No se envía contenido a sistemas de IA, "
            "ni se eliminan mensajes ni se sanciona.",
        ]
        return "\n".join(lines)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return await self.access_check(interaction, self.guild_id, self.owner_id)

    async def choose_sensitivity(self, interaction: discord.Interaction):
        self.pending_sensitivity = self.selector.values[0]
        self._sync_controls()
        await interaction.response.edit_message(content=self.summary(), view=self, embed=None)

    async def check_rules(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        token = os.environ.get("DISCORD_TOKEN", "")
        try:
            snapshot = await load_server_rules(self.guild_id, token)
        except (RulesUnavailable, ValueError) as exc:
            reason = exc.reason if isinstance(exc, RulesUnavailable) else "token_unavailable"
            await interaction.edit_original_response(
                content="No fue posible consultar Server Rules (" + reason +
                        "). Las preferencias no se modificaron.",
                view=self, embed=None,
            )
            return
        await interaction.edit_original_response(
            content=self.summary() + "\n\n"
                    f"**Server Rules:** activadas; {snapshot.count} reglas leídas. "
                    f"Revisión: {snapshot.revision[:12]}. "
                    "La API de Discord puede cambiar sin previo aviso.",
            view=self, embed=None,
        )

    async def save_changes(self, interaction: discord.Interaction):
        changes = self._raw_changes()
        if not changes:
            await interaction.response.send_message(
                "La configuración propuesta ya coincide con los valores guardados.",
                ephemeral=True,
            )
            return
        original = {k: self.get_setting(self.guild_id, k) for k in DEFAULTS}
        confirm = CustodioConfirmView(self, changes, original)
        await interaction.response.edit_message(
            content=(
                "**Modo Custodio · Confirmar preferencias**\n\n"
                "Modo: Observar (no operativo aún).\n"
                f"Sensibilidad: {DISPLAY[KEY_SENSITIVITY][self.pending_sensitivity]}.\n"
                "Alcance: Canales elegibles y autorizados.\n"
                "Avisos de cambios: Desactivados.\n"
                "Supervisión: No activada.\n\n"
                "Confirmar solo guarda estas preferencias; no activa sanciones ni IA."
            ),
            view=confirm, embed=None,
        )

    async def discard_changes(self, interaction: discord.Interaction):
        self.pending_sensitivity = load_preferences(self.get_setting, self.guild_id).sensitivity
        self._sync_controls()
        await interaction.response.edit_message(content=self.summary(), view=self, embed=None)

    async def back(self, interaction: discord.Interaction):
        await interaction.response.edit_message(
            content="**El Heraldo · AutoMod**\n\nConfigura las protecciones automáticas del servidor.",
            embed=None, view=self.parent_factory(),
        )


class CustodioConfirmView(discord.ui.View):
    def __init__(self, parent: CustodioSetupView, changes: dict[str, str],
                 original: dict[str, str | None]):
        super().__init__(timeout=300)
        self.parent = parent
        self.changes = validate_settings({
            **{key: original[key] or DEFAULTS[key] for key in DEFAULTS},
            **changes,
        })
        self.original = original
        self.done = False

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if self.done:
            await interaction.response.send_message(
                "Esta confirmación ya fue utilizada.", ephemeral=True)
            return False
        return await self.parent.access_check(
            interaction, self.parent.guild_id, self.parent.owner_id)

    @discord.ui.button(label="Confirmar y guardar", style=discord.ButtonStyle.success)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            ok = self.parent.save_atomic(
                self.parent.guild_id, self.original,
                self.changes,
            )
        except Exception:
            await interaction.response.send_message(
                "No se pudieron guardar los cambios. Inténtelo nuevamente.",
                ephemeral=True,
            )
            return
        if not ok:
            self.done = True
            self.stop()
            await interaction.response.edit_message(
                content="La configuración cambió en otra sesión. No se guardó nada. Abra el panel nuevamente.",
                view=None, embed=None,
            )
            return
        self.done = True
        self.stop()
        self.parent._sync_controls()
        await interaction.response.edit_message(
            content=self.parent.summary() + "\n\n**Preferencias guardadas correctamente.**",
            view=self.parent, embed=None,
        )

    @discord.ui.button(label="Cancelar", style=discord.ButtonStyle.danger)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.done = True
        self.stop()
        self.parent._sync_controls()
        await interaction.response.edit_message(
            content=self.parent.summary() + "\n\nNo se guardaron cambios.",
            view=self.parent, embed=None,
        )
