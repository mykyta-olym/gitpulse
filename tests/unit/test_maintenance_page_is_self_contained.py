"""The outage page must render when the application cannot serve anything.

During a redeploy the api container is briefly gone. `reverse_proxy` then
produces a 502/503 with an EMPTY body and the browser draws its own "This page
isn't working", which is what a reader actually saw. Caddy now answers with our
own page instead.

That page is served precisely when /static is unreachable - static files come
from the application, not from Caddy - so it may not link a stylesheet, a
script or an image. Everything it needs is inlined. These checks exist because
that constraint is invisible while the app is up: a link added here would look
perfectly fine in every test and only break during the outage it exists for.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[2]
_PAGE = _REPO / "deploy" / "errors" / "maintenance.html"
_CADDYFILE = _REPO / "Caddyfile"
_COMPOSE = _REPO / "docker-compose.yml"


@pytest.fixture(scope="module")
def page_html() -> str:
    assert _PAGE.is_file(), f"{_PAGE} is missing - Caddy has nothing to serve"
    return _PAGE.read_text(encoding="utf-8")


# Attributes that make the browser FETCH something. Plain `href` on an <a> is
# a link the reader may click once the app is back, which is fine; a stylesheet
# href or any src is a resource the page needs in order to render, which is not.
_FETCHING = (
    re.compile(r"<link\b[^>]*\bhref\s*=", re.IGNORECASE),
    re.compile(r"<script\b[^>]*\bsrc\s*=", re.IGNORECASE),
    re.compile(r"<img\b[^>]*\bsrc\s*=", re.IGNORECASE),
    re.compile(r"\burl\(\s*['\"]?(?!data:)", re.IGNORECASE),
    re.compile(r"@import\b", re.IGNORECASE),
)


def test_the_outage_page_fetches_nothing(page_html: str) -> None:
    offenders = [p.pattern for p in _FETCHING if p.search(page_html)]
    assert not offenders, (
        "the outage page loads an external resource, which cannot arrive while "
        f"the app is down: {offenders}"
    )


def test_the_outage_page_carries_its_own_illustration(page_html: str) -> None:
    """Inlined, not linked - the same 5xx artwork the app's error pages use."""
    assert "<svg" in page_html, "the outage page has no inlined illustration"


def test_the_outage_page_recovers_on_its_own(page_html: str) -> None:
    """A reader left on this page should not have to keep pressing reload."""
    assert "/health/ready" in page_html, "the outage page never re-checks health"
    assert "location.reload" in page_html, "the outage page never comes back"


def test_caddy_serves_the_outage_page_when_the_app_is_unreachable() -> None:
    caddy = _CADDYFILE.read_text(encoding="utf-8")
    assert "handle_errors" in caddy, "Caddy still returns an empty-bodied 502"
    assert "/srv/errors" in caddy, "handle_errors does not point at the page"
    assert "maintenance.html" in caddy, "handle_errors serves something else"


def test_the_outage_page_keeps_the_error_status() -> None:
    """Answering 200 would tell monitoring and crawlers the site is healthy."""
    caddy = _CADDYFILE.read_text(encoding="utf-8")
    assert "status {err.status_code}" in caddy, (
        "the outage page is served with the file_server's default 200 - an "
        "outage would be indistinguishable from a healthy page"
    )


def test_caddy_waits_out_a_container_swap_before_giving_up() -> None:
    """The outage page is the fallback, not the first response.

    A redeploy stops the api container and starts the new one. Without a retry
    window every request in that gap failed instantly, so a reader who happened
    to click during a deploy saw an error for something that resolved itself a
    few seconds later. Holding the request turns that into a slow page load.
    """
    caddy = _CADDYFILE.read_text(encoding="utf-8")
    assert "lb_try_duration" in caddy, (
        "requests during a container swap fail immediately instead of waiting"
    )


def test_the_deploy_reloads_caddy_rather_than_recreating_it() -> None:
    """Keep Caddy running so it can serve the maintenance page during deployment."""
    deploy = (_REPO / "redeploy.py").read_text(encoding="utf-8")
    assert "--force-recreate caddy" not in deploy, (
        "the deploy restarts the proxy that serves the outage page"
    )
    assert "caddy reload" in deploy, "the deploy never applies Caddyfile changes"


def test_compose_mounts_the_outage_page_into_caddy() -> None:
    compose = _COMPOSE.read_text(encoding="utf-8")
    assert "./deploy/errors:/srv/errors" in compose, (
        "the Caddy container has no /srv/errors, so handle_errors would 404"
    )
