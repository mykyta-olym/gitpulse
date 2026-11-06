"""Support submission keeps its draft, request state and feedback on its own page."""

from __future__ import annotations

import os
from urllib.parse import urlsplit

import pytest

pytestmark = pytest.mark.e2e
if not os.getenv("GITPULSE_E2E_BASE_URL"):
    pytest.skip("needs a running local server", allow_module_level=True)


@pytest.fixture(
    params=[
        (390, "light", False),
        (390, "dark", False),
        (1440, "light", False),
        (1440, "dark", False),
        (390, "dark", True),
    ]
)
def submission_page(browser, context_for, live_server, request):
    assert urlsplit(live_server).hostname in {"127.0.0.1", "localhost"}
    width, theme, reduced = request.param
    identity = context_for("admin")
    courses = identity.request.get(live_server + "/api/v1/courses").json()
    assert courses, "requires a local course fixture"
    path = f"/dashboard/support?course_id={courses[0]['id']}&category=general&lang=en"
    with browser.new_context(
        storage_state=identity.storage_state(),
        viewport={"width": width, "height": 1000},
        is_mobile=width == 390,
        has_touch=width == 390,
        service_workers="block",
        reduced_motion="reduce" if reduced else "no-preference",
    ) as context:
        context.add_init_script("""(() => {
          const fetch = window.fetch;
          window.__submissions = [];
          window.fetch = (url, options) => {
            if (options?.method !== 'POST' || options.body instanceof FormData
                || !String(url).includes('/api/v1/support/'))
              return fetch(url, options);
            return new Promise((resolve, reject) => {
              __submissions.push({
              body:JSON.parse(options.body), signal:options.signal,
              reply(fail=false) {resolve(new Response(JSON.stringify(
                fail ? {detail:'Owned submission failure'} : {ok:true}),
                {status:fail ? 503 : 200, headers:{'Content-Type':'application/json'}}));},
              reject() {reject(new TypeError('Owned network failure'));},
              });
              options.signal.addEventListener('abort', () => reject(options.signal.reason),
                {once:true});
            });
          };
        })()""")
        page = context.new_page()
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.on("console", lambda msg: errors.append(msg.text) if msg.type == "error" else None)
        page.goto(live_server + path)
        page.wait_for_selector("#supportForm")
        page.wait_for_function("() => document.documentElement.hasAttribute('data-gp-ready')")
        page.evaluate("theme => document.documentElement.dataset.theme = theme", theme)
        yield page, path
        assert not errors


def _fill(page):
    page.locator("#title").fill("Owned request")
    page.locator("#description").fill("Owned description with **Markdown**")


def _submit(page):
    page.locator('#supportForm [type="submit"]').click()
    page.wait_for_function("() => __submissions.length === 1")


def test_required_fields_do_not_start_a_request(submission_page):
    page, _ = submission_page
    assert not page.evaluate("GP.hasDirtyReason('support_form')")
    page.locator('#supportForm [type="submit"]').click()
    assert page.evaluate("__submissions.length") == 0
    assert page.locator("#successMessage").is_hidden()


@pytest.mark.parametrize("method", ["click", "requestSubmit"])
def test_invalid_preview_reveals_and_focuses_the_required_editor(submission_page, method):
    page, _ = submission_page
    page.locator("#title").fill("Preview validation")
    page.get_by_role("tab", name="Preview", exact=True).click()
    page.get_by_text("Nothing to preview.", exact=True).wait_for(state="visible")
    if method == "click":
        page.locator('#supportForm [type="submit"]').click()
    else:
        page.evaluate("() => document.querySelector('#supportForm').requestSubmit()")
    page.locator("#description").wait_for(state="visible")
    assert page.locator("#description").evaluate("el => document.activeElement === el")
    assert (
        page.get_by_role("tab", name="Write", exact=True).get_attribute("aria-selected") == "true"
    )
    assert page.locator(".gh-md-preview").is_hidden()
    assert page.evaluate("__submissions.length") == 0
    page.locator("#description").fill("Now the description is valid")
    page.get_by_role("tab", name="Preview", exact=True).click()
    page.evaluate("() => document.querySelector('#supportForm').requestSubmit()")
    page.wait_for_function("() => __submissions.length === 1")
    page.evaluate("() => __submissions[0].reply()")
    page.wait_for_selector("#successMessage .empty-state-title")


