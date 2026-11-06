"""The classroom assistant, each exercise from the first event to the last.

Real PostgreSQL (the advisory locks, the task rows, the joins that find a
project's course and assistant), real webhook payload shapes, and a GitLab
kept in memory - commits with parents, branches, merge requests, issues - so
"is the colleague's commit in the branch yet" is answered by history, as git
answers it.

* push review: a push to main gets one comment, a redelivered webhook none,
  a clean push to an existing branch none, the teacher and the bot none;
* merge conflict: the colleague's commit lands on main only once the branch
  edits the file, the resolution is checked only once main is merged in, and
  markers left in are pointed out before the clean one is praised;
* issues and merge requests: the exercise prepared (and prepared again without
  doubling), a review that asks for what is missing, an answer to a comment,
  approval and merge, the issue closed from GitLab's merge event - and a
  merge request merged before the review is said to be so.
"""

from __future__ import annotations

import os
import uuid
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select
from starlette.responses import Response

from app.models.assistant import AssistantTask, CourseAssistant
from app.models.course import Course
from app.models.course_settings import CourseSettings
from app.models.project import GitLabProject
from app.models.student import Student
from app.models.team import Team
from app.models.team_member import TeamMember
from app.models.webhook_event import WebhookEvent
from app.services.gitlab.client_types import GitLabAPIError

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]

BOT_ID = 990_001
BASE_README = "# Cvicenie\n\nMeno: ???\nSkupina: ???\nPrikaz: ???\n"


# -- GitLab, in memory ----------------------------------------------------------


