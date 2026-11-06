---
title: "Introduction"
nav_title: "Introduction"
description: "Introduction to GitPulse"
---
{{< details >}}
- For: Everyone
- Requires: Nothing
{{< /details >}}
GitPulse is a platform for transparent and scalable evaluation of team work in GitLab projects.

## Primary Goal

Replace manual, subjective grading with a measurable data-driven process:

- automated event collection
- consistent compliance rules
- auditable outputs for teachers

```mermaid
flowchart TB
    A["Student GitLab activity"] --> B["Webhook ingestion"]
    B --> C["Worker processing"]
    C --> D["Compliance checks (R01-R13)"]
    D --> E["Dashboard + data exports"]
    E --> F["More objective grading"]
```

## Target Audience

- teachers: metric interpretation and evaluation decisions
- developers: implementation, testing, release workflow
- operators: deployment, monitoring, incident response

## Next Steps

- [Project overview](prehlad.md)
- [Thesis goals](ciele.md)
- [System architecture](architektura.md)
