---
title: "2. Analysis of the team assignments"
weight: 2
description: "Course requirements, observable practices and checks R01 to R13"
---
{{< details >}}
- For: Thesis reader
- Requires: Nothing
{{< /details >}}
The chapter settles what to observe. The assignment brings three duties: one's own
contribution with tests, reviewing the code of the other team members, and merging
the change into the main branch. Both courses share the wording of the project and
differ in preparation, so one set of checks serves both and each course sets its own
thresholds.

## 2.1 What leaves a trace in the repository

Branches and merge requests, the link between a change and its issue, automated
testing in pipelines, code review and the way the student uses Git can all be
observed. A green pipeline without a test job proves no testing, though, and an
approval click is not the same as a real review comment. The tool therefore tells
apart reviewers, comments, discussion threads, author replies and approvals.

## 2.2 Checks R01 to R13

| ID | Question |
|---|---|
| R01 | Does the student have at least one assigned issue? |
| R02 | Was their change made in their own branch with a merge request? |
| R03 | Did they add or change a test file in one of their merge requests? |
| R04 | Does the merge request refer to the issue it solves? |
| R05 | Does the merge request description have minimal content or template sections? |
| R06 | Did the required number of classmates comment on their merge request? |
| R07 | Did they review the required number of other merge requests? |
| R08 | Did they reply to the review threads in their own merge request? |
| R09 | Was their merge request approved? |
| R10 | Did the team member chosen by the course rule merge the change? |
| R11 | Are the merge request and its issue closed? |
| R12 | Is there a passing pipeline with a test job? |
| R13 | Does the share of web editor commits stay below the threshold? |

R03 checks only that a test file changed, not test quality. R06 and R07 join one
reviewer's comments on one merge request and require fifteen words by default;
GitLab's system notes do not count. R13 compares commit titles with the web editor's
default patterns and is off with zero weight by default.

## 2.3 Limits of the decomposition

An issue or pipeline state is stored directly, while R06, R07 and R13 work with
proxy indicators. Their results prompt a manual look. Research on student projects
shows how strongly aggregates depend on the chosen metric, so they serve as a basis
for a talk with the team.
