"""Operational lists and modern theme colors work in the real browser."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

pytestmark = pytest.mark.e2e
ROOT = Path(__file__).resolve().parents[3]


def _mock_jobs_response(jobs: list[dict], job_types: list[str]) -> str:
    from starlette.requests import Request

    from app.api.dashboard.admin.system import _jobs_table_context
    from app.main import templates

    request = Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/dashboard/api/v1/admin/system/jobs",
            "query_string": b"lang=en",
            "headers": [(b"accept-language", b"en")],
        }
    )
    payload = {
        "jobs": jobs,
        "total": len(jobs),
        "job_types": job_types,
        "failure_history": {"available": True, "total": 0, "limit": 100},
    }
    ctx = _jobs_table_context(request, payload)
    payload["rows_html"] = bytes(
        templates.TemplateResponse(request, "partials/admin/_system_job_rows.html", ctx).body
    ).decode()
    payload["history_html"] = bytes(
        templates.TemplateResponse(request, "partials/admin/_system_failure_info.html", ctx).body
    ).decode()
    return json.dumps(payload)


@pytest.fixture
def operations_context(browser, admin_context, live_server):
    with browser.new_context(
        storage_state=admin_context.storage_state(), service_workers="block"
    ) as context:
        context.add_cookies([{"name": "gp_lang", "value": "en", "url": live_server}])
        yield context


def _student_url(page, base):
    page.goto(base + "/dashboard/")
    course = page.locator('a[href^="/dashboard/courses/"]').first.get_attribute("href")
    if not course:
        pytest.skip("needs a course with student compliance history")
    page.goto(base + course.split("?")[0])
    team = page.locator('a[href^="/dashboard/teams/"]').first
    if not team.count():
        pytest.skip("needs a group")
    page.goto(base + team.get_attribute("href"))
    student = page.locator('a[href^="/dashboard/students/"]').first
    if not student.count():
        pytest.skip("needs a student")
    return base + student.get_attribute("href")


@pytest.mark.parametrize(("width", "mode"), [(1440, "light"), (390, "dark")])
def test_compliance_charts_accept_modern_colors_and_follow_theme(
    operations_context, live_server, width, mode
):
    page = operations_context.new_page()
    page.set_viewport_size({"width": width, "height": 900})
    page.bring_to_front()
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.goto(_student_url(page, live_server))
    if not page.evaluate(
        "JSON.parse(document.getElementById('gp-student-history').textContent).history.length"
    ):
        pytest.skip("needs compliance snapshots")
    page.locator("#historyCanvas").scroll_into_view_if_needed()
    page.wait_for_function("() => !!Chart.getChart('historyCanvas')")
    for accent in ("default", "indigo", "blue", "green", "red", "gray"):
        result = page.evaluate(
            """({mode, accent}) => {
              const root = document.documentElement;
              root.dataset.theme = mode;
              root.dataset.accent = accent;
              window.dispatchEvent(new Event('gp:themechange'));
              const color = GP.chartTheme.colors.brand;
              const chart = Chart.getChart('historyCanvas');
              return {color, border: chart.data.datasets[0].borderColor,
                fill: chart.data.datasets[0].backgroundColor instanceof CanvasGradient,
                points: chart.data.labels.length};
            }""",
            {"mode": mode, "accent": accent},
        )
        assert result["border"] == result["color"]
        assert result["fill"]
        assert result["points"] > 0
    colors = page.evaluate("""() => {
      const ctx = document.createElement('canvas').getContext('2d');
      const gradient = ctx.createLinearGradient(0, 0, 0, 100);
      const values = ['color(srgb 0.560784 0.557647 0.576471)',
        'oklch(60% 0.15 270)', 'rgb(40 100 200 / 50%)', '#428fdc'];
      return values.map(value => {
        const result = GP.chartTheme.alpha(value, 0.2);
        gradient.addColorStop(0, result);
        return result;
      });
    }""")
    assert colors[0] == "rgba(143, 142, 147, 0.2)"
    assert all(value.startswith("rgba(") for value in colors)
    history = page.evaluate("JSON.parse(document.getElementById('gp-student-history').textContent)")
    history_url = "**/api/v1/compliance/**/student/**?weeks=52"
    page.route(history_url, lambda route: route.fulfill(content_type="application/json", body="[]"))
    page.locator("#btnRefreshHistory").click()
    page.wait_for_function("() => !Chart.getChart('historyCanvas')")
    assert page.locator("#skillRadarCanvas").count() == 1
    assert page.locator("#skillRadarEmpty").is_visible()
    page.unroute(history_url)
    page.route(
        history_url,
        lambda route: route.fulfill(
            content_type="application/json", body=json.dumps(history["history"])
        ),
    )
    page.locator("#btnRefreshHistory").click()
    page.wait_for_function("() => !!Chart.getChart('historyCanvas')")
    page.locator("#skillRadarCanvas").scroll_into_view_if_needed()
    page.wait_for_function("() => !!Chart.getChart('skillRadarCanvas')")
    if width == 390:
        page.locator("#mobileMenuBtn").click()
    page.locator('.gl-sidebar-item[href="/dashboard/admin/system"]').click()
    page.wait_for_url(live_server + "/dashboard/admin/system")
    assert (
        page.evaluate(
            "typeof Chart === 'undefined' ? 0 : "
            "Object.values(Chart.instances).filter(c => c.canvas.id === 'historyCanvas').length"
        )
        == 0
    )
    assert errors == []


@pytest.mark.parametrize("width", [1440, 390])
def test_job_filter_empty_state_and_queue_diagnostics(operations_context, live_server, width):
    page = operations_context.new_page()
    page.set_viewport_size({"width": width, "height": 900})
    page.bring_to_front()
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.route(
        "**/dashboard/api/v1/admin/system/stats",
        lambda route: route.fulfill(
            content_type="application/json",
            body='{"queues":{"high":2,"default":3,"low":0},"workers":0}',
        ),
    )
    page.route(
        "**/dashboard/api/v1/admin/system/jobs?*",
        lambda route: route.fulfill(
            content_type="application/json",
            body=_mock_jobs_response([], ["sync"]),
        ),
    )
    page.goto(live_server + "/dashboard/admin/system")
    page.wait_for_function(
        "() => document.getElementById('queueStatus').textContent.includes('queued jobs will wait')"
    )
    assert "queued jobs will wait" in page.locator("#queueStatus").inner_text()
    assert page.locator("#roleBreakdownCard").count() == 0
    assert page.locator("#jobsTable th.sortable").count() == 0
    page.locator("#jobStatusFilter_toggle").click()
    page.locator('#jobStatusFilter_options [data-value="failed"]').click()
    page.wait_for_function(
        "() => document.querySelector('#jobsTableBody .table-empty-row') !== null"
    )
    assert "0-0" in page.locator("#jobsPagination").inner_text()
    assert page.locator("#jobsPagination .pagination-next").is_disabled()
    page.locator("#jobStatusFilter_toggle").click()
    page.locator('#jobStatusFilter_options [data-value="cancelled"]').click()
    assert errors == []


def test_sse_short_greetings_do_not_reset_failure_backoff(browser):
    with browser.new_context(service_workers="block") as context:
        page = context.new_page()
        page.set_content("<main>SSE transport contract</main>")
        page.evaluate("""() => {
          window.GP = {};
          window.__timers = [];
          window.setTimeout = (callback, delay) => {
            const timer = {callback, delay}; __timers.push(timer); return timer;
          };
          window.clearTimeout = timer => {
            const index = __timers.indexOf(timer); if (index >= 0) __timers.splice(index, 1);
          };
          window.__sources = [];
          window.EventSource = class {
            constructor() { this.events = {}; __sources.push(this); }
            addEventListener(name, callback) { this.events[name] = callback; }
            close() { this.closed = true; }
          };
        }""")
        page.add_script_tag(path=str(ROOT / "src/app/templates/static/js/_parts/core/08-sse.js"))
        result = page.evaluate("""() => {
          let gaveUp = 0;
          const stream = GP.sse({url:'/stream', events:{connected() {}}, maxErrors:3,
            onGiveUp() { gaveUp++; }});
          const delays = [];
          for (let i = 0; i < 3; i++) {
            const source = __sources.at(-1);
            source.onopen(); source.events.connected({}); source.onerror();
            if (__timers.length) {
              const timer = __timers.shift(); delays.push(timer.delay); timer.callback();
            }
          }
          const failed = {gaveUp, errors:stream.errors, active:stream.active, delays};
          stream.reopen();
          __sources.at(-1).onopen();
          __timers.shift().callback();
          const recovered = stream.errors;
          stream.close();
          return {failed, recovered, timers:__timers.length};
        }""")
        assert result == {
            "failed": {"gaveUp": 1, "errors": 3, "active": False, "delays": [2000, 4000]},
            "recovered": 0,
            "timers": 0,
        }


@pytest.mark.parametrize(
    ("width", "theme"), [(1440, "light"), (1440, "dark"), (390, "light"), (390, "dark")]
)
def test_job_details_share_table_layout_and_do_not_repeat_short_results(
    operations_context, live_server, width, theme
):
    page = operations_context.new_page()
    page.set_viewport_size({"width": width, "height": 900})
    page.bring_to_front()
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    message = "Data already up to date"
    long_error = "GitLab returned an error: <request>\n" + "Cannot load the project. " * 20
    jobs = [
        {
            "id": f"00000000-0000-0000-0000-00000000000{i}",
            "job_type": "enrich",
            "status": "completed" if i == 1 else "failed",
            "enqueued_at": "2026-10-22T10:00:00Z",
            "started_at": "2026-10-22T10:00:00Z",
            "completed_at": "2026-10-22T10:00:01Z",
            "duration_ms": 503,
            "result_summary": message if i == 1 else "",
            "error_message": long_error if i == 2 else "",
            "rq_job_id": None,
        }
        for i in (1, 2)
    ]
    page.route(
        "**/dashboard/api/v1/admin/system/jobs?*",
        lambda route: route.fulfill(
            content_type="application/json",
            body=_mock_jobs_response(jobs, ["enrich"]),
        ),
    )
    page.goto(live_server + "/dashboard/admin/system")
    page.evaluate(
        """theme => {
      document.documentElement.dataset.theme = theme;
      window.dispatchEvent(new Event('gp:themechange'));
    }""",
        theme,
    )
    page.locator("#btnRefreshJobs").click()
    page.wait_for_function(
        "() => document.querySelectorAll('#jobsTableBody > .job-row').length === 2"
    )
    toggle = page.locator("[data-table-detail-toggle]").first
    toggle.focus()
    page.keyboard.press("Enter")
    details = page.locator(".table-detail-row").first
    assert details.is_visible()
    assert message not in details.inner_text()
    assert "2026-10-22" in details.inner_text()
    style = details.locator("td").evaluate("""cell => {
      const css = getComputedStyle(cell), list = cell.querySelector('dl');
      const viewport = cell.closest('.table-responsive').getBoundingClientRect();
      const rect = list.getBoundingClientRect();
      const values = [...list.querySelectorAll('dd')];
      return {position: css.position, align: css.textAlign,
        labels: getComputedStyle(list.querySelector('dt')).textTransform,
        inside: rect.left >= viewport.left && rect.right <= viewport.right + 1,
        valuesAligned: values.every(el =>
          el.getBoundingClientRect().left === values[0].getBoundingClientRect().left)};
    }""")
    assert style == {
        "position": "static",
        "align": "left",
        "labels": "none",
        "inside": True,
        "valuesAligned": True,
    }
    page.keyboard.press("Space")
    assert not details.is_visible()
    page.locator(".job-select").first.check()
    assert not details.is_visible()
    page.locator("[data-table-detail-toggle]").nth(1).click()
    error_details = page.locator(".table-detail-row").nth(1)
    assert long_error in error_details.inner_text()
    assert error_details.locator("request").count() == 0
    assert error_details.locator("pre").count() == 0
    assert "1-2" in page.locator("#jobsPagination").inner_text()
    assert errors == []
