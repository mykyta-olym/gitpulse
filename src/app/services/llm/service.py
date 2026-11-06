import asyncio
import json
import logging
import re
import uuid
from typing import Any, cast

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.models.course import Course
from app.models.llm_log import LLMAnalysisLog
from app.models.merge_request import MergeRequest
from app.models.mr_diff import MergeRequestDiff
from app.models.mr_note import MRNote
from app.models.pipeline import Pipeline
from app.models.project import GitLabProject
from app.models.team import Team
from app.schemas.llm import LLMAnalysisResult
from app.services.llm.redaction import RedactionService
from app.services.llm.types import LLMResponse

logger = logging.getLogger(__name__)

_GROQ_DEFAULT_BASE_URL = "https://api.groq.com/openai/v1"

__all__ = ["DEFAULT_ANALYSIS_PROMPT", "LLMResponse", "LLMService", "PROMPT_PRESETS"]  # noqa: RUF022

# -- Common output rules & JSON schema shared by all presets --
_OUTPUT_RULES_AND_SCHEMA = """
== OUTPUT RULES ==
1. Output ONLY valid JSON matching the schema below.
2. For every strength and risk_flag, provide evidence with source_type and snippet.
3. source_type MUST be one of: "note", "description", "title", "diff", "commit", "general"
4. Be balanced - always find both strengths AND areas for improvement.
5. confidence_score: Float 0.0-1.0 (higher if more data available).
6. explanation: 3-5 sentences summarizing your assessment reasoning.
7. If data is limited, still analyze what's available and note limitations.

== ACCURACY AND EVIDENCE RULES ==
- Reference ONLY data explicitly present in the provided MR context.
- NEVER invent, guess, or assume information not in the context.
- When citing a review comment, quote the actual commenter alias (e.g. Participant_1)
  and paraphrase their actual words - do NOT fabricate quotes.
- When citing files changed, use only filenames listed in the context.
- When referencing commit messages, use only messages present in the diffs or metadata.
- If the MR has no test changes (has_test_changes: false), do NOT claim tests were written.
- If pipeline status is null, do NOT claim the pipeline passed or failed.
- If approvals_count is 0, state that no approvals were obtained.
- source_id should reference a concrete artifact when possible:
  a note ID for comments, a file path for diffs, "metadata" for MR metadata fields.
- If you cannot find enough evidence for a claim, omit it rather than fabricate.

== EVIDENCE SNIPPET RULES ==
Evidence snippets MUST be human-readable descriptions that cite specific artifacts.
BAD examples (do NOT do this):
  - "class AppError(Exception):"
  - "branch_naming_ok: True"
  - "Closes #5"
GOOD examples:
  - "Student implemented custom AppError exception class for structured error handling"
  - "Branch '3-implement-flagging' correctly follows the issue-XX-description naming convention"
  - "Reviewer Participant_2 commented: 'Consider checking for null before accessing board[row][col]' - a substantive review pointing out a potential null pointer issue"
  - "MR description states 'Implements mine flagging feature as described in Issue #3, adds toggle_flag() function and 8 unit tests covering edge cases'"
  - "Diff shows new file tests/test_flagging.py with 45 lines added, containing 3 test functions"
Always DESCRIBE the evidence in context rather than dumping raw text.
Always specify WHERE the evidence comes from (which comment, which file, which field).

== JSON SCHEMA ==
{
  "summary": "STRING - 3-4 sentence overview focusing on process quality, code review, and learning outcomes",
  "strengths": [
    {
      "category": "communication|code_quality|collaboration|devops|testing|process",
      "description": "STRING - what was done well",
      "evidence": [{"source_type": "note|description|title|diff|commit|general", "source_id": "STRING or null", "snippet": "STRING - described evidence"}]
    }
  ],
  "risk_flags": [
    {
      "flag": "STRING - short identifier",
      "description": "STRING - why this is a concern for grading",
      "severity": "low|medium|high",
      "evidence": [{"source_type": "note|description|title|diff|commit|general", "source_id": "STRING or null", "snippet": "STRING"}]
    }
  ],
  "improvements": [
    {
      "area": "communication|code_quality|collaboration|devops|testing|process",
      "suggestion": "STRING - specific actionable improvement tied to course objectives",
      "priority": "low|medium|high",
      "learning_resource": "STRING or null"
    }
  ],
  "devops_practices": [
    {"practice": "STRING", "status": "good|needs_improvement|missing|not_applicable", "observation": "STRING"}
  ],
  "collaboration_metrics": [
    {"metric": "STRING", "score": "excellent|good|fair|poor", "detail": "STRING", "evidence": [{"source_type": "note|description|title|diff|commit|general", "source_id": "STRING or null", "snippet": "STRING - described evidence"}]}
  ],
  "recommended_questions": ["STRING"],
  "learning_tips": ["STRING"],
  "grading_suggestion": "STRING - holistic grading assessment with specific reasoning",
  "confidence_score": FLOAT,
  "explanation": "STRING - 3-5 sentences explaining your reasoning"
}"""

