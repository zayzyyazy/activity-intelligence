"""
ingest_screen_time.py — Import iPhone/iPad Screen Time data from knowledgeC.db.

Usage:
    python scripts/ingest_screen_time.py [--days N]

Options:
    --days N    How many days back to import (default: 7).
                On re-runs, already-stored rows are skipped automatically via
                INSERT OR IGNORE — it is safe to run this repeatedly.

Source:
    ~/Library/Application Support/Knowledge/knowledgeC.db

    This database is maintained by macOS and syncs Screen Time data from
    iPhone/iPad when "Share Across Devices" is enabled in Screen Time settings.

Permissions required:
    The process (or the terminal app running it) must have Full Disk Access.
    System Settings → Privacy & Security → Full Disk Access → enable Terminal
    (or whichever app you run this from). Without Full Disk Access, sqlite3
    will raise OperationalError: unable to open database file.

Schema notes (knowledgeC.db):
    - Main table: ZOBJECT
    - ZSTREAMNAME = '/app/inFocus' selects foreground app usage intervals.
    - ZVALUESTRING holds the bundle ID (e.g. "com.apple.mobilesafari").
    - ZCREATIONDATE and ZENDDATE use Apple's Core Data reference epoch:
      seconds since 2001-01-01 00:00:00 UTC (not Unix epoch).
      Add APPLE_EPOCH_OFFSET (978307200) to convert to Unix timestamp.
    - ZDEVICEID is an opaque string identifying the source device.
    - Device friendly names may be stored in a ZSOURCE table (not present on
      all macOS versions) — the script is defensive about its absence.
    - All timestamps are queried as floats and converted here; no date math
      is delegated to SQLite to avoid Core Data epoch confusion.
"""

import sys
import sqlite3
import argparse
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Allow imports from project root when run as a script
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db import init_db
from app.models.mobile_screen_time_event import MobileScreenTimeEvent
from app.storage.mobile_screen_time import (
    save_mobile_screen_time_event,
    get_latest_screen_time_timestamp,
)

# knowledgeC.db default location
KNOWLEDGE_DB = Path.home() / "Library/Application Support/Knowledge/knowledgeC.db"

# Seconds between Unix epoch (1970-01-01) and Apple Core Data epoch (2001-01-01)
APPLE_EPOCH_OFFSET = 978307200

# Partial bundle-ID → human-readable name lookup.
# Not exhaustive — unknown bundle IDs are stored as-is in app_name.
BUNDLE_NAMES: dict[str, str] = {
    "com.apple.mobilesafari":         "Safari",
    "com.apple.MobileSMS":            "Messages",
    "com.apple.mobilemail":           "Mail",
    "com.apple.Maps":                 "Maps",
    "com.apple.Music":                "Music",
    "com.apple.camera":               "Camera",
    "com.apple.Photos":               "Photos",
    "com.apple.mobilenotes":          "Notes",
    "com.apple.mobilephone":          "Phone",
    "com.apple.facetime":             "FaceTime",
    "com.apple.Preferences":          "Settings",
    "com.apple.springboard":          "Home Screen",
    "com.apple.news":                 "News",
    "com.apple.podcasts":             "Podcasts",
    "com.apple.tv":                   "TV",
    "com.apple.Health":               "Health",
    "com.apple.reminders":            "Reminders",
    "com.apple.mobilecal":            "Calendar",
    "com.apple.stocks":               "Stocks",
    "com.apple.iBooks":               "Books",
    "com.apple.shortcuts":            "Shortcuts",
    "com.google.ios.youtube":         "YouTube",
    "com.google.chrome.ios":          "Chrome",
    "com.google.Gmail":               "Gmail",
    "com.google.Maps":                "Google Maps",
    "com.instagram.barcelona":        "Instagram",
    "com.facebook.Facebook":          "Facebook",
    "com.facebook.Messenger":         "Messenger",
    "com.zhiliaoapp.musically":       "TikTok",
    "com.twitter.ios":                "X (Twitter)",
    "com.atebits.Tweetie2":           "X (Twitter)",
    "com.reddit.reddit":              "Reddit",
    "com.discord.discord":            "Discord",
    "com.spotify.client":             "Spotify",
    "com.microsoft.Office.Outlook":   "Outlook",
    "com.microsoft.teams":            "Teams",
    "com.apple.mobilegarageband":     "GarageBand",
    "com.amazon.Amazon":              "Amazon",
    "com.netflix.Netflix":            "Netflix",
    "com.burbn.instagram":            "Instagram",
}


