import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.services.work_item_reminders import get_stale_open_work_items

items = get_stale_open_work_items(hours=24)

if not items:
    print("No stale work items.")
else:
    print("Stale Work Items")
    print("----------------")
    for item in items:
        print(f"- {item['title']} [{item['tag']}]")
        print(f"  last update: {item['last_updated_at']}")
        print(f"  latest note: {item['latest_update']}")
