from dataclasses import dataclass, field
from datetime import datetime
from uuid import uuid4


@dataclass
class PassiveEvent:
    # Unique identifier for this passive event
    id: str = field(default_factory=lambda: str(uuid4()))

    # When the window/app was active (from ActivityWatch event timestamp)
    timestamp: datetime = field(default_factory=datetime.utcnow)

    # How long the window was active, in seconds
    duration_seconds: float = 0.0

    # Application name, e.g. "Code", "Safari", "Terminal"
    app: str = ""

    # Window title, e.g. "main.py — activity-intelligence"
    title: str = ""

    # Source identifier, e.g. "activitywatch"
    source: str = "activitywatch"

    # ActivityWatch bucket id, e.g. "aw-watcher-window_hostname"
    bucket_id: str = ""

    # When this record was inserted into the local database
    created_at: datetime = field(default_factory=datetime.utcnow)
