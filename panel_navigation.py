"""Close controls for rendered administrative panels, including nested drafts."""
import discord

from production_panel_text import guild_context, text as _t, use_guild, variants


def lineage(view):
    seen = set()
    while view is not None and id(view) not in seen:
        seen.add(id(view))
        yield view
        view = next((getattr(view, name) for name in ("parent", "editor", "parent_view", "setup_view")
                     if getattr(view, name, None) is not None), None)


class AdministrativeClose(discord.ui.Button):
    def __init__(self, guild_id, owner_id):
        self.guild_id, self.owner_id = guild_id, owner_id
        with use_guild(guild_id):
            super().__init__(label=_t("text.aeccae342e4bd0"), style=discord.ButtonStyle.danger)

    @guild_context
    async def callback(self, interaction):
        perms = getattr(interaction.user, "guild_permissions", None)
        if (interaction.guild is None or interaction.guild.id != self.guild_id
                or interaction.user.id != self.owner_id or not getattr(perms, "manage_guild", False)):
            return await interaction.response.send_message(_t("setup.access_denied"), ephemeral=True)
        if not await self.view.interaction_check(interaction):
            return
        for panel in lineage(self.view):
            panel.stop()
        await interaction.response.edit_message(content=_t("setup.structure.closed"), embed=None, view=None)


def ensure_close_control(view):
    if not isinstance(view, discord.ui.View):
        return
    panels = tuple(lineage(view))
    owner = next((panel for panel in panels if getattr(panel, "guild_id", None)
                  and getattr(panel, "owner_id", None)), None)
    if owner is None:
        return
    labels = variants("text.aeccae342e4bd0")
    existing = [item for item in view.children if isinstance(item, discord.ui.Button) and item.label in labels]
    if existing:
        for item in existing:
            item.style = discord.ButtonStyle.danger
        return
    close = AdministrativeClose(owner.guild_id, owner.owner_id)
    for row in range(4, -1, -1):
        close.row = row
        try:
            view.add_item(close)
            return
        except ValueError:
            continue
    raise ValueError("administrative_panel_has_no_close_slot")
