"""drop remember_period

The contract half of migration 021. The "Remember the period I pick" checkbox
became Preferences > Behavior > "Default period": 021 carried every account's
value into ``users.default_period`` and kept the old column only so the
containers of the previous release could still read it during that deploy. No
release since maps it.

The downgrade brings the column back with each account's value derived from
``default_period``, the way 021's own downgrade does.

Revision ID: 022
Revises: 021
Create Date: 2026-09-27 12:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "022"
down_revision: str | None = "021"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_column("users", "remember_period")


def downgrade() -> None:
    op.add_column(
        "users",
        sa.Column("remember_period", sa.Boolean(), nullable=False, server_default=sa.text("true")),
    )
    op.execute("UPDATE users SET remember_period = (default_period = 'remembered')")
