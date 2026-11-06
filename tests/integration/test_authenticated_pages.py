"""Walk every dashboard page as a logged-in admin and assert none of them 500.

The existing dashboard integration tests only prove that these routes *refuse*
anonymous callers. Nothing ever renders them with a session, so a template that
references a removed attribute, or a route that unpacks a shape it no longer
gets, reaches production as a 500 with no test failing first.

`create_session_cookie` is used to mint the cookie rather than hand-rolling the
payload, so the test cannot drift from what login actually writes.
"""

from __future__ import annotations

import os
import uuid
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient
from starlette.responses import Response

pytestmark = pytest.mark.integration

_ADMIN = "render-probe-admin"


async def test_project_check_columns_match_live_data_when_only_stored_flags_exist(
    app, admin_client
):
    import re

    from sqlalchemy import delete

    from app.db.session import async_session_ctx
    from app.models import Course, GitLabProject, MetricSnapshot, Student, Team, TeamMember

    async with async_session_ctx() as db:
        course = Course(
            code=uuid.uuid4().hex[:12], name="Stored check flags", academic_year="2026/2027"
        )
        student = Student(gitlab_username="check-flags-" + uuid.uuid4().hex)
        db.add_all([course, student])
        await db.flush()
        team = Team(course_id=course.id, name="Stored flags")
        db.add(team)
        await db.flush()
        project = GitLabProject(
            team_id=team.id,
            gitlab_project_id=uuid.uuid4().int % 10**12,
            gitlab_project_path="qa/stored-checks",
        )
        db.add_all(
            [
                project,
                TeamMember(team_id=team.id, student_id=student.id),
                MetricSnapshot(
                    course_id=course.id,
                    team_id=team.id,
                    student_id=student.id,
                    weighted_score=0.5,
                    r01_issue_assigned=True,
                    checks_detail={},
                ),
            ]
        )
        await db.commit()
        course_id, student_id, project_id = course.id, student.id, project.id
    try:
        live = await admin_client.get(f"/dashboard/projects/{project_id}/live-data")
        assert live.status_code == 200
        assert live.json()["students"][0]["checks"]["R01"]["pass"] is True
        page = await admin_client.get(f"/dashboard/projects/{project_id}")
        assert page.status_code == 200
        row = re.search(
            rf'<tr\b[^>]*data-student-id="{student_id}"[^>]*>(.*?)</tr>', page.text, re.S
        )
        assert row
        assert 'class="check-pass"' in row[1]
    finally:
        async with async_session_ctx() as db:
            await db.execute(delete(MetricSnapshot).where(MetricSnapshot.course_id == course_id))
            await db.execute(delete(Course).where(Course.id == course_id))
            await db.execute(delete(Student).where(Student.id == student_id))
            await db.commit()


@pytest.mark.asyncio
async def test_activity_refresh_reuses_html_and_replaces_cached_snapshot(admin_client: Any):
    import json
    import re
    from datetime import UTC, datetime

    from sqlalchemy import delete

    from app.config import get_settings
    from app.db.session import async_session_ctx
    from app.models import Course, GitLabProject, Pipeline, Team
    from app.redis_pool import close_redis_pool, init_redis_pool
    from app.services.page_cache import invalidate_cascade

    course_id = uuid.uuid4()
    path = f"/dashboard/courses/{course_id}/activity"

    async def stats(headers=None):
        response = await admin_client.get(path, headers=headers)
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/html")
        config = re.search(
            r'<script\b[^>]*id="gp-course-activity-config"[^>]*>(.*?)</script>',
            response.text,
            re.S,
        )
        assert config
        return json.loads(config[1])["pipelineStats"]

    async with async_session_ctx() as db:
        db.add(
            Course(
                id=course_id,
                code=course_id.hex[:12],
                name="Activity cache",
                academic_year="2026/2027",
            )
        )
        await db.commit()
    init_redis_pool(str(get_settings().redis_url))
    try:
        assert (await stats())["passed"] == 0
        async with async_session_ctx() as db:
            team = Team(course_id=course_id, name="Activity cache")
            db.add(team)
            await db.flush()
            project = GitLabProject(
                team_id=team.id,
                gitlab_project_id=course_id.int % 10**12,
                gitlab_project_path="qa/activity-cache",
            )
            db.add(project)
            await db.flush()
            db.add(
                Pipeline(
                    project_id=project.id,
                    gitlab_pipeline_id=1,
                    status="success",
                    created_at=datetime.now(UTC),
                )
            )
            await db.commit()
        assert (await stats())["passed"] == 0
        assert (await stats({"Cache-Control": "no-cache"}))["passed"] == 1
        assert (await stats())["passed"] == 1
    finally:
        async with async_session_ctx() as db:
            await db.execute(delete(Course).where(Course.id == course_id))
            await db.commit()
        invalidate_cascade(course_id=course_id)
        close_redis_pool()


