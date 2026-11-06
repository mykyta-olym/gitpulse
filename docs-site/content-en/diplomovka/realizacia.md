---
title: "6. Implementation"
weight: 6
description: "Technologies, import and sync, event processing, a check walkthrough and quality"
---
{{< details >}}
- For: Thesis reader
- Requires: Nothing
{{< /details >}}
GitPulse has run since July 2026 on the public instance
[gitpulse.kpi.fei.tuke.sk](https://gitpulse.kpi.fei.tuke.sk). It is written in
Python 3.12 on FastAPI, stores data in PostgreSQL 16 and uses Redis 7 as cache, RQ
job queue and live update channel. Pages are rendered on the server with Jinja2 and
completed in the browser by htmx, Alpine.js and Chart.js. Check scoring lives in the
`compliance` package, which knows nothing about the web or the queues. The code
layout is described in the [developer section](../../vyvojari/struktura/).

## 6.1 A check walkthrough

The teacher's main path has four steps. The screenshots come from a demonstration
course with made-up data, but the results were computed by the same check engine
that runs on real projects.

![Teacher dashboard](/docs/assets/thesis/gitpulse-01-prehlad.png)

*The dashboard with the term summary and items that need attention.*

![Course groups with traffic lights](/docs/assets/thesis/gitpulse-02-kurz.png)

*Course groups with average score and traffic light.*

![Group members](/docs/assets/thesis/gitpulse-03-skupina.png)

*Group members with score and the number of enabled checks passed.*

![Student detail](/docs/assets/thesis/gitpulse-04-student.png)

*A student's detail with the merge request progress and a link to GitLab.*

## 6.2 Quality and operations

As of 2 Nov 2026 the suite has 4,656 unit tests including 26 contract tests, and
173 integration tests run in CI against PostgreSQL and Redis. The assistant was
verified by a script against a local GitLab CE 19.4.2. Its first run exposed three
webhook defects that hand-written fixtures had hidden, and thirteen captured
deliveries became the new contract fixtures. Preparing the screenshots found three
more defects (a switched-off check shown as failed, an unnormalised score, a
student's progress counted for the whole group), fixed in 2026.11.2.post4.

CI checks style, types, static files and dependencies, scans for vulnerabilities,
runs the tests, builds the Docker image and publishes the documentation. Prometheus
metrics are shown in Grafana and eighteen alert rules email the administrator.
Operations are described in the [operators section](../../operatori/).
