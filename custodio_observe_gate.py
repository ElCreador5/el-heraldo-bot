"""Puerta segura de observación: ninguna regla se presupone aprobada.

Este componente no escucha mensajes ni envía reportes; exige una regla
verificada y una aprobación explícita de su revisión por el administrador.
"""
from __future__ import annotations
from dataclasses import dataclass
from custodio_core import RulesSnapshot
from custodio_observe import ObserveBuffer, Observation

@dataclass(frozen=True)
class ObserveAuthorization:
    guild_id: int
    approved_revision: str
    approved_rule_numbers: frozenset[int]
    enabled: bool = False

def evaluate_observation(
    detector: ObserveBuffer,
    snapshot: RulesSnapshot,
    authorization: ObserveAuthorization | None,
    *,
    rule_number: int,
    channel_id: int,
    actor_id: int,
    message_id: int,
    timestamp: float,
    content: str,
    exempt: bool = False,
) -> Observation | None:
    """Sin revisión aprobada, autorización o regla concreta: no detectar."""
    if (authorization is None or not authorization.enabled or exempt
            or authorization.guild_id != snapshot.guild_id
            or authorization.approved_revision != snapshot.revision
            or type(rule_number) is not int
            or not 1 <= rule_number <= snapshot.count
            or rule_number not in authorization.approved_rule_numbers):
        return None
    return detector.inspect(
        guild_id=snapshot.guild_id, channel_id=channel_id,
        actor_id=actor_id, message_id=message_id, timestamp=timestamp,
        content=content, approved_rule_number=rule_number,
    )
