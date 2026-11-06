"""Report CSS classes that nothing appears to render.

Advisory only - it prints candidates, it never edits. Read the caveats before
acting on the output, because a naive version of this check was wrong four
separate times, each time in a way that would have deleted live styles:

1. Vendor libraries apply their own classes at runtime. `htmx-indicator`,
   `htmx-request` and `tippy-box` are configured inside the bundled libraries,
   so the vendor directory has to be part of the haystack.

2. Class names are assembled at runtime. `'health-component-badge ' +
   'health-component-badge--' + status` never contains the final class as a
   literal, so any quoted string that is concatenated or interpolated
   contributes its LAST token as a live prefix. Matching only single-token
   prefixes misses exactly this case.

3. Markup is emitted from PYTHON, not just templates and scripts. The
   `render_gl_description` filter writes `<a class="gl-ref gl-ref--issue">`
   from `app/i18n`, so `src/app/**/*.py` must be scanned too. This one nearly
   cost the entire `gl-ref` family.

4. Substring matches lie. `.severity-label` looked used because
   `finding-severity-label` exists, and `teaching-notes` looked used because a
   JS *comment* mentions it. Whole-selector comparison is the only safe basis
   for removal.

Utility classes (`mt-6`, `px-0`, `grid-cols-*`) will always appear here.
Being currently unused is the normal state of a utility library; removing
them is a design decision, not dead-code cleanup.

Usage:  python scripts/dead_css_report.py
"""

from __future__ import annotations

import collections
import re
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_APP = _ROOT / "src" / "app"
_TEMPLATES = _APP / "templates"
_CSS = _TEMPLATES / "static" / "css"

# Third-party stylesheet: its classes belong to the vendored libraries.
_SKIP_CSS = {"vendor.css"}

_CLASS_IN_SELECTOR = re.compile(r"\.(-?[_a-zA-Z][_a-zA-Z0-9-]{2,})")
_RULE_HEAD = re.compile(r"^([^{}@]+)\{", re.M)
_COMMENT = re.compile(r"/\*.*?\*/", re.S)

# A quoted string immediately followed by concatenation or interpolation.
_DYNAMIC = (
    r"""['"`]([^'"`\n]*?)['"`]\s*\+""",  # 'prefix-' + value
    r"""['"`]([^'"`\n]*?)\$\{""",  # `prefix-${value}`
    r"""([^\s'"=<>]*?)\{\{""",  # class="prefix-{{ value }}"
    r"""['"]([^'"\n]*?)['"]\s*~""",  # 'prefix-' ~ value
)


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def _haystack() -> str:
    """Everything that can put a class into the DOM."""
    parts: list[str] = [_read(p) for p in _TEMPLATES.rglob("*.html")]
    # Sources AND vendor bundles - see caveat 1.
    parts += [
        _read(p)
        for p in (_TEMPLATES / "static").rglob("*.js")
        if p.is_file() and "bundle" not in p.name
    ]
    # Python renders markup too - see caveat 3.
    parts += [_read(p) for p in _APP.rglob("*.py")]
    return "\n".join(parts)


def _dynamic_prefixes(hay: str) -> set[str]:
    """Prefixes used to build class names at runtime - see caveat 2."""
    found: set[str] = set()
    for pattern in _DYNAMIC:
        for match in re.finditer(pattern, hay):
            tokens = match.group(1).split()
            if tokens and re.fullmatch(r"[a-zA-Z][\w-]*-{1,2}", tokens[-1]):
                found.add(tokens[-1])
    return found


def _declared() -> dict[str, set[str]]:
    declared: dict[str, set[str]] = collections.defaultdict(set)
    for path in sorted(_CSS.rglob("*.css")):
        if ".min." in path.name or "bundle" in path.name or path.name in _SKIP_CSS:
            continue
        text = _COMMENT.sub("", _read(path))
        for rule in _RULE_HEAD.finditer(text):
            for name in _CLASS_IN_SELECTOR.findall(rule.group(1)):
                declared[name].add(path.name)
    return declared


def main() -> int:
    hay = _haystack()
    prefixes = _dynamic_prefixes(hay)
    declared = _declared()

    candidates = {
        name: files
        for name, files in declared.items()
        if name not in hay and not any(name.startswith(p) for p in prefixes)
    }

    print(f"declared classes : {len(declared)}")
    print(f"runtime prefixes : {len(prefixes)}")
    print(f"candidates       : {len(candidates)}\n")
    for name, files in sorted(candidates.items()):
        print(f"  {name:34} {', '.join(sorted(files))}")

    print(
        "\nAdvisory only. Confirm each one by hand before deleting, and remove"
        "\nwhole rules by exact selector - a substring match has been wrong here"
        "\nbefore. See this file's docstring."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
