"""A table row's actions are icon buttons - one shape, one size, one look per action.

Reported on an archived course: the same three actions were 34px, 24px and 26px
wide in two tables. An audit of every table found the rest: a filled "View"
among 24px squares in the groups table, a "View" with words in the tickets
and project members tables, worded "Details" / "Resurrect" / "Cancel" buttons
drawn by JS, a 34px exclusion toggle at 40% opacity (a phone never hovers it to
full strength), a grey trash where every other delete is red, and a group row
added by JS with 14px glyphs and a filled delete.

So: `btn_icon_only` / `btn_link_icon_only` (or `btn-icon-only` in JS), 24px
on a desktop and 36px on a touch screen; neutral actions secondary, a delete
the red trash, "look at it" the eye.
"""

from __future__ import annotations

import re
from pathlib import Path

TEMPLATES = Path(__file__).resolve().parents[2] / "src/app/templates"
JS = TEMPLATES / "static/js"
_WORDED = re.compile(r"\{\{\s*(btn|btn_icon|btn_link|btn_link_icon)\(")
_RAW = re.compile(r"<(?:button|a)\b[^>]*class=\"((?:[^\"]*\s)?btn(?:\s[^\"]*)?)\"")


def test_no_worded_button_in_a_table_cell() -> None:
    offenders = []
    for path in TEMPLATES.rglob("*.html"):
        text = path.read_text(encoding="utf-8")
        for cell in re.finditer(r"<td\b.*?</td>", text, re.S):
            block = cell.group(0)
            if "table-empty-state" in block:  # an empty table's call to action
                continue
            if 'colspan="5"' in block and "'action': 'expandTreeRow'" in block:
                # This loads more project names in the content columns. It is
                # not a row action; the Actions cell after it remains empty.
                continue
            line = text.count("\n", 0, cell.start()) + 1
            where = f"{path.relative_to(TEMPLATES)}:{line}"
            offenders += [f"{where} {m.group(1)}(" for m in _WORDED.finditer(block)]
            offenders += [
                f"{where} class={m.group(1)!r}"
                for m in _RAW.finditer(block)
                if "btn-icon-only" not in m.group(1)
            ]
            for call in re.finditer(r"restore_actions\((.*?)\)\s*\}\}", block, re.S):
                if "icon_only=true" not in call.group(1):
                    offenders.append(f"{where} restore_actions without icon_only")
    assert not offenders, "worded buttons in table rows: " + "; ".join(offenders)


def test_rows_drawn_by_js_use_the_same_buttons() -> None:
    teams = (JS / "_parts/course-detail/10-teams-crud.js").read_text(encoding="utf-8")
    assert "btn btn-icon btn-" not in teams, "a JS-added group row has padded icon boxes again"
    assert 'class="btn btn-primary btn-sm">' not in teams, "a JS-added group row has a filled View"
    assert teams.count('class="btn btn-icon-only btn-') == 4

    events = (JS / "pages/admin-events.js").read_text(encoding="utf-8")
    assert "btn btn-icon-only btn-secondary btn-sm dlq-view-detail" in events
    assert "btn btn-icon-only btn-success btn-sm resurrect-btn" in events

    jobs = (TEMPLATES / "partials/admin/_system_job_rows.html").read_text(encoding="utf-8")
    assert "btn_icon_only('x-circle', variant='danger', size='sm', class='btn-cancel-job'" in jobs

    weekly = (JS / "_parts/course-settings/80-weekly-deadlines.js").read_text(encoding="utf-8")
    assert "'deleteWeek', 'trash', i, t('Delete week'), t('Delete this week'), 'danger')" in weekly


def test_the_scoring_toggle_is_a_plain_row_action() -> None:
    """Full strength at rest, and not an eye: the eye is View, beside it."""
    css = (TEMPLATES / "static/css/member-filters.css").read_text(encoding="utf-8")
    toggle = css.split(".btn-toggle-exclusion {", 1)[1].split("}", 1)[0]
    assert "opacity" not in toggle, "the toggle rests faded again - a phone never hovers it"
    for rel in ("partials/project/_members_table.html", "partials/team/_detail_content.html"):
        page = (TEMPLATES / rel).read_text(encoding="utf-8")
        assert "btn btn-icon-only btn-sm btn-secondary" in page, rel
        assert "icon('user-plus' if is_excluded else 'user-minus', size='sm')" in page, rel
    js = (JS / "member-exclusion.js").read_text(encoding="utf-8")
    assert "excluded ? 'user-plus' : 'user-minus'" in js
    assert "GP.iconSvg(name, 'sm')" in js
