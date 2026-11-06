"""remember_period

Preferences > Behavior > "Remember the academic period I pick".

The period selector remembers the reader's pick across pages until the next
term starts (a localStorage value with a cookie mirror). That is what most
readers want, and it is also how a reader who once looked at next winter kept
opening the Dashboard on an empty term. Turned off, each page opens on its own
default - the newest term that holds the reader's courses - and the pick is
not stored.

The server default keeps today's behaviour for every existing account.

Revision ID: 020
Revises: 019
Create Date: 2026-09-26 15:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "020"
down_revision: str | None = "019"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


_COLUMNS: tuple[tuple[str, sa.types.TypeEngine[object], str], ...] = (
    ("remember_period", sa.Boolean(), "true"),
)


def upgrade() -> None:
    for name, type_, server_default in _COLUMNS:
        # NOT NULL is safe only because it carries a default for the existing
        # rows to take - the rule migration 012 got wrong.
        op.add_column(
            "users",
            sa.Column(name, type_, nullable=False, server_default=sa.text(server_default)),
        )


def downgrade() -> None:
    for name, _type, _default in reversed(_COLUMNS):
        op.drop_column("users", name)
