"""Interpretaciones revisables: datos ligados a una regla, nunca autorización de sanción."""
from __future__ import annotations
from dataclasses import asdict, dataclass, replace
from hashlib import sha256
import json
import re
import time

from custodio_taxonomy import BEHAVIORS, TAXONOMY_VERSION, fold, grounded_category

KEY = "custodio_interpretation_v1"
MAX_BYTES = 131072
STATES = frozenset({"watchable", "partial", "clarification", "unsupported", "no_prohibition",
                    "contradiction", "disabled", "unavailable"})
NORMATIVE = frozenset({"prohibition", "restriction", "obligation", "permission", "none", "ambiguous"})
CORRECTIONS = frozenset({'incorrect','allowed','exception','false_positive','ambiguous','disable','restore'})
_RESTRICTION = re.compile(r"\b(?:no|nao|sin|sem|without|proibid\w*|prohibid\w*|prohibe\w*|forbid\w*|prohibit\w*|vedad\w*|banned|must not|do not|don't|avoid|evita\w*|evite\w*|solo|only|somente|apenas)\b")
_NEGATED = re.compile(r"\b(?:no se prohibe|no esta prohibido|nao e proibido|nao eh proibido|not prohibited|not forbidden|do not forbid|sin prohibicion|sem proibicao)\b")
_EXCEPTION = re.compile(r"\b(?:except\w*|salvo|unless|exceto|somente|apenas|only|solo)\b")
_INJECTION = re.compile(r"(?:ignore|ignora|desconsidere).{0,60}(?:previous instructions|system|instrucciones anteriores|instrucoes anteriores)|system prompt|developer message|prompt de sistema", re.S)
_CHANNEL = re.compile(r"<#(\d{1,19})>|(?<![\w<])#([\w\-]+)")
_ROLE = re.compile(r"<@&(\d{1,19})>")


def fingerprint(rule):
    return sha256(rule.encode()).hexdigest()


def restriction_present(rule):
    text = fold(rule)
    return bool(_RESTRICTION.search(text) and not _NEGATED.search(text) and not _INJECTION.search(text))


def literal_spans(rule, values):
    if type(values) is not list or len(values) > 32:
        raise ValueError("invalid_citations")
    spans = []
    for quote in values:
        if type(quote) is not str or not quote.strip() or quote not in rule or rule.count(quote) != 1:
            raise ValueError("unverified_citation")
        start = rule.index(quote)
        spans.append((start, start + len(quote)))
    return tuple(dict.fromkeys(spans))


def resolve_channels(rule, channels):
    """Solo referencias auténticas e inequívocas del mismo servidor."""
    resolved = set()
    for match in _CHANNEL.finditer(rule):
        if match[1]:
            number = int(match[1])
            if number not in channels:
                raise ValueError("unknown_channel_reference")
        else:
            candidates = [key for key, name in channels.items() if fold(name) == fold(match[2])]
            if len(candidates) != 1:
                raise ValueError("ambiguous_channel_reference")
            number = candidates[0]
        resolved.add(number)
    return tuple(sorted(resolved))


@dataclass(frozen=True)
class RuleInterpretation:
    number: int
    rule_hash: str
    status: str = "unavailable"
    normative: str = "ambiguous"
    categories: tuple[str, ...] = ()
    citations: tuple[tuple[int, int], ...] = ()
    prohibitions: tuple[tuple[int, int], ...] = ()
    obligations: tuple[tuple[int, int], ...] = ()
    permissions: tuple[tuple[int, int], ...] = ()
    exceptions: tuple[tuple[int, int], ...] = ()
    conditions: tuple[tuple[int, int], ...] = ()
    references: tuple[int, ...] = ()
    scope: str = "all"
    channels: tuple[int, ...] = ()
    exempt_roles: tuple[int, ...] = ()
    limitations: tuple[str, ...] = ()
    correction: str = ""
    clarification: str = ""
    base_status: str = ""

    def __post_init__(self):
        if not self.base_status:
            object.__setattr__(self, 'base_status', self.status)

    @property
    def kinds(self):
        if self.status not in {"watchable", "partial"}:
            return frozenset()
        return frozenset(kind for category in self.categories for kind in BEHAVIORS[category].kinds)

    def eligible(self, channel_id, roles):
        if not self.kinds or set(roles).intersection(self.exempt_roles):
            return False
        if self.scope == "outside_allowed_channels" and channel_id in self.channels:
            return False
        return self.scope != "only_listed_channels" or channel_id in self.channels


