"""Closing and switching profiles must remain usable while reads are pending."""

from __future__ import annotations

import json
import os

import pytest

pytestmark = pytest.mark.e2e

if not os.getenv("GITPULSE_E2E_BASE_URL"):
    pytest.skip("profile request races need a running server", allow_module_level=True)


@pytest.fixture(params=[1440, 390])
def users_page(browser, context_for, live_server: str, request):
    width = request.param
    with browser.new_context(
        storage_state=context_for("admin").storage_state(),
        service_workers="block",
        viewport={"width": width, "height": 844},
        has_touch=width == 390,
        is_mobile=width == 390,
    ) as ctx:
        page = ctx.new_page()
        page.bring_to_front()
        page.goto(live_server + "/dashboard/admin/users")
        page.wait_for_function("() => !!window.openUserInfoModal && !!GP.ensureUserInfoModule")
        page.evaluate("""() => {
          const original = window.fetch;
          // Deliberately allow an aborted read to resolve: response ownership
          // must hold even when transport cancellation arrives too late.
          const reads = [];
          window.__userReads = reads;
          window.fetch = (url, options) => {
            const path = String(url);
            if (path.endsWith('/info') && path.includes('race-')) {
              return new Promise(resolve => reads.push({url: path, signal: options.signal,
                respond: () => resolve(new Response(JSON.stringify({
                  profile: {username: path.includes('first') ? 'race-first' : 'race-second'},
                  courses: [], teams: [], projects: []
                }), {headers: {'Content-Type': 'application/json'}}))}));
            }
            if (path.endsWith('/race-first/enrich')) return Promise.resolve(new Response(
              JSON.stringify({ok: true, updated_fields: ['full_name']}),
              {headers: {'Content-Type': 'application/json'}}));
            return original(url, options);
          };
        }""")
        yield page


def _configure_profile(page, kind: str) -> tuple[str, str]:
    modal = "globalUserInfoModal" if kind == "global" else "userInfoModal"
    content = "globalUserInfoContent" if kind == "global" else "userInfoContent"
    page.evaluate(
        """kind => {
          window.__openProfile = kind === 'global' ? openUserInfo : openUserInfoModal;
        }""",
        kind,
    )
    return modal, content


@pytest.mark.parametrize("kind", ["global", "admin"])
@pytest.mark.parametrize("close_first", [False, "closing", True])
def test_latest_profile_wins_even_when_the_previous_read_resolves_late(
    users_page, kind: str, close_first: bool | str
) -> None:
    page = users_page
    modal, content = _configure_profile(page, kind)
    page.evaluate("async () => { await GP.ensureUserInfoModule(); }")
    page.evaluate("() => { window.__firstProfile = __openProfile('race-first'); }")
    page.wait_for_function("() => __userReads.length === 1")
    # An actual double-click on the same person must still make only one read.
    page.evaluate("() => { __openProfile('race-first'); }")
    assert page.evaluate("() => __userReads.length") == 1
    if close_first:
        page.evaluate("id => closeModal(id)", modal)
        if close_first is True:
            page.wait_for_function(
                "id => !document.getElementById(id).classList.contains('active')", arg=modal
            )
            assert page.evaluate("() => __userReads[0].signal.aborted")
    page.evaluate("() => { window.__secondProfile = __openProfile('race-second'); }")
    page.wait_for_function("() => __userReads.length === 2")
    assert page.locator("#" + modal).is_visible()
    assert page.evaluate("() => __userReads[0].signal.aborted")
    page.evaluate("async () => { __userReads[1].respond(); await __secondProfile; }")
    assert "race-second" in page.locator("#" + content).inner_text()
    page.evaluate("async () => { __userReads[0].respond(); await __firstProfile; }")
    assert "race-second" in page.locator("#" + content).inner_text()
    assert "race-first" not in page.locator("#" + content).inner_text()


