"""Shared header geometry and ticket actions against an owned local database."""

from __future__ import annotations

import asyncio
import json
import os
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from urllib.parse import urlsplit

import pytest
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

pytestmark = pytest.mark.e2e
if not os.getenv("GITPULSE_E2E_SUPPORT_FIXTURE"):
    pytest.skip("needs an owned local support fixture", allow_module_level=True)


@pytest.fixture
def ticket_data(live_server):
    from app.models import Course
    from app.models.support_ticket import SupportTicket

    database = os.environ["DATABASE_URL"]
    assert urlsplit(live_server).hostname in {"127.0.0.1", "localhost"}
    assert urlsplit(database).hostname in {"127.0.0.1", "localhost"}
    course = uuid.uuid4()

    async def write(create):
        engine = create_async_engine(database, poolclass=NullPool)
        try:
            async with async_sessionmaker(engine)() as db:
                if create:
                    db.add(
                        Course(
                            id=course,
                            code="support-" + course.hex[:8],
                            name="Support lifecycle",
                            academic_year="2026/2027",
                        )
                    )
                    await db.flush()
                    db.add_all(
                        SupportTicket(
                            feedback_token=uuid.uuid4(),
                            course_id=course,
                            feedback_type="support",
                            title=f"Owned {status} ticket",
                            status=status,
                            priority="medium",
                            category="general",
                            responses={"description": "Owned browser fixture"},
                            submitted_by="e2e-admin",
                            resolved_at=None if status == "open" else datetime.now(UTC),
                        )
                        for status in ["open", "resolved", "closed"]
                    )
                else:
                    await db.execute(delete(Course).where(Course.id == course))
                await db.commit()
        finally:
            await engine.dispose()

    def change(create):
        with ThreadPoolExecutor(max_workers=1) as worker:
            worker.submit(asyncio.run, write(create)).result()

    change(True)
    try:
        yield str(course)
    finally:
        change(False)


@pytest.fixture(params=[(390, "light"), (390, "dark"), (1440, "light"), (1440, "dark")])
def ticket_page(browser, context_for, live_server, ticket_data, request):
    width, theme = request.param
    with browser.new_context(
        storage_state=context_for("admin").storage_state(),
        viewport={"width": width, "height": 1000},
        service_workers="block",
        is_mobile=width == 390,
        has_touch=width == 390,
    ) as ctx:
        ctx.add_init_script(
            """(() => {
          const course=__COURSE_ID__;
          const Native = window.EventSource;
          window.__ticketProbe = {streams:[], hold:false, fail:false, pending:[], writes:0};
          class TicketStream extends EventTarget {
            constructor(url) {
              super(); this.url=url; this.closed=false; __ticketProbe.streams.push(this);
            }
            close() {this.closed=true;}
          }
          window.EventSource=function(url,options) {
            return String(url).includes('/courses/'+course+'/stream')
              ? new TicketStream(url) : new Native(url,options);
          };
          const fetch=window.fetch;
          window.fetch=(url,options)=>{
            if(String(url).includes('/api/v1/support/tickets/') && options?.method==='POST') {
              const s=__ticketProbe; s.writes++;
              if(s.fail)return Promise.resolve(new Response(
                JSON.stringify({detail:'Owned failure'}),
                {status:503,headers:{'Content-Type':'application/json'}}));
              return fetch(url,options).then(r=>s.hold
                ? new Promise(resolve=>s.pending.push(()=>resolve(r))) : r);
            }
            return fetch(url,options);
          };
        })();""".replace("__COURSE_ID__", json.dumps(ticket_data))
        )
        errors = []
        page = ctx.new_page()
        page.bring_to_front()
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.on("console", lambda msg: errors.append(msg.text) if msg.type == "error" else None)
        page.goto(f"{live_server}/dashboard/support/tickets?course_id={ticket_data}&lang=en")
        page.wait_for_function("() => __ticketProbe.streams.length === 1")
        page.evaluate(
            "theme => {document.documentElement.dataset.theme=theme;"
            " window.dispatchEvent(new Event('gp:themechange'));}",
            theme,
        )
        yield page, ticket_data
        assert not errors, errors


