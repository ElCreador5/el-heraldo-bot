"""Referencias abiertas y evaluación reproducible de Custodio, sin descargar datos.

Los ejemplos de debates públicos no son reglas del servidor. Los conjuntos
externos solo podrán incorporarse tras revisar la licencia, minimizar datos y
separar entrenamiento/evaluación. No se autoentrena ni accede a mensajes Discord.
"""
from __future__ import annotations
from dataclasses import dataclass
from collections.abc import Mapping

# Registro de fuentes documentadas; NO descarga ni almacena mensajes externos.
PUBLIC_CORPORA = (
    {
        "name": "Civil Comments",
        "url": "https://www.tensorflow.org/datasets/catalog/civil_comments",
        "license": "CC0",
        "language": "en",
        "purpose": "Debates públicos, contexto de respuesta y categorías de toxicidad",
    },
    {
        "name": "Wikipedia Talk Labels: Toxicity",
        "url": "https://figshare.com/articles/dataset/Wikipedia_Talk_Labels_Toxicity/4563973",
        "license": "CC0",
        "language": "en",
        "purpose": "Comentarios de debates colaborativos con anotaciones humanas",
    },
    {
        "name": "Multilingual HateCheck, Spanish",
        "url": "https://huggingface.co/datasets/Paul/hatecheck-spanish",
        "license": "CC-BY-4.0",
        "language": "es",
        "purpose": "Pruebas funcionales de errores y falsos positivos en español",
    },
)

OUTCOMES = frozenset({"clear", "suspected", "ambiguous"})
MAX_CASE_CHARS = 500


@dataclass(frozen=True)
class Case:
    reference: str
    context: str
    message: str
    outcome: str
    rule_numbers: tuple[int, ...]
    category: str

    def __post_init__(self):
        if self.outcome not in OUTCOMES:
            raise ValueError("invalid_gold_label")
        if not self.reference or len(self.context) > MAX_CASE_CHARS or len(self.message) > MAX_CASE_CHARS:
            raise ValueError("invalid_case")
        if self.outcome == "clear" and self.rule_numbers:
            raise ValueError("clear_case_must_have_no_rules")
        if self.outcome != "clear" and not self.rule_numbers:
            raise ValueError("flagged_case_must_reference_rules")


# Casos inventados y despersonalizados. No son capturas ni publicaciones copiadas.
LAB_CASES: tuple[Case, ...] = (
    Case("respect-1", "Dos miembros debaten sobre un videojuego.",
         "Creo que tu estrategia no funciona porque deja el equipo expuesto.",
         "clear", (), "disagreement"),
    Case("respect-2", "Una persona intenta abandonar una conversación; la otra insiste.",
         "Te seguiré enviando mensajes aunque me pidas que pare.",
         "suspected", (1,), "unwanted_contact"),
    Case("respect-3", "Entre compañeros hay bromas frecuentes, sin contexto suficiente.",
         "Eres muy lento, de verdad.", "ambiguous", (2,), "context"),
    Case("reports-1", "Un miembro denuncia un mensaje recibido.",
         "Alguien me insultó en privado; ¿pueden revisar mi reporte?",
         "clear", (), "report"),
    Case("reports-2", "Un miembro cita una frase ajena para reportarla.",
         "Esta frase fue ofensiva; la comparto únicamente para denunciarla.",
         "clear", (), "quotation"),
    Case("spam-1", "Usuario publica repetidamente el mismo anuncio sin autorización.",
         "¡Entren todos al enlace del anuncio!", "suspected", (4, 6,), "repetition"),
    Case("spam-2", "Mensaje único de celebración en un canal general.",
         "¡Qué bien! 🎉🎉", "clear", (), "emoji"),
    Case("links-1", "Miembro pregunta por una noticia tecnológica.",
         "¿Alguien tiene una fuente fiable que explique este cambio?",
         "clear", (), "reference"),
    Case("links-2", "Se anuncia una supuesta recompensa a cambio de credenciales.",
         "Para recibir el premio debes entregar la contraseña.",
         "suspected", (7, 8), "credentials"),
    Case("impersonation-1", "No se dispone de información para confirmar la identidad.",
         "Soy parte del equipo, escríbeme por privado.",
         "ambiguous", (8,), "identity"),
    Case("privacy-1", "Un miembro busca ayuda para eliminar datos expuestos.",
         "Alguien compartió mi teléfono sin permiso; necesito ayuda.",
         "clear", (), "privacy_report"),
    Case("privacy-2", "Alguien propone difundir datos de un tercero.",
         "Publiquemos el número privado de otra persona.",
         "suspected", (9,), "privacy"),
    Case("appeal-1", "Miembro quiere impugnar una decisión de moderación.",
         "No estoy de acuerdo con la sanción; ¿dónde puedo apelar?",
         "clear", (), "appeal"),
    Case("appeal-2", "Un miembro comenta que piensa usar otra cuenta para esquivar medidas.",
         "Si me sancionan, entraré con otra cuenta para continuar.",
         "suspected", (11,), "evasion"),
    Case("appeal-3", "Un miembro expresa frustración pero no evade medidas.",
         "Si me sancionan otra vez, dejaré de participar.",
         "clear", (), "frustration"),
    Case("identity-1", "Conversación educativa sin descalificar colectivos.",
         "Estamos estudiando por qué la discriminación es perjudicial.",
         "clear", (), "education"),
)

def evaluate_predictions(predictions: Mapping[str, str], cases: tuple[Case, ...] = LAB_CASES) -> dict[str, int]:
    """Métricas simples sin imprimir contenidos ni identidades de usuarios."""
    if set(predictions) != {c.reference for c in cases}:
        raise ValueError("incomplete_predictions")
    if any(v not in OUTCOMES for v in predictions.values()):
        raise ValueError("invalid_prediction_label")
    result = {
        "samples": len(cases),
        "correct": 0,
        "false_positive": 0,
        "missed_suspected": 0,
        "ambiguous_sent_to_review": 0,
    }
    for case in cases:
        predicted = predictions[case.reference]
        result["correct"] += int(predicted == case.outcome)
        result["false_positive"] += int(case.outcome == "clear" and predicted == "suspected")
        result["missed_suspected"] += int(case.outcome == "suspected" and predicted == "clear")
        result["ambiguous_sent_to_review"] += int(case.outcome == "ambiguous" and predicted == "ambiguous")
    return result
