"""Load test script for scale optimizations.

Tests system behavior under load with configurable:
- Request rates
- Concurrent connections
- Payload sizes
- Duration

Usage:
    # Quick test (1 minute, 50 rps)
    python scripts/load_test_scale.py --duration 60 --rps 50

    # Full load test (10 minutes, ramping to 200 rps)
    python scripts/load_test_scale.py --duration 600 --rps 200 --ramp-up 60

    # Test specific component
    python scripts/load_test_scale.py --target webhooks --duration 120 --rps 100

    # Test with backpressure monitoring
    python scripts/load_test_scale.py --monitor-backpressure --duration 300 --rps 150
"""

import argparse
import asyncio
import hashlib
import json
import random
import sys
import time
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

import httpx


@dataclass
class LoadTestConfig:
    """Load test configuration."""

    base_url: str = "http://localhost:8000"
    target: str = "webhooks"  # webhooks, api, reports, all
    duration_seconds: int = 60
    requests_per_second: int = 50
    ramp_up_seconds: int = 0
    concurrent_connections: int = 10
    timeout_seconds: float = 30.0
    webhook_secret: str = "test-secret"
    auth_token: str = ""
    monitor_backpressure: bool = False
    verbose: bool = False


@dataclass
class LoadTestResult:
    """Results from a load test run."""

    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    rate_limited_requests: int = 0
    timeout_requests: int = 0

    total_duration_seconds: float = 0.0
    avg_latency_ms: float = 0.0
    p50_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0
    p99_latency_ms: float = 0.0
    max_latency_ms: float = 0.0

    requests_per_second: float = 0.0
    error_rate: float = 0.0

    latencies: list[float] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def calculate_percentiles(self) -> None:
        """Calculate latency percentiles."""
        if not self.latencies:
            return

        sorted_latencies = sorted(self.latencies)
        n = len(sorted_latencies)

        self.avg_latency_ms = sum(sorted_latencies) / n
        self.p50_latency_ms = sorted_latencies[int(n * 0.50)]
        self.p95_latency_ms = sorted_latencies[int(n * 0.95)]
        self.p99_latency_ms = sorted_latencies[min(int(n * 0.99), n - 1)]
        self.max_latency_ms = sorted_latencies[-1]

        if self.total_duration_seconds > 0:
            self.requests_per_second = self.total_requests / self.total_duration_seconds

        if self.total_requests > 0:
            self.error_rate = self.failed_requests / self.total_requests


