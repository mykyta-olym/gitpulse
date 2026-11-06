"""Transport failures and page-size changes stay within their intended scope."""

from __future__ import annotations

import json
import os

import pytest

pytestmark = pytest.mark.e2e

if not os.getenv("GITPULSE_E2E_BASE_URL"):
    pytest.skip("request contracts need a running server", allow_module_level=True)


@pytest.fixture
def request_page(browser, context_for, live_server: str):
    # Fault injection must reach the request, rather than the service worker.
    with browser.new_context(
        storage_state=context_for("admin").storage_state(), service_workers="block"
    ) as ctx:
        page = ctx.new_page()
        page.bring_to_front()
        page.goto(live_server + "/dashboard/")
        page.wait_for_function("() => !!window.GP?.apiCall")
        yield page


@pytest.mark.parametrize(
    "status", [400, 401, 403, 404, 409, 422, 408, 425, 429, 500, 502, 503, 504]
)
def test_http_retries_obey_the_status_policy(request_page, status: int) -> None:
    page = request_page
    calls = []

    def respond(route) -> None:
        calls.append(route.request.method)
        route.fulfill(
            status=status,
            content_type="application/json",
            body=json.dumps({"detail": "Contract response"}),
        )

    page.route("**/__request_contract__", respond)
    result = page.evaluate("""async () => {
      try {
        await GP.apiCall('/__request_contract__', 'GET', null,
          {maxRetries: 2, retryDelayMs: 50});
        return {ok: true};
      } catch (error) { return {status: error.status, message: error.message}; }
    }""")
    assert calls == ["GET"] * (1 if status in (400, 401, 403, 404, 409, 422) else 3)
    assert result == {"status": status, "message": "Contract response"}


@pytest.mark.parametrize(
    ("method", "failure", "allow_unsafe", "attempts", "success"),
    [
        ("GET", "network", False, 2, True),
        ("POST", "network", False, 1, False),
        ("POST", "network", True, 2, True),
        ("POST", "503", False, 1, False),
        ("POST", "503", True, 2, True),
        ("POST", "403", True, 1, False),
    ],
)
def test_network_recovery_keeps_mutation_retries_explicit(
    request_page, method: str, failure: str, allow_unsafe: bool, attempts: int, success: bool
) -> None:
    page = request_page
    calls = []

    def respond(route) -> None:
        calls.append(route.request.method)
        if len(calls) == 1:
            if failure == "network":
                route.abort("failed")
                return
            route.fulfill(
                status=int(failure), content_type="application/json", body='{"detail":"Refused"}'
            )
            return
        route.fulfill(content_type="application/json", body='{"ok":true}')

    page.route("**/__request_contract__", respond)
    result = page.evaluate(
        """async cfg => {
          try {
            const data = await GP.apiCall('/__request_contract__', cfg.method, {},
              {maxRetries: 2, retryDelayMs: 50, allowRetryUnsafe: cfg.allow_unsafe});
            return data.ok;
          } catch (_) { return false; }
        }""",
        {"method": method, "allow_unsafe": allow_unsafe},
    )
    assert len(calls) == attempts
    assert result is success


@pytest.mark.parametrize(
    "mode", ["default", "explicit-message", "custom-error", "custom-type-error"]
)
def test_cancellation_keeps_a_readable_message_without_retrying(request_page, mode: str) -> None:
    page = request_page
    calls = []
    page.route("**/__request_contract__", lambda route: (calls.append(1), route.abort("failed")))
    result = page.evaluate(
        """async mode => {
          const originalFetch = window.fetch;
          let attempts = 0;
          window.fetch = (...args) => {
            if (String(args[0]).includes('__request_contract__')) attempts++;
            return originalFetch(...args);
          };
          const ctl = new AbortController();
          if (mode === 'custom-error') ctl.abort(new Error('User stopped the request'));
          else if (mode === 'custom-type-error') {
            ctl.abort(new TypeError('User stopped the request'));
          }
          else ctl.abort();
          try {
            await GP.apiCall('/__request_contract__', 'GET', null,
              {signal: ctl.signal, maxRetries: 2, retryDelayMs: 50,
               abortMessage: mode === 'explicit-message' ? 'Stopped explicitly' : ''});
            return {ok: true};
          } catch (e) { return {name: e.name, message: e.message, attempts}; }
          finally { window.fetch = originalFetch; }
        }""",
        mode,
    )
    expected = (
        "Stopped explicitly"
        if mode == "explicit-message"
        else "User stopped the request"
        if mode.startswith("custom-")
        else page.evaluate("() => GP.t('Request cancelled.')")
    )
    assert result == {"name": "AbortError", "message": expected, "attempts": 1}
    assert not calls


@pytest.mark.parametrize("width", [1440, 390])
def test_page_size_does_not_change_a_table_from_the_previous_page(
    browser, context_for, live_server: str, width: int
) -> None:
    with browser.new_context(
        storage_state=context_for("admin").storage_state(),
        service_workers="block",
        viewport={"width": width, "height": 844},
        has_touch=width == 390,
        is_mobile=width == 390,
    ) as ctx:
        page = ctx.new_page()
        page.bring_to_front()
        page.goto(live_server + "/dashboard/admin/system")
        page.wait_for_function("() => !!document.querySelector('#jobsTableBody')?._clientPaginator")
        page.evaluate("""() => {
          window.__previousPager = document.querySelector('#jobsTableBody')._clientPaginator;
          window.__previousSize = window.__previousPager.pageSize;
          window.__previousPreference = localStorage.getItem(
            'gp_ps_' + window.__previousPager._storageKey);
        }""")
        if width == 390:
            page.locator("#mobileMenuBtn").click()
        page.locator('a[href="/dashboard/admin/users"]').first.click()
        page.wait_for_url("**/dashboard/admin/users")
        page.wait_for_function(
            "() => !!document.querySelector('.users-table tbody')?._clientPaginator"
        )
        page.locator("#paginationControls .gl-dropdown-toggle").click()
        page.locator('[data-gl-portal] [data-size="100"]').click()
        assert page.evaluate("""() => {
          const old = window.__previousPager;
          return !old.controls.isConnected && old.pageSize === window.__previousSize
            && localStorage.getItem('gp_ps_' + old._storageKey) === window.__previousPreference;
        }""")
        assert (
            page.evaluate(
                "() => document.querySelector('.users-table tbody')._clientPaginator.pageSize"
            )
            == 100
        )
        assert page.locator("[data-gl-portal]").count() == 0

        # A passive row refresh also redraws the controls. Its old menu must
        # return from the portal before the old controls are removed.
        page.locator("#paginationControls .gl-dropdown-toggle").click()
        assert page.locator("[data-gl-portal]").count() == 1
        page.evaluate(
            "() => document.querySelector('.users-table tbody')._clientPaginator.render()"
        )
        assert page.locator("[data-gl-portal]").count() == 0
        page.locator("#paginationControls .gl-dropdown-toggle").click()
        page.locator('[data-gl-portal] [data-size="25"]').click()
        assert (
            page.evaluate(
                "() => document.querySelector('.users-table tbody')._clientPaginator.pageSize"
            )
            == 25
        )
