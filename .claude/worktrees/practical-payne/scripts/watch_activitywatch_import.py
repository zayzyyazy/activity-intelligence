import subprocess
import time

print("Auto-syncing ActivityWatch every 5 minutes...")

while True:
    try:
        subprocess.run(["python3", "scripts/ingest_activitywatch.py"], check=True)
    except Exception as e:
        print(f"Import error: {e}")
    time.sleep(300)
