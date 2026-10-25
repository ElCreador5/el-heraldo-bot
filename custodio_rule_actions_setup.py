"""Editor de plantillas de acciones de Custodio: borrador aislado por servidor.

No habilita modo automático ni configura sanciones en Discord. Las propuestas
por categoría deben ligarse posteriormente a reglas locales aprobadas.
"""
from __future__ import annotations
from heraldo_i18n import text as _t, guild_context as _i18n_context, use_guild as _i18n_guild

import discord

from custodio_rule_actions import (
    SETTING_KEY, TEMPLATES, TEMPLATE_BY_KEY, VALID_ACTIONS,
    decode_actions, encode_actions, suggested_action,
)

ACTION_LABELS = {
    "report": _t('text.fb57b92cfc0723'),
    "warn": _t('text.8448814dc5caff'),
    "temp_ban": _t('text.560bdcdd9b4bbd'),
    "kick": _t('text.c1df82c8d7ed93'),
    "ban": _t('text.5047b0ff0e35b4'),
}
ACTION_DESCRIPTIONS = {
    "report": _t('text.0cd0ee7856aa89'),
    "warn": _t('text.fe5583126103ee'),
    "temp_ban": _t('text.6f719cc02ce8bb'),
    "kick": _t('text.204bc4d08f485e'),
    "ban": _t('text.30c170b8779c5a'),
}


class CustodioRuleActionsView(discord.ui.View):
    @_i18n_context
    def __init__(self, parent):
        super().__init__(timeout=600)
        self.parent = parent
        self.selected_category = TEMPLATES[0].key
        self.original_raw = parent.get_setting(parent.guild_id, SETTING_KEY)
        self.saved_actions, self.has_saved_policy = decode_actions(self.original_raw)
        self.pending_actions = self.saved_actions.copy()
        self._committing = False

        self.category_selector = discord.ui.Select(
            placeholder=_t('text.4180f6860b00ea'),
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
            placeholder=_t('text.84a8d1547097dc'),
            row=1, min_values=1, max_values=1,
            options=[
                discord.SelectOption(
                    label=ACTION_LABELS[action],
                    value=action,
                    description=ACTION_DESCRIPTIONS[action],
                ) for action in ("report", "warn", "temp_ban", "kick", "ban")
            ],
        )
        self.action_selector.callback = self.choose_action
        self.add_item(self.action_selector)

        suggestion = discord.ui.Button(
            label=_t('text.3dff800821bcd8'), style=discord.ButtonStyle.primary, row=2,
        )
        suggestion.callback = self.apply_suggestion
        self.add_item(suggestion)

        save = discord.ui.Button(
            label=_t('text.14bdfaf2face3a'), style=discord.ButtonStyle.success, row=2,
        )
        save.callback = self.save_changes
        self.save_button = save
        self.add_item(save)

        discard = discord.ui.Button(
            label=_t('text.80ca383e9c8d3e'), style=discord.ButtonStyle.danger, row=3,
        )
        discard.callback = self.discard_changes
        self.discard_button = discard
        self.add_item(discard)

        back = discord.ui.Button(
            label=_t('text.ab26ae7bca3621'), style=discord.ButtonStyle.secondary, row=3,
        )
        back.callback = self.back
        self.add_item(back)
        self._sync_controls()

    @_i18n_context
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return await self.parent.access_check(
            interaction, self.parent.guild_id, self.parent.owner_id
        )

    @_i18n_context
    def _dirty(self) -> bool:
        return self.pending_actions != self.saved_actions

    @_i18n_context
    def _sync_controls(self) -> None:
        for option in self.category_selector.options:
            option.default = option.value == self.selected_category
        for option in self.action_selector.options:
            option.default = option.value == self.pending_actions[self.selected_category]
        self.save_button.disabled = not self._dirty() or self._committing
        self.discard_button.disabled = not self._dirty() or self._committing

    @_i18n_context
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
            _t('text.8b54caa88de96f', p0=f'{entries}', p1=f'{category.label}', p2=f'{ACTION_LABELS[suggested_action(category.key)]}', p3=f'{ACTION_LABELS[pending]}', p4=f'{pending_count}', p5=f"{(_t('text.e524a9ec1211a5') if self.has_saved_policy else _t('text.f8b73aaaaf9da0'))}")
        )

    @_i18n_context
    async def choose_category(self, interaction: discord.Interaction) -> None:
        category = self.category_selector.values[0]
        if category not in TEMPLATE_BY_KEY:
            await interaction.response.edit_message(content=self.summary(), view=self, embed=None)
            return
        self.selected_category = category
        self._sync_controls()
        await interaction.response.edit_message(content=self.summary(), view=self, embed=None)

    @_i18n_context
    async def choose_action(self, interaction: discord.Interaction) -> None:
        action = self.action_selector.values[0]
        if action not in VALID_ACTIONS:
            await interaction.response.edit_message(content=self.summary(), view=self, embed=None)
            return
        self.pending_actions[self.selected_category] = action
        self._sync_controls()
        await interaction.response.edit_message(content=self.summary(), view=self, embed=None)

    @_i18n_context
    async def apply_suggestion(self, interaction: discord.Interaction) -> None:
        self.pending_actions[self.selected_category] = suggested_action(self.selected_category)
        self._sync_controls()
        await interaction.response.edit_message(content=self.summary(), view=self, embed=None)

    @_i18n_context
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
                status = _t('text.e9b5b8dfdd82a4')
            else:
                self.original_raw = proposal
                self.saved_actions = self.pending_actions.copy()
                self.has_saved_policy = True
                status = _t('text.8b89abd03d1b14')
        except Exception:
            status = _t('text.90afd4119451a6')
        finally:
            self._committing = False
            self._sync_controls()
        await interaction.edit_original_response(content=self.summary() + status, view=self, embed=None)

    @_i18n_context
    async def discard_changes(self, interaction: discord.Interaction) -> None:
        self.pending_actions = self.saved_actions.copy()
        self._sync_controls()
        await interaction.response.edit_message(content=self.summary(), view=self, embed=None)

    @_i18n_context
    async def back(self, interaction: discord.Interaction) -> None:
        if self._dirty():
            await interaction.response.edit_message(
                content=self.summary() + _t('text.969ff46d338ddc'),
                view=self, embed=None,
            )
            return
        self.parent._sync_controls()
        await interaction.response.edit_message(
            content=self.parent.summary(), view=self.parent, embed=None,
        )
