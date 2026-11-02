"""Mensajes personales: biblioteca privada de embeds, sin configuración de servidor."""
import copy
import json
import os
import sqlite3
from urllib.parse import urlsplit
import discord
from discord import app_commands
import personal_publications as pub
from autofeed_embed_builder import EmbedBuilderView, validate_data, has_content, render


def _db():
    path = os.getenv("DB_PATH", "heraldo.db")
    connection = sqlite3.connect(path, timeout=10)
    connection.execute("CREATE TABLE IF NOT EXISTS personal_embeds (user_id INTEGER NOT NULL, name TEXT NOT NULL COLLATE NOCASE, payload TEXT NOT NULL, PRIMARY KEY(user_id, name))")
    pub.setup(connection)
    return connection


def entries(user_id):
    with _db() as db:
        rows = db.execute("SELECT name, payload FROM personal_embeds WHERE user_id=? ORDER BY name COLLATE NOCASE", (user_id,)).fetchall()
    return [(name, json.loads(payload)) for name, payload in rows]


def get_entry(user_id, name):
    with _db() as db:
        row = db.execute("SELECT payload FROM personal_embeds WHERE user_id=? AND name=? COLLATE NOCASE", (user_id, name)).fetchone()
    return json.loads(row[0]) if row else None


def valid_personal(payload):
    if isinstance(payload, dict) and payload.get("kind") == "text":
        text = str(payload.get("text") or "").strip()
        image = str(payload.get("image_url") or "").strip()
        if len(text) > 2000 or (image and (len(image) > 1900 or urlsplit(image).scheme != "https" or not urlsplit(image).netloc)):
            raise ValueError("Texto o enlace de imagen inválido.")
        if not text and not image:
            raise ValueError("Escribe texto o proporciona una foto.")
        return {"kind": "text", "text": text, "image_url": image}
    valid = validate_data(payload)
    if not has_content(valid):
        raise ValueError("El embed está vacío.")
    return valid


def personal_has_content(payload):
    if isinstance(payload, dict) and payload.get("kind") == "text":
        return bool(payload.get("text") or payload.get("image_url"))
    return bool(payload) and has_content(payload)


def store(user_id, name, payload):
    if not 1 <= len(name.strip()) <= 70:
        raise ValueError("El nombre debe tener entre 1 y 70 caracteres.")
    valid = valid_personal(payload)
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


class EditMessageModal(discord.ui.Modal, title="Editar mensaje"):
    """Formulario básico del embed, sin controles de programación."""
    name = discord.ui.TextInput(label="Nombre del mensaje", max_length=70, min_length=1)
    embed_title = discord.ui.TextInput(label="Título", max_length=256, required=False)
    description = discord.ui.TextInput(
        label="Descripción", style=discord.TextStyle.paragraph,
        max_length=4000, required=False,
    )
    color_hex = discord.ui.TextInput(
        label="Color hexadecimal (#5865F2)", max_length=7,
        min_length=6, default="5865F2",
    )

    def __init__(self, panel):
        super().__init__()
        self.panel = panel
        payload = panel.embed or {}
        if payload.get("kind") == "text":
            payload = {}
        self.name.default = panel.name or ""
        self.embed_title.default = str(payload.get("title") or "")
        self.description.default = str(payload.get("description") or "")
        self.color_hex.default = str(payload.get("color_hex") or "5865F2")

    async def on_submit(self, interaction):
        if not await self.panel.interaction_check(interaction):
            return
        name = str(self.name).strip()
        payload = copy.deepcopy(self.panel.embed or {})
        if payload.get("kind") == "text":
            payload = {}
        payload["title"] = str(self.embed_title).strip()
        payload["description"] = str(self.description).strip()
        payload["color_hex"] = str(self.color_hex).strip().lstrip("#")
        try:
            payload = validate_data(payload)
            if not has_content(payload):
                raise ValueError("empty")
        except ValueError:
            return await interaction.response.send_message(
                "Introduce un título o descripción y un color hexadecimal válido.", ephemeral=True)
        self.panel.name = name
        self.panel.embed = payload
        self.panel.dirty = True
        # No se guarda en SQLite hasta Guardar cambios -> Confirmar cambios.
        await interaction.response.edit_message(**self.panel.kwargs(interaction.guild))


