"""Unit tests for deactivate_orphaned_team_members (sync_common).

When a GitLab project is deleted (confirmed 404), the sync deactivates it.
If that was the team's *last* active project, its roster is stale and must
be deactivated too. These tests pin the safety rules with a mocked session:

* team still has an active project  -> no-op (roster preserved)
* team has zero active projects     -> members deactivated + audited
* CSV-placeholder members (negative gitlab_user_id) are never touched
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.workers.sync_common import (
    deactivate_orphaned_team_members,
    deactivate_project_and_reconcile,
    gitlab_repo_is_empty,
    project_has_stored_commits,
)


@dataclass
class StubProject:
    is_active: bool = True


@dataclass
class StubStudent:
    gitlab_user_id: int | None = 100
    gitlab_username: str | None = "alice"


@dataclass
class StubMember:
    student_id: uuid.UUID = field(default_factory=uuid.uuid4)
    student: StubStudent | None = field(default_factory=StubStudent)
    is_active: bool = True
    left_at: datetime | None = None
    last_synced_at: datetime | None = None
    gitlab_access_role: str | None = "developer"
    gitlab_access_level: int | None = 30


def _make_session(*, active_projects: int, members: list[StubMember]) -> MagicMock:
    session = MagicMock()
    session.scalar = AsyncMock(return_value=active_projects)
    session.execute = AsyncMock(
        return_value=MagicMock(
            scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=members)))
        )
    )
    session.add = MagicMock()
    session.commit = AsyncMock()
    return session


@pytest.mark.asyncio
async def test_noop_when_team_still_has_active_project() -> None:
    members = [StubMember()]
    session = _make_session(active_projects=1, members=members)

    count = await deactivate_orphaned_team_members(session, uuid.uuid4())

    assert count == 0
    # Roster left untouched, nothing committed.
    assert members[0].is_active is True
    session.commit.assert_not_awaited()
    session.add.assert_not_called()


@pytest.mark.asyncio
async def test_deactivates_members_when_no_active_projects() -> None:
    members = [StubMember(), StubMember(student=StubStudent(gitlab_user_id=101))]
    session = _make_session(active_projects=0, members=members)

    with patch(
        "app.workers.progress.publish_dashboard_update",
        new=MagicMock(),
    ) as pub:
        count = await deactivate_orphaned_team_members(session, uuid.uuid4())

    assert count == 2
    assert all(m.is_active is False for m in members)
    assert all(m.left_at is not None for m in members)
    # One audit row added per deactivated member, then a single commit.
    assert session.add.call_count == 2
    session.commit.assert_awaited_once()
    pub.assert_called_once()


@pytest.mark.asyncio
async def test_skips_csv_placeholder_members() -> None:
    # Negative gitlab_user_id == manually-imported placeholder; never touch it.
    placeholder = StubMember(student=StubStudent(gitlab_user_id=-5))
    real = StubMember(student=StubStudent(gitlab_user_id=200))
    session = _make_session(active_projects=0, members=[placeholder, real])

    with patch("app.workers.progress.publish_dashboard_update", new=MagicMock()):
        count = await deactivate_orphaned_team_members(session, uuid.uuid4())

    assert count == 1
    assert placeholder.is_active is True  # untouched
    assert real.is_active is False
    assert session.add.call_count == 1


@pytest.mark.asyncio
async def test_no_commit_when_only_placeholders() -> None:
    placeholder = StubMember(student=StubStudent(gitlab_user_id=-1))
    session = _make_session(active_projects=0, members=[placeholder])

    count = await deactivate_orphaned_team_members(session, uuid.uuid4())

    assert count == 0
    assert placeholder.is_active is True
    session.commit.assert_not_awaited()


# -- gitlab_repo_is_empty (pure) --


@pytest.mark.parametrize(
    ("info", "expected"),
    [
        ({"empty_repo": True}, True),
        ({"empty_repo": False, "default_branch": "main"}, False),
        ({"default_branch": None}, True),  # no empty_repo key -> fall back
        ({"default_branch": "main"}, False),
        ({}, True),  # nothing means no branch -> empty
        (None, False),  # non-dict -> not "empty" (unknown)
        ("nope", False),
    ],
)
def test_gitlab_repo_is_empty(info: object, expected: bool) -> None:
    assert gitlab_repo_is_empty(info) is expected


# -- project_has_stored_commits --


@pytest.mark.asyncio
async def test_project_has_stored_commits_true() -> None:
    session = MagicMock()
    session.scalar = AsyncMock(return_value="abc123")
    assert await project_has_stored_commits(session, uuid.uuid4()) is True


@pytest.mark.asyncio
async def test_project_has_stored_commits_false() -> None:
    session = MagicMock()
    session.scalar = AsyncMock(return_value=None)
    assert await project_has_stored_commits(session, uuid.uuid4()) is False


def _session_returning_project(project: StubProject | None) -> MagicMock:
    session = MagicMock()
    session.execute = AsyncMock(
        return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=project))
    )
    session.commit = AsyncMock()
    return session


# -- deactivate_project_and_reconcile --


@pytest.mark.asyncio
async def test_deactivate_project_and_reconcile_flips_and_reconciles() -> None:
    project = StubProject(is_active=True)
    session = _session_returning_project(project)

    with patch(
        "app.workers.sync_common.deactivate_orphaned_team_members",
        new=AsyncMock(return_value=3),
    ) as recon:
        await deactivate_project_and_reconcile(
            session,
            project_db_id=uuid.uuid4(),
            team_id=uuid.uuid4(),
            gitlab_pid=42,
            reason="repo deleted",
        )

    assert project.is_active is False
    session.commit.assert_awaited_once()
    recon.assert_awaited_once()


@pytest.mark.asyncio
async def test_deactivate_project_skips_commit_when_already_inactive() -> None:
    project = StubProject(is_active=False)
    session = _session_returning_project(project)

    with patch(
        "app.workers.sync_common.deactivate_orphaned_team_members",
        new=AsyncMock(return_value=0),
    ):
        await deactivate_project_and_reconcile(
            session,
            project_db_id=uuid.uuid4(),
            team_id=uuid.uuid4(),
            gitlab_pid=42,
            reason="repo deleted",
        )

    # Already inactive -> no redundant flip/commit.
    session.commit.assert_not_awaited()