@pytest.mark.parametrize("role", ["teacher", "student"])
@pytest.mark.parametrize("suffix", ["", "/activity"])
async def test_cached_course_groups_stay_scoped_to_each_reader(app, role, suffix):
    import re

    from sqlalchemy import delete

    from app.config import get_settings
    from app.db.session import async_session_ctx
    from app.models import Course, CourseMembership, Student, Team, TeamMember, User
    from app.redis_pool import close_redis_pool, init_redis_pool
    from app.security.session_auth import SESSION_COOKIE_NAME, create_session_cookie

    async with async_session_ctx() as db:
        course = Course(
            code=uuid.uuid4().hex[:12], name="Private groups", academic_year="2026/2027"
        )
        db.add(course)
        await db.flush()
        viewers = []
        for _ in range(2):
            name = "cached-student-" + uuid.uuid4().hex
            user = User(username=name, gitlab_username=name, role=role, password_hash="unused")
            student = Student(gitlab_username=name)
            team = Team(course_id=course.id, name=name)
            db.add_all([user, student, team])
            await db.flush()
            db.add(CourseMembership(course_id=course.id, user_id=user.id, role="student"))
            db.add(TeamMember(team_id=team.id, student_id=student.id))
            viewers.append((name, user.id, student.id, team.id))
        await db.commit()
        course_id = course.id

    settings = get_settings()
    init_redis_pool(str(settings.redis_url))
    try:
        for index in (0, 1, 0, 1):
            name, user_id, _, team_id = viewers[index]
            carrier = Response()
            create_session_cookie(
                carrier,
                secret_key=settings.secret_key,
                user=name,
                role=role,
                user_id=str(user_id),
                gitlab_username=name,
                allow_stateless_fallback=True,
            )
            token = (
                carrier.headers["set-cookie"]
                .split(f"{SESSION_COOKIE_NAME}=", 1)[1]
                .split(";", 1)[0]
            )
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test",
                cookies={SESSION_COOKIE_NAME: token},
                headers={"User-Agent": "pytest"},
            ) as client:
                response = await client.get(f"/dashboard/courses/{course_id}{suffix}")
                assert response.status_code == 200
                rows = re.findall(r'<tr\b[^>]*\bdata-team-id="([^"]+)"', response.text)
                assert rows == [str(team_id)]
    finally:
        async with async_session_ctx() as db:
            await db.execute(delete(Course).where(Course.id == course_id))
            await db.execute(delete(User).where(User.id.in_([v[1] for v in viewers])))
            await db.execute(delete(Student).where(Student.id.in_([v[2] for v in viewers])))
            await db.commit()
        close_redis_pool()


@pytest.mark.asyncio
async def test_activity_group_uses_the_latest_finished_pipeline_across_projects(app):
    from datetime import UTC, datetime, timedelta

    from sqlalchemy import delete

    from app.api.dashboard.courses.activity import course_activity
    from app.db.session import async_session_ctx
    from app.models import Course, GitLabProject, Pipeline, Team

    course_id = uuid.uuid4()
    async with async_session_ctx() as db:
        course = Course(
            id=course_id,
            code=course_id.hex[:12],
            name="Activity order",
            academic_year="2026/2027",
            settings=None,
        )
        db.add(course)
        await db.flush()
        team = Team(course_id=course_id, name="Activity order")
        db.add(team)
        await db.flush()
        projects = [
            GitLabProject(
                team_id=team.id,
                gitlab_project_id=uuid.uuid4().int % 10**12,
                gitlab_project_path=f"qa/activity-order-{i}",
            )
            for i in range(2)
        ]
        db.add_all(projects)
        await db.flush()
        now = datetime.now(UTC)
        db.add_all(
            [
                Pipeline(
                    project_id=projects[0].id,
                    gitlab_pipeline_id=1,
                    status="success",
                    created_at=now - timedelta(hours=2),
                ),
                Pipeline(
                    project_id=projects[0].id,
                    gitlab_pipeline_id=2,
                    status="failed",
                    created_at=None,
                ),
                Pipeline(
                    project_id=projects[1].id,
                    gitlab_pipeline_id=3,
                    status="failed",
                    created_at=now - timedelta(hours=1),
                ),
                Pipeline(
                    project_id=projects[1].id,
                    gitlab_pipeline_id=4,
                    status="running",
                    created_at=now,
                ),
            ]
        )
        await db.flush()
        activity = await course_activity(db, course, [team])
        assert activity.pipeline_stats == {
            "passed": 1,
            "failed": 0,
            "running": 1,
            "pending": 0,
            "other": 0,
        }
        assert activity.rows[0]["latest_status"] == "failed"
        await db.execute(delete(Course).where(Course.id == course_id))
        await db.commit()