def _apple_ts_to_utc(apple_ts: float) -> datetime:
    """Convert an Apple Core Data timestamp (float, seconds since 2001-01-01)
    to a naive UTC datetime."""
    unix_ts = apple_ts + APPLE_EPOCH_OFFSET
    return datetime.utcfromtimestamp(unix_ts)


def _resolve_app_name(bundle_id: str) -> str:
    """Return a human-readable name for a bundle ID, or the bundle ID itself
    if no mapping exists."""
    return BUNDLE_NAMES.get(bundle_id, bundle_id)


def _load_device_names(kc_conn: sqlite3.Connection) -> dict[str, str]:
    """Attempt to read device friendly names from the ZSOURCE table.

    Returns a dict of {device_id: friendly_name}. Returns an empty dict if
    the table does not exist or has no usable data — this is normal on some
    macOS versions.
    """
    try:
        rows = kc_conn.execute(
            "SELECT ZDEVICEID, ZFRIENDLYNAME FROM ZSOURCE WHERE ZDEVICEID IS NOT NULL"
        ).fetchall()
        return {r[0]: r[1] or "" for r in rows if r[0]}
    except sqlite3.OperationalError:
        return {}


def _open_knowledge_db() -> sqlite3.Connection:
    """Open knowledgeC.db read-only.

    Raises FileNotFoundError if the file does not exist.
    Raises PermissionError (via sqlite3.OperationalError) if FDA is missing.
    """
    if not KNOWLEDGE_DB.exists():
        raise FileNotFoundError(KNOWLEDGE_DB)

    # immutable=1 tells SQLite not to look for a WAL/shm file — safe for
    # a system database that another process is actively writing to.
    uri = f"file:{KNOWLEDGE_DB}?mode=ro&immutable=1"
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def _fetch_raw_rows(
    kc_conn: sqlite3.Connection,
    cutoff_apple_ts: float,
) -> list[sqlite3.Row]:
    """Query ZOBJECT for app usage intervals newer than cutoff.

    Filters on ZSTREAMNAME = '/app/usage' (available on this macOS schema;
    '/app/inFocus' is absent). ZVALUESTRING holds the bundle ID.
    ZSTARTDATE/ZENDDATE are used (ZCREATIONDATE not present in this schema).
    ZDEVICEID is not present; device_id is hardcoded to 'unknown_device'.

    Returns only rows where both ZSTARTDATE and ZVALUESTRING are present,
    to avoid storing incomplete records.
    """
    return kc_conn.execute(
        """
        SELECT
            ZVALUESTRING        AS bundle_id,
            ZSTARTDATE          AS start_ts,
            ZENDDATE            AS end_ts,
            'unknown_device'    AS device_id
        FROM ZOBJECT
        WHERE ZSTREAMNAME   = '/app/usage'
          AND ZVALUESTRING  IS NOT NULL
          AND ZSTARTDATE    IS NOT NULL
          AND ZSTARTDATE    > ?
        ORDER BY ZSTARTDATE ASC
        """,
        (cutoff_apple_ts,),
    ).fetchall()