class WebhookPayloadGenerator:
    """Generates realistic GitLab webhook payloads."""

    def __init__(self, project_ids: list[int] | None = None):
        self.project_ids = project_ids or list(range(1000, 1020))
        self.user_ids = list(range(100, 150))

    def generate_push_event(self) -> dict[str, Any]:
        """Generate a push event payload."""
        project_id = random.choice(self.project_ids)
        user_id = random.choice(self.user_ids)
        commit_sha = hashlib.sha1(str(uuid.uuid4()).encode()).hexdigest()

        return {
            "object_kind": "push",
            "event_name": "push",
            "before": "0" * 40,
            "after": commit_sha,
            "ref": f"refs/heads/feature/{random.randint(1, 100)}",
            "checkout_sha": commit_sha,
            "user_id": user_id,
            "user_name": f"user{user_id}",
            "user_email": f"user{user_id}@example.com",
            "project_id": project_id,
            "project": {
                "id": project_id,
                "name": f"project-{project_id}",
                "web_url": f"https://gitlab.example.com/project-{project_id}",
            },
            "commits": [
                {
                    "id": commit_sha,
                    "message": f"Test commit {uuid.uuid4()}",
                    "timestamp": datetime.now(UTC).isoformat(),
                    "author": {
                        "name": f"user{user_id}",
                        "email": f"user{user_id}@example.com",
                    },
                }
            ],
            "total_commits_count": 1,
        }

    def generate_mr_event(self) -> dict[str, Any]:
        """Generate a merge request event payload."""
        project_id = random.choice(self.project_ids)
        user_id = random.choice(self.user_ids)
        mr_iid = random.randint(1, 500)

        return {
            "object_kind": "merge_request",
            "event_type": "merge_request",
            "user": {
                "id": user_id,
                "name": f"user{user_id}",
                "username": f"user{user_id}",
                "email": f"user{user_id}@example.com",
            },
            "project": {
                "id": project_id,
                "name": f"project-{project_id}",
                "web_url": f"https://gitlab.example.com/project-{project_id}",
            },
            "object_attributes": {
                "id": random.randint(10000, 99999),
                "iid": mr_iid,
                "title": f"Feature {mr_iid}: Test merge request",
                "description": "Test MR description with issue reference #"
                + str(random.randint(1, 100)),
                "state": random.choice(["opened", "merged", "closed"]),
                "source_branch": f"feature/{mr_iid}",
                "target_branch": "main",
                "author_id": user_id,
                "created_at": datetime.now(UTC).isoformat(),
                "updated_at": datetime.now(UTC).isoformat(),
                "action": random.choice(["open", "update", "merge", "close"]),
            },
        }

    def generate_note_event(self) -> dict[str, Any]:
        """Generate a note (comment) event payload."""
        project_id = random.choice(self.project_ids)
        user_id = random.choice(self.user_ids)

        return {
            "object_kind": "note",
            "event_type": "note",
            "user": {
                "id": user_id,
                "name": f"user{user_id}",
                "username": f"user{user_id}",
            },
            "project": {
                "id": project_id,
                "name": f"project-{project_id}",
            },
            "object_attributes": {
                "id": random.randint(10000, 99999),
                "note": f"Review comment: {uuid.uuid4()}",
                "noteable_type": "MergeRequest",
                "noteable_id": random.randint(1, 500),
                "created_at": datetime.now(UTC).isoformat(),
            },
            "merge_request": {
                "id": random.randint(10000, 99999),
                "iid": random.randint(1, 500),
                "title": "Test MR",
            },
        }

    def generate_pipeline_event(self) -> dict[str, Any]:
        """Generate a pipeline event payload."""
        project_id = random.choice(self.project_ids)

        return {
            "object_kind": "pipeline",
            "object_attributes": {
                "id": random.randint(100000, 999999),
                "ref": "main",
                "status": random.choice(["success", "failed", "running"]),
                "created_at": datetime.now(UTC).isoformat(),
                "finished_at": datetime.now(UTC).isoformat(),
                "duration": random.randint(30, 600),
            },
            "project": {
                "id": project_id,
                "name": f"project-{project_id}",
            },
        }

    def generate_random_event(self) -> tuple[dict[str, Any], str]:
        """Generate a random webhook event.

        Returns:
            (payload, event_type) tuple
        """
        generators = [
            (self.generate_push_event, "Push Hook"),
            (self.generate_mr_event, "Merge Request Hook"),
            (self.generate_note_event, "Note Hook"),
            (self.generate_pipeline_event, "Pipeline Hook"),
        ]

        # Weight towards MR and push events (more common)
        weights = [0.3, 0.35, 0.2, 0.15]
        gen, event_type = random.choices(generators, weights=weights)[0]

        return gen(), event_type


