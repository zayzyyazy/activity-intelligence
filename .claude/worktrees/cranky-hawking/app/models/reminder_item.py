from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import uuid4


class ReminderStatus(str, Enum):
    PENDING = "pending"  # Not yet completed
    DONE = "done"        # Marked as completed


@dataclass
class ReminderItem:
    # Unique identifier for this reminder
    id: str = field(default_factory=lambda: str(uuid4()))

    # Short description of what to remember or do, e.g. "Submit assignment"
    title: str = ""

    # Optional longer context or instructions attached to this reminder
    note: Optional[str] = None

    # When this reminder is due (None means no specific deadline)
    due_at: Optional[datetime] = None

    # Current state: pending or done
    status: ReminderStatus = ReminderStatus.PENDING

    # When this reminder was first created
    created_at: datetime = field(default_factory=datetime.utcnow)

    # When this reminder was marked done (None if still pending)
    completed_at: Optional[datetime] = None
