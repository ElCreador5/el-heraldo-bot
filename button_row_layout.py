"""Balanced, reusable Discord UI rows without replacing button callbacks.

Selectors keep their own rows. Ordinary actions use balanced groups of two
or three where space permits; Back/Close share the final navigation row.
Discord's five-row/five-button hard limits always take precedence.
"""
from functools import wraps

BACK_LABELS = frozenset({"volver", "back", "voltar"})
CLOSE_LABELS = frozenset({"cerrar", "close", "fechar"})


def _row_sizes(amount, rows):
    """Spread actions as evenly as possible; left-hand rows may be longer."""
    return [amount // rows + (index < amount % rows) for index in range(rows)] if rows else []


def _navigation_kind(button):
    label = str(getattr(button, "label", "") or "").strip().casefold()
    if label in BACK_LABELS:
        return "back"
    if label in CLOSE_LABELS:
        return "close"
    return None


def _choose_navigation(buttons, kind):
    matching = [button for button in buttons if _navigation_kind(button) == kind]
    if not matching:
        return None
    # Keep the panel's own callback rather than an automatically injected one.
    generic_name = "AdministrativeBack" if kind == "back" else "AdministrativeClose"
    return next((item for item in matching if type(item).__name__ != generic_name), matching[0])


def synchronize_dropdown_defaults(view):
    """Retain visible choices from the CURRENT interaction, never save them.

    A newly-created selector has no interaction values, so defaults set by
    its constructor (including intentionally blank creation forms) are kept.
    Saved selections explicitly loaded by edit views remain untouched.
    """
    import discord
    if not isinstance(view, discord.ui.View):
        return False
    changed = False
    string_select = getattr(discord.ui, "Select", None)
    select_types = (
        ("RoleSelect", "role"),
        ("UserSelect", "user"),
        ("ChannelSelect", "channel"),
    )
    for item in view.children:
        # discord.py populates _values only when Discord submitted a selection.
        # Never infer a selection from a placeholder or from stored SQLite data.
        raw = getattr(item, "_values", None)
        if not raw:
            continue
        if string_select is not None and isinstance(item, string_select):
            selected = {str(v) for v in raw}
            options = getattr(item, "options", None) or ()
            if not any(str(opt.value) in selected for opt in options):
                continue  # The options changed; do not revive an obsolete value.
            for opt in options:
                desired = str(opt.value) in selected
                if opt.default != desired:
                    opt.default = desired
                    changed = True
            continue
        kind = next((kind for class_name, kind in select_types
                     if isinstance(item, getattr(discord.ui, class_name, ()))), None)
        mixed = isinstance(item, getattr(discord.ui, "MentionableSelect", ()))
        if kind is None and not mixed:
            continue
        requested = []
        for value in raw:
            identifier = getattr(value, "id", None)
            if type(identifier) is not int or identifier <= 0:
                break
            actual_kind = kind
            if mixed:
                if isinstance(value, getattr(discord, "Role", ())):
                    actual_kind = "role"
                elif isinstance(value, (getattr(discord, "Member", ()),
                                        getattr(discord, "User", ()))):
                    actual_kind = "user"
                else:
                    break  # Never guess whether a mentionable ID is a role or user.
            requested.append((identifier, actual_kind))
        if len(requested) != len(raw):
            continue
        current = [(int(v.id), getattr(v.type, "value", v.type))
                   for v in (getattr(item, "default_values", None) or [])]
        if current == requested:
            continue
        item.default_values = [
            discord.SelectDefaultValue(
                id=value, type=getattr(discord.SelectDefaultValueType, type_name))
            for value, type_name in requested
        ]
        changed = True
    return changed


def balance_view_buttons(view):
    """Repack an existing discord.ui.View while retaining each item and callback.

    If the layout cannot fit, leave it unchanged rather than losing actions.
    Repeated rendering is idempotent. No data, permissions or actions change.
    """
    import discord
    if not isinstance(view, discord.ui.View):
        return False
    items = list(view.children)
    if not items:
        return False
    # Avoid guessing how experimental/v2 or custom-width components should fit.
    if any(not isinstance(item, discord.ui.Button) and getattr(item, "width", None) != 5
           for item in items):
        return False
    selects = [item for item in items if not isinstance(item, discord.ui.Button)]
    buttons = [item for item in items if isinstance(item, discord.ui.Button)]
    if not buttons or len(selects) >= 5:
        return False

    back = _choose_navigation(buttons, "back")
    close = _choose_navigation(buttons, "close")
    chosen_navigation = [button for button in (back, close) if button is not None]
    actions = [item for item in buttons if _navigation_kind(item) is None]
    available_rows = 5 - len(selects)
    nav_size = len(chosen_navigation)
    planned = [[item] for item in selects]

    # Keep navigation in a dedicated final row whenever Discord has room.
    separate_nav = bool(nav_size and (not actions or
                     (available_rows >= 2 and len(actions) <= (available_rows - 1) * 5)))
    if separate_nav:
        action_rows = available_rows - 1
    else:
        action_rows = available_rows
    if actions:
        minimum = (len(actions) + 4) // 5
        preferred = (len(actions) + 2) // 3
        rows = min(preferred, action_rows)
        rows = max(minimum, rows)
        if rows > action_rows:
            return False
        sizes = _row_sizes(len(actions), rows)
        if not separate_nav and nav_size:
            # Reserve the last row's edge slots for Back and Close.
            if len(actions) + nav_size > available_rows * 5:
                return False
            while sizes[-1] > 5 - nav_size:
                recipient = next((i for i in range(len(sizes) - 1)
                                  if sizes[i] < 5), None)
                if recipient is None:
                    # Allow another row if one is available.
                    if len(sizes) < available_rows:
                        sizes = _row_sizes(len(actions), len(sizes) + 1)
                        continue
                    return False
                sizes[recipient] += 1
                sizes[-1] -= 1
        offset = 0
        for size in sizes:
            planned.append(actions[offset:offset + size])
            offset += size
    if separate_nav:
        planned.append(chosen_navigation)
    elif nav_size:
        if not planned or all(group and group[0] in selects for group in planned):
            planned.append(chosen_navigation)
        else:
            last = planned[-1]
            if back is not None:
                last.insert(0, back)
            if close is not None:
                last.append(close)

    if len(planned) > 5 or any(sum(getattr(item, "width", 1) for item in row) > 5
                               for row in planned):
        return False
    desired = [(item, row_num) for row_num, row in enumerate(planned) for item in row]
    if (len(desired) == len(items)
            and all(item is old and getattr(item, "_rendered_row", None) == row_num
                    for (item, row_num), old in zip(desired, items))):
        return False

    # Re-add the SAME objects; this refreshes discord.py's private row weights.
    # Never create replacement buttons, so callbacks/custom_id/disabled stay intact.
    view.clear_items()
    for item, row_num in desired:
        item.row = row_num
        view.add_item(item)
    return True


def install(discord):
    """Apply the layout to every View serialized by discord.py."""
    original = discord.ui.View.to_components
    if getattr(original, "_heraldo_balanced_rows", False):
        return

    @wraps(original)
    def components(view):
        synchronize_dropdown_defaults(view)
        balance_view_buttons(view)
        return original(view)

    components._heraldo_balanced_rows = True
    discord.ui.View.to_components = components
