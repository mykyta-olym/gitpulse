"""The documentation is gated by role, and the map is the contract.

The docs are a static site behind their own nginx, so they cannot know who is
reading. Caddy asks `/internal/docs-authz` first, forwarding the original path
in `X-Forwarded-Uri`. These tests pin the decision table rather than the wiring:
if a section moves between tiers, that is a deliberate change and this fails.
"""

from __future__ import annotations

import pytest

from app.api.docs_authz import required_role

PUBLIC = [
    "/docs/",
    "/docs/uvod/ciele/",
    "/docs/studenti/faq/",
    "/docs/api/",
    "/docs/vyvojari/prostredie/",
    "/docs/diplomovka/navrh/",
    "/docs/pravne/podmienky/",
    "/docs/en/studenti/",
]
STAFF = [
    "/docs/ucitelia/",
    "/docs/ucitelia/dashboard/",
    "/docs/gitlab/webhooky/",
    "/docs/en/ucitelia/",
    "/docs/en/gitlab/cicd/",
]
ADMIN = [
    "/docs/operatori/",
    "/docs/operatori/nasadenie/",
    "/docs/bezpecnost/hardening/",
    "/docs/en/operatori/monitoring/",
    "/docs/en/bezpecnost/",
]


@pytest.mark.parametrize("uri", PUBLIC)
def test_public_sections_need_no_session(uri: str) -> None:
    assert required_role(uri) is None, f"{uri} should be readable by anyone"


@pytest.mark.parametrize("uri", STAFF)
def test_teaching_sections_require_staff(uri: str) -> None:
    assert required_role(uri) == "staff", f"{uri} should require a teacher or admin"


@pytest.mark.parametrize("uri", ADMIN)
def test_operations_sections_require_admin(uri: str) -> None:
    assert required_role(uri) == "admin", f"{uri} should require an admin"


def test_language_prefix_does_not_change_the_tier() -> None:
    """A page must not become public by being read in the other language."""
    for sk, en in [
        ("/docs/operatori/", "/docs/en/operatori/"),
        ("/docs/ucitelia/", "/docs/en/ucitelia/"),
    ]:
        assert required_role(sk) == required_role(en)


def test_unknown_sections_are_public() -> None:
    """A new page is readable rather than unreachable; gated prefixes are explicit."""
    assert required_role("/docs/nieco-nove/") is None


@pytest.fixture(scope="module")
def client():
    """A client for the endpoint the documentation pages call.

    Built here rather than from a shared fixture: this suite only needs the
    application object, and the host header has to be one the trusted-host
    middleware accepts.
    """
    from fastapi.testclient import TestClient

    from app.config import get_settings
    from app.main import create_app

    # The trusted-host middleware rejects anything not in ALLOWED_HOSTS, and an
    # empty list means "allow all". Taking the host from settings keeps this
    # working under whatever the environment configures.
    hosts = get_settings().allowed_hosts
    host = next((h for h in hosts if "*" not in h), None) if hosts else "testserver"
    return TestClient(create_app(), base_url=f"http://{host or 'testserver'}")


class TestReaderRoleEndpoint:
    """What `/internal/docs-role` tells a reader they may open.

    The documentation is static HTML and cannot see the role header Caddy passes
    it, so a page asks this instead. The answer must be honest for anonymous
    readers too - that is the case a signed-out student actually hits.
    """

    def test_anonymous_gets_only_public_sections(self, client) -> None:
        body = client.get("/internal/docs-role").json()
        assert body["role"] == "anonymous"
        assert "studenti" in body["sections"]
        assert "ucitelia" not in body["sections"], "the teacher guide is not public"
        assert "operatori" not in body["sections"], "operations is not public"

    def test_offered_sections_are_actually_openable(self, client) -> None:
        """Whatever this endpoint offers must not be refused by the gate."""
        body = client.get("/internal/docs-role").json()
        for section in body["sections"]:
            assert required_role(f"/docs/{section}/") is None, (
                f"{section} is offered to an anonymous reader but the gate would refuse it"
            )


