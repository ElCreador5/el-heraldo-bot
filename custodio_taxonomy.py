"""Registro extensible de conductas; nombres visibles solo mediante catálogo."""
from __future__ import annotations
from dataclasses import dataclass
import json
from pathlib import Path
import re
import unicodedata

from custodio_detection import KINDS

TAXONOMY_VERSION = "1.0.0"

NAME_KEYS = {
    'exact_text': 'text.custodio.behavior.exact_text',
    'near_text': 'text.custodio.behavior.near_text',
    'repeated_links': 'text.custodio.behavior.repeated_links',
    'character_flood': 'text.custodio.behavior.character_flood',
    'emoji_flood': 'text.custodio.behavior.emoji_flood',
    'fragmented_posts': 'text.custodio.behavior.fragmented_posts',
    'message_burst': 'text.custodio.behavior.message_burst',
    'cross_channel_repeat': 'text.custodio.behavior.cross_channel_repeat',
    'mass_forwarding': 'text.custodio.behavior.mass_forwarding',
    'chain_messages': 'text.custodio.behavior.chain_messages',
    'insistent_requests': 'text.custodio.behavior.insistent_requests',
    'repeated_images': 'text.custodio.behavior.repeated_images',
    'similar_images': 'text.custodio.behavior.similar_images',
    'repeated_gifs': 'text.custodio.behavior.repeated_gifs',
    'repeated_stickers': 'text.custodio.behavior.repeated_stickers',
    'attachment_burst': 'text.custodio.behavior.attachment_burst',
    'embed_burst': 'text.custodio.behavior.embed_burst',
    'unauthorized_promotion': 'text.custodio.behavior.unauthorized_promotion',
    'repeated_promotion': 'text.custodio.behavior.repeated_promotion',
    'server_invites': 'text.custodio.behavior.server_invites',
    'referral_links': 'text.custodio.behavior.referral_links',
    'commercial_solicitation': 'text.custodio.behavior.commercial_solicitation',
    'covert_advertising': 'text.custodio.behavior.covert_advertising',
    'invasive_recruitment': 'text.custodio.behavior.invasive_recruitment',
    'directed_insult': 'text.custodio.behavior.directed_insult',
    'repeated_devaluation': 'text.custodio.behavior.repeated_devaluation',
    'persistent_provocation': 'text.custodio.behavior.persistent_provocation',
    'repeated_harassment': 'text.custodio.behavior.repeated_harassment',
    'cross_channel_pursuit': 'text.custodio.behavior.cross_channel_pursuit',
    'collective_harassment': 'text.custodio.behavior.collective_harassment',
    'threats': 'text.custodio.behavior.threats',
    'intimidation': 'text.custodio.behavior.intimidation',
    'degrading_mockery': 'text.custodio.behavior.degrading_mockery',
    'discrimination': 'text.custodio.behavior.discrimination',
    'protected_attribute_attacks': 'text.custodio.behavior.protected_attribute_attacks',
    'harassment_incitement': 'text.custodio.behavior.harassment_incitement',
    'contextual_hostility': 'text.custodio.behavior.contextual_hostility',
    'sexual_harassment': 'text.custodio.behavior.sexual_harassment',
    'credential_solicitation': 'text.custodio.behavior.credential_solicitation',
    'staff_impersonation': 'text.custodio.behavior.staff_impersonation',
    'user_impersonation': 'text.custodio.behavior.user_impersonation',
    'phishing_links': 'text.custodio.behavior.phishing_links',
    'masked_link': 'text.custodio.behavior.masked_link',
    'financial_scams': 'text.custodio.behavior.financial_scams',
    'fake_support': 'text.custodio.behavior.fake_support',
    'giveaway_fraud': 'text.custodio.behavior.giveaway_fraud',
    'nonconsensual_pii': 'text.custodio.behavior.nonconsensual_pii',
    'social_engineering': 'text.custodio.behavior.social_engineering',
    'suspicious_files': 'text.custodio.behavior.suspicious_files',
    'synchronized_posts': 'text.custodio.behavior.synchronized_posts',
    'mention_campaign': 'text.custodio.behavior.mention_campaign',
    'interruption_campaign': 'text.custodio.behavior.interruption_campaign',
    'brigading': 'text.custodio.behavior.brigading',
    'ban_evasion': 'text.custodio.behavior.ban_evasion',
    'mass_mentions': 'text.custodio.behavior.mass_mentions',
    'broadcast_mentions': 'text.custodio.behavior.broadcast_mentions',
    'directed_mentions': 'text.custodio.behavior.directed_mentions',
    'spoiler_abuse': 'text.custodio.behavior.spoiler_abuse',
    'invisible_formatting': 'text.custodio.behavior.invisible_formatting',
    'format_flood': 'text.custodio.behavior.format_flood',
    'unauthorized_automation': 'text.custodio.behavior.unauthorized_automation',
    'reaction_spam': 'text.custodio.behavior.reaction_spam',
    'component_spam': 'text.custodio.behavior.component_spam',
    'thread_misuse': 'text.custodio.behavior.thread_misuse',
    'forum_misuse': 'text.custodio.behavior.forum_misuse',
    'reply_misuse': 'text.custodio.behavior.reply_misuse',
    'edited_link_evasion': 'text.custodio.behavior.edited_link_evasion',
    'off_topic': 'text.custodio.behavior.off_topic',
    'channel_conventions': 'text.custodio.behavior.channel_conventions',
    'ignored_staff_instruction': 'text.custodio.behavior.ignored_staff_instruction',
    'requests_after_response': 'text.custodio.behavior.requests_after_response',
    'age_restricted_placement': 'text.custodio.behavior.age_restricted_placement',
    'private_message_harassment': 'text.custodio.behavior.private_message_harassment',
}

