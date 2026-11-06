"""Event refresh owns both reads and retires its live connection on navigation."""

from __future__ import annotations

import os

import pytest

pytestmark = pytest.mark.e2e
if not os.getenv("GITPULSE_E2E_BASE_URL"):
    pytest.skip("needs a running server", allow_module_level=True)


@pytest.fixture(params=[(390, "light"), (390, "dark"), (1440, "light"), (1440, "dark")])
def pipeline_page(browser, context_for, live_server, request):
    width, theme = request.param
    with browser.new_context(
        storage_state=context_for("admin").storage_state(),
        viewport={"width": width, "height": 1000},
        is_mobile=width == 390,
        has_touch=width == 390,
        service_workers="block",
    ) as context:
        context.add_init_script("""(() => {
          const Native = EventSource;
          window.__pipeline = {streams:[], reads:[], hold:false, blocked:false};
          window.GP = {};
          Object.defineProperty(GP, 'sse', {configurable:true, set(real) {
            delete GP.sse;
            GP.sse = function(options) {
              if (!String(new Error().stack).includes('admin-events.')) return real(options);
              return real({...options, beforeConnect() {__pipeline.ownConnection = true;}});
            };
          }});
          window.EventSource = class extends EventTarget {
            constructor(url, options) {
              super();
              if (!__pipeline.ownConnection) return new Native(url, options);
              __pipeline.ownConnection = false;
              if (__pipeline.blocked) throw new Error('Blocked stream');
              this.closed = false;
              __pipeline.streams.push(this);
            }
            close() {this.closed = true;}
          };
          const fetch = window.fetch;
          window.fetch = (url, options) => {
            if (__pipeline.fakeReplay && String(url).endsWith('/events/replay'))
              return Promise.resolve(new Response('{"replayed":1}', {
                status:200, headers:{'Content-Type':'application/json'}}));
            const kind = String(url).includes('/events/recent?') ? 'recent'
              : String(url).includes('/events/dlq?') ? 'dlq' : null;
            if (!kind || !__pipeline.hold) return fetch(url, options);
            const recent = JSON.parse(document.querySelector('#gp-recent-events').textContent);
            return new Promise(resolve => __pipeline.reads.push({kind, signal:options.signal,
              reply:(fail=false, body=null) => resolve(new Response(JSON.stringify(fail
                ? {detail:'Read failed'}
                : kind === 'dlq' ? {count:7, events:[]} : body || recent),
                {status:fail ? 503 : 200, headers:{'Content-Type':'application/json'}}))}));
          };
          window.__greet = () => __pipeline.streams.at(-1)
            .dispatchEvent(new MessageEvent('connected'));
          window.__update = () => __pipeline.streams.at(-1)
            .dispatchEvent(new MessageEvent('update'));
        })()""")
        page = context.new_page()
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(f"{live_server}/dashboard/admin/events?theme={theme}&lang=en")
        page.wait_for_selector("#recentEventsTableBody .dlq-view-detail")
        page.wait_for_function("() => __pipeline.streams.length === 1")
        yield page
        assert not errors


def test_refresh_waits_for_both_reads_and_preserves_selection(pipeline_page):
    page = pipeline_page
    checkbox = page.locator(".recent-select").first
    checkbox.check()
    selected = checkbox.input_value()
    page.evaluate("() => __pipeline.hold = true")
    before = page.locator("#btnRefreshDLQ").bounding_box()
    page.locator("#btnRefreshDLQ").click()
    page.wait_for_function("() => __pipeline.reads.length === 2")
    assert page.locator("#eventPipelineRegion").get_attribute("aria-busy") == "true"
    assert page.locator("#eventPipelineRegion").evaluate("el => el.inert")
    page.evaluate("() => __pipeline.reads.find(read => read.kind === 'recent').reply()")
    assert page.locator("#btnRefreshDLQ").is_disabled()
    pending = page.locator("#btnRefreshDLQ").bounding_box()
    assert all(abs(before[key] - pending[key]) < 1 for key in ("x", "y", "width", "height"))
    page.evaluate("() => __pipeline.reads.find(read => read.kind === 'dlq').reply()")
    page.wait_for_function("() => !document.querySelector('#btnRefreshDLQ').disabled")
    assert page.locator("#dlqCount").inner_text() == "7"
    assert page.locator(f'.recent-select[value="{selected}"]').is_checked()
    assert not page.locator("#eventPipelineRegion").evaluate("el => el.inert")
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")


