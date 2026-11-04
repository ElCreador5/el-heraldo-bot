"""Panel de recordatorios de reportes (producción): borrador y guardado explícito."""
from __future__ import annotations

import re
from datetime import datetime, timezone

import discord

from production_report_reminders import (
    reminder_settings, reminder_preview, reminder_next_due, FREQUENCIES,
)

LABELS = {
    "es-419": {
        "title": "El Heraldo · Moderación · Recordatorios", "active": "Activo",
        "paused": "Pausado", "frequency": "Frecuencia", "channel": "Canal",
        "next": "Próxima publicación", "unconfigured": "No configurado",
        "preview": "Vista previa", "edit": "Editar horario",
        "activate": "Activar", "pause": "Pausar", "back": "Volver",
        "close": "Cerrar", "save": "Guardar cambios", "discard": "Descartar cambios",
        "saved": "Cambios guardados.", "concurrent": "La configuración cambió en otra sesión.",
        "denied": "El bot necesita permisos en el canal guardado.",
        "select": "Frecuencia de publicación", "weekday": "Día de la semana",
        "hour": "Hora exacta (RD)", "choose": "Selecciona el canal",
        "interval": "Frecuencia personalizada", "start": "Inicio (AAAA-MM-DD HH:MM)",
        "invalid": "Introduce un intervalo de al menos 1 día, por ejemplo 1d, 7d o 24h.",
        "invalid_start": "Utiliza AAAA-MM-DD HH:MM en horario de República Dominicana.",
        "month_day": "Día del mes (1–28)", "custom": "Personalizada",
        "not_set": "Selecciona y guarda un canal para activar los recordatorios.",
        "pending": "Borrador sin guardar", "empty": "No hay cambios pendientes.",
        "closed": "Panel de recordatorios cerrado.",
    },
    "en-US": {
        "title": "El Heraldo · Moderation · Reminders", "active": "Active",
        "paused": "Paused", "frequency": "Frequency", "channel": "Channel",
        "next": "Next publication", "unconfigured": "Not configured",
        "preview": "Preview", "edit": "Edit schedule",
        "activate": "Enable", "pause": "Pause", "back": "Back",
        "close": "Close", "save": "Save changes", "discard": "Discard changes",
        "saved": "Changes saved.", "concurrent": "Settings were changed in another session.",
        "denied": "The bot needs permissions in the saved channel.",
        "select": "Publication frequency", "weekday": "Day of week",
        "hour": "Exact time (DR)", "choose": "Choose channel",
        "interval": "Custom interval", "start": "Start (YYYY-MM-DD HH:MM)",
        "invalid": "Enter an interval of at least 1 day, e.g. 1d, 7d or 24h.",
        "invalid_start": "Use YYYY-MM-DD HH:MM in Dominican Republic local time.",
        "month_day": "Day of month (1–28)", "custom": "Custom",
        "not_set": "Choose and save a channel before enabling reminders.",
        "pending": "Unsaved draft", "empty": "No pending changes.",
        "closed": "Reminder panel closed.",
    },
    "pt-BR": {
        "title": "El Heraldo · Moderação · Lembretes", "active": "Ativo",
        "paused": "Pausado", "frequency": "Frequência", "channel": "Canal",
        "next": "Próxima publicação", "unconfigured": "Não configurado",
        "preview": "Prévia", "edit": "Editar programação",
        "activate": "Ativar", "pause": "Pausar", "back": "Voltar",
        "close": "Fechar", "save": "Salvar alterações", "discard": "Descartar alterações",
        "saved": "Alterações salvas.", "concurrent": "A configuração mudou em outra sessão.",
        "denied": "O bot precisa de permissões no canal salvo.",
        "select": "Frequência de publicação", "weekday": "Dia da semana",
        "hour": "Hora exata (RD)", "choose": "Selecionar canal",
        "interval": "Intervalo personalizado", "start": "Início (AAAA-MM-DD HH:MM)",
        "invalid": "Insira um intervalo de pelo menos 1 dia, como 1d, 7d ou 24h.",
        "invalid_start": "Use AAAA-MM-DD HH:MM no horário da República Dominicana.",
        "month_day": "Dia do mês (1–28)", "custom": "Personalizada",
        "not_set": "Selecione e salve um canal antes de ativar os lembretes.",
        "pending": "Rascunho não salvo", "empty": "Sem alterações pendentes.",
        "closed": "Painel de lembretes fechado.",
    },
}

