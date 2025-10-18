# Selective Access Control with Data Bootloader

This project provides a secure Flask-based backend that accepts data from authorised
clients, verifies the integrity of the data by comparing SHA-256 hashes, caches the
validated payloads in a local SQLite database, and optionally forwards the data to a
remote main server.

## Features

- **Authentication:** Each request is validated using pre-configured user credentials.
- **Integrity verification:** The service recomputes SHA-256 hashes and rejects
  tampered payloads.
- **Local caching:** Validated payloads are stored in an SQLite cache for auditing and
  recovery.
- **Main server push:** When a `SELECTIVE_ACCESS_TARGET` URL is configured, the
  service forwards payloads upstream after successful verification.

## Configuration

Configuration is controlled via environment variables:

| Variable | Description | Default |
| --- | --- | --- |
| `SELECTIVE_ACCESS_USERS` | JSON object mapping usernames to tokens. | `{"alice": "token-alice", "bob": "token-bob"}` |
| `SELECTIVE_ACCESS_DB` | Path to the SQLite cache file. | `data/cache.sqlite` |
| `SELECTIVE_ACCESS_TARGET` | Optional URL for the main server endpoint. | _unset_ |

## Running the service

1. (Optional) Create and activate a virtual environment so the dependencies do not
   pollute your global Python installation:

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows use: .venv\Scripts\activate
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Configure any credentials or destinations that differ from the defaults. For
   example, to accept requests from two custom users and push accepted payloads
   to `https://example.com/ingest` while storing the cache in `/tmp/cache.sqlite`:

   ```bash
   export SELECTIVE_ACCESS_USERS='{"ops": "super-secret", "auditor": "read-only"}'
   export SELECTIVE_ACCESS_TARGET="https://example.com/ingest"
   export SELECTIVE_ACCESS_DB="/tmp/cache.sqlite"
   ```

4. Start the Flask application in development mode:

   ```bash
   flask --app app run --host 0.0.0.0 --port 8000
   ```

   Alternatively, run `python app.py` to start the built-in development server.

5. In a separate terminal session, send a request that includes the SHA-256 hash of
   the payload. The snippet below assumes the default `alice` credentials:

   ```bash
   python scripts/send_sample.py
   ```

   Or, using `curl` directly:

   ```bash
   payload='{"amount": 1000, "currency": "USD"}'
   hash=$(python -c "import hashlib, json; print(hashlib.sha256(json.dumps(json.loads('$payload'), sort_keys=True, separators=(',', ':')).encode()).hexdigest())")
   curl -X POST http://localhost:8000/ingest \
        -H 'Content-Type: application/json' \
        -d '{"user_id": "alice", "auth_token": "token-alice", "payload": '$payload', "hash": '"$hash"'}'
   ```

   A successful response returns HTTP 202 and includes the cache record identifier.

## API

### `POST /ingest`

Accepts JSON payloads of the form:

```json
{
  "user_id": "alice",
  "auth_token": "token-alice",
  "payload": {"amount": 1000, "currency": "USD"},
  "hash": "<sha-256 hash of payload>"
}
```

- Returns HTTP 202 when the payload is accepted and cached.
- Returns HTTP 409 when hash validation fails.
- Returns HTTP 401 when credentials are invalid.

### `GET /health`

Simple health-check endpoint that returns `{"status": "ok"}`.

## Testing the hash workflow

```python
import json
import hashlib
import requests

payload = {"amount": 1000, "currency": "USD"}
serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
hash_value = hashlib.sha256(serialized.encode("utf-8")).hexdigest()

response = requests.post(
    "http://localhost:8000/ingest",
    json={
        "user_id": "alice",
        "auth_token": "token-alice",
        "payload": payload,
        "hash": hash_value,
    },
)
print(response.status_code, response.json())
```

This example demonstrates how clients should prepare data before sending it to the
service.

## Preparing a GitHub push

The repository in this workspace does not have a remote configured. To push your
commits to GitHub:

1. Create an empty repository on GitHub (do **not** initialize it with files).
2. Add the GitHub repository as a remote:

   ```bash
   git remote add origin git@github.com:<your-account>/selective-access-control.git
   ```

   Replace the URL with either the SSH or HTTPS URL provided by GitHub.

3. Push the current branch (named `work` in this environment) to GitHub:

   ```bash
   git push -u origin work
   ```

4. Open a pull request on GitHub if you want to review or merge the changes.
