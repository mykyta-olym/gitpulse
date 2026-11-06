"""History views agree after refreshes, including missing and zero scores."""

from __future__ import annotations

import json
import os
import re

import pytest

pytestmark = pytest.mark.e2e
STUDENT_PATH = os.getenv("GITPULSE_E2E_HISTORY_STUDENT_PATH")
if not os.getenv("GITPULSE_E2E_BASE_URL") or not STUDENT_PATH:
    pytest.skip("needs a local student fixture", allow_module_level=True)


def _week(number, score, checks=True):
    return {
        "week_number": number,
        "snapshot_date": "2026-10-20",
        "overall_score": score,
        "mr_score": score,
        "review_score": score,
        "ci_score": score,
        "issue_score": score,
        "improvement_delta": 0,
        "checks_detail": {
            "R01": {
                "name": "Owned history check",
                "pass": bool(score),
                "expected": score is not None,
            }
        }
        if checks
        else {},
    }


@pytest.fixture(params=[(390, "light"), (390, "dark"), (1440, "light"), (1440, "dark")])
def history_page(browser, context_for, live_server, request):
    width, theme = request.param
    with browser.new_context(
        storage_state=context_for("admin").storage_state(),
        service_workers="block",
        viewport={"width": width, "height": 1000},
        has_touch=width == 390,
        is_mobile=width == 390,
    ) as ctx:
        state = {"data": [_week(1, 0.82)], "hold": False, "pending": [], "error": False, "reads": 0}
        errors, writes = [], []
        page = ctx.new_page()
        page.bring_to_front()
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.on(
            "console",
            lambda msg: (
                errors.append(msg.text)
                if msg.type == "error" and not (state["error"] and "503" in msg.text)
                else None
            ),
        )

        def read_only(route):
            if route.request.method in {"GET", "HEAD"}:
                route.continue_()
            else:
                writes.append(route.request.url)
                route.abort()

        def profile(route):
            response = route.fetch()
            html = re.sub(
                r'(<script\b[^>]*id="gp-student-history"[^>]*>).*?(</script>)',
                lambda match: match[1] + json.dumps({"history": state["data"]}) + match[2],
                response.text(),
                flags=re.S,
            )
            route.fulfill(response=response, body=html)

        def history(route):
            state["reads"] += 1
            if state["hold"]:
                state["pending"].append(route)
            elif state["error"]:
                route.fulfill(status=503, json={"detail": "Owned history unavailable"})
            else:
                route.fulfill(json=state["data"])

        ctx.route("**/*", read_only)
        ctx.route("**/dashboard/students/**", profile)
        ctx.route("**/api/v1/compliance/**/student/**", history)
        page.goto(live_server + STUDENT_PATH)
        page.wait_for_function("() => document.documentElement.hasAttribute('data-gp-ready')")
        page.evaluate("theme => document.documentElement.dataset.theme = theme", theme)
        yield page, state
        assert not errors, errors
        assert not writes, writes


def _refresh(page, state, data):
    state["data"] = data
    page.locator("#btnRefreshHistory").click()
    page.wait_for_function(
        "() => document.querySelector('#complianceHistoryPanel > .card-body')"
        ".getAttribute('aria-busy') !== 'true'"
    )


def _radar(page):
    page.locator("#skillRadarCanvas").scroll_into_view_if_needed()
    page.wait_for_function("() => !!Chart.getChart('skillRadarCanvas')")


