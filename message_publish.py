"""Single-message publishing for /setup -> Mensajes -> Crear mensaje.

Shares the same footer renderer and mention policy as ScheduledMessages.
No database writes or background retries for immediate messages.
"""
from __future__ import annotations
import discord
import message_payload
from autofeed_embed_builder import render, has_content
from message_autofeeds import referenced_mentions


def create_payload(host, guild, job):
    text = (job.get("text") or "").strip()
    data = job.get("embed")
    if not text and not has_content(data):
        raise ValueError("empty")
    allowed = referenced_mentions(guild, job)
    if job.get("role"):
        role = guild.get_role(job["role"])
        if role is None or not role.mentionable:
            raise ValueError("role")
        if role.mention not in text:
            text = (text + "\n" + role.mention).strip()
    visual = render(data, host["stamp_embed"], guild)
    if visual is None:
        # Every El Heraldo message must carry its existing global footer.
        visual = host["stamp_embed"](discord.Embed(), guild)
    return {
        "content": text or None,
        "embeds": message_payload.TemplateEmbeds([visual]),
        "allowed_mentions": discord.AllowedMentions(
            everyone=False, users=False, roles=allowed,
        ),
    }


async def publish_message(host, guild, channel, job):
    if channel.guild.id != guild.id:
        raise ValueError("invalid_channel")
    me = guild.me
    perms = channel.permissions_for(me) if me is not None else discord.Permissions.none()
    if not (perms.view_channel and perms.send_messages and perms.embed_links):
        raise ValueError("permissions")
    payload = create_payload(host, guild, job)
    # No retries on ambiguous HTTP errors: could otherwise duplicate the post.
    return await channel.send(**payload)
