"""Presentation helpers exposed to Jinja templates.

Centralises the rendering of UTC timestamps so every template emits the
exact same ``<time data-localize-time>`` markup.  The companion client
script ``static/js/localize-time.js`` rewrites these elements into the
viewer's local timezone, so the single source of truth for *how* a time
is rendered lives here rather than being duplicated as ad-hoc
``strftime`` calls scattered across dozens of templates.
"""

from __future__ import annotations

from datetime import UTC, datetime

from markupsafe import Markup, escape

# Map a server ``strftime`` format to the client-side formatting mode read
# by ``localize-time.js`` via ``data-localize-format``.  ``None`` means the
# default ``YYYY-MM-DD HH:MM`` rendering (no attribute emitted).
_FORMAT_MODES: dict[str, str | None] = {
    "%Y-%m-%d %H:%M": None,
    "%H:%M": "time",
    "%b %d, %H:%M": "monthday-time",
    "relative": "relative",
}


def local_time(
    value: datetime | None,
    fmt: str = "%Y-%m-%d %H:%M",
    fallback: str = "-",
) -> Markup:
    """Render a UTC datetime as a client-localizable ``<time>`` element.

    The visible text is the server-side ``strftime`` output (so the page is
    readable before JS runs and for SSR scrapers); ``localize-time.js``
    converts it to the viewer's timezone in place.  Naive datetimes are
    assumed to be UTC; timezone-aware datetimes are normalised to UTC.

    Returns the escaped ``fallback`` text when ``value`` is falsy.
    """
    if not value:
        return Markup(escape(fallback))

    dt = value
    if dt.tzinfo is not None:
        dt = dt.astimezone(UTC)

    iso = dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    if fmt == "relative":
        now = datetime.now(UTC)
        diff = now - dt
        if diff.days >= 365:
            y = diff.days // 365
            display = "1 year ago" if y == 1 else f"{y} years ago"
        elif diff.days >= 30:
            m = diff.days // 30
            display = "1 month ago" if m == 1 else f"{m} months ago"
        elif diff.days >= 7:
            w = diff.days // 7
            display = "1 week ago" if w == 1 else f"{w} weeks ago"
        elif diff.days >= 1:
            display = "1 day ago" if diff.days == 1 else f"{diff.days} days ago"
        elif diff.seconds >= 3600:
            h = diff.seconds // 3600
            display = "1 hour ago" if h == 1 else f"{h} hours ago"
        elif diff.seconds >= 60:
            m = diff.seconds // 60
            display = "1 minute ago" if m == 1 else f"{m} minutes ago"
        else:
            display = "just now"
        mode = "relative"
    else:
        display = dt.strftime(fmt)
        mode = _FORMAT_MODES.get(fmt) or ""

    mode_attr = f' data-localize-format="{mode}"' if mode else ""
    time_attrs = f'datetime="{escape(iso)}" data-localize-time{mode_attr}'

    return Markup(f"<time {time_attrs}>{escape(display)}</time>")


def identicon(key: object) -> int:
    """GlAvatar's identicon colour for *key*: 1-7, ``gl-avatar-identicon-bg{n}``.

    GitLab takes ``entityId % 7 + 1``; our ids are UUIDs and usernames, so
    the number is the sum of the key's character codes instead. ``GP.identicon``
    in core/46-avatar-fallback.js computes the same sum, so a person or a group
    drawn by the server and by a script gets the same colour.
    """
    return sum(ord(ch) for ch in str(key or "")) % 7 + 1
