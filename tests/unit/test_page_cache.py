"""Tests for ``app.services.page_cache``.

The page cache underpins every slow lazy-loaded dashboard fragment
(team / project / course / student detail, course analytics). These
tests pin down the substitution rules - getting them wrong leaks
CSRF tokens, usernames, avatars or the per-request CSP nonce between
unrelated viewers - and the cascade invalidation contract so a write
to one entity drops every dependent cached fragment.
"""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock, patch

import pytest

from app.services import page_cache as pc

# --------------------------- make_variant ---------------------------


class TestMakeVariant:
    def test_returns_short_hex(self) -> None:
        h = pc.make_variant("en", "teacher", 1, 0)
        assert isinstance(h, str)
        assert len(h) == 16
        int(h, 16)  # parses as hex

    def test_distinct_inputs_yield_distinct_hashes(self) -> None:
        assert pc.make_variant("en", "teacher") != pc.make_variant("sk", "teacher")
        assert pc.make_variant("en", "teacher") != pc.make_variant("en", "admin")

    def test_none_normalised_to_empty_string(self) -> None:
        assert pc.make_variant("en", None) == pc.make_variant("en", "")

    def test_delimiter_like_values_do_not_collide(self) -> None:
        assert pc.make_variant("a|b", "c") != pc.make_variant("a", "b|c")


# --------------------------- personalize ---------------------------


class TestPersonalize:
    def test_substitutes_csrf_placeholder(self) -> None:
        body = f'<input name="csrf" value="{pc.CSRF_PLACEHOLDER}">'
        out = pc.personalize(body, csrf_token="real-token-abc")
        assert "real-token-abc" in out
        assert pc.CSRF_PLACEHOLDER not in out

    def test_substitutes_csp_nonce_placeholder(self) -> None:
        body = f'<script nonce="{pc.CSP_NONCE_PLACEHOLDER}">init()</script>'
        out = pc.personalize(body, csrf_token="t", csp_nonce="abc123nonce")
        assert 'nonce="abc123nonce"' in out
        assert pc.CSP_NONCE_PLACEHOLDER not in out

    def test_empty_csp_nonce_strips_placeholder(self) -> None:
        body = f'<script nonce="{pc.CSP_NONCE_PLACEHOLDER}">x</script>'
        out = pc.personalize(body, csrf_token="t", csp_nonce="")
        assert pc.CSP_NONCE_PLACEHOLDER not in out
        assert 'nonce=""' in out

    def test_substitutes_all_personal_placeholders(self) -> None:
        body = " ".join(pc.PERSONAL_PLACEHOLDERS.values())
        role_ctx = {
            "username": "alice",
            "gitlab_username": "alice_gl",
            "avatar_url": "https://gravatar/a",
            "full_name": "Alice Example",
        }
        out = pc.personalize(body, csrf_token="t", role_ctx=role_ctx)
        for placeholder in pc.PERSONAL_PLACEHOLDERS.values():
            assert placeholder not in out
        assert "alice" in out
        assert "alice_gl" in out
        assert "Alice Example" in out

    def test_missing_personal_fields_substituted_with_empty(self) -> None:
        body = pc.PERSONAL_PLACEHOLDERS["username"]
        out = pc.personalize(body, csrf_token="t", role_ctx={})
        # Placeholder gone, no raw sentinel leaked
        assert "PLACEHOLDER" not in out
        assert out == ""

    def test_csrf_skipped_when_empty(self) -> None:
        # Empty CSRF must NOT replace the placeholder (keeps it visible
        # for debugging rather than silently producing a broken form).
        body = pc.CSRF_PLACEHOLDER
        out = pc.personalize(body, csrf_token="", role_ctx={})
        assert out == pc.CSRF_PLACEHOLDER

    def test_does_not_mutate_other_text(self) -> None:
        body = "<div>hello world</div>"
        assert pc.personalize(body, csrf_token="t") == body


# --------------------------- cacheable_role_ctx ---------------------------


class TestCacheableRoleCtx:
    def test_replaces_personal_fields_with_placeholders(self) -> None:
        rc = {
            "username": "alice",
            "gitlab_username": "alice_gl",
            "avatar_url": "https://x",
            "full_name": "Alice",
            "user_role": "teacher",
            "is_teacher": True,
            "is_admin": False,
            "can_edit": True,
        }
        out = pc.cacheable_role_ctx(rc)
        assert out["username"] == pc.PERSONAL_PLACEHOLDERS["username"]
        assert out["avatar_url"] == pc.PERSONAL_PLACEHOLDERS["avatar_url"]
        # Role flags MUST be kept verbatim - they belong in the variant
        # key and templates branch on them.
        assert out["user_role"] == "teacher"
        assert out["is_teacher"] is True
        assert out["can_edit"] is True

    def test_does_not_mutate_input(self) -> None:
        rc = {"username": "alice"}
        pc.cacheable_role_ctx(rc)
        assert rc["username"] == "alice"


