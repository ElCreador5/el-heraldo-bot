"""Localización conservadora de etiquetas predeterminadas de reportes.

Diseñado para el motor mínimo de producción: no importa los catálogos del
laboratorio ni reescribe datos de usuarios o la base de datos.
"""
from __future__ import annotations

DEFAULTS = {
    "📢": {
        "es-419": "Spam", "en-US": "Spam", "pt-BR": "Spam",
    },
    "🚩": {
        "es-419": "Contenido inapropiado / no permitido",
        "en-US": "Inappropriate content / not permitted",
        "pt-BR": "Conteúdo inadequado / não permitido",
    },
    "🤓": {
        "es-419": "Sospechoso (posible cuenta falsa o estafa)",
        "en-US": "Suspect (possible fake account or fraud)",
        "pt-BR": "Suspeito (possível conta falsa ou fraude)",
    },
    "🔞": {
        "es-419": "Posible menor de edad",
        "en-US": "Possible minor",
        "pt-BR": "Possível menor de idade",
    },
}


def report_label(item: dict, locale: str) -> str:
    """Solo cambiar etiquetas de catálogo asociadas al MISMO emoji."""
    original = str(item.get("label") or "")
    emoji = str(item.get("emoji") or "").replace("\ufe0f", "").strip()
    translations = DEFAULTS.get(emoji)
    if not translations or original not in translations.values():
        return original
    return translations.get(locale, original)
