"""Configuración única de destinatarios de Sugerencias en /setup -> Moderación.

Las selecciones son un borrador: ninguna mutación se realiza antes de
Guardar cambios -> Confirmar cambios. Mantiene la base de datos existente.
"""
import discord

from heraldo_i18n import DEFAULT_LOCALE

LANG = {
    "es-419": {
        "choose_reviewer": "Seleccionar revisor para añadir o quitar",
        "owner_exclude": "Excluir dueño de los avisos",
        "owner_include": "Incluir dueño en los avisos",
        "remove_reviewer": "Quitar revisor seleccionado",
        "save": "Guardar cambios",
        "discard": "Descartar cambios",
        "back": "Volver",
        "confirm": "Confirmar cambios",
        "none": "Ninguno",
        "not_configured": "No configurado",
        "yes": "Sí",
        "negative": "No",
        "summary": "**Moderación → Sugerencias**\nCanal del panel: {channel}\nNotificar al propietario: {owner}\nRevisores: {reviewers}\nSelecciona un miembro para añadirlo como revisor o quitarlo con el botón correspondiente. Nada se guarda hasta confirmar.",
        "pending": "**Cambios sin guardar**",
        "choose_member": "Selecciona un miembro.",
        "check_failed": "No pude comprobar ese miembro.",
        "bots_denied": "Los bots no pueden revisar sugerencias.",
        "choose_existing": "Selecciona un revisor existente.",
        "nothing_to_save": "No hay cambios pendientes.",
        "confirm_question": "¿Confirmas estos cambios?",
        "changed_elsewhere": "La configuración cambió desde que abriste el panel. Vuelve a abrirlo.",
        "cannot_verify_reviewer": "No pude comprobar uno de los revisores. No se guardaron cambios.",
        "bot_cannot_be_reviewer": "Un bot no puede ser revisor. No se guardaron cambios.",
        "saved": "Cambios guardados."
    },
    "en-US": {
        "choose_reviewer": "Select reviewer to add or remove",
        "owner_exclude": "Exclude owner from notifications",
        "owner_include": "Include owner in notifications",
        "remove_reviewer": "Remove selected reviewer",
        "save": "Save changes",
        "discard": "Discard changes",
        "back": "Back",
        "confirm": "Confirm changes",
        "none": "None",
        "not_configured": "Not configured",
        "yes": "Yes",
        "negative": "No",
        "summary": "**Moderation → Suggestions**\nPanel channel: {channel}\nNotify server owner: {owner}\nReviewers: {reviewers}\nSelect a member to add as a reviewer or remove with the corresponding button. Nothing is saved until confirmed.",
        "pending": "**Unsaved changes**",
        "choose_member": "Select a member.",
        "check_failed": "Could not verify that member.",
        "bots_denied": "Bots cannot review suggestions.",
        "choose_existing": "Select an existing reviewer.",
        "nothing_to_save": "No pending changes.",
        "confirm_question": "Confirm these changes?",
        "changed_elsewhere": "Settings changed since you opened this panel. Reopen it.",
        "cannot_verify_reviewer": "Could not verify one of the reviewers. No changes were saved.",
        "bot_cannot_be_reviewer": "A bot cannot be a reviewer. No changes were saved.",
        "saved": "Changes saved."
    },
    "pt-BR": {
        "choose_reviewer": "Selecionar revisor para adicionar ou remover",
        "owner_exclude": "Excluir proprietário das notificações",
        "owner_include": "Incluir proprietário nas notificações",
        "remove_reviewer": "Remover revisor selecionado",
        "save": "Salvar alterações",
        "discard": "Descartar alterações",
        "back": "Voltar",
        "confirm": "Confirmar alterações",
        "none": "Nenhum",
        "not_configured": "Não configurado",
        "yes": "Sim",
        "negative": "Não",
        "summary": "**Moderação → Sugestões**\nCanal do painel: {channel}\nNotificar proprietário: {owner}\nRevisores: {reviewers}\nSelecione um membro para adicionar como revisor ou remover com o botão correspondente. Nada é salvo até confirmar.",
        "pending": "**Alterações não salvas**",
        "choose_member": "Selecione um membro.",
        "check_failed": "Não foi possível verificar esse membro.",
        "bots_denied": "Bots não podem revisar sugestões.",
        "choose_existing": "Selecione um revisor existente.",
        "nothing_to_save": "Não há alterações pendentes.",
        "confirm_question": "Confirma estas alterações?",
        "changed_elsewhere": "As configurações mudaram desde que você abriu este painel. Abra-o novamente.",
        "cannot_verify_reviewer": "Não foi possível verificar um dos revisores. Nenhuma alteração foi salva.",
        "bot_cannot_be_reviewer": "Um bot não pode ser revisor. Nenhuma alteração foi salva.",
        "saved": "Alterações salvas."
    }
}

