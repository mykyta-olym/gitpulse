"""Removed dialogs cannot block or close the next dialog with the same id."""

from __future__ import annotations

import os

import pytest

pytestmark = pytest.mark.e2e

if not os.getenv("GITPULSE_E2E_BASE_URL"):
    pytest.skip("modal retirement checks need a running server", allow_module_level=True)


@pytest.fixture(params=["desktop", "mobile", "reduced", "no-gsap"])
def retirement_page(browser, context_for, live_server: str, request):
    mode = request.param
    with browser.new_context(
        storage_state=context_for("admin").storage_state(),
        service_workers="block",
        viewport={"width": 1440 if mode == "desktop" else 390, "height": 900},
        has_touch=mode != "desktop",
        is_mobile=mode != "desktop",
        reduced_motion="reduce" if mode == "reduced" else "no-preference",
    ) as ctx:
        ctx.route(
            "**/*",
            lambda route: (
                route.continue_()
                if route.request.method in {"GET", "HEAD"}
                else route.fulfill(status=204)
            ),
        )
        if mode == "no-gsap":
            ctx.route(
                "**/gsap*.js*",
                lambda r: r.fulfill(body="", content_type="application/javascript"),
            )
        page = ctx.new_page()
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.on(
            "console",
            lambda msg: errors.append(msg.text) if "Blocked aria-hidden" in msg.text else None,
        )
        page.bring_to_front()
        page.goto(live_server + "/dashboard/")
        page.wait_for_function("() => !!window.GP?.navigateTo")
        page.evaluate("() => GP.openModal('createCourseModal')")
        page.wait_for_timeout(450)
        yield page
        assert not errors, errors


def _hold_close(page) -> None:
    page.evaluate("""() => {
      window.__retiringModal = document.getElementById('createCourseModal');
      const original = GP.motion.overlayOut;
      GP.motion.overlayOut = (modal, done) => {
        if (modal === __retiringModal) window.__finishOldClose = done;
        else original(modal, done);
      };
    }""")


def _assert_current_open(page) -> None:
    assert page.evaluate("""() => {
      const current = document.getElementById('createCourseModal');
      return current.classList.contains('active') && !current.classList.contains('closing')
        && current.getAttribute('aria-hidden') === 'false'
        && document.body.classList.contains('scroll-locked');
    }""")


def test_replacement_opens_at_arrival_and_ignores_the_retired_close(
    retirement_page, live_server: str
):
    page = retirement_page
    # Replay a real dashboard response while holding only the outgoing exit
    # callback. Network/animation speed cannot hide the ownership regression.
    html = page.context.request.get(live_server + "/dashboard/").text()
    url = live_server + "/dashboard/?retirement-probe=1"
    page.route(url, lambda r: r.fulfill(body=html, content_type="text/html"))
    _hold_close(page)
    page.evaluate(
        """url => {
          window.__arrivalState = null;
          window.addEventListener('gp:page-ready', () => {
            const current = document.getElementById('createCourseModal');
            GP.openModal(current.id);
            window.__arrivalState = {replaced: current !== __retiringModal,
              oldConnected: __retiringModal.isConnected,
              active: current.classList.contains('active')};
          }, {once: true});
          GP.navigateTo(url);
        }""",
        url,
    )
    page.wait_for_function("() => !!window.__arrivalState")
    state = page.evaluate("() => __arrivalState")
    assert state == {"replaced": True, "oldConnected": False, "active": True}
    page.locator("#courseCode").fill("NEW-DRAFT")
    assert page.evaluate("() => GP.hasUnsavedState()")
    page.evaluate("() => __finishOldClose()")
    _assert_current_open(page)
    assert page.evaluate("() => GP.hasUnsavedState()")
    page.keyboard.press("Escape")
    page.locator("#gpConfirmDialog.active").wait_for()


def test_reopened_node_ignores_its_previous_close_completion(retirement_page):
    page = retirement_page
    _hold_close(page)
    page.evaluate("""() => {
      GP.forceCloseModal('createCourseModal');
      GP.openModal('createCourseModal');
      __finishOldClose();
    }""")
    _assert_current_open(page)
    page.locator("#courseCode").fill("REOPENED")
    assert page.evaluate("() => GP.hasUnsavedState()")


def test_removing_an_active_page_modal_releases_it_immediately_once(retirement_page):
    page = retirement_page
    state = page.evaluate("""() => {
      window.__closedCount = 0;
      document.addEventListener('modal-closed', event => {
        if (event.detail.id === 'createCourseModal') ++__closedCount;
      });
      window.__retiringModal = document.getElementById('createCourseModal');
      GP.dropPageModals();
      return {connected: __retiringModal.isConnected,
        active: __retiringModal.classList.contains('active'),
        hidden: __retiringModal.getAttribute('aria-hidden'),
        locked: document.body.classList.contains('scroll-locked'), count: __closedCount};
    }""")
    assert state == {
        "connected": False,
        "active": False,
        "hidden": "true",
        "locked": False,
        "count": 1,
    }
    page.wait_for_timeout(450)
    assert page.evaluate("() => __closedCount") == 1


def test_reused_id_does_not_inherit_old_guards_or_dirty_fields(retirement_page):
    page = retirement_page
    page.locator("#courseCode").fill("OLD-DRAFT")
    assert page.evaluate("() => GP.hasUnsavedState()")
    state = page.evaluate("""() => {
      GP.registerModalGuard('createCourseModal', () => false);
      GP.dropPageModals();
      const fresh = document.createElement('div');
      fresh.id = 'createCourseModal'; fresh.className = 'modal-backdrop';
      fresh.innerHTML = '<div class="modal" tabindex="-1"><div class="modal-body">'
        + '<p>Read-only replacement</p></div></div>';
      document.body.append(fresh);
      GP.openModal(fresh.id);
      const dirty = GP.hasUnsavedState(), active = fresh.classList.contains('active');
      const closed = GP.closeModal(fresh.id);
      return {dirty, active, closed};
    }""")
    assert state == {"dirty": False, "active": True, "closed": True}
    page.wait_for_timeout(450)
    assert not page.evaluate("() => document.body.classList.contains('scroll-locked')")


def test_page_retirement_preserves_the_global_confirmation_and_its_lock(retirement_page):
    page = retirement_page
    page.evaluate("""() => {
      window.__confirmationResult = null;
      GP.confirmDialog({message: 'Keep the global dialog'}).then(value => {
        window.__confirmationResult = value;
      });
      GP.dropPageModals();
    }""")
    page.wait_for_timeout(450)
    assert page.locator("#gpConfirmDialog.active").count() == 1
    assert page.evaluate("() => document.body.classList.contains('scroll-locked')")
    page.keyboard.press("Escape")
    page.wait_for_function("() => __confirmationResult === false")
    assert not page.evaluate("() => document.body.classList.contains('scroll-locked')")
