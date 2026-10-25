"""Configuración de respuestas por cada regla real verificada de Discord.

Solo preferencias inactivas. La revisión exacta del reglamento es obligatoria.
"""
from __future__ import annotations
import json
import discord

from custodio_rule_actions import VALID_ACTIONS
from custodio_core import RulesSnapshot

SETTING_KEY = "custodio_server_rule_actions_v1"
ACTIONS = (
    ("report", "Solo reportar", "Registra el caso para revisión humana."),
    ("warn", "Warn", "Advertencia central pendiente de integración."),
    ("temp_ban", "Temp Ban", "Baneo temporal pendiente de integración."),
    ("kick", "Expulsar", "Expulsión pendiente de integración."),
    ("ban", "Ban", "Baneo pendiente de integración."),
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

def encode(snapshot: RulesSnapshot, choices):
    if len(choices) != snapshot.count or any(a not in VALID_ACTIONS for a in choices):
        raise ValueError("invalid_rule_actions")
    return json.dumps({
        "version": 1, "revision": snapshot.revision,
        "enforcement_enabled": False, "actions": list(choices),
    }, separators=(",", ":"), ensure_ascii=False)

class CustodioServerRuleActionsView(discord.ui.View):
    """Acciones de las reglas oficiales, nunca de plantillas genéricas."""

    def __init__(self, parent, snapshot: RulesSnapshot):
        super().__init__(timeout=600)
        self.parent = parent
        self.snapshot = snapshot
        self.original = parent.get_setting(parent.guild_id, SETTING_KEY)
        self.saved = decode(self.original, snapshot)
        self.pending = self.saved.copy()
        self.index = 0
        self._saving = False

        self.rules_select = discord.ui.Select(
            placeholder="Seleccione una regla real del servidor",
            row=0,
            options=[
                discord.SelectOption(
                    label=f"Regla {i+1}: {text[:75]}",
                    value=str(i),
                    description="Regla obtenida de Server Rules",
                ) for i, text in enumerate(snapshot.rules)
            ],
        )
        self.rules_select.callback = self.select_rule
        self.add_item(self.rules_select)

        self.actions_select = discord.ui.Select(
            placeholder="Respuesta para esta regla (borrador)",
            row=1,
            options=[
                discord.SelectOption(label=label, value=value, description=desc)
                for value, label, desc in ACTIONS
            ],
        )
        self.actions_select.callback = self.select_action
        self.add_item(self.actions_select)

        self.save_button = discord.ui.Button(
            label="Guardar cambios", style=discord.ButtonStyle.success, row=2)
        self.save_button.callback = self.save
        self.add_item(self.save_button)
        self.discard_button = discord.ui.Button(
            label="Descartar cambios", style=discord.ButtonStyle.danger, row=2)
        self.discard_button.callback = self.discard
        self.add_item(self.discard_button)
        back = discord.ui.Button(label="Volver", style=discord.ButtonStyle.secondary, row=2)
        back.callback = self.back
        self.add_item(back)
        self.sync()

    async def interaction_check(self, interaction):
        return await self.parent.access_check(
            interaction, self.parent.guild_id, self.parent.owner_id)

    def sync(self):
        for option in self.rules_select.options:
            option.default = option.value == str(self.index)
        for option in self.actions_select.options:
            option.default = option.value == self.pending[self.index]
        dirty = self.pending != self.saved
        self.save_button.disabled = not dirty or self._saving
        self.discard_button.disabled = not dirty or self._saving

    def summary(self):
        selected = self.snapshot.rules[self.index]
        selected = selected[:1100] + ("…" if len(selected) > 1100 else "")
        labels = dict((value, label) for value, label, _ in ACTIONS)
        return (
            "**El Heraldo · AutoMod · Custodio · Acciones por regla**\n\n"
            f"**Reglas oficiales verificadas:** {self.snapshot.count}\n"
            f"**Revisión:** {self.snapshot.revision[:12]}\n\n"
            f"**Regla {self.index + 1}:** {selected}\n\n"
            f"**Respuesta propuesta:** {labels[self.pending[self.index]]}\n"
            f"**Cambios pendientes:** {sum(a != b for a, b in zip(self.pending, self.saved))}\n\n"
            "Cada regla se obtiene del servidor actual. No existen categorías universales "
            "ni sugerencias automáticas. Guardar no activa vigilancia ni sanciones. "
            "Si cambian las reglas de Discord, estas preferencias quedan invalidadas."
        )

    async def select_rule(self, interaction):
        self.index = int(self.rules_select.values[0])
        self.sync()
        await interaction.response.edit_message(content=self.summary(), view=self, embed=None)

    async def select_action(self, interaction):
        action = self.actions_select.values[0]
        if action in VALID_ACTIONS:
            self.pending[self.index] = action
        self.sync()
        await interaction.response.edit_message(content=self.summary(), view=self, embed=None)

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
                notice = "Las reglas del servidor cambiaron. Vuelva a abrir Acciones para revisarlas."
            else:
                proposal = encode(self.snapshot, self.pending)
                ok = self.parent.save_atomic(
                    self.parent.guild_id,
                    {SETTING_KEY: self.original},
                    {SETTING_KEY: proposal},
                )
                if ok:
                    self.original = proposal
                    self.saved = self.pending.copy()
                    notice = "Preferencias guardadas sin activar sanciones."
                else:
                    notice = "La configuración fue modificada en otra sesión. Vuelva a abrir Acciones."
        except Exception:
            notice = "No se pudieron verificar las reglas. No se guardaron cambios."
        finally:
            self._saving = False
            self.sync()
        await interaction.edit_original_response(content=self.summary() + "\n\n" + notice, view=self, embed=None)

    async def discard(self, interaction):
        self.pending = self.saved.copy()
        self.sync()
        await interaction.response.edit_message(content=self.summary(), view=self, embed=None)

    async def back(self, interaction):
        if self.pending != self.saved:
            await interaction.response.edit_message(
                content=self.summary() + "\n\nGuarde o descarte antes de volver.",
                view=self, embed=None,
            )
            return
        self.parent._sync_controls()
        await interaction.response.edit_message(
            content=self.parent.summary(), view=self.parent, embed=None)
