"""Editor AutoFeeds para /setup -> Mensajes -> Programaciones.

Discord no ofrece campos web tipo Carl-bot: cada fila se representa con un
selector o un botón/modal dentro del mismo mensaje de configuración.
"""
from __future__ import annotations
from datetime import datetime, timedelta, timezone
import json
import uuid

import discord
from heraldo_i18n import guild_context, use_guild
import message_autofeeds as feeds

LANG = {
    "es-419": {
        "hub_title": "**Programaciones de mensajes**",
        "hub_help": "Crea publicaciones como en AutoFeeds: elige canal, escribe el mensaje o diseña un embed, establece fecha, mención y repetición. Nada se publica antes de confirmar.",
        "new": "Crear programación", "manage": "Gestionar programaciones", "permissions": "Permisos",
        "new_title": "**Crear Autofeed**", "edit_title": "**Editar programación**",
        "select_channel": "Canal donde publicar", "select_role": "Rol para mencionar (opcional)",
        "message": "Mensaje", "embed": "Editor de embed", "schedule": "Fecha y repetición",
        "preview": "Vista previa", "silent": "Sin rol", "save": "Guardar cambios",
        "discard": "Descartar cambios", "confirm": "Confirmar cambios", "back": "Volver",
        "empty": "Sin definir", "no_repeat": "No se repite", "start": "Fecha y hora",
        "repeat": "Repetir cada", "members": "Rol mencionado", "none": "Ninguno",
        "warning": "Completa el canal, el mensaje o embed y una fecha futura.",
        "invalid_interval": "La repetición debe ser de al menos una hora (o un mes).",
        "time_format": "AAAA-MM-DD HH:MM", "months": "Meses", "days": "Días",
        "hours": "Horas", "minutes": "Minutos",
        "saved": "Programación guardada.", "cancelled": "Cambios descartados.",
        "unavailable": "Selecciona un canal válido y comprueba los permisos.",
        "conflict": "La programación cambió en otra sesión. Ábrela de nuevo.",
        "limit": "Se alcanzó el límite de programaciones de este servidor.",
        "embed_title": "Título del embed", "embed_desc": "Descripción del embed",
        "embed_color": "Color hexadecimal (opcional)",
        "message_hint": "Contenido del mensaje (máximo 2000 caracteres)",
        "saved_tip": "Confirma para guardar; seleccionar o editar no guarda automáticamente.",
        "choose": "Selecciona una programación",
        "new_preview": "Vista previa de la publicación; no se enviará nada al canal.",
        "insert_mention": "Insertar mención",
        "mention_help": "Elige si insertar el canal o rol en el texto o la descripción del embed. Solo el rol incluido en el mensaje normal puede notificar.",
        "mention_target": "Insertar en",
        "in_text": "Mensaje",
        "in_embed": "Descripción del embed",
        "choose_role": "Seleccionar rol",
        "choose_channel": "Seleccionar canal",
        "date_picker": "Fecha y hora",
        "date_only": "Fecha (AAAA-MM-DD)",
        "time_only": "Hora (HH:MM)",
        "repeat_picker": "Frecuencia",
        "choose_frequency": "Elegir frecuencia",
        "once": "Una vez",
        "daily": "Diaria",
        "weekly": "Semanal",
        "monthly": "Mensual",
        "custom": "Personalizada",
        "role_again": "Para volver a elegir un rol de aviso, utiliza el selector superior.",
        "date_help": "Zona horaria: Santo Domingo (UTC−4). Fecha y hora se configuran por separado.",
        "embed_hub_title": "**Editor de embed**",
        "embed_hub_hint": "Selecciona un rol o canal para colocarlo en la descripción. Después puedes abrir Editar texto y diseño. No necesitas escribir IDs.",
        "embed_notify_note": "Los roles dentro del embed se muestran, pero no envían notificaciones. Para avisar utiliza el rol de aviso o el texto normal.",
        "embed_choose_role": "Añadir rol al embed",
        "embed_choose_channel": "Añadir canal al embed",
        "embed_text_design": "Editar texto y diseño",
        "embed_preview": "Vista previa del embed",
        "embed_remove": "Quitar embed",
        "embed_inserted": "Mención añadida a la descripción del embed.",
        "embed_none": "Todavía no hay texto ni menciones en el embed.",
        "embed_section_title": "Título",
        "embed_section_desc": "Descripción",
        "embed_manual_note": "Los campos de Discord no sugieren menciones mientras escribes. Usa los selectores de este editor para insertarlas.",
        "embed_deleted": "Embed retirado del borrador.",
        "embed_references": "Referencias insertadas",
    },
    "en-US": {
        "hub_title": "**Message schedules**", "hub_help": "Create posts like AutoFeeds: choose a channel, write a message or build an embed, set the date, mention, and repeat interval. Nothing is posted before confirmation.",
        "new": "Create schedule", "manage": "Manage schedules", "permissions": "Permissions",
        "new_title": "**Create Autofeed**", "edit_title": "**Edit schedule**",
        "select_channel": "Destination channel", "select_role": "Role to mention (optional)",
        "message": "Message", "embed": "Embed builder", "schedule": "Date and repeat",
        "preview": "Preview", "silent": "No role", "save": "Save changes",
        "discard": "Discard changes", "confirm": "Confirm changes", "back": "Back",
        "empty": "Not set", "no_repeat": "No repeat", "start": "Date and time",
        "repeat": "Repeat every", "members": "Mentioned role", "none": "None",
        "warning": "Choose a channel, message or embed, and a future date.",
        "invalid_interval": "The repeat interval must be at least one hour (or one month).",
        "time_format": "YYYY-MM-DD HH:MM", "months": "Months", "days": "Days",
        "hours": "Hours", "minutes": "Minutes",
        "saved": "Schedule saved.", "cancelled": "Changes discarded.",
        "unavailable": "Select a valid channel and check permissions.",
        "conflict": "The schedule changed in another session. Open it again.",
        "limit": "The server's schedule limit has been reached.",
        "embed_title": "Embed title", "embed_desc": "Embed description",
        "embed_color": "Hex color (optional)",
        "message_hint": "Message content (maximum 2000 characters)",
        "saved_tip": "Confirm to save; selecting or editing never saves automatically.",
        "choose": "Choose a schedule",
        "new_preview": "Post preview; nothing will be sent to the channel.",
        "insert_mention": "Insert mention",
        "mention_help": "Select whether to insert a channel or role in the text or embed description. Only a role in normal message content can notify.",
        "mention_target": "Insert into",
        "in_text": "Message",
        "in_embed": "Embed description",
        "choose_role": "Select role",
        "choose_channel": "Select channel",
        "date_picker": "Date and time",
        "date_only": "Date (YYYY-MM-DD)",
        "time_only": "Time (HH:MM)",
        "repeat_picker": "Frequency",
        "choose_frequency": "Choose frequency",
        "once": "Once",
        "daily": "Daily",
        "weekly": "Weekly",
        "monthly": "Monthly",
        "custom": "Custom",
        "role_again": "To pick an alert role again, use the role selector above.",
        "date_help": "Time zone: Santo Domingo (UTC−4). Choose date and time separately.",
        "embed_hub_title": "**Embed editor**",
        "embed_hub_hint": "Select a role or channel to insert it into the description. Then use Edit text and design. No IDs needed.",
        "embed_notify_note": "Roles inside embeds display but do not notify. To ping a role, use the alert role or regular message text.",
        "embed_choose_role": "Add role to embed",
        "embed_choose_channel": "Add channel to embed",
        "embed_text_design": "Edit text and design",
        "embed_preview": "Embed preview",
        "embed_remove": "Remove embed",
        "embed_inserted": "Mention added to the embed description.",
        "embed_none": "No embed text or mentions yet.",
        "embed_section_title": "Title",
        "embed_section_desc": "Description",
        "embed_manual_note": "Discord's form text fields do not suggest mentions as you type. Use these selectors to insert them.",
        "embed_deleted": "Embed removed from draft.",
        "embed_references": "Inserted references",
    },
    "pt-BR": {
        "hub_title": "**Programações de mensagens**", "hub_help": "Crie publicações como no AutoFeeds: escolha canal, texto ou embed, data, menção e repetição. Nada é publicado antes de confirmar.",
        "new": "Criar programação", "manage": "Gerenciar programações", "permissions": "Permissões",
        "new_title": "**Criar Autofeed**", "edit_title": "**Editar programação**",
        "select_channel": "Canal de destino", "select_role": "Cargo a mencionar (opcional)",
        "message": "Mensagem", "embed": "Editor de embed", "schedule": "Data e repetição",
        "preview": "Prévia", "silent": "Sem cargo", "save": "Salvar alterações",
        "discard": "Descartar alterações", "confirm": "Confirmar alterações", "back": "Voltar",
        "empty": "Não definido", "no_repeat": "Não repetir", "start": "Data e hora",
        "repeat": "Repetir a cada", "members": "Cargo mencionado", "none": "Nenhum",
        "warning": "Escolha o canal, texto ou embed e uma data futura.",
        "invalid_interval": "O intervalo deve ser de pelo menos uma hora (ou um mês).",
        "time_format": "AAAA-MM-DD HH:MM", "months": "Meses", "days": "Dias",
        "hours": "Horas", "minutes": "Minutos",
        "saved": "Programação salva.", "cancelled": "Alterações descartadas.",
        "unavailable": "Selecione um canal válido e confira as permissões.",
        "conflict": "A programação foi alterada em outra sessão. Abra novamente.",
        "limit": "O limite de programações deste servidor foi atingido.",
        "embed_title": "Título do embed", "embed_desc": "Descrição do embed",
        "embed_color": "Cor hexadecimal (opcional)",
        "message_hint": "Conteúdo da mensagem (máximo 2000 caracteres)",
        "saved_tip": "Confirme para salvar; selecionar ou editar não salva automaticamente.",
        "choose": "Selecione uma programação",
        "new_preview": "Prévia da publicação; nada será enviado ao canal.",
        "insert_mention": "Inserir menção",
        "mention_help": "Escolha inserir canal ou cargo no texto ou na descrição do embed. Apenas o cargo no texto comum pode notificar.",
        "mention_target": "Inserir em",
        "in_text": "Mensagem",
        "in_embed": "Descrição do embed",
        "choose_role": "Selecionar cargo",
        "choose_channel": "Selecionar canal",
        "date_picker": "Data e hora",
        "date_only": "Data (AAAA-MM-DD)",
        "time_only": "Hora (HH:MM)",
        "repeat_picker": "Frequência",
        "choose_frequency": "Escolher frequência",
        "once": "Uma vez",
        "daily": "Diária",
        "weekly": "Semanal",
        "monthly": "Mensal",
        "custom": "Personalizada",
        "role_again": "Para voltar a selecionar um cargo de aviso, use o seletor acima.",
        "date_help": "Fuso horário: Santo Domingo (UTC−4). Defina data e hora separadamente.",
        "embed_hub_title": "**Editor de embed**",
        "embed_hub_hint": "Selecione um cargo ou canal para inserir na descrição. Depois use Editar texto e design. Não precisa de IDs.",
        "embed_notify_note": "Cargos dentro do embed aparecem, mas não notificam. Para avisar, use o cargo de aviso ou texto normal.",
        "embed_choose_role": "Adicionar cargo ao embed",
        "embed_choose_channel": "Adicionar canal ao embed",
        "embed_text_design": "Editar texto e design",
        "embed_preview": "Prévia do embed",
        "embed_remove": "Remover embed",
        "embed_inserted": "Menção adicionada à descrição do embed.",
        "embed_none": "Ainda não há texto nem menções no embed.",
        "embed_section_title": "Título",
        "embed_section_desc": "Descrição",
        "embed_manual_note": "Os campos de texto do formulário Discord não sugerem menções ao digitar. Use os seletores deste editor.",
        "embed_deleted": "Embed removido do rascunho.",
        "embed_references": "Referências inseridas",
    }
}


