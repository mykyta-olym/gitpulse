"""Scope validation and secret generation for webhook configurations.

`_validate_scope_payload` mirrors a database CHECK constraint so a bad scope is
rejected with a readable message instead of a Postgres error. Mirrored rules
drift silently - the constraint keeps holding while the friendly path stops
matching it - so the rules are pinned here.

`_normalize_path` decides whether an incoming GitLab group path matches a
stored one. It is the comparison an authentication decision rests on, so its
case and slash handling matter more than it looks.
"""

from __future__ import annotations

import pytest

from app.models.webhook_configuration import WebhookScope
from app.services.webhook_configs import (
    SECRET_PLAINTEXT_PREFIX,
    _new_plaintext,
    _normalize_path,
    _validate_scope_payload,
)


def _validate(scope_type: str, *, path: str | None = None, ids: list[int] | None = None) -> None:
    _validate_scope_payload(scope_type=scope_type, gitlab_group_path=path, gitlab_project_ids=ids)


class TestScopeType:
    def test_an_unknown_scope_is_rejected_by_name(self) -> None:
        with pytest.raises(ValueError, match="Unknown scope_type"):
            _validate("everything")

    @pytest.mark.parametrize("scope", list(WebhookScope))
    def test_every_declared_scope_is_accepted_with_a_valid_payload(
        self, scope: WebhookScope
    ) -> None:
        """A new enum member must not be silently unvalidatable."""
        _validate(scope.value, path="kpi/zsi", ids=[1])


class TestProjectScope:
    def test_requires_at_least_one_project(self) -> None:
        with pytest.raises(ValueError, match="at least one project id"):
            _validate(WebhookScope.PROJECTS.value, ids=[])

    def test_rejects_non_positive_ids(self) -> None:
        with pytest.raises(ValueError, match="positive integers"):
            _validate(WebhookScope.PROJECTS.value, ids=[1, 0])

    def test_rejects_non_integer_ids(self) -> None:
        with pytest.raises(ValueError, match="positive integers"):
            _validate(WebhookScope.PROJECTS.value, ids=["7"])  # type: ignore[list-item]

    def test_rejects_duplicates(self) -> None:
        """A repeated id would widen the scope silently on update."""
        with pytest.raises(ValueError, match="unique"):
            _validate(WebhookScope.PROJECTS.value, ids=[5, 5])

    def test_accepts_a_clean_list(self) -> None:
        _validate(WebhookScope.PROJECTS.value, ids=[5, 6, 7])


class TestGroupScope:
    @pytest.mark.parametrize("scope", [WebhookScope.GROUP, WebhookScope.SUBGROUP])
    def test_requires_a_group_path(self, scope: WebhookScope) -> None:
        with pytest.raises(ValueError, match="requires gitlab_group_path"):
            _validate(scope.value, path=None)

    @pytest.mark.parametrize("scope", [WebhookScope.GROUP, WebhookScope.SUBGROUP])
    def test_an_empty_path_counts_as_missing(self, scope: WebhookScope) -> None:
        with pytest.raises(ValueError, match="requires gitlab_group_path"):
            _validate(scope.value, path="")


class TestPathNormalisation:
    def test_none_stays_none(self) -> None:
        assert _normalize_path(None) is None

    @pytest.mark.parametrize(
        "given",
        ["kpi/zsi", "/kpi/zsi", "kpi/zsi/", "  /kpi/zsi/  ", "KPI/ZSI"],
    )
    def test_slashes_whitespace_and_case_all_collapse_to_one_form(self, given: str) -> None:
        """GitLab sends the same group several ways; a stored path must match
        all of them or the webhook is rejected as out of scope."""
        assert _normalize_path(given) == "kpi/zsi"

    @pytest.mark.parametrize("given", ["", "   ", "/", "///"])
    def test_a_path_with_no_content_becomes_none(self, given: str) -> None:
        assert _normalize_path(given) is None


class TestSecretGeneration:
    def test_secret_carries_the_recognisable_prefix(self) -> None:
        assert _new_plaintext().startswith(SECRET_PLAINTEXT_PREFIX)

    def test_secret_has_the_documented_entropy(self) -> None:
        """24 bytes -> 48 hex chars; anything shorter weakens every webhook."""
        body = _new_plaintext().removeprefix(SECRET_PLAINTEXT_PREFIX)

        assert len(body) == 48
        assert all(c in "0123456789abcdef" for c in body)

    def test_secrets_do_not_repeat(self) -> None:
        assert len({_new_plaintext() for _ in range(200)}) == 200
