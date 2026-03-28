from typing import Optional

import sqlite3

from app.db import get_connection
from app.models.work_item import WorkItem


def save_work_item(work_item: WorkItem) -> None:
    """Insert one WorkItem into the work_items table.

    Datetime fields are stored as ISO 8601 strings.
    Enum fields are stored as their string values.
    """
    conn = get_connection()
    conn.execute(
        """
        INSERT INTO work_items (
            id,
            title,
            tag,
            status,
            started_at,
            finished_at,
            last_updated_at,
            latest_update,
            source_event_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            work_item.id,
            work_item.title,
            work_item.tag.value,
            work_item.status.value,
            work_item.started_at.isoformat(),
            work_item.finished_at.isoformat() if work_item.finished_at else None,
            work_item.last_updated_at.isoformat(),
            work_item.latest_update,
            work_item.source_event_id,
        ),
    )
    conn.commit()
    conn.close()


def get_work_item_by_id(work_item_id: str) -> Optional[sqlite3.Row]:
    """Return a single work item row by its id, or None if not found.

    Rows support column access by name (e.g. row['title']).
    """
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM work_items WHERE id = ?",
        (work_item_id,),
    ).fetchone()
    conn.close()
    return row


def get_latest_in_progress_work_item_by_tag(tag: str) -> Optional[sqlite3.Row]:
    """Return the most recently updated in-progress work item for a given tag.

    Used to decide whether a continuation or end event should act on an
    existing item rather than creating a new one.
    """
    conn = get_connection()
    row = conn.execute(
        """
        SELECT * FROM work_items
        WHERE status = 'in_progress' AND tag = ?
        ORDER BY last_updated_at DESC
        LIMIT 1
        """,
        (tag,),
    ).fetchone()
    conn.close()
    return row


def update_work_item(work_item_id: str, latest_update: str, last_updated_at: str, source_event_id: str) -> None:
    """Update the progress note and timestamps on an existing work item."""
    conn = get_connection()
    conn.execute(
        """
        UPDATE work_items
        SET latest_update   = ?,
            last_updated_at = ?,
            source_event_id = ?
        WHERE id = ?
        """,
        (latest_update, last_updated_at, source_event_id, work_item_id),
    )
    conn.commit()
    conn.close()


def get_all_open_work_items():
    """Return all in-progress work items ordered by most recently updated."""
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT * FROM work_items
        WHERE status = 'in_progress'
        ORDER BY last_updated_at DESC
        """
    ).fetchall()
    conn.close()
    return rows


def mark_work_item_done(work_item_id: str, finished_at: str, latest_update: str) -> None:
    """Set a work item's status to done and record the finish time."""
    conn = get_connection()
    conn.execute(
        """
        UPDATE work_items
        SET status        = 'done',
            finished_at   = ?,
            latest_update = ?,
            last_updated_at = ?
        WHERE id = ?
        """,
        (finished_at, latest_update, finished_at, work_item_id),
    )
    conn.commit()
    conn.close()
