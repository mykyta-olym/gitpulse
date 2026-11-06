"""System health and monitoring refreshes delegate busy state to GP.refreshRegion.

Both cards render on the server from the first frame, so there is no initial
placeholder loader to strand. Explicit refreshes go through `GP.refreshRegion`,
which clears button busy state and `.is-refreshing` in `finally` on both
success and failure while preserving the existing server-rendered content.
"""

from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
BOOT = REPO / "src/app/templates/static/js/_parts/admin-system/30-maintenance-boot.js"
STATES = REPO / "src/app/templates/static/js/_parts/core/22-content-states.js"


def _fn_body(src: str, header: str, next_marker: str) -> str:
    start = src.index(header)
    return src[start : src.index(next_marker, start)]


def test_health_and_monitoring_refreshes_both_delegate_to_refresh_region() -> None:
    src = BOOT.read_text(encoding="utf-8")
    health_body = _fn_body(
        src,
        "async function checkSystemHealth(arg)",
        "async function _fetchMonitoringPartial(fresh)",
    )
    mon_body = _fn_body(
        src,
        "async function _fetchMonitoringPartial(fresh)",
        "/* -- Clear Cache",
    )
    assert "GP.refreshRegion({" in health_body
    assert "GP.refreshRegion({" in mon_body
    assert "resp.status === 503" in mon_body, (
        "monitoring returns a 503 HTML partial when Prometheus is unreachable; "
        "throwing raw HTML would show markup in the error toast"
    )


def test_refresh_region_clears_busy_and_dimming_in_finally() -> None:
    states = STATES.read_text(encoding="utf-8")
    start = states.index("async function refreshRegion(")
    body = states[start:]
    finally_branch = body[body.index("} finally {") :]
    assert "is-refreshing" in finally_branch
    assert "setButtonLoading(button, false)" in finally_branch
