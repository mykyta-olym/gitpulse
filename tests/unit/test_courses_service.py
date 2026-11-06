"""Unit tests for course_service - clone, archive, activate logic.

Uses mocked AsyncSession to test DB interaction patterns without a real database.
"""

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.services.courses import (
    activate_course,
    archive_course,
    clone_course,
    ensure_course_active,
)


def _uuid() -> uuid.UUID:
    return uuid.uuid4()


# -- Stub models --


@dataclass
class StubCourseSettings:
    branch_pattern: str = "issue-{iid}-*"
    mr_template_required_sections: list[str] = field(default_factory=lambda: ["Description"])
    min_reviews_per_mr: int = 2
    min_review_word_count: int = 10
    min_distinct_mrs_reviewed: int = 2
    weight_issue_ownership: float = 1.0
    weight_branch_naming: float = 1.0
    weight_mr_issue_link: float = 1.0
    weight_mr_template: float = 1.0
    weight_test_changes: float = 1.0
    weight_review_count: float = 1.0
    weight_review_duty: float = 1.0
    weight_response_complete: float = 1.0
    weight_approvals: float = 1.0
    weight_merge_by_author: float = 1.0
    weight_closure: float = 1.0
    weight_pipeline_health: float = 1.0
    weight_commit_quality: float = 0.0
    green_threshold: float = 0.8
    yellow_threshold: float = 0.5
    test_file_patterns: list[str] = field(default_factory=lambda: ["**/test_*"])
    enabled_checks: list[str] = field(default_factory=list)
    weekly_deadlines: list[dict[str, Any]] = field(default_factory=list)
    mr_creation_deadline: datetime | None = None
    merge_deadline: datetime | None = None
    semester_start_date: datetime | None = None
    semester_end_date: datetime | None = None
    skip_auto_archive: bool = False
    check_configs: dict[str, Any] = field(default_factory=dict)
    gitlab_group_path: str | None = None


@dataclass
class StubCourse:
    id: uuid.UUID = field(default_factory=_uuid)
    code: str = "DEVOPS101"
    name: str = "DevOps Intro"
    description: str = "A course"
    academic_year: str = "2024/2025"
    semester: str = "winter"
    is_active: bool = True
    cloned_from_id: uuid.UUID | None = None
    archived_at: datetime | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    teacher_usernames: list[str] = field(
        default_factory=lambda: ["teacher1"]
    )  # kept for import param compat
    settings: StubCourseSettings | None = None


# -- Tests --


class TestArchiveCourse:
    @pytest.mark.asyncio
    async def test_archive_not_found(self) -> None:
        db = AsyncMock()
        db.get = AsyncMock(return_value=None)
        with pytest.raises(HTTPException) as exc_info:
            await archive_course(db, _uuid())
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_archive_sets_inactive(self) -> None:
        course = StubCourse()
        db = AsyncMock()
        db.get = AsyncMock(return_value=course)
        db.execute = AsyncMock(
            return_value=MagicMock(
                scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))
            )
        )
        db.flush = AsyncMock()
        db.rollback = AsyncMock()

        with (
            patch(
                "app.services.courses._cancel_course_jobs",
                new_callable=AsyncMock,
                return_value=0,
            ),
            patch(
                "app.services.courses._deactivate_course_webhooks",
                new_callable=AsyncMock,
                return_value=0,
            ),
        ):
            result = await archive_course(db, course.id)

        assert result.is_active is False
        assert result.archived_at is not None

    @pytest.mark.asyncio
    async def test_archive_deactivates_webhook_configurations(self) -> None:
        """archive_course must call _deactivate_course_webhooks."""
        course = StubCourse()
        db = AsyncMock()
        db.get = AsyncMock(return_value=course)
        db.execute = AsyncMock(
            return_value=MagicMock(
                scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))
            )
        )
        db.flush = AsyncMock()
        db.rollback = AsyncMock()

        with (
            patch(
                "app.services.courses._cancel_course_jobs",
                new_callable=AsyncMock,
                return_value=0,
            ),
            patch(
                "app.services.courses._deactivate_course_webhooks",
                new_callable=AsyncMock,
                return_value=3,
            ) as mock_deactivate,
        ):
            await archive_course(db, course.id)

        mock_deactivate.assert_awaited_once_with(db, course.id)

    @pytest.mark.asyncio
    async def test_archive_lock_timeout_raises_409(self) -> None:
        from sqlalchemy.exc import OperationalError

        course = StubCourse()
        db = AsyncMock()
        db.get = AsyncMock(return_value=course)
        db.execute = AsyncMock(side_effect=OperationalError("lock timeout", {}, Exception()))
        db.rollback = AsyncMock()

        with pytest.raises(HTTPException) as exc_info:
            await archive_course(db, course.id)
        assert exc_info.value.status_code == 409


