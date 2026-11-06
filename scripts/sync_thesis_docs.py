#!/usr/bin/env python3
"""Sync the Slovak thesis LaTeX chapters into the MkDocs thesis section.

The authoritative thesis text lives in a separate LaTeX repository. This script
keeps the public docs-site "Diplomovka" section from drifting by converting the
current Slovak chapter sources to Markdown with a small preprocessing pass for
project-specific LaTeX macros.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS_DIPLOMOVKA = ROOT / "docs-site" / "content" / "diplomovka"
DEFAULT_THESIS_REPO = Path(r"C:\thesis")


@dataclass(frozen=True)
class Chapter:
    source: str
    slug: str
    number: int
    title: str
    description: str
    tags: tuple[str, ...]


CHAPTERS = (
    Chapter(
        "01-introduction.tex",
        "uvod",
        1,
        "Úvod",
        "Motivácia, problém a formulácia úlohy",
        ("diplomovka", "uvod"),
    ),
    Chapter(
        "02-analysis.tex",
        "analyza",
        2,
        "Analýza existujúcich riešení",
        "DevOps kompetencie, výučba a existujúce hodnotiace nástroje",
        ("diplomovka", "analyza"),
    ),
    Chapter(
        "03-exploration.tex",
        "preskumanie",
        3,
        "Preskúmanie možností riešenia",
        "Empirické overenie GitLab udalostí, REST API a existujúcich nástrojov",
        ("diplomovka", "preskumanie"),
    ),
    Chapter(
        "04-design.tex",
        "navrh",
        4,
        "Návrh riešenia",
        "Požiadavky, architektúra, hodnotiaci mechanizmus a technologický zásobník GitPulse",
        ("diplomovka", "navrh"),
    ),
    Chapter(
        "09-summary.tex",
        "zaver",
        5,
        "Záver",
        "Zhrnutie prínosov práce a ďalšieho postupu",
        ("diplomovka", "zaver"),
    ),
)


ACRONYMS = {
    "api": "API",
    "cicd": "CI/CD",
    "http": "HTTP",
    "json": "JSON",
    "oauth": "OAuth",
    "orm": "ORM",
    "rest": "REST",
}

GLOSSARY = {
    "cicd-pipeline": "CI/CD pipeline",
    "code-review": "revízia kódu",
    "devops": "DevOps",
    "merge-request": "žiadosť o zlúčenie",
    "webhook": "webhook",
}

REFS = {
    "ch:analysis": "2",
    "subsec:auto-grading": "2.3.1",
    "subsec:compliance-tools": "2.3.3",
    "tab:comparison": "2.1",
    "tab:webhook-coverage": "3.1",
    "fig:gp-architecture": "4.1",
    "fig:gp-eventflow": "4.2",
}

ARCHITECTURE_PLACEHOLDER = "GP_ARCHITECTURE_DIAGRAM_PLACEHOLDER"
EVENTFLOW_PLACEHOLDER = "GP_EVENTFLOW_DIAGRAM_PLACEHOLDER"

DESIGN_ARCHITECTURE_DIAGRAM = """\
```mermaid
flowchart LR
  GL[GitLab TUKE] -->|webhook| Caddy[Caddy / TLS]
  Caddy --> API[FastAPI]
  API -->|/metrics| Obs[Prometheus / Grafana]
  API -->|queue| Redis[Redis + RQ]
  Redis --> Worker[Worker]
  Worker --> DB[(PostgreSQL)]
  API --> DB
  Worker -. REST API .-> GL
```
"""

DESIGN_EVENTFLOW_DIAGRAM = """\
```mermaid
flowchart LR
  Recv[1. Príjem webhooku<br/>overenie tokenu]
  Dedup[2. Odstránenie duplicít]
  Queue[3. Zaradenie do frontu]
  Enrich[4. Doplnenie cez REST API]
  Eval[5. Vyhodnotenie pravidiel]
  Store[6. Uloženie a stav Quality Gates]

  Recv --> Dedup --> Queue --> Enrich --> Eval --> Store
```
"""


def _replace_figure(tex: str, label: str, diagram: str) -> str:
    pattern = re.compile(
        rf"\\begin\{{figure\}}(?:.|\n)*?\\label\{{{re.escape(label)}\}}(?:.|\n)*?\\end\{{figure\}}",
        re.MULTILINE,
    )
    return pattern.sub("\n\n" + diagram + "\n", tex)


def _preprocess_tex(tex: str) -> str:
    tex = re.sub(r"(?<!\\)%[^\r\n]*", "", tex)
    tex = _replace_figure(tex, "fig:gp-architecture", ARCHITECTURE_PLACEHOLDER)
    tex = _replace_figure(tex, "fig:gp-eventflow", EVENTFLOW_PLACEHOLDER)
    tex = re.sub(r"\\glslink\{[^}]+\}\{([^}]+)\}", r"\1", tex)
    tex = re.sub(
        r"\\acr(?:short|long|full)\{([^}]+)\}",
        lambda m: ACRONYMS.get(m.group(1).lower(), m.group(1).upper()),
        tex,
    )
    tex = re.sub(
        r"\\gls\{([^}]+)\}",
        lambda m: GLOSSARY.get(m.group(1), m.group(1).replace("-", " ")),
        tex,
    )
    tex = re.sub(r"\\ref\{([^}]+)\}", lambda m: REFS.get(m.group(1), m.group(1)), tex)
    tex = re.sub(r"\\label\{[^}]+\}", "", tex)
    tex = re.sub(r"\\rotatebox\{[^}]+\}\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}", r"\1", tex)
    tex = tex.replace(r"\checkmark", "✓")
    tex = tex.replace(r"$\sim$", "≈")
    tex = tex.replace(r"\(\sim\)", "≈")
    tex = tex.replace(r"\sim", "≈")
    tex = tex.replace(r"\midrule", r"\hline")
    return tex


def _run_pandoc(tex: str, thesis_repo: Path) -> str:
    bibliography = thesis_repo / "bibliography.bib"
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp = Path(tmp_dir) / "chapter.tex"
        tmp.write_text(tex, encoding="utf-8")
        cmd = [
            "pandoc",
            "--from",
            "latex",
            "--to",
            "gfm",
            "--wrap=none",
            "--bibliography",
            str(bibliography),
            "--citeproc",
            str(tmp),
        ]
        return subprocess.check_output(cmd, text=True, encoding="utf-8")  # noqa: S603


def _renumber_headings(markdown: str, chapter: Chapter) -> str:
    section = 0
    subsection = 0
    lines: list[str] = []
    for line in markdown.splitlines():
        if line.startswith("# "):
            lines.append(f"# {chapter.number}. {chapter.title}")
            continue
        if line.startswith("## "):
            section += 1
            subsection = 0
            lines.append(f"## {chapter.number}.{section} {line[3:]}")
            continue
        if line.startswith("### "):
            subsection += 1
            lines.append(f"### {chapter.number}.{section}.{subsection} {line[4:]}")
            continue
        lines.append(line)
    return "\n".join(lines).strip() + "\n"


def _front_matter(chapter: Chapter) -> str:
    tags = "\n".join(f"  - {tag}" for tag in chapter.tags)
    return (
        "---\n"
        f"title: {chapter.number}. {chapter.title}\n"
        f"description: {chapter.description}\n"
        f"tags:\n{tags}\n"
        "---\n\n"
    )


def _postprocess(markdown: str, chapter: Chapter) -> str:
    markdown = markdown.replace(ARCHITECTURE_PLACEHOLDER, DESIGN_ARCHITECTURE_DIAGRAM.rstrip())
    markdown = markdown.replace(EVENTFLOW_PLACEHOLDER, DESIGN_EVENTFLOW_DIAGRAM.rstrip())
    markdown = markdown.replace("\u00a0", " ")
    markdown = markdown.replace("\u00ad", "")
    markdown = markdown.replace("\\_", "_")
    markdown = markdown.replace("$`≈`$", "≈")
    markdown = markdown.replace("$`✓`$", "✓")
    markdown = re.sub(r"\n{3,}", "\n\n", markdown)
    markdown = _renumber_headings(markdown, chapter)
    return _front_matter(chapter) + markdown


def _strip_tex_inline(value: str) -> str:
    value = _preprocess_tex(value)
    value = re.sub(r"\\emph\{([^}]+)\}", r"\1", value)
    value = re.sub(r"\\textbf\{([^}]+)\}", r"\1", value)
    value = value.replace("---", "-")
    value = value.replace("~", " ")
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def _extract_two_args(tex: str, command: str) -> tuple[str, str]:
    marker = "\\" + command
    start = tex.index(marker) + len(marker)
    args: list[str] = []
    idx = start
    for _ in range(2):
        while idx < len(tex) and tex[idx].isspace():
            idx += 1
        if idx >= len(tex) or tex[idx] != "{":
            raise ValueError(f"Expected braced argument for \\{command}")
        depth = 0
        arg_start = idx + 1
        while idx < len(tex):
            char = tex[idx]
            if char == "{" and (idx == 0 or tex[idx - 1] != "\\"):
                depth += 1
            elif char == "}" and (idx == 0 or tex[idx - 1] != "\\"):
                depth -= 1
                if depth == 0:
                    args.append(tex[arg_start:idx])
                    idx += 1
                    break
            idx += 1
    return args[0], args[1]


def _build_index(thesis_repo: Path, *, english: bool) -> str:
    metadata = (thesis_repo / "metadata.tex").read_text(encoding="utf-8")
    title_en, title_sk = _extract_two_args(metadata, "title")
    keywords_en, keywords_sk = _extract_two_args(metadata, "keywords")
    abstract_en, abstract_sk = _extract_two_args(metadata, "abstract")
    if english:
        title = "Master's Thesis"
        description = "Master's thesis text - mirror of the source in the thesis repository"
        heading = "Master's Thesis"
        thesis_title = _strip_tex_inline(title_en)
        abstract = _strip_tex_inline(abstract_en)
        keywords = _strip_tex_inline(keywords_en)
        cards = (
            (
                "text-box-outline",
                "Introduction",
                "Problem statement, motivation and task formulation.",
                "uvod.md",
            ),
            (
                "magnify",
                "Analysis of Existing Solutions",
                "DevOps as a discipline, the current teaching context and existing assessment tools.",
                "analyza.md",
            ),
            (
                "flask-outline",
                "Exploring Solution Options",
                "Empirical verification of GitLab events, REST API coverage and existing tools.",
                "preskumanie.md",
            ),
            (
                "source-branch",
                "Solution Design",
                "GitPulse requirements, event-driven architecture, quality gates and technology stack.",
                "navrh.md",
            ),
            (
                "flag-checkered",
                "Conclusion",
                "Summary of thesis contributions and remaining work.",
                "zaver.md",
            ),
        )
        source_note = (
            "The text in this section is derived from the LaTeX source of the thesis in the\n"
            "[`dp.mykyta.olym/thesis`](https://gitlab.example.com/kpi-zp/2027/dp.mykyta.olym/thesis) repository.\n"
            "In case of conflict the LaTeX source takes precedence."
        )
        tags = "  - thesis\n  - research"
        topic_label = "Topic"
        author_label = "Author"
        supervisor_label = "Supervisor"
        programme_label = "Study programme"
        submission_label = "Expected submission"
        abstract_label = "Abstract"
        keywords_label = "Keywords"
        contents_label = "Contents"
        read_label = "Read"
        source_label = "Source of truth"
        submission = "31 Jan 2027"
    else:
        title = "Diplomová práca"
        description = "Text diplomovej práce - zrkadlo zdroja v thesis repozitári"
        heading = "Diplomová práca"
        thesis_title = _strip_tex_inline(title_sk)
        abstract = _strip_tex_inline(abstract_sk)
        keywords = _strip_tex_inline(keywords_sk)
        cards = (
            (
                "text-box-outline",
                "Úvod",
                "Vymedzenie problému, motivácia a formulácia úlohy.",
                "uvod.md",
            ),
            (
                "magnify",
                "Analýza existujúcich riešení",
                "DevOps ako disciplína, súčasný stav výučby a prehľad existujúcich nástrojov.",
                "analyza.md",
            ),
            (
                "flask-outline",
                "Preskúmanie možností riešenia",
                "Empirické overenie pokrytia kontrolného zoznamu udalosťami GitLab a existujúcimi nástrojmi.",
                "preskumanie.md",
            ),
            (
                "source-branch",
                "Návrh riešenia",
                "Požiadavky, architektúra, Quality Gates a technologický zásobník platformy GitPulse.",
                "navrh.md",
            ),
            (
                "flag-checkered",
                "Záver",
                "Zhrnutie prínosov práce a ďalšieho postupu.",
                "zaver.md",
            ),
        )
        source_note = (
            "Text tejto sekcie je odvodený z LaTeX zdroja diplomovej práce v repozitári\n"
            "[`dp.mykyta.olym/thesis`](https://gitlab.example.com/kpi-zp/2027/dp.mykyta.olym/thesis).\n"
            "Pri rozdiele má prednosť LaTeX zdroj."
        )
        tags = "  - diplomovka\n  - vyskum"
        topic_label = "Téma"
        author_label = "Autor"
        supervisor_label = "Vedúci práce"
        programme_label = "Študijný program"
        submission_label = "Predpokladané odovzdanie"
        abstract_label = "Abstrakt"
        keywords_label = "Kľúčové slová"
        contents_label = "Obsah práce"
        read_label = "Čítať"
        source_label = "Zdroj pravdy"
        submission = "31. 1. 2027"

    card_blocks = []
    for icon, card_title, text, href in cards:
        card_blocks.append(
            f"-   :material-{icon}: **{card_title}**\n\n"
            "    ---\n\n"
            f"    {text}\n\n"
            f"    [{read_label}]({href})"
        )

    return (
        "---\n"
        f"title: {title}\n"
        f"description: {description}\n"
        "tags:\n"
        f"{tags}\n"
        "---\n\n"
        f"# {heading}\n\n"
        f"**{topic_label}:** {thesis_title}<br>\n"
        f"**{author_label}:** Bc.&nbsp;Mykyta Olym<br>\n"
        f"**{supervisor_label}:** Ing.&nbsp;Sergej Chodarev,&nbsp;PhD.<br>\n"
        f"**{programme_label}:** Informatika<br>\n"
        f"**{submission_label}:** {submission}\n\n"
        "---\n\n"
        f"## {abstract_label}\n\n"
        f"{abstract}\n\n"
        f"**{keywords_label}:** {keywords}\n\n"
        "---\n\n"
        f"## {contents_label}\n\n"
        '<div class="grid cards" markdown>\n\n' + "\n\n".join(card_blocks) + "\n\n</div>\n\n"
        "---\n\n"
        f'!!! info "{source_label}"\n'
        + "\n".join(f"    {line}" for line in source_note.splitlines())
        + "\n"
    )


def sync(thesis_repo: Path) -> None:
    chapters_dir = thesis_repo / "chapters"
    if not chapters_dir.exists():
        raise FileNotFoundError(f"Missing thesis chapters directory: {chapters_dir}")
    DOCS_DIPLOMOVKA.mkdir(parents=True, exist_ok=True)

    for chapter in CHAPTERS:
        source = chapters_dir / chapter.source
        tex = _preprocess_tex(source.read_text(encoding="utf-8"))
        markdown = _run_pandoc(tex, thesis_repo)
        output = _postprocess(markdown, chapter)
        (DOCS_DIPLOMOVKA / f"{chapter.slug}.md").write_text(
            output,
            encoding="utf-8",
            newline="\n",
        )

    (DOCS_DIPLOMOVKA / "index.md").write_text(
        _build_index(thesis_repo, english=False),
        encoding="utf-8",
        newline="\n",
    )
    (DOCS_DIPLOMOVKA / "index.en.md").write_text(
        _build_index(thesis_repo, english=True),
        encoding="utf-8",
        newline="\n",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--thesis-repo",
        type=Path,
        default=DEFAULT_THESIS_REPO,
        help="Path to the local thesis repository (default: C:\\thesis)",
    )
    args = parser.parse_args()
    sync(args.thesis_repo.resolve())


if __name__ == "__main__":
    main()
