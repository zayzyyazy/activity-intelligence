from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import uuid4


class EventType(str, Enum):
    START = "start"        # Beginning a new activity
    CONTINUE = "continue"  # Still on the same activity
    END = "end"            # Finishing an activity
    SWITCH = "switch"      # Moving from one activity to another
    DISTRACTION = "distraction"  # Off-task / unplanned detour
    UNKNOWN = "unknown"    # Could not be determined


class Category(str, Enum):
    STUDY = "study"
    WORK = "work"
    BREAK = "break"
    DISTRACTION = "distraction"
    PERSONAL = "personal"
    UNKNOWN = "unknown"


class ProductivityLabel(str, Enum):
    PRODUCTIVE = "productive"
    NEUTRAL = "neutral"
    UNPRODUCTIVE = "unproductive"
    UNKNOWN = "unknown"


@dataclass
class ActivityEvent:
    # --- Core identity ---
    id: str = field(default_factory=lambda: str(uuid4()))
    # When the user submitted this update
    timestamp: datetime = field(default_factory=datetime.utcnow)

    # --- Raw input ---
    # Exactly what the user typed
    raw_text: str = ""
    # Normalised, punctuation-cleaned version of raw_text
    clean_summary: str = ""

    # --- Classification ---
    # Whether this event starts, continues, ends, or switches an activity
    event_type: EventType = EventType.UNKNOWN
    # Short label for the activity, e.g. "math revision", "coding"
    activity_label: str = ""
    # Broad category bucket
    category: Category = Category.UNKNOWN
    # Whether this activity is considered productive
    productivity_label: ProductivityLabel = ProductivityLabel.UNKNOWN

    # --- Context / continuity ---
    # ID of the event that came directly before this one
    previous_event_id: Optional[str] = None
    # Activity label of the previous event — used to detect switches
    previous_activity_label: Optional[str] = None

    # --- Metadata ---
    # 0.0–1.0 confidence score from the classifier
    confidence: float = 0.0
    # When this record was created (may differ from timestamp if ingested later)
    created_at: datetime = field(default_factory=datetime.utcnow)
