"""Confirmed configuration for the existing server structure backup scheduler."""
from datetime import datetime, timedelta, timezone, time
import unicodedata

from heraldo_datetime import format_clock, parse_clock

import discord

from heraldo_i18n import guild_context, text as t
from operation_progress import status_text


FIELDS = {
    "template_mode": "get_template_mode",
    "template_hour": "get_template_hour",
    "template_minute": "get_template_minute",
    "template_weekday": "get_template_weekday",
    "template_monthday": "get_template_monthday",
}
MARKERS = ("template_last_run", "template_last_slot", "template_interval_minutes")
ACTIVE_MODES = ("off", "daily", "weekly", "monthly")
SCHEDULED_MODES = ("daily", "weekly", "monthly")


def last_slot(values, now):
    """Same calendar as the historical scheduler; no DB writes or API calls."""
    mode = values["template_mode"]
    slot = now.replace(hour=int(values["template_hour"]), minute=int(values.get("template_minute", 0)), second=0, microsecond=0)
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


def weekday_label(index: int) -> str:
    """Nombre visible del día según el idioma del servidor."""
    return t("setup.structure.weekday." + str(index))


def parse_weekday(value: str) -> int:
    """Reconoce el nombre de día en los tres idiomas y los índices anteriores."""
    clean = "".join(
        character for character in unicodedata.normalize("NFKD", value.strip().casefold())
        if not unicodedata.combining(character)
    )
    if clean in {str(index) for index in range(7)}:
        return int(clean)
    variants = {
        0: ("lunes", "monday", "segunda", "segunda-feira"),
        1: ("martes", "tuesday", "terca", "terca-feira"),
        2: ("miercoles", "wednesday", "quarta", "quarta-feira"),
        3: ("jueves", "thursday", "quinta", "quinta-feira"),
        4: ("viernes", "friday", "sexta", "sexta-feira"),
        5: ("sabado", "saturday"),
        6: ("domingo", "sunday"),
    }
    for index, names in variants.items():
        if clean in names:
            return index
    raise ValueError("weekday")


class StructureScheduleModal(discord.ui.Modal):
    """Muestra solo los campos que necesita la frecuencia elegida."""
    @guild_context
    def __init__(self, editor):
        self.editor = editor
        self.guild_id, self.owner_id = editor.guild_id, editor.owner_id
        self.mode = editor.values["template_mode"]
        if self.mode not in SCHEDULED_MODES:
            raise ValueError("unsupported_schedule_mode")
        super().__init__(title=t("setup.structure.schedule"))
        clock = format_clock(
            time(int(editor.values["template_hour"]), int(editor.values["template_minute"])),
            editor.date_mode, editor.time_mode,
        )
        # La hora siempre es exacta, no una duración.
        self.clock = discord.ui.TextInput(
            label=t("setup.structure.clock"), required=True,
            default=clock, placeholder=clock, max_length=16,
        )
        if self.mode == "weekly":
            label = weekday_label(int(editor.values["template_weekday"]))
            self.weekday = discord.ui.TextInput(
                label=t("setup.structure.weekday_name"), required=True,
                default=label, placeholder=weekday_label(0), max_length=24,
            )
            self.add_item(self.weekday)
        elif self.mode == "monthly":
            self.monthday = discord.ui.TextInput(
                label=t("setup.structure.monthday"), required=True,
                default=editor.values["template_monthday"], placeholder="15", max_length=2,
            )
            self.add_item(self.monthday)
        self.add_item(self.clock)

    @guild_context
    async def on_submit(self, interaction):
        if not await self.editor.interaction_check(interaction):
            return
        if (self.editor.is_finished() or self.editor.values["template_mode"] != self.mode):
            return await interaction.response.send_message(t("setup.structure.expired"), ephemeral=True)
        try:
            clock = parse_clock(str(self.clock))
            proposed = {"template_hour": str(clock.hour), "template_minute": str(clock.minute)}
            if self.mode == "weekly":
                proposed["template_weekday"] = str(parse_weekday(str(self.weekday)))
            elif self.mode == "monthly":
                monthday = int(str(self.monthday).strip())
                if not 1 <= monthday <= 28:
                    raise ValueError("monthday")
                proposed["template_monthday"] = str(monthday)
        except ValueError:
            return await interaction.response.send_message(t("setup.structure.invalid"), ephemeral=True)
        self.editor.values.update(proposed)
        self.editor.refresh()
        await interaction.response.edit_message(
            content=self.editor.summary(), embed=None, view=self.editor,
        )

