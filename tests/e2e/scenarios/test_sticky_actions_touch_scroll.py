"""Native touch pans keep pinned Actions steady without per-scroll sizing."""

from __future__ import annotations

import os

import pytest

from app.main import templates

pytestmark = pytest.mark.e2e

if not os.getenv("GITPULSE_E2E_BASE_URL"):
    pytest.skip("touch scrolling needs a running server", allow_module_level=True)

_FIXTURE = """
{% from 'components/cards.html' import card with context %}
{% from 'components/tables.html' import data_table %}
{% from 'components/buttons.html' import btn_icon_only, btn_link_icon_only %}
{% call card(title='Archived Courses', id='swipeFixture') %}
{% call data_table(class='table-scrollable table-scrollable-lg table-sticky-actions') %}
<colgroup><col class="col-arch-code"><col class="col-arch-name">
<col class="col-arch-year"><col class="col-arch-archived"><col class="col-arch-actions"></colgroup>
<thead><tr><th>Code</th><th>Name</th><th>Year / Semester</th>
<th>Archived</th><th>Actions</th></tr></thead>
<tbody>{% for name in ['Základy DevOps', 'Základy softvérového inžinierstva'] %}
<tr><td>DEVOPS</td><td>{{ name }}</td><td>2025/2026 · Summer</td><td>2026-07-11</td>
<td><div class="gl-row-actions">
{{ btn_link_icon_only('eye', '#', 'View', size='sm') }}
{{ btn_icon_only('check-circle', variant='success', size='sm') }}
{{ btn_icon_only('trash', variant='danger', size='sm') }}
</div></td></tr>{% endfor %}</tbody>
{% endcall %}{% endcall %}
"""


