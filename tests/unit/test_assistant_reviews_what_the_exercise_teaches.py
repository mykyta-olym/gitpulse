"""The rules the assistant reviews by - deterministic, and each one a lesson.

Push review: work on a branch, write the commit message yourself. Conflict:
no markers left, both sides kept. Merge request: your own branch, a link to the
issue, a change in the assigned file only, nothing left to fill in. These are
the functions that decide what a comment says, tested apart from GitLab.
"""

from __future__ import annotations

import uuid
from typing import Any

from app.models.assistant import AssistantTask, CourseAssistant
from app.models.course import Course
from app.models.course_settings import DEFAULT_BRANCH_PATTERN
from app.models.project import GitLabProject
from app.services.assistant.conflict import resolution_findings
from app.services.assistant.mr_review import review_findings
from app.services.assistant.push_review import findings, pushed_branch
from app.services.assistant.tasks import Context, branch_rule_to_name


def _codes(found: list[Any]) -> list[str]:
    return [f.code for f in found]


class TestWhichPushIsReviewed:
    def test_a_branch_push(self) -> None:
        assert pushed_branch({"ref": "refs/heads/feature/x", "after": "a" * 40}) == "feature/x"

    def test_not_a_tag(self) -> None:
        assert pushed_branch({"ref": "refs/tags/v1", "after": "a" * 40}) is None

    def test_not_a_deleted_branch(self) -> None:
        assert pushed_branch({"ref": "refs/heads/x", "after": "0" * 40}) is None


class TestPushFindings:
    def test_a_push_to_the_default_branch(self) -> None:
        found = findings("main", "main", [{"id": "a" * 40, "title": "Add the login form"}], 10)
        assert _codes(found) == ["direct_push"]

    def test_a_title_the_web_editor_wrote(self) -> None:
        found = findings("work", "main", [{"id": "b" * 40, "title": "Update README.md"}], 10)
        assert _codes(found) == ["web_editor_title"]
        assert found[0].params == {"sha": "bbbbbbbb", "title": "Update README.md"}

    def test_a_title_too_short_to_say_anything(self) -> None:
        found = findings("work", "main", [{"id": "c" * 40, "message": "fix\n\nmore"}], 10)
        assert _codes(found) == ["short_title"]
        assert found[0].params["title"] == "fix"
        assert found[0].params["min"] == 10

    def test_a_merge_commit_is_gits_wording_not_the_students(self) -> None:
        commits = [{"id": "d" * 40, "title": "Merge branch 'main' into work"}]
        assert findings("work", "main", commits, 60) == []

    def test_a_good_push_has_nothing_to_say(self) -> None:
        commits = [{"id": "e" * 40, "title": "Fill in my name and group"}]
        assert findings("work", "main", commits, 10) == []


class TestConflictResolution:
    LINE = "A colleague changed this line (GP-ABC123) - keep it."

    def test_a_clean_resolution(self) -> None:
        content = f"Name: Jana\n{self.LINE}\n"
        assert resolution_findings(content, self.LINE, ["Name: Jana"]) == []

    def test_markers_left_in(self) -> None:
        content = f"<<<<<<< HEAD\nName: Jana\n=======\n{self.LINE}\n>>>>>>> main\n"
        assert _codes(resolution_findings(content, self.LINE, ["Name: Jana"])) == [
            "conflict_markers"
        ]

    def test_the_colleagues_line_dropped(self) -> None:
        found = resolution_findings("Name: Jana\n", self.LINE, ["Name: Jana"])
        assert _codes(found) == ["control_line_missing"]

    def test_the_students_own_line_dropped(self) -> None:
        found = resolution_findings(f"{self.LINE}\n", self.LINE, ["Name: Jana", "Group: 3"])
        assert _codes(found) == ["own_line_missing", "own_line_missing"]


def _ctx() -> Context:
    course = Course(id=uuid.uuid4(), code="ZSI", name="x", academic_year="2025/2026")
    project = GitLabProject(
        id=uuid.uuid4(), team_id=uuid.uuid4(), gitlab_project_id=1, gitlab_project_path="g/p"
    )
    return Context(course, project, CourseAssistant(course_id=course.id), "main", "https://g/p")


def _task() -> AssistantTask:
    return AssistantTask(issue_iid=7, file_path="ulohy/jana.txt", student_username="jana")


def _mr(**overrides: Any) -> dict[str, Any]:
    mr = {
        "source_branch": "jana-ulohy",
        "target_branch": "main",
        "description": "Vyplnil som subor.\n\nCloses #7",
        "draft": False,
        "has_conflicts": False,
        "blocking_discussions_resolved": True,
    }
    return {**mr, **overrides}


