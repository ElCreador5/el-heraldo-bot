"""H-03: adaptador de publicación comprobable sin acceso implícito a proveedores.

IMPORTANTE: sólo laboratorio. No es un publicador real ni puede mantener un
callback vivo durante un reinicio de Railway; aún falta el puente de dos fases
propietario del volumen. Los proveedores se inyectan y se prueban sin red.
"""
from dataclasses import dataclass
import re


class ReleaseBlocked(RuntimeError):
    """Código operativo seguro, sin identificadores de cuentas ni secretos."""


_SHA = re.compile(r"[0-9a-f]{40}\Z")
_REQUEST = re.compile(r"[0-9a-f]{32}\Z")
_DEPLOYMENT = re.compile(r"[A-Za-z0-9_-]{1,128}\Z")


@dataclass(frozen=True)
class ReleasePlan:
    environment: str
    source_revision: str
    target_revision: str
    request_id: str

    def validate_for_lab(self):
        if self.environment != "lab":
            raise ReleaseBlocked("laboratory_only")
        if (not isinstance(self.source_revision, str) or not _SHA.fullmatch(self.source_revision)
                or not isinstance(self.target_revision, str) or not _SHA.fullmatch(self.target_revision)
                or self.source_revision == self.target_revision
                or not isinstance(self.request_id, str) or not _REQUEST.fullmatch(self.request_id)):
            raise ReleaseBlocked("invalid_release_identity")


def run_lab_release(plan: ReleasePlan, *, read_source_revision,
                    target_approved, prepare_and_restore,
                    guarded_update, publish_exact, confirm_final_deployment,
                    read_running_revision) -> bool:
    """Contrato síncrono de publicación con validación de resultado FINAL.

    guarded_update tiene que reservar un permiso durable de un solo uso;
    no basta con simularlo mediante un callback. Un despliegue interrumpido
    exige reconciliación y nunca un segundo intento ciego.
    """
    if not isinstance(plan, ReleasePlan):
        raise ReleaseBlocked("invalid_plan")
    plan.validate_for_lab()
    handlers = (read_source_revision, target_approved, prepare_and_restore,
                guarded_update, publish_exact, confirm_final_deployment,
                read_running_revision)
    if not all(callable(x) for x in handlers):
        raise ReleaseBlocked("missing_trusted_adapter")
    if read_source_revision() != plan.source_revision:
        raise ReleaseBlocked("source_revision_changed")
    if target_approved(plan) is not True:
        raise ReleaseBlocked("target_not_approved")
    if prepare_and_restore(plan) != "verified_and_restored":
        raise ReleaseBlocked("backup_not_verified")
    if read_source_revision() != plan.source_revision:
        raise ReleaseBlocked("source_revision_changed")
    callback_count = 0

    def callback():
        nonlocal callback_count
        callback_count += 1
        if callback_count != 1:
            raise ReleaseBlocked("callback_reused")
        if read_source_revision() != plan.source_revision:
            raise ReleaseBlocked("source_revision_changed")
        if target_approved(plan) is not True:
            raise ReleaseBlocked("target_not_approved")
        deployment_id = publish_exact(plan)
        if (not isinstance(deployment_id, str)
                or not _DEPLOYMENT.fullmatch(deployment_id)):
            raise ReleaseBlocked("deployment_unconfirmed")
        if confirm_final_deployment(plan, deployment_id) is not True:
            raise ReleaseBlocked("deployment_unconfirmed")
        if read_running_revision() != plan.target_revision:
            raise ReleaseBlocked("running_revision_mismatch")
        return True

    if guarded_update(plan, callback) is not True or callback_count != 1:
        raise ReleaseBlocked("guarded_update_unconfirmed")
    if read_running_revision() != plan.target_revision:
        raise ReleaseBlocked("running_revision_changed")
    return True
