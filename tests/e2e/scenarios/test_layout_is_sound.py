"""Walk the app as each role and fail on anything that renders unsoundly.

This is the check the rest of the suite cannot make. The unit tests read the
bundle, and the existing browser walk loads a fixed list of pages as an admin.
Neither follows the app's own links, and neither looks at geometry - so the
defects that get reported from screenshots (a table whose content is clipped
with no way to scroll to it, a page that scrolls sideways, a dialog that
collapses when its data lands) were all invisible to it.

Three faults are audited on every page reached:

  * **Unreachable text** - an element clipped by `text-overflow: ellipsis`
    whose full text cannot be reached by scrolling anything. Truncation with a
    scrollable ancestor is fine; truncation without one hides content for good.
  * **Sideways scroll** - the document itself wider than the viewport. Wide
    content belongs in its own scroll container, never the page.
  * **Layout that will not settle** - the page still resizing well after load,
    which is what a reader sees as things jumping about.

Run against a server you point it at:

    GITPULSE_E2E_BASE_URL=http://127.0.0.1:8000 \
      python -m pytest tests/e2e/scenarios -q
"""

from __future__ import annotations

import json
import os
from collections import deque
from urllib.parse import urlsplit

import pytest

from tests.e2e.scenarios.conftest import ROLES

pytestmark = pytest.mark.e2e

if not os.getenv("GITPULSE_E2E_BASE_URL"):
    pytest.skip(
        "scenario walks need GITPULSE_E2E_BASE_URL pointing at a running server",
        allow_module_level=True,
    )

# Reached by following links, so the walk covers the parameterised pages (a
# course, a group, a project, a student) that a hard-coded list never does.
_START = "/dashboard/"
_MAX_PAGES = 24
_SKIP = ("/logout", "/oauth", "/docs", "/static/", "mailto:", "tel:", "#")

# What each role can actually reach from the dashboard. A student sees a much
# smaller app than an admin, so a single floor would either be vacuous for the
# admin or fail for the student. Raise these when a role gains pages.
_MIN_AUTHENTICATED = {"admin": 10, "teacher": 6, "student": 2}

_AUDIT = r"""
() => {
  const vw = document.documentElement.clientWidth;
  const name = (el) => el.tagName.toLowerCase() + '.' +
    (el.className || '').toString().trim().split(/\s+/).slice(0, 2).join('.');
  const findings = [];

  // HORIZONTALLY scrollable, specifically. Accepting any scrollable ancestor
  // made this check dead: the page itself scrolls vertically, so every element
  // on it looked reachable and the truncation audit never once fired. Text cut
  // off at the right edge is only reachable by scrolling sideways.
  const scrollableAncestor = (el) => {
    for (let p = el.parentElement; p; p = p.parentElement) {
      const s = getComputedStyle(p);
      if (/(auto|scroll)/.test(s.overflowX) && p.scrollWidth > p.clientWidth + 1) return true;
    }
    return false;
  };

  // 1. Text clipped with nowhere to scroll to reach it.
  document.querySelectorAll('td, th, .badge, .btn, a, span, div').forEach((el) => {
    if (el.children.length > 2) return;              // containers, not text nodes
    const s = getComputedStyle(el);
    if (s.textOverflow !== 'ellipsis') return;
    if (el.scrollWidth <= el.clientWidth + 1) return;
    if (scrollableAncestor(el)) return;
    // An ellipsis is a deliberate choice in a narrow column - a sidebar row
    // cannot be made to fit every course code. What makes it a DEFECT is the
    // value being unreadable, so text that carries its full form in a tooltip
    // is reachable and not reported.
    if (el.getAttribute('data-tippy-content') || el.getAttribute('title')
        || el.getAttribute('aria-label')) return;
    findings.push({
      kind: 'unreachable-text',
      text: (el.textContent || '').trim().slice(0, 40),
      needs: Math.round(el.scrollWidth), has: Math.round(el.clientWidth),
      sel: name(el)
    });
  });

  // 2. A child painting outside the box that is supposed to contain it. This
  //    is what "deformation" looks like in numbers: a control or cell wider
  //    than its own parent, spilling over whatever sits next to it.
  const boxed = 'td, th, .btn, .badge, .card, .form-group, .gl-dropdown';
  document.querySelectorAll(boxed).forEach((el) => {
    const parent = el.parentElement;
    if (!parent) return;
    const ps = getComputedStyle(parent);
    if (/(auto|scroll|hidden)/.test(ps.overflowX)) return;   // parent clips or scrolls: fine
    const a = el.getBoundingClientRect(), b = parent.getBoundingClientRect();
    const over = Math.round(a.right - b.right);
    if (over > 2 && a.width > 0) {
      findings.push({ kind: 'child-wider-than-parent', by: over,
                      child: name(el), parent: name(parent) });
    }
  });

  // 3. Images that resolved to nothing - a broken avatar or icon is a defect
  //    the eye reads instantly and no unit test can see.
  document.querySelectorAll('img').forEach((img) => {
    if (img.complete && img.naturalWidth === 0 && !img.classList.contains('gl-hidden')) {
      findings.push({ kind: 'broken-image', src: (img.currentSrc || img.src || '').slice(-60) });
    }
  });

  // 4. Duplicate ids. Every `getElementById` on the page silently picks the
  //    first, so a duplicate is a wiring bug waiting to be blamed on something
  //    else.
  const ids = {};
  document.querySelectorAll('[id]').forEach((el) => {
    ids[el.id] = (ids[el.id] || 0) + 1;
  });
  Object.keys(ids).filter((k) => ids[k] > 1).slice(0, 5).forEach((k) => {
    findings.push({ kind: 'duplicate-id', id: k, count: ids[k] });
  });

  // 5. The document itself scrolling sideways.
  if (document.documentElement.scrollWidth > vw + 1) {
    const wide = [...document.querySelectorAll('body *')]
      .filter((el) => el.getBoundingClientRect().right > vw + 1)
      .slice(0, 3)
      .map(name);
    findings.push({ kind: 'page-scrolls-sideways',
                    docWidth: document.documentElement.scrollWidth, viewport: vw, widest: wide });
  }
  return findings;
}
"""


