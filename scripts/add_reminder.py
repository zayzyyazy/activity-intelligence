import argparse
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.db import init_db
from app.models.reminder_item import ReminderItem
from app.storage.reminders import save_reminder

parser = argparse.ArgumentParser(description="Add a reminder.")
parser.add_argument("title", help="Short description of the reminder")
parser.add_argument("--note", default=None, help="Optional longer note")
parser.add_argument("--due", default=None, help="Optional due date, e.g. '2026-03-22 18:00'")
args = parser.parse_args()

due_at = None
if args.due:
    due_at = datetime.strptime(args.due, "%Y-%m-%d %H:%M")

init_db()

reminder = ReminderItem(
    title=args.title,
    note=args.note,
    due_at=due_at,
)

save_reminder(reminder)

due_str = f"  due: {due_at.strftime('%Y-%m-%d %H:%M')}" if due_at else ""
print(f"Reminder saved: {reminder.title}{due_str}")
