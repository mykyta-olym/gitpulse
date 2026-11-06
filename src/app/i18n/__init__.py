"""Application i18n helpers (English + Slovak).

Catalog entries: see catalogs/sk.json (1840 entries)
"""

import contextvars
import json
import json as _json
import re
from contextlib import suppress
from functools import lru_cache
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from fastapi import Request
from jinja2 import Environment, pass_context
from markupsafe import Markup
from starlette.responses import Response

from app.i18n.gl_markdown import linkify_gl_refs, render_gl_description

SUPPORTED_LOCALES: tuple[str, ...] = ("sk", "en")
DEFAULT_LOCALE = "sk"
SOURCE_LOCALE = "en"
LOCALE_COOKIE_NAME = "gp_lang"
LOCALE_QUERY_PARAM = "lang"
LOCALE_COOKIE_MAX_AGE_SECONDS = 60 * 60 * 24 * 365  # 1 year
LOCALE_LABELS = {
    "en": "English",
    "sk": "Slovenčina",
}

_CATALOG_DIR = Path(__file__).resolve().parent / "catalogs"
_SPACE_RE = re.compile(r"\s+")
_NUMBER_RE = re.compile(r"\b\d+(?:[.,]\d+)?\b")
_SHORT_LANG_RE = re.compile(r"^[a-z]{2,3}(?:[-_][a-z]{2,4})?$", re.IGNORECASE)

# Per-request locale stored via contextvars so that Jinja2 globals
# decorated with @pass_context can resolve the locale even inside
# macros imported *without* ``with context`` (where ``request`` is
# not present in the Jinja2 template context).
_current_locale_var: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "_current_locale",
    default=None,
)


@lru_cache(maxsize=64)
def normalize_locale(value: str | None) -> str | None:
    """Normalize locale values like 'sk-SK'/'sk_SK' to 'sk'.

    Pure, and asked the same handful of questions constantly - 494 times per
    dashboard render, each one a regex match and two splits over a string that
    is almost always "sk". The domain is the supported locales plus whatever a
    header offers, so the cache stays tiny.
    """
    if not value:
        return None
    raw = str(value).strip()
    if not raw or not _SHORT_LANG_RE.match(raw):
        return None
    short = raw.split("-")[0].split("_")[0].lower()
    if short in SUPPORTED_LOCALES:
        return short
    return None


@lru_cache(maxsize=4096)
def _canonical_text(text: str) -> str:
    """Collapse whitespace for catalog lookup.

    Also pure, and called once per translated phrase - the catalog is ~3 100
    keys, so the cache is bounded by the text the templates actually contain.
    """
    return _SPACE_RE.sub(" ", str(text).strip())


def _tokenize_numbers(text: str) -> tuple[str, list[str]]:
    """Replace numbers with positional placeholders and collect originals."""
    values: list[str] = []

    def _repl(match: re.Match[str]) -> str:
        idx = len(values)
        values.append(match.group(0))
        return f"__N{idx}__"

    tokenized = _NUMBER_RE.sub(_repl, text)
    return tokenized, values


def _detokenize_numbers(text: str, values: list[str]) -> str:
    result = text
    for idx, value in enumerate(values):
        result = result.replace(f"__N{idx}__", value)
    return result


@lru_cache(maxsize=8)
def get_catalog(locale: str) -> dict[str, str]:
    """Load locale catalog (phrase -> translation)."""
    normalized = normalize_locale(locale) or DEFAULT_LOCALE
    if normalized == SOURCE_LOCALE:
        return {}

    path = _CATALOG_DIR / f"{normalized}.json"
    if not path.exists():
        return {}

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}

    catalog: dict[str, str] = {}
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(key, str) and isinstance(value, str):
                catalog[_canonical_text(key)] = value
    return catalog


@lru_cache(maxsize=8)
def _get_pattern_catalog(locale: str) -> dict[str, str]:
    """Build signature catalog for dynamic phrases that include numbers."""
    patterns: dict[str, str] = {}
    for src, translated in get_catalog(locale).items():
        src_sig, src_values = _tokenize_numbers(src)
        if not src_values:
            continue
        translated_sig, _ = _tokenize_numbers(translated)
        patterns[src_sig] = translated_sig
    return patterns


def translate_text(locale: str, text: str, **kwargs: Any) -> str:
    """Translate a phrase for the given locale, falling back to source text."""
    original = str(text)
    canonical = _canonical_text(original)
    if not canonical:
        return original

    normalized = normalize_locale(locale) or DEFAULT_LOCALE
    if normalized == SOURCE_LOCALE:
        translated = canonical
    else:
        catalog = get_catalog(normalized)
        _found = catalog.get(canonical)
        if _found is not None:
            translated = _found
        else:
            signature, values = _tokenize_numbers(canonical)
            pattern = _get_pattern_catalog(normalized).get(signature)
            translated = _detokenize_numbers(pattern, values) if pattern is not None else canonical

    if kwargs:
        with suppress(KeyError, ValueError):
            translated = translated.format(**kwargs)

    if original == canonical:
        return translated

    # Preserve surrounding whitespace from the original text node/attribute.
    return original.replace(canonical, translated, 1)


