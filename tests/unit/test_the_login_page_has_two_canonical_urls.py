"""The login page is two pages to a search engine, not three.

Search Console reported "Duplicate, Google chose a different canonical than
the user" for the login page: the bare `/dashboard/login` and
`/dashboard/login?lang=sk` were both submitted, both canonical for
themselves, and both Slovak - Googlebot sends no Accept-Language - so Google
merged the pair and picked the canonical itself.

The contract now: the bare URL is the Slovak page and the x-default,
`?lang=sk` is the same page and canonicalises to it, `?lang=en` is the
English page and canonical for itself. Every hreflang target is one of the
two canonical URLs, and the sitemap submits those two and nothing else.
"""

import re

from fastapi.testclient import TestClient

BASE = "https://gitpulse.kpi.fei.tuke.sk"


def _client(monkeypatch) -> TestClient:
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+asyncpg://gitpulse:testpassword@localhost:5432/gitpulse_test",
    )
    monkeypatch.setenv("SECRET_KEY", "test-secret-key-minimum-sixteen-chars")
    monkeypatch.setenv("TEACHER_API_TOKEN", "test-token-12345678")
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("APP_BASE_URL", BASE)
    monkeypatch.setenv("ALLOWED_HOSTS", '["testserver","localhost","127.0.0.1"]')

    from app import config
    from app.main import create_app

    config.get_settings.cache_clear()
    return TestClient(create_app())


def _canonical(html: str) -> str:
    m = re.search(r'<link rel="canonical" href="([^"]+)"', html)
    assert m, "the login page lost its canonical"
    return m.group(1)


def _hreflangs(html: str) -> dict[str, str]:
    return dict(re.findall(r'<link rel="alternate" hreflang="([^"]+)" href="([^"]+)"', html))


def test_the_sitemap_submits_the_two_canonical_login_urls_only(monkeypatch) -> None:
    client = _client(monkeypatch)

    locs = re.findall(r"<loc>([^<]+)</loc>", client.get("/sitemap.xml").text)

    assert locs == [f"{BASE}/dashboard/login", f"{BASE}/dashboard/login?lang=en"]


def test_the_bare_login_url_is_the_slovak_page_and_the_x_default(monkeypatch) -> None:
    client = _client(monkeypatch)

    html = client.get("/dashboard/login").text

    assert _canonical(html) == f"{BASE}/dashboard/login"
    assert _hreflangs(html) == {
        "sk": f"{BASE}/dashboard/login",
        "en": f"{BASE}/dashboard/login?lang=en",
        "x-default": f"{BASE}/dashboard/login",
    }


def test_lang_sk_is_the_same_page_and_says_so(monkeypatch) -> None:
    client = _client(monkeypatch)

    html = client.get("/dashboard/login?lang=sk").text

    assert _canonical(html) == f"{BASE}/dashboard/login"


def test_lang_en_is_the_english_page_and_canonical_for_itself(monkeypatch) -> None:
    client = _client(monkeypatch)

    html = client.get("/dashboard/login?lang=en").text

    assert _canonical(html) == f"{BASE}/dashboard/login?lang=en"


def test_every_hreflang_target_is_a_canonical_url(monkeypatch) -> None:
    """The rule Google states: an alternate that disclaims itself breaks the
    cluster. So every URL the cluster names must be canonical for itself."""
    client = _client(monkeypatch)

    targets = set(_hreflangs(client.get("/dashboard/login").text).values())
    for url in targets:
        path = url.removeprefix(BASE)
        assert _canonical(client.get(path).text) == url, path
