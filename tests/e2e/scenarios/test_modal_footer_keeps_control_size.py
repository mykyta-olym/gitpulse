"""Tooltip wrappers must preserve the footer layout through button states."""

from __future__ import annotations

import os

import pytest

pytestmark = pytest.mark.e2e

if not os.getenv("GITPULSE_E2E_BASE_URL"):
    pytest.skip("modal layout checks need a running server", allow_module_level=True)


@pytest.mark.parametrize("width", [390, 640, 768, 1440])
@pytest.mark.parametrize("theme", ["light", "dark"])
@pytest.mark.parametrize("layout", ["fixed", "fluid"])
def test_modal_footer_buttons_keep_their_size(
    browser, context_for, live_server, width, theme, layout
):
    with browser.new_context(
        storage_state=context_for("admin").storage_state(),
        service_workers="block",
        viewport={"width": width, "height": 1000},
        has_touch=width <= 768,
        is_mobile=width <= 768,
    ) as ctx:
        writes, errors = [], []

        def read_only(route):
            if route.request.method in {"GET", "HEAD"}:
                route.continue_()
            else:
                writes.append(route.request.url)
                route.abort()

        ctx.route("**/api/v1/**", read_only)
        page = ctx.new_page()
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.bring_to_front()
        page.goto(live_server + "/dashboard/admin/courses?lang=en")
        courses = page.request.get(live_server + "/api/v1/courses").json()
        course = next((c for c in courses if c["archived_at"] is None), None)
        assert course, "seed an active course for the Add teacher regression"
        dialogs = [
            (
                f"/dashboard/courses/{course['id']}/teachers",
                "addTeacherModal",
                "btnAddTeacherSubmit",
            ),
            ("/dashboard/admin/users", "editUserModal", "editUserBtn"),
            ("/dashboard/", "createCourseModal", "createCourseBtn"),
        ]
        for path, modal_id, button_id in dialogs:
            page.goto(live_server + path + "?lang=en")
            page.wait_for_function("() => document.documentElement.hasAttribute('data-gp-ready')")
            page.evaluate(
                """({theme, layout}) => {
                  document.documentElement.dataset.theme = theme;
                  document.documentElement.dataset.layoutWidth = layout;
                }""",
                {"theme": theme, "layout": layout},
            )
            page.evaluate("id => GP.openModal(id)", modal_id)
            page.wait_for_function("() => !document.querySelector('.modal-animating')")
            button = page.locator("#" + button_id)
            initial = button.bounding_box()
            assert initial
            if modal_id == "addTeacherModal":
                assert button.is_disabled()
                username = page.locator('#addTeacherModal [x-data="teacherInvite()"]').evaluate(
                    "el => Alpine.$data(el).filteredUsers[0].username"
                )
                page.locator("#teacher-search").fill(username)
                page.locator("#addTeacherModal .gl-dropdown-item").first.click()
                page.wait_for_function(
                    "() => !document.getElementById('btnAddTeacherSubmit').disabled"
                )
                enabled = button.bounding_box()
                assert enabled
                assert abs(enabled["width"] - initial["width"]) <= 1
            page.evaluate(
                """id => {
                  const button = document.getElementById(id);
                  const footer = button.closest('.modal-footer');
                  window.__footerFrames = [];
                  window.__footerSampling = true;
                  function sample() {
                    const box = button.getBoundingClientRect();
                    const area = footer.getBoundingClientRect();
                    const spinner = button.querySelector(':scope > .gp-spinner');
                    // GlButton adds a leading spinner to a desktop text button;
                    // icon buttons replace their icon and grid tracks stay fixed.
                    const added = innerWidth > 768 && spinner
                      && !button.querySelector(':scope > .icon')
                      ? spinner.getBoundingClientRect().width
                        + parseFloat(getComputedStyle(button).columnGap) : 0;
                    __footerFrames.push({width: box.width - added, height: box.height,
                      footerHeight: area.height, inside: box.left >= area.left - 1
                        && box.right <= area.right + 1});
                    if (__footerSampling) requestAnimationFrame(sample);
                  }
                  sample();
                  button.disabled = true;
                  GP.setDisabledReason(button, GP.t('Loading...'));
                }""",
                button_id,
            )
            page.wait_for_timeout(80)
            cancel = page.locator(f"#{modal_id} .modal-footer [data-modal-close]").last
            if width <= 768:
                assert abs(button.bounding_box()["width"] - cancel.bounding_box()["width"]) <= 1
            page.evaluate("id => GP.setButtonLoading(document.getElementById(id), true)", button_id)
            page.wait_for_timeout(250)
            page.evaluate(
                "id => GP.setButtonLoading(document.getElementById(id), false)", button_id
            )
            page.wait_for_timeout(450)
            frames = page.evaluate("() => { __footerSampling = false; return __footerFrames; }")
            for dimension in ("width", "height", "footerHeight"):
                sizes = [frame[dimension] for frame in frames]
                assert max(sizes) - min(sizes) <= 1, (modal_id, dimension, sizes)
            assert all(frame["inside"] for frame in frames)
            page.evaluate("id => GP.closeModal(id, {force: true})", modal_id)
        assert not errors, errors
        assert not writes, writes
