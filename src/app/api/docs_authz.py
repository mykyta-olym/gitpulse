"""Authorize a documentation request by the reader's role.

The documentation is a static site served by its own nginx, so it has no way to
know who is reading. Caddy therefore asks this endpoint before serving anything
under ``/docs/``: it forwards the original path in ``X-Forwarded-Uri`` and serves
the page only on a 2xx.

Three tiers, from the sections the content already has:

    admin only     operations and security - deployment, backups, tokens,
                   hardening. A student or a teacher has nothing to do there and
                   the pages name internal hosts.
    staff          the teacher's guide and the GitLab integration, which
                   describe grading and the instance configuration.
    everyone       introduction, the student guide, the API contract, the
                   developer guide, the thesis and the legal pages.

Anything not matched is treated as public: a new page becomes readable rather
than unreachable, and the two tiers above are listed explicitly.
"""

from __future__ import annotations

from html import escape
from urllib.parse import quote, unquote

import structlog
from fastapi import APIRouter, Request, Response, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

from app.config import get_settings
from app.security.session_auth import get_current_session

logger = structlog.get_logger(__name__)

router = APIRouter(tags=["internal"])

#: Roles that may read each gated prefix. Paths are matched after the ``/docs``
#: prefix, in both languages (``/en/`` is stripped before matching).
ADMIN_ONLY = ("operatori/", "bezpecnost/")
STAFF_ONLY = ("ucitelia/", "gitlab/")

#: Readable without a session. Named so the reader can be TOLD what they
#: may open, instead of finding out by being refused.
PUBLIC_SECTIONS = ("uvod/", "studenti/", "vyvojari/", "api/", "diplomovka/", "pravne/")

#: Everyone with a session; ``admin`` is staff too.
_STAFF = frozenset({"admin", "teacher"})

#: Requests for files rather than pages. Gating these breaks the pages that ARE
#: allowed to load, so they always pass.
#:
#: `.json`, `.xml` and `.txt` are deliberately NOT here. They were, for the
#: theme's own data files - but the suffix says nothing about where the file
#: lives, so any of them published inside a gated section would have been served
#: to anyone. The theme's data sits under the prefixes in `_ASSET_PREFIXES`.
_ASSET_SUFFIXES = (
    ".css",
    ".js",
    ".mjs",
    ".map",
    ".svg",
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".gif",
    ".ico",
    ".woff",
    ".woff2",
    ".ttf",
    ".pf",
)

#: Directories that hold build output rather than documentation. Note which
#: search index is here and which is not: `pagefind/` carries the PUBLIC pages
#: only, so it is an asset; `pagefind-staff/` and `pagefind-admin/` carry the
#: text of gated pages and are gated with them. One index over the whole site
#: was a hole straight through this gate - see bin/build-search-indexes.sh.
_ASSET_PREFIXES = (
    "pagefind/",
    "vite/",
    "css/",
    "js/",
    "gitlab_ui/",
    "fa-icons/",
    "assets/",
    "manifests/",
)

#: Search indexes that carry gated text, and the role each one needs.
_GATED_INDEXES = {
    "pagefind-staff/": "staff",
    "pagefind-admin/": "admin",
}


def _is_asset(uri: str) -> bool:
    """True for build output, never for a page - and never for a gated index."""
    section = _section_of(uri)
    if section.startswith(tuple(_GATED_INDEXES)):
        return False
    path = uri.split("?", 1)[0]
    return path.endswith(_ASSET_SUFFIXES) or section.startswith(_ASSET_PREFIXES)


