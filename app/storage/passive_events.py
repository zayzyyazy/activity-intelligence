from typing import Optional

from app.db import get_connection
from app.models.passive_event import PassiveEvent


def save_passive_event(event: PassiveEvent) -> bool:
    """Insert one PassiveEvent into the passive_events table.

    Uses INSERT OR IGNORE so re-running the ingestion script on overlapping
    time ranges is safe — duplicate rows (matched on the UNIQUE constraint on
    bucket_id, timestamp, app, title) are silently skipped.

    Returns True if the row was inserted, False if it was a duplicate.
    """
    conn = get_connection()
    cursor = conn.execute(
        """
        INSERT OR IGNORE INTO passive_events (
            id,
            timestamp,
            duration_seconds,
            app,
            title,
            source,
            bucket_id,
            created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            event.id,
            event.timestamp.isoformat(),
            event.duration_seconds,
            event.app,
            event.title,
            event.source,
            event.bucket_id,
            event.created_at.isoformat(),
        ),
    )
    conn.commit()
    inserted = cursor.rowcount == 1
    conn.close()
    return inserted


def get_latest_passive_timestamp() -> Optional[str]:
    """Return the ISO 8601 timestamp of the most recently ingested passive event.

    Used by the ingestion script to request only new events from ActivityWatch
    rather than re-fetching the full history on every run.

    Returns None if no passive events have been ingested yet.
    """
    conn = get_connection()
    row = conn.execute(
        "SELECT MAX(timestamp) AS latest FROM passive_events"
    ).fetchone()
    conn.close()
    return row["latest"] if row else None
