"""Course and CourseSettings schemas."""

from datetime import date, datetime
from typing import Annotated, Any, Literal
from uuid import UUID

from pydantic import AfterValidator, BaseModel, Field, model_validator

from app.schemas.common import ORMBase
from app.schemas.custom_check import CheckUpdate
from app.utils.academic_period import calendar_period, normalize_academic_year, normalize_semester
from app.utils.semester import SemesterDateError, validate_semester_window

#: An academic year and a semester as every way in accepts them - the dialogs,
#: this API, the GitLab import and the JSON config import. A course whose year
#: is "2026/2028" or whose semester is "Winter" matches no period, so it would
#: vanish from every period-scoped page; nothing can create one now.
AcademicYear = Annotated[str, AfterValidator(normalize_academic_year)]
Semester = Annotated[str, AfterValidator(normalize_semester)]


def _calendar_year() -> str:
    """The academic year a request that names none means: the calendar's."""
    return calendar_period().academic_year


def _calendar_semester() -> str:
    """The semester a request that names none means: the calendar's.

    It used to be "winter" for a created course and "summer" for an imported
    one - two defaults for the same question, one of them wrong half the year.
    """
    return calendar_period().semester


def _check_window(start: date | None, end: date | None) -> None:
    """The semester-window rules the settings page enforces, for a NEW course."""
    try:
        validate_semester_window(start, end)
    except SemesterDateError as exc:
        raise ValueError(str(exc)) from exc


class CourseCreate(BaseModel):
    code: str = Field(..., max_length=20)
    name: str = Field(..., max_length=200)
    description: str = Field("", max_length=2000)
    academic_year: AcademicYear
    semester: Semester = Field(default_factory=_calendar_semester)
    # Optional: populate CourseSettings timeline fields at creation time so a
    # manually-created course can auto-archive once its semester ends without
    # requiring a separate "edit settings" step.
    semester_start_date: date | None = None
    semester_end_date: date | None = None

    @model_validator(mode="after")
    def _window(self) -> "CourseCreate":
        _check_window(self.semester_start_date, self.semester_end_date)
        return self


class CourseUpdate(BaseModel):
    code: str | None = Field(None, max_length=20)
    name: str | None = Field(None, max_length=200)
    description: str | None = Field(None, max_length=2000)
    academic_year: AcademicYear | None = None
    semester: Semester | None = None
    # The dates travel with the period they belong to: a dialog that moves a
    # course to another term moves its dates in the same request. Sent as null
    # to clear; left out to keep. Validated against the stored values in the
    # endpoint, where they are known.
    semester_start_date: date | None = None
    semester_end_date: date | None = None
    expected_updated_at: datetime | None = Field(
        default=None,
        description="Optimistic lock: expected updated_at timestamp. Returns 409 if stale.",
    )


class CourseTransferRequest(BaseModel):
    """Full semester carry-over (see course_service.transfer_course)."""

    academic_year: AcademicYear
    semester: Semester = Field(default_factory=_calendar_semester)
    carry_mode: Literal["all", "selected", "none"] = "all"
    team_ids: list[UUID] = []
    webhook_mode: Literal["move", "fresh", "none"] = "move"
    archive_source: bool = True
    enqueue_sync: bool = True
    # The new course's dates, when the dialog names them (the official ones of
    # the target term, or the teacher's own). Left out, they are derived from
    # the source course - see transfer_course.
    semester_start_date: date | None = None
    semester_end_date: date | None = None

    @model_validator(mode="after")
    def _window(self) -> "CourseTransferRequest":
        _check_window(self.semester_start_date, self.semester_end_date)
        return self


class CourseTransferResponse(BaseModel):
    id: UUID
    code: str
    academic_year: str
    semester: str
    teams_carried: int
    webhooks_moved: int
    webhooks_created: int
    webhook_secrets: list[dict[str, str]]
    sync_enqueued: int
    source_archived: bool


class CourseRead(ORMBase):
    id: UUID
    code: str
    name: str
    academic_year: str
    semester: str
    is_active: bool
    description: str = ""
    archived_at: datetime | None = None
    cloned_from_id: UUID | None = None
    created_at: datetime
    updated_at: datetime | None = None


