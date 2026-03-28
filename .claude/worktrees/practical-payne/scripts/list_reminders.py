import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.db import init_db
from app.storage.reminders import get_pending_reminders

init_db()

reminders = get_pending_reminders()

print("Pending Reminders")
print("-----------------")

if not reminders:
    print("No pending reminders.")
else:
    for r in reminders:
        print(f"- {r['id']}")
        print(f"  title: {r['title']}")
        print(f"  due:   {r['due_at'] or 'none'}")
        print(f"  note:  {r['note'] or 'none'}")
