"""Carl-style embed builder, adapted to Discord's five action-row interface.

One draft, one parent panel, no automatic persistence and no extra ephemeral panels.
The server footer is always stamped by El Heraldo; it cannot be overwritten.
"""
from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import re
from urllib.parse import urlsplit

import discord
from heraldo_i18n import current_locale, guild_context

COPY = {
    "es-419": {
        "title":"Constructor de embed", "help":"Completa las secciones con el menú. La vista previa se actualiza sin publicar ni guardar.",
        "section":"Sección del embed", "main":"Contenido y color", "author":"Autor", "media":"Imágenes",
        "fields":"Campos adicionales", "date":"Fecha",
        "edit":"Editar sección", "add":"Añadir campo", "timestamp":"Fecha automática",
        "preview":"Vista previa", "clear":"Quitar embed", "back":"Volver",
        "role":"Insertar rol en la descripción", "channel":"Insertar canal en la descripción",
        "title_label":"Título", "description":"Descripción", "url":"Enlace del título (https://)",
        "color":"Color hexadecimal (#5865F2)", "author_name":"Nombre del autor",
        "author_url":"Enlace del autor (https://)", "author_icon":"Icono del autor (https://)",
        "image":"Imagen principal (https://)", "thumbnail":"Miniatura (https://)",
        "field_name":"Nombre del campo", "field_value":"Valor del campo", "inline":"En línea (sí/no)",
        "field_select":"Campo que deseas editar o retirar", "edit_field":"Editar campo",
        "delete_field":"Retirar campo", "fields_menu":"Administrar campos",
        "locked":"El nombre y el icono del servidor se añaden automáticamente. En Lab se usa El Heraldo's Labs 🧪. No se pueden reemplazar aquí.",
        "safe":"Las menciones insertadas en un embed son referencias visibles: NO notifican a roles. Para avisar, utiliza el texto normal o el rol de aviso.",
        "empty":"Sin contenido", "invalid":"Revisa el contenido, enlaces HTTPS, límites del embed y permisos.",
        "too_many":"El embed admite hasta 25 campos y un máximo de 6000 caracteres.",
        "nothing":"Todavía no hay campos.", "placeholder":"Selecciona una sección y pulsa Editar sección.",
        "timestamp_on":"Activada", "timestamp_off":"Desactivada", "new_field":"Nuevo campo",
        "info":"Formato Discord: título, descripción, color, autor, miniatura, imagen, hasta 25 campos, fecha y footer automático.",
        "write_hint":"Puedes escribir @Nombre del rol o #canal en la descripción. Utiliza los selectores para evitar errores de nombres.",
        "date_error": "Introduce una fecha válida de Santo Domingo o deja vacío para limpiar.",
        "date_input": "Fecha del embed (AAAA-MM-DD HH:MM)",
        "date_manual": "Seleccionar fecha",
    },
    "en-US": {
        "title":"Embed builder", "help":"Complete each section using the menu. The preview updates without posting or saving.",
        "section":"Embed section", "main":"Content and color", "author":"Author", "media":"Images",
        "fields":"Additional fields", "date":"Date",
        "edit":"Edit section", "add":"Add field", "timestamp":"Automatic date",
        "preview":"Preview", "clear":"Remove embed", "back":"Back",
        "role":"Insert role in description", "channel":"Insert channel in description",
        "title_label":"Title", "description":"Description", "url":"Title link (https://)",
        "color":"Hex color (#5865F2)", "author_name":"Author name",
        "author_url":"Author link (https://)", "author_icon":"Author icon (https://)",
        "image":"Main image (https://)", "thumbnail":"Thumbnail (https://)",
        "field_name":"Field name", "field_value":"Field value", "inline":"Inline (yes/no)",
        "field_select":"Choose a field to edit or remove", "edit_field":"Edit field",
        "delete_field":"Remove field", "fields_menu":"Manage fields",
        "locked":"Server name and icon are added automatically. Lab uses El Heraldo's Labs 🧪. They cannot be replaced here.",
        "safe":"Mentions inside embeds are visible references, NOT role notifications. To ping a role use regular message content or the alert role.",
        "empty":"Empty", "invalid":"Check content, HTTPS links, embed size limits and permissions.",
        "too_many":"An embed supports up to 25 fields and at most 6000 characters.",
        "nothing":"There are no fields yet.", "placeholder":"Choose a section, then Edit section.",
        "timestamp_on":"On", "timestamp_off":"Off", "new_field":"New field",
        "info":"Discord format: title, description, color, author, thumbnail, image, up to 25 fields, timestamp and automatic footer.",
        "write_hint":"You may type @Role name or #channel in descriptions. Use the selectors when names are ambiguous.",
        "date_error": "Enter a valid Santo Domingo date or leave empty to clear.",
        "date_input": "Embed date (YYYY-MM-DD HH:MM)",
        "date_manual": "Select date",
    },
    "pt-BR": {
        "title":"Construtor de embed", "help":"Preencha as seções pelo menu. A prévia é atualizada sem publicar ou salvar.",
        "section":"Seção do embed", "main":"Conteúdo e cor", "author":"Autor", "media":"Imagens",
        "fields":"Campos adicionais", "date":"Data",
        "edit":"Editar seção", "add":"Adicionar campo", "timestamp":"Data automática",
        "preview":"Prévia", "clear":"Remover embed", "back":"Voltar",
        "role":"Inserir cargo na descrição", "channel":"Inserir canal na descrição",
        "title_label":"Título", "description":"Descrição", "url":"Link do título (https://)",
        "color":"Cor hexadecimal (#5865F2)", "author_name":"Nome do autor",
        "author_url":"Link do autor (https://)", "author_icon":"Ícone do autor (https://)",
        "image":"Imagem principal (https://)", "thumbnail":"Miniatura (https://)",
        "field_name":"Nome do campo", "field_value":"Valor do campo", "inline":"Na mesma linha (sim/não)",
        "field_select":"Campo a editar ou remover", "edit_field":"Editar campo",
        "delete_field":"Remover campo", "fields_menu":"Gerenciar campos",
        "locked":"Nome e ícone do servidor são adicionados automaticamente. Lab usa El Heraldo's Labs 🧪. Não é possível substituí-los aqui.",
        "safe":"Menções nos embeds são referências visíveis, NÃO notificações. Para avisar use texto normal ou o cargo de aviso.",
        "empty":"Sem conteúdo", "invalid":"Verifique conteúdo, links HTTPS, limites do embed e permissões.",
        "too_many":"Um embed suporta até 25 campos e no máximo 6000 caracteres.",
        "nothing":"Ainda não há campos.", "placeholder":"Escolha uma seção e clique em Editar seção.",
        "timestamp_on":"Ativada", "timestamp_off":"Desativada", "new_field":"Novo campo",
        "info":"Formato Discord: título, descrição, cor, autor, miniatura, imagem, até 25 campos, data e rodapé automático.",
        "write_hint":"É possível digitar @Nome do cargo ou #canal na descrição. Use os seletores para nomes ambíguos.",
        "date_error": "Digite uma data válida de Santo Domingo ou deixe vazio para limpar.",
        "date_input": "Data do embed (AAAA-MM-DD HH:MM)",
        "date_manual": "Selecionar data",
    }
}


