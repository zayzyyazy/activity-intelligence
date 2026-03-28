"""
ingest_activitywatch.py — Fetch window activity from ActivityWatch and store it locally.

Usage:
    python scripts/ingest_activitywatch.py [--hours N]

Options:
    --hours N   How many hours back to fetch (default: 24).
                Ignored if the database already has passive events — in that
                case the script fetches from the latest stored timestamp onward.
"""

import sys
import socket
import argparse
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Allow imports from project root when run as a script
sys.path.insert(0, str(Path(__file__).parent.parent))

import requests

from app.db import init_db
from app.models.passive_event import PassiveEvent
from app.storage.passive_events import save_passive_event, get_latest_passive_timestamp

# ActivityWatch default local API base URL
AW_BASE_URL = "http://localhost:5600/api/0"

# Default bucket name pattern used by aw-watcher-window
# ActivityWatch names the bucket after the hostname of the machine.
AW_BUCKET_TEMPLATE = "aw-watcher-window_{hostname}"


def _resolve_bucket_id() -> str:
    """Return the expected window-watcher bucket id for this machine."""
    hostname = socket.gethostname()
    return AW_BUCKET_TEMPLATE.format(hostname=hostname)


def _fetch_events(bucket_id: str, start: datetime) -> list[dict]:
    """Fetch events from an ActivityWatch bucket starting from `start`.

    Returns a list of raw AW event dicts, or raises on connection failure.
    """
    params = {
        "start": start.isoformat(),
        "limit": -1,  # -1 = no limit
    }
    url = f"{AW_BASE_URL}/buckets/{bucket_id}/events"
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    return response.json()


def _to_passive_event(raw: dict, bucket_id: str) -> PassiveEvent:
    """Map one raw ActivityWatch event dict to a PassiveEvent."""
    # AW timestamps are ISO 8601 with timezone info
    ts = datetime.fromisoformat(raw["timestamp"])
    # Normalise to UTC naive for consistency with the rest of the project
    if ts.tzinfo is not None:
        ts = ts.astimezone(timezone.utc).replace(tzinfo=None)

    data = raw.get("data", {})

    return PassiveEvent(
        timestamp=ts,
        duration_seconds=raw.get("duration", 0.0),
        app=data.get("app", ""),
        title=data.get("title", ""),
        source="activitywatch",
        bucket_id=bucket_id,
        created_at=datetime.utcnow(),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest ActivityWatch window events.")
    parser.add_argument(
        "--hours",
        type=int,
        default=24,
        help="Hours back to fetch on first run (default: 24).",
    )
    args = parser.parse_args()

    init_db()

    bucket_id = _resolve_bucket_id()
    print(f"Bucket: {bucket_id}")

    # Use the latest stored timestamp as the start point to avoid re-fetching.
    # On first run, fall back to N hours ago.
    latest = get_latest_passive_timestamp()
    if latest:
        start = datetime.fromisoformat(latest).replace(tzinfo=timezone.utc)
        print(f"Resuming from last ingested timestamp: {latest}")
    else:
        start = datetime.now(timezone.utc) - timedelta(hours=args.hours)
        print(f"No prior data — fetching last {args.hours} hours.")

    try:
        raw_events = _fetch_events(bucket_id, start)
    except requests.exceptions.ConnectionError:
        print(
            "ERROR: Could not connect to ActivityWatch at http://localhost:5600.\n"
            "Make sure ActivityWatch is running before running this script."
        )
        sys.exit(1)
    except requests.exceptions.HTTPError as e:
        print(f"ERROR: ActivityWatch API returned an error: {e}")
        sys.exit(1)

    fetched = len(raw_events)
    saved = 0

    for raw in raw_events:
        event = _to_passive_event(raw, bucket_id)
        if save_passive_event(event):
            saved += 1

    print(f"Fetched {fetched} events from ActivityWatch.")
    print(f"Saved   {saved} new events ({fetched - saved} duplicates skipped).")


if __name__ == "__main__":
    main()
