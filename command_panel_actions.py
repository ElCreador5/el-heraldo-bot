"""Confirm sensitive actions exposed by the consolidated command panels."""
import copy
import json
from datetime import datetime, timezone

import discord

from heraldo_i18n import guild_context, text as _t


class RaidActionConfirm(discord.ui.View):
    @guild_context
    def __init__(self, host, parent, action):
        self.host, self.parent, self.action = host, parent, action
        self.guild_id, self.owner_id = parent.guild_id, parent.owner_id
        self.original_until = host["raid_until"](self.guild_id)
        self.original_settings = {key: host["guild_config_get"](self.guild_id, key) for key in (
            "raid_enabled", "raid_threshold", "raid_window_seconds", "raid_duration_seconds",
            "raid_action", "raid_min_age_seconds", "raid_new_account_ratio",
            "raid_pause_invites", "raid_purge", "raid_ping_role")}
        self.finished = False
        super().__init__(timeout=180)

    async def interaction_check(self, interaction):
        return not self.finished and await self.host["configuration_access"](interaction, self.guild_id, self.owner_id)

    @discord.ui.button(label=_t("setup.structure.confirm_button"), style=discord.ButtonStyle.success)
    @guild_context
    async def confirm(self, interaction, button):
        if not await self.interaction_check(interaction):
            return
        if (self.host["raid_until"](self.guild_id) != self.original_until
                or any(self.host["guild_config_get"](self.guild_id, key) != value
                       for key, value in self.original_settings.items())):
            return await interaction.response.send_message(_t("setup.structure.conflict"), ephemeral=True)
        self.finished = True
        await interaction.response.defer()
        try:
            if self.action == "start":
                await self.host["raid_start"](interaction.guild,
                    trigger=_t("setup.command_panels.manual_raid", user=interaction.user),
                    suspects=[], started_by=interaction.user)
            else:
                await self.host["raid_end"](interaction.guild, automatic=False,
                    ended_by=interaction.user, release=self.action == "release")
        finally:
            self.stop()
        await interaction.edit_original_response(content=self.host["raid_config_summary"](interaction.guild),
                                                  embed=None, view=self.parent)

    @discord.ui.button(label=_t("text.ab26ae7bca3621"), style=discord.ButtonStyle.secondary)
    @guild_context
    async def back(self, interaction, button):
        self.finished = True
        self.stop()
        await interaction.response.edit_message(content=self.host["raid_config_summary"](interaction.guild),
                                                 embed=None, view=self.parent)


class EmbedCreateReview(discord.ui.View):
    @guild_context
    def __init__(self, host, parent, name, data):
        self.host, self.parent, self.name, self.data = host, parent, name, copy.deepcopy(data)
        self.guild_id, self.owner_id = parent.guild_id, parent.owner_id
        self.finished = False
        super().__init__(timeout=300)

    async def interaction_check(self, interaction):
        return (not self.finished and not self.parent.is_finished()
                and await self.host["configuration_access"](interaction, self.guild_id, self.owner_id))

    @discord.ui.button(label=_t("setup.structure.confirm_button"), style=discord.ButtonStyle.success)
    @guild_context
    async def confirm(self, interaction, button):
        if not await self.interaction_check(interaction):
            return
        conn = self.host["_embed_conn"]()
        try:
            result = conn.execute("INSERT OR IGNORE INTO custom_embeds(guild_id,name,data,refs,updated_at) VALUES(?,?,?,'[]',?)",
                (self.guild_id, self.name, json.dumps(self.data, ensure_ascii=False), datetime.now(timezone.utc).isoformat()))
            conn.commit()
            if result.rowcount != 1:
                return await interaction.response.send_message(_t("setup.command_panels.name_exists"), ephemeral=True)
        finally:
            conn.close()
        self.finished = True
        self.stop()
        await self.host["embed_refresh"](interaction, self.name)

    @discord.ui.button(label=_t("text.ab26ae7bca3621"), style=discord.ButtonStyle.secondary)
    @guild_context
    async def back(self, interaction, button):
        self.finished = True
        self.stop()
        await interaction.response.edit_message(content=_t("setup.command_panels.embeds_hub"), embed=None, view=self.parent)
