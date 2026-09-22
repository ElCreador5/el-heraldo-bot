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
import sqlite3
from datetime import datetime, timedelta, timezone

import discord
from discord.ext import commands, tasks

# ---------------------------------------------------------------------------
# Configuración
# ---------------------------------------------------------------------------

GUILD_ID = 0  # TODO: ID del servidor "Paraíso"
TENTADO_ROLE_ID = 1510692050889085142
EVAL_ROLE_IDS = {
    1522877846026981396,  # Bisex-🚻
    1522875944371486780,  # Gay🥒
    1522877558893580298,  # Curios@ 👀
    1522876908935581846,  # Chico + Hetero 🍆
    1549502828563665056,  # Chica + Hetero 🍓
    522878005104345218,   # Chica Trans 🌶️
    1549500856515166238,  # Chico Trans 🍓
}
RECOVERY_CHANNEL_ID = 1522863826545016913  # canal donde se genera el invite de recuperación
VERIFICATION_WINDOW = timedelta(minutes=10)

DM_TEXT = (
    "La verificación no te salva del todo, se expulsará a quienes no seleccionen "
    "ningún de estos <#{channel_id}> o no den señal de ser un alma genuina (humana). "
    "Tendrás otro chance de volver a intentar {invite_url}"
)

DB_PATH = "heraldo.db"

intents = discord.Intents.default()
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix="!heraldo ", intents=intents)

# invite_cache[guild_id][invite_code] = uses
invite_cache: dict[int, dict[str, int]] = {}


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
    check_pending_verifications.start()
    print(f"El Heraldo conectado como {bot.user}")


@bot.event
async def on_member_join(member: discord.Member) -> None:
    invite_code = await detect_used_invite(member.guild)
    db_upsert_join(member.id, invite_code)


# ---------------------------------------------------------------------------
# Detección del rol Tentad@ y verificación a los 10 min
# ---------------------------------------------------------------------------

@bot.event
async def on_member_update(before: discord.Member, after: discord.Member) -> None:
    before_role_ids = {r.id for r in before.roles}
    after_role_ids = {r.id for r in after.roles}

    if TENTADO_ROLE_ID in after_role_ids and TENTADO_ROLE_ID not in before_role_ids:
        now = datetime.now(timezone.utc)
        db_set_tentado(after.id, now)
        asyncio.create_task(schedule_check(after.guild.id, after.id, now))


async def schedule_check(guild_id: int, user_id: int, tentado_at: datetime) -> None:
    delay = (tentado_at + VERIFICATION_WINDOW - datetime.now(timezone.utc)).total_seconds()
    if delay > 0:
        await asyncio.sleep(delay)
    await evaluate_member(guild_id, user_id)


@tasks.loop(minutes=2)
async def check_pending_verifications() -> None:
    """Red de seguridad: si el bot se reinició, retoma verificaciones pendientes
    cuyo timer ya venció o está por vencer."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT user_id, tentado_at FROM members WHERE tentado_at IS NOT NULL"
    ).fetchall()
    conn.close()

    now = datetime.now(timezone.utc)
    for row in rows:
        tentado_at = datetime.fromisoformat(row["tentado_at"])
        if now >= tentado_at + VERIFICATION_WINDOW:
            for guild in bot.guilds:
                if guild.get_member(row["user_id"]):
                    await evaluate_member(guild.id, row["user_id"])
                    break


async def evaluate_member(guild_id: int, user_id: int) -> None:
    guild = bot.get_guild(guild_id)
    if guild is None:
        return
    member = guild.get_member(user_id)
    if member is None:
        db_clear_tentado(user_id)  # ya no está, nada que hacer
        return

    role_ids = {r.id for r in member.roles}
    if role_ids & EVAL_ROLE_IDS:
        db_clear_tentado(user_id)  # se verificó a tiempo
        return

    await expel(member)


# ---------------------------------------------------------------------------
# Expulsión + DM condicional
# ---------------------------------------------------------------------------

async def expel(member: discord.Member) -> None:
    row = db_get(member.id)
    dm_sent_before = bool(row["dm_sent"]) if row else False

    if not dm_sent_before:
        await send_recovery_dm(member)
        db_mark_dm_sent(member.id)

    db_clear_tentado(member.id)
    try:
        await member.kick(reason="No seleccionó rol de verificación en 10 min")
    except discord.Forbidden:
        print(f"Sin permisos para expulsar a {member.id}")


async def send_recovery_dm(member: discord.Member) -> None:
    channel = member.guild.get_channel(RECOVERY_CHANNEL_ID)
    invite_url = ""
    if channel is not None:
        try:
            invite = await channel.create_invite(
                max_uses=1, unique=True, reason="Recuperación tras expulsión de Heraldo"
            )
            invite_url = invite.url
        except discord.Forbidden:
            print("Sin permisos para crear invite de recuperación")

    text = DM_TEXT.format(channel_id=RECOVERY_CHANNEL_ID, invite_url=invite_url)
    try:
        await member.send(text)
    except discord.Forbidden:
        print(f"No se pudo enviar DM a {member.id} (DMs cerrados)")


# ---------------------------------------------------------------------------

if __name__ == "__main__":
    bot.run("TU_TOKEN_AQUI")
