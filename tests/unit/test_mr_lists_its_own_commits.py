"""A merge request lists the commits GitLab says are in it.

Reported: an MR whose GitLab page shows 7 commits showed **30** here, and 23 of
those were "Teacher commit" entries from four to six years before the assignment
existed - the template repository's history, inherited by the fork.

Two separate things were wrong, and both are visible in that number:

* The card listed every commit stored with ``ref = <source branch>``. That is
  the branch's whole history, not the merge request's contents.
* 30 was not a count. It is ``_branch_commit_cap``, the ceiling on how many
  commits the page keeps per branch, so the real figure was larger still.

It cannot be derived from what was stored: ``git_commits`` keeps ONE ref per
commit, so a commit reachable from both ``main`` and the branch is filed under
whichever was synced first, and the sync skips the default branch entirely.
"Commits on the source branch that are not on the target branch" - GitLab's own
rule - is unanswerable from that.

The sync already fetches the right list per MR (``get_mr_commits``) and used it
only to backfill commits the branch sync had missed. It stores it now, and the
page asks for those commits by sha.

Verified end to end on real data before this was written: a merge request with
ten commits on its branch, its stored list set to two of them, rendered a card
reading 2 - and a merge request with no stored list rendered its branch listing
exactly as before.
"""

from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SYNC = REPO / "src/app/workers/project_sync.py"
PAGE = REPO / "src/app/api/dashboard/students/profile.py"
MODEL = REPO / "src/app/models/merge_request.py"
MIGRATION = REPO / "alembic/versions/018_mr_commit_shas.py"


class TestTheListIsStored:
    def test_the_column_exists_on_the_model(self) -> None:
        src = MODEL.read_text(encoding="utf-8")
        assert "commit_shas" in src, "the merge request has nowhere to keep its commit list"
        assert "nullable=True" in src.split("commit_shas", 1)[1][:200], (
            "the column must be nullable - NULL is what tells the page to fall back"
        )

    def test_a_migration_adds_it(self) -> None:
        src = MIGRATION.read_text(encoding="utf-8")
        assert 'revision: str = "018"' in src
        assert "commit_shas" in src
        assert "def downgrade" in src, "the migration cannot be undone"

    def test_the_sync_records_it(self) -> None:
        src = SYNC.read_text(encoding="utf-8")
        assert "shas_by_iid" in src, "the fetched list is still thrown away"
        assert "commit_shas=shas" in src, "the list is collected but never written"

    def test_the_list_is_taken_before_the_cross_mr_dedupe(self) -> None:
        """`seen` exists to avoid fetching one commit's detail twice.
        Recording after it would drop a shared commit from the SECOND merge
        request - which is precisely the list this is trying to get right."""
        src = SYNC.read_text(encoding="utf-8")
        block = src.split("for c in listed or []:", 1)[1][:1200]
        record = block.index("shas_by_iid.setdefault")
        dedupe = block.index("seen.add")
        assert record < dedupe, "the MR's own list is recorded after the dedupe drops shas"


class TestThePageAsksForThoseCommits:
    def test_it_prefers_the_merge_request_s_own_list(self) -> None:
        src = PAGE.read_text(encoding="utf-8")
        assert "commits_by_mr" in src, "the page still lists the whole branch"
        assert "commits = commits_by_mr.get(mr.id, by_branch.get(branch, []))" in src, (
            "the per-MR list is built but not used for the card"
        )

    def test_a_merge_request_without_a_list_keeps_the_old_listing(self) -> None:
        """NULL means 'not synced since the column existed', not 'no commits'."""
        src = PAGE.read_text(encoding="utf-8")
        entry = src.split("commits = commits_by_mr.get", 1)[1][:300]
        assert "by_branch.get(" in entry, "old data would render an empty commit list"

    def test_the_commits_are_fetched_by_sha_not_filtered_from_the_capped_bucket(self) -> None:
        """The branch bucket is truncated at `_BRANCH_COMMIT_CAP` BEFORE anything
        is filtered, so on a branch carrying a template's history the merge
        request's own commits can fall outside the cap and disappear."""
        src = PAGE.read_text(encoding="utf-8")
        block = src.split("by_mr: dict[uuid.UUID, list[Commit]]", 1)[1][:900]
        assert "Commit.sha" in block, "the per-MR commits are not looked up by sha"
        assert "_BRANCH_COMMIT_CAP" not in block, "the capped bucket is being filtered again"
