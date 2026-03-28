import json
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from openai import OpenAI
from app.config import OPENAI_API_KEY
from app.db import init_db
from app.models.reminder_item import ReminderItem
from app.storage.reminders import save_reminder

client = OpenAI(api_key=OPENAI_API_KEY)

_PROMPT_TEMPLATE = """You are a reminder parser. Given a natural-language reminder input, return a JSON object with:

- title: short, clean action title (required, imperative tone, e.g. "Clean up the dock")
- due_at: ISO 8601 datetime string if a due date/time is clearly implied, otherwise null
- note: any extra context worth keeping, otherwise null

Rules:
- Keep the title short and clean — strip filler like "maybe", "probably", "after lunch"
- Only include due_at if a specific date or deadline is mentioned
- If only a date is mentioned with no time, use 23:59 as the time
- Today's date is {today}
- Only return valid JSON, no explanation

Input:
"{raw_text}"
"""


def parse_reminder(raw_text: str) -> dict:
    today = datetime.now().strftime("%Y-%m-%d")
    prompt = _PROMPT_TEMPLATE.format(raw_text=raw_text, today=today)

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )

    content = response.choices[0].message.content.strip()

    if content.startswith("```"):
        lines = [l for l in content.splitlines() if not l.strip().startswith("```")]
        content = "\n".join(lines).strip()

    return json.loads(content)


def main():
    if len(sys.argv) > 1:
        raw_text = " ".join(sys.argv[1:])
    else:
        raw_text = input("Reminder: ").strip()

    if not raw_text:
        print("No input provided.")
        sys.exit(1)

    parsed = parse_reminder(raw_text)

    title = parsed.get("title", "").strip()
    note = parsed.get("note") or None
    due_at = None

    raw_due = parsed.get("due_at")
    if raw_due:
        try:
            due_at = datetime.fromisoformat(raw_due)
        except ValueError:
            pass

    if not title:
        print("Could not extract a title. Aborting.")
        sys.exit(1)

    init_db()

    reminder = ReminderItem(title=title, note=note, due_at=due_at)
    save_reminder(reminder)

    due_str = f"  due: {due_at.strftime('%Y-%m-%d %H:%M')}" if due_at else ""
    note_str = f"  note: {note}" if note else ""
    print(f"Saved: {title}{due_str}{note_str}")


if __name__ == "__main__":
    main()
