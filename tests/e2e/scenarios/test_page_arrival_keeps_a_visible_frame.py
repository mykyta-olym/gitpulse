"""Delayed page scripts must not expose a blank frame between two pages."""

from __future__ import annotations

import os
import re
import time

import pytest

pytestmark = pytest.mark.e2e

if not os.getenv("GITPULSE_E2E_BASE_URL"):
    pytest.skip("needs GITPULSE_E2E_BASE_URL", allow_module_level=True)


@pytest.fixture
def arrival_context(browser, context_for):
    made = []

    def create(width=1440, reduced=False):
        ctx = browser.new_context(
            storage_state=context_for("admin").storage_state(),
            service_workers="block",
            viewport={"width": width, "height": 900},
            reduced_motion="reduce" if reduced else "no-preference",
        )
        made.append(ctx)
        return ctx

    try:
        yield create
    finally:
        for ctx in made:
            ctx.close()


@pytest.mark.parametrize("mode", ["normal", "reduced", "no-gsap"])
def test_delayed_spa_scripts_keep_the_previous_frame(arrival_context, live_server, mode):
    ctx = arrival_context(width=390 if mode == "reduced" else 1440, reduced=mode == "reduced")
    if mode == "no-gsap":
        ctx.route(
            "**/gsap*.js*",
            lambda route: route.fulfill(body="", content_type="application/javascript"),
        )
    page = ctx.new_page()
    page.bring_to_front()
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.goto(live_server + "/dashboard/admin/system", wait_until="domcontentloaded")
    page.wait_for_function("document.documentElement.hasAttribute('data-gp-ready')")
    assert page.evaluate("() => !!window.gsap") is (mode != "no-gsap")

    def delay_script(route):
        time.sleep(0.45)
        route.continue_()

    page.route("**/js/pages/admin-users.*.js", delay_script)
    page.evaluate("""() => {
      window.__arrivalFrames = [];
      window.__arrivalDone = false;
      const table = document.getElementById('jobsTable');
      const scroller = table.closest('.table-responsive');
      scroller.scrollLeft = 125;
      const scroll = scroller.scrollLeft;
      const widths = [...table.querySelectorAll('thead th')].map(node =>
        node.getBoundingClientRect().width);
      function sample() {
        const main = document.querySelector('#main-content');
        const cover = document.querySelector('.gp-page-cover');
        const copy = cover?.shadowRoot.querySelector('#jobsTable');
        window.__arrivalFrames.push({
          hidden: getComputedStyle(main).visibility === 'hidden',
          cover: !!cover,
          opacity: cover ? Number(getComputedStyle(cover).opacity) : 0,
          activeCopy: !!cover?.shadowRoot.querySelector('script')
            || !!cover && [...cover.shadowRoot.querySelectorAll('[x-data]')]
              .some(node => !!node._x_dataStack),
          duplicateId: !!cover && [...cover.shadowRoot.querySelectorAll('[id]')].some(node =>
            document.getElementById(node.id) === node),
          anonymousField: !!cover && Array.from(cover.shadowRoot.querySelectorAll(
            'input, select, textarea')).some(node => !node.id && !node.name),
          shifted: !!cover && (!copy ||
            Math.abs(copy.closest('.table-responsive').scrollLeft - scroll) > 1 ||
            [...copy.querySelectorAll('thead th')].some((node, index) =>
              Math.abs(node.getBoundingClientRect().width - widths[index]) > 1))
        });
        if (!window.__arrivalDone) requestAnimationFrame(sample);
      }
      requestAnimationFrame(sample);
      GP.navigateTo('/dashboard/admin/users');
    }""")
    page.wait_for_url("**/dashboard/admin/users")
    page.wait_for_function("""() => !document.querySelector('#main-content.is-arriving')
      && !document.querySelector('.gp-page-cover')""")
    frames = page.evaluate("() => { window.__arrivalDone = true; return window.__arrivalFrames; }")
    assert any(frame["hidden"] for frame in frames), "the delayed arrival was not exercised"
    assert not any(frame["hidden"] and not frame["cover"] for frame in frames)
    assert not any(frame["activeCopy"] for frame in frames), "the cover retained live behaviour"
    assert not any(frame["duplicateId"] for frame in frames), "the cover duplicated live ids"
    assert not any(frame["anonymousField"] for frame in frames), (
        "the cover created anonymous fields"
    )
    assert not any(frame["shifted"] for frame in frames), (
        "the outgoing table changed column widths or horizontal scroll"
    )
    if mode == "normal":
        assert any(0 < frame["opacity"] < 1 for frame in frames), "the cover disappeared instantly"
    assert not errors


