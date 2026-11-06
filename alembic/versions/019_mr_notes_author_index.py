"""mr_notes_author_index

The database catches up with the model.

``NoteMixin.author_id`` is declared ``index=True``, and base.py says so
explicitly: "The per-table index name for ``author_id`` is derived from the
table name, so it stays ``ix_<table>_author_id``". ``issue_notes`` has
``ix_issue_notes_author_id``. ``mr_notes`` does not - the two tables inherit the
same mixin and disagree about what it means.

Honest about the reason: this is drift repair, not a measured speed-up. The
query that made it worth looking - the student page's note counts - is scoped by
two joins down to about a hundred rows before the author condition is evaluated,
and measured on production at **1.24ms**. The seconds seen on that query earlier
were a deploy rebuilding container images on the same four cores, not a missing
index.

It is still worth having. A model that declares an index and a database that
lacks it is a difference that only shows up when the table is large enough for
the planner to change its mind, which is the worst moment to discover it.

Revision ID: 019
Revises: 018
Create Date: 2026-09-04 11:05:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "019"
down_revision: str | None = "018"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TABLE = "mr_notes"
_INDEX = "ix_mr_notes_author_id"
_COLUMN = "author_id"


def _has_index(bind: sa.engine.Connection, table: str, index: str) -> bool:
    return index in {i["name"] for i in sa.inspect(bind).get_indexes(table)}


def upgrade() -> None:
    bind = op.get_bind()
    if not _has_index(bind, _TABLE, _INDEX):
        op.create_index(_INDEX, _TABLE, [_COLUMN])


def downgrade() -> None:
    bind = op.get_bind()
    if _has_index(bind, _TABLE, _INDEX):
        op.drop_index(_INDEX, table_name=_TABLE)
