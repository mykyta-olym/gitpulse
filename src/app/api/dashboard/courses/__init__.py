"""Course pages: the course, its checks, its settings and its assistant."""

from app.api.dashboard.courses.assistant import router as assistant_router
from app.api.dashboard.courses.checks import router as checks_router
from app.api.dashboard.courses.routes import router as courses_router
from app.api.dashboard.courses.settings import router as settings_router

__all__ = ["assistant_router", "checks_router", "courses_router", "settings_router"]
