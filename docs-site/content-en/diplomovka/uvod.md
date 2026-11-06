---
title: "1. Introduction"
weight: 1
description: "Problem, motivation and task formulation"
---
{{< details >}}
- For: Thesis reader
- Requires: Nothing
{{< /details >}}
The team assignment of Fundamentals of Software Engineering asks a student to solve
an assigned task with unit tests, review the code of the other team members and
merge their solutions into the main branch. Fundamentals of DevOps uses almost the
same assignment. The way a student works is graded too, and the finished program
does not show it.

The evidence for one task sits in several places in GitLab: the issue, the branch
and the merge request, the review discussion and approval, the pipeline result and
the commit history. In the summer term 2025/2026 the first course had 189 students
in nine groups and the second 393 students in eight groups. At that size an ongoing
manual check is hardly ever done, although it matters most during the term.

## 1.1 Motivation

Many check questions can be answered straight from the state stored in GitLab, for
example whether a student has an assigned issue or whether a pipeline passed. When
such indicators are recomputed shortly after a change and every result carries its
reason and a link to the original object, both teacher and student see a missing
step in time. One computation for the whole course makes the groups comparable.
Code quality and the student's understanding are still judged by the teacher and the
tool does not turn percentages into grades.

## 1.2 Task formulation

The goal is to design, build and evaluate tools that support teaching DevOps
fundamentals on team projects kept in GitLab. Sub-tasks:

1. analyse the team assignment requirements and separate conditions a program can
   check from those the teacher has to judge,
2. examine existing tools for automated assessment, repository analytics and change
   checking,
3. verify which data GitLab sends through webhooks and which must be fetched through
   the REST API, and set the limits of interpreting each,
4. design the architecture, data flow and security boundaries of a platform that
   does not touch student repositories,
5. build a prototype with course import, synchronisation, configurable checks and
   views per course, group, project and student,
6. design an evaluation that separates technical correctness from pedagogical effect
   and prepare it with the target group.
