"""
Daily Command Center — `day`

Shows a snapshot of your day:
  - Pending tasks (reminders)
  - Stale work items (not updated in >24h)
  - Passive activity today (top apps by time)
  - A simple rule-based suggestion
"""

import glob as _glob
import os
from datetime import datetime, timedelta

from app.db import get_connection

# File paths for flat-file sections
SW_IDEAS = "/Users/zay/Desktop/Software and     tools/ideas.txt"
SW_FINISHED = "/Users/zay/Desktop/Software and     tools/finishedprojects.txt"
RW_FINISHED = "/Users/zay/Desktop/Research and writing/finishedprojectssearch.txt"
RW_IDEAS_DIR = "/Users/zay/Desktop/Research and writing"

ITEMS_PER_CATEGORY = 3


_SECTION_LABELS = {"project", "tools", "steps", "time", "notes", "goal", "stack", "why", "how"}


def _parse_items(content, n):
    """
    Extract last n item titles from file content.
    Strategy: if bracketed [Title] lines exist, use those.
    Otherwise fall back to last n non-empty, non-label lines (>20 chars).
    """
    # Drop RTF preamble lines (start with backslash, braces, or are lone close-braces)
    def _is_rtf(l):
        s = l.lstrip()
        return s.startswith("\\") or s.startswith("{\\") or s == "}"

    lines = [l for l in content.splitlines() if not _is_rtf(l)]

    # Try bracketed titles first: lines starting with [
    titled = [l.strip() for l in lines if l.strip().startswith("[") and l.strip().endswith("]")]
    if titled:
        return [t[:120] for t in titled[-n:]]

    # Fallback: meaningful lines (skip section labels and short lines)
    meaningful = []
    for l in lines:
        s = l.strip()
        if not s:
            continue
        label = s.rstrip(":").lower()
        if label in _SECTION_LABELS:
            continue
        if len(s) < 15:
            continue
        # Strip leading bullet characters
        s = s.lstrip("•⁠ -–—*·").strip()
        if s:
            meaningful.append(s[:120])
    return meaningful[-n:] if meaningful else []


def _read_last_blocks(filepath, n):
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
    except FileNotFoundError:
        return []
    return _parse_items(content, n)


def _read_last_blocks_merged(dirpath, filename, n):
    """Merge ideas.txt files from all subfolders sorted by mtime, return last n titles."""
    pattern = os.path.join(dirpath, "**", filename)
    paths = sorted(_glob.glob(pattern, recursive=True), key=os.path.getmtime)
    combined = []
    for path in paths:
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                combined.append(f.read())
        except FileNotFoundError:
            pass
    return _parse_items("\n".join(combined), n)


STALE_HOURS = 24
TOP_N = 5
FOCUS_N = 3

# Apps considered distracting for the suggestion heuristic
DISTRACTION_APPS = {"youtube", "twitter", "instagram", "reddit", "tiktok", "netflix"}


def get_tasks(conn):
    rows = conn.execute(
        """
        SELECT title, due_at
        FROM reminder_items
        WHERE status = 'pending'
        ORDER BY due_at ASC NULLS LAST, created_at ASC
        """,
    ).fetchall()
    return rows


def get_stale_work(conn):
    cutoff = (datetime.utcnow() - timedelta(hours=STALE_HOURS)).isoformat()
    rows = conn.execute(
        """
        SELECT title, last_updated_at
        FROM work_items
        WHERE status = 'in_progress'
          AND last_updated_at < ?
        ORDER BY last_updated_at DESC
        LIMIT 1
        """,
        (cutoff,),
    ).fetchall()
    return rows


def get_activity(conn):
    now = datetime.utcnow()
    today = now.date().isoformat()
    tomorrow = (now + timedelta(days=1)).date().isoformat()
    rows = conn.execute(
        """
        SELECT app, SUM(duration_seconds) AS total_seconds
        FROM passive_events
        WHERE timestamp >= ? AND timestamp < ?
        GROUP BY app
        ORDER BY total_seconds DESC
        LIMIT ?
        """,
        (today, tomorrow, TOP_N),
    ).fetchall()
    return rows


