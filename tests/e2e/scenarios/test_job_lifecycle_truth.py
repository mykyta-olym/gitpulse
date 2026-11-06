"""Run the shipped core; only the network transport supplies controlled job states."""

import os

import pytest

pytestmark = pytest.mark.e2e

if not os.getenv("GITPULSE_E2E_BASE_URL"):
    pytest.skip("job lifecycle checks need a running server", allow_module_level=True)

JOB = "11111111-1111-4111-8111-111111111111"
COURSE = "22222222-2222-4222-8222-222222222222"
KEY = "run_checks:team:probe"

# EventSource is the transport, not a replacement for GP.sse/streamJobProgress.
TRANSPORT = """() => {
  window.__sources = [];
  window.EventSource = class extends EventTarget {
    constructor(url) { super(); this.url = String(url); this.closed = false;
      __sources.push(this); }
    close() { this.closed = true; }
    send(type, data) {
      const body = typeof data === 'string' ? data : JSON.stringify(data);
      const ev = new MessageEvent(type, {data: body});
      this.dispatchEvent(ev);
      if (type === 'message') this.onmessage?.(ev);
    }
  };
} """


@pytest.fixture(params=[(390, "light"), (390, "dark"), (1440, "light"), (1440, "dark")])
def job_page(context_for, live_server, request):
    width, theme = request.param
    context = context_for("admin", width=width)
    context.add_init_script("(" + TRANSPORT + ")()")
    context.route("**/api/v1/sync/active", lambda route: route.fulfill(json={"courses": []}))
    page = context.new_page()
    errors = []
    failed_responses = []
    page.on(
        "response",
        lambda response: (
            failed_responses.append((response.status, response.url))
            if response.status >= 400
            else None
        ),
    )
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.on(
        "console", lambda message: errors.append(message.text) if message.type == "error" else None
    )
    page.goto(live_server + "/dashboard/preferences?lang=en")
    page.wait_for_function("() => window._globalJobsReady && !!GP.refreshProcessActionGuards")
    page.evaluate("theme => document.documentElement.dataset.theme = theme", theme)
    page.evaluate("""() => {
      window.__done = [];
      addEventListener('gp:job-complete', event => __done.push(event.detail));
    }""")
    yield page
    assert not errors, (errors, failed_responses)


def start_job(page):
    page.evaluate(
        """({key, id}) => showGlobalJob('Checking', key,
          {jobKind: 'run_checks', jobId: id, teamId: 'probe'})""",
        {"key": KEY, "id": JOB},
    )


def state(page, key=KEY):
    return page.evaluate("key => window._globalJobs[key]?.status", key)


@pytest.mark.parametrize("status", ["completed", "failed", "cancelled"])
def test_confirmed_completion_is_immediate_and_idempotent(job_page, status):
    page = job_page
    start_job(page)
    page.evaluate(
        """status => __sources.findLast(s => s.url.endsWith('/stream') && s.url.includes('/jobs/'))
          .send('complete', {status, error_message: 'Worker failed'})""",
        status,
    )
    assert state(page) == ("done" if status == "completed" else "error")
    assert not page.evaluate("key => isGlobalJobRunning(key)", KEY)
    page.evaluate("key => completeGlobalJob(key, 'Duplicate', 'done')", KEY)
    assert page.evaluate("() => __done.length") == 1
    assert page.evaluate("() => __done[0].meta.jobId") == JOB


def test_finishing_waits_for_server_and_preserves_failure(job_page):
    page = job_page
    page.clock.install()
    page.evaluate(
        "id => showGlobalJob('Syncing', id, {jobKind: 'course_sync', courseId: id})", COURSE
    )
    page.evaluate(
        """id => __sources.findLast(s => s.url.includes(id)).send('message',
          {has_active_sync: true, sync_running_count: 0, sync_queued_count: 0})""",
        COURSE,
    )
    assert state(page, COURSE) == "finishing"
    assert page.evaluate("id => _globalJobs[id].progress", COURSE) is None
    page.clock.fast_forward(12000)
    assert state(page, COURSE) == "finishing"
    assert page.evaluate("id => isGlobalJobRunning(id)", COURSE)
    assert not page.evaluate("() => GP.guardProcessAction(['sync'], {toast: false})")
    assert page.evaluate("() => __done.length") == 0
    page.evaluate(
        """id => __sources.findLast(s => s.url.includes(id)).send('complete',
          {has_active_sync: false, sync_failed_count: 1})""",
        COURSE,
    )
    assert state(page, COURSE) == "error"
    assert page.evaluate("() => GP.guardProcessAction(['sync'], {toast: false})")
    assert page.evaluate("() => __done.length") == 1


