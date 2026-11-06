"""Row actions are one line, and the columns fit their contents.

The admin Courses table gives each row up to four controls: archive or activate,
delete, settings - and, until now, a LABELLED "Teachers" button. The label was
the widest thing in a 12% column, so the group wrapped and that row stood about
40px taller than its neighbours: 85px against 45px, measured at 1440x900.

Making them all icons fixed the wrap and uncovered the real problem underneath.
The table was `table-layout: fixed` over six percentage columns, and no set of
percentages fits at every width: measured at 1600x1000 the course name needed
283px in a 265px column while the teacher cell needed 326px - moving points
between them only moved which cell was cut. The table is wider than its
container at that size, and a table that does not fit should scroll, not hide
its own content behind three dots.

So it uses the contract the Users table already uses, and that this file's own
tablet rule already used below 1180px: columns size to their content, the
wrapper scrolls. Measured after, at 1180 / 1440 / 1600 / 1920: nothing clipped,
and the four buttons (100px of buttons and gaps) inside a 128-144px group.
"""

from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
PAGE = REPO / "src/app/templates/admin_courses.html"
CSS = REPO / "src/app/templates/static/css/pages/admin.css"


def test_the_actions_never_wrap() -> None:
    css = (CSS.parent.parent / "tables.css").read_text(encoding="utf-8")
    shared = css.split(".gl-row-actions {", 1)[1].split("}", 1)[0]
    assert "flex-wrap: nowrap" in shared
    assert 'class="gl-row-actions"' in PAGE.read_text(encoding="utf-8")


def test_the_teachers_action_is_an_icon_like_the_rest_of_its_group() -> None:
    page = PAGE.read_text(encoding="utf-8")
    teachers = [line for line in page.splitlines() if "/teachers'" in line]
    assert teachers, "the Teachers action is gone from the row"
    # btn_link_icon_only, not a btn_link_icon with no words: that one kept its
    # text padding and stood 34px wide beside the 24px squares of its group.
    assert all("btn_link_icon_only(" in line for line in teachers), (
        "the Teachers action carries a label again - it is the widest thing in that "
        "column and pushes the other three onto a second line"
    )
    assert all("t('Assign teachers')" in line for line in teachers), (
        "an icon-only action needs its tooltip, or nobody can tell what it does"
    )


class TestTheColumnsFitTheirContents:
    def test_the_table_sizes_to_its_content(self) -> None:
        css = CSS.read_text(encoding="utf-8")
        assert "#adminCoursesTable.tbl-fixed { table-layout: auto; min-width: 860px; }" in css, (
            "the courses table is back on fixed percentage columns, which cannot "
            "fit every width - see this file's docstring for the measurements"
        )
        assert "#adminCoursesTable colgroup { display: none; }" in css

    def test_the_percentage_columns_are_gone(self) -> None:
        """A `width` is still a hint under auto layout, so leftover PERCENTAGES
        would pull against the content they are supposed to follow - the same
        note the Users table carries a few lines above.

        Pixel widths measured from the rendered table are a different thing and
        are allowed: they say what the column needs, not what fraction of the
        table it should take. The check is on the unit, which is what the name
        of this test says.
        """
        import re as _re

        css = CSS.read_text(encoding="utf-8")
        pct = _re.findall(r"\.col-course-[a-z]+\s*\{\s*width:\s*[\d.]+%", css)
        assert not pct, f"percentage widths are back on the courses columns: {pct}"

    def test_the_wrapper_can_scroll(self) -> None:
        """Content-sized columns only work because the scroll viewport around
        the table takes the overflow."""
        page = PAGE.read_text(encoding="utf-8")
        assert "table-scrollable" in page.split("id='adminCoursesTable'", 1)[0][-400:]
