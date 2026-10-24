"""Núcleo aislado de Modo Custodio.

No inicia sesión en Discord, no almacena mensajes ni ejecuta sanciones.
Las reglas oficiales se suministran desde un lector autorizado; el clasificador
contextual se integrará en una fase posterior y solo puede proponer revisiones.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Any, Mapping

SCREENING_FEATURE = "MEMBER_VERIFICATION_GATE_ENABLED"
MAX_RULES = 16
MAX_RULE_LENGTH = 2048
MAX_SUMMARY_LENGTH = 280
VALID_MODES = frozenset({"observe", "assist"})
VALID_OUTCOMES = frozenset({"clear", "suspected", "ambiguous"})
VALID_SEVERITIES = frozenset({"low", "medium", "high"})


class RulesUnavailable(ValueError):
    """No hay un reglamento vigente y verificable para supervisar."""

    def __init__(self, reason: str, http_status: int | None = None):
        self.reason = reason
        self.http_status = http_status
        super().__init__(reason)


@dataclass(frozen=True)
class RulesSnapshot:
    guild_id: int
    rules: tuple[str, ...]
    revision: str

    @property
    def count(self) -> int:
        return len(self.rules)

    def metadata(self) -> dict[str, Any]:
        """Diagnóstico sin texto del reglamento."""
        return {
            "guild_id": self.guild_id,
            "rules_count": self.count,
            "revision": self.revision,
        }


def read_snapshot(
    guild_id: int,
    guild_status: int,
    guild_payload: Mapping[str, Any],
    verification_status: int,
    verification_payload: Mapping[str, Any],
) -> RulesSnapshot:
    """Extrae reglas TERMS a partir de dos respuestas GET de la API de Discord.

    Si falla la API no se interpreta como un conjunto vacío aprobado.
    La ruta member-verification no tiene garantía pública de estabilidad.
    """
    if not isinstance(guild_id, int) or isinstance(guild_id, bool) or guild_id <= 0:
        raise ValueError("invalid_guild_id")
    if guild_status != 200 or not isinstance(guild_payload, Mapping):
        raise RulesUnavailable("guild_unavailable", guild_status)
    features = guild_payload.get("features")
    if not isinstance(features, list) or not all(isinstance(f, str) for f in features):
        raise RulesUnavailable("features_unknown")
    if SCREENING_FEATURE not in features:
        raise RulesUnavailable("screening_disabled")
    if verification_status != 200 or not isinstance(verification_payload, Mapping):
        raise RulesUnavailable("verification_unavailable", verification_status)
    form_fields = verification_payload.get("form_fields")
    if not isinstance(form_fields, list):
        raise RulesUnavailable("unexpected_verification_payload")

    collected: list[str] = []
    for field in form_fields:
        if not isinstance(field, Mapping):
            raise RulesUnavailable("unexpected_verification_payload")
        if field.get("field_type") != "TERMS":
            continue
        values = field.get("values")
        if not isinstance(values, list):
            raise RulesUnavailable("unexpected_verification_payload")
        for rule in values:
            if not isinstance(rule, str) or not rule.strip() or len(rule) > MAX_RULE_LENGTH:
                raise RulesUnavailable("invalid_rule_content")
            collected.append(rule)

    if not collected:
        raise RulesUnavailable("rules_empty")
    if len(collected) > MAX_RULES:
        raise RulesUnavailable("too_many_rules")
    serialized = json.dumps(collected, ensure_ascii=False, separators=(",", ":"))
    revision = sha256(serialized.encode("utf-8")).hexdigest()
    return RulesSnapshot(guild_id, tuple(collected), revision)


@dataclass(frozen=True)
class ReviewPlan:
    """Resultado puramente declarativo: NUNCA realiza acciones sobre Discord."""

    state: str                  # paused, ignore, observe, review
    reason: str
    guild_id: int
    rule_numbers: tuple[int, ...] = ()
    severity: str | None = None
    summary: str = ""
    dedupe_key: str | None = None
    action: str = "none"        # none, record_only, notify_staff


def plan_review(
    snapshot: RulesSnapshot,
    approved_revision: str | None,
    message_id: int,
    message_revision: str,
    model_result: Mapping[str, Any] | None,
    *,
    mode: str = "observe",
) -> ReviewPlan:
    """Control de seguridad para un futuro clasificador, sin efectos laterales.

    El resultado de IA no autoriza borrar, sancionar, expulsar ni banear.
    Reglas nuevas o no aprobadas suspenden la evaluación.
    """
    if mode not in VALID_MODES:
        raise ValueError("mode_not_available")
    if (
        not approved_revision
        or snapshot.revision != approved_revision
    ):
        return ReviewPlan("paused", "rules_not_approved", snapshot.guild_id)
    if not isinstance(message_id, int) or isinstance(message_id, bool) or message_id <= 0:
        raise ValueError("invalid_message_id")
    if not isinstance(message_revision, str) or not message_revision or len(message_revision) > 128:
        raise ValueError("invalid_message_revision")

    raw_key = f"{snapshot.guild_id}:{message_id}:{message_revision}:{snapshot.revision}"
    dedupe_key = sha256(raw_key.encode("utf-8")).hexdigest()
    if not isinstance(model_result, Mapping):
        return ReviewPlan("review", "classifier_unavailable", snapshot.guild_id, dedupe_key=dedupe_key, action="notify_staff")

    outcome = model_result.get("outcome")
    numbers = model_result.get("rule_numbers", [])
    severity = model_result.get("severity", "medium")
    summary = model_result.get("summary", "")
    if (
        outcome not in VALID_OUTCOMES
        or not isinstance(numbers, (tuple, list))
        or not all(type(n) is int and 1 <= n <= snapshot.count for n in numbers)
        or not isinstance(severity, str)
        or severity not in VALID_SEVERITIES
        or not isinstance(summary, str)
    ):
        return ReviewPlan("review", "invalid_classifier_result", snapshot.guild_id, dedupe_key=dedupe_key, action="notify_staff")
    rule_numbers = tuple(sorted(set(numbers)))
    if outcome == "clear":
        if rule_numbers:
            return ReviewPlan("review", "inconsistent_classifier_result", snapshot.guild_id, dedupe_key=dedupe_key, action="notify_staff")
        return ReviewPlan("ignore", "no_violation", snapshot.guild_id, dedupe_key=dedupe_key)
    if not rule_numbers:
        return ReviewPlan("review", "missing_rule_reference", snapshot.guild_id, dedupe_key=dedupe_key, action="notify_staff")

    return ReviewPlan(
        "observe" if mode == "observe" else "review",
        "suspected_violation" if outcome == "suspected" else "ambiguous_context",
        snapshot.guild_id,
        rule_numbers=rule_numbers,
        severity=severity,
        summary=summary[:MAX_SUMMARY_LENGTH],
        dedupe_key=dedupe_key,
        action="record_only" if mode == "observe" else "notify_staff",
    )