@dataclass(frozen=True)
class Behavior:
    identifier: str
    name_key: str
    family: str
    kinds: frozenset[str]
    capability: str


def fold(value):
    return "".join(c for c in unicodedata.normalize("NFKD", value).casefold() if not unicodedata.combining(c))


_data = json.loads(Path(__file__).with_name("data").joinpath("custodio_taxonomy.json").read_text())
BEHAVIORS = {item["id"]: Behavior(item["id"], NAME_KEYS[item["id"]], item["family"],
    frozenset(item["method"]) & KINDS, item["capability"]) for item in _data["behaviors"]}
if _data["taxonomy_version"] != TAXONOMY_VERSION or set(BEHAVIORS) != set(NAME_KEYS):
    raise ValueError("taxonomy_registry_mismatch")
_review_terms = {item['id']: tuple(set(fold(word) for name in item['name'].values()
    for word in re.findall(r'\w+',name) if len(word)>=5)) for item in _data['behaviors']}
del _data

# Anclas para validar la relación semántica propuesta, no filtros de mensajes.
_CUES = {
    'exact_text': re.compile('\\b(?:spam\\w*|repea\\w*|repet\\w*|duplic\\w*)\\b'),
    'near_text': re.compile('\\b(?:spam\\w*|repea\\w*|repet\\w*|similar\\w*|parecid\\w*)\\b'),
    'repeated_links': re.compile('\\b(?:spam\\w*|repea\\w*|repet\\w*|links?|enlaces?|ligacoes)\\b'),
    'character_flood': re.compile('\\b(?:flood|satur\\w*|caracter\\w*|characters?|spam\\w*)\\b'),
    'emoji_flood': re.compile('\\b(?:flood|satur\\w*|emojis?|spam\\w*)\\b'),
    'fragmented_posts': re.compile('\\b(?:flood|satur\\w*|fragment\\w*|spam\\w*)\\b'),
    'message_burst': re.compile('\\b(?:spam\\w*|flood|satur\\w*|frequen\\w*|rafaga\\w*)\\b'),
    'cross_channel_repeat': re.compile('\\b(?:spam\\w*|repea\\w*|repet\\w*|duplic\\w*)\\b'),
    'mass_forwarding': re.compile('\\b(?:spam\\w*|reenvi\\w*|encaminh\\w*|forward\\w*)\\b'),
    'insistent_requests': re.compile('\\b(?:spam\\w*|insist\\w*|solicitud\\w*|requests?|pedidos?|repet\\w*)\\b'),
    'repeated_images': re.compile('\\b(?:spam\\w*|imagenes?|images?|imagens?|fotos?|pictures?|repet\\w*)\\b'),
    'similar_images': re.compile('\\b(?:spam\\w*|imagenes?|images?|imagens?|fotos?|pictures?|repet\\w*)\\b'),
    'repeated_gifs': re.compile('\\b(?:spam\\w*|gifs?|repet\\w*)\\b'),
    'repeated_stickers': re.compile('\\b(?:spam\\w*|stickers?|figurinhas?|pegatinas?|repet\\w*)\\b'),
    'attachment_burst': re.compile('\\b(?:flood|satur\\w*|adjuntos?|attachments?|anexos?|spam\\w*)\\b'),
    'unauthorized_promotion': re.compile('\\b(?:publicid\\w*|promoc\\w*|advertis\\w*|promotion\\w*|propaganda\\w*|anuncios?)\\b'),
    'repeated_promotion': re.compile('\\b(?:publicid\\w*|promoc\\w*|advertis\\w*|promotion\\w*|propaganda\\w*|anuncios?)\\b'),
    'synchronized_posts': re.compile('\\b(?:spam\\w*|coordin\\w*|coorden\\w*|sincron\\w*|synchron\\w*)\\b'),
    'mention_campaign': re.compile('\\b(?:mencion\\w*|mentions?|mencoes|everyone|here|spam\\w*)\\b'),
    'interruption_campaign': re.compile('\\b(?:spam\\w*|interrup\\w*|disrupt\\w*|coordin\\w*|coorden\\w*)\\b'),
    'mass_mentions': re.compile('\\b(?:mencion\\w*|mentions?|mencoes|everyone|here|spam\\w*)\\b'),
    'broadcast_mentions': re.compile('\\b(?:everyone|here|menciones? generales|broadcast mentions|mencoes gerais)\\b'),
    'directed_mentions': re.compile('\\b(?:mencion\\w*|mentions?|mencoes|pings?)\\b'),
    'masked_link': re.compile('\\b(?:enlaces? enganosos|links? (?:enganosos|enganadores|disguised|misleading)|masked links?|destinos? (?:falsos?|ocultos?))\\b'),
}


