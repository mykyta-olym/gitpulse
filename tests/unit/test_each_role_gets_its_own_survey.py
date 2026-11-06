"""The dashboard's support panel links every role to its own thesis survey."""

from pathlib import Path

import pytest
from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.config import Settings
from app.i18n import register_jinja_i18n

TEMPLATES = Path(__file__).resolve().parents[2] / "src/app/templates"
SURVEYS = {
    "student": "https://forms.example/student",
    "teacher": "https://forms.example/teacher",
    "admin": "https://forms.example/admin",
}


def _survey_links(role: str) -> list[str]:
    env = Environment(loader=FileSystemLoader(TEMPLATES), autoescape=select_autoescape())
    register_jinja_i18n(env)
    env.globals["t"] = lambda text: text
    html = env.get_template("partials/dashboard/_sidebar.html").render(
        is_admin=role == "admin",
        is_teacher=role in ("admin", "teacher"),
        is_student=role == "student",
        survey_urls=SURVEYS,
        contact_email="author@example.test",
    )
    return [key for key, url in SURVEYS.items() if f'href="{url}"' in html]


@pytest.mark.parametrize(
    ("role", "surveys"),
    [("student", ["student"]), ("teacher", ["teacher"]), ("admin", ["teacher", "admin"])],
)
def test_each_role_gets_its_own_survey(role: str, surveys: list[str]) -> None:
    assert _survey_links(role) == surveys


def test_the_default_surveys_are_three_different_forms() -> None:
    defaults = {Settings.model_fields[f"survey_url_{role}"].default for role in SURVEYS}
    assert len(defaults) == 3
