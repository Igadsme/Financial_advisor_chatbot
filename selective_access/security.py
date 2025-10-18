"""Security helpers for hashing and authorisation."""

from __future__ import annotations

import hashlib
import hmac
import json
from typing import Any, Dict

from .config import get_settings


def compute_hash(payload: Dict[str, Any]) -> str:
    """Generate a SHA-256 hash from a JSON payload."""

    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(serialized.encode("utf-8"))
    return digest.hexdigest()


def hashes_match(payload: Dict[str, Any], provided_hash: str) -> bool:
    """Check whether the supplied hash matches the calculated hash for the payload."""

    expected = compute_hash(payload)
    return hmac.compare_digest(expected, provided_hash)


def is_authorized(user_id: str, auth_token: str) -> bool:
    """Verify that the provided token matches the configured credentials."""

    settings = get_settings()
    expected_token = settings.allowed_users.get(user_id)
    if expected_token is None:
        return False
    return hmac.compare_digest(expected_token, auth_token)
