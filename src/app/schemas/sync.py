"""Sync endpoint response schemas."""

from pydantic import BaseModel


class SyncAllResponse(BaseModel):
    """Response for sync-all endpoint."""

    enqueued: int
    skipped: int
    failed: int
    already_fresh: int = 0
    message: str


class TeamSyncStatus(BaseModel):
    """Status info for a single team."""

    team_id: str
    team_name: str
    member_count: int
    sync_status: str | None
    avg_score: float | None
    traffic_light: str | None
    last_updated: str | None
    last_updated_iso: str | None = None
    # Transient note for an in-flight retry, e.g. "Retrying (2/3)...". Present
    # only while the group's active sync job is on a retry attempt; lets the
    # row show "RETRY 2/3" instead of a plain SYNCING badge.
    sync_note: str | None = None


class CourseSyncStatusResponse(BaseModel):
    """Response for course sync status endpoint."""

    sync_running_count: int
    sync_queued_count: int
    sync_failed_count: int
    sync_cancelled_count: int = 0
    has_active_sync: bool
    total_students: int | None = None
    synced_groups: int | None = None
    total_groups: int | None = None
    progress: int | None = None
    teams: list[TeamSyncStatus]
    # Per-project sync status keyed by project UUID (string). Populated
    # only when a *project-scoped* sync job is active (or recently
    # completed) - team-wide jobs do not contribute here. The frontend
    # uses this to paint per-row SYNCING badges precisely instead of
    # lighting up every project row whenever the team is syncing.
    sync_status_by_project: dict[str, str] = {}
    project_sync_running_count: int = 0
    project_sync_queued_count: int = 0
    # False only when the shared token-health flag is KNOWN-bad (a 401/403 was
    # seen somewhere in the app). Drives a "GitLab token invalid" banner and
    # tells the UI that sync/import will be refused until the token is fixed.
    gitlab_token_ok: bool = True


class CourseRunChecksStatusResponse(BaseModel):
    """Aggregate status for a course-level run-checks fan-out."""

    status: str
    running_count: int = 0
    queued_count: int = 0
    active_count: int = 0
    total_groups: int = 0
    progress: int = 100
    result_summary: str | None = None
    error_message: str | None = None


class ActiveSyncCourse(BaseModel):
    """A course with an in-progress sync (for global-bar discovery)."""

    course_id: str
    name: str | None = None
    code: str | None = None
    running: int = 0
    queued: int = 0
    # Earliest enqueued_at of the batch - used client-side to decide
    # whether a dismissed bar belongs to the current run (suppressed) or
    # a fresh run that started after dismissal (re-shown). Epoch ms, UTC.
    started_at_ms: int | None = None


class ActiveSyncsResponse(BaseModel):
    """Response listing all courses with active syncs."""

    courses: list[ActiveSyncCourse]