def tr(host, guild_id, key, **values):
    locale = host["guild_language"](guild_id)
    return LANG.get(locale, LANG[DEFAULT_LOCALE])[key].format(**values)


class SuggestionsSetupView(discord.ui.View):
    def __init__(self, host, guild_id: int, owner_id: int):
        super().__init__(timeout=900)
        self.host, self.guild_id, self.owner_id = host, guild_id, owner_id
        self.original_owner = bool(host["suggestion_owner_enabled"](guild_id))
        self.original_reviewers = set(host["suggestion_reviewer_ids"](guild_id))
        self.pending_owner = self.original_owner
        self.pending_reviewers = set(self.original_reviewers)
        self.selected_id = None
        users = discord.ui.UserSelect(
            placeholder=self.tr("choose_reviewer"), min_values=1,
            max_values=1, row=0)
        users.callback = self.pick_user
        self.add_item(users)
        self._sync()

    def tr(self, key, **values):
        return tr(self.host, self.guild_id, key, **values)

    async def interaction_check(self, interaction):
        return await self.host["configuration_access"](
            interaction, self.guild_id, self.owner_id)

    def _dirty(self):
        return (self.pending_owner != self.original_owner or
                self.pending_reviewers != self.original_reviewers)

    def _sync(self):
        self.toggle_owner.label = self.tr("owner_exclude" if self.pending_owner else "owner_include")
        self.remove_reviewer.label = self.tr("remove_reviewer")
        self.save_changes.label = self.tr("save")
        self.discard_changes.label = self.tr("discard")
        self.back.label = self.tr("back")
        self.remove_reviewer.disabled = self.selected_id not in self.pending_reviewers
        self.save_changes.disabled = not self._dirty()
        self.discard_changes.disabled = not self._dirty()

    def to_components(self):
        self._sync()
        return super().to_components()

    def summary(self, guild):
        ids = sorted(self.pending_reviewers)
        reviewers = ", ".join(f"<@{user_id}>" for user_id in ids) if ids else self.tr("none")
        channel_id = self.host["suggestion_get_channel_id"](self.guild_id)
        channel = f"<#{channel_id}>" if channel_id else self.tr("not_configured")
        content = self.tr("summary", channel=channel,
                          owner=self.tr("yes" if self.pending_owner else "negative"),
                          reviewers=reviewers)
        return content + ("\n\n" + self.tr("pending") if self._dirty() else "")

    async def pick_user(self, interaction):
        values = (interaction.data or {}).get("values", [])
        if not values:
            await interaction.response.send_message(self.tr("choose_member"), ephemeral=True)
            return
        user_id = int(values[0])
        member = interaction.guild.get_member(user_id)
        if member is None:
            try:
                member = await interaction.guild.fetch_member(user_id)
            except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                await interaction.response.send_message(
                    self.tr("check_failed"), ephemeral=True)
                return
        if member.bot:
            await interaction.response.send_message(
                self.tr("bots_denied"), ephemeral=True)
            return
        self.selected_id = user_id
        self.pending_reviewers.add(user_id)
        self._sync()
        await interaction.response.edit_message(content=self.summary(interaction.guild), view=self)

    @discord.ui.button(label=LANG["es-419"]["owner_include"], style=discord.ButtonStyle.secondary, row=1)
    async def toggle_owner(self, interaction, button):
        self.pending_owner = not self.pending_owner
        self._sync()
        await interaction.response.edit_message(content=self.summary(interaction.guild), view=self)

    @discord.ui.button(label=LANG["es-419"]["remove_reviewer"], style=discord.ButtonStyle.secondary, row=1)
    async def remove_reviewer(self, interaction, button):
        if self.selected_id not in self.pending_reviewers:
            await interaction.response.send_message(self.tr("choose_existing"), ephemeral=True)
            return
        self.pending_reviewers.discard(self.selected_id)
        self._sync()
        await interaction.response.edit_message(content=self.summary(interaction.guild), view=self)

    @discord.ui.button(label=LANG["es-419"]["save"], style=discord.ButtonStyle.success, row=2)
    async def save_changes(self, interaction, button):
        if not self._dirty():
            await interaction.response.send_message(self.tr("nothing_to_save"), ephemeral=True)
            return
        await interaction.response.edit_message(
            content=self.summary(interaction.guild) + "\n\n" + self.tr("confirm_question"),
            view=SuggestionsSetupConfirmView(self))

    @discord.ui.button(label=LANG["es-419"]["discard"], style=discord.ButtonStyle.danger, row=2)
    async def discard_changes(self, interaction, button):
        self.pending_owner = self.original_owner
        self.pending_reviewers = set(self.original_reviewers)
        self.selected_id = None
        self._sync()
        await interaction.response.edit_message(content=self.summary(interaction.guild), view=self)

    @discord.ui.button(label=LANG["es-419"]["back"], style=discord.ButtonStyle.secondary, row=2)
    async def back(self, interaction, button):
        view = self.host["HeraldoModerationSetupView"](self.guild_id, self.owner_id)
        await interaction.response.edit_message(
            content=self.host["_t"]('text.da10e9d8927c80'), embed=None, view=view)


