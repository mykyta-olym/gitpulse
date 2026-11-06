"""When the server says why, the reader is told why.

"Refresh from GitLab" on the Users page answered `400 {"message": "GitLab API
token not configured"}` and the toast said only "Failed to start enrichment".
The reason was not missing from the response - it was dropped by the client:

    showToast(t('Failed to start enrichment') || 'Failed to start enrichment: ' + err.message)

`||` short-circuits on the translated headline, so the half carrying
`err.message` could never run. The fallback that appends the reason was
unreachable in every language, including the one it was written for.

Measured after the fix, clicking the button with no token configured:
"Failed to start enrichment: GitLab API token not configured".

This pins the shape rather than the string: a headline and a reason, joined -
never a headline that shadows the reason behind `||`.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

JS = Path(__file__).resolve().parents[2] / "src/app/templates/static/js/pages/admin-users.js"

#: `t('X') || 'X: ' + something` - the shadowing shape. The left side is a
#: translated string, so the right side, which is the one carrying the reason,
#: is dead.
_SHADOWED = re.compile(r"t\?\.\('[^']+'\)\s*\|\|\s*'[^']*:\s*'\s*\+")


@pytest.fixture(scope="module")
def src() -> str:
    return JS.read_text(encoding="utf-8")


def test_the_headline_no_longer_shadows_the_reason(src: str) -> None:
    hit = _SHADOWED.search(src)
    assert not hit, (
        f"a toast falls back to a message that can never be reached: {hit.group(0) if hit else ''}"
    )


def test_the_enrichment_failure_says_what_failed(src: str) -> None:
    block = src.split("Failed to start enrichment", 1)[1][:900]
    assert "err.message" in block, "the server's reason is not read at all"
    assert re.search(r"headline\s*\+\s*':\s*'\s*\+\s*reason", src), (
        "the headline and the reason are not joined - one of them will be lost"
    )