# -- Analysis area instructions per course type --

_DEFAULT_ANALYSIS_AREAS = """
== ANALYSIS AREAS ==

1. **STRENGTHS** - What the student did well (find 2-4 concrete examples):
   - MR description quality: does it explain WHAT was changed, WHY, and HOW?
   - Issue linkage: is the MR properly linked to the assigned GitLab Issue?
   - Branch naming: does the branch follow convention (e.g. feature/issue-XX-description)?
   - Code quality: proper structure, naming, error handling in the implementation
   - Unit tests: did they write tests? Do tests actually verify the functionality?
   - Commit quality: small focused commits with descriptive messages (not "fix", "update")
   - Review participation: did they review others' MRs with useful, constructive feedback?
   - Responsiveness: did they respond to review comments and fix issues?
   - Git workflow: proper use of branches, no force-pushes, clean merge

2. **RISK FLAGS** - Issues the teacher should investigate (be thorough):
   - Shallow or missing MR description (just a title, no explanation)
   - No unit tests or trivial tests that don't actually test anything
   - Self-merged without getting 2 reviews/approvals
   - No issue link or wrong issue referenced
   - Ignored or dismissed review comments without explanation
   - Copy-pasted or model-generated code without understanding
   - Force-push that destroyed review history
   - Minimal or no code review activity on others' MRs
   - Toxic, dismissive, or empty review comments (e.g. "ok", "LGTM" with no substance)
   - Pipeline failures not fixed before merge
   - Very large unfocused MR mixing multiple concerns
   - Suspicious patterns: identical comments across MRs, unrealistic timing

3. **IMPROVEMENTS** - Specific, actionable suggestions (2-5):
   - Be VERY specific: "Add edge case tests for empty board in mark_mine()" not just "Add tests"
   - Connect each to course learning objectives
   - Include priority (high/medium/low)

4. **CODE REVIEW QUALITY** - Deep analysis of review comments:
   Evaluate ALL comments on the MR. For each reviewer, assess:
   - Are comments substantive? (pointing out real issues, suggesting alternatives)
   - Or superficial? ("looks good", "ok", "+1" without explanation)
   - Do they suggest specific improvements with reasoning?
   - Is the tone constructive and professional?
   - Did the author respond to each comment and either fix the issue or explain why not?
   - Are there references to specific commits where fixes were applied?
   This is CRITICAL for grading - comment quality directly affects score.

5. **DEVOPS PRACTICES** - Evaluate each:
   - branch_naming: follows issue-XX-description convention?
   - mr_description: explains what/why/how clearly?
   - code_review_participation: received AND gave meaningful reviews?
   - ci_pipeline_usage: pipeline green before merge? Tests pass?
   - issue_tracking: MR linked to issue correctly?
   - test_coverage: meaningful tests included?
   - commit_quality: small, focused, well-described commits?
   - merge_strategy: proper merge (not direct push to master)?
   - approval_process: merged only after required approvals?

6. **COLLABORATION METRICS** - Rate each (excellent/good/fair/poor):
   - communication_clarity: how well ideas are expressed in MR, comments, commits
   - feedback_responsiveness: how they handled review feedback (fixed issues, explained decisions)
   - review_quality: depth and helpfulness of reviews they gave to others
   - team_coordination: evidence of working with teammates, not in isolation
   - process_adherence: following the defined Git workflow (branch->MR->review->approve->merge)

7. **LEARNING TIPS** - 3-5 practical tips for the student:
   - Tied to specific observations from THIS MR
   - Focused on skills they can apply immediately
   - Connected to software engineering principles (Clean Code, testing, communication)

8. **QUESTIONS FOR TEACHER** - 3-4 questions to ask the student:
   - To verify they understand their own code changes
   - To check if they wrote tests themselves (vs copy-paste)
   - To assess their understanding of the review process
   - To explore their teamwork with teammates

9. **GRADING SUGGESTION** - Brief assessment for the teacher:
   - Consider: implementation quality, test quality, code review quality (given AND received),
     communication in MR/comments, Git workflow adherence
   - Flag any red flags that should affect scoring"""