class FakeGitLab:
    """One project's repository, merge requests and issues, behind the same
    methods ``BotGitLabClient`` offers."""

    def __init__(self, gitlab_id: int) -> None:
        self.gitlab_id = gitlab_id
        self.commits: dict[str, tuple[list[str], dict[str, str], str]] = {}
        self.branches: dict[str, str] = {}
        self.mrs: dict[int, dict[str, Any]] = {}
        self.issues: dict[int, dict[str, Any]] = {}
        self.mr_notes: list[tuple[int, str]] = []
        self.commit_comments: list[tuple[str, str]] = []
        self.approvals: list[int] = []
        self.refuses_token = False
        self.saw_unauthorized = False
        self._seq = 0

    def _gate(self) -> None:
        """A revoked token: every call answers 401."""
        if self.refuses_token:
            self.saw_unauthorized = True
            raise GitLabAPIError(401, "401 Unauthorized")

    async def token_rejected(self) -> bool:
        return self.saw_unauthorized and self.refuses_token

    # -- the repository, for the test to drive --

    def _sha(self) -> str:
        self._seq += 1
        return f"{self._seq:040x}"

    def write(
        self,
        branch: str,
        files: dict[str, str],
        message: str = "Edit the files",
        parents: list[str] | None = None,
    ) -> str:
        """Commit ``files`` on ``branch`` (a new branch starts from main)."""
        head = self.branches.get(branch) or self.branches.get("main")
        parents = parents if parents is not None else ([head] if head else [])
        tree = dict(self.commits[parents[0]][1]) if parents else {}
        tree.update(files)
        sha = self._sha()
        self.commits[sha] = (parents, tree, message)
        self.branches[branch] = sha
        return sha

    def _resolve(self, ref: str) -> str | None:
        return self.branches.get(ref) or (ref if ref in self.commits else None)

    def _ancestors(self, sha: str) -> list[str]:
        order, queue, seen = [], [sha], set()
        while queue:
            node = queue.pop(0)
            if node in seen:
                continue
            seen.add(node)
            order.append(node)
            queue.extend(self.commits[node][0])
        return order

    # -- the client's methods --

    async def __aenter__(self) -> FakeGitLab:
        return self

    async def __aexit__(self, *args: object) -> None:
        return None

    async def project(self, _pid: int) -> dict[str, Any]:
        return {"id": self.gitlab_id, "default_branch": "main"}

    async def file_text(self, _pid: int, path: str, ref: str) -> str | None:
        sha = self._resolve(ref)
        return self.commits[sha][1].get(path) if sha else None

    async def file_revision(self, _pid: int, path: str, ref: str) -> tuple[str, str] | None:
        sha = self._resolve(ref)
        if not sha or path not in self.commits[sha][1]:
            return None
        return self.commits[sha][1][path], self._last_change(sha, path)

    def _last_change(self, sha: str, path: str) -> str:
        node = sha
        while True:
            parents, tree, _ = self.commits[node]
            if not parents or self.commits[parents[0]][1].get(path) != tree.get(path):
                return node
            node = parents[0]

    async def merge_base(self, _pid: int, first: str, second: str) -> str | None:
        self._gate()
        a, b = self._resolve(first), self._resolve(second)
        if not a or not b:
            return None
        mine = set(self._ancestors(a))
        return next((node for node in self._ancestors(b) if node in mine), None)

    async def is_ancestor(self, pid: int, ancestor: str, descendant: str) -> bool:
        return await self.merge_base(pid, ancestor, descendant) == ancestor

    async def commit(
        self, _pid: int, branch: str, message: str, actions: list[dict[str, Any]]
    ) -> dict[str, Any]:
        head = self.branches[branch]
        for action in actions:
            if action["action"] == "update" and action.get("last_commit_id") != self._last_change(
                head, action["file_path"]
            ):
                raise GitLabAPIError(400, "the file has changed since you started editing it")
        sha = self.write(branch, {a["file_path"]: a["content"] for a in actions}, message)
        return {"id": sha, "web_url": f"https://gitlab.test/-/commit/{sha}"}

    async def comment_on_commit(self, _pid: int, sha: str, note: str) -> dict[str, Any]:
        self._gate()
        self.commit_comments.append((sha, note))
        return {"note": note}

    async def create_issue(
        self, _pid: int, title: str, description: str, assignee_id: int
    ) -> dict[str, Any]:
        iid = len(self.issues) + 1
        self.issues[iid] = {
            "iid": iid,
            "title": title,
            "description": description,
            "assignee_id": assignee_id,
            "state": "opened",
            "web_url": f"https://gitlab.test/-/issues/{iid}",
        }
        return self.issues[iid]

    async def find_issue(self, _pid: int, text: str) -> dict[str, Any] | None:
        return next((i for i in self.issues.values() if text in i["description"]), None)

    async def issue(self, _pid: int, iid: int) -> dict[str, Any] | None:
        return self.issues.get(iid)

    async def close_issue(self, _pid: int, iid: int) -> dict[str, Any]:
        self.issues[iid]["state"] = "closed"
        return self.issues[iid]

    def open_mr(self, author_id: int, branch: str, description: str) -> dict[str, Any]:
        iid = len(self.mrs) + 1
        self.mrs[iid] = {
            "iid": iid,
            "author": {"id": author_id},
            "author_id": author_id,
            "source_branch": branch,
            "target_branch": "main",
            "description": description,
            "state": "opened",
            "draft": False,
            "has_conflicts": False,
            "blocking_discussions_resolved": True,
            "head_pipeline": None,
        }
        return self.mrs[iid]

    async def merge_request(self, _pid: int, iid: int) -> dict[str, Any] | None:
        self._gate()
        mr = self.mrs.get(iid)
        if mr is None:
            return None
        return {**mr, "sha": self.branches[mr["source_branch"]]}

    async def changed_paths(self, pid: int, iid: int) -> list[str]:
        mr = self.mrs[iid]
        head = self.branches[mr["source_branch"]]
        base = await self.merge_base(pid, "main", head)
        before = self.commits[base][1] if base else {}
        after = self.commits[head][1]
        return sorted(p for p in set(before) | set(after) if before.get(p) != after.get(p))

    async def open_merge_request_for(self, _pid: int, branch: str) -> dict[str, Any] | None:
        return next(
            (
                m
                for m in self.mrs.values()
                if m["source_branch"] == branch and m["state"] == "opened"
            ),
            None,
        )

    async def comment_on_merge_request(self, _pid: int, iid: int, body: str) -> dict[str, Any]:
        self.mr_notes.append((iid, body))
        # GitLab's note ids grow across the instance, students' notes included.
        return {"id": 1000 + len(self.mr_notes)}

    async def approve(self, _pid: int, iid: int, _sha: str) -> dict[str, Any]:
        if iid in self.approvals:
            raise GitLabAPIError(401, "401 Unauthorized")
        self.approvals.append(iid)
        return {}

    async def merge(self, _pid: int, iid: int, sha: str, *, when_pipeline: bool) -> dict[str, Any]:
        mr = self.mrs[iid]
        head = self.branches[mr["source_branch"]]
        assert sha == head, "the bot merges what it reviewed"
        self.merge_in_gitlab(iid)
        return {**mr, "state": "merged"}

    def merge_in_gitlab(self, iid: int) -> str:
        """GitLab's merge: a merge commit on main, the merge request merged."""
        mr = self.mrs[iid]
        head = self.branches[mr["source_branch"]]
        tree = self.commits[head][1]
        sha = self.write("main", tree, "Merge", parents=[self.branches["main"], head])
        mr["state"] = "merged"
        mr["merge_commit_sha"] = sha
        return sha

    async def merge_requests_of_commit(self, _pid: int, sha: str) -> list[dict[str, Any]]:
        return [
            m
            for m in self.mrs.values()
            if sha in (m.get("merge_commit_sha"), self.branches.get(m["source_branch"]))
        ]


# -- The course ----------------------------------------------------------------


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
    engine = init_engine(str(settings.database_url), pool_size=5, echo=False)
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS pgcrypto"))
        await conn.run_sync(Base.metadata.create_all)
    application = create_app()
    try:
        yield application
    finally:
        await dispose_engine()


class SeededCourse:
    """The ids of one seeded course."""

    course_id: uuid.UUID
    project_id: uuid.UUID
    gitlab_id: int
    jana: Student
    peter: Student
    teacher: Student


