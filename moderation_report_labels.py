"""Etiquetas de reporte del sistema en el idioma manual de cada servidor.

No altera SQLite ni traduce texto de usuarios. Solo reconoce textos por defecto
exactos del mismo emoji que El Heraldo ya distribuyó en sus tres idiomas.
"""
from __future__ import annotations

import heraldo_i18n as i18n

DEFAULT_REACTION_LABEL_KEYS = {
    "❗": "text.8e0e9e0ddc829f",
    "📢": "text.94a9eac404c8c6",
    "🚩": "text.ce9c8e559ad9fe",
    "🤓": "text.fa7c7004213f04",
    "🔞": "text.bdfac38f2af4cc",
}


def report_label(item: dict, locale: str) -> str:
    """Traduce únicamente un rótulo predeterminado idéntico al catálogo.

    Aunque el registro conserve el español de cuando se creó, el rótulo
    institucional cambia al visualizarse. Etiquetas libres y emojis distintos
    nunca se modifican ni se vuelven a guardar automáticamente.
    """
    stored = str(item.get("label") or "")
    emoji = str(item.get("emoji") or "").replace("\ufe0f", "").strip()
    key = DEFAULT_REACTION_LABEL_KEYS.get(emoji)
    if not key or locale not in i18n.SUPPORTED_LOCALES:
        return stored
    variants = {catalog.messages.get(key) for catalog in i18n.CATALOGS.values()}
    if stored not in variants:
        return stored
    return i18n.translate(locale, key)
