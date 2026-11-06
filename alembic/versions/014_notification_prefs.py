"""notification_prefs

Adds the per-category notification opt-outs behind Preferences > Notifications.

One flag per category ``enqueue_email()`` is called with (``ticket``,
``course``, ``user``). ``welcome`` deliberately has none: it is the one-off
mail that explains the account, sent before the reader has ever seen the
preferences page.

All three default to true with a server default, so every existing account
keeps receiving exactly what it received before this migration.

Revision ID: 014
Revises: 013
Create Date: 2026-08-25 12:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "014"
down_revision: str | None = "013"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_COLUMNS = ("notify_tickets", "notify_courses", "notify_account")


def upgrade() -> None:
    for name in _COLUMNS:
        # NOT NULL is safe here because each column carries a server default
        # for the existing rows to take - the rule migration 012 got wrong.
        op.add_column(
            "users",
            sa.Column(name, sa.Boolean(), nullable=False, server_default=sa.text("true")),
        )


def downgrade() -> None:
    for name in reversed(_COLUMNS):
        op.drop_column("users", name)