class TestActivateCourse:
    @pytest.mark.asyncio
    async def test_activate_not_found(self) -> None:
        db = AsyncMock()
        db.get = AsyncMock(return_value=None)
        with pytest.raises(HTTPException) as exc_info:
            await activate_course(db, _uuid())
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_activate_sets_active(self) -> None:
        course = StubCourse(is_active=False, archived_at=datetime.now(UTC))
        stub_cs = StubCourseSettings()
        db = AsyncMock()
        db.get = AsyncMock(return_value=course)
        db.flush = AsyncMock()
        db.execute = AsyncMock(
            return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=stub_cs))
        )

        with patch(
            "app.services.courses._enqueue_team_syncs",
            new_callable=AsyncMock,
            return_value=0,
        ):
            result = await activate_course(db, course.id)

        assert result.is_active is True
        assert result.archived_at is None
        # Manual reactivation sets skip_auto_archive=True so the next sweep
        # won't immediately re-archive the course if the end date has passed.
        assert stub_cs.skip_auto_archive is True


class TestCloneCourse:
    @pytest.mark.asyncio
    async def test_clone_not_found(self) -> None:
        db = AsyncMock()
        db.get = AsyncMock(return_value=None)
        with pytest.raises(HTTPException) as exc_info:
            await clone_course(db, _uuid(), "2025/2026", "winter")
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_clone_creates_new_course(self) -> None:
        source = StubCourse(settings=StubCourseSettings())
        db = AsyncMock()
        db.get = AsyncMock(return_value=source)
        db.flush = AsyncMock()

        added_objects: list[Any] = []

        def track_add(obj: Any) -> None:
            added_objects.append(obj)

        db.add = track_add

        # Mock the custom check query
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        db.execute = AsyncMock(return_value=mock_result)

        with (
            patch("app.services.courses.Course") as mock_course_cls,
            patch("app.services.courses.CourseSettings") as mock_settings_cls,
        ):
            mock_course_inst = MagicMock()
            mock_course_inst.id = _uuid()
            mock_course_cls.return_value = mock_course_inst
            mock_settings_cls.return_value = MagicMock()

            await clone_course(db, source.id, "2025/2026", "summer")

        assert db.flush.await_count >= 1


class TestEnsureCourseActive:
    """ensure_course_active gates course-scoped mutations on archived courses."""

    @pytest.mark.asyncio
    async def test_active_course_passes(self):
        db = AsyncMock()
        db.get = AsyncMock(return_value=StubCourse(is_active=True))
        # Must NOT raise.
        await ensure_course_active(db, uuid.uuid4())

    @pytest.mark.asyncio
    async def test_archived_course_raises_409(self):
        db = AsyncMock()
        db.get = AsyncMock(return_value=StubCourse(is_active=False))
        with pytest.raises(HTTPException) as exc:
            await ensure_course_active(db, uuid.uuid4())
        assert exc.value.status_code == 409

    @pytest.mark.asyncio
    async def test_missing_course_does_not_raise(self):
        # A missing course is left to the caller's own 404 handling.
        db = AsyncMock()
        db.get = AsyncMock(return_value=None)
        await ensure_course_active(db, uuid.uuid4())


class TestArchiveWritesAudit:
    @pytest.mark.asyncio
    async def test_archive_writes_course_archive_audit(self) -> None:
        """archive_course records a course.archive audit so the activity feed
        can surface auto/manual archives."""
        from app.models.audit_log import AuditLog

        course = StubCourse()
        db = AsyncMock()
        db.get = AsyncMock(return_value=course)
        db.execute = AsyncMock(
            return_value=MagicMock(
                scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))
            )
        )
        db.flush = AsyncMock()
        db.rollback = AsyncMock()
        added: list[Any] = []
        db.add = MagicMock(side_effect=lambda o: added.append(o))

        with (
            patch(
                "app.services.courses._cancel_course_jobs",
                new_callable=AsyncMock,
                return_value=0,
            ),
            patch(
                "app.services.courses._deactivate_course_webhooks",
                new_callable=AsyncMock,
                return_value=0,
            ),
        ):
            await archive_course(db, course.id, actor="teacher1")

        audits = [o for o in added if isinstance(o, AuditLog)]
        assert any(a.action == "course.archive" and a.actor == "teacher1" for a in audits)


