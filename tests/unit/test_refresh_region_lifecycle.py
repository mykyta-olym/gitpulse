"""A refresh owns the region until it finishes, including cancellation and duplicates."""

import shutil
import subprocess
from pathlib import Path

import pytest

from tests.js_progress_runtime import top_progress_runtime


def test_refresh_region_releases_only_its_own_state(tmp_path):
    node = shutil.which("node")
    if not node:
        pytest.skip("Refresh lifecycle contract needs Node")
    scripts = Path(__file__).resolve().parents[2] / "src/app/templates/static/js"
    source = (scripts / "_parts/core/22-content-states.js").read_text(encoding="utf-8")
    harness = tmp_path / "refresh.cjs"
    harness.write_text(
        top_progress_runtime()
        + r"""
const assert = require('node:assert/strict');
"""
        + source
        + r"""
function region(busy = null, inert = false) {
  const classes = new Set();
  const attributes = new Map(busy === null ? [] : [['aria-busy', busy]]);
  return Object.assign(new EventTarget(), {nodeType: 1, isConnected: true, inert,
    getAttribute: name => attributes.get(name) ?? null,
    setAttribute: (name, value) => attributes.set(name, value),
    removeAttribute: name => attributes.delete(name),
    classList: {
      contains: name => classes.has(name), add: name => classes.add(name),
      toggle(name, active) { if (active) classes.add(name); else classes.delete(name); }
    }
  });
}
(async () => {
  const progress = document.documentElement.children[0];
  for (const result of [true, false, 'cancelled', 'detached']) {
    const block = region();
    let settled = 0;
    block.addEventListener('gp:region-settled', () => {
      settled++;
      assert.equal(block.getAttribute('aria-busy'), null);
      assert.equal(block.inert, false);
    });
    let finish, reads = 0;
    const load = () => { reads++; return new Promise(resolve => finish = resolve); };
    const pending = GP.refreshRegion({region: block, load});
    assert.equal(block.getAttribute('aria-busy'), 'true');
    assert.equal(block.inert, true);
    assert.equal(progress.classList.contains('is-active'), true);
    assert.equal(block.classList.contains('is-refreshing'), false);
    assert.equal(await GP.refreshRegion({region: block, load}), false);
    assert.equal(reads, 1);
    if (result === 'detached') block.isConnected = false;
    if (result === 'cancelled') finish(Promise.reject({superseded: true}));
    else finish(result === true);
    assert.equal(await pending, result === true);
    assert.equal(block.getAttribute('aria-busy'), null);
    assert.equal(block.inert, false);
    assert.equal(progress.classList.contains('is-active'), false);
    assert.equal(block.classList.contains('is-refreshing'), false);
    block.isConnected = true;
    assert.equal(settled, result === 'detached' ? 0 : 1);
    const retried = await GP.refreshRegion({region: block, load: async () => true});
    assert.equal(retried, true);
  }
  const locked = region('false', true);
  locked.classList.add('is-refreshing');
  await GP.refreshRegion({region: locked, load: async () => true});
  assert.equal(locked.inert, true);
  assert.equal(locked.getAttribute('aria-busy'), 'false');
  assert.equal(locked.classList.contains('is-refreshing'), true);
})();
""",
        encoding="utf-8",
    )
    subprocess.run(  # noqa: S603 - fixed local Node harness, no shell
        [node, str(harness)], check=True, capture_output=True, text=True, timeout=10
    )
