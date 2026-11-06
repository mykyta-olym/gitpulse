"""Tests for frontend resilience: connection recovery, update detection, SSE fallback.

Validates that the JavaScript source files (health-monitor.js, sse-stream.js,
core.js, components.js) contain correct patterns for:
- Health monitor state machine transitions (unknown -> ok -> down -> ok)
- "Connection restored" toast only when baseline exists
- Offline handler using correct previous status
- GitLab banner takeover/reset logic
- SSE -> polling fallback when backend is down
- Version mismatch detection with infinite-reload guard
- PollingController error threshold enforcement
- Toast deduplication within time window
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from tests.build_outputs import served

_ROOT = Path(__file__).resolve().parent.parent.parent
_STATIC_JS = _ROOT / "src" / "app" / "templates" / "static" / "js"
_STATIC_CSS = _ROOT / "src" / "app" / "templates" / "static" / "css"
_TEMPLATES = _ROOT / "src" / "app" / "templates"
_DASHBOARD_API = _ROOT / "src" / "app" / "api" / "dashboard"
_API = _ROOT / "src" / "app" / "api"
_WORKERS = _ROOT / "src" / "app" / "workers"
_SERVICES = _ROOT / "src" / "app" / "services"


def _read_js(filename: str) -> str:
    """Read a JS source file and return its content.

    Large source files are split into build-only fragments under
    ``_parts/<stem>/`` (concatenated back by ``scripts/build_bundle.py``).
    When the original file no longer exists, transparently read and
    concatenate its parts so source-pattern assertions keep working.
    """
    path = _STATIC_JS / filename
    if not path.exists():
        parts_dir = _STATIC_JS / "_parts" / Path(filename).stem
        if parts_dir.is_dir():
            parts = sorted(parts_dir.glob("*.js"))
            assert parts, f"No split parts found for {filename} in {parts_dir}"
            return "\n".join(p.read_text(encoding="utf-8") for p in parts)
    assert path.exists(), f"JS file not found: {path}"
    return path.read_text(encoding="utf-8")


def _read_css(filename: str) -> str:
    """Read a CSS source file and return its content."""
    path = _STATIC_CSS / filename
    assert path.exists(), f"CSS file not found: {path}"
    return path.read_text(encoding="utf-8")


def _read_template(filename: str) -> str:
    """Read a Jinja template and return its content, INCLUDES AND ALL.

    A contract about what a page renders should not care how that page is split
    into files. The Users page is one card holding one table that
    lives in its own partial, and every assertion about that markup still
    holds; it just does not live in the same file any more. Following
    `{% include %}` keeps those tests about the page, not about its filenames.
    """
    path = _TEMPLATES / filename
    assert path.exists(), f"Template file not found: {path}"
    text = path.read_text(encoding="utf-8")
    # Each partial once, however many branches include it - appending one
    # twice would double every count a caller makes.
    for included in dict.fromkeys(re.findall(r'{%-?\s*include\s+"([^"]+)"', text)):
        child = _TEMPLATES / included
        if child.exists():
            text += "\n" + child.read_text(encoding="utf-8")
    return text


def _code_only(text: str) -> str:
    """Strip Jinja `{# #}`, CSS/JS `/* */` and `//` comments.

    A "this must be gone" assertion has to read the CODE. The note left behind
    to explain a removal names the thing it removed, which otherwise fails the
    very test that removal was meant to satisfy.
    """
    text = re.sub(r"\{#.*?#\}", "", text, flags=re.S)
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    return re.sub(r"(?m)^\s*//.*$", "", text)


def _read_api(filename: str) -> str:
    """Read an API source file and return its content."""
    path = _API / filename
    assert path.exists(), f"API file not found: {path}"
    return path.read_text(encoding="utf-8")


def _read_dashboard_api(filename: str) -> str:
    """Read a dashboard API source file and return its content."""
    path = _DASHBOARD_API / filename
    assert path.exists(), f"Dashboard API file not found: {path}"
    return path.read_text(encoding="utf-8")


def _read_worker(filename: str) -> str:
    """Read a worker source file and return its content."""
    path = _WORKERS / filename
    assert path.exists(), f"Worker file not found: {path}"
    return path.read_text(encoding="utf-8")


def _read_service(filename: str) -> str:
    """Read a service source file and return its content."""
    path = _SERVICES / filename
    assert path.exists(), f"Service file not found: {path}"
    return path.read_text(encoding="utf-8")


class TestProcessCancellationContracts:
    """Pin process cancellation and import guard contracts."""

    def test_import_error_handler_does_not_read_missing_team_set(self) -> None:
        src = _read_js("import-stream.js")
        assert "_importSeen.teams.size" not in src
        assert "_importCounts.teams > 0" in src
        assert "function _isImportCancelError" in src

    def test_import_uses_abort_controller_and_validation(self) -> None:
        src = _read_js("import-stream.js")
        assert "validateGitLabImportUrl" in src
        assert "new AbortController()" in src
        assert "signal: _activeImportAbortController.signal" in src
        assert "window.cancelActiveImport = cancelActiveImport" in src
        assert "addDirtyReason('import_running'" not in src

    def test_gitlab_import_guards_drafts_but_not_the_running_process(self) -> None:
        src = _read_js("import-stream.js")
        assert "GP.enableFormDirtyGuard?.('importGitlabCourseModal')" in src
        assert "if (isBusy) GP.clearModalDirty?.('importGitlabCourseModal')" in src
        dashboard_src = _read_js("dashboard.js")
        assert "enableFormDirtyGuard('createCourseModal')" in dashboard_src

    def test_course_detail_run_checks_and_deleted_toggle_contracts(self) -> None:
        course_detail_src = _read_js("pages/course-detail.js")
        course_data_src = (_STATIC_JS / "_parts" / "course-detail" / "30-course-data.js").read_text(
            encoding="utf-8"
        )

        assert "window.toggleDeletedTeams = toggleDeletedTeams;" in course_detail_src
        assert "const enqueueChecks = async () =>" in course_data_src
        assert "{ confirmText: confirmMsg, singleConfirm: true }" in course_data_src
        assert "confirmDangerousAction({ title:" not in course_data_src

    def test_global_job_bar_has_cancel_action(self) -> None:
        src = _read_js("global-job-bar.js")
        assert "data-job-cancel" in src
        assert "function _cancelGlobalJob" in src
        assert "/api/v1/jobs/" in src
        assert "/jobs/cancel" in src
        assert "cancelActiveLLMGeneration" in src
        restart = re.search(
            r"function confirmProcessRestart\(jobType, processLabel = 'A process'\).*?\n\}",
            src,
            re.DOTALL,
        )
        assert restart
        assert "hideGlobalJob(jobType);" not in restart.group()

    def test_cancelled_is_terminal_in_sse_and_stream_helper(self) -> None:
        sse_src = _read_api("sse.py")
        stream_src = _read_js("sse-stream.js")
        assert "TERMINAL_JOB_STATUSES" in sse_src
        assert "cancelled" in sse_src
        assert (
            "status === 'completed' || status === 'failed' || status === 'cancelled'" in stream_src
        )

    def test_frontend_only_processes_have_real_abort_hooks(self) -> None:
        src = _read_js("course-settings.js")
        assert "function cancelActiveLLMGeneration" in src
        assert "window.cancelActiveLLMGeneration = cancelActiveLLMGeneration" in src
        assert "new AbortController()" in src
        assert "signal: controller.signal" in src
        assert "abortMessage: t('AI generation cancelled.')" in src

    def test_enrichment_stream_treats_cancelled_as_terminal(self) -> None:
        src = _read_dashboard_api("admin/users.py")
        assert 'status_val in ("completed", "failed", "cancelled")' in src

    def test_active_job_filters_include_started_state(self) -> None:
        files = [
            _API / "helpers" / "sync.py",
            _API / "sync.py",
            _API / "sync_stream.py",
            _API / "course_import.py",
            _DASHBOARD_API / "courses" / "routes.py",
            _DASHBOARD_API / "home" / "sync_info.py",
            _ROOT / "src" / "app" / "services" / "courses.py",
        ]
        for path in files:
            src = path.read_text(encoding="utf-8")
            assert '["enqueued", "running"]' not in src, path
            assert '("enqueued", "running")' not in src, path

    def test_workers_do_not_overwrite_cancelled_jobs(self) -> None:
        # Both sync jobs keep their job row through sync_lifecycle: it checks
        # for a cancel when the job starts, completes and fails.
        lifecycle_src = _read_worker("sync_lifecycle.py")
        metrics_src = _read_worker("metrics_job.py")
        assert lifecycle_src.count('if bg_job.status == "cancelled":') == 3
        for job in ("sync_job.py", "sync_project_job.py"):
            src = _read_worker(job)
            for step in ("job.start(", "job.complete(", "job.record_failure("):
                assert step in src, (job, step)
        assert "is_terminal_job_status(bg_job.status)" in metrics_src

    def test_project_detail_uses_stored_gitlab_scope_not_live_fetches(self) -> None:
        src = _read_dashboard_api("projects/routes.py")
        assert "from app.services.gitlab.client import GitLabClient" not in src
        assert "await _resolve_project_member_scope(db, project)" in src
        # The page and its live refresh share one roster, and an unknown scope
        # loads nobody - never the whole team, which shows phantom rows.
        assert src.count("await _project_roster(db, project, team, course)") == 2
        assert 'if memberships and (display_usernames or source == "single_project_team"):' in src

    def test_project_intelligence_api_reads_db_snapshot_not_gitlab(self) -> None:
        src = _read_api("projects.py")
        start = src.index("# -- GitLab Intelligence Endpoints --")
        intelligence_src = src[start:]
        assert "GitLabClient" not in intelligence_src
        assert "raise_service_unavailable" not in intelligence_src
        assert "project.gitlab_intel" in intelligence_src
        assert 'stored.get("protectedBranches")' in intelligence_src
        assert 'stored.get("contributors")' in intelligence_src
        assert 'stored.get("statistics")' in intelligence_src
        assert 'stored.get("milestones")' in intelligence_src
        assert 'stored.get("releases")' in intelligence_src
        assert 'stored.get("labels")' in intelligence_src

    def test_project_member_sync_is_additive_only(self) -> None:
        src = _read_service("member_sync.py")
        start = src.index("async def sync_project_members_into_team(")
        block = src[start:]
        assert "non-destructive" in block
        assert "members_removed +=" not in block
        assert "left_at = now" not in block

    def test_run_checks_use_shared_progress_handler(self) -> None:
        core_src = _read_js("core.js")
        team_src = _read_js("team-detail.js")
        project_src = _read_js("project-detail.js")
        course_src = _read_js("pages/course-detail.js")

        assert "function runScopedChecksProcess" in core_src
        assert "connectGlobalJob(jobKey" in core_src
        assert "streamJobProgress(result.job_id" in core_src
        assert "startGenericStatusPolling(jobKey" in core_src
        assert "runScopedChecksProcess" in team_src
        assert "runScopedChecksProcess" in project_src
        assert "runScopedChecksProcess" in course_src
        assert "Fallback polling (max 60" not in team_src
        assert "Fallback polling (max 60" not in project_src

    def test_webhooks_refresh_stored_project_intelligence(self) -> None:
        event_src = _read_worker("event_processor.py")
        sweep_projects_src = _read_worker("sweep_projects.py")
        sweep_src = _read_worker("sweep.py")

        assert "_enqueue_project_intel_refresh(event.gitlab_project_id)" in event_src
        assert "project_intel_refresh_debounce" in event_src
        assert "def refresh_project_gitlab_intel" in sweep_projects_src
        assert "fetch_gitlab_intel_snapshot" in sweep_projects_src
        assert "refresh_project_gitlab_intel" in sweep_src


# ===================================================
# health-monitor.js - state machine & toast correctness
# ===================================================


class TestHealthMonitorStateMachine:
    """Verify health-monitor.js state transitions and toast triggers."""

    @pytest.fixture(autouse=True)
    def _load_source(self) -> None:
        self.src = _read_js("health-monitor.js")

    def test_initial_status_is_unknown(self) -> None:
        """State machine must start in 'unknown' to avoid false recovery toast on first load."""
        assert re.search(r"status:\s*'unknown'", self.src)

    def test_connection_restored_toast_requires_baseline(self) -> None:
        """'Connection restored' must NOT fire on unknown->ok (first-ever success).

        The condition must check that lastOk existed (i.e., we were healthy before).
        """
        # The condition should include _state.lastOk check
        pattern = re.compile(
            r"prevStatus\s*!==\s*'ok'\s*&&\s*prevStatus\s*!==\s*'unknown'\s*&&\s*_state\.lastOk",
        )
        assert pattern.search(self.src), (
            "_handleSuccess must check _state.lastOk before showing 'Connection restored' toast"
        )

    def test_connection_restored_toast_excludes_unknown_to_ok(self) -> None:
        """Transition unknown->ok must not trigger 'Connection restored'."""
        match = re.search(r"prevStatus\s*!==\s*'unknown'", self.src)
        assert match, "Must exclude unknown->ok from recovery toast"

    def test_offline_handler_captures_prev_status(self) -> None:
        """The 'offline' event handler must capture prevStatus BEFORE modifying _state.status.

        BUG FIX: Previously dispatched hardcoded 'unknown' instead of actual previous status.
        Now also distinguishes 'offline' (client) from 'down' (server unreachable).
        """
        offline_block = re.search(
            r"addEventListener\('offline'.*?\}\);",
            self.src,
            re.DOTALL,
        )
        assert offline_block, "offline event handler must exist"
        block = offline_block.group()

        # Must capture previous status before mutation
        assert "prevStatus = _state.status" in block, (
            "offline handler must capture _state.status before modifying it"
        )
        # Must dispatch with captured prevStatus to 'offline' or 'down' (not hardcoded 'unknown')
        assert (
            "_dispatch(prevStatus, 'offline')" in block or "_dispatch(prevStatus, 'down')" in block
        ), "offline handler must dispatch with actual previous status"
        assert "_dispatch('unknown', 'down')" not in block, (
            "offline handler must NOT dispatch hardcoded 'unknown'"
        )

    def test_fail_threshold_is_positive_integer(self) -> None:
        """FAIL_THRESHOLD must be ≥ 2 to avoid false alarms on transient failures."""
        match = re.search(r"FAIL_THRESHOLD\s*=\s*(\d+)", self.src)
        assert match, "FAIL_THRESHOLD must be defined"
        threshold = int(match.group(1))
        assert threshold >= 2, f"FAIL_THRESHOLD={threshold} is too low, needs ≥ 2"

    def test_backoff_capped_at_max(self) -> None:
        """Exponential back-off must be capped by MAX_BACKOFF_MS."""
        assert re.search(r"Math\.min\(.*MAX_BACKOFF_MS\)", self.src), (
            "Back-off must be capped at MAX_BACKOFF_MS"
        )

    def test_banner_dismissed_reset_on_recovery(self) -> None:
        """_bannerDismissed resets to false on 'ok' for future banners."""
        assert "_bannerDismissed = false" in self.src

    def test_meta_refresh_started_with_banner(self) -> None:
        """The 'Last healthy: Xs ago' meta text must be updated while banner is visible."""
        assert "_startMetaRefresh()" in self.src
        assert "_stopMetaRefresh()" in self.src

    def test_beforeunload_cleanup(self) -> None:
        """Timers must be cleaned up on page unload to prevent leaks."""
        block = re.search(
            r"addEventListener\('beforeunload'.*?\}\);",
            self.src,
            re.DOTALL,
        )
        assert block, "beforeunload handler must exist"
        body = block.group()
        assert "clearTimeout(_timerId)" in body or "_timerId = null" in body
        assert "_stopMetaRefresh()" in body


class TestHealthMonitorGitLab:
    """Verify GitLab health check sub-system in health-monitor.js."""

    @pytest.fixture(autouse=True)
    def _load_source(self) -> None:
        self.src = _read_js("health-monitor.js")

    def test_gitlab_banner_requires_baseline(self) -> None:
        """GitLab banner must only show if the server was previously reachable."""
        assert "if (!_glState.hasBaseline || !_glState.lastOk) return;" in self.src

    def test_gitlab_banner_defers_to_main_banner(self) -> None:
        """GitLab banner must not show when the main health banner is already visible."""
        assert "if (_bannerVisible) return;" in self.src

    def test_show_banner_resets_gl_banner_flag(self) -> None:
        """When the main banner takes over, _glBannerVisible must be reset.

        BUG FIX: Previously _glBannerVisible stayed true after main banner overwrote
        the GitLab content, causing a phantom 'GitLab connection restored' toast.
        """
        # _showBanner must reset _glBannerVisible
        show_banner_fn = re.search(
            r"function _showBanner\(status\).*?_bannerVisible = true;",
            self.src,
            re.DOTALL,
        )
        assert show_banner_fn, "_showBanner function must exist"
        body = show_banner_fn.group()
        assert "_glBannerVisible" in body, (
            "_showBanner must reset _glBannerVisible when taking over"
        )

    def test_hide_gl_banner_no_toast_when_main_banner_active(self) -> None:
        """'GitLab connection restored' toast must not fire if the main banner is active.

        This prevents misleading toasts when the GitLab recovery happens
        while the main health banner was already showing. The toast is also
        gated behind an explicit ``notify`` argument so a *manual dismiss*
        never shows a phantom "restored" message.
        """
        hide_fn = re.search(
            r"function _hideGlBanner\(notify\).*?(?=\n  function |\n  /\*)",
            self.src,
            re.DOTALL,
        )
        assert hide_fn, "_hideGlBanner(notify) function must exist"
        body = hide_fn.group()
        assert re.search(r"if \(notify && !_bannerVisible && window\.showToast\)", body), (
            "_hideGlBanner must gate the toast on both notify and !_bannerVisible"
        )

    def test_gl_banner_dismissal_is_sticky(self) -> None:
        """Dismissing the GitLab banner must use its OWN flag, not the shared one.

        REGRESSION: the GitLab banner shares one DOM strip with the app-health
        banner but has an independent lifecycle. Previously both used
        ``_bannerDismissed``; every successful /health poll reset it to false,
        so a dismissed GitLab banner reappeared ~30s later. The GitLab banner
        must key off a separate ``_glBannerDismissed`` that only a genuine
        GitLab recovery clears.
        """
        assert "_glBannerDismissed" in self.src, "separate GitLab dismissal flag must exist"
        # _showGlBanner must respect the GitLab-specific dismissal flag.
        show_fn = re.search(
            r"function _showGlBanner\(\).*?(?=\n  function |\n  /\*)",
            self.src,
            re.DOTALL,
        )
        assert show_fn, "_showGlBanner function must exist"
        assert "_glBannerDismissed" in show_fn.group(), (
            "_showGlBanner must bail out when _glBannerDismissed is set"
        )

    def test_main_health_ok_does_not_revive_gl_banner(self) -> None:
        """The app-health 'ok' path must NOT clear the GitLab dismissal flag.

        This is the core of the reappearing-banner regression: _handleSuccess
        may reset _bannerDismissed (its own banner), but must leave
        _glBannerDismissed untouched so a dismissed GitLab banner stays hidden.
        """
        handle_ok = re.search(
            r"function _handleSuccess\(data\).*?(?=\n  function )",
            self.src,
            re.DOTALL,
        )
        assert handle_ok, "_handleSuccess function must exist"
        assert "_glBannerDismissed" not in handle_ok.group(), (
            "_handleSuccess must not touch _glBannerDismissed"
        )

    def test_gl_recovery_clears_gl_dismissal(self) -> None:
        """A real GitLab recovery must clear _glBannerDismissed so a future
        outage can surface a fresh banner."""
        check_fn = re.search(
            r"async function _checkGitLab\(\).*?(?=\n  function _glHandleFail)",
            self.src,
            re.DOTALL,
        )
        assert check_fn, "_checkGitLab function must exist"
        assert "_glBannerDismissed = false" in check_fn.group(), (
            "GitLab recovery path must reset _glBannerDismissed"
        )

    def test_gl_banner_meta_ticks_live(self) -> None:
        """The GitLab banner's 'Last connected' age must refresh, not freeze.

        _showGlBanner must route its meta through the shared _updateBannerMeta
        + _startMetaRefresh (which reads _glState.lastOk), so the age keeps
        ticking instead of freezing at the value it had when first shown.
        """
        show_fn = re.search(
            r"function _showGlBanner\(\).*?(?=\n  function |\n  /\*)",
            self.src,
            re.DOTALL,
        )
        assert show_fn, "_showGlBanner function must exist"
        body = show_fn.group()
        assert "_updateBannerMeta()" in body, "_showGlBanner must refresh the meta on show"
        assert "_startMetaRefresh()" in body, "_showGlBanner must start the live meta ticker"
        # _updateBannerMeta must know how to render the GitLab "Last connected"
        # variant from _glState (not only the main-health "Last healthy").
        assert re.search(r"_glState\.lastOk", self.src), "meta must read _glState.lastOk"
        assert "Last connected" in self.src, "GitLab banner meta must show 'Last connected'"

    def test_gitlab_fail_threshold_separate(self) -> None:
        """GitLab must have its own failure threshold (GL_FAIL_THRESHOLD)."""
        match = re.search(r"GL_FAIL_THRESHOLD\s*=\s*(\d+)", self.src)
        assert match
        assert int(match.group(1)) >= 2

    def test_gitlab_check_skipped_when_hidden(self) -> None:
        """GitLab check should skip when tab is hidden to save bandwidth."""
        check_fn = re.search(
            r"async function _checkGitLab\(\).*?(?=\n  function )",
            self.src,
            re.DOTALL,
        )
        assert check_fn
        assert "document.hidden" in check_fn.group()


# ===================================================
# sse-stream.js - SSE->polling fallback
# ===================================================


class TestSseStreamFallback:
    """Verify SSE-to-polling fallback logic in sse-stream.js."""

    @pytest.fixture(autouse=True)
    def _load_source(self) -> None:
        self.src = _read_js("sse-stream.js")

    def test_sse_falls_back_to_polling_on_max_errors(self) -> None:
        """After maxErrors, SSE must close and fall back to polling."""
        assert "source.close();" in self.src
        assert "startPollingFallback(" in self.src

    def test_sse_falls_back_when_backend_down(self) -> None:
        """When health.isDown is true, SSE must fall back to polling (not silently die).

        BUG FIX: Previously SSE was closed without starting polling fallback,
        causing job progress to silently stop.
        """
        onerror_block = re.search(
            r"source\.onerror\s*=.*?};",
            self.src,
            re.DOTALL,
        )
        assert onerror_block, "source.onerror handler must exist"
        body = onerror_block.group()

        # When isDown, must call startPollingFallback (not just return)
        is_down_section = body[body.index("isDown") :] if "isDown" in body else ""
        assert "startPollingFallback(" in is_down_section, (
            "SSE onerror must start polling fallback when backend is down"
        )
        # Must NOT have a bare 'return;' after isDown without fallback
        lines_after_down = is_down_section.split("\n")
        found_fallback_before_return = False
        for line in lines_after_down:
            if "startPollingFallback(" in line:
                found_fallback_before_return = True
                break
            if line.strip() == "return;" and "startPollingFallback" not in line:
                break
        assert found_fallback_before_return, (
            "Polling fallback must be started before return in isDown branch"
        )

    def test_sse_triggers_health_check_on_first_error(self) -> None:
        """First SSE error must trigger an immediate health check."""
        assert "errorCount === 1" in self.src
        assert "health.check()" in self.src or "health?.check()" in self.src

    def test_sse_fallback_stops_if_error_callback_closes_controller(self) -> None:
        """An error callback may close the controller before internal polling starts."""
        fallback_fn = re.search(
            r"function startPollingFallback\(reasonError\).*?state\.mode = 'polling';",
            self.src,
            re.DOTALL,
        )
        assert fallback_fn, "startPollingFallback must exist"
        body = fallback_fn.group()
        emit_idx = body.index("emitError(reasonError);")
        recheck_idx = body.index("if (state.closed)", emit_idx)
        mode_idx = body.index("state.mode = 'polling';")
        assert emit_idx < recheck_idx < mode_idx, (
            "startPollingFallback must re-check state.closed after emitError"
        )

    def test_sse_disabled_option_falls_straight_to_polling(self) -> None:
        """disableSse: true must skip EventSource entirely."""
        assert "config.disableSse" in self.src

    def test_controller_close_prevents_duplicate_callbacks(self) -> None:
        """After close(), neither onUpdate nor onComplete must fire."""
        assert "if (state.closed)" in self.src

    def test_polling_fallback_uses_api_call(self) -> None:
        """Manual polling fallback must use apiCall for retries and CSRF."""
        assert "new GP.PollingController(config.pollUrl" in self.src
        assert "maxErrors: Infinity" in self.src

    def test_callbacks_cannot_leave_stream_open(self) -> None:
        """Callback exceptions must not keep a completed stream alive."""
        assert "function callCallback(callback, payload)" in self.src
        assert "finally {\n      controller.close();" in self.src


class TestGlobalJobBarState:
    """Verify global job bar state stays minimal and current."""

    @pytest.fixture(autouse=True)
    def _load_source(self) -> None:
        self.src = "\n".join(
            (_STATIC_JS / "_parts" / "global-job-bar" / name).read_text(encoding="utf-8")
            for name in ("00-state-polling.js", "10-sse-render.js", "20-listeners-api.js")
        )

    def test_removed_eta_state_is_not_persisted(self) -> None:
        """ETA UI was removed; the old state key must not leak across tabs."""
        assert not re.search(r"\beta\s*:", self.src)
        assert not re.search(r"\.eta\b", self.src)

    def test_finishing_has_no_timer_that_can_invent_success(self) -> None:
        """Only a server response can finish pending work, including after reload."""
        assert "FINISHING_MIN_VISIBLE_MS" not in self.src
        assert "_scheduleFinishingCompletion" not in self.src
        assert "finishGlobalJobReadable" not in self.src
        assert "payload[jobType].lastUpdate = job.lastUpdate;" in self.src

    def test_finishing_restore_revalidates_with_indeterminate_progress(self) -> None:
        assert "status: value.status === 'finishing' ? 'running'" in self.src
        assert "progress: value.status === 'finishing' ? null" in self.src
        assert "if (v.meta?.jobId) return;" in self.src

    def test_course_detail_waits_for_a_confirmed_terminal_snapshot(self) -> None:
        course = _read_js("pages/course-detail.js")
        assert "const isFinishing = !hasSyncWork && data.has_active_sync === true;" in course
        assert "window.markCourseSyncFinishing(COURSE_ID, msg);" in course
        assert "_FINISHING_FALLBACK_MS" not in course
        assert "_DONE_RELOAD_DELAY_MS" not in course
        assert "data?.has_active_sync !== false" in course
        assert "_inactivePolls >= 2" in course

    def test_complete_global_job_reports_terminal_ownership(self) -> None:
        """Components need a true/false signal to avoid duplicate fallback toasts."""
        assert "if (!job) {\n    return false;" in self.src
        assert (
            "if (job.status === 'done' || job.status === 'error') {\n    return true;" in self.src
        )
        complete_fn = re.search(
            r"function completeGlobalJob\(.*?^\}",
            self.src,
            re.DOTALL | re.MULTILINE,
        )
        assert complete_fn, "completeGlobalJob must exist"
        assert "return true;" in complete_fn.group()

    def test_terminal_transition_requires_an_explicit_server_status(self) -> None:
        assert "function _completeStatusJob(jobType, data, onDone, onFailed)" in self.src
        assert "if (status === 'completed') return completeGlobalJob" in self.src
        assert "if (status === 'failed') return completeGlobalJob" in self.src
        assert "if (status === 'cancelled') return completeGlobalJob" in self.src
        assert "onDone({})" not in self.src

    def test_storage_removal_cannot_report_success(self) -> None:
        merge = self.src.split("function _mergeStoredJobs(remote) {", 1)[1]
        merge = merge.split("window.addEventListener('storage'", 1)[0]
        assert "if (!remote[jobType] && _isUiTerminalStatus(job.status)) hideGlobalJob" in merge
        assert "new CustomEvent" not in merge

    def test_global_job_bar_removal_no_longer_depends_on_appearance_animations(self) -> None:
        """Finished/dismissed rows should disappear deterministically, not via CSS timing."""
        state_src = (_STATIC_JS / "_parts" / "global-job-bar" / "00-state-polling.js").read_text(
            encoding="utf-8"
        )
        render_src = (_STATIC_JS / "_parts" / "global-job-bar" / "10-sse-render.js").read_text(
            encoding="utf-8"
        )
        navbar_css = _read_css("navbar.css")

        assert (
            "function _animateJobExit(item, jobType) {\n  hideGlobalJob(jobType);\n}" in state_src
        )
        assert "item.classList.add('job-item-exit')" not in render_src
        assert "animationend" not in state_src
        assert "animationend" not in render_src
        assert "gjb-enter" not in navbar_css
        assert "job-item-enter" not in navbar_css
        assert "job-state-pulse" not in navbar_css

    def test_stuck_connecting_jobs_freed_fast_to_unlock_buttons(self) -> None:
        """An optimistic 'connecting' job (connectGlobalJob sets it on click,
        before the server confirms a run) that never got a backend job_id - a
        refused sync (401) or a restored pre-POST snapshot - must be retired
        quickly. Otherwise it keeps the Sync / Run Checks button process-locked
        for the whole 5-45 min maxAge, and inconsistently across project / team /
        course. The staleness guard frees it after a short window instead.
        """
        state_src = (_STATIC_JS / "_parts" / "global-job-bar" / "00-state-polling.js").read_text(
            encoding="utf-8"
        )
        # Ghosts (no real backend job) are retired fast; genuine runs are exempt
        # on all three counts: a real job_id, a server-confirmed course sync, or
        # a fresh SSE heartbeat.
        assert "_isBackedByRealJob" in state_src
        assert "job.meta && job.meta.jobId" in state_src, "a real job_id exempts the job"
        assert "job.serverConfirmedRunning" in state_src, "server-confirmed syncs are exempt"
        # Team/project syncs must NOT inherit the 45-min course maxAge cap.
        assert "/^sync:(team|project):/" in state_src


class TestTerminalJobToastOwnership:
    """Terminal job states should be emitted by one owner, not each component."""

    def test_core_exposes_terminal_job_fallback_helper(self) -> None:
        src = _read_js("core.js")

        assert "function finishGlobalJobOrToast(" in src
        assert "GP.finishGlobalJobOrToast = finishGlobalJobOrToast;" in src
        assert "const handledByGlobal = typeof completeFn === 'function'" in src

    def test_import_completion_uses_global_job_or_single_fallback_toast(self) -> None:
        src = _read_js("import-stream.js")

        assert "function _finishImportGlobalJob" in src
        assert "completeGlobalJob('import', message, status)" in src
        assert "flashToast(_t('Imported:')" not in src
        assert "flashToast(err.message, 'danger')" not in src

    def test_course_team_sync_completion_does_not_double_toast(self) -> None:
        src = (_STATIC_JS / "_parts" / "course-detail" / "10-teams-crud.js").read_text(
            encoding="utf-8"
        )

        assert "const handledByGlobal = typeof completeGlobalJob === 'function'" in src
        assert "showToast(t('Sync completed successfully'), 'success')" not in src
        assert "showToast(t('Sync failed'), 'danger')" not in src

    def test_team_sync_modal_completion_does_not_double_toast(self) -> None:
        src = (_STATIC_JS / "_parts" / "team-detail" / "10-sync.js").read_text(encoding="utf-8")

        assert "return handledByGlobal;" in src
        assert "if (!handledByGlobal) showToast(doneMsg, 'success');" in src
        assert not re.search(
            r"showSyncError\(t\?\.\('Sync Failed'\).*?;\s*showToast\?\.\(",
            src,
            re.DOTALL,
        )

    def test_project_and_team_analysis_completion_do_not_double_toast(self) -> None:
        project_src = (_STATIC_JS / "_parts" / "project-detail" / "10-analysis.js").read_text(
            encoding="utf-8"
        )
        team_src = (_STATIC_JS / "_parts" / "team-detail" / "20-analysis-boot.js").read_text(
            encoding="utf-8"
        )

        assert "flashToast(t('AI analysis completed successfully')" not in project_src
        assert (
            "GP.finishGlobalJobOrToast('analysis', doneMsg, 'done', { flash: true });"
            in project_src
        )
        assert "showToast(data.message || t('AI Analysis completed!')" not in team_src
        assert "showGlobalJob(message, 'analysis', {" in team_src
        assert "completeGlobalJob(" not in team_src
        assert "new EventSource(" not in team_src

    def test_course_settings_llm_generation_does_not_double_toast(self) -> None:
        src = (_STATIC_JS / "_parts" / "course-settings" / "30-llm-generate.js").read_text(
            encoding="utf-8"
        )

        assert (
            "GP.finishGlobalJobOrToast('llm_generate', message, 'done', { type: 'warning' });"
            in src
        )
        assert (
            "GP.finishGlobalJobOrToast('llm_generate', message, 'error', "
            "cancelled ? { type: 'warning' } : undefined);" in src
        )
        assert "showToast(t('LLM returned no suggestions'), 'warning')" not in src
        assert "completeGlobalJob('llm_generate', t('Generation failed'), 'error')" not in src

    def test_course_analytics_no_dead_report_job(self) -> None:
        src = (_STATIC_JS / "_parts" / "course-analytics" / "10-refresh.js").read_text(
            encoding="utf-8"
        )
        global_src = (_STATIC_JS / "_parts" / "global-job-bar" / "00-state-polling.js").read_text(
            encoding="utf-8"
        )

        legacy_job_type = "pdf" + "_" + "report"
        legacy_form_selector = "#" + "report" + "Form"
        assert legacy_job_type not in src
        assert legacy_form_selector not in src
        assert legacy_job_type not in global_src
        assert legacy_form_selector not in global_src


class TestDashboardLiveRefreshContracts:
    """Dashboard live-refresh contracts should stay coherent."""

    def test_dashboard_live_refresh_helper_updates_all_home_fragments(self) -> None:
        src = _read_js("pages/dashboard.js")
        helper = re.search(
            r"function refreshDashboardLive\(options\).*?return Promise\.allSettled\(tasks\);",
            src,
            re.DOTALL,
        )
        assert helper, "dashboard.js must centralize live refresh fan-out"
        body = helper.group()

        assert "refreshDashboardStats()" in body
        assert "refreshAttentionItems()" in body
        assert "refreshActivityFeed()" in body
        assert "window.GP?._sidebar?.pollBadges" in body
        assert "refreshDashboardLive({ includeSidebar: true });" in src


class TestCurrentUiRegressionContracts:
    """Guard the concrete UI contracts requested for this cleanup pass."""

    def test_the_users_page_pages_once(self) -> None:
        """One table, so one pagination bar and one paginator.

        The service accounts used to be a second table with a second bar and a
        second `ClientPaginator` scoped to the panel around it. They are rows in
        the users table now, so a second of either would be paging nothing.
        """
        template = _read_template("partials/admin/_users_content.html")
        js = _read_js("pages/admin-users.js")
        css = _read_css("navbar.css")

        assert template.count("pagination_controls(") == 1
        assert "serviceAccounts" not in template
        assert "serviceAccounts" not in js
        assert js.count("new ClientPaginator(") == 1
        assert "details .pagination-controls" not in css
        assert "details.card .card-body:not(.p-0) > .pagination-controls" in css

    def test_dashboard_role_stats_config(self) -> None:
        # The dashboard stat-cards config (home/stats.py) exposes the group + open-MR
        # stats.
        stats = (_DASHBOARD_API / "home" / "stats.py").read_text(encoding="utf-8")
        assert stats.count('"id": "statGroups"') == 2
        assert stats.count('"id": "statOpenMrs"') == 1

    def test_project_members_table_uses_shared_head_macro(self) -> None:
        # Pages are server-rendered inline (GitLab-style) in one response. The live
        # project-members table sources its column matrix from the ONE shared head
        # macro, so the columns (incl. actions, hidden-source) stay in lockstep.
        live = _read_template("partials/project/_members_table.html")
        heads = _read_template("components/table_heads.html")

        # Both call sites (student view and teacher view) carry the same class
        # contract, and both pin the Actions column - the only table with one
        # that did not, so its View buttons scrolled out of reach.
        assert live.count("table-sticky-actions") == 2
        assert "table-sticky-first" not in live, (
            "that class does nothing: 84c8ac3b removed the rule behind it"
        )
        assert '<col class="col-member-actions">' in heads
        assert '<col class="col-member-source col-hide-lg">' not in heads
        assert "project_members_head_full(checks)" in live

    def test_responsive_css_keeps_all_tables_scrollable_without_card_collapse(
        self,
    ) -> None:
        tables = _read_css("tables.css")
        mobile = _read_css("_parts/responsive/00-mobile.css")
        course = _read_css("pages/course.css")

        # Card-collapse mode was removed - every data table now uses one uniform
        # horizontal-scroll model, so the .table-cards CSS must be gone.
        assert ".data-table.table-cards {" not in tables
        assert ".data-table:not(.table-no-cards)" not in tables
        mobile_matrix_selector = (
            ".table-responsive .data-table.table-scrollable"
            ":not(.team-members-table):not(.project-members-table)"
        )
        assert mobile_matrix_selector in mobile
        assert ".table-responsive .data-table:not(.data-table--fixed-3col)" not in mobile
        # No table-level width floor on the member matrices. `.data-table` is
        # width:100%, so a floor ABOVE the columns' own sum reserves nothing -
        # `table-layout: auto` hands the surplus back to the columns. At 1320px
        # against 1010px of content, each of the thirteen check columns grew
        # from 48px to 67px to hold one 16px tick, while the names beside them
        # were cut with an ellipsis.
        assert "min-width: 1320px" not in course
        # The matrix is sized by its content and shares the surplus among all
        # its columns: no percentages that cut "R01" to "R...", and no column
        # told to take the whole surplus (the name stood beside 200px of air).
        members = course.split("MEMBER TABLES", 1)[1].split("PROJECTS TABLE", 1)[0]
        assert "width: 1%" not in members
        assert "table-layout: fixed" not in members
        assert "min-width: 1180px" not in course, "a fixed floor that the content already sets"

    def test_stale_snapshot_banner_reports_partial_group_coverage(self) -> None:
        helpers = (_DASHBOARD_API / "_helpers.py").read_text(encoding="utf-8")
        alerts = _read_template("components/alerts.html")
        analytics = _read_template("partials/course/_analytics_content.html")
        activity = _read_template("partials/course/_activity_content.html")

        assert "func.count(func.distinct(TeamMetricSnapshot.team_id))" in helpers
        assert "current_week_groups < total_active_groups" in helpers
        assert "current week has not been synced yet" not in alerts
        assert "Some groups do not have a current-week analytics snapshot yet." in alerts
        assert "current_week_groups=current_week_groups|default(0)" in analytics
        assert "total_active_groups=total_active_groups|default(0)" in activity

    def test_auth_pages_use_system_alert_and_exit_fade(self) -> None:
        login = _read_template("login.html")
        login_css = _read_css("login.css")
        logout_js = _read_js("pages/logout.js")

        assert "{{ alert(t('Your GitPulse session has ended.')" in login
        assert "login-logged-out" not in login
        # The logged-out notice is server-rendered and permanent, so it must not
        # animate in. That used to need a `--static` modifier switching off an
        # entrance declared on the base class; GP.motion animates only alerts it
        # is asked to, so the suppression - and the modifier - are gone.
        assert "login-auth-alert--static" not in login
        assert "login-auth-alert--static" not in login_css
        # The exit treatment is gone at the user's request: it lifted the card
        # 4px (measured 137px -> 133px top) and held the navigation 140ms to
        # play that lift, while its `opacity: 0` never applied at all -
        # `.login-card` carries `animation: fadeIn ... both`, and a filled
        # animation outranks a plain declaration. See
        # tests/unit/test_auth_card_has_no_lift.py.
        assert "auth-is-leaving" not in login_css
        assert "auth-is-leaving" not in logout_js

    def test_team_header_actions_stay_on_right(self) -> None:
        template = _read_template("team_detail.html")

        assert "page-header--actions-below" not in template

    def test_team_visible_refresh_is_single_flight(self) -> None:
        src = (_STATIC_JS / "_parts" / "team-detail" / "30-live.js").read_text(encoding="utf-8")

        assert "let _lastVisibleRefreshAt = 0;" in src
        assert "if (now - _lastVisibleRefreshAt < 800)" in src
        assert "resumeTeamAnalysis();" in src
        analysis = (_STATIC_JS / "_parts" / "team-detail" / "20-analysis-boot.js").read_text(
            encoding="utf-8"
        )
        assert "analysisProbe || isGlobalJobRunning('analysis')" in analysis
        assert "if (analysisProbe === read) analysisProbe = null;" in analysis

    def test_reload_carries_no_dead_scroll_state(self) -> None:
        """A reload lands at the top on purpose, so nothing saves a scroll offset.

        `_gp_scroll_y` was written before every reload, cleared before every row
        navigation and read back by nobody - the restore it fed was replaced by
        `_resetScrollOnLoad`, which starts every load at the top. Reading the
        offset also forced a layout on the way out of the page.
        """
        core = _read_js("core.js")
        reload = (_STATIC_JS / "_parts" / "core" / "16-reload.js").read_text(encoding="utf-8")

        assert "_gp_scroll_y" not in core
        assert "clearReloadScroll" not in core
        # The flag theme-bootstrap reads pre-paint still has to be written.
        assert "sessionStorage.setItem('_gp_silent_reload', '1')" in reload

    def test_llm_analysis_uses_effective_production_gate(self) -> None:
        config = Path("src/app/config.py").read_text(encoding="utf-8")
        project_routes = Path("src/app/api/dashboard/projects/llm.py").read_text(encoding="utf-8")
        team_routes = Path("src/app/api/dashboard/teams/llm.py").read_text(encoding="utf-8")
        worker = Path("src/app/workers/llm_job.py").read_text(encoding="utf-8")

        assert "def llm_analysis_enabled" in config
        assert "return self.feature_llm_suggestions and not self.is_production" in config
        # The surfaces read the effective gate only; a fallback to the raw
        # flag would let production expose the analysis the gate hides.
        for src in (project_routes, team_routes, worker):
            assert "settings.llm_analysis_enabled" in src
            assert "feature_llm_suggestions" not in src


class TestSharedDropdownContracts:
    """Standalone and shell dropdowns use one CSP-safe controller."""

    def test_user_and_language_menus_use_shared_controller(self) -> None:
        header = _read_template("components/header.html")
        forms = _read_template("components/forms.html")
        controller = _read_js("dropdowns.js")

        assert "data-dropdown-toggle" in header
        assert "data-dropdown-menu" in header
        assert 'x-data="userMenu"' not in header
        assert "gl-lang-selector-label" in forms
        assert "selected_locale.label" in forms
        assert "closeAll(root)" in controller
        assert "event.key === 'Escape'" in controller

    def test_select_field_has_server_rendered_label(self) -> None:
        forms = _read_template("components/forms.html")

        assert "initial_selection.label" in forms
        assert ">{{ initial_selection.label }}</span>" in forms


class TestSharedTourContracts:
    """Shell behavior should be explained consistently on every page tour."""

    def test_appearance_step_is_registered_once_as_a_shared_step(self) -> None:
        engine = (_STATIC_JS / "_parts" / "tours" / "00-engine.js").read_text(encoding="utf-8")
        public_api = (_STATIC_JS / "_parts" / "tours" / "10-render.js").read_text(encoding="utf-8")
        content = (_STATIC_JS / "_parts" / "tours" / "20-courses.js").read_text(encoding="utf-8")

        assert "const sharedStepGroups = new Map();" in engine
        assert "const registerSharedSteps = (key, steps) =>" in engine
        assert "...(tour.steps || []), ...sharedSteps" in engine
        assert "registerSharedSteps," in public_api
        assert "registerSharedSteps('appearance'," in content
        assert content.count("title_en: 'Appearance &amp; account menu'") == 1

    def test_header_exposes_stable_theme_tour_targets(self) -> None:
        header = _read_template("components/header.html")
        switcher = _read_template("components/theme_switcher.html")

        assert 'data-tour="user-menu"' in header
        assert 'data-tour="theme-switcher"' in switcher


class TestBackendLiveUpdateContracts:
    """Backend live-update events must not race commits or page-cache invalidation."""

    def test_course_settings_event_publishes_after_commit_and_cache_invalidation(self) -> None:
        courses_path = (
            Path(__file__).resolve().parent.parent.parent / "src" / "app" / "api" / "courses.py"
        )
        src = courses_path.read_text(encoding="utf-8")
        start = src.index("async def update_course_settings(")
        end = src.index("\n\n\n# -- Course Lifecycle", start)
        handler = src[start:end]
        assert handler.index("await db.flush()") < handler.index(
            "await configuration.after_settings_update(db, course_id, cs)"
        )
        src = (_ROOT / "src/app/services/course_settings.py").read_text(encoding="utf-8")
        start = src.index("async def after_settings_update(")
        end = src.index("\n\n\n", start)
        body = src[start:end]

        commit_at = body.index("await db.commit()")
        invalidate_at = body.index("invalidate_course_settings_cache(course_id, team_ids)")
        publish_at = body.index("publish_course_settings_changed(")
        recompute_at = body.index("enqueue_course_settings_recompute")

        assert commit_at < invalidate_at < publish_at < recompute_at
        assert "publish_dashboard_update(" not in body

    def test_project_sync_completion_uses_shared_reload_helper(self) -> None:
        src = (_STATIC_JS / "_parts" / "project-detail" / "20-mr-ci.js").read_text(encoding="utf-8")

        assert "setTimeout(() => { reloadKeepScroll(); }, 1200);" in src
        assert "setTimeout(() => { window.location.reload(); }, 1200);" not in src

    def test_support_ticket_updates_use_shared_request_states(self) -> None:
        src = (_STATIC_JS / "pages" / "support-ticket-detail.js").read_text(encoding="utf-8")

        assert "GP.refreshRegion({" in src
        assert "GP.sse({" in src
        assert "this._injectComment({ ...comment" in src
        assert "setTimeout" not in src
        assert "GP.hasUnsavedState()" in src
        assert "if (!discard || !current()) return;" in src
        assert "window.location.reload()" not in src

    def test_reload_keep_scroll_bypasses_page_cache_and_cleans_the_url(self) -> None:
        src = (_STATIC_JS / "_parts" / "core" / "16-reload.js").read_text(encoding="utf-8")
        body = re.search(
            r"function reloadKeepScroll\(\) \{.*?\n\}",
            src,
            re.DOTALL,
        )

        assert "const _REFRESH_PARAM = '_gp_refresh';" in src
        assert "function _cacheBustedCurrentUrl()" in src
        assert "url.searchParams.set(_REFRESH_PARAM, String(Date.now()));" in src
        assert "window.location.assign(_cacheBustedCurrentUrl());" in src
        assert "url.searchParams.delete(_REFRESH_PARAM);" in src
        assert (
            "window.history.replaceState(window.history.state, '', clean || url.pathname);" in src
        )
        assert "GP.cacheBustedCurrentUrl = _cacheBustedCurrentUrl;" in src
        assert body, "reloadKeepScroll must stay explicit and reviewable"
        assert "location.reload" not in body.group()

    def test_owned_refresh_paths_do_not_use_raw_page_reload(self) -> None:
        paths = (
            _STATIC_JS / "import-stream.js",
            _STATIC_JS / "pull-to-refresh.js",
            _STATIC_JS / "locale-sync.js",
            _STATIC_JS / "error-actions.js",
            _STATIC_JS / "pages" / "admin-users.js",
        )

        for path in paths:
            src = path.read_text(encoding="utf-8")
            assert "window.location.reload(" not in src, path
            assert "location.reload(" not in src, path

    def test_sync_jobs_report_no_change_completion_reason(self) -> None:
        project_src = (
            Path(__file__).resolve().parent.parent.parent
            / "src"
            / "app"
            / "workers"
            / "sync_project_job.py"
        ).read_text(encoding="utf-8")
        team_src = (
            Path(__file__).resolve().parent.parent.parent
            / "src"
            / "app"
            / "workers"
            / "sync_job.py"
        ).read_text(encoding="utf-8")

        counts_src = (
            Path(__file__).resolve().parent.parent.parent
            / "src"
            / "app"
            / "workers"
            / "project_sync.py"
        ).read_text(encoding="utf-8")

        assert "No GitLab records found in the configured course window" in counts_src
        assert 'counts.summary("project timestamp and metrics refresh completed.")' in project_src
        assert 'counts.summary("team metrics and cache refresh completed.")' in team_src
        assert "{self.commits} commits" in counts_src


class TestFullConfigImportContract:
    """Frontend preview/confirm and backend apply paths must share the same full-config contract."""

    def test_shared_full_config_import_defaults_to_current_schema(self) -> None:
        src = _read_js("config-import.js")
        template = _read_template("components/_config_import_body.html")

        assert "config.$schema = 'gitpulse/full-config/v2';" in src
        assert '"$schema": "gitpulse/full-config/v2"' in template
        assert "gitpulse/full-config/v1" not in src
        assert "gitpulse/full-config/v1" not in template

    def test_course_settings_confirm_lists_all_backend_sections(self) -> None:
        src = (_STATIC_JS / "_parts" / "course-settings" / "40-full-config.js").read_text(
            encoding="utf-8"
        )
        expected_sections = (
            "course",
            "settings",
            "builtin_checks",
            "custom_checks",
            "weekly_deadlines",
        )

        assert "const FULL_CONFIG_SECTION_KEYS = [" in src
        assert "FULL_CONFIG_SECTION_KEYS.forEach" in src
        for section in expected_sections:
            assert f"'{section}'" in src


class TestDashboardQuickAccessContracts:
    """Dashboard shortcuts must navigate to the entity they visually represent."""

    def test_project_quick_access_links_to_project_page(self) -> None:
        template = _read_template("partials/dashboard/_sidebar.html")

        assert '<a href="/dashboard/projects/{{ p.id }}" class="gl-qa-item">' in template
        assert '<a href="/dashboard/teams/{{ p.team_id }}" class="gl-qa-item">' not in template


class TestProcessActionGuardContracts:
    """Process guards should protect writes without breaking passive controls."""

    @pytest.fixture(autouse=True)
    def _load_source(self) -> None:
        self.src = _read_js("process-action-guards.js")

    def test_filters_tabs_and_quick_access_tabs_bypass_process_intercepts(self) -> None:
        assert "function isPassiveUiControl" in self.src
        for selector in (
            ".check-filter-btn",
            ".tab-btn",
            '[role="tab"]',
            "[data-filter]",
        ):
            assert selector in self.src
        assert "if (isPassiveUiControl(event.target)) return;" in self.src
        # Quick access switches its views with the shared filter_tabs, so its
        # tabs are `.tab-btn` and pass the same way.
        sidebar = _read_template("partials/dashboard/_sidebar.html")
        assert "filter_tabs([" in sidebar
        assert "panels=true" in sidebar

    def test_guard_bypass_does_not_apply_to_real_write_actions(self) -> None:
        for selector in (
            "[data-action]",
            "[data-modal-open]",
            "[data-sync-trigger]",
            "[data-process-write]",
        ):
            assert selector in self.src


class TestResponsiveLoadingContracts:
    """Loading states must follow the same responsive layout as real data."""

    def test_one_table_loading_state_and_no_fake_rows_anywhere(self) -> None:
        """A table has exactly ONE loading state, and it is not a fake row.

        No row-shaped placeholder exists in the app: each one would draw a
        second copy of its table's markup, column for column, kept in sync by
        hand, with a guessed row count whose miss resizes the card when the
        data lands. The loading state is `sk_table_loading` - one centred box
        in the same shape as the empty state, spanning every column - handed
        over to GP.tableLoading, which keeps the rows a table already has and
        only dims them.
        """
        template = _read_template("components/loaders.html")

        assert "sk_table(" not in template  # dead generic macro must stay gone
        assert "sk_job_tbody_rows" not in template
        assert "sk_dlq_tbody_rows" not in template
        assert "{% macro sk_table_loading(" in template
        assert "table-loading-state" in template
        assert 'colspan="{{ cols }}"' in template

        # A single cell spanning every column needs no per-column mobile label.
        assert "data-label" not in template

        # No macro may render a fake table row again.
        code = _code_only(template)
        assert "sk_compliance_checks_tbody_rows" not in code
        assert "sk_webhook_configs_tbody_rows" not in code
        assert "sk_table_cell" not in code
        assert "gl-table-" not in code

        # Both settings tables render their actual rows before page scripts run.
        for page, rows in (
            (
                "partials/course_settings/_webhook_settings.html",
                "partials/course_settings/_webhook_rows.html",
            ),
            (
                "partials/course_settings/_compliance_settings.html",
                "partials/course_settings/_check_rows.html",
            ),
        ):
            markup = _read_template(page)
            assert f'include "{rows}"' in markup, f"{page}: render the shared rows on the server"
            assert "gl-table-" not in _code_only(markup), page

    def test_loaders_css_carries_only_the_spinner_states(self) -> None:
        """Every waiting state is the spinner + label: the block loader for a
        region, the table loading state for a tbody. No grey-bar placeholder
        rule may come back."""
        css = _code_only(_read_css("loaders.css"))

        assert "gl-table-" not in css
        assert "gl-skel" not in css
        assert "gl-chart-skel" not in css
        assert "gl-sk-" not in css
        assert ".gp-block-loading {" in css
        assert ".table-loading-state" in _code_only(_read_css("tables.css"))

    def test_table_heads_share_one_macro_so_columns_cannot_drift(self) -> None:
        """Every rendering of a table must take its <thead> from the shared head
        macro - never an inlined, hand-maintained copy that can silently drift
        (e.g. plain <th> with no sortable header)."""
        heads = _read_template("components/table_heads.html")
        loaders = _read_template("components/loaders.html")
        users = _read_template("partials/admin/_users_content.html")
        detail = _read_template("partials/course/_detail_content.html")

        tickets = _read_template("partials/support/_tickets_content.html")
        proj_members = _read_template("partials/project/_members_table.html")
        team_members = _read_template("partials/team/_detail_content.html")

        # Single definitions.
        assert "macro users_table_head(" in heads
        assert "macro teams_table_head(" in heads
        assert "macro tickets_table_head(" in heads
        assert "macro project_members_head_basic(" in heads
        assert "macro project_members_head_full(" in heads
        assert "macro team_members_head_basic(" in heads
        assert "macro team_members_head_summary(" in heads

        # Live tables call the shared head macro.
        assert "users_table_head()" in users
        assert "teams_table_head(" in detail
        assert "tickets_table_head()" in tickets
        # Member tables (project + group), both privacy and full/summary views.
        assert "project_members_head_basic()" in proj_members
        assert "project_members_head_full(checks)" in proj_members
        assert "team_members_head_basic()" in team_members
        assert "team_members_head_summary()" in team_members
        # The per-check <th> and the th-center-50 score/status heads live ONLY
        # in the shared macro - loaders.html must not inline its own copies.
        assert 'class="th-check"' not in loaders
        assert 'class="th-center-50"' not in loaders

        # No inlined users head (plain <th>, no sortable_header) - it comes from
        # the shared macro (which uses sortable_header).
        assert "<th class=\"col-username\">{{ t('Username') }}</th>" not in loaders
        # No inlined tree-toggle + plain Group head either.
        assert (
            '<th class="col-tree-toggle col-hide-sm" aria-label="{{ t(\'Expand\') }}"></th>'
            not in loaders
        )

    def test_student_pipeline_test_status_uses_badges_not_raw_text(self) -> None:
        # MR rendering moved into the shared, MR-centric component library.
        template = _read_template("components/student.html")

        assert "pipeline-test-badges" in template
        assert "t('Tests')" in template
        assert "t('tests:')" not in template

    def test_issues_to_address_chart_animates_on_first_reveal_only(self) -> None:
        """The Issues chart plays the staggered entrance animation once, on its
        first reveal (consistent with the other dashboard charts), but never
        replays it on live-data refreshes - those replace the whole container
        and would otherwise re-animate on every exclude/include, run-checks, or
        role change."""
        src = _read_js("project-detail.js")

        # No fragile window-global key map (the previous approach that leaked the
        # "already animated" flag across SPA navigations).
        assert "window.__gpIssuesChartAnimatedKeys" not in src
        # The entrance animation is gated on the per-render `_animate` flag, not
        # unconditional, so it can be suppressed on re-renders.
        assert "animation: _animate ?" in src
        # The live-data re-render path explicitly disables the animation so it
        # cannot replay on every refresh.
        assert "initIssuesChart({ animate: false })" in src


class TestAdminUsersTableContracts:
    """Admin users table, filters, and live updates stay structurally aligned."""

    def test_role_filter_is_one_accessible_tab_strip(self) -> None:
        """Picking one of five views of one table is switching, not filtering,
        so it is drawn as the tab strip the course sub-navigation uses - and it
        announces itself as tabs, not as pressed buttons."""
        template = _read_template("partials/admin/_users_content.html")
        layout = _read_template("components/layout.html")
        components = _read_js("components.js")

        assert "filter_tabs(" in template
        assert "class='users-role-filter'" in template
        assert "aria_label=t('Filter users')" in template
        assert "filter-pill" not in template, "the pills are back"
        assert 'class="tabs-nav filter-tabs' in layout
        assert 'role="tab"' in layout
        assert "aria-selected=" in layout
        assert "node.setAttribute('aria-selected', String(isActive));" in components

    def test_table_cells_own_their_column_contract_and_compact_actions(self) -> None:
        template = _read_template("partials/admin/_users_content.html")

        for column in (
            "col-username",
            "col-gitlabid",
            "col-fullname",
            "col-email",
            "col-role",
            "col-status",
            "col-created",
            "col-actions",
        ):
            assert f'<td class="{column}' in template
        # One table, so one row template - it was written out twice, once for
        # people and once for bots.
        assert template.count('class="gl-row-actions"') == 1
        assert "btn_icon_only('info'" in template
        assert "btn_icon_only('edit'" in template

    def test_toolbar_columns_and_mobile_scroll_have_page_scoped_layout(self) -> None:
        css = _read_css("pages/admin.css")

        # The header toolbar strip is gone altogether: the search and the
        # filter tabs live in the shared `.table-controls` band (tables.css),
        # and no template renders `.card-filter-toolbar` any more - its rules
        # were dead CSS and were removed with the rest of that report.
        assert ".card-filter-toolbar" not in _read_css("cards.css")
        # The pill-shaped rules went with the pills: a tab strip carries its own
        # look (layout.css) and scrolls sideways rather than wrapping, so the
        # page has nothing left to say about how these are drawn.
        assert ".users-role-filter {" in css
        assert "filter-pill" not in css, "page-scoped pill styling is back"
        assert "grid-template-columns: repeat(4, minmax(0, 1fr))" not in css
        # Narrow viewports hide lower-priority columns by name; the remaining
        # columns scroll inside the shared wrapper.
        assert ".users-table .col-gitlabid { display: none; }" in css
        # Users table scrolls horizontally on phones (no card collapse): its
        # floor holds at every width - 1240px, where every column is as wide as
        # its own label on one line in both languages.
        assert ".users-table.table-scrollable {" in css
        assert ".users-table.table-scrollable { min-width: 1240px; }" in css
        assert "td[data-label]::before" not in css

    def test_live_status_updates_reuse_ssr_status_indicator_markup(self) -> None:
        src = _read_js("pages/admin-users.js")

        assert "function statusIndicatorHtml(isActive)" in src
        assert "status-indicator status-indicator--${variant}" in src
        assert "status-badge status-active" not in src
        assert "status-badge status-inactive" not in src


class TestTourPersistence:
    """Verify guided-tour completion survives DOM drift and fast navigation."""

    @pytest.fixture(autouse=True)
    def _load_source(self) -> None:
        self.src = _read_js("tours.js")

    def test_legacy_completed_scan_uses_real_local_storage_prefix(self) -> None:
        """Old per-stage completion keys include gp_tour_v2: in localStorage."""
        assert "STORAGE_PREFIX + scopedKey(tour.slug, COMPLETED_SUFFIX, role) + ':fp='" in self.src
        assert "STORAGE_PREFIX + completedGlobal + ':fp='" in self.src
        assert "const _prefix = completedGlobal + ':fp='" not in self.src

    def test_seen_sync_survives_navigation_and_retries_failed_posts(self) -> None:
        """Completion POSTs should not be cancelled permanently on quick navigation."""
        sync_fn = re.search(
            r"const syncToServer = \(key\) => \{.*?^\s+};",
            self.src,
            re.DOTALL | re.MULTILINE,
        )
        assert sync_fn, "syncToServer must exist"
        body = sync_fn.group()

        assert "keepalive: true" in body
        assert ".then((response) =>" in body
        assert "_syncedKeys.delete(key)" in body


# ===================================================
# core.js - version detection & toast deduplication
# ===================================================


class TestVersionDetection:
    """Verify app version mismatch detection in core.js."""

    @pytest.fixture(autouse=True)
    def _load_source(self) -> None:
        self.src = _read_js("core.js")

    def test_version_from_meta_tag(self) -> None:
        """Version must be read from <meta name='app-version'> tag."""
        assert 'meta[name="app-version"]' in self.src

    def test_version_header_name(self) -> None:
        """Server version must be read from 'x-app-version' header."""
        assert "x-app-version" in self.src

    def test_infinite_reload_guard(self) -> None:
        """Version reload must have a sessionStorage guard to prevent infinite loops.

        BUG FIX: If the browser serves cached HTML with an old meta tag,
        reload would trigger again with version mismatch, creating a loop.
        """
        check_fn = re.search(
            r"function _checkVersionHeader.*?^}",
            self.src,
            re.DOTALL | re.MULTILINE,
        )
        assert check_fn, "_checkVersionHeader must exist"
        body = check_fn.group()

        # Must use sessionStorage to detect repeated reloads for same version
        assert "sessionStorage" in body, (
            "_checkVersionHeader must use sessionStorage to guard against infinite reload"
        )
        # Must check if we already reloaded for this version
        assert re.search(r"sessionStorage\.getItem", body), (
            "Must read sessionStorage to check for prior reload"
        )
        assert re.search(r"sessionStorage\.setItem", body), (
            "Must write sessionStorage before triggering reload"
        )

    def test_reload_waits_for_a_quiet_moment(self) -> None:
        """The reload must give the reader time to read the toast AND must not
        land in the middle of what they are doing.

        A fixed delay was not enough: `hasUnsavedState` only knows about dirty
        forms, so someone who had just set a filter, opened a menu or started
        typing lost it and saw the page reset itself for no reason they could
        connect to anything. The timer now restarts while the page is being
        touched.
        """
        check_fn = re.search(
            r"function _checkVersionHeader.*?^}",
            self.src,
            re.DOTALL | re.MULTILINE,
        )
        assert check_fn
        body = check_fn.group()

        match = re.search(r"const IDLE_MS = (\d{4,});", body)
        assert match, "the idle window must be a named constant"
        assert int(match.group(1)) >= 5000, "shorter than the toast can be read"

        # Interaction has to restart the wait, not merely be checked once.
        for evt in ("pointerdown", "keydown", "input", "change", "scroll"):
            assert f"'{evt}'" in body, f"{evt} must count as the page being in use"
        assert "Date.now() - _lastTouch" in body
        assert "setTimeout(_tryReload, IDLE_MS - quietFor)" in body

    def test_version_mismatch_flag_prevents_repeated_toasts(self) -> None:
        """Once a version mismatch is detected, subsequent checks must be no-ops."""
        assert "if (_versionMismatch" in self.src


class TestToastDeduplication:
    """Verify toast dedup logic in core.js."""

    @pytest.fixture(autouse=True)
    def _load_source(self) -> None:
        self.src = _read_js("core.js")

    def test_dedup_key_includes_type_and_message(self) -> None:
        """Dedup key must combine type + message to avoid different toasts blocking each other."""
        assert re.search(r"normalizedType\s*\+\s*.*message", self.src)

    def test_dedup_window_is_positive(self) -> None:
        """Dedup window must be a positive duration (in ms)."""
        match = re.search(r"_dedupWindowMs:\s*(\d+)", self.src)
        assert match, "_dedupWindowMs must be defined"
        assert int(match.group(1)) > 0

    def test_dedup_map_pruning(self) -> None:
        """Dedup map must be pruned to prevent memory leaks."""
        assert "_recentMap.size" in self.src
        assert "_recentMap.delete" in self.src

    def test_toast_persists_to_session_storage(self) -> None:
        """Toasts must be persisted via sessionStorage to survive page navigation."""
        assert "sessionStorage" in self.src
        assert "_enqueueFlash" in self.src

    def test_expired_toasts_discarded_on_restore(self) -> None:
        """Restoring toasts after navigation must discard genuinely stale ones.

        A toast still on screen at navigation is intentionally given a minimum
        visible window on the destination page (so short sync confirmations are
        not swallowed by page-load time); only toasts older than their natural
        duration plus a stale grace window are dropped.
        """
        assert "elapsed > dur + STALE_MS" in self.src or "remaining <= 0" in self.src


class TestApiCallResilience:
    """Verify apiCall retry and error handling in core.js."""

    @pytest.fixture(autouse=True)
    def _load_source(self) -> None:
        self.src = _read_js("core.js")

    def test_retry_uses_exponential_backoff(self) -> None:
        """Retry delay must use exponential backoff with jitter."""
        assert "Math.pow(2, attempt)" in self.src or "Math.pow(2," in self.src

    def test_jitter_added_to_retry(self) -> None:
        assert "Math.random()" in self.src

    def test_max_retries_capped(self) -> None:
        """maxRetries must be capped to prevent infinite retry storms."""
        assert "_clamp(opts.maxRetries, 0, 5)" in self.src

    def test_abort_timeout_cleanup(self) -> None:
        """Abort controller timeout must be cleaned up to avoid leaks."""
        assert "timeoutInfo.cleanup()" in self.src

    def test_network_error_user_friendly_message(self) -> None:
        """Network errors must get a user-friendly message instead of raw TypeError."""
        assert "Network error" in self.src

    def test_session_expired_detection(self) -> None:
        """Redirect to /dashboard/login must be detected as session expiry."""
        assert "/dashboard/login" in self.src
        assert "Session expired" in self.src

    def test_lazy_error_retry_uses_declarative_reload_action(self) -> None:
        """Lazy-load retry buttons must avoid inline onclick handlers."""
        assert "_handleDeclarativeReload" in self.src
        assert 'data-action="reload-keep-scroll"' in self.src
        assert 'onclick="reloadKeepScroll()"' not in self.src

    def test_the_mutation_throttle_is_part_of_apicall(self) -> None:
        """One apiCall: the throttle is not a second definition patched over it."""
        assert "const _inflightMutations = new Set();" in self.src
        assert self.src.count("GP.apiCall = ") == 1
        assert self.src.count("window.apiCall = ") == 1


class TestDeclarativeClientActions:
    """Guard CSP-friendly client markup generated from JavaScript sources."""

    def test_source_js_does_not_emit_inline_onclick_handlers(self) -> None:
        offenders: list[str] = []
        paths = [*_STATIC_JS.rglob("*.js"), _TEMPLATES / "static" / "sw.js"]
        for path in paths:
            src = path.read_text(encoding="utf-8")
            if "onclick=" in src:
                offenders.append(str(path.relative_to(_TEMPLATES.parents[2])))

        assert offenders == []

    def test_native_select_component_has_no_inline_change_handler_escape_hatch(self) -> None:
        src = _read_template("components/forms.html")

        assert "onchange=" not in src
        assert "onchange=''" not in src

    def test_course_tabs_keyboard_navigation_is_external_module(self) -> None:
        template = _read_template("partials/course/_course_nav.html")
        js = _read_js("course-tabs.js")

        assert "<script" not in template
        assert "initCourseTabs" in js
        assert "addEventListener('keydown'" in js

    def test_legacy_process_status_inline_component_is_removed(self) -> None:
        """Import flow must use external JS, not dead inline-JS macros."""
        process_status = _TEMPLATES / "components" / "process_status.html"
        dashboard = _read_template("partials/dashboard/_content.html")
        course_detail = _read_template("partials/course/_detail_content.html")
        import_helpers = _read_template("components/import_helpers.html")

        assert not process_status.exists()
        assert "components/process_status.html" not in dashboard
        assert "components/process_status.html" not in course_detail
        assert "static/js/import-stream.js" in import_helpers

    def test_process_action_guard_refresh_includes_root_element(self) -> None:
        src = _read_js("process-action-guards.js")

        assert "root.matches?.('[data-process-lock-when]')" in src
        assert "candidates.unshift(root)" in src

    def test_process_action_guard_refreshes_on_job_updates(self) -> None:
        src = _read_js("process-action-guards.js")

        assert "function scheduleGuardRefresh()" in src
        assert "window.addEventListener('gp:job-update', scheduleGuardRefresh)" in src
        assert "window.addEventListener('gp:job-complete', scheduleGuardRefresh)" in src

    def test_course_delete_group_action_uses_clicked_button_context(self) -> None:
        src = (_STATIC_JS / "_parts" / "course-detail" / "10-teams-crud.js").read_text(
            encoding="utf-8"
        )
        template = _read_template("partials/course/_detail_content.html")

        assert "_jsonAttr([teamId, teamName, '$event'])" in src
        assert "[team.id|string, team.name, '$event']|tojson_attr" in template
        assert "closest?.('button[data-action=\"deleteTeam\"]')" in src
        assert 'data-action-args*="${teamId}"' not in src

    def test_scoring_toggle_buttons_have_declarative_process_locks(self) -> None:
        templates = (
            _read_template("partials/team/_detail_content.html"),
            _read_template("partials/project/_members_table.html"),
        )

        for src in templates:
            assert 'data-action="toggleExclusion"' in src
            assert 'data-process-lock-when="sync run_checks"' in src

    def test_declarative_actions_do_not_eval_inline_expressions(self) -> None:
        js = _read_js("core.js")
        templates = "\n".join(
            path.read_text(encoding="utf-8") for path in sorted(_TEMPLATES.rglob("*.html"))
        )

        assert "new Function" not in js
        assert "_runDataExpression" not in js
        for marker in (
            "data-action-expr",
            "data-submit-expr",
            "data-change-expr",
            "data-keyup-expr",
        ):
            assert marker not in js
            assert marker not in templates

    def test_reload_toasts_use_shared_action_contract(self) -> None:
        src = _read_js("pages/project-detail.js") + _read_js("pages/course-detail.js")

        assert "GP.errorStateHtml(" in src
        assert "GP.bindRetry(infoCard, _pollSyncStatusOnce)" in src
        assert 'reloadKeepScroll()" class="toast-link' not in src
        assert 'onclick="reloadKeepScroll()' not in src

    def test_support_ticket_hint_uses_css_class_not_inline_margin(self) -> None:
        # The markup lives in ONE place now: support_ticket_detail.html used to
        # be a 311-line copy of this partial and has been reduced to the page
        # shell that includes it, so asserting against both read the same file
        # twice - and the copy was the one that had drifted.
        src = _read_template("partials/support/_ticket_detail_content.html")
        css = _read_css("pages/support.css")

        assert "gh-md-hint gh-md-hint--standalone" in src
        assert 'gh-md-hint" style=' not in src
        assert ".gh-md-hint--standalone" in css
        shell = _read_template("support_ticket_detail.html")
        assert '{% include "partials/support/_ticket_detail_content.html" %}' in shell

    def test_login_service_worker_registration_is_external(self) -> None:
        template = _read_template("login.html")
        js = _read_js("pages/login.js")

        assert "serviceWorker.register" not in template
        assert "navigator.serviceWorker.register('/sw.js'" in js

    def test_service_worker_never_caches_dashboard_html(self) -> None:
        src = (_TEMPLATES / "static" / "sw.js").read_text(encoding="utf-8")

        assert "url.pathname === '/dashboard' || url.pathname.startsWith('/dashboard/')" in src
        assert "return !/(^|,\\s*)(no-store|private)" in src
        assert "isCacheableResponse(response)" in src

    def test_global_job_bar_delegates_job_endpoint_sse_fallback(self) -> None:
        src = "\n".join(
            (_STATIC_JS / "_parts" / "global-job-bar" / name).read_text(encoding="utf-8")
            for name in ("00-state-polling.js", "10-sse-render.js", "20-listeners-api.js")
        )
        job_endpoint_branch = re.search(
            r"if \(jobIdMatch && typeof window\.streamJobProgress === 'function'\).*?"
            r"\n  // -- Non-job URL",
            src,
            re.DOTALL,
        )
        assert job_endpoint_branch, "global job bar must have the streamJobProgress branch"
        error_handler = job_endpoint_branch.group().split("onError() {", 1)[1].split("},", 1)[0]
        assert "_startLegacyGenericPoll" not in error_handler
        assert (
            "if (!_completeStatusJob(jobType, data, onDone, onFailed))"
            in job_endpoint_branch.group()
        )

    def test_error_page_actions_are_external(self) -> None:
        template = _read_template("errors/error.html")
        js = _read_js("error-actions.js")

        assert "js/error-actions.js" in template
        assert "document.addEventListener('click'" not in template
        assert "historyBack" in js
        assert "reloadPage" in js

    def test_error_page_timers_are_external(self) -> None:
        # One template for every status; 401 and 429 are branches of it.
        unauthorized = rate_limited = _read_template("errors/error.html")
        js = _read_js("error-actions.js")
        css = _read_css("error.css")

        assert "setTimeout(" not in unauthorized
        assert "setInterval(" not in rate_limited
        assert "data-redirect-after-seconds" in unauthorized
        assert "data-countdown-seconds" in rate_limited
        assert "_initTimedRedirect" in js
        assert "_initCountdownReload" in js
        assert ".error-note" in css

    def test_color_mode_bootstraps_before_styles(self) -> None:
        controller = _read_js("theme-bootstrap.js")
        tokens = _read_css("tokens.css")
        theme = _read_css("theme.css")

        for name in ("base.html", "login.html", "errors/error.html"):
            template = _read_template(name)
            assert template.index("js/theme-bootstrap.js") < template.index(".css")
            assert 'content="light dark"' in template

        assert "gitpulse-color-mode" in controller
        assert '"light", "dark", "system"' in controller
        assert 'data-theme-persist-url="/dashboard/api/theme"' in _read_template("base.html")
        assert "persistOnServer" in controller
        assert 'html[data-theme="light"]' in tokens
        assert "[data-theme-value]" in controller
        assert ".theme-switcher-button" in theme

    def test_pwa_install_state_is_verified_against_browser_installations(self) -> None:
        controller = _read_js("pwa-install.js")
        manifest = (_TEMPLATES / "static" / "site.webmanifest").read_text(encoding="utf-8")

        assert "navigator.getInstalledRelatedApps" in controller
        assert "_clearInstalledMarker" in controller
        assert '"platform": "webapp"' in manifest

    def test_pwa_install_does_not_unconditionally_suppress_native_banner(self) -> None:
        controller = _read_js("pwa-install.js")
        before_prompt = controller.index("window.addEventListener('beforeinstallprompt'")
        installed = controller.index("window.addEventListener('appinstalled'", before_prompt)
        handler = controller[before_prompt:installed]

        assert "_customPromptEnabled" in controller
        assert "preventDefault" not in handler
        assert "deferredPrompt = ev" in handler

    def test_header_uses_shared_role_badge_contract(self) -> None:
        header = _read_template("components/header.html")

        assert "import role_badge" in header
        assert "{{ role_badge(user_role or 'user') }}" in header
        assert "variant='danger' if is_admin" not in header

    def test_home_and_top_bar_avatars_are_the_shared_avatar(self) -> None:
        """Both drew their own disc, ring and overlay; they are GlAvatar now,
        at the sizes GitLab's home greeting and user menu use."""
        dashboard = _read_template("dashboard.html")
        header = _read_template("components/header.html")

        assert (
            "{{ avatar(avatar_url, full_name or username|default('?', true), size=64," in dashboard
        )
        assert "{{ avatar(avatar_url, full_name or username|default('?', true), size=32," in header
        for css in ("home.css", "topbar.css"):
            src = _read_css(css)
            assert ".gl-home-avatar" not in src
            assert ".gl-top-bar-avatar {" not in src

    def test_modal_opening_does_not_defer_scrollbar_until_after_animation(self) -> None:
        modal_js = (_STATIC_JS / "_parts" / "core" / "10-modals.js").read_text(encoding="utf-8")
        modal_css = _read_css("modals.css")

        assert "function _resetModalScroll" in modal_js
        assert "_resetModalScroll(modal);" in modal_js
        assert ".modal-backdrop.modal-animating .modal-body" not in modal_css
        assert "overscroll-behavior: contain;" in modal_css

    def test_loading_icons_have_one_shared_dom_contract(self) -> None:
        template = _read_template("components/loaders.html")
        button_template = _read_template("components/buttons.html")
        button_css = _read_css("buttons.css")
        global_jobs = _read_js("global-job-bar.js")

        # No button may grow a loading mark of its own: the loading state inserts
        # the SAME `gp-spinner` (tanuki in its turning ring) that every other
        # loading state in the app uses, sized to the icon box it replaces.
        assert "btn-spinner" not in button_template
        assert ".btn-spinner" not in button_css
        assert "{{ spinner(size='xs') }}" in button_template
        assert ".btn > .gp-spinner" in button_css
        # The old blanking treatment must not come back.
        button_rules = _code_only(button_css)
        assert "color: transparent !important" not in button_rules
        assert ".btn.btn-loading-text" not in button_rules

        # ONE loading mark for the whole app: the brand tanuki inside the same
        # turning ring the full-page navigation loader uses, at one of four
        # sizes. A table waiting for rows and a page waiting to arrive are the
        # same event and now look like it, instead of a plain arc here and a
        # tanuki there.
        # It lives in its own dependency-free template so BOTH loaders.html and
        # buttons.html can use it (loaders.html imports buttons.html, so the
        # reverse import would be a Jinja cycle).
        template = _read_template("components/spinner.html")
        assert '{% from "components/spinner.html" import spinner %}' in _read_template(
            "components/loaders.html"
        )
        assert "gp-spinner-mark" in template, "the shared macro renders the mark"
        assert "gl-loading-icon" not in template, "the bare arc must stay gone"
        assert "global-job-spinner gp-spinner gp-spinner--sm" in global_jobs
        assert "GP.tanukiMarkHtml()" in global_jobs

        logo_css = _read_css("logo.css")
        assert ".gp-spinner::before" in logo_css, "the ring is one rule"
        # Flat fills, no gradient <defs>: several spinners can be on a page at
        # once, and duplicate ids resolve to whichever rendered first - the rest
        # would borrow another spinner's colours.
        assert "linearGradient" not in template.split("macro spinner(")[1].split("endmacro")[0]

    def test_offline_fallback_is_a_shared_static_surface(self) -> None:
        sw = (_TEMPLATES / "static" / "sw.js").read_text(encoding="utf-8")
        offline = (_TEMPLATES / "static" / "offline.html").read_text(encoding="utf-8")

        assert "caches.match('/static/offline.html')" in sw
        assert "<style>" not in sw
        assert "css/error.css" in offline
        assert "js/theme-bootstrap.js" in offline

    def test_course_settings_llm_helpers_are_external(self) -> None:
        template = _read_template("course_settings.html")
        js = _read_js("pages/course-settings.js")

        assert "window.llmResourceUrls" not in template
        assert "document.addEventListener('DOMContentLoaded'" not in template
        assert "llmResourceUrls" in js
        assert "initLlmPromptPresets" in js

    def test_admin_courses_controller_uses_srp_parts(self) -> None:
        parts_dir = _STATIC_JS / "_parts" / "admin-courses"
        expected_parts = ["00-core.js", "10-lifecycle.js", "20-events.js"]

        for name in expected_parts:
            assert (parts_dir / name).exists(), f"Missing admin-courses source part: {name}"

        js = _read_js("pages/admin-courses.js")
        assert "function renderLifecycleButton" in js
        assert "status-indicator--" in js
        assert '<svg width="8"' not in js


