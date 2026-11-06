"""Assistant reads and delayed reloads belong to their originating page."""

from __future__ import annotations

import os

import pytest

pytestmark = pytest.mark.e2e

if not os.getenv("GITPULSE_E2E_BASE_URL"):
    pytest.skip("Assistant races need a running server", allow_module_level=True)


@pytest.fixture(params=[390, 1440])
def assistant_page(browser, context_for, live_server: str, request):
    with browser.new_context(
        storage_state=context_for("admin").storage_state(),
        service_workers="block",
        viewport={"width": request.param, "height": 900},
        has_touch=request.param == 390,
        is_mobile=request.param == 390,
    ) as ctx:
        ctx.route(
            "**/*",
            lambda route: (
                route.continue_()
                if route.request.method in {"GET", "HEAD"}
                else route.fulfill(status=204)
            ),
        )
        page = ctx.new_page()
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.bring_to_front()
        page.goto(live_server + "/dashboard/?period=all")
        course = page.locator("#my-courses .course-card[data-course-id]").first
        course_id = course.get_attribute("data-course-id")
        path = "/dashboard/courses/" + course_id + "/assistant"
        page.evaluate("""() => {
          const sse = GP.sse;
          GP.sse = options => {
            if (options.url.includes('/courses/')) window.__courseStream = options;
            return sse(options);
          };
          window.__reloads = 0;
          GP.reloadKeepScroll = () => { __reloads++; };
        }""")
        page.evaluate("path => GP.navigateTo(path)", path)
        page.wait_for_url(live_server + path)
        page.wait_for_function("() => !!window.__courseStream && !!window.saveAssistantTools")
        page.wait_for_timeout(650)
        # A transient toast may expire while Playwright waits for its animation.
        page.locator(".toast .toast-close").evaluate_all(
            "buttons => buttons.forEach(b => b.click())"
        )
        page.wait_for_function("() => !document.querySelector('.toast')")
        page.evaluate("""async () => {
          const fetch = window.fetch;
          window.__activityHtml = await (await fetch(
            document.getElementById('assistantActivityCard').dataset.refreshUrl)).text();
          window.__reads = []; window.__honorAbort = false; window.__slowBody = false;
          window.fetch = (url, options) => String(url).includes('/assistant/activity')
            ? new Promise((resolve, reject) => {
              const read = {url: String(url), signal: options?.signal,
                respond(status = 200, marker = 'latest') {
                  resolve(new Response(status === 200
                    ? __activityHtml.replace('<tbody',
                      '<tbody data-probe-snapshot="' + marker + '"')
                    : '{"detail":"Controlled activity failure"}',
                    {status, headers: {'Content-Type': status === 200
                      ? 'text/html' : 'application/json'}}));
                }
              };
              __reads.push(read);
              if (__slowBody) resolve({ok: true, status: 200, redirected: false,
                headers: new Headers({'Content-Type': 'text/html'}),
                text: () => new Promise((resolveBody, rejectBody) => {
                  read.respond = (_status, marker) => resolveBody(__activityHtml.replace(
                    '<tbody', '<tbody data-probe-snapshot="' + marker + '"'));
                  read.rejectBody = rejectBody;
                })
              });
              options?.signal?.addEventListener('abort', () => {
                if (__honorAbort) (read.rejectBody || reject)(
                  new DOMException('Read cancelled', 'AbortError'));
              }, {once: true});
            }) : fetch(url, options);
        }""")
        yield page, live_server + path, course_id
        assert not errors, errors


def _refresh(page, count: int = 1):
    page.locator("#btnRefreshAssistantActivity").click()
    page.wait_for_function("count => __reads.length === count", arg=count)


def _respond(page, index: int = 0, status: int = 200, marker: str = "latest"):
    page.evaluate("([i, s, m]) => __reads[i].respond(s, m)", [index, status, marker])


def _job(page, course_id: str):
    page.evaluate(
        """courseId => window.dispatchEvent(new CustomEvent('gp:job-complete', {
          detail: {jobType: 'assistant_exercise', status: 'done', meta: {courseId}}
        }))""",
        course_id,
    )


@pytest.mark.parametrize("status", [200, 500])
def test_retired_read_cannot_replace_a_new_page_or_announce_its_result(assistant_page, status: int):
    page, url, _course_id = assistant_page
    _refresh(page)
    page.evaluate("() => GP.navigateTo('/dashboard/preferences')")
    page.wait_for_url("**/dashboard/preferences")
    page.wait_for_timeout(650)
    page.evaluate("url => GP.navigateTo(url)", url)
    page.wait_for_url(url)
    page.wait_for_timeout(650)
    page.locator("#assistantActivityTable tbody").evaluate(
        "el => el.dataset.probeSnapshot = 'replacement'"
    )
    page.evaluate("""() => {
      window.__retiredToasts = new Map([...document.querySelectorAll('.toast')]
        .map(el => [el, el.textContent]));
    }""")
    _respond(page, status=status, marker="retired")
    page.wait_for_timeout(750)
    assert page.locator("#assistantActivityTable tbody").get_attribute("data-probe-snapshot") == (
        "replacement"
    )
    assert page.locator(".toast").evaluate_all(
        "els => els.every(el => __retiredToasts.get(el) === el.textContent)"
    )
    assert page.evaluate("() => __reads[0].signal.aborted")


