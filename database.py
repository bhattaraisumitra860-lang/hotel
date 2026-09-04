"""Small persistence adapter for Hotel 77.

Vercel deployments should set DATABASE_URL to a managed PostgreSQL database.
Local development keeps using data.json so the project remains easy to run.
"""
import json
import os
from pathlib import Path

try:
    import psycopg
except ImportError:  # pragma: no cover - local fallback when dependency is absent
    psycopg = None


DATA_FILE = Path(__file__).resolve().parent / "data.json"


def _database_url():
    return os.environ.get("DATABASE_URL") or os.environ.get("POSTGRES_URL")


def _connect():
    url = _database_url()
    if not url or psycopg is None:
        return None
    return psycopg.connect(url, connect_timeout=5)


def load_state(default_factory):
    """Load the single JSON application state, seeding it only once."""
    connection = _connect()
    if connection is None:
        if DATA_FILE.exists():
            return json.loads(DATA_FILE.read_text(encoding="utf-8"))
        state = default_factory()
        DATA_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")
        return state

    with connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """CREATE TABLE IF NOT EXISTS hotel_state (
                    state_key TEXT PRIMARY KEY,
                    payload JSONB NOT NULL,
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )"""
            )
            cursor.execute("SELECT payload FROM hotel_state WHERE state_key = 'default'")
            row = cursor.fetchone()
            if row:
                return row[0]
            state = default_factory()
            cursor.execute(
                "INSERT INTO hotel_state (state_key, payload) VALUES ('default', %s)",
                (json.dumps(state),),
            )
            return state


def save_state(state):
    """Persist state without resetting or replacing unrelated records."""
    connection = _connect()
    if connection is None:
        DATA_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")
        return
    with connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """INSERT INTO hotel_state (state_key, payload, updated_at)
                   VALUES ('default', %s, NOW())
                   ON CONFLICT (state_key) DO UPDATE
                   SET payload = EXCLUDED.payload, updated_at = NOW()""",
                (json.dumps(state),),
            )
