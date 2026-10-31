"""Estado de «Guardar cambios» en los paneles nativos de /setup.

Solo modifica la disponibilidad visual del botón. Nunca persiste datos ni
interfiere con Confirmar cambios, Activar, Pausar o Publicar.
"""
from __future__ import annotations

import sys

SAVE_LABELS = {"Guardar cambios", "Save changes", "Salvar alterações"}
# Las variantes del catálogo son traducibles sin depender del idioma del usuario.
SUPPORTED = {
    "HeraldoChannelSetupView", "HeraldoRoleSetupView",
    "HeraldoJoinRolesBasicView", "HeraldoJoinRolesUsersView",
    "HeraldoJoinRolesBotsView", "HeraldoJoinRolesSyncView",
    "HeraldoOrientationSetupView", "HeraldoMotwSetupView",
    "HeraldoHoneypotSetupView", "HeraldoHoneypotDraftSubView",
    "HeraldoVerificationSetupView", "HeraldoRaidSetupView",
    "HeraldoUserReportsSetupView", "ReportReminderSetupView",
    "EmbedEditorView", "TemplateEditorView", "AutofeedEditorView",
    "PolicyView",
}


def _any_pending(view, *names):
    return any(getattr(view, name, None) is not None for name in names)


def _different_saved(view, values, getter_name):
    """Evita habilitar Guardar si se volvió a escoger el valor persistido."""
    module = sys.modules.get(type(view).__module__)
    getter = getattr(module, getter_name, None) if module else None
    if getter is None:
        return bool(values)
    return any(getter(view.guild_id, key) != value for key, value in values.items())


def has_unsaved_changes(view):
    """Devuelve None para controles desconocidos: nunca bloquear por suposición."""
    if view is None:
        return None
    name = type(view).__name__
    if name not in SUPPORTED:
        return None
    if name == "HeraldoChannelSetupView":
        return _different_saved(view, view.pending_channels, "get_guild_channel_id")
    if name == "HeraldoRoleSetupView":
        module = sys.modules.get(type(view).__module__)
        getter = getattr(module, "guild_resource_get", None) if module else None
        if getter is None:
            return bool(view.pending_roles)
        return any(getter(view.guild_id, "role", key) != value
                   for key, value in view.pending_roles.items())
    if name == "HeraldoJoinRolesBasicView":
        return _any_pending(view, "pending_role_ids", "pending_screening",
                            "pending_enabled", "pending_delay")
    if name == "HeraldoJoinRolesUsersView":
        return _any_pending(view, "pending_remove_after")
    if name == "HeraldoJoinRolesBotsView":
        return _any_pending(view, "pending_role_ids", "pending_enabled",
                            "pending_delay", "pending_different")
    if name == "HeraldoJoinRolesSyncView":
        return _any_pending(view, "pending_excluded")
    if name == "HeraldoOrientationSetupView":
        return _any_pending(view, "pending_channel_id", "pending_bindings",
                            "pending_enabled", "pending_required",
                            "pending_allow_change", "pending_dm_template")
    if name == "HeraldoMotwSetupView":
        return (getattr(view, "pending_channel_id", None) is not None
                and view.pending_channel_id != getattr(view, "original_channel_id", None))
    if name in {"HeraldoHoneypotSetupView", "HeraldoHoneypotDraftSubView"}:
        parent = getattr(view, "parent", view)
        return _any_pending(parent, "pending_trap_id", "pending_enabled",
                            "pending_paused", "pending_action", "pending_kick_purge_minutes",
                            "pending_ban_minutes", "pending_timeout_minutes",
                            "pending_purge_spec")
    if name == "HeraldoVerificationSetupView":
        return _any_pending(view, "pending_role_id", "pending_sin_role_id",
                            "pending_channel_id", "pending_enabled")
    if name == "HeraldoRaidSetupView":
        return _any_pending(view, "pending_action", "pending_role_id",
                            "pending_enabled", "pending_invites", "pending_purge")
    if name in {"HeraldoUserReportsSetupView", "ReportReminderSetupView"}:
        return bool(view._has_pending_changes())
    if name == "EmbedEditorView":
        return _any_pending(view, "pending_timestamp", "pending_remove_index")
    if name == "TemplateEditorView":
        if view.original_template is None:
            # Canal, rol, fecha y frecuencia son ajustes de publicación,
            # NO modificaciones de la plantilla guardable.
            return bool(view.name.strip() or view.text.strip()
                        or view.embed or view.extra_embeds)
        try:
            return view.template() != view.original_template
        except ValueError:
            return bool(view.dirty)
    if name == "AutofeedEditorView":
        if view.original is None:
            return None  # «Enviar», no «Guardar cambios».
        saved = view.original
        try:
            values = (view.channel_id, view.role_id, view.text, view.embed,
                      view.start.isoformat() if view.start else None, view.parts)
            before = (saved.get("channel"), saved.get("role"), saved.get("text") or "",
                      saved.get("embed"), saved.get("start"), saved.get("repeat_parts"))
            return values != before
        except (TypeError, AttributeError, ValueError):
            return bool(view.dirty)
    if name == "PolicyView":
        module = sys.modules.get(type(view).__module__)
        policy = getattr(module, "policy", None) if module else None
        if policy is None:
            return None
        stored = policy(view.host, view.guild_id)
        return any(view.current.get(key) != stored.get(key)
                   for key in ("channels", "roles", "max_per_member"))
    return None


def refresh_save_button(view):
    """Sincroniza antes de enviar/editar el mensaje, también desde modales."""
    pending = has_unsaved_changes(view)
    if pending is None:
        return None
    try:
        from heraldo_i18n import variants
        labels = SAVE_LABELS | set(variants("text.14bdfaf2face3a"))
    except (ImportError, KeyError, TypeError):
        labels = SAVE_LABELS
    for item in view.children:
        if getattr(item, "label", None) in labels:
            item.disabled = not pending
    return pending
