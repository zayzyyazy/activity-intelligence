import sqlite3
from datetime import date, datetime
from pathlib import Path

DB_PATH = Path(__file__).parent.parent.parent / "data" / "activity.db"

# Number of top results to show for apps and titles
TOP_N = 5


def generate_passive_summary(day: date = None) -> None:
    """Print a summary of passive window activity for the given day.

    Args:
        day: The date to summarise. Defaults to today.
    """
    if day is None:
        day = date.today()

    day_str = day.isoformat()  # e.g. "2026-03-21"

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    rows = conn.execute(
        """
        SELECT app, title, duration_seconds
        FROM passive_events
        WHERE DATE(timestamp) = ?
        """,
        (day_str,),
    ).fetchall()

    conn.close()

    if not rows:
        print(f"No passive events found for {day_str}.")
        return

    # Aggregate time per app
    app_totals: dict[str, float] = {}
    title_totals: dict[str, float] = {}

    for row in rows:
        app = row["app"] or "(unknown)"
        title = row["title"] or "(no title)"
        duration = row["duration_seconds"] or 0.0

        app_totals[app] = app_totals.get(app, 0.0) + duration
        title_totals[title] = title_totals.get(title, 0.0) + duration

    total_seconds = sum(app_totals.values())
    total_minutes = total_seconds / 60

    top_apps = sorted(app_totals.items(), key=lambda x: x[1], reverse=True)[:TOP_N]
    top_titles = sorted(title_totals.items(), key=lambda x: x[1], reverse=True)[:TOP_N]

    print(f"Passive Activity Summary — {day_str}")
    print("=" * 45)
    print(f"Total tracked time: {total_minutes:.1f} min  ({len(rows)} events)")

    print(f"\nTop {TOP_N} Apps:")
    for app, seconds in top_apps:
        minutes = seconds / 60
        pct = (seconds / total_seconds * 100) if total_seconds > 0 else 0.0
        print(f"  {app:<30} {minutes:>6.1f} min  ({pct:.0f}%)")

    print(f"\nTop {TOP_N} Window Titles:")
    for title, seconds in top_titles:
        minutes = seconds / 60
        pct = (seconds / total_seconds * 100) if total_seconds > 0 else 0.0
        # Truncate long titles for readability
        display = title if len(title) <= 50 else title[:47] + "..."
        print(f"  {display:<50} {minutes:>6.1f} min  ({pct:.0f}%)")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        try:
            day = date.fromisoformat(sys.argv[1])
        except ValueError:
            print(f"Invalid date '{sys.argv[1]}'. Expected format: YYYY-MM-DD")
            sys.exit(1)
    else:
        day = date.today()

    generate_passive_summary(day)