@pytest.mark.parametrize("edit", ["format", "priority", "attachment"])
def test_custom_controls_protect_the_changed_draft_without_marking_setup_dirty(
    submission_page, edit
):
    page, _ = submission_page
    # A programmatic default and opening a dropdown do not edit the draft.
    page.locator('#supportForm input[name="priority"]').dispatch_event("change")
    assert not page.evaluate("GP.hasDirtyReason('support_form')")
    if edit == "format":
        page.get_by_role("button", name="Bold", exact=True).click()
        assert page.locator("#description").input_value() == "**text**"
    elif edit == "priority":
        dropdown = page.locator('[data-tour="support-priority"]')
        dropdown.locator(".gl-form-dropdown-toggle").click()
        assert not page.evaluate("GP.hasDirtyReason('support_form')")
        dropdown.locator('[data-value="high"]').click()
        page.wait_for_function("() => document.querySelector('[name=priority]').value === 'high'")
    else:
        page.route(
            "**/api/v1/support/upload",
            lambda route: route.fulfill(json={"url": "/uploads/owned.txt"}),
        )
        with page.expect_file_chooser() as picker:
            page.locator("[data-md-upload]").click()
        assert not page.evaluate("GP.hasDirtyReason('support_form')")
        picker.value.set_files({"name": "owned.txt", "mimeType": "text/plain", "buffer": b"draft"})
        page.wait_for_function(
            "() => document.querySelector('#description').value.includes('/uploads/owned.txt')"
        )
    assert page.evaluate("GP.hasDirtyReason('support_form')")
    page.evaluate("() => GP.navigateTo('/dashboard/preferences')")
    page.locator('#gpConfirmDialog [data-gp-confirm="cancel"]').last.click()
    page.wait_for_function("() => !document.querySelector('#gpConfirmDialog.active')")
    assert page.locator("#supportForm").is_visible()
    assert page.evaluate("GP.hasDirtyReason('support_form')")


def test_formatting_and_preview_work_after_entering_from_a_page_without_the_editor(
    submission_page, live_server
):
    page, path = submission_page
    page.goto(live_server + "/dashboard/preferences?lang=en")
    page.evaluate("path => GP.navigateTo(path)", path)
    page.wait_for_url(live_server + path)
    page.wait_for_function(
        "() => !document.querySelector('#main-content.is-arriving,#main-content.is-navigating')"
    )
    page.get_by_role("button", name="Bold", exact=True).click()
    assert page.locator("#description").input_value() == "**text**"
    page.get_by_role("tab", name="Preview", exact=True).click()
    assert page.locator(".gh-md-preview strong").inner_text() == "text"
    assert page.evaluate("GP.hasDirtyReason('support_form')")


def test_pending_is_real_stable_and_only_success_reveals_the_shared_result(submission_page):
    page, _ = submission_page
    _fill(page)
    button = page.locator('#supportForm [type="submit"]')
    button.scroll_into_view_if_needed()
    before = button.bounding_box()
    _submit(page)
    assert page.locator("#supportForm").evaluate("el => el.inert")
    assert page.locator("#supportForm").get_attribute("aria-busy") == "true"
    page.wait_for_timeout(220)
    pending = button.bounding_box()
    assert all(abs(before[key] - pending[key]) < 1 for key in ("x", "y", "width", "height"))
    assert button.locator(".gp-spinner").count() == 1
    assert page.locator("#supportForm").evaluate(
        "el => getComputedStyle(el, '::after').content === 'none'"
    )
    assert page.locator("#successMessage").is_hidden()
    page.evaluate("() => document.querySelector('#supportForm').requestSubmit()")
    assert page.evaluate("__submissions.length") == 1
    assert (
        page.evaluate("__submissions[0].body.responses.description")
        == "Owned description with **Markdown**"
    )
    page.evaluate("() => __submissions[0].reply()")
    page.wait_for_selector("#successMessage .empty-state-title")
    assert page.locator("#supportForm").is_hidden()
    assert page.locator("#successMessage .empty-state-illustration svg").is_visible()
    assert page.locator("#successMessage").evaluate("el => document.activeElement === el")
    assert not page.evaluate("GP.hasDirtyReason('support_form')")
    page.evaluate("() => document.querySelector('#supportForm').requestSubmit()")
    assert page.evaluate("__submissions.length") == 1
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")


