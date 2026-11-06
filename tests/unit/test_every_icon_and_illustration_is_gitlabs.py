"""Every icon and illustration the app draws is GitLab's own, used as GitLab uses it.

The dashboard's "No courses in <term>" state drew a Pajamas calendar glyph inside
a grey rounded tile - a picture GitLab never draws: GlEmptyState leads with an
illustration. Alongside it the app
carried hand-drawn marks GitLab does not have: a stroked sort caret pair, a
dismiss cross that was not Pajamas `close`, a dropdown tick that was not
Pajamas `check`, CSS-border checkmarks and chevrons, Feather icons on the
offline and login pages, and text characters (check marks, crosses, triangles,
dots) standing in for icons.

What remains is copied from @gitlab/svgs 3.165.0 and @gitlab/ui 137.3.1; the
GitPulse logo and the loading tanuki are the app's own brand and stay.
"""

from __future__ import annotations

import hashlib
import html
import re
from pathlib import Path

from jinja2 import Environment, nodes

REPO = Path(__file__).resolve().parents[2]
TEMPLATES = REPO / "src/app/templates"
STATIC = TEMPLATES / "static"

# sha256 (first 16 hex) of each file with line endings normalised. The
# illustrations are byte copies of @gitlab/svgs dist/illustrations; the error
# art is dist/illustrations/error/error-*-lg.svg, with a viewBox added to the
# two that ship without one (404, 429) so the <img> scales on a phone instead
# of being cropped. 401 draws the 403 art: GitLab has no 401 page.
GITLAB_ART = {
    "components/illustrations/empty-access.svg": "4ffd05f4c8b1559b",
    "components/illustrations/empty-activity.svg": "8e592259c4a20bae",
    "components/illustrations/empty-ai-catalog.svg": "ac9823396850f629",
    "components/illustrations/empty-chart.svg": "5866464bf65b9577",
    "components/illustrations/empty-commit.svg": "3d909692128c5f66",
    "components/illustrations/empty-dashboard.svg": "a9f4952d987ad1b0",
    "components/illustrations/empty-issues.svg": "4a9d9f9fae410835",
    "components/illustrations/empty-merge-requests.svg": "ed2fc495e850f1ff",
    "components/illustrations/empty-projects.svg": "37ca8dc8abe738fc",
    "components/illustrations/empty-schedule.svg": "bdbc459974d825f8",
    "components/illustrations/empty-search.svg": "e1a55bfad6855c07",
    "components/illustrations/empty-service-desk.svg": "8538923a8a0f8da4",
    "components/illustrations/empty-subgroup.svg": "c6a4849edb544159",
    "components/illustrations/empty-todos-all-done.svg": "aada4fab06745b0d",
    "components/illustrations/empty-user.svg": "3bdb28723f2a26a5",
    "components/illustrations/empty-variables.svg": "d80b0b6f6cf1b48e",
    "components/illustrations/chart-bar-sm.svg": "8e6e6cfdf9677a29",
    "components/illustrations/search-sm.svg": "2a7f29ce1d7c6c17",
    "components/illustrations/status-fail-sm.svg": "039896fd74237ce1",
    "components/illustrations/status-nothing-sm.svg": "b2731062ef4fbcda",
    "components/illustrations/status-success-sm.svg": "64a3ad0146399857",
    "static/img/error-401.svg": "b028fca87060664a",
    "static/img/error-403.svg": "b028fca87060664a",
    "static/img/error-404.svg": "220294fe3e61eba0",
    "static/img/error-429.svg": "24bac994b2242aa4",
    "static/img/error-500.svg": "996d2c09516b004c",
    "static/img/error-502.svg": "0836513cc048f027",
    "static/img/error-503.svg": "f505155cd5baad19",
}

# check marks, crosses, multiplication sign, triangles, dots, circled slash
GLYPHS = "".join(
    map(
        chr,
        (
            0x2713,
            0x2714,
            0x2717,
            0x2715,
            0x2716,
            0xD7,
            0x25B2,
            0x25BC,
            0x25B6,
            0x25C0,
            0x25CF,
            0x25CB,
            0x2298,
        ),
    )
)