class LoadTester:
    """Executes load tests against the GitPulse API."""

    def __init__(self, config: LoadTestConfig):
        self.config = config
        self.generator = WebhookPayloadGenerator()
        self.result = LoadTestResult()
        self._running = True
        self._semaphore: asyncio.Semaphore | None = None

    async def run(self) -> LoadTestResult:
        """Run the load test."""
        print(f"Starting load test: {self.config.target}")
        print(f"  Duration: {self.config.duration_seconds}s")
        print(f"  Target RPS: {self.config.requests_per_second}")
        print(f"  Concurrent: {self.config.concurrent_connections}")
        print()

        self._semaphore = asyncio.Semaphore(self.config.concurrent_connections)

        start_time = time.monotonic()
        end_time = start_time + self.config.duration_seconds

        async with httpx.AsyncClient(timeout=self.config.timeout_seconds) as client:
            tasks: list[asyncio.Task[None]] = []

            while time.monotonic() < end_time and self._running:
                # Calculate current target RPS (with ramp-up)
                elapsed = time.monotonic() - start_time
                if self.config.ramp_up_seconds > 0 and elapsed < self.config.ramp_up_seconds:
                    current_rps = self.config.requests_per_second * (
                        elapsed / self.config.ramp_up_seconds
                    )
                else:
                    current_rps = self.config.requests_per_second

                # Calculate delay between requests
                delay = 1.0 / max(1, current_rps)

                # Launch request
                task = asyncio.create_task(self._make_request(client))
                tasks.append(task)

                # Wait for delay
                await asyncio.sleep(delay)

                # Clean up completed tasks periodically
                if len(tasks) > 1000:
                    done = [t for t in tasks if t.done()]
                    for t in done:
                        tasks.remove(t)

            # Wait for remaining tasks
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)

        self.result.total_duration_seconds = time.monotonic() - start_time
        self.result.calculate_percentiles()

        return self.result

    async def _make_request(self, client: httpx.AsyncClient) -> None:
        """Make a single request based on target."""
        semaphore = self._semaphore
        if semaphore is None:
            raise RuntimeError("load tester semaphore is not initialized")
        async with semaphore:
            if self.config.target == "webhooks":
                await self._make_webhook_request(client)
            elif self.config.target == "api":
                await self._make_api_request(client)
            elif self.config.target == "reports":
                await self._make_report_request(client)
            else:
                # Random mix
                target = random.choice(["webhooks", "api"])
                if target == "webhooks":
                    await self._make_webhook_request(client)
                else:
                    await self._make_api_request(client)

    def _record(self, status_code: int, latency_ms: float, *, success: bool) -> None:
        """One place where a response becomes a statistic.

        The three request paths each classified their own responses and only
        the webhook one counted 429. An API run that was almost entirely
        throttled therefore printed "Rate Limited: 0" next to a 75% error
        rate, which reads as the application falling over when the rate
        limiter was in fact doing its job.
        """
        self.result.total_requests += 1
        self.result.latencies.append(latency_ms)
        if success:
            self.result.successful_requests += 1
            return
        if status_code == 429:
            self.result.rate_limited_requests += 1
        self.result.failed_requests += 1
        if self.config.verbose:
            self.result.errors.append(f"HTTP {status_code}")

    async def _make_webhook_request(self, client: httpx.AsyncClient) -> None:
        """Make a webhook request."""
        payload, event_type = self.generator.generate_random_event()
        event_uuid = str(uuid.uuid4())

        # Calculate signature
        body = json.dumps(payload)

        headers = {
            "Content-Type": "application/json",
            "X-Gitlab-Event": event_type,
            "X-Gitlab-Event-UUID": event_uuid,
        }

        if self.config.webhook_secret:
            import hmac

            signature = hmac.new(
                self.config.webhook_secret.encode(),
                body.encode(),
                hashlib.sha256,
            ).hexdigest()
            headers["X-Gitlab-Token"] = self.config.webhook_secret

        url = f"{self.config.base_url}/api/v1/webhooks/gitlab"

        try:
            start = time.monotonic()
            response = await client.post(url, content=body, headers=headers)
            latency_ms = (time.monotonic() - start) * 1000

            self._record(response.status_code, latency_ms, success=response.status_code == 200)

        except httpx.TimeoutException:
            self.result.total_requests += 1
            self.result.timeout_requests += 1
            self.result.failed_requests += 1
        except Exception as exc:
            self.result.total_requests += 1
            self.result.failed_requests += 1
            if self.config.verbose:
                self.result.errors.append(str(exc))

    async def _make_api_request(self, client: httpx.AsyncClient) -> None:
        """Make an API request."""
        # Real endpoints, checked against the served OpenAPI spec. The old
        # list was stale in every entry: /api/v1/health does not exist and
        # answered 404, /api/v1/teams does not exist either, and
        # /api/v1/courses (no trailing slash) only 307-redirected to the real
        # path, which this client does not follow. Two thirds of the "load"
        # was 404s and the last third never reached a handler, so the latency
        # and error numbers this printed described nothing.
        endpoints = [
            "/health",
            "/api/v1/courses/",
            "/api/v1/projects/",
            "/api/v1/students/",
        ]

        url = f"{self.config.base_url}{random.choice(endpoints)}"
        headers = {}
        if self.config.auth_token:
            headers["Authorization"] = f"Bearer {self.config.auth_token}"

        try:
            start = time.monotonic()
            response = await client.get(url, headers=headers)
            latency_ms = (time.monotonic() - start) * 1000

            self._record(
                response.status_code,
                latency_ms,
                success=200 <= response.status_code < 400,
            )

        except httpx.TimeoutException:
            self.result.total_requests += 1
            self.result.timeout_requests += 1
            self.result.failed_requests += 1
        except Exception:
            self.result.total_requests += 1
            self.result.failed_requests += 1

    async def _make_report_request(self, client: httpx.AsyncClient) -> None:
        """Make a report generation request."""
        team_id = str(uuid.uuid4())
        url = f"{self.config.base_url}/api/v1/teams/{team_id}/report"

        headers = {}
        if self.config.auth_token:
            headers["Authorization"] = f"Bearer {self.config.auth_token}"

        try:
            start = time.monotonic()
            response = await client.post(url, headers=headers, params={"fmt": "json"})
            latency_ms = (time.monotonic() - start) * 1000

            self._record(
                response.status_code,
                latency_ms,
                success=response.status_code in (200, 202),
            )

        except httpx.TimeoutException:
            self.result.total_requests += 1
            self.result.timeout_requests += 1
            self.result.failed_requests += 1
        except Exception:
            self.result.total_requests += 1
            self.result.failed_requests += 1

    def print_results(self) -> None:
        """Print load test results."""
        r = self.result

        print("\n" + "=" * 60)
        print("LOAD TEST RESULTS")
        print("=" * 60)

        print("\nRequests:")
        print(f"  Total:        {r.total_requests:,}")
        print(f"  Successful:   {r.successful_requests:,}")
        print(f"  Failed:       {r.failed_requests:,}")
        print(f"  Rate Limited: {r.rate_limited_requests:,}")
        print(f"  Timeouts:     {r.timeout_requests:,}")

        print("\nThroughput:")
        print(f"  Duration:     {r.total_duration_seconds:.1f}s")
        print(f"  Requests/sec: {r.requests_per_second:.1f}")
        print(f"  Error Rate:   {r.error_rate * 100:.2f}%")

        print("\nLatency (ms):")
        print(f"  Average:  {r.avg_latency_ms:.1f}")
        print(f"  P50:      {r.p50_latency_ms:.1f}")
        print(f"  P95:      {r.p95_latency_ms:.1f}")
        print(f"  P99:      {r.p99_latency_ms:.1f}")
        print(f"  Max:      {r.max_latency_ms:.1f}")

        print("\n" + "=" * 60)

        # Success criteria
        if r.error_rate < 0.01 and r.p99_latency_ms < 1000:
            print("[PASS] Error rate < 1% and P99 < 1s")
        else:
            print("[FAIL] Performance criteria not met")
            if r.error_rate >= 0.01:
                print(f"  - Error rate {r.error_rate * 100:.2f}% >= 1%")
            if r.p99_latency_ms >= 1000:
                print(f"  - P99 latency {r.p99_latency_ms:.1f}ms >= 1000ms")