class EditTextModal(discord.ui.Modal, title="Editar texto"):
    name = discord.ui.TextInput(label="Nombre del mensaje", max_length=70, min_length=1)
    message = discord.ui.TextInput(label="Texto", style=discord.TextStyle.paragraph, max_length=2000, required=False)
    image_url = discord.ui.TextInput(label="Foto (enlace HTTPS)", max_length=1900, required=False)

    def __init__(self, panel):
        super().__init__()
        self.panel = panel
        payload = panel.embed or {}
        self.name.default = panel.name or ""
        if payload.get("kind") == "text":
            self.message.default = payload.get("text", "")
            self.image_url.default = payload.get("image_url", "")

    async def on_submit(self, interaction):
        if not await self.panel.interaction_check(interaction):
            return
        try:
            payload = valid_personal({"kind": "text", "text": str(self.message), "image_url": str(self.image_url)})
        except ValueError as exc:
            return await interaction.response.send_message(str(exc), ephemeral=True)
        self.panel.name = str(self.name).strip()
        self.panel.embed = payload
        self.panel.dirty = True
        await interaction.response.edit_message(**self.panel.kwargs(interaction.guild))


class EditImagesModal(discord.ui.Modal, title="Imágenes del embed"):
    image_url = discord.ui.TextInput(
        label="Imagen grande (URL)", placeholder="https://ejemplo.com/imagen.jpg",
        max_length=2048, required=False,
    )
    thumbnail_url = discord.ui.TextInput(
        label="Miniatura (URL)", placeholder="https://ejemplo.com/miniatura.png",
        max_length=2048, required=False,
    )

    def __init__(self, panel):
        super().__init__()
        self.panel = panel
        payload = panel.embed or {}
        if payload.get("kind") == "text":
            payload = {}
        self.image_url.default = str(payload.get("image_url") or "")
        self.thumbnail_url.default = str(payload.get("thumbnail_url") or "")

    async def on_submit(self, interaction):
        if not await self.panel.interaction_check(interaction):
            return
        if isinstance(self.panel.embed, dict) and self.panel.embed.get("kind") == "text":
            return await interaction.response.send_message(
                "Selecciona un embed para editar sus imágenes. Los mensajes de texto tienen su propio campo de foto.",
                ephemeral=True,
            )
        payload = copy.deepcopy(self.panel.embed or {})
        payload["image_url"] = str(self.image_url).strip()
        payload["thumbnail_url"] = str(self.thumbnail_url).strip()
        try:
            payload = validate_data(payload)
        except ValueError:
            return await interaction.response.send_message(
                "Introduce enlaces HTTPS válidos para las imágenes.", ephemeral=True,
            )
        self.panel.embed = payload
        self.panel.dirty = True
        await interaction.response.edit_message(**self.panel.kwargs(interaction.guild))


class PersonalPanel(discord.ui.View):
    def __init__(self, user_id, guild_id, host, name="", embed=None):
        super().__init__(timeout=900)
        self.owner_id, self.guild_id, self.host = user_id, guild_id, host
        self.personal = True
        self.panel_message = None
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
        self.save.disabled = not changed or not personal_has_content(self.embed)
        self.discard.disabled = not changed

    def summary(self):
        names = entries(self.owner_id)
        return ("**El Heraldo · Mis mensajes**\n"
                "Biblioteca personal. Los borradores no son anuncios ni programaciones.\n\n"
                f"**Mensaje seleccionado:** {discord.utils.escape_markdown(self.name) if self.name else 'Nuevo mensaje'}\n"
                f"**Guardados:** {len(names)}\n"
                f"**Estado:** {'Cambios sin guardar' if not self.save.disabled else 'Sin cambios pendientes'}")

    async def refresh_visible(self, guild):
        """Actualizar la vista original /embed, incluso después de una confirmación efímera."""
        if self.panel_message is not None:
            try:
                await self.panel_message.edit(**self.kwargs(guild))
            except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                pass

    def kwargs(self, guild):
        self.refresh()
        is_text = isinstance(self.embed, dict) and self.embed.get("kind") == "text"
        preview = ""
        if is_text:
            preview = "\n\n**Vista previa del texto:**\n" + (self.embed.get("text") or "")
            if self.embed.get("image_url"):
                preview += "\n" + self.embed["image_url"]
        return dict(content=self.summary() + preview,
                    embed=render(self.embed, self.host["stamp_embed"], guild) if self.embed and not is_text else None,
                    view=self, allowed_mentions=discord.AllowedMentions.none())

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
        await interaction.response.send_modal(EditMessageModal(self))

    @discord.ui.button(label="Editar texto", style=discord.ButtonStyle.primary, row=1)
    async def edit_text(self, interaction, button):
        await interaction.response.send_modal(EditTextModal(self))

    @discord.ui.button(label="Imágenes", style=discord.ButtonStyle.secondary, row=1)
    async def edit_images(self, interaction, button):
        if isinstance(self.embed, dict) and self.embed.get("kind") == "text":
            return await interaction.response.send_message(
                "Para una foto en un mensaje de texto, utiliza «Editar texto».", ephemeral=True,
            )
        await interaction.response.send_modal(EditImagesModal(self))

    @discord.ui.button(label="Mis publicaciones", style=discord.ButtonStyle.secondary, row=3)
    async def published(self, interaction, button):
        with _db() as db:
            rows = pub.list_for(db, self.owner_id, self.name) if self.name else []
        if not rows:
            return await interaction.response.send_message("Este mensaje no tiene publicaciones registradas.", ephemeral=True)
        await interaction.response.send_message(
            "Selecciona una publicación para editarla o eliminarla.",
            view=PublicationsView(self), ephemeral=True)

    @discord.ui.button(label="Nombre", style=discord.ButtonStyle.secondary, row=1)
    async def rename(self, interaction, button):
        await interaction.response.send_modal(NameModal(self))

    @discord.ui.button(label="Guardar cambios", style=discord.ButtonStyle.success, row=2)
    async def save(self, interaction, button):
        if not self.name:
            return await interaction.response.send_message("Asigna primero un nombre al mensaje.", ephemeral=True)
        try:
            valid_personal(self.embed)
        except ValueError:
            return await interaction.response.send_message("Completa correctamente el embed antes de guardar.", ephemeral=True)
        await interaction.response.send_message("¿Confirmas guardar este mensaje personal?", view=ConfirmSave(self), ephemeral=True)

    @discord.ui.button(label="Descartar cambios", style=discord.ButtonStyle.danger, row=2)
    async def discard(self, interaction, button):
        self.embed, self.dirty = copy.deepcopy(self.initial), False
        await interaction.response.edit_message(**self.kwargs(interaction.guild))

    @discord.ui.button(label="Enviar", style=discord.ButtonStyle.primary, row=2)
    async def send(self, interaction, button):
        if not personal_has_content(self.embed):
            return await interaction.response.send_message("Primero edita o selecciona un mensaje.", ephemeral=True)
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


