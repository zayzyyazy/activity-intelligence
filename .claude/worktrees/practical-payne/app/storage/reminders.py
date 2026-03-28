import sqlite3
from datetime import datetime
from typing import List

from app.db import get_connection
from app.models.reminder_item import ReminderItem


def save_reminder(reminder: ReminderItem) -> None:
    """Insert one ReminderItem into the reminder_items table.

    Datetime fields are stored as ISO 8601 strings.
    Enum fields are stored as their string values.
    """
    conn = get_connection()
    conn.execute(
        """
        INSERT INTO reminder_items (
            id,
            title,
            note,
            due_at,
            status,
            created_at,
            completed_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            reminder.id,
            reminder.title,
            reminder.note,
            reminder.due_at.isoformat() if reminder.due_at else None,
            reminder.status.value,
            reminder.created_at.isoformat(),
            reminder.completed_at.isoformat() if reminder.completed_at else None,
        ),
    )
    conn.commit()
    conn.close()


def get_pending_reminders() -> List[sqlite3.Row]:
    """Return all pending reminders ordered by due_at ascending, nulls last.

    Used to surface upcoming reminders in the daily report.
    Rows support column access by name (e.g. row['title']).
    """
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT * FROM reminder_items
        WHERE status = 'pending'
        ORDER BY
            CASE WHEN due_at IS NULL THEN 1 ELSE 0 END,
            due_at ASC
        """
    ).fetchall()
    conn.close()
    return rows


def mark_reminder_done(reminder_id: str) -> None:
    """Set a reminder's status to done and record the completion timestamp."""
    conn = get_connection()
    conn.execute(
        """
        UPDATE reminder_items
        SET status       = 'done',
            completed_at = ?
        WHERE id = ?
        """,
        (datetime.utcnow().isoformat(), reminder_id),
    )
    conn.commit()
    conn.close()
