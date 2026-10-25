"""Preferencias seguras de Modo Custodio; sin sanciones ni servicios externos.

El sistema todavía no procesa mensajes. Estos ajustes solo preparan el
futuro modo Observar, y nunca habilitan el bot o sanciones automáticamente.
"""
from __future__ import annotations
from heraldo_i18n import text as _t, guild_context as _i18n_context, use_guild as _i18n_guild
from dataclasses import dataclass
from typing import Callable

PREFIX = "custodio_"
KEY_MODE = PREFIX + "mode"
KEY_SENSITIVITY = PREFIX + "sensitivity"
KEY_SCOPE = PREFIX + "scope"
KEY_NOTIFY = PREFIX + "notify_changes"
KEY_ENABLED = PREFIX + "enabled"

DEFAULTS = {
    KEY_MODE: "observe",
    KEY_SENSITIVITY: "balanced",
    KEY_SCOPE: "eligible",
    KEY_NOTIFY: "0",
    KEY_ENABLED: "0",
}
# Otros valores son futuros, no se ofrecen hasta implementar sus garantías.
ALLOWED = {
    KEY_MODE: frozenset({"observe"}),
    KEY_SENSITIVITY: frozenset({"conservative", "balanced", "strict"}),
    KEY_SCOPE: frozenset({"eligible"}),
    KEY_NOTIFY: frozenset({"0"}),
    KEY_ENABLED: frozenset({"0"}),
}
LABELS = {
    KEY_MODE: _t('text.60a768691b6ae3'),
    KEY_SENSITIVITY: _t('text.809853d64fec84'),
    KEY_SCOPE: _t('text.477f2a69f25fbe'),
    KEY_NOTIFY: _t('text.29b7e825b434dd'),
    KEY_ENABLED: _t('text.1f286c36208889'),
}
DISPLAY = {
    KEY_MODE: {"observe": _t('text.1eb041c4d73c8d')},
    KEY_SENSITIVITY: {
        "conservative": _t('text.4227fbef304d05'),
        "balanced": _t('text.911d1179bfed6c'),
        "strict": _t('text.87956eb4fc2585'),
    },
    KEY_SCOPE: {"eligible": _t('text.8ba04df688d575')},
    KEY_NOTIFY: {"0": _t('text.1b70e48efeecce')},
    KEY_ENABLED: {"0": _t('text.77317410e35649')},
}


@dataclass(frozen=True)
class CustodioPreferences:
    mode: str = "observe"
    sensitivity: str = "balanced"
    scope: str = "eligible"
    notify_changes: str = "0"
    enabled: str = "0"

    @_i18n_context
    def as_settings(self) -> dict[str, str]:
        return dict(zip(DEFAULTS, (
            self.mode, self.sensitivity, self.scope, self.notify_changes, self.enabled,
        )))


def validate_settings(values: dict[str, str]) -> dict[str, str]:
    if set(values) != set(DEFAULTS):
        raise ValueError("custodio_keys_invalid")
    for key, value in values.items():
        if value not in ALLOWED[key]:
            raise ValueError(f"custodio_value_invalid:{key}")
    return values.copy()


@_i18n_context
def load_preferences(get_setting: Callable[[int, str], str | None], guild_id: int) -> CustodioPreferences:
    if type(guild_id) is not int or guild_id <= 0:
        raise ValueError("invalid_guild_id")
    raw = {key: get_setting(guild_id, key) for key in DEFAULTS}
    settings = {key: (value if value in ALLOWED[key] else DEFAULTS[key])
                for key, value in raw.items()}
    return CustodioPreferences(
        settings[KEY_MODE],
        settings[KEY_SENSITIVITY],
        settings[KEY_SCOPE],
        settings[KEY_NOTIFY],
        settings[KEY_ENABLED],
    )


def pending_changes(
    saved: CustodioPreferences,
    sensitivity: str,
) -> dict[str, str]:
    """Persistir únicamente lo autorizado; no activar vigilancia por guardar."""
    proposal = CustodioPreferences(sensitivity=sensitivity).as_settings()
    validate_settings(proposal)
    return {key: value for key, value in proposal.items()
            if saved.as_settings()[key] != value}


def display_preferences(prefs: CustodioPreferences) -> str:
    return (
        _t('text.678e2d5eab4062', p0=f'{DISPLAY[KEY_SENSITIVITY][prefs.sensitivity]}')
    )
