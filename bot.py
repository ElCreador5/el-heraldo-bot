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
   - /verify_setup (rol, timeout, acción, activar) y /verify_texts (mensaje del
     panel, texto del botón y mensaje tras verificarse) configuran todo sin redeploy.

6. COPIA DE SEGURIDAD DE LA PLANTILLA (/server_template_setup, /template_sync)
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
   - /liberar devuelve los roles guardados; /list condenados muestra motivo, origen, inicio y caducidad.
   - Las condenas tienen duración opcional, sobreviven reinicios y sobreviven a una salida/reentrada.
   - /honeypot release deja de existir para evitar dos motores de liberación distintos.
   - La reacción de condena solo la procesan moderadores/administradores y exige una razón en un formulario antes de aplicar la sanción.
   - Quien tenga una condena activa no puede usar el botón de verificación; al reiniciar, el Heraldo
     reconcilia el rol con la base de datos (libera o reaplica según corresponda).
   - Los cambios de rol del propio Heraldo no vuelven a disparar el proceso (guardia con periodo de gracia).
   - Aviso privado al condenado y anuncio opcional en el canal configurado con /condenar_setup.

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
   - /raid setup, /raid status, /raid start (manual), /raid end (con opción de liberar a los condenados).

10. VARIABLES (/variables)
   - Los textos personalizables aceptan {usuario}, {servidor}, {servericon}, {miembros}, {canal},
     {fecha}… (también ${nombre}), y búsquedas por nombre/ID: {#canal}, {@rol}, {emoji:nombre}.
   - No distinguen mayúsculas, tildes ni separadores. Lo desconocido se deja tal cual.
   - Se aplican al panel y DM de verificación, al mensaje tras verificarse y al aviso del honeypot.
     /list variables lista todas; /variables texto:… prueba un texto con datos reales.

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
   - /embed editar | enviar | borrar. /list embeds muestra los embeds guardados por nombre.
     Los mensajes ya enviados se actualizan solos al editarlos.
   - /list comandos | variables | condenados | embeds centraliza los listados privados del creador del servidor.

Toda la actividad relevante se reporta como embed en el canal de logs
(LOG_CHANNEL_ID por defecto; cambiable con /heraldo_log_channel).
Persistencia: SQLite (DB_PATH; en Railway, un Volume para sobrevivir deploys).
Permisos requeridos: Administrador (bot personal, confirmado por el usuario).
"""

import asyncio
import contextvars
import io
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
from discord import app_commands
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
CONDEMNED_CHANNEL_ID = 0  # configurable con /condenar_setup; 0 = sin canal de avisos
CONDEMNED_EMOJI = "☠️"
CONDEMNATION_MAX_MINUTES = 10 * 365 * 24 * 60
VERIFICATION_WINDOW = timedelta(minutes=10)

# --- Orientación / Reaction Roles ------------------------------------------
# El Heraldo NO crea, renombra ni elimina roles. El administrador selecciona
# entre 1 y 6 roles existentes; el emoji se obtiene automáticamente del propio rol.
ORIENTATION_MIN_ROLES = 1
ORIENTATION_MAX_ROLES = 6
# Definiciones antiguas conservadas únicamente para migrar instalaciones previas.
ORIENTATION_ROLE_DEFINITIONS = (
    ("orientation_rr_hetero", "Hetero", "🍑"),
    ("orientation_rr_curioso", "Curios@", "👀"),
    ("orientation_rr_gay", "Gay", "🥒"),
    ("orientation_rr_bisex", "Bisex", "🚻"),
)
ORIENTATION_EMBED_TITLE = "ORIENTACIÓN"
ORIENTATION_EMBED_COLOR = 0x19A7E0
ORIENTATION_EMBED_INTRO = "Selecciona el rol que te represente reaccionando con el emoji correspondiente:"
ORIENTATION_EMBED_DETAILS = (
    "Estos roles permiten definir tu orientación dentro del servidor. "
    "Si tu preferencia cambia, puedes seleccionar otra opción.\n\n"
    "**¿Cómo funciona?**\n"
    "Reacciona con el emoji correspondiente para recibir el rol asociado. "
    "Solo puedes mantener una orientación activa a la vez. Al elegir otra, "
    "la anterior será reemplazada.\n\n"
    "Esto certifica que eres una persona y tu participación en el servidor.\n"
    "Si se detecta que no posees un rol de estos serás expulsado por sospecha."
)

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
# /verify_setup y /verify_texts; estos son solo los valores por defecto.
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

# --- Copia de seguridad de la plantilla del servidor (/server_template_setup) ---
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
    """Reporta actividad de El Heraldo en el canal de logs como embed configurable.
    La plantilla visual se edita desde el Centro de Mensajes y nunca debe tumbar
    el flujo principal si falta configuración o permisos."""
    print(f"{title} — {description}")
    if guild is None:
        return
    channel = guild.get_channel(get_log_channel_id(guild.id))
    if channel is None:
        return
    try:
        embed = build_log_template_embed(guild, title, description, color)
        await channel.send(embed=embed)
    except discord.Forbidden:
        print("Sin permisos para escribir en el canal de logs")
    except Exception:
        traceback.print_exc()
        try:
            fallback = discord.Embed(
                title=title,
                description=description,
                color=color,
                timestamp=datetime.now(timezone.utc),
            )
            await channel.send(embed=fallback)
        except discord.HTTPException:
            pass


# ---------------------------------------------------------------------------
# Persistencia
# ---------------------------------------------------------------------------

def db_connect() -> sqlite3.Connection:
    """Conexión SQLite corta y segura para un bot asíncrono.

    Autocommit evita dejar transacciones de escritura abiertas si una función falla
    entre execute() y close(). WAL permite lectores mientras hay una escritura.
    """
    conn = sqlite3.connect(DB_PATH, timeout=2.0, isolation_level=None)
    conn.execute("PRAGMA busy_timeout = 2000")
    return conn


def db_init() -> None:
    conn = db_connect()
    try:
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA synchronous = NORMAL")
    except sqlite3.OperationalError:
        # Si un despliegue anterior aún está drenando, continúa; las siguientes
        # conexiones mantienen busy_timeout y el próximo arranque reintentará WAL.
        pass
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
        CREATE TABLE IF NOT EXISTS guild_members (
            guild_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            entry_invite TEXT,
            tentado_at TEXT,
            dm_sent INTEGER DEFAULT 0,
            verification_dm_sent INTEGER DEFAULT 0,
            sin_verificado_at TEXT,
            verify_pending_at TEXT,
            PRIMARY KEY (guild_id, user_id)
        )
        """
    )
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
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS guild_activity (
            guild_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            messages INTEGER NOT NULL DEFAULT 0,
            streak INTEGER NOT NULL DEFAULT 0,
            last_active_day TEXT,
            week_messages INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (guild_id, user_id)
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
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS guild_config (
            guild_id INTEGER PRIMARY KEY,
            initialized INTEGER NOT NULL DEFAULT 0,
            setup_version INTEGER NOT NULL DEFAULT 1,
            updated_at TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS guild_resources (
            guild_id INTEGER NOT NULL,
            resource_type TEXT NOT NULL,
            config_key TEXT NOT NULL,
            resource_id INTEGER NOT NULL,
            PRIMARY KEY (guild_id, resource_type, config_key),
            UNIQUE (guild_id, resource_type, resource_id)
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS guild_settings (
            guild_id INTEGER NOT NULL,
            key TEXT NOT NULL,
            value TEXT,
            PRIMARY KEY (guild_id, key)
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS moderation_reaction_reports (
            guild_id INTEGER NOT NULL,
            message_id INTEGER NOT NULL,
            target_id INTEGER NOT NULL,
            emoji_key TEXT NOT NULL,
            reporter_id INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            action_executed INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (guild_id, message_id, emoji_key, reporter_id)
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS moderation_cases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id INTEGER NOT NULL,
            case_number INTEGER NOT NULL,
            type TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            reason TEXT NOT NULL,
            duration_minutes INTEGER,
            created_at TEXT NOT NULL,
            expires_at TEXT,
            author_id INTEGER,
            proof TEXT,
            verified_proof TEXT,
            moderator_notes TEXT,
            message_history TEXT,
            open INTEGER NOT NULL DEFAULT 1,
            closed_at TEXT,
            closed_by INTEGER,
            resolution TEXT,
            UNIQUE (guild_id, case_number)
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS moderation_message_cache (
            guild_id INTEGER NOT NULL,
            channel_id INTEGER NOT NULL,
            message_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            content TEXT,
            attachments TEXT,
            created_at TEXT NOT NULL,
            PRIMARY KEY (guild_id, message_id)
        )
        """
    )

    conn.commit()
    conn.close()


def db_get(guild_id: int, user_id: int) -> sqlite3.Row | None:
    conn = db_connect()
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        "SELECT * FROM guild_members WHERE guild_id = ? AND user_id = ?", (guild_id, user_id)
    ).fetchone()
    conn.close()
    return row


def db_upsert_join(guild_id: int, user_id: int, invite_code: str | None) -> None:
    """Registra el estado del miembro de forma independiente en cada servidor."""
    row = db_get(guild_id, user_id)
    conn = db_connect()
    if row is None:
        conn.execute(
            "INSERT INTO guild_members (guild_id, user_id, entry_invite, dm_sent) VALUES (?, ?, ?, 0)",
            (guild_id, user_id, invite_code),
        )
    else:
        if row["entry_invite"] and invite_code == row["entry_invite"]:
            conn.execute(
                "UPDATE guild_members SET dm_sent = 0 WHERE guild_id = ? AND user_id = ?",
                (guild_id, user_id),
            )
        if row["entry_invite"] is None:
            conn.execute(
                "UPDATE guild_members SET entry_invite = ? WHERE guild_id = ? AND user_id = ?",
                (invite_code, guild_id, user_id),
            )
    conn.commit()
    conn.close()


def _db_member_set(guild_id: int, user_id: int, column: str, value) -> None:
    allowed = {"tentado_at", "dm_sent", "verification_dm_sent", "sin_verificado_at", "verify_pending_at"}
    if column not in allowed:
        raise ValueError("Columna de miembro no permitida")
    conn = db_connect()
    conn.execute(
        f"INSERT INTO guild_members (guild_id, user_id, {column}) VALUES (?, ?, ?) "
        f"ON CONFLICT(guild_id, user_id) DO UPDATE SET {column} = excluded.{column}",
        (guild_id, user_id, value),
    )
    conn.commit()
    conn.close()


def db_set_tentado(guild_id: int, user_id: int, when: datetime) -> None:
    _db_member_set(guild_id, user_id, "tentado_at", when.isoformat())


def db_mark_dm_sent(guild_id: int, user_id: int) -> None:
    _db_member_set(guild_id, user_id, "dm_sent", 1)


def db_verification_dm_sent(guild_id: int, user_id: int) -> bool:
    row = db_get(guild_id, user_id)
    return bool(row and row["verification_dm_sent"])


def db_mark_verification_dm_sent(guild_id: int, user_id: int) -> None:
    _db_member_set(guild_id, user_id, "verification_dm_sent", 1)


def db_clear_tentado(guild_id: int, user_id: int) -> None:
    _db_member_set(guild_id, user_id, "tentado_at", None)


def db_set_sin_verificado(guild_id: int, user_id: int, when: datetime) -> None:
    _db_member_set(guild_id, user_id, "sin_verificado_at", when.isoformat())


def db_clear_sin_verificado(guild_id: int, user_id: int) -> None:
    _db_member_set(guild_id, user_id, "sin_verificado_at", None)


def db_set_verify_pending(guild_id: int, user_id: int, when: datetime) -> None:
    _db_member_set(guild_id, user_id, "verify_pending_at", when.isoformat())


def db_clear_verify_pending(guild_id: int, user_id: int) -> None:
    _db_member_set(guild_id, user_id, "verify_pending_at", None)


def db_track_message(guild_id: int, user_id: int, today: str, yesterday: str) -> None:
    """Suma actividad de un miembro únicamente dentro de su servidor."""
    conn = db_connect()
    row = conn.execute(
        "SELECT messages, streak, last_active_day FROM guild_activity WHERE guild_id = ? AND user_id = ?",
        (guild_id, user_id),
    ).fetchone()
    if row is None:
        conn.execute(
            "INSERT INTO guild_activity (guild_id, user_id, messages, streak, last_active_day, week_messages) "
            "VALUES (?, ?, 1, 1, ?, 1)",
            (guild_id, user_id, today),
        )
    else:
        messages, streak, last_active = row
        if last_active != today:
            streak = streak + 1 if last_active == yesterday else 1
            last_active = today
        conn.execute(
            "UPDATE guild_activity SET messages = ?, streak = ?, last_active_day = ?, "
            "week_messages = week_messages + 1 WHERE guild_id = ? AND user_id = ?",
            (messages + 1, streak, last_active, guild_id, user_id),
        )
    conn.commit()
    conn.close()


def db_get_activity(guild_id: int, user_id: int) -> tuple[int, int, str | None]:
    conn = db_connect()
    row = conn.execute(
        "SELECT messages, streak, last_active_day FROM guild_activity WHERE guild_id = ? AND user_id = ?",
        (guild_id, user_id),
    ).fetchone()
    conn.close()
    return (row[0], row[1], row[2]) if row else (0, 0, None)


def db_week_ranking(guild_id: int) -> list[tuple[int, int]]:
    conn = db_connect()
    rows = conn.execute(
        "SELECT user_id, week_messages FROM guild_activity "
        "WHERE guild_id = ? AND week_messages > 0 ORDER BY week_messages DESC, user_id ASC",
        (guild_id,),
    ).fetchall()
    conn.close()
    return [(r[0], r[1]) for r in rows]


def db_zero_week_messages(guild_id: int, user_id: int) -> None:
    conn = db_connect()
    conn.execute(
        "UPDATE guild_activity SET week_messages = 0 WHERE guild_id = ? AND user_id = ?",
        (guild_id, user_id),
    )
    conn.commit()
    conn.close()


def db_reset_week(guild_id: int) -> None:
    conn = db_connect()
    conn.execute("UPDATE guild_activity SET week_messages = 0 WHERE guild_id = ?", (guild_id,))
    conn.commit()
    conn.close()


def guild_config_get(guild_id: int, key: str) -> str | None:
    conn = db_connect()
    row = conn.execute(
        "SELECT value FROM guild_settings WHERE guild_id = ? AND key = ?",
        (guild_id, key),
    ).fetchone()
    conn.close()
    return row[0] if row else None


def guild_config_set(guild_id: int, key: str, value: str) -> None:
    conn = db_connect()
    try:
        conn.execute(
            """
            INSERT INTO guild_settings (guild_id, key, value)
            VALUES (?, ?, ?)
            ON CONFLICT(guild_id, key) DO UPDATE SET value = excluded.value
            """,
            (guild_id, key, value),
        )
        conn.execute(
            "UPDATE guild_config SET updated_at = ? WHERE guild_id = ?",
            (datetime.now(timezone.utc).isoformat(), guild_id),
        )
    finally:
        conn.close()


def guild_resource_get(guild_id: int, resource_type: str, config_key: str) -> int | None:
    conn = db_connect()
    row = conn.execute(
        "SELECT resource_id FROM guild_resources WHERE guild_id = ? AND resource_type = ? AND config_key = ?",
        (guild_id, resource_type, config_key),
    ).fetchone()
    conn.close()
    return int(row[0]) if row else None


def guild_resource_set(guild_id: int, resource_type: str, config_key: str, resource_id: int) -> None:
    conn = db_connect()
    conn.execute(
        """
        INSERT INTO guild_resources (guild_id, resource_type, config_key, resource_id)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(guild_id, resource_type, config_key)
        DO UPDATE SET resource_id = excluded.resource_id
        """,
        (guild_id, resource_type, config_key, resource_id),
    )
    conn.commit()
    conn.close()


def guild_is_initialized(guild_id: int) -> bool:
    conn = db_connect()
    row = conn.execute(
        "SELECT initialized FROM guild_config WHERE guild_id = ?",
        (guild_id,),
    ).fetchone()
    conn.close()
    return bool(row and row[0])


def guild_mark_initialized(guild_id: int) -> None:
    conn = db_connect()
    conn.execute(
        """
        INSERT INTO guild_config (guild_id, initialized, setup_version, updated_at)
        VALUES (?, 1, 1, ?)
        ON CONFLICT(guild_id) DO UPDATE SET initialized = 1, updated_at = excluded.updated_at
        """,
        (guild_id, datetime.now(timezone.utc).isoformat()),
    )
    conn.commit()
    conn.close()


def db_meta_get(key: str) -> str | None:
    conn = db_connect()
    row = conn.execute("SELECT value FROM meta WHERE key = ?", (key,)).fetchone()
    conn.close()
    return row[0] if row else None


def db_meta_set(key: str, value: str) -> None:
    conn = db_connect()
    conn.execute(
        "INSERT INTO meta (key, value) VALUES (?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        (key, value),
    )
    conn.commit()
    conn.close()


def legacy_fallback_allowed(guild_id: int | None) -> bool:
    if guild_id is None:
        return True
    legacy_owner = db_meta_get("verify_legacy_guild_id")
    if legacy_owner is not None:
        try:
            return int(legacy_owner) == guild_id
        except (TypeError, ValueError):
            return False
    return len(bot.guilds) <= 1


def _guild_or_legacy_setting(guild_id: int | None, key: str, default: str) -> str:
    """Lee primero la configuración por servidor. La configuración global antigua
    solo se acepta si pertenece a este servidor o si el bot aún está en un único servidor."""
    if guild_id is None:
        return db_meta_get(key) or default
    configured = guild_config_get(guild_id, key)
    if configured is not None:
        return configured
    if not legacy_fallback_allowed(guild_id):
        return default
    return db_meta_get(key) or default


def get_motw_weekday(guild_id: int) -> int:
    value = guild_config_get(guild_id, "motw_weekday")
    if value is None and legacy_fallback_allowed(guild_id):
        value = db_meta_get("motw_weekday")
    return int(value) if value is not None else MOTW_WEEKDAY_DEFAULT


def get_motw_hour(guild_id: int) -> int:
    value = guild_config_get(guild_id, "motw_hour")
    if value is None and legacy_fallback_allowed(guild_id):
        value = db_meta_get("motw_hour")
    return int(value) if value is not None else MOTW_HOUR_DEFAULT


def get_motw_channel_id(guild_id: int) -> int:
    value = guild_config_get(guild_id, "motw_channel_id")
    if value is not None:
        return int(value)
    if legacy_fallback_allowed(guild_id):
        legacy = db_meta_get("motw_channel_id")
        if legacy:
            return int(legacy)
        if len(bot.guilds) <= 1:
            return MOTW_CHANNEL_ID
    return 0


def set_motw_channel_id(guild_id: int, channel_id: int) -> None:
    guild_config_set(guild_id, "motw_channel_id", str(channel_id))


def set_motw_schedule(guild_id: int, weekday: int, hour: int) -> None:
    guild_config_set(guild_id, "motw_weekday", str(weekday))
    guild_config_set(guild_id, "motw_hour", str(hour))


def get_guild_role_id(guild_id: int, key: str, fallback: int = 0) -> int:
    value = guild_resource_get(guild_id, "role", key)
    return value if value is not None else fallback


def get_guild_channel_id(guild_id: int, key: str, fallback: int = 0) -> int:
    value = guild_resource_get(guild_id, "channel", key)
    return value if value is not None else fallback


def guild_setting_int(guild_id: int, key: str, fallback: int) -> int:
    value = guild_config_get(guild_id, key)
    try:
        return int(value) if value is not None else fallback
    except (TypeError, ValueError):
        return fallback


def get_sin_verificado_role_id(guild_id: int) -> int:
    return get_guild_role_id(guild_id, "sin_verificar")

JOIN_ROLES_MAX = 25


def _joinroles_load_id_list(guild_id: int, key: str) -> list[int]:
    raw = guild_config_get(guild_id, key)
    if not raw:
        return []
    try:
        values = json.loads(raw)
        result: list[int] = []
        for value in values:
            role_id = int(value)
            if role_id > 0 and role_id not in result:
                result.append(role_id)
        return result[:JOIN_ROLES_MAX]
    except (TypeError, ValueError, json.JSONDecodeError):
        return []


def _joinroles_save_id_list(guild_id: int, key: str, role_ids: list[int]) -> None:
    unique: list[int] = []
    for role_id in role_ids:
        role_id = int(role_id)
        if role_id > 0 and role_id not in unique:
            unique.append(role_id)
    guild_config_set(guild_id, key, json.dumps(unique[:JOIN_ROLES_MAX]))


def get_join_role_ids(guild_id: int) -> list[int]:
    raw = guild_config_get(guild_id, "join_role_ids")
    if raw is None:
        # Migración suave: el antiguo rol Sin Verificar pasa a ser el primer
        # Join Role sin que el administrador tenga que configurarlo de nuevo.
        legacy_role = get_guild_role_id(guild_id, "sin_verificar")
        return [legacy_role] if legacy_role else []
    return _joinroles_load_id_list(guild_id, "join_role_ids")


def set_join_role_ids(guild_id: int, role_ids: list[int]) -> None:
    _joinroles_save_id_list(guild_id, "join_role_ids", role_ids)


def get_join_bot_role_ids(guild_id: int) -> list[int]:
    return _joinroles_load_id_list(guild_id, "join_bot_role_ids")


def set_join_bot_role_ids(guild_id: int, role_ids: list[int]) -> None:
    _joinroles_save_id_list(guild_id, "join_bot_role_ids", role_ids)


def get_join_sync_excluded_role_ids(guild_id: int) -> list[int]:
    return _joinroles_load_id_list(guild_id, "join_sync_excluded_role_ids")


def set_join_sync_excluded_role_ids(guild_id: int, role_ids: list[int]) -> None:
    _joinroles_save_id_list(guild_id, "join_sync_excluded_role_ids", role_ids)


def get_join_roles_delay(guild_id: int) -> int:
    return max(0, guild_setting_int(guild_id, "join_roles_delay_seconds", 0))


def join_roles_wait_screening(guild_id: int) -> bool:
    return guild_config_get(guild_id, "join_roles_wait_screening") == "1"


def join_roles_enabled(guild_id: int) -> bool:
    value = guild_config_get(guild_id, "join_roles_enabled")
    if value is None:
        return bool(get_join_role_ids(guild_id))
    return value == "1"


def join_roles_bot_enabled(guild_id: int) -> bool:
    return guild_config_get(guild_id, "join_roles_bot_enabled") == "1"


def join_roles_bot_use_different(guild_id: int) -> bool:
    return guild_config_get(guild_id, "join_roles_bot_use_different") == "1"


def join_roles_bot_apply_delay(guild_id: int) -> bool:
    return guild_config_get(guild_id, "join_roles_bot_apply_delay") == "1"


def join_roles_remove_specific_after_join(guild_id: int) -> bool:
    return guild_config_get(guild_id, "join_roles_specific_remove_after_join") == "1"


def get_join_sync_interval_minutes(guild_id: int) -> int:
    return max(0, guild_setting_int(guild_id, "join_sync_interval_minutes", 0))


def get_join_sync_last(guild_id: int) -> datetime | None:
    raw = guild_config_get(guild_id, "join_sync_last")
    if not raw:
        return None
    try:
        dt = datetime.fromisoformat(raw)
        return dt if dt.tzinfo is not None else dt.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def set_join_sync_last(guild_id: int, when: datetime | None = None) -> None:
    guild_config_set(
        guild_id,
        "join_sync_last",
        (when or datetime.now(timezone.utc)).astimezone(timezone.utc).isoformat(),
    )


def get_join_specific_roles(guild_id: int) -> dict[int, list[int]]:
    raw = guild_config_get(guild_id, "join_specific_roles")
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
        result: dict[int, list[int]] = {}
        for user_id_raw, role_ids_raw in parsed.items():
            user_id = int(user_id_raw)
            roles: list[int] = []
            for role_id_raw in role_ids_raw:
                role_id = int(role_id_raw)
                if role_id > 0 and role_id not in roles:
                    roles.append(role_id)
            if user_id > 0 and roles:
                result[user_id] = roles[:JOIN_ROLES_MAX]
        return result
    except (TypeError, ValueError, json.JSONDecodeError):
        return {}


def set_join_specific_roles(guild_id: int, mapping: dict[int, list[int]]) -> None:
    serializable = {
        str(int(user_id)): [int(role_id) for role_id in role_ids[:JOIN_ROLES_MAX]]
        for user_id, role_ids in mapping.items()
        if int(user_id) > 0 and role_ids
    }
    guild_config_set(guild_id, "join_specific_roles", json.dumps(serializable))


def set_join_specific_user_roles(guild_id: int, user_id: int, role_ids: list[int]) -> None:
    mapping = get_join_specific_roles(guild_id)
    clean: list[int] = []
    for role_id in role_ids:
        role_id = int(role_id)
        if role_id > 0 and role_id not in clean:
            clean.append(role_id)
    if clean:
        mapping[int(user_id)] = clean[:JOIN_ROLES_MAX]
    else:
        mapping.pop(int(user_id), None)
    set_join_specific_roles(guild_id, mapping)


def remove_join_specific_user(guild_id: int, user_id: int) -> bool:
    mapping = get_join_specific_roles(guild_id)
    existed = int(user_id) in mapping
    mapping.pop(int(user_id), None)
    set_join_specific_roles(guild_id, mapping)
    return existed


def _join_role_status(guild: discord.Guild, role_id: int) -> tuple[discord.Role | None, str | None]:
    role = guild.get_role(int(role_id))
    if role is None:
        return None, "rol eliminado"
    me = guild.me
    if role.managed:
        return role, "rol administrado por Discord/integración"
    if me is None or role >= me.top_role:
        return role, "El Heraldo debe estar por encima de este rol"
    return role, None


def _join_roles_render(guild: discord.Guild, role_ids: list[int]) -> str:
    if not role_ids:
        return "**Ninguno**"
    parts: list[str] = []
    for role_id in role_ids:
        role, issue = _join_role_status(guild, role_id)
        if role is None:
            parts.append(f"⚠️ Rol eliminado (\`{role_id}\`)")
        elif issue:
            parts.append(f"⚠️ {role.mention} — {issue}")
        else:
            parts.append(role.mention)
    return ", ".join(parts)


def join_roles_basic_summary(guild: discord.Guild) -> str:
    return (
        "### Basic setup\n"
        f"Estado: **{'Activo' if join_roles_enabled(guild.id) else 'Desactivado'}**\n"
        f"Roles: {_join_roles_render(guild, get_join_role_ids(guild.id))}\n\n"
        "### Additional Options\n"
        f"Rules Screening: **{'Esperar' if join_roles_wait_screening(guild.id) else 'No esperar'}**\n"
        f"Delay: **{get_join_roles_delay(guild.id)} s**\n\n"
        "Los roles configurados se asignan a cada usuario nuevo. Los avisos ⚠️ indican "
        "problemas de jerarquía, roles eliminados o roles que Discord no permite asignar."
    )


def join_roles_users_summary(guild: discord.Guild) -> str:
    mapping = get_join_specific_roles(guild.id)
    lines: list[str] = []
    for user_id, role_ids in list(mapping.items())[:15]:
        lines.append(f"<@{user_id}> (\`{user_id}\`) → {_join_roles_render(guild, role_ids)}")
    if len(mapping) > 15:
        lines.append(f"… y **{len(mapping) - 15}** usuario(s) más.")
    return (
        "### User specific roles\n"
        + ("\n".join(lines) if lines else "**No hay usuarios configurados.**")
        + "\n\n"
        f"Remove user from list after join: **{'Sí' if join_roles_remove_specific_after_join(guild.id) else 'No'}**\n\n"
        "Estos roles se añaden **además** de los Join Roles generales cuando ese ID vuelve a entrar."
    )


def join_roles_bots_summary(guild: discord.Guild) -> str:
    use_different = join_roles_bot_use_different(guild.id)
    effective_ids = get_join_bot_role_ids(guild.id) if use_different else get_join_role_ids(guild.id)
    return (
        "### Bot roles\n"
        f"Assign Join Roles for bots: **{'Sí' if join_roles_bot_enabled(guild.id) else 'No'}**\n"
        f"Apply assignment delay for bots: **{'Sí' if join_roles_bot_apply_delay(guild.id) else 'No'}**\n"
        f"Use different roles for bots: **{'Sí' if use_different else 'No'}**\n"
        f"Roles efectivos: {_join_roles_render(guild, effective_ids)}"
    )


def _join_verify_pending_ids(guild_id: int) -> set[int]:
    conn = db_connect()
    try:
        rows = conn.execute(
            "SELECT user_id FROM guild_members WHERE guild_id = ? AND verify_pending_at IS NOT NULL",
            (guild_id,),
        ).fetchall()
        return {int(row[0]) for row in rows}
    finally:
        conn.close()


def _join_member_sync_excluded(member: discord.Member) -> bool:
    excluded = set(get_join_sync_excluded_role_ids(member.guild.id))
    return bool(excluded.intersection(role.id for role in member.roles))


def _join_member_required_general_roles(
    member: discord.Member,
    *,
    synchronization: bool,
    pending_ids: set[int] | None = None,
) -> list[discord.Role]:
    guild = member.guild
    verify_role_id = get_verify_role_id(guild.id)
    already_verified = bool(verify_role_id and verify_role_id in {role.id for role in member.roles})
    sin_role_id = get_sin_verificado_role_id(guild.id)
    if synchronization:
        if pending_ids is None:
            verification_pending = member.id in _join_verify_pending_ids(guild.id)
        else:
            verification_pending = member.id in pending_ids
    else:
        verification_pending = False

    roles: list[discord.Role] = []
    for role_id in get_join_role_ids(guild.id):
        role = guild.get_role(role_id)
        if role is None:
            continue
        if already_verified and role.id == sin_role_id:
            continue
        if synchronization and role.id == sin_role_id and not verification_pending:
            continue
        roles.append(role)
    return roles


async def _joinroles_add_roles(
    member: discord.Member,
    role_ids: list[int],
    *,
    reason: str,
) -> tuple[bool, int, str]:
    roles_to_add: list[discord.Role] = []
    for role_id in role_ids:
        role, issue = _join_role_status(member.guild, role_id)
        if role is None:
            continue
        if issue:
            return False, 0, f"{role.mention}: {issue}."
        if role not in member.roles:
            roles_to_add.append(role)

    if not roles_to_add:
        return True, 0, "No había roles pendientes."
    try:
        await member.add_roles(*roles_to_add, reason=reason)
        return True, len(roles_to_add), f"Asignados {len(roles_to_add)} rol(es)."
    except discord.HTTPException as exc:
        return False, 0, f"Discord rechazó la asignación: {exc}."


async def _assign_join_roles_now(
    member: discord.Member,
    *,
    synchronization: bool = False,
    pending_ids: set[int] | None = None,
) -> tuple[bool, str]:
    if member.bot or not join_roles_enabled(member.guild.id):
        return True, "No aplica."
    if synchronization and _join_member_sync_excluded(member):
        return True, "Excluido de sincronización."

    role_ids = [
        role.id
        for role in _join_member_required_general_roles(
            member,
            synchronization=synchronization,
            pending_ids=pending_ids,
        )
    ]
    ok, count, note = await _joinroles_add_roles(
        member,
        role_ids,
        reason="El Heraldo · Join Roles" + (" · sincronización" if synchronization else ""),
    )
    if ok and count:
        return True, f"Asignados {count} Join Role(s)."
    return ok, note


async def assign_user_specific_roles(member: discord.Member) -> tuple[bool, str]:
    if member.bot:
        return True, "No aplica."
    mapping = get_join_specific_roles(member.guild.id)
    role_ids = mapping.get(member.id, [])
    if not role_ids:
        return True, "Sin roles específicos."

    ok, count, note = await _joinroles_add_roles(
        member,
        role_ids,
        reason="El Heraldo · User specific Join Roles",
    )
    if ok and join_roles_remove_specific_after_join(member.guild.id):
        remove_join_specific_user(member.guild.id, member.id)
    if ok and count:
        return True, f"Asignados {count} rol(es) específicos."
    return ok, note


async def assign_join_roles(member: discord.Member) -> tuple[bool, str]:
    if member.bot:
        return True, "No aplica."

    has_general = join_roles_enabled(member.guild.id) and bool(get_join_role_ids(member.guild.id))
    has_specific = member.id in get_join_specific_roles(member.guild.id)
    if not has_general and not has_specific:
        return True, "No aplica."

    if join_roles_wait_screening(member.guild.id) and getattr(member, "pending", False):
        return True, "Esperando Rules Screening."

    delay = get_join_roles_delay(member.guild.id)
    if delay > 0:
        await asyncio.sleep(delay)
        refreshed = member.guild.get_member(member.id)
        if refreshed is None:
            return True, "El miembro ya no está en el servidor."
        member = refreshed
        if join_roles_wait_screening(member.guild.id) and getattr(member, "pending", False):
            return True, "Esperando Rules Screening."

    if has_general:
        ok, note = await _assign_join_roles_now(member)
    else:
        ok, note = True, "Sin Join Roles generales."
    specific_ok, specific_note = await assign_user_specific_roles(member)
    if not ok:
        return False, note
    if not specific_ok:
        return False, specific_note
    return True, f"{note} {specific_note}".strip()


async def assign_bot_join_roles(member: discord.Member) -> tuple[bool, str]:
    if not member.bot or not join_roles_bot_enabled(member.guild.id):
        return True, "No aplica."

    if join_roles_bot_apply_delay(member.guild.id):
        delay = get_join_roles_delay(member.guild.id)
        if delay > 0:
            await asyncio.sleep(delay)
            refreshed = member.guild.get_member(member.id)
            if refreshed is None:
                return True, "El bot ya no está en el servidor."
            member = refreshed

    role_ids = (
        get_join_bot_role_ids(member.guild.id)
        if join_roles_bot_use_different(member.guild.id)
        else get_join_role_ids(member.guild.id)
    )
    ok, count, note = await _joinroles_add_roles(
        member,
        role_ids,
        reason="El Heraldo · Bot Join Roles",
    )
    if ok and count:
        return True, f"Asignados {count} Bot Join Role(s)."
    return ok, note


def approximate_missing_join_roles(guild: discord.Guild) -> int:
    missing = 0
    pending_ids = _join_verify_pending_ids(guild.id)
    for member in guild.members:
        if member.bot or _join_member_sync_excluded(member):
            continue
        required = _join_member_required_general_roles(
            member,
            synchronization=True,
            pending_ids=pending_ids,
        )
        member_ids = {role.id for role in member.roles}
        if any(role.id not in member_ids for role in required):
            missing += 1
    return missing


async def sync_join_roles(guild: discord.Guild) -> tuple[int, int, list[str]]:
    assigned = 0
    skipped = 0
    errors: list[str] = []
    pending_ids = _join_verify_pending_ids(guild.id)

    async for member in guild.fetch_members(limit=None):
        if member.bot:
            continue
        ok, note = await _assign_join_roles_now(
            member,
            synchronization=True,
            pending_ids=pending_ids,
        )
        if ok:
            if note.startswith("Asignados"):
                assigned += 1
            else:
                skipped += 1
        else:
            errors.append(f"{member}: {note}")
        await asyncio.sleep(0.15)

    set_join_sync_last(guild.id)
    return assigned, skipped, errors


def join_roles_sync_summary(guild: discord.Guild) -> str:
    last = get_join_sync_last(guild.id)
    interval = get_join_sync_interval_minutes(guild.id)
    excluded = get_join_sync_excluded_role_ids(guild.id)
    last_text = discord.utils.format_dt(last, "R") if last else "**Nunca**"
    return (
        "### Synchronization\n"
        f"Approx. missing Join Roles: **{approximate_missing_join_roles(guild)}**\n"
        f"Last synchronization: {last_text}\n"
        f"Exclude roles from sync: {_join_roles_render(guild, excluded)}\n"
        f"Schedule regular sync: **{f'cada {interval} min' if interval else 'Desactivado'}**\n\n"
        "Sync now asigna los Join Roles generales configurados a todos los usuarios elegibles. "
        "Los miembros que tengan cualquiera de los roles excluidos permanecen sin cambios."
    )


def join_roles_summary(guild: discord.Guild) -> str:
    return (
        "El módulo replica la estructura funcional de Join Roles: configuración general, "
        "roles específicos por usuario, roles para bots y sincronización.\n\n"
        f"**Join Roles generales:** {len(get_join_role_ids(guild.id))}\n"
        f"**Usuarios específicos:** {len(get_join_specific_roles(guild.id))}\n"
        f"**Bot roles:** {'Activo' if join_roles_bot_enabled(guild.id) else 'Desactivado'}\n"
        f"**Sync periódico:** {'Activo' if get_join_sync_interval_minutes(guild.id) else 'Desactivado'}"
    )



@tasks.loop(minutes=10)
async def join_roles_sync_loop() -> None:
    """Ejecuta los Sync periódicos configurados por servidor."""
    now = datetime.now(timezone.utc)
    for guild in bot.guilds:
        try:
            interval = get_join_sync_interval_minutes(guild.id)
            if interval <= 0 or not join_roles_enabled(guild.id):
                continue
            last = get_join_sync_last(guild.id)
            if last is not None and now < last + timedelta(minutes=interval):
                continue
            assigned, skipped, errors = await sync_join_roles(guild)
            await log_embed(
                guild,
                "🔄 Join Roles · sincronización periódica",
                f"Asignados a **{assigned}** miembro(s); **{skipped}** sin cambios."
                + (f" **{len(errors)}** error(es)." if errors else ""),
                discord.Color.blurple() if not errors else discord.Color.orange(),
            )
        except Exception:
            traceback.print_exc()


def get_sin_verificado_window(guild_id: int) -> timedelta:
    seconds = guild_setting_int(guild_id, "sin_verificado_timeout_seconds", int(SIN_VERIFICAR_WINDOW.total_seconds()))
    return timedelta(seconds=max(1, seconds))


def get_orientation_window(guild_id: int) -> timedelta:
    seconds = guild_setting_int(guild_id, "orientation_timeout_seconds", int(VERIFICATION_WINDOW.total_seconds()))
    return timedelta(seconds=max(1, seconds))


def get_tentado_role_id(guild_id: int) -> int:
    return get_guild_role_id(guild_id, "tentado")


def get_condenado_role_id(guild_id: int) -> int:
    return get_guild_role_id(guild_id, "condenado")


def get_eval_role_ids(guild_id: int) -> set[int]:
    """Roles seleccionados que satisfacen la verificación de orientación."""
    return {int(item["role_id"]) for item in get_orientation_bindings(guild_id)}


def orientation_enabled(guild_id: int) -> bool:
    return guild_config_get(guild_id, "orientation_enabled") == "1"


def get_orientation_channel_id(guild_id: int) -> int:
    return guild_setting_int(guild_id, "orientation_channel_id", 0)


def get_orientation_message_id(guild_id: int) -> int:
    return guild_setting_int(guild_id, "orientation_message_id", 0)


def get_orientation_message_channel_id(guild_id: int) -> int:
    return guild_setting_int(guild_id, "orientation_message_channel_id", 0)


def _orientation_emoji_key(value: str) -> str:
    return value.replace("\ufe0f", "").strip()


def _orientation_role_emoji(role: discord.Role) -> str | None:
    """Obtiene el emoji del propio rol: icono Unicode del rol o emoji en su nombre."""
    role_unicode = getattr(role, "unicode_emoji", None)
    if role_unicode:
        return str(role_unicode).strip()

    name = role.name
    # Banderas (dos indicadores regionales).
    flag_matches = re.findall(r"[\U0001F1E6-\U0001F1FF]{2}", name)
    if flag_matches:
        return flag_matches[-1]

    # Emojis Unicode comunes, incluyendo VS16, modificador de piel y secuencias ZWJ.
    emoji_pattern = re.compile(
        r"(?:"
        r"[\U0001F300-\U0001FAFF]"
        r"|[\u2600-\u27BF]"
        r")"
        r"(?:\uFE0F|\uFE0E)?"
        r"(?:[\U0001F3FB-\U0001F3FF])?"
        r"(?:\u200D(?:[\U0001F300-\U0001FAFF]|[\u2600-\u27BF])"
        r"(?:\uFE0F|\uFE0E)?(?:[\U0001F3FB-\U0001F3FF])?)*"
    )
    matches = emoji_pattern.findall(name)
    return matches[-1] if matches else None


def get_orientation_bindings(guild_id: int) -> list[dict[str, object]]:
    raw = guild_config_get(guild_id, "orientation_role_bindings")
    if raw is not None:
        try:
            parsed = json.loads(raw)
            result: list[dict[str, object]] = []
            for item in parsed:
                role_id = int(item.get("role_id", 0))
                emoji = str(item.get("emoji", "")).strip()
                if role_id and emoji:
                    result.append({"role_id": role_id, "emoji": emoji})
            return result[:ORIENTATION_MAX_ROLES]
        except (TypeError, ValueError, json.JSONDecodeError):
            return []

    # Migración suave desde la versión anterior: conserva los cuatro enlaces
    # existentes como selección inicial, sin volver a administrar esos roles.
    # Los enlaces antiguos se migran con el emoji histórico solo hasta que el
    # administrador vuelva a seleccionar los roles desde el nuevo panel.
    migrated: list[dict[str, object]] = []
    for key, _label, emoji in ORIENTATION_ROLE_DEFINITIONS:
        role_id = guild_resource_get(guild_id, "role", key)
        if role_id:
            migrated.append({"role_id": int(role_id), "emoji": emoji})
    return migrated[:ORIENTATION_MAX_ROLES]


def set_orientation_bindings(guild_id: int, bindings: list[dict[str, object]]) -> None:
    clean = [
        {"role_id": int(item["role_id"]), "emoji": str(item["emoji"]).strip()}
        for item in bindings[:ORIENTATION_MAX_ROLES]
        if int(item.get("role_id", 0)) and str(item.get("emoji", "")).strip()
    ]
    guild_config_set(guild_id, "orientation_role_bindings", json.dumps(clean, ensure_ascii=False))


def orientation_role_for_emoji(guild: discord.Guild, emoji: str) -> discord.Role | None:
    normalized = _orientation_emoji_key(emoji)
    for binding in get_orientation_bindings(guild.id):
        if _orientation_emoji_key(str(binding["emoji"])) == normalized:
            return guild.get_role(int(binding["role_id"]))
    return None


def get_orientation_embed_title(guild_id: int) -> str:
    return guild_config_get(guild_id, "orientation_embed_title") or ORIENTATION_EMBED_TITLE


def get_orientation_embed_intro(guild_id: int) -> str:
    return guild_config_get(guild_id, "orientation_embed_intro") or ORIENTATION_EMBED_INTRO


def get_orientation_embed_details(guild_id: int) -> str:
    return guild_config_get(guild_id, "orientation_embed_details") or ORIENTATION_EMBED_DETAILS


def get_orientation_embed_color(guild_id: int) -> int:
    raw = (guild_config_get(guild_id, "orientation_embed_color") or f"{ORIENTATION_EMBED_COLOR:06X}").lstrip("#")
    try:
        return int(raw, 16)
    except ValueError:
        return ORIENTATION_EMBED_COLOR


def get_orientation_embed_footer(guild: discord.Guild) -> str:
    configured = guild_config_get(guild.id, "orientation_embed_footer")
    return configured if configured is not None else f"{guild.name} {datetime.now(STREAK_TZ).year} ©"


def build_orientation_embed(guild: discord.Guild) -> discord.Embed:
    option_lines = []
    for binding in get_orientation_bindings(guild.id):
        role = guild.get_role(int(binding["role_id"]))
        if role is not None:
            option_lines.append(f"{binding['emoji']}  {role.mention}")

    description = get_orientation_embed_intro(guild.id).strip()
    if option_lines:
        description += "\n\n" + "\n".join(option_lines)
    description += "\n\n" + get_orientation_embed_details(guild.id).strip()

    embed = discord.Embed(
        title=get_orientation_embed_title(guild.id),
        description=description,
        color=discord.Color(get_orientation_embed_color(guild.id)),
    )
    footer_text = get_orientation_embed_footer(guild)
    if footer_text:
        if guild.icon:
            embed.set_footer(text=footer_text, icon_url=guild.icon.url)
        else:
            embed.set_footer(text=footer_text)
    return embed


def orientation_setup_summary(guild: discord.Guild) -> str:
    enabled = orientation_enabled(guild.id)
    channel = guild.get_channel(get_orientation_channel_id(guild.id))
    roles = []
    for binding in get_orientation_bindings(guild.id):
        role = guild.get_role(int(binding["role_id"]))
        emoji = str(binding["emoji"])
        roles.append(f"{emoji} {role.mention if role else '**Rol eliminado**'}")

    role_text = "\n".join(roles) if roles else "**No hay roles seleccionados.**"
    return (
        f"Estado: **{'Activo' if enabled else 'Desactivado'}**\n"
        f"Canal: {channel.mention if isinstance(channel, discord.TextChannel) else '**No configurado**'}\n"
        f"Tarjeta administrada: **{'Sí' if enabled else 'No'}**\n"
        f"Roles vinculados: **{len(roles)}/{ORIENTATION_MAX_ROLES}**\n\n"
        + role_text
        + "\n\n**Cómo funciona:** El Heraldo establece un sistema para la selección de roles "
          "obligatorios usando **roles que ya existen en tu servidor**. Puedes seleccionar de **1 a 6** "
          "roles; El Heraldo toma automáticamente el emoji incluido en cada rol. No crea, renombra ni elimina esos roles. "
          "Estos roles complementan la verificación, ayudan a garantizar participación dentro del servidor "
          "y sirven como una señal adicional de que el miembro es humano.\n\n"
          "• Después de verificar su edad, el miembro debe seleccionar uno de los roles configurados "
          "antes de que venza el temporizador de **10 minutos**.\n"
          "• Si no selecciona ninguno dentro del plazo, El Heraldo lo expulsa y envía una invitación "
          "de recuperación de **un solo uso** para darle una oportunidad de volver a ingresar.\n"
          "• Los permisos de los roles siguen siendo completamente tuyos y pueden personalizar la vista del servidor."
    )


async def ensure_orientation_system(guild: discord.Guild) -> tuple[bool, str]:
    """Sincroniza la tarjeta y reacciones usando roles existentes seleccionados."""
    if not orientation_enabled(guild.id):
        return False, "El módulo de orientación está desactivado."

    channel = guild.get_channel(get_orientation_channel_id(guild.id))
    if not isinstance(channel, discord.TextChannel):
        return False, "No hay un canal de orientación válido configurado."

    me = guild.me
    if me is None:
        return False, "No pude resolver el miembro del bot en el servidor."

    perms = channel.permissions_for(me)
    missing = [
        label for label, ok in (
            ("Ver canal", perms.view_channel),
            ("Enviar mensajes", perms.send_messages),
            ("Insertar enlaces", perms.embed_links),
            ("Añadir reacciones", perms.add_reactions),
            ("Leer historial", perms.read_message_history),
            ("Gestionar mensajes", perms.manage_messages),
        ) if not ok
    ]
    if not me.guild_permissions.manage_roles:
        missing.append("Gestionar roles")
    if missing:
        return False, "Faltan permisos: **" + ", ".join(missing) + "**."

    bindings = get_orientation_bindings(guild.id)
    if not (ORIENTATION_MIN_ROLES <= len(bindings) <= ORIENTATION_MAX_ROLES):
        return False, "Selecciona entre **1 y 6 roles existentes** antes de activar el sistema."

    seen_roles: set[int] = set()
    seen_emojis: set[str] = set()
    managed_roles: list[tuple[discord.Role, str]] = []
    for binding in bindings:
        role_id = int(binding["role_id"])
        emoji = str(binding["emoji"]).strip()
        emoji_key = _orientation_emoji_key(emoji)
        role = guild.get_role(role_id)
        if role is None:
            return False, f"Uno de los roles configurados ya no existe (`{role_id}`). Selecciónalo de nuevo."
        if role_id in seen_roles:
            return False, f"El rol {role.mention} está repetido en la configuración."
        if emoji_key in seen_emojis:
            return False, f"El emoji **{emoji}** está repetido. Cada rol necesita uno distinto."
        if not role.is_assignable():
            return False, f"No puedo asignar {role.mention}. Coloca el rol de El Heraldo por encima de ese rol."
        seen_roles.add(role_id)
        seen_emojis.add(emoji_key)
        managed_roles.append((role, emoji))

    # Persiste cualquier configuración migrada de la versión anterior y deja de
    # considerar los roles como recursos creados por El Heraldo.
    set_orientation_bindings(guild.id, bindings)
    guild_config_set(guild.id, "orientation_created_role_ids", "[]")

    message = None
    old_channel_id = get_orientation_message_channel_id(guild.id)
    old_message_id = get_orientation_message_id(guild.id)

    # Si el canal cambió, elimina la tarjeta anterior para garantizar una sola fuente
    # de verdad y evita duplicados.
    if old_message_id and old_channel_id and old_channel_id != channel.id:
        old_channel = guild.get_channel(old_channel_id)
        if isinstance(old_channel, discord.TextChannel):
            try:
                old_message = await old_channel.fetch_message(old_message_id)
                await old_message.delete()
            except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                pass
        guild_config_set(guild.id, "orientation_message_id", "0")

    message_id = get_orientation_message_id(guild.id)
    if message_id:
        try:
            message = await channel.fetch_message(message_id)
        except discord.NotFound:
            message = None
        except (discord.Forbidden, discord.HTTPException):
            return False, "No pude acceder a la tarjeta de orientación guardada."

    if message is None:
        try:
            message = await channel.send(embed=build_orientation_embed(guild))
        except (discord.Forbidden, discord.HTTPException):
            return False, "No pude publicar la tarjeta de orientación."
        guild_config_set(guild.id, "orientation_message_id", str(message.id))
        guild_config_set(guild.id, "orientation_message_channel_id", str(channel.id))
    else:
        try:
            await message.edit(embed=build_orientation_embed(guild), content=None, view=None)
        except (discord.Forbidden, discord.HTTPException):
            return False, "No pude actualizar la tarjeta de orientación."

    try:
        await message.clear_reactions()
        for _role, emoji in managed_roles:
            await message.add_reaction(emoji)
    except (discord.Forbidden, discord.HTTPException):
        return False, "La tarjeta existe, pero no pude sincronizar sus reacciones."

    return True, f"Orientación sincronizada en {channel.mention}."


async def disable_orientation_system(guild: discord.Guild) -> tuple[bool, str]:
    """Desactiva el módulo sin modificar ningún rol del servidor."""
    guild_config_set(guild.id, "orientation_enabled", "0")

    message_id = get_orientation_message_id(guild.id)
    channel_id = get_orientation_message_channel_id(guild.id)
    channel = guild.get_channel(channel_id) if channel_id else None
    if message_id and isinstance(channel, discord.TextChannel):
        try:
            message = await channel.fetch_message(message_id)
            await message.delete()
        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            pass

    guild_config_set(guild.id, "orientation_message_id", "0")
    guild_config_set(guild.id, "orientation_message_channel_id", "0")
    guild_config_set(guild.id, "orientation_role_bindings", "[]")
    guild_config_set(guild.id, "orientation_created_role_ids", "[]")

    # Limpia únicamente referencias antiguas de configuración. Nunca borra roles.
    conn = db_connect()
    conn.execute(
        """
        DELETE FROM guild_resources
        WHERE guild_id = ? AND resource_type = 'role'
          AND (config_key LIKE 'orientation_rr_%' OR config_key LIKE 'orientation_role_%')
        """,
        (guild.id,),
    )
    conn.commit()
    conn.close()
    return True, "Orientación desactivada. La tarjeta y sus vínculos fueron limpiados; los roles del servidor no se modificaron."


def get_recovery_channel_id(guild_id: int) -> int:
    return get_guild_channel_id(guild_id, "recovery")


def get_log_channel_id(guild_id: int | None = None) -> int:
    if guild_id is None:
        value = db_meta_get("log_channel_id")
        return int(value) if value is not None else LOG_CHANNEL_ID
    configured = get_guild_channel_id(guild_id, "logs")
    if configured:
        return configured
    configured = guild_config_get(guild_id, "log_channel_id")
    if configured:
        return int(configured)
    if legacy_fallback_allowed(guild_id):
        value = db_meta_get("log_channel_id")
        if value is not None:
            return int(value)
        return LOG_CHANNEL_ID
    return 0


def set_log_channel_id(channel_id: int, guild_id: int | None = None) -> None:
    if guild_id is None:
        db_meta_set("log_channel_id", str(channel_id))
    else:
        guild_resource_set(guild_id, "channel", "logs", channel_id)
        guild_config_set(guild_id, "log_channel_id", str(channel_id))


def verify_enabled(guild_id: int | None = None) -> bool:
    if guild_id is None:
        return db_meta_get("verify_enabled") == "1"
    value = _guild_or_legacy_setting(guild_id, "verify_enabled", "0")
    return value == "1"


def get_verify_role_id(guild_id: int | None = None) -> int:
    if guild_id is not None:
        configured = guild_config_get(guild_id, "verify_role_id")
        if configured:
            return int(configured)
        legacy = _guild_or_legacy_setting(guild_id, "verify_role_id", "")
        if legacy:
            try:
                return int(legacy)
            except ValueError:
                pass
        tentado = get_tentado_role_id(guild_id)
        if tentado:
            return tentado
        return 0
    value = db_meta_get("verify_role_id")
    try:
        return int(value) if value is not None else TENTADO_ROLE_ID
    except (TypeError, ValueError):
        return TENTADO_ROLE_ID


def get_verify_timeout(guild_id: int | None = None) -> int:
    """Timeout de verificación por servidor, con compatibilidad con la configuración antigua."""
    if guild_id is None:
        value = db_meta_get("verify_timeout")
    else:
        value = _guild_or_legacy_setting(guild_id, "verify_timeout", str(VERIFY_TIMEOUT_DEFAULT))
    try:
        return int(value)
    except (TypeError, ValueError):
        return VERIFY_TIMEOUT_DEFAULT


def get_verify_action(guild_id: int | None = None) -> str:
    if guild_id is None:
        value = db_meta_get("verify_action")
    else:
        value = _guild_or_legacy_setting(guild_id, "verify_action", VERIFY_ACTION_DEFAULT)
    return value if value in VERIFY_ACTION_LABELS else VERIFY_ACTION_DEFAULT


def get_verify_panel_text(guild_id: int | None = None) -> str:
    return _guild_or_legacy_setting(guild_id, "verify_panel_text", VERIFY_PANEL_TEXT_DEFAULT)


def get_verify_button_label(guild_id: int | None = None) -> str:
    return _guild_or_legacy_setting(guild_id, "verify_button_label", VERIFY_BUTTON_LABEL_DEFAULT)


def get_verify_success_text(guild_id: int | None = None) -> str:
    return _guild_or_legacy_setting(guild_id, "verify_success_text", VERIFY_SUCCESS_TEXT_DEFAULT)


VERIFY_DM_TITLE_DEFAULT = "HAS CRUZADO EL UMBRAL"
VERIFY_DM_BODY_DEFAULT = (
    "Pero antes de que puedas perderte entre las puertas del paraíso, hay dos pasos que separan a los curiosos de los que realmente pertenecen:\n\n"
    "**Verifícate** en el canal de verificación — sin esto, sigues del otro lado del portón.\n\n"
    "🎭 Luego, elige tus roles de orientación cuando nadie está mirando.\n\n"
    "Cada rol abre una puerta distinta. Elige bien.\n\n"
    "¿Dudas? Revisa el canal de dudas del servidor."
)
VERIFY_DM_FIELD_NAME_DEFAULT = "Este no es un lugar cualquiera"
VERIFY_DM_FOOTER_DEFAULT = "© Paraíso Morboso 🍑🍆🥛"
VERIFY_DM_COLOR_DEFAULT = "4F5BDC"
VERIFY_DM_FOOTER_ICON_DEFAULT = "https://media.discordapp.net/attachments/1548766637866360852/1548771260476162189/39d74668-f12d-4979-bcc3-9b6826f2e8d5.png?ex=6ac49d63&is=6ac34be3&hm=b939835c020aeea2d422d7057213117b1744d4f95d37d180e8f"

def get_verify_dm_title(guild_id: int | None = None) -> str:
    return _guild_or_legacy_setting(guild_id, "verify_dm_title", VERIFY_DM_TITLE_DEFAULT)

def get_verify_dm_body(guild_id: int | None = None) -> str:
    return _guild_or_legacy_setting(guild_id, "verify_dm_body", VERIFY_DM_BODY_DEFAULT)

def get_verify_dm_field_name(guild_id: int | None = None) -> str:
    return _guild_or_legacy_setting(guild_id, "verify_dm_field_name", VERIFY_DM_FIELD_NAME_DEFAULT)

def get_verify_dm_footer(guild_id: int | None = None) -> str:
    return _guild_or_legacy_setting(guild_id, "verify_dm_footer", VERIFY_DM_FOOTER_DEFAULT)

def get_verify_dm_color(guild_id: int | None = None) -> str:
    return _guild_or_legacy_setting(guild_id, "verify_dm_color", VERIFY_DM_COLOR_DEFAULT)

def get_verify_dm_footer_icon(guild_id: int | None = None) -> str:
    return _guild_or_legacy_setting(guild_id, "verify_dm_footer_icon", VERIFY_DM_FOOTER_ICON_DEFAULT)


def build_verification_welcome_embed(
    member: discord.Member | None = None, guild: discord.Guild | None = None,
) -> discord.Embed:
    ctx = VarContext(guild or (member.guild if member is not None else None), member)
    effective_guild = guild or (member.guild if member is not None else None)
    guild_id = effective_guild.id if effective_guild is not None else None
    color_text = get_verify_dm_color(guild_id).strip().lstrip("#")
    try:
        color_value = int(color_text, 16)
        if not 0 <= color_value <= 0xFFFFFF:
            raise ValueError
    except ValueError:
        color_value = int(VERIFY_DM_COLOR_DEFAULT, 16)

    embed = discord.Embed(
        title=render_vars(get_verify_dm_title(guild_id), ctx, 256),
        color=discord.Color(color_value),
    )
    embed.add_field(
        name=render_vars(get_verify_dm_field_name(guild_id), ctx, 256),
        value=render_vars(get_verify_dm_body(guild_id), ctx, 1024),
        inline=False,
    )
    footer_icon = render_url_var(get_verify_dm_footer_icon(guild_id), ctx)
    footer_text = render_vars(get_verify_dm_footer(guild_id), ctx, 2048)
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
async def on_ready() -> None:
    global _startup_done

    if not any(isinstance(view, VerifyView) for view in bot.persistent_views):
        try:
            bot.add_view(VerifyView())
        except Exception:
            print("❌ No se pudo registrar la vista persistente de verificación:")
            traceback.print_exc()

    if _startup_done:
        # on_ready también se dispara tras una reconexión. Las vistas y loops siguen
        # registrados, pero la caché de invitaciones puede haber quedado obsoleta
        # mientras el bot estuvo desconectado.
        for guild in bot.guilds:
            try:
                await refresh_invite_cache(guild)
            except Exception:
                print(f"⚠️ No pude refrescar invitaciones tras reconectar en {guild.name}:")
                traceback.print_exc()
        return

    db_init()
    honeypot_db_init()

    # Vincula la configuración antigua de una sola instancia al servidor que contiene
    # el panel de verificación, evitando que otro servidor herede esos textos.
    if db_meta_get("verify_legacy_guild_id") is None:
        legacy_ref = db_meta_get("verify_panel_ref")
        if legacy_ref and legacy_ref.count(":") == 1:
            try:
                legacy_channel_id = int(legacy_ref.split(":")[0])
                legacy_guild = next(
                    (g for g in bot.guilds if g.get_channel(legacy_channel_id) is not None),
                    None,
                )
                if legacy_guild is not None:
                    db_meta_set("verify_legacy_guild_id", str(legacy_guild.id))
            except (TypeError, ValueError):
                pass

    if db_meta_get("verify_legacy_guild_id") is None:
        legacy_ids = {x for x in (LOG_CHANNEL_ID, CONDEMNED_CHANNEL_ID, TENTADO_ROLE_ID, SIN_VERIFICAR_ROLE_ID) if x}
        scored: list[tuple[int, discord.Guild]] = []
        for candidate in bot.guilds:
            score = sum(
                1 for resource_id in legacy_ids
                if candidate.get_channel(resource_id) is not None or candidate.get_role(resource_id) is not None
            )
            if score:
                scored.append((score, candidate))
        scored.sort(key=lambda item: item[0], reverse=True)
        if scored and (len(scored) == 1 or scored[0][0] > scored[1][0]):
            db_meta_set("verify_legacy_guild_id", str(scored[0][1].id))
        elif len(bot.guilds) == 1:
            db_meta_set("verify_legacy_guild_id", str(bot.guilds[0].id))

    for guild in bot.guilds:
        try:
            await bootstrap_guild_configuration(guild)
            # Migra recursos heredados del servidor actual únicamente si existen allí.
            legacy_roles = {
                "sin_verificar": SIN_VERIFICAR_ROLE_ID,
                "tentado": TENTADO_ROLE_ID,
                "condenado": 0,
            }
            for key, role_id in legacy_roles.items():
                if role_id and guild.get_role(role_id):
                    if guild_resource_get(guild.id, "role", key) is None:
                        guild_resource_set(guild.id, "role", key, role_id)
            for idx, role_id in enumerate(sorted(EVAL_ROLE_IDS), 1):
                if guild.get_role(role_id) and guild_resource_get(guild.id, "role", f"eval_{idx}") is None:
                    guild_resource_set(guild.id, "role", f"eval_{idx}", role_id)
            legacy_channels = {
                "logs": LOG_CHANNEL_ID,
                "condemned": CONDEMNED_CHANNEL_ID,
            }
            for key, channel_id in legacy_channels.items():
                if channel_id and guild.get_channel(channel_id) and guild_resource_get(guild.id, "channel", key) is None:
                    guild_resource_set(guild.id, "channel", key, channel_id)
            if orientation_enabled(guild.id):
                ok, note = await ensure_orientation_system(guild)
                if not ok:
                    print(f"⚠️ Orientación · {guild.name}: {note}")
        except Exception:
            traceback.print_exc()

    # Reasocia cada botón de perdón a su mensaje real. Esto es más robusto que
    # registrar una vista global porque Discord puede entregar el custom_id de
    # una tarjeta antigua después de un reinicio.
    try:
        active_condemnations = condemnation_list_all_active()
        for condemnation_row in active_condemnations:
            message_id = condemnation_row["announcement_message_id"]
            if not message_id:
                continue
            bot.add_view(
                CondemnationPardonView(),
                message_id=int(message_id),
            )
        print(
            f"✅ Vistas de perdón restauradas: "
            f"{sum(1 for row in active_condemnations if row['announcement_message_id'])}"
        )
    except Exception:
        print("❌ No se pudieron restaurar las vistas de perdón:")
        traceback.print_exc()
    # Sistema de sugerencias: registra las vistas persistentes y recupera el panel/revisiones pendientes.
    try:
        await suggestions_startup()
    except Exception:
        traceback.print_exc()
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
            print(f"Comando global huérfano eliminado: /{cmd.name}")
    except discord.HTTPException as e:
        print(f"No se pudo limpiar comandos globales: {e}")
    if not moderation_case_expiry_loop.is_running():
        moderation_case_expiry_loop.start()
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

        setup_view_errors = validate_setup_view_layouts(guild.id)
        if setup_view_errors:
            print(f"❌ Autoprueba /setup falló en {guild.name}:")
            for error in setup_view_errors:
                print(f"   - {error}")
        else:
            print(f"✅ Autoprueba /setup correcta en {guild.name}.")
    if not member_of_the_week_loop.is_running():
        member_of_the_week_loop.start()
    if not join_roles_sync_loop.is_running():
        join_roles_sync_loop.start()
    if not template_backup_loop.is_running():
        template_backup_loop.start()
    _startup_done = True
    print(f"El Heraldo conectado como {bot.user}")


@bot.event
async def on_guild_join(guild: discord.Guild) -> None:
    """Registra un servidor nuevo y publica allí los comandos sin esperar un reinicio."""
    try:
        await bootstrap_guild_configuration(guild, create_missing=False)
        await log_embed(
            guild,
            "🪽 El Heraldo está listo para configurarse",
            "No se crearon canales ni roles automáticamente. Usa /setup para "
            "decidir si quieres permitir la creación de recursos faltantes.",
            discord.Color.blurple(),
        )
    except Exception:
        traceback.print_exc()

    try:
        await refresh_invite_cache(guild)
    except Exception:
        print(f"⚠️ No pude inicializar la caché de invitaciones en {guild.name}:")
        traceback.print_exc()

    # Los comandos globales se eliminan deliberadamente en on_ready; por eso un
    # servidor añadido después del arranque necesita su propia sincronización.
    try:
        bot.tree.copy_global_to(guild=guild)
        await bot.tree.sync(guild=guild)
    except Exception:
        print(f"⚠️ No se pudieron sincronizar los comandos en el nuevo servidor {guild.name}:")
        traceback.print_exc()

    setup_view_errors = validate_setup_view_layouts(guild.id)
    if setup_view_errors:
        print(f"❌ Autoprueba /setup falló en el nuevo servidor {guild.name}:")
        for error in setup_view_errors:
            print(f"   - {error}")


@bot.event
async def on_member_join(member: discord.Member) -> None:
    if member.bot:
        # Los bots no pasan por verificación, pero Sapphire-style Bot Roles sí
        # pueden asignarse de forma independiente.
        if join_roles_bot_enabled(member.guild.id):
            asyncio.create_task(assign_bot_join_roles(member))
        return

    invite_code = await detect_used_invite(member.guild)
    db_upsert_join(member.guild.id, member.id, invite_code)

    # Una condena activa tiene prioridad absoluta sobre los flujos de verificación.
    # El miembro puede salir y volver: la condena persiste en SQLite.
    condemnation = condemnation_get(member.guild.id, member.id)
    if condemnation is not None and condemnation_is_expired(condemnation):
        condemnation_deactivate(member.guild.id, member.id)  # caducó mientras estaba fuera: entra como cualquier miembro nuevo
        condemnation = None
    if condemnation is not None:
        db_clear_verify_pending(member.guild.id, member.id)
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
            db_clear_verify_pending(member.guild.id, member.id)
            return
    except Exception:
        traceback.print_exc()

    if join_roles_enabled(member.guild.id) or member.id in get_join_specific_roles(member.guild.id):
        asyncio.create_task(assign_join_roles(member))

    if verify_enabled(member.guild.id):
        waiting_screening = (
            join_roles_wait_screening(member.guild.id)
            and (join_roles_enabled(member.guild.id) or member.id in get_join_specific_roles(member.guild.id))
            and getattr(member, "pending", False)
        )
        if not waiting_screening:
            now = datetime.now(timezone.utc)
            db_set_verify_pending(member.guild.id, member.id, now)
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
    active_condemnation = condemnation_get(after.guild.id, after.id)
    condemned_id = condemnation_role_id(active_condemnation, after.guild.id)
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
                    purge_spec=hp_purge_spec(after.guild.id),
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
                    condemnation_add_saved_roles(after.guild.id, after.id, new_ids)
                else:
                    await log_embed(after.guild, "⚠️ No pude re-quitar roles a un condenado", f"{after.mention}: {note}", discord.Color.orange())
            except Exception:
                traceback.print_exc()
            finally:
                _condemn_sync_busy.discard(after.id)
        db_clear_tentado(after.guild.id, after.id)
        db_clear_sin_verificado(after.guild.id, after.id)
        db_clear_verify_pending(after.guild.id, after.id)
        return

    # Flujos normales de verificación; una condena activa ya salió por arriba.
    # Join Roles que esperan Rules Screening se asignan al completar la pantalla.
    if (
        (join_roles_enabled(after.guild.id) or after.id in get_join_specific_roles(after.guild.id))
        and join_roles_wait_screening(after.guild.id)
        and getattr(before, "pending", False)
        and not getattr(after, "pending", False)
    ):
        asyncio.create_task(assign_join_roles(after))
        verify_role_id_after_screening = get_verify_role_id(after.guild.id)
        if (
            verify_enabled(after.guild.id)
            and verify_role_id_after_screening not in after_role_ids
        ):
            now = datetime.now(timezone.utc)
            db_set_verify_pending(after.guild.id, after.id, now)
            asyncio.create_task(schedule_verify_timeout(after.guild.id, after.id, now))

    # Si el rol de verificación aparece por cualquier medio, Sin Verificar se retira.
    verify_role_id = get_verify_role_id(after.guild.id)
    if verify_role_id and verify_role_id in after_role_ids and verify_role_id not in before_role_ids:
        await clear_sin_verificar_after_verification(
            after,
            reason="Rol de verificación detectado por El Heraldo",
        )
        return

    if get_sin_verificado_role_id(after.guild.id) in after_role_ids and get_sin_verificado_role_id(after.guild.id) not in before_role_ids:
        if verify_role_id and verify_role_id in after_role_ids:
            await clear_sin_verificar_after_verification(
                after,
                reason="Sin Verificar no aplica a un miembro ya verificado",
            )
        else:
            now = datetime.now(timezone.utc)
            db_set_sin_verificado(after.guild.id, after.id, now)
            asyncio.create_task(schedule_sin_verificado_check(after.guild.id, after.id, now))
            print(f"⏳ {after} recibió Sin Verificar — respaldo armado.")

    # IMPORTANTE: asignar el rol de verificación/orientación manualmente NO inicia
    # el temporizador. La orientación solo nace cuando El Heraldo procesa una
    # verificación nueva desde su botón. Esto protege a miembros antiguos y evita
    # aplicar expulsiones retroactivas al instalar o reconfigurar el bot.


async def schedule_sin_verificado_check(guild_id: int, user_id: int, marked_at: datetime) -> None:
    delay = (marked_at + get_sin_verificado_window(guild_id) - datetime.now(timezone.utc)).total_seconds()
    if delay > 0:
        await asyncio.sleep(delay)
    await evaluate_sin_verificado(guild_id, user_id)


async def evaluate_sin_verificado(guild_id: int, user_id: int) -> None:
    """Respaldo del timeout de Sin Verificar (299s). Si a los 300s el
    miembro sigue con Sin Verificar, se expulsa directo — sin DM."""
    if condemnation_get(guild_id, user_id) is not None:
        db_clear_sin_verificado(guild_id, user_id)
        return
    guild = bot.get_guild(guild_id)
    if guild is None:
        return
    member = guild.get_member(user_id)
    if member is None:
        db_clear_sin_verificado(guild_id, user_id)  # ya lo expulsaron — nada que hacer
        return

    if get_sin_verificado_role_id(guild_id) not in {r.id for r in member.roles}:
        db_clear_sin_verificado(guild_id, user_id)  # ya verificó a tiempo
        return

    db_clear_sin_verificado(guild_id, user_id)
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
    delay = (tentado_at + get_orientation_window(guild_id) - datetime.now(timezone.utc)).total_seconds()
    if delay > 0:
        await asyncio.sleep(delay)
    await evaluate_member(guild_id, user_id)


@tasks.loop(minutes=2)
async def check_pending_verifications() -> None:
    """Red de seguridad: retoma verificaciones pendientes sin dejar que una fila
    dañada o un fallo puntual detenga toda la automatización."""
    conn: sqlite3.Connection | None = None
    try:
        conn = db_connect()
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT guild_id, user_id, tentado_at, sin_verificado_at, verify_pending_at FROM guild_members "
            "WHERE tentado_at IS NOT NULL OR sin_verificado_at IS NOT NULL "
            "OR verify_pending_at IS NOT NULL"
        ).fetchall()
    except Exception:
        print("❌ Falló la lectura de verificaciones pendientes:")
        traceback.print_exc()
        return
    finally:
        if conn is not None:
            conn.close()

    now = datetime.now(timezone.utc)
    for row in rows:
        try:
            guild = bot.get_guild(row["guild_id"])
            if guild is None:
                if row["tentado_at"] is not None:
                    db_clear_tentado(row["guild_id"], row["user_id"])
                if row["sin_verificado_at"] is not None:
                    db_clear_sin_verificado(row["guild_id"], row["user_id"])
                if row["verify_pending_at"] is not None:
                    db_clear_verify_pending(row["guild_id"], row["user_id"])
                continue

            if row["tentado_at"] is not None:
                tentado_at = datetime.fromisoformat(row["tentado_at"])
                if now >= tentado_at + get_orientation_window(guild.id):
                    await evaluate_member(guild.id, row["user_id"])

            if row["sin_verificado_at"] is not None:
                sin_verificado_at = datetime.fromisoformat(row["sin_verificado_at"])
                if now >= sin_verificado_at + get_sin_verificado_window(guild.id):
                    await evaluate_sin_verificado(guild.id, row["user_id"])

            if row["verify_pending_at"] is not None:
                verify_pending_at = datetime.fromisoformat(row["verify_pending_at"])
                verify_window = timedelta(seconds=get_verify_timeout(guild.id))
                if now >= verify_pending_at + verify_window:
                    await evaluate_verify_timeout(guild.id, row["user_id"])
        except Exception:
            print(
                "❌ Verificación pendiente falló "
                f"(guild={row['guild_id']}, user={row['user_id']}):"
            )
            traceback.print_exc()


async def evaluate_member(guild_id: int, user_id: int, report: bool = True) -> str:
    """Devuelve 'verificado', 'expulsado', 'castigado' o 'ausente'/'sin-guild'."""
    if condemnation_get(guild_id, user_id) is not None:
        db_clear_tentado(guild_id, user_id)
        return "castigado"
    guild = bot.get_guild(guild_id)
    if guild is None:
        return "sin-guild"
    member = guild.get_member(user_id)
    if member is None:
        db_clear_tentado(guild_id, user_id)  # ya no está, nada que hacer
        return "ausente"

    punish_id = hp_punish_role_id(guild_id)
    if punish_id and any(r.id == punish_id for r in member.roles):
        db_clear_tentado(guild_id, user_id)  # castigado por el honeypot: no se expulsa por falta de orientación
        return "castigado"

    role_ids = {r.id for r in member.roles}
    if role_ids & get_eval_role_ids(guild.id):
        db_clear_tentado(guild_id, user_id)  # se verificó a tiempo
        if report:
            await log_embed(guild, "✅ Verificado", f"{member.mention} eligió un buen camino.", discord.Color.green())
        return "verificado"

    await expel(member, report=report)
    return "expulsado"


# ---------------------------------------------------------------------------
# Expulsión + DM condicional
# ---------------------------------------------------------------------------

async def expel(member: discord.Member, report: bool = True) -> None:
    row = db_get(member.guild.id, member.id)
    dm_sent_before = bool(row["dm_sent"]) if row else False
    is_first_fault = not dm_sent_before

    dm_ok = None  # None = no aplica (2da falta, no se intenta DM)
    if is_first_fault:
        dm_ok = await send_recovery_dm(member, report=report)
        db_mark_dm_sent(member.guild.id, member.id)

    db_clear_tentado(member.guild.id, member.id)
    try:
        await member.kick(reason="No definió su orientación")
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
        value="No definió su orientación.",
        inline=False,
    )
    embed.add_field(name="Falta", value="1ra — se le dio otra oportunidad" if is_first_fault else "2da — sin nueva oportunidad", inline=True)
    if dm_ok is not None:
        embed.add_field(name="DM de recuperación", value="✅ Enviado" if dm_ok else "⚠️ Falló (DMs cerrados)", inline=True)
    embed.add_field(name="Resultado", value="✅ Expulsado" if kicked else "⚠️ Falló — revisa jerarquía de roles", inline=True)
    embed.set_footer(text="Paraíso Morboso 2026 © - El Heraldo 🪽")

    channel = member.guild.get_channel(get_log_channel_id(member.guild.id))
    if channel is not None:
        try:
            await channel.send(embed=embed)
        except discord.Forbidden:
            print("Sin permisos para escribir en el canal de logs")


async def send_recovery_dm(member: discord.Member, report: bool = True) -> bool:
    """Devuelve True si el DM se envió con éxito."""
    channel = member.guild.get_channel(get_recovery_channel_id(member.guild.id))
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

async def bootstrap_guild_configuration(guild: discord.Guild, create_missing: bool | None = None) -> dict[str, list[int]]:
    """Detecta/reutiliza la estructura base y, opcionalmente, crea lo que falte.

    Por defecto NO crea canales ni roles. La creación automática solo se habilita
    cuando el administrador la activa desde /setup. Así, añadir el bot a
    un servidor existente nunca crea recursos inesperados.
    """
    desired_channels = {
        "logs": "El Heraldo",
        "condemned": "Condenados",
        "honeypot": "Honeypot",
        "verification": "Verificación",
        "questions": "Dudas",
    }
    created: dict[str, list[int]] = {"channels": [], "roles": []}
    if create_missing is None:
        create_missing = guild_config_get(guild.id, "heraldo_auto_create_resources") == "1"
    me = guild.me
    if me is None:
        return created

    # La instalación es deliberadamente idempotente: /setup también sirve
    # para reparar la estructura después de que un canal/rol haya sido eliminado.
    # Primero respetamos el ID guardado; solo si ya no existe buscamos por nombre.
    existing_channels = {c.name.casefold(): c for c in guild.text_channels}
    for key, default_name in desired_channels.items():
        channel = None
        saved_id = guild_resource_get(guild.id, "channel", key)
        if saved_id:
            candidate = guild.get_channel(saved_id)
            if isinstance(candidate, discord.TextChannel):
                channel = candidate
        if channel is None:
            channel = existing_channels.get(default_name.casefold())
        if channel is None:
            if not create_missing:
                continue
            if not me.guild_permissions.manage_channels:
                continue
            try:
                channel = await guild.create_text_channel(
                    default_name,
                    reason="El Heraldo: instalación/reparación de plantilla base",
                )
                created["channels"].append(channel.id)
                existing_channels[channel.name.casefold()] = channel
            except discord.Forbidden:
                continue
        guild_resource_set(guild.id, "channel", key, channel.id)

    if me.guild_permissions.manage_roles:
        desired_roles = {
            "sin_verificar": "Sin Verificar",
            "tentado": "Tentad@",
            "condenado": "Condenado",
        }
        existing_roles = {r.name.casefold(): r for r in guild.roles}
        for key, default_name in desired_roles.items():
            role = None
            saved_id = guild_resource_get(guild.id, "role", key)
            if saved_id:
                candidate = guild.get_role(saved_id)
                if candidate is not None:
                    role = candidate
            if role is None:
                role = existing_roles.get(default_name.casefold())
            if role is None:
                if not create_missing:
                    continue
                try:
                    role = await guild.create_role(
                        name=default_name,
                        reason="El Heraldo: instalación/reparación de plantilla base",
                    )
                    created["roles"].append(role.id)
                    existing_roles[role.name.casefold()] = role
                except discord.Forbidden:
                    continue
            guild_resource_set(guild.id, "role", key, role.id)

    # Solo se marca como inicializado después de ejecutar el proceso completo.
    # En una ejecución posterior se vuelve a comprobar todo, por lo que una
    # eliminación accidental puede repararse sin borrar ni duplicar recursos.
    guild_mark_initialized(guild.id)
    return created


class HeraldoGeneralConfigModal(discord.ui.Modal, title="El Heraldo · Configuración general"):
    verify_timeout = discord.ui.TextInput(
        label="Tiempo de verificación (minutos)",
        required=False,
        max_length=6,
        placeholder="Ejemplo: 5",
    )
    orientation_timeout = discord.ui.TextInput(
        label="Tiempo de orientación (minutos)",
        required=False,
        max_length=6,
        placeholder="Ejemplo: 10",
    )
    sin_verificar_timeout = discord.ui.TextInput(
        label="Respaldo Sin Verificar (minutos)",
        required=False,
        max_length=6,
        placeholder="Ejemplo: 5",
    )

    def __init__(self, guild_id: int) -> None:
        super().__init__()
        self.guild_id = guild_id
        self.verify_timeout.default = str(max(1, get_verify_timeout(guild_id) // 60))
        self.orientation_timeout.default = str(max(1, int(get_orientation_window(guild_id).total_seconds() // 60)))
        self.sin_verificar_timeout.default = str(max(1, int(get_sin_verificado_window(guild_id).total_seconds() // 60)))

    async def on_submit(self, interaction: discord.Interaction) -> None:
        try:
            verify_minutes = int(str(self.verify_timeout).strip())
            orientation_minutes = int(str(self.orientation_timeout).strip())
            sin_verificar_minutes = int(str(self.sin_verificar_timeout).strip())
            if min(verify_minutes, orientation_minutes, sin_verificar_minutes) < 1:
                raise ValueError
        except ValueError:
            await interaction.response.send_message("❌ Los tres tiempos deben ser números enteros mayores que 0.", ephemeral=True)
            return

        guild_config_set(self.guild_id, "verify_timeout", str(verify_minutes * 60))
        guild_config_set(self.guild_id, "orientation_timeout_seconds", str(orientation_minutes * 60))
        guild_config_set(self.guild_id, "sin_verificado_timeout_seconds", str(sin_verificar_minutes * 60))
        await interaction.response.send_message(
            "✅ Tiempos guardados por servidor.\n"
            f"• Verificación: **{verify_minutes} min**\n"
            f"• Orientación: **{orientation_minutes} min**\n"
            f"• Respaldo Sin Verificar: **{sin_verificar_minutes} min**",
            ephemeral=True,
        )


HERALDO_CHANNEL_DEFINITIONS = {
    "logs": ("📋 Logs", "El Heraldo"),
    "condemned": ("⚖️ Condenados", "Condenados"),
    "honeypot": ("🍯 Honeypot", "Honeypot"),
    "verification": ("✅ Verificación", "Verificación"),
    "questions": ("💬 Dudas", "Dudas"),
}


def heraldo_channels_summary(guild: discord.Guild) -> str:
    lines: list[str] = []
    for key, (label, default_name) in HERALDO_CHANNEL_DEFINITIONS.items():
        channel_id = get_guild_channel_id(guild.id, key)
        channel = guild.get_channel(channel_id) if channel_id else None
        if isinstance(channel, discord.TextChannel):
            lines.append(f"✅ **{label}:** {channel.mention}")
            continue
        exact = next(
            (c for c in guild.text_channels if c.name.casefold() == default_name.casefold()),
            None,
        )
        if exact is not None:
            lines.append(f"🟡 **{label}:** existe {exact.mention}, pero todavía no está seleccionado")
        else:
            lines.append(f"⚪ **{label}:** no configurado · puedes seleccionar uno o crear **#{default_name}**")
    return "\n".join(lines)


def heraldo_setup_home_content() -> str:
    return (
        "🪽 **El Heraldo · Configuración del servidor**\n\n"
        "La configuración está organizada por módulos. Entra en la sección que quieras modificar:\n"
        "**AutoMod · Moderation · Join Roles · Reaction Roles · Role Connections · Logging · Verification · Idioma**."
    )


async def heraldo_setup_go_home(
    interaction: discord.Interaction, guild_id: int, owner_id: int,
) -> None:
    await interaction.response.edit_message(
        content=heraldo_setup_home_content(),
        embed=None,
        view=HeraldoSetupView(guild_id, owner_id),
    )



def _pending_config_text(items: list[str]) -> str:
    if not items:
        return ""
    return "\n\n**Cambios pendientes (aún no guardados):**\n" + "\n".join(f"• {item}" for item in items)


async def _setup_publish_verification_panel(
    guild: discord.Guild, channel: discord.TextChannel,
) -> str:
    """Publica o mueve el panel de verificación al canal elegido desde /setup."""
    ref = guild_config_get(guild.id, "verify_panel_ref")
    if ref and ref.count(":") == 1:
        try:
            old_channel_id, old_message_id = (int(x) for x in ref.split(":"))
            old_channel = guild.get_channel(old_channel_id)
            if isinstance(old_channel, discord.TextChannel):
                old_message = await old_channel.fetch_message(old_message_id)
                if old_channel.id == channel.id:
                    await old_message.edit(
                        content=render_vars(
                            get_verify_panel_text(guild.id),
                            VarContext(guild, None, channel),
                            2000,
                        ),
                        view=VerifyView(label=get_verify_button_label(guild.id)),
                        allowed_mentions=discord.AllowedMentions.none(),
                    )
                    return "Panel de verificación actualizado."
                try:
                    await old_message.delete()
                except discord.HTTPException:
                    pass
        except (ValueError, discord.NotFound, discord.Forbidden, discord.HTTPException):
            pass

    message = await channel.send(
        content=render_vars(
            get_verify_panel_text(guild.id),
            VarContext(guild, None, channel),
            2000,
        ),
        view=VerifyView(label=get_verify_button_label(guild.id)),
        allowed_mentions=discord.AllowedMentions.none(),
    )
    guild_config_set(guild.id, "verify_panel_ref", f"{channel.id}:{message.id}")
    return "Panel de verificación publicado."


async def _setup_apply_system_channel(
    guild: discord.Guild,
    key: str,
    channel: discord.TextChannel,
    *,
    publish_messages: bool = True,
) -> str:
    """Vincula un canal de /setup con su módulo y sincroniza su mensaje persistente."""
    guild_resource_set(guild.id, "channel", key, channel.id)

    if key == "logs":
        set_log_channel_id(channel.id, guild.id)
        if publish_messages:
            await log_embed(
                guild,
                "⚙️ Canal de logs configurado",
                f"{channel.mention} quedó establecido como canal de logs de El Heraldo.",
                discord.Color.blurple(),
            )
        return "Canal de logs establecido."

    if key == "condemned":
        set_condemnation_channel_id(channel.id, guild.id)
        return "Canal de condenados establecido."

    if key == "verification":
        guild_config_set(guild.id, "verify_channel_id", str(channel.id))
        if publish_messages:
            return await _setup_publish_verification_panel(guild, channel)
        return "Canal de verificación establecido."

    if key == "honeypot":
        hp_add_trap(guild.id, channel.id)
        # Si se crea/configura desde /setup, su tarjeta debe existir aunque el
        # honeypot todavía no haya sido activado para sancionar.
        hp_setting_set(guild.id, "honeypot_warning_enabled", "1")
        if publish_messages:
            warning_error = await hp_sync_warning(channel)
            if warning_error:
                return f"Canal Honeypot establecido, pero {warning_error}"
        return "Canal Honeypot establecido y tarjeta sincronizada."

    return "Canal establecido."


async def _setup_get_or_create_system_role(
    guild: discord.Guild,
    key: str,
    label: str,
    default_name: str,
) -> tuple[discord.Role | None, bool, str | None]:
    """Reutiliza o crea un rol del sistema y lo deja vinculado inmediatamente."""
    configured_id = get_guild_role_id(guild.id, key)
    role = guild.get_role(configured_id) if configured_id else None
    created_now = False

    if role is None:
        role = next(
            (candidate for candidate in guild.roles if candidate.name.casefold() == default_name.casefold()),
            None,
        )

    if role is None:
        me = guild.me
        if me is None or not me.guild_permissions.manage_roles:
            return None, False, "El Heraldo no tiene permiso Gestionar roles."
        try:
            role = await guild.create_role(
                name=default_name,
                reason=f"El Heraldo: crear rol del sistema para {label}",
            )
            created_now = True
        except discord.Forbidden:
            return None, False, "Discord rechazó la creación del rol. Revisa Gestionar roles."
        except discord.HTTPException as exc:
            return None, False, f"Discord no pudo crear el rol: {exc}"

    me = guild.me
    if me is None or role.is_default() or role.managed or role >= me.top_role:
        return None, created_now, f"No puedo administrar {role.mention}. Revisa la jerarquía o integraciones."

    guild_resource_set(guild.id, "role", key, role.id)
    if key == "tentado":
        guild_config_set(guild.id, "verify_role_id", str(role.id))
    return role, created_now, None


class HeraldoChannelSetupView(discord.ui.View):
    def __init__(self, guild_id: int, owner_id: int) -> None:
        super().__init__(timeout=900)
        self.guild_id = guild_id
        self.owner_id = owner_id
        self.current_key = "logs"
        self.pending_channels: dict[str, int] = {}

        function_select = discord.ui.Select(
            placeholder="1. Elige qué canal del sistema configurar",
            min_values=1,
            max_values=1,
            options=[
                discord.SelectOption(
                    label=label.split(" ", 1)[-1],
                    value=key,
                    emoji=label.split(" ", 1)[0],
                    description=f"Canal para {label.split(' ', 1)[-1].lower()}",
                )
                for key, (label, _) in HERALDO_CHANNEL_DEFINITIONS.items()
            ],
            row=0,
        )
        function_select.callback = self.select_function
        self.function_select = function_select
        self.add_item(function_select)

        channel_select = discord.ui.ChannelSelect(
            placeholder="2. Selecciona un canal existente",
            channel_types=[discord.ChannelType.text],
            min_values=1,
            max_values=1,
            row=1,
        )
        channel_select.callback = self.select_existing_channel
        self.channel_select = channel_select
        self.add_item(channel_select)

        create_button = discord.ui.Button(label="Crear si no existe", style=discord.ButtonStyle.secondary, row=2)
        create_button.callback = self.create_channel_if_missing
        self.add_item(create_button)

        save_button = discord.ui.Button(label="Guardar cambios", style=discord.ButtonStyle.success, row=3)
        save_button.callback = self.save_changes
        self.add_item(save_button)

        discard_button = discord.ui.Button(label="Descartar cambios", style=discord.ButtonStyle.secondary, row=3)
        discard_button.callback = self.discard_changes
        self.add_item(discard_button)

        back_button = discord.ui.Button(label="Volver", style=discord.ButtonStyle.secondary, row=3)
        back_button.callback = self.back
        self.add_item(back_button)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("Este panel de configuración no es tuyo.", ephemeral=True)
            return False
        return True

    def _label(self, key: str | None = None) -> str:
        return HERALDO_CHANNEL_DEFINITIONS[key or self.current_key][0]

    def _pending_lines(self, guild: discord.Guild) -> list[str]:
        lines: list[str] = []
        for key, channel_id in self.pending_channels.items():
            channel = guild.get_channel(channel_id)
            lines.append(f"{self._label(key)} → {channel.mention if channel else channel_id}")
        return lines

    def _content(self, guild: discord.Guild, notice: str | None = None) -> str:
        label, default_name = HERALDO_CHANNEL_DEFINITIONS[self.current_key]
        text = (
            "🪽 **El Heraldo · Canales del sistema**\n\n"
            + heraldo_channels_summary(guild)
            + f"\n\n**Configurando ahora:** {label}\n"
            f"Selecciona un canal existente o usa **Crear si no existe** para crear **#{default_name}**."
            + _pending_config_text(self._pending_lines(guild))
        )
        if notice:
            text += f"\n\n{notice}"
        return text

    async def select_function(self, interaction: discord.Interaction) -> None:
        self.current_key = self.function_select.values[0]
        label, _ = HERALDO_CHANNEL_DEFINITIONS[self.current_key]
        self.channel_select.placeholder = f"2. Selecciona canal para {label.split(' ', 1)[-1]}"
        await interaction.response.edit_message(content=self._content(interaction.guild), view=self)

    async def select_existing_channel(self, interaction: discord.Interaction) -> None:
        values = interaction.data.get("values") if interaction.data else []
        selected = interaction.guild.get_channel(int(values[0])) if interaction.guild and values else None
        if not isinstance(selected, discord.TextChannel):
            await interaction.response.send_message("No pude localizar ese canal.", ephemeral=True)
            return
        self.pending_channels[self.current_key] = selected.id
        await interaction.response.edit_message(
            content=self._content(interaction.guild, f"Selección pendiente: {self._label()} → {selected.mention}."),
            view=self,
        )

    async def create_channel_if_missing(self, interaction: discord.Interaction) -> None:
        guild = interaction.guild
        label, default_name = HERALDO_CHANNEL_DEFINITIONS[self.current_key]
        target: discord.TextChannel | None = None
        created_now = False

        saved_id = self.pending_channels.get(self.current_key) or get_guild_channel_id(guild.id, self.current_key)
        saved = guild.get_channel(saved_id) if saved_id else None
        if isinstance(saved, discord.TextChannel):
            target = saved

        if target is None:
            target = next(
                (c for c in guild.text_channels if c.name.casefold() == default_name.casefold()),
                None,
            )

        if target is None:
            me = guild.me
            if me is None or not me.guild_permissions.manage_channels:
                await interaction.response.send_message(
                    "El canal no existe y El Heraldo no tiene permiso Gestionar canales para crearlo.",
                    ephemeral=True,
                )
                return
            await interaction.response.defer(ephemeral=True)
            try:
                target = await guild.create_text_channel(
                    default_name,
                    reason=f"El Heraldo: crear canal del sistema para {label}",
                )
                created_now = True
            except discord.Forbidden:
                await interaction.followup.send(
                    "Discord rechazó la creación del canal. Revisa Gestionar canales.",
                    ephemeral=True,
                )
                return
            except discord.HTTPException:
                await interaction.followup.send(
                    "Discord no pudo crear el canal en este momento.",
                    ephemeral=True,
                )
                return
        else:
            await interaction.response.defer(ephemeral=True)

        try:
            note = await _setup_apply_system_channel(
                guild,
                self.current_key,
                target,
                publish_messages=True,
            )
        except discord.HTTPException as exc:
            await interaction.followup.send(
                f"El canal quedó disponible, pero no pude terminar de configurarlo: `{exc}`.",
                ephemeral=True,
            )
            return

        self.pending_channels.pop(self.current_key, None)
        action = "Creé" if created_now else "Reutilicé"
        await interaction.edit_original_response(
            content=self._content(
                guild,
                f"{action} {target.mention} y quedó configurado inmediatamente para {label}. {note}",
            ),
            view=self,
        )

    async def save_changes(self, interaction: discord.Interaction) -> None:
        if not self.pending_channels:
            await interaction.response.send_message("No hay cambios pendientes.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)
        notes: list[str] = []
        saved_count = 0
        for key, channel_id in list(self.pending_channels.items()):
            channel = interaction.guild.get_channel(channel_id)
            if not isinstance(channel, discord.TextChannel):
                notes.append(f"{self._label(key)}: el canal ya no existe.")
                continue
            try:
                note = await _setup_apply_system_channel(
                    interaction.guild,
                    key,
                    channel,
                    publish_messages=True,
                )
                notes.append(f"{self._label(key)}: {note}")
                saved_count += 1
            except discord.HTTPException as exc:
                notes.append(f"{self._label(key)}: error de Discord `{exc}`.")
        self.pending_channels.clear()
        await interaction.edit_original_response(
            content=self._content(
                interaction.guild,
                f"Guardados {saved_count} cambio(s) de canales.\n" + "\n".join(f"• {note}" for note in notes),
            ),
            view=self,
        )

    async def discard_changes(self, interaction: discord.Interaction) -> None:
        self.pending_channels.clear()
        await interaction.response.edit_message(
            content=self._content(interaction.guild, "Cambios pendientes descartados."),
            view=self,
        )

    async def back(self, interaction: discord.Interaction) -> None:
        await heraldo_setup_go_home(interaction, self.guild_id, self.owner_id)



class HeraldoRoleSetupView(discord.ui.View):
    def __init__(self, guild_id: int, owner_id: int) -> None:
        super().__init__(timeout=900)
        self.guild_id = guild_id
        self.owner_id = owner_id
        self.pending_roles: dict[str, int] = {}
        definitions = (
            ("sin_verificar", "Sin Verificar", "Sin Verificar"),
            ("tentado", "Verificación", "Tentad@"),
            ("condenado", "Condenado", "Condenado"),
        )
        for row_index, (key, label, _default_name) in enumerate(definitions):
            select = discord.ui.RoleSelect(
                placeholder=f"Seleccionar rol · {label}",
                min_values=1,
                max_values=1,
                row=row_index,
            )
            select.callback = self._make_callback(key, label)
            self.add_item(select)

        # La fila 3 admite cinco botones: los tres creadores + Guardar + Descartar.
        for key, label, default_name in definitions:
            create_button = discord.ui.Button(
                label=f"Crear {label}",
                style=discord.ButtonStyle.secondary,
                row=3,
            )
            create_button.callback = self._make_create_callback(key, label, default_name)
            self.add_item(create_button)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("Este panel de configuración no es tuyo.", ephemeral=True)
            return False
        return True

    def _pending_text(self, guild: discord.Guild) -> str:
        items = []
        for key, role_id in self.pending_roles.items():
            role = guild.get_role(role_id)
            items.append(f"{key.replace('_', ' ').title()} → {role.mention if role else role_id}")
        return _pending_config_text(items)

    def _make_callback(self, key: str, label: str):
        async def callback(interaction: discord.Interaction) -> None:
            values = interaction.data.get("values") if interaction.data else None
            role = interaction.guild.get_role(int(values[0])) if interaction.guild and values else None
            if role is None:
                await interaction.response.send_message("No pude localizar ese rol.", ephemeral=True)
                return
            if role.is_default() or role.managed or role >= interaction.guild.me.top_role:
                await interaction.response.send_message(
                    "Ese rol no puede ser administrado por El Heraldo. Revisa jerarquía o integraciones.",
                    ephemeral=True,
                )
                return
            self.pending_roles[key] = role.id
            await interaction.response.edit_message(
                content=(
                    "🪽 **El Heraldo · Roles del sistema**\n\n"
                    "Las selecciones no se aplican hasta pulsar **Guardar cambios**."
                    + self._pending_text(interaction.guild)
                ),
                view=self,
            )
        return callback

    def _make_create_callback(self, key: str, label: str, default_name: str):
        async def callback(interaction: discord.Interaction) -> None:
            guild = interaction.guild
            configured_id = self.pending_roles.get(key) or get_guild_role_id(guild.id, key)
            role = guild.get_role(configured_id) if configured_id else None
            created_now = False

            if role is None:
                role = next(
                    (candidate for candidate in guild.roles if candidate.name.casefold() == default_name.casefold()),
                    None,
                )

            if role is None:
                me = guild.me
                if me is None or not me.guild_permissions.manage_roles:
                    await interaction.response.send_message(
                        "El rol no existe y El Heraldo no tiene permiso Gestionar roles para crearlo.",
                        ephemeral=True,
                    )
                    return
                await interaction.response.defer(ephemeral=True)
                try:
                    role = await guild.create_role(
                        name=default_name,
                        reason=f"El Heraldo: crear rol del sistema para {label}",
                    )
                    created_now = True
                except discord.Forbidden:
                    await interaction.followup.send(
                        "Discord rechazó la creación del rol. Revisa Gestionar roles.",
                        ephemeral=True,
                    )
                    return
                except discord.HTTPException:
                    await interaction.followup.send(
                        "Discord no pudo crear el rol en este momento.",
                        ephemeral=True,
                    )
                    return
            else:
                await interaction.response.defer(ephemeral=True)

            if role.is_default() or role.managed or role >= guild.me.top_role:
                await interaction.followup.send(
                    f"No puedo administrar {role.mention}. Revisa la jerarquía o integraciones.",
                    ephemeral=True,
                )
                return

            guild_resource_set(self.guild_id, "role", key, role.id)
            if key == "tentado":
                guild_config_set(self.guild_id, "verify_role_id", str(role.id))

            self.pending_roles.pop(key, None)
            action = "Creé" if created_now else "Reutilicé"
            await interaction.edit_original_response(
                content=(
                    "🪽 **El Heraldo · Roles del sistema**\n\n"
                    f"{action} {role.mention} y quedó configurado inmediatamente como **{label}**."
                    + self._pending_text(guild)
                ),
                view=self,
            )
        return callback

    @discord.ui.button(label="Guardar cambios", style=discord.ButtonStyle.success, row=3)
    async def save_changes(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if not self.pending_roles:
            await interaction.response.send_message("No hay cambios pendientes.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)
        for key, role_id in self.pending_roles.items():
            guild_resource_set(self.guild_id, "role", key, role_id)
            if key == "tentado":
                guild_config_set(self.guild_id, "verify_role_id", str(role_id))
        count = len(self.pending_roles)
        self.pending_roles.clear()
        await interaction.edit_original_response(
            content=f"🪽 **El Heraldo · Roles del sistema**\n\nGuardados {count} cambio(s).",
            view=self,
        )

    @discord.ui.button(label="Descartar cambios", style=discord.ButtonStyle.secondary, row=3)
    async def discard_changes(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        self.pending_roles.clear()
        await interaction.response.edit_message(
            content="🪽 **El Heraldo · Roles del sistema**\n\nCambios pendientes descartados.",
            view=self,
        )

    @discord.ui.button(label="Volver", style=discord.ButtonStyle.secondary, row=4)
    async def back(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await heraldo_setup_go_home(interaction, self.guild_id, self.owner_id)


class JoinRolesDelayModal(discord.ui.Modal, title="Join Roles · Delay"):
    delay = discord.ui.TextInput(
        label="Retraso antes de asignar (segundos)",
        required=True,
        max_length=6,
        placeholder="0 = inmediato",
    )

    def __init__(self, guild_id: int) -> None:
        super().__init__()
        self.guild_id = guild_id
        self.delay.default = str(get_join_roles_delay(guild_id))

    async def on_submit(self, interaction: discord.Interaction) -> None:
        try:
            seconds = int(str(self.delay).strip())
            if seconds < 0 or seconds > 86400:
                raise ValueError
        except ValueError:
            await interaction.response.send_message(
                "❌ El delay debe estar entre 0 y 86400 segundos.", ephemeral=True
            )
            return
        guild_config_set(self.guild_id, "join_roles_delay_seconds", str(seconds))
        await interaction.response.send_message(f"✅ Delay guardado: **{seconds} s**.", ephemeral=True)


class JoinRolesScheduleModal(discord.ui.Modal, title="Join Roles · Sync periódico"):
    minutes = discord.ui.TextInput(
        label="Intervalo en minutos",
        required=True,
        max_length=6,
        placeholder="0 = desactivar",
    )

    def __init__(self, guild_id: int) -> None:
        super().__init__()
        self.guild_id = guild_id
        self.minutes.default = str(get_join_sync_interval_minutes(guild_id))

    async def on_submit(self, interaction: discord.Interaction) -> None:
        try:
            minutes = int(str(self.minutes).strip())
            if minutes < 0 or minutes > 10080:
                raise ValueError
            if minutes and minutes < 10:
                await interaction.response.send_message(
                    "❌ El intervalo mínimo para Sync periódico es **10 minutos**.",
                    ephemeral=True,
                )
                return
        except ValueError:
            await interaction.response.send_message(
                "❌ Usa un valor entre 0 y 10080 minutos.", ephemeral=True
            )
            return
        guild_config_set(self.guild_id, "join_sync_interval_minutes", str(minutes))
        if minutes:
            set_join_sync_last(self.guild_id)
        await interaction.response.send_message(
            "✅ Sync periódico " + (f"configurado cada **{minutes} min**." if minutes else "desactivado."),
            ephemeral=True,
        )


class _JoinRolesOwnedView(discord.ui.View):
    def __init__(self, guild_id: int, owner_id: int) -> None:
        super().__init__(timeout=900)
        self.guild_id = guild_id
        self.owner_id = owner_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message(
                "Este panel de configuración no es tuyo.", ephemeral=True
            )
            return False
        return True


class HeraldoJoinRolesSetupView(_JoinRolesOwnedView):
    @discord.ui.button(label="Basic setup", style=discord.ButtonStyle.primary, row=0)
    async def basic(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await interaction.response.edit_message(
            content="🚪 **El Heraldo · Join Roles · Basic setup**\n\n" + join_roles_basic_summary(interaction.guild),
            view=HeraldoJoinRolesBasicView(self.guild_id, self.owner_id),
        )

    @discord.ui.button(label="User specific roles", style=discord.ButtonStyle.secondary, row=0)
    async def users(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await interaction.response.edit_message(
            content="🚪 **El Heraldo · Join Roles · User specific roles**\n\n" + join_roles_users_summary(interaction.guild),
            view=HeraldoJoinRolesUsersView(self.guild_id, self.owner_id),
        )

    @discord.ui.button(label="Bot roles", style=discord.ButtonStyle.secondary, row=1)
    async def bots(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await interaction.response.edit_message(
            content="🚪 **El Heraldo · Join Roles · Bot roles**\n\n" + join_roles_bots_summary(interaction.guild),
            view=HeraldoJoinRolesBotsView(self.guild_id, self.owner_id),
        )

    @discord.ui.button(label="Synchronization", style=discord.ButtonStyle.secondary, row=1)
    async def synchronization(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await interaction.response.edit_message(
            content="🚪 **El Heraldo · Join Roles · Synchronization**\n\n" + join_roles_sync_summary(interaction.guild),
            view=HeraldoJoinRolesSyncView(self.guild_id, self.owner_id),
        )

    @discord.ui.button(label="Volver", style=discord.ButtonStyle.secondary, row=2)
    async def back(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await heraldo_setup_go_home(interaction, self.guild_id, self.owner_id)



class HeraldoJoinRolesBasicView(_JoinRolesOwnedView):
    def __init__(self, guild_id: int, owner_id: int) -> None:
        super().__init__(guild_id, owner_id)
        self.pending_role_ids: list[int] | None = None
        self.pending_screening: bool | None = None
        self.pending_enabled: bool | None = None
        selector = discord.ui.RoleSelect(
            placeholder="Roles asignados a todos los usuarios nuevos",
            min_values=0,
            max_values=JOIN_ROLES_MAX,
            row=0,
        )
        selector.callback = self.select_roles
        self.add_item(selector)

    def _pending(self, guild: discord.Guild) -> str:
        items: list[str] = []
        if self.pending_role_ids is not None:
            roles = [guild.get_role(rid) for rid in self.pending_role_ids]
            items.append("Join Roles → " + (", ".join(r.mention for r in roles if r) or "ninguno"))
        if self.pending_screening is not None:
            items.append(f"Rules Screening → {'sí' if self.pending_screening else 'no'}")
        if self.pending_enabled is not None:
            items.append(f"Sistema → {'activo' if self.pending_enabled else 'desactivado'}")
        return _pending_config_text(items)

    async def select_roles(self, interaction: discord.Interaction) -> None:
        values = interaction.data.get("values") if interaction.data else []
        roles = [interaction.guild.get_role(int(value)) for value in values]
        roles = [role for role in roles if role is not None]
        me = interaction.guild.me
        invalid = [role for role in roles if role.managed or me is None or role >= me.top_role]
        if invalid:
            await interaction.response.send_message(
                "No puedo asignar: " + ", ".join(role.mention for role in invalid), ephemeral=True
            )
            return
        self.pending_role_ids = [role.id for role in roles]
        await interaction.response.edit_message(
            content="🚪 **El Heraldo · Join Roles · Basic setup**\n\n"
            + join_roles_basic_summary(interaction.guild)
            + self._pending(interaction.guild),
            view=self,
        )

    @discord.ui.button(label="Rules Screening", style=discord.ButtonStyle.secondary, row=1)
    async def screening(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        current = self.pending_screening if self.pending_screening is not None else join_roles_wait_screening(self.guild_id)
        self.pending_screening = not current
        await interaction.response.edit_message(
            content="🚪 **El Heraldo · Join Roles · Basic setup**\n\n"
            + join_roles_basic_summary(interaction.guild)
            + self._pending(interaction.guild),
            view=self,
        )

    @discord.ui.button(label="Delay", style=discord.ButtonStyle.secondary, row=1)
    async def delay(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await interaction.response.send_modal(JoinRolesDelayModal(self.guild_id))

    @discord.ui.button(label="Activar", style=discord.ButtonStyle.success, row=2)
    async def enable(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        prospective_roles = self.pending_role_ids if self.pending_role_ids is not None else get_join_role_ids(self.guild_id)
        if not prospective_roles:
            await interaction.response.send_message("Añade al menos un Join Role.", ephemeral=True)
            return
        self.pending_enabled = True
        await interaction.response.edit_message(
            content="🚪 **El Heraldo · Join Roles · Basic setup**\n\n"
            + join_roles_basic_summary(interaction.guild)
            + self._pending(interaction.guild),
            view=self,
        )

    @discord.ui.button(label="Desactivar", style=discord.ButtonStyle.danger, row=2)
    async def disable(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        self.pending_enabled = False
        await interaction.response.edit_message(
            content="🚪 **El Heraldo · Join Roles · Basic setup**\n\n"
            + join_roles_basic_summary(interaction.guild)
            + self._pending(interaction.guild),
            view=self,
        )

    @discord.ui.button(label="Guardar cambios", style=discord.ButtonStyle.success, row=3)
    async def save_changes(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if self.pending_role_ids is None and self.pending_screening is None and self.pending_enabled is None:
            await interaction.response.send_message("No hay cambios pendientes.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)
        if self.pending_role_ids is not None:
            set_join_role_ids(self.guild_id, self.pending_role_ids)
        if self.pending_screening is not None:
            guild_config_set(self.guild_id, "join_roles_wait_screening", "1" if self.pending_screening else "0")
        if self.pending_enabled is not None:
            guild_config_set(self.guild_id, "join_roles_enabled", "1" if self.pending_enabled else "0")
        self.pending_role_ids = None
        self.pending_screening = None
        self.pending_enabled = None
        await interaction.edit_original_response(
            content="🚪 **El Heraldo · Join Roles · Basic setup**\n\n"
            + join_roles_basic_summary(interaction.guild)
            + "\n\nCambios guardados.",
            view=self,
        )

    @discord.ui.button(label="Descartar cambios", style=discord.ButtonStyle.secondary, row=3)
    async def discard_changes(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        self.pending_role_ids = None
        self.pending_screening = None
        self.pending_enabled = None
        await interaction.response.edit_message(
            content="🚪 **El Heraldo · Join Roles · Basic setup**\n\n" + join_roles_basic_summary(interaction.guild),
            view=self,
        )

    @discord.ui.button(label="Join Roles", style=discord.ButtonStyle.secondary, row=4)
    async def back(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await interaction.response.edit_message(
            content="🚪 **El Heraldo · Join Roles**\n\n" + join_roles_summary(interaction.guild),
            view=HeraldoJoinRolesSetupView(self.guild_id, self.owner_id),
        )


class JoinRolesUserIdModal(discord.ui.Modal, title="Join Roles · Usuario específico"):
    user_id_input = discord.ui.TextInput(
        label="Discord User ID",
        required=True,
        max_length=24,
        placeholder="Ej.: 123456789012345678",
    )

    def __init__(self, parent_view: "HeraldoJoinRolesUsersView") -> None:
        super().__init__()
        self.parent_view = parent_view
        if parent_view.selected_user_id:
            self.user_id_input.default = str(parent_view.selected_user_id)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        raw = str(self.user_id_input).strip()
        try:
            user_id = int(raw)
            if user_id <= 0:
                raise ValueError
        except ValueError:
            await interaction.response.send_message(
                "❌ Introduce un Discord User ID numérico válido.", ephemeral=True
            )
            return
        self.parent_view.selected_user_id = user_id
        await interaction.response.send_message(
            f"✅ Usuario objetivo guardado: <@{user_id}> (\`{user_id}\`). "
            "Ahora selecciona sus roles y pulsa **Guardar usuario**.",
            ephemeral=True,
        )



class HeraldoJoinRolesUsersView(_JoinRolesOwnedView):
    def __init__(self, guild_id: int, owner_id: int) -> None:
        super().__init__(guild_id, owner_id)
        self.selected_user_id: int | None = None
        self.selected_role_ids: list[int] = []
        self.pending_remove_after: bool | None = None

        role_select = discord.ui.RoleSelect(
            placeholder="Roles adicionales para ese User ID",
            min_values=1,
            max_values=JOIN_ROLES_MAX,
            row=1,
        )
        role_select.callback = self.select_roles
        self.add_item(role_select)

    def _content(self, guild: discord.Guild) -> str:
        items: list[str] = []
        if self.selected_user_id is not None and self.selected_role_ids:
            roles = [guild.get_role(role_id) for role_id in self.selected_role_ids]
            items.append(
                f"Usuario <@{self.selected_user_id}> → "
                + ", ".join(role.mention for role in roles if role is not None)
            )
        if self.pending_remove_after is not None:
            items.append(f"Remove after join → {'sí' if self.pending_remove_after else 'no'}")
        return (
            "🚪 **El Heraldo · Join Roles · User specific roles**\n\n"
            + join_roles_users_summary(guild)
            + _pending_config_text(items)
        )

    @discord.ui.button(label="Definir User ID", style=discord.ButtonStyle.primary, row=0)
    async def set_user_id(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await interaction.response.send_modal(JoinRolesUserIdModal(self))

    async def select_roles(self, interaction: discord.Interaction) -> None:
        values = interaction.data.get("values") if interaction.data else []
        self.selected_role_ids = [int(value) for value in values]
        await interaction.response.edit_message(content=self._content(interaction.guild), view=self)

    @discord.ui.button(label="Guardar usuario", style=discord.ButtonStyle.success, row=2)
    async def save_user(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if self.selected_user_id is None or not self.selected_role_ids:
            await interaction.response.send_message("Selecciona primero un usuario y uno o más roles.", ephemeral=True)
            return
        roles = [interaction.guild.get_role(role_id) for role_id in self.selected_role_ids]
        roles = [role for role in roles if role is not None]
        me = interaction.guild.me
        invalid = [role for role in roles if role.managed or me is None or role >= me.top_role]
        if invalid:
            await interaction.response.send_message("No puedo asignar: " + ", ".join(role.mention for role in invalid), ephemeral=True)
            return
        set_join_specific_user_roles(self.guild_id, self.selected_user_id, [role.id for role in roles])
        self.selected_role_ids = []
        await interaction.response.edit_message(content=self._content(interaction.guild) + "\n\nUsuario guardado.", view=self)

    @discord.ui.button(label="Quitar usuario", style=discord.ButtonStyle.danger, row=2)
    async def remove_user(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if self.selected_user_id is None:
            await interaction.response.send_message("Selecciona primero un usuario.", ephemeral=True)
            return
        existed = remove_join_specific_user(self.guild_id, self.selected_user_id)
        await interaction.response.edit_message(
            content=self._content(interaction.guild)
            + ("\n\nUsuario eliminado de la lista." if existed else "\n\nEse usuario no estaba en la lista."),
            view=self,
        )

    @discord.ui.button(label="Remove after join", style=discord.ButtonStyle.secondary, row=3)
    async def remove_after(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        current = self.pending_remove_after if self.pending_remove_after is not None else join_roles_remove_specific_after_join(self.guild_id)
        self.pending_remove_after = not current
        await interaction.response.edit_message(content=self._content(interaction.guild), view=self)

    @discord.ui.button(label="Guardar cambios", style=discord.ButtonStyle.success, row=3)
    async def save_changes(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if self.pending_remove_after is None:
            await interaction.response.send_message("No hay cambios de configuración pendientes.", ephemeral=True)
            return
        guild_config_set(self.guild_id, "join_roles_specific_remove_after_join", "1" if self.pending_remove_after else "0")
        self.pending_remove_after = None
        await interaction.response.edit_message(content=self._content(interaction.guild) + "\n\nCambios guardados.", view=self)

    @discord.ui.button(label="Descartar cambios", style=discord.ButtonStyle.secondary, row=4)
    async def discard_changes(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        self.pending_remove_after = None
        await interaction.response.edit_message(content=self._content(interaction.guild), view=self)

    @discord.ui.button(label="Join Roles", style=discord.ButtonStyle.secondary, row=4)
    async def back(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await interaction.response.edit_message(
            content="🚪 **El Heraldo · Join Roles**\n\n" + join_roles_summary(interaction.guild),
            view=HeraldoJoinRolesSetupView(self.guild_id, self.owner_id),
        )


class HeraldoJoinRolesBotsView(_JoinRolesOwnedView):
    def __init__(self, guild_id: int, owner_id: int) -> None:
        super().__init__(guild_id, owner_id)
        self.pending_role_ids: list[int] | None = None
        self.pending_enabled: bool | None = None
        self.pending_delay: bool | None = None
        self.pending_different: bool | None = None
        selector = discord.ui.RoleSelect(
            placeholder="Roles alternativos para bots",
            min_values=0,
            max_values=JOIN_ROLES_MAX,
            row=0,
        )
        selector.callback = self.select_bot_roles
        self.add_item(selector)

    def _pending(self, guild: discord.Guild) -> str:
        items = []
        if self.pending_role_ids is not None:
            roles = [guild.get_role(rid) for rid in self.pending_role_ids]
            items.append("Roles de bots → " + (", ".join(r.mention for r in roles if r) or "ninguno"))
        if self.pending_enabled is not None:
            items.append(f"Asignar a bots → {'sí' if self.pending_enabled else 'no'}")
        if self.pending_delay is not None:
            items.append(f"Aplicar delay → {'sí' if self.pending_delay else 'no'}")
        if self.pending_different is not None:
            items.append(f"Roles diferentes → {'sí' if self.pending_different else 'no'}")
        return _pending_config_text(items)

    async def select_bot_roles(self, interaction: discord.Interaction) -> None:
        values = interaction.data.get("values") if interaction.data else []
        roles = [interaction.guild.get_role(int(value)) for value in values]
        roles = [role for role in roles if role is not None]
        me = interaction.guild.me
        invalid = [role for role in roles if role.managed or me is None or role >= me.top_role]
        if invalid:
            await interaction.response.send_message("No puedo asignar: " + ", ".join(role.mention for role in invalid), ephemeral=True)
            return
        self.pending_role_ids = [role.id for role in roles]
        await interaction.response.edit_message(
            content="🚪 **El Heraldo · Join Roles · Bot roles**\n\n" + join_roles_bots_summary(interaction.guild) + self._pending(interaction.guild),
            view=self,
        )

    @discord.ui.button(label="Assign for bots", style=discord.ButtonStyle.secondary, row=1)
    async def bot_enabled(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        current = self.pending_enabled if self.pending_enabled is not None else join_roles_bot_enabled(self.guild_id)
        self.pending_enabled = not current
        await interaction.response.edit_message(content="🚪 **El Heraldo · Join Roles · Bot roles**\n\n" + join_roles_bots_summary(interaction.guild) + self._pending(interaction.guild), view=self)

    @discord.ui.button(label="Apply delay", style=discord.ButtonStyle.secondary, row=1)
    async def bot_delay(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        current = self.pending_delay if self.pending_delay is not None else join_roles_bot_apply_delay(self.guild_id)
        self.pending_delay = not current
        await interaction.response.edit_message(content="🚪 **El Heraldo · Join Roles · Bot roles**\n\n" + join_roles_bots_summary(interaction.guild) + self._pending(interaction.guild), view=self)

    @discord.ui.button(label="Different roles", style=discord.ButtonStyle.secondary, row=1)
    async def bot_different(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        current = self.pending_different if self.pending_different is not None else join_roles_bot_use_different(self.guild_id)
        target = not current
        prospective_roles = self.pending_role_ids if self.pending_role_ids is not None else get_join_bot_role_ids(self.guild_id)
        if target and not prospective_roles:
            await interaction.response.send_message("Selecciona primero uno o más roles alternativos para bots.", ephemeral=True)
            return
        self.pending_different = target
        await interaction.response.edit_message(content="🚪 **El Heraldo · Join Roles · Bot roles**\n\n" + join_roles_bots_summary(interaction.guild) + self._pending(interaction.guild), view=self)

    @discord.ui.button(label="Guardar cambios", style=discord.ButtonStyle.success, row=2)
    async def save_changes(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if all(v is None for v in (self.pending_role_ids, self.pending_enabled, self.pending_delay, self.pending_different)):
            await interaction.response.send_message("No hay cambios pendientes.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)
        if self.pending_role_ids is not None:
            set_join_bot_role_ids(self.guild_id, self.pending_role_ids)
        if self.pending_enabled is not None:
            guild_config_set(self.guild_id, "join_roles_bot_enabled", "1" if self.pending_enabled else "0")
        if self.pending_delay is not None:
            guild_config_set(self.guild_id, "join_roles_bot_apply_delay", "1" if self.pending_delay else "0")
        if self.pending_different is not None:
            guild_config_set(self.guild_id, "join_roles_bot_use_different", "1" if self.pending_different else "0")
        self.pending_role_ids = self.pending_enabled = self.pending_delay = self.pending_different = None
        await interaction.edit_original_response(content="🚪 **El Heraldo · Join Roles · Bot roles**\n\n" + join_roles_bots_summary(interaction.guild) + "\n\nCambios guardados.", view=self)

    @discord.ui.button(label="Descartar cambios", style=discord.ButtonStyle.secondary, row=2)
    async def discard_changes(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        self.pending_role_ids = self.pending_enabled = self.pending_delay = self.pending_different = None
        await interaction.response.edit_message(content="🚪 **El Heraldo · Join Roles · Bot roles**\n\n" + join_roles_bots_summary(interaction.guild), view=self)

    @discord.ui.button(label="Join Roles", style=discord.ButtonStyle.secondary, row=3)
    async def back(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await interaction.response.edit_message(
            content="🚪 **El Heraldo · Join Roles**\n\n" + join_roles_summary(interaction.guild),
            view=HeraldoJoinRolesSetupView(self.guild_id, self.owner_id),
        )



class HeraldoJoinRolesSyncView(_JoinRolesOwnedView):
    def __init__(self, guild_id: int, owner_id: int) -> None:
        super().__init__(guild_id, owner_id)
        self.pending_excluded: list[int] | None = None
        selector = discord.ui.RoleSelect(
            placeholder="Roles que excluyen miembros del Sync",
            min_values=0,
            max_values=JOIN_ROLES_MAX,
            row=0,
        )
        selector.callback = self.select_excluded
        self.add_item(selector)

    async def select_excluded(self, interaction: discord.Interaction) -> None:
        values = interaction.data.get("values") if interaction.data else []
        self.pending_excluded = [int(value) for value in values]
        roles = [interaction.guild.get_role(rid) for rid in self.pending_excluded]
        await interaction.response.edit_message(
            content="🚪 **El Heraldo · Join Roles · Synchronization**\n\n"
            + join_roles_sync_summary(interaction.guild)
            + _pending_config_text(["Excluir del Sync → " + (", ".join(r.mention for r in roles if r) or "ninguno")]),
            view=self,
        )

    @discord.ui.button(label="Sync now", style=discord.ButtonStyle.primary, row=1)
    async def sync_now(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if self.pending_excluded is not None:
            await interaction.response.send_message("Guarda o descarta los cambios pendientes antes de ejecutar Sync now.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True, thinking=True)
        assigned, skipped, errors = await sync_join_roles(interaction.guild)
        msg = f"Sync terminado. {assigned} miembro(s) recibieron roles; {skipped} no necesitaron cambios."
        if errors:
            msg += f"\n{len(errors)} error(es) por permisos/jerarquía."
        await interaction.followup.send(msg, ephemeral=True)

    @discord.ui.button(label="Schedule", style=discord.ButtonStyle.secondary, row=1)
    async def schedule(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await interaction.response.send_modal(JoinRolesScheduleModal(self.guild_id))

    @discord.ui.button(label="Guardar cambios", style=discord.ButtonStyle.success, row=2)
    async def save_changes(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if self.pending_excluded is None:
            await interaction.response.send_message("No hay cambios pendientes.", ephemeral=True)
            return
        set_join_sync_excluded_role_ids(self.guild_id, self.pending_excluded)
        self.pending_excluded = None
        await interaction.response.edit_message(
            content="🚪 **El Heraldo · Join Roles · Synchronization**\n\n" + join_roles_sync_summary(interaction.guild) + "\n\nCambios guardados.",
            view=self,
        )

    @discord.ui.button(label="Descartar cambios", style=discord.ButtonStyle.secondary, row=2)
    async def discard_changes(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        self.pending_excluded = None
        await interaction.response.edit_message(content="🚪 **El Heraldo · Join Roles · Synchronization**\n\n" + join_roles_sync_summary(interaction.guild), view=self)

    @discord.ui.button(label="Join Roles", style=discord.ButtonStyle.secondary, row=3)
    async def back(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await interaction.response.edit_message(
            content="🚪 **El Heraldo · Join Roles**\n\n" + join_roles_summary(interaction.guild),
            view=HeraldoJoinRolesSetupView(self.guild_id, self.owner_id),
        )


class OrientationEmbedModal(discord.ui.Modal, title="Editar tarjeta de orientación"):
    title_input = discord.ui.TextInput(
        label="Título",
        required=True,
        max_length=256,
    )
    intro_input = discord.ui.TextInput(
        label="Texto antes de las opciones",
        style=discord.TextStyle.paragraph,
        required=True,
        max_length=1000,
    )
    details_input = discord.ui.TextInput(
        label="Texto después de las opciones",
        style=discord.TextStyle.paragraph,
        required=True,
        max_length=3000,
    )
    color_input = discord.ui.TextInput(
        label="Color HEX",
        required=True,
        max_length=7,
    )
    footer_input = discord.ui.TextInput(
        label="Footer",
        required=False,
        max_length=2048,
    )

    def __init__(self, guild: discord.Guild) -> None:
        super().__init__()
        self.guild_id = guild.id
        self.title_input.default = get_orientation_embed_title(guild.id)
        self.intro_input.default = get_orientation_embed_intro(guild.id)
        self.details_input.default = get_orientation_embed_details(guild.id)
        self.color_input.default = f"{get_orientation_embed_color(guild.id):06X}"
        self.footer_input.default = get_orientation_embed_footer(guild)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        title = str(self.title_input).strip()
        intro = str(self.intro_input).strip()
        details = str(self.details_input).strip()
        color = str(self.color_input).strip().lstrip("#")
        footer = str(self.footer_input).strip()

        if not title or not intro or not details:
            await interaction.response.send_message(
                "❌ Título y textos de la tarjeta no pueden quedar vacíos.",
                ephemeral=True,
            )
            return
        if not re.fullmatch(r"[0-9a-fA-F]{6}", color):
            await interaction.response.send_message(
                "❌ El color debe ser HEX de 6 dígitos, por ejemplo `19A7E0`.",
                ephemeral=True,
            )
            return

        guild_config_set(self.guild_id, "orientation_embed_title", title)
        guild_config_set(self.guild_id, "orientation_embed_intro", intro)
        guild_config_set(self.guild_id, "orientation_embed_details", details)
        guild_config_set(self.guild_id, "orientation_embed_color", color.upper())
        guild_config_set(self.guild_id, "orientation_embed_footer", footer)

        await interaction.response.defer(ephemeral=True)
        note = "Tarjeta guardada."
        if orientation_enabled(self.guild_id):
            ok, sync_note = await ensure_orientation_system(interaction.guild)
            note = sync_note if ok else f"Guardé el texto, pero no pude actualizar la tarjeta: {sync_note}"
        await interaction.followup.send(f"✅ {note}", ephemeral=True)



class HeraldoOrientationSetupView(discord.ui.View):
    def __init__(self, guild_id: int, owner_id: int) -> None:
        super().__init__(timeout=900)
        self.guild_id = guild_id
        self.owner_id = owner_id
        self.pending_channel_id: int | None = None
        self.pending_bindings: list[dict[str, object]] | None = None
        self.pending_enabled: bool | None = None

        channel_select = discord.ui.ChannelSelect(
            placeholder="Selecciona el canal de roles/orientación",
            channel_types=[discord.ChannelType.text],
            min_values=1,
            max_values=1,
            row=0,
        )
        channel_select.callback = self.select_channel
        self.add_item(channel_select)

        role_select = discord.ui.RoleSelect(
            placeholder="Selecciona 1–6 roles existentes con emoji",
            min_values=ORIENTATION_MIN_ROLES,
            max_values=ORIENTATION_MAX_ROLES,
            row=1,
        )
        role_select.callback = self.select_roles
        self.add_item(role_select)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("Este panel de configuración no es tuyo.", ephemeral=True)
            return False
        return True

    def _content(self, guild: discord.Guild) -> str:
        items: list[str] = []
        if self.pending_channel_id is not None:
            channel = guild.get_channel(self.pending_channel_id)
            items.append(f"Canal → {channel.mention if channel else self.pending_channel_id}")
        if self.pending_bindings is not None:
            roles = [guild.get_role(int(item["role_id"])) for item in self.pending_bindings]
            items.append("Roles → " + ", ".join(role.mention for role in roles if role is not None))
        if self.pending_enabled is not None:
            items.append(f"Orientación → {'activa' if self.pending_enabled else 'desactivada'}")
        return "🧭 **El Heraldo · Roles de orientación**\n\n" + orientation_setup_summary(guild) + _pending_config_text(items)

    async def select_channel(self, interaction: discord.Interaction) -> None:
        values = interaction.data.get("values") if interaction.data else []
        channel = interaction.guild.get_channel(int(values[0])) if interaction.guild and values else None
        if not isinstance(channel, discord.TextChannel):
            await interaction.response.send_message("No pude localizar ese canal.", ephemeral=True)
            return
        self.pending_channel_id = channel.id
        await interaction.response.edit_message(content=self._content(interaction.guild), view=self)

    async def select_roles(self, interaction: discord.Interaction) -> None:
        values = interaction.data.get("values") if interaction.data else []
        guild = interaction.guild
        if guild is None:
            await interaction.response.send_message("No pude resolver este servidor.", ephemeral=True)
            return
        roles = [guild.get_role(int(value)) for value in values]
        roles = [role for role in roles if role is not None]
        if not (ORIENTATION_MIN_ROLES <= len(roles) <= ORIENTATION_MAX_ROLES):
            await interaction.response.send_message("Selecciona entre 1 y 6 roles.", ephemeral=True)
            return
        me = guild.me
        blocked = [role.mention for role in roles if me is None or role >= me.top_role or role.managed]
        if blocked:
            await interaction.response.send_message("No puedo administrar estos roles: " + ", ".join(blocked), ephemeral=True)
            return

        used: set[str] = set()
        bindings: list[dict[str, object]] = []
        missing_emoji: list[str] = []
        duplicate_emoji: list[str] = []
        for role in roles:
            emoji = _orientation_role_emoji(role)
            if not emoji:
                missing_emoji.append(role.mention)
                continue
            key = _orientation_emoji_key(emoji)
            if key in used:
                duplicate_emoji.append(f"{role.mention} ({emoji})")
                continue
            used.add(key)
            bindings.append({"role_id": role.id, "emoji": emoji})
        if missing_emoji:
            await interaction.response.send_message("Estos roles no contienen un emoji utilizable: " + ", ".join(missing_emoji), ephemeral=True)
            return
        if duplicate_emoji:
            await interaction.response.send_message("Cada Reaction Role necesita un emoji diferente: " + ", ".join(duplicate_emoji), ephemeral=True)
            return
        self.pending_bindings = bindings
        await interaction.response.edit_message(content=self._content(guild), view=self)

    @discord.ui.button(label="Activar / reparar", style=discord.ButtonStyle.success, row=2)
    async def activate(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        self.pending_enabled = True
        await interaction.response.edit_message(content=self._content(interaction.guild), view=self)

    @discord.ui.button(label="Desactivar", style=discord.ButtonStyle.danger, row=2)
    async def deactivate(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        self.pending_enabled = False
        await interaction.response.edit_message(content=self._content(interaction.guild), view=self)

    @discord.ui.button(label="Editar tarjeta", style=discord.ButtonStyle.secondary, row=2)
    async def edit_card(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await interaction.response.send_modal(OrientationEmbedModal(interaction.guild))

    @discord.ui.button(label="Guardar cambios", style=discord.ButtonStyle.success, row=3)
    async def save_changes(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if self.pending_channel_id is None and self.pending_bindings is None and self.pending_enabled is None:
            await interaction.response.send_message("No hay cambios pendientes.", ephemeral=True)
            return

        guild = interaction.guild
        prospective_channel_id = self.pending_channel_id or get_orientation_channel_id(self.guild_id)
        prospective_bindings = self.pending_bindings if self.pending_bindings is not None else get_orientation_bindings(self.guild_id)
        prospective_enabled = self.pending_enabled if self.pending_enabled is not None else orientation_enabled(self.guild_id)
        if prospective_enabled:
            channel = guild.get_channel(prospective_channel_id)
            if not isinstance(channel, discord.TextChannel):
                await interaction.response.send_message("Selecciona primero un canal de orientación.", ephemeral=True)
                return
            if not (ORIENTATION_MIN_ROLES <= len(prospective_bindings) <= ORIENTATION_MAX_ROLES):
                await interaction.response.send_message("Selecciona primero entre 1 y 6 roles.", ephemeral=True)
                return

        await interaction.response.defer(ephemeral=True)
        old_channel_id = get_orientation_channel_id(self.guild_id)
        old_bindings = get_orientation_bindings(self.guild_id)
        old_enabled = orientation_enabled(self.guild_id)
        try:
            if self.pending_channel_id is not None:
                guild_config_set(self.guild_id, "orientation_channel_id", str(self.pending_channel_id))
            if self.pending_bindings is not None:
                set_orientation_bindings(self.guild_id, self.pending_bindings)
                guild_config_set(self.guild_id, "orientation_created_role_ids", "[]")
            if self.pending_enabled is not None:
                guild_config_set(self.guild_id, "orientation_enabled", "1" if self.pending_enabled else "0")

            if prospective_enabled:
                ok, note = await ensure_orientation_system(guild)
            elif old_enabled:
                ok, note = await disable_orientation_system(guild)
            else:
                ok, note = True, "Configuración guardada."

            if not ok:
                guild_config_set(self.guild_id, "orientation_channel_id", str(old_channel_id or 0))
                set_orientation_bindings(self.guild_id, old_bindings)
                guild_config_set(self.guild_id, "orientation_enabled", "1" if old_enabled else "0")
                if old_enabled:
                    await ensure_orientation_system(guild)
                await interaction.followup.send(f"No pude aplicar los cambios: {note}", ephemeral=True)
                return
        except (sqlite3.OperationalError, discord.HTTPException) as exc:
            await interaction.followup.send(f"No pude guardar los cambios: {exc}", ephemeral=True)
            return

        self.pending_channel_id = None
        self.pending_bindings = None
        self.pending_enabled = None
        await interaction.edit_original_response(content=self._content(guild) + f"\n\nCambios guardados. {note}", embed=None, view=self)

    @discord.ui.button(label="Descartar cambios", style=discord.ButtonStyle.secondary, row=3)
    async def discard_changes(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        self.pending_channel_id = None
        self.pending_bindings = None
        self.pending_enabled = None
        await interaction.response.edit_message(content=self._content(interaction.guild), embed=None, view=self)

    @discord.ui.button(label="Volver", style=discord.ButtonStyle.secondary, row=3)
    async def back(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await heraldo_setup_go_home(interaction, self.guild_id, self.owner_id)


@bot.listen("on_raw_reaction_add")
async def orientation_reaction_add(payload: discord.RawReactionActionEvent) -> None:
    if payload.guild_id is None or payload.user_id == getattr(bot.user, "id", None):
        return
    if not orientation_enabled(payload.guild_id):
        return
    if payload.message_id != get_orientation_message_id(payload.guild_id):
        return
    if payload.channel_id != get_orientation_message_channel_id(payload.guild_id):
        return

    guild = bot.get_guild(payload.guild_id)
    if guild is None:
        return
    member = payload.member or guild.get_member(payload.user_id)
    if member is None or member.bot:
        return

    target_role = orientation_role_for_emoji(guild, str(payload.emoji))
    channel = guild.get_channel(payload.channel_id)
    if target_role is None or not isinstance(channel, discord.TextChannel):
        return

    all_orientation_ids = get_eval_role_ids(guild.id)
    to_remove = [
        role for role in member.roles
        if role.id in all_orientation_ids and role.id != target_role.id and role.is_assignable()
    ]
    try:
        if to_remove:
            await member.remove_roles(*to_remove, reason="El Heraldo: cambio de orientación")
        if target_role not in member.roles:
            await member.add_roles(target_role, reason="El Heraldo: Reaction Role de orientación")

        # Orientación admite una sola elección. Se retiran las demás reacciones del
        # usuario para que mensaje, roles y estado visible siempre coincidan.
        message = await channel.fetch_message(payload.message_id)
        chosen = str(payload.emoji).replace("\ufe0f", "")
        for binding in get_orientation_bindings(guild.id):
            emoji = str(binding["emoji"])
            if _orientation_emoji_key(emoji) != chosen:
                try:
                    await message.remove_reaction(emoji, member)
                except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                    pass
    except (discord.Forbidden, discord.HTTPException):
        await log_embed(
            guild,
            "⚠️ Error de orientación",
            f"No pude sincronizar el rol de orientación de {member.mention}. Revisa la jerarquía de roles.",
            discord.Color.orange(),
        )


@bot.listen("on_raw_reaction_remove")
async def orientation_reaction_remove(payload: discord.RawReactionActionEvent) -> None:
    if payload.guild_id is None or not orientation_enabled(payload.guild_id):
        return
    if payload.message_id != get_orientation_message_id(payload.guild_id):
        return
    if payload.channel_id != get_orientation_message_channel_id(payload.guild_id):
        return

    guild = bot.get_guild(payload.guild_id)
    if guild is None:
        return
    member = guild.get_member(payload.user_id)
    if member is None or member.bot:
        return
    role = orientation_role_for_emoji(guild, str(payload.emoji))
    if role is None or role not in member.roles:
        return
    try:
        await member.remove_roles(role, reason="El Heraldo: reacción de orientación retirada")
    except (discord.Forbidden, discord.HTTPException):
        pass


@bot.listen("on_guild_role_delete")
async def orientation_role_deleted(role: discord.Role) -> None:
    if not orientation_enabled(role.guild.id):
        return

    bindings = get_orientation_bindings(role.guild.id)
    if role.id not in {int(item["role_id"]) for item in bindings}:
        return

    remaining = [item for item in bindings if int(item["role_id"]) != role.id]
    set_orientation_bindings(role.guild.id, remaining)

    if remaining:
        ok, note = await ensure_orientation_system(role.guild)
        title = "🧭 Orientación actualizada" if ok else "⚠️ Orientación necesita atención"
        description = (
            f"Se eliminó el rol **{role.name}**. El Heraldo retiró su vínculo y su reacción; "
            "no creó ningún rol nuevo.\n\n" + note
        )
        color = discord.Color.green() if ok else discord.Color.orange()
    else:
        await disable_orientation_system(role.guild)
        title = "⚠️ Orientación desactivada"
        description = (
            f"Se eliminó **{role.name}**, que era el último rol vinculado. "
            "El módulo se desactivó porque necesita al menos un rol existente."
        )
        color = discord.Color.orange()

    await log_embed(role.guild, title, description, color)


@bot.listen("on_raw_message_delete")
async def orientation_message_deleted(payload: discord.RawMessageDeleteEvent) -> None:
    if payload.guild_id is None or not orientation_enabled(payload.guild_id):
        return
    if payload.message_id != get_orientation_message_id(payload.guild_id):
        return
    guild = bot.get_guild(payload.guild_id)
    if guild is None:
        return
    guild_config_set(guild.id, "orientation_message_id", "0")
    await asyncio.sleep(1)
    await ensure_orientation_system(guild)


class HeraldoMotwScheduleModal(discord.ui.Modal, title="Miembro de la Semana · Horario"):
    weekday_input = discord.ui.TextInput(
        label="Día (0=Lunes ... 6=Domingo)",
        required=True,
        max_length=1,
    )
    hour_input = discord.ui.TextInput(
        label="Hora (0-23, hora RD)",
        required=True,
        max_length=2,
    )

    def __init__(self, guild_id: int) -> None:
        super().__init__()
        self.guild_id = guild_id
        self.weekday_input.default = str(get_motw_weekday(guild_id))
        self.hour_input.default = str(get_motw_hour(guild_id))

    async def on_submit(self, interaction: discord.Interaction) -> None:
        try:
            weekday = int(str(self.weekday_input).strip())
            hour = int(str(self.hour_input).strip())
            if weekday not in range(7) or hour not in range(24):
                raise ValueError
        except ValueError:
            await interaction.response.send_message(
                "❌ Día debe estar entre 0 y 6, y hora entre 0 y 23.",
                ephemeral=True,
            )
            return
        set_motw_schedule(self.guild_id, weekday, hour)
        motw_mark_current_slot(self.guild_id)
        await interaction.response.send_message(
            f"✅ Miembro de la Semana: **{MOTW_WEEKDAY_NAMES[weekday]} a las {hour}:00** (hora RD).",
            ephemeral=True,
        )



class HeraldoMotwSetupView(discord.ui.View):
    def __init__(self, guild_id: int, owner_id: int) -> None:
        super().__init__(timeout=900)
        self.guild_id = guild_id
        self.owner_id = owner_id
        self.pending_channel_id: int | None = None
        channel = discord.ui.ChannelSelect(
            placeholder="Seleccionar canal de Miembro de la Semana",
            channel_types=[discord.ChannelType.text],
            min_values=1,
            max_values=1,
            row=0,
        )
        channel.callback = self.select_channel
        self.add_item(channel)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("Este panel de configuración no es tuyo.", ephemeral=True)
            return False
        return True

    def _content(self, guild: discord.Guild) -> str:
        current = guild.get_channel(get_motw_channel_id(self.guild_id))
        items = []
        if self.pending_channel_id is not None:
            pending = guild.get_channel(self.pending_channel_id)
            items.append(f"Canal → {pending.mention if pending else self.pending_channel_id}")
        return (
            "👑 **El Heraldo · Miembro de la Semana**\n\n"
            f"Canal guardado: {current.mention if current else 'no configurado'}\n"
            f"Horario: **{MOTW_WEEKDAY_NAMES[get_motw_weekday(self.guild_id)]} a las {get_motw_hour(self.guild_id)}:00** (hora RD)"
            + _pending_config_text(items)
        )

    async def select_channel(self, interaction: discord.Interaction) -> None:
        values = interaction.data.get("values") if interaction.data else []
        channel = interaction.guild.get_channel(int(values[0])) if interaction.guild and values else None
        if not isinstance(channel, discord.TextChannel):
            await interaction.response.send_message("No pude localizar ese canal.", ephemeral=True)
            return
        perms = channel.permissions_for(interaction.guild.me)
        if not (perms.view_channel and perms.send_messages and perms.embed_links):
            await interaction.response.send_message("El Heraldo necesita Ver canal, Enviar mensajes e Insertar enlaces.", ephemeral=True)
            return
        self.pending_channel_id = channel.id
        await interaction.response.edit_message(content=self._content(interaction.guild), view=self)

    @discord.ui.button(label="Horario", style=discord.ButtonStyle.primary, row=1)
    async def schedule(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await interaction.response.send_modal(HeraldoMotwScheduleModal(self.guild_id))

    @discord.ui.button(label="Probar", style=discord.ButtonStyle.secondary, row=1)
    async def test(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if self.pending_channel_id is not None:
            await interaction.response.send_message("Guarda o descarta el canal pendiente antes de probar.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)
        error = await announce_member_of_the_week(self.guild_id, reset=False)
        await interaction.followup.send("Anuncio de prueba publicado." if not error else f"No pude publicar: {error}", ephemeral=True)

    @discord.ui.button(label="Guardar cambios", style=discord.ButtonStyle.success, row=2)
    async def save_changes(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if self.pending_channel_id is None:
            await interaction.response.send_message("No hay cambios pendientes.", ephemeral=True)
            return
        set_motw_channel_id(self.guild_id, self.pending_channel_id)
        self.pending_channel_id = None
        await interaction.response.edit_message(content=self._content(interaction.guild) + "\n\nCambios guardados.", view=self)

    @discord.ui.button(label="Descartar cambios", style=discord.ButtonStyle.secondary, row=2)
    async def discard_changes(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        self.pending_channel_id = None
        await interaction.response.edit_message(content=self._content(interaction.guild), view=self)

    @discord.ui.button(label="Volver", style=discord.ButtonStyle.secondary, row=2)
    async def back(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await heraldo_setup_go_home(interaction, self.guild_id, self.owner_id)



class HeraldoHoneypotSetupView(discord.ui.View):
    def __init__(self, guild_id: int, owner_id: int) -> None:
        super().__init__(timeout=900)
        self.guild_id = guild_id
        self.owner_id = owner_id
        self.pending_trap_id: int | None = None
        self.pending_enabled: bool | None = None
        channel = discord.ui.ChannelSelect(
            placeholder="Seleccionar / añadir canal trampa",
            channel_types=[discord.ChannelType.text],
            min_values=1,
            max_values=1,
            row=0,
        )
        channel.callback = self.select_trap
        self.add_item(channel)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("Este panel de configuración no es tuyo.", ephemeral=True)
            return False
        return True

    def _content(self, guild: discord.Guild) -> str:
        items = []
        if self.pending_trap_id is not None:
            channel = guild.get_channel(self.pending_trap_id)
            items.append(f"Añadir canal trampa → {channel.mention if channel else self.pending_trap_id}")
        if self.pending_enabled is not None:
            items.append(f"Honeypot → {'activo' if self.pending_enabled else 'desactivado'}")
        return "🍯 **El Heraldo · Honeypot**\n\n" + hp_config_summary(guild) + _pending_config_text(items)

    async def select_trap(self, interaction: discord.Interaction) -> None:
        values = interaction.data.get("values") if interaction.data else []
        channel = interaction.guild.get_channel(int(values[0])) if interaction.guild and values else None
        if not isinstance(channel, discord.TextChannel):
            await interaction.response.send_message("No pude localizar ese canal.", ephemeral=True)
            return
        reason = hp_protected_channel_reason(channel)
        if reason:
            await interaction.response.send_message(f"Ese canal no puede ser trampa porque {reason}.", ephemeral=True)
            return
        self.pending_trap_id = channel.id
        await interaction.response.edit_message(content=self._content(interaction.guild), view=self)

    @discord.ui.button(label="Crear canal", style=discord.ButtonStyle.success, row=1)
    async def create_channel(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        guild = interaction.guild
        existing_id = get_guild_channel_id(self.guild_id, "honeypot")
        channel = guild.get_channel(existing_id) if existing_id else None
        created_now = False
        if not isinstance(channel, discord.TextChannel):
            channel = next((c for c in guild.text_channels if c.name.casefold() == "honeypot"), None)
        if not isinstance(channel, discord.TextChannel):
            me = guild.me
            if me is None or not me.guild_permissions.manage_channels:
                await interaction.response.send_message(
                    "El Heraldo necesita Gestionar canales para crear el Honeypot.",
                    ephemeral=True,
                )
                return
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(
                    view_channel=True,
                    send_messages=True,
                    create_public_threads=False,
                    create_private_threads=False,
                    send_messages_in_threads=False,
                )
            }
            await interaction.response.defer(ephemeral=True)
            try:
                channel = await guild.create_text_channel(
                    "Honeypot",
                    overwrites=overwrites,
                    reason="El Heraldo: crear canal Honeypot desde /setup",
                )
                created_now = True
            except discord.HTTPException as exc:
                await interaction.followup.send(f"No pude crear el canal: `{exc}`.", ephemeral=True)
                return
        else:
            await interaction.response.defer(ephemeral=True)

        note = await _setup_apply_system_channel(guild, "honeypot", channel, publish_messages=True)
        self.pending_trap_id = None
        action = "Creé" if created_now else "Reutilicé"
        await interaction.edit_original_response(
            content=self._content(guild) + f"\n\n{action} {channel.mention}. {note}",
            view=self,
        )

    @discord.ui.button(label="Activar / Pausar", style=discord.ButtonStyle.primary, row=1)
    async def toggle(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        current = self.pending_enabled if self.pending_enabled is not None else honeypot_enabled(self.guild_id)
        target = not current
        if target and not hp_traps(self.guild_id) and self.pending_trap_id is None:
            await interaction.response.send_message("Añade al menos un canal trampa antes de activar el Honeypot.", ephemeral=True)
            return
        self.pending_enabled = target
        await interaction.response.edit_message(content=self._content(interaction.guild), view=self)

    @discord.ui.button(label="Editar aviso", style=discord.ButtonStyle.secondary, row=1)
    async def edit_warning(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await interaction.response.send_modal(HoneypotWarningEmbedModal(self.guild_id))

    @discord.ui.button(label="Texto aviso", style=discord.ButtonStyle.secondary, row=1)
    async def edit_text(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await interaction.response.send_modal(HoneypotWarningModal(self.guild_id))

    @discord.ui.button(label="Guardar cambios", style=discord.ButtonStyle.success, row=2)
    async def save_changes(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if self.pending_trap_id is None and self.pending_enabled is None:
            await interaction.response.send_message("No hay cambios pendientes.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)
        if self.pending_trap_id is not None:
            hp_add_trap(self.guild_id, self.pending_trap_id)
            channel = interaction.guild.get_channel(self.pending_trap_id)
            if isinstance(channel, discord.TextChannel):
                await hp_sync_warning(channel)
        if self.pending_enabled is not None:
            hp_setting_set(self.guild_id, "honeypot_enabled", "1" if self.pending_enabled else "0")
            hp_setting_set(self.guild_id, "honeypot_paused", "0")
        self.pending_trap_id = None
        self.pending_enabled = None
        await interaction.edit_original_response(content=self._content(interaction.guild) + "\n\nCambios guardados.", view=self)

    @discord.ui.button(label="Descartar cambios", style=discord.ButtonStyle.secondary, row=2)
    async def discard_changes(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        self.pending_trap_id = None
        self.pending_enabled = None
        await interaction.response.edit_message(content=self._content(interaction.guild), view=self)

    @discord.ui.button(label="Volver", style=discord.ButtonStyle.secondary, row=3)
    async def back(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await heraldo_setup_go_home(interaction, self.guild_id, self.owner_id)


def heraldo_permissions_summary(guild: discord.Guild) -> str:
    lines: list[str] = []
    channel_defs = (
        ("logs", "Logs"),
        ("condemned", "Condenados"),
        ("honeypot", "Honeypot"),
        ("verification", "Verificación"),
        ("questions", "Dudas"),
    )
    for key, label in channel_defs:
        channel_id = get_guild_channel_id(guild.id, key)
        channel = guild.get_channel(channel_id) if channel_id else None
        if not isinstance(channel, discord.TextChannel):
            lines.append(f"❌ **{label}:** no configurado")
            continue
        perms = channel.permissions_for(guild.me)
        missing: list[str] = []
        if not perms.view_channel:
            missing.append("Ver canal")
        if not perms.send_messages:
            missing.append("Enviar mensajes")
        if key in {"logs", "condemned", "honeypot", "verification"} and not perms.embed_links:
            missing.append("Insertar enlaces")
        if key == "honeypot" and not perms.manage_messages:
            missing.append("Gestionar mensajes")
        lines.append(
            f"{'✅' if not missing else '⚠️'} **{label}:** {channel.mention}"
            + (f" · faltan: {', '.join(missing)}" if missing else "")
        )

    role_defs = (
        ("sin_verificar", "Sin Verificar"),
        ("tentado", "Verificación / orientación"),
        ("condenado", "Condenado"),
    )
    for key, label in role_defs:
        role_id = get_guild_role_id(guild.id, key)
        role = guild.get_role(role_id) if role_id else None
        if role is None:
            lines.append(f"❌ **Rol {label}:** no configurado")
            continue
        problem = None
        if role.is_default():
            problem = "es @everyone"
        elif role.managed:
            problem = "está gestionado por Discord o una integración"
        elif role >= guild.me.top_role:
            problem = "está al mismo nivel o por encima del rol del Heraldo"
        lines.append(
            f"{'✅' if problem is None else '⚠️'} **Rol {label}:** {role.mention}"
            + (f" · {problem}" if problem else "")
        )
    return "\n".join(lines)



class HeraldoVerificationSetupView(discord.ui.View):
    def __init__(self, guild_id: int, owner_id: int) -> None:
        super().__init__(timeout=900)
        self.guild_id = guild_id
        self.owner_id = owner_id
        self.pending_role_id: int | None = None
        self.pending_sin_role_id: int | None = None
        self.pending_channel_id: int | None = None
        self.pending_enabled: bool | None = None

        role_select = discord.ui.RoleSelect(
            placeholder="Seleccionar rol que se otorga al verificarse",
            min_values=1,
            max_values=1,
            row=0,
        )
        role_select.callback = self.select_role
        self.add_item(role_select)

        sin_role_select = discord.ui.RoleSelect(
            placeholder="Seleccionar rol Sin Verificar",
            min_values=1,
            max_values=1,
            row=1,
        )
        sin_role_select.callback = self.select_sin_role
        self.add_item(sin_role_select)

        channel_select = discord.ui.ChannelSelect(
            placeholder="Seleccionar canal de verificación",
            channel_types=[discord.ChannelType.text],
            min_values=1,
            max_values=1,
            row=2,
        )
        channel_select.callback = self.select_channel
        self.add_item(channel_select)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("Este panel de configuración no es tuyo.", ephemeral=True)
            return False
        return True

    def _content(self, guild: discord.Guild) -> str:
        items = []
        if self.pending_role_id is not None:
            role = guild.get_role(self.pending_role_id)
            items.append(f"Rol de verificación → {role.mention if role else self.pending_role_id}")
        if self.pending_sin_role_id is not None:
            role = guild.get_role(self.pending_sin_role_id)
            items.append(f"Rol Sin Verificar → {role.mention if role else self.pending_sin_role_id}")
        if self.pending_channel_id is not None:
            channel = guild.get_channel(self.pending_channel_id)
            items.append(f"Canal de verificación → {channel.mention if channel else self.pending_channel_id}")
        if self.pending_enabled is not None:
            items.append(f"Verificación automática → {'activa' if self.pending_enabled else 'desactivada'}")
        return "✅ **El Heraldo · Verificación**\n\n" + verify_config_summary(guild) + _pending_config_text(items)

    async def select_role(self, interaction: discord.Interaction) -> None:
        values = interaction.data.get("values") if interaction.data else []
        role = interaction.guild.get_role(int(values[0])) if interaction.guild and values else None
        if role is None:
            await interaction.response.send_message("No pude localizar ese rol.", ephemeral=True)
            return
        problem = verify_role_problem(role, interaction.guild)
        if problem:
            await interaction.response.send_message(f"No puedo usar {role.mention}: {problem}.", ephemeral=True)
            return
        self.pending_role_id = role.id
        await interaction.response.edit_message(content=self._content(interaction.guild), view=self)

    async def select_sin_role(self, interaction: discord.Interaction) -> None:
        values = interaction.data.get("values") if interaction.data else []
        role = interaction.guild.get_role(int(values[0])) if interaction.guild and values else None
        if role is None:
            await interaction.response.send_message("No pude localizar ese rol.", ephemeral=True)
            return
        if role.is_default() or role.managed or role >= interaction.guild.me.top_role:
            await interaction.response.send_message(
                "Ese rol no puede ser administrado por El Heraldo. Revisa jerarquía o integraciones.",
                ephemeral=True,
            )
            return
        self.pending_sin_role_id = role.id
        await interaction.response.edit_message(content=self._content(interaction.guild), view=self)

    async def select_channel(self, interaction: discord.Interaction) -> None:
        values = interaction.data.get("values") if interaction.data else []
        channel = interaction.guild.get_channel(int(values[0])) if interaction.guild and values else None
        if not isinstance(channel, discord.TextChannel):
            await interaction.response.send_message("No pude localizar ese canal.", ephemeral=True)
            return
        perms = channel.permissions_for(interaction.guild.me)
        missing = []
        if not perms.view_channel:
            missing.append("Ver canal")
        if not perms.send_messages:
            missing.append("Enviar mensajes")
        if missing:
            await interaction.response.send_message(f"Faltan {', '.join(missing)} en {channel.mention}.", ephemeral=True)
            return
        self.pending_channel_id = channel.id
        await interaction.response.edit_message(content=self._content(interaction.guild), view=self)

    @discord.ui.button(label="Crear canal", style=discord.ButtonStyle.success, row=3)
    async def create_verify_channel(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        guild = interaction.guild
        existing_id = get_guild_channel_id(self.guild_id, "verification")
        channel = guild.get_channel(existing_id) if existing_id else None
        created_now = False
        if not isinstance(channel, discord.TextChannel):
            channel = next((c for c in guild.text_channels if c.name.casefold() == "verificación".casefold()), None)
        if not isinstance(channel, discord.TextChannel):
            me = guild.me
            if me is None or not me.guild_permissions.manage_channels:
                await interaction.response.send_message(
                    "El Heraldo necesita Gestionar canales para crear el canal de verificación.",
                    ephemeral=True,
                )
                return
            await interaction.response.defer(ephemeral=True)
            try:
                channel = await guild.create_text_channel(
                    "Verificación",
                    reason="El Heraldo: crear canal de verificación desde /setup",
                )
                created_now = True
            except discord.HTTPException as exc:
                await interaction.followup.send(f"No pude crear el canal: `{exc}`.", ephemeral=True)
                return
        else:
            await interaction.response.defer(ephemeral=True)

        note = await _setup_apply_system_channel(guild, "verification", channel, publish_messages=True)
        self.pending_channel_id = None
        action = "Creé" if created_now else "Reutilicé"
        await interaction.edit_original_response(
            content=self._content(guild) + f"\n\n{action} {channel.mention}. {note}",
            view=self,
        )

    @discord.ui.button(label="Crear rol verificación", style=discord.ButtonStyle.success, row=4)
    async def create_verify_role(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await interaction.response.defer(ephemeral=True)
        role, created_now, error = await _setup_get_or_create_system_role(
            interaction.guild, "tentado", "Verificación", "Tentad@"
        )
        if error or role is None:
            await interaction.followup.send(error or "No pude preparar el rol.", ephemeral=True)
            return
        self.pending_role_id = None
        action = "Creé" if created_now else "Reutilicé"
        await interaction.edit_original_response(
            content=self._content(interaction.guild) + f"\n\n{action} {role.mention} como rol de verificación.",
            view=self,
        )

    @discord.ui.button(label="Crear Sin Verificar", style=discord.ButtonStyle.success, row=4)
    async def create_sin_role(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await interaction.response.defer(ephemeral=True)
        role, created_now, error = await _setup_get_or_create_system_role(
            interaction.guild, "sin_verificar", "Sin Verificar", "Sin Verificar"
        )
        if error or role is None:
            await interaction.followup.send(error or "No pude preparar el rol.", ephemeral=True)
            return
        self.pending_sin_role_id = None
        action = "Creé" if created_now else "Reutilicé"
        await interaction.edit_original_response(
            content=self._content(interaction.guild) + f"\n\n{action} {role.mention} como rol Sin Verificar.",
            view=self,
        )

    @discord.ui.button(label="Textos", style=discord.ButtonStyle.secondary, row=3)
    async def texts(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await interaction.response.send_modal(VerifyTextsModal(self.guild_id))

    @discord.ui.button(label="Publicar / actualizar", style=discord.ButtonStyle.secondary, row=3)
    async def publish(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if self.pending_role_id is not None or self.pending_sin_role_id is not None or self.pending_channel_id is not None or self.pending_enabled is not None:
            await interaction.response.send_message("Guarda o descarta los cambios pendientes antes de publicar.", ephemeral=True)
            return
        channel_id = get_guild_channel_id(self.guild_id, "verification")
        channel = interaction.guild.get_channel(channel_id) if channel_id else None
        if not isinstance(channel, discord.TextChannel):
            await interaction.response.send_message("Configura primero un canal de verificación.", ephemeral=True)
            return
        role = interaction.guild.get_role(get_verify_role_id(self.guild_id))
        if role is None:
            await interaction.response.send_message("Configura primero un rol de verificación.", ephemeral=True)
            return
        problem = verify_role_problem(role, interaction.guild)
        if problem:
            await interaction.response.send_message(f"{role.mention} {problem}.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)
        ref = guild_config_get(self.guild_id, "verify_panel_ref")
        if ref and ref.count(":") == 1:
            try:
                old_channel_id, old_message_id = (int(x) for x in ref.split(":"))
                old_channel = interaction.guild.get_channel(old_channel_id)
                if isinstance(old_channel, discord.TextChannel):
                    old_message = await old_channel.fetch_message(old_message_id)
                    await old_message.edit(
                        content=render_vars(get_verify_panel_text(self.guild_id), VarContext(interaction.guild, None, old_channel), 2000),
                        view=VerifyView(label=get_verify_button_label(self.guild_id)),
                    )
                    await interaction.followup.send(f"Panel de verificación actualizado en {old_channel.mention}.", ephemeral=True)
                    return
            except (ValueError, discord.NotFound, discord.Forbidden, discord.HTTPException):
                pass
        message = await channel.send(
            content=render_vars(get_verify_panel_text(self.guild_id), VarContext(interaction.guild, None, channel), 2000),
            view=VerifyView(label=get_verify_button_label(self.guild_id)),
            allowed_mentions=discord.AllowedMentions.none(),
        )
        guild_config_set(self.guild_id, "verify_panel_ref", f"{channel.id}:{message.id}")
        await interaction.followup.send(f"Panel de verificación publicado en {channel.mention}.", ephemeral=True)

    @discord.ui.button(label="Activar / desactivar", style=discord.ButtonStyle.primary, row=3)
    async def toggle(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        current = self.pending_enabled if self.pending_enabled is not None else verify_enabled(self.guild_id)
        target = not current
        prospective_role_id = self.pending_role_id or get_verify_role_id(self.guild_id)
        if target and interaction.guild.get_role(prospective_role_id) is None:
            await interaction.response.send_message("Configura primero un rol de verificación.", ephemeral=True)
            return
        self.pending_enabled = target
        await interaction.response.edit_message(content=self._content(interaction.guild), view=self)

    @discord.ui.button(label="Guardar cambios", style=discord.ButtonStyle.success, row=4)
    async def save_changes(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if self.pending_role_id is None and self.pending_sin_role_id is None and self.pending_channel_id is None and self.pending_enabled is None:
            await interaction.response.send_message("No hay cambios pendientes.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)
        if self.pending_role_id is not None:
            guild_config_set(self.guild_id, "verify_role_id", str(self.pending_role_id))
            guild_resource_set(self.guild_id, "role", "tentado", self.pending_role_id)
        if self.pending_sin_role_id is not None:
            guild_resource_set(self.guild_id, "role", "sin_verificar", self.pending_sin_role_id)
        if self.pending_channel_id is not None:
            channel = interaction.guild.get_channel(self.pending_channel_id)
            if isinstance(channel, discord.TextChannel):
                await _setup_apply_system_channel(interaction.guild, "verification", channel, publish_messages=True)
        if self.pending_enabled is not None:
            if self.pending_enabled and not guild_config_get(self.guild_id, "verify_panel_ref"):
                await interaction.followup.send("No activé la verificación: primero publica el panel.", ephemeral=True)
                return
            guild_config_set(self.guild_id, "verify_enabled", "1" if self.pending_enabled else "0")
        self.pending_role_id = self.pending_sin_role_id = self.pending_channel_id = self.pending_enabled = None
        await interaction.edit_original_response(content=self._content(interaction.guild) + "\n\nCambios guardados.", view=self)

    @discord.ui.button(label="Descartar cambios", style=discord.ButtonStyle.secondary, row=4)
    async def discard_changes(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        self.pending_role_id = self.pending_sin_role_id = self.pending_channel_id = self.pending_enabled = None
        await interaction.response.edit_message(content=self._content(interaction.guild), view=self)

    @discord.ui.button(label="Volver", style=discord.ButtonStyle.secondary, row=4)
    async def back(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await heraldo_setup_go_home(interaction, self.guild_id, self.owner_id)


class HeraldoRaidDetectionModal(discord.ui.Modal, title="Raid Protection · Detección"):
    threshold_input = discord.ui.TextInput(
        label="Umbral de entradas",
        required=True,
        max_length=4,
        placeholder="Ej.: 5",
    )
    window_input = discord.ui.TextInput(
        label="Ventana de detección",
        required=True,
        max_length=24,
        placeholder="Ej.: 30s, 1m",
    )
    age_input = discord.ui.TextInput(
        label="Edad máxima de cuenta nueva",
        required=True,
        max_length=24,
        placeholder="Ej.: 7d · 0 = sin filtro",
    )
    ratio_input = discord.ui.TextInput(
        label="Proporción mínima de cuentas nuevas (%)",
        required=True,
        max_length=3,
        placeholder="Ej.: 60 · 0 = desactivada",
    )
    duration_input = discord.ui.TextInput(
        label="Duración de la respuesta",
        required=True,
        max_length=24,
        placeholder="Ej.: 10m, 2h",
    )

    def __init__(self, guild_id: int) -> None:
        super().__init__()
        self.guild_id = guild_id
        self.threshold_input.default = str(raid_threshold(guild_id))
        self.window_input.default = format_flex_duration(raid_window_seconds(guild_id))
        age = raid_min_age_seconds(guild_id)
        self.age_input.default = format_flex_duration(age) if age else "0"
        self.ratio_input.default = str(raid_new_account_ratio(guild_id))
        self.duration_input.default = format_flex_duration(raid_duration_seconds(guild_id))

    async def on_submit(self, interaction: discord.Interaction) -> None:
        try:
            threshold = int(str(self.threshold_input).strip())
            ratio = int(str(self.ratio_input).strip())
            if not RAID_THRESHOLD_MIN <= threshold <= RAID_THRESHOLD_MAX:
                raise ValueError(
                    f"El umbral debe estar entre {RAID_THRESHOLD_MIN} y {RAID_THRESHOLD_MAX}."
                )
            if not 0 <= ratio <= 100:
                raise ValueError("La proporción debe estar entre 0 y 100.")
            window_s = parse_flex_duration(
                str(self.window_input).strip(), RAID_WINDOW_MIN, RAID_WINDOW_MAX
            )
            age_s = parse_flex_duration(
                str(self.age_input).strip(), 0, RAID_AGE_MAX
            )
            duration_s = parse_flex_duration(
                str(self.duration_input).strip(), RAID_DURATION_MIN, RAID_DURATION_MAX
            )
            if ratio > 0 and age_s <= 0:
                raise ValueError(
                    "Si usas una proporción de cuentas nuevas, la edad máxima debe ser mayor que 0."
                )
        except ValueError as e:
            await interaction.response.send_message(f"❌ No guardé nada: {e}", ephemeral=True)
            return

        guild_config_set(self.guild_id, "raid_threshold", str(threshold))
        guild_config_set(self.guild_id, "raid_window_seconds", str(window_s))
        guild_config_set(self.guild_id, "raid_min_age_seconds", str(age_s))
        guild_config_set(self.guild_id, "raid_new_account_ratio", str(ratio))
        guild_config_set(self.guild_id, "raid_duration_seconds", str(duration_s))
        await interaction.response.send_message(
            "✅ Detección de Raid Protection actualizada.\n\n"
            + raid_config_summary(interaction.guild),
            ephemeral=True,
        )



class HeraldoRaidSetupView(discord.ui.View):
    def __init__(self, guild_id: int, owner_id: int) -> None:
        super().__init__(timeout=900)
        self.guild_id = guild_id
        self.owner_id = owner_id
        self.pending_action: str | None = None
        self.pending_role_id: int | None = None
        self.pending_enabled: bool | None = None
        self.pending_invites: bool | None = None
        self.pending_purge: bool | None = None

        action_select = discord.ui.Select(
            placeholder="Respuesta ante el raid",
            min_values=1,
            max_values=1,
            options=[discord.SelectOption(label=label[:100], value=value, default=(value == raid_action(guild_id))) for value, label in RAID_ACTION_LABELS.items()],
            row=0,
        )
        action_select.callback = self.select_action
        self.action_select = action_select
        self.add_item(action_select)

        role_select = discord.ui.RoleSelect(
            placeholder="Rol a mencionar en las alertas",
            min_values=1,
            max_values=1,
            row=1,
        )
        role_select.callback = self.select_alert_role
        self.add_item(role_select)

        self.toggle_enabled.label = "Protección activada" if raid_enabled(guild_id) else "Protección desactivada"
        self.toggle_invites.label = "Pausar invitaciones: sí" if raid_lock_invites_enabled(guild_id) else "Pausar invitaciones: no"
        self.toggle_purge.label = "Purgar mensajes: sí" if raid_purge_enabled(guild_id) else "Purgar mensajes: no"

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("Este panel de configuración no es tuyo.", ephemeral=True)
            return False
        return True

    def _content(self, guild: discord.Guild) -> str:
        items = []
        if self.pending_action is not None:
            items.append(f"Respuesta → {RAID_ACTION_LABELS.get(self.pending_action, self.pending_action)}")
        if self.pending_role_id is not None:
            role = guild.get_role(self.pending_role_id)
            items.append(f"Rol de alertas → {role.mention if role else self.pending_role_id}")
        if self.pending_enabled is not None:
            items.append(f"Protección → {'activa' if self.pending_enabled else 'desactivada'}")
        if self.pending_invites is not None:
            items.append(f"Pausar invitaciones → {'sí' if self.pending_invites else 'no'}")
        if self.pending_purge is not None:
            items.append(f"Purgar mensajes → {'sí' if self.pending_purge else 'no'}")
        return "**El Heraldo · Raid Protection**\n\n" + raid_config_summary(guild) + _pending_config_text(items)

    async def select_action(self, interaction: discord.Interaction) -> None:
        value = self.action_select.values[0]
        if value == "condemn" and interaction.guild.get_role(condemnation_role_id(guild_id=self.guild_id)) is None:
            await interaction.response.send_message("Para usar «Condenar» primero debes configurar el rol Condenado.", ephemeral=True)
            return
        self.pending_action = value
        await interaction.response.edit_message(content=self._content(interaction.guild), view=self)

    async def select_alert_role(self, interaction: discord.Interaction) -> None:
        values = interaction.data.get("values") if interaction.data else []
        role = interaction.guild.get_role(int(values[0])) if interaction.guild and values else None
        if role is None:
            await interaction.response.send_message("No pude localizar ese rol.", ephemeral=True)
            return
        self.pending_role_id = role.id
        await interaction.response.edit_message(content=self._content(interaction.guild), view=self)

    @discord.ui.button(label="Detección y duración", style=discord.ButtonStyle.primary, row=2)
    async def detection(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await interaction.response.send_modal(HeraldoRaidDetectionModal(self.guild_id))

    @discord.ui.button(label="Protección", style=discord.ButtonStyle.success, row=2)
    async def toggle_enabled(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        current = self.pending_enabled if self.pending_enabled is not None else raid_enabled(self.guild_id)
        self.pending_enabled = not current
        self.toggle_enabled.label = "Protección activada" if self.pending_enabled else "Protección desactivada"
        await interaction.response.edit_message(content=self._content(interaction.guild), view=self)

    @discord.ui.button(label="Pausar invitaciones", style=discord.ButtonStyle.secondary, row=3)
    async def toggle_invites(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        current = self.pending_invites if self.pending_invites is not None else raid_lock_invites_enabled(self.guild_id)
        self.pending_invites = not current
        self.toggle_invites.label = "Pausar invitaciones: sí" if self.pending_invites else "Pausar invitaciones: no"
        await interaction.response.edit_message(content=self._content(interaction.guild), view=self)

    @discord.ui.button(label="Purgar mensajes", style=discord.ButtonStyle.secondary, row=3)
    async def toggle_purge(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        current = self.pending_purge if self.pending_purge is not None else raid_purge_enabled(self.guild_id)
        self.pending_purge = not current
        self.toggle_purge.label = "Purgar mensajes: sí" if self.pending_purge else "Purgar mensajes: no"
        await interaction.response.edit_message(content=self._content(interaction.guild), view=self)

    @discord.ui.button(label="Guardar cambios", style=discord.ButtonStyle.success, row=4)
    async def save_changes(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if all(v is None for v in (self.pending_action, self.pending_role_id, self.pending_enabled, self.pending_invites, self.pending_purge)):
            await interaction.response.send_message("No hay cambios pendientes.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)
        if self.pending_action is not None:
            guild_config_set(self.guild_id, "raid_action", self.pending_action)
        if self.pending_role_id is not None:
            guild_config_set(self.guild_id, "raid_ping_role", str(self.pending_role_id))
        if self.pending_enabled is not None:
            guild_config_set(self.guild_id, "raid_enabled", "1" if self.pending_enabled else "0")
        if self.pending_invites is not None:
            guild_config_set(self.guild_id, "raid_lock_invites", "1" if self.pending_invites else "0")
        if self.pending_purge is not None:
            guild_config_set(self.guild_id, "raid_purge", "1" if self.pending_purge else "0")
        self.pending_action = self.pending_role_id = self.pending_enabled = self.pending_invites = self.pending_purge = None
        await interaction.edit_original_response(content=self._content(interaction.guild) + "\n\nCambios guardados.", view=self)

    @discord.ui.button(label="Descartar cambios", style=discord.ButtonStyle.secondary, row=4)
    async def discard_changes(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        self.pending_action = self.pending_role_id = self.pending_enabled = self.pending_invites = self.pending_purge = None
        await interaction.response.edit_message(content=self._content(interaction.guild), view=self)

    @discord.ui.button(label="Volver", style=discord.ButtonStyle.secondary, row=4)
    async def back(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await heraldo_setup_go_home(interaction, self.guild_id, self.owner_id)


class VerifyDmEditorContentModal(discord.ui.Modal):
    """Editor del contenido principal del DM que se envía al verificarse."""

    def __init__(self, guild_id: int) -> None:
        super().__init__(title="DM de verificación · Contenido")
        self.guild_id = guild_id
        self.title_input = discord.ui.TextInput(
            label="Título",
            default=get_verify_dm_title(guild_id),
            required=True,
            max_length=256,
        )
        self.field_input = discord.ui.TextInput(
            label="Nombre del campo",
            default=get_verify_dm_field_name(guild_id),
            required=True,
            max_length=256,
        )
        self.body_input = discord.ui.TextInput(
            label="Mensaje",
            style=discord.TextStyle.paragraph,
            default=get_verify_dm_body(guild_id),
            required=True,
            max_length=4000,
        )
        self.footer_input = discord.ui.TextInput(
            label="Pie del embed",
            default=get_verify_dm_footer(guild_id),
            required=True,
            max_length=2048,
        )
        self.color_input = discord.ui.TextInput(
            label="Color HEX",
            default=get_verify_dm_color(guild_id),
            required=True,
            max_length=7,
            placeholder="4F5BDC",
        )
        for item in (
            self.title_input,
            self.field_input,
            self.body_input,
            self.footer_input,
            self.color_input,
        ):
            self.add_item(item)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        color = self.color_input.value.strip().lstrip("#")
        if not re.fullmatch(r"[0-9a-fA-F]{6}", color):
            await interaction.response.send_message(
                "❌ El color debe ser HEX de 6 caracteres, por ejemplo `4F5BDC`.",
                ephemeral=True,
            )
            return

        values = {
            "verify_dm_title": self.title_input.value.strip(),
            "verify_dm_field_name": self.field_input.value.strip(),
            "verify_dm_body": self.body_input.value.strip(),
            "verify_dm_footer": self.footer_input.value.strip(),
            "verify_dm_color": color.upper(),
        }
        if not all(values.values()):
            await interaction.response.send_message(
                "❌ Ningún campo puede quedar vacío.",
                ephemeral=True,
            )
            return

        for key, value in values.items():
            guild_config_set(self.guild_id, key, value)

        await interaction.response.send_message(
            "✅ Contenido del DM de verificación actualizado.",
            ephemeral=True,
        )


class VerifyDmEditorVisualModal(discord.ui.Modal):
    """Editor de la imagen pequeña del pie del DM de verificación."""

    def __init__(self, guild_id: int) -> None:
        super().__init__(title="DM de verificación · Recurso visual")
        self.guild_id = guild_id
        self.footer_icon = discord.ui.TextInput(
            label="Icono del pie (URL o variable)",
            default=get_verify_dm_footer_icon(guild_id),
            required=False,
            max_length=500,
            placeholder="https://… o {servericon}",
        )
        self.add_item(self.footer_icon)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        icon = self.footer_icon.value.strip()
        if (
            icon
            and not re.match(r"^https?://", icon, re.IGNORECASE)
            and not VAR_PATTERN.search(icon)
        ):
            await interaction.response.send_message(
                "❌ El icono debe ser una URL `http(s)://…` o una variable como `{servericon}`.",
                ephemeral=True,
            )
            return

        guild_config_set(self.guild_id, "verify_dm_footer_icon", icon)
        await interaction.response.send_message(
            "✅ Recurso visual del DM actualizado.",
            ephemeral=True,
        )


class VerifyDmMessageSetupView(discord.ui.View):
    def __init__(self, guild_id: int, owner_id: int) -> None:
        super().__init__(timeout=900)
        self.guild_id = guild_id
        self.owner_id = owner_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message(
                "Este editor no es tuyo.",
                ephemeral=True,
            )
            return False
        return True

    @discord.ui.button(label="Contenido", style=discord.ButtonStyle.primary, row=0)
    async def content(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await interaction.response.send_modal(VerifyDmEditorContentModal(self.guild_id))

    @discord.ui.button(label="Recurso visual", style=discord.ButtonStyle.secondary, row=0)
    async def visual(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await interaction.response.send_modal(VerifyDmEditorVisualModal(self.guild_id))

    @discord.ui.button(label="Vista previa", style=discord.ButtonStyle.secondary, row=0)
    async def preview(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await interaction.response.send_message(
            "👁️ **Vista previa del DM de verificación**",
            embed=build_verification_welcome_embed(
                member=interaction.user if isinstance(interaction.user, discord.Member) else None,
                guild=interaction.guild,
            ),
            ephemeral=True,
        )

    @discord.ui.button(label="Volver", style=discord.ButtonStyle.secondary, row=1)
    async def back(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await interaction.response.edit_message(
            content=heraldo_messages_setup_content(),
            embed=None,
            view=HeraldoMessagesSetupView(self.guild_id, self.owner_id),
        )


class SuggestionPanelContentModal(discord.ui.Modal):
    def __init__(self, guild_id: int) -> None:
        super().__init__(title="Sugerencias · Contenido")
        self.guild_id = guild_id
        self.title_input = discord.ui.TextInput(
            label="Título",
            default=guild_config_get(guild_id, "suggestion_panel_title") or SUGGESTION_PANEL_TITLE_DEFAULT,
            required=True,
            max_length=256,
        )
        self.description_input = discord.ui.TextInput(
            label="Descripción",
            style=discord.TextStyle.paragraph,
            default=guild_config_get(guild_id, "suggestion_panel_description") or SUGGESTION_PANEL_DESCRIPTION_DEFAULT,
            required=True,
            max_length=4000,
        )
        self.color_input = discord.ui.TextInput(
            label="Color HEX",
            default=guild_config_get(guild_id, "suggestion_panel_color") or SUGGESTION_PANEL_COLOR_DEFAULT,
            required=True,
            max_length=7,
            placeholder="4F5BDC",
        )
        for item in (self.title_input, self.description_input, self.color_input):
            self.add_item(item)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        title = self.title_input.value.strip()
        description = self.description_input.value.strip()
        color = self.color_input.value.strip().lstrip("#")
        if not title or not description:
            await interaction.response.send_message(
                "❌ El título y la descripción no pueden quedar vacíos.",
                ephemeral=True,
            )
            return
        if not re.fullmatch(r"[0-9a-fA-F]{6}", color):
            await interaction.response.send_message(
                "❌ El color debe ser HEX de 6 caracteres, por ejemplo `4F5BDC`.",
                ephemeral=True,
            )
            return

        guild_config_set(self.guild_id, "suggestion_panel_title", title)
        guild_config_set(self.guild_id, "suggestion_panel_description", description)
        guild_config_set(self.guild_id, "suggestion_panel_color", color.upper())

        await interaction.response.defer(ephemeral=True)
        await suggestion_ensure_panel(interaction.guild)
        await interaction.followup.send(
            "✅ Contenido del panel de sugerencias guardado y sincronizado.",
            ephemeral=True,
        )


class SuggestionPanelVisualModal(discord.ui.Modal):
    def __init__(self, guild_id: int) -> None:
        super().__init__(title="Sugerencias · Diseño")
        self.guild_id = guild_id
        self.footer_input = discord.ui.TextInput(
            label="Pie del embed",
            default=guild_config_get(guild_id, "suggestion_panel_footer") or SUGGESTION_PANEL_FOOTER_DEFAULT,
            required=False,
            max_length=2048,
        )
        self.button_input = discord.ui.TextInput(
            label="Texto del botón",
            default=guild_config_get(guild_id, "suggestion_panel_button_label") or SUGGESTION_PANEL_BUTTON_DEFAULT,
            required=True,
            max_length=80,
        )
        self.image_input = discord.ui.TextInput(
            label="Imagen grande (URL o variable)",
            default=guild_config_get(guild_id, "suggestion_panel_image") or SUGGESTION_PANEL_IMAGE_DEFAULT,
            required=False,
            max_length=500,
            placeholder="https://… o {serverbanner}",
        )
        self.thumbnail_input = discord.ui.TextInput(
            label="Miniatura (URL o variable)",
            default=guild_config_get(guild_id, "suggestion_panel_thumbnail") or SUGGESTION_PANEL_THUMBNAIL_DEFAULT,
            required=False,
            max_length=500,
            placeholder="https://… o {servericon}",
        )
        for item in (
            self.footer_input,
            self.button_input,
            self.image_input,
            self.thumbnail_input,
        ):
            self.add_item(item)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        button_label = self.button_input.value.strip()
        image = self.image_input.value.strip()
        thumbnail = self.thumbnail_input.value.strip()

        if not button_label:
            await interaction.response.send_message(
                "❌ El texto del botón no puede quedar vacío.",
                ephemeral=True,
            )
            return

        for label, value in (("imagen", image), ("miniatura", thumbnail)):
            if (
                value
                and not re.match(r"^https?://", value, re.IGNORECASE)
                and not VAR_PATTERN.search(value)
            ):
                await interaction.response.send_message(
                    f"❌ La {label} debe ser una URL `http(s)://…` o una variable de imagen.",
                    ephemeral=True,
                )
                return

        guild_config_set(self.guild_id, "suggestion_panel_footer", self.footer_input.value.strip())
        guild_config_set(self.guild_id, "suggestion_panel_button_label", button_label)
        guild_config_set(self.guild_id, "suggestion_panel_image", image)
        guild_config_set(self.guild_id, "suggestion_panel_thumbnail", thumbnail)

        await interaction.response.defer(ephemeral=True)
        await suggestion_ensure_panel(interaction.guild)
        await interaction.followup.send(
            "✅ Diseño del panel de sugerencias guardado y sincronizado.",
            ephemeral=True,
        )


class SuggestionPanelMessageSetupView(discord.ui.View):
    def __init__(self, guild_id: int, owner_id: int) -> None:
        super().__init__(timeout=900)
        self.guild_id = guild_id
        self.owner_id = owner_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("Este editor no es tuyo.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Contenido", style=discord.ButtonStyle.primary, row=0)
    async def content(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await interaction.response.send_modal(SuggestionPanelContentModal(self.guild_id))

    @discord.ui.button(label="Diseño", style=discord.ButtonStyle.secondary, row=0)
    async def design(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await interaction.response.send_modal(SuggestionPanelVisualModal(self.guild_id))

    @discord.ui.button(label="Sincronizar", style=discord.ButtonStyle.secondary, row=0)
    async def sync(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await interaction.response.defer(ephemeral=True)
        await suggestion_ensure_panel(interaction.guild)
        await interaction.followup.send(
            "✅ Panel de sugerencias sincronizado.",
            ephemeral=True,
        )

    @discord.ui.button(label="Volver", style=discord.ButtonStyle.secondary, row=1)
    async def back(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await interaction.response.edit_message(
            content=heraldo_messages_setup_content(),
            embed=None,
            view=HeraldoMessagesSetupView(self.guild_id, self.owner_id),
        )


MESSAGE_STUDIO_LABELS = {
    "verification": "✅ Panel de verificación",
    "verify_dm": "📩 DM de verificación",
    "suggestions": "💡 Panel de sugerencias",
    "honeypot": "🍯 Aviso del Honeypot",
    "condemnation": "☠️ Tarjeta de condenados",
}

MESSAGE_STUDIO_VARIABLE_CONTEXT = {
    "verification": (
        "El mensaje del panel recibe contexto de servidor y canal. "
        "El mensaje de éxito recibe además el miembro que se verificó."
    ),
    "verify_dm": (
        "Este DM recibe contexto de servidor y del miembro verificado. "
        "No depende de un canal del servidor."
    ),
    "suggestions": (
        "El panel persistente se renderiza con contexto del servidor. "
        "Usa variables de servidor e imágenes como {servericon} o {serverbanner}."
    ),
    "honeypot": (
        "El aviso fijado recibe contexto del servidor y del canal trampa donde está publicado."
    ),
    "condemnation": (
        "La tarjeta real recibe los datos del caso, del condenado y del moderador. "
        "La vista previa usa datos de ejemplo sin tocar ningún caso real."
    ),
}


def message_studio_preview(
    kind: str,
    guild: discord.Guild,
    user: discord.Member,
    channel: discord.abc.GuildChannel | None,
) -> discord.Embed:
    if kind == "verification":
        rendered = render_vars(
            get_verify_panel_text(guild.id),
            VarContext(guild, None, channel),
            2000,
        )
        return stamp_embed(_content_embed(rendered), guild)
    if kind == "verify_dm":
        return build_verification_welcome_embed(member=user, guild=guild)
    if kind == "suggestions":
        return suggestion_panel_embed(guild)
    if kind == "honeypot":
        if channel is not None and getattr(channel, "guild", None) == guild:
            return hp_warning_embed(channel)
        cfg = hp_warning_custom(guild.id)
        try:
            color = discord.Color(int(cfg["color"].lstrip("#"), 16))
        except (TypeError, ValueError):
            color = discord.Color.gold()
        embed = discord.Embed(
            title=render_vars(cfg["title"], VarContext(guild), 256),
            description=render_vars(cfg["description"], VarContext(guild), 4096),
            color=color,
        )
        image = render_url_var(cfg["image"], VarContext(guild)) if cfg["image"] else ""
        if image:
            embed.set_image(url=image)
        thumbnail = render_url_var(cfg["thumbnail"], VarContext(guild)) if cfg["thumbnail"] else ""
        if thumbnail:
            embed.set_thumbnail(url=thumbnail)
        footer = render_vars(cfg["footer"], VarContext(guild), 2048) if cfg["footer"] else ""
        if footer:
            embed.set_footer(text=footer)
        return embed
    if kind == "condemnation":
        return condemnation_template_preview(guild, user)
    raise ValueError(f"Tipo de mensaje no soportado: {kind}")


def message_studio_content(kind: str, mode: str = "preview", notice: str | None = None) -> str:
    label = MESSAGE_STUDIO_LABELS.get(kind, kind)
    if mode == "edit":
        body = (
            f"✏️ **Edit · {label}**\n"
            "Modifica únicamente propiedades que este mensaje usa de verdad. "
            "Los cambios se guardan por servidor."
        )
    elif mode == "variables":
        body = (
            f"🧩 **Variables · {label}**\n"
            f"{MESSAGE_STUDIO_VARIABLE_CONTEXT.get(kind, '')}\n\n"
            "Consulta el catálogo completo con /list variables. "
            "Una variable que no tenga el contexto necesario queda sin resolver."
        )
    else:
        body = (
            f"👁️ **Preview · {label}**\n"
            "Vista previa con la configuración guardada actualmente."
        )
    return (f"✅ {notice}\n\n" if notice else "") + body


class DefaultMessageStudioView(discord.ui.View):
    def __init__(
        self,
        guild_id: int,
        owner_id: int,
        kind: str,
        mode: str = "preview",
        return_to: str = "messages_command",
    ) -> None:
        super().__init__(timeout=900)
        if kind not in MESSAGE_STUDIO_LABELS:
            raise ValueError(f"Mensaje no soportado: {kind}")
        self.guild_id = guild_id
        self.owner_id = owner_id
        self.kind = kind
        self.mode = mode if mode in {"preview", "edit", "variables"} else "preview"
        self.return_to = return_to

        preview_btn = discord.ui.Button(
            label="Preview",
            style=discord.ButtonStyle.primary if self.mode == "preview" else discord.ButtonStyle.secondary,
            row=0,
            disabled=self.mode == "preview",
        )
        preview_btn.callback = self.show_preview
        self.add_item(preview_btn)

        edit_btn = discord.ui.Button(
            label="Edit",
            style=discord.ButtonStyle.primary if self.mode == "edit" else discord.ButtonStyle.secondary,
            row=0,
            disabled=self.mode == "edit",
        )
        edit_btn.callback = self.show_edit
        self.add_item(edit_btn)

        vars_btn = discord.ui.Button(
            label="Variables",
            style=discord.ButtonStyle.primary if self.mode == "variables" else discord.ButtonStyle.secondary,
            row=0,
            disabled=self.mode == "variables",
        )
        vars_btn.callback = self.show_variables
        self.add_item(vars_btn)

        back_btn = discord.ui.Button(label="Volver", style=discord.ButtonStyle.secondary, row=0)
        back_btn.callback = self.go_back
        self.add_item(back_btn)

        if self.mode == "edit":
            self._add_edit_controls()
        elif self.mode == "preview":
            self._add_component_preview()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("Este editor no es tuyo.", ephemeral=True)
            return False
        return True

    async def _switch(self, interaction: discord.Interaction, mode: str) -> None:
        embed = message_studio_preview(
            self.kind,
            interaction.guild,
            interaction.user,
            interaction.channel,
        )
        await interaction.response.edit_message(
            content=message_studio_content(self.kind, mode),
            embed=embed if mode != "variables" else None,
            view=DefaultMessageStudioView(
                self.guild_id, self.owner_id, self.kind, mode, self.return_to
            ),
        )

    async def show_preview(self, interaction: discord.Interaction) -> None:
        await self._switch(interaction, "preview")

    async def show_edit(self, interaction: discord.Interaction) -> None:
        await self._switch(interaction, "edit")

    async def show_variables(self, interaction: discord.Interaction) -> None:
        await self._switch(interaction, "variables")

    async def go_back(self, interaction: discord.Interaction) -> None:
        if self.return_to == "messages_setup":
            await interaction.response.edit_message(
                content=heraldo_messages_setup_content(),
                embed=None,
                view=HeraldoMessagesSetupView(self.guild_id, self.owner_id),
            )
            return
        await interaction.response.edit_message(
            content=heraldo_messages_command_content(),
            embed=None,
            view=HeraldoMessagesView(self.guild_id, self.owner_id),
        )

    def _add_component_preview(self) -> None:
        if self.kind == "verification":
            self.add_item(
                discord.ui.Button(
                    label=get_verify_button_label(self.guild_id)[:80],
                    style=discord.ButtonStyle.success,
                    disabled=True,
                    row=1,
                )
            )
        elif self.kind == "suggestions":
            self.add_item(
                discord.ui.Button(
                    label=(
                        guild_config_get(self.guild_id, "suggestion_panel_button_label")
                        or SUGGESTION_PANEL_BUTTON_DEFAULT
                    )[:80],
                    style=discord.ButtonStyle.primary,
                    disabled=True,
                    row=1,
                )
            )
        elif self.kind == "condemnation":
            label = condemnation_template_get(self.guild_id, "button_label").strip()
            url = condemnation_template_get(self.guild_id, "button_url").strip()
            if label and url:
                self.add_item(
                    discord.ui.Button(
                        label=label[:80],
                        style=discord.ButtonStyle.link,
                        url=url,
                        row=1,
                    )
                )

    def _action_button(self, label: str, callback, *, row: int = 1, style=discord.ButtonStyle.secondary) -> None:
        button = discord.ui.Button(label=label, style=style, row=row)
        button.callback = callback
        self.add_item(button)

    def _add_edit_controls(self) -> None:
        if self.kind == "verification":
            self._action_button("🎨 Visual", self.edit_verification, style=discord.ButtonStyle.primary)
        elif self.kind == "verify_dm":
            self._action_button("🎨 Visual", self.edit_verify_dm_content, style=discord.ButtonStyle.primary)
            self._action_button("🖼️ Recurso visual", self.edit_verify_dm_visual)
        elif self.kind == "suggestions":
            self._action_button("🎨 Visual", self.edit_suggestion_content, style=discord.ButtonStyle.primary)
            self._action_button("🖼️ Imagen / botón", self.edit_suggestion_visual)
        elif self.kind == "honeypot":
            self._action_button("🎨 Visual", self.edit_honeypot, style=discord.ButtonStyle.primary)
        elif self.kind == "condemnation":
            self._action_button("🎨 Visual", self.edit_condemnation_core, style=discord.ButtonStyle.primary)
            self._action_button("🏷️ Etiquetas", self.edit_condemnation_labels)
            self._action_button("🏷️ Más etiquetas", self.edit_condemnation_more, row=2)
            self._action_button("🔗 Botón", self.edit_condemnation_button, row=2)
            self._action_button("⏳ Duración", self.edit_condemnation_duration, row=2)

    async def edit_verification(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_modal(VerifyTextsModal(self.guild_id))

    async def edit_verify_dm_content(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_modal(VerifyDmEditorContentModal(self.guild_id))

    async def edit_verify_dm_visual(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_modal(VerifyDmEditorVisualModal(self.guild_id))

    async def edit_suggestion_content(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_modal(SuggestionPanelContentModal(self.guild_id))

    async def edit_suggestion_visual(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_modal(SuggestionPanelVisualModal(self.guild_id))

    async def edit_honeypot(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_modal(HoneypotWarningEmbedModal(self.guild_id))

    async def edit_condemnation_core(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_modal(
            CondemnationCoreModal(interaction.guild.id, f"studio:{self.return_to}")
        )

    async def edit_condemnation_labels(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_modal(
            CondemnationDetailsModal(interaction.guild.id, f"studio:{self.return_to}")
        )

    async def edit_condemnation_more(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_modal(
            CondemnationMoreDetailsModal(interaction.guild.id, f"studio:{self.return_to}")
        )

    async def edit_condemnation_button(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_modal(
            CondemnationButtonUrlModal(interaction.guild.id, f"studio:{self.return_to}")
        )

    async def edit_condemnation_duration(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_modal(
            CondemnationDurationModal(interaction.guild.id, f"studio:{self.return_to}")
        )


async def open_default_message_studio(
    interaction: discord.Interaction,
    kind: str,
    owner_id: int,
    return_to: str,
    *,
    notice: str | None = None,
) -> None:
    embed = message_studio_preview(kind, interaction.guild, interaction.user, interaction.channel)
    kwargs = dict(
        content=message_studio_content(kind, "preview", notice),
        embed=embed,
        view=DefaultMessageStudioView(
            interaction.guild.id, owner_id, kind, "preview", return_to
        ),
    )
    if interaction.response.is_done():
        await interaction.edit_original_response(**kwargs)
    else:
        await interaction.response.edit_message(**kwargs)


LOG_TEMPLATE_CATEGORIES = {
    "general": ("📜 General", "Logs que no pertenecen a otra categoría."),
    "verification": ("✅ Verificación", "Verificación, orientación y accesos."),
    "condemnation": ("☠️ Condenas", "Condenas, liberaciones y perdones."),
    "honeypot": ("🍯 Honeypot", "Disparos, pausas y acciones del honeypot."),
    "raid": ("Raid Protection", "Detección y acciones de protección contra raids."),
    "purge": ("Purgas", "Purgas manuales y automáticas."),
    "backup": ("💾 Backups / plantilla", "Copias y sincronización de la plantilla del servidor."),
    "configuration": ("⚙️ Configuración", "Cambios de canales, roles y configuración."),
    "suggestions": ("💡 Sugerencias", "Creación y resolución de sugerencias."),
    "errors": ("⚠️ Errores / avisos", "Errores, permisos insuficientes y advertencias."),
}

LOG_EVENT_CATALOG = {
    "general": [
        ("heraldo_ready", "🪽 El Heraldo está listo para configurarse"),
        ("manual_check", "🔧 Chequeo manual"),
        ("mass_check_started", "🔍 Chequeo masivo iniciado"),
        ("channel_merge_completed", "🔀 Fusión de canales completada"),
        ("channel_merge_partial", "⚠️ Fusión de canales parcial"),
    ],
    "verification": [
        ("verified_path", "✅ Verificado"),
        ("age_verification", "✅ Verificación de edad"),
        ("verification_expired", "⏰ Verificación vencida"),
        ("verification_kick", "👢 Kick — No se verificó"),
        ("verification_ban", "🔨 Ban — No se verificó"),
        ("verification_panel_published", "⚙️ Panel de verificación publicado"),
        ("verification_texts_updated", "⚙️ Textos de verificación actualizados"),
        ("verification_dm_updated", "⚙️ DM de bienvenida actualizado"),
        ("verification_updated", "⚙️ Verificación actualizada"),
    ],
    "condemnation": [
        ("condemnation_applied", "☠️ Condena aplicada"),
        ("condemnation_restored", "☠️ Condena restaurada al reingresar"),
        ("condemnation_rejected", "⚠️ Condena rechazada"),
        ("condemnation_reaction_rejected", "⚠️ Condena por reacción rechazada"),
        ("condemnation_pardoned", "🕊️ Condena perdonada"),
        ("condemnation_lifted", "🕊️ Condena levantada"),
        ("condemnation_card_not_deleted", "⚠️ Tarjeta de condena no eliminada"),
    ],
    "honeypot": [
        ("honeypot_paused", "⏸️ Honeypot pausado (protección contra fallos)"),
        ("honeypot_trap_deleted", "🍯 Canal trampa eliminado"),
        ("honeypot_updated", "⚙️ Honeypot actualizado"),
        ("honeypot_trap_added", "🍯 Canal trampa añadido"),
        ("honeypot_trap_created", "🍯 Canal trampa creado"),
        ("honeypot_trap_removed", "🍯 Canal trampa quitado"),
        ("honeypot_embed_updated", "⚙️ Embed del honeypot actualizado"),
        ("honeypot_resumed", "▶️ Honeypot reanudado"),
    ],
    "raid": [("raid_updated", "⚙️ Raid Protection actualizada")],
    "purge": [
        ("purge_failed", "⚠️ Purga fallida"),
        ("purge_completed", "Purga completada"),
        ("honeypot_purge_completed", "🍯 Purga del honeypot completada"),
    ],
    "backup": [
        ("template_backup_failed", "⚠️ Falló la copia de seguridad de la plantilla"),
        ("template_synced_dm_failed", "Plantilla sincronizada (mensaje privado no enviado)"),
        ("template_backup_updated", "⚙️ Copia de seguridad de la plantilla actualizada"),
        ("template_synced_manual", "Plantilla sincronizada manualmente"),
    ],
    "configuration": [
        ("log_channel_updated", "⚙️ Canal de logs actualizado"),
        ("condemnation_channel_updated", "⚙️ Canal de condenas actualizado"),
        ("motw_schedule_updated", "⚙️ Horario de Miembro de la Semana actualizado"),
        ("motw_channel_updated", "⚙️ Canal de Miembro de la Semana actualizado"),
    ],
    "suggestions": [
        ("suggestion_created", "💡 Nueva sugerencia"),
        ("suggestion_accepted", "✅ Sugerencia aceptada"),
        ("suggestion_rejected", "❌ Sugerencia rechazada"),
    ],
    "errors": [
        ("verification_not_configured", "⚠️ Verificación sin configurar"),
        ("verification_blocked", "⚠️ Verificación bloqueada"),
        ("verification_error", "⚠️ Error al verificar"),
        ("verification_timeout_error", "⚠️ Error al aplicar el timeout de verificación"),
        ("kick_error", "⚠️ Error al expulsar"),
        ("invite_error", "⚠️ Error de invite"),
        ("remove_unverified_error", "⚠️ No pude quitar Sin Verificar"),
        ("welcome_dm_error", "⚠️ No pude enviar el DM de bienvenida"),
        ("condemnation_roles_error", "⚠️ No pude re-quitar roles a un condenado"),
        ("condemnation_reapply_error", "⚠️ No pude reaplicar la condena al reingresar"),
        ("suggestion_dm_error", "⚠️ No pude enviar una sugerencia por DM"),
    ],
}

LOG_TEMPLATE_DEFAULTS = {
    "title": "{titulo_log}",
    "description": "{detalle_log}",
    "footer": "El Heraldo 🪽 · {servidor}",
    "color": "",
    "image": "",
    "thumbnail": "",
    "timestamp": "1",
    "fields": "",
}


def _log_normalize_title(title: str) -> str:
    raw = unicodedata.normalize("NFKD", title or "")
    return "".join(ch for ch in raw if not unicodedata.combining(ch)).strip().lower()


def _log_slug(title: str) -> str:
    value = _log_normalize_title(title)
    value = re.sub(r"[^a-z0-9]+", "_", value).strip("_")
    return value[:80] or "event"


def _log_catalog_event(category: str, event_key: str | None) -> tuple[str, str]:
    events = LOG_EVENT_CATALOG.get(category) or LOG_EVENT_CATALOG["general"]
    if event_key:
        for key, label in events:
            if key == event_key:
                return key, label
    return events[0]


def _log_template_key(scope: str, field: str) -> str:
    return f"log_template.{scope}.{field}"


def log_template_get(guild_id: int, category: str, field: str, event_key: str | None = None) -> str:
    if category not in LOG_TEMPLATE_CATEGORIES:
        category = "general"
    if event_key:
        stored = guild_config_get(guild_id, _log_template_key(f"event.{event_key}", field))
        if stored is not None:
            return stored
    stored = guild_config_get(guild_id, _log_template_key(category, field))
    if stored is not None:
        return stored
    return LOG_TEMPLATE_DEFAULTS.get(field, "")


def log_template_set(
    guild_id: int, category: str, field: str, value: str, event_key: str | None = None,
) -> None:
    if category not in LOG_TEMPLATE_CATEGORIES:
        raise ValueError("Categoría de log no válida")
    if field not in LOG_TEMPLATE_DEFAULTS:
        raise ValueError("Campo de plantilla de log no válido")
    scope = f"event.{event_key}" if event_key else category
    guild_config_set(guild_id, _log_template_key(scope, field), value)


def log_template_reset(guild_id: int, category: str, event_key: str | None = None) -> None:
    scope = f"event.{event_key}" if event_key else category
    conn = db_connect()
    conn.execute(
        "DELETE FROM guild_settings WHERE guild_id = ? AND key LIKE ?",
        (guild_id, f"log_template.{scope}.%"),
    )
    conn.commit()
    conn.close()


def log_event_category(title: str) -> str:
    normalized = _log_normalize_title(title)
    for category, events in LOG_EVENT_CATALOG.items():
        for _, label in events:
            if _log_normalize_title(label) == normalized:
                return category
    if any(word in normalized for word in ("error", "fall", "rechaz", "no pude", "sin permisos", "⚠")):
        return "errors"
    if any(word in normalized for word in ("conden", "perdon", "liberad")):
        return "condemnation"
    if any(word in normalized for word in ("honeypot", "trampa")):
        return "honeypot"
    if "raid" in normalized:
        return "raid"
    if "purga" in normalized:
        return "purge"
    if any(word in normalized for word in ("verific", "orientacion", "sin verificar", "tentad")):
        return "verification"
    if any(word in normalized for word in ("plantilla", "template", "copia de seguridad", "backup")):
        return "backup"
    if "suger" in normalized:
        return "suggestions"
    if any(word in normalized for word in ("config", "canal", "rol actualizado", "setup")):
        return "configuration"
    return "general"


def log_event_key(title: str, category: str | None = None) -> str:
    category = category or log_event_category(title)
    normalized = _log_normalize_title(title)
    for key, label in LOG_EVENT_CATALOG.get(category, []):
        if _log_normalize_title(label) == normalized:
            return key
    return "dynamic_" + _log_slug(title)

def _log_special_vars(text: str, title: str, description: str, category: str, event_key: str) -> str:
    return (
        (text or "")
        .replace("{titulo_log}", title or "")
        .replace("{detalle_log}", description or "")
        .replace("{categoria_log}", LOG_TEMPLATE_CATEGORIES.get(category, LOG_TEMPLATE_CATEGORIES["general"])[0])
        .replace("{tipo_log}", event_key)
    )


def _log_render(
    text: str, guild: discord.Guild, title: str, description: str,
    category: str, event_key: str, limit: int,
) -> str:
    value = _log_special_vars(text, title, description, category, event_key)
    try:
        return render_vars(value, VarContext(guild, None, None), limit, plain=True)
    except Exception:
        return value[:limit]


def _log_render_url(
    text: str, guild: discord.Guild, title: str, description: str,
    category: str, event_key: str,
) -> str:
    value = _log_render(text, guild, title, description, category, event_key, 2000).strip()
    return value if re.match(r"^https?://", value, re.IGNORECASE) else ""


def _log_parse_fields(
    raw: str, guild: discord.Guild, title: str, description: str,
    category: str, event_key: str,
) -> list[tuple[str, str, bool]]:
    result: list[tuple[str, str, bool]] = []
    for line in (raw or "").splitlines():
        if not line.strip():
            continue
        parts = [part.strip() for part in line.split("|", 2)]
        if len(parts) < 2:
            continue
        name = _log_render(parts[0], guild, title, description, category, event_key, 256) or "\u200b"
        value = _log_render(parts[1], guild, title, description, category, event_key, 1024) or "\u200b"
        inline = len(parts) >= 3 and parts[2].lower() in {"1", "si", "sí", "true", "inline"}
        result.append((name, value, inline))
        if len(result) >= 10:
            break
    return result


def build_log_template_embed(
    guild: discord.Guild,
    title: str,
    description: str,
    original_color: discord.Color,
    *,
    category: str | None = None,
    event_key: str | None = None,
) -> discord.Embed:
    category = category if category in LOG_TEMPLATE_CATEGORIES else log_event_category(title)
    event_key = event_key or log_event_key(title, category)
    custom_color = log_template_get(guild.id, category, "color", event_key).strip().lstrip("#")
    color_value = original_color
    if custom_color and re.fullmatch(r"[0-9a-fA-F]{6}", custom_color):
        color_value = discord.Color(int(custom_color, 16))

    embed = discord.Embed(
        title=_log_render(
            log_template_get(guild.id, category, "title", event_key),
            guild, title, description, category, event_key, 256,
        ) or None,
        description=_log_render(
            log_template_get(guild.id, category, "description", event_key),
            guild, title, description, category, event_key, 4096,
        ) or None,
        color=color_value,
        timestamp=(
            datetime.now(timezone.utc)
            if log_template_get(guild.id, category, "timestamp", event_key) != "0"
            else None
        ),
    )
    footer = _log_render(
        log_template_get(guild.id, category, "footer", event_key),
        guild, title, description, category, event_key, 2048,
    ).strip()
    if footer:
        embed.set_footer(text=footer)
    image = _log_render_url(
        log_template_get(guild.id, category, "image", event_key),
        guild, title, description, category, event_key,
    )
    if image:
        embed.set_image(url=image)
    thumbnail = _log_render_url(
        log_template_get(guild.id, category, "thumbnail", event_key),
        guild, title, description, category, event_key,
    )
    if thumbnail:
        embed.set_thumbnail(url=thumbnail)
    for name, value, inline in _log_parse_fields(
        log_template_get(guild.id, category, "fields", event_key),
        guild, title, description, category, event_key,
    ):
        embed.add_field(name=name, value=value, inline=inline)
    return embed


def log_template_preview(
    guild: discord.Guild, category: str, event_key: str | None = None,
) -> discord.Embed:
    event_key, event_label = _log_catalog_event(category, event_key)
    return build_log_template_embed(
        guild,
        event_label,
        f"Este es un ejemplo del contenido dinámico que genera el evento «{event_label}».",
        discord.Color.blurple(),
        category=category,
        event_key=event_key,
    )


class LogTemplateContentModal(discord.ui.Modal):
    def __init__(
        self, guild_id: int, category: str, event_key: str,
        owner_id: int, return_to: str,
    ) -> None:
        _, event_label = _log_catalog_event(category, event_key)
        super().__init__(title=f"Log · {event_label}"[:45])
        self.guild_id = guild_id
        self.category = category
        self.event_key = event_key
        self.owner_id = owner_id
        self.return_to = return_to
        self.title_input = discord.ui.TextInput(
            label="Título",
            default=log_template_get(guild_id, category, "title", event_key),
            required=False,
            max_length=256,
            placeholder="{titulo_log}",
        )
        self.description_input = discord.ui.TextInput(
            label="Descripción",
            style=discord.TextStyle.paragraph,
            default=log_template_get(guild_id, category, "description", event_key),
            required=False,
            max_length=4000,
            placeholder="{detalle_log}",
        )
        self.footer_input = discord.ui.TextInput(
            label="Footer",
            default=log_template_get(guild_id, category, "footer", event_key),
            required=False,
            max_length=2048,
        )
        self.fields_input = discord.ui.TextInput(
            label="Campos · Nombre | Valor | inline",
            style=discord.TextStyle.paragraph,
            default=log_template_get(guild_id, category, "fields", event_key),
            required=False,
            max_length=4000,
            placeholder="Servidor | {servidor}\nTipo | {tipo_log} | inline",
        )
        for item in (self.title_input, self.description_input, self.footer_input, self.fields_input):
            self.add_item(item)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        log_template_set(
            self.guild_id, self.category, "title",
            self.title_input.value.strip() or "{titulo_log}", self.event_key,
        )
        log_template_set(
            self.guild_id, self.category, "description",
            self.description_input.value.strip() or "{detalle_log}", self.event_key,
        )
        log_template_set(
            self.guild_id, self.category, "footer",
            self.footer_input.value.strip(), self.event_key,
        )
        log_template_set(
            self.guild_id, self.category, "fields",
            self.fields_input.value.strip(), self.event_key,
        )
        await log_template_editor_update(
            interaction, self.owner_id, self.category,
            self.event_key, self.return_to, "Contenido actualizado.",
        )


class LogTemplateVisualModal(discord.ui.Modal):
    def __init__(
        self, guild_id: int, category: str, event_key: str,
        owner_id: int, return_to: str,
    ) -> None:
        _, event_label = _log_catalog_event(category, event_key)
        super().__init__(title=f"Diseño · {event_label}"[:45])
        self.guild_id = guild_id
        self.category = category
        self.event_key = event_key
        self.owner_id = owner_id
        self.return_to = return_to
        self.color_input = discord.ui.TextInput(
            label="Color HEX · vacío = color original",
            default=log_template_get(guild_id, category, "color", event_key),
            required=False,
            max_length=7,
            placeholder="5865F2",
        )
        self.image_input = discord.ui.TextInput(
            label="Imagen grande · URL o variable",
            default=log_template_get(guild_id, category, "image", event_key),
            required=False,
            max_length=2000,
        )
        self.thumbnail_input = discord.ui.TextInput(
            label="Miniatura · URL o variable",
            default=log_template_get(guild_id, category, "thumbnail", event_key),
            required=False,
            max_length=2000,
        )
        self.timestamp_input = discord.ui.TextInput(
            label="Timestamp · sí/no",
            default=(
                "sí"
                if log_template_get(guild_id, category, "timestamp", event_key) != "0"
                else "no"
            ),
            required=True,
            max_length=3,
        )
        for item in (self.color_input, self.image_input, self.thumbnail_input, self.timestamp_input):
            self.add_item(item)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        color = self.color_input.value.strip().lstrip("#")
        if color and not re.fullmatch(r"[0-9a-fA-F]{6}", color):
            await interaction.response.send_message(
                "❌ El color debe ser HEX de 6 caracteres.", ephemeral=True
            )
            return
        for label, value in (
            ("imagen", self.image_input.value.strip()),
            ("miniatura", self.thumbnail_input.value.strip()),
        ):
            if value and "{" not in value and not re.match(r"^https?://", value, re.IGNORECASE):
                await interaction.response.send_message(
                    f"❌ La {label} debe ser una URL http(s) o una variable.",
                    ephemeral=True,
                )
                return
        timestamp_value = self.timestamp_input.value.strip().lower()
        if timestamp_value not in {"si", "sí", "s", "1", "true", "no", "n", "0", "false"}:
            await interaction.response.send_message(
                "❌ Timestamp debe ser sí o no.", ephemeral=True
            )
            return
        log_template_set(
            self.guild_id, self.category, "color", color, self.event_key
        )
        log_template_set(
            self.guild_id, self.category, "image",
            self.image_input.value.strip(), self.event_key,
        )
        log_template_set(
            self.guild_id, self.category, "thumbnail",
            self.thumbnail_input.value.strip(), self.event_key,
        )
        log_template_set(
            self.guild_id, self.category, "timestamp",
            "0" if timestamp_value in {"no", "n", "0", "false"} else "1",
            self.event_key,
        )
        await log_template_editor_update(
            interaction, self.owner_id, self.category,
            self.event_key, self.return_to, "Diseño actualizado.",
        )


async def log_template_editor_update(
    interaction: discord.Interaction,
    owner_id: int,
    category: str,
    event_key: str,
    return_to: str,
    notice: str | None = None,
) -> None:
    content = log_template_editor_content(category, event_key, mode="edit")
    if notice:
        content = f"✅ {notice}\n\n" + content
    view = LogTemplateEditorView(
        interaction.guild.id, owner_id, category, event_key, return_to, mode="edit"
    )
    try:
        await interaction.response.edit_message(
            content=content,
            embed=log_template_preview(interaction.guild, category, event_key),
            view=view,
        )
    except discord.HTTPException:
        if not interaction.response.is_done():
            await interaction.response.send_message(
                content=content,
                embed=log_template_preview(interaction.guild, category, event_key),
                view=view,
                ephemeral=True,
            )
        else:
            await interaction.followup.send(
                content=content,
                embed=log_template_preview(interaction.guild, category, event_key),
                view=view,
                ephemeral=True,
            )


def log_template_editor_content(
    category: str,
    event_key: str | None = None,
    *,
    mode: str = "preview",
) -> str:
    event_key, event_label = _log_catalog_event(category, event_key)
    category_label, description = LOG_TEMPLATE_CATEGORIES.get(
        category, LOG_TEMPLATE_CATEGORIES["general"]
    )
    if mode == "variables":
        return (
            f"🧩 **Variables · {event_label}**\n"
            f"Módulo: {category_label}\n\n"
            "Variables propias de este log: {titulo_log}, {detalle_log}, "
            "{categoria_log}, {tipo_log}.\n"
            "El renderer de logs usa contexto del servidor; los datos concretos del evento "
            "se conservan dentro de {titulo_log} y {detalle_log}."
        )
    if mode == "edit":
        return (
            f"✏️ **Edit · {event_label}**\n"
            f"Módulo: {category_label}\n{description}\n\n"
            "Edita únicamente esta plantilla. Los demás eventos mantienen su configuración."
        )
    return (
        f"👁️ **Preview · {event_label}**\n"
        f"Módulo: {category_label}\n{description}"
    )


class LogTemplateEditorView(discord.ui.View):
    def __init__(
        self,
        guild_id: int,
        owner_id: int,
        category: str = "general",
        event_key: str | None = None,
        return_to: str = "messages_setup",
        mode: str = "preview",
    ) -> None:
        super().__init__(timeout=900)
        self.guild_id = guild_id
        self.owner_id = owner_id
        self.category = category if category in LOG_TEMPLATE_CATEGORIES else "general"
        self.event_key, _ = _log_catalog_event(self.category, event_key)
        self.return_to = return_to
        self.mode = mode if mode in {"preview", "edit", "variables"} else "preview"

        category_select = discord.ui.Select(
            placeholder="1. Elige el módulo de logs",
            min_values=1,
            max_values=1,
            options=[
                discord.SelectOption(
                    label=label.split(" ", 1)[-1],
                    value=key,
                    emoji=label.split(" ", 1)[0],
                    description=description[:100],
                    default=(key == self.category),
                )
                for key, (label, description) in LOG_TEMPLATE_CATEGORIES.items()
            ],
            row=0,
        )
        category_select.callback = self.change_category
        self.add_item(category_select)

        event_select = discord.ui.Select(
            placeholder="2. Elige el tipo exacto de log",
            min_values=1,
            max_values=1,
            options=[
                discord.SelectOption(
                    label=label[:100],
                    value=key,
                    default=(key == self.event_key),
                )
                for key, label in LOG_EVENT_CATALOG.get(self.category, [])[:25]
            ],
            row=1,
        )
        event_select.callback = self.change_event
        self.add_item(event_select)

        preview_btn = discord.ui.Button(
            label="Preview",
            style=discord.ButtonStyle.primary if self.mode == "preview" else discord.ButtonStyle.secondary,
            disabled=self.mode == "preview",
            row=2,
        )
        preview_btn.callback = self.show_preview
        self.add_item(preview_btn)

        edit_btn = discord.ui.Button(
            label="Edit",
            style=discord.ButtonStyle.primary if self.mode == "edit" else discord.ButtonStyle.secondary,
            disabled=self.mode == "edit",
            row=2,
        )
        edit_btn.callback = self.show_edit
        self.add_item(edit_btn)

        vars_btn = discord.ui.Button(
            label="Variables",
            style=discord.ButtonStyle.primary if self.mode == "variables" else discord.ButtonStyle.secondary,
            disabled=self.mode == "variables",
            row=2,
        )
        vars_btn.callback = self.show_variables
        self.add_item(vars_btn)

        back_btn = discord.ui.Button(label="Volver", style=discord.ButtonStyle.secondary, row=2)
        back_btn.callback = self.back
        self.add_item(back_btn)

        if self.mode == "edit":
            content_btn = discord.ui.Button(
                label="Visual", style=discord.ButtonStyle.primary, row=3
            )
            content_btn.callback = self.edit_content
            self.add_item(content_btn)

            design_btn = discord.ui.Button(
                label="Diseño", style=discord.ButtonStyle.secondary, row=3
            )
            design_btn.callback = self.edit_design
            self.add_item(design_btn)

            reset_btn = discord.ui.Button(
                label="Restaurar este evento",
                style=discord.ButtonStyle.danger,
                row=3,
            )
            reset_btn.callback = self.reset_event
            self.add_item(reset_btn)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message(
                "Este editor de logs no es tuyo.", ephemeral=True
            )
            return False
        return True

    async def _render(
        self,
        interaction: discord.Interaction,
        *,
        category: str | None = None,
        event_key: str | None = None,
        mode: str | None = None,
    ) -> None:
        category = category or self.category
        event_key, _ = _log_catalog_event(category, event_key or self.event_key)
        mode = mode or self.mode
        await interaction.response.edit_message(
            content=log_template_editor_content(category, event_key, mode=mode),
            embed=(
                None
                if mode == "variables"
                else log_template_preview(interaction.guild, category, event_key)
            ),
            view=LogTemplateEditorView(
                self.guild_id,
                self.owner_id,
                category,
                event_key,
                self.return_to,
                mode=mode,
            ),
        )

    async def change_category(self, interaction: discord.Interaction) -> None:
        values = interaction.data.get("values") if interaction.data else []
        category = (
            values[0]
            if values and values[0] in LOG_TEMPLATE_CATEGORIES
            else "general"
        )
        event_key, _ = _log_catalog_event(category, None)
        await self._render(interaction, category=category, event_key=event_key)

    async def change_event(self, interaction: discord.Interaction) -> None:
        values = interaction.data.get("values") if interaction.data else []
        event_key, _ = _log_catalog_event(
            self.category, values[0] if values else None
        )
        await self._render(interaction, event_key=event_key)

    async def show_preview(self, interaction: discord.Interaction) -> None:
        await self._render(interaction, mode="preview")

    async def show_edit(self, interaction: discord.Interaction) -> None:
        await self._render(interaction, mode="edit")

    async def show_variables(self, interaction: discord.Interaction) -> None:
        await self._render(interaction, mode="variables")

    async def edit_content(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_modal(
            LogTemplateContentModal(
                self.guild_id,
                self.category,
                self.event_key,
                self.owner_id,
                self.return_to,
            )
        )

    async def edit_design(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_modal(
            LogTemplateVisualModal(
                self.guild_id,
                self.category,
                self.event_key,
                self.owner_id,
                self.return_to,
            )
        )

    async def reset_event(self, interaction: discord.Interaction) -> None:
        log_template_reset(self.guild_id, self.category, self.event_key)
        await interaction.response.edit_message(
            content=(
                "✅ Este evento volvió a su plantilla heredada/predeterminada.\n\n"
                + log_template_editor_content(
                    self.category, self.event_key, mode="edit"
                )
            ),
            embed=log_template_preview(
                interaction.guild, self.category, self.event_key
            ),
            view=LogTemplateEditorView(
                self.guild_id,
                self.owner_id,
                self.category,
                self.event_key,
                self.return_to,
                mode="edit",
            ),
        )

    async def back(self, interaction: discord.Interaction) -> None:
        if self.return_to == "messages_command":
            await interaction.response.edit_message(
                content=heraldo_messages_command_content(),
                embed=None,
                view=HeraldoMessagesView(self.guild_id, self.owner_id),
            )
            return
        await interaction.response.edit_message(
            content=heraldo_messages_setup_content(),
            embed=None,
            view=HeraldoMessagesSetupView(self.guild_id, self.owner_id),
        )


def heraldo_messages_command_content() -> str:
    return (
        "📝 **El Heraldo · Centro de mensajes**\n\n"
        "Desde aquí puedes editar los paneles persistentes que sí admiten personalización. "
        "Los cambios siguen separados por servidor y, cuando existe un panel ya publicado, "
        "se actualiza sin crear duplicados.\n\n"
        "**No aparecen aquí** paneles que solo muestran información real del bot o del servidor, "
        "como Variables, comandos, diagnósticos, estados y listados."
    )


def heraldo_messages_setup_content() -> str:
    return (
        "✉️ **El Heraldo · Mensajes y paneles**\n\n"
        "Edita los mensajes persistentes y plantillas visuales del servidor desde un solo lugar. "
        "Los cambios quedan aislados por servidor y los paneles publicados se sincronizan cuando corresponde.\n\n"
        "**Editables:** Verificación, DM de verificación, Sugerencias, Honeypot, Condenas y Logs.\n"
        "**Excluidos a propósito:** Variables, comandos, listas, estados, perfiles, historiales, "
        "rankings y cualquier panel cuyo contenido represente datos reales o generados en tiempo real."
    )


class HeraldoMessagesSetupView(discord.ui.View):
    def __init__(self, guild_id: int, owner_id: int) -> None:
        super().__init__(timeout=900)
        self.guild_id = guild_id
        self.owner_id = owner_id

        panel_select = discord.ui.Select(
            placeholder="Selecciona el panel o mensaje que quieres editar",
            min_values=1,
            max_values=1,
            options=[
                discord.SelectOption(
                    label="Verificación",
                    value="verification",
                    emoji="✅",
                    description="Texto del panel, botón y mensaje de éxito.",
                ),
                discord.SelectOption(
                    label="DM de verificación",
                    value="verify_dm",
                    emoji="📩",
                    description="Embed enviado al miembro después de verificarse.",
                ),
                discord.SelectOption(
                    label="Sugerencias",
                    value="suggestions",
                    emoji="💡",
                    description="Título, descripción, color, imágenes y botón.",
                ),
                discord.SelectOption(
                    label="Honeypot",
                    value="honeypot",
                    emoji="🍯",
                    description="Aviso persistente de los canales trampa.",
                ),
                discord.SelectOption(
                    label="Condenas",
                    value="condemnation",
                    emoji="☠️",
                    description="Plantilla de la tarjeta de condenados.",
                ),
                discord.SelectOption(
                    label="Logs",
                    value="logs",
                    emoji="📜",
                    description="Plantillas visuales de los registros del Heraldo.",
                ),
            ],
            row=0,
        )
        panel_select.callback = self.open_editor
        self.panel_select = panel_select
        self.add_item(panel_select)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message(
                "Este panel de configuración no es tuyo.",
                ephemeral=True,
            )
            return False
        return True

    async def open_editor(self, interaction: discord.Interaction) -> None:
        values = interaction.data.get("values") if interaction.data else []
        selected = values[0] if values else ""

        if selected == "verification":
            await open_default_message_studio(
                interaction, "verification", self.owner_id, "messages_setup"
            )
            return

        if selected == "verify_dm":
            await open_default_message_studio(
                interaction, "verify_dm", self.owner_id, "messages_setup"
            )
            return

        if selected == "suggestions":
            await open_default_message_studio(
                interaction, "suggestions", self.owner_id, "messages_setup"
            )
            return

        if selected == "honeypot":
            await open_default_message_studio(
                interaction, "honeypot", self.owner_id, "messages_setup"
            )
            return

        if selected == "condemnation":
            await open_default_message_studio(
                interaction, "condemnation", self.owner_id, "messages_setup"
            )
            return

        if selected == "logs":
            await interaction.response.edit_message(
                content=log_template_editor_content("general"),
                embed=log_template_preview(interaction.guild, "general"),
                view=LogTemplateEditorView(self.guild_id, self.owner_id, "general", None, "messages_setup"),
            )
            return

        await interaction.response.send_message(
            "❌ No pude abrir ese editor.",
            ephemeral=True,
        )

    @discord.ui.button(label="Volver a /setup", style=discord.ButtonStyle.secondary, row=1)
    async def back(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await heraldo_setup_go_home(interaction, self.guild_id, self.owner_id)


def validate_setup_view_layouts(guild_id: int) -> list[str]:
    """Construye las vistas de /setup para detectar errores de layout al arrancar."""
    factories = [
        ("HeraldoSetupView", lambda: HeraldoSetupView(guild_id, 0)),
        ("HeraldoChannelSetupView", lambda: HeraldoChannelSetupView(guild_id, 0)),
        ("HeraldoRoleSetupView", lambda: HeraldoRoleSetupView(guild_id, 0)),
        ("HeraldoOrientationSetupView", lambda: HeraldoOrientationSetupView(guild_id, 0)),
        ("HeraldoMotwSetupView", lambda: HeraldoMotwSetupView(guild_id, 0)),
        ("HeraldoHoneypotSetupView", lambda: HeraldoHoneypotSetupView(guild_id, 0)),
        ("HeraldoVerificationSetupView", lambda: HeraldoVerificationSetupView(guild_id, 0)),
        ("HeraldoRaidSetupView", lambda: HeraldoRaidSetupView(guild_id, 0)),
        ("HeraldoMessagesSetupView", lambda: HeraldoMessagesSetupView(guild_id, 0)),
        ("HeraldoJoinRolesSetupView", lambda: HeraldoJoinRolesSetupView(guild_id, 0)),
        ("HeraldoJoinRolesBasicView", lambda: HeraldoJoinRolesBasicView(guild_id, 0)),
        ("HeraldoJoinRolesUsersView", lambda: HeraldoJoinRolesUsersView(guild_id, 0)),
        ("HeraldoJoinRolesBotsView", lambda: HeraldoJoinRolesBotsView(guild_id, 0)),
        ("HeraldoJoinRolesSyncView", lambda: HeraldoJoinRolesSyncView(guild_id, 0)),
        ("DefaultMessageStudioView:verification:preview", lambda: DefaultMessageStudioView(guild_id, 0, "verification", "preview", "messages_setup")),
        ("DefaultMessageStudioView:verification:edit", lambda: DefaultMessageStudioView(guild_id, 0, "verification", "edit", "messages_setup")),
        ("DefaultMessageStudioView:verify_dm:edit", lambda: DefaultMessageStudioView(guild_id, 0, "verify_dm", "edit", "messages_setup")),
        ("DefaultMessageStudioView:suggestions:edit", lambda: DefaultMessageStudioView(guild_id, 0, "suggestions", "edit", "messages_setup")),
        ("DefaultMessageStudioView:honeypot:edit", lambda: DefaultMessageStudioView(guild_id, 0, "honeypot", "edit", "messages_setup")),
        ("DefaultMessageStudioView:condemnation:edit", lambda: DefaultMessageStudioView(guild_id, 0, "condemnation", "edit", "messages_setup")),
        ("LogTemplateEditorView:preview", lambda: LogTemplateEditorView(guild_id, 0, "general", None, "messages_setup", "preview")),
        ("LogTemplateEditorView:edit", lambda: LogTemplateEditorView(guild_id, 0, "general", None, "messages_setup", "edit")),
        ("LogTemplateEditorView:variables", lambda: LogTemplateEditorView(guild_id, 0, "general", None, "messages_setup", "variables")),
    ]
    errors: list[str] = []
    for name, factory in factories:
        try:
            view = factory()
            if len(view.children) > 25:
                errors.append(f"{name}: {len(view.children)} componentes; Discord permite 25.")
            view.stop()
        except Exception as exc:
            errors.append(f"{name}: {type(exc).__name__}: {exc}")
    return errors



class ModerationReactionEditModal(discord.ui.Modal, title="Moderation · Editar reporte"):
    emoji = discord.ui.TextInput(label="Emoji", required=True, max_length=100, placeholder="📢")
    label = discord.ui.TextInput(label="Nombre del reporte", required=True, max_length=100, placeholder="Spam")

    def __init__(self, parent_view: "HeraldoUserReportsSetupView", index: int | None = None) -> None:
        super().__init__()
        self.parent_view = parent_view
        self.index = index
        if index is not None:
            item = parent_view._working_reactions()[index]
            self.emoji.default = str(item["emoji"])
            self.label.default = str(item["label"])

    async def on_submit(self, interaction: discord.Interaction) -> None:
        emoji = str(self.emoji).strip()
        label = str(self.label).strip()
        key = _moderation_emoji_key(emoji)
        condemn_key = _moderation_emoji_key(self.parent_view.pending_condemn_emoji or get_condemnation_emoji(self.parent_view.guild_id))
        if key == condemn_key:
            await interaction.response.send_message("Ese emoji está reservado para la condena directa.", ephemeral=True)
            return
        reactions = [dict(item) for item in self.parent_view._working_reactions()]
        for idx, item in enumerate(reactions):
            if idx != self.index and _moderation_emoji_key(str(item["emoji"])) == key:
                await interaction.response.send_message("Ese emoji ya está usado por otro reporte.", ephemeral=True)
                return
        if self.index is None:
            if len(reactions) >= MODERATION_REPORT_MAX_REACTIONS:
                await interaction.response.send_message(f"Ya alcanzaste el máximo de {MODERATION_REPORT_MAX_REACTIONS} reacciones.", ephemeral=True)
                return
            reactions.append({
                "emoji": emoji, "label": label, "action": "report",
                "duration_minutes": None, "threshold": 1, "purge_minutes": None,
            })
            self.parent_view.selected_reaction_index = len(reactions) - 1
        else:
            reactions[self.index]["emoji"] = emoji
            reactions[self.index]["label"] = label
            self.parent_view.selected_reaction_index = self.index
        self.parent_view.pending_reactions = reactions
        self.parent_view._rebuild_reaction_select()
        await interaction.response.edit_message(content=self.parent_view._content(interaction.guild), view=self.parent_view)


class ModerationReactionRuleModal(discord.ui.Modal, title="Moderation · Regla del reporte"):
    action = discord.ui.TextInput(label="Acción", required=True, max_length=20, placeholder="report, timeout, kick, ban o condemn")
    duration = discord.ui.TextInput(label="Duración", required=False, max_length=30, placeholder="30m, 1d o -")
    threshold = discord.ui.TextInput(label="Umbral", required=True, max_length=2, placeholder="2")
    purge = discord.ui.TextInput(label="Ventana de purga", required=False, max_length=30, placeholder="30m o -")

    def __init__(self, parent_view: "HeraldoUserReportsSetupView", index: int) -> None:
        super().__init__()
        self.parent_view = parent_view
        self.index = index
        item = parent_view._working_reactions()[index]
        self.action.default = str(item.get("action", "report"))
        duration = item.get("duration_minutes")
        self.duration.default = format_duration(int(duration)) if duration else "-"
        self.threshold.default = str(item.get("threshold", 1))
        purge = item.get("purge_minutes")
        self.purge.default = format_duration(int(purge)) if purge else "-"

    async def on_submit(self, interaction: discord.Interaction) -> None:
        action = str(self.action).strip().lower()
        if action not in MODERATION_REPORT_ACTIONS:
            await interaction.response.send_message("Acciones válidas: report, timeout, kick, ban o condemn.", ephemeral=True)
            return
        try:
            threshold = int(str(self.threshold).strip())
            if not 1 <= threshold <= 25:
                raise ValueError
        except ValueError:
            await interaction.response.send_message("Los reportes necesarios deben estar entre 1 y 25.", ephemeral=True)
            return
        duration_raw = str(self.duration).strip().lower()
        duration_minutes = None
        if duration_raw not in {"", "-", "0", "none", "indefinida"}:
            try:
                duration_minutes = parse_duration(duration_raw, 1, 28 * 24 * 60)
            except ValueError as exc:
                await interaction.response.send_message(f"Duración inválida: {exc}", ephemeral=True)
                return
        if action == "timeout" and duration_minutes is None:
            await interaction.response.send_message("Timeout necesita una duración.", ephemeral=True)
            return
        purge_raw = str(self.purge).strip().lower()
        purge_minutes = None
        if purge_raw not in {"", "-", "0", "none", "no"}:
            try:
                kind, value = parse_purge_spec(purge_raw)
                if kind != "time":
                    raise ValueError("Usa una ventana de tiempo, por ejemplo 30m o 2h.")
                purge_minutes = value
            except ValueError as exc:
                await interaction.response.send_message(f"Purga inválida: {exc}", ephemeral=True)
                return
        reactions = [dict(item) for item in self.parent_view._working_reactions()]
        reactions[self.index].update(
            action=action, duration_minutes=duration_minutes, threshold=threshold, purge_minutes=purge_minutes
        )
        self.parent_view.pending_reactions = reactions
        self.parent_view.selected_reaction_index = self.index
        self.parent_view._rebuild_reaction_select()
        await interaction.response.edit_message(content=self.parent_view._content(interaction.guild), view=self.parent_view)

class ModerationCondemnEmojiModal(discord.ui.Modal, title="Moderation · Emoji de condena"):
    emoji = discord.ui.TextInput(label="Emoji de condena", required=True, max_length=100, placeholder="☠️")

    def __init__(self, parent_view: "HeraldoUserReportsSetupView") -> None:
        super().__init__()
        self.parent_view = parent_view
        self.emoji.default = parent_view.pending_condemn_emoji or get_condemnation_emoji(parent_view.guild_id)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        emoji = str(self.emoji).strip()
        if not emoji:
            await interaction.response.send_message("El emoji no puede estar vacío.", ephemeral=True)
            return
        report_mappings = self.parent_view.pending_reactions
        if report_mappings is None:
            report_mappings = moderation_report_reactions(self.parent_view.guild_id)
        if any(_moderation_emoji_key(item["emoji"]) == _moderation_emoji_key(emoji) for item in report_mappings):
            await interaction.response.send_message("Ese emoji ya está configurado para un reporte normal.", ephemeral=True)
            return
        self.parent_view.pending_condemn_emoji = emoji
        await interaction.response.edit_message(content=self.parent_view._content(interaction.guild), view=self.parent_view)


class HeraldoUserReportsSetupView(discord.ui.View):
    def __init__(self, guild_id: int, owner_id: int) -> None:
        super().__init__(timeout=900)
        self.guild_id = guild_id
        self.owner_id = owner_id
        self.pending_channel_id: int | None = None
        self.pending_reactions: list[dict[str, object]] | None = None
        self.pending_condemn_emoji: str | None = None
        self.selected_reaction_index: int | None = None

        channel_select = discord.ui.ChannelSelect(
            placeholder="Seleccionar canal de reportes",
            channel_types=[discord.ChannelType.text], min_values=1, max_values=1, row=0,
        )
        channel_select.callback = self.select_channel
        self.add_item(channel_select)
        self.reaction_select: discord.ui.Select | None = None
        self._rebuild_reaction_select()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("Este panel de configuración no es tuyo.", ephemeral=True)
            return False
        return True

    def _working_reactions(self) -> list[dict[str, object]]:
        return self.pending_reactions if self.pending_reactions is not None else moderation_report_reactions(self.guild_id)

    def _rebuild_reaction_select(self) -> None:
        if self.reaction_select is not None:
            self.remove_item(self.reaction_select)
        reactions = self._working_reactions()
        if reactions:
            options = []
            for index, item in enumerate(reactions):
                action = moderation_action_label(str(item.get("action", "report")))
                options.append(discord.SelectOption(
                    label=str(item["label"])[:100],
                    value=str(index),
                    emoji=str(item["emoji"]),
                    description=f"{action} · {item.get('threshold', 1)} reporte(s)"[:100],
                    default=index == self.selected_reaction_index,
                ))
            select = discord.ui.Select(placeholder=f"Reacciones configuradas · {len(reactions)}/{MODERATION_REPORT_MAX_REACTIONS}", options=options, row=1)
            select.callback = self.select_reaction
        else:
            select = discord.ui.Select(
                placeholder=f"Sin reacciones · 0/{MODERATION_REPORT_MAX_REACTIONS}",
                options=[discord.SelectOption(label="Sin reacciones configuradas", value="-1")],
                disabled=True, row=1,
            )
        self.reaction_select = select
        self.add_item(select)

    def _content(self, guild: discord.Guild) -> str:
        lines: list[str] = []
        if self.pending_channel_id is not None:
            channel = guild.get_channel(self.pending_channel_id)
            lines.append(f"Canal de reportes → {channel.mention if channel else self.pending_channel_id}")
        if self.pending_reactions is not None:
            lines.append(f"Reacciones → {len(self.pending_reactions)}/{MODERATION_REPORT_MAX_REACTIONS}")
        if self.pending_condemn_emoji is not None:
            lines.append(f"Emoji de condena → {self.pending_condemn_emoji}")
        selected = ""
        if self.selected_reaction_index is not None:
            reactions = self._working_reactions()
            if 0 <= self.selected_reaction_index < len(reactions):
                item = reactions[self.selected_reaction_index]
                duration = item.get("duration_minutes")
                purge = item.get("purge_minutes")
                selected = (
                    f"\n\n**Seleccionado:** {item['emoji']} **{item['label']}**"
                    f"\nAcción: {moderation_action_label(str(item.get('action', 'report')))}"
                    f" · Umbral: {item.get('threshold', 1)}"
                    f" · Duración: {format_duration(int(duration)) if duration else '—'}"
                    f" · Ventana de purga: {format_duration(int(purge)) if purge else '—'}"
                )
        return "**El Heraldo · Moderation · Reportes**\n\n" + moderation_reports_summary(guild) + selected + _pending_config_text(lines)

    async def select_channel(self, interaction: discord.Interaction) -> None:
        values = interaction.data.get("values") if interaction.data else []
        channel = interaction.guild.get_channel(int(values[0])) if interaction.guild and values else None
        if not isinstance(channel, discord.TextChannel):
            await interaction.response.send_message("No pude localizar ese canal.", ephemeral=True)
            return
        perms = channel.permissions_for(interaction.guild.me)
        if not perms.view_channel or not perms.send_messages or not perms.embed_links:
            await interaction.response.send_message("El Heraldo necesita Ver canal, Enviar mensajes e Insertar enlaces en ese canal.", ephemeral=True)
            return
        self.pending_channel_id = channel.id
        await interaction.response.edit_message(content=self._content(interaction.guild), view=self)

    async def select_reaction(self, interaction: discord.Interaction) -> None:
        values = interaction.data.get("values") if interaction.data else []
        if not values:
            return
        index = int(values[0])
        if index < 0 or index >= len(self._working_reactions()):
            await interaction.response.send_message("Esa reacción ya no está disponible.", ephemeral=True)
            return
        self.selected_reaction_index = index
        self._rebuild_reaction_select()
        await interaction.response.edit_message(content=self._content(interaction.guild), view=self)

    @discord.ui.button(label="Añadir", style=discord.ButtonStyle.primary, row=2)
    async def add_reaction(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if len(self._working_reactions()) >= MODERATION_REPORT_MAX_REACTIONS:
            await interaction.response.send_message("Ya alcanzaste el máximo de reacciones.", ephemeral=True)
            return
        await interaction.response.send_modal(ModerationReactionEditModal(self))

    @discord.ui.button(label="Editar", style=discord.ButtonStyle.secondary, row=2)
    async def edit_reaction(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if self.selected_reaction_index is None:
            await interaction.response.send_message("Selecciona primero una reacción.", ephemeral=True)
            return
        await interaction.response.send_modal(ModerationReactionEditModal(self, self.selected_reaction_index))

    @discord.ui.button(label="Regla", style=discord.ButtonStyle.secondary, row=2)
    async def edit_rule(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if self.selected_reaction_index is None:
            await interaction.response.send_message("Selecciona primero una reacción.", ephemeral=True)
            return
        await interaction.response.send_modal(ModerationReactionRuleModal(self, self.selected_reaction_index))

    @discord.ui.button(label="Eliminar", style=discord.ButtonStyle.danger, row=2)
    async def delete_reaction(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if self.selected_reaction_index is None:
            await interaction.response.send_message("Selecciona primero una reacción.", ephemeral=True)
            return
        reactions = [dict(item) for item in self._working_reactions()]
        reactions.pop(self.selected_reaction_index)
        self.pending_reactions = reactions
        self.selected_reaction_index = None
        self._rebuild_reaction_select()
        await interaction.response.edit_message(content=self._content(interaction.guild), view=self)

    @discord.ui.button(label="Emoji de condena", style=discord.ButtonStyle.secondary, row=2)
    async def edit_condemn_emoji(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await interaction.response.send_modal(ModerationCondemnEmojiModal(self))

    @discord.ui.button(label="Guardar cambios", style=discord.ButtonStyle.success, row=3)
    async def save_changes(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if self.pending_channel_id is None and self.pending_reactions is None and self.pending_condemn_emoji is None:
            await interaction.response.send_message("No hay cambios pendientes.", ephemeral=True)
            return
        if self.pending_reactions is not None:
            condemn_key = _moderation_emoji_key(self.pending_condemn_emoji or get_condemnation_emoji(self.guild_id))
            if any(_moderation_emoji_key(str(item["emoji"])) == condemn_key for item in self.pending_reactions):
                await interaction.response.send_message("El emoji de condena no puede coincidir con una reacción de reporte.", ephemeral=True)
                return
        if self.pending_channel_id is not None:
            set_moderation_report_channel_id(self.guild_id, self.pending_channel_id)
        if self.pending_reactions is not None:
            set_moderation_report_reactions(self.guild_id, self.pending_reactions)
        if self.pending_condemn_emoji is not None:
            guild_config_set(self.guild_id, "condemnation_emoji", self.pending_condemn_emoji)
        self.pending_channel_id = None
        self.pending_reactions = None
        self.pending_condemn_emoji = None
        self._rebuild_reaction_select()
        await interaction.response.edit_message(content=self._content(interaction.guild) + "\n\nCambios guardados.", view=self)

    @discord.ui.button(label="Descartar cambios", style=discord.ButtonStyle.secondary, row=3)
    async def discard_changes(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        self.pending_channel_id = None
        self.pending_reactions = None
        self.pending_condemn_emoji = None
        self.selected_reaction_index = None
        self._rebuild_reaction_select()
        await interaction.response.edit_message(content=self._content(interaction.guild), view=self)

    @discord.ui.button(label="Volver", style=discord.ButtonStyle.secondary, row=4)
    async def back(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await interaction.response.edit_message(
            content="**El Heraldo · Moderation**\n\nConfigura las funciones de moderación disponibles.",
            view=HeraldoModerationSetupView(self.guild_id, self.owner_id),
        )

class HeraldoCasesSetupView(discord.ui.View):
    def __init__(self, guild_id: int, owner_id: int) -> None:
        super().__init__(timeout=900)
        self.guild_id = guild_id
        self.owner_id = owner_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("Este panel de configuración no es tuyo.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Actualizar", style=discord.ButtonStyle.secondary, row=0)
    async def refresh(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await interaction.response.edit_message(content=moderation_cases_summary(interaction.guild), view=self)

    @discord.ui.button(label="Volver", style=discord.ButtonStyle.secondary, row=0)
    async def back(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await interaction.response.edit_message(
            content="**El Heraldo · Moderation**\n\nConfigura las funciones de moderación disponibles.",
            view=HeraldoModerationSetupView(self.guild_id, self.owner_id),
        )

class HeraldoCondemnationSetupView(discord.ui.View):
    def __init__(self, guild_id: int, owner_id: int) -> None:
        super().__init__(timeout=900)
        self.guild_id = guild_id
        self.owner_id = owner_id
        self.pending_channel_id: int | None = None
        self.pending_role_id: int | None = None

        channel_select = discord.ui.ChannelSelect(
            placeholder="Seleccionar canal de condenados",
            channel_types=[discord.ChannelType.text],
            min_values=1,
            max_values=1,
            row=0,
        )
        channel_select.callback = self.select_channel
        self.add_item(channel_select)

        role_select = discord.ui.RoleSelect(
            placeholder="Seleccionar rol Condenado",
            min_values=1,
            max_values=1,
            row=1,
        )
        role_select.callback = self.select_role
        self.add_item(role_select)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("Este panel de configuración no es tuyo.", ephemeral=True)
            return False
        return True

    def _content(self, guild: discord.Guild) -> str:
        channel = guild.get_channel(condemnation_channel_id(guild.id))
        role = guild.get_role(get_condenado_role_id(guild.id))
        items: list[str] = []
        if self.pending_channel_id is not None:
            pending_channel = guild.get_channel(self.pending_channel_id)
            items.append(f"Canal → {pending_channel.mention if pending_channel else self.pending_channel_id}")
        if self.pending_role_id is not None:
            pending_role = guild.get_role(self.pending_role_id)
            items.append(f"Rol → {pending_role.mention if pending_role else self.pending_role_id}")
        return (
            "⚖️ **El Heraldo · Moderation · Condenas**\n\n"
            f"Canal de condenados: {channel.mention if isinstance(channel, discord.TextChannel) else 'no configurado'}\n"
            f"Rol Condenado: {role.mention if role else 'no configurado'}"
            + _pending_config_text(items)
        )

    async def select_channel(self, interaction: discord.Interaction) -> None:
        values = interaction.data.get("values") if interaction.data else []
        channel = interaction.guild.get_channel(int(values[0])) if interaction.guild and values else None
        if not isinstance(channel, discord.TextChannel):
            await interaction.response.send_message("No pude localizar ese canal.", ephemeral=True)
            return
        perms = channel.permissions_for(interaction.guild.me)
        if not perms.view_channel or not perms.send_messages or not perms.embed_links:
            await interaction.response.send_message(
                "El Heraldo necesita Ver canal, Enviar mensajes e Insertar enlaces en ese canal.",
                ephemeral=True,
            )
            return
        self.pending_channel_id = channel.id
        await interaction.response.edit_message(content=self._content(interaction.guild), view=self)

    async def select_role(self, interaction: discord.Interaction) -> None:
        values = interaction.data.get("values") if interaction.data else []
        role = interaction.guild.get_role(int(values[0])) if interaction.guild and values else None
        if role is None:
            await interaction.response.send_message("No pude localizar ese rol.", ephemeral=True)
            return
        if role.is_default() or role.managed or role >= interaction.guild.me.top_role:
            await interaction.response.send_message(
                "Ese rol no puede ser administrado por El Heraldo. Revisa jerarquía o integraciones.",
                ephemeral=True,
            )
            return
        self.pending_role_id = role.id
        await interaction.response.edit_message(content=self._content(interaction.guild), view=self)

    @discord.ui.button(label="Crear canal", style=discord.ButtonStyle.success, row=2)
    async def create_channel(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        guild = interaction.guild
        existing_id = get_guild_channel_id(self.guild_id, "condemned")
        channel = guild.get_channel(existing_id) if existing_id else None
        created_now = False
        if not isinstance(channel, discord.TextChannel):
            channel = next((c for c in guild.text_channels if c.name.casefold() == "condenados"), None)
        if not isinstance(channel, discord.TextChannel):
            me = guild.me
            if me is None or not me.guild_permissions.manage_channels:
                await interaction.response.send_message(
                    "El Heraldo necesita Gestionar canales para crear el canal de condenados.",
                    ephemeral=True,
                )
                return
            await interaction.response.defer(ephemeral=True)
            try:
                channel = await guild.create_text_channel(
                    "Condenados",
                    reason="El Heraldo: crear canal de condenados desde /setup",
                )
                created_now = True
            except discord.HTTPException as exc:
                await interaction.followup.send(f"No pude crear el canal: `{exc}`.", ephemeral=True)
                return
        else:
            await interaction.response.defer(ephemeral=True)

        note = await _setup_apply_system_channel(guild, "condemned", channel, publish_messages=True)
        self.pending_channel_id = None
        action = "Creé" if created_now else "Reutilicé"
        await interaction.edit_original_response(
            content=self._content(guild) + f"\n\n{action} {channel.mention}. {note}",
            view=self,
        )

    @discord.ui.button(label="Crear rol Condenado", style=discord.ButtonStyle.success, row=2)
    async def create_role(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await interaction.response.defer(ephemeral=True)
        role, created_now, error = await _setup_get_or_create_system_role(
            interaction.guild, "condenado", "Condenado", "Condenado"
        )
        if error or role is None:
            await interaction.followup.send(error or "No pude preparar el rol.", ephemeral=True)
            return
        self.pending_role_id = None
        action = "Creé" if created_now else "Reutilicé"
        await interaction.edit_original_response(
            content=self._content(interaction.guild) + f"\n\n{action} {role.mention} como rol Condenado.",
            view=self,
        )

    @discord.ui.button(label="Guardar cambios", style=discord.ButtonStyle.success, row=3)
    async def save(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if self.pending_channel_id is None and self.pending_role_id is None:
            await interaction.response.send_message("No hay cambios pendientes.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)
        if self.pending_channel_id is not None:
            channel = interaction.guild.get_channel(self.pending_channel_id)
            if isinstance(channel, discord.TextChannel):
                await _setup_apply_system_channel(interaction.guild, "condemned", channel, publish_messages=True)
        if self.pending_role_id is not None:
            guild_resource_set(self.guild_id, "role", "condenado", self.pending_role_id)
        self.pending_channel_id = self.pending_role_id = None
        await interaction.edit_original_response(content=self._content(interaction.guild) + "\n\nCambios guardados.", view=self)

    @discord.ui.button(label="Descartar", style=discord.ButtonStyle.secondary, row=3)
    async def discard(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        self.pending_channel_id = self.pending_role_id = None
        await interaction.response.edit_message(content=self._content(interaction.guild), view=self)

    @discord.ui.button(label="Volver", style=discord.ButtonStyle.secondary, row=3)
    async def back(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await interaction.response.edit_message(
            content="**El Heraldo · Moderation**\n\nConfigura las funciones de moderación disponibles.",
            view=HeraldoModerationSetupView(self.guild_id, self.owner_id),
        )


class HeraldoModerationSetupView(discord.ui.View):
    def __init__(self, guild_id: int, owner_id: int) -> None:
        super().__init__(timeout=900)
        self.guild_id = guild_id
        self.owner_id = owner_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("Este panel de configuración no es tuyo.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Condenas", style=discord.ButtonStyle.primary, row=0)
    async def condemnations(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        view = HeraldoCondemnationSetupView(self.guild_id, self.owner_id)
        await interaction.response.edit_message(content=view._content(interaction.guild), view=view)

    @discord.ui.button(label="Cases", style=discord.ButtonStyle.primary, row=0)
    async def cases(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await interaction.response.edit_message(
            content=moderation_cases_summary(interaction.guild),
            view=HeraldoCasesSetupView(self.guild_id, self.owner_id),
        )

    @discord.ui.button(label="Reportes", style=discord.ButtonStyle.primary, row=0)
    async def user_reports(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        view = HeraldoUserReportsSetupView(self.guild_id, self.owner_id)
        await interaction.response.edit_message(content=view._content(interaction.guild), view=view)

    @discord.ui.button(label="Volver a /setup", style=discord.ButtonStyle.secondary, row=1)
    async def back(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await heraldo_setup_go_home(interaction, self.guild_id, self.owner_id)



class HeraldoAutomodSetupView(discord.ui.View):
    def __init__(self, guild_id: int, owner_id: int) -> None:
        super().__init__(timeout=900)
        self.guild_id = guild_id
        self.owner_id = owner_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("Este panel de configuración no es tuyo.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Honeypot", style=discord.ButtonStyle.primary, row=0)
    async def honeypot(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await interaction.response.defer(ephemeral=True)
        await interaction.edit_original_response(
            content="**El Heraldo · AutoMod · Honeypot**\n\n" + hp_config_summary(interaction.guild),
            embed=None,
            view=HeraldoHoneypotSetupView(self.guild_id, self.owner_id),
        )

    @discord.ui.button(label="Raid Protection", style=discord.ButtonStyle.primary, row=0)
    async def raid_protection(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await interaction.response.defer(ephemeral=True)
        await interaction.edit_original_response(
            content="**El Heraldo · AutoMod · Raid Protection**\n\n" + raid_config_summary(interaction.guild),
            embed=None,
            view=HeraldoRaidSetupView(self.guild_id, self.owner_id),
        )

    @discord.ui.button(label="Volver", style=discord.ButtonStyle.secondary, row=1)
    async def back(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await heraldo_setup_go_home(interaction, self.guild_id, self.owner_id)


class HeraldoVerificationHubView(discord.ui.View):
    def __init__(self, guild_id: int, owner_id: int) -> None:
        super().__init__(timeout=900)
        self.guild_id = guild_id
        self.owner_id = owner_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("Este panel de configuración no es tuyo.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Verificación de edad", style=discord.ButtonStyle.primary, row=0)
    async def age_verification(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await interaction.response.defer(ephemeral=True)
        await interaction.edit_original_response(
            content="**El Heraldo · Verification · Verificación de edad**\n\n" + verify_config_summary(interaction.guild),
            embed=None,
            view=HeraldoVerificationSetupView(self.guild_id, self.owner_id),
        )

    @discord.ui.button(label="Verificación de preferencia", style=discord.ButtonStyle.primary, row=0)
    async def preference_verification(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await interaction.response.defer(ephemeral=True)
        await interaction.edit_original_response(
            content="**El Heraldo · Verification · Verificación de preferencia**\n\n" + orientation_setup_summary(interaction.guild),
            embed=None,
            view=HeraldoOrientationSetupView(self.guild_id, self.owner_id),
        )

    @discord.ui.button(label="Tiempos", style=discord.ButtonStyle.secondary, row=1)
    async def times(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await interaction.response.send_modal(HeraldoGeneralConfigModal(self.guild_id))

    @discord.ui.button(label="Volver", style=discord.ButtonStyle.secondary, row=1)
    async def back(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await heraldo_setup_go_home(interaction, self.guild_id, self.owner_id)


class HeraldoLoggingSetupView(discord.ui.View):
    def __init__(self, guild_id: int, owner_id: int) -> None:
        super().__init__(timeout=900)
        self.guild_id = guild_id
        self.owner_id = owner_id
        self.pending_channel_id: int | None = None
        channel_select = discord.ui.ChannelSelect(
            placeholder="Seleccionar canal de Logging",
            channel_types=[discord.ChannelType.text],
            min_values=1,
            max_values=1,
            row=0,
        )
        channel_select.callback = self.select_channel
        self.add_item(channel_select)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("Este panel de configuración no es tuyo.", ephemeral=True)
            return False
        return True

    def _content(self, guild: discord.Guild) -> str:
        current_id = get_log_channel_id(guild.id)
        current = guild.get_channel(current_id) if current_id else None
        pending = ""
        if self.pending_channel_id is not None:
            channel = guild.get_channel(self.pending_channel_id)
            pending = _pending_config_text([f"Canal de Logging → {channel.mention if channel else self.pending_channel_id}"])
        return (
            "**El Heraldo · Logging**\n\n"
            f"Canal actual: {current.mention if isinstance(current, discord.TextChannel) else 'no configurado'}\n"
            "Desde aquí se configura el destino de los registros y sus plantillas visuales."
            + pending
        )

    async def select_channel(self, interaction: discord.Interaction) -> None:
        values = interaction.data.get("values") if interaction.data else []
        channel = interaction.guild.get_channel(int(values[0])) if interaction.guild and values else None
        if not isinstance(channel, discord.TextChannel):
            await interaction.response.send_message("No pude localizar ese canal.", ephemeral=True)
            return
        perms = channel.permissions_for(interaction.guild.me)
        if not perms.view_channel or not perms.send_messages or not perms.embed_links:
            await interaction.response.send_message(
                "El Heraldo necesita Ver canal, Enviar mensajes e Insertar enlaces en ese canal.",
                ephemeral=True,
            )
            return
        self.pending_channel_id = channel.id
        await interaction.response.edit_message(content=self._content(interaction.guild), view=self)

    @discord.ui.button(label="Crear canal", style=discord.ButtonStyle.success, row=1)
    async def create_channel(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        guild = interaction.guild
        existing_id = get_guild_channel_id(self.guild_id, "logs")
        channel = guild.get_channel(existing_id) if existing_id else None
        created_now = False
        if not isinstance(channel, discord.TextChannel):
            channel = next((c for c in guild.text_channels if c.name.casefold() == "el heraldo"), None)
        if not isinstance(channel, discord.TextChannel):
            me = guild.me
            if me is None or not me.guild_permissions.manage_channels:
                await interaction.response.send_message(
                    "El Heraldo necesita Gestionar canales para crear el canal de logs.",
                    ephemeral=True,
                )
                return
            await interaction.response.defer(ephemeral=True)
            try:
                channel = await guild.create_text_channel(
                    "El Heraldo",
                    reason="El Heraldo: crear canal de logs desde /setup",
                )
                created_now = True
            except discord.HTTPException as exc:
                await interaction.followup.send(f"No pude crear el canal: `{exc}`.", ephemeral=True)
                return
        else:
            await interaction.response.defer(ephemeral=True)

        note = await _setup_apply_system_channel(guild, "logs", channel, publish_messages=True)
        self.pending_channel_id = None
        action = "Creé" if created_now else "Reutilicé"
        await interaction.edit_original_response(
            content=self._content(guild) + f"\n\n{action} {channel.mention}. {note}",
            view=self,
        )

    @discord.ui.button(label="Plantillas de logs", style=discord.ButtonStyle.primary, row=1)
    async def templates(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await interaction.response.edit_message(
            content=log_template_editor_content("general"),
            embed=log_template_preview(interaction.guild, "general"),
            view=LogTemplateEditorView(self.guild_id, self.owner_id, "general", None, "setup"),
        )

    @discord.ui.button(label="Guardar cambios", style=discord.ButtonStyle.success, row=2)
    async def save(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if self.pending_channel_id is None:
            await interaction.response.send_message("No hay cambios pendientes.", ephemeral=True)
            return
        channel = interaction.guild.get_channel(self.pending_channel_id)
        if not isinstance(channel, discord.TextChannel):
            await interaction.response.send_message("Ese canal ya no existe.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)
        note = await _setup_apply_system_channel(interaction.guild, "logs", channel, publish_messages=True)
        self.pending_channel_id = None
        await interaction.edit_original_response(content=self._content(interaction.guild) + f"\n\nCambios guardados. {note}", view=self)

    @discord.ui.button(label="Descartar cambios", style=discord.ButtonStyle.secondary, row=2)
    async def discard(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        self.pending_channel_id = None
        await interaction.response.edit_message(content=self._content(interaction.guild), view=self)

    @discord.ui.button(label="Volver", style=discord.ButtonStyle.secondary, row=2)
    async def back(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await heraldo_setup_go_home(interaction, self.guild_id, self.owner_id)


class HeraldoPendingSetupModuleView(discord.ui.View):
    def __init__(self, guild_id: int, owner_id: int, module_name: str) -> None:
        super().__init__(timeout=900)
        self.guild_id = guild_id
        self.owner_id = owner_id
        self.module_name = module_name

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("Este panel de configuración no es tuyo.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Volver", style=discord.ButtonStyle.secondary)
    async def back(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await heraldo_setup_go_home(interaction, self.guild_id, self.owner_id)


class HeraldoSetupView(discord.ui.View):
    def __init__(self, guild_id: int, owner_id: int) -> None:
        super().__init__(timeout=900)
        self.guild_id = guild_id
        self.owner_id = owner_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("Este panel de configuración no es tuyo.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="AutoMod", style=discord.ButtonStyle.primary, row=0)
    async def automod(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await interaction.response.edit_message(
            content="**El Heraldo · AutoMod**\n\nConfigura las protecciones automáticas del servidor.",
            embed=None,
            view=HeraldoAutomodSetupView(self.guild_id, self.owner_id),
        )

    @discord.ui.button(label="Moderation", style=discord.ButtonStyle.primary, row=0)
    async def moderation(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await interaction.response.edit_message(
            content="**El Heraldo · Moderation**\n\nConfigura las funciones de moderación disponibles.",
            embed=None,
            view=HeraldoModerationSetupView(self.guild_id, self.owner_id),
        )

    @discord.ui.button(label="Join Roles", style=discord.ButtonStyle.primary, row=0)
    async def join_roles(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await interaction.response.defer(ephemeral=True)
        await interaction.edit_original_response(
            content="**El Heraldo · Join Roles**\n\n" + join_roles_summary(interaction.guild),
            embed=None,
            view=HeraldoJoinRolesSetupView(self.guild_id, self.owner_id),
        )

    @discord.ui.button(label="Reaction Roles", style=discord.ButtonStyle.primary, row=0)
    async def reaction_roles(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await interaction.response.edit_message(
            content="**El Heraldo · Reaction Roles**\n\nMódulo reservado en la nueva arquitectura. Su alcance sigue pendiente de definición.",
            embed=None,
            view=HeraldoPendingSetupModuleView(self.guild_id, self.owner_id, "Reaction Roles"),
        )

    @discord.ui.button(label="Role Connections", style=discord.ButtonStyle.secondary, row=1)
    async def role_connections(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await interaction.response.edit_message(
            content="**El Heraldo · Role Connections**\n\nMódulo reservado. La configuración se implementará cuando definamos su alcance.",
            embed=None,
            view=HeraldoPendingSetupModuleView(self.guild_id, self.owner_id, "Role Connections"),
        )

    @discord.ui.button(label="Logging", style=discord.ButtonStyle.secondary, row=1)
    async def logging(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        view = HeraldoLoggingSetupView(self.guild_id, self.owner_id)
        await interaction.response.edit_message(content=view._content(interaction.guild), embed=None, view=view)

    @discord.ui.button(label="Verification", style=discord.ButtonStyle.secondary, row=1)
    async def verification(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await interaction.response.edit_message(
            content="**El Heraldo · Verification**\n\nConfigura los sistemas de verificación.",
            embed=None,
            view=HeraldoVerificationHubView(self.guild_id, self.owner_id),
        )

    @discord.ui.button(label="Idioma", style=discord.ButtonStyle.secondary, row=1)
    async def language(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await interaction.response.edit_message(
            content="**El Heraldo · Idioma**\n\nMódulo reservado para la internacionalización del bot.",
            embed=None,
            view=HeraldoPendingSetupModuleView(self.guild_id, self.owner_id, "Idioma"),
        )

    @discord.ui.button(label="Cerrar", style=discord.ButtonStyle.danger, row=2)
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        self.stop()
        await interaction.response.defer(ephemeral=True)
        await interaction.edit_original_response(content="Panel de configuración cerrado.", view=None)


@bot.tree.command(name="setup", description="Configura las opciones generales de El Heraldo en este servidor.")
@app_commands.default_permissions(administrator=True)
@app_commands.guild_only()
async def setup(interaction: discord.Interaction) -> None:
    guild = interaction.guild
    if guild is None:
        await interaction.response.send_message("Este comando solo puede usarse dentro de un servidor.", ephemeral=True)
        return

    await interaction.response.send_message(
        heraldo_setup_home_content(),
        view=HeraldoSetupView(guild.id, interaction.user.id),
        ephemeral=True,
    )


async def heraldo_config(interaction: discord.Interaction) -> None:
    guild = interaction.guild
    if guild is None:
        await interaction.response.send_message("Este comando solo puede usarse dentro de un servidor.", ephemeral=True)
        return

    create_missing = guild_config_get(guild.id, "heraldo_auto_create_resources") == "1"
    estado = "activada" if create_missing else "desactivada"
    await interaction.response.send_message(
        "⚙️ **Configuración general de El Heraldo**\n\n"
        f"Creación automática de recursos: **{estado}**.\n"
        "La configuración de canales, roles, verificación, orientación, tiempos, permisos y demás opciones se realiza mediante `/setup`.",
        ephemeral=True,
    )


@bot.tree.command(name="heraldo_check", description="Fuerza la evaluación inmediata de un miembro (sin esperar el timer de 10 min).")
@discord.app_commands.checks.has_permissions(kick_members=True)
@discord.app_commands.guild_only()
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
@discord.app_commands.guild_only()
async def heraldo_check_all(interaction: discord.Interaction) -> None:
    guild = interaction.guild
    await interaction.response.send_message("Revisando a todos los miembros con Tentad@... esto puede tardar un poco.", ephemeral=True)
    await log_embed(guild, "🔍 Chequeo masivo iniciado", f"Solicitado por {interaction.user.mention}.", discord.Color.blurple())

    verified = 0
    expelled: list[discord.Member] = []
    expelled_sin_verificar: list[discord.Member] = []

    async for member in guild.fetch_members(limit=None):
        if member.bot or condemnation_get(member.guild.id, member.id) is not None:
            continue  # los condenados quedan fuera de toda evaluación
        role_ids = {r.id for r in member.roles}
        if get_tentado_role_id(guild.id) in role_ids:
            status = await evaluate_member(guild.id, member.id, report=False)
            if status == "verificado":
                verified += 1
            elif status == "expulsado":
                expelled.append(member)
            await asyncio.sleep(1)  # evitar ráfagas contra el rate limit de Discord
        elif get_sin_verificado_role_id(guild.id) in role_ids:
            db_clear_sin_verificado(member.guild.id, member.id)
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

    channel = guild.get_channel(get_log_channel_id(guild.id))
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

    set_log_channel_id(canal.id, interaction.guild.id)
    guild_resource_set(interaction.guild.id, "channel", "logs", canal.id)
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
            # Esta vista se registra al arrancar sin conocer un guild concreto.
            # El panel real conserva el texto configurado por su propio servidor.
            label=label or VERIFY_BUTTON_LABEL_DEFAULT,
            style=discord.ButtonStyle.success,
            custom_id=VERIFY_BUTTON_ID,
        )
        button.callback = handle_verify_click
        self.add_item(button)


async def send_verification_welcome_dm(member: discord.Member) -> bool:
    """Envía el DM de bienvenida una sola vez, cuando el miembro se verifica por primera vez."""
    if db_verification_dm_sent(member.guild.id, member.id):
        return True

    embed = build_verification_welcome_embed(member=member)
    try:
        await member.send(embed=embed)
        db_mark_verification_dm_sent(member.guild.id, member.id)
        return True
    except discord.HTTPException:
        return False


async def clear_sin_verificar_after_verification(
    member: discord.Member,
    *,
    reason: str,
) -> bool:
    """Retira Sin Verificar y cancela sus estados pendientes tras verificarse."""
    guild = member.guild
    db_clear_verify_pending(guild.id, member.id)
    db_clear_sin_verificado(guild.id, member.id)

    sin_role = guild.get_role(get_sin_verificado_role_id(guild.id))
    if sin_role is None or sin_role not in member.roles:
        return True
    try:
        await member.remove_roles(sin_role, reason=reason)
        return True
    except discord.HTTPException as exc:
        await log_embed(
            guild,
            "⚠️ No pude quitar Sin Verificar",
            f"{member.mention} ya está verificado, pero no pude quitarle "
            f"{sin_role.mention}: {exc}. Revisa jerarquía y permisos.",
            discord.Color.dark_red(),
        )
        return False


async def handle_verify_click(interaction: discord.Interaction) -> None:
    guild = interaction.guild
    member = interaction.user
    if guild is None or not isinstance(member, discord.Member):
        await interaction.response.send_message("Esto solo funciona dentro del servidor.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True, thinking=True)

    punish_role_id = hp_punish_role_id(guild.id)
    if condemnation_get(member.guild.id, member.id) is not None or (punish_role_id and any(r.id == punish_role_id for r in member.roles)):
        await interaction.followup.send("☠️ Estás condenado: no puedes verificarte mientras la condena esté activa.", ephemeral=True)
        return

    role = guild.get_role(get_verify_role_id(guild.id))
    if role is None:
        await interaction.followup.send("⚠️ La verificación no está configurada todavía. Avisa a un administrador.", ephemeral=True)
        await log_embed(
            guild, "⚠️ Verificación sin configurar",
            f"{member.mention} pulsó el botón pero el rol de verificación no existe.",
            discord.Color.dark_red(),
        )
        return

    role_ids = {r.id for r in member.roles}
    if role.id in role_ids:
        await clear_sin_verificar_after_verification(
            member,
            reason="Limpieza automática: el miembro ya posee el rol de verificación",
        )
        await interaction.followup.send("✅ ¡Ya estás verificado!", ephemeral=True)
        return
    if role_ids & get_eval_role_ids(guild.id):
        await interaction.followup.send("✅ Ya completaste la selección de orientación.", ephemeral=True)
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

    db_clear_verify_pending(member.guild.id, member.id)
    # Quien se verifica deja de estar "Sin Verificar" (si no, el respaldo de 300 s lo expulsaría).
    sin_role = guild.get_role(get_sin_verificado_role_id(guild.id))
    if sin_role is not None and sin_role in member.roles:
        try:
            await member.remove_roles(sin_role, reason="Verificación de edad (botón de El Heraldo)")
            db_clear_sin_verificado(member.guild.id, member.id)
        except discord.HTTPException as e:
            await log_embed(
                guild, "⚠️ No pude quitar Sin Verificar",
                f"{member.mention} se verificó pero no pude quitarle {sin_role.mention}: `{e}`.",
                discord.Color.dark_red(),
            )

    await interaction.followup.send(
        render_vars(get_verify_success_text(guild.id), VarContext(guild, member, interaction.channel), 2000),
        ephemeral=True, allowed_mentions=discord.AllowedMentions.none(),
    )

    # Orientación por preferencias: solo se inicia desde ESTE evento de verificación.
    # Nunca se arma al detectar roles en miembros antiguos. Si el servidor no configuró
    # roles de orientación, no existe obligación ni expulsión por preferencias.
    orientation_roles = get_eval_role_ids(guild.id)
    if orientation_roles and not ({r.id for r in member.roles} & orientation_roles):
        now = datetime.now(timezone.utc)
        db_set_tentado(member.guild.id, member.id, now)
        asyncio.create_task(schedule_check(guild.id, member.id, now))
        # Log de "Orientación iniciada" desactivado temporalmente.
        # La orientación y su temporizador siguen funcionando con normalidad.
    else:
        db_clear_tentado(member.guild.id, member.id)

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
        f"{member.mention} (`{member.id}`) se verificó correctamente.",
        discord.Color.green(),
    )


async def schedule_verify_timeout(guild_id: int, user_id: int, pending_at: datetime) -> None:
    delay = (pending_at + timedelta(seconds=get_verify_timeout(guild_id)) - datetime.now(timezone.utc)).total_seconds()
    if delay > 0:
        await asyncio.sleep(delay)
    await evaluate_verify_timeout(guild_id, user_id)


async def evaluate_verify_timeout(guild_id: int, user_id: int) -> None:
    """Aplica la acción configurada si el miembro no se verificó dentro del timeout.
    Lee siempre la configuración actual: si el timeout se alargó mientras esperaba, no
    actúa todavía (check_pending_verifications lo retoma al vencer el nuevo plazo)."""
    if condemnation_get(guild_id, user_id) is not None:
        db_clear_verify_pending(guild_id, user_id)
        return
    row = db_get(guild_id, user_id)
    if row is None or row["verify_pending_at"] is None:
        return  # ya verificado, ya evaluado o nunca estuvo pendiente
    guild = bot.get_guild(guild_id)
    if guild is None:
        return
    member = guild.get_member(user_id)
    if member is None or not verify_enabled(guild.id):
        db_clear_verify_pending(guild_id, user_id)  # se fue, o la verificación se desactivó
        return

    timeout = get_verify_timeout(guild_id)
    deadline = datetime.fromisoformat(row["verify_pending_at"]) + timedelta(seconds=timeout)
    if datetime.now(timezone.utc) + timedelta(seconds=1) < deadline:
        return

    role_ids = {r.id for r in member.roles}
    db_clear_verify_pending(guild_id, user_id)
    if get_verify_role_id(guild.id) in role_ids or role_ids & get_eval_role_ids(guild.id):
        return  # se verificó a tiempo (o un admin le dio un rol de orientación)

    action = get_verify_action(guild.id)
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
    ref = guild_config_get(guild.id, "verify_panel_ref")
    if ref is None and legacy_fallback_allowed(guild.id):
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
            content=render_vars(get_verify_panel_text(guild.id), VarContext(guild, None, channel), 2000),
            view=VerifyView(label=get_verify_button_label(guild.id)),
            allowed_mentions=discord.AllowedMentions.none(),
        )
        return "El panel publicado ya muestra los textos nuevos."
    except discord.NotFound:
        return "⚠️ El panel ya no existe (¿lo borraron?); publícalo de nuevo con /verify."
    except (discord.HTTPException, ValueError) as e:
        return f"⚠️ No pude actualizar el panel publicado: `{e}`. Publícalo de nuevo con /verify."


def verify_config_summary(guild: discord.Guild) -> str:
    role_id = get_verify_role_id(guild.id)
    role = guild.get_role(role_id)
    role_text = role.mention if role else f"⚠️ no encontrado (`{role_id}`)"
    ref = guild_config_get(guild.id, "verify_panel_ref")
    if ref is None and legacy_fallback_allowed(guild.id):
        ref = db_meta_get("verify_panel_ref")
    if ref and ref.count(":") == 1:
        channel_id, message_id = ref.split(":")
        panel_text = f"[ir al panel](https://discord.com/channels/{guild.id}/{channel_id}/{message_id})"
    elif ref:
        panel_text = "⚠️ referencia dañada: publícalo de nuevo con /verify"
    else:
        panel_text = "sin publicar (usa /verify)"
    return (
        f"**Verificación:** {'✅ activada' if verify_enabled(guild.id) else '⏸️ desactivada'}\n"
        f"**Rol de verificación:** {role_text}\n"
        f"**Timeout:** {format_duration((get_verify_timeout(guild.id) + 59) // 60)}\n"
        f"**Acción al agotarse:** {VERIFY_ACTION_LABELS[get_verify_action(guild.id)]}\n"
        f"**Panel:** {panel_text}"
    )


class VerifyTextsModal(discord.ui.Modal):
    """Formulario de textos; se abre con los valores actuales."""

    def __init__(self, guild_id: int) -> None:
        super().__init__(title="Textos de la verificación")
        self.guild_id = guild_id
        self.panel = discord.ui.TextInput(
            label="Mensaje del panel (sobre el botón)",
            style=discord.TextStyle.paragraph,
            default=get_verify_panel_text(guild_id),
            max_length=2000,
        )
        self.button_label = discord.ui.TextInput(
            label="Texto del botón",
            default=get_verify_button_label(guild_id),
            max_length=80,
        )
        self.success = discord.ui.TextInput(
            label="Mensaje tras pulsar el botón",
            style=discord.TextStyle.paragraph,
            default=get_verify_success_text(guild_id),
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
        guild_config_set(interaction.guild.id, "verify_panel_text", panel)
        guild_config_set(interaction.guild.id, "verify_button_label", label)
        guild_config_set(interaction.guild.id, "verify_success_text", success)
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
    role = guild.get_role(get_verify_role_id(guild.id))
    if role is None:
        await interaction.response.send_message("❌ El rol de verificación no existe. Elige uno con `/verify_setup`.", ephemeral=True)
        return
    problem = verify_role_problem(role, guild)
    if problem:
        await interaction.response.send_message(
            f"❌ No publiqué el panel: el rol {role.mention} {problem}. Elige otro con `/verify_setup`.",
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
            content=render_vars(get_verify_panel_text(guild.id), VarContext(guild, None, target), 2000),
            view=VerifyView(label=get_verify_button_label(guild.id)),
            allowed_mentions=discord.AllowedMentions.none(),
        )
    except discord.HTTPException as e:
        await interaction.followup.send(f"❌ No pude publicar el panel: `{e}`", ephemeral=True)
        return
    guild_config_set(guild.id, "verify_panel_ref", f"{target.id}:{message.id}")
    await interaction.followup.send(
        f"✅ Panel publicado en {target.mention}. Cuando quieras que el timeout empiece a aplicarse, "
        f"usa `/verify_setup activado:True`.",
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
        guild_config_set(interaction.guild.id, key, value)

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
    log_channel = guild.get_channel(get_log_channel_id(guild.id))
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
    await interaction.response.send_modal(VerifyTextsModal(interaction.guild.id))


@bot.tree.command(name="verify_setup", description="Ver o cambiar la configuración de la verificación por botón.")
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
        effective_role = rol or guild.get_role(get_verify_role_id(guild.id))
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
        panel_ref = guild_config_get(guild.id, "verify_panel_ref")
        if panel_ref is None and legacy_fallback_allowed(guild.id):
            panel_ref = db_meta_get("verify_panel_ref")
        if not panel_ref:
            await interaction.response.send_message(
                "❌ No activé la verificación: aún no hay panel publicado. Usa `/verify` primero; "
                "si no, nadie podría verificarse y todos los que entren serían sancionados.",
                ephemeral=True,
            )
            return

    # 2) Guardar.
    changes: list[str] = []
    if rol is not None:
        guild_config_set(interaction.guild.id, "verify_role_id", str(rol.id))
        changes.append(f"rol → {rol.mention}")
    if timeout_seconds is not None:
        guild_config_set(interaction.guild.id, "verify_timeout", str(timeout_seconds))
        changes.append(f"timeout → {format_duration(timeout_seconds // 60)}")
    if accion is not None:
        guild_config_set(interaction.guild.id, "verify_action", accion.value)
        changes.append(f"acción → {accion.name}")
    if activado is not None:
        guild_config_set(interaction.guild.id, "verify_enabled", "1" if activado else "0")
        changes.append("activada" if activado else "desactivada")

    warnings: list[str] = []
    if get_verify_timeout(guild.id) > get_sin_verificado_window(guild.id).total_seconds():
        warnings.append("⚠️ El respaldo de Sin Verificar sigue en 300 s: quien tenga ese rol será expulsado antes que este timeout.")
    if get_verify_role_id(guild.id) != get_tentado_role_id(guild.id):
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


joinroles_group = discord.app_commands.Group(
    name="joinroles",
    description="Gestionar Join Roles al estilo Sapphire.",
    guild_only=True,
    default_permissions=discord.Permissions(manage_guild=True),
)


def _joinroles_command_roles(*roles: discord.Role | None) -> list[discord.Role]:
    result: list[discord.Role] = []
    for role in roles:
        if role is not None and role not in result:
            result.append(role)
    return result


def _joinroles_validate_command_roles(
    guild: discord.Guild,
    roles: list[discord.Role],
) -> str | None:
    issues: list[str] = []
    for role in roles:
        _role, issue = _join_role_status(guild, role.id)
        if issue:
            issues.append(f"{role.mention}: {issue}")
    return "; ".join(issues) if issues else None


@joinroles_group.command(name="status", description="Ver la configuración actual de Join Roles.")
@discord.app_commands.checks.has_permissions(manage_guild=True)
async def joinroles_status(interaction: discord.Interaction) -> None:
    await interaction.response.send_message(
        "🚪 **El Heraldo · Join Roles**\n\n"
        + join_roles_basic_summary(interaction.guild)
        + "\n\n"
        + join_roles_bots_summary(interaction.guild)
        + "\n\n"
        + join_roles_sync_summary(interaction.guild),
        ephemeral=True,
    )


@joinroles_group.command(name="sync", description="Asignar ahora los Join Roles a los miembros elegibles.")
@discord.app_commands.checks.has_permissions(manage_guild=True)
async def joinroles_sync_command(interaction: discord.Interaction) -> None:
    await interaction.response.defer(ephemeral=True, thinking=True)
    assigned, skipped, errors = await sync_join_roles(interaction.guild)
    text = (
        f"✅ Sync terminado. **{assigned}** miembro(s) recibieron Join Roles; "
        f"**{skipped}** no necesitaron cambios."
    )
    if errors:
        text += f"\n⚠️ **{len(errors)}** error(es) por permisos o jerarquía."
    await interaction.followup.send(text, ephemeral=True)


@joinroles_group.command(name="add", description="Añadir uno o varios Join Roles generales.")
@discord.app_commands.checks.has_permissions(manage_guild=True)
async def joinroles_add(
    interaction: discord.Interaction,
    rol: discord.Role,
    rol2: Optional[discord.Role] = None,
    rol3: Optional[discord.Role] = None,
    rol4: Optional[discord.Role] = None,
    rol5: Optional[discord.Role] = None,
) -> None:
    roles = _joinroles_command_roles(rol, rol2, rol3, rol4, rol5)
    issue = _joinroles_validate_command_roles(interaction.guild, roles)
    if issue:
        await interaction.response.send_message(f"❌ {issue}", ephemeral=True)
        return
    current = get_join_role_ids(interaction.guild.id)
    for role in roles:
        if role.id not in current:
            current.append(role.id)
    set_join_role_ids(interaction.guild.id, current[:JOIN_ROLES_MAX])
    guild_config_set(interaction.guild.id, "join_roles_enabled", "1")
    await interaction.response.send_message(
        "✅ Join Roles actualizados:\n" + _join_roles_render(interaction.guild, get_join_role_ids(interaction.guild.id)),
        ephemeral=True,
    )


@joinroles_group.command(name="remove", description="Quitar uno o varios Join Roles generales.")
@discord.app_commands.checks.has_permissions(manage_guild=True)
async def joinroles_remove(
    interaction: discord.Interaction,
    rol: discord.Role,
    rol2: Optional[discord.Role] = None,
    rol3: Optional[discord.Role] = None,
    rol4: Optional[discord.Role] = None,
    rol5: Optional[discord.Role] = None,
) -> None:
    remove_ids = {role.id for role in _joinroles_command_roles(rol, rol2, rol3, rol4, rol5)}
    current = [role_id for role_id in get_join_role_ids(interaction.guild.id) if role_id not in remove_ids]
    set_join_role_ids(interaction.guild.id, current)
    await interaction.response.send_message(
        "✅ Join Roles actualizados:\n" + _join_roles_render(interaction.guild, current),
        ephemeral=True,
    )


@joinroles_group.command(name="user_add", description="Añadir un rol específico a un Discord User ID.")
@discord.app_commands.checks.has_permissions(manage_guild=True)
async def joinroles_user_add(
    interaction: discord.Interaction,
    user_id: str,
    rol: discord.Role,
) -> None:
    try:
        target_id = int(user_id.strip())
        if target_id <= 0:
            raise ValueError
    except ValueError:
        await interaction.response.send_message("❌ Discord User ID inválido.", ephemeral=True)
        return
    issue = _joinroles_validate_command_roles(interaction.guild, [rol])
    if issue:
        await interaction.response.send_message(f"❌ {issue}", ephemeral=True)
        return
    mapping = get_join_specific_roles(interaction.guild.id)
    roles = mapping.get(target_id, [])
    if rol.id not in roles:
        roles.append(rol.id)
    set_join_specific_user_roles(interaction.guild.id, target_id, roles)
    await interaction.response.send_message(
        f"✅ <@{target_id}> recibirá {rol.mention} cuando ingrese.", ephemeral=True
    )


@joinroles_group.command(name="user_remove", description="Quitar un rol específico o eliminar el User ID de la lista.")
@discord.app_commands.checks.has_permissions(manage_guild=True)
async def joinroles_user_remove(
    interaction: discord.Interaction,
    user_id: str,
    rol: Optional[discord.Role] = None,
) -> None:
    try:
        target_id = int(user_id.strip())
        if target_id <= 0:
            raise ValueError
    except ValueError:
        await interaction.response.send_message("❌ Discord User ID inválido.", ephemeral=True)
        return

    mapping = get_join_specific_roles(interaction.guild.id)
    if target_id not in mapping:
        await interaction.response.send_message("ℹ️ Ese User ID no está configurado.", ephemeral=True)
        return
    if rol is None:
        remove_join_specific_user(interaction.guild.id, target_id)
        await interaction.response.send_message("✅ Usuario eliminado de la lista.", ephemeral=True)
        return

    roles = [role_id for role_id in mapping[target_id] if role_id != rol.id]
    set_join_specific_user_roles(interaction.guild.id, target_id, roles)
    await interaction.response.send_message(
        f"✅ {rol.mention} eliminado de los roles específicos de <@{target_id}>.",
        ephemeral=True,
    )


@joinroles_group.error
async def joinroles_group_error(
    interaction: discord.Interaction,
    error: discord.app_commands.AppCommandError,
) -> None:
    await verify_command_error(interaction, error)


bot.tree.add_command(joinroles_group)


# ---------------------------------------------------------------------------
# Copia de seguridad de la plantilla del servidor (/server_template_setup, /template_sync)
# ---------------------------------------------------------------------------

def _meta_int(key: str, default: int) -> int:
    value = db_meta_get(key)
    return int(value) if value is not None else default


def _template_value(guild_id: int, key: str, default: str) -> str:
    value = guild_config_get(guild_id, key)
    if value is not None:
        return value
    if db_meta_get("template_guild_id") == str(guild_id):
        legacy = db_meta_get(key)
        if legacy is not None:
            return legacy
        if key == "template_interval_minutes":
            old = db_meta_get("template_interval_hours")
            if old is not None:
                return str(int(old) * 60)
    return default


def get_template_mode(guild_id: int) -> str:
    value = _template_value(guild_id, "template_mode", "off")
    return value if value in TEMPLATE_MODE_LABELS else "off"


def get_template_hour(guild_id: int) -> int:
    try:
        return int(_template_value(guild_id, "template_hour", str(TEMPLATE_HOUR_DEFAULT)))
    except (TypeError, ValueError):
        return TEMPLATE_HOUR_DEFAULT


def get_template_weekday(guild_id: int) -> int:
    try:
        value = int(_template_value(guild_id, "template_weekday", str(TEMPLATE_WEEKDAY_DEFAULT)))
    except (TypeError, ValueError):
        return TEMPLATE_WEEKDAY_DEFAULT
    return value if 0 <= value <= 6 else TEMPLATE_WEEKDAY_DEFAULT


def get_template_monthday(guild_id: int) -> int:
    try:
        value = int(_template_value(guild_id, "template_monthday", str(TEMPLATE_MONTHDAY_DEFAULT)))
    except (TypeError, ValueError):
        return TEMPLATE_MONTHDAY_DEFAULT
    return max(1, min(28, value))


def get_template_interval_minutes(guild_id: int) -> int:
    try:
        value = int(_template_value(guild_id, "template_interval_minutes", str(TEMPLATE_INTERVAL_DEFAULT * 60)))
    except (TypeError, ValueError):
        return TEMPLATE_INTERVAL_DEFAULT * 60
    return max(1, value)


def template_schedule_text(guild_id: int) -> str:
    mode = get_template_mode(guild_id)
    hour = f"{get_template_hour(guild_id)}:00 (hora de RD)"
    if mode == "off":
        return "Desactivada"
    if mode == "daily":
        return f"Cada día a las {hour}"
    if mode == "weekly":
        return f"Cada semana, {MOTW_WEEKDAY_NAMES[get_template_weekday(guild_id)]} a las {hour}"
    if mode == "monthly":
        return f"Cada mes, el día {get_template_monthday(guild_id)} a las {hour}"
    return f"Cada {format_duration(get_template_interval_minutes(guild_id))}"


def template_last_slot(guild_id: int, mode: str, now: datetime) -> datetime | None:
    hour = get_template_hour(guild_id)
    if mode == "daily":
        slot = now.replace(hour=hour, minute=0, second=0, microsecond=0)
        if slot > now:
            slot -= timedelta(days=1)
        return slot
    if mode == "weekly":
        days_back = (now.weekday() - get_template_weekday(guild_id)) % 7
        slot = (now - timedelta(days=days_back)).replace(hour=hour, minute=0, second=0, microsecond=0)
        if slot > now:
            slot -= timedelta(days=7)
        return slot
    if mode == "monthly":
        day = get_template_monthday(guild_id)
        slot = now.replace(day=day, hour=hour, minute=0, second=0, microsecond=0)
        if slot > now:
            last_of_previous = now.replace(day=1) - timedelta(days=1)
            slot = last_of_previous.replace(day=day, hour=hour, minute=0, second=0, microsecond=0)
        return slot
    return None


def template_next_run(guild_id: int, now_utc: datetime) -> datetime | None:
    mode = get_template_mode(guild_id)
    if mode == "off":
        return None
    if mode == "interval":
        last = guild_config_get(guild_id, "template_last_run")
        if last is None and db_meta_get("template_guild_id") == str(guild_id):
            last = db_meta_get("template_last_run")
        base = datetime.fromisoformat(last) if last else now_utc
        return (base + timedelta(minutes=get_template_interval_minutes(guild_id))).astimezone(STREAK_TZ)
    slot = template_last_slot(guild_id, mode, now_utc.astimezone(STREAK_TZ))
    if mode == "daily":
        return slot + timedelta(days=1)
    if mode == "weekly":
        return slot + timedelta(days=7)
    first_of_next = (slot.replace(day=28) + timedelta(days=4)).replace(day=1)
    return first_of_next.replace(day=get_template_monthday(guild_id))


def template_due(guild_id: int, now_utc: datetime) -> bool:
    mode = get_template_mode(guild_id)
    if mode == "off":
        return False
    if mode == "interval":
        last = guild_config_get(guild_id, "template_last_run")
        if last is None and db_meta_get("template_guild_id") == str(guild_id):
            last = db_meta_get("template_last_run")
        if last is None:
            guild_config_set(guild_id, "template_last_run", now_utc.isoformat())
            return False
        return now_utc >= datetime.fromisoformat(last) + timedelta(minutes=get_template_interval_minutes(guild_id))
    slot = template_last_slot(guild_id, mode, now_utc.astimezone(STREAK_TZ))
    handled = guild_config_get(guild_id, "template_last_slot")
    if handled is None and db_meta_get("template_guild_id") == str(guild_id):
        handled = db_meta_get("template_last_slot")
    if handled is None:
        guild_config_set(guild_id, "template_last_slot", slot.isoformat())
        return False
    return slot > datetime.fromisoformat(handled)


def template_mark_done(guild_id: int, now_utc: datetime) -> None:
    guild_config_set(guild_id, "template_last_run", now_utc.isoformat())
    mode = get_template_mode(guild_id)
    if mode in ("daily", "weekly", "monthly"):
        slot = template_last_slot(guild_id, mode, now_utc.astimezone(STREAK_TZ))
        if slot is not None:
            guild_config_set(guild_id, "template_last_slot", slot.isoformat())


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
        title="Copia de seguridad de la plantilla",
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


async def run_scheduled_template_backup(guild: discord.Guild) -> bool:
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
        # La copia programada siempre pertenece al servidor: el destinatario es
        # el propietario actual del servidor, no el usuario que configuró el comando.
        owner = await bot.fetch_user(guild.owner_id)
        await owner.send(embed=embed)
        sent = True
    except discord.HTTPException:
        pass  # incluye Forbidden (mensajes privados cerrados)
    # El enlace nunca va al canal de logs: ahí solo queda constancia del fallo o del envío fallido.
    if error:
        await log_embed(guild, "⚠️ Falló la copia de seguridad de la plantilla", error, discord.Color.dark_red())
    elif not sent:
        await log_embed(
            guild, "Plantilla sincronizada (mensaje privado no enviado)",
            "La copia se hizo, pero no pude mandarte el enlace por mensaje privado. Usa /template_sync para verlo.",
            discord.Color.orange(),
        )
    return error is None


@tasks.loop(minutes=10)
async def template_backup_loop() -> None:
    """Revisa cada servidor por separado y solo marca el turno tras una copia correcta."""
    now = datetime.now(timezone.utc)
    for guild in bot.guilds:
        try:
            if not template_due(guild.id, now):
                continue
            if await run_scheduled_template_backup(guild):
                template_mark_done(guild.id, now)
        except Exception:
            print(f"❌ Falló la copia programada de plantilla en {guild.name}:")
            traceback.print_exc()


def template_config_summary(guild_id: int, now_utc: datetime) -> str:
    next_run = template_next_run(guild_id, now_utc)
    next_text = (
        f"{discord.utils.format_dt(next_run, 'F')} ({discord.utils.format_dt(next_run, 'R')})"
        if next_run else "—"
    )
    last = guild_config_get(guild_id, "template_last_run")
    if last is None and db_meta_get("template_guild_id") == str(guild_id):
        last = db_meta_get("template_last_run")
    last_text = discord.utils.format_dt(datetime.fromisoformat(last), "f") if last and get_template_mode(guild_id) != "off" else "ninguna todavía"
    return (
        f"**Frecuencia:** {template_schedule_text(guild_id)}\n"
        f"**Próxima copia:** {next_text}\n"
        f"**Última copia programada:** {last_text}\n"
        f"**Enlace por mensaje privado a:** creador/propietario del servidor"
    )


@bot.tree.command(name="server_template_setup", description="Ver o cambiar cuándo se sincroniza la plantilla del servidor (copia de seguridad).")
@discord.app_commands.describe(
    frecuencia="Cada cuánto se hace la copia",
    hora="Hora del día (0-23, hora de RD)",
    dia_semana="Día de la semana (frecuencia semanal)",
    dia_mes="Día del mes, 1-28 (frecuencia mensual)",
    intervalo="Intervalo entre copias (frecuencia por intervalo): usa d, h y m, por ejemplo 30m, 6h o 1d",
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
) -> None:
    guild = interaction.guild
    now = datetime.now(timezone.utc)
    if all(v is None for v in (frecuencia, hora, dia_semana, dia_mes, intervalo)):
        await interaction.response.send_message(template_config_summary(guild.id, now), ephemeral=True)
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
        guild_config_set(guild.id, "template_mode", frecuencia.value)
        changes.append(f"frecuencia → {frecuencia.name}")
    if hora is not None:
        guild_config_set(guild.id, "template_hour", str(hora))
        changes.append(f"hora → {hora}:00")
    if dia_semana is not None:
        guild_config_set(guild.id, "template_weekday", str(dia_semana.value))
        changes.append(f"día de la semana → {dia_semana.name}")
    if dia_mes is not None:
        guild_config_set(guild.id, "template_monthday", str(dia_mes))
        changes.append(f"día del mes → {dia_mes}")
    if intervalo_minutes is not None:
        guild_config_set(guild.id, "template_interval_minutes", str(intervalo_minutes))
        changes.append(f"intervalo → {format_duration(intervalo_minutes)}")
    # Un cambio de horario solo afecta a la PRÓXIMA copia: da por hecho el turno actual
    # (o reinicia el reloj del intervalo) para que no dispare una copia inmediata.
    if get_template_mode(guild.id) == "interval":
        guild_config_set(guild.id, "template_last_run", now.isoformat())
    elif get_template_mode(guild.id) in ("daily", "weekly", "monthly"):
        slot = template_last_slot(guild.id, get_template_mode(guild.id), now.astimezone(STREAK_TZ))
        if slot is not None:
            guild_config_set(guild.id, "template_last_slot", slot.isoformat())

    note = ""
    if get_template_mode(guild.id) != "off":
        try:
            if not await guild.templates():
                note = "\n\n⚠️ El servidor aún no tiene plantilla: créala en Ajustes del servidor → Plantilla de servidor, o la copia fallará."
        except discord.HTTPException as e:
            note = f"\n\n⚠️ No pude comprobar si hay plantilla: `{e}`"

    await interaction.followup.send(
        "✅ Guardado: " + "; ".join(changes) + "\n\n" + template_config_summary(guild.id, now) + note,
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
        owner = await bot.fetch_user(interaction.guild.owner_id)
        await owner.send(embed=embed)
        if interaction.user.id == owner.id:
            confirmation = "✅ Plantilla sincronizada. Te envié el enlace por mensaje privado."
        else:
            confirmation = "✅ Plantilla sincronizada. El enlace fue enviado por mensaje privado al creador del servidor."
        await interaction.followup.send(confirmation, ephemeral=True)
    except discord.HTTPException:
        # El enlace no se publica en el canal ni se entrega a otro administrador.
        await interaction.followup.send(
            "⚠️ La plantilla se sincronizó, pero no pude enviar el enlace por mensaje privado al creador del servidor. Debe tener los DMs habilitados.",
            ephemeral=True,
        )
    await log_embed(
        interaction.guild, "Plantilla sincronizada manualmente",
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
    if message.channel.id in hp_trap_ids(message.guild.id):
        return  # lo escrito en un canal trampa no cuenta como actividad
    punish_id = hp_punish_role_id(message.guild.id)
    if (punish_id and any(r.id == punish_id for r in message.author.roles)) or condemnation_get(message.guild.id, message.author.id) is not None:
        return  # los condenados no suman actividad

    today = datetime.now(STREAK_TZ).date()
    yesterday = today - timedelta(days=1)
    db_track_message(message.guild.id, message.author.id, today.isoformat(), yesterday.isoformat())


@bot.listen("on_message")
async def moderation_cache_recent_messages(message: discord.Message) -> None:
    if message.guild is None or message.author.bot:
        return
    conn = db_connect()
    conn.execute(
        "INSERT OR REPLACE INTO moderation_message_cache "
        "(guild_id, channel_id, message_id, user_id, content, attachments, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (message.guild.id, message.channel.id, message.id, message.author.id, (message.content or "")[:2000],
         json.dumps([attachment.url for attachment in message.attachments[:5]], ensure_ascii=False), message.created_at.isoformat()),
    )
    conn.execute(
        "DELETE FROM moderation_message_cache WHERE guild_id = ? AND channel_id = ? AND user_id = ? AND message_id NOT IN ("
        "SELECT message_id FROM moderation_message_cache WHERE guild_id = ? AND channel_id = ? AND user_id = ? "
        "ORDER BY created_at DESC LIMIT 5)",
        (message.guild.id, message.channel.id, message.author.id, message.guild.id, message.channel.id, message.author.id),
    )
    conn.close()


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

    messages, streak, last_active = db_get_activity(interaction.guild.id, target.id)

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

def motw_last_scheduled(guild_id: int, now: datetime) -> datetime:
    """Último momento programado (día/hora configurables, hora local) que ya
    pasó respecto a `now`."""
    weekday, hour = get_motw_weekday(guild_id), get_motw_hour(guild_id)
    days_back = (now.weekday() - weekday) % 7
    scheduled = (now - timedelta(days=days_back)).replace(
        hour=hour, minute=0, second=0, microsecond=0
    )
    if scheduled > now:
        scheduled -= timedelta(days=7)
    return scheduled


def motw_mark_current_slot(guild_id: int, now: datetime | None = None) -> None:
    """Llamar tras cambiar el horario: da por "ya pasado" el turno más reciente del
    nuevo horario, para que el cambio solo afecte al PRÓXIMO anuncio y no dispare uno
    inmediato con la semana a medias. Solo avanza el marcador, nunca lo retrocede
    (así tampoco se duplica un anuncio ya hecho hoy)."""
    new_slot = motw_last_scheduled(guild_id, now or datetime.now(STREAK_TZ)).date().isoformat()
    last = guild_config_get(guild_id, "motw_last_slot")
    if last is None or new_slot > last:
        guild_config_set(guild_id, "motw_last_slot", new_slot)


@tasks.loop(minutes=10)
async def member_of_the_week_loop() -> None:
    """Revisa cada servidor por separado y confirma el turno solo si el anuncio salió."""
    now = datetime.now(STREAK_TZ)
    for guild in bot.guilds:
        try:
            if not get_motw_channel_id(guild.id):
                continue
            slot = motw_last_scheduled(guild.id, now).date().isoformat()
            last = guild_config_get(guild.id, "motw_last_slot")
            if last is None:
                guild_config_set(guild.id, "motw_last_slot", slot)
                continue
            if last == slot:
                continue
            error = await announce_member_of_the_week(guild.id)
            if error is None:
                guild_config_set(guild.id, "motw_last_slot", slot)
            else:
                print(f"⚠️ Miembro de la Semana reintentará en {guild.name}: {error}")
        except Exception:
            print(f"❌ Falló Miembro de la Semana en {guild.name}:")
            traceback.print_exc()


async def announce_member_of_the_week(guild_id: int, reset: bool = True) -> str | None:
    """reset=False es para /motw_test: anuncia con los datos reales pero no
    toca los contadores, para poder probar sin afectar la semana en curso.
    Devuelve None si se publicó bien, o el texto del error si Discord lo rechazó
    (en ese caso NO se reinician los contadores, para no perder la semana)."""
    channel = bot.get_channel(get_motw_channel_id(guild_id))
    if channel is None:
        print("⚠️ Miembro de la Semana: no encontré el canal de anuncios configurado.")
        return "No encontré el canal de anuncios configurado."
    guild = channel.guild

    # Top 2 entre quienes siguen en el servidor.
    ranking: list[tuple[discord.Member, int]] = []
    for user_id, count in db_week_ranking(guild.id):
        member = guild.get_member(user_id)
        punish_id = hp_punish_role_id(guild.id)
        if punish_id and member is not None and any(r.id == punish_id for r in member.roles):
            continue  # castigado por el honeypot: no puede ganar
        if member is not None and condemnation_get(member.guild.id, member.id) is not None:
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
            db_reset_week(guild.id)
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
        db_reset_week(guild.id)  # contadores de la nueva semana en cero (para TODOS, no solo el top)
    return None


@bot.tree.command(name="motw_set_schedule", description="Cambiar el día/hora del anuncio de Miembro de la Semana.")
@discord.app_commands.describe(dia="Día de la semana", hora="Hora del día (0-23, hora de RD)")
@discord.app_commands.choices(dia=[
    discord.app_commands.Choice(name=name, value=i) for i, name in enumerate(MOTW_WEEKDAY_NAMES)
])
@discord.app_commands.checks.has_permissions(kick_members=True)
@discord.app_commands.guild_only()
async def motw_set_schedule(interaction: discord.Interaction, dia: discord.app_commands.Choice[int], hora: discord.app_commands.Range[int, 0, 23]) -> None:
    set_motw_schedule(interaction.guild.id, dia.value, hora)
    motw_mark_current_slot(interaction.guild.id)
    now = datetime.now(STREAK_TZ)
    next_run = motw_last_scheduled(interaction.guild.id, now) + timedelta(days=7)
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
@discord.app_commands.guild_only()
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

    set_motw_channel_id(interaction.guild.id, canal.id)
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
@discord.app_commands.guild_only()
async def motw_test(interaction: discord.Interaction) -> None:
    if bot.get_channel(get_motw_channel_id(interaction.guild.id)) is None:
        await interaction.response.send_message("No encuentro el canal de anuncios configurado (¿fue borrado o el bot perdió acceso?). Elige otro con /motw_set_channel.", ephemeral=True)
        return
    await interaction.response.send_message("Probando el anuncio de Miembro de la Semana (no se resetean contadores)...", ephemeral=True)
    error = await announce_member_of_the_week(interaction.guild.id, reset=False)
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
    conn = db_connect()
    conn.execute(
        "CREATE TABLE IF NOT EXISTS honeypot_channels ("
        "channel_id INTEGER PRIMARY KEY, warning_message_id INTEGER)"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS honeypot_exempt ("
        "kind TEXT NOT NULL, target_id INTEGER NOT NULL, PRIMARY KEY (kind, target_id))"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS guild_honeypot_channels ("
        "guild_id INTEGER NOT NULL, channel_id INTEGER NOT NULL, warning_message_id INTEGER, "
        "PRIMARY KEY (guild_id, channel_id))"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS guild_honeypot_exempt ("
        "guild_id INTEGER NOT NULL, kind TEXT NOT NULL, target_id INTEGER NOT NULL, "
        "PRIMARY KEY (guild_id, kind, target_id))"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS guild_honeypot_state ("
        "guild_id INTEGER NOT NULL, user_id INTEGER NOT NULL, role_ids TEXT NOT NULL, saved_at TEXT NOT NULL, "
        "PRIMARY KEY (guild_id, user_id))"
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
    try:
        conn.execute("ALTER TABLE honeypot_triggers ADD COLUMN guild_id INTEGER NOT NULL DEFAULT 0")
    except sqlite3.OperationalError:
        pass
    conn.execute(
        "CREATE TABLE IF NOT EXISTS condemnations ("
        "user_id INTEGER PRIMARY KEY, guild_id INTEGER NOT NULL, role_id INTEGER NOT NULL DEFAULT 0, role_ids TEXT NOT NULL, "
        "reason TEXT NOT NULL, duration_minutes INTEGER, condemned_at TEXT NOT NULL, "
        "expires_at TEXT, origin TEXT NOT NULL, applied_by INTEGER, active INTEGER NOT NULL DEFAULT 1, "
        "pardoned_by INTEGER, pardoned_at TEXT, resolution TEXT, announcement_message_id INTEGER)"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS guild_cases ("
        "guild_id INTEGER NOT NULL, user_id INTEGER NOT NULL, role_id INTEGER NOT NULL DEFAULT 0, role_ids TEXT NOT NULL, "
        "reason TEXT NOT NULL, duration_minutes INTEGER, condemned_at TEXT NOT NULL, "
        "expires_at TEXT, origin TEXT NOT NULL, applied_by INTEGER, active INTEGER NOT NULL DEFAULT 1, "
        "pardoned_by INTEGER, pardoned_at TEXT, resolution TEXT, announcement_message_id INTEGER, "
        "moderation_case_number INTEGER, "
        "PRIMARY KEY (guild_id, user_id))"
    )
    try:
        conn.execute("ALTER TABLE guild_cases ADD COLUMN moderation_case_number INTEGER")
    except sqlite3.OperationalError:
        pass
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


def hp_setting_get(guild_id: int, key: str) -> str | None:
    value = guild_config_get(guild_id, key)
    if value is not None:
        return value
    if legacy_fallback_allowed(guild_id):
        return hp_meta_get(key)
    return None


def hp_setting_set(guild_id: int, key: str, value: str) -> None:
    guild_config_set(guild_id, key, value)


def hp_trap_ids(guild_id: int) -> set[int]:
    return set(hp_traps(guild_id))


def hp_traps(guild_id: int) -> dict[int, int | None]:
    conn = db_connect()
    rows = conn.execute(
        "SELECT channel_id, warning_message_id FROM guild_honeypot_channels WHERE guild_id = ?",
        (guild_id,),
    ).fetchall()
    if not rows:
        if legacy_fallback_allowed(guild_id):
            rows = conn.execute("SELECT channel_id, warning_message_id FROM honeypot_channels").fetchall()
            for channel_id, warning_message_id in rows:
                conn.execute(
                    "INSERT OR IGNORE INTO guild_honeypot_channels (guild_id, channel_id, warning_message_id) VALUES (?, ?, ?)",
                    (guild_id, channel_id, warning_message_id),
                )
            conn.commit()
    conn.close()
    return {row[0]: row[1] for row in rows}


def hp_add_trap(guild_id: int, channel_id: int) -> None:
    conn = db_connect()
    conn.execute(
        "INSERT OR IGNORE INTO guild_honeypot_channels (guild_id, channel_id) VALUES (?, ?)",
        (guild_id, channel_id),
    )
    conn.commit()
    conn.close()


def hp_remove_trap(guild_id: int, channel_id: int) -> None:
    conn = db_connect()
    conn.execute(
        "DELETE FROM guild_honeypot_channels WHERE guild_id = ? AND channel_id = ?",
        (guild_id, channel_id),
    )
    conn.commit()
    conn.close()


def hp_set_warning_message(guild_id: int, channel_id: int, message_id: int | None) -> None:
    conn = db_connect()
    conn.execute(
        "UPDATE guild_honeypot_channels SET warning_message_id = ? WHERE guild_id = ? AND channel_id = ?",
        (message_id, guild_id, channel_id),
    )
    conn.commit()
    conn.close()


def hp_exempt_ids(guild_id: int, kind: str) -> set[int]:
    conn = db_connect()
    rows = conn.execute(
        "SELECT target_id FROM guild_honeypot_exempt WHERE guild_id = ? AND kind = ?",
        (guild_id, kind),
    ).fetchall()
    if not rows:
        if legacy_fallback_allowed(guild_id):
            rows = conn.execute("SELECT target_id FROM honeypot_exempt WHERE kind = ?", (kind,)).fetchall()
            for (target_id,) in rows:
                conn.execute(
                    "INSERT OR IGNORE INTO guild_honeypot_exempt (guild_id, kind, target_id) VALUES (?, ?, ?)",
                    (guild_id, kind, target_id),
                )
            conn.commit()
    conn.close()
    return {row[0] for row in rows}


def hp_exempt_add(guild_id: int, kind: str, target_id: int) -> None:
    conn = db_connect()
    conn.execute(
        "INSERT OR IGNORE INTO guild_honeypot_exempt (guild_id, kind, target_id) VALUES (?, ?, ?)",
        (guild_id, kind, target_id),
    )
    conn.commit()
    conn.close()


def hp_exempt_remove(guild_id: int, kind: str, target_id: int) -> None:
    conn = db_connect()
    conn.execute(
        "DELETE FROM guild_honeypot_exempt WHERE guild_id = ? AND kind = ? AND target_id = ?",
        (guild_id, kind, target_id),
    )
    conn.commit()
    conn.close()


def hp_save_punished(guild_id: int, user_id: int, role_ids: list[int]) -> None:
    conn = db_connect()
    conn.execute(
        "INSERT INTO guild_honeypot_state (guild_id, user_id, role_ids, saved_at) VALUES (?, ?, ?, ?) "
        "ON CONFLICT(guild_id, user_id) DO UPDATE SET role_ids = excluded.role_ids, saved_at = excluded.saved_at",
        (guild_id, user_id, json.dumps(role_ids), datetime.now(timezone.utc).isoformat()),
    )
    conn.commit()
    conn.close()


def hp_get_punished(guild_id: int, user_id: int) -> list[int] | None:
    conn = db_connect()
    row = conn.execute(
        "SELECT role_ids FROM guild_honeypot_state WHERE guild_id = ? AND user_id = ?",
        (guild_id, user_id),
    ).fetchone()
    conn.close()
    return json.loads(row[0]) if row else None


def hp_clear_punished(guild_id: int, user_id: int) -> None:
    conn = db_connect()
    conn.execute(
        "DELETE FROM guild_honeypot_state WHERE guild_id = ? AND user_id = ?",
        (guild_id, user_id),
    )
    conn.commit()
    conn.close()


def condemnation_get(guild_id: int, user_id: int, active_only: bool = True) -> sqlite3.Row | None:
    conn = db_connect()
    conn.row_factory = sqlite3.Row
    query = "SELECT * FROM guild_cases WHERE guild_id = ? AND user_id = ?"
    params = (guild_id, user_id)
    if active_only:
        query += " AND active = 1"
    row = conn.execute(query, params).fetchone()
    if row is None:
        if legacy_fallback_allowed(guild_id):
            legacy_query = "SELECT * FROM condemnations WHERE user_id = ? AND (guild_id = ? OR guild_id = 0)"
            if active_only:
                legacy_query += " AND active = 1"
            legacy = conn.execute(legacy_query, (user_id, guild_id)).fetchone()
            if legacy is not None:
                conn.execute(
                    "INSERT OR REPLACE INTO guild_cases "
                    "(guild_id, user_id, role_id, role_ids, reason, duration_minutes, condemned_at, expires_at, origin, applied_by, active, pardoned_by, pardoned_at, resolution, announcement_message_id) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (guild_id, legacy["user_id"], legacy["role_id"], legacy["role_ids"], legacy["reason"],
                     legacy["duration_minutes"], legacy["condemned_at"], legacy["expires_at"], legacy["origin"],
                     legacy["applied_by"], legacy["active"], legacy["pardoned_by"], legacy["pardoned_at"],
                     legacy["resolution"], legacy["announcement_message_id"]),
                )
                conn.commit()
                row = conn.execute(query, params).fetchone()
    conn.close()
    return row


def condemnation_save(
    user_id: int, guild_id: int, role_id: int, role_ids: list[int], reason: str,
    duration_minutes: int | None, origin: str, applied_by: int | None,
    condemned_at: datetime | None = None,
) -> None:
    when = condemned_at or datetime.now(timezone.utc)
    expires = when + timedelta(minutes=duration_minutes) if duration_minutes else None
    conn = db_connect()
    conn.execute(
        "INSERT INTO guild_cases "
        "(guild_id, user_id, role_id, role_ids, reason, duration_minutes, condemned_at, expires_at, origin, applied_by, active) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1) "
        "ON CONFLICT(guild_id, user_id) DO UPDATE SET role_id=excluded.role_id, role_ids=excluded.role_ids, "
        "reason=excluded.reason, duration_minutes=excluded.duration_minutes, condemned_at=excluded.condemned_at, "
        "expires_at=excluded.expires_at, origin=excluded.origin, applied_by=excluded.applied_by, active=1, "
        "pardoned_by=NULL, pardoned_at=NULL, resolution=NULL, announcement_message_id=NULL",
        (guild_id, user_id, role_id, json.dumps(role_ids), reason, duration_minutes, when.isoformat(),
         expires.isoformat() if expires else None, origin, applied_by),
    )
    conn.commit()
    conn.close()


def condemnation_deactivate(
    guild_id: int, user_id: int, *, resolution: str | None = None, resolved_by: int | None = None
) -> None:
    conn = db_connect()
    if resolution == "pardoned":
        conn.execute(
            "UPDATE guild_cases SET active = 0, pardoned_by = ?, pardoned_at = ?, resolution = 'pardoned' "
            "WHERE guild_id = ? AND user_id = ?",
            (resolved_by, datetime.now(timezone.utc).isoformat(), guild_id, user_id),
        )
    elif resolution:
        conn.execute(
            "UPDATE guild_cases SET active = 0, resolution = ? WHERE guild_id = ? AND user_id = ?",
            (resolution, guild_id, user_id),
        )
    else:
        conn.execute("UPDATE guild_cases SET active = 0 WHERE guild_id = ? AND user_id = ?", (guild_id, user_id))
    conn.commit()
    conn.close()
    hp_clear_punished(guild_id, user_id)


def condemnation_add_saved_roles(guild_id: int, user_id: int, new_ids: list[int]) -> None:
    row = condemnation_get(guild_id, user_id)
    if row is None or not new_ids:
        return
    merged = condemnation_parse_role_ids(row["role_ids"])
    for rid in new_ids:
        if rid not in merged:
            merged.append(rid)
    conn = db_connect()
    conn.execute(
        "UPDATE guild_cases SET role_ids = ? WHERE guild_id = ? AND user_id = ? AND active = 1",
        (json.dumps(merged), guild_id, user_id),
    )
    conn.commit()
    conn.close()


def condemnation_is_expired(row: sqlite3.Row) -> bool:
    return bool(row["expires_at"]) and datetime.fromisoformat(row["expires_at"]) <= datetime.now(timezone.utc)


def condemnation_list_all_active() -> list[sqlite3.Row]:
    conn = db_connect()
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT * FROM guild_cases WHERE active = 1 AND (expires_at IS NULL OR expires_at > ?)",
        (datetime.now(timezone.utc).isoformat(),),
    ).fetchall()
    conn.close()
    return rows


def condemnation_list(guild_id: int) -> list[sqlite3.Row]:
    conn = db_connect()
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT * FROM guild_cases WHERE active = 1 AND guild_id = ? "
        "AND (expires_at IS NULL OR expires_at > ?) ORDER BY condemned_at DESC",
        (guild_id, datetime.now(timezone.utc).isoformat()),
    ).fetchall()
    conn.close()
    return rows


def condemnation_default_duration_minutes(guild_id: int | None = None) -> int | None:
    """Duración predeterminada para nuevas condenas. None = indefinida."""
    value = guild_config_get(guild_id, "condemnation_default_duration") if guild_id is not None else None
    if value is None:
        if legacy_fallback_allowed(guild_id):
            value = db_meta_get("condemnation_default_duration")
    if not value or value.strip().lower() in {"indefinida", "indefinido", "none", "null", "0"}:
        return None
    try:
        return parse_duration(value, 1, get_condemnation_max_minutes(guild_id))
    except ValueError:
        return None


def set_condemnation_default_duration(value: str | None, guild_id: int | None = None) -> None:
    if guild_id is not None:
        guild_config_set(guild_id, "condemnation_default_duration", value or "indefinida")
    else:
        db_meta_set("condemnation_default_duration", value or "indefinida")


def condemnation_channel_id(guild_id: int | None = None) -> int:
    if guild_id is None:
        value = db_meta_get("condemned_channel_id")
        return int(value) if value else CONDEMNED_CHANNEL_ID
    configured = get_guild_channel_id(guild_id, "condemned")
    if configured:
        return configured
    value = guild_config_get(guild_id, "condemned_channel_id")
    if value:
        return int(value)
    if legacy_fallback_allowed(guild_id):
        value = db_meta_get("condemned_channel_id")
        return int(value) if value else CONDEMNED_CHANNEL_ID
    return 0


def get_condemnation_emoji(guild_id: int | None = None) -> str:
    if guild_id is not None:
        value = guild_config_get(guild_id, "condemnation_emoji")
        if value:
            return value
    if legacy_fallback_allowed(guild_id):
        return db_meta_get("condemnation_emoji") or CONDEMNED_EMOJI
    return CONDEMNED_EMOJI



MODERATION_CASE_TYPES = {"WARN", "MUTE", "KICK", "BAN", "CONDEMN"}


def moderation_case_next_number(guild_id: int) -> int:
    conn = db_connect()
    row = conn.execute(
        "SELECT COALESCE(MAX(case_number), 0) + 1 FROM moderation_cases WHERE guild_id = ?",
        (guild_id,),
    ).fetchone()
    conn.close()
    return int(row[0])


def moderation_case_get(guild_id: int, case_number: int) -> sqlite3.Row | None:
    conn = db_connect()
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        "SELECT * FROM moderation_cases WHERE guild_id = ? AND case_number = ?",
        (guild_id, case_number),
    ).fetchone()
    conn.close()
    return row


def moderation_case_list(guild_id: int, user_id: int | None = None, case_type: str | None = None, open_only: bool | None = None, limit: int = 20) -> list[sqlite3.Row]:
    conn = db_connect()
    conn.row_factory = sqlite3.Row
    where = ["guild_id = ?"]
    params: list[object] = [guild_id]
    if user_id is not None:
        where.append("user_id = ?")
        params.append(user_id)
    if case_type:
        where.append("type = ?")
        params.append(case_type.upper())
    if open_only is not None:
        where.append("open = ?")
        params.append(1 if open_only else 0)
    params.append(max(1, min(limit, 50)))
    rows = conn.execute(
        "SELECT * FROM moderation_cases WHERE " + " AND ".join(where) + " ORDER BY case_number DESC LIMIT ?",
        params,
    ).fetchall()
    conn.close()
    return rows


def moderation_case_message_history(guild_id: int, user_id: int) -> str:
    conn = db_connect()
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT channel_id, message_id, content, attachments, created_at FROM moderation_message_cache "
        "WHERE guild_id = ? AND user_id = ? ORDER BY channel_id, created_at DESC",
        (guild_id, user_id),
    ).fetchall()
    conn.close()
    grouped: dict[int, list[dict[str, object]]] = {}
    for row in rows:
        bucket = grouped.setdefault(int(row["channel_id"]), [])
        if len(bucket) >= 5:
            continue
        try:
            attachment_list = json.loads(row["attachments"] or "[]")
        except json.JSONDecodeError:
            attachment_list = []
        bucket.append({
            "message_id": int(row["message_id"]),
            "content": (row["content"] or "")[:1000],
            "attachments": attachment_list,
            "created_at": row["created_at"],
        })
    return json.dumps(grouped, ensure_ascii=False)


def moderation_case_create(guild_id: int, case_type: str, user_id: int, reason: str, *, duration_minutes: int | None = None, author_id: int | None = None, proof: str | None = None, verified_proof: str | None = None, moderator_notes: str | None = None) -> int:
    case_type = case_type.upper()
    if case_type not in MODERATION_CASE_TYPES:
        raise ValueError("Tipo de caso inválido.")
    case_number = moderation_case_next_number(guild_id)
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=duration_minutes) if duration_minutes else None
    conn = db_connect()
    conn.execute(
        "INSERT INTO moderation_cases "
        "(guild_id, case_number, type, user_id, reason, duration_minutes, created_at, expires_at, author_id, proof, verified_proof, moderator_notes, message_history, open) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)",
        (guild_id, case_number, case_type, user_id, reason[:1000], duration_minutes, now.isoformat(),
         expires_at.isoformat() if expires_at else None, author_id, (proof or "")[:2000],
         (verified_proof or "")[:2000], (moderator_notes or "")[:2000],
         moderation_case_message_history(guild_id, user_id)),
    )
    conn.close()
    return case_number


def moderation_case_update(guild_id: int, case_number: int, *, reason: str | None = None, duration_minutes: int | None | object = ..., proof: str | None = None, verified_proof: str | None = None, notes: str | None = None) -> bool:
    row = moderation_case_get(guild_id, case_number)
    if row is None:
        return False
    updates: list[str] = []
    params: list[object] = []
    if reason is not None:
        updates.append("reason = ?")
        params.append(reason[:1000])
    if duration_minutes is not ...:
        updates.extend(["duration_minutes = ?", "expires_at = ?"])
        params.append(duration_minutes)
        params.append((datetime.fromisoformat(row["created_at"]) + timedelta(minutes=int(duration_minutes))).isoformat() if duration_minutes else None)
    if proof is not None:
        updates.append("proof = ?")
        params.append(proof[:2000])
    if verified_proof is not None:
        updates.append("verified_proof = ?")
        params.append(verified_proof[:2000])
    if notes is not None:
        updates.append("moderator_notes = ?")
        params.append(notes[:2000])
    if not updates:
        return True
    params.extend([guild_id, case_number])
    conn = db_connect()
    conn.execute("UPDATE moderation_cases SET " + ", ".join(updates) + " WHERE guild_id = ? AND case_number = ?", params)
    conn.close()
    return True


def moderation_case_close(guild_id: int, case_number: int, *, closed_by: int | None, resolution: str = "closed") -> bool:
    conn = db_connect()
    cur = conn.execute(
        "UPDATE moderation_cases SET open = 0, closed_at = ?, closed_by = ?, resolution = ? "
        "WHERE guild_id = ? AND case_number = ? AND open = 1",
        (datetime.now(timezone.utc).isoformat(), closed_by, resolution[:500], guild_id, case_number),
    )
    conn.close()
    return cur.rowcount > 0


def moderation_case_delete(guild_id: int, case_number: int) -> bool:
    conn = db_connect()
    cur = conn.execute("DELETE FROM moderation_cases WHERE guild_id = ? AND case_number = ?", (guild_id, case_number))
    conn.close()
    return cur.rowcount > 0


async def moderation_verified_proof(guild: discord.Guild, proof: str | None) -> str | None:
    if not proof:
        return None
    match = re.search(r"discord(?:app)?\.com/channels/(\d+)/(\d+)/(\d+)", proof)
    if not match or int(match.group(1)) != guild.id:
        return None
    channel = guild.get_channel_or_thread(int(match.group(2)))
    if channel is None or not hasattr(channel, "fetch_message"):
        return None
    try:
        message = await channel.fetch_message(int(match.group(3)))
    except discord.HTTPException:
        return None
    text = message.content or "(sin texto)"
    if message.attachments:
        text += "\n" + "\n".join(attachment.url for attachment in message.attachments[:5])
    return text[:2000]


def moderation_case_embed(guild: discord.Guild, row: sqlite3.Row) -> discord.Embed:
    embed = discord.Embed(
        title=f"Moderation Case #{row['case_number']} · {row['type']}",
        color=discord.Color.orange() if row["open"] else discord.Color.dark_grey(),
        timestamp=datetime.fromisoformat(row["created_at"]),
    )
    embed.add_field(name="Estado", value="Abierto" if row["open"] else "Cerrado", inline=True)
    embed.add_field(name="Usuario", value=f"<@{row['user_id']}>\nID: {row['user_id']}", inline=True)
    embed.add_field(name="Autor", value=f"<@{row['author_id']}>" if row["author_id"] else "El Heraldo", inline=True)
    embed.add_field(name="Motivo", value=str(row["reason"])[:1024], inline=False)
    duration_text = format_duration(int(row["duration_minutes"])) if row["duration_minutes"] else "Indefinida / no aplica"
    embed.add_field(name="Duración", value=duration_text, inline=True)
    if row["expires_at"]:
        embed.add_field(name="Caduca", value=discord.utils.format_dt(datetime.fromisoformat(row["expires_at"]), "R"), inline=True)
    if row["proof"]:
        embed.add_field(name="Prueba", value=str(row["proof"])[:1024], inline=False)
    if row["verified_proof"]:
        embed.add_field(name="Prueba verificada", value=str(row["verified_proof"])[:1024], inline=False)
    if row["moderator_notes"]:
        embed.add_field(name="Notas del moderador", value=str(row["moderator_notes"])[:1024], inline=False)
    if not row["open"] and row["resolution"]:
        embed.add_field(name="Resolución", value=str(row["resolution"])[:1024], inline=False)
    embed.set_footer(text=f"{guild.name} · El Heraldo 🪽")
    return embed


def moderation_cases_summary(guild: discord.Guild) -> str:
    rows = moderation_case_list(guild.id, limit=8)
    if not rows:
        return "**El Heraldo · Moderation · Cases**\n\nTodavía no hay casos registrados."
    lines = []
    for row in rows:
        state = "abierto" if row["open"] else "cerrado"
        lines.append(f"**#{row['case_number']}** · {row['type']} · <@{row['user_id']}> · {state}\n{str(row['reason'])[:120]}")
    return "**El Heraldo · Moderation · Cases**\n\n" + "\n\n".join(lines)


async def moderation_send_case_dm(guild: discord.Guild, user_id: int, case_number: int) -> bool:
    row = moderation_case_get(guild.id, case_number)
    member = guild.get_member(user_id)
    if row is None or member is None:
        return False
    try:
        await member.send(embed=moderation_case_embed(guild, row))
        return True
    except discord.HTTPException:
        return False


async def moderation_apply_case_punishment(interaction: discord.Interaction, member: discord.Member, case_type: str, reason: str, duration_minutes: int | None = None, proof: str | None = None) -> tuple[bool, str, int | None]:
    guild = interaction.guild
    case_type = case_type.upper()
    if member.bot:
        return False, "Los bots no se castigan desde Moderation.", None
    if member.id == guild.owner_id:
        return False, "No se puede castigar al dueño del servidor.", None
    if interaction.user.id != guild.owner_id and member.top_role >= interaction.user.top_role:
        return False, "La jerarquía del servidor impide aplicar esta acción.", None
    if member.top_role >= guild.me.top_role:
        return False, "El rol del miembro está al mismo nivel o por encima de El Heraldo.", None
    verified = await moderation_verified_proof(guild, proof)
    try:
        if case_type == "MUTE":
            minutes = duration_minutes or 30
            await member.timeout(datetime.now(timezone.utc) + timedelta(minutes=min(minutes, 28 * 24 * 60)), reason=reason)
        elif case_type == "KICK":
            await member.kick(reason=reason)
        elif case_type == "BAN":
            await member.ban(reason=reason, delete_message_seconds=0)
        elif case_type != "WARN":
            return False, "Tipo de castigo no compatible.", None
    except discord.HTTPException as exc:
        return False, f"Discord rechazó la acción: {exc}", None
    case_number = moderation_case_create(
        guild.id, case_type, member.id, reason, duration_minutes=duration_minutes,
        author_id=interaction.user.id, proof=proof, verified_proof=verified,
    )
    dm_ok = await moderation_send_case_dm(guild, member.id, case_number)
    await log_embed(
        guild, f"Moderation · {case_type}",
        f"Caso #{case_number} · {member.mention} ({member.id})\nMotivo: {reason}\nModerador: {interaction.user.mention}\nDM: {'enviado' if dm_ok else 'no disponible'}",
        discord.Color.orange(),
    )
    return True, f"Caso #{case_number} creado.", case_number


async def moderation_close_case_effect(guild: discord.Guild, row: sqlite3.Row, actor: discord.Member) -> str:
    case_type = str(row["type"])
    user_id = int(row["user_id"])
    if case_type == "MUTE":
        member = guild.get_member(user_id)
        if member is not None:
            try:
                await member.timeout(None, reason=f"Cierre del caso #{row['case_number']}")
                return "Timeout retirado."
            except discord.HTTPException:
                return "Caso cerrado; no pude retirar el timeout."
    if case_type == "BAN":
        try:
            await guild.unban(discord.Object(id=user_id), reason=f"Cierre del caso #{row['case_number']}")
            return "Ban retirado."
        except (discord.NotFound, discord.HTTPException):
            return "Caso cerrado; el usuario no estaba baneado o no pude retirarlo."
    if case_type == "CONDEMN":
        member = guild.get_member(user_id)
        if member is not None and condemnation_get(guild.id, user_id) is not None:
            ok, note = await release_condemned_member(member, released_by=actor, automatic=False)
            return note if ok else f"No pude levantar la condena: {note}"
    return "Caso cerrado."

MODERATION_REPORT_MAX_REACTIONS = 10
MODERATION_REPORT_ACTIONS = {"report", "timeout", "kick", "ban", "condemn"}
MODERATION_REPORT_REACTION_DEFAULTS = (
    {"emoji": "📢", "label": "Spam", "action": "timeout", "duration_minutes": 30, "threshold": 2, "purge_minutes": 30},
    {"emoji": "🚩", "label": "Contenido inapropiado / no permitido", "action": "condemn", "duration_minutes": 1440, "threshold": 3, "purge_minutes": 30},
    {"emoji": "🤓", "label": "Sospechoso (posible cuenta falsa o estafa)", "action": "condemn", "duration_minutes": None, "threshold": 2, "purge_minutes": 30},
    {"emoji": "🔞", "label": "Posible menor de edad", "action": "ban", "duration_minutes": None, "threshold": 2, "purge_minutes": 30},
)
_moderation_report_dedupe: dict[tuple[int, int, int, str], float] = {}
_reaction_condemn_pending: set[tuple[int, int]] = set()


def _moderation_emoji_key(value: str) -> str:
    return str(value).replace("\ufe0f", "").strip()


def _moderation_report_default_reactions() -> list[dict[str, object]]:
    return [dict(item) for item in MODERATION_REPORT_REACTION_DEFAULTS]


def _normalize_moderation_report_rule(item: dict) -> dict[str, object] | None:
    emoji = str(item.get("emoji", "")).strip()
    label = str(item.get("label", "")).strip()
    if not emoji or not label:
        return None
    action = str(item.get("action", "report")).strip().lower()
    if action not in MODERATION_REPORT_ACTIONS:
        action = "report"
    try:
        threshold = max(1, min(25, int(item.get("threshold", 1))))
    except (TypeError, ValueError):
        threshold = 1
    duration = item.get("duration_minutes")
    try:
        duration_minutes = int(duration) if duration not in (None, "", 0, "0") else None
    except (TypeError, ValueError):
        duration_minutes = None
    if duration_minutes is not None:
        duration_minutes = max(1, min(28 * 24 * 60, duration_minutes))
    purge_raw = item.get("purge_minutes")
    if purge_raw in (None, "", 0, "0") and item.get("delete_message"):
        # Compatibilidad con la versión anterior: "borrar mensaje" pasa a una purga reciente.
        purge_raw = 30
    try:
        purge_minutes = int(purge_raw) if purge_raw not in (None, "", 0, "0") else None
    except (TypeError, ValueError):
        purge_minutes = None
    if purge_minutes is not None:
        purge_minutes = max(1, min(PURGE_MAX_MINUTES, purge_minutes))
    return {
        "emoji": emoji[:100],
        "label": label[:100],
        "action": action,
        "duration_minutes": duration_minutes,
        "threshold": threshold,
        "purge_minutes": purge_minutes,
    }


def moderation_report_reactions(guild_id: int) -> list[dict[str, object]]:
    raw = guild_config_get(guild_id, "moderation_report_reactions")
    if raw is None:
        return _moderation_report_default_reactions()
    try:
        data = json.loads(raw)
    except (TypeError, json.JSONDecodeError):
        return _moderation_report_default_reactions()
    result: list[dict[str, object]] = []
    seen: set[str] = set()
    for item in data if isinstance(data, list) else []:
        if not isinstance(item, dict):
            continue
        normalized = _normalize_moderation_report_rule(item)
        if normalized is None:
            continue
        key = _moderation_emoji_key(str(normalized["emoji"]))
        if key in seen:
            continue
        seen.add(key)
        result.append(normalized)
        if len(result) >= MODERATION_REPORT_MAX_REACTIONS:
            break
    return result


def set_moderation_report_reactions(guild_id: int, reactions: list[dict]) -> None:
    clean: list[dict[str, object]] = []
    seen: set[str] = set()
    for item in reactions:
        normalized = _normalize_moderation_report_rule(item)
        if normalized is None:
            continue
        key = _moderation_emoji_key(str(normalized["emoji"]))
        if key in seen:
            continue
        seen.add(key)
        clean.append(normalized)
        if len(clean) >= MODERATION_REPORT_MAX_REACTIONS:
            break
    guild_config_set(guild_id, "moderation_report_reactions", json.dumps(clean, ensure_ascii=False))


def moderation_report_rule_for_emoji(guild_id: int, emoji: str) -> dict[str, object] | None:
    key = _moderation_emoji_key(emoji)
    for item in moderation_report_reactions(guild_id):
        if _moderation_emoji_key(str(item["emoji"])) == key:
            return item
    return None


def moderation_report_type_for_emoji(guild_id: int, emoji: str) -> str | None:
    rule = moderation_report_rule_for_emoji(guild_id, emoji)
    return str(rule["label"]) if rule else None


def moderation_report_record(
    guild_id: int, message_id: int, target_id: int, emoji_key: str, reporter_id: int
) -> tuple[int, bool]:
    conn = db_connect()
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        "INSERT OR IGNORE INTO moderation_reaction_reports "
        "(guild_id, message_id, target_id, emoji_key, reporter_id, created_at, action_executed) "
        "VALUES (?, ?, ?, ?, ?, ?, 0)",
        (guild_id, message_id, target_id, emoji_key, reporter_id, now),
    )
    row = conn.execute(
        "SELECT COUNT(*), MAX(action_executed) FROM moderation_reaction_reports "
        "WHERE guild_id = ? AND message_id = ? AND target_id = ? AND emoji_key = ?",
        (guild_id, message_id, target_id, emoji_key),
    ).fetchone()
    conn.close()
    return int(row[0]), bool(row[1])


def moderation_report_mark_executed(guild_id: int, message_id: int, target_id: int, emoji_key: str) -> None:
    conn = db_connect()
    conn.execute(
        "UPDATE moderation_reaction_reports SET action_executed = 1 "
        "WHERE guild_id = ? AND message_id = ? AND target_id = ? AND emoji_key = ?",
        (guild_id, message_id, target_id, emoji_key),
    )
    conn.close()


def moderation_action_label(action: str) -> str:
    return {
        "report": "Solo reportar",
        "timeout": "Timeout / mute",
        "kick": "Expulsar",
        "ban": "Banear",
        "condemn": "Condenar",
    }.get(action, action)


async def execute_moderation_report_action(
    guild: discord.Guild,
    target: discord.Member,
    message: discord.Message,
    rule: dict[str, object],
    reporter_count: int,
) -> tuple[bool, str]:
    action = str(rule.get("action", "report"))
    purge_minutes = rule.get("purge_minutes")
    purge_minutes = int(purge_minutes) if purge_minutes else None
    duration_minutes = rule.get("duration_minutes")
    duration_minutes = int(duration_minutes) if duration_minutes else None
    reason = f"Reporte automático: {rule.get('label', 'reporte')} · {reporter_count} reporte(s) distintos"

    protection = condemnation_protection_reason(target)
    if action != "report" and protection:
        return False, f"Acción bloqueada: {protection}."

    notes: list[str] = []
    if purge_minutes:
        after = datetime.now(timezone.utc) - timedelta(minutes=purge_minutes)
        result = await run_purge_job(
            guild,
            target,
            scope_text=f"mensajes de los últimos {format_duration(purge_minutes)}",
            requested_by=f"Moderation · {rule.get('label', 'reporte')}",
            after=after,
            title="Moderation · Purga automática completada",
        )
        if result is None:
            notes.append("purga ya en curso")
        else:
            notes.append(f"purga reciente: {purge_result_text(result)}")

    if action == "report":
        return True, "; ".join(notes) if notes else "solo registrado"

    try:
        if action == "timeout":
            if duration_minutes is None:
                duration_minutes = 30
            until = datetime.now(timezone.utc) + timedelta(minutes=duration_minutes)
            await target.timeout(until, reason=reason)
            notes.append(f"timeout {format_duration(duration_minutes)}")
        elif action == "kick":
            await target.kick(reason=reason)
            notes.append("miembro expulsado")
        elif action == "ban":
            await target.ban(reason=reason, delete_message_seconds=0)
            notes.append("miembro baneado")
        elif action == "condemn":
            ok, note = await condemn_member(
                target,
                reason=reason,
                duration_minutes=duration_minutes,
                purge_spec=None,
                origin="reaction_report",
                applied_by=None,
                source_message_url=message.jump_url,
                source_channel_id=message.channel.id,
            )
            if not ok:
                return False, note
            notes.append("condena aplicada")
    except discord.HTTPException as exc:
        return False, f"Discord rechazó la acción: {exc}"

    return True, "; ".join(notes) if notes else moderation_action_label(action)


def moderation_report_channel_id(guild_id: int) -> int:
    return guild_setting_int(guild_id, "moderation_report_channel_id", 0)


def set_moderation_report_channel_id(guild_id: int, channel_id: int) -> None:
    guild_config_set(guild_id, "moderation_report_channel_id", str(channel_id))


def moderation_report_type_for_emoji(guild_id: int, emoji: str) -> str | None:
    key = _moderation_emoji_key(emoji)
    for item in moderation_report_reactions(guild_id):
        if _moderation_emoji_key(item["emoji"]) == key:
            return item["label"]
    return None


def moderation_is_staff(member: discord.Member) -> bool:
    perms = member.guild_permissions
    return bool(
        perms.administrator
        or perms.moderate_members
        or perms.manage_messages
        or perms.kick_members
        or perms.ban_members
    )


def moderation_reports_summary(guild: discord.Guild) -> str:
    channel_id = moderation_report_channel_id(guild.id)
    channel = guild.get_channel(channel_id) if channel_id else None
    mappings = moderation_report_reactions(guild.id)
    def rule_line(item: dict[str, object]) -> str:
        action = moderation_action_label(str(item.get("action", "report")))
        threshold = int(item.get("threshold", 1))
        duration = item.get("duration_minutes")
        duration_text = f" · {format_duration(int(duration))}" if duration else ""
        purge = item.get("purge_minutes")
        purge_text = f" · purgar {format_duration(int(purge))}" if purge else ""
        return f"• {item['emoji']} → **{item['label']}** · {action}{duration_text} · {threshold} reporte(s){purge_text}"
    mapping_text = "\n".join(rule_line(item) for item in mappings) or "• Sin reacciones configuradas"
    return (
        f"**Canal de reportes:** {channel.mention if isinstance(channel, discord.TextChannel) else 'no configurado'}\n"
        f"**Reacciones de reporte:**\n{mapping_text}\n"
        f"**Reacción para condenar:** {get_condemnation_emoji(guild.id)}\n\n"
        "Los reportes normales solo notifican al equipo de moderación. "
        "La reacción de condena solo puede ser usada por moderadores y exige una razón antes de aplicar el rol de castigo."
    )


def get_condemnation_max_minutes(guild_id: int | None = None) -> int:
    if guild_id is not None:
        return guild_setting_int(guild_id, "condemnation_max_minutes", CONDEMNATION_MAX_MINUTES)
    return CONDEMNATION_MAX_MINUTES


def set_condemnation_channel_id(channel_id: int, guild_id: int | None = None) -> None:
    if guild_id is not None:
        guild_resource_set(guild_id, "channel", "condemned", channel_id)
        guild_config_set(guild_id, "condemned_channel_id", str(channel_id))
    else:
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
        "raid": "Raid Protection",
    }.get(origin, origin)


def condemnation_parse_role_ids(value: str) -> list[int]:
    try:
        return [int(x) for x in json.loads(value)]
    except (TypeError, ValueError, json.JSONDecodeError):
        return []


def hp_log_trigger(member: discord.Member, channel_id: int, content: str, action: str,
                   success: bool, note: str) -> None:
    conn = db_connect()
    conn.execute(
        "INSERT INTO honeypot_triggers (guild_id, user_id, username, channel_id, content, action, success, note, "
        "account_created, joined_at, triggered_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            member.guild.id, member.id, str(member), channel_id, content[:1500], action, int(success), note,
            member.created_at.isoformat(),
            member.joined_at.isoformat() if member.joined_at else None,
            datetime.now(timezone.utc).isoformat(),
        ),
    )
    conn.commit()
    conn.close()
    hp_prune_history(member.guild.id)


def hp_retention_minutes(guild_id: int) -> int:
    value = hp_setting_get(guild_id, "honeypot_retention_minutes")
    return int(value) if value else HONEYPOT_RETENTION_DEFAULT_MINUTES


def _hp_history_legacy_allowed(guild_id: int) -> bool:
    return legacy_fallback_allowed(guild_id)


def hp_prune_history(guild_id: int) -> None:
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=hp_retention_minutes(guild_id))
    conn = db_connect()
    if _hp_history_legacy_allowed(guild_id):
        conn.execute(
            "DELETE FROM honeypot_triggers WHERE (guild_id = ? OR guild_id = 0) AND triggered_at < ?",
            (guild_id, cutoff.isoformat()),
        )
    else:
        conn.execute(
            "DELETE FROM honeypot_triggers WHERE guild_id = ? AND triggered_at < ?",
            (guild_id, cutoff.isoformat()),
        )
    conn.commit()
    conn.close()


def hp_recent_triggers(guild_id: int, limit: int = 10) -> list[sqlite3.Row]:
    conn = db_connect()
    conn.row_factory = sqlite3.Row
    if _hp_history_legacy_allowed(guild_id):
        rows = conn.execute(
            "SELECT * FROM honeypot_triggers WHERE guild_id = ? OR guild_id = 0 ORDER BY id DESC LIMIT ?",
            (guild_id, limit),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM honeypot_triggers WHERE guild_id = ? ORDER BY id DESC LIMIT ?",
            (guild_id, limit),
        ).fetchall()
    conn.close()
    return rows


def hp_total_triggers(guild_id: int) -> int:
    conn = db_connect()
    if _hp_history_legacy_allowed(guild_id):
        total = conn.execute(
            "SELECT COUNT(*) FROM honeypot_triggers WHERE success = 1 AND (guild_id = ? OR guild_id = 0)",
            (guild_id,),
        ).fetchone()[0]
    else:
        total = conn.execute(
            "SELECT COUNT(*) FROM honeypot_triggers WHERE success = 1 AND guild_id = ?",
            (guild_id,),
        ).fetchone()[0]
    conn.close()
    return total


# --- Configuración (guardada en meta) ---------------------------------------

def honeypot_enabled(guild_id: int) -> bool:
    return hp_setting_get(guild_id, "honeypot_enabled") == "1"


def honeypot_paused(guild_id: int) -> bool:
    return hp_setting_get(guild_id, "honeypot_paused") == "1"


def hp_action(guild_id: int) -> str:
    v = hp_setting_get(guild_id, "honeypot_action")
    if v in (None, "", "kick", "ban"):
        return "role"
    return v


def hp_punish_role_id(guild_id: int) -> int:
    configured = get_guild_role_id(guild_id, "condenado")
    if configured:
        return configured
    v = hp_setting_get(guild_id, "honeypot_punish_role")
    return int(v) if v else 0


def hp_protected_channel_reason(channel: discord.abc.GuildChannel) -> str | None:
    """Canales del propio Heraldo que nunca deben ser una trampa."""
    if channel.id == get_log_channel_id(channel.guild.id):
        return "es el canal de logs del Heraldo"
    if channel.id == get_motw_channel_id(channel.guild.id):
        return "es el canal del Miembro de la Semana"
    if channel.id == get_recovery_channel_id(channel.guild.id):
        return "es el canal de recuperación"
    ref = guild_config_get(channel.guild.id, "verify_panel_ref")
    if ref is None and legacy_fallback_allowed(channel.guild.id):
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


def hp_purge_spec(guild_id: int) -> tuple[str, int]:
    """(tipo, valor): none | all | count (N mensajes) | time (minutos hacia atrás)."""
    v = hp_setting_get(guild_id, "honeypot_purge_spec")
    if v:
        kind, _, val = v.partition(":")
        return kind, int(val or 0)
    old = hp_setting_get(guild_id, "honeypot_purge_minutes")  # compatibilidad con versiones anteriores
    if old is not None:
        return ("time", int(old)) if int(old) > 0 else ("none", 0)
    old = hp_setting_get(guild_id, "honeypot_purge_hours")
    if old is not None:
        return ("time", int(old) * 60) if int(old) > 0 else ("none", 0)
    return HONEYPOT_PURGE_DEFAULT


def hp_timeout_minutes(guild_id: int) -> int:
    v = hp_setting_get(guild_id, "honeypot_timeout_minutes")
    if v is not None:
        return int(v)
    old = hp_setting_get(guild_id, "honeypot_timeout_hours")
    return int(old) * 60 if old is not None else HONEYPOT_TIMEOUT_MINUTES_DEFAULT


def hp_warning_enabled(guild_id: int) -> bool:
    return hp_setting_get(guild_id, "honeypot_warning_enabled") != "0"  # activado por defecto


def hp_warning_style(guild_id: int) -> str:
    value = hp_setting_get(guild_id, "honeypot_warning_style")
    return value if value in ("text", "custom") else "text"


def hp_warning_text(guild_id: int) -> str:
    return hp_setting_get(guild_id, "honeypot_warning_text") or HONEYPOT_WARNING_TEXT_DEFAULT


def hp_warning_custom(guild_id: int) -> dict[str, str]:
    return {
        "title": hp_setting_get(guild_id, "honeypot_warning_title") or "⚠️ No escribas en este canal",
        "description": hp_setting_get(guild_id, "honeypot_warning_description") or HONEYPOT_WARNING_TEXT_DEFAULT,
        "color": hp_setting_get(guild_id, "honeypot_warning_color") or "F1C40F",
        "image": hp_setting_get(guild_id, "honeypot_warning_image") or "",
        "thumbnail": hp_setting_get(guild_id, "honeypot_warning_thumbnail") or "",
        "footer": hp_setting_get(guild_id, "honeypot_warning_footer") or "",
    }


def hp_ping_role_id(guild_id: int) -> int:
    v = hp_setting_get(guild_id, "honeypot_ping_role")
    return int(v) if v else 0


def hp_is_exempt(member: discord.Member) -> bool:
    """Dueño, administradores y quien tenga Gestionar servidor siempre están exentos."""
    if member.guild.owner_id == member.id:
        return True
    perms = member.guild_permissions
    if (perms.administrator or perms.manage_guild or perms.manage_messages
            or perms.kick_members or perms.ban_members or perms.moderate_members):
        return True  # el equipo de moderación nunca cae en la trampa
    if member.id in hp_exempt_ids(member.guild.id, "member"):
        return True
    exempt_roles = hp_exempt_ids(member.guild.id, "role")
    return any(r.id in exempt_roles for r in member.roles)


def hp_config_summary(guild: discord.Guild) -> str:
    traps = hp_traps(guild.id)
    trap_text = ", ".join(f"<#{cid}>" for cid in traps) or "—"
    ping = f"<@&{hp_ping_role_id(guild.id)}>" if hp_ping_role_id(guild.id) else "—"
    estado = "✅ Activado" if honeypot_enabled(guild.id) else "❌ Desactivado"
    if honeypot_paused(guild.id):
        estado += " · ⏸️ **PAUSADO** por protección contra fallos (`/honeypot resume`)"
    lines = [
        f"**Estado:** {estado}",
        f"**Canales trampa:** {trap_text}",
        f"**Acción:** {HONEYPOT_ACTION_LABELS.get(hp_action(guild.id), hp_action(guild.id))}",
        f"**Rol de castigo:** {f'<@&{hp_punish_role_id(guild.id)}>' if hp_punish_role_id(guild.id) else '—'}",
        f"**Purga al castigado:** {format_purge_spec(*hp_purge_spec(guild.id))}",
        f"**Duración del timeout:** {format_duration(hp_timeout_minutes(guild.id))}",
        f"**Aviso fijado:** {'sí' if hp_warning_enabled(guild.id) else 'no'}"
        + (" (texto personalizado)" if hp_setting_get(guild.id, "honeypot_warning_text") else " (texto por defecto)"),
        f"**Rol a mencionar en reportes:** {ping}",
        f"**Roles exentos:** {', '.join(f'<@&{i}>' for i in hp_exempt_ids(guild.id, 'role')) or '—'}",
        f"**Miembros exentos:** {', '.join(f'<@{i}>' for i in hp_exempt_ids(guild.id, 'member')) or '—'}",
        f"**Capturas en el historial:** {hp_total_triggers(guild.id)} (se guardan {format_duration(hp_retention_minutes(guild.id))})",
    ]
    return "\n".join(lines)


# --- Aviso fijado -----------------------------------------------------------

def hp_warning_embed(channel: discord.abc.GuildChannel | None = None) -> discord.Embed:
    guild_id = channel.guild.id if channel is not None else 0
    ctx = VarContext(channel.guild if channel is not None else None, None, channel)
    if hp_warning_style(guild_id) == "custom":
        cfg = hp_warning_custom(guild_id)
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
        description=render_vars(hp_warning_text(guild_id), ctx, 4096),
        color=discord.Color.gold(),
    )


async def hp_sync_warning(channel: discord.TextChannel) -> str | None:
    """Publica/actualiza (o borra) el aviso fijado de un canal trampa. Devuelve un
    texto de error o None si todo fue bien."""
    msg_id = hp_traps(channel.guild.id).get(channel.id)
    existing: discord.Message | None = None
    if msg_id:
        try:
            existing = await channel.fetch_message(msg_id)
        except discord.NotFound:
            existing = None
        except discord.HTTPException as e:
            return f"{channel.mention}: no pude leer el aviso (`{e}`)"

    try:
        if not hp_warning_enabled(channel.guild.id):
            if existing:
                await existing.delete()
            hp_set_warning_message(channel.guild.id, channel.id, None)
            return None
        if existing:
            await existing.edit(embed=hp_warning_embed(channel))
            if not existing.pinned:
                await existing.pin()
            return None
        message = await channel.send(embed=hp_warning_embed(channel))
        await message.pin()
        hp_set_warning_message(channel.guild.id, channel.id, message.id)
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
    for channel_id in list(hp_traps(guild.id)):
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
    title: str = "Purga completada",
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
    kind, value = hp_purge_spec(member.guild.id)
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
_pardon_inflight: set[int] = set()


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



async def condemnation_fetch_source_message(
    guild: discord.Guild, source_message_url: str | None,
) -> discord.Message | None:
    if not source_message_url:
        return None
    match = re.search(r"discord(?:app)?\.com/channels/(\d+)/(\d+)/(\d+)", source_message_url)
    if not match or int(match.group(1)) != guild.id:
        return None
    channel = guild.get_channel_or_thread(int(match.group(2)))
    if channel is None or not hasattr(channel, "fetch_message"):
        return None
    try:
        return await channel.fetch_message(int(match.group(3)))
    except (discord.NotFound, discord.Forbidden, discord.HTTPException):
        return None


async def condemnation_archive_evidence(
    guild: discord.Guild,
    member: discord.Member,
    *,
    source_message_url: str | None,
    reason: str,
    applied_by: discord.abc.User | None,
) -> tuple[str | None, str | None]:
    """Preserva la prueba antes de cualquier purga.

    La URL del mensaje original se conserva solo como referencia. La evidencia real
    es una copia del texto y, cuando Discord lo permite, de los adjuntos re-subidos
    por El Heraldo a Logs (o al canal de condenas como respaldo).
    """
    message = await condemnation_fetch_source_message(guild, source_message_url)
    if message is None:
        return None, None

    archive_channel = guild.get_channel(get_log_channel_id(guild.id))
    if not isinstance(archive_channel, discord.TextChannel):
        archive_channel = guild.get_channel(condemnation_channel_id(guild.id))
    if not isinstance(archive_channel, discord.TextChannel):
        return None, (message.content or "(sin texto)")[:2000]

    me = guild.me
    if me is None:
        return None, (message.content or "(sin texto)")[:2000]
    perms = archive_channel.permissions_for(me)
    if not (perms.view_channel and perms.send_messages and perms.embed_links):
        return None, (message.content or "(sin texto)")[:2000]

    snapshot_text = (message.content or "(mensaje sin texto)")[:3500]
    evidence = discord.Embed(
        title="Evidencia archivada · Condena",
        description=snapshot_text,
        color=discord.Color.dark_red(),
        timestamp=message.created_at,
    )
    evidence.add_field(name="Autor original", value=f"{member.mention}\nID: {member.id}", inline=True)
    evidence.add_field(name="Canal original", value=message.channel.mention, inline=True)
    evidence.add_field(
        name="Moderador",
        value=applied_by.mention if applied_by else "El Heraldo",
        inline=True,
    )
    evidence.add_field(name="Motivo", value=reason[:1024], inline=False)
    if source_message_url:
        evidence.add_field(
            name="Referencia original",
            value=f"[Mensaje original]({source_message_url}) · puede dejar de existir tras la purga.",
            inline=False,
        )
    conn = db_connect()
    recent_rows = conn.execute(
        "SELECT channel_id, message_id, content, created_at FROM moderation_message_cache "
        "WHERE guild_id = ? AND user_id = ? AND message_id != ? "
        "ORDER BY created_at DESC LIMIT 8",
        (guild.id, member.id, message.id),
    ).fetchall()
    conn.close()
    if recent_rows:
        context_lines: list[str] = []
        for channel_id, message_id, cached_content, created_at in recent_rows:
            excerpt = (cached_content or "(sin texto)").replace("\n", " ")[:180]
            context_lines.append(f"<#{channel_id}> · {excerpt}")
        evidence.add_field(
            name="Contexto reciente preservado",
            value="\n".join(context_lines)[:1024],
            inline=False,
        )

    evidence.set_footer(text="Copia preservada antes de la purga por El Heraldo")

    files: list[discord.File] = []
    archived_names: list[str] = []
    max_size = int(getattr(guild, "filesize_limit", 8 * 1024 * 1024))
    for attachment in message.attachments[:5]:
        if attachment.size > max_size:
            archived_names.append(f"{attachment.filename} (demasiado grande para re-subir)")
            continue
        try:
            data = await attachment.read(use_cached=True)
            files.append(discord.File(io.BytesIO(data), filename=attachment.filename))
            archived_names.append(attachment.filename)
        except (discord.HTTPException, OSError):
            archived_names.append(f"{attachment.filename} (no se pudo copiar)")

    if archived_names:
        evidence.add_field(
            name="Adjuntos preservados",
            value="\n".join(f"• {name}" for name in archived_names)[:1024],
            inline=False,
        )

    try:
        archived = await archive_channel.send(
            embed=evidence,
            files=files,
            allowed_mentions=discord.AllowedMentions.none(),
        )
        return archived.jump_url, snapshot_text
    except discord.HTTPException:
        return None, snapshot_text


async def condemnation_send_pardon_dm(
    member: discord.Member,
    row: sqlite3.Row,
    pardoned_by: discord.abc.User,
    restored_count: int,
    lost_count: int,
) -> bool:
    condemned_at = datetime.fromisoformat(row["condemned_at"])
    pardoned_at = datetime.now(timezone.utc)
    linked_case = (
        int(row["moderation_case_number"])
        if "moderation_case_number" in row.keys() and row["moderation_case_number"] is not None
        else None
    )
    case_id = condemnation_case_id(member, condemned_at, linked_case)
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
    include_pardon_button: bool = False, evidence_url: str | None = None, evidence_text: str | None = None,
) -> tuple[discord.Embed, discord.ui.View | None]:
    """Construye la MISMA tarjeta que se usa tanto en el canal de castigo como en el DM."""
    when = when or datetime.now(timezone.utc)
    case_id = case_id or condemnation_case_id(member, when)
    source_channel = guild.get_channel(source_channel_id) if source_channel_id else None

    render = lambda value: _condemnation_render_template(
        value, member=member, guild=guild, case_id=case_id, applied_by=applied_by,
        reason=reason, when=when, source_channel=source_channel,
        duration_minutes=duration_minutes, origin=origin, source_message_url=source_message_url,
        evidence_url=evidence_url,
    )

    embed = discord.Embed(
        title=render(condemnation_template_get(guild.id, "title"))[:256],
        description=render(condemnation_template_get(guild.id, "description"))[:4096],
        color=condemnation_template_color(guild.id),
        timestamp=when,
    )
    embed.set_thumbnail(url=member.display_avatar.url)

    def field(label_key: str, value: str, inline: bool = True) -> None:
        embed.add_field(name=condemnation_template_get(guild.id, label_key)[:256], value=value[:1024] or "—", inline=inline)

    field("label_case", f"`{case_id}`", True)
    field("label_user", f"{member.mention}\n`{member}`", True)
    field("label_by", applied_by.mention if applied_by else "🤖 El Heraldo", True)
    field("label_reason", reason, False)
    field("label_when", f"{discord.utils.format_dt(when, 'F')}\n{discord.utils.format_dt(when, 'R')}", True)

    where = source_channel.mention if source_channel else ("Canal del mensaje original" if source_message_url else "No registrado")
    field("label_where", where, True)
    field("label_duration", format_duration(duration_minutes) if duration_minutes else "Indefinida", True)

    role_mentions = []
    for rid in removed_role_ids or []:
        role = guild.get_role(rid)
        if role is not None:
            role_mentions.append(f"`{role.name}`")
    field("label_roles", ", ".join(role_mentions) if role_mentions else "Ninguno (o no asignable)", False)

    if evidence_url:
        value = f"[Abrir evidencia preservada]({evidence_url})"
        if evidence_text:
            value += "\n" + evidence_text[:700]
        field("label_message", value, False)
    elif evidence_text:
        field("label_message", "**Copia de texto preservada:**\n" + evidence_text[:850], False)
    elif source_message_url:
        field(
            "label_message",
            f"[Referencia al mensaje original]({source_message_url}) · no se considera evidencia preservada.",
            False,
        )

    embed.set_footer(text=render(condemnation_template_get(guild.id, "footer"))[:2048])

    button_url = condemnation_template_get(guild.id, "button_url").strip()
    button_label = render(condemnation_template_get(guild.id, "button_label")).strip()[:80]
    valid_button_url = button_url if re.match(r"^https?://", button_url, re.IGNORECASE) else None
    if include_pardon_button:
        view = CondemnationPardonView(
            link_label=button_label or "Ver información del caso",
            link_url=valid_button_url,
        )
    elif valid_button_url:
        view = discord.ui.View(timeout=None)
        view.add_item(
            discord.ui.Button(
                label=button_label or "Ver información del caso",
                style=discord.ButtonStyle.link,
                url=valid_button_url,
            )
        )
    else:
        view = None
    return embed, view


class CondemnationPardonView(discord.ui.View):
    def __init__(self, *, link_label: str | None = None, link_url: str | None = None) -> None:
        super().__init__(timeout=None)
        if link_url:
            self.add_item(
                discord.ui.Button(
                    label=(link_label or "Ver información del caso")[:80],
                    style=discord.ButtonStyle.link,
                    url=link_url,
                )
            )
        pardon_button = discord.ui.Button(
            label="Perdonar",
            style=discord.ButtonStyle.success,
            custom_id="heraldo:condemnation:pardon",
        )
        pardon_button.callback = self.pardon_callback
        self.add_item(pardon_button)

    async def pardon_callback(
        self,
        interaction: discord.Interaction,
    ) -> None:
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

            row = condemnation_get(member.guild.id, member.id)
            if row is None:
                await interaction.followup.send(
                    "ℹ️ Este expediente ya no tiene una condena activa o ya fue resuelto.",
                    ephemeral=True,
                )
                return

            if member.id in _pardon_inflight:
                await interaction.followup.send(
                    "⏳ Este perdón ya se está procesando.",
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

            _pardon_inflight.add(member.id)
            try:
                ok, note = await release_condemned_member(
                    member,
                    released_by=interaction.user,
                    pardon=True,
                    announcement_message=interaction.message,
                )
            finally:
                _pardon_inflight.discard(member.id)

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
    evidence_url: str | None = None, evidence_text: str | None = None,
) -> bool:
    """Envía por DM la misma tarjeta de condena, incluido el botón configurable."""
    embed, view = _build_condemnation_embed(
        member.guild, member, reason, duration_minutes, origin, applied_by,
        source_message_url=source_message_url, source_channel_id=source_channel_id,
        removed_role_ids=removed_role_ids, when=when, case_id=case_id,
        include_pardon_button=False, evidence_url=evidence_url, evidence_text=evidence_text,
    )
    try:
        await member.send(embed=embed, view=view)
        return True
    except discord.HTTPException:
        return False


def condemnation_template_get(guild_id: int, key: str) -> str:
    value = guild_config_get(guild_id, f"condemnation_template_{key}")
    if value is not None:
        return value
    if legacy_fallback_allowed(guild_id):
        legacy = db_meta_get(f"condemnation_template_{key}")
        if legacy is not None:
            return legacy
    return CONDEMNATION_TEMPLATE_DEFAULTS[key]


def condemnation_template_set(guild_id: int, key: str, value: str) -> None:
    guild_config_set(guild_id, f"condemnation_template_{key}", value[:1024])


def condemnation_template_reset(guild_id: int) -> None:
    conn = db_connect()
    for key in CONDEMNATION_TEMPLATE_DEFAULTS:
        conn.execute(
            "DELETE FROM guild_settings WHERE guild_id = ? AND key = ?",
            (guild_id, f"condemnation_template_{key}"),
        )
    conn.commit()
    conn.close()


def condemnation_template_color(guild_id: int) -> discord.Color:
    raw = condemnation_template_get(guild_id, "color").strip().lstrip("#")
    try:
        value = int(raw, 16)
        if not 0 <= value <= 0xFFFFFF:
            raise ValueError
        return discord.Color(value)
    except ValueError:
        return discord.Color.dark_red()


def condemnation_case_id(
    member: discord.Member, when: datetime, moderation_case_number: int | None = None,
) -> str:
    # Las condenas nuevas usan el mismo identificador único que Moderation Cases.
    if moderation_case_number is not None:
        return f"C-{moderation_case_number:06d}"
    # Compatibilidad para expedientes antiguos creados antes de Moderation Cases.
    return f"C-{when.astimezone(STREAK_TZ):%Y%m%d}-{member.id % 100000:05d}"


def _condemnation_render_template(text: str, *, member: discord.Member, guild: discord.Guild,
                                  case_id: str, applied_by: discord.abc.User | None,
                                  reason: str, when: datetime, source_channel: discord.abc.GuildChannel | None,
                                  duration_minutes: int | None, origin: str,
                                  source_message_url: str | None, evidence_url: str | None = None) -> str:
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
        "{mensaje}": (
            f"[Abrir evidencia preservada]({evidence_url})"
            if evidence_url
            else f"[Referencia original]({source_message_url})" if source_message_url else "No disponible"
        ),
    }
    for key, value in values.items():
        text = text.replace(key, value)
    return text


async def condemnation_announce(
    guild: discord.Guild, member: discord.Member, reason: str,
    duration_minutes: int | None, origin: str, applied_by: discord.abc.User | None,
    *, source_message_url: str | None = None, source_channel_id: int | None = None,
    removed_role_ids: list[int] | None = None, when: datetime | None = None, case_id: str | None = None,
    evidence_url: str | None = None, evidence_text: str | None = None,
) -> int | None:
    channel = guild.get_channel(condemnation_channel_id(guild.id))
    if not isinstance(channel, discord.TextChannel):
        return None
    embed, view = _build_condemnation_embed(
        guild, member, reason, duration_minutes, origin, applied_by,
        source_message_url=source_message_url, source_channel_id=source_channel_id,
        removed_role_ids=removed_role_ids, when=when, case_id=case_id,
        include_pardon_button=True, evidence_url=evidence_url, evidence_text=evidence_text,
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
    """Crea la tarjeta nueva de perdón y elimina la tarjeta original del caso."""
    message_id = row["announcement_message_id"] if "announcement_message_id" in row.keys() else None
    channel = member.guild.get_channel(condemnation_channel_id(member.guild.id))
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
        linked_case = (
            int(row["moderation_case_number"])
            if "moderation_case_number" in row.keys() and row["moderation_case_number"] is not None
            else None
        )
        case_id = condemnation_case_id(member, condemned_at, linked_case)
        pardoned_at = datetime.now(timezone.utc)

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
        resolution.add_field(name="Duración original", value=condemnation_duration_text(row), inline=True)
        resolution.set_footer(text=f"{member.guild.name} · El Heraldo 🪽 · Resolución {case_id}")

        new_message = await channel.send(
            content=member.mention,
            embed=resolution,
            allowed_mentions=discord.AllowedMentions(users=[member], roles=False, everyone=False),
        )

        old_deleted = False
        try:
            await message.delete()
            old_deleted = True
        except discord.NotFound:
            old_deleted = True
        except discord.Forbidden:
            print(f"⚠️ No pude eliminar la tarjeta original del expediente {case_id}: faltan permisos.")
        except discord.HTTPException as e:
            print(f"⚠️ No pude eliminar la tarjeta original del expediente {case_id}: {e}")

        conn = db_connect()
        conn.execute(
            "UPDATE guild_cases SET announcement_message_id = ? WHERE guild_id = ? AND user_id = ?",
            (new_message.id, member.guild.id, member.id),
        )
        conn.commit()
        conn.close()

        if not old_deleted:
            await log_embed(
                member.guild,
                "⚠️ Tarjeta de condena no eliminada",
                f"Expediente: {case_id}\nNo pude eliminar la tarjeta original. "
                f"La tarjeta de resolución sí fue creada: {new_message.jump_url}",
                discord.Color.orange(),
            )
        return True
    except (discord.NotFound, discord.Forbidden, discord.HTTPException):
        traceback.print_exc()
        return False


def condemnation_role_id(row: sqlite3.Row | None = None, guild_id: int | None = None) -> int:
    if row is not None and row["role_id"]:
        return int(row["role_id"])
    if guild_id is None and row is not None and "guild_id" in row.keys():
        guild_id = int(row["guild_id"])
    return hp_punish_role_id(guild_id) if guild_id is not None else 0


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
    punish_role = guild.get_role(role_id or hp_punish_role_id(guild.id))
    if punish_role is None:
        return False, [], "No hay rol Condenado configurado; usa `/honeypot setup rol_castigo` para elegirlo."
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
        hp_save_punished(member.guild.id, member.id, saved_ids)
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
            "raid": "Protección RAID: ingreso detectado durante un patrón de incursión masiva.",
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
    existing = condemnation_get(member.guild.id, member.id)
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

    db_clear_tentado(member.guild.id, member.id)
    db_clear_sin_verificado(member.guild.id, member.id)
    db_clear_verify_pending(member.guild.id, member.id)
    db_zero_week_messages(member.guild.id, member.id)

    evidence_url, evidence_text = await condemnation_archive_evidence(
        member.guild,
        member,
        source_message_url=source_message_url,
        reason=reason,
        applied_by=applied_by,
    )

    # Ambos destinos reciben la misma resolución y el mismo Moderation Case.
    condemnation_when = datetime.now(timezone.utc)
    linked_case_number: int | None = None
    if send_dm or announce:
        try:
            verified = evidence_text or await moderation_verified_proof(member.guild, source_message_url)
            linked_case_number = moderation_case_create(
                member.guild.id, "CONDEMN", member.id, reason,
                duration_minutes=duration_minutes,
                author_id=applied_by.id if applied_by else None,
                proof=evidence_url or source_message_url,
                verified_proof=verified,
            )
            conn = db_connect()
            conn.execute(
                "UPDATE guild_cases SET moderation_case_number = ? WHERE guild_id = ? AND user_id = ?",
                (linked_case_number, member.guild.id, member.id),
            )
            conn.close()
        except Exception:
            traceback.print_exc()
    elif existing is not None and "moderation_case_number" in existing.keys() and existing["moderation_case_number"]:
        linked_case_number = int(existing["moderation_case_number"])

    condemnation_case = condemnation_case_id(member, condemnation_when, linked_case_number)
    dm_ok = await condemnation_send_dm(
        member, reason, duration_minutes, origin, applied_by,
        source_message_url=source_message_url, source_channel_id=source_channel_id,
        removed_role_ids=removed_role_ids, when=condemnation_when, case_id=condemnation_case,
        evidence_url=evidence_url, evidence_text=evidence_text,
    ) if send_dm else None
    if announce:
        announcement_message_id = await condemnation_announce(
            member.guild, member, reason, duration_minutes, origin, applied_by,
            source_message_url=source_message_url, source_channel_id=source_channel_id,
            removed_role_ids=removed_role_ids, when=condemnation_when, case_id=condemnation_case,
            evidence_url=evidence_url, evidence_text=evidence_text,
        )
        if announcement_message_id:
            conn = db_connect()
            conn.execute(
                "UPDATE guild_cases SET announcement_message_id = ? WHERE guild_id = ? AND user_id = ?",
                (announcement_message_id, member.guild.id, member.id),
            )
            conn.close()
    if purge_spec and purge_spec[0] != "none":
        kind, value = purge_spec
        after = datetime.now(timezone.utc) - timedelta(minutes=value) if kind == "time" else None
        limit = value if kind == "count" else None
        asyncio.create_task(
            run_purge_job(
                member.guild,
                member,
                scope_text=format_purge_spec(kind, value),
                requested_by=f"Condena ({condemnation_origin_label(origin)})",
                after=after,
                limit=limit,
                title="Purga de condena completada",
            )
        )

    # La tarjeta del canal de condenas ya es el aviso principal. Si Logs apunta
    # al mismo canal, no dupliques el mismo evento con un segundo embed.
    if get_log_channel_id(member.guild.id) != condemnation_channel_id(member.guild.id):
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
    row = condemnation_get(member.guild.id, member.id)
    punish_role = member.guild.get_role(condemnation_role_id(row))
    if row is None and not (punish_role and punish_role in member.roles):
        return False, "Ese miembro no tiene una condena activa."

    saved = condemnation_parse_role_ids(row["role_ids"]) if row else (hp_get_punished(member.guild.id, member.id) or [])
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

    linked_case_number = (
        int(row["moderation_case_number"])
        if row is not None and "moderation_case_number" in row.keys() and row["moderation_case_number"] is not None
        else None
    )
    if pardon and row is not None and released_by is not None:
        condemnation_deactivate(member.guild.id, member.id, resolution="pardoned", resolved_by=released_by.id)
        if linked_case_number is not None:
            moderation_case_close(
                member.guild.id, linked_case_number,
                closed_by=released_by.id, resolution="Perdonado",
            )
    else:
        condemnation_deactivate(member.guild.id, member.id, resolution="expired" if automatic else None)
        if automatic and linked_case_number is not None:
            moderation_case_close(
                member.guild.id, linked_case_number,
                closed_by=None, resolution="Expirado automáticamente",
            )
    db_clear_tentado(member.guild.id, member.id)
    db_clear_sin_verificado(member.guild.id, member.id)
    db_clear_verify_pending(member.guild.id, member.id)

    # Si entre los roles originales estaban los de verificación, vuelven a su flujo normal
    # desde cero; mientras la condena estuvo activa nunca corrió ninguna evaluación.
    restored_ids = {r.id for r in restore}
    if get_tentado_role_id(member.guild.id) in restored_ids:
        now = datetime.now(timezone.utc)
        db_set_tentado(member.guild.id, member.id, now)
        asyncio.create_task(schedule_check(member.guild.id, member.id, now))
    if get_sin_verificado_role_id(member.guild.id) in restored_ids:
        now = datetime.now(timezone.utc)
        db_set_sin_verificado(member.guild.id, member.id, now)
        asyncio.create_task(schedule_sin_verificado_check(member.guild.id, member.id, now))

    text = f"{len(restore)} rol(es) restaurado(s)" + (f"; {lost} no se pudieron restaurar" if lost else "")
    if pardon and row is not None and released_by is not None:
        condemned_at = datetime.fromisoformat(row["condemned_at"])
        case_id = condemnation_case_id(member, condemned_at, linked_case_number)
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
    conn = db_connect()
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT * FROM guild_cases WHERE active = 1 AND expires_at IS NOT NULL AND expires_at <= ?",
        (now.isoformat(),),
    ).fetchall()
    conn.close()
    for row in rows:
        guild_id = int(row["guild_id"])
        user_id = int(row["user_id"])
        guild = bot.get_guild(guild_id)
        if guild is None:
            condemnation_deactivate(guild_id, user_id, resolution="expired")
            linked_case = (
                int(row["moderation_case_number"])
                if "moderation_case_number" in row.keys() and row["moderation_case_number"] is not None
                else None
            )
            if linked_case is not None:
                moderation_case_close(
                    guild_id, linked_case, closed_by=None, resolution="Expirado automáticamente"
                )
            continue
        member = guild.get_member(user_id)
        if member is not None:
            await release_condemned_member(member, automatic=True)
        else:
            condemnation_deactivate(guild_id, user_id, resolution="expired")
            linked_case = (
                int(row["moderation_case_number"])
                if "moderation_case_number" in row.keys() and row["moderation_case_number"] is not None
                else None
            )
            if linked_case is not None:
                moderation_case_close(
                    guild_id, linked_case, closed_by=None, resolution="Expirado automáticamente"
                )


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

    punish_role = guild.get_role(hp_punish_role_id(guild.id))
    if punish_role is None:
        return
    for member in list(punish_role.members):
        if member.bot or condemnation_get(member.guild.id, member.id) is not None:
            continue
        await condemn_member(
            member, reason="El rol Condenado fue otorgado manualmente (detectado al arrancar).",
            duration_minutes=condemnation_default_duration_minutes(guild.id), purge_spec=None, origin="role", applied_by=None,
            send_dm=True, announce=True,
        )
        await asyncio.sleep(1)


@tasks.loop(minutes=1)
async def moderation_case_expiry_loop() -> None:
    now = datetime.now(timezone.utc)
    conn = db_connect()
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM moderation_cases WHERE open = 1 AND expires_at IS NOT NULL").fetchall()
    conn.close()
    for row in rows:
        try:
            expires = datetime.fromisoformat(row["expires_at"])
            guild = bot.get_guild(int(row["guild_id"]))
            if guild is None:
                continue
            member = guild.get_member(int(row["user_id"]))
            case_type = str(row["type"])
            if case_type == "MUTE" and member is not None and expires > now + timedelta(days=27):
                current = member.timed_out_until
                if current is None or current < now + timedelta(days=27):
                    await member.timeout(min(expires, now + timedelta(days=28)), reason=f"Extensión del caso #{row['case_number']}")
            if expires > now:
                continue
            if case_type == "MUTE" and member is not None:
                try:
                    await member.timeout(None, reason=f"Expiró caso #{row['case_number']}")
                except discord.HTTPException:
                    pass
            elif case_type == "BAN":
                try:
                    await guild.unban(discord.Object(id=int(row["user_id"])), reason=f"Expiró caso #{row['case_number']}")
                except (discord.NotFound, discord.HTTPException):
                    pass
            moderation_case_close(guild.id, int(row["case_number"]), closed_by=None, resolution="Expirado automáticamente")
        except Exception:
            traceback.print_exc()

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
            minutes = hp_timeout_minutes(member.guild.id)
            await member.timeout(timedelta(minutes=minutes), reason=reason)
            purge_note = hp_start_purge(member)
            return True, f"Aislado {format_duration(minutes)}" + (f"; {purge_note}" if purge_note else "")
        if action == "role":
            purge_spec = hp_purge_spec(member.guild.id)
            return await condemn_member(
                member,
                reason="Honeypot: escribió en un canal trampa",
                duration_minutes=condemnation_default_duration_minutes(member.guild.id),
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
    log_channel = guild.get_channel(get_log_channel_id(guild.id))
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
    role_id = hp_ping_role_id(guild.id)
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
    action = hp_action(guild.id)

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
        hp_setting_set(guild.id, "honeypot_paused", "1")
        _hp_veteran_hits.clear()
        await log_embed(
            guild, "⏸️ Honeypot pausado (protección contra fallos)",
            f"{HONEYPOT_MISFIRE_THRESHOLD}+ miembros con más de 30 días en el servidor escribieron en la trampa en "
            f"pocos minutos: probablemente apunta a un canal que tu comunidad usa de verdad.\n"
            f"Revisa los canales trampa con `/honeypot setup` y reactiva con `/honeypot resume`. "
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
    if not honeypot_enabled(message.guild.id) or honeypot_paused(message.guild.id):
        return
    if message.channel.id not in hp_trap_ids(message.guild.id):
        return
    member = message.author
    if not isinstance(member, discord.Member) or hp_is_exempt(member):
        return
    punish_id = hp_punish_role_id(message.guild.id)
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
    if channel.id not in hp_traps(channel.guild.id):
        return
    hp_remove_trap(channel.guild.id, channel.id)
    await log_embed(
        channel.guild, "🍯 Canal trampa eliminado",
        f"Se borró `#{channel.name}` en Discord y se quitó del honeypot automáticamente. "
        f"Quedan {len(hp_traps(channel.guild.id))} canal(es) trampa.",
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
    duration_minutes: int | None = condemnation_default_duration_minutes(guild.id)
    try:
        if duracion is not None:
            raw_duration = duracion.strip()
            if raw_duration.lower() in {"0", "indefinida", "indefinido", "permanente", "hasta retirar"}:
                duration_minutes = None
            else:
                duration_minutes = parse_duration(raw_duration, 1, get_condemnation_max_minutes(guild.id))
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


@bot.tree.command(name="condenar_setup", description="Configurar el canal donde se anuncian las nuevas condenas.")
@discord.app_commands.describe(canal="Canal de texto para los avisos de condena; vacío = ver configuración")
@discord.app_commands.checks.has_permissions(manage_guild=True)
@discord.app_commands.guild_only()
async def condenar_config(interaction: discord.Interaction, canal: Optional[discord.TextChannel] = None) -> None:
    if canal is None:
        current = interaction.guild.get_channel(condemnation_channel_id(interaction.guild.id))
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
    set_condemnation_channel_id(canal.id, interaction.guild.id)
    guild_resource_set(interaction.guild.id, "channel", "condemned", canal.id)
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

    def __init__(self, guild_id: int, return_to: str = "setup") -> None:
        super().__init__()
        self.guild_id = guild_id
        self.return_to = return_to
        self.title_input.default = condemnation_template_get(guild_id, "title")
        self.description_input.default = condemnation_template_get(self.guild_id, "description")
        self.color_input.default = condemnation_template_get(self.guild_id, "color")
        self.footer_input.default = condemnation_template_get(self.guild_id, "footer")
        self.button_label_input.default = condemnation_template_get(self.guild_id, "button_label")

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
        condemnation_template_set(interaction.guild.id, "title", str(self.title_input).strip())
        condemnation_template_set(interaction.guild.id, "description", str(self.description_input).strip())
        condemnation_template_set(interaction.guild.id, "color", color or CONDEMNATION_TEMPLATE_DEFAULTS["color"])
        condemnation_template_set(interaction.guild.id, "footer", str(self.footer_input).strip())
        condemnation_template_set(
            interaction.guild.id, "button_label",
            str(self.button_label_input).strip() or CONDEMNATION_TEMPLATE_DEFAULTS["button_label"],
        )
        await condemnation_template_editor_update(interaction, "Diseño actualizado.", self.return_to)


class CondemnationDetailsModal(discord.ui.Modal, title="Condenados · Etiquetas"):
    case_input = discord.ui.TextInput(label="Expediente", required=True, max_length=256)
    user_input = discord.ui.TextInput(label="Condenado", required=True, max_length=256)
    by_input = discord.ui.TextInput(label="Quién condenó", required=True, max_length=256)
    reason_input = discord.ui.TextInput(label="Motivo", required=True, max_length=256)
    when_input = discord.ui.TextInput(label="Cuándo", required=True, max_length=256)

    def __init__(self, guild_id: int, return_to: str = "setup") -> None:
        super().__init__()
        self.guild_id = guild_id
        self.return_to = return_to
        self.case_input.default = condemnation_template_get(guild_id, "label_case")
        self.user_input.default = condemnation_template_get(self.guild_id, "label_user")
        self.by_input.default = condemnation_template_get(self.guild_id, "label_by")
        self.reason_input.default = condemnation_template_get(self.guild_id, "label_reason")
        self.when_input.default = condemnation_template_get(self.guild_id, "label_when")

    async def on_submit(self, interaction: discord.Interaction) -> None:
        values = (
            ("label_case", self.case_input.value),
            ("label_user", self.user_input.value),
            ("label_by", self.by_input.value),
            ("label_reason", self.reason_input.value),
            ("label_when", self.when_input.value),
        )
        for key, value in values:
            condemnation_template_set(interaction.guild.id, key, value.strip())
        await condemnation_template_editor_update(interaction, "Etiquetas principales actualizadas.", self.return_to)


class CondemnationDurationModal(discord.ui.Modal, title="Condenados · Duración"):
    duration_input = discord.ui.TextInput(
        label="Duración predeterminada",
        required=True,
        max_length=32,
        placeholder="Indefinida, 30m, 12h, 7d…",
    )

    def __init__(self, guild_id: int, return_to: str = "setup") -> None:
        super().__init__()
        self.guild_id = guild_id
        self.return_to = return_to
        current = condemnation_default_duration_minutes(guild_id)
        self.duration_input.default = format_duration(current) if current else "Indefinida"

    async def on_submit(self, interaction: discord.Interaction) -> None:
        value = str(self.duration_input).strip()
        if value.lower() in {"indefinida", "indefinido", "permanente", "hasta retirar", "0"}:
            set_condemnation_default_duration(None, interaction.guild.id)
            await condemnation_template_editor_update(interaction, "Duración predeterminada: **Indefinida (hasta retirar)**.", self.return_to)
            return
        try:
            minutes = parse_duration(value, 1, CONDEMNATION_MAX_MINUTES)
        except ValueError as e:
            await interaction.response.send_message(f"❌ {e}", ephemeral=True)
            return
        set_condemnation_default_duration(value, interaction.guild.id)
        await condemnation_template_editor_update(interaction, f"Duración predeterminada: **{format_duration(minutes)}**.", self.return_to)


class CondemnationMoreDetailsModal(discord.ui.Modal, title="Condenados · Más etiquetas"):
    where_input = discord.ui.TextInput(label="Dónde ocurrió", required=True, max_length=256)
    duration_input = discord.ui.TextInput(label="Duración", required=True, max_length=256)
    origin_input = discord.ui.TextInput(label="Origen", required=True, max_length=256)
    roles_input = discord.ui.TextInput(label="Roles retirados", required=True, max_length=256)
    evidence_input = discord.ui.TextInput(label="Evidencia / mensaje", required=True, max_length=256)

    def __init__(self, guild_id: int, return_to: str = "setup") -> None:
        super().__init__()
        self.guild_id = guild_id
        self.return_to = return_to
        self.where_input.default = condemnation_template_get(self.guild_id, "label_where")
        self.duration_input.default = condemnation_template_get(self.guild_id, "label_duration")
        self.origin_input.default = condemnation_template_get(self.guild_id, "label_origin")
        self.roles_input.default = condemnation_template_get(self.guild_id, "label_roles")
        self.evidence_input.default = condemnation_template_get(self.guild_id, "label_message")

    async def on_submit(self, interaction: discord.Interaction) -> None:
        values = (
            ("label_where", self.where_input.value),
            ("label_duration", self.duration_input.value),
            ("label_origin", self.origin_input.value),
            ("label_roles", self.roles_input.value),
            ("label_message", self.evidence_input.value),
        )
        for key, value in values:
            condemnation_template_set(interaction.guild.id, key, value.strip())
        await condemnation_template_editor_update(interaction, "Más etiquetas actualizadas.", self.return_to)


class CondemnationButtonUrlModal(discord.ui.Modal, title="Condenados · Enlace"):
    url_input = discord.ui.TextInput(
        label="URL del botón",
        required=False,
        max_length=2000,
        placeholder="https://…",
    )

    def __init__(self, guild_id: int, return_to: str = "setup") -> None:
        super().__init__()
        self.guild_id = guild_id
        self.return_to = return_to
        self.url_input.default = condemnation_template_get(guild_id, "button_url")

    async def on_submit(self, interaction: discord.Interaction) -> None:
        url = str(self.url_input).strip()
        if url and not re.match(r"^https?://", url, re.IGNORECASE):
            await interaction.response.send_message(
                "❌ La URL debe comenzar por https:// o http://.",
                ephemeral=True,
            )
            return
        condemnation_template_set(interaction.guild.id, "button_url", url)
        await condemnation_template_editor_update(interaction, "Enlace del botón actualizado.", self.return_to)


def condemnation_template_preview(guild: discord.Guild, member: discord.Member) -> discord.Embed:
    # La vista previa no usa los roles reales del administrador que abrió el editor.
    # En una condena real sí se muestran únicamente los roles que fueron retirados al condenado.
    embed, _ = _build_condemnation_embed(
        guild,
        member,
        "Ejemplo de vista previa — motivo de la condena.",
        60,
        "role",
        member,
        removed_role_ids=[],
        when=datetime.now(timezone.utc),
    )
    return embed


async def condemnation_template_editor_update(
    interaction: discord.Interaction,
    notice: str | None = None,
    return_to: str = "setup",
) -> None:
    guild = interaction.guild
    if guild is None:
        await interaction.response.send_message(
            "❌ Este editor solo funciona dentro de un servidor.",
            ephemeral=True,
        )
        return

    if return_to == "studio_messages" or return_to.startswith("studio:"):
        studio_return_to = (
            return_to.split(":", 1)[1]
            if return_to.startswith("studio:")
            else "messages_command"
        )
        if studio_return_to not in {"messages_command", "messages_setup"}:
            studio_return_to = "messages_command"
        await open_default_message_studio(
            interaction,
            "condemnation",
            interaction.user.id,
            studio_return_to,
            notice=notice,
        )
        return

    embed = condemnation_template_preview(guild, interaction.user)
    view = CondemnationTemplateEditorView(interaction.user.id, return_to=return_to)
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
    def __init__(self, owner_id: int, return_to: str = "setup") -> None:
        super().__init__(timeout=900)
        self.owner_id = owner_id
        self.return_to = return_to

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message(
                "Este editor no es tuyo. Usa /condenar template para abrir el tuyo.",
                ephemeral=True,
            )
            return False
        return True

    @discord.ui.button(label="Diseño", style=discord.ButtonStyle.primary, row=0)
    async def edit_core(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await interaction.response.send_modal(CondemnationCoreModal(interaction.guild.id, self.return_to))

    @discord.ui.button(label="Etiquetas", style=discord.ButtonStyle.primary, row=0)
    async def edit_details(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await interaction.response.send_modal(CondemnationDetailsModal(interaction.guild.id, self.return_to))

    @discord.ui.button(label="Más etiquetas", style=discord.ButtonStyle.primary, row=0)
    async def edit_more_details(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await interaction.response.send_modal(CondemnationMoreDetailsModal(interaction.guild.id, self.return_to))

    @discord.ui.button(label="Enlace del botón", style=discord.ButtonStyle.secondary, row=1)
    async def edit_button_url(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await interaction.response.send_modal(CondemnationButtonUrlModal(interaction.guild.id, self.return_to))

    @discord.ui.button(label="Duración", style=discord.ButtonStyle.secondary, row=1)
    async def edit_duration(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await interaction.response.send_modal(CondemnationDurationModal(interaction.guild.id, self.return_to))

    @discord.ui.button(label="Vista previa", style=discord.ButtonStyle.secondary, row=1)
    async def preview(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if interaction.guild is None:
            await interaction.response.send_message("❌ Solo disponible en un servidor.", ephemeral=True)
            return
        await interaction.response.send_message(
            "👁️ **Vista previa actual de la tarjeta de condenados:**",
            embed=condemnation_template_preview(interaction.guild, interaction.user),
            ephemeral=True,
        )

    @discord.ui.button(label="Restaurar valores", style=discord.ButtonStyle.danger, row=1)
    async def reset(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        condemnation_template_reset(interaction.guild.id)
        await condemnation_template_editor_update(
            interaction,
            "La plantilla de condenados volvió a sus valores predeterminados.",
            self.return_to,
        )


    @discord.ui.button(label="Volver", style=discord.ButtonStyle.secondary, row=2)
    async def back_to_heraldo(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if self.return_to == "messages_command":
            await interaction.response.edit_message(
                content=heraldo_messages_command_content(),
                embed=None,
                view=HeraldoMessagesView(interaction.guild.id, self.owner_id),
            )
            return
        if self.return_to == "messages_setup":
            await interaction.response.edit_message(
                content=heraldo_messages_setup_content(),
                embed=None,
                view=HeraldoMessagesSetupView(interaction.guild.id, self.owner_id),
            )
            return
        await heraldo_setup_go_home(interaction, interaction.guild.id, self.owner_id)


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
        view=CondemnationTemplateEditorView(interaction.user.id, return_to="setup"),
        ephemeral=True,
    )


@bot.listen("on_raw_reaction_add")
async def moderation_reaction_add(payload: discord.RawReactionActionEvent) -> None:
    if payload.guild_id is None or payload.user_id == getattr(bot.user, "id", None):
        return

    guild = bot.get_guild(payload.guild_id)
    if guild is None:
        return
    actor = payload.member or guild.get_member(payload.user_id)
    if actor is None:
        try:
            actor = await guild.fetch_member(payload.user_id)
        except discord.HTTPException:
            return
    if actor.bot:
        return

    emoji = str(payload.emoji)
    condemn_emoji = get_condemnation_emoji(guild.id)
    is_condemn = _moderation_emoji_key(emoji) == _moderation_emoji_key(condemn_emoji)
    report_rule = moderation_report_rule_for_emoji(guild.id, emoji)
    report_type = str(report_rule["label"]) if report_rule else None
    if not is_condemn and report_rule is None:
        return

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

    if is_condemn:
        if not moderation_is_staff(actor) or target.id == actor.id:
            return
        if condemnation_get(guild.id, target.id) is not None:
            return
        pending_key = (guild.id, message.id)
        if pending_key in _reaction_condemn_pending:
            return
        _reaction_condemn_pending.add(pending_key)
        view = ReactionCondemnReasonView(
            guild_id=guild.id,
            actor_id=actor.id,
            channel_id=message.channel.id,
            message_id=message.id,
            target_id=target.id,
            pending_key=pending_key,
        )
        try:
            prompt = await actor.send(
                f"**Condenar por reacción**\n"
                f"Servidor: **{guild.name}**\n"
                f"Miembro: **{target}** (`{target.id}`)\n"
                f"Canal: {message.channel.mention}\n"
                f"[Abrir mensaje]({message.jump_url})\n\n"
                "La razón es obligatoria. Pulsa **Indicar razón** para continuar.",
                view=view,
                allowed_mentions=discord.AllowedMentions.none(),
            )
            view.prompt_message = prompt
        except discord.HTTPException:
            _reaction_condemn_pending.discard(pending_key)
        return

    report_channel = guild.get_channel(moderation_report_channel_id(guild.id))
    if not isinstance(report_channel, discord.TextChannel):
        return

    now = time.monotonic()
    dedupe_key = (guild.id, message.id, actor.id, _moderation_emoji_key(emoji))
    last = _moderation_report_dedupe.get(dedupe_key)
    if last is not None and now - last < 3600:
        return
    _moderation_report_dedupe[dedupe_key] = now
    emoji_key = _moderation_emoji_key(emoji)
    reporter_count, action_executed = moderation_report_record(
        guild.id, message.id, target.id, emoji_key, actor.id
    )
    threshold = int(report_rule.get("threshold", 1)) if report_rule else 1
    if len(_moderation_report_dedupe) > 5000:
        cutoff = now - 3600
        for key, stamp in list(_moderation_report_dedupe.items()):
            if stamp < cutoff:
                _moderation_report_dedupe.pop(key, None)

    embed = discord.Embed(
        title="Reporte de usuario por reacción",
        description=f"**Tipo:** {report_type}",
        color=discord.Color.orange(),
        timestamp=datetime.now(timezone.utc),
    )
    embed.add_field(name="Reportado", value=f"{target.mention}\nID: {target.id}", inline=True)
    embed.add_field(name="Reportó", value=f"{actor.mention}\nID: {actor.id}", inline=True)
    embed.add_field(name="Dónde", value=message.channel.mention, inline=True)
    content = (message.content or "(mensaje sin texto)")[:1500]
    embed.add_field(name="Mensaje", value=content, inline=False)
    if message.attachments:
        attachments = "\n".join(a.url for a in message.attachments[:5])
        embed.add_field(name="Adjuntos", value=attachments[:1024], inline=False)
    embed.add_field(name="Referencia", value=f"[Abrir mensaje]({message.jump_url})", inline=False)
    embed.add_field(name="Reportes distintos", value=f"{reporter_count}/{threshold}", inline=True)
    embed.add_field(
        name="Acción configurada",
        value=moderation_action_label(str(report_rule.get("action", "report"))) if report_rule else "Solo reportar",
        inline=True,
    )
    try:
        await report_channel.send(embed=embed, allowed_mentions=discord.AllowedMentions.none())
    except discord.HTTPException:
        _moderation_report_dedupe.pop(dedupe_key, None)

    if report_rule and reporter_count >= threshold and not action_executed:
        ok, note = await execute_moderation_report_action(guild, target, message, report_rule, reporter_count)
        if ok:
            moderation_report_mark_executed(guild.id, message.id, target.id, emoji_key)
        await log_embed(
            guild,
            "Moderation · Acción automática de reporte" if ok else "Moderation · Acción automática rechazada",
            f"{target.mention} · {report_type}\nReportes: {reporter_count}/{threshold}\nResultado: {note}\n{message.jump_url}",
            discord.Color.green() if ok else discord.Color.orange(),
        )


class ReactionCondemnReasonModal(discord.ui.Modal, title="Condenar por reacción"):
    reason = discord.ui.TextInput(
        label="Razón de la condena",
        style=discord.TextStyle.paragraph,
        required=True,
        min_length=3,
        max_length=1000,
        placeholder="Explica obligatoriamente por qué se aplica la condena.",
    )

    def __init__(self, view: "ReactionCondemnReasonView") -> None:
        super().__init__()
        self.parent_view = view

    async def on_submit(self, interaction: discord.Interaction) -> None:
        view = self.parent_view
        if interaction.user.id != view.actor_id:
            await interaction.response.send_message("Este proceso de condena no te pertenece.")
            return
        guild = bot.get_guild(view.guild_id)
        if guild is None:
            await interaction.response.send_message("Ya no puedo acceder al servidor donde se inició esta condena.")
            _reaction_condemn_pending.discard(view.pending_key)
            return
        actor = guild.get_member(view.actor_id)
        if actor is None or not moderation_is_staff(actor):
            await interaction.response.send_message("Ya no tienes permisos suficientes para aplicar esta condena.")
            _reaction_condemn_pending.discard(view.pending_key)
            return
        channel = guild.get_channel_or_thread(view.channel_id)
        if channel is None or not hasattr(channel, "fetch_message"):
            await interaction.response.send_message("El mensaje original ya no está disponible.")
            _reaction_condemn_pending.discard(view.pending_key)
            return
        try:
            message = await channel.fetch_message(view.message_id)
        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            await interaction.response.send_message("El mensaje original ya no está disponible.")
            _reaction_condemn_pending.discard(view.pending_key)
            return
        target = guild.get_member(view.target_id)
        if target is None or target.bot or target.id != message.author.id:
            await interaction.response.send_message("El miembro objetivo ya no está disponible.")
            _reaction_condemn_pending.discard(view.pending_key)
            return
        reason = str(self.reason).strip()
        if not reason:
            await interaction.response.send_message("La razón es obligatoria.")
            return

        await interaction.response.defer(thinking=True)
        ok, note = await condemn_member(
            target,
            reason=reason,
            duration_minutes=condemnation_default_duration_minutes(guild.id),
            purge_spec=HONEYPOT_PURGE_DEFAULT,
            origin="reaction",
            applied_by=actor,
            source_message_url=message.jump_url,
            source_channel_id=message.channel.id,
        )
        _reaction_condemn_pending.discard(view.pending_key)
        if view.prompt_message is not None:
            try:
                await view.prompt_message.edit(
                    content=(
                        f"Condena aplicada a **{target}**. {note}"
                        if ok else f"No pude aplicar la condena: {note}"
                    ),
                    view=None,
                )
            except discord.HTTPException:
                await interaction.followup.send(
                    f"Condena aplicada a **{target}**. {note}"
                    if ok else f"No pude aplicar la condena: {note}"
                )
        else:
            await interaction.followup.send(
                f"Condena aplicada a **{target}**. {note}"
                if ok else f"No pude aplicar la condena: {note}"
            )


class ReactionCondemnReasonView(discord.ui.View):
    def __init__(
        self, *, guild_id: int, actor_id: int, channel_id: int, message_id: int,
        target_id: int, pending_key: tuple[int, int],
    ) -> None:
        super().__init__(timeout=120)
        self.guild_id = guild_id
        self.actor_id = actor_id
        self.channel_id = channel_id
        self.message_id = message_id
        self.target_id = target_id
        self.pending_key = pending_key
        self.prompt_message: discord.Message | None = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.actor_id:
            await interaction.response.send_message("Solo el moderador que inició esta condena puede continuar.")
            return False
        return True

    @discord.ui.button(label="Indicar razón", style=discord.ButtonStyle.danger)
    async def enter_reason(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await interaction.response.send_modal(ReactionCondemnReasonModal(self))

    @discord.ui.button(label="Cancelar", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        _reaction_condemn_pending.discard(self.pending_key)
        await interaction.response.edit_message(content="Condena por reacción cancelada.", view=None)
        self.stop()

    async def on_timeout(self) -> None:
        _reaction_condemn_pending.discard(self.pending_key)
        if self.prompt_message is not None:
            try:
                await self.prompt_message.edit(content="La solicitud de condena por reacción expiró.", view=None)
            except discord.HTTPException:
                pass




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

    def __init__(self, guild_id: int) -> None:
        super().__init__()
        self.guild_id = guild_id
        self.text.default = hp_setting_get(guild_id, "honeypot_warning_text") or HONEYPOT_WARNING_TEXT_DEFAULT

    async def on_submit(self, interaction: discord.Interaction) -> None:
        value = str(self.text).strip()
        if value and value != HONEYPOT_WARNING_TEXT_DEFAULT:
            hp_setting_set(interaction.guild.id, "honeypot_warning_text", value)
        else:
            hp_setting_set(interaction.guild.id, "honeypot_warning_text", "")
        hp_setting_set(interaction.guild.id, "honeypot_warning_style", "text")
        await interaction.response.defer(ephemeral=True)
        errors = await hp_sync_all_warnings(interaction.guild)
        await interaction.followup.send(
            "✅ Aviso actualizado en los canales trampa." + ("\n" + "\n".join(errors) if errors else ""),
            ephemeral=True,
        )


@honeypot_group.command(name="setup", description="Ver o cambiar la configuración del honeypot.")
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
    if activado and not hp_traps(guild.id):
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
    effective_action = accion.value if accion is not None else hp_action(guild.id)
    effective_role_id = rol_castigo.id if rol_castigo is not None else hp_punish_role_id(guild.id)
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
        hp_setting_set(interaction.guild.id, "honeypot_enabled", "1" if activado else "0")
        if activado:
            hp_setting_set(interaction.guild.id, "honeypot_paused", "0")
        changes.append("activado" if activado else "desactivado")
    if accion is not None:
        hp_setting_set(interaction.guild.id, "honeypot_action", accion.value)
        changes.append(f"acción → {accion.name}")
    if rol_castigo is not None:
        hp_setting_set(interaction.guild.id, "honeypot_punish_role", str(rol_castigo.id))
        changes.append(f"rol de castigo → {rol_castigo.mention}")
    if purga_spec is not None:
        hp_setting_set(interaction.guild.id, "honeypot_purge_spec", f"{purga_spec[0]}:{purga_spec[1]}")
        changes.append(f"purga → {format_purge_spec(*purga_spec)}")
    if timeout_min is not None:
        hp_setting_set(interaction.guild.id, "honeypot_timeout_minutes", str(timeout_min))
        changes.append(f"timeout → {format_duration(timeout_min)}")
    if retencion_min is not None:
        hp_setting_set(interaction.guild.id, "honeypot_retention_minutes", str(retencion_min))
        hp_prune_history(interaction.guild.id)
        changes.append(f"retención → {format_duration(retencion_min)}")
    if ping_rol is not None:
        hp_setting_set(interaction.guild.id, "honeypot_ping_role", str(ping_rol.id))
        changes.append(f"ping → {ping_rol.mention}")
    if aviso is not None:
        hp_setting_set(interaction.guild.id, "honeypot_warning_enabled", "1" if aviso else "0")
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
    if canal.id in hp_traps(guild.id):
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
    hp_add_trap(guild.id, canal.id)
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
    hp_add_trap(guild.id, channel.id)
    err = await hp_sync_warning(channel)
    await interaction.followup.send(
        f"✅ Creé {channel.mention} y lo añadí como trampa." + (f"\n⚠️ {err}" if err else "")
        + "\nActívalo con `/honeypot setup activado:True` (empieza con `accion: Solo registrar` si quieres probar).",
        ephemeral=True,
    )
    await log_embed(guild, "🍯 Canal trampa creado", f"{interaction.user.mention} creó {channel.mention}.")


@honeypot_group.command(name="remove", description="Quitar un canal del honeypot (no lo borra).")
async def honeypot_remove(interaction: discord.Interaction, canal: discord.TextChannel) -> None:
    traps = hp_traps(interaction.guild.id)
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
    hp_remove_trap(interaction.guild.id, canal.id)
    extra = ""
    if not hp_traps(interaction.guild.id) and honeypot_enabled(interaction.guild.id):
        hp_setting_set(interaction.guild.id, "honeypot_enabled", "0")
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

    def __init__(self, guild_id: int) -> None:
        super().__init__()
        self.guild_id = guild_id
        cfg = hp_warning_custom(guild_id)
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

        hp_setting_set(interaction.guild.id, "honeypot_warning_title", title)
        hp_setting_set(interaction.guild.id, "honeypot_warning_description", description)
        hp_setting_set(interaction.guild.id, "honeypot_warning_color", color.upper())
        hp_setting_set(interaction.guild.id, "honeypot_warning_image", image)
        hp_setting_set(interaction.guild.id, "honeypot_warning_thumbnail", "")
        hp_setting_set(interaction.guild.id, "honeypot_warning_footer", footer)
        hp_setting_set(interaction.guild.id, "honeypot_warning_style", "custom")

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
    await interaction.response.send_modal(HoneypotWarningEmbedModal(interaction.guild.id))


@honeypot_group.command(name="warning_text", description="Editar el texto del aviso fijado en los canales trampa.")
async def honeypot_warning_text_cmd(interaction: discord.Interaction) -> None:
    await interaction.response.send_modal(HoneypotWarningModal(interaction.guild.id))


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
        hp_exempt_add(interaction.guild.id, "role", rol.id)
        text = f"rol {rol.mention}"
    else:
        hp_exempt_add(interaction.guild.id, "member", miembro.id)
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
        hp_exempt_remove(interaction.guild.id, "role", rol.id)
        text = f"rol {rol.mention}"
    else:
        hp_exempt_remove(interaction.guild.id, "member", miembro.id)
        text = f"miembro {miembro.mention}"
    await interaction.response.send_message(f"✅ Exención quitada: {text}.", ephemeral=True)


@honeypot_group.command(name="history", description="Ver los últimos miembros atrapados.")
@discord.app_commands.describe(cantidad="Cuántos mostrar (1-10)")
async def honeypot_history(
    interaction: discord.Interaction, cantidad: discord.app_commands.Range[int, 1, 10] = 10
) -> None:
    rows = hp_recent_triggers(interaction.guild.id, cantidad)
    if not rows:
        await interaction.response.send_message("Aún no ha caído nadie en la trampa.", ephemeral=True)
        return
    embed = discord.Embed(
        title="🍯 Historial del honeypot",
        description=f"**{hp_total_triggers(interaction.guild.id)}** miembros atrapados en total.",
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
    if not honeypot_paused(interaction.guild.id):
        await interaction.response.send_message("El honeypot no está pausado.", ephemeral=True)
        return
    hp_setting_set(interaction.guild.id, "honeypot_paused", "0")
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


@bot.tree.command(name="warn", description="Advierte a un miembro y crea un caso de Moderation.")
@app_commands.describe(usuario="Miembro", motivo="Motivo", duracion="Opcional: 30m, 2h, 7d", prueba="Enlace o texto de prueba")
@app_commands.checks.has_permissions(moderate_members=True)
@app_commands.guild_only()
async def moderation_warn(interaction: discord.Interaction, usuario: discord.Member, motivo: str, duracion: Optional[str] = None, prueba: Optional[str] = None) -> None:
    minutes = None
    if duracion:
        try:
            minutes = parse_duration(duracion, 1, 365 * 24 * 60)
        except ValueError as exc:
            await interaction.response.send_message(f"Duración inválida: {exc}", ephemeral=True)
            return
    await interaction.response.defer(ephemeral=True, thinking=True)
    ok, note, _ = await moderation_apply_case_punishment(interaction, usuario, "WARN", motivo.strip(), minutes, prueba)
    await interaction.followup.send(("Listo. " if ok else "No pude hacerlo: ") + note, ephemeral=True)


@bot.tree.command(name="mute", description="Aplica timeout y crea un caso de Moderation.")
@app_commands.describe(usuario="Miembro", duracion="Ej.: 30m, 2h, 7d", motivo="Motivo", prueba="Enlace o texto de prueba")
@app_commands.checks.has_permissions(moderate_members=True)
@app_commands.guild_only()
async def moderation_mute(interaction: discord.Interaction, usuario: discord.Member, duracion: str, motivo: str, prueba: Optional[str] = None) -> None:
    try:
        minutes = parse_duration(duracion, 1, 365 * 24 * 60)
    except ValueError as exc:
        await interaction.response.send_message(f"Duración inválida: {exc}", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True, thinking=True)
    ok, note, _ = await moderation_apply_case_punishment(interaction, usuario, "MUTE", motivo.strip(), minutes, prueba)
    await interaction.followup.send(("Listo. " if ok else "No pude hacerlo: ") + note, ephemeral=True)


@bot.tree.command(name="kick", description="Expulsa a un miembro y crea un caso de Moderation.")
@app_commands.describe(usuario="Miembro", motivo="Motivo", prueba="Enlace o texto de prueba")
@app_commands.checks.has_permissions(kick_members=True)
@app_commands.guild_only()
async def moderation_kick(interaction: discord.Interaction, usuario: discord.Member, motivo: str, prueba: Optional[str] = None) -> None:
    await interaction.response.defer(ephemeral=True, thinking=True)
    ok, note, _ = await moderation_apply_case_punishment(interaction, usuario, "KICK", motivo.strip(), None, prueba)
    await interaction.followup.send(("Listo. " if ok else "No pude hacerlo: ") + note, ephemeral=True)


@bot.tree.command(name="ban", description="Banea a un miembro y crea un caso de Moderation.")
@app_commands.describe(usuario="Miembro", motivo="Motivo", duracion="Opcional: ban temporal", prueba="Enlace o texto de prueba")
@app_commands.checks.has_permissions(ban_members=True)
@app_commands.guild_only()
async def moderation_ban(interaction: discord.Interaction, usuario: discord.Member, motivo: str, duracion: Optional[str] = None, prueba: Optional[str] = None) -> None:
    minutes = None
    if duracion:
        try:
            minutes = parse_duration(duracion, 1, 10 * 365 * 24 * 60)
        except ValueError as exc:
            await interaction.response.send_message(f"Duración inválida: {exc}", ephemeral=True)
            return
    await interaction.response.defer(ephemeral=True, thinking=True)
    ok, note, _ = await moderation_apply_case_punishment(interaction, usuario, "BAN", motivo.strip(), minutes, prueba)
    await interaction.followup.send(("Listo. " if ok else "No pude hacerlo: ") + note, ephemeral=True)


@bot.tree.command(name="caseinfo", description="Muestra la información de un caso de Moderation.")
@app_commands.checks.has_permissions(moderate_members=True)
@app_commands.guild_only()
async def moderation_caseinfo(interaction: discord.Interaction, caso: int) -> None:
    row = moderation_case_get(interaction.guild.id, caso)
    if row is None:
        await interaction.response.send_message("No existe ese caso en este servidor.", ephemeral=True)
        return
    await interaction.response.send_message(embed=moderation_case_embed(interaction.guild, row), ephemeral=True)


@bot.tree.command(name="caselist", description="Lista los casos más recientes de Moderation.")
@app_commands.describe(usuario="Filtrar por usuario", tipo="WARN, MUTE, KICK, BAN o CONDEMN", abiertos="True: abiertos; False: cerrados")
@app_commands.checks.has_permissions(moderate_members=True)
@app_commands.guild_only()
async def moderation_caselist(interaction: discord.Interaction, usuario: Optional[discord.User] = None, tipo: Optional[str] = None, abiertos: Optional[bool] = None) -> None:
    case_type = tipo.upper() if tipo else None
    if case_type and case_type not in MODERATION_CASE_TYPES:
        await interaction.response.send_message("Tipo inválido. Usa WARN, MUTE, KICK, BAN o CONDEMN.", ephemeral=True)
        return
    rows = moderation_case_list(interaction.guild.id, usuario.id if usuario else None, case_type, abiertos, 20)
    if not rows:
        await interaction.response.send_message("No encontré casos con esos filtros.", ephemeral=True)
        return
    lines = [f"#{row['case_number']} · {row['type']} · <@{row['user_id']}> · {'abierto' if row['open'] else 'cerrado'} · {str(row['reason'])[:90]}" for row in rows]
    await interaction.response.send_message("\n".join(lines)[:1900], ephemeral=True)


@bot.tree.command(name="caseupdate", description="Actualiza motivo, duración o notas de un caso.")
@app_commands.describe(caso="Número de caso", motivo="Nuevo motivo", duracion="Nueva duración; 0 = sin duración", notas="Notas internas")
@app_commands.checks.has_permissions(moderate_members=True)
@app_commands.guild_only()
async def moderation_caseupdate(interaction: discord.Interaction, caso: int, motivo: Optional[str] = None, duracion: Optional[str] = None, notas: Optional[str] = None) -> None:
    if moderation_case_get(interaction.guild.id, caso) is None:
        await interaction.response.send_message("No existe ese caso.", ephemeral=True)
        return
    duration_value: int | None | object = ...
    if duracion is not None:
        if duracion.strip() == "0":
            duration_value = None
        else:
            try:
                duration_value = parse_duration(duracion, 1, 10 * 365 * 24 * 60)
            except ValueError as exc:
                await interaction.response.send_message(f"Duración inválida: {exc}", ephemeral=True)
                return
    moderation_case_update(interaction.guild.id, caso, reason=motivo, duration_minutes=duration_value, notes=notas)
    row = moderation_case_get(interaction.guild.id, caso)
    await interaction.response.send_message(embed=moderation_case_embed(interaction.guild, row), ephemeral=True)


@bot.tree.command(name="setproof", description="Establece o reemplaza la prueba de un caso.")
@app_commands.describe(caso="Número de caso", prueba="Texto o enlace de mensaje")
@app_commands.checks.has_permissions(moderate_members=True)
@app_commands.guild_only()
async def moderation_setproof(interaction: discord.Interaction, caso: int, prueba: str) -> None:
    row = moderation_case_get(interaction.guild.id, caso)
    if row is None:
        await interaction.response.send_message("No existe ese caso.", ephemeral=True)
        return
    verified = await moderation_verified_proof(interaction.guild, prueba)
    moderation_case_update(interaction.guild.id, caso, proof=prueba, verified_proof=verified if verified is not None else row["verified_proof"])
    await interaction.response.send_message("Prueba actualizada.", ephemeral=True)


@bot.tree.command(name="caseclose", description="Cierra un caso y revierte el castigo reversible cuando corresponde.")
@app_commands.describe(caso="Número de caso", motivo="Resolución o motivo de cierre")
@app_commands.checks.has_permissions(moderate_members=True)
@app_commands.guild_only()
async def moderation_caseclose(interaction: discord.Interaction, caso: int, motivo: Optional[str] = None) -> None:
    row = moderation_case_get(interaction.guild.id, caso)
    if row is None:
        await interaction.response.send_message("No existe ese caso.", ephemeral=True)
        return
    if not row["open"]:
        await interaction.response.send_message("Ese caso ya está cerrado.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True, thinking=True)
    effect = await moderation_close_case_effect(interaction.guild, row, interaction.user)
    moderation_case_close(interaction.guild.id, caso, closed_by=interaction.user.id, resolution=motivo or "Cerrado manualmente")
    await interaction.followup.send(f"Caso #{caso} cerrado. {effect}", ephemeral=True)


@bot.tree.command(name="casedelete", description="Elimina definitivamente un caso de Moderation.")
@app_commands.checks.has_permissions(administrator=True)
@app_commands.guild_only()
async def moderation_casedelete(interaction: discord.Interaction, caso: int) -> None:
    if not moderation_case_delete(interaction.guild.id, caso):
        await interaction.response.send_message("No existe ese caso.", ephemeral=True)
        return
    await interaction.response.send_message(f"Caso #{caso} eliminado.", ephemeral=True)

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

def raid_setting_get(guild_id: int, key: str) -> str | None:
    value = guild_config_get(guild_id, key)
    if value is not None:
        return value
    if legacy_fallback_allowed(guild_id):
        return db_meta_get(key)
    return None


def raid_setting_int(guild_id: int, key: str, fallback: int) -> int:
    value = raid_setting_get(guild_id, key)
    try:
        return int(value) if value is not None else fallback
    except (TypeError, ValueError):
        return fallback


def raid_enabled(guild_id: int) -> bool:
    value = raid_setting_get(guild_id, "raid_enabled")
    return RAID_ENABLED_DEFAULT if value is None else value == "1"


def raid_threshold(guild_id: int) -> int:
    return raid_setting_int(guild_id, "raid_threshold", RAID_THRESHOLD_DEFAULT)


def raid_window_seconds(guild_id: int) -> int:
    return raid_setting_int(guild_id, "raid_window_seconds", RAID_WINDOW_DEFAULT)


def raid_duration_seconds(guild_id: int) -> int:
    return raid_setting_int(guild_id, "raid_duration_seconds", RAID_DURATION_DEFAULT)


def raid_min_age_seconds(guild_id: int) -> int:
    return raid_setting_int(guild_id, "raid_min_age_seconds", 0)


def raid_new_account_ratio(guild_id: int) -> int:
    """Porcentaje mínimo de cuentas nuevas dentro de la ventana. 0 = desactivado."""
    return max(0, min(100, raid_setting_int(guild_id, "raid_new_account_ratio", 0)))



def raid_action(guild_id: int) -> str:
    value = raid_setting_get(guild_id, "raid_action")
    return value if value in RAID_ACTION_LABELS else RAID_ACTION_DEFAULT


def raid_lock_invites_enabled(guild_id: int) -> bool:
    return raid_setting_get(guild_id, "raid_lock_invites") != "0"


def raid_purge_enabled(guild_id: int) -> bool:
    return raid_setting_get(guild_id, "raid_purge") != "0"


def raid_ping_role_id(guild_id: int) -> int:
    return raid_setting_int(guild_id, "raid_ping_role", 0)


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
    min_age = raid_min_age_seconds(member.guild.id)
    if min_age <= 0:
        return True
    return (datetime.now(timezone.utc) - member.created_at).total_seconds() < min_age


async def raid_alert(guild: discord.Guild, title: str, description: str, color: discord.Color) -> None:
    """Embed en el canal de logs con mención opcional al rol de alerta."""
    print(f"{title} — {description}")
    channel = guild.get_channel(get_log_channel_id(guild.id))
    if channel is None:
        return
    role = guild.get_role(raid_ping_role_id(guild.id)) if raid_ping_role_id(guild.id) else None
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
        return "invitaciones pausadas"
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
    return "invitaciones reabiertas"


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
        "started": datetime.now(timezone.utc), "trigger": "—", "action": raid_action(guild.id),
        "acted": 0, "failed": 0, "skipped": 0, "logged": 0, "purged": 0, "ids": [],
    })
    if member.bot or hp_is_exempt(member) or not raid_is_suspicious(member):
        stats["skipped"] += 1
        return False
    action = raid_action(guild.id)
    reason = "Raid Protection: ingreso masivo de miembros"
    if action == "log":
        stats["logged"] += 1
        stats["ids"].append(member.id)
        return False
    try:
        if action == "condemn":
            ok, note = await condemn_member(
                member, reason=reason, duration_minutes=condemnation_default_duration_minutes(member.guild.id), purge_spec=None, origin="raid",
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
    if raid_purge_enabled(guild.id) and action in ("condemn", "kick"):
        asyncio.create_task(_raid_purge_member(member, stats))
    return True


async def raid_start(
    guild: discord.Guild, *, trigger: str, suspects: list[int], started_by: discord.abc.User | None = None,
) -> set[int]:
    """Activa el modo raid y actúa sobre los sospechosos. Devuelve los ids que salieron del flujo normal."""
    duration = raid_duration_seconds(guild.id)
    now = datetime.now(timezone.utc)
    # Marcar el raid como activo ANTES de cualquier await: los ingresos simultáneos ya lo ven activo.
    _raid_set_until(guild.id, now + timedelta(seconds=duration))
    _raid_stats[guild.id] = {
        "started": now, "trigger": trigger, "action": raid_action(guild.id),
        "acted": 0, "failed": 0, "skipped": 0, "logged": 0, "purged": 0, "ids": [],
    }
    lock_note = await raid_lock_invites(guild) if raid_lock_invites_enabled(guild.id) else "—"
    await raid_alert(
        guild, "RAID DETECTADO — modo raid activado",
        f"**Motivo:** {trigger}\n"
        f"**Duración:** {format_flex_duration(duration)} (termina <t:{int((now + timedelta(seconds=duration)).timestamp())}:R>)\n"
        f"**Acción sobre los sospechosos:** {RAID_ACTION_LABELS[raid_action(guild.id)]}\n"
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
    await raid_alert(guild, "Modo raid terminado", "\n".join(lines), discord.Color.green())
    return "\n".join(lines)


async def raid_handle_join(member: discord.Member) -> bool:
    """Se llama en cada ingreso. Devuelve True si el miembro ya fue sancionado y debe saltarse
    el flujo normal de verificación."""
    if not raid_enabled(member.guild.id):
        return False
    guild = member.guild
    now = time.monotonic()
    window = raid_window_seconds(guild.id)
    joins = _raid_joins.setdefault(guild.id, deque())
    joins.append((now, member.id))
    while joins and now - joins[0][0] > window:
        joins.popleft()

    if raid_is_active(guild.id):
        return await raid_act_on_member(member)
    if len(joins) < raid_threshold(guild.id):
        return False

    suspects = [uid for _, uid in joins]
    ratio_required = raid_new_account_ratio(guild.id)
    min_age = raid_min_age_seconds(guild.id)
    ratio_note = ""
    if ratio_required > 0:
        if min_age <= 0:
            return False
        now_utc = datetime.now(timezone.utc)
        resolved = [guild.get_member(uid) for uid in suspects]
        new_accounts = [
            m for m in resolved
            if m is not None and (now_utc - m.created_at).total_seconds() < min_age
        ]
        ratio_actual = round((len(new_accounts) / len(suspects)) * 100) if suspects else 0
        if ratio_actual < ratio_required:
            return False
        ratio_note = f" · cuentas nuevas: {ratio_actual}% (mínimo: {ratio_required}%)"

    joins.clear()
    trigger = (
        f"{len(suspects)} ingresos en {format_flex_duration(window)} "
        f"(umbral: {raid_threshold(guild.id)}){ratio_note}"
    )
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
    role = guild.get_role(raid_ping_role_id(guild.id)) if raid_ping_role_id(guild.id) else None
    min_age = raid_min_age_seconds(guild.id)
    ratio = raid_new_account_ratio(guild.id)
    state = "🔴 **MODO RAID ACTIVO**" if raid_is_active(guild.id) else "🟢 Sin raid"
    until = raid_until(guild.id)
    lines = [
        f"**Raid Protection** — {'✅ activada' if raid_enabled(guild.id) else '❌ desactivada'} · {state}",
        f"• Disparo: **{raid_threshold(guild.id)}** ingresos en **{format_flex_duration(raid_window_seconds(guild.id))}**",
        f"• Duración del modo raid: **{format_flex_duration(raid_duration_seconds(guild.id))}**",
        f"• Acción: **{RAID_ACTION_LABELS[raid_action(guild.id)]}**",
        f"• Filtro de edad de cuenta: **{'cuentas de menos de ' + format_flex_duration(min_age) if min_age else 'sin filtro (todos los ingresos del raid)'}**",
        f"• Proporción mínima de cuentas nuevas: **{str(ratio) + '%' if ratio else 'desactivada'}**",
        f"• Alertas: **canal general de Logs de El Heraldo**",
        f"• Pausar invitaciones: **{'sí' if raid_lock_invites_enabled(guild.id) else 'no'}**",
        f"• Purgar mensajes de los sancionados: **{'sí' if raid_purge_enabled(guild.id) else 'no'}**",
        f"• Rol de alerta: {role.mention if role else '**ninguno**'}",
    ]
    if raid_is_active(guild.id) and until:
        lines.append(f"• El modo raid termina <t:{int(until.timestamp())}:R>")
    if raid_action(guild.id) == "condemn" and guild.get_role(condemnation_role_id(guild_id=guild.id)) is None:
        lines.append("⚠️ La acción es Condenar pero no hay rol Condenado: configúralo con `/honeypot setup rol_castigo`.")
    return "\n".join(lines)


raid_group = HoneypotGroup(
    name="raid",
    description="Protección contra raids (ingresos masivos).",
    guild_only=True,
    default_permissions=discord.Permissions(manage_guild=True),
)


@raid_group.command(name="setup", description="Ver o cambiar la configuración de la protección anti-raid.")
@discord.app_commands.describe(
    activado="Activar o desactivar la protección anti-raid",
    ingresos=f"Cuántos ingresos disparan el raid ({RAID_THRESHOLD_MIN} a {RAID_THRESHOLD_MAX})",
    ventana="En cuánto tiempo deben llegar: 10s, 1m… (1s a 1h)",
    duracion="Cuánto dura el modo raid: 30s, 10m, 12h, 2d, 1 mes… (10s a 12 meses)",
    accion="Qué hacer con los sospechosos durante el raid",
    edad_cuenta="Considerar nueva una cuenta más joven que esto: 30m, 7d, 1 mes…; 0 = sin filtro",
    proporcion_cuentas_nuevas="Porcentaje mínimo de cuentas nuevas en la ráfaga: 0 a 100; 0 = desactivado",
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
    proporcion_cuentas_nuevas: Optional[discord.app_commands.Range[int, 0, 100]] = None,
    pausar_invitaciones: Optional[bool] = None,
    purgar: Optional[bool] = None,
    ping_rol: Optional[discord.Role] = None,
) -> None:
    guild = interaction.guild
    values = (
        activado, ingresos, ventana, duracion, accion, edad_cuenta,
        proporcion_cuentas_nuevas, canal_alertas, pausar_invitaciones, purgar, ping_rol
    )
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
    effective_action = accion.value if accion is not None else raid_action(guild.id)
    effective_enabled = activado if activado is not None else raid_enabled(guild.id)
    effective_age = edad_s if edad_s is not None else raid_min_age_seconds(guild.id)
    effective_ratio = (
        int(proporcion_cuentas_nuevas)
        if proporcion_cuentas_nuevas is not None
        else raid_new_account_ratio(guild.id)
    )
    if effective_ratio > 0 and effective_age <= 0:
        await interaction.response.send_message(
            "❌ No guardé nada: para usar una proporción de cuentas nuevas debes configurar "
            "también una edad de cuenta mayor que 0.",
            ephemeral=True,
        )
        return
    if effective_enabled and effective_action == "condemn" and guild.get_role(condemnation_role_id(guild_id=guild.id)) is None \
            and (activado or accion is not None):
        await interaction.response.send_message(
            "❌ No guardé nada: la acción «Condenar» necesita el rol Condenado. "
            "Configúralo con `/honeypot setup rol_castigo` o elige otra acción.",
            ephemeral=True,
        )
        return

    changes: list[str] = []
    if activado is not None:
        guild_config_set(guild.id, "raid_enabled", "1" if activado else "0")
        changes.append("activada" if activado else "desactivada")
    if ingresos is not None:
        guild_config_set(guild.id, "raid_threshold", str(ingresos))
        changes.append(f"ingresos → {ingresos}")
    if ventana_s is not None:
        guild_config_set(guild.id, "raid_window_seconds", str(ventana_s))
        changes.append(f"ventana → {format_flex_duration(ventana_s)}")
    if duracion_s is not None:
        guild_config_set(guild.id, "raid_duration_seconds", str(duracion_s))
        changes.append(f"duración → {format_flex_duration(duracion_s)}")
    if accion is not None:
        guild_config_set(guild.id, "raid_action", accion.value)
        changes.append(f"acción → {accion.name}")
    if edad_s is not None:
        guild_config_set(guild.id, "raid_min_age_seconds", str(edad_s))
        changes.append(f"edad de cuenta → {format_flex_duration(edad_s) if edad_s else 'sin filtro'}")
    if proporcion_cuentas_nuevas is not None:
        guild_config_set(guild.id, "raid_new_account_ratio", str(int(proporcion_cuentas_nuevas)))
        changes.append(
            "proporción de cuentas nuevas → "
            + (f"{int(proporcion_cuentas_nuevas)}%" if int(proporcion_cuentas_nuevas) else "desactivada")
        )
    if pausar_invitaciones is not None:
        guild_config_set(guild.id, "raid_lock_invites", "1" if pausar_invitaciones else "0")
        changes.append("pausar invitaciones: " + ("sí" if pausar_invitaciones else "no"))
    if purgar is not None:
        guild_config_set(guild.id, "raid_purge", "1" if purgar else "0")
        changes.append("purgar: " + ("sí" if purgar else "no"))
    if ping_rol is not None:
        guild_config_set(guild.id, "raid_ping_role", str(ping_rol.id))
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
        f"✅ Modo raid activado por {format_flex_duration(raid_duration_seconds(guild.id))}: "
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
    ("👤 Usuario", "usuario_nombre", ("usuario", "user", "nombre", "name"),
     "nombre visible del usuario", _vm(lambda m: _safe(m.display_name))),
    ("👤 Usuario", "usuario_mencion", ("mencion", "mention", "ping"),
     "@mención del usuario", _vm(lambda m: m.mention)),
    ("👤 Usuario", "usuario_id", ("usuarioid", "userid", "id"),
     "ID del usuario", _vm(lambda m: str(m.id))),
    ("👤 Usuario", "usuario_tag", ("tag", "username", "handle"),
     "nombre de usuario / tag", _vm(lambda m: _safe(m.name))),
    ("👤 Usuario", "usuario_avatar_url", ("avatar", "pfp", "foto"),
     "URL del avatar del usuario", _vm(lambda m: m.display_avatar.url)),
    ("👤 Usuario", "usuario_fecha_creacion", ("cuenta", "created", "cuentacreada"),
     "fecha de creación de la cuenta", _vm(lambda m: discord.utils.format_dt(m.created_at, "D"))),
    ("👤 Usuario", "usuario_antiguedad", ("cuentahace", "accountago", "antiguedad"),
     "tiempo transcurrido desde que creó la cuenta", _vm(lambda m: discord.utils.format_dt(m.created_at, "R"))),
    ("👤 Usuario", "usuario_fecha_ingreso", ("ingreso", "joined", "entro"),
     "fecha en que el usuario entró al servidor",
     _vm(lambda m: discord.utils.format_dt(m.joined_at, "D") if getattr(m, "joined_at", None) else "")),

    ("🏠 Servidor", "servidor_nombre", ("servidor", "server", "guild", "servername"),
     "nombre del servidor", _vg(lambda g: _safe(g.name))),
    ("🏠 Servidor", "servidor_id", ("servidorid", "serverid", "guildid"),
     "ID del servidor", _vg(lambda g: str(g.id))),
    ("🏠 Servidor", "servidor_icono_url", ("servericon", "guildicon", "iconoservidor", "icono", "icon"),
     "URL del icono del servidor", _vg(lambda g: g.icon.url if g.icon else "")),
    ("🏠 Servidor", "servidor_banner_url", ("serverbanner", "guildbanner", "bannerservidor", "banner"),
     "URL del banner del servidor", _vg(lambda g: g.banner.url if g.banner else "")),
    ("🏠 Servidor", "servidor_miembros", ("miembros", "members", "membercount", "usuarios"),
     "cantidad de miembros del servidor", _vg(lambda g: str(g.member_count or len(g.members)))),
    ("🏠 Servidor", "servidor_boosts", ("boosts", "boostcount"),
     "cantidad de boosts del servidor", _vg(lambda g: str(g.premium_subscription_count))),
    ("🏠 Servidor", "servidor_nivel_boost", ("nivelboost", "boostlevel", "premiumtier"),
     "nivel de boost del servidor", _vg(lambda g: str(g.premium_tier))),
    ("🏠 Servidor", "servidor_dueno_mencion", ("dueno", "dueño", "owner"),
     "@mención del propietario del servidor", _vg(lambda g: f"<@{g.owner_id}>")),
    ("🏠 Servidor", "servidor_fecha_creacion", ("creado", "servercreated", "guildcreated"),
     "fecha de creación del servidor", _vg(lambda g: discord.utils.format_dt(g.created_at, "D"))),
    ("🏠 Servidor", "servidor_canal_reglas", ("reglas", "rules"),
     "mención del canal de reglas configurado en Discord", _vg(lambda g: _chan_mention(g.rules_channel))),
    ("🏠 Servidor", "servidor_canal_sistema", ("sistema", "system", "systemchannel"),
     "mención del canal de sistema configurado en Discord", _vg(lambda g: _chan_mention(g.system_channel))),

    ("💬 Canal actual", "canal_mencion", ("canal", "channel", "aqui", "here"),
     "#mención del canal donde se publica", _vc(lambda ch: ch.mention)),
    ("💬 Canal actual", "canal_id", ("canalid", "channelid"),
     "ID del canal donde se publica", _vc(lambda ch: str(ch.id))),
    ("💬 Canal actual", "canal_nombre", ("canalnombre", "channelname"),
     "nombre del canal donde se publica", _vc(lambda ch: _safe(ch.name))),

    ("🕒 Fecha y hora", "fecha_actual", ("fecha", "date"),
     "fecha actual", lambda c: discord.utils.format_dt(_vn(), "D")),
    ("🕒 Fecha y hora", "hora_actual", ("hora", "time"),
     "hora actual", lambda c: discord.utils.format_dt(_vn(), "t")),
    ("🕒 Fecha y hora", "fecha_hora_actual", ("ahora", "now"),
     "fecha y hora actuales completas", lambda c: discord.utils.format_dt(_vn(), "F")),
    ("🕒 Fecha y hora", "timestamp_unix", ("timestamp", "unix"),
     "marca de tiempo Unix actual", lambda c: str(int(_vn().timestamp()))),
    ("📝 Texto", "salto_linea", ("salto", "nl", "br"),
     "salto de línea", lambda c: "\n"),
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
        if kind in ("canal", "channel", "c", "canalmencion", "mencioncanal"):
            return _lookup_channel(rest, ctx.guild)
        if kind in ("rol", "role", "r", "mencionrol", "rolmencion"):
            return _lookup_role(rest, ctx.guild)
        if kind in ("usuario", "user", "miembro", "member", "u", "usuariomencion", "mencionusuario"):
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
            "Escríbelas con `{nombre}` o `${nombre}` en cualquier texto personalizable del Heraldo. "
            "Los nombres principales son explícitos y en español; los nombres antiguos siguen funcionando como alias.\n"
            "No importan mayúsculas, tildes ni separadores. Si una variable no existe o no aplica, "
            "se deja tal cual para que puedas detectar el error."
        ),
        color=discord.Color.blurple(),
    )
    for group, lines in groups.items():
        embed.add_field(name=group, value="\n".join(lines)[:1024], inline=False)
    embed.add_field(
        name="🔎 Buscar cosas del servidor por nombre o ID",
        value=(
            "`{canal_mencion:reglas}` → mención de un canal por nombre o ID\n"
            "`{rol_mencion:Moderador}` → mención de un rol por nombre o ID\n"
            "`{usuario_mencion:Nombre}` → mención de un miembro por nombre o ID\n"
            "`{emoji:fuego}` → emoji personalizado del servidor\n"
            "Atajos compatibles: `{#reglas}` · `{@Moderador}` · `{canal:nombre}` · `{rol:nombre}` · `{usuario:nombre}`\n"
            "Ejemplo: `Hola {usuario_mencion}, lee {canal_mencion:reglas}` · "
            "imagen: `{servidor_icono_url}`"
        ),
        inline=False,
    )
    embed.set_footer(text="Prueba un texto con /variables texto:…")
    return [embed]


@bot.tree.command(name="variables", description="Probar un texto con las variables de El Heraldo.")
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
        await interaction.response.send_message(
            "ℹ️ El catálogo de variables se movió a `/list variables`. "
            "Usa este comando con `texto` cuando quieras probar cómo se resuelven.",
            ephemeral=True,
        )
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
# LISTADOS CENTRALIZADOS (/list)
# ---------------------------------------------------------------------------
# Los listados administrativos viven aquí para evitar comandos duplicados como
# /condenados o /embed lista. Son privados para el creador del bot, el creador del servidor o administradores.

list_group = discord.app_commands.Group(
    name="list",
    description="Consultar los listados privados de El Heraldo.",
    guild_only=True,
)


async def _list_require_server_owner(interaction: discord.Interaction) -> bool:
    guild = interaction.guild
    if guild is None:
        await interaction.response.send_message("❌ Este comando solo funciona dentro de un servidor.", ephemeral=True)
        return False
    is_bot_owner = await bot.is_owner(interaction.user)
    perms = getattr(interaction.user, "guild_permissions", None)
    is_admin = bool(perms and perms.administrator)
    if interaction.user.id != guild.owner_id and not is_bot_owner and not is_admin:
        await interaction.response.send_message(
            "❌ Solo el creador del bot, el creador del servidor o un administrador pueden consultar estos listados.",
            ephemeral=True,
        )
        return False
    return True


def _list_text_embeds(
    title: str,
    lines: list[str],
    *,
    color: discord.Color = discord.Color.blurple(),
    empty_text: str = "No hay elementos.",
) -> list[discord.Embed]:
    """Convierte líneas en páginas seguras para Discord (máx. 10 embeds por respuesta)."""
    if not lines:
        return [discord.Embed(title=title, description=empty_text, color=color)]

    pages: list[str] = []
    current = ""
    for line in lines:
        candidate = f"{current}\n{line}" if current else line
        if len(candidate) > 3800:
            if current:
                pages.append(current)
            current = line[:3800]
        else:
            current = candidate
    if current:
        pages.append(current)

    hidden_pages = max(0, len(pages) - 10)
    pages = pages[:10]
    embeds: list[discord.Embed] = []
    total = len(pages)
    for index, page in enumerate(pages, start=1):
        page_title = title if total == 1 else f"{title} · {index}/{total}"
        embed = discord.Embed(title=page_title, description=page, color=color)
        if hidden_pages and index == total:
            embed.set_footer(text=f"Hay {hidden_pages} página(s) adicional(es) que exceden el límite de Discord.")
        embeds.append(embed)
    return embeds


def _list_command_lines() -> list[str]:
    lines: list[str] = []

    def visit(commands_list, prefix: str = "") -> None:
        for command in sorted(commands_list, key=lambda item: item.name):
            qualified = f"{prefix} {command.name}".strip()
            children = getattr(command, "commands", None)
            if children:
                visit(children, qualified)
                continue
            description = (getattr(command, "description", "") or "Sin descripción").strip()
            lines.append(f"• `/{qualified}` — {description}")

    visit(bot.tree.get_commands())
    return lines


@list_group.command(name="comandos", description="Ver todos los comandos disponibles del Heraldo.")
async def list_commands_command(interaction: discord.Interaction) -> None:
    if not await _list_require_server_owner(interaction):
        return
    lines = _list_command_lines()
    embeds = _list_text_embeds(
        "📚 Comandos de El Heraldo",
        lines,
        empty_text="No hay comandos registrados.",
    )
    embeds[0].description = f"**{len(lines)}** comando(s) registrado(s).\n\n" + (embeds[0].description or "")
    await interaction.response.send_message(embeds=embeds, ephemeral=True)


@list_group.command(name="variables", description="Ver todas las variables disponibles para textos y embeds.")
async def list_variables_command(interaction: discord.Interaction) -> None:
    if not await _list_require_server_owner(interaction):
        return
    await interaction.response.send_message(embeds=variables_embeds(), ephemeral=True)


@list_group.command(name="condenados", description="Ver todas las condenas activas del servidor.")
async def list_condemned_command(interaction: discord.Interaction) -> None:
    if not await _list_require_server_owner(interaction):
        return
    rows = condemnation_list(interaction.guild.id)
    if not rows:
        await interaction.response.send_message(
            embed=discord.Embed(
                title="☠️ Condenados activos",
                description="No hay condenas activas.",
                color=discord.Color.dark_red(),
            ),
            ephemeral=True,
        )
        return

    embeds: list[discord.Embed] = []
    for start in range(0, len(rows), 25):
        batch = rows[start:start + 25]
        page = start // 25 + 1
        total_pages = (len(rows) + 24) // 25
        title = "☠️ Condenados activos" if total_pages == 1 else f"☠️ Condenados activos · {page}/{total_pages}"
        embed = discord.Embed(
            title=title,
            description=f"**{len(rows)}** condena(s) activa(s) en este servidor.",
            color=discord.Color.dark_red(),
        )
        for row in batch:
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
        embeds.append(embed)
        if len(embeds) == 10:
            break
    if len(rows) > 250:
        embeds[-1].set_footer(text=f"Mostrando 250 de {len(rows)} condenas activas por el límite de Discord.")
    await interaction.response.send_message(embeds=embeds, ephemeral=True)


@list_group.command(name="embeds", description="Ver los embeds personalizados guardados por nombre.")
async def list_embeds_command(interaction: discord.Interaction) -> None:
    if not await _list_require_server_owner(interaction):
        return
    names = embed_names(interaction.guild.id)
    lines = [
        f"• `{name}`" + (f" — enviado en **{count}** mensaje(s)" if count else " — todavía no enviado")
        for name, count in names
    ]
    embeds = _list_text_embeds(
        "🧩 Embeds guardados",
        lines,
        empty_text="No hay embeds guardados. Crea uno con `/embed crear`.",
    )
    if names:
        embeds[0].description = f"**{len(names)}** embed(s) guardado(s).\n\n" + (embeds[0].description or "")
    await interaction.response.send_message(embeds=embeds, ephemeral=True)


@list_group.error
async def list_group_error(interaction: discord.Interaction, error: discord.app_commands.AppCommandError) -> None:
    await verify_command_error(interaction, error)


bot.tree.add_command(list_group)


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
    if guild is not None and (
        typed[:1] == "#" or kind_key in ("canal", "channel", "c", "canalmencion", "mencioncanal")
    ):
        query = typed[1:] if typed[:1] == "#" else rest
        prefix = "#" if typed[:1] == "#" else f"{kind}:"
        pick([c for c in guild.channels if not isinstance(c, discord.CategoryChannel)], lambda c: c.name, query,
             lambda c: add(f"#{c.name} (canal)", f"{prefix}{c.name}"))
    elif guild is not None and (
        typed[:1] == "@" or kind_key in (
            "rol", "role", "r", "mencionrol", "rolmencion",
            "usuario", "user", "miembro", "member", "u", "usuariomencion", "mencionusuario",
        )
    ):
        is_role_kind = typed[:1] == "@" or kind_key in ("rol", "role", "r", "mencionrol", "rolmencion")
        query = typed[1:] if typed[:1] == "@" else rest
        prefix = "@" if typed[:1] == "@" else f"{kind}:"
        roles = [r for r in guild.roles if not r.is_default()] if is_role_kind else []
        pick(roles, lambda r: r.name, query, lambda r: add(f"@{r.name} (rol)", f"{prefix}{r.name}"))
        if typed[:1] == "@" or not is_role_kind:
            pick(guild.members, lambda m: m.display_name, query,
                 lambda m: add(f"@{m.display_name} (usuario)", f"{prefix}{m.display_name}"))
    elif kind_key in ("emoji", "e"):
        pools = list(guild.emojis) if guild is not None else []
        pick(pools, lambda e: e.name, rest, lambda e: add(f"{e} :{e.name}:", f"{kind}:{e.name}"))
    elif not sep and typed[:1] not in ("#", "@"):
        typed_key = _var_key(typed)
        if not typed_key:  # recién escrita la llave: enseñar también las búsquedas
            for label, inner in (
                ("canal_mencion:  → mencionar un canal", "canal_mencion:"),
                ("rol_mencion:  → mencionar un rol", "rol_mencion:"),
                ("usuario_mencion:  → mencionar un usuario", "usuario_mencion:"),
                ("emoji:  → insertar un emoji del servidor", "emoji:"),
                ("#  → atajo para canales", "#"),
                ("@  → atajo para roles o usuarios", "@"),
            ):
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
    conn = db_connect()
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
        self.pending_timestamp: bool | None = None
        self.pending_remove_index: int | None = None
        self.toggle_time.label = "Fecha: " + ("sí" if data.get("timestamp") else "no")
        fields = data.get("fields", [])
        if fields:
            options = [
                discord.SelectOption(label=f"{i + 1}. {field['name']}"[:100], value=str(i), description=field["value"][:100] or None)
                for i, field in enumerate(fields[:25])
            ]
            select = discord.ui.Select(placeholder="Quitar un campo…", options=options, row=1)
            select.callback = self.select_remove_field
            self.remove_select = select
            self.add_item(select)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("Este editor no es tuyo: usa /embed editar.", ephemeral=True)
            return False
        return True

    def _data(self) -> dict | None:
        record = embed_get(self.guild_id, self.name)
        return record[0] if record else None

    async def _gone(self, interaction: discord.Interaction) -> None:
        await interaction.response.edit_message(content="Ese embed ya no existe.", embed=None, view=None)

    @discord.ui.button(label="Contenido", style=discord.ButtonStyle.primary, row=0)
    async def edit_content(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        data = self._data()
        if data is None:
            return await self._gone(interaction)
        await interaction.response.send_modal(EmbedContentModal(self.guild_id, self.name, data))

    @discord.ui.button(label="Autor y pie", style=discord.ButtonStyle.primary, row=0)
    async def edit_author(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        data = self._data()
        if data is None:
            return await self._gone(interaction)
        await interaction.response.send_modal(EmbedAuthorFooterModal(self.guild_id, self.name, data))

    @discord.ui.button(label="Campo", style=discord.ButtonStyle.secondary, row=0)
    async def add_field(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await interaction.response.send_modal(EmbedFieldModal(self.guild_id, self.name))

    @discord.ui.button(label="Fecha: no", style=discord.ButtonStyle.secondary, row=0)
    async def toggle_time(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        data = self._data()
        if data is None:
            return await self._gone(interaction)
        current = self.pending_timestamp if self.pending_timestamp is not None else bool(data.get("timestamp"))
        self.pending_timestamp = not current
        self.toggle_time.label = "Fecha: " + ("sí" if self.pending_timestamp else "no")
        await interaction.response.edit_message(
            content=f"Editando {self.name}. Cambio de fecha pendiente; pulsa Guardar cambios.",
            view=self,
        )

    async def select_remove_field(self, interaction: discord.Interaction) -> None:
        data = self._data()
        if data is None:
            return await self._gone(interaction)
        index = int(self.remove_select.values[0])
        if not 0 <= index < len(data.get("fields", [])):
            await interaction.response.send_message("Ese campo ya no existe.", ephemeral=True)
            return
        self.pending_remove_index = index
        await interaction.response.edit_message(
            content=f"Editando {self.name}. Se quitará el campo {index + 1} al guardar.",
            view=self,
        )

    @discord.ui.button(label="Guardar cambios", style=discord.ButtonStyle.success, row=2)
    async def save_changes(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if self.pending_timestamp is None and self.pending_remove_index is None:
            await interaction.response.send_message("No hay cambios pendientes.", ephemeral=True)
            return
        record = embed_get(self.guild_id, self.name)
        if record is None:
            return await self._gone(interaction)
        data = json.loads(json.dumps(record[0]))
        if self.pending_timestamp is not None:
            data["timestamp"] = self.pending_timestamp
        if self.pending_remove_index is not None and 0 <= self.pending_remove_index < len(data.get("fields", [])):
            data["fields"].pop(self.pending_remove_index)
        embed_save(self.guild_id, self.name, data)
        self.pending_timestamp = None
        self.pending_remove_index = None
        await embed_refresh(interaction, self.name)

    @discord.ui.button(label="Descartar cambios", style=discord.ButtonStyle.secondary, row=2)
    async def discard_changes(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        self.pending_timestamp = None
        self.pending_remove_index = None
        await embed_refresh(interaction, self.name)

    @discord.ui.button(label="Enviar", style=discord.ButtonStyle.success, row=3)
    async def send_embed(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if self.pending_timestamp is not None or self.pending_remove_index is not None:
            await interaction.response.send_message("Guarda o descarta los cambios pendientes antes de enviar.", ephemeral=True)
            return
        await interaction.response.send_message("¿A qué canal lo envío?", view=EmbedChannelPicker(interaction.user.id, self.name), ephemeral=True)


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
        await interaction.response.send_message(f"❌ No existe un embed llamado `{name}`. Mira `/list embeds`.", ephemeral=True)
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

SUGGESTION_PANEL_TITLE_DEFAULT = "EL ORÁCULO ESCUCHA"
SUGGESTION_PANEL_DESCRIPTION_DEFAULT = (
    "Toda alma tiene algo que pedir, y este paraíso está dispuesto a escuchar.\n\n"
    "¿Tienes una idea para mejorar este mundo? ¿Alguna inquietud? Un canal que falta, "
    "un evento que sueñas ver, una regla que merece cambiar — El Oráculo la recibe.\n\n"
    "**¿Cómo invocar tu deseo?**\n"
    "Pulsa **💡 Crear sugerencia** y completa el formulario privado.\n\n"
    "Tu propuesta será enviada directamente a quienes gobiernan este paraíso. "
    "El canal no se llenará con las sugerencias.\n\n"
    "No hay deseo demasiado pequeño, ni pecado demasiado grande de proponer."
)
SUGGESTION_PANEL_COLOR_DEFAULT = "4F5BDC"
SUGGESTION_PANEL_IMAGE_DEFAULT = ""
SUGGESTION_PANEL_THUMBNAIL_DEFAULT = "{servericon}"
SUGGESTION_PANEL_FOOTER_DEFAULT = ""
SUGGESTION_PANEL_BUTTON_DEFAULT = "💡 Crear sugerencia"


def suggestion_db_init() -> None:
    conn = db_connect()
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
    conn = db_connect()
    rows = conn.execute(
        "SELECT user_id FROM suggestion_reviewers WHERE guild_id = ? ORDER BY user_id",
        (guild_id,),
    ).fetchall()
    conn.close()
    return [int(row[0]) for row in rows]


def suggestion_add_reviewer(guild_id: int, user_id: int) -> None:
    conn = db_connect()
    conn.execute(
        "INSERT OR IGNORE INTO suggestion_reviewers (guild_id, user_id) VALUES (?, ?)",
        (guild_id, user_id),
    )
    conn.commit()
    conn.close()


def suggestion_remove_reviewer(guild_id: int, user_id: int) -> bool:
    conn = db_connect()
    cur = conn.execute(
        "DELETE FROM suggestion_reviewers WHERE guild_id = ? AND user_id = ?",
        (guild_id, user_id),
    )
    conn.commit()
    conn.close()
    return cur.rowcount > 0


def suggestion_get(suggestion_id: int) -> sqlite3.Row | None:
    conn = db_connect()
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT * FROM suggestions WHERE id = ?", (suggestion_id,)).fetchone()
    conn.close()
    return row


def suggestion_create(guild_id: int, user_id: int, title: str, content: str) -> int:
    conn = db_connect()
    cur = conn.execute(
        "INSERT INTO suggestions (guild_id, user_id, title, content, status, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (guild_id, user_id, title, content, SUGGESTION_STATUS_PENDING, datetime.now(timezone.utc).isoformat()),
    )
    suggestion_id = int(cur.lastrowid)
    conn.commit()
    conn.close()
    return suggestion_id


def suggestion_set_review_message(suggestion_id: int, reviewer_id: int, channel_id: int, message_id: int) -> None:
    conn = db_connect()
    conn.execute(
        "INSERT OR REPLACE INTO suggestion_review_messages "
        "(suggestion_id, reviewer_id, channel_id, message_id) VALUES (?, ?, ?, ?)",
        (suggestion_id, reviewer_id, channel_id, message_id),
    )
    conn.commit()
    conn.close()


def suggestion_review_messages(suggestion_id: int) -> list[sqlite3.Row]:
    conn = db_connect()
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
    conn = db_connect()
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
    ctx = VarContext(guild)
    title = guild_config_get(guild.id, "suggestion_panel_title") or SUGGESTION_PANEL_TITLE_DEFAULT
    description = guild_config_get(guild.id, "suggestion_panel_description") or SUGGESTION_PANEL_DESCRIPTION_DEFAULT
    color_raw = (
        guild_config_get(guild.id, "suggestion_panel_color")
        or SUGGESTION_PANEL_COLOR_DEFAULT
    ).strip().lstrip("#")
    image_raw = (
        guild_config_get(guild.id, "suggestion_panel_image")
        or SUGGESTION_PANEL_IMAGE_DEFAULT
    ).strip()
    thumbnail_raw = (
        guild_config_get(guild.id, "suggestion_panel_thumbnail")
        or SUGGESTION_PANEL_THUMBNAIL_DEFAULT
    ).strip()
    footer_raw = guild_config_get(guild.id, "suggestion_panel_footer")
    if footer_raw is None:
        footer_raw = SUGGESTION_PANEL_FOOTER_DEFAULT

    try:
        color = discord.Color(int(color_raw, 16))
    except (TypeError, ValueError):
        color = discord.Color.blurple()

    embed = discord.Embed(
        title=render_vars(title, ctx, 256),
        description=render_vars(description, ctx, 4096),
        color=color,
    )

    image_url = render_url_var(image_raw, ctx)
    if image_url:
        embed.set_image(url=image_url)

    thumbnail_url = render_url_var(thumbnail_raw, ctx)
    if thumbnail_url:
        embed.set_thumbnail(url=thumbnail_url)

    footer_text = render_vars(footer_raw, ctx, 2048, plain=True)
    if footer_text:
        embed.set_footer(text=footer_text)

    return embed


class SuggestionPanelView(discord.ui.View):
    def __init__(self, guild_id: int | None = None) -> None:
        super().__init__(timeout=None)
        label = SUGGESTION_PANEL_BUTTON_DEFAULT
        if guild_id is not None:
            label = guild_config_get(guild_id, "suggestion_panel_button_label") or label
        button = discord.ui.Button(
            label=label[:80],
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
    message = await channel.send(embed=suggestion_panel_embed(guild), view=SuggestionPanelView(guild.id))
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
            await message.edit(embed=suggestion_panel_embed(guild), view=SuggestionPanelView(guild.id))
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
    conn = db_connect()
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


@suggestions_group.command(name="setup", description="Elegir si el creador del servidor también recibe las sugerencias por DM.")
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
# 15. CENTRO DE MENSAJES — editor unificado de paneles persistentes
# ---------------------------------------------------------------------------
# Inspirado en el flujo de "Messages" de Sapphire: un único lugar para abrir los
# editores de los mensajes/paneles visuales que sí tiene sentido personalizar.
# Se excluyen deliberadamente paneles informativos generados a partir del estado
# real del bot, como /variables, diagnósticos, listas de comandos y resúmenes.


class SuggestionPanelEditorModal(discord.ui.Modal, title="Mensajes · Panel de sugerencias"):
    title_input = discord.ui.TextInput(label="Título", required=True, max_length=256)
    description_input = discord.ui.TextInput(
        label="Descripción",
        style=discord.TextStyle.paragraph,
        required=True,
        max_length=4000,
    )
    color_input = discord.ui.TextInput(
        label="Color HEX",
        required=True,
        max_length=7,
        placeholder="4F5BDC",
    )
    image_input = discord.ui.TextInput(
        label="Imagen grande (URL, opcional)",
        required=False,
        max_length=500,
        placeholder="https://…",
    )
    button_input = discord.ui.TextInput(
        label="Texto del botón",
        required=True,
        max_length=80,
    )

    def __init__(self, guild_id: int) -> None:
        super().__init__()
        self.guild_id = guild_id
        self.title_input.default = guild_config_get(guild_id, "suggestion_panel_title") or SUGGESTION_PANEL_TITLE_DEFAULT
        self.description_input.default = guild_config_get(guild_id, "suggestion_panel_description") or SUGGESTION_PANEL_DESCRIPTION_DEFAULT
        self.color_input.default = guild_config_get(guild_id, "suggestion_panel_color") or SUGGESTION_PANEL_COLOR_DEFAULT
        self.image_input.default = guild_config_get(guild_id, "suggestion_panel_image") or SUGGESTION_PANEL_IMAGE_DEFAULT
        self.button_input.default = guild_config_get(guild_id, "suggestion_panel_button_label") or SUGGESTION_PANEL_BUTTON_DEFAULT

    async def on_submit(self, interaction: discord.Interaction) -> None:
        color = str(self.color_input).strip().lstrip("#")
        image = str(self.image_input).strip()
        if not re.fullmatch(r"[0-9a-fA-F]{6}", color):
            await interaction.response.send_message(
                "❌ El color debe ser HEX de 6 caracteres, por ejemplo `4F5BDC`.",
                ephemeral=True,
            )
            return
        if image and not re.match(r"^https?://", image, re.IGNORECASE):
            await interaction.response.send_message(
                "❌ La imagen debe ser una URL que empiece por `http://` o `https://`.",
                ephemeral=True,
            )
            return

        guild_config_set(self.guild_id, "suggestion_panel_title", str(self.title_input).strip())
        guild_config_set(self.guild_id, "suggestion_panel_description", str(self.description_input).strip())
        guild_config_set(self.guild_id, "suggestion_panel_color", color.upper())
        guild_config_set(self.guild_id, "suggestion_panel_image", image)
        guild_config_set(self.guild_id, "suggestion_panel_button_label", str(self.button_input).strip())

        await interaction.response.defer(ephemeral=True)
        try:
            await suggestion_ensure_panel(interaction.guild)
            note = "El panel publicado también fue actualizado."
        except Exception:
            traceback.print_exc()
            note = "La configuración se guardó, pero no pude refrescar el panel publicado."
        await interaction.followup.send(f"✅ Panel de sugerencias guardado. {note}", ephemeral=True)


class HeraldoMessagesView(discord.ui.View):
    def __init__(self, guild_id: int, owner_id: int) -> None:
        super().__init__(timeout=900)
        self.guild_id = guild_id
        self.owner_id = owner_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("Este editor de mensajes no es tuyo.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Verificación", style=discord.ButtonStyle.primary, row=0)
    async def verification(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await open_default_message_studio(
            interaction, "verification", self.owner_id, "messages_command"
        )

    @discord.ui.button(label="Sugerencias", style=discord.ButtonStyle.primary, row=0)
    async def suggestions(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await open_default_message_studio(
            interaction, "suggestions", self.owner_id, "messages_command"
        )

    @discord.ui.button(label="Honeypot", style=discord.ButtonStyle.primary, row=0)
    async def honeypot(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await open_default_message_studio(
            interaction, "honeypot", self.owner_id, "messages_command"
        )

    @discord.ui.button(label="DM verificación", style=discord.ButtonStyle.secondary, row=1)
    async def verify_dm(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await open_default_message_studio(
            interaction, "verify_dm", self.owner_id, "messages_command"
        )

    @discord.ui.button(label="Condenas", style=discord.ButtonStyle.secondary, row=1)
    async def condemnations(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await open_default_message_studio(
            interaction, "condemnation", self.owner_id, "messages_command"
        )

    @discord.ui.button(label="Logs", style=discord.ButtonStyle.secondary, row=1)
    async def logs(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await interaction.response.edit_message(
            content=log_template_editor_content("general"),
            embed=log_template_preview(interaction.guild, "general"),
            view=LogTemplateEditorView(self.guild_id, self.owner_id, "general", None, "messages_command"),
        )

    @discord.ui.button(label="Embeds personalizados", style=discord.ButtonStyle.secondary, row=1)
    async def custom_embeds(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        names = embed_names(self.guild_id)
        if names:
            available = ", ".join(f"`{name}`" for name, _ in names[:20])
            text = (
                "🧩 **Embeds personalizados**\n"
                f"Guardados: {available}\n\n"
                "Usa `/embed editar` para abrir uno o `/embed crear` para crear otro."
            )
        else:
            text = "🧩 No hay embeds personalizados guardados. Crea el primero con `/embed crear`."
        await interaction.response.send_message(text, ephemeral=True)

    @discord.ui.button(label="Cerrar", style=discord.ButtonStyle.danger, row=2)
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        self.stop()
        await interaction.response.edit_message(content="Centro de mensajes cerrado.", view=None)


@bot.tree.command(
    name="mensajes",
    description="Editar los paneles y mensajes visuales personalizables de El Heraldo.",
)
@app_commands.default_permissions(manage_guild=True)
@app_commands.guild_only()
async def mensajes_command(interaction: discord.Interaction) -> None:
    await interaction.response.send_message(
        heraldo_messages_command_content(),
        view=HeraldoMessagesView(interaction.guild.id, interaction.user.id),
        ephemeral=True,
    )


mensajes_command.error(verify_command_error)

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