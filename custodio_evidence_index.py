"""Índice mínimo de referencias de evidencia; nunca almacena mensajes ni reglas."""
from __future__ import annotations
import sqlite3
from pathlib import Path

def prepare_index(db_path: str) -> None:
    with sqlite3.connect(db_path, timeout=10) as db:
        db.execute("""CREATE TABLE IF NOT EXISTS custodio_evidence_refs (
            guild_id INTEGER NOT NULL,
            source_message_id INTEGER NOT NULL,
            report_message_id INTEGER NOT NULL,
            PRIMARY KEY (guild_id, source_message_id)
        )""")

def find_reference(db_path: str, guild_id: int, source_message_id: int) -> int | None:
    with sqlite3.connect(db_path, timeout=10) as db:
        row = db.execute(
            "SELECT report_message_id FROM custodio_evidence_refs WHERE guild_id=? AND source_message_id=?",
            (guild_id, source_message_id),
        ).fetchone()
    return int(row[0]) if row else None

def save_reference(db_path: str, guild_id: int, source_message_id: int, report_message_id: int) -> None:
    if not all(type(v) is int and v > 0 for v in (guild_id, source_message_id, report_message_id)):
        raise ValueError("invalid_reference")
    with sqlite3.connect(db_path, timeout=10) as db:
        db.execute(
            "INSERT OR IGNORE INTO custodio_evidence_refs VALUES (?, ?, ?)",
            (guild_id, source_message_id, report_message_id),
        )

def remove_reference(db_path: str, guild_id: int, source_message_id: int) -> None:
    with sqlite3.connect(db_path, timeout=10) as db:
        db.execute(
            "DELETE FROM custodio_evidence_refs WHERE guild_id=? AND source_message_id=?",
            (guild_id, source_message_id),
        )
