"""
El Heraldo - Bot de expulsión por falta de verificación de rol (Paraíso)

Flujo:
1. Invite Tracker otorga el rol Tentad@ (TENTADO_ROLE_ID) al entrar un miembro.
2. El Heraldo detecta ese rol vía on_member_update y arma un timer de 10 min.
3. Si al vencer el timer el miembro sigue sin ninguno de los EVAL_ROLE_IDS:
   - 1ra vez (dm_sent=False): DM con explicación + invite de uso único, luego kick.
   - 2da vez (dm_sent=True):
       - Si el invite con el que reingresó == su invite de entrada original -> se
         le da otra oportunidad (mismo flujo que 1ra vez).
       - Si no -> kick directo, sin DM.
4. El tracking de invites es por usuario (no un invite genérico), comparando el
   contador de usos de cada invite del servidor antes/después de cada join.

Persistencia: SQLite (heraldo.db) para sobrevivir reinicios del bot.
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

GUILD_ID = 0  # TODO: ID del servidor "Paraíso"
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
LOG_CHANNEL_ID = 1549052747117240381  # canal donde El Heraldo reporta su actividad
VERIFICATION_WINDOW = timedelta(minutes=10)

# --- Perfil (/profile): mensajes y racha diaria ---
# Roles cuyos mensajes NO cuentan para el perfil (equivale a "excluded_roles" de MEE6).
# Ejemplo: {123456789012345678, 987654321098765432}
EXCLUDED_ROLE_IDS: set[int] = set()
# Zona horaria que define el "día" de la racha. República Dominicana = UTC-4, sin horario de verano.
STREAK_TZ = timezone(timedelta(hours=-4))
PROFILE_MAX_ROLES = 10  # máximo de roles mostrados en la tarjeta

# --- Miembro de la Semana ---
# Mientras estos dos IDs estén en 0, la función queda desactivada.
MOTW_CHANNEL_ID = 0  # TODO: canal donde se anuncia al Miembro de la Semana
MOTW_ROLE_ID = 0  # TODO: rol "Miembro de la Semana"
MOTW_WEEKDAY = 3  # día del anuncio: 0=lunes ... 3=jueves ... 6=domingo
MOTW_HOUR = 9  # hora del anuncio (hora local de STREAK_TZ)

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

DB_PATH = "heraldo.db"

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
    """Reporta actividad de El Heraldo en LOG_CHANNEL_ID como embed. Nunca debe
    tumbar el flujo principal si falla (canal no encontrado, sin permisos, etc.)."""
    print(f"{title} — {description}")
    if guild is None:
        return
    channel = guild.get_channel(LOG_CHANNEL_ID)
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
    for guild in bot.guilds:
        await refresh_invite_cache(guild)
        bot.tree.copy_global_to(guild=guild)
        await bot.tree.sync(guild=guild)  # sync por guild: propagación instantánea
    check_pending_verifications.start()
    if MOTW_CHANNEL_ID and MOTW_ROLE_ID:
        if not member_of_the_week_loop.is_running():
            member_of_the_week_loop.start()
    else:
        print("ℹ️ Miembro de la Semana desactivado: configura MOTW_CHANNEL_ID y MOTW_ROLE_ID.")
    print(f"El Heraldo conectado como {bot.user}")


@bot.event
async def on_member_join(member: discord.Member) -> None:
    if member.bot:
        return  # los bots no pasan por el flujo de verificación
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
        "SELECT user_id, tentado_at, sin_verificado_at FROM members "
        "WHERE tentado_at IS NOT NULL OR sin_verificado_at IS NOT NULL"
    ).fetchall()
    conn.close()

    now = datetime.now(timezone.utc)
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

    channel = member.guild.get_channel(LOG_CHANNEL_ID)
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

    channel = guild.get_channel(LOG_CHANNEL_ID)
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
async def profile(interaction: discord.Interaction, user: Optional[discord.Member] = None) -> None:
    target = user or interaction.user
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
    """Último momento programado (MOTW_WEEKDAY a las MOTW_HOUR:00, hora local)
    que ya pasó respecto a `now`."""
    days_back = (now.weekday() - MOTW_WEEKDAY) % 7
    scheduled = (now - timedelta(days=days_back)).replace(
        hour=MOTW_HOUR, minute=0, second=0, microsecond=0
    )
    if scheduled > now:
        scheduled -= timedelta(days=7)
    return scheduled


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


async def announce_member_of_the_week() -> None:
    channel = bot.get_channel(MOTW_CHANNEL_ID)
    if channel is None:
        print("⚠️ Miembro de la Semana: no encontré MOTW_CHANNEL_ID.")
        return
    guild = channel.guild
    role = guild.get_role(MOTW_ROLE_ID)
    if role is None:
        await log_embed(guild, "⚠️ Miembro de la Semana", "No encontré el rol de MOTW_ROLE_ID; no se anunció a nadie (los contadores se conservan).", discord.Color.dark_red())
        return

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
        except discord.HTTPException:
            print("No se pudo escribir en el canal de Miembro de la Semana")
        db_reset_week()
        return

    winner, winner_count = ranking[0]

    # Quitar el rol a quien lo tenga (el ganador anterior) y dárselo al nuevo.
    errors: list[str] = []
    for holder in list(role.members):
        if holder.id == winner.id:
            continue
        try:
            await holder.remove_roles(role, reason="Ya no es el Miembro de la Semana")
        except discord.HTTPException as e:
            errors.append(f"Quitar el rol a {holder.mention}: `{e}`")
    if role not in winner.roles:
        try:
            await winner.add_roles(role, reason="Miembro de la Semana")
        except discord.HTTPException as e:
            errors.append(f"Dar el rol a {winner.mention}: `{e}`")
    if errors:
        await log_embed(
            guild, "⚠️ Miembro de la Semana — problemas con el rol",
            "\n".join(errors) + "\n\nRevisa que el rol del Heraldo esté por encima del rol de Miembro de la Semana.",
            discord.Color.dark_red(),
        )

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
        title="👑 Miembro de la Semana",
        description=description,
        color=discord.Color.gold(),
        timestamp=datetime.now(timezone.utc),
    )
    embed.set_thumbnail(url=winner.display_avatar.url)
    embed.set_footer(text="Paraíso Morboso 2026 © - El Heraldo 🪽")
    try:
        await channel.send(embed=embed)
    except discord.HTTPException:
        print("No se pudo escribir en el canal de Miembro de la Semana")

    db_reset_week()  # contadores de la nueva semana en cero (para TODOS, no solo el top)


# ---------------------------------------------------------------------------

if __name__ == "__main__":
    token = os.environ.get("DISCORD_TOKEN")
    if not token:
        raise RuntimeError(
            "Falta la variable de entorno DISCORD_TOKEN. Configúrala en Railway "
            "(Variables del servicio) antes de desplegar."
        )
    bot.run(token)
