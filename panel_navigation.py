"""Close controls for rendered administrative panels, including nested drafts."""
import discord

from heraldo_i18n import guild_context, text as _t, use_guild, variants


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


class AdministrativeBack(discord.ui.Button):
    """Navigate to the real previous panel; never commit an unfinished draft."""

    def __init__(self, guild_id, owner_id):
        self.guild_id, self.owner_id = guild_id, owner_id
        with use_guild(guild_id):
            super().__init__(label=_t("text.ab26ae7bca3621"), style=discord.ButtonStyle.secondary)

    @guild_context
    async def callback(self, interaction):
        if not await self.view.interaction_check(interaction):
            return
        previous = getattr(self.view, "_heraldo_back_target", None)
        if isinstance(previous, discord.ui.View) and previous is not self.view:
            # This is a navigation operation, not a save or confirmation.
            payload = dict(getattr(self.view, "_heraldo_back_snapshot", {}) or {})
            payload["view"] = previous
            await interaction.response.edit_message(**payload)
            self.view.stop()
            return
        # There is no known predecessor (e.g. a slash-opened panel). Use /setup
        # as a safe destination, never an untracked or guessed subpanel.
        import sys
        host = sys.modules.get("__main__")
        if host is not None and hasattr(host, "HeraldoSetupView"):
            home = host.HeraldoSetupView(self.guild_id, self.owner_id)
            await interaction.response.edit_message(
                content=host.heraldo_setup_home_content(self.guild_id),
                embed=None, view=home)
            self.view.stop()
            return
        await interaction.response.send_message(
            _t("setup.structure.closed"), ephemeral=True)


def is_setup_home(view):
    """The first /setup screen has no previous panel to return to."""
    return type(view).__name__ == "HeraldoSetupView"


def _keep_only_close_on_setup_home(view):
    """Root navigation is Close only, preserving its original callback."""
    back_labels = variants("text.ab26ae7bca3621")
    close_labels = variants("text.aeccae342e4bd0")
    for item in tuple(view.children):
        if (isinstance(item, discord.ui.Button)
                and (isinstance(item, AdministrativeBack) or item.label in back_labels)):
            view.remove_item(item)
    closes = [item for item in view.children
              if isinstance(item, discord.ui.Button)
              and (isinstance(item, AdministrativeClose) or item.label in close_labels)]
    if not closes:
        return
    close = next((item for item in closes if not isinstance(item, AdministrativeClose)), closes[0])
    for item in closes:
        if item is not close:
            view.remove_item(item)
    close.style = discord.ButtonStyle.danger
    view._children[:] = [item for item in view.children if item is not close] + [close]


def ensure_back_control(view):
    if not isinstance(view, discord.ui.View) or is_setup_home(view):
        return
    panels = tuple(lineage(view))
    owner = next((panel for panel in panels if getattr(panel, "guild_id", None)
                  and getattr(panel, "owner_id", None)), None)
    if owner is None:
        return
    labels = variants("text.ab26ae7bca3621")
    if any(isinstance(item, discord.ui.Button) and item.label in labels for item in view.children):
        return
    back = AdministrativeBack(owner.guild_id, owner.owner_id)
    for row in range(4, -1, -1):
        back.row = row
        try:
            view.add_item(back)
            return
        except ValueError:
            continue
    # Discord permits at most five rows. Do not break an otherwise valid panel.
    print(f"PANEL_NAVIGATION status=NO_BACK_SLOT panel={type(view).__name__}", flush=True)


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



def _arrange_navigation_controls(view):
    """One Back on the left, one Close on the right, using valid Discord rows.

    Preserve existing button objects and callbacks, even when a panel defines
    custom navigation. Rebuild the rows only for the two navigation actions.
    """
    back_labels = variants("text.ab26ae7bca3621")
    close_labels = variants("text.aeccae342e4bd0")
    backs = [item for item in view.children
             if isinstance(item, discord.ui.Button)
             and (isinstance(item, AdministrativeBack) or item.label in back_labels)]
    closes = [item for item in view.children
              if isinstance(item, discord.ui.Button)
              and (isinstance(item, AdministrativeClose) or item.label in close_labels)]
    if not backs or not closes:
        return

    # Prefer the panel's own callback; never replace it with an unrelated one.
    back = next((item for item in backs if not isinstance(item, AdministrativeBack)), backs[0])
    close = next((item for item in closes if not isinstance(item, AdministrativeClose)), closes[0])
    for item in (*backs, *closes):
        view.remove_item(item)

    back.style = discord.ButtonStyle.secondary
    close.style = discord.ButtonStyle.danger

    occupied = [0] * 5
    for item in view.children:
        row = getattr(item, "_rendered_row", None)
        if row is None:
            row = item.row
        if row is not None:
            occupied[row] += item.width

    # Prefer the first free row immediately after the other controls.
    # If the panel occupies all five rows, share its last available row.
    last_used = max((row for row, width in enumerate(occupied) if width), default=-1)
    together = next((row for row in range(last_used + 1, 5)
                     if occupied[row] <= 3), None)
    if together is None:
        together = next((row for row in range(4, -1, -1)
                         if occupied[row] <= 3), None)
    if together is not None:
        back_row = close_row = together
    else:
        # Packed five-row panels may have only one spare slot in each row.
        # Keep both actions visible, with Back before Close.
        available = [row for row, width in enumerate(occupied) if width <= 4]
        if len(available) < 2:
            raise ValueError("navigation_controls_no_two_available_slots")
        back_row, close_row = available[-2:]

    back.row = back_row
    close.row = close_row
    view.add_item(back)
    view.add_item(close)

    # discord.py orders components within a rendered row by insertion order.
    # Reorder the underlying list without recreating buttons or their callbacks.
    view._children[:] = [back] + [
        item for item in view.children if item is not back and item is not close
    ] + [close]


def ensure_navigation_controls(view):
    """Normalize Back / Close on every rendered panel with known navigation."""
    if not isinstance(view, discord.ui.View):
        return
    panels = tuple(lineage(view))
    owner = next((panel for panel in panels if getattr(panel, "guild_id", None)
                  and getattr(panel, "owner_id", None)), None)
    if is_setup_home(view):
        ensure_close_control(view)
        _keep_only_close_on_setup_home(view)
        return
    if owner is not None:
        ensure_back_control(view)
        ensure_close_control(view)
    # Panels outside /setup can retain their own actions; merely standardize
    # existing Back / Close controls without inventing administrative callbacks.
    _arrange_navigation_controls(view)
