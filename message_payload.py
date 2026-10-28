"""Validación y renderizado de plantillas. No realiza operaciones de red."""
from heraldo_i18n import text as _t, guild_context as _i18n_context, use_guild as _i18n_guild
import copy
import re
from datetime import datetime
from urllib.parse import urlsplit

VARIABLES = {'usuario', 'usuario_id', 'servidor', 'servidor_id', 'canal', 'fecha'}
VISUAL_KEYS = {'title', 'description', 'image', 'button_label', 'button_url', 'content', 'embeds'}


class TemplateEmbeds(list):
    """Lista Discord normal que conserva el diseño explícito ante hooks heredados."""


def text(value, limit):
    if not isinstance(value, str) or len(value) > limit:
        raise ValueError(_t('text.ccfe6659fcf359', p0=f'{limit}'))
    return value


def url(value):
    text(value, 2048)
    parsed = urlsplit(value)
    if value and (parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password
                  or any(c.isspace() for c in value)):
        raise ValueError(_t('text.b9bebe2d586542'))
    return value


def validate(values):
    if not isinstance(values, dict) or set(values) - VISUAL_KEYS:
        raise ValueError(_t('text.4647d65e92605f'))
    result = copy.deepcopy(values)
    for key, limit in {'title': 256, 'description': 4096, 'content': 2000, 'button_label': 80}.items():
        text(result.get(key, ''), limit)
    for key in ('image', 'button_url'):
        url(result.get(key, ''))
    if bool(result.get('button_url')) != bool(result.get('button_label')):
        raise ValueError(_t('text.e6adf1faab3088'))
    embeds = result.get('embeds', [])
    if not isinstance(embeds, list) or len(embeds) > 10:
        raise ValueError(_t('text.a32aad3e849f80'))
    total = 0
    for embed in embeds:
        if not isinstance(embed, dict) or set(embed) - {'title', 'description', 'url', 'color', 'image', 'thumbnail', 'footer', 'author', 'fields', 'timestamp'}:
            raise ValueError(_t('text.e30fc1bebd0a1f'))
        if not any(embed.get(k) for k in ('title', 'description', 'image', 'thumbnail', 'footer', 'author', 'fields')):
            raise ValueError(_t('text.a460bbdb699931'))
        for key, limit in (('title', 256), ('description', 4096)):
            total += len(text(embed.get(key, ''), limit))
        url(embed.get('url', ''))
        if 'timestamp' in embed:
            try:
                value = embed['timestamp']
                if not isinstance(value, str) or len(value) > 40 or datetime.fromisoformat(value.replace('Z', '+00:00')).tzinfo is None:
                    raise ValueError('timestamp')
            except (ValueError, TypeError) as exc:
                raise ValueError('Invalid embed timestamp') from exc
        color = embed.get('color', 0x2B2D31)
        if type(color) is not int or not 0 <= color <= 0xFFFFFF:
            raise ValueError(_t('text.28724350339107'))
        for key in ('image', 'thumbnail'):
            if key in embed:
                if not isinstance(embed[key], dict) or set(embed[key]) != {'url'}:
                    raise ValueError(_t('text.3af247d93ed913'))
                if not embed[key]['url']:
                    raise ValueError(_t('text.2c96b384152b66'))
                url(embed[key]['url'])
        for key, caption, limit in (('footer', 'text', 2048), ('author', 'name', 256)):
            if key in embed:
                obj = embed[key]
                if not isinstance(obj, dict) or set(obj) - {caption, 'icon_url', 'url'}:
                    raise ValueError(_t('text.afcab719309535'))
                if not obj.get(caption):
                    raise ValueError(_t('text.5e6c3f135b80cf'))
                total += len(text(obj.get(caption, ''), limit))
                for field in ('url', 'icon_url'):
                    url(obj.get(field, ''))
        fields = embed.get('fields', [])
        if not isinstance(fields, list) or len(fields) > 25:
            raise ValueError(_t('text.b912f1e71db140'))
        for field in fields:
            if not isinstance(field, dict) or set(field) - {'name', 'value', 'inline'}:
                raise ValueError(_t('text.a3bc3e1722f928'))
            for key, limit in (('name', 256), ('value', 1024)):
                if not field.get(key):
                    raise ValueError(_t('text.236c0738873508'))
                total += len(text(field[key], limit))
            if type(field.get('inline', False)) is not bool:
                raise ValueError(_t('text.1723c29b5563f1'))
    if total > 6000:
        raise ValueError(_t('text.34845b77024b64'))
    if not embeds and not any(result.get(k) for k in ('content', 'title', 'description', 'image')):
        raise ValueError(_t('text.e0d336052d6e5f'))
    return result


def render(template, context=None):
    values = {k: copy.deepcopy(v) for k, v in template.items() if k in VISUAL_KEYS}
    context = context or {}
    def expand(value):
        if isinstance(value, str):
            return re.sub(r'\{([a-z_]+)\}', lambda m: str(context.get(m[1], m[0])) if m[1] in VARIABLES else m[0], value)
        if isinstance(value, list):
            return [expand(x) for x in value]
        if isinstance(value, dict):
            return {k: expand(v) for k, v in value.items()}
        return value
    values = validate(expand(values))
    embeds = values.get('embeds', [])
    if not embeds and any(values.get(k) for k in ('title', 'description', 'image')):
        embed = {k: values[k] for k in ('title', 'description') if values.get(k)}
        embed['color'] = 0x2B2D31
        if values.get('image'):
            embed['image'] = {'url': values['image']}
        embeds = [embed]
        validate({'embeds': embeds})
    return values.get('content') or None, embeds


def import_kit(data):
    if not isinstance(data, dict) or type(data.get('version')) is not int or data.get('version') not in (1, 2) or not isinstance(data.get('templates'), list):
        raise ValueError(_t('text.9a4da7d4d43de4'))
    if not 1 <= len(data['templates']) <= 25:
        raise ValueError(_t('text.228ce5099dd20f'))
    cleaned, names = [], set()
    for item in data['templates']:
        if not isinstance(item, dict):
            raise ValueError(_t('text.f9e8c63c2240df'))
        name = text(item.get('name'), 70).strip()
        if not name or name.casefold() in names:
            raise ValueError(_t('text.d515f64e825e05'))
        names.add(name.casefold())
        visual = validate({k: v for k, v in item.items() if k in VISUAL_KEYS})
        cleaned.append(dict(visual, name=name, role_component='', role_component_mode='ninguno'))
    return cleaned