@pytest.mark.parametrize("layout", ["fixed", "fluid"])
def test_history_views_follow_missing_zero_empty_and_recovered_data(history_page, layout):
    page, state = history_page
    page.evaluate("layout => document.documentElement.dataset.layoutWidth = layout", layout)
    _radar(page)
    assert page.locator("#summaryCurrentScore").inner_text() == "82%"
    assert page.locator("#radarWeekLabel").inner_text() == "W1"
    geometry = page.locator("#checkHeatmapBody-wrap").evaluate("""el => ({
      box: el.getBoundingClientRect().height,
      table: el.querySelector('table').getBoundingClientRect().height,
      reservation: el.style.minHeight
    })""")
    assert geometry["reservation"] == ""
    assert abs(geometry["box"] - geometry["table"]) <= 1

    _refresh(page, state, [_week(2, 0.4, checks=False)])
    assert not page.locator("#checkHeatmapPanel").is_visible()
    assert page.locator("#checkHeatmapBody tr").count() == 0
    assert page.locator("#checkHeatmapHead tr").count() == 0
    assert page.locator("#summaryCurrentScore").inner_text() == "40%"

    _refresh(page, state, [_week(3, None)])
    assert not page.locator("#skillRadarCanvas").is_visible()
    assert not page.evaluate("() => !!Chart.getChart('skillRadarCanvas')")
    assert page.locator("#skillRadarEmpty").is_visible()
    assert not page.locator("#weekSummaryStats").is_visible()
    assert page.locator("#radarWeekLabel").inner_text() == ""
    assert page.locator("#checkHeatmapBody .hm-cell--na").count() == 1

    _refresh(page, state, [_week(4, 0)])
    _radar(page)
    assert page.locator("#summaryCurrentScore").inner_text() == "0%"
    assert page.locator("#weekSummaryStats").is_visible()
    assert page.locator("#radarWeekLabel").inner_text() == "W4"
    assert (
        page.evaluate("() => Chart.getChart('skillRadarCanvas').data.datasets[0].data") == [0] * 4
    )
    assert page.locator("#checkHeatmapBody .hm-cell--fail").count() == 1

    _refresh(page, state, [])
    assert not page.evaluate("() => !!Chart.getChart('historyCanvas')")
    assert not page.locator("#checkHeatmapPanel").is_visible()
    assert page.locator("#checkHeatmapBody tr").count() == 0
    assert page.locator("#radarWeekLabel").inner_text() == ""
    assert page.locator("#historyBody .table-empty-state").is_visible()

    _refresh(page, state, [_week(5, 1)])
    _radar(page)
    assert page.locator("#summaryCurrentScore").inner_text() == "100%"
    colors = []
    for accent in ("blue", "green"):
        color = page.evaluate(
            """accent => {
          document.documentElement.dataset.accent = accent;
          window.dispatchEvent(new Event('gp:themechange'));
          const chart = Chart.getChart('historyCanvas');
          const style = getComputedStyle(document.querySelector('#historyBody .progress-bar'));
          return {fill: style.backgroundColor,
            chart: chart.data.datasets[0].borderColor, theme: GP.chartTheme.colors.brand,
            gradient: style.backgroundImage};
        }""",
            accent,
        )
        assert color["chart"] == color["theme"]
        assert color["gradient"] == "none"
        colors.append(color["fill"])
    assert colors[0] != colors[1]
    before = page.locator("#historyBody").inner_text()
    state["error"] = True
    _refresh(page, state, state["data"])
    page.locator(".toast").filter(has_text="Owned history unavailable").wait_for()
    assert page.locator(".toast").filter(has_text="Owned history unavailable").count() == 1
    assert page.locator("#historyBody").inner_text() == before
    assert page.locator("#summaryCurrentScore").inner_text() == "100%"
    state["error"] = False

    # A slow retry preserves real rows and geometry while the shared region owns it.
    state["hold"] = True
    widths = page.locator("#historyTable th").evaluate_all(
        "nodes => nodes.map(node => node.getBoundingClientRect().width)"
    )
    page.locator("#btnRefreshHistory").click()
    page.wait_for_function("() => document.querySelector('#complianceHistoryPanel .is-refreshing')")
    assert state["pending"], "the history read was not held"
    assert page.locator("#btnRefreshHistory").get_attribute("aria-busy") == "true"
    assert page.locator("#historyBody").inner_text() == before
    assert (
        page.locator("#historyTable th").evaluate_all(
            "nodes => nodes.map(node => node.getBoundingClientRect().width)"
        )
        == widths
    )
    state["pending"].pop().fulfill(json=[_week(6, 0.5)])
    page.wait_for_function(
        "() => document.getElementById('summaryCurrentScore').textContent === '50%'"
    )
    assert not page.locator("#complianceHistoryPanel .is-refreshing").count()
    assert not page.locator("#historyBody .table-loading-row").count()


def test_summary_is_available_before_deferred_chart_drawing(history_page):
    page, state = history_page
    # Reset the real chart to a below-fold position while refreshing its data.
    page.locator("#complianceHistoryPanel").evaluate("""el => {
      el.style.marginTop = '1600px';
      document.querySelector('.gl-page-content').scrollTop = 0;
      delete document.getElementById('skillRadarCanvas').dataset.gpEntered;
    }""")
    state["data"] = [_week(2, 0.6)]
    page.evaluate("() => document.getElementById('btnRefreshHistory').click()")
    page.wait_for_function("() => document.getElementById('radarWeekLabel').textContent === 'W2'")
    assert page.locator("#summaryCurrentScore").inner_text() == "60%"
    assert page.evaluate("() => !!document.getElementById('skillRadarCanvas')._gpEntry")
    assert not page.evaluate("() => !!Chart.getChart('skillRadarCanvas')")
    page.evaluate("() => GP.navigateTo('/dashboard/admin/users')")
    page.wait_for_url("**/dashboard/admin/users")
    assert page.evaluate(
        "() => !Chart.getChart('skillRadarCanvas') && !Chart.getChart('historyCanvas')"
    )


@pytest.mark.parametrize("initial", ["empty", "unscored", "zero"])
def test_initial_cached_history_uses_the_same_terminal_states(history_page, initial):
    page, state = history_page
    state["data"] = [] if initial == "empty" else [_week(1, None if initial == "unscored" else 0)]
    state["reads"] = 0
    page.reload()
    page.wait_for_function("() => document.documentElement.hasAttribute('data-gp-ready')")
    assert state["reads"] == 0
    assert not page.locator("#historyBody .table-loading-row").count()
    if initial == "zero":
        assert page.locator("#summaryCurrentScore").inner_text() == "0%"
        assert page.locator("#weekSummaryStats").is_visible()
    else:
        assert page.locator("#skillRadarEmpty").is_visible()
        assert not page.locator("#weekSummaryStats").is_visible()
        assert page.locator("#radarWeekLabel").inner_text() == ""
