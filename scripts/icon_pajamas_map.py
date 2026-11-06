"""GitPulse icon name -> GitLab Pajamas icon name.

Only the names that differ are listed; anything absent is identical in both sets.
Each choice is the closest Pajamas icon by MEANING, since Pajamas is a smaller,
product-specific set and has no 1:1 counterpart for a generic Feather glyph.
"""

MAP = {
    # status / feedback
    "alert-circle": "error",
    "alert-triangle": "warning",
    "x-circle": "status_failed",
    "info": "information-o",
    "help-circle": "question-o",
    "slash": "cancel",
    "wifi-off": "status_notfound",
    # navigation / chrome
    "menu": "hamburger",
    "more-horizontal": "ellipsis_h",
    "more-vertical": "ellipsis_v",
    "grid": "dashboard",
    "layers": "documents",
    "list": "list-bulleted",
    "align-left": "text-description",
    "type": "heading",
    "minus": "dash",
    "plus-circle": "plus",
    "log-in": "import",
    "log-out": "leave",
    "globe": "earth",
    "link-2": "link",
    "corner-down-right": "reply",
    "mouse-pointer": "marquee-selection",
    # Pajamas `x` is the X (Twitter) logo; the dismiss cross is `close`
    "x": "close",
    # editing
    "edit": "pencil",
    "edit-2": "pencil",
    "edit-3": "pencil-square",
    "trash": "remove",
    "trash-2": "remove",
    "save": "disk",
    "copy": "copy-to-clipboard",
    "clipboard": "copy-to-clipboard",
    "check-square": "task-done",
    "eye-off": "eye-slash",
    "unlock": "lock-open",
    "toggle-left": "feature-flag",
    "sliders": "preferences",
    "tool": "setup",
    # git
    "git-branch": "branch",
    "git-commit": "commit",
    "git-pull-request": "merge-request",
    "gitlab": "tanuki",
    # files
    "file": "document",
    "file-text": "doc-text",
    "file-diff": "doc-changes",
    "file-code": "doc-code",
    "box": "package",
    "book-open": "book",
    "graduation": "book",
    # data / charts
    "bar-chart": "chart",
    "bar-chart-2": "chart",
    "activity": "history",
    "trending-up": "trend-up",
    "trending-down": "trend-down",
    "target": "compass",
    "database": "disk",
    "server": "infrastructure",
    "cpu": "tanuki-ai",
    "bot": "agent-ai",
    "zap": "quick-actions",
    # people
    "user-check": "approval",
    "user-plus": "assignee",
    "user-minus": "unassignee",
    "thumbs-up": "thumb-up",
    "thumbs-down": "thumb-down",
    "award": "license",
    # comms
    "bell": "notifications",
    "message-circle": "comment",
    "message-square": "comment-dots",
    "inbox": "archive",
    "headphones": "service-desk",
    "life-buoy": "service-desk",
    # actions
    "play-circle": "play",
    "refresh": "retry",
    "refresh-cw": "retry",
    "rotate-ccw": "go-back",
    # `spinner` is a 10%-opacity sprite placeholder; a running pipeline is status_running
    "loader": "status_running",
}
