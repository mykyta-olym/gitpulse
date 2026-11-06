"""RQ worker job definitions.

Job registry
------------
1. process_event      - Dispatch a single webhook event to its type-specific processor.
2. enrich_issue       - Re-fetch issue data from GitLab API and update DB.
3. enrich_mr          - Re-fetch MR data (diff, approvals, notes) from GitLab API.
4. compute_metrics    - Recompute compliance metrics for one team.

All jobs are idempotent: running them twice with the same arguments produces the
same DB state.  Safe retries are handled via RQ Retry objects with exponential
back-off intervals defined in config.
"""
