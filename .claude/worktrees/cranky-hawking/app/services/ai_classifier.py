import json
from openai import OpenAI
from app.config import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)

# Default returned when the API response cannot be parsed
_FALLBACK = {
    "event_type":         "note",
    "activity_label":     "general",
    "category":           "other",
    "productivity_label": "neutral",
}

_PROMPT_TEMPLATE = """You are an activity classification system.

Given a short user input describing what they are doing, return a JSON object with:

- event_type: one of ["start", "continue", "end", "switch", "note"]
- activity_label: short label like "studying", "coding", "youtube", "break"
- category: one of ["studying", "building", "admin", "break", "distraction", "other"]
- productivity_label: one of ["productive", "neutral", "unproductive"]

Rules:
- Be concise
- No explanations
- Only return valid JSON

User input:
"{raw_text}"
"""


def classify_event_ai(raw_text: str) -> dict:
    """Send raw_text to the OpenAI API and return a classification dict.

    Returns the same shape as the rule-based classifier:
      event_type, activity_label, category, productivity_label
    Falls back to default values if the response cannot be parsed.
    """
    prompt = _PROMPT_TEMPLATE.format(raw_text=raw_text)

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )

    content = response.choices[0].message.content.strip()

    print("AI RAW RESPONSE:", content)

    # Strip markdown code fences if the model wrapped the JSON
    if content.startswith("```"):
        lines = content.splitlines()
        # Drop the opening fence (```json or ```) and closing fence (```)
        lines = [l for l in lines if not l.strip().startswith("```")]
        content = "\n".join(lines).strip()

    try:
        parsed = json.loads(content)

        # Normalize category to expected set
        category = parsed.get("category", "")
        if category == "work":
            parsed["category"] = "building"
        elif category == "study":
            parsed["category"] = "studying"
        elif category == "rest":
            parsed["category"] = "break"

        return parsed
    except (json.JSONDecodeError, KeyError) as e:
        print("AI PARSE ERROR:", e, "| raw content:", content)
        return _FALLBACK.copy()