@pytest.fixture
async def course(app: Any, monkeypatch: pytest.MonkeyPatch) -> Any:
    from app.config import get_settings
    from app.db.session import async_session_ctx
    from app.security.token_encryption import encrypt_token

    settings = get_settings()
    monkeypatch.setattr(settings, "feature_classroom_assistant", True)
    seeded = SeededCourse()
    seeded.gitlab_id = 880_000_000 + uuid.uuid4().int % 1_000_000
    suffix = uuid.uuid4().hex[:8]
    async with async_session_ctx() as session:
        row = Course(code=f"A{suffix[:6]}", name="Assistant", academic_year="2025/2026")
        session.add(row)
        await session.flush()
        session.add(CourseSettings(course_id=row.id))
        team = Team(course_id=row.id, name=f"Team {suffix}")
        session.add(team)
        await session.flush()
        project = GitLabProject(
            team_id=team.id,
            gitlab_project_id=seeded.gitlab_id,
            gitlab_project_path=f"zsi/{suffix}",
            default_branch="main",
        )
        session.add(project)
        people = []
        for n, (name, is_teacher) in enumerate(
            (("jana", False), ("peter", False), ("teacher", True)), start=1
        ):
            student = Student(
                gitlab_user_id=seeded.gitlab_id + n, gitlab_username=f"{name}-{suffix}"
            )
            session.add(student)
            await session.flush()
            session.add(TeamMember(team_id=team.id, student_id=student.id, is_teacher=is_teacher))
            people.append(student)
        session.add(
            CourseAssistant(
                course_id=row.id,
                bot_token=encrypt_token("bot-token", settings.secret_key),
                bot_user_id=BOT_ID,
                bot_username="group_bot",
                push_review_enabled=True,
                conflict_enabled=True,
                mr_review_enabled=True,
            )
        )
        await session.commit()
        seeded.course_id, seeded.project_id = row.id, project.id
        seeded.jana, seeded.peter, seeded.teacher = people
    try:
        yield seeded
    finally:
        async with async_session_ctx() as session:
            await session.execute(delete(Course).where(Course.id == seeded.course_id))
            await session.execute(delete(Student).where(Student.id.in_([p.id for p in people])))
            await session.commit()


@pytest.fixture
def gitlab(course: Any, monkeypatch: pytest.MonkeyPatch) -> FakeGitLab:
    from app.services.assistant import events

    fake = FakeGitLab(course.gitlab_id)
    fake.write("main", {"README.md": BASE_README, "app.py": "print('hi')\n"}, "Initial commit")
    monkeypatch.setattr(events, "BotGitLabClient", lambda *_a, **_k: fake)
    return fake


async def _deliver(kind: str, gitlab_id: int, payload: dict[str, Any]) -> None:
    """Hand an event to the assistant as its job does: a session of its own."""
    from app.db.session import async_session_ctx
    from app.services.assistant import events

    event = WebhookEvent(
        gitlab_object_kind=kind,
        payload={"project": {"id": gitlab_id, "default_branch": "main"}, **payload},
        gitlab_project_id=gitlab_id,
    )
    async with async_session_ctx() as session:
        await events.handle(session, event)


def _push(gitlab: FakeGitLab, who: Student, branch: str, before: str, title: str) -> dict[str, Any]:
    after = gitlab.branches[branch]
    return {
        "ref": f"refs/heads/{branch}",
        "before": before,
        "after": after,
        "user_id": who.gitlab_user_id,
        "user_username": who.gitlab_username,
        "commits": [{"id": after, "title": title}],
    }


async def _tasks(course: Any, tool: str) -> list[AssistantTask]:
    from app.db.session import async_session_ctx

    async with async_session_ctx() as session:
        stmt = select(AssistantTask).where(
            AssistantTask.course_id == course.course_id, AssistantTask.tool == tool
        )
        return list((await session.execute(stmt)).scalars())


ZERO = "0" * 40


# -- Push review ---------------------------------------------------------------


async def test_a_push_review_comments_once_and_only_on_a_students_push(
    course: Any, gitlab: FakeGitLab
) -> None:
    before = gitlab.branches["main"]
    gitlab.write("main", {"app.py": "print('x')\n"}, "Update app.py")
    push = _push(gitlab, course.jana, "main", before, "Update app.py")
    await _deliver("push", course.gitlab_id, push)
    await _deliver("push", course.gitlab_id, push)  # GitLab redelivers

    assert len(gitlab.commit_comments) == 1
    sha, body = gitlab.commit_comments[0]
    assert sha == push["after"]
    assert "išiel priamo do `main`" in body
    assert "„Update app.py“" in body
    [task] = await _tasks(course, "push_review")
    assert task.state == "needs_work"
    assert task.history[-1]["action"] == "commented"

    gitlab.write("feature", {"app.py": "print('y')\n"}, "Print a friendlier greeting")
    await _deliver(
        "push",
        course.gitlab_id,
        _push(gitlab, course.jana, "feature", ZERO, "Print a friendlier greeting"),
    )
    assert "Dobrý začiatok" in gitlab.commit_comments[-1][1]

    before = gitlab.branches["feature"]
    gitlab.write("feature", {"app.py": "print('z')\n"}, "Greet in Slovak as well")
    await _deliver(
        "push",
        course.gitlab_id,
        _push(gitlab, course.jana, "feature", before, "Greet in Slovak as well"),
    )
    gitlab.write("main", {"app.py": "print('t')\n"}, "Update app.py")
    await _deliver(
        "push", course.gitlab_id, _push(gitlab, course.teacher, "main", ZERO, "Update app.py")
    )
    await _deliver(
        "push",
        course.gitlab_id,
        {**_push(gitlab, course.jana, "main", ZERO, "Update app.py"), "user_id": BOT_ID},
    )
    assert len(gitlab.commit_comments) == 2, "a clean push, the teacher and the bot get nothing"
    assert len(await _tasks(course, "push_review")) == 2


# -- Merge conflict ---------------------------------------------------------------


