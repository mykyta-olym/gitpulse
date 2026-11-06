"""Shared constants used across multiple modules.

Centralises magic values that were previously scattered and duplicated
to ensure a single source of truth for theme colours, default weights,
thresholds, and other shared configuration.
"""

# -- Custom check defaults --
DEFAULT_CUSTOM_CHECK_WEIGHT: float = 0.05

# -- Auth sentinel values --
# Hash placeholder for users who authenticate via OAuth/SSO and have no
# local password.  Used in ``password_hash`` column.
NO_LOGIN_HASH = "!NOLOGIN"

# -- Default Git branch --
DEFAULT_BRANCH = "main"

# -- String truncation limits --
MAX_ERROR_MSG_LEN = 500
MAX_TITLE_LEN = 200
MAX_TRACEBACK_HEAD = 200
MAX_TRACEBACK_TAIL = 295

# -- Pagination defaults --
# Central source of truth for page sizes across all dashboard views.
# Note: default of 10 is too low for teachers with 20-50 students.
PAGE_SIZE_DEFAULT = 50  # default rows per page (was 10)
PAGE_SIZE_SEARCH = 8  # autocomplete / search dropdown results
PAGE_SIZE_DETAIL_ITEMS = 25  # issues, MRs, notes per detail page
PAGE_SIZE_COMMITS = 50  # commits list on student detail
PAGE_SIZE_REPORTS = 10  # LLM analyses and other paginated reports
PAGE_SIZE_FEED = 20  # activity feed items (recent MRs, etc.)
PAGE_SIZE_STATS_MAX = 10_000  # ceiling for batch stats computation

# -- Default course settings applied when a course is created --
# The CourseSettings columns default to an EMPTY list, so these literals are the
# real defaults. They were copy-pasted into every course-creation path (the API,
# the full-config import, and the GitLab group import), so changing a pattern
# meant editing three places and silently drifting if one was missed.
# Tuples, so the shared default can never be mutated in place through one
# course's settings; call sites wrap them in ``list(...)``.
DEFAULT_MR_TEMPLATE_SECTIONS: tuple[str, ...] = ("## Description", "## Testing")
DEFAULT_TEST_FILE_PATTERNS: tuple[str, ...] = (
    "**/test_*.py",
    "**/*_test.py",
    "**/*_test.go",
    "**/Test*.java",
    "**/*.test.js",
    "**/*.test.ts",
    "**/*.spec.js",
    "**/*.spec.ts",
)

# -- CSP allowlist domains --
CSP_STYLE_ORIGINS = ("https://fonts.googleapis.com",)
CSP_FONT_ORIGINS = ("https://fonts.gstatic.com",)
# Gravatar on both of its hosts: GitLab hands out `secure.gravatar.com` when it
# is served over HTTPS and `www.gravatar.com` otherwise.
CSP_IMAGE_ORIGINS = (
    "https://fastapi.tiangolo.com",
    "https://secure.gravatar.com",
    "https://www.gravatar.com",
)