def _sources(*suffixes: str) -> list[Path]:
    skip = re.compile(r"\.min\.|bundle|[\\/]vendor[\\/]|i18n-catalog")
    return [
        p
        for p in TEMPLATES.rglob("*")
        if p.suffix in suffixes and not skip.search(str(p)) and "illustrations" not in p.parts
    ]


def test_the_art_is_gitlabs_unedited() -> None:
    on_disk = {
        p.relative_to(TEMPLATES).as_posix()
        for p in [
            *(TEMPLATES / "components/illustrations").glob("*.svg"),
            *(STATIC / "img").glob("error-*.svg"),
        ]
    }
    assert on_disk == set(GITLAB_ART), (
        "an illustration was added or removed without its GitLab source"
    )
    for rel, digest in GITLAB_ART.items():
        data = (TEMPLATES / rel).read_bytes().replace(b"\r\n", b"\n")
        assert hashlib.sha256(data).hexdigest()[:16] == digest, f"{rel} is no longer GitLab's file"


def test_an_empty_state_leads_with_an_illustration_never_an_icon() -> None:
    cards = (TEMPLATES / "components/cards.html").read_text(encoding="utf-8")
    macro = re.search(r"{% macro empty_state\((.*?)\) %}(.*?){% endmacro %}", cards, re.S)
    assert macro, "empty_state macro is gone"
    assert "icon" not in macro.group(1), "empty_state takes an icon again"
    assert "icon(" not in macro.group(2)

    for path in _sources(".html"):
        text = path.read_text(encoding="utf-8")
        for call in re.finditer(r"(?<!macro )empty_state\(", text):
            window = text[call.start() : call.start() + 800]
            name = re.search(r"illustration=(?:'([a-z0-9-]+)'|_empty\.illustration)", window)
            assert name, f"{path.name}: an empty_state without a GitLab illustration"
            if name.group(1):
                assert (TEMPLATES / f"components/illustrations/{name.group(1)}.svg").exists()

    for path in _sources(".html", ".js", ".css"):
        assert "empty-state-icon" not in path.read_text(encoding="utf-8"), (
            f"{path.name}: the icon tile is back"
        )


def test_every_empty_state_leads_with_a_gitlab_illustration() -> None:
    """The card-level empty states led with a GitLab illustration and the table,
    list and chart ones with nothing - "not everywhere are these icons in an
    empty state". Every one of them is GlEmptyState now: the page-sized ones
    through empty_state (md), the rest through one sm slot, the one the loading
    spinner takes."""
    tables = (TEMPLATES / "components/tables.html").read_text(encoding="utf-8")
    table_empty = re.search(r"{% macro table_empty\((.*?)\) %}(.*?){% endmacro %}", tables, re.S)
    assert table_empty
    assert "illustration='status-nothing-sm'" in table_empty.group(1)
    include = "{% include 'components/illustrations/' ~ illustration ~ '.svg' %}"
    assert include in table_empty.group(2)

    cards = (TEMPLATES / "components/cards.html").read_text(encoding="utf-8")
    block_empty = re.search(r"{% macro block_empty\((.*?)\) %}(.*?){% endmacro %}", cards, re.S)
    assert block_empty
    assert "illustration='status-nothing-sm'" in block_empty.group(1)
    assert include in block_empty.group(2)
    chart_empty = re.search(r"{% macro chart_empty\((.*?)\) %}(.*?){% endmacro %}", cards, re.S)
    assert chart_empty
    assert "block_empty(message, 'chart-bar-sm'" in chart_empty.group(2)

    helpers = (STATIC / "js/_parts/core/22-content-states.js").read_text(encoding="utf-8")
    body = re.search(r"function emptyStateHtml\((.*?)\) \{(.*?)\n\}", helpers, re.S)
    assert body
    assert body.group(1) == "message, illustration"
    assert "illustrationSlot(illustration || 'status-nothing-sm')" in body.group(2)
    error = re.search(r"function errorStateHtml\((.*?)\) \{(.*?)\n\}", helpers, re.S)
    assert error
    assert "illustrationSlot('status-fail-sm')" in error.group(2)
    assert "iconSvg" not in error.group(2)

    # The JS states read the same vendored files, from one <template>.
    base = (TEMPLATES / "base.html").read_text(encoding="utf-8")
    shelf = base.split('<template id="gpStateIllustrations">', 1)[1].split("</template>", 1)[0]
    for name in ("status-nothing-sm", "search-sm", "chart-bar-sm", "status-fail-sm"):
        assert f"'{name}'" in shelf, f"{name} is not on the shelf the JS reads"

    # No empty-state box without the slot, anywhere.
    for path in _sources(".html", ".js"):
        text = path.read_text(encoding="utf-8")
        for m in re.finditer(r"<div class=\"table-empty-state[^\"]*\">\s*(<[^>]*>)", text):
            assert "table-empty-icon" in m.group(1), f"{path.name}: an empty state without its art"
        # the hand-written grey lines they replaced
        for gone in ('gl-empty"', "user-info-empty", "gl-activity-empty", '"rcm-empty'):
            assert gone not in text, f"{path.name}: {gone} is an empty state of its own again"