@pytest.mark.parametrize("failed_kind", ["recent", "dlq"])
def test_partial_failure_is_not_success_and_refresh_retries(pipeline_page, failed_kind):
    page = pipeline_page
    page.evaluate("() => __pipeline.hold = true")
    page.locator("#btnRefreshDLQ").click()
    page.wait_for_function("() => __pipeline.reads.length === 2")
    page.evaluate(
        "kind => __pipeline.reads.find(read => read.kind === kind).reply(true)", failed_kind
    )
    page.wait_for_timeout(100)
    assert page.locator("#btnRefreshDLQ").is_disabled()
    page.evaluate("kind => __pipeline.reads.find(read => read.kind !== kind).reply()", failed_kind)
    page.wait_for_function("() => !document.querySelector('#btnRefreshDLQ').disabled")
    assert not page.locator("#eventPipelineRegion").evaluate("el => el.inert")
    assert page.get_by_text("Read failed", exact=True).is_visible()
    assert not page.get_by_text("Events refreshed", exact=True).count()
    page.locator("#btnRefreshDLQ").click()
    page.wait_for_function("() => __pipeline.reads.length === 4")
    page.evaluate("() => __pipeline.reads.slice(2).forEach(read => read.reply())")
    page.wait_for_function("() => !document.querySelector('#btnRefreshDLQ').disabled")
    assert page.locator("#dlqCount").inner_text() == "7"
    assert not page.locator("#recentEventsTableBody .table-empty-state--error").count()


def test_greetings_cannot_reset_the_reconnect_limit(pipeline_page):
    page = pipeline_page
    page.clock.install()
    page.evaluate("() => {GP.SSE_RECONNECT_MS = 10; __greet();}")
    for count in range(5):
        page.evaluate("() => {__greet(); __pipeline.streams.at(-1).onerror();}")
        page.clock.run_for(200)
        assert page.evaluate("__pipeline.streams.length") == min(count + 2, 5)
    assert page.evaluate("__pipeline.streams.at(-1).closed")
    page.clock.run_for(1000)
    assert page.evaluate("__pipeline.streams.length") == 5
    page.locator("#btnRefreshDLQ").click()
    page.wait_for_function("() => __pipeline.streams.length === 6")


def test_hidden_unhealthy_page_waits_for_both_recovery_conditions(pipeline_page):
    page = pipeline_page
    page.evaluate("""() => {
      Object.defineProperty(document, 'visibilityState', {configurable:true, value:'hidden'});
      document.dispatchEvent(new Event('visibilitychange'));
      document.dispatchEvent(new CustomEvent('gp-health-change', {detail:{current:'down'}}));
      Object.defineProperty(document, 'visibilityState', {configurable:true, value:'visible'});
      document.dispatchEvent(new Event('visibilitychange'));
    }""")
    assert page.evaluate("__pipeline.streams.at(-1).closed")
    assert page.evaluate("__pipeline.streams.length") == 1
    page.evaluate("""() => {
      document.dispatchEvent(new CustomEvent('gp-health-change', {detail:{current:'up'}}));
      __greet(); __pipeline.hold = true;
      window.dispatchEvent(new Event('beforeunload'));
    }""")
    assert page.evaluate("__pipeline.streams.length") == 2
    assert not page.evaluate("__pipeline.streams.at(-1).closed")
    page.evaluate("() => __update()")
    page.wait_for_function("() => __pipeline.reads.length === 2")
    page.evaluate("() => __pipeline.reads.forEach(read => read.reply())")
    page.wait_for_function("() => document.querySelector('#dlqCount').textContent === '7'")


