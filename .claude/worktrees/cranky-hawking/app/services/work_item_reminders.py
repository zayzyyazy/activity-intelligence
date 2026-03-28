from datetime import datetime, timedelta, timezone
from typing import List

from app.storage.work_items import get_all_open_work_items


def get_stale_open_work_items(hours: int = 24) -> List:
    """Return open work items that have not been updated within the given threshold.

    An item is stale if its last_updated_at is older than `hours` ago.
    Uses UTC for comparison since timestamps are stored in ISO format (UTC).
    """
    threshold = datetime.now(timezone.utc) - timedelta(hours=hours)
    stale = []

    for item in get_all_open_work_items():
        last_updated = datetime.fromisoformat(item["last_updated_at"])
        # Attach UTC timezone if the stored value is naive
        if last_updated.tzinfo is None:
            last_updated = last_updated.replace(tzinfo=timezone.utc)
        if last_updated < threshold:
            stale.append(item)

    return stale
