import sqlite3
from datetime import date
from pathlib import Path

import pandas as pd

from app.config import OPENAI_API_KEY
from app.storage.work_items import get_all_open_work_items
from app.services.work_item_reminders import get_stale_open_work_items

DB_PATH = Path(__file__).parent.parent.parent / "data" / "activity.db"


def run_daily_checkup() -> None:
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM activity_events", conn)
    conn.close()

    if df.empty:
        print("No events found for today.")
        return

    df["timestamp"] = pd.to_datetime(df["timestamp"])
    today = date.today()
    df = df[df["timestamp"].dt.date == today]

    if df.empty:
        print("No events found for today.")
        return

    # Duration estimation
    df = df.sort_values("timestamp").reset_index(drop=True)
    df["duration_minutes"] = (
        df["timestamp"].shift(-1) - df["timestamp"]
    ).dt.total_seconds() / 60
    df.loc[df.index[-1], "duration_minutes"] = 1.0  # default for last event

    total_events = len(df)
    total_time = df["duration_minutes"].sum()
    productive_time = df.loc[
        df["productivity_label"] == "productive", "duration_minutes"
    ].sum()

    category_counts = df["category"].value_counts()
    productivity_counts = df["productivity_label"].value_counts()
    top_activity = df["activity_label"].mode()[0]

    print("Daily Checkup")
    print("-------------")
    print(f"Total events: {total_events}")
    print(f"Total time:   {total_time:.1f} minutes")
    print(f"Productive time: {productive_time:.1f} minutes")

    print("\nBy category:")
    for cat, count in category_counts.items():
        print(f"  - {cat}: {count}")

    print("\nProductivity:")
    for label, count in productivity_counts.items():
        print(f"  - {label}: {count}")

    print("\nTop activity:")
    print(f"  - {top_activity}")

    open_items = get_all_open_work_items()
    print("\nOpen Work Items")
    print("---------------")
    if not open_items:
        print("No open work items.")
    else:
        for item in open_items:
            print(f"- {item['title']} [{item['tag']}]")
            print(f"  started:     {item['started_at']}")
            print(f"  last update: {item['last_updated_at']}")
            print(f"  latest note: {item['latest_update'] or 'none'}")

    stale_items = get_stale_open_work_items(hours=24)
    print("\nStale Work Items")
    print("----------------")
    if not stale_items:
        print("No stale work items.")
    else:
        for item in stale_items:
            print(f"- {item['title']} [{item['tag']}]")
            print(f"  last update: {item['last_updated_at']}")
            print(f"  latest note: {item['latest_update'] or 'none'}")

    # Compute passive + alignment data early so it is available for the AI prompt
    top_logged = (
        df.groupby("activity_label")["duration_minutes"]
        .sum()
        .sort_values(ascending=False)
        .head(5)
    )

    today_str = today.isoformat()
    _pc = sqlite3.connect(DB_PATH)
    _pc.row_factory = sqlite3.Row
    passive_rows = _pc.execute(
        "SELECT app, duration_seconds FROM passive_events WHERE DATE(timestamp) = ?",
        (today_str,),
    ).fetchall()
    _pc.close()

    top_apps: list[tuple[str, float]] = []
    if passive_rows:
        _totals: dict[str, float] = {}
        for _r in passive_rows:
            _a = _r["app"] or "(unknown)"
            _totals[_a] = _totals.get(_a, 0.0) + (_r["duration_seconds"] or 0.0)
        top_apps = sorted(_totals.items(), key=lambda x: x[1], reverse=True)[:5]

    _CODING_APPS  = {"code", "terminal", "iterm", "iterm2", "xcode", "pycharm",
                     "intellij", "cursor", "sublime", "vim", "neovim"}
    _BROWSER_APPS = {"safari", "chrome", "firefox", "arc", "edge", "brave", "opera"}
    _STUDY_APPS   = {"preview", "acrobat", "kindle", "books", "notion",
                     "obsidian", "anki", "zotero"}

    alignment_messages: list[str] = []
    if top_apps:
        _pa = {a.lower() for a, _ in top_apps}
        _la = {lbl.lower() for lbl in top_logged.index}
        _has_coding  = bool(_pa & _CODING_APPS)
        _has_browser = bool(_pa & _BROWSER_APPS)
        _has_study   = bool(_pa & _STUDY_APPS)

        if any(kw in lbl for lbl in _la for kw in ("cod", "build", "programming", "dev", "script")):
            if _has_coding:
                alignment_messages.append(
                    "Logged coding appears aligned with passive activity (Code, Terminal detected)."
                )
            elif _has_browser:
                alignment_messages.append(
                    "Logged coding may not fully align — browser was most active in passive data."
                )

        if any(kw in lbl for lbl in _la for kw in ("study", "revision", "lecture", "math", "university", "reading", "research")):
            if _has_coding or _has_study:
                alignment_messages.append(
                    "Logged studying appears reasonably aligned with passive activity."
                )
            elif _has_browser:
                alignment_messages.append(
                    "Logged studying may not fully align — browser was dominant in passive data (YouTube, Safari)."
                )

        if any(kw in lbl for lbl in _la for kw in ("break", "rest", "youtube", "social")):
            if _has_browser:
                alignment_messages.append(
                    "Logged break/distraction aligns with browser usage — acceptable."
                )

    api_key = OPENAI_API_KEY
    if api_key:
        from openai import OpenAI

        client = OpenAI(api_key=api_key)

        if open_items:
            open_items_text = "\n".join(
                f"- {item['title']} [{item['tag']}], started {item['started_at']}, "
                f"last update {item['last_updated_at']}, "
                f"latest note: {item['latest_update'] or 'none'}"
                for item in open_items
            )
        else:
            open_items_text = "None"

        if stale_items:
            stale_items_text = "\n".join(
                f"- {item['title']} [{item['tag']}], last update {item['last_updated_at']}, "
                f"latest note: {item['latest_update'] or 'none'}"
                for item in stale_items
            )
        else:
            stale_items_text = "None"

        alignment_notes_text = (
            "\n".join(f"- {m}" for m in alignment_messages)
            if alignment_messages else "none"
        )

        summary_data = f"""
Total events: {total_events}
Total time: {total_time:.1f} minutes
Productive time: {productive_time:.1f} minutes

Category breakdown:
{category_counts.to_dict()}

Productivity breakdown:
{productivity_counts.to_dict()}

Top activity: {top_activity}

Open work items:
{open_items_text}

Stale work items (not updated in 24+ hours):
{stale_items_text}

Alignment notes:
{alignment_notes_text}
"""

        prompt = f"""
You are a productivity coach reviewing someone's end-of-day activity log.

Provide a brief daily summary (3–5 sentences) covering:
- how the day went overall
- main focus areas
- any notable patterns or distractions
- which open work items look worth continuing tomorrow, and which (if any) should be closed or deprioritised
- for any stale work items, suggest whether to continue, close, or deprioritise them
- if alignment notes suggest a mismatch between logged work and passive activity, name it clearly and suggest one concrete fix for tomorrow
- one small actionable suggestion for tomorrow

Data:
{summary_data}
"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
        )
        ai_summary = response.choices[0].message.content

        print("\nAI Daily Summary")
        print("----------------")
        print(ai_summary)

    # --- Passive vs Logged Activity ---
    print("\nPassive vs Logged Activity")
    print("--------------------------")

    print("\nTop logged activities:")
    for label, minutes in top_logged.items():
        print(f"  - {label}: {minutes:.0f} min")

    if not top_apps:
        print("\nNo passive activity found for today.")
    else:
        print("\nTop passive apps:")
        for app, seconds in top_apps:
            print(f"  - {app}: {seconds / 60:.0f} min")

    # --- Alignment Check ---
    print("\nAlignment Check")
    print("---------------")

    if not top_apps:
        print("Not enough passive data for alignment check.")
    else:
        to_print = alignment_messages if alignment_messages else [
            "No clear alignment pattern detected from available data."
        ]
        for msg in to_print:
            print(f"  {msg}")


if __name__ == "__main__":
    run_daily_checkup()