class GitLabGroupImportRequest(BaseModel):
    """Request payload for auto-importing a course from a GitLab group."""

    group_url: str = Field(
        ...,
        max_length=500,
        description="GitLab group URL or path",
    )
    target_course_id: UUID | None = Field(
        default=None,
        description="Optional existing course ID to import into",
    )
    course_code: str = Field(default="", max_length=20)
    course_name: str = Field(default="", max_length=200)
    # Defaults were the literals "2025/2026" and "summer": a client that named
    # no period got last year's summer forever.
    academic_year: AcademicYear = Field(default_factory=_calendar_year)
    semester: Semester = Field(default_factory=_calendar_semester)
    include_subgroups: bool = Field(
        default=True,
        description="Import subgroup groups/projects recursively",
    )
    one_team_per_project: bool = Field(
        default=False,
        description="Create separate group for each project (instead of groups from subgroups)",
    )
    auto_sync: bool = Field(
        default=True,
        description="Automatically enqueue full data sync after import",
    )
    teacher_usernames: list[str] | None = Field(
        default=None,
        description="Optional explicit teachers to include alongside auto-detected teachers",
    )
    semester_start_date: date | None = Field(
        default=None,
        description="Optional semester start date; populated onto the course settings on create",
    )
    semester_end_date: date | None = Field(
        default=None,
        description="Optional semester end date; drives auto-archive sweep when reached",
    )

    @model_validator(mode="after")
    def _require_code_name_without_target(self) -> "GitLabGroupImportRequest":
        """course_code and course_name are required when creating a new course."""
        if self.target_course_id is None:
            if len(self.course_code) < 2:
                msg = "course_code required (min 2 chars) without target_course_id"
                raise ValueError(msg)
            if len(self.course_name) < 2:
                msg = "course_name required (min 2 chars) without target_course_id"
                raise ValueError(msg)
            # The window rules only bite for a course this import creates; an
            # import INTO an existing course never writes its dates.
            _check_window(self.semester_start_date, self.semester_end_date)
        return self


class GitLabGroupImportResponse(BaseModel):
    """Result summary for GitLab group import."""

    course_id: UUID
    course_code: str
    course_name: str
    # The period the course is in, so the page that started the import can go
    # to it: an import into another term than the one on screen otherwise
    # "succeeds" and leaves the reader looking at a list without it.
    course_academic_year: str = ""
    course_semester: str = ""
    group_path: str
    created_course: bool
    teams_created: int
    teams_updated: int
    students_created: int
    students_updated: int
    memberships_created: int
    projects_created: int
    projects_updated: int
    projects_deactivated: int = 0
    teachers_detected: list[str]
    sync_jobs_enqueued: int = 0
    sync_jobs_skipped: int = 0
    warnings: list[str] = Field(default_factory=list)


class CourseImportDuplicateMatchCourse(BaseModel):
    id: UUID
    code: str
    name: str
    academic_year: str
    semester: str
    team_count: int
    student_count: int
    project_count: int


class CourseImportDuplicateMatchTeam(BaseModel):
    name: str
    gitlab_group_id: int | None = None
    project_count: int


class CourseImportDuplicateMatchProject(BaseModel):
    gitlab_project_path: str
    gitlab_project_name: str | None = None
    current_course_code: str | None = None
    current_team_name: str | None = None


class CourseImportDuplicateCheckResponse(BaseModel):
    has_duplicate: bool = False
    matching_course: CourseImportDuplicateMatchCourse | None = None
    matching_teams: list[CourseImportDuplicateMatchTeam] = Field(default_factory=list)
    cross_course_projects: list[CourseImportDuplicateMatchProject] = Field(default_factory=list)


