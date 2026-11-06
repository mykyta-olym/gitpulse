"""default_period

Preferences > Behavior > "Default period" - which academic period a page with a
period selector opens on, like "Homepage" picks the page:

- ``remembered``: the period last picked on any page, kept on every page until
  the next term starts (what the "Remember the period I pick" checkbox of
  migration 020 did when on - the default);
- ``newest``: the newest term that holds the reader's courses (the checkbox off);
- ``current``: the term the TUKE calendar is in;
- ``all``: every period.

Expand, then contract: this adds ``default_period`` and carries every account's
checkbox over (off -> ``newest``); ``remember_period`` stays in the table until
a later migration drops it, so the containers still running the previous
release during a deploy keep reading a column that exists.

Revision ID: 021
Revises: 020
Create Date: 2026-09-26 18:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "021"
down_revision: str | None = "020"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_COLUMNS: tuple[tuple[str, sa.types.TypeEngine[object], str], ...] = (
    ("default_period", sa.String(12), "'remembered'"),
)


def upgrade() -> None:
    for name, type_, server_default in _COLUMNS:
        # NOT NULL is safe only because it carries a default for the existing
        # rows to take - the rule migration 012 got wrong.
        op.add_column(
            "users",
            sa.Column(name, type_, nullable=False, server_default=sa.text(server_default)),
        )
    op.execute("UPDATE users SET default_period = 'newest' WHERE remember_period IS FALSE")


def downgrade() -> None:
    op.execute("UPDATE users SET remember_period = (default_period = 'remembered')")
    for name, _type, _default in reversed(_COLUMNS):
        op.drop_column("users", name)
