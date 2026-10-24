"""Preferencias seguras de Modo Custodio; sin sanciones ni servicios externos.

El sistema todavía no procesa mensajes. Estos ajustes solo preparan el
futuro modo Observar, y nunca habilitan el bot o sanciones automáticamente.
"""
from __future__ import annotations
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
    KEY_MODE: "Modo de respuesta",
    KEY_SENSITIVITY: "Sensibilidad",
    KEY_SCOPE: "Alcance",
    KEY_NOTIFY: "Avisos de cambios",
    KEY_ENABLED: "Supervisión continua",
}
DISPLAY = {
    KEY_MODE: {"observe": "Observar"},
    KEY_SENSITIVITY: {
        "conservative": "Conservadora",
        "balanced": "Equilibrada",
        "strict": "Estricta",
    },
    KEY_SCOPE: {"eligible": "Canales elegibles y autorizados"},
    KEY_NOTIFY: {"0": "Desactivados"},
    KEY_ENABLED: {"0": "No activada"},
}


@dataclass(frozen=True)
class CustodioPreferences:
    mode: str = "observe"
    sensitivity: str = "balanced"
    scope: str = "eligible"
    notify_changes: str = "0"
    enabled: str = "0"

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
        "**Modo de respuesta:** Observar (sin sanciones)\n"
        f"**Sensibilidad:** {DISPLAY[KEY_SENSITIVITY][prefs.sensitivity]}\n"
        "**Alcance:** Canales elegibles y autorizados\n"
        "**Avisos sobre cambios en las reglas:** Desactivados\n"
        "**Supervisión continua:** No activada\n"
        "\nLas preferencias preparan la futura supervisión. El bot todavía "
        "no clasifica mensajes mediante IA ni aplica sanciones."
    )
