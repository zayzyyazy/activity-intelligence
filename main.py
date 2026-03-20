import sys
from datetime import datetime, timezone
from uuid import uuid4

from app.models.activity_event import ActivityEvent, EventType, Category, ProductivityLabel
from app.services.ai_classifier import classify_event_ai
from app.db import init_db
from app.storage.events import save_event, get_last_event

# Classifier returns plain strings; map them to the enum values used by the model
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

init_db()

if len(sys.argv) < 2:
    print("Please provide an activity, e.g. python main.py 'starting math'")
    sys.exit(1)

activity_text = sys.argv[1]
print(f"Received activity: {activity_text}")

now = datetime.now(timezone.utc)
last_event = get_last_event()

event = ActivityEvent(
    id=str(uuid4()),
    timestamp=now,
    raw_text=activity_text,
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

# Classify the raw text and populate the relevant fields
result = classify_event_ai(activity_text)
event.event_type         = EVENT_TYPE_MAP.get(result["event_type"], EventType.UNKNOWN)
event.activity_label     = result["activity_label"]
event.clean_summary      = result["activity_label"]
event.category           = CATEGORY_MAP.get(result["category"], Category.UNKNOWN)
event.productivity_label = PRODUCTIVITY_MAP.get(result["productivity_label"], ProductivityLabel.UNKNOWN)

# If no strong keyword was detected (note) but the activity hasn't changed, treat it as a continue
if event.event_type == EventType.UNKNOWN and event.activity_label == event.previous_activity_label:
    event.event_type = EventType.CONTINUE

# If no strong keyword was detected but the activity changed, treat it as a switch
elif (
    event.event_type == EventType.UNKNOWN
    and event.previous_activity_label is not None
    and event.activity_label != event.previous_activity_label
):
    event.event_type = EventType.SWITCH

save_event(event)
print("Event saved to database.")

print(f"\nCreated ActivityEvent:")
print(f"  id                     : {event.id}")
print(f"  timestamp              : {event.timestamp.isoformat()}")
print(f"  raw_text               : {event.raw_text}")
print(f"  clean_summary          : {event.clean_summary}")
print(f"  event_type             : {event.event_type.value}")
print(f"  activity_label         : {event.activity_label}")
print(f"  category               : {event.category.value}")
print(f"  productivity_label     : {event.productivity_label.value}")
print(f"  previous_event_id      : {event.previous_event_id}")
print(f"  previous_activity_label: {event.previous_activity_label}")
print(f"  confidence             : {event.confidence}")
print(f"  created_at             : {event.created_at.isoformat()}")
