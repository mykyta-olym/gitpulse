"""Unit tests for shared constants and small type modules."""

from __future__ import annotations


class TestConstants:
    def test_page_size_defaults(self):
        from app.utils.constants import PAGE_SIZE_DEFAULT, PAGE_SIZE_SEARCH

        assert PAGE_SIZE_DEFAULT == 50
        assert PAGE_SIZE_SEARCH == 8

    def test_default_branch(self):
        from app.utils.constants import DEFAULT_BRANCH

        assert DEFAULT_BRANCH == "main"

    def test_no_login_hash(self):
        from app.utils.constants import NO_LOGIN_HASH

        assert NO_LOGIN_HASH == "!NOLOGIN"

    def test_csp_origins(self):
        from app.utils.constants import CSP_FONT_ORIGINS, CSP_IMAGE_ORIGINS, CSP_STYLE_ORIGINS

        assert len(CSP_STYLE_ORIGINS) >= 1
        assert len(CSP_FONT_ORIGINS) >= 1
        assert len(CSP_IMAGE_ORIGINS) >= 1


class TestGitLabAPIError:
    def test_error_creation(self):
        from app.services.gitlab.client_types import GitLabAPIError

        err = GitLabAPIError(404, "Not found")
        assert err.status_code == 404
        assert "404" in str(err)
        assert "Not found" in str(err)

    def test_is_exception(self):
        from app.services.gitlab.client_types import GitLabAPIError

        assert issubclass(GitLabAPIError, Exception)
