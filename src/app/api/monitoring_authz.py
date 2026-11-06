"""Let a signed-in GitPulse administrator into the monitoring tools.

Grafana, Prometheus, Jaeger and Alertmanager sit behind Caddy at /grafana/,
/prometheus/, /jaeger/ and /alertmanager/. They used to ask for a password of
their own - one Basic Auth credential shared by all four, which had ended up in
the operator documentation. Caddy now asks this endpoint before each request
there, the way it asks docs_authz before serving /docs/:

    204  an administrator - serve it; for Grafana, with the user's login, which
         its auth proxy signs in (GF_AUTH_PROXY_*)
    302  no session - sign in, then come back
    403  signed in without the admin role

Unlike the documentation gate this one fails CLOSED. A documentation page is
harmless to show; the monitoring tools are the system's insides, so a session
that cannot be read lets nobody in.
"""

from __future__ import annotations

from html import escape
from urllib.parse import quote

import structlog
from fastapi import APIRouter, Query, Request, Response, status
from fastapi.responses import HTMLResponse, RedirectResponse

from app.config import get_settings
from app.i18n import resolve_locale
from app.security.session_auth import get_current_session

logger = structlog.get_logger(__name__)

router = APIRouter(tags=["internal"])

#: What Caddy serves at each prefix. Prometheus and Alertmanager sit behind
#: `handle_path`, which strips the prefix before this endpoint sees the URI.
SERVICES = ("grafana", "prometheus", "jaeger", "alertmanager")

#: The headers Grafana's auth proxy reads. Caddy copies them from this answer
#: onto the request, and drops a client's own (copy_headers).
GRAFANA_USER_HEADER = "X-Grafana-User"
GRAFANA_EMAIL_HEADER = "X-Grafana-Email"

#: Marks a request already sent to sign in once, so a bug can cost an
#: explanation but never a redirect loop (see docs_authz).
_RETRY_MARKER = "signin=1"

_STYLE = """
  body { margin:0; min-height:100vh; display:grid; place-items:center;
         background:#18171d; color:#ececef;
         font:16px/1.6 "GitLab Sans", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
  main { max-width:34rem; padding:2rem; text-align:center; }
  h1 { font-size:1.75rem; margin:0 0 .75rem; }
  p { margin:0 0 1rem; color:#bfbfc3; }
  a { color:#63a6e9; }
"""

_TEXT = {
    "sk": {
        "refused_title": "Prístup zamietnutý",
        "refused": "Monitorovanie ({service}) je len pre administrátorov GitPulse."
        " Ste prihlásený s rolou <strong>{role}</strong>.",
        "signin_title": "Prihlásenie potrebné",
        "signin": "Monitorovanie ({service}) otvoríte po prihlásení do GitPulse ako administrátor.",
        "signin_link": "Prihlásiť sa",
        "unavailable_title": "Prihlásenie sa nedá overiť",
        "unavailable": "GitPulse teraz nevie overiť prihlásenie, preto monitorovanie"
        " nikoho nepustí. Skúste to o chvíľu znova.",
        "back": "Späť do GitPulse",
    },
    "en": {
        "refused_title": "Access denied",
        "refused": "Monitoring ({service}) is for GitPulse administrators only."
        " You are signed in with the role <strong>{role}</strong>.",
        "signin_title": "Sign-in required",
        "signin": "Sign in to GitPulse as an administrator to open monitoring ({service}).",
        "signin_link": "Sign in",
        "unavailable_title": "Sign-in cannot be checked",
        "unavailable": "GitPulse cannot check the sign-in right now, so monitoring lets"
        " nobody in. Try again in a moment.",
        "back": "Back to GitPulse",
    },
}


def _page(*, lang: str, title_key: str, body: str, signin: bool = False) -> str:
    t = _TEXT.get(lang, _TEXT["sk"])
    links = f'<a href="/dashboard/">{t["back"]}</a>'
    if signin:
        links = f'<a href="/dashboard/login">{t["signin_link"]}</a> &middot; ' + links
    return f"""<!doctype html>
<html lang="{lang}"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{t[title_key]} | GitPulse</title>
<style>{_STYLE}</style></head>
<body><main>
  <h1>{t[title_key]}</h1>
  <p>{body}</p>
  <p>{links}</p>
</main></body></html>
"""


def public_path(service: str, uri: str) -> str:
    """The address the reader typed, from the URI Caddy forwarded.

    `handle_path` strips the prefix (Prometheus, Alertmanager), `handle` does
    not (Grafana, Jaeger), so the prefix is added back only when it is missing.
    """
    prefix = f"/{service}"
    if not uri.startswith("/"):
        uri = "/" + uri
    if uri == prefix or uri.startswith(prefix + "/"):
        return uri
    return prefix + uri


@router.get("/internal/monitoring-authz", include_in_schema=False)
async def monitoring_authz(request: Request, service: str = Query(...)) -> Response:
    """Allow or refuse one request to a monitoring tool."""
    lang = resolve_locale(request)
    t = _TEXT.get(lang, _TEXT["sk"])
    if service not in SERVICES:
        return Response(status_code=status.HTTP_403_FORBIDDEN)
    uri = request.headers.get("X-Forwarded-Uri", "/")

    try:
        settings = get_settings()
        # enforce_ua=False for the reason docs_authz gives: this runs as Caddy's
        # subrequest, not as the browser's own request. It performs no action.
        session = get_current_session(
            request,
            secret_key=settings.secret_key,
            app_base_url=settings.app_base_url,
            enforce_ua=False,
        )
    except Exception:
        logger.warning("monitoring_authz_session_read_failed", service=service)
        return HTMLResponse(
            _page(lang=lang, title_key="unavailable_title", body=t["unavailable"]),
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    if session is None:
        target = public_path(service, uri)
        if _RETRY_MARKER in target:
            return HTMLResponse(
                _page(
                    lang=lang,
                    title_key="signin_title",
                    body=t["signin"].format(service=escape(service)),
                    signin=True,
                ),
                status_code=status.HTTP_401_UNAUTHORIZED,
            )
        sep = "&" if "?" in target else "?"
        return RedirectResponse(
            url=f"/dashboard/login?next={quote(target + sep + _RETRY_MARKER, safe='/?&=')}",
            status_code=status.HTTP_302_FOUND,
        )

    role = (session.get("role") or "").lower()
    if role != "admin":
        logger.info("monitoring_authz_role_too_low", service=service, role=role)
        return HTMLResponse(
            _page(
                lang=lang,
                title_key="refused_title",
                body=t["refused"].format(service=escape(service), role=escape(role or "-")),
            ),
            status_code=status.HTTP_403_FORBIDDEN,
        )

    headers: dict[str, str] = {"Cache-Control": "no-store"}
    if service == "grafana":
        # A header carries latin-1 at most; a GitLab login is ASCII, and an
        # account without one is let into the other tools but not signed in
        # to Grafana under a name it cannot carry.
        login = str(session.get("user") or "")
        if not login or not login.isascii():
            logger.warning("monitoring_authz_grafana_login_unusable")
            return HTMLResponse(
                _page(
                    lang=lang,
                    title_key="refused_title",
                    body=t["refused"].format(service="grafana", role=escape(role)),
                ),
                status_code=status.HTTP_403_FORBIDDEN,
            )
        headers[GRAFANA_USER_HEADER] = login
        email = str(session.get("email") or "")
        if email and email.isascii():
            headers[GRAFANA_EMAIL_HEADER] = email
    return Response(status_code=status.HTTP_204_NO_CONTENT, headers=headers)