@pytest.mark.asyncio
async def test_mr_roles_resolve_people_without_membership_or_comments(app):
    from datetime import UTC, datetime

    from app.api.dashboard.students.profile import Roster, Scope, _authored_mrs, _reviews_given
    from app.db.session import async_session_ctx
    from app.models.course import Course
    from app.models.merge_request import MergeRequest
    from app.models.mr_note import MRNote
    from app.models.project import GitLabProject
    from app.models.review_activity import ReviewActivity
    from app.models.student import Student
    from app.models.team import Team

    async with async_session_ctx() as db:
        try:
            course = Course(
                code=uuid.uuid4().hex[:12],
                name="MR roles",
                academic_year="2026/2027",
                settings=None,
            )
            db.add(course)
            await db.flush()
            team = Team(course_id=course.id, name="MR roles")
            db.add(team)
            await db.flush()
            author = Student(
                gitlab_username="mr-role-author", full_name="MR Author", gitlab_user_id=900001
            )
            reviewer = Student(
                gitlab_username="mr-role-reviewer",
                full_name="Assigned outsider",
                gitlab_user_id=900002,
            )
            approver = Student(
                gitlab_username="mr-role-approver",
                full_name="Approving outsider",
                gitlab_user_id=900003,
            )
            db.add_all([author, reviewer, approver])
            project = GitLabProject(
                team_id=team.id,
                gitlab_project_id=uuid.uuid4().int % 10**12,
                gitlab_project_path="qa/mr-roles",
            )
            db.add(project)
            await db.flush()
            for iid in [1, 2]:
                mr = MergeRequest(
                    project_id=project.id,
                    gitlab_id=uuid.uuid4().int % 10**12,
                    gitlab_iid=iid,
                    author_id=author.id,
                    state="merged",
                    reviewer_gitlab_ids=[900002],
                    approved_by_gitlab_ids=[900003] if iid == 1 else [],
                    commit_shas=[],
                    created_at=datetime.now(UTC),
                )
                db.add(mr)
                await db.flush()
                db.add(
                    MRNote(
                        merge_request_id=mr.id,
                        gitlab_note_id=uuid.uuid4().int % 10**12,
                        author_id=author.id,
                        body="Author explaining the change",
                        is_system=False,
                    )
                )
                if iid == 2:
                    db.add(
                        ReviewActivity(
                            merge_request_id=mr.id, reviewer_id=reviewer.id, is_approved=True
                        )
                    )
            await db.flush()
            cards, _, _ = await _authored_mrs(
                db,
                Scope.of(author, author.id, team.id, course),
                Roster({}, {}, {}, {}, set(), set()),
                None,
            )
            by_iid = {card["mr"].gitlab_iid: card for card in cards}
            first = by_iid[1]
            assert [p["name"] for p in first["reviewers"]] == ["Assigned outsider"]
            assert first["reviewers"][0]["profile_url"] is None
            assert [p["name"] for p in first["participants"]] == ["Approving outsider"]
            assert first["participants"][0]["is_approved"]
            assert first["has_review_activity"]
            assert by_iid[2]["thread_count"] == 1
            assert not by_iid[2]["has_review_activity"], (
                "assignment and author notes are not a review"
            )
            assert not by_iid[2]["reviewers"][0]["is_approved"], (
                "a stale aggregate must not restore a revoked approval"
            )

            approved_mr = first["mr"]
            approved_mr.approved_by_gitlab_ids = [900002]
            aggregate = ReviewActivity(
                merge_request_id=approved_mr.id,
                reviewer_id=reviewer.id,
                note_count=1,
                is_approved=False,
            )
            db.add(aggregate)
            db.add(
                MRNote(
                    merge_request_id=approved_mr.id,
                    gitlab_note_id=uuid.uuid4().int % 10**12,
                    author_id=reviewer.id,
                    body="Review from the assigned reviewer",
                    is_system=False,
                )
            )
            await db.flush()
            reviewer_scope = Scope.of(reviewer, reviewer.id, team.id, course)
            reviewer_roster = Roster({}, {}, {}, {}, set(), set())
            _, _, view = await _authored_mrs(db, reviewer_scope, reviewer_roster, None)
            given = await _reviews_given(db, reviewer_scope, reviewer_roster, view)
            assert len(given) == 1
            assert given[0]["is_approved"]
            assert not given[0]["review"].is_approved

            approved_mr.approved_by_gitlab_ids = []
            aggregate.is_approved = True
            await db.flush()
            given = await _reviews_given(db, reviewer_scope, reviewer_roster, view)
            assert not given[0]["is_approved"]
            assert given[0]["review"].is_approved
        finally:
            await db.rollback()


@pytest.mark.asyncio
async def test_incremental_sync_repairs_old_mr_lists_and_retries_missing_details(app):
    from datetime import UTC, datetime

    from sqlalchemy import delete

    from app.db.session import async_session_ctx
    from app.models.commit import Commit
    from app.models.course import Course
    from app.models.merge_request import MergeRequest
    from app.models.project import GitLabProject
    from app.models.team import Team
    from app.services.gitlab.client import GitLabAPIError
    from app.workers.project_sync import SyncCounts, _recover_mr_commits, _Run

    class GitLab:
        calls: list[int]

        def __init__(self):
            self.calls = []
            self.fail = True

        async def get_mr_commits(self, _pid, iid):
            self.calls.append(iid)
            if iid == 5 and self.fail:
                raise GitLabAPIError(503, "Temporary read failure")
            return [
                {"id": key * 40} for key in {1: ["a", "b"], 3: ["a", "c"], 6: ["a"]}.get(iid, [])
            ]

        async def get_commit(self, _pid, sha):
            return {
                "id": sha,
                "short_id": sha[:8],
                "title": "Recovered commit",
                "author_name": "Recovered author",
                "author_email": "qa@example.test",
                "committed_date": "2026-10-20T10:00:00Z",
                "stats": {"additions": 1, "deletions": 0},
            }

    async with async_session_ctx() as db:
        course = Course(code=uuid.uuid4().hex[:12], name="MR backfill", academic_year="2026/2027")
        db.add(course)
        await db.flush()
        team = Team(course_id=course.id, name="MR backfill")
        db.add(team)
        await db.flush()
        course_id = course.id
        try:
            project = GitLabProject(
                team_id=team.id,
                gitlab_project_id=uuid.uuid4().int % 10**12,
                gitlab_project_path="qa/mr-backfill",
            )
            db.add(project)
            await db.flush()
            for key in ["a", "b"]:
                db.add(Commit(project_id=project.id, sha=key * 40, short_sha=key * 8))
            mrs = {}
            for iid, shas in [
                (1, None),
                (2, None),
                (3, ["a", "c"]),
                (4, ["a"]),
                (5, None),
                (6, None),
            ]:
                mr = MergeRequest(
                    project_id=project.id,
                    gitlab_id=uuid.uuid4().int % 10**12,
                    gitlab_iid=iid,
                    state="merged",
                    source_branch="feature",
                    created_at=datetime(2020, 1, 1, tzinfo=UTC),
                    commit_shas=[key * 40 for key in shas] if shas is not None else None,
                )
                db.add(mr)
                mrs[iid] = mr
            await db.flush()
            gl = GitLab()
            run = _Run(
                db, gl, int(project.gitlab_project_id), project.id, "2026-09-01", {}, SyncCounts()
            )
            assert not run.mrs, "the incremental GitLab MR response contains no changed MR"
            assert await _recover_mr_commits(run, project, {}) == 1
            await db.flush()
            for mr in mrs.values():
                await db.refresh(mr)
            assert set(gl.calls) == {1, 2, 3, 5, 6}
            assert mrs[1].commit_shas == ["a" * 40, "b" * 40]
            assert mrs[2].commit_shas == []
            assert mrs[3].commit_shas == ["a" * 40, "c" * 40]
            assert mrs[5].commit_shas is None
            assert mrs[6].commit_shas == ["a" * 40]
            gl.calls.clear()
            gl.fail = False
            run.mrs = [{"iid": 4, "source_branch": "feature"}]
            assert await _recover_mr_commits(run, project, {}) == 0
            for mr in mrs.values():
                await db.refresh(mr)
            assert set(gl.calls) == {4, 5}
            assert mrs[4].commit_shas == []
            assert mrs[5].commit_shas == []
        finally:
            await db.rollback()
            await db.execute(delete(Course).where(Course.id == course_id))
            await db.commit()


