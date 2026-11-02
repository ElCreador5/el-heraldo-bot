"""Mensajes personales: biblioteca privada de embeds, sin configuración de servidor."""
import copy
import json
import os
import sqlite3
import discord
from discord import app_commands
from autofeed_embed_builder import EmbedBuilderView, validate_data, has_content, render


def _db():
    path = os.getenv("DB_PATH", "heraldo.db")
    connection = sqlite3.connect(path, timeout=10)
    connection.execute("CREATE TABLE IF NOT EXISTS personal_embeds (user_id INTEGER NOT NULL, name TEXT NOT NULL COLLATE NOCASE, payload TEXT NOT NULL, PRIMARY KEY(user_id, name))")
    return connection


def entries(user_id):
    with _db() as db:
        rows = db.execute("SELECT name, payload FROM personal_embeds WHERE user_id=? ORDER BY name COLLATE NOCASE", (user_id,)).fetchall()
    return [(name, json.loads(payload)) for name, payload in rows]


def get_entry(user_id, name):
    with _db() as db:
        row = db.execute("SELECT payload FROM personal_embeds WHERE user_id=? AND name=? COLLATE NOCASE", (user_id, name)).fetchone()
    return json.loads(row[0]) if row else None


def store(user_id, name, payload):
    if not 1 <= len(name.strip()) <= 70:
        raise ValueError("El nombre debe tener entre 1 y 70 caracteres.")
    valid = validate_data(payload)
    if not has_content(valid):
        raise ValueError("Completa el embed antes de guardarlo.")
    with _db() as db:
        db.execute("INSERT INTO personal_embeds(user_id,name,payload) VALUES(?,?,?) ON CONFLICT(user_id,name) DO UPDATE SET payload=excluded.payload", (user_id, name.strip(), json.dumps(valid, ensure_ascii=False)))


def remove(user_id, name):
    with _db() as db:
        db.execute("DELETE FROM personal_embeds WHERE user_id=? AND name=? COLLATE NOCASE", (user_id, name))


class NameModal(discord.ui.Modal, title="Nombre del mensaje"):
    name = discord.ui.TextInput(label="Nombre para Mis mensajes", max_length=70, min_length=1)
    def __init__(self, panel):
        super().__init__()
        self.panel = panel
        self.name.default = panel.name or ""

    async def on_submit(self, interaction):
        if not await self.panel.interaction_check(interaction):
            return
        name = str(self.name).strip()
        if not name:
            return await interaction.response.send_message("Escribe un nombre.", ephemeral=True)
        changed = name != self.panel.name
        self.panel.name = name
        self.panel.dirty = changed or self.panel.dirty
        self.panel.refresh()
        await interaction.response.edit_message(**self.panel.kwargs(interaction.guild))


