"""Configuración real de detectores y exenciones. Seleccionar nunca persiste."""
from __future__ import annotations
from dataclasses import replace
import os
import discord
from heraldo_i18n import text as _t, guild_context as _i18n_context
from custodio_policy import KEY, ObservePolicy
from custodio_detection import KINDS, KIND_KEYS
from custodio_source import load_server_rules
from custodio_reports import SETTING_KEY, _get_safe_existing


class CustodioObserveSetupView(discord.ui.View):
    @_i18n_context
    def __init__(self, parent, snapshot, *, exemptions=False):
        super().__init__(timeout=600)
        self.parent, self.snapshot = parent, snapshot
        self.guild_id, self.owner_id = parent.guild_id, parent.owner_id
        self.original = parent.get_setting(self.guild_id, KEY)
        self.saved = ObservePolicy.decode(self.original, snapshot)
        self.pending = self.saved
        self.index = 0
        self.exemptions = exemptions
        self.busy = False
        self.rule_select = discord.ui.Select(
            placeholder=_t("text.custodio.select_scope" if exemptions else "text.428d2d90458fc5"), row=0,
            options=([discord.SelectOption(label=_t("text.custodio.all_rules"), value="0",
                         description=_t("text.custodio.scope_help"))] if exemptions else []) + [
                discord.SelectOption(label=_t("text.21c2960681a0f2", p0=str(n), p1=rule[:75]),
                         value=str(n), description=_t("text.ab827188c50dff"))
                for n, rule in enumerate(snapshot.rules, 1)])
        self.rule_select.callback = self.select_rule
        self.add_item(self.rule_select)
        if exemptions:
            self.role_select = discord.ui.RoleSelect(placeholder=_t("text.custodio.exempt_roles"),
                                                    min_values=0, max_values=25, row=1)
            self.role_select.callback = self.select_roles
            self.add_item(self.role_select)
            self.channel_select = discord.ui.ChannelSelect(placeholder=_t("text.custodio.exempt_channels"),
                min_values=0, max_values=25, channel_types=[discord.ChannelType.text], row=2)
            self.channel_select.callback = self.select_channels
            self.add_item(self.channel_select)
        else:
            self.kind_select = discord.ui.Select(placeholder=_t("text.custodio.select_detector"),
                min_values=0, max_values=len(KINDS), row=1, options=[
                    discord.SelectOption(label=_t(KIND_KEYS[kind]), value=kind,
                                         description=_t("text.custodio.detector_help")) for kind in sorted(KINDS)])
            self.kind_select.callback = self.select_kinds
            self.add_item(self.kind_select)
            self.index = 1
        for name, label, style in (("save", "text.14bdfaf2face3a", discord.ButtonStyle.success),
                                  ("discard", "text.80ca383e9c8d3e", discord.ButtonStyle.danger),
                                  *(([("activate", "text.custodio.activate", discord.ButtonStyle.success),
                                      ("pause", "text.custodio.pause", discord.ButtonStyle.danger)]) if not exemptions else []),
                                  ("back", "text.ab26ae7bca3621", discord.ButtonStyle.secondary)):
            button = discord.ui.Button(label=_t(label), style=style, row=3)
            button.callback = getattr(self, name)
            setattr(self, name + "_button", button)
            self.add_item(button)
        self.sync()

    @_i18n_context
    async def interaction_check(self, interaction):
        return await self.parent.access_check(interaction, self.guild_id, self.owner_id)

    def binding(self):
        return self.pending.bindings[self.index - 1] if self.index else None

    def update(self, **changes):
        if not self.index:
            self.pending = replace(self.pending, **changes)
        else:
            bindings = list(self.pending.bindings)
            bindings[self.index - 1] = replace(bindings[self.index - 1], **changes)
            self.pending = replace(self.pending, bindings=tuple(bindings))
        self.sync()

    def sync(self):
        for option in self.rule_select.options:
            option.default = option.value == str(self.index)
        if self.exemptions:
            scope = self.binding() or self.pending
            self.role_select.default_values = [discord.SelectDefaultValue(id=rid, type=discord.SelectDefaultValueType.role)
                                               for rid in sorted(scope.roles)]
            self.channel_select.default_values = [discord.SelectDefaultValue(id=cid, type=discord.SelectDefaultValueType.channel)
                                                  for cid in sorted(scope.channels)]
        else:
            for option in self.kind_select.options:
                option.default = option.value in self.binding().kinds
            self.activate_button.disabled = self.busy or self.saved.enabled or not any(b.kinds for b in self.saved.bindings)
            self.pause_button.disabled = self.busy or not self.saved.enabled
        self.save_button.disabled = self.busy or self.pending == self.saved
        self.discard_button.disabled = self.busy or self.pending == self.saved

    @_i18n_context
    def summary(self):
        selected = self.binding()
        quote = self.snapshot.rules[self.index - 1] if self.index else ""
        # Texto completo disponible en Reglas del servidor; aquí se rotula el extracto.
        excerpt = quote[:350] + (str(_t("text.custodio.excerpt")) if len(quote) > 350 else "")
        scope = selected or self.pending
        kinds = ", ".join(str(_t(KIND_KEYS[kind])) for kind in sorted(selected.kinds)) if selected else ""
        return str(_t("text.custodio.observe_panel", status=str(_t("text.custodio.on" if self.saved.enabled else "text.custodio.off")),
                      rule=self.index, quote=excerpt, kinds=kinds or str(_t("common.none_sentence")),
                      roles=", ".join(f"<@&{v}>" for v in sorted(scope.roles)) or str(_t("common.none_sentence")),
                      channels=", ".join(f"<#{v}>" for v in sorted(scope.channels)) or str(_t("common.none_sentence")),
                      pending=str(_t("text.custodio.yes" if self.pending != self.saved else "text.custodio.no"))))

    async def wait_for_save(self, interaction):
        if self.busy:
            await interaction.response.defer(thinking=False)
            return True
        return False

    async def select_rule(self, interaction):
        if await self.wait_for_save(interaction):
            return
        self.index = int(self.rule_select.values[0])
        self.sync()
        await interaction.response.edit_message(content=self.summary(), view=self, embed=None)

    async def select_kinds(self, interaction):
        if await self.wait_for_save(interaction):
            return
        self.update(kinds=frozenset(self.kind_select.values))
        await interaction.response.edit_message(content=self.summary(), view=self, embed=None)

    async def select_roles(self, interaction):
        if await self.wait_for_save(interaction):
            return
        self.update(roles=frozenset(role.id for role in self.role_select.values))
        await interaction.response.edit_message(content=self.summary(), view=self, embed=None)

    async def select_channels(self, interaction):
        if await self.wait_for_save(interaction):
            return
        self.update(channels=frozenset(channel.id for channel in self.channel_select.values))
        await interaction.response.edit_message(content=self.summary(), view=self, embed=None)

    @_i18n_context
    async def persist(self, interaction, *, enabled=None):
        if not await self.interaction_check(interaction):
            return
        await interaction.response.defer(thinking=False)
        if self.busy:
            return
        self.busy = True
        notice = _t("text.custodio.save_failed")
        try:
            old = self.parent.get_setting(self.guild_id, KEY)
            if old != self.original:
                raise ValueError("stale_draft")
            if enabled is False:
                proposal = replace(self.saved, enabled=False)
            else:
                fresh = await load_server_rules(self.guild_id, os.environ.get("DISCORD_TOKEN", ""))
                if fresh.revision != self.snapshot.revision:
                    raise ValueError("stale_rules")
                if enabled is True:
                    raw_channel = self.parent.get_setting(self.guild_id, SETTING_KEY)
                    if not raw_channel or not raw_channel.isdecimal() or not any(b.kinds for b in self.saved.bindings):
                        raise ValueError("saved_configuration_required")
                    if not interaction.client.intents.message_content:
                        raise ValueError("content_intent_required")
                    _get_safe_existing(interaction.guild, int(raw_channel))
                    proposal = replace(self.saved, enabled=True)
                else:
                    proposal = self.pending
            if not await self.interaction_check(interaction):
                return
            raw = proposal.encode(self.snapshot.count)
            if not self.parent.save_atomic(self.guild_id, {KEY: self.original}, {KEY: raw}):
                raise ValueError("stale_draft")
            self.original, self.saved = raw, proposal
            self.pending = replace(self.pending, enabled=proposal.enabled) if enabled is not None else proposal
            notice = _t("text.custodio.saved")
        except Exception:
            pass
        finally:
            self.busy = False
            self.sync()
        await interaction.edit_original_response(content=self.summary() + "\n\n" + str(notice), view=self, embed=None)

    async def save(self, interaction):
        await self.persist(interaction)

    async def activate(self, interaction):
        await self.persist(interaction, enabled=True)

    async def pause(self, interaction):
        await self.persist(interaction, enabled=False)

    async def discard(self, interaction):
        if await self.wait_for_save(interaction):
            return
        self.original = self.parent.get_setting(self.guild_id, KEY)
        self.saved = ObservePolicy.decode(self.original, self.snapshot)
        self.pending = self.saved
        self.sync()
        await interaction.response.edit_message(content=self.summary(), view=self, embed=None)

    async def back(self, interaction):
        if await self.wait_for_save(interaction):
            return
        self.parent._sync_controls()
        await interaction.response.edit_message(content=self.parent.summary(), view=self.parent, embed=None)
