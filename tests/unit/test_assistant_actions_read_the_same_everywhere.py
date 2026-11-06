"""Assistant job and activity labels stay consistent across shared views."""

from __future__ import annotations

import json
from pathlib import Path

from app.api.dashboard.home.activity import _AUDIT_LABELS

JOB_MESSAGES = Path(__file__).resolve().parents[2] / "src/app/i18n/job_messages.json"


def _job_type_labels() -> dict[str, str]:
    return json.loads(JOB_MESSAGES.read_text(encoding="utf-8"))["labels"]


def test_every_assistant_action_has_the_feeds_label_in_job_history() -> None:
    labels = _job_type_labels()
    listed = {
        action: label
        for action, label in _AUDIT_LABELS.items()
        if action.startswith("assistant.") and not action.startswith("assistant.exercise")
    }
    assert listed
    for action, label in listed.items():
        assert labels.get(action.replace(".", "_")) == label, action


def test_the_exercise_is_one_row_in_job_history() -> None:
    assert _job_type_labels()["assistant_exercise"] == "Assistant exercise"