# -- Transfer (semester carry-over) --


@dataclass
class StubTeam:
    id: uuid.UUID = field(default_factory=_uuid)
    name: str = "Team Alpha"
    gitlab_group_id: int | None = 123
    gitlab_group_path: str | None = "kpi/devops/team-alpha"
    is_active: bool = True


@dataclass
class StubWebhookConfig:
    id: uuid.UUID = field(default_factory=_uuid)
    course_id: uuid.UUID = field(default_factory=_uuid)
    name: str = "Group hook"
    description: str | None = None
    scope_type: str = "group"
    gitlab_group_id: int | None = 123
    gitlab_group_path: str | None = "kpi/devops"
    gitlab_project_ids: list[int] = field(default_factory=list)
    is_active: bool = True


def _transfer_db(source: Any, teams: list[Any], configs: list[Any]) -> AsyncMock:
    db = AsyncMock()
    db.get = AsyncMock(return_value=source)
    db.flush = AsyncMock()
    db.add = MagicMock()

    def _scalars_result(items: list[Any]) -> MagicMock:
        return MagicMock(all=MagicMock(return_value=list(items)))

    # transfer_course awaits db.scalars twice: teams first, then webhook configs
    db.scalars = AsyncMock(side_effect=[_scalars_result(teams), _scalars_result(configs)])
    return db


def _new_course_stub(source: Any, year: str, semester: str) -> Any:
    return StubCourse(
        code=source.code,
        academic_year=year,
        semester=semester,
        cloned_from_id=source.id,
        settings=StubCourseSettings(
            weekly_deadlines=[
                {"week": 3, "label": "Git", "expected_checks": ["R01"]},
                {
                    "week": 12,
                    "label": "Final",
                    "mr_deadline": "2025-05-20T23:59:00",
                    "expected_checks": ["R01", "R02"],
                },
            ]
        ),
    )


