"""Personal preferences page, modelled on GitLab's ``/-/profile/preferences``.

Every setting here is the reader's own and applies to every role, so the page
sits behind plain ``DashboardAuth`` rather than a role gate: a student tunes
their own clock exactly the way an admin does.

The whole surface is driven by ``PREFERENCE_FIELDS`` below. The template
renders its options from the same table the POST validates against, so a value
the form can offer is by construction a value the endpoint accepts - there is
no second list to drift.
"""

from __future__ import annotations

import re
from typing import Any

from fastapi import APIRouter, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse

from app.api.dashboard._helpers import _csrf_token, _role_context, _templates
from app.dependencies import CSRFCheck, DashboardAuth, DbSession, RateLimitDep
from app.i18n import LOCALE_COOKIE_NAME, SUPPORTED_LOCALES, set_locale_cookie
from app.models.user import User

router = APIRouter()


ALL_ROLES: tuple[str, ...] = ("student", "teacher", "admin")

# Exactly "#RRGGBB". Kept strict rather than accepting the 3-digit or named
# forms: the value is echoed straight into a CSS custom property, and a lax
# pattern there is how a style-injection bug starts.
_HEX_COLOR = re.compile(r"#[0-9a-fA-F]{6}")

# The app's own diff colours - what a NULL column renders as.
DEFAULT_DIFF_REMOVED = "#dd2b0e"  # --gl-red-500
DEFAULT_DIFF_ADDED = "#108548"  # --gl-green-500

# GitLab offers Orange and Blue beside the current/default pair
# (app/assets/javascripts/profile/preferences/components/diffs_colors.vue).
SUGGESTED_DIFF_COLORS: tuple[tuple[str, str], ...] = (
    ("#d99530", "Orange"),
    ("#1f75cb", "Blue"),
    (DEFAULT_DIFF_REMOVED, "Default removal color"),
    (DEFAULT_DIFF_ADDED, "Default addition color"),
)


class Choice:
    """One selectable value, with the copy the template renders beside it.

    ``roles`` restricts who may pick it. It exists for the homepage list: the
    admin pages are real destinations, but a student who pinned one would be
    bounced by the role gate on every single sign-in, which reads as the app
    being broken rather than as a bad choice.
    """

    __slots__ = ("description", "label", "roles", "value")

    def __init__(
        self,
        value: str,
        label: str,
        description: str = "",
        roles: tuple[str, ...] = ALL_ROLES,
    ) -> None:
        self.value = value
        self.label = label
        self.description = description
        self.roles = roles

    def allowed_for(self, role: str) -> bool:
        return role in self.roles


class PreferenceField:
    """A single persisted preference and everything the page needs to draw it.

    ``choices`` doubles as the validation whitelist for a "choice" field: a
    value is rejected unless it is one of them, which is why the template must
    never invent an option of its own. "bool" and "color" fields carry no
    choices - a colour is checked against a pattern instead.
    """

    __slots__ = ("choices", "default", "kind", "name")

    def __init__(
        self,
        name: str,
        kind: str,
        default: Any,
        choices: tuple[Choice, ...] = (),
    ) -> None:
        self.name = name
        self.kind = kind  # "choice" | "bool" | "color"
        self.default = default
        self.choices = choices

    def choices_for(self, role: str) -> tuple[Choice, ...]:
        """The options this role may actually be offered."""
        return tuple(c for c in self.choices if c.allowed_for(role))

    def coerce(self, raw: Any, role: str = "admin") -> Any | None:
        """Return the value to store, or None when ``raw`` is not acceptable.

        ``role`` defaults to the most permissive one so pure value checks read
        naturally; the endpoint always passes the real role, which is what
        stops a student pinning a page they cannot open.
        """
        if self.kind == "bool":
            if isinstance(raw, bool):
                return raw
            # An unchecked checkbox posts nothing at all; a checked one posts
            # "true"/"on" depending on the widget. Anything else is a bug, not
            # a user choice, so it is refused rather than coerced to False.
            if isinstance(raw, str) and raw.lower() in {"true", "on", "1"}:
                return True
            if isinstance(raw, str) and raw.lower() in {"false", "off", "0"}:
                return False
            return None
        if self.kind == "color":
            # "" is a real answer: it clears the override and returns the row
            # to the app's own green/red.
            if raw == "" or raw is None:
                return ""
            if not isinstance(raw, str) or not _HEX_COLOR.fullmatch(raw.strip()):
                return None
            # Normalised so "#ABC123" and "#abc123" are one stored value.
            return raw.strip().lower()
        if not isinstance(raw, str):
            return None
        return raw if any(c.value == raw for c in self.choices_for(role)) else None


