"""Archivo verificable en el canal privado existente; no elimina contenido.

El ledger guarda referencias/hashes, no credenciales ni adjuntos. Un envío cuyo
resultado se desconoce permanece pendiente: nunca se reenvía automáticamente.
"""
from heraldo_i18n import text as _t, guild_context as _i18n_context, use_guild as _i18n_guild
import asyncio
from contextlib import closing
import hashlib
import io
import json
import sqlite3

import discord

ARCHIVE_CHANNEL_NAME = "archivo-evidencias"
ARCHIVE_CHANNEL_TOPIC = "El Heraldo · Archivo privado de evidencias verificadas"
_archive_channel_locks: dict[int, asyncio.Lock] = {}


async def ensure_private_archive(guild, *, log_channel_id: int = 0):
    """Aisla los archivos técnicos y no utiliza nunca el canal de registros."""
    if guild is None or guild.me is None:
        return None
    lock = _archive_channel_locks.setdefault(guild.id, asyncio.Lock())
    async with lock:
        matches = [
            ch for ch in guild.text_channels
            if isinstance(ch, discord.TextChannel) and ch.topic == ARCHIVE_CHANNEL_TOPIC
        ]
        if matches:
            if len(matches) != 1:
                return None
            ch = matches[0]
            if (ch.id == log_channel_id or not ch.is_nsfw()
                    or ch.overwrites_for(guild.default_role).view_channel is not False
                    or not private_channel(guild, ch)):
                return None
            return ch
        if not guild.me.guild_permissions.manage_channels:
            return None
        overrides = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            guild.me: discord.PermissionOverwrite(
                view_channel=True, send_messages=True, attach_files=True,
                read_message_history=True,
            ),
        }
        try:
            ch = await guild.create_text_channel(
                ARCHIVE_CHANNEL_NAME, topic=ARCHIVE_CHANNEL_TOPIC,
                overwrites=overrides, nsfw=True,
                reason="Separar evidencias técnicas de los registros de moderación.",
            )
        except (discord.Forbidden, discord.HTTPException):
            return None
        if (ch.id == log_channel_id or not ch.is_nsfw()
                or ch.overwrites_for(guild.default_role).view_channel is not False
                or not private_channel(guild, ch)):
            return None
        return ch


@_i18n_context
def private_channel(guild, channel):
    if not isinstance(channel, discord.TextChannel) or guild.me is None:
        return False
    if channel.permissions_for(guild.default_role).view_channel:
        return False
    for role in guild.roles:
        if role.is_default() or role.permissions.administrator:
            continue
        if getattr(getattr(role, 'tags', None), 'bot_id', None) == guild.me.id:
            continue
        if channel.permissions_for(role).view_channel:
            return False
    for target, overwrite in channel.overwrites.items():
        if isinstance(target, discord.Member) and overwrite.view_channel is True:
            if target.id != guild.me.id and not target.guild_permissions.administrator:
                return False
    p = channel.permissions_for(guild.me)
    return bool(p.view_channel and p.send_messages and p.attach_files and p.read_message_history)


@_i18n_context
def snapshot(message):
    # Estos formatos contienen recursos que aún no se copian íntegramente.
    if message.stickers or message.poll or getattr(message, 'message_snapshots', []):
        raise ValueError('unsupported_message_resources')
    return {
        'schema': 1, 'guild_id': message.guild.id, 'channel_id': message.channel.id,
        'message_id': message.id, 'author_id': message.author.id,
        'author': str(message.author), 'content': message.content,
        'created_at': message.created_at.isoformat(),
        'edited_at': message.edited_at.isoformat() if message.edited_at else None,
        'type': int(message.type.value), 'flags': message.flags.value,
        'embeds': [e.to_dict() for e in message.embeds],
        'components': [c.to_dict() for c in message.components],
        'attachments': [{'id': a.id, 'filename': a.filename, 'size': a.size,
                         'content_type': a.content_type, 'description': a.description}
                        for a in message.attachments],
    }


def encoded(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True).encode('utf-8')


