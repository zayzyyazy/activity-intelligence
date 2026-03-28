"""
ingest_activity_inbox.py — Import activity logs from the iCloud inbox file.

The iPhone/iPad Shortcut appends plain-text log lines to:
  ~/Library/Mobile Documents/com~apple~CloudDocs/Shortcuts/activity_log_inbox.txt

This script reads those lines and runs each one through the normal
ActivityEvent logging flow (classify → save → work item check).

After a successful run the inbox file is cleared (truncated to empty).
The events are permanently stored in the SQLite database, so clearing
the inbox is safe.

Usage:
    python3 scripts/ingest_activity_inbox.py
"""

import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

# Ensure project root is on the path when run as a script
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db import init_db
from app.models.activity_event import ActivityEvent, Category, EventType, ProductivityLabel
from app.services.ai_classifier import classify_event_ai
from app.services.work_item_service import (
    RESULT_CREATED,
    RESULT_DONE,
    RESULT_UPDATED,
    create_work_item_from_event,
)
from app.storage.events import get_last_event, save_event

INBOX_PATH = Path.home() / "Library/Mobile Documents/com~apple~CloudDocs/Shortcuts/activity_log_inbox.txt"

EVENT_TYPE_MAP = {
    "start":    EventType.START,
    "continue": EventType.CONTINUE,
    "end":      EventType.END,
    "switch":   EventType.SWITCH,
    "note":     EventType.UNKNOWN,
}

CATEGORY_MAP = {
    "studying":    Category.STUDY,
    "building":    Category.WORK,
    "distraction": Category.DISTRACTION,
    "break":       Category.BREAK,
    "other":       Category.UNKNOWN,
}

PRODUCTIVITY_MAP = {
    "productive":   ProductivityLabel.PRODUCTIVE,
    "neutral":      ProductivityLabel.NEUTRAL,
    "unproductive": ProductivityLabel.UNPRODUCTIVE,
}


def log_activity(raw_text: str) -> None:
    """Run one activity line through the full classify → save → work-item flow."""
    now = datetime.now(timezone.utc)
    last_event = get_last_event()

    event = ActivityEvent(
        id=str(uuid4()),
        timestamp=now,
        raw_text=raw_text,
        clean_summary="",
        event_type=EventType.UNKNOWN,
        activity_label="",
        category=Category.UNKNOWN,
        productivity_label=ProductivityLabel.UNKNOWN,
        previous_event_id=last_event["id"] if last_event else None,
        previous_activity_label=last_event["activity_label"] if last_event else None,
        confidence=0.0,
        created_at=now,
    )

    result = classify_event_ai(raw_text)
    event.event_type         = EVENT_TYPE_MAP.get(result["event_type"], EventType.UNKNOWN)
    event.activity_label     = result["activity_label"]
    event.clean_summary      = result["activity_label"]
    event.category           = CATEGORY_MAP.get(result["category"], Category.UNKNOWN)
    event.productivity_label = PRODUCTIVITY_MAP.get(result["productivity_label"], ProductivityLabel.UNKNOWN)

    if event.event_type == EventType.UNKNOWN and event.activity_label == event.previous_activity_label:
        event.event_type = EventType.CONTINUE
    elif (
        event.event_type == EventType.UNKNOWN
        and event.previous_activity_label is not None
        and event.activity_label != event.previous_activity_label
    ):
        event.event_type = EventType.SWITCH

    save_event(event)

    wi_result = create_work_item_from_event(event)
    wi_note = ""
    if wi_result is not None:
        item, action = wi_result
        title = item.title if hasattr(item, "title") else item["title"]
        tag   = item.tag.value if hasattr(item, "tag") else item["tag"]
        if action == RESULT_CREATED:
            wi_note = f" → work item created: {title} [{tag}]"
        elif action == RESULT_UPDATED:
            wi_note = f" → work item updated: {title} [{tag}]"
        elif action == RESULT_DONE:
            wi_note = f" → work item done: {title} [{tag}]"

    print(f"  ✓ [{event.event_type.value}] {event.activity_label} ({event.category.value}){wi_note}")


def main() -> None:
    if not INBOX_PATH.exists():
        print(f"Inbox file not found: {INBOX_PATH}")
        print("Create it on your iPhone using the Shortcuts app and try again.")
        sys.exit(0)

    lines = [l.strip() for l in INBOX_PATH.read_text().splitlines() if l.strip()]

    if not lines:
        print("Inbox is empty. Nothing to import.")
        sys.exit(0)

    print(f"Found {len(lines)} line(s) in inbox. Importing...\n")

    init_db()

    failed = []
    for raw_text in lines:
        print(f"  → {raw_text}")
        try:
            log_activity(raw_text)
        except Exception as e:
            print(f"  ✗ Failed: {e}")
            failed.append(raw_text)

    imported = len(lines) - len(failed)

    print(f"\n{imported}/{len(lines)} activities imported.")

    if failed:
        print(f"\nThe following lines could not be imported and will remain in the inbox:")
        for line in failed:
            print(f"  - {line}")
        # Write only the failed lines back so they can be retried
        INBOX_PATH.write_text("\n".join(failed) + "\n")
    else:
        # All imported — clear the inbox
        INBOX_PATH.write_text("")
        print("Inbox cleared.")


if __name__ == "__main__":
    main()
