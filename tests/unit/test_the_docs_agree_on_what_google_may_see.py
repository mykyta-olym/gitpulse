"""Four files decide what a crawler sees of the documentation. They must agree.

They did not. Measured against the live site on 2026-09-08, of the 49 URLs the
docs sitemap submitted:

  * 20 answered `302` to `/dashboard/login` - every page of `ucitelia/`,
    `gitlab/`, `operatori/` and `bezpecnost/`, which need a session;
  * the Slovak half of the site - the DEFAULT language, another 49 pages - was
    in no sitemap at all, because Hugo wanted to write it to the same path as
    the sitemap index and the index won. The index then pointed at
    `/docs/sk/sitemap.xml`, which Caddy 301s back to the index: a loop;
  * `api/`, `changelog/`, `diplomovka/` and `vyvojari/` - public sections, the
    ones worth finding - were served `X-Robots-Tag: noindex` by nginx while
    being listed in that same sitemap, which Search Console reports as
    "Submitted URL marked noindex".

The rule now has one source: whether a reader needs a session. `docs_authz.py`
already knows, so everything else is checked against it here.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs-site"
NGINX = DOCS / "nginx/default.conf"
HUGO_CONFIG = DOCS / "config/_default/hugo.yaml"
SITEMAPS = (DOCS / "layouts/sitemapindex.xml", DOCS / "layouts/sitemap.xml")
MAIN = ROOT / "src/app/api/site.py"

#: Public sections that must stay in the index - the reason this site exists.
PUBLIC = ("api", "changelog", "diplomovka", "vyvojari", "studenti", "uvod", "pravne")


@pytest.fixture(scope="module")
def gated() -> set[str]:
    """The sections the application refuses without a session."""
    sys.path.insert(0, str(ROOT / "src"))
    from app.api.docs_authz import ADMIN_ONLY, STAFF_ONLY

    return {p.rstrip("/") for p in (*ADMIN_ONLY, *STAFF_ONLY)}


def test_hugo_keeps_the_gated_sections_out_of_the_sitemap(gated: set[str]) -> None:
    params = yaml.safe_load(HUGO_CONFIG.read_text(encoding="utf-8"))["params"]
    assert set(params["gatedSections"]) == gated, (
        "the sitemap's exclusion list and docs_authz.py disagree: a section "
        "added to one and not the other is either submitted and refused, or "
        "readable and invisible"
    )


@pytest.mark.parametrize("template", SITEMAPS, ids=lambda p: p.name)
def test_both_sitemaps_apply_the_exclusions(template: Path) -> None:
    src = template.read_text(encoding="utf-8")
    assert "gatedSections" in src, f"{template.name} lists gated sections"
    assert "noindexSections" in src, f"{template.name} lists generated listings"
    assert "AllTranslations" in src, (
        f"{template.name} drops the hreflang alternates, so the two languages "
        "read as duplicates of each other"
    )


def test_the_sitemap_index_was_replaced_by_a_real_listing() -> None:
    """The loop: an index whose only Slovak entry redirects back to the index."""
    src = (DOCS / "layouts/sitemapindex.xml").read_text(encoding="utf-8")
    assert "<urlset" in src, "still emitting a sitemapindex - the sk entry loops"
    assert "sitemapindex" not in src.split("*/", 1)[1], "the index element is back"


def test_nginx_no_longer_hides_the_public_sections() -> None:
    src = NGINX.read_text(encoding="utf-8")
    rule = next(ln for ln in src.splitlines() if "noindex" in ln and "~*" in ln)
    hidden = [name for name in PUBLIC if re.search(rf"\b{name}\b", rule)]
    assert not hidden, f"these public sections are served noindex by nginx: {hidden}"


def test_nginx_states_the_positive_case_too() -> None:
    """A page that says nothing leaves the decision to whatever else is guessing."""
    src = NGINX.read_text(encoding="utf-8")
    default = next(ln for ln in src.splitlines() if re.match(r"\s*default\s", ln))
    assert "index, follow" in default, "the default is still an empty header"


def test_robots_txt_disallows_what_a_crawler_cannot_reach(gated: set[str]) -> None:
    src = MAIN.read_text(encoding="utf-8")
    block = src.split("async def robots_txt", 1)[1].split("return Response", 1)[0]
    missing = [
        f"/docs/{prefix}{section}/"
        for section in sorted(gated)
        for prefix in ("", "en/")
        if f"Disallow: /docs/{prefix}{section}/" not in block
    ]
    assert not missing, f"robots.txt lets the crawler walk into a login redirect: {missing}"


def test_the_head_says_what_the_header_says() -> None:
    head = (DOCS / "themes/gitlab-docs/layouts/_partials/head.html").read_text("utf-8")
    assert 'name="robots"' in head
    assert "index, follow, max-image-preview:large" in head, (
        "the page itself no longer declares that it may be indexed"
    )
    assert 'name="zd-site-verification"' not in head, (
        "GitLab's Zendesk verification tokens are back; they verify their site, not this one"
    )