async def test_the_conflict_is_planted_then_its_resolution_is_checked(
    course: Any, gitlab: FakeGitLab
) -> None:
    gitlab.write("work", {"app.py": "print('mine')\n"}, "Change the greeting")
    await _deliver(
        "push", course.gitlab_id, _push(gitlab, course.jana, "work", ZERO, "Change the greeting")
    )
    [task] = await _tasks(course, "conflict")
    assert task.state == "waiting"
    assert task.detail["waiting_for"] == "edit"
    main_before = gitlab.branches["main"]

    edited = BASE_README.replace("Meno: ???", "Meno: Jana Nova")
    before = gitlab.branches["work"]
    gitlab.write("work", {"README.md": edited}, "Fill in my name")
    await _deliver(
        "push", course.gitlab_id, _push(gitlab, course.jana, "work", before, "Fill in my name")
    )

    [task] = await _tasks(course, "conflict")
    assert task.state == "planted"
    assert gitlab.branches["main"] != main_before
    planted = gitlab.commits[gitlab.branches["main"]][1]["README.md"]
    control = task.detail["control_line"]
    assert control in planted
    assert "Meno: ???" not in planted, "the student's line is the target"
    assert task.detail["own_lines"] == ["Meno: Jana Nova"]
    assert gitlab.commits[task.commit_sha][2].startswith("Úprava súboru README.md")

    # Pushing on without merging main in: nothing to check yet.
    before = gitlab.branches["work"]
    gitlab.write("work", {"app.py": "print('more')\n"}, "Say more")
    await _deliver("push", course.gitlab_id, _push(gitlab, course.jana, "work", before, "Say more"))
    about_the_conflict = [b for _, b in gitlab.commit_comments if "konflikt" in b.lower()]
    assert about_the_conflict == []
    assert gitlab.mr_notes == []

    # Merged main in, markers left: the merge request hears about it.
    gitlab.open_mr(course.jana.gitlab_user_id, "work", "Closes #1")
    markers = f"<<<<<<< HEAD\nMeno: Jana Nova\n=======\n{control}\n>>>>>>> main\n"
    before = gitlab.branches["work"]
    gitlab.write(
        "work",
        {"README.md": BASE_README.replace("Meno: ???\n", markers)},
        "Merge branch 'main' into work",
        parents=[before, gitlab.branches["main"]],
    )
    await _deliver(
        "push",
        course.gitlab_id,
        _push(gitlab, course.jana, "work", before, "Merge branch 'main' into work"),
    )
    [task] = await _tasks(course, "conflict")
    assert task.state == "needs_work"
    iid, body = gitlab.mr_notes[-1]
    assert iid == 1
    assert "značky konfliktu" in body

    # Both lines kept, no markers: praised, and done.
    before = gitlab.branches["work"]
    resolved = BASE_README.replace("Meno: ???\n", f"Meno: Jana Nova\n{control}\n")
    gitlab.write("work", {"README.md": resolved}, "Resolve the conflict in README.md")
    await _deliver(
        "push",
        course.gitlab_id,
        _push(gitlab, course.jana, "work", before, "Resolve the conflict in README.md"),
    )
    [task] = await _tasks(course, "conflict")
    assert task.state == "passed"
    assert "je vyriešený" in gitlab.mr_notes[-1][1]
    notes = len(gitlab.mr_notes)
    await _deliver(
        "push",
        course.gitlab_id,
        _push(gitlab, course.jana, "work", before, "Resolve the conflict in README.md"),
    )
    assert len(gitlab.mr_notes) == notes, "a finished exercise is left alone"


# -- Issues and merge requests -------------------------------------------------------


async def _let_the_bot_merge(course: Any) -> None:
    from sqlalchemy import update

    from app.db.session import async_session_ctx

    async with async_session_ctx() as session:
        await session.execute(
            update(CourseAssistant)
            .where(CourseAssistant.course_id == course.course_id)
            .values(mr_bot_merges=True)
        )
        await session.commit()


async def _prepare(course: Any, gitlab: FakeGitLab) -> None:
    from app.db.session import async_session_ctx
    from app.services.assistant import exercise

    async with async_session_ctx() as session:
        row = await session.get(Course, course.course_id)
        assistant = (
            await session.execute(
                select(CourseAssistant).where(CourseAssistant.course_id == course.course_id)
            )
        ).scalar_one()
        project = await session.get(GitLabProject, course.project_id)
        assert row is not None
        assert project is not None
        await exercise.prepare(
            session, row, assistant, gitlab, [project], actor="teacher", gitlab_url="https://g"
        )


def _mr_event(gitlab: FakeGitLab, iid: int, action: str, who: int) -> dict[str, Any]:
    mr = gitlab.mrs[iid]
    return {
        "user": {"id": who},
        "object_attributes": {
            "iid": iid,
            "action": action,
            "description": mr["description"],
            "source_branch": mr["source_branch"],
            "author_id": mr["author_id"],
        },
    }


