import sqlite3
import pandas as pd
from pathlib import Path
from app.config import OPENAI_API_KEY
from openai import OpenAI

DB_PATH = Path(__file__).parent.parent.parent / "data" / "activity.db"

client = OpenAI(api_key=OPENAI_API_KEY)


def run_weekly_summary() -> None:
    """Load all events from the DB and print a weekly summary to the terminal."""
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM activity_events", conn)
    conn.close()

    if df.empty:
        print("No events found.")
        return

    # Sort and compute time-based durations
    df = df.sort_values("timestamp").reset_index(drop=True)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["duration_minutes"] = (
        df["timestamp"].shift(-1) - df["timestamp"]
    ).dt.total_seconds() / 60
    df.loc[df.index[-1], "duration_minutes"] = 1.0  # default for last event

    total_time      = df["duration_minutes"].sum()
    productive_time = df.loc[df["productivity_label"] == "productive", "duration_minutes"].sum()
    focus_score     = (productive_time / total_time) * 100 if total_time > 0 else 0.0

    total_events = len(df)

    category_counts    = df["category"].value_counts()
    productivity_counts = df["productivity_label"].value_counts()
    top_activity       = df["activity_label"].mode()[0]

    print("Weekly Summary")
    print("--------------")
    print(f"Total events: {total_events}")
    print(f"Total time:   {total_time:.1f} min")
    print(f"Productive:   {productive_time:.1f} min")

    print("\nBy category:")
    for cat, count in category_counts.items():
        print(f"  - {cat}: {count}")

    print("\nProductivity:")
    for label, count in productivity_counts.items():
        print(f"  - {label}: {count}")

    print("\nTop activity:")
    print(f"  - {top_activity}")

    print("\nFocus score:")
    print(f"  - {focus_score:.1f}%")

    summary_data = f"""
Total events: {total_events}
Total time: {total_time:.1f} minutes
Productive time: {productive_time:.1f} minutes

Category breakdown:
{category_counts.to_dict()}

Productivity breakdown:
{productivity_counts.to_dict()}

Focus score: {focus_score:.1f}%
"""

    prompt = f"""
You are a productivity coach.

Analyze this weekly activity data and provide:
- key patterns
- main distractions
- strengths
- 1–2 actionable suggestions

Be concise (4–6 sentences max).

Data:
{summary_data}
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    ai_summary = response.choices[0].message.content

    print("\nAI Weekly Review")
    print("----------------")
    print(ai_summary)


if __name__ == "__main__":
    run_weekly_summary()
