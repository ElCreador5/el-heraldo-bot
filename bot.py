"""
El Heraldo - Bot de verificación, actividad y Miembro de la Semana (Paraíso)

1. VERIFICACIÓN DE EDAD (respaldo de Guardián)
   - Guardián asigna Sin Verificar al entrar y expulsa a los 299s si no verifica.
   - El Heraldo arma un respaldo de 300s (SIN_VERIFICAR_WINDOW): si Guardián falla,
     expulsa directo, sin DM.

2. VERIFICACIÓN DE ORIENTACIÓN (Tentad@ -> rol de orientación)
   - Tentad@ (TENTADO_ROLE_ID) se otorga al pasar la verificación de edad (botón de
     /verify; antes, Invite Tracker).
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

5. VERIFICACIÓN POR BOTÓN (/verify — reemplaza la verificación de Invite Tracker)
   - /verify publica un panel con un botón; quien lo pulsa recibe el rol de
     verificación (por defecto Tentad@) y pierde Sin Verificar. Es una declaración
     de mayoría de edad, no una comprobación.
   - Con la verificación activada, quien no la complete en `timeout` segundos desde
     que entra sufre la acción configurada (expulsar, banear o solo registrar).
   - /verify_config (rol, timeout, acción, activar) y /verify_texts (mensaje del
     panel, texto del botón y mensaje tras verificarse) configuran todo sin redeploy.

6. COPIA DE SEGURIDAD DE LA PLANTILLA (/template_config, /template_sync)
   - Sincroniza la plantilla del servidor (roles, canales y permisos) con su estado
     actual, como una copia de seguridad: cada día, semana o mes, o cada N horas, con
     día y hora a elección. Tras cada copia manda el enlace por mensaje privado (si no
     puede, deja constancia en el canal de logs, sin el enlace).
   - /template_sync la hace al momento y muestra el enlace.

7. HONEYPOT (/honeypot)
   - Canales trampa visibles para todos; quien escriba (y no esté exento) sufre, en orden:
     se le quitan todos los roles menos el de verificación y se le pone el rol de castigo
     (elegible), mientras sus mensajes se purgan en segundo plano (todos, una cantidad o un
     rango de tiempo, sin tope). También hay timeout o solo registrar.
     /honeypot release devuelve sus roles. Aviso fijado automático, exenciones, protección
     contra fallos (pausa si caen varios miembros antiguos) e historial de capturas.

8. PURGA (/purge)
   - Borra mensajes de un usuario sin límites: todos, sus N más recientes o un rango de tiempo
     (desde/hasta), en todo el servidor o en un canal/hilo. "Todos" pide confirmación.

Toda la actividad relevante se reporta como embed en el canal de logs
(LOG_CHANNEL_ID por defecto; cambiable con /heraldo_log_channel).
Persistencia: SQLite (DB_PATH; en Railway, un Volume para sobrevivir deploys).
Permisos requeridos: Administrador (bot personal, confirmado por el usuario).
"""

import asyncio
import json
import os
import re
import sqlite3
import sys
import traceback
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional, Union

import discord
from discord.ext import commands, tasks

# ---------------------------------------------------------------------------
# Configuración
# ---------------------------------------------------------------------------

SIN_VERIFICAR_ROLE_ID = 1549913794296414339  # rol de verificación de edad (Guardián)
SIN_VERIFICAR_WINDOW = timedelta(seconds=300)  # respaldo: Guardián usa 299s, por si falla
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
VERIFICATION_WINDOW = timedelta(minutes=10)

# --- Perfil (/profile): mensajes y racha diaria ---
# Roles cuyos mensajes NO cuentan para el perfil (equivale a "excluded_roles" de MEE6).
# Ejemplo: {123456789012345678, 987654321098765432}
EXCLUDED_ROLE_IDS: set[int] = set()
# Zona horaria que define el "día" de la racha. República Dominicana = UTC-4, sin horario de verano.
STREAK_TZ = timezone(timedelta(hours=-4))
PROFILE_MAX_ROLES = 10  # máximo de roles mostrados en la tarjeta

# --- Miembro de la Semana ---
# Mientras este ID esté en 0, la función queda desactivada. Solo anuncio, sin rol.
MOTW_CHANNEL_ID = 1555606764278382722  # canal por defecto (cambiable con /motw_set_channel)
MOTW_WEEKDAY_DEFAULT = 3  # día por defecto: 0=lunes ... 3=jueves ... 6=domingo
MOTW_HOUR_DEFAULT = 9  # hora por defecto (hora local de STREAK_TZ)
MOTW_WEEKDAY_NAMES = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]