async def test_the_issue_exercise_runs_from_the_issue_to_the_merge(
    course: Any, gitlab: FakeGitLab
) -> None:
    await _let_the_bot_merge(course)
    await _prepare(course, gitlab)
    await _prepare(course, gitlab)  # again: nothing doubles

    assert len(gitlab.issues) == 2, "one issue per student, the teacher left out"
    tasks = {t.student_id: t for t in await _tasks(course, "mr_review")}
    jana_task = tasks[course.jana.id]
    assert jana_task.state == "assigned"
    path = jana_task.file_path
    assert path == f"ulohy/{course.jana.gitlab_username}.txt"
    assert "???" in gitlab.commits[gitlab.branches["main"]][1][path]
    issue = gitlab.issues[jana_task.issue_iid]
    assert issue["assignee_id"] == course.jana.gitlab_user_id
    assert issue["title"] == f"Doplň súbor {path}"

    # A first try: the issue not linked, a placeholder left.
    half = gitlab.commits[gitlab.branches["main"]][1][path].replace("???", "Jana Nova", 1)
    gitlab.write("jana-task", {path: half}, "Fill in my name")
    gitlab.open_mr(course.jana.gitlab_user_id, "jana-task", "Moja praca")
    event = _mr_event(gitlab, 1, "open", course.jana.gitlab_user_id)
    await _deliver("merge_request", course.gitlab_id, event)
    assert len(gitlab.mr_notes) == 1
    body = gitlab.mr_notes[0][1]
    assert f"`Closes #{jana_task.issue_iid}`" in body
    assert "ostalo `???`" in body

    await _deliver(
        "merge_request",
        course.gitlab_id,
        {**event, "object_attributes": {**event["object_attributes"], "action": "update"}},
    )
    assert len(gitlab.mr_notes) == 1, "nothing new, nothing said"

    await _deliver(
        "note",
        course.gitlab_id,
        {
            "user": {"id": course.jana.gitlab_user_id, "username": course.jana.gitlab_username},
            "object_attributes": {"noteable_type": "MergeRequest", "system": False},
            "merge_request": event["object_attributes"],
        },
    )
    assert len(gitlab.mr_notes) == 2, "a student's comment is answered"

    # Fixed: approved and merged; the merge event closes the issue.
    full = half.replace("???", "git rebase")
    gitlab.write("jana-task", {path: full}, "Name my favourite Git command")
    gitlab.mrs[1]["description"] = f"Doplnene.\n\nCloses #{jana_task.issue_iid}"
    await _deliver(
        "merge_request",
        course.gitlab_id,
        _mr_event(gitlab, 1, "update", course.jana.gitlab_user_id),
    )
    assert gitlab.approvals == [1]
    assert gitlab.mrs[1]["state"] == "merged"
    [task] = [t for t in await _tasks(course, "mr_review") if t.student_id == course.jana.id]
    assert task.state == "approved"

    await _deliver("merge_request", course.gitlab_id, _mr_event(gitlab, 1, "merge", BOT_ID))
    [task] = [t for t in await _tasks(course, "mr_review") if t.student_id == course.jana.id]
    assert task.state == "passed"
    assert gitlab.issues[task.issue_iid]["state"] == "closed"
    assert "Výborná práca" in gitlab.mr_notes[-1][1]
    assert [h["action"] for h in task.history][-3:] == ["approved", "closed_issue", "merged"]

    await _deliver("merge_request", course.gitlab_id, _mr_event(gitlab, 1, "merge", BOT_ID))
    praise = [body for _, body in gitlab.mr_notes if "Výborná práca" in body]
    assert len(praise) == 1, "the merge is finished once"


async def test_by_default_the_student_merges_after_the_approval(
    course: Any, gitlab: FakeGitLab
) -> None:
    await _prepare(course, gitlab)
    task = next(t for t in await _tasks(course, "mr_review") if t.student_id == course.jana.id)
    path = task.file_path
    done = gitlab.commits[gitlab.branches["main"]][1][path].replace("???", "Jana")
    gitlab.write("jana-task", {path: done}, "Fill in my file")
    gitlab.open_mr(course.jana.gitlab_user_id, "jana-task", f"Closes #{task.issue_iid}")
    await _deliver(
        "merge_request", course.gitlab_id, _mr_event(gitlab, 1, "open", course.jana.gitlab_user_id)
    )
    assert gitlab.approvals == [1]
    assert gitlab.mrs[1]["state"] == "opened", "the student merges, not the bot"
    assert "Teraz merge request zlúč" in gitlab.mr_notes[-1][1]
    task = next(t for t in await _tasks(course, "mr_review") if t.student_id == course.jana.id)
    assert task.state == "approved"

    # GitLab pushes the merge to main as the student who clicked Merge.
    main_before = gitlab.branches["main"]
    merge_sha = gitlab.merge_in_gitlab(1)
    merge_push = {
        **_push(gitlab, course.jana, "main", main_before, "Merge branch 'jana-task' into 'main'"),
        "after": merge_sha,
    }
    merge_push["commits"].insert(0, {"id": gitlab.branches["jana-task"], "title": "Update app.py"})
    await _deliver("push", course.gitlab_id, merge_push)
    assert gitlab.commit_comments == [], "merging the merge request is not a direct push"
    await _deliver(
        "merge_request",
        course.gitlab_id,
        _mr_event(gitlab, 1, "merge", course.jana.gitlab_user_id),
    )
    task = next(t for t in await _tasks(course, "mr_review") if t.student_id == course.jana.id)
    assert task.state == "passed"
    assert gitlab.issues[task.issue_iid]["state"] == "closed"
    assert "Výborná práca" in gitlab.mr_notes[-1][1]


