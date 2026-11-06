"""Both course feeds keep missing metrics, sync states and sorting consistent."""

from __future__ import annotations

import os
import re

import pytest

from tests.e2e.scenarios.conftest import COURSE

pytestmark = pytest.mark.e2e

if not os.getenv("GITPULSE_E2E_BASE_URL"):
    pytest.skip("group states need a running server", allow_module_level=True)


@pytest.fixture(
    params=[
        (390, "light", "en", "normal"),
        (390, "dark", "sk", "normal"),
        (1440, "light", "en", "normal"),
        (1440, "dark", "sk", "normal"),
        (390, "dark", "en", "reduced"),
        (390, "light", "sk", "no-gsap"),
    ]
)
def group_page(browser, context_for, live_server, request):
    width, theme, locale, motion = request.param
    with browser.new_context(
        storage_state=context_for("admin").storage_state(),
        service_workers="block",
        viewport={"width": width, "height": 1000},
        is_mobile=width == 390,
        has_touch=width == 390,
        reduced_motion="reduce" if motion == "reduced" else "no-preference",
    ) as ctx:
        if motion == "no-gsap":
            ctx.route("**/gsap*.js*", lambda route: route.fulfill(body=""))
        ctx.add_cookies([{"name": "gp_lang", "value": locale, "url": live_server}])
        ctx.add_init_script("""
          window.__groupSources = [];
          const NativeSource = EventSource;
          window.EventSource = class {
            constructor(url, options) {
              if (!String(url).includes('/courses/')) return new NativeSource(url, options);
              this.url = String(url); this.listeners = {}; __groupSources.push(this);
            }
            addEventListener(name, fn) { this.listeners[name] = fn; }
            close() { this.closed = true; }
          };
        """)
        page = ctx.new_page()
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.on("console", lambda msg: errors.append(msg.text) if msg.type == "error" else None)
        page.bring_to_front()
        path = live_server + "/dashboard/courses/" + COURSE
        html = page.request.get(path).text()
        html = re.sub('data-theme-preference="[^"]*"', f'data-theme-preference="{theme}"', html)
        page.route(path, lambda route: route.fulfill(body=html, content_type="text/html"))
        data = page.request.get(path + "/live-data").json()
        page.route(path + "/live-data", lambda route: route.fulfill(json=data))
        page.goto(path)
        page.wait_for_function("() => document.documentElement.hasAttribute('data-gp-ready')")
        page.evaluate("""() => {
          window.__groupPaints = 0;
          window.__syncPaints = 0;
          const fetch = window.fetch;
          window.fetch = (...args) => fetch(...args).then(response => {
            if (String(args[0]).endsWith('/live-data')) {
              requestAnimationFrame(() => requestAnimationFrame(() => __groupPaints++));
            }
            if (String(args[0]).endsWith('/sync-status')) {
              requestAnimationFrame(() => requestAnimationFrame(() => __syncPaints++));
            }
            return response;
          });
        }""")
        team = data["teams"][0]
        row = page.locator(f'#teamsTable tr[data-team-id="{team["id"]}"]')
        row.wait_for(state="attached")
        yield page, row, data, team
        assert not errors, errors


def _paint(page, data, team, feed, values):
    if feed in ("live", "poll"):
        data["teams"] = [{**team, **values}]
        if values.get("avg_score") is not None:
            data["teams"][0]["avg_score"] = round(values["avg_score"])
        before = page.evaluate("__groupPaints")
    if feed == "live":
        page.evaluate(
            """course => window.dispatchEvent(new CustomEvent('gp:job-complete', {
          detail: {jobType:'sync:course:'+course, status:'done', meta:{courseId:course}},
        }))""",
            COURSE,
        )
        page.wait_for_function("before => __groupPaints > before", arg=before)
    else:
        payload = {
            "team_id": team["id"],
            "team_name": team["name"],
            "member_count": team["members"],
            **values,
        }
        if payload.get("avg_score") is not None:
            payload["avg_score"] /= 100
        if feed == "poll":
            snapshot = {
                "teams": [payload],
                "has_active_sync": False,
                "sync_running_count": 0,
                "sync_queued_count": 0,
                "sync_failed_count": 0,
                "sync_cancelled_count": 0,
            }
            page.route("**/courses/*/sync-status", lambda route: route.fulfill(json=snapshot))
            before_sync = page.evaluate("__syncPaints")
            page.evaluate("document.dispatchEvent(new Event('visibilitychange'))")
            page.wait_for_function("n => __syncPaints > n", arg=before_sync)
            page.wait_for_function("n => __groupPaints > n", arg=before)
            return
        page.evaluate(
            """team => {
          const source = __groupSources.find(s => !s.closed && s.url.endsWith('/sync-stream'));
          source.listeners.message({data:JSON.stringify({teams:[team],
            has_active_sync:false, sync_running_count:0, sync_queued_count:0,
            sync_failed_count:0, sync_cancelled_count:0})});
        }""",
            payload,
        )
        page.evaluate(
            """async () => {
              await new Promise(requestAnimationFrame); await new Promise(requestAnimationFrame);
            }"""
        )


