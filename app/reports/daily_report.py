import os
import sqlite3
from datetime import date
from pathlib import Path

import pandas as pd

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

    api_key = os.environ.get("OPENAI_API_KEY")
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
"""

        prompt = f"""
You are a productivity coach reviewing someone's end-of-day activity log.

Provide a brief daily summary (3–5 sentences) covering:
- how the day went overall
- main focus areas
- any notable patterns or distractions
- which open work items look worth continuing tomorrow, and which (if any) should be closed or deprioritised
- for any stale work items, suggest whether to continue, close, or deprioritise them
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


if __name__ == "__main__":
    run_daily_checkup()
