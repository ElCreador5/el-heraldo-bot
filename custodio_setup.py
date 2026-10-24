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
from custodio_reports import (
    SETTING_KEY, ReportChannelError, create_private_report_channel,
)


class CustodioSetupView(discord.ui.View):
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

        check_button = discord.ui.Button(
            label="Reglas del servidor", style=discord.ButtonStyle.primary, row=1)
        check_button.callback = self.check_rules
        self.add_item(check_button)

        report_button = discord.ui.Button(
            label="Reportes", style=discord.ButtonStyle.primary, row=3)
        report_button.callback = self.request_report_channel
        self.add_item(report_button)

        actions_button = discord.ui.Button(
            label="Acciones", style=discord.ButtonStyle.primary, row=1)
        actions_button.callback = self.open_rule_actions
        self.add_item(actions_button)

        for caption, description, placement in (
            ("Detección", "Detección de texto, imágenes similares, saturación y patrones colectivos. Pendiente de conexión con detectores verificables.", 1),
            ("Exenciones", "Exenciones por roles, reglas y canales. El propietario y los moderadores no reciben sanciones automáticas. Configuración avanzada pendiente.", 3),
            ("Integraciones", "Advertencias centralizadas, Condenas y revisiones. Las conexiones disciplinarias todavía no están activadas.", 3),
        ):
            nav = discord.ui.Button(label=caption, style=discord.ButtonStyle.secondary, row=placement)
            async def open_section(interaction: discord.Interaction, text=description, heading=caption):
                view = CustodioInformationView(self, heading, text)
                await interaction.response.edit_message(content=view.summary(), view=view, embed=None)
            nav.callback = open_section
            self.add_item(nav)

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
        self._sync_controls()

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
            "Modo Custodio ayuda a mantener una comunidad segura, organizada y respetuosa. "
            "Se guía por las reglas del servidor y busca actuar con justicia y proporcionalidad. "
            "Prioriza orientar antes de sancionar cuando sea posible: es amable, paciente y discreto, "
            "pero firme ante reincidencias o faltas graves. No inventa prohibiciones: "
            "ante una norma ambigua solicita aclaración administrativa. "
            "Su principio es educar cuando sea posible, corregir cuando sea necesario "
            "y sancionar solo cuando esté justificado.",
            "",
            "**Requisito:** las Reglas del servidor (Server Rules) deben estar activas. "
            "Abre «Reglas del servidor» para consultar su disponibilidad manualmente; "
            "esta acción no activa IA ni sanciones.",
            "",
            display_preferences(existing),
            "**Canal de reportes:** " + (
                "Vinculado (acceso sujeto a verificación)"
                if self.get_setting(self.guild_id, SETTING_KEY)
                else "No configurado"
            ),
            "",
            "**Cambios pendientes:** " + (
                f"Sensibilidad → {DISPLAY[KEY_SENSITIVITY][self.pending_sensitivity]}"
                if self.pending_sensitivity != existing.sensitivity
                else "Preferencias predeterminadas sin guardar."
                if self._raw_changes() else "Ninguno."
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
        """Consulta manual del reglamento, sin ejecución de inteligencia artificial."""
        await interaction.response.defer()
        token = os.environ.get("DISCORD_TOKEN", "")
        try:
            snapshot = await load_server_rules(self.guild_id, token)
        except (RulesUnavailable, ValueError) as exc:
            reason = exc.reason if isinstance(exc, RulesUnavailable) else "token_unavailable"
            details = {
                "screening_disabled_or_unknown": "Active las Reglas del servidor en Discord antes de configurar Custodio.",
                "screening_disabled": "Active las Reglas del servidor en Discord antes de configurar Custodio.",
                "rules_empty": "Las Reglas del servidor están vacías. Defina las reglas en Discord.",
                "verification_unavailable": "Discord no permitió consultar las reglas. No se pueden aprobar ni interpretar.",
            }
            explanation = details.get(reason, "No fue posible verificar las reglas oficiales de Discord.")
            await interaction.edit_original_response(
                content=self.summary() + "\\n\\n**Reglas del servidor no disponibles.** " + explanation,
                view=self, embed=None,
            )
            return
        view = CustodioRulesView(self, snapshot)
        await interaction.edit_original_response(content=view.summary(), view=view, embed=None)

    async def open_rule_actions(self, interaction: discord.Interaction):
        """Abre las plantillas por categoría sin guardar ni sancionar."""
        from custodio_rule_actions_setup import CustodioRuleActionsView
        view = CustodioRuleActionsView(self)
        await interaction.response.edit_message(
            content=view.summary(), view=view, embed=None,
        )

    async def request_report_channel(self, interaction: discord.Interaction):
        """Solo abre confirmación; no crea canales ni cambia SQLite."""
        existing = self.get_setting(self.guild_id, SETTING_KEY)
        if self.set_setting is None:
            await interaction.response.send_message(
                "El canal de reportes no se puede configurar en esta instancia.",
                ephemeral=True,
            )
            return
        if existing:
            await interaction.response.send_message(
                "Ya existe una referencia a un canal de reportes. "
                "No se creará otro automáticamente. Revise el canal existente.",
                ephemeral=True,
            )
            return
        view = CustodioReportChannelConfirmView(self)
        await interaction.response.edit_message(
            content="**Modo Custodio · Crear reportes📢**\n\n"
                    "Se creará un canal privado, oculto para miembros normales "
                    "y accesible únicamente al bot y al equipo de moderación "
                    "que tenga permisos adecuados.\n\n"
                    "**No se enviarán observaciones todavía:** el análisis continuo "
                    "no está activado. La creación del canal no sanciona ni registra "
                    "mensajes antiguos.\n\n"
                    "Confirme para crear el canal o cancele sin realizar cambios.",
            view=view, embed=None,
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

class CustodioReportChannelConfirmView(discord.ui.View):
    """Confirmación NH independiente del guardado de preferencias."""

    def __init__(self, parent: CustodioSetupView):
        super().__init__(timeout=300)
        self.parent = parent
        self.done = False

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if self.done:
            await interaction.response.send_message(
                "La solicitud ya se procesó. Abra de nuevo el panel.",
                ephemeral=True,
            )
            return False
        return await self.parent.access_check(
            interaction, self.parent.guild_id, self.parent.owner_id)

    @discord.ui.button(label="Confirmar creación", style=discord.ButtonStyle.success)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        if guild is None or guild.id != self.parent.guild_id:
            await interaction.response.send_message("Servidor no válido.", ephemeral=True)
            return
        if not interaction.user.guild_permissions.manage_channels:
            await interaction.response.send_message(
                "Se necesita el permiso Gestionar canales para esta operación.",
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
                content="No se completó la creación del canal privado. "
                        "Compruebe permisos y configuración. "
                        + (str(exc) if isinstance(exc, ReportChannelError) else "Error de persistencia."),
                view=None,
            )
            return
        self.stop()
        self.parent._sync_controls()
        await interaction.edit_original_response(
            content=self.parent.summary() + "\n\n"
                    f"**Canal de reportes:** {channel.mention} "
                    + ("creado y vinculado." if created else "reutilizado de forma segura.")
                    + "\nCustodio sigue sin supervisión ni sanciones automáticas.",
            view=self.parent, embed=None,
        )

    @discord.ui.button(label="Cancelar", style=discord.ButtonStyle.danger)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.done = True
        self.stop()
        self.parent._sync_controls()
        await interaction.response.edit_message(
            content=self.parent.summary() + "\n\nNo se creó ningún canal.",
            view=self.parent, embed=None,
        )


class CustodioRulesView(discord.ui.View):
    """Consulta de reglas obtenidas: IA explícitamente desactivada por defecto."""

    def __init__(self, parent: CustodioSetupView, snapshot):
        super().__init__(timeout=300)
        self.parent = parent
        self.snapshot = snapshot

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return await self.parent.access_check(interaction, self.parent.guild_id, self.parent.owner_id)

    def summary(self) -> str:
        rules = "\\n".join(
            f"**{index}.** {rule[:600]}" + ("…" if len(rule) > 600 else "")
            for index, rule in enumerate(self.snapshot.rules, 1)
        )
        # Mensajes de Discord tienen un límite de 2000 caracteres.
        if len(rules) > 1300:
            rules = rules[:1290].rsplit("\\n", 1)[0] + "\\n… Consulte las restantes en Discord."
        return (
            "**Modo Custodio · Reglas del servidor**\\n\\n"
            f"**Estado:** activadas · **Reglas:** {self.snapshot.count}\\n"
            f"**Revisión:** {self.snapshot.revision[:12]}\\n\\n"
            + rules + "\\n\\n"
            "**Análisis de ambigüedades:** no configurado. "
            "La IA solo se ejecutará mediante una acción administrativa manual "
            "cuando se disponga de un modelo comprobado. "
            "Ninguna regla se modifica ni se sanciona desde este panel."
        )

    @discord.ui.button(label="Analizar reglas", style=discord.ButtonStyle.secondary, row=0)
    async def analyze_rules(self, interaction: discord.Interaction, button: discord.ui.Button):
        from custodio_ai_config import CustodioAIConfig, prepare_rule_analysis
        # Nunca se pasa texto a un servicio externo; IA permanece apagada.
        result = prepare_rule_analysis(
            config=CustodioAIConfig(), rules_active=True,
            administrator_requested=True, text="\\n".join(self.snapshot.rules),
        )
        if result["status"] != "manual_review":
            raise RuntimeError("El modo seguro de IA no se ha respetado")
        await interaction.response.edit_message(
            content=self.summary() + "\\n\\n**Análisis pendiente:** "
                    "todavía no hay modelo gratuito instalado y verificado. "
                    "Puede revisar las ambigüedades manualmente; "
                    "no se ha enviado ningún texto a una IA.",
            view=self, embed=None,
        )

    @discord.ui.button(label="Volver", style=discord.ButtonStyle.secondary, row=0)
    async def back(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.stop()
        self.parent._sync_controls()
        await interaction.response.edit_message(
            content=self.parent.summary(), view=self.parent, embed=None,
        )


class CustodioInformationView(discord.ui.View):
    """Submenú informativo hasta que sus controles estén implementados."""

    def __init__(self, parent: CustodioSetupView, title: str, information: str):
        super().__init__(timeout=300)
        self.parent = parent
        self.title = title
        self.information = information

    def summary(self):
        return (
            f"**El Heraldo · AutoMod · Modo Custodio · {self.title}**\\n\\n"
            f"{self.information}\\n\\n"
            "No hay cambios que guardar ni acciones automáticas activas en este apartado."
        )

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return await self.parent.access_check(interaction, self.parent.guild_id, self.parent.owner_id)

    @discord.ui.button(label="Volver", style=discord.ButtonStyle.secondary)
    async def back(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.stop()
        self.parent._sync_controls()
        await interaction.response.edit_message(content=self.parent.summary(), view=self.parent, embed=None)
