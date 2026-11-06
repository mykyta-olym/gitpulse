"""Shared job wording for server-rendered rows and the core bundle's job bar."""

import json
import re
from collections.abc import Callable
from pathlib import Path

METADATA: dict[str, dict[str, str]] = json.loads(
    Path(__file__).with_suffix(".json").read_text(encoding="utf-8")
)


def label(value: str, t: Callable[[str], str]) -> str:
    if value in METADATA["labels"]:
        return t(METADATA["labels"][value])
    bare = value.split(":")[-1].replace("_", " ").strip()
    if not bare:
        return value
    pretty = bare[0].upper() + bare[1:]
    return t(pretty)


def message(value: str, t: Callable[[str], str]) -> str:
    """Mirror GP.formatJobMessage for the persisted worker message contract."""
    if not value or t(value) != value:
        return t(value) if value else ""
    sync = re.fullmatch(
        r"Synced (\d+) issues?, (\d+) MRs?, (\d+) MR notes?, (\d+) issue notes?, (\d+) pipelines?",
        value,
    )
    if sync:
        return (
            t("Synced")
            + " "
            + ", ".join(
                f"{count} {t(noun)}"
                for count, noun in zip(
                    sync.groups(),
                    ("issues", "MRs", "MR notes", "issue notes", "pipelines"),
                    strict=True,
                )
            )
        )
    enrich = re.fullmatch(r"Enriched (\d+) names?, (\d+) emails?", value)
    if enrich:
        return f"{t('Enriched')} {enrich[1]} {t('names')}, {enrich[2]} {t('emails')}"
    if value.startswith("Updated: "):
        return t("Updated") + ": " + value[9:]
    return value