class TestDocsSiteHtmlContracts:
    """Guard the docs site's serving contracts.

    The Material template overrides these used to cover are gone: the docs are
    built by Astro Starlight now, which has no `overrides/partials`. What still
    matters, and is still asserted, is how nginx serves the result.
    """

    _DOCS_SITE = Path(__file__).resolve().parent.parent.parent / "docs-site"

    @staticmethod
    def _nginx_location_block(config: str, selector: str) -> str:
        pattern = rf"location {re.escape(selector)} \{{(?P<body>.*?)\n    \}}"
        match = re.search(pattern, config, re.DOTALL)
        assert match, f"Missing Nginx location block: {selector}"
        return match.group("body")

    def test_nginx_404_page_is_not_cacheable_or_indexable(self) -> None:
        config = (self._DOCS_SITE / "nginx" / "default.conf").read_text(encoding="utf-8")
        block = self._nginx_location_block(config, "= /404.html")
        no_store_header = 'add_header Cache-Control "no-store, no-cache, must-revalidate" always;'
        robots_header = 'add_header X-Robots-Tag "noindex, nofollow, nosnippet" always;'

        assert no_store_header in block
        assert robots_header in block

    def test_nginx_health_check_is_exact_plain_text_endpoint(self) -> None:
        config = (self._DOCS_SITE / "nginx" / "default.conf").read_text(encoding="utf-8")
        block = self._nginx_location_block(config, "= /health")

        assert "location /health" not in config
        assert "default_type text/plain;" in block
        assert 'return 200 "OK\\n";' in block

    def test_nginx_html_cache_headers_apply_to_error_responses(self) -> None:
        config = (self._DOCS_SITE / "nginx" / "default.conf").read_text(encoding="utf-8")
        no_store_header = 'add_header Cache-Control "no-store, no-cache, must-revalidate" always;'

        for selector in ("~* \\.html$", "= /", "/"):
            block = self._nginx_location_block(config, selector)
            assert no_store_header in block


