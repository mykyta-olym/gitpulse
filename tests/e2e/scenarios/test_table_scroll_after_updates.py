"""Filtering and fragment swaps retain the shared horizontal-scroll behavior."""

from __future__ import annotations

import os

import pytest

pytestmark = pytest.mark.e2e

if not os.getenv("GITPULSE_E2E_BASE_URL"):
    pytest.skip("table updates need a running server", allow_module_level=True)


@pytest.fixture(params=[(390, "light"), (390, "dark"), (768, "light"), (768, "dark")])
def table_page(browser, context_for, live_server: str, request):
    width, theme = request.param
    with browser.new_context(
        storage_state=context_for("admin").storage_state(),
        viewport={"width": width, "height": 900},
        is_mobile=width == 390,
        has_touch=width == 390,
        service_workers="block",
    ) as ctx:
        page = ctx.new_page()
        page.bring_to_front()
        page.goto(live_server + "/dashboard/admin/courses?period=all")
        page.wait_for_function(
            "() => !!document.querySelector('#adminCoursesTable')?._clientPaginator"
        )
        page.evaluate("theme => document.documentElement.dataset.theme = theme", theme)
        yield page


def test_filtering_out_the_first_row_keeps_the_correct_actions_width(table_page) -> None:
    page = table_page
    rows = page.locator("#adminCoursesTable tbody tr[data-search]")
    if rows.count() < 2:
        pytest.skip("needs two courses")
    code = rows.nth(1).locator(".course-code").inner_text()
    page.locator("#courseSearch").fill(code)
    page.wait_for_function("""() => !document.querySelector(
      '#adminCoursesTable tbody tr[data-search]').getBoundingClientRect().height""")
    # Let the resize observer react to the hidden row before measuring.
    page.wait_for_timeout(250)
    assert page.evaluate("""() => {
      const table = document.getElementById('adminCoursesTable');
      const wrap = table.closest('.table-scroll'), sc = table.closest('.table-responsive');
      const width = table.querySelector('thead th:last-child').getBoundingClientRect().width;
      return wrap.classList.contains('sticky-column-off') === (sc.clientWidth - width < 190);
    }""")
    page.locator("#courseSearch").fill("")
    page.wait_for_function("""() => {
      const table = document.getElementById('adminCoursesTable');
      const sc = table.closest('.table-responsive');
      const width = table.querySelector('thead th:last-child').getBoundingClientRect().width;
      return table.closest('.table-scroll').classList.contains('sticky-column-off')
        === (sc.clientWidth - width < 190);
    }""")
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")


def test_htmx_replacements_keep_scroll_state_and_rebind_the_current_viewport(table_page) -> None:
    page = table_page
    for replacement in ("wrapper", "viewport", "table"):
        fragment = page.locator("#adminCoursesTable").evaluate(
            """(table, replacement) => {
              const target = replacement === 'wrapper' ? table.closest('.table-scroll')
                : replacement === 'viewport' ? table.closest('.table-responsive') : table;
              return target.outerHTML;
            }""",
            replacement,
        )
        page.route(
            "**/__table-fragment-test",
            lambda route, _request, body=fragment: route.fulfill(
                content_type="text/html", body=body
            ),
        )
        page.evaluate(
            """async replacement => {
              const table = document.getElementById('adminCoursesTable');
              const target = replacement === 'wrapper' ? table.closest('.table-scroll')
                : replacement === 'viewport' ? table.closest('.table-responsive') : table;
              await htmx.ajax('GET', '/__table-fragment-test', {target, swap: 'outerHTML'});
            }""",
            replacement,
        )
        page.wait_for_function("""() => !!document.getElementById('adminCoursesTable')
          .closest('.table-scroll').__tableScrollBound""")
        for end in (True, False, True):
            page.locator("#adminCoursesTable").evaluate(
                """(table, end) => {
                  const sc = table.closest('.table-responsive');
                  sc.scrollLeft = end ? sc.scrollWidth : 0;
                }""",
                end,
            )
            page.wait_for_function(
                """end => document.getElementById('adminCoursesTable')
                  .closest('.table-scroll').classList.contains('at-scroll-end') === end""",
                arg=end,
            )
        page.unroute("**/__table-fragment-test")


def test_htmx_replacement_of_a_navigation_strip_keeps_its_scroll_state(
    table_page, live_server: str
) -> None:
    page = table_page
    course = page.locator("#adminCoursesTable .course-code").first.get_attribute("href")
    page.goto(live_server + course)
    strip = page.locator("#main-content .tabs-nav").first
    strip.wait_for()
    fragment = strip.evaluate("el => el.outerHTML")
    page.route(
        "**/__strip-fragment-test",
        lambda route: route.fulfill(content_type="text/html", body=fragment),
    )
    page.evaluate("""async () => {
      const target = document.querySelector('#main-content .tabs-nav');
      await htmx.ajax('GET', '/__strip-fragment-test', {target, swap: 'outerHTML'});
    }""")
    page.wait_for_function("""() => !!document.querySelector('#main-content .tabs-nav')
      .__stripScrollBound""")
    strip.evaluate("el => { el.scrollLeft = el.scrollWidth; }")
    page.wait_for_function("""() => document.querySelector('#main-content .tabs-nav')
      .classList.contains('at-scroll-end')""")
