"""Presentación nativa de comandos por servidor, sin cambiar identificadores."""
from __future__ import annotations

import copy
import functools
import hashlib
import json
from pathlib import Path

import heraldo_i18n as i18n


def metadata_fields(payload):
    """Entrega únicamente descripciones y nombres visibles de opciones fijas."""
    def walk(node, parents):
        path = parents + [node['name']]
        prefix = '.'.join(path)
        if node.get('description') not in (None, '', '…', '...'):
            yield node, 'description', prefix + '.description'
        for choice in node.get('choices', []):
            value = json.dumps(choice['value'], ensure_ascii=False, sort_keys=True)
            tag = hashlib.sha256(value.encode()).hexdigest()[:12]
            yield choice, 'name', prefix + '.choice.' + tag
        for option in node.get('options', []):
            yield from walk(option, path)

    for command in payload:
        yield from walk(command, [])


def localize_schema(payload, locale):
    registry = json.loads(Path(__file__).with_name('locales').joinpath('command_schema.json').read_text())
    result = copy.deepcopy(payload)
    for node, field, path in metadata_fields(result):
        spec = registry.get(path)
        if spec is None or i18n.canonical_text(node[field]) != spec['source']:
            raise i18n.TranslationUnavailable('command_schema_changed:' + path)
        message = i18n.CATALOGS[locale].messages[spec['key']]
        if not 1 <= len(message) <= 100:
            raise i18n.TranslationUnavailable('command_schema_limit:' + path)
        node[field] = message
        # Las localizaciones del cliente no pueden sustituir el idioma guardado.
        node.pop(field + '_localizations', None)
    return result


def install(http, language_for_guild):
    """Aislar el cuerpo de cada PUT de servidor; los comandos globales no cambian."""
    original = http.bulk_upsert_guild_commands
    if getattr(original, '_heraldo_guild_language', False) is True:
        return

    @functools.wraps(original)
    async def guild_commands(application_id, guild_id, payload):
        locale = language_for_guild(guild_id)
        localized = localize_schema(payload, locale)
        result = await original(application_id, guild_id, payload=localized)
        print(f"COMMAND_SYNC status=SUCCESS scope=GUILD locale={locale} commands={len(localized)}")
        return result

    guild_commands._heraldo_guild_language = True
    http.bulk_upsert_guild_commands = guild_commands