class TestTeamMembersTableContracts:
    """Guard team member table badge rendering and overflow contracts."""

    def test_role_badge_mapping_lives_in_member_component(self) -> None:
        """Member role badges render through ONE component (members.html
        member_role_badges, composed by member_name_cell) - never an inlined
        role ladder in the page template. (The old dedicated Role-column macro
        member_access_role_badge was deleted as dead code after the redesign
        dropped the standalone Role column.)"""
        template = _read_template("partials/team/_detail_content.html")
        members = _read_template("components/members.html")

        assert "macro member_role_badges" in members
        assert "macro member_name_cell" in members
        assert "member_name_cell(" in template
        assert "member_access_role_badge" not in template  # stays deleted
        assert "gl_role == 'maintainer'" not in template  # no inlined ladder

    def test_badge_only_cells_do_not_render_ellipsis_markers(self) -> None:
        template = _read_template("partials/team/_detail_content.html")
        css = _read_css("pages/course.css")
        block = re.search(
            r"\.team-members-table td\.member-badge-cell,\n"
            r"\.project-members-table td\.member-badge-cell\s*\{(?P<body>.*?)\n\}",
            css,
            re.DOTALL,
        )

        assert template.count('class="text-nowrap member-badge-cell"') == 0
        assert template.count('class="text-center member-badge-cell"') == 1
        assert block, "Missing badge-only team member cell contract"
        # No member-table cell clips to an ellipsis any more: the columns size to
        # their content, so there is no marker for a badge cell to switch off.
        members = css.split("MEMBER TABLES", 1)[1].split("PROJECTS TABLE", 1)[0]
        assert "text-overflow: ellipsis" not in members


