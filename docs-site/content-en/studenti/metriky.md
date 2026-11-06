---
title: "Understanding Metrics"
description: "Explanation of compliance rules R01-R13 for students"
---
{{< details >}}
- For: Student
- Requires: A university GitLab account
{{< /details >}}
GitPulse evaluates your project using 13 compliance rules (R01-R13). These rules are designed to verify the application of DevOps best practices, git workflow quality, and teamwork.

## Rules Overview

| Rule | Code | What it tracks | Why it matters |
|---|---|---|---|
| **Issue Assigned** | R01 | Student has an assigned issue | Each team member should take ownership of a specific task. |
| **Branch + MR Created** | R02 | Feature branch and MR opening | Code should not be pushed directly to the `main` branch. |
| **Tests Written** | R03 | Test file changes | Code without tests is not considered complete. |
| **MR Linked to Issue** | R04 | Linking MR to its issue | Traceability - the ability to trace a change back to its origin. |
| **MR Description** | R05 | Description in the Merge Request | Other team members must understand what the MR changes and how to test it. |
| **Code Review Received** | R06 | Receiving meaningful peer review | Prevents merging code without verification by peers (min. 2 reviewers). |
| **Code Review Given** | R07 | Giving meaningful peer review | Software development is team-based; reviewing peer code is essential. |
| **Review Response** | R08 | Replies to comments in threads | Discussion threads in MRs must not be ignored. |
| **MR Approved** | R09 | Receiving formal approval | MR must be approved before being merged into `main`. |
| **Merged by Author** | R10 | MR merged by its author | A developer should complete their workflow and merge the approved code themselves. |
| **MR + Issue Closed** | R11 | Closure of both MR and linked issue | Keeping tasks and the project board clean. |
| **Pipeline Green** | R12 | Successful CI/CD pipeline run | Code must pass automated checks in GitLab CI. |
| **Commit Quality** | R13 | Local Git workflow usage | Minimizes direct file edits via the GitLab web editor (Web IDE). |

---

## Compliance Score

Your overall compliance score is a weighted average of all active rules. The course instructor determines the weights for each rule. A lower score indicates process deficiencies or workflow violations that may affect the team's final grade.

### Score Levels

| Indicator | Score | Meaning |
|---|---|---|
| :green_heart: **Green (OK)** | 80 - 100 % | Team follows DevOps processes and collaborates perfectly. |
| :yellow_heart: **Yellow (Warning)** | 50 - 79 % | Some processes or individuals lag behind and need attention. |
| :heart: **Red (Critical)** | 0 - 49 % | Serious process errors, lack of teamwork, or incorrect branching. |

---

## Rule Details

### R01 - Issue Assigned
{{< alert type="note" >}}
**What the system checks.** Verifies if you have at least **1 issue** assigned to you in the GitLab project (default configuration). Every developer must take responsibility for specific tasks.
{{< /alert >}}
**How to pass:**
- Create or assign yourself an issue in GitLab before starting work.
- Do not leave tasks unassigned or assigned only to a single ("lead") member.

### R02 - Branch + MR Created
{{< alert type="note" >}}
**What the system checks.** Verifies if you work on your own feature branch and open a Merge Request. If the instructor enables the strict mode (`require_branch_convention=true`), the branch name must match the pattern (e.g. `issue-123-description`).
{{< /alert >}}
**How to pass:**
- Never push code directly to the `main` or `master` branch.
- Create a branch such as `issue-42-login` and open a Merge Request from it.

### R03 - Tests Written
{{< alert type="note" >}}
**What the system checks.** Verifies if at least one of your MRs contains changes in test files (files matching the default pattern, e.g. `*test*`, `tests/` etc.).
{{< /alert >}}
**How to pass:**
- Ensure your changes in the MR include adding or updating tests.

### R04 - MR Linked to Issue
{{< alert type="note" >}}
**What the system checks.** The MR must explicitly reference the issue it resolves. Linking can be done either via the source branch name (e.g. `issue-42-login`) or the MR description text (e.g. `Closes #42`, `Fixes #42`).
{{< /alert >}}
**How to pass:**
- When opening an MR, include a line like `Closes #XYZ` (where XYZ is the issue number) in the description.