async def test_a_member_excluded_from_scoring_is_left_alone(
    course: Any, gitlab: FakeGitLab
) -> None:
    """The teacher excluded Peter from scoring (a mentor with access, say):
    the course does not count him as a student, so neither does the assistant."""
    from sqlalchemy import update

    from app.db.session import async_session_ctx

    async with async_session_ctx() as session:
        await session.execute(
            update(TeamMember)
            .where(TeamMember.student_id == course.peter.id)
            .values(excluded_from_scoring=True)
        )
        await session.commit()
    await _prepare(course, gitlab)
    assert [i["assignee_id"] for i in gitlab.issues.values()] == [course.jana.gitlab_user_id]

    before = gitlab.branches["main"]
    gitlab.write("main", {"app.py": "print(7)\n"}, "fix")
    await _deliver("push", course.gitlab_id, _push(gitlab, course.peter, "main", before, "fix"))
    assert gitlab.commit_comments == []


async def test_a_comment_the_review_already_answered_is_not_answered_twice(
    course: Any, gitlab: FakeGitLab
) -> None:
    """On a real GitLab the review of an edit and the student's comment came
    in close together and both said "approved": the comment was older than
    the review's reply, so the reply had answered it already."""
    await _prepare(course, gitlab)
    task = next(t for t in await _tasks(course, "mr_review") if t.student_id == course.jana.id)
    gitlab.write("jana-y", {task.file_path: "Meno: Jana\n"}, "Fill in my file")
    gitlab.open_mr(course.jana.gitlab_user_id, "jana-y", "Hotovo.")
    event = _mr_event(gitlab, 1, "open", course.jana.gitlab_user_id)
    await _deliver("merge_request", course.gitlab_id, event)
    assert len(gitlab.mr_notes) == 1

    def comment(note_id: int) -> dict[str, Any]:
        return {
            "user": {"id": course.jana.gitlab_user_id, "username": course.jana.gitlab_username},
            "object_attributes": {"id": note_id, "noteable_type": "MergeRequest", "system": False},
            "merge_request": event["object_attributes"],
        }

    await _deliver("note", course.gitlab_id, comment(1000))  # written before the reply
    assert len(gitlab.mr_notes) == 1
    await _deliver("note", course.gitlab_id, comment(1002))  # written after it
    assert len(gitlab.mr_notes) == 2


async def test_someone_elses_issue_and_a_merge_before_the_review(
    course: Any, gitlab: FakeGitLab
) -> None:
    await _prepare(course, gitlab)
    tasks = {t.student_id: t for t in await _tasks(course, "mr_review")}
    jana_issue = tasks[course.jana.id].issue_iid
    peter_path = tasks[course.peter.id].file_path

    gitlab.write("peter-x", {peter_path: "Meno: Peter\nPrikaz: ???\n"}, "Fill in Peter's file")
    gitlab.open_mr(course.peter.gitlab_user_id, "peter-x", f"Closes #{jana_issue}")
    event = _mr_event(gitlab, 1, "open", course.peter.gitlab_user_id)
    await _deliver("merge_request", course.gitlab_id, event)
    await _deliver(
        "merge_request",
        course.gitlab_id,
        {**event, "object_attributes": {**event["object_attributes"], "action": "update"}},
    )
    told = [body for _, body in gitlab.mr_notes if "je pridelený" in body]
    assert len(told) == 1, "the other student is told once whose issue it is"

    # Peter's own merge request, merged by a person before the review approved it.
    gitlab.mrs[1]["description"] = f"Closes #{tasks[course.peter.id].issue_iid}"
    await _deliver(
        "merge_request",
        course.gitlab_id,
        _mr_event(gitlab, 1, "update", course.peter.gitlab_user_id),
    )
    peter = next(t for t in await _tasks(course, "mr_review") if t.student_id == course.peter.id)
    assert peter.state == "needs_work"
    assert peter.mr_iid == 1
    await _deliver(
        "merge_request",
        course.gitlab_id,
        _mr_event(gitlab, 1, "merge", course.teacher.gitlab_user_id),
    )
    peter = next(t for t in await _tasks(course, "mr_review") if t.student_id == course.peter.id)
    assert peter.state == "merged_unreviewed"
    assert "zlúčený skôr" in gitlab.mr_notes[-1][1]


# -- What the pipeline asks, and the page ----------------------------------------------


async def test_the_pipeline_wants_the_event_only_while_the_bot_is_connected(
    course: Any,
) -> None:
    from app.db.session import async_session_ctx
    from app.services.assistant import account, events

    async with async_session_ctx() as session:
        assert await events.wants(session, course.gitlab_id, "push") is True
        assert await events.wants(session, course.gitlab_id, "pipeline") is False
        assistant = await account.assistant_for(session, course.course_id)
        assert assistant is not None
        await account.disconnect(session, assistant, actor="teacher")
        assert await events.wants(session, course.gitlab_id, "push") is False


def _admin(app: Any) -> AsyncClient:
    from app.config import get_settings
    from app.security.csrf import generate_csrf_token
    from app.security.session_auth import SESSION_COOKIE_NAME, create_session_cookie

    secret = str(get_settings().secret_key)
    carrier = Response()
    create_session_cookie(
        carrier,
        secret_key=secret,
        user="assistant-probe-admin",
        role="admin",
        user_id=str(uuid.uuid4()),
        gitlab_username="assistant-probe-admin",
        allow_stateless_fallback=True,
    )
    raw = carrier.headers.get("set-cookie", "")
    token = raw.split(f"{SESSION_COOKIE_NAME}=", 1)[-1].split(";", 1)[0]
    return AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        cookies={SESSION_COOKIE_NAME: token},
        headers={
            "User-Agent": "pytest",
            "X-CSRF-Token": generate_csrf_token({"user": "assistant-probe-admin"}, secret),
        },
    )