@pytest.mark.parametrize("network", [False, True])
def test_failure_preserves_the_draft_and_can_retry(submission_page, network):
    page, _ = submission_page
    _fill(page)
    page.get_by_role("tab", name="Preview", exact=True).click()
    _submit(page)
    page.evaluate(
        "network => network ? __submissions[0].reject() : __submissions[0].reply(true)", network
    )
    page.wait_for_function("() => !document.querySelector('#supportForm').inert")
    assert page.locator("#title").input_value() == "Owned request"
    assert page.locator("#description").input_value() == "Owned description with **Markdown**"
    assert page.locator(".gh-md-preview").is_visible()
    assert page.locator("#successMessage").is_hidden()
    assert page.evaluate("GP.hasDirtyReason('support_form')")
    page.locator('#supportForm [type="submit"]').click()
    page.wait_for_function("() => __submissions.length === 2")
    page.evaluate("() => __submissions[1].reply()")
    page.wait_for_selector("#successMessage .empty-state-title")


@pytest.mark.parametrize("fail", [False, True])
def test_previous_form_response_cannot_change_the_new_form_or_its_feedback(
    submission_page, live_server, fail
):
    page, path = submission_page
    _fill(page)
    _submit(page)
    page.evaluate("() => GP.navigateTo('/dashboard/preferences')")
    page.locator('#gpConfirmDialog [data-gp-confirm="ok"]').click()
    page.wait_for_url(live_server + "/dashboard/preferences")
    page.wait_for_function("() => !document.querySelector('#main-content.is-arriving')")
    page.evaluate("path => GP.navigateTo(path)", path)
    page.wait_for_url(live_server + path)
    page.wait_for_selector("#supportForm")
    page.wait_for_function(
        "() => !document.querySelector('#main-content.is-arriving,#main-content.is-navigating')"
    )
    page.locator("#title").fill("New unsent draft")
    assert page.evaluate("GP.hasDirtyReason('support_form')")
    page.evaluate("() => GP.showToast('New page error', 'danger')")
    page.evaluate("fail => __submissions[0].reply(fail)", fail)
    page.wait_for_timeout(150)
    assert page.evaluate("GP.hasDirtyReason('support_form')")
    assert page.locator("#title").input_value() == "New unsent draft"
    assert page.locator("#successMessage").is_hidden()
    assert page.get_by_text("New page error", exact=True).is_visible()
    assert not page.get_by_text("Owned submission failure", exact=True).count()


def test_cancelled_navigation_keeps_the_pending_form_and_draft_guard(submission_page):
    page, path = submission_page
    _fill(page)
    _submit(page)
    page.evaluate("() => GP.navigateTo('/dashboard/preferences')")
    page.locator('#gpConfirmDialog [data-gp-confirm="cancel"]').last.click()
    page.wait_for_function("() => !document.querySelector('#gpConfirmDialog.active')")
    assert page.url.endswith(path)
    assert page.locator("#supportForm").evaluate("el => el.inert")
    assert page.evaluate("GP.hasDirtyReason('support_form')")
    page.evaluate("() => window.dispatchEvent(new Event('beforeunload'))")
    assert page.evaluate("GP.hasDirtyReason('support_form')")
    page.evaluate("() => __submissions[0].reply()")
    page.wait_for_selector("#successMessage .empty-state-title")


def test_timeout_unlocks_the_form_and_allows_an_explicit_retry(submission_page):
    page, _ = submission_page
    page.clock.install()
    _fill(page)
    _submit(page)
    page.clock.fast_forward(10001)
    page.wait_for_function("() => !document.querySelector('#supportForm').inert")
    assert page.evaluate("__submissions[0].signal.aborted")
    assert page.locator("#description").input_value() == "Owned description with **Markdown**"
    assert page.locator("#successMessage").is_hidden()
    page.locator('#supportForm [type="submit"]').click()
    page.wait_for_function("() => __submissions.length === 2")
    page.evaluate("() => __submissions[1].reply()")
    page.wait_for_selector("#successMessage .empty-state-title")


