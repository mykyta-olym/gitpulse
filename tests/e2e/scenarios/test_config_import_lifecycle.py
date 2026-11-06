"""JSON imports apply the reviewed editor and discard drafts consistently."""

from __future__ import annotations

import itertools
import json
import os

import pytest

pytestmark = pytest.mark.e2e

if not os.getenv("GITPULSE_E2E_BASE_URL"):
    pytest.skip("config import checks need a running server", allow_module_level=True)

_IMPORTS = {
    "dashboard": (
        "importConfigCourseModal",
        "import_config_paste_input",
        "btnImportConfigApply",
        "importConfigPreview",
    ),
    "full": (
        "fullConfigModal",
        "full_config_paste_input",
        "btnFullConfigApply",
        "fullConfigPreview",
    ),
    "checks": (
        "importChecksModal",
        "checks_config_paste_input",
        "btnImportChecksApply",
        "importChecksPreview",
    ),
}


def _config(code: str = "DRAFT-A") -> str:
    metadata = {"code": code, "name": code, "academic_year": "2026/2027", "semester": "winter"}
    return json.dumps(
        {"course": metadata, "source_course": metadata, "builtin_checks": [], "custom_checks": []}
    )


@pytest.fixture(
    params=list(itertools.product(_IMPORTS, ["desktop", "mobile", "reduced"])),
    ids=lambda value: "-".join(value),
)
def import_page(browser, context_for, live_server: str, request):
    kind, mode = request.param
    with browser.new_context(
        storage_state=context_for("admin").storage_state(),
        service_workers="block",
        viewport={"width": 1440 if mode == "desktop" else 390, "height": 900},
        has_touch=mode != "desktop",
        is_mobile=mode != "desktop",
        reduced_motion="reduce" if mode == "reduced" else "no-preference",
    ) as ctx:
        writes = []

        def block_writes(route):
            if route.request.method in {"GET", "HEAD"}:
                route.continue_()
            elif any(
                part in route.request.url
                for part in ("/courses/import-config", "/settings/full-config", "/checks/import")
            ):
                writes.append(json.loads(route.request.post_data))
                route.fulfill(status=409, json={"detail": "Import rejected for testing"})
            else:
                route.fulfill(status=204)

        ctx.route("**/*", block_writes)
        page = ctx.new_page()
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.bring_to_front()
        if kind == "dashboard":
            page.goto(live_server + "/dashboard/")
        else:
            page.goto(live_server + "/dashboard/admin/courses?period=all")
            rows = page.locator('#adminCoursesTable tr[data-is-active="true"]')
            if not rows.count():
                pytest.skip("an active development course is required")
            course_id = rows.first.get_attribute("data-course-id")
            page.goto(live_server + f"/dashboard/courses/{course_id}/settings")
        modal, editor, button, preview = _IMPORTS[kind]
        page.wait_for_function("() => !!GP.ConfigImport && !!GP.openModal")
        page.locator(f"#{editor}").wait_for(state="attached")
        page.evaluate("id => GP.openModal(id)", modal)
        yield page, modal, editor, button, preview, writes
        assert not errors, errors


def _answer(page, discard: bool) -> None:
    page.locator("#gpConfirmDialog.active").wait_for()
    page.locator(
        f'#gpConfirmDialog [data-gp-confirm="{"ok" if discard else "cancel"}"]'
    ).last.click()
    page.wait_for_function("() => !document.querySelector('#gpConfirmDialog.active')")


def _close(page, modal: str, path: str) -> None:
    if path == "cancel":
        page.locator(f"#{modal} .modal-footer .btn-secondary").click()
    elif path == "x":
        page.locator(f"#{modal} .modal-close").click()
    elif path == "escape":
        page.keyboard.press("Escape")
    else:
        page.wait_for_timeout(220)
        page.locator(f"#{modal}").click(position={"x": 2, "y": 2})