def _confirm(page, action):
    page.get_by_role("button", name=action, exact=True).last.click()


def _select_closed(page):
    page.locator('#ticketsTable tr[data-status="closed"] .ticket-select').check()
    page.locator("#btnDeleteSelectedTickets").click()


def test_ticket_stream_reconnect_cannot_outlive_its_page(ticket_page):
    page, _ = ticket_page
    page.evaluate("() => __ticketProbe.streams[0].onerror(new Event('error'))")
    page.evaluate("() => GP.navigateTo('/dashboard/admin/users?lang=en')")
    page.wait_for_url("**/admin/users?lang=en")
    page.wait_for_timeout(2300)
    assert page.evaluate("() => __ticketProbe.streams.length") == 1
    assert page.evaluate("() => __ticketProbe.streams.every(s=>s.closed)")
    page.evaluate(
        "() => __ticketProbe.streams[0].dispatchEvent(new MessageEvent('update',"
        "{data:JSON.stringify({event:'ticket_created'})}))"
    )
    page.wait_for_timeout(200)
    assert "/admin/users" in page.url


def test_ticket_stream_ignores_invalid_and_unrelated_events(ticket_page):
    page, _ = ticket_page
    page.evaluate("""() => {
      for (const data of ['{', '{}', '{"event":12}', '{"event":"sync_finished"}'])
        __ticketProbe.streams[0].dispatchEvent(new MessageEvent('update',{data}));
    }""")
    page.wait_for_timeout(200)
    assert page.locator("#ticketsTable tbody tr").count() == 3
    assert page.evaluate("() => __ticketProbe.streams.length") == 1
    with page.expect_navigation(wait_until="domcontentloaded"):
        page.evaluate(
            "() => __ticketProbe.streams[0].dispatchEvent(new MessageEvent('update',"
            "{data:JSON.stringify({event:'ticket_created'})}))"
        )
    page.wait_for_function("() => document.documentElement.hasAttribute('data-gp-ready')")
    assert page.locator("#ticketsTable tbody tr").count() == 3


def test_ticket_delete_cancel_failure_and_success_follow_real_result(ticket_page):
    page, _ = ticket_page
    _select_closed(page)
    _confirm(page, "Cancel")
    assert page.evaluate("() => __ticketProbe.writes") == 0
    assert page.locator("#ticketsTable tbody tr").count() == 3
    page.evaluate("() => __ticketProbe.fail=true")
    page.locator("#btnDeleteSelectedTickets").click()
    _confirm(page, "Delete")
    page.wait_for_function(
        "() => document.getElementById('btnDeleteSelectedTickets').getAttribute('aria-busy')"
        " !== 'true'"
    )
    assert page.locator("#ticketsTable tbody tr").count() == 3
    assert page.locator("#btnDeleteSelectedTickets").is_enabled()
    page.evaluate("() => {__ticketProbe.fail=false; __ticketProbe.hold=true;}")
    page.locator("#btnDeleteSelectedTickets").click()
    _confirm(page, "Delete")
    page.wait_for_function("() => __ticketProbe.pending.length === 1")
    button = page.locator("#btnDeleteSelectedTickets")
    assert button.is_disabled()
    assert button.get_attribute("aria-busy") == "true"
    with page.expect_navigation(wait_until="domcontentloaded"):
        page.evaluate("() => __ticketProbe.pending.splice(0).forEach(resolve=>resolve())")
    page.wait_for_function("() => document.documentElement.hasAttribute('data-gp-ready')")
    assert page.locator("#ticketsTable tbody tr").count() == 2
    assert page.locator('#ticketsTable tr[data-status="open"]').count() == 1


def test_ticket_purge_keeps_open_tickets(ticket_page):
    page, _ = ticket_page
    page.locator("#btnPurgeTickets").click()
    page.locator('[data-purge-tickets-hours="87600"]').click()
    with page.expect_navigation(wait_until="domcontentloaded"):
        _confirm(page, "Purge")
    page.wait_for_function("() => document.documentElement.hasAttribute('data-gp-ready')")
    assert page.locator("#ticketsTable tbody tr").count() == 1
    assert page.locator('#ticketsTable tr[data-status="open"]').count() == 1


