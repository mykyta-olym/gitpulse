"""workspace_prefs

Adds GitPulse's own two preferences - the ones that are not copied from GitLab.

Both are choices the app already offers and then forgets, because they live in
localStorage: the per-table "Per page" control writes ``gp_ps_<table>`` and the
sidebar writes ``sidebar-collapsed``. Client-side only, they are lost on every
new device - the same complaint that moved ``theme_preference`` onto the
account in the first place.

``default_page_size`` is a String rather than an Integer because "all" is one
of its values, and it must round-trip through the same field table as every
other choice.

Both carry a server default, so existing rows keep exactly today's behaviour:
50 rows a page and an expanded sidebar.

Revision ID: 015
Revises: 014
Create Date: 2026-08-25 12:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "015"
down_revision: str | None = "014"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_COLUMNS: tuple[tuple[str, sa.types.TypeEngine[object], str], ...] = (
    ("default_page_size", sa.String(4), "'50'"),
    ("sidebar_collapsed", sa.Boolean(), "false"),
)


def upgrade() -> None:
    for name, type_, server_default in _COLUMNS:
        # NOT NULL is safe only because each carries a default for the existing
        # rows to take - the rule migration 012 got wrong.
        op.add_column(
            "users",
            sa.Column(name, type_, nullable=False, server_default=sa.text(server_default)),
        )


def downgrade() -> None:
    for name, _type, _default in reversed(_COLUMNS):
        op.drop_column("users", name)
