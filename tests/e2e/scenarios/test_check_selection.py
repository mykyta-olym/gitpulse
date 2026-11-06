"""The shared check picker must describe and protect the parameters it runs."""

from __future__ import annotations

import os

import pytest

from tests.e2e.scenarios.conftest import COURSE, PROJECT, TEAM

pytestmark = pytest.mark.e2e

if not os.getenv("GITPULSE_E2E_BASE_URL"):
    pytest.skip("check selection needs a running server", allow_module_level=True)


@pytest.fixture(params=["desktop", "mobile", "reduced", "no-gsap"])
def check_page(browser, context_for, live_server: str, request):
    mode = request.param
    with browser.new_context(
        storage_state=context_for("admin").storage_state(),
        service_workers="block",
        viewport={"width": 1440 if mode == "desktop" else 390, "height": 1000},
        is_mobile=mode != "desktop",
        has_touch=mode != "desktop",
        reduced_motion="reduce" if mode == "reduced" else "no-preference",
    ) as ctx:
        ctx.add_cookies([{"name": "gp_lang", "value": "en", "url": live_server}])
        writes = []

        def intercept(route):
            if route.request.method in {"GET", "HEAD"}:
                route.continue_()
            else:
                writes.append(route.request.url)
                route.fulfill(status=204)

        ctx.route("**/*", intercept)
        if mode == "no-gsap":
            ctx.route(
                "**/gsap*.js*",
                lambda route: route.fulfill(body="", content_type="application/javascript"),
            )
        page = ctx.new_page()
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.bring_to_front()
        page.goto(live_server + "/dashboard/courses/" + COURSE)
        page.locator("#runChecksGrid .rcm-cb").first.wait_for(state="attached")
        yield page
        assert not errors, errors
        assert not [url for url in writes if url.endswith("/run-checks")], writes


def _open(page, delay: int = 750) -> None:
    page.evaluate("() => GP.openModal('runChecksModal')")
    page.wait_for_timeout(delay)


def _selected(page) -> list[str]:
    return page.locator("#runChecksGrid .rcm-cb:checked").evaluate_all(
        "boxes => boxes.map(box => box.value)"
    )


def _confirm(page, accept: bool) -> None:
    page.locator("#gpConfirmDialog.active").wait_for()
    page.locator(
        '#gpConfirmDialog [data-gp-confirm="ok"]'
        if accept
        else '#gpConfirmDialog [data-gp-confirm="cancel"]'
    ).last.click()
    page.wait_for_function("() => !document.querySelector('#gpConfirmDialog.active')")


@pytest.mark.parametrize("delay", [0, 750])
@pytest.mark.parametrize("action", ["rcSelectAll", "rcDeselectAll"])
def test_early_and_late_bulk_edits_remain_dirty(check_page, delay: int, action: str) -> None:
    page = check_page
    _open(page, delay)
    baseline = _selected(page)
    assert 0 < len(baseline) < page.locator("#runChecksGrid .rcm-cb").count()
    page.locator("#" + action).click()
    changed = _selected(page)
    assert changed != baseline
    page.wait_for_timeout(750)
    assert page.evaluate("() => GP.hasUnsavedState()")
    page.locator("#runChecksModal .modal-close").click()
    _confirm(page, False)
    assert _selected(page) == changed
    page.locator("#runChecksModal .modal-close").click()
    _confirm(page, True)
    page.wait_for_function("() => !document.querySelector('#runChecksModal.active')")
    _open(page)
    assert _selected(page) == baseline
    assert not page.evaluate("() => GP.hasUnsavedState()")


def test_filter_is_transient_and_cannot_hide_the_real_selected_count(check_page) -> None:
    page = check_page
    _open(page)
    selection = _selected(page)
    total = page.locator("#runChecksGrid .rcm-cb").count()
    page.locator("#rcSearch").fill(selection[0])
    assert page.locator('[data-rcm-count="selected"]').inner_text() == str(len(selection))
    assert page.locator('[data-rcm-count="total"]').inner_text() == str(total)
    page.locator("#rcSearch").fill("NO-CHECK-MATCHES-THIS")
    assert page.locator("[data-rcm-empty]").is_visible()
    assert page.locator("#btnRunChecks").is_enabled()
    assert not page.evaluate("() => GP.hasUnsavedState()")
    page.keyboard.press("Escape")
    page.wait_for_function("() => !document.querySelector('#runChecksModal.active')")
    assert page.locator("#gpConfirmDialog.active").count() == 0
    _open(page)
    assert page.locator("#rcSearch").input_value() == ""
    assert page.locator("#runChecksGrid .rcm-item.is-hidden").count() == 0
    assert _selected(page) == selection


