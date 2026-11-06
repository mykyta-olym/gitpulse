"""A role is the same colour wherever it is drawn.

The colour for a role is written down in four places - the two Jinja macros in
``components/badges.html`` that render it server-side, and two JavaScript maps
that redraw the same roles into a live table and into the User Info dialog. Each
carried a comment saying it must stay in sync with the others, and each had
drifted anyway:

  - ``CROLE_BADGE`` drew a course owner ``warning`` and a course teacher
    ``purple``, where the server draws them ``teal`` and ``info``. The same
    person's course role was orange in the dialog and teal on the page behind
    it.
  - ``ROLE_BADGE_MAP`` in the users table had no ``mentor`` at all, so a mentor
    was grey there and teal in the dialog opened from that very row.

The account role is drawn in JS by ONE helper now, ``GP.roleBadgeHtml`` in core -
the users table, the User Info dialog and the search palette all call it (the
palette had a third copy, ``gl-search-badge--*``, that painted every student
green). The client maps are allowed to know roles the server macro does not
(``mentor`` is a course-level idea), but where they overlap they must agree.
"""

from __future__ import annotations

import re
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_BADGES = _ROOT / "src/app/templates/components/badges.html"
_JS = _ROOT / "src/app/templates/static/js"
_CORE_BADGES = _JS / "_parts/core/22-content-states.js"
_USER_INFO = _JS / "user-info-modal.js"
_ADMIN_USERS = _JS / "pages/admin-users.js"
_PALETTE = _JS / "search-palette.js"

# 'admin': (t('Admin'), 'warning') - or an untranslated ('TA', 'info')
_JINJA_ENTRY = re.compile(r"'([a-z_]+)':\s*\((?:t\()?'[^']*'\)?,\s*'([a-z_]+)'\)")
# admin: 'warning'
_JS_ENTRY = re.compile(r"([a-z_]+):\s*'([a-z_]+)'")


def _jinja_map(macro: str) -> dict[str, str]:
    src = _BADGES.read_text(encoding="utf-8")
    body = src.split(f"macro {macro}(", 1)[1].split("endmacro", 1)[0]
    return dict(_JINJA_ENTRY.findall(body))


def _js_map(path: Path, name: str) -> dict[str, str]:
    line = next(
        ln for ln in path.read_text(encoding="utf-8").splitlines() if f"const {name} = {{" in ln
    )
    return dict(_JS_ENTRY.findall(line.split("{", 1)[1]))


def test_the_maps_were_all_found() -> None:
    """Every assertion below is vacuous if a map silently parses to nothing."""
    for label, mapping in (
        ("role_badge", _jinja_map("role_badge")),
        ("course_role_badge", _jinja_map("course_role_badge")),
        ("ROLE_BADGE_VARIANTS", _js_map(_CORE_BADGES, "ROLE_BADGE_VARIANTS")),
        ("CROLE_BADGE", _js_map(_USER_INFO, "CROLE_BADGE")),
    ):
        assert mapping, f"{label} parsed to an empty map"


def test_global_role_colours_agree_with_the_server() -> None:
    server = _jinja_map("role_badge")
    for label, client in (
        ("core ROLE_BADGE_VARIANTS", _js_map(_CORE_BADGES, "ROLE_BADGE_VARIANTS")),
    ):
        for role, variant in server.items():
            assert client.get(role) == variant, (
                f"{label} draws {role!r} as {client.get(role)!r}, "
                f"badges.html role_badge draws it {variant!r}"
            )


def test_course_role_colours_agree_with_the_server() -> None:
    server = _jinja_map("course_role_badge")
    client = _js_map(_USER_INFO, "CROLE_BADGE")
    for role, variant in server.items():
        assert client.get(role) == variant, (
            f"CROLE_BADGE draws course role {role!r} as {client.get(role)!r}, "
            f"badges.html course_role_badge draws it {variant!r}"
        )


def test_every_client_account_role_badge_is_the_core_one() -> None:
    """A row repainted in place, the dialog that opens from it and a search
    result draw the same badge because they call the same helper - not because
    three maps happen to agree today."""
    for path in (_USER_INFO, _ADMIN_USERS, _PALETTE):
        src = path.read_text(encoding="utf-8")
        assert "GP.roleBadgeHtml(" in src, f"{path.name} draws the role badge itself"
        for own_map in ("ROLE_BADGE_MAP", "const ROLE_BADGE "):
            assert own_map not in src, f"{path.name} keeps its own account-role colour map"


def test_access_level_is_not_confused_with_a_course_role() -> None:
    """GitLab's access level and the course role share only the word "owner".
    Copying one into the other is how CROLE_BADGE drifted in the first place."""
    access = _js_map(_USER_INFO, "ACCESS_BADGE")
    crole = _js_map(_USER_INFO, "CROLE_BADGE")
    assert access["owner"] != crole["owner"], (
        "a GitLab access-level owner and a course owner are different things "
        "and are drawn differently on the server"
    )
