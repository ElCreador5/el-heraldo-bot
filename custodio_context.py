"""Contexto por servidor/canal para Custodio. Sin acceso a mensajes ni contenido NSFW.

Un marcador de edad no modifica ni sustituye las Server Rules aprobadas.
Discord Guild NSFW: 0=indeterminado, 1=explicit, 2=safe, 3=age_restricted.
"""
from __future__ import annotations
from heraldo_i18n import text as _t, guild_context as _i18n_context, use_guild as _i18n_guild

from dataclasses import dataclass
from enum import Enum
from typing import Any

AGE_LEVELS = {0: "unknown", 1: "age_restricted", 2: "sfw", 3: "age_restricted"}


def age_value(raw: Any) -> int | None:
    value = getattr(raw, "value", raw)
    if type(value) is int and value in AGE_LEVELS:
        return value
    return None


@dataclass(frozen=True)
class CommunityContext:
    guild_id: int
    channel_id: int
    guild_classification: str
    channel_classification: str
    effective_classification: str
    rules_revision: str | None
    rules_approved: bool

    @property
    @_i18n_context
    def can_evaluate(self) -> bool:
        return bool(self.rules_revision and self.rules_approved)


@_i18n_context
def classify_community(
    guild_id: int, channel_id: int,
    guild_nsfw_level: Any, channel_is_nsfw: bool | None,
    rules_revision: str | None, approved_revision: str | None,
) -> CommunityContext:
    """Diferencia ámbitos sin presumir edades, permisos o contenido permitido."""
    if type(guild_id) is not int or type(channel_id) is not int or guild_id <= 0 or channel_id <= 0:
        raise ValueError("invalid_guild_or_channel")
    level = age_value(guild_nsfw_level)
    guild_classification = AGE_LEVELS.get(level, "unknown")
    if type(channel_is_nsfw) is bool:
        channel_classification = "age_restricted" if channel_is_nsfw else "sfw"
    else:
        channel_classification = "unknown"
    if guild_classification == "age_restricted" or channel_classification == "age_restricted":
        effective = "age_restricted"
    elif guild_classification == "sfw" and channel_classification == "sfw":
        effective = "sfw"
    else:
        effective = "unknown"
    return CommunityContext(
        guild_id=guild_id, channel_id=channel_id,
        guild_classification=guild_classification,
        channel_classification=channel_classification,
        effective_classification=effective,
        rules_revision=rules_revision,
        rules_approved=bool(rules_revision and approved_revision and rules_revision == approved_revision),
    )


def may_collect_evidence(context: CommunityContext, is_accessible: bool, is_excluded: bool) -> bool:
    """Solo metadatos de mensajes en canales autorizados y reglas vigentes."""
    return bool(context.can_evaluate and is_accessible and not is_excluded)


PUBLIC_NETWORKS = (
    {
        "name": _t('text.eb0050f72303bc'),
        "role": _t('text.d9ed49787a687f'),
        "source": "https://redditinc.com/policies/data-api-terms",
        "training": "not_authorized",
    },
    {
        "name": "X",
        "role": _t('text.5925eccab1dffa'),
        "source": _t('text.3e344b07d5ed24'),
        "training": "not_authorized",
    },
    {
        "name": _t('text.bad57ef7837c8e'),
        "role": _t('text.81df47bd1eed5c'),
        "source": "https://www.facebook.com/legal/automated_data_collection_terms",
        "training": "not_authorized",
    },
)
