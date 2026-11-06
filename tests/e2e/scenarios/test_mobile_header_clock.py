"""The clock and header controls must fit narrow screens in either time format."""

from __future__ import annotations

import os

import pytest

pytestmark = pytest.mark.e2e

if not os.getenv("GITPULSE_E2E_BASE_URL"):
    pytest.skip("header layout needs a running server", allow_module_level=True)


@pytest.mark.parametrize("width", [320, 360, 390, 414, 430])
@pytest.mark.parametrize("time_format", ["12h", "24h"])
def test_header_clock_and_controls_fit(browser, context_for, live_server, width, time_format):
    with browser.new_context(
        storage_state=context_for("admin").storage_state(),
        service_workers="block",
        viewport={"width": width, "height": 900},
        is_mobile=True,
        has_touch=True,
    ) as ctx:
        ctx.route(
            "**/*",
            lambda route: (
                route.continue_()
                if route.request.method in {"GET", "HEAD"}
                else route.fulfill(status=204)
            ),
        )
        page = ctx.new_page()
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.bring_to_front()
        page.goto(live_server + "/dashboard/")
        page.evaluate("() => document.fonts.ready")
        info = page.evaluate(
            """format => {
          document.documentElement.dataset.timeFormat = format;
          const clock = document.getElementById('topBarClock');
          document.getElementById('topBarClockText').textContent = '25.10. '
            + formatClock(new Date(2026, 9, 25, 23, 59, 0));
          const box = el => {
            const r = el.getBoundingClientRect();
            return {left: r.left, right: r.right, width: r.width};
          };
          const controls = Array.from(document.querySelectorAll(
            '#mobileMenuBtn,#globalSearchBtn,#topBarClock,.gl-top-bar-avatar-btn',
          )).map(box);
          return {controls, clock: box(clock), context: box(clock.parentElement),
            clockText: clock.textContent.trim(),
            overflow: document.documentElement.scrollWidth > innerWidth};
        }""",
            time_format,
        )
        assert not info["overflow"]
        assert info["clock"]["width"] > 0
        assert info["clock"]["right"] <= info["context"]["right"] + 1
        assert ("PM" in info["clockText"]) == (time_format == "12h")
        assert len(info["controls"]) == 4
        for index, control in enumerate(info["controls"]):
            assert control["width"] > 0
            assert 0 <= control["left"] < control["right"] <= width + 1
            for other in info["controls"][index + 1 :]:
                assert control["right"] <= other["left"] or other["right"] <= control["left"]
        assert not errors, errors
