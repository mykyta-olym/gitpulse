"""Attacks on the documentation gate, kept as tests.

Every case here is a way of naming a restricted page that a naive prefix match
does not recognise. All of them worked before 2026-08-20, measured against the
running site and against the code:

  - the search index. The gate refuses `/docs/operatori/`, but the index was
    built from the whole site and the gate waved anything under `/pagefind/`
    through as an asset. A signed-out browser driving Pagefind's own API got
    back the full text of 11 restricted pages - deployment runbook, rollback
    commands, monitoring ports, the hardening and threat-model pages. There are
    three indexes now, one per tier, and the two narrow ones are gated.

  - path normalisation. `/ucitelia/../operatori/` claimed the staff tier while
    the file served was the admin page; `/./operatori/` and `/OPERATORI/` and
    `/%6f%70...` matched no prefix at all and came out public. Caddy normalises
    before forwarding, which is what kept these theoretical - but an
    authorization decision must not rest on someone else's normaliser.

  - suffix confusion. `.json`, `.xml` and `.txt` were blanket assets, so any
    such file inside a gated section was served to anyone.
"""

from __future__ import annotations

import pytest

from app.api.docs_authz import _is_asset, _section_of, required_role

PUBLIC = None

# (uri, required role, what the attack is)
ATTACKS = [
    # the honest cases, which must keep working
    ("/uvod/", PUBLIC, "public page"),
    ("/en/uvod/ciele/", PUBLIC, "public page, English"),
    ("/ucitelia/", "staff", "staff page"),
    ("/docs/ucitelia/dashboard/", "staff", "staff page with the /docs prefix"),
    ("/operatori/", "admin", "admin page"),
    ("/en/bezpecnost/hrozby/", "admin", "admin page, English"),
    # traversal
    ("/ucitelia/../operatori/", "admin", "climb out of staff into admin"),
    ("/uvod/../operatori/", "admin", "climb out of public into admin"),
    ("/uvod/../../operatori/", "admin", "climb past the root"),
    ("/./operatori/", "admin", "current-directory segment"),
    ("/operatori/./nasadenie/", "admin", "dot segment inside the path"),
    ("//operatori/", "admin", "doubled separator"),
    ("/uvod/./../operatori/", "admin", "mixed dot segments"),
    # encoding
    ("/%6f%70%65%72%61%74%6f%72%69/", "admin", "percent-encoded section name"),
    ("/uvod/%2e%2e/operatori/", "admin", "percent-encoded traversal"),
    ("/uvod/%2E%2E/bezpecnost/", "admin", "percent-encoded traversal, uppercase"),
    ("/OPERATORI/", "admin", "uppercase section"),
    ("/Ucitelia/Dashboard/", "staff", "mixed case"),
    ("/uvod\\..\\operatori/", "admin", "backslash traversal"),
    # prefix confusion
    ("/docs/docs/operatori/", "admin", "doubled /docs prefix"),
    ("/en/en/operatori/", "admin", "doubled language prefix"),
    ("/docs/en/operatori/", "admin", "both prefixes"),
    # the search indexes
    ("/pagefind-staff/pagefind.js", "staff", "staff index"),
    ("/pagefind-staff/fragment/x.pf_fragment", "staff", "staff index fragment"),
    ("/pagefind-admin/fragment/x.pf_fragment", "admin", "admin index fragment"),
    ("/docs/pagefind-admin/index/a.pf_index", "admin", "admin index, /docs prefix"),
    (
        "/pagefind/../pagefind-admin/fragment/x.pf_fragment",
        "admin",
        "traverse from the public index into the admin one",
    ),
    # suffix confusion
    ("/operatori/runbook.json", "admin", "JSON inside a gated section"),
    ("/operatori/notes.txt", "admin", "text file inside a gated section"),
    ("/bezpecnost/index.xml", "admin", "feed inside a gated section"),
    ("/operatori/nasadenie/index.html", "admin", "explicit index.html"),
]


@pytest.mark.parametrize(("uri", "role", "attack"), ATTACKS, ids=[a[2] for a in ATTACKS])
def test_gate_sees_through_the_disguise(uri: str, role: str | None, attack: str) -> None:
    assert required_role(uri) == role, f"{attack}: {uri}"


@pytest.mark.parametrize(("uri", "role", "attack"), ATTACKS, ids=[a[2] for a in ATTACKS])
def test_a_gated_path_is_never_an_asset(uri: str, role: str | None, attack: str) -> None:
    """The asset bypass runs BEFORE the role check, so anything it lets through
    is served with no check at all."""
    if role is None:
        return
    assert not _is_asset(uri), f"{attack}: {uri} bypasses the gate as an asset"


def test_the_public_index_stays_readable_by_everyone() -> None:
    """The fix must not take search away from a signed-out reader: the public
    index holds only public pages, so it is an asset like any other build
    output."""
    for uri in (
        "/pagefind/pagefind.js",
        "/pagefind/pagefind-ui.css",
        "/pagefind/fragment/sk_1.pf_fragment",
        "/docs/pagefind/index/sk_1.pf_index",
    ):
        assert required_role(uri) is None, uri
        assert _is_asset(uri), uri


def test_normalisation_collapses_the_disguises() -> None:
    assert _section_of("/ucitelia/../operatori/") == "operatori/"
    assert _section_of("/%6f%70%65%72%61%74%6f%72%69/") == "operatori/"
    assert _section_of("/docs/en/OPERATORI/") == "operatori/"
    assert _section_of("/docs/en/") == ""


def test_the_tier_list_matches_the_index_builder() -> None:
    """The three indexes are built from a section list in a shell script. If the
    two lists drift, a page moves tier in one place and not the other - which is
    the same hole, reopened by accident."""
    import re
    from pathlib import Path

    from app.api.docs_authz import ADMIN_ONLY, PUBLIC_SECTIONS, STAFF_ONLY

    script = (
        Path(__file__).resolve().parents[2] / "docs-site/bin/build-search-indexes.sh"
    ).read_text(encoding="utf-8")

    def listed(name: str) -> set[str]:
        m = re.search(rf'^{name}="([^"]*)"', script, re.M)
        assert m, f"{name} not found in build-search-indexes.sh"
        return set(m.group(1).split())

    # `changelog` is public but is a single page rather than a section prefix,
    # so it is in the script's public list and not in PUBLIC_SECTIONS.
    assert listed("STAFF_SECTIONS") == {s.rstrip("/") for s in STAFF_ONLY}
    assert listed("ADMIN_SECTIONS") == {s.rstrip("/") for s in ADMIN_ONLY}
    assert {s.rstrip("/") for s in PUBLIC_SECTIONS} <= listed("PUBLIC_SECTIONS")
