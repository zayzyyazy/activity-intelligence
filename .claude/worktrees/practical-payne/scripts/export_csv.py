import sqlite3
import pandas as pd
from pathlib import Path

DB_PATH  = Path(__file__).parent.parent / "data" / "activity.db"
CSV_PATH = Path(__file__).parent.parent / "data" / "activity_log.csv"

conn = sqlite3.connect(DB_PATH)
df = pd.read_sql_query("SELECT * FROM activity_events", conn)
conn.close()

COLUMNS = [
    "timestamp",
    "clean_summary",
    "event_type",
    "activity_label",
    "category",
    "productivity_label",
]

df = df[COLUMNS]
df.to_csv(CSV_PATH, index=False)

print(f"Exported {len(df)} rows to {CSV_PATH}")
