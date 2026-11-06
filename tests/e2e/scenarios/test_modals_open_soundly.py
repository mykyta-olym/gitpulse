"""Open every modal the app offers and audit what appears.

The page walk next door only ever sees a page at rest. Half this app's surface
is behind a button: the modals are where the User Info dialog was found
collapsing 107px when its data landed, and nothing automated could see that
because nothing opened it.

Every `[data-modal-open]` trigger on every reachable page is clicked, and the
dialog that appears is audited for the same faults the page walk looks for,
plus the one that only a dialog can have - changing size after it is already
open, which is what a reader sees as the thing deforming under them.
"""

from __future__ import annotations

import json
import os
from collections import deque
from contextlib import suppress
from urllib.parse import urlsplit

import pytest

from tests.e2e.scenarios.conftest import ROLES
from tests.e2e.scenarios.test_layout_is_sound import _AUDIT, _SKIP, _START

pytestmark = pytest.mark.e2e

if not os.getenv("GITPULSE_E2E_BASE_URL"):
    pytest.skip(
        "scenario walks need GITPULSE_E2E_BASE_URL pointing at a running server",
        allow_module_level=True,
    )

_MAX_PAGES = 12
_MAX_MODALS_PER_PAGE = 8
# How much a dialog may still resize after it has opened. A few pixels is the
# loader handing over to real content; a hundred is the collapse that was
# reported.
_SETTLE_TOLERANCE_PX = 24


def _page_links(page, base: str) -> list[str]:
    host = urlsplit(base).netloc
    hrefs = page.eval_on_selector_all(
        "a[href]", "els => els.map(e => e.getAttribute('href') || '')"
    )
    out = []
    for href in hrefs:
        if not href or any(skip in href for skip in _SKIP):
            continue
        if href.startswith("http") and urlsplit(href).netloc != host:
            continue
        path = urlsplit(href).path
        if path.startswith("/dashboard"):
            out.append(path)
    return out


# A role sees a different set of dialogs, and the narrow variants are where
# the reports come from. Measured on the seeded dev stack: an admin opens
# fourteen, a teacher reaches the three on the home page, a student is offered
# none at all. The floors sit under those so a trigger that stops working is
# caught, rather than the walk quietly shrinking to nothing while reporting
# green.
_MIN_OPENED = {"admin": 7, "teacher": 1, "student": 0}


@pytest.mark.parametrize("role", ROLES)
def test_every_modal_opens_and_holds_its_shape(context_for, live_server: str, role: str) -> None:
    ctx = context_for(role, 1500, 950)
    page = ctx.new_page()

    seen_pages: set[str] = set()
    queue: deque[str] = deque([_START])
    problems: list[str] = []
    opened = 0

    while queue and len(seen_pages) < _MAX_PAGES:
        path = queue.popleft()
        if path in seen_pages:
            continue
        seen_pages.add(path)

        resp = page.goto(live_server + path, wait_until="domcontentloaded")
        if not resp or resp.status >= 400:
            continue
        page.wait_for_timeout(700)

        for link in _page_links(page, live_server):
            if link not in seen_pages:
                queue.append(link)

        triggers = page.query_selector_all("[data-modal-open]")
        for trigger in triggers[:_MAX_MODALS_PER_PAGE]:
            modal_id = trigger.get_attribute("data-modal-open") or ""
            if not modal_id or not trigger.is_visible() or not trigger.is_enabled():
                continue
            # A trigger that will not click (covered, detached mid-walk) is its
            # own story; this walk is about what the modal looks like once open.
            with suppress(Exception):
                trigger.click(timeout=3000)
            page.wait_for_timeout(500)

            shape = page.evaluate(
                """(id) => {
                  const back = document.getElementById(id);
                  const dialog = back && back.querySelector('.modal');
                  if (!dialog) return null;
                  const r = dialog.getBoundingClientRect();
                  return { open: back.classList.contains('active'),
                           h: Math.round(r.height), w: Math.round(r.width) };
                }""",
                modal_id,
            )
            if not shape or not shape["open"]:
                page.keyboard.press("Escape")
                page.wait_for_timeout(250)
                continue

            opened += 1
            page.wait_for_timeout(900)
            after = page.evaluate(
                """(id) => {
                  const d = document.getElementById(id).querySelector('.modal');
                  const r = d.getBoundingClientRect();
                  return { h: Math.round(r.height), w: Math.round(r.width) };
                }""",
                modal_id,
            )
            drift = abs(after["h"] - shape["h"])
            if drift > _SETTLE_TOLERANCE_PX:
                problems.append(
                    f"{path} #{modal_id} resized after opening: "
                    f"height {shape['h']} -> {after['h']} ({drift}px)"
                )

            for finding in page.evaluate(_AUDIT):
                if finding["kind"] != "page-scrolls-sideways":
                    problems.append(f"{path} #{modal_id} {json.dumps(finding, ensure_ascii=False)}")

            page.keyboard.press("Escape")
            page.wait_for_timeout(350)

    ctx.close()

    assert opened >= _MIN_OPENED[role], (
        f"a {role} opened only {opened} modal(s) across {len(seen_pages)} pages - "
        "this walk has stopped exercising them"
    )
    assert not problems, (
        f"{opened} modals opened as {role}, {len(problems)} problem(s):"
        + chr(10)
        + "  "
        + (chr(10) + "  ").join(problems[:25])
    )
