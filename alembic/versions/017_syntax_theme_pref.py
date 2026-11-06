"""syntax_theme_pref

Adds the Syntax highlighting preference - GitLab's "Choose a highlight color
scheme for viewing and editing code."

It is a real setting here rather than a copied label: fenced code blocks with a
recognised language tag are highlighted by Pygments in ``app/i18n`` and rendered
as ``<pre class="gl-desc-pre highlight">``, whose token colours are now ten CSS
variables. A scheme redefines those ten, keyed on the root attribute base.html
renders from this column, so the choice applies before first paint.

Carries a server default, so every existing row keeps exactly today's palette.

Revision ID: 017
Revises: 016
Create Date: 2026-08-31 10:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "017"
down_revision: str | None = "016"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_COLUMNS: tuple[tuple[str, sa.types.TypeEngine[object], str], ...] = (
    ("syntax_theme", sa.String(20), "'default'"),
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
