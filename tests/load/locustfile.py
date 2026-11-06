"""Locust load test for webhook ingestion.

Run with:
    pip install -e ".[load]"
    locust -f tests/load/locustfile.py --host http://localhost:8000

Or headless mode:
    locust -f tests/load/locustfile.py --host http://localhost:8000 \
           --headless -u 100 -r 10 -t 60s --csv=results

This simulates GitLab webhook traffic patterns for load testing
the webhook ingestion endpoint.
"""

import hashlib
import json
import secrets
import time
import uuid
from typing import Any, cast

from locust import HttpUser, between, task

# Sample payloads (embedded for portability)
PUSH_EVENT_TEMPLATE = {
    "object_kind": "push",
    "event_name": "push",
    "before": "0" * 40,
    "after": "a" * 40,
    "ref": "refs/heads/main",
    "checkout_sha": "a" * 40,
    "user_id": 42,
    "user_name": "Test User",
    "user_username": "testuser",
    "user_email": "test@example.com",
    "user_avatar": "https://example.com/avatar.png",
    "project_id": 123,
    "project": {
        "id": 123,
        "name": "test-project",
        "web_url": "https://gitlab.example.com/test/project",
        "git_ssh_url": "git@gitlab.example.com:test/project.git",
        "git_http_url": "https://gitlab.example.com/test/project.git",
        "namespace": "test",
        "path_with_namespace": "test/project",
        "default_branch": "main",
    },
    "commits": [],
    "total_commits_count": 0,
}

MR_EVENT_TEMPLATE = {
    "object_kind": "merge_request",
    "event_type": "merge_request",
    "user": {"id": 42, "name": "Test User", "username": "testuser"},
    "project": {
        "id": 123,
        "name": "test-project",
        "path_with_namespace": "test/project",
    },
    "object_attributes": {
        "id": 1,
        "iid": 1,
        "title": "Test MR",
        "state": "opened",
        "action": "open",
        "source_branch": "feature",
        "target_branch": "main",
        "source_project_id": 123,
        "target_project_id": 123,
        "author_id": 42,
        "created_at": "2025-01-30 00:00:00 UTC",
        "updated_at": "2025-01-30 00:00:00 UTC",
    },
}

NOTE_EVENT_TEMPLATE = {
    "object_kind": "note",
    "event_type": "note",
    "user": {"id": 42, "name": "Test User", "username": "testuser"},
    "project_id": 123,
    "project": {
        "id": 123,
        "name": "test-project",
        "path_with_namespace": "test/project",
    },
    "object_attributes": {
        "id": 1,
        "note": "Test comment",
        "noteable_type": "MergeRequest",
        "author_id": 42,
        "created_at": "2025-01-30 00:00:00 UTC",
        "updated_at": "2025-01-30 00:00:00 UTC",
        "project_id": 123,
        "noteable_id": 1,
        "system": False,
        "discussion_id": "abc123",
    },
}

PIPELINE_EVENT_TEMPLATE = {
    "object_kind": "pipeline",
    "object_attributes": {
        "id": 1,
        "iid": 1,
        "ref": "main",
        "sha": "a" * 40,
        "source": "push",
        "status": "success",
        "stages": ["lint", "test", "build"],
        "created_at": "2025-01-30 00:00:00 UTC",
        "finished_at": "2025-01-30 00:10:00 UTC",
    },
    "user": {"id": 42, "name": "Test User", "username": "testuser"},
    "project": {
        "id": 123,
        "name": "test-project",
        "path_with_namespace": "test/project",
    },
    "builds": [],
}


def generate_unique_payload(template: dict[str, Any], seq: int) -> dict[str, Any]:
    """Generate a unique payload from template."""
    payload = cast(dict[str, Any], json.loads(json.dumps(template)))

    # Generate unique identifiers
    unique_sha = hashlib.sha256(f"{seq}-{time.time()}".encode()).hexdigest()[:40]

    if "after" in payload:
        payload["after"] = unique_sha
        payload["checkout_sha"] = unique_sha

    if "object_attributes" in payload:
        payload["object_attributes"]["id"] = 10000 + seq
        if "iid" in payload["object_attributes"]:
            payload["object_attributes"]["iid"] = seq
        payload["object_attributes"]["updated_at"] = (
            f"2025-01-30 {seq % 24:02d}:{seq % 60:02d}:00 UTC"
        )
        if "sha" in payload["object_attributes"]:
            payload["object_attributes"]["sha"] = unique_sha

    return payload