class TestRefusalIsActionable:
    """A refused reader must be given something they can do next.

    The case this exists for: a teacher follows a search-engine link to the
    teacher's guide, has never signed in here, and a bare 401 tells them nothing.
    """

    def test_no_session_redirects_to_sign_in_and_back(self, client) -> None:
        r = client.get(
            "/internal/docs-authz",
            headers={"X-Forwarded-Uri": "/ucitelia/"},
            follow_redirects=False,
        )
        assert r.status_code == 302
        location = r.headers["location"]
        assert location.startswith("/dashboard/login?next=")
        assert "/docs/ucitelia/" in location, (
            "must return to the documentation page, not to the path Caddy stripped"
        )

    def test_the_return_path_keeps_the_docs_prefix(self) -> None:
        """`handle_path` strips /docs before this endpoint sees the URI."""
        from app.api.docs_authz import _public_path

        assert _public_path("/ucitelia/") == "/docs/ucitelia/"
        assert _public_path("/en/gitlab/") == "/docs/en/gitlab/"
        assert _public_path("/docs/operatori/") == "/docs/operatori/", "never doubled"


class TestRedirectCannotLoop:
    """A refusal may send the reader to sign in once, never twice.

    When this endpoint looked for the wrong cookie name, a signed-in admin was
    refused, redirected to sign in, arrived back still looking signed out, and
    bounced until the rate limiter answered 429. The marker makes that
    structurally impossible: whatever the cause, the second pass explains
    instead of redirecting.
    """

    def test_first_refusal_redirects(self, client) -> None:
        r = client.get(
            "/internal/docs-authz",
            headers={"X-Forwarded-Uri": "/ucitelia/"},
            follow_redirects=False,
        )
        assert r.status_code == 302
        assert "signin=1" in r.headers["location"], "the return trip must be marked"

    def test_second_refusal_explains_instead_of_redirecting(self, client) -> None:
        r = client.get(
            "/internal/docs-authz",
            headers={"X-Forwarded-Uri": "/ucitelia/?signin=1"},
            follow_redirects=False,
        )
        assert r.status_code == 401
        assert "Prihlásiť sa" in r.text, "must offer the sign-in link by hand"
        assert "location" not in {k.lower() for k in r.headers}, "no second redirect"


class TestGatePagesSpeakTheReadersLanguage:
    """A refusal explains itself in the language the reader was reading.

    Both gate pages were Slovak-only, so an English reader who opened
    `/docs/en/ucitelia/` was stopped by a Slovak page. The language is in the
    URI - `/en/` for English, nothing for the default - so the gate can tell.
    """

    def test_language_is_read_off_the_forwarded_uri(self) -> None:
        from app.api.docs_authz import _lang_of

        assert _lang_of("/ucitelia/") == "sk"
        assert _lang_of("/docs/ucitelia/") == "sk"
        assert _lang_of("/en/ucitelia/") == "en"
        assert _lang_of("/docs/en/operatori/") == "en"
        # a section that merely STARTS with the letters is not the language
        assert _lang_of("/endpoints/") == "sk"

    def test_sign_in_page_is_english_for_an_english_uri(self, client) -> None:
        r = client.get(
            "/internal/docs-authz",
            headers={"X-Forwarded-Uri": "/en/ucitelia/?signin=1"},
            follow_redirects=False,
        )
        assert r.status_code == 401
        assert '<html lang="en"' in r.text
        assert "Sign in" in r.text
        assert "Prihlásiť sa" not in r.text

    def test_refusal_page_is_translated(self) -> None:
        from app.api.docs_authz import _refusal_page

        sk = _refusal_page(needed="admin", role="teacher", path="/docs/operatori/", lang="sk")
        en = _refusal_page(needed="admin", role="teacher", path="/docs/en/operatori/", lang="en")
        assert '<html lang="sk"' in sk
        assert "vyhradená" in sk
        assert '<html lang="en"' in en
        assert "restricted" in en
        # and each sends the reader home in their own language
        assert 'href="/docs/"' in sk
        assert 'href="/docs/en/"' in en