def test_the_sort_mark_is_gltables_text_arrow() -> None:
    tables = (TEMPLATES / "components/tables.html").read_text(encoding="utf-8")
    header = re.search(r"{% macro sortable_header.*?{% endmacro %}", tables, re.S)
    assert header
    assert "<svg" not in header.group(0)
    assert "<svg" not in (STATIC / "js/sortable-table.js").read_text(encoding="utf-8")
    css = (STATIC / "css/tables.css").read_text(encoding="utf-8")
    assert ".sort-arrow::before { content: '\\2191'; }" in css


def _decoded(text: str) -> str:
    """The characters a string will show: `&#10003;` and `\\u2713` count too -
    both slipped past the first version of this check."""
    text = re.sub(r"\\u([0-9a-fA-F]{4})", lambda m: chr(int(m.group(1), 16)), text)
    return html.unescape(text)


# The one sanctioned use: a toast's repeat counter reads "x3" as a count.
COUNT_SIGN = ("09-toasts.js", "'\\u00d7'")


def test_no_text_character_stands_in_for_an_icon() -> None:
    # plus the arrows and the warning sign drawn as "trend" / "careful" marks
    glyphs = GLYPHS + "".join(map(chr, (0x2191, 0x2193, 0x26A0)))
    strings = re.compile(r"""(['"`])(?:(?!\1)[^\\\n]|\\.)*\1""")
    for path in _sources(".html", ".js"):
        text = path.read_text(encoding="utf-8")
        if path.suffix == ".js":
            text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
            text = re.sub(r"^\s*//.*$", "", text, flags=re.M)
            chunks = [m.group(0) for m in strings.finditer(text)]
        else:
            chunks = [re.sub(r"{#.*?#}|<!--.*?-->", "", text, flags=re.S)]
        for chunk in chunks:
            if (path.name, chunk) == COUNT_SIGN:
                continue
            found = [g for g in glyphs if g in _decoded(chunk)]
            assert not found, f"{path.name}: {found} drawn as an icon in {chunk[:60]}"
    for path in _sources(".css"):
        assert not re.search(r"content:\s*'\\27(13|17)", path.read_text(encoding="utf-8")), (
            path.name
        )


def test_the_empty_state_macros_are_called_with_their_own_arguments() -> None:
    """chart_empty lost its icon argument and one caller still passed one
    positionally - course Analytics answered 500 until it was caught."""
    env = Environment(autoescape=True)
    cards = env.parse((TEMPLATES / "components/cards.html").read_text(encoding="utf-8"))
    tables = env.parse((TEMPLATES / "components/tables.html").read_text(encoding="utf-8"))
    sigs = {
        m.name: [a.name for a in m.args]
        for ast in (cards, tables)
        for m in ast.find_all(nodes.Macro)
        if m.name in ("empty_state", "block_empty", "chart_empty", "table_empty")
    }
    assert set(sigs) == {"empty_state", "block_empty", "chart_empty", "table_empty"}
    for path in _sources(".html"):
        for call in env.parse(path.read_text(encoding="utf-8")).find_all(nodes.Call):
            name = getattr(call.node, "name", None)
            if name not in sigs:
                continue
            assert len(call.args) <= len(sigs[name]), f"{path.name}:{call.lineno} {name}"
            for kw in call.kwargs:
                assert kw.key in sigs[name], f"{path.name}:{call.lineno} {name}({kw.key}=)"
