"""Generate the global navigation from the content tree, per language.

Hand-writing it is how dead entries get in: the file and the pages drift
independently and nothing checks them against each other. Walking the tree means
every entry has a page behind it by construction.

Shape is theirs: title / url / submenu, URLs relative to the root with a
trailing slash and no leading one. URLs come from the DEFAULT language's tree so
they are the same in every language - only the titles are translated - which is
what `data/<lang>/page-metadata.json` and the sidebar's active-trail matching
both assume.

Run from anywhere:  python scripts/gen_docs_nav.py
"""

from __future__ import annotations

import re
from pathlib import Path

DOCS = Path(__file__).resolve().parent.parent / "docs-site"

# language code -> its content directory, mirroring config/_default/hugo.yaml.
# The first entry is the default language and supplies the URLs.
LANGUAGES = {
    "sk": DOCS / "content",
    "en": DOCS / "content-en",
}

# Order the sections the way a reader meets them, not alphabetically.
ORDER = [
    "uvod",
    "ucitelia",
    "studenti",
    "vyvojari",
    "operatori",
    "gitlab",
    "api",
    "bezpecnost",
    "diplomovka",
    # A top-level PAGE, not a section - see `main`. It had no way into this
    # list before, so the changelog was published on every release and linked
    # from nowhere in the site.
    "changelog",
    "pravne",
]

HEADER = [
    "# Global navigation for the GitPulse documentation.",
    "# GENERATED per language from that language's content by scripts/gen_docs_nav.py",
    "# NOTE: no commas in these comments - Hugo unmarshal guesses the format",
    "# from the content and a comma makes it read this YAML as CSV.",
    "",
]


def title_of(path: Path, fallback: Path | None = None) -> str:
    """The page's nav label, falling back to the default language's.

    `nav_title` wins over `title`: a section heading ("Príručka pre učiteľov")
    is not a nav label, and the subheader is one row of section names.
    """
    for candidate in (path, fallback):
        if candidate is None or not candidate.exists():
            continue
        text = candidate.read_text(encoding="utf-8")
        for key in ("nav_title", "title"):
            m = re.search(rf'^{key}:\s*"?(.+?)"?\s*$', text, re.M)
            if m:
                return m.group(1)
    return path.stem


def weight_of(child: Path) -> int:
    """The `weight` front-matter of a child (its `_index.md` for a directory).

    Files sort by filename by default, but a section whose pages are numbered in
    their titles - `1. Úvod`, `2. Analýza` - needs an explicit order, because the
    slugs (uvod, analyza) do not sort into 1, 2, 3. A page with no weight sorts
    after the weighted ones, keeping alphabetical order everywhere else.
    """
    source = child / "_index.md" if child.is_dir() else child
    if source.exists():
        m = re.search(r"^weight:\s*(-?\d+)\s*$", source.read_text(encoding="utf-8"), re.M)
        if m:
            return int(m.group(1))
    return 10_000


def entries(directory: Path, translated: Path, prefix: str, indent: int) -> list[str]:
    """Render `directory`'s children, titled from `translated` where present.

    `directory` is the DEFAULT language's tree - it decides which entries exist
    and what their URLs are - and `translated` is the same place in the language
    being written, which supplies the titles.

    Ordered by `weight` then filename: a numbered section states its order in
    front matter, everything else stays alphabetical.
    """
    pad = " " * indent
    out: list[str] = []
    for child in sorted(directory.iterdir(), key=lambda c: (weight_of(c), c.name)):
        if child.is_dir():
            index = child / "_index.md"
            if not index.exists():
                continue
            out.append(f"{pad}- title: {title_of(translated / child.name / '_index.md', index)}")
            out.append(f"{pad}  url: '{prefix}{child.name}/'")
            sub = entries(child, translated / child.name, f"{prefix}{child.name}/", indent + 4)
            if sub:
                out.append(f"{pad}  submenu:")
                out.extend(sub)
        elif child.suffix == ".md" and child.name != "_index.md":
            out.append(f"{pad}- title: {title_of(translated / child.name, child)}")
            out.append(f"{pad}  url: '{prefix}{child.stem}/'")
    return out


def main() -> None:
    default_lang, default_root = next(iter(LANGUAGES.items()))
    for lang, root in LANGUAGES.items():
        lines = list(HEADER)
        for name in ORDER:
            section = default_root / name
            index = section / "_index.md"
            if index.exists():
                lines.append(f"- title: {title_of(root / name / '_index.md', index)}")
                lines.append(f"  url: '{name}/'")
                sub = entries(section, root / name, f"{name}/", 4)
                if sub:
                    lines.append("  submenu:")
                    lines.extend(sub)
                continue
            # A top-level page with no section of its own. `entries` already
            # handles these INSIDE a section; the top level only ever looked
            # for directories, which is why `changelog.md` never appeared.
            page = default_root / f"{name}.md"
            if page.exists():
                lines.append(f"- title: {title_of(root / f'{name}.md', page)}")
                lines.append(f"  url: '{name}/'")

        out = DOCS / "data" / lang / "navigation.yaml"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(("\n".join(lines) + "\n").encode("utf-8"))
        count = sum(1 for x in lines if x.lstrip().startswith("- title:"))
        note = " (default: supplies the URLs)" if lang == default_lang else ""
        print(f"{out.relative_to(DOCS)}: {count} entries{note}")


if __name__ == "__main__":
    main()
