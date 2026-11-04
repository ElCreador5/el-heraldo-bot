"""Configuración global de fecha y reloj del servidor, sin mezclar duraciones.

No depende de los módulos de Laboratorio ni guarda valores hasta la confirmación.
"""
from datetime import datetime

import discord

from heraldo_datetime import clock_style, format_clock, format_date_time


DATE_CHOICES = {
    "discord": "Fecha local de Discord",
    "dmy24": "Día/mes/año",
    "mdy12": "Mes/día/año",
    "iso": "Año-mes-día",
}
TIME_CHOICES = {"12h": "12 horas (6:30 p. m.)", "24h": "24 horas (18:30)"}


class ServerDateTimeSetupView(discord.ui.View):
    def __init__(self, host, guild_id: int, owner_id: int):
        super().__init__(timeout=900)
        self.host, self.guild_id, self.owner_id = host, guild_id, owner_id
        get = host["guild_config_get"]
        self.raw_date = get(guild_id, "display_date_format")
        self.raw_time = get(guild_id, "display_time_format")
        self.original_date = self.raw_date if self.raw_date in DATE_CHOICES else "discord"
        self.original_time = clock_style(self.original_date, self.raw_time)
        self.pending_date = self.original_date
        self.pending_time = self.original_time
        self.explicit_clock = False
        self.date_select = discord.ui.Select(
            placeholder="Formato de fecha", row=0,
            options=[discord.SelectOption(label=label, value=value, default=value == self.pending_date)
                     for value, label in DATE_CHOICES.items()],
        )
        self.date_select.callback = self.select_date
        self.add_item(self.date_select)
        self.time_select = discord.ui.Select(
            placeholder="Formato de hora", row=1,
            options=[discord.SelectOption(label=label, value=value, default=value == self.pending_time)
                     for value, label in TIME_CHOICES.items()],
        )
        self.time_select.callback = self.select_time
        self.add_item(self.time_select)
        self._refresh()

    def _changes(self) -> dict[str, str]:
        changes = {}
        if self.pending_date != self.original_date:
            changes["display_date_format"] = self.pending_date
        if self.pending_time != self.original_time or self.explicit_clock:
            # La preferencia horaria siempre es independiente del orden de fecha.
            if self.raw_time != self.pending_time:
                changes["display_time_format"] = self.pending_time
        elif self.pending_date != self.original_date and self.raw_time is None:
            # Evita que cambiar el orden de fecha también cambie el tipo de reloj.
            changes["display_time_format"] = self.original_time
        return changes

    def _refresh(self):
        for option in self.date_select.options:
            option.default = option.value == self.pending_date
        for option in self.time_select.options:
            option.default = option.value == self.pending_time
        self.save.disabled = self.discard.disabled = not bool(self._changes())

    def summary(self) -> str:
        style = format_date_time(
            datetime(2026, 11, 3, 18, 30, tzinfo=__import__("zoneinfo").ZoneInfo("America/Santo_Domingo")),
            date_mode=self.pending_date, time_mode=self.pending_time,
        )
        return ("**El Heraldo · Formato de fecha y hora**\n\n"
                + f"**Fecha:** {DATE_CHOICES[self.pending_date]}\n"
                + f"**Reloj:** {TIME_CHOICES[self.pending_time]}\n"
                + f"**Ejemplo:** {style}\n\n"
                + "Las horas exactas usan este formato. Las duraciones de castigos "
                  "y los intervalos de repetición siguen expresándose en minutos, horas y días.\n"
                + "Nada se guarda hasta confirmar los cambios.")

    async def interaction_check(self, interaction):
        return await self.host["configuration_access"](interaction, self.guild_id, self.owner_id)

    async def select_date(self, interaction):
        value = (interaction.data or {}).get("values", [None])[0]
        if value not in DATE_CHOICES:
            return await interaction.response.send_message("Formato inválido.", ephemeral=True)
        self.pending_date = value
        self._refresh()
        await interaction.response.edit_message(content=self.summary(), view=self)

    async def select_time(self, interaction):
        value = (interaction.data or {}).get("values", [None])[0]
        if value not in TIME_CHOICES:
            return await interaction.response.send_message("Formato inválido.", ephemeral=True)
        self.pending_time = value
        self.explicit_clock = True
        self._refresh()
        await interaction.response.edit_message(content=self.summary(), view=self)

    @discord.ui.button(label="Guardar cambios", style=discord.ButtonStyle.success, row=2)
    async def save(self, interaction, button):
        if not self._changes():
            return await interaction.response.send_message("No hay cambios pendientes.", ephemeral=True)
        confirm = ServerDateTimeConfirmView(self)
        await interaction.response.edit_message(
            content=self.summary() + "\n\n¿Confirmar los cambios?", view=confirm,
        )

    @discord.ui.button(label="Descartar cambios", style=discord.ButtonStyle.danger, row=2)
    async def discard(self, interaction, button):
        self.pending_date, self.pending_time = self.original_date, self.original_time
        self.explicit_clock = False
        self._refresh()
        await interaction.response.edit_message(content=self.summary(), view=self)

    @discord.ui.button(label="Volver", style=discord.ButtonStyle.secondary, row=2)
    async def back(self, interaction, button):
        if self._changes():
            return await interaction.response.send_message("Guarda o descarta los cambios antes de volver.", ephemeral=True)
        await self.host["heraldo_setup_go_home"](interaction, self.guild_id, self.owner_id)

    @discord.ui.button(label="Cerrar", style=discord.ButtonStyle.danger, row=3)
    async def close(self, interaction, button):
        self.stop()
        await interaction.response.edit_message(content="Panel cerrado.", view=None)


