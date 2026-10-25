"""Vista de /setup de Modo Custodio, sin clasificador ni sanciones.

El modo Observar todavía no está en funcionamiento: estas preferencias no
activan supervisión. Todos los cambios requieren una segunda confirmación.
"""
from __future__ import annotations
from heraldo_i18n import text as _t, guild_context as _i18n_context, use_guild as _i18n_guild
from heraldo_i18n import join_text as _i18n_join

import os
from typing import Callable, Any

import discord

from custodio_preferences import (
    DEFAULTS, DISPLAY, KEY_SENSITIVITY,
    CustodioPreferences, display_preferences, load_preferences, validate_settings,
)
from custodio_source import load_server_rules
from custodio_core import RulesUnavailable
from custodio_reports import (
    SETTING_KEY, ReportChannelError, create_private_report_channel,
)


class CustodioSetupView(discord.ui.View):
    @_i18n_context
    def __init__(
        self, guild_id: int, owner_id: int, *,
        get_setting: Callable[[int, str], str | None],
        save_atomic: Callable[..., bool],
        access_check: Callable[..., Any],
        parent_factory: Callable[[], discord.ui.View],
        set_setting: Callable[[int, str, str], None] | None = None,
    ):
        super().__init__(timeout=600)
        self.guild_id = guild_id
        self.owner_id = owner_id
        self.get_setting = get_setting
        self.save_atomic = save_atomic
        self.set_setting = set_setting
        self.access_check = access_check
        self.parent_factory = parent_factory
        self.pending_sensitivity = load_preferences(get_setting, guild_id).sensitivity

        select = discord.ui.Select(
            placeholder=_t('text.c385fb7beb311c'),
            row=0, min_values=1, max_values=1,
            options=[
                discord.SelectOption(label=_t('text.4227fbef304d05'), value="conservative",
                    description=_t('text.f379ac09a64f34')),
                discord.SelectOption(label=_t('text.911d1179bfed6c'), value="balanced",
                    description=_t('text.1b6bb21bd0b69b')),
                discord.SelectOption(label=_t('text.87956eb4fc2585'), value="strict",
                    description=_t('text.0bfad45b9215ae')),
            ],
        )
        select.callback = self.choose_sensitivity
        self.selector = select
        self.add_item(select)

        check_button = discord.ui.Button(
            label=_t('text.10dde311ff3ffe'), style=discord.ButtonStyle.primary, row=1)
        check_button.callback = self.check_rules
        self.add_item(check_button)

        report_button = discord.ui.Button(
            label=_t('text.772ffb657276d9'), style=discord.ButtonStyle.primary, row=3)
        report_button.callback = self.request_report_channel
        self.add_item(report_button)

        actions_button = discord.ui.Button(
            label=_t('text.fb89a30ba7f64d'), style=discord.ButtonStyle.primary, row=1)
        actions_button.callback = self.open_rule_actions
        self.add_item(actions_button)

        for caption, description, placement in (
            (_t('text.2cc32e458872c6'), _t('text.7cb87385497004'), 1),
            (_t('text.3e9bb29a0832fc'), _t('text.8348e279630516'), 3),
            (_t('text.5beed665025da3'), _t('text.5aa657464cd546'), 3),
        ):
            nav = discord.ui.Button(label=caption, style=discord.ButtonStyle.secondary, row=placement)
            @_i18n_context
            async def open_section(interaction: discord.Interaction, text=description, heading=caption):
                view = CustodioInformationView(self, heading, text)
                await interaction.response.edit_message(content=view.summary(), view=view, embed=None)
            nav.callback = open_section
            self.add_item(nav)

        save_button = discord.ui.Button(
            label=_t('text.14bdfaf2face3a'), style=discord.ButtonStyle.success, row=2)
        save_button.callback = self.save_changes
        self.save_button = save_button
        self.add_item(save_button)

        discard_button = discord.ui.Button(
            label=_t('text.80ca383e9c8d3e'), style=discord.ButtonStyle.danger, row=2)
        discard_button.callback = self.discard_changes
        self.discard_button = discard_button
        self.add_item(discard_button)

        back_button = discord.ui.Button(
            label=_t('text.ab26ae7bca3621'), style=discord.ButtonStyle.secondary, row=2)
        back_button.callback = self.back
        self.add_item(back_button)
        self._sync_controls()

    @_i18n_context
    def _sync_controls(self) -> None:
        for option in self.selector.options:
            option.default = option.value == self.pending_sensitivity
        current = load_preferences(self.get_setting, self.guild_id).sensitivity
        self.save_button.disabled = not self._raw_changes()
        self.discard_button.disabled = self.pending_sensitivity == current

    @_i18n_context
    def _raw_changes(self) -> dict[str, str]:
        proposal = validate_settings(CustodioPreferences(
            sensitivity=self.pending_sensitivity).as_settings())
        return {k: v for k, v in proposal.items()
                if self.get_setting(self.guild_id, k) != v}

    @_i18n_context
    def summary(self) -> str:
        existing = load_preferences(self.get_setting, self.guild_id)
        lines = [
            _t('text.d4f534b0b43247'),
            "",
            _t('text.bfefbb40e50c94'),
            "",
            _t('text.1b962bfe039d02'),
            "",
            display_preferences(existing),
            _t('text.3e707d6f729815') + (
                _t('text.f9892f3ecae073')
                if self.get_setting(self.guild_id, SETTING_KEY)
                else _t('text.67db68445a607d')
            ),
            "",
            _t('text.c364369f1d9925') + (
                _t('text.ac661742a1c744', p0=f'{DISPLAY[KEY_SENSITIVITY][self.pending_sensitivity]}')
                if self.pending_sensitivity != existing.sensitivity
                else _t('text.196bb0724613d5')
                if self._raw_changes() else _t('common.none_sentence')
            ),
            "",
            _t('text.b74d22c0bda1ce'),
        ]
        return _i18n_join("\n", lines)

    @_i18n_context
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return await self.access_check(interaction, self.guild_id, self.owner_id)

    @_i18n_context
    async def choose_sensitivity(self, interaction: discord.Interaction):
        self.pending_sensitivity = self.selector.values[0]
        self._sync_controls()
        await interaction.response.edit_message(content=self.summary(), view=self, embed=None)

    @_i18n_context
    async def check_rules(self, interaction: discord.Interaction):
        """Consulta manual del reglamento, sin ejecución de inteligencia artificial."""
        await interaction.response.defer()
        token = os.environ.get("DISCORD_TOKEN", "")
        try:
            snapshot = await load_server_rules(self.guild_id, token)
        except (RulesUnavailable, ValueError) as exc:
            reason = exc.reason if isinstance(exc, RulesUnavailable) else "token_unavailable"
            details = {
                "screening_disabled_or_unknown": _t('text.d518f58185fcdf'),
                "screening_disabled": _t('text.d518f58185fcdf'),
                "rules_empty": _t('text.6a86ca315f5e7f'),
                "verification_unavailable": _t('text.e306d46cbb0040'),
            }
            explanation = details.get(reason, _t('text.b28b40091d7015'))
            await interaction.edit_original_response(
                content=self.summary() + _t('text.6b6251cb2db9b9') + explanation,
                view=self, embed=None,
            )
            return
        view = CustodioRulesView(self, snapshot)
        await interaction.edit_original_response(content=view.summary(), view=view, embed=None)

    @_i18n_context
    async def open_rule_actions(self, interaction: discord.Interaction):
        """Carga únicamente reglas oficiales del servidor actual."""
        await interaction.response.defer(thinking=False)
        from custodio_server_rule_actions_setup import CustodioServerRuleActionsView
        try:
            snapshot = await load_server_rules(
                self.guild_id, os.environ.get("DISCORD_TOKEN", "")
            )
        except (RulesUnavailable, ValueError):
            await interaction.edit_original_response(
                content=self.summary() + _t('text.dbb413c4fa004b'),
                view=self, embed=None,
            )
            return
        view = CustodioServerRuleActionsView(self, snapshot)
        await interaction.edit_original_response(
            content=view.summary(), view=view, embed=None,
        )

    @_i18n_context
    async def request_report_channel(self, interaction: discord.Interaction):
        """Solo abre confirmación; no crea canales ni cambia SQLite."""
        existing = self.get_setting(self.guild_id, SETTING_KEY)
        if self.set_setting is None:
            await interaction.response.send_message(
                _t('text.66607603e19149'),
                ephemeral=True,
            )
            return
        if existing:
            view = CustodioInformationView(
                self, _t('text.772ffb657276d9'),
                _t('text.16aca8df1f3040'),
            )
            await interaction.response.edit_message(
                content=view.summary(), view=view, embed=None,
            )
            return
        view = CustodioReportChannelConfirmView(self)
        await interaction.response.edit_message(
            content=_t('text.15e01183b72751'),
            view=view, embed=None,
        )

    @_i18n_context
    async def save_changes(self, interaction: discord.Interaction):
        changes = self._raw_changes()
        if not changes:
            await interaction.response.send_message(
                _t('text.4c9e4a198ac444'),
                ephemeral=True,
            )
            return
        original = {k: self.get_setting(self.guild_id, k) for k in DEFAULTS}
        confirm = CustodioConfirmView(self, changes, original)
        await interaction.response.edit_message(
            content=(
                _t('text.dffce88b3c324d', p0=f'{DISPLAY[KEY_SENSITIVITY][self.pending_sensitivity]}')
            ),
            view=confirm, embed=None,
        )

    @_i18n_context
    async def discard_changes(self, interaction: discord.Interaction):
        self.pending_sensitivity = load_preferences(self.get_setting, self.guild_id).sensitivity
        self._sync_controls()
        await interaction.response.edit_message(content=self.summary(), view=self, embed=None)

    @_i18n_context
    async def back(self, interaction: discord.Interaction):
        await interaction.response.edit_message(
            content=_t('text.fb957b65618b1a'),
            embed=None, view=self.parent_factory(),
        )