def _locale_choices() -> tuple[Choice, ...]:
    """Languages the app actually ships, plus "follow my browser".

    Built from SUPPORTED_LOCALES so adding a translation cannot leave the
    preferences page offering a language the app has no catalogue for.
    """
    names = {"sk": "Slovenčina", "en": "English"}
    return (
        # No description: select_field renders (value, label) only, so one here
        # would never reach the reader. The field's help_text carries the
        # explanation instead.
        Choice("", "System default"),
        *(Choice(code, names.get(code, code.upper())) for code in SUPPORTED_LOCALES),
    )


PREFERENCE_FIELDS: tuple[PreferenceField, ...] = (
    PreferenceField(
        "theme_preference",
        "choice",
        "system",
        (
            Choice("light", "Light"),
            Choice("dark", "Dark"),
            Choice("system", "System"),
        ),
    ),
    PreferenceField(
        "accent_theme",
        "choice",
        "default",
        (
            Choice("default", "Default"),
            Choice("indigo", "Indigo"),
            Choice("blue", "Blue"),
            Choice("green", "Green"),
            Choice("red", "Red"),
            Choice("gray", "Gray"),
        ),
    ),
    PreferenceField(
        # GitLab's "Choose a highlight color scheme for viewing and editing
        # code." Real here: app/i18n highlights fenced code blocks with Pygments
        # and each scheme redefines the ten token colours in cards.css.
        "syntax_theme",
        "choice",
        "dark",
        (
            # GitLab's own set and GitLab's own order, from
            # lib/gitlab/color_schemes.rb: Light, Dark, Solarized Light,
            # Solarized Dark, Monokai, Dracula, None.
            #
            # "Default" is gone. It was a seventh palette that no upstream
            # scheme corresponds to, it duplicated "Dark" closely enough that
            # the two previews read as the same swatch, and it left the list
            # one short of GitLab's while still missing Dracula. A stored
            # "default" is no longer offered, so hydration degrades it to this
            # field's default - "dark", the palette it was a copy of.
            Choice("light", "Light"),
            Choice("dark", "Dark"),
            Choice("solarized-light", "Solarized Light"),
            Choice("solarized-dark", "Solarized Dark"),
            Choice("monokai", "Monokai"),
            Choice("dracula", "Dracula"),
            Choice("none", "None"),
        ),
    ),
    PreferenceField(
        "layout_width",
        "choice",
        "fixed",
        (
            Choice("fixed", "Fixed", "Content will be a maximum of 1280 pixels wide."),
            Choice("fluid", "Fluid", "Content will span 100% of the page width."),
        ),
    ),
    PreferenceField("keyboard_shortcuts_enabled", "bool", True),
    # Every value here is a REAL navigable page taken from the sidebar, not an
    # invented name. "activity" looked like an obvious third option and is not
    # one: /dashboard/activity is an HTML *fragment* the feed polls, so landing
    # on it would serve a bare partial with no chrome.
    # "My courses" is absent for a different reason: it is /dashboard/#my-courses,
    # and a fragment never reaches the server - so redirecting /dashboard/ there
    # would resolve back to /dashboard/ and loop forever.
    PreferenceField(
        "default_homepage",
        "choice",
        "dashboard",
        (
            Choice("dashboard", "Dashboard"),
            Choice("support", "Support"),
            Choice("admin-courses", "Courses (management)", roles=("teacher", "admin")),
            Choice("admin-system", "System status", roles=("teacher", "admin")),
            Choice("admin-users", "Users", roles=("admin",)),
        ),
    ),
    # -- GitPulse's own, not copied from GitLab --------------------------
    # The per-table "Per page" control and the sidebar toggle already exist;
    # they just forget. These are the account-level DEFAULT, and a per-table
    # choice still wins for that table.
    PreferenceField(
        "default_page_size",
        "choice",
        "50",
        (
            Choice("25", "25 per page"),
            Choice("50", "50 per page"),
            Choice("100", "100 per page"),
            Choice("all", "Show all"),
        ),
    ),
    PreferenceField("sidebar_collapsed", "bool", False),
    # Which period a page with a period selector opens on - the way
    # default_homepage picks the page. "remembered" carries a pick to every page
    # until the next term; with the others a pick changes only its own page.
    PreferenceField(
        "default_period",
        "choice",
        "remembered",
        (
            Choice("remembered", "The period I picked last"),
            Choice("newest", "The newest term with my courses"),
            Choice("current", "The term running now"),
            Choice("all", "All periods"),
        ),
    ),
    PreferenceField("preferred_language", "choice", "", _locale_choices()),
    PreferenceField(
        "first_day_of_week",
        "choice",
        "system",
        (
            Choice("system", "System default"),
            Choice("monday", "Monday"),
            Choice("sunday", "Sunday"),
            Choice("saturday", "Saturday"),
        ),
    ),
    PreferenceField("diff_color_removed", "color", ""),
    PreferenceField("diff_color_added", "color", ""),
    # Notifications. Each maps to a category enqueue_email() is called with,
    # and is enforced server-side in that function - not merely hidden here.
    PreferenceField("notify_tickets", "bool", True),
    PreferenceField("notify_ticket_queue", "bool", True),
    PreferenceField("notify_courses", "bool", True),
    PreferenceField("notify_account", "bool", True),
    PreferenceField("use_relative_times", "bool", True),
    PreferenceField(
        "time_format",
        "choice",
        "system",
        (
            Choice("system", "System"),
            Choice("12h", "12-hour: 2:34 PM"),
            Choice("24h", "24-hour: 14:34"),
        ),
    ),
)

