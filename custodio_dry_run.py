"""Simulador *aislado* de decisiones Custodio, exclusivamente para pruebas.

No importa discord, no accede a SQLite, no modifica configuración ni envía
mensajes. No se debe conectar a un worker real ni llamar a sus resultados
como sanciones confirmadas.
"""
from heraldo_i18n import text as _t, guild_context as _i18n_context, use_guild as _i18n_guild
from dataclasses import dataclass


@dataclass(frozen=True)
class Scenario:
    incident_id: str
    rules_active: bool = True
    rule_applies: bool = True
    evidence_clear: bool = True
    exempt: bool = False
    requested: str = "educational_notice"
    authorized_actions: tuple[str, ...] = ("educational_notice",)
    recognized_error: bool = False
    repeated_conduct: bool = False
    double_warning_approved: bool = False


@dataclass(frozen=True)
class Decision:
    action: str
    warning_points: int = 0
    review: bool = False
    reason: str = ""


class CustodioDryRun:
    """Motor de simulación no persistente. Útil solo para contratos y ejemplos."""

    @_i18n_context
    def __init__(self):
        self._seen = {}

    @_i18n_context
    def evaluate(self, scenario: Scenario) -> Decision:
        if not scenario.incident_id:
            raise ValueError(_t('text.09686a85af66c9'))
        if scenario.incident_id in self._seen:
            return self._seen[scenario.incident_id]
        result = self._decide(scenario)
        self._seen[scenario.incident_id] = result
        return result

    @staticmethod
    def _decide(case: Scenario) -> Decision:
        if not case.rules_active:
            return Decision("none", reason=_t('text.d8652586dbffce'))
        if not case.rule_applies:
            return Decision("human_review", review=True, reason=_t('text.47dc5db6ea4504'))
        if not case.evidence_clear:
            return Decision("human_review", review=True, reason=_t('text.d6214253f2fb73'))
        if case.exempt:
            return Decision("human_review", review=True, reason=_t('text.741830f35a0ef5'))
        if case.requested not in case.authorized_actions:
            return Decision("human_review", review=True, reason=_t('text.38dc370d6a0322'))
        if case.requested == "formal_warning":
            if case.recognized_error and case.repeated_conduct and case.double_warning_approved:
                return Decision("formal_warning", warning_points=2)
            return Decision("formal_warning", warning_points=1)
        if case.requested in ("educational_notice", "educational_close", "delete_message"):
            return Decision(case.requested)
        return Decision("human_review", review=True, reason=_t('text.ebcff43cd1f739'))
