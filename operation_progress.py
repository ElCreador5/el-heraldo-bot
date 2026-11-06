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
    },
    "en-US": {
        "heading": "Operation status",
        "scan": "Reviewing messages…\nChannels reviewed: {channels}/{total} · Messages examined: {examined} · Matches: {found}",
        "delete": "Deleting messages…\nProcessed: {processed}/{total} · Deleted: {deleted} · Failed: {failed}",
        "scan_failed": "The review was interrupted. No messages were deleted.",
        "delete_failed": "Deletion was interrupted. Check the partial result and the audit log.",
        "remaining": "Not processed: {count}.",
        "interrupted": "Operation interrupted",
    },
    "pt-BR": {
        "heading": "Status da operação",
        "scan": "Analisando mensagens…\nCanais analisados: {channels}/{total} · Mensagens examinadas: {examined} · Correspondências: {found}",
        "delete": "Excluindo mensagens…\nProcessadas: {processed}/{total} · Excluídas: {deleted} · Falhas: {failed}",
        "scan_failed": "A análise foi interrompida. Nenhuma mensagem foi excluída.",
        "delete_failed": "A exclusão foi interrompida. Confira o resultado parcial e o registro.",
        "remaining": "Não processadas: {count}.",
        "interrupted": "Operação interrompida",
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
