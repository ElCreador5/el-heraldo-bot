"""NH: evidencia literal reutilizable, sin base de datos ni envíos automáticos.

El informe de Discord es una copia explícita en un canal privado; el vínculo
solo se agrega si el mensaje original fue verificado como disponible.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
import discord

@dataclass(frozen=True)
class LiteralEvidence:
    actor: str
    guild: str
    channel: str
    occurred_at: datetime
    verbatim: str
    rule_quote: str | None = None
    rule_number: int | None = None
    conduct: str = "Conducta pendiente de revisión"
    outcome: str = "Solo reportar"
    original_url: str | None = None
    original_exists: bool = False

    def __post_init__(self):
        if self.occurred_at.tzinfo is None:
            raise ValueError("timestamp_requires_timezone")
        if not isinstance(self.verbatim, str) or not self.verbatim:
            raise ValueError("verbatim_required")
        if self.rule_number is not None and (type(self.rule_number) is not int or self.rule_number < 1):
            raise ValueError("invalid_rule_number")
        if bool(self.rule_quote) != (self.rule_number is not None):
            raise ValueError("rule_quote_and_number_required_together")

def discord_local_timestamp(moment: datetime) -> str:
    """Fecha completa que Discord presenta en la zona horaria del lector."""
    if moment.tzinfo is None:
        raise ValueError("timestamp_requires_timezone")
    return f"<t:{int(moment.timestamp())}:F>"


def make_evidence_embeds(evidence: LiteralEvidence, *, footer: str, icon_url: str | None = None):
    """Trocea citas extensas sin presentar fragmentos truncados como completos.

    Se limita la transcripción por lote a evitar spam; si excede el límite,
    no se publica una representación incompleta como evidencia literal.
    """
    text = evidence.verbatim
    if len(text) > 7200:
        raise ValueError("evidence_too_long_for_single_report")
    chunks = [text[i:i+900] for i in range(0, len(text), 900)]
    rule = evidence.rule_quote or ""
    if len(rule) > 2000:
        raise ValueError("rule_quote_too_long")
    parts = [rule[i:i+900] for i in range(0, len(rule), 900)] if rule else []
    if len(chunks) + len(parts) > 10:
        raise ValueError("report_exceeds_embed_limits")
    embeds = []
    stamp = evidence.occurred_at.astimezone(timezone.utc)
    for index, chunk in enumerate(chunks):
        item = discord.Embed(
            title="El Heraldo · Evidencia" if index == 0 else f"Evidencia · Parte {index+1}/{len(chunks)}",
            description="Registro literal para revisión; no constituye prueba concluyente.",
            color=discord.Color.orange(), timestamp=stamp,
        )
        if index == 0:
            item.add_field(name="Miembro", value=evidence.actor[:1024], inline=True)
            item.add_field(name="Servidor y canal", value=f"{evidence.guild} · {evidence.channel}"[:1024], inline=True)
            item.add_field(name="Fecha y hora", value=discord_local_timestamp(evidence.occurred_at), inline=False)
            item.add_field(name="Conducta", value=evidence.conduct[:1024], inline=False)
            item.add_field(name="Resultado", value=evidence.outcome[:1024], inline=False)
        # Discord embeds no enlazan dinámicamente un campo sin volver a editarlo.
        # La transcripción siempre es visible, exista o no el mensaje original.
        displayed = chunk
        if evidence.original_exists and evidence.original_url and index == 0:
            item.add_field(name="Original disponible", value=evidence.original_url[:1024], inline=False)
        item.add_field(name=f"Transcripción literal · {index+1}/{len(chunks)}", value=displayed, inline=False)
        item.set_footer(text=footer, icon_url=icon_url or None)
        embeds.append(item)
    for index, fragment in enumerate(parts):
        item = discord.Embed(title="Regla oficial citada literalmente", color=discord.Color.orange(), timestamp=stamp)
        item.add_field(name=f"Regla {evidence.rule_number} · Parte {index+1}/{len(parts)}", value=fragment, inline=False)
        item.set_footer(text=footer, icon_url=icon_url or None)
        embeds.append(item)
    return embeds