def test_edited_or_invalid_json_cannot_apply_an_old_preview(import_page):
    page, modal, editor, button, preview, writes = import_page
    field, apply = page.locator(f"#{editor}"), page.locator(f"#{button}")
    field.fill(_config())
    page.wait_for_timeout(650)
    assert apply.is_enabled()
    field.fill("{invalid")
    assert apply.is_disabled()
    assert not page.locator(f"#{preview}").is_visible()
    page.wait_for_timeout(650)
    assert apply.is_disabled()
    field.fill("[]")
    page.wait_for_timeout(650)
    assert apply.is_disabled()
    field.fill(_config("DRAFT-B"))
    page.wait_for_timeout(650)
    apply.click()
    _answer(page, True)
    page.wait_for_function(
        "id => !document.getElementById(id).classList.contains('loading')", arg=button
    )
    assert len(writes) == 1
    assert writes[0]["course"]["code"] == "DRAFT-B"
    assert writes[0]["$schema"] == (
        "gitpulse/check-config/v1" if modal == "importChecksModal" else "gitpulse/full-config/v2"
    )
    assert field.input_value() == _config("DRAFT-B")
    assert apply.is_enabled(), "a failed import must remain retryable"


@pytest.mark.parametrize("path", ["cancel", "x", "escape", "backdrop"])
def test_all_close_paths_protect_and_discard_parsed_and_unparsed_drafts(import_page, path):
    page, modal, editor, button, preview, writes = import_page
    text = "{unparsed" if path in {"cancel", "x"} else _config()
    page.locator(f"#{editor}").fill(text)
    if path in {"x", "escape"}:
        page.wait_for_timeout(650)
    _close(page, modal, path)
    _answer(page, False)
    assert page.locator(f"#{editor}").input_value() == text
    assert page.locator(f"#{modal}.active").count() == 1
    assert page.evaluate("() => GP.hasUnsavedState()")
    _close(page, modal, path)
    _answer(page, True)
    page.wait_for_function(
        "id => !document.getElementById(id).classList.contains('active')", arg=modal
    )
    page.wait_for_timeout(650)
    assert not page.evaluate("() => GP.hasUnsavedState()")
    page.evaluate("id => GP.openModal(id)", modal)
    assert page.locator(f"#{editor}").input_value() == ""
    assert page.locator(f"#{button}").is_disabled()
    assert not page.locator(f"#{preview}").is_visible()
    assert not writes


def test_pending_parse_is_cancelled_on_close_and_quick_reopen(import_page):
    page, modal, editor, button, _preview, writes = import_page
    page.locator(f"#{editor}").fill(_config())
    page.evaluate("id => { GP.forceCloseModal(id); GP.openModal(id); }", modal)
    page.wait_for_timeout(750)
    assert page.locator(f"#{editor}").input_value() == ""
    assert page.locator(f"#{button}").is_disabled()
    assert not page.evaluate("() => GP.hasUnsavedState()")
    page.locator(f"#{editor}").fill("{new draft")
    page.keyboard.press("Escape")
    _answer(page, False)
    assert page.locator(f"#{editor}").input_value() == "{new draft"
    assert not writes


def test_file_chip_and_editor_are_cleared_only_after_discard(import_page):
    page, modal, editor, button, _preview, writes = import_page
    control = page.locator(f"#{modal} .gl-file-upload-input")
    control.focus()
    with page.expect_file_chooser() as picker:
        control.press("Enter")
    picker.value.set_files(
        {
            "name": "long-course-configuration-name-" * 6 + ".json",
            "mimeType": "application/json",
            "buffer": _config().encode(),
        }
    )
    page.wait_for_timeout(650)
    assert page.locator(f"#{button}").is_enabled()
    assert page.locator(f"#{modal} .gl-json-drop-file").is_visible()
    assert page.locator(f"#{modal} .gl-json-drop").evaluate("""el => {
      const box=el.getBoundingClientRect();
      const picker=el.querySelector('.gl-file-upload').getBoundingClientRect();
      return picker.left>=box.left && picker.right<=box.right+1;
    }""")
    _close(page, modal, "cancel")
    _answer(page, False)
    assert page.locator(f"#{modal} .gl-json-drop-file").is_visible()
    _close(page, modal, "cancel")
    _answer(page, True)
    page.evaluate("id => GP.openModal(id)", modal)
    assert page.locator(f"#{editor}").input_value() == ""
    assert not page.locator(f"#{modal} .gl-json-drop-file").is_visible()
    assert not writes