class ServerDateTimeConfirmView(discord.ui.View):
    def __init__(self, editor: ServerDateTimeSetupView):
        super().__init__(timeout=300)
        self.editor = editor
        self.guild_id, self.owner_id = editor.guild_id, editor.owner_id
        self.changes = editor._changes()
        self.finished = False

    async def interaction_check(self, interaction):
        return (not self.finished and await self.editor.interaction_check(interaction))

    @discord.ui.button(label="Confirmar cambios", style=discord.ButtonStyle.success)
    async def confirm(self, interaction, button):
        editor = self.editor
        if editor.is_finished() or editor._changes() != self.changes:
            return await interaction.response.send_message("Este borrador ha cambiado. Abre el panel de nuevo.", ephemeral=True)
        conn = editor.host["db_connect"]()
        try:
            conn.execute("BEGIN IMMEDIATE")
            for key, value in (("display_date_format", editor.raw_date),
                               ("display_time_format", editor.raw_time)):
                row = conn.execute(
                    "SELECT value FROM guild_settings WHERE guild_id=? AND key=?",
                    (self.guild_id, key),
                ).fetchone()
                if (row[0] if row else None) != value:
                    conn.rollback()
                    return await interaction.response.send_message(
                        "La configuración cambió en otra sesión.", ephemeral=True,
                    )
            for key, value in self.changes.items():
                conn.execute(
                    "INSERT INTO guild_settings(guild_id,key,value) VALUES(?,?,?) "
                    "ON CONFLICT(guild_id,key) DO UPDATE SET value=excluded.value",
                    (self.guild_id, key, value),
                )
            conn.commit()
        finally:
            conn.close()
        self.finished = True
        self.stop()
        editor.stop()
        fresh = ServerDateTimeSetupView(editor.host, self.guild_id, self.owner_id)
        await interaction.response.edit_message(content=fresh.summary(), view=fresh)

    @discord.ui.button(label="Volver", style=discord.ButtonStyle.secondary)
    async def back(self, interaction, button):
        self.finished = True
        self.stop()
        await interaction.response.edit_message(content=self.editor.summary(), view=self.editor)

    @discord.ui.button(label="Cerrar", style=discord.ButtonStyle.danger)
    async def close(self, interaction, button):
        self.finished = True
        self.stop()
        self.editor.stop()
        await interaction.response.edit_message(content="Panel cerrado.", view=None)
