"""Enforce use of shared error factories in API routers."""

from pathlib import Path


def test_api_routers_do_not_raise_http_exception_directly() -> None:
    api_dir = Path("src/app/api")
    excluded = {"errors.py", "exception_handlers.py"}

    offenders: list[str] = []
    for path in sorted(api_dir.glob("*.py")):
        if path.name in excluded:
            continue
        text = path.read_text(encoding="utf-8")
        if "raise HTTPException(" in text:
            offenders.append(str(path).replace("\\", "/"))

    assert offenders == [], f"Direct HTTPException raises found in: {', '.join(offenders)}"