_ZSI_ANALYSIS_AREAS = """
== ANALYSIS AREAS (Software Engineering Fundamentals) ==

This is a Software Engineering Fundamentals course. Students learn version control (Git),
requirements analysis, conceptual design, automated testing, code review, teamwork,
and CI/CD. Language: C (gcc, make). Evaluate with emphasis on engineering practices and
learning progression.

1. **STRENGTHS** - What the student did well (find 2-4 concrete examples):
   - MR description: does it explain WHAT was changed, WHY, and HOW? Is it structured
     with required sections (Popis/Zmeny/Testovanie or Description/Changes/Testing)?
   - Issue linkage: is the MR properly linked to the assigned GitLab Issue?
   - Branch naming: follows convention (e.g. feature/issue-XX-description)?
   - C code quality: proper structure, header guards, memory management (malloc/free),
     meaningful variable/function names, error handling (return codes)
   - Unit tests: did they write tests using a framework (check, CUnit)? Do tests cover
     edge cases (empty input, boundary values, NULL pointers)?
   - Makefile quality: properly structured build targets, clean target, test target
   - Commit quality: small focused commits with descriptive messages
   - Code review: substantive reviews pointing out real issues (memory leaks, logic errors)
   - Requirements traceability: does the implementation match the issue requirements?

2. **RISK FLAGS** - Issues the teacher should investigate:
   - Shallow or missing MR description (no required sections)
   - No unit tests or trivial tests that don't verify real behavior
   - Self-merged without getting 2 reviews/approvals
   - Memory-related issues: missing free(), buffer overflows, dangling pointers
   - No issue link or wrong issue referenced
   - Ignored or dismissed review comments without explanation
   - Copy-pasted or model-generated code without understanding (especially C patterns)
   - Force-push that destroyed review history
   - Missing or broken Makefile (no test target, hardcoded paths)
   - Minimal or superficial code reviews (e.g. "ok", "LGTM")
   - Suspicious patterns: identical code/comments across team members
   - Pipeline failures not fixed before merge
   - Printf debugging left in code instead of proper tests

3. **IMPROVEMENTS** - Specific, actionable suggestions (2-5):
   - Be VERY specific: "Add edge case test for empty board in mark_mine()" not just "Add tests"
   - Connect each to course learning objectives (testing, clean code, requirements)
   - Consider C-specific improvements: const correctness, struct usage, modular design
   - Include priority (high/medium/low)

4. **CODE REVIEW QUALITY** - Deep analysis of review comments:
   Evaluate ALL comments on the MR. For each reviewer, assess:
   - Are comments substantive? (pointing out logic errors, memory issues, missing tests)
   - Or superficial? ("looks good", "ok", "+1" without explanation)
   - Do they reference specific lines of code with reasoning?
   - Is the tone constructive and professional?
   - Did the author respond to each comment and either fix or explain?
   This is CRITICAL for grading - review quality directly affects score.

5. **DEVOPS PRACTICES** - Evaluate each:
   - branch_naming: follows issue-XX-description convention?
   - mr_description: has required sections, explains what/why/how?
   - code_review_participation: received AND gave meaningful reviews?
   - ci_pipeline_usage: pipeline green before merge? make test passes?
   - issue_tracking: MR linked to issue correctly?
   - test_coverage: meaningful unit tests with edge cases?
   - commit_quality: small, focused, well-described commits?
   - merge_strategy: proper merge (not direct push to master)?
   - approval_process: merged only after required approvals?

6. **COLLABORATION METRICS** - Rate each (excellent/good/fair/poor):
   - communication_clarity: how well ideas are expressed in MR, comments, commits
   - feedback_responsiveness: how they handled review feedback
   - review_quality: depth and helpfulness of reviews given to others
   - team_coordination: evidence of working with teammates
   - process_adherence: following the defined Git workflow

7. **LEARNING TIPS** - 3-5 practical tips for the student:
   - Tied to specific observations from THIS MR
   - Focused on C programming and software engineering skills
   - Connected to principles: Clean Code, defensive programming, testing discipline

8. **QUESTIONS FOR TEACHER** - 3-4 questions to ask the student:
   - To verify they understand their own C code (pointer usage, memory management)
   - To check if they wrote tests themselves (vs copy-paste from examples)
   - To assess conceptual design understanding (data structures, algorithms chosen)
   - To explore their requirements analysis process

9. **GRADING SUGGESTION** - Brief assessment for the teacher:
   - Consider: implementation quality, test quality (coverage + edge cases),
     code review quality, MR description, Git workflow adherence
   - Flag any red flags that should affect scoring"""

