"""GitLab-style role hierarchy for the compliance engine.

GitLab access levels (numeric):
    10 - Guest
    20 - Reporter
    30 - Developer
    40 - Maintainer
    50 - Owner

This module provides constants, comparison helpers, and predicates used by
the compliance engine, templates, and the membership sync service.

Scoring rules
-------------
A team member is **scored** (included in the team aggregate) when they meet
ALL of the following conditions:

1. ``is_active is True``   - not soft-removed.
2. ``is_teacher is False`` - teachers are always excluded (they get
   their own snapshot but don't count toward the team average).
3. The member is a **contributing member**: either they hold a `developer`+
   role (access_level ≥ 30), OR they have actual activity (MRs, issues,
   commits).  Guests and reporters with zero activity are display-only.

This prevents inherited group-level members who never touched any project
from dragging down the team score.
"""

from __future__ import annotations

# -- GitLab numeric access levels --
ACCESS_GUEST: int = 10
ACCESS_REPORTER: int = 20
ACCESS_DEVELOPER: int = 30
ACCESS_MAINTAINER: int = 40
ACCESS_OWNER: int = 50

# Ordered list for iteration / display
ACCESS_LEVELS: list[tuple[int, str]] = [
    (ACCESS_GUEST, "guest"),
    (ACCESS_REPORTER, "reporter"),
    (ACCESS_DEVELOPER, "developer"),
    (ACCESS_MAINTAINER, "maintainer"),
    (ACCESS_OWNER, "owner"),
]

ACCESS_LEVEL_NAMES: dict[int, str] = dict(ACCESS_LEVELS)

# Minimum level to be considered a *contributing* member for scoring
# purposes.  Members below this level with zero project activity are
# excluded from the team aggregate (but still get an individual snapshot).
MIN_CONTRIBUTING_LEVEL: int = ACCESS_DEVELOPER  # 30


def access_role_name(level: int) -> str:
    """Map a numeric GitLab access level to a human-readable role name."""
    for threshold in sorted(ACCESS_LEVEL_NAMES.keys(), reverse=True):
        if level >= threshold:
            return ACCESS_LEVEL_NAMES[threshold]
    return "none"


def is_contributing_role(access_level: int | None) -> bool:
    """Return True if the access level is high enough to contribute.

    Developer (30), Maintainer (40), Owner (50) are contributing roles.
    Guest (10) and Reporter (20) are not - unless they have actual activity,
    which is checked separately.
    """
    if access_level is None:
        return True  # Unknown level -> assume contributing (safe default)
    return access_level >= MIN_CONTRIBUTING_LEVEL


_ROLE_PRIORITY = {
    "owner": 50,
    "maintainer": 40,
    "developer": 30,
    "reporter": 20,
    "guest": 10,
}


def role_priority(role_name: str | None) -> int:
    """Return a sort-priority for a role name (higher = more privileged)."""
    return _ROLE_PRIORITY.get((role_name or "").lower(), 0)
