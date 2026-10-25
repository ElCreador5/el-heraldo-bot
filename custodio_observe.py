"""Detección local y conservadora para el futuro modo Observar.

No escucha Discord, no consulta IA y no clasifica infracciones sin una regla
oficial aprobada que prohíba explícitamente el comportamiento observado.
"""
from __future__ import annotations
from dataclasses import dataclass
from collections import defaultdict, deque
from hashlib import sha256
import unicodedata

URL_PATTERN = re.compile(r"https?://[^\s<>]+", re.IGNORECASE)
MAX_TEXT = 4000
WINDOW_SECONDS = 90
REPEAT_MIN = 3
MAX_TRACKED_PATTERNS = 2048

@dataclass(frozen=True)
class Observation:
    guild_id: int
    channel_id: int
    actor_id: int
    message_id: int
    kind: str
    occurrences: int
    rule_number: int | None = None
    action: str = "report_only"

def normalize(text: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", text).casefold().split())

class ObserveBuffer:
    """Ventana temporal acotada; solo huellas, nunca contenido ni sanciones."""
    def __init__(self):
        self._events = defaultdict(deque)
        self._latest = {}

    def inspect(self, *, guild_id: int, channel_id: int, actor_id: int,
                message_id: int, timestamp: float, content: str,
                approved_rule_number: int | None = None) -> Observation | None:
        if (not all(type(v) is int and v > 0 for v in
                    (guild_id, channel_id, actor_id, message_id))
                or not isinstance(timestamp, (int, float)) or timestamp < 0):
            raise ValueError("invalid_observation")
        if not isinstance(content, str) or len(content) > MAX_TEXT:
            return None
        normalized = normalize(content)
        if len(normalized) < 8:
            return None
        # Reglas obligatorias: no asociar observaciones a una norma inventada.
        if approved_rule_number is None:
            return None
        if type(approved_rule_number) is not int or approved_rule_number < 1:
            raise ValueError("invalid_rule_number")
        fingerprint = sha256(normalized.encode("utf-8")).digest()
        key = (guild_id, actor_id, fingerprint)
        if key not in self._events and len(self._events) >= MAX_TRACKED_PATTERNS:
            # Cota de memoria: descartar el patrón menos reciente.
            oldest = min(self._latest, key=self._latest.get)
            self._events.pop(oldest, None)
            self._latest.pop(oldest, None)
        events = self._events[key]
        while events and events[0][0] < timestamp - WINDOW_SECONDS:
            events.popleft()
        if any(mid == message_id for _, mid in events):
            return None
        events.append((timestamp, message_id))
        self._latest[key] = timestamp
        # Evidencia mecánica, no prueba por sí sola de una infracción.
        if len(events) == REPEAT_MIN:
            return Observation(guild_id, channel_id, actor_id, message_id,
                               "identical_text_repetition", len(events),
                               approved_rule_number)
        return None
