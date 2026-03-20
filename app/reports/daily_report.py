import os
import sqlite3
from datetime import date
from pathlib import Path

import pandas as pd

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

    api_key = os.environ.get("OPENAI_API_KEY")
    if api_key:
        from openai import OpenAI

        client = OpenAI(api_key=api_key)

        summary_data = f"""
Total events: {total_events}
Total time: {total_time:.1f} minutes
Productive time: {productive_time:.1f} minutes

Category breakdown:
{category_counts.to_dict()}

Productivity breakdown:
{productivity_counts.to_dict()}

Top activity: {top_activity}
"""

        prompt = f"""
You are a productivity coach reviewing someone's end-of-day activity log.

Provide a brief daily summary (3–5 sentences) covering:
- how the day went overall
- main focus areas
- any notable patterns or distractions
- one small suggestion for tomorrow

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
