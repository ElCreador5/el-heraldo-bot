"""Motor de internacionalización de El Heraldo.

Los idiomas distintos del español solo se habilitan cuando el inventario de
mensajes del bot está completo y las pruebas de integración cubren cada ruta.
No hay fallback silencioso para un idioma que se declare publicado.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

DEFAULT_LOCALE = "es-419"
TARGET_LOCALES = ("es-419", "en-US", "pt-BR")
SUPPORTED_LOCALES = frozenset({DEFAULT_LOCALE})


class TranslationUnavailable(RuntimeError):
    """No permitir mostrar silenciosamente español en otro idioma."""


@dataclass(frozen=True)
class Catalog:
    locale: str
    messages: Mapping[str, str]


CATALOGS = {
    "es-419": Catalog("es-419", {
        "language.title": "El Heraldo · Idioma",
        "language.description": "Configura el idioma del bot para este servidor, incluidos los registros, los avisos y los mensajes privados asociados.",
        "language.current": "Actual: {language}",
        "language.pending": "Sin guardar: {language}",
        "language.help": "Los idiomas adicionales aparecerán cuando sus traducciones estén completas y verificadas. Los textos personalizados se conservan.",
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
        "language.title": "El Heraldo · Language",
        "language.description": "Configure the bot's language for this server, including logs, notices, and associated direct messages.",
        "language.current": "Current: {language}",
        "language.pending": "Not saved: {language}",
        "language.help": "Additional languages will appear once their translations have been completed and verified. Custom text is preserved.",
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
        "language.title": "El Heraldo · Idioma",
        "language.description": "Configure o idioma do bot neste servidor, incluindo registros, avisos e mensagens privadas relacionadas.",
        "language.current": "Atual: {language}",
        "language.pending": "Não salvo: {language}",
        "language.help": "Outros idiomas aparecerão quando todas as traduções estiverem concluídas e verificadas. Os textos personalizados serão preservados.",
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