# --------------------------- Redis get/set ---------------------------


class TestGetSetCached:
    def _conn(self) -> MagicMock:
        return MagicMock()

    def test_set_then_get_roundtrip(self) -> None:
        store: dict[str, bytes] = {}
        conn = self._conn()
        conn.set.side_effect = lambda k, v, *, ex: store.__setitem__(
            k, v.encode() if isinstance(v, str) else v
        )
        conn.get.side_effect = lambda k: store.get(k)
        with patch("app.services.page_cache.get_redis", return_value=conn):
            pc.set_cached("team", "abc", "v1", "<p>body</p>")
            assert pc.get_cached("team", "abc", "v1") == "<p>body</p>"

    def test_get_returns_none_on_miss(self) -> None:
        conn = self._conn()
        conn.get.return_value = None
        with patch("app.services.page_cache.get_redis", return_value=conn):
            assert pc.get_cached("team", "abc", "v1") is None

    def test_get_returns_none_when_redis_unavailable(self) -> None:
        with patch("app.services.page_cache.get_redis", side_effect=Exception("down")):
            assert pc.get_cached("team", "abc", "v1") is None

    def test_set_swallows_redis_failure(self) -> None:
        with patch("app.services.page_cache.get_redis", side_effect=Exception("down")):
            pc.set_cached("team", "abc", "v1", "<p>x</p>")  # must not raise

    def test_key_scope_isolation(self) -> None:
        store: dict[str, bytes] = {}
        conn = self._conn()
        conn.set.side_effect = lambda k, v, *, ex: store.__setitem__(
            k, v.encode() if isinstance(v, str) else v
        )
        conn.get.side_effect = lambda k: store.get(k)
        with patch("app.services.page_cache.get_redis", return_value=conn):
            pc.set_cached("team", "id1", "v1", "team-body")
            pc.set_cached("project", "id1", "v1", "project-body")
            # Different kinds, same scope_id and variant => different keys
            assert pc.get_cached("team", "id1", "v1") == "team-body"
            assert pc.get_cached("project", "id1", "v1") == "project-body"


# --------------------------- invalidate / cascade ---------------------------


class TestInvalidate:
    def _conn_with_keys(self, keys: list[bytes]) -> MagicMock:
        conn = MagicMock()
        # Simulate a single SCAN page (cursor returns to 0 after one batch)
        conn.scan.return_value = (0, keys)
        conn.delete.return_value = len(keys)
        return conn

    def test_invalidate_returns_zero_when_no_match(self) -> None:
        conn = self._conn_with_keys([])
        with patch("app.services.page_cache.get_redis", return_value=conn):
            assert pc.invalidate("team", "abc") == 0
        conn.delete.assert_not_called()

    def test_invalidate_deletes_matching_keys(self) -> None:
        keys = [b"gp:page:v2:team:abc:v1", b"gp:page:v2:team:abc:v2"]
        conn = self._conn_with_keys(keys)
        with patch("app.services.page_cache.get_redis", return_value=conn):
            removed = pc.invalidate("team", "abc")
        assert removed == 2
        conn.delete.assert_called_once_with(*keys)

    def test_invalidate_swallows_redis_failure(self) -> None:
        with patch("app.services.page_cache.get_redis", side_effect=Exception("down")):
            # Best-effort: zero keys removed, no exception escapes.
            assert pc.invalidate("team", "abc") == 0

    def test_invalidate_many_deduplicates_scopes(self) -> None:
        pairs = [("team", "abc"), ("team", "abc"), ("project", "abc")]
        with patch("app.services.page_cache.invalidate", return_value=1) as mock_invalidate:
            assert pc.invalidate_many(pairs) == 2
        assert mock_invalidate.call_count == 2
        mock_invalidate.assert_any_call("team", "abc")
        mock_invalidate.assert_any_call("project", "abc")

    def test_cascade_skips_none_ids(self) -> None:
        with patch("app.services.page_cache.invalidate_many") as mock_many:
            mock_many.return_value = 0
            pc.invalidate_cascade()  # nothing given
        mock_many.assert_not_called()

    def test_cascade_invalidates_project_team_course_analytics_and_students(self) -> None:
        project_id = uuid.uuid4()
        team_id = uuid.uuid4()
        course_id = uuid.uuid4()
        s1, s2 = uuid.uuid4(), uuid.uuid4()
        with patch("app.services.page_cache.invalidate_many") as mock_many:
            mock_many.return_value = 7
            total = pc.invalidate_cascade(
                project_id=project_id,
                team_id=team_id,
                course_id=course_id,
                student_ids=[s1, s2],
            )
        assert total == 7
        pairs = mock_many.call_args.args[0]
        assert ("project", project_id) in pairs
        assert ("team", team_id) in pairs
        assert ("course", course_id) in pairs
        assert ("course-analytics", course_id) in pairs
        assert ("course-activity", course_id) in pairs
        assert ("student", s1) in pairs
        assert ("student", s2) in pairs

    def test_cascade_course_only_drops_all_three_course_kinds(self) -> None:
        course_id = uuid.uuid4()
        with patch("app.services.page_cache.invalidate_many") as mock_many:
            mock_many.return_value = 0
            pc.invalidate_cascade(course_id=course_id)
        pairs = mock_many.call_args.args[0]
        kinds = {kind for kind, _ in pairs}
        assert kinds == {"course", "course-analytics", "course-activity"}