def test_ticket_mutation_result_cannot_reload_the_destination(ticket_page):
    page, _ = ticket_page
    _select_closed(page)
    page.evaluate("() => __ticketProbe.hold=true")
    _confirm(page, "Delete")
    page.wait_for_function("() => __ticketProbe.pending.length === 1")
    page.evaluate("() => GP.navigateTo('/dashboard/admin/users?lang=en')")
    page.wait_for_url("**/admin/users?lang=en")
    page.wait_for_function("() => document.documentElement.hasAttribute('data-gp-ready')")
    reads = []
    page.on(
        "request",
        lambda request: reads.append(request.url) if request.is_navigation_request() else None,
    )
    page.evaluate("() => __ticketProbe.pending.splice(0).forEach(resolve=>resolve())")
    page.wait_for_timeout(500)
    assert not reads, reads
    assert "/admin/users" in page.url


@pytest.mark.parametrize("layout", ["fixed", "fluid"])
def test_mobile_card_heading_and_real_refresh_states_keep_their_geometry(
    ticket_page, live_server, layout
):
    page, course = ticket_page
    page.goto(f"{live_server}/dashboard/courses/{course}/activity?lang=en")
    page.wait_for_function("() => document.documentElement.hasAttribute('data-gp-ready')")
    page.evaluate("layout => document.documentElement.dataset.layoutWidth=layout", layout)
    header = page.locator("#activityHealthCard .card-header")
    for title in ["CI/CD Health", "CI/CD Health with a deliberately long translated title"]:
        header.locator(".card-title").evaluate("(el,title) => el.textContent=title", title)
        geometry = header.evaluate("""h => {
          const r=e=>e.getBoundingClientRect(), b=r(h), heading=r(h.querySelector('.card-heading')),
            icon=r(h.querySelector('.card-heading > .icon')),
            title=r(h.querySelector('.card-title')), actions=r(h.querySelector('.card-actions')),
            tip=r(h.querySelector('.card-header-info-tip'));
          return {left:b.left+parseFloat(getComputedStyle(h).paddingLeft),
            right:b.right-parseFloat(getComputedStyle(h).paddingRight),
            heading:{left:heading.left,right:heading.right,bottom:heading.bottom},
            actions:{left:actions.left,right:actions.right,top:actions.top},
            trailingRight:tip.right,
            iconWithTitle:icon.right<=title.left&&icon.top<title.bottom&&icon.bottom>title.top,
            noHelpOverlap:heading.right<=tip.left+1||heading.bottom<=tip.top+1
              ||heading.top>=tip.bottom-1};
        }""")
        assert geometry["iconWithTitle"]
        assert geometry["noHelpOverlap"]
        if title == "CI/CD Health":
            assert geometry["actions"]["top"] < geometry["heading"]["bottom"]
            assert abs(geometry["trailingRight"] - geometry["right"]) < 1
        elif geometry["actions"]["top"] >= geometry["heading"]["bottom"]:
            assert abs(geometry["actions"]["left"] - geometry["left"]) < 1
        assert geometry["actions"]["right"] <= geometry["right"] + 1
    button = page.locator("#btnRefreshActivity")
    before = button.bounding_box()
    button.click()
    page.wait_for_function(
        "() => document.getElementById('btnRefreshActivity').getAttribute('aria-busy') !== 'true'"
    )
    after = button.bounding_box()
    assert abs(before["width"] - after["width"]) < 1
    assert abs(before["height"] - after["height"]) < 1
    if page.viewport_size["width"] == 390:
        assert after["height"] >= 32


