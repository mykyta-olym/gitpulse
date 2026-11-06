"""MR membership, assignment and discussion evidence must stay distinct."""

import os

import pytest

pytestmark = pytest.mark.e2e

PATH = os.getenv("GITPULSE_E2E_MR_STUDENT_PATH")
if not os.getenv("GITPULSE_E2E_BASE_URL") or not PATH:
    pytest.skip(
        "MR evidence needs the local MR fixture and a running server", allow_module_level=True
    )


@pytest.mark.parametrize("width", [390, 1440])
@pytest.mark.parametrize("theme", ["light", "dark"])
def test_merge_requests_explain_their_commits_and_participants(
    context_for, live_server, width, theme
):
    context = context_for("admin", width=width)
    page = context.new_page()
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.on(
        "console", lambda message: errors.append(message.text) if message.type == "error" else None
    )
    response = page.goto(live_server + PATH + "?lang=en")
    assert response.status == 200
    page.wait_for_function("() => !!GP && document.documentElement.hasAttribute('data-gp-ready')")
    page.evaluate("theme => document.documentElement.dataset.theme = theme", theme)
    first = page.locator("#mr-1")
    assert first.locator(".mr-commit").count() == 2
    assert "Saved branch commits" in first.locator(".mr-section-toggle").first.inner_text()
    assert "authorship is not verified" in first.locator(".gitlab-alert").inner_text()
    assigned = first.locator(".mr-people-group").filter(has_text="Assigned reviewers")
    assert "Assigned reviewer" in assigned.inner_text()
    assert "Discussion contributor" not in assigned.inner_text()
    assert "1 comment" in assigned.inner_text()
    others = first.locator(".mr-people-group").filter(has_text="Discussion participants")
    assert "Discussion contributor" in others.inner_text()
    assert "Assigned reviewer" not in others.inner_text()
    assert (
        "Reviewers: Assigned reviewer, Discussion contributor"
        in first.locator(".mr-desc").inner_text()
    )
    assert not first.locator(".wf-step").nth(4).evaluate("el => el.classList.contains('is-done')")

    empty = page.locator("#mr-2")
    assert empty.locator(".mr-commit").count() == 0
    assert empty.locator(".gitlab-alert").count() == 0
    assert "No commits" in empty.inner_text()
    assert "Awaiting review" in empty.inner_text()
    assert not empty.locator(".wf-step").nth(3).evaluate("el => el.classList.contains('is-done')")

    partial = page.locator("#mr-3")
    assert "1 / 2" in partial.locator(".gitlab-alert").inner_text()
    assert "Approval without comment" in partial.locator(".mr-people").inner_text()
    assert "Approved" in partial.locator(".mr-people").inner_text()
    assert partial.locator(".wf-step").nth(4).evaluate("el => el.classList.contains('is-done')")
    assert page.locator("#mr-4 .gitlab-alert").count() == 0
    assert page.locator("#mr-4 .mr-commit").count() == 2
    assert "Also by:" in page.locator("#mr-4").inner_text()
    assert "Commit data unavailable" not in page.locator("body").inner_text()
    for link in first.locator(".gitlab-alert a").all():
        assert link.get_attribute("href").endswith("/merge_requests/1/commits")
    overflow = page.locator(".mr-people").evaluate_all(
        "els => els.filter(el => el.scrollWidth > el.clientWidth + 1).map(el => el.outerHTML)"
    )
    assert not overflow, overflow
    if width == 1440:
        spacing = first.locator(".mr-people").evaluate("""el => {
          const groups = [...el.children].map(node => node.getBoundingClientRect());
          return {gap: parseFloat(getComputedStyle(el).columnGap),
            distances: groups.slice(1).map((rect, i) => rect.left - groups[i].right)};
        }""")
        assert all(abs(distance - spacing["gap"]) <= 1 for distance in spacing["distances"])
    page.locator("#mr-1 .mr-people").screenshot(
        path=f"output/playwright/mr-people-{width}-{theme}.png"
    )
    assert not errors, errors
