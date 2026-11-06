"""Built-in compliance checks (R01-R13) and the check runner.

Each check is a pure function of (StudentContext, CourseSettings, cfg) returning
a CheckResult. Extracted from engine.py to isolate the scoring rules from the
metric-aggregation orchestration.
"""

import re
from typing import Any

from app.compliance.types import CheckResult, StudentContext
from app.models.course_settings import CourseSettings
from app.utils.gitlab_patterns import is_web_editor_commit


def _cfg_int(cfg: dict[str, Any], key: str, default: int) -> int:
    """Safely read an integer from a user-supplied config dict.

    Handles None, empty strings, and non-numeric values without crashing.
    """
    try:
        return int(cfg.get(key, default))
    except (ValueError, TypeError):
        return default


def _cfg_bool(cfg: dict[str, Any], key: str, default: bool) -> bool:
    """Read a bool from a user-supplied config dict, tolerating JSON strings.

    Strings ``"false"``/``"0"``/``"no"`` (case-insensitive) are False; any other
    string is True. Non-string values fall back to ``bool(value)``.
    """
    value = cfg.get(key, default)
    if isinstance(value, str):
        return value.lower() not in ("false", "0", "no")
    return bool(value)


def _partial_ratio(numerator: float, threshold: int) -> float:
    """Capped partial-credit ratio: ``min(numerator / max(threshold, 1), 1.0)``.

    Guards against a zero threshold and never exceeds 1.0, so partial scores
    stay within ``[0, weight]`` when multiplied by a check weight.
    """
    return min(numerator / max(threshold, 1), 1.0)


def run_all_checks(ctx: StudentContext, cs: CourseSettings) -> list[CheckResult]:
    """Evaluate all 13 compliance checks for one student.

    Each check is a pure function of (StudentContext, CourseSettings).
    Checks not in cs.enabled_checks (if that attribute exists)
    are skipped and returned with score=0, weight=0, passed=False.

    Per-check thresholds/options from cs.check_configs (JSONB) are forwarded
    to each check function so teachers can customise behaviour per course.
    """
    all_checks = {
        "R01": _check_r01_issue_ownership,
        "R02": _check_r02_branch_naming,
        "R03": _check_r03_test_changes,
        "R04": _check_r04_mr_issue_link,
        "R05": _check_r05_mr_template,
        "R06": _check_r06_review_received,
        "R07": _check_r07_review_duty,
        "R08": _check_r08_response_quality,
        "R09": _check_r09_approval_received,
        "R10": _check_r10_merged_by_author,
        "R11": _check_r11_closure_state,
        "R12": _check_r12_pipeline_health,
        "R13": _check_r13_commit_quality,
    }

    selection = getattr(cs, "enabled_checks", None)
    enabled = set(all_checks if selection is None else selection)

    check_cfgs: dict[str, dict[str, Any]] = getattr(cs, "check_configs", None) or {}

    # Review checks that require teammates - auto-pass for solo teams.
    review_check_weights = {
        "R06": "weight_review_count",
        "R07": "weight_review_duty",
        "R08": "weight_response_complete",
        "R09": "weight_approvals",
    }

    results: list[CheckResult] = []
    for check_id, fn in all_checks.items():
        if check_id in enabled:
            # Solo-team waiver: review checks are impossible without peers.
            if check_id in review_check_weights and ctx.team_member_count <= 1:
                w = getattr(cs, review_check_weights[check_id], 0.0)
                results.append(
                    CheckResult(
                        check_id=check_id,
                        name=fn.__doc__.split("\n")[0] if fn.__doc__ else check_id,
                        passed=True,
                        detail="Auto-passed: solo team (no peers to review/be reviewed by).",
                        weight=w,
                        score=w,
                    )
                )
                continue
            cfg = check_cfgs.get(check_id, {})
            results.append(fn(ctx, cs, cfg))
        else:
            results.append(
                CheckResult(
                    check_id=check_id,
                    name=fn.__doc__.split(":")[0].strip() if fn.__doc__ else check_id,
                    passed=False,
                    detail="Check disabled",
                    weight=0.0,
                    score=0.0,
                    enabled=False,
                )
            )
    return results