async def test_the_page_shows_what_the_assistant_did_and_saves_its_tools(
    app: Any, course: Any, gitlab: FakeGitLab
) -> None:
    await _prepare(course, gitlab)
    async with _admin(app) as client:
        page = await client.get(f"/dashboard/courses/{course.course_id}/assistant")
        assert page.status_code == 200
        assert page.text.count('class="assistant-row') == 2
        assert "@group_bot" in page.text

        saved = await client.post(
            f"/dashboard/courses/{course.course_id}/assistant/tools",
            data={
                "push_review_enabled": "true",
                "min_commit_title_length": "15",
                "conflict_file_path": "docs/zadanie.md",
                "exercise_file_template": "ulohy/{username}.md",
            },
            headers={"Accept": "application/json"},
        )
        assert saved.json() == {"ok": True}
        refused = await client.post(
            f"/dashboard/courses/{course.course_id}/assistant/tools",
            data={"conflict_file_path": "../x", "exercise_file_template": "x"},
            headers={"Accept": "application/json"},
        )
        assert refused.status_code == 422

    from app.db.session import async_session_ctx
    from app.services.assistant import account

    async with async_session_ctx() as session:
        assistant = await account.assistant_for(session, course.course_id)
        assert assistant is not None
        assert assistant.conflict_file_path == "docs/zadanie.md"
        assert assistant.mr_review_enabled is False
        assert assistant.min_commit_title_length == 15


# -- The states around the exercises ----------------------------------------------


async def _set(course: Any, **values: Any) -> None:
    from sqlalchemy import update

    from app.db.session import async_session_ctx

    async with async_session_ctx() as session:
        await session.execute(
            update(CourseAssistant)
            .where(CourseAssistant.course_id == course.course_id)
            .values(**values)
        )
        await session.commit()


async def _course_settings(course: Any, **values: Any) -> None:
    from sqlalchemy import update

    from app.db.session import async_session_ctx

    async with async_session_ctx() as session:
        await session.execute(
            update(CourseSettings)
            .where(CourseSettings.course_id == course.course_id)
            .values(**values)
        )
        await session.commit()


async def _assistant_row(course: Any) -> CourseAssistant:
    from app.db.session import async_session_ctx

    async with async_session_ctx() as session:
        stmt = select(CourseAssistant).where(CourseAssistant.course_id == course.course_id)
        return (await session.execute(stmt)).scalar_one()


async def test_a_closed_merge_request_lets_the_next_one_be_reviewed(
    course: Any, gitlab: FakeGitLab
) -> None:
    await _prepare(course, gitlab)
    task = next(t for t in await _tasks(course, "mr_review") if t.student_id == course.jana.id)
    path, jana = task.file_path, course.jana.gitlab_user_id
    gitlab.write("try-1", {path: "Meno: Jana\n"}, "First try at my file")
    gitlab.open_mr(jana, "try-1", "Moja praca")
    await _deliver("merge_request", course.gitlab_id, _mr_event(gitlab, 1, "open", jana))
    gitlab.mrs[1]["state"] = "closed"
    await _deliver("merge_request", course.gitlab_id, _mr_event(gitlab, 1, "close", jana))
    task = next(t for t in await _tasks(course, "mr_review") if t.student_id == course.jana.id)
    assert task.mr_iid is None
    assert task.state == "assigned"
    assert task.history[-1]["action"] == "mr_closed"

    gitlab.write("try-2", {path: "Meno: Jana\n"}, "Second try at my file")
    gitlab.open_mr(jana, "try-2", f"Closes #{task.issue_iid}")
    await _deliver("merge_request", course.gitlab_id, _mr_event(gitlab, 2, "open", jana))
    task = next(t for t in await _tasks(course, "mr_review") if t.student_id == course.jana.id)
    assert task.mr_iid == 2
    assert task.state == "approved"
    assert gitlab.approvals == [2]


async def test_a_token_gitlab_refuses_stops_the_assistant(course: Any, gitlab: FakeGitLab) -> None:
    from app.db.session import async_session_ctx
    from app.services.assistant import events

    gitlab.refuses_token = True
    before = gitlab.branches["main"]
    gitlab.write("main", {"app.py": "print(1)\n"}, "Update app.py")
    await _deliver(
        "push", course.gitlab_id, _push(gitlab, course.jana, "main", before, "Update app.py")
    )
    assistant = await _assistant_row(course)
    assert assistant.token_rejected_at is not None
    [task] = await _tasks(course, "push_review")
    assert task.state == "failed"

    async with async_session_ctx() as session:
        assert await events.wants(session, course.gitlab_id, "push") is False


async def test_an_english_course_is_answered_in_english(course: Any, gitlab: FakeGitLab) -> None:
    await _set(course, comment_language="en")
    before = gitlab.branches["main"]
    gitlab.write("main", {"app.py": "print(2)\n"}, "Update app.py")
    await _deliver(
        "push", course.gitlab_id, _push(gitlab, course.jana, "main", before, "Update app.py")
    )
    body = gitlab.commit_comments[-1][1]
    assert body.startswith("Push to the branch `main`:")
    assert "went straight to `main`" in body