class PersonalPanel(discord.ui.View):
    def __init__(self, user_id, guild_id, host, name="", embed=None):
        super().__init__(timeout=900)
        self.owner_id, self.guild_id, self.host = user_id, guild_id, host
        self.personal = True
        self.name = name
        self.embed = copy.deepcopy(embed)
        self.initial = copy.deepcopy(embed)
        self.text, self.role_id = "", None
        self.dirty = False
        self.refresh()

    async def interaction_check(self, interaction):
        if interaction.user.id != self.owner_id or (interaction.guild.id if interaction.guild else None) != self.guild_id:
            await interaction.response.send_message("Este panel es personal. Abre /embed para usar el tuyo.", ephemeral=True)
            return False
        return True

    def refresh(self):
        names = [name for name, _ in entries(self.owner_id)]
        self.pick.options = [discord.SelectOption(label=name[:100], value=name, default=name.casefold() == self.name.casefold()) for name in names[:25]] or [discord.SelectOption(label="No tienes mensajes guardados", value="_empty")]
        self.pick.disabled = not names
        changed = self.dirty or self.embed != self.initial or bool(self.embed and not self.name)
        self.save.disabled = not changed or not has_content(self.embed)
        self.discard.disabled = not changed

    def summary(self):
        names = entries(self.owner_id)
        return ("**El Heraldo · Mis mensajes**\n"
                "Biblioteca personal. Los borradores no son anuncios ni programaciones.\n\n"
                f"**Mensaje seleccionado:** {discord.utils.escape_markdown(self.name) if self.name else 'Nuevo mensaje'}\n"
                f"**Guardados:** {len(names)}\n"
                f"**Estado:** {'Cambios sin guardar' if not self.save.disabled else 'Sin cambios pendientes'}")

    def kwargs(self, guild):
        self.refresh()
        return dict(content=self.summary(), embed=render(self.embed, self.host["stamp_embed"], guild) if self.embed else None, view=self, allowed_mentions=discord.AllowedMentions.none())

    @discord.ui.select(placeholder="Mis mensajes", options=[discord.SelectOption(label="Sin mensajes", value="_empty")], row=0)
    async def pick(self, interaction, select):
        name = select.values[0]
        if name == "_empty":
            return await interaction.response.defer()
        if self.dirty or self.embed != self.initial:
            return await interaction.response.send_message("Guarda o descarta los cambios antes de cambiar de mensaje.", ephemeral=True)
        loaded = get_entry(self.owner_id, name)
        if loaded is None:
            return await interaction.response.send_message("El mensaje ya no existe.", ephemeral=True)
        self.name, self.embed, self.initial, self.dirty = name, loaded, copy.deepcopy(loaded), False
        await interaction.response.edit_message(**self.kwargs(interaction.guild))

    @discord.ui.button(label="Editar mensaje", style=discord.ButtonStyle.primary, row=1)
    async def edit(self, interaction, button):
        view = EmbedBuilderView(self)
        await interaction.response.edit_message(content=view.summary(), embed=view.preview_embed(interaction.guild), view=view, allowed_mentions=discord.AllowedMentions.none())

    @discord.ui.button(label="Nombre", style=discord.ButtonStyle.secondary, row=1)
    async def rename(self, interaction, button):
        await interaction.response.send_modal(NameModal(self))

    @discord.ui.button(label="Guardar cambios", style=discord.ButtonStyle.success, row=2)
    async def save(self, interaction, button):
        if not self.name:
            return await interaction.response.send_message("Asigna primero un nombre al mensaje.", ephemeral=True)
        try:
            validate_data(self.embed)
            if not has_content(self.embed):
                raise ValueError("El embed está vacío.")
        except ValueError:
            return await interaction.response.send_message("Completa correctamente el embed antes de guardar.", ephemeral=True)
        await interaction.response.send_message("¿Confirmas guardar este mensaje personal?", view=ConfirmSave(self), ephemeral=True)

    @discord.ui.button(label="Descartar cambios", style=discord.ButtonStyle.danger, row=2)
    async def discard(self, interaction, button):
        self.embed, self.dirty = copy.deepcopy(self.initial), False
        await interaction.response.edit_message(**self.kwargs(interaction.guild))

    @discord.ui.button(label="Enviar", style=discord.ButtonStyle.primary, row=2)
    async def send(self, interaction, button):
        if not has_content(self.embed):
            return await interaction.response.send_message("Primero crea o selecciona un embed.", ephemeral=True)
        await interaction.response.send_message(
            "Selecciona el canal de destino. No se enviará nada hasta confirmar.",
            view=PublishChannelView(self), ephemeral=True,
        )

    @discord.ui.button(label="Eliminar mensaje", style=discord.ButtonStyle.danger, row=3)
    async def delete(self, interaction, button):
        if not self.name or get_entry(self.owner_id, self.name) is None:
            return await interaction.response.send_message("Selecciona un mensaje guardado.", ephemeral=True)
        await interaction.response.send_message("¿Eliminar este mensaje de Mis mensajes?", view=ConfirmDelete(self), ephemeral=True)

    @discord.ui.button(label="Cerrar", style=discord.ButtonStyle.danger, row=3)
    async def close(self, interaction, button):
        if self.dirty or self.embed != self.initial:
            return await interaction.response.send_message("Hay cambios pendientes. Guárdalos o descártalos antes de cerrar.", ephemeral=True)
        self.stop()
        await interaction.response.edit_message(content="Panel personal cerrado.", embed=None, view=None)


def can_publish(interaction, channel):
    if not isinstance(channel, discord.TextChannel) or interaction.guild is None:
        return False
    if channel.guild.id != interaction.guild.id:
        return False
    member = interaction.guild.get_member(interaction.user.id)
    bot_member = interaction.guild.me
    if member is None or bot_member is None:
        return False
    user_perms = channel.permissions_for(member)
    bot_perms = channel.permissions_for(bot_member)
    return (user_perms.view_channel and user_perms.send_messages
            and user_perms.embed_links and bot_perms.view_channel
            and bot_perms.send_messages and bot_perms.embed_links)