@pytest.fixture
def detail_page(ticket_page, live_server):
    page, _ = ticket_page
    href = page.locator('#ticketsTable tr[data-status="open"] .ticket-title-link').get_attribute(
        "href"
    )
    assert href
    page.add_init_script(r"""(() => {
      const Native=window.EventSource, fetch=window.fetch;
      window.__detailProbe={streams:[],posts:0,puts:0,hold:false,holdFields:false,
        pending:[],fields:[],failStatus:false,failComment:false,blocked:false};
      class Stream extends EventTarget {
        constructor(url){super();this.url=url;this.closed=false;__detailProbe.streams.push(this);}
        close(){this.closed=true;}
      }
      window.EventSource=function(url,options){
        if(__detailProbe.blocked)throw new Error('Owned blocked connection');
        return /\/support\/tickets\/\d+\/stream/.test(String(url))
          ? new Stream(url) : new Native(url,options);
      };
      window.fetch=(url,options)=>{
        const s=__detailProbe;
        if(/\/support\/tickets\/\d+\/comments$/.test(String(url))&&options?.method==='POST'){
          s.posts++;
          if(s.failComment)return Promise.resolve(new Response(
            JSON.stringify({detail:'Owned comment failure'}),
            {status:422,headers:{'Content-Type':'application/json'}}));
          return fetch(url,options).then(r=>s.hold
            ? new Promise(resolve=>s.pending.push(()=>resolve(r))) : r);
        }
        if(/\/support\/tickets\/\d+$/.test(String(url))&&options?.method==='PUT'){
          s.puts++;
          if(s.failStatus)return Promise.resolve(new Response(
            JSON.stringify({detail:'Owned status failure'}),
            {status:422,headers:{'Content-Type':'application/json'}}));
          if(s.holdFields)return fetch(url,options).then(r=>
            new Promise(resolve=>s.fields.push(()=>resolve(r))));
        }
        return fetch(url,options);
      };
    })();""")
    page.goto(f"{live_server}{href}?lang=en")
    page.wait_for_function("() => __detailProbe.streams.length === 1")
    return page


def test_empty_reply_preview_reveals_the_invalid_editor_without_a_request(detail_page):
    page = detail_page
    page.get_by_role("tab", name="Preview", exact=True).click()
    page.get_by_text("Nothing to preview.", exact=True).wait_for(state="visible")
    page.locator('.gh-reply-buttons [value="comment"]').click()
    page.locator("#reply_content").wait_for(state="visible")
    assert page.locator("#reply_content").evaluate("el => document.activeElement === el")
    assert page.evaluate("__detailProbe.posts") == 0
    assert (
        page.get_by_role("tab", name="Write", exact=True).get_attribute("aria-selected") == "true"
    )
    page.get_by_role("button", name="Bold", exact=True).click()
    assert page.locator("#reply_content").input_value() == "**text**"
    page.get_by_role("tab", name="Preview", exact=True).click()
    assert page.locator(".gh-md-preview strong").inner_text() == "text"


def test_reply_upload_prevents_comment_submission_until_the_file_is_confirmed(detail_page):
    page = detail_page
    page.evaluate("""()=>{
      const f=window.fetch;
      window.fetch=(url,o)=>String(url).includes('/api/v1/support/upload')
        ?new Promise(resolve=>window.__finishUpload=()=>resolve(new Response(
          '{"url":"/uploads/owned.txt"}',{headers:{'Content-Type':'application/json'}})))
        :f(url,o);
    }""")
    page.locator("#reply_content").fill("Keep this reply")
    with page.expect_file_chooser() as picker:
        page.locator("[data-md-upload]").click()
    picker.value.set_files({"name": "owned.txt", "mimeType": "text/plain", "buffer": b"owned"})
    page.wait_for_function("() => !!window.__finishUpload")
    assert page.locator(".gh-reply-form").evaluate("el => el.inert")
    page.evaluate("""()=>document.querySelector('.gh-reply-form').requestSubmit(
      document.querySelector('.gh-reply-buttons [value=comment]'))""")
    assert page.evaluate("__detailProbe.posts") == 0
    assert page.locator("#reply_content").input_value() == "Keep this reply"
    page.evaluate("""()=>{
      const id=Number(location.pathname.split('/').pop());
      __detailProbe.streams[0].dispatchEvent(new MessageEvent('update',{
        data:JSON.stringify({ticket_id:id,fields:{status:'closed'}})
      }));
    }""")
    page.evaluate("() => __finishUpload()")
    page.wait_for_function("() => !document.querySelector('.gh-reply-form').inert")
    assert page.locator("#reply_content").input_value().endswith("[owned.txt](/uploads/owned.txt)")
    assert page.locator('.gh-reply-buttons [value="reopen"]').is_visible()


