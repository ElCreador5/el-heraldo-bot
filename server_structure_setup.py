"""Confirmed configuration for the existing server structure backup scheduler."""
from datetime import datetime, timedelta, timezone

import discord

from heraldo_i18n import guild_context, text as t


FIELDS = {
    "template_mode": "get_template_mode",
    "template_hour": "get_template_hour",
    "template_weekday": "get_template_weekday",
    "template_monthday": "get_template_monthday",
    "template_interval_minutes": "get_template_interval_minutes",
}
MARKERS = ("template_last_run", "template_last_slot")


def last_slot(values, now):
    """Same calendar as the historical scheduler; no DB writes or API calls."""
    mode = values["template_mode"]
    slot = now.replace(hour=int(values["template_hour"]), minute=0, second=0, microsecond=0)
    if mode == "daily":
        return slot - timedelta(days=1) if slot > now else slot
    if mode == "weekly":
        slot -= timedelta(days=(now.weekday() - int(values["template_weekday"])) % 7)
        return slot - timedelta(days=7) if slot > now else slot
    if mode == "monthly":
        slot = slot.replace(day=int(values["template_monthday"]))
        if slot > now:
            slot = (slot.replace(day=1) - timedelta(days=1)).replace(day=slot.day)
        return slot
    return None


class StructureScheduleModal(discord.ui.Modal):
    @guild_context
    def __init__(self, editor):
        self.editor = editor
        self.guild_id, self.owner_id = editor.guild_id, editor.owner_id
        super().__init__(title=t("setup.structure.schedule"))
        for name, key in (("hour", "template_hour"), ("weekday", "template_weekday"),
                          ("monthday", "template_monthday"), ("interval", "template_interval_minutes")):
            field = discord.ui.TextInput(label=t("setup.structure." + name), default=editor.values[key], max_length=6)
            setattr(self, name, field)
            self.add_item(field)

    @guild_context
    async def on_submit(self, interaction):
        if not await self.editor.interaction_check(interaction):
            return
        if self.editor.is_finished():
            return await interaction.response.send_message(t("setup.structure.expired"), ephemeral=True)
        try:
            values = [int(str(getattr(self, name))) for name in ("hour", "weekday", "monthday", "interval")]
            if not (0 <= values[0] <= 23 and 0 <= values[1] <= 6
                    and 1 <= values[2] <= 28 and 1 <= values[3] <= 43200):
                raise ValueError
        except ValueError:
            return await interaction.response.send_message(t("setup.structure.invalid"), ephemeral=True)
        for key, value in zip(list(FIELDS)[1:], values):
            self.editor.values[key] = str(value)
        self.editor.refresh()
        await interaction.response.edit_message(content=self.editor.summary(), embed=None, view=self.editor)


class ServerStructureSetupView(discord.ui.View):
    @guild_context
    def __init__(self, host, guild_id, owner_id):
        self.host, self.guild_id, self.owner_id = host, guild_id, owner_id
        super().__init__(timeout=900)
        self.original = {key: host["guild_config_get"](guild_id, key) for key in (*FIELDS, *MARKERS)}
        self.initial = {key: str(host[getter](guild_id)) for key, getter in FIELDS.items()}
        self.values = dict(self.initial)
        chooser = discord.ui.Select(
            placeholder=t("setup.structure.choose"), row=0,
            options=[discord.SelectOption(label=t("setup.structure.mode." + mode), value=mode,
                                          description=t("setup.structure.help." + mode))
                     for mode in ("off", "daily", "weekly", "monthly", "interval")])
        chooser.callback = self.choose
        self.chooser = chooser
        self.add_item(chooser)
        self.refresh()

    async def interaction_check(self, interaction):
        return await self.host["configuration_access"](interaction, self.guild_id, self.owner_id)

    def _has_pending_changes(self):
        return self.values != self.initial

    @guild_context
    def refresh(self):
        for option in self.chooser.options:
            option.default = option.value == self.values["template_mode"]
        self.save.disabled = self.discard.disabled = not self._has_pending_changes()

    @guild_context
    def summary(self):
        return (t("setup.structure.title") + "\n\n"
                + self.host["template_config_summary"](self.guild_id, datetime.now(timezone.utc))
                + "\n\n" + t("setup.structure.draft", mode=t("setup.structure.mode." + self.values["template_mode"]),
                    hour=self.values["template_hour"], weekday=self.values["template_weekday"],
                    monthday=self.values["template_monthday"], interval=self.values["template_interval_minutes"]))

    @guild_context
    async def choose(self, interaction):
        selected = (interaction.data or {}).get("values", [None])[0]
        if selected not in {option.value for option in self.chooser.options}:
            return await interaction.response.send_message(t("setup.structure.invalid"), ephemeral=True)
        self.values["template_mode"] = selected
        self.refresh()
        await interaction.response.edit_message(content=self.summary(), view=self)

    @discord.ui.button(label=t("setup.structure.schedule"), style=discord.ButtonStyle.primary, row=1)
    @guild_context
    async def schedule(self, interaction, button):
        await interaction.response.send_modal(StructureScheduleModal(self))

    @discord.ui.button(label=t("text.14bdfaf2face3a"), style=discord.ButtonStyle.success, row=2)
    @guild_context
    async def save(self, interaction, button):
        if not self._has_pending_changes():
            return await interaction.response.send_message(t("text.3ef181ed6e0a1e"), ephemeral=True)
        confirm = StructureSaveConfirmView(self)
        await interaction.response.edit_message(content=self.summary() + "\n\n" + t("setup.structure.confirm"), view=confirm)

    @discord.ui.button(label=t("text.80ca383e9c8d3e"), style=discord.ButtonStyle.danger, row=2)
    @guild_context
    async def discard(self, interaction, button):
        self.values = dict(self.initial)
        self.refresh()
        await interaction.response.edit_message(content=self.summary(), view=self)

    @discord.ui.button(label=t("text.ab26ae7bca3621"), style=discord.ButtonStyle.secondary, row=2)
    @guild_context
    async def back(self, interaction, button):
        if self._has_pending_changes():
            return await interaction.response.send_message(t("setup.structure.unsaved"), ephemeral=True)
        await self.host["heraldo_setup_go_home"](interaction, self.guild_id, self.owner_id)

    @discord.ui.button(label=t("text.aeccae342e4bd0"), style=discord.ButtonStyle.danger, row=2)
    @guild_context
    async def close(self, interaction, button):
        self.stop()
        await interaction.response.edit_message(content=t("setup.structure.closed"), embed=None, view=None)


