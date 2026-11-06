"""The READMEs state countable facts - keep them true.

Both READMEs had drifted into fiction: `README.sk.md` still advertised
`rq-scheduler` with 12 periodic jobs (there is no scheduler), 44 models across
48 migrations at head `047_bg_job_project_id` (it is 39 across 11 at `011`),
and both linked an `LLM_README.md` that does not exist. A reader cannot tell a
stale number from a current one, so pin the ones a machine can check.
"""

import json
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
READMES = ("README.md", "README.sk.md")


def _read(name: str) -> str:
    return (REPO_ROOT / name).read_text(encoding="utf-8")


def _model_class_count() -> int:
    total = 0
    for f in (REPO_ROOT / "src/app/models").glob("*.py"):
        total += len(re.findall(r"^class \w+\(", f.read_text(encoding="utf-8"), re.M))
    return total


def _migration_head() -> tuple[int, str]:
    files = sorted((REPO_ROOT / "alembic/versions").glob("*.py"))
    revs, downs = set(), set()
    for f in files:
        txt = f.read_text(encoding="utf-8")
        if m := re.search(r'revision(?::\s*str)?\s*=\s*["\']([^"\']+)', txt):
            revs.add(m.group(1))
        if m := re.search(r'down_revision(?::\s*[^=]+)?\s*=\s*["\']([^"\']+)', txt):
            downs.add(m.group(1))
    (head,) = revs - downs
    return len(files), head


@pytest.mark.parametrize("readme", READMES)
def test_readme_links_only_to_files_that_exist(readme: str) -> None:
    text = _read(readme)
    missing = []
    for target in re.findall(r"\[[^\]]+\]\(([^)#]+)\)", text):
        if target.startswith(("http://", "https://", "mailto:")):
            continue
        if not (REPO_ROOT / target).exists():
            missing.append(target)
    # Backtick-quoted paths in the documentation tables count too.
    for target in re.findall(r"`((?:docs|src|scripts|monitoring)/[\w./-]+\.\w+)`", text):
        if not (REPO_ROOT / target).exists():
            missing.append(target)
    assert not missing, f"{readme} points at files that do not exist: {sorted(set(missing))}"


@pytest.mark.parametrize("readme", READMES)
def test_readme_model_and_migration_counts(readme: str) -> None:
    text = _read(readme)
    models = _model_class_count()
    count, head = _migration_head()
    assert f"{models} ORM model" in text or f"{models} model classes" in text, (
        f"{readme} does not state the real model count ({models})"
    )
    assert head in text, f"{readme} does not name the real migration head ({head})"
    assert re.search(rf"{count} (migration|migračných)", text), (
        f"{readme} does not state the real migration count ({count})"
    )


@pytest.mark.parametrize("readme", READMES)
def test_readme_i18n_key_count(readme: str) -> None:
    catalog = (REPO_ROOT / "src/app/i18n/catalogs/sk.json").read_text(encoding="utf-8")
    keys = len(json.loads(catalog))
    # The README writes it with a thin space: "2 823 keys".
    pretty = f"{keys // 1000} {keys % 1000:03d}"
    assert pretty in _read(readme), f"{readme} should state {pretty} SK catalog keys"


@pytest.mark.parametrize("readme", READMES)
def test_readme_alert_rule_count(readme: str) -> None:
    rules = (REPO_ROOT / "monitoring/prometheus/alerts.yml").read_text(encoding="utf-8")
    count = rules.count("- alert:")
    assert re.search(rf"{count} alert", _read(readme)), f"{readme} should state {count} alert rules"


@pytest.mark.parametrize("readme", READMES)
def test_readme_does_not_promise_a_scheduler(readme: str) -> None:
    """There is no cron/rq-scheduler; every job is event- or action-driven."""
    text = _read(readme).lower()
    assert "rq-scheduler" not in text, (
        f"{readme} still advertises rq-scheduler - the worker runs with with_scheduler=False"
    )