def t(key):
    from heraldo_i18n import current_locale
    return LANG.get(current_locale(), LANG["es-419"])[key]


def _owner(interaction, guild_id, owner_id):
    return bool(interaction.guild and interaction.guild.id == guild_id
                and interaction.user.id == owner_id
                and interaction.user.guild_permissions.manage_guild)


def setup_panel(host, guild_id, owner_id):
    view = AutofeedHubView(host, guild_id, owner_id)
    return view.summary(), view


class AutofeedHubView(discord.ui.View):
    def __init__(self, host, guild_id, owner_id):
        super().__init__(timeout=900)
        self.host, self.guild_id, self.owner_id = host, guild_id, owner_id
        self.create.label, self.manage.label = t("new"), t("manage")
        self.permissions.label, self.back.label = t("permissions"), t("back")

    def summary(self):
        jobs = [j for j in feeds.get_jobs(self.host, self.guild_id)
                if j.get("autofeed")]
        active = sum(not j.get("paused") for j in jobs)
        return (t("hub_title") + "\n\n" + t("hub_help")
                + f"\n\n{t('manage')}: **{len(jobs)}** · {t('start')}: **{active}**")

    @guild_context
    async def interaction_check(self, interaction):
        if not _owner(interaction, self.guild_id, self.owner_id):
            await feeds.respond_error(interaction, "denied")
            return False
        return True

    @discord.ui.button(label="Crear programación", style=discord.ButtonStyle.primary, row=0)
    @guild_context
    async def create(self, interaction, button):
        editor = AutofeedEditorView(self.host, self.guild_id, self.owner_id)
        await interaction.response.edit_message(content=editor.summary(), embed=None, view=editor)

    @discord.ui.button(label="Gestionar programaciones", style=discord.ButtonStyle.secondary, row=0)
    @guild_context
    async def manage(self, interaction, button):
        jobs = [j for j in feeds.get_jobs(self.host, self.guild_id) if j.get("autofeed")]
        if not jobs:
            return await feeds.respond_error(interaction, "no_jobs")
        view = feeds.ManageView(self.host, self.guild_id, self.owner_id, jobs,
                                from_setup=True)
        await interaction.response.edit_message(
            content="\n".join(feeds.show_job(j, detail=False) for j in jobs[:8]),
            embed=None, view=view)

    @discord.ui.button(label="Permisos", style=discord.ButtonStyle.secondary, row=1)
    @guild_context
    async def permissions(self, interaction, button):
        view = feeds.PolicyView(self.host, self.guild_id, self.owner_id, return_to_setup=True)
        await interaction.response.edit_message(content=view.summary(), embed=None, view=view)

    @discord.ui.button(label="Volver", style=discord.ButtonStyle.secondary, row=1)
    @guild_context
    async def back(self, interaction, button):
        await interaction.response.edit_message(
            content=self.host["heraldo_messages_setup_content"](),
            embed=None,
            view=self.host["HeraldoMessagesSetupView"](self.guild_id, self.owner_id))