def _section_of(uri: str) -> str:
    """The section a docs URI belongs to, normalised, language prefix removed.

    Normalisation is part of the authorization decision, not tidiness. Comparing
    raw segments meant `/ucitelia/../operatori/` matched the STAFF prefix while
    the file actually served was the admin page, and `/./operatori/` matched no
    prefix at all and so came out public. Caddy normalises before forwarding
    today; an access-control decision must not rest on that staying true.

    Percent-encoding is decoded first, for the same reason: `%2e%2e` is `..` to
    whatever serves the file, so it must be `..` here too.
    """
    path = unquote(uri.split("?", 1)[0])
    # Backslashes are path separators to some servers; treat them as such.
    path = path.replace("\\", "/").lower()

    segments: list[str] = []
    for segment in path.split("/"):
        if segment in ("", "."):
            continue
        if segment == "..":
            if segments:
                segments.pop()
            continue
        segments.append(segment)

    while segments and segments[0] in ("docs", "en"):
        segments.pop(0)
    return "/".join(segments) + "/" if segments else ""


def _lang_of(uri: str) -> str:
    """The language the reader asked for.

    Slovak is the default language and owns the un-prefixed URLs, so only an
    `/en/` segment means anything. Without this the gate answered a refusal in
    Slovak to a reader who was reading the site in English.
    """
    path = uri.split("?", 1)[0].lstrip("/")
    if path.startswith("docs/"):
        path = path[len("docs/") :]
    return "en" if path == "en" or path.startswith("en/") else "sk"


def required_role(uri: str) -> str | None:
    """``"admin"``, ``"staff"`` or ``None`` when the page is public."""
    section = _section_of(uri)
    for prefix, role in _GATED_INDEXES.items():
        if section.startswith(prefix):
            return role
    if section.startswith(ADMIN_ONLY):
        return "admin"
    if section.startswith(STAFF_ONLY):
        return "staff"
    return None


def _public_path(uri: str) -> str:
    """The URL a reader typed, rebuilt from the path Caddy forwarded.

    `handle_path /docs/*` strips the prefix before this endpoint sees it, so the
    forwarded URI is `/ucitelia/` while the reader is looking at
    `/docs/ucitelia/`. Sending them back to the stripped path would land them on
    the application instead of the documentation.
    """
    path = uri.split("?", 1)[0]
    if not path.startswith("/"):
        path = "/" + path
    return path if path.startswith("/docs/") else "/docs" + path


#: Marks a request that has already been sent to sign in once. Its only job is
#: to make a redirect loop impossible.
_RETRY_MARKER = "signin=1"


#: Both gate pages are plain and self-contained on purpose: Caddy serves them
#: in place of the documentation, so the documentation's stylesheets may never
#: have been fetched.
_GATE_STYLE = """
  body { margin:0; min-height:100vh; display:grid; place-items:center;
         background:#18171d; color:#ececef;
         font:16px/1.6 "GitLab Sans", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
  main { max-width:34rem; padding:2rem; text-align:center; }
  h1 { font-size:1.75rem; margin:0 0 .75rem; }
  p { margin:0 0 1rem; color:#bfbfc3; }
  a { color:#63a6e9; }
"""

_SIGNIN_TEXT = {
    "sk": {
        "title": "Prihlásenie potrebné",
        "heading": "Táto časť vyžaduje prihlásenie",
        "body": "Stránku <code>{path}</code> vidia prihlásení učitelia a administrátori.",
        "signin": "Prihlásiť sa",
        "back": "Späť na verejnú dokumentáciu",
    },
    "en": {
        "title": "Sign-in required",
        "heading": "This section requires signing in",
        "body": "<code>{path}</code> is visible to signed-in teachers and administrators.",
        "signin": "Sign in",
        "back": "Back to the public documentation",
    },
}


def _signin_page(*, path: str, lang: str = "sk") -> str:
    """Shown when signing in did not produce a session the gate can see."""
    t = _SIGNIN_TEXT.get(lang, _SIGNIN_TEXT["sk"])
    home = "/docs/en/" if lang == "en" else "/docs/"
    return f"""<!doctype html>
<html lang="{lang}"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{t["title"]} | GitPulse Docs</title>
<style>{_GATE_STYLE}</style></head>
<body><main>
  <h1>{t["heading"]}</h1>
  <p>{t["body"].format(path=escape(path))}</p>
  <p><a href="/dashboard/login">{t["signin"]}</a> &middot;
     <a href="{home}">{t["back"]}</a></p>
</main></body></html>
"""


