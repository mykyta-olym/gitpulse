"""Master API router - aggregates all sub-routers."""

from enum import Enum
from typing import Any, cast

from fastapi import APIRouter

from app.api.compliance_history import router as compliance_history_router
from app.api.contracts import API_ERROR_RESPONSES
from app.api.courses import router as courses_router
from app.api.events import router as events_router
from app.api.gitlab_parse import router as gitlab_parse_router
from app.api.llm import router as llm_router
from app.api.observability import router as observability_router
from app.api.projects import router as projects_router
from app.api.sse import router as sse_router
from app.api.students import router as students_router
from app.api.support import router as support_router
from app.api.sync import router as sync_router
from app.api.teams import router as teams_router
from app.api.users import router as users_router
from app.api.webhook_configs import router as webhook_configs_router
from app.api.webhooks import router as webhooks_router

api_router = APIRouter()


def _include(router: APIRouter, *, prefix: str = "", tags: list[str] | None = None) -> None:
    include_tags = cast(list[str | Enum] | None, tags)
    include_responses = cast(dict[int | str, dict[str, Any]], dict(API_ERROR_RESPONSES))
    api_router.include_router(
        router,
        prefix=prefix,
        tags=include_tags,
        responses=include_responses,
    )


_include(webhooks_router, prefix="/webhooks", tags=["webhooks"])
_include(webhook_configs_router, tags=["webhooks"])
_include(llm_router, prefix="/llm", tags=["llm"])

_include(gitlab_parse_router, prefix="/gitlab", tags=["gitlab"])
_include(courses_router, prefix="/courses", tags=["courses"])
_include(teams_router, prefix="/teams", tags=["teams"])
_include(students_router, prefix="/students", tags=["students"])
_include(projects_router, prefix="/projects", tags=["projects"])
_include(users_router, prefix="/users", tags=["users"])
_include(events_router, prefix="/events", tags=["events"])
_include(sync_router, tags=["sync"])
_include(sse_router, tags=["sse"])
_include(compliance_history_router, tags=["compliance"])
_include(observability_router, tags=["observability"])
_include(support_router, tags=["support"])
