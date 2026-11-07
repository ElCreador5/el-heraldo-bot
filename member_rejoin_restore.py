"""Restauración conservadora de verificación al reingresar. Ramas Pruebas y main (habilitación manual por servidor).

Solo se guarda el rol de personalidad vigente o el rol provisional de edad;
no se conservan roles arbitrarios ni privilegios. Los registros requieren una
salida voluntaria confirmada con permiso de auditoría de Discord.
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
import sqlite3

TABLE_SQL = """
CREATE TABLE IF NOT EXISTS verified_rejoin_snapshots (
    guild_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    role_id INTEGER NOT NULL,
    departed_at TEXT NOT NULL,
    PRIMARY KEY (guild_id, user_id)
)
"""


def _connect(connect):
    db = connect()
    db.execute(TABLE_SQL)
    return db


def forget(connect, guild_id: int, user_id: int) -> None:
    db = _connect(connect)
    try:
        db.execute("DELETE FROM verified_rejoin_snapshots WHERE guild_id=? AND user_id=?",
                   (guild_id, user_id))
    finally:
        db.close()


def saved_role(connect, guild_id: int, user_id: int) -> int | None:
    db = _connect(connect)
    try:
        row = db.execute(
            "SELECT role_id, departed_at FROM verified_rejoin_snapshots "
            "WHERE guild_id=? AND user_id=?", (guild_id, user_id)).fetchone()
    finally:
        db.close()
    if not row:
        return None
    try:
        when = datetime.fromisoformat(row[1])
        if when.tzinfo is None or datetime.now(timezone.utc) - when > timedelta(days=30):
            return None
        return int(row[0])
    except (TypeError, ValueError):
        return None


def _safe_role(guild, role) -> bool:
    me = getattr(guild, "me", None)
    if role is None or me is None:
        return False
    if (role.is_default() or role.managed or role >= me.top_role
            or not me.guild_permissions.manage_roles):
        return False
    permissions = role.permissions
    return not (permissions.administrator or permissions.manage_guild
                or permissions.manage_roles or permissions.ban_members
                or permissions.kick_members or permissions.moderate_members)


async def capture_departure(member, *, connect, enabled, personality_ids,
                            verify_role_id, is_verified, audit_action):
    """Fail closed: an audit failure or a kick/ban prevents snapshot creation."""
    if member.bot:
        return
    guild = member.guild
    # Invalidate every previous snapshot, even when this exit is a kick or ban.
    forget(connect, guild.id, member.id)
    if not enabled(guild.id):
        return
    permitted = set(personality_ids(guild.id))
    provisional_id = int(verify_role_id(guild.id) or 0)
    held = {role.id for role in member.roles}
    chosen = sorted(held & permitted)
    role_id = chosen[0] if len(chosen) == 1 else (
        provisional_id if not chosen and provisional_id in held else None)
    if role_id is None or not is_verified(member):
        return
    if not _safe_role(guild, guild.get_role(role_id)):
        return
    me = getattr(guild, "me", None)
    if not me or not me.guild_permissions.view_audit_log:
        return
    observed = datetime.now(timezone.utc)
    # Give Discord time to write the audit entries; a successful audit query
    # is mandatory. Never interpret Forbidden/HTTP errors as voluntary exit.
    await asyncio.sleep(3)
    try:
        for action in (audit_action.kick, audit_action.ban):
            async for entry in guild.audit_logs(
                limit=40, action=action, after=observed - timedelta(seconds=20)
            ):
                if (getattr(getattr(entry, "target", None), "id", None) == member.id
                        and abs((entry.created_at - observed).total_seconds()) <= 25):
                    return
    except Exception:
        return
    # A member who rejoined before audit completed must not get a late snapshot.
    if guild.get_member(member.id) is not None:
        return
    db = _connect(connect)
    try:
        db.execute(
            "INSERT INTO verified_rejoin_snapshots "
            "(guild_id, user_id, role_id, departed_at) VALUES (?,?,?,?) "
            "ON CONFLICT(guild_id,user_id) DO UPDATE SET "
            "role_id=excluded.role_id, departed_at=excluded.departed_at",
            (guild.id, member.id, role_id, observed.isoformat()),
        )
    finally:
        db.close()


async def restore_join(member, *, connect, enabled, personality_ids,
                       verify_role_id, sin_role_id):
    if member.bot or not enabled(member.guild.id):
        return False
    # Capture may still be checking the departure audit log.
    await asyncio.sleep(4)
    guild = member.guild
    if guild.get_member(member.id) is None:
        return False
    role_id = saved_role(connect, guild.id, member.id)
    if role_id is None:
        return False
    # Consume once: later kicks/ban cannot reuse an old verified state.
    forget(connect, guild.id, member.id)
    if role_id not in set(personality_ids(guild.id)) | {int(verify_role_id(guild.id) or 0)}:
        return False
    role = guild.get_role(role_id)
    if not _safe_role(guild, role):
        return False
    try:
        await member.add_roles(role, reason="rejoin")
        unverified = guild.get_role(int(sin_role_id(guild.id) or 0))
        if unverified is not None and unverified in member.roles and _safe_role(guild, unverified):
            await member.remove_roles(unverified, reason="rejoin")
        return True
    except Exception:
        return False
