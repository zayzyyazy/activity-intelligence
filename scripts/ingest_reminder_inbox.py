"""
ingest_reminder_inbox.py — Import reminders from the iCloud inbox file.

The iPhone/iPad Shortcut appends one reminder title per line to:
  ~/Library/Mobile Documents/com~apple~CloudDocs/Shortcuts/reminder_inbox.txt

This script reads those lines and saves each one as a ReminderItem
(title only, status=pending) using the existing reminder storage flow.

After a successful run the inbox file is cleared (truncated to empty).
Failed lines are written back so they can be retried.

Usage:
    python3 scripts/ingest_reminder_inbox.py
"""

import sys
from pathlib import Path

# Ensure project root is on the path when run as a script
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db import init_db
from app.models.reminder_item import ReminderItem
from app.storage.reminders import save_reminder

INBOX_PATH = (
    Path.home()
    / "Library/Mobile Documents/com~apple~CloudDocs/Shortcuts/reminder_inbox.txt"
)


def main() -> None:
    if not INBOX_PATH.exists():
        print(f"Inbox file not found: {INBOX_PATH}")
        print("Create it on your iPhone using the Shortcuts app and try again.")
        sys.exit(0)

    lines = [l.strip() for l in INBOX_PATH.read_text().splitlines() if l.strip()]

    if not lines:
        print("Inbox is empty. Nothing to import.")
        sys.exit(0)

    print(f"Found {len(lines)} reminder(s) in inbox. Importing...\n")

    init_db()

    failed = []
    for title in lines:
        print(f"  -> {title}")
        try:
            reminder = ReminderItem(title=title)
            save_reminder(reminder)
            print(f"  + saved: {reminder.id}")
        except Exception as e:
            print(f"  x Failed: {e}")
            failed.append(title)

    imported = len(lines) - len(failed)
    print(f"\n{imported}/{len(lines)} reminder(s) imported.")

    if failed:
        print("\nThe following lines could not be imported and will remain in the inbox:")
        for line in failed:
            print(f"  - {line}")
        INBOX_PATH.write_text("\n".join(failed) + "\n")
    else:
        INBOX_PATH.write_text("")
        print("Inbox cleared.")


if __name__ == "__main__":
    main()