@pytest.mark.asyncio
@pytest.mark.parametrize("project_scoped", [False, True])
@pytest.mark.parametrize(
    "status", ["started", "running", "enqueued", "completed", "failed", "cancelled"]
)
async def test_sync_matches_discovery_poll_and_stream(app, admin_client, project_scoped, status):
    from datetime import UTC, datetime

    from sqlalchemy import delete

    from app.api.sync_stream import _sync_snapshot
    from app.db.session import async_session_ctx
    from app.models.background_job import BackgroundJob
    from app.models.course import Course
    from app.models.project import GitLabProject
    from app.models.team import Team

    async with async_session_ctx() as db:
        course = Course(
            code=uuid.uuid4().hex[:12],
            name="Started sync parity",
            academic_year="2026/2027",
            settings=None,
        )
        db.add(course)
        await db.flush()
        team = Team(course_id=course.id, name="Started")
        db.add(team)
        await db.flush()
        project = GitLabProject(
            team_id=team.id,
            gitlab_project_id=uuid.uuid4().int % 10**12,
            gitlab_project_path="qa/started",
            is_active=True,
        )
        db.add(project)
        await db.flush()
        job = BackgroundJob(
            job_type="sync",
            status=status,
            team_id=team.id,
            course_id=course.id,
            project_id=project.id if project_scoped else None,
            completed_at=datetime.now(UTC)
            if status in {"completed", "failed", "cancelled"}
            else None,
        )
        db.add(job)
        await db.commit()
        course_id, job_id = course.id, job.id
        try:
            running = status in {"started", "running"}
            queued = status == "enqueued"
            snapshot = await _sync_snapshot(db, course)
            poll = await admin_client.get(f"/api/v1/courses/{course.id}/sync-status")
            assert poll.status_code == 200
            for data in [snapshot, poll.json()]:
                assert data["sync_running_count"] == int(running and not project_scoped)
                assert data["sync_queued_count"] == int(queued and not project_scoped)
                assert data["has_active_sync"] is (not project_scoped)
                assert data["project_sync_running_count"] == int(running and project_scoped)
                assert data["project_sync_queued_count"] == int(queued and project_scoped)
                if not project_scoped:
                    assert data["teams"][0]["sync_status"] == ("running" if running else status)
            response = await admin_client.get("/api/v1/sync/active")
            assert response.status_code == 200
            discovered = [c for c in response.json()["courses"] if c["course_id"] == str(course.id)]
            assert len(discovered) == int(not project_scoped)
            if discovered:
                assert discovered[0]["running"] == int(running)
                assert discovered[0]["queued"] == int(queued)
        finally:
            await db.rollback()
            await db.execute(delete(BackgroundJob).where(BackgroundJob.id == job_id))
            await db.execute(delete(Course).where(Course.id == course_id))
            await db.commit()


@pytest.mark.asyncio
async def test_mr_attribution_uses_only_its_complete_gitlab_commit_list(app):
    from datetime import UTC, datetime

    from app.api.dashboard.students.profile import Roster, Scope, _authored_mrs
    from app.db.session import async_session_ctx
    from app.models.commit import Commit
    from app.models.course import Course
    from app.models.merge_request import MergeRequest
    from app.models.project import GitLabProject
    from app.models.student import Student
    from app.models.team import Team

    async with async_session_ctx() as db:
        try:
            course = Course(
                code=uuid.uuid4().hex[:12],
                name="MR attribution",
                academic_year="2026/2027",
                settings=None,
            )
            student = Student(gitlab_username="attribution-student")
            teacher = Student(gitlab_username="attribution-teacher")
            db.add_all([course, student, teacher])
            await db.flush()
            team = Team(course_id=course.id, name="Attribution")
            db.add(team)
            await db.flush()
            project = GitLabProject(
                team_id=team.id,
                gitlab_project_id=uuid.uuid4().int % 10**12,
                gitlab_project_path="qa/attribution",
                is_active=True,
            )
            db.add(project)
            await db.flush()
            now = datetime(2026, 10, 30, tzinfo=UTC)
            for sha, name, author_id, ref, date in [
                ("a", "Page student", student.id, "feature", now),
                ("b", "Peer", None, "feature", now),
                ("c", "Teacher template", teacher.id, "feature", datetime(2020, 1, 1, tzinfo=UTC)),
                ("d", "Teacher contribution", teacher.id, "feature", now),
                ("e", "Unrelated", None, None, now),
                ("f", "Peer", None, "feature", now),
            ]:
                db.add(
                    Commit(
                        project_id=project.id,
                        sha=sha * 40,
                        short_sha=sha * 8,
                        author_name=name,
                        author_id=author_id,
                        ref=ref,
                        committed_at=date,
                    )
                )
            for iid, shas, branch in [
                (1, ["a", "b", "f"], "feature"),
                (2, ["d"], "feature"),
                (3, [], "feature"),
                (4, ["a", "missing"], "feature"),
                (5, None, "feature"),
                (6, None, "deleted"),
            ]:
                db.add(
                    MergeRequest(
                        project_id=project.id,
                        gitlab_id=iid,
                        gitlab_iid=iid,
                        title="Attribution probe",
                        state="merged",
                        source_branch=branch,
                        author_id=student.id,
                        commit_shas=[s * 40 for s in shas] if shas is not None else None,
                        created_at=now,
                        updated_at=now,
                        source_branch_deleted=True,
                    )
                )
            await db.flush()
            roster = Roster({}, {}, {}, {}, {teacher.id}, set())
            cards, _branches, _view = await _authored_mrs(
                db, Scope.of(student, student.id, team.id, course), roster, None
            )
            by_iid = {card["mr"].gitlab_iid: card for card in cards}
            first = by_iid[1]
            assert {a["name"] for a in first["commit_authors"]} == {"Page student", "Peer"}
            assert len(first["commit_authors"]) == 2
            assert not first["commit_data_missing"]
            assert len(first["branch_commits"]) == 3
            assert by_iid[2]["commit_authors"] == [
                {"name": "Teacher contribution", "is_page_student": False, "is_teacher": True}
            ]
            assert by_iid[3]["branch_commits"] == []
            assert by_iid[3]["commit_authors"] == []
            assert not by_iid[3]["commit_data_missing"]
            for iid in [4, 5, 6]:
                assert by_iid[iid]["commit_data_missing"]
                assert by_iid[iid]["commit_authors"] == []
        finally:
            await db.rollback()