def main() -> None:
    parser = argparse.ArgumentParser(description="Load test for GitPulse scale optimizations")

    parser.add_argument(
        "--base-url", default="http://localhost:8000", help="Base URL of the GitPulse API"
    )
    parser.add_argument(
        "--target",
        choices=["webhooks", "api", "reports", "all"],
        default="webhooks",
        help="Target endpoint type",
    )
    parser.add_argument("--duration", type=int, default=60, help="Test duration in seconds")
    parser.add_argument("--rps", type=int, default=50, help="Target requests per second")
    parser.add_argument("--ramp-up", type=int, default=0, help="Ramp-up period in seconds")
    parser.add_argument("--concurrent", type=int, default=10, help="Maximum concurrent connections")
    parser.add_argument("--webhook-secret", default="", help="Webhook secret for signature")
    parser.add_argument("--auth-token", default="", help="API authentication token")
    parser.add_argument(
        "--monitor-backpressure",
        action="store_true",
        help="Monitor backpressure metrics during test",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Verbose output including errors"
    )

    args = parser.parse_args()

    config = LoadTestConfig(
        base_url=args.base_url,
        target=args.target,
        duration_seconds=args.duration,
        requests_per_second=args.rps,
        ramp_up_seconds=args.ramp_up,
        concurrent_connections=args.concurrent,
        webhook_secret=args.webhook_secret,
        auth_token=args.auth_token,
        monitor_backpressure=args.monitor_backpressure,
        verbose=args.verbose,
    )

    tester = LoadTester(config)

    try:
        asyncio.run(tester.run())
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        tester._running = False

    tester.print_results()

    # Exit with error code if test failed
    if tester.result.error_rate >= 0.01 or tester.result.p99_latency_ms >= 1000:
        sys.exit(1)


if __name__ == "__main__":
    main()
