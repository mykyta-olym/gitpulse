"""patterns_into_check_configs

Moves the three convention patterns into the per-check configuration.

``branch_pattern``, ``test_file_patterns`` and ``mr_template_required_sections``
were top-level ``course_settings`` columns edited in their own "Patterns" card,
away from the checks that actually read them. Teachers could not tell which
pattern fed which rule, and two of the three did nothing at all unless the
matching check was separately switched to strict mode. They now live in
``course_settings.check_configs`` beside the rest of each check's options:

    branch_pattern                 -> check_configs['R02']['branch_pattern']
    test_file_patterns             -> check_configs['R03']['test_file_patterns']
    mr_template_required_sections  -> check_configs['R05']['required_sections']

This migration only COPIES the values across; it does not drop the columns.
``app.compliance.patterns.resolve_patterns`` prefers ``check_configs`` and falls
back to the columns, so a row restored from an older dump keeps scoring exactly
as it did. Dropping the columns is a separate, destructive step for a later
release once prod has run on the new source for a while.

Existing keys in ``check_configs`` are never overwritten - a course that
somehow already carries a pattern there has the more specific value.

Revision ID: 011
Revises: 010
Create Date: 2026-07-21 12:00:00.000000
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "011"
down_revision: str | None = "010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Merge rather than jsonb_set. `jsonb_set(cfg, '{R02,branch_pattern}', ...)`
    # only creates the LAST path element: when the 'R02' object itself is
    # missing it returns the input UNCHANGED, which is precisely the state
    # every course needing this backfill is in. The `||` form rebuilds the
    # per-check object from whatever is already there (or '{}') and merges it
    # back, so it works whether or not 'R02' exists.
    #
    # The guard's inner COALESCE matters for the same reason: `check_configs ->
    # 'R02'` is NULL when absent, `NULL ? 'key'` is NULL, and `NOT NULL` is
    # NULL - so the row would fail WHERE and be skipped.
    #
    # Empty columns are skipped so we do not write a meaningless "" / []
    # override that would mask a future default change.
    op.execute(
        """
        UPDATE course_settings
        SET check_configs = COALESCE(check_configs, '{}'::jsonb)
            || jsonb_build_object(
                'R02',
                COALESCE(check_configs -> 'R02', '{}'::jsonb)
                    || jsonb_build_object('branch_pattern', to_jsonb(branch_pattern))
            )
        WHERE branch_pattern IS NOT NULL
          AND branch_pattern <> ''
          AND NOT (COALESCE(check_configs -> 'R02', '{}'::jsonb) ? 'branch_pattern')
        """
    )
    op.execute(
        """
        UPDATE course_settings
        SET check_configs = COALESCE(check_configs, '{}'::jsonb)
            || jsonb_build_object(
                'R03',
                COALESCE(check_configs -> 'R03', '{}'::jsonb)
                    || jsonb_build_object('test_file_patterns', to_jsonb(test_file_patterns))
            )
        WHERE test_file_patterns IS NOT NULL
          AND jsonb_array_length(to_jsonb(test_file_patterns)) > 0
          AND NOT (COALESCE(check_configs -> 'R03', '{}'::jsonb) ? 'test_file_patterns')
        """
    )
    op.execute(
        """
        UPDATE course_settings
        SET check_configs = COALESCE(check_configs, '{}'::jsonb)
            || jsonb_build_object(
                'R05',
                COALESCE(check_configs -> 'R05', '{}'::jsonb)
                    || jsonb_build_object(
                        'required_sections', to_jsonb(mr_template_required_sections)
                    )
            )
        WHERE mr_template_required_sections IS NOT NULL
          AND jsonb_array_length(to_jsonb(mr_template_required_sections)) > 0
          AND NOT (COALESCE(check_configs -> 'R05', '{}'::jsonb) ? 'required_sections')
        """
    )


def downgrade() -> None:
    # Copy the values back so the legacy columns are authoritative again, then
    # remove the relocated keys. The columns were never cleared on upgrade, so
    # this only matters for courses edited after the move.
    op.execute(
        """
        UPDATE course_settings
        SET branch_pattern = check_configs #>> '{R02,branch_pattern}'
        WHERE check_configs #>> '{R02,branch_pattern}' IS NOT NULL
        """
    )
    op.execute(
        """
        UPDATE course_settings
        SET test_file_patterns = ARRAY(
            SELECT jsonb_array_elements_text(check_configs #> '{R03,test_file_patterns}')
        )
        WHERE jsonb_typeof(check_configs #> '{R03,test_file_patterns}') = 'array'
        """
    )
    op.execute(
        """
        UPDATE course_settings
        SET mr_template_required_sections = ARRAY(
            SELECT jsonb_array_elements_text(check_configs #> '{R05,required_sections}')
        )
        WHERE jsonb_typeof(check_configs #> '{R05,required_sections}') = 'array'
        """
    )
    op.execute(
        """
        UPDATE course_settings
        SET check_configs = (check_configs
            #- '{R02,branch_pattern}'
            #- '{R03,test_file_patterns}'
            #- '{R05,required_sections}')
        WHERE check_configs IS NOT NULL
        """
    )
