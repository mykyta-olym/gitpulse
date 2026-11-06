"""Attacks on `?next=`, kept as tests.

`safe_redirect_target` is what stands between the sign-in page's `next`
parameter and an open redirect - a phishing link that begins on the real login
form, collects the password, and hands the reader to someone else's server.

`/\\evil.example` defeated it until 2026-08-20. It refused `//evil.example`,
but browsers normalise backslashes to forward slashes in the authority position
of a special scheme, so the two navigate to the same place; the check was
reading a different address than the one the browser would load.

The payloads below are the ways of writing an off-site address that a check on
the raw characters mistakes for a local path.
"""

from __future__ import annotations

from urllib.parse import urlparse

import pytest

from app.i18n import safe_redirect_target

FALLBACK = "/dashboard/"
OUR_HOST = "gitpulse.kpi.fei.tuke.sk"


class _FakeRequest:
    """Only `.url.netloc` is read."""

    class _URL:
        netloc = OUR_HOST

    url = _URL()


def browser_target_host(location: str) -> str | None:
    """The host a browser navigates to, or None when it stays on this origin."""
    probe = location.replace("\\", "/")
    probe = probe.translate({0x09: None, 0x0A: None, 0x0D: None})
    if probe.startswith("//") and not probe.startswith("///"):
        host = probe[2:].split("/")[0].split("?")[0].split("#")[0]
        return host or None
    parsed = urlparse(probe)
    if parsed.scheme in ("http", "https") and parsed.netloc:
        return parsed.netloc
    return None


ESCAPES = [
    ("//evil.example", "protocol-relative"),
    ("https://evil.example", "absolute, other host"),
    ("http://evil.example/x", "absolute, other scheme"),
    ("/\\evil.example", "backslash after one slash"),
    ("\\\\evil.example", "two backslashes"),
    ("/\\/evil.example", "backslash then slash"),
    ("\\/evil.example", "backslash slash"),
    ("/\\\\evil.example", "slash then two backslashes"),
    ("/\\\\\\evil.example", "three backslashes"),
    ("//evil.example\\@" + OUR_HOST, "userinfo confusion"),
    ("//\tevil.example", "tab after slashes"),
    ("/\r\n//evil.example", "CR LF then protocol-relative"),
    ("  //evil.example", "leading whitespace"),
    ("//evil.example/%2e%2e", "protocol-relative with traversal"),
]

LOCAL = [
    "/dashboard/",
    "/docs/uvod/",
    "/docs/ucitelia/dashboard/?signin=1",
    "/dashboard/courses/123/settings#danger-zone",
    f"https://{OUR_HOST}/dashboard/",
]


@pytest.mark.parametrize(("payload", "attack"), ESCAPES, ids=[a[1] for a in ESCAPES])
def test_the_reader_never_leaves_this_origin(payload: str, attack: str) -> None:
    out = safe_redirect_target(_FakeRequest(), payload, fallback=FALLBACK)
    host = browser_target_host(out)
    assert host is None, f"{attack}: {payload!r} -> {out!r} -> https://{host}"


@pytest.mark.parametrize("payload", LOCAL)
def test_an_honest_target_still_works(payload: str) -> None:
    """A redirect guard that sends everything to the fallback is not a guard,
    it is a broken feature - signing in has to land where the reader was."""
    out = safe_redirect_target(_FakeRequest(), payload, fallback=FALLBACK)
    assert out.startswith("/"), out
    assert browser_target_host(out) is None
    if payload.startswith("/"):
        assert out == payload


def test_every_result_is_rooted() -> None:
    """A bare relative path resolves against the current directory, which is not
    where anybody meant to send the reader."""
    for payload in ("https:somewhere", "somewhere", "?x=1", ""):
        out = safe_redirect_target(_FakeRequest(), payload, fallback=FALLBACK)
        assert out.startswith("/"), (payload, out)


def test_empty_and_missing_fall_back() -> None:
    for payload in (None, "", "   ", "\t\r\n"):
        assert safe_redirect_target(_FakeRequest(), payload, fallback=FALLBACK) == FALLBACK