_DEVOPS_ANALYSIS_AREAS = """
== ANALYSIS AREAS (DevOps Fundamentals) ==

This is a DevOps Fundamentals course. Students learn CI/CD pipelines, version control,
containerization, automation, monitoring, and teamwork through practical
GitLab-based workflows. Evaluate with emphasis on DevOps culture and automation practices.

1. **STRENGTHS** - What the student did well (find 2-4 concrete examples):
   - MR description: explains WHAT was changed, WHY, and HOW? Well-structured?
   - CI/CD pipeline: properly configured .gitlab-ci.yml with meaningful stages
     (build, test, lint, deploy)? Pipeline passes before merge?
   - Containerization: proper Dockerfile (multi-stage builds, minimal base images,
     non-root user, .dockerignore)? Docker Compose for multi-service setups?
   - Automation: scripts for repetitive tasks, proper use of CI variables and artifacts
   - Branch naming: follows convention (e.g. feature/issue-XX-description)?
   - Infrastructure as Code: configuration managed in version control, not manual
   - Testing in pipeline: automated tests run in CI, test reports generated
   - Code review: substantive reviews on CI/CD configs, Dockerfiles, automation scripts
   - Monitoring/observability: health checks, logging configuration, metrics

2. **RISK FLAGS** - Issues the teacher should investigate:
   - No CI/CD pipeline or broken pipeline not fixed before merge
   - Hardcoded secrets, credentials, or API keys in code/configs
   - Dockerfile anti-patterns: running as root, no .dockerignore, bloated images,
     installing unnecessary packages, not using multi-stage builds
   - Pipeline misconfigurations: missing stages, no test stage, allow_failure on critical jobs
   - Self-merged without reviews/approvals
   - Missing or shallow MR description
   - Manual steps that should be automated (manual deployments, manual tests)
   - No issue link or wrong issue referenced
   - Ignored review comments without explanation
   - Force-push that destroyed review history
   - Infrastructure drift: configs not matching actual setup
   - Suspicious patterns: identical pipeline configs copy-pasted without understanding

3. **IMPROVEMENTS** - Specific, actionable suggestions (2-5):
   - Be VERY specific: "Add a lint stage to .gitlab-ci.yml using hadolint for Dockerfile validation"
   - Connect each to DevOps principles (automation, reliability, fast feedback)
   - Consider DevOps-specific improvements: pipeline optimization, container security,
     deployment strategies (blue-green, canary), monitoring
   - Include priority (high/medium/low)

4. **CODE REVIEW QUALITY** - Deep analysis of review comments:
   Evaluate ALL comments on the MR. For each reviewer, assess:
   - Are comments substantive? (pointing out CI/CD issues, security concerns, missing automation)
   - Or superficial? ("looks good", "ok" without explanation)
   - Do they suggest specific improvements with reasoning?
   - Is the tone constructive and professional?
   - Did the author respond to each comment and either fix or explain?
   This is CRITICAL for grading - review quality directly affects score.

5. **DEVOPS PRACTICES** - Evaluate each:
   - branch_naming: follows convention?
   - mr_description: explains what/why/how clearly?
   - code_review_participation: received AND gave meaningful reviews?
   - ci_pipeline_usage: well-structured pipeline, green before merge?
   - issue_tracking: MR linked to issue correctly?
   - test_coverage: automated tests in CI pipeline?
   - commit_quality: small, focused, well-described commits?
   - merge_strategy: proper merge (not direct push to master)?
   - approval_process: merged only after required approvals?
   - containerization: proper Docker practices followed?
   - automation: manual processes eliminated where possible?
   - security: no secrets in code, proper access controls?

6. **COLLABORATION METRICS** - Rate each (excellent/good/fair/poor):
   - communication_clarity: how well ideas are expressed in MR, comments, commits
   - feedback_responsiveness: how they handled review feedback
   - review_quality: depth and helpfulness of reviews given to others
   - team_coordination: evidence of working with teammates
   - process_adherence: following the defined DevOps workflow

7. **LEARNING TIPS** - 3-5 practical tips for the student:
   - Tied to specific observations from THIS MR
   - Focused on DevOps skills they can apply immediately
   - Connected to DevOps principles: automation, reliability, fast feedback, security

8. **QUESTIONS FOR TEACHER** - 3-4 questions to ask the student:
   - To verify they understand their CI/CD pipeline configuration
   - To check understanding of containerization choices (base image, stages)
   - To assess their automation mindset (what else could be automated?)
   - To explore their teamwork and code review practices

9. **GRADING SUGGESTION** - Brief assessment for the teacher:
   - Consider: CI/CD quality, containerization, automation, code review quality,
     communication, DevOps workflow adherence
   - Flag any red flags that should affect scoring"""

# -- Built-in prompt presets per course type --
# Each preset = analysis areas + output rules + JSON schema.
DEFAULT_ANALYSIS_PROMPT = (_DEFAULT_ANALYSIS_AREAS + _OUTPUT_RULES_AND_SCHEMA).lstrip()

PROMPT_PRESETS: dict[str, str] = {
    "default": DEFAULT_ANALYSIS_PROMPT,
    "zsi": (_ZSI_ANALYSIS_AREAS + _OUTPUT_RULES_AND_SCHEMA).lstrip(),
    "devops": (_DEVOPS_ANALYSIS_AREAS + _OUTPUT_RULES_AND_SCHEMA).lstrip(),
}


def _alias(aliases: dict[str, str], author_id: Any) -> str:
    """An author's anonymous handle (Participant_1, Participant_2, ...), numbered
    in order of appearance."""
    key = str(author_id) if author_id else "unknown"
    return aliases.setdefault(key, f"Participant_{len(aliases) + 1}")


