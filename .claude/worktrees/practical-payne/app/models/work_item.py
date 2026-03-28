from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import uuid4


class WorkStatus(str, Enum):
    IN_PROGRESS = "in_progress"  # Currently being worked on
    DONE = "done"                # Completed


class WorkTag(str, Enum):
    RESEARCH = "research"              # Investigating or learning about a topic
    WRITING = "writing"                # Writing essays, notes, or documentation
    UNIVERSITY = "university"          # Lectures, coursework, or exam prep
    PERSONAL_PROJECT = "personal_project"  # Side projects, building, coding
    ADMIN = "admin"                    # Planning, organising, scheduling
    OTHER = "other"                    # Meaningful work that doesn't fit above


@dataclass
class WorkItem:
    # Unique identifier for this work item
    id: str = field(default_factory=lambda: str(uuid4()))

    # Short human-readable name, e.g. "Study for linear algebra midterm"
    title: str = ""

    # Broad category of work — used for filtering and weekly summaries
    tag: WorkTag = WorkTag.OTHER

    # Current state of the item
    status: WorkStatus = WorkStatus.IN_PROGRESS

    # When the user first started this work item
    started_at: datetime = field(default_factory=datetime.utcnow)

    # When the item was marked done (None if still in progress)
    finished_at: Optional[datetime] = None

    # Timestamp of the most recent update to this item
    last_updated_at: datetime = field(default_factory=datetime.utcnow)

    # Most recent free-text progress note, e.g. "finished section 3, stuck on proofs"
    latest_update: str = ""

    # ID of the ActivityEvent that created or last updated this item
    source_event_id: Optional[str] = None
