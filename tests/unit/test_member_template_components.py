"""Static invariants for shared member table components."""

from __future__ import annotations

from pathlib import Path


def test_member_name_cell_does_not_duplicate_gitlab_access_role_badges() -> None:
    template = Path("src/app/templates/components/members.html").read_text(encoding="utf-8")
    role_badges_macro = template.split("{% macro member_role_badges", maxsplit=1)[1].split(
        "{% endmacro %}",
        maxsplit=1,
    )[0]

    assert "t('Admin')" not in role_badges_macro
    assert "t('Teacher')" not in role_badges_macro
    assert "t('Owner')" in role_badges_macro
