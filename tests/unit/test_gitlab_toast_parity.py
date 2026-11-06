"""Toast parity: our .toast must match @gitlab/ui's toast.scss.

Two things were wrong and they pulled in opposite directions:

* The chip read --surface-strong, which is gray-800 in dark but gray-50 in
  light - so the light-theme toast was a near-white box. GitLab's .gl-toast
  paints --gl-feedback-strong-background-color, the same dark chip in both
  themes.
* Its border colour was declared without a terminating semicolon, so the
  custom property swallowed the following line and resolved to garbage.
  GitLab's toast has no border at all.
"""

import re
from pathlib import Path

import pytest

CSS_DIR = Path(__file__).resolve().parents[2] / "src/app/templates/static/css"
TOASTS = (CSS_DIR / "toasts.css").read_text(encoding="utf-8")


def _strip_comments(css: str) -> str:
    """Rules only. Several of these rules explain a rejected token by name in
    a comment, which a bare substring check would read as a declaration."""
    return re.sub(r"/\*.*?\*/", "", css, flags=re.S)


def _block(css: str, selector: str) -> str:
    m = re.search(rf"(?m)^{re.escape(selector)}\s*\{{(.*?)\}}", css, re.S)
    assert m, f"{selector} not found"
    return _strip_comments(m.group(1))


@pytest.fixture(scope="module")
def toast() -> str:
    return _block(TOASTS, ".toast")


@pytest.fixture(scope="module")
def container() -> str:
    return _block(TOASTS, ".toast-container")


def test_chip_is_the_feedback_strong_surface(toast: str) -> None:
    """The one token @gitlab/ui documents for a toast, and it does not move
    between themes."""
    assert "--_toast-bg: var(--gl-feedback-strong-bg)" in toast
    assert "--surface-strong" not in toast, (
        "--surface-strong is gray-50 in light, which makes the toast white"
    )


def test_toast_has_no_border(toast: str) -> None:
    assert re.search(r"(?m)^\s*border:\s*0;", toast), ".gl-toast declares no border"


def test_toast_width_is_one_size_for_the_whole_stack(container: str, toast: str) -> None:
    """A DELIBERATE divergence from GitLab - do not "fix" it back.

    GitLab sizes each toast to its content up to $toast-max-width (586px), so a
    stack of them is a ragged column of different widths. This app fixes the
    width on the CONTAINER and gives every toast `width: 100%`, so the stack is
    one steady size and a new toast does not resize the ones already on screen.
    Same standing as the light-mode toast: a requested divergence, recorded
    rather than reverted.
    """
    assert "width: min(24rem" in container, "the container sets the one width"
    assert "width: 100%" in toast, "each toast fills that width rather than its content"


def test_toast_uses_the_shadow_md_colour(toast: str) -> None:
    """gl-shadow-md is three layers over --gl-shadow-color-default."""
    assert toast.count("var(--gl-shadow-color-default)") == 3


def test_toast_has_no_hover_elevation() -> None:
    """GitLab animates colour, never elevation - see the motion inventory."""
    assert ".toast:hover" not in TOASTS


def test_container_insets_match_the_toaster(container: str) -> None:
    """.b-toaster-bottom-left: spacing-6 inset, spacing-4 stack gap."""
    assert "bottom: var(--gl-spacing-6)" in container
    assert "var(--gl-spacing-6)" in container
    assert "gap: var(--gl-spacing-4)" in container


def test_no_custom_property_is_missing_its_semicolon() -> None:
    """A custom property without a trailing `;` swallows the next declaration
    and resolves to an invalid value - silently, with no parse error. That is
    exactly how the toast border died, so guard the whole file.
    """
    offenders = [
        m.group(0).strip() for m in re.finditer(r"--[\w-]+\s*:[^;{}]*?\n\s*--[\w-]+\s*:", TOASTS)
    ]
    assert not offenders, f"custom property not terminated by ';': {offenders}"
