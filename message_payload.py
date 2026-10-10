"""Validación y renderizado de plantillas. No realiza operaciones de red."""
import copy
import re
from urllib.parse import urlsplit

VARIABLES = {'usuario', 'usuario_id', 'servidor', 'servidor_id', 'canal', 'fecha'}
VISUAL_KEYS = {'title', 'description', 'image', 'button_label', 'button_url', 'content', 'embeds'}


def text(value, limit):
    if not isinstance(value, str) or len(value) > limit:
        raise ValueError(f'El texto supera {limit} caracteres o no es texto.')
    return value


def url(value):
    text(value, 2048)
    parsed = urlsplit(value)
    if value and (parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password
                  or any(c.isspace() for c in value)):
        raise ValueError('Se requiere una URL HTTPS sin credenciales.')
    return value


def validate(values):
    if not isinstance(values, dict) or set(values) - VISUAL_KEYS:
        raise ValueError('Propiedades de plantilla no admitidas.')
    result = copy.deepcopy(values)
    for key, limit in {'title': 256, 'description': 4096, 'content': 2000, 'button_label': 80}.items():
        text(result.get(key, ''), limit)
    for key in ('image', 'button_url'):
        url(result.get(key, ''))
    if bool(result.get('button_url')) != bool(result.get('button_label')):
        raise ValueError('El botón requiere etiqueta y URL.')
    embeds = result.get('embeds', [])
    if not isinstance(embeds, list) or len(embeds) > 10:
        raise ValueError('Se admiten hasta diez embeds.')
    total = 0
    for embed in embeds:
        if not isinstance(embed, dict) or set(embed) - {'title', 'description', 'url', 'color', 'image', 'thumbnail', 'footer', 'author', 'fields'}:
            raise ValueError('Embed no válido.')
        if not any(embed.get(k) for k in ('title', 'description', 'image', 'thumbnail', 'footer', 'author', 'fields')):
            raise ValueError('No se admiten embeds vacíos.')
        for key, limit in (('title', 256), ('description', 4096)):
            total += len(text(embed.get(key, ''), limit))
        url(embed.get('url', ''))
        color = embed.get('color', 0x2B2D31)
        if type(color) is not int or not 0 <= color <= 0xFFFFFF:
            raise ValueError('Color fuera de rango.')
        for key in ('image', 'thumbnail'):
            if key in embed:
                if not isinstance(embed[key], dict) or set(embed[key]) != {'url'}:
                    raise ValueError('Imagen no válida.')
                url(embed[key]['url'])
        for key, caption, limit in (('footer', 'text', 2048), ('author', 'name', 256)):
            if key in embed:
                obj = embed[key]
                if not isinstance(obj, dict) or set(obj) - {caption, 'icon_url', 'url'}:
                    raise ValueError('Autor o pie no válido.')
                total += len(text(obj.get(caption, ''), limit))
                for field in ('url', 'icon_url'):
                    url(obj.get(field, ''))
        fields = embed.get('fields', [])
        if not isinstance(fields, list) or len(fields) > 25:
            raise ValueError('Se admiten hasta 25 campos por embed.')
        for field in fields:
            if not isinstance(field, dict) or set(field) - {'name', 'value', 'inline'}:
                raise ValueError('Campo no válido.')
            for key, limit in (('name', 256), ('value', 1024)):
                if not field.get(key):
                    raise ValueError('Los campos requieren nombre y valor.')
                total += len(text(field[key], limit))
            if type(field.get('inline', False)) is not bool:
                raise ValueError('inline debe ser booleano.')
    if total > 6000:
        raise ValueError('Los embeds juntos superan 6000 caracteres.')
    if not embeds and not any(result.get(k) for k in ('content', 'title', 'description', 'image')):
        raise ValueError('La plantilla requiere contenido.')
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
    if not isinstance(data, dict) or data.get('version') not in (1, 2) or not isinstance(data.get('templates'), list):
        raise ValueError('Versión o formato de kit no admitido.')
    if not 1 <= len(data['templates']) <= 25:
        raise ValueError('El kit requiere entre 1 y 25 plantillas.')
    cleaned, names = [], set()
    for item in data['templates']:
        if not isinstance(item, dict):
            raise ValueError('Plantilla no válida.')
        name = text(item.get('name'), 70).strip()
        if not name or name.casefold() in names:
            raise ValueError('Nombre vacío o repetido.')
        names.add(name.casefold())
        visual = validate({k: v for k, v in item.items() if k in VISUAL_KEYS})
        cleaned.append(dict(visual, name=name, role_component='', role_component_mode='ninguno'))
    return cleaned
