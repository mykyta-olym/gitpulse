"""A radio group marks a form dirty when its selection changes.

`_snapshotFormFields` keyed every control by `name`, and for radios it stored
`el.checked`. A radio GROUP shares one name, so the snapshot ended up holding
whichever button came LAST in the DOM - normally an unchecked one, and still
unchecked after the reader picked a different option. The value never changed,
so `_isFormDirtyGuard` reported "clean" and the Save button never armed.

That is every radio group on Preferences: the accent theme, the layout width,
the syntax scheme and the time format. Picking any of them looked like no edit
had been made at all, which is what "the settings do nothing" looked like from
the outside.

The behaviour is exercised for real - the two functions are lifted out of the
bundle and run in Node against a stub group - because a source-text assertion
would have passed just as happily on the broken version.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import textwrap
from pathlib import Path

import pytest

from tests.js_progress_runtime import top_progress_runtime

REPO = Path(__file__).resolve().parents[2]
MODAL_NAV = REPO / "src/app/templates/static/js/_parts/core/14-save-guard.js"

pytestmark = pytest.mark.skipif(shutil.which("node") is None, reason="node is not installed")


def _run(script: str) -> dict[str, object]:
    # Written to a file rather than passed with `node -e`: the inline form on
    # Windows trips over the escaped path and is parsed as TypeScript.
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "harness.js"
        path.write_text(script, encoding="utf-8")
        # Same convention as test_bundle_runtime, which also shells out to node.
        # That one LOADS whole bundles against a stub DOM; this one exercises a
        # single function's return value, so it needs its own tiny harness.
        result = subprocess.run(  # noqa: S603
            ["node", str(path)],  # noqa: S607
            capture_output=True,
            text=True,
            timeout=60,
            cwd=str(REPO),
        )
    assert result.returncode == 0, result.stderr[:400]
    return json.loads(result.stdout.strip().splitlines()[-1])


HARNESS = textwrap.dedent("""
    const fs = require('fs');
    const src = fs.readFileSync(%s, 'utf8');
    const grab = (name) => {
      const i = src.indexOf('function ' + name + '(');
      let d = 0, started = false;
      for (let j = i; j < src.length; j++) {
        if (src[j] === '{') { d++; started = true; }
        else if (src[j] === '}') { d--; if (started && d === 0) return src.slice(i, j + 1); }
      }
      throw new Error('not found: ' + name);
    };
    eval(grab('_snapshotFormFields') + ';' + grab('_isFormDirtyGuard'));

    const radios = ['default', 'indigo', 'gray'].map(v => ({
      type: 'radio', name: 'accent_theme', value: v,
      checked: v === 'default', closest: () => null, form: null, hasAttribute: () => false,
    }));
    const container = { tagName: 'DIV', querySelectorAll: () => radios };

    const before = _snapshotFormFields(container);
    const cleanAtRest = _isFormDirtyGuard(container, before);
    radios[0].checked = false;
    radios[1].checked = true;
    const after = _snapshotFormFields(container);
    const dirtyAfterPick = _isFormDirtyGuard(container, before);
    console.log(JSON.stringify({ before, after, cleanAtRest, dirtyAfterPick }));
""")


def test_changing_the_selected_radio_arms_the_save_button() -> None:
    out = _run(HARNESS % json.dumps(str(MODAL_NAV)))
    assert out["before"] == {"accent_theme": "default"}, (
        f"the snapshot should hold the SELECTED VALUE, not {out['before']}"
    )
    assert out["cleanAtRest"] is False, "an untouched form must not look dirty"
    assert out["after"] == {"accent_theme": "indigo"}
    assert out["dirtyAfterPick"] is True, (
        "picking a different option in a radio group left the form looking clean, "
        "so the Save button never armed"
    )


def test_every_radio_group_on_preferences_is_covered_by_this() -> None:
    """Names the groups the bug affected, so removing one is a deliberate act."""
    page = (REPO / "src/app/templates/preferences.html").read_text(encoding="utf-8")
    for group in ("accent_theme", "layout_width", "syntax_theme", "time_format"):
        assert f"radio('{group}'" in page, f"{group} is no longer a radio group on the page"


def test_checkboxes_sharing_a_form_name_keep_independent_state() -> None:
    script = HARNESS.replace(
        "type: 'radio', name: 'accent_theme'", "type: 'checkbox', name: 'enabled_checks'"
    )
    script = script.replace("radios[0].checked = false;", "")
    result = _run(script % json.dumps(str(MODAL_NAV)))
    assert result["cleanAtRest"] is False
    assert result["dirtyAfterPick"] is True
    assert len(result["before"]) == 3


def test_global_post_fallback_does_not_race_the_pages_submit_handler() -> None:
    source = REPO / "src/app/templates/static/js/_parts/core/43-htmx-requests.js"
    script = """
      const fs = require('fs');
      let submit, capture, calls = 0;
      const button = { disabled: false, dataset: {}, classList: { contains: () => false },
        setAttribute() {} };
      const form = { tagName: 'FORM', dataset: {}, method: 'POST', action: '/save',
        hasAttribute() { return false; }, querySelector() { return button; } };
      global.document = { body: { addEventListener() {} },
        addEventListener(type, fn, phase) {
          if (type === 'submit') { submit = fn; capture = !!phase; }
        } };
      global.FormData = class {};
      global.fetch = () => { calls++; return new Promise(() => {}); };
      const _BUSY_DELAY_MS = 180;
      eval(fs.readFileSync(%s, 'utf8') + '\\nGP.setButtonLoading = setButtonLoading;');
      eval(fs.readFileSync(%s, 'utf8'));
      submit({ target: form, defaultPrevented: true });
      const enhancedRequests = calls;
      submit({ target: form, defaultPrevented: false, preventDefault() {} });
      submit({ target: form, defaultPrevented: false, preventDefault() {} });
      clearTimeout(button._loadingArmed);
      console.log(JSON.stringify({ capture, enhancedRequests, nativeRequests: calls }));
    """
    buttons = source.with_name("21-buttons.js")
    result = _run(
        top_progress_runtime() + script % (json.dumps(str(buttons)), json.dumps(str(source)))
    )
    assert result == {"capture": False, "enhancedRequests": 0, "nativeRequests": 1}