def _parse_accept_language(value: str) -> list[str]:
    candidates: list[tuple[float, str]] = []
    for part in value.split(","):
        segment = part.strip()
        if not segment:
            continue
        lang_part = segment
        quality = 1.0
        if ";" in segment:
            lang_part, *params = [item.strip() for item in segment.split(";")]
            for param in params:
                if not param.lower().startswith("q="):
                    continue
                try:
                    quality = float(param[2:].strip())
                except ValueError:
                    quality = 1.0
        normalized = normalize_locale(lang_part)
        if normalized:
            candidates.append((quality, normalized))

    candidates.sort(key=lambda item: item[0], reverse=True)
    return [locale for _, locale in candidates]


def resolve_locale(request: Request) -> str:
    """Resolve active locale from query, cookie, headers, then fallback."""
    state_locale = getattr(request.state, "locale", None)
    normalized_state = normalize_locale(state_locale) if state_locale else None
    if normalized_state:
        return normalized_state

    query_locale = normalize_locale(request.query_params.get(LOCALE_QUERY_PARAM))
    if query_locale:
        return query_locale

    cookie_locale = normalize_locale(request.cookies.get(LOCALE_COOKIE_NAME))
    if cookie_locale:
        return cookie_locale

    accept_language = request.headers.get("Accept-Language", "")
    for locale in _parse_accept_language(accept_language):
        if locale in SUPPORTED_LOCALES:
            return locale

    return DEFAULT_LOCALE


def set_locale_cookie(response: Response, locale: str, *, secure: bool = False) -> None:
    """Persist selected locale in cookie."""
    normalized = normalize_locale(locale) or DEFAULT_LOCALE
    response.set_cookie(
        key=LOCALE_COOKIE_NAME,
        value=normalized,
        max_age=LOCALE_COOKIE_MAX_AGE_SECONDS,
        path="/",
        secure=secure,
        httponly=False,
        samesite="lax",
    )


def safe_redirect_target(
    request: Request,
    target: str | None,
    *,
    fallback: str = "/dashboard/",
) -> str:
    """Allow only local redirects to prevent open-redirect issues.

    The judgement has to be made on the address a BROWSER will resolve, not on
    the characters as typed. Browsers normalise backslashes to forward slashes
    in the authority position and drop tab, CR and LF from a URL before parsing
    it - so `/\\evil.example` navigates to `https://evil.example` while reading,
    to a naive check, as an ordinary local path beginning with one slash. That
    was a working open redirect out of the sign-in page.
    """
    if not target:
        return fallback

    raw = str(target).strip()
    if not raw:
        return fallback

    # What the browser will see. Do this BEFORE any decision, or the decision is
    # about a different address than the one that gets loaded.
    raw = raw.replace("\\", "/")
    raw = raw.translate({0x09: None, 0x0A: None, 0x0D: None})
    if not raw:
        return fallback

    parsed = urlparse(raw)
    if parsed.scheme or parsed.netloc:
        req = request.url
        if parsed.netloc and parsed.netloc != req.netloc:
            return fallback
        path = parsed.path or fallback
        query = f"?{parsed.query}" if parsed.query else ""
        raw = f"{path}{query}"
        # A scheme-only target ("https:somewhere") leaves a bare relative path,
        # which resolves against the current directory rather than the site
        # root - not an escape, but not what anybody meant either.
        return raw if raw.startswith("/") else f"/{raw.lstrip('/')}"

    # `///x` is `//x` to a browser once the empty authority collapses, so ask
    # about any run of leading slashes rather than exactly two.
    if raw.startswith("//"):
        return fallback
    if not raw.startswith("/"):
        raw = f"/{raw}"
    return raw


def _locale_options() -> list[dict[str, str]]:
    return [{"code": code, "label": LOCALE_LABELS.get(code, code)} for code in SUPPORTED_LOCALES]


def get_template_i18n_context(request: Request) -> dict[str, Any]:
    """Context processor for Jinja templates."""
    from app.config import get_settings

    locale = resolve_locale(request)
    request.state.locale = locale
    _current_locale_var.set(locale)

    path_with_query = request.url.path
    if request.url.query:
        path_with_query = f"{path_with_query}?{request.url.query}"

    settings = get_settings()
    return {
        "current_locale": locale,
        "supported_locales": _locale_options(),
        "current_path_with_query": path_with_query,
        "feature_support_forms": settings.feature_support_forms,
        "observability_enabled": bool(settings.prometheus_url),
        "feature_event_pipeline": settings.feature_event_pipeline,
        "feature_multi_tenant": settings.feature_multi_tenant,
        "feature_llm_suggestions": settings.llm_analysis_enabled,
        "feature_classroom_assistant": settings.feature_classroom_assistant,
        # The catalogue is NOT in here any more. Inlined, it was 205KB raw and
        # about ninety per cent of what a compressed page weighed, re-sent on
        # every full load because inline content has no URL to cache. It is
        # identical for every reader on a locale, so it ships as a
        # content-hashed file that the browser keeps until the translations
        # change; this island now carries only which locale to read it as.
        "i18n_client_config": {
            "locale": locale,
            "default_locale": DEFAULT_LOCALE,
            "source_locale": SOURCE_LOCALE,
        },
        "i18n_catalog_url": _catalog_url(locale),
    }