class MessageModal(discord.ui.Modal):
    def __init__(self, editor):
        super().__init__(title=t("message"))
        self.editor = editor
        self.message = discord.ui.TextInput(label=t("message"), placeholder=t("message_hint"),
                                             style=discord.TextStyle.paragraph,
                                             required=False, max_length=1900,
                                             default=editor.text)
        self.add_item(self.message)

    @guild_context
    async def on_submit(self, interaction):
        if not _owner(interaction, self.editor.guild_id, self.editor.owner_id):
            return await feeds.respond_error(interaction, "denied")
        self.editor.text = str(self.message).strip()
        self.editor.dirty = True
        await interaction.response.edit_message(
            content=self.editor.summary(), embed=None, view=self.editor)


class EmbedModal(discord.ui.Modal):
    def __init__(self, editor, *, from_embed_editor=False):
        super().__init__(title=t("embed"))
        self.editor = editor
        self.from_embed_editor = from_embed_editor
        old = editor.embed or {}
        self.title_input = discord.ui.TextInput(label=t("embed_title"), required=False,
                                                 max_length=256, default=old.get("title", ""))
        self.desc = discord.ui.TextInput(label=t("embed_desc"), style=discord.TextStyle.paragraph,
                                        required=False, max_length=4000, default=old.get("description", ""))
        self.color = discord.ui.TextInput(label=t("embed_color"), required=False,
                                         max_length=7, default=old.get("color_hex", "5865F2"))
        for item in (self.title_input, self.desc, self.color):
            self.add_item(item)

    @guild_context
    async def on_submit(self, interaction):
        if not _owner(interaction, self.editor.guild_id, self.editor.owner_id):
            return await feeds.respond_error(interaction, "denied")
        value = str(self.color).strip().lstrip("#")
        if value and (len(value) != 6 or any(c not in "0123456789abcdefABCDEF" for c in value)):
            return await feeds.respond_error(interaction, "invalid")
        title, desc = str(self.title_input).strip(), str(self.desc).strip()
        self.editor.embed = ({"title": title, "description": desc,
                              "color_hex": value or "5865F2"} if (title or desc) else None)
        self.editor.dirty = True
        if self.from_embed_editor:
            view = EmbedEditorView(self.editor)
            await interaction.response.edit_message(
                content=view.summary(interaction.guild),
                embed=view.preview_embed(interaction.guild), view=view,
                allowed_mentions=discord.AllowedMentions.none())
        else:
            await interaction.response.edit_message(
                content=self.editor.summary(), embed=None, view=self.editor)


