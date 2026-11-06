"""The transactional email chrome must stay 1:1 with GitLab's own mailer.

Ground truth is gitlab-org/gitlab:
  app/views/layouts/_mailer.html.haml
  app/assets/stylesheets/mailers/mailer.scss
  app/assets/stylesheets/mailers/mailer_client_specific.scss

The email used to be built from a Tailwind slate palette in Google-hosted
Inter, with a gradient CTA - none of which GitLab has anywhere. These tests
pin the values so it cannot drift back.
"""

import re
from pathlib import Path

import pytest

from app.services.email_notifications import _build_html


@pytest.fixture(scope="module")
def rendered() -> str:
    return _build_html(
        heading="Compliance run finished",
        body_lines=["Course finished its weekly run."],
        action_url="https://example.test/dashboard/courses/1",
        action_label="View report",
        meta_rows=[("Course", "DevOps 2026"), ("Students", "42")],
    )


# value -> the mailer.scss / variables.scss declaration it comes from
GITLAB_MAILER_VALUES = {
    "width:640px": "$full-width",
    "height:4px;font-size:4px;line-height:4px": "tr.line td",
    "background-color:#6b4fbb": "$mailer-line-cell-bg-color / $purple",
    "'Helvetica Neue', Helvetica, Arial, sans-serif": "$mailer-font",
    "color:#333333": "$mailer-text-color",
    "background-color:#fafafa": "$mailer-bg-color",
    "color:#3777b0": "$mailer-link-color",
    "1px solid #ededed": "$mailer-wrapper-cell-border-color",
    "color:#5c5c5c": "$mailer-header-footer-text-color",
    "color:#89888d": "$gray-400 (.gitlab-info-text)",
    "padding:25px 0": "tr.header/tr.footer padding",
    "font-size:15px": "td.text-content font-size",
    "text-align:center": "td.text-content text-align",
}

# Where the RENDERED mail departs from the raw SCSS, and why. mailer.scss is a
# stylesheet premailer post-processes; what actually lands in an inbox is
# roomier than the declarations suggest, and GitLab's own screenshots are the
# ground truth the reader compares against.
RENDERED_OVERRIDES = {
    # scss says `border-radius: 3px`; GitLab's mail renders a 4px card, the
    # same $gl-border-radius-base every other GitLab surface uses.
    "border-radius:4px": "rendered card corner (scss declares 3px)",
    # scss says `padding: 18px 25px`; the delivered card is markedly roomier.
    "padding:32px 40px": "rendered card padding (scss declares 18px 25px)",
    # $gl-btn-*-padding describes an in-app button. The one prominent action in
    # a GitLab email is much larger - see .invite-btn-join.
    "padding:12px 24px": "rendered email button (in-app button is 8px 12px)",
}


@pytest.mark.parametrize(("value", "source"), GITLAB_MAILER_VALUES.items())
def test_gitlab_mailer_value_present(rendered: str, value: str, source: str) -> None:
    assert value in rendered, f"{value} missing - GitLab declares it as {source}"


@pytest.mark.parametrize(("value", "why"), RENDERED_OVERRIDES.items())
def test_rendered_override_present(rendered: str, value: str, why: str) -> None:
    assert value in rendered, f"{value} missing - {why}"


# These are what the email carried before; none exist anywhere in GitLab.
OFF_SYSTEM = [
    "Inter",
    "fonts.googleapis",
    "#0f172a",
    "#334155",
    "#475569",
    "#64748b",
    "#94a3b8",
    "#cbd5e1",
    "#e2e8f0",
    "#f8fafc",
    "#f1f5f9",
    "2563eb",
    "3b82f6",
    "linear-gradient",
    "box-shadow",
]


@pytest.mark.parametrize("token", OFF_SYSTEM)
def test_no_off_system_styling(rendered: str, token: str) -> None:
    assert token not in rendered, f"{token} is not a GitLab value"


