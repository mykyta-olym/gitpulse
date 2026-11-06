"""diff_colors

Adds the per-user diff row colours behind Preferences > Diffs, modelled on
GitLab's "Color for removed lines" / "Color for added lines".

These are real settings here, not decoration: the student profile renders a
unified diff (``components/student.html``, ``.dn-code-row--add`` /
``--del``) with tinted rows and a +/- gutter, plus additions/deletions
counters on the profile header and the commit table.

Both columns are NULLable and that is the meaningful default: NULL means "use
the app's own green/red", which is exactly what every row did before this
migration, so an untouched account renders diffs identically.

Revision ID: 013
Revises: 012
Create Date: 2026-08-21 12:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "013"
down_revision: str | None = "012"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_COLUMNS = ("diff_color_removed", "diff_color_added")


def upgrade() -> None:
    for name in _COLUMNS:
        # String(7) holds exactly "#RRGGBB"; the endpoint refuses anything else.
        op.add_column("users", sa.Column(name, sa.String(7), nullable=True))


def downgrade() -> None:
    for name in reversed(_COLUMNS):
        op.drop_column("users", name)
