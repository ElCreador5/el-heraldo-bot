"""
El Heraldo - Bot de verificación, actividad y Miembro de la Semana (Paraíso)

1. VERIFICACIÓN DE EDAD (rol Sin Verificar)
   - Quien entra recibe el rol Sin Verificar y debe verificarse en 299s o es expulsado.
   - El Heraldo arma un respaldo de 300s (SIN_VERIFICAR_WINDOW): si esa expulsión no
     ocurre, expulsa directo, sin DM.

2. VERIFICACIÓN DE ORIENTACIÓN (Tentad@ -> rol de orientación)
   - Tentad@ (TENTADO_ROLE_ID) se otorga al pasar la verificación de edad (botón de
     /verify).
   - El Heraldo arma un timer de 10 min (VERIFICATION_WINDOW). Si vence sin que el
     miembro tenga ninguno de los EVAL_ROLE_IDS:
       - 1ra vez (dm_sent=False): DM de recuperación + invite de uso único, luego kick.
       - 2da vez (dm_sent=True):
           - Si reingresó con el mismo invite de entrada original -> otra oportunidad
             (mismo flujo que la 1ra vez).
           - Si no -> kick directo, sin DM.
   - El tracking de invites es por usuario (no un invite genérico), comparando el
     contador de usos de cada invite del servidor antes/después de cada join.
   - /heraldo_check y /heraldo_check_all fuerzan la evaluación manual (individual o
     de todo el servidor) sin esperar los timers.

3. ACTIVIDAD Y PERFIL (/profile)
   - Cuenta mensajes y racha diaria por miembro (zona horaria STREAK_TZ, RD).
   - /profile muestra avatar, nombre, mensajes, racha y roles del miembro.

4. MIEMBRO DE LA SEMANA
   - Ranking semanal de mensajes (week_messages); cada jueves (configurable) se
     anuncia al más activo, sin asignar ningún rol, y se resetean los contadores
     de TODOS los miembros.
   - /motw_set_schedule y /motw_set_channel cambian día/hora/canal sin redeploy.
   - /motw_test dispara el anuncio con datos reales sin resetear contadores.

5. VERIFICACIÓN POR BOTÓN (/verify)
   - /verify publica un panel con un botón; quien lo pulsa recibe el rol de
     verificación (por defecto Tentad@) y pierde Sin Verificar. Es una declaración
     de mayoría de edad, no una comprobación.
   - Con la verificación activada, quien no la complete dentro de `timeout` (configurable
     en días/horas/minutos) desde que entra sufre la acción configurada.
   - /verify_config (rol, timeout, acción, activar) y /verify_texts (mensaje del
     panel, texto del botón y mensaje tras verificarse) configuran todo sin redeploy.

6. COPIA DE SEGURIDAD DE LA PLANTILLA (/template_config, /template_sync)
   - Sincroniza la plantilla del servidor (roles, canales y permisos) con su estado
     actual, como una copia de seguridad: cada día, semana o mes, o cada intervalo
     configurable en días/horas/minutos, con
     día y hora a elección. Tras cada copia manda el enlace por mensaje privado (si no
     puede, deja constancia en el canal de logs, sin el enlace).
   - /template_sync la hace al momento y muestra el enlace.

7. CONDENAS / HONEYPOT
   - El rol Condenado es la fuente de verdad. /condenar, el honeypot, una reacción ☠️ de un
     administrador o la asignación manual del rol activan el mismo proceso: se guardan los
     roles, se quitan los roles asignables (incluidos Tentad@ y Sin Verificar), se aplica Condenado,
     se pausa la evaluación de verificación y se excluye actividad/Miembro de la Semana.
   - /liberar devuelve los roles guardados; /condenados muestra motivo, origen, inicio y caducidad.
   - Las condenas tienen duración opcional, sobreviven reinicios y sobreviven a una salida/reentrada.
   - /honeypot release deja de existir para evitar dos motores de liberación distintos.
   - La reacción ☠️ solo la procesan administradores.
   - Quien tenga una condena activa no puede usar el botón de verificación; al reiniciar, el Heraldo
     reconcilia el rol con la base de datos (libera o reaplica según corresponda).
   - Los cambios de rol del propio Heraldo no vuelven a disparar el proceso (guardia con periodo de gracia).
   - Aviso privado al condenado y anuncio opcional en el canal configurado con /condenar_config.

8. PURGA (/purge)
   - Borra mensajes de un usuario sin límites: todos, sus N más recientes o un rango de tiempo
     (desde/hasta), en todo el servidor o en un canal/hilo. "Todos" pide confirmación.

9. RAID PROTECTION (/raid)
   - Detecta ingresos masivos (X miembros en Y segundos), activa el modo raid durante un tiempo
     configurable (segundos a meses) y aplica una acción a los sospechosos: condenar (por defecto,
     reversible, mismo motor que el honeypot), expulsar, banear o solo registrar.
   - Pausa las invitaciones del servidor mientras dure (y las reabre solo si las pausó el Heraldo),
     purga los mensajes de los sancionados desde que entraron y avisa en el canal de logs con ping opcional.
   - Filtro opcional de edad de cuenta; staff y bots nunca se sancionan. El estado sobrevive reinicios.
   - /raid config, /raid status, /raid start (manual), /raid end (con opción de liberar a los condenados).

10. VARIABLES (/variables)
   - Los textos personalizables aceptan {usuario}, {servidor}, {servericon}, {miembros}, {canal},
     {fecha}… (también ${nombre}), y búsquedas por nombre/ID: {#canal}, {@rol}, {emoji:nombre}.
   - No distinguen mayúsculas, tildes ni separadores. Lo desconocido se deja tal cual.
   - Se aplican al panel y DM de verificación, al mensaje tras verificarse y al aviso del honeypot.
     /variables lista todas; /variables texto:… prueba un texto con datos reales.

11. RESPUESTAS SIEMPRE EN EMBED
   - Todo lo que el Heraldo envía o edita sale como embed (el texto plano se convierte) con el
     footer {servidor} + {servericon}. Los embeds con pie propio configurado lo conservan.
     Se cambia en GLOBAL_FOOTER_TEXT / GLOBAL_FOOTER_ICON.

12. AUTOCOMPLETADO DE VARIABLES
   - Al escribir "{" en los parámetros de texto (/variables, /verify_dm_texts) Discord sugiere las
     variables; tras "{#", "{@" o "{emoji:" sugiere canales, roles/miembros o emojis. Límite de Discord:
     el texto resultante no puede pasar de 100 caracteres; los formularios (modales) no lo admiten.

13. EMBEDS PERSONALIZADOS (/embed)
   - /embed crear abre un formulario; luego un panel con botones sigue la edición (contenido, autor y
     pie, campos, fecha) también con formularios. Todos los textos aceptan variables.
   - /embed editar | enviar | lista | borrar. Los embeds se guardan por nombre y los mensajes ya
     enviados se actualizan solos al editarlos.

Toda la actividad relevante se reporta como embed en el canal de logs
(LOG_CHANNEL_ID por defecto; cambiable con /heraldo_log_channel).
Persistencia: SQLite (DB_PATH; en Railway, un Volume para sobrevivir deploys).
Permisos requeridos: Administrador (bot personal, confirmado por el usuario).
"""

import asyncio
import contextvars
from collections import deque
import json
import os
import re
import sqlite3
import sys
import tempfile
import time
import traceback
import unicodedata
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional, Union

import discord
from discord.ext import commands, tasks

# ---------------------------------------------------------------------------
# Configuración
# ---------------------------------------------------------------------------

SIN_VERIFICAR_ROLE_ID = 1549913794296414339  # rol Sin Verificar: verificación de edad pendiente
SIN_VERIFICAR_WINDOW = timedelta(seconds=300)  # respaldo: expulsa a los 300s a quien siga con Sin Verificar
TENTADO_ROLE_ID = 1510692050889085142
EVAL_ROLE_IDS = {
    1522877846026981396,  # Bisex-🚻
    1522875944371486780,  # Gay🥒
    1522877558893580298,  # Curios@ 👀
    1522876908935581846,  # Chico + Hetero 🍆
    1549502828563665056,  # Chica + Hetero 🍓
    1522878005104345218,   # Chica Trans 🌶️
    1549500856515166238,  # Chico Trans 🍓
}
RECOVERY_CHANNEL_ID = 1522863826545016913  # canal donde se genera el invite de recuperación
LOG_CHANNEL_ID = 1549052747117240381  # canal de logs por defecto (cambiable con /heraldo_log_channel)
CONDEMNED_CHANNEL_ID = 0  # configurable con /condenar_config; 0 = sin canal de avisos
CONDEMNED_EMOJI = "☠️"
CONDEMNATION_MAX_MINUTES = 10 * 365 * 24 * 60
VERIFICATION_WINDOW = timedelta(minutes=10)

# --- Tarjeta de condena ----------------------------------------------------
# Todo el contenido está persistido en `meta`, por lo que se puede cambiar sin redeploy.
CONDEMNATION_TEMPLATE_DEFAULTS = {
    "title": "☠️ RESOLUCIÓN DE CONDENA",
    "description": "Se ha aplicado una condena a {usuario}. A continuación se detalla el caso registrado.",
    "color": "8B0000",
    "footer": "El Heraldo 🪽 · {servidor}",
    "label_case": "Expediente",
    "label_message": "Evidencia / mensaje",
    "label_user": "Condenado",
    "label_by": "Condenó",
    "label_reason": "Qué hizo / Motivo",
    "label_when": "Cuándo",
    "label_where": "Dónde ocurrió",
    "label_duration": "Duración",
    "label_origin": "Origen",
    "label_roles": "Roles retirados",
    "button_label": "🔎 Ver información del caso",
    "button_url": "",
}


# --- Perfil (/profile): mensajes y racha diaria ---
# Roles cuyos mensajes NO cuentan para el perfil.
# Ejemplo: {123456789012345678, 987654321098765432}
EXCLUDED_ROLE_IDS: set[int] = set()
# Zona horaria que define el "día" de la racha. República Dominicana = UTC-4, sin horario de verano.
STREAK_TZ = timezone(timedelta(hours=-4))
PROFILE_MAX_ROLES = 10  # máximo de roles mostrados en la tarjeta

# --- Miembro de la Semana ---
# Solo anuncio, sin rol. Canal, día y hora se cambian con /motw_set_channel y /motw_set_schedule;
# con este ID en 0 y sin canal elegido, la función queda desactivada.
MOTW_CHANNEL_ID = 1555606764278382722  # canal por defecto (cambiable con /motw_set_channel)
MOTW_WEEKDAY_DEFAULT = 3  # día por defecto: 0=lunes ... 3=jueves ... 6=domingo
MOTW_HOUR_DEFAULT = 9  # hora por defecto (hora local de STREAK_TZ)
MOTW_WEEKDAY_NAMES = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]

# --- Verificación por botón (/verify) ---
# Rol, timeout, acción, textos y activación se guardan en la DB y se cambian con
# /verify_config y /verify_texts; estos son solo los valores por defecto.
VERIFY_BUTTON_ID = "heraldo_verify"
VERIFY_TIMEOUT_DEFAULT = 299  # segundos desde que entra
VERIFY_ACTION_DEFAULT = "kick"
VERIFY_ACTION_LABELS = {"kick": "Expulsar", "ban": "Banear", "none": "Solo registrar (sin acción)"}
VERIFY_PANEL_TEXT_DEFAULT = "✅ Pulsa el botón de abajo para confirmar que eres mayor de edad y obtener acceso al servidor."
VERIFY_BUTTON_LABEL_DEFAULT = "Verificar"
VERIFY_SUCCESS_TEXT_DEFAULT = "✅ ¡Verificado! Ya tienes acceso al servidor."
# Permisos que un rol de verificación NO puede tener: lo otorga un botón que pulsa cualquiera.
VERIFY_DANGEROUS_PERMS = (
    ("administrator", "Administrador"),
    ("manage_guild", "Gestionar servidor"),
    ("manage_roles", "Gestionar roles"),
    ("manage_channels", "Gestionar canales"),
    ("manage_webhooks", "Gestionar webhooks"),
    ("kick_members", "Expulsar miembros"),
    ("ban_members", "Banear miembros"),
    ("moderate_members", "Aislar miembros"),
    ("manage_messages", "Gestionar mensajes"),
    ("mention_everyone", "Mencionar a todos"),
)

# --- Copia de seguridad de la plantilla del servidor (/template_config) ---
# Valores por defecto; la configuración real se guarda en la DB. Hora local de STREAK_TZ.
TEMPLATE_MODE_LABELS = {
    "off": "Desactivada",
    "daily": "Cada día",
    "weekly": "Cada semana",
    "monthly": "Cada mes",
    "interval": "Cada X horas",
}
TEMPLATE_HOUR_DEFAULT = 4  # madrugada
TEMPLATE_WEEKDAY_DEFAULT = 6  # domingo
TEMPLATE_MONTHDAY_DEFAULT = 1
TEMPLATE_INTERVAL_DEFAULT = 24  # horas

DM_TEXT = (
    "¡Hola! Fuiste expulsado del Paraíso porque no seleccionaste tu rol de "
    "orientación. Al volver a entrar, busca en el canal de roles el embed que "
    "dice \"Orientación\" y elige el que te represente — estos roles son "
    "importantes: nos ayudan a confirmar que eres una persona real y son los "
    "que te dan acceso al contenido del servidor. (El rol de verificación de "
    "edad es algo aparte — ese solo confirma que eres mayor de edad, no "
    "sustituye este paso). Si quieres volver a intentarlo, aquí tienes otra "
    "oportunidad: {invite_url}"
)

# En Railway apunta al Volume (variable DB_PATH=/data/heraldo.db) para que los datos
# sobrevivan a los deploys. Sin la variable, usa un archivo local (pruebas en PC).
DB_PATH = os.environ.get("DB_PATH", "heraldo.db")

intents = discord.Intents.default()
intents.members = True
intents.guilds = True
# Opcional: permite guardar el texto del mensaje como evidencia del honeypot.
# Requiere activar "Message Content Intent" en el portal de desarrolladores.
intents.message_content = os.environ.get("MESSAGE_CONTENT_INTENT") == "1"

bot = commands.Bot(command_prefix="!heraldo ", intents=intents)

# invite_cache[guild_id][invite_code] = uses
invite_cache: dict[int, dict[str, int]] = {}


async def log_embed(
    guild: discord.Guild | None,
    title: str,
    description: str,
    color: discord.Color = discord.Color.blurple(),
) -> None:
    """Reporta actividad de El Heraldo en el canal de logs como embed. Nunca debe
    tumbar el flujo principal si falla (canal no encontrado, sin permisos, etc.)."""
    print(f"{title} — {description}")
    if guild is None:
        return
    channel = guild.get_channel(get_log_channel_id())
    if channel is None:
        return
    embed = discord.Embed(
        title=title,
        description=description,
        color=color,
        timestamp=datetime.now(timezone.utc),
    )
    try:
        await channel.send(embed=embed)
    except discord.Forbidden:
        print("Sin permisos para escribir en el canal de logs")


# ---------------------------------------------------------------------------
# Persistencia
# ---------------------------------------------------------------------------

def db_init() -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS members (
            user_id INTEGER PRIMARY KEY,
            entry_invite TEXT,
            tentado_at TEXT,
            dm_sent INTEGER DEFAULT 0,
            verification_dm_sent INTEGER DEFAULT 0
        )
        """
    )
    try:
        conn.execute("ALTER TABLE members ADD COLUMN sin_verificado_at TEXT")
    except sqlite3.OperationalError:
        pass  # la columna ya existe (bots reiniciados sobre una DB previa)
    try:
        conn.execute("ALTER TABLE members ADD COLUMN verify_pending_at TEXT")
    except sqlite3.OperationalError:
        pass  # la columna ya existe
    try:
        conn.execute("ALTER TABLE members ADD COLUMN verification_dm_sent INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass  # la columna ya existe
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS activity (
            user_id INTEGER PRIMARY KEY,
            messages INTEGER NOT NULL DEFAULT 0,
            streak INTEGER NOT NULL DEFAULT 0,
            last_active_day TEXT
        )
        """
    )
    try:
        conn.execute("ALTER TABLE activity ADD COLUMN week_messages INTEGER NOT NULL DEFAULT 0")
    except sqlite3.OperationalError:
        pass  # la columna ya existe
    conn.execute(
        "CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT)"
    )
    conn.commit()
    conn.close()


def db_get(user_id: int) -> sqlite3.Row | None:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        "SELECT * FROM members WHERE user_id = ?", (user_id,)
    ).fetchone()
    conn.close()
    return row


def db_upsert_join(user_id: int, invite_code: str | None) -> None:
    """Registra o actualiza el invite de entrada de un usuario al unirse."""
    row = db_get(user_id)
    conn = sqlite3.connect(DB_PATH)
    if row is None:
        conn.execute(
            "INSERT INTO members (user_id, entry_invite, dm_sent) VALUES (?, ?, 0)",
            (user_id, invite_code),
        )
    else:
        # Reingreso: si usó el mismo invite original, se le resetea dm_sent
        # para darle otra oportunidad; si no, se conserva el estado previo.
        if row["entry_invite"] and invite_code == row["entry_invite"]:
            conn.execute(
                "UPDATE members SET dm_sent = 0 WHERE user_id = ?", (user_id,)
            )
        # si entry_invite era NULL (primer registro sin invite detectado), lo fija ahora
        if row["entry_invite"] is None:
            conn.execute(
                "UPDATE members SET entry_invite = ? WHERE user_id = ?",
                (invite_code, user_id),
            )
    conn.commit()
    conn.close()


def db_set_tentado(user_id: int, when: datetime) -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "UPDATE members SET tentado_at = ? WHERE user_id = ?",
        (when.isoformat(), user_id),
    )
    conn.commit()
    conn.close()


def db_mark_dm_sent(user_id: int) -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "UPDATE members SET dm_sent = 1 WHERE user_id = ?", (user_id,)
    )
    conn.commit()
    conn.close()


def db_verification_dm_sent(user_id: int) -> bool:
    row = db_get(user_id)
    return bool(row and row["verification_dm_sent"])


def db_mark_verification_dm_sent(user_id: int) -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "UPDATE members SET verification_dm_sent = 1 WHERE user_id = ?", (user_id,)
    )
    conn.commit()
    conn.close()


def db_clear_tentado(user_id: int) -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "UPDATE members SET tentado_at = NULL WHERE user_id = ?", (user_id,)
    )
    conn.commit()
    conn.close()


def db_set_sin_verificado(user_id: int, when: datetime) -> None:
    """Upsert: la fila puede no existir todavía si Sin Verificar se asigna
    antes de que on_member_join termine de registrar el join."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        INSERT INTO members (user_id, sin_verificado_at, dm_sent) VALUES (?, ?, 0)
        ON CONFLICT(user_id) DO UPDATE SET sin_verificado_at = excluded.sin_verificado_at
        """,
        (user_id, when.isoformat()),
    )
    conn.commit()
    conn.close()


def db_clear_sin_verificado(user_id: int) -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "UPDATE members SET sin_verificado_at = NULL WHERE user_id = ?", (user_id,)
    )
    conn.commit()
    conn.close()


def db_set_verify_pending(user_id: int, when: datetime) -> None:
    """Upsert: marca desde cuándo corre el timeout de verificación del miembro."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        INSERT INTO members (user_id, verify_pending_at, dm_sent) VALUES (?, ?, 0)
        ON CONFLICT(user_id) DO UPDATE SET verify_pending_at = excluded.verify_pending_at
        """,
        (user_id, when.isoformat()),
    )
    conn.commit()
    conn.close()


def db_clear_verify_pending(user_id: int) -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "UPDATE members SET verify_pending_at = NULL WHERE user_id = ?", (user_id,)
    )
    conn.commit()
    conn.close()


def db_track_message(user_id: int, today: str, yesterday: str) -> None:
    """Suma 1 mensaje y actualiza la racha diaria (días en formato YYYY-MM-DD)."""
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute(
        "SELECT messages, streak, last_active_day FROM activity WHERE user_id = ?",
        (user_id,),
    ).fetchone()
    if row is None:
        conn.execute(
            "INSERT INTO activity (user_id, messages, streak, last_active_day, week_messages) "
            "VALUES (?, 1, 1, ?, 1)",
            (user_id, today),
        )
    else:
        messages, streak, last_active = row
        if last_active != today:
            # Ayer -> la racha continúa; cualquier otra cosa -> empieza de nuevo.
            streak = streak + 1 if last_active == yesterday else 1
            last_active = today
        conn.execute(
            "UPDATE activity SET messages = ?, streak = ?, last_active_day = ?, "
            "week_messages = week_messages + 1 WHERE user_id = ?",
            (messages + 1, streak, last_active, user_id),
        )
    conn.commit()
    conn.close()


def db_get_activity(user_id: int) -> tuple[int, int, str | None]:
    """Devuelve (mensajes, racha guardada, último día activo)."""
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute(
        "SELECT messages, streak, last_active_day FROM activity WHERE user_id = ?",
        (user_id,),
    ).fetchone()
    conn.close()
    return (row[0], row[1], row[2]) if row else (0, 0, None)


def db_week_ranking() -> list[tuple[int, int]]:
    """[(user_id, mensajes_de_la_semana)] de mayor a menor. En empate, gana el
    user_id menor (cuenta más antigua) para que el resultado sea determinista."""
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT user_id, week_messages FROM activity WHERE week_messages > 0 "
        "ORDER BY week_messages DESC, user_id ASC"
    ).fetchall()
    conn.close()
    return [(r[0], r[1]) for r in rows]


def db_zero_week_messages(user_id: int) -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.execute("UPDATE activity SET week_messages = 0 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()


def db_reset_week() -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.execute("UPDATE activity SET week_messages = 0")
    conn.commit()
    conn.close()


def db_meta_get(key: str) -> str | None:
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute("SELECT value FROM meta WHERE key = ?", (key,)).fetchone()
    conn.close()
    return row[0] if row else None


def db_meta_set(key: str, value: str) -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO meta (key, value) VALUES (?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        (key, value),
    )
    conn.commit()
    conn.close()


def get_motw_weekday() -> int:
    value = db_meta_get("motw_weekday")
    return int(value) if value is not None else MOTW_WEEKDAY_DEFAULT


def get_motw_hour() -> int:
    value = db_meta_get("motw_hour")
    return int(value) if value is not None else MOTW_HOUR_DEFAULT


def get_motw_channel_id() -> int:
    """Canal elegido con /motw_set_channel; si no hay, el MOTW_CHANNEL_ID por defecto."""
    value = db_meta_get("motw_channel_id")
    return int(value) if value is not None else MOTW_CHANNEL_ID


def set_motw_channel_id(channel_id: int) -> None:
    db_meta_set("motw_channel_id", str(channel_id))


def set_motw_schedule(weekday: int, hour: int) -> None:
    db_meta_set("motw_weekday", str(weekday))
    db_meta_set("motw_hour", str(hour))


def get_log_channel_id() -> int:
    """Canal elegido con /heraldo_log_channel; si no hay, el LOG_CHANNEL_ID por defecto."""
    value = db_meta_get("log_channel_id")
    return int(value) if value is not None else LOG_CHANNEL_ID


def set_log_channel_id(channel_id: int) -> None:
    db_meta_set("log_channel_id", str(channel_id))


def verify_enabled() -> bool:
    return db_meta_get("verify_enabled") == "1"


def get_verify_role_id() -> int:
    value = db_meta_get("verify_role_id")
    return int(value) if value is not None else TENTADO_ROLE_ID


def get_verify_timeout() -> int:
    """Devuelve el timeout en segundos. Las configuraciones antiguas siguen guardadas en segundos;
    las nuevas se guardan como duración d/h/m convertida a segundos."""
    value = db_meta_get("verify_timeout")
    return int(value) if value is not None else VERIFY_TIMEOUT_DEFAULT


def get_verify_action() -> str:
    value = db_meta_get("verify_action")
    return value if value in VERIFY_ACTION_LABELS else VERIFY_ACTION_DEFAULT


def get_verify_panel_text() -> str:
    return db_meta_get("verify_panel_text") or VERIFY_PANEL_TEXT_DEFAULT


def get_verify_button_label() -> str:
    return db_meta_get("verify_button_label") or VERIFY_BUTTON_LABEL_DEFAULT


def get_verify_success_text() -> str:
    return db_meta_get("verify_success_text") or VERIFY_SUCCESS_TEXT_DEFAULT


VERIFY_DM_TITLE_DEFAULT = "HAS CRUZADO EL UMBRAL"
VERIFY_DM_BODY_DEFAULT = (
    "Pero antes de que puedas perderte entre las puertas del paraíso, hay dos pasos que separan a los curiosos de los que realmente pertenecen:\n\n"
    "🔒 **Verifícate** en <#1547500809015660585> — sin esto, sigues del otro lado del portón.\n\n"
    "🎭 Luego, en <#1522863826545016913>, elige quién eres cuando nadie está mirando: Hetero, Curios@, Bi, Gay o Trans.\n\n"
    "Cada rol abre una puerta distinta. Elige bien.\n\n"
    "¿Dudas? <#1543412172158271560> te está esperando."
)
VERIFY_DM_FIELD_NAME_DEFAULT = "Este no es un lugar cualquiera"
VERIFY_DM_FOOTER_DEFAULT = "© Paraíso Morboso 🍑🍆🥛"
VERIFY_DM_COLOR_DEFAULT = "4F5BDC"
VERIFY_DM_FOOTER_ICON_DEFAULT = "https://media.discordapp.net/attachments/1548766637866360852/1548771260476162189/39d74668-f12d-4979-bcc3-9b6826f2e8d5.png?ex=6ac49d63&is=6ac34be3&hm=b939835c020aeea2d422d7057213117b1744d4f95d37d180e8f"

def get_verify_dm_title() -> str:
    return db_meta_get("verify_dm_title") or VERIFY_DM_TITLE_DEFAULT

def get_verify_dm_body() -> str:
    return db_meta_get("verify_dm_body") or VERIFY_DM_BODY_DEFAULT

def get_verify_dm_field_name() -> str:
    return db_meta_get("verify_dm_field_name") or VERIFY_DM_FIELD_NAME_DEFAULT

def get_verify_dm_footer() -> str:
    return db_meta_get("verify_dm_footer") or VERIFY_DM_FOOTER_DEFAULT

def get_verify_dm_color() -> str:
    return db_meta_get("verify_dm_color") or VERIFY_DM_COLOR_DEFAULT

def get_verify_dm_footer_icon() -> str:
    return db_meta_get("verify_dm_footer_icon") or VERIFY_DM_FOOTER_ICON_DEFAULT


def build_verification_welcome_embed(
    member: discord.Member | None = None, guild: discord.Guild | None = None,
) -> discord.Embed:
    ctx = VarContext(guild or (member.guild if member is not None else None), member)
    color_text = get_verify_dm_color().strip().lstrip("#")
    try:
        color_value = int(color_text, 16)
        if not 0 <= color_value <= 0xFFFFFF:
            raise ValueError
    except ValueError:
        color_value = int(VERIFY_DM_COLOR_DEFAULT, 16)

    embed = discord.Embed(
        title=render_vars(get_verify_dm_title(), ctx, 256),
        color=discord.Color(color_value),
    )
    embed.add_field(
        name=render_vars(get_verify_dm_field_name(), ctx, 256),
        value=render_vars(get_verify_dm_body(), ctx, 1024),
        inline=False,
    )
    footer_icon = render_url_var(get_verify_dm_footer_icon(), ctx)
    footer_text = render_vars(get_verify_dm_footer(), ctx, 2048)
    if footer_icon:
        embed.set_footer(text=footer_text, icon_url=footer_icon)
    else:
        embed.set_footer(text=footer_text)
    return embed


# ---------------------------------------------------------------------------
# Tracking de invites por usuario
# ---------------------------------------------------------------------------

async def refresh_invite_cache(guild: discord.Guild) -> None:
    invite_cache[guild.id] = {inv.code: inv.uses for inv in await guild.invites()}


async def detect_used_invite(guild: discord.Guild) -> str | None:
    """Compara el cache antes/después del join para saber qué invite subió su
    contador de usos. Debe llamarse ANTES de refrescar el cache."""
    before = invite_cache.get(guild.id, {})
    after = {inv.code: inv.uses for inv in await guild.invites()}
    used_code = None
    for code, uses in after.items():
        if uses > before.get(code, 0):
            used_code = code
            break
    invite_cache[guild.id] = after
    return used_code


_startup_done = False


@bot.event
@bot.event
async def on_ready() -> None:
    global _startup_done
    if _startup_done:
        return  # on_ready se repite en cada reconexión: no resincronizar comandos ni relanzar tareas
    db_init()
    honeypot_db_init()
    # Sistema de sugerencias: registra las vistas persistentes y recupera el panel/revisiones pendientes.
    try:
        await suggestions_startup()
    except Exception:
        traceback.print_exc()
    if not any(isinstance(view, VerifyView) for view in bot.persistent_views):
        bot.add_view(VerifyView())
    if not any(isinstance(view, CondemnationPardonView) for view in bot.persistent_views):
        bot.add_view(CondemnationPardonView())
    for guild in bot.guilds:
        await refresh_invite_cache(guild)
        # Un fallo al publicar comandos (p. ej. una descripción inválida) no debe impedir que
        # arranquen la verificación, el Miembro de la Semana ni la copia de la plantilla.
        try:
            bot.tree.copy_global_to(guild=guild)
            await bot.tree.sync(guild=guild)  # sync por guild: propagación instantánea
        except Exception:
            print(f"⚠️ No se pudieron sincronizar los comandos en {guild.name}:")
            traceback.print_exc()
    # Los comandos se publican solo por guild: cualquier comando global es un
    # huérfano de versiones anteriores (aparece duplicado en el selector). Se borra.
    try:
        for cmd in await bot.tree.fetch_commands():
            await cmd.delete()
            print(f"🧹 Comando global huérfano eliminado: /{cmd.name}")
    except discord.HTTPException as e:
        print(f"No se pudo limpiar comandos globales: {e}")
    if not condemnation_expiry_loop.is_running():
        condemnation_expiry_loop.start()
    if not raid_expiry_loop.is_running():
        raid_expiry_loop.start()
    if not check_pending_verifications.is_running():
        check_pending_verifications.start()
    for guild in bot.guilds:
        try:
            await condemnation_reconcile(guild)
        except Exception:
            traceback.print_exc()
    if get_motw_channel_id():
        if not member_of_the_week_loop.is_running():
            member_of_the_week_loop.start()
    else:
        print("ℹ️ Miembro de la Semana desactivado: configura MOTW_CHANNEL_ID o usa /motw_set_channel.")
    if not template_backup_loop.is_running():
        template_backup_loop.start()
    _startup_done = True
    print(f"El Heraldo conectado como {bot.user}")


@bot.event
async def on_member_join(member: discord.Member) -> None:
    if member.bot:
        return  # los bots no pasan por el flujo de verificación

    invite_code = await detect_used_invite(member.guild)
    db_upsert_join(member.id, invite_code)

    # Una condena activa tiene prioridad absoluta sobre los flujos de verificación.
    # El miembro puede salir y volver: la condena persiste en SQLite.
    condemnation = condemnation_get(member.id)
    if condemnation is not None and condemnation_is_expired(condemnation):
        condemnation_deactivate(member.id)  # caducó mientras estaba fuera: entra como cualquier miembro nuevo
        condemnation = None
    if condemnation is not None:
        db_clear_verify_pending(member.id)
        _condemn_sync_busy.add(member.id)
        try:
            ok, _, note = await condemnation_sync_roles(member, save_snapshot=False, reason="Reingreso con condena activa", role_id=condemnation_role_id(condemnation))
            if not ok:
                await log_embed(member.guild, "⚠️ No pude reaplicar la condena al reingresar", f"{member.mention}: {note}", discord.Color.orange())
                return
            await log_embed(
                member.guild, "☠️ Condena restaurada al reingresar",
                f"{member.mention} (`{member.id}`) volvió al servidor con una condena activa. "
                "Se restauró el rol Condenado y se evitó la evaluación de verificación.",
                discord.Color.dark_red(),
            )
        except Exception:
            traceback.print_exc()
        finally:
            _condemn_sync_busy.discard(member.id)
        return

    # Raid Protection: si este ingreso dispara o cae dentro de un raid y ya fue sancionado,
    # no pasa por la verificación.
    try:
        if await raid_handle_join(member):
            db_clear_verify_pending(member.id)
            return
    except Exception:
        traceback.print_exc()

    if verify_enabled():
        now = datetime.now(timezone.utc)
        db_set_verify_pending(member.id, now)
        asyncio.create_task(schedule_verify_timeout(member.guild.id, member.id, now))


# ---------------------------------------------------------------------------
# Detección del rol Tentad@ y verificación a los 10 min
# ---------------------------------------------------------------------------

@bot.event
async def on_raw_message_delete(payload: discord.RawMessageDeleteEvent) -> None:
    # Si alguien borra el panel de sugerencias, el Heraldo lo vuelve a publicar y fijar.
    try:
        await suggestion_panel_deleted(payload.guild_id, payload.message_id)
    except Exception:
        traceback.print_exc()


@bot.event
async def on_member_update(before: discord.Member, after: discord.Member) -> None:
    if after.bot:
        return  # los bots no pasan por el flujo de verificación
    if after.id in _condemn_sync_busy:
        return

    before_role_ids = {r.id for r in before.roles}
    after_role_ids = {r.id for r in after.roles}
    active_condemnation = condemnation_get(after.id)
    condemned_id = condemnation_role_id(active_condemnation)
    had_condemned = bool(condemned_id and condemned_id in before_role_ids)
    has_condemned = bool(condemned_id and condemned_id in after_role_ids)

    # El rol Condenado es la fuente de verdad: si se quita por cualquier medio, se libera.
    if had_condemned and not has_condemned and active_condemnation is not None:
        _condemn_sync_busy.add(after.id)
        try:
            await release_condemned_member(after, automatic=False)
        finally:
            _condemn_sync_busy.discard(after.id)
        return

    # Si alguien asigna Condenado a mano, se ejecuta exactamente el mismo proceso.
    if has_condemned and not had_condemned and active_condemnation is None:
        actor = None
        try:
            async for entry in after.guild.audit_logs(limit=8, action=discord.AuditLogAction.member_role_update):
                if entry.target and entry.target.id == after.id and (datetime.now(timezone.utc) - entry.created_at).total_seconds() < 20:
                    actor = entry.user
                    break
        except (discord.Forbidden, discord.HTTPException):
            pass
        _condemn_sync_busy.add(after.id)
        try:
            protection = condemnation_protection_reason(after)
            if protection:
                role = after.guild.get_role(condemned_id)
                if role is not None and role in after.roles and role.is_assignable():
                    await after.remove_roles(role, reason=f"Condena no permitida: {protection}")
                await log_embed(after.guild, "⚠️ Condena rechazada", f"{after.mention}: {protection}.", discord.Color.orange())
            else:
                await condemn_member(
                    after,
                    reason="El rol Condenado fue otorgado manualmente.",
                    duration_minutes=None,
                    purge_spec=hp_purge_spec(),
                    origin="role",
                    applied_by=actor,
                    preserve_role_ids=list(before_role_ids),
                )
        finally:
            _condemn_sync_busy.discard(after.id)
        return

    # Si ya estaba condenado y otro moderador/bot añade roles, se vuelven a quitar.
    if active_condemnation is not None and has_condemned:
        added_assignable = any(
            r.id not in before_role_ids and r.id != condemned_id and r.is_assignable() and not r.managed
            for r in after.roles
        )
        if added_assignable:
            new_ids = [
                r.id for r in after.roles
                if r.id not in before_role_ids and r.id != condemned_id and r.is_assignable() and not r.managed
            ]
            _condemn_sync_busy.add(after.id)
            try:
                ok, _, note = await condemnation_sync_roles(
                    after, save_snapshot=False, reason="Condenado: no puede recibir otros roles",
                    role_id=condemned_id,
                )
                if ok:
                    condemnation_add_saved_roles(after.id, new_ids)
                else:
                    await log_embed(after.guild, "⚠️ No pude re-quitar roles a un condenado", f"{after.mention}: {note}", discord.Color.orange())
            except Exception:
                traceback.print_exc()
            finally:
                _condemn_sync_busy.discard(after.id)
        db_clear_tentado(after.id)
        db_clear_sin_verificado(after.id)
        db_clear_verify_pending(after.id)
        return

    # Flujos normales de verificación; una condena activa ya salió por arriba.
    if SIN_VERIFICAR_ROLE_ID in after_role_ids and SIN_VERIFICAR_ROLE_ID not in before_role_ids:
        now = datetime.now(timezone.utc)
        db_set_sin_verificado(after.id, now)
        asyncio.create_task(schedule_sin_verificado_check(after.guild.id, after.id, now))
        print(f"⏳ {after} recibió Sin Verificar — respaldo de 300s armado.")

    if TENTADO_ROLE_ID in after_role_ids and TENTADO_ROLE_ID not in before_role_ids:
        now = datetime.now(timezone.utc)
        db_set_tentado(after.id, now)
        asyncio.create_task(schedule_check(after.guild.id, after.id, now))
        print(f"⏳ {after} recibió Tentad@ — timer de 10 min armado.")


async def schedule_sin_verificado_check(guild_id: int, user_id: int, marked_at: datetime) -> None:
    delay = (marked_at + SIN_VERIFICAR_WINDOW - datetime.now(timezone.utc)).total_seconds()
    if delay > 0:
        await asyncio.sleep(delay)
    await evaluate_sin_verificado(guild_id, user_id)


async def evaluate_sin_verificado(guild_id: int, user_id: int) -> None:
    """Respaldo del timeout de Sin Verificar (299s). Si a los 300s el
    miembro sigue con Sin Verificar, se expulsa directo — sin DM."""
    if condemnation_get(user_id) is not None:
        db_clear_sin_verificado(user_id)
        return
    guild = bot.get_guild(guild_id)
    if guild is None:
        return
    member = guild.get_member(user_id)
    if member is None:
        db_clear_sin_verificado(user_id)  # ya lo expulsaron — nada que hacer
        return

    if SIN_VERIFICAR_ROLE_ID not in {r.id for r in member.roles}:
        db_clear_sin_verificado(user_id)  # ya verificó a tiempo
        return

    db_clear_sin_verificado(user_id)
    try:
        await member.kick(reason="No se verificó (respaldo del timeout)")
        await log_embed(
            guild, "👢 Kick — No se verificó",
            f"{member.mention} (`{member.id}`) — no se verificó dentro del tiempo límite. "
            f"(Respaldo: no fue expulsado antes por el timeout.)",
            discord.Color.red(),
        )
    except discord.Forbidden:
        await log_embed(
            guild, "⚠️ Error al expulsar",
            f"Sin permisos para expulsar a {member.mention} (Sin Verificar) — revisa jerarquía de roles.",
            discord.Color.dark_red(),
        )


async def schedule_check(guild_id: int, user_id: int, tentado_at: datetime) -> None:
    delay = (tentado_at + VERIFICATION_WINDOW - datetime.now(timezone.utc)).total_seconds()
    if delay > 0:
        await asyncio.sleep(delay)
    await evaluate_member(guild_id, user_id)


@tasks.loop(minutes=2)
async def check_pending_verifications() -> None:
    """Red de seguridad: si el bot se reinició, retoma verificaciones pendientes
    cuyo timer ya venció o está por vencer (ambos flujos: Sin Verificar y Tentad@)."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT user_id, tentado_at, sin_verificado_at, verify_pending_at FROM members "
        "WHERE tentado_at IS NOT NULL OR sin_verificado_at IS NOT NULL "
        "OR verify_pending_at IS NOT NULL"
    ).fetchall()
    conn.close()

    now = datetime.now(timezone.utc)
    verify_window = timedelta(seconds=get_verify_timeout())
    for row in rows:
        if row["tentado_at"] is not None:
            tentado_at = datetime.fromisoformat(row["tentado_at"])
            if now >= tentado_at + VERIFICATION_WINDOW:
                for guild in bot.guilds:
                    if guild.get_member(row["user_id"]):
                        await evaluate_member(guild.id, row["user_id"])
                        break
                else:
                    db_clear_tentado(row["user_id"])  # ya no está en ningún servidor
        if row["sin_verificado_at"] is not None:
            sin_verificado_at = datetime.fromisoformat(row["sin_verificado_at"])
            if now >= sin_verificado_at + SIN_VERIFICAR_WINDOW:
                for guild in bot.guilds:
                    if guild.get_member(row["user_id"]):
                        await evaluate_sin_verificado(guild.id, row["user_id"])
                        break
                else:
                    db_clear_sin_verificado(row["user_id"])
        if row["verify_pending_at"] is not None:
            verify_pending_at = datetime.fromisoformat(row["verify_pending_at"])
            if now >= verify_pending_at + verify_window:
                for guild in bot.guilds:
                    if guild.get_member(row["user_id"]):
                        await evaluate_verify_timeout(guild.id, row["user_id"])
                        break
                else:
                    db_clear_verify_pending(row["user_id"])  # ya no está en ningún servidor


async def evaluate_member(guild_id: int, user_id: int, report: bool = True) -> str:
    """Devuelve 'verificado', 'expulsado', 'castigado' o 'ausente'/'sin-guild'."""
    if condemnation_get(user_id) is not None:
        db_clear_tentado(user_id)
        return "castigado"
    guild = bot.get_guild(guild_id)
    if guild is None:
        return "sin-guild"
    member = guild.get_member(user_id)
    if member is None:
        db_clear_tentado(user_id)  # ya no está, nada que hacer
        return "ausente"

    punish_id = hp_punish_role_id()
    if punish_id and any(r.id == punish_id for r in member.roles):
        db_clear_tentado(user_id)  # castigado por el honeypot: no se expulsa por falta de orientación
        return "castigado"

    role_ids = {r.id for r in member.roles}
    if role_ids & EVAL_ROLE_IDS:
        db_clear_tentado(user_id)  # se verificó a tiempo
        if report:
            await log_embed(guild, "✅ Verificado", f"{member.mention} eligió un buen camino.", discord.Color.green())
        return "verificado"

    await expel(member, report=report)
    return "expulsado"


# ---------------------------------------------------------------------------
# Expulsión + DM condicional
# ---------------------------------------------------------------------------

async def expel(member: discord.Member, report: bool = True) -> None:
    row = db_get(member.id)
    dm_sent_before = bool(row["dm_sent"]) if row else False
    is_first_fault = not dm_sent_before

    dm_ok = None  # None = no aplica (2da falta, no se intenta DM)
    if is_first_fault:
        dm_ok = await send_recovery_dm(member, report=report)
        db_mark_dm_sent(member.id)

    db_clear_tentado(member.id)
    try:
        await member.kick(reason="No seleccionó rol de verificación en 10 min")
        kicked = True
    except discord.Forbidden:
        kicked = False

    if not report:
        return

    embed = discord.Embed(
        title="👢 Kick — Falta de verificación",
        color=discord.Color.red() if kicked else discord.Color.dark_red(),
        timestamp=datetime.now(timezone.utc),
    )
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.add_field(name="Usuario", value=f"{member.mention} (`{member.id}`)", inline=False)
    embed.add_field(
        name="Razón",
        value="No definió su rol dentro de los 10 min tras recibir **Tentad@**.",
        inline=False,
    )
    embed.add_field(name="Falta", value="1ra — se le dio otra oportunidad" if is_first_fault else "2da — sin nueva oportunidad", inline=True)
    if dm_ok is not None:
        embed.add_field(name="DM de recuperación", value="✅ Enviado" if dm_ok else "⚠️ Falló (DMs cerrados)", inline=True)
    embed.add_field(name="Resultado", value="✅ Expulsado" if kicked else "⚠️ Falló — revisa jerarquía de roles", inline=True)
    embed.set_footer(text="Paraíso Morboso 2026 © - El Heraldo 🪽")

    channel = member.guild.get_channel(get_log_channel_id())
    if channel is not None:
        try:
            await channel.send(embed=embed)
        except discord.Forbidden:
            print("Sin permisos para escribir en el canal de logs")


async def send_recovery_dm(member: discord.Member, report: bool = True) -> bool:
    """Devuelve True si el DM se envió con éxito."""
    channel = member.guild.get_channel(RECOVERY_CHANNEL_ID)
    invite_url = ""
    if channel is not None:
        try:
            invite = await channel.create_invite(
                max_uses=1, unique=True, reason="Recuperación tras expulsión de Heraldo"
            )
            invite_url = invite.url
        except discord.Forbidden:
            if report:
                await log_embed(member.guild, "⚠️ Error de invite", "Sin permisos para crear invite de recuperación.", discord.Color.dark_red())

    text = DM_TEXT.format(invite_url=invite_url)
    try:
        await member.send(text)
        return True
    except discord.Forbidden:
        return False


# ---------------------------------------------------------------------------
# Comando manual de prueba (slash command — no requiere message_content intent)
# ---------------------------------------------------------------------------

@bot.tree.command(name="heraldo_check", description="Fuerza la evaluación inmediata de un miembro (sin esperar el timer de 10 min).")
@discord.app_commands.checks.has_permissions(kick_members=True)
async def heraldo_check(interaction: discord.Interaction, user: discord.User) -> None:
    try:
        member = await interaction.guild.fetch_member(user.id)
    except discord.NotFound:
        await interaction.response.send_message(f"{user} no está en el servidor.", ephemeral=True)
        return

    await interaction.response.send_message(f"Evaluando a {member}...", ephemeral=True)
    await log_embed(
        interaction.guild, "🔧 Chequeo manual",
        f"Solicitado por {interaction.user.mention} sobre {member.mention}.",
        discord.Color.blurple(),
    )
    await evaluate_member(interaction.guild.id, member.id)


@heraldo_check.error
async def heraldo_check_error(interaction: discord.Interaction, error: discord.app_commands.AppCommandError) -> None:
    if isinstance(error, discord.app_commands.MissingPermissions):
        await interaction.response.send_message("No tienes permiso para usar este comando.", ephemeral=True)
    else:
        await interaction.response.send_message(f"Error: {error}", ephemeral=True)


@bot.tree.command(name="heraldo_check_all", description="Fuerza la evaluación inmediata de TODOS los miembros que tengan Tentad@.")
@discord.app_commands.checks.has_permissions(kick_members=True)
async def heraldo_check_all(interaction: discord.Interaction) -> None:
    guild = interaction.guild
    await interaction.response.send_message("Revisando a todos los miembros con Tentad@... esto puede tardar un poco.", ephemeral=True)
    await log_embed(guild, "🔍 Chequeo masivo iniciado", f"Solicitado por {interaction.user.mention}.", discord.Color.blurple())

    verified = 0
    expelled: list[discord.Member] = []
    expelled_sin_verificar: list[discord.Member] = []

    async for member in guild.fetch_members(limit=None):
        if member.bot or condemnation_get(member.id) is not None:
            continue  # los condenados quedan fuera de toda evaluación
        role_ids = {r.id for r in member.roles}
        if TENTADO_ROLE_ID in role_ids:
            status = await evaluate_member(guild.id, member.id, report=False)
            if status == "verificado":
                verified += 1
            elif status == "expulsado":
                expelled.append(member)
            await asyncio.sleep(1)  # evitar ráfagas contra el rate limit de Discord
        elif SIN_VERIFICAR_ROLE_ID in role_ids:
            db_clear_sin_verificado(member.id)
            try:
                await member.kick(reason="No se verificó")
                expelled_sin_verificar.append(member)
            except discord.Forbidden:
                await log_embed(
                    guild, "⚠️ Error al expulsar",
                    f"Sin permisos para expulsar a {member.mention} (Sin Verificar) — revisa jerarquía de roles.",
                    discord.Color.dark_red(),
                )
            await asyncio.sleep(1)

    embed = discord.Embed(
        title="🔍 Chequeo masivo completado",
        description=(
            f"✅ **{verified}** verificado(s) a tiempo.\n"
            f"👢 **{len(expelled)}** expulsado(s) por falta de rol de orientación.\n"
            f"👢 **{len(expelled_sin_verificar)}** expulsado(s) por no verificarse (Sin Verificar)."
        ),
        color=discord.Color.blurple(),
        timestamp=datetime.now(timezone.utc),
    )

    def add_mention_fields(embed: discord.Embed, members: list[discord.Member], label: str) -> None:
        if not members:
            return
        chunk, blocks = "", []
        for m in members:
            line = f"{m.mention} (`{m.id}`)\n"
            if len(chunk) + len(line) > 1000:
                blocks.append(chunk)
                chunk = ""
            chunk += line
        if chunk:
            blocks.append(chunk)
        for i, block in enumerate(blocks, start=1):
            name = label if len(blocks) == 1 else f"{label} ({i}/{len(blocks)})"
            embed.add_field(name=name, value=block, inline=False)

    add_mention_fields(embed, expelled, "Expulsados — sin rol de orientación")
    add_mention_fields(embed, expelled_sin_verificar, "Expulsados — no se verificaron")

    channel = guild.get_channel(get_log_channel_id())
    if channel is not None:
        try:
            await channel.send(embed=embed)
        except discord.Forbidden:
            print("Sin permisos para escribir en el canal de logs")

    await interaction.followup.send(
        f"Listo — {verified} verificado(s), {len(expelled)} expulsado(s) (orientación), "
        f"{len(expelled_sin_verificar)} expulsado(s) (Sin Verificar).",
        ephemeral=True,
    )


@heraldo_check_all.error
async def heraldo_check_all_error(interaction: discord.Interaction, error: discord.app_commands.AppCommandError) -> None:
    if isinstance(error, discord.app_commands.MissingPermissions):
        await interaction.response.send_message("No tienes permiso para usar este comando.", ephemeral=True)
    else:
        await interaction.response.send_message(f"Error: {error}", ephemeral=True)


@bot.tree.command(name="heraldo_log_channel", description="Cambiar el canal donde El Heraldo reporta su actividad (logs).")
@discord.app_commands.describe(canal="Canal de texto donde se publicarán los logs")
@discord.app_commands.checks.has_permissions(kick_members=True)
@discord.app_commands.guild_only()
async def heraldo_log_channel(interaction: discord.Interaction, canal: discord.TextChannel) -> None:
    # Validar antes de guardar: así no se configura un canal donde el bot no puede escribir.
    perms = canal.permissions_for(canal.guild.me)
    missing = [
        name for name, ok in (
            ("Ver canal", perms.view_channel),
            ("Enviar mensajes", perms.send_messages),
            ("Insertar enlaces", perms.embed_links),
        ) if not ok
    ]
    if missing:
        await interaction.response.send_message(
            f"❌ No guardé el cambio: el Heraldo no tiene estos permisos en {canal.mention}: "
            f"**{', '.join(missing)}**. Dáselos y vuelve a intentarlo.",
            ephemeral=True,
        )
        return

    set_log_channel_id(canal.id)
    await interaction.response.send_message(
        f"✅ Los logs de El Heraldo ahora se publicarán en {canal.mention}.",
        ephemeral=True,
    )
    # Ya apunta al canal nuevo: este embed sirve además de prueba de que escribe bien.
    await log_embed(
        interaction.guild, "⚙️ Canal de logs actualizado",
        f"{interaction.user.mention} lo cambió a {canal.mention}.",
        discord.Color.blurple(),
    )


@heraldo_log_channel.error
async def heraldo_log_channel_error(interaction: discord.Interaction, error: discord.app_commands.AppCommandError) -> None:
    if isinstance(error, discord.app_commands.MissingPermissions):
        await interaction.response.send_message("No tienes permiso para usar este comando.", ephemeral=True)
    else:
        await interaction.response.send_message(f"Error: {error}", ephemeral=True)


# ---------------------------------------------------------------------------
# Verificación por botón (/verify)
# ---------------------------------------------------------------------------

def verify_role_problem(role: discord.Role, guild: discord.Guild) -> str | None:
    """Motivo por el que NO conviene usar este rol como rol de verificación, o None
    si está bien. El botón lo puede pulsar cualquiera: el rol no puede dar poderes de
    moderación, y el Heraldo tiene que poder asignarlo."""
    if role.is_default():
        return "es @everyone"
    if role.managed:
        return "es un rol gestionado por una integración o un bot"
    if role >= guild.me.top_role:
        return "está al mismo nivel o por encima del rol más alto del Heraldo"
    risky = [label for attr, label in VERIFY_DANGEROUS_PERMS if getattr(role.permissions, attr)]
    if risky:
        return "da permisos que no deben salir de un botón público (" + ", ".join(risky) + ")"
    return None


class VerifyView(discord.ui.View):
    """Vista persistente: el botón sigue funcionando tras reinicios (se registra en on_ready)."""

    def __init__(self, label: str | None = None) -> None:
        super().__init__(timeout=None)
        button = discord.ui.Button(
            label=label or get_verify_button_label(),
            style=discord.ButtonStyle.success,
            custom_id=VERIFY_BUTTON_ID,
        )
        button.callback = handle_verify_click
        self.add_item(button)


async def send_verification_welcome_dm(member: discord.Member) -> bool:
    """Envía el DM de bienvenida una sola vez, cuando el miembro se verifica por primera vez."""
    if db_verification_dm_sent(member.id):
        return True

    embed = build_verification_welcome_embed(member=member)
    try:
        await member.send(embed=embed)
        db_mark_verification_dm_sent(member.id)
        return True
    except discord.HTTPException:
        return False


async def handle_verify_click(interaction: discord.Interaction) -> None:
    guild = interaction.guild
    member = interaction.user
    if guild is None or not isinstance(member, discord.Member):
        await interaction.response.send_message("Esto solo funciona dentro del servidor.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True, thinking=True)

    punish_role_id = hp_punish_role_id()
    if condemnation_get(member.id) is not None or (punish_role_id and any(r.id == punish_role_id for r in member.roles)):
        await interaction.followup.send("☠️ Estás condenado: no puedes verificarte mientras la condena esté activa.", ephemeral=True)
        return

    role = guild.get_role(get_verify_role_id())
    if role is None:
        await interaction.followup.send("⚠️ La verificación no está configurada todavía. Avisa a un administrador.", ephemeral=True)
        await log_embed(
            guild, "⚠️ Verificación sin configurar",
            f"{member.mention} pulsó el botón pero el rol de verificación no existe.",
            discord.Color.dark_red(),
        )
        return

    role_ids = {r.id for r in member.roles}
    if role.id in role_ids or role_ids & EVAL_ROLE_IDS:
        await interaction.followup.send("✅ ¡Ya estás verificado!", ephemeral=True)
        return

    problem = verify_role_problem(role, guild)
    if problem:
        await interaction.followup.send("⚠️ La verificación está mal configurada. Avisa a un administrador.", ephemeral=True)
        await log_embed(
            guild, "⚠️ Verificación bloqueada",
            f"{member.mention} pulsó el botón, pero el rol {role.mention} {problem}. No se le dio.",
            discord.Color.dark_red(),
        )
        return

    try:
        await member.add_roles(role, reason="Verificación de edad (botón de El Heraldo)")
    except discord.HTTPException as e:  # incluye Forbidden (jerarquía o permisos)
        await interaction.followup.send("❌ No pude darte el rol. Avisa a un administrador.", ephemeral=True)
        await log_embed(
            guild, "⚠️ Error al verificar",
            f"No pude darle {role.mention} a {member.mention}: `{e}`. Revisa jerarquía de roles y permisos.",
            discord.Color.dark_red(),
        )
        return

    db_clear_verify_pending(member.id)
    # Quien se verifica deja de estar "Sin Verificar" (si no, el respaldo de 300 s lo expulsaría).
    sin_role = guild.get_role(SIN_VERIFICAR_ROLE_ID)
    if sin_role is not None and sin_role in member.roles:
        try:
            await member.remove_roles(sin_role, reason="Verificación de edad (botón de El Heraldo)")
            db_clear_sin_verificado(member.id)
        except discord.HTTPException as e:
            await log_embed(
                guild, "⚠️ No pude quitar Sin Verificar",
                f"{member.mention} se verificó pero no pude quitarle {sin_role.mention}: `{e}`.",
                discord.Color.dark_red(),
            )

    await interaction.followup.send(
        render_vars(get_verify_success_text(), VarContext(guild, member, interaction.channel), 2000),
        ephemeral=True, allowed_mentions=discord.AllowedMentions.none(),
    )

    # DM de bienvenida: solo la primera vez que este usuario obtiene el rol de verificación.
    dm_welcome_ok = await send_verification_welcome_dm(member)
    if not dm_welcome_ok:
        await log_embed(
            guild, "⚠️ No pude enviar el DM de bienvenida",
            f"{member.mention} se verificó, pero tiene los DMs cerrados o Discord rechazó el mensaje.",
            discord.Color.orange(),
        )

    await log_embed(
        guild, "✅ Verificación de edad",
        f"{member.mention} (`{member.id}`) pulsó el botón y recibió {role.mention}.",
        discord.Color.green(),
    )


async def schedule_verify_timeout(guild_id: int, user_id: int, pending_at: datetime) -> None:
    delay = (pending_at + timedelta(seconds=get_verify_timeout()) - datetime.now(timezone.utc)).total_seconds()
    if delay > 0:
        await asyncio.sleep(delay)
    await evaluate_verify_timeout(guild_id, user_id)


async def evaluate_verify_timeout(guild_id: int, user_id: int) -> None:
    """Aplica la acción configurada si el miembro no se verificó dentro del timeout.
    Lee siempre la configuración actual: si el timeout se alargó mientras esperaba, no
    actúa todavía (check_pending_verifications lo retoma al vencer el nuevo plazo)."""
    if condemnation_get(user_id) is not None:
        db_clear_verify_pending(user_id)
        return
    row = db_get(user_id)
    if row is None or row["verify_pending_at"] is None:
        return  # ya verificado, ya evaluado o nunca estuvo pendiente
    guild = bot.get_guild(guild_id)
    if guild is None:
        return
    member = guild.get_member(user_id)
    if member is None or not verify_enabled():
        db_clear_verify_pending(user_id)  # se fue, o la verificación se desactivó
        return

    timeout = get_verify_timeout()
    deadline = datetime.fromisoformat(row["verify_pending_at"]) + timedelta(seconds=timeout)
    if datetime.now(timezone.utc) + timedelta(seconds=1) < deadline:
        return

    role_ids = {r.id for r in member.roles}
    db_clear_verify_pending(user_id)
    if get_verify_role_id() in role_ids or role_ids & EVAL_ROLE_IDS:
        return  # se verificó a tiempo (o un admin le dio un rol de orientación)

    action = get_verify_action()
    if action == "none":
        await log_embed(
            guild, "⏰ Verificación vencida",
            f"{member.mention} (`{member.id}`) no se verificó en {timeout} s. "
            f"Acción configurada: solo registrar.",
            discord.Color.orange(),
        )
        return
    try:
        if action == "ban":
            await member.ban(reason="No se verificó dentro del tiempo límite", delete_message_seconds=0)
        else:
            await member.kick(reason="No se verificó dentro del tiempo límite")
    except discord.HTTPException as e:  # incluye Forbidden (jerarquía de roles)
        await log_embed(
            guild, "⚠️ Error al aplicar el timeout de verificación",
            f"No pude {'banear' if action == 'ban' else 'expulsar'} a {member.mention}: `{e}`. "
            f"Revisa la jerarquía de roles.",
            discord.Color.dark_red(),
        )
        return
    await log_embed(
        guild, "🔨 Ban — No se verificó" if action == "ban" else "👢 Kick — No se verificó",
        f"{member.mention} (`{member.id}`) no se verificó en {timeout} s.",
        discord.Color.red(),
    )


async def update_verify_panel(guild: discord.Guild) -> str:
    """Edita el panel ya publicado con los textos actuales. Devuelve una nota para el admin."""
    ref = db_meta_get("verify_panel_ref")
    if not ref:
        return "Aún no hay panel publicado: usa /verify para publicarlo."
    try:
        channel_id, message_id = (int(x) for x in ref.split(":"))
        channel = guild.get_channel(channel_id)
        if channel is None:
            return "⚠️ No encontré el canal del panel; publícalo de nuevo con /verify."
        message = await channel.fetch_message(message_id)
        await message.edit(
            content=render_vars(get_verify_panel_text(), VarContext(guild, None, channel), 2000),
            view=VerifyView(),
            allowed_mentions=discord.AllowedMentions.none(),
        )
        return "El panel publicado ya muestra los textos nuevos."
    except discord.NotFound:
        return "⚠️ El panel ya no existe (¿lo borraron?); publícalo de nuevo con /verify."
    except (discord.HTTPException, ValueError) as e:
        return f"⚠️ No pude actualizar el panel publicado: `{e}`. Publícalo de nuevo con /verify."


def verify_config_summary(guild: discord.Guild) -> str:
    role_id = get_verify_role_id()
    role = guild.get_role(role_id)
    role_text = role.mention if role else f"⚠️ no encontrado (`{role_id}`)"
    ref = db_meta_get("verify_panel_ref")
    if ref and ref.count(":") == 1:
        channel_id, message_id = ref.split(":")
        panel_text = f"[ir al panel](https://discord.com/channels/{guild.id}/{channel_id}/{message_id})"
    elif ref:
        panel_text = "⚠️ referencia dañada: publícalo de nuevo con /verify"
    else:
        panel_text = "sin publicar (usa /verify)"
    return (
        f"**Verificación:** {'✅ activada' if verify_enabled() else '⏸️ desactivada'}\n"
        f"**Rol de verificación:** {role_text}\n"
        f"**Timeout:** {format_duration((get_verify_timeout() + 59) // 60)}\n"
        f"**Acción al agotarse:** {VERIFY_ACTION_LABELS[get_verify_action()]}\n"
        f"**Panel:** {panel_text}"
    )


class VerifyTextsModal(discord.ui.Modal):
    """Formulario de textos; se abre con los valores actuales."""

    def __init__(self) -> None:
        super().__init__(title="Textos de la verificación")
        self.panel = discord.ui.TextInput(
            label="Mensaje del panel (sobre el botón)",
            style=discord.TextStyle.paragraph,
            default=get_verify_panel_text(),
            max_length=2000,
        )
        self.button_label = discord.ui.TextInput(
            label="Texto del botón",
            default=get_verify_button_label(),
            max_length=80,
        )
        self.success = discord.ui.TextInput(
            label="Mensaje tras pulsar el botón",
            style=discord.TextStyle.paragraph,
            default=get_verify_success_text(),
            max_length=1000,
        )
        self.add_item(self.panel)
        self.add_item(self.button_label)
        self.add_item(self.success)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        panel = self.panel.value.strip()
        label = self.button_label.value.strip()
        success = self.success.value.strip()
        if not (panel and label and success):
            await interaction.response.send_message("❌ Ningún texto puede quedar vacío; no guardé nada.", ephemeral=True)
            return
        db_meta_set("verify_panel_text", panel)
        db_meta_set("verify_button_label", label)
        db_meta_set("verify_success_text", success)
        await interaction.response.defer(ephemeral=True, thinking=True)
        note = await update_verify_panel(interaction.guild)
        await interaction.followup.send(f"✅ Textos guardados. {note}", ephemeral=True)
        await log_embed(
            interaction.guild, "⚙️ Textos de verificación actualizados",
            f"{interaction.user.mention} editó el mensaje del panel, el botón o el mensaje de éxito.",
            discord.Color.blurple(),
        )


@bot.tree.command(name="verify", description="Publicar el panel de verificación (botón) en un canal.")
@discord.app_commands.describe(canal="Canal donde publicarlo (por defecto, este)")
@discord.app_commands.checks.has_permissions(manage_guild=True)
@discord.app_commands.guild_only()
async def verify(interaction: discord.Interaction, canal: Optional[discord.TextChannel] = None) -> None:
    guild = interaction.guild
    target = canal or interaction.channel
    if not isinstance(target, discord.TextChannel):
        await interaction.response.send_message("Úsalo en un canal de texto o elige uno con la opción `canal`.", ephemeral=True)
        return
    role = guild.get_role(get_verify_role_id())
    if role is None:
        await interaction.response.send_message("❌ El rol de verificación no existe. Elige uno con `/verify_config`.", ephemeral=True)
        return
    problem = verify_role_problem(role, guild)
    if problem:
        await interaction.response.send_message(
            f"❌ No publiqué el panel: el rol {role.mention} {problem}. Elige otro con `/verify_config`.",
            ephemeral=True,
        )
        return
    perms = target.permissions_for(guild.me)
    if not (perms.view_channel and perms.send_messages):
        await interaction.response.send_message(
            f"❌ El Heraldo no puede escribir en {target.mention} (necesita Ver canal y Enviar mensajes).",
            ephemeral=True,
        )
        return

    await interaction.response.defer(ephemeral=True)
    try:
        message = await target.send(
            content=render_vars(get_verify_panel_text(), VarContext(guild, None, target), 2000),
            view=VerifyView(),
            allowed_mentions=discord.AllowedMentions.none(),
        )
    except discord.HTTPException as e:
        await interaction.followup.send(f"❌ No pude publicar el panel: `{e}`", ephemeral=True)
        return
    db_meta_set("verify_panel_ref", f"{target.id}:{message.id}")
    await interaction.followup.send(
        f"✅ Panel publicado en {target.mention}. Cuando quieras que el timeout empiece a aplicarse, "
        f"usa `/verify_config activado:True`.",
        ephemeral=True,
    )
    await log_embed(
        guild, "⚙️ Panel de verificación publicado",
        f"{interaction.user.mention} lo publicó en {target.mention}.",
        discord.Color.blurple(),
    )


@bot.tree.command(
    name="verify_dm_texts",
    description="Editar el DM de bienvenida, parte por parte y en orden.",
)
@discord.app_commands.describe(
    titulo="1/6 · Título principal del embed (máx. 256 caracteres).",
    campo="2/6 · Nombre del campo del embed (máx. 256 caracteres).",
    mensaje="3/6 · Contenido del mensaje; puedes usar Markdown y menciones de canales.",
    footer="4/6 · Texto del pie del embed (máx. 2048 caracteres).",
    color="5/6 · Color HEX de 6 caracteres, por ejemplo 4F5BDC.",
    icono_footer="6/6 · URL de la imagen pequeña que aparece junto al footer.",
)
@discord.app_commands.checks.has_permissions(manage_guild=True)
@discord.app_commands.guild_only()
async def verify_dm_texts(
    interaction: discord.Interaction,
    titulo: str,
    campo: str,
    mensaje: str,
    footer: str,
    color: str,
    icono_footer: str,
) -> None:
    """Editor directo del DM: Discord muestra las 6 partes en este mismo orden."""
    titulo = titulo.strip()
    campo = campo.strip()
    mensaje = mensaje.strip()
    footer = footer.strip()
    color = color.strip().lstrip("#")
    icono_footer = icono_footer.strip()

    if not titulo or not campo or not mensaje or not footer or not color or not icono_footer:
        await interaction.response.send_message(
            "❌ No guardé nada: todas las partes del embed son obligatorias.",
            ephemeral=True,
        )
        return

    if len(titulo) > 256:
        await interaction.response.send_message("❌ El título no puede superar 256 caracteres.", ephemeral=True)
        return
    if len(campo) > 256:
        await interaction.response.send_message("❌ El nombre del campo no puede superar 256 caracteres.", ephemeral=True)
        return
    if len(mensaje) > 4000:
        await interaction.response.send_message("❌ El mensaje no puede superar 4000 caracteres.", ephemeral=True)
        return
    if len(footer) > 2048:
        await interaction.response.send_message("❌ El footer no puede superar 2048 caracteres.", ephemeral=True)
        return
    if not re.fullmatch(r"[0-9a-fA-F]{6}", color):
        await interaction.response.send_message(
            "❌ El color debe ser HEX de 6 caracteres, por ejemplo `4F5BDC` o `#4F5BDC`.",
            ephemeral=True,
        )
        return
    if len(icono_footer) > 500:
        await interaction.response.send_message("❌ La URL del icono del footer es demasiado larga.", ephemeral=True)
        return
    if not re.match(r"^https?://", icono_footer, re.IGNORECASE) and not VAR_PATTERN.search(icono_footer):
        await interaction.response.send_message(
            "❌ El icono del footer debe ser una URL válida (`https://…`) o una variable como `{servericon}`.",
            ephemeral=True,
        )
        return

    values = {
        "verify_dm_title": titulo,
        "verify_dm_field_name": campo,
        "verify_dm_body": mensaje,
        "verify_dm_footer": footer,
        "verify_dm_color": color.upper(),
        "verify_dm_footer_icon": icono_footer,
    }
    for key, value in values.items():
        db_meta_set(key, value)

    await interaction.response.send_message(
        "✅ **DM de bienvenida actualizado correctamente.**\n"
        "Las próximas primeras verificaciones recibirán esta nueva versión.\n\n"
        "Usa `/verify_dm_preview` para verla en el canal de logs.",
        ephemeral=True,
    )
    await log_embed(
        interaction.guild,
        "⚙️ DM de bienvenida actualizado",
        f"{interaction.user.mention} actualizó las 6 partes del embed de primera verificación.",
        discord.Color.blurple(),
    )


@bot.tree.command(name="verify_dm_preview", description="Mostrar en el canal de logs una vista previa del DM de bienvenida.")
@discord.app_commands.checks.has_permissions(manage_guild=True)
@discord.app_commands.guild_only()
async def verify_dm_preview(interaction: discord.Interaction) -> None:
    guild = interaction.guild
    log_channel = guild.get_channel(get_log_channel_id())
    if log_channel is None:
        await interaction.response.send_message(
            "❌ No encontré el canal de logs configurado. Configúralo con `/heraldo_log_channel`.",
            ephemeral=True,
        )
        return
    perms = log_channel.permissions_for(guild.me)
    if not (perms.view_channel and perms.send_messages and perms.embed_links):
        await interaction.response.send_message(
            f"❌ No puedo publicar la vista previa en {log_channel.mention}: necesito Ver canal, Enviar mensajes y Insertar enlaces.",
            ephemeral=True,
        )
        return
    try:
        embed = build_verification_welcome_embed(
            member=interaction.user if isinstance(interaction.user, discord.Member) else None, guild=guild,
        )
        await log_channel.send(
            content=f"🔎 **Vista previa del DM de bienvenida** — solicitada por {interaction.user.mention}",
            embed=embed,
            allowed_mentions=discord.AllowedMentions.none(),
        )
    except discord.HTTPException as e:
        await interaction.response.send_message(f"❌ No pude publicar la vista previa: `{e}`", ephemeral=True)
        return
    await interaction.response.send_message(
        f"✅ Vista previa publicada en {log_channel.mention}.", ephemeral=True
    )


@bot.tree.command(name="verify_texts", description="Editar el mensaje del panel, el texto del botón y el mensaje tras verificarse.")
@discord.app_commands.checks.has_permissions(manage_guild=True)
@discord.app_commands.guild_only()
async def verify_texts(interaction: discord.Interaction) -> None:
    await interaction.response.send_modal(VerifyTextsModal())


@bot.tree.command(name="verify_config", description="Ver o cambiar la configuración de la verificación por botón.")
@discord.app_commands.describe(
    rol="Rol que se otorga al verificarse",
    timeout="Tiempo para verificarse desde que entra (usa d, h y m; por ejemplo 5m, 1h o 1d)",
    accion="Qué hacer con quien no se verifica a tiempo",
    activado="Activar o desactivar el timeout automático",
)
@discord.app_commands.choices(accion=[
    discord.app_commands.Choice(name="Expulsar", value="kick"),
    discord.app_commands.Choice(name="Banear (permanente)", value="ban"),
    discord.app_commands.Choice(name="Solo registrar (sin acción)", value="none"),
])
@discord.app_commands.checks.has_permissions(manage_guild=True)
@discord.app_commands.guild_only()
async def verify_config(
    interaction: discord.Interaction,
    rol: Optional[discord.Role] = None,
    timeout: Optional[str] = None,
    accion: Optional[discord.app_commands.Choice[str]] = None,
    activado: Optional[bool] = None,
) -> None:
    guild = interaction.guild
    if rol is None and timeout is None and accion is None and activado is None:
        await interaction.response.send_message(verify_config_summary(guild), ephemeral=True)
        return

    # 1) Validar todo antes de guardar nada.
    timeout_seconds = None
    if timeout is not None:
        try:
            timeout_minutes = parse_duration(timeout, 1, 28 * 24 * 60)
            timeout_seconds = timeout_minutes * 60
        except ValueError as e:
            await interaction.response.send_message(f"❌ No guardé nada: {e}", ephemeral=True)
            return
    if rol is not None:
        problem = verify_role_problem(rol, guild)
        if problem:
            await interaction.response.send_message(f"❌ No guardé nada: {rol.mention} {problem}.", ephemeral=True)
            return
    if activado:
        effective_role = rol or guild.get_role(get_verify_role_id())
        if effective_role is None:
            await interaction.response.send_message(
                "❌ No activé la verificación: el rol de verificación no existe. Elige uno con `rol`.",
                ephemeral=True,
            )
            return
        problem = verify_role_problem(effective_role, guild)
        if problem:
            await interaction.response.send_message(
                f"❌ No activé la verificación: {effective_role.mention} {problem}.", ephemeral=True
            )
            return
        if not db_meta_get("verify_panel_ref"):
            await interaction.response.send_message(
                "❌ No activé la verificación: aún no hay panel publicado. Usa `/verify` primero; "
                "si no, nadie podría verificarse y todos los que entren serían sancionados.",
                ephemeral=True,
            )
            return

    # 2) Guardar.
    changes: list[str] = []
    if rol is not None:
        db_meta_set("verify_role_id", str(rol.id))
        changes.append(f"rol → {rol.mention}")
    if timeout_seconds is not None:
        db_meta_set("verify_timeout", str(timeout_seconds))
        changes.append(f"timeout → {format_duration(timeout_seconds // 60)}")
    if accion is not None:
        db_meta_set("verify_action", accion.value)
        changes.append(f"acción → {accion.name}")
    if activado is not None:
        db_meta_set("verify_enabled", "1" if activado else "0")
        changes.append("activada" if activado else "desactivada")

    warnings: list[str] = []
    if get_verify_timeout() > SIN_VERIFICAR_WINDOW.total_seconds():
        warnings.append("⚠️ El respaldo de Sin Verificar sigue en 300 s: quien tenga ese rol será expulsado antes que este timeout.")
    if get_verify_role_id() != TENTADO_ROLE_ID:
        warnings.append("⚠️ El timer de orientación (10 min) solo se arma con Tentad@; con otro rol no se activará.")

    await interaction.response.send_message(
        "✅ Guardado: " + "; ".join(changes) + "\n\n" + verify_config_summary(guild)
        + ("\n\n" + "\n".join(warnings) if warnings else ""),
        ephemeral=True,
    )
    await log_embed(
        guild, "⚙️ Verificación actualizada",
        f"{interaction.user.mention}: " + "; ".join(changes),
        discord.Color.blurple(),
    )


async def verify_command_error(interaction: discord.Interaction, error: discord.app_commands.AppCommandError) -> None:
    if isinstance(error, discord.app_commands.MissingPermissions):
        text = "No tienes permiso para usar este comando."
    else:
        text = f"Error: {error}"
    if interaction.response.is_done():
        await interaction.followup.send(text, ephemeral=True)
    else:
        await interaction.response.send_message(text, ephemeral=True)


verify.error(verify_command_error)
verify_texts.error(verify_command_error)
verify_config.error(verify_command_error)
verify_dm_texts.error(verify_command_error)
verify_dm_preview.error(verify_command_error)


# ---------------------------------------------------------------------------
# Copia de seguridad de la plantilla del servidor (/template_config, /template_sync)
# ---------------------------------------------------------------------------

def _meta_int(key: str, default: int) -> int:
    value = db_meta_get(key)
    return int(value) if value is not None else default


def get_template_mode() -> str:
    value = db_meta_get("template_mode")
    return value if value in TEMPLATE_MODE_LABELS else "off"


def get_template_hour() -> int:
    return _meta_int("template_hour", TEMPLATE_HOUR_DEFAULT)


def get_template_weekday() -> int:
    return _meta_int("template_weekday", TEMPLATE_WEEKDAY_DEFAULT)


def get_template_monthday() -> int:
    return _meta_int("template_monthday", TEMPLATE_MONTHDAY_DEFAULT)


def get_template_interval_minutes() -> int:
    """Intervalo en minutos. Las versiones antiguas guardaban horas; se leen como compatibilidad."""
    value = db_meta_get("template_interval_minutes")
    if value is not None:
        return int(value)
    old = db_meta_get("template_interval_hours")
    if old is not None:
        return int(old) * 60
    return TEMPLATE_INTERVAL_DEFAULT * 60


def template_schedule_text() -> str:
    mode = get_template_mode()
    hour = f"{get_template_hour()}:00 (hora de RD)"
    if mode == "off":
        return "Desactivada"
    if mode == "daily":
        return f"Cada día a las {hour}"
    if mode == "weekly":
        return f"Cada semana, {MOTW_WEEKDAY_NAMES[get_template_weekday()]} a las {hour}"
    if mode == "monthly":
        return f"Cada mes, el día {get_template_monthday()} a las {hour}"
    return f"Cada {format_duration(get_template_interval_minutes())}"


def template_last_slot(mode: str, now: datetime) -> datetime | None:
    """Último turno programado (hora local de STREAK_TZ) que ya pasó respecto a `now`.
    Solo para los modos de calendario (diario, semanal, mensual)."""
    hour = get_template_hour()
    if mode == "daily":
        slot = now.replace(hour=hour, minute=0, second=0, microsecond=0)
        if slot > now:
            slot -= timedelta(days=1)
        return slot
    if mode == "weekly":
        days_back = (now.weekday() - get_template_weekday()) % 7
        slot = (now - timedelta(days=days_back)).replace(hour=hour, minute=0, second=0, microsecond=0)
        if slot > now:
            slot -= timedelta(days=7)
        return slot
    if mode == "monthly":
        day = get_template_monthday()  # 1-28: existe en todos los meses
        slot = now.replace(day=day, hour=hour, minute=0, second=0, microsecond=0)
        if slot > now:
            last_of_previous = now.replace(day=1) - timedelta(days=1)
            slot = last_of_previous.replace(day=day, hour=hour, minute=0, second=0, microsecond=0)
        return slot
    return None


def template_next_run(now_utc: datetime) -> datetime | None:
    """Próxima copia programada, en hora local de STREAK_TZ (None si está desactivada)."""
    mode = get_template_mode()
    if mode == "off":
        return None
    if mode == "interval":
        last = db_meta_get("template_last_run")
        base = datetime.fromisoformat(last) if last else now_utc
        return (base + timedelta(minutes=get_template_interval_minutes())).astimezone(STREAK_TZ)
    slot = template_last_slot(mode, now_utc.astimezone(STREAK_TZ))
    if mode == "daily":
        return slot + timedelta(days=1)
    if mode == "weekly":
        return slot + timedelta(days=7)
    first_of_next = (slot.replace(day=28) + timedelta(days=4)).replace(day=1)
    return first_of_next.replace(day=get_template_monthday())


def template_due(now_utc: datetime) -> bool:
    """¿Toca la copia? En el primer arranque (o tras activarla) solo arranca el reloj:
    no hace una copia con la configuración recién cambiada."""
    mode = get_template_mode()
    if mode == "off":
        return False
    if mode == "interval":
        last = db_meta_get("template_last_run")
        if last is None:
            db_meta_set("template_last_run", now_utc.isoformat())
            return False
        return now_utc >= datetime.fromisoformat(last) + timedelta(minutes=get_template_interval_minutes())
    slot = template_last_slot(mode, now_utc.astimezone(STREAK_TZ))
    handled = db_meta_get("template_last_slot")
    if handled is None:
        db_meta_set("template_last_slot", slot.isoformat())
        return False
    return slot > datetime.fromisoformat(handled)


def template_mark_done(now_utc: datetime) -> None:
    """Da el turno actual por hecho (se llama ANTES de la copia, para no duplicarla)."""
    db_meta_set("template_last_run", now_utc.isoformat())
    mode = get_template_mode()
    if mode in ("daily", "weekly", "monthly"):
        db_meta_set("template_last_slot", template_last_slot(mode, now_utc.astimezone(STREAK_TZ)).isoformat())


async def sync_server_template(guild: discord.Guild) -> tuple[discord.Template | None, bool | None, str | None]:
    """Sincroniza la plantilla. Devuelve (plantilla, tenía_cambios_pendientes, error)."""
    try:
        templates = await guild.templates()
    except discord.HTTPException as e:
        return None, None, f"No pude leer las plantillas del servidor: `{e}`"
    if not templates:
        return None, None, "El servidor no tiene plantilla. Créala en Ajustes del servidor → Plantilla de servidor."
    template = templates[0]
    was_dirty = template.is_dirty
    try:
        template = await template.sync()
    except discord.HTTPException as e:
        return None, was_dirty, f"No pude sincronizar la plantilla: `{e}`"
    return template, was_dirty, None


def template_report_embed(template: discord.Template, was_dirty: bool | None, trigger: str) -> discord.Embed:
    if was_dirty is True:
        state = "✅ Había cambios pendientes y ya están sincronizados."
    elif was_dirty is False:
        state = "✅ Sin cambios pendientes: la plantilla ya estaba al día."
    else:
        state = "✅ Sincronizada (Discord no indicó si había cambios)."
    embed = discord.Embed(
        title="🛡️ Copia de seguridad de la plantilla",
        description=state,
        color=discord.Color.green(),
        timestamp=datetime.now(timezone.utc),
    )
    embed.add_field(name="Enlace", value=template.url, inline=False)
    synced_at = template.updated_at or datetime.now(timezone.utc)
    embed.add_field(name="Última sincronización", value=discord.utils.format_dt(synced_at, "f"), inline=True)
    embed.add_field(name="Usos", value=str(template.uses), inline=True)
    embed.add_field(name="Disparada por", value=trigger, inline=True)
    embed.set_footer(text="Paraíso Morboso 2026 © - El Heraldo 🪽")
    return embed


async def run_scheduled_template_backup() -> None:
    guild = bot.get_guild(_meta_int("template_guild_id", 0))
    if guild is None:
        print("⚠️ Copia de plantilla: no encontré el servidor configurado.")
        return
    template, was_dirty, error = await sync_server_template(guild)
    if error:
        embed = discord.Embed(
            title="⚠️ Falló la copia de seguridad de la plantilla",
            description=error,
            color=discord.Color.dark_red(),
            timestamp=datetime.now(timezone.utc),
        )
    else:
        embed = template_report_embed(template, was_dirty, "programada")

    sent = False
    try:
        user = await bot.fetch_user(_meta_int("template_user_id", 0))
        await user.send(embed=embed)
        sent = True
    except discord.HTTPException:
        pass  # incluye Forbidden (mensajes privados cerrados)
    # El enlace nunca va al canal de logs: ahí solo queda constancia del fallo o del envío fallido.
    if error:
        await log_embed(guild, "⚠️ Falló la copia de seguridad de la plantilla", error, discord.Color.dark_red())
    elif not sent:
        await log_embed(
            guild, "🛡️ Plantilla sincronizada (mensaje privado no enviado)",
            "La copia se hizo, pero no pude mandarte el enlace por mensaje privado. Usa /template_sync para verlo.",
            discord.Color.orange(),
        )


@tasks.loop(minutes=10)
async def template_backup_loop() -> None:
    """Revisa cada 10 min si toca la copia. Al comparar contra el último turno guardado en
    la DB, también se recupera si el bot estaba caído a la hora."""
    try:
        now = datetime.now(timezone.utc)
        if template_due(now):
            template_mark_done(now)  # se marca antes; si falla, se reintenta en el próximo turno
            await run_scheduled_template_backup()
    except Exception:
        traceback.print_exc()  # que un error no detenga el loop


def template_config_summary(now_utc: datetime) -> str:
    next_run = template_next_run(now_utc)
    next_text = (
        f"{discord.utils.format_dt(next_run, 'F')} ({discord.utils.format_dt(next_run, 'R')})"
        if next_run else "—"
    )
    last = db_meta_get("template_last_run")
    last_text = discord.utils.format_dt(datetime.fromisoformat(last), "f") if last and get_template_mode() != "off" else "ninguna todavía"
    user_id = db_meta_get("template_user_id")
    return (
        f"**Frecuencia:** {template_schedule_text()}\n"
        f"**Próxima copia:** {next_text}\n"
        f"**Última copia programada:** {last_text}\n"
        f"**Enlace por mensaje privado a:** {f'<@{user_id}>' if user_id else 'quien configure (aún sin definir)'}"
    )


@bot.tree.command(name="template_config", description="Ver o cambiar cuándo se sincroniza la plantilla del servidor (copia de seguridad).")
@discord.app_commands.describe(
    frecuencia="Cada cuánto se hace la copia",
    hora="Hora del día (0-23, hora de RD)",
    dia_semana="Día de la semana (frecuencia semanal)",
    dia_mes="Día del mes, 1-28 (frecuencia mensual)",
    intervalo="Intervalo entre copias (frecuencia por intervalo): usa d, h y m, por ejemplo 30m, 6h o 1d",
    enviar_a="Quién recibe el enlace por mensaje privado (por defecto, tú)",
)
@discord.app_commands.choices(
    frecuencia=[
        discord.app_commands.Choice(name=label, value=value) for value, label in TEMPLATE_MODE_LABELS.items()
    ],
    dia_semana=[
        discord.app_commands.Choice(name=name, value=i) for i, name in enumerate(MOTW_WEEKDAY_NAMES)
    ],
)
@discord.app_commands.checks.has_permissions(manage_guild=True)
@discord.app_commands.guild_only()
async def template_config(
    interaction: discord.Interaction,
    frecuencia: Optional[discord.app_commands.Choice[str]] = None,
    hora: Optional[discord.app_commands.Range[int, 0, 23]] = None,
    dia_semana: Optional[discord.app_commands.Choice[int]] = None,
    dia_mes: Optional[discord.app_commands.Range[int, 1, 28]] = None,
    intervalo: Optional[str] = None,
    enviar_a: Optional[discord.User] = None,
) -> None:
    guild = interaction.guild
    now = datetime.now(timezone.utc)
    if all(v is None for v in (frecuencia, hora, dia_semana, dia_mes, intervalo, enviar_a)):
        await interaction.response.send_message(template_config_summary(now), ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True)

    # Validar el intervalo antes de guardar cualquier cambio.
    intervalo_minutes = None
    if intervalo is not None:
        try:
            intervalo_minutes = parse_duration(intervalo, 1, 30 * 24 * 60)
        except ValueError as e:
            await interaction.followup.send(f"❌ No guardé nada: {e}", ephemeral=True)
            return

    changes: list[str] = []
    if frecuencia is not None:
        db_meta_set("template_mode", frecuencia.value)
        changes.append(f"frecuencia → {frecuencia.name}")
    if hora is not None:
        db_meta_set("template_hour", str(hora))
        changes.append(f"hora → {hora}:00")
    if dia_semana is not None:
        db_meta_set("template_weekday", str(dia_semana.value))
        changes.append(f"día de la semana → {dia_semana.name}")
    if dia_mes is not None:
        db_meta_set("template_monthday", str(dia_mes))
        changes.append(f"día del mes → {dia_mes}")
    if intervalo_minutes is not None:
        db_meta_set("template_interval_minutes", str(intervalo_minutes))
        changes.append(f"intervalo → {format_duration(intervalo_minutes)}")
    db_meta_set("template_guild_id", str(guild.id))
    if enviar_a is not None:
        db_meta_set("template_user_id", str(enviar_a.id))
        changes.append(f"enviar a → {enviar_a.mention}")
    elif db_meta_get("template_user_id") is None:
        db_meta_set("template_user_id", str(interaction.user.id))

    # Un cambio de horario solo afecta a la PRÓXIMA copia: da por hecho el turno actual
    # (o reinicia el reloj del intervalo) para que no dispare una copia inmediata.
    if get_template_mode() == "interval":
        db_meta_set("template_last_run", now.isoformat())
    elif get_template_mode() in ("daily", "weekly", "monthly"):
        db_meta_set("template_last_slot", template_last_slot(get_template_mode(), now.astimezone(STREAK_TZ)).isoformat())

    note = ""
    if get_template_mode() != "off":
        try:
            if not await guild.templates():
                note = "\n\n⚠️ El servidor aún no tiene plantilla: créala en Ajustes del servidor → Plantilla de servidor, o la copia fallará."
        except discord.HTTPException as e:
            note = f"\n\n⚠️ No pude comprobar si hay plantilla: `{e}`"

    await interaction.followup.send(
        "✅ Guardado: " + "; ".join(changes) + "\n\n" + template_config_summary(now) + note,
        ephemeral=True,
    )
    await log_embed(
        guild, "⚙️ Copia de seguridad de la plantilla actualizada",
        f"{interaction.user.mention}: " + "; ".join(changes),
        discord.Color.blurple(),
    )


@bot.tree.command(name="template_sync", description="Sincronizar ahora la plantilla del servidor y ver su enlace.")
@discord.app_commands.checks.has_permissions(manage_guild=True)
@discord.app_commands.guild_only()
async def template_sync(interaction: discord.Interaction) -> None:
    await interaction.response.defer(ephemeral=True)
    template, was_dirty, error = await sync_server_template(interaction.guild)
    if error:
        await interaction.followup.send(f"❌ {error}", ephemeral=True)
        return
    embed = template_report_embed(template, was_dirty, "manual")
    try:
        await interaction.user.send(embed=embed)  # el enlace va a tus mensajes privados
        await interaction.followup.send("✅ Plantilla sincronizada. Te envié el enlace por mensaje privado.", ephemeral=True)
    except discord.HTTPException:
        # DMs cerrados: se muestra aquí, solo visible para ti, para no perder el enlace.
        await interaction.followup.send(
            "⚠️ No pude enviarte el mensaje privado (¿tienes los DMs cerrados?). Aquí tienes el enlace:",
            embed=embed, ephemeral=True,
        )
    await log_embed(
        interaction.guild, "🛡️ Plantilla sincronizada manualmente",
        f"{interaction.user.mention} sincronizó la plantilla del servidor.",
        discord.Color.blurple(),
    )


# Manejador genérico (permisos / errores), el mismo de los comandos de verificación.
template_config.error(verify_command_error)
template_sync.error(verify_command_error)


# ---------------------------------------------------------------------------
# Perfil: conteo de mensajes, racha diaria y comando /profile
# ---------------------------------------------------------------------------

# bot.listen (en vez de bot.event) para no pisar el on_message por defecto.
@bot.listen("on_message")
async def track_activity(message: discord.Message) -> None:
    if message.author.bot or message.guild is None:
        return  # bots, webhooks y DMs no cuentan
    if not isinstance(message.author, discord.Member):
        return
    if EXCLUDED_ROLE_IDS and any(r.id in EXCLUDED_ROLE_IDS for r in message.author.roles):
        return
    if message.channel.id in hp_trap_ids():
        return  # lo escrito en un canal trampa no cuenta como actividad
    punish_id = hp_punish_role_id()
    if (punish_id and any(r.id == punish_id for r in message.author.roles)) or condemnation_get(message.author.id) is not None:
        return  # los condenados no suman actividad

    today = datetime.now(STREAK_TZ).date()
    yesterday = today - timedelta(days=1)
    db_track_message(message.author.id, today.isoformat(), yesterday.isoformat())


@bot.tree.command(name="profile", description="Muestra tu perfil o el de otro miembro.")
@discord.app_commands.describe(user="Miembro a consultar (déjalo vacío para ver el tuyo)")
@discord.app_commands.guild_only()
async def profile(interaction: discord.Interaction, user: Optional[discord.User] = None) -> None:
    if user is None:
        target = interaction.user  # ya es un discord.Member dentro de un guild
    else:
        try:
            target = await interaction.guild.fetch_member(user.id)
        except discord.NotFound:
            await interaction.response.send_message(f"{user} no está en el servidor.", ephemeral=True)
            return

    messages, streak, last_active = db_get_activity(target.id)

    # La racha guardada solo es "actual" si el último día activo fue hoy o ayer;
    # si pasó más tiempo, la racha ya se rompió aunque aún no haya escrito de nuevo.
    today = datetime.now(STREAK_TZ).date()
    if last_active not in (today.isoformat(), (today - timedelta(days=1)).isoformat()):
        streak = 0

    # Roles de mayor a menor jerarquía, sin @everyone.
    roles = [r for r in reversed(target.roles) if not r.is_default()]
    if roles:
        roles_text = " ".join(r.mention for r in roles[:PROFILE_MAX_ROLES])
        if len(roles) > PROFILE_MAX_ROLES:
            roles_text += f" … +{len(roles) - PROFILE_MAX_ROLES} más"
    else:
        roles_text = "Sin roles"

    embed = discord.Embed(
        title=f"📋 Perfil de {target.display_name}",
        color=discord.Color.blurple(),
        timestamp=datetime.now(timezone.utc),
    )
    embed.set_thumbnail(url=target.display_avatar.url)
    embed.add_field(name="Usuario", value=discord.utils.escape_markdown(target.name), inline=True)
    embed.add_field(name="Nombre visible", value=discord.utils.escape_markdown(target.display_name), inline=True)
    embed.add_field(name="💬 Mensajes", value=f"{messages:,}", inline=True)
    embed.add_field(name="🔥 Racha diaria", value=f"{streak} día{'s' if streak != 1 else ''}", inline=True)
    embed.add_field(name="Roles", value=roles_text, inline=False)
    embed.set_footer(text="Paraíso Morboso 2026 © - El Heraldo 🪽")

    await interaction.response.send_message(embed=embed)


# ---------------------------------------------------------------------------
# Miembro de la Semana
# ---------------------------------------------------------------------------

def motw_last_scheduled(now: datetime) -> datetime:
    """Último momento programado (día/hora configurables, hora local) que ya
    pasó respecto a `now`."""
    weekday, hour = get_motw_weekday(), get_motw_hour()
    days_back = (now.weekday() - weekday) % 7
    scheduled = (now - timedelta(days=days_back)).replace(
        hour=hour, minute=0, second=0, microsecond=0
    )
    if scheduled > now:
        scheduled -= timedelta(days=7)
    return scheduled


def motw_mark_current_slot(now: datetime | None = None) -> None:
    """Llamar tras cambiar el horario: da por "ya pasado" el turno más reciente del
    nuevo horario, para que el cambio solo afecte al PRÓXIMO anuncio y no dispare uno
    inmediato con la semana a medias. Solo avanza el marcador, nunca lo retrocede
    (así tampoco se duplica un anuncio ya hecho hoy)."""
    new_slot = motw_last_scheduled(now or datetime.now(STREAK_TZ)).date().isoformat()
    last = db_meta_get("motw_last_slot")
    if last is None or new_slot > last:
        db_meta_set("motw_last_slot", new_slot)


@tasks.loop(minutes=10)
async def member_of_the_week_loop() -> None:
    """Revisa cada 10 min si toca el anuncio. Al comparar contra el último
    anuncio guardado en la DB, también se recupera si el bot estaba caído a la hora."""
    try:
        slot = motw_last_scheduled(datetime.now(STREAK_TZ)).date().isoformat()
        last = db_meta_get("motw_last_slot")
        if last is None:
            # Primer arranque: no anunciar con datos parciales, esperar al próximo turno.
            db_meta_set("motw_last_slot", slot)
            return
        if last == slot:
            return
        db_meta_set("motw_last_slot", slot)  # se marca antes para no duplicar anuncios
        await announce_member_of_the_week()
    except Exception:
        traceback.print_exc()  # que un error no detenga el loop


async def announce_member_of_the_week(reset: bool = True) -> str | None:
    """reset=False es para /motw_test: anuncia con los datos reales pero no
    toca los contadores, para poder probar sin afectar la semana en curso.
    Devuelve None si se publicó bien, o el texto del error si Discord lo rechazó
    (en ese caso NO se reinician los contadores, para no perder la semana)."""
    channel = bot.get_channel(get_motw_channel_id())
    if channel is None:
        print("⚠️ Miembro de la Semana: no encontré el canal de anuncios configurado.")
        return "No encontré el canal de anuncios configurado."
    guild = channel.guild

    # Top 2 entre quienes siguen en el servidor.
    ranking: list[tuple[discord.Member, int]] = []
    for user_id, count in db_week_ranking():
        member = guild.get_member(user_id)
        punish_id = hp_punish_role_id()
        if punish_id and member is not None and any(r.id == punish_id for r in member.roles):
            continue  # castigado por el honeypot: no puede ganar
        if member is not None and condemnation_get(member.id) is not None:
            continue  # condenado: no puede ganar
        if member is not None and not member.bot:
            ranking.append((member, count))
            if len(ranking) == 2:
                break

    if not ranking:
        try:
            await channel.send("📊 ¡No hubo actividad esta semana!")
        except discord.HTTPException as e:
            print(f"No se pudo escribir en el canal de Miembro de la Semana: {e}")
            return str(e)
        if reset:
            db_reset_week()
        return None

    winner, winner_count = ranking[0]

    # Anuncio
    description = (
        f"¡Felicidades a {winner.mention} por ser el miembro más activo de la semana "
        f"con **{winner_count:,} mensajes**!"
    )
    if len(ranking) > 1:
        lead = winner_count - ranking[1][1]
        if lead > 0:
            description += f" Le sacó **{lead:,} mensaje{'s' if lead != 1 else ''}** de ventaja al segundo lugar."
        else:
            description += " Empató con el segundo lugar y ganó por desempate."

    embed = discord.Embed(
        title="👑 Miembro de la Semana" if reset else "🧪 Miembro de la Semana (prueba)",
        description=description,
        color=discord.Color.gold(),
        timestamp=datetime.now(timezone.utc),
    )
    embed.set_thumbnail(url=winner.display_avatar.url)
    embed.set_footer(text="Paraíso Morboso 2026 © - El Heraldo 🪽")
    try:
        await channel.send(embed=embed)
    except discord.HTTPException as e:
        print(f"No se pudo escribir en el canal de Miembro de la Semana: {e}")
        return str(e)

    if reset:
        db_reset_week()  # contadores de la nueva semana en cero (para TODOS, no solo el top)
    return None


@bot.tree.command(name="motw_set_schedule", description="Cambiar el día/hora del anuncio de Miembro de la Semana.")
@discord.app_commands.describe(dia="Día de la semana", hora="Hora del día (0-23, hora de RD)")
@discord.app_commands.choices(dia=[
    discord.app_commands.Choice(name=name, value=i) for i, name in enumerate(MOTW_WEEKDAY_NAMES)
])
@discord.app_commands.checks.has_permissions(kick_members=True)
async def motw_set_schedule(interaction: discord.Interaction, dia: discord.app_commands.Choice[int], hora: discord.app_commands.Range[int, 0, 23]) -> None:
    set_motw_schedule(dia.value, hora)
    motw_mark_current_slot()
    now = datetime.now(STREAK_TZ)
    next_run = motw_last_scheduled(now) + timedelta(days=7)
    await interaction.response.send_message(
        f"✅ Miembro de la Semana ahora se anuncia los **{dia.name}** a las **{hora}:00** (hora de RD).\n"
        f"Próximo anuncio: **{MOTW_WEEKDAY_NAMES[next_run.weekday()]} {next_run.day}/{next_run.month} a las {next_run.hour}:00**.",
        ephemeral=True,
    )
    await log_embed(
        interaction.guild, "⚙️ Horario de Miembro de la Semana actualizado",
        f"{interaction.user.mention} lo cambió a {dia.name} {hora}:00 (hora de RD).",
        discord.Color.blurple(),
    )


@motw_set_schedule.error
async def motw_set_schedule_error(interaction: discord.Interaction, error: discord.app_commands.AppCommandError) -> None:
    if isinstance(error, discord.app_commands.MissingPermissions):
        await interaction.response.send_message("No tienes permiso para usar este comando.", ephemeral=True)
    else:
        await interaction.response.send_message(f"Error: {error}", ephemeral=True)


@bot.tree.command(name="motw_set_channel", description="Cambiar el canal donde se anuncia el Miembro de la Semana.")
@discord.app_commands.describe(canal="Canal de texto o de anuncios donde se publicará")
@discord.app_commands.checks.has_permissions(kick_members=True)
async def motw_set_channel(interaction: discord.Interaction, canal: discord.TextChannel) -> None:
    # Validar antes de guardar: así no se configura un canal donde el bot no puede escribir.
    perms = canal.permissions_for(canal.guild.me)
    missing = [
        name for name, ok in (
            ("Ver canal", perms.view_channel),
            ("Enviar mensajes", perms.send_messages),
            ("Insertar enlaces", perms.embed_links),
        ) if not ok
    ]
    if missing:
        await interaction.response.send_message(
            f"❌ No guardé el cambio: el Heraldo no tiene estos permisos en {canal.mention}: "
            f"**{', '.join(missing)}**. Dáselos y vuelve a intentarlo.",
            ephemeral=True,
        )
        return

    set_motw_channel_id(canal.id)
    await interaction.response.send_message(
        f"✅ Miembro de la Semana se anunciará en {canal.mention}. Usa `/motw_test` para probarlo.",
        ephemeral=True,
    )
    await log_embed(
        interaction.guild, "⚙️ Canal de Miembro de la Semana actualizado",
        f"{interaction.user.mention} lo cambió a {canal.mention}.",
        discord.Color.blurple(),
    )


@motw_set_channel.error
async def motw_set_channel_error(interaction: discord.Interaction, error: discord.app_commands.AppCommandError) -> None:
    if isinstance(error, discord.app_commands.MissingPermissions):
        await interaction.response.send_message("No tienes permiso para usar este comando.", ephemeral=True)
    else:
        await interaction.response.send_message(f"Error: {error}", ephemeral=True)


@bot.tree.command(name="motw_test", description="Probar el anuncio de Miembro de la Semana ahora mismo, sin resetear los contadores reales.")
@discord.app_commands.checks.has_permissions(kick_members=True)
async def motw_test(interaction: discord.Interaction) -> None:
    if bot.get_channel(get_motw_channel_id()) is None:
        await interaction.response.send_message("No encuentro el canal de anuncios configurado (¿fue borrado o el bot perdió acceso?). Elige otro con /motw_set_channel.", ephemeral=True)
        return
    await interaction.response.send_message("Probando el anuncio de Miembro de la Semana (no se resetean contadores)...", ephemeral=True)
    error = await announce_member_of_the_week(reset=False)
    if error:
        await interaction.followup.send(
            f"❌ No pude publicar en el canal de anuncios: `{error}`\n"
            "Revisa que el Heraldo tenga permisos de **Ver canal**, **Enviar mensajes** "
            "e **Insertar enlaces** en ese canal.",
            ephemeral=True,
        )
    else:
        await interaction.followup.send("✅ Anuncio de prueba publicado.", ephemeral=True)


@motw_test.error
async def motw_test_error(interaction: discord.Interaction, error: discord.app_commands.AppCommandError) -> None:
    if isinstance(error, discord.app_commands.MissingPermissions):
        await interaction.response.send_message("No tienes permiso para usar este comando.", ephemeral=True)
    else:
        await interaction.response.send_message(f"Error: {error}", ephemeral=True)


# ---------------------------------------------------------------------------
# 7. HONEYPOT (canales trampa para bots de spam)
# ---------------------------------------------------------------------------
# Un canal visible para todos donde ningún miembro real escribiría. Quien postee
# en él (y no esté exento) recibe el castigo configurado en segundos.
# Todo se configura con /honeypot (config, add, remove, create, warning_text,
# exempt_add, exempt_remove, history, resume); los valores de abajo son por defecto.

HONEYPOT_ACTION_LABELS = {
    "role": "Purgar y aplicar rol de castigo",
    "log": "Solo registrar",
    "timeout": "Aislar (timeout)",
}
HONEYPOT_RETENTION_DEFAULT_MINUTES = 30 * 24 * 60  # el historial (y el texto guardado) se borra a los 30 días
HONEYPOT_PURGE_DEFAULT = ("time", 24 * 60)  # por defecto: mensajes de las últimas 24 h (sin tope máximo)
HONEYPOT_TIMEOUT_MINUTES_DEFAULT = 24 * 60  # duración del timeout (1 min a 28 días)
HONEYPOT_TIMEOUT_MIN_MINUTES = 1
HONEYPOT_TIMEOUT_MAX_MINUTES = 28 * 24 * 60  # límite de Discord para timeouts
HONEYPOT_WARNING_TEXT_DEFAULT = (
    "Este canal es un **honeypot**: una trampa que atrapa bots de spam y que todos los "
    "bots ven. **Cualquier mensaje enviado aquí activa un castigo automático.** "
    "Si puedes leer esto, no envíes mensajes en este canal."
)
# Protección contra fallos: si varios miembros ANTIGUOS postean en la trampa en pocos
# minutos, la trampa apunta casi seguro a un canal que tu comunidad usa de verdad.
HONEYPOT_MISFIRE_MEMBER_AGE = timedelta(days=30)
HONEYPOT_MISFIRE_WINDOW = timedelta(minutes=5)
HONEYPOT_MISFIRE_THRESHOLD = 3

_hp_busy: set[int] = set()  # usuarios en pleno castigo (evita doble castigo si postea en varias trampas)
_hp_veteran_hits: list[tuple[datetime, int]] = []


# --- Persistencia -----------------------------------------------------------

def honeypot_db_init() -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS honeypot_channels ("
        "channel_id INTEGER PRIMARY KEY, warning_message_id INTEGER)"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS honeypot_exempt ("
        "kind TEXT NOT NULL, target_id INTEGER NOT NULL, PRIMARY KEY (kind, target_id))"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS honeypot_punished ("
        "user_id INTEGER PRIMARY KEY, role_ids TEXT NOT NULL, punished_at TEXT NOT NULL)"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS honeypot_triggers ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, username TEXT, "
        "channel_id INTEGER, content TEXT, action TEXT, success INTEGER, note TEXT, "
        "account_created TEXT, joined_at TEXT, triggered_at TEXT)"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS condemnations ("
        "user_id INTEGER PRIMARY KEY, guild_id INTEGER NOT NULL, role_id INTEGER NOT NULL DEFAULT 0, role_ids TEXT NOT NULL, "
        "reason TEXT NOT NULL, duration_minutes INTEGER, condemned_at TEXT NOT NULL, "
        "expires_at TEXT, origin TEXT NOT NULL, applied_by INTEGER, active INTEGER NOT NULL DEFAULT 1, "
        "pardoned_by INTEGER, pardoned_at TEXT, resolution TEXT, announcement_message_id INTEGER)"
    )
    try:
        conn.execute("ALTER TABLE condemnations ADD COLUMN role_id INTEGER NOT NULL DEFAULT 0")
    except sqlite3.OperationalError:
        pass
    for column_sql in (
        "ALTER TABLE condemnations ADD COLUMN pardoned_by INTEGER",
        "ALTER TABLE condemnations ADD COLUMN pardoned_at TEXT",
        "ALTER TABLE condemnations ADD COLUMN resolution TEXT",
        "ALTER TABLE condemnations ADD COLUMN announcement_message_id INTEGER",
    ):
        try:
            conn.execute(column_sql)
        except sqlite3.OperationalError:
            pass
    # Migración de la tabla histórica del honeypot: lo ya castigado pasa a ser una
    # condena activa indefinida, sin perder los roles que había guardado.
    legacy = conn.execute(
        "SELECT user_id, role_ids, punished_at FROM honeypot_punished"
    ).fetchall()
    for user_id, role_ids, punished_at in legacy:
        conn.execute(
            "INSERT OR IGNORE INTO condemnations "
            "(user_id, guild_id, role_ids, reason, duration_minutes, condemned_at, expires_at, origin, applied_by, active) "
            "VALUES (?, 0, ?, ?, NULL, ?, NULL, 'honeypot', NULL, 1)",
            (user_id, role_ids, "Condena heredada del honeypot", punished_at),
        )
    conn.commit()
    conn.close()
    hp_prune_history()


_hp_meta_cache: dict[str, str | None] = {}
_hp_trap_cache: set[int] | None = None


def hp_meta_get(key: str) -> str | None:
    """Lectura de configuración con caché en memoria (el listener corre en cada mensaje)."""
    if key not in _hp_meta_cache:
        _hp_meta_cache[key] = db_meta_get(key)
    return _hp_meta_cache[key]


def hp_meta_set(key: str, value: str) -> None:
    db_meta_set(key, value)
    _hp_meta_cache.pop(key, None)


def hp_trap_ids() -> set[int]:
    global _hp_trap_cache
    if _hp_trap_cache is None:
        _hp_trap_cache = set(hp_traps())
    return _hp_trap_cache


def hp_traps() -> dict[int, int | None]:
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("SELECT channel_id, warning_message_id FROM honeypot_channels").fetchall()
    conn.close()
    return {r[0]: r[1] for r in rows}


def hp_add_trap(channel_id: int) -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.execute("INSERT OR IGNORE INTO honeypot_channels (channel_id) VALUES (?)", (channel_id,))
    conn.commit()
    conn.close()
    global _hp_trap_cache
    _hp_trap_cache = None


def hp_remove_trap(channel_id: int) -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM honeypot_channels WHERE channel_id = ?", (channel_id,))
    conn.commit()
    conn.close()
    global _hp_trap_cache
    _hp_trap_cache = None


def hp_set_warning_message(channel_id: int, message_id: int | None) -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.execute("UPDATE honeypot_channels SET warning_message_id = ? WHERE channel_id = ?", (message_id, channel_id))
    conn.commit()
    conn.close()


def hp_exempt_ids(kind: str) -> set[int]:
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("SELECT target_id FROM honeypot_exempt WHERE kind = ?", (kind,)).fetchall()
    conn.close()
    return {r[0] for r in rows}


def hp_exempt_add(kind: str, target_id: int) -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.execute("INSERT OR IGNORE INTO honeypot_exempt (kind, target_id) VALUES (?, ?)", (kind, target_id))
    conn.commit()
    conn.close()


def hp_exempt_remove(kind: str, target_id: int) -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM honeypot_exempt WHERE kind = ? AND target_id = ?", (kind, target_id))
    conn.commit()
    conn.close()


def hp_save_punished(user_id: int, role_ids: list[int]) -> None:
    """Guarda los roles quitados para poder devolverlos con /liberar."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO honeypot_punished (user_id, role_ids, punished_at) VALUES (?, ?, ?) "
        "ON CONFLICT(user_id) DO UPDATE SET role_ids = excluded.role_ids, punished_at = excluded.punished_at",
        (user_id, json.dumps(role_ids), datetime.now(timezone.utc).isoformat()),
    )
    conn.commit()
    conn.close()


def hp_get_punished(user_id: int) -> list[int] | None:
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute("SELECT role_ids FROM honeypot_punished WHERE user_id = ?", (user_id,)).fetchone()
    conn.close()
    return json.loads(row[0]) if row else None


def hp_clear_punished(user_id: int) -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM honeypot_punished WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()


def condemnation_get(user_id: int, active_only: bool = True) -> sqlite3.Row | None:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    query = "SELECT * FROM condemnations WHERE user_id = ?"
    if active_only:
        query += " AND active = 1"
    row = conn.execute(query, (user_id,)).fetchone()
    conn.close()
    return row


def condemnation_save(
    user_id: int, guild_id: int, role_id: int, role_ids: list[int], reason: str,
    duration_minutes: int | None, origin: str, applied_by: int | None,
    condemned_at: datetime | None = None,
) -> None:
    when = condemned_at or datetime.now(timezone.utc)
    expires = when + timedelta(minutes=duration_minutes) if duration_minutes else None
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO condemnations "
        "(user_id, guild_id, role_id, role_ids, reason, duration_minutes, condemned_at, expires_at, origin, applied_by, active, pardoned_by, pardoned_at, resolution, announcement_message_id) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, NULL, NULL, NULL, NULL) "
        "ON CONFLICT(user_id) DO UPDATE SET guild_id=excluded.guild_id, role_ids=excluded.role_ids, "
        "role_id=excluded.role_id, reason=excluded.reason, duration_minutes=excluded.duration_minutes, condemned_at=excluded.condemned_at, "
        "expires_at=excluded.expires_at, origin=excluded.origin, applied_by=excluded.applied_by, active=1, "
        "pardoned_by=NULL, pardoned_at=NULL, resolution=NULL, announcement_message_id=NULL",
        (user_id, guild_id, role_id, json.dumps(role_ids), reason, duration_minutes, when.isoformat(),
         expires.isoformat() if expires else None, origin, applied_by),
    )
    conn.commit()
    conn.close()


def condemnation_deactivate(
    user_id: int, *, resolution: str | None = None, resolved_by: int | None = None
) -> None:
    conn = sqlite3.connect(DB_PATH)
    if resolution == "pardoned":
        conn.execute(
            "UPDATE condemnations SET active = 0, pardoned_by = ?, pardoned_at = ?, resolution = 'pardoned' WHERE user_id = ?",
            (resolved_by, datetime.now(timezone.utc).isoformat(), user_id),
        )
    elif resolution:
        conn.execute("UPDATE condemnations SET active = 0, resolution = ? WHERE user_id = ?", (resolution, user_id))
    else:
        conn.execute("UPDATE condemnations SET active = 0 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()
    hp_clear_punished(user_id)


def condemnation_add_saved_roles(user_id: int, new_ids: list[int]) -> None:
    """Añade a la fotografía de roles de una condena activa los que un moderador/bot intentó
    darle mientras estaba condenado, para que también se le devuelvan al liberarlo."""
    row = condemnation_get(user_id)
    if row is None or not new_ids:
        return
    merged = condemnation_parse_role_ids(row["role_ids"])
    for rid in new_ids:
        if rid not in merged:
            merged.append(rid)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("UPDATE condemnations SET role_ids = ? WHERE user_id = ? AND active = 1", (json.dumps(merged), user_id))
    conn.commit()
    conn.close()


def condemnation_is_expired(row: sqlite3.Row) -> bool:
    return bool(row["expires_at"]) and datetime.fromisoformat(row["expires_at"]) <= datetime.now(timezone.utc)


def condemnation_list(guild_id: int) -> list[sqlite3.Row]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT * FROM condemnations WHERE active = 1 AND (guild_id = ? OR guild_id = 0) "
        "AND (expires_at IS NULL OR expires_at > ?) ORDER BY condemned_at DESC",
        (guild_id, datetime.now(timezone.utc).isoformat()),
    ).fetchall()
    conn.close()
    return rows


def condemnation_default_duration_minutes() -> int | None:
    """Duración predeterminada para nuevas condenas. None = indefinida."""
    value = db_meta_get("condemnation_default_duration")
    if not value or value.strip().lower() in {"indefinida", "indefinido", "none", "null", "0"}:
        return None
    try:
        return parse_duration(value, 1, CONDEMNATION_MAX_MINUTES)
    except ValueError:
        return None


def set_condemnation_default_duration(value: str | None) -> None:
    db_meta_set("condemnation_default_duration", value or "indefinida")


def condemnation_channel_id() -> int:
    value = db_meta_get("condemned_channel_id")
    return int(value) if value else CONDEMNED_CHANNEL_ID


def set_condemnation_channel_id(channel_id: int) -> None:
    db_meta_set("condemned_channel_id", str(channel_id))


def condemnation_duration_text(row: sqlite3.Row) -> str:
    if row["expires_at"] is None:
        return "Indefinida"
    expires = datetime.fromisoformat(row["expires_at"])
    return f"hasta {discord.utils.format_dt(expires, 'R')} ({discord.utils.format_dt(expires, 'f')})"


def condemnation_origin_label(origin: str) -> str:
    return {
        "honeypot": "🍯 Honeypot",
        "command": "⌨️ Comando",
        "reaction": "☠️ Reacción",
        "role": "🎭 Rol otorgado a mano",
        "raid": "🛡️ Raid Protection",
    }.get(origin, origin)


def condemnation_parse_role_ids(value: str) -> list[int]:
    try:
        return [int(x) for x in json.loads(value)]
    except (TypeError, ValueError, json.JSONDecodeError):
        return []


def hp_log_trigger(member: discord.Member, channel_id: int, content: str, action: str,
                   success: bool, note: str) -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO honeypot_triggers (user_id, username, channel_id, content, action, success, note, "
        "account_created, joined_at, triggered_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            member.id, str(member), channel_id, content[:1500], action, int(success), note,
            member.created_at.isoformat(),
            member.joined_at.isoformat() if member.joined_at else None,
            datetime.now(timezone.utc).isoformat(),
        ),
    )
    conn.commit()
    conn.close()
    hp_prune_history()


def hp_retention_minutes() -> int:
    v = hp_meta_get("honeypot_retention_minutes")
    return int(v) if v else HONEYPOT_RETENTION_DEFAULT_MINUTES


def hp_prune_history() -> None:
    """Borra capturas (con el texto de los mensajes) más antiguas que la retención."""
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=hp_retention_minutes())
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM honeypot_triggers WHERE triggered_at < ?", (cutoff.isoformat(),))
    conn.commit()
    conn.close()


def hp_recent_triggers(limit: int = 10) -> list[sqlite3.Row]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM honeypot_triggers ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    conn.close()
    return rows


def hp_total_triggers() -> int:
    conn = sqlite3.connect(DB_PATH)
    total = conn.execute("SELECT COUNT(*) FROM honeypot_triggers WHERE success = 1").fetchone()[0]
    conn.close()
    return total


# --- Configuración (guardada en meta) ---------------------------------------

def honeypot_enabled() -> bool:
    return hp_meta_get("honeypot_enabled") == "1"


def honeypot_paused() -> bool:
    return hp_meta_get("honeypot_paused") == "1"


def hp_action() -> str:
    v = hp_meta_get("honeypot_action")
    if v in (None, "", "kick", "ban"):  # kick/ban ya no existen: el valor por defecto es el rol de castigo
        return "role"
    return v


def hp_punish_role_id() -> int:
    v = hp_meta_get("honeypot_punish_role")
    return int(v) if v else 0


def hp_protected_channel_reason(channel: discord.abc.GuildChannel) -> str | None:
    """Canales del propio Heraldo que nunca deben ser una trampa."""
    if channel.id == get_log_channel_id():
        return "es el canal de logs del Heraldo"
    if channel.id == get_motw_channel_id():
        return "es el canal del Miembro de la Semana"
    if channel.id == RECOVERY_CHANNEL_ID:
        return "es el canal de recuperación"
    ref = db_meta_get("verify_panel_ref")
    if ref:
        try:
            if int(ref.split(":")[0]) == channel.id:
                return "es el canal del panel de verificación"
        except ValueError:
            pass
    return None


def hp_role_problem(role: discord.Role, guild: discord.Guild) -> str | None:
    """Motivo por el que el Heraldo no puede usar este rol como rol de castigo, o None."""
    if role.is_default():
        return "es @everyone"
    if role.managed:
        return "es un rol gestionado por una integración o un bot"
    if role >= guild.me.top_role:
        return "está al mismo nivel o por encima del rol más alto del Heraldo"
    return None


_DURATION_RE = re.compile(r"(\d+)\s*(d(?:[ií]as?)?|h(?:oras?)?|m(?:in(?:utos?)?)?)(?![a-záéíóú])", re.IGNORECASE)


def parse_duration(text: str, min_minutes: int, max_minutes: int) -> int:
    """Convierte '30m', '12h', '2d' o '1d 12h 30m' (también 'días/horas/minutos') en minutos.
    '0' significa sin duración (solo válido si min_minutes es 0). Lanza ValueError con
    un mensaje listo para mostrar al usuario."""
    raw = text.strip().lower()
    example = "Usa d (días), h (horas) y m (minutos), por ejemplo `30m`, `12h`, `2d` o `1d 12h 30m`."
    if raw == "0":
        if min_minutes > 0:
            raise ValueError(f"El mínimo es {format_duration(min_minutes)}. {example}")
        return 0
    matches = list(_DURATION_RE.finditer(raw))
    leftover = _DURATION_RE.sub("", raw).replace(",", "").replace(" y ", "").strip()
    if not matches or leftover:
        raise ValueError(f"No entendí `{text}`. {example}")
    total = 0
    for m in matches:
        unit = m.group(2)[0]
        total += int(m.group(1)) * {"d": 1440, "h": 60, "m": 1}[unit]
    if total < min_minutes or total > max_minutes:
        raise ValueError(
            f"`{text}` queda fuera del rango permitido "
            f"({format_duration(min_minutes)} – {format_duration(max_minutes)})."
        )
    return total


def format_duration(minutes: int) -> str:
    if minutes <= 0:
        return "0 min"
    d, rest = divmod(minutes, 1440)
    h, m = divmod(rest, 60)
    parts = [f"{d} d" if d else "", f"{h} h" if h else "", f"{m} min" if m else ""]
    return " ".join(p for p in parts if p)


def hp_purge_spec() -> tuple[str, int]:
    """(tipo, valor): none | all | count (N mensajes) | time (minutos hacia atrás)."""
    v = hp_meta_get("honeypot_purge_spec")
    if v:
        kind, _, val = v.partition(":")
        return kind, int(val or 0)
    old = hp_meta_get("honeypot_purge_minutes")  # compatibilidad con versiones anteriores
    if old is not None:
        return ("time", int(old)) if int(old) > 0 else ("none", 0)
    old = hp_meta_get("honeypot_purge_hours")
    if old is not None:
        return ("time", int(old) * 60) if int(old) > 0 else ("none", 0)
    return HONEYPOT_PURGE_DEFAULT


def hp_timeout_minutes() -> int:
    v = hp_meta_get("honeypot_timeout_minutes")
    if v is not None:
        return int(v)
    old = hp_meta_get("honeypot_timeout_hours")
    return int(old) * 60 if old is not None else HONEYPOT_TIMEOUT_MINUTES_DEFAULT


def hp_warning_enabled() -> bool:
    return hp_meta_get("honeypot_warning_enabled") != "0"  # activado por defecto


def hp_warning_style() -> str:
    value = hp_meta_get("honeypot_warning_style")
    return value if value in ("text", "custom") else "text"


def hp_warning_text() -> str:
    return hp_meta_get("honeypot_warning_text") or HONEYPOT_WARNING_TEXT_DEFAULT


def hp_warning_custom() -> dict[str, str]:
    return {
        "title": hp_meta_get("honeypot_warning_title") or "⚠️ No escribas en este canal",
        "description": hp_meta_get("honeypot_warning_description") or HONEYPOT_WARNING_TEXT_DEFAULT,
        "color": hp_meta_get("honeypot_warning_color") or "F1C40F",
        "image": hp_meta_get("honeypot_warning_image") or "",
        "thumbnail": hp_meta_get("honeypot_warning_thumbnail") or "",
        "footer": hp_meta_get("honeypot_warning_footer") or "",
    }


def hp_ping_role_id() -> int:
    v = hp_meta_get("honeypot_ping_role")
    return int(v) if v else 0


def hp_is_exempt(member: discord.Member) -> bool:
    """Dueño, administradores y quien tenga Gestionar servidor siempre están exentos."""
    if member.guild.owner_id == member.id:
        return True
    perms = member.guild_permissions
    if (perms.administrator or perms.manage_guild or perms.manage_messages
            or perms.kick_members or perms.ban_members or perms.moderate_members):
        return True  # el equipo de moderación nunca cae en la trampa
    if member.id in hp_exempt_ids("member"):
        return True
    exempt_roles = hp_exempt_ids("role")
    return any(r.id in exempt_roles for r in member.roles)


def hp_config_summary(guild: discord.Guild) -> str:
    traps = hp_traps()
    trap_text = ", ".join(f"<#{cid}>" for cid in traps) or "—"
    ping = f"<@&{hp_ping_role_id()}>" if hp_ping_role_id() else "—"
    estado = "✅ Activado" if honeypot_enabled() else "❌ Desactivado"
    if honeypot_paused():
        estado += " · ⏸️ **PAUSADO** por protección contra fallos (`/honeypot resume`)"
    lines = [
        f"**Estado:** {estado}",
        f"**Canales trampa:** {trap_text}",
        f"**Acción:** {HONEYPOT_ACTION_LABELS.get(hp_action(), hp_action())}",
        f"**Rol de castigo:** {f'<@&{hp_punish_role_id()}>' if hp_punish_role_id() else '—'}",
        f"**Purga al castigado:** {format_purge_spec(*hp_purge_spec())}",
        f"**Duración del timeout:** {format_duration(hp_timeout_minutes())}",
        f"**Aviso fijado:** {'sí' if hp_warning_enabled() else 'no'}"
        + (" (texto personalizado)" if hp_meta_get("honeypot_warning_text") else " (texto por defecto)"),
        f"**Rol a mencionar en reportes:** {ping}",
        f"**Roles exentos:** {', '.join(f'<@&{i}>' for i in hp_exempt_ids('role')) or '—'}",
        f"**Miembros exentos:** {', '.join(f'<@{i}>' for i in hp_exempt_ids('member')) or '—'}",
        f"**Capturas en el historial:** {hp_total_triggers()} (se guardan {format_duration(hp_retention_minutes())})",
    ]
    return "\n".join(lines)


# --- Aviso fijado -----------------------------------------------------------

def hp_warning_embed(channel: discord.abc.GuildChannel | None = None) -> discord.Embed:
    ctx = VarContext(channel.guild if channel is not None else None, None, channel)
    if hp_warning_style() == "custom":
        cfg = hp_warning_custom()
        try:
            color = discord.Color(int(cfg["color"].lstrip("#"), 16))
        except ValueError:
            color = discord.Color.gold()
        embed = discord.Embed(
            title=render_vars(cfg["title"], ctx, 256),
            description=render_vars(cfg["description"], ctx, 4096), color=color,
        )
        image = render_url_var(cfg["image"], ctx) if cfg["image"] else ""
        if image:
            embed.set_image(url=image)
        thumbnail = render_url_var(cfg["thumbnail"], ctx) if cfg["thumbnail"] else ""
        if thumbnail:
            embed.set_thumbnail(url=thumbnail)
        footer = render_vars(cfg["footer"], ctx, 2048) if cfg["footer"] else ""
        if footer:
            embed.set_footer(text=footer)
        return embed
    return discord.Embed(
        title="⚠️ No escribas en este canal",
        description=render_vars(hp_warning_text(), ctx, 4096),
        color=discord.Color.gold(),
    )


async def hp_sync_warning(channel: discord.TextChannel) -> str | None:
    """Publica/actualiza (o borra) el aviso fijado de un canal trampa. Devuelve un
    texto de error o None si todo fue bien."""
    msg_id = hp_traps().get(channel.id)
    existing: discord.Message | None = None
    if msg_id:
        try:
            existing = await channel.fetch_message(msg_id)
        except discord.NotFound:
            existing = None
        except discord.HTTPException as e:
            return f"{channel.mention}: no pude leer el aviso (`{e}`)"

    try:
        if not hp_warning_enabled():
            if existing:
                await existing.delete()
            hp_set_warning_message(channel.id, None)
            return None
        if existing:
            await existing.edit(embed=hp_warning_embed(channel))
            if not existing.pinned:
                await existing.pin()
            return None
        message = await channel.send(embed=hp_warning_embed(channel))
        await message.pin()
        hp_set_warning_message(channel.id, message.id)
        # Quita el mensaje de sistema "X ha fijado un mensaje".
        async for m in channel.history(limit=5):
            if m.type == discord.MessageType.pins_add:
                await m.delete()
                break
    except discord.Forbidden:
        return f"{channel.mention}: faltan permisos (Enviar mensajes y Gestionar mensajes)"
    except discord.HTTPException as e:
        return f"{channel.mention}: error al publicar el aviso (`{e}`)"
    return None


async def hp_sync_all_warnings(guild: discord.Guild) -> list[str]:
    errors: list[str] = []
    for channel_id in list(hp_traps()):
        channel = guild.get_channel(channel_id)
        if isinstance(channel, discord.TextChannel):
            err = await hp_sync_warning(channel)
            if err:
                errors.append(err)
    return errors


# --- Castigo ----------------------------------------------------------------

# --- Motor de purga (sin límites): lo usan el honeypot y /purge ----------------

PURGE_MAX_MINUTES = 100 * 365 * 24 * 60  # 100 años: en la práctica, sin tope
_purge_running: set[tuple[int, int]] = set()  # (guild_id, user_id) con una purga en curso


@dataclass
class PurgeResult:
    deleted: int = 0
    failed: int = 0
    channels_scanned: int = 0
    channels_skipped: int = 0


def parse_purge_spec(text: str) -> tuple[str, int]:
    """'todo' | '200 mensajes' | '30m' / '12h' / '2d' / '1d 12h' | '0' -> (tipo, valor).
    Tipos: none, all, count (N mensajes), time (minutos hacia atrás)."""
    raw = text.strip().lower()
    if raw in ("0", "ninguno", "nada", "no"):
        return "none", 0
    if raw in ("todo", "todos", "all", "siempre"):
        return "all", 0
    m = re.fullmatch(r"(\d+)\s*(?:msgs?|mensajes?)", raw)
    if m:
        n = int(m.group(1))
        if n < 1:
            raise ValueError("La cantidad de mensajes debe ser al menos 1.")
        return "count", n
    try:
        return "time", parse_duration(raw, 1, PURGE_MAX_MINUTES)
    except ValueError:
        raise ValueError(
            f"No entendí `{text}`. Usa `todo`, una cantidad (`200 mensajes`), un tiempo hacia atrás "
            f"(`30m`, `12h`, `2d`, `1d 12h 30m`) o `0` para no borrar."
        )


def format_purge_spec(kind: str, value: int) -> str:
    if kind == "none":
        return "no borrar"
    if kind == "all":
        return "todos sus mensajes"
    if kind == "count":
        return f"sus últimos {value} mensajes"
    return f"mensajes de los últimos {format_duration(value)}"


async def purge_targets(guild: discord.Guild, only=None, after: datetime | None = None) -> list:
    """Canales y hilos donde buscar mensajes (incluye hilos activos y archivados públicos)."""
    if only is not None:
        if isinstance(only, discord.ForumChannel):
            threads = list(only.threads)
            try:
                async for t in only.archived_threads(limit=None):
                    if after is not None and t.archive_timestamp < after:
                        break  # vienen del más reciente al más antiguo
                    threads.append(t)
            except discord.HTTPException:
                pass
            return threads
        return [only]
    targets: dict[int, object] = {}
    for ch in [*guild.text_channels, *guild.voice_channels, *guild.stage_channels, *guild.threads]:
        targets[ch.id] = ch
    for parent in [*guild.text_channels, *guild.forums]:
        try:
            async for t in parent.archived_threads(limit=None):
                if after is not None and t.archive_timestamp < after:
                    break  # archivado antes del corte: no puede tener mensajes más nuevos
                targets[t.id] = t
        except discord.HTTPException:
            continue  # sin permiso para ver hilos archivados de ese canal
    for forum in guild.forums:
        for t in forum.threads:
            targets[t.id] = t
    return list(targets.values())


_PURGE_URL_RE = re.compile(r"https?://[^\s<>]+|(?:www\.)[^\s<>]+", re.IGNORECASE)


def _purge_message_matches(message: discord.Message, content_type: str) -> bool:
    """Determina si un mensaje entra en el filtro multimedia solicitado por /purge."""
    if content_type == "all":
        return True

    content = (message.content or "").strip()
    if content_type == "links":
        return bool(_PURGE_URL_RE.search(content))

    if content_type == "text":
        if not content:
            return False
        # Texto acompañado de una imagen o vídeo NO cuenta como texto puro.
        has_image_or_video = any(
            (a.content_type or "").lower().startswith(("image/", "video/"))
            or Path(a.filename).suffix.lower() in {
                ".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".tif", ".tiff",
                ".mp4", ".mov", ".webm", ".mkv", ".avi", ".m4v", ".mpeg", ".mpg",
            }
            for a in message.attachments
        )
        return not has_image_or_video

    return True


async def _collect_user_messages(
    ch, user_id: int, after, before, limit: int | None, content_type: str = "all"
) -> list[int]:
    ids: list[int] = []
    kwargs = {"limit": None, "after": after, "before": before}
    if limit is not None:
        kwargs["oldest_first"] = False  # para quedarnos con los más recientes
    async for m in ch.history(**kwargs):
        if m.author.id == user_id and _purge_message_matches(m, content_type):
            ids.append(m.id)
            if limit is not None and len(ids) >= limit:
                break
    return ids


async def _delete_ids(ch, ids: list[int]) -> tuple[int, int]:
    """Borra mensajes por id: en bloques de 100 los de menos de 14 días, uno a uno los antiguos."""
    bulk_cutoff = datetime.now(timezone.utc) - timedelta(days=14) + timedelta(minutes=10)
    recent = [i for i in ids if discord.utils.snowflake_time(i) > bulk_cutoff]
    old = [i for i in ids if discord.utils.snowflake_time(i) <= bulk_cutoff]
    deleted = failed = 0

    async def delete_one(message_id: int) -> None:
        nonlocal deleted, failed
        try:
            await ch.get_partial_message(message_id).delete()
            deleted += 1
        except discord.NotFound:
            pass  # ya no existe
        except discord.HTTPException:
            failed += 1

    for start in range(0, len(recent), 100):
        chunk = recent[start:start + 100]
        if len(chunk) == 1:
            await delete_one(chunk[0])
            continue
        try:
            await ch.delete_messages([discord.Object(i) for i in chunk])
            deleted += len(chunk)
        except discord.HTTPException:
            for message_id in chunk:  # un id inválido tumba el bloque: reintento uno a uno
                await delete_one(message_id)
    for message_id in old:
        await delete_one(message_id)
    return deleted, failed


async def purge_user_messages(
    guild: discord.Guild,
    user_id: int,
    *,
    channel=None,
    after: datetime | None = None,
    before: datetime | None = None,
    limit: int | None = None,
    progress=None,
    content_type: str = "all",
) -> PurgeResult:
    """Borra mensajes de un usuario (aunque ya no esté en el servidor), sin tope propio:
    - sin after/before/limit -> TODOS sus mensajes
    - after/before -> los de ese rango de tiempo
    - limit -> sus N mensajes más recientes (dentro del rango, si lo hay)
    `progress(hechos, total, borrados)` se llama a medida que avanza."""
    result = PurgeResult()
    targets = await purge_targets(guild, channel, after)
    sem = asyncio.Semaphore(4)  # 4 canales a la vez; discord.py gestiona el rate limit
    collected: list[tuple[object, list[int]]] = []
    done = 0

    async def work(ch) -> None:
        nonlocal done
        perms = ch.permissions_for(guild.me)
        if not (perms.view_channel and perms.read_message_history and perms.manage_messages):
            result.channels_skipped += 1
            return
        async with sem:
            try:
                ids = await _collect_user_messages(ch, user_id, after, before, limit, content_type)
                result.channels_scanned += 1
                if limit is None and ids:  # sin tope global: se borra canal a canal
                    d, f = await _delete_ids(ch, ids)
                    result.deleted += d
                    result.failed += f
                elif ids:
                    collected.append((ch, ids))
            except discord.HTTPException:
                result.channels_skipped += 1
        done += 1
        if progress:
            try:
                await progress(done, len(targets), result.deleted)
            except Exception:
                pass

    await asyncio.gather(*(work(ch) for ch in targets))

    if limit is not None and collected:
        # Los N más recientes entre todos los canales (el id de un mensaje crece con el tiempo).
        pairs = sorted(((i, ch) for ch, ids in collected for i in ids), key=lambda p: p[0], reverse=True)[:limit]
        by_channel: dict[int, tuple[object, list[int]]] = {}
        for message_id, ch in pairs:
            by_channel.setdefault(ch.id, (ch, []))[1].append(message_id)
        for ch, ids in by_channel.values():
            d, f = await _delete_ids(ch, ids)
            result.deleted += d
            result.failed += f
    return result


def purge_result_text(result: PurgeResult) -> str:
    text = f"**{result.deleted}** mensaje(s) borrado(s) en {result.channels_scanned} canal(es)/hilo(s)"
    if result.failed:
        text += f"; {result.failed} no se pudieron borrar"
    if result.channels_skipped:
        text += f"; {result.channels_skipped} omitido(s) por falta de permisos"
    return text


async def run_purge_job(
    guild: discord.Guild,
    user: discord.abc.User,
    *,
    scope_text: str,
    requested_by: str,
    channel=None,
    after: datetime | None = None,
    before: datetime | None = None,
    limit: int | None = None,
    progress=None,
    content_type: str = "all",
    title: str = "🧹 Purga completada",
) -> PurgeResult | None:
    """Ejecuta una purga con control de duplicados y reporta el resultado en el log."""
    key = (guild.id, user.id)
    if key in _purge_running:
        return None
    _purge_running.add(key)
    try:
        result = await purge_user_messages(
            guild, user.id, channel=channel, after=after, before=before, limit=limit,
            progress=progress, content_type=content_type
        )
    except Exception:
        traceback.print_exc()
        await log_embed(
            guild, "⚠️ Purga fallida",
            f"{requested_by} · {user.mention} · {scope_text}\nOcurrió un error; revisa los logs del bot.",
            discord.Color.red(),
        )
        raise
    finally:
        _purge_running.discard(key)
    await log_embed(
        guild, title,
        f"{requested_by} · {user.mention} (`{user.id}`)\nAlcance: {scope_text}\n{purge_result_text(result)}",
        discord.Color.green(),
    )
    return result


def hp_start_purge(member: discord.Member) -> str | None:
    """Lanza la purga del honeypot en segundo plano (sin tope: puede tardar). Devuelve un texto
    para el reporte, o None si la purga está desactivada."""
    kind, value = hp_purge_spec()
    if kind == "none":
        return None
    after = datetime.now(timezone.utc) - timedelta(minutes=value) if kind == "time" else None
    limit = value if kind == "count" else None
    scope = format_purge_spec(kind, value)
    asyncio.create_task(
        run_purge_job(
            member.guild, member, scope_text=scope, requested_by="🍯 Honeypot",
            after=after, limit=limit, title="🍯 Purga del honeypot completada",
        )
    )
    return f"purga en segundo plano ({scope})"


class _SyncGuard:
    """Marca los cambios de rol hechos por el propio Heraldo. Al terminar, la marca se mantiene unos
    segundos de gracia: el evento de gateway on_member_update puede llegar DESPUÉS de que
    member.edit() haya devuelto, y sin la gracia el Heraldo reaccionaría a sus propios cambios."""
    GRACE = 5.0

    def __init__(self) -> None:
        self._until: dict[int, float] = {}

    def add(self, user_id: int) -> None:
        self._until[user_id] = float("inf")

    def discard(self, user_id: int) -> None:
        if user_id in self._until:
            self._until[user_id] = time.monotonic() + self.GRACE

    def __contains__(self, user_id: object) -> bool:
        until = self._until.get(user_id)  # type: ignore[arg-type]
        if until is None:
            return False
        if time.monotonic() >= until:
            self._until.pop(user_id, None)  # type: ignore[arg-type]
            return False
        return True


_condemn_sync_busy = _SyncGuard()
_condemn_inflight: set[int] = set()


def condemnation_protection_reason(member: discord.Member) -> str | None:
    """Motivo por el que no se puede condenar a este miembro."""
    guild = member.guild
    if member.id == guild.owner_id:
        return "es el dueño del servidor"
    if member.guild_permissions.administrator:
        return "tiene el permiso Administrador y está exento"
    if member.top_role >= guild.me.top_role:
        return "su rol más alto es igual o superior al del Heraldo"
    if hp_is_exempt(member):
        return "es staff o está en la lista de exentos"
    return None


async def condemnation_send_pardon_dm(
    member: discord.Member,
    row: sqlite3.Row,
    pardoned_by: discord.abc.User,
    restored_count: int,
    lost_count: int,
) -> bool:
    condemned_at = datetime.fromisoformat(row["condemned_at"])
    pardoned_at = datetime.now(timezone.utc)
    case_id = condemnation_case_id(member, condemned_at)
    embed = discord.Embed(
        title="🕊️ CONDENA PERDONADA",
        description=(
            f"Tu condena del expediente **{case_id}** ha sido levantada. "
            "Tus roles guardados fueron restaurados en la medida permitida por la jerarquía del servidor."
        ),
        color=discord.Color.green(),
        timestamp=pardoned_at,
    )
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.add_field(name="Expediente", value=case_id, inline=True)
    embed.add_field(name="Condenado", value=f"{member.mention}\n{member}", inline=True)
    embed.add_field(name="Motivo original", value=str(row["reason"])[:1024], inline=False)
    embed.add_field(name="Condenado el", value=discord.utils.format_dt(condemned_at, "F"), inline=True)
    embed.add_field(name="Perdonado por", value=pardoned_by.mention, inline=True)
    embed.add_field(name="Perdonado el", value=discord.utils.format_dt(pardoned_at, "F"), inline=True)
    embed.add_field(name="Resultado", value=(f"🕊️ Condena levantada. **{restored_count}** rol(es) restaurado(s)" + (f"; ⚠️ **{lost_count}** no se pudieron restaurar." if lost_count else ".")), inline=False)
    embed.add_field(name="Origen", value=condemnation_origin_label(row["origin"]), inline=True)
    embed.add_field(name="Duración original", value=condemnation_duration_text(row), inline=True)
    embed.set_footer(text=f"{member.guild.name} · El Heraldo 🪽")
    try:
        await member.send(embed=embed)
        return True
    except discord.HTTPException:
        return False


def _build_condemnation_embed(
    guild: discord.Guild, member: discord.Member, reason: str,
    duration_minutes: int | None, origin: str, applied_by: discord.abc.User | None,
    *, source_message_url: str | None = None, source_channel_id: int | None = None,
    removed_role_ids: list[int] | None = None, when: datetime | None = None, case_id: str | None = None,
    include_pardon_button: bool = False,
) -> tuple[discord.Embed, discord.ui.View | None]:
    """Construye la MISMA tarjeta que se usa tanto en el canal de castigo como en el DM."""
    when = when or datetime.now(timezone.utc)
    case_id = case_id or condemnation_case_id(member, when)
    source_channel = guild.get_channel(source_channel_id) if source_channel_id else None

    render = lambda value: _condemnation_render_template(
        value, member=member, guild=guild, case_id=case_id, applied_by=applied_by,
        reason=reason, when=when, source_channel=source_channel,
        duration_minutes=duration_minutes, origin=origin, source_message_url=source_message_url,
    )

    embed = discord.Embed(
        title=render(condemnation_template_get("title"))[:256],
        description=render(condemnation_template_get("description"))[:4096],
        color=condemnation_template_color(),
        timestamp=when,
    )
    embed.set_thumbnail(url=member.display_avatar.url)

    def field(label_key: str, value: str, inline: bool = True) -> None:
        embed.add_field(name=condemnation_template_get(label_key)[:256], value=value[:1024] or "—", inline=inline)

    field("label_case", f"`{case_id}`", True)
    field("label_user", f"{member.mention}\n`{member}`", True)
    field("label_by", applied_by.mention if applied_by else "🤖 El Heraldo", True)
    field("label_reason", reason, False)
    field("label_when", f"{discord.utils.format_dt(when, 'F')}\n{discord.utils.format_dt(when, 'R')}", True)

    where = source_channel.mention if source_channel else ("Canal del mensaje original" if source_message_url else "No registrado")
    field("label_where", where, True)
    field("label_duration", format_duration(duration_minutes) if duration_minutes else "Indefinida", True)
    field("label_origin", condemnation_origin_label(origin), True)

    role_mentions = []
    for rid in removed_role_ids or []:
        role = guild.get_role(rid)
        if role is not None:
            role_mentions.append(f"`{role.name}`")
    field("label_roles", ", ".join(role_mentions) if role_mentions else "Ninguno (o no asignable)", False)

    if source_message_url:
        field("label_message", f"[🔗 Abrir mensaje que originó la condena]({source_message_url})", False)

    embed.set_footer(text=render(condemnation_template_get("footer"))[:2048])

    button_url = condemnation_template_get("button_url").strip()
    button_label = render(condemnation_template_get("button_label")).strip()[:80]
    view = None
    if button_url and re.match(r"^https?://", button_url, re.IGNORECASE):
        view = discord.ui.View(timeout=None)
        view.add_item(discord.ui.Button(label=button_label or "Ver información del caso", style=discord.ButtonStyle.link, url=button_url))
    if include_pardon_button:
        if view is None:
            view = discord.ui.View(timeout=None)
        view.add_item(discord.ui.Button(label="🕊️ Perdonar", style=discord.ButtonStyle.success, custom_id="heraldo:condemnation:pardon"))
    return embed, view


class CondemnationPardonView(discord.ui.View):
    def __init__(self) -> None:
        super().__init__(timeout=None)
        button = discord.ui.Button(
            label="🕊️ Perdonar",
            style=discord.ButtonStyle.success,
            custom_id="heraldo:condemnation:pardon",
        )
        button.callback = self.pardon_callback
        self.add_item(button)

    async def pardon_callback(self, interaction: discord.Interaction) -> None:
        # Acknowledge the interaction immediately. Si cualquier paso posterior
        # falla, Discord no mostrará "La aplicación no respondió".
        if interaction.guild is None or interaction.message is None:
            await interaction.response.send_message(
                "❌ Este botón solo funciona dentro del servidor.",
                ephemeral=True,
            )
            return

        try:
            await interaction.response.defer(ephemeral=True)

            mentions = interaction.message.mentions
            if not mentions:
                await interaction.followup.send(
                    "❌ No pude identificar al condenado asociado a este expediente.",
                    ephemeral=True,
                )
                return

            member = interaction.guild.get_member(mentions[0].id)
            if member is None:
                try:
                    member = await interaction.guild.fetch_member(mentions[0].id)
                except discord.HTTPException:
                    member = None

            if member is None:
                await interaction.followup.send(
                    "❌ Ese miembro ya no está disponible en el servidor.",
                    ephemeral=True,
                )
                return

            row = condemnation_get(member.id)
            if row is None:
                await interaction.followup.send(
                    "ℹ️ Este expediente ya no tiene una condena activa.",
                    ephemeral=True,
                )
                return

            is_admin = bool(
                getattr(interaction.user.guild_permissions, "administrator", False)
            )
            is_condemner = (
                row["applied_by"] is not None
                and int(row["applied_by"]) == interaction.user.id
            )
            if not (is_admin or is_condemner):
                await interaction.followup.send(
                    "⛔ No puedes perdonar esta condena. Solo puede hacerlo quien la aplicó o un administrador.",
                    ephemeral=True,
                )
                return

            ok, note = await release_condemned_member(
                member,
                released_by=interaction.user,
                pardon=True,
                announcement_message=interaction.message,
            )
            await interaction.followup.send(
                ("🕊️ " if ok else "❌ ") + note,
                ephemeral=True,
            )
        except Exception:
            traceback.print_exc()
            try:
                if interaction.response.is_done():
                    await interaction.followup.send(
                        "❌ Ocurrió un error al procesar el perdón. El error quedó registrado en los logs del bot.",
                        ephemeral=True,
                    )
                else:
                    await interaction.response.send_message(
                        "❌ Ocurrió un error al procesar el perdón. El error quedó registrado en los logs del bot.",
                        ephemeral=True,
                    )
            except Exception:
                traceback.print_exc()


async def condemnation_send_dm(
    member: discord.Member, reason: str, duration_minutes: int | None, origin: str,
    applied_by: discord.abc.User | None = None,
    *, source_message_url: str | None = None, source_channel_id: int | None = None,
    removed_role_ids: list[int] | None = None, when: datetime | None = None, case_id: str | None = None,
) -> bool:
    """Envía por DM la misma tarjeta de condena, incluido el botón configurable."""
    embed, view = _build_condemnation_embed(
        member.guild, member, reason, duration_minutes, origin, applied_by,
        source_message_url=source_message_url, source_channel_id=source_channel_id,
        removed_role_ids=removed_role_ids, when=when, case_id=case_id,
        include_pardon_button=False,
    )
    try:
        await member.send(embed=embed, view=view)
        return True
    except discord.HTTPException:
        return False


def condemnation_template_get(key: str) -> str:
    return db_meta_get(f"condemnation_template_{key}") or CONDEMNATION_TEMPLATE_DEFAULTS[key]


def condemnation_template_set(key: str, value: str) -> None:
    db_meta_set(f"condemnation_template_{key}", value[:1024])


def condemnation_template_reset() -> None:
    for key in CONDEMNATION_TEMPLATE_DEFAULTS:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("DELETE FROM meta WHERE key = ?", (f"condemnation_template_{key}",))
        conn.commit()
        conn.close()


def condemnation_template_color() -> discord.Color:
    raw = condemnation_template_get("color").strip().lstrip("#")
    try:
        value = int(raw, 16)
        if not 0 <= value <= 0xFFFFFF:
            raise ValueError
        return discord.Color(value)
    except ValueError:
        return discord.Color.dark_red()


def condemnation_case_id(member: discord.Member, when: datetime) -> str:
    # Identificador legible y estable para referirse al expediente sin exponer datos extra.
    return f"C-{when.astimezone(STREAK_TZ):%Y%m%d}-{member.id % 100000:05d}"


def _condemnation_render_template(text: str, *, member: discord.Member, guild: discord.Guild,
                                  case_id: str, applied_by: discord.abc.User | None,
                                  reason: str, when: datetime, source_channel: discord.abc.GuildChannel | None,
                                  duration_minutes: int | None, origin: str,
                                  source_message_url: str | None) -> str:
    values = {
        "{usuario}": member.mention,
        "{servidor}": guild.name,
        "{caso}": case_id,
        "{moderador}": applied_by.mention if applied_by else "El Heraldo",
        "{motivo}": reason,
        "{fecha}": discord.utils.format_dt(when, "F"),
        "{fecha_relativa}": discord.utils.format_dt(when, "R"),
        "{canal}": source_channel.mention if source_channel else "No registrado",
        "{duracion}": format_duration(duration_minutes) if duration_minutes else "Indefinida",
        "{origen}": condemnation_origin_label(origin),
        "{mensaje}": f"[Abrir mensaje]({source_message_url})" if source_message_url else "No disponible",
    }
    for key, value in values.items():
        text = text.replace(key, value)
    return text


async def condemnation_announce(
    guild: discord.Guild, member: discord.Member, reason: str,
    duration_minutes: int | None, origin: str, applied_by: discord.abc.User | None,
    *, source_message_url: str | None = None, source_channel_id: int | None = None,
    removed_role_ids: list[int] | None = None, when: datetime | None = None, case_id: str | None = None,
) -> int | None:
    channel = guild.get_channel(condemnation_channel_id())
    if not isinstance(channel, discord.TextChannel):
        return None
    embed, view = _build_condemnation_embed(
        guild, member, reason, duration_minutes, origin, applied_by,
        source_message_url=source_message_url, source_channel_id=source_channel_id,
        removed_role_ids=removed_role_ids, when=when, case_id=case_id,
        include_pardon_button=True,
    )
    try:
        message = await channel.send(
            content=member.mention, embed=embed, view=view,
            allowed_mentions=discord.AllowedMentions(users=[member], roles=False, everyone=False),
        )
        return message.id
    except discord.HTTPException:
        return None


async def condemnation_update_pardoned_card(
    member: discord.Member,
    row: sqlite3.Row,
    pardoned_by: discord.abc.User,
    restored_count: int,
    lost_count: int,
    message: discord.Message | None = None,
) -> bool:
    """Cierra la tarjeta original y publica una nueva tarjeta de resolución."""
    message_id = row["announcement_message_id"] if "announcement_message_id" in row.keys() else None
    channel = member.guild.get_channel(condemnation_channel_id())
    if not isinstance(channel, discord.TextChannel):
        return False

    try:
        if message is None:
            if not message_id:
                return False
            message = await channel.fetch_message(int(message_id))
        elif message.channel.id != channel.id:
            return False

        condemned_at = datetime.fromisoformat(row["condemned_at"])
        case_id = condemnation_case_id(member, condemned_at)
        pardoned_at = datetime.now(timezone.utc)

        # 1) Cerrar la tarjeta original del expediente. No se borra ni se reemplaza:
        # queda como registro histórico y ya no contiene acciones ejecutables.
        closed_embed = discord.Embed(
            title="🔒 EXPEDIENTE CERRADO",
            description=(
                f"El expediente **{case_id}** fue cerrado porque la condena "
                "fue levantada mediante perdón."
            ),
            color=discord.Color.dark_grey(),
            timestamp=pardoned_at,
        )
        closed_embed.set_thumbnail(url=member.display_avatar.url)
        closed_embed.add_field(name="Expediente", value=f"`{case_id}`", inline=True)
        closed_embed.add_field(name="Condenado", value=f"{member.mention}\n`{member}`", inline=True)
        closed_embed.add_field(name="Motivo original", value=str(row["reason"])[:1024], inline=False)
        closed_embed.add_field(name="Estado", value="🔒 Cerrado", inline=True)
        closed_embed.add_field(name="Resuelto por", value=pardoned_by.mention, inline=True)
        closed_embed.add_field(name="Cerrado el", value=discord.utils.format_dt(pardoned_at, "F"), inline=True)
        closed_embed.set_footer(text=f"{member.guild.name} · El Heraldo 🪽 · Expediente {case_id}")
        await message.edit(content=member.mention, embed=closed_embed, view=None)

        # 2) Crear una tarjeta NUEVA con la resolución del perdón.
        resolution = discord.Embed(
            title="🕊️ CONDENA PERDONADA",
            description=(
                f"El expediente **{case_id}** ha sido resuelto mediante perdón. "
                "Esta tarjeta registra la resolución del caso."
            ),
            color=discord.Color.green(),
            timestamp=pardoned_at,
        )
        resolution.set_thumbnail(url=member.display_avatar.url)
        resolution.add_field(name="Expediente", value=f"`{case_id}`", inline=True)
        resolution.add_field(name="Condenado", value=f"{member.mention}\n`{member}`", inline=True)
        resolution.add_field(name="Motivo original", value=str(row["reason"])[:1024], inline=False)
        resolution.add_field(name="Condenado el", value=discord.utils.format_dt(condemned_at, "F"), inline=True)
        resolution.add_field(name="Perdonado por", value=pardoned_by.mention, inline=True)
        resolution.add_field(name="Perdonado el", value=discord.utils.format_dt(pardoned_at, "F"), inline=True)
        result = f"🕊️ Condena levantada. **{restored_count}** rol(es) restaurado(s)"
        if lost_count:
            result += f"; ⚠️ **{lost_count}** no se pudieron restaurar."
        else:
            result += "."
        resolution.add_field(name="Resultado", value=result, inline=False)
        resolution.add_field(name="Origen", value=condemnation_origin_label(row["origin"]), inline=True)
        resolution.add_field(name="Duración original", value=condemnation_duration_text(row), inline=True)
        resolution.set_footer(text=f"{member.guild.name} · El Heraldo 🪽 · Resolución {case_id}")
        await channel.send(
            content=member.mention,
            embed=resolution,
            allowed_mentions=discord.AllowedMentions(users=[member], roles=False, everyone=False),
        )
        return True
    except discord.HTTPException:
        traceback.print_exc()
        return False


def condemnation_role_id(row: sqlite3.Row | None = None) -> int:
    if row is not None and row["role_id"]:
        return int(row["role_id"])
    return hp_punish_role_id()


async def condemnation_sync_roles(
    member: discord.Member,
    *,
    preserve_role_ids: list[int] | None = None,
    save_snapshot: bool = False,
    reason: str = "Condena de El Heraldo",
    role_id: int | None = None,
) -> tuple[bool, list[int], str]:
    """Deja solo el rol de condenado entre los roles asignables y conserva roles gestionados."""
    guild = member.guild
    punish_role = guild.get_role(role_id or hp_punish_role_id())
    if punish_role is None:
        return False, [], "No hay rol Condenado configurado; usa `/honeypot config rol_castigo` para elegirlo."
    problem = hp_role_problem(punish_role, guild)
    if problem:
        return False, [], f"El rol Condenado {problem}."

    source = preserve_role_ids if preserve_role_ids is not None else [r.id for r in member.roles]
    excluded = {punish_role.id}
    saved_ids = []
    for rid in source:
        role = guild.get_role(rid)
        # Solo se guardan roles que el Heraldo puede devolver (no @everyone ni gestionados).
        if rid in excluded or role is None or role.is_default() or role.managed or not role.is_assignable():
            continue
        saved_ids.append(rid)

    removed = [
        r for r in member.roles
        if r.id not in excluded and r.is_assignable() and not r.managed
    ]
    managed = [r for r in member.roles if r.managed and not r.is_default()]
    try:
        await member.edit(roles=managed + [punish_role], reason=reason)
    except discord.Forbidden:
        return False, [], "Faltan permisos para cambiar roles o la jerarquía del Heraldo no alcanza al usuario."
    except discord.HTTPException as e:
        return False, [], f"Error al cambiar roles: `{e}`"

    if save_snapshot:
        # Solo se guardan roles que realmente estaban antes de la condena y que el bot puede restaurar.
        hp_save_punished(member.id, saved_ids)
    return True, saved_ids, f"{len(removed)} rol(es) asignable(s) retirado(s); Tentad@ y Sin Verificar retirados."


async def condemn_member(
    member: discord.Member,
    *,
    reason: str,
    duration_minutes: int | None,
    purge_spec: tuple[str, int] | None,
    origin: str,
    applied_by: discord.abc.User | None,
    preserve_role_ids: list[int] | None = None,
    source_message_url: str | None = None,
    source_channel_id: int | None = None,
    send_dm: bool = True,
    announce: bool = True,
) -> tuple[bool, str]:
    """Motor único de condena. Lo usan honeypot, comando, reacción, rol manual y raid protection."""
    if member.bot:
        return False, "Los bots no se condenan."
    reason = (reason or "").strip()
    if not reason:
        automatic_reasons = {
            "raid": "🛡️ Protección RAID: ingreso detectado durante un patrón de incursión masiva.",
            "honeypot": "🍯 Honeypot: el miembro activó un canal trampa de seguridad.",
            "role": "🎭 El rol Condenado fue otorgado manualmente y activó el motor de condenas.",
            "reaction": "☠️ Condena aplicada mediante la reacción de moderación.",
        }
        reason = automatic_reasons.get(origin, "⚠️ Condena automática de seguridad de El Heraldo.")
    if member.id in _condemn_inflight:
        return False, "Ya hay una condena en proceso para este miembro."
    protection = condemnation_protection_reason(member)
    if protection:
        return False, f"No se puede condenar: {protection}."

    _condemn_inflight.add(member.id)
    try:
        return await _condemn_member_inner(
            member, reason=reason, duration_minutes=duration_minutes, purge_spec=purge_spec,
            origin=origin, applied_by=applied_by, preserve_role_ids=preserve_role_ids,
            source_message_url=source_message_url, source_channel_id=source_channel_id, send_dm=send_dm, announce=announce,
        )
    finally:
        _condemn_inflight.discard(member.id)


async def _condemn_member_inner(
    member: discord.Member,
    *,
    reason: str,
    duration_minutes: int | None,
    purge_spec: tuple[str, int] | None,
    origin: str,
    applied_by: discord.abc.User | None,
    preserve_role_ids: list[int] | None,
    source_message_url: str | None,
    source_channel_id: int | None,
    send_dm: bool,
    announce: bool,
) -> tuple[bool, str]:
    existing = condemnation_get(member.id)
    active_role_id = condemnation_role_id(existing)
    snapshot = preserve_role_ids
    if snapshot is None and existing is None:
        snapshot = [r.id for r in member.roles]

    _condemn_sync_busy.add(member.id)
    try:
        ok, saved_ids, role_note = await condemnation_sync_roles(
            member, preserve_role_ids=snapshot, save_snapshot=(existing is None),
            reason=f"{reason[:400]} — {condemnation_origin_label(origin)}",
            role_id=active_role_id,
        )
    finally:
        _condemn_sync_busy.discard(member.id)
    if not ok:
        return False, role_note
    removed_role_ids = [
        rid for rid in (snapshot or [])
        if rid != active_role_id
        and (member.guild.get_role(rid) is not None)
        and member.guild.get_role(rid).is_assignable()
        and not member.guild.get_role(rid).managed
    ]

    if existing is None:
        condemnation_save(member.id, member.guild.id, active_role_id, saved_ids, reason[:1000], duration_minutes, origin,
                           applied_by.id if applied_by else None)
    else:
        # Una nueva orden sobre una condena activa actualiza motivo/duración/origen, pero NO pisa la fotografía original de roles.
        condemnation_save(member.id, member.guild.id, active_role_id, condemnation_parse_role_ids(existing["role_ids"]),
                           reason[:1000], duration_minutes, origin, applied_by.id if applied_by else None,
                           condemned_at=datetime.fromisoformat(existing["condemned_at"]))

    db_clear_tentado(member.id)
    db_clear_sin_verificado(member.id)
    db_clear_verify_pending(member.id)
    db_zero_week_messages(member.id)

    if purge_spec and purge_spec[0] != "none":
        kind, value = purge_spec
        after = datetime.now(timezone.utc) - timedelta(minutes=value) if kind == "time" else None
        limit = value if kind == "count" else None
        asyncio.create_task(run_purge_job(
            member.guild, member, scope_text=format_purge_spec(kind, value),
            requested_by=f"☠️ Condena ({condemnation_origin_label(origin)})",
            after=after, limit=limit, title="☠️ Purga de condena completada",
        ))

    # Ambos destinos reciben la misma resolución: mismo expediente, fecha y datos.
    condemnation_when = datetime.now(timezone.utc)
    condemnation_case = condemnation_case_id(member, condemnation_when)
    dm_ok = await condemnation_send_dm(
        member, reason, duration_minutes, origin, applied_by,
        source_message_url=source_message_url, source_channel_id=source_channel_id,
        removed_role_ids=removed_role_ids, when=condemnation_when, case_id=condemnation_case,
    ) if send_dm else None
    if announce:
        announcement_message_id = await condemnation_announce(
            member.guild, member, reason, duration_minutes, origin, applied_by,
            source_message_url=source_message_url, source_channel_id=source_channel_id,
            removed_role_ids=removed_role_ids, when=condemnation_when, case_id=condemnation_case,
        )
        if announcement_message_id:
            conn = sqlite3.connect(DB_PATH)
            conn.execute(
                "UPDATE condemnations SET announcement_message_id = ? WHERE user_id = ?",
                (announcement_message_id, member.id),
            )
            conn.commit()
            conn.close()
    await log_embed(
        member.guild, "☠️ Condena aplicada",
        f"{member.mention} (`{member.id}`)\n"
        f"Motivo: {reason}\n"
        f"Duración: {format_duration(duration_minutes) if duration_minutes else 'Indefinida'}\n"
        f"Origen: {condemnation_origin_label(origin)}\n"
        f"Aplicó: {applied_by.mention if applied_by else 'El Heraldo'}\n"
        f"{role_note}\n"
        f"DM: {'✅ enviado' if dm_ok else '⚠️ no enviado' if dm_ok is not None else '—'}",
        discord.Color.dark_red(),
    )
    return True, role_note + ("; DM enviado" if dm_ok else "; DM no disponible" if dm_ok is not None else "")


async def release_condemned_member(
    member: discord.Member, *, released_by: discord.abc.User | None = None,
    automatic: bool = False, pardon: bool = False,
    announcement_message: discord.Message | None = None,
) -> tuple[bool, str]:
    row = condemnation_get(member.id)
    punish_role = member.guild.get_role(condemnation_role_id(row))
    if row is None and not (punish_role and punish_role in member.roles):
        return False, "Ese miembro no tiene una condena activa."

    saved = condemnation_parse_role_ids(row["role_ids"]) if row else (hp_get_punished(member.id) or [])
    restore: list[discord.Role] = []
    lost = 0
    for rid in saved:
        role = member.guild.get_role(rid)
        if role is not None and role.is_assignable() and not role.managed:
            restore.append(role)
        else:
            lost += 1

    current = [
        r for r in member.roles
        if not r.is_default() and (punish_role is None or r.id != punish_role.id)
    ]
    new_roles = list({r.id: r for r in current + restore}.values())
    _condemn_sync_busy.add(member.id)
    try:
        await member.edit(roles=new_roles, reason=("Condena expirada" if automatic else f"Liberado por {released_by}"))
    except discord.HTTPException as e:
        return False, f"No pude cambiar sus roles: `{e}`"
    finally:
        _condemn_sync_busy.discard(member.id)

    if pardon and row is not None and released_by is not None:
        condemnation_deactivate(member.id, resolution="pardoned", resolved_by=released_by.id)
    else:
        condemnation_deactivate(member.id, resolution="expired" if automatic else None)
    db_clear_tentado(member.id)
    db_clear_sin_verificado(member.id)
    db_clear_verify_pending(member.id)

    # Si entre los roles originales estaban los de verificación, vuelven a su flujo normal
    # desde cero; mientras la condena estuvo activa nunca corrió ninguna evaluación.
    restored_ids = {r.id for r in restore}
    if TENTADO_ROLE_ID in restored_ids:
        now = datetime.now(timezone.utc)
        db_set_tentado(member.id, now)
        asyncio.create_task(schedule_check(member.guild.id, member.id, now))
    if SIN_VERIFICAR_ROLE_ID in restored_ids:
        now = datetime.now(timezone.utc)
        db_set_sin_verificado(member.id, now)
        asyncio.create_task(schedule_sin_verificado_check(member.guild.id, member.id, now))

    text = f"{len(restore)} rol(es) restaurado(s)" + (f"; {lost} no se pudieron restaurar" if lost else "")
    if pardon and row is not None and released_by is not None:
        condemned_at = datetime.fromisoformat(row["condemned_at"])
        case_id = condemnation_case_id(member, condemned_at)
        card_ok = await condemnation_update_pardoned_card(
            member, row, released_by, len(restore), lost, message=announcement_message
        )
        dm_ok = await condemnation_send_pardon_dm(member, row, released_by, len(restore), lost)
        await log_embed(
            member.guild, "🕊️ Condena perdonada",
            f"Expediente: {case_id}\nUsuario: {member.mention} ({member.id})\n"
            f"Motivo original: {row['reason']}\nOrigen: {condemnation_origin_label(row['origin'])}\n"
            f"Perdonó: {released_by.mention}\nRoles: {text}\n"
            f"Tarjeta original: {'✅ cerrada' if card_ok else '⚠️ no cerrada'}\n"
            f"Tarjeta de resolución: {'✅ creada' if card_ok else '⚠️ no creada'}\n"
            f"DM: {'✅ enviado' if dm_ok else '⚠️ no enviado'}",
            discord.Color.green(),
        )
        return True, text + (
            "; tarjeta de resolución creada" if card_ok else "; no pude publicar la tarjeta de resolución"
        ) + ("; DM de perdón enviado" if dm_ok else "; DM de perdón no disponible")
    await log_embed(member.guild, "🕊️ Condena levantada", f"{member.mention} — {text}. Por: {released_by.mention if released_by else 'El Heraldo'}.", discord.Color.green())
    return True, text


async def check_expired_condemnations() -> None:
    now = datetime.now(timezone.utc)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT * FROM condemnations WHERE active = 1 AND expires_at IS NOT NULL AND expires_at <= ?",
        (now.isoformat(),),
    ).fetchall()
    conn.close()
    for row in rows:
        guild = bot.get_guild(row["guild_id"]) if row["guild_id"] else None
        if guild is None:
            condemnation_deactivate(row["user_id"])
            continue
        member = guild.get_member(row["user_id"])
        if member is not None:
            await release_condemned_member(member, automatic=True)
        else:
            condemnation_deactivate(row["user_id"])


async def condemnation_reconcile(guild: discord.Guild) -> None:
    """Al arrancar, el rol Condenado vuelve a ser la fuente de verdad por si cambió con el bot apagado:
    - condena activa pero sin el rol: si el miembro reingresó después, se le reaplica; si no, se le libera.
    - rol Condenado sin condena registrada: se condena como si lo hubieran puesto a mano."""
    for row in condemnation_list(guild.id):
        role = guild.get_role(condemnation_role_id(row))
        member = guild.get_member(row["user_id"])
        if role is None or member is None or role in member.roles:
            continue
        condemned_at = datetime.fromisoformat(row["condemned_at"])
        if member.joined_at and member.joined_at > condemned_at:
            _condemn_sync_busy.add(member.id)
            try:
                await condemnation_sync_roles(member, save_snapshot=False, reason="Condena activa reaplicada al arrancar", role_id=role.id)
            finally:
                _condemn_sync_busy.discard(member.id)
        else:
            await release_condemned_member(member, automatic=False)
        await asyncio.sleep(1)

    punish_role = guild.get_role(hp_punish_role_id())
    if punish_role is None:
        return
    for member in list(punish_role.members):
        if member.bot or condemnation_get(member.id) is not None:
            continue
        await condemn_member(
            member, reason="El rol Condenado fue otorgado manualmente (detectado al arrancar).",
            duration_minutes=condemnation_default_duration_minutes(), purge_spec=None, origin="role", applied_by=None,
            send_dm=False, announce=False,
        )
        await asyncio.sleep(1)


@tasks.loop(minutes=1)
async def condemnation_expiry_loop() -> None:
    try:
        await check_expired_condemnations()
    except Exception:
        traceback.print_exc()


async def hp_punish(member: discord.Member, action: str, source_channel_id: int | None = None) -> tuple[bool, str]:
    guild = member.guild
    reason = "Honeypot: escribió en un canal trampa"
    if action == "log":
        return True, "Solo registrado (sin castigo)"
    if member.top_role >= guild.me.top_role:
        return False, "Su rol es igual o superior al del bot (jerarquía de roles)"
    try:
        if action == "timeout":
            minutes = hp_timeout_minutes()
            await member.timeout(timedelta(minutes=minutes), reason=reason)
            purge_note = hp_start_purge(member)
            return True, f"Aislado {format_duration(minutes)}" + (f"; {purge_note}" if purge_note else "")
        if action == "role":
            purge_spec = hp_purge_spec()
            return await condemn_member(
                member,
                reason="Honeypot: escribió en un canal trampa",
                duration_minutes=condemnation_default_duration_minutes(),
                purge_spec=purge_spec,
                origin="honeypot",
                applied_by=None,
                source_channel_id=source_channel_id,
                send_dm=True,
                announce=True,
            )
    except discord.Forbidden:
        return False, "Faltan permisos (Moderar miembros / Gestionar roles)"
    except discord.HTTPException as e:
        return False, f"Error de Discord: `{e}`"
    return False, f"Acción desconocida: {action}"


async def hp_report(guild: discord.Guild, member: discord.Member, channel: discord.abc.GuildChannel,
                    content: str, attachments: int, action: str, success: bool, note: str) -> None:
    log_channel = guild.get_channel(get_log_channel_id())
    if log_channel is None:
        return
    evidence = content.replace("`", "'")[:900] if content else ""
    if not evidence:
        evidence = ("(sin texto)" if attachments or os.environ.get("MESSAGE_CONTENT_INTENT") == "1"
                    else "(no disponible: activa MESSAGE_CONTENT_INTENT=1 y el intent en el portal)")
    if attachments:
        evidence += f"\n📎 {attachments} adjunto(s)"
    embed = discord.Embed(
        title="🍯 Honeypot: miembro atrapado" if success else "🍯 Honeypot: castigo FALLIDO",
        color=discord.Color.orange() if success else discord.Color.red(),
        timestamp=datetime.now(timezone.utc),
    )
    embed.add_field(name="Usuario", value=f"{member.mention} (`{member}` · {member.id})", inline=False)
    embed.add_field(name="Cuenta creada", value=discord.utils.format_dt(member.created_at, "R"), inline=True)
    embed.add_field(
        name="Se unió",
        value=discord.utils.format_dt(member.joined_at, "R") if member.joined_at else "—",
        inline=True,
    )
    embed.add_field(name="Canal", value=channel.mention, inline=True)
    embed.add_field(name="Acción", value=f"{HONEYPOT_ACTION_LABELS.get(action, action)} — {note}", inline=False)
    embed.add_field(name="Mensaje", value=f"```{evidence}```", inline=False)
    embed.set_thumbnail(url=member.display_avatar.url)
    role_id = hp_ping_role_id()
    try:
        await log_channel.send(
            content=f"<@&{role_id}>" if role_id else None,
            embed=embed,
            allowed_mentions=discord.AllowedMentions(roles=True, users=False, everyone=False),
        )
    except discord.HTTPException as e:
        print(f"Honeypot: no pude reportar en el canal de logs: {e}")


async def hp_handle_trigger(message: discord.Message, member: discord.Member) -> None:
    guild = member.guild
    content = message.content or ""
    attachments = len(message.attachments)
    action = hp_action()

    # Borra el mensaje trampa (si el castigo no lo purga ya).
    try:
        await message.delete()
    except discord.HTTPException:
        pass

    # Protección contra fallos: varios miembros veteranos atrapados en pocos minutos.
    now = datetime.now(timezone.utc)
    if member.joined_at and now - member.joined_at > HONEYPOT_MISFIRE_MEMBER_AGE:
        _hp_veteran_hits.append((now, member.id))
    _hp_veteran_hits[:] = [(t, u) for t, u in _hp_veteran_hits if now - t <= HONEYPOT_MISFIRE_WINDOW]
    if len({u for _, u in _hp_veteran_hits}) >= HONEYPOT_MISFIRE_THRESHOLD:
        hp_meta_set("honeypot_paused", "1")
        _hp_veteran_hits.clear()
        await log_embed(
            guild, "⏸️ Honeypot pausado (protección contra fallos)",
            f"{HONEYPOT_MISFIRE_THRESHOLD}+ miembros con más de 30 días en el servidor escribieron en la trampa en "
            f"pocos minutos: probablemente apunta a un canal que tu comunidad usa de verdad.\n"
            f"Revisa los canales trampa con `/honeypot config` y reactiva con `/honeypot resume`. "
            f"Este último mensaje ({member.mention}) **no** fue castigado.",
            discord.Color.red(),
        )
        return

    success, note = await hp_punish(member, action, message.channel.id)
    hp_log_trigger(member, message.channel.id, content, action, success, note)
    await hp_report(guild, member, message.channel, content, attachments, action, success, note)


@bot.listen("on_message")
async def honeypot_listener(message: discord.Message) -> None:
    if message.guild is None or message.webhook_id is not None or message.author.bot:
        return  # DMs, webhooks y otros bots se ignoran (tus integraciones están a salvo)
    if not honeypot_enabled() or honeypot_paused():
        return
    if message.channel.id not in hp_trap_ids():
        return
    member = message.author
    if not isinstance(member, discord.Member) or hp_is_exempt(member):
        return
    punish_id = hp_punish_role_id()
    if punish_id and any(r.id == punish_id for r in member.roles):
        try:
            await message.delete()  # ya está castigado: solo se borra lo que siga escribiendo
        except discord.HTTPException:
            pass
        return
    if member.id in _hp_busy:
        try:
            await message.delete()
        except discord.HTTPException:
            pass
        return
    _hp_busy.add(member.id)
    try:
        await hp_handle_trigger(message, member)
    except Exception:
        traceback.print_exc()
    finally:
        _hp_busy.discard(member.id)


@bot.listen("on_guild_channel_delete")
async def honeypot_channel_deleted(channel: discord.abc.GuildChannel) -> None:
    if channel.id not in hp_traps():
        return
    hp_remove_trap(channel.id)
    await log_embed(
        channel.guild, "🍯 Canal trampa eliminado",
        f"Se borró `#{channel.name}` en Discord y se quitó del honeypot automáticamente. "
        f"Quedan {len(hp_traps())} canal(es) trampa.",
        discord.Color.orange(),
    )



# ---------------------------------------------------------------------------
# CONDENAS — fuente de verdad compartida por comando, rol, reacción y honeypot
# ---------------------------------------------------------------------------

@bot.tree.command(name="condenar", description="Condenar a un miembro: guarda sus roles, los retira y aplica Condenado.")
@discord.app_commands.describe(
    miembro="Miembro que será condenado",
    motivo="Motivo de la condena",
    duracion="Duración: 30m, 12h, 2d…; vacío = usa la configurada; «indefinida» = hasta retirar",
    purga="Qué borrar del condenado; vacío = últimas 24h, 0 = no borrar",
)
@discord.app_commands.checks.has_permissions(kick_members=True)
@discord.app_commands.guild_only()
async def condenar(
    interaction: discord.Interaction,
    miembro: discord.Member,
    motivo: str,
    duracion: Optional[str] = None,
    purga: Optional[str] = None,
) -> None:
    guild = interaction.guild
    reason = (motivo or "").strip()[:1000]
    if not reason:
        await interaction.response.send_message("❌ El motivo de la condena es obligatorio.", ephemeral=True)
        return
    duration_minutes: int | None = condemnation_default_duration_minutes()
    try:
        if duracion is not None:
            raw_duration = duracion.strip()
            if raw_duration.lower() in {"0", "indefinida", "indefinido", "permanente", "hasta retirar"}:
                duration_minutes = None
            else:
                duration_minutes = parse_duration(raw_duration, 1, CONDEMNATION_MAX_MINUTES)
        purge_spec = parse_purge_spec(purga) if purga else HONEYPOT_PURGE_DEFAULT
    except ValueError as e:
        await interaction.response.send_message(f"❌ No se pudo condenar: {e}", ephemeral=True)
        return

    if miembro.id == interaction.user.id:
        # No es una protección de seguridad; evita una equivocación especialmente fácil con el comando.
        await interaction.response.send_message("❌ No puedes condenarte a ti mismo con este comando.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)
    ok, note = await condemn_member(
        miembro,
        reason=reason,
        duration_minutes=duration_minutes,
        purge_spec=purge_spec,
        origin="command",
        applied_by=interaction.user,
    )
    if not ok:
        await interaction.followup.send(f"❌ No se aplicó la condena: {note}", ephemeral=True)
        return
    await interaction.followup.send(
        f"☠️ {miembro.mention} condenado. **Duración:** {format_duration(duration_minutes) if duration_minutes else 'indefinida'} · "
        f"**Purga:** {format_purge_spec(*purge_spec)}.", ephemeral=True,
    )


@condenar.error
async def condenar_error(interaction: discord.Interaction, error: discord.app_commands.AppCommandError) -> None:
    if isinstance(error, discord.app_commands.MissingPermissions):
        await interaction.response.send_message("No tienes permiso para usar este comando.", ephemeral=True)
    else:
        await interaction.response.send_message(f"Error: {error}", ephemeral=True)


@bot.tree.command(name="liberar", description="Levantar una condena y devolver los roles guardados.")
@discord.app_commands.describe(miembro="Miembro condenado que será liberado")
@discord.app_commands.checks.has_permissions(kick_members=True)
@discord.app_commands.guild_only()
async def liberar(interaction: discord.Interaction, miembro: discord.Member) -> None:
    await interaction.response.defer(ephemeral=True)
    ok, text = await release_condemned_member(miembro, released_by=interaction.user)
    await interaction.followup.send(("✅ " if ok else "❌ ") + text, ephemeral=True)


@liberar.error
async def liberar_error(interaction: discord.Interaction, error: discord.app_commands.AppCommandError) -> None:
    if isinstance(error, discord.app_commands.MissingPermissions):
        await interaction.response.send_message("No tienes permiso para usar este comando.", ephemeral=True)
    else:
        await interaction.response.send_message(f"Error: {error}", ephemeral=True)


@bot.tree.command(name="condenados", description="Listar las condenas activas con motivo, origen y caducidad.")
@discord.app_commands.checks.has_permissions(kick_members=True)
@discord.app_commands.guild_only()
async def condenados(interaction: discord.Interaction) -> None:
    rows = condemnation_list(interaction.guild.id)
    if not rows:
        await interaction.response.send_message("No hay condenas activas.", ephemeral=True)
        return
    embed = discord.Embed(
        title="☠️ Condenados activos",
        description=f"**{len(rows)}** condena(s) activa(s).",
        color=discord.Color.dark_red(),
    )
    for row in rows[:25]:
        member = interaction.guild.get_member(row["user_id"])
        mention = member.mention if member else f"`{row['user_id']}`"
        when = discord.utils.format_dt(datetime.fromisoformat(row["condemned_at"]), "R")
        value = (
            f"**Motivo:** {row['reason'][:500]}\n"
            f"**Desde:** {when}\n"
            f"**Caduca:** {condemnation_duration_text(row)}\n"
            f"**Origen:** {condemnation_origin_label(row['origin'])}"
        )
        embed.add_field(name=mention, value=value, inline=False)
    if len(rows) > 25:
        embed.set_footer(text=f"Mostrando 25 de {len(rows)} condenas activas.")
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="condenar_config", description="Configurar el canal donde se anuncian las nuevas condenas.")
@discord.app_commands.describe(canal="Canal de texto para los avisos de condena; vacío = ver configuración")
@discord.app_commands.checks.has_permissions(manage_guild=True)
@discord.app_commands.guild_only()
async def condenar_config(interaction: discord.Interaction, canal: Optional[discord.TextChannel] = None) -> None:
    if canal is None:
        current = interaction.guild.get_channel(condemnation_channel_id())
        await interaction.response.send_message(
            f"**Canal de condenas:** {current.mention if current else 'no configurado'}",
            ephemeral=True,
        )
        return
    perms = canal.permissions_for(interaction.guild.me)
    missing = [name for name, ok in (("Ver canal", perms.view_channel), ("Enviar mensajes", perms.send_messages), ("Insertar enlaces", perms.embed_links)) if not ok]
    if missing:
        await interaction.response.send_message(
            f"❌ No guardé el cambio: faltan **{', '.join(missing)}** en {canal.mention}.", ephemeral=True
        )
        return
    set_condemnation_channel_id(canal.id)
    await interaction.response.send_message(f"✅ Los avisos de condena se publicarán en {canal.mention}.", ephemeral=True)
    await log_embed(interaction.guild, "⚙️ Canal de condenas actualizado", f"{interaction.user.mention} lo cambió a {canal.mention}.")


class CondemnationCoreModal(discord.ui.Modal, title="Condenados · Diseño"):
    title_input = discord.ui.TextInput(label="Título", required=False, max_length=256)
    description_input = discord.ui.TextInput(
        label="Descripción",
        style=discord.TextStyle.paragraph,
        required=False,
        max_length=4000,
        placeholder="Admite variables: {usuario}, {servidor}, {motivo}…",
    )
    color_input = discord.ui.TextInput(label="Color HEX", required=False, max_length=7, placeholder="#8B0000")
    footer_input = discord.ui.TextInput(
        label="Pie del embed",
        required=False,
        max_length=2048,
        placeholder="Admite variables: {servidor}, {servericon}…",
    )
    button_label_input = discord.ui.TextInput(label="Texto del botón", required=False, max_length=80)

    def __init__(self) -> None:
        super().__init__()
        self.title_input.default = condemnation_template_get("title")
        self.description_input.default = condemnation_template_get("description")
        self.color_input.default = condemnation_template_get("color")
        self.footer_input.default = condemnation_template_get("footer")
        self.button_label_input.default = condemnation_template_get("button_label")

    async def on_submit(self, interaction: discord.Interaction) -> None:
        color = str(self.color_input).strip().lstrip("#")
        if color:
            try:
                if len(color) != 6:
                    raise ValueError
                int(color, 16)
            except ValueError:
                await interaction.response.send_message(
                    "❌ El color debe ser HEX de 6 dígitos, por ejemplo 8B0000.",
                    ephemeral=True,
                )
                return
        condemnation_template_set("title", str(self.title_input).strip())
        condemnation_template_set("description", str(self.description_input).strip())
        condemnation_template_set("color", color or CONDEMNATION_TEMPLATE_DEFAULTS["color"])
        condemnation_template_set("footer", str(self.footer_input).strip())
        condemnation_template_set(
            "button_label",
            str(self.button_label_input).strip() or CONDEMNATION_TEMPLATE_DEFAULTS["button_label"],
        )
        await condemnation_template_editor_update(interaction, "Diseño actualizado.")


class CondemnationDetailsModal(discord.ui.Modal, title="Condenados · Etiquetas"):
    case_input = discord.ui.TextInput(label="Expediente", required=True, max_length=256)
    user_input = discord.ui.TextInput(label="Condenado", required=True, max_length=256)
    by_input = discord.ui.TextInput(label="Quién condenó", required=True, max_length=256)
    reason_input = discord.ui.TextInput(label="Motivo", required=True, max_length=256)
    when_input = discord.ui.TextInput(label="Cuándo", required=True, max_length=256)

    def __init__(self) -> None:
        super().__init__()
        self.case_input.default = condemnation_template_get("label_case")
        self.user_input.default = condemnation_template_get("label_user")
        self.by_input.default = condemnation_template_get("label_by")
        self.reason_input.default = condemnation_template_get("label_reason")
        self.when_input.default = condemnation_template_get("label_when")

    async def on_submit(self, interaction: discord.Interaction) -> None:
        values = (
            ("label_case", self.case_input.value),
            ("label_user", self.user_input.value),
            ("label_by", self.by_input.value),
            ("label_reason", self.reason_input.value),
            ("label_when", self.when_input.value),
        )
        for key, value in values:
            condemnation_template_set(key, value.strip())
        await condemnation_template_editor_update(interaction, "Etiquetas principales actualizadas.")


class CondemnationDurationModal(discord.ui.Modal, title="Condenados · Duración"):
    duration_input = discord.ui.TextInput(
        label="Duración predeterminada",
        required=True,
        max_length=32,
        placeholder="Indefinida, 30m, 12h, 7d…",
    )

    def __init__(self) -> None:
        super().__init__()
        current = condemnation_default_duration_minutes()
        self.duration_input.default = format_duration(current) if current else "Indefinida"

    async def on_submit(self, interaction: discord.Interaction) -> None:
        value = str(self.duration_input).strip()
        if value.lower() in {"indefinida", "indefinido", "permanente", "hasta retirar", "0"}:
            set_condemnation_default_duration(None)
            await condemnation_template_editor_update(interaction, "Duración predeterminada: **Indefinida (hasta retirar)**.")
            return
        try:
            minutes = parse_duration(value, 1, CONDEMNATION_MAX_MINUTES)
        except ValueError as e:
            await interaction.response.send_message(f"❌ {e}", ephemeral=True)
            return
        set_condemnation_default_duration(value)
        await condemnation_template_editor_update(interaction, f"Duración predeterminada: **{format_duration(minutes)}**.")


class CondemnationMoreDetailsModal(discord.ui.Modal, title="Condenados · Más etiquetas"):
    where_input = discord.ui.TextInput(label="Dónde ocurrió", required=True, max_length=256)
    duration_input = discord.ui.TextInput(label="Duración", required=True, max_length=256)
    origin_input = discord.ui.TextInput(label="Origen", required=True, max_length=256)
    roles_input = discord.ui.TextInput(label="Roles retirados", required=True, max_length=256)
    evidence_input = discord.ui.TextInput(label="Evidencia / mensaje", required=True, max_length=256)

    def __init__(self) -> None:
        super().__init__()
        self.where_input.default = condemnation_template_get("label_where")
        self.duration_input.default = condemnation_template_get("label_duration")
        self.origin_input.default = condemnation_template_get("label_origin")
        self.roles_input.default = condemnation_template_get("label_roles")
        self.evidence_input.default = condemnation_template_get("label_message")

    async def on_submit(self, interaction: discord.Interaction) -> None:
        values = (
            ("label_where", self.where_input.value),
            ("label_duration", self.duration_input.value),
            ("label_origin", self.origin_input.value),
            ("label_roles", self.roles_input.value),
            ("label_message", self.evidence_input.value),
        )
        for key, value in values:
            condemnation_template_set(key, value.strip())
        await condemnation_template_editor_update(interaction, "Más etiquetas actualizadas.")


class CondemnationButtonUrlModal(discord.ui.Modal, title="Condenados · Enlace"):
    url_input = discord.ui.TextInput(
        label="URL del botón",
        required=False,
        max_length=2000,
        placeholder="https://…",
    )

    def __init__(self) -> None:
        super().__init__()
        self.url_input.default = condemnation_template_get("button_url")

    async def on_submit(self, interaction: discord.Interaction) -> None:
        url = str(self.url_input).strip()
        if url and not re.match(r"^https?://", url, re.IGNORECASE):
            await interaction.response.send_message(
                "❌ La URL debe comenzar por https:// o http://.",
                ephemeral=True,
            )
            return
        condemnation_template_set("button_url", url)
        await condemnation_template_editor_update(interaction, "Enlace del botón actualizado.")


def condemnation_template_preview(guild: discord.Guild, member: discord.Member) -> discord.Embed:
    embed, _ = _build_condemnation_embed(
        guild,
        member,
        "Ejemplo de vista previa — motivo de la condena.",
        60,
        "role",
        member,
        removed_role_ids=[r.id for r in member.roles if r.is_assignable() and not r.managed],
        when=datetime.now(timezone.utc),
    )
    return embed


async def condemnation_template_editor_update(
    interaction: discord.Interaction,
    notice: str | None = None,
) -> None:
    guild = interaction.guild
    if guild is None:
        await interaction.response.send_message(
            "❌ Este editor solo funciona dentro de un servidor.",
            ephemeral=True,
        )
        return

    embed = condemnation_template_preview(guild, interaction.user)
    view = CondemnationTemplateEditorView(interaction.user.id)
    content = (
        "☠️ **Editor de la tarjeta de condenados**\n"
        "Cada sección se modifica mediante un formulario. Los cambios se guardan "
        "automáticamente y la vista previa refleja la configuración actual."
    )
    if notice:
        content = "✅ " + notice + "\n\n" + content

    try:
        await interaction.response.edit_message(
            content=content,
            embed=embed,
            view=view,
        )
    except discord.HTTPException:
        if not interaction.response.is_done():
            await interaction.response.send_message(
                content=content,
                embed=embed,
                view=view,
                ephemeral=True,
            )
        else:
            await interaction.followup.send(
                content=content,
                embed=embed,
                view=view,
                ephemeral=True,
            )


class CondemnationTemplateEditorView(discord.ui.View):
    def __init__(self, owner_id: int) -> None:
        super().__init__(timeout=900)
        self.owner_id = owner_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message(
                "Este editor no es tuyo. Usa /condenar template para abrir el tuyo.",
                ephemeral=True,
            )
            return False
        return True

    @discord.ui.button(label="✏️ Diseño", style=discord.ButtonStyle.primary, row=0)
    async def edit_core(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await interaction.response.send_modal(CondemnationCoreModal())

    @discord.ui.button(label="🏷️ Etiquetas", style=discord.ButtonStyle.primary, row=0)
    async def edit_details(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await interaction.response.send_modal(CondemnationDetailsModal())

    @discord.ui.button(label="🏷️ Más etiquetas", style=discord.ButtonStyle.primary, row=0)
    async def edit_more_details(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await interaction.response.send_modal(CondemnationMoreDetailsModal())

    @discord.ui.button(label="🔗 Enlace del botón", style=discord.ButtonStyle.secondary, row=1)
    async def edit_button_url(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await interaction.response.send_modal(CondemnationButtonUrlModal())

    @discord.ui.button(label="⏳ Duración", style=discord.ButtonStyle.secondary, row=1)
    async def edit_duration(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await interaction.response.send_modal(CondemnationDurationModal())

    @discord.ui.button(label="👁️ Vista previa", style=discord.ButtonStyle.secondary, row=1)
    async def preview(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if interaction.guild is None:
            await interaction.response.send_message("❌ Solo disponible en un servidor.", ephemeral=True)
            return
        await interaction.response.send_message(
            "👁️ **Vista previa actual de la tarjeta de condenados:**",
            embed=condemnation_template_preview(interaction.guild, interaction.user),
            ephemeral=True,
        )

    @discord.ui.button(label="↩️ Restaurar valores", style=discord.ButtonStyle.danger, row=1)
    async def reset(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        condemnation_template_reset()
        await condemnation_template_editor_update(
            interaction,
            "La plantilla de condenados volvió a sus valores predeterminados.",
        )


@bot.tree.command(
    name="condenar_template",
    description="Abrir el formulario profesional de la tarjeta de condenados.",
)
@discord.app_commands.checks.has_permissions(manage_guild=True)
@discord.app_commands.guild_only()
async def condenar_template(interaction: discord.Interaction) -> None:
    if interaction.guild is None:
        await interaction.response.send_message(
            "❌ Este comando solo funciona dentro de un servidor.",
            ephemeral=True,
        )
        return

    await interaction.response.send_message(
        content=(
            "☠️ **Editor de la tarjeta de condenados**\n"
            "Selecciona una sección para abrir su formulario. Los cambios se guardan "
            "automáticamente y la vista previa se actualiza al terminar cada formulario."
        ),
        embed=condemnation_template_preview(interaction.guild, interaction.user),
        view=CondemnationTemplateEditorView(interaction.user.id),
        ephemeral=True,
    )


@bot.listen("on_raw_reaction_add")
async def condemnation_reaction(payload: discord.RawReactionActionEvent) -> None:
    # Con o sin selector de variación (U+FE0F) el cráneo es el mismo emoji.
    if payload.guild_id is None or str(payload.emoji).replace("\ufe0f", "") != CONDEMNED_EMOJI.replace("\ufe0f", ""):
        return
    guild = bot.get_guild(payload.guild_id)
    if guild is None or payload.user_id == bot.user.id:
        return
    actor = payload.member or guild.get_member(payload.user_id)
    if actor is None:
        try:
            actor = await guild.fetch_member(payload.user_id)
        except discord.HTTPException:
            return
    if not actor.guild_permissions.administrator:
        return  # solo los administradores pueden condenar con la reacción
    channel = guild.get_channel_or_thread(payload.channel_id)
    if channel is None or not hasattr(channel, "fetch_message"):
        return
    try:
        message = await channel.fetch_message(payload.message_id)
    except (discord.NotFound, discord.Forbidden, discord.HTTPException):
        return
    target = message.author
    if not isinstance(target, discord.Member) or target.bot:
        return
    if target.id == actor.id:
        return
    if condemnation_get(target.id) is not None:
        return
    ok, note = await condemn_member(
        target,
        reason=f"Condena por reacción ☠️ al mensaje {message.jump_url}",
        duration_minutes=condemnation_default_duration_minutes(),
        purge_spec=HONEYPOT_PURGE_DEFAULT,
        origin="reaction",
        applied_by=actor,
        source_message_url=message.jump_url,
        source_channel_id=message.channel.id,
    )
    if not ok:
        await log_embed(guild, "⚠️ Condena por reacción rechazada", f"{actor.mention} reaccionó con ☠️ a {message.jump_url}: {note}", discord.Color.orange())


# --- Comandos /honeypot -----------------------------------------------------

class HoneypotGroup(discord.app_commands.Group):
    """Además de default_permissions (que un admin puede ampliar en Integraciones), el código
    exige Gestionar servidor en cada subcomando."""

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        perms = getattr(interaction.user, "guild_permissions", None)
        if perms is None or not perms.manage_guild:
            raise discord.app_commands.MissingPermissions(["manage_guild"])
        return True


honeypot_group = HoneypotGroup(
    name="honeypot",
    description="Canales trampa que atrapan bots de spam.",
    guild_only=True,
    default_permissions=discord.Permissions(manage_guild=True),
)


class HoneypotWarningModal(discord.ui.Modal, title="Texto del aviso fijado"):
    text = discord.ui.TextInput(
        label="Aviso (vacío = texto por defecto)",
        style=discord.TextStyle.paragraph,
        required=False,
        max_length=1500,
        default="",
    )

    def __init__(self) -> None:
        super().__init__()
        self.text.default = hp_meta_get("honeypot_warning_text") or HONEYPOT_WARNING_TEXT_DEFAULT

    async def on_submit(self, interaction: discord.Interaction) -> None:
        value = str(self.text).strip()
        if value and value != HONEYPOT_WARNING_TEXT_DEFAULT:
            hp_meta_set("honeypot_warning_text", value)
        else:
            hp_meta_set("honeypot_warning_text", "")
        hp_meta_set("honeypot_warning_style", "text")
        await interaction.response.defer(ephemeral=True)
        errors = await hp_sync_all_warnings(interaction.guild)
        await interaction.followup.send(
            "✅ Aviso actualizado en los canales trampa." + ("\n" + "\n".join(errors) if errors else ""),
            ephemeral=True,
        )


@honeypot_group.command(name="config", description="Ver o cambiar la configuración del honeypot.")
@discord.app_commands.describe(
    activado="Activar o desactivar el honeypot",
    accion="Qué hacer con quien caiga en la trampa",
    rol_castigo="Rol Condenado: se le quitan todos los demás roles asignables (incluidos Tentad@ y Sin Verificar)",
    purga="Qué borrar: todo, una cantidad (200 mensajes) o un rango (30m, 2d…); 0 = nada",
    timeout="Duración del timeout si la acción es Aislar: 30m, 12h, 2d… (1m a 28d)",
    aviso="Publicar un aviso fijado en cada canal trampa",
    ping_rol="Rol a mencionar en cada reporte",
    retencion="Cuánto guardar el historial y los textos capturados: 12h, 7d, 30d… (por defecto 30d)",
)
@discord.app_commands.choices(accion=[
    discord.app_commands.Choice(name="Purgar y aplicar rol de castigo", value="role"),
    discord.app_commands.Choice(name="Solo registrar (prueba segura)", value="log"),
    discord.app_commands.Choice(name="Aislar (timeout)", value="timeout"),
])
async def honeypot_config(
    interaction: discord.Interaction,
    activado: Optional[bool] = None,
    accion: Optional[discord.app_commands.Choice[str]] = None,
    rol_castigo: Optional[discord.Role] = None,
    purga: Optional[str] = None,
    timeout: Optional[str] = None,
    aviso: Optional[bool] = None,
    ping_rol: Optional[discord.Role] = None,
    retencion: Optional[str] = None,
) -> None:
    guild = interaction.guild
    if all(v is None for v in (activado, accion, rol_castigo, purga, timeout, aviso, ping_rol, retencion)):
        await interaction.response.send_message(hp_config_summary(guild), ephemeral=True)
        return
    if activado and not hp_traps():
        await interaction.response.send_message(
            "❌ No lo activé: añade al menos un canal trampa con `/honeypot add` o `/honeypot create`.",
            ephemeral=True,
        )
        return

    if rol_castigo is not None:
        problem = hp_role_problem(rol_castigo, guild)
        if problem:
            await interaction.response.send_message(f"❌ No guardé nada: {rol_castigo.mention} {problem}.", ephemeral=True)
            return
    effective_action = accion.value if accion is not None else hp_action()
    effective_role_id = rol_castigo.id if rol_castigo is not None else hp_punish_role_id()
    if effective_action == "role" and guild.get_role(effective_role_id) is None and (activado or accion is not None):
        await interaction.response.send_message(
            "❌ No guardé nada: la acción «rol de castigo» necesita un rol. Elígelo con `rol_castigo`.",
            ephemeral=True,
        )
        return

    # Validar duraciones antes de guardar nada.
    purga_spec = None
    timeout_min = None
    retencion_min = None
    try:
        if purga is not None:
            purga_spec = parse_purge_spec(purga)
        if timeout is not None:
            timeout_min = parse_duration(timeout, HONEYPOT_TIMEOUT_MIN_MINUTES, HONEYPOT_TIMEOUT_MAX_MINUTES)
        if retencion is not None:
            retencion_min = parse_duration(retencion, 1, PURGE_MAX_MINUTES)
    except ValueError as e:
        await interaction.response.send_message(f"❌ No guardé nada: {e}", ephemeral=True)
        return

    changes: list[str] = []
    if activado is not None:
        hp_meta_set("honeypot_enabled", "1" if activado else "0")
        if activado:
            hp_meta_set("honeypot_paused", "0")
        changes.append("activado" if activado else "desactivado")
    if accion is not None:
        hp_meta_set("honeypot_action", accion.value)
        changes.append(f"acción → {accion.name}")
    if rol_castigo is not None:
        hp_meta_set("honeypot_punish_role", str(rol_castigo.id))
        changes.append(f"rol de castigo → {rol_castigo.mention}")
    if purga_spec is not None:
        hp_meta_set("honeypot_purge_spec", f"{purga_spec[0]}:{purga_spec[1]}")
        changes.append(f"purga → {format_purge_spec(*purga_spec)}")
    if timeout_min is not None:
        hp_meta_set("honeypot_timeout_minutes", str(timeout_min))
        changes.append(f"timeout → {format_duration(timeout_min)}")
    if retencion_min is not None:
        hp_meta_set("honeypot_retention_minutes", str(retencion_min))
        hp_prune_history()
        changes.append(f"retención → {format_duration(retencion_min)}")
    if ping_rol is not None:
        hp_meta_set("honeypot_ping_role", str(ping_rol.id))
        changes.append(f"ping → {ping_rol.mention}")
    if aviso is not None:
        hp_meta_set("honeypot_warning_enabled", "1" if aviso else "0")
        changes.append("aviso fijado activado" if aviso else "aviso fijado desactivado")

    await interaction.response.defer(ephemeral=True)
    errors = await hp_sync_all_warnings(guild) if aviso is not None else []
    await interaction.followup.send(
        "✅ Guardado: " + "; ".join(changes) + "\n\n" + hp_config_summary(guild)
        + ("\n\n⚠️ " + "\n".join(errors) if errors else ""),
        ephemeral=True,
    )
    await log_embed(guild, "⚙️ Honeypot actualizado", f"{interaction.user.mention}: " + "; ".join(changes))


@honeypot_group.command(name="add", description="Convertir un canal de texto existente en canal trampa.")
@discord.app_commands.describe(canal="Canal de texto que todos puedan ver y en el que puedan escribir")
async def honeypot_add(interaction: discord.Interaction, canal: discord.TextChannel) -> None:
    guild = interaction.guild
    if canal.id in hp_traps():
        await interaction.response.send_message(f"{canal.mention} ya es un canal trampa.", ephemeral=True)
        return
    reason = hp_protected_channel_reason(canal)
    if reason:
        await interaction.response.send_message(
            f"❌ No puedo usar {canal.mention} como trampa: {reason}. Elige un canal que nadie use de verdad.",
            ephemeral=True,
        )
        return
    perms = canal.permissions_for(guild.me)
    if not (perms.view_channel and perms.send_messages and perms.manage_messages):
        await interaction.response.send_message(
            f"❌ El Heraldo necesita Ver canal, Enviar mensajes y Gestionar mensajes en {canal.mention}.",
            ephemeral=True,
        )
        return
    everyone = canal.permissions_for(guild.default_role)
    hp_add_trap(canal.id)
    await interaction.response.defer(ephemeral=True)
    err = await hp_sync_warning(canal)
    notes: list[str] = []
    if not (everyone.view_channel and everyone.send_messages):
        notes.append("⚠️ @everyone no puede ver o escribir ahí: los bots que entren no lo verán y no atrapará nada.")
    if err:
        notes.append("⚠️ " + err)
    await interaction.followup.send(
        f"✅ {canal.mention} añadido como canal trampa." + ("\n" + "\n".join(notes) if notes else ""),
        ephemeral=True,
    )
    await log_embed(guild, "🍯 Canal trampa añadido", f"{interaction.user.mention} añadió {canal.mention}.")


@honeypot_group.command(name="create", description="Crear #honeypot ya configurado (visible, con aviso fijado).")
async def honeypot_create(interaction: discord.Interaction) -> None:
    guild = interaction.guild
    await interaction.response.defer(ephemeral=True)
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(
            view_channel=True,
            send_messages=True,
            create_public_threads=False,
            create_private_threads=False,
            send_messages_in_threads=False,
        )
    }
    try:
        channel = await guild.create_text_channel(
            "honeypot", overwrites=overwrites, reason=f"Honeypot creado por {interaction.user}"
        )
    except discord.HTTPException as e:
        await interaction.followup.send(f"❌ No pude crear el canal: `{e}`", ephemeral=True)
        return
    hp_add_trap(channel.id)
    err = await hp_sync_warning(channel)
    await interaction.followup.send(
        f"✅ Creé {channel.mention} y lo añadí como trampa." + (f"\n⚠️ {err}" if err else "")
        + "\nActívalo con `/honeypot config activado:True` (empieza con `accion: Solo registrar` si quieres probar).",
        ephemeral=True,
    )
    await log_embed(guild, "🍯 Canal trampa creado", f"{interaction.user.mention} creó {channel.mention}.")


@honeypot_group.command(name="remove", description="Quitar un canal del honeypot (no lo borra).")
async def honeypot_remove(interaction: discord.Interaction, canal: discord.TextChannel) -> None:
    traps = hp_traps()
    if canal.id not in traps:
        await interaction.response.send_message(f"{canal.mention} no es un canal trampa.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True)
    msg_id = traps[canal.id]
    if msg_id:
        try:
            await (await canal.fetch_message(msg_id)).delete()
        except discord.HTTPException:
            pass
    hp_remove_trap(canal.id)
    extra = ""
    if not hp_traps() and honeypot_enabled():
        hp_meta_set("honeypot_enabled", "0")
        extra = "\nℹ️ Era el último canal trampa: desactivé el honeypot."
    await interaction.followup.send(f"✅ {canal.mention} ya no es un canal trampa.{extra}", ephemeral=True)
    await log_embed(interaction.guild, "🍯 Canal trampa quitado", f"{interaction.user.mention} quitó {canal.mention}.")


class HoneypotWarningEmbedModal(discord.ui.Modal, title="Embed personalizado del aviso"):
    title_input = discord.ui.TextInput(
        label="Título",
        required=False,
        max_length=256,
    )
    description_input = discord.ui.TextInput(
        label="Descripción",
        style=discord.TextStyle.paragraph,
        required=True,
        max_length=4000,
    )
    color_input = discord.ui.TextInput(
        label="Color HEX (ej. F1C40F o #F1C40F)",
        required=True,
        max_length=7,
    )
    image_input = discord.ui.TextInput(
        label="Imagen URL (opcional)",
        required=False,
        max_length=2000,
    )
    footer_input = discord.ui.TextInput(
        label="Pie del embed (opcional)",
        required=False,
        max_length=2048,
    )

    def __init__(self) -> None:
        super().__init__()
        cfg = hp_warning_custom()
        self.title_input.default = cfg["title"]
        self.description_input.default = cfg["description"]
        self.color_input.default = cfg["color"]
        self.image_input.default = cfg["image"]
        self.footer_input.default = cfg["footer"]

    async def on_submit(self, interaction: discord.Interaction) -> None:
        title = str(self.title_input).strip()
        description = str(self.description_input).strip()
        color = str(self.color_input).strip().lstrip("#")
        image = str(self.image_input).strip()
        footer = str(self.footer_input).strip()

        if not description:
            await interaction.response.send_message("❌ La descripción no puede quedar vacía.", ephemeral=True)
            return
        if not re.fullmatch(r"[0-9a-fA-F]{6}", color):
            await interaction.response.send_message("❌ El color debe ser HEX de 6 dígitos, por ejemplo `F1C40F`.", ephemeral=True)
            return
        for label, url in (("imagen", image),):
            if url and not re.match(r"^https?://", url, re.IGNORECASE) and not VAR_PATTERN.search(url):
                await interaction.response.send_message(f"❌ La URL de {label} debe empezar por `http://` o `https://` (o ser una variable como `{{servericon}}`).", ephemeral=True)
                return

        hp_meta_set("honeypot_warning_title", title)
        hp_meta_set("honeypot_warning_description", description)
        hp_meta_set("honeypot_warning_color", color.upper())
        hp_meta_set("honeypot_warning_image", image)
        hp_meta_set("honeypot_warning_thumbnail", "")
        hp_meta_set("honeypot_warning_footer", footer)
        hp_meta_set("honeypot_warning_style", "custom")

        await interaction.response.defer(ephemeral=True)
        errors = await hp_sync_all_warnings(interaction.guild)
        await interaction.followup.send(
            "✅ Embed personalizado guardado y aplicado a los avisos fijados."
            + ("\n" + "\n".join(errors) if errors else ""),
            ephemeral=True,
        )
        await log_embed(
            interaction.guild,
            "⚙️ Embed del honeypot actualizado",
            f"{interaction.user.mention} personalizó título, descripción, color, imagen y pie del aviso.",
            discord.Color.blurple(),
        )


@honeypot_group.command(name="warning_embed", description="Personalizar por completo el embed del aviso fijado.")
async def honeypot_warning_embed_cmd(interaction: discord.Interaction) -> None:
    await interaction.response.send_modal(HoneypotWarningEmbedModal())


@honeypot_group.command(name="warning_text", description="Editar el texto del aviso fijado en los canales trampa.")
async def honeypot_warning_text_cmd(interaction: discord.Interaction) -> None:
    await interaction.response.send_modal(HoneypotWarningModal())


@honeypot_group.command(name="exempt_add", description="Eximir a un rol o miembro de la trampa.")
@discord.app_commands.describe(rol="Rol a eximir", miembro="Miembro a eximir")
async def honeypot_exempt_add(
    interaction: discord.Interaction,
    rol: Optional[discord.Role] = None,
    miembro: Optional[discord.Member] = None,
) -> None:
    if (rol is None) == (miembro is None):
        await interaction.response.send_message("Elige **uno**: `rol` o `miembro`.", ephemeral=True)
        return
    if rol is not None:
        hp_exempt_add("role", rol.id)
        text = f"rol {rol.mention}"
    else:
        hp_exempt_add("member", miembro.id)
        text = f"miembro {miembro.mention}"
    await interaction.response.send_message(f"✅ Eximido: {text}.", ephemeral=True)


@honeypot_group.command(name="exempt_remove", description="Quitar la exención de un rol o miembro.")
@discord.app_commands.describe(rol="Rol", miembro="Miembro")
async def honeypot_exempt_remove(
    interaction: discord.Interaction,
    rol: Optional[discord.Role] = None,
    miembro: Optional[discord.Member] = None,
) -> None:
    if (rol is None) == (miembro is None):
        await interaction.response.send_message("Elige **uno**: `rol` o `miembro`.", ephemeral=True)
        return
    if rol is not None:
        hp_exempt_remove("role", rol.id)
        text = f"rol {rol.mention}"
    else:
        hp_exempt_remove("member", miembro.id)
        text = f"miembro {miembro.mention}"
    await interaction.response.send_message(f"✅ Exención quitada: {text}.", ephemeral=True)


@honeypot_group.command(name="history", description="Ver los últimos miembros atrapados.")
@discord.app_commands.describe(cantidad="Cuántos mostrar (1-10)")
async def honeypot_history(
    interaction: discord.Interaction, cantidad: discord.app_commands.Range[int, 1, 10] = 10
) -> None:
    rows = hp_recent_triggers(cantidad)
    if not rows:
        await interaction.response.send_message("Aún no ha caído nadie en la trampa.", ephemeral=True)
        return
    embed = discord.Embed(
        title="🍯 Historial del honeypot",
        description=f"**{hp_total_triggers()}** miembros atrapados en total.",
        color=discord.Color.orange(),
    )
    for r in rows:
        when = discord.utils.format_dt(datetime.fromisoformat(r["triggered_at"]), "R")
        content = (r["content"] or "(sin texto)").replace("`", "'")[:150]
        embed.add_field(
            name=f"{'✅' if r['success'] else '❌'} {r['username']} · {when}",
            value=(
                f"<#{r['channel_id']}> · {HONEYPOT_ACTION_LABELS.get(r['action'], r['action'])}\n"
                f"Cuenta creada: {discord.utils.format_dt(datetime.fromisoformat(r['account_created']), 'R')}\n"
                f"```{content}```"
            ),
            inline=False,
        )
    await interaction.response.send_message(embed=embed, ephemeral=True)


@honeypot_group.command(name="resume", description="Reanudar el honeypot tras una pausa por protección contra fallos.")
async def honeypot_resume(interaction: discord.Interaction) -> None:
    if not honeypot_paused():
        await interaction.response.send_message("El honeypot no está pausado.", ephemeral=True)
        return
    hp_meta_set("honeypot_paused", "0")
    await interaction.response.send_message("✅ Honeypot reanudado.", ephemeral=True)
    await log_embed(interaction.guild, "▶️ Honeypot reanudado", f"{interaction.user.mention} lo reanudó.")


@honeypot_group.error
async def honeypot_group_error(interaction: discord.Interaction, error: discord.app_commands.AppCommandError) -> None:
    await verify_command_error(interaction, error)


bot.tree.add_command(honeypot_group)

# ---------------------------------------------------------------------------
# 8. /fusionar_canales — migración segura de mensajes entre canales
# ---------------------------------------------------------------------------

FUSION_MAX_MESSAGES = 10000


def fusion_channel_label(channel: discord.TextChannel) -> str:
    return f"{channel.mention} (`#{channel.name}`)"


def fusion_final_name(
    origen: discord.TextChannel,
    destino: discord.TextChannel,
    nombre: str,
    personalizado: Optional[str],
) -> str:
    if nombre == "origen":
        return origen.name
    if nombre == "personalizado":
        return (personalizado or destino.name).strip().lower().replace(" ", "-")[:100]
    return destino.name


def fusion_clean_name(name: str) -> str:
    # Discord acepta letras, números, guiones y guiones bajos en nombres de texto.
    name = re.sub(r"[^a-zA-Z0-9áéíóúÁÉÍÓÚñÑ_-]+", "-", name.strip())
    name = re.sub(r"-+", "-", name).strip("-")
    return name[:100] or "canal-fusionado"


class FusionChannelsView(discord.ui.View):
    def __init__(
        self,
        executor_id: int,
        origen: discord.TextChannel,
        destino: discord.TextChannel,
        final_name: str,
        eliminar_origen: bool,
        message_count: int,
    ) -> None:
        super().__init__(timeout=120)
        self.executor_id = executor_id
        self.origen = origen
        self.destino = destino
        self.final_name = final_name
        self.eliminar_origen = eliminar_origen
        self.message_count = message_count

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.executor_id:
            await interaction.response.send_message(
                "❌ Solo quien inició esta fusión puede confirmarla.", ephemeral=True
            )
            return False
        return True

    @discord.ui.button(label="Confirmar fusión", style=discord.ButtonStyle.danger)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        self.stop()
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(
            content="⏳ Fusión confirmada. Estoy migrando los mensajes; el canal origen no se tocará hasta terminar correctamente.",
            view=self,
        )
        asyncio.create_task(
            execute_channel_merge(
                interaction,
                self.origen,
                self.destino,
                self.final_name,
                self.eliminar_origen,
                self.message_count,
            )
        )

    @discord.ui.button(label="Cancelar", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        self.stop()
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(content="Fusión cancelada. No se modificó ningún canal.", view=self)


async def collect_fusion_messages(channel: discord.TextChannel) -> list[discord.Message]:
    messages: list[discord.Message] = []
    async for message in channel.history(limit=FUSION_MAX_MESSAGES, oldest_first=True):
        messages.append(message)
    return messages


async def send_migrated_message(
    destino: discord.TextChannel,
    message: discord.Message,
    index: int,
    total: int,
) -> tuple[int, int]:
    """Migra un mensaje conservando su texto cuando exista y re-subiendo sus adjuntos.

    - Texto sin adjuntos: se mantiene como embed con autor/fecha.
    - Texto + multimedia: el texto va en el embed y los archivos se suben como
      adjuntos reales; no se añade un campo de enlaces de "Adjuntos".
    - Solo multimedia: se envían únicamente los archivos, sin embed debajo.
    - Si un archivo no puede descargarse/subirse o supera el límite de Discord,
      se deja su URL como respaldo y se informa al proceso de fusión.

    Devuelve (adjuntos_migrados, adjuntos_fallidos).
    """
    attachments = list(message.attachments)
    filesize_limit = getattr(destino.guild, "filesize_limit", 10 * 1024 * 1024)
    temp_paths: list[str] = []
    files: list[discord.File] = []
    fallback_urls: list[str] = []

    try:
        for attachment in attachments:
            if attachment.size > filesize_limit:
                fallback_urls.append(attachment.url)
                continue

            suffix = Path(attachment.filename).suffix
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
            temp_path = tmp.name
            tmp.close()
            temp_paths.append(temp_path)

            try:
                await attachment.save(temp_path, use_cached=False)
                actual_size = Path(temp_path).stat().st_size
                if actual_size > filesize_limit:
                    fallback_urls.append(attachment.url)
                    continue

                files.append(
                    discord.File(
                        temp_path,
                        filename=attachment.filename,
                        spoiler=attachment.is_spoiler(),
                    )
                )
            except (OSError, discord.HTTPException):
                fallback_urls.append(attachment.url)

        description = message.content.strip()
        if len(description) > 3900:
            description = description[:3890] + "…"

        # Mensaje únicamente multimedia: no crear el embed de migración.
        if not description and attachments:
            if files:
                try:
                    await destino.send(
                        files=files,
                        allowed_mentions=discord.AllowedMentions.none(),
                    )
                except discord.HTTPException:
                    # No reintentamos con los mismos archivos: el primer request
                    # pudo haber sido aceptado aunque Discord devolviera un error.
                    fallback_urls.extend(
                        a.url for a in attachments if a.url not in fallback_urls
                    )
                    return len(attachments) - len(fallback_urls), len(fallback_urls)

            if fallback_urls:
                # Solo si algún multimedia no pudo migrarse, dejamos sus enlaces
                # como respaldo. No usamos embed para el caso normal.
                await destino.send(
                    content="\n".join(f"📎 {url}" for url in fallback_urls),
                    allowed_mentions=discord.AllowedMentions.none(),
                )
            return len(attachments) - len(fallback_urls), len(fallback_urls)

        # Mensaje con texto (con o sin multimedia).
        embed = discord.Embed(
            description=description or "*(sin texto)*",
            color=discord.Color.blurple(),
            timestamp=message.created_at,
        )
        embed.set_author(
            name=str(message.author),
            icon_url=message.author.display_avatar.url,
        )

        if message.reference and message.reference.message_id:
            embed.add_field(
                name="Respuesta",
                value=f"Mensaje original: `{message.reference.message_id}`",
                inline=False,
            )

        embed.set_footer(text=f"Migrado por El Heraldo 🪽 · {index}/{total} · ID {message.id}")

        if fallback_urls:
            fallback_text = "\n".join(
                f"📎 [{a.filename}]({a.url})"
                for a in attachments
                if a.url in fallback_urls
            )
            if fallback_text:
                embed.add_field(
                    name="Adjuntos no migrados",
                    value=fallback_text[:1000],
                    inline=False,
                )

        if files:
            try:
                await destino.send(
                    embed=embed,
                    files=files,
                    allowed_mentions=discord.AllowedMentions.none(),
                )
            except discord.HTTPException:
                # No repetir el envío con archivos para evitar duplicados si Discord
                # aceptó el request pero devolvió un error posteriormente.
                fallback_urls.extend(
                    a.url for a in attachments if a.url not in fallback_urls
                )
                await destino.send(
                    embed=embed,
                    allowed_mentions=discord.AllowedMentions.none(),
                )
        else:
            await destino.send(embed=embed, allowed_mentions=discord.AllowedMentions.none())

        return len(attachments) - len(fallback_urls), len(fallback_urls)
    finally:
        for path in temp_paths:
            try:
                Path(path).unlink(missing_ok=True)
            except OSError:
                pass


async def execute_channel_merge(
    interaction: discord.Interaction,
    origen: discord.TextChannel,
    destino: discord.TextChannel,
    final_name: str,
    eliminar_origen: bool,
    expected_count: int,
) -> None:
    guild = interaction.guild
    if guild is None:
        return

    # Volver a validar antes de tocar nada: el estado/permisos pueden haber cambiado
    # mientras el administrador tenía abierta la confirmación.
    if origen.id == destino.id:
        await interaction.followup.send("❌ La fusión fue cancelada: origen y destino son el mismo canal.", ephemeral=True)
        return

    me = guild.me
    if me is None:
        await interaction.followup.send("❌ No pude identificar al Heraldo en el servidor.", ephemeral=True)
        return

    dest_perms = destino.permissions_for(me)
    src_perms = origen.permissions_for(me)
    if not (src_perms.view_channel and src_perms.read_message_history):
        await interaction.followup.send("❌ No tengo permisos para leer el canal origen.", ephemeral=True)
        return
    if not (dest_perms.view_channel and dest_perms.send_messages and dest_perms.embed_links):
        await interaction.followup.send("❌ No tengo permisos suficientes para escribir embeds en el canal destino.", ephemeral=True)
        return

    try:
        messages = await collect_fusion_messages(origen)
    except discord.HTTPException as e:
        await interaction.followup.send(f"❌ No pude leer los mensajes del canal origen: `{e}`", ephemeral=True)
        return

    if not messages:
        await interaction.followup.send("⚠️ El canal origen no contiene mensajes migrables. No hice cambios.", ephemeral=True)
        return

    if len(messages) >= FUSION_MAX_MESSAGES:
        await interaction.followup.send(
            f"❌ La fusión fue detenida porque el origen tiene al menos {FUSION_MAX_MESSAGES:,} mensajes. "
            "Para evitar una migración incompleta, primero divide el trabajo en una migración por partes.",
            ephemeral=True,
        )
        return

    final_name = fusion_clean_name(final_name)
    if final_name != destino.name:
        try:
            await destino.edit(name=final_name, reason=f"Fusión de canales solicitada por {interaction.user}")
        except discord.Forbidden:
            await interaction.followup.send(
                "❌ No pude cambiar el nombre del canal destino. Revisa Gestionar canales y la jerarquía del bot.",
                ephemeral=True,
            )
            return
        except discord.HTTPException as e:
            await interaction.followup.send(f"❌ No pude cambiar el nombre del canal destino: `{e}`", ephemeral=True)
            return

    migrated = 0
    failed = 0
    attachment_failures = 0
    progress_message = None
    try:
        progress_message = await interaction.followup.send(
            f"⏳ Migrando **{len(messages):,}** mensajes de {origen.mention} → {destino.mention}…\n"
            "Esto puede tardar si el canal es grande.",
            ephemeral=True,
            wait=True,
        )
    except discord.HTTPException:
        pass

    for message in messages:
        try:
            _, message_attachment_failures = await send_migrated_message(
                destino, message, migrated + failed + 1, len(messages)
            )
            attachment_failures += message_attachment_failures
            migrated += 1
        except discord.HTTPException:
            failed += 1
        # Mantener una cadencia conservadora para no golpear los rate limits.
        await asyncio.sleep(0.35)
        if progress_message is not None and (migrated + failed) % 25 == 0:
            try:
                await progress_message.edit(
                    content=(
                        f"⏳ Migrando canales… **{migrated + failed:,}/{len(messages):,}** procesados. "
                        f"Correctos: {migrated:,} · Fallidos: {failed:,}."
                    )
                )
            except discord.HTTPException:
                pass

    # Nunca borrar el origen si hubo errores de migración.
    deleted_source = False
    if failed == 0 and attachment_failures == 0 and eliminar_origen:
        src_perms = origen.permissions_for(me)
        if not src_perms.manage_channels:
            await interaction.followup.send(
                f"⚠️ Migración completada ({migrated:,}/{len(messages):,}), pero no pude eliminar {origen.mention}: "
                "al Heraldo le falta Gestionar canales.",
                ephemeral=True,
            )
        else:
            try:
                await origen.delete(reason=f"Canal fusionado con #{destino.name} por {interaction.user}")
                deleted_source = True
            except discord.HTTPException:
                await interaction.followup.send(
                    f"⚠️ Migración completada, pero no pude eliminar {origen.mention}.", ephemeral=True
                )

    if failed or attachment_failures:
        details = []
        if failed:
            details.append(f"{failed:,} mensajes fallaron")
        if attachment_failures:
            details.append(f"{attachment_failures:,} adjuntos no pudieron migrarse")
        result = (
            f"⚠️ Fusión parcial: **{migrated:,}/{len(messages):,}** mensajes procesados; "
            + " · ".join(details)
            + ". El canal origen se conservó por seguridad."
        )
        color = discord.Color.orange()
    else:
        result = (
            f"✅ Fusión completada: **{migrated:,}** mensajes migrados a {destino.mention}. "
            + ("El canal origen fue eliminado." if deleted_source else "El canal origen se conservó.")
        )
        color = discord.Color.green()

    if progress_message is not None:
        try:
            await progress_message.edit(content=result)
        except discord.HTTPException:
            pass
    else:
        await interaction.followup.send(result, ephemeral=True)

    await log_embed(
        guild,
        "🔀 Fusión de canales completada" if not (failed or attachment_failures) else "⚠️ Fusión de canales parcial",
        (
            f"{interaction.user.mention} fusionó {origen.mention} → {destino.mention}.\n"
            f"Mensajes: {migrated}/{len(messages)} · Fallidos: {failed} · Adjuntos no migrados: {attachment_failures}.\n"
            f"Nombre final: `#{destino.name}` · Origen eliminado: {'sí' if deleted_source else 'no'}."
        ),
        color,
    )


@bot.tree.command(name="fusionar_canales", description="Fusionar dos canales de texto mediante una migración segura de mensajes.")
@discord.app_commands.describe(
    origen="Canal que contiene los mensajes que quieres migrar",
    destino="Canal que conservará los mensajes migrados",
    nombre="Qué nombre conservará el canal destino",
    nombre_personalizado="Nombre final si elegiste 'Personalizado'",
    eliminar_origen="Eliminar el canal origen solo si TODOS los mensajes se migran correctamente",
)
@discord.app_commands.choices(nombre=[
    discord.app_commands.Choice(name="Conservar nombre del destino", value="destino"),
    discord.app_commands.Choice(name="Conservar nombre del origen", value="origen"),
    discord.app_commands.Choice(name="Usar nombre personalizado", value="personalizado"),
])
@discord.app_commands.checks.has_permissions(manage_channels=True)
@discord.app_commands.guild_only()
async def fusionar_canales(
    interaction: discord.Interaction,
    origen: discord.TextChannel,
    destino: discord.TextChannel,
    nombre: discord.app_commands.Choice[str],
    nombre_personalizado: Optional[str] = None,
    eliminar_origen: bool = False,
) -> None:
    guild = interaction.guild
    if guild is None:
        await interaction.response.send_message("❌ Este comando solo funciona dentro de un servidor.", ephemeral=True)
        return
    if origen.id == destino.id:
        await interaction.response.send_message("❌ El canal origen y el destino deben ser diferentes.", ephemeral=True)
        return
    if origen.guild.id != guild.id or destino.guild.id != guild.id:
        await interaction.response.send_message("❌ Ambos canales deben pertenecer a este servidor.", ephemeral=True)
        return
    if nombre.value == "personalizado" and not (nombre_personalizado or "").strip():
        await interaction.response.send_message(
            "❌ Si eliges `Usar nombre personalizado`, debes indicar `nombre_personalizado`.",
            ephemeral=True,
        )
        return
    if nombre.value != "personalizado" and nombre_personalizado:
        await interaction.response.send_message(
            "❌ `nombre_personalizado` solo se usa cuando `nombre` es `Usar nombre personalizado`.",
            ephemeral=True,
        )
        return

    me = guild.me
    if me is None:
        await interaction.response.send_message("❌ No pude identificar al Heraldo en el servidor.", ephemeral=True)
        return
    src_perms = origen.permissions_for(me)
    dst_perms = destino.permissions_for(me)
    missing = []
    if not src_perms.view_channel:
        missing.append("Ver canal (origen)")
    if not src_perms.read_message_history:
        missing.append("Leer historial (origen)")
    if not dst_perms.view_channel:
        missing.append("Ver canal (destino)")
    if not dst_perms.send_messages:
        missing.append("Enviar mensajes (destino)")
    if not dst_perms.embed_links:
        missing.append("Insertar enlaces (destino)")
    if missing:
        await interaction.response.send_message(
            "❌ No puedo preparar la fusión porque me faltan: **" + ", ".join(missing) + "**.",
            ephemeral=True,
        )
        return

    await interaction.response.defer(ephemeral=True)
    try:
        messages = await collect_fusion_messages(origen)
    except discord.HTTPException as e:
        await interaction.followup.send(f"❌ No pude leer el canal origen: `{e}`", ephemeral=True)
        return

    if len(messages) >= FUSION_MAX_MESSAGES:
        await interaction.followup.send(
            f"❌ El canal origen tiene al menos {FUSION_MAX_MESSAGES:,} mensajes. "
            "La herramienta se detiene antes de iniciar para evitar una migración incompleta.",
            ephemeral=True,
        )
        return
    if not messages:
        await interaction.followup.send("⚠️ El canal origen está vacío. No hay nada que fusionar.", ephemeral=True)
        return

    final_name = fusion_final_name(origen, destino, nombre.value, nombre_personalizado)
    final_name = fusion_clean_name(final_name)
    embed = discord.Embed(
        title="🔀 Vista previa de fusión de canales",
        description=(
            "Revisa cuidadosamente esta operación. **Los mensajes se recrearán en el destino; Discord no permite moverlos directamente.**\n\n"
            "El canal origen solo se eliminará si activaste esa opción y **todos** los mensajes se migran correctamente."
        ),
        color=discord.Color.orange(),
    )
    embed.add_field(name="Origen", value=fusion_channel_label(origen), inline=True)
    embed.add_field(name="Destino", value=fusion_channel_label(destino), inline=True)
    embed.add_field(name="Mensajes", value=f"**{len(messages):,}**", inline=True)
    embed.add_field(name="Nombre final", value=f"`#{final_name}`", inline=True)
    embed.add_field(name="Canal origen", value="🗑️ Se eliminará si todo sale bien" if eliminar_origen else "📌 Se conservará", inline=True)
    embed.add_field(name="Seguridad", value="No se toca el origen hasta terminar la migración.", inline=True)
    embed.set_footer(text="La confirmación solo puede hacerla quien ejecutó el comando.")

    await interaction.followup.send(
        embed=embed,
        view=FusionChannelsView(
            interaction.user.id,
            origen,
            destino,
            final_name,
            eliminar_origen,
            len(messages),
        ),
        ephemeral=True,
    )


@fusionar_canales.error
async def fusionar_canales_error(interaction: discord.Interaction, error: discord.app_commands.AppCommandError) -> None:
    if isinstance(error, discord.app_commands.MissingPermissions):
        await interaction.response.send_message("❌ Necesitas el permiso **Gestionar canales** para usar este comando.", ephemeral=True)
    else:
        if interaction.response.is_done():
            await interaction.followup.send(f"❌ Error: {error}", ephemeral=True)
        else:
            await interaction.response.send_message(f"❌ Error: {error}", ephemeral=True)


# ---------------------------------------------------------------------------
# 9. /purge — limpieza individual de mensajes de un usuario
# ---------------------------------------------------------------------------

class PurgeConfirmView(discord.ui.View):
    def __init__(self, user_id: int) -> None:
        super().__init__(timeout=60)
        self.user_id = user_id
        self.value: bool | None = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.user_id

    @discord.ui.button(label="Sí, borrar todo", style=discord.ButtonStyle.danger)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        self.value = True
        await interaction.response.edit_message(content="⏳ Iniciando purga…", view=None)
        self.stop()

    @discord.ui.button(label="Cancelar", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        self.value = False
        await interaction.response.edit_message(content="Purga cancelada.", view=None)
        self.stop()


@bot.tree.command(name="purge", description="Borrar mensajes de un usuario: todos, una cantidad o un rango de tiempo.")
@discord.app_commands.describe(
    usuario="Usuario cuyos mensajes borrar (puede haber salido del servidor)",
    tipo="Qué tipo de contenido borrar: todo, links o solo texto",
    todos="Borrar TODOS sus mensajes (no se combina con cantidad ni rango)",
    cantidad="Borrar solo sus N mensajes más recientes",
    desde="Inicio del rango: hace cuánto (30m, 12h, 2d, 1d 12h…)",
    hasta="Fin del rango: hace cuánto (por defecto, ahora)",
    canal="Limitar a un canal o hilo (por defecto, todo el servidor)",
)
@discord.app_commands.choices(tipo=[
    discord.app_commands.Choice(name="Todo — cualquier mensaje", value="all"),
    discord.app_commands.Choice(name="Links — mensajes con enlaces", value="links"),
    discord.app_commands.Choice(name="Texto — sin imagen ni vídeo", value="text"),
])
@discord.app_commands.checks.has_permissions(manage_messages=True)
@discord.app_commands.guild_only()
async def purge_command(
    interaction: discord.Interaction,
    usuario: discord.User,
    tipo: discord.app_commands.Choice[str],
    todos: Optional[bool] = None,
    cantidad: Optional[discord.app_commands.Range[int, 1]] = None,
    desde: Optional[str] = None,
    hasta: Optional[str] = None,
    canal: Optional[Union[discord.TextChannel, discord.VoiceChannel, discord.StageChannel,
                          discord.Thread, discord.ForumChannel]] = None,
) -> None:
    guild = interaction.guild
    if todos and not interaction.user.guild_permissions.manage_guild:
        await interaction.response.send_message(
            "❌ Borrar **todos** los mensajes de alguien requiere el permiso Gestionar servidor. "
            "Con Gestionar mensajes puedes usar `cantidad` o un rango.",
            ephemeral=True,
        )
        return
    has_scope = cantidad is not None or desde is not None or hasta is not None
    if todos and has_scope:
        await interaction.response.send_message("❌ Con `todos` no uses `cantidad`, `desde` ni `hasta`.", ephemeral=True)
        return
    if not todos and not has_scope:
        await interaction.response.send_message(
            "❌ Indica qué borrar: `todos:True`, una `cantidad`, o un rango con `desde` / `hasta` "
            "(también puedes combinar cantidad con rango).",
            ephemeral=True,
        )
        return
    if (guild.id, usuario.id) in _purge_running:
        await interaction.response.send_message("⏳ Ya hay una purga en curso para ese usuario.", ephemeral=True)
        return

    now = datetime.now(timezone.utc)
    after = before = None
    try:
        if desde is not None:
            after = now - timedelta(minutes=parse_duration(desde, 1, PURGE_MAX_MINUTES))
        if hasta is not None:
            before = now - timedelta(minutes=parse_duration(hasta, 1, PURGE_MAX_MINUTES))
    except ValueError as e:
        await interaction.response.send_message(f"❌ {e}", ephemeral=True)
        return
    if after is not None and before is not None and after >= before:
        await interaction.response.send_message(
            "❌ `desde` debe ser más antiguo que `hasta` (por ejemplo desde `3d` hasta `1d`).", ephemeral=True
        )
        return

    content_type = tipo.value
    content_labels = {
        "all": "todo tipo de contenido",
        "links": "solo mensajes con links",
        "text": "solo mensajes de texto sin imagen ni vídeo",
    }

    parts: list[str] = []
    if todos:
        parts.append("**todos** sus mensajes")
    if cantidad is not None:
        parts.append(f"sus **{cantidad}** mensajes más recientes")
    if desde is not None or hasta is not None:
        parts.append(f"rango: desde hace {desde or '—'} hasta hace {hasta or '0'}")
    where = canal.mention if canal is not None else "todo el servidor"
    parts.append(content_labels[content_type])
    scope_text = " · ".join(parts) + f" · en {where}"

    if todos:
        view = PurgeConfirmView(interaction.user.id)
        await interaction.response.send_message(
            f"⚠️ Vas a borrar **todos** los mensajes de {usuario.mention} que coincidan con **{content_labels[content_type]}** en {where}. No se puede deshacer.",
            view=view,
            ephemeral=True,
        )
        await view.wait()
        if view.value is None:
            await interaction.edit_original_response(content="Tiempo agotado: no se borró nada.", view=None)
            return
        if not view.value:
            return
    else:
        await interaction.response.send_message("⏳ Iniciando purga…", ephemeral=True)

    last_edit = [0.0]

    async def progress(done: int, total: int, deleted: int) -> None:
        if asyncio.get_event_loop().time() - last_edit[0] < 3:
            return
        last_edit[0] = asyncio.get_event_loop().time()
        await interaction.edit_original_response(content=f"⏳ Purgando… {done}/{total} canales revisados, {deleted} borrados.")

    async def job() -> None:
        try:
            result = await run_purge_job(
                guild, usuario, scope_text=scope_text, requested_by=interaction.user.mention,
                channel=canal, after=after, before=before, limit=cantidad, progress=progress,
                content_type=content_type,
            )
        except Exception:
            text = "❌ La purga falló a mitad de camino; revisa el canal de logs."
        else:
            text = "⏳ Ya había una purga en curso para ese usuario." if result is None else f"✅ {purge_result_text(result)}."
        try:
            await interaction.edit_original_response(content=text)
        except discord.HTTPException:
            pass  # el token de la interacción dura 15 min; el resultado ya quedó en el canal de logs

    asyncio.create_task(job())


purge_command.error(verify_command_error)



# ---------------------------------------------------------------------------
# 9. RAID PROTECTION (/raid)
# ---------------------------------------------------------------------------
# Detecta ingresos masivos (X miembros en Y segundos), activa el "modo raid" durante un tiempo
# y aplica una acción a los sospechosos. La condena es la acción por defecto: reversible, usa el
# mismo motor que el honeypot y no expulsa a nadie. Estado por servidor; ajustes en la DB (meta).

RAID_ENABLED_DEFAULT = True
RAID_THRESHOLD_DEFAULT = 5          # ingresos que disparan el raid...
RAID_THRESHOLD_MIN, RAID_THRESHOLD_MAX = 2, 200
RAID_WINDOW_DEFAULT = 10            # ...dentro de esta ventana (segundos)
RAID_WINDOW_MIN, RAID_WINDOW_MAX = 1, 3600
RAID_DURATION_DEFAULT = 10 * 60     # cuánto dura el modo raid (segundos)
RAID_DURATION_MIN, RAID_DURATION_MAX = 10, 365 * 24 * 3600
RAID_AGE_MAX = 365 * 24 * 3600      # edad mínima de cuenta configurable (0 = sin filtro)
RAID_ACTION_DEFAULT = "condemn"
RAID_ACTION_LABELS = {
    "condemn": "Condenar (rol Condenado, reversible)",
    "kick": "Expulsar",
    "ban": "Banear",
    "log": "Solo registrar (prueba segura)",
}
RAID_MONTH_SECONDS = 30 * 24 * 3600

_RAID_UNIT_RE = re.compile(
    r"(\d+)\s*(meses|mes|mo|seg(?:undos?)?|s|min(?:utos?)?|m|h(?:oras?)?|d(?:[ií]as?)?)(?![a-záéíóú])",
    re.IGNORECASE,
)


def parse_flex_duration(text: str, min_seconds: int, max_seconds: int) -> int:
    """'30s', '10m', '12h', '2d', '1 mes' o combinaciones ('1d 12h 30m') -> segundos.
    '0' solo es válido si min_seconds es 0. Lanza ValueError con un mensaje listo para mostrar."""
    raw = text.strip().lower()
    example = "Usa s (segundos), m (minutos), h (horas), d (días) y mes (meses), por ejemplo `30s`, `10m`, `12h`, `2d`, `1 mes` o `1d 12h`."
    if raw == "0":
        if min_seconds > 0:
            raise ValueError(f"El mínimo es {format_flex_duration(min_seconds)}. {example}")
        return 0
    matches = list(_RAID_UNIT_RE.finditer(raw))
    leftover = _RAID_UNIT_RE.sub("", raw).replace(",", "").replace(" y ", "").strip()
    if not matches or leftover:
        raise ValueError(f"No entendí `{text}`. {example}")
    total = 0
    for m in matches:
        unit = m.group(2).lower()
        if unit.startswith("mes") or unit == "mo":
            mult = RAID_MONTH_SECONDS
        elif unit.startswith("s"):
            mult = 1
        elif unit.startswith("m"):
            mult = 60
        elif unit.startswith("h"):
            mult = 3600
        else:
            mult = 86400
        total += int(m.group(1)) * mult
    if total < min_seconds or total > max_seconds:
        raise ValueError(
            f"`{text}` queda fuera del rango permitido "
            f"({format_flex_duration(min_seconds)} – {format_flex_duration(max_seconds)})."
        )
    return total


def format_flex_duration(seconds: int) -> str:
    if seconds <= 0:
        return "0 s"
    mo, rest = divmod(seconds, RAID_MONTH_SECONDS)
    d, rest = divmod(rest, 86400)
    h, rest = divmod(rest, 3600)
    m, s = divmod(rest, 60)
    parts = [
        f"{mo} {'mes' if mo == 1 else 'meses'}" if mo else "",
        f"{d} d" if d else "", f"{h} h" if h else "", f"{m} min" if m else "", f"{s} s" if s else "",
    ]
    return " ".join(p for p in parts if p)


# --- Configuración (DB) ---

def raid_enabled() -> bool:
    v = db_meta_get("raid_enabled")
    return RAID_ENABLED_DEFAULT if v is None else v == "1"


def raid_threshold() -> int:
    return _meta_int("raid_threshold", RAID_THRESHOLD_DEFAULT)


def raid_window_seconds() -> int:
    return _meta_int("raid_window_seconds", RAID_WINDOW_DEFAULT)


def raid_duration_seconds() -> int:
    return _meta_int("raid_duration_seconds", RAID_DURATION_DEFAULT)


def raid_min_age_seconds() -> int:
    return _meta_int("raid_min_age_seconds", 0)


def raid_action() -> str:
    v = db_meta_get("raid_action")
    return v if v in RAID_ACTION_LABELS else RAID_ACTION_DEFAULT


def raid_lock_invites_enabled() -> bool:
    return db_meta_get("raid_lock_invites") != "0"  # por defecto activado


def raid_purge_enabled() -> bool:
    return db_meta_get("raid_purge") != "0"  # por defecto activado


def raid_ping_role_id() -> int:
    return _meta_int("raid_ping_role", 0)


# --- Estado por servidor ---

_raid_joins: dict[int, deque] = {}            # guild_id -> deque[(monotonic, user_id)]
_raid_until_cache: dict[int, datetime | None] = {}
_raid_stats: dict[int, dict] = {}
_raid_purge_lock = asyncio.Lock()             # las purgas de raid van de una en una: cada una recorre todos los canales


def raid_until(guild_id: int) -> datetime | None:
    if guild_id not in _raid_until_cache:
        value = db_meta_get(f"raid_until:{guild_id}")
        try:
            _raid_until_cache[guild_id] = datetime.fromisoformat(value) if value else None
        except ValueError:
            _raid_until_cache[guild_id] = None
    return _raid_until_cache[guild_id]


def _raid_set_until(guild_id: int, until: datetime | None) -> None:
    _raid_until_cache[guild_id] = until
    db_meta_set(f"raid_until:{guild_id}", until.isoformat() if until else "")


def raid_is_active(guild_id: int) -> bool:
    until = raid_until(guild_id)
    return until is not None and datetime.now(timezone.utc) < until


def raid_is_suspicious(member: discord.Member) -> bool:
    """Con edad mínima configurada, solo se actúa sobre cuentas más nuevas que ese tiempo."""
    min_age = raid_min_age_seconds()
    if min_age <= 0:
        return True
    return (datetime.now(timezone.utc) - member.created_at).total_seconds() < min_age


async def raid_alert(guild: discord.Guild, title: str, description: str, color: discord.Color) -> None:
    """Embed en el canal de logs con mención opcional al rol de alerta."""
    print(f"{title} — {description}")
    channel = guild.get_channel(get_log_channel_id())
    if channel is None:
        return
    role = guild.get_role(raid_ping_role_id()) if raid_ping_role_id() else None
    embed = discord.Embed(title=title, description=description, color=color, timestamp=datetime.now(timezone.utc))
    try:
        await channel.send(
            content=role.mention if role else None, embed=embed,
            allowed_mentions=discord.AllowedMentions(roles=[role]) if role else discord.AllowedMentions.none(),
        )
    except discord.HTTPException:
        print("No pude enviar la alerta de raid al canal de logs")


async def raid_lock_invites(guild: discord.Guild) -> str:
    try:
        if guild.invites_paused():
            return "ℹ️ las invitaciones ya estaban pausadas (no las toco)"
        await guild.edit(invites_disabled=True, reason="Raid Protection: modo raid activado")
        db_meta_set(f"raid_invites_locked:{guild.id}", "1")
        return "🔒 invitaciones pausadas"
    except (discord.HTTPException, TypeError) as e:
        return f"⚠️ no pude pausar las invitaciones ({e})"


async def raid_unlock_invites(guild: discord.Guild) -> str:
    """Solo reabre las invitaciones si las pausó el propio Heraldo."""
    if db_meta_get(f"raid_invites_locked:{guild.id}") != "1":
        return "—"
    try:
        await guild.edit(invites_disabled=False, reason="Raid Protection: modo raid terminado")
    except (discord.HTTPException, TypeError) as e:
        return f"⚠️ no pude reabrir las invitaciones ({e}); reábrelas a mano en Ajustes del servidor"
    db_meta_set(f"raid_invites_locked:{guild.id}", "0")
    return "🔓 invitaciones reabiertas"


async def _raid_purge_member(member: discord.Member, stats: dict) -> None:
    """Borra los mensajes que el sospechoso mandó desde que entró (una purga a la vez)."""
    async with _raid_purge_lock:
        after = member.joined_at or (datetime.now(timezone.utc) - timedelta(hours=1))
        try:
            result = await purge_user_messages(member.guild, member.id, after=after)
            stats["purged"] += result.deleted
        except Exception:
            traceback.print_exc()


async def raid_act_on_member(member: discord.Member) -> bool:
    """Aplica la acción configurada. Devuelve True si el miembro salió del flujo normal
    (condenado, expulsado o baneado)."""
    guild = member.guild
    stats = _raid_stats.setdefault(guild.id, {
        "started": datetime.now(timezone.utc), "trigger": "—", "action": raid_action(),
        "acted": 0, "failed": 0, "skipped": 0, "logged": 0, "purged": 0, "ids": [],
    })
    if member.bot or hp_is_exempt(member) or not raid_is_suspicious(member):
        stats["skipped"] += 1
        return False
    action = raid_action()
    reason = "Raid Protection: ingreso masivo de miembros"
    if action == "log":
        stats["logged"] += 1
        stats["ids"].append(member.id)
        return False
    try:
        if action == "condemn":
            ok, note = await condemn_member(
                member, reason=reason, duration_minutes=condemnation_default_duration_minutes(), purge_spec=None, origin="raid",
                applied_by=None, send_dm=False, announce=False,
            )
            if not ok:
                stats["failed"] += 1
                print(f"Raid Protection: no pude condenar a {member.id}: {note}")
                return False
        elif action == "kick":
            await member.kick(reason=reason)
        else:  # ban
            joined = member.joined_at
            secs = int((datetime.now(timezone.utc) - joined).total_seconds()) + 60 if joined else 3600
            await member.ban(reason=reason, delete_message_seconds=min(max(secs, 60), 7 * 24 * 3600))
    except discord.HTTPException as e:
        stats["failed"] += 1
        print(f"Raid Protection: no pude aplicar «{action}» a {member.id}: {e}")
        return False
    stats["acted"] += 1
    stats["ids"].append(member.id)
    if raid_purge_enabled() and action in ("condemn", "kick"):
        asyncio.create_task(_raid_purge_member(member, stats))
    return True


async def raid_start(
    guild: discord.Guild, *, trigger: str, suspects: list[int], started_by: discord.abc.User | None = None,
) -> set[int]:
    """Activa el modo raid y actúa sobre los sospechosos. Devuelve los ids que salieron del flujo normal."""
    duration = raid_duration_seconds()
    now = datetime.now(timezone.utc)
    # Marcar el raid como activo ANTES de cualquier await: los ingresos simultáneos ya lo ven activo.
    _raid_set_until(guild.id, now + timedelta(seconds=duration))
    _raid_stats[guild.id] = {
        "started": now, "trigger": trigger, "action": raid_action(),
        "acted": 0, "failed": 0, "skipped": 0, "logged": 0, "purged": 0, "ids": [],
    }
    lock_note = await raid_lock_invites(guild) if raid_lock_invites_enabled() else "—"
    await raid_alert(
        guild, "🛡️ RAID DETECTADO — modo raid activado",
        f"**Motivo:** {trigger}\n"
        f"**Duración:** {format_flex_duration(duration)} (termina <t:{int((now + timedelta(seconds=duration)).timestamp())}:R>)\n"
        f"**Acción sobre los sospechosos:** {RAID_ACTION_LABELS[raid_action()]}\n"
        f"**Invitaciones:** {lock_note}\n"
        f"**Activó:** {started_by.mention if started_by else 'El Heraldo (automático)'}",
        discord.Color.red(),
    )
    acted: set[int] = set()
    for uid in suspects:
        member = guild.get_member(uid)
        if member is not None and await raid_act_on_member(member):
            acted.add(uid)
    return acted


async def raid_end(
    guild: discord.Guild, *, automatic: bool, ended_by: discord.abc.User | None = None, release: bool = False,
) -> str:
    """Termina el modo raid, reabre invitaciones (si las pausó el Heraldo) y reporta el balance."""
    _raid_set_until(guild.id, None)
    _raid_joins.pop(guild.id, None)
    unlock_note = await raid_unlock_invites(guild)
    stats = _raid_stats.pop(guild.id, None)
    released = failed_release = 0
    if release:
        for row in condemnation_list(guild.id):
            if row["origin"] != "raid":
                continue
            member = guild.get_member(row["user_id"])
            if member is None:
                continue
            ok, _ = await release_condemned_member(member, released_by=ended_by)
            released += ok
            failed_release += (not ok)
    lines = [f"**Terminó:** {'automáticamente al vencer el tiempo' if automatic else f'manualmente por {ended_by.mention}' if ended_by else 'manualmente'}"]
    if stats:
        lines += [
            f"**Motivo:** {stats['trigger']}",
            f"**Acción:** {RAID_ACTION_LABELS.get(stats['action'], stats['action'])}",
            f"**Sancionados:** {stats['acted']} · **Registrados:** {stats['logged']} · "
            f"**Omitidos (staff, bots, cuentas antiguas):** {stats['skipped']} · **Fallidos:** {stats['failed']}",
            f"**Mensajes borrados:** {stats['purged']}",
        ]
        if stats["ids"]:
            shown = ", ".join(f"<@{i}>" for i in stats["ids"][:25])
            lines.append(f"**Miembros:** {shown}" + (f" y {len(stats['ids']) - 25} más" if len(stats["ids"]) > 25 else ""))
    lines.append(f"**Invitaciones:** {unlock_note}")
    if release:
        lines.append(f"**Condenas del raid liberadas:** {released}" + (f" ({failed_release} fallaron)" if failed_release else ""))
    elif stats and stats["action"] == "condemn" and stats["acted"]:
        lines.append("ℹ️ Las condenas del raid siguen activas: revísalas con `/condenados` o libéralas con `/raid end liberar:True`.")
    await raid_alert(guild, "🛡️ Modo raid terminado", "\n".join(lines), discord.Color.green())
    return "\n".join(lines)


async def raid_handle_join(member: discord.Member) -> bool:
    """Se llama en cada ingreso. Devuelve True si el miembro ya fue sancionado y debe saltarse
    el flujo normal de verificación."""
    if not raid_enabled():
        return False
    guild = member.guild
    now = time.monotonic()
    window = raid_window_seconds()
    joins = _raid_joins.setdefault(guild.id, deque())
    joins.append((now, member.id))
    while joins and now - joins[0][0] > window:
        joins.popleft()

    if raid_is_active(guild.id):
        return await raid_act_on_member(member)
    if len(joins) < raid_threshold():
        return False
    suspects = [uid for _, uid in joins]
    joins.clear()
    trigger = f"{len(suspects)} ingresos en {format_flex_duration(window)} (umbral: {raid_threshold()})"
    acted = await raid_start(guild, trigger=trigger, suspects=suspects)
    return member.id in acted


@tasks.loop(seconds=15)
async def raid_expiry_loop() -> None:
    for guild in bot.guilds:
        try:
            until = raid_until(guild.id)
            if until is not None and datetime.now(timezone.utc) >= until:
                await raid_end(guild, automatic=True)
            elif until is None and db_meta_get(f"raid_invites_locked:{guild.id}") == "1":
                await raid_unlock_invites(guild)  # restos de un reinicio a mitad de raid
        except Exception:
            traceback.print_exc()


# --- Comandos ---

def raid_config_summary(guild: discord.Guild) -> str:
    role = guild.get_role(raid_ping_role_id()) if raid_ping_role_id() else None
    min_age = raid_min_age_seconds()
    state = "🔴 **MODO RAID ACTIVO**" if raid_is_active(guild.id) else "🟢 Sin raid"
    until = raid_until(guild.id)
    lines = [
        f"🛡️ **Raid Protection** — {'✅ activada' if raid_enabled() else '❌ desactivada'} · {state}",
        f"• Disparo: **{raid_threshold()}** ingresos en **{format_flex_duration(raid_window_seconds())}**",
        f"• Duración del modo raid: **{format_flex_duration(raid_duration_seconds())}**",
        f"• Acción: **{RAID_ACTION_LABELS[raid_action()]}**",
        f"• Filtro de edad de cuenta: **{'cuentas de menos de ' + format_flex_duration(min_age) if min_age else 'sin filtro (todos los ingresos del raid)'}**",
        f"• Pausar invitaciones: **{'sí' if raid_lock_invites_enabled() else 'no'}**",
        f"• Purgar mensajes de los sancionados: **{'sí' if raid_purge_enabled() else 'no'}**",
        f"• Rol de alerta: {role.mention if role else '**ninguno**'}",
    ]
    if raid_is_active(guild.id) and until:
        lines.append(f"• El modo raid termina <t:{int(until.timestamp())}:R>")
    if raid_action() == "condemn" and guild.get_role(condemnation_role_id()) is None:
        lines.append("⚠️ La acción es Condenar pero no hay rol Condenado: configúralo con `/honeypot config rol_castigo`.")
    return "\n".join(lines)


raid_group = HoneypotGroup(
    name="raid",
    description="Protección contra raids (ingresos masivos).",
    guild_only=True,
    default_permissions=discord.Permissions(manage_guild=True),
)


@raid_group.command(name="config", description="Ver o cambiar la configuración de la protección anti-raid.")
@discord.app_commands.describe(
    activado="Activar o desactivar la protección anti-raid",
    ingresos=f"Cuántos ingresos disparan el raid ({RAID_THRESHOLD_MIN} a {RAID_THRESHOLD_MAX})",
    ventana="En cuánto tiempo deben llegar: 10s, 1m… (1s a 1h)",
    duracion="Cuánto dura el modo raid: 30s, 10m, 12h, 2d, 1 mes… (10s a 12 meses)",
    accion="Qué hacer con los sospechosos durante el raid",
    edad_cuenta="Solo actuar sobre cuentas más nuevas que esto: 30m, 7d, 1 mes…; 0 = todas",
    pausar_invitaciones="Pausar las invitaciones del servidor mientras dure el raid",
    purgar="Borrar los mensajes que los sancionados mandaron desde que entraron",
    ping_rol="Rol a mencionar en la alerta de raid",
)
@discord.app_commands.choices(accion=[
    discord.app_commands.Choice(name=label, value=value) for value, label in RAID_ACTION_LABELS.items()
])
async def raid_config(
    interaction: discord.Interaction,
    activado: Optional[bool] = None,
    ingresos: Optional[discord.app_commands.Range[int, RAID_THRESHOLD_MIN, RAID_THRESHOLD_MAX]] = None,
    ventana: Optional[str] = None,
    duracion: Optional[str] = None,
    accion: Optional[discord.app_commands.Choice[str]] = None,
    edad_cuenta: Optional[str] = None,
    pausar_invitaciones: Optional[bool] = None,
    purgar: Optional[bool] = None,
    ping_rol: Optional[discord.Role] = None,
) -> None:
    guild = interaction.guild
    values = (activado, ingresos, ventana, duracion, accion, edad_cuenta, pausar_invitaciones, purgar, ping_rol)
    if all(v is None for v in values):
        await interaction.response.send_message(raid_config_summary(guild), ephemeral=True)
        return

    # Validar todo antes de guardar nada.
    try:
        ventana_s = parse_flex_duration(ventana, RAID_WINDOW_MIN, RAID_WINDOW_MAX) if ventana is not None else None
        duracion_s = parse_flex_duration(duracion, RAID_DURATION_MIN, RAID_DURATION_MAX) if duracion is not None else None
        edad_s = parse_flex_duration(edad_cuenta, 0, RAID_AGE_MAX) if edad_cuenta is not None else None
    except ValueError as e:
        await interaction.response.send_message(f"❌ No guardé nada: {e}", ephemeral=True)
        return
    effective_action = accion.value if accion is not None else raid_action()
    effective_enabled = activado if activado is not None else raid_enabled()
    if effective_enabled and effective_action == "condemn" and guild.get_role(condemnation_role_id()) is None \
            and (activado or accion is not None):
        await interaction.response.send_message(
            "❌ No guardé nada: la acción «Condenar» necesita el rol Condenado. "
            "Configúralo con `/honeypot config rol_castigo` o elige otra acción.",
            ephemeral=True,
        )
        return

    changes: list[str] = []
    if activado is not None:
        db_meta_set("raid_enabled", "1" if activado else "0")
        changes.append("activada" if activado else "desactivada")
    if ingresos is not None:
        db_meta_set("raid_threshold", str(ingresos))
        changes.append(f"ingresos → {ingresos}")
    if ventana_s is not None:
        db_meta_set("raid_window_seconds", str(ventana_s))
        changes.append(f"ventana → {format_flex_duration(ventana_s)}")
    if duracion_s is not None:
        db_meta_set("raid_duration_seconds", str(duracion_s))
        changes.append(f"duración → {format_flex_duration(duracion_s)}")
    if accion is not None:
        db_meta_set("raid_action", accion.value)
        changes.append(f"acción → {accion.name}")
    if edad_s is not None:
        db_meta_set("raid_min_age_seconds", str(edad_s))
        changes.append(f"edad de cuenta → {format_flex_duration(edad_s) if edad_s else 'sin filtro'}")
    if pausar_invitaciones is not None:
        db_meta_set("raid_lock_invites", "1" if pausar_invitaciones else "0")
        changes.append("pausar invitaciones: " + ("sí" if pausar_invitaciones else "no"))
    if purgar is not None:
        db_meta_set("raid_purge", "1" if purgar else "0")
        changes.append("purgar: " + ("sí" if purgar else "no"))
    if ping_rol is not None:
        db_meta_set("raid_ping_role", str(ping_rol.id))
        changes.append(f"rol de alerta → {ping_rol.mention}")
    await interaction.response.send_message(
        "✅ Guardado: " + "; ".join(changes) + "\n\n" + raid_config_summary(guild), ephemeral=True,
    )
    await log_embed(guild, "⚙️ Raid Protection actualizada", f"{interaction.user.mention}: " + "; ".join(changes))


@raid_group.command(name="status", description="Ver si hay un raid activo y la configuración actual.")
async def raid_status(interaction: discord.Interaction) -> None:
    text = raid_config_summary(interaction.guild)
    stats = _raid_stats.get(interaction.guild.id)
    if stats and raid_is_active(interaction.guild.id):
        text += (f"\n\n**Raid en curso:** {stats['trigger']}\n"
                 f"Sancionados: {stats['acted']} · Registrados: {stats['logged']} · "
                 f"Omitidos: {stats['skipped']} · Fallidos: {stats['failed']} · Mensajes borrados: {stats['purged']}")
    await interaction.response.send_message(text, ephemeral=True)


@raid_group.command(name="start", description="Activar el modo raid a mano (p. ej. si ves un ataque que no detectó).")
async def raid_start_command(interaction: discord.Interaction) -> None:
    guild = interaction.guild
    if raid_is_active(guild.id):
        await interaction.response.send_message("ℹ️ El modo raid ya está activo. Usa `/raid status`.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True)
    await raid_start(guild, trigger=f"activado a mano por {interaction.user}", suspects=[], started_by=interaction.user)
    await interaction.followup.send(
        f"✅ Modo raid activado por {format_flex_duration(raid_duration_seconds())}: "
        "los ingresos de ahora en adelante recibirán la acción configurada.", ephemeral=True,
    )


@raid_group.command(name="end", description="Terminar el modo raid ahora y reabrir invitaciones.")
@discord.app_commands.describe(liberar="Liberar también a quienes el raid dejó condenados")
async def raid_end_command(interaction: discord.Interaction, liberar: bool = False) -> None:
    guild = interaction.guild
    if raid_until(guild.id) is None:
        await interaction.response.send_message("ℹ️ No hay ningún modo raid activo.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True)
    summary = await raid_end(guild, automatic=False, ended_by=interaction.user, release=liberar)
    await interaction.followup.send("✅ Modo raid terminado.\n\n" + summary, ephemeral=True)


@raid_group.error
async def raid_group_error(interaction: discord.Interaction, error: discord.app_commands.AppCommandError) -> None:
    await verify_command_error(interaction, error)


bot.tree.add_command(raid_group)


# ---------------------------------------------------------------------------
# 10. VARIABLES ({usuario}, {servidor}, {#canal}, {@rol}, {servericon}…)
# ---------------------------------------------------------------------------
# Se escriben con {nombre} o ${nombre}. No distinguen mayúsculas, tildes ni separadores:
# {servericon} = {server_icon} = {server.icon} = {IconoServidor}. Si una variable no existe o no
# aplica en ese texto, se deja tal cual para que el error se vea. /variables lista y prueba.

VAR_PATTERN = re.compile(r"\$?\{([^{}\n]{1,100})\}")


@dataclass
class VarContext:
    guild: discord.Guild | None = None
    member: discord.Member | discord.User | None = None
    channel: object | None = None  # canal, hilo... de donde sale {canal}


def _var_key(text: str) -> str:
    """Minúsculas, sin tildes y solo letras/números: 'Server_Icon' -> 'servericon'."""
    text = unicodedata.normalize("NFKD", text)
    return re.sub(r"[^a-z0-9]", "", "".join(c for c in text if not unicodedata.combining(c)).lower())


_var_plain: contextvars.ContextVar[bool] = contextvars.ContextVar("var_plain", default=False)


def _safe(text: str) -> str:
    if _var_plain.get():  # texto sin formato (p. ej. el pie de un embed): no hace falta escapar
        return text
    return discord.utils.escape_mentions(discord.utils.escape_markdown(text))


def _vm(fn):  # necesita un miembro en el contexto
    return lambda c: fn(c.member) if c.member is not None else None


def _vg(fn):  # necesita un servidor
    return lambda c: fn(c.guild) if c.guild is not None else None


def _vc(fn):  # necesita un canal
    return lambda c: fn(c.channel) if c.channel is not None else None


def _vn(*_):  # fecha/hora actuales
    return datetime.now(timezone.utc)


def _chan_mention(channel) -> str:
    return channel.mention if channel is not None else ""


# (grupo, nombre, alias, descripción, resolutor)
VARIABLES: list[tuple[str, str, tuple[str, ...], str, object]] = [
    ("👤 Persona (solo en mensajes dirigidos a alguien)", "usuario", ("user", "nombre", "name"),
     "nombre visible", _vm(lambda m: _safe(m.display_name))),
    ("👤 Persona (solo en mensajes dirigidos a alguien)", "mencion", ("mention", "ping"),
     "@mención", _vm(lambda m: m.mention)),
    ("👤 Persona (solo en mensajes dirigidos a alguien)", "usuarioid", ("userid", "id"),
     "ID de usuario", _vm(lambda m: str(m.id))),
    ("👤 Persona (solo en mensajes dirigidos a alguien)", "tag", ("username", "handle"),
     "nombre de usuario (@tag)", _vm(lambda m: _safe(m.name))),
    ("👤 Persona (solo en mensajes dirigidos a alguien)", "avatar", ("pfp", "foto"),
     "URL de su avatar", _vm(lambda m: m.display_avatar.url)),
    ("👤 Persona (solo en mensajes dirigidos a alguien)", "cuenta", ("created", "cuentacreada"),
     "fecha de creación de su cuenta", _vm(lambda m: discord.utils.format_dt(m.created_at, "D"))),
    ("👤 Persona (solo en mensajes dirigidos a alguien)", "cuentahace", ("accountago", "antiguedad"),
     "hace cuánto creó la cuenta", _vm(lambda m: discord.utils.format_dt(m.created_at, "R"))),
    ("👤 Persona (solo en mensajes dirigidos a alguien)", "ingreso", ("joined", "entro"),
     "fecha en que entró al servidor",
     _vm(lambda m: discord.utils.format_dt(m.joined_at, "D") if getattr(m, "joined_at", None) else "")),
    ("🏠 Servidor", "servidor", ("server", "guild", "servername"),
     "nombre del servidor", _vg(lambda g: _safe(g.name))),
    ("🏠 Servidor", "servidorid", ("serverid", "guildid"),
     "ID del servidor", _vg(lambda g: str(g.id))),
    ("🏠 Servidor", "servericon", ("guildicon", "iconoservidor", "icono", "icon"),
     "URL del icono (úsala en imagen/miniatura/icono del pie)", _vg(lambda g: g.icon.url if g.icon else "")),
    ("🏠 Servidor", "serverbanner", ("guildbanner", "bannerservidor", "banner"),
     "URL del banner del servidor", _vg(lambda g: g.banner.url if g.banner else "")),
    ("🏠 Servidor", "miembros", ("members", "membercount", "usuarios"),
     "cantidad de miembros", _vg(lambda g: str(g.member_count or len(g.members)))),
    ("🏠 Servidor", "boosts", ("boostcount",),
     "cantidad de boosts", _vg(lambda g: str(g.premium_subscription_count))),
    ("🏠 Servidor", "nivelboost", ("boostlevel", "premiumtier"),
     "nivel de boost", _vg(lambda g: str(g.premium_tier))),
    ("🏠 Servidor", "dueno", ("owner", "dueño"),
     "@mención del dueño", _vg(lambda g: f"<@{g.owner_id}>")),
    ("🏠 Servidor", "creado", ("servercreated", "guildcreated"),
     "fecha de creación del servidor", _vg(lambda g: discord.utils.format_dt(g.created_at, "D"))),
    ("🏠 Servidor", "reglas", ("rules",),
     "canal de reglas de Discord", _vg(lambda g: _chan_mention(g.rules_channel))),
    ("🏠 Servidor", "sistema", ("system", "systemchannel"),
     "canal de mensajes del sistema", _vg(lambda g: _chan_mention(g.system_channel))),
    ("💬 Canal (donde se publica el mensaje)", "canal", ("channel", "aqui", "here"),
     "#mención del canal", _vc(lambda ch: ch.mention)),
    ("💬 Canal (donde se publica el mensaje)", "canalid", ("channelid",),
     "ID del canal", _vc(lambda ch: str(ch.id))),
    ("💬 Canal (donde se publica el mensaje)", "canalnombre", ("channelname",),
     "nombre del canal", _vc(lambda ch: _safe(ch.name))),
    ("🕒 Tiempo y texto", "fecha", ("date",),
     "fecha de hoy", lambda c: discord.utils.format_dt(_vn(), "D")),
    ("🕒 Tiempo y texto", "hora", ("time",),
     "hora actual", lambda c: discord.utils.format_dt(_vn(), "t")),
    ("🕒 Tiempo y texto", "ahora", ("now",),
     "fecha y hora completas", lambda c: discord.utils.format_dt(_vn(), "F")),
    ("🕒 Tiempo y texto", "timestamp", ("unix",),
     "marca de tiempo Unix", lambda c: str(int(_vn().timestamp()))),
    ("🕒 Tiempo y texto", "salto", ("nl", "br"),
     "salto de línea (útil en campos de una sola línea)", lambda c: "\n"),
]

_VAR_INDEX: dict[str, object] = {}
for _g, _name, _aliases, _desc, _fn in VARIABLES:
    for _k in (_name, *_aliases):
        _VAR_INDEX[_var_key(_k)] = _fn


def _lookup_named(items, arg: str, label_fn=lambda x: x.name):
    """Busca por ID o por nombre (primero exacto, luego sin tildes/emojis/separadores)."""
    arg = arg.strip()
    if not arg:
        return None
    if arg.isdigit():
        return next((i for i in items if i.id == int(arg)), None)
    exact = next((i for i in items if label_fn(i).lower() == arg.lower()), None)
    if exact is not None:
        return exact
    key = _var_key(arg)
    return next((i for i in items if key and _var_key(label_fn(i)) == key), None) if key else None


def _lookup_channel(arg: str, guild: discord.Guild | None) -> str | None:
    if guild is None:
        return None
    ch = _lookup_named([*guild.channels, *guild.threads], arg.lstrip("#"))
    return ch.mention if ch else None


def _lookup_role(arg: str, guild: discord.Guild | None) -> str | None:
    if guild is None:
        return None
    role = _lookup_named(guild.roles, arg.lstrip("@&"))
    return role.mention if role else None


def _lookup_member(arg: str, guild: discord.Guild | None) -> str | None:
    if guild is None:
        return None
    arg = arg.lstrip("@")
    member = _lookup_named(guild.members, arg, label_fn=lambda m: m.display_name) \
        or _lookup_named(guild.members, arg, label_fn=lambda m: m.name)
    return member.mention if member else None


def _lookup_emoji(arg: str, guild: discord.Guild | None) -> str | None:
    pools = [guild.emojis] if guild is not None else []
    pools.append(bot.emojis)
    for pool in pools:
        emoji = next((e for e in pool if e.name.lower() == arg.strip().strip(":").lower()), None)
        if emoji is not None:
            return str(emoji)
    return None


def _var_resolve(name: str, ctx: VarContext) -> str | None:
    """Valor de una variable, o None si no existe / no aplica (se deja el texto original)."""
    raw = name.strip()
    if raw[:1] == "#":
        return _lookup_channel(raw[1:], ctx.guild)
    if raw[:1] == "@":
        return _lookup_role(raw[1:], ctx.guild) or _lookup_member(raw[1:], ctx.guild)
    if ":" in raw:
        prefix, _, rest = raw.partition(":")
        kind = _var_key(prefix)
        if kind in ("canal", "channel", "c"):
            return _lookup_channel(rest, ctx.guild)
        if kind in ("rol", "role", "r"):
            return _lookup_role(rest, ctx.guild)
        if kind in ("usuario", "user", "miembro", "member", "u"):
            return _lookup_member(rest, ctx.guild)
        if kind in ("emoji", "e"):
            return _lookup_emoji(rest, ctx.guild)
        return None
    fn = _VAR_INDEX.get(_var_key(raw))
    return fn(ctx) if fn is not None else None


def render_vars_report(
    text: str, ctx: VarContext, limit: int | None = None, plain: bool = False,
) -> tuple[str, list[str]]:
    """Reemplaza las variables. Devuelve (texto, variables sin resolver). plain=True no escapa markdown."""
    unresolved: list[str] = []

    def repl(match: re.Match) -> str:
        try:
            value = _var_resolve(match.group(1), ctx)
        except Exception:
            traceback.print_exc()
            value = None
        if value is None:
            unresolved.append(match.group(0))
            return match.group(0)
        return value

    token = _var_plain.set(plain)
    try:
        result = VAR_PATTERN.sub(repl, text)
    finally:
        _var_plain.reset(token)
    if limit is not None and len(result) > limit:
        result = result[: limit - 1] + "…"
    return result, unresolved


def render_vars(text: str, ctx: VarContext, limit: int | None = None, plain: bool = False) -> str:
    return render_vars_report(text, ctx, limit, plain)[0]


def render_url_var(text: str, ctx: VarContext) -> str:
    """Para campos de imagen/URL: devuelve la URL ya resuelta, o '' si no es una URL válida."""
    value = render_vars(text.strip(), ctx).strip()
    return value if re.match(r"^https?://", value, re.IGNORECASE) else ""


def variables_embeds() -> list[discord.Embed]:
    groups: dict[str, list[str]] = {}
    for group, name, aliases, desc, _ in VARIABLES:
        extra = " / ".join(f"`{{{a}}}`" for a in aliases[:2])
        groups.setdefault(group, []).append(f"`{{{name}}}` — {desc}" + (f" · {extra}" if extra else ""))
    embed = discord.Embed(
        title="🧩 Variables de El Heraldo",
        description=(
            "Escríbelas con `{nombre}` o `${nombre}` en cualquier texto personalizable del Heraldo "
            "(panel y DM de verificación, aviso del honeypot…). No importan mayúsculas, tildes ni "
            "separadores: `{servericon}` = `{server_icon}` = `{Server.Icon}`.\n"
            "Si una variable no existe o no aplica en ese texto, se deja tal cual para que veas el error."
        ),
        color=discord.Color.blurple(),
    )
    for group, lines in groups.items():
        embed.add_field(name=group, value="\n".join(lines)[:1024], inline=False)
    embed.add_field(
        name="🔎 Buscar cosas del servidor por nombre o ID",
        value=(
            "`{#reglas}` → mención del canal · `{#123456789}` → canal por ID\n"
            "`{@Moderador}` → mención del rol (o del miembro con ese nombre)\n"
            "`{emoji:fuego}` → emoji personalizado del servidor\n"
            "Más explícitas: `{canal:nombre}` · `{rol:nombre}` · `{usuario:nombre}`\n"
            "Ejemplo: `Bienvenid@ {usuario} a {servidor}, lee {#reglas}` · "
            "`<#{canalid}>` · imagen: `{servericon}`"
        ),
        inline=False,
    )
    embed.set_footer(text="Prueba un texto con /variables texto:…")
    return [embed]


@bot.tree.command(name="variables", description="Ver las variables disponibles o probar un texto con ellas.")
@discord.app_commands.describe(
    texto="Texto con variables para probar, por ejemplo: Hola {usuario}, lee {#reglas}",
    miembro="Miembro con cuyos datos se prueba (por defecto, tú)",
    canal="Canal con cuyos datos se prueba (por defecto, este)",
)
@discord.app_commands.checks.has_permissions(manage_guild=True)
@discord.app_commands.guild_only()
async def variables_command(
    interaction: discord.Interaction,
    texto: Optional[str] = None,
    miembro: Optional[discord.Member] = None,
    canal: Optional[discord.abc.GuildChannel] = None,
) -> None:
    if texto is None:
        await interaction.response.send_message(embeds=variables_embeds(), ephemeral=True)
        return
    ctx = VarContext(interaction.guild, miembro or interaction.user, canal or interaction.channel)
    result, unresolved = render_vars_report(texto, ctx, limit=1800)
    note = ""
    if unresolved:
        note = "\n\n⚠️ Sin resolver (revisa el nombre o si aplica ahí): " + " ".join(f"`{u}`" for u in unresolved[:10])
    await interaction.response.send_message(
        f"**Resultado:**\n{result}{note}", ephemeral=True, allowed_mentions=discord.AllowedMentions.none(),
    )


variables_command.error(verify_command_error)


# ---------------------------------------------------------------------------
# 11. RESPUESTAS SIEMPRE EN EMBED, CON FOOTER {servidor}{servericon}
# ---------------------------------------------------------------------------
# Todo lo que El Heraldo envía o edita (respuestas a comandos, follow-ups, mensajes a canales y DMs)
# pasa por aquí: el texto plano se convierte en embed y todo embed sin pie recibe el footer global
# (nombre del servidor + su icono). Los embeds que ya traen un pie propio (el DM de verificación o el
# aviso del honeypot, si lo configuraste) lo conservan. Los mensajes con solo archivos no se tocan.
# Se engancha en discord.py una sola vez, así que no hay que tocar cada comando.

GLOBAL_FOOTER_TEXT = "{servidor}"
GLOBAL_FOOTER_ICON = "{servericon}"
EMBED_DEFAULT_COLOR = 0xE7CF7F  # color de los embeds que nacen de texto plano (❌ rojo, ✅ verde, ⚠️ naranja)

_MISSING = discord.utils.MISSING
_interaction_guilds: dict[str, int] = {}  # token de interacción -> guild_id (para los follow-ups)


def heraldo_footer(guild: discord.Guild | None) -> tuple[str, str]:
    """(texto, icono) del footer global, resueltos con el sistema de variables."""
    if guild is None and len(bot.guilds) == 1:
        guild = bot.guilds[0]
    if guild is None:
        return (bot.user.name if bot.user else "El Heraldo"), ""
    ctx = VarContext(guild)
    return render_vars(GLOBAL_FOOTER_TEXT, ctx, 2048, plain=True), render_url_var(GLOBAL_FOOTER_ICON, ctx)


def stamp_embed(embed: discord.Embed, guild: discord.Guild | None) -> discord.Embed:
    if not embed.footer.text:
        text, icon = heraldo_footer(guild)
        if text:
            embed.set_footer(text=text, icon_url=icon or None)
    return embed


def _content_embed(content: str) -> discord.Embed:
    stripped = content.lstrip()
    if stripped.startswith(("❌", "🚫", "⛔")):
        color = discord.Color.red()
    elif stripped.startswith("✅"):
        color = discord.Color.green()
    elif stripped.startswith(("⚠️", "⚠")):
        color = discord.Color.orange()
    else:
        color = discord.Color(EMBED_DEFAULT_COLOR)
    return discord.Embed(description=content[:4096], color=color)


def _embedify(content, kw: dict, guild: discord.Guild | None, empty):
    """Devuelve (content, kw) con el texto convertido a embed y todos los embeds con footer."""
    embed = kw.get("embed")
    embeds = kw.get("embeds")
    has_embed = embed not in (None, _MISSING)
    has_embeds = embeds not in (None, _MISSING) and len(embeds) > 0
    if has_embed or has_embeds:
        if has_embed:
            stamp_embed(embed, guild)
        if has_embeds:
            for e in embeds:
                stamp_embed(e, guild)
        return content, kw
    if isinstance(content, str) and content.strip():
        kw["embed"] = stamp_embed(_content_embed(content), guild)
        return empty, kw
    return content, kw


def _guild_for(obj) -> discord.Guild | None:
    guild = getattr(obj, "guild", None)
    if guild is None:
        guild = getattr(getattr(obj, "channel", None), "guild", None)
    return guild


def _install_embed_hooks() -> None:
    # Guarda el servidor de cada interacción para los follow-ups (el Webhook no lo conoce).
    orig_from_data = discord.Interaction._from_data

    def _from_data(self, data):
        orig_from_data(self, data)
        try:
            if self.guild_id:
                _interaction_guilds[self.token] = self.guild_id
                while len(_interaction_guilds) > 2000:
                    _interaction_guilds.pop(next(iter(_interaction_guilds)))
        except Exception:
            pass

    discord.Interaction._from_data = _from_data

    def wrap_positional(cls, name, guild_of, empty):
        orig = getattr(cls, name)

        async def wrapper(self, content=_MISSING if empty is _MISSING else None, **kw):
            try:
                content, kw = _embedify(content, kw, guild_of(self), empty)
            except Exception:
                traceback.print_exc()
            return await orig(self, content, **kw)

        wrapper.__name__ = name
        wrapper.__doc__ = orig.__doc__
        setattr(cls, name, wrapper)

    def wrap_edit(cls, name, guild_of):
        orig = getattr(cls, name)

        async def wrapper(self, **kw):
            try:
                content = kw.pop("content", _MISSING)
                if content is not _MISSING and content is not None:
                    content, kw = _embedify(content, kw, guild_of(self), None)
                else:
                    _, kw = _embedify(None, kw, guild_of(self), None)
                if content is not _MISSING:
                    kw["content"] = content
            except Exception:
                traceback.print_exc()
            return await orig(self, **kw)

        wrapper.__name__ = name
        wrapper.__doc__ = orig.__doc__
        setattr(cls, name, wrapper)

    def webhook_guild(self):
        gid = _interaction_guilds.get(getattr(self, "token", None))
        return bot.get_guild(gid) if gid else None

    wrap_positional(discord.InteractionResponse, "send_message", lambda s: s._parent.guild, None)
    wrap_edit(discord.InteractionResponse, "edit_message", lambda s: s._parent.guild)
    wrap_positional(discord.Webhook, "send", webhook_guild, _MISSING)
    wrap_positional(discord.abc.Messageable, "send", _guild_for, None)
    wrap_edit(discord.Message, "edit", _guild_for)
    wrap_edit(discord.WebhookMessage, "edit", _guild_for)
    wrap_edit(discord.InteractionMessage, "edit", _guild_for)
    wrap_edit(discord.Interaction, "edit_original_response", lambda s: s.guild)


_install_embed_hooks()


# ---------------------------------------------------------------------------
# 12. AUTOCOMPLETADO DE VARIABLES (al escribir "{")
# ---------------------------------------------------------------------------
# En los parámetros de texto de los comandos, al escribir "{" (o "${") Discord muestra sugerencias
# como en cualquier comando: variables, o canales/roles/miembros/emojis tras "{#", "{@" y "{emoji:".
# Límite de Discord: el valor de una sugerencia no puede pasar de 100 caracteres, y la sugerencia
# reemplaza el texto entero; si el texto + la variable pasan de 100, no se puede ofrecer.
# Los formularios (modales) de Discord no admiten autocompletado.

_AC_OPEN_RE = re.compile(r"(\$?)\{([^{}\n]*)$")
AC_MAX_VALUE = 100


def _ac_choice(label: str, value: str):
    if not value or len(value) > AC_MAX_VALUE:
        return None
    return discord.app_commands.Choice(name=label[:100], value=value)


def _ac_rank(typed_key: str, *names: str) -> int | None:
    """0 = empieza igual, 1 = lo contiene, None = no coincide."""
    keys = [_var_key(n) for n in names if n]
    if not typed_key:
        return 0
    if any(k.startswith(typed_key) for k in keys):
        return 0
    if any(typed_key in k for k in keys):
        return 1
    return None


def variable_suggestions(guild: discord.Guild | None, current: str) -> list:
    match = _AC_OPEN_RE.search(current)
    if match is None:
        return []
    head = current[: match.start()]
    dollar, typed = match.group(1), match.group(2)
    opener = f"{dollar}{{"
    out: list = []

    def add(label: str, inner: str) -> None:
        choice = _ac_choice(label, f"{head}{opener}{inner}}}")
        if choice is not None:
            out.append(choice)

    def pick(items, label_fn, query: str, make) -> None:
        q = _var_key(query)
        scored = []
        for item in items:
            rank = _ac_rank(q, label_fn(item))
            if rank is not None:
                scored.append((rank, label_fn(item).lower(), item))
        for _, _, item in sorted(scored, key=lambda t: (t[0], len(t[1]), t[1]))[:25]:
            make(item)

    kind, sep, rest = typed.partition(":")
    kind_key = _var_key(kind) if sep else ""
    if guild is not None and (typed[:1] == "#" or kind_key in ("canal", "channel", "c")):
        query = typed[1:] if typed[:1] == "#" else rest
        prefix = "#" if typed[:1] == "#" else f"{kind}:"
        pick([c for c in guild.channels if not isinstance(c, discord.CategoryChannel)], lambda c: c.name, query,
             lambda c: add(f"#{c.name}", f"{prefix}{c.name}"))
    elif guild is not None and (typed[:1] == "@" or kind_key in ("rol", "role", "r", "usuario", "user", "miembro", "member", "u")):
        is_role_kind = typed[:1] == "@" or kind_key in ("rol", "role", "r")
        query = typed[1:] if typed[:1] == "@" else rest
        prefix = "@" if typed[:1] == "@" else f"{kind}:"
        roles = [r for r in guild.roles if not r.is_default()] if is_role_kind else []
        pick(roles, lambda r: r.name, query, lambda r: add(f"@{r.name} (rol)", f"{prefix}{r.name}"))
        if typed[:1] == "@" or not is_role_kind:
            pick(guild.members, lambda m: m.display_name, query,
                 lambda m: add(f"@{m.display_name} (miembro)", f"{prefix}{m.display_name}"))
    elif kind_key in ("emoji", "e"):
        pools = list(guild.emojis) if guild is not None else []
        pick(pools, lambda e: e.name, rest, lambda e: add(f"{e} :{e.name}:", f"{kind}:{e.name}"))
    elif not sep and typed[:1] not in ("#", "@"):
        typed_key = _var_key(typed)
        if not typed_key:  # recién escrita la llave: enseñar también las búsquedas
            for label, inner in (("#  → canales del servidor", "#"), ("@  → roles y miembros", "@"), ("emoji:  → emojis del servidor", "emoji:")):
                choice = _ac_choice(label, f"{head}{opener}{inner}")
                if choice is not None:
                    out.append(choice)
        scored = []
        for group, name, aliases, desc, _ in VARIABLES:
            rank = _ac_rank(typed_key, name, *aliases)
            if rank is None and typed_key and typed_key in _var_key(desc):
                rank = 1
            if rank is not None:
                scored.append((rank, name, aliases, desc))
        for _, name, aliases, desc in sorted(scored, key=lambda t: t[0]):
            add(f"{{{name}}} — {desc}", name)
    return out[:25]


async def variable_autocomplete(
    interaction: discord.Interaction, current: str,
) -> list[discord.app_commands.Choice[str]]:
    perms = getattr(interaction.user, "guild_permissions", None)
    if perms is None or not perms.manage_guild:
        return []
    try:
        return variable_suggestions(interaction.guild, current)
    except Exception:
        traceback.print_exc()
        return []


variables_command.autocomplete("texto")(variable_autocomplete)
for _param in ("titulo", "campo", "mensaje", "footer", "icono_footer"):
    verify_dm_texts.autocomplete(_param)(variable_autocomplete)


# ---------------------------------------------------------------------------
# 13. EMBEDS PERSONALIZADOS (/embed)
# ---------------------------------------------------------------------------
# /embed crear abre un formulario (como /verify_texts); después un panel con botones permite seguir
# editándolo con más formularios: contenido, autor y pie, campos y fecha. Todos los textos aceptan
# variables ({servidor}, {#reglas}, {servericon}…). Los embeds se guardan por nombre y recuerdan los
# mensajes donde se enviaron: al editarlos, esos mensajes se actualizan solos.

EMBED_NAME_RE = re.compile(r"^[a-z0-9_-]{1,32}$")
EMBED_MAX_FIELDS = 25
EMBED_ALLOWED_MENTIONS = discord.AllowedMentions(roles=True, users=True, everyone=False)
EMBED_PERSON_NOTE = "las variables de persona como `{usuario}` solo se resuelven si eliges `miembro` al enviar"


def _embed_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS custom_embeds ("
        "guild_id INTEGER NOT NULL, name TEXT NOT NULL, data TEXT NOT NULL, "
        "refs TEXT NOT NULL DEFAULT '[]', updated_at TEXT, PRIMARY KEY (guild_id, name))"
    )
    return conn


def embed_get(guild_id: int, name: str) -> tuple[dict, list] | None:
    conn = _embed_conn()
    row = conn.execute("SELECT data, refs FROM custom_embeds WHERE guild_id = ? AND name = ?", (guild_id, name)).fetchone()
    conn.close()
    return (json.loads(row[0]), json.loads(row[1])) if row else None


def embed_save(guild_id: int, name: str, data: dict, refs: list | None = None) -> None:
    conn = _embed_conn()
    now = datetime.now(timezone.utc).isoformat()
    if refs is None:
        row = conn.execute("SELECT refs FROM custom_embeds WHERE guild_id = ? AND name = ?", (guild_id, name)).fetchone()
        refs_json = row[0] if row else "[]"
    else:
        refs_json = json.dumps(refs)
    conn.execute(
        "INSERT INTO custom_embeds (guild_id, name, data, refs, updated_at) VALUES (?, ?, ?, ?, ?) "
        "ON CONFLICT(guild_id, name) DO UPDATE SET data = excluded.data, refs = excluded.refs, updated_at = excluded.updated_at",
        (guild_id, name, json.dumps(data), refs_json, now),
    )
    conn.commit()
    conn.close()


def embed_names(guild_id: int) -> list[tuple[str, int]]:
    conn = _embed_conn()
    rows = conn.execute("SELECT name, refs FROM custom_embeds WHERE guild_id = ? ORDER BY name", (guild_id,)).fetchall()
    conn.close()
    return [(name, len(json.loads(refs))) for name, refs in rows]


def embed_delete(guild_id: int, name: str) -> bool:
    conn = _embed_conn()
    cur = conn.execute("DELETE FROM custom_embeds WHERE guild_id = ? AND name = ?", (guild_id, name))
    conn.commit()
    conn.close()
    return cur.rowcount > 0


def parse_hex_color(text: str) -> int:
    raw = text.strip().lstrip("#").removeprefix("0x").removeprefix("0X")
    if not re.fullmatch(r"[0-9a-fA-F]{6}", raw):
        raise ValueError(f"El color `{text}` no es válido: usa un código hexadecimal de 6 dígitos, por ejemplo `#E7CF7F`.")
    return int(raw, 16)


def _check_url_field(label: str, value: str) -> str | None:
    value = value.strip()
    if value and not re.match(r"^https?://", value, re.IGNORECASE) and not VAR_PATTERN.search(value):
        return f"La URL de {label} debe empezar por `http://` o `https://` (o ser una variable como `{{servericon}}`)."
    return None


def build_custom_embed(data: dict, ctx: VarContext) -> tuple[discord.Embed, str | None, list[str]]:
    """(embed, texto fuera del embed, variables sin resolver) con las variables ya aplicadas."""
    unresolved: list[str] = []

    def r(text: str, limit: int) -> str:
        out, bad = render_vars_report(text or "", ctx, limit, plain=False)
        unresolved.extend(bad)
        return out

    color = EMBED_DEFAULT_COLOR
    if data.get("color"):
        try:
            color = parse_hex_color(data["color"])
        except ValueError:
            pass
    embed = discord.Embed(color=discord.Color(color))
    if data.get("title"):
        embed.title = r(data["title"], 256)
    if data.get("description"):
        embed.description = r(data["description"], 4096)
    if data.get("author"):
        icon = render_url_var(data.get("author_icon", ""), ctx) if data.get("author_icon") else ""
        embed.set_author(name=r(data["author"], 256), icon_url=icon or None)
    for f in data.get("fields", []):
        embed.add_field(name=r(f["name"], 256) or "\u200b", value=r(f["value"], 1024) or "\u200b", inline=bool(f.get("inline")))
    image = render_url_var(data["image"], ctx) if data.get("image") else ""
    if image:
        embed.set_image(url=image)
    thumb = render_url_var(data["thumbnail"], ctx) if data.get("thumbnail") else ""
    if thumb:
        embed.set_thumbnail(url=thumb)
    if data.get("footer"):
        icon = render_url_var(data.get("footer_icon", ""), ctx) if data.get("footer_icon") else ""
        embed.set_footer(text=render_vars(data["footer"], ctx, 2048, plain=True), icon_url=icon or None)
    if data.get("timestamp"):
        embed.timestamp = datetime.now(timezone.utc)
    content = r(data["content"], 2000) if data.get("content") else None
    return embed, (content or None), list(dict.fromkeys(unresolved))


def embed_is_empty(embed: discord.Embed) -> bool:
    return not (embed.title or embed.description or embed.fields or embed.image or embed.thumbnail or embed.author)


async def embed_sync(guild: discord.Guild, name: str) -> int:
    """Actualiza los mensajes donde ya se envió el embed. Devuelve cuántos se actualizaron."""
    record = embed_get(guild.id, name)
    if record is None:
        return 0
    data, refs = record
    kept, updated = [], 0
    for channel_id, message_id in refs:
        channel = guild.get_channel_or_thread(channel_id)
        if channel is None:
            continue
        try:
            message = await channel.fetch_message(message_id)
            embed, content, _ = build_custom_embed(data, VarContext(guild, None, channel))
            if embed_is_empty(embed):
                kept.append([channel_id, message_id])
                continue
            await message.edit(content=content, embed=embed, allowed_mentions=EMBED_ALLOWED_MENTIONS)
            kept.append([channel_id, message_id])
            updated += 1
        except discord.NotFound:
            continue  # el mensaje se borró: se olvida
        except discord.HTTPException:
            kept.append([channel_id, message_id])
    if kept != refs:
        embed_save(guild.id, name, data, kept)
    return updated


async def embed_send(
    guild: discord.Guild, name: str, channel, member: discord.Member | None = None,
) -> str:
    record = embed_get(guild.id, name)
    if record is None:
        return f"❌ No existe un embed llamado `{name}`."
    data, refs = record
    embed, content, _ = build_custom_embed(data, VarContext(guild, member, channel))
    if embed_is_empty(embed):
        return "❌ El embed está vacío: añade título, descripción o algún campo antes de enviarlo."
    if len(embed) > 6000:
        return f"❌ El embed mide {len(embed)} caracteres y Discord permite 6000 como máximo: acórtalo."
    try:
        message = await channel.send(content=content, embed=embed, allowed_mentions=EMBED_ALLOWED_MENTIONS)
    except discord.Forbidden:
        return f"❌ No tengo permiso para enviar mensajes o embeds en {channel.mention}."
    except discord.HTTPException as e:
        return f"❌ Discord rechazó el embed: {e}"
    refs.append([channel.id, message.id])
    embed_save(guild.id, name, data, refs)
    return f"✅ Embed `{name}` enviado en {channel.mention}: {message.jump_url}"


def _clean(value: str | None) -> str:
    return (value or "").strip()


class EmbedContentModal(discord.ui.Modal):
    """Título, descripción, color e imágenes."""

    def __init__(self, guild_id: int, name: str, data: dict, is_new: bool = False) -> None:
        super().__init__(title=f"Embed: {name}"[:45])
        self.guild_id, self.name, self.data, self.is_new = guild_id, name, data, is_new
        self.e_title = discord.ui.TextInput(
            label="Título", default=data.get("title", ""), required=False, max_length=256)
        self.e_description = discord.ui.TextInput(
            label="Descripción", style=discord.TextStyle.paragraph, default=data.get("description", ""),
            required=False, max_length=4000, placeholder="Admite variables: {servidor}, {#reglas}…")
        self.e_color = discord.ui.TextInput(
            label="Color (hexadecimal)", default=data.get("color", ""), required=False, max_length=10,
            placeholder="#E7CF7F")
        self.e_image = discord.ui.TextInput(
            label="Imagen grande (URL o variable)", default=data.get("image", ""), required=False, max_length=500,
            placeholder="https://… o {serverbanner}")
        self.e_thumb = discord.ui.TextInput(
            label="Miniatura (URL o variable)", default=data.get("thumbnail", ""), required=False, max_length=500,
            placeholder="https://… o {servericon}")
        for item in (self.e_title, self.e_description, self.e_color, self.e_image, self.e_thumb):
            self.add_item(item)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        color = _clean(self.e_color.value)
        error = None
        if color:
            try:
                parse_hex_color(color)
            except ValueError as e:
                error = str(e)
        error = error or _check_url_field("la imagen", self.e_image.value) or _check_url_field("la miniatura", self.e_thumb.value)
        if error:
            await interaction.response.send_message(f"❌ No guardé nada: {error}", ephemeral=True)
            return
        if self.is_new and embed_get(self.guild_id, self.name) is not None:
            await interaction.response.send_message(f"❌ Ya existe un embed llamado `{self.name}`.", ephemeral=True)
            return
        record = embed_get(self.guild_id, self.name)
        data = record[0] if record else dict(self.data)
        data.update(title=_clean(self.e_title.value), description=_clean(self.e_description.value),
                    color=color, image=_clean(self.e_image.value), thumbnail=_clean(self.e_thumb.value))
        embed_save(self.guild_id, self.name, data)
        await embed_refresh(interaction, self.name, new=self.is_new)


class EmbedAuthorFooterModal(discord.ui.Modal):
    """Autor, pie y texto fuera del embed."""

    def __init__(self, guild_id: int, name: str, data: dict) -> None:
        super().__init__(title=f"Autor y pie: {name}"[:45])
        self.guild_id, self.name = guild_id, name
        self.e_author = discord.ui.TextInput(
            label="Autor (arriba del título)", default=data.get("author", ""), required=False, max_length=256)
        self.e_author_icon = discord.ui.TextInput(
            label="Icono del autor (URL o variable)", default=data.get("author_icon", ""), required=False,
            max_length=500, placeholder="https://… o {servericon}")
        self.e_footer = discord.ui.TextInput(
            label="Pie del embed", default=data.get("footer", ""), required=False, max_length=2048,
            placeholder="Vacío = pie del servidor")
        self.e_footer_icon = discord.ui.TextInput(
            label="Icono del pie (URL o variable)", default=data.get("footer_icon", ""), required=False,
            max_length=500, placeholder="https://… o {servericon}")
        self.e_content = discord.ui.TextInput(
            label="Texto fuera del embed (menciones)", style=discord.TextStyle.paragraph,
            default=data.get("content", ""), required=False, max_length=2000,
            placeholder="Aquí sí notifican las menciones: <@&rol>, {@Moderador}…")
        for item in (self.e_author, self.e_author_icon, self.e_footer, self.e_footer_icon, self.e_content):
            self.add_item(item)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        error = _check_url_field("el icono del autor", self.e_author_icon.value) \
            or _check_url_field("el icono del pie", self.e_footer_icon.value)
        if error:
            await interaction.response.send_message(f"❌ No guardé nada: {error}", ephemeral=True)
            return
        record = embed_get(self.guild_id, self.name)
        if record is None:
            await interaction.response.send_message("❌ Ese embed ya no existe.", ephemeral=True)
            return
        data = record[0]
        data.update(author=_clean(self.e_author.value), author_icon=_clean(self.e_author_icon.value),
                    footer=_clean(self.e_footer.value), footer_icon=_clean(self.e_footer_icon.value),
                    content=_clean(self.e_content.value))
        embed_save(self.guild_id, self.name, data)
        await embed_refresh(interaction, self.name)


class EmbedFieldModal(discord.ui.Modal):
    def __init__(self, guild_id: int, name: str) -> None:
        super().__init__(title=f"Nuevo campo: {name}"[:45])
        self.guild_id, self.name = guild_id, name
        self.f_name = discord.ui.TextInput(label="Nombre del campo", max_length=256)
        self.f_value = discord.ui.TextInput(
            label="Valor", style=discord.TextStyle.paragraph, max_length=1024,
            placeholder="Admite variables: {miembros}, {#reglas}…")
        self.f_inline = discord.ui.TextInput(
            label="¿En línea con otros campos? (sí / no)", default="no", required=False, max_length=3)
        for item in (self.f_name, self.f_value, self.f_inline):
            self.add_item(item)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        record = embed_get(self.guild_id, self.name)
        if record is None:
            await interaction.response.send_message("❌ Ese embed ya no existe.", ephemeral=True)
            return
        data = record[0]
        fields = data.setdefault("fields", [])
        if len(fields) >= EMBED_MAX_FIELDS:
            await interaction.response.send_message(f"❌ Un embed admite como máximo {EMBED_MAX_FIELDS} campos.", ephemeral=True)
            return
        inline = _clean(self.f_inline.value).lower() in ("si", "sí", "s", "yes", "y", "true", "1")
        fields.append({"name": _clean(self.f_name.value), "value": _clean(self.f_value.value), "inline": inline})
        embed_save(self.guild_id, self.name, data)
        await embed_refresh(interaction, self.name)


class EmbedChannelPicker(discord.ui.View):
    """Elegir el canal al que enviar el embed desde el panel."""

    def __init__(self, owner_id: int, name: str) -> None:
        super().__init__(timeout=300)
        self.owner_id, self.name = owner_id, name
        select = discord.ui.ChannelSelect(
            placeholder="Elige el canal de destino…",
            channel_types=[discord.ChannelType.text, discord.ChannelType.news],
        )
        select.callback = self.picked
        self.select = select
        self.add_item(select)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("Este selector no es tuyo.", ephemeral=True)
            return False
        return True

    async def picked(self, interaction: discord.Interaction) -> None:
        channel = interaction.guild.get_channel(self.select.values[0].id)
        if channel is None:
            await interaction.response.edit_message(content="❌ No pude encontrar ese canal.", view=None)
            return
        await interaction.response.defer()
        result = await embed_send(interaction.guild, self.name, channel)
        await interaction.edit_original_response(content=result, view=None)


class EmbedEditorView(discord.ui.View):
    def __init__(self, owner_id: int, guild_id: int, name: str, data: dict) -> None:
        super().__init__(timeout=900)
        self.owner_id, self.guild_id, self.name = owner_id, guild_id, name
        self.toggle_time.label = "🕒 Fecha: " + ("sí" if data.get("timestamp") else "no")
        fields = data.get("fields", [])
        if fields:
            options = [
                discord.SelectOption(label=f"{i + 1}. {f['name']}"[:100], value=str(i), description=f["value"][:100] or None)
                for i, f in enumerate(fields[:25])
            ]
            select = discord.ui.Select(placeholder="🗑️ Quitar un campo…", options=options, row=1)
            select.callback = self.remove_field
            self.remove_select = select
            self.add_item(select)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("Este editor no es tuyo: usa `/embed editar`.", ephemeral=True)
            return False
        return True

    def _data(self) -> dict | None:
        record = embed_get(self.guild_id, self.name)
        return record[0] if record else None

    async def _gone(self, interaction: discord.Interaction) -> None:
        await interaction.response.edit_message(content="❌ Ese embed ya no existe.", embed=None, view=None)

    @discord.ui.button(label="✏️ Contenido", style=discord.ButtonStyle.primary, row=0)
    async def edit_content(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        data = self._data()
        if data is None:
            return await self._gone(interaction)
        await interaction.response.send_modal(EmbedContentModal(self.guild_id, self.name, data))

    @discord.ui.button(label="👤 Autor y pie", style=discord.ButtonStyle.primary, row=0)
    async def edit_author(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        data = self._data()
        if data is None:
            return await self._gone(interaction)
        await interaction.response.send_modal(EmbedAuthorFooterModal(self.guild_id, self.name, data))

    @discord.ui.button(label="➕ Campo", style=discord.ButtonStyle.secondary, row=0)
    async def add_field(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await interaction.response.send_modal(EmbedFieldModal(self.guild_id, self.name))

    @discord.ui.button(label="🕒 Fecha: no", style=discord.ButtonStyle.secondary, row=0)
    async def toggle_time(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        record = embed_get(self.guild_id, self.name)
        if record is None:
            return await self._gone(interaction)
        data = record[0]
        data["timestamp"] = not data.get("timestamp")
        embed_save(self.guild_id, self.name, data)
        await embed_refresh(interaction, self.name)

    async def remove_field(self, interaction: discord.Interaction) -> None:
        record = embed_get(self.guild_id, self.name)
        if record is None:
            return await self._gone(interaction)
        data = record[0]
        index = int(self.remove_select.values[0])
        if 0 <= index < len(data.get("fields", [])):
            data["fields"].pop(index)
            embed_save(self.guild_id, self.name, data)
        await embed_refresh(interaction, self.name)

    @discord.ui.button(label="📤 Enviar", style=discord.ButtonStyle.success, row=2)
    async def send_embed(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await interaction.response.send_message(
            "¿A qué canal lo envío?", view=EmbedChannelPicker(interaction.user.id, self.name), ephemeral=True)


async def embed_refresh(interaction: discord.Interaction, name: str, new: bool = False) -> None:
    """Sincroniza los mensajes ya enviados y muestra (o actualiza) el panel con la vista previa."""
    guild = interaction.guild
    record = embed_get(guild.id, name)
    if record is None:
        await interaction.response.send_message("❌ Ese embed ya no existe.", ephemeral=True)
        return
    data, refs = record
    synced = 0
    if refs and not new:
        await interaction.response.defer()
        synced = await embed_sync(guild, name)
    embed, content, unresolved = build_custom_embed(data, VarContext(guild, None, interaction.channel))
    if embed_is_empty(embed):
        embed.description = "*(embed vacío: usa ✏️ Contenido para escribirlo)*"
    lines = [f"📝 **Editando** `{name}` — vista previa (las variables ya aplicadas)."]
    if content:
        lines.append(f"Texto fuera del embed: {content}")
    if synced:
        lines.append(f"🔄 {synced} mensaje(s) ya enviados se actualizaron.")
    if unresolved:
        lines.append("⚠️ Sin resolver: " + " ".join(f"`{u}`" for u in unresolved[:8]) + f" · {EMBED_PERSON_NOTE}.")
    view = EmbedEditorView(interaction.user.id, guild.id, name, data)
    text = "\n".join(lines)[:1900]
    kwargs = dict(content=text, embed=embed, view=view, allowed_mentions=discord.AllowedMentions.none())
    if new:
        await interaction.response.send_message(ephemeral=True, **kwargs)
    elif interaction.response.is_done():
        await interaction.edit_original_response(**kwargs)
    else:
        await interaction.response.edit_message(**kwargs)


embed_group = HoneypotGroup(
    name="embed",
    description="Crear, editar y enviar embeds personalizados.",
    guild_only=True,
    default_permissions=discord.Permissions(manage_guild=True),
)


async def embed_name_autocomplete(interaction: discord.Interaction, current: str) -> list[discord.app_commands.Choice[str]]:
    if interaction.guild is None:
        return []
    q = current.strip().lower()
    return [
        discord.app_commands.Choice(name=f"{name} ({n} enviado(s))" if n else name, value=name)
        for name, n in embed_names(interaction.guild.id) if q in name
    ][:25]


@embed_group.command(name="crear", description="Crear un embed nuevo con un formulario.")
@discord.app_commands.describe(nombre="Nombre para guardarlo (letras, números, - y _; máx. 32)")
async def embed_create(interaction: discord.Interaction, nombre: str) -> None:
    name = nombre.strip().lower()
    if not EMBED_NAME_RE.match(name):
        await interaction.response.send_message("❌ El nombre solo puede tener letras minúsculas sin tildes, números, `-` y `_` (máx. 32).", ephemeral=True)
        return
    if embed_get(interaction.guild.id, name) is not None:
        await interaction.response.send_message(f"❌ Ya existe un embed llamado `{name}`. Edítalo con `/embed editar`.", ephemeral=True)
        return
    await interaction.response.send_modal(EmbedContentModal(interaction.guild.id, name, {}, is_new=True))


@embed_group.command(name="editar", description="Abrir el panel de edición de un embed guardado.")
@discord.app_commands.describe(nombre="Embed a editar")
@discord.app_commands.autocomplete(nombre=embed_name_autocomplete)
async def embed_edit(interaction: discord.Interaction, nombre: str) -> None:
    name = nombre.strip().lower()
    if embed_get(interaction.guild.id, name) is None:
        await interaction.response.send_message(f"❌ No existe un embed llamado `{name}`. Mira `/embed lista`.", ephemeral=True)
        return
    await embed_refresh(interaction, name, new=True)


@embed_group.command(name="enviar", description="Enviar un embed guardado a un canal.")
@discord.app_commands.describe(
    nombre="Embed a enviar", canal="Canal de destino (por defecto, este)",
    miembro="Miembro cuyos datos usan {usuario}, {mencion}, {avatar}… (opcional)",
)
@discord.app_commands.autocomplete(nombre=embed_name_autocomplete)
async def embed_send_command(
    interaction: discord.Interaction, nombre: str,
    canal: Optional[discord.TextChannel] = None, miembro: Optional[discord.Member] = None,
) -> None:
    await interaction.response.defer(ephemeral=True)
    result = await embed_send(interaction.guild, nombre.strip().lower(), canal or interaction.channel, miembro)
    await interaction.followup.send(result, ephemeral=True)


@embed_group.command(name="lista", description="Ver los embeds guardados.")
async def embed_list_command(interaction: discord.Interaction) -> None:
    names = embed_names(interaction.guild.id)
    if not names:
        await interaction.response.send_message("No hay embeds guardados. Crea uno con `/embed crear`.", ephemeral=True)
        return
    lines = [f"• `{name}`" + (f" — enviado en {n} mensaje(s)" if n else "") for name, n in names]
    await interaction.response.send_message("**Embeds guardados:**\n" + "\n".join(lines)[:1900], ephemeral=True)


@embed_group.command(name="borrar", description="Borrar un embed guardado (los mensajes ya enviados se quedan).")
@discord.app_commands.describe(nombre="Embed a borrar")
@discord.app_commands.autocomplete(nombre=embed_name_autocomplete)
async def embed_delete_command(interaction: discord.Interaction, nombre: str) -> None:
    name = nombre.strip().lower()
    if embed_delete(interaction.guild.id, name):
        await interaction.response.send_message(f"🗑️ Embed `{name}` borrado. Los mensajes ya enviados no se tocan, pero dejarán de actualizarse.", ephemeral=True)
    else:
        await interaction.response.send_message(f"❌ No existe un embed llamado `{name}`.", ephemeral=True)


@embed_group.error
async def embed_group_error(interaction: discord.Interaction, error: discord.app_commands.AppCommandError) -> None:
    await verify_command_error(interaction, error)


bot.tree.add_command(embed_group)


# ---------------------------------------------------------------------------
# 14. SISTEMA DE SUGERENCIAS — panel fijo + formulario + revisión por DM
# ---------------------------------------------------------------------------

SUGGESTION_PANEL_BUTTON_ID = "heraldo_suggestion_create"
SUGGESTION_REVIEW_PREFIX = "heraldo_suggestion_review"
SUGGESTION_STATUS_PENDING = "pending"
SUGGESTION_STATUS_ACCEPTED = "accepted"
SUGGESTION_STATUS_REJECTED = "rejected"


def suggestion_db_init() -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS suggestions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            decided_by INTEGER,
            rejection_reason TEXT,
            created_at TEXT NOT NULL,
            decided_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS suggestion_reviewers (
            guild_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            PRIMARY KEY (guild_id, user_id)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS suggestion_review_messages (
            suggestion_id INTEGER NOT NULL,
            reviewer_id INTEGER NOT NULL,
            channel_id INTEGER NOT NULL,
            message_id INTEGER NOT NULL,
            PRIMARY KEY (suggestion_id, reviewer_id)
        )
    """)
    conn.commit()
    conn.close()


def suggestion_meta_key(guild_id: int, suffix: str) -> str:
    return f"suggestions:{guild_id}:{suffix}"


def suggestion_get_channel_id(guild_id: int) -> int:
    return int(db_meta_get(suggestion_meta_key(guild_id, "channel")) or 0)


def suggestion_set_channel_id(guild_id: int, channel_id: int) -> None:
    db_meta_set(suggestion_meta_key(guild_id, "channel"), str(channel_id))


def suggestion_get_panel_message_id(guild_id: int) -> int:
    return int(db_meta_get(suggestion_meta_key(guild_id, "panel")) or 0)


def suggestion_set_panel_message_id(guild_id: int, message_id: int) -> None:
    db_meta_set(suggestion_meta_key(guild_id, "panel"), str(message_id))


def suggestion_owner_enabled(guild_id: int) -> bool:
    value = db_meta_get(suggestion_meta_key(guild_id, "owner"))
    return value != "0"  # por defecto: el creador/owner recibe las sugerencias


def suggestion_set_owner_enabled(guild_id: int, enabled: bool) -> None:
    db_meta_set(suggestion_meta_key(guild_id, "owner"), "1" if enabled else "0")


def suggestion_reviewer_ids(guild_id: int) -> list[int]:
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT user_id FROM suggestion_reviewers WHERE guild_id = ? ORDER BY user_id",
        (guild_id,),
    ).fetchall()
    conn.close()
    return [int(row[0]) for row in rows]


def suggestion_add_reviewer(guild_id: int, user_id: int) -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT OR IGNORE INTO suggestion_reviewers (guild_id, user_id) VALUES (?, ?)",
        (guild_id, user_id),
    )
    conn.commit()
    conn.close()


def suggestion_remove_reviewer(guild_id: int, user_id: int) -> bool:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.execute(
        "DELETE FROM suggestion_reviewers WHERE guild_id = ? AND user_id = ?",
        (guild_id, user_id),
    )
    conn.commit()
    conn.close()
    return cur.rowcount > 0


def suggestion_get(suggestion_id: int) -> sqlite3.Row | None:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT * FROM suggestions WHERE id = ?", (suggestion_id,)).fetchone()
    conn.close()
    return row


def suggestion_create(guild_id: int, user_id: int, title: str, content: str) -> int:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.execute(
        "INSERT INTO suggestions (guild_id, user_id, title, content, status, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (guild_id, user_id, title, content, SUGGESTION_STATUS_PENDING, datetime.now(timezone.utc).isoformat()),
    )
    suggestion_id = int(cur.lastrowid)
    conn.commit()
    conn.close()
    return suggestion_id


def suggestion_set_review_message(suggestion_id: int, reviewer_id: int, channel_id: int, message_id: int) -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT OR REPLACE INTO suggestion_review_messages "
        "(suggestion_id, reviewer_id, channel_id, message_id) VALUES (?, ?, ?, ?)",
        (suggestion_id, reviewer_id, channel_id, message_id),
    )
    conn.commit()
    conn.close()


def suggestion_review_messages(suggestion_id: int) -> list[sqlite3.Row]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT * FROM suggestion_review_messages WHERE suggestion_id = ?",
        (suggestion_id,),
    ).fetchall()
    conn.close()
    return rows


def suggestion_decide(
    suggestion_id: int,
    status: str,
    decided_by: int,
    rejection_reason: str | None = None,
) -> bool:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.execute(
        """UPDATE suggestions
           SET status = ?, decided_by = ?, rejection_reason = ?, decided_at = ?
           WHERE id = ? AND status = 'pending'""",
        (status, decided_by, rejection_reason, datetime.now(timezone.utc).isoformat(), suggestion_id),
    )
    conn.commit()
    conn.close()
    return cur.rowcount == 1


def suggestion_panel_embed(guild: discord.Guild) -> discord.Embed:
    embed = discord.Embed(
        title="EL ORÁCULO ESCUCHA",
        description=(
            "Toda alma tiene algo que pedir, y este paraíso está dispuesto a escuchar.\n\n"
            "¿Tienes una idea para mejorar este mundo? ¿Alguna inquietud? Un canal que falta, "
            "un evento que sueñas ver, una regla que merece cambiar — El Oráculo la recibe.\n\n"
            "**¿Cómo invocar tu deseo?**\n"
            "Pulsa **💡 Crear sugerencia** y completa el formulario privado.\n\n"
            "Tu propuesta será enviada directamente a quienes gobiernan este paraíso. "
            "El canal no se llenará con las sugerencias.\n\n"
            "No hay deseo demasiado pequeño, ni pecado demasiado grande de proponer."
        ),
        color=discord.Color.blurple(),
    )
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)
    embed.set_footer(text="Paraíso Morboso 2026 © - El Heraldo 🪽")
    return embed


class SuggestionPanelView(discord.ui.View):
    def __init__(self) -> None:
        super().__init__(timeout=None)
        button = discord.ui.Button(
            label="💡 Crear sugerencia",
            style=discord.ButtonStyle.primary,
            custom_id=SUGGESTION_PANEL_BUTTON_ID,
        )
        button.callback = self.create_suggestion
        self.add_item(button)

    async def create_suggestion(self, interaction: discord.Interaction) -> None:
        if interaction.guild is None:
            await interaction.response.send_message("Este botón solo funciona dentro del servidor.", ephemeral=True)
            return
        await interaction.response.send_modal(SuggestionModal())


class SuggestionModal(discord.ui.Modal, title="Nueva sugerencia"):
    titulo = discord.ui.TextInput(
        label="Título de la sugerencia",
        placeholder="Ej.: Crear un canal para eventos",
        max_length=100,
        required=True,
    )
    propuesta = discord.ui.TextInput(
        label="¿Qué propones?",
        placeholder="Explica tu idea con claridad…",
        style=discord.TextStyle.paragraph,
        max_length=1800,
        required=True,
    )

    async def on_submit(self, interaction: discord.Interaction) -> None:
        guild = interaction.guild
        if guild is None:
            await interaction.response.send_message("Este formulario solo funciona dentro del servidor.", ephemeral=True)
            return

        reviewer_ids: list[int] = []
        if suggestion_owner_enabled(guild.id) and guild.owner_id:
            reviewer_ids.append(guild.owner_id)
        for user_id in suggestion_reviewer_ids(guild.id):
            if user_id not in reviewer_ids:
                reviewer_ids.append(user_id)

        if not reviewer_ids:
            await interaction.response.send_message(
                "⚠️ El sistema de sugerencias todavía no tiene ningún destinatario configurado. Avisa a un administrador.",
                ephemeral=True,
            )
            return

        suggestion_id = suggestion_create(
            guild.id,
            interaction.user.id,
            self.titulo.value.strip(),
            self.propuesta.value.strip(),
        )

        embed = discord.Embed(
            title=f"💡 Nueva sugerencia #{suggestion_id}",
            description=self.propuesta.value.strip(),
            color=discord.Color.blurple(),
            timestamp=datetime.now(timezone.utc),
        )
        embed.add_field(name="Título", value=self.titulo.value.strip(), inline=False)
        embed.add_field(name="Solicitada por", value=f"{interaction.user.mention} (`{interaction.user.id}`)", inline=False)
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        embed.set_footer(text=f"{guild.name} · Sugerencia #{suggestion_id}")

        sent = 0
        for reviewer_id in reviewer_ids:
            try:
                reviewer = await bot.fetch_user(reviewer_id)
                message = await reviewer.send(embed=embed, view=SuggestionReviewView(suggestion_id))
                suggestion_set_review_message(suggestion_id, reviewer_id, message.channel.id, message.id)
                sent += 1
            except discord.HTTPException:
                await log_embed(
                    guild,
                    "⚠️ No pude enviar una sugerencia por DM",
                    f"La sugerencia #{suggestion_id} de {interaction.user.mention} no pudo llegar a <@{reviewer_id}>.",
                    discord.Color.orange(),
                )

        if sent == 0:
            suggestion_decide(suggestion_id, SUGGESTION_STATUS_REJECTED, bot.user.id if bot.user else 0,
                              "No se pudo entregar la sugerencia a ningún destinatario configurado.")
            await interaction.response.send_message(
                "❌ No pude entregar la sugerencia por mensaje privado. Comprueba que los destinatarios permitan DMs.",
                ephemeral=True,
            )
            return

        await interaction.response.send_message(
            f"✅ Tu sugerencia **#{suggestion_id}** fue enviada de forma privada a {sent} destinatario(s). "
            "Cuando sea aceptada o rechazada recibirás la respuesta por DM.",
            ephemeral=True,
        )
        await log_embed(
            guild,
            "💡 Nueva sugerencia",
            f"Sugerencia **#{suggestion_id}** enviada por {interaction.user.mention} a {sent} destinatario(s).",
            discord.Color.blurple(),
        )


class SuggestionRejectModal(discord.ui.Modal):
    def __init__(self, suggestion_id: int) -> None:
        super().__init__(title=f"Rechazar sugerencia #{suggestion_id}"[:45])
        self.suggestion_id = suggestion_id
        self.reason = discord.ui.TextInput(
            label="Razón del rechazo (obligatoria)",
            placeholder="Explica por qué no se acepta esta sugerencia…",
            style=discord.TextStyle.paragraph,
            min_length=3,
            max_length=1500,
            required=True,
        )
        self.add_item(self.reason)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        await finalize_suggestion_decision(
            interaction,
            self.suggestion_id,
            SUGGESTION_STATUS_REJECTED,
            self.reason.value.strip(),
        )


class SuggestionReviewView(discord.ui.View):
    def __init__(self, suggestion_id: int) -> None:
        super().__init__(timeout=None)
        self.suggestion_id = suggestion_id
        accept = discord.ui.Button(
            label="Aceptar",
            style=discord.ButtonStyle.success,
            custom_id=f"{SUGGESTION_REVIEW_PREFIX}:accept:{suggestion_id}",
        )
        reject = discord.ui.Button(
            label="Rechazar",
            style=discord.ButtonStyle.danger,
            custom_id=f"{SUGGESTION_REVIEW_PREFIX}:reject:{suggestion_id}",
        )
        accept.callback = self.accept_suggestion
        reject.callback = self.reject_suggestion
        self.add_item(accept)
        self.add_item(reject)

    async def accept_suggestion(self, interaction: discord.Interaction) -> None:
        await finalize_suggestion_decision(interaction, self.suggestion_id, SUGGESTION_STATUS_ACCEPTED, None)

    async def reject_suggestion(self, interaction: discord.Interaction) -> None:
        row = suggestion_get(self.suggestion_id)
        if row is None:
            await interaction.response.send_message("❌ Esa sugerencia ya no existe.", ephemeral=True)
            return
        if row["status"] != SUGGESTION_STATUS_PENDING:
            await interaction.response.send_message("ℹ️ Esta sugerencia ya fue resuelta.", ephemeral=True)
            return
        await interaction.response.send_modal(SuggestionRejectModal(self.suggestion_id))


async def finalize_suggestion_decision(
    interaction: discord.Interaction,
    suggestion_id: int,
    status: str,
    rejection_reason: str | None,
) -> None:
    row = suggestion_get(suggestion_id)
    if row is None:
        await _suggestion_interaction_reply(interaction, "❌ Esa sugerencia ya no existe.", ephemeral=True)
        return
    if row["status"] != SUGGESTION_STATUS_PENDING:
        await _suggestion_interaction_reply(interaction, "ℹ️ Esta sugerencia ya fue resuelta por otra persona.", ephemeral=True)
        return
    if status == SUGGESTION_STATUS_REJECTED and not (rejection_reason or "").strip():
        await _suggestion_interaction_reply(interaction, "❌ La razón del rechazo es obligatoria.", ephemeral=True)
        return

    changed = suggestion_decide(suggestion_id, status, interaction.user.id, rejection_reason)
    if not changed:
        await _suggestion_interaction_reply(interaction, "ℹ️ Esta sugerencia ya fue resuelta por otra persona.", ephemeral=True)
        return

    guild = bot.get_guild(int(row["guild_id"]))
    requester = None
    try:
        requester = await bot.fetch_user(int(row["user_id"]))
    except discord.HTTPException:
        pass

    decision_word = "aceptada" if status == SUGGESTION_STATUS_ACCEPTED else "rechazada"
    decision_color = discord.Color.green() if status == SUGGESTION_STATUS_ACCEPTED else discord.Color.red()
    result_embed = discord.Embed(
        title=f"{'✅' if status == SUGGESTION_STATUS_ACCEPTED else '❌'} Tu sugerencia #{suggestion_id} fue {decision_word}",
        description=f"**{row['title']}**",
        color=decision_color,
        timestamp=datetime.now(timezone.utc),
    )
    if status == SUGGESTION_STATUS_ACCEPTED:
        result_embed.add_field(
            name="Respuesta",
            value="La propuesta fue aceptada por el equipo que administra el paraíso.",
            inline=False,
        )
    else:
        result_embed.add_field(name="Razón del rechazo", value=rejection_reason.strip(), inline=False)
    result_embed.set_footer(text=f"Sugerencia #{suggestion_id} · {guild.name if guild else 'Servidor'}")

    dm_ok = False
    if requester is not None:
        try:
            await requester.send(embed=result_embed)
            dm_ok = True
        except discord.HTTPException:
            pass

    # Desactiva los botones de TODAS las copias que recibieron los revisores.
    review_rows = suggestion_review_messages(suggestion_id)
    final_embed = discord.Embed(
        title=f"{'✅ Aceptada' if status == SUGGESTION_STATUS_ACCEPTED else '❌ Rechazada'} — Sugerencia #{suggestion_id}",
        description=f"**{row['title']}**\n\n{row['content']}",
        color=decision_color,
        timestamp=datetime.now(timezone.utc),
    )
    final_embed.add_field(name="Resuelta por", value=interaction.user.mention, inline=False)
    if status == SUGGESTION_STATUS_REJECTED:
        final_embed.add_field(name="Razón", value=rejection_reason.strip(), inline=False)
    final_embed.set_footer(text="Esta sugerencia ya no admite otra decisión.")

    for review_row in review_rows:
        try:
            channel = bot.get_channel(int(review_row["channel_id"]))
            if channel is None:
                channel = await bot.fetch_channel(int(review_row["channel_id"]))
            message = await channel.fetch_message(int(review_row["message_id"]))
            await message.edit(embed=final_embed, view=None)
        except discord.HTTPException:
            pass

    if guild is not None:
        await log_embed(
            guild,
            f"{'✅ Sugerencia aceptada' if status == SUGGESTION_STATUS_ACCEPTED else '❌ Sugerencia rechazada'}",
            f"Sugerencia **#{suggestion_id}** de <@{row['user_id']}> — resuelta por {interaction.user.mention}. "
            + (f"Razón: {rejection_reason.strip()}" if status == SUGGESTION_STATUS_REJECTED else ""),
            decision_color,
        )

    dm_note = "DM enviado al autor." if dm_ok else "⚠️ No pude enviar el DM al autor (puede tener los DMs cerrados)."
    await _suggestion_interaction_reply(
        interaction,
        f"{'✅ Sugerencia aceptada.' if status == SUGGESTION_STATUS_ACCEPTED else '❌ Sugerencia rechazada.'} {dm_note}",
        ephemeral=True,
    )


async def _suggestion_interaction_reply(interaction: discord.Interaction, text: str, ephemeral: bool = True) -> None:
    if interaction.response.is_done():
        await interaction.followup.send(text, ephemeral=ephemeral)
    else:
        await interaction.response.send_message(text, ephemeral=ephemeral)


async def suggestion_publish_panel(guild: discord.Guild, channel: discord.TextChannel) -> discord.Message:
    message = await channel.send(embed=suggestion_panel_embed(guild), view=SuggestionPanelView())
    suggestion_set_channel_id(guild.id, channel.id)
    suggestion_set_panel_message_id(guild.id, message.id)
    try:
        await message.pin(reason="Panel sticky del sistema de sugerencias de El Heraldo")
    except discord.HTTPException:
        pass
    return message


async def suggestion_ensure_panel(guild: discord.Guild) -> None:
    channel_id = suggestion_get_channel_id(guild.id)
    if not channel_id:
        return
    channel = guild.get_channel(channel_id)
    if not isinstance(channel, discord.TextChannel):
        return
    panel_id = suggestion_get_panel_message_id(guild.id)
    if panel_id:
        try:
            message = await channel.fetch_message(panel_id)
            # Refresca el contenido/vista sin crear mensajes duplicados.
            await message.edit(embed=suggestion_panel_embed(guild), view=SuggestionPanelView())
            return
        except discord.NotFound:
            pass
        except discord.HTTPException:
            return
    await suggestion_publish_panel(guild, channel)


async def suggestion_panel_deleted(guild_id: int | None, message_id: int) -> None:
    if not guild_id:
        return
    if suggestion_get_panel_message_id(guild_id) != message_id:
        return
    guild = bot.get_guild(guild_id)
    if guild is None:
        return
    await asyncio.sleep(1)
    await suggestion_ensure_panel(guild)


async def suggestions_startup() -> None:
    suggestion_db_init()
    # Vista del panel: un solo custom_id, persistente tras reinicios.
    if not any(isinstance(v, SuggestionPanelView) for v in bot.persistent_views):
        bot.add_view(SuggestionPanelView())

    # Registra los botones de todas las sugerencias pendientes para que sobrevivan reinicios.
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    pending = conn.execute("SELECT id FROM suggestions WHERE status = 'pending'").fetchall()
    review_messages = conn.execute(
        "SELECT suggestion_id, channel_id, message_id FROM suggestion_review_messages"
    ).fetchall()
    conn.close()
    pending_ids = {int(row["id"]) for row in pending}
    for row in review_messages:
        sid = int(row["suggestion_id"])
        if sid in pending_ids:
            try:
                bot.add_view(SuggestionReviewView(sid), message_id=int(row["message_id"]))
            except Exception:
                traceback.print_exc()

    for guild in bot.guilds:
        try:
            await suggestion_ensure_panel(guild)
        except Exception:
            traceback.print_exc()


suggestions_group = discord.app_commands.Group(
    name="suggestions",
    description="Configurar y administrar el sistema de sugerencias.",
    guild_only=True,
    default_permissions=discord.Permissions(manage_guild=True),
)


@suggestions_group.command(name="panel", description="Publicar o reconstruir el panel sticky de sugerencias en un canal.")
@discord.app_commands.describe(canal="Canal donde quedará el botón para crear sugerencias")
@discord.app_commands.checks.has_permissions(manage_guild=True)
async def suggestions_panel(interaction: discord.Interaction, canal: discord.TextChannel) -> None:
    perms = canal.permissions_for(interaction.guild.me)
    missing = [
        name for name, ok in (
            ("Ver canal", perms.view_channel),
            ("Enviar mensajes", perms.send_messages),
            ("Insertar enlaces", perms.embed_links),
            ("Gestionar mensajes", perms.manage_messages),
        ) if not ok
    ]
    if missing:
        await interaction.response.send_message(
            f"❌ El Heraldo no tiene en {canal.mention}: **{', '.join(missing)}**.", ephemeral=True
        )
        return
    await interaction.response.defer(ephemeral=True)
    suggestion_set_channel_id(interaction.guild.id, canal.id)
    await suggestion_ensure_panel(interaction.guild)
    await interaction.followup.send(f"✅ Panel de sugerencias configurado en {canal.mention}.", ephemeral=True)


@suggestions_group.command(name="config", description="Elegir si el creador del servidor también recibe las sugerencias por DM.")
@discord.app_commands.describe(dueno="Sí = el dueño/creador recibe las sugerencias; No = solo destinatarios añadidos")
@discord.app_commands.checks.has_permissions(manage_guild=True)
async def suggestions_config(interaction: discord.Interaction, dueno: bool) -> None:
    suggestion_set_owner_enabled(interaction.guild.id, dueno)
    owner_text = "incluido" if dueno else "excluido"
    await interaction.response.send_message(
        f"✅ El dueño del servidor queda **{owner_text}** como destinatario de sugerencias.", ephemeral=True
    )


@suggestions_group.command(name="revisor_add", description="Añadir una persona que recibirá y podrá resolver sugerencias por DM.")
@discord.app_commands.describe(usuario="Persona que recibirá las sugerencias")
@discord.app_commands.checks.has_permissions(manage_guild=True)
async def suggestions_reviewer_add(interaction: discord.Interaction, usuario: discord.Member) -> None:
    if usuario.bot:
        await interaction.response.send_message("❌ No puedes añadir un bot como revisor.", ephemeral=True)
        return
    suggestion_add_reviewer(interaction.guild.id, usuario.id)
    await interaction.response.send_message(f"✅ {usuario.mention} recibirá las nuevas sugerencias por DM.", ephemeral=True)


@suggestions_group.command(name="revisor_remove", description="Quitar una persona de los destinatarios de sugerencias.")
@discord.app_commands.describe(usuario="Persona que dejará de recibir nuevas sugerencias")
@discord.app_commands.checks.has_permissions(manage_guild=True)
async def suggestions_reviewer_remove(interaction: discord.Interaction, usuario: discord.Member) -> None:
    removed = suggestion_remove_reviewer(interaction.guild.id, usuario.id)
    await interaction.response.send_message(
        "✅ Revisor eliminado." if removed else "ℹ️ Esa persona no estaba configurada como revisor.",
        ephemeral=True,
    )


@suggestions_group.command(name="lista", description="Ver el canal y las personas que reciben las sugerencias.")
@discord.app_commands.checks.has_permissions(manage_guild=True)
async def suggestions_list(interaction: discord.Interaction) -> None:
    guild = interaction.guild
    channel = guild.get_channel(suggestion_get_channel_id(guild.id))
    reviewers = []
    for user_id in suggestion_reviewer_ids(guild.id):
        member = guild.get_member(user_id)
        reviewers.append(member.mention if member else f"<@{user_id}>")
    owner = f"<@{guild.owner_id}>" if suggestion_owner_enabled(guild.id) and guild.owner_id else "Desactivado"
    text = (
        f"**Canal:** {channel.mention if channel else 'No configurado'}\n"
        f"**Dueño/creador:** {owner}\n"
        f"**Revisores adicionales:** " + (", ".join(reviewers) if reviewers else "Ninguno")
    )
    await interaction.response.send_message(text, ephemeral=True)


@suggestions_group.error
async def suggestions_group_error(interaction: discord.Interaction, error: discord.app_commands.AppCommandError) -> None:
    await verify_command_error(interaction, error)


bot.tree.add_command(suggestions_group)

# ---------------------------------------------------------------------------

if __name__ == "__main__":
    token = os.environ.get("DISCORD_TOKEN")
    if not token:
        raise RuntimeError(
            "Falta la variable de entorno DISCORD_TOKEN. Configúrala en Railway "
            "(Variables del servicio) antes de desplegar."
        )
    try:
        bot.run(token)
    except discord.PrivilegedIntentsRequired:
        if os.environ.get("MESSAGE_CONTENT_INTENT") != "1":
            raise
        # MESSAGE_CONTENT_INTENT=1 sin activar el intent en el portal: en vez de quedarse
        # sin conectar, el bot se reinicia sin él (el log del honeypot no mostrará el texto).
        print("⚠️ El intent Message Content no está activado en el portal de desarrolladores: "
              "reiniciando sin él. Actívalo en el portal o quita MESSAGE_CONTENT_INTENT.")
        os.environ["MESSAGE_CONTENT_INTENT"] = "0"
        os.execv(sys.executable, [sys.executable, *sys.argv])