class StructureSaveConfirmView(discord.ui.View):
    @guild_context
    def __init__(self, editor):
        self.editor = editor
        self.guild_id, self.owner_id = editor.guild_id, editor.owner_id
        self.pending = dict(editor.values)
        self.finished = False
        super().__init__(timeout=300)

    async def interaction_check(self, interaction):
        return not self.finished and await self.editor.interaction_check(interaction)

    @discord.ui.button(label=t("setup.structure.confirm_button"), style=discord.ButtonStyle.success)
    @guild_context
    async def confirm(self, interaction, button):
        if not await self.interaction_check(interaction):
            return
        host, editor = self.editor.host, self.editor
        if editor.is_finished() or editor.values != self.pending:
            return await interaction.response.send_message(t("setup.structure.expired"), ephemeral=True)
        now = datetime.now(timezone.utc)
        changes = {key: value for key, value in self.pending.items() if value != editor.initial[key]}
        if self.pending["template_mode"] == "interval":
            changes["template_last_run"] = now.isoformat()
        else:
            slot = last_slot(self.pending, now.astimezone(host["STREAK_TZ"]))
            if slot is not None:
                changes["template_last_slot"] = slot.isoformat()
        conn = host["db_connect"]()
        try:
            conn.execute("BEGIN IMMEDIATE")
            for key, original in editor.original.items():
                row = conn.execute("SELECT value FROM guild_settings WHERE guild_id=? AND key=?", (self.guild_id, key)).fetchone()
                if (row[0] if row else None) != original:
                    conn.rollback()
                    return await interaction.response.send_message(t("setup.structure.conflict"), ephemeral=True)
            for key, value in changes.items():
                conn.execute("INSERT INTO guild_settings(guild_id,key,value) VALUES(?,?,?) "
                             "ON CONFLICT(guild_id,key) DO UPDATE SET value=excluded.value", (self.guild_id, key, value))
            conn.commit()
        finally:
            conn.close()
        self.finished = True
        self.stop()
        editor.stop()
        view = ServerStructureSetupView(host, self.guild_id, self.owner_id)
        await interaction.response.edit_message(content=view.summary(), embed=None, view=view)

    @discord.ui.button(label=t("text.ab26ae7bca3621"), style=discord.ButtonStyle.secondary)
    @guild_context
    async def back(self, interaction, button):
        self.finished = True
        self.stop()
        await interaction.response.edit_message(content=self.editor.summary(), view=self.editor)

    @discord.ui.button(label=t("text.aeccae342e4bd0"), style=discord.ButtonStyle.danger)
    @guild_context
    async def close(self, interaction, button):
        self.finished = True
        self.stop()
        self.editor.stop()
        await interaction.response.edit_message(content=t("setup.structure.closed"), embed=None, view=None)
