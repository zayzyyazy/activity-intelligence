import argparse
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.db import init_db
from app.storage.reminders import get_pending_reminders, mark_reminder_done

parser = argparse.ArgumentParser(description="Mark a reminder as done.")
parser.add_argument("identifier", help="Reminder id or exact title")
args = parser.parse_args()

init_db()

pending = get_pending_reminders()

# Try exact id match first
id_match = next((r for r in pending if r["id"] == args.identifier), None)
if id_match:
    mark_reminder_done(id_match["id"])
    print(f"Reminder marked done: {id_match['title']}")
    sys.exit(0)

# Fall back to exact title match
title_matches = [r for r in pending if r["title"] == args.identifier]

if not title_matches:
    print(f"No pending reminder found matching: {args.identifier}")
    sys.exit(1)

if len(title_matches) > 1:
    print("Multiple pending reminders with that title. Use the id instead:")
    for r in title_matches:
        print(f"  id: {r['id']}  title: {r['title']}")
    sys.exit(1)

match = title_matches[0]
mark_reminder_done(match["id"])
print(f"Reminder marked done: {match['title']}")