def make_suggestion(focus_tasks, stale_item):
    if focus_tasks:
        title = focus_tasks[0]["title"]
        return f"Start with \"{title}\"."
    if stale_item:
        title = stale_item["title"]
        return f"Resume \"{title}\"."
    return "Looks clean. Keep the momentum going."


def fmt_minutes(seconds):
    minutes = int(seconds // 60)
    return "< 1 min" if minutes < 1 else f"{minutes} min"


def fmt_stale_age(last_updated_at):
    try:
        updated = datetime.fromisoformat(last_updated_at)
        hours = int((datetime.utcnow() - updated).total_seconds() // 3600)
        if hours >= 48:
            return f"{hours // 24}d ago"
        return f"{hours}h ago"
    except Exception:
        return "?"


def main():
    conn = get_connection()

    tasks = get_tasks(conn)
    stale = get_stale_work(conn)
    activity = get_activity(conn)

    conn.close()

    focus_tasks = tasks[:FOCUS_N]
    later_tasks = tasks[FOCUS_N:]
    stale_item = stale[0] if stale else None

    today_str = datetime.now().strftime("%A, %B %-d")

    print(f"\nTODAY — {today_str}")
    print("─" * 40)

    # Focus Today
    print("\n🔥 Focus Today")
    if focus_tasks:
        for row in focus_tasks:
            due = f"  (due {row['due_at'][:10]})" if row["due_at"] else ""
            print(f"  - {row['title']}{due}")
    else:
        print("  Nothing pending.")

    # Later
    if later_tasks:
        seen = set()
        deduped = []
        for row in later_tasks:
            key = row["title"].strip().lower()
            if key not in seen:
                seen.add(key)
                deduped.append(row)
        deduped = deduped[:5]
        print("\n⚠️  Later / Don't forget")
        for row in deduped:
            due = f"  (due {row['due_at'][:10]})" if row["due_at"] else ""
            print(f"  - {row['title'].strip()}{due}")

    # Resume
    print("\n🧠 Resume")
    if stale_item:
        age = fmt_stale_age(stale_item["last_updated_at"])
        print(f"  - {stale_item['title']}  [{age}]")
    else:
        print("  No stale work items.")

    # Completed Projects
    sw_finished = _read_last_blocks(SW_FINISHED, ITEMS_PER_CATEGORY)
    rw_finished = _read_last_blocks(RW_FINISHED, ITEMS_PER_CATEGORY)
    print("\n🚀 Completed Projects")
    print("\n  Software & Tools")
    if sw_finished:
        for item in sw_finished:
            print(f"  - {item}")
    else:
        print("  (none)")
    print("\n  Research & Writing")
    if rw_finished:
        for item in rw_finished:
            print(f"  - {item}")
    else:
        print("  (none)")

    # New Ideas
    sw_ideas = _read_last_blocks(SW_IDEAS, ITEMS_PER_CATEGORY)
    rw_ideas = _read_last_blocks_merged(RW_IDEAS_DIR, "ideas.txt", ITEMS_PER_CATEGORY)
    print("\n💡 New Ideas")
    print("\n  Software & Tools")
    if sw_ideas:
        for item in sw_ideas:
            print(f"  - {item}")
    else:
        print("  (none)")
    print("\n  Research & Writing")
    if rw_ideas:
        for item in rw_ideas:
            print(f"  - {item}")
    else:
        print("  (none)")

    # Activity
    print("\n Activity (today)")
    if activity:
        for row in activity:
            app = row["app"] or "(unknown)"
            print(f"  - {app}: {fmt_minutes(row['total_seconds'])}")
    else:
        print("  No activity recorded yet today.")

    # Suggestion
    print("\n→", make_suggestion(focus_tasks, stale_item))

    print()


if __name__ == "__main__":
    main()
