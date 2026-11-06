"""A payload the app cannot parse is a 422, not a 500.

`WebhookPayload` is described as permissive, and it is - about EXTRA fields. The
nested ids are still required (`user.id`, `project.id`, `object_attributes.id`),
so a delivery shaped even slightly differently raised a bare `ValidationError`
out of `model_validate` - the one path in that function that did not describe its
own rejection, while the JSON parse, the missing `project.id` and the non-integer
`project.id` all raise a described 422 right beside it.

The cost of the difference: the error boundary logs an unhandled crash, the
caller gets "Internal Server Error", and GitLab treats 5xx as "try again" and
redelivers the same unusable payload for 24 hours.

Reproduced against the running app before the fix - a payload without `user.id`
returned 500 with `error_boundary_caught_unhandled` in the log - and 422
afterwards.

The message names the failing FIELDS and not their values: a webhook body
carries student names, emails and commit messages, and none of that belongs in
an error string that GitLab stores in its own delivery log.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

WEBHOOKS = Path(__file__).resolve().parents[2] / "src/app/api/webhooks.py"


@pytest.fixture(scope="module")
def src() -> str:
    return WEBHOOKS.read_text(encoding="utf-8")


def test_the_model_validation_is_guarded(src: str) -> None:
    guarded = re.search(
        r"try:\s*\n\s*payload = WebhookPayload\.model_validate\(payload_dict\)\s*\n"
        r"\s*except ValidationError",
        src,
    )
    assert guarded, "a payload that does not match the model raises straight out again"


def test_it_answers_unprocessable(src: str) -> None:
    handler = src.split("except ValidationError", 1)[1][:400]
    assert "raise_unprocessable" in handler, (
        "the rejection must be a 4xx: a 5xx makes GitLab retry an unusable payload for a day"
    )


def test_it_names_the_fields_and_not_the_values(src: str) -> None:
    handler = src.split("except ValidationError", 1)[1][:400]
    assert 'error["loc"]' in handler, "the message does not say WHICH field was wrong"
    for leak in ("exc.errors()[0]", "input_value", "str(exc)", "{exc}"):
        assert leak not in handler, (
            f"{leak} puts the payload's own values in the error message - a webhook body "
            "carries student data"
        )