def repeat_parts(months, days, hours, minutes):
    values = (months, days, hours, minutes)
    if any(type(x) is not int or x < 0 for x in values):
        raise ValueError("negative")
    if months > 120 or days > 365 or hours > 8760 or minutes > 59:
        raise ValueError("range")
    if months == 0 and days * 1440 + hours * 60 + minutes < 60:
        if any(values):
            raise ValueError("short")
        return None
    return dict(zip(("months", "days", "hours", "minutes"), values))


class DateTimeModal(discord.ui.Modal):
    """Use separate date and time inputs and a local-time preview."""
    def __init__(self, editor):
        super().__init__(title=t("date_picker"))
        self.editor = editor
        local = editor.start.astimezone(editor.timezone) if editor.start else (
            datetime.now(editor.timezone) + timedelta(days=1)).replace(
                hour=18, minute=0, second=0, microsecond=0)
        self.date = discord.ui.TextInput(label=t("date_only"),
            default=local.strftime("%Y-%m-%d"), placeholder="2026-11-01", max_length=10)
        self.time = discord.ui.TextInput(label=t("time_only"),
            default=local.strftime("%H:%M"), placeholder="18:00", max_length=5)
        self.add_item(self.date)
        self.add_item(self.time)

    @guild_context
    async def on_submit(self, interaction):
        if not _owner(interaction, self.editor.guild_id, self.editor.owner_id):
            return await feeds.respond_error(interaction, "denied")
        try:
            self.editor.start = feeds.start_from_form(
                f"{str(self.date).strip()} {str(self.time).strip()}",
                "America/Santo_Domingo")
        except ValueError:
            return await feeds.respond_error(interaction, "invalid")
        self.editor.dirty = True
        await interaction.response.edit_message(
            content=self.editor.summary(), embed=None, view=self.editor)


class CustomRepeatModal(discord.ui.Modal):
    def __init__(self, editor):
        super().__init__(title=t("repeat_picker"))
        self.editor = editor
        parts = editor.parts or {}
        self.fields = [discord.ui.TextInput(
            label=t(key), default=str(parts.get(key, 0)), max_length=4)
            for key in ("months", "days", "hours", "minutes")]
        for field in self.fields:
            self.add_item(field)

    @guild_context
    async def on_submit(self, interaction):
        if not _owner(interaction, self.editor.guild_id, self.editor.owner_id):
            return await feeds.respond_error(interaction, "denied")
        try:
            parts = repeat_parts(*(int(str(field).strip()) for field in self.fields))
            if parts is None:
                raise ValueError("short")
        except ValueError:
            return await interaction.response.send_message(
                t("invalid_interval"), ephemeral=True)
        self.editor.parts = parts
        self.editor.dirty = True
        await interaction.response.edit_message(
            content=self.editor.summary(), embed=None, view=self.editor)


PRESETS = {
    "once": None,
    "daily": {"months": 0, "days": 1, "hours": 0, "minutes": 0},
    "weekly": {"months": 0, "days": 7, "hours": 0, "minutes": 0},
    "monthly": {"months": 1, "days": 0, "hours": 0, "minutes": 0},
}