@pytest.mark.parametrize("kind", ["global", "admin"])
def test_closing_during_renderer_loading_does_not_start_an_obsolete_read(
    users_page, kind: str
) -> None:
    page = users_page
    modal, _ = _configure_profile(page, kind)
    held = []
    page.route("**/user-info-modal*.js", lambda route: held.append(route))
    page.evaluate("() => { window.__firstProfile = __openProfile('race-first'); }")
    page.wait_for_function("() => !!document.querySelector('script[src*=\"user-info-modal\"]')")
    page.wait_for_timeout(100)
    assert len(held) == 1
    page.evaluate("id => closeModal(id)", modal)
    page.wait_for_function(
        "id => !document.getElementById(id).classList.contains('active')", arg=modal
    )
    held[0].continue_()
    page.evaluate("async () => { await __firstProfile; }")
    assert page.evaluate("() => __userReads.length") == 0
    assert not page.locator("#" + modal).is_visible()


@pytest.mark.parametrize("kind", ["global", "admin"])
def test_a_renderer_timeout_is_retryable_without_reopening(users_page, kind: str) -> None:
    page = users_page
    _, content = _configure_profile(page, kind)
    held = []
    page.route("**/user-info-modal*.js", lambda route: held.append(route))
    page.clock.install()
    page.evaluate("() => { window.__firstProfile = __openProfile('race-first'); }")
    page.wait_for_function("() => !!document.querySelector('script[src*=\"user-info-modal\"]')")
    page.wait_for_timeout(100)
    assert len(held) == 1
    page.clock.fast_forward(10_100)
    page.wait_for_selector("#" + content + " .gp-retry-btn")
    assert page.locator("#" + content).get_attribute("aria-busy") is None
    page.unroute("**/user-info-modal*.js")
    page.evaluate("id => document.querySelector('#' + id + ' .gp-retry-btn').click()", content)
    page.wait_for_function("() => __userReads.length === 1")
    page.evaluate("() => __userReads[0].respond()")
    page.wait_for_selector("#" + content + " .user-info-header")
    assert page.locator("#" + content).get_attribute("aria-busy") is None


@pytest.mark.parametrize("action", ["close", "switch", "navigate"])
def test_enrichment_does_not_reopen_or_replace_a_dismissed_profile(users_page, action: str) -> None:
    page = users_page
    page.evaluate("async () => { await GP.ensureUserInfoModule(); }")
    page.evaluate("() => { window.__firstProfile = openUserInfoModal('race-first'); }")
    page.wait_for_function("() => __userReads.length === 1")
    page.evaluate("async () => { __userReads[0].respond(); await __firstProfile; }")
    page.locator("#enrichSingleUserBtn").click()
    page.wait_for_function(
        "() => document.querySelector('#enrichSingleUserBtn')?.classList.contains('btn-done')"
    )
    if action == "switch":
        page.evaluate("() => { window.__secondProfile = openUserInfoModal('race-second'); }")
        page.wait_for_function("() => __userReads.length === 2")
        page.evaluate("async () => { __userReads[1].respond(); await __secondProfile; }")
    elif action == "navigate":
        page.evaluate("() => { GP.navigateTo('/dashboard/'); }")
        page.wait_for_url("**/dashboard/")
        page.wait_for_function(
            "() => !document.getElementById('main-content').classList.contains('is-navigating')"
        )
    else:
        page.locator("#userInfoModal .modal-close").click()
    page.wait_for_timeout(1800)
    assert page.evaluate("() => __userReads.length") == (2 if action == "switch" else 1)
    if action == "switch":
        assert "race-second" in page.locator("#userInfoContent").inner_text()
    else:
        assert not page.locator("#userInfoModal").is_visible()