class CustodioConfirmView(discord.ui.View):
    @_i18n_context
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

    @_i18n_context
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if self.done:
            await interaction.response.send_message(
                _t('text.3bb8672b373151'), ephemeral=True)
            return False
        return await self.parent.access_check(
            interaction, self.parent.guild_id, self.parent.owner_id)

    @discord.ui.button(label=_t('text.aadfff0cc172b1'), style=discord.ButtonStyle.success)
    @_i18n_context
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            ok = self.parent.save_atomic(
                self.parent.guild_id, self.original,
                self.changes,
            )
        except Exception:
            await interaction.response.send_message(
                _t('text.b48ad3f4f5377b'),
                ephemeral=True,
            )
            return
        if not ok:
            self.done = True
            self.stop()
            await interaction.response.edit_message(
                content=_t('text.55ed96514b3001'),
                view=None, embed=None,
            )
            return
        self.done = True
        self.stop()
        self.parent._sync_controls()
        await interaction.response.edit_message(
            content=self.parent.summary() + _t('text.d6404388cff88f'),
            view=self.parent, embed=None,
        )

    @discord.ui.button(label=_t('text.bb9dbb406dcbd5'), style=discord.ButtonStyle.danger)
    @_i18n_context
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.done = True
        self.stop()
        self.parent._sync_controls()
        await interaction.response.edit_message(
            content=self.parent.summary() + _t('text.f6ea8eb06aac7b'),
            view=self.parent, embed=None,
        )