@pytest.mark.asyncio
@pytest.mark.parametrize("mode", ["new", "reactivate", "reassign"])
async def test_linking_a_project_discards_cached_group_and_course_views(admin_client, mode):
    from sqlalchemy import delete

    from app.config import get_settings
    from app.db.session import async_session_ctx
    from app.models.course import Course
    from app.models.project import GitLabProject
    from app.models.team import Team
    from app.redis_pool import close_redis_pool, init_redis_pool
    from app.security.csrf import generate_csrf_token
    from app.services.page_cache import get_cached, set_cached

    init_redis_pool(str(get_settings().redis_url))
    course_ids = [uuid.uuid4(), uuid.uuid4()]
    team_ids = [uuid.uuid4(), uuid.uuid4()]
    project_id, gitlab_id = uuid.uuid4(), uuid.uuid4().int % 10**12
    async with async_session_ctx() as db:
        for course_id, team_id in zip(course_ids, team_ids, strict=True):
            db.add(
                Course(
                    id=course_id,
                    code=course_id.hex[:12],
                    name="Cache probe",
                    academic_year="2026/2027",
                )
            )
            await db.flush()
            db.add(Team(id=team_id, course_id=course_id, name="Cache probe"))
        if mode != "new":
            await db.flush()
            db.add(
                GitLabProject(
                    id=project_id,
                    team_id=team_ids[1] if mode == "reassign" else team_ids[0],
                    gitlab_project_id=gitlab_id,
                    gitlab_project_path="qa/cache-probe",
                    is_active=False,
                )
            )
        await db.commit()

    scopes = [
        ("team", team_ids[0]),
        ("course", course_ids[0]),
        ("course-activity", course_ids[0]),
        ("course-analytics", course_ids[0]),
    ]
    if mode != "new":
        scopes.append(("project", project_id))
    if mode == "reassign":
        scopes.extend([("team", team_ids[1]), ("course", course_ids[1])])
    try:
        for kind, scope_id in scopes:
            set_cached(kind, scope_id, "probe", "stale table")
            assert get_cached(kind, scope_id, "probe") == "stale table"
        response = await admin_client.post(
            f"/api/v1/projects/{team_ids[0]}/projects",
            json={"gitlab_project_id": gitlab_id, "gitlab_project_path": "qa/cache-probe"},
            headers={
                "X-CSRF-Token": generate_csrf_token({"user": _ADMIN}, get_settings().secret_key)
            },
        )
        assert response.status_code == 201
        assert all(get_cached(kind, scope_id, "probe") is None for kind, scope_id in scopes)
        async with async_session_ctx() as db:
            project = await db.get(GitLabProject, uuid.UUID(response.json()["id"]))
            assert project is not None
            assert project.is_active
            assert project.team_id == team_ids[0]
    finally:
        async with async_session_ctx() as db:
            await db.execute(delete(Course).where(Course.id.in_(course_ids)))
            await db.commit()
        close_redis_pool()


@pytest.fixture
async def app() -> Any:
    os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
    os.environ.setdefault("SECRET_KEY", "test-secret-key-minimum-sixteen-chars")
    os.environ.setdefault("TEACHER_API_TOKEN", "test-token-12345678")
    os.environ.setdefault("APP_ENV", "test")
    os.environ["ALLOWED_HOSTS"] = '["test","localhost","127.0.0.1"]'

    from sqlalchemy import text

    from app.config import get_settings
    from app.db.session import dispose_engine, init_engine
    from app.main import create_app
    from app.models import Base

    get_settings.cache_clear()
    settings = get_settings()
    engine = init_engine(
        str(settings.database_url),
        pool_size=settings.db_pool_size,
        echo=settings.db_echo,
    )
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS pgcrypto"))
        await conn.run_sync(Base.metadata.create_all)
    application = create_app()
    try:
        yield application
    finally:
        await dispose_engine()