def resolve_publish_channel(interaction, selected):
    """ChannelSelect can return AppCommandChannel rather than a TextChannel."""
    guild = interaction.guild
    if guild is None or selected is None:
        return None
    channel_id = getattr(selected, "id", selected)
    try:
        channel = guild.get_channel(int(channel_id))
    except (TypeError, ValueError):
        return None
    return channel if isinstance(channel, discord.TextChannel) and channel.guild.id == guild.id else None


def can_publish(interaction, channel):
    channel = resolve_publish_channel(interaction, channel)
    if channel is None:
        return False
    guild = interaction.guild
    member = interaction.user if isinstance(interaction.user, discord.Member) else guild.get_member(interaction.user.id)
    bot_member = guild.me
    if member is None or bot_member is None:
        return False
    user_perms = channel.permissions_for(member)
    bot_perms = channel.permissions_for(bot_member)
    # El usuario necesita poder escribir; el embed lo publica el bot, no el usuario.
    return (user_perms.view_channel and user_perms.send_messages
            and bot_perms.view_channel and bot_perms.send_messages
            and bot_perms.embed_links)


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
        channel = resolve_publish_channel(interaction, self.channel_select.values[0])
        if not can_publish(interaction, channel):
            return await interaction.response.send_message(
                "No tienes permisos para publicar embeds en ese canal.", ephemeral=True)
        self.channel_id = channel.id
        self.confirm.disabled = False
        await interaction.response.edit_message(
            content=f"Destino: {channel.mention}. Revisa la vista previa y confirma el envío.",
            embed=(render(self.panel.embed, self.panel.host["stamp_embed"], interaction.guild)
                   if self.panel.embed.get("kind") != "text" else None),
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
            valid_personal(payload)
            await interaction.response.defer(ephemeral=True)
            if payload.get("kind") == "text":
                content = payload.get("text", "")
                if payload.get("image_url"):
                    content += ("\n" if content else "") + payload["image_url"]
                sent = await channel.send(content=content, allowed_mentions=discord.AllowedMentions.none())
            else:
                embed = render(payload, self.panel.host["stamp_embed"], interaction.guild)
                embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)
                sent = await channel.send(embed=embed, allowed_mentions=discord.AllowedMentions.none())
        except (ValueError, discord.HTTPException):
            return await interaction.followup.send("No fue posible publicar el embed.", ephemeral=True)
        try:
            with _db() as db:
                pub.register(db, self.panel.owner_id, self.panel.name, interaction.guild.id, channel.id, sent.id, interaction.user.id)
            result = "Mensaje enviado y registrado."
        except sqlite3.Error:
            result = "Mensaje enviado, pero falló el registro de la publicación."
        self.stop()
        await interaction.edit_original_response(content=result, embed=None, view=None)

    @discord.ui.button(label="Cancelar", style=discord.ButtonStyle.danger, row=1)
    async def cancel(self, interaction, button):
        self.stop()
        await interaction.response.edit_message(content="Envío cancelado.", embed=None, view=None)