def _cutoff_apple_ts(days: int, device_ids_seen: set[str]) -> float:
    """Return the Apple-epoch cutoff timestamp to use for this run.

    Strategy:
    - If we have already imported data for any of the devices in the DB,
      use the global latest stored timestamp as the cutoff (incremental).
    - Otherwise fall back to `days` ago (initial import).

    Since we do not know device IDs before querying knowledgeC.db, we use
    the stored global max as a conservative lower bound. INSERT OR IGNORE
    handles any edge-case overlaps.
    """
    # Look up latest for each known device_id and take the global minimum
    # (so we do not miss any device that lags behind the others).
    known_latest: list[datetime] = []
    for did in device_ids_seen:
        ts_str = get_latest_screen_time_timestamp(did)
        if ts_str:
            known_latest.append(datetime.fromisoformat(ts_str))

    if known_latest:
        oldest_latest = min(known_latest)
        unix_ts = oldest_latest.replace(tzinfo=timezone.utc).timestamp()
        apple_ts = unix_ts - APPLE_EPOCH_OFFSET
        return apple_ts

    # First run — go back `days` days from now
    cutoff_unix = (datetime.now(timezone.utc) - timedelta(days=days)).timestamp()
    return cutoff_unix - APPLE_EPOCH_OFFSET


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Import iPhone/iPad Screen Time data from knowledgeC.db."
    )
    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Days back to import on first run (default: 7). "
             "Ignored on subsequent runs — uses last stored timestamp instead.",
    )
    args = parser.parse_args()

    # Ensure our project DB and tables exist
    init_db()

    # --- Open knowledgeC.db ---
    try:
        kc_conn = _open_knowledge_db()
    except FileNotFoundError:
        print(
            f"ERROR: knowledgeC.db not found at:\n  {KNOWLEDGE_DB}\n\n"
            "Possible reasons:\n"
            "  - You are on a macOS version that stores this file elsewhere.\n"
            "  - iCloud Knowledge sync is disabled.\n"
            "Check that the path exists and try again."
        )
        sys.exit(1)
    except sqlite3.OperationalError as exc:
        print(
            f"ERROR: Could not open knowledgeC.db: {exc}\n\n"
            "This is almost always a Full Disk Access problem.\n"
            "Fix: System Settings → Privacy & Security → Full Disk Access\n"
            "     Enable the app you are running this script from (e.g. Terminal, iTerm2).\n"
            "Then re-run this script."
        )
        sys.exit(1)

    print(f"Opened: {KNOWLEDGE_DB}")

    # Load device friendly names (best-effort; empty dict if table absent)
    device_names = _load_device_names(kc_conn)
    if device_names:
        print(f"Found {len(device_names)} known device(s): {list(device_names.values())}")
    else:
        print("No device name table found — device_name will be left blank.")

    # Determine cutoff. On first run we have no stored device IDs, so pass
    # an empty set and the fallback (--days) will be used.
    cutoff = _cutoff_apple_ts(args.days, set(device_names.keys()))

    cutoff_utc = _apple_ts_to_utc(cutoff)
    print(f"Importing rows newer than: {cutoff_utc.isoformat()} UTC")

    # --- Fetch rows from knowledgeC.db ---
    try:
        raw_rows = _fetch_raw_rows(kc_conn, cutoff)
    except sqlite3.OperationalError as exc:
        print(
            f"ERROR: Query against knowledgeC.db failed: {exc}\n\n"
            "Possible reasons:\n"
            "  - knowledgeC.db schema differs on this macOS version.\n"
            "  - ZOBJECT table or expected columns are missing.\n"
            "  - No Screen Time data is present (no mobile devices synced).\n\n"
            "No data was imported."
        )
        kc_conn.close()
        sys.exit(1)
    finally:
        kc_conn.close()

    fetched = len(raw_rows)
    print(f"Raw rows fetched from knowledgeC.db: {fetched}")

    if fetched == 0:
        print(
            "\nNo rows returned. Likely reasons:\n"
            "  1. iCloud Screen Time sync is off:\n"
            "     Settings (iPhone) → Screen Time → Share Across Devices → enable.\n"
            "  2. Full Disk Access not granted — the DB opened but returned no data.\n"
            "  3. No mobile device has been used since the cutoff date.\n"
            "  4. knowledgeC.db on this macOS version uses a different ZSTREAMNAME.\n"
            "     Try: sqlite3 ~/Library/Application\\ Support/Knowledge/knowledgeC.db\n"
            "          SELECT DISTINCT ZSTREAMNAME FROM ZOBJECT LIMIT 20;\n"
        )
        sys.exit(0)

    # --- Map rows to MobileScreenTimeEvent and save ---
    saved = 0
    skipped = 0
    now = datetime.utcnow()

    for row in raw_rows:
        bundle_id  = row["bundle_id"] or ""
        start_ts   = row["start_ts"]
        end_ts_raw = row["end_ts"]
        device_id  = row["device_id"] or ""

        # Convert Apple timestamps to UTC datetimes
        try:
            timestamp = _apple_ts_to_utc(float(start_ts))
        except (TypeError, ValueError, OSError):
            skipped += 1
            continue

        end_timestamp = None
        if end_ts_raw is not None:
            try:
                end_timestamp = _apple_ts_to_utc(float(end_ts_raw))
            except (TypeError, ValueError, OSError):
                pass  # end_timestamp stays None — still a valid record

        # Duration: prefer computed from start/end; fall back to 0
        if end_timestamp is not None:
            duration_seconds = max(
                0.0, (end_timestamp - timestamp).total_seconds()
            )
        else:
            duration_seconds = 0.0

        event = MobileScreenTimeEvent(
            timestamp=timestamp,
            end_timestamp=end_timestamp,
            duration_seconds=duration_seconds,
            bundle_id=bundle_id,
            app_name=_resolve_app_name(bundle_id),
            device_id=device_id,
            device_name=device_names.get(device_id, ""),
            source="screentime_knowledgeC",
            created_at=now,
        )

        if save_mobile_screen_time_event(event):
            saved += 1
        else:
            skipped += 1

    print(f"Saved   {saved} new rows.")
    print(f"Skipped {skipped} rows ({fetched - saved - skipped} conversion errors).")


if __name__ == "__main__":
    main()
