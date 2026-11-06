"""Shared helpers for webhook entity processors."""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.mr_diff import MergeRequestDiff


async def replace_mr_diffs(
    session: AsyncSession, merge_request_id: uuid.UUID, changes: list[Any]
) -> None:
    """The MR's per-file diffs, replaced by GitLab's change entries (an entry
    with neither a new nor an old path is skipped)."""
    await session.execute(
        delete(MergeRequestDiff).where(MergeRequestDiff.merge_request_id == merge_request_id)
    )
    session.add_all(
        MergeRequestDiff(
            merge_request_id=merge_request_id,
            file_path=change.get("new_path") or change.get("old_path"),
            old_path=change.get("old_path"),
            diff=change.get("diff"),
            new_file=bool(change.get("new_file", False)),
            renamed_file=bool(change.get("renamed_file", False)),
            deleted_file=bool(change.get("deleted_file", False)),
        )
        for change in changes
        if isinstance(change, dict) and (change.get("new_path") or change.get("old_path"))
    )


def is_stale_update(
    existing_updated_at: datetime | None, incoming_updated_at: datetime | None
) -> bool:
    """True when an incoming webhook is older than the state we already stored.

    GitLab does NOT guarantee webhook ordering (and re-delivers on failure), so
    a stale ``update`` event can arrive *after* a terminal one (an MR ``merge``,
    an issue ``close``). GitLab's ``updated_at`` is monotonic per real change, so
    an incoming timestamp strictly older than the stored one means we already
    hold newer state; applying the stale payload would regress ``state`` (e.g.
    un-merge an MR or re-open a closed issue) and flip the author's R10/R11
    scoring until the next manual full sync.

    Conservative by design:
      * missing timestamps never block (new entities, legacy rows) -> False;
      * equal timestamps are allowed to re-apply (idempotent full syncs);
      * only a strictly-older timestamp is treated as stale.
    """
    if existing_updated_at is None or incoming_updated_at is None:
        return False
    return incoming_updated_at < existing_updated_at