class CustodioReportChannelConfirmView(discord.ui.View):
    """Confirmación NH independiente del guardado de preferencias."""

    @_i18n_context
    def __init__(self, parent: CustodioSetupView):
        super().__init__(timeout=300)
        self.parent = parent
        self.done = False

    @_i18n_context
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if self.done:
            await interaction.response.send_message(
                _t('text.2f5c8a7d8f9e4e'),
                ephemeral=True,
            )
            return False
        return await self.parent.access_check(
            interaction, self.parent.guild_id, self.parent.owner_id)

    @discord.ui.button(label=_t('text.8b43fae929eaa0'), style=discord.ButtonStyle.success)
    @_i18n_context
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        if guild is None or guild.id != self.parent.guild_id:
            await interaction.response.send_message(_t('text.2d0559112e6cc3'), ephemeral=True)
            return
        if not interaction.user.guild_permissions.manage_channels:
            await interaction.response.send_message(
                _t('text.2500449308a522'),
                ephemeral=True,
            )
            return
        self.done = True
        await interaction.response.defer(ephemeral=True)
        try:
            channel, created = await create_private_report_channel(
                guild, self.parent.get_setting,
                self.parent.set_setting,
            )
        except (ReportChannelError, OSError, ValueError) as exc:
            self.stop()
            await interaction.edit_original_response(
                content=_t('text.fb0dc2d7f2f0a1')
                        + (str(exc) if isinstance(exc, ReportChannelError) else _t('text.4e23a8fdd158a2')),
                view=None,
            )
            return
        self.stop()
        self.parent._sync_controls()
        await interaction.edit_original_response(
            content=self.parent.summary() + _t('text.308e703a90bc13', p0=f'{channel.mention}')
                    + (_t("common.created_linked") if created else _t('text.a1315642c3cc9a'))
                    + _t('text.e63a066c01112a'),
            view=self.parent, embed=None,
        )

    @discord.ui.button(label=_t('text.bb9dbb406dcbd5'), style=discord.ButtonStyle.danger)
    @_i18n_context
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.done = True
        self.stop()
        self.parent._sync_controls()
        await interaction.response.edit_message(
            content=self.parent.summary() + _t('text.52cc3d5caeb1e9'),
            view=self.parent, embed=None,
        )