class FrequencyPickerView(discord.ui.View):
    def __init__(self, editor):
        super().__init__(timeout=600)
        self.editor = editor
        self.select = discord.ui.Select(
            placeholder=t("choose_frequency"), row=0, options=[
                discord.SelectOption(label=t(key), value=key)
                for key in (*PRESETS, "custom")])
        self.select.callback = self.pick
        self.add_item(self.select)
        self.back.label = t("back")

    @guild_context
    async def interaction_check(self, interaction):
        if not _owner(interaction, self.editor.guild_id, self.editor.owner_id):
            await feeds.respond_error(interaction, "denied")
            return False
        return True

    @guild_context
    async def pick(self, interaction):
        mode = self.select.values[0]
        if mode == "custom":
            return await interaction.response.send_modal(CustomRepeatModal(self.editor))
        value = PRESETS[mode]
        self.editor.parts = dict(value) if value else None
        self.editor.dirty = True
        await interaction.response.edit_message(
            content=self.editor.summary(), embed=None, view=self.editor)

    @discord.ui.button(label="Volver", style=discord.ButtonStyle.secondary, row=1)
    @guild_context
    async def back(self, interaction, button):
        await interaction.response.edit_message(
            content=self.editor.summary(), embed=None, view=self.editor)


class MentionPickerView(discord.ui.View):
    """Insert a guild-scoped mention token in the draft without saving it."""
    def __init__(self, editor):
        super().__init__(timeout=600)
        self.editor = editor
        self.destination = "text"
        self.target = discord.ui.Select(
            placeholder=t("mention_target"), row=0, options=[
                discord.SelectOption(label=t("in_text"), value="text", default=True),
                discord.SelectOption(label=t("in_embed"), value="embed")])
        self.target.callback = self.pick_target
        self.add_item(self.target)
        self.roles = discord.ui.RoleSelect(
            placeholder=t("choose_role"), min_values=1, max_values=1, row=1)
        self.roles.callback = self.insert_role
        self.add_item(self.roles)
        self.channels = discord.ui.ChannelSelect(
            placeholder=t("choose_channel"), min_values=1, max_values=1, row=2,
            channel_types=[discord.ChannelType.text])
        self.channels.callback = self.insert_channel
        self.add_item(self.channels)
        self.back.label = t("back")

    @guild_context
    async def interaction_check(self, interaction):
        if not _owner(interaction, self.editor.guild_id, self.editor.owner_id):
            await feeds.respond_error(interaction, "denied")
            return False
        return True

    @guild_context
    async def pick_target(self, interaction):
        self.destination = self.target.values[0]
        await interaction.response.edit_message(content=t("mention_help"), embed=None, view=self)

    def insert(self, token):
        editor = self.editor
        if self.destination == "embed":
            embed = dict(editor.embed or {"color_hex": "5865F2"})
            old = embed.get("description", "")
            if len(old) + len(token) + 1 > 4000:
                raise ValueError("invalid")
            embed["description"] = (old + " " + token).strip()
            editor.embed = embed
        else:
            if len(editor.text) + len(token) + 1 > 1900:
                raise ValueError("invalid")
            editor.text = (editor.text + " " + token).strip()
        editor.dirty = True

    @guild_context
    async def insert_role(self, interaction):
        role = self.roles.values[0]
        if role.guild.id != self.editor.guild_id:
            return await feeds.respond_error(interaction, "role")
        try:
            self.insert(role.mention)
        except ValueError:
            return await feeds.respond_error(interaction, "invalid")
        await interaction.response.edit_message(
            content=self.editor.summary(), embed=None, view=self.editor)

    @guild_context
    async def insert_channel(self, interaction):
        channel = self.channels.values[0]
        if channel.guild.id != self.editor.guild_id:
            return await feeds.respond_error(interaction, "invalid")
        try:
            self.insert(channel.mention)
        except ValueError:
            return await feeds.respond_error(interaction, "invalid")
        await interaction.response.edit_message(
            content=self.editor.summary(), embed=None, view=self.editor)

    @discord.ui.button(label="Volver", style=discord.ButtonStyle.secondary, row=3)
    @guild_context
    async def back(self, interaction, button):
        await interaction.response.edit_message(
            content=self.editor.summary(), embed=None, view=self.editor)


def embed_reference_names(guild, description):
    """Human-readable reference inventory; never ping during editor preview."""
    if not guild:
        return "—"
    pieces = []
    for role_id in re.findall(r"<@&(\d+)>", description or ""):
        role = guild.get_role(int(role_id))
        if role:
            pieces.append("@" + role.name)
    for channel_id in re.findall(r"<#(\d+)>", description or ""):
        channel = guild.get_channel(int(channel_id))
        if channel:
            pieces.append("#" + channel.name)
    return ", ".join(dict.fromkeys(pieces)) or "—"