def abstain(snapshot, index, reason="provider_unavailable"):
    return RuleInterpretation(index + 1, fingerprint(snapshot.rules[index]), limitations=(reason,))


def validate_rule(value, snapshot, index, *, channels=None, role_ids=()):
    """Validar forma, citas, negación y ámbito; una propuesta nunca ejecuta nada."""
    source = snapshot.rules[index]
    expected = {"number", "quote", "normative", "conducts", "prohibitions", "obligations",
                "permissions", "exceptions", "conditions", "references", "scope", "ambiguous"}
    if (type(value) is not dict or set(value) != expected or type(value['number']) is not int
            or value['number'] != index + 1 or value['quote'] != source
            or type(value['normative']) is not str or value['normative'] not in NORMATIVE
            or type(value['ambiguous']) is not bool
            or type(value['conducts']) is not list or len(value['conducts']) > len(BEHAVIORS)):
        raise ValueError("invalid_rule_interpretation")
    kind = value['normative']
    fields = {name: literal_spans(source, value[name]) for name in
              ('prohibitions', 'obligations', 'permissions', 'exceptions', 'conditions')}
    references = value['references']
    if (type(references) is not list or len(references) > snapshot.count
            or any(type(n) is not int or not 1 <= n <= snapshot.count or n == index + 1 for n in references)):
        raise ValueError("invalid_cross_reference")
    categories, citations = [], []
    for conduct in value['conducts']:
        if (type(conduct) is not dict or set(conduct) != {'id', 'quote'}
                or type(conduct['id']) is not str or conduct['id'] not in BEHAVIORS):
            raise ValueError("unknown_conduct")
        spans = literal_spans(source, [conduct['quote']])
        if not grounded_category(conduct['id'], conduct['quote']):
            raise ValueError("ungrounded_conduct")
        categories.append(conduct['id']); citations.extend(spans)
    scope = value['scope']
    if type(scope) is not str or scope not in {'all', 'outside_allowed_channels', 'only_listed_channels', 'ambiguous'}:
        raise ValueError("invalid_rule_scope")
    limitations = []
    channel_refs = resolve_channels(source, channels or {}) if _CHANNEL.search(source) else ()
    roles = tuple(sorted({int(match[1]) for quote in value['exceptions'] for match in _ROLE.finditer(quote)}))
    if any(r not in set(role_ids) for r in roles):
        raise ValueError("unknown_role_reference")
    if scope != 'all' and not channel_refs:
        limitations.append('unresolved_scope')
    if scope == 'all' and channel_refs:
        limitations.append('unresolved_scope')
    if scope == 'outside_allowed_channels' and not _EXCEPTION.search(fold(source)):
        limitations.append('unresolved_scope')
    if _EXCEPTION.search(fold(source)) and not fields['exceptions'] and not fields['permissions']:
        limitations.append('unresolved_exception')
    if fields['exceptions'] and not channel_refs and not roles:
        limitations.append('unresolved_exception')
    if fields['exceptions'] and roles:
        for start,end in fields['exceptions']:
            # Una mención de rol dentro de una excepción más amplia no resuelve esa excepción.
            if not re.fullmatch(r'(?:excepto|except|exceto|salvo)\s+(?:(?:el rol|the role|o cargo|rol|role|cargo)\s+)?<@&\d+>\.?',fold(source[start:end]).strip()):
                limitations.append('unresolved_exception')
    if fields['exceptions'] and channel_refs and not roles and scope != 'outside_allowed_channels':
        limitations.append('unresolved_exception')
    if fields['conditions']:
        # Condiciones semánticas no se convierten en umbrales ficticios.
        limitations.append('conditional_rule_requires_review')
    if references:
        limitations.append('cross_reference_requires_review')
    if _NEGATED.search(fold(source)) or _INJECTION.search(fold(source)):
        limitations.append('ambiguous_normative')
    if kind in {'none', 'permission'} and not restriction_present(source):
        status = 'no_prohibition'
    elif kind == 'obligation':
        status = 'unsupported'; limitations.append('obligation_requires_review')
    elif value['ambiguous'] or kind == 'ambiguous' or limitations or not restriction_present(source):
        status = 'clarification'
    elif not categories or not fields['prohibitions'] and kind == 'prohibition':
        status = 'clarification'; limitations.append('missing_prohibition')
    else:
        available = [bool(BEHAVIORS[c].kinds) for c in categories]
        status = 'watchable' if all(available) else 'partial' if any(available) else 'unsupported'
        if not all(available):
            limitations.append('human_review_only')
    return RuleInterpretation(index + 1, fingerprint(source), status, kind,
        tuple(dict.fromkeys(categories)), tuple(dict.fromkeys(citations)), **fields,
        references=tuple(sorted(set(references))), scope=scope, channels=channel_refs,
        exempt_roles=roles, limitations=tuple(dict.fromkeys(limitations)))


