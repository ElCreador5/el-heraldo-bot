"""Visible, rate-limited status updates for long-running Discord operations.

The operation itself stays independent from presentation. A failed edit never
turns a successful moderation action into a retry of that action.
"""
from __future__ import annotations

import time
import discord


STATUS_TEXT = {
    "es-419": {
        "heading": "Estado de la operación",
        "scan": "Revisando mensajes…\nCanales revisados: {channels}/{total} · Mensajes examinados: {examined} · Coincidencias: {found}",
        "delete": "Eliminando mensajes…\nProcesados: {processed}/{total} · Eliminados: {deleted} · Fallidos: {failed}",
        "scan_failed": "La revisión se interrumpió. No se eliminaron mensajes.",
        "delete_failed": "La eliminación se interrumpió. Comprueba el resultado parcial y el registro.",
        "remaining": "Sin procesar: {count}.",
        "interrupted": "Operación interrumpida",
        "purge_scan_title": "Purga · Revisando mensajes",
        "purge_scan_count": "{done} / {total} canales revisados",
        "purge_scan_unknown": "{done} canales revisados",
        "purge_scan_metrics": "{examined} examinados · {found} coincidencias",
        "purge_delete_title": "Purga · Eliminando mensajes",
        "purge_delete_count": "{done} / {total} mensajes procesados",
        "purge_delete_unknown": "{done} mensajes procesados",
        "purge_delete_metrics": "{deleted} eliminados · {failed} fallidos",
        "fusion_title": "Fusión · Migrando mensajes",
        "fusion_count": "{done} / {total} mensajes procesados",
        "fusion_unknown": "{done} mensajes procesados",
        "fusion_metrics": "{migrated} migrados · {failed} fallidos · {attachments} adjuntos fallidos",
        "join_roles_title": "Sincronizando roles de ingreso",
        "join_roles_count": "{done} / {total} miembros revisados",
        "join_roles_unknown": "{done} miembros revisados",
        "join_roles_metrics": "{assigned} asignados · {skipped} omitidos · {failed} errores",
        "verification_title": "Revisando verificaciones",
        "verification_count": "{done} / {total} miembros revisados",
        "verification_unknown": "{done} miembros revisados",
        "verification_metrics": "{verified} verificados · {expelled} expulsados · {failed} errores",
        "template_running": "**Plantilla del servidor**\nSincronizando con Discord…",
    },
    "en-US": {
        "heading": "Operation status",
        "scan": "Reviewing messages…\nChannels reviewed: {channels}/{total} · Messages examined: {examined} · Matches: {found}",
        "delete": "Deleting messages…\nProcessed: {processed}/{total} · Deleted: {deleted} · Failed: {failed}",
        "scan_failed": "The review was interrupted. No messages were deleted.",
        "delete_failed": "Deletion was interrupted. Check the partial result and the audit log.",
        "remaining": "Not processed: {count}.",
        "interrupted": "Operation interrupted",
        "purge_scan_title": "Purge · Reviewing messages",
        "purge_scan_count": "{done} / {total} channels reviewed",
        "purge_scan_unknown": "{done} channels reviewed",
        "purge_scan_metrics": "{examined} examined · {found} matches",
        "purge_delete_title": "Purge · Deleting messages",
        "purge_delete_count": "{done} / {total} messages processed",
        "purge_delete_unknown": "{done} messages processed",
        "purge_delete_metrics": "{deleted} deleted · {failed} failed",
        "fusion_title": "Channel merge · Migrating messages",
        "fusion_count": "{done} / {total} messages processed",
        "fusion_unknown": "{done} messages processed",
        "fusion_metrics": "{migrated} migrated · {failed} failed · {attachments} failed attachments",
        "join_roles_title": "Syncing entry roles",
        "join_roles_count": "{done} / {total} members reviewed",
        "join_roles_unknown": "{done} members reviewed",
        "join_roles_metrics": "{assigned} assigned · {skipped} skipped · {failed} errors",
        "verification_title": "Reviewing verifications",
        "verification_count": "{done} / {total} members reviewed",
        "verification_unknown": "{done} members reviewed",
        "verification_metrics": "{verified} verified · {expelled} expelled · {failed} errors",
        "template_running": "**Server template**\nSyncing with Discord…",
    },
    "pt-BR": {
        "heading": "Status da operação",
        "scan": "Analisando mensagens…\nCanais analisados: {channels}/{total} · Mensagens examinadas: {examined} · Correspondências: {found}",
        "delete": "Excluindo mensagens…\nProcessadas: {processed}/{total} · Excluídas: {deleted} · Falhas: {failed}",
        "scan_failed": "A análise foi interrompida. Nenhuma mensagem foi excluída.",
        "delete_failed": "A exclusão foi interrompida. Confira o resultado parcial e o registro.",
        "remaining": "Não processadas: {count}.",
        "interrupted": "Operação interrompida",
        "purge_scan_title": "Limpeza · Analisando mensagens",
        "purge_scan_count": "{done} / {total} canais analisados",
        "purge_scan_unknown": "{done} canais analisados",
        "purge_scan_metrics": "{examined} analisadas · {found} correspondências",
        "purge_delete_title": "Limpeza · Excluindo mensagens",
        "purge_delete_count": "{done} / {total} mensagens processadas",
        "purge_delete_unknown": "{done} mensagens processadas",
        "purge_delete_metrics": "{deleted} excluídas · {failed} falhas",
        "fusion_title": "Fusão · Migrando mensagens",
        "fusion_count": "{done} / {total} mensagens processadas",
        "fusion_unknown": "{done} mensagens processadas",
        "fusion_metrics": "{migrated} migradas · {failed} falhas · {attachments} anexos com falha",
        "join_roles_title": "Sincronizando cargos de entrada",
        "join_roles_count": "{done} / {total} membros analisados",
        "join_roles_unknown": "{done} membros analisados",
        "join_roles_metrics": "{assigned} atribuídos · {skipped} ignorados · {failed} erros",
        "verification_title": "Analisando verificações",
        "verification_count": "{done} / {total} membros analisados",
        "verification_unknown": "{done} membros analisados",
        "verification_metrics": "{verified} verificados · {expelled} expulsos · {failed} erros",
        "template_running": "**Modelo do servidor**\nSincronizando com o Discord…",
    },
}