def t(key):
    return COPY.get(current_locale(), COPY["es-419"])[key]


def https_url(value):
    value = str(value or "").strip()
    if not value:
        return ""
    try:
        parts = urlsplit(value)
        if parts.scheme.lower() != "https" or not parts.hostname or parts.username or parts.password:
            raise ValueError("url")
        if not (1 <= len(value) <= 2048):
            raise ValueError("url")
    except Exception as exc:
        raise ValueError("url") from exc
    return value


def validate_data(data):
    if not isinstance(data, dict):
        raise ValueError("invalid")
    result = dict(data)
    title = str(result.get("title") or "")
    desc = str(result.get("description") or "")
    if len(title) > 256 or len(desc) > 4096:
        raise ValueError("size")
    color = str(result.get("color_hex") or "5865F2").lstrip("#")
    if not re.fullmatch(r"[0-9A-Fa-f]{6}", color):
        raise ValueError("color")
    result["color_hex"] = color.upper()
    for key in ("url", "image_url", "thumbnail_url"):
        result[key] = https_url(result.get(key))
    author = result.get("author") or {}
    if not isinstance(author, dict):
        raise ValueError("author")
    if len(str(author.get("name") or "")) > 256:
        raise ValueError("author")
    result["author"] = {k: str(author.get(k) or "") for k in ("name", "url", "icon_url")}
    result["author"]["url"] = https_url(result["author"]["url"])
    result["author"]["icon_url"] = https_url(result["author"]["icon_url"])
    if (result["author"]["url"] or result["author"]["icon_url"]) and not result["author"]["name"]:
        raise ValueError("author")
    fields = result.get("fields") or []
    if not isinstance(fields, list) or len(fields) > 25:
        raise ValueError("fields")
    out_fields = []
    for field in fields:
        if not isinstance(field, dict):
            raise ValueError("fields")
        name, value = str(field.get("name") or ""), str(field.get("value") or "")
        if not (1 <= len(name) <= 256 and 1 <= len(value) <= 1024):
            raise ValueError("fields")
        out_fields.append({"name": name, "value": value, "inline": bool(field.get("inline", False))})
    result["fields"] = out_fields
    total = (len(title) + len(desc) + len(result["author"]["name"])
             + sum(len(f["name"]) + len(f["value"]) for f in out_fields))
    if total > 5800:  # reserve space for the mandatory global footer
        raise ValueError("size")
    result["timestamp"] = bool(result.get("timestamp", False))
    custom_date = str(result.get("timestamp_value") or "").strip()
    if custom_date:
        try:
            parsed = datetime.fromisoformat(custom_date.replace("Z", "+00:00"))
            if parsed.tzinfo is None or len(custom_date) > 40:
                raise ValueError("date")
        except ValueError as exc:
            raise ValueError("date") from exc
    result["timestamp_value"] = custom_date
    return result


