"""Dashboard (HTML) routes - one package per domain, the way GitLab lays out
`app/controllers/<domain>/`: home, courses, teams, projects, students, admin,
support, auth and preferences. Each package exposes its router here; the JSON API lives
in `app/api/` (`api/v1`)."""

from fastapi import APIRouter

from app.api.dashboard._access import _ensure_session_user_in_db, _is_session_user_active
from app.api.dashboard.admin import router as admin_router
from app.api.dashboard.auth import router as auth_router
from app.api.dashboard.auth import switch_language
from app.api.dashboard.courses import (
    assistant_router,
    checks_router,
    courses_router,
    settings_router,
)
from app.api.dashboard.home import router as home_router
from app.api.dashboard.preferences import router as preferences_router
from app.api.dashboard.projects import router as projects_router
from app.api.dashboard.students import router as students_router
from app.api.dashboard.support import router as support_router
from app.api.dashboard.teams import router as teams_router

router = APIRouter()

router.include_router(auth_router)
router.include_router(home_router)
router.include_router(preferences_router)
router.include_router(courses_router)
router.include_router(settings_router)
router.include_router(checks_router)
router.include_router(assistant_router)
router.include_router(teams_router)
router.include_router(projects_router)
router.include_router(students_router)
router.include_router(support_router)
router.include_router(admin_router)

__all__ = ["_ensure_session_user_in_db", "_is_session_user_active", "router", "switch_language"]
