"""Action columns keep their alignment and spacing across table renderers."""

from __future__ import annotations

import json

import pytest

pytestmark = pytest.mark.e2e


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


def _table_layout(page, table):
    table.scroll_into_view_if_needed()
    table.evaluate("el => { el.closest('.table-responsive').scrollLeft = el.scrollWidth; }")
    page.wait_for_function("() => !document.querySelector('#main-content .is-loading')")
    result = table.evaluate("""table => {
      const header = table.querySelector('thead th:last-child');
      const h = getComputedStyle(header), hr = header.getBoundingClientRect();
      const viewport = table.closest('.table-responsive').getBoundingClientRect();
      const selector = 'tbody > tr:not(.table-detail-row) > td:last-child:not([colspan])';
      const cells = [...table.querySelectorAll(selector)];
      const groups = cells.map(cell => {
        const buttons = [...cell.querySelectorAll('.btn')].map(b => b.getBoundingClientRect());
        const c = getComputedStyle(cell), cr = cell.getBoundingClientRect();
        return {padding: c.padding, align: c.textAlign,
          offset: buttons.length ? hr.right - parseFloat(h.paddingRight) - buttons.at(-1).right : 0,
          inside: !buttons.length || (buttons[0].left >= viewport.left - 1 &&
            buttons.at(-1).right <= viewport.right + 1),
          fits: !buttons.length || buttons[0].left >= cr.left + parseFloat(c.paddingLeft) - 1,
          gaps: buttons.slice(1).map((b, i) => b.left - buttons[i].right),
          oneLine: buttons.every(b => Math.abs(b.top - buttons[0].top) < 1)};
      });
      return {header: {font: h.fontSize, weight: h.fontWeight, color: h.color,
        transform: h.textTransform, padding: h.padding},
        bodyPadding: getComputedStyle(table.closest('.card-body')).padding, groups};
    }""")
    assert result["groups"], "needs data rows with action cells"
    assert result["header"]["transform"] == "none"
    for group in result["groups"]:
        assert group["align"] == "right"
        assert abs(group["offset"]) < 1
        assert group["inside"]
        assert group["fits"]
        assert group["oneLine"]
        assert all(abs(gap - 4) < 1 for gap in group["gaps"])
    return result


@pytest.mark.parametrize(
    ("width", "layout"), [(1440, "fixed"), (2560, "fixed"), (2560, "fluid"), (390, "fluid")]
)
@pytest.mark.parametrize("theme", ["light", "dark"])
def test_jobs_and_archived_courses_use_the_standard_table(
    browser, admin_context, live_server, width, layout, theme
):
    with browser.new_context(
        storage_state=admin_context.storage_state(),
        service_workers="block",
        viewport={"width": width, "height": 1000},
        has_touch=width == 390,
    ) as context:
        context.add_cookies([{"name": "gp_lang", "value": "en", "url": live_server}])
        page = context.new_page()
        page.bring_to_front()
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        jobs = [
            {
                "id": f"00000000-0000-0000-0000-00000000000{i}",
                "job_type": "enrich",
                "status": "completed" if i == 1 else "running",
                "enqueued_at": "2026-10-22T10:00:00Z",
                "started_at": "2026-10-22T10:00:00Z",
                "completed_at": "2026-10-22T10:00:01Z" if i == 1 else None,
                "duration_ms": 503,
                "result_summary": "Data already up to date" if i == 1 else "",
                "rq_job_id": f"job-{i}",
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

        def appearance():
            page.evaluate(
                """({theme, layout}) => {
                  document.documentElement.dataset.theme = theme;
                  document.documentElement.dataset.layoutWidth = layout;
                  window.dispatchEvent(new Event('resize'));
                }""",
                {"theme": theme, "layout": layout},
            )

        page.goto(live_server + "/dashboard/admin/system")
        appearance()
        page.locator("#btnRefreshJobs").click()
        page.wait_for_function(
            "() => document.querySelectorAll('#jobsTableBody > .job-row').length === 2"
        )
        jobs_layout = _table_layout(page, page.locator("#jobsTable"))
        assert page.locator("#jobsTableBody .badge").evaluate_all("""badges => badges.every(b => {
          const cell = b.closest('td'), css = getComputedStyle(cell);
          return b.getBoundingClientRect().width <= cell.getBoundingClientRect().width -
            parseFloat(css.paddingLeft) - parseFloat(css.paddingRight) + 0.5;
        })""")
        page.locator("#btnRefreshJobs").click()
        assert _table_layout(page, page.locator("#jobsTable")) == jobs_layout

        page.goto(live_server + "/dashboard/?period=all")
        appearance()
        archived = page.locator("#main-content .gl-home-archived")
        if not archived.count():
            pytest.skip("needs an archived course")
        archived.locator(".card-header").click()
        page.wait_for_function(
            """() => {
              const region = document.querySelector('.gl-home-archived .card-collapse-region');
              return region.style.height === 'auto' || !region.style.height;
            }"""
        )
        archived_layout = _table_layout(page, archived.locator("table"))
        assert archived_layout["header"] == jobs_layout["header"]
        assert archived_layout["bodyPadding"] == jobs_layout["bodyPadding"]
        assert archived_layout["groups"][0]["padding"] == jobs_layout["groups"][0]["padding"]

        page.goto(live_server + "/dashboard/admin/courses")
        appearance()
        _table_layout(page, page.locator("#adminCoursesTable"))
        assert errors == []


@pytest.mark.parametrize("width", [1440, 390])
def test_course_lifecycle_replaces_actions_inside_the_shared_group(
    browser, admin_context, live_server, width
):
    with browser.new_context(
        storage_state=admin_context.storage_state(),
        service_workers="block",
        viewport={"width": width, "height": 1000},
        has_touch=width == 390,
    ) as context:
        page = context.new_page()
        page.bring_to_front()
        page.goto(live_server + "/dashboard/admin/courses")
        row = (
            page.locator("#adminCoursesTable tr")
            .filter(has=page.locator(".btn-archive-course"))
            .first
        )
        if not row.count():
            pytest.skip("needs an active course")
        course_id = row.get_attribute("data-course-id")
        if not course_id:
            course_id = row.locator(".btn-archive-course").get_attribute("data-course-id")
        row = page.locator(f'#adminCoursesTable tr[data-course-id="{course_id}"]')
        calls = []

        def mutation(route):
            calls.append(route.request.url.rsplit("/", 1)[-1])
            route.fulfill(content_type="application/json", body='{"ok":true}')

        page.route(f"**/api/v1/courses/{course_id}/archive", mutation)
        page.route(f"**/api/v1/courses/{course_id}/activate", mutation)
        for action, next_action in [("archive", "activate"), ("activate", "archive")]:
            row.locator(f".btn-{action}-course").click()
            page.locator('#gpConfirmDialog [data-gp-confirm="ok"]').click()
            row.locator(f".gl-row-actions .btn-{next_action}-course").wait_for()
            _table_layout(page, page.locator("#adminCoursesTable"))
        assert calls == ["archive", "activate"]
        assert row.locator(".btn-delete-course").count() == 0