# --- Verificación por botón (/verify): reemplaza la verificación de Invite Tracker ---
# Rol, timeout, acción, textos y activación se guardan en la DB y se cambian con
# /verify_config y /verify_texts; estos son solo los valores por defecto.
VERIFY_BUTTON_ID = "heraldo_verify"
VERIFY_TIMEOUT_DEFAULT = 299  # segundos desde que entra (igual que Invite Tracker)
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
            dm_sent INTEGER DEFAULT 0
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


@bot.event
async def on_ready() -> None:
    db_init()
    honeypot_db_init()
    if not bot.persistent_views:
        bot.add_view(VerifyView())  # el botón de /verify sigue respondiendo tras reinicios
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
    check_pending_verifications.start()
    if get_motw_channel_id():
        if not member_of_the_week_loop.is_running():
            member_of_the_week_loop.start()
    else:
        print("ℹ️ Miembro de la Semana desactivado: configura MOTW_CHANNEL_ID o usa /motw_set_channel.")
    if not template_backup_loop.is_running():
        template_backup_loop.start()
    print(f"El Heraldo conectado como {bot.user}")


@bot.event
async def on_member_join(member: discord.Member) -> None:
    if member.bot:
        return  # los bots no pasan por el flujo de verificación
    if verify_enabled():
        now = datetime.now(timezone.utc)
        db_set_verify_pending(member.id, now)
        asyncio.create_task(schedule_verify_timeout(member.guild.id, member.id, now))
    invite_code = await detect_used_invite(member.guild)
    db_upsert_join(member.id, invite_code)


# ---------------------------------------------------------------------------
# Detección del rol Tentad@ y verificación a los 10 min
# ---------------------------------------------------------------------------

