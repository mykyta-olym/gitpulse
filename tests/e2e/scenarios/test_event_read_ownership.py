"""Late event reads cannot replace the current dialog or a later page visit."""

from __future__ import annotations

import os

import pytest

pytestmark = pytest.mark.e2e

if not os.getenv("GITPULSE_E2E_BASE_URL"):
    pytest.skip("event read races need a running server", allow_module_level=True)


@pytest.fixture(params=[(1440, False), (390, False), (390, True)])
def events_page(browser, context_for, live_server, request):
    width, reduced = request.param
    with browser.new_context(
        storage_state=context_for("admin").storage_state(),
        service_workers="block",
        viewport={"width": width, "height": 900},
        reduced_motion="reduce" if reduced else "no-preference",
        is_mobile=width == 390,
        has_touch=width == 390,
    ) as context:
        page = context.new_page()
        page.bring_to_front()
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(live_server + "/dashboard/admin/events")
        page.wait_for_selector("#recentEventsTableBody .dlq-view-detail")
        page.evaluate("""() => {
          const original = window.fetch;
          window.__eventReads = [];
          window.__holdRecent = false;
          window.__holdDlq = false;
          window.fetch = (url, options) => {
            const path = String(url);
            if (!path.includes('/payload') && !(__holdRecent && path.includes('/events/recent?'))
                && !(__holdDlq && path.includes('/events/dlq?'))) return original(url, options);
            return new Promise(resolve => __eventReads.push({path, signal: options.signal,
              respond: (body, fail = false) => resolve(new Response(JSON.stringify(body), {
                status: fail ? 409 : 200, headers: {'Content-Type': 'application/json'}
              }))}));
          };
          window.__openEvent = id => {
            const row = document.createElement('tr');
            row.dataset.eventId = id;
            row.innerHTML = '<td><button type="button" class="dlq-view-detail">'
              + 'Details</button></td>';
            document.querySelector('#recentEventsTableBody').append(row);
            row.querySelector('button').click();
            row.remove();
          };
          window.__answerEvent = (index, fail = false, empty = false) => {
            const id = __eventReads[index].path.includes('first') ? 'race-first' : 'race-second';
            __eventReads[index].respond(fail ? {detail: 'stale-error'} : {
              id, event_type: id, payload: empty ? {} : {chosen: id}
            }, fail);
          };
        }""")
        yield page
        assert not errors


@pytest.mark.parametrize("close_first", [False, "closing", "closed"])
@pytest.mark.parametrize("fail_first", [False, True])
def test_latest_event_wins_even_if_old_read_ignores_abort(events_page, close_first, fail_first):
    page = events_page
    page.evaluate("() => __openEvent('race-first')")
    page.wait_for_function("() => __eventReads.length === 1")
    if close_first:
        page.evaluate("() => closeModal('eventDetailModal')")
        if close_first == "closed":
            page.wait_for_function("() => !document.querySelector('#eventDetailModal.active')")
    page.evaluate("() => __openEvent('race-second')")
    page.wait_for_function("() => __eventReads.length === 2")
    assert page.evaluate("() => __eventReads[0].signal.aborted")
    page.evaluate("() => __answerEvent(1)")
    page.wait_for_function(
        "() => document.querySelector('#eventDetailFacts').textContent.includes('race-second')"
    )
    page.evaluate("fail => __answerEvent(0, fail)", fail_first)
    page.wait_for_timeout(100)
    assert "race-second" in page.locator("#eventDetailFacts").inner_text()
    assert "race-first" not in page.locator("#eventDetailFacts").inner_text()
    assert not page.locator("#eventDetailPayloadContainer .table-empty-state--error").count()
    assert page.locator("#eventDetailModal").is_visible()


@pytest.mark.parametrize("fail", [False, True])
def test_dismissed_event_does_not_receive_late_content(events_page, fail):
    page = events_page
    page.evaluate("() => __openEvent('race-first')")
    page.wait_for_function("() => __eventReads.length === 1")
    page.evaluate("() => closeModal('eventDetailModal')")
    before = page.locator("#eventDetailPayloadContainer").inner_html()
    page.evaluate("fail => __answerEvent(0, fail)", fail)
    page.wait_for_timeout(150)
    assert page.locator("#eventDetailPayloadContainer").inner_html() == before
    assert page.locator("#eventDetailFacts").inner_text() == ""


