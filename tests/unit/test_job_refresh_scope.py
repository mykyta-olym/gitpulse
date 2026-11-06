"""Data refresh follows the actual job scope rather than process-lock conflicts."""

import json
import shutil
import subprocess
from pathlib import Path

import pytest

TARGETS = {
    "course": {"courseId": "c"},
    "team": {"courseId": "c", "teamId": "t"},
    "project": {"courseId": "c", "teamId": "t", "projectId": "p"},
}
CASES = [
    ("unknown", {"jobType": "enrichment"}, "project", {}, False),
    ("no-detail", None, "project", {}, False),
    ("course-to-course", {"jobType": "sync:course:c"}, "course", {}, True),
    ("course-to-team", {"jobType": "sync:course:c"}, "team", {}, True),
    ("course-to-project", {"jobType": "sync:course:c"}, "project", {}, True),
    ("foreign-course", {"jobType": "sync:course:other"}, "project", {}, False),
    ("team-to-project", {"jobType": "run_checks:team:t"}, "project", {}, True),
    (
        "foreign-team",
        {"jobType": "sync:team:other", "meta": {"courseId": "c"}},
        "project",
        {},
        False,
    ),
    ("project-to-project", {"jobType": "sync:project:p"}, "project", {}, True),
    (
        "sibling-project",
        {"jobType": "sync:project:other", "meta": {"teamId": "t", "courseId": "c"}},
        "project",
        {},
        False,
    ),
    ("project-to-team", {"jobType": "sync:project:p", "meta": {"teamId": "t"}}, "team", {}, True),
    (
        "project-to-course",
        {"jobType": "sync:project:p", "meta": {"courseId": "c"}},
        "course",
        {},
        True,
    ),
    ("unknown-parent", {"jobType": "sync:project:p"}, "team", {}, False),
    (
        "team-origin-project",
        {"jobType": "run_checks:team:t", "meta": {"projectId": "other"}},
        "project",
        {},
        True,
    ),
    (
        "course-origin-project",
        {"jobType": "sync:course:c", "meta": {"teamId": "other", "projectId": "other"}},
        "project",
        {},
        True,
    ),
    (
        "key-before-meta",
        {"jobType": "sync:project:other", "meta": {"projectId": "p"}},
        "project",
        {},
        False,
    ),
    ("metadata-project", {"jobType": "analysis", "meta": {"projectId": "p"}}, "project", {}, True),
    (
        "metadata-foreign-project",
        {"jobType": "analysis", "meta": {"projectId": "other", "teamId": "t"}},
        "project",
        {},
        False,
    ),
    ("metadata-team", {"jobType": "analysis", "meta": {"teamId": "t"}}, "project", {}, True),
    ("metadata-course", {"jobType": "import", "meta": {"courseId": "c"}}, "project", {}, True),
    (
        "stored-meta",
        {"jobType": "analysis"},
        "project",
        {"analysis": {"meta": {"projectId": "p"}}},
        True,
    ),
    (
        "merge-meta",
        {"jobType": "analysis", "meta": {"message": "done"}},
        "project",
        {"analysis": {"meta": {"projectId": "p"}}},
        True,
    ),
    ("legacy-course-key", {"jobType": "c"}, "project", {}, True),
    ("foreign-legacy-key", {"jobType": "other"}, "project", {}, False),
    (
        "legacy-course-kind",
        {"jobType": "c", "meta": {"jobKind": "course_sync", "courseId": "c", "projectId": "other"}},
        "project",
        {},
        True,
    ),
    (
        "legacy-project-poll",
        {"jobType": "analysis", "meta": {"pollUrl": "/dashboard/projects/p/llm-analysis-status"}},
        "project",
        {},
        True,
    ),
    (
        "foreign-project-poll",
        {
            "jobType": "analysis",
            "meta": {"pollUrl": "/dashboard/projects/other/llm-analysis-status"},
        },
        "project",
        {},
        False,
    ),
    (
        "legacy-team-poll",
        {"jobType": "analysis", "meta": {"pollUrl": "/dashboard/teams/t/llm-analysis-status?x=1"}},
        "project",
        {},
        True,
    ),
    (
        "unrelated-poll",
        {"jobType": "analysis", "meta": {"pollUrl": "/dashboard/projects/p/unrelated"}},
        "project",
        {},
        False,
    ),
    (
        "external-poll",
        {
            "jobType": "analysis",
            "meta": {"pollUrl": "https://example.test/dashboard/projects/p/llm-analysis-status"},
        },
        "project",
        {},
        False,
    ),
    (
        "contradictory-team",
        {"jobType": "sync:team:t", "meta": {"teamId": "other"}},
        "team",
        {},
        False,
    ),
    (
        "contradictory-poll",
        {
            "jobType": "analysis",
            "meta": {"projectId": "other", "pollUrl": "/dashboard/projects/p/llm-analysis-status"},
        },
        "project",
        {},
        False,
    ),
]


@pytest.fixture(scope="module")
def results(tmp_path_factory):
    node = shutil.which("node")
    if not node:
        pytest.skip("scope contracts need Node")
    source = (
        Path(__file__).resolve().parents[2]
        / "src/app/templates/static/js/_parts/core/24-scoped-processes.js"
    ).read_text(encoding="utf-8")
    helper = source.split("async function runScopedChecksProcess", 1)[0]
    script = tmp_path_factory.mktemp("job-scope") / "check.cjs"
    script.write_text(
        "const window = {_globalJobs: {}}; const GP = {};\n"
        + helper
        + "\nconst cases = JSON.parse(process.argv[2]);\n"
        + "console.log(JSON.stringify(cases.map(c => {window._globalJobs=c.stored;"
        + "return GP.jobAffectsScope(c.detail,c.target);})));\n",
        encoding="utf-8",
    )
    payload = [
        {"detail": detail, "target": TARGETS[target], "stored": stored}
        for _, detail, target, stored, _ in CASES
    ]
    completed = subprocess.run(  # noqa: S603 - local source and fixed test cases; no shell
        [node, str(script), json.dumps(payload)],
        capture_output=True,
        text=True,
        check=True,
        timeout=15,
    )
    return json.loads(completed.stdout)


@pytest.mark.parametrize("index", range(len(CASES)), ids=[row[0] for row in CASES])
def test_job_scope_matches_refresh_target(results, index):
    assert results[index] is CASES[index][4]