@pytest.fixture
def attachment_page(submission_page):
    page, path = submission_page
    page.evaluate("""() => {
      const fetch=window.fetch;
      window.__uploads=[];
      window.__detachedFocus=0;
      const focus=HTMLTextAreaElement.prototype.focus;
      HTMLTextAreaElement.prototype.focus=function(){
        if(!this.isConnected)__detachedFocus++;
        return focus.apply(this,arguments);
      };
      window.fetch=(url,options)=>{
        if(!String(url).includes('/api/v1/support/upload'))return fetch(url,options);
        return new Promise((resolve,reject)=>{
          __uploads.push({file:options.body.get('file').name, signal:options.signal,
            reply(fail=false,url='/uploads/owned.txt') {resolve(new Response(
              JSON.stringify(fail ? {detail:'Owned attachment failure'} : {url}),
              {status:fail?503:200,headers:{'Content-Type':'application/json'}}));},
            reject(){reject(new TypeError('Owned attachment network failure'));}
          });
          options.signal.addEventListener('abort',()=>reject(options.signal.reason),{once:true});
        });
      };
    }""")
    return page, path


def _choose_attachment(page, files=None):
    control = page.locator(".gl-file-upload-input")
    control.focus()
    with page.expect_file_chooser() as picker:
        control.press("Enter")
    picker.value.set_files(
        files
        if files is not None
        else {"name": "owned.txt", "mimeType": "text/plain", "buffer": b"owned"}
    )


def test_upload_hint_keeps_text_and_pending_feedback_in_place(attachment_page):
    page, _ = attachment_page
    page.set_viewport_size({"width": 320, "height": 1000})
    assert page.locator(".gh-required-notice").evaluate(
        "el => el.getBoundingClientRect().height <= parseFloat(getComputedStyle(el).lineHeight) + 1"
    )
    button = page.locator("[data-md-upload]")
    button.scroll_into_view_if_needed()
    hint = page.locator(".gh-md-hint").first
    measure = """el => {
      const outer=el.getBoundingClientRect();
      return [...el.children].map(child=>{
        const r=child.getBoundingClientRect();
        return {x:r.x-outer.x,y:r.y-outer.y,width:r.width,height:r.height,
          inside:r.left>=outer.left&&r.right<=outer.right};
      });
    }"""
    before = hint.evaluate(measure)
    assert before
    assert all(item["inside"] for item in before)
    assert hint.evaluate("""el => {
      const text=el.querySelector(':scope > .flex-1').getBoundingClientRect();
      return [...el.querySelectorAll('label, button')].every(button=>
        button.getBoundingClientRect().left>=text.right);
    }""")
    assert hint.evaluate("""el => {
      const centers=[...el.children].map(child=>{
        const r=child.getBoundingClientRect();return r.y+r.height/2;
      });
      return Math.max(...centers)-Math.min(...centers)<1;
    }""")
    _choose_attachment(page)
    page.wait_for_function("() => __uploads.length === 1")
    page.wait_for_timeout(220)
    pending = hint.evaluate(measure)
    assert len(before) == len(pending)
    for old, new in zip(before, pending, strict=True):
        assert new["inside"]
        assert all(abs(old[key] - new[key]) < 1 for key in ("x", "y", "width", "height"))
    assert page.locator("#supportForm").evaluate(
        "el => getComputedStyle(el).opacity === '1' && "
        "getComputedStyle(el, '::after').content === 'none'"
    )
    page.evaluate("() => __uploads[0].reply()")
    page.wait_for_function("() => !document.querySelector('#supportForm').inert")
    assert hint.evaluate(measure) == before


@pytest.mark.parametrize("method", ["choose", "paste", "drop"])
def test_attachment_is_a_real_form_state_and_preserves_selection(attachment_page, method):
    page, _ = attachment_page
    _fill(page)
    before = page.locator("[data-md-upload]").bounding_box()
    page.locator("#description").evaluate("el => el.setSelectionRange(0,5)")
    if method == "choose":
        _choose_attachment(page)
    else:
        page.locator("#description").evaluate(
            """(el,method)=>{
              const data=new DataTransfer();data.items.add(new File(['owned'],'owned.txt'));
              const event=method==='paste'
                ? new ClipboardEvent('paste',{clipboardData:data,bubbles:true,cancelable:true})
                : new DragEvent('drop',{dataTransfer:data,bubbles:true,cancelable:true});
              el.dispatchEvent(event);
            }""",
            method,
        )
    page.wait_for_function("() => __uploads.length===1")
    assert page.locator("#supportForm").evaluate("el => el.inert")
    assert page.locator("#supportForm").get_attribute("aria-busy") == "true"
    assert page.locator("#description").input_value() == "Owned description with **Markdown**"
    page.wait_for_timeout(220)
    assert page.locator("[data-md-upload] .gp-spinner").count() == 1
    assert page.locator("#supportForm").evaluate(
        "el => getComputedStyle(el, '::after').content === 'none'"
    )
    after = page.locator("[data-md-upload]").bounding_box()
    assert all(abs(before[key] - after[key]) < 1 for key in ("width", "height"))
    page.evaluate("() => document.querySelector('#supportForm').requestSubmit()")
    assert page.evaluate("__submissions.length") == 0
    page.evaluate("() => __uploads[0].reply()")
    page.wait_for_function("() => !document.querySelector('#supportForm').inert")
    assert (
        page.locator("#description").input_value()
        == "[owned.txt](/uploads/owned.txt) description with **Markdown**"
    )
    assert page.evaluate("GP.hasDirtyReason('support_form')")
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")


