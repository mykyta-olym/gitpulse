"""HTTP header helpers.

Provides RFC 5987 ``Content-Disposition`` encoding so filenames with
non-ASCII characters (``č``, ``ě``, ``á``, Cyrillic, CJK, ...) do not
trigger ``UnicodeEncodeError: 'latin-1' codec can't encode character``
when Starlette/uvicorn serialises response headers.
"""

from __future__ import annotations

from urllib.parse import quote


def content_disposition_attachment(filename: str) -> str:
    """Return an RFC 5987-compliant ``Content-Disposition`` header value.

    Emits both a legacy ASCII ``filename=`` (with unsafe chars replaced
    by underscore) and a ``filename*=UTF-8''...`` form that modern browsers
    prefer.  This avoids the HTTP/1.1 latin-1 header limitation.

    Example: ``ApI 1 (Kolosovskyi - Penička).json`` ->
    ``attachment; filename="ApI 1 (Kolosovskyi - Peni_ka).json";
    filename*=UTF-8''ApI%201%20%28Kolosovskyi%20-%20Peni%C4%8Dka%29.json``
    """
    # ASCII fallback: replace any non-latin-1 char + quotes/backslash.
    ascii_safe_chars = []
    for ch in filename:
        try:
            ch.encode("latin-1")
        except UnicodeEncodeError:
            ascii_safe_chars.append("_")
            continue
        if ch in ('"', "\\", "\r", "\n"):
            ascii_safe_chars.append("_")
        else:
            ascii_safe_chars.append(ch)
    ascii_fallback = "".join(ascii_safe_chars)
    encoded = quote(filename, safe="")
    return f"attachment; filename=\"{ascii_fallback}\"; filename*=UTF-8''{encoded}"
