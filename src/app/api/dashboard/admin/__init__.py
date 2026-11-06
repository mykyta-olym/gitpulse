"""Administration pages: users, courses and teachers, system, analytics, events."""

from fastapi import APIRouter

from app.api.dashboard.admin.analytics import router as analytics_router
from app.api.dashboard.admin.course_teachers import router as course_teachers_router
from app.api.dashboard.admin.events import router as events_router
from app.api.dashboard.admin.system import router as system_router
from app.api.dashboard.admin.users import router as users_router

router = APIRouter()
router.include_router(users_router)
router.include_router(course_teachers_router)
router.include_router(system_router)
router.include_router(analytics_router)
router.include_router(events_router)

__all__ = ["router"]