class CustodioRulesView(discord.ui.View):
    """Consulta de reglas obtenidas: IA explícitamente desactivada por defecto."""

    @_i18n_context
    def __init__(self, parent: CustodioSetupView, snapshot):
        super().__init__(timeout=300)
        self.parent = parent
        self.snapshot = snapshot

    @_i18n_context
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return await self.parent.access_check(interaction, self.parent.guild_id, self.parent.owner_id)

    @_i18n_context
    def summary(self) -> str:
        rules = _i18n_join("\n", (
            f"**{index}.** {rule[:600]}" + ("…" if len(rule) > 600 else "")
            for index, rule in enumerate(self.snapshot.rules, 1)
        ))
        # Mensajes de Discord tienen un límite de 2000 caracteres.
        if len(rules) > 1300:
            rules = rules[:1290].rsplit("\n", 1)[0] + _t('text.233e756c692ec6')
        return (
            _t('text.c040284e65f9e2', p0=f'{self.snapshot.count}', p1=f'{self.snapshot.revision[:12]}')
            + rules + _t('text.3eaf2f7e758b56')
        )

    @discord.ui.button(label=_t('text.ba4c0deba27b34'), style=discord.ButtonStyle.secondary, row=0)
    @_i18n_context
    async def analyze_rules(self, interaction: discord.Interaction, button: discord.ui.Button):
        from custodio_ai_config import CustodioAIConfig, prepare_rule_analysis
        # Nunca se pasa texto a un servicio externo; IA permanece apagada.
        result = prepare_rule_analysis(
            config=CustodioAIConfig(), rules_active=True,
            administrator_requested=True, text=_i18n_join("\n", self.snapshot.rules),
        )
        if result["status"] != "manual_review":
            raise RuntimeError(_t('text.85ab1149c4ef10'))
        await interaction.response.edit_message(
            content=self.summary() + _t('text.b7334ef09fe43d'),
            view=self, embed=None,
        )

    @discord.ui.button(label=_t('text.ab26ae7bca3621'), style=discord.ButtonStyle.secondary, row=0)
    @_i18n_context
    async def back(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.stop()
        self.parent._sync_controls()
        await interaction.response.edit_message(
            content=self.parent.summary(), view=self.parent, embed=None,
        )


class CustodioInformationView(discord.ui.View):
    """Submenú informativo hasta que sus controles estén implementados."""

    @_i18n_context
    def __init__(self, parent: CustodioSetupView, title: str, information: str):
        super().__init__(timeout=300)
        self.parent = parent
        self.title = title
        self.information = information

    @_i18n_context
    def summary(self):
        return (
            _t('text.3f09b4c7e1a213', p0=f'{self.title}', p1=f'{self.information}')
        )

    @_i18n_context
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return await self.parent.access_check(interaction, self.parent.guild_id, self.parent.owner_id)

    @discord.ui.button(label=_t('text.ab26ae7bca3621'), style=discord.ButtonStyle.secondary)
    @_i18n_context
    async def back(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.stop()
        self.parent._sync_controls()
        await interaction.response.edit_message(content=self.parent.summary(), view=self.parent, embed=None)