def has_content(data):
    if not data:
        return False
    return any((data.get("title"), data.get("description"),
                (data.get("author") or {}).get("name"), data.get("image_url"),
                data.get("thumbnail_url"), data.get("fields")))


def render(data, stamp, guild):
    if not has_content(data):
        return None
    data = validate_data(data)
    embed = discord.Embed(
        title=data.get("title") or None,
        description=data.get("description") or None,
        url=data.get("url") or None,
        color=int(data["color_hex"], 16),
        timestamp=(datetime.fromisoformat(data["timestamp_value"]) if data["timestamp_value"]
                   else datetime.now(timezone.utc)) if data["timestamp"] else None,
    )
    author = data.get("author") or {}
    if author.get("name"):
        embed.set_author(name=author["name"], url=author["url"] or None,
                         icon_url=author["icon_url"] or None)
    if data.get("image_url"):
        embed.set_image(url=data["image_url"])
    if data.get("thumbnail_url"):
        embed.set_thumbnail(url=data["thumbnail_url"])
    for field in data["fields"]:
        embed.add_field(name=field["name"], value=field["value"],
                        inline=field["inline"])
    return stamp(embed, guild)


def owner(interaction, parent):
    return (interaction.guild is not None
            and interaction.guild.id == parent.guild_id
            and interaction.user.id == parent.owner_id
            and interaction.user.guild_permissions.manage_guild)


async def denied(interaction):
    from message_autofeeds import respond_error
    await respond_error(interaction, "denied")


def update(parent, data):
    validated = validate_data(data)
    parent.embed = validated if has_content(validated) else None
    parent.dirty = True


async def redraw(interaction, parent, section):
    next_view = EmbedBuilderView(parent, section=section)
    await interaction.response.edit_message(
        content=next_view.summary(), embed=next_view.preview_embed(interaction.guild),
        view=next_view, allowed_mentions=discord.AllowedMentions.none())


