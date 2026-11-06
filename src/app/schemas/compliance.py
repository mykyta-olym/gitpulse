"""Compliance history response schemas (api/compliance_history.py)."""

from pydantic import BaseModel


class StudentComplianceHistoryResponse(BaseModel):
    week_number: int
    snapshot_date: str | None = None
    overall_score: float | None = None
    commit_score: float | None = None
    mr_score: float | None = None
    review_score: float | None = None
    ci_score: float | None = None
    issue_score: float | None = None
    improvement_delta: float | None = None
    improvement_pct: float | None = None
    checks_detail: dict[str, dict[str, object]] | None = None


class ComplianceTrendResponse(BaseModel):
    week_number: int
    week_start: str | None = None
    avg_score: float
    std_dev: float
    min_score: float
    max_score: float
    students_count: int
    improved_count: int
    declined_count: int
