"""Application configuration for the Selective Access Control service."""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict

logger = logging.getLogger(__name__)

DEFAULT_ALLOWED_USERS = {
    "alice": "token-alice",
    "bob": "token-bob",
}


@dataclass(frozen=True)
class Settings:
    """Runtime configuration for the service."""

    database_path: Path
    allowed_users: Dict[str, str]
    main_server_url: str | None


_settings: Settings | None = None


def _load_allowed_users() -> Dict[str, str]:
    """Load user credentials from the environment or fall back to defaults."""

    raw_users = os.getenv("SELECTIVE_ACCESS_USERS")
    if not raw_users:
        return DEFAULT_ALLOWED_USERS.copy()

    try:
        parsed = json.loads(raw_users)
    except json.JSONDecodeError:
        logger.warning(
            "Failed to parse SELECTIVE_ACCESS_USERS. Falling back to default users."
        )
        return DEFAULT_ALLOWED_USERS.copy()

    if not isinstance(parsed, dict):
        logger.warning(
            "SELECTIVE_ACCESS_USERS must be a JSON object mapping usernames to tokens."
        )
        return DEFAULT_ALLOWED_USERS.copy()

    allowed: Dict[str, str] = {}
    for username, token in parsed.items():
        if token is None:
            continue
        allowed[str(username)] = str(token)

    if not allowed:
        logger.warning("No valid user credentials supplied; using defaults instead.")
        return DEFAULT_ALLOWED_USERS.copy()

    return allowed


def get_settings() -> Settings:
    """Return the cached Settings instance, initializing it when necessary."""

    global _settings
    if _settings is None:
        database_path = Path(os.getenv("SELECTIVE_ACCESS_DB", "data/cache.sqlite"))
        main_server_url = os.getenv("SELECTIVE_ACCESS_TARGET")
        allowed_users = _load_allowed_users()
        if not database_path.parent.exists():
            database_path.parent.mkdir(parents=True, exist_ok=True)
        _settings = Settings(
            database_path=database_path,
            allowed_users=allowed_users,
            main_server_url=main_server_url,
        )
    return _settings