def test_client_specific_rules_present(rendered: str) -> None:
    """Media queries and client hacks cannot be inlined, so they must survive
    in the <style> block - GitLab marks the same sheet 'premailer: ignore'."""
    for rule in (
        "max-width: 639px",  # the one breakpoint GitLab ships
        "mso-table-lspace",  # Outlook table spacing
        "x-apple-data-detectors",  # iOS auto-linking
        "-webkit-text-size-adjust",
        "-ms-interpolation-mode",
    ):
        assert rule in rendered, f"{rule} missing"


def test_no_external_stylesheet_or_font_request(rendered: str) -> None:
    """A mail client that blocks remote content must still render correctly,
    and a Google Fonts request from an email leaks the recipient's open."""
    assert "<link" not in rendered
    assert "@import" not in rendered


def test_structure_matches_gitlab_layout(rendered: str) -> None:
    """table#body > tr.line, tr.header, table.wrapper > td.wrapper-cell >
    table.content, then the footer rows - _mailer.html.haml's skeleton."""
    for marker in (
        'id="body"',
        'class="line"',
        'class="header"',
        'class="wrapper"',
        'class="wrapper-cell"',
        'class="content"',
        'class="footer"',
        'class="footer-message"',
    ):
        assert marker in rendered, f"{marker} missing from the layout"


@pytest.mark.parametrize("tag", ["table", "tr", "td", "tbody", "html", "body"])
def test_tags_balanced(rendered: str, tag: str) -> None:
    """An unbalanced table silently collapses the whole layout in Outlook."""
    opened = len(re.findall(rf"<{tag}[ >]", rendered))
    closed = len(re.findall(rf"</{tag}>", rendered))
    assert opened == closed, f"<{tag}>: {opened} open vs {closed} close"


# -- The whole module, not just one rendered sample -------------------------
#
# The tests above render _build_html once. That is not enough: several mails
# build their own inline HTML and pass it in as a body line, bypassing the
# chrome entirely. The welcome mail did exactly that - an <li> list in
# Google-hosted Inter over #475569, and a #2563eb link - and every check above
# passed while it shipped.

_SOURCE = (
    Path(__file__).resolve().parents[2] / "src/app/services/email_notifications.py"
).read_text(encoding="utf-8")


@pytest.mark.parametrize("token", OFF_SYSTEM)
def test_no_off_system_value_anywhere_in_the_module(token: str) -> None:
    """Not just in the rendered sample - anywhere a mail is composed."""
    # The parity tests name these tokens in their own prose; the module must not.
    assert token not in _SOURCE, (
        f"{token} is not a GitLab value, and it is in email_notifications.py"
    )


def test_every_internal_link_points_at_a_real_route() -> None:
    """A footer link to a page that does not exist sends every reader to a 404.

    /dashboard/settings was referenced twice - in the footer and in the
    List-Unsubscribe header - and has never existed as a route.
    """
    import os
    import re
    import sys

    os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://u:p@localhost/x")
    os.environ.setdefault("SECRET_KEY", "x" * 32)
    os.environ.setdefault("TEACHER_API_TOKEN", "y" * 16)
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
    from app.main import create_app
    from tests.route_discovery import iter_routes

    # This FastAPI defers include_router into placeholders that a plain read of
    # app.routes does not expand (~19 routes, no dashboard at all), so every
    # /dashboard/... link looked missing. iter_routes recurses them - all 195 -
    # so a link that resolves in the running app resolves here too.
    routes = {path for path, _methods in iter_routes(create_app().routes)}
    referenced = set(re.findall(r"/dashboard/[a-z0-9/-]+", _SOURCE))

    missing = []
    for path in sorted(referenced):
        # Paths built with an interpolated id (…/ticket/{id}) are parameterised
        # routes; compare their stem instead.
        stem = path.rstrip("/")
        if stem in routes or f"{stem}/" in routes:
            continue
        if any(r.startswith(stem.rsplit("/", 1)[0]) for r in routes if "{" in r):
            continue
        missing.append(path)

    assert not missing, f"emails link to routes that do not exist: {missing}"
