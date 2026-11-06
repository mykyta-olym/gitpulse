---
title: "Master's thesis"
nav_title: "Thesis"
description: "Overview of the master's thesis following the current text in the thesis repository"
---
{{< details >}}
- For: Thesis reader
- Requires: Nothing
{{< /details >}}
**Topic:** Tools for Supporting DevOps Fundamentals Teaching<br />
**Author:** Bc.&nbsp;Mykyta Olym<br />
**Supervisor:** Ing.&nbsp;Sergej Chodarev,&nbsp;PhD.<br />
**Study programme:** Informatics<br />
**Current stage:** 4th interim submission, 1 Nov 2026 (implementation and evaluation methods)

---

## Abstract

Teachers of Fundamentals of Software Engineering and Fundamentals of DevOps grade
the way a student works on the team project, but the evidence is spread across
GitLab issues, branches, merge requests, review threads, commits and pipelines.
The thesis turns both assignments into thirteen questions a program can answer and
states for each what it cannot tell. It compares existing tools and examines which
data a GitLab webhook carries, which must be fetched through the REST API and which
are not available at all. On that basis it builds GitPulse, a web platform driven
by GitLab events, with an optional classroom assistant. The last part describes how
the solution will be evaluated with teachers and students.

**Keywords:** DevOps, GitPulse, GitLab, webhooks, process assessment, code review, software engineering education

---

## Contents

  - [1. Introduction](./uvod/) - problem, motivation and task formulation.
  - [2. Analysis of the team assignments](./analyza/) - course requirements and checks R01 to R13.
  - [3. Existing tools](./nastroje/) - Artemis, GitHub Classroom, GitLab analytics, Danger and SonarQube.
  - [4. Getting data from GitLab](./preskumanie/) - webhooks, the REST API and the limits of interpretation.
  - [5. Design of the GitPulse platform](./navrh/) - scenarios, architecture, check scoring and the assistant.
  - [6. Implementation](./realizacia/) - technologies, main parts, a check walkthrough and quality.
  - [7. Evaluation methods](./vyhodnotenie/) - what will be measured, how and with whom.
  - [8. Conclusion](./zaver/) - contributions, goals met and next steps.

---

{{< alert type="note" >}}
**Source of truth.** This section is a short guide to the current text of the thesis. The full text is the LaTeX source in the [`dp.mykyta.olym/thesis`](https://gitlab.example.com/kpi-zp/2027/dp.mykyta.olym/thesis) repository. Where they differ, the LaTeX source wins.
{{< /alert >}}
