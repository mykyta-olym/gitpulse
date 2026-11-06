"""The assistant is wired into the rest of GitPulse, not only its own page.

* "Items that need your attention" says what its page says at the top - a
  token GitLab refuses, tools on without a bot - and the actions GitLab
  refused it this week, linking to the Assistant page; students see none.
* "Follow the latest updates" names its actions and links them to the
  Assistant page; students see none of them (the page and the bot are the
  teachers').
* Both are for whoever runs the course - its owner and teachers, an admin -
  not for a teacher who sees it only as a team's mentor: the page they link
  to would refuse them.
* A refused token is written to the audit log once, however many events
  run into it.
* A course's configuration file carries the assistant's tool settings, and
  importing one applies them through the form's own checks - never a token.
"""

from __future__ import annotations

import os
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from sqlalchemy import delete, func, select

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


@pytest.fixture
async def course(monkeypatch: pytest.MonkeyPatch) -> Any:
    os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
    os.environ.setdefault("SECRET_KEY", "test-secret-key-minimum-sixteen-chars")
    os.environ.setdefault("APP_ENV", "test")

    from sqlalchemy import text

    from app.config import get_settings
    from app.db.session import async_session_ctx, dispose_engine, init_engine
    from app.models import Base
    from app.models.assistant import CourseAssistant
    from app.models.course import Course
    from app.models.course_membership import CourseMembership
    from app.models.course_settings import CourseSettings
    from app.models.user import User
    from app.security.token_encryption import encrypt_token

    get_settings.cache_clear()
    settings = get_settings()
    monkeypatch.setattr(settings, "feature_classroom_assistant", True)
    engine = init_engine(str(settings.database_url), pool_size=5, echo=False)
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS pgcrypto"))
        await conn.run_sync(Base.metadata.create_all)
    suffix = uuid.uuid4().hex[:6]
    async with async_session_ctx() as session:
        row = Course(code=f"D{suffix}", name="Dashboard", academic_year="2026/2027")
        session.add(row)
        await session.flush()
        session.add(CourseSettings(course_id=row.id))
        teacher = User(username=_teacher(row.id), password_hash="!", role="teacher")
        mentor = User(username=_mentor(row.id), password_hash="!", role="teacher")
        session.add_all([teacher, mentor])
        await session.flush()
        session.add(CourseMembership(user_id=teacher.id, course_id=row.id, role="teacher"))
        session.add(
            CourseAssistant(
                course_id=row.id,
                bot_token=encrypt_token("bot-token", settings.secret_key),
                bot_user_id=4242,
                bot_username="group_bot",
                push_review_enabled=True,
            )
        )
        await session.commit()
        course_id = row.id
    try:
        yield course_id
    finally:
        from app.models.audit_log import AuditLog

        async with async_session_ctx() as session:
            await session.execute(delete(AuditLog).where(AuditLog.entity_id == course_id))
            await session.execute(delete(Course).where(Course.id == course_id))
            await session.execute(
                delete(User).where(User.username.in_([_teacher(course_id), _mentor(course_id)]))
            )
            await session.commit()
        await dispose_engine()


def _teacher(course_id: uuid.UUID) -> str:
    """A teacher of the course (a CourseMembership with the role teacher)."""
    return f"teacher-{course_id.hex[:12]}"


def _mentor(course_id: uuid.UUID) -> str:
    """A teacher with no course role here - one who sees it as a team's mentor."""
    return f"mentor-{course_id.hex[:12]}"


async def _attention(
    course_id: uuid.UUID, role: str, user: str | None = None
) -> list[dict[str, Any]]:
    from app.api.dashboard.home.attention import _build_attention_items
    from app.db.session import async_session_ctx
    from app.models.course import Course

    async with async_session_ctx() as session:
        course = await session.get(Course, course_id)
        return await _build_attention_items(
            role,
            [course_id],
            {},
            session,
            {"user": user or _teacher(course_id), "role": role},
            "en",
            active_courses=[course],
        )


async def _assistant_items(
    course_id: uuid.UUID, role: str, user: str | None = None
) -> list[dict[str, Any]]:
    items = await _attention(course_id, role, user)
    return [i for i in items if i["title"].startswith("Assistant:")]