@pytest.mark.parametrize("navigate", [False, True])
def test_a_late_user_list_cannot_overwrite_a_newer_table(users_page, navigate: bool) -> None:
    page = users_page
    page.evaluate("""() => {
      const original = window.fetch;
      window.__tableReads = [];
      window.__tableUsername = document.querySelector(
        '.users-table tbody td strong').textContent.trim();
      window.fetch = (url, options) => {
        if (String(url).endsWith('/dashboard/admin/users/list')) {
          return new Promise(resolve => __tableReads.push(name => resolve(new Response(
            JSON.stringify({users: [{username: __tableUsername, full_name: name}]}),
            {headers: {'Content-Type': 'application/json'}}))));
        }
        return original(url, options);
      };
      document.dispatchEvent(new Event('gp-tab-visible'));
    }""")
    page.wait_for_function("() => __tableReads.length === 1")
    if navigate:
        page.evaluate("() => { GP.navigateTo('/dashboard/'); }")
        page.wait_for_url("**/dashboard/")
        page.wait_for_function(
            "() => !document.getElementById('main-content').classList.contains('is-navigating')"
        )
        page.evaluate("() => { GP.navigateTo('/dashboard/admin/users'); }")
        page.wait_for_url("**/dashboard/admin/users")
        page.wait_for_function("() => !!window.openUserInfoModal")
    page.evaluate("() => { document.dispatchEvent(new Event('gp-tab-visible')); }")
    page.wait_for_function("() => __tableReads.length === 2")
    page.evaluate("() => { __tableReads[1]('Fresh profile name'); }")
    page.wait_for_function(
        """() => document.querySelector('.users-table tbody')
          .textContent.includes('Fresh profile name')"""
    )
    page.evaluate("() => { __tableReads[0]('Stale profile name'); }")
    page.wait_for_timeout(150)
    assert "Fresh profile name" in page.locator(".users-table tbody").inner_text()
    assert "Stale profile name" not in page.locator(".users-table tbody").inner_text()


def test_refreshed_users_still_obey_the_current_search(users_page) -> None:
    page = users_page
    page.evaluate("""() => {
      const original = window.fetch;
      const username = document.querySelector('.users-table tbody td strong').textContent.trim();
      window.__listName = 'Before profile refresh';
      window.__listCalls = 0;
      window.fetch = (url, options) => {
        if (String(url).endsWith('/dashboard/admin/users/list')) {
          __listCalls++;
          return Promise.resolve(new Response(JSON.stringify({users: [
            {username, full_name: __listName}
          ]}), {headers: {'Content-Type': 'application/json'}}));
        }
        return original(url, options);
      };
      document.dispatchEvent(new Event('gp-tab-visible'));
    }""")
    page.wait_for_function("""() => document.querySelector('.users-table tbody')
      .textContent.includes('Before profile refresh')""")
    page.locator("#userSearch").fill("Before profile refresh")
    page.wait_for_function("""() => [...document.querySelectorAll(
      '.users-table tbody tr[data-search]')].filter(row => row.offsetHeight).length === 1""")
    page.wait_for_timeout(2100)
    page.evaluate("""() => {
      window.__listName = 'After profile refresh';
      document.dispatchEvent(new Event('gp-tab-visible'));
    }""")
    page.wait_for_function("() => __listCalls === 2")
    page.wait_for_function("""() => document.querySelector('.users-table tbody')
      .textContent.includes('After profile refresh')""")
    assert page.locator(".users-table tbody tr[data-search]:visible").count() == 0
    page.locator("#userSearch").fill("After profile refresh")
    page.wait_for_function("""() => [...document.querySelectorAll(
      '.users-table tbody tr[data-search]')].filter(row => row.offsetHeight).length === 1""")


def test_refreshed_role_and_status_are_used_by_the_edit_form(users_page) -> None:
    page = users_page
    row = page.locator('.users-table tr[data-bot="0"]').first
    opener = row.locator('[data-action="openEditUserModal"]')
    user_id, username, old_role, active, _ = json.loads(opener.get_attribute("data-action-args"))
    role = "teacher" if old_role != "teacher" else "student"
    page.route(
        "**/dashboard/admin/users/list",
        lambda route: route.fulfill(
            json={
                "users": [
                    {"id": user_id, "username": username, "role": role, "is_active": not active}
                ]
            }
        ),
    )
    page.evaluate("() => document.dispatchEvent(new Event('gp-tab-visible'))")
    page.wait_for_function(
        "role => document.querySelector('.users-table tr[data-bot=\"0\"]').dataset.role === role",
        arg=role,
    )
    opener.click()
    assert page.locator("#editRole").input_value() == role
    assert page.locator("#editIsActive").is_checked() is not active
    assert not page.locator("#editIsBot").is_checked()
    assert page.locator("#editUserBtn").is_disabled()
    page.wait_for_timeout(900)
    assert page.locator("#editUserBtn").is_disabled()


