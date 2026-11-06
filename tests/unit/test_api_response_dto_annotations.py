"""Enforce DTO-based return annotations for API route handlers."""

import ast
from pathlib import Path

_ROUTE_DECORATORS = {"get", "post", "put", "patch", "delete", "options", "head"}


def _is_router_decorator(decorator: ast.expr) -> bool:
    if not isinstance(decorator, ast.Call):
        return False
    func = decorator.func
    return isinstance(func, ast.Attribute) and func.attr in _ROUTE_DECORATORS


def test_api_route_handlers_do_not_use_dict_return_annotations() -> None:
    api_dir = Path("src/app/api")
    excluded = {"errors.py", "exception_handlers.py", "contracts.py"}
    offenders: list[str] = []

    for path in sorted(api_dir.glob("*.py")):
        if path.name in excluded:
            continue
        source = path.read_text(encoding="utf-8")
        assert "response_model=dict" not in source
        tree = ast.parse(source, filename=str(path))

        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if not any(_is_router_decorator(decorator) for decorator in node.decorator_list):
                continue
            if node.returns is None:
                continue
            annotation = ast.unparse(node.returns).replace(" ", "")
            if "dict[" in annotation or annotation.startswith("dict"):
                offenders.append(f"{path}:{node.name}:{annotation}")

    assert offenders == [], "Route handlers must use DTO return annotations: " + ", ".join(
        offenders
    )
