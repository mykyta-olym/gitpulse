"""assistant_language_and_token_state

Two facts the classroom assistant's course row did not keep:

* ``comment_language`` - the language the bot writes its comments, issues and
  the colleague's line in. The app teaches in Slovak, but a course taught in
  English needs its bot to speak English. Every existing row takes ``sk``,
  which is what the bot has written so far.
* ``token_rejected_at`` - when GitLab last answered the bot's token with 401
  (revoked, expired early, deleted bot). Until a teacher connects a new token
  the assistant stops instead of failing every event, and the page says why.
  NULL for every existing row: no rejection is known.

Revision ID: 024
Revises: 023
Create Date: 2026-10-19 18:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "024"
down_revision: str | None = "023"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "course_assistants",
        sa.Column("comment_language", sa.String(5), nullable=False, server_default="sk"),
    )
    op.add_column(
        "course_assistants",
        sa.Column("token_rejected_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("course_assistants", "token_rejected_at")
    op.drop_column("course_assistants", "comment_language")
