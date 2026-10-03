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

Toda la actividad relevante se reporta como embed en el canal de logs
(LOG_CHANNEL_ID por defecto; cambiable con /heraldo_log_channel).
Persistencia: SQLite (DB_PATH; en Railway, un Volume para sobrevivir deploys).
Permisos requeridos: Administrador (bot personal, confirmado por el usuario).
"""

import asyncio
import os
import sqlite3
import traceback
from datetime import datetime, timedelta, timezone
from typing import Optional

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
    if not bot.persistent_views:
        bot.add_view(VerifyView())  # el botón de /verify sigue respondiendo tras reinicios
    for guild in bot.guilds:
        await refresh_invite_cache(guild)
        bot.tree.copy_global_to(guild=guild)
        await bot.tree.sync(guild=guild)  # sync por guild: propagación instantánea
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
    """Devuelve 'verificado', 'expulsado' o 'ausente'/'sin-guild'."""
    guild = bot.get_guild(guild_id)
    if guild is None:
        return "sin-guild"
    member = guild.get_member(user_id)
    if member is None:
        db_clear_tentado(user_id)  # ya no está, nada que hacer
        return "ausente"

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

if __name__ == "__main__":
    token = os.environ.get("DISCORD_TOKEN")
    if not token:
        raise RuntimeError(
            "Falta la variable de entorno DISCORD_TOKEN. Configúrala en Railway "
            "(Variables del servicio) antes de desplegar."
        )
    bot.run(token)