class TestMergeRequestFindings:
    def test_a_merge_request_that_does_what_the_issue_asks(self) -> None:
        found = review_findings(_ctx(), _task(), _mr(), ["ulohy/jana.txt"], "Meno: Jana Nova\n")
        assert found == []

    def test_everything_missing_at_once(self) -> None:
        found = review_findings(
            _ctx(),
            _task(),
            _mr(
                source_branch="main",
                target_branch="develop",
                description="",
                draft=True,
                has_conflicts=True,
                blocking_discussions_resolved=False,
            ),
            ["README.md"],
            None,
        )
        assert _codes(found) == [
            "source_is_default",
            "target_not_default",
            "missing_issue_link",
            "file_untouched",
            "extra_files",
            "draft",
            "has_conflicts",
            "unresolved_threads",
        ]

    def test_another_issue_is_not_this_one(self) -> None:
        found = review_findings(
            _ctx(), _task(), _mr(description="Closes #8"), ["ulohy/jana.txt"], "Meno: Jana\n"
        )
        assert _codes(found) == ["missing_issue_link"]

    def test_a_placeholder_left_in_the_file(self) -> None:
        found = review_findings(
            _ctx(), _task(), _mr(), ["ulohy/jana.txt"], "Meno: Jana\nPrikaz: ???\n"
        )
        assert _codes(found) == ["placeholder_left"]

    def test_the_extra_files_are_named(self) -> None:
        found = review_findings(
            _ctx(), _task(), _mr(), ["ulohy/jana.txt", "README.md", "x.py"], "Meno: Jana\n"
        )
        assert _codes(found) == ["extra_files"]
        assert found[0].params["files"] == "`README.md`, `x.py`"


def test_a_finding_signature_is_stable_whatever_the_param_order() -> None:
    from app.services.assistant.texts import Finding

    first = Finding("x", {"b": 1, "a": 2})
    second = Finding("x", {"a": 2, "b": 1})
    assert first.signature() == second.signature() == "x:a=2,b=1"


class TestTheCoursesOwnRules:
    """The assistant asks what the course grades - and nothing it switched off."""

    RULE = "^issue-[0-9]+"

    def test_a_new_branch_breaking_the_course_rule(self) -> None:
        found = findings("feature", "main", [], 10, new_branch=True, branch_rule=self.RULE)
        assert _codes(found) == ["branch_name"]
        assert found[0].params == {"branch": "feature", "pattern": self.RULE}

    def test_the_rule_is_judged_once_when_the_branch_is_made(self) -> None:
        assert findings("feature", "main", [], 10, new_branch=False, branch_rule=self.RULE) == []

    def test_a_push_to_the_default_branch_is_not_also_a_naming_problem(self) -> None:
        found = findings("main", "main", [], 10, new_branch=True, branch_rule=self.RULE)
        assert _codes(found) == ["direct_push"]

    def test_a_merge_request_from_a_misnamed_branch(self) -> None:
        ctx = _ctx_with(branch_rule=self.RULE)
        found = review_findings(ctx, _task(), _mr(), ["ulohy/jana.txt"], "Meno: Jana\n")
        assert _codes(found) == ["branch_name"]
        assert (
            review_findings(
                ctx, _task(), _mr(source_branch="issue-7"), ["ulohy/jana.txt"], "Meno: Jana\n"
            )
            == []
        )

    def test_the_sections_the_course_asks_for(self) -> None:
        ctx = _ctx_with(required_sections=("## Co", "## Preco"))
        found = review_findings(
            ctx, _task(), _mr(description="## Co\nnieco\nCloses #7"), ["ulohy/jana.txt"], "x\n"
        )
        assert _codes(found) == ["template_sections"]
        assert found[0].params == {"sections": "`## Preco`"}

    def test_a_failed_pipeline(self) -> None:
        mr = _mr(head_pipeline={"status": "failed"})
        found = review_findings(_ctx(), _task(), mr, ["ulohy/jana.txt"], "Meno: Jana\n")
        assert _codes(found) == ["pipeline_failed"]

    def test_a_check_the_course_switched_off_asks_nothing(self) -> None:
        from app.models.course_settings import CourseSettings
        from app.services.assistant.tasks import course_rules

        settings = CourseSettings(
            enabled_checks=["R01"],
            check_configs={
                "R02": {"branch_pattern": self.RULE},
                "R05": {"required_sections": "## Co"},
            },
        )
        assert course_rules(settings) == ("", ())
        settings.enabled_checks = ["R02", "R05"]
        assert course_rules(settings) == (self.RULE, ("## Co",))
        assert course_rules(None) == ("", ())


def _ctx_with(**rules: Any) -> Context:
    base = _ctx()
    return Context(
        base.course, base.project, base.assistant, base.default_branch, base.web_url, **rules
    )


def test_the_default_branch_rule_goes_without_saying() -> None:
    """Any name but main and the like: the page and the issue do not print it."""
    assert branch_rule_to_name(DEFAULT_BRANCH_PATTERN) == ""
    assert branch_rule_to_name("^[0-9]+-") == "^[0-9]+-"
    assert branch_rule_to_name("") == ""