FREQUENCY_NAMES = {
    "es-419": {"daily": "Diaria", "weekly": "Semanal", "fortnightly": "Quincenal",
               "monthly": "Mensual", "custom": "Personalizada"},
    "en-US": {"daily": "Daily", "weekly": "Weekly", "fortnightly": "Every two weeks",
              "monthly": "Monthly", "custom": "Custom"},
    "pt-BR": {"daily": "Diária", "weekly": "Semanal", "fortnightly": "Quinzenal",
              "monthly": "Mensal", "custom": "Personalizada"},
}

DAYS = {
    "es-419": ("Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"),
    "en-US": ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"),
    "pt-BR": ("Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"),
}


def _locale(host, guild_id):
    return host["language"](guild_id)


def _t(host, guild_id, key):
    return LABELS[_locale(host, guild_id)][key]


def _summary(host, guild_id, settings, *, draft=False, message=""):
    lang = _locale(host, guild_id)
    words = LABELS[lang]
    frequency = settings["report_reminder_frequency"]
    frequency_name = FREQUENCY_NAMES[lang][frequency]
    if frequency in {"weekly", "fortnightly"}:
        frequency_name += " · " + DAYS[lang][int(settings["report_reminder_day"]) % 7]
    elif frequency == "monthly":
        frequency_name += " · " + str(max(1, int(settings["report_reminder_day"])))
    elif frequency == "custom":
        frequency_name += " · " + settings["report_reminder_interval"]
        if settings["report_reminder_start"]:
            frequency_name += " · " + settings["report_reminder_start"]
    channel_id = int(settings["report_reminder_channel"])
    channel = f"<#{channel_id}>" if channel_id else words["unconfigured"]
    active = words["active"] if settings["report_reminder_enabled"] == "1" else words["paused"]
    next_due = reminder_next_due(settings, datetime.now(timezone.utc))
    when = host["format_datetime"](guild_id, next_due)
    content = (f"**{words['title']}**\n\n"
               f"**{active}** · {words['frequency']}: {frequency_name}\n"
               f"**{words['channel']}:** {channel}\n"
               f"**{words['next']}:** {when}")
    if draft:
        content += "\n\n**" + words["pending"] + "**"
    if message:
        content += "\n\n" + message
    return content


class ReminderHomeView(discord.ui.View):
    def __init__(self, guild_id, owner_id, host):
        super().__init__(timeout=900)
        self.guild_id, self.owner_id, self.host = guild_id, owner_id, host
        self._apply_labels()

    def _apply_labels(self):
        for item, name in (
            (self.back, "back"), (self.edit, "edit"), (self.preview, "preview"),
            (self.close, "close"),
        ):
            item.label = _t(self.host, self.guild_id, name)
        enabled = reminder_settings(self.guild_id, self.host["get"])["report_reminder_enabled"] == "1"
        self.toggle.label = _t(self.host, self.guild_id, "pause" if enabled else "activate")
        self.toggle.style = discord.ButtonStyle.danger if enabled else discord.ButtonStyle.success

    def summary(self, notice=""):
        return _summary(self.host, self.guild_id, reminder_settings(self.guild_id, self.host["get"]),
                        message=notice)

    async def interaction_check(self, interaction):
        return await self.host["check_access"](interaction, self.guild_id, self.owner_id)

    @discord.ui.button(label="Volver", style=discord.ButtonStyle.secondary, row=0)
    async def back(self, interaction, button):
        self.stop()
        await self.host["return_reports"](interaction, self.guild_id, self.owner_id)

    @discord.ui.button(label="Editar horario", style=discord.ButtonStyle.primary, row=0)
    async def edit(self, interaction, button):
        self.stop()
        panel = ReminderEditorView(self.guild_id, self.owner_id, self.host)
        await interaction.response.edit_message(content=panel.summary(), view=panel)

    @discord.ui.button(label="Vista previa", style=discord.ButtonStyle.secondary, row=0)
    async def preview(self, interaction, button):
        await interaction.response.send_message(
            content=reminder_preview(self.guild_id, self.host), ephemeral=True,
            allowed_mentions=discord.AllowedMentions.none(),
        )

    @discord.ui.button(label="Activar", style=discord.ButtonStyle.success, row=0)
    async def toggle(self, interaction, button):
        settings = reminder_settings(self.guild_id, self.host["get"])
        active = settings["report_reminder_enabled"] == "1"
        if not active:
            channel_id = int(settings["report_reminder_channel"])
            channel = interaction.guild.get_channel(channel_id)
            me = interaction.guild.me
            if not isinstance(channel, discord.TextChannel) or me is None:
                await interaction.response.edit_message(content=self.summary(
                    _t(self.host, self.guild_id, "not_set")), view=self)
                return
            perms = channel.permissions_for(me)
            if not (perms.view_channel and perms.send_messages and perms.embed_links):
                await interaction.response.edit_message(content=self.summary(
                    _t(self.host, self.guild_id, "denied")), view=self)
                return
        self.host["set"](self.guild_id, "report_reminder_enabled", "0" if active else "1")
        self._apply_labels()
        await interaction.response.edit_message(content=self.summary(), view=self)

    @discord.ui.button(label="Cerrar", style=discord.ButtonStyle.danger, row=0)
    async def close(self, interaction, button):
        self.stop()
        await interaction.response.edit_message(
            content=_t(self.host, self.guild_id, "closed"), view=None)


