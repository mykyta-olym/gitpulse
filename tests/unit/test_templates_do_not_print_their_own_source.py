"""A macro call written with one brace renders as text, not as a control.

Five call sites wrote `{ restore_actions(...) }` instead of `{{ ... }}`. Jinja
has no meaning for a single brace, so it passed the expression straight
through and the page printed its own source into a table cell:

    { restore_actions('project', project.id, icon_only=true,
      lock_scope='course:' ~ team.course_id ~ ' team:' ~ team.id ~ ...) }

It cannot fail a render or a syntax check - the template is valid, it just
says something different from what it means - so nothing caught it until a
reader saw the code where the restore button should have been.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

_TEMPLATES = Path(__file__).resolve().parents[2] / "src" / "app" / "templates"

#: `{ name(` at the start of a line: a call written as prose. The real forms
#: are `{{ name(...) }}` and `{% ... %}`, and neither matches.
_ONE_BRACE_CALL = re.compile(r"^\s*\{ *[a-zA-Z_][\w.]*\(")

#: `~` is Jinja's concatenation operator. Outside a `{{ }}` or `{% %}` it is
#: just a tilde in the page - the tail of the same mistake, on the line that
#: continues the call.
_STRAY_JINJA_OPERATOR = re.compile(r"^\s*[a-zA-Z_]\w*=['\"].*~.*['\"].*\) *\}\s*$")


def _html_templates() -> list[Path]:
    return sorted(_TEMPLATES.rglob("*.html"))


@pytest.mark.parametrize("path", _html_templates(), ids=lambda p: p.name)
def test_no_macro_call_is_written_with_one_brace(path: Path) -> None:
    offenders = [
        f"{path.name}:{n} {line.strip()[:70]}"
        for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1)
        if _ONE_BRACE_CALL.match(line) or _STRAY_JINJA_OPERATOR.match(line)
    ]
    assert not offenders, (
        f"this renders as text instead of calling the macro - it needs `{{{{ }}}}`: {offenders}"
    )