def _mr_metadata(mr: MergeRequest, pipeline: Pipeline | None, participants: int) -> dict[str, Any]:
    return {
        "state": mr.state,
        "source_branch": mr.source_branch,
        "target_branch": mr.target_branch,
        "files_changed": mr.files_changed,
        "lines_added": mr.lines_added,
        "lines_removed": mr.lines_removed,
        "has_test_changes": mr.has_test_changes,
        "has_issue_link": mr.has_issue_link,
        "linked_issue_iid": mr.linked_issue_iid,
        "branch_naming_ok": mr.branch_naming_ok,
        "template_compliant": mr.template_compliant,
        "approvals_count": mr.approvals_count,
        "approvals_required": mr.approvals_required,
        "pipeline_status": pipeline.status if pipeline else None,
        "pipeline_has_tests": pipeline.has_test_job if pipeline else None,
        "pipeline_test_status": pipeline.test_job_status if pipeline else None,
        "created_at": str(mr.created_at) if mr.created_at else None,
        "merged_at": str(mr.merged_at) if mr.merged_at else None,
        "closed_at": str(mr.closed_at) if mr.closed_at else None,
        "author_is_merger": (
            mr.author_gitlab_id == mr.merged_by_gitlab_id
            if mr.author_gitlab_id and mr.merged_by_gitlab_id
            else None
        ),
        "participant_count": participants,
    }


async def _issue_context(session: AsyncSession, mr: MergeRequest, aliases: dict[str, str]) -> str:
    """The MR's linked issue: title, state, labels, description and its first
    comments (redacted, authors anonymised like the MR's)."""
    if not mr.linked_issue_id:
        return ""
    from app.models.issue import Issue
    from app.models.issue_note import IssueNote

    issue_stmt = select(Issue).where(Issue.id == mr.linked_issue_id)
    issue_row = (await session.execute(issue_stmt)).scalar_one_or_none()
    if not issue_row:
        return ""
    issue_context = "\nLinked Issue:\n"
    issue_context += (
        f"- Issue #{issue_row.gitlab_iid}: {RedactionService.redact(issue_row.title or '')}\n"
    )
    issue_context += f"- State: {issue_row.state}\n"
    if issue_row.labels:
        issue_context += f"- Labels: {', '.join(issue_row.labels)}\n"
    if issue_row.description:
        desc_redacted = RedactionService.redact(issue_row.description[:500])
        issue_context += f"- Description: {desc_redacted}\n"
    inotes_stmt = (
        select(IssueNote)
        .where(IssueNote.issue_id == issue_row.id, IssueNote.is_system.is_(False))
        .order_by(IssueNote.created_at)
        .limit(20)
    )
    inotes = list((await session.execute(inotes_stmt)).scalars())
    if inotes:
        issue_context += f"- Comments ({len(inotes)}):\n"
        for inote in inotes:
            issue_context += (
                f"  [{_alias(aliases, inote.author_id)}]: "
                f"{RedactionService.redact(inote.body or '')[:300]}\n"
            )
    return issue_context


async def _review_context(session: AsyncSession, project_id: uuid.UUID, mr: MergeRequest) -> str:
    """The reviews the MR's author gave on OTHER MRs of the same project."""
    if not mr.author_id:
        return ""
    from app.models.review_activity import ReviewActivity

    rev_stmt = (
        select(ReviewActivity)
        .join(MergeRequest, MergeRequest.id == ReviewActivity.merge_request_id)
        .where(
            ReviewActivity.reviewer_id == mr.author_id,
            MergeRequest.project_id == project_id,
            MergeRequest.id != mr.id,
        )
        .order_by(ReviewActivity.last_note_at.desc().nulls_last())
        .limit(10)
    )
    rev_rows = list((await session.execute(rev_stmt)).scalars())
    if not rev_rows:
        return ""
    meaningful = sum(1 for r in rev_rows if r.is_meaningful)
    total_words_given = sum(r.total_words for r in rev_rows)
    return (
        f"\nAuthor's review activity on other MRs in this project:\n"
        f"- Reviews given: {len(rev_rows)} (meaningful: {meaningful})\n"
        f"- Total review words: {total_words_given}\n"
    )


async def _custom_checks_context(session: AsyncSession, course_id: uuid.UUID) -> str:
    """The course's active custom checks, for the model to take into account."""
    from app.models.custom_check import CustomCheck

    cc_stmt = (
        select(CustomCheck.check_code, CustomCheck.name, CustomCheck.description)
        .where(
            CustomCheck.course_id == course_id,
            CustomCheck.is_active.is_(True),
        )
        .order_by(CustomCheck.sort_order, CustomCheck.check_code)
    )
    cc_rows = (await session.execute(cc_stmt)).all()
    if not cc_rows:
        return ""
    cc_lines = [f"- {r.check_code}: {r.name}" for r in cc_rows]
    return (
        "\nThis course also has custom compliance checks:\n"
        + "\n".join(cc_lines)
        + "\nConsider these additional requirements when analyzing the MR.\n"
    )


