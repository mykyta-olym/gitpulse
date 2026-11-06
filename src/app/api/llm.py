import uuid as uuid_mod

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select

from app.api.errors import raise_bad_request, raise_not_found, raise_unprocessable
from app.config import Settings, get_settings
from app.dependencies import ApiAuth, DbSession, RequireLLMSuggestions
from app.models.llm_log import LLMAnalysisLog
from app.models.project import GitLabProject
from app.schemas.llm import (
    LLMAnalysisLog as LLMAnalysisLogSchema,
)
from app.schemas.llm import (
    LLMAnalysisResponse,
)
from app.services.llm.service import LLMService

router = APIRouter()


def get_llm_service(settings: Settings = Depends(get_settings)) -> LLMService:
    return LLMService(settings)


@router.post("/mr/{project_id}/{mr_iid}", response_model=LLMAnalysisResponse)
async def analyze_merge_request(
    project_id: str,
    mr_iid: int,
    request: Request,
    _auth: ApiAuth,  # Authentication required
    _feature: RequireLLMSuggestions,  # Feature flag check
    db: DbSession,
    service: LLMService = Depends(get_llm_service),
    settings: Settings = Depends(get_settings),
) -> LLMAnalysisResponse:
    """
    Trigger LLM analysis for a specific Merge Request.
    Returns structured analysis with evidence links.
    """
    # Find project by UUID or GitLab ID
    try:
        p_uuid = uuid_mod.UUID(project_id)
        project_stmt = select(GitLabProject).where(GitLabProject.id == p_uuid)
    except ValueError:
        if project_id.isdigit():
            project_stmt = select(GitLabProject).where(
                GitLabProject.gitlab_project_id == int(project_id)
            )
        else:
            raise_bad_request("Invalid project ID format")

    result = await db.execute(project_stmt)
    project = result.scalars().first()

    if not project:
        raise_not_found("Project not found")

    # Authorize against the project's course (ApiAuth only authenticates, so
    # without this any logged-in student could trigger a paid LLM analysis on
    # any project by UUID/GitLab-id). Bearer tokens + admins unrestricted,
    # session users only projects in a course/team they may view.
    from app.api.dashboard._access import can_manage_via_request

    if not await can_manage_via_request(request, db, project=project):
        raise_not_found("Project not found")

    # An archived course is read-only, and this endpoint STARTS a paid external
    # process. Refuse it on the server so a stale tab or a direct call cannot
    # spend budget on a course that is closed.
    from app.models.team import Team
    from app.services.courses import ensure_course_active

    if project.team_id is not None:
        _team = await db.get(Team, project.team_id)
        if _team is not None:
            await ensure_course_active(db, _team.course_id)

    # Perform analysis
    analysis = await service.analyze_mr(db, project.id, mr_iid)
    if not analysis:
        raise_unprocessable("MR not found or analysis failed. Check logs for details.")

    # Construct evidence link templates for UI
    gitlab_mr_url = f"{settings.gitlab_url}/{project.gitlab_project_path}/-/merge_requests/{mr_iid}"
    note_url_template = f"{gitlab_mr_url}#note_{{id}}"

    return LLMAnalysisResponse(
        analysis=analysis, gitlab_mr_url=gitlab_mr_url, note_url_template=note_url_template
    )


@router.get("/mr/{project_id}/{mr_iid}/history", response_model=list[LLMAnalysisLogSchema])
async def get_mr_analysis_history(
    project_id: str,
    mr_iid: int,
    request: Request,
    _auth: ApiAuth,  # Authentication required
    db: DbSession,
) -> list[LLMAnalysisLogSchema]:
    """
    Get past analysis results from DB.
    """
    try:
        p_uuid = uuid_mod.UUID(project_id)
        project_stmt = select(GitLabProject).where(GitLabProject.id == p_uuid)
    except ValueError:
        if project_id.isdigit():
            project_stmt = select(GitLabProject).where(
                GitLabProject.gitlab_project_id == int(project_id)
            )
        else:
            raise_bad_request("Invalid project ID format")

    result = await db.execute(project_stmt)
    project = result.scalars().first()

    if not project:
        raise_not_found("Project not found")

    # Authorize against the project's course before returning analysis history
    # (ApiAuth only authenticates). Same model as the trigger endpoint above.
    from app.api.dashboard._access import can_manage_via_request

    if not await can_manage_via_request(request, db, project=project):
        raise_not_found("Project not found")

    log_stmt = (
        select(LLMAnalysisLog)
        .where(
            LLMAnalysisLog.project_id == project.id,
            LLMAnalysisLog.mr_iid == mr_iid,
            LLMAnalysisLog.target_type.notin_(["error", "job_running"]),
        )
        .order_by(LLMAnalysisLog.analysis_timestamp.desc())
        .limit(50)
    )

    logs = await db.execute(log_stmt)
    items = list(logs.scalars().all())
    return [LLMAnalysisLogSchema.model_validate(item) for item in items]
