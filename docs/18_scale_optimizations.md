# Scale and cache operations

This guide describes the implementations used by the API and workers.

## Page-fragment cache

`app.services.page_cache` stores rendered dashboard fragments in Redis. Cache
keys include the deployed build and a locale/role variant. Scope invalidation
runs after changes to courses, teams, projects or compliance snapshots.

Cached HTML contains placeholders for CSRF, the current CSP nonce and personal
fields. `personalize` substitutes them on each response; `render_inline` embeds
the fragment in the current page shell. A cached nonce or another user's token
must never be served directly. The default TTL is 300 seconds; callers may
supply a shorter lifetime for their data.

The implementation records `page_cache_hits_total`, `page_cache_misses_total`
and `page_cache_invalidations_total` through the shared observability module.

## GitLab API cache and retries

When `FEATURE_GITLAB_CACHE=true`, the event processor passes a Redis-backed
`GitLabAPICache` to `GitLabClient`. Responses and ETags use separate Redis keys;
conditional requests use `If-None-Match`, and a 304 reuses the cached response.
Malformed or unavailable cache entries fall back to the GitLab request.

`CacheConfig` defines TTLs of 300 seconds for entities, 120 seconds for lists
and 900 seconds for users. Responses over 1024 bytes use gzip compression.
There is no separate request-batching subsystem.

`GitLabClient` retries transient server errors and timeouts with bounded
exponential waits. A 429 honors `Retry-After`; exhausting retries is an error,
not a successful empty result. Invalid tokens update shared token health so
other entry points can avoid repeatedly using rejected credentials.

Active GitLab metrics are `gitlab_api_requests_total` and
`gitlab_api_duration_seconds`, recorded at the actual HTTP boundary.

## Queue backpressure

`FEATURE_BACKPRESSURE` controls webhook admission to the high-priority RQ
queue. The webhook event is persisted before admission; shed events remain
available for the periodic sweep to retry.

`QueueBackpressure` reads `rq:queue:high` from Redis. Its configured limits are
`QUEUE_HIGH_WATERMARK` (default 1000) and `QUEUE_CRITICAL_WATERMARK` (default
5000). Below the high limit, work is admitted normally. Between the limits,
priority affects probabilistic admission. At the critical limit, only the
highest priority passes. A failed depth check permits enqueueing.

The shared collector sets the real `rq_queue_depth` gauge. Inspect queue depth,
worker availability and job failures in System and the monitoring dashboards.
`RATE_LIMIT_REQUESTS_PER_MINUTE` independently controls API request admission
in `app.dependencies`; it is not a second GitLab-client limiter.

## Checks after a change

Run the repository quality gates and the integration tests against a fresh
`gitpulse_test` database. Validate cache hits and misses, ETag 304 behavior,
Redis failure, queue overload and token rejection. Browser checks must include
an initial page, a cached page and navigation between them under the enforced
nonce-based CSP.