class LLMService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.enabled = settings.llm_analysis_enabled
        self.provider = settings.llm_provider.lower()

    async def analyze_mr(
        self, session: AsyncSession, project_id: uuid.UUID, mr_iid: int
    ) -> LLMAnalysisResult | None:
        """
        Analyzes a Merge Request's communication and metadata using LLM.
        """
        if not self.enabled:
            logger.info("LLM feature disabled.")
            return None

        stmt = select(MergeRequest).where(
            MergeRequest.project_id == project_id,
            MergeRequest.gitlab_iid == mr_iid,
        )
        result = await session.execute(stmt)
        mr = result.scalars().first()

        if not mr:
            logger.error("MR %s in project %s not found for analysis", mr_iid, project_id)
            return None

        context_text = await self._mr_context(session, project_id, mr)
        system_prompt = await self._system_prompt(session, project_id)
        return await self._ask(session, project_id, mr_iid, system_prompt, context_text)

    async def _mr_context(
        self, session: AsyncSession, project_id: uuid.UUID, mr: MergeRequest
    ) -> str:
        """The MR as the model reads it (minimized, authors anonymised), with
        its linked issue and its author's review activity appended."""
        aliases: dict[str, str] = {}
        notes = (
            await session.execute(select(MRNote).where(MRNote.merge_request_id == mr.id))
        ).scalars()
        comments_data = [
            {
                "id": str(note.gitlab_note_id),
                "body": note.body,
                "author": _alias(aliases, note.author_id),
                "created_at": str(note.created_at),
            }
            for note in notes
            if not note.is_system
        ]

        pipeline_stmt = (
            select(Pipeline)
            .where(Pipeline.merge_request_id == mr.id)
            .order_by(Pipeline.created_at.desc().nulls_last(), Pipeline.id.desc())
            .limit(1)
        )
        pipeline = (await session.execute(pipeline_stmt)).scalar_one_or_none()

        diff_stmt = select(MergeRequestDiff).where(MergeRequestDiff.merge_request_id == mr.id)
        diffs = [
            {
                "file_path": diff.file_path,
                "diff": diff.diff,
            }
            for diff in (await session.execute(diff_stmt)).scalars()
        ]

        context_text = RedactionService.minimize_mr_context(
            title=mr.title or "",
            description=mr.description or "",
            comments=comments_data,
            filenames=list(mr.changed_files or []),
            metadata=_mr_metadata(mr, pipeline, participants=len(aliases)),
            diffs=diffs,
            max_diff_chars=self.settings.llm_max_diff_chars,
        )
        issue_context = await _issue_context(session, mr, aliases)
        review_context = await _review_context(session, project_id, mr)
        if issue_context:
            context_text += "\n" + issue_context
        if review_context:
            context_text += "\n" + review_context
        return context_text

    async def _system_prompt(self, session: AsyncSession, project_id: uuid.UUID) -> str:
        """The course's teaching-assistant prompt: its domain, custom checks,
        analysis preset (or custom prompt) and the answer language."""
        course_stmt = (
            select(Course.id, Course.code, Course.name, Course.description)
            .join(Team, Team.course_id == Course.id)
            .join(GitLabProject, GitLabProject.team_id == Team.id)
            .where(GitLabProject.id == project_id)
        )
        course_row = (await session.execute(course_stmt)).first()
        course_name = course_row.name if course_row else "DevOps / Software Engineering"
        course_code = course_row.code.upper().strip() if course_row and course_row.code else ""
        course_desc = (
            course_row.description.strip() if course_row and course_row.description else ""
        )

        llm_course_type = "default"
        llm_resource_urls: list[dict[str, str]] = []
        llm_custom_prompt: str | None = None
        if course_row:
            from app.models.course_settings import CourseSettings

            cs_stmt = select(CourseSettings).where(CourseSettings.course_id == course_row.id)
            cs_row = (await session.execute(cs_stmt)).scalar_one_or_none()
            if cs_row:
                llm_course_type = cs_row.llm_course_type or "default"
                llm_resource_urls = cs_row.llm_resource_urls or []
                llm_custom_prompt = cs_row.llm_custom_prompt or None

        # Build dynamic course context (fetches configured URLs)
        from app.services.llm.course_context import build_course_context

        course_domain = await build_course_context(
            course_type=llm_course_type,
            resource_urls=llm_resource_urls,
            course_name=course_name,
            course_description=course_desc,
        )
        custom_checks_context = (
            await _custom_checks_context(session, course_row.id) if course_row else ""
        )

        prompt_header = (
            f'You are an expert Teaching Assistant for "{course_name}" ({course_code}).\n'
            f"{course_domain}"
            f"{custom_checks_context}"
            "\nYour role: help the TEACHER evaluate student work on this MR. "
            "Focus on what matters for grading: process quality, communication, "
            "code review depth, test coverage, and Git workflow adherence.\n"
            "Be specific, cite evidence from the MR data, and give actionable feedback.\n"
            "IMPORTANT: Only reference information that is explicitly present in the "
            "MR data provided below. Do not invent file names, comments, or metrics. "
            "If data is insufficient for a conclusion, state that explicitly."
        )

        if llm_custom_prompt:
            analysis_body = llm_custom_prompt
        else:
            analysis_body = PROMPT_PRESETS.get(llm_course_type, DEFAULT_ANALYSIS_PROMPT)
        return prompt_header + "\n" + analysis_body + self._language_rule()

    def _language_rule(self) -> str:
        """The mandatory answer-language instruction.

        English unless configured - NOT the UI locale: teachers may use a Slovak
        UI but want the analysis in English (or vice versa). It is always added,
        so the model does not switch to the language of the content it reads.
        """
        lang = self.settings.llm_response_language.strip() or "en"
        lang_names: dict[str, str] = {
            "sk": "Slovak",
            "en": "English",
            "cs": "Czech",
            "de": "German",
        }
        lang_full = lang_names.get(lang, lang)
        return (
            f"\n\n== LANGUAGE (MANDATORY) ==\n"
            f"CRITICAL: Write ALL output text values in {lang_full} ({lang}). "
            f"This includes: summary, descriptions, suggestions, tips, explanations, "
            f"grading_suggestion, observations, details, snippets. "
            f"Even if the MR content, comments, or code is in a different language, "
            f"your analysis text MUST be in {lang_full}. "
            f"Only keep these in English: JSON keys, enum values "
            f"(good/fair/poor/excellent, low/medium/high, category names like "
            f"communication/code_quality/collaboration/devops/testing/process), "
            f"source_type values (note/description/title/diff/commit/general), "
            f"and practice/metric names."
        )

    async def _ask(
        self,
        session: AsyncSession,
        project_id: uuid.UUID,
        mr_iid: int,
        system_prompt: str,
        context_text: str,
    ) -> LLMAnalysisResult | None:
        """Call the model, retrying an unparseable answer, and log the result."""
        max_attempts = self.settings.llm_max_retries
        last_exc: Exception | None = None

        for attempt in range(max_attempts):
            try:
                response = await self._call_llm(system_prompt, context_text)
                content = self._answer_text(response)
                # Validate with Pydantic - this enforces strict schema
                analysis_result = LLMAnalysisResult(**self._clean_and_parse_json(content))
                session.add(
                    LLMAnalysisLog(
                        project_id=project_id,
                        mr_iid=mr_iid,
                        target_type="mr",
                        model_used=self.settings.llm_model,
                        structured_result=analysis_result.model_dump(),
                        risk_score=self._calculate_risk(analysis_result),
                        raw_prompt_redacted=context_text if self.settings.llm_debug_mode else None,
                        raw_response=content if self.settings.llm_debug_mode else None,
                    )
                )
                await session.flush()
                return analysis_result

            except (json.JSONDecodeError, ValueError, KeyError, ValidationError) as exc:
                last_exc = exc
                if attempt < max_attempts - 1:
                    logger.warning(
                        "LLM parse error for MR %s#%s (attempt %d/%d), retrying: %s",
                        project_id,
                        mr_iid,
                        attempt + 1,
                        max_attempts,
                        exc,
                    )
                    continue
                logger.error(
                    "LLM response parsing failed for MR %s#%s: %s", project_id, mr_iid, exc
                )
                raise
            except Exception:
                logger.exception("LLM analysis failed for MR %s#%s", project_id, mr_iid)
                raise

        # Fallback when max_retries == 0
        if last_exc:
            raise last_exc
        return None

    def _answer_text(self, response: LLMResponse) -> str:
        """The answer's text; a ValueError when there is none."""
        if not response.choices:
            raise ValueError("LLM returned empty choices")
        content = response.choices[0].message.content
        if not content:
            raise ValueError("LLM returned empty content")

        # Detect truncated response (likely max_tokens too low)
        content_stripped = content.rstrip()
        if not content_stripped.endswith("}"):
            logger.warning(
                "LLM response appears truncated (ends with %r), "
                "consider increasing LLM_MAX_TOKENS (current: %d)",
                content_stripped[-20:],
                self.settings.llm_max_tokens,
            )
        return cast(str, content)

    async def _call_llm(self, system_prompt: str, user_content: str) -> LLMResponse:
        """Call the configured LLM provider."""
        if self.provider == "mock":
            return self._call_mock(system_prompt, user_content)
        if self.provider == "gemini":
            return await self._call_gemini(system_prompt, user_content)
        if self.provider == "groq":
            return await self._call_groq(system_prompt, user_content)
        # Default: OpenAI-compatible (openai, azure, or custom base_url)
        return await self._call_openai(system_prompt, user_content)

    def _call_mock(self, system_prompt: str, _user_content: str) -> LLMResponse:
        """Answer locally, without a provider, for development and tests.

        Every LLM-backed feature is otherwise unexercisable whenever the real
        account is unreachable or out of quota - the failure looks identical to
        a broken integration, which makes it impossible to tell whether the
        surrounding code works. Setting ``LLM_PROVIDER=mock`` returns shaped,
        schema-valid answers so those paths can be driven end to end.

        The answer is derived from the prompt so it stays plausible: a request
        for check definitions gets check definitions, anything else gets a
        generic analysis object.
        """
        prompt = system_prompt.lower()
        if "evaluation_rule" in prompt or "check definitions" in prompt:
            count = 3
            match = re.search(r"generate exactly (\d+)", prompt)
            if match:
                count = max(1, min(int(match.group(1)), 20))
            body = json.dumps(
                [
                    {
                        "name": f"Mock check {i + 1}",
                        "description": ("Generated by the mock LLM provider for local testing."),
                        "category": "custom",
                        "weight": 0.05,
                        "evaluation_rule": {
                            "type": "count",
                            "entity": "merge_request",
                            "operator": ">=",
                            "threshold": i + 1,
                            "partial_scoring": False,
                        },
                    }
                    for i in range(count)
                ]
            )
        else:
            body = json.dumps(
                {
                    "summary": "Mock analysis produced without calling a provider.",
                    "strengths": ["Consistent merge request descriptions"],
                    "improvements": ["Link merge requests to their issue"],
                    "score": 0.75,
                }
            )

        class MockResponse:
            class Choice:
                class Message:
                    def __init__(self, content: str) -> None:
                        self.content = content

                def __init__(self, content: str) -> None:
                    self.message = self.Message(content)

            def __init__(self, text: str) -> None:
                self.choices = [self.Choice(text)]

        logger.info("LLM mock provider answered locally (%d chars)", len(body))
        return cast(LLMResponse, MockResponse(body))

    async def _call_openai(self, system_prompt: str, user_content: str) -> LLMResponse:
        """Call OpenAI-compatible API (OpenAI, Azure, or custom endpoint)."""
        import openai

        kwargs: dict[str, Any] = {"api_key": self.settings.llm_api_key}
        if self.settings.llm_api_base_url:
            kwargs["base_url"] = self.settings.llm_api_base_url

        client = openai.AsyncOpenAI(**kwargs)
        try:
            response = await client.chat.completions.create(
                model=self.settings.llm_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content},
                ],
                temperature=0.2,
                max_tokens=self.settings.llm_max_tokens,
                response_format={"type": "json_object"},
            )
            return cast(LLMResponse, response)
        finally:
            await client.close()

    async def _call_groq(self, system_prompt: str, user_content: str) -> LLMResponse:
        """Call Groq API (OpenAI-compatible, free tier available).

        Groq provides fast inference for open-source models:
        - llama-3.3-70b-versatile (best quality, free tier)
        - mixtral-8x7b-32768 (good balance, free tier)
        - llama-3.1-8b-instant (fastest, free tier)

        Uses the OpenAI client with Groq's base URL.
        """
        import openai

        base_url = self.settings.llm_api_base_url or _GROQ_DEFAULT_BASE_URL
        client = openai.AsyncOpenAI(
            api_key=self.settings.llm_api_key,
            base_url=base_url,
        )
        try:
            response = await client.chat.completions.create(
                model=self.settings.llm_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content},
                ],
                temperature=0.2,
                max_tokens=self.settings.llm_max_tokens,
                response_format={"type": "json_object"},
            )
            return cast(LLMResponse, response)
        finally:
            await client.close()

    async def _call_gemini(self, system_prompt: str, user_content: str) -> LLMResponse:
        """Call Google Gemini API."""
        from google import genai

        client = genai.Client(api_key=self.settings.llm_api_key)

        try:
            # Combine system prompt and user content for Gemini
            full_prompt = (
                f"{system_prompt}\n\n---\n\nAnalyze this:\n{user_content}\n\n"
                "Respond with valid JSON only."
            )

            response = await asyncio.to_thread(
                client.models.generate_content,
                model=self.settings.llm_model,
                contents=full_prompt,
            )

            # Wrap Gemini response in OpenAI-like structure for compatibility
            class GeminiResponseWrapper:
                class Choice:
                    class Message:
                        def __init__(self, content: str) -> None:
                            self.content = content

                    def __init__(self, content: str) -> None:
                        self.message = self.Message(content)

                def __init__(self, text: str) -> None:
                    self.choices = [self.Choice(text)]

            return GeminiResponseWrapper(response.text or "")
        finally:
            if hasattr(client, "close"):
                client.close()

    def _clean_and_parse_json(self, text: str) -> dict[str, Any]:
        """Extract and parse JSON from LLM output, handling markdown fences and preamble."""
        text = text.strip()

        # Try extracting from markdown code fences first
        fence_match = re.search(r"```(?:json)?\s*\n?(\{.*?})\s*```", text, re.DOTALL)
        if fence_match:
            return cast(dict[str, Any], json.loads(fence_match.group(1)))

        # Strip leading/trailing markdown fences if wrapping the whole text
        if text.startswith("```"):
            first_nl = text.find("\n")
            if first_nl != -1:
                text = text[first_nl + 1 :]
        text = text.removesuffix("```")
        text = text.strip()

        # Try direct parse
        try:
            return cast(dict[str, Any], json.loads(text))
        except json.JSONDecodeError:
            pass

        # Find the first '{' and last '}' - extract the outermost JSON object
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end > start:
            return cast(dict[str, Any], json.loads(text[start : end + 1]))

        raise json.JSONDecodeError("No JSON object found in LLM response", text, 0)

    def _calculate_risk(self, result: LLMAnalysisResult) -> float:
        # Simple heuristic
        score = 0.0
        for flag in result.risk_flags:
            if flag.severity == "high":
                score += 10
            elif flag.severity == "medium":
                score += 5
            else:
                score += 1
        return score