class SectionModal(discord.ui.Modal):
    def __init__(self, parent, section):
        super().__init__(title=t(section)[:45])
        self.parent, self.section = parent, section
        old = parent.embed or {}
        fields = {
            "main": (
                ("title", "title_label", 256, False, old.get("title")),
                ("description", "description", 4000, True, old.get("description")),
                ("url", "url", 2048, False, old.get("url")),
                ("color_hex", "color", 7, False, old.get("color_hex", "5865F2")),
            ),
            "author": (
                ("name", "author_name", 256, False, (old.get("author") or {}).get("name")),
                ("url", "author_url", 2048, False, (old.get("author") or {}).get("url")),
                ("icon_url", "author_icon", 2048, False, (old.get("author") or {}).get("icon_url")),
            ),
            "media": (
                ("image_url", "image", 2048, False, old.get("image_url")),
                ("thumbnail_url", "thumbnail", 2048, False, old.get("thumbnail_url")),
            ),
        }
        self.inputs = {}
        for key, label, length, paragraph, default in fields[section]:
            control = discord.ui.TextInput(
                label=t(label)[:45], max_length=length, required=False,
                style=discord.TextStyle.paragraph if paragraph else discord.TextStyle.short,
                default=str(default or ""),
            )
            self.inputs[key] = control
            self.add_item(control)

    @guild_context
    async def on_submit(self, interaction):
        if not owner(interaction, self.parent):
            return await denied(interaction)
        data = dict(self.parent.embed or {})
        values = {key: str(input_field).strip() for key, input_field in self.inputs.items()}
        if self.section == "main":
            from autofeed_setup import resolve_inline_embed_names
            values["description"] = resolve_inline_embed_names(
                interaction.guild, values["description"])
            # Discord does not render role/channel references inside embed titles.
            # Keep the title literal; description supports Discord mention tokens.
            data.update(values)
        elif self.section == "author":
            data["author"] = values
        else:
            data.update(values)
        try:
            update(self.parent, data)
        except ValueError:
            from message_autofeeds import respond_error
            return await respond_error(interaction, "invalid")
        await redraw(interaction, self.parent, self.section)



class DateStampModal(discord.ui.Modal):
    """Fecha mostrada dentro del embed, independiente de la programación."""
    def __init__(self, parent):
        super().__init__(title=t("date_manual"))
        self.parent = parent
        previous = (parent.embed or {}).get("timestamp_value") or ""
        if previous:
            try:
                previous = datetime.fromisoformat(previous).astimezone(
                    ZoneInfo("America/Santo_Domingo")).strftime("%Y-%m-%d %H:%M")
            except ValueError:
                previous = ""
        self.date = discord.ui.TextInput(label=t("date_input"), required=False,
                                         max_length=16, default=previous)
        self.add_item(self.date)

    @guild_context
    async def on_submit(self, interaction):
        if not owner(interaction, self.parent):
            return await denied(interaction)
        raw = str(self.date).strip()
        data = dict(self.parent.embed or {})
        if raw:
            try:
                local = datetime.strptime(raw, "%Y-%m-%d %H:%M")
                instant = local.replace(tzinfo=ZoneInfo("America/Santo_Domingo"))
                data["timestamp_value"] = instant.astimezone(timezone.utc).isoformat()
                data["timestamp"] = True
            except ValueError:
                from message_autofeeds import respond_error
                return await interaction.response.send_message(t("date_error"), ephemeral=True)
        else:
            data["timestamp_value"], data["timestamp"] = "", False
        try:
            update(self.parent, data)
        except ValueError:
            from message_autofeeds import respond_error
            return await respond_error(interaction, "invalid")
        await redraw(interaction, self.parent, "date")


class FieldModal(discord.ui.Modal):
    def __init__(self, parent, *, index=None):
        super().__init__(title=t("edit_field") if index is not None else t("new_field"))
        self.parent, self.index = parent, index
        fields = (parent.embed or {}).get("fields") or []
        old = fields[index] if index is not None else {}
        self.name = discord.ui.TextInput(
            label=t("field_name")[:45], max_length=256, default=old.get("name", ""))
        self.value = discord.ui.TextInput(
            label=t("field_value")[:45], max_length=1024, style=discord.TextStyle.paragraph,
            default=old.get("value", ""))
        self.inline = discord.ui.TextInput(
            label=t("inline")[:45], max_length=4,
            default="sí" if old.get("inline") else "no")
        for field in (self.name, self.value, self.inline):
            self.add_item(field)

    @guild_context
    async def on_submit(self, interaction):
        if not owner(interaction, self.parent):
            return await denied(interaction)
        raw = str(self.inline).strip().casefold()
        if raw not in ("sí", "si", "yes", "sim", "true", "no", "false", "não", "nao"):
            from message_autofeeds import respond_error
            return await respond_error(interaction, "invalid")
        data = dict(self.parent.embed or {})
        fields = [dict(f) for f in data.get("fields") or []]
        entry = {"name": str(self.name).strip(), "value": str(self.value).strip(),
                 "inline": raw in ("sí", "si", "yes", "sim", "true")}
        if self.index is None:
            fields.append(entry)
        else:
            fields[self.index] = entry
        data["fields"] = fields
        try:
            update(self.parent, data)
        except ValueError:
            from message_autofeeds import respond_error
            return await respond_error(interaction, "invalid")
        await redraw(interaction, self.parent, "fields")


