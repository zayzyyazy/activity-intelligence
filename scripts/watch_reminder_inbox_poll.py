import subprocess
import time

print("Auto-syncing reminder inbox every 10 seconds...")

while True:
    try:
        subprocess.run(["python3", "scripts/ingest_reminder_inbox.py"], check=True)
    except Exception as e:
        print(f"Import error: {e}")
    time.sleep(10)
