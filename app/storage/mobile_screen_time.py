from typing import Optional

from app.db import get_connection
from app.models.mobile_screen_time_event import MobileScreenTimeEvent


def save_mobile_screen_time_event(event: MobileScreenTimeEvent) -> bool:
    """Insert one MobileScreenTimeEvent into mobile_screen_time_events.

    Uses INSERT OR IGNORE so re-running the importer on overlapping time
    ranges is safe — duplicate rows (matched on the UNIQUE constraint on
    timestamp, bundle_id, device_id) are silently skipped.

    Returns True if the row was inserted, False if it was a duplicate.
    """
    conn = get_connection()
    cursor = conn.execute(
        """
        INSERT OR IGNORE INTO mobile_screen_time_events (
            id,
            timestamp,
            end_timestamp,
            duration_seconds,
            bundle_id,
            app_name,
            device_id,
            device_name,
            source,
            created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            event.id,
            event.timestamp.isoformat(),
            event.end_timestamp.isoformat() if event.end_timestamp else None,
            event.duration_seconds,
            event.bundle_id,
            event.app_name,
            event.device_id,
            event.device_name,
            event.source,
            event.created_at.isoformat(),
        ),
    )
    conn.commit()
    inserted = cursor.rowcount == 1
    conn.close()
    return inserted


def get_latest_screen_time_timestamp(device_id: str) -> Optional[str]:
    """Return the ISO 8601 timestamp of the most recently stored event for
    a given device_id.

    Used by the importer to fetch only new records from knowledgeC.db
    rather than re-processing the full history on every run.

    Returns None if no rows exist for this device yet.
    """
    conn = get_connection()
    row = conn.execute(
        "SELECT MAX(timestamp) AS latest FROM mobile_screen_time_events WHERE device_id = ?",
        (device_id,),
    ).fetchone()
    conn.close()
    return row["latest"] if row else None