class TestLoginGitLabAlert:
    """Verify the login page uses the reusable GitLab-style alert contract."""

    def test_login_template_uses_shared_alert_component(self) -> None:
        src = _read_template("login.html")

        assert "{{ alert(error" in src
        assert "login-alert-region" in src
        assert "login-error-alert" not in src

    def test_alert_macro_exposes_dismissible_gitlab_alert(self) -> None:
        src = _read_template("components/alerts.html")

        assert "{% macro alert(" in src
        assert "macro gitlab_alert" not in src, "two alert components again"
        assert "gitlab-alert gitlab-alert-{{ variant }}" in src
        assert "close_button(t('Dismiss'), class='gitlab-alert-close'" in src
        assert "data_attrs={'remove-closest': '.gitlab-alert'}" in src
        assert "gitlab-alert-message" in src

    def test_alert_css_matches_gitlab_error_banner_shape(self) -> None:
        """The shared alert must carry @gitlab/ui's GlAlert shape.

        This used to pin `border-top: 2px solid` and
        `--gl-feedback-strong-{bg,text}`. Both were wrong against the real
        design system: @gitlab/ui ships every --gl-alert-*-border-* colour as
        rgba(0, 0, 0, 0), and documents feedback-strong as the background for
        "a tooltip or toast message" - not an alert. Detail lives in
        tests/unit/test_gitlab_alert_parity.py.
        """
        src = _read_css("alerts.css")

        assert ".gitlab-alert" in src
        assert ".gitlab-alert-message" in src
        assert ".gitlab-alert-close" in src
        # gl-py-5 block / calc(spacing-9) inline, and the alert radius token.
        assert "var(--gl-spacing-5) var(--gl-spacing-9)" in src
        assert "var(--gl-alert-border-radius)" in src
        # The toast's background must not come back to the alert. Checked as a
        # declaration, not a bare substring - the rule above explains the token
        # by name in a comment.
        assert "background: var(--gl-feedback-strong-bg" not in src
        assert "color: var(--gl-feedback-strong-text)" not in src

    def test_login_runtime_errors_reuse_alert_contract(self) -> None:
        """The browser-side error is the server's component, cloned - not a
        hand-built copy with its own icons and close button."""
        src = _read_js("pages/login.js")
        page = _read_template("login.html")

        assert (
            "getElementById('loginErrorTemplate').content.firstElementChild.cloneNode(true)" in src
        )
        assert "gitlab-alert-message" in src
        assert "createElementNS" not in src
        assert "login-error-alert" not in src
        assert '<template id="loginErrorTemplate">' in page
        assert "{{ alert('', variant='danger', dismissible=true, class='login-auth-alert'" in page

    def test_obsolete_login_error_css_removed(self) -> None:
        src = _read_css("login.css") + _read_css("utilities.css")

        assert ".login-error-alert" not in src
        assert "#f09" not in src


