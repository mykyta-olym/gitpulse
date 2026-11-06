"""A confirmation raised from inside a modal can actually be confirmed.

Stacking is a browser question, so it is asked in a browser. The course page's
"Run selected checks" lives inside the Run Compliance Checks modal and calls
`confirmDangerousAction`. Both surfaces are `.modal-backdrop`, both were at
z-index 1000, and a page modal is moved to the end of `<body>` when it opens -
so the modal painted over the confirmation that it had just raised.

What that cost: the dialog was in the DOM, `visibility: visible`, opacity 1, and
`document.elementFromPoint` at the Confirm button's centre returned
`#runChecksGrid`. Nothing on screen, nothing clickable, and the course-wide Run
Checks could not be completed at all.

    GITPULSE_E2E_BASE_URL=http://127.0.0.1:8000 \
      python -m pytest tests/e2e/scenarios/test_the_confirmation_can_be_clicked.py -q
"""

from __future__ import annotations

import os

import pytest

pytestmark = pytest.mark.e2e

if not os.getenv("GITPULSE_E2E_BASE_URL"):
    pytest.skip(
        "scenario walks need GITPULSE_E2E_BASE_URL pointing at a running server",
        allow_module_level=True,
    )

_HIT_TEST = """
() => {
  const ok = document.querySelector('[data-gp-confirm="ok"]');
  if (!ok) return {found: false};
  const r = ok.getBoundingClientRect();
  const hit = document.elementFromPoint(
    Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2));
  return {
    found: true,
    visible: getComputedStyle(ok).visibility === 'visible' && r.width > 0,
    hitsItself: !!hit && (hit === ok || ok.contains(hit)),
    hit: hit ? (hit.tagName + (hit.id ? '#' + hit.id : '')) : null,
  };
}
"""


def test_the_confirm_button_is_the_element_under_the_pointer(context_for, live_server: str) -> None:
    """Open a modal, raise a confirmation from inside it, and check that the
    thing under the Confirm button IS the Confirm button."""
    ctx = context_for("admin", 1440, 900)
    page = ctx.new_page()
    page.goto(live_server + "/dashboard/", wait_until="domcontentloaded")
    page.wait_for_timeout(800)

    # Any course this session can open; the first course card links to one.
    link = page.locator("a[href^='/dashboard/courses/']").first
    if not link.count():
        ctx.close()
        pytest.skip("no course reachable for this session")
    page.goto(live_server + link.get_attribute("href"), wait_until="domcontentloaded")
    page.wait_for_timeout(1500)

    opener = page.locator("#btnOpenRunChecks")
    if not opener.count():
        ctx.close()
        pytest.skip("this course offers no Run Checks action")
    opener.click()
    page.wait_for_timeout(600)
    page.locator("#btnRunChecks").click()
    page.wait_for_timeout(700)

    state = page.evaluate(_HIT_TEST)
    ctx.close()

    assert state["found"], "clicking Run selected checks raised no confirmation at all"
    assert state["visible"], "the confirmation is in the DOM but has no box on screen"
    assert state["hitsItself"], (
        "the Confirm button is not the element under its own centre - "
        f"{state['hit']} is on top of it, so the confirmation cannot be clicked"
    )