def test_file_clear_has_a_touch_target_and_restores_the_clean_editor(import_page):
    page, modal, editor, _button, _preview, writes = import_page
    page.locator(f"#{modal} input[type=file]").set_input_files(
        {"name": "config.json", "mimeType": "application/json", "buffer": _config().encode()}
    )
    page.locator(f"#{modal} .gl-json-drop-file").wait_for()
    clear = page.locator(f"#{modal} .gl-json-drop-clear")
    assert clear.get_attribute("aria-label")
    if page.evaluate("matchMedia('(pointer: coarse)').matches"):
        clear.click(trial=True)
        assert clear.evaluate("el => parseFloat(getComputedStyle(el,'::before').width) >= 32")
        box = clear.bounding_box()
        page.mouse.click(box["x"] + box["width"] / 2 - 18, box["y"] + box["height"] / 2)
    else:
        clear.click()
    assert page.locator(f"#{editor}").input_value() == ""
    assert page.locator(f"#{modal} .gl-json-drop-file").is_hidden()
    assert not page.evaluate("GP.hasUnsavedState()")
    assert not writes


def test_file_reads_cannot_overwrite_a_new_file_typing_or_a_closed_dialog(import_page):
    page, modal, editor, _button, _preview, writes = import_page
    page.evaluate("""() => {
      window.__readers = [];
      window.FileReader = class {
        readAsText(file) { this.name = file.name; __readers.push(this); }
        abort() { this.aborted = true; }
        finish(text) { this.onload({target:{result:text}}); }
      };
    }""")
    upload = page.locator(f"#{modal} input[type=file]")
    for name in ("first.json", "second.json"):
        upload.set_input_files({"name": name, "mimeType": "application/json", "buffer": b"{}"})
    page.evaluate(
        "text => { __readers[1].finish(text); __readers[0].finish('{}'); }", _config("SECOND")
    )
    assert page.locator(f"#{editor}").input_value() == _config("SECOND")
    upload.set_input_files({"name": "third.json", "mimeType": "application/json", "buffer": b"{}"})
    page.locator(f"#{editor}").fill("manual edit")
    page.evaluate("() => __readers[2].finish('{}')")
    assert page.locator(f"#{editor}").input_value() == "manual edit"
    upload.set_input_files({"name": "late.json", "mimeType": "application/json", "buffer": b"{}"})
    page.evaluate("id => { GP.forceCloseModal(id); __readers[3].finish('{}'); }", modal)
    page.wait_for_timeout(750)
    assert page.locator(f"#{editor}").input_value() == ""
    assert not page.evaluate("() => GP.hasUnsavedState()")
    assert not writes


def test_navigation_discards_pending_import_and_returns_with_a_fresh_controller(
    import_page, live_server
):
    page, modal, editor, button, _preview, writes = import_page
    path = page.url.removeprefix(live_server)
    page.locator(f"#{editor}").fill(_config())
    page.evaluate("() => GP.navigateTo('/dashboard/preferences')")
    _answer(page, False)
    assert page.locator(f"#{editor}").input_value() == _config()
    page.evaluate("() => GP.navigateTo('/dashboard/preferences')")
    _answer(page, True)
    page.wait_for_function(
        """() => location.pathname === '/dashboard/preferences'
          && !document.querySelector('#main-content.is-navigating')"""
    )
    page.wait_for_timeout(750)
    assert not page.evaluate("() => GP.hasUnsavedState()")
    page.evaluate("path => GP.navigateTo(path)", path)
    page.wait_for_function(
        """path => location.pathname + location.search === path
          && !document.querySelector('#main-content.is-navigating')""",
        arg=path,
    )
    page.evaluate("id => GP.openModal(id)", modal)
    assert page.locator(f"#{editor}").input_value() == ""
    assert page.locator(f"#{button}").is_disabled()
    page.locator(f"#{editor}").fill(_config("RETURNED"))
    page.wait_for_timeout(750)
    assert page.locator(f"#{button}").is_enabled()
    page.keyboard.press("Escape")
    _answer(page, False)
    assert page.locator(f"#{editor}").input_value() == _config("RETURNED")
    assert not writes
