import sqlite3
import pandas as pd
from pathlib import Path

DB_PATH  = Path(__file__).parent.parent / "data" / "activity.db"
CSV_PATH = Path(__file__).parent.parent / "data" / "work_items.csv"

COLUMNS = [
    "title",
    "tag",
    "status",
    "started_at",
    "last_updated_at",
    "latest_update",
    "finished_at",
]

conn = sqlite3.connect(DB_PATH)
df = pd.read_sql_query("SELECT * FROM work_items", conn)
conn.close()

if df.empty:
    # Write headers-only CSV so the file exists and is ready to open
    pd.DataFrame(columns=COLUMNS).to_csv(CSV_PATH, index=False)
    print("No work items found.")
else:
    df = df[COLUMNS]
    df.to_csv(CSV_PATH, index=False)
    print(f"Exported {len(df)} work items to {CSV_PATH}")