class PublicationsView(discord.ui.View):
    def __init__(self, panel):
        super().__init__(timeout=180)
        self.panel, self.selected = panel, None
        with _db() as db:
            rows = pub.list_for(db, panel.owner_id, panel.name)[:25]
        self.pick.options = [
            discord.SelectOption(label=f"Canal {c} · mensaje {m}", value=f"{g}:{c}:{m}")
            for g,c,m,_ in rows]
        self.edit.disabled = self.delete_one.disabled = True

    async def interaction_check(self, interaction):
        return await self.panel.interaction_check(interaction)

    @discord.ui.select(placeholder="Mis publicaciones", options=[discord.SelectOption(label="Seleccionar", value="_")], row=0)
    async def pick(self, interaction, select):
        selected = tuple(map(int, select.values[0].split(":")))
        with _db() as db:
            valid = any((g,c,m) == selected for g,c,m,_ in pub.list_for(db,self.panel.owner_id,self.panel.name))
        if not valid:
            return await interaction.response.send_message("Publicación no disponible.", ephemeral=True)
        self.selected = selected
        self.edit.disabled = self.delete_one.disabled = False
        await interaction.response.edit_message(content="Publicación seleccionada.", view=self)

    @discord.ui.button(label="Editar", style=discord.ButtonStyle.primary, row=1)
    async def edit(self, interaction, button):
        if not self.selected:
            return await interaction.response.send_message("Selecciona una publicación.", ephemeral=True)
        await interaction.response.send_message(
            "Edita el borrador desde «Editar mensaje» o «Editar texto». Al confirmar «Guardar cambios» se actualizarán las publicaciones vinculadas.",
            ephemeral=True)

    @discord.ui.button(label="Eliminar publicación", style=discord.ButtonStyle.danger, row=1)
    async def delete_one(self, interaction, button):
        if not self.selected:
            return await interaction.response.send_message("Selecciona una publicación.", ephemeral=True)
        await interaction.response.send_message("¿Eliminar esta publicación del canal seleccionado?",
            view=ConfirmPublishedDelete(self.panel, self.selected), ephemeral=True)

    @discord.ui.button(label="Eliminar todas", style=discord.ButtonStyle.danger, row=2)
    async def delete_all(self, interaction, button):
        with _db() as db:
            total = len(pub.list_for(db,self.panel.owner_id,self.panel.name))
        await interaction.response.send_message(
            f"¿Eliminar las {total} publicaciones de este mensaje? Se conservará el borrador.",
            view=ConfirmPublishedDelete(self.panel), ephemeral=True)

    @discord.ui.button(label="Volver", style=discord.ButtonStyle.secondary, row=2)
    async def back(self, interaction, button):
        self.stop()
        await interaction.response.edit_message(content="Abre /embed para regresar a Mis mensajes.", view=None)


class ConfirmPublishedDelete(discord.ui.View):
    def __init__(self, panel, selected=None):
        super().__init__(timeout=90)
        self.panel, self.selected = panel, selected

    async def interaction_check(self, interaction):
        return await self.panel.interaction_check(interaction)

    @discord.ui.button(label="Confirmar eliminación", style=discord.ButtonStyle.danger)
    async def confirm(self, interaction, button):
        await interaction.response.defer()
        deleted, failed = await pub.delete(
            self.panel.host["bot"], _db, self.panel.owner_id, self.panel.name, self.selected)
        self.stop()
        await self.panel.refresh_visible(interaction.guild)
        await interaction.edit_original_response(
            content=f"Eliminadas: {deleted}. Pendientes: {failed}.", view=None)

    @discord.ui.button(label="Cancelar", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction, button):
        self.stop()
        await interaction.response.edit_message(content="Eliminación cancelada.", view=None)


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
        await interaction.response.defer()
        updated, failed = await pub.update(self.panel.host["bot"], _db, self.panel.owner_id,
            self.panel.name, self.panel.embed, self.panel.host["stamp_embed"], render)
        await interaction.edit_original_response(
            content=f"Guardado. Publicaciones actualizadas: {updated}; pendientes: {failed}.", view=None)
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
        await interaction.response.defer()
        deleted, failed = await pub.delete(self.panel.host["bot"], _db, self.panel.owner_id, self.panel.name)
        if failed:
            return await interaction.edit_original_response(
                content=f"Publicaciones eliminadas: {deleted}. Quedan {failed} pendientes; el borrador se conserva.", view=None)
        remove(self.panel.owner_id, self.panel.name)
        self.panel.name, self.panel.embed, self.panel.initial, self.panel.dirty = "", None, None, False
        self.panel.refresh()
        self.stop()
        await self.panel.refresh_visible(interaction.guild)
        await interaction.edit_original_response(content="Mensaje guardado y publicaciones eliminados.", view=None)

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
        panel.panel_message = await interaction.original_response()