class PublishChannelView(discord.ui.View):
    def __init__(self, panel):
        super().__init__(timeout=180)
        self.panel = panel
        self.channel_id = None
        self.channel_select = discord.ui.ChannelSelect(
            placeholder="Selecciona un canal donde puedas publicar",
            channel_types=[discord.ChannelType.text], row=0,
        )
        self.channel_select.callback = self.choose
        self.add_item(self.channel_select)
        self.confirm.disabled = True

    async def interaction_check(self, interaction):
        return await self.panel.interaction_check(interaction)

    async def choose(self, interaction):
        channel = self.channel_select.values[0]
        if not can_publish(interaction, channel):
            return await interaction.response.send_message(
                "No tienes permisos para publicar embeds en ese canal.", ephemeral=True)
        self.channel_id = channel.id
        self.confirm.disabled = False
        await interaction.response.edit_message(
            content=f"Destino: {channel.mention}. Revisa la vista previa y confirma el envío.",
            embed=render(self.panel.embed, self.panel.host["stamp_embed"], interaction.guild),
            view=self, allowed_mentions=discord.AllowedMentions.none(),
        )

    @discord.ui.button(label="Confirmar envío", style=discord.ButtonStyle.success, row=1)
    async def confirm(self, interaction, button):
        channel = interaction.guild.get_channel(self.channel_id) if self.channel_id else None
        if not can_publish(interaction, channel):
            return await interaction.response.send_message(
                "No se puede publicar: revisa los permisos actuales del canal.", ephemeral=True)
        try:
            payload = copy.deepcopy(self.panel.embed)
            if not has_content(payload):
                raise ValueError("El embed está vacío.")
            embed = render(payload, self.panel.host["stamp_embed"], interaction.guild)
            await interaction.response.defer(ephemeral=True)
            await channel.send(embed=embed, allowed_mentions=discord.AllowedMentions.none())
        except (ValueError, discord.HTTPException):
            return await interaction.followup.send("No fue posible publicar el embed.", ephemeral=True)
        self.stop()
        await interaction.edit_original_response(content="Mensaje enviado correctamente.", embed=None, view=None)

    @discord.ui.button(label="Cancelar", style=discord.ButtonStyle.danger, row=1)
    async def cancel(self, interaction, button):
        self.stop()
        await interaction.response.edit_message(content="Envío cancelado.", embed=None, view=None)


class ConfirmSave(discord.ui.View):
    def __init__(self, panel):
        super().__init__(timeout=90)
        self.panel = panel

    async def interaction_check(self, interaction):
        return await self.panel.interaction_check(interaction)

    @discord.ui.button(label="Confirmar cambios", style=discord.ButtonStyle.success)
    async def confirm(self, interaction, button):
        try:
            store(self.panel.owner_id, self.panel.name, self.panel.embed)
        except (ValueError, sqlite3.Error):
            return await interaction.response.send_message("No se pudo guardar el mensaje.", ephemeral=True)
        self.panel.initial = copy.deepcopy(self.panel.embed)
        self.panel.dirty = False
        self.panel.refresh()
        self.stop()
        await interaction.response.edit_message(content="Mensaje guardado en Mis mensajes.", view=None)
        try:
            await self.panel_message_update(interaction)
        except Exception:
            pass

    async def panel_message_update(self, interaction):
        # La confirmación es efímera independiente; el panel se refresca al usarlo.
        return

    @discord.ui.button(label="Descartar", style=discord.ButtonStyle.danger)
    async def cancel(self, interaction, button):
        self.stop()
        await interaction.response.edit_message(content="Guardado cancelado.", view=None)


class ConfirmDelete(discord.ui.View):
    def __init__(self, panel):
        super().__init__(timeout=90)
        self.panel = panel

    async def interaction_check(self, interaction):
        return await self.panel.interaction_check(interaction)

    @discord.ui.button(label="Eliminar", style=discord.ButtonStyle.danger)
    async def yes(self, interaction, button):
        remove(self.panel.owner_id, self.panel.name)
        self.panel.name, self.panel.embed, self.panel.initial, self.panel.dirty = "", None, None, False
        self.panel.refresh()
        self.stop()
        await interaction.response.edit_message(content="Mensaje eliminado.", view=None)

    @discord.ui.button(label="Descartar", style=discord.ButtonStyle.danger)
    async def no(self, interaction, button):
        self.stop()
        await interaction.response.edit_message(content="Eliminación cancelada.", view=None)


def install(host):
    host = dict(host)
    if "stamp_embed" not in host:
        def stamp_embed(embed, guild):
            bot_name = str(getattr(getattr(host["bot"], "user", None), "name", "")).lower()
            if "lab" in bot_name or "test" in bot_name:
                embed.set_footer(text="El Heraldo's Labs 🧪")
            elif guild is not None:
                embed.set_footer(text=guild.name, icon_url=guild.icon.url if guild.icon else None)
            return embed
        host["stamp_embed"] = stamp_embed

    @host["bot"].tree.command(name="embed", description="Crear, guardar y enviar mensajes embed personales.")
    async def personal_embed(interaction: discord.Interaction):
        if interaction.guild is None:
            return await interaction.response.send_message("Por ahora, abre /embed dentro de un servidor.", ephemeral=True)
        panel = PersonalPanel(interaction.user.id, interaction.guild.id, host)
        await interaction.response.send_message(**panel.kwargs(interaction.guild), ephemeral=True)
