"""Navigation targets reveal the actual shared card, including nested parents."""

from __future__ import annotations

import os
import time

import pytest

from app.main import templates

pytestmark = pytest.mark.e2e

if not os.getenv("GITPULSE_E2E_BASE_URL"):
    pytest.skip("needs GITPULSE_E2E_BASE_URL", allow_module_level=True)

_FIXTURE = """
{% from 'components/cards.html' import card with context %}
<a id="revealFirst" href="#revealDestination">First destination</a>
<a id="revealSecond" href="#secondDestination">Second destination</a>
<div style="height:900px"></div>
<details id="outerDisclosure"><summary>Outer section</summary>
{% call card(title='Shared collapsible card', id='revealCard', collapsible=true, collapsed=true) %}
  <details id="innerDisclosure"><summary>Inner section</summary>
    {% if named %}<a name="revealDestination">First destination</a>
    {% else %}<p id="revealDestination">First destination</p>{% endif %}
    <div style="height:300px"></div>
    <p id="secondDestination">Second destination</p>
  </details>
{% endcall %}
</details>
<div style="height:1200px"></div>
"""


def _markup(named=False):
    return templates.env.from_string(_FIXTURE).render(named=named, t=lambda value: value)


def _install(page, named=False):
    page.evaluate(
        "html => document.querySelector('#main-content').insertAdjacentHTML('afterbegin', html)",
        _markup(named),
    )
    page.wait_for_function(
        "() => Alpine.$data(document.querySelector('#revealCard')).open === false"
    )


def _assert_revealed(page, selector):
    target = page.locator(selector)
    target.wait_for(state="visible")
    page.wait_for_timeout(350)
    assert page.locator("#outerDisclosure").evaluate("el => el.open")
    assert page.locator("#innerDisclosure").evaluate("el => el.open")
    assert page.locator("#revealCard .card-collapse-btn").get_attribute("aria-expanded") == "true"
    position = target.evaluate("""el => {
      const root = el.closest('.gl-page-content');
      return {offset: el.getBoundingClientRect().top - root.getBoundingClientRect().top,
              windowY: scrollY};
    }""")
    assert position["offset"] == pytest.approx(16, abs=1)
    assert position["windowY"] == 0


@pytest.mark.parametrize(
    ("width", "mode"),
    [
        (390, "normal"),
        (1440, "normal"),
        (2560, "normal"),
        (390, "reduced"),
        (1440, "reduced"),
        (390, "no-gsap"),
        (1440, "no-gsap"),
    ],
)
def test_fragment_reveals_nested_disclosures_and_reopens_them(
    context_for, live_server, width, mode
):
    ctx = context_for("admin", width, 900)
    if mode == "no-gsap":
        ctx.route(
            "**/gsap*.js*",
            lambda route: route.fulfill(body="", content_type="application/javascript"),
        )
    page = ctx.new_page()
    if mode == "reduced":
        page.emulate_media(reduced_motion="reduce")
    page.bring_to_front()
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.goto(live_server + "/dashboard/preferences", wait_until="networkidle")
    assert page.evaluate("() => !!window.gsap") is (mode != "no-gsap")
    _install(page)
    page.locator("#revealFirst").click()
    _assert_revealed(page, "#revealDestination")
    history_length = page.evaluate("history.length")
    page.locator("#revealCard .card-header").click()
    page.locator("#revealDestination").wait_for(state="hidden")
    page.locator("#revealFirst").click()
    _assert_revealed(page, "#revealDestination")
    assert page.evaluate("history.length") == history_length
    assert not errors


def test_named_fragment_reveals_its_parents(context_for, live_server):
    page = context_for("admin").new_page()
    page.bring_to_front()
    page.goto(live_server + "/dashboard/preferences", wait_until="networkidle")
    _install(page, named=True)
    page.locator("#revealFirst").click()
    _assert_revealed(page, '[name="revealDestination"]')


def test_new_fragment_wins_during_disclosure_opening(context_for, live_server):
    page = context_for("admin", 390, 900).new_page()
    page.bring_to_front()
    page.goto(live_server + "/dashboard/preferences", wait_until="networkidle")
    _install(page)
    page.evaluate("""() => {
      document.querySelector('#revealFirst').click();
      document.querySelector('#revealSecond').click();
    }""")
    _assert_revealed(page, "#secondDestination")


