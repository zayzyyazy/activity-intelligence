def classify_event(raw_text: str) -> dict:
    """Classify a raw activity string into structured fields.

    Uses simple keyword matching — no AI, no regex.
    Returns a dict with event_type, activity_label, category, productivity_label.
    All matching is done on lowercased input.
    """
    text = raw_text.lower()

    # --- Event type ---
    # Detect what kind of transition this event represents
    if any(word in text for word in ["start", "starting", "begin"]):
        event_type = "start"
    elif any(word in text for word in ["still", "continuing"]):
        event_type = "continue"
    elif any(word in text for word in ["done", "finished"]):
        event_type = "end"
    elif any(word in text for word in ["back", "switch"]):
        event_type = "switch"
    else:
        event_type = "note"

    # --- Activity label ---
    # Map keywords to a short label for the activity being described
    if any(word in text for word in ["math", "study", "revision"]):
        activity_label = "studying"
    elif any(word in text for word in ["code", "coding", "project"]):
        activity_label = "coding"
    elif any(word in text for word in ["youtube", "scroll", "instagram"]):
        activity_label = "social media"
    elif any(word in text for word in ["break", "rest"]):
        activity_label = "break"
    else:
        activity_label = "general"

    # --- Category ---
    # Broad bucket based on activity label
    category_map = {
        "studying":     "studying",
        "coding":       "building",
        "social media": "distraction",
        "break":        "break",
        "general":      "other",
    }
    category = category_map.get(activity_label, "other")

    # --- Productivity label ---
    # How productive is this activity considered to be
    if activity_label in ("studying", "coding"):
        productivity_label = "productive"
    elif activity_label == "break":
        productivity_label = "neutral"
    elif activity_label == "social media":
        productivity_label = "unproductive"
    else:
        productivity_label = "neutral"

    return {
        "event_type":         event_type,
        "activity_label":     activity_label,
        "category":           category,
        "productivity_label": productivity_label,
    }