@pytest.mark.parametrize("network", [False, True])
def test_attachment_failure_preserves_the_draft_and_same_file_can_retry(attachment_page, network):
    page, _ = attachment_page
    _fill(page)
    _choose_attachment(page)
    page.wait_for_function("() => __uploads.length===1")
    page.evaluate("n=>n?__uploads[0].reject():__uploads[0].reply(true)", network)
    page.wait_for_function("() => !document.querySelector('#supportForm').inert")
    assert page.locator("#description").input_value() == "Owned description with **Markdown**"
    assert page.locator("[data-md-upload]").is_enabled()
    assert page.evaluate("__uploads.length") == 1
    _choose_attachment(page)
    page.wait_for_function("() => __uploads.length===2")
    page.evaluate("() => __uploads[1].reply()")
    page.wait_for_function("() => !document.querySelector('#supportForm').inert")
    assert "/uploads/owned.txt" in page.locator("#description").input_value()


def test_failed_attachment_keeps_an_untouched_form_clean(attachment_page):
    page, _ = attachment_page
    _choose_attachment(page)
    page.wait_for_function("() => __uploads.length === 1")
    page.evaluate("() => __uploads[0].reply(true)")
    page.wait_for_function("() => !document.querySelector('#supportForm').inert")
    assert page.locator("#description").input_value() == ""
    assert not page.evaluate("GP.hasUnsavedState()")


def test_attachment_timeout_releases_the_real_state_without_mutating_the_draft(attachment_page):
    page, _ = attachment_page
    page.clock.install()
    _choose_attachment(page)
    page.wait_for_function("() => __uploads.length===1")
    assert page.evaluate("GP.hasUnsavedState()")
    page.clock.fast_forward(10001)
    page.wait_for_function("() => !document.querySelector('#supportForm').inert")
    assert page.evaluate("__uploads[0].signal.aborted")
    assert page.locator("#description").input_value() == ""
    assert not page.evaluate("GP.hasUnsavedState()")


@pytest.mark.parametrize("fail", [False, True])
def test_late_attachment_cannot_touch_the_next_editor_or_clear_its_upload_guard(
    attachment_page, live_server, fail
):
    page, path = attachment_page
    _choose_attachment(page)
    page.wait_for_function("() => __uploads.length===1")
    page.evaluate("() => GP.navigateTo('/dashboard/preferences?lang=en')")
    page.locator('#gpConfirmDialog [data-gp-confirm="ok"]').click()
    page.wait_for_url(live_server + "/dashboard/preferences?lang=en")
    page.wait_for_function("() => !document.querySelector('#main-content.is-arriving')")
    assert page.evaluate("__uploads[0].signal.aborted")
    page.evaluate("path => GP.navigateTo(path)", path)
    page.wait_for_url(live_server + path)
    page.wait_for_function(
        "() => !document.querySelector('#main-content.is-arriving,#main-content.is-navigating')"
    )
    _choose_attachment(page)
    page.wait_for_function("() => __uploads.length===2")
    page.evaluate("f=>__uploads[0].reply(f)", fail)
    page.wait_for_timeout(100)
    assert page.locator("#description").input_value() == ""
    assert page.locator("#supportForm").evaluate("el => el.inert")
    assert page.evaluate("GP.hasUnsavedState()")
    assert page.evaluate("__detachedFocus") == 0
    assert not page.get_by_text("Owned attachment failure", exact=True).count()
    page.evaluate("() => __uploads[1].reply()")
    page.wait_for_function("() => !document.querySelector('#supportForm').inert")