# ===================================================
# components.js - PollingController
# ===================================================


class TestPollingController:
    """Verify PollingController in components.js."""

    @pytest.fixture(autouse=True)
    def _load_source(self) -> None:
        self.src = _read_js("components.js")

    def test_polling_controller_class_exists(self) -> None:
        assert "class PollingController" in self.src

    def test_start_guard_prevents_double_start(self) -> None:
        """Starting while already running must be a no-op."""
        assert "if (!this._stopped)" in self.src

    def test_stop_clears_timer(self) -> None:
        """stop() must clear the pending timer."""
        stop_block = re.search(
            r"stop\(\)\s*\{.*?\}",
            self.src,
            re.DOTALL,
        )
        assert stop_block
        assert "clearTimeout" in stop_block.group()

    def test_error_count_tracked(self) -> None:
        assert "_errorCount" in self.src

    def test_pause_when_hidden(self) -> None:
        """Polling must pause when the tab is hidden."""
        assert "document.hidden" in self.src
        assert "_pauseWhenHidden" in self.src

    def test_in_flight_guard(self) -> None:
        """Concurrent ticks must be prevented by an in-flight guard."""
        assert "_inFlight" in self.src


# ===================================================
# Cross-cutting: bundle consistency
# ===================================================


class TestBundleConsistency:
    """Verify that the bundle includes all source modules."""

    def test_bundle_contains_all_modules(self) -> None:
        """core.bundle.js must contain content from all individual modules."""
        bundle = served("js/core.bundle.js").read_text(encoding="utf-8")

        # Key signatures from each module
        signatures = {
            "health-monitor.js": "initHealthMonitor",
            "sse-stream.js": "streamJobProgress",
            "core.js": "_checkVersionHeader",
            "components.js": "PollingController",
            "course-tabs.js": "initCourseTabs",
            "global-job-bar.js": "_beginCourseSyncSse",
        }

        for module, sig in signatures.items():
            assert sig in bundle, f"Bundle missing content from {module} (signature: {sig})"

    def test_bundle_is_not_empty(self) -> None:
        bundle = served("js/core.bundle.js").read_text(encoding="utf-8")
        assert len(bundle) > 10000, "Bundle seems too small, likely incomplete"

    def test_bundle_auto_generated_header(self) -> None:
        bundle = served("js/core.bundle.js").read_text(encoding="utf-8")
        assert "AUTO-GENERATED" in bundle


