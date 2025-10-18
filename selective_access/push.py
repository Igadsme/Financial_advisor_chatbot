"""Utilities for pushing cached data to the main server."""

from __future__ import annotations

import logging
from typing import Dict

import requests

from .config import get_settings

logger = logging.getLogger(__name__)


def push_to_main_server(payload: Dict[str, object], hash_value: str) -> bool:
    """Send the validated payload to the configured main server."""

    settings = get_settings()
    if not settings.main_server_url:
        logger.info("Main server URL not configured; skipping remote push.")
        return False

    try:
        response = requests.post(
            settings.main_server_url,
            json={"payload": payload, "hash": hash_value},
            timeout=10,
        )
        response.raise_for_status()
    except requests.RequestException as exc:  # pragma: no cover - network failures are logged
        logger.error("Failed to push update to main server: %s", exc)
        return False

    logger.info("Successfully pushed payload to main server: %s", settings.main_server_url)
    return True
