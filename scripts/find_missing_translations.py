"""Scan templates/JS for t(...) calls whose source string is missing from sk.json.

Usage:
    python scripts/find_missing_translations.py
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SK_PATH = ROOT / "src" / "app" / "i18n" / "catalogs" / "sk.json"

# Matches:  t('foo')   t("foo", ...)   t?.('foo')   {{ t('foo') }}   {{ t("foo", ...) }}
# and the JS aliases the page scripts use for the same catalogue: tx(...) in the
# tour engine, _t(...) in the standalone scripts, GP.t(...), _translateUiText(...).
# "Tour history cleared." shipped untranslated because only bare t( was scanned.
PAT = re.compile(
    r"""(?<![\w.])(?:t|tx|_t|GP\.t|_translateUiText)\s*\??\.?\s*\(\s*(['"])([^'"\\]+?)\1\s*[,)]""",
    re.VERBOSE,
)


def main() -> int:
    sk = json.loads(SK_PATH.read_text(encoding="utf-8"))
    scan_dir = ROOT / "src" / "app"
    missing: dict[str, list[str]] = {}
    seen = 0

    for path in scan_dir.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix not in {".js", ".html", ".jinja", ".jinja2"}:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for match in PAT.finditer(text):
            seen += 1
            key = match.group(2)
            if key in sk:
                continue
            rel = str(path.relative_to(ROOT)).replace("\\", "/")
            missing.setdefault(key, []).append(rel)

    reconfigure = getattr(sys.stdout, "reconfigure", None)
    if callable(reconfigure):
        reconfigure(encoding="utf-8")
    print(f"Scanned {seen} t(...) calls")
    print(f"Missing keys: {len(missing)}\n")
    for key in sorted(missing):
        files = sorted(set(missing[key]))[:3]
        print(f"  {key!r}")
        for f in files:
            print(f"    - {f}")
    return 0 if not missing else 1


if __name__ == "__main__":
    raise SystemExit(main())
