"""Enforce that route modules keep DTOs in app.schemas.* files."""

import ast
from pathlib import Path


def _is_basemodel_subclass(node: ast.ClassDef) -> bool:
    for base in node.bases:
        if isinstance(base, ast.Name) and base.id == "BaseModel":
            return True
        if isinstance(base, ast.Attribute) and base.attr == "BaseModel":
            return True
    return False


def test_api_modules_do_not_define_pydantic_schemas_inline() -> None:
    api_dir = Path("src/app/api")
    excluded = {"errors.py", "exception_handlers.py", "contracts.py"}
    offenders: list[str] = []

    for path in sorted(api_dir.glob("*.py")):
        if path.name in excluded:
            continue

        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and _is_basemodel_subclass(node):
                offenders.append(f"{path}:{node.name}")

    assert offenders == [], (
        "Pydantic schemas must live in app.schemas.*, not in router modules: "
        + ", ".join(offenders)
    )
