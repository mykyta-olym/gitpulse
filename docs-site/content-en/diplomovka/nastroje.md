---
title: "3. Existing tools"
weight: 3
description: "Assessment of tools for automated grading, analytics and change checking"
---
{{< details >}}
- For: Thesis reader
- Requires: Nothing
{{< /details >}}
For each tool the thesis asks whether it already solves the task, what is worth
taking over and whether it can be plugged in directly. It looks at whether the tool
works on an existing GitLab, follows an individual's process steps, shows the state
across the projects of a course, can be configured by the course rules and leads
from a result back to the original data.

| Tool | On GitLab | Process | Course | Config. | Detail |
|---|:---:|:---:|:---:|:---:|:---:|
| Artemis | ~ | ✓ | ✓ | ✓ | ✓ |
| GitHub Classroom | × | ~ | ✓ | ~ | ✓ |
| GitLab analytics | ✓ | ~ | × | × | ✓ |
| Danger | ✓ | ~ | × | ✓ | ✓ |
| SonarQube | ✓ | × | × | ✓ | ✓ |

*✓ supported directly, ~ partly or after additions, × not a goal of the tool.*

**Artemis and GitHub Classroom** create assignments and repositories themselves
from a template. The course projects live in the department's GitLab outside any
grading system, so adopting them would move the work out of the real tool.

**GitLab analytics** measures activity in one project or group. It knows neither
a course nor the course rules. GitPulse takes over its link from each result to the
original object.

**Danger and SonarQube** see one change or one project and would need a change in
every student repository. GitPulse takes over Danger's readable explanation of a
result and SonarQube's configurable gate with thresholds set by whoever deploys it.

No tool gives a view of process compliance across the projects of a course, so the
thesis builds a separate layer on top of GitLab that only reads student repositories.
