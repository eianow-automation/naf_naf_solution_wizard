def join_human(items):
    """
    Join a list of strings with commas and 'and' for the last item.
    Empty/falsey items are ignored. If none remain, returns 'TBD'.
    """
    items = [i for i in (items or []) if i]
    if not items:
        return "TBD"
    if len(items) == 1:
        return items[0]
    return ", ".join(items[:-1]) + f" and {items[-1]}"


def md_line(text: str) -> str:
    """Return a Markdown bullet line if text is non-empty, else empty string."""
    return f"- {text}" if text else ""


def is_meaningful(text: str) -> bool:
    """
    Determine if a sentence contains meaningful content (not placeholders/TBD).
    """
    if not text:
        return False
    t = text.strip().lower()
    if not t or "tbd" in t:
        return False
    default_placeholders = {
        "no additional gating logic beyond the defined go/no-go criteria.",
        "this solution will not employ a distinct orchestration layer.",
    }
    return t not in default_placeholders
