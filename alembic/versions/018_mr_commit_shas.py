"""mr_commit_shas

An MR's commit list, as GitLab reports it.

A merge request showed 30 commits where GitLab showed 7, and 23 of those were
the template repository's history - "Teacher commit" entries from four to six
years before the assignment existed. The page had no way to know better: it
listed every commit stored with ``ref = <source branch>``, which is the whole
branch history, and capped the result at 30 (which is where the 30 came from -
it was not even a count).

There is no way to derive GitLab's answer from what was stored. ``git_commits``
keeps ONE ref per commit, and the sync deliberately skips the default branch, so
"commits on the source branch that are not on the target branch" cannot be asked.

The sync already fetches the right answer, though: it calls
``/projects/:id/merge_requests/:iid/commits`` per MR and uses the result only to
backfill commits the branch sync missed. This column keeps that list, so the
page can show exactly the commits GitLab shows.

Nullable on purpose: NULL means "never synced since this column existed", and
the page falls back to the old branch listing for those rows rather than
claiming a merge request has no commits.

Revision ID: 018
Revises: 017
Create Date: 2026-09-04 10:20:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "018"
down_revision: str | None = "017"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TABLE = "merge_requests"
_COLUMN = "commit_shas"


def _has_column(bind: sa.engine.Connection, table: str, column: str) -> bool:
    return column in {c["name"] for c in sa.inspect(bind).get_columns(table)}


def upgrade() -> None:
    bind = op.get_bind()
    if _has_column(bind, _TABLE, _COLUMN):
        return
    op.add_column(
        _TABLE,
        sa.Column(
            _COLUMN,
            sa.ARRAY(sa.String()),
            nullable=True,
            comment=(
                "SHAs GitLab reports for this merge request "
                "(/merge_requests/:iid/commits). NULL = not synced since this "
                "column existed; the page then falls back to the branch listing."
            ),
        ),
    )


def downgrade() -> None:
    bind = op.get_bind()
    if _has_column(bind, _TABLE, _COLUMN):
        op.drop_column(_TABLE, _COLUMN)