@pytest.mark.parametrize("payload", ["invalid-json", {}, {"status": "idle"}])
def test_unconfirmed_job_complete_uses_real_polling(job_page, payload):
    page = job_page
    reply = {"status": "running", "progress": 25}
    page.route("**/api/v1/jobs/" + JOB, lambda route: route.fulfill(json=reply))
    start_job(page)
    page.evaluate(
        """payload => __sources.findLast(s => s.url.includes('/jobs/'))
          .send('complete', payload)""",
        payload,
    )
    assert state(page) == "running"
    assert page.evaluate("() => __done.length") == 0
    reply["status"] = "completed"
    page.wait_for_function("key => _globalJobs[key]?.status === 'done'", arg=KEY)
    assert page.evaluate("() => __done.length") == 1


def test_storage_transitions_do_not_invent_completion_or_resurrect_old_runs(job_page):
    page = job_page
    start_job(page)
    page.evaluate("""() => {
      window.__stored = JSON.parse(localStorage.getItem('gitpulse_global_job'));
      dispatchEvent(new StorageEvent('storage', {key: 'gitpulse_global_job', newValue: null}));
    }""")
    assert state(page) == "running"
    assert page.evaluate("() => __done.length") == 0
    page.evaluate(
        """key => {
          __stored[key].status = 'finishing';
          dispatchEvent(new StorageEvent('storage', {key: 'gitpulse_global_job',
            newValue: JSON.stringify(__stored)}));
        }""",
        KEY,
    )
    assert state(page) == "finishing"
    page.evaluate(
        """key => {
          __stored[key].status = 'done';
          dispatchEvent(new StorageEvent('storage', {key: 'gitpulse_global_job',
            newValue: JSON.stringify(__stored)}));
        }""",
        KEY,
    )
    assert state(page) == "done"
    assert page.evaluate("() => __done.length") == 1
    page.evaluate(
        """key => {
          __stored[key].status = 'running';
          dispatchEvent(new StorageEvent('storage', {key: 'gitpulse_global_job',
            newValue: JSON.stringify(__stored)}));
        }""",
        KEY,
    )
    assert state(page) == "done"


def test_invalid_course_response_cannot_count_as_inactive(job_page):
    page = job_page
    page.clock.install()
    page.route("**/api/v1/courses/" + COURSE + "/sync-status", lambda route: route.fulfill(json={}))
    page.evaluate(
        "id => showGlobalJob('Syncing', id, {jobKind: 'course_sync', courseId: id})", COURSE
    )
    page.evaluate("id => __sources.findLast(s => s.url.includes(id)).send('complete', {})", COURSE)
    for _ in range(3):
        page.clock.run_for(3100)
    assert state(page, COURSE) == "running"
    assert page.evaluate("() => __done.length") == 0


def test_reload_revalidates_finishing_instead_of_replaying_success(job_page):
    page = job_page
    start_job(page)
    page.evaluate("""() => {
      const stored = JSON.parse(localStorage.getItem('gitpulse_global_job'));
      Object.values(stored).forEach(job => {job.status = 'finishing'; job.progress = 100;});
      localStorage.setItem('gitpulse_global_job', JSON.stringify(stored));
    }""")
    page.reload()
    page.wait_for_function("key => !!_globalJobs[key]?.poller", arg=KEY)
    assert state(page) == "running"
    assert page.evaluate("key => _globalJobs[key].progress", KEY) is None
    page.clock.install()
    page.clock.fast_forward(12000)
    assert state(page) == "running"
    page.evaluate("""() => __sources.findLast(s => s.url.includes('/jobs/'))
      .send('complete', {status: 'failed'})""")
    assert state(page) == "error"


