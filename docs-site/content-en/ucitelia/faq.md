---
title: "Frequently Asked Questions"
description: "FAQ for teachers using GitPulse"
---
{{< details >}}
- For: Teacher
- Requires: A GitPulse account with the instructor role
{{< /details >}}
## General Questions

### What is GitPulse?

GitPulse is a tool for automatic analysis of student activity on GitLab projects. It provides objective metrics for evaluating teamwork and DevOps practices.

### Who can use GitPulse?

GitPulse is intended primarily for teachers and teachers. Log in via GitLab OAuth or contact the administrator for access.

### What data does GitPulse collect?

GitPulse collects publicly available data from GitLab projects:

- Commit history
- Merge requests and code review comments
- Pipeline results and test coverage
- Issues
- Project/group members

{{< alert type="note" >}}
**What we don't collect.** GitPulse does not collect the content of private messages, local student data, or monitor activity outside of GitLab. AI enrichment processes only aggregated metrics - personal data is automatically redacted.
{{< /alert >}}
---

## Import and Synchronization

### How to import a course from GitLab?

1. On the dashboard, click **"Import from GitLab"**
2. Paste a URL:
      - **Group URL** - imports all subgroups (teams) and projects
      - **Project URL** - imports only a single project
3. Fill in the course name and semester
4. Click **"Import"**

### Why was the entire parent group imported?

If you paste a group URL, GitPulse imports all subgroups as teams. If you want to import only one project, make sure you paste the URL of a specific **project**, not a group.

### Why can't I see team activity?

**Possible causes:**

1. **Synchronization hasn't run yet**
   - Check the global status bar - sync may still be in progress
   - Click **"Sync"** on the course page

2. **Project is not in the course**
   - Check if the project is added in GitPulse

3. **Processing delay**
   - There may be a delay of a few minutes under high load

### What does synchronization download?

- Commits, Merge Requests, Issues, Pipeline results
- Project members (automatic student detection)
- Code review comments
- Test coverage data

### Why does the status bar show incorrect numbers?

The status bar updates every 2 seconds. Stale jobs (older than 3 minutes) are automatically cleaned up. If you see incorrect counts, refresh the page.

---

## Metrics and Evaluation

### What does the compliance score mean?

The compliance score (0-100%) expresses how well the team adheres to defined DevOps practices. It consists of 13 built-in checks (R01-R13) plus optional custom checks. Only enabled checks count, and the sum of their partial scores is divided by their total weight.

### Are thresholds configurable?

Yes. In course settings you can change:

- **Green threshold** (default 80%) - team meets requirements
- **Yellow threshold** (default 50%) - needs attention
- Changes are reflected immediately on the dashboard

### Is the compliance score an absolute grade?

**No.** Compliance score is only one indicator. You should combine it with:

- Quality of outputs (demo, code)
- Project presentation
- Individual interviews
- Peer evaluation

### How to interpret a low score in one category?

A low score in a category can mean:

1. **Real problem** - the team ignores the given practice
2. **Different workflow** - legitimate reason (e.g. pair programming)
3. **Technical problem** - data is not collected correctly
4. **Missing configuration** - e.g. missing CI/CD in the project

{{< alert type="note" >}}
**Best Practice.** Always verify low scores by talking to the team.
{{< /alert >}}
---

## Roles and Scoring

### What do the colored badges next to member names mean?

Badges display the GitLab role of the team member. Colors correspond to access levels:

- **Owner** (yellow) - highest level (50)
- **Maintainer** (blue) - level 40
- **Developer** (grey) - level 30
- **Reporter/Guest** (light grey) - level 20/10

### What does "(not in team score)" mean?

This label means the member is excluded from the team compliance score. Reasons:

1. **Low role with no activity** - Guest or Reporter who created no commits, MRs, issues, or reviews
2. **Inherited access with no activity** - member inherited access via a parent group but has no project activity
3. **Teacher** - teacher/TA added as `is_teacher`

### What is "inherited" membership?

A member with the "inherited" badge gained project/group access not directly, but through inheritance from a parent GitLab group. If they have no activity, they are automatically excluded from the team score.

### Why is my team score lower than expected?

Check for inactive members dragging down the average. GitPulse now automatically excludes Guest/Reporter with no activity and inherited members with no activity, but Developer+ with zero activity still counts toward the score.

### What does the "Re-check" button do?

The button triggers an immediate recomputation of team compliance metrics. Unlike regular recomputation, it runs **all** checks (R01-R13 + custom), even if some are filtered for the current curriculum week.

---

## Academic Integrity

### How should suspicious activity be handled?

GitPulse shows the data needed for manual review: commit timeline, issues, MRs, reviews, and CI. If you see many generic commits, superficial reviews, or unusual work distribution, verify the GitLab detail before drawing a conclusion.

### What should be documented?

1. **Concrete links** - issue, MR, commit, or pipeline
2. **Context** - deadline, task type, agreed workflow
3. **Student explanation** - if provided
4. **Instructor decision** - according to the course rules

---

## Configuration and Export

### How to share settings between courses?

Use **JSON export/import**:

1. On the source course, click **"Export JSON"**
2. On the target course, click **"Import JSON"** and upload the file
3. JSON includes compliance controls, deadlines, and thresholds

### Can I add custom controls?

Yes. GitPulse supports custom controls (C01+) with configurable rules and weights.

---

## Privacy and GDPR

### What are the rights of students?

According to GDPR, students have the right to:

- **Access** - they can request their data
- **Correction** - if the data is incorrect
- **Deletion** - in justified cases
- **Portability** - data export in standard format

### How long is data stored?

Data is kept for the duration of the academic course plus 6 months in case of appeals. It is then automatically deleted.

### What about AI enrichment and privacy?

AI enrichment processes only aggregated metrics (commit counts, MRs, etc.), not code content. Student personal data (names, emails) is automatically redacted before sending to the AI model.

---

## Problems and Support

### Dashboard is slow

**Solutions:**

1. Refresh the page (F5)
2. Clear your browser cache
3. Try a different browser
4. Report the problem to an administrator

### How to report a bug?

1. Use **in-app support** at [gitpulse.kpi.fei.tuke.sk/dashboard/support](https://gitpulse.kpi.fei.tuke.sk/dashboard/support)
2. Attach a screenshot and steps to reproduce
3. Specify the browser and operating system

---

## Contacts

| Support Type | Contact |
|-------------|---------|
| Technical support | [mykyta.olym.work@gmail.com](mailto:mykyta.olym.work@gmail.com) |
| Bug reports | [In-app support](https://gitpulse.kpi.fei.tuke.sk/dashboard/support) |
| Feature requests | [In-app support](https://gitpulse.kpi.fei.tuke.sk/dashboard/support) |
| Documentation | This page |