class FieldManageView(discord.ui.View):
    def __init__(self, parent):
        super().__init__(timeout=900)
        self.parent, self.selected = parent, None
        fields = (parent.embed or {}).get("fields") or []
        if fields:
            self.choose = discord.ui.Select(
                placeholder=t("field_select"), row=0,
                options=[discord.SelectOption(label=f"{i+1}. {f['name']}"[:100],
                                               value=str(i)) for i, f in enumerate(fields)])
            self.choose.callback = self.chosen
            self.add_item(self.choose)
        self.new.label, self.edit.label, self.remove.label = (
            t("add"), t("edit_field"), t("delete_field"))
        self.back.label = t("back")
        self.edit.disabled = self.remove.disabled = not fields
        self.new.disabled = len(fields) >= 25

    @guild_context
    async def interaction_check(self, interaction):
        if not owner(interaction, self.parent):
            await denied(interaction)
            return False
        return True

    @guild_context
    async def chosen(self, interaction):
        self.selected = int(self.choose.values[0])
        await interaction.response.edit_message(
            content=self.summary(), view=self, allowed_mentions=discord.AllowedMentions.none())

    def summary(self):
        fields = (self.parent.embed or {}).get("fields") or []
        return (t("fields_menu") + "\n\n" +
                ("\n".join(f"{i+1}. {f['name'][:80]}" for i, f in enumerate(fields))
                 if fields else t("nothing")))

    @discord.ui.button(label="Añadir campo", style=discord.ButtonStyle.primary, row=1)
    @guild_context
    async def new(self, interaction, button):
        await interaction.response.send_modal(FieldModal(self.parent))

    @discord.ui.button(label="Editar campo", style=discord.ButtonStyle.secondary, row=1)
    @guild_context
    async def edit(self, interaction, button):
        if self.selected is None:
            return await interaction.response.send_message(t("field_select"), ephemeral=True)
        await interaction.response.send_modal(FieldModal(self.parent, index=self.selected))

    @discord.ui.button(label="Retirar campo", style=discord.ButtonStyle.danger, row=1)
    @guild_context
    async def remove(self, interaction, button):
        if self.selected is None:
            return await interaction.response.send_message(t("field_select"), ephemeral=True)
        data = dict(self.parent.embed or {})
        fields = list(data.get("fields") or [])
        fields.pop(self.selected)
        data["fields"] = fields
        update(self.parent, data)
        new_view = FieldManageView(self.parent)
        await interaction.response.edit_message(
            content=new_view.summary(), embed=render(self.parent.embed,
                self.parent.host["stamp_embed"], interaction.guild), view=new_view,
            allowed_mentions=discord.AllowedMentions.none())

    @discord.ui.button(label="Volver", style=discord.ButtonStyle.secondary, row=2)
    @guild_context
    async def back(self, interaction, button):
        await redraw(interaction, self.parent, "fields")