def test_comment_is_confirmed_without_a_live_stream(detail_page):
    page = detail_page
    text = "Owned comment without a stream"
    page.locator("#reply_content").fill(text)
    page.get_by_role("tab", name="Preview", exact=True).click()
    page.evaluate("() => __detailProbe.hold=true")
    button = page.locator('.gh-reply-buttons [value="comment"]')
    before = button.bounding_box()
    page.get_by_role("button", name="Comment", exact=True).click()
    page.wait_for_function("() => __detailProbe.pending.length === 1")
    button.locator(".gp-spinner").wait_for(state="visible")
    during = button.bounding_box()
    assert abs(before["width"] - during["width"]) < 1
    assert abs(before["height"] - during["height"]) < 1
    assert page.locator(".gh-reply-form").get_attribute("aria-busy") == "true"
    assert page.locator(".gh-reply-form").evaluate("el => el.inert")
    page.evaluate("() => __detailProbe.pending.splice(0).forEach(resolve=>resolve())")
    page.locator(".gh-ticket-thread .gh-thread-text").filter(has_text=text).wait_for()
    assert page.locator("#reply_content").input_value() == ""
    assert page.locator("#reply_content").is_visible()
    assert page.evaluate("() => __detailProbe.posts") == 1
    assert page.locator(".gh-ticket-thread [data-comment-id]").count() == 1
    assert page.locator(".gh-thread-time time[data-localize-time]").count() >= 1
    comment_id = page.locator(".gh-ticket-thread [data-comment-id]").get_attribute(
        "data-comment-id"
    )
    page.reload()
    page.wait_for_function("() => __detailProbe.streams.length === 1")
    page.evaluate(
        """id => {
          const ticket=JSON.parse(document.getElementById('gh-ticket-cfg').textContent).ticketId;
          const data=JSON.stringify({ticket_id:ticket,comment:{id,content:'Duplicate echo'}});
          __detailProbe.streams[0].dispatchEvent(new MessageEvent('comment',{data}));
          __detailProbe.streams[0].dispatchEvent(new MessageEvent('comment',{data:'invalid'}));
        }""",
        comment_id,
    )
    assert page.locator(".gh-ticket-thread [data-comment-id]").count() == 1


def test_comment_success_is_kept_when_status_update_fails(detail_page):
    page = detail_page
    text = "Owned comment with a failed close"
    page.locator("#reply_content").fill(text)
    page.evaluate("() => __detailProbe.failStatus=true")
    page.get_by_role("button", name="Close with comment", exact=True).click()
    page.wait_for_function("() => __detailProbe.puts === 1")
    page.wait_for_function("() => !document.querySelector('.gh-reply-form').inert")
    assert page.locator("#reply_content").input_value() == ""
    assert page.locator(".gh-ticket-thread .gh-thread-text").filter(has_text=text).count() == 1
    assert "Open" in page.locator("#ghStatusBadge").inner_text()
    assert "Comment added" in page.locator(".toast").last.inner_text()
    assert page.evaluate("() => __detailProbe.posts") == 1


def test_detail_stream_reconnect_cannot_outlive_navigation(detail_page):
    page = detail_page
    page.evaluate("() => __detailProbe.streams[0].onerror(new Event('error'))")
    page.evaluate("() => GP.navigateTo('/dashboard/admin/users?lang=en')")
    page.wait_for_url("**/admin/users?lang=en")
    page.wait_for_timeout(5300)
    assert page.evaluate("() => __detailProbe.streams.length") == 1
    assert page.evaluate("() => __detailProbe.streams.every(s=>s.closed)")


def test_detail_stream_pauses_and_recovers_from_a_blocked_connection(detail_page):
    page = detail_page
    page.evaluate("""() => {
      Object.defineProperty(document,'visibilityState',{configurable:true,value:'hidden'});
      document.dispatchEvent(new Event('visibilitychange'));
    }""")
    assert page.evaluate("() => __detailProbe.streams[0].closed")
    page.get_by_text("Live updates paused", exact=True).wait_for()
    page.evaluate("""() => {
      __detailProbe.blocked=true;
      Object.defineProperty(document,'visibilityState',{configurable:true,value:'visible'});
      document.dispatchEvent(new Event('visibilitychange'));
    }""")
    page.get_by_text("Live updates unavailable", exact=True).wait_for()
    page.evaluate("() => __detailProbe.blocked=false")
    page.get_by_role("button", name="Retry", exact=True).click()
    page.evaluate("""() => __detailProbe.streams.at(-1).dispatchEvent(
      new MessageEvent('connected',{data:'{}'}))""")
    page.get_by_text("Live updates active", exact=True).wait_for()


