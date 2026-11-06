"""Unit coverage for the stored GitLab-intelligence snapshot helper.

``fetch_gitlab_intel_snapshot`` persists protected-branches / contributors /
repository-stats on ``GitLabProject.gitlab_intel`` during sync so the
project-detail panels keep rendering when GitLab is later unreachable. These
tests lock the stored SHAPE (must match what the route feeds into
``_build_gl_intel_view``) and the best-effort semantics (partial data kept;
total failure returns ``None`` so callers never wipe a good snapshot).
"""

import pytest

from app.workers.sync_common import fetch_gitlab_intel_snapshot


class _FakeGitLab:
    def __init__(
        self,
        *,
        protected=None,
        contribs=None,
        stats=None,
        members=None,
        direct=None,
        milestones=None,
        releases=None,
        labels=None,
        raise_on=(),
    ):
        self._protected = protected
        self._contribs = contribs
        self._stats = stats
        self._members = members
        self._direct = direct
        self._milestones = milestones
        self._releases = releases
        self._labels = labels
        self._raise_on = set(raise_on)

    async def get_protected_branches(self, project_id):
        if "protected" in self._raise_on:
            raise RuntimeError("boom")
        return self._protected

    async def get_contributors(self, project_id, *, ref=None):
        if "contribs" in self._raise_on:
            raise RuntimeError("boom")
        return self._contribs

    async def get_project_statistics(self, project_id):
        if "stats" in self._raise_on:
            raise RuntimeError("boom")
        return self._stats

    async def get_project_members(self, project_id, *, include_inherited=True):
        if "members" in self._raise_on:
            raise RuntimeError("boom")
        return self._members if include_inherited else self._direct

    async def get_project_milestones(self, project_id, *, state="all"):
        if "milestones" in self._raise_on:
            raise RuntimeError("boom")
        return self._milestones

    async def get_project_releases(self, project_id):
        if "releases" in self._raise_on:
            raise RuntimeError("boom")
        return self._releases

    async def get_project_labels(self, project_id):
        if "labels" in self._raise_on:
            raise RuntimeError("boom")
        return self._labels


@pytest.mark.asyncio
async def test_snapshot_shape_matches_view_contract() -> None:
    gl = _FakeGitLab(
        protected=[{"name": "main"}, {"name": "release"}],
        contribs=[{"name": "Ann", "commits": 12}],
        stats={
            "open_issues_count": 3,
            "star_count": 1,
            "forks_count": 0,
            "last_activity_at": "2026-07-01T10:00:00Z",
            "statistics": {"commit_count": 42, "repository_size": 1024, "storage_size": 2048},
        },
        members=[{"username": "Ann"}, {"username": "bob"}, {"username": "teach01"}],
        direct=[{"username": "Ann"}, {"username": "bob"}],
        milestones=[{"title": "Sprint 1", "state": "active"}],
        releases=[{"name": "v1.0"}],
        labels=[{"name": "bug"}],
    )
    snap = await fetch_gitlab_intel_snapshot(gl, 99, "main")
    assert snap is not None
    # Raw lists preserved for the route's own filtering + _build_gl_intel_view.
    assert snap["protectedBranches"] == [{"name": "main"}, {"name": "release"}]
    assert snap["contributors"] == [{"name": "Ann", "commits": 12}]
    # Statistics normalised into the shape _build_gl_intel_view reads.
    assert snap["statistics"]["commit_count"] == 42
    assert snap["statistics"]["repository_size"] == 1024
    assert snap["statistics"]["open_issues_count"] == 3
    assert snap["statistics"]["last_activity_at"] == "2026-07-01T10:00:00Z"
    # Member roster (lowercased) - lets the members table scope to this project.
    assert snap["members"] == ["ann", "bob", "teach01"]
    assert snap["direct_members"] == ["ann", "bob"]
    # Milestones, releases, and labels are stored
    assert snap["milestones"] == [{"title": "Sprint 1", "state": "active"}]
    assert snap["releases"] == [{"name": "v1.0"}]
    assert snap["labels"] == [{"name": "bug"}]
    assert "synced_at" in snap


@pytest.mark.asyncio
async def test_partial_failure_keeps_available_cards() -> None:
    gl = _FakeGitLab(
        protected=[{"name": "main"}],
        contribs=None,
        stats=None,
        raise_on=("contribs", "stats"),
    )
    snap = await fetch_gitlab_intel_snapshot(gl, 1, "main")
    assert snap is not None
    assert snap["protectedBranches"] == [{"name": "main"}]
    assert "contributors" not in snap
    assert "statistics" not in snap


@pytest.mark.asyncio
async def test_total_failure_returns_none_so_snapshot_not_wiped() -> None:
    gl = _FakeGitLab(raise_on=("protected", "contribs", "stats"))
    assert await fetch_gitlab_intel_snapshot(gl, 1, "main") is None


@pytest.mark.asyncio
async def test_empty_results_return_none() -> None:
    # GitLab reachable but returns nothing usable (e.g. empty repo) - still None,
    # so a prior good snapshot survives rather than being overwritten with {}.
    gl = _FakeGitLab(protected=None, contribs=None, stats=None)
    assert await fetch_gitlab_intel_snapshot(gl, 1, "main") is None
