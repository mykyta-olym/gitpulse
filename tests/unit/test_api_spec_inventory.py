"""`docs/04-api-spec.md` must list the routes the app actually serves.

The spec had drifted badly - it documented `POST /api/v1/teams/{id}/recheck`,
`/api/v1/reports/{filename}`, `/api/v1/telemetry/flags*`,
`/api/v1/telemetry/report/*`, `/api/v1/telemetry/support/forms*`,
`/api/v1/courses/{id}/clone` and more, none of which exist, while omitting
whole areas that do (transfer, run-checks, webhook-configs, job cancel, SSE
streams). Anyone integrating against it was reading fiction.

Section 5 of that document is generated from the live route table; this test is
what keeps it honest.
"""

import re
from pathlib import Path

from app.main import create_app
from tests.route_discovery import iter_routes

SPEC = Path(__file__).resolve().parents[2] / "docs" / "04-api-spec.md"


def _spec_paths() -> set[str]:
    text = SPEC.read_text(encoding="utf-8")
    start = text.index("## 5. Current Endpoint Inventory")
    section = text[start : text.index("## 6. Dashboard Routes")]
    # Lines look like: - `GET /api/v1/courses/{course_id}`
    return {m.group(1) for m in re.finditer(r"^- `[A-Z/]+ (/api/v1[^`]*)`", section, re.M)}


def _app_paths() -> set[str]:
    # `app.routes` alone reports ~19 entries: this app defers `include_router`
    # into placeholders that are only flattened at startup. `iter_routes`
    # unwraps them, which is what the page-walk suites already rely on.
    app = create_app()
    return {path for path, _methods in iter_routes(app.routes) if path.startswith("/api/v1")}


def test_spec_documents_every_api_route() -> None:
    missing = sorted(_app_paths() - _spec_paths())
    assert not missing, (
        f"docs/04-api-spec.md is missing {len(missing)} live route(s): {missing}. "
        "Regenerate section 5 from the route table."
    )


def test_spec_documents_no_phantom_routes() -> None:
    phantom = sorted(_spec_paths() - _app_paths())
    assert not phantom, (
        f"docs/04-api-spec.md documents {len(phantom)} route(s) that do not exist: "
        f"{phantom}. Remove them or implement them."
    )
