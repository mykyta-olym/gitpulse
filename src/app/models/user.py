"""User model for RBAC."""

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin


class User(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "users"

    username: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    full_name: Mapped[str | None] = mapped_column(String(200))
    email: Mapped[str | None] = mapped_column(String(200))
    password_hash: Mapped[str] = mapped_column(String(200), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="student")
    role_locked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    # ``is_bot``: True for GitLab service accounts (``project_*_bot_*``,
    # ``group_*_bot``, ``*-bot``, etc.). Set at creation time via
    # ``app.services.gitlab_import.is_bot_user``. Default ``False``
    # so existing OAuth flows that omit the kwarg keep producing humans.
    # Bots are excluded from default listings and statistics - see
    # ``app.services.user_filters`` for the canonical SQL predicate.
    is_bot: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # GitLab username for linking to OAuth sessions
    gitlab_username: Mapped[str | None] = mapped_column(String(100), unique=True)

    # GitLab numeric user ID (from GitLab API)
    gitlab_user_id: Mapped[int | None] = mapped_column(BigInteger, unique=True)

    # GitLab avatar URL (synced from GitLab API on OAuth login)
    avatar_url: Mapped[str | None] = mapped_column(String(500))

    # GitLab OAuth token storage (Fernet-encrypted via app.security.token_encryption)
    gitlab_access_token: Mapped[str | None] = mapped_column(String(500))
    gitlab_refresh_token: Mapped[str | None] = mapped_column(String(500))
    gitlab_token_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Tour seen keys - JSON array of gp_tour_v2 localStorage keys.
    # Persisted server-side so completions/dismissals carry over to new devices.
    tour_seen: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Account-level appearance preference. The resolved light/dark mode remains
    # client-dependent when this is "system", but the preference follows the
    # user across browsers and devices.
    theme_preference: Mapped[str] = mapped_column(
        String(10), nullable=False, default="system", server_default="system"
    )

    # -- Preferences (GitLab's /-/profile/preferences) ----------------------
    # Every one of these is account-level for the same reason theme_preference
    # is: a preference kept only in a cookie is silently lost on a new device,
    # and the reader reads that as the setting "not saving".

    # Accent colour of the interface chrome. GitLab calls this the theme.
    accent_theme: Mapped[str] = mapped_column(
        String(16), nullable=False, default="default", server_default="default"
    )
    # "fixed" caps the content column; "fluid" spans the viewport.
    layout_width: Mapped[str] = mapped_column(
        String(8), nullable=False, default="fixed", server_default="fixed"
    )
    # Gates the "/" search palette and the other global key handlers.
    keyboard_shortcuts_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )
    # Where "/dashboard/" lands this user.
    default_homepage: Mapped[str] = mapped_column(
        String(20), nullable=False, default="dashboard", server_default="dashboard"
    )
    # NULL means "follow the browser/cookie", which is what the app did before
    # this column existed - so existing rows keep their current behaviour.
    preferred_language: Mapped[str | None] = mapped_column(String(5), nullable=True)
    # "system" defers to the locale (Monday for sk/en-GB, Sunday for en-US).
    first_day_of_week: Mapped[str] = mapped_column(
        String(10), nullable=False, default="system", server_default="system"
    )
    # "3 days ago" vs an absolute timestamp.
    use_relative_times: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )
    # "system" | "12h" | "24h".
    time_format: Mapped[str] = mapped_column(
        String(8), nullable=False, default="system", server_default="system"
    )

    # Which Pygments palette a highlighted code block uses. Real, not
    # decorative: app/i18n highlights fenced blocks with Pygments and the token
    # colours are CSS variables a scheme redefines.
    #
    # The column default is still "default", a scheme the page no longer offers
    # (the set is GitLab's seven now). It needs no migration: both read paths -
    # `current_preferences` for the page and `_choice_allowlists` for the
    # session - degrade a value that is not offered to the field's default,
    # "dark", which is the palette "default" was a near-copy of.
    syntax_theme: Mapped[str] = mapped_column(
        String(20), nullable=False, default="default", server_default="default"
    )

    # Diff row colours, as "#RRGGBB". NULL means "use the app's own green/red",
    # which is what every row did before these columns existed - so an untouched
    # account renders diffs exactly as it always has.
    diff_color_removed: Mapped[str | None] = mapped_column(String(7), nullable=True)
    diff_color_added: Mapped[str | None] = mapped_column(String(7), nullable=True)

    # -- Notification opt-outs ---------------------------------------------
    # One flag per category enqueue_email() is called with. Enforced SERVER
    # side in enqueue_email, not merely hidden in the UI: a preference that
    # only the form respects is not a preference, it is a suggestion.
    # `welcome` has no flag on purpose - it is the one-off mail that explains
    # the account, and it is sent before the reader has ever seen this page.
    notify_tickets: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )
    # Staff-facing: "a new ticket has arrived and nobody owns it". Separate from
    # notify_tickets so muting your own ticket updates does not also silence an
    # operational duty. Students never receive this mail, so the flag is simply
    # inert for them.
    notify_ticket_queue: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )
    notify_courses: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )
    notify_account: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )

    # -- GitPulse's own, not GitLab's --------------------------------------
    # Both are choices the app ALREADY offers and then forgets: the per-table
    # "Per page" control writes localStorage `gp_ps_<table>`, and the sidebar
    # writes `sidebar-collapsed`. Kept only client-side they are lost on every
    # new device, which is the same complaint theme_preference was moved here
    # to fix. These are the account-level DEFAULT; a per-table choice still
    # wins for that table.
    default_page_size: Mapped[str] = mapped_column(
        String(4), nullable=False, default="50", server_default="50"
    )
    sidebar_collapsed: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    # Which academic period a page with a period selector opens on
    # (migration 021; preferences.py lists the values).
    default_period: Mapped[str] = mapped_column(
        String(12), nullable=False, default="remembered", server_default="remembered"
    )