class EmbedEditorView(discord.ui.View):
    """Embed-specific controls in the same message, with an actual embed preview.

    The Discord modal text field itself cannot offer live @/# autocomplete,
    therefore selection is integrated into this embed editor surface.
    """
    def __init__(self, parent):
        super().__init__(timeout=900)
        self.parent = parent
        self.guild_id, self.owner_id = parent.guild_id, parent.owner_id
        self.roles = discord.ui.RoleSelect(
            placeholder=t("embed_choose_role"), min_values=1, max_values=1, row=0)
        self.roles.callback = self.add_role
        self.add_item(self.roles)
        self.channels = discord.ui.ChannelSelect(
            placeholder=t("embed_choose_channel"), min_values=1, max_values=1,
            row=1, channel_types=[discord.ChannelType.text])
        self.channels.callback = self.add_channel
        self.add_item(self.channels)
        for control, key in (
            (self.edit, "embed_text_design"),
            (self.preview, "embed_preview"),
            (self.clear, "embed_remove"),
            (self.back, "back")
        ):
            control.label = t(key)

    def summary(self, guild):
        data = self.parent.embed or {}
        title = data.get("title") or "—"
        description = data.get("description") or t("embed_none")
        references = embed_reference_names(guild, description)
        # Avoid unbounded strings and unintended mentions in the panel itself;
        # the embed preview shows the exact stored description separately.
        description_plain = re.sub(r"<@&\d+>|<#\d+>", "●", description)
        return (
            t("embed_hub_title") + "\n\n" + t("embed_hub_hint")
            + "\n\n" + "**" + t("embed_section_title") + ":** " + title[:180]
            + "\n**" + t("embed_section_desc") + ":** "
            + description_plain[:350]
            + "\n**" + t("embed_references") + ":** " + references
            + "\n\n" + t("embed_manual_note")
            + "\n" + t("embed_notify_note")
        )

    def preview_embed(self, guild):
        data = self.parent.embed
        if not data or not (data.get("title") or data.get("description")):
            return None
        embed = discord.Embed(
            title=data.get("title") or None,
            description=data.get("description") or None,
            color=int(data.get("color_hex", "5865F2"), 16),
        )
        return self.parent.host["stamp_embed"](embed, guild)

    @guild_context
    async def interaction_check(self, interaction):
        if not _owner(interaction, self.guild_id, self.owner_id):
            await feeds.respond_error(interaction, "denied")
            return False
        return True

    async def add_token(self, interaction, token):
        current = dict(self.parent.embed or {"color_hex": "5865F2"})
        old = current.get("description") or ""
        if len(old) + len(token) + 1 > 4000:
            return await feeds.respond_error(interaction, "invalid")
        current["description"] = (old + " " + token).strip()
        try:
            feeds.referenced_mentions(interaction.guild, {
                "text": self.parent.text, "embed": current,
                "role": self.parent.role_id,
            })
        except ValueError:
            return await feeds.respond_error(interaction, "invalid")
        self.parent.embed = current
        self.parent.dirty = True
        next_view = EmbedEditorView(self.parent)
        await interaction.response.edit_message(
            content=next_view.summary(interaction.guild),
            embed=next_view.preview_embed(interaction.guild), view=next_view,
            allowed_mentions=discord.AllowedMentions.none(),
        )

    @guild_context
    async def add_role(self, interaction):
        role = self.roles.values[0]
        if role.guild.id != self.guild_id:
            return await feeds.respond_error(interaction, "role")
        await self.add_token(interaction, role.mention)

    @guild_context
    async def add_channel(self, interaction):
        channel = self.channels.values[0]
        if channel.guild.id != self.guild_id:
            return await feeds.respond_error(interaction, "invalid")
        await self.add_token(interaction, channel.mention)

    @discord.ui.button(label="Editar texto y diseño", style=discord.ButtonStyle.primary, row=2)
    @guild_context
    async def edit(self, interaction, button):
        await interaction.response.send_modal(
            EmbedModal(self.parent, from_embed_editor=True))

    @discord.ui.button(label="Vista previa", style=discord.ButtonStyle.secondary, row=2)
    @guild_context
    async def preview(self, interaction, button):
        await interaction.response.edit_message(
            content=self.summary(interaction.guild),
            embed=self.preview_embed(interaction.guild), view=self,
            allowed_mentions=discord.AllowedMentions.none())

    @discord.ui.button(label="Quitar embed", style=discord.ButtonStyle.danger, row=3)
    @guild_context
    async def clear(self, interaction, button):
        self.parent.embed = None
        self.parent.dirty = True
        next_view = EmbedEditorView(self.parent)
        await interaction.response.edit_message(
            content=next_view.summary(interaction.guild), embed=None,
            view=next_view, allowed_mentions=discord.AllowedMentions.none())

    @discord.ui.button(label="Volver", style=discord.ButtonStyle.secondary, row=3)
    @guild_context
    async def back(self, interaction, button):
        await interaction.response.edit_message(
            content=self.parent.summary(), embed=None, view=self.parent,
            allowed_mentions=discord.AllowedMentions.none())