### R05 - MR Description
{{< alert type="note" >}}
**What the system checks.** The Merge Request description must be of sufficient quality - at least **10 words** after stripping markdown syntax. If required, the description must contain specific template sections (e.g. `## Description` and `## Testing`).
{{< /alert >}}
**How to pass:**
- Write a clear description of what the MR changes and how to verify it. Avoid one-word descriptions like "fix" or "changes".

### R06 - Code Review Received
{{< alert type="note" >}}
**What the system checks.** Tracks whether your MRs received meaningful feedback from at least **2 distinct teammates**.
{{< /alert >}}

*Note: This check supports **partial scoring**. If you get a review from only 1 teammate, you receive 50% of this rule's weight. Comments must be meaningful (default minimum is 15 words).*
**How to pass:**
- Ask your colleagues to review your code before merging. Merging without review reduces your score.

### R07 - Code Review Given
{{< alert type="note" >}}
**What the system checks.** Tracks your activity as a reviewer. You must provide meaningful feedback on your colleagues' MRs (default is at least **2 distinct MRs** and each review must contain at least **15 words**).
{{< /alert >}}
**How to pass:**
- Actively review peer code. Write constructive and detailed comments instead of just saying "lgtm" or "+1".

### R08 - Review Response
{{< alert type="note" >}}
**What the system checks.** If colleagues leave comments on your MR, you must respond to them or resolve the threads. If no threads exist on your MR, this rule automatically passes. Comments by bot accounts, such as the classroom assistant, need no reply.
{{< /alert >}}
**How to pass:**
- Reply to discussion threads, explain changes, or reference a bug-fixing commit.

### R09 - MR Approved
{{< alert type="note" >}}
**What the system checks.** Tracks whether your MR received at least **1 formal approval (Approve)**. If `count_merged_as_approval` is enabled, a merged MR is considered approved.
{{< /alert >}}
**How to pass:**
- Ask colleagues to click the **Approve** button in the GitLab interface after a successful review.

### R10 - Merged by Author
{{< alert type="note" >}}
**What the system checks.** The developer who wrote the code and created the MR should merge it themselves once it is approved.
{{< /alert >}}
**How to pass:**
- After receiving approvals and ensuring the pipeline is green, merge your Merge Request yourself. Do not leave the merge action to colleagues.

### R11 - MR + Issue Closed
{{< alert type="note" >}}
**What the system checks.** After merging the MR, the linked GitLab issue must also be closed. The system verifies if the linked pair is successfully closed.
{{< /alert >}}
**How to pass:**
- Use closing keywords in the MR description (e.g., `Closes #XYZ`) to automatically close the issue on merge, or close the issue manually right after merging.

### R12 - Pipeline Green
{{< alert type="note" >}}
**What the system checks.** Tracks whether the branch from which the MR is created successfully passes the build and automated tests (CI pipeline is green) and whether a test job actually ran.
{{< /alert >}}
**How to pass:**
- Ensure your project has a `.gitlab-ci.yml` file configured.
- Fix compilation or test errors immediately when a pipeline fails.

### R13 - Commit Quality
{{< alert type="note" >}}
**What the system checks.** Verifies that you work in a local environment via Git CLI and push changes. The ratio of commits made via the GitLab web editor (Web IDE) must not exceed **30 %**.
{{< /alert >}}
**How to pass:**
- Clone the repository locally and work in your local IDE (e.g., VS Code).
- Only use the GitLab web editor exceptionally for quick typo fixes in documentation.

---

## Frequently Asked Questions (FAQ)

{{< alert type="note" >}}
**Can I see my score calculation details?.** Yes, clicking on your team's compliance score on the dashboard opens a breakdown showing each rule, its status (Passed / Failed / Partially passed), weight, and points.
{{< /alert >}}
{{< alert type="note" >}}
**Why does the system show 0% for R06 when I received a comment?.** Feedback from teammates must be meaningful. Short comments like "+1", "LGTM", or empty remarks are ignored. The default minimum length for a comment to be considered meaningful is 15 words.
{{< /alert >}}
{{< alert type="note" >}}
**What happens if we are a solo team (only 1 member)?.** The compliance engine automatically detects solo teams. For teamwork-focused rules (e.g. Code Review Given R07, Code Review Received R06), the system automatically awards full points so you are not penalized for having no teammates.
{{< /alert >}}