@pytest.fixture
async def admin_client(app: Any) -> Any:
    """A client carrying a real admin session cookie."""
    from app.config import get_settings
    from app.security.session_auth import SESSION_COOKIE_NAME, create_session_cookie

    secret = get_settings().secret_key
    secret = secret.get_secret_value() if hasattr(secret, "get_secret_value") else str(secret)

    carrier = Response()
    create_session_cookie(
        carrier,
        secret_key=secret,
        user=_ADMIN,
        role="admin",
        user_id=str(uuid.uuid4()),
        gitlab_username=_ADMIN,
        allow_stateless_fallback=True,
    )
    # Read the value back off the response rather than re-deriving it.
    raw = carrier.headers.get("set-cookie", "")
    token = raw.split(f"{SESSION_COOKIE_NAME}=", 1)[-1].split(";", 1)[0]
    assert token, "could not mint a session cookie"

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        cookies={SESSION_COOKIE_NAME: token},
        headers={"User-Agent": "pytest"},
    ) as client:
        yield client


def _pages() -> list[str]:
    """Discovered from the app, not hard-coded.

    The previous list named `/dashboard/courses/`, which does not exist, and
    omitted `/dashboard/activity` and `/dashboard/notifications` entirely.
    """
    from app.main import create_app
    from tests.route_discovery import dashboard_pages

    return dashboard_pages(create_app())


_PAGES = _pages()


def test_the_page_list_is_not_empty() -> None:
    """Discovery walks lazily-included routers; if that breaks it returns an
    empty list and every page test below silently disappears."""
    assert len(_PAGES) >= 8, f"only discovered {_PAGES}"
    assert "/dashboard/" in _PAGES
    assert "/dashboard/status" not in _PAGES  # Bookmark redirect, not a separate page.


async def test_the_session_actually_authenticates(admin_client: AsyncClient) -> None:
    """Otherwise every page below would 302 and the walk would prove nothing."""
    response = await admin_client.get("/dashboard/", follow_redirects=False)

    assert response.status_code == 200, (
        f"expected an authenticated 200, got {response.status_code} - "
        "the cookie is not being accepted, so the page walk is vacuous"
    )


@pytest.mark.parametrize("path", _PAGES)
async def test_page_does_not_error(admin_client: AsyncClient, path: str) -> None:
    response = await admin_client.get(path, follow_redirects=False)

    assert response.status_code < 500, f"{path} -> {response.status_code}\n{response.text[:600]}"


async def test_support_submission_uses_one_service_and_the_session_author(
    admin_client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    from sqlalchemy import delete

    from app.config import get_settings
    from app.db.session import async_session_ctx
    from app.models.course import Course
    from app.models.support_form import SupportForm
    from app.models.support_ticket import SupportTicket
    from app.models.user import User
    from app.security.csrf import generate_csrf_token

    settings = get_settings()
    monkeypatch.setattr(settings, "feature_support_forms", True)
    monkeypatch.setattr(settings, "feature_email_notifications", False)
    course_id, form_id = uuid.uuid4(), uuid.uuid4()
    async with async_session_ctx() as db:
        from sqlalchemy import select

        existing_user = (await db.execute(select(User.id).where(User.username == _ADMIN))).scalar()
        if not existing_user:
            db.add(User(username=_ADMIN, password_hash="!", role="admin"))
        db.add(
            Course(id=course_id, code="SUPPORT-PROBE", name="Support", academic_year="2026/2027")
        )
        await db.flush()
        db.add(
            SupportForm(id=form_id, course_id=course_id, category="bug", title="Bug", questions=[])
        )
        await db.commit()
    headers = {"X-CSRF-Token": generate_csrf_token({"user": _ADMIN}, settings.secret_key)}
    payload = {
        "course_id": str(course_id),
        "form_id": str(form_id),
        "responses": {},
        "title": "Submission probe",
        "submitted_by": "forged-author",
        "support_type": "student",
    }
    path = f"/api/v1/support/{uuid.uuid4()}"
    try:
        assert (await admin_client.post(path, json=payload)).status_code == 403
        wrong = {**payload, "course_id": str(uuid.uuid4())}
        assert (await admin_client.post(path, json=wrong, headers=headers)).status_code == 404
        response = await admin_client.post(path, json=payload, headers=headers)
        assert response.status_code == 201, response.text
        async with async_session_ctx() as db:
            ticket = await db.get(SupportTicket, response.json()["id"])
            assert ticket is not None
            assert ticket.submitted_by == _ADMIN
            assert ticket.feedback_type == "teacher"
            assert ticket.category == "bug"
        monkeypatch.setattr(settings, "feature_support_forms", False)
        response = await admin_client.post(path, json=payload, headers=headers)
        assert response.status_code == 503
    finally:
        async with async_session_ctx() as db:
            await db.execute(delete(Course).where(Course.id == course_id))
            if not existing_user:
                await db.execute(delete(User).where(User.username == _ADMIN))
            await db.commit()


@pytest.mark.parametrize("role", ["admin", "teacher", "student"])
async def test_monitoring_consolidation_keeps_role_boundaries(app, role):
    from app.config import get_settings
    from app.security.session_auth import SESSION_COOKIE_NAME, create_session_cookie

    secret = get_settings().secret_key
    carrier = Response()
    create_session_cookie(
        carrier,
        secret_key=secret,
        user=f"integration_monitoring_{role}",
        role=role,
        user_id=str(uuid.uuid4()),
        allow_stateless_fallback=True,
    )
    token = carrier.headers["set-cookie"].split(f"{SESSION_COOKIE_NAME}=", 1)[1].split(";", 1)[0]
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        cookies={SESSION_COOKIE_NAME: token},
        headers={"User-Agent": "pytest"},
    ) as client:
        bookmark = await client.get("/dashboard/status", follow_redirects=False)
        assert bookmark.status_code == 303
        assert bookmark.headers["location"] == (
            "/dashboard/admin/system" if role == "admin" else "/dashboard/"
        )
        for path in (
            "/dashboard/admin/system",
            "/dashboard/api/v1/admin/system/monitoring",
            "/dashboard/api/v1/admin/system/jobs",
        ):
            response = await client.get(path, follow_redirects=False)
            assert response.status_code == (200 if role == "admin" else 403), (
                path,
                role,
                response.text[:300],
            )


