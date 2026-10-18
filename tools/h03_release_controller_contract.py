"""Contrato offline de controlador H-03, exclusivo del laboratorio.

No es un ejecutor de despliegue ni un control obligatorio de GitHub/Railway.
Los adaptadores de respaldo y publicación se inyectan; no hay red, secretos ni
acceso a producción. Cuando PR #18 se integre con autorización, el adaptador
fiable deberá invocar su preupdate_gate.guarded_update dentro del dueño de /data.
"""
from dataclasses import dataclass
import re
import uuid


class ReleaseContractBlocked(RuntimeError):
    """Motivo de bloqueo sin datos privados."""


@dataclass(frozen=True)
class ReleasePlan:
    environment: str
    source_revision: str
    target_revision: str
    request_id: str

    @classmethod
    def for_lab(cls, source_revision: str, target_revision: str):
        return cls("lab", source_revision, target_revision, uuid.uuid4().hex)


def _validate(plan: ReleasePlan) -> None:
    if not isinstance(plan, ReleasePlan) or plan.environment != "lab":
        raise ReleaseContractBlocked("laboratory_only")
    if (not re.fullmatch(r"[0-9a-f]{40}", plan.source_revision)
            or not re.fullmatch(r"[0-9a-f]{40}", plan.target_revision)
            or not re.fullmatch(r"[0-9a-f]{32}", plan.request_id)):
        raise ReleaseContractBlocked("invalid_revision_or_request")
    if plan.source_revision == plan.target_revision:
        raise ReleaseContractBlocked("same_revision")


def run_lab_contract(
    plan: ReleasePlan, *, read_live_revision, prepare_and_restore,
    guarded_update, publish_and_confirm,
) -> bool:
    """Probar en laboratorio la secuencia obligatoria, sin desplegar por sí sola.

    El adaptador real de guarded_update debe verificar y restaurar de nuevo el
    objeto externo y consumir una autorización durable antes del callback.
    El publicador debe bloquear hasta confirmar el resultado FINAL, no solo
    hasta recibir un ID o encolar un despliegue.

    Ninguna función de este módulo permite operar sobre producción.
    """
    _validate(plan)
    if not all(callable(fn) for fn in (
            read_live_revision, prepare_and_restore,
            guarded_update, publish_and_confirm)):
        raise ReleaseContractBlocked("missing_trusted_adapter")
    if read_live_revision() != plan.source_revision:
        raise ReleaseContractBlocked("source_revision_changed")
    if prepare_and_restore(plan) != "verified_and_restored":
        raise ReleaseContractBlocked("backup_not_verified")
    if read_live_revision() != plan.source_revision:
        raise ReleaseContractBlocked("source_revision_changed")

    callback_calls = 0

    def apply():
        nonlocal callback_calls
        callback_calls += 1
        if callback_calls != 1:
            raise ReleaseContractBlocked("callback_reused")
        if read_live_revision() != plan.source_revision:
            raise ReleaseContractBlocked("source_revision_changed")
        result = publish_and_confirm(plan)
        if result is not True:
            raise ReleaseContractBlocked("deployment_unconfirmed")
        if read_live_revision() != plan.target_revision:
            raise ReleaseContractBlocked("target_revision_unconfirmed")
        return True

    result = guarded_update(plan, apply)
    if result is not True or callback_calls != 1:
        raise ReleaseContractBlocked("guarded_update_unconfirmed")
    if read_live_revision() != plan.target_revision:
        raise ReleaseContractBlocked("target_revision_changed")
    return True
