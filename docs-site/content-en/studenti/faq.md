---
title: "Student FAQ"
description: "Frequently asked questions for GitPulse students"
---
{{< details >}}
- For: Student
- Requires: A university GitLab account
{{< /details >}}
## Access and Login

{{< alert type="note" >}}
**How do I log in to GitPulse?.** Visit [gitpulse.kpi.fei.tuke.sk](https://gitpulse.kpi.fei.tuke.sk/) and click **Sign in with GitLab**. You'll be redirected to GitLab to authorize access.
{{< /alert >}}
{{< alert type="note" >}}
**I don't see any courses or projects after logging in. What should I do?.** Your instructor needs to add you to a course in GitPulse first. Contact your instructor or teaching assistant.
{{< /alert >}}
{{< alert type="note" >}}
**Can I access GitPulse from my phone?.** Yes, GitPulse is a responsive web application and works in mobile browsers. For the best experience, we recommend the desktop version.
{{< /alert >}}
{{< alert type="note" >}}
**My avatar or name is incorrect. How do I change it?.** GitPulse syncs your information from GitLab. Change your avatar or name in your profile settings at [gitlab.example.com](https://gitlab.example.com) and the data will update during the next sync.
{{< /alert >}}
## Metrics and Evaluation

{{< alert type="note" >}}
**What is a compliance score?.** The compliance score is a percentage expression of how well your team follows established DevOps practices. A higher score means better practices. More details in [Understanding Metrics](metriky.md).
{{< /alert >}}
{{< alert type="note" >}}
**Is the compliance score my grade?.** No. The compliance score serves as input data for the instructor, who decides the final grade independently. The instructor can also consider additional factors.
{{< /alert >}}
{{< alert type="note" >}}
**Why is my individual score low?.** Check the rule breakdown on the dashboard. Most common reasons:
{{< /alert >}}

- Few commits or uneven distribution over time
- Missing issues or merge requests
- Non-functional CI/CD pipeline
- Commits not linked to issues
{{< alert type="note" >}}
**When do metrics update?.** Metrics update after each GitLab synchronization, typically within a few minutes after push, issue creation, or merge request.
{{< /alert >}}
{{< alert type="note" >}}
**Can the instructor override automated evaluation?.** Yes. The compliance score is only supporting evidence; the instructor can account for manual code review, demo results, oral defence, and course-specific rules.
{{< /alert >}}
## Working with GitLab

{{< alert type="note" >}}
**What GitLab actions does GitPulse track?.** GitPulse tracks: commits, issues, merge requests, CI/CD pipelines, comments and reviews on merge requests, and branch operations.
{{< /alert >}}
{{< alert type="note" >}}
**Does GitPulse track private repositories?.** GitPulse only accesses projects registered by the instructor in a course. Your personal or other projects are not accessible.
{{< /alert >}}
{{< alert type="note" >}}
**Do commits on branches other than main count?.** Yes, GitPulse tracks activity on all branches of a registered project.
{{< /alert >}}
{{< alert type="note" >}}
**Who is the bot commenting on my commits?.** When the teacher turns on the classroom assistant for the course, it acts in GitLab like a colleague on the project. It is the course's bot account (for example `group_123_bot_…`): it comments on commits and merge requests, assigns you the exercise issue and, in the merge-conflict exercise, adds a commit of its own to the project. When you reply to it with a comment on the merge request, it looks again and answers. Its comments do not count towards your grade; your work on the issue and the merge request is assessed like any other.
{{< /alert >}}
{{< alert type="note" >}}
**What if I committed under a different email?.** GitPulse maps commits by GitLab identity. If you use a different email in your Git configuration, commits may not be correctly attributed. Set the correct email in Git:
{{< /alert >}}

```bash
git config user.email "your.email@student.university.edu"
```
## Privacy and Security

{{< alert type="note" >}}
**What data does GitPulse collect?.** GitPulse only collects data from your GitLab projects: commits, issues, merge requests, pipeline results. It does not track your activity outside GitLab. Details in our [Privacy Statement](../pravne/ochrana-udajov.md).
{{< /alert >}}
{{< alert type="note" >}}
**Who can see my data?.** Your data is visible to: you, your team members, and course instructors/TAs. Other teams or students do not have access to your data.
{{< /alert >}}
{{< alert type="note" >}}
**Can I request deletion of my data?.** Yes, under GDPR you have the right to erasure. Contact [mykyta.olym.work@gmail.com](mailto:mykyta.olym.work@gmail.com) with the subject "Data Deletion Request".
{{< /alert >}}
## Technical Issues

{{< alert type="note" >}}
**The dashboard isn't loading or is slow..** Try:
{{< /alert >}}

1. Refresh the page (Ctrl+F5)
2. Clear browser cache
3. Try a different browser
4. If the problem persists, report it to your instructor
{{< alert type="note" >}}
**I see a '403 Forbidden' or 'Access Denied' error..** This means you don't have access to the requested resource. Most common reasons:
{{< /alert >}}

- You haven't been added to the course - contact your instructor
- Your session has expired - log out and log back in
- You're trying to access another team's project
{{< alert type="note" >}}
**I'm not receiving email notifications..** Check your spam/junk folder in your email client. Notifications come from the system address. If nothing arrives, contact your instructor.
{{< /alert >}}