def test_upload_navigation_can_be_cancelled_without_losing_the_pending_file(attachment_page):
    page, path = attachment_page
    _choose_attachment(page)
    page.wait_for_function("() => __uploads.length===1")
    page.evaluate("() => GP.navigateTo('/dashboard/preferences')")
    page.locator('#gpConfirmDialog [data-gp-confirm="cancel"]').last.click()
    page.wait_for_function("() => !document.querySelector('#gpConfirmDialog.active')")
    assert page.url.endswith(path)
    assert page.locator("#supportForm").evaluate("el => el.inert")
    page.evaluate("() => __uploads[0].reply()")
    page.wait_for_function("() => !document.querySelector('#supportForm').inert")
    assert "/uploads/owned.txt" in page.locator("#description").input_value()


@pytest.mark.parametrize("partial", [False, True])
def test_uploads_with_the_same_name_are_ordered_and_partial_success_is_retained(
    attachment_page, partial
):
    page, _ = attachment_page
    files = [{"name": "same.txt", "mimeType": "text/plain", "buffer": b"one"}] * 2
    _choose_attachment(page, files)
    page.wait_for_function("() => __uploads.length===1")
    page.evaluate("() => __uploads[0].reply(false,'/uploads/one.txt')")
    page.wait_for_function("() => __uploads.length===2")
    page.evaluate("p=>__uploads[1].reply(p,'/uploads/two.txt')", partial)
    page.wait_for_function("() => !document.querySelector('#supportForm').inert")
    expected = "[same.txt](/uploads/one.txt)"
    if not partial:
        expected += "\n[same.txt](/uploads/two.txt)"
    assert page.locator("#description").input_value() == expected


def test_attachment_updates_an_open_preview_without_stealing_outside_focus(attachment_page):
    page, _ = attachment_page
    page.get_by_role("tab", name="Preview", exact=True).click()
    _choose_attachment(page)
    page.wait_for_function("() => __uploads.length===1")
    outside = page.get_by_role("link", name="Skip to main content", exact=True)
    outside.focus()
    page.evaluate("() => __uploads[0].reply()")
    page.wait_for_function("() => !document.querySelector('#supportForm').inert")
    assert page.locator('.gh-md-preview a[href="/uploads/owned.txt"]').is_visible()
    assert outside.evaluate("el => document.activeElement === el")


def test_file_drag_state_preserves_geometry_and_text_drags_keep_native_behavior(attachment_page):
    page, _ = attachment_page
    before = page.locator("#description").bounding_box()
    result = page.locator("#description").evaluate("""el=>{
      const data=new DataTransfer();data.items.add(new File(['x'],'owned.txt'));
      const enter=new DragEvent('dragover',{dataTransfer:data,bubbles:true,cancelable:true});
      el.dispatchEvent(enter);
      const r=el.getBoundingClientRect();
      const active=el.classList.contains('dragover');
      el.dispatchEvent(new DragEvent('dragleave',{bubbles:true}));
      const text=new DataTransfer();text.setData('text/plain','native text');
      const plain=new DragEvent('dragover',{dataTransfer:text,bubbles:true,cancelable:true});
      el.dispatchEvent(plain);
      return {width:r.width,height:r.height,active,textPrevented:plain.defaultPrevented};
    }""")
    assert result["active"]
    assert not result["textPrevented"]
    assert abs(result["width"] - before["width"]) < 1
    assert abs(result["height"] - before["height"]) < 1


def test_cancelled_picker_and_oversize_batch_do_not_change_or_upload_the_draft(attachment_page):
    page, _ = attachment_page
    _choose_attachment(page, files=[])
    page.locator("#description").evaluate("""el=>{
      const data=new DataTransfer();
      data.items.add(new File(['small'],'small.txt'));
      data.items.add(new File([new Uint8Array(50*1024*1024+1)],'large.txt'));
      el.dispatchEvent(new DragEvent('drop',{dataTransfer:data,bubbles:true,cancelable:true}));
    }""")
    assert page.evaluate("__uploads.length") == 0
    assert page.locator("#description").input_value() == ""
    assert not page.locator("#supportForm").evaluate("el => el.inert")
    assert not page.evaluate("GP.hasUnsavedState()")
    assert page.get_by_text("File is too large. Max 50 MB", exact=True).is_visible()
