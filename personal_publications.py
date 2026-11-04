"""Registro SQLite de publicaciones personales y operaciones seguras sobre Discord."""
import sqlite3
import discord

def publication_embed(payload, stamp, guild, author, name, render):
    """Use the same author, title and embedded image on send and subsequent edits."""
    if payload.get("kind") == "text":
        embed = discord.Embed(title=name or None, color=discord.Color.blurple())
        if payload.get("image_url"):
            embed.set_image(url=payload["image_url"])
        embed = stamp(embed, guild)
    else:
        embed = render(payload, stamp, guild)
        if embed is None:
            raise ValueError("El embed está vacío.")
        if not embed.title and name:
            embed.title = name
    if author is not None:
        embed.set_author(
            name=getattr(author, "display_name", None) or getattr(author, "name", str(author)),
            icon_url=str(getattr(getattr(author, "display_avatar", None), "url", "") or "") or None,
        )
    return embed


def setup(db):
    db.execute("""CREATE TABLE IF NOT EXISTS personal_publications (
        user_id INTEGER NOT NULL, name TEXT NOT NULL COLLATE NOCASE,
        guild_id INTEGER NOT NULL, channel_id INTEGER NOT NULL,
        message_id INTEGER NOT NULL, author_id INTEGER NOT NULL,
        PRIMARY KEY (guild_id,channel_id,message_id))""")

def list_for(db, user_id, name):
    return db.execute("SELECT guild_id,channel_id,message_id,author_id FROM personal_publications WHERE user_id=? AND name=? COLLATE NOCASE ORDER BY message_id DESC", (user_id,name)).fetchall()

def register(db, user_id, name, guild_id, channel_id, message_id, author_id):
    db.execute("INSERT OR IGNORE INTO personal_publications VALUES (?,?,?,?,?,?)",
               (user_id,name,guild_id,channel_id,message_id,author_id))

def unlink(db, guild_id, channel_id, message_id):
    db.execute("DELETE FROM personal_publications WHERE guild_id=? AND channel_id=? AND message_id=?",
               (guild_id,channel_id,message_id))

async def delete(bot, connect, user_id, name, target=None):
    with connect() as db:
        rows = list_for(db,user_id,name)
    deleted = failed = 0
    for guild_id, channel_id, message_id, _ in rows:
        if target is not None and (guild_id,channel_id,message_id) != tuple(target):
            continue
        guild = bot.get_guild(guild_id)
        channel = guild.get_channel(channel_id) if guild else None
        if channel is None:
            failed += 1
            continue
        try:
            msg = await channel.fetch_message(message_id)
            if msg.author.id != bot.user.id:
                failed += 1
                continue
            await msg.delete()
        except discord.NotFound:
            pass
        except (discord.Forbidden, discord.HTTPException):
            failed += 1
            continue
        with connect() as db:
            unlink(db,guild_id,channel_id,message_id)
        deleted += 1
    return deleted, failed

async def update(bot, connect, user_id, name, payload, stamp, render):
    with connect() as db:
        rows = list_for(db,user_id,name)
    updated = failed = 0
    for guild_id, channel_id, message_id, author_id in rows:
        guild = bot.get_guild(guild_id)
        channel = guild.get_channel(channel_id) if guild else None
        if channel is None:
            failed += 1
            continue
        try:
            msg = await channel.fetch_message(message_id)
            if msg.author.id != bot.user.id:
                failed += 1
                continue
            member = guild.get_member(author_id) or bot.get_user(author_id)
            embed = publication_embed(payload, stamp, guild, member, name, render)
            body = (payload.get("text") or None) if payload.get("kind") == "text" else None
            await msg.edit(content=body, embed=embed, allowed_mentions=discord.AllowedMentions.none())
            updated += 1
        except discord.NotFound:
            with connect() as db:
                unlink(db,guild_id,channel_id,message_id)
        except (discord.Forbidden, discord.HTTPException, ValueError):
            failed += 1
    return updated, failed