def test_leaving_during_opening_does_not_scroll_the_new_page(context_for, live_server):
    page = context_for("admin", 390, 900).new_page()
    page.bring_to_front()
    page.goto(live_server + "/dashboard/preferences", wait_until="networkidle")
    _install(page)
    page.evaluate("""() => {
      document.querySelector('#revealFirst').click();
      GP.navigateTo('/dashboard/admin/users');
    }""")
    page.wait_for_url("**/dashboard/admin/users")
    page.wait_for_function("() => !document.querySelector('#main-content.is-arriving')")
    before = page.evaluate("""() => {
      const root = document.querySelector('.gl-page-content');
      root.scrollTop = 500; return root.scrollTop;
    }""")
    assert before > 0
    page.wait_for_timeout(450)
    assert page.evaluate("document.querySelector('.gl-page-content').scrollTop") == pytest.approx(
        before, abs=1
    )


def test_closing_a_parent_cancels_the_pending_scroll(context_for, live_server):
    page = context_for("admin", 390, 900).new_page()
    page.bring_to_front()
    page.goto(live_server + "/dashboard/preferences", wait_until="networkidle")
    _install(page)
    page.evaluate("document.querySelector('#revealFirst').click()")
    page.wait_for_timeout(50)
    before = page.evaluate("""() => {
      document.querySelector('#revealCard .card-header').click();
      const root = document.querySelector('.gl-page-content');
      root.scrollTop = 500; return root.scrollTop;
    }""")
    page.locator("#revealDestination").wait_for(state="hidden")
    page.wait_for_timeout(350)
    assert page.evaluate("document.querySelector('.gl-page-content').scrollTop") == pytest.approx(
        before, abs=1
    )


def test_a_delayed_spa_page_reveals_its_target_after_alpine_initializes(context_for, live_server):
    ctx = context_for("admin", 390, 900)
    page = ctx.new_page()
    page.bring_to_front()
    ctx.new_cdp_session(page).send("Network.setBypassServiceWorker", {"bypass": True})
    page.goto(live_server + "/dashboard/", wait_until="networkidle")

    def inject(route):
        response = route.fetch()
        body = response.text().replace(
            '<form id="preferencesForm"', _markup() + '<form id="preferencesForm"', 1
        )
        route.fulfill(response=response, body=body)

    ctx.route("**/dashboard/preferences", inject)

    def delay_script(route):
        time.sleep(0.4)
        route.continue_()

    ctx.route("**/js/pages/preferences.*.js", delay_script)
    page.evaluate("GP.navigateTo('/dashboard/preferences#revealDestination')")
    page.wait_for_url("**/preferences#revealDestination")
    _assert_revealed(page, "#revealDestination")


@pytest.mark.parametrize("suffix", ["#revealDestination", "?highlight=revealDestination"])
def test_direct_load_reveals_the_target_after_alpine_starts(context_for, live_server, suffix):
    ctx = context_for("admin", 390, 900)
    page = ctx.new_page()
    page.bring_to_front()
    ctx.new_cdp_session(page).send("Network.setBypassServiceWorker", {"bypass": True})

    def inject(route):
        response = route.fetch()
        body = response.text().replace(
            '<form id="preferencesForm"', _markup() + '<form id="preferencesForm"', 1
        )
        route.fulfill(response=response, body=body)

    ctx.route("**/dashboard/preferences*", inject)
    page.goto(live_server + "/dashboard/preferences" + suffix, wait_until="networkidle")
    if suffix.startswith("#"):
        _assert_revealed(page, "#revealDestination")
    else:
        page.locator("#revealDestination").wait_for(state="visible")
        page.wait_for_function("""() => {
          const el = document.querySelector('#revealDestination');
          const root = el.closest('.gl-page-content').getBoundingClientRect();
          const rect = el.getBoundingClientRect();
          return Math.abs(rect.top + rect.height / 2 - root.top - root.height / 2) < 1;
        }""")
        assert (
            page.locator("#revealCard .card-collapse-btn").get_attribute("aria-expanded") == "true"
        )
