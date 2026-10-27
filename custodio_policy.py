"""Autorización de observación por revisión y regla; solo metadatos en SQLite."""
from __future__ import annotations
from dataclasses import dataclass, field
import json
import re
from custodio_detection import KINDS

KEY = "custodio_observe_policy_v1"
MAX_BYTES = 16384


def ids(values):
    if (type(values) not in (list, tuple, set, frozenset) or len(values) > 25
            or any(type(x) is not int or not 0 < x < 2**63 for x in values)):
        raise ValueError("invalid_exempt_ids")
    return frozenset(values)


@dataclass(frozen=True)
class RuleBinding:
    number: int
    kinds: frozenset[str] = frozenset()
    roles: frozenset[int] = frozenset()
    channels: frozenset[int] = frozenset()


@dataclass(frozen=True)
class ObservePolicy:
    revision: str
    enabled: bool = False
    roles: frozenset[int] = frozenset()
    channels: frozenset[int] = frozenset()
    bindings: tuple[RuleBinding, ...] = ()

    def encode(self, rule_count: int) -> str:
        if not re.fullmatch(r"[a-f0-9]{64}", self.revision) or type(self.enabled) is not bool:
            raise ValueError("invalid_policy")
        ids(self.roles); ids(self.channels)
        if len(self.bindings) != rule_count or not 1 <= rule_count <= 16:
            raise ValueError("invalid_binding_count")
        for number, binding in enumerate(self.bindings, 1):
            if type(binding.number) is not int or binding.number != number or not binding.kinds <= KINDS:
                raise ValueError("invalid_rule_binding")
            ids(binding.roles); ids(binding.channels)
        raw = json.dumps({"version": 1, "revision": self.revision, "enabled": self.enabled,
            "roles": sorted(self.roles), "channels": sorted(self.channels),
            "bindings": [{"number": b.number, "kinds": sorted(b.kinds),
                          "roles": sorted(b.roles), "channels": sorted(b.channels)}
                         for b in self.bindings]}, separators=(",", ":"), sort_keys=True)
        if len(raw.encode()) > MAX_BYTES:
            raise ValueError("policy_size_limit")
        return raw

    @classmethod
    def empty(cls, snapshot):
        return cls(snapshot.revision, bindings=tuple(RuleBinding(n) for n in range(1, snapshot.count + 1)))

    @classmethod
    def decode(cls, raw, snapshot):
        try:
            if type(raw) is not str or len(raw.encode()) > MAX_BYTES:
                raise ValueError("invalid_policy")
            data = json.loads(raw)
            if (type(data) is not dict or data.get("version") != 1
                    or data.get("revision") != snapshot.revision
                    or type(data.get("enabled")) is not bool
                    or set(data) != {"version", "revision", "enabled", "roles", "channels", "bindings"}):
                raise ValueError("invalid_policy")
            bindings = tuple(RuleBinding(b["number"], frozenset(b["kinds"]), ids(b["roles"]), ids(b["channels"]))
                             for b in data["bindings"])
            policy = cls(data["revision"], data["enabled"], ids(data["roles"]), ids(data["channels"]), bindings)
            policy.encode(snapshot.count)
            return policy
        except (TypeError, ValueError, KeyError):
            return cls.empty(snapshot)

    @classmethod
    def rebase(cls,raw,snapshot):
        """Conservar interruptor y exenciones globales al aprobar una nueva revisión.

        Los enlaces por regla requieren la revisión exacta; no se transfieren
        por número a un texto que pudo cambiar de significado.
        """
        try:
            from types import SimpleNamespace
            data=json.loads(raw)
            previous=cls.decode(raw,SimpleNamespace(revision=data['revision'],count=len(data['bindings'])))
            if previous.encode(len(data['bindings'])) != raw:
                # Admitir serialización equivalente, pero no un documento reparado silenciosamente.
                if json.loads(previous.encode(len(data['bindings']))) != data:
                    raise ValueError('invalid_previous_policy')
            if previous.revision==snapshot.revision:
                return cls.decode(raw,snapshot)
            from dataclasses import replace
            return replace(cls.empty(snapshot),enabled=previous.enabled,roles=previous.roles,channels=previous.channels)
        except (TypeError,ValueError,KeyError,AttributeError):
            return cls.empty(snapshot)

    def eligible(self, *, role_ids, channel_id, owner=False, staff=False):
        return bool(self.enabled and not owner and not staff
                    and not self.roles.intersection(role_ids) and channel_id not in self.channels)

    def allowed_bindings(self, *, role_ids, channel_id):
        return tuple(b for b in self.bindings if b.kinds and not b.roles.intersection(role_ids)
                     and channel_id not in b.channels)
