"""Event/sync-driven worker jobs (re-export hub).

These are thin orchestration functions enqueued directly by other code paths.
GitPulse is webhook-driven: there is no recurring scheduler, so nothing here
fires on a timer.

.. note:: **``asyncio.run()`` per job is intentional.**

    RQ workers fork a short-lived child process per job (default
    ``WORKER_FORK=true``) so each job gets a brand-new process - there
    is no event loop or connection pool to reuse across jobs anyway.
    For jobs that need async DB access we therefore call
    ``asyncio.run(_*_async())`` which creates a fresh loop, opens
    its own SQLAlchemy session factory through ``init_engine`` (cached
    per-process), runs it, and tears the loop down.

**Webhook-first philosophy**: webhooks and explicit sync actions are the
only data-refresh paths.  GitLab polling must not be reintroduced.

This module only re-exports the event/sync-driven jobs so their
``app.workers.sweep.<name>`` string paths keep resolving for the enqueuers:
    refresh_project_gitlab_intel    - webhook -> per-project intel refresh
    sync_single_team_members        - push -> team member sync
    compliance_snapshot_for_team    - post-team-sync compliance snapshot
"""

from rq import Retry

from app.workers.sweep_compliance import (  # noqa: F401
    _compliance_snapshot_for_team_async,
    compliance_snapshot_for_team,
)
from app.workers.sweep_membership import (  # noqa: F401
    _sync_single_team_async,
    sync_single_team_members,
)
from app.workers.sweep_projects import (  # noqa: F401
    _incremental_project_refresh,
    _incremental_refresh_async,
    _refresh_project_gitlab_intel_async,
    refresh_project_gitlab_intel,
)

# Retry policy for sub-jobs enqueued by the event/sync-driven jobs above.
# 2 retries with exponential backoff: 10 s -> 30 s (matches the ``max_retries=2``
# default in ``event_service._enqueue``; only ``process_event`` opts into a 3rd).
# Without this, transient Redis / worker failures silently drop jobs.
_SWEEP_RETRY = Retry(max=2, interval=[10, 30])
