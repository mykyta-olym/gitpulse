"""Tooltips follow live references through page swaps and table updates."""

from __future__ import annotations

import os

import pytest

from tests.e2e.scenarios.conftest import COURSE

pytestmark = pytest.mark.e2e

if not os.getenv("GITPULSE_E2E_BASE_URL"):
    pytest.skip("tooltip lifecycle needs a running server", allow_module_level=True)


@pytest.fixture(params=["desktop", "mobile", "reduced", "no-gsap"])
def tooltip_page(browser, context_for, live_server: str, request):
    mode = request.param
    with browser.new_context(
        storage_state=context_for("admin").storage_state(),
        service_workers="block",
        viewport={"width": 1440 if mode == "desktop" else 390, "height": 1000},
        is_mobile=mode != "desktop",
        has_touch=mode != "desktop",
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
                lambda route: route.fulfill(body="", content_type="application/javascript"),
            )
        page = ctx.new_page()
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.bring_to_front()
        page.goto(live_server + "/dashboard/courses/" + COURSE)
        page.wait_for_function(
            "() => !!document.querySelector('#main-content .card-header-info-tip')?._tippy"
        )
        yield page
        assert not errors, errors


def _remember_info(page):
    page.evaluate("""() => {
      window.__tipReference = document.querySelector('#main-content .card-header-info-tip');
      window.__tipInstance = __tipReference._tippy;
    }""")


def _ordinary_tooltip(page):
    # Exercise the real delegated mouseover/focus path, including on a hybrid
    # touch device, rather than constructing a test-only Tippy instance.
    button = page.locator("#main-content [data-tippy-content]:not(.card-header-info-tip)").first
    button.hover()
    page.wait_for_function(
        "() => [...document.querySelectorAll('#main-content [data-tippy-content]')]"
        ".some(el => !el.matches('.card-header-info-tip') && !!el._tippy)"
    )
    page.evaluate("""() => {
      window.__tipReference = [...document.querySelectorAll('#main-content [data-tippy-content]')]
        .find(el => !el.matches('.card-header-info-tip') && !!el._tippy);
      window.__tipInstance = __tipReference._tippy;
    }""")


def test_navigation_destroys_the_open_card_explanation(tooltip_page):
    page = tooltip_page
    _remember_info(page)
    page.evaluate("() => __tipInstance.show()")
    page.wait_for_function("() => __tipInstance.state.isVisible")
    page.evaluate("() => GP.navigateTo('/dashboard/admin/users')")
    page.wait_for_function("() => !__tipReference.isConnected")
    page.wait_for_function("() => __tipInstance.state.isDestroyed")
    assert not page.locator('[data-tippy-root] [data-state="visible"]').count()


@pytest.mark.parametrize("kind", ["info", "ordinary"])
def test_removing_a_reference_disposes_hidden_and_visible_instances(tooltip_page, kind):
    page = tooltip_page
    (_remember_info if kind == "info" else _ordinary_tooltip)(page)
    page.evaluate("""() => {
      __tipInstance.show();
      __tipReference.removeAttribute('data-tippy-content');
      __tipReference.parentElement.remove();
    }""")
    page.wait_for_function("() => __tipInstance.state.isDestroyed")
    assert not page.evaluate("() => __tipInstance.popper.isConnected")


def test_an_unopened_card_explanation_is_disposed_too(tooltip_page):
    page = tooltip_page
    _remember_info(page)
    assert not page.evaluate("() => __tipInstance.state.isVisible")
    page.evaluate("() => __tipReference.remove()")
    page.wait_for_function("() => __tipInstance.state.isDestroyed")


def test_moving_a_reference_keeps_its_instance_and_explanation(tooltip_page):
    page = tooltip_page
    _remember_info(page)
    page.evaluate("""() => {
      const parent = document.createElement('div');
      document.getElementById('main-content').appendChild(parent);
      parent.appendChild(__tipReference);
      document.getElementById('main-content').appendChild(__tipReference);
      parent.remove();
    }""")
    page.wait_for_timeout(100)
    assert page.evaluate("() => __tipReference._tippy === __tipInstance")
    assert not page.evaluate("() => __tipInstance.state.isDestroyed")
    page.evaluate("() => __tipInstance.show()")
    assert page.evaluate("() => __tipInstance.state.isVisible")


def test_card_explanations_read_the_current_content_and_share_one_open_popup(tooltip_page):
    page = tooltip_page
    result = page.evaluate("""() => {
      const first = document.querySelector('#main-content .card-header-info-tip');
      const second = first.cloneNode(true);
      first.parentElement.appendChild(second);
      initCardInfoTips(first.parentElement);
      first._tippy.show(); first._tippy.hide(0);
      first.dataset.tippyContent = 'Updated course explanation';
      first._tippy.show();
      const text = first._tippy.popper.textContent;
      second._tippy.show();
      return {text, firstVisible:first._tippy.state.isVisible,
        secondVisible:second._tippy.state.isVisible};
    }""")
    assert result == {
        "text": "Updated course explanation",
        "firstVisible": False,
        "secondVisible": True,
    }


def test_a_removed_pending_tooltip_cannot_open_later(tooltip_page):
    page = tooltip_page
    _ordinary_tooltip(page)
    page.evaluate("""() => {
      __tipInstance.hide(0);
      __tipInstance.setProps({delay:[150,0]});
      __tipReference.dispatchEvent(new MouseEvent('mouseenter'));
      __tipReference.remove();
    }""")
    page.wait_for_function("() => __tipInstance.state.isDestroyed")
    page.wait_for_timeout(250)
    assert not page.evaluate("() => __tipInstance.popper.isConnected")