async def test_a_refused_token_and_refused_actions_need_attention(course: Any) -> None:
    from app.db.session import async_session_ctx
    from app.models.assistant import AssistantTask, CourseAssistant
    from app.models.project import GitLabProject
    from app.models.team import Team
    from app.services.assistant import account

    async with async_session_ctx() as session:
        assistant = await account.assistant_for(session, course)
        assert assistant is not None
        await account.mark_token_rejected(session, assistant.id, assistant.bot_token)
        await account.mark_token_rejected(session, assistant.id, assistant.bot_token)
        team = Team(course_id=course, name="Team")
        session.add(team)
        await session.flush()
        project = GitLabProject(
            team_id=team.id,
            gitlab_project_id=860_000_000 + uuid.uuid4().int % 1_000_000,
            gitlab_project_path=f"kurz/{uuid.uuid4().hex[:6]}",
        )
        session.add(project)
        await session.flush()
        session.add(
            AssistantTask(
                course_id=course,
                project_id=project.id,
                tool="push_review",
                key="sha",
                state="failed",
                detail={},
                history=[],
            )
        )
        await session.commit()
        stored = await session.get(CourseAssistant, assistant.id)
        assert stored is not None
        assert account.problems(stored) == ["token_rejected"]

    items = await _assistant_items(course, "teacher")
    titles = [i["title"] for i in items]
    assert titles == [
        "Assistant: GitLab refuses the bot token",
        "Assistant: GitLab refused some of its actions",
    ]
    assert items[0]["severity"] == "danger"
    assert all(i["url"] == f"/dashboard/courses/{course}/assistant" for i in items)
    assert "In the last 7 days: 1." in items[1]["detail"]
    assert await _assistant_items(course, "student") == []
    assert await _assistant_items(course, "teacher", _mentor(course)) == []
    assert len(await _assistant_items(course, "admin", "nobody")) == 2


async def test_a_refused_token_is_written_to_the_feed_once(course: Any) -> None:
    from app.api.dashboard.home.activity import _assistant_rows_for_staff, _audit_entries
    from app.db.session import async_session_ctx
    from app.models.audit_log import AuditLog
    from app.services.assistant import account

    async with async_session_ctx() as session:
        assistant = await account.assistant_for(session, course)
        assert assistant is not None
        for _ in range(3):
            await account.mark_token_rejected(session, assistant.id, assistant.bot_token)
        await account.save_tools(session, assistant, account.tools_of(assistant), actor="teacher")
        refused = await session.scalar(
            select(func.count())
            .select_from(AuditLog)
            .where(AuditLog.entity_id == course, AuditLog.action == "assistant.token_rejected")
        )
        assert refused == 1

        cutoff = datetime.now(UTC) - timedelta(hours=1)
        teacher = await _audit_entries("teacher", [course], session, lambda s: s, cutoff)
        mine = {e["_action"]: e for e in teacher if e["_entity_id"] == str(course)}
        assert (
            mine["assistant.token_rejected"]["action"] == "GitLab refused the assistant's bot token"
        )
        assert mine["assistant.token_rejected"]["detail"] == "@group_bot"
        assert mine["assistant.tools_saved"]["action"] == "Assistant tools updated"
        for entry in mine.values():
            assert entry["url"] == f"/dashboard/courses/{course}/assistant"
            assert entry["icon"] != "activity", "every assistant action has its own icon"

        student = await _audit_entries("student", [course], session, lambda s: s, cutoff)
        assert not [e for e in student if str(e["_action"]).startswith("assistant.")]

        def others(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
            return [e for e in entries if not str(e["_action"]).startswith("assistant.")]

        for user, role, sees in (
            (_teacher(course), "teacher", True),
            ("nobody", "admin", True),
            (_mentor(course), "teacher", False),
        ):
            kept = await _assistant_rows_for_staff(
                teacher, [course], session, {"user": user, "role": role}
            )
            assert kept == (teacher if sees else others(teacher)), user


async def test_tools_on_without_a_bot_need_attention(course: Any) -> None:
    from app.db.session import async_session_ctx
    from app.services.assistant import account

    async with async_session_ctx() as session:
        assistant = await account.assistant_for(session, course)
        assert assistant is not None
        await account.disconnect(session, assistant, actor="teacher")
    items = await _assistant_items(course, "teacher")
    assert [i["title"] for i in items] == ["Assistant: no bot is connected"]


async def test_the_configuration_file_carries_the_tools_never_the_token(course: Any) -> None:
    from app.api.dashboard.courses.settings_config import apply_config_sections
    from app.db.session import async_session_ctx
    from app.models.course import Course
    from app.services.assistant import account

    async with async_session_ctx() as session:
        exported = account.tools_config(await account.assistant_for(session, course))
        assert exported["push_review_enabled"] is True
        assert not {"bot_token", "bot_username", "bot_user_id"} & set(exported)

        row = await session.get(Course, course)
        assert row is not None
        errors: list[str] = []
        applied: list[str] = []
        config = {"assistant": {"conflict_enabled": True, "conflict_file_path": "docs/zadanie.md"}}
        await apply_config_sections(session, row.settings, course, config, errors, applied)
        await session.commit()
        assert applied == ["assistant"], errors
        assistant = await account.assistant_for(session, course)
        assert assistant is not None
        assert assistant.conflict_file_path == "docs/zadanie.md"
        assert assistant.push_review_enabled is True, "a field the file leaves out stays"
        assert assistant.bot_username == "group_bot", "the bot stays with the course"

        errors, applied = [], []
        bad = {"assistant": {"min_commit_title_length": "10", "conflict_file_path": "../x"}}
        await apply_config_sections(session, row.settings, course, bad, errors, applied)
        assert applied == []
        assert errors == ["assistant: invalid min_commit_title_length - not applied"]
        await session.refresh(assistant)
        assert assistant.conflict_file_path == "docs/zadanie.md"
