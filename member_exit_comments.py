"""Persistencia aislada de comentarios voluntarios tras abandonar un servidor.

No importa discord.py ni inicia conexiones de red. La migración crea únicamente
una tabla propia; no modifica las tablas de miembros, moderación o mensajes.
"""
from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone

COMMENT_LIMIT = 500
RESPONSE_DAYS = 7
PENDING_RETENTION_DAYS = 30
APPLIED_RETENTION_DAYS = 30


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat()


def init_storage(conn: sqlite3.Connection) -> None:
    conn.execute(
        """CREATE TABLE IF NOT EXISTS member_exit_comments (
            guild_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            log_channel_id INTEGER NOT NULL,
            log_message_id INTEGER NOT NULL,
            dm_message_id INTEGER,
            requested_at TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            comment TEXT,
            submitted_at TEXT,
            applied_at TEXT,
            PRIMARY KEY (guild_id, log_message_id),
            UNIQUE (dm_message_id)
        )"""
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_member_exit_comments_expiry "
        "ON member_exit_comments(expires_at)"
    )


def create_pending(
    conn: sqlite3.Connection, *,
    guild_id: int, user_id: int,
    channel_id: int, log_message_id: int,
    created_at: datetime | None = None,
) -> bool:
    now = created_at or utcnow()
    cur = conn.execute(
        """INSERT OR IGNORE INTO member_exit_comments
        (guild_id, user_id, log_channel_id, log_message_id, requested_at, expires_at)
        VALUES (?, ?, ?, ?, ?, ?)""",
        (guild_id, user_id, channel_id, log_message_id,
         _iso(now), _iso(now + timedelta(days=RESPONSE_DAYS))),
    )
    return cur.rowcount == 1


def attach_dm(conn: sqlite3.Connection, *, guild_id: int, log_message_id: int,
              dm_message_id: int) -> bool:
    cur = conn.execute(
        """UPDATE member_exit_comments SET dm_message_id=?
           WHERE guild_id=? AND log_message_id=? AND dm_message_id IS NULL
             AND comment IS NULL""",
        (dm_message_id, guild_id, log_message_id),
    )
    return cur.rowcount == 1


def find_by_dm(conn: sqlite3.Connection, *, dm_message_id: int, user_id: int,
               now: datetime | None = None) -> sqlite3.Row | None:
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        """SELECT * FROM member_exit_comments WHERE dm_message_id=?
           AND user_id=? AND comment IS NULL""",
        (dm_message_id, user_id),
    ).fetchone()
    if row is None or datetime.fromisoformat(row["expires_at"]) <= (now or utcnow()):
        return None
    return row


def submit_comment(conn: sqlite3.Connection, *, dm_message_id: int,
                   user_id: int, comment: str, now: datetime | None = None) -> bool:
    value = comment.strip()
    if not value or len(value) > COMMENT_LIMIT:
        raise ValueError("El comentario debe contener entre 1 y 500 caracteres.")
    timestamp = now or utcnow()
    cur = conn.execute(
        """UPDATE member_exit_comments SET comment=?, submitted_at=?
           WHERE dm_message_id=? AND user_id=? AND comment IS NULL
             AND expires_at>?""",
        (value, _iso(timestamp), dm_message_id, user_id, _iso(timestamp)),
    )
    return cur.rowcount == 1


def mark_applied(conn: sqlite3.Connection, *, guild_id: int,
                 log_message_id: int, now: datetime | None = None) -> bool:
    cur = conn.execute(
        """UPDATE member_exit_comments SET applied_at=?
           WHERE guild_id=? AND log_message_id=?
             AND comment IS NOT NULL AND applied_at IS NULL""",
        (_iso(now or utcnow()), guild_id, log_message_id),
    )
    return cur.rowcount == 1


def pending_edits(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    conn.row_factory = sqlite3.Row
    return conn.execute(
        "SELECT * FROM member_exit_comments WHERE comment IS NOT NULL AND applied_at IS NULL"
    ).fetchall()


def purge_expired(conn: sqlite3.Connection, *, now: datetime | None = None) -> int:
    """Retirar solicitudes sin respuesta y copias de comentarios ya publicados.

    Los comentarios que todavía no se han incorporado NO se borran: requieren
    recuperación o revisión administrativa para evitar pérdidas silenciosas.
    Las tarjetas originales de Discord no se modifican al purgar SQLite.
    """
    current = now or utcnow()
    abandoned = _iso(current - timedelta(days=PENDING_RETENTION_DAYS))
    applied = _iso(current - timedelta(days=APPLIED_RETENTION_DAYS))
    cur = conn.execute(
        """DELETE FROM member_exit_comments
           WHERE (comment IS NULL AND expires_at < ?)
              OR (comment IS NOT NULL AND applied_at IS NOT NULL
                  AND applied_at < ?)""",
        (abandoned, applied),
    )
    return cur.rowcount
