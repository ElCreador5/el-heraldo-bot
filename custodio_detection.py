"""Detección mecánica acotada. No interpreta normas ni ejecuta medidas.

Solo devuelve indicadores elegidos por un administrador para una regla real.
Conserva huellas temporales; nunca transcripciones o perfiles de miembros.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from hashlib import blake2b, sha256
import math
import re
import unicodedata

KINDS = frozenset({"repeat", "similar_text", "links", "mentions", "flood",
                   "cross_channel", "images", "similar_images", "coordinated", "advertising"})
KIND_KEYS = {
    "repeat": "text.custodio.kind.repeat", "similar_text": "text.custodio.kind.similar_text",
    "links": "text.custodio.kind.links", "mentions": "text.custodio.kind.mentions",
    "flood": "text.custodio.kind.flood", "cross_channel": "text.custodio.kind.cross_channel",
    "images": "text.custodio.kind.images", "similar_images": "text.custodio.kind.similar_images",
    "coordinated": "text.custodio.kind.coordinated",
    "advertising": "text.custodio.kind.advertising",
}
WINDOW = 90.0
MAX_EVENTS = 4096
MAX_MESSAGE_CHARS = 4000


def normalize(text: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", text).casefold().split())


def text_sketch(text: str) -> int | None:
    words = [word for word in re.findall(r"\w+", text)[:512] if not word.isdecimal()]
    if len(set(words)) < 5:
        return None
    weights = [0] * 64
    for word in set(words):
        digest = int.from_bytes(blake2b(word.encode(), digest_size=8).digest(), "big")
        for bit in range(64):
            weights[bit] += 1 if digest & (1 << bit) else -1
    return sum(1 << bit for bit, weight in enumerate(weights) if weight > 0)


@dataclass(frozen=True)
class MessageSignal:
    guild_id: int
    channel_id: int
    actor_id: int
    message_id: int
    at: float
    exact: bytes | None
    sketch: int | None
    length: int
    links: frozenset[bytes]
    mentions: int
    images: tuple[tuple[str, int | None], ...] = ()
    rule_number: int = 0


@dataclass(frozen=True)
class Detection:
    kind: str
    occurrences: int
    message_ids: tuple[int, ...]
    coordinated: bool = False


class LocalDetector:
    """Ventana acotada y reloj monotónico, independiente de la hora del miembro."""
    def __init__(self, *, capacity: int = MAX_EVENTS):
        if type(capacity) is not int or not 8 <= capacity <= MAX_EVENTS:
            raise ValueError("invalid_capacity")
        self.capacity = capacity
        self.events: deque[MessageSignal] = deque(maxlen=capacity)
        self.latest = 0.0

    def expire(self, now: float) -> None:
        if not math.isfinite(now) or now < self.latest:
            raise ValueError("invalid_monotonic_time")
        self.latest = now
        while self.events and self.events[0].at < now - WINDOW:
            self.events.popleft()

    def clear_guild(self, guild_id):
        self.events = deque((event for event in self.events if event.guild_id != guild_id), maxlen=self.capacity)

    def inspect(self, *, guild_id: int, channel_id: int, actor_id: int,
                message_id: int, now: float, content: str,
                kinds: frozenset[str], mention_count: int = 0,
                images: tuple[tuple[str, int | None], ...] = (),
                sensitivity: str = "balanced", rule_number: int = 0) -> tuple[Detection, ...]:
        if (not all(type(v) is int and v > 0 for v in
                    (guild_id, channel_id, actor_id, message_id))
                or type(now) not in (int, float) or isinstance(now, bool)
                or not isinstance(content, str) or len(content) > MAX_MESSAGE_CHARS
                or not kinds <= KINDS or type(mention_count) is not int or mention_count < 0
                or sensitivity not in {"conservative", "balanced", "strict"}
                or type(rule_number) is not int or not 0 <= rule_number <= 16
                or len(images) > 4 or any(not re.fullmatch(r"[0-9a-f]{64}", h)
                      or (p is not None and (type(p) is not int or not 0 <= p < 2**64))
                      for h, p in images)):
            raise ValueError("invalid_signal")
        self.expire(float(now))
        if any(e.guild_id == guild_id and e.message_id == message_id
               and e.rule_number == rule_number for e in self.events):
            return ()
        text = normalize(content)
        digest = sha256(text.encode()).digest() if len(text) >= 12 else None
        previous = self.events[-1] if self.events else None
        shared_fingerprint = bool(previous and digest is not None
            and (previous.guild_id, previous.channel_id, previous.actor_id, previous.message_id, previous.exact)
                == (guild_id, channel_id, actor_id, message_id, digest))
        signal = MessageSignal(
            guild_id, channel_id, actor_id, message_id, float(now),
            digest,
            previous.sketch if shared_fingerprint else text_sketch(text) if len(text) >= 32 else None,
            len(text),
            previous.links if shared_fingerprint else frozenset(sha256(link.rstrip(".,!?)").encode()).digest()
                      for link in re.findall(r"(?:https?://|discord\.gg/|discord\.com/invite/)[^\s<>]+", text)[:20]),
            mention_count, images, rule_number,
        )
        self.events.append(signal)
        applicable = [e for e in self.events if e.guild_id == guild_id and e.rule_number == rule_number]
        own = [e for e in applicable if e.actor_id == actor_id]
        channel = [e for e in applicable if e.channel_id == channel_id]
        threshold = {"conservative": 4, "balanced": 3, "strict": 3}[sensitivity]
        result = []

        def add(kind, matches, minimum=threshold, coordinated=False):
            # Solo un aviso al cruzar el umbral; no repetirlo en cada mensaje.
            if kind in kinds and len(matches) == minimum and signal in matches:
                result.append(Detection(kind, len(matches), tuple(e.message_id for e in matches), coordinated))

        exact = [e for e in own if signal.exact is not None and e.exact == signal.exact]
        add("repeat", exact)
        similar = [e for e in own if signal.sketch is not None and e.sketch is not None
                   and min(e.length, signal.length) / max(e.length, signal.length) >= .8
                   and (e.sketch ^ signal.sketch).bit_count() <= 4]
        if not any(d.kind == "repeat" for d in result):
            add("similar_text", similar)
        if signal.links:
            add("links", [e for e in own if signal.links & e.links])
        if ("advertising" in kinds and signal.links and re.search(
                r"\b(?:buy|subscribe|giveaway|sale|oferta|compra|compre|suscríbete|suscribete|inscreva|promoção|promoción)\b", text)):
            result.append(Detection("advertising", 1, (message_id,)))
        if "mentions" in kinds and mention_count >= 8:
            result.append(Detection("mentions", mention_count, (message_id,)))
        recent = [e for e in own if e.channel_id == channel_id and e.at >= now - 8]
        # Un canal concurrido eleva el umbral: conversar normalmente no es spam.
        others = len({e.actor_id for e in channel if e.at >= now - 8})
        add("flood", recent, max(8, others * 3))
        if len({e.channel_id for e in exact}) >= 3:
            add("cross_channel", exact)
        same_images = [e for e in own if any(h == other for h, _ in images for other, _ in e.images)]
        add("images", same_images)
        near_images = [e for e in own if any(p is not None and q is not None
                        and (p ^ q).bit_count() <= 3 for _, p in images for _, q in e.images)]
        if not any(d.kind == "images" for d in result):
            add("similar_images", near_images)
        campaign = [e for e in applicable if signal.exact is not None and e.exact == signal.exact]
        if len({e.actor_id for e in campaign}) >= 3 and len(exact) >= 2:
            # Nunca atribuir la actividad ajena a un miembro con una sola entrada.
            add("coordinated", campaign, 6, coordinated=True)
        return tuple(result)


def image_fingerprint(data: bytes) -> tuple[str, int | None]:
    """Hash exacto siempre; dHash opcional, acotado, sin archivos temporales."""
    if not isinstance(data, bytes) or not 0 < len(data) <= 1024 * 1024:
        raise ValueError("image_size_limit")
    exact = sha256(data).hexdigest()
    try:
        from PIL import Image, ImageOps
        import io
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(data)) as image:
                if image.width * image.height > 4_000_000 or getattr(image, "n_frames", 1) != 1:
                    return exact, None
                with ImageOps.exif_transpose(image).convert("L").resize((9, 8)) as gray:
                    pixels = list(gray.getdata())
                    bits = [pixels[y * 9 + x] > pixels[y * 9 + x + 1]
                            for y in range(8) for x in range(8)]
                    sketch = sum(1 << bit for bit, on in enumerate(bits) if on)
                    return exact, sketch if 3 <= sketch.bit_count() <= 61 else None
    except Exception:
        # Un decoder desconocido nunca debe derribar la supervisión.
        return exact, None
