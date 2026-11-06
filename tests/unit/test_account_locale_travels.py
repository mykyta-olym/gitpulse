"""The account's language has to reach a device with no locale cookie.

The Preferences page tells the reader these settings "travel with your account
to every device you log in from", and every other one does - they are rendered
onto `<html>` from the user row loaded on each request. Language was the
exception: `resolve_locale` consults the query param, then the `gp_lang`
cookie, then Accept-Language, and never the account. Saving a language writes
that cookie, so it worked on the device you changed it on and nowhere else - a
fresh browser rendered Slovak (measured) while the Preferences form on the same
page said English.

The documented precedence is unchanged: an explicit switch still outranks the
account, because the account value is only consulted when NEITHER the query
param nor the cookie said anything.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
DEPS = REPO / "src/app/dependencies.py"
I18N = REPO / "src/app/i18n/__init__.py"
MIDDLEWARE = REPO / "src/app/middleware/locale.py"


def test_resolve_locale_still_ignores_the_account() -> None:
    """The premise. `resolve_locale` runs in middleware, before any DB row is
    loaded, so it cannot know the account - which is why the refinement lives
    in the auth dependency instead."""
    src = I18N.read_text(encoding="utf-8")
    body = src.split("def resolve_locale(", 1)[1].split("\ndef ", 1)[0]
    assert "preferred_language" not in body, (
        "if resolve_locale learned about the account, the dependency-side "
        "refinement is now a duplicate - keep exactly one of them"
    )


def test_the_dependency_applies_the_account_language() -> None:
    src = DEPS.read_text(encoding="utf-8")
    assert "def _apply_account_locale(" in src
    assert "_apply_account_locale(request, session_data)" in src, (
        "the helper exists but require_dashboard_auth never calls it"
    )


def test_an_explicit_choice_still_outranks_the_account() -> None:
    src = DEPS.read_text(encoding="utf-8")
    body = src.split("def _apply_account_locale(", 1)[1].split("\ndef ", 1)[0]
    reason = (
        "the account value must yield to an explicit switch - the precedence "
        "recorded in api/dashboard/preferences.py"
    )
    assert "LOCALE_QUERY_PARAM" in body, reason
    assert "LOCALE_COOKIE_NAME" in body, (
        "the account value must yield to an explicit switch - the precedence "
        "recorded in api/dashboard/preferences.py"
    )
    guard = re.search(
        r"if request\.query_params\.get\(LOCALE_QUERY_PARAM\).*?:\s*\n\s*return", body, re.S
    )
    assert guard, "the early return that lets an explicit switch win is gone"


def test_the_response_header_reports_what_was_rendered() -> None:
    """The dependency refines the locale after the middleware captured it."""
    src = MIDDLEWARE.read_text(encoding="utf-8")
    assert 'getattr(request.state, "locale", None)' in src, (
        "content-language is built from the middleware's own early value again, "
        "so it can disagree with the language actually rendered"
    )