def test_late_poll_cannot_complete_a_replacement_job(job_page):
    page = job_page
    pending = []
    page.route("**/qa/job-status", lambda route: pending.append(route))
    start_job(page)
    page.evaluate(
        """key => startGenericStatusPolling(key, '/qa/job-status', {interval: 100})""", KEY
    )
    page.wait_for_function("() => true")
    page.wait_for_timeout(1100)
    assert len(pending) == 1
    page.wait_for_timeout(400)
    assert len(pending) == 1, "one read must stay in flight across timer ticks"
    page.evaluate(
        """key => {
          hideGlobalJob(key);
          showGlobalJob('New run', key, {jobKind: 'run_checks',
            jobId: '33333333-3333-4333-8333-333333333333'});
        }""",
        KEY,
    )
    pending[0].fulfill(json={"status": "completed"})
    page.wait_for_timeout(100)
    assert state(page) == "running"
    assert page.evaluate("() => __done.length") == 0


def test_course_page_waits_for_the_debounced_terminal_event(job_page, live_server):
    page = job_page
    course_id = "631165d5-c694-4280-82a8-eb73aa646ac7"
    response = page.request.get(live_server + f"/api/v1/courses/{course_id}/sync-status")
    assert response.status == 200
    data = response.json()
    page.goto(live_server + f"/dashboard/courses/{course_id}")
    page.wait_for_function(
        "id => __sources.some(s => s.url.includes(id) && s.url.endsWith('/sync-stream'))",
        arg=course_id,
    )
    data.update(has_active_sync=True, sync_running_count=1, sync_queued_count=0)
    page.evaluate(
        """({id, data}) => __sources.findLast(s => !s.closed && s.url.includes(id)
          && s.url.endsWith('/sync-stream')).send('message', data)""",
        {"id": course_id, "data": data},
    )
    page.wait_for_function("id => !!_globalJobs[id]", arg=course_id)
    data.update(has_active_sync=False, sync_running_count=0)
    page.evaluate(
        """({id, data}) => {
          window.__sameDocument = true;
          __sources.findLast(s => !s.closed && s.url.includes(id) && s.url.endsWith('/sync-stream'))
            .send('message', data);
        }""",
        {"id": course_id, "data": data},
    )
    page.wait_for_timeout(300)
    assert page.evaluate("() => window.__sameDocument === true")
    assert state(page, course_id) == "running"
    with page.expect_navigation(timeout=10000):
        page.evaluate(
            """({id, data}) => __sources.findLast(s => !s.closed && s.url.includes(id)
              && s.url.endsWith('/sync-stream')).send('complete', data)""",
            {"id": course_id, "data": data},
        )
    assert page.evaluate("() => window.__sameDocument === undefined")


def test_recovered_status_replaces_the_connection_warning(job_page):
    page = job_page
    start_job(page)
    page.evaluate("""() => __sources.findLast(s => s.url.includes('/jobs/')).send('message', {})""")
    assert "Status unavailable" in page.evaluate("key => _globalJobs[key].message", KEY)
    assert state(page) == "running"
    page.evaluate("""() => __sources.findLast(s => s.url.includes('/jobs/'))
      .send('message', {status: 'running', progress: 35})""")
    assert "Status unavailable" not in page.evaluate("key => _globalJobs[key].message", KEY)
    assert page.evaluate("key => _globalJobs[key].progress", KEY) == 35
    assert page.evaluate("() => __done.length") == 0


@pytest.mark.parametrize("blocked", [False, True])
def test_enrichment_uses_shared_stream_and_recovers_when_blocked(job_page, blocked):
    page = job_page
    reply = {"status": "running", "progress": 30}
    page.route(
        "**/dashboard/admin/users/enrich-gitlab/status", lambda route: route.fulfill(json=reply)
    )
    page.evaluate(
        """blocked => {
          if (blocked) window.EventSource = class { constructor() { throw new Error('Blocked'); } };
          showGlobalJob('Enriching', 'enrichment');
          if (!blocked) __sources.findLast(s => s.url.includes('/enrich-gitlab/'))
            .send('complete', 'invalid-json');
        }""",
        blocked,
    )
    assert state(page, "enrichment") == "running"
    assert page.evaluate("() => __done.length") == 0
    reply["status"] = "completed"
    page.wait_for_function("() => _globalJobs.enrichment?.status === 'done'")
    assert page.evaluate("() => __done.length") == 1
