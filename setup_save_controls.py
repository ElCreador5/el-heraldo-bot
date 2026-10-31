"""Estado de «Guardar cambios» en los paneles nativos de /setup.

Solo modifica la disponibilidad visual del botón. Nunca persiste datos ni
interfiere con Confirmar cambios, Activar, Pausar o Publicar.
"""
from __future__ import annotations

import sys

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


def _changed_vs_getters(view, pairs):
    """No cuenta como cambio volver a seleccionar el valor ya guardado."""
    module = sys.modules.get(type(view).__module__)
    for field, getter_name in pairs:
        pending = getattr(view, field, None)
        if pending is None:
            continue
        getter = getattr(module, getter_name, None) if module else None
        if getter is None or getter(view.guild_id) != pending:
            return True
    return False


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
        return _changed_vs_getters(view, (
            ("pending_role_ids", "get_join_role_ids"),
            ("pending_screening", "join_roles_wait_screening"),
            ("pending_enabled", "join_roles_enabled"),
            ("pending_delay", "get_join_roles_delay"),
        ))
    if name == "HeraldoJoinRolesUsersView":
        return _changed_vs_getters(view, (
            ("pending_remove_after", "join_roles_remove_specific_after_join"),
        ))
    if name == "HeraldoJoinRolesBotsView":
        return _changed_vs_getters(view, (
            ("pending_role_ids", "get_join_bot_role_ids"),
            ("pending_enabled", "join_roles_bot_enabled"),
            ("pending_delay", "join_roles_bot_apply_delay"),
            ("pending_different", "join_roles_bot_use_different"),
        ))
    if name == "HeraldoJoinRolesSyncView":
        return _changed_vs_getters(view, (
            ("pending_excluded", "get_join_sync_excluded_role_ids"),
        ))
    if name == "HeraldoOrientationSetupView":
        return (_changed_vs_getters(view, (
            ("pending_channel_id", "get_orientation_channel_id"),
            ("pending_bindings", "get_orientation_bindings"),
            ("pending_enabled", "orientation_enabled"),
            ("pending_required", "personality_required"),
            ("pending_allow_change", "personality_allow_change"),
        )) or _any_pending(view, "pending_dm_template"))
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
        return _changed_vs_getters(view, (
            ("pending_action", "raid_action"),
            ("pending_role_id", "raid_ping_role_id"),
            ("pending_enabled", "raid_enabled"),
            ("pending_invites", "raid_lock_invites_enabled"),
            ("pending_purge", "raid_purge_enabled"),
        ))
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
            return not view._is_saved()
        except ValueError:
            return bool(view.dirty)
    if name == "AutofeedEditorView":
        checker = getattr(view, "_has_pending_changes", None)
        if callable(checker):
            return bool(checker())
        if view.original is None:
            return None  # Compatibilidad con vistas antiguas.
        saved = view.original
        try:
            source = sys.modules.get(type(view).__module__)
            presets = getattr(source, "PRESETS", {}) if source else {}
            repeat = saved.get("repeat")
            preset = {"diaria": "daily", "semanal": "weekly", "mensual": "monthly"}.get(repeat)
            old_parts = (saved.get("repeat_parts") if repeat == "custom" else
                         dict(presets[preset]) if preset in presets else None)
            values = (view.channel_id, view.role_id, view.text, view.embed,
                      view.start.isoformat() if view.start else None, view.parts)
            before = (saved.get("channel"), saved.get("role"), saved.get("text") or "",
                      saved.get("embed"), saved.get("start"), old_parts)
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
    from heraldo_i18n import variants
    labels = set(variants("text.14bdfaf2face3a"))
    for item in view.children:
        if getattr(item, "label", None) in labels:
            item.disabled = not pending
    # En Anuncios, Descartar cambia de estado junto con Guardar.
    if type(view).__name__ == "AutofeedEditorView":
        discard = getattr(view, "discard", None)
        if discard in view.children:
            discard.disabled = not pending
    return pending
