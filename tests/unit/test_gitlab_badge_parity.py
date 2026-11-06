"""Badge parity: our badge tokens must match @gitlab/ui's, in BOTH themes.

The light theme already matched exactly (-100 background, -700 text). Dark did
not: @gitlab/ui INVERTS the badge in dark - a light -300 background with dark
-950 text - while ours kept the light theme's polarity (-800 background, -200
text). Every badge in the app was therefore the photographic negative of the
same badge in GitLab, which is what "the numbers don't match" meant.
"""

import re
from pathlib import Path

import pytest

TOKENS = (
    Path(__file__).resolve().parents[2] / "src/app/templates/static/css/tokens.css"
).read_text(encoding="utf-8")

# @gitlab/ui 136.3.0, tokens.css / tokens.dark.css.
# variant -> (light bg, light text, dark bg, dark text)
GITLAB_BADGES = {
    "neutral": ("gray-100", "gray-700", "gray-300", "gray-950"),
    "info": ("blue-100", "blue-700", "blue-300", "blue-950"),
    "success": ("green-100", "green-700", "green-300", "green-950"),
    "warning": ("orange-100", "orange-700", "orange-300", "orange-950"),
    "danger": ("red-100", "red-700", "red-300", "red-950"),
    "tier": ("purple-100", "purple-700", "purple-300", "purple-950"),
}


def _values(prop: str) -> list[str]:
    return [
        re.sub(r"\s+", " ", v).strip()
        for v in re.findall(rf"{re.escape(prop)}:\s*([^;]+);", TOKENS)
    ]


@pytest.mark.parametrize(("variant", "steps"), GITLAB_BADGES.items())
def test_badge_tokens_match_gitlab_in_both_themes(
    variant: str, steps: tuple[str, str, str, str]
) -> None:
    light_bg, light_text, dark_bg, dark_text = steps

    backgrounds = _values(f"--gl-badge-{variant}-bg")
    texts = _values(f"--gl-badge-{variant}-text")

    assert len(backgrounds) == 2, f"expected light + dark, got {backgrounds}"
    assert len(texts) == 2, f"expected light + dark, got {texts}"

    assert f"var(--gl-{light_bg})" in backgrounds
    assert f"var(--gl-{dark_bg})" in backgrounds
    assert f"var(--gl-{light_text})" in texts
    assert f"var(--gl-{dark_text})" in texts


@pytest.mark.parametrize("variant", list(GITLAB_BADGES))
def test_dark_badge_is_inverted(variant: str) -> None:
    """The polarity itself, stated independently of the exact steps: in dark a
    badge is a LIGHT chip carrying DARK text. Reading -800/-200 here means the
    light theme's polarity leaked into dark again."""
    backgrounds = _values(f"--gl-badge-{variant}-bg")
    texts = _values(f"--gl-badge-{variant}-text")

    assert not any("-800)" in v or "-900)" in v for v in backgrounds), (
        f"--gl-badge-{variant}-bg still has a dark chip: {backgrounds}"
    )
    assert not any("-200)" in v or "-300)" in v for v in texts), (
        f"--gl-badge-{variant}-text still has light text: {texts}"
    )


def test_every_badge_variant_is_tokenised() -> None:
    """A variant that reaches past the badge tokens to a raw colour drifts the
    moment the scale moves - .badge-teal did exactly that."""
    badges_css = (
        Path(__file__).resolve().parents[2] / "src/app/templates/static/css/badges.css"
    ).read_text(encoding="utf-8")
    rules = re.findall(r"(\.badge-[\w., -]*)\{([^}]*)\}", badges_css)
    offenders = []
    for selector, body in rules:
        if "size" in selector or selector.strip().startswith((".badge-sm", ".badge-lg")):
            continue
        for prop in ("background", "color"):
            for m in re.finditer(rf"(?m)^\s*{prop}:\s*([^;]+);", body):
                value = m.group(1)
                if "var(--gl-badge-" not in value and value.strip() != "inherit":
                    offenders.append(f"{selector.strip()} -> {prop}: {value.strip()}")
    assert not offenders, f"badge variants bypassing the badge tokens: {offenders}"
