---
title: "Classroom assistant"
description: "A bot that works on the exercise projects like a colleague - push review, a merge conflict, issues and merge requests"
---
{{< details >}}
- For: Teacher
- Requires: The owner or teacher role in the course (or an administrator), a bot token in GitLab, `FEATURE_CLASSROOM_ASSISTANT=true` on the server
{{< /details >}}
The classroom assistant is a bot that behaves like a colleague on the project during exercises. Students get no new interface for it - they meet it in GitLab: a comment on a commit, a merge request review, an issue it assigns them, a commit from a "colleague". Teachers set it up and follow it on the course's **Assistant** tab.

The tab is there for the course's owner, its teachers and administrators. A teacher who sees the course only because they mentor one of its teams does not get it, and their dashboard shows none of the assistant's warnings or events either. The bot writes to GitLab for the whole course, so only the people who run the course control it.

Every rule is deterministic - the assistant uses no LLM. Each step has a clear GitLab event that starts it and a clear condition for when it is met.

## Watching and acting are kept apart

GitPulse reads GitLab with a read-only token, and the analytics (checks R01 to R13) never write to GitLab. The assistant is the one part that acts in GitLab - it comments, commits, opens issues, approves and merges. It does so **under a bot account and token of its own**, stored encrypted with the course:

- the read-only token GitPulse syncs with is refused,
- when the bot token expires or GitLab rejects it, the course's sync keeps running,
- disconnecting the token stops every tool at once; what the assistant already did in GitLab stays.

## Connecting the bot

1. In GitLab, open the course's group, then **Settings > Access tokens**.
2. Add a token with the **Maintainer** role and the **`api`** scope; set the expiry to, for example, the end of the semester. GitLab creates a bot user for the token (e.g. `group_123_bot_…`) that is a member of the group and its projects.
3. In GitPulse, open the course, the **Assistant** tab, click **Connect bot** and paste the token. GitPulse asks GitLab who the token belongs to and whether it has the `api` scope - only then is it stored.

The Maintainer role is needed because the assistant commits to the default (protected) branch and merges merge requests. Developer is enough for push review alone.

The assistant reacts to the **Push**, **Merge request** and **Comments** events GitPulse already receives. Set the webhook up as described in [Webhooks](../../gitlab/webhooky/) - nothing else is needed.

The card shows which account the bot acts as and when its token expires; it flags the token two weeks before the expiry. When the token expires or GitLab refuses it (it was revoked, say), the assistant stops and the page says so at the top - **Replace token** connects a new one. The top of the page also warns when tools are on but no bot is connected. When the course has no webhook, or its webhook has received no event from GitLab for 48 hours, the page says so as it opens, in a notice in the corner of the screen, as the Events page does.

## The tools

Each tool is switched on separately and saved with **Save changes**. The **Comments** card sets the language the assistant writes in GitLab (Slovak or English) - its comments, the issues and the colleague's line.

The assistant also follows the rules the course grades: with check **R02** on, a new branch and a merge request's branch are checked against the course's branch-naming rule; with **R05** on, the review asks for the merge request description sections. The tool cards name these rules. A check the course switched off is never asked for.

### Push review

After a student's push, the assistant comments on the pushed commit when something is off:

- the push went **straight to the default branch** instead of a branch of their own and a merge request,
- the commit message **was written by the GitLab web editor** ("Update README.md") - the same rule as check R13,
- the first line of the message is **shorter** than the set length (10 characters by default),
- a new branch's name **breaks the course's rule** (only when the course grades R02).

A new branch gets a word of encouragement with its first commits; a clean push to an existing branch gets no comment - a colleague does not answer every push. A branch created in GitLab with **New branch** has no commit of its own yet, so the assistant speaks at the first push to it, and judges its name then. GitLab writes the merge of a merge request to the default branch on behalf of the student who clicked **Merge** - that is not a push straight to `main` and gets no comment; its commits were judged on the branch. Merge commits are not judged, git writes their message. Every push is commented on at most once, even when GitLab delivers its webhook again.

The comment a student gets - in Slovak, the language the app's students are taught in:

```text
Push do vetvy `main`:

- Tento push išiel priamo do `main`, predvolenej vetvy. Pracuj vo vlastnej vetve a zmenu do nej dostaň cez merge request.
- Commit 1a2b3c4d má správu „Update README.md“, ktorú napísal webový editor GitLabu. Napíš, čo sa zmenilo a prečo.

Maj to na pamäti pri ďalších commitoch.
```

### Merge conflict

The exercise names a file (`README.md` by default) the students edit on a branch of their own.

1. The **first time a student's branch changes the file**, the assistant, as a "colleague", commits to the default branch an edit of **exactly the lines** the student changed - a line with a control code (`GP-1A2B3C`). Merging the branch then always stops with a conflict, even when the default branch has moved on in the meantime.
2. Until the student merges the default branch into theirs (merge or rebase), the assistant stays silent - the conflict waits for the student to merge.
3. Then, on every push, it checks the file: **no conflict markers left**, both the **colleague's line** and the **student's own change** kept. The result goes to the branch's merge request if one is open, otherwise to the commit. When everything is in order it says well done and the task is finished.

Until the branch changes the file, or while the file is not in the repository, the task waits and the Activity table says what for. Each student has one exercise per project: the first branch that changes the file. Say in the exercise text which file to edit and that resolving the conflict means keeping both changes.

