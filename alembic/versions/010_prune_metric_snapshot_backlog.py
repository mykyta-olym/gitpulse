"""prune_metric_snapshot_backlog

Retroactively completes the growth cap from release post33.

post33 made ``compute_team_metrics`` keep exactly ONE ``metric_snapshots`` row
per (team, student, calendar week) going forward (it deletes the rows it is
about to supersede within the same Monday-anchored week before inserting). It
deliberately did NOT prune the ~480k redundant rows already in production
(prod measured 506,076 rows across 574 students, ~882 each), because that is a
separate destructive step. Those historical duplicates are what make the
per-group "latest snapshot per student" aggregate slow (1.2s x 8 groups on a
course page) and cause the intermittent multi-second page loads.

This migration deletes the backlog with the SAME semantics the live path uses:
for each (team_id, student_id, week-bucket) it keeps the row with the newest
``computed_at`` and drops the rest. ``date_trunc('week', ...)`` in PostgreSQL is
Monday-anchored, matching post33's ``now - now.weekday()`` window, so the row
kept here is identical to the one the going-forward dedup would keep. The
"latest snapshot" every score chip / checklist aggregate reads is unchanged;
only redundant intra-week duplicates are removed.

One-way cleanup: downgrade cannot resurrect deleted duplicates (and the
going-forward code would immediately re-dedup them anyway), so it is a no-op.

Revision ID: 010
Revises: 009
Create Date: 2026-07-10 11:30:00.000000
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "010"
down_revision: str | None = "009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Keep the newest computed_at per (team, student, Monday-week); delete the
    # rest. row_number() over the same partition the live dedup uses.
    op.execute(
        """
        DELETE FROM metric_snapshots ms
        USING (
            SELECT id,
                   row_number() OVER (
                       PARTITION BY team_id, student_id,
                                    date_trunc('week', computed_at AT TIME ZONE 'UTC')
                       ORDER BY computed_at DESC, id DESC
                   ) AS rn
            FROM metric_snapshots
        ) dup
        WHERE ms.id = dup.id
          AND dup.rn > 1
        """
    )
    # Refresh planner statistics after a large delete so the "latest snapshot
    # per student" query immediately benefits from the smaller table.
    op.execute("ANALYZE metric_snapshots")


def downgrade() -> None:
    # Deleted duplicates cannot be restored, and the post33 dedup would remove
    # them again on the next recompute. Intentionally a no-op.
    pass