def _check_r01_issue_ownership(
    ctx: StudentContext, cs: CourseSettings, cfg: dict[str, Any] | None = None
) -> CheckResult:
    """R01: Student has at least min_issues assigned issues.

    Formula:  passed ⟺ |assigned_issues| ≥ min_issues
    Config:   cfg.min_issues (default 1)
    """
    cfg = cfg or {}
    min_issues: int = _cfg_int(cfg, "min_issues", 1)
    count = len(ctx.issues_assigned)
    passed = count >= min_issues
    if count == 0:
        detail = "No issue assigned"
    elif min_issues > 1:
        detail = f"{count}/{min_issues} issue(s) assigned"
    else:
        detail = f"{count} issue(s) assigned"

    return CheckResult(
        check_id="R01",
        name="Issue Assigned",
        passed=passed,
        detail=detail,
        weight=cs.weight_issue_ownership,
        score=cs.weight_issue_ownership if passed else 0.0,
    )


def _check_r02_branch_naming(
    ctx: StudentContext, cs: CourseSettings, cfg: dict[str, Any] | None = None
) -> CheckResult:
    """R02: At least one MR source branch follows the naming convention.

    Formula:  passed ⟺ |mrs_authored| ≥ 1 ∧ R, where
              R = True when the convention is disabled, else
              R = ∃ MR ∈ authored: branch_naming_ok
    Pseudocode:
        pass if len(authored) >= 1 and (not require_convention or ok_count > 0)

    Note: this is an ANY rule (one compliant branch is enough), consistent with
    R03/R04/R05 which likewise require only one qualifying MR - not ∀.
    """
    cfg = cfg or {}
    # Default to False (permissive) to match builtin_checks.json - teachers
    # must explicitly opt-in to strict branch naming.  Previously defaulted
    # to True, which made R02 fail for reasonable names like
    # ``feature/login`` or ``fix-auth-bug`` when courses had no custom cfg.
    require_convention = _cfg_bool(cfg, "require_branch_convention", False)
    authored = ctx.mrs_authored
    if not authored:
        return CheckResult(
            check_id="R02",
            name="Branch + MR Created",
            passed=False,
            detail="No MR created - cannot evaluate branch naming",
            weight=cs.weight_branch_naming,
            score=0.0,
        )
    if not require_convention:
        # Branch naming convention disabled - pass if at least one MR exists
        return CheckResult(
            check_id="R02",
            name="Branch + MR Created",
            passed=True,
            detail=f"{len(authored)} MR(s) - branch naming not required",
            weight=cs.weight_branch_naming,
            score=cs.weight_branch_naming,
        )
    # Only count MRs that have been evaluated (skip None = not yet synced)
    evaluated = [m for m in authored if m.branch_naming_ok is not None]
    ok_count = sum(1 for m in evaluated if m.branch_naming_ok)
    if not evaluated:
        # All MRs pending evaluation - treat as not yet passed
        passed = False
        detail = f"{len(authored)} MR(s) pending branch-name evaluation"
    else:
        passed = ok_count > 0
        if passed:
            bad_count = len(evaluated) - ok_count
            if bad_count == 0:
                detail = f"{ok_count} MR(s) with valid branch naming"
            else:
                detail = f"{ok_count}/{len(evaluated)} MR(s) with valid branch naming"
        else:
            # Show which branches failed (more user-friendly)
            bad_branches = [m.source_branch or "?" for m in evaluated if not m.branch_naming_ok]
            if len(bad_branches) == 1:
                detail = (
                    f"Branch '{bad_branches[0]}' is on a protected name or "
                    "does not match the configured naming convention"
                )
            else:
                detail = f"{len(bad_branches)} branches don't match the naming convention"
    return CheckResult(
        check_id="R02",
        name="Branch + MR Created",
        passed=passed,
        detail=detail,
        weight=cs.weight_branch_naming,
        score=cs.weight_branch_naming if passed else 0.0,
    )