@pytest.mark.parametrize("bot", [False, True])
def test_saving_and_reopening_keeps_the_account_kind_and_latest_values(
    users_page, bot: bool
) -> None:
    page = users_page
    if bot:
        page.locator('.users-role-filter [data-value="bot"]').click()
    row = page.locator(f'.users-table tr[data-bot="{int(bot)}"]').first
    opener = row.locator('[data-action="openEditUserModal"]')
    user_id, _, old_role, active, _ = json.loads(opener.get_attribute("data-action-args"))
    bot_label = row.locator(".col-role .badge").inner_text()
    role = "teacher" if old_role != "teacher" else "student"
    writes = []

    def save(route):
        writes.append(route.request.post_data_json)
        route.fulfill(json={"role": role, "is_active": not active, "is_bot": bot})

    page.route("**/api/v1/users/" + user_id, save)
    opener.click()
    page.locator("#editRole_toggle").click()
    page.locator(f'#editRole_options [data-value="{role}"]').click()
    page.locator("#editIsActive").set_checked(not active)
    page.locator("#editUserBtn").click()
    page.wait_for_function(
        "() => !document.getElementById('editUserModal').classList.contains('active')"
    )
    assert writes == [{"role": role, "is_active": not active, "is_bot": bot}]
    opener.click()
    assert page.locator("#editRole").input_value() == role
    assert page.locator("#editIsActive").is_checked() is not active
    assert page.locator("#editIsBot").is_checked() is bot
    assert row.get_attribute("data-role") == role
    if bot:
        assert row.locator(".col-role .badge").inner_text() == bot_label


@pytest.mark.parametrize("field", ["role", "status"])
def test_fast_modal_edits_remain_saveable_after_the_entrance(users_page, field: str) -> None:
    page = users_page
    row = page.locator('.users-table tr[data-bot="0"]').first
    row.locator('[data-action="openEditUserModal"]').click()
    old_role = page.locator("#editRole").input_value()
    active = page.locator("#editIsActive").is_checked()
    assert page.locator("#editUserBtn").is_disabled()
    if field == "role":
        role = "teacher" if old_role != "teacher" else "student"
        page.locator("#editRole_toggle").click()
        page.locator(f'#editRole_options [data-value="{role}"]').click()
    else:
        page.locator("#editIsActive").set_checked(not active)
    page.wait_for_function("() => !document.getElementById('editUserBtn').disabled")
    # Cross both the entrance class cleanup and the 600 ms settle callback.
    page.wait_for_timeout(900)
    assert page.locator("#editUserBtn").is_enabled()
    if field == "role":
        page.locator("#editRole_toggle").click()
        page.locator(f'#editRole_options [data-value="{old_role}"]').click()
    else:
        page.locator("#editIsActive").set_checked(active)
    page.wait_for_function("() => document.getElementById('editUserBtn').disabled")


def test_fast_course_edit_reverts_to_a_clean_form(users_page, live_server: str) -> None:
    page = users_page
    page.goto(live_server + "/dashboard/")
    menu = page.locator('[data-action="openCourseMenu"]:not(:disabled)').first
    if not menu.count():
        pytest.skip("needs an editable course in the development database")
    menu.click()
    page.locator('#courseMenuModal [data-action="openEditCourseModal"]').click()
    name = page.locator("#editCourseName")
    original = name.input_value()
    assert page.locator("#editCourseBtn").is_disabled()
    name.fill(original + " QA")
    page.wait_for_function("() => !document.getElementById('editCourseBtn').disabled")
    page.wait_for_timeout(900)
    assert page.locator("#editCourseBtn").is_enabled()
    name.fill(original)
    page.wait_for_function("() => document.getElementById('editCourseBtn').disabled")
    # The close warning must agree with Save about the reverted form.
    page.locator('#editCourseModal [data-modal-close="editCourseModal"]').first.click()
    page.wait_for_function(
        "() => !document.getElementById('editCourseModal').classList.contains('active')"
    )
    assert not page.locator("#gpConfirmDialog.active").count()