class ReminderIntervalModal(discord.ui.Modal):
    def __init__(self, parent):
        self.parent = parent
        lang = _locale(parent.host, parent.guild_id)
        word = LABELS[lang]
        super().__init__(title=word["interval"])
        self.every = discord.ui.TextInput(
            label=word["interval"], placeholder="7d", max_length=10,
            default=parent.pending["report_reminder_interval"],
        )
        self.start = discord.ui.TextInput(
            label=word["start"], placeholder="2026-11-04 12:00",
            required=True, max_length=16,
            default=parent.pending["report_reminder_start"] or None,
        )
        self.add_item(self.every)
        self.add_item(self.start)

    async def on_submit(self, interaction):
        if not await self.parent.interaction_check(interaction):
            return
        interval = str(self.every).strip().lower().replace(" ", "")
        match = re.fullmatch(r"(\d+)(h|d)", interval)
        seconds = (int(match[1]) * (3600 if match[2] == "h" else 86400)
                   if match else 0)
        if seconds < 86400 or seconds > 365 * 86400:
            await interaction.response.send_message(
                _t(self.parent.host, self.parent.guild_id, "invalid"), ephemeral=True)
            return
        start = str(self.start).strip()
        try:
            datetime.strptime(start, "%Y-%m-%d %H:%M")
        except ValueError:
            await interaction.response.send_message(
                _t(self.parent.host, self.parent.guild_id, "invalid_start"), ephemeral=True)
            return
        self.parent.pending.update(
            report_reminder_frequency="custom", report_reminder_interval=interval,
            report_reminder_start=start,
        )
        self.parent._refresh()
        await interaction.response.edit_message(content=self.parent.summary(), view=self.parent)


class ReminderMonthdayModal(discord.ui.Modal):
    def __init__(self, parent):
        self.parent = parent
        super().__init__(title=_t(parent.host, parent.guild_id, "month_day"))
        self.day = discord.ui.TextInput(
            label=_t(parent.host, parent.guild_id, "month_day"),
            default=str(max(1, int(parent.pending["report_reminder_day"]))),
            placeholder="1", max_length=2,
        )
        self.add_item(self.day)

    async def on_submit(self, interaction):
        if not await self.parent.interaction_check(interaction):
            return
        try:
            day = int(str(self.day).strip())
            if not 1 <= day <= 28:
                raise ValueError("day")
        except ValueError:
            await interaction.response.send_message(
                _t(self.parent.host, self.parent.guild_id, "month_day"), ephemeral=True)
            return
        self.parent.pending["report_reminder_frequency"] = "monthly"
        self.parent.pending["report_reminder_day"] = str(day)
        self.parent._refresh()
        await interaction.response.edit_message(content=self.parent.summary(), view=self.parent)


