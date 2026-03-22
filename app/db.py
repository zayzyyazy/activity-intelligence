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
        # Raw timeline: one row per user check-in, classified by AI
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

        # Meaningful work units: one row per sustained piece of work spanning
        # one or more activity events (e.g. "study session", "build feature X")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS work_items (
                id              TEXT PRIMARY KEY,
                title           TEXT NOT NULL,
                tag             TEXT NOT NULL,
                status          TEXT NOT NULL DEFAULT 'in_progress',
                started_at      TEXT NOT NULL,
                finished_at     TEXT,
                last_updated_at TEXT NOT NULL,
                latest_update   TEXT,
                source_event_id TEXT
            )
        """)

        # Passive timeline: one row per window-focus interval captured by ActivityWatch.
        # UNIQUE constraint on (bucket_id, timestamp, app, title) allows INSERT OR IGNORE
        # deduplication so the ingestion script is safe to re-run.
        conn.execute("""
            CREATE TABLE IF NOT EXISTS passive_events (
                id               TEXT PRIMARY KEY,
                timestamp        TEXT NOT NULL,
                duration_seconds REAL NOT NULL DEFAULT 0.0,
                app              TEXT NOT NULL DEFAULT '',
                title            TEXT NOT NULL DEFAULT '',
                source           TEXT NOT NULL DEFAULT 'activitywatch',
                bucket_id        TEXT NOT NULL DEFAULT '',
                created_at       TEXT NOT NULL,
                UNIQUE (bucket_id, timestamp, app, title)
            )
        """)

        # Manual reminders set by the user, shown in the daily report
        conn.execute("""
            CREATE TABLE IF NOT EXISTS reminder_items (
                id           TEXT PRIMARY KEY,
                title        TEXT NOT NULL,
                note         TEXT,
                due_at       TEXT,
                status       TEXT NOT NULL DEFAULT 'pending',
                created_at   TEXT NOT NULL,
                completed_at TEXT
            )
        """)

        # Mobile Screen Time: one row per app-usage interval imported from
        # knowledgeC.db on the Mac (synced from iPhone/iPad via iCloud).
        # UNIQUE constraint on (timestamp, bundle_id, device_id) makes the
        # ingestion script safe to re-run without creating duplicate rows.
        conn.execute("""
            CREATE TABLE IF NOT EXISTS mobile_screen_time_events (
                id               TEXT PRIMARY KEY,
                timestamp        TEXT NOT NULL,
                end_timestamp    TEXT,
                duration_seconds REAL NOT NULL DEFAULT 0.0,
                bundle_id        TEXT NOT NULL DEFAULT '',
                app_name         TEXT NOT NULL DEFAULT '',
                device_id        TEXT NOT NULL DEFAULT '',
                device_name      TEXT NOT NULL DEFAULT '',
                source           TEXT NOT NULL DEFAULT 'screentime_knowledgeC',
                created_at       TEXT NOT NULL,
                UNIQUE (timestamp, bundle_id, device_id)
            )
        """)

        conn.commit()
