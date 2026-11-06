from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

# Accepted source types - LLMs may invent new values so we normalize
_SOURCE_TYPE_MAP: dict[str, str] = {
    "note": "note",
    "comment": "note",
    "discussion": "note",
    "review": "note",
    "description": "description",
    "mr_description": "description",
    "title": "title",
    "mr_title": "title",
    "general": "general",
    "metadata": "general",
    "overall": "general",
    "observation": "general",
    "diff": "diff",
    "code": "diff",
    "commit": "commit",
    "pipeline": "general",
    "branch": "general",
    "ci": "general",
}

_SCORE_MAP: dict[str, str] = {
    "excellent": "excellent",
    "good": "good",
    "fair": "fair",
    "poor": "poor",
    "not_applicable": "fair",
    "n/a": "fair",
    "none": "fair",
    "average": "fair",
    "great": "excellent",
    "bad": "poor",
    "moderate": "fair",
}


class LLMEvidenceRef(BaseModel):
    source_type: str = Field(..., description="Source of the evidence")
    source_id: str | None = Field(
        None, description="The GitLab Note ID or other identifier (if applicable)"
    )
    snippet: str | None = Field(
        None, description="Short redacted quote from the text used as evidence"
    )

    @field_validator("source_type", mode="before")
    @classmethod
    def normalize_source_type(cls, v: str) -> str:
        if isinstance(v, str):
            return _SOURCE_TYPE_MAP.get(v.lower().strip(), "general")
        return "general"


class LLMRiskFlag(BaseModel):
    flag: str = Field(..., description="Short identifier of the risk")
    description: str = Field(..., description="Explanation of why this is a risk")
    severity: Literal["low", "medium", "high"] = Field(..., description="Severity level")
    evidence: list[LLMEvidenceRef] = Field(
        default_factory=list, description="List of evidence references supporting this flag"
    )


class LLMStrength(BaseModel):
    """Positive observation about the student's work."""

    category: str = Field(
        ...,
        description="Category: communication, code_quality, teamwork, devops, testing",
    )
    description: str = Field(..., description="What the student did well")
    evidence: list[LLMEvidenceRef] = Field(default_factory=list)


class LLMImprovement(BaseModel):
    """Actionable improvement suggestion."""

    area: str = Field(
        ...,
        description="Area to improve: communication, code_quality, teamwork, devops, testing",
    )
    suggestion: str = Field(..., description="Specific actionable improvement suggestion")
    priority: Literal["low", "medium", "high"] = Field(default="medium")
    learning_resource: str | None = Field(
        None, description="Optional link/reference to learning material"
    )


class LLMDevOpsPractice(BaseModel):
    """Evaluation of a DevOps practice."""

    practice: str = Field(..., description="DevOps practice name")
    status: Literal["good", "needs_improvement", "missing", "not_applicable"] = Field(...)
    observation: str = Field(..., description="Brief observation about this practice")


class LLMCollaborationMetric(BaseModel):
    """Teamwork quality indicator."""

    metric: str = Field(..., description="Metric name")
    score: str = Field(..., description="Score: excellent, good, fair, or poor")
    detail: str = Field(..., description="Explanation of the score")
    evidence: list[LLMEvidenceRef] = Field(default_factory=list)

    @field_validator("score", mode="before")
    @classmethod
    def normalize_score(cls, v: str) -> str:
        if isinstance(v, str):
            return _SCORE_MAP.get(v.lower().strip(), "fair")
        return "fair"


class LLMAnalysisResult(BaseModel):
    summary: str = Field(..., description="Concise summary of the interaction/code")

    # Strengths - what the student did well
    strengths: list[LLMStrength] = Field(
        default_factory=list, description="Positive observations about the student's work"
    )

    # Risk flags - potential issues
    risk_flags: list[LLMRiskFlag] = Field(default_factory=list, description="Detected risks")

    # Improvements - actionable suggestions
    improvements: list[LLMImprovement] = Field(
        default_factory=list, description="Specific actionable improvement suggestions"
    )

    # DevOps practices evaluation
    devops_practices: list[LLMDevOpsPractice] = Field(
        default_factory=list, description="Evaluation of DevOps best practices"
    )

    # Teamwork quality
    collaboration_metrics: list[LLMCollaborationMetric] = Field(
        default_factory=list, description="Teamwork quality indicators"
    )

    # Questions for the teacher to ask
    recommended_questions: list[str] = Field(
        default_factory=list, description="Questions the teacher should ask the student"
    )

    # Learning tips for the student
    learning_tips: list[str] = Field(
        default_factory=list, description="Tips for the student to improve their skills"
    )

    grading_suggestion: str | None = Field(
        None, description="Optional grading hint based on course criteria context if available"
    )
    confidence_score: float = Field(
        ..., ge=0.0, le=1.0, description="Confidence score of the analysis (0.0 to 1.0)"
    )
    explanation: str = Field(
        ..., description="Explanation of the reasoning behind the analysis/confidence"
    )


class LLMAnalysisLog(BaseModel):
    id: int
    project_id: str  # UUID as string
    mr_iid: int | None
    target_type: str
    analysis_timestamp: datetime
    model_used: str
    structured_result: LLMAnalysisResult
    risk_score: float | None

    model_config = ConfigDict(from_attributes=True)

    @field_validator("project_id", mode="before")
    @classmethod
    def _coerce_uuid_to_str(cls, v: object) -> str:
        """Accept UUID objects from ORM and convert to string."""
        return str(v)


# Response model for API that includes GitLab URL for evidence linking
class LLMAnalysisResponse(BaseModel):
    analysis: LLMAnalysisResult
    gitlab_mr_url: str | None = Field(
        None, description="Base URL to MR for constructing evidence links"
    )
    note_url_template: str | None = Field(
        None, description="Template for note links, e.g. {base}#note_{id}"
    )