class WebhookUser(HttpUser):
    """Simulates GitLab sending webhooks."""

    # Wait 0.2-1.0 seconds between tasks (keeps RPS above pipeline threshold)
    wait_time = between(0.2, 1.0)

    # Webhook token (must match registered project)
    webhook_token = "test-webhook-token"

    # Sequence counter for unique payloads
    seq = 0

    def on_start(self):
        """Initialize user session."""
        self.seq = secrets.randbelow(100000) + 1

    def _send_webhook(self, payload: dict[str, Any], event_type: str) -> None:
        """Send a webhook request."""
        self.seq += 1
        unique_payload = generate_unique_payload(payload, self.seq)

        headers = {
            "Content-Type": "application/json",
            "X-Gitlab-Token": self.webhook_token,
            "X-Gitlab-Event": event_type,
            "X-Gitlab-Event-UUID": str(uuid.uuid4()),
            "X-Gitlab-Delivery": str(uuid.uuid4()),
        }

        with self.client.post(
            "/api/v1/webhooks/gitlab",
            json=unique_payload,
            headers=headers,
            name=f"webhook/{event_type}",
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if data.get("status") in ("accepted", "duplicate"):
                    response.success()
                else:
                    response.failure(f"Unexpected status: {data.get('status')}")
            elif response.status_code == 404:
                # Project not registered - expected in load test without DB
                response.success()
            elif response.status_code == 401:
                # Invalid token - expected without proper setup
                response.success()
            else:
                response.failure(f"HTTP {response.status_code}: {response.text[:100]}")

    @task(30)
    def push_event(self):
        """Send push event (most common - 30% weight)."""
        self._send_webhook(PUSH_EVENT_TEMPLATE, "Push Hook")

    @task(25)
    def merge_request_event(self):
        """Send MR event (25% weight)."""
        self._send_webhook(MR_EVENT_TEMPLATE, "Merge Request Hook")

    @task(20)
    def note_event(self):
        """Send note/comment event (20% weight)."""
        self._send_webhook(NOTE_EVENT_TEMPLATE, "Note Hook")

    @task(15)
    def pipeline_event(self):
        """Send pipeline event (15% weight)."""
        self._send_webhook(PIPELINE_EVENT_TEMPLATE, "Pipeline Hook")

    @task(10)
    def burst_push_events(self):
        """Simulate burst of push events (10% weight)."""
        # GitLab can send multiple pushes in quick succession
        for _ in range(5):
            self._send_webhook(PUSH_EVENT_TEMPLATE, "Push Hook")


class HeavyWebhookUser(HttpUser):
    """Simulates heavy CI/CD activity (more pipeline events)."""

    wait_time = between(0.1, 0.5)  # Faster than normal
    webhook_token = "test-webhook-token"
    seq = 0

    def on_start(self):
        self.seq = secrets.randbelow(100001) + 100000

    def _send_webhook(self, payload: dict[str, Any], event_type: str) -> None:
        self.seq += 1
        unique_payload = generate_unique_payload(payload, self.seq)

        headers = {
            "Content-Type": "application/json",
            "X-Gitlab-Token": self.webhook_token,
            "X-Gitlab-Event": event_type,
            "X-Gitlab-Event-UUID": str(uuid.uuid4()),
        }

        with self.client.post(
            "/api/v1/webhooks/gitlab",
            json=unique_payload,
            headers=headers,
            name=f"heavy/{event_type}",
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if data.get("status") in ("accepted", "duplicate"):
                    response.success()
                else:
                    response.failure(f"Unexpected status: {data.get('status')}")
            elif response.status_code == 404:
                # Project not registered - expected in load test without DB
                response.success()
            elif response.status_code == 401:
                # Invalid token - expected without proper setup
                response.success()
            else:
                response.failure(f"HTTP {response.status_code}: {response.text[:100]}")

    @task(50)
    def pipeline_event(self):
        """Heavy pipeline activity."""
        self._send_webhook(PIPELINE_EVENT_TEMPLATE, "Pipeline Hook")

    @task(30)
    def push_event(self):
        """Push events."""
        self._send_webhook(PUSH_EVENT_TEMPLATE, "Push Hook")

    @task(20)
    def merge_request_event(self):
        """MR events."""
        self._send_webhook(MR_EVENT_TEMPLATE, "Merge Request Hook")