def test_ticket_fields_keep_the_draft_and_roll_back_on_failure(detail_page):
    page = detail_page
    page.evaluate(
        "() => window.__priorityLabel="
        "document.querySelector('#priority_toggle .gl-form-dropdown-text')"
    )
    page.locator("#reply_content").fill("Keep my unsent reply")
    page.evaluate("() => __detailProbe.holdFields=true")
    page.locator("#priority_toggle").click()
    page.locator('#priority_options [data-value="high"]').click()
    page.wait_for_function("() => __detailProbe.fields.length === 1")
    before = page.locator("#priority_toggle .gl-form-dropdown-text").bounding_box()
    page.wait_for_timeout(250)
    during = page.locator("#priority_toggle .gl-form-dropdown-text").bounding_box()
    assert abs(before["y"] - during["y"]) < 1
    assert abs(before["height"] - during["height"]) < 1
    assert page.locator(".gh-ticket-sidebar .card-body").evaluate("el => el.inert")
    assert page.locator(".gh-ticket-sidebar .card-body").get_attribute("aria-busy") == "true"
    page.evaluate("() => __detailProbe.fields.splice(0).forEach(resolve=>resolve())")
    page.wait_for_function("() => !document.querySelector('.gh-ticket-sidebar .card-body').inert")
    assert "High" in page.locator("#priority_toggle").inner_text()
    assert page.locator("#reply_content").input_value() == "Keep my unsent reply"
    page.evaluate("() => __detailProbe.failStatus=true")
    page.locator("#priority_toggle").click()
    page.locator('#priority_options [data-value="critical"]').click()
    page.wait_for_function("() => __detailProbe.puts === 2")
    page.wait_for_function("() => !document.querySelector('.gh-ticket-sidebar .card-body').inert")
    assert page.locator("#priority").input_value() == "high"
    assert "High" in page.locator("#priority_toggle").inner_text()
    assert page.evaluate(
        "() => __priorityLabel===document.querySelector('#priority_toggle .gl-form-dropdown-text')"
    )
    assert page.locator("#reply_content").input_value() == "Keep my unsent reply"


def test_late_comment_result_cannot_touch_the_destination(detail_page):
    page = detail_page
    page.locator("#reply_content").fill("Owned late response")
    page.evaluate("() => __detailProbe.hold=true")
    page.get_by_role("button", name="Comment", exact=True).click()
    page.wait_for_function("() => __detailProbe.pending.length === 1")
    page.evaluate("() => GP.navigateTo('/dashboard/admin/users?lang=en')")
    page.get_by_role("button", name="Leave page", exact=True).click()
    page.wait_for_url("**/admin/users?lang=en")
    page.evaluate("() => window.__destinationMain=document.getElementById('main-content')")
    page.evaluate("() => __detailProbe.pending.splice(0).forEach(resolve=>resolve())")
    page.wait_for_timeout(700)
    assert page.evaluate("() => __destinationMain===document.getElementById('main-content')")
    assert page.locator(".gh-thread-entry").count() == 0
    assert page.locator(".toast").filter(has_text="Comment added").count() == 0


def test_cancelled_navigation_keeps_the_reply_and_live_connection(detail_page):
    page = detail_page
    page.locator("#reply_content").fill("Keep this unsent reply")
    page.evaluate("() => GP.navigateTo('/dashboard/admin/users?lang=en')")
    page.get_by_role("button", name="Cancel", exact=True).last.click()
    assert "/support/ticket/" in page.url
    assert page.locator("#reply_content").input_value() == "Keep this unsent reply"
    page.evaluate("() => window.dispatchEvent(new Event('beforeunload'))")
    assert not page.evaluate("() => __detailProbe.streams[0].closed")
    page.locator("#reply_content").fill("")
    assert not page.evaluate("() => GP.hasUnsavedState()")
    page.evaluate("() => GP.navigateTo('/dashboard/admin/users?lang=en')")
    page.wait_for_url("**/admin/users?lang=en")


