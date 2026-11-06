"""The pinned Actions edge signals hidden columns without moving the controls."""

from __future__ import annotations

import os

import pytest

pytestmark = pytest.mark.e2e

if not os.getenv("GITPULSE_E2E_BASE_URL"):
    pytest.skip("sticky column checks need a running server", allow_module_level=True)


@pytest.mark.parametrize("path", ["users", "courses"])
@pytest.mark.parametrize("theme", ["light", "dark"])
@pytest.mark.parametrize("width", [390, 768])
def test_separator_fades_at_the_scroll_end_and_returns(
    browser, context_for, live_server: str, path: str, theme: str, width: int
) -> None:
    with browser.new_context(
        storage_state=context_for("admin").storage_state(),
        viewport={"width": width, "height": 900},
        is_mobile=width == 390,
        has_touch=width == 390,
        service_workers="block",
    ) as ctx:
        page = ctx.new_page()
        page.bring_to_front()
        page.goto(live_server + "/dashboard/admin/" + path)
        page.evaluate("theme => document.documentElement.dataset.theme = theme", theme)
        page.wait_for_function("""() => [...document.querySelectorAll('.table-scroll')]
          .some(w => w.__tableScrollBound && w.querySelector(
            '.table-sticky-actions tbody tr td:last-child:not([colspan])'))""")
        report = page.evaluate("""async () => {
          const wrap = [...document.querySelectorAll('.table-scroll')].find(w =>
            w.querySelector('.table-sticky-actions tbody tr td:last-child:not([colspan])'));
          const sc = wrap.querySelector('.table-responsive');
          const cells = () => [...wrap.querySelectorAll(
            '.table-sticky-actions > :is(thead,tbody) > tr > :last-child:not([colspan])')];
          const last = cells().find(cell => cell.tagName === 'TD');
          const opacity = cell => Number(getComputedStyle(cell, '::before').opacity);
          const rect = () => {
            const r = last.getBoundingClientRect();
            return [r.left, r.right, r.width];
          };
          sc.scrollLeft = 0;
          await new Promise(r => setTimeout(r, 180));
          const pinned = !wrap.classList.contains('sticky-column-off');
          const overflow = wrap.classList.contains('is-scrollable-x');
          const initial = opacity(last), before = rect();
          const themeColor = getComputedStyle(last, '::before').backgroundColor;
          const pointerEvents = getComputedStyle(last, '::before').pointerEvents;
          sc.scrollLeft = sc.scrollWidth;
          const frames = [];
          for (let i = 0; i < 16; i++) {
            await new Promise(requestAnimationFrame);
            frames.push(opacity(last));
          }
          const end = cells().map(opacity), after = rect();
          const atEnd = wrap.classList.contains('at-scroll-end');
          sc.scrollLeft = 0;
          await new Promise(r => setTimeout(r, 180));
          return {pinned,overflow,initial,frames,end,before,after,atEnd,
            returned: opacity(last),themeColor,pointerEvents};
        }""")
        assert report["atEnd"]
        if report["pinned"] and report["overflow"]:
            assert report["initial"] == 1
            assert report["returned"] == 1
            assert all(value == 0 for value in report["end"])
            assert any(0 < value < 1 for value in report["frames"])
            assert report["before"] == pytest.approx(report["after"], abs=1)
            assert report["themeColor"] not in ["transparent", "rgba(0, 0, 0, 0)"]
            assert report["pointerEvents"] == "none"
        else:
            assert report["initial"] in [0, 1]  # no generated separator when unpinned
            assert page.evaluate("""() => {
              const wrap = [...document.querySelectorAll('.table-scroll')].find(w =>
                w.querySelector('.table-sticky-actions tbody tr td:last-child:not([colspan])'));
              const cell = wrap.querySelector('.table-sticky-actions tbody td:last-child');
              return getComputedStyle(cell, '::before').content === 'none'
                || Number(getComputedStyle(cell, '::before').opacity) === 0;
            }""")
        assert page.evaluate("() => document.documentElement.scrollWidth <= innerWidth")


def test_separator_is_hidden_without_overflow_and_honors_reduced_motion(
    browser, context_for, live_server: str
) -> None:
    with browser.new_context(storage_state=context_for("admin").storage_state()) as ctx:
        page = ctx.new_page()
        page.bring_to_front()
        page.set_viewport_size({"width": 2560, "height": 1000})
        page.goto(live_server + "/dashboard/admin/users")
        page.evaluate("() => document.documentElement.dataset.layoutWidth = 'fluid'")
        page.wait_for_function("""() => document.querySelector('.users-table')
          ?.closest('.table-scroll')?.__tableScrollBound""")
        page.wait_for_timeout(180)
        cell = page.locator(".users-table tbody td:last-child:not([colspan])").first
        assert cell.evaluate("""cell =>
          Number(getComputedStyle(cell, '::before').opacity) === 0""")
        page.set_viewport_size({"width": 768, "height": 1000})
        page.emulate_media(reduced_motion="reduce")
        page.wait_for_timeout(180)
        report = page.locator(".users-table").evaluate("""async table => {
          const sc = table.closest('.table-responsive');
          sc.scrollLeft = 0;
          await new Promise(requestAnimationFrame);
          const cell = table.querySelector('tbody td:last-child:not([colspan])');
          const duration = parseFloat(getComputedStyle(cell, '::before').transitionDuration);
          sc.scrollLeft = sc.scrollWidth;
          return {duration};
        }""")
        assert report["duration"] < 0.001
        page.wait_for_function("""() => {
          const table = document.querySelector('.users-table');
          const cell = table.querySelector('tbody td:last-child:not([colspan])');
          return table.closest('.table-scroll').classList.contains('at-scroll-end')
            && Number(getComputedStyle(cell, '::before').opacity) === 0;
        }""")
