"""Database helpers for the Selective Access Control service."""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Dict, Iterator

from .config import get_settings


def _get_connection() -> sqlite3.Connection:
    settings = get_settings()
    connection = sqlite3.connect(settings.database_path)
    connection.row_factory = sqlite3.Row
    return connection


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    connection = _get_connection()
    try:
        yield connection
    finally:
        connection.close()


def initialize() -> None:
    """Create the cache table if it does not already exist."""

    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS data_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                payload TEXT NOT NULL,
                hash_value TEXT NOT NULL,
                synced INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL
            )
            """
        )
        connection.commit()


def cache_payload(user_id: str, payload: Dict[str, Any], hash_value: str) -> int:
    """Persist a validated payload into the cache and return the row identifier."""

    serialized_payload = json.dumps(payload, sort_keys=True)
    timestamp = datetime.now(timezone.utc).isoformat()

    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO data_cache (user_id, payload, hash_value, synced, created_at)
            VALUES (?, ?, ?, 0, ?)
            """,
            (user_id, serialized_payload, hash_value, timestamp),
        )
        connection.commit()
        return int(cursor.lastrowid)


def mark_synced(record_id: int) -> None:
    """Mark the cached payload as successfully synchronised with the main server."""

    with get_connection() as connection:
        connection.execute(
            "UPDATE data_cache SET synced = 1 WHERE id = ?",
            (record_id,),
        )
        connection.commit()