@pytest.mark.parametrize("reduced", [False, True])
def test_full_redirect_waits_for_the_incoming_first_frame(arrival_context, live_server, reduced):
    ctx = arrival_context(reduced=reduced)
    ctx.add_init_script("""window.addEventListener('pagereveal', event => {
      window.__arrival = {transition: !!event.viewTransition};
      if (!event.viewTransition) return;
      event.viewTransition.ready.then(() => {
        const old = getComputedStyle(document.documentElement, '::view-transition-old(root)');
        Object.assign(window.__arrival, {
          gated: !document.documentElement.hasAttribute('data-gp-ready'),
          oldOpacity: Number(old.opacity), oldState: old.animationPlayState
        });
      }).catch(error => window.__arrival.error = String(error));
      event.viewTransition.finished.then(() => window.__arrival.finished = true)
        .catch(error => window.__arrival.error = String(error));
    });""")
    page = ctx.new_page()
    page.bring_to_front()
    page.goto(live_server + "/dashboard/", wait_until="domcontentloaded")
    page.wait_for_function("document.documentElement.hasAttribute('data-gp-ready')")

    def delay_core(route):
        time.sleep(0.4)
        route.continue_()

    page.route("**/core.bundle.*.js", delay_core)
    page.evaluate("() => location.assign('/dashboard/preferences')")
    page.wait_for_url("**/dashboard/preferences")
    page.wait_for_function("document.documentElement.hasAttribute('data-gp-ready')")
    page.wait_for_timeout(350)
    state = page.evaluate("() => window.__arrival")
    assert state["transition"] is not reduced
    if not reduced:
        assert state.get("gated"), "the delayed document gate was not exercised"
        assert state["oldOpacity"] == 1
        assert state["oldState"] == "paused"
        assert state.get("finished"), state
    assert page.evaluate("getComputedStyle(document.body).visibility") == "visible"


@pytest.mark.parametrize("width", [390, 1440])
@pytest.mark.parametrize("placement", ["content", "modal-slot"])
@pytest.mark.parametrize("failed", [False, True])
def test_page_modals_wait_for_their_factories(
    arrival_context, live_server, width, placement, failed
):
    page = arrival_context(width=width).new_page()
    page.bring_to_front()
    errors, scripts = [], []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.goto(live_server + "/dashboard/admin/courses?lang=en")
    page.wait_for_function("document.documentElement.hasAttribute('data-gp-ready')")
    courses = page.request.get(live_server + "/api/v1/courses").json()
    course = next((c for c in courses if c["archived_at"] is None), None)
    if course is None:
        pytest.skip("no active course in the development database")
    path = f"/dashboard/courses/{course['id']}/teachers?lang=en"
    html = page.request.get(live_server + path).text()
    assert 'id="addTeacherModal"' in html
    if placement == "modal-slot":
        html = page.evaluate(
            """html => {
              const doc = new DOMParser().parseFromString(html, 'text/html');
              doc.getElementById('gp-modals').appendChild(doc.getElementById('addTeacherModal'));
              return '<!DOCTYPE html>' + doc.documentElement.outerHTML;
            }""",
            html,
        )
    page.route(live_server + path, lambda r: r.fulfill(body=html, content_type="text/html"))
    page.route("**/js/pages/course-teachers.*.js", lambda r: scripts.append(r))
    page.evaluate("path => GP.navigateTo(path)", path)
    page.wait_for_function("() => document.querySelector('#main-content.is-arriving #teacherForm')")
    page.wait_for_timeout(100)
    assert scripts, "the page factory read was not held"
    assert not errors, errors
    assert page.locator('#addTeacherModal [x-data="teacherInvite()"]').evaluate(
        "el => !el._x_dataStack"
    ), "the modal initialised before its factory"
    assert page.locator("#gp-top-progress").get_attribute("aria-hidden") == "false"
    if failed:
        scripts.pop().fulfill(status=503, body="Expected script failure")
    else:
        scripts.pop().continue_()
    page.wait_for_function("() => !document.querySelector('#main-content.is-arriving')")
    if failed:
        assert page.locator("#main-content").get_by_text("Failed to load", exact=True).count() == 1
        assert page.locator("#addTeacherModal").count() == 0
    else:
        page.evaluate("() => GP.openModal('addTeacherModal')")
        page.locator("#teacher-search").fill("no-such-user-probe")
        page.locator("#addTeacherModal .gl-dropdown-empty").first.wait_for(state="visible")
        assert page.locator("#btnAddTeacherSubmit").is_disabled()
        assert page.locator('#addTeacherModal [x-data="teacherInvite()"]').evaluate(
            "el => Alpine.$data(el).search === 'no-such-user-probe'"
        )
        page.locator('#addTeacherModal [data-modal-close="addTeacherModal"]').last.click()
        page.locator("#addTeacherModal").wait_for(state="hidden")
    assert not errors, errors