class CourseSettingsUpdate(BaseModel):
    branch_pattern: str | None = Field(None, max_length=200)
    mr_template_required_sections: list[str] | None = None
    min_reviews_per_mr: int | None = Field(None, ge=1, le=100)
    min_review_word_count: int | None = Field(None, ge=1, le=10000)
    min_distinct_mrs_reviewed: int | None = Field(None, ge=1, le=100)
    mr_creation_deadline: datetime | None = None
    merge_deadline: datetime | None = None
    weight_issue_ownership: float | None = Field(default=None, ge=0.0, le=1.0)
    weight_branch_naming: float | None = Field(default=None, ge=0.0, le=1.0)
    weight_mr_issue_link: float | None = Field(default=None, ge=0.0, le=1.0)
    weight_mr_template: float | None = Field(default=None, ge=0.0, le=1.0)
    weight_test_changes: float | None = Field(default=None, ge=0.0, le=1.0)
    weight_review_count: float | None = Field(default=None, ge=0.0, le=1.0)
    weight_review_duty: float | None = Field(default=None, ge=0.0, le=1.0)
    weight_response_complete: float | None = Field(default=None, ge=0.0, le=1.0)
    weight_approvals: float | None = Field(default=None, ge=0.0, le=1.0)
    weight_merge_by_author: float | None = Field(default=None, ge=0.0, le=1.0)
    weight_closure: float | None = Field(default=None, ge=0.0, le=1.0)
    weight_pipeline_health: float | None = Field(default=None, ge=0.0, le=1.0)
    weight_commit_quality: float | None = Field(default=None, ge=0.0, le=1.0)
    green_threshold: float | None = Field(default=None, ge=0.0, le=1.0)
    yellow_threshold: float | None = Field(default=None, ge=0.0, le=1.0)
    test_file_patterns: list[str] | None = None
    enabled_checks: list[str] | None = None
    weekly_deadlines: list[dict[str, Any]] | None = None
    check_configs: dict[str, dict[str, Any]] | None = None
    gitlab_group_path: str | None = Field(None, max_length=300)
    gitlab_group_id: int | None = Field(default=None, ge=1)
    webhook_secret: str | None = Field(None, max_length=128)
    semester_start_date: date | None = None
    semester_end_date: date | None = None
    skip_auto_archive: bool | None = None
    # -- AI analysis configuration --
    llm_course_type: Literal["default", "zsi", "devops"] | None = None
    llm_custom_prompt: str | None = Field(default=None, max_length=20000)
    llm_resource_urls: list[dict[str, Any]] | None = None
    expected_updated_at: datetime | None = Field(
        default=None,
        description="Optimistic lock: expected updated_at timestamp. Returns 409 if stale.",
    )

    @model_validator(mode="after")
    def _non_null_settings(self) -> "CourseSettingsUpdate":
        nullable = {
            "expected_updated_at",
            "mr_creation_deadline",
            "merge_deadline",
            "semester_start_date",
            "semester_end_date",
            "gitlab_group_path",
            "gitlab_group_id",
            "webhook_secret",
            "llm_custom_prompt",
        }
        for field in self.model_fields_set - nullable:
            if getattr(self, field) is None:
                raise ValueError(f"{field} cannot be null")
        return self


class CourseConfigurationUpdate(BaseModel):
    """One settings-page save, including staged check edits."""

    course: CourseUpdate
    settings: CourseSettingsUpdate
    checks: dict[str, CheckUpdate] = Field(default_factory=dict, max_length=100)


class CourseSettingsRead(ORMBase):
    id: UUID
    course_id: UUID
    branch_pattern: str
    min_reviews_per_mr: int
    min_review_word_count: int
    min_distinct_mrs_reviewed: int
    green_threshold: float
    yellow_threshold: float
    weight_issue_ownership: float = 0.08
    weight_branch_naming: float = 0.06
    weight_mr_issue_link: float = 0.08
    weight_mr_template: float = 0.05
    weight_test_changes: float = 0.10
    weight_review_count: float = 0.12
    weight_review_duty: float = 0.12
    weight_response_complete: float = 0.10
    weight_approvals: float = 0.09
    weight_merge_by_author: float = 0.07
    weight_closure: float = 0.06
    weight_pipeline_health: float = 0.07
    weight_commit_quality: float = 0.0
    test_file_patterns: list[str] = Field(default_factory=list)
    mr_template_required_sections: list[str] = Field(default_factory=list)
    enabled_checks: list[str] = Field(default_factory=list)
    weekly_deadlines: list[dict[str, Any]] = Field(default_factory=list)
    mr_creation_deadline: datetime | None = None
    merge_deadline: datetime | None = None
    semester_start_date: date | None = None
    semester_end_date: date | None = None
    skip_auto_archive: bool = False
    check_configs: dict[str, dict[str, Any]] = Field(default_factory=dict)
    gitlab_group_path: str | None = None
    gitlab_group_id: int | None = None
    updated_at: datetime
