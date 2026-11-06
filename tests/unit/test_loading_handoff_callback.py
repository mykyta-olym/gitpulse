"""Charts measure their visible container as soon as their data is ready."""

import shutil
import subprocess
from pathlib import Path

import pytest


def test_chart_callback_waits_for_the_visible_container(tmp_path):
    node = shutil.which("node")
    if not node:
        pytest.skip("Loading hand-off contract needs Node")
    static = Path(__file__).resolve().parents[2] / "src/app/templates/static/js"
    harness = tmp_path / "handoff.cjs"
    harness.write_text(
        r"""
const assert = require('node:assert/strict');
global.window = {GP: {}, matchMedia: () => ({matches: true, addEventListener() {}})};
global.GP = window.GP;
global.document = {readyState: 'loading', documentElement: {}, addEventListener() {}};
global.getComputedStyle = () => ({getPropertyValue: () => ''});
global.requestAnimationFrame = fn => fn();
"""
        + (static / "_parts/core/22-content-states.js").read_text(encoding="utf-8")
        + (static / "motion.js").read_text(encoding="utf-8")
        + r"""
(async () => {
  {
    let hidden = true, calls = 0;
    const content = {classList: {remove(c) {assert.equal(c, 'd-none'); hidden = false;}}};
    const loader = {classList: {contains: () => false, add() {}}};
    await new Promise(resolve => {
      GP.revealAfterLoading(loader, content, () => {
        assert.equal(hidden, false);
        calls++; resolve();
      });
      assert.equal(calls, 1);
    });
    assert.equal(calls, 1);
  }
  let calls = 0;
  const content = {classList: {remove() {}}};
  GP.revealAfterLoading(null, content, () => calls++);
  assert.equal(calls, 1);
})();
""",
        encoding="utf-8",
    )
    subprocess.run(  # noqa: S603 - fixed local Node harness, no shell
        [node, str(harness)], check=True, capture_output=True, text=True, timeout=10
    )


def test_modal_handoff_cannot_outlive_its_read(tmp_path):
    node = shutil.which("node")
    if not node:
        pytest.skip("Modal hand-off contract needs Node")
    static = Path(__file__).resolve().parents[2] / "src/app/templates/static/js"
    harness = tmp_path / "modal-handoff.cjs"
    harness.write_text(
        r"""
const assert = require('node:assert/strict');
global.window = {GP: {}, matchMedia: () => ({matches: true, addEventListener() {}})};
global.GP = window.GP;
global.document = {readyState: 'loading', documentElement: {}, addEventListener() {}};
global.getComputedStyle = () => ({getPropertyValue: () => ''});
global.requestAnimationFrame = fn => fn();
"""
        + (static / "_parts/core/12-user-info.js").read_text(encoding="utf-8")
        + (static / "_parts/core/22-content-states.js").read_text(encoding="utf-8")
        + (static / "motion.js").read_text(encoding="utf-8")
        + r"""
(async () => {
  const attrs = new Map();
  const body = {isConnected: true, innerHTML: 'loading',
    setAttribute: (name, value) => attrs.set(name, value),
    removeAttribute: name => attrs.delete(name),
    getBoundingClientRect: () => ({height: 120})};
  const modal = {id: 'user-info', isConnected: true, querySelector: () => body,
    classList: {contains: name => name === 'active'}};
  let read = GP.beginUserInfoRead(modal, 'first');
  assert.equal(attrs.get('aria-busy'), 'true');
  const next = GP.beginUserInfoRead(modal, 'second');
  assert.equal(read.controller.signal.aborted, true);
  read.finish();
  assert.equal(attrs.get('aria-busy'), 'true');
  read = next;
  const stale = GP.swapModalBodyAnimated(body, 'stale', read.current);
  GP.cancelUserInfoRead(modal.id);
  assert.equal(await stale, false);
  assert.equal(body.innerHTML, 'loading');
  assert.equal(attrs.has('aria-busy'), false);
  read = GP.beginUserInfoRead(modal, 'third');
  assert.equal(await GP.swapModalBodyAnimated(body, 'ready', read.current), true);
  assert.equal(body.innerHTML, 'ready');
  read.finish();
  assert.equal(attrs.has('aria-busy'), false);
})();
""",
        encoding="utf-8",
    )
    subprocess.run(  # noqa: S603 - fixed local Node harness, no shell
        [node, str(harness)], check=True, capture_output=True, text=True, timeout=10
    )