class AutofeedEditorView(discord.ui.View):
    def __init__(self, host, guild_id, owner_id, *, job=None):
        super().__init__(timeout=900)
        self.host, self.guild_id, self.owner_id = host, guild_id, owner_id
        self.original = job
        self.snapshot = host["guild_config_get"](guild_id, feeds.CONFIG_KEY)
        self.channel_id = job.get("channel") if job else None
        self.role_id = job.get("role") if job else None
        self.text = (job.get("text") or "") if job else ""
        self.embed = job.get("embed") if job else None
        self.start = datetime.fromisoformat(job["start"]) if job else None
        self.timezone = __import__("zoneinfo").ZoneInfo("America/Santo_Domingo")
        self.parts = (job.get("repeat_parts") if job and job.get("repeat") == "custom" else
                      dict(PRESETS["daily"]) if job and job.get("repeat") == "diaria" else
                      dict(PRESETS["weekly"]) if job and job.get("repeat") == "semanal" else
                      dict(PRESETS["monthly"]) if job and job.get("repeat") == "mensual" else None)
        self.dirty = False

        self.channels = discord.ui.ChannelSelect(
            placeholder=t("select_channel"), row=0, min_values=1, max_values=1,
            channel_types=[discord.ChannelType.text])
        self.channels.callback = self.pick_channel
        self.add_item(self.channels)

        self.roles = discord.ui.RoleSelect(placeholder=t("select_role"), row=1,
                                           min_values=0, max_values=1)
        self.roles.callback = self.pick_role
        self.add_item(self.roles)
        for item, key in [(self.message, "message"), (self.embed_builder, "embed"),
                          (self.date_time, "date_picker"), (self.frequency, "repeat_picker"),
                          (self.preview, "preview"), (self.mention, "insert_mention"),
                          (self.silent, "silent"), (self.save, "save"),
                          (self.discard, "discard"), (self.back, "back")]:
            item.label = t(key)

    def summary(self):
        channel = f"<#{self.channel_id}>" if self.channel_id else t("empty")
        role = f"<@&{self.role_id}>" if self.role_id else t("none")
        date = f"<t:{int(self.start.timestamp())}:F>" if self.start else t("empty")
        period = (", ".join(f"{v} {t(k)}" for k, v in self.parts.items() if v)
                  if self.parts else t("no_repeat"))
        text = (self.text[:450] + ("…" if len(self.text) > 450 else "")) or t("empty")
        if self.embed:
            description = self.embed.get("description") or ""
            title = self.embed.get("title") or ""
            references = re.findall(r"<@&\d+>|<#\d+>", description)
            # Show the description too, even when the embed has a title.
            embed = (title[:65] + (" · " if title and description else "")
                     + description[:155] + (f" ({len(references)} refs)" if references else ""))
        else:
            embed = t("empty")
        return (f"{t('edit_title') if self.original else t('new_title')}\n\n"
                f"**{t('select_channel')}:** {channel}\n"
                f"**{t('message')}:** {discord.utils.escape_mentions(text)}\n"
                f"**{t('embed')}:** {discord.utils.escape_mentions(embed)}\n"
                f"**{t('start')}:** {date}\n"
                f"**{t('members')}:** {role}\n"
                f"**{t('repeat')}:** {period}\n\n"
                f"{t('saved_tip')}")

    @guild_context
    async def interaction_check(self, interaction):
        if not _owner(interaction, self.guild_id, self.owner_id):
            await feeds.respond_error(interaction, "denied")
            return False
        return True

    @guild_context
    async def pick_channel(self, interaction):
        self.channel_id = self.channels.values[0].id
        self.dirty = True
        await interaction.response.edit_message(content=self.summary(), embed=None, view=self)

    @guild_context
    async def pick_role(self, interaction):
        self.role_id = self.roles.values[0].id if self.roles.values else None
        self.dirty = True
        await interaction.response.edit_message(content=self.summary(), embed=None, view=self)

    @discord.ui.button(label="Mensaje", style=discord.ButtonStyle.primary, row=2)
    @guild_context
    async def message(self, interaction, button):
        await interaction.response.send_modal(MessageModal(self))

    @discord.ui.button(label="Editor de embed", style=discord.ButtonStyle.primary, row=2)
    @guild_context
    async def embed_builder(self, interaction, button):
        view = EmbedEditorView(self)
        await interaction.response.edit_message(
            content=view.summary(interaction.guild),
            embed=view.preview_embed(interaction.guild), view=view,
            allowed_mentions=discord.AllowedMentions.none())

    @discord.ui.button(label="Fecha y hora", style=discord.ButtonStyle.primary, row=2)
    @guild_context
    async def date_time(self, interaction, button):
        await interaction.response.send_modal(DateTimeModal(self))

    @discord.ui.button(label="Frecuencia", style=discord.ButtonStyle.primary, row=2)
    @guild_context
    async def frequency(self, interaction, button):
        picker = FrequencyPickerView(self)
        await interaction.response.edit_message(
            content=t("choose_frequency"), embed=None, view=picker)

    @discord.ui.button(label="Vista previa", style=discord.ButtonStyle.secondary, row=2)
    @guild_context
    async def preview(self, interaction, button):
        embed = None
        if self.embed:
            embed = discord.Embed(title=self.embed.get("title") or None,
                                  description=self.embed.get("description") or None,
                                  color=int(self.embed.get("color_hex", "5865F2"), 16))
            embed = self.host["stamp_embed"](embed, interaction.guild)
        await interaction.response.edit_message(
            content=self.summary() + "\n\n" + t("new_preview"),
            embed=embed, view=self,
            allowed_mentions=discord.AllowedMentions.none())

    @discord.ui.button(label="Insertar mención", style=discord.ButtonStyle.secondary, row=3)
    @guild_context
    async def mention(self, interaction, button):
        picker = MentionPickerView(self)
        await interaction.response.edit_message(
            content=t("mention_help"), embed=None, view=picker)

    @discord.ui.button(label="Sin rol", style=discord.ButtonStyle.secondary, row=3)
    @guild_context
    async def silent(self, interaction, button):
        self.role_id = None
        self.dirty = True
        self.remove_item(self.roles)
        self.roles = discord.ui.RoleSelect(
            placeholder=t("select_role"), row=1, min_values=0, max_values=1)
        self.roles.callback = self.pick_role
        self.add_item(self.roles)
        await interaction.response.edit_message(
            content=self.summary() + "\n\n" + t("role_again"), embed=None, view=self)

    def prepared(self, interaction):
        guild = interaction.guild
        channel = guild.get_channel(self.channel_id) if self.channel_id else None
        role = guild.get_role(self.role_id) if self.role_id else None
        if not (isinstance(channel, discord.TextChannel)
                and feeds.is_ready(interaction, self.host, channel, role)
                and (self.role_id is None or role is not None)):
            raise ValueError("unavailable")
        if not self.start or (not self.text and not self.embed):
            raise ValueError("warning")
        if self.start <= datetime.now(timezone.utc) + timedelta(minutes=1):
            raise ValueError("warning")
        try:
            feeds.referenced_mentions(guild, {
                "text": self.text, "embed": self.embed, "role": self.role_id})
        except ValueError as exc:
            raise ValueError("unavailable") from exc
        previous = self.original or {}
        return {
            "id": previous.get("id", uuid.uuid4().hex[:12]),
            "guild": self.guild_id, "author": previous.get("author", self.owner_id),
            "requester": self.owner_id, "channel": self.channel_id,
            "role": self.role_id, "text": self.text, "embed": self.embed,
            "start": self.start.isoformat(), "zone": "America/Santo_Domingo",
            "repeat": "custom" if self.parts else "ninguna",
            "repeat_parts": self.parts, "autofeed": True,
            "paused": previous.get("paused", False), "template": None,
        }

    @discord.ui.button(label="Guardar cambios", style=discord.ButtonStyle.success, row=4)
    @guild_context
    async def save(self, interaction, button):
        try:
            prepared = self.prepared(interaction)
        except ValueError as exc:
            return await interaction.response.send_message(
                t(str(exc)) if str(exc) in ("unavailable", "warning") else feeds.tr("invalid"),
                ephemeral=True)
        confirm = SetupConfirmView(self.host, prepared, self.snapshot, editing=self.original is not None)
        await interaction.response.edit_message(
            content=t("preview") + "\n" + feeds.show_job(prepared) + "\n\n" + t("saved_tip"),
            embed=None, view=confirm)

    @discord.ui.button(label="Descartar cambios", style=discord.ButtonStyle.danger, row=4)
    @guild_context
    async def discard(self, interaction, button):
        parent, view = setup_panel(self.host, self.guild_id, self.owner_id)
        await interaction.response.edit_message(content=parent, embed=None, view=view)

    @discord.ui.button(label="Volver", style=discord.ButtonStyle.secondary, row=4)
    @guild_context
    async def back(self, interaction, button):
        parent, view = setup_panel(self.host, self.guild_id, self.owner_id)
        await interaction.response.edit_message(content=parent, embed=None, view=view)