# ===================================================
# Health endpoint Python schemas & logic
# ===================================================


class TestHealthEndpointVersionHeader:
    """Verify that the health endpoint provides X-App-Version for client detection."""

    def test_health_response_includes_version_field(self) -> None:
        from app.schemas.health import HealthResponse

        fields = HealthResponse.model_fields
        assert "version" in fields, "HealthResponse must include 'version' for mismatch detection"

    def test_health_response_status_values(self) -> None:
        """HealthResponse status must support ok/degraded/down to match JS state machine."""
        from app.schemas.health import OverallStatus

        assert hasattr(OverallStatus, "OK")
        assert hasattr(OverallStatus, "DEGRADED")
        assert hasattr(OverallStatus, "DOWN")

    def test_overall_status_resolution_all_ok(self) -> None:
        """When all components are OK, overall status must be OK."""
        from app.schemas.health import ComponentHealth

        components = {
            "database": ComponentHealth(status="ok", latency_ms=1.0),
            "redis": ComponentHealth(status="ok", latency_ms=0.5),
        }
        statuses = [c.status for c in components.values()]
        all_ok = all(s == "ok" for s in statuses)
        assert all_ok, "All-ok components should resolve to ok"

    def test_overall_status_resolution_one_error(self) -> None:
        """When one component is error, status can't be ok."""
        from app.schemas.health import ComponentHealth

        components = {
            "database": ComponentHealth(status="ok", latency_ms=1.0),
            "redis": ComponentHealth(status="error", error="Connection refused"),
        }
        statuses = [c.status for c in components.values()]
        has_error = any(s == "error" for s in statuses)
        all_ok = all(s == "ok" for s in statuses)
        assert has_error, "Mixed statuses must have an error"
        assert not all_ok, "Mixed statuses must not resolve to ok"

    def test_overall_status_resolution_all_error(self) -> None:
        """When all components are error, overall must be down."""
        from app.schemas.health import ComponentHealth

        components = {
            "database": ComponentHealth(status="error", error="Timeout"),
            "redis": ComponentHealth(status="error", error="Timeout"),
        }
        statuses = [c.status for c in components.values()]
        all_error = all(s == "error" for s in statuses)
        assert all_error, "All-error must resolve to down"


