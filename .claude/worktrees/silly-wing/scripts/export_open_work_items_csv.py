import sqlite3
import pandas as pd
from pathlib import Path

DB_PATH  = Path(__file__).parent.parent / "data" / "activity.db"
CSV_PATH = Path(__file__).parent.parent / "data" / "open_work_items.csv"

COLUMNS = [
    "title",
    "tag",
    "started_at",
    "last_updated_at",
    "latest_update",
]

conn = sqlite3.connect(DB_PATH)
df = pd.read_sql_query("SELECT * FROM work_items WHERE status = 'in_progress'", conn)
conn.close()

if df.empty:
    pd.DataFrame(columns=COLUMNS).to_csv(CSV_PATH, index=False)
    print("No open work items found.")
else:
    df = df[COLUMNS]
    df.to_csv(CSV_PATH, index=False)
    print(f"Exported {len(df)} open work items to {CSV_PATH}")