_REVIEW_ALIASES = {
    'repeated_harassment': re.compile(r'\b(?:acoso|assedio|harass\w*|hostig\w*)\b'),
    'cross_channel_pursuit': re.compile(r'\b(?:persegu\w*|pursu\w*|target\w*|acoso|assedio)\b'),
    'threats': re.compile(r'\b(?:amenaz\w*|threat\w*|ameac\w*)\b'),
    'directed_insult': re.compile(r'\b(?:insult\w*|ofens\w*|xing\w*|injur\w*|ataques? personales)\b'),
    'nonconsensual_pii': re.compile(r'\b(?:datos personales|informacion personal|personal data|dados pessoais|doxx\w*)\b'),
    'financial_scams': re.compile(r'\b(?:estaf\w*|scam\w*|golpe\w*|fraud\w*)\b'),
    'channel_conventions': re.compile(r'\b(?:format\w*|convenc\w*|conventions?)\b'),
}


def grounded_category(identifier, quote):
    behavior = BEHAVIORS.get(identifier)
    if behavior is None:
        return False
    if not behavior.kinds:
        normalized = fold(quote)
        alias = _REVIEW_ALIASES.get(identifier)
        return bool(alias and alias.search(normalized) or any(re.search(r'\b'+re.escape(term), normalized)
                   for term in _review_terms[identifier]))
    pattern = _CUES.get(identifier)
    return bool(pattern and pattern.search(fold(quote)))
