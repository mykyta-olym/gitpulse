"""Dashboard API schemas."""

from pydantic import BaseModel


class LLMProjectAnalysisStatusResponse(BaseModel):
    status: str
    message: str
    reload: bool | None = None
    analyzed: int | None = None
    failed: int | None = None
    skipped: int | None = None
    total: int | None = None
    progress: int | None = None
    current_mr: int | None = None


class LLMTeamAnalysisStatusResponse(BaseModel):
    status: str
    message: str
    completed: int | None = None
    failed: int | None = None
    running: int | None = None
    total: int | None = None
    progress: int | None = None
