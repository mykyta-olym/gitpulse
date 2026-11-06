"""Text analysis utilities for review comment quality."""

import re


def word_count(text: str | None) -> int:
    """Count words in text, handling None and empty strings."""
    if not text:
        return 0
    return len(text.split())


def char_count(text: str | None) -> int:
    """Count non-whitespace characters."""
    if not text:
        return 0
    return len(re.sub(r"\s+", "", text))


def is_meaningful_comment(text: str | None, min_words: int = 15) -> bool:
    """Determine if a comment is meaningful (not trivial).

    Trivial patterns: "ok", "lgtm", "+1", "looks good", "👍", etc.
    """
    if not text:
        return False

    # Strip markdown formatting artifacts
    cleaned = re.sub(r"[>`*_~\[\]()]", "", text).strip()

    # Trivial patterns
    trivial = {
        "ok",
        "okay",
        "lgtm",
        "looks good",
        "looks fine",
        "good",
        "nice",
        "great",
        "+1",
        "approved",
        "done",
        "fixed",
        "thanks",
        "thank you",
        "thx",
        "ack",
        "noted",
        "yes",
        "no",
        "nope",
    }

    if cleaned.lower().strip() in trivial:
        return False

    # Emoji-only comments
    if len(re.sub(r"[\s\U00010000-\U0010ffff]", "", cleaned)) == 0:
        return False

    return word_count(cleaned) >= min_words