def status_text(locale: str, key: str, **values) -> str:
    catalog = STATUS_TEXT.get(locale, STATUS_TEXT["es-419"])
    return catalog[key].format(**values)


def progress_bar(checked: int, total: int | None = None, *,
                 complete: bool = False, width: int = 16) -> tuple[str, int | None]:
    """Text-only Discord progress indicator.

    Guild.member_count is an estimate, not a verified fetch total. Do not
    announce 100% before completion. When the estimate is missing or stale,
    use an indeterminate activity indicator without claiming a percentage.
    """
    width = max(6, min(24, int(width)))
    checked = max(0, int(checked))
    if complete:
        return "`" + "█" * width + "`", 100
    if not isinstance(total, int) or isinstance(total, bool) or total <= 0 or checked > total:
        pulse = 3
        offset = (checked // 20) % (width - pulse + 1)
        bar = "░" * offset + "█" * pulse + "░" * (width - pulse - offset)
        return "`" + bar + "`", None
    percent = min(99, checked * 100 // total)
    filled = min(width - 1, checked * width // total)
    return "`" + "█" * filled + "░" * (width - filled) + "`", percent



def compact_progress_bar(checked: int, total: int | None) -> tuple[str, int | None]:
    """Ten-character Discord text bar; no percentage for an unreliable total.

    The cached guild member count is approximate, so 100% is reserved for
    the final result rather than the running progress panel.
    """
    width = 10
    checked = max(0, int(checked))
    valid = (isinstance(total, int) and not isinstance(total, bool)
             and total > 0 and checked <= total)
    if not valid:
        offset = (checked // 20) % width
        return "`" + "·" * offset + "▌" + "·" * (width - offset - 1) + "`", None
    percent = min(99, checked * 100 // total)
    full = min(width - 1, checked * width // total)
    fractional = (checked * width) % total > 0
    half = 1 if fractional and full < width else 0
    bar = "█" * full + "▌" * half + "·" * (width - full - half)
    return f"`{bar}`", percent


def compact_operation_status(locale: str, action: str, done: int,
                             total: int | None, **counters: int) -> str:
    """Five-line, context-specific status with an honest ten-cell progress bar."""
    if action not in {"purge_scan", "purge_delete", "fusion", "join_roles", "verification"}:
        raise ValueError("unsupported_progress_action")
    bar, percent = compact_progress_bar(done, total)
    title = status_text(locale, action + "_title")
    label = (status_text(locale, action + "_count", done=done, total=total)
             if percent is not None
             else status_text(locale, action + "_unknown", done=done))
    metrics = status_text(locale, action + "_metrics", **counters)
    return f"**{title}**\\n{bar}{f' **{percent}%**' if percent is not None else ''}\\n{label}\\n{metrics}"


class ProgressReporter:
    """Updates an existing panel at most once per interval (unless forced)."""

    def __init__(self, edit, *, interval: float = 2.5):
        self.edit = edit
        self.interval = interval
        self.last_at = float("-inf")
        self.last_content = None

    async def publish(self, content: str, *, force: bool = False) -> bool:
        now = time.monotonic()
        if not force and (now - self.last_at < self.interval or content == self.last_content):
            return False
        self.last_at = now
        try:
            await self.edit(content)
        except discord.HTTPException as exc:
            print(f"OPERATION_PROGRESS status=UI_EDIT_FAILED error={type(exc).__name__}", flush=True)
            return False
        self.last_content = content
        return True