def ledger(db_path, key, operation, value=None):
    with closing(sqlite3.connect(db_path, timeout=2)) as conn, conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS evidence_archive_v1 (
            evidence_key TEXT PRIMARY KEY, status TEXT NOT NULL,
            receipts TEXT NOT NULL DEFAULT '[]')''')
        if operation == 'claim':
            changed = conn.execute(
                "INSERT OR IGNORE INTO evidence_archive_v1(evidence_key,status) VALUES (?, 'pending')",
                (key,)).rowcount
            row = conn.execute('SELECT status, receipts FROM evidence_archive_v1 WHERE evidence_key=?',
                               (key,)).fetchone()
            return bool(changed), row[0], json.loads(row[1])
        conn.execute('UPDATE evidence_archive_v1 SET status=?, receipts=? WHERE evidence_key=?',
                     (operation, json.dumps(value), key))


@_i18n_context
async def verify(channel, receipts):
    if not receipts:
        return False
    for receipt in receipts:
        if receipt.get('channel_id') != channel.id:
            return False
        copy = await channel.fetch_message(receipt['message_id'])
        if copy.author.id != channel.guild.me.id or len(copy.attachments) != 1:
            return False
        attachment = copy.attachments[0]
        if attachment.size != receipt['size']:
            return False
        data = await attachment.read(use_cached=False)
        if len(data) != receipt['size'] or hashlib.sha256(data).hexdigest() != receipt['sha256']:
            return False
    return True


@_i18n_context
async def preserve(message, archive_channel, db_path):
    """Devuelve referencia solo tras lectura íntegra. Los errores los maneja el llamador."""
    guild = message.guild
    if (archive_channel is None or archive_channel.topic != ARCHIVE_CHANNEL_TOPIC
            or not archive_channel.is_nsfw()
            or not private_channel(guild, archive_channel)
            or message.channel.id == archive_channel.id):
        return None
    metadata = snapshot(message)
    fingerprint = hashlib.sha256(encoded(metadata)).hexdigest()
    # El destino forma parte de la clave: los recibos heredados del canal
    # de logs no bloquean un nuevo archivado en el canal privado separado.
    key = f'{guild.id}:{message.channel.id}:{message.id}:{fingerprint}:{archive_channel.id}'
    claimed, status, receipts = await asyncio.to_thread(ledger, db_path, key, 'claim')
    if not claimed:
        if status != 'complete' or not await verify(archive_channel, receipts):
            return None
        return f'https://discord.com/channels/{guild.id}/{archive_channel.id}/{receipts[-1]["message_id"]}'

    # Un archivo por envío: admite diez adjuntos más el manifiesto sin truncarlos.
    # Se limita memoria por archivo; no se descarga uno que Discord no pueda copiar.
    max_size = min(guild.filesize_limit, 25 * 1024 * 1024)
    if any(a.size > max_size for a in message.attachments):
        return None

    async def upload(data, filename):
        if len(data) > max_size or not private_channel(guild, archive_channel):
            raise ValueError('archive_unavailable')
        file = discord.File(io.BytesIO(data), filename=filename)
        try:
            sent = await archive_channel.send(file=file, allowed_mentions=discord.AllowedMentions.none())
        finally:
            file.close()
        receipts.append({'guild_id': guild.id, 'channel_id': archive_channel.id,
                         'message_id': sent.id, 'filename': filename,
                         'size': len(data), 'sha256': hashlib.sha256(data).hexdigest()})
        await asyncio.to_thread(ledger, db_path, key, 'pending', receipts)

    for attachment in message.attachments:
        data = await attachment.read(use_cached=False)
        if len(data) != attachment.size:
            raise ValueError('incomplete_attachment')
        await upload(data, f'{message.id}-{attachment.id}.bin')
    metadata['copies'] = list(receipts)
    await upload(encoded(metadata), f'{message.id}-evidence.json')
    if not private_channel(guild, archive_channel) or not await verify(archive_channel, receipts):
        return None
    await asyncio.to_thread(ledger, db_path, key, 'complete', receipts)
    return f'https://discord.com/channels/{guild.id}/{archive_channel.id}/{receipts[-1]["message_id"]}'
