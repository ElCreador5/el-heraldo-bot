import os
import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.members = True  # necesario para detectar cambios de rol

bot = commands.Bot(command_prefix="!", intents=intents)

# IDs de roles del servidor (Server Settings > Roles > clic derecho > Copiar ID)
ROLE_IDS = {
    "Chico+Hetero": 1522876908935581846,
    "Chica+Hetero": 1549502828563665056,
    "Hetero":       1549549503592267908,
    "Chico":        1549506512391770193,
    "Chica":        1549506426492420147,
}

# Combos activos: (orientación, género) -> nombre clave en ROLE_IDS
COMBOS = {
    ("Hetero", "Chico"): "Chico+Hetero",
    ("Hetero", "Chica"): "Chica+Hetero",
}

ORIENTACIONES = ["Hetero"]
GENEROS = ["Chico", "Chica"]


@bot.event
async def on_ready():
    print(f"Conectado como {bot.user}")


@bot.event
async def on_member_update(before: discord.Member, after: discord.Member):
    before_ids = {r.id for r in before.roles}
    after_ids = {r.id for r in after.roles}
    if before_ids == after_ids:
        return  # no cambió nada de roles

    guild = after.guild

    orientacion_actual = next(
        (o for o in ORIENTACIONES if ROLE_IDS[o] in after_ids), None
    )
    genero_actual = next(
        (g for g in GENEROS if ROLE_IDS[g] in after_ids), None
    )

    for (orient, gen), combo_key in COMBOS.items():
        combo_role = guild.get_role(ROLE_IDS[combo_key])
        if combo_role is None:
            continue  # el rol no existe o el ID está mal

        tiene_combo = combo_role in after.roles
        deberia_tener = (orientacion_actual == orient and genero_actual == gen)

        if deberia_tener and not tiene_combo:
            await after.add_roles(combo_role)
        elif not deberia_tener and tiene_combo:
            await after.remove_roles(combo_role)


bot.run(os.environ["DISCORD_TOKEN"])
