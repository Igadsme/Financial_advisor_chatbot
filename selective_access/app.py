"""Flask application for the Selective Access Control service."""

from __future__ import annotations

import hmac
import logging
from typing import Any, Dict

from flask import Flask, jsonify, request

from . import database
from .config import get_settings
from .push import push_to_main_server
from .security import compute_hash, is_authorized

logger = logging.getLogger(__name__)


def create_app() -> Flask:
    """Create and configure the Flask application."""

    logging.basicConfig(level=logging.INFO)

    app = Flask(__name__)
    database.initialize()
    settings = get_settings()

    @app.get("/health")
    def health_check() -> Any:
        """Health-check endpoint used by monitoring services."""

        return jsonify({"status": "ok"})

    @app.post("/ingest")
    def ingest() -> Any:
        """Ingest data from authorised clients after verifying integrity."""

        payload = request.get_json(silent=True)
        if not payload:
            return jsonify({"status": "error", "message": "Invalid JSON payload."}), 400

        user_id = payload.get("user_id")
        auth_token = payload.get("auth_token")
        content = payload.get("payload")
        provided_hash = payload.get("hash")

        if not all([user_id, auth_token, content, provided_hash]):
            return (
                jsonify({"status": "error", "message": "Missing required fields."}),
                400,
            )

        if not isinstance(content, dict):
            return (
                jsonify({"status": "error", "message": "Payload must be a JSON object."}),
                400,
            )

        if not is_authorized(str(user_id), str(auth_token)):
            return (
                jsonify({"status": "error", "message": "Unauthorized."}),
                401,
            )

        if not isinstance(provided_hash, str):
            return (
                jsonify({"status": "error", "message": "Hash must be a string."}),
                400,
            )

        computed_hash = compute_hash(content)
        if not hmac.compare_digest(computed_hash, provided_hash):
            logger.warning("Hash mismatch for user %s", user_id)
            return (
                jsonify({"status": "error", "message": "Hash mismatch."}),
                409,
            )

        record_id = database.cache_payload(str(user_id), content, computed_hash)
        pushed = push_to_main_server(content, computed_hash)
        if pushed:
            database.mark_synced(record_id)

        response: Dict[str, Any] = {
            "status": "accepted",
            "record_id": record_id,
            "pushed_to_main_server": pushed,
            "database": str(settings.database_path),
        }
        return jsonify(response), 202

    return app
