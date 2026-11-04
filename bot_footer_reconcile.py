"""Actualización retroactiva no destructiva de footers del bot."""
from __future__ import annotations
import asyncio
import hashlib
import discord


async def reconcile_existing_bot_footers(bot, stamp_embed, marker_get, marker_set):
    """Revisa canales visibles e hilos activos una vez por identidad del bot.

    Solo edita los embeds ricos de mensajes del propio bot; deja intactos
    contenido, adjuntos, componentes y mensajes de otros autores. Cada canal
    completado se marca en la SQLite para no repetirlo al reiniciar.
    """
    user = bot.user
    if user is None:
        return {"scanned": 0, "updated": 0, "errors": 0}
    avatar = str(getattr(getattr(user, "display_avatar", None), "url", ""))
    identity = hashlib.sha256(f"{user.id}|{user.name}|{avatar}|v1".encode("utf-8")).hexdigest()
    scanned = updated = errors = 0
    for guild in tuple(bot.guilds):
        seen = set()
        channels = list(getattr(guild, "text_channels", ())) + list(getattr(guild, "threads", ()))
        for channel in channels:
            if channel.id in seen or not hasattr(channel, "history"):
                continue
            seen.add(channel.id)
            key = f"footer_identity:v1:{user.id}:{guild.id}:{channel.id}"
            try:
                if marker_get(key) == identity:
                    continue
                member = getattr(guild, "me", None)
                if member is not None and hasattr(channel, "permissions_for"):
                    permissions = channel.permissions_for(member)
                    if not (permissions.view_channel and permissions.read_message_history):
                        continue
                incomplete = False
                async for message in channel.history(limit=None):
                    scanned += 1
                    if getattr(getattr(message, "author", None), "id", None) != user.id:
                        continue
                    embeds = message.embeds
                    if not embeds or any(e.type != "rich" for e in embeds):
                        continue  # No convertir vistas previas automáticas de enlaces.
                    revised = [stamp_embed(e.copy(), guild) for e in embeds]
                    old = [(e.footer.text, str(e.footer.icon_url or "")) for e in embeds]
                    new = [(e.footer.text, str(e.footer.icon_url or "")) for e in revised]
                    if old == new:
                        continue
                    if sum(len(e) for e in revised) > 6000:
                        incomplete = True
                        errors += 1
                        continue
                    try:
                        await message.edit(embeds=revised)
                        updated += 1
                        await asyncio.sleep(0.25)
                    except (discord.Forbidden, discord.NotFound, discord.HTTPException):
                        incomplete = True
                        errors += 1
                if not incomplete and bot.user is not None and (
                    bot.user.name == user.name and
                    str(getattr(getattr(bot.user, "display_avatar", None), "url", "")) == avatar
                ):
                    marker_set(key, identity)
            except (discord.Forbidden, discord.NotFound, discord.HTTPException, OSError, ValueError):
                errors += 1
    print(f"FOOTER_RECONCILE status=FINISHED scanned={scanned} updated={updated} errors={errors}", flush=True)
    return {"scanned": scanned, "updated": updated, "errors": errors}
