import sqlite3
from pathlib import Path

# Path to the SQLite database file
DB_PATH = Path(__file__).parent.parent / "data" / "activity.db"


def get_connection() -> sqlite3.Connection:
    """Return a connection to the SQLite database with row_factory set."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Allows column access by name
    return conn


def init_db() -> None:
    """Create the database and all tables if they do not already exist."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS activity_events (
                id                      TEXT PRIMARY KEY,
                timestamp               TEXT NOT NULL,
                raw_text                TEXT NOT NULL,
                clean_summary           TEXT,
                event_type              TEXT,
                activity_label          TEXT,
                category                TEXT,
                productivity_label      TEXT,
                previous_event_id       TEXT,
                previous_activity_label TEXT,
                confidence              REAL DEFAULT 0.0,
                created_at              TEXT NOT NULL
            )
        """)
        conn.commit()
