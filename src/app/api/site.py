"""The site's public, non-dashboard routes: the root, the icons a browser and a
crawler probe for, the service worker, and what search engines read."""

import pathlib
from datetime import UTC, datetime

from fastapi import APIRouter
from fastapi.responses import RedirectResponse, Response

from app.config import get_settings

_STATIC_DIR = pathlib.Path(__file__).resolve().parents[1] / "templates" / "static"

site_router = APIRouter()


@site_router.get("/", include_in_schema=False)
async def root() -> Response:
    # The bare domain is the brand entry, so send it straight to the
    # indexable login page. Redirecting to /dashboard/ instead dead-ends
    # crawlers (it is Disallow-ed in robots.txt), which is why Google was
    # surfacing /docs/ rather than the app for the "gitpulse" query.
    # Authenticated visitors are bounced on to /dashboard/ by the login
    # route's own session check, so logged-in UX is unchanged.
    return RedirectResponse(url="/dashboard/login")


@site_router.api_route("/favicon.ico", methods=["GET", "HEAD"], include_in_schema=False)
async def favicon_ico() -> Response:
    # Serve a real multi-resolution .ico with a 200 at the canonical location
    # every crawler probes by default. The previous 301 -> PNG worked in
    # browsers but is the least reliable signal for Google Search's favicon
    # fetcher, which prefers a directly-served .ico - one reason the site
    # showed the generic globe in results. Fall back to the PNG if the asset
    # is ever missing.
    ico_path = _STATIC_DIR / "favicon.ico"
    if ico_path.is_file():
        return Response(
            content=ico_path.read_bytes(),
            media_type="image/x-icon",
            headers={"Cache-Control": "public, max-age=604800"},
        )
    return RedirectResponse(url="/static/img/icons/icon-96x96.png", status_code=301)


@site_router.get("/sw.js", include_in_schema=False)
async def service_worker() -> Response:
    """Serve the service worker from root scope '/' so it can control all pages."""
    sw_path = _STATIC_DIR / "sw.js"
    return Response(
        content=sw_path.read_bytes(),
        media_type="application/javascript",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Service-Worker-Allowed": "/",
        },
    )


# -- SEO: robots.txt --
@site_router.api_route("/robots.txt", methods=["GET", "HEAD"], include_in_schema=False)
async def robots_txt() -> Response:
    base = (get_settings().app_base_url or "").rstrip("/")
    # The monitoring paths are served by Caddy behind basic-auth and never
    # reach this app, so no X-Robots-Tag of ours can cover them. Google
    # crawled them anyway and reported "Blocked due to unauthorized request
    # (401)" in Search Console. Keeping crawlers off them is what robots.txt
    # is for. /metrics answers 403 for the same reason.
    body = (
        "User-agent: *\n"
        "Disallow: /api/\n"
        "Disallow: /dashboard/\n"
        "Disallow: /oauth/\n"
        "Disallow: /health/\n"
        "Disallow: /metrics\n"
        "Disallow: /grafana\n"
        "Disallow: /prometheus\n"
        "Disallow: /jaeger\n"
        "Disallow: /alertmanager\n"
        # The documentation sections behind a session (docs_authz.py:
        # ADMIN_ONLY + STAFF_ONLY). Caddy answers 302 to the login page for
        # anyone without one, so a crawler that follows these learns nothing
        # and Search Console fills with "Page with redirect" - 20 of the 49
        # URLs the docs sitemap submitted on 2026-09-08. This is the host's
        # robots.txt, which is the only one a crawler reads: /docs has its
        # own nginx but not its own hostname.
        "Disallow: /docs/ucitelia/\n"
        "Disallow: /docs/gitlab/\n"
        "Disallow: /docs/operatori/\n"
        "Disallow: /docs/bezpecnost/\n"
        "Disallow: /docs/en/ucitelia/\n"
        "Disallow: /docs/en/gitlab/\n"
        "Disallow: /docs/en/operatori/\n"
        "Disallow: /docs/en/bezpecnost/\n"
        "Allow: /dashboard/login\n"
        "Allow: /\n\n"
        f"Sitemap: {base}/sitemap.xml\n"
        f"Sitemap: {base}/docs/sitemap.xml\n"
    )
    return Response(
        content=body,
        media_type="text/plain",
        headers={"Cache-Control": "public, max-age=3600"},
    )