async def test_the_course_branch_rule_is_taught_on_a_new_branch(
    course: Any, gitlab: FakeGitLab
) -> None:
    await _course_settings(
        course,
        enabled_checks=["R02"],
        check_configs={"R02": {"branch_pattern": "^issue-[0-9]+"}},
    )
    gitlab.write("feature", {"app.py": "print(3)\n"}, "Print the third greeting")
    await _deliver(
        "push",
        course.gitlab_id,
        _push(gitlab, course.jana, "feature", ZERO, "Print the third greeting"),
    )
    assert "nezodpovedá pravidlu kurzu `^issue-[0-9]+`" in gitlab.commit_comments[-1][1]
    gitlab.write("issue-3-greeting", {"app.py": "print(4)\n"}, "Print the fourth greeting")
    await _deliver(
        "push",
        course.gitlab_id,
        _push(gitlab, course.jana, "issue-3-greeting", ZERO, "Print the fourth greeting"),
    )
    assert "Dobrý začiatok" in gitlab.commit_comments[-1][1]


async def test_a_branch_created_in_gitlab_waits_for_its_first_commits(
    course: Any, gitlab: FakeGitLab
) -> None:
    """GitLab's "New branch" sends a push of no commits whose head is main's
    (a teacher's) commit: nothing to say yet. The first commits on it are
    the new branch - greeted, and its name judged by the course rule."""
    await _course_settings(
        course,
        enabled_checks=["R02"],
        check_configs={"R02": {"branch_pattern": "^issue-[0-9]+"}},
    )
    gitlab.branches["feature"] = gitlab.branches["main"]
    empty = {**_push(gitlab, course.jana, "feature", ZERO, ""), "commits": []}
    await _deliver("push", course.gitlab_id, empty)
    assert gitlab.commit_comments == []

    before = gitlab.branches["feature"]
    gitlab.write("feature", {"app.py": "print(5)\n"}, "Print the fifth greeting")
    await _deliver(
        "push",
        course.gitlab_id,
        _push(gitlab, course.jana, "feature", before, "Print the fifth greeting"),
    )
    [(sha, body)] = gitlab.commit_comments
    assert sha == gitlab.branches["feature"]
    assert "nezodpovedá pravidlu kurzu `^issue-[0-9]+`" in body

    before = gitlab.branches["feature"]
    gitlab.write("feature", {"app.py": "print(6)\n"}, "Print the sixth greeting")
    await _deliver(
        "push",
        course.gitlab_id,
        _push(gitlab, course.jana, "feature", before, "Print the sixth greeting"),
    )
    assert len(gitlab.commit_comments) == 1, "a later clean push is left alone"


async def test_a_failed_pipeline_holds_the_approval(course: Any, gitlab: FakeGitLab) -> None:
    await _prepare(course, gitlab)
    task = next(t for t in await _tasks(course, "mr_review") if t.student_id == course.jana.id)
    jana = course.jana.gitlab_user_id
    gitlab.write("jana-x", {task.file_path: "Meno: Jana\n"}, "Fill in my file")
    gitlab.open_mr(jana, "jana-x", f"Closes #{task.issue_iid}")
    gitlab.mrs[1]["head_pipeline"] = {"status": "failed"}
    await _deliver("merge_request", course.gitlab_id, _mr_event(gitlab, 1, "open", jana))
    assert gitlab.approvals == []
    assert "Pipeline tohto merge requestu zlyhala" in gitlab.mr_notes[-1][1]


async def test_students_without_a_gitlab_account_are_counted(
    course: Any, gitlab: FakeGitLab
) -> None:
    from app.db.session import async_session_ctx

    async with async_session_ctx() as session:
        project = await session.get(GitLabProject, course.project_id)
        assert project is not None
        ghost = Student(
            gitlab_user_id=-(course.gitlab_id), gitlab_username=f"roster-{course.gitlab_id}"
        )
        session.add(ghost)
        await session.flush()
        session.add(TeamMember(team_id=project.team_id, student_id=ghost.id))
        await session.commit()
        ghost_id = ghost.id
    try:
        await _prepare(course, gitlab)
        run = (await _assistant_row(course)).last_exercise_run
        assert run is not None
        assert run["projects"][0]["unassignable"] == 1
        assert len(gitlab.issues) == 2
    finally:
        async with async_session_ctx() as session:
            await session.execute(delete(TeamMember).where(TeamMember.student_id == ghost_id))
            await session.execute(delete(Student).where(Student.id == ghost_id))
            await session.commit()


async def test_a_transferred_course_keeps_its_tools_but_not_its_bot(course: Any) -> None:
    from app.db.session import async_session_ctx
    from app.services.courses import clone_course

    await _set(course, conflict_file_path="docs/zadanie.md", comment_language="en")
    async with async_session_ctx() as session:
        clone = await clone_course(session, course.course_id, "2030/2031", "summer")
        await session.commit()
        clone_id = clone.id
    try:
        async with async_session_ctx() as session:
            stmt = select(CourseAssistant).where(CourseAssistant.course_id == clone_id)
            carried = (await session.execute(stmt)).scalar_one()
        assert carried.conflict_file_path == "docs/zadanie.md"
        assert carried.comment_language == "en"
        assert carried.push_review_enabled is True
        assert carried.bot_token is None
        assert carried.bot_user_id is None
    finally:
        async with async_session_ctx() as session:
            await session.execute(delete(Course).where(Course.id == clone_id))
            await session.commit()