def _check_r03_test_changes(
    ctx: StudentContext, cs: CourseSettings, cfg: dict[str, Any] | None = None
) -> CheckResult:
    """R03: At least one MR contains test file changes.

    Formula:  passed <=> exists MR in authored: has_test_changes == True
    """
    cfg = cfg or {}
    min_test_files = _cfg_int(cfg, "min_test_files", 1)
    if not ctx.mrs_authored:
        return CheckResult(
            check_id="R03",
            name="Tests Written",
            passed=False,
            detail="No MR created - cannot evaluate test changes",
            weight=cs.weight_test_changes,
            score=0.0,
        )
    count = sum(1 for m in ctx.mrs_authored if m.has_test_changes)
    passed = count >= min_test_files
    ratio = _partial_ratio(count, min_test_files)
    if passed:
        detail = f"{count} MR(s) with test files"
    elif count > 0:
        detail = f"{count}/{min_test_files} MR(s) with test files"
    else:
        detail = "No test files in any MR diff"
    return CheckResult(
        check_id="R03",
        name="Tests Written",
        passed=passed,
        detail=detail,
        weight=cs.weight_test_changes,
        score=cs.weight_test_changes * ratio,
    )


def _check_r04_mr_issue_link(
    ctx: StudentContext, cs: CourseSettings, cfg: dict[str, Any] | None = None
) -> CheckResult:
    """R04: At least one MR references an issue in its description.

    Formula:  passed <=> exists MR in authored: has_issue_link == True
    """
    cfg = cfg or {}
    require_issue_ref = _cfg_bool(cfg, "require_issue_ref", True)
    if not ctx.mrs_authored:
        return CheckResult(
            check_id="R04",
            name="MR Linked to Issue",
            passed=False,
            detail="No MR created - cannot evaluate issue link",
            weight=cs.weight_mr_issue_link,
            score=0.0,
        )
    if not require_issue_ref:
        return CheckResult(
            check_id="R04",
            name="MR Linked to Issue",
            passed=True,
            detail="Issue reference not required",
            weight=cs.weight_mr_issue_link,
            score=cs.weight_mr_issue_link,
        )
    has_link = any(m.has_issue_link for m in ctx.mrs_authored)
    return CheckResult(
        check_id="R04",
        name="MR Linked to Issue",
        passed=has_link,
        detail="MR references issue" if has_link else "No issue reference in MR description",
        weight=cs.weight_mr_issue_link,
        score=cs.weight_mr_issue_link if has_link else 0.0,
    )


