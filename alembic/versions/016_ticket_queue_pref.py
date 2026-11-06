"""ticket_queue_pref

Splits staff-facing ticket-queue mail out of the personal ticket toggle.

``notify_ticket_new_to_staff`` shared ``notify_tickets`` with the mail a reader
gets about their OWN tickets, so an admin who muted ticket updates also stopped
being told that a new ticket had arrived with nobody on it - silencing an
operational duty along with a personal preference.

Defaults to true with a server default, so nobody's mail changes.

Revision ID: 016
Revises: 015
Create Date: 2026-08-25 12:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "016"
down_revision: str | None = "015"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_COLUMNS = ("notify_ticket_queue",)


def upgrade() -> None:
    for name in _COLUMNS:
        op.add_column(
            "users",
            sa.Column(name, sa.Boolean(), nullable=False, server_default=sa.text("true")),
        )


def downgrade() -> None:
    for name in reversed(_COLUMNS):
        op.drop_column("users", name)