@pytest.mark.parametrize("width", [390, 400, 427, 430, 600])
@pytest.mark.parametrize("theme", ["light", "dark"])
@pytest.mark.parametrize("reduced", [False, True])
def test_touch_pans_do_not_remeasure_or_repin_actions(
    browser, context_for, live_server: str, width: int, theme: str, reduced: bool
):
    with browser.new_context(
        storage_state=context_for("admin").storage_state(),
        viewport={"width": width, "height": 952 if width == 427 else 1000},
        device_scale_factor=3,
        is_mobile=True,
        has_touch=True,
        service_workers="block",
        reduced_motion="reduce" if reduced else "no-preference",
    ) as ctx:
        page = ctx.new_page()
        page.bring_to_front()
        page.goto(live_server + "/dashboard/preferences")
        page.evaluate("theme => document.documentElement.dataset.theme = theme", theme)
        page.evaluate(
            """html => {
              document.getElementById('main-content').insertAdjacentHTML('afterbegin', html);
              const card = document.getElementById('swipeFixture');
              card.dispatchEvent(new CustomEvent('htmx:afterSwap', {
                bubbles:true, detail:{target:card}
              }));
            }""",
            templates.env.from_string(_FIXTURE).render(t=lambda value: value),
        )
        page.locator("#swipeFixture").scroll_into_view_if_needed()
        page.wait_for_timeout(250)
        initial = page.evaluate("""() => {
          const sc = document.querySelector('#swipeFixture .table-responsive');
          const wrap = sc.parentElement, head = sc.querySelector('thead th:last-child');
          const cell = sc.querySelector('tbody td:last-child');
          const box = sc.getBoundingClientRect();
          window.__sizingReads = 0; window.__panFrames = []; window.__recordPan = true;
          const measure = head.getBoundingClientRect.bind(head);
          head.getBoundingClientRect = () => { __sizingReads++; return measure(); };
          const sample = () => {
            if (!__recordPan) return;
            const rect = cell.getBoundingClientRect();
            __panFrames.push({x:rect.x, left:sc.scrollLeft,
              pinned:!wrap.classList.contains('sticky-column-off')});
            requestAnimationFrame(sample);
          };
          requestAnimationFrame(sample);
          const style = getComputedStyle(sc);
          return {x:box.x+180, y:box.y+55, max:sc.scrollWidth-sc.clientWidth,
            overscrollX:style.overscrollBehaviorX, overscrollY:style.overscrollBehaviorY,
            pinned:!wrap.classList.contains('sticky-column-off')};
        }""")
        assert initial["max"] > 10
        assert initial["overscrollX"] == "none", "native edge bounce can move pinned Actions"
        assert initial["overscrollY"] == "auto", (
            "table swipes must preserve vertical page scrolling"
        )
        cdp = ctx.new_cdp_session(page)
        layers = []

        def remember_layers(event):
            layers[:] = event.get("layers", [])

        cdp.on("LayerTree.layerTreeDidChange", remember_layers)
        cdp.send("LayerTree.enable")
        # A real native pan, including touch cancellation and momentum, rather
        # than assigning scrollLeft directly as the separator tests do.
        for direction in (-1, 1):
            x = initial["x"] if direction == -1 else initial["x"] - 144
            cdp.send(
                "Input.dispatchTouchEvent",
                {"type": "touchStart", "touchPoints": [{"x": x, "y": initial["y"], "id": 1}]},
            )
            for step in range(1, 13):
                cdp.send(
                    "Input.dispatchTouchEvent",
                    {
                        "type": "touchMove",
                        "touchPoints": [
                            {"x": x + direction * step * 12, "y": initial["y"], "id": 1}
                        ],
                    },
                )
                page.wait_for_timeout(16)
            cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})
            page.wait_for_timeout(150)
        # Reverse the same contact repeatedly, then drag beyond both edges.
        # Separate one-way swipes never exercised this reported interaction.
        x, y = initial["x"], initial["y"]
        for at_end in (False, True):
            page.locator("#swipeFixture .table-responsive").evaluate(
                "(sc, end) => sc.scrollLeft = end ? sc.scrollWidth : 0", at_end
            )
            cdp.send(
                "Input.dispatchTouchEvent",
                {"type": "touchStart", "touchPoints": [{"x": x, "y": y, "id": 1}]},
            )
            direction = -1 if at_end else 1
            for offset in (0, 30, 60, 90, 60, 30, 0, -30, -60, -30, 0, 30, 60, 30, 0):
                cdp.send(
                    "Input.dispatchTouchEvent",
                    {
                        "type": "touchMove",
                        "touchPoints": [{"x": x + direction * offset, "y": y, "id": 1}],
                    },
                )
                page.wait_for_timeout(16)
            cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})
            page.wait_for_timeout(150)
        report = page.evaluate("""() => {
          __recordPan = false;
          return {reads:__sizingReads, frames:__panFrames};
        }""")
        assert report["reads"] == 0, "swiping re-measures the Actions header"
        frames = report["frames"]
        assert max(frame["left"] for frame in frames) > 10, "the gesture did not scroll"
        assert all(frame["pinned"] == initial["pinned"] for frame in frames)
        if initial["pinned"]:
            # Stable DOM rectangles alone missed Chrome's compositor lag:
            # will-change:transform stripped the native sticky constraints.
            root = cdp.send("DOM.getDocument")["root"]["nodeId"]
            nodes = cdp.send(
                "DOM.querySelectorAll",
                {
                    "nodeId": root,
                    "selector": "#swipeFixture :is(thead,tbody) > tr > :last-child",
                },
            )["nodeIds"]
            references = {
                cdp.send("DOM.describeNode", {"nodeId": node})["node"]["backendNodeId"]
                for node in nodes
            }
            constrained = {
                layer["backendNodeId"] for layer in layers if layer.get("stickyPositionConstraint")
            }
            assert references <= constrained, "Actions lost native compositor sticky constraints"
            # A fractional CSS table width can differ from rounded scrollWidth
            # by less than one pixel when the sticky cell reaches its own edge.
            assert max(frame["x"] for frame in frames) - min(frame["x"] for frame in frames) < 1
        assert page.evaluate("() => document.documentElement.scrollWidth <= innerWidth")
        # Suppressing horizontal edge effects must not trap a vertical swipe
        # on the table: the page remains the phone's vertical scroller.
        before_top = page.locator(".gl-page-content").evaluate("el => el.scrollTop")
        cdp.send(
            "Input.dispatchTouchEvent",
            {"type": "touchStart", "touchPoints": [{"x": x - 80, "y": y, "id": 1}]},
        )
        for step in range(1, 9):
            cdp.send(
                "Input.dispatchTouchEvent",
                {
                    "type": "touchMove",
                    "touchPoints": [{"x": x - 80, "y": y - step * 12, "id": 1}],
                },
            )
            page.wait_for_timeout(16)
        cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})
        page.wait_for_timeout(150)
        assert page.locator(".gl-page-content").evaluate("el => el.scrollTop") > before_top + 5
