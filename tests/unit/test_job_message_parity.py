"""The server table and real core formatter use the same labels and messages."""

import json
import shutil
import subprocess
from pathlib import Path

from app.i18n.job_messages import METADATA, label, message


def test_server_and_real_javascript_job_wording_agree():
    node = shutil.which("node")
    assert node, "Node is required by the frontend quality gates"
    source = (
        (Path(__file__).parents[2] / "src/app/templates/static/js/_parts/core/01-job-messages.js")
        .read_text(encoding="utf-8")
        .replace("__GP_JOB_LABELS__", json.dumps(METADATA["labels"]))
    )
    tokens = {
        "Synced": "SYNC",
        "issues": "ISSUES",
        "names": "NAMES",
        "Updated": "UPDATE",
        "Data already up to date": "CURRENT",
    }
    samples = [
        "",
        "Data already up to date",
        "Synced 1 issue, 2 MRs, 3 MR notes, 4 issue notes, 5 pipelines",
        "Enriched 1 name, 2 emails",
        "Updated: title, assignee",
        "Unknown raw message",
    ]
    types = [
        *METADATA["labels"],
        "manual:full_sync",
        "_incremental_project_refresh",
        "_custom_worker_job",
        "unrecognised_task",
    ]
    script = (
        "const GP={};const words="
        + json.dumps(tokens)
        + ";const _translateUiText=s=>words[s]||s;\n"
        + source
        + "\nconsole.log(JSON.stringify(["
        + json.dumps(samples)
        + ".map(GP.formatJobMessage),"
        + json.dumps(types)
        + ".map(GP.jobTypeLabel)]));"
    )
    result = subprocess.run([node, "-e", script], capture_output=True, text=True, check=True)  # noqa: S603 - local source and fixed test input

    def t(value):
        return tokens.get(value, value)

    assert json.loads(result.stdout) == [
        [message(value, t) for value in samples],
        [label(value, t) for value in types],
    ]
