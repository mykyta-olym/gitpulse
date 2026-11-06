import re
from typing import Any, ClassVar


class RedactionService:
    """
    Sanitizes text to remove sensitive information before sending to LLM.
    Strict privacy constraints:
    - No secrets (GitLab tokens, AWS keys, generic long hex strings).
    - No potential PII (emails).
    - No URLs that might leak internal tokens.
    """

    PATTERNS: ClassVar[dict[str, str]] = {
        "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
        "at_mention": r"@[A-Za-z0-9_][A-Za-z0-9_.\-]{0,38}",
        "ipv4": r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b",
        "bearer_token": r"Bearer\s+[a-zA-Z0-9\-\._~\+\/]+=*",
        "gitlab_token": r"token_prefix_[0-9a-zA-Z\-\_]{20,}",
        "generic_secret": (
            r"(?i)(api_key|secret|password|token)\s*[:=]\s*"
            r"['\"]?[a-zA-Z0-9\-\._~\+\/]{8,}['\"]?"
        ),
        "long_hex": r"\b[a-fA-F0-9]{32,}\b",  # MD5/SHA-ish
    }

    @classmethod
    def redact(cls, text: str) -> str:
        if not text:
            return ""

        redacted = text
        for name, pattern in cls.PATTERNS.items():
            redacted = re.sub(pattern, f"<{name.upper()}_REDACTED>", redacted)

        return redacted

    @classmethod
    def minimize_mr_context(
        cls,
        title: str,
        description: str,
        comments: list[dict[str, Any]],
        filenames: list[str],
        metadata: dict[str, Any] | None = None,
        diffs: list[dict[str, Any]] | None = None,
        max_diff_chars: int = 8000,
    ) -> str:
        """
        Constructs a minimized prompt context with traceable IDs.

        Args:
            title: MR Title
            description: MR Description
            comments: List of dicts with keys: 'id' (str/int), 'body' (str),
                'author' (str), 'created_at' (str/datetime)
            filenames: List of changed filenames
        """
        redacted_title = cls.redact(title)
        redacted_desc = cls.redact(description)

        context = f"MR Title: {redacted_title}\n"
        context += f"MR Description: {redacted_desc}\n\n"

        if metadata:
            context += "MR Metadata:\n"
            for key, value in metadata.items():
                if value is None:
                    continue
                # Redact string values (e.g. branch names) - they can carry a
                # student handle / email; non-strings (ints, bools) pass through.
                safe_value = cls.redact(value) if isinstance(value, str) else value
                context += f"- {key}: {safe_value}\n"
            context += "\n"

        if filenames:
            # File paths may embed a username; redact each before sending.
            context += (
                "Filenames involved:\n"
                + "\n".join(f"- {cls.redact(fn)}" for fn in filenames)
                + "\n\n"
            )

        if diffs:
            context += "Diffs (truncated):\n"
            used_chars = 0
            for diff in diffs:
                # File paths can embed a student handle / email (e.g.
                # "src/jane.doe@uni.edu/x.py"), so redact the header too -
                # matching how the standalone `filenames` list is handled.
                file_path = cls.redact(diff.get("file_path", "unknown"))
                raw_diff = diff.get("diff", "") or ""
                if not raw_diff:
                    continue
                redacted_diff = cls.redact(raw_diff)
                remaining = max_diff_chars - used_chars
                if remaining <= 0:
                    break
                if len(redacted_diff) > remaining:
                    redacted_diff = redacted_diff[:remaining] + "\n...[truncated]"
                context += f"--- {file_path} ---\n{redacted_diff}\n\n"
                used_chars += len(redacted_diff)

        context += "Discussion History:\n"
        if not comments:
            context += "(No comments)\n"

        # Map real author handles to anonymous labels for privacy
        author_map: dict[str, str] = {}
        author_counter = 0

        for comment in comments:
            c_id = comment.get("id", "unknown")
            c_body = cls.redact(comment.get("body", ""))
            raw_author = comment.get("author", "unknown_user")
            if raw_author not in author_map:
                author_counter += 1
                author_map[raw_author] = f"Participant_{author_counter}"
            c_author = author_map[raw_author]
            c_date = comment.get("created_at", "")

            context += f"--- Note ID: {c_id} ---\n"
            context += f"Author: {c_author} | Date: {c_date}\n"
            context += f"Content:\n{c_body}\n\n"

        return context
