"""No two bundle modules may declare the same top-level name.

`core.bundle.js` is a plain concatenation, so every module that is not wrapped
in an IIFE shares one scope. Function declarations hoist, which means a
duplicate name is not a syntax error - whichever copy lands last silently wins
for *every* caller, including those in the module that defined the other one.

One module GROUP is wrapped in an IIFE by the builder itself rather than in
its own source (global-job-bar, see build_bundle.py), so this check has to
model that wrapping. Reading the sources alone reports collisions
that cannot happen - `_now` and `GP` both look duplicated but are not.

Most modules are IIFE-wrapped, so the sharper hazard is the `GP` namespace:
every module reaches the same object, and a second `GP.foo = ...` silently
replaces the first with no error and no warning. That is exactly how
`initGlFileUpload` came to be defined twice, with the cut-down copy in core
overwritten by components.js before anything could call it.
"""

from __future__ import annotations

import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, "scripts")

from build_bundle import JS_MODULES

_JS_ROOT = Path("src/app/templates/static/js")

# Top-level `function name(` - indentation means it is nested, and therefore
# already scoped.
_TOP_LEVEL_FN = re.compile(r"^(?:async\s+)?function\s+([A-Za-z_$][\w$]*)\s*\(", re.M)
_TOP_LEVEL_BINDING = re.compile(r"^(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=", re.M)


def _is_iife_wrapped(source: str) -> bool:
    """True when the whole module body sits inside an IIFE."""
    for line in source.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith(("//", "/*", "*")):
            continue
        return stripped.startswith(
            (";(function", "(function", ";(async function", "(async function")
        )
    return False


def _builder_wrapped_modules() -> set[str]:
    """Modules the builder itself encloses in an IIFE.

    Derived from build_bundle.py rather than hard-coded, so a change to the
    wrapping is noticed here instead of silently widening the check.
    """
    builder = Path("scripts/build_bundle.py").read_text(encoding="utf-8")
    opens = re.findall(r'mod == "([^"]+)":\n\s+content = ";\(function', builder)
    closes = re.findall(r'mod == "([^"]+)":\n\s+content = content \+ "\\n\}\)\(\);', builder)
    assert opens, "could not read the builder's IIFE open markers"
    assert closes, "could not read the builder's IIFE close markers"

    wrapped: set[str] = set()
    for start, end in zip(opens, closes, strict=True):
        i, j = JS_MODULES.index(start), JS_MODULES.index(end)
        wrapped.update(JS_MODULES[i : j + 1])
    return wrapped


def _shared_scope_names() -> dict[str, list[str]]:
    """Map top-level name -> modules declaring it, for shared-scope modules."""
    wrapped = _builder_wrapped_modules()
    names: dict[str, list[str]] = defaultdict(list)
    for module in JS_MODULES:
        path = _JS_ROOT / module
        if not path.exists() or module in wrapped:
            continue
        source = path.read_text(encoding="utf-8", errors="ignore")
        if _is_iife_wrapped(source):
            continue
        declared = set(_TOP_LEVEL_FN.findall(source)) | set(_TOP_LEVEL_BINDING.findall(source))
        for name in declared:
            names[name].append(module)
    return names


def test_the_builder_still_wraps_the_groups_this_check_assumes() -> None:
    wrapped = _builder_wrapped_modules()

    assert "_parts/global-job-bar/00-state-polling.js" in wrapped
    assert "_parts/global-job-bar/20-listeners-api.js" in wrapped
    # The tours left core for their own lazily loaded bundle.
    assert not any(m.startswith("_parts/tours/") for m in JS_MODULES)


def test_the_scan_sees_the_unwrapped_core_modules() -> None:
    """Guard the detector - if it silently found nothing the test is vacuous."""
    names = _shared_scope_names()

    assert names, "no top-level names found: the parser or JS_MODULES import broke"
    assert any("_parts/core/" in m for ms in names.values() for m in ms)


def test_no_two_unwrapped_modules_declare_the_same_top_level_name() -> None:
    collisions = {n: ms for n, ms in _shared_scope_names().items() if len(ms) > 1}

    assert not collisions, "top-level name collisions in core.bundle.js: " + "; ".join(
        f"{name} in {' + '.join(mods)}" for name, mods in sorted(collisions.items())
    )


_GP_ASSIGN = re.compile(r"^\s*GP\.([A-Za-z_$][\w$]*)\s*=(?!=)", re.M)


def _gp_assignments() -> dict[str, list[str]]:
    """Map `GP.<name>` -> modules assigning it."""
    owners: dict[str, list[str]] = defaultdict(list)
    for module in JS_MODULES:
        path = _JS_ROOT / module
        if not path.exists():
            continue
        source = path.read_text(encoding="utf-8", errors="ignore")
        for name in set(_GP_ASSIGN.findall(source)):
            owners[name].append(module)
    return owners


def test_the_gp_scan_is_not_vacuous() -> None:
    owners = _gp_assignments()

    assert len(owners) > 20, "GP namespace scan found almost nothing - parser broke"
    assert "reloadKeepScroll" in owners


def test_each_gp_export_has_exactly_one_owning_module() -> None:
    """A second `GP.foo = ...` overwrites the first silently - and a module that
    wraps an earlier module's export is an override, not a component: the
    behaviour belongs in the owning function."""
    clashes = {n: ms for n, ms in _gp_assignments().items() if len(set(ms)) > 1}

    assert not clashes, "GP exports defined by more than one module: " + "; ".join(
        f"GP.{name} in {' + '.join(sorted(set(mods)))}" for name, mods in sorted(clashes.items())
    )