def _catalog_url(locale: str) -> str | None:
    """Cache-busted URL of the client catalogue, or None when there is none.

    The source locale has no catalogue (phrases are authored in it), and a
    locale whose file was never built must not leave a 404 in the page.
    """
    if locale == SOURCE_LOCALE:
        return None
    from app.assets import is_served, static_url

    rel = f"js/i18n-catalog-{locale}.js"
    if not is_served(rel):
        return None
    return static_url(rel)


@pass_context
def _jinja_translate(context: dict[str, Any], text: str, **kwargs: Any) -> str:
    request = context.get("request")
    if isinstance(request, Request):
        locale = resolve_locale(request)
    else:
        # Fallback for macros imported without ``with context`` where
        # the Jinja2 context does not contain ``request``.
        locale = _current_locale_var.get() or DEFAULT_LOCALE
    return translate_text(locale, text, **kwargs)


def _tojson_attr(value: object) -> str:
    """Serialize *value* as JSON escaped for use in HTML attributes.

    Unlike the built-in ``|tojson`` filter (which returns ``Markup``),
    this returns a plain ``str`` so that Jinja2 auto-escaping converts
    ``"`` -> ``&#34;`` etc., making it safe inside ``x-data="..."``.

    ``ensure_ascii=False`` keeps non-ASCII characters (em-dash ``-``,
    accented Slovak letters, ...) as their actual UTF-8 codepoints in the
    attribute payload. With the default ``ensure_ascii=True`` the
    em-dash is emitted as ``\\u2014`` - a JSON-valid escape that JS
    re-evaluates correctly - but in a few translation keys the literal
    ``u2014`` (without the leading backslash) was being rendered to
    the user, suggesting that some downstream pass on the attribute
    string was stripping the backslash. Emitting raw UTF-8 sidesteps
    the issue entirely; Jinja autoescape only touches ``<>&"'`` so the
    em-dash byte sequence reaches the browser intact.
    """
    return _json.dumps(
        value,
        separators=(",", ":"),
        sort_keys=True,
        ensure_ascii=False,
    )


def _pretty_json(value: object) -> Markup:
    """Pretty-print *value* as JSON with ``ensure_ascii=False``.

    Unlike ``|tojson``, this keeps human-readable characters like
    apostrophes (``'``) instead of escaping them to ``\\u0027``.
    The result is wrapped in ``Markup`` so Jinja2 won't double-escape it.
    Only ``<``, ``>``, and ``&`` are escaped for HTML safety.
    """
    raw = _json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True)
    safe = raw.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return Markup(safe)


def _force_escape(value: object) -> str:
    """Force HTML-escape a value, even if it is already ``Markup``.

    The built-in ``|e`` filter (``markupsafe.escape``) is a no-op on
    ``Markup`` objects because it assumes they are already safe.  This
    filter first unwraps any ``Markup`` to a plain ``str`` so that
    Jinja2 auto-escaping converts ``"`` -> ``&#34;`` etc., making it
    safe for use inside HTML attribute values.
    """
    if isinstance(value, Markup):
        # Drop the Markup wrapper -> plain str -> auto-escaping will kick in
        return str.__str__(value)
    return str(value)


def register_jinja_i18n(env: Environment) -> None:
    """Register template-level translation helper and custom filters."""

    # jinja2 stubs type env.globals' value union too narrowly
    env.globals["t"] = _jinja_translate  # pyrefly: ignore[unsupported-operation]
    env.filters["tojson_attr"] = _tojson_attr
    env.filters["pretty_json"] = _pretty_json
    env.filters["force_escape"] = _force_escape

    # The GitLab base URL is a template global that may be set after this
    # runs, so the text filters read it on every call.
    def _linkify(
        text: str | None,
        project_path: str = "",
        username_map: dict[str, str] | None = None,
    ) -> Markup:
        gl_base = str(env.globals.get("gitlab_url") or "")
        return linkify_gl_refs(text, project_path, username_map, gl_base=gl_base)

    def _describe(
        text: str | None,
        project_path: str = "",
        username_map: dict[str, str] | None = None,
        student_url_map: dict[str, str] | None = None,
    ) -> Markup:
        gl_base = str(env.globals.get("gitlab_url") or "")
        return render_gl_description(
            text, project_path, username_map, student_url_map, gl_base=gl_base
        )

    env.filters["linkify_gl_refs"] = _linkify
    env.filters["render_gl_description"] = _describe


__all__ = [
    "DEFAULT_LOCALE",
    "LOCALE_COOKIE_NAME",
    "LOCALE_LABELS",
    "LOCALE_QUERY_PARAM",
    "SOURCE_LOCALE",
    "SUPPORTED_LOCALES",
    "_current_locale_var",
    "get_catalog",
    "get_template_i18n_context",
    "normalize_locale",
    "register_jinja_i18n",
    "resolve_locale",
    "safe_redirect_target",
    "set_locale_cookie",
    "translate_text",
]