def test_event_retry_renders_shared_empty_payload(events_page):
    page = events_page
    page.evaluate("() => __openEvent('race-first')")
    page.wait_for_function("() => __eventReads.length === 1")
    page.evaluate("() => __answerEvent(0, true)")
    page.locator("#eventDetailPayloadContainer .gp-retry-btn").click()
    page.wait_for_function("() => __eventReads.length === 2")
    page.evaluate("() => __answerEvent(1, false, true)")
    page.wait_for_selector("#eventDetailPayloadContainer .table-empty-icon svg")
    assert page.locator("#eventDetailCopyBtn").is_hidden()
    assert not page.locator("#eventDetailPayloadContainer .table-empty-state--error").count()


@pytest.mark.parametrize("fail", [False, True])
def test_previous_visit_cannot_replace_event_rows_or_counters(events_page, live_server, fail):
    page = events_page
    page.evaluate("""() => {
      __holdRecent = true; __holdDlq = true;
      document.querySelector('#recentStatusFilter')
        .dispatchEvent(new Event('change', {bubbles:true}));
      window.dispatchEvent(new CustomEvent('gp:job-complete', {
        detail:{status:'done',jobType:'event_replay'}
      }));
    }""")
    page.wait_for_function("() => __eventReads.length === 3")
    page.evaluate("() => GP.navigateTo('/dashboard/preferences')")
    page.wait_for_url(live_server + "/dashboard/preferences")
    page.wait_for_function("() => !document.querySelector('#main-content.is-arriving')")
    assert page.evaluate("() => __eventReads.every(read => read.signal.aborted)")
    page.evaluate("() => { __holdRecent = false; __holdDlq = false; }")
    page.evaluate("() => GP.navigateTo('/dashboard/admin/events')")
    page.wait_for_url(live_server + "/dashboard/admin/events")
    page.wait_for_selector("#recentEventsTableBody .dlq-view-detail")
    page.wait_for_function("() => document.querySelector('#dlqCount').textContent.trim() !== ''")
    page.wait_for_function("""() => !document.querySelector('#main-content.is-arriving')
      && document.querySelector('#recentEventsTableBody').innerText.trim() !== ''""")
    before = page.locator("#recentEventsTableBody tr[data-event-id]").evaluate_all(
        "rows => rows.map(row => row.dataset.eventId)"
    )
    count = page.locator("#dlqCount").inner_text()
    page.evaluate(
        """fail => {
      __eventReads.forEach(read => read.respond(fail ? {detail:'stale-error'} : {
        events:[{id:'stale-old-page', event_type:'STALE', processed:true}],count:999
      }, fail));
    }""",
        fail,
    )
    page.wait_for_timeout(150)
    assert (
        page.locator("#recentEventsTableBody tr[data-event-id]").evaluate_all(
            "rows => rows.map(row => row.dataset.eventId)"
        )
        == before
    )
    assert page.locator("#dlqCount").inner_text() == count
    assert not page.locator("#recentEventsTableBody .table-empty-state--error").count()


@pytest.mark.parametrize("filtered", [False, True])
def test_empty_event_table_uses_shared_illustration_and_pagination(events_page, filtered):
    page = events_page
    page.evaluate(
        """filtered => {
      __holdRecent = true;
      const select = document.querySelector('#recentStatusFilter');
      if (filtered) select.value = 'failed';
      else select.dispatchEvent(new Event('change', {bubbles:true}));
    }""",
        filtered,
    )
    page.wait_for_function("() => __eventReads.length === 1")
    page.evaluate(
        """filtered => __eventReads[0].respond({events: filtered ? [
      {id:'processed-row',event_type:'push',processed:true}
    ] : []})""",
        filtered,
    )
    page.wait_for_selector("#recentEventsTableBody .table-empty-icon svg")
    assert page.locator("#recentEventsTableBody .table-empty-row").count() == 1
    assert page.locator("#recentEventsTableBody td").get_attribute("colspan") == "9"
    assert page.locator("#main-content .pagination-controls").is_visible()
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")


