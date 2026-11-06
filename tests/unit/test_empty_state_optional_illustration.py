"""The shared empty state's default illustration is optional."""

import pytest

from app.main import templates


@pytest.mark.parametrize("illustration", ["", "empty-commit"])
def test_empty_state_renders_with_or_without_an_illustration(illustration):
    template = templates.env.from_string(
        "{% from 'components/cards.html' import empty_state %}"
        "{{ empty_state('No commits', message='No records', illustration=illustration) }}"
    )
    html = template.render(illustration=illustration)
    assert "No commits" in html
    assert "No records" in html
    assert ("empty-state-illustration" in html) is bool(illustration)
