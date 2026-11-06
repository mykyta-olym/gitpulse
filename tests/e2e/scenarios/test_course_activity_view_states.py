"""Activity refreshes the server's components, with real local DB and cache states."""

from __future__ import annotations

import asyncio
import os
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from urllib.parse import urlsplit

import pytest
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

pytestmark = pytest.mark.e2e
if not os.getenv("GITPULSE_E2E_ACTIVITY_FIXTURE"):
    pytest.skip("needs an owned local Activity fixture", allow_module_level=True)


@pytest.fixture
def activity_data(live_server):
    from app.models import Course, GitLabProject, MergeRequest, Pipeline, Team

    assert urlsplit(live_server).hostname in {"127.0.0.1", "localhost"}
    database = os.environ["DATABASE_URL"]
    assert urlsplit(database).hostname in {"127.0.0.1", "localhost"}
    course, group = uuid.uuid4(), uuid.uuid4()
    projects = [uuid.uuid4(), uuid.uuid4()]

    async def write(kind):
        engine = create_async_engine(database, poolclass=NullPool)
        try:
            async with async_sessionmaker(engine)() as db:
                if kind == "create":
                    db.add(
                        Course(
                            id=course,
                            code="act-" + course.hex[:8],
                            name="Activity states",
                            academic_year="2026/2027",
                        )
                    )
                    await db.flush()
                    db.add_all(
                        Team(
                            id=group if i == 0 else uuid.uuid4(),
                            course_id=course,
                            name=f"Activity group {i:02}",
                        )
                        for i in range(26)
                    )
                    await db.flush()
                    db.add_all(
                        GitLabProject(
                            id=p,
                            team_id=group,
                            gitlab_project_id=p.int % 10**12,
                            gitlab_project_path=f"qa/activity-{p.hex}",
                        )
                        for p in projects
                    )
                elif kind == "delete":
                    await db.execute(delete(Course).where(Course.id == course))
                else:
                    await db.execute(delete(Pipeline).where(Pipeline.project_id.in_(projects)))
                    await db.execute(
                        delete(MergeRequest).where(MergeRequest.project_id.in_(projects))
                    )
                    statuses = {
                        "scored": ["success", "failed"],
                        "running": ["running"],
                        "other": ["canceled"],
                        "zero": ["failed"],
                        "empty": [],
                    }[kind]
                    for i, status in enumerate(statuses):
                        db.add(
                            Pipeline(
                                project_id=projects[i],
                                gitlab_pipeline_id=uuid.uuid4().int % 10**12,
                                status=status,
                                created_at=datetime.now(UTC) + timedelta(seconds=i),
                            )
                        )
                    if statuses:
                        db.add(
                            MergeRequest(
                                project_id=projects[0],
                                gitlab_id=uuid.uuid4().int % 10**12,
                                gitlab_iid=1,
                                title="Activity request",
                                state="opened",
                                created_at=datetime.now(UTC),
                            )
                        )
                await db.commit()
        finally:
            await engine.dispose()

    def change(kind):
        with ThreadPoolExecutor(max_workers=1) as worker:
            worker.submit(asyncio.run, write(kind)).result()

    change("create")
    try:
        yield str(course), change
    finally:
        change("delete")


@pytest.fixture(params=[(390, "light"), (390, "dark"), (1440, "light"), (1440, "dark")])
def activity_page(browser, context_for, live_server, activity_data, request):
    course, change = activity_data
    width, theme = request.param
    with browser.new_context(
        storage_state=context_for("admin").storage_state(),
        service_workers="block",
        viewport={"width": width, "height": 1000},
    ) as ctx:
        ctx.add_init_script("""(() => {
          const fetch = window.fetch;
          window.__activity = {
            reads:0, hold:false, fail:false, pending:[], signals:[], health:'ok', lastHealth:''};
          document.addEventListener('gp-health-change', e => {
            __activity.lastHealth = e.detail.current;
          });
          window.fetch = (url, opts) => {
            if (String(url) === '/health') return Promise.resolve(new Response(
              JSON.stringify({status:__activity.health}),
              {headers:{'Content-Type':'application/json'}}));
            if (String(url).includes('/activity')
                && opts?.headers?.['Cache-Control'] === 'no-cache') {
              const state = __activity;
              state.reads++;
              state.signals.push(opts.signal);
              if (state.fail) return Promise.resolve(new Response(
                JSON.stringify({detail:'Activity unavailable'}),
                {status:503, headers:{'Content-Type':'application/json'}}));
              const response = fetch(url, opts);
              if (state.hold) return response.then(r => new Promise(
                resolve => state.pending.push(() => resolve(r))));
              return response;
            }
            return fetch(url, opts);
          };
        })();""")
        errors, writes = [], []
        ctx.route(
            "**/*",
            lambda r: (
                r.continue_()
                if r.request.method in {"GET", "HEAD"}
                else (writes.append(r.request.url), r.abort())
            ),
        )
        page = ctx.new_page()
        page.bring_to_front()
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.on("console", lambda msg: errors.append(msg.text) if msg.type == "error" else None)
        page.goto(f"{live_server}/dashboard/courses/{course}/activity?lang=en")
        page.wait_for_function(
            "() => GP.courseActivityCleanup"
            " && document.documentElement.hasAttribute('data-gp-ready')"
        )
        page.evaluate(
            "theme => {document.documentElement.dataset.theme=theme;"
            " window.dispatchEvent(new CustomEvent('gp:themechange'));}",
            theme,
        )
        yield page, course, change
        assert not errors, errors
        assert not writes, writes


