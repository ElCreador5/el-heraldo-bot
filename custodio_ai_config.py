"""Configuración segura propuesta para IA de Server Rules en Custodio.

Módulo aislado: no abre red, no descarga modelos, no llama a Discord ni escribe
SQLite. La IA no está instalada ni conectada al bot por importar este archivo.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class CustodioAIConfig:
    enabled: bool = False
    purpose: str = "server_rule_ambiguity_only"
    trigger: str = "administrator_manual_analyze_rules"
    provider: str = "none"
    model: str = ""
    maximum_rule_chars: int = 6000
    timeout_seconds: int = 30
    require_human_approval: bool = True
    allow_messages: bool = False
    allow_user_profiles: bool = False
    allow_sanctions: bool = False
    allow_auto_rule_edit: bool = False
    allow_background_analysis: bool = False

    def validate(self):
        if self.purpose != "server_rule_ambiguity_only":
            raise ValueError("IA solo permitida para ambigüedades de Server Rules")
        if self.trigger != "administrator_manual_analyze_rules":
            raise ValueError("El análisis requiere inicio manual del administrador")
        if not self.require_human_approval:
            raise ValueError("Las sugerencias requieren aprobación humana")
        if any((self.allow_messages, self.allow_user_profiles, self.allow_sanctions,
                self.allow_auto_rule_edit, self.allow_background_analysis)):
            raise ValueError("Capacidad fuera del alcance autorizado para IA")
        if not 1 <= self.maximum_rule_chars <= 6000:
            raise ValueError("Límite de caracteres inválido")
        if not 1 <= self.timeout_seconds <= 60:
            raise ValueError("Timeout inválido")
        if self.enabled and (self.provider == "none" or not self.model):
            raise ValueError("No activar IA sin proveedor y modelo verificados")
        return self


def prepare_rule_analysis(*, config: CustodioAIConfig, rules_active: bool,
                          administrator_requested: bool, text: str) -> dict:
    """Solo prepara una solicitud; nunca ejecuta inferencia ni cambia reglas."""
    config.validate()
    if not rules_active:
        return {"status": "blocked", "reason": "server_rules_inactive"}
    if not administrator_requested:
        return {"status": "blocked", "reason": "manual_action_required"}
    if not config.enabled:
        return {"status": "manual_review", "reason": "ai_not_configured"}
    if not isinstance(text, str) or not text.strip():
        return {"status": "blocked", "reason": "empty_rules"}
    if len(text) > config.maximum_rule_chars:
        return {"status": "blocked", "reason": "rules_too_long"}
    return {"status": "prepared_not_executed", "text": text, "approval_required": True}
