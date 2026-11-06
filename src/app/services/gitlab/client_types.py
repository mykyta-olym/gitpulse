"""Data types for GitLab API client."""


class GitLabAPIError(Exception):
    """Raised when GitLab API returns an unexpected error."""

    def __init__(self, status_code: int, message: str) -> None:
        self.status_code = status_code
        super().__init__(f"GitLab API error {status_code}: {message}")


def is_gitlab_auth_error(exc: BaseException) -> bool:
    """True for a GitLab 401/403 - a permanent auth failure, never retried.

    An invalid/expired token is not transient: retrying just re-runs the same
    doomed work. Single source of truth used by the sync worker and the
    background-job token guard to fail fast (and stop RQ retries) on auth errors.
    """
    return isinstance(exc, GitLabAPIError) and getattr(exc, "status_code", None) in (401, 403)


class GitLabPaginationTruncatedError(GitLabAPIError):
    """Raised when a paginated endpoint hit the page cap with a FULL final page,
    meaning GitLab has more data that was not fetched.

    Silent truncation is worse than a loud failure: the sync job would mark
    itself as "completed" while the dashboard shows wrong metrics computed
    on partial data. Callers wrap per-project sync in try/except and will
    mark just that project as failed so the sweep retries it.
    """

    def __init__(self, path: str, items_fetched: int, max_pages: int, per_page: int) -> None:
        self.path = path
        self.items_fetched = items_fetched
        self.max_pages = max_pages
        self.per_page = per_page
        super().__init__(
            0,
            f"pagination truncated at {max_pages} pages "
            f"(per_page={per_page}, fetched={items_fetched}) for {path}",
        )
