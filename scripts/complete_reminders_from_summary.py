import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from openai import OpenAI
from app.config import OPENAI_API_KEY
from app.db import init_db
from app.storage.reminders import get_pending_reminders, mark_reminder_done

client = OpenAI(api_key=OPENAI_API_KEY)

_PROMPT_TEMPLATE = """You are a reminder-matching assistant.

The user has provided a plain-text summary of what they completed today.
Below is a list of their pending reminders, each with an id and title.

Your job: identify which reminders from the list are clearly completed based on the summary.
Be conservative — only include reminders where the match is reasonably clear.
Do not invent, rephrase, or add reminders that are not in the list.

Return ONLY a JSON array of reminder ids that were completed.
If nothing matches, return an empty array: []
No explanations. No markdown. Only valid JSON.

--- Pending reminders ---
{reminder_list}

--- User summary ---
{summary}

Return only a JSON array of matched reminder ids."""


def build_reminder_list(reminders) -> str:
    lines = []
    for r in reminders:
        lines.append(f'id: {r["id"]}  title: {r["title"]}')
    return "\n".join(lines)


def ask_openai(summary: str, reminders) -> list[str]:
    reminder_list = build_reminder_list(reminders)
    prompt = _PROMPT_TEMPLATE.format(reminder_list=reminder_list, summary=summary)

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )

    content = response.choices[0].message.content.strip()

    # Strip markdown fences if present
    if content.startswith("```"):
        lines = [l for l in content.splitlines() if not l.strip().startswith("```")]
        content = "\n".join(lines).strip()

    try:
        result = json.loads(content)
        if not isinstance(result, list):
            print("AI returned unexpected format (not a list). Marking nothing done.")
            return []
        # Only keep ids that actually exist in pending reminders (safety check)
        valid_ids = {r["id"] for r in reminders}
        filtered = [item for item in result if isinstance(item, str) and item in valid_ids]
        return filtered
    except json.JSONDecodeError as e:
        print(f"AI response could not be parsed: {e}\nRaw response: {content}")
        return []


def main():
    if len(sys.argv) > 1:
        summary = " ".join(sys.argv[1:])
    else:
        summary = input("What did you complete today? ").strip()

    if not summary:
        print("No summary provided. Exiting.")
        sys.exit(0)

    init_db()
    pending = get_pending_reminders()

    if not pending:
        print("No pending reminders found.")
        sys.exit(0)

    matched_ids = ask_openai(summary, pending)

    if not matched_ids:
        print("No reminders matched your summary. Nothing was marked done.")
        sys.exit(0)

    id_to_title = {r["id"]: r["title"] for r in pending}

    print("\nMatched reminders:")
    for rid in matched_ids:
        print(f"  - {id_to_title[rid]}")
        mark_reminder_done(rid)

    count = len(matched_ids)
    print(f"\nMarked {count} reminder{'s' if count != 1 else ''} done.")


if __name__ == "__main__":
    main()
