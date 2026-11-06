"""Changing tour text must resize the card without displacing its buttons."""

from __future__ import annotations

import os

import pytest

pytestmark = pytest.mark.e2e

if not os.getenv("GITPULSE_E2E_BASE_URL"):
    pytest.skip("tour geometry needs a running server", allow_module_level=True)


@pytest.mark.parametrize(("width", "height"), [(1440, 900), (390, 844), (700, 900), (844, 390)])
def test_next_and_back_resize_without_bouncing_the_actions(
    context_for, live_server: str, width: int, height: int
) -> None:
    ctx = context_for("admin", width, height)
    page = ctx.new_page()
    page.bring_to_front()
    page.goto(live_server + "/dashboard/")
    page.wait_for_function("() => !!window.GP?.tour")
    page.evaluate("() => document.fonts.ready")
    page.evaluate("""() => {
      GP.tour.register({slug: 'navigation-geometry', roles: ['admin'], steps: [
        {title_en: 'Welcome', body_en: 'Start here.'},
        {element: '#topBarClock', title_en: 'Long step',
         body_en: 'Review your courses and recent activity. '.repeat(24)},
        {element: '#globalSearchBtn', title_en: 'Short step', body_en: 'Continue here.'}
      ]});
      GP.tour.run('navigation-geometry');
    }""")
    page.locator(".driver-popover-next-btn").click()
    page.wait_for_timeout(500)

    for direction in ("next", "prev"):
        sample = page.evaluate(
            """async direction => {
              const read = () => {
                const root = document.querySelector('.gp-tour-popover');
                const card = root.getBoundingClientRect();
                const footer = root.querySelector('.driver-popover-footer').getBoundingClientRect();
                return {height: card.height, bottom: card.bottom, footer: footer.bottom,
                        width: card.width, top: card.top};
              };
              const before = read();
              document.querySelector('.driver-popover-' + direction + '-btn').click();
              const frames = [read()], start = performance.now();
              while (performance.now() - start < 500) {
                await new Promise(requestAnimationFrame);
                frames.push(read());
              }
              return {before, frames};
            }""",
            direction,
        )
        before, frames = sample["before"], sample["frames"]
        assert all(abs(frame["bottom"] - before["bottom"]) < 1 for frame in frames)
        assert all(abs(frame["footer"] - before["footer"]) < 1 for frame in frames)
        assert all(abs(frame["width"] - before["width"]) < 1 for frame in frames)
        assert all(frame["top"] >= -1 and frame["bottom"] <= height + 1 for frame in frames)
        if abs(frames[-1]["height"] - before["height"]) > 10:
            low, high = sorted((before["height"], frames[-1]["height"]))
            assert any(low + 1 < frame["height"] < high - 1 for frame in frames)

    page.keyboard.press("Escape")
    page.wait_for_function("() => !document.querySelector('.driver-overlay')")


def test_closing_during_a_placement_change_keeps_the_visible_position(
    context_for, live_server: str
) -> None:
    ctx = context_for("admin", 844, 390)
    page = ctx.new_page()
    page.bring_to_front()
    page.goto(live_server + "/dashboard/")
    page.wait_for_function("() => !!window.GP?.tour")
    page.evaluate("""() => {
      const target = document.createElement('button');
      target.id = 'tour-exit-target';
      target.textContent = 'Bottom action';
      target.style.cssText = 'position: fixed; bottom: 16px; left: 16px';
      document.body.append(target);
      GP.tour.register({slug: 'exit-geometry', roles: ['admin'], steps: [
        {element: '#topBarClock', title_en: 'Clock', body_en: 'Current time.'},
        {element: '#tour-exit-target', title_en: 'Action', body_en: 'Continue here.'}
      ]});
      GP.tour.run('exit-geometry');
    }""")
    page.wait_for_timeout(500)
    page.locator(".driver-popover-next-btn").click()
    page.wait_for_timeout(75)
    sample = page.evaluate("""async () => {
      const root = document.querySelector('.gp-tour-popover');
      const before = root.getBoundingClientRect();
      const anchor = document.documentElement.dataset.gpTourPos;
      const start = performance.now();
      root.querySelector('.driver-popover-close-btn').click();
      await new Promise(requestAnimationFrame);
      return {before: before.top, after: root.getBoundingClientRect().top, anchor,
              elapsed: performance.now() - start, height: before.height,
              duration: GP.motion.tokens.D.tour * 1000};
    }""")
    assert sample["anchor"] == "mobileTop", "the card did not switch placements"
    # An eased exit cannot travel faster than traversing the whole viewport
    # linearly. A px/% conversion jumped tens of pixels on this first frame.
    limit = (390 + sample["height"]) * sample["elapsed"] / sample["duration"] + 2
    assert abs(sample["after"] - sample["before"]) <= limit
    page.wait_for_function("() => !document.querySelector('.driver-overlay')")
