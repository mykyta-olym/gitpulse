"""A stat card with no value renders a spinner. Something must replace it.

`stat_card` renders a spinner whenever it is given `value_id` and the value
`'-'`: the number is coming from JavaScript. That is a promise, and on the Event
Pipeline page three of the six cards never kept it - DLQ Events, Oldest Event
and Avg Retries span for the life of the page, on every load, while the three
beside them showed their numbers.

The cause was a guard that outlived its element. `loadDLQ()` opened with

    const tbody = document.getElementById('dlqTableBody');
    if (!tbody) return;

from the days when the dead-letter queue had a table of its own. Once the two
tables became one, that element was gone, every call returned on its first line,
and the three counters it also filled were never written.

Nothing failed. No request errored, no exception was thrown, the page looked
loaded. Only the spinners said otherwise, and they say it forever.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from jinja2 import Environment, nodes

from tests.build_outputs import served

ROOT = Path(__file__).resolve().parents[2]
TEMPLATES = ROOT / "src/app/templates"
JS = TEMPLATES / "static/js"

#: Pages whose stat cards are filled by a page script of the same name.
PAGES = {
    "admin_events.html": "pages/admin-events.js",
    "partials/course/_activity_content.html": "pages/course-activity.js",
    "partials/course/_analytics_content.html": "pages/course-analytics.js",
}


@pytest.mark.parametrize(("template", "script"), PAGES.items())
def test_every_spinner_has_something_that_fills_it(template: str, script: str) -> None:
    html = (TEMPLATES / template).read_text(encoding="utf-8")
    js = served(f"js/{script}").read_text(encoding="utf-8")  # what the page receives
    ids = []
    # Only a literal '-' with an identifier is an asynchronous placeholder.
    # Server-rendered numbers may also have ids for later component refreshes.
    for call in Environment(autoescape=True).parse(html).find_all(nodes.Call):
        if not isinstance(call.node, nodes.Name) or call.node.name != "stat_card":
            continue
        if len(call.args) < 2 or not isinstance(call.args[1], nodes.Const):
            continue
        if call.args[1].value != "-":
            continue
        ids.extend(
            arg.value.value
            for arg in call.kwargs
            if arg.key in {"id", "value_id"} and isinstance(arg.value, nodes.Const)
        )
    orphaned = [i for i in ids if i not in js]
    assert not orphaned, (
        f"{template} renders a spinner for {orphaned}, and {script} never writes "
        "them - the card spins for the life of the page"
    )


def test_the_dlq_loader_does_not_wait_for_a_table_that_is_gone() -> None:
    """The specific guard, by name: it returned before the counters were set."""
    js = (JS / "pages/admin-events.js").read_text(encoding="utf-8")
    body = js.split("async function loadDLQ", 1)[1].split("\n  }", 1)[0]
    code = re.sub(r"/\*.*?\*/", "", body, flags=re.S)  # the note explaining this
    assert "getElementById('dlqTableBody')" not in code, (
        "loadDLQ looks up the removed dead-letter table again; if it returns on "
        "a missing element the three DLQ counters never get a value"
    )
    for stat in ("dlqCount", "dlqOldest", "dlqAvgRetries"):
        assert stat in body, f"loadDLQ no longer fills {stat}"


def test_a_failed_load_shows_a_number_not_a_spinner() -> None:
    """An error must end the promise too, or the spinner outlives the failure."""
    js = (JS / "pages/admin-events.js").read_text(encoding="utf-8")
    catch = js.split("async function loadDLQ", 1)[1].split("} catch (err) {", 1)[1]
    catch = catch.split("\n  }", 1)[0]
    assert "dlqCount" in catch, (
        "when the dead-letter queue cannot be loaded the counters keep spinning, "
        "which reads as 'still loading' rather than 'unknown'"
    )