@pytest.mark.parametrize(
    ("width", "layout", "gutter"), [(2560, "fixed", 8), (390, "fluid", 8), (390, "fluid", 34)]
)
def test_save_bar_leaves_space_for_a_following_section(
    arrival_context, live_server, width, layout, gutter
):
    page = arrival_context(width=width).new_page()
    page.bring_to_front()
    page.goto(live_server + "/dashboard/admin/courses", wait_until="load")
    page.wait_for_function("document.documentElement.hasAttribute('data-gp-ready')")
    course = page.locator('a[href*="/dashboard/courses/"]').first
    if not course.count():
        pytest.skip("no course in the development database")
    path = re.search(r"/dashboard/courses/[0-9a-f-]{36}", course.get_attribute("href") or "")
    assert path
    page.goto(live_server + path[0] + "/assistant", wait_until="load")
    page.wait_for_function("document.documentElement.hasAttribute('data-gp-ready')")
    page.evaluate(
        """({layout, gutter}) => {
      document.documentElement.setAttribute('data-layout-width', layout);
      const scroller = document.querySelector('.gl-page-content');
      scroller.style.setProperty('--page-bottom-gutter', gutter + 'px');
      scroller.scrollTop = scroller.scrollHeight;
    }""",
        {"layout": layout, "gutter": gutter},
    )
    page.wait_for_timeout(150)
    gap = page.evaluate("""() => {
      const footer = document.querySelector('.settings-sticky-footer').getBoundingClientRect();
      const next = document.querySelector('#assistantActivityCard').getBoundingClientRect();
      return next.top - footer.bottom;
    }""")
    assert 12 <= gap <= 24, f"save bar to next section: {gap}px"
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")


@pytest.mark.parametrize("width", [390, 1440])
@pytest.mark.parametrize("failed", [False, True])
def test_date_pickers_mount_only_after_a_successful_page_arrival(
    arrival_context, live_server, width, failed
):
    page = arrival_context(width=width).new_page()
    page.bring_to_front()
    scripts, errors = [], []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.goto(live_server + "/dashboard/admin/users?lang=en")
    page.wait_for_function("() => document.documentElement.hasAttribute('data-gp-ready')")
    courses = page.request.get(live_server + "/api/v1/courses").json()
    course = next((c for c in courses if c["archived_at"] is None), None)
    if course is None:
        pytest.skip("no active course in the development database")
    page.route("**/js/pages/course-settings.*.js", lambda route: scripts.append(route))
    page.evaluate("path => GP.navigateTo(path)", f"/dashboard/courses/{course['id']}/settings")
    page.wait_for_function("() => document.querySelector('#main-content.is-arriving')")
    page.wait_for_timeout(100)
    assert scripts
    assert page.locator(".flatpickr-calendar").count() == 0
    if failed:
        scripts.pop().fulfill(status=503, body="Expected script failure")
    else:
        scripts.pop().continue_()
    page.wait_for_function("() => !document.querySelector('#main-content.is-arriving')")
    if failed:
        assert page.locator("#main-content").get_by_text("Failed to load", exact=True).count() == 1
    else:
        page.locator('[name="semester_start_date"]').first.evaluate("el => el._flatpickr.open()")
        page.locator(".flatpickr-calendar.open").wait_for(state="visible")
        page.evaluate("() => GP.navigateTo('/dashboard/admin/users?calendar-return=1')")
        page.wait_for_function("""() => location.search.includes('calendar-return=1')
          && !document.querySelector('#main-content.is-arriving')""")
    assert page.locator(".flatpickr-calendar").count() == 0
    assert not errors, errors