class ServerStructureSetupView(discord.ui.View):
    @guild_context
    def __init__(self, host, guild_id, owner_id):
        self.host, self.guild_id, self.owner_id = host, guild_id, owner_id
        self.date_mode = host["guild_config_get"](guild_id, "display_date_format") or "discord"
        self.time_mode = host["guild_config_get"](guild_id, "display_time_format")
        super().__init__(timeout=900)
        self.original = {key: host["guild_config_get"](guild_id, key) for key in (*FIELDS, *MARKERS)}
        self.initial = {key: str(host[getter](guild_id)) for key, getter in FIELDS.items()}
        self.values = dict(self.initial)
        chooser = discord.ui.Select(
            placeholder=t("setup.structure.choose"), row=0,
            options=[discord.SelectOption(
                label=t("setup.structure.mode.legacy_interval")
                      if mode == "interval" else t("setup.structure.mode." + mode),
                value=mode,
                description=t("setup.structure.help.legacy_interval")
                            if mode == "interval" else t("setup.structure.help." + mode),
            )
                     for mode in ((*ACTIVE_MODES, "interval")
                                  if self.initial["template_mode"] == "interval"
                                  else ACTIVE_MODES)])
        chooser.callback = self.choose
        self.chooser = chooser
        self.add_item(chooser)
        self.sync_now.label = t("setup.structure.sync")
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
        self.schedule.disabled = self.values["template_mode"] not in SCHEDULED_MODES

    @guild_context
    def summary(self):
        mode = self.values["template_mode"]
        clock = format_clock(
            time(int(self.values["template_hour"]), int(self.values["template_minute"])),
            self.date_mode, self.time_mode,
        )
        if mode == "daily":
            detail = t("setup.structure.detail.daily", clock=clock)
        elif mode == "weekly":
            detail = t(
                "setup.structure.detail.weekly",
                weekday=weekday_label(int(self.values["template_weekday"])),
                clock=clock,
            )
        elif mode == "monthly":
            detail = t(
                "setup.structure.detail.monthly",
                monthday=self.values["template_monthday"], clock=clock,
            )
        elif mode == "interval":
            detail = t("setup.structure.detail.legacy")
        else:
            detail = t("setup.structure.detail.off")
        original = (t("setup.structure.legacy_active")
                    if self.initial["template_mode"] == "interval"
                    else self.host["template_config_summary"](
                        self.guild_id, datetime.now(timezone.utc)))
        return (t("setup.structure.title") + "\n\n" + original + "\n\n"
                + t("setup.structure.draft",
                    mode=t("setup.structure.mode.legacy_interval") if mode == "interval"
                    else t("setup.structure.mode." + mode),
                    details=detail))
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
        if self.values["template_mode"] not in SCHEDULED_MODES:
            return await interaction.response.send_message(
                t("setup.structure.select_frequency"), ephemeral=True)
        await interaction.response.send_modal(StructureScheduleModal(self))

    @discord.ui.button(label="Sincronizar ahora", style=discord.ButtonStyle.secondary, row=1)
    @guild_context
    async def sync_now(self, interaction, button):
        if self._has_pending_changes():
            return await interaction.response.send_message(t("setup.structure.sync_unsaved"), ephemeral=True)
        confirm = StructureSyncConfirmView(self)
        await interaction.response.edit_message(
            content=self.summary() + "\n\n" + t("setup.structure.sync_confirm"), view=confirm)

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


class StructureSyncConfirmView(discord.ui.View):
    """Confirmación manual sin alterar la frecuencia ni otros ajustes."""
    @guild_context
    def __init__(self, editor):
        self.editor = editor
        self.guild_id, self.owner_id = editor.guild_id, editor.owner_id
        self.running = False
        super().__init__(timeout=300)
        self.execute.label = t("setup.structure.sync_do")

    async def interaction_check(self, interaction):
        return (not self.running and not self.is_finished()
                and await self.editor.interaction_check(interaction))

    @discord.ui.button(label="Confirmar sincronización", style=discord.ButtonStyle.success)
    @guild_context
    async def execute(self, interaction, button):
        if not await self.interaction_check(interaction):
            return
        if self.editor.is_finished() or self.editor._has_pending_changes():
            return await interaction.response.send_message(t("setup.structure.expired"), ephemeral=True)
        self.running = True
        host, guild = self.editor.host, interaction.guild
        locale = host["guild_language"](guild.id)
        # This is a multi-request API operation, not a counted batch.
        # Acknowledge its active state without inventing a percentage.
        await interaction.response.edit_message(
            content=status_text(locale, "template_running"),
            embed=None, view=None,
        )
        try:
            template, dirty, error = await host["sync_server_template"](guild)
            if error:
                outcome = t("setup.structure.sync_error", error=error)
            else:
                embed = host["template_report_embed"](guild, template, dirty, "manual")
                try:
                    owner = await host["bot"].fetch_user(guild.owner_id)
                    await owner.send(embed=host["stamp_embed"](embed.copy(), guild))
                    outcome = t("setup.structure.sync_sent")
                except discord.HTTPException:
                    outcome = t("setup.structure.sync_dm_failed")
                await host["log_embed"](
                    guild, t("text.ad1fa0172380ff"),
                    t("text.22854288f334bb", p0=interaction.user.mention),
                    discord.Color.blurple(),
                )
        except discord.HTTPException as exc:
            outcome = t("setup.structure.sync_error", error=str(exc))
        except Exception as exc:
            print(f"STRUCTURE_SYNC status=FAILED guild={guild.id} "
                  f"error={type(exc).__name__}", flush=True)
            outcome = t("setup.structure.sync_error", error=type(exc).__name__)
        finally:
            self.stop()
        view = ServerStructureSetupView(host, self.guild_id, self.owner_id)
        summary = view.summary()
        await interaction.edit_original_response(
            content=summary[:max(0, 1998 - len(outcome))] + "\n\n" + outcome,
            embed=None, view=view,
        )

    @discord.ui.button(label=t("text.ab26ae7bca3621"), style=discord.ButtonStyle.secondary)
    @guild_context
    async def back(self, interaction, button):
        self.stop()
        await interaction.response.edit_message(content=self.editor.summary(), view=self.editor)

    @discord.ui.button(label=t("text.aeccae342e4bd0"), style=discord.ButtonStyle.danger)
    @guild_context
    async def close(self, interaction, button):
        self.stop()
        self.editor.stop()
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
        if self.pending["template_mode"] not in ACTIVE_MODES:
            return await interaction.response.send_message(
                t("setup.structure.select_frequency"), ephemeral=True)
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
