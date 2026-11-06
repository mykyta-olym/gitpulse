"""Shared FastAPI dependency providers for the support endpoints."""

from app.config import get_settings
from app.dependencies import DbSession
from app.services.support_forms import SupportFormService


def get_support_form_service(
    db: DbSession,
) -> SupportFormService:
    """Get support-form service instance."""
    settings = get_settings()
    return SupportFormService(
        db,
        enabled=settings.feature_support_forms,
        anonymize_text=settings.support_anonymize_free_text,
    )