def test_live_read_cannot_overwrite_a_newer_result(assistant_page):
    page, _url, _course_id = assistant_page
    _refresh(page)
    page.evaluate("""() => __courseStream.events.update({
      data: JSON.stringify({event: 'assistant_activity'})
    })""")
    page.wait_for_function("() => __reads.length === 2")
    assert page.evaluate("() => __reads[0].signal.aborted")
    _respond(page, index=1, marker="newer")
    page.wait_for_function("""() => document.querySelector('#assistantActivityTable tbody')
      .dataset.probeSnapshot === 'newer'""")
    _respond(page, marker="older")
    page.wait_for_timeout(700)
    assert (
        page.locator("#assistantActivityTable tbody").get_attribute("data-probe-snapshot")
        == "newer"
    )
    page.evaluate("() => GP.showToast('Background activity completed', 'success')")
    assert not page.locator("#btnRefreshAssistantActivity").evaluate(
        "b => b.classList.contains('btn-done')"
    )


def test_activity_refresh_defers_while_the_reader_is_typing(assistant_page):
    page, _url, _course_id = assistant_page
    _refresh(page)
    page.locator("#assistantSearch").fill("new query")
    _respond(page)
    page.wait_for_timeout(750)
    assert page.locator("#assistantSearch").input_value() == "new query"
    assert page.locator("#assistantSearch").evaluate("el => el === document.activeElement")
    assert page.locator(".toast").count() == 0
    assert (
        page.locator("#assistantActivityTable tbody").get_attribute("data-probe-snapshot") is None
    )
    page.locator("#btnRefreshAssistantActivity").focus()
    page.wait_for_function("() => __reads.length === 2")
    assert "q=new+query" in page.evaluate("() => __reads[1].url")
    _respond(page, index=1)
    page.wait_for_function("""() => document.querySelector('#assistantActivityTable tbody')
      .dataset.probeSnapshot === 'latest'""")
    assert page.locator("#assistantSearch").input_value() == "new query"


def test_a_job_timer_cannot_reload_over_edits_made_after_completion(assistant_page):
    page, _url, course_id = assistant_page
    _job(page, course_id)
    page.locator("#conflict_file_path").fill("later-draft.txt")
    page.wait_for_timeout(1400)
    assert page.evaluate("() => __reloads") == 0
    assert page.evaluate("() => GP.hasDirtyReason('assistant_tools')")
    assert page.locator("#conflict_file_path").input_value() == "later-draft.txt"


def test_a_job_timer_cannot_reload_a_replacement_page(assistant_page):
    page, _url, course_id = assistant_page
    _job(page, course_id)
    page.evaluate("() => GP.navigateTo('/dashboard/preferences')")
    page.wait_for_url("**/dashboard/preferences")
    page.wait_for_function(
        "() => document.getElementById('preferencesForm')?.dataset.preferencesBound"
    )
    page.locator("#diff_color_removed").fill("#112233")
    page.wait_for_timeout(1400)
    assert page.evaluate("() => __reloads") == 0
    assert page.evaluate("() => GP.hasDirtyReason('preferences_form')")


def test_another_courses_job_does_not_reload_the_page(assistant_page):
    page, _url, _course_id = assistant_page
    _job(page, "another-course")
    page.wait_for_timeout(1400)
    assert page.evaluate("() => __reloads") == 0
    assert page.evaluate("() => __reads.length") == 0


def test_a_completed_job_still_reloads_a_clean_current_page(assistant_page):
    page, _url, course_id = assistant_page
    _job(page, course_id)
    page.wait_for_function("() => __reloads === 1")


def test_a_pending_draft_keeps_its_state_when_job_activity_refreshes(assistant_page):
    page, _url, course_id = assistant_page
    page.locator("#conflict_file_path").fill("pending-draft.txt")
    _job(page, course_id)
    page.wait_for_function("() => __reads.length === 1")
    _respond(page)
    page.wait_for_timeout(1400)
    assert page.evaluate("() => __reloads") == 0
    assert page.evaluate("() => GP.hasDirtyReason('assistant_tools')")
    assert page.locator("#conflict_file_path").input_value() == "pending-draft.txt"


@pytest.mark.parametrize("pending_body", [False, True])
def test_activity_refresh_times_out_once_and_can_be_retried(assistant_page, pending_body: bool):
    page, _url, _course_id = assistant_page
    page.evaluate("body => { __honorAbort = true; __slowBody = body; }", pending_body)
    _refresh(page)
    page.wait_for_function("""() => {
      const b = document.getElementById('btnRefreshAssistantActivity');
      return !b.classList.contains('loading') && !b._loadingArmed;
    }""")
    assert page.evaluate("() => __reads.length") == 1
    assert page.locator(".toast").count() == 1
    assert page.locator("#btnRefreshAssistantActivity").is_enabled()
    page.evaluate("() => { __slowBody = false; }")
    _refresh(page, count=2)
    _respond(page, index=1, marker="retry")
    page.wait_for_function("""() => document.querySelector('#assistantActivityTable tbody')
      .dataset.probeSnapshot === 'retry'""")


def test_shared_refresh_does_not_announce_a_superseded_request(assistant_page):
    page, _url, _course_id = assistant_page
    page.evaluate("""() => {
      __honorAbort = true; window.__refreshResult = null;
      const url = document.getElementById('assistantActivityCard').dataset.refreshUrl;
      const options = {key: 'refresh-contract-probe', raw: true};
      GP.refreshRegion({button: document.getElementById('btnRefreshAssistantActivity'),
        load: () => GP.apiCall(url, 'GET', null, options),
        successMessage: 'Refresh succeeded', errorMessage: 'Refresh failed'
      }).then(result => { __refreshResult = result; });
      GP.apiCall(url, 'GET', null, options).catch(() => {});
    }""")
    page.wait_for_function("() => __reads.length === 2")
    _respond(page, index=1)
    page.wait_for_function("() => __refreshResult === false")
    assert page.locator(".toast").count() == 0
    assert page.locator("#btnRefreshAssistantActivity").is_enabled()
