"""
View today's passive activity (ActivityWatch) grouped by app.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from datetime import datetime, timedelta
from app.db import get_connection


def main():
    now = datetime.utcnow()
    today = now.date().isoformat()
    tomorrow = (now + timedelta(days=1)).date().isoformat()

    conn = get_connection()
    rows = conn.execute(
        """
        SELECT app, SUM(duration_seconds) AS total_seconds
        FROM passive_events
        WHERE timestamp >= ? AND timestamp < ?
        GROUP BY app
        ORDER BY total_seconds DESC
        """,
        (today, tomorrow),
    ).fetchall()

    debug = conn.execute(
        """
        SELECT
            SUM(duration_seconds) AS total_seconds,
            MIN(timestamp) AS earliest,
            MAX(timestamp) AS latest
        FROM passive_events
        WHERE timestamp >= ? AND timestamp < ?
        """,
        (today, tomorrow),
    ).fetchone()
    conn.close()

    print("Passive Activity Today")
    print("----------------------")

    if not rows:
        print("No passive activity recorded today.")
        return

    for row in rows:
        app = row["app"] or "(unknown)"
        minutes = int(row["total_seconds"] // 60)
        if minutes < 1:
            label = "< 1 min"
        else:
            label = f"{minutes} min"
        print(f"- {app}: {label}")

    total_minutes = int((debug["total_seconds"] or 0) // 60)
    print()
    print(f"[debug] total passive time : {total_minutes} min")
    print(f"[debug] earliest timestamp : {debug['earliest']}")
    print(f"[debug] latest timestamp   : {debug['latest']}")
    print(f"[debug] query window       : {today} → {tomorrow} (UTC)")


if __name__ == "__main__":
    main()
