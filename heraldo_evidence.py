"""NH: evidencia literal reutilizable, sin base de datos ni envíos automáticos.

El informe de Discord es una copia explícita en un canal privado; el vínculo
solo se agrega si el mensaje original fue verificado como disponible.
"""
from __future__ import annotations
from heraldo_i18n import text as _t, guild_context as _i18n_context, use_guild as _i18n_guild
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
    conduct: str = _t('text.5f7cc9faf6c801')
    outcome: str = _t('text.fb57b92cfc0723')
    original_url: str | None = None
    original_exists: bool = False
    verbatim_is_description: bool = False

    @_i18n_context
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
    if len(text) > 32000:
        raise ValueError("evidence_too_long_for_single_report")
    chunks = [text[i:i+900] for i in range(0, len(text), 900)]
    rule = evidence.rule_quote or ""
    if len(rule) > 2048:
        raise ValueError("rule_quote_too_long")
    parts = [rule[i:i+900] for i in range(0, len(rule), 900)] if rule else []
    embeds = []
    stamp = evidence.occurred_at.astimezone(timezone.utc)
    for index, chunk in enumerate(chunks):
        item = discord.Embed(
            title=_t('text.ddee76accf5041') if index == 0 else _t('text.325a947cbeea43', p0=f'{index + 1}', p1=f'{len(chunks)}'),
            description=_t('text.46f21fb5b47836'),
            color=discord.Color.orange(), timestamp=stamp,
        )
        if index == 0:
            item.add_field(name=_t('text.e841f8bfd02f85'), value=evidence.actor[:1024], inline=True)
            item.add_field(name=_t('text.cb99a42f984137'), value=f"{evidence.guild} · {evidence.channel}"[:1024], inline=True)
            item.add_field(name=_t('text.b0bddd1a69b779'), value=discord_local_timestamp(evidence.occurred_at), inline=False)
            item.add_field(name=_t('text.0c46011974c95e'), value=evidence.conduct[:1024], inline=False)
            item.add_field(name=_t('text.a71bc39fe3f33e'), value=evidence.outcome[:1024], inline=False)
        # Discord embeds no enlazan dinámicamente un campo sin volver a editarlo.
        # La transcripción siempre es visible, exista o no el mensaje original.
        displayed = chunk
        if evidence.original_exists and evidence.original_url and index == 0:
            item.add_field(name=_t('text.a376d1351c3f23'), value=evidence.original_url[:1024], inline=False)
        caption = (_t('text.custodio.action_description', part=index + 1, total=len(chunks))
                   if evidence.verbatim_is_description else
                   _t('text.ed432ad50b8d94', p0=f'{index + 1}', p1=f'{len(chunks)}'))
        item.add_field(name=caption, value=displayed, inline=False)
        item.set_footer(text=footer, icon_url=icon_url or None)
        embeds.append(item)
    for index, fragment in enumerate(parts):
        item = discord.Embed(title=_t('text.6bbb7c3704b1b8'), color=discord.Color.orange(), timestamp=stamp)
        item.add_field(name=_t('text.b9ea7f24caa539', p0=f'{evidence.rule_number}', p1=f'{index + 1}', p2=f'{len(parts)}'), value=fragment, inline=False)
        item.set_footer(text=footer, icon_url=icon_url or None)
        embeds.append(item)
    return embeds


def evidence_batches(embeds):
    """Preserva todas las partes respetando 6000 caracteres y diez embeds/envío."""
    batches, batch, size = [], [], 0
    for item in embeds:
        if len(item) > 6000:
            raise ValueError("evidence_embed_too_large")
        if batch and (len(batch) == 10 or size + len(item) > 6000):
            batches.append(batch)
            batch, size = [], 0
        batch.append(item)
        size += len(item)
    if batch:
        batches.append(batch)
    return batches