class TestStudentPipelineCoverageUi:
    """Pipeline coverage is integrated directly into the test stage badge."""

    def test_coverage_renders_integrated_with_test_badges(self) -> None:
        student_template = (_TEMPLATES / "components" / "student.html").read_text(encoding="utf-8")
        student_css = (_STATIC_CSS / "pages" / "student.css").read_text(encoding="utf-8")

        assert "pipeline.has_test_job" in student_template
        assert "pipeline-test-badges" in student_template
        assert "mr-pipeline-coverage" not in student_template
        assert ".mr-pipeline-coverage" not in student_css


class TestStudentDiffCommentsUi:
    """Diff comments and changed-file jumps must stay scoped to their owning card."""

    def test_diff_file_ids_are_scoped_per_mr_or_review_card(self) -> None:
        students_api = (_DASHBOARD_API / "students" / "profile.py").read_text(encoding="utf-8")
        student_diffs = (_DASHBOARD_API / "students" / "diffs.py").read_text(encoding="utf-8")
        student_template = (_TEMPLATES / "components" / "student.html").read_text(encoding="utf-8")
        student_js = _read_js("pages/student-detail.js")

        assert "def _scope_diff_views" in student_diffs
        assert 'view["anchor"] = f"{scope_id}-diff-file-' in student_diffs
        assert '"diff_anchor": diff.get("anchor")' in student_diffs
        assert '_scope_diff_views(views[mr_id], f"{scope}-{mr_id}")' in students_api
        assert '_diff_views(db, mr_ids, "mr")' in students_api
        assert '_diff_views(db, list(by_mr), "review")' in students_api

        assert "id=\"{{ diff.anchor or ('diff-file-' ~ diff.idx) }}\"" in student_template
        assert "'diff-target': f.anchor or ('diff-file-' ~ f.idx)" in student_template
        assert "diff-summary-files" not in student_template

        assert "_queryScopedId(layout, this.dataset.diffTarget)" in student_js
        assert "this.closest('[data-mr-card], .rg-card')" in student_js
        assert "manualDiffScrollUntil" in student_js
        assert "document.getElementById(this.dataset.diffTarget)" not in student_js
        assert "document.getElementById(targetId)" not in student_js
        assert ".scrollIntoView(" not in student_js

    def test_inline_code_context_uses_double_line_gutter(self) -> None:
        student_template = (_TEMPLATES / "components" / "student.html").read_text(encoding="utf-8")

        assert "dn-code-ln--old" in student_template
        assert "dn-code-ln--new" in student_template
        assert "Comment on lines" in student_template
        assert "Comment on line" in student_template
        assert "cc.line_start" in student_template
        assert "cc.line_end" in student_template


