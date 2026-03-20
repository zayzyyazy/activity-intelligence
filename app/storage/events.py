from app.db import get_connection
from app.models.activity_event import ActivityEvent


def save_event(event: ActivityEvent) -> None:
    """Insert one ActivityEvent into the activity_events table.

    Assumes the database and table already exist (init_db() has been called).
    Datetime fields are stored as ISO 8601 strings.
    Enum fields are stored as their string values.
    """
    conn = get_connection()
    conn.execute(
        """
        INSERT INTO activity_events (
            id,
            timestamp,
            raw_text,
            clean_summary,
            event_type,
            activity_label,
            category,
            productivity_label,
            previous_event_id,
            previous_activity_label,
            confidence,
            created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            event.id,
            event.timestamp.isoformat(),
            event.raw_text,
            event.clean_summary,
            event.event_type.value,
            event.activity_label,
            event.category.value,
            event.productivity_label.value,
            event.previous_event_id,
            event.previous_activity_label,
            event.confidence,
            event.created_at.isoformat(),
        ),
    )
    conn.commit()
    conn.close()


def get_last_event():
    """Return the most recently saved activity event as a sqlite3.Row.

    Rows support column access by name (e.g. row['activity_label']).
    Returns None if the table is empty.
    """
    conn = get_connection()
    row = conn.execute(
        """
        SELECT * FROM activity_events
        ORDER BY timestamp DESC
        LIMIT 1
        """
    ).fetchone()
    conn.close()
    return row
