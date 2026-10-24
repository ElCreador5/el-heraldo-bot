"""Editor de plantillas de acciones de Custodio: borrador aislado por servidor.

No habilita modo automático ni configura sanciones en Discord. Las propuestas
por categoría deben ligarse posteriormente a reglas locales aprobadas.
"""
from __future__ import annotations

import discord

from custodio_rule_actions import (
    SETTING_KEY, TEMPLATES, TEMPLATE_BY_KEY, VALID_ACTIONS,
    decode_actions, encode_actions, suggested_action,
)

ACTION_LABELS = {
    "report": "Solo reportar",
    "kick": "Expulsar (futuro)",
    "ban": "Banear (futuro)",
}
ACTION_DESCRIPTIONS = {
    "report": "Registra la observación para revisión, sin sancionar.",
    "kick": "Propuesta de expulsión; no ejecutable en esta fase.",
    "ban": "Propuesta de baneo; no ejecutable en esta fase.",
}


class CustodioRuleActionsView(discord.ui.View):
    def __init__(self, parent):
        super().__init__(timeout=600)
        self.parent = parent
        self.selected_category = TEMPLATES[0].key
        self.original_raw = parent.get_setting(parent.guild_id, SETTING_KEY)
        self.saved_actions, self.has_saved_policy = decode_actions(self.original_raw)
        self.pending_actions = self.saved_actions.copy()
        self._committing = False

        self.category_selector = discord.ui.Select(
            placeholder="Tipo de infracción según las reglas del servidor",
            row=0, min_values=1, max_values=1,
            options=[
                discord.SelectOption(
                    label=entry.label, value=entry.key,
                    description=entry.description[:100],
                ) for entry in TEMPLATES
            ],
        )
        self.category_selector.callback = self.choose_category
        self.add_item(self.category_selector)

        self.action_selector = discord.ui.Select(
            placeholder="Acción propuesta para este tipo (sin sanciones activas)",
            row=1, min_values=1, max_values=1,
            options=[
                discord.SelectOption(
                    label=ACTION_LABELS[action],
                    value=action,
                    description=ACTION_DESCRIPTIONS[action],
                ) for action in ("report", "kick", "ban")
            ],
        )
        self.action_selector.callback = self.choose_action
        self.add_item(self.action_selector)

        suggestion = discord.ui.Button(
            label="Usar sugerencia", style=discord.ButtonStyle.primary, row=2,
        )
        suggestion.callback = self.apply_suggestion
        self.add_item(suggestion)

        save = discord.ui.Button(
            label="Guardar cambios", style=discord.ButtonStyle.success, row=2,
        )
        save.callback = self.save_changes
        self.save_button = save
        self.add_item(save)

        discard = discord.ui.Button(
            label="Descartar cambios", style=discord.ButtonStyle.danger, row=3,
        )
        discard.callback = self.discard_changes
        self.discard_button = discard
        self.add_item(discard)

        back = discord.ui.Button(
            label="Volver", style=discord.ButtonStyle.secondary, row=3,
        )
        back.callback = self.back
        self.add_item(back)
        self._sync_controls()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return await self.parent.access_check(
            interaction, self.parent.guild_id, self.parent.owner_id
        )

    def _dirty(self) -> bool:
        return self.pending_actions != self.saved_actions

    def _sync_controls(self) -> None:
        for option in self.category_selector.options:
            option.default = option.value == self.selected_category
        for option in self.action_selector.options:
            option.default = option.value == self.pending_actions[self.selected_category]
        self.save_button.disabled = not self._dirty() or self._committing
        self.discard_button.disabled = not self._dirty() or self._committing

    def summary(self) -> str:
        category = TEMPLATE_BY_KEY[self.selected_category]
        pending = self.pending_actions[self.selected_category]
        pending_count = sum(
            new != self.saved_actions[key]
            for key, new in self.pending_actions.items()
        )
        entries = "\n".join(
            f"• {entry.label}: {ACTION_LABELS[self.pending_actions[entry.key]]}"
            for entry in TEMPLATES
        )
        return (
            "**El Heraldo · AutoMod · Custodio · Acciones por tipo**\n\n"
            "Estas son plantillas sugeridas, no reglas universales. "
            "Cada servidor debe vincularlas a sus propias Server Rules aprobadas.\n"
            "NH se refiere a las normas internas del bot.\n\n"
            f"**Plantillas:**\n{entries}\n\n"
            f"**Tipo seleccionado:** {category.label}\n"
            f"**Sugerencia:** {ACTION_LABELS[suggested_action(category.key)]}\n"
            f"**Selección actual:** {ACTION_LABELS[pending]}\n"
            f"**Cambios pendientes:** {pending_count}\n"
            f"**Configuración:** {'Guardada (inactiva)' if self.has_saved_policy else 'Sin guardar'}\n\n"
            "**Importante:** este panel guarda preferencias para el futuro. "
            "Custodio permanece en modo Observar, sin clasificador operativo, "
            "sin supervisión activa y sin expulsiones ni baneos automáticos."
        )

    async def choose_category(self, interaction: discord.Interaction) -> None:
        category = self.category_selector.values[0]
        if category not in TEMPLATE_BY_KEY:
            await interaction.response.edit_message(content=self.summary(), view=self, embed=None)
            return
        self.selected_category = category
        self._sync_controls()
        await interaction.response.edit_message(content=self.summary(), view=self, embed=None)

    async def choose_action(self, interaction: discord.Interaction) -> None:
        action = self.action_selector.values[0]
        if action not in VALID_ACTIONS:
            await interaction.response.edit_message(content=self.summary(), view=self, embed=None)
            return
        self.pending_actions[self.selected_category] = action
        self._sync_controls()
        await interaction.response.edit_message(content=self.summary(), view=self, embed=None)

    async def apply_suggestion(self, interaction: discord.Interaction) -> None:
        self.pending_actions[self.selected_category] = suggested_action(self.selected_category)
        self._sync_controls()
        await interaction.response.edit_message(content=self.summary(), view=self, embed=None)

    async def save_changes(self, interaction: discord.Interaction) -> None:
        if self._committing:
            await interaction.response.defer(thinking=False)
            return
        if not self._dirty():
            await interaction.response.edit_message(content=self.summary(), view=self, embed=None)
            return
        self._committing = True
        self._sync_controls()
        await interaction.response.defer(thinking=False)
        try:
            proposal = encode_actions(self.pending_actions)
            ok = self.parent.save_atomic(
                self.parent.guild_id,
                {SETTING_KEY: self.original_raw},
                {SETTING_KEY: proposal},
            )
            if not ok:
                # CAS: no sobrescribir cambios de otra sesión.
                self.original_raw = self.parent.get_setting(self.parent.guild_id, SETTING_KEY)
                self.saved_actions, self.has_saved_policy = decode_actions(self.original_raw)
                self.pending_actions = self.saved_actions.copy()
                status = "\n\nLa configuración cambió en otra sesión. No se guardaron sus cambios."
            else:
                self.original_raw = proposal
                self.saved_actions = self.pending_actions.copy()
                self.has_saved_policy = True
                status = "\n\nPreferencias guardadas, sin activar sanciones."
        except Exception:
            status = "\n\nNo se pudieron guardar las preferencias. No se activó ninguna sanción."
        finally:
            self._committing = False
            self._sync_controls()
        await interaction.edit_original_response(content=self.summary() + status, view=self, embed=None)

    async def discard_changes(self, interaction: discord.Interaction) -> None:
        self.pending_actions = self.saved_actions.copy()
        self._sync_controls()
        await interaction.response.edit_message(content=self.summary(), view=self, embed=None)

    async def back(self, interaction: discord.Interaction) -> None:
        if self._dirty():
            await interaction.response.edit_message(
                content=self.summary() + "\n\nGuarde o descarte los cambios para volver.",
                view=self, embed=None,
            )
            return
        self.parent._sync_controls()
        await interaction.response.edit_message(
            content=self.parent.summary(), view=self.parent, embed=None,
        )
