"""Entry point for the Selective Access Control with Data Bootloader service."""

from __future__ import annotations

from selective_access import create_app

app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