_FIELDS_BY_NAME = {f.name: f for f in PREFERENCE_FIELDS}

# default_homepage value -> the path it lands on. Kept beside the choices so a
# new option cannot be offered without a destination; a test pins the two
# together. "dashboard" maps to None because it IS /dashboard/ - redirecting it
# to itself would loop.
HOMEPAGE_PATHS: dict[str, str | None] = {
    "dashboard": None,
    "support": "/dashboard/support",
    "admin-courses": "/dashboard/admin/courses",
    "admin-system": "/dashboard/admin/system",
    "admin-users": "/dashboard/admin/users",
}


def homepage_redirect_for(role: str, preference: str | None) -> str | None:
    """Where this user's dashboard root should land, or None to stay put.

    Re-checks the role rather than trusting the stored value: a teacher who
    pinned an admin page and was later demoted must fall back to the dashboard
    instead of being bounced by the role gate on every sign-in.
    """
    if not preference or preference == "dashboard":
        return None
    field = _FIELDS_BY_NAME["default_homepage"]
    if not any(c.value == preference for c in field.choices_for(role)):
        return None
    return HOMEPAGE_PATHS.get(preference)


def current_preferences(user: User) -> dict[str, Any]:
    """The user's stored values, falling back to each field's default."""
    values: dict[str, Any] = {}
    for field in PREFERENCE_FIELDS:
        stored = getattr(user, field.name, None)
        if field.kind == "color" or field.name == "preferred_language":
            # NULL is a real, meaningful value here ("follow the browser"), so
            # it maps to the empty-string choice rather than to a default.
            values[field.name] = stored or ""
        elif field.kind == "choice":
            # A stored value that is no longer offered - an older release wrote
            # it, or the option was retired, as "default" was from syntax_theme
            # - falls back to the field's default. Echoing it back instead
            # renders a radio group with NOTHING selected, so the page cannot
            # say what is in force and saving is the only way to find out.
            allowed = {choice.value for choice in field.choices}
            values[field.name] = stored if stored in allowed else field.default
        else:
            values[field.name] = field.default if stored is None else stored
    return values


