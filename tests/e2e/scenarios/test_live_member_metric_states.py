"""Live member cells keep the server's grades, privacy and missing-data states."""

from __future__ import annotations

import os
import re

import pytest

pytestmark = pytest.mark.e2e

if not os.getenv("GITPULSE_E2E_BASE_URL"):
    pytest.skip("member updates need a running server", allow_module_level=True)


@pytest.fixture(
    params=[
        (390, "light", "normal"),
        (390, "dark", "normal"),
        (1440, "light", "normal"),
        (1440, "dark", "normal"),
        (390, "dark", "reduced"),
        (390, "light", "no-gsap"),
    ]
)
def member_page(browser, context_for, live_server, request):
    width, theme, motion = request.param
    with browser.new_context(
        storage_state=context_for("admin").storage_state(),
        viewport={"width": width, "height": 1000},
        is_mobile=width == 390,
        has_touch=width == 390,
        service_workers="block",
        reduced_motion="reduce" if motion == "reduced" else "no-preference",
    ) as context:
        context.add_cookies([{"name": "gp_lang", "value": "en", "url": live_server}])
        if motion == "no-gsap":
            context.route("**/gsap*.js*", lambda route: route.fulfill(body=""))
        page = context.new_page()
        page.bring_to_front()
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        yield page, theme
        assert not errors, errors


def _visit(page, live_server, kind, theme):
    scope = "teams" if kind == "team" else "projects"
    entity = os.environ["GITPULSE_E2E_TEAM_ID" if kind == "team" else "GITPULSE_E2E_PROJECT_ID"]
    path = f"{live_server}/dashboard/{scope}/{entity}"
    html = page.request.get(path).text()
    html = re.sub('data-theme-preference="[^"]*"', f'data-theme-preference="{theme}"', html)
    page.route(path, lambda route: route.fulfill(body=html, content_type="text/html"))
    data = page.request.get(path + "/live-data").json()
    page.goto(path)
    page.wait_for_function("() => document.documentElement.hasAttribute('data-gp-ready')")
    page.evaluate("""() => {
      window.__memberPaints = 0;
      const fetch = window.fetch;
      window.fetch = (...args) => fetch(...args).then(response => {
        if (String(args[0]).endsWith('/live-data')) {
          requestAnimationFrame(() => requestAnimationFrame(() => __memberPaints++));
        }
        return response;
      });
    }""")
    assert page.evaluate("document.documentElement.dataset.theme") == theme
    table = "#teamMembersTable" if kind == "team" else "#projectMembersTable"
    row = page.locator(
        table + " tr[data-student-id]:not([data-member-teacher]):not([data-member-mentor])"
    ).first
    row.wait_for(state="attached")
    student = next(s for s in data["students"] if s["id"] == row.get_attribute("data-student-id"))
    row = page.locator(table + f' tr[data-student-id="{student["id"]}"]')
    reads = []

    def respond(route):
        reads.append(route.request.url)
        route.fulfill(json=data)

    page.route(path + "/live-data", respond)
    return row, student, data, reads


def _refresh(page, reads):
    # Group visibility refreshes deliberately coalesce within 800 ms.
    if "/teams/" in page.url:
        page.wait_for_timeout(850)
    before = len(reads)
    page.evaluate("() => document.dispatchEvent(new CustomEvent('gp-tab-visible'))")
    page.wait_for_function("n => window.__memberPaints > n", arg=before)


@pytest.mark.parametrize("kind", ["team", "project"])
@pytest.mark.parametrize("category", ["student", "excluded", "teacher", "mentor"])
def test_metric_states_preserve_identity_and_server_visibility(
    member_page, live_server, kind, category
):
    page, theme = member_page
    row, student, data, reads = _visit(page, live_server, kind, theme)
    identity = row.locator("td").first.inner_html()
    row.evaluate(
        """(row, category) => {
      if (category === 'teacher') row.dataset.memberTeacher = '1';
      if (category === 'mentor') row.dataset.memberMentor = '1';
    }""",
        category,
    )
    config = page.locator(f"#gp-{kind}-detail-config").evaluate("el => JSON.parse(el.textContent)")
    score_cell = row.locator("td").nth(1 if kind == "team" else len(config["checkCodes"]) + 1)
    for score in (92, 0, None, 77):
        active = score is not None and score > 0
        updated = {
            **student,
            "score": score,
            "excluded_from_scoring": category == "excluded",
            "checks_passed": int(active),
            "checks_total": 2,
            "mrs_created": int(active),
            "issues_assigned": int(active),
            "pipeline_success": int(active),
            "pipeline_total": int(active),
            "checks": {
                code: {"pass": True, "expected": True} for code in config.get("checkCodes", [])
            },
        }
        data["students"] = [updated]
        _refresh(page, reads)
        visible = score is not None and (
            category in ("student", "excluded") or (kind == "team" and active)
        )
        assert score_cell.inner_text() == (f"{score}%" if visible else "-")
        assert score_cell.get_attribute("data-sort-value") == (str(score) if visible else "-1")
        assert row.locator("td").first.inner_html() == identity
        if visible:
            expected = page.evaluate(
                "p => GP.badgeHtml(p.score+'%', "
                "p.score>=p.green?'green':p.score>=p.yellow?'amber':'red')",
                {"score": score, "green": config["greenPct"], "yellow": config["yellowPct"]},
            )
            assert score_cell.inner_html() == expected
        elif kind == "team":
            assert row.locator("td").all_inner_texts()[1:] == ["-"] * 5
        else:
            assert all(text == "-" for text in row.locator("td").all_inner_texts()[1:-1])


def test_shared_score_component_accepts_zero_thresholds_without_repainting(
    member_page, live_server
):
    page, theme = member_page
    row, _, _, _ = _visit(page, live_server, "team", theme)
    cell = row.locator("td").nth(1)
    result = cell.evaluate("""cell => {
      GP.updateScoreCell(cell, 0, 0, 0);
      const html = cell.innerHTML;
      const observer = new MutationObserver(() => {});
      observer.observe(cell, {attributes:true,childList:true,subtree:true});
      GP.updateScoreCell(cell, 0, 0, 0);
      const mutations = observer.takeRecords().length;
      observer.disconnect();
      return {html, mutations};
    }""")
    assert result["html"] == page.evaluate("GP.badgeHtml('0%', 'green')")
    assert result["mutations"] == 0


def test_check_tooltips_follow_the_current_result(member_page, live_server):
    page, theme = member_page
    row, student, data, reads = _visit(page, live_server, "project", theme)
    code = page.locator("#gp-project-detail-config").evaluate(
        "el => JSON.parse(el.textContent).checkCodes[0]"
    )
    cell = row.locator("td").nth(1)
    name = page.locator("#projectMembersTable thead th").nth(1).get_attribute("data-tippy-content")
    for passed, expected, label, tooltip in (
        (True, True, "Pass", "Pass"),
        (False, True, "Fail", "Fail"),
        (None, True, "N/A", "N/A"),
        (False, False, "Not yet required", "not yet required"),
    ):
        data["students"] = [
            {**student, "score": 80, "checks": {code: {"pass": passed, "expected": expected}}}
        ]
        _refresh(page, reads)
        assert cell.get_attribute("aria-label") == label
        assert cell.get_attribute("data-tippy-content") == f"{name}: {tooltip}"