def test_table_refresh_dismisses_a_tooltip_before_replacing_its_row(events_page):
    page = events_page
    page.evaluate("""() => {
      const cell = document.querySelector('#recentEventsTableBody tr td');
      cell.dataset.tippyContent = 'Old row explanation';
      window.__oldTip = tippy(cell, {content:'Old row explanation',duration:0});
      __oldTip.show();
    }""")
    page.wait_for_selector('[data-tippy-root] [data-state="visible"]')
    page.evaluate("""() => {
      __holdRecent = true;
      document.querySelector('#recentStatusFilter').dispatchEvent(new Event('change'));
    }""")
    page.wait_for_function("() => __eventReads.length === 1")
    assert not page.locator('[data-tippy-root] [data-state="visible"]').count()
    page.evaluate("() => __eventReads[0].respond({events:[]})")
    page.wait_for_selector("#recentEventsTableBody .table-empty-row")
    assert not page.locator('[data-tippy-root] [data-state="visible"]').count()


def test_a_late_response_cannot_override_a_newer_filter(events_page):
    page = events_page
    page.evaluate("""() => {
      __holdRecent = true;
      document.querySelector('#recentStatusFilter').dispatchEvent(new Event('change'));
    }""")
    page.wait_for_function("() => __eventReads.length === 1")
    page.evaluate(
        "() => document.querySelector('#recentStatusFilter').dispatchEvent(new Event('change'))"
    )
    page.wait_for_function("() => __eventReads.length === 2")
    page.evaluate("""() => __eventReads[1].respond({events:[
      {id:'new-filter',event_type:'push',processed:true}
    ]})""")
    page.wait_for_selector('#recentEventsTableBody tr[data-event-id="new-filter"]')
    page.evaluate("""() => {
      __eventReads[0].respond({events:[
        {id:'old-filter',event_type:'push',processed:true}
      ]});
    }""")
    page.wait_for_timeout(100)
    assert page.locator('#recentEventsTableBody tr[data-event-id="new-filter"]').count() == 1
    assert page.locator('#recentEventsTableBody tr[data-event-id="old-filter"]').count() == 0


@pytest.mark.parametrize("outcome", ["success", "failure", "abort"])
def test_keyed_api_reads_release_external_abort_listeners(events_page, outcome):
    result = events_page.evaluate(
        """async outcome => {
      const controller = new AbortController();
      const signal = controller.signal;
      const add = signal.addEventListener.bind(signal);
      const remove = signal.removeEventListener.bind(signal);
      const listeners = new Set();
      signal.addEventListener = (name, fn, ...rest) => {
        if (name === 'abort') listeners.add(fn);
        return add(name, fn, ...rest);
      };
      signal.removeEventListener = (name, fn, ...rest) => {
        if (name === 'abort') listeners.delete(fn);
        return remove(name, fn, ...rest);
      };
      const original = window.fetch;
      window.fetch = (url, opts) => new Promise((resolve, reject) => {
        if (outcome === 'abort') {
          const cancel = () => reject(new DOMException('Aborted', 'AbortError'));
          if (opts.signal.aborted) cancel();
          else opts.signal.addEventListener('abort', cancel, {once:true});
        }
        else resolve(new Response(JSON.stringify({ok:true}), {
          status: outcome === 'failure' ? 409 : 200,
          headers:{'Content-Type':'application/json'}
        }));
      });
      let aborted = false;
      try {
        const read = GP.apiCall('/api/v1/read-lifecycle-probe', 'GET', null,
          {key:'listener-probe', signal, maxRetries:0});
        if (outcome === 'abort') controller.abort();
        await read;
      } catch (error) { aborted = error.name === 'AbortError'; }
      finally { window.fetch = original; }
      return {remaining:listeners.size, aborted};
    }""",
        outcome,
    )
    assert result["remaining"] == 0
    assert result["aborted"] is (outcome == "abort")
