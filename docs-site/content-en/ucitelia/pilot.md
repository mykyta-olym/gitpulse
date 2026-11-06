---
title: "Evaluation in teaching"
description: "How GitPulse will be evaluated with teachers and students and what a teacher does"
---
{{< details >}}
- For: Teacher
- Requires: A GitPulse account with the teacher role
{{< /details >}}
This page describes how GitPulse will be evaluated in teaching. It follows chapter
[7. Evaluation methods](../../diplomovka/vyhodnotenie/) of the thesis. There are no
results yet; the measurements are still to come.

## What is verified

1. The checks compute correctly and a repeated or missing event delivery neither
   loses nor duplicates data.
2. A check result agrees with a teacher answering the same question in GitLab.
3. With GitPulse a teacher answers common questions faster and with fewer page
   changes and finds the system usable.
4. A student who sees their own overview can name the step they are missing.

## Schedule

| Period | What happens |
|:-------|:-------------|
| Winter term 2026/2027 | Agreement measurement on finished projects from summer 2025/2026 and a task study with teachers. Evaluation by March 2027. |
| Summer term 2026/2027 | Live deployment in the course, operational metrics, a student questionnaire after the team project and one exercise with the assistant. |

Both data sets live in the same instance, kept apart by the course's academic period.

## What a teacher does

### Before the live deployment

- [ ] Import the course after the teams are formed ([Getting started](../zaciname/)).
- [ ] Set up webhooks before work on the team project starts, so events are collected
      from the beginning ([Webhooks](../../gitlab/webhooky/)).
- [ ] Review the enabled checks, weights and thresholds in the course settings.
- [ ] Tell the students in class that they have their own overview and that using it
      is voluntary.

### During the term

- Use the overview as you see fit. The tool is not a condition of grading and grades
  are given as before.
- Treat a low score as a reason to talk to the student, not as a verdict. It can
  mean an incomplete sync, a differently organised project or a missing step
  ([Interpreting results](../interpretacia/)).
- Use the classroom assistant only in practice projects so it does not affect the
  checks of the team project ([Classroom assistant](../asistent/)).

### During the agreement measurement and the task study

- In the agreement measurement two teachers assess a sample of students
  independently and directly in GitLab, without opening GitPulse.
- In the task study a teacher solves four tasks once with GitLab alone and once with
  GitPulse on two comparable groups; a fifth task checks a system answer in GitLab.
  The System Usability Scale questionnaire and a short interview follow.

## Questionnaires

Every role has its own anonymous questionnaire in Google Forms (in Slovak). The
application shows each user theirs in the Support & suggestions panel of the
dashboard.

| Questionnaire | Who fills it in |
|:--------------|:----------------|
| [Student questionnaire](https://forms.gle/mNvu5Yv4bLmm4D6L6) | students after the team project is handed in |
| [Teacher questionnaire](https://forms.gle/TaHFrQaFM1a33hG27) | teachers and course owners, after the task study or during the term (includes the System Usability Scale) |
| [Assistant comment review](https://forms.gle/6AbyWK3HGoYpjkfm7) | teachers, one response per reviewed assistant comment |
| [Administrator questionnaire](https://forms.gle/AYkbAJEft1bmHpTq5) | administrators of the GitPulse instance |

## Data and privacy

GitPulse data stays in the university's infrastructure and results are reported in
aggregate without names. Screen recordings from the task study are deleted once the
times are transcribed. Questionnaire responses are stored by Google Forms, which
collects no name, email or login with them. GitPulse does not track browser use and
does not estimate saved clicks. See the [privacy notice](../../pravne/ochrana-udajov/).