def detect_contradictions(results):
    values = list(results)
    for i, left in enumerate(values):
        for j, right in enumerate(values):
            if i >= j or not set(left.categories).intersection(right.categories):
                continue
            opposites = ((left.normative == 'permission') != (right.normative == 'permission'))
            if opposites and left.scope == right.scope == 'all' and not left.exceptions and not right.exceptions:
                for at in (i, j):
                    values[at] = replace(values[at], status='contradiction', base_status='contradiction',
                        limitations=tuple(dict.fromkeys((*values[at].limitations, 'contradictory_rules'))))
    return tuple(values)


@dataclass(frozen=True)
class InterpretationPlan:
    guild_id: int
    revision: str
    rules: tuple[RuleInterpretation, ...]
    created_at: int
    approved_by: int = 0
    corrections: tuple[dict, ...] = ()

    def encode(self, snapshot):
        if (type(self.guild_id) is not int or self.guild_id != snapshot.guild_id or self.revision != snapshot.revision
                or len(self.rules) != snapshot.count or type(self.approved_by) is not int
                or not 0 <= self.approved_by < 2**63 or type(self.created_at) is not int
                or not 0 < self.created_at < 2**63 or len(self.corrections) > 32):
            raise ValueError('invalid_interpretation_plan')
        for correction in self.corrections:
            if (type(correction) is not dict or set(correction) !=
                    {'number','rule_hash','reason','revision','administrator_id','at'}
                    or type(correction['number']) is not int or not 1 <= correction['number'] <= 16
                    or type(correction['rule_hash']) is not str or not re.fullmatch('[a-f0-9]{64}',correction['rule_hash'])
                    or type(correction['revision']) is not str or not re.fullmatch('[a-f0-9]{64}',correction['revision'])
                    or type(correction['reason']) is not str or correction['reason'] not in CORRECTIONS
                    or any(type(correction[v]) is not int or not 0 < correction[v] < 2**63
                           for v in ('administrator_id','at'))):
                raise ValueError('invalid_correction_audit')
        for index, rule in enumerate(self.rules):
            source = snapshot.rules[index]
            if (type(rule.number) is not int or rule.number != index + 1
                    or rule.rule_hash != fingerprint(source) or rule.status not in STATES or rule.base_status not in STATES
                    or rule.normative not in NORMATIVE or not set(rule.categories) <= set(BEHAVIORS)
                    or rule.scope not in {'all','outside_allowed_channels','only_listed_channels','ambiguous'}
                    or any(type(v) is not int or not 0 < v < 2**63 for v in (*rule.channels,*rule.exempt_roles))
                    or type(rule.clarification) is not str or len(rule.clarification) > 1000
                    or rule.correction not in CORRECTIONS - {'restore'} | {''}
                    or any(type(v) is not int or not 1 <= v <= snapshot.count or v == rule.number
                           for v in rule.references)):
                raise ValueError('invalid_saved_rule')
            for name in ('citations','prohibitions','obligations','permissions','exceptions','conditions'):
                if any(len(span) != 2 or any(type(v) is not int for v in span)
                       or not 0 <= span[0] < span[1] <= len(source) for span in getattr(rule, name)):
                    raise ValueError('invalid_saved_span')
            if rule.kinds and (not restriction_present(source) or not rule.citations
                    or rule.normative not in {'prohibition','restriction'}
                    or rule.conditions or rule.references or rule.scope == 'ambiguous'
                    or rule.scope != 'all' and not rule.channels
                    or rule.scope != 'all' and not _CHANNEL.search(source)
                    or rule.scope == 'all' and bool(rule.channels)
                    or _EXCEPTION.search(fold(source)) and not rule.exceptions and not rule.permissions
                    or rule.exceptions and not rule.channels and not rule.exempt_roles
                    or set(rule.exempt_roles) != {int(match[1]) for start,end in rule.exceptions
                                                  for match in _ROLE.finditer(source[start:end])}
                    or rule.normative == 'prohibition' and not rule.prohibitions
                    or any(not any(grounded_category(category,source[start:end]) for start,end in rule.citations)
                           for category in rule.categories)):
                raise ValueError('saved_rule_without_grounding')
        raw = json.dumps({'version':1,'taxonomy_version':TAXONOMY_VERSION,**asdict(self)},
                         ensure_ascii=False,separators=(',',':'),sort_keys=True)
        if len(raw.encode()) > MAX_BYTES:
            raise ValueError('interpretation_size_limit')
        return raw

    @classmethod
    def decode(cls, raw, snapshot):
        if type(raw) is not str or len(raw.encode()) > MAX_BYTES:
            return None
        try:
            value=json.loads(raw)
            if (type(value) is not dict or set(value) != {'version','taxonomy_version','guild_id','revision',
                    'rules','created_at','approved_by','corrections'} or value['version'] != 1
                    or value['taxonomy_version'] != TAXONOMY_VERSION):
                return None
            rules=[]
            for item in value['rules']:
                for name in ('categories','references','channels','exempt_roles','limitations'):
                    item[name]=tuple(item[name])
                for name in ('citations','prohibitions','obligations','permissions','exceptions','conditions'):
                    item[name]=tuple(tuple(span) for span in item[name])
                rules.append(RuleInterpretation(**item))
            plan=cls(value['guild_id'],value['revision'],tuple(rules),value['created_at'],
                     value['approved_by'],tuple(value['corrections']))
            plan.encode(snapshot)
            return plan
        except (TypeError,ValueError,KeyError,AttributeError):
            return None

    def approve(self, administrator_id):
        if type(administrator_id) is not int or not 0 < administrator_id < 2**63:
            raise ValueError('administrator_required')
        return replace(self,approved_by=administrator_id)

    def correct(self, index, *, reason, note, administrator_id):
        if (type(index) is not int or not 0 <= index < len(self.rules)
                or reason not in CORRECTIONS
                or type(note) is not str or len(note) > 1000 or type(administrator_id) is not int
                or not 0 < administrator_id < 2**63):
            raise ValueError('invalid_interpretation_correction')
        rules=list(self.rules); previous=rules[index]
        if reason == 'restore':
            rules[index]=replace(previous,status=previous.base_status,correction='',clarification='')
        else:
            rules[index]=replace(previous,status='disabled',correction=reason,clarification=note)
        audit={'number':index+1,'rule_hash':previous.rule_hash,'reason':reason,
               'revision':self.revision,'administrator_id':administrator_id,'at':int(time.time())}
        return replace(self,rules=tuple(rules),approved_by=0,
                       corrections=(*self.corrections[-31:],audit))
