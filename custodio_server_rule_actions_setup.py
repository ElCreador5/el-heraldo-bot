"""Configuración de respuestas por cada regla real verificada de Discord.

Solo preferencias inactivas. La revisión exacta del reglamento es obligatoria.
"""
from __future__ import annotations
from heraldo_i18n import text as _t, guild_context as _i18n_context, use_guild as _i18n_guild
import json
import discord

from custodio_rule_actions import VALID_ACTIONS
from custodio_core import RulesSnapshot

SETTING_KEY = "custodio_server_rule_actions_v1"
ACTIONS = (
    ("report", _t('text.fb57b92cfc0723'), _t('text.37ae072b3fc80e')),
    ("warn", _t('text.8448814dc5caff'), _t('text.2d196f9f6b469f')),
    ("temp_ban", _t('text.560bdcdd9b4bbd'), _t('text.defd04a66bfabc')),
    ("kick", _t('text.ffb1a9c946e708'), _t('text.6a74479ec8e587')),
    ("ban", _t('text.520ed297c96f7b'), _t('text.99d6cca06ae564')),
)

def decode(raw, snapshot: RulesSnapshot):
    defaults = ["report"] * snapshot.count
    try:
        obj = json.loads(raw) if raw else {}
        if (type(obj) is dict and obj.get("version") == 1
                and obj.get("revision") == snapshot.revision
                and obj.get("enforcement_enabled") is False
                and type(obj.get("actions")) is list
                and len(obj["actions"]) == snapshot.count
                and all(a in VALID_ACTIONS for a in obj["actions"])):
            return list(obj["actions"])
    except (TypeError, ValueError):
        pass
    return defaults

def encode(snapshot: RulesSnapshot, choices, durations=None):
    if len(choices) != snapshot.count or any(a not in VALID_ACTIONS for a in choices):
        raise ValueError("invalid_rule_actions")
    payload = {
        "version": 1, "revision": snapshot.revision,
        "enforcement_enabled": False, "actions": list(choices),
    }
    if durations is not None:
        if len(durations) != snapshot.count or any(type(n) is not int or not 1 <= n <= 43200 for n in durations):
            raise ValueError("invalid_temp_ban_duration")
        payload["temp_ban_minutes"] = list(durations)
    return json.dumps(payload, separators=(",", ":"), ensure_ascii=False)


def decode_durations(raw, snapshot):
    try:
        data = json.loads(raw)
        values = data.get("temp_ban_minutes")
        if (data.get("revision") == snapshot.revision and type(values) is list
                and len(values) == snapshot.count and all(type(n) is int and 1 <= n <= 43200 for n in values)):
            return values.copy()
    except (ValueError, TypeError, AttributeError):
        pass
    return [60] * snapshot.count

