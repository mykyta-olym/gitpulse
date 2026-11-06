"""Shared controls keep their geometry and expose identifiable form fields."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.e2e


@pytest.fixture
def controls_context(browser, admin_context, live_server):
    with browser.new_context(
        storage_state=admin_context.storage_state(), service_workers="block"
    ) as context:
        context.add_cookies([{"name": "gp_lang", "value": "en", "url": live_server}])
        yield context


def _course_path(page, base):
    page.goto(base + "/dashboard/")
    link = page.locator('a[href^="/dashboard/courses/"]').first
    if not link.count():
        pytest.skip("needs a course in the development database")
    return link.get_attribute("href").split("?")[0]


@pytest.mark.parametrize("table", ["assistant", "users"])
@pytest.mark.parametrize(
    ("width", "layout"),
    [(1440, "fixed"), (2560, "fixed"), (2560, "fluid"), (390, "fluid")],
)
def test_filter_selection_does_not_resize_neighbouring_controls(
    controls_context, live_server, table, width, layout
):
    page = controls_context.new_page()
    page.set_viewport_size({"width": width, "height": 1000})
    page.bring_to_front()
    path = (
        _course_path(page, live_server) + "/assistant"
        if table == "assistant"
        else "/dashboard/admin/users"
    )
    page.goto(live_server + path)
    page.evaluate("layout => document.documentElement.dataset.layoutWidth = layout", layout)
    strip = page.locator(".table-controls .filter-tabs").first
    strip.scroll_into_view_if_needed()
    page.wait_for_timeout(100)
    for index in range(strip.locator(".tab-btn").count()):
        samples = strip.evaluate(
            """async (strip, index) => {
              const band = strip.closest('.table-controls');
              const measure = () => {
                const root = band.getBoundingClientRect();
                const search = band.querySelector('.table-controls-search');
                const sr = search?.getBoundingClientRect();
                const tr = strip.getBoundingClientRect();
                return [root.width, root.height, sr?.width || 0, tr.width,
                  ...[...strip.querySelectorAll('.tab-btn')].flatMap(el => {
                    const r = el.getBoundingClientRect();
                    return [r.left - tr.left + strip.scrollLeft, r.width, r.height];
                  })];
              };
              const frames = [measure()];
              strip.querySelectorAll('.tab-btn')[index].click();
              for (let i = 0; i < 12; i++) {
                await new Promise(requestAnimationFrame);
                frames.push(measure());
              }
              return frames;
            }""",
            index,
        )
        baseline = samples[0]
        for sample in samples[1:]:
            assert sample == pytest.approx(baseline, abs=0.5), (
                f"{table}, {width}px/{layout}: selecting filter {index} shifted the controls"
            )
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")


@pytest.mark.parametrize("width", [390, 1440])
@pytest.mark.parametrize("theme", ["light", "dark"])
def test_tab_indicators_meet_the_divider_and_stay_visible(
    controls_context, live_server, width, theme
):
    page = controls_context.new_page()
    page.set_viewport_size({"width": width, "height": 1000})
    page.bring_to_front()
    course = _course_path(page, live_server)
    course_id = course.rsplit("/", 1)[-1]
    for path, selector in [
        (course + "/settings", "#checkFilters"),
        ("/dashboard/admin/users", ".users-role-filter"),
        ("/dashboard/", ".gl-home-sidebar-panel .filter-tabs"),
        (f"/dashboard/support?course_id={course_id}&category=bug", ".gh-md-header .tabs-nav"),
    ]:
        page.goto(live_server + path)
        page.evaluate("theme => document.documentElement.dataset.theme = theme", theme)
        strip = page.locator(selector).first
        strip.scroll_into_view_if_needed()
        samples = strip.evaluate("""async strip => {
          const measure = () => {
            const r = strip.getBoundingClientRect();
            const active = strip.querySelector('.active');
            const a = active.getBoundingClientRect();
            const s = getComputedStyle(active);
            const before = getComputedStyle(active, '::before');
            const ink = strip.querySelector('.gp-tab-ink')?.getBoundingClientRect();
            const bottom = ink?.bottom ?? a.bottom - parseFloat(s.borderBottomWidth)
              - parseFloat(before.bottom);
            const top = ink?.top ?? bottom - parseFloat(before.borderBottomWidth);
            const band = strip.closest('.table-controls, .gh-md-header');
            return {height: r.height, baseline: r.bottom, bottom,
              band: band?.getBoundingClientRect().bottom ?? r.bottom,
              visible: Math.min(bottom, r.bottom) - Math.max(top, r.top)};
          };
          const samples = [measure()];
          const tabs = strip.querySelectorAll('.tab-btn');
          for (const tab of [tabs[tabs.length - 1], tabs[0]]) {
            tab.click();
            for (let i = 0; i < 16; i++) {
              await new Promise(requestAnimationFrame);
              samples.push(measure());
            }
          }
          return samples;
        }""")
        for sample in samples:
            assert sample["height"] == samples[0]["height"]
            assert sample["baseline"] == pytest.approx(sample["band"], abs=0.5)
            assert sample["baseline"] == pytest.approx(sample["bottom"], abs=0.5)
            assert sample["visible"] == pytest.approx(2, abs=0.1)


def test_form_fields_have_an_identity_after_render_and_dynamic_refresh(
    controls_context, live_server
):
    page = controls_context.new_page()
    page.bring_to_front()
    course = _course_path(page, live_server)
    page.goto(live_server + course)
    links = page.locator('a[href^="/dashboard/teams/"]')
    team = links.first.get_attribute("href") if links.count() else None
    paths = [
        "/dashboard/admin/system",
        "/dashboard/admin/users",
        "/dashboard/admin/events",
        "/dashboard/preferences",
        "/dashboard/support/tickets",
        course + "/assistant",
        course + "/settings",
    ]
    if team:
        paths.append(team)
    for path in paths:
        response = page.goto(live_server + path)
        assert response.status == 200, path
        page.wait_for_timeout(150)
        if path.endswith("/system"):
            page.locator("#btnRefreshJobs").click()
            page.wait_for_function(
                "() => !document.querySelector('#jobsTableBody .table-loading-row')"
            )
        if path.endswith("/settings"):
            page.wait_for_function(
                "() => !!document.querySelector('[data-check-code] input, input[data-check-code]')"
            )
        missing = page.locator("input,select,textarea").evaluate_all(
            "els => els.filter(el => !el.id.trim() && !el.name.trim()).map(el => el.outerHTML)"
        )
        assert not missing, f"{path}: fields without id or name: {missing}"
        duplicates = page.locator("input[id],select[id],textarea[id]").evaluate_all(
            """els => els.filter(el => el.id && document.querySelectorAll(
                '#' + CSS.escape(el.id)).length > 1).map(el => el.id)"""
        )
        assert not duplicates, f"{path}: duplicate field ids: {duplicates}"


def test_analytics_renders_checklist_and_week_without_late_requests(controls_context, live_server):
    page = controls_context.new_page()
    page.bring_to_front()
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    path = _course_path(page, live_server)
    response = page.goto(live_server + path + "/analytics?_gp_refresh=1")
    assert response.status == 200
    config = page.locator("#gp-analytics-config")
    assert config.count() == 1
    if page.evaluate(
        "JSON.parse(document.querySelector('#gp-analytics-config').textContent).checklistData.length"
    ):
        page.locator("#checklistCanvas").scroll_into_view_if_needed()
        page.wait_for_function("() => !!Chart.getChart('checklistCanvas')")
    page.locator("#weekPills .tab-btn").last.click()
    assert page.locator("#weekDetail").is_visible()
    assert not errors


def test_transition_cover_keeps_field_identities_separate(controls_context, live_server):
    page = controls_context.new_page()
    page.bring_to_front()
    page.goto(live_server + "/dashboard/preferences")
    report = page.evaluate("""() => {
      const main = document.getElementById('main-content');
      GP.motion.coverPage(main);
      const cover = document.querySelector('.gp-page-cover');
      const snapshot = cover.shadowRoot;
      const fields = [...snapshot.querySelectorAll('input, select, textarea')];
      const report = {
        inert: cover.inert,
        fields: fields.length,
        missing: fields.filter(el => !el.id && !el.name).length,
        duplicates: fields.filter(el => document.getElementById(el.id) === el).length,
        liveBehaviour: !!snapshot.querySelector('script')
          || [...snapshot.querySelectorAll('[x-data]')].some(el => !!el._x_dataStack),
        invalidLabels: [...snapshot.querySelectorAll('label')].filter(label =>
          !label.control || !snapshot.contains(label.control)).length
      };
      GP.motion.uncoverPage(main, true);
      return report;
    }""")
    assert report["fields"] > 10, "the cover must actually contain a form"
    assert report["inert"]
    assert not report["missing"]
    assert not report["duplicates"]
    assert not report["liveBehaviour"]
    assert not report["invalidLabels"]
