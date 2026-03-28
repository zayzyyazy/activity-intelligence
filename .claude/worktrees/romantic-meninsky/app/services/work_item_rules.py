from app.models.activity_event import ActivityEvent, Category
from app.models.work_item import WorkTag


# Words in raw_text that signal a non-work event regardless of category
_SKIP_WORDS = {
    "walk", "walked", "walking",
    "lunch", "dinner", "breakfast", "eat", "eating", "food",
    "break", "rest", "nap",
    "youtube", "instagram", "twitter", "tiktok", "netflix", "scroll",
}

# Keyword sets mapped to a WorkTag — checked against activity_label and raw_text
_TAG_KEYWORDS: list[tuple[set[str], WorkTag]] = [
    (
        {"study", "studying", "exam", "lecture", "course", "university", "uni",
         "revision", "revise", "assignment", "homework", "tutorial", "seminar"},
        WorkTag.UNIVERSITY,
    ),
    (
        {"research", "researching", "investigate", "investigating", "literature",
         "paper", "papers", "reading"},
        WorkTag.RESEARCH,
    ),
    (
        {"writing", "write", "essay", "draft", "drafting", "notes", "note",
         "documentation", "doc", "blog", "report"},
        WorkTag.WRITING,
    ),
    (
        {"coding", "code", "build", "building", "project", "feature", "implement",
         "implementing", "programming", "debug", "debugging", "dev", "develop",
         "developing", "deploy", "deploying", "script", "scripting"},
        WorkTag.PERSONAL_PROJECT,
    ),
    (
        {"admin", "plan", "planning", "schedule", "scheduling", "organise",
         "organize", "meeting", "email", "emails", "review", "reviewing"},
        WorkTag.ADMIN,
    ),
]


def should_create_work_item(event: ActivityEvent) -> bool:
    """Return True if this event represents meaningful work worth tracking.

    Filters out distractions, breaks, and low-value activities before
    attempting any tag inference.
    """
    # Skip known non-work categories outright
    if event.category in (Category.DISTRACTION, Category.BREAK):
        return False

    # Skip if raw text contains any known skip words
    raw_lower = event.raw_text.lower()
    if any(word in raw_lower for word in _SKIP_WORDS):
        return False

    # Only proceed if at least one tag keyword matches
    return infer_work_tag(event) != WorkTag.OTHER


def infer_work_tag(event: ActivityEvent) -> WorkTag:
    """Return the best-matching WorkTag for this event.

    Checks activity_label first (already normalised by the classifier),
    then falls back to scanning raw_text directly.
    Returns WorkTag.OTHER if no keywords match.
    """
    label_lower = event.activity_label.lower()
    raw_lower = event.raw_text.lower()

    for keywords, tag in _TAG_KEYWORDS:
        if any(kw in label_lower for kw in keywords):
            return tag
        if any(kw in raw_lower for kw in keywords):
            return tag

    return WorkTag.OTHER