def test_cancelled_assignment_keeps_the_unsent_reply(detail_page):
    page = detail_page
    username = page.locator("#gh-ticket-cfg").evaluate(
        "el => JSON.parse(el.textContent).staffUsers[0].username"
    )
    page.locator("#reply_content").fill("Keep my reply before reassignment")
    page.locator("#assignee_search").fill(username)
    page.locator(".gh-assignee-search .gl-dropdown-item").first.click()
    page.get_by_text(
        "Changing the assignee reloads this page. Discard your unsent reply?", exact=True
    ).wait_for()
    page.get_by_role("button", name="Cancel", exact=True).last.click()
    assert page.evaluate("() => __detailProbe.puts") == 0
    assert page.locator("#reply_content").input_value() == "Keep my reply before reassignment"
    assert not page.evaluate("() => __detailProbe.streams[0].closed")
    page.locator("#reply_content").fill("")
    page.locator("#assignee_search").fill(username)
    with page.expect_navigation(wait_until="domcontentloaded"):
        page.locator(".gh-assignee-search .gl-dropdown-item").first.click()
    page.wait_for_function("() => document.documentElement.hasAttribute('data-gp-ready')")
    assert page.locator(".gh-assignee-current .gl-avatar-labeled-label").inner_text() == username
    assert page.locator(".toast").filter(has_text="Ticket updated").count() == 1


def test_failed_comment_preserves_the_draft_for_retry(detail_page):
    page = detail_page
    page.locator("#reply_content").fill("Retry this owned comment")
    page.locator('[name="is_internal"]').check()
    page.evaluate("() => __detailProbe.failComment=true")
    page.locator('.gh-reply-buttons [value="comment"]').click()
    page.wait_for_function(
        "() => __detailProbe.posts === 1 && !document.querySelector('.gh-reply-form').inert"
    )
    assert page.locator("#reply_content").input_value() == "Retry this owned comment"
    assert page.locator('[name="is_internal"]').is_checked()
    assert page.evaluate("() => GP.hasUnsavedState()")
    assert page.locator(".gh-ticket-thread [data-comment-id]").count() == 0
    page.evaluate("() => __detailProbe.failComment=false")
    page.locator('.gh-reply-buttons [value="comment"]').click()
    page.locator(".gh-ticket-thread [data-comment-id]").wait_for()
    assert not page.evaluate("() => GP.hasUnsavedState()")
    assert page.locator(".gh-thread-internal").count() == 1


def test_comment_close_and_reopen_keep_the_working_button(detail_page):
    page = detail_page
    page.locator("#reply_content").fill("Close this owned ticket")
    page.evaluate("() => __detailProbe.hold=true")
    page.locator('.gh-reply-buttons [value="close"]').click()
    page.wait_for_function("() => __detailProbe.pending.length === 1")
    page.evaluate("""() => {
      const ticket=JSON.parse(document.getElementById('gh-ticket-cfg').textContent).ticketId;
      __detailProbe.streams[0].dispatchEvent(new MessageEvent('update',{
        data:JSON.stringify({ticket_id:ticket,fields:{status:'closed'}})}));
    }""")
    assert page.locator('.gh-reply-buttons [value="close"]').get_attribute("aria-busy") == "true"
    page.evaluate("() => __detailProbe.pending.splice(0).forEach(resolve=>resolve())")
    page.locator('.gh-reply-buttons [value="reopen"]').wait_for()
    assert "Closed" in page.locator("#ghStatusBadge").inner_text()
    page.locator("#reply_content").fill("Reopen this owned ticket")
    page.evaluate("() => __detailProbe.hold=false")
    page.locator('.gh-reply-buttons [value="reopen"]').click()
    page.locator('.gh-reply-buttons [value="comment"]').wait_for()
    assert "Open" in page.locator("#ghStatusBadge").inner_text()
    assert page.locator(".gh-ticket-thread [data-comment-id]").count() == 2
