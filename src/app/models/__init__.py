"""SQLAlchemy ORM models - import all for Alembic autogenerate."""

from app.models.assistant import AssistantTask, CourseAssistant
from app.models.audit_log import AuditLog
from app.models.background_job import BackgroundJob
from app.models.base import Base
from app.models.commit import Commit
from app.models.course import Course
from app.models.course_membership import CourseMembership
from app.models.course_settings import CourseSettings
from app.models.custom_check import CustomCheck
from app.models.email_log import EmailLog
from app.models.issue import Issue
from app.models.issue_note import IssueNote
from app.models.llm_log import LLMAnalysisLog
from app.models.membership_change import MembershipChange
from app.models.merge_request import MergeRequest
from app.models.metric_snapshot import MetricSnapshot
from app.models.mr_approval import MRApproval
from app.models.mr_diff import MergeRequestDiff
from app.models.mr_note import MRNote
from app.models.pipeline import Pipeline
from app.models.project import GitLabProject
from app.models.review_activity import ReviewActivity
from app.models.student import Student
from app.models.student_compliance_snapshot import StudentComplianceSnapshot
from app.models.support_comment import SupportComment
from app.models.support_form import SupportForm
from app.models.support_link import SupportLink
from app.models.support_ticket import SupportTicket
from app.models.team import Team
from app.models.team_member import TeamMember
from app.models.team_metric_snapshot import TeamMetricSnapshot
from app.models.user import User
from app.models.user_api_token import UserApiToken
from app.models.webhook_configuration import WebhookConfiguration, WebhookScope
from app.models.webhook_event import WebhookEvent

__all__ = [
    "AssistantTask",
    "AuditLog",
    "BackgroundJob",
    "Base",
    "Commit",
    "Course",
    "CourseAssistant",
    "CourseMembership",
    "CourseSettings",
    "CustomCheck",
    "EmailLog",
    "GitLabProject",
    "Issue",
    "IssueNote",
    "LLMAnalysisLog",
    "MRApproval",
    "MRNote",
    "MembershipChange",
    "MergeRequest",
    "MergeRequestDiff",
    "MetricSnapshot",
    "Pipeline",
    "ReviewActivity",
    "Student",
    "StudentComplianceSnapshot",
    "SupportComment",
    "SupportForm",
    "SupportLink",
    "SupportTicket",
    "Team",
    "TeamMember",
    "TeamMetricSnapshot",
    "User",
    "UserApiToken",
    "WebhookConfiguration",
    "WebhookEvent",
    "WebhookScope",
]