_ROLE_NAMES = {
    "sk": {
        "admin": "administrátor",
        "staff": "učiteľ alebo administrátor",
        "unknown": "neznáma",
    },
    "en": {
        "admin": "an administrator",
        "staff": "a teacher or an administrator",
        "unknown": "unknown",
    },
}

_REFUSAL_TEXT = {
    "sk": {
        "title": "Prístup zamietnutý",
        "heading": "Táto časť dokumentácie je vyhradená",
        "body": (
            "Stránku <code>{path}</code> môže otvoriť {need}."
            " Ste prihlásený s rolou <strong>{role}</strong>."
        ),
        "ask": 'Ak potrebujete prístup, napíšte na <a href="mailto:{email}">{email}</a>.',
        "back": "Späť na dokumentáciu",
    },
    "en": {
        "title": "Access denied",
        "heading": "This part of the documentation is restricted",
        "body": (
            "<code>{path}</code> can be opened by {need}."
            " You are signed in with the role <strong>{role}</strong>."
        ),
        "ask": 'If you need access, write to <a href="mailto:{email}">{email}</a>.',
        "back": "Back to the documentation",
    },
}

_CONTACT_EMAIL = "mykyta.olym.work@gmail.com"


def _refusal_page(*, needed: str, role: str, path: str, lang: str = "sk") -> str:
    """Explain a refusal in a way the reader can act on."""
    t = _REFUSAL_TEXT.get(lang, _REFUSAL_TEXT["sk"])
    names = _ROLE_NAMES.get(lang, _ROLE_NAMES["sk"])
    need = names.get(needed, needed)
    home = "/docs/en/" if lang == "en" else "/docs/"
    body = t["body"].format(
        path=escape(path), need=escape(need), role=escape(role or names["unknown"])
    )
    return f"""<!doctype html>
<html lang="{lang}"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{t["title"]} | GitPulse Docs</title>
<style>{_GATE_STYLE}</style></head>
<body><main>
  <h1>{t["heading"]}</h1>
  <p>{body}</p>
  <p>{t["ask"].format(email=_CONTACT_EMAIL)}</p>
  <p><a href="{home}">{t["back"]}</a></p>
</main></body></html>
"""


@router.get("/internal/docs-role", include_in_schema=False)
async def docs_role(request: Request) -> JSONResponse:
    """Who the reader is, and which documentation sections that opens.

    The documentation is static HTML, so it cannot read the role header Caddy
    passes it. This is what a page asks instead, to tell the reader what they
    may open rather than letting them discover it by being refused.

    Answers for anonymous readers too - the public sections are the honest
    answer to "what can I see".
    """
    role = ""
    try:
        settings = get_settings()
        # Same reasoning as docs_authz: this is asked by a page, not by the
        # browser's own navigation, and it only reports a role.
        session = get_current_session(
            request,
            secret_key=settings.secret_key,
            app_base_url=settings.app_base_url,
            enforce_ua=False,
        )
        if session:
            role = (session.get("role") or "").lower()
    except Exception:
        logger.warning("docs_role_session_read_failed")

    sections = list(PUBLIC_SECTIONS)
    if role in _STAFF:
        sections += list(STAFF_ONLY)
    if role == "admin":
        sections += list(ADMIN_ONLY)

    return JSONResponse(
        {"role": role or "anonymous", "sections": sorted(s.rstrip("/") for s in sections)},
        headers={"Cache-Control": "no-store"},
    )


