"""Configuración única de destinatarios de Sugerencias en /setup -> Moderación.

Las selecciones son un borrador: ninguna mutación se realiza antes de
Guardar cambios -> Confirmar cambios. Mantiene la base de datos existente.
"""
import discord

from heraldo_i18n import DEFAULT_LOCALE

LANG = {
    "es-419": {
        "channel_select": "Canal donde publicar el panel",
        "invalid_channel": "Selecciona un canal de texto válido.",
        "channel_permissions": "El bot necesita ver el canal, enviar mensajes, insertar enlaces y gestionar mensajes.",
        "channel_changed": "El canal seleccionado se publicará al confirmar el guardado.",
        "edit_panel": "Mensaje del panel",
        "publish_panel": "Publicar / actualizar panel",
        "publish_confirm": "¿Publicar o actualizar el panel de sugerencias en {channel}?",
        "publish_requires_save": "Guarda los cambios pendientes antes de publicar.",
        "publish_requires_channel": "Selecciona y guarda primero el canal del panel.",
        "publish_failed": "No pude publicar el panel. Comprueba los permisos y vuelve a intentarlo.",
        "publish_success": "Panel publicado o actualizado correctamente.",
        "move_warning": "No fue posible retirar el panel del canal anterior; revisa ese mensaje.",
        "save_failed": "No pude guardar la configuración; no se aplicaron los cambios de revisores.",
        "status_published": "Mensaje del panel: {state}",
        "published": "Publicado",
        "not_published": "Todavía sin publicar",
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
        "channel_select": "Channel to publish the panel",
        "invalid_channel": "Select a valid text channel.",
        "channel_permissions": "The bot needs permission to view, send, embed links and manage messages.",
        "channel_changed": "The panel will be published in the selected channel after confirming the save.",
        "edit_panel": "Panel message",
        "publish_panel": "Publish / update panel",
        "publish_confirm": "Publish or update the suggestions panel in {channel}?",
        "publish_requires_save": "Save the pending changes before publishing.",
        "publish_requires_channel": "Select and save the panel channel first.",
        "publish_failed": "Could not publish the panel. Check permissions and try again.",
        "publish_success": "Panel successfully published or updated.",
        "move_warning": "Could not remove the panel from the previous channel; check that message.",
        "save_failed": "Could not save the settings; reviewer changes were not applied.",
        "status_published": "Panel message: {state}",
        "published": "Published",
        "not_published": "Not yet published",
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
        "channel_select": "Canal para publicar o painel",
        "invalid_channel": "Selecione um canal de texto válido.",
        "channel_permissions": "O bot precisa ver o canal, enviar mensagens, incorporar links e gerenciar mensagens.",
        "channel_changed": "O painel será publicado no canal selecionado após confirmar o salvamento.",
        "edit_panel": "Mensagem do painel",
        "publish_panel": "Publicar / atualizar painel",
        "publish_confirm": "Publicar ou atualizar o painel de sugestões em {channel}?",
        "publish_requires_save": "Salve as alterações pendentes antes de publicar.",
        "publish_requires_channel": "Selecione e salve primeiro o canal do painel.",
        "publish_failed": "Não foi possível publicar o painel. Verifique as permissões e tente novamente.",
        "publish_success": "Painel publicado ou atualizado com sucesso.",
        "move_warning": "Não foi possível remover o painel do canal anterior; verifique a mensagem.",
        "save_failed": "Não foi possível salvar as configurações; as alterações dos revisores não foram aplicadas.",
        "status_published": "Mensagem do painel: {state}",
        "published": "Publicado",
        "not_published": "Ainda não publicado",
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
        self.original_channel_id = int(host["suggestion_get_channel_id"](guild_id) or 0)
        self.pending_channel_id = None
        self.original_owner = bool(host["suggestion_owner_enabled"](guild_id))
        self.original_reviewers = set(host["suggestion_reviewer_ids"](guild_id))
        self.pending_owner = self.original_owner
        self.pending_reviewers = set(self.original_reviewers)
        self.selected_id = None
        channels = discord.ui.ChannelSelect(
            placeholder=self.tr("channel_select"),
            channel_types=[discord.ChannelType.text],
            min_values=1, max_values=1, row=0)
        channels.callback = self.pick_channel
        self.channel_select = channels
        self.add_item(channels)
        self._reset_channel_selection()
        users = discord.ui.UserSelect(
            placeholder=self.tr("choose_reviewer"), min_values=1,
            max_values=1, row=1)
        users.callback = self.pick_user
        self.add_item(users)
        self._sync()

    def tr(self, key, **values):
        return tr(self.host, self.guild_id, key, **values)

    async def interaction_check(self, interaction):
        return await self.host["configuration_access"](
            interaction, self.guild_id, self.owner_id)

    def _dirty(self):
        return (self.pending_channel_id is not None
                or self.pending_owner != self.original_owner
                or self.pending_reviewers != self.original_reviewers)

    def _reset_channel_selection(self):
        effective_id = self.pending_channel_id or self.original_channel_id
        self.channel_select.default_values = (
            [discord.SelectDefaultValue(
                id=effective_id, type=discord.SelectDefaultValueType.channel)]
            if effective_id else [])

    def _sync(self):
        self.toggle_owner.label = self.tr("owner_exclude" if self.pending_owner else "owner_include")
        self.remove_reviewer.label = self.tr("remove_reviewer")
        self.save_changes.label = self.tr("save")
        self.discard_changes.label = self.tr("discard")
        self.back.label = self.tr("back")
        self.channel_select.placeholder = self.tr("channel_select")
        self.edit_panel.label = self.tr("edit_panel")
        self.publish_panel.label = self.tr("publish_panel")
        self.publish_panel.disabled = not self.original_channel_id or self._dirty()
        self.remove_reviewer.disabled = self.selected_id not in self.pending_reviewers
        self.save_changes.disabled = not self._dirty()
        self.discard_changes.disabled = not self._dirty()

    def to_components(self):
        self._sync()
        return super().to_components()

    def summary(self, guild):
        ids = sorted(self.pending_reviewers)
        reviewers = ", ".join(f"<@{user_id}>" for user_id in ids) if ids else self.tr("none")
        channel_id = self.pending_channel_id or self.original_channel_id
        channel = f"<#{channel_id}>" if channel_id else self.tr("not_configured")
        panel_state = self.tr("published") if self.host["suggestion_get_panel_message_id"](self.guild_id) else self.tr("not_published")
        content = self.tr("summary", channel=channel,
                          owner=self.tr("yes" if self.pending_owner else "negative"),
                          reviewers=reviewers)
        content += "\n" + self.tr("status_published", state=panel_state)
        if self.pending_channel_id is not None:
            content += "\n" + self.tr("channel_changed")
        return content + ("\n\n" + self.tr("pending") if self._dirty() else "")

    async def pick_channel(self, interaction):
        values = (interaction.data or {}).get("values", [])
        channel = interaction.guild.get_channel(int(values[0])) if values else None
        if not isinstance(channel, discord.TextChannel):
            await interaction.response.send_message(self.tr("invalid_channel"), ephemeral=True)
            return
        me = interaction.guild.me
        perms = channel.permissions_for(me) if me else None
        if perms is None or not (perms.view_channel and perms.send_messages
                                and perms.embed_links and perms.manage_messages):
            await interaction.response.send_message(self.tr("channel_permissions"), ephemeral=True)
            return
        self.pending_channel_id = channel.id if channel.id != self.original_channel_id else None
        self._reset_channel_selection()
        self._sync()
        await interaction.response.edit_message(content=self.summary(interaction.guild), view=self)

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

    @discord.ui.button(label=LANG["es-419"]["edit_panel"], style=discord.ButtonStyle.secondary, row=3)
    async def edit_panel(self, interaction, button):
        await self.host["open_default_message_studio"](
            interaction, "suggestions", self.owner_id, "suggestions_setup")

    @discord.ui.button(label=LANG["es-419"]["publish_panel"], style=discord.ButtonStyle.primary, row=3)
    async def publish_panel(self, interaction, button):
        if self._dirty():
            await interaction.response.send_message(self.tr("publish_requires_save"), ephemeral=True)
            return
        if not self.original_channel_id:
            await interaction.response.send_message(self.tr("publish_requires_channel"), ephemeral=True)
            return
        channel = interaction.guild.get_channel(self.original_channel_id)
        if not isinstance(channel, discord.TextChannel):
            await interaction.response.send_message(self.tr("invalid_channel"), ephemeral=True)
            return
        await interaction.response.edit_message(
            content=self.summary(interaction.guild) + "\n\n" +
                    self.tr("publish_confirm", channel=channel.mention),
            view=SuggestionsSetupPublishConfirmView(self))

    @discord.ui.button(label=LANG["es-419"]["save"], style=discord.ButtonStyle.success, row=4)
    async def save_changes(self, interaction, button):
        if not self._dirty():
            await interaction.response.send_message(self.tr("nothing_to_save"), ephemeral=True)
            return
        await interaction.response.edit_message(
            content=self.summary(interaction.guild) + "\n\n" + self.tr("confirm_question"),
            view=SuggestionsSetupConfirmView(self))

    @discord.ui.button(label=LANG["es-419"]["discard"], style=discord.ButtonStyle.danger, row=4)
    async def discard_changes(self, interaction, button):
        self.pending_owner = self.original_owner
        self.pending_reviewers = set(self.original_reviewers)
        self.pending_channel_id = None
        self._reset_channel_selection()
        self.selected_id = None
        self._sync()
        await interaction.response.edit_message(content=self.summary(interaction.guild), view=self)

    @discord.ui.button(label=LANG["es-419"]["back"], style=discord.ButtonStyle.secondary, row=4)
    async def back(self, interaction, button):
        view = self.host["HeraldoModerationSetupView"](self.guild_id, self.owner_id)
        await interaction.response.edit_message(
            content=self.host["_t"]('text.da10e9d8927c80'), embed=None, view=view)


class SuggestionsSetupConfirmView(discord.ui.View):
    def __init__(self, editor: SuggestionsSetupView):
        super().__init__(timeout=300)
        self.editor = editor
        self.finished = False
        self.channel_id = editor.pending_channel_id or editor.original_channel_id
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
        if (int(h["suggestion_get_channel_id"](guild_id) or 0) != editor.original_channel_id
                or bool(h["suggestion_owner_enabled"](guild_id)) != editor.original_owner
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
        target = interaction.guild.get_channel(self.channel_id) if self.channel_id else None
        if self.channel_id != editor.original_channel_id:
            if not isinstance(target, discord.TextChannel):
                await interaction.response.send_message(editor.tr("invalid_channel"), ephemeral=True)
                return
            me = interaction.guild.me
            perms = target.permissions_for(me) if me else None
            if perms is None or not (perms.view_channel and perms.send_messages
                                    and perms.embed_links and perms.manage_messages):
                await interaction.response.send_message(editor.tr("channel_permissions"), ephemeral=True)
                return
        await interaction.response.defer()
        previous_panel_id = h["suggestion_get_panel_message_id"](guild_id)
        previous_channel_id = editor.original_channel_id
        cleanup_warning = False
        if self.channel_id != previous_channel_id:
            try:
                await h["suggestion_publish_panel"](interaction.guild, target)
            except (discord.Forbidden, discord.HTTPException):
                await interaction.followup.send(editor.tr("save_failed"), ephemeral=True)
                return
            if previous_channel_id and previous_panel_id:
                old_channel = interaction.guild.get_channel(previous_channel_id)
                if isinstance(old_channel, discord.TextChannel):
                    try:
                        previous = await old_channel.fetch_message(previous_panel_id)
                        await previous.delete()
                    except discord.NotFound:
                        pass
                    except (discord.Forbidden, discord.HTTPException):
                        cleanup_warning = True
        if self.owner != editor.original_owner:
            h["suggestion_set_owner_enabled"](guild_id, self.owner)
        for user_id in sorted(editor.original_reviewers - self.reviewers):
            h["suggestion_remove_reviewer"](guild_id, user_id)
        for user_id in sorted(self.reviewers - editor.original_reviewers):
            h["suggestion_add_reviewer"](guild_id, user_id)
        self.finished = True
        self.stop()
        editor.original_channel_id = self.channel_id
        editor.pending_channel_id = None
        editor._reset_channel_selection()
        editor.original_owner = self.owner
        editor.original_reviewers = set(self.reviewers)
        editor.pending_owner = self.owner
        editor.pending_reviewers = set(self.reviewers)
        editor._sync()
        message = editor.summary(interaction.guild) + "\n\n" + editor.tr("saved")
        if cleanup_warning:
            message += "\n" + editor.tr("move_warning")
        await interaction.edit_original_response(content=message, view=editor)

    @discord.ui.button(label=LANG["es-419"]["back"], style=discord.ButtonStyle.secondary)
    async def back(self, interaction, button):
        self.finished = True
        self.stop()
        await interaction.response.edit_message(
            content=self.editor.summary(interaction.guild), view=self.editor)



class SuggestionsSetupPublishConfirmView(discord.ui.View):
    """Publicar/reparar el panel guardado sin crear otro editor de mensajes."""

    def __init__(self, editor: SuggestionsSetupView):
        super().__init__(timeout=300)
        self.editor = editor
        self.channel_id = editor.original_channel_id
        self.finished = False
        self.confirm.label = editor.tr("confirm")
        self.back.label = editor.tr("back")

    async def interaction_check(self, interaction):
        return not self.finished and await self.editor.interaction_check(interaction)

    @discord.ui.button(label=LANG["es-419"]["confirm"], style=discord.ButtonStyle.success)
    async def confirm(self, interaction, button):
        editor = self.editor
        h = editor.host
        if (editor._dirty() or not self.channel_id
                or h["suggestion_get_channel_id"](editor.guild_id) != self.channel_id):
            await interaction.response.send_message(editor.tr("changed_elsewhere"), ephemeral=True)
            return
        channel = interaction.guild.get_channel(self.channel_id)
        if not isinstance(channel, discord.TextChannel):
            await interaction.response.send_message(editor.tr("invalid_channel"), ephemeral=True)
            return
        me = interaction.guild.me
        perms = channel.permissions_for(me) if me else None
        if perms is None or not (perms.view_channel and perms.send_messages
                                and perms.embed_links and perms.manage_messages):
            await interaction.response.send_message(editor.tr("channel_permissions"), ephemeral=True)
            return
        await interaction.response.defer()
        try:
            await h["suggestion_ensure_panel"](interaction.guild)
            message_id = h["suggestion_get_panel_message_id"](editor.guild_id)
            if not message_id:
                raise RuntimeError("Panel not available after ensure")
            await channel.fetch_message(message_id)
        except (discord.HTTPException, RuntimeError):
            await interaction.followup.send(editor.tr("publish_failed"), ephemeral=True)
            return
        self.finished = True
        self.stop()
        await interaction.edit_original_response(
            content=editor.summary(interaction.guild) + "\n\n" + editor.tr("publish_success"),
            view=editor)

    @discord.ui.button(label=LANG["es-419"]["back"], style=discord.ButtonStyle.secondary)
    async def back(self, interaction, button):
        self.finished = True
        self.stop()
        await interaction.response.edit_message(
            content=self.editor.summary(interaction.guild), view=self.editor)
