"""Analysis errors use the server's shared component and role-specific guidance."""

from pathlib import Path
from types import SimpleNamespace

import pytest
from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.i18n import register_jinja_i18n

TEMPLATES = Path(__file__).resolve().parents[2] / "src/app/templates"


def _render(role: str, error_type: str, enabled: bool = True) -> str:
    env = Environment(loader=FileSystemLoader(TEMPLATES), autoescape=select_autoescape())
    register_jinja_i18n(env)
    env.globals["t"] = lambda text: text
    return env.get_template("partials/project/_ai_analysis.html").render(
        feature_llm_suggestions=enabled,
        can_edit=role != "student",
        is_admin=role == "admin",
        is_teacher=role == "teacher",
        is_student=role == "student",
        project=SimpleNamespace(id="project"),
        analysis_started=False,
        llm_analyses=[],
        llm_last_error={
            "error_type": error_type,
            "error_message": "<script>untrusted</script>",
            "errors": [{"mr_iid": 1, "exception": "Error", "detail": "private provider detail"}],
        },
        csrf_token="fixture-token",
    )


@pytest.mark.parametrize("role", ["admin", "teacher", "student"])
@pytest.mark.parametrize(
    ("error_type", "variant"),
    [
        ("quota_exceeded", "warning"),
        ("network_error", "warning"),
        ("no_mrs", "info"),
        ("invalid_api_key", "danger"),
        ("parse_error", "danger"),
        ("unexpected", "danger"),
    ],
)
def test_error_guidance_and_actions_follow_the_viewer_role(role, error_type, variant):
    html = _render(role, error_type)
    assert f"gitlab-alert gitlab-alert-{variant} llm-error-card" in html
    assert "<script>untrusted</script>" not in html
    assert "&lt;script&gt;untrusted&lt;/script&gt;" in html
    assert ("private provider detail" in html) == (role == "admin")
    assert "Your instructor has been notified" not in html
    assert ('data-action="retryProjectAnalysis"' in html) == (role != "student")
    assert ('data-submit-action="dismissLlmError"' in html) == (role != "student")


def test_disabled_analysis_has_no_ui_or_controls():
    html = _render("admin", "network_error", enabled=False)
    assert 'id="analysisProgress"' not in html
    assert 'id="llmAnalysisForm"' not in html
    assert "private provider detail" not in html
