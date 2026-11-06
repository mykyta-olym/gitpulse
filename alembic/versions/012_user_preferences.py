"""user_preferences

Adds the account-level preferences behind the Preferences page, modelled on
GitLab's ``/-/profile/preferences``.

``theme_preference`` (the light/dark/system mode) already lived on ``users``;
these join it for the same reason it is there rather than in a cookie - a
preference kept only client-side is silently lost on a new device, and the
reader reads that as the setting not saving.

Every column is NOT NULL with a server default, so existing rows adopt exactly
the behaviour the app had before this migration:

    accent_theme               'default'   the current neutral chrome
    layout_width               'fixed'     the current capped content column
    keyboard_shortcuts_enabled true        the "/" palette already worked
    default_homepage           'dashboard' where /dashboard/ already landed
    first_day_of_week          'system'    already derived from the locale
    use_relative_times         true        local_time() already did this
    time_format                'system'    already followed the locale

``preferred_language`` is the one NULLable column: NULL means "follow the
locale cookie / Accept-Language", which is what every existing session does.
Defaulting it to 'sk' instead would silently pin every English reader back to
Slovak on their next request.

Revision ID: 012
Revises: 011
Create Date: 2026-08-21 12:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "012"
down_revision: str | None = "011"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


_COLUMNS: tuple[tuple[str, sa.types.TypeEngine[object], str | None], ...] = (
    ("accent_theme", sa.String(16), "'default'"),
    ("layout_width", sa.String(8), "'fixed'"),
    ("keyboard_shortcuts_enabled", sa.Boolean(), "true"),
    ("default_homepage", sa.String(20), "'dashboard'"),
    ("preferred_language", sa.String(5), None),
    ("first_day_of_week", sa.String(10), "'system'"),
    ("use_relative_times", sa.Boolean(), "true"),
    ("time_format", sa.String(8), "'system'"),
)


def upgrade() -> None:
    for name, type_, server_default in _COLUMNS:
        op.add_column(
            "users",
            sa.Column(
                name,
                type_,
                # A column WITH a server default can be NOT NULL - existing rows
                # get the default. One WITHOUT a default must be NULLable, or the
                # ALTER fails on any table that already has rows. This condition
                # was inverted, which is exactly how it failed in production:
                #   NotNullViolationError: column "preferred_language" of relation
                #   "users" contains null values
                nullable=server_default is None,
                server_default=sa.text(server_default) if server_default else None,
            ),
        )


def downgrade() -> None:
    for name, _type, _default in reversed(_COLUMNS):
        op.drop_column("users", name)