class CustodioServerRuleActionsView(discord.ui.View):
    """Acciones de las reglas oficiales, nunca de plantillas genéricas."""

    @_i18n_context
    def __init__(self, parent, snapshot: RulesSnapshot):
        super().__init__(timeout=600)
        self.parent = parent
        self.snapshot = snapshot
        self.original = parent.get_setting(parent.guild_id, SETTING_KEY)
        self.saved = decode(self.original, snapshot)
        self.pending = self.saved.copy()
        self.saved_durations = decode_durations(self.original, snapshot)
        self.durations = self.saved_durations.copy()
        self.index = 0
        self._saving = False

        self.rules_select = discord.ui.Select(
            placeholder=_t('text.428d2d90458fc5'),
            row=0,
            options=[
                discord.SelectOption(
                    label=_t('text.21c2960681a0f2', p0=f'{i + 1}', p1=f'{text[:75]}'),
                    value=str(i),
                    description=_t('text.ab827188c50dff'),
                ) for i, text in enumerate(snapshot.rules)
            ],
        )
        self.rules_select.callback = self.select_rule
        self.add_item(self.rules_select)

        self.actions_select = discord.ui.Select(
            placeholder=_t('text.4c283dd491f48b'),
            row=1,
            options=[
                discord.SelectOption(label=label, value=value, description=desc)
                for value, label, desc in ACTIONS
            ],
        )
        self.actions_select.callback = self.select_action
        self.add_item(self.actions_select)

        self.duration_select = discord.ui.Select(placeholder=_t("text.custodio.temp_duration"), row=2,
            options=[discord.SelectOption(label=_t("text.custodio.minutes", minutes=n), value=str(n),
                       description=_t("text.custodio.temp_help")) for n in (15, 60, 360, 1440, 10080, 43200)])
        self.duration_select.callback = self.select_duration
        self.add_item(self.duration_select)

        self.save_button = discord.ui.Button(
            label=_t('text.14bdfaf2face3a'), style=discord.ButtonStyle.success, row=3)
        self.save_button.callback = self.save
        self.add_item(self.save_button)
        self.discard_button = discord.ui.Button(
            label=_t('text.80ca383e9c8d3e'), style=discord.ButtonStyle.danger, row=3)
        self.discard_button.callback = self.discard
        self.add_item(self.discard_button)
        back = discord.ui.Button(label=_t('text.ab26ae7bca3621'), style=discord.ButtonStyle.secondary, row=3)
        back.callback = self.back
        self.add_item(back)
        full = discord.ui.Button(label=_t("text.custodio.full_rule"), style=discord.ButtonStyle.secondary, row=4)
        full.callback = self.full_rule
        self.add_item(full)
        self.sync()

    @_i18n_context
    async def interaction_check(self, interaction):
        return await self.parent.access_check(
            interaction, self.parent.guild_id, self.parent.owner_id)

    @_i18n_context
    def sync(self):
        for option in self.rules_select.options:
            option.default = option.value == str(self.index)
        for option in self.actions_select.options:
            option.default = option.value == self.pending[self.index]
        for option in self.duration_select.options:
            option.default = option.value == str(self.durations[self.index])
        self.duration_select.disabled = self.pending[self.index] != "temp_ban"
        dirty = self.pending != self.saved or self.durations != self.saved_durations
        self.save_button.disabled = not dirty or self._saving
        self.discard_button.disabled = not dirty or self._saving

    @_i18n_context
    def summary(self):
        selected = self.snapshot.rules[self.index]
        selected = selected[:1100] + (str(_t("text.custodio.excerpt")) if len(selected) > 1100 else "")
        labels = dict((value, label) for value, label, _ in ACTIONS)
        return (
            _t('text.cdf37bc5779ea5', p0=f'{self.snapshot.count}', p1=f'{self.snapshot.revision[:12]}', p2=f'{self.index + 1}', p3=f'{selected}', p4=f'{labels[self.pending[self.index]]}', p5=f'{sum((a != b for a, b in zip(self.pending, self.saved)))}')
        ) + ("\n" + str(_t("text.custodio.minutes", minutes=self.durations[self.index])) if self.pending[self.index] == "temp_ban" else "")

    async def full_rule(self, interaction):
        from custodio_setup import CustodioRulesView
        view = CustodioRulesView(self.parent, self.snapshot, index=self.index, return_view=self)
        await interaction.response.edit_message(content=view.summary(), view=view, embed=None)

    async def select_duration(self, interaction):
        self.durations[self.index] = int(self.duration_select.values[0])
        self.sync()
        await interaction.response.edit_message(content=self.summary(), view=self, embed=None)

    @_i18n_context
    async def select_rule(self, interaction):
        self.index = int(self.rules_select.values[0])
        self.sync()
        await interaction.response.edit_message(content=self.summary(), view=self, embed=None)

    @_i18n_context
    async def select_action(self, interaction):
        action = self.actions_select.values[0]
        if action in VALID_ACTIONS:
            self.pending[self.index] = action
        self.sync()
        await interaction.response.edit_message(content=self.summary(), view=self, embed=None)

    @_i18n_context
    async def save(self, interaction):
        if self._saving:
            await interaction.response.defer(thinking=False)
            return
        self._saving = True
        self.sync()
        await interaction.response.defer(thinking=False)
        try:
            # Otra consulta valida que las reglas no hayan cambiado durante la edición.
            import os
            from custodio_source import load_server_rules
            fresh = await load_server_rules(self.parent.guild_id, os.environ.get("DISCORD_TOKEN", ""))
            if fresh.revision != self.snapshot.revision:
                notice = _t('text.e5474b8245453f')
            else:
                proposal = encode(self.snapshot, self.pending, self.durations)
                ok = self.parent.save_atomic(
                    self.parent.guild_id,
                    {SETTING_KEY: self.original},
                    {SETTING_KEY: proposal},
                )
                if ok:
                    self.original = proposal
                    self.saved = self.pending.copy()
                    self.saved_durations = self.durations.copy()
                    notice = _t('text.5a21fcce6712fa')
                else:
                    notice = _t('text.a58bbaf3c14428')
        except Exception:
            notice = _t('text.efb87e37779416')
        finally:
            self._saving = False
            self.sync()
        await interaction.edit_original_response(content=self.summary() + "\n\n" + notice, view=self, embed=None)

    @_i18n_context
    async def discard(self, interaction):
        self.original = self.parent.get_setting(self.parent.guild_id, SETTING_KEY)
        self.saved = decode(self.original, self.snapshot)
        self.saved_durations = decode_durations(self.original, self.snapshot)
        self.pending = self.saved.copy()
        self.durations = self.saved_durations.copy()
        self.sync()
        await interaction.response.edit_message(content=self.summary(), view=self, embed=None)

    @_i18n_context
    async def back(self, interaction):
        if self.pending != self.saved or self.durations != self.saved_durations:
            await interaction.response.edit_message(
                content=self.summary() + _t('text.c15d7d491d22ac'),
                view=self, embed=None,
            )
            return
        self.parent._sync_controls()
        await interaction.response.edit_message(
            content=self.parent.summary(), view=self.parent, embed=None)