class TestTransferCourse:
    @pytest.mark.asyncio
    async def test_invalid_modes_rejected(self) -> None:
        from app.services.courses import transfer_course

        db = AsyncMock()
        with pytest.raises(HTTPException) as e1:
            await transfer_course(db, _uuid(), "2026/2027", "winter", carry_mode="bogus")
        assert e1.value.status_code == 400
        with pytest.raises(HTTPException) as e2:
            await transfer_course(db, _uuid(), "2026/2027", "winter", webhook_mode="bogus")
        assert e2.value.status_code == 400

    @pytest.mark.asyncio
    async def test_source_not_found(self) -> None:
        from app.services.courses import transfer_course

        db = AsyncMock()
        db.get = AsyncMock(return_value=None)
        with pytest.raises(HTTPException) as exc:
            await transfer_course(db, _uuid(), "2026/2027", "winter")
        assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_carry_all_teams_moves_webhooks_and_enqueues_sync(self) -> None:
        from app.models.team import Team
        from app.services.courses import transfer_course

        source = StubCourse(
            academic_year="2025/2026", semester="winter", settings=StubCourseSettings()
        )
        teams = [StubTeam(name="A"), StubTeam(name="B")]
        cfg = StubWebhookConfig(course_id=source.id)
        db = _transfer_db(source, teams, [cfg])
        new_course = _new_course_stub(source, "2026/2027", "winter")
        # transfer_course reads the clone's settings row with a query
        db.scalar = AsyncMock(return_value=new_course.settings)

        with (
            patch(
                "app.services.courses.clone_course",
                new_callable=AsyncMock,
                return_value=new_course,
            ),
            patch("app.services.courses.archive_course", new_callable=AsyncMock) as mock_archive,
            patch(
                "app.services.courses._enqueue_team_syncs",
                new_callable=AsyncMock,
                return_value=2,
            ) as mock_sync,
            patch("app.services.audit.write_audit", new_callable=AsyncMock),
        ):
            result = await transfer_course(db, source.id, "2026/2027", "winter")

        assert result.teams_carried == 2
        carried = [c.args[0] for c in db.add.call_args_list if isinstance(c.args[0], Team)]
        assert {t.name for t in carried} == {"A", "B"}
        assert all(t.course_id == new_course.id for t in carried)
        # webhook moved to the new course, no secrets issued
        assert cfg.course_id == new_course.id
        assert result.webhooks_moved == 1
        assert result.webhooks_created == 0
        assert result.webhook_secrets == []
        mock_archive.assert_awaited_once()
        mock_sync.assert_awaited_once_with(db, new_course.id)
        assert result.sync_enqueued == 2

    @pytest.mark.asyncio
    async def test_selected_mode_validates_team_ownership(self) -> None:
        from app.services.courses import transfer_course

        source = StubCourse(settings=StubCourseSettings())
        teams = [StubTeam(name="A")]
        db = _transfer_db(source, teams, [])
        new_course = _new_course_stub(source, "2026/2027", "winter")
        # transfer_course reads the clone's settings row with a query
        db.scalar = AsyncMock(return_value=new_course.settings)

        with (
            patch(
                "app.services.courses.clone_course",
                new_callable=AsyncMock,
                return_value=new_course,
            ),
            patch("app.services.courses.archive_course", new_callable=AsyncMock),
            patch(
                "app.services.courses._enqueue_team_syncs",
                new_callable=AsyncMock,
                return_value=0,
            ),
            patch("app.services.audit.write_audit", new_callable=AsyncMock),
            pytest.raises(HTTPException) as exc,
        ):
            await transfer_course(
                db,
                source.id,
                "2026/2027",
                "winter",
                carry_mode="selected",
                team_ids=[_uuid()],  # id from another course
            )
        assert exc.value.status_code == 400

    @pytest.mark.asyncio
    async def test_none_mode_skips_teams_and_sync(self) -> None:
        from app.services.courses import transfer_course

        source = StubCourse(settings=StubCourseSettings())
        db = _transfer_db(source, [], [])
        # carry none: only ONE scalars call (webhook configs)
        db.scalars = AsyncMock(return_value=MagicMock(all=MagicMock(return_value=[])))
        new_course = _new_course_stub(source, "2026/2027", "winter")
        # transfer_course reads the clone's settings row with a query
        db.scalar = AsyncMock(return_value=new_course.settings)

        with (
            patch(
                "app.services.courses.clone_course",
                new_callable=AsyncMock,
                return_value=new_course,
            ),
            patch("app.services.courses.archive_course", new_callable=AsyncMock),
            patch(
                "app.services.courses._enqueue_team_syncs",
                new_callable=AsyncMock,
                return_value=0,
            ) as mock_sync,
            patch("app.services.audit.write_audit", new_callable=AsyncMock),
        ):
            result = await transfer_course(db, source.id, "2026/2027", "winter", carry_mode="none")

        assert result.teams_carried == 0
        mock_sync.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_fresh_webhooks_issue_new_secrets(self) -> None:
        from app.services.courses import transfer_course

        source = StubCourse(settings=StubCourseSettings())
        cfg = StubWebhookConfig(course_id=source.id, name="Hook X")
        db = _transfer_db(source, [], [cfg])
        # carry_mode="none" skips the teams query - the ONLY scalars call is
        # the webhook-config one, so it must not consume the teams slot.
        db.scalars = AsyncMock(return_value=MagicMock(all=MagicMock(return_value=[cfg])))
        new_course = _new_course_stub(source, "2026/2027", "winter")
        # transfer_course reads the clone's settings row with a query
        db.scalar = AsyncMock(return_value=new_course.settings)
        created = MagicMock()
        created.plaintext = "whsec_NEW"

        with (
            patch(
                "app.services.courses.clone_course",
                new_callable=AsyncMock,
                return_value=new_course,
            ),
            patch("app.services.courses.archive_course", new_callable=AsyncMock),
            patch(
                "app.services.courses._enqueue_team_syncs",
                new_callable=AsyncMock,
                return_value=0,
            ),
            patch(
                "app.services.webhook_configs.create_configuration",
                new_callable=AsyncMock,
                return_value=created,
            ) as mock_create,
            patch("app.services.audit.write_audit", new_callable=AsyncMock),
        ):
            result = await transfer_course(
                db,
                source.id,
                "2026/2027",
                "winter",
                carry_mode="none",
                webhook_mode="fresh",
            )

        assert result.webhooks_created == 1
        assert result.webhook_secrets == [{"name": "Hook X", "secret": "whsec_NEW"}]
        assert cfg.course_id == source.id  # original untouched in fresh mode
        assert mock_create.await_args.kwargs["course_id"] == new_course.id

    @pytest.mark.asyncio
    async def test_archive_source_false_keeps_source_active(self) -> None:
        from app.services.courses import transfer_course

        source = StubCourse(settings=StubCourseSettings())
        db = _transfer_db(source, [], [])
        db.scalars = AsyncMock(return_value=MagicMock(all=MagicMock(return_value=[])))
        new_course = _new_course_stub(source, "2026/2027", "winter")
        # transfer_course reads the clone's settings row with a query
        db.scalar = AsyncMock(return_value=new_course.settings)

        with (
            patch(
                "app.services.courses.clone_course",
                new_callable=AsyncMock,
                return_value=new_course,
            ),
            patch("app.services.courses.archive_course", new_callable=AsyncMock) as mock_archive,
            patch(
                "app.services.courses._enqueue_team_syncs",
                new_callable=AsyncMock,
                return_value=0,
            ),
            patch("app.services.audit.write_audit", new_callable=AsyncMock),
        ):
            result = await transfer_course(
                db,
                source.id,
                "2026/2027",
                "winter",
                carry_mode="none",
                archive_source=False,
            )

        mock_archive.assert_not_awaited()
        assert result.source_archived is False

    @staticmethod
    async def _transfer(source: Any, year: str, semester: str, **kwargs: Any) -> Any:
        from app.services.courses import transfer_course

        db = _transfer_db(source, [], [])
        db.scalars = AsyncMock(return_value=MagicMock(all=MagicMock(return_value=[])))
        new_course = _new_course_stub(source, year, semester)
        # transfer_course reads the clone's settings row with a query
        db.scalar = AsyncMock(return_value=new_course.settings)
        with (
            patch(
                "app.services.courses.clone_course",
                new_callable=AsyncMock,
                return_value=new_course,
            ),
            patch("app.services.courses.archive_course", new_callable=AsyncMock),
            patch(
                "app.services.courses._enqueue_team_syncs",
                new_callable=AsyncMock,
                return_value=0,
            ),
            patch("app.services.audit.write_audit", new_callable=AsyncMock),
        ):
            await transfer_course(db, source.id, year, semester, carry_mode="none", **kwargs)
        return new_course.settings

    @pytest.mark.asyncio
    async def test_the_new_term_gets_its_official_dates_and_deadlines_keep_their_weekday(
        self,
    ) -> None:
        """The target term's TUKE dates, and every deadline moved by exactly as
        much as the start did.

        It used to add calendar years: 2025-09-15 (a Monday) became 2026-09-15
        (a Tuesday), and every Friday deadline landed on a Saturday.
        """
        from datetime import date as _date

        src_settings = StubCourseSettings(
            semester_start_date=_date(2025, 9, 15),
            semester_end_date=_date(2025, 12, 20),
        )
        source = StubCourse(academic_year="2025/2026", semester="winter", settings=src_settings)

        ns = await self._transfer(source, "2026/2027", "winter")

        assert ns.semester_start_date == _date(2026, 9, 21)  # TUKE winter 2026/2027
        assert ns.semester_end_date == _date(2027, 2, 12)
        final = next(e for e in ns.weekly_deadlines if e["week"] == 12)
        # 2025-05-20 is a Tuesday; so is its moved date.
        assert final["mr_deadline"] == "2026-05-26T23:59:00"
        assert _date(2026, 5, 26).weekday() == _date(2025, 5, 20).weekday()

    @pytest.mark.asyncio
    async def test_beyond_the_calendar_the_window_moves_by_whole_weeks(self) -> None:
        """No official dates for the target: the source's window, 52 weeks on -
        the same weekday, not the same calendar date."""
        from datetime import date as _date

        src_settings = StubCourseSettings(
            semester_start_date=_date(2026, 9, 21),
            semester_end_date=_date(2027, 2, 12),
        )
        source = StubCourse(academic_year="2026/2027", semester="winter", settings=src_settings)

        ns = await self._transfer(source, "2027/2028", "winter")

        assert ns.semester_start_date == _date(2027, 9, 20)
        assert ns.semester_start_date.weekday() == 0  # still a Monday
        assert ns.semester_end_date == _date(2028, 2, 11)

    @pytest.mark.asyncio
    async def test_the_dates_the_dialog_sent_win(self) -> None:
        from datetime import date as _date

        src_settings = StubCourseSettings(
            semester_start_date=_date(2025, 9, 15),
            semester_end_date=_date(2025, 12, 20),
        )
        source = StubCourse(academic_year="2025/2026", semester="winter", settings=src_settings)

        ns = await self._transfer(
            source,
            "2026/2027",
            "winter",
            semester_start_date=_date(2026, 9, 28),
            semester_end_date=_date(2027, 1, 29),
        )

        assert ns.semester_start_date == _date(2026, 9, 28)
        assert ns.semester_end_date == _date(2027, 1, 29)
        final = next(e for e in ns.weekly_deadlines if e["week"] == 12)
        # moved by start-to-start: 2025-09-15 -> 2026-09-28 is 378 days
        assert final["mr_deadline"] == "2026-06-02T23:59:00"

    @pytest.mark.asyncio
    async def test_a_change_of_term_keeps_the_week_structure_when_both_starts_are_known(
        self,
    ) -> None:
        """Winter to summer used to drop every deadline date. With the summer's
        official start known, week 5 stays week 5."""
        from datetime import date as _date

        src_settings = StubCourseSettings(
            semester_start_date=_date(2025, 9, 22),
            semester_end_date=_date(2026, 2, 13),
        )
        source = StubCourse(academic_year="2025/2026", semester="winter", settings=src_settings)

        ns = await self._transfer(source, "2025/2026", "summer")

        assert ns.semester_start_date == _date(2026, 2, 16)
        final = next(e for e in ns.weekly_deadlines if e["week"] == 12)
        assert "mr_deadline" in final

    @pytest.mark.asyncio
    async def test_the_clones_settings_are_queried_not_lazy_loaded(self) -> None:
        """Every real transfer ended in a 500 (MissingGreenlet).

        `new_course.settings` on the course the session had just created
        lazy-loads, which an async session cannot do. The unit tests handed in
        a stub whose `.settings` was a plain attribute, so none of them saw it;
        this stub fails the way the real relationship does.
        """
        from datetime import date as _date

        from app.services.courses import transfer_course

        class _LazyCourse(StubCourse):
            @property  # type: ignore[override]
            def settings(self) -> Any:
                raise RuntimeError("lazy load in an async session")

            @settings.setter
            def settings(self, _value: Any) -> None:
                pass

        src_settings = StubCourseSettings(semester_start_date=_date(2025, 9, 15))
        source = StubCourse(academic_year="2025/2026", semester="winter", settings=src_settings)
        db = _transfer_db(source, [], [])
        db.scalars = AsyncMock(return_value=MagicMock(all=MagicMock(return_value=[])))
        clone = _LazyCourse(code=source.code, academic_year="2026/2027", semester="winter")
        clone_settings = StubCourseSettings()
        db.scalar = AsyncMock(return_value=clone_settings)
        with (
            patch("app.services.courses.clone_course", new_callable=AsyncMock, return_value=clone),
            patch("app.services.courses.archive_course", new_callable=AsyncMock),
            patch(
                "app.services.courses._enqueue_team_syncs",
                new_callable=AsyncMock,
                return_value=0,
            ),
            patch("app.services.audit.write_audit", new_callable=AsyncMock),
        ):
            await transfer_course(db, source.id, "2026/2027", "winter", carry_mode="none")

        assert clone_settings.semester_start_date == _date(2026, 9, 21)

    @pytest.mark.asyncio
    async def test_cross_semester_transfer_clears_weekly_dates(self) -> None:
        from app.services.courses import transfer_course

        source = StubCourse(
            academic_year="2025/2026", semester="winter", settings=StubCourseSettings()
        )
        db = _transfer_db(source, [], [])
        db.scalars = AsyncMock(return_value=MagicMock(all=MagicMock(return_value=[])))
        new_course = _new_course_stub(source, "2025/2026", "summer")
        # transfer_course reads the clone's settings row with a query
        db.scalar = AsyncMock(return_value=new_course.settings)

        with (
            patch(
                "app.services.courses.clone_course",
                new_callable=AsyncMock,
                return_value=new_course,
            ),
            patch("app.services.courses.archive_course", new_callable=AsyncMock),
            patch(
                "app.services.courses._enqueue_team_syncs",
                new_callable=AsyncMock,
                return_value=0,
            ),
            patch("app.services.audit.write_audit", new_callable=AsyncMock),
        ):
            await transfer_course(db, source.id, "2025/2026", "summer", carry_mode="none")

        ns = new_course.settings
        assert all("mr_deadline" not in e for e in ns.weekly_deadlines)
        # structure (weeks + expected checks) preserved
        assert {e["week"] for e in ns.weekly_deadlines} == {3, 12}
