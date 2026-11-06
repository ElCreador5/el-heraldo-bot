"""Configuration of opt-in verification role restoration for the main bot.

A draft never writes to SQLite until the administrator confirms Save.
"""
from __future__ import annotations

import discord


LABELS = {
    "es-419": {
        "heading": "**Verificación · Restaurar roles al reingresar**",
        "help": "Solo recupera un rol de personalidad o el rol de edad permitido tras una salida voluntaria verificada. No restaura permisos elevados. Los registros vencen después de 30 días. Requiere acceso al registro de auditoría.",
        "active": "Activada", "paused": "Desactivada",
        "status": "Estado: **{status}**",
        "draft": "Cambio pendiente: **{status}**",
        "toggle": "Activar / Pausar", "save": "Guardar cambios",
        "discard": "Descartar cambios", "back": "Volver", "close": "Cerrar",
        "confirm": "Confirmar cambios", "cancel": "Volver",
        "prompt": "Confirma para aplicar esta configuración.",
        "conflict": "La configuración cambió durante la edición. Ábrela nuevamente.",
        "saved": "Configuración guardada.", "denied": "Acceso denegado.",
    },
    "en-US": {
        "heading": "**Verification · Restore roles on rejoin**",
        "help": "Restores only an allowed personality or age-verification role after a verified voluntary departure. Elevated permissions are never restored. Snapshots expire after 30 days. Audit-log access is required.",
        "active": "Enabled", "paused": "Disabled",
        "status": "Status: **{status}**",
        "draft": "Pending change: **{status}**",
        "toggle": "Enable / Pause", "save": "Save changes",
        "discard": "Discard changes", "back": "Back", "close": "Close",
        "confirm": "Confirm changes", "cancel": "Back",
        "prompt": "Confirm to apply this setting.",
        "conflict": "Settings changed while editing. Open the panel again.",
        "saved": "Setting saved.", "denied": "Access denied.",
    },
    "pt-BR": {
        "heading": "**Verificação · Restaurar cargos ao retornar**",
        "help": "Restaura somente um cargo permitido de personalidade ou verificação de idade após saída voluntária confirmada. Nunca restaura permissões elevadas. Os registros expiram em 30 dias. Requer acesso ao registro de auditoria.",
        "active": "Ativado", "paused": "Desativado",
        "status": "Estado: **{status}**",
        "draft": "Alteração pendente: **{status}**",
        "toggle": "Ativar / Pausar", "save": "Salvar alterações",
        "discard": "Descartar alterações", "back": "Voltar", "close": "Fechar",
        "confirm": "Confirmar alterações", "cancel": "Voltar",
        "prompt": "Confirme para aplicar esta configuração.",
        "conflict": "A configuração mudou durante a edição. Abra o painel novamente.",
        "saved": "Configuração salva.", "denied": "Acesso negado.",
    }
}


class RejoinEditor(discord.ui.View):
    def __init__(self, host, guild_id, owner_id):
        super().__init__(timeout=900)
        self.host, self.guild_id, self.owner_id = host, guild_id, owner_id
        self.locale = host.get("guild_language", lambda gid: "es-419")(guild_id)
        self.original = host["guild_config_get"](guild_id, "verified_rejoin_restore_enabled") == "1"
        self.pending = self.original
        for component, name in ((self.toggle,"toggle"),(self.save,"save"),
                                (self.discard,"discard"),(self.back,"back"),
                                (self.close,"close")):
            component.label = self.t(name)
        self.sync_buttons()

    def t(self, key, **values):
        return LABELS.get(self.locale, LABELS["es-419"])[key].format(**values)

    async def interaction_check(self, interaction):
        if (interaction.guild is None or interaction.guild.id != self.guild_id
                or interaction.user.id != self.owner_id
                or not getattr(interaction.user.guild_permissions, "manage_guild", False)):
            await interaction.response.send_message(self.t("denied"), ephemeral=True)
            return False
        return True

    def sync_buttons(self):
        self.save.disabled = self.discard.disabled = self.original == self.pending

    def summary(self):
        state = self.t("active" if self.original else "paused")
        text = self.t("heading") + "\n\n" + self.t("help") + "\n\n" + self.t("status", status=state)
        if self.pending != self.original:
            text += "\n" + self.t("draft", status=self.t("active" if self.pending else "paused"))
        return text

    @discord.ui.button(label="Activar / Pausar", style=discord.ButtonStyle.primary, row=0)
    async def toggle(self, interaction, button):
        self.pending = not self.pending
        self.sync_buttons()
        await interaction.response.edit_message(content=self.summary(), view=self)

    @discord.ui.button(label="Guardar cambios", style=discord.ButtonStyle.success, row=0)
    async def save(self, interaction, button):
        if self.pending == self.original:
            return await interaction.response.send_message(self.t("saved"), ephemeral=True)
        confirm = RejoinConfirm(self)
        await interaction.response.edit_message(
            content=self.summary() + "\n\n" + self.t("prompt"), view=confirm)

    @discord.ui.button(label="Descartar cambios", style=discord.ButtonStyle.secondary, row=0)
    async def discard(self, interaction, button):
        self.pending = self.original
        self.sync_buttons()
        await interaction.response.edit_message(content=self.summary(), view=self)

    @discord.ui.button(label="Volver", style=discord.ButtonStyle.secondary, row=1)
    async def back(self, interaction, button):
        if self.pending != self.original:
            return await interaction.response.send_message(self.t("prompt"), ephemeral=True)
        view = self.host["HeraldoVerificationHubView"](self.guild_id, self.owner_id)
        await interaction.response.edit_message(
            content="**El Heraldo · Verification**", embed=None, view=view)

    @discord.ui.button(label="Cerrar", style=discord.ButtonStyle.danger, row=1)
    async def close(self, interaction, button):
        self.stop()
        from panel_navigation import dismiss_panel
        await dismiss_panel(interaction)


class RejoinConfirm(discord.ui.View):
    def __init__(self, editor):
        super().__init__(timeout=180)
        self.editor = editor
        self.confirm.label = editor.t("confirm")
        self.back.label = editor.t("cancel")

    async def interaction_check(self, interaction):
        return await self.editor.interaction_check(interaction)

    @discord.ui.button(label="Confirmar cambios", style=discord.ButtonStyle.success, row=0)
    async def confirm(self, interaction, button):
        editor = self.editor
        current = editor.host["guild_config_get"](
            editor.guild_id, "verified_rejoin_restore_enabled") == "1"
        if current != editor.original:
            return await interaction.response.send_message(
                editor.t("conflict"), ephemeral=True)
        editor.host["guild_config_set"](
            editor.guild_id, "verified_rejoin_restore_enabled",
            "1" if editor.pending else "0")
        editor.original = editor.pending
        editor.sync_buttons()
        self.stop()
        await interaction.response.edit_message(
            content=editor.t("saved") + "\n\n" + editor.summary(),
            view=editor)

    @discord.ui.button(label="Volver", style=discord.ButtonStyle.secondary, row=0)
    async def back(self, interaction, button):
        self.stop()
        await interaction.response.edit_message(
            content=self.editor.summary(), view=self.editor)


def create_panel(host, guild_id, owner_id):
    view = RejoinEditor(host, guild_id, owner_id)
    return view.summary(), view