@router.get("/internal/docs-authz", include_in_schema=False)
async def docs_authz(request: Request, response: Response) -> Response:
    """Allow or refuse one documentation request.

    Three answers, and Caddy passes each of them to the browser unchanged:

        204  serve the page
        302  no session - go and sign in, then come back to this page
        403  signed in, wrong role - a page explaining which role opens it

    The 302 matters for the reader who arrives from a search engine: a teacher
    following a link to the teacher's guide has never signed in here, and a bare
    401 gives them nothing to act on.
    """
    uri = request.headers.get("X-Forwarded-Uri", request.url.path)

    # Assets are never gated. Caddy asks about EVERY request under /docs/,
    # stylesheets and fonts included, and refusing one of those does not hide a
    # page - it breaks the page that is allowed to load.
    if _is_asset(uri):
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    needed = required_role(uri)
    if needed is None:
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    # Fail OPEN. This runs in front of every documentation request; if reading a
    # session ever raises, the documentation must stay readable rather than the
    # whole site turning into a sign-in wall.
    try:
        settings = get_settings()
        # enforce_ua=False deliberately.
        #
        # A session cookie is bound to the browser's User-Agent fingerprint, and
        # this runs as a Caddy SUBREQUEST - not as the browser's own request.
        # With the check on, a genuinely signed-in reader was rejected here and
        # refused every gated page, which is exactly what was reported.
        #
        # The binding still protects everything it was added for: this endpoint
        # performs no action and returns no data, it only answers whether a
        # documentation page may be served.
        session = get_current_session(
            request,
            secret_key=settings.secret_key,
            # Without this the default is http://localhost:8000, which means
            # "not secure" - so it looked for the UNPREFIXED cookie name while
            # the browser sends `__Host-gitpulse_session`. The cookie was
            # arriving and simply not being looked for, which is why a
            # signed-in admin was refused and the sign-in redirect then looped.
            app_base_url=settings.app_base_url,
            enforce_ua=False,
        )
    except Exception:
        logger.warning("docs_authz_session_read_failed", uri=uri)
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    if session is None:
        # Which of the two it is decides the fix, and the logs could not tell
        # them apart: a reader who really is signed out, or a signed-in reader
        # whose cookie never reached this subrequest.
        logger.info(
            "docs_authz_refused",
            uri=uri,
            needed=needed,
            cookie_header_present=bool(request.headers.get("cookie")),
            cookie_names=sorted(request.cookies.keys())[:6],
            user_agent_present=bool(request.headers.get("user-agent")),
        )
        # Send them to sign in and back, rather than showing a bare 401.
        #
        # The reader this matters for arrives from a search engine: a teacher
        # follows a link to the teacher's guide, has never signed in to this
        # site, and a 401 tells them nothing they can act on.
        #
        # ONCE, though. If the reader comes back still looking signed out, the
        # redirect would bounce them between the gate and the sign-in page until
        # the rate limiter answered 429 - which is exactly what happened when
        # this endpoint was looking for the wrong cookie name. The marker makes
        # a second pass show an explanation instead, so a bug here can cost a
        # confusing page but never a loop.
        if _RETRY_MARKER in uri:
            return HTMLResponse(
                _signin_page(path=_public_path(uri), lang=_lang_of(uri)),
                status_code=status.HTTP_401_UNAUTHORIZED,
            )
        target = _public_path(uri)
        sep = "&" if "?" in target else "?"
        return RedirectResponse(
            url=f"/dashboard/login?next={quote(target + sep + _RETRY_MARKER, safe='/?&=')}",
            status_code=status.HTTP_302_FOUND,
        )

    role = (session.get("role") or "").lower()
    allowed = role == "admin" if needed == "admin" else role in _STAFF
    if not allowed:
        # Signed in, but not for this section. Sending them to sign in again
        # would loop, so say which role opens it and where they can go instead.
        logger.info("docs_authz_role_too_low", uri=uri, needed=needed, role=role)
        return HTMLResponse(
            _refusal_page(needed=needed, role=role, path=_public_path(uri), lang=_lang_of(uri)),
            status_code=status.HTTP_403_FORBIDDEN,
        )

    # Passed back to the docs container so a page can note who it rendered for.
    response.headers["X-Docs-Role"] = role
    return Response(status_code=status.HTTP_204_NO_CONTENT, headers={"X-Docs-Role": role})