def test_navigation_retires_stream_and_late_updates(pipeline_page, live_server):
    page = pipeline_page
    page.evaluate("() => {__pipeline.hold = true; __update();}")
    page.wait_for_function("() => __pipeline.reads.length === 2")
    page.evaluate("() => GP.navigateTo('/dashboard/preferences')")
    page.wait_for_url(live_server + "/dashboard/preferences")
    assert page.evaluate("__pipeline.streams.at(-1).closed")
    assert page.evaluate("__pipeline.reads.every(read => read.signal.aborted)")
    page.evaluate("() => {__pipeline.reads.forEach(read => read.reply()); __update();}")
    page.wait_for_timeout(100)
    assert page.evaluate("__pipeline.reads.length") == 2
    page.locator("#eventPipelineRegion").wait_for(state="detached")


def test_blocked_stream_can_retry_after_a_successful_refresh(pipeline_page):
    page = pipeline_page
    page.evaluate("""() => {
      document.dispatchEvent(new CustomEvent('gp-health-change', {detail:{current:'down'}}));
      __pipeline.blocked = true;
      document.dispatchEvent(new CustomEvent('gp-health-change', {detail:{current:'up'}}));
      __pipeline.blocked = false;
    }""")
    assert page.evaluate("__pipeline.streams.length") == 1
    page.locator("#btnRefreshDLQ").click()
    page.wait_for_function("() => __pipeline.streams.length === 2")


def test_live_refresh_keeps_the_page_and_empty_results_clear_selection(pipeline_page):
    page = pipeline_page
    page.evaluate("""() => {
      __pipeline.hold = true;
      const seed = JSON.parse(document.querySelector('#gp-recent-events').textContent).events[0];
      window.__manyEvents = {events:Array.from({length:150}, (_,index) =>
        ({...seed,id:'owned-row-'+index}))};
      __update();
    }""")
    page.wait_for_function("() => __pipeline.reads.length === 2")
    page.evaluate("() => __pipeline.reads.forEach(read => read.reply(false, __manyEvents))")
    page.wait_for_selector('.recent-select[value="owned-row-0"]')
    page.evaluate(
        "() => document.querySelector('#recentEventsTableBody')._clientPaginator.goToPage(2)"
    )
    page.locator(".recent-select:visible").first.check()
    selected = page.locator(".recent-select:checked").input_value()
    page.evaluate("() => __update()")
    page.wait_for_function("() => __pipeline.reads.length === 4")
    page.evaluate(
        "() => __pipeline.reads.slice(2).forEach(read => read.reply(false, __manyEvents))"
    )
    page.wait_for_function("() => !document.querySelector('#recentEventsTableBody').inert")
    assert (
        page.evaluate(
            "document.querySelector('#recentEventsTableBody')._clientPaginator.currentPage"
        )
        == 2
    )
    assert page.locator(f'.recent-select[value="{selected}"]').is_checked()
    page.evaluate("() => __update()")
    page.wait_for_function("() => __pipeline.reads.length === 6")
    page.evaluate("() => __pipeline.reads.slice(4).forEach(read => read.reply(false, {events:[]}))")
    page.wait_for_selector("#recentEventsTableBody .table-empty-row")
    assert page.locator("#recentSelectedCount").inner_text() == "0"
    assert not page.locator("#recentSelectAll").is_checked()
    assert page.locator("#btnReplaySelected").is_disabled()


def test_bulk_action_stays_locked_until_both_refresh_reads_finish(pipeline_page):
    page = pipeline_page
    page.locator(".recent-select").first.check()
    page.evaluate("() => {__pipeline.fakeReplay = true; __pipeline.hold = true;}")
    page.locator("#btnReplaySelected").click()
    page.locator('#gpConfirmDialog [data-gp-confirm="ok"]').click()
    page.wait_for_function("() => __pipeline.reads.length === 2")
    page.evaluate("() => __pipeline.reads.find(read => read.kind === 'recent').reply()")
    page.wait_for_function("() => !document.querySelector('#recentEventsTableBody').inert")
    assert page.locator("#btnReplaySelected").is_disabled()
    assert page.locator("#btnReplaySelected").get_attribute("aria-busy") == "true"
    page.evaluate("() => __pipeline.reads.find(read => read.kind === 'dlq').reply()")
    page.wait_for_function("() => !document.querySelector('#btnReplaySelected').disabled")
    assert page.locator(".recent-select:checked").count() == 1