# -- SEO: sitemap.xml --
@site_router.api_route("/sitemap.xml", methods=["GET", "HEAD"], include_in_schema=False)
async def sitemap_xml() -> Response:

    base = (get_settings().app_base_url or "").rstrip("/")
    current_date = datetime.now(UTC).date().isoformat()

    # Local variables to keep XML line lengths under 100 characters.
    # Two URLs, the two canonical ones: the bare login page is the Slovak
    # version and the x-default (login.html explains); `?lang=sk` is the
    # same page under another name and canonicalises to it, so it is not
    # a page to submit. Submitting it was what had Search Console report
    # the pair as duplicates with a canonical Google chose itself.
    sk_href = f"{base}/dashboard/login"
    en_href = f"{base}/dashboard/login?lang=en"
    def_href = f"{base}/dashboard/login"

    body = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"\n'
        '        xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
        "  <url>\n"
        f"    <loc>{base}/dashboard/login</loc>\n"
        f'    <xhtml:link rel="alternate" hreflang="sk" href="{sk_href}" />\n'
        f'    <xhtml:link rel="alternate" hreflang="en" href="{en_href}" />\n'
        f'    <xhtml:link rel="alternate" hreflang="x-default" href="{def_href}" />\n'
        f"    <lastmod>{current_date}</lastmod>\n"
        "    <changefreq>monthly</changefreq>\n"
        # The public login page is the application's primary entry point and
        # the brand landing page, so it carries the top priority. Docs are a
        # secondary resource (their own /docs/sitemap.xml) and must not
        # outrank the app for the brand query.
        "    <priority>1.0</priority>\n"
        "  </url>\n"
        "  <url>\n"
        f"    <loc>{base}/dashboard/login?lang=en</loc>\n"
        f'    <xhtml:link rel="alternate" hreflang="sk" href="{sk_href}" />\n'
        f'    <xhtml:link rel="alternate" hreflang="en" href="{en_href}" />\n'
        f'    <xhtml:link rel="alternate" hreflang="x-default" href="{def_href}" />\n'
        f"    <lastmod>{current_date}</lastmod>\n"
        "    <changefreq>monthly</changefreq>\n"
        "    <priority>0.8</priority>\n"
        "  </url>\n"
        "</urlset>\n"
    )
    return Response(
        content=body,
        media_type="application/xml",
        headers={"Cache-Control": "public, max-age=3600"},
    )


# -- SEO: llms.txt --
@site_router.get("/llms.txt", include_in_schema=False)
async def llms_txt() -> Response:
    base = (get_settings().app_base_url or "").rstrip("/")
    body = (
        "# GitPulse\n\n"
        "GitPulse is a GitLab Teamwork & Assessment Platform designed for the "
        "Technical University of Košice (TUKE), specifically the Department of Computers "
        "and Informatics (KPI).\n\n"
        "It evaluates teamwork, GitLab metrics, DevOps compliance checks (R01-R13), "
        "and automates course grading workflows for teachers.\n\n"
        "## Public Resources\n\n"
        f"- User Login: {base}/dashboard/login\n"
        f"- Documentation: {base}/docs/\n"
        f"- English Documentation: {base}/docs/en/\n\n"
        "## Key Concepts\n\n"
        "- **GitLab Sync**: Automatic sync jobs fetching commit histories, "
        "merge requests, CI pipelines, and repository events.\n"
        "- **Compliance Rules (R01-R13)**: Strict automated checks verifying "
        "repository structure, branching models, commit messages, and deployment setups.\n"
        "- **Course Metrics**: Consolidated dashboards displaying teamwork trends, "
        "grading recommendations, and student activity logs.\n\n"
        "## Excluded Private Routes\n\n"
        "All student teamwork data, grades, team details, course metrics, "
        "sync schedules, and settings are strictly private and "
        "authentication-guarded. Do not crawl or index the following paths:\n"
        "- `/dashboard/*` (except `/dashboard/login`)\n"
        "- `/api/*`\n"
        "- `/health/*`\n"
        "- `/oauth/*`\n"
    )
    return Response(
        content=body,
        media_type="text/plain",
        headers={"Cache-Control": "public, max-age=3600"},
    )


# -- Google Search Console verification --
@site_router.api_route(
    "/google32f411f09f436ae2.html", methods=["GET", "HEAD"], include_in_schema=False
)
async def google_verification() -> Response:
    return Response(
        content="google-site-verification: google32f411f09f436ae2.html",
        media_type="text/html",
    )


# -- Privacy Policy (GDPR) - redirect to docs site --
@site_router.api_route("/privacy", methods=["GET", "HEAD"], include_in_schema=False)
async def privacy_policy() -> Response:
    return RedirectResponse(url="/docs/pravne/ochrana-udajov/", status_code=301)


# -- Terms of Service - redirect to docs site --
@site_router.api_route("/terms", methods=["GET", "HEAD"], include_in_schema=False)
async def terms_of_service() -> Response:
    return RedirectResponse(url="/docs/pravne/podmienky/", status_code=301)