def _refresh(page):
    page.locator("#btnRefreshActivity").click()
    page.wait_for_function(
        "() => document.querySelector('.gl-tab-content').getAttribute('aria-busy') !== 'true'"
    )


@pytest.mark.parametrize("layout", ["fixed", "fluid"])
def test_activity_keeps_server_rows_tabs_pagination_and_honest_chart_states(activity_page, layout):
    page, _, change = activity_page
    page.evaluate("layout => document.documentElement.dataset.layoutWidth = layout", layout)
    assert page.locator("#activityHealthCard").get_by_text("No pipelines", exact=True).is_visible()
    assert page.locator("#pipelineDoughnut").count() == 0
    change("scored")
    _refresh(page)
    page.wait_for_function("() => !!Chart.getChart('pipelineDoughnut')")
    assert page.locator("#pipelineHealthPct").inner_text() == "50%"
    assert (
        page.locator("#groupActivityTable tbody tr").first.locator("td").last.inner_text()
        == "Failed"
    )
    assert page.locator("#recentMrsTable tbody tr").count() == 1
    assert page.locator("#actStatPassed").inner_text() == "1"
    assert page.locator("#actStatFailed").inner_text() == "1"
    assert page.evaluate("() => Chart.getChart('pipelineDoughnut').data.datasets[0].data") == [
        1,
        1,
        0,
        0,
        0,
    ]
    page.locator("#activityViews [data-value='mrs']").click()
    _refresh(page)
    assert page.locator("#tab-panel-mrs").is_visible()
    assert not page.locator("#tab-panel-groups").is_visible()
    page.locator("#activityViews [data-value='groups']").click()
    page.locator("#groupActivityTable th[data-sort-key='team']").click()
    scroll_left = page.evaluate(
        "() => {const s=document.querySelector('#groupActivityTable').closest('.table-responsive');"
        " s.scrollLeft=40; return s.scrollLeft;}"
    )
    page.evaluate(
        "() => {const p=document.querySelector('#groupActivityTable tbody')._clientPaginator;"
        " p.changePageSize(25); p.goToPage(2);}"
    )
    _refresh(page)
    assert (
        page.evaluate(
            "() => GP.SortableTable.getInstance("
            "document.getElementById('groupActivityTable')).sortDir"
        )
        == "desc"
    )
    assert (
        page.locator("#groupActivityTable tbody tr:visible")
        .first.inner_text()
        .startswith("Activity group 00")
    )
    assert (
        abs(
            page.evaluate(
                "() => document.querySelector('#groupActivityTable')"
                ".closest('.table-responsive').scrollLeft"
            )
            - scroll_left
        )
        < 1
    )
    assert (
        page.evaluate(
            "() => document.querySelector('#groupActivityTable tbody')._clientPaginator.currentPage"
        )
        == 2
    )
    change("running")
    _refresh(page)
    assert page.locator("#pipelineHealthPct").inner_text() == "-"
    change("other")
    _refresh(page)
    assert page.locator("#pipelineHealthPct").inner_text() == "-"
    assert page.evaluate("() => Chart.getChart('pipelineDoughnut').data.datasets[0].data") == [
        0,
        0,
        0,
        0,
        1,
    ]
    change("zero")
    _refresh(page)
    assert page.locator("#pipelineHealthPct").inner_text() == "0%"
    change("empty")
    _refresh(page)
    assert page.locator("#pipelineDoughnut").count() == 0
    assert not page.evaluate("() => Object.keys(Chart.instances).length")
    assert page.locator("#activityHealthCard").get_by_text("No pipelines", exact=True).is_visible()
    assert page.locator("#recentMrsTable").count() == 0


def test_activity_busy_failure_retry_and_theme_follow_the_real_result(activity_page):
    page, _, change = activity_page
    change("scored")
    _refresh(page)
    button = page.locator("#btnRefreshActivity")
    width = button.bounding_box()["width"]
    page.evaluate("() => {__activity.hold=true; __activity.fail=false;}")
    button.click()
    page.wait_for_function("() => __activity.pending.length === 1")
    assert button.is_disabled()
    assert button.get_attribute("aria-busy") == "true"
    assert abs(button.bounding_box()["width"] - width) < 1
    page.evaluate(
        "() => {__activity.hold=false; __activity.pending.splice(0).forEach(resolve=>resolve());}"
    )
    page.wait_for_function(
        "() => document.querySelector('#btnRefreshActivity').getAttribute('aria-busy') !== 'true'"
    )
    page.evaluate("() => __activity.fail=true")
    _refresh(page)
    assert page.locator("#pipelineHealthPct").inner_text() == "50%"
    assert not button.is_disabled()
    page.evaluate("() => __activity.fail=false")
    _refresh(page)
    page.evaluate(
        "() => {document.documentElement.dataset.theme="
        "document.documentElement.dataset.theme==='dark'?'light':'dark';"
        " window.dispatchEvent(new CustomEvent('gp:themechange'));}"
    )
    assert page.evaluate(
        "() => Chart.getChart('pipelineDoughnut').getDatasetMeta(0).data[0]"
        ".options.backgroundColor === GP.chartTheme.colors.green"
    )


