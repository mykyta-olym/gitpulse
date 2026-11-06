---
title: "Getting Started"
description: "Introductory guide for students - first steps with GitPulse"
---
{{< details >}}
- For: Student
- Requires: A university GitLab account
{{< /details >}}
## Logging In

1. Open [GitPulse](https://gitpulse.kpi.fei.tuke.sk/) in your web browser
2. Click **Sign in with GitLab**
3. Authorize access using your account at [gitlab.example.com](https://gitlab.example.com)
4. After successful login, you will be redirected to the dashboard

{{< alert type="note" >}}
**First login.** On your first login, the system automatically creates your profile and syncs basic information from GitLab (name, email, avatar). Your instructor must first add you to a course before you can see your projects.
{{< /alert >}}
## Dashboard Navigation

After logging in, you'll see the main sections:

### Course Selection

At the top of the page, select the course you're enrolled in. Each course contains a list of projects you have access to.

### Project Overview

For each project you can see:

| Section | Description |
|---|---|
| **Compliance score** | Overall project evaluation against rules R01-R13 |
| **Activity timeline** | Graph of commits, issues, and merge requests over time |
| **Team members** | Overview of individual member contributions |
| **Recent events** | List of latest actions in the project |

### Rule Details

Clicking on the compliance score shows individual rule details:

- **Passed** - rule is satisfied
- **Failed** - rule is not satisfied
- **Partial** - rule is partially satisfied

## What You Can Do

As a student, you have the following capabilities in GitPulse:

- **View** your team's compliance score
- **Track** your project's activity timeline
- **See** individual team member contributions
- **Export** activity summaries (if enabled by instructor)
- **Receive** email notifications about project status

## What You Cannot Do

- Change rule configurations or course settings
- Access other teams' projects
- Modify instructor evaluations
- Change rule weights

---

## Tips for Effective Work

{{< alert type="note" >}}
**Planning via Issues (R01, R04, R11).** Always plan every change as an Issue in the GitLab project first and assign it to the responsible team member. When opening a Merge Request, don't forget to link it to the issue using closing keywords (e.g. `Closes #XYZ` in the MR description) so that the issue is automatically closed upon merge.
{{< /alert >}}
{{< alert type="note" >}}
**Branching and Merge Requests (R02, R05, R10).** Never push code directly to the main branch (`main`/`master`). Create a feature branch (e.g. `issue-42-login`) and open a Merge Request from it with a clear and detailed description of the changes. Once the MR is approved, merge it yourself as the author.
{{< /alert >}}
{{< alert type="note" >}}
**Meaningful Code Review (R06, R07, R08, R09).** Code review is not just a formal "Approve" click. Provide constructive and detailed comments (at least 15 words) on your colleagues' MRs and, conversely, respond to all discussion threads in your own Merge Requests.
{{< /alert >}}
{{< alert type="note" >}}
**Testing and CI/CD (R03, R12).** Every Merge Request should also include changes to tests. Make sure your changes pass automated testing and the pipeline in GitLab CI is successful (green).
{{< /alert >}}
{{< alert type="note" >}}
**Local Work and Git CLI (R13).** Clone the repository locally and work in your favorite IDE (e.g. VS Code). Avoid editing files directly via the GitLab web interface (Web IDE) as this violates the commit quality rule.
{{< /alert >}}
## Need Help?

If you have access issues or questions about evaluation:

1. Contact your **instructor** or **teaching assistant**
2. Check the [FAQ](faq.md) section
3. For technical issues, contact [mykyta.olym.work@gmail.com](mailto:mykyta.olym.work@gmail.com)
