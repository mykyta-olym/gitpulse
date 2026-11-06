"""GlAlert parity: our .gitlab-alert must match @gitlab/ui's alert.scss.

The alert used to be painted with --gl-feedback-strong-*, which @gitlab/ui
documents as "a background associated with strong feedback like a tooltip or
toast message" - it was wearing the toast's clothes. It also drew a 2px
coloured top rule and a drop shadow, neither of which GitLab's alert has:
every --gl-alert-*-border-{top,bottom}-color in @gitlab/ui ships as
rgba(0, 0, 0, 0).
"""

import re
from pathlib import Path

import pytest

CSS_DIR = Path(__file__).resolve().parents[2] / "src/app/templates/static/css"
ALERTS = (CSS_DIR / "alerts.css").read_text(encoding="utf-8")
TOKENS = (CSS_DIR / "tokens.css").read_text(encoding="utf-8")

VARIANTS = ["neutral", "info", "success", "warning", "danger"]


def _block(css: str, selector: str) -> str:
    """The declaration body of the first rule with exactly this selector."""
    m = re.search(rf"(?m)^{re.escape(selector)}\s*\{{(.*?)\}}", css, re.S)
    assert m, f"{selector} not found"
    return m.group(1)


@pytest.fixture(scope="module")
def alert_rule() -> str:
    return _block(ALERTS, ".gitlab-alert")


def test_alert_is_not_painted_with_the_toast_token(alert_rule: str) -> None:
    assert "feedback-strong" not in alert_rule, (
        "--gl-feedback-strong-* is GitLab's tooltip/toast background, not an alert background"
    )


def test_alert_has_no_shadow(alert_rule: str) -> None:
    """GitLab's .gl-alert declares no box-shadow at any elevation."""
    assert "box-shadow" not in alert_rule


def test_alert_geometry_matches_gitlab(alert_rule: str) -> None:
    """gl-py-5 (16px) block, calc(spacing-9 + 0) = 48px inline, radius token."""
    assert "var(--gl-spacing-5) var(--gl-spacing-9)" in alert_rule
    assert "var(--gl-alert-border-radius)" in alert_rule


def test_alert_icon_is_absolutely_positioned() -> None:
    """gl-alert-icon-container is absolute at the spacing-5 inset; as a flex
    child it would push the text and break the 48px inline rhythm."""
    icon = _block(ALERTS, ".gitlab-alert-icon")
    assert "position: absolute" in icon
    assert "var(--gl-spacing-5)" in icon
    assert "var(--gl-line-height-20)" in icon


@pytest.mark.parametrize("variant", VARIANTS)
def test_alert_borders_are_transparent_in_both_themes(variant: str) -> None:
    decls = re.findall(rf"--gl-alert-{variant}-border:\s*([^;]+);", TOKENS)
    assert len(decls) == 2, f"expected a light and a dark declaration, got {decls}"
    for value in decls:
        assert "rgba(0, 0, 0, 0)" in value, (
            f"--gl-alert-{variant}-border is {value.strip()}; @gitlab/ui ships "
            "every alert border transparent"
        )


# @gitlab/ui light theme: the background carries the variant.
LIGHT_BACKGROUNDS = {
    "neutral": "--gl-gray-50",  # #ececef
    "info": "--gl-blue-50",  # #e9f3fc
    "success": "--gl-green-50",  # #ecf4ee
    "warning": "--gl-orange-50",  # #fdf1dd
    "danger": "--gl-red-50",  # #fcf1ef
}


def _values(prop: str) -> list[str]:
    """Every declared value for a custom property, whitespace-normalised."""
    return [
        re.sub(r"\s+", " ", v).strip()
        for v in re.findall(rf"{re.escape(prop)}:\s*([^;]+);", TOKENS)
    ]


@pytest.mark.parametrize(("variant", "scale_token"), LIGHT_BACKGROUNDS.items())
def test_alert_background_has_both_themes(variant: str, scale_token: str) -> None:
    """Light carries the variant in the background (a -50 tint); dark gives
    every alert background-subtle and lets the TITLE carry it instead."""
    values = _values(f"--gl-alert-{variant}-bg")
    assert len(values) == 2, f"expected a light and a dark declaration, got {values}"
    assert f"var({scale_token})" in values, (
        f"light --gl-alert-{variant}-bg should be var({scale_token})"
    )
    assert "var(--gl-background-color-subtle)" in values, (
        f"dark --gl-alert-{variant}-bg should be background-subtle"
    )


@pytest.mark.parametrize("variant", ["info", "success", "warning", "danger"])
def test_every_variant_sets_background_title_and_icon(variant: str) -> None:
    """gl-alert-variant() sets exactly these three. A variant that only moved
    a border colour is how the old rules failed."""
    for prop in (
        f"--gl-alert-{variant}-bg",
        f"--gl-alert-{variant}-title",
        f"--gl-feedback-{variant}-icon",
    ):
        assert prop in ALERTS, f"{variant} variant never references {prop}"


def test_body_text_does_not_demote_when_a_title_is_present() -> None:
    """GitLab's .gl-alert-body is text-default at the base size regardless."""
    assert ".gitlab-alert-title + .gitlab-alert-message" not in ALERTS
