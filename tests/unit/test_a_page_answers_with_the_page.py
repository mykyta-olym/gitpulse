"""Dashboard GET routes return complete pages even with fragment-request headers.

Support category, form and ticket pages must retain their own response shape."""

from __future__ import annotations

from pathlib import Path

APP = Path(__file__).resolve().parents[2] / "src" / "app"


def test_no_route_answers_a_content_only_header() -> None:
    sources = [
        p
        for p in APP.rglob("*")
        if p.is_file() and p.suffix in {".py", ".html", ".js"} and "vendor" not in p.parts
    ]
    offenders = sorted(
        p.relative_to(APP).as_posix()
        for p in sources
        if "HX-Content-Only" in p.read_text(encoding="utf-8")
    )
    assert not offenders, f"a fragment branch for HX-Content-Only is back: {offenders}"
