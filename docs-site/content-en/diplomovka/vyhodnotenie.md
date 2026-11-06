---
title: "7. Evaluation methods"
weight: 7
description: "Technical verification, agreement with manual grading, a teacher study and student feedback"
---
{{< details >}}
- For: Thesis reader
- Requires: Nothing
{{< /details >}}
Technical correctness and pedagogical effect are evaluated separately. The
evaluation has to verify four claims:

1. the result of every check matches the described mapping, and a repeated or
   missing delivery neither loses nor duplicates data,
2. a check result agrees with a teacher answering the same question in GitLab,
3. with GitPulse a teacher answers common questions faster and with fewer page
   changes and finds the system usable,
4. a student with access to their own overview can name the step they are missing.

## 7.1 Method

- **Technical verification:** automated tests on every release and operational
  metrics during the term. At least 95 % of events must be processed within a minute
  and every failure must have a known cause.
- **Agreement with manual grading:** the finished Fundamentals of Software
  Engineering projects of summer 2025/2026, a sample of at least thirty students,
  two independent teachers. For each check the share of agreement, both kinds of
  disagreement and Cohen's kappa. Directly stored states should agree in at least
  95 % of cases; disagreements on proxy indicators are sorted by cause.
- **Teacher study:** five tasks, four of them once with GitLab alone and once with
  GitPulse, measuring time and page changes, then the System Usability Scale with a
  target of at least 68 and a short interview.
- **Student feedback:** an anonymous questionnaire after the team project during
  the live deployment.
- **Classroom assistant:** one exercise in practice projects, the number of finished
  exercises and a sample of comments rated by a teacher.

## 7.2 Schedule

The agreement measurement and the teacher study take place in the winter term
2026/2027 on finished projects, with their evaluation planned by March 2027. The
live deployment starts with the summer term 2026/2027. The academic period of a
course keeps both data sets apart. Participation of teachers and students is
voluntary and results are reported in aggregate without names.