class TestStudentDiagnosticsUi:
    """Diagnostics should not duplicate unreliable or pipeline-owned metrics."""

    def test_response_rate_and_test_coverage_stat_cards_are_removed(self) -> None:
        diagnostics = (_TEMPLATES / "partials" / "student" / "_diagnostics.html").read_text(
            encoding="utf-8"
        )
        loaders = (_TEMPLATES / "components" / "loaders.html").read_text(encoding="utf-8")

        assert "Response Rate" not in diagnostics
        assert "snapshot.response_rate" not in diagnostics
        assert "t('Test Coverage')" not in diagnostics
        assert "mrs_with_test_changes" not in diagnostics
        assert "sk_stat(label=t('Response Rate')" not in loaders
        assert "sk_stat(label=t('Test Coverage')" not in loaders


class TestLocalPageScrollContract:
    """In-app jumps must scroll .gl-page-content, not the browser viewport."""

    def test_core_anchor_hash_scroll_uses_local_page_content_scroller(self) -> None:
        core = (_STATIC_JS / "_parts" / "core" / "32-page-scroll.js").read_text(encoding="utf-8")

        assert "function scrollWithinPageContent" in core
        assert "GP.scrollWithinPageContent = scrollWithinPageContent" in core
        assert "_targetFromHash(href)" in core
        assert "scrollWithinPageContent(target, { block: 'start' })" in core
        assert "target.scrollIntoView({ behavior: 'smooth', block: 'start' })" not in core

    def test_page_jump_callers_reuse_shared_local_scroller(self) -> None:
        dashboard = (_STATIC_JS / "_parts" / "dashboard" / "00-core.js").read_text(encoding="utf-8")
        project = (_STATIC_JS / "_parts" / "project-detail" / "30-live-intel.js").read_text(
            encoding="utf-8"
        )
        student = _read_js("pages/student-detail.js")
        components = _read_js("components.js")

        assert "GP.scrollWithinPageContent(targetEl, { block: 'start' })" in dashboard
        assert "GP.scrollWithinPageContent(row, { block: 'center' })" in project
        assert "GP.scrollWithinPageContent(el, { block: 'nearest', offset: 24 })" in project
        assert "GP.scrollWithinPageContent(target, { block: 'center' })" in student
        assert "GP.scrollWithinPageContent?.(this.tbody, { block: 'start' })" in components

        for source in (dashboard, project, student, components):
            assert ".scrollIntoView(" not in source
            assert "document.scrollingElement" not in source

    def test_search_palette_focus_scrolls_its_own_result_container(self) -> None:
        palette = _read_js("search-palette.js")

        assert "function scrollResultIntoBody(item)" in palette
        assert "item.focus({ preventScroll: true });\n    scrollResultIntoBody(item);" in palette
        assert ".scrollIntoView" not in palette


class TestPageScriptGlobalScopeSafety:
    """Standalone page scripts must not redeclare `GP` at top level.

    ``core.bundle.js`` (via ``_parts/core/00-namespace.js``) declares a GLOBAL
    ``GP`` in the shared classic-script scope. Any
    page script that ALSO does ``const GP = ...`` at column 0 throws
    ``SyntaxError: Identifier 'GP' has already been declared`` at parse time,
    which aborts the ENTIRE file - so its Alpine component factory never
    registers and the page renders as a dead shell (this took down the course
    Teachers page). Every page script must be wrapped in an IIFE so its ``GP``
    binding is function-scoped.
    """

    def test_no_page_script_redeclares_gp_at_top_level(self) -> None:
        pages_dir = _STATIC_JS / "pages"
        offenders: list[str] = []
        for path in sorted(pages_dir.glob("*.js")):
            src = path.read_text(encoding="utf-8")
            # Column-0 `const GP` / `let GP` = top-level (not inside an IIFE).
            if re.search(r"^(?:const|let)\s+GP\b", src, re.MULTILINE):
                offenders.append(path.name)
        assert not offenders, (
            "Page script(s) declare `GP` at global scope and will collide with "
            "core.bundle.js's global `const GP` (SyntaxError -> dead page). Wrap "
            f"them in an IIFE: {offenders}"
        )
