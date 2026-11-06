"""The setup guide must name every event the checks depend on.

The GitLab integration page told teachers to tick "Push, MR, Issues,
Pipelines". GitLab delivers comments as the `note` event, and `note` is what
R06 (review received), R07 (review given) and R08 (response to review) are
computed from - 0.12 + 0.12 + 0.08 = **0.32 of the total score weight**.

A webhook configured from that table delivered pushes, merge requests, issues
and pipelines, so it looked healthy in GitLab's delivery log and in the app's
event pipeline. The three review rules simply never passed, for anyone, and
nothing anywhere said why.

The application's own settings page had it right all along
(`_webhook_settings.html`: "Enable: Push, Issues, Merge requests, Note,
Pipelines"), and the worker's dispatch table is the final authority. This
checks the guide against both, in both languages.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
GUIDES = (
    ROOT / "docs-site/content/gitlab/webhooky.md",
    ROOT / "docs-site/content-en/gitlab/webhooky.md",
)
PROCESSOR = ROOT / "src/app/workers/event_processor.py"
SETTINGS_UI = ROOT / "src/app/templates/partials/course_settings/_webhook_settings.html"

#: How GitLab labels each processed `object_kind` in the webhook trigger list.
#: `note` is the one the guide omitted.
TRIGGER_LABELS = {
    "push": "Push",
    "issue": "Issues",
    "merge_request": "Merge request",
    "note": "Comments",
    "pipeline": "Pipeline",
}


def test_the_worker_still_processes_what_this_test_assumes() -> None:
    """If the dispatch table changes, the guide's list has to change with it."""
    src = PROCESSOR.read_text(encoding="utf-8")
    dispatch = src.split("def _handlers()", 1)[1].split("return {", 1)[1].split("}", 1)[0]
    handled = set(re.findall(r'"([a-z_]+)":', dispatch))
    missing = {k for k in TRIGGER_LABELS if k not in handled}
    assert not missing, f"these events are no longer processed: {missing}"


def test_the_settings_page_names_note() -> None:
    """The app's own instruction - the one the guide should have matched."""
    ui = SETTINGS_UI.read_text(encoding="utf-8")
    assert "Note" in ui, "the course settings page stopped naming the Note trigger"


@pytest.mark.parametrize("guide", GUIDES, ids=lambda p: p.parent.parent.name)
def test_the_guide_names_every_trigger(guide: Path) -> None:
    table = guide.read_text(encoding="utf-8").split("| Trigger |", 1)[1].split("\n", 1)[0]
    missing = [
        label for kind, label in TRIGGER_LABELS.items() if label.lower() not in table.lower()
    ]
    assert not missing, (
        f"{guide.parent.parent.name}: the trigger list omits {missing}. A teacher "
        "who follows it configures a webhook that silently never delivers those "
        "events - and for `note`, three of the thirteen rules can never pass."
    )


@pytest.mark.parametrize("guide", GUIDES, ids=lambda p: p.parent.parent.name)
def test_the_guide_says_why_comments_matter(guide: Path) -> None:
    """Naming the trigger is not enough - a reader skimming a table skips it."""
    src = guide.read_text(encoding="utf-8")
    assert re.search(r"R06.*R07.*R08|R06, R07", src, re.S), (
        "nothing on the page connects the Comments trigger to the rules it feeds"
    )
