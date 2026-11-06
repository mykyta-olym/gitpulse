---
title: "Thesis goals"
description: "The sub-tasks of the thesis, their chapters and status"
---
{{< details >}}
- For: Everyone
- Requires: Nothing
{{< /details >}}
This page lists the sub-tasks of the master's thesis *Tools for Supporting DevOps
Fundamentals Teaching* as stated in the task formulation (Section 1.2 of the thesis)
and links the chapters that address them.

{{< alert type="note" >}}
**Source.** The authoritative source is the thesis text in the [`dp.mykyta.olym/thesis`](https://gitlab.example.com/kpi-zp/2027/dp.mykyta.olym/thesis) repository. A short overview of the chapters is in the [Thesis](../../diplomovka/) section.
{{< /alert >}}
## Sub-tasks

| # | Task | Chapter | Status |
|---|------|---------|--------|
| 1 | Analyse the team assignment requirements and separate conditions a program can check from those the teacher judges. | [2. Analysis of the team assignments](../../diplomovka/analyza/) | Done |
| 2 | Examine existing tools for automated assessment, repository analytics and change checking. | [3. Existing tools](../../diplomovka/nastroje/) | Done |
| 3 | Verify which data GitLab sends through webhooks and which must come from the REST API, and set the limits of interpreting them. | [4. Getting data from GitLab](../../diplomovka/preskumanie/) | Done |
| 4 | Design the architecture, data flow and security boundaries of a platform that does not touch student repositories. | [5. Design of the GitPulse platform](../../diplomovka/navrh/) | Done |
| 5 | Build a prototype with course import, synchronisation, configurable checks and overviews. | [6. Implementation](../../diplomovka/realizacia/) | Done, running on the public instance |
| 6 | Design an evaluation that separates technical correctness from pedagogical effect and prepare it with the target group. | [7. Evaluation methods](../../diplomovka/vyhodnotenie/) | Method ready, measurements in winter 2026/2027 and from February 2027 |

## Tasks and this documentation

| Task | Documentation section |
|------|-----------------------|
| 1 and 2 | [Project overview](../prehlad/), [Thesis](../../diplomovka/) |
| 3 | [GitLab integration](../../gitlab/) |
| 4 and 5 | [Architecture](../architektura/), [Developers](../../vyvojari/), [API](../../api/), [Classroom assistant](../../ucitelia/asistent/) |
| 6 | [Evaluation in teaching](../../ucitelia/pilot/), [Operators](../../operatori/) |

## Design principles

1. **Event-driven.** GitPulse receives GitLab webhooks and fetches details through
   the REST API. Nothing changes on the GitLab side and student repositories are only
   read; only the optional classroom assistant writes, under the course's own account.
2. **A student over a term.** Checks R01 to R13 follow a student's work across their
   merge requests, not a single change.
3. **The teacher decides.** A check result carries an explanation and a link to
   GitLab and is not a grade.
