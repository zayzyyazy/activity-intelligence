from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from uuid import uuid4


@dataclass
class MobileScreenTimeEvent:
    # Unique identifier for this record
    id: str = field(default_factory=lambda: str(uuid4()))

    # When the app usage interval began (UTC, from knowledgeC.db ZCREATIONDATE)
    timestamp: datetime = field(default_factory=datetime.utcnow)

    # When the app usage interval ended (UTC, from knowledgeC.db ZENDDATE)
    end_timestamp: Optional[datetime] = None

    # Length of the usage interval in seconds (derived from start/end)
    duration_seconds: float = 0.0

    # Apple bundle identifier, e.g. "com.apple.mobilesafari"
    bundle_id: str = ""

    # Human-readable app name resolved from the bundle ID, e.g. "Safari"
    app_name: str = ""

    # Device identifier from knowledgeC.db ZDEVICEID (opaque string)
    device_id: str = ""

    # Human-readable device label, e.g. "iPhone", "iPad" (set at import time)
    device_name: str = ""

    # Origin of this record — always "screentime_knowledgeC" for this source
    source: str = "screentime_knowledgeC"

    # When this record was inserted into the local database
    created_at: datetime = field(default_factory=datetime.utcnow)
