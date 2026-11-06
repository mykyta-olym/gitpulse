"""A previous table read cannot retire the next read's busy state."""

import shutil
import subprocess
from pathlib import Path

import pytest


def test_table_semantics_follow_the_read_and_cancel_late_spinners(tmp_path):
    node = shutil.which("node")
    if not node:
        pytest.skip("Table lifecycle contract needs Node")
    source = (
        Path(__file__).resolve().parents[2]
        / "src/app/templates/static/js/_parts/core/22-content-states.js"
    ).read_text(encoding="utf-8")
    harness = tmp_path / "table-busy.cjs"
    harness.write_text(
        r"""
const assert = require('node:assert/strict');
global.window = {GP: {}};
global.GP = window.GP;
global.document = {addEventListener() {}};
global.MutationObserver = class {observe() {} disconnect() {}};
"""
        + source
        + r"""
(async () => {
  const classes = new Set(), attributes = new Map();
  const viewport = {style: {minHeight: '24px'}, getBoundingClientRect: () => ({height: 120})};
  const tbody = {inert: false, dataset: {},
    children: [{classList: {contains: () => false}, hasAttribute: () => false}],
    classList: {contains: name => classes.has(name), add: name => classes.add(name),
      remove: name => classes.delete(name)},
    closest: () => viewport,
    getAttribute: name => attributes.get(name) ?? null,
    setAttribute: (name, value) => attributes.set(name, value),
    removeAttribute: name => attributes.delete(name)};
  GP.tableLoading(tbody, 1);
  assert.equal(tbody.inert, true);
  assert.equal(attributes.get('aria-busy'), 'true');
  assert.equal(classes.has('is-refreshing'), false);
  GP.tableLoaded(tbody);
  assert.equal(tbody.inert, false);
  assert.equal(tbody._busyTimer, 0);
  assert.equal(viewport.style.minHeight, '24px');
  GP.tableLoading(tbody, 1);
  await new Promise(resolve => setTimeout(resolve, 200));
  assert.equal(tbody.inert, true);
  assert.equal(attributes.get('aria-busy'), 'true');
  assert.equal(classes.has('is-refreshing'), true);
  GP.tableLoaded(tbody);
  assert.equal(tbody.inert, false);
  assert.equal(attributes.has('aria-busy'), false);
  assert.equal(classes.has('is-refreshing'), false);
  assert.equal(viewport.style.minHeight, '24px');
})();
""",
        encoding="utf-8",
    )
    subprocess.run(  # noqa: S603 - fixed local Node harness, no shell
        [node, str(harness)], check=True, capture_output=True, text=True, timeout=10
    )