@pytest.mark.parametrize("feed", ["live", "sync", "poll"])
def test_course_metrics_clear_restore_and_keep_status_tooltips(group_page, feed):
    page, row, data, team = group_page
    identity = row.locator("td").nth(1).inner_html()
    for score, light, sort, tip in (
        (87, "GREEN", "2", "All compliance checks are passing"),
        (None, None, "3", None),
        (0, "RED", "0", "Critical compliance checks are failing"),
        (65, "YELLOW", "1", "Some compliance checks need attention"),
        (76.5, "GREEN", "2", "All compliance checks are passing"),
        (75.5, "GREEN", "2", "All compliance checks are passing"),
    ):
        iso = "2026-11-04T07:00:00Z" if score else None
        _paint(
            page,
            data,
            team,
            feed,
            {
                "avg_score": score,
                "traffic_light": light,
                "sync_status": None,
                "last_updated": "2026-11-04 07:00" if iso else None,
                "last_updated_iso": iso,
            },
        )
        assert row.locator("td").nth(3).inner_text() == (
            "-" if score is None else f"{round(score)}%"
        )
        status = row.locator("td").nth(4)
        assert status.get_attribute("data-sort-value") == sort
        assert status.locator(".badge").inner_text() == page.evaluate(
            "s => GP.t(s)", light or "N/A"
        )
        assert status.locator(".badge").get_attribute("data-tippy-content") == (
            page.evaluate("s => GP.t(s)", tip) if tip else None
        )
        if iso:
            assert row.locator("td").nth(5).locator("time").get_attribute("datetime") == iso
        else:
            assert row.locator("td").nth(5).inner_text() == "-"
        assert row.locator("td").nth(5).get_attribute("data-sort-value") == (iso or "")
        assert row.locator("td").nth(1).inner_html() == identity


def test_live_metrics_keep_retry_notes_until_the_job_finishes(group_page):
    page, row, data, team = group_page
    _paint(
        page,
        data,
        team,
        "sync",
        {
            "avg_score": 87,
            "traffic_light": "GREEN",
            "sync_status": "running",
            "sync_note": "Retrying (2/3)...",
        },
    )
    assert row.locator("td").nth(4).get_attribute("data-sort-value") == "4"
    for state in ("running", "completed"):
        _paint(
            page,
            data,
            team,
            "live",
            {
                "avg_score": 90,
                "traffic_light": "GREEN",
                "sync_status": state,
                "last_updated": "2026-11-04 07:00",
                "last_updated_iso": "2026-11-04T07:00:00Z",
            },
        )
        status, updated = row.locator("td").nth(4), row.locator("td").nth(5)
        assert status.get_attribute("data-sort-value") == ("4" if state == "running" else "2")
        assert status.inner_text() == (
            "RETRY 2/3" if state == "running" else page.evaluate("GP.t('GREEN')")
        )
        if state == "running":
            assert updated.inner_text() == "Retrying (2/3)..."
        else:
            assert updated.locator("time").get_attribute("datetime") == "2026-11-04T07:00:00Z"
            assert updated.get_attribute("data-sort-value") == "2026-11-04T07:00:00Z"


def test_sync_data_cannot_turn_a_deleted_group_into_a_live_group(group_page):
    page, row, data, team = group_page
    row.evaluate("row => row.dataset.teamInactive = 'true'")
    _paint(
        page,
        data,
        team,
        "sync",
        {"avg_score": 87, "traffic_light": "GREEN", "sync_status": "running"},
    )
    assert row.locator("td").nth(4).locator(".badge").text_content() == page.evaluate(
        "GP.t('Deleted')"
    )