@pytest.mark.parametrize("active", [True, False])
@pytest.mark.parametrize(
    ("role", "membership", "can_edit"),
    [
        ("admin", None, True),
        ("teacher", None, False),
        ("teacher", "student", False),
        ("teacher", "teacher", True),
        ("teacher", "owner", True),
        ("student", "student", False),
    ],
)
async def test_detail_pages_use_course_staff_rights_on_cache_hit_and_miss(
    app, role, membership, can_edit, active
):
    import json
    import re
    from datetime import UTC, datetime

    from sqlalchemy import delete, select

    from app.config import get_settings
    from app.db.session import async_session_ctx
    from app.models import Course, CourseMembership, GitLabProject, Student, Team, TeamMember, User
    from app.models.background_job import BackgroundJob
    from app.redis_pool import close_redis_pool, init_redis_pool
    from app.security.csrf import generate_csrf_token
    from app.security.session_auth import SESSION_COOKIE_NAME, create_session_cookie

    username = "course-rights-" + uuid.uuid4().hex
    async with async_session_ctx() as db:
        user = User(username=username, role=role, password_hash="unused", is_active=True)
        student = Student(full_name=username, gitlab_username=username)
        course = Course(
            code=username[-12:], name=username, academic_year="2026/2027", is_active=active
        )
        db.add_all([user, student, course])
        await db.flush()
        team = Team(course_id=course.id, name="Rights probe")
        db.add(team)
        await db.flush()
        db.add(TeamMember(team_id=team.id, student_id=student.id))
        project = GitLabProject(
            team_id=team.id,
            gitlab_project_id=uuid.uuid4().int % 10**12,
            gitlab_project_path="qa/course-rights",
        )
        db.add(project)
        if membership:
            db.add(CourseMembership(course_id=course.id, user_id=user.id, role=membership))
        await db.commit()
        course_id, user_id, student_id = course.id, user.id, student.id
        team_id, project_id = team.id, project.id

    pages = (
        (f"courses/{course_id}", "gp-course-detail-config"),
        (f"courses/{course_id}/activity", "gp-course-activity-config"),
        (f"teams/{team_id}", "gp-team-detail-config"),
        (f"projects/{project_id}", "gp-project-detail-config"),
        (f"students/{student_id}/team/{team_id}", "gp-student-detail-config"),
    )

    settings = get_settings()
    init_redis_pool(str(settings.redis_url))
    carrier = Response()
    create_session_cookie(
        carrier,
        secret_key=settings.secret_key,
        user=username,
        role=role,
        user_id=str(user_id),
        gitlab_username=username,
        allow_stateless_fallback=True,
    )
    token = carrier.headers["set-cookie"].split(f"{SESSION_COOKIE_NAME}=", 1)[1].split(";", 1)[0]
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
            cookies={SESSION_COOKIE_NAME: token},
            headers={"User-Agent": "pytest"},
        ) as client:
            for _ in range(2):
                for path, config_id in pages:
                    response = await client.get(f"/dashboard/{path}")
                    assert response.status_code == 200, (path, response.text[:300])
                    config = re.search(
                        rf'<script\b[^>]*id="{config_id}"[^>]*>(.*?)</script>',
                        response.text,
                        re.S,
                    )
                    assert config, path
                    assert json.loads(config[1])["canEdit"] is can_edit, path
                    if path == f"courses/{course_id}":
                        assert ('data-action="triggerSyncAll"' in response.text) is can_edit
                        assert ('id="addTeamModal"' in response.text) is can_edit
                    if path == f"teams/{team_id}":
                        assert ('id="linkProjectModal"' in response.text) is can_edit

            for path in (
                f"/dashboard/courses/{course_id}/teachers",
                f"/dashboard/courses/{course_id}/analytics",
                f"/api/v1/courses/{course_id}/run-checks-status",
                f"/api/v1/courses/{course_id}/sync-status",
            ):
                response = await client.get(path)
                expected = (
                    200
                    if can_edit
                    else (403 if role == "student" and not path.endswith("/sync-status") else 404)
                )
                assert response.status_code == expected, (path, response.text[:300])
            async with async_session_ctx() as db:
                db.add(
                    BackgroundJob(
                        job_type="sync",
                        status="completed",
                        team_id=team_id,
                        course_id=course_id,
                        completed_at=datetime.now(UTC),
                    )
                )
                await db.commit()
            discovery = await client.get("/api/v1/sync/active")
            assert discovery.status_code == 200
            assert (
                any(c["course_id"] == str(course_id) for c in discovery.json()["courses"])
                is can_edit
            )

            for scope, entity_id in (("teams", team_id), ("projects", project_id)):
                live = await client.get(f"/dashboard/{scope}/{entity_id}/live-data")
                assert live.status_code == 200
                data = live.json()
                assert "summary" not in data
                if role == "student" and not can_edit:
                    assert data["students"] == []
                else:
                    assert [s["id"] for s in data["students"]] == [str(student_id)]
                    assert all(
                        "email" not in s and "gitlab_user_id" not in s for s in data["students"]
                    )

            if not can_edit:
                headers = {
                    "X-CSRF-Token": generate_csrf_token({"user": username}, settings.secret_key)
                }
                for path in (
                    f"/dashboard/courses/{course_id}/archive",
                    f"/dashboard/courses/{course_id}/activate",
                    f"/dashboard/courses/{course_id}/teachers",
                    f"/dashboard/admin/courses/{course_id}/teachers",
                    f"/dashboard/teams/{team_id}/members/{student_id}/toggle-exclusion",
                ):
                    response = await client.post(path, headers=headers)
                    expected = (
                        403 if role == "student" or path.endswith("toggle-exclusion") else 404
                    )
                    assert response.status_code == expected, (path, response.text[:300])
                async with async_session_ctx() as db:
                    assert (await db.get(Course, course_id)).is_active is active
                    member = await db.get(TeamMember, (team_id, student_id))
                    assert not member.excluded_from_scoring
            elif role == "teacher":
                async with async_session_ctx() as db:
                    staff = await db.scalar(
                        select(CourseMembership).where(
                            CourseMembership.course_id == course_id,
                            CourseMembership.user_id == user_id,
                        )
                    )
                    staff.role = "student"
                    await db.commit()
                for path, config_id in pages:
                    response = await client.get(f"/dashboard/{path}")
                    assert response.status_code == 200
                    config = re.search(
                        rf'<script\b[^>]*id="{config_id}"[^>]*>(.*?)</script>',
                        response.text,
                        re.S,
                    )
                    assert config, path
                    assert json.loads(config[1])["canEdit"] is False, path
    finally:
        async with async_session_ctx() as db:
            await db.execute(delete(Course).where(Course.id == course_id))
            await db.execute(delete(User).where(User.id == user_id))
            await db.execute(delete(Student).where(Student.id == student_id))
            await db.commit()
        close_redis_pool()