class SuggestionsSetupConfirmView(discord.ui.View):
    def __init__(self, editor: SuggestionsSetupView):
        super().__init__(timeout=300)
        self.editor = editor
        self.finished = False
        self.owner = editor.pending_owner
        self.reviewers = set(editor.pending_reviewers)
        self.confirm.label = editor.tr("confirm")
        self.back.label = editor.tr("back")

    async def interaction_check(self, interaction):
        return not self.finished and await self.editor.interaction_check(interaction)

    @discord.ui.button(label=LANG["es-419"]["confirm"], style=discord.ButtonStyle.success)
    async def confirm(self, interaction, button):
        editor = self.editor
        h, guild_id = editor.host, editor.guild_id
        if (bool(h["suggestion_owner_enabled"](guild_id)) != editor.original_owner
                or set(h["suggestion_reviewer_ids"](guild_id)) != editor.original_reviewers):
            await interaction.response.send_message(
                editor.tr("changed_elsewhere"), ephemeral=True)
            return
        for user_id in sorted(self.reviewers - editor.original_reviewers):
            member = interaction.guild.get_member(user_id)
            if member is None:
                try:
                    member = await interaction.guild.fetch_member(user_id)
                except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                    await interaction.response.send_message(
                        editor.tr("cannot_verify_reviewer"),
                        ephemeral=True)
                    return
            if member.bot:
                await interaction.response.send_message(
                    editor.tr("bot_cannot_be_reviewer"), ephemeral=True)
                return
        await interaction.response.defer()
        if self.owner != editor.original_owner:
            h["suggestion_set_owner_enabled"](guild_id, self.owner)
        for user_id in sorted(editor.original_reviewers - self.reviewers):
            h["suggestion_remove_reviewer"](guild_id, user_id)
        for user_id in sorted(self.reviewers - editor.original_reviewers):
            h["suggestion_add_reviewer"](guild_id, user_id)
        self.finished = True
        self.stop()
        editor.original_owner = self.owner
        editor.original_reviewers = set(self.reviewers)
        editor.pending_owner = self.owner
        editor.pending_reviewers = set(self.reviewers)
        editor._sync()
        await interaction.edit_original_response(
            content=editor.summary(interaction.guild) + "\n\n" + editor.tr("saved"),
            view=editor)

    @discord.ui.button(label=LANG["es-419"]["back"], style=discord.ButtonStyle.secondary)
    async def back(self, interaction, button):
        self.finished = True
        self.stop()
        await interaction.response.edit_message(
            content=self.editor.summary(interaction.guild), view=self.editor)
