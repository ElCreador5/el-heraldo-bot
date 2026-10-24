"""Plantillas de respuesta por categoría de Custodio (solo configuración).

NH son los estándares internos del bot, NO las reglas de convivencia.
Ninguna plantilla concede permiso para sancionar: la supervisión y el
motor de clasificación/ejecución siguen desactivados.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Callable, Mapping

SETTING_KEY = "custodio_rule_actions_v1"
VALID_ACTIONS = frozenset({"report", "warn", "kick", "ban", "temp_ban"})
SCHEMA_VERSION = 1
MAX_POLICY_BYTES = 4096


@dataclass(frozen=True)
class RuleTemplate:
    key: str
    label: str
    suggested_action: str
    description: str


# Sugerencias editoriales, NO reglas universales. Cada servidor decide
# cuáles de estas categorías existen realmente en sus Server Rules.
TEMPLATES: tuple[RuleTemplate, ...] = (
    RuleTemplate("spam", "Spam y publicidad", "report",
                 "Mensajes repetidos o publicidad prohibida por el servidor."),
    RuleTemplate("harassment", "Acoso reiterado", "kick",
                 "Hostigamiento corroborado según las reglas locales."),
    RuleTemplate("scams", "Fraude y suplantación", "ban",
                 "Fraude comprobado o suplantación prohibida."),
    RuleTemplate("threats", "Amenazas graves", "ban",
                 "Amenazas creíbles y verificadas, no citas ni denuncias."),
    RuleTemplate("channel_content", "Contenido fuera de lugar", "report",
                 "Publicaciones contrarias a las reglas del canal; respetar SFW/NSFW."),
)
TEMPLATE_BY_KEY = {item.key: item for item in TEMPLATES}
DEFAULT_ACTIONS = {item.key: "report" for item in TEMPLATES}


class InvalidRuleActions(ValueError):
    pass


def validate_actions(actions: Mapping[str, str]) -> dict[str, str]:
    """Evitar categorías inventadas o acciones no admitidas."""
    if not isinstance(actions, Mapping) or set(actions) != set(DEFAULT_ACTIONS):
        raise InvalidRuleActions("invalid_categories")
    if any(type(v) is not str or v not in VALID_ACTIONS for v in actions.values()):
        raise InvalidRuleActions("invalid_actions")
    return {key: actions[key] for key in DEFAULT_ACTIONS}


def encode_actions(actions: Mapping[str, str]) -> str:
    """Las sanciones quedan expresamente INACTIVAS hasta otra fase aprobada."""
    payload = {
        "version": SCHEMA_VERSION,
        "enforcement_enabled": False,
        "actions": validate_actions(actions),
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    if len(encoded.encode("utf-8")) > MAX_POLICY_BYTES:
        raise InvalidRuleActions("oversized_policy")
    return encoded


def decode_actions(raw: str | None) -> tuple[dict[str, str], bool]:
    """Fail closed si faltan datos o fueron alterados fuera de /setup."""
    if raw is None:
        return DEFAULT_ACTIONS.copy(), False
    if not isinstance(raw, str) or len(raw.encode("utf-8")) > MAX_POLICY_BYTES:
        return DEFAULT_ACTIONS.copy(), False
    try:
        data = json.loads(raw)
        if (
            not isinstance(data, dict)
            or set(data) != {"version", "enforcement_enabled", "actions"}
            or type(data["version"]) is not int
            or data["version"] != SCHEMA_VERSION
            or data["enforcement_enabled"] is not False
        ):
            return DEFAULT_ACTIONS.copy(), False
        return validate_actions(data["actions"]), True
    except (ValueError, TypeError, KeyError):
        return DEFAULT_ACTIONS.copy(), False


def load_actions(
    get_setting: Callable[[int, str], str | None], guild_id: int
) -> tuple[dict[str, str], bool]:
    if type(guild_id) is not int or guild_id <= 0:
        raise ValueError("invalid_guild_id")
    return decode_actions(get_setting(guild_id, SETTING_KEY))


def suggested_action(category: str) -> str:
    if category not in TEMPLATE_BY_KEY:
        raise InvalidRuleActions("unknown_category")
    return TEMPLATE_BY_KEY[category].suggested_action


def preview_action(actions: Mapping[str, str], category: str) -> str:
    """Propuesta visible para moderadores, NUNCA autorización ejecutable."""
    if category not in TEMPLATE_BY_KEY:
        raise InvalidRuleActions("unknown_category")
    return validate_actions(actions)[category]


def enforcement_permitted(*, mode: str, running: bool, approved_rules: bool,
                          verified_incident: bool, staff_exempt: bool) -> bool:
    """Puerta cerrada hasta que exista la fase de ejecución auditada.

    Aun si un perfil contiene 'ban' o 'kick', esta fase nunca los ejecuta.
    """
    return False
