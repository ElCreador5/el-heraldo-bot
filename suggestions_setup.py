"""Configuración única de destinatarios de Sugerencias en /setup -> Moderación.

Las selecciones son un borrador: ninguna mutación se realiza antes de
Guardar cambios -> Confirmar cambios. Mantiene la base de datos existente.
"""
import discord


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
            placeholder="Seleccionar revisor para añadir o quitar", min_values=1,
            max_values=1, row=0)
        users.callback = self.pick_user
        self.add_item(users)
        self._sync()

    async def interaction_check(self, interaction):
        return await self.host["configuration_access"](
            interaction, self.guild_id, self.owner_id)

    def _dirty(self):
        return (self.pending_owner != self.original_owner or
                self.pending_reviewers != self.original_reviewers)

    def _sync(self):
        self.toggle_owner.label = (
            "Excluir dueño de los avisos" if self.pending_owner
            else "Incluir dueño en los avisos")
        self.remove_reviewer.disabled = self.selected_id not in self.pending_reviewers
        self.save_changes.disabled = not self._dirty()
        self.discard_changes.disabled = not self._dirty()

    def to_components(self):
        self._sync()
        return super().to_components()

    def summary(self, guild):
        ids = sorted(self.pending_reviewers)
        reviewers = ", ".join(f"<@{user_id}>" for user_id in ids) if ids else "Ninguno"
        channel_id = self.host["suggestion_get_channel_id"](self.guild_id)
        channel = f"<#{channel_id}>" if channel_id else "No configurado"
        return ("**Moderación → Sugerencias**\n"
                f"Canal del panel: {channel}\n"
                f"Notificar al propietario: {'Sí' if self.pending_owner else 'No'}\n"
                f"Revisores: {reviewers}\n"
                "Selecciona un miembro para añadirlo a los revisores o quitarlo "
                "con el botón correspondiente. Nada se guarda hasta confirmar."
                + ("\n\n**Cambios sin guardar**" if self._dirty() else ""))

    async def pick_user(self, interaction):
        values = (interaction.data or {}).get("values", [])
        if not values:
            await interaction.response.send_message("Selecciona un miembro.", ephemeral=True)
            return
        user_id = int(values[0])
        member = interaction.guild.get_member(user_id)
        if member is None:
            try:
                member = await interaction.guild.fetch_member(user_id)
            except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                await interaction.response.send_message(
                    "No pude comprobar ese miembro.", ephemeral=True)
                return
        if member.bot:
            await interaction.response.send_message(
                "Los bots no pueden revisar sugerencias.", ephemeral=True)
            return
        self.selected_id = user_id
        self.pending_reviewers.add(user_id)
        self._sync()
        await interaction.response.edit_message(content=self.summary(interaction.guild), view=self)

    @discord.ui.button(label="Incluir dueño en los avisos", style=discord.ButtonStyle.secondary, row=1)
    async def toggle_owner(self, interaction, button):
        self.pending_owner = not self.pending_owner
        self._sync()
        await interaction.response.edit_message(content=self.summary(interaction.guild), view=self)

    @discord.ui.button(label="Quitar revisor seleccionado", style=discord.ButtonStyle.secondary, row=1)
    async def remove_reviewer(self, interaction, button):
        if self.selected_id not in self.pending_reviewers:
            await interaction.response.send_message("Selecciona un revisor existente.", ephemeral=True)
            return
        self.pending_reviewers.discard(self.selected_id)
        self._sync()
        await interaction.response.edit_message(content=self.summary(interaction.guild), view=self)

    @discord.ui.button(label="Guardar cambios", style=discord.ButtonStyle.success, row=2)
    async def save_changes(self, interaction, button):
        if not self._dirty():
            await interaction.response.send_message("No hay cambios pendientes.", ephemeral=True)
            return
        await interaction.response.edit_message(
            content=self.summary(interaction.guild) + "\n\n¿Confirmas estos cambios?",
            view=SuggestionsSetupConfirmView(self))

    @discord.ui.button(label="Descartar cambios", style=discord.ButtonStyle.danger, row=2)
    async def discard_changes(self, interaction, button):
        self.pending_owner = self.original_owner
        self.pending_reviewers = set(self.original_reviewers)
        self.selected_id = None
        self._sync()
        await interaction.response.edit_message(content=self.summary(interaction.guild), view=self)

    @discord.ui.button(label="Volver", style=discord.ButtonStyle.secondary, row=2)
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

    async def interaction_check(self, interaction):
        return not self.finished and await self.editor.interaction_check(interaction)

    @discord.ui.button(label="Confirmar cambios", style=discord.ButtonStyle.success)
    async def confirm(self, interaction, button):
        editor = self.editor
        h, guild_id = editor.host, editor.guild_id
        if (bool(h["suggestion_owner_enabled"](guild_id)) != editor.original_owner
                or set(h["suggestion_reviewer_ids"](guild_id)) != editor.original_reviewers):
            await interaction.response.send_message(
                "La configuración cambió desde que abriste el panel. Vuelve a abrirlo.", ephemeral=True)
            return
        for user_id in sorted(self.reviewers - editor.original_reviewers):
            member = interaction.guild.get_member(user_id)
            if member is None:
                try:
                    member = await interaction.guild.fetch_member(user_id)
                except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                    await interaction.response.send_message(
                        "No pude comprobar uno de los revisores. No se guardaron cambios.",
                        ephemeral=True)
                    return
            if member.bot:
                await interaction.response.send_message(
                    "Un bot no puede ser revisor. No se guardaron cambios.", ephemeral=True)
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
            content=editor.summary(interaction.guild) + "\n\nCambios guardados.",
            view=editor)

    @discord.ui.button(label="Volver", style=discord.ButtonStyle.secondary)
    async def back(self, interaction, button):
        self.finished = True
        self.stop()
        await interaction.response.edit_message(
            content=self.editor.summary(interaction.guild), view=self.editor)