@bot.event
async def on_member_update(before: discord.Member, after: discord.Member) -> None:
    if after.bot:
        return  # los bots no pasan por el flujo de verificación

    before_role_ids = {r.id for r in before.roles}
    after_role_ids = {r.id for r in after.roles}

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
    """Respaldo del Verification Timeout de Guardián (299s). Si a los 300s el
    miembro sigue con Sin Verificar, se expulsa directo — sin DM."""
    guild = bot.get_guild(guild_id)
    if guild is None:
        return
    member = guild.get_member(user_id)
    if member is None:
        db_clear_sin_verificado(user_id)  # Guardián (u otro) ya lo expulsó — nada que hacer
        return

    if SIN_VERIFICAR_ROLE_ID not in {r.id for r in member.roles}:
        db_clear_sin_verificado(user_id)  # ya verificó a tiempo
        return

    db_clear_sin_verificado(user_id)
    try:
        await member.kick(reason="No se verificó (respaldo del timeout de Guardián)")
        await log_embed(
            guild, "👢 Kick — No se verificó",
            f"{member.mention} (`{member.id}`) — no se verificó dentro del tiempo límite. "
            f"(Respaldo: el timeout de Guardián no lo expulsó a tiempo.)",
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
        if row["sin_verificado_at"] is not None:
            sin_verificado_at = datetime.fromisoformat(row["sin_verificado_at"])
            if now >= sin_verificado_at + SIN_VERIFICAR_WINDOW:
                for guild in bot.guilds:
                    if guild.get_member(row["user_id"]):
                        await evaluate_sin_verificado(guild.id, row["user_id"])
                        break
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
        if member.bot:
            continue
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
# Verificación por botón (/verify) — reemplaza la verificación de Invite Tracker
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


async def handle_verify_click(interaction: discord.Interaction) -> None:
    guild = interaction.guild
    member = interaction.user
    if guild is None or not isinstance(member, discord.Member):
        await interaction.response.send_message("Esto solo funciona dentro del servidor.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True, thinking=True)

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

    await interaction.followup.send(get_verify_success_text(), ephemeral=True)
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
            content=get_verify_panel_text(),
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
        f"**Timeout:** {get_verify_timeout()} s\n"
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
            content=get_verify_panel_text(),
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


@bot.tree.command(name="verify_texts", description="Editar el mensaje del panel, el texto del botón y el mensaje tras verificarse.")
@discord.app_commands.checks.has_permissions(manage_guild=True)
@discord.app_commands.guild_only()
async def verify_texts(interaction: discord.Interaction) -> None:
    await interaction.response.send_modal(VerifyTextsModal())


@bot.tree.command(name="verify_config", description="Ver o cambiar la configuración de la verificación por botón.")
@discord.app_commands.describe(
    rol="Rol que se otorga al verificarse",
    timeout="Segundos para verificarse desde que entra (30-3600)",
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
    timeout: Optional[discord.app_commands.Range[int, 30, 3600]] = None,
    accion: Optional[discord.app_commands.Choice[str]] = None,
    activado: Optional[bool] = None,
) -> None:
    guild = interaction.guild
    if rol is None and timeout is None and accion is None and activado is None:
        await interaction.response.send_message(verify_config_summary(guild), ephemeral=True)
        return

    # 1) Validar todo antes de guardar nada.
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
    if timeout is not None:
        db_meta_set("verify_timeout", str(timeout))
        changes.append(f"timeout → {timeout} s")
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


def get_template_interval() -> int:
    return _meta_int("template_interval_hours", TEMPLATE_INTERVAL_DEFAULT)


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
    return f"Cada {get_template_interval()} h"


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
        return (base + timedelta(hours=get_template_interval())).astimezone(STREAK_TZ)
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
        return now_utc >= datetime.fromisoformat(last) + timedelta(hours=get_template_interval())
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
    cada_horas="Cada cuántas horas, 1-720 (frecuencia por intervalo)",
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
    cada_horas: Optional[discord.app_commands.Range[int, 1, 720]] = None,
    enviar_a: Optional[discord.User] = None,
) -> None:
    guild = interaction.guild
    now = datetime.now(timezone.utc)
    if all(v is None for v in (frecuencia, hora, dia_semana, dia_mes, cada_horas, enviar_a)):
        await interaction.response.send_message(template_config_summary(now), ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True)

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
    if cada_horas is not None:
        db_meta_set("template_interval_hours", str(cada_horas))
        changes.append(f"intervalo → {cada_horas} h")
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
    if punish_id and any(r.id == punish_id for r in message.author.roles):
        return  # los castigados por el honeypot no suman

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
    """Guarda los roles quitados para poder devolverlos con /honeypot release."""
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


def hp_warning_text() -> str:
    return hp_meta_get("honeypot_warning_text") or HONEYPOT_WARNING_TEXT_DEFAULT


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

def hp_warning_embed() -> discord.Embed:
    return discord.Embed(
        title="⚠️ No escribas en este canal",
        description=hp_warning_text(),
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
            await existing.edit(embed=hp_warning_embed())
            if not existing.pinned:
                await existing.pin()
            return None
        message = await channel.send(embed=hp_warning_embed())
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


async def _collect_user_messages(ch, user_id: int, after, before, limit: int | None) -> list[int]:
    ids: list[int] = []
    kwargs = {"limit": None, "after": after, "before": before}
    if limit is not None:
        kwargs["oldest_first"] = False  # para quedarnos con los más recientes
    async for m in ch.history(**kwargs):
        if m.author.id == user_id:
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
                ids = await _collect_user_messages(ch, user_id, after, before, limit)
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
    title: str = "🧹 Purga completada",
) -> PurgeResult | None:
    """Ejecuta una purga con control de duplicados y reporta el resultado en el log."""
    key = (guild.id, user.id)
    if key in _purge_running:
        return None
    _purge_running.add(key)
    try:
        result = await purge_user_messages(
            guild, user.id, channel=channel, after=after, before=before, limit=limit, progress=progress
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


async def hp_punish(member: discord.Member, action: str) -> tuple[bool, str]:
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
            punish_role = guild.get_role(hp_punish_role_id())
            if punish_role is None:
                return False, "No hay rol de castigo configurado (usa /honeypot config rol_castigo)"
            problem = hp_role_problem(punish_role, guild)
            if problem:
                return False, f"El rol de castigo {problem}"

            # La purga no tiene tope y puede tardar: arranca en segundo plano a la vez que los
            # roles, para que el castigado quede neutralizado de inmediato.
            notes: list[str] = []
            purge_note = hp_start_purge(member)
            if purge_note:
                notes.append(purge_note)
            verify_id = get_verify_role_id()
            keep_ids = (verify_id, SIN_VERIFICAR_ROLE_ID, punish_role.id)  # Sin Verificar se conserva: así el respaldo de 300 s lo expulsa
            removed = [r for r in member.roles if r.is_assignable() and r.id not in keep_ids]
            removed_ids = {r.id for r in removed}
            kept = [
                r for r in member.roles
                if not r.is_default() and r.id not in removed_ids and r.id != punish_role.id
            ]
            # Un solo edit cambia el set completo de roles: sin estado intermedio sin castigo.
            try:
                await member.edit(roles=kept + [punish_role], reason=reason)
            except discord.Forbidden:
                return False, "; ".join(notes + ["faltan permisos para cambiar roles (Gestionar roles)"])
            except discord.HTTPException as e:
                return False, "; ".join(notes + [f"error al cambiar roles: `{e}`"])
            hp_save_punished(member.id, [r.id for r in removed])
            notes.append(f"{len(removed)} rol(es) quitado(s)")
            notes.append(f"rol {punish_role.mention} aplicado")
            if any(r.id == SIN_VERIFICAR_ROLE_ID for r in member.roles):
                notes.append("sigue sin verificar: el respaldo de verificación lo expulsará")
            db_zero_week_messages(member.id)  # un castigado no puede ganar el Miembro de la Semana
            return True, "; ".join(notes)
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

    success, note = await hp_punish(member, action)
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
    rol_castigo="Rol que se le pone al castigado (se le quitan los demás, menos el de verificación)",
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


@honeypot_group.command(name="release", description="Liberar a un castigado: devuelve sus roles y quita el rol de castigo.")
@discord.app_commands.describe(miembro="Miembro castigado por el honeypot")
async def honeypot_release(interaction: discord.Interaction, miembro: discord.Member) -> None:
    guild = interaction.guild
    punish_role = guild.get_role(hp_punish_role_id())
    saved = hp_get_punished(miembro.id)
    if saved is None and not (punish_role and punish_role in miembro.roles):
        await interaction.response.send_message("Ese miembro no está castigado por el honeypot.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True)
    restore: list[discord.Role] = []
    lost = 0
    for rid in saved or []:
        role = guild.get_role(rid)
        if role is not None and role.is_assignable():
            restore.append(role)
        else:
            lost += 1  # el rol se borró o el bot ya no puede asignarlo
    current = [
        r for r in miembro.roles
        if not r.is_default() and (punish_role is None or r.id != punish_role.id)
    ]
    new_roles = list({r.id: r for r in current + restore}.values())
    try:
        await miembro.edit(roles=new_roles, reason=f"Honeypot: liberado por {interaction.user}")
    except discord.HTTPException as e:
        await interaction.followup.send(f"❌ No pude cambiar sus roles: `{e}`", ephemeral=True)
        return
    hp_clear_punished(miembro.id)
    text = f"✅ {miembro.mention} liberado: {len(restore)} rol(es) devuelto(s)" + (
        f", {lost} no se pudieron devolver (borrados o fuera de alcance)." if lost else "."
    )
    await interaction.followup.send(text, ephemeral=True)
    await log_embed(guild, "🍯 Miembro liberado", f"{interaction.user.mention} liberó a {miembro.mention}. {text}")


@honeypot_group.error
async def honeypot_group_error(interaction: discord.Interaction, error: discord.app_commands.AppCommandError) -> None:
    await verify_command_error(interaction, error)


bot.tree.add_command(honeypot_group)

# ---------------------------------------------------------------------------
# 8. /purge — limpieza individual de mensajes de un usuario
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
    todos="Borrar TODOS sus mensajes (no se combina con cantidad ni rango)",
    cantidad="Borrar solo sus N mensajes más recientes",
    desde="Inicio del rango: hace cuánto (30m, 12h, 2d, 1d 12h…)",
    hasta="Fin del rango: hace cuánto (por defecto, ahora)",
    canal="Limitar a un canal o hilo (por defecto, todo el servidor)",
)
@discord.app_commands.checks.has_permissions(manage_messages=True)
@discord.app_commands.guild_only()
async def purge_command(
    interaction: discord.Interaction,
    usuario: discord.User,
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

    parts: list[str] = []
    if todos:
        parts.append("**todos** sus mensajes")
    if cantidad is not None:
        parts.append(f"sus **{cantidad}** mensajes más recientes")
    if desde is not None or hasta is not None:
        parts.append(f"rango: desde hace {desde or '—'} hasta hace {hasta or '0'}")
    where = canal.mention if canal is not None else "todo el servidor"
    scope_text = " · ".join(parts) + f" · en {where}"

    if todos:
        view = PurgeConfirmView(interaction.user.id)
        await interaction.response.send_message(
            f"⚠️ Vas a borrar **todos** los mensajes de {usuario.mention} en {where}. No se puede deshacer.",
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