@pytest.mark.parametrize("latest", ["failed", "cancelled", "started", None])
@pytest.mark.parametrize("with_metric", [False, True])
async def test_course_group_state_agrees_across_render_live_poll_and_stream(
    app, admin_client, latest, with_metric
):
    import re
    from datetime import UTC, datetime, timedelta

    from sqlalchemy import delete

    from app.api.dashboard.courses.overview import team_sync_states
    from app.api.sync_stream import _sync_snapshot
    from app.db.session import async_session_ctx
    from app.models import BackgroundJob, Course, GitLabProject, Team, TeamMetricSnapshot

    now = datetime.now(UTC)
    async with async_session_ctx() as db:
        course = Course(code=uuid.uuid4().hex[:12], name="Group state", academic_year="2026/2027")
        db.add(course)
        await db.flush()
        team = Team(course_id=course.id, name="Newest group job")
        db.add(team)
        await db.flush()
        if with_metric:
            db.add(
                TeamMetricSnapshot(
                    course_id=course.id,
                    team_id=team.id,
                    computed_at=now,
                    avg_weighted_score=0.765,
                    overall_traffic_light="GREEN",
                )
            )
        project = GitLabProject(
            team_id=team.id,
            gitlab_project_id=uuid.uuid4().int % 10**12,
            gitlab_project_path="qa/group-state",
        )
        db.add(project)
        await db.flush()
        jobs = [
            BackgroundJob(
                course_id=course.id,
                team_id=team.id,
                job_type="sync",
                status="completed",
                enqueued_at=now - timedelta(hours=3),
                completed_at=now - timedelta(hours=3),
            )
        ]
        if latest:
            for age, state in ((40, "running"), (30, "completed"), (20, latest)):
                jobs.append(
                    BackgroundJob(
                        course_id=course.id,
                        team_id=team.id,
                        job_type="sync",
                        status=state,
                        enqueued_at=now - timedelta(seconds=age),
                    )
                )
        jobs.append(
            BackgroundJob(
                course_id=course.id,
                team_id=team.id,
                project_id=project.id,
                job_type="sync",
                status="running",
                enqueued_at=now - timedelta(seconds=5),
            )
        )
        db.add_all(jobs)
        await db.commit()
        course_id, team_id = course.id, team.id
    expected = "running" if latest == "started" else latest
    try:
        async with async_session_ctx() as db:
            states, counts = await team_sync_states(db, [team_id])
            assert states.get(team_id) == expected
            assert counts["sync_running_count"] == int(expected == "running")
            course = await db.get(Course, course_id)
            streamed = await _sync_snapshot(db, course)
            assert streamed["teams"][0]["sync_status"] == expected
        poll = await admin_client.get(f"/api/v1/courses/{course_id}/sync-status")
        assert poll.status_code == 200
        assert poll.json()["teams"][0]["sync_status"] == expected
        live = await admin_client.get(f"/dashboard/courses/{course_id}/live-data")
        assert live.status_code == 200
        assert live.json()["teams"][0]["sync_status"] == expected
        iso = now.strftime("%Y-%m-%dT%H:%M:%SZ") if with_metric else None
        for payload in (streamed, poll.json(), live.json()):
            assert payload["teams"][0]["last_updated_iso"] == iso
        assert live.json()["teams"][0]["avg_score"] == (76 if with_metric else None)
        page = await admin_client.get(f"/dashboard/courses/{course_id}?lang=en")
        assert page.status_code == 200
        row = re.search(rf'<tr\b[^>]*data-team-id="{team_id}"[^>]*>(.*?)</tr>', page.text, re.S)
        assert row
        label = {"running": "SYNCING", "failed": "FAILED", "cancelled": "CANCELLED"}.get(
            expected, "N/A"
        )
        if with_metric and expected not in ("running", "cancelled"):
            label = "GREEN"
        if with_metric:
            assert "76%" in row[1]
        assert f">{label}</span>" in row[1]
    finally:
        async with async_session_ctx() as db:
            await db.execute(delete(BackgroundJob).where(BackgroundJob.course_id == course_id))
            await db.execute(
                delete(TeamMetricSnapshot).where(TeamMetricSnapshot.course_id == course_id)
            )
            await db.execute(delete(Course).where(Course.id == course_id))
            await db.commit()
