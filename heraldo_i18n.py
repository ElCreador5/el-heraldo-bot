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
        "setup.home": "**El Heraldo · Configuración**\\\n\\\nSelecciona una sección y se abrirá directamente. Guarda los cambios solo cuando estés conforme.\\\nPuedes volver a este menú desde las opciones de navegación de cada módulo.",
        "setup.access_denied": "Acceso denegado. Se requiere Gestionar servidor y una sesión propia en este servidor.",
        "language.title": "El Heraldo · Idioma",
        "language.description": "Configura el idioma del bot para este servidor, incluidos los registros, los avisos y los mensajes privados asociados.",
        "language.current": "Actual: {language}",
        "language.pending": "Sin guardar: {language}",
        "language.help": "Otras funciones del bot todavía pueden aparecer en español.",
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
        "setup.home": "**El Heraldo · Settings**\\\n\\\nSelect a section to open it directly. Save changes only when you are satisfied.\\\nYou can return to this menu from each module's navigation options.",
        "setup.access_denied": "Access denied. You need Manage Server permission and must use your own session in this server.",
        "language.title": "El Heraldo · Language",
        "language.description": "Configure the bot's language for this server, including logs, notices, and associated direct messages.",
        "language.current": "Current: {language}",
        "language.pending": "Not saved: {language}",
        "language.help": "Other bot features may still appear in Spanish.",
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
        "setup.home": "**El Heraldo · Configurações**\\\n\\\nSelecione uma seção para abri-la diretamente. Salve as alterações somente quando estiver satisfeito.\\\nVocê pode voltar a este menu pelas opções de navegação de cada módulo.",
        "setup.access_denied": "Acesso negado. É necessário ter a permissão Gerenciar Servidor e usar sua própria sessão neste servidor.",
        "language.title": "El Heraldo · Idioma",
        "language.description": "Configure o idioma do bot neste servidor, incluindo registros, avisos e mensagens privadas relacionadas.",
        "language.current": "Atual: {language}",
        "language.pending": "Não salvo: {language}",
        "language.help": "Outras funções do bot ainda podem aparecer em espanhol.",
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
