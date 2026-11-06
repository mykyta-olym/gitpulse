"""Every delivery a real GitLab 19.4 sent passes the receiver's schema.

The fixtures were captured from a GitLab CE 19.4.2 in a local end-to-end run
of the classroom assistant. The schema typed ``object_attributes.source`` as
a string - a pipeline's source - while a merge request's is its source
project, so every merge request event was refused.
"""

import json
from pathlib import Path

import pytest

from app.schemas.webhooks import WebhookPayload

FIXTURES = Path(__file__).parents[1] / "fixtures" / "payloads" / "gitlab_19_4"
NAMES = sorted(p.stem for p in FIXTURES.glob("*.json"))


def _payload(name: str) -> dict:
    return json.loads((FIXTURES / f"{name}.json").read_text(encoding="utf-8"))["payload"]


def test_there_is_a_delivery_of_every_kind_the_app_processes() -> None:
    kinds = {_payload(name)["object_kind"] for name in NAMES}
    assert kinds >= {"push", "issue", "merge_request", "note", "pipeline"}


@pytest.mark.parametrize("name", NAMES)
def test_the_delivery_passes_the_schema(name: str) -> None:
    WebhookPayload.model_validate(_payload(name))


def test_a_merge_requests_source_is_its_project() -> None:
    payload = _payload("merge_request_open")
    assert isinstance(payload["object_attributes"]["source"], dict)
    parsed = WebhookPayload.model_validate(payload)
    assert parsed.object_attributes is not None
