from datetime import datetime
from typing import Optional

from app.models.activity_event import ActivityEvent, EventType
from app.models.work_item import WorkItem, WorkStatus
from app.services.work_item_rules import should_create_work_item, infer_work_tag
from app.storage.work_items import (
    save_work_item,
    get_latest_in_progress_work_item_by_tag,
    update_work_item,
    mark_work_item_done,
)


# Simple result labels used by main.py to print the right confirmation line
RESULT_CREATED = "created"
RESULT_UPDATED = "updated"
RESULT_DONE    = "done"


def _to_datetime(value) -> datetime:
    """Return value as a datetime, parsing from ISO string if needed."""
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(value)


def _make_work_item(event: ActivityEvent, tag, text: str, ts: datetime) -> WorkItem:
    """Build and save a brand-new WorkItem from an event."""
    work_item = WorkItem(
        title=text,
        tag=tag,
        status=WorkStatus.IN_PROGRESS,
        started_at=ts,
        finished_at=None,
        last_updated_at=ts,
        latest_update=text,
        source_event_id=event.id,
    )
    save_work_item(work_item)
    return work_item


def create_work_item_from_event(event: ActivityEvent):
    """Decide whether to create, update, or close a WorkItem for this event.

    Returns a (WorkItem | sqlite3.Row, result_label) tuple, or None if no
    action was taken.

    Result labels: 'created', 'updated', 'done'
    """
    if not should_create_work_item(event):
        return None

    tag  = infer_work_tag(event)
    text = event.clean_summary if event.clean_summary else event.raw_text
    ts   = _to_datetime(event.timestamp)
    ts_iso = ts.isoformat()

    if event.event_type == EventType.CONTINUE:
        # Try to progress an existing open item with the same tag
        existing = get_latest_in_progress_work_item_by_tag(tag.value)
        if existing:
            update_work_item(existing["id"], text, ts_iso, event.id)
            return existing, RESULT_UPDATED
        # No open item found — treat this as a fresh start
        return _make_work_item(event, tag, text, ts), RESULT_CREATED

    if event.event_type == EventType.END:
        # Close the most recent open item with the same tag
        existing = get_latest_in_progress_work_item_by_tag(tag.value)
        if existing:
            mark_work_item_done(existing["id"], ts_iso, text)
            return existing, RESULT_DONE
        return None

    # START, SWITCH, or anything else that passed the filter -> new item
    return _make_work_item(event, tag, text, ts), RESULT_CREATED