@router.get("/preferences", response_class=HTMLResponse)
async def preferences_page(request: Request, auth: DashboardAuth, db: DbSession) -> Response:
    """Render the preferences page for the signed-in user."""
    from app.dependencies import get_current_user

    user = await get_current_user(auth, db)

    return _templates(request).TemplateResponse(
        request,
        "preferences.html",
        {
            "request": request,
            "fields": PREFERENCE_FIELDS,
            "prefs": current_preferences(user),
            # "Restore defaults" resets to the same values a brand-new account
            # gets, read from the field table rather than restated in JS.
            "defaults": {f.name: f.default for f in PREFERENCE_FIELDS},
            "suggested_diff_colors": SUGGESTED_DIFF_COLORS,
            "csrf_token": _csrf_token(auth),
            **_role_context(auth),
        },
    )


@router.post("/api/preferences", response_class=JSONResponse)
async def update_preferences(
    request: Request,
    auth: DashboardAuth,
    db: DbSession,
    _csrf: CSRFCheck,
    _rl: RateLimitDep,
) -> Response:
    """Persist a partial update of the signed-in user's preferences.

    Only keys present in the payload are touched, and only if they name a
    field in ``PREFERENCE_FIELDS`` - there is no ``setattr`` over arbitrary
    input, so a crafted body cannot reach ``role``, ``is_active`` or any other
    column.
    """
    from app.dependencies import get_current_user

    try:
        payload = await request.json()
    except Exception:
        return JSONResponse({"error": "invalid_json"}, status_code=400)

    if not isinstance(payload, dict):
        return JSONResponse({"error": "invalid_payload"}, status_code=422)

    unknown = sorted(set(payload) - set(_FIELDS_BY_NAME))
    if unknown:
        return JSONResponse({"error": "unknown_fields", "fields": unknown}, status_code=422)

    # The role decides which options are legal, not just which are rendered:
    # the form is only the polite half of the check.
    role = str(_role_context(auth).get("user_role", "student"))

    resolved: dict[str, Any] = {}
    rejected: list[str] = []
    for key, raw in payload.items():
        value = _FIELDS_BY_NAME[key].coerce(raw, role)
        if value is None:
            rejected.append(key)
        else:
            resolved[key] = value

    if rejected:
        return JSONResponse(
            {"error": "invalid_values", "fields": sorted(rejected)}, status_code=422
        )

    user = await get_current_user(auth, db)
    changed = False
    for key, value in resolved.items():
        # preferred_language stores NULL, not "", for "follow the browser".
        # "" means "no override" for both the language and the diff colours,
        # and NULL is how that is stored.
        stored = None if value == "" else value
        if getattr(user, key) != stored:
            setattr(user, key, stored)
            changed = True

    if changed:
        await db.commit()

    response = JSONResponse(
        {"saved": sorted(resolved)},
        status_code=200,
        headers={"Cache-Control": "no-store"},
    )

    # Language has to reach THIS browser now, not on some later request.
    # resolve_locale() reads the cookie before it reaches any account value,
    # and deliberately so: the language switcher writes that cookie, and an
    # account value outranking it would revert the reader's explicit switch on
    # the very next request - the same flip that bit the theme preference.
    # So saving a language writes the same cookie the switcher does; the two
    # then agree instead of fighting.
    # Any default but "remembered" forgets the pick NOW, not on the next page:
    # the server reads it from this cookie (requested_period), and the
    # browser's copy is cleared by academic-period.js on the next load.
    if resolved.get("default_period", "remembered") != "remembered":
        from app.services.academic_periods import PERIOD_COOKIE

        response.delete_cookie(PERIOD_COOKIE, path="/")

    if "preferred_language" in resolved:
        chosen = resolved["preferred_language"]
        secure = request.headers.get("X-Forwarded-Proto") == "https"
        if chosen:
            set_locale_cookie(response, chosen, secure=secure)
        else:
            # "System default" - drop the pin and let the browser decide again.
            response.delete_cookie(LOCALE_COOKIE_NAME, path="/")

    return response
