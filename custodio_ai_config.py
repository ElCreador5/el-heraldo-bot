"""Configuración segura propuesta para IA de Server Rules en Custodio.

Módulo aislado: no abre red, no descarga modelos, no llama a Discord ni escribe
SQLite. La IA no está instalada ni conectada al bot por importar este archivo.
"""
from heraldo_i18n import text as _t, guild_context as _i18n_context, use_guild as _i18n_guild
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

    @_i18n_context
    def validate(self):
        if self.purpose != "server_rule_ambiguity_only":
            raise ValueError(_t('text.8ff021901db5c3'))
        if self.trigger != "administrator_manual_analyze_rules":
            raise ValueError(_t('text.0819b80c552a4d'))
        if not self.require_human_approval:
            raise ValueError(_t('text.27f5e3e5b8e2fb'))
        if any((self.allow_messages, self.allow_user_profiles, self.allow_sanctions,
                self.allow_auto_rule_edit, self.allow_background_analysis)):
            raise ValueError(_t('text.8e3eb8e62e97bf'))
        if not 1 <= self.maximum_rule_chars <= 6000:
            raise ValueError(_t('text.04d36ae4a1f5b3'))
        if not 1 <= self.timeout_seconds <= 60:
            raise ValueError(_t('text.133a4c34ebf329'))
        if self.enabled and (self.provider == "none" or not self.model):
            raise ValueError(_t('text.3f4de686c7d83d'))
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