class SetupConfirmView(discord.ui.View):
    def __init__(self, host, job, snapshot, *, editing=False):
        super().__init__(timeout=300)
        self.host, self.job, self.snapshot, self.editing = host, job, snapshot, editing
        self.guild_id, self.owner_id = job["guild"], job["requester"]
        self.confirm.label, self.cancel.label = t("confirm"), t("discard")
        self.finished = False

    @guild_context
    async def interaction_check(self, interaction):
        if self.finished or not _owner(interaction, self.guild_id, self.owner_id):
            await feeds.respond_error(interaction, "denied")
            return False
        return True

    @discord.ui.button(label="Confirmar cambios", style=discord.ButtonStyle.success)
    @guild_context
    async def confirm(self, interaction, button):
        job = self.job
        guild = interaction.guild
        channel = guild.get_channel(job["channel"])
        role = guild.get_role(job["role"]) if job.get("role") else None
        if (not isinstance(channel, discord.TextChannel)
                or not feeds.is_ready(interaction, self.host, channel, role)
                or (job.get("role") and not role)):
            return await feeds.respond_error(interaction, "denied")
        try:
            feeds.persist_schedule(self.host, guild.id, interaction.user, job,
                                   snapshot=self.snapshot, editing=self.editing)
        except ValueError as exc:
            key = {"conflict": "conflict", "quota": "limit", "missing": "conflict"}.get(str(exc))
            return await interaction.response.send_message(
                t(key) if key else feeds.tr("invalid"), ephemeral=True)
        self.finished = True
        self.stop()
        parent, view = setup_panel(self.host, self.guild_id, self.owner_id)
        await interaction.response.edit_message(
            content=t("saved") + "\n\n" + parent, embed=None, view=view)

    @discord.ui.button(label="Descartar cambios", style=discord.ButtonStyle.danger)
    @guild_context
    async def cancel(self, interaction, button):
        self.finished = True
        self.stop()
        parent, view = setup_panel(self.host, self.guild_id, self.owner_id)
        await interaction.response.edit_message(content=parent, embed=None, view=view)