def test_activity_ignores_unrelated_jobs_and_retires_pending_reads(activity_page):
    page, course, change = activity_page
    page.evaluate(
        "() => window.dispatchEvent(new CustomEvent('gp:job-complete',"
        "{detail:{status:'done',jobType:'sync:course:unrelated',meta:{courseId:'unrelated'}}}))"
    )
    page.wait_for_timeout(500)
    assert page.evaluate("() => __activity.reads") == 0
    change("scored")
    page.evaluate(
        "course => {__activity.hold=true; window.dispatchEvent(new CustomEvent('gp:job-complete',"
        "{detail:{status:'done',jobType:'sync:course:'+course,meta:{courseId:course}}}));}",
        course,
    )
    page.wait_for_function("() => __activity.pending.length === 1")
    page.locator('.gl-content-breadcrumb-nav a[href="/dashboard/"]').first.click()
    page.wait_for_url("**/dashboard/")
    page.wait_for_function("() => __activity.signals[0].aborted")
    page.evaluate(
        "() => {__activity.hold=false; __activity.pending.splice(0).forEach(resolve=>resolve());}"
    )
    page.wait_for_timeout(500)
    live_page = page.locator("#main-content").first
    assert live_page.locator("#activityHealthCard").count() == 0
    assert live_page.locator(".is-refreshing").count() == 0


def test_activity_missing_chart_library_has_a_real_retry(activity_page):
    page, _, change = activity_page
    change("scored")
    page.evaluate("() => window.Chart = undefined")
    _refresh(page)
    error = page.locator("#activityHealthCard .table-empty-state--error")
    assert error.is_visible()
    assert "Failed to load chart" in error.inner_text()
    assert page.locator("#actStatPassed").inner_text() == "1"
    with page.expect_navigation(wait_until="domcontentloaded"):
        error.get_by_role("button", name="Retry").click()
    page.wait_for_function(
        "() => typeof Chart !== 'undefined' && !!Chart.getChart('pipelineDoughnut')"
    )
    assert page.locator("#activityHealthCard .table-empty-state--error").count() == 0


def test_activity_waits_for_visibility_recovery_and_a_reader_to_leave_the_table(activity_page):
    page, course, change = activity_page
    change("scored")
    page.evaluate(
        """course => {
      window.__visibility = 'hidden';
      Object.defineProperty(document, 'visibilityState', {get:()=>__visibility});
      Object.defineProperty(document, 'hidden', {get:()=>__visibility === 'hidden'});
      document.dispatchEvent(new Event('visibilitychange'));
      window.dispatchEvent(new CustomEvent('gp:job-complete', {
        detail:{status:'done',jobType:'sync:course:'+course,meta:{courseId:course}}
      }));
    }""",
        course,
    )
    page.wait_for_timeout(500)
    assert page.evaluate("() => __activity.reads") == 0
    page.evaluate("""() => {
      __visibility='visible'; document.dispatchEvent(new Event('visibilitychange'));
    }""")
    page.wait_for_function("() => __activity.reads === 1 && !!Chart.getChart('pipelineDoughnut')")
    page.wait_for_function("() => __activity.lastHealth === 'ok'")
    page.evaluate("async () => {__activity.health='down'; await GP.health.check();}")
    page.wait_for_function("() => GP.health.isDown")
    page.evaluate(
        """course => {
      window.dispatchEvent(new CustomEvent('gp:job-complete', {
        detail:{status:'done',jobType:'sync:course:'+course,meta:{courseId:course}}
      }));
    }""",
        course,
    )
    page.wait_for_timeout(500)
    assert page.evaluate("() => __activity.reads") == 1
    page.evaluate("() => {__activity.health='ok'; GP.health.check();}")
    page.wait_for_function("() => __activity.reads === 2")
    page.wait_for_function("() => !document.querySelector('.gl-tab-content').inert")
    page.locator("#groupActivityTable tbody tr a").first.focus()
    page.evaluate(
        """course => window.dispatchEvent(new CustomEvent('gp:job-complete', {
      detail:{status:'done',jobType:'sync:course:'+course,meta:{courseId:course}}
    }))""",
        course,
    )
    page.wait_for_timeout(500)
    assert page.evaluate("() => __activity.reads") == 2
    page.evaluate("() => document.activeElement.blur()")
    page.wait_for_function("() => __activity.reads === 3")