class EmbedBuilderView(discord.ui.View):
    def __init__(self, parent, *, section="main"):
        super().__init__(timeout=900)
        self.parent, self.section = parent, section
        self.section_select = discord.ui.Select(
            placeholder=t("section"), row=0, options=[
                discord.SelectOption(label=t(name), value=name, default=section == name)
                for name in ("main", "author", "media", "fields", "date")])
        self.section_select.callback = self.pick_section
        self.add_item(self.section_select)
        self.roles = discord.ui.RoleSelect(
            placeholder=t("role"), row=1, min_values=1, max_values=1)
        self.roles.callback = self.add_role
        self.add_item(self.roles)
        self.channels = discord.ui.ChannelSelect(
            placeholder=t("channel"), row=2, min_values=1, max_values=1,
            channel_types=[discord.ChannelType.text])
        self.channels.callback = self.add_channel
        self.add_item(self.channels)
        for button, key in ((self.edit, "edit"), (self.add_field, "add"),
                            (self.timestamp, "timestamp"), (self.date_manual, "date_manual"), (self.preview, "preview"),
                            (self.clear, "clear"), (self.back, "back")):
            button.label = t(key)
        self.edit.disabled = section in ("date", "fields")
        self.add_field.disabled = section != "fields"
        self.timestamp.disabled = section != "date"
        self.date_manual.disabled = section != "date"

    def summary(self):
        data = self.parent.embed or {}
        parts = [f"**{t('title')}**", t("help"), t("info"), "",
                 f"**{t('section')}:** {t(self.section)}",
                 f"**{t('title_label')}:** {str(data.get('title') or t('empty'))[:140]}",
                 f"**{t('description')}:** {str(data.get('description') or t('empty'))[:200]}",
                 f"**{t('author')}:** {str((data.get('author') or {}).get('name') or t('empty'))[:100]}",
                 f"**{t('fields')}:** {len(data.get('fields') or [])}",
                 f"**{t('timestamp')}:** {str(data.get('timestamp_value') or t('timestamp_on')) if data.get('timestamp') else t('timestamp_off')}"]
        if self.section in ("main", "fields"):
            parts += ["", t("write_hint")]
        parts += ["", t("locked"), t("safe")]
        return "\n".join(parts)

    def preview_embed(self, guild):
        return render(self.parent.embed, self.parent.host["stamp_embed"], guild)

    @guild_context
    async def interaction_check(self, interaction):
        if not owner(interaction, self.parent):
            await denied(interaction)
            return False
        return True

    @guild_context
    async def pick_section(self, interaction):
        await redraw(interaction, self.parent, self.section_select.values[0])

    async def add_token(self, interaction, token):
        from message_autofeeds import referenced_mentions, respond_error
        data = dict(self.parent.embed or {})
        old = str(data.get("description") or "")
        if len(old) + len(token) + 1 > 4000:
            return await respond_error(interaction, "invalid")
        data["description"] = (old + " " + token).strip()
        try:
            referenced_mentions(interaction.guild, {"embed": data, "text": self.parent.text,
                                                     "role": self.parent.role_id})
            update(self.parent, data)
        except ValueError:
            return await respond_error(interaction, "invalid")
        await redraw(interaction, self.parent, self.section)

    @guild_context
    async def add_role(self, interaction):
        role = self.roles.values[0]
        if role.guild.id != self.parent.guild_id:
            return await denied(interaction)
        await self.add_token(interaction, role.mention)

    @guild_context
    async def add_channel(self, interaction):
        channel = self.channels.values[0]
        if channel.guild.id != self.parent.guild_id:
            return await denied(interaction)
        await self.add_token(interaction, channel.mention)

    @discord.ui.button(label="Editar sección", style=discord.ButtonStyle.primary, row=3)
    @guild_context
    async def edit(self, interaction, button):
        await interaction.response.send_modal(SectionModal(self.parent, self.section))

    @discord.ui.button(label="Añadir campo", style=discord.ButtonStyle.secondary, row=3)
    @guild_context
    async def add_field(self, interaction, button):
        view = FieldManageView(self.parent)
        await interaction.response.edit_message(
            content=view.summary(), embed=self.preview_embed(interaction.guild),
            view=view, allowed_mentions=discord.AllowedMentions.none())

    @discord.ui.button(label="Fecha automática", style=discord.ButtonStyle.secondary, row=3)
    @guild_context
    async def timestamp(self, interaction, button):
        data = dict(self.parent.embed or {})
        data["timestamp"] = not bool(data.get("timestamp", False))
        try:
            update(self.parent, data)
        except ValueError:
            from message_autofeeds import respond_error
            return await respond_error(interaction, "invalid")
        await redraw(interaction, self.parent, "date")

    @discord.ui.button(label="Seleccionar fecha", style=discord.ButtonStyle.primary, row=3)
    @guild_context
    async def date_manual(self, interaction, button):
        await interaction.response.send_modal(DateStampModal(self.parent))

    @discord.ui.button(label="Vista previa", style=discord.ButtonStyle.secondary, row=4)
    @guild_context
    async def preview(self, interaction, button):
        await redraw(interaction, self.parent, self.section)

    @discord.ui.button(label="Quitar embed", style=discord.ButtonStyle.danger, row=4)
    @guild_context
    async def clear(self, interaction, button):
        self.parent.embed = None
        self.parent.dirty = True
        await redraw(interaction, self.parent, "main")

    @discord.ui.button(label="Volver", style=discord.ButtonStyle.secondary, row=4)
    @guild_context
    async def back(self, interaction, button):
        from autofeed_setup import editor_panel_kwargs
        await interaction.response.edit_message(
            **editor_panel_kwargs(self.parent, interaction.guild),
            view=self.parent, allowed_mentions=discord.AllowedMentions.none())
