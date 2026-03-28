"""
reset_week.py — Archive the current week's data and start fresh.

Usage:
    python scripts/reset_week.py
"""

import shutil
from datetime import datetime
from pathlib import Path

# Allow imports from project root
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db import DB_PATH, init_db

# Paths
DATA_DIR = Path(__file__).parent.parent / "data"
CSV_PATH = DATA_DIR / "activity_log.csv"

# Compute ISO year and week number (e.g. "2026-12")
now = datetime.now()
iso_year, iso_week, _ = now.isocalendar()
week_label = f"{iso_year}-{iso_week:02d}"

# Archive destination
archive_dir = DATA_DIR / "archive" / week_label
archive_dir.mkdir(parents=True, exist_ok=True)

print(f"Archive folder: {archive_dir}")

# Move DB
if DB_PATH.exists():
    shutil.move(str(DB_PATH), str(archive_dir / "activity.db"))
    print(f"  archived DB  -> {archive_dir / 'activity.db'}")
else:
    print("  no DB found, skipping")

# Move CSV
if CSV_PATH.exists():
    shutil.move(str(CSV_PATH), str(archive_dir / "activity_log.csv"))
    print(f"  archived CSV -> {archive_dir / 'activity_log.csv'}")
else:
    print("  no CSV found, skipping")

# Recreate fresh DB
init_db()
print(f"  created fresh DB at {DB_PATH}")