def _check_r05_mr_template(
    ctx: StudentContext, cs: CourseSettings, cfg: dict[str, Any] | None = None
) -> CheckResult:
    """R05: At least one MR description meets quality requirements.

    Config:
        require_template (bool, default false): require template sections
        min_description_words (int, default 10): minimum words in description
    """
    cfg = cfg or {}
    require_template = cfg.get("require_template", False)
    if isinstance(require_template, str):
        require_template = require_template.lower() in ("true", "1", "yes")
    min_words = _cfg_int(cfg, "min_description_words", 10)

    if not ctx.mrs_authored:
        return CheckResult(
            check_id="R05",
            name="MR Description",
            passed=False,
            detail="No MR created - cannot evaluate MR description",
            weight=cs.weight_mr_template,
            score=0.0,
        )

    # Check word count across all authored MRs
    def _word_count(mr: Any) -> int:
        desc = getattr(mr, "description", None) or ""
        # Strip markdown structural tokens that shouldn't count as content:
        # headings (#, ##, ###), list bullets (-, *, +), inline code/emphasis
        # markers, link targets, table separators, blockquotes, horizontal
        # rules. This prevents passing the threshold with a description that
        # is just empty section headers like "## Goal\n## Steps\n## Tests\n".
        cleaned = re.sub(r"^[#>\-*+|`~_]+\s*", "", desc, flags=re.MULTILINE)
        cleaned = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", cleaned)  # [text](url) -> text
        cleaned = re.sub(r"[`*_~]+", "", cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        # Filter out tokens that are pure punctuation / single chars.
        return sum(1 for tok in cleaned.split() if len(tok) >= 2 and re.search(r"\w", tok))

    meets_words = any(_word_count(m) >= min_words for m in ctx.mrs_authored)

    if require_template:
        # Both template compliance and word count required
        evaluated = [m for m in ctx.mrs_authored if m.template_compliant is not None]
        compliant = any(m.template_compliant for m in evaluated)
        if not evaluated:
            detail = f"{len(ctx.mrs_authored)} MR(s) pending template evaluation"
            passed = False
        elif compliant and meets_words:
            passed = True
            detail = "MR follows template with sufficient description"
        elif not compliant:
            passed = False
            detail = "MR description missing required sections"
        else:
            passed = False
            detail = f"MR description too short (min {min_words} words)"
    else:
        # Only word count required
        passed = meets_words
        if passed:
            detail = "MR description meets word count requirement"
        else:
            detail = f"MR description too short (min {min_words} words)"

    return CheckResult(
        check_id="R05",
        name="MR Description",
        passed=passed,
        detail=detail,
        weight=cs.weight_mr_template,
        score=cs.weight_mr_template if passed else 0.0,
    )


def _check_r06_review_received(
    ctx: StudentContext, cs: CourseSettings, cfg: dict[str, Any] | None = None
) -> CheckResult:
    """R06: Own MR received meaningful reviews from >= min_reviewers distinct teammates.

    A "meaningful" reviewer is one whose joined notes on this student's MR
    contain enough substantive content (per ``is_meaningful_comment``).
    Trivial "LGTM"/"+1" comments therefore don't satisfy the ZSI requirement
    that two team members perform a real code review.
    Config:
        cfg.min_reviewers (default cs.min_reviews_per_mr)
        cfg.require_meaningful (default True)
    """
    cfg = cfg or {}
    require_meaningful = _cfg_bool(cfg, "require_meaningful", True)

    note_reviewer_ids = {n.author_id for n in ctx.notes_on_own_mr if n.author_id}

    if require_meaningful and ctx.notes_on_own_mr:
        from app.utils.text_analysis import is_meaningful_comment

        min_words = _cfg_int(cfg, "min_word_count", cs.min_review_word_count)
        notes_by_reviewer: dict[Any, list[Any]] = {}
        for n in ctx.notes_on_own_mr:
            if n.author_id is None:
                continue
            notes_by_reviewer.setdefault(n.author_id, []).append(n)
        meaningful_ids: set[Any] = set()
        for rid, notes in notes_by_reviewer.items():
            bodies = [getattr(n, "body", None) or "" for n in notes]
            joined = " ".join(b for b in bodies if b)
            if joined:
                if is_meaningful_comment(joined, min_words=min_words):
                    meaningful_ids.add(rid)
            else:
                # Fallback: rely on pre-computed word_count when no body
                # text is available (older records / test stubs).
                total_words = sum(int(getattr(n, "word_count", 0) or 0) for n in notes)
                if total_words >= min_words:
                    meaningful_ids.add(rid)
        reviewer_ids = meaningful_ids
    else:
        reviewer_ids = note_reviewer_ids

    count = len(reviewer_ids)
    threshold = _cfg_int(cfg, "min_reviewers", cs.min_reviews_per_mr)
    passed = count >= threshold
    ratio = _partial_ratio(count, threshold)

    bot_notes = ctx.bot_notes_on_own_mr + sum(1 for n in ctx.notes_on_own_mr if not n.author_id)
    detail = f"{count}/{threshold} distinct reviewers on own MR"
    if count == 0 and bot_notes > 0:
        detail += f" (bot comments: {bot_notes}, only group members count)"
    elif require_meaningful and count == 0 and len(note_reviewer_ids) > 0:
        detail += f" ({len(note_reviewer_ids)} reviewer(s) left only short comments)"

    return CheckResult(
        check_id="R06",
        name="Code Review Received",
        passed=passed,
        detail=detail,
        weight=cs.weight_review_count,
        score=cs.weight_review_count * ratio,
    )


def _check_r07_review_duty(
    ctx: StudentContext, cs: CourseSettings, cfg: dict[str, Any] | None = None
) -> CheckResult:
    """R07: Student meaningfully reviewed >= threshold peer MRs.

    Formula:  passed <=> |{r.merge_request_id : r in reviews_given, r.is_meaningful}|
              >= threshold
    Partial score: weight x (count / threshold) if count < threshold
    Config:   cfg.min_mrs_reviewed (default cs.min_distinct_mrs_reviewed)
              cfg.min_word_count (default cs.min_review_word_count)
    """
    cfg = cfg or {}
    word_threshold = _cfg_int(cfg, "min_word_count", cs.min_review_word_count)
    # Honour the course-configured word threshold (F3): the stored
    # ReviewActivity.is_meaningful flag is computed once at the default
    # 15-word floor (note_processor has no course settings), so relying on it
    # alone made R07 ignore a course's custom min_review_word_count while R06
    # respected it. `is_meaningful` still gates trivial/emoji-only reviews and
    # the 15-word floor; `total_words >= word_threshold` layers the configured
    # threshold on top. At the default (15) this is a no-op because
    # is_meaningful already implies total_words >= 15.
    meaningful_mr_ids = {
        r.merge_request_id
        for r in ctx.reviews_given
        if r.is_meaningful and (getattr(r, "total_words", 0) or 0) >= word_threshold
    }
    count = len(meaningful_mr_ids)
    threshold = _cfg_int(cfg, "min_mrs_reviewed", cs.min_distinct_mrs_reviewed)
    passed = count >= threshold
    ratio = _partial_ratio(count, threshold)

    total_reviews = len(ctx.reviews_given)
    detail = f"Meaningfully reviewed {count}/{threshold} distinct MRs"
    if count == 0 and total_reviews > 0:
        detail += f" ({total_reviews} review(s) below {word_threshold}-word threshold)"
    elif count == 0 and total_reviews == 0:
        if ctx.team_member_count <= 1:
            detail += " - solo group, no peer MRs available to review"
        else:
            detail += " - review other group members' MRs (self-reviews don't count)"

    return CheckResult(
        check_id="R07",
        name="Code Review Given",
        passed=passed,
        detail=detail,
        weight=cs.weight_review_duty,
        score=cs.weight_review_duty * ratio,
    )


def _check_r08_response_quality(
    ctx: StudentContext, cs: CourseSettings, cfg: dict[str, Any] | None = None
) -> CheckResult:
    """R08: Author responded to all review threads (and optionally cited a commit).

    A "review thread" includes both inline diff discussions (those with a
    ``discussion_id``) **and** standalone reviewer comments without a
    discussion thread - both expect a reply from the MR author.
    Config:
        cfg.require_commit_ref (default False) - commit-SHA citation is
            recommended but no longer mandatory by default; many students
            don't know about the convention.
        cfg.pass_if_no_threads (default True) - if no reviewer feedback
            exists yet, the check passes (you can't respond to feedback
            you haven't received).
    """
    cfg = cfg or {}
    require_commit_ref = bool(cfg.get("require_commit_ref", False))
    pass_if_no_threads = bool(cfg.get("pass_if_no_threads", True))

    if not ctx.mrs_authored:
        return CheckResult(
            check_id="R08",
            name="Review Response",
            passed=False,
            detail="No merge requests authored yet",
            weight=cs.weight_response_complete,
            score=0.0,
        )

    # Inline diff threads - keyed by discussion_id.
    reviewer_discussions = {n.discussion_id for n in ctx.notes_on_own_mr if n.discussion_id}
    author_discussions = {n.discussion_id for n in ctx.own_responses if n.discussion_id}

    # Standalone reviewer comments without a discussion_id - each treated
    # as one "thread" requiring acknowledgement. We approximate "answered"
    # by counting how many own_responses lack discussion_id (i.e. plain MR
    # comments) up to the number of standalone reviewer comments.
    standalone_reviewer_notes = sum(1 for n in ctx.notes_on_own_mr if not n.discussion_id)
    standalone_author_notes = sum(1 for n in ctx.own_responses if not n.discussion_id)

    inline_total = len(reviewer_discussions)
    inline_answered = len(reviewer_discussions & author_discussions)
    standalone_answered = min(standalone_author_notes, standalone_reviewer_notes)

    total_threads = inline_total + standalone_reviewer_notes
    answered = inline_answered + standalone_answered

    if total_threads == 0:
        # No reviewer feedback yet - nothing to respond to.
        return CheckResult(
            check_id="R08",
            name="Review Response",
            passed=pass_if_no_threads,
            detail="No review threads yet - waiting for code review feedback",
            weight=cs.weight_response_complete,
            score=cs.weight_response_complete if pass_if_no_threads else 0.0,
        )

    response_rate = answered / total_threads
    has_commit_ref = any(n.contains_commit_ref for n in ctx.own_responses)
    all_answered = answered >= total_threads
    commit_ref_ok = has_commit_ref or not require_commit_ref
    passed = all_answered and commit_ref_ok

    ref_factor = 1.0 if commit_ref_ok else 0.0
    partial = 0.5 * response_rate + 0.5 * ref_factor if require_commit_ref else response_rate

    detail = f"{answered}/{total_threads} threads answered"
    if require_commit_ref:
        detail += ", commit ref cited" if has_commit_ref else ", no commit ref"
    elif has_commit_ref:
        detail += " (commit ref cited)"

    return CheckResult(
        check_id="R08",
        name="Review Response",
        passed=passed,
        detail=detail,
        weight=cs.weight_response_complete,
        score=cs.weight_response_complete * partial,
    )


def _check_r09_approval_received(
    ctx: StudentContext, cs: CourseSettings, cfg: dict[str, Any] | None = None
) -> CheckResult:
    """R09: Own MR received >= threshold approvals.

    Formula:  passed <=> |{a.approver_gitlab_id : a in approvals_on_own_mr}|
              + (1 if any merged MR and count_merged_as_approval else 0)
              >= threshold
    Partial score: weight x (count / threshold)
    Config:
        cfg.min_approvals (default 1) - usually 1 ("at least one
            approver"). Independent from cs.min_reviews_per_mr which
            controls how many *reviews* a student must give/receive
            (R06/R07) - semantically distinct from "is the MR approved".
        cfg.count_merged_as_approval (default True) - when an MR is merged
            it is treated as receiving one implicit approval, since GitLab
            requires approval before merging in most properly-configured
            projects, and many students leave LGTM as a comment instead of
            clicking the Approve button.
    """
    cfg = cfg or {}
    # Union the live /approvals list with approvers recovered from the permanent
    # "approved this merge request" system notes. GitLab clears the /approvals
    # list once an MR merges + its branch is deleted, so relying on it alone made
    # R09 wrongly drop below threshold for every merged MR on the next sync.
    distinct_approvers = {a.approver_gitlab_id for a in ctx.approvals_on_own_mr} | getattr(
        ctx, "approval_note_approver_ids", set()
    )
    count = len(distinct_approvers)

    count_merged = _cfg_bool(cfg, "count_merged_as_approval", True)
    implicit = 0
    if count_merged and any(m.state == "merged" for m in ctx.mrs_authored) and count == 0:
        # Only credit the implicit approval when no explicit approver exists,
        # so we don't double-count (the merger is often also an approver).
        implicit = 1

    effective = count + implicit
    threshold = _cfg_int(cfg, "min_approvals", 1)
    passed = effective >= threshold
    ratio = _partial_ratio(effective, threshold)

    if implicit and not count:
        detail = f"{effective}/{threshold} approvals on own MR (merged MR counted as approval)"
    else:
        detail = f"{count}/{threshold} approvals on own MR"

    return CheckResult(
        check_id="R09",
        name="MR Approved",
        passed=passed,
        detail=detail,
        weight=cs.weight_approvals,
        score=cs.weight_approvals * ratio,
    )


def _check_r10_merged_by_author(
    ctx: StudentContext, cs: CourseSettings, cfg: dict[str, Any] | None = None
) -> CheckResult:
    """R10: The MR was merged by the author or a coordinated team-mate.

    ZSI text: "the assignment owner (or designated assignee) executed the
    merge after approval - not someone else without coordination". The
    spirit is: a human team member performed the merge after review, not a
    bot/admin/external user. Default behaviour therefore accepts merge by
    the author OR by another known student (someone with merged_by_id
    resolved to a Student row), and only flags merges by unknown users.
    Config:
        require_self_merge (bool, default False): if True, the author
            specifically must have clicked Merge.
        forbid_self_merge (bool, default False): if True, someone OTHER
            than the author must merge (reviewer-gates-merge model).
    """
    cfg = cfg or {}
    require_self = _cfg_bool(cfg, "require_self_merge", False)
    forbid_self = _cfg_bool(cfg, "forbid_self_merge", False)

    any_merged = any(m.state == "merged" for m in ctx.mrs_authored)
    merged_mrs = [m for m in ctx.mrs_authored if m.state == "merged"]

    def _is_self(m: Any) -> bool:
        return m.merged_by_id == ctx.student_id or (
            m.merged_by_id is None and m.merged_by_gitlab_id == ctx.gitlab_user_id
        )

    merged_by_self = any(_is_self(m) for m in merged_mrs)
    merged_by_known_student = any(m.merged_by_id is not None for m in merged_mrs)
    merged_by_someone_else = any(not _is_self(m) for m in merged_mrs)

    if not any_merged:
        return CheckResult(
            check_id="R10",
            name="Merged by Author",
            passed=False,
            detail="MR not yet merged",
            weight=cs.weight_merge_by_author,
            score=0.0,
        )

    if forbid_self:
        passed = merged_by_someone_else
        detail = (
            "Merged by reviewer"
            if passed
            else "Author merged own MR - reviewer should execute merge"
        )
    elif require_self:
        passed = merged_by_self
        detail = (
            "Merged by author" if passed else "Merged by someone else - author should execute merge"
        )
    else:
        # Permissive default: author OR a resolved teammate is acceptable.
        passed = merged_by_self or merged_by_known_student
        if merged_by_self:
            detail = "Merged by author"
        elif merged_by_known_student:
            detail = "Merged by a team member after approval"
        else:
            detail = "Merged by an unknown user (not a team member)"

    return CheckResult(
        check_id="R10",
        name="Merged by Author",
        passed=passed,
        detail=detail,
        weight=cs.weight_merge_by_author,
        score=cs.weight_merge_by_author if passed else 0.0,
    )


def _check_r11_closure_state(
    ctx: StudentContext, cs: CourseSettings, cfg: dict[str, Any] | None = None
) -> CheckResult:
    """R11: At least one merged MR has its linked issue closed.

    The MR and its referenced issue must be coupled - it is not enough that
    *some* assigned issue happens to be closed and *some* MR happens to be
    merged. We look at MRs that reference an issue (via Closes #N or branch
    name) and check the matching issue's state.
    Config:
        require_both_closed (bool, default True): if True, both must be
            closed. If False, the merged MR alone is enough.
    """
    cfg = cfg or {}
    require_both = _cfg_bool(cfg, "require_both_closed", True)

    merged_mrs = [m for m in ctx.mrs_authored if m.state in ("merged", "closed")]
    if not merged_mrs:
        return CheckResult(
            check_id="R11",
            name="MR + Issue Closed",
            passed=False,
            detail="No merged/closed MR yet",
            weight=cs.weight_closure,
            score=0.0,
        )

    if not require_both:
        return CheckResult(
            check_id="R11",
            name="MR + Issue Closed",
            passed=True,
            detail="MR closed (issue closure not required)",
            weight=cs.weight_closure,
            score=cs.weight_closure,
        )

    # Build a lookup of assigned issues by IID so we can resolve the MR's
    # linked_issue_iid into a state without an extra query.
    issues_by_iid = {i.gitlab_iid: i for i in ctx.issues_assigned}

    linked_pair_closed = False
    has_linked_mr = False
    for mr in merged_mrs:
        linked_iid = getattr(mr, "linked_issue_iid", None)
        if not linked_iid:
            continue
        has_linked_mr = True
        issue = issues_by_iid.get(linked_iid)
        if issue and issue.state == "closed":
            linked_pair_closed = True
            break

    if linked_pair_closed:
        passed = True
        detail = "Merged MR's linked issue is closed"
    elif has_linked_mr:
        passed = False
        detail = "Merged MR references an issue that is still open"
    else:
        # MR is merged but doesn't reference any issue - fall back to the
        # legacy any-issue-closed heuristic so we don't penalise students
        # whose MR description never linked the ticket explicitly.
        any_issue_closed = any(i.state == "closed" for i in ctx.issues_assigned)
        passed = any_issue_closed
        detail = (
            "MR merged and assigned issue closed (no explicit link)"
            if any_issue_closed
            else "MR merged but no assigned issue is closed"
        )

    return CheckResult(
        check_id="R11",
        name="MR + Issue Closed",
        passed=passed,
        detail=detail,
        weight=cs.weight_closure,
        score=cs.weight_closure if passed else 0.0,
    )


def _check_r12_pipeline_health(
    ctx: StudentContext, cs: CourseSettings, cfg: dict[str, Any] | None = None
) -> CheckResult:
    """R12: At least one pipeline succeeded, optionally with a test job.

    Formula:  passed <=> exists pipeline: status=="success"
              and (not require_test_job or has_test_job)
    Config:   cfg.require_test_job (default True)
    """
    cfg = cfg or {}
    require_test_job = bool(cfg.get("require_test_job", True))
    has_pipeline = len(ctx.pipelines) > 0
    has_green = any(p.status == "success" for p in ctx.pipelines)
    has_test = any(p.has_test_job for p in ctx.pipelines)
    passed = has_green and (has_test or not require_test_job)

    if passed:
        detail = (
            "Pipeline passed with test job"
            if has_test
            else "Pipeline passed (test job not required)"
        )
    elif not has_pipeline:
        detail = "No pipelines found for student's branch"
    elif not has_green:
        detail = "No successful pipeline - fix CI failures"
    else:
        detail = "Pipeline passes but no test job detected"

    return CheckResult(
        check_id="R12",
        name="Pipeline Green",
        passed=passed,
        detail=detail,
        weight=cs.weight_pipeline_health,
        score=cs.weight_pipeline_health if passed else 0.0,
    )


def _check_r13_commit_quality(
    ctx: StudentContext, cs: CourseSettings, cfg: dict[str, Any] | None = None
) -> CheckResult:
    """R13: Commits use meaningful messages - web-editor ratio below threshold.

    Formula:  passed <=> |web_editor_commits| / |total_commits| <= max_web_editor_ratio
    Config:   cfg.max_web_editor_ratio (default 0.3)
    """
    cfg = cfg or {}
    max_ratio: float = float(cfg.get("max_web_editor_ratio", 0.3))

    commits = [c for c in ctx.commits if not getattr(c, "is_merge_commit", False)]
    total = len(commits)
    if total == 0:
        return CheckResult(
            check_id="R13",
            name="Commit Quality",
            passed=False,
            detail="No commits to evaluate",
            weight=cs.weight_commit_quality,
            score=0.0,
        )

    web_count = sum(1 for c in commits if is_web_editor_commit(c.title))
    ratio = web_count / total
    passed = ratio <= max_ratio

    if web_count == 0:
        detail = f"{total} commit(s), all with meaningful messages"
    elif passed:
        detail = f"{web_count}/{total} web-editor commits ({ratio:.0%} ≤ {max_ratio:.0%})"
    else:
        detail = (
            f"{web_count}/{total} web-editor commits ({ratio:.0%} > {max_ratio:.0%}) "
            "- use git CLI instead of GitLab web editor"
        )

    if passed:
        score = cs.weight_commit_quality
    else:
        # Partial credit: proportional to good commits
        good_ratio = 1.0 - ratio
        score = (
            cs.weight_commit_quality * min(good_ratio / (1.0 - max_ratio), 1.0)
            if max_ratio < 1.0
            else 0.0
        )

    return CheckResult(
        check_id="R13",
        name="Commit Quality",
        passed=passed,
        detail=detail,
        weight=cs.weight_commit_quality,
        score=round(score, 4),
    )