class ReminderEditorView(discord.ui.View):
    def __init__(self, guild_id, owner_id, host):
        super().__init__(timeout=900)
        self.guild_id, self.owner_id, self.host = guild_id, owner_id, host
        self.original = reminder_settings(guild_id, host["get"])
        self.pending = dict(self.original)
        self.raw = {key: host["get"](guild_id, key) for key in self.original}
        lang = _locale(host, guild_id)

        self.frequency_select = discord.ui.Select(
            placeholder=LABELS[lang]["select"],
            options=[discord.SelectOption(label=FREQUENCY_NAMES[lang][key], value=key)
                     for key in ("daily", "weekly", "fortnightly", "monthly", "custom")],
            row=0,
        )
        self.frequency_select.callback = self.set_frequency
        self.add_item(self.frequency_select)

        self.day_select = discord.ui.Select(
            placeholder=LABELS[lang]["weekday"],
            options=[discord.SelectOption(label=day, value=str(i))
                     for i, day in enumerate(DAYS[lang])],
            row=1,
        )
        self.day_select.callback = self.set_day
        self.add_item(self.day_select)

        self.hour_select = discord.ui.Select(
            placeholder=LABELS[lang]["hour"],
            options=[discord.SelectOption(label=f"{i:02d}:00", value=str(i))
                     for i in range(24)], row=2,
        )
        self.hour_select.callback = self.set_hour
        self.add_item(self.hour_select)

        self.channel_select = discord.ui.ChannelSelect(
            placeholder=LABELS[lang]["choose"],
            channel_types=[discord.ChannelType.text], row=3,
        )
        self.channel_select.callback = self.set_channel
        self.add_item(self.channel_select)

        for item, name in ((self.back, "back"), (self.save, "save"),
                           (self.discard, "discard"), (self.close, "close")):
            item.label = LABELS[lang][name]
        self._refresh()

    def _refresh(self):
        freq = self.pending["report_reminder_frequency"]
        for option in self.frequency_select.options:
            option.default = option.value == freq
        for option in self.day_select.options:
            option.default = option.value == self.pending["report_reminder_day"]
        for option in self.hour_select.options:
            option.default = option.value == self.pending["report_reminder_hour"]
        channel_id = int(self.pending["report_reminder_channel"])
        self.channel_select.default_values = (
            [discord.SelectDefaultValue(id=channel_id, type=discord.SelectDefaultValueType.channel)]
            if channel_id else [])
        if freq in ("weekly", "fortnightly"):
            if self.day_select not in self.children:
                self.add_item(self.day_select)
        elif self.day_select in self.children:
            self.remove_item(self.day_select)
        if freq != "custom":
            if self.hour_select not in self.children:
                self.add_item(self.hour_select)
        elif self.hour_select in self.children:
            self.remove_item(self.hour_select)
        self.save.disabled = self.pending == self.original
        if self.pending == self.original and self.discard in self.children:
            self.remove_item(self.discard)
        if self.pending != self.original and self.discard not in self.children:
            self.add_item(self.discard)
        # Orden fijo en la última fila: Volver, Guardar, Descartar (si aplica), Cerrar.
        for item in (self.back, self.save, self.discard, self.close):
            self.remove_item(item)
        for item in (self.back, self.save):
            self.add_item(item)
        if self.pending != self.original:
            self.add_item(self.discard)
        self.add_item(self.close)

    def summary(self, notice=""):
        return _summary(self.host, self.guild_id, self.pending,
                        draft=self.pending != self.original, message=notice)

    async def interaction_check(self, interaction):
        return await self.host["check_access"](
            interaction, self.guild_id, self.owner_id)

    async def set_frequency(self, interaction):
        value = (interaction.data or {}).get("values", [None])[0]
        if value not in FREQUENCIES:
            return await interaction.response.send_message(
                _t(self.host, self.guild_id, "select"), ephemeral=True)
        if value == "custom":
            return await interaction.response.send_modal(ReminderIntervalModal(self))
        if value == "monthly":
            return await interaction.response.send_modal(ReminderMonthdayModal(self))
        self.pending["report_reminder_frequency"] = value
        self.pending["report_reminder_start"] = ""
        self._refresh()
        await interaction.response.edit_message(content=self.summary(), view=self)

    async def set_day(self, interaction):
        value = (interaction.data or {}).get("values", [None])[0]
        if value not in {str(i) for i in range(7)}:
            return
        self.pending["report_reminder_day"] = value
        self._refresh()
        await interaction.response.edit_message(content=self.summary(), view=self)

    async def set_hour(self, interaction):
        value = (interaction.data or {}).get("values", [None])[0]
        if value not in {str(i) for i in range(24)}:
            return
        self.pending["report_reminder_hour"] = value
        self._refresh()
        await interaction.response.edit_message(content=self.summary(), view=self)

    async def set_channel(self, interaction):
        values = (interaction.data or {}).get("values", ())
        channel = interaction.guild.get_channel(int(values[0])) if values else None
        if not isinstance(channel, discord.TextChannel):
            return await interaction.response.send_message(
                _t(self.host, self.guild_id, "not_set"), ephemeral=True)
        me = interaction.guild.me
        perms = channel.permissions_for(me) if me is not None else None
        if not perms or not (perms.view_channel and perms.send_messages and perms.embed_links):
            return await interaction.response.send_message(
                _t(self.host, self.guild_id, "denied"), ephemeral=True)
        self.pending["report_reminder_channel"] = str(channel.id)
        self._refresh()
        await interaction.response.edit_message(content=self.summary(), view=self)

    @discord.ui.button(label="Volver", style=discord.ButtonStyle.secondary, row=4)
    async def back(self, interaction, button):
        self.stop()
        panel = ReminderHomeView(self.guild_id, self.owner_id, self.host)
        await interaction.response.edit_message(content=panel.summary(), view=panel)

    @discord.ui.button(label="Guardar cambios", style=discord.ButtonStyle.success, row=4)
    async def save(self, interaction, button):
        changes = {key: value for key, value in self.pending.items()
                   if key != "report_reminder_enabled" and value != self.original[key]}
        if not changes:
            return await interaction.response.edit_message(
                content=self.summary(_t(self.host, self.guild_id, "empty")), view=self)
        if self.original["report_reminder_enabled"] == "1":
            channel = interaction.guild.get_channel(int(self.pending["report_reminder_channel"]))
            me = interaction.guild.me
            perms = channel.permissions_for(me) if isinstance(channel, discord.TextChannel) and me else None
            if not perms or not (perms.view_channel and perms.send_messages and perms.embed_links):
                return await interaction.response.edit_message(
                    content=self.summary(_t(self.host, self.guild_id, "denied")), view=self)
        conn = self.host["connect"]()
        try:
            conn.execute("BEGIN IMMEDIATE")
            current = dict(conn.execute(
                "SELECT key,value FROM guild_settings WHERE guild_id=? AND key IN ("
                + ",".join("?" for _ in self.original) + ")",
                (self.guild_id, *self.original.keys()),
            ).fetchall())
            if any(current.get(key) != self.raw[key] for key in self.original):
                conn.rollback()
                return await interaction.response.edit_message(
                    content=self.summary(_t(self.host, self.guild_id, "concurrent")), view=self)
            for key, value in changes.items():
                conn.execute(
                    "INSERT INTO guild_settings(guild_id,key,value) VALUES (?,?,?) "
                    "ON CONFLICT(guild_id,key) DO UPDATE SET value=excluded.value",
                    (self.guild_id, key, value),
                )
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
        self.stop()
        panel = ReminderHomeView(self.guild_id, self.owner_id, self.host)
        await interaction.response.edit_message(
            content=panel.summary(_t(self.host, self.guild_id, "saved")), view=panel)

    @discord.ui.button(label="Descartar cambios", style=discord.ButtonStyle.secondary, row=4)
    async def discard(self, interaction, button):
        self.pending = dict(self.original)
        self._refresh()
        await interaction.response.edit_message(content=self.summary(), view=self)

    @discord.ui.button(label="Cerrar", style=discord.ButtonStyle.danger, row=4)
    async def close(self, interaction, button):
        self.stop()
        await interaction.response.edit_message(
            content=_t(self.host, self.guild_id, "closed"), view=None)
