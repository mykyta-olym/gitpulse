"""Compliance check types, data structures, and communication indicators.

Formulas Reference
------------------
Each compliance check maps to a course requirement:

  R01  Issue Ownership    : |assigned_issues| >= min_issues (default 1)
  R02  Branch Naming      : |authored| >= 1 AND (convention off OR
                            exists MR in authored: branch_naming_ok == True)
  R03  Test Changes       : exists MR in authored: has_test_changes == True
  R04  MR-Issue Link      : exists MR in authored: has_issue_link == True
  R05  MR Template        : exists MR in authored: template_compliant == True
  R06  Review Received    : |{n.author_id : n in notes_on_own_mr}| >= min_reviews_per_mr
  R07  Review Duty        : |{r.merge_request_id : r in reviews_given, r.is_meaningful}|
                            >= min_distinct_mrs_reviewed
  R08  Response Quality   : response_rate == 1.0 AND |responses_with_commit_ref| >= 1
  R09  Approval Received  : |approvals_on_own_mr| >= min_reviews_per_mr
  R10  Merged by Author   : exists MR in authored: state=="merged" AND merged_by_id == student_id
  R11  Closure State      : (exists MR in authored: state in {merged,closed}) AND
                            (exists issue in assigned: state=="closed")
  R12  Pipeline Health    : exists pipeline in pipelines: status=="success" AND has_test_job==True
  R13  Commit Quality     : |web_editor_commits| / |total_commits| <= max_web_editor_ratio

Traffic Light Thresholds
------------------------
  GREEN  : weighted_score >= green_threshold  (default 0.80)
  YELLOW : weighted_score >= yellow_threshold (default 0.50)
  RED    : weighted_score < yellow_threshold

Communication Indicators (non-scoring, diagnostic)
---------------------------------------------------
  median_first_response_h : median hours from MR creation to first reviewer note
  median_review_rounds    : median |{discussion_id}| per MR (iteration depth)
  discussion_resolution_pct: % of resolvable discussions marked resolved
  review_word_depth       : avg word count across all reviewer notes on own MRs
"""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING
from uuid import UUID

if TYPE_CHECKING:
    from app.models.commit import Commit
    from app.models.issue import Issue
    from app.models.merge_request import MergeRequest
    from app.models.mr_approval import MRApproval
    from app.models.mr_note import MRNote
    from app.models.pipeline import Pipeline
    from app.models.review_activity import ReviewActivity


@dataclass
class CheckResult:
    """Result of a single compliance check."""

    check_id: str  # e.g. "R01"
    name: str  # e.g. "Issue Ownership"
    passed: bool
    detail: str  # human-readable explanation
    weight: float = 0.0  # from CourseSettings; the score divides by the active total
    score: float = 0.0  # weight x pass_ratio (1.0 if passed, partial for some checks)
    # False for a built-in check the course switched off: it is reported, but
    # neither scored, counted nor listed as a failing check.
    enabled: bool = True


@dataclass
class CommunicationIndicators:
    """Non-scoring diagnostic metrics about review communication quality.

    These are stored alongside the snapshot but do NOT affect the weighted
    score or traffic light.  They help the teacher identify *how* the team
    communicates - not just *whether* they did.
    """

    # Response time: median hours from MR created_at to first reviewer note
    median_first_response_hours: float | None = None

    # Iteration depth: median count of distinct discussion threads per MR
    median_review_rounds: float | None = None

    # Resolution: fraction of resolvable discussions that are resolved
    discussion_resolution_pct: float | None = None

    # Review depth: average word count across all reviewer notes on own MRs
    review_word_depth: float | None = None

    # Author engagement: average word count of author responses
    author_response_word_depth: float | None = None

    # Time to merge: median hours from MR created_at to merged_at
    median_time_to_merge_hours: float | None = None


@dataclass
class StudentContext:
    """All data needed to evaluate one student's compliance.

    Per course rules each student must:
    - Self-assign >= min_issues issue(s) (configurable, default 1)
    - Create >= 1 MR implementing that issue
    - Review >= min_distinct_mrs_reviewed peer MRs (configurable, default 2)
    """

    student_id: UUID
    gitlab_user_id: int
    gitlab_username: str

    # Issues assigned to this student in the team's projects
    issues_assigned: list["Issue"] = field(default_factory=list)

    # MRs authored by this student
    mrs_authored: list["MergeRequest"] = field(default_factory=list)

    # ReviewActivity records where this student is the reviewer (on others' MRs)
    reviews_given: list["ReviewActivity"] = field(default_factory=list)

    # Notes on this student's own MR(s) by others (non-system, non-author,
    # not by a bot account)
    notes_on_own_mr: list["MRNote"] = field(default_factory=list)

    # How many notes on own MR(s) a bot account wrote (left out above)
    bot_notes_on_own_mr: int = 0

    # Notes by this student on their own MR(s) (responses to reviewers)
    own_responses: list["MRNote"] = field(default_factory=list)

    # MRApproval records on this student's MR(s)
    approvals_on_own_mr: list["MRApproval"] = field(default_factory=list)

    # Distinct GitLab user IDs who approved this student's own MR(s), derived
    # from the permanent "approved this merge request" system notes (net of any
    # later "unapproved" note). GitLab CLEARS the /approvals list once an MR is
    # merged and its branch deleted, so a re-sync clobbers approvals_on_own_mr
    # to empty; these system notes survive, keeping R09 correct for merged MRs.
    approval_note_approver_ids: set[int] = field(default_factory=set)

    # Pipelines on this student's MR branch(es)
    pipelines: list["Pipeline"] = field(default_factory=list)

    # Commits authored by this student
    commits: list["Commit"] = field(default_factory=list)

    # All MR notes across the team (needed for communication indicators)
    all_team_notes: list["MRNote"] = field(default_factory=list)
    # Total number of non-teacher active team members (for solo-team detection)
    team_member_count: int = 1
