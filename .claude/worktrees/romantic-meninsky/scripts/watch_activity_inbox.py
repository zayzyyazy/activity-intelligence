"""
watch_activity_inbox.py — Watch the iCloud inbox and auto-ingest on change.

Monitors the iCloud Shortcuts folder for changes to activity_log_inbox.txt.
When the file is modified, runs ingest_activity_inbox.py automatically.

A 2-second debounce prevents duplicate triggers from rapid filesystem events
(iCloud sync often fires multiple events per write).

Usage:
    python3 scripts/watch_activity_inbox.py

Stop with Ctrl+C.
"""

import re
import subprocess
import sys
import time
from pathlib import Path

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

WATCH_DIR  = Path.home() / "Library/Mobile Documents/com~apple~CloudDocs/Shortcuts"
INBOX_FILE = "activity_log_inbox.txt"
INGEST_SCRIPT = Path(__file__).parent / "ingest_activity_inbox.py"
DEBOUNCE_SECONDS = 2


def notify(message: str) -> None:
    subprocess.run(
        ["osascript", "-e", f'display notification "{message}" with title "Activity Intelligence"'],
        check=False,
    )


class InboxHandler(FileSystemEventHandler):
    def __init__(self):
        self._last_triggered = 0.0

    def on_modified(self, event):
        if event.is_directory:
            return
        if Path(event.src_path).name != INBOX_FILE:
            return

        now = time.time()
        if now - self._last_triggered < DEBOUNCE_SECONDS:
            return
        self._last_triggered = now

        print(f"\nInbox updated → ingesting...")
        try:
            result = subprocess.run(
                [sys.executable, str(INGEST_SCRIPT)],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.stdout:
                print(result.stdout, end="")
            if result.returncode != 0:
                print(f"Ingest exited with code {result.returncode}.")
            else:
                for line in result.stdout.splitlines():
                    m = re.search(r"✓ \[.*?\] (.+?) \(", line)
                    if m:
                        notify(f"Activity imported: {m.group(1)}")
        except Exception as e:
            print(f"Failed to run ingest script: {e}")


def main():
    if not WATCH_DIR.exists():
        print(f"Watch directory not found: {WATCH_DIR}")
        print("Make sure iCloud Drive is enabled and the Shortcuts folder exists.")
        sys.exit(1)

    handler  = InboxHandler()
    observer = Observer()
    observer.schedule(handler, str(WATCH_DIR), recursive=False)
    observer.start()

    print(f"Watching iCloud inbox for activity logs...")
    print(f"  Directory : {WATCH_DIR}")
    print(f"  File      : {INBOX_FILE}")
    print(f"  Debounce  : {DEBOUNCE_SECONDS}s")
    print(f"  Ingest    : {INGEST_SCRIPT}")
    print(f"\nPress Ctrl+C to stop.\n")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping watcher.")
        observer.stop()

    observer.join()


if __name__ == "__main__":
    main()