# --------------------------- build_cache_render_ctx ---------------------------


class TestBuildCacheRenderCtx:
    def test_includes_placeholders_for_csrf_and_csp_and_personals(self) -> None:
        # i18n context lookup will fail for a bare MagicMock - that's
        # explicitly handled by suppress(Exception) - but the
        # placeholders MUST still be present.
        req = MagicMock()
        ctx = pc.build_cache_render_ctx(req)
        assert ctx["csrf_token"] == pc.CSRF_PLACEHOLDER
        assert ctx["csp_nonce"] == pc.CSP_NONCE_PLACEHOLDER
        for name, placeholder in pc.PERSONAL_PLACEHOLDERS.items():
            assert ctx[name] == placeholder

    def test_i18n_failure_does_not_raise(self) -> None:
        req = MagicMock()
        with patch(
            "app.i18n.get_template_i18n_context",
            side_effect=RuntimeError("no request scope"),
        ):
            ctx = pc.build_cache_render_ctx(req)
        # Placeholders still wired up.
        assert ctx["csrf_token"] == pc.CSRF_PLACEHOLDER


# --------------------------- request_csp_nonce ---------------------------


class TestRequestCspNonce:
    def test_returns_state_nonce(self) -> None:
        req = MagicMock()
        req.state.csp_nonce = "xyz"
        assert pc.request_csp_nonce(req) == "xyz"

    def test_returns_empty_when_missing(self) -> None:
        req = MagicMock(spec=[])  # no .state attribute
        assert pc.request_csp_nonce(req) == ""

    @pytest.mark.parametrize("bad_value", [None, ""])
    def test_returns_empty_for_falsy_nonce(self, bad_value: object) -> None:
        req = MagicMock()
        req.state.csp_nonce = bad_value
        assert pc.request_csp_nonce(req) == ""


# --------------------------- make_role_variant ---------------------------


class TestMakeRoleVariant:
    def test_course_permissions_separate_the_same_global_role(self) -> None:
        req = MagicMock()
        role = {"user_role": "teacher", "is_teacher": True}
        with patch("app.i18n.resolve_locale", return_value="en"):
            staff = pc.make_role_variant(req, {**role, "can_edit": True})
            reader = pc.make_role_variant(req, {**role, "can_edit": False})
        assert staff != reader

    def test_includes_locale_and_role_flags(self) -> None:
        req = MagicMock()
        with patch("app.i18n.resolve_locale", return_value="en"):
            v1 = pc.make_role_variant(req, {"user_role": "teacher", "is_teacher": True})
            v2 = pc.make_role_variant(req, {"user_role": "teacher", "is_teacher": False})
        assert v1 != v2

    def test_extra_args_differentiate(self) -> None:
        req = MagicMock()
        with patch("app.i18n.resolve_locale", return_value="en"):
            v1 = pc.make_role_variant(req, {"user_role": "teacher"}, "owner")
            v2 = pc.make_role_variant(req, {"user_role": "teacher"}, "member")
        assert v1 != v2

    def test_locale_failure_falls_back_to_empty(self) -> None:
        req = MagicMock()
        with patch("app.i18n.resolve_locale", side_effect=RuntimeError("no scope")):
            v = pc.make_role_variant(req, {"user_role": "admin"})
        assert isinstance(v, str)
        assert len(v) == 16
