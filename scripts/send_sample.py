"""Send a sample payload to the Selective Access Control service."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Dict

import requests

SERVICE_URL = "http://localhost:8000/ingest"
DEFAULT_PAYLOAD: Dict[str, Any] = {"amount": 1000, "currency": "USD"}
DEFAULT_USER_ID = "alice"
DEFAULT_TOKEN = "token-alice"


@dataclass
class Submission:
    """Data required to submit a payload to the ingest endpoint."""

    user_id: str
    auth_token: str
    payload: Dict[str, Any]

    def to_request_body(self) -> Dict[str, Any]:
        """Create the JSON body expected by the ingest endpoint."""

        serialized = json.dumps(self.payload, sort_keys=True, separators=(",", ":"))
        hash_value = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
        return {
            "user_id": self.user_id,
            "auth_token": self.auth_token,
            "payload": self.payload,
            "hash": hash_value,
        }


def main() -> None:
    submission = Submission(DEFAULT_USER_ID, DEFAULT_TOKEN, DEFAULT_PAYLOAD)
    response = requests.post(SERVICE_URL, json=submission.to_request_body(), timeout=10)
    print(f"Status: {response.status_code}")
    try:
        print("Response:", response.json())
    except ValueError:
        print("Raw body:", response.text)


if __name__ == "__main__":
    main()
