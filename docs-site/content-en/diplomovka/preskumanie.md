---
title: "4. Getting data from GitLab"
weight: 4
description: "Webhooks, the REST API and mapping checks R01 to R13 to data sources"
---
{{< details >}}
- For: Thesis reader
- Requires: Nothing
{{< /details >}}
GitLab offers two ways to the data. A **webhook** reports a change within seconds,
but delivery is not guaranteed exactly once, order is not guaranteed and GitLab
disables it after repeated failures. The **REST API** returns the full current
state of an object, but a program does not learn about a change by itself. The
platform therefore treats an event as a signal and the REST API as the source of
detail.

## 4.1 What an event body contains

A merge request event lacks the changed files (R03), a Note event lacks the whole
discussion thread (R08) and a Push event carries at most twenty commits. A pipeline
event, on the other hand, lists its jobs, so R12 can be decided from the body alone.
On receipt the body is stored, the response returns at once and enrichment runs in
the background. A manual sync fills in what happened before the webhook was set up
or what was not delivered. GitPulse has no periodic crawl of the projects.

## 4.2 Mapping checks to sources

| Check | Trigger | Enrichment | Limit of interpretation |
|---|---|---|---|
| R01 | Issue | state and assignee | An assignment does not prove work was done. |
| R02 | Merge Request | none | The branch name convention is optional per course. |
| R03 | Merge Request | changed files | A file name says nothing about test quality. |
| R04 | Merge Request | none | A reference does not prove the change matches the issue. |
| R05 | Merge Request | none | Length and sections are only a formal minimum. |
| R06 | Note | merge request notes | Word count is a proxy for quality. |
| R07 | Note | notes of several merge requests | The count does not show how hard a review was. |
| R08 | Note | discussion threads | Comments outside a thread are paired only roughly. |
| R09 | Merge Request | approvals | An approval without a comment proves no review. |
| R10 | Merge Request | none | Who may merge is set by the course rule. |
| R11 | Issue, Merge Request | state of both | Without an explicit link the result is less certain. |
| R12 | Pipeline | none | A pass proves only what the pipeline really runs. |
| R13 | Push, sync | commit history | A title pattern does not prove which client was used. |

## 4.3 Findings for the design

All thirteen checks have an available input. For two of them the needed data does
not exist in GitLab: which comment a reply outside a thread answers (R08) and which
client created a commit (R13). The interface marks such checks, and results store
object identifiers and a textual explanation. A separate detector of insincere
fulfilment was dropped from the design, since it would combine uncertain signals
into a claim about a student's behaviour.

## Interface sources

- [GitLab webhooks](https://docs.gitlab.com/user/project/integrations/webhooks/)
- [GitLab REST API](https://docs.gitlab.com/api/rest/)
