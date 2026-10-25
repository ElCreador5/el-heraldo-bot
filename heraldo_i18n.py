"""Motor de internacionalización de El Heraldo.

Inglés y portugués brasileño están disponibles en estado PARCIAL, según
solicitud del propietario. El catálogo traduce únicamente las claves integradas;
los demás mensajes del bot conservan temporalmente su idioma original.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

DEFAULT_LOCALE = "es-419"
TARGET_LOCALES = ("es-419", "en-US", "pt-BR")
SUPPORTED_LOCALES = frozenset(TARGET_LOCALES)
PARTIAL_LOCALES = frozenset({"en-US", "pt-BR"})


class TranslationUnavailable(RuntimeError):
    """No permitir mostrar silenciosamente español en otro idioma."""


@dataclass(frozen=True)
class Catalog:
    locale: str
    messages: Mapping[str, str]


CATALOGS = {
    "es-419": Catalog("es-419", {
        "setup.home": "**El Heraldo · Configuración**\n\nSelecciona una sección y se abrirá directamente. Guarda los cambios solo cuando estés conforme.\nPuedes volver a este menú desde las opciones de navegación de cada módulo.",
        "setup.access_denied": "Acceso denegado. Se requiere Gestionar servidor y una sesión propia en este servidor.",
        "language.title": "El Heraldo · Idioma",
        "language.description": "Configura el idioma del bot para este servidor, incluidos los registros, los avisos y los mensajes privados asociados.",
        "language.current": "Actual: {language}",
        "language.pending": "Sin guardar: {language}",
        "language.help": "Otras funciones del bot pueden aparecer en español. En desarrollo.",
        "language.select": "Selecciona el idioma del servidor",
        "language.verified": "Idioma completo y verificado",
        "language.not_available": "Este idioma todavía no está disponible.",
        "language.concurrent_change": "El idioma cambió en otra sesión. Abre nuevamente el editor.",
        "language.saved": "Cambios guardados.",
        "language.closed": "Configuración de idioma cerrada.",
        "language.save": "Guardar cambios",
        "language.discard": "Descartar cambios",
        "language.back": "Volver",
    }),
    "en-US": Catalog("en-US", {
        "setup.home": "**El Heraldo · Settings**\n\nSelect a section to open it directly. Save changes only when you are satisfied.\nYou can return to this menu from each module's navigation options.",
        "setup.access_denied": "Access denied. You need Manage Server permission and must use your own session in this server.",
        "language.title": "El Heraldo · Language",
        "language.description": "Configure the bot's language for this server, including logs, notices, and associated direct messages.",
        "language.current": "Current: {language}",
        "language.pending": "Not saved: {language}",
        "language.help": "Other bot features may appear in Spanish. In development.",
        "language.select": "Select the server language",
        "language.verified": "Fully translated and verified",
        "language.not_available": "This language is not available yet.",
        "language.concurrent_change": "The language was changed in another session. Reopen the editor.",
        "language.saved": "Changes saved.",
        "language.closed": "Language settings closed.",
        "language.save": "Save changes",
        "language.discard": "Discard changes",
        "language.back": "Back",
    }),
    "pt-BR": Catalog("pt-BR", {
        "setup.home": "**El Heraldo · Configurações**\n\nSelecione uma seção para abri-la diretamente. Salve as alterações somente quando estiver satisfeito.\nVocê pode voltar a este menu pelas opções de navegação de cada módulo.",
        "setup.access_denied": "Acesso negado. É necessário ter a permissão Gerenciar Servidor e usar sua própria sessão neste servidor.",
        "language.title": "El Heraldo · Idioma",
        "language.description": "Configure o idioma do bot neste servidor, incluindo registros, avisos e mensagens privadas relacionadas.",
        "language.current": "Atual: {language}",
        "language.pending": "Não salvo: {language}",
        "language.help": "Outras funções do bot podem aparecer em espanhol. Em desenvolvimento.",
        "language.select": "Selecione o idioma do servidor",
        "language.verified": "Idioma totalmente traduzido e verificado",
        "language.not_available": "Este idioma ainda não está disponível.",
        "language.concurrent_change": "O idioma foi alterado em outra sessão. Abra o editor novamente.",
        "language.saved": "Alterações salvas.",
        "language.closed": "Configuração de idioma fechada.",
        "language.save": "Salvar alterações",
        "language.discard": "Descartar alterações",
        "language.back": "Voltar",
    }),
}


def _fields(template: str) -> frozenset[str]:
    from string import Formatter
    return frozenset(field for _, field, _, _ in Formatter().parse(template) if field)


def verify_catalogs() -> None:
    base = CATALOGS[DEFAULT_LOCALE].messages
    for locale, catalog in CATALOGS.items():
        if catalog.locale != locale or set(catalog.messages) != set(base):
            raise TranslationUnavailable(f"Catálogo incompleto: {locale}")
        for key, message in catalog.messages.items():
            if not message.strip() or _fields(message) != _fields(base[key]):
                raise TranslationUnavailable(f"Texto o variables incompletas: {locale}/{key}")


def translate(locale: str, key: str, **variables: object) -> str:
    if locale not in SUPPORTED_LOCALES:
        raise TranslationUnavailable(f"Idioma todavía no habilitado: {locale}")
    template = CATALOGS[locale].messages.get(key)
    if template is None:
        raise TranslationUnavailable(f"Traducción faltante: {locale}/{key}")
    return template.format(**variables)


verify_catalogs()

# Catálogos de presentación extraídos del código; no contienen textos de usuarios.
import contextlib
import contextvars
import functools
import inspect
import json
from pathlib import Path

_current_guild = contextvars.ContextVar("heraldo_i18n_guild", default=None)
_locale_resolver = lambda guild_id: DEFAULT_LOCALE


def set_locale_resolver(resolver):
    global _locale_resolver
    _locale_resolver = resolver


def current_locale():
    guild_id = _current_guild.get()
    return _locale_resolver(guild_id) if guild_id is not None else DEFAULT_LOCALE


@contextlib.contextmanager
def use_guild(guild_id):
    token = _current_guild.set(guild_id)
    try:
        yield
    finally:
        _current_guild.reset(token)


def _source_id(value, *, guild=False, seen=None):
    # Nunca leer user.locale/interaction.locale. Solo relaciones explícitas.
    if value is None:
        return None
    seen = set() if seen is None else seen
    if id(value) in seen:
        return None
    seen.add(id(value))
    if guild and type(value) is int:
        return value
    if guild:
        candidate = getattr(value, "id", None)
        return candidate if type(candidate) is int else None
    candidate = getattr(value, "guild_id", None)
    if type(candidate) is int:
        return candidate
    source = getattr(value, "guild", None)
    candidate = getattr(source, "id", None)
    if type(candidate) is int:
        return candidate
    extras = getattr(value, "extras", None)
    if isinstance(extras, dict):
        original = extras.get("heraldo_source_guild")
        candidate = getattr(original, "id", None)
        if type(candidate) is int:
            return candidate
    for attr in ("parent", "editor", "parent_view", "setup_view", "channel"):
        parent = (getattr(value, attr, None)
                  if attr in getattr(value, "__dict__", {}) or hasattr(type(value), attr) else None)
        if parent is not None and parent is not value:
            found = _source_id(parent, seen=seen)
            if found is not None:
                return found
    return None


def guild_context(function):
    """Contexto por llamada/tarea; restaura el servidor incluso al fallar.

    Los puntos de entrada usan los argumentos reales del evento, nunca una
    preferencia del usuario. Las llamadas internas heredan el contexto.
    """
    signature = inspect.signature(function)
    names = tuple(signature.parameters)

    def source(args, kwargs):
        values = dict(zip(names, args))
        values.update(kwargs)
        gid = values.get("guild_id")
        if type(gid) is int:
            return gid
        for name in ("row", "case", "saved"):
            item = values.get(name)
            try:
                candidate = item["guild_id"]
            except (TypeError, KeyError, IndexError):
                continue
            if type(candidate) is int:
                return candidate
        for name in ("guild", "source_guild", "origin_guild", "interaction", "ctx", "member", "message", "channel", "self", "parent", "editor", "view"):
            if name in values:
                found = _source_id(values[name], guild=name in {"guild", "source_guild", "origin_guild"})
                if found is not None:
                    return found
        return _current_guild.get()

    if inspect.iscoroutinefunction(function):
        @functools.wraps(function)
        async def wrapped(*args, **kwargs):
            with use_guild(source(args, kwargs)):
                return resolve_owned(await function(*args, **kwargs))
    else:
        @functools.wraps(function)
        def wrapped(*args, **kwargs):
            with use_guild(source(args, kwargs)):
                return resolve_owned(function(*args, **kwargs))
    return wrapped


class DeferredText(str):
    """Texto propio con procedencia; nunca identifica ni traduce texto libre."""
    def __new__(cls, key, variables=None, locale=None):
        locale = locale or current_locale()
        variables = dict(variables or {})
        template = CATALOGS[locale].messages[key]
        rendered = template.format(**variables) if variables else template
        obj = super().__new__(cls, rendered)
        obj.key, obj.variables, obj.locale = key, variables, locale
        return obj

    def __str__(self):
        locale = current_locale() if _current_guild.get() is not None else self.locale
        template = CATALOGS[locale].messages[self.key]
        return template.format(**self.variables) if self.variables else template

    def __format__(self, spec):
        return format(str(self), spec)

    def format(self, *args, **kwargs):
        return str(self).format(*args, **kwargs)

    def replace(self, *args, **kwargs):
        return str(self).replace(*args, **kwargs)

    def split(self, *args, **kwargs):
        return str(self).split(*args, **kwargs)

    def strip(self, *args, **kwargs):
        return str(self).strip(*args, **kwargs)

    def splitlines(self, *args, **kwargs):
        return str(self).splitlines(*args, **kwargs)

    def __deepcopy__(self, memo):
        return type(self)(self.key, self.variables, self.locale)


def text(key, **variables):
    """Texto propio por clave; los parámetros se interpolan una sola vez."""
    if key not in CATALOGS[DEFAULT_LOCALE].messages:
        raise TranslationUnavailable(f"Traducción faltante: {key}")
    return DeferredText(key, variables, current_locale())


def variants(key):
    """Etiquetas propias actuales/históricas, exclusivamente para localizar UI."""
    return frozenset(catalog.messages[key] for catalog in CATALOGS.values())


def resolve_owned(value):
    """Resuelve únicamente constantes etiquetadas, jamás compara texto libre."""
    if isinstance(value, DeferredText):
        return DeferredText(value.key, value.variables, current_locale())
    if type(value) is dict:
        return {key: resolve_owned(item) for key, item in value.items()}
    if type(value) is list:
        return [resolve_owned(item) for item in value]
    if type(value) is tuple:
        return tuple(resolve_owned(item) for item in value)
    return value


def _load_extended_catalogs():
    directory = Path(__file__).with_name("locales")
    for locale, catalog in tuple(CATALOGS.items()):
        path = directory / f"{locale}.json"
        if path.exists():
            messages = dict(catalog.messages)
            extra = json.loads(path.read_text(encoding="utf-8"))
            if messages.keys() & extra.keys():
                raise TranslationUnavailable(f"Claves duplicadas: {locale}")
            messages.update(extra)
            CATALOGS[locale] = Catalog(locale, messages)
    verify_catalogs()


_load_extended_catalogs()


def install_discord(discord):
    """Serializa constantes de decoradores en el idioma del servidor emisor."""
    if getattr(discord.ui.View.to_components, "_heraldo_i18n", False):
        return
    view_components = discord.ui.View.to_components
    modal_dict = discord.ui.Modal.to_dict
    send_modal = discord.InteractionResponse.send_modal

    @functools.wraps(view_components)
    def components(view):
        source = _source_id(view)
        if source is None:
            source = _current_guild.get()
        with use_guild(source):
            return resolve_owned(view_components(view))
    components._heraldo_i18n = True

    @functools.wraps(modal_dict)
    def modal_payload(modal):
        source = _source_id(modal)
        if source is None:
            source = _current_guild.get()
        with use_guild(source):
            return resolve_owned(modal_dict(modal))

    @functools.wraps(send_modal)
    async def modal_response(response, modal, **kwargs):
        source = _source_id(response._parent)
        if source is None:
            source = _source_id(modal) or _current_guild.get()
        with use_guild(source):
            return await send_modal(response, modal, **kwargs)

    discord.ui.View.to_components = components
    discord.ui.Modal.to_dict = modal_payload
    discord.InteractionResponse.send_modal = modal_response

_FIXED_INPUTS = {
    "Todos": "access.all", "Lista blanca": "access.allowlist", "Lista negra": "access.denylist",
    "guardar": "common.save", "eliminar": "common.delete",
    "añadir": "input.add", "quitar": "input.remove", "alternar": "input.toggle",
    "boton": "input.button", "menu": "input.menu", "ninguno": "input.none",
}


def fixed_label(value):
    key = _FIXED_INPUTS.get(value)
    return text(key) if key else value


def canonical_fixed(value):
    for original, key in _FIXED_INPUTS.items():
        if value.casefold() in {entry.casefold() for entry in variants(key)}:
            return original
    return value


def bool_input(value):
    normalized = value.strip().casefold()
    if normalized in {"yes", "sim", "sí", "si"}:
        return "si"
    if normalized in {"no", "não", "nao"}:
        return "no"
    return normalized


def current_guild_id():
    return _current_guild.get()


def set_source(guild_id):
    # Usar dentro de un punto de entrada con guild_context, que restaura el token.
    if type(guild_id) is int:
        _current_guild.set(guild_id)


def source_id(row):
    try:
        candidate = row["guild_id"]
    except (TypeError, KeyError, IndexError):
        return None
    return candidate if type(candidate) is int else None


def canonical_text(value):
    """Identificar eventos propios por su clave, sin clasificar texto traducido."""
    if isinstance(value, DeferredText):
        return CATALOGS[DEFAULT_LOCALE].messages[value.key]
    return str(value)