def test_bulk_selection_affects_only_visible_checks_and_defaults_restore_clean_state(
    check_page,
) -> None:
    page = check_page
    _open(page)
    baseline = _selected(page)
    page.locator("#rcSearch").fill(baseline[0])
    page.locator("#rcDeselectAll").click()
    visible = page.locator("#runChecksGrid .rcm-item:not(.is-hidden) .rcm-cb").evaluate_all(
        "boxes => boxes.map(box => box.value)"
    )
    assert _selected(page) == [code for code in baseline if code not in visible]
    assert page.locator('[data-rcm-count="selected"]').inner_text() == str(len(_selected(page)))
    page.locator("#rcResetDefaults").click()
    assert _selected(page) == baseline
    assert not page.evaluate("() => GP.hasUnsavedState()")


@pytest.mark.parametrize("scope", ["course", "team", "project", "student"])
def test_run_payload_matches_counter_and_closes_without_discard(
    check_page, live_server: str, scope: str
) -> None:
    page = check_page
    if scope == "student":
        page.goto(live_server + "/dashboard/teams/" + TEAM)
        link = page.locator('a[href*="/dashboard/students/"]').first
        link.wait_for(state="attached")
        path = link.get_attribute("href")
        page.goto(live_server + path)
    elif scope != "course":
        page.goto(
            live_server
            + ("/dashboard/teams/" + TEAM if scope == "team" else "/dashboard/projects/" + PROJECT)
        )
    page.locator("#runChecksGrid .rcm-cb").first.wait_for(state="attached")
    _open(page)
    page.locator("#runChecksGrid .rcm-cb:checked").first.uncheck()
    expected = _selected(page)
    assert len(expected) > 1
    page.locator("#rcSearch").fill(expected[0])
    assert page.locator('[data-rcm-count="selected"]').inner_text() == str(len(expected))
    assert page.locator("#runChecksGrid .rcm-item.is-hidden").count() > 0
    page.evaluate("""() => {
      const fetch = window.fetch;
      window.__runPayload = null;
      window.fetch = (url, options) => {
        if (options?.method === 'POST' && String(url).endsWith('/run-checks')) {
          window.__runPayload = JSON.parse(options.body);
          return new Promise(() => {});
        }
        return fetch(url, options);
      };
    }""")
    page.locator("#btnRunChecks").click()
    if scope == "course":
        _confirm(page, True)
    page.wait_for_function("() => !!window.__runPayload")
    page.wait_for_timeout(750)
    assert page.evaluate("() => __runPayload.check_codes") == expected
    assert page.locator("#gpConfirmDialog.active").count() == 0
    assert page.locator("#runChecksModal.active").count() == 0
    assert not page.evaluate("() => GP.hasUnsavedState()")


@pytest.mark.parametrize("lock", ["loading", "cooldown", "process", "archived"])
def test_filtering_does_not_take_over_a_locked_run_button(check_page, lock: str) -> None:
    page = check_page
    _open(page)
    page.evaluate(
        """lock => {
      const btn = document.getElementById('btnRunChecks');
      if (lock === 'loading') GP.setButtonLoading(btn, true);
      if (lock === 'cooldown') GP.applyCooldown(btn);
      if (lock === 'process') btn.dataset.processLocked = '1';
      if (lock === 'archived') btn.dataset.archivedLocked = '1';
      if (lock !== 'loading') btn.disabled = true;
    }""",
        lock,
    )
    if lock == "loading":
        page.wait_for_function(
            "() => document.getElementById('btnRunChecks').classList.contains('loading')"
        )
    page.evaluate("""() => {
      const btn = document.getElementById('btnRunChecks');
      GP.runChecksModal.applyFilter(document.querySelector('#runChecksModal .rcm'), 'R');
      window.__stillLocked = btn.disabled;
    }""")
    assert page.evaluate("() => window.__stillLocked")


def test_cancelling_the_run_confirmation_keeps_the_selection_unsaved(check_page) -> None:
    page = check_page
    _open(page)
    page.locator("#runChecksGrid .rcm-cb:checked").first.uncheck()
    expected = _selected(page)
    page.locator("#btnRunChecks").click()
    _confirm(page, False)
    assert page.locator("#runChecksModal.active").count() == 1
    assert _selected(page) == expected
    assert page.evaluate("() => GP.hasUnsavedState()")
    page.locator("#runChecksModal .modal-close").click()
    _confirm(page, True)
    page.wait_for_function("() => !document.querySelector('#runChecksModal.active')")