### Issues and merge requests

**Preparation.** The **Prepare exercise** button (it needs the bot connected and the tool switched on and saved), in every chosen project:

- creates, in one commit, a file for each student of the team from the template (`ulohy/{username}.txt` by default) with `???` placeholders to fill in,
- opens an issue assigned to each student, with the steps: a branch of their own, fill the file in, commit, a merge request with `Closes #N`. The issue also says in advance what the review will ask for besides: the description sections when the course grades R05, and the branch-name rule when the course is stricter than the default "anything but `main` and the like". The last step says who merges.

Running it again adds only students who do not have an issue yet - that is also how a student added later gets one. Existing files are never overwritten. It runs in the background like a sync: the top bar shows its progress, a notice says when it is done, and the page reloads with the result per project. If the form has unsaved changes, the page does not reload, so they are not lost; only the activity card is redrawn. While it runs the card shows "Preparing" and the button allows no second run. When the run cannot even start, because GitLab refused the token in the meantime for example, the card says so at once, with the reason. Every run is in Administration, System, in the job history, with its duration. A student GitPulse does not yet know as a GitLab user (after a roster import, before the sync) cannot be assigned an issue - the result counts them apart.

**The run** is a finite state machine over the events GitPulse receives:

| Event | What the assistant does |
|:--|:--|
| A student opens or changes a merge request | Review: a branch of their own, the default branch as the target, the description links the issue, the change is in the assigned file only, no `???` left, not a draft, no conflicts, threads resolved. If something is missing, one comment with exactly that. |
| The student comments on the merge request | Reviews again and answers, even when nothing changed. When a newer review already followed the comment (after an edit of the merge request, say), it is not repeated. |
| Nothing is missing | Approves it and asks the student to merge. With **Merge the approved merge request** on, it merges it itself; if a pipeline is running, the merge waits for it. While GitLab is still working out after a push whether the merge request can merge, the review waits a few seconds so as not to approve a conflict. |
| GitLab merged the merge request | Closes the issue and says well done. |
| Someone merged it before the approval | Says so on the merge request; the task is "Merged without review". |
| The merge request is closed unmerged | The task lets go of it; the next merge request for the issue is reviewed from the start. |

By default the student merges: check R10 asks whether the author or a team member merged after the approval, and a merge by a bot does not count as the student's. If you want the whole cycle automatic, turn merging by the assistant on - R10 then does not pass for those merge requests. R09 counts the assistant's approval like a teacher's; the bot's comments are no reviews for R06, as the bot is no team member. Nor does R08 count them among the threads the author has to answer, so a student need not reply to an "approved, merge it".

{{< alert type="warning" >}}
**The exercise counts in grading.** The exercise's issue, branch, merge request and closed issue are ordinary GitLab work, and checks R01, R02, R04, R05 and R11 count them like any other. Prepare it in projects meant for practice (a course of its own, say) or before the team assignment starts. The card says so next to **Prepare exercise**.
{{< /alert >}}

The review also reports a failed pipeline, and in a course grading R02 and R05 the branch name and missing description sections.

A review is posted only when it has something new to say (another commit or other findings), so changing a label does not repeat it. A merge request that names someone else's issue is told once whose issue it is.

## Assistant activity

The **Assistant activity** card shows what the assistant did - newest first, with a link to where it happened in GitLab. It filters by tool, searches by student, group or project, and sorts by group too. The card updates itself when the assistant does something in GitLab, and **Refresh** reloads it.

| State | Meaning |
|:--|:--|
| Waiting | The assistant is watching and has nothing to do yet (the branch has not changed the file). |
| Conflict planted | The colleague's commit is on the default branch. |
| Issue assigned | The issue is open, no merge request yet. |
| Changes requested | The last review or check asked for a change. |
| Approved | Approved, merging or waiting for the pipeline. |
| Done | The task is done, and done right. |
| Merged without review | The merge request was merged before the assistant approved it. |
| GitLab refused | GitLab refused the action (e.g. 403 when the bot lacks permission); the reason is in the Last action column. The next event tries again. |

## On the dashboard and in the course configuration

- **Items that need your attention** on the dashboard say what the Assistant page says at its top: a token GitLab refuses or that has expired, tools on without a bot, a token that expires soon, and an exercise preparation that did not finish. They also count the actions GitLab refused the assistant in the last 7 days. Each item leads to the Assistant page. A missing webhook already has an item of its own for the course, so it is not repeated for the assistant.
- **Follow the latest updates** shows the bot connected and disconnected, the tools changed, an exercise prepared and a token GitLab refused, with a link to the Assistant page. Students do not see these rows.
- **Exporting and importing the course configuration** carries the assistant's tool settings too (the `assistant` section), never the bot or its token. The import checks them as the page's form does; with the assistant switched off on the server, it skips the section.

## Limits

- The assistant ignores the events it caused itself (its comments, its commit, its approval) - except the merge event, which tells it the merge happened.
- It acts only for the team's students - a teacher's or a mentor's push gets no comment. A member you excluded from scoring is no student to the assistant either: no issue, no comments.
- An archived course is read-only: GitPulse drops its webhooks, so the assistant stands still, and the Assistant tab allows no change.
- A course transferred to a new semester keeps the tools' settings (which are on, the files, the language, who merges), not the bot token - the new semester connects its own.
- The server administrator switches the whole feature on and off with `FEATURE_CLASSROOM_ASSISTANT`.