def _links(page, base: str) -> list[str]:
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


def _settled_height(page) -> tuple[int, int]:
    first = page.evaluate("() => Math.round(document.body.scrollHeight)")
    page.wait_for_timeout(700)
    second = page.evaluate("() => Math.round(document.body.scrollHeight)")
    return first, second


# Wide is where the fixed-percentage layouts hide their truncation; narrow is
# where anything that cannot reflow spills out of its parent. Both have produced
# real defects, so both are walked.
_VIEWPORTS = ((1600, 1000), (1280, 900))


@pytest.mark.parametrize("role", ROLES)
@pytest.mark.parametrize(("width", "height"), _VIEWPORTS)
def test_every_reachable_page_renders_soundly(
    context_for, live_server: str, role: str, width: int, height: int
) -> None:
    ctx = context_for(role, width, height)
    page = ctx.new_page()
    console: list[str] = []
    page.on("pageerror", lambda e: console.append(f"pageerror: {str(e)[:160]}"))
    page.on(
        "console",
        lambda m: (
            console.append(f"console.{m.type}: {m.text[:160]}") if m.type == "error" else None
        ),
    )

    seen: set[str] = set()
    queue: deque[str] = deque([_START])
    problems: list[str] = []
    # A walk that silently ran against the login form would report a clean
    # sweep of nothing. Count the pages that actually rendered the app shell.
    authenticated = 0

    while queue and len(seen) < _MAX_PAGES:
        path = queue.popleft()
        if path in seen:
            continue
        seen.add(path)

        resp = page.goto(live_server + path, wait_until="domcontentloaded")
        status = resp.status if resp else 0
        if status >= 500:
            problems.append(f"[{role}] {path} -> HTTP {status}")
            continue
        if status in (401, 403, 404):
            continue  # a role legitimately cannot see everything
        page.wait_for_timeout(900)
        if page.evaluate("() => !!document.getElementById('appSidebar')"):
            authenticated += 1

        for finding in page.evaluate(_AUDIT):
            problems.append(f"[{role}] {path} {json.dumps(finding, ensure_ascii=False)}")

        before, after = _settled_height(page)
        if abs(after - before) > 120:
            problems.append(
                f"[{role}] {path} layout still moving after load: body height {before} -> {after}"
            )

        for link in _links(page, live_server):
            if link not in seen:
                queue.append(link)

    ctx.close()
    # The guard the whole walk rests on: if the session was rejected, every
    # "page" was the login form and every audit below passed on nothing. This
    # is also the coverage report - a walk that suddenly reaches three pages
    # instead of a dozen has stopped testing most of the app, and says so.
    assert authenticated >= _MIN_AUTHENTICATED[role], (
        f"[{role}] only {authenticated} of {len(seen)} pages rendered the app shell "
        f"(expected at least {_MIN_AUTHENTICATED[role]}); visited: {sorted(seen)}"
    )

    assert not problems, (
        f"{len(problems)} layout problem(s) as {role} across {len(seen)} pages:\n  "
        + "\n  ".join(problems[:30])
        + (f"\n  ... and {len(problems) - 30} more" if len(problems) > 30 else "")
        + ("\nconsole:\n  " + "\n  ".join(console[:10]) if console else "")
    )


def test_the_audit_can_actually_see_a_defect(context_for, live_server: str) -> None:
    """Plant each fault and check the audit reports it.

    Without this the walk above is unfalsifiable: an audit that silently
    matches nothing passes every page it is pointed at, which is precisely how
    the earlier browser suite once reported ten clean pages that were all the
    login form.
    """
    ctx = context_for("admin")
    page = ctx.new_page()
    page.goto(live_server + _START, wait_until="domcontentloaded")
    page.wait_for_timeout(600)

    page.evaluate(
        """() => {
        const host = document.querySelector('#main-content') || document.body;

        // unreachable text: clipped, and no scrollable ancestor to reach it
        const clipped = document.createElement('div');
        clipped.style.cssText =
          'width:40px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap';
        clipped.textContent = 'a value far too long to fit in forty pixels';
        host.appendChild(clipped);

        // a child painting outside its parent
        const parent = document.createElement('div');
        parent.style.cssText = 'width:100px;position:relative';
        const child = document.createElement('div');
        child.className = 'badge';
        child.style.cssText = 'width:400px';
        child.textContent = 'spills';
        parent.appendChild(child);
        host.appendChild(parent);

        // a broken image
        const img = document.createElement('img');
        img.src = '/static/img/definitely-not-here.png';
        host.appendChild(img);

        // a duplicate id
        const a = document.createElement('span'); a.id = 'planted-duplicate';
        const b = document.createElement('span'); b.id = 'planted-duplicate';
        host.appendChild(a); host.appendChild(b);
      }"""
    )
    # the broken image needs a tick to fail its request
    page.wait_for_timeout(900)

    kinds = {f["kind"] for f in page.evaluate(_AUDIT)}
    ctx.close()

    for expected in (
        "unreachable-text",
        "child-wider-than-parent",
        "broken-image",
        "duplicate-id",
    ):
        assert expected in kinds, (
            f"the audit did not report a planted {expected!r} - it is not "
            f"looking for it, so every clean run above proves nothing. Saw: {sorted(kinds)}"
        )
