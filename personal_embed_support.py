"""Dependencias mínimas del editor personal; aisladas de Anuncios y AutoMod."""
import functools
import re
import discord

def current_locale():
    return "es-419"

def guild_context(func):
    @functools.wraps(func)
    async def wrapped(*args, **kwargs):
        return await func(*args, **kwargs)
    return wrapped

async def respond_error(interaction, reason):
    message = "No tienes permisos para esta acción." if reason == "denied" else "Los datos del embed no son válidos."
    if interaction.response.is_done():
        await interaction.followup.send(message, ephemeral=True)
    else:
        await interaction.response.send_message(message, ephemeral=True)

def resolve_inline_embed_names(guild, content):
    if not guild:
        return content
    def substitute(match):
        name = match.group(1)
        channels = [c for c in guild.channels if c.name.casefold() == name.casefold()]
        return f"<#{channels[0].id}>" if len(channels) == 1 else match.group(0)
    return re.sub(r"(?<!\\w)#([a-zA-Z0-9_\-]+)", substitute, content)

def referenced_mentions(guild, payload):
    # No habilita menciones de masa ni omite controles de Discord.
    return None

def editor_panel_kwargs(parent, guild):
    return parent.kwargs(guild)
