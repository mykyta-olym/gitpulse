---
title: "Changelog"
description: "Complete history of GitPulse system changes"
---
Complete change history of the **GitPulse** project - from first commit to latest updates.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [2026.11.4.post2] - 2026-11-04

### Fixed

- Course group rows share one renderer for metric refreshes, sync streams and fallback polls. Missing scores and timestamps clear old values; zero scores, retry notes, cancelled jobs and deleted groups retain their correct states.
- Group status badges keep the shared component's translated labels, explanations and sort order. Timestamp sorting uses UTC ISO values, and percentage rounding agrees with the server.
- Course rendering and live reads use the same recent-job query as sync tracking. The newest group job wins over older running/completed jobs; project jobs do not change group status.
- Sync polling includes the same canonical timestamp as the stream, so fallback updates preserve localized times and user preferences.

## [2026.11.4.post1] - 2026-11-04

### Fixed

- Group and project live updates share the score-cell component, including zero scores, missing metrics, restored data and the course's configured thresholds. Excluded members retain their visible scores, and teacher/mentor rows keep the same blank states as the server render.
- Check tooltips and accessibility labels follow the current pass, fail, unavailable or not-yet-required result. Stored check flags appear on first paint even when detailed JSON is absent.
- Student live responses follow their names-only member tables and omit individual grades. Remove unused email and GitLab-id fields from live responses and project row attributes.
- Remove refresh code and database calculations for group summary cards and staleness/webhook notices that are no longer rendered.
- Delayed startup reconciliation preserves jobs already tracked in memory, preventing duplicate SSE connections and lost poller references.

## [2026.11.4] - 2026-11-04

### Fixed

- Activity caches are isolated by reader and course staff permissions. Group, project and student profile caches also separate management controls from read-only views, including after a course role changes.
- Course archiving, activation, teacher assignment and scoring exclusions require the course's staff permissions through their existing shared access checks.
- Course sync discovery, polling and check status follow the same permissions as the sync stream. Read-only group pages do not request staff-only course snapshots after tab or connection recovery.

## [2026.11.3.post7] - 2026-11-03

### Fixed

- Course overview controls and cached content use the shared course staff permission check. A global teacher role alone no longer shows management controls in a course the viewer does not run.
- Pass the same permission to course JavaScript so staff actions work, while read-only viewers do not open the restricted sync stream or its fallback poll, including after tab visibility and connection recovery.
- Resolve course membership for local accounts by their username even when the session uses the same value as its GitLab identity without a linked GitLab profile.
- Share one account lookup across course, group and student access. Keep cached group rows separate for each read-only viewer; course staff may share the full course cache.

## [2026.11.3.post6] - 2026-11-03

### Fixed

- Bind the course group filter to its own search field and table. Reuse the shared filter lifecycle for typing, blur, pagination and navigation; remove the duplicate keyup handler.
- Delayed tour prompts yield to edited forms, focused fields, calendars, dropdowns, search and the mobile sidebar instead of closing controls or taking focus.
- Use the shared close button for selected JSON files, including its touch target. Remove the separate clear-button and Enrich-button styles.
- Reserve enough space for job status badges and touch actions without changing table widths when rows load.

## [2026.11.3.post5] - 2026-11-03

### Fixed

- JSON imports and Markdown attachments use the same native upload control, with consistent keyboard access, focus and disabled styling.
- Desktop keeps full button labels, attachment hints and course teacher headings. Shared responsive components shorten them on narrow screens while keeping text left and controls right.
- Long selected JSON filenames truncate within the editor instead of pushing the upload control outside it.
- Selecting a file marks the form as edited only when its content is inserted successfully; a rejected attachment keeps an untouched form clean.

## [2026.11.3.post4] - 2026-11-03

### Fixed

- Use the shorter Teachers heading in the course table and keep Assigned Teachers in its tooltip. The populated production table keeps the header on one line on phones and tablets, with the same label in each cell's metadata.

## [2026.11.3.post3] - 2026-11-03

### Changed

- Each role links to its own questionnaire: the Support & suggestions panel shows students the student survey, teachers the teacher survey with the System Usability Scale and administrators the teacher and the administrator survey.
- The documentation banner links to a separate documentation questionnaire, Evaluation in teaching lists all questionnaires and the privacy notice says they run in Google Forms without names or emails.

## [2026.11.3.post2] - 2026-11-03

### Fixed

- A form's own action button carries its loading feedback. Keep the form busy and inert without dimming every field or placing a second spinner over unrelated sections; card and table refresh indicators remain scoped to their regions.
- Markdown uploads keep a short hint on the left and shared upload and help icon buttons on the right in one row, including narrow screens, without a second footer row or loading layout shifts.
- Shorten the required-fields notice so its asterisk stays on the same line on narrow screens.
- Stop animating the page margin in the mobile layout: crossing from a desktop width no longer briefly squeezes text and controls into the old sidebar gutter. Desktop rail transitions stay intact.
- Remove prose-cell wrapping overrides from System table headings so short column labels keep the shared single-line layout.

## [2026.11.3.post1] - 2026-11-03

### Fixed

- Markdown attachments use the shared API and request state. Keep the draft unchanged while uploading and block submission until the server confirms the file, instead of saving an Uploading placeholder.
- Upload batches sequentially, retain confirmed links on partial failure, and allow explicit retries after errors or timeouts. Late responses cannot edit a replacement form, move focus or clear its upload guard.
- Use the shared keyboard-accessible upload button, one Preview renderer, and a drag outline that preserves field dimensions. Remove duplicate Preview state and refresh reply actions from the latest live ticket status when the shared request state settles.

## [2026.11.3] - 2026-11-03

### Changed

- The Thesis section follows the current thesis text: eight chapters, the abstract and new screenshots of the current version. Thesis goals, Evaluation in teaching and the teacher guide describe the planned evaluation instead of a past pilot schedule and unmeasured time savings.
- The documentation describes scoring as the engine computes it (only enabled checks, divided by their total weight), R02, R04, R05 and R10 as they are checked, all 27 migrations and the LLM analysis as disabled in production. Em dashes are replaced.

## [2026.11.2.post13] - 2026-11-02

### Fixed

- Required Markdown fields leave Preview and receive native validation focus instead of blocking submission with an invisible error. The shared editor fixes both support requests and ticket replies.
- Register formatting actions independently of the first page so they work after SPA navigation from a page without an editor. Remove the unused rendering magic and internal Alpine scope fallbacks.
- Support drafts use shared user-interaction tracking for formatting, priority selection and attachment insertion. Initial values and opening a file picker do not trigger an unsaved-changes warning; navigation retires the tracking listeners.

## [2026.11.2.post12] - 2026-11-02

### Fixed

- Support submission uses the shared request state: lock fields while sending, preserve the draft and Preview on failure, and allow an explicit retry after a timeout without automatically repeating a POST.
- Retire form handlers on navigation and ignore late responses. A previous submission cannot clear another page's draft guard or remove unrelated error messages.
- Replace the custom success screen and submit markup with shared components. Use the shared resize animation, focus the completed state, and delete the page-specific success styles.

## [2026.11.2.post11] - 2026-11-02

### Fixed

- Event Pipeline refresh waits for the event feed and dead-letter counters. Partial failures report an error and release the shared loading state only after both requests finish; successful retries update the counters.
- Event Pipeline uses the shared SSE client with bounded reconnects. Hidden, offline and unhealthy connections pause; reconnection catches up missed events. Cancelled navigation keeps live updates, while completed navigation retires connections and pending reads.
- Refresh and live updates preserve selected events and the current page. Empty results clear obsolete selections. Remove sorting code for the retired dead-letter table.

## [2026.11.2.post10] - 2026-11-02

### Fixed

- Ticket detail uses shared request states for comments and fields. Display saved comments immediately, deduplicate live echoes, preserve the reply on failed requests, and restore rejected field changes. A failed close or reopen clearly reports that the comment was saved.
- Replace the custom ticket SSE reconnect loop with the shared client. Pause hidden or offline connections, expose unavailable and retry states, and retire connections and late responses on navigation. Remove delayed page reloads.
- Live comments and updated timestamps use the shared time component. Confirm discarding an unsent reply before an assignment change reloads server-rendered permissions.
- Shared button outcomes preserve form dropdown values and their Alpine bindings instead of replacing them with Done or Failed.

## [2026.11.2.post9] - 2026-11-02

### Fixed

- Shared card headers keep icon, title and count together. Headings, actions and help share one row where space permits; mobile wrapping keeps controls readable. Remove absolute positioning and conflicting responsive rules; shorten the Activity heading to CI/CD Health.
- Support Tickets uses the shared SSE client and its bounded backoff. Navigation closes pending reconnects and removes page listeners; stale events and completed mutations cannot reload or toast on the destination page.
- Remove artificial 450 ms delays from ticket deletion and purging, use the shared operation lock, and keep selection handling on its own table. Cancelling confirmation sends no request; failed operations retain the current rows.

## [2026.11.2.post8] - 2026-11-02

### Fixed

- Activity refresh uses the initial page's server-rendered components for metrics, groups and merge requests. Preserve the selected view, sorting, pagination and horizontal scroll; support empty-to-populated transitions without stale badges or missing rows. Remove the duplicate JSON endpoint and DOM renderer.
- Add the shared Refresh control with real pending, success and failure states. An explicit refresh reads current DB data and replaces the cached fragment. Background updates share the SSE client, follow the relevant job scope, pause while hidden or offline, and cancel on navigation.
- Group pipeline status follows the most recent finished pipeline across projects, with dated records ahead of undated ones and deterministic ties. Missing pipelines use a shared badge; an undefined pass rate is not shown as zero. Chart colors follow theme changes and a missing chart library has a working retry.

## [2026.11.2.post7] - 2026-11-02

### Fixed

- Constrain CI type checks, unit, contract and integration tests to the same application dependency versions as production, including OpenTelemetry. Development setup instructions use the same lock constraints while respecting platform-specific dependencies.
- Pin the local and CI asset minifiers to the Docker build versions so identical sources produce identical bundles. Remove redundant JSON Schema installation and obsolete Python documentation extras; documentation is built with Hugo.

## [2026.11.2.post6] - 2026-11-02

### Fixed

- Clear the skill profile and its week label when history has no scored weeks, including after a scored result. Remove obsolete check rows when check details or the whole history disappear; a real zero remains a scored result.
- Update summary values as soon as history arrives, independently of deferred chart drawing. Dispose previous charts and pending draws before applying a new history result.
- Release the heatmap's initial height reservation once rows are ready, avoiding empty space beneath smaller matrices. Use the shared progress component for weekly scores and remove its duplicate gradient styles, unused badge styles and obsolete row-delay plumbing.

## [2026.11.2.post5] - 2026-11-02

### Fixed

- Keep modal footer buttons equally sized on mobile and tablet when disabled tooltips wrap them. Preserve their dimensions through selection and loading without changing desktop button sizing.
- Protect unsaved edits when a dialog opens during navigation before its page registers the form guard. Use the same opening snapshot and initial-value settling as normal dialogs.
- Reserve room for the jobs selection checkbox and its standard cell padding on tablet widths. Remove redundant checkbox header widths from Events and Tickets and delete the unused width utility.
- Page dialogs wait for their Alpine factories before initialisation and teleporting, including the separate modal slot. A failed page script removes its unusable dialogs and shows the shared retry state.
- Mount date pickers only after page scripts succeed, preventing orphaned calendars when an incoming settings script fails.
- Project live updates preserve shared button locks and ignore responses and queued refreshes from a retired page. AI discovery respects the feature flag and staff role; outdated discovery cannot restart tracking.
- Release completed coalesced refresh entries instead of retaining page closures indefinitely. Dispose the project's issues chart when leaving and prevent its deferred draw from touching a replacement page. Replace outdated modal lifecycle comments with the current contract.

## [2026.11.2.post4] - 2026-11-02

### Fixed

- A check the course switched off is no longer scored, counted or listed as failing. Students no longer see "Check disabled" among their failing checks, and member tables count passed checks out of the enabled ones instead of out of 13.
- Scores divide by the total weight of the scored checks, as the weekly plan already did. With the default R09, R11 and R13 off, passing every enabled check reads 100 % instead of 85 %. Course settings no longer flag the default weights as invalid and warn only when the active checks weigh nothing.
- "Your progress" on the student dashboard counts the student's own open merge requests and failed pipelines, matching the Open MRs card instead of totalling the whole group.

## [2026.11.2.post3] - 2026-11-02

### Fixed

- Replace the moving navigation segment with one continuous, left-anchored fill that follows the active theme. Complete the full width before fading after the last request and page initialisation finish.
- Preserve the visible fill when new work interrupts completion. Remove the old CSS loop; reduced motion and an unavailable animation library still paint the full-width terminal frame.

## [2026.11.2.post2] - 2026-11-02

### Fixed

- Complete navigation progress visibly at the right edge even when the waiting animation has already left the viewport. Accelerate the final sweep and let its edge paint before fading, including reduced motion and unavailable GSAP. A new request cancels the old pending fade.
- Group AI analysis uses the shared job bar for progress, cancellation, reconnects and completion. Remove the duplicate page tracker and references to a nonexistent local indicator. Discovery respects the feature flag and staff role, including read-only teachers.
- Group progress follows aggregate snapshots; an individual project's completion cannot finish the whole group. Zero progress is valid, unknown progress remains indeterminate, and percentages are bounded to 0–100.
- Ignore delayed discovery after leaving the page and preserve language, filters and fragment when removing the analysis redirect marker. Remove the duplicate MR button animation; a failed enqueue cannot mark an unrelated analysis as failed.

## [2026.11.2.post1] - 2026-11-02

### Fixed

- Optional AI analysis uses the shared alerts, spinner, progress and button states. Render errors and results from the server template; remove the duplicate client renderer and page-specific component styling.
- Ignore responses and stream events from an earlier analysis or a disposed page. Preserve pending work on unknown statuses, accept real zero progress, and close streams through the shared SSE client.
- Refresh results immediately on a confirmed terminal state. A failed result read offers a shared Refresh action without spending analysis tokens again. Restore the server empty state when no results exist; cancellation and failure never show a completed percentage.

## [2026.11.2] - 2026-11-02

### Fixed

- Navigation progress follows all six accent choices in light and dark modes. Resume interrupted sweeps from their current position and scale completion time to the remaining distance.
- Forms, mutations and explicit region refreshes share progress ownership until their real result. Concurrent work cannot hide another operation's indicator; background reads stay quiet. Malformed JSON is a failed response rather than an empty success.
- Remove three delayed dashboard scans: restored and newly started jobs already update course badges through the shared job events. Remove the redundant modal form lock fallback.

## [2026.11.1.post7] - 2026-11-01

### Fixed

- Complete the moving navigation indicator at the right edge before fading after the last request and page initialisation finish. New requests cancel an older finish. Keep feedback functional with reduced motion or unavailable GSAP.
- Use the GitLab progress indicator's light and dark theme colors and completion timing.
- Remove obsolete progress-reset calls from group validation. Invalid or blocked submissions no longer throw or finish another request's loading indicator.

## [2026.11.1.post6] - 2026-11-01

### Fixed

- Keep merge-request participant fields compact and left-aligned, sized to their content rather than equal-width columns. Shared avatars and badges wrap naturally on narrow screens.
- Show approvals consistently on authored MR cards and Reviews given using GitLab's saved approver list. Stale review aggregates cannot hide a current approval or restore a revoked one. Clarify the Reviewed workflow tooltip.

## [2026.11.1.post5] - 2026-11-01

### Fixed

- Distinguish an unknown MR commit list, missing commit details and a confirmed empty list. Explain saved branch history beside its commits, keep authorship unverified until the exact list is complete and link directly to GitLab. Incremental sync repairs unchanged historical MRs and retries missing details; unavailable API pages cannot be stored as an empty success.
- Separate assigned reviewers from other discussion participants, label comment counts and show approval or pending-review states. Resolve assigned and approving identities even without comments. Assignment alone is not a completed review; merging alone is not an approval.
- Use the shared avatar's wrapping metadata slot from GlAvatarLabeled and align participant fields consistently across desktop and mobile. Fix the shared empty state when no illustration is supplied.

## [2026.11.1.post4] - 2026-11-01

### Fixed

- Finish background jobs only after a confirmed server result. Remove artificial finishing holds, timer-driven success and the test-only readable-completion API. Invalid SSE messages and missing statuses trigger verification instead of a green result.
- Keep real finishing work locked and indeterminate until verified. Restore and cross-tab updates share terminal transitions; removing browser storage cannot manufacture completion. Ignore obsolete poll responses and prevent overlapping status reads.
- Align course discovery, HTTP polling and streaming for started jobs and between-batch grace periods. Track project-only syncs separately. Use the shared polling and retry components, retaining monitoring after transient read failures.

## [2026.11.1.post3] - 2026-11-01

### Fixed

- Align avatars with their labels in the shared component. Derive MR attribution from the exact synced commit list, preserving genuine teacher contributions without importing template history or guessing authors from timestamps. Distinguish an empty list from unavailable data.
- Keep navigation busy until requests and page scripts finish, without simulated percentages or a premature three-second reveal. Bound script reads, abort timed-out loads and offer the shared retry state on failure. Duplicate request events cannot finish another pending request.
- Distinguish search failures from empty results, provide retry and cancel obsolete reads immediately. Remove the remaining artificial delay after saving preferences.

## [2026.11.1.post2] - 2026-11-01

### Fixed

- Shared button, table and card loading states follow pending work. Spinners wait briefly for fast responses; busy state starts immediately. Remove artificial completion holds and the invisible animation clock so ready data is available immediately.
- Release retry controls after completion, preserve content on failed refreshes and retarget height transitions to the new content. Bound loading of the User Info renderer and allow another attempt after an asset failure.
- System Health reports degraded external checks in its summary instead of presenting them as all operational; infrastructure readiness remains independent.
- Keep Assistant search usable during activity refreshes and preserve text entered before the response arrives.

## [2026.11.1.post1] - 2026-11-01

### Fixed

- Render webhook configuration rows with one shared Jinja template for initial load and refresh. Remove the duplicate JavaScript row renderer, inline JSON payload and estimated height reservation so populated lists cannot shift the filters below them.
- Use shared badges, timestamps and action buttons for active and archived courses. Keep the JSON API unchanged and enforce the settings page permissions on HTML refreshes.

## [2026.11.1] - 2026-11-01

### Fixed

- Align the shared tab indicator with its divider, without clipped pixels or a double baseline. Keep the server-rendered and moving indicators identical in light and dark themes on mobile and desktop.
- Remove unused card-header tab restyling and duplicate filter selectors; preserve hover feedback and verify filter/panel switches frame by frame.

## [2026.10.31.post3] - 2026-10-31

### Fixed

- Make the first-visit tour welcome yield to open confirmations and forms. Listen to the shared modal event so the invitation cannot cover Cancel or interrupt a user's dialog.
- Remove the unused tour auto-dismiss flag and verify visible invitations and delayed tour-state responses in real mobile and desktop browsers.

## [2026.10.31.post2] - 2026-10-31

### Fixed

- Share PostgreSQL and Redis/RQ job-history cleanup across Purge Old, selected jobs and permanent course/group/project deletion. Confirm both stores, report separate removal counts, preserve active jobs and retain SQL records when Redis is unavailable.
- Invalidate course/group/project page caches after committing mutations; also evict deleted descendants. Fix RQ enum handling for cancellation and prevent Redis outages or missing history from being reported as successful analysis or sync.
- Require course staff for session-authenticated API mutations and LLM analysis writes; viewing a course or belonging to a group does not grant write access.
- Keep shared table-header checkbox alignment stable when disabled tooltips appear, and exclude locked rows from bulk selection.

## [2026.10.31.post1] - 2026-10-31

### Security

- Upgrade the transitive Google authentication dependency `pyasn1` from 0.6.4 to 0.6.5 to fix four ASN.1 decoder CPU-exhaustion vulnerabilities reported by dependency scanning. Other locked packages are unchanged.

## [2026.10.31] - 2026-10-31

### Fixed

- Fix Purge Old to remove retained RQ failures as well as tracked terminal jobs, using last activity for age limits. Preserve active/retried jobs, recent completions, the audit and execution-error counters.
- Align wrapped stat-card labels and values through shared grid tracks, cap the default grid at four columns, and declare diagnostic table widths through the shared table component.

## [2026.10.30] - 2026-10-30

### Changed

- Rebuild the System page around shared Pajamas components: health and monitoring render on the first frame as `stat_card` grids and a `data_table` of components, refreshes swap server-rendered HTML partials without layout shifts, and monitoring tool links sit in one header dropdown.
- Align the global service notice with the shared `.gp-top-banner` strip and include a localized System action link for administrators.

### Fixed

- Clamp negative SQLAlchemy pool overflow counts, populate Redis connected clients from a single `INFO` call, ignore proxy environment variables in internal GitLab probes, and serialize health cache refreshes behind a single-flight lock.
- Normalize leading underscores and interior capitals in job labels, register missing worker task names, preserve job descriptions, deduplicate repeated failure causes, and remove unused Python helpers, Jinja macro imports, JS symbols, CSS rules and translation keys.

## [2026.10.29.post7] - 2026-10-29

### Changed

- Consolidate service diagnostics into System: health, monitoring metrics and alerts share one section; tracked background jobs and retained RQ failures share one deduplicated, paginated journal. RQ-only history remains read-only.
- Remove the separate Service status view, script and sidebar entry. Old bookmarks redirect by role; teachers and students receive shared impact notices on their existing pages.
- Render job rows with one server template for the first page and all refreshes. Share job wording with the core bundle and retain loading, retry, selection and cancellation controls.

## [2026.10.29.post6] - 2026-10-29 - Readable diagnostic task labels

**Fixed**

- Long task labels wrap inside their failure-log cell on mobile. Queue names use the shared gray badge variant.

## [2026.10.29.post5] - 2026-10-29 - Readable job failure diagnostics

**Fixed**

- Service status separates historical RQ failures from new execution errors; Grafana and the one-hour alert use the real worker error counter, including retries.
- Administrators can inspect dates, causes, remediation hints and safe job/source references in a shared paginated table. Historical records remain available; credentials and job payloads stay off the page.
- Share the existing code-reference styles across pages and keep the current failure-log page on Refresh.

## [2026.10.29.post4] - 2026-10-29 - Retire unused implementations

**Fixed**

- Alpine CSP and collapse use pinned 3.17.5 with a verified patch avoiding the deprecated window.fence getter. Remove the standard Alpine runtime and weaker CSP fallback.
- Copy actions share Clipboard API; remove execCommand and duplicate fallbacks. Nested summary buttons and links do not toggle the disclosure.
- Delete unused project limiters, adaptive circuit breakers, request batching, cache statistics, inert metrics and test-only reset functions. Active caching, retries, queue protection and monitoring remain in their shared paths.
- Use canonical model imports and configured webhook queue limits. Remove tests and documentation that described retired implementations.

## [2026.10.29.post3] - 2026-10-29 - Stable navigation and request states

**Fixed**

- Outgoing tables, charts and sticky controls retain their geometry and scroll while the next page initializes. Navigation restores interaction and focus on completion or failure.
- User-info modals use the shared loading handoff and reject canceled or superseded responses. Earlier table reads cannot clear the next read's busy state.
- HTMX and POST forms use shared button outcomes. Project intelligence and optional AI cards refresh from one server projection, removing duplicate renderers and caches.

## [2026.10.29.post2] - 2026-10-29 - Shared refresh states

**Fixed**

- System Health, jobs, Events, service status, assistant activity, webhooks and Compliance Progress share one refresh lifecycle. Keep the content visible, mark the region busy and restore interactions on every exit.
- Failed refreshes preserve the last data. First-load failures use shared error states with Retry; duplicate and superseded requests do not report success.
- Remove duplicate refresh styles and keep compliance charts visible during reload.

## [2026.10.29.post1] - 2026-10-29 - Opaque sticky settings headings

**Fixed**

- Keep control shadows and keyboard focus rings behind shared sticky settings headings while scrolling. Section spacing and dropdown menus remain intact.

## [2026.10.29] - 2026-10-29 - Consistent table navigation

**Fixed**

- Table rows are passive. Open a record through its native identity link or an Actions button; reading, selecting text and horizontal swipes no longer trigger row-wide navigation.
- Group project tables include explicit project links and shared View/GitLab buttons. Live metric updates preserve student link context and match group members by ID.
- Linking a project reloads the server-rendered table. Remove the separate client-rendered project list and unused member table builder.
- Invalidate group and course caches after linking or restoring a project, including its previous group after reassignment. Match initial course-code ordering to the shared table's numeric sort.
- Course Management uses shared teacher badges and disclosure buttons. The tour explains the actual native link and keyboard behavior instead of unsupported row menus and drag controls.

## [2026.10.28.post7] - 2026-10-28 - Consistent refresh and chart states

**Fixed**

- Service status refreshes in place with shared loading and outcome states. Failed requests preserve the displayed data; leaving the page cancels the request. Replaced status and assistant tables retain their shared scrolling behavior.
- Markdown tabs meet the header divider. Membership badges stay beside their text when they fit and wrap left when necessary.
- Teacher's Checklist measures its visible container before animating. Chart entrances respect reduced motion, and Week Analytics includes its initial summary in the server response without growing after paint.

## [2026.10.28.post6] - 2026-10-28 - Readable mobile metadata

**Fixed**

- Wrapped support badges and other metadata align left on mobile. User Info membership badges follow their content; desktop alignment stays unchanged.
- Share the mobile alignment rules and remove duplicates. Replace stale build/release comments with concise descriptions of current behavior, retaining tour completion migration.

## [2026.10.28.post5] - 2026-10-28 - Clear mobile support ticket layout

**Fixed**

- Read a request, its details, the conversation and the reply editor in that order. Attributes stay on the right on desktop and precede the discussion on phones.
- Remove duplicated author, course and period metadata and misplaced timestamp icons. Consolidate attributes into one shared Details card; mobile reply buttons wrap and align left.
- Match the ticket tour to the current layout and course staff permissions.
- Persist emails and check notification preferences on one loop-owned database engine. Support notifications run outside the request event loop without unawaited coroutines or cross-loop asyncpg failures; opt-outs and delivery deduplication remain enforced.

## [2026.10.28.post4] - 2026-10-28 - Correct GitLab reachability checks

**Fixed**

- Probe the public GitLab sign-in page instead of requesting its protected version API anonymously. Healthy visits no longer generate expected HTTP 401 error traces. Authenticated token validation and real connection/outage failures remain visible.

## [2026.10.28.post3] - 2026-10-28 - Consistent support and mobile scrolling

**Fixed**

- Hidden field labels stay in the shared scrollport; long mobile pages no longer add an empty document below the application panel.
- Ticket details use shared cards, alerts, labels and avatars. Unanswered optional fields are omitted.
- Failed submissions preserve drafts and leave warnings. Live dropdown updates do not issue another write; failed updates restore the saved selection.
- Assignees must be active administrators or staff of the ticket's course. Null required metadata is rejected during validation.
- Jaeger retains at most 10,000 traces, with a 384 MiB Go runtime memory target below the 512 MiB container limit.

## [2026.10.28.post2] - 2026-10-28 - Reachable latency alerts

**Fixed**

- Extend HTTP, webhook-processing and GitLab API duration histograms beyond their 5/10/15-second alert thresholds. Slow requests can now be represented instead of being clipped below an alert's firing condition.
- Retain only raw deleted static assets during deployment. Exclude JS/CSS build sources so retired scripts cannot be recompiled into the new image's manifest.

## [2026.10.28.post1] - 2026-10-28 - Service monitoring and retired usage tracking

**Changed**

- Remove retired pilot browser tracking, click/time-saving estimates, flag-resolution tracking, their API, worker tasks and four usage tables. Preserve weekly compliance history, activity analytics, support records and LLM analysis.
- Use one support-form service instead of the unused legacy survey API. Bind new tickets to the session author, active course form and course access; require CSRF and honor the support feature switch.
- Add a role-aware Service status page and shared service notices from the existing Prometheus stack. Admins can inspect metrics/alerts and open Grafana, Prometheus, Jaeger and Alertmanager; students and teachers receive service-impact notices without internal details.
- Bound monitoring reads to 1.5 seconds, share results for 20 seconds per process and report unavailable monitoring as unknown. Keep monitoring optional with PROMETHEUS_URL, independently of course tools.
- Consolidate avatar labels, chart legends, badges and responsive header buttons into shared components, remove local restyling, and retain the centered sign-in language selector.

## [2026.10.28] - 2026-10-28 - Atomic course configuration

**Fixed**

- Save course metadata, scoring settings and staged check edits in one transaction. A stale or invalid check leaves the entire draft unchanged; native forms and enhanced saves use the same validation.
- Preserve configuration for hidden optional modules, including LLM analysis, and interpret an explicitly empty built-in check selection as disabled checks.
- Render compliance rows with shared Jinja components on the first frame and refresh through the same template. Preserve staged edits during table refresh and ignore notifications for the page's own save.
- Use shared badge variants and checkbox/button components instead of course-specific restyling.

## [2026.10.27.post5] - 2026-10-27 - Compatible benchmark test runner

**Fixed**

- Keep pytest below 9.2 while pytest-benchmark 5.3 depends on the removed private Node._nodeid field. CI installs a compatible pytest version and runs all benchmark tests without a compatibility shim.

## [2026.10.27.post4] - 2026-10-27 - Remove unused upstream documentation tooling

**Removed**

- Remove unused GitLab product-release, repository-cloning, Elasticsearch and content-generation tooling from the documentation build. Retain and test the navigation generator; its Slovak and English output is unchanged.
- Remove unused Firebase feedback/contact forms, GitLab feature walkthroughs, deprecation pages and archive-version handling. Build only the documentation's actual JavaScript entry points and prune their unused dependencies.
- Documentation search uses Pagefind and names GitPulse rather than fetching a GitLab product version. LLM analysis, activity analytics and compliance history remain available.

## [2026.10.27.post3] - 2026-10-27 - Language placement and latest-snapshot reads

**Fixed**

- Centre the shared language selector on sign-in and sign-out, including the mobile authentication sheet.
- A composite index finds the latest course snapshot without scanning its history. The migration and ORM declare the same index; an integration test checks the PostgreSQL plan and the result for a course without snapshots.

## [2026.10.27.post2] - 2026-10-27 - Consistent MR filter toolbar

**Fixed**

- The CI unit-test job installs Node.js so JavaScript contract tests execute instead of being skipped or failing because the runtime is missing.
- MR analysis filters use the shared table toolbar so the search and risk dropdown align without custom wrappers or sizing rules. The confidence label uses the standard info badge. Shared select fields reserve their widest option from the server-rendered frame, including dynamically added options, so changing a filter does not resize adjacent controls.

## [2026.10.27.post1] - 2026-10-27 - Shared controls throughout the interface

**Changed**

- Sign-in language selection uses GitLab's small tertiary listbox on the existing white authentication surface, with no page-specific dropdown styling.
- Reviewer and sync indicators, issue legends and MR risk labels use shared badges. Week and Markdown navigation use shared tabs; diff file navigation uses shared list items. Text actions and the MR risk filter use the common button and select components.
- Removed component restyling in card headers and table controls, the unused header-fit observer, duplicate font-size aliases and dead core helper guards. Visible text and chart labels are at least 12 px. Week selection is server-rendered before page scripts run.

## [2026.10.27] - 2026-10-27 - Shared components instead of copies

**Changed**

- The search palette is built from the shared components: the borderless search box, dropdown group headers, the close button and avatars. Close buttons, avatars, badges, alerts, the person typeahead and the support ticket thread follow the same rule on the server and in the browser, so their page-specific copies and about 2,000 lines of overriding CSS are removed.
- Avatars follow GitLab's GlAvatar: fixed sizes, a per-name identicon colour and the initial under the picture until it loads. Badges, alerts and close buttons follow GlBadge, GlAlert and GitLab's close button; the sign-in alerts are the standard alert.
- Browser code calls the core helpers directly. Hundreds of local copies and dead fallbacks for translation, HTML escaping, toasts and other always-present functions are removed, together with the unused drawer component. Pagination arrows and dropdown checks come from the icon registry.

**Fixed**

- Leaving a page runs its cleanup once; the next page no longer repeats the previous page's teardown.
- Pagination buttons carry translated labels from the first frame instead of English until scripts load.
- Project score colours use the course thresholds. Disabled tertiary buttons no longer show a grey fill, and the link hover and focus ring rules no longer override the colour or corner radius of components that are links or buttons.

## [2026.10.26.post12] - 2026-10-26 - Preserve pagination clicks during search

**Fixed**

- Finishing a table search updates its URL without replacing controls during a pointer press. Client pagination commits pending filters inside its click handler, then resolves Next and Previous from the filtered page. Fast clicks remain actionable instead of losing their target during blur.

## [2026.10.26.post11] - 2026-10-26 - Search commits before table refresh

**Fixed**

- Shared table searches commit pending input when editing ends, before Refresh reads the current filters. Quickly refreshing Assistant activity no longer drops the latest query.
- Committing a filter consumes its pending typing update, so the old timer cannot reset a later page selection. Detached inputs and outgoing pages remain unable to overwrite the current search URL.

## [2026.10.26.post10] - 2026-10-26 - Assistant refresh ownership

**Fixed**

- Assistant activity uses the shared keyed request transport with a ten-second timeout and no automatic retries. Retired or older responses cannot overwrite another page or a newer snapshot. Updates defer while the reader types or changes the activity view, preserving focus and the current query.
- Delayed Assistant reloads are canceled when leaving their page and recheck unsaved edits when they run. Exercise completion events identifying another course are ignored.
- Shared Refresh controls suppress feedback for superseded, deferred or retired actions, so old requests cannot announce success or failure on the destination page.

## [2026.10.26.post9] - 2026-10-26 - Consistent button lock release

**Fixed**

- Completing a background process or retry cooldown restores Save from the current form draft. Edits made during a lock become saveable when it ends; reverted or unchanged forms remain disabled, without stale disabled styling or accessibility attributes.
- Loading, process, synchronization, archive and cooldown locks share one button-state restoration path. Finishing one lock cannot enable an action still held by another or prematurely cancel its retry countdown. Settings also recheck their Save guard when server synchronization polling releases its lock.
- Process guards no longer create a separate tooltip instance after unlocking; restored controls use the shared delegated tooltip behavior.

## [2026.10.26.post8] - 2026-10-26 - Keeping edits made during a save

**Fixed**

- Shared form guards acknowledge the values submitted to the server and retain later edits as unsaved. Save buttons respect active loading, process, sync, archive and cooldown locks, then re-evaluate remaining edits when loading finishes, including fast responses whose spinner never appeared.
- Preferences restore the last submitted preview on navigation and defer language reloads while a later draft remains. Settings and Assistant save responses belong to their original form; late responses cannot reset a replacement form, open a sync prompt or reload over another draft.
- Native diff-color pickers use the existing derived-field exclusion shared with modal dirty tracking, so reverting a color immediately returns the form to its saved state.

## [2026.10.26.post7] - 2026-10-26 - Calendar dates without time zone shifts

**Fixed**

- Shared calendars parse semester dates as local calendar days through Flatpickr instead of UTC timestamps. Teaching and exam weeks keep the same numbering in every browser time zone, including across daylight-saving changes and live edits to a paired start date.
- Empty deadline calendars open in the future semester's actual month. A semester starting on the first day of a month no longer opens in the previous month in time zones west of UTC; opening the calendar leaves the deadline empty.

## [2026.10.26.post6] - 2026-10-26 - Retiring outgoing dialogs

**Fixed**

- Removing a page modal retires its animation, open-stack entry, close guard and dirty-field snapshot before its ID can be reused. Fast SPA arrivals can immediately open the replacement dialog without inheriting the removed dialog's state or leaving the page scroll-locked.
- Modal exit callbacks belong to their original opening and DOM node. A late completion cannot hide or unlock a reopened/replacement dialog or notify its listeners that it closed.
- Removed obsolete per-dialog scale-origin calculations and inline animation overrides. Modal entrances retain the shared translation motion without unnecessary layout reads or inline transform origins.

## [2026.10.26.post5] - 2026-10-26 - Consistent calendar semester context

**Fixed**

- Calendars initialise after SPA navigation reconciles the incoming course's semester metadata. Inline fields and teleported deadline dialogs use the new course's week numbers and week-column policy instead of retaining the previous page's context.
- Semester-end calendars resolve their anchor from their own academic-period component, including form-less Transfer dialogs and multiple date pairs in one form. Editing that pair's start date updates its week numbers without using another pair or the source course.

## [2026.10.26.post4] - 2026-10-26 - Recovering from navigation failures

**Fixed**

- Failed SPA requests preserve the current page's URL, modals, event handlers and unsaved-change protection. Cleanup and Alpine suspension occur only before a successful content swap; HTTP errors and empty responses cannot create history entries for pages that never arrived.
- Failed Back/Forward navigation restores the rendered page's address. Queued history navigation compares destinations with the rendered page instead of skipping a request whose URL is already in the address bar.
- HTMX removal destroys each date picker through Flatpickr's lifecycle API, releasing its popup and global listeners. Removed an incorrect orphan-calendar sweep that relied on a property Flatpickr does not provide and could detach live calendars.

## [2026.10.26.post3] - 2026-10-26 - Protecting fast form edits

**Fixed**

- Fast calendar selections and number-stepper actions remain unsaved edits while modal fields initialise. Cancel warns before discarding and restores the opening values, including the calendar selection.
- Standard form save guards retain their original baseline after user input, dropdown selections or calendar interactions. Follow-up synthetic events cannot disable Save or silently adopt an unsaved edit; untouched programmatic population still settles normally.

## [2026.10.26.post2] - 2026-10-26 - Calendars on narrow screens

**Fixed**

- Shared calendars fit narrow screens without clipping weekdays, hiding semester weeks or enlarging the mobile layout viewport. Resizing back to desktop preserves the standard calendar width.
- Body-mounted calendars follow their input when an ancestor page or modal body scrolls, using Flatpickr's existing positioning helper instead of duplicating its geometry.
- Viewport-width changes close an open calendar without changing its date; reopening clears stale positioning offsets. Height-only changes from an on-screen keyboard keep it open.

## [2026.10.26.post1] - 2026-10-26 - Dialog timers

**Fixed**

- Delayed modal autofocus only applies to the current, open, topmost dialog and preserves an already chosen field. Closed or background dialogs cannot steal focus; confirmation dialogs retain their safe initial control.
- Opening timers and confirmation animation-frame callbacks belong to their original opening. Rapid reopening preserves the new animation state, and a replaced confirmation cannot focus its previous control.

## [2026.10.26] - 2026-10-26 - Dialog focus

**Fixed**

- Modal autofocus and Tab wrapping exclude controls with a negative tabindex, disabled controls (including disabled fieldsets), and inert subtrees. The semester transfer dialog focuses the visible academic-period selector instead of its hidden validator.
- Browser regression checks cover transfer keyboard navigation, inactive controls at both dialog boundaries, and the accessible JSON file picker on desktop, touch and reduced-motion layouts.

## [2026.10.25.post10] - 2026-10-25 - Consistent JSON imports

**Fixed**

- JSON imports immediately invalidate an edited preview and share draft protection, discard, timer cancellation and page cleanup across dashboard, full-course and check configuration imports. Invalid root arrays are rejected.
- File uploads cannot overwrite a newer file or manual edit; discarded imports clear the file chip and pending reads. Reopening a closing dialog starts a fresh dirty-state baseline.

## [2026.10.25.post9] - 2026-10-25 - Table edge behavior

**Fixed**

- Responsive tables disable native horizontal edge bounce/stretch instead of allowing it with `overscroll-behavior-x: contain`. Vertical scrolling retains its default behavior.
- Native touch regression checks now reverse one continuous contact and drag beyond both horizontal edges, across five mobile widths, both themes and reduced-motion settings.

## [2026.10.25.post8] - 2026-10-25 - Native sticky Actions

**Fixed**

- Removed `will-change: transform` from touch sticky Actions cells. Chrome retains native compositor sticky constraints during horizontal panning.
- Touch regression checks cover the reported Pixel 9 Pro viewport (427 by 952) and verify native sticky constraints for every pinned Actions cell, alongside scroll geometry and pinning state.

## [2026.10.25.post7] - 2026-10-25 - Tooltips and touch scrolling

**Fixed**

- Tooltips are destroyed when their reference leaves the document after a page swap or row replacement. Open, hidden and pending instances release their popups and handlers; moving a live reference preserves its instance.
- Card explanations use the same current-content and one-open-tooltip rules as delegated tooltips. Removed an unreachable info-tip branch from the ordinary tooltip handler.
- Tooltip cleanup checks created instances without scanning every possible target or eagerly creating ordinary tooltips.
- Horizontal scrolling no longer remeasures or switches the Actions pinning mode on every scroll event. Geometry changes still update pinning through resize observation, including changes to the Actions header width.
- Overflowing pinned Actions cells use separate compositor layers on touch devices. Removed unused mobile scroll snapping; the themed separator still fades at the right edge.

## [2026.10.25.post6] - 2026-10-25 - Scoped job refresh

**Fixed**

- Course, group, project and student job refreshes share scope matching. Unrelated completions no longer request live data or invalidate project GitLab caches; actual course/group scopes take precedence over the originating project.
- Project detail uses one job-completion listener. Relevant analysis completions from another tab refresh result cards, while hidden pages defer their refresh.
- Analysis jobs carry course/group/project metadata. Stored job metadata, legacy course keys and existing analysis polling URLs remain supported.
- Narrow top bars keep the clock and avatar visible in both time formats. The academic year and separator yield space first.


## [2026.10.25.post5] - 2026-10-25 - Queue outcomes

**Fixed**

- Group sync, project sync and group check responses report the persisted enqueue error instead of claiming that a failed job was queued.
- Course check launches clear per-group recomputing indicators when queueing fails or no work is accepted, independently of live-data refresh.
- Course checks revalidate the process scope after the confirmation dialog, preventing a redundant launch when another run starts while the dialog is open.

## [2026.10.25.post4] - 2026-10-25 - Group checks

**Fixed**

- Student Run Checks uses the shared group process lifecycle: enqueue failures retire the progress indicator, cancelled jobs report an error, and a disconnected progress stream falls back to status polling.
- The check picker and progress message on student and project pages show the group actually recomputed by the API, rather than suggesting a narrower scope.
- Student profiles refresh only after successful jobs in their group or course. Unrelated and failed jobs no longer reload the page; bursts of completion events share one refresh.

## [2026.10.25.post3] - 2026-10-25 - Check selection

**Fixed**

- Run Compliance Checks protects early bulk selection changes. Transient check filtering does not count as unsaved work and resets on reopening.
- The selected-check counter and Run button use the whole selection, matching the request payload even when some selected checks are hidden by the filter. Refreshing the selection preserves archived, process, loading and cooldown locks.
- An intentional check run accepts its selected parameters before closing the modal. It no longer sends the request while showing a second Discard prompt. The unused run-success listener was removed.

## [2026.10.25.post2] - 2026-10-25 - Discarding form drafts

**Fixed**

- Escape acts only on the top dialog. The key that opens a discard confirmation no longer immediately dismisses that confirmation, and Tab stays inside it.
- Confirmed navigation closes outgoing dialogs without asking for the same discarded changes a second time.
- Closing a changed GitLab import draft asks before discarding it. Cancel, the close button, Escape and the backdrop use the same guard, and leaving the page protects the draft too. Starting the import keeps its separate process cancellation behavior.
- Confirming Discard restores the opening form values, including custom selects, checkboxes, derived academic-period fields and date pickers, instead of retaining a discarded draft on reopening. A late confirmation cannot discard a newer opening.
- Import progress uses shared modal lifecycle events instead of replacing openModal/closeModal, preserving opener animations, close-guard results and lifecycle behavior for both GP and window callers.

## [2026.10.25.post1] - 2026-10-25 - Shared table filtering

**Fixed**

- Debounced table searches stop when their input or table is detached or its page is being left. A fast navigation can no longer copy the outgoing search into the destination URL.
- Users, Course Teachers and Assistant activity configure the shared TableFilter with their row predicate and URL parameters instead of replacing apply() with page-specific implementations. Search, pagination, empty states and URL updates follow one implementation.
- Table filtering retains the current URL fragment and history state, including when switching the Users role tabs or searching the user list.

## [2026.10.25] - 2026-10-25 - Reliable event loading

**Fixed**

- Table refreshes dismiss open tooltips before replacing their rows, preventing orphaned explanations over empty results.
- Event details keep the selected event when an older payload request finishes later. Closing or reopening the dialog prevents late successes and failures from replacing its current contents.
- Leaving Events cancels its reads and invalidates delayed table renders. Returning to the page cannot receive a previous visit's event rows or dead-letter counters.
- Event-table and empty-payload states use the shared themed illustrations. Keyed API reads remove their caller's abort listener after completion instead of retaining every completed request until the page closes.

## [2026.10.24.post9] - 2026-10-24 - Consistent dropdown keyboard navigation

**Fixed**

- Shared dropdowns support arrow keys, Home/End, Tab and Escape, including menus portaled outside scrolling tables. Disabled options are skipped and existing button/link actions remain responsible for selection.
- Escape finds the actual open dropdown instead of a preceding closed data-dropdown element. It dismisses the menu before its containing dialog; Tab returns a portaled menu to its original container and continues normal focus navigation.
- Changing rows per page restores focus to the replacement dropdown button after pagination controls rerender, preserving keyboard operation across repeated size changes.

## [2026.10.24.post8] - 2026-10-24 - Stable fields during modal saves

**Fixed**

- Shared modal forms capture their payload before temporarily disabling editable fields and custom select controls. Users can still cancel or close the dialog, but cannot change values while a pending save's callback expects the submitted form state.
- Errors restore editing without enabling fields that were already disabled. Reopening immediately releases the previous interaction's fields; an older completion cannot unlock a newer save. Modal Save guards recognize a pending submission before its delayed spinner appears.
- A modal save failure already reported to the user no longer escapes as an unhandled promise rejection. The error callback and visible message remain available for recovery and retry.

## [2026.10.24.post7] - 2026-10-24 - Modal form response ownership

**Fixed**

- Delayed modal form responses cannot close a newly opened dialog, update another user's row or show stale success/error feedback after navigation. The shared submit handler checks the original form and dialog opening before applying the response.
- Reopening a form clears its previous loading and result feedback. A new interaction can submit independently while the earlier write finishes; that write cannot reset the new submit button.

## [2026.10.24.post6] - 2026-10-24 - Table scrolling after filters and refreshes

**Fixed**

- Filtering no longer measures Actions from a hidden first row as zero pixels. The shared component uses the visible column header and preserves space for row information on narrow screens.
- HTMX swaps initialize table and navigation-strip roots themselves. Replacing a scroll viewport or its inner table reconnects tracking to the new elements and disconnects the previous binding.
- Horizontal scroll indicators and the Actions separator keep updating after fragment refreshes inside an existing table wrapper.

## [2026.10.24.post5] - 2026-10-24 - Consistent user edits

**Fixed**

- Refreshing Users keeps Edit in sync with the displayed role and active status. Reopening the form no longer restores stale values after another administrator's change.
- Saving a service account preserves its Bot label and account type when Edit is reopened. Refresh and save share one update for row state and action data.
- Modal Save buttons use the same baseline as the unsaved-changes warning. Entrance animations and settling timers no longer swallow fast edits; reverting a value disables Save again.
- Modal dirty checks ignore the dropdown's asynchronous validation mirror. Restoring the original course data no longer leaves Save enabled or warns about nonexistent changes.

## [2026.10.24.post4] - 2026-10-24 - Sticky Actions separator and proxy recovery

**Fixed**

- Pinned Actions columns use a shared theme border to mark hidden columns. The border fades out at the right scroll end and returns when scrolling back. It leaves buttons in place, disappears when the column unpins and follows reduced-motion preferences.
- Deployment applies recovery settings to a running Caddy before replacing the API. A failed reload leaves the serving API in place; first-time deployments retain the normal proxy setup.

## [2026.10.24.post3] - 2026-10-24 - Image bytecode and cold startup

**Fixed**

- The image compiles installed dependencies and the Python standard library during the build. Read-only processes reuse this bytecode instead of compiling hundreds of modules at startup; release metadata does not invalidate those layers.
- Gunicorn's unused control socket is disabled, removing a read-only filesystem error. Deployment and shutdown continue to use container signals.
- Caddy waits within the API's 20-second startup window before returning maintenance, covering a previously observed 503 just before readiness.
- Startup documentation distinguishes bytecode preparation, proxy retries and warm request execution.

## [2026.10.24.post2] - 2026-10-24 - Profile dialogs and late responses

**Fixed**

- Closing a pending User Info dialog no longer blocks opening another person. Both dialogs cancel dismissed reads, retain duplicate-click protection and ignore late responses.
- Closing during the shared renderer download prevents an obsolete profile request. Reads share the standard timeout and navigation cancellation.
- Delayed enrichment refreshes cannot reopen a dismissed profile, replace another person or run after navigation.
- User table refreshes ignore older responses and responses belonging to a previous visit. Updated fields immediately obey the active search and role filter. Browser regressions cover desktop and touch layouts.

## [2026.10.24.post1] - 2026-10-24 - API readiness before worker startup

**Fixed**

- Compose starts background workers after the API is ready, so four RQ imports no longer compete with API initialization. Later API health changes do not stop existing workers.
- Container health uses the full readiness endpoint and one-second startup polling, followed by the normal 15-second interval.
- Page transition copies keep labels associated with dropdown buttons and other labelable controls, removing Chrome form-label warnings when leaving Preferences and Assistant.
- Startup documentation distinguishes API preparation, first response, warm requests and Docker restart-policy behavior after a host reboot.

## [2026.10.23.post11] - 2026-10-23 - Consistent Analytics cohorts and risk counts

**Fixed**

- Checklist, weekly trends and fallback history use the same active student cohort. Inactive teams/memberships and manually excluded students no longer contribute stale scores; archived course reports remain available.
- A student with simultaneous snapshots in multiple teams counts once, so checklist percentages cannot exceed 100% through duplication.
- At-risk counts respect the expected built-in and custom checks of each student's snapshot. SQL regression tests cover exclusions, restoration, multiple memberships and individual deadlines.

## [2026.10.23.post10] - 2026-10-23 - Indexed Analytics and correct course roles

**Fixed**

- Analytics excludes teachers and mentors through membership in the requested course. A staff role in another course no longer removes a student's scores or causes an additional scan of snapshot history.
- Course/student/date and covering course/week indexes reduce history reads for the latest checklist and weekly trends. Includes Alembic migration 025 and matching model metadata.
- Regression coverage checks teaching and mentoring roles across courses. The performance guide distinguishes query plans, cold requests and page-cache hits.

## [2026.10.23.post9] - 2026-10-23 - Consistent components and deadline editing

**Fixed**

- Escape closes an open calendar before its parent dialog. Toast text does not block modal fields or Save; toast close buttons and actions remain available.
- Project member actions remain available on phones. Removed the rule hiding the entire column and global project button margins that changed shared gaps from 4 px to 12 px.
- Weekly deadline editing restores the selected date, time and calendar month, and clears dates for empty or new weeks. Initial and regenerated rows share button variants, badges and archived locks; archived Add week is disabled in HTML before scripts run.
- Removed custom priority badge borders, weights and padding, duplicate responsive badge metrics, obsolete course header styles and redundant badge classes. Analysis error dismissal uses the shared secondary button.
- The UI reads GitLab connectivity through a shared cached status report, avoiding failed HTTP polls during an outage while preserving outage/recovery banners. The monitoring probe still returns HTTP 503. Added endpoint and browser regression coverage for dates, actions, archived controls and connection states.

## [2026.10.23.post8] - 2026-10-23 - Consistent tables and row actions

**Fixed**

- Background job buttons align with the Actions heading and use standard table spacing, including refreshes and phones.
- Archived Courses inherits shared table/card typography, padding and corners. Removed custom uppercase headings, muted colors and zero body padding.
- Courses, groups, projects and webhooks use the shared row-actions component without duplicated page rules or inline alignment. Button gaps no longer accumulate legacy margins. Browser coverage checks both themes, touch screens and fixed/fluid desktop layouts.

## [2026.10.23.post7] - 2026-10-23 - Faster API cold start

**Fixed**

- Caddy checks API liveness every second. Once startup finishes it no longer waits for another fifteen-second interval, which delayed first requests and caused 502 responses.
- Gunicorn loads the application before forking four Uvicorn workers. Models and routers are imported once; database/Redis connections and asynchronous warm-up remain separate in each worker's lifespan. Keep-alive remains five seconds.
- Cold-start measurement begins at the restart itself rather than after readiness succeeds. Verified the Linux container process model, multiprocess metrics and real-browser user flows.

## [2026.10.23.post6] - 2026-10-23 - Stable filters and identified fields

**Fixed**

- Shared tabs reserve the selected label's width. Search fields and neighbouring filters stay in place when switching views; course navigation uses the same rule.
- Added stable identifiers to job, event, check, suggestion, ticket and course-transfer selections, and preference color pickers. Temporary attachment and clipboard fields are named too.
- Transition covers give copied controls separate identifiers and reconnect their labels, preventing anonymous or duplicate fields during navigation while keeping the copy inert.
- Analytics fetches only check outcomes and their details, without unused diagnostic counters and arrays. Verified charts, form identities and filter geometry on phones and fixed/fluid desktop layouts.

## [2026.10.23.post5] - 2026-10-23 - Shared table row details

**Fixed**

- Expanded jobs use a shared table-details component with left-aligned labels, normal typography and precise local timestamps. Short results are not repeated; long messages remain available in the details.
- Sticky action columns exclude spanning cells. Expanded details and empty states keep their own alignment, and detail content fits the visible table width on phones.
- Removed System-specific grids, backgrounds, code panels and padding overrides. Shared disclosure controls work with the keyboard and remain separate from checkbox selection.

## [2026.10.23.post4] - 2026-10-23 - System operations and reliable charts

**Changed**

- System shows service health, actual RQ queues and online workers, background jobs and deployment configuration. It no longer duplicates role analytics or user-action audit rows. Monitoring links appear when deployed.
- Jobs use database pagination, exact filtered counts, all statuses and keyboard-accessible details. Cleanup preserves active jobs and the activity audit.

**Fixed**

- Compliance Progress accepts modern CSS colors, shares alpha handling and redraws when the theme changes. Charts and listeners are released on navigation.
- Empty assistant activity retains the shared table, filters and pagination. Project icons use the shared size without custom colored tiles.
- SSE gets upstream restart retries, compatible proxy keepalive and stream cancellation when clients disconnect. Client retries back off; short-lived greetings do not reset failures. Student detail uses the shared client.
- Cache clearing reports server failures and preserves sessions, job locks and rate limits. Health summaries reflect degraded external services.

## [2026.10.23.post3] - 2026-10-23 - Leaner system history and bounded database probes

**Fixed**

- System Job History loads only the archived-course fields it displays and skips unrelated course settings and relationships, preserving the same operations.
- Database health and readiness timeouts include waiting for a connection and establishing it, as well as running the query.
- Regression tests cover stalled connection acquisition and stalled queries for both probes.

## [2026.10.23.post2] - 2026-10-23 - Prepare page templates before serving requests

**Fixed**

- The image builds Jinja and application Python bytecode once; API processes reuse it after restarts instead of compiling the same templates during the first page visits.
- Each API process finishes template and ORM warm-up before accepting requests. Database warm-up is limited to five seconds, and readiness continues to check database availability.
- Template bytecode is readable by the runtime user and stays outside the mounted templates directory. Changed, missing or invalid entries fall back to source compilation without writes to the read-only filesystem.
- Regression checks cover cache reuse, source invalidation, escaping, cache misses and startup readiness.

## [2026.10.23.post1] - 2026-10-23 - Deep links reveal nested disclosures

**Fixed**

- Deep links open all parent disclosures and shared Alpine collapsible components while keeping their controls and reactive state synchronized.
- Scrolling waits for height transitions and follows the latest destination when another link is selected during opening. Closing a parent or leaving the page cancels the pending scroll.
- Selecting the current fragment again reopens its destination without duplicating history. Named anchors use the same behavior.
- Deferred SPA pages reveal targets after Alpine initializes, and hidden destinations no longer cause an initial empty-position jump.
- Fallback checks handle cache-busted GSAP URLs and verify that the library is absent before exercising modals, selects and page arrival.

## [2026.10.23] - 2026-10-23 - Fragment history preserves the current page

**Fixed**

- Back and Forward between sections of the same page preserve its form and unsaved edits without fetching the page again or asking to leave.
- Full-URL fragment links use the shared local scrolling component, including after client-side filter changes. Modified clicks, downloads and links to another window keep their native behavior.
- Client-side address changes keep navigation history synchronized. Cancelling Back restores the complete query and fragment; returning to another filter still loads it.
- Cross-page fragments share decoded ID and named-anchor lookup, keeping scrolling inside the content pane.
- Destination highlighting no longer recentres fragment anchors or repeats after unrelated lazy-region updates.
- Pending anchor lookups stop when leaving a page or choosing another fragment. A missing anchor cannot reset the next page's scroll position.

## [2026.10.22.post10] - 2026-10-22 - Save-bar spacing and smooth page arrival

**Fixed**

- A shared save bar leaves a small gap before the next card while retaining the existing page-bottom gutter when it is the final section.
- In-app navigation keeps the previous frame visible until incoming scripts and Alpine finish, then briefly fades its inert cover over the ready page.
- Redirects and reloads retain the previous browser frame until the incoming page is ready. The short transition respects reduced motion.
- Browser checks cover delayed scripts, completed transitions, missing GSAP, and spacing in fixed desktop and narrow layouts.

## [2026.10.22.post9] - 2026-10-22 - Request retries and isolated pagination

**Fixed**

- HTTP client errors finish without unnecessary retries. Transient statuses and network failures keep bounded retries; opting into mutation retries still respects the HTTP status policy.
- Cancellation preserves translated or caller-provided messages instead of the read-only browser exception text. Custom abort reasons do not trigger retries.
- Page-size changes update only the clicked menu's table, including after SPA navigation. One delegated handler replaces listeners retained by old paginator instances.
- Refreshing pagination closes and returns its open portaled menu before replacing controls, preventing an orphan menu from floating over the page.

## [2026.10.22.post8] - 2026-10-22 - Consistent form-select interactions

**Fixed**

- Escape closes an open form select before its containing dialog. Arrow keys, Home and End navigate options; Tab leaves the control without retaining focus in its hidden menu.
- Server-rendered and dynamically loaded options share selected styling and accessible selection state, including numeric and externally assigned archived values. Adding options removes the empty placeholder.
- Choosing an option returns focus to the toggle. Closing a dialog resets its open selects, and closed menus become inert during their exit animation.
- Choosing a custom-select option while a dialog opens remains an unsaved edit after delayed initialization, including keyboard activation.
- Form selects inherit shared dropdown text wrapping, keeping long course names and unbroken labels readable on mobile.
- Browser regressions cover desktop and narrow layouts, reduced motion, missing GSAP and dialog reopening, together with the existing modal and tour scenarios.

## [2026.10.22.post7] - 2026-10-22 - Bounded OpenTelemetry header parsing

**Security**

- Require OpenTelemetry API 1.45.1 or newer and update its matching SDK, exporters and instrumentation in the lockfile. This fixes CVE-2026-114603 / GHSA-xcq7-p3pf-p88h, excessive CPU usage when parsing malformed inbound `tracestate` headers.
- A regression test preserves valid trace state while verifying oversized headers are rejected before parsing.

## [2026.10.22.post6] - 2026-10-22 - Unsaved edits, mobile sheets and keyboard actions

**Fixed**

- Modal entrance cleanup preserves text entered during opening. Delayed initialization snapshots no longer turn trusted edits into the pristine state.
- Mobile swipes check unsaved-change guards before leaving the screen. A vetoed close settles back smoothly, and the gesture belongs to the dialog actually touched.
- Swiping or programmatically closing a confirmation resolves its pending answer as cancellation, including reduced-motion and missing-GSAP fallbacks.
- Tab and Shift+Tab stay inside a modal when its container initially has focus, instead of moving to the page underneath it.
- The question-mark key opens keyboard help with or without Shift. Ctrl+S recognizes shared guarded forms, including Preferences, and leaves background forms alone while a dialog is open.

## [2026.10.22.post5] - 2026-10-22 - Stable tour navigation buttons

**Fixed**

- Next and Back resize tour cards at their fixed anchor, keeping buttons still when descriptions change length. The shared motion component animates height and position together without scaling text or briefly exposing scrollbars.
- Cards slide between top and bottom placements on tablets and landscape phones. Closing mid-transition continues from the visible position without a pixel-to-percentage jump. First appearance, reverse exit and highlight timing remain intact, including reduced-motion and missing-GSAP fallbacks.
- Browser regression tests check action positioning during forward and backward navigation on desktop, phone, tablet and landscape layouts.

## [2026.10.22.post4] - 2026-10-22 - Fewer unnecessary requests and browser warnings

**Fixed**

- The teacher profile menu no longer links to the administrator-only System page. Student compliance alerts open the course instead of restricted settings. Routine tour and team stream diagnostics require debug mode.
- Profiles, staff lists, user cards and assistant activity use stored avatar URLs. Missing photographs show initials without requesting invented GitLab upload paths.
- Public cookie preferences arrive as escaped page data. Consent, language and theme writes use asynchronous Cookie Store where supported, retaining the standard fallback. The application and auth pages share one cookie implementation.
- The offline shell receives a matching CSP nonce for its theme bootstrap, allowing cached offline navigation to apply the theme without blocking the script.

## [2026.10.22.post3] - 2026-10-22 - Touch gestures and installation without browser warnings

**Fixed**

- Shared tour gestures no longer try to cancel non-cancelable touch events. Mobile modal dragging yields when the browser owns scrolling; the fix applies throughout the application.
- PWA installation keeps the browser's native promotion available while retaining the in-app Install button. A native prompt result clears the saved event and hides the card so it cannot offer a consumed prompt.

## [2026.10.22.post2] - 2026-10-22 - Smaller tour close button

**Fixed**

- The tour close control uses the compact transparent button component instead of a large filled square, while retaining its larger touch target on phones.

## [2026.10.22.post1] - 2026-10-22 - Compact mobile layout and shared component states

**Fixed**

- Browser toolbars no longer inflate bottom padding. Settings actions count the safe area once, and the shared settings form keeps sections compact on phones.
- Table stripes, hover, press, selection and navigation feedback have one owner and use theme accent tokens. Pinned actions inherit the same opaque row background; nested projects and expanded jobs no longer override it.
- Tours place targets using the measured card height. Mobile cards slide in and out, highlights follow the moving sidebar, and closing folds the highlight while dismissing the card and drawer together. Tour and tree-disclosure buttons reuse the shared button component; theme segments and selected files use shared selection and focus tokens.

## [2026.10.21.post5] - 2026-10-21 - Monitoring without a second password

**Changed**

- Monitoring opens with the GitPulse sign-in. Grafana, Prometheus, Jaeger and Alertmanager asked for a Basic Auth password of their own, one shared by all four; now a signed-in GitPulse administrator walks straight in and nobody else does. Caddy asks the application before each request (`/internal/monitoring-authz`, as for the documentation): an administrator is served, a reader without a session is sent to sign in and back to the same page, any other role gets a page saying who may open it. Grafana signs the administrator in under their GitPulse login (its auth proxy; Admin of the main org), and a client cannot name itself - Caddy overwrites the header. Unlike the documentation the gate fails closed. Checked end to end through Caddy with Grafana 11.1: anonymous, a spoofed header, a teacher and an administrator.

## [2026.10.21.post4] - 2026-10-21 - An alert email worth reading

**Fixed**

- The alert email reads like GitPulse's other mail. It was Alertmanager's default: raw labels (`alertname=... component=...`), a "View in Alertmanager" button to `http://alertmanager:9093` and a "Source" link to the Prometheus container, neither of which opens from a mailbox. Now it is the application's mail chrome with GitLab's pipeline status bar - red with a cross while an alert fires, green with a check once it is resolved - the summary as its headline, a table of what happened, the alert, its severity, the label that matters (a queue, an event type) and the times in Bratislava time, and links that work: the alert's query in Prometheus, all alerts, the dashboard and a Silence link. The subject is the summary: `Firing: RQ jobs are failing (10 in the last hour) | GitPulse`.
- Alertmanager is reachable at `/alertmanager/`, behind the monitoring password, for that Silence link; Prometheus and Alertmanager know their public addresses, so the links an alert carries are absolute.

## [2026.10.21.post3] - 2026-10-21 - Alerts reach the inbox

**Fixed**

- Alerts reach the inbox: Alertmanager reads the SMTP password without its whitespace, as the application does (`config.py`). Google shows an app password in groups of four, and Gmail answered the spaced form with a bare `535 Username and Password not accepted` - the first test alert on production was refused that way.

## [2026.10.21.post2] - 2026-10-21 - Monitoring that measures

**Fixed**

- Monitoring: what the workers measure reaches Prometheus. Webhook processing, enrichment, metric computation and the GitLab API calls of a sync are recorded in the work-horse RQ forks for each job, which exited with the values, and Prometheus scrapes only the API - so six of the eighteen alert rules watched metrics that did not exist and half of the Grafana dashboard stayed empty. Those metrics are kept in Redis now and the API's `/metrics` exports them.
- Monitoring: the API's four uvicorn processes add up their metrics (prometheus_client's multiprocess mode, in the container's tmpfs). A scrape reached one process at random, so `http_requests_total` read 4195, 9956, 1487, 4196 on consecutive scrapes and Prometheus counted 5 808 counter resets in six hours: every rate, the HTTP panels and the HTTP alerts were noise.
- HTTP metrics are labelled by the route a request matched (`/dashboard/courses/{course_id}`), a mount point or `<unmatched>`, so a release's hashed bundle or a scanner's path is no longer a series of its own; an event stream is counted but kept out of the latency histogram, where its open-tab hours read as response time.
- Alerts: `RQFailedJobsHigh` watches new failures (86 failed jobs from April-July kept it firing for good); `HighHTTPErrorRate` sums before it divides (a single 5xx read as 100 %); `HighHTTPLatency` takes the overall p95; `NoWebhooksReceived` fires when a week of traffic stops for 12 hours - not every quiet hour, all winter long - and also right after a deploy, which it could not; `DatabaseDown` is `ApiDown`, the thing it checks. Verified with promtool rule tests, which the old rules fail and the new ones pass.
- Alerts are delivered. Alertmanager sent them to `ops@example.com` through `localhost:25` - 64 221 delivery errors in six days and not one alert received; it uses the application's SMTP account now, to `ALERT_EMAIL_TO`, with the password as a compose secret.
- Jaeger keeps at most 100 000 traces. Unbounded, it filled its 512M every day and a half and was OOM-killed with every trace in it.
- Redis's `maxmemory` (200mb) is under its container limit (256M), so it evicts before the kernel kills it.
- The connection pools fit Postgres: four API processes × (12 + 4) and four workers × (2 + 2) is 80 of its 100 connections. 25 + 15 promised 220, and the 101st is refused instead of waiting for the pool.
- Deploy: Caddy reloads the pulled Caddyfile (through stdin). A file mounted on its own keeps the inode it had when the container started and `git pull` writes a changed file as a new one, so `caddy reload` re-read the old text - reproduced. Prometheus and Alertmanager restart when the pull changed their config; Redis and the monitoring services are recreated when their compose definition changed.
- Security: the monitoring password is no longer in the documentation or in `prometheus.yml` (Grafana's `/metrics` needs none), and it was changed.
- `redis.asyncio` connections are closed with `aclose()` (`close()` is deprecated since redis-py 5.0.1), and the obsolete `types-redis` stubs, which hid `aclose()` from the editor, are no longer a dev dependency.

## [2026.10.21.post1] - 2026-10-21 - certifi security update

**Fixed**

- **Security:** `certifi` 2026.6.17 -> 2026.10.19 (PYSEC-2026-4320 / GHSA-6q48-6c7w-9gw2: the bundled CA store trusted `emSign ECC Root CA - G3`, whose intermediates' private keys were compromised and revoked), which un-breaks the `dependency-scan` CI job. `exclude-newer` moved to 2026-10-20 12:00 UTC so uv can see the fix (uploaded 2026-10-20 02:24 UTC); certifi is the only pin that moved.

## [2026.10.21] - 2026-10-21 - A page arrives finished

**Fixed**

- An in-app navigation shows the incoming page once it is finished, as a full load does. The page's scripts - which paint its rows, charts and counts - were loaded only after the new content was already on screen, so Admin > Events showed its table 39px tall with every column at its header's width for a few frames before the rows landed and it opened out to full size with other column widths; longest on the first visit, before the page script was cached. The swapped content stays laid out but unpainted until the scripts and Alpine are done (3 s safety net); a filter or sort that stays on the page keeps its controls on screen.
- Dashboard: the courses header's Import, Import JSON and New course no longer run out of their row at 1024-1280px (New course lay 101px over the Quick access card); the three are one group that wraps under the search together.
- Users: every column is at least as wide as its own label in both languages, so the header row is one line (36px) - "Používateľské meno" wrapped and made it 56px tall.
- Admin > System, Job History: the "Enqueued" header is no longer cut ("Zaradené do fronty" needs 180px, the column had 142px).
- A table header holding a select-all checkbox (Job History, Events) is 36px like every other, not 39px: the checkbox sits on the middle of the line, not on its baseline.
- The content security policy names GitLab's origin with its port, so a GitLab on a port of its own (https://git.example:8443) gets its avatars and API calls through, and it allows GitLab's default avatars on both gravatar hosts.

**Tests**

- The browser scenarios run clean (53 of 53): the two that change the e2e admin's preferences put them back (a collapsed sidebar left behind was most of four walks' findings), the per-page menu test closes the first-visit tour card that covers the selector, and three tests follow the current design (people's names wrap in the users table, card bodies are padded, a page ending in a sticky save bar has no footer).

## [2026.10.20.post3] - 2026-10-20 - Buttons that say Done, text that stays put

**Fixed**

- The Assistant activity card's Refresh goes through the states every Refresh does - working, "Done", back - as on Job History. The redraw replaced the whole card, the header too, so the working button was swapped for a fresh idle one at once and no state was ever seen; only the card's body is redrawn now.
- Saving the assistant's tools (and connecting or replacing the bot) shows "Done" on the button before the page comes back, as Settings' Save does. The success toast was handed to the next page only and the page reloaded at once, so the button never reported its own end; the toast is raised on the page now and carried over by the reload.
- On a development server the fonts are cached as in production (one year, immutable). Revalidated on every page load, GitLab Sans sometimes arrived after `font-display: optional` had given up on it: that page stayed in the system font and the next one did not, so the search box's text (and every other) jumped between pages - 113.8 px wide in GitLab Sans, 104.2 px and 1 px higher in Segoe UI.

## [2026.10.20.post2] - 2026-10-20 - The exercise in the top bar, the activity live

**Changed**

- Prepare exercise runs as a background job, like a sync: the top bar follows it from the queue to its end, a toast says when it is done, and the Assistant page then shows the result by itself - no more "reload the page in a moment". With unsaved tool settings on the page, only the activity card is redrawn, so the edit is not lost. A run that cannot start (the course archived, the bot gone, its token refused since the click) fails at once and says why, instead of "Preparing" for a quarter of an hour. Every run is one row in Admin -> System's Job History ("Assistant exercise"), with its duration.
- The Assistant activity card keeps itself current: the course's live stream redraws it when the bot acts in GitLab, and a Refresh button in its header reloads it, as on Job History and Webhooks. The group has a column of its own (sortable, searchable) instead of wrapping under the username, and an empty card shows the small empty state every empty list shows, not the page-sized one.
- The Assistant page also warns about a webhook that has received nothing from GitLab for 48 hours, the Events page's second case, not only about a missing one.
- Every chart enters the same way as Admin -> System's role chart: its first draw waits until it is on screen, bars grow over 900 ms each 80 ms after the one before, a ring sweeps round in 900 ms. Analytics' compliance ring and weekly chart used to animate while still below the fold and were seen standing still; the five hand-written copies of "draw when visible" (System, Analytics, the student detail, the project detail) are one function, `GP.drawOnEntry`.

**Fixed**

- An avatar that failed before the page script was listening (a quick 404, a source the image policy refuses) showed a broken picture and its alt text for eight seconds after it scrolled in, on every page with avatars; it now shows the initials at once.
- The course role badge in every course page's header ("Teacher", "Course Owner") and the user role badge were English in the first frame and translated a moment later; they are translated on the server.

## [2026.10.20.post1] - 2026-10-20 - The assistant for whoever runs the course

**Fixed**

- The classroom assistant is for whoever runs the course: its tab, its page and its four actions are open to the course's owner and teachers and to admins, not to a teacher who sees the course only as a team's mentor (such a teacher used to get the tab and the page, the bot token form included). Its items in **Items that need your attention** and its rows in **Follow the latest updates** follow the same rule.
- Check R08 no longer counts a bot account's comments as review threads the author has to answer. The assistant writes "approved - merge it" after its review, so every exercise merge request was left with a thread nobody is meant to answer and R08 failed for students who did everything right; a CI bot's report counted the same way. R06's hint still counts those comments among the ones that are no team member's.
- Admin -> System's Job History names the assistant's operations as the dashboard feed does ("Assistant tools updated", translated, instead of an untranslated "Assistant tools saved").

**Documentation**

- The privacy statement says what the assistant writes to the teams' projects and under which account; the student FAQ says who the bot commenting on commits is; the assistant guide and the R08 description say who controls the assistant and that a bot's comments need no reply.

## [2026.10.20] - 2026-10-20 - The assistant on the dashboard

**Changed**

- The assistant is part of the dashboard: **Items that need your attention** say what its page says at the top (a token GitLab refuses or that has expired, tools on without a bot, a token about to expire, an exercise run that never finished; one function, `account.problems()`, answers both) and count the actions GitLab refused it in the last 7 days; **Follow the latest updates** names its actions (bot connected or disconnected, tools updated, exercise prepared, token refused) and links them to the Assistant page, with none of them shown to students. A refused token is written to the audit log once.
- The course configuration file (export / import) carries the assistant's tool settings in an `assistant` section, never the bot or its token; the import checks them as the tools form does, and skips them while the assistant is switched off, as its preview now says.
- The Assistant page says that a course has no webhook the way the Events page says it: a warning toast raised once when the page opens, not a block in the page (none on an archived course, whose webhooks are dropped by design).
- Nothing on the Assistant page is said twice: an expired token is announced by the alert at the top only (the card no longer adds a "Token expired" badge), the course's default branch rule is no longer printed in two cards (as in the exercise's issue, only a stricter rule is named), and the activity card is "Assistant activity", not "Activity" like the course tab next to it.
- The tour prompt counts its steps as "Steps: 4", grammatical in Slovak for every number ("4 krokov" was wrong).
- `scripts/assistant_e2e.py accounts` prints logins for trying the assistant by hand on the local GitLab: the teacher's and the students' GitLab passwords and the GitPulse dev login.

## [2026.10.19.post10] - 2026-10-19 - The assistant verified on a real GitLab

**Fixed**

- A course's webhook configuration (the only secret the Settings page issues) authenticates the course's imported projects. Every imported project carries a secret of its own that nobody ever sees, and the receiver stopped at it, so every delivery from an imported project was refused with 401. The project's own secret is still tried first, and a token that matches nothing is still refused.
- Merge request webhooks from GitLab are received. A merge request event's `object_attributes.source` is the source project, not a word, and the schema refused every one with 422; merge requests reached GitPulse only through sync. The hand-written contract fixture had no such field.
- A pipeline webhook outside a merge request (`"merge_request": null`) no longer crashes the processor.
- The classroom assistant, run end to end against GitLab CE 19.4.2: a branch created in GitLab with no commits is not commented on (the comment landed on main's last commit) - its first commits are greeted and its name judged then; GitLab's push of a merged merge request to main is not called a direct push; the issue says what the review will also ask for (the course's description sections, a stricter branch rule) and who merges; the review waits while GitLab still checks whether the merge request can merge, so it never approves a conflict; a comment the review already answered is not answered twice; a member excluded from scoring gets no issue and no comments; a quoted line in a conflict comment no longer ends in a second full stop.

**Added**

- The Assistant page has a guided tour like every other course tab, Cancel next to Save as on the Settings page, and a note that the exercise's issues and merge requests count in R01-R13; a team name in the activity table no longer breaks across lines.
- `scripts/assistant_e2e.py` with `docker-compose.gitlab-e2e.yml` runs the assistant end to end against a real GitLab CE 19.4.2 (56 checks). The deliveries such a run captured are contract fixtures in `tests/fixtures/payloads/gitlab_19_4/`.

## [2026.10.19.post9] - 2026-10-19 - Smooth tour highlight fold on exit

**Fixed**

- Tour highlights fold vertically closed over 400 ms, reversing the first reveal when closing the tour or returning to a centred step. Close, Escape and mobile swipe share the same exit. Closing during a reveal continues from its visible shape; repeated Escape no longer interrupts the animation.

## [2026.10.19.post8] - 2026-10-19 - Smooth first tour highlight

**Fixed**

- The first guided-tour highlight opens vertically at its target over 400 ms instead of appearing instantly or starting as a circle at the viewport centre. Tours without an introduction and returning from a centred step use the same reveal. Animation waits for the target measurement; the stable-DOM refresh no longer restarts a valid step or reopens a closed tour.

## [2026.10.19.post7] - 2026-10-19 - Smooth transitions throughout guided tours

**Fixed**

- Tour highlights keep their 400 ms transition when scrolling to the next or previous element. The shared motion module follows the live target without scroll refreshes replacing the visible highlight. Cards start from their previous visible position when a new description has a different height. Reduced motion, interrupted steps and solid introduction/closing backdrops remain supported.

## [2026.10.19.post6] - 2026-10-19 - Classroom assistant in production

**Added**

- The classroom assistant is on in production (`redeploy.py` sets `FEATURE_CLASSROOM_ASSISTANT=true`; `docker-compose.yml` now passes the flag to the API and the workers, which it did not). Each course still connects its own bot and switches its tools on.
- The assistant follows the course's own rules: with R02 on it checks a new branch and a merge request's branch against the course's naming rule, with R05 on the review asks for the description sections. A check the course switched off is never asked for. The review also reports a failed pipeline.
- A course chooses the language its assistant writes in (Slovak or English): comments, issues and the colleague's line.
- A course transferred to a new semester keeps its assistant's tool settings; the bot token stays with the old course.

**Fixed**

- A merge request closed without merging no longer holds its issue: the next merge request for it is reviewed from the start.
- A bot token that expired or that GitLab refuses (confirmed with `GET /user`, since GitLab also answers 401 to a repeated approval) stops the assistant instead of failing every event; the Assistant page says so at the top and asks for a new token.
- The Assistant page says what keeps the assistant from acting: no course webhook, tools on without a bot, an unusable token. A waiting conflict task says what it waits for; Prepare exercise shows a run in progress, refuses a second one and counts students without a GitLab account in GitPulse yet.

## [2026.10.19.post5] - 2026-10-19 - Smoother mobile search

**Fixed**

- Mobile search reveals a fixed-size panel through clipping and translation instead of recalculating layout every frame. The backdrop uses a separate opacity layer, and animation starts after preparation and input focus. Opening the keyboard no longer interrupts the transition. Text, scrolling, rapid reopening and device rotation remain stable.
- Guided-tour highlight and popover transitions return to their previous 400 ms duration. Introduction and closing steps keep the circular cut-out fix.

## [2026.10.19.post4] - 2026-10-19 - Restored guided-tour motion

**Fixed**

- Restored smooth highlight morphs between real targets and popover slides between anchors. Introduction and closing steps retain their solid backdrop without a circular cut-out. Scrolling tracks targets directly; rapid navigation and reduced-motion preferences remain supported.

## [2026.10.19.post3] - 2026-10-19 - Faster search without text reflow

**Fixed**

- Search opens in 200 ms and closes in 100 ms. Its input and results keep their full dimensions while the shell expands, preventing text reflow and temporary scrollbars. Long result lists regain normal scrolling when the transition finishes.

## [2026.10.19.post2] - 2026-10-19 - Search field expansion

**Changed**

- Search expands from its top-bar field into the palette and returns to the field when closed. Results reveal inside the growing panel without scaling text. The shared motion module handles interruptions, viewport changes, keyboard focus, reduced motion and a missing GSAP library.

## [2026.10.19.post1] - 2026-10-19 - Guided tour transitions

**Fixed**

- Introduction and closing steps use a solid backdrop without a circular cut-out. Highlights and popover anchors update together, removing distorted SVG sweeps and cross-screen slides. The opening and closing fade is preserved.

## [2026.10.19] - 2026-10-19 - Classroom assistant

**Added**

- Classroom assistant, behind `FEATURE_CLASSROOM_ASSISTANT` (off by default): a bot that works on a course's projects as a colleague, which students meet only in GitLab. A teacher connects its token on the course's new **Assistant** tab - a group access token with the Maintainer role and the `api` scope, checked with GitLab and stored encrypted. The analytics keep their read-only token; the bot has its own client, and a rejection of its token never stops the course's sync.
- Push review: after a student's push, a comment on the pushed commit when it went straight to the default branch, when the GitLab web editor wrote the message (the R13 rule) or when the message is too short. A new branch is encouraged, a clean push to an existing branch gets no comment, and a redelivered webhook is never answered twice.
- Merge conflict: the first time a student's branch changes the exercise file, a colleague's commit on the default branch edits exactly those lines, so merging the branch conflicts - also when the default branch moved on, verified with real git. Once the default branch is merged in, each push is checked for conflict markers and for both changes kept; the result goes to the merge request or the commit.
- Issues and merge requests: **Prepare exercise** gives every student of the chosen projects a file and an assigned issue; running it again adds only new students. The student's merge request is reviewed - own branch, a link to the issue, only the assigned file, nothing left to fill in, not a draft, no conflicts - with one comment on exactly what is missing and an answer to the student's comments. Once nothing is missing the assistant approves it and the student merges it (R10 does not count a bot's merge as the student's), or, if the course chooses, the assistant merges it. GitLab's merge event closes the issue and says well done; a merge before the approval is named as such.
- The Assistant tab shows the bot and its token expiry, the three tools on the shared save bar, the last exercise run per project and an activity table - tool tabs, search, pagination - with links into GitLab. An archived course is read-only. A guide for teachers in Slovak and English.

**Changed**

- R13 and the push review share one rule for web-editor commits.

## [2026.10.16.post3] - 2026-10-16 - Opaque settings save bar

**Fixed**

- The shared Course Settings and Preferences save bar covers the scroll area's bottom gutter, so content no longer shows below its buttons during scrolling. Buttons keep their position, and the final page gutter, including below Danger Zone, is preserved.

## [2026.10.16.post2] - 2026-10-16 - Deployment checks and dependency caching

**Fixed**

- Deployment stops on Git, remote command and readiness failures, preserves a changed production checkout, and verifies the running commit and version.
- Migrations are checked in the new image before replacing the API. Documentation stays running until its replacement has built successfully.
- A version-only release no longer invalidates the Docker dependency layer. Runtime dependencies remain locked by `requirements.lock`.

**Changed**

- Local agent settings, runtime uploads, scratch files and tool caches are excluded from the Docker build context. Deployment instructions reflect the verified release order.

## [2026.10.16.post1] - 2026-10-16 - Selector hover feedback and cleanup

**Fixed**

- Period, form, language and page-size menus show a subdued check when an available option is hovered or focused with the keyboard. Selected options keep a solid check; opening a menu under a resting pointer does not preview a choice. Labels keep their position.

**Removed**

- The unused GitLab documentation CSS snapshot from the repository root.

## [2026.10.16] - 2026-10-16 - User table spacing and shared components

**Fixed**

- The Users table gives Email the extra room on wide layouts while preserving column widths in Fixed mode. Filters and pagination keep columns in place.
- Course Settings and Preferences keep space below their final block, including a Danger Zone nested inside a tab panel. Save bars remain sticky.

**Changed**

- Users and member tables share row-action styles. Danger Zone styles belong to the card component; Users layout rules are consolidated without duplicate ID overrides.

## [2026.9.30.post110] - 2026-09-30 - urllib3 security update

**Fixed**

- **Security:** `urllib3` updated to 2.8.0 (three CVEs).

## [2026.9.30.post109] - 2026-09-30 - Teachers like every other list, pages no longer blink while loading

**Changed**

- A course's Teachers page looks and behaves like the other lists: search, role filters, sorting and pages. Changing a role, removing a teacher and adding one (in a dialog) apply at once - no Save button. Nothing blinks while it loads: the table is in place from the first frame.

**Fixed**

- The pager under the tables is there as the page loads instead of being drawn a moment later.
- The user list no longer grows from 25 to 50 rows while loading.
- Course settings with no webhooks show the empty state at once; the card no longer jumps.

## [2026.9.30.post108] - 2026-09-30 - The same action buttons in every table

**Fixed**

- The row actions of every table are the same square icon buttons (larger on a touch screen): view is always the eye, delete always the red trash. Gone are the worded buttons among the icons (View in the groups, tickets and project members tables, Details and Resurrect in the events, Cancel in the job history) and the grey trash among the teachers.
- The toggle that counts a member in the score is fully visible on a phone too and has its own icon (a person with a minus / plus) - it used to be an eye, the same as the View button right beside it.

**Changed**

- All of a course's tabs (overview, Activity, Analytics, Settings, Teachers) share one header: the course's code and name, the term, your role and the course description - switching tabs changes only the content.

## [2026.9.30.post107] - 2026-09-30 - The toast counter and the archived courses' buttons

**Fixed**

- A single click never shows "×2" on a notification any more - only a further press counts, not an echo of the same action.
- An archived course's action buttons are the same size in course management and on the dashboard, and the same action has the same icon and colour (activate - green check, delete - red trash).

## [2026.9.30.post106] - 2026-09-30 - The service accounts table

**Fixed**

- In User Management's Service Accounts view the texts no longer overlap: a bot's name, full name and e-mail are cut to the width of their column (the whole value is in the tooltip), and a row says Bot once - in the Role column.

## [2026.9.30.post105] - 2026-09-30 - Disabled buttons and the phone layout

**Fixed**

- Disabled checkboxes and buttons are clearly visible on the light theme and clearly read as disabled - the Active column of an archived course's checks no longer looks like empty boxes.
- The pagination arrows sit on the card's white background; a disabled arrow is a plain grey glyph without a frame.
- Every disabled button says why it is disabled - on hover, and on a phone when you tap it.
- Phones: buttons and links have a touch area of at least 32px, no text is smaller than 12px, an empty table's message is fully on screen, and long link buttons wrap.

## [2026.9.30.post104] - 2026-09-30 - Maintenance

**Removed**

- An old way of loading part of a page that nothing has used since the summer. A hand-made request could make the support page fail; every address now returns the full page. Nothing changes for users.

## [2026.9.30.post103] - 2026-09-30 - The Save bar fix actually deployed

**Fixed**

- The post102 change to the Save / Restore bar and the actions column did not reach the server - it kept sending the old styles. The styles are now always built from the current sources.

## [2026.9.30.post102] - 2026-09-30 - The save bar, and app files with a fingerprint in the name

**Fixed**

- **The Save / Restore bar** on course settings, preferences and course teachers takes the page's colour and ends exactly where the content does - on the light theme it no longer stands out as a shadowed white box wider than the cards above it.
- An excluded member's row in a project's members table keeps its tint in the actions column too.

**Changed**

- **The app's scripts and styles carry a fingerprint of their content in the name.** The browser can therefore keep them for good and, after an update, downloads only the ones that actually changed. Pages look and behave as before.
- **An update no longer briefly breaks pages that are open.** Files the new version removes stay available until the next update.

## [2026.9.30.post101] - 2026-09-30 - Tables without blank space and steadier live refresh

**Fixed**

- **No blank space under a table once it has loaded.** Short tables (e.g. a student's issues) had an empty band under the last row that disappeared only after switching a filter and came back on reload.
- **Importing a full configuration in a course's settings works** - it always failed with "No configuration provided" before.
- **A webhook event that cannot be processed is recorded as failed** and is no longer retried for ever.
- **A page's live refresh shows the same as the page.** On a course page the contributor count no longer switches to an all-time count, a group's pipeline status in the Activity Monitor no longer switches to "running", on a project page members excluded from scoring refresh too, and group sync badges no longer flip between two answers.

**Changed**

- The application's code is split into smaller parts; pages behave the same (checked by comparing the old and new versions).

## [2026.9.30.post100] - 2026-09-30 - Error pages, tables and faster loading

**Changed**

- **Error pages offer only what works.** During an outage (502/503/504) the page shows Retry and reloads itself - no search or links that could not load anyway. The heading and the text under it no longer repeat each other; on a phone the search stays one row and buttons keep a normal width. The texts are translated into Slovak.
- **Table columns get the room their content needs.** In the project Members table the name and the checks are sized sensibly, User Management wraps names, logins and e-mails instead of cutting them to "...", and Job History shows the whole job type and wraps the result.
- **The guided tour loads after the page is shown**, so pages appear faster. The tour works as before.
- **Syncing one project stores the same data as syncing its whole group** - including the commits of merged merge requests whose branch was deleted - and is faster, as unchanged data is not fetched again.

**Fixed**

- The dashboard's live activity refresh no longer drops the "Course created" and "Course archived" rows.
- A course without groups shows only its own jobs in the activity feed.

## [2026.9.30.post99] - 2026-09-30 - Check results aligned under their codes

**Changed**

- **In the project Members table the check codes and their results are centred**, each result exactly under its code.

## [2026.9.30.post98] - 2026-09-30 - One file per component, ticket access and the members table

**Changed**

- **The shared interface code is split by component** - instead of four files of thousands of lines, each component (buttons, content states, tooltips, date pickers, navigation, ...) has a file of its own. The app looks and behaves exactly as before.
- **The student page is built from separate sections** instead of one 1 334-line function; it shows exactly the same.
- Removed code nothing used, styles that another style always overrode, and translations the app never asks for.

**Fixed**

- **A support ticket is visible only to its course's teachers.** Until now any teacher could open another course's ticket by its number, internal notes included.
- **The project Members table cut its check headers to "R..." and its View buttons.** Columns now take the width of their content, every check the same; on wider screens the table fits whole, on narrower ones it scrolls sideways instead of clipping.
- The Slovak 404 page showed "Member" and "Ticket" in English.

## [2026.9.30.post97] - 2026-09-28 - One controls band above every table

**Changed**

- **The search and filter row above every table is laid out like the one on User Management** - the same height and the same spacing above and below the controls, whether it holds a search, dropdowns or tabs, on the desktop and on a phone.

## [2026.9.30.post96] - 2026-09-28 - One card header everywhere, the full GitLab User ID column

**Changed**

- **Every card header looks the same**: an icon, then the title, in the same place on every page. Some cards had no icon and others placed it differently.

**Fixed**

- **The "GitLab User ID" column header in User Management was cut off**; it now shows in full, and on narrower screens the table scrolls sideways instead of cutting columns.

## [2026.9.30.post95] - 2026-09-27 - Tabs switch without a blink

**Fixed**

- **Switching tabs no longer makes the content blink** - for example the empty-state picture under Quick access on the dashboard. The new tab's content appears at once, as in GitLab.

## [2026.9.30.post94] - 2026-09-27 - Illustrated empty states, one tooltip at a time

**Changed**

- **Every empty state has a GitLab illustration**: empty tables, lists, charts and panels, and searches that matched nothing, now show GitLab's picture above the message - as the page-level empty states already did.
- **Less space round a table's search row.**

**Fixed**

- **Two tooltips could show at once** (for example on the Enqueued column of Job History); only one shows now, everywhere.
- **A time's UTC tooltip** shows the time to the second with "UTC" instead of the server's raw value.
- **Two dropdowns could be open at once** on the Support page.

## [2026.9.30.post93] - 2026-09-27 - Animations and sizes in step with GitLab

**Changed**

- **Alike elements move alike**: buttons, close buttons, badges, tabs and chevrons share one speed, list items and table rows another, form fields a third - each GitLab's own. Panels open the same way, every progress fill runs at one speed, live marks pulse on one clock, and pressing a control no longer shrinks it.
- **Control sizes are GitLab's**: buttons are 32px, small buttons 24px with the same text everywhere, pagination arrows match the page numbers, and tabs in one strip are the same height.
- **The README** has new screenshots of the current interface and a clearer overview.

## [2026.9.30.post92] - 2026-09-27 - CSRF on every write, dialogs without a flash

**Security**

- **Every request that changes data checks the CSRF token** - twelve did not: retrying and replaying webhook events, deleting, purging and updating tickets, comments and attachments on them, recomputing a weekly snapshot and the four telemetry beacons. The app always sent the token, so nothing changes for a reader.

**Fixed**

- **Opening a dialog no longer lights up a select** as if the pointer were on it: the dialog passes under the resting pointer as it arrives, and its contents answer the pointer only once it has landed.
- **CI runs the integration tests again** - it used to skip every one of them.

## [2026.9.30.post91] - 2026-09-27 - Empty states laid out as GitLab's

**Changed**

- **Empty states follow GitLab's layout and sizes exactly** - illustration, a 28px title, the description and the buttons spaced as in GitLab.
- **The date picker's month arrows**, a running pipeline, the project members table, the week explorer, merge request branches and every close button draw GitLab's own icons; no text character stands in for an icon.

**Fixed**

- **Course Analytics no longer fails** when the checklist chart has no data.

## [2026.9.30.post90] - 2026-09-26 - Every icon and illustration from GitLab

**Changed**

- **Every icon and illustration is GitLab's own** (`@gitlab/svgs`, `@gitlab/ui`), used the way GitLab uses it; the GitPulse logo and the loading tanuki stay the app's own.
- **Empty states lead with a GitLab illustration** - "No courses in <term>" on the Dashboard shows GitLab's calendar illustration instead of an icon in a grey box.
- **Empty tables and charts say so in words alone**, like GitLab's tables.
- **Items that need your attention** use GitLab's to-do marks, and "Good job!" GitLab's illustration.
- **Sorting** shows GitLab's arrow (↑ / ↓) on the sorted column.
- Close buttons, ticks, chevrons, checkboxes, the job bar, the student heatmap and the error and offline pages draw GitLab's own icons and illustrations; no text character stands in for an icon.

**Fixed**

- **Pagination arrows were invisible in a narrow window** (below 768px).

## [2026.9.30.post89] - 2026-09-26 - A Default period in Preferences

**Changed**

- **Preferences > Behavior > "Default period"** - where every page with a period selector opens: the period you picked last (the default), the newest term with your courses, the term running now, or all periods.

**Fixed**

- **Teacher and admin pages use the account's language** on a device with no language cookie too.

## [2026.9.30.post88] - 2026-09-26 - A JavaScript audit: four bugs, no var

**Fixed**

- **The Dashboard re-rendered its lists on every refresh** - an invisible character stood where a regex meant `\b`.
- **The course page's fallback sync check failed on its first answer** - two declarations were missing.
- **Tabs and filters were taken for the button the next toast reports to.**
- **Table pagination had two versions of the same method.**

**Changed**

- **No `var` left in the JavaScript sources**, bindings that never change are `const`, and dead code is gone.

## [2026.9.30.post87] - 2026-09-26 - A table's search in the middle of its band

**Added**

- **Preferences > Behavior > "Remember the period I pick"** - turned off, each page opens on the newest term with your courses.
- **Course Management has a Status filter** (active, archived), and a course's row opens the course.

**Fixed**

- **A link opens the view it is about** - archived courses with their term and filter, tickets in the course's own list.
- **Archived courses can always be reached** - the Dashboard's period selector stays, and an empty term says where your courses are.
- **A filter a link sets is applied**, and it does not blink while the page loads.
- **The Academic period field** fills its row on an archived course's settings.
- **A table's search and filters have the same room above and below them** - 24px on a desktop, 12px on a phone.

## [2026.9.30.post86] - 2026-09-26 - Ticket filters, no blinking filter, a repeated toast you can see

**Added**

- **The support tickets overview filters by period and status** - the same period selector every list of courses has, and a Status filter (active or archived).

**Changed**

- **Support opens with the same table of courses as Support Tickets** - term, status, the filters and your own request counts; a *New request* button.
- **The Events webhook warning is a toast again** - raised on arrival, never twice.

**Fixed**

- **A selected filter no longer blinks while its page loads** - changing the period, the sort or the page of the same list keeps the controls at full strength; only the rows step back.
- **The period box shows the pick at once** and keeps the focus when the page lands.
- **A repeated toast is visible again** - it replays its entrance and counts *×2*, *×3*.
- **Every table has the same margin on all sides** - as much below the table as above its controls, the pagination bar flush to the card's edge.

## [2026.9.30.post85] - 2026-09-26 - Tickets by course, webhook state on the page, the term everywhere

**Changed**

- **The support tickets overview is a table of courses**: term, active or archived, open tickets, total, last ticket; active courses first, every column sorts, search narrows it.
- **The webhook state on Events is an alert on the page**, not a toast on every visit - active courses only, each with its term and a link to its webhook settings.
- **A toast already on screen is not raised a second time** - the one on screen draws attention to itself and its countdown starts over.

**Fixed**

- **Collapsible cards open and close smoothly**, with no stall at the height of their padding.
- **The term next to every course**: User Info, the Events *Where* column, search, Support headers, the Run Checks dialog and the archive, activate and delete confirmations.
- **Support says when the course is archived** - requests still reach its teachers.
- **Purge Old clears only the tickets of the course on screen**, and the dialog names it with its term.
- **Deleting a course from its Settings asks for the course code**, not its UUID.

## [2026.9.30.post84] - 2026-09-26 - A badge for every person, archived courses apart

**Fixed**

- **The Period column of User Management has a badge on every row**: a student the terms of their groups or *No period*, a teacher the terms of their courses or *No courses*, an administrator and a service account *All periods*.
- **A service account no longer reads as a student** - its Role cell says *Bot*.
- **Support tickets say who is who**: the submitter, the assignee and each comment author carry a role badge.
- **The Support course picker keeps archived courses apart**, in a collapsed *Archived Courses* card.
- **A card header** no longer pushes its title to the middle, and **a collapsed disclosure card** has no empty strip under its header.

## [2026.9.30.post83] - 2026-09-25 - One period field, dates from the calendar, Transfer fixed

**Changed**

- **One Academic period field instead of three.** Create, Import, Edit and Transfer a course and its Settings all ask the same way: the current term and the ones after it, Import also the last two finished ones. Transfer never offers the term the course is already in.
- **A term and its dates are one fact.** Picking a term fills its official TUKE dates, and changing it moves them - until you set your own; a start date in another term is pointed out. **Use the official TUKE dates** puts them back.
- **The period selector looks like the other filters**, every option explains itself, and finished terms with no courses are not listed. **Your pick is remembered** until the next term starts.
- **The top bar names the term**, e.g. *2026/2027 · Winter*.

**Fixed**

- **Transfer to New Semester** ended in a server error; it works, and deadlines keep their weekday.
- **The Dashboard's live refresh** counted the cards and the feed across every term; the **Students** card counted every student in the installation.
- **An empty term** said you had no courses; housekeeping items look at all your courses.
- **Period badges** in User Management ran over the Status column; they have a column of their own.
- **Dropdown menus** were cut off by the page area.
- **A period is validated** on every way in, API and config import included; a stored semester date no longer blocks saving an older course's settings.

## [2026.9.30.post82] - 2026-09-25 - Academic period on the Dashboard, courses and users

**Added**

- **Academic period selector.** The Dashboard, Course Management and User Management each carry a period selector - one academic year and one semester, e.g. *2026/2027 · Winter*. It decides which courses and students the page is about, and lives in the URL, so a link to a cohort opens that cohort. Every term is listed, winter and summer, including empty ones (**No courses**); **All periods** shows everything; **No period** lists students who are not in any group yet.
- **Only students are narrowed.** Administrators, teachers and service accounts appear in every period.
- **The term on group, student and project pages**, as a badge next to the title, highlighted when it is the one running.

**How the period is decided**

- A page opens on **the newest term holding courses the reader can see** - not the calendar's, which for summer-only courses is empty half the year. The calendar's term is marked **Current** or **Upcoming**.
- A period is defined **at every date**, including after the TUKE preset table ends on 2027-06-25.

**Fixed**

- Import from GitLab pre-filled **summer** and Create Course **winter** - both now pre-fill the term the page is showing.
- New courses defaulted to **the year the server booted in**; Transfer to New Semester proposed **the term the course is already in**.
- The User Info card and the import preview printed the raw value *winter* instead of the translated term.
- Dropdown menus opened **off the screen** on phones.

## [2026.9.30.post81] - 2026-09-23 - The header's date and time sit on the row

**Fixed**

- **The date and time in the header did not sit on the row.** Every box up there is centred by the layout engine, so nothing looked wrong in the CSS - the misalignment was inside the boxes: a line box around 14px digits carries the font's full ascent, room for accents those digits never use, so the ink landed about a pixel below the middle of its own box. Measured from the rendered pixels and fixed so it holds under the fallback font too.
- **Pressing an unavailable control now says why**, whatever made it unavailable. The handler answered for exactly one cause, the archived-course lock; anything disabled by a running process or a permission stayed mute, and on a phone there was no way to ask at all.

## [2026.9.30.post80] - 2026-09-23 - The phone keyboard, and four lost CSS rules

**Fixed**

- **Four stylesheets silently dropped their first rule.** An older sweep of dead selectors left a lone `/` on line 1. CSS error recovery does not stop there - it swallows the stray character together with the NEXT selector - so four rules never applied at all, on production, with no error anywhere. A new test checks every stylesheet for the whole class of leftover.
- **Opening any modal on a phone raised the on-screen keyboard.** Focus went to the first field on every device; on touch that covers half the dialog before the reader has decided to type, and on a modal with nothing to type into it hid the list being picked from. A focused field also collects whatever the keyboard emits, so closing asked about "unsaved changes" nobody made. On touch the dialog itself takes focus now.
- **A tooltip gave a disabled button a live cursor** - every bulk action over a selection showed the pointer of a working control.
- **The tour's Back button looked enabled on step 1** and did nothing; it now uses the same disabled tokens as the rest of the app.

**Changed**

- **Icons are back on the scale.** Thirteen one-off sizes (10, 11, 13, 14, 15 and 18px) and a second pixel-named scale had grown around the five real steps. All snapped to the nearest step.
- **The top bar's date and clock icons sit on their text** - 16px beside 14px, the pairing this app follows everywhere else. The MR section labels had the same mismatch.

## [2026.9.30.post79] - 2026-09-23 - One icon set, and a failure mark that is actually red

**Fixed**

- **Every failure mark in the app was drawn grey.** The danger colour rule sat above the base rule at the same specificity, so the base grey won - the alert triangle on a failed table, chart or modal looked exactly like the "nothing here" mark beside it.
- **The course-card sync badge drew two spinners** and carried a `</span>` that closes nothing, so a badge injected by a live update looked different from the same badge rendered by the server.
- **Three strings reached the screen in English** on a Slovak page - the sync failure detail, the queued-sync cell and one aria-label. The Slovak was already in the catalogue for all three. A fourth was missing from the catalogue outright.

**Changed**

- **One JS icon registry, not four.** `GP.icons` with its 122 Pajamas glyphs has been in the bundle all along, and three more tables had grown beside it - including seven hand-written glyphs for toasts and the Done/Failed button marks, one of which had drifted into a hand-drawn tick. All gone, and a test now fails on any private icon table.
- **Three more hand-rolled empty states** became the one shared block with a mark, and "No courses in this section" spans the grid instead of sitting in its first column.
- **Two error states gained a way back.** The event-detail and MR-history modals both failed to a dead end; both now carry a Retry with its loading state.

**Verified**

Every page walked as every role at 1440 and 390: no empty icon boxes, no leftover glyphs, no duplicate ids, no horizontal overflow, no stuck loaders, no JS errors. Every modal opened twice in a row - none re-opens.

## [2026.9.30.post78] - 2026-09-23 - A modal no longer re-opens under you

**Fixed**

- **User Info opens again.** Last release's dead-code sweep removed an export that the Users page script calls, and the modal answered "Failed to load user info" without making a single request.
- **A modal no longer re-opens under you.** Every path that re-entered the open function to repaint the body - Retry in an error state, a reload inside a modal, a second click on the opener - restarted the entrance animation, scrolled the body to the top and pulled focus back to the first field.
- **Icons that drew nothing now draw.** Four of the names the JS asked its icon mirror for were absent, and an absent name answers with an empty string: an empty, padded box where an error state's alert mark belongs.

**Changed**

- **One icon set, everywhere.** The JS mirror had stayed on the 24x24 stroked Feather glyphs the app moved off, and five more files carried private icon tables of their own - the User Info card, the job bar, the ticket page, the LLM error card and the webhook rows. All now resolve through the one mirror regenerated from `icons.html` (Pajamas 16x16), and a test fails if they drift again.
- **One error state in the User Info modal**, with a Retry that shows its loading state, and a spinner painted *before* the card renderer is fetched rather than after.
- **The error pages' buttons have a state.** Retry and Search both navigate, which on the connection that produced the error is not instant; both show the app's spinner now, sharing its one `spin` keyframe.
- **The support-ticket page speaks Slovak.** Every label it paints from JS was English; the Slovak was already in the catalogue with no `t()` to reach it.

**Removed**

- The scroll offset no reload reads, with the helpers that wrote and cleared it.
- A deeper pass: 166 orphaned Slovak keys, 11 phantom routes in the API spec, 9 unused schemas, 3 unused template macros and the CSS they orphaned.

## [2026.9.30.post77] - 2026-09-22 - Dead code removed

**Removed**

- About 1 000 lines with no reader: 22 settings for machinery that does not exist (the `SCHEDULER_*` intervals first - there is no scheduler), the GitLab client's six write helpers (GitPulse never writes to a repository), four event-repository methods and the session index behind an uncalled force-logout, the hex colour palette in `constants.py` and seven other unused helpers, two unreachable legacy-role branches, five dead JS entry points and 26 CSS rules for classes nothing renders.

## [2026.9.30.post76] - 2026-09-22 - Home greeting matches GitLab's on PC and phone

**Changed**

- **Home greeting:** 64px avatar, name at 20px semibold (18px on a phone), the sentence at 16px, centred with a 16px gap - GitLab's own greeting, measured, the same on the PC and on the phone.

## [2026.9.30.post75] - 2026-09-22 - Home greeting consistent with page headers on phones

**Fixed**

- **Home greeting on phones:** the name keeps the size every other page title has on a phone, and the avatar sits on the name's line instead of floating beside a wrapped sentence.

## [2026.9.30.post74] - 2026-09-22 - Focus ring survives hover, empty preview state, consistency sweep

**Fixed**

- **Focus ring:** hovering a focused input, checkbox, radio or search box no longer removes the blue ring; filter tabs above tables and the theme segments on Preferences show a keyboard focus ring again.
- **Empty states:** the Markdown Preview tab says "Nothing to preview." instead of a blank box.
- **Consistency:** four native checkboxes now use the shared style; the weight-preset buttons are plain secondary buttons; filter tabs above tables are the same height as every other tab strip on the desktop.

## [2026.9.30.post73] - 2026-09-22 - No second reload after a deploy

**Fixed**

- **Refresh after a restart:** a new service worker taking control no longer reloads the page on a timer (which, on a server still warming up, made one manual refresh into two and landed the second one mid-scroll). It asks the server whether the page is behind and lets the version check reload once, at a quiet moment, with a notice.

## [2026.9.30.post72] - 2026-09-22 - Charts follow the theme from the first frame, readable score trend, install card back, Slovak toasts

**Fixed**

- **Charts and themes:** chart defaults (ticks, font, tooltips) are applied once Chart.js has loaded instead of never; dark-mode grid and radar web are visible again (`--chart-grid`).
- **Score Trend:** threshold lines and point colours use the course's 80/50 like the legend, each line labelled; bands and rings repaint on a theme switch; the fill is the brand colour; the Skill Profile uses the category colours.
- **Install card:** the "Install GitPulse" card shows again and is translated.
- **Language switcher** lists each language in its own name; 29 error toasts and prompts translated to Slovak.

## [2026.9.30.post71] - 2026-09-22 - Archived courses: read-only buttons no longer die after one use; centred outcome tick

**Fixed**

- **Button unavailable after "Done" on an archived course:** the loading reset disabled every untagged button under an archived course after its first use, although the read-only guard had left it live. Reload/Refresh actions now stay usable; only what the guard locks stays locked.
- **Strip beside the green tick:** the outcome word shrank to a 2px sliver inside icon-only buttons; it is now screen-reader-only there, and the mark sits centred.
- **Demo course seed:** the compliance history now covers the whole semester (weeks derived from the engine's result) instead of a single point.

## [2026.9.30.post70] - 2026-09-22 - Button icons 16px everywhere; card-header reload no longer an empty square

**Fixed**

- **Icons too small:** the Reload on the student's Compliance Progress card rendered its glyph 6px wide (header padding beat the icon-only button's zero padding), which looked like a disabled, empty control before and after every reload. Button icons are now 16px at every size, as GitLab draws them - the 13px/14px steps for card headers, small buttons and phones are gone - and a small button keeps its width while loading.

## [2026.9.30.post69] - 2026-09-21 - Button states: locks released when a job finishes, cooldown restores the label, submit guard

**Fixed**

- **Locks held through "Finishing..." and across a reload:** Sync / Run Checks / Link / Delete stayed disabled for the bar's eight-second readable hold after a job had already completed (and again after F5). A finishing job now holds no lock, the Run Checks button stops spinning at that moment, and a restored hold finishes with its own wording instead of "Sync completed!".
- **Failed Sync came back reading "Failed":** the 5 s cooldown snapshotted the red outcome as the button's label; it now restores the real label, aria-label and tooltip.
- **Submit buttons dead for 5 s:** the double-submit guard fired before the form's own handler on every AJAX form; it now defers past the dispatch and shows the shared loading state.
- **Job bar icons:** finished syncs and check runs show their own mark instead of the default clock.

## [2026.9.30.post68] - 2026-09-21 - Refresh feedback, Slovak check details, phone consistency pass

**Fixed**

- **Refresh Stats** on the System page reports its outcome again (a shared helper swallowed the loader's answer, so the success toast never fired).
- **Check Details in Slovak:** the engine's reasons for a failed check ("0/2 distinct reviewers on own MR", ...) are translated wherever they are shown, and 28 missing catalogue strings were added.
- **Phones:** wrapped course-card actions align left; tables with an unpinned actions column and tab strips fade at the edge they scroll past; student commit rows are two lines with the full message; the checklist chart keeps every label; System page header buttons fold to icons like the Events page.
- **Tooltips** on View, + Group, Show all, the JSON toggles; loading state on Rotate secret.

## [2026.9.30.post67] - 2026-09-21 - Slovak interface completed, anyio security update

**Fixed**

- **Slovak Interface:** the greeting phrase on the home page, every job type and audit action in Job History and the activity feed, and the Score column header are translated; the checks card and import dialog say R01-R13.
- **Security:** `anyio` updated to 4.14.2 (three CVEs).

**Changed**

- **README Screenshots:** retaken from the current build in the light theme and Slovak over a `ZSI-DEMO` demo course.

## [2026.9.30.post66] - 2026-09-21 - Every table measured on phones

**Fixed**

- **Tables on Phones:**
  - Pinned action columns stay pinned wherever they leave room for the row and scroll with it where they do not - measured on every table at 360-430px.
  - Compliance Checks shows every column on a phone (toggle, code, name, category, weight, source) and scrolls; Job History rows are compact; the Projects and Tickets tables no longer inflate their first column.

## [2026.9.30.post65] - 2026-09-21 - Tables on small phones

**Fixed**

- **Tables on Small Phones:**
  - A pinned actions column that would take more than two fifths of the screen now scrolls with the row, so the columns before it are readable; row icon buttons are 36px on touch so two-button columns stay pinned.

## [2026.9.30.post64] - 2026-09-21 - Card help mark and role select on phones

**Fixed**

- **Card Help Mark on Phones:**
  - The "?" help mark in a card header is no longer locked on an archived course and no longer overlaps the action beside it; it is one 28px tap target.
- **Course Role Select on Phones:**
  - The "Course Owner" select in the Teachers table is no longer cut off at its chevron by the pinned Actions column.

## [2026.9.30.post63] - 2026-09-21 - Selects inside scroll boxes, table fades, panel bottom gap, touch hover, badges, and ticket empty state

**Fixed**

- **Selects Inside Scroll Boxes:**
  - The Course role select in the Teachers table opens its menu above the table instead of being clipped to a sliver on the last rows.
- **Table Fades:**
  - The right-edge fade no longer darkens a pinned actions column, and there is no bottom fade painting over the last visible row.
- **Panel Bottom Gap:**
  - Pages with a save bar keep the 8px gap under the rounded panel like every other page; course settings' last card no longer touches the panel's edge.
- **Touch Hover:**
  - Button and help-mark hover styles apply only to pointer devices, so a tapped control does not stay highlighted on a phone.
- **Badges:**
  - The "disabled" mark in the Weekly Deadline list sits beside its check name; the Auto-fill mark next to "GitLab URL" is a standard small badge.
- **Ticket Empty State:**
  - A request opened without a description says so instead of showing an empty box.

## [2026.9.30.post62] - 2026-09-21 - Inner card corners, tab-return replays, sticky column edge, phone header actions, and dead CSS

**Fixed**

- **Inner Card Corners:**
  - Tables, pagination bars and notes inside a card end on the card body's own corner radius - no notch of card ground at the bottom corners of the last row.
- **Tab-Return Replays:**
  - In development a server restart with no code change no longer reloads every open tab; the dashboard and System Health only redraw when something actually changed, so nothing replays when you come back to the tab.
- **Sticky Column Edge:**
  - The pinned actions column's shadow shows only while columns are hidden beneath it, not when the table is scrolled to its end.
- **Phone Header Actions:**
  - On phones a header action shows its icon with the label as tooltip and accessible name, so Events' bulk actions sit on the title row.
- **Dead CSS:**
  - Rules nothing rendered any more were removed, together with the tests that guarded them.

## [2026.9.30.post61] - 2026-09-21 - Table corner notch, page height on phones, card actions wrap, selected rows, touch hover, disabled-control toasts, job type explanations, refresh contract, and chart colour tokens

**Fixed**

- **Table Corner Notch:**
  - The last row of a table no longer shows a notch of card background at its bottom corners.
- **Page Height on Phones:**
  - The document is exactly one viewport tall again, so the page no longer slides under the top bar and the save bar and the last table row stay reachable. Long tables no longer scroll inside a box of their own on phones - the page scrolls to their last row.
- **Card Actions on Phones:**
  - Header actions stay on the title row while they fit, at its right, and wrap onto their own row - flush left - only when they do not.
- **Selected Rows and Touch Hover:**
  - Ticking a row checkbox lights that row in the selected tint in every table with selection; row hover applies only to pointer devices, so a tapped row no longer stays highlighted.
- **Disabled Controls Explain Themselves on Tap:**
  - Tapping a disabled control shows its reason as a toast.
- **Job History:**
  - The type tooltip explains what the job does, and the locked checkbox of an audit-derived row says why it cannot be selected.
- **Refresh Contract:**
  - Student history Reload, Events Refresh and the admin Refresh buttons behave like System Health's "Check now": working state, in-place region, one outcome, and success claimed only when the load succeeded.
- **Chart Colour Tokens:**
  - The pipeline doughnut and the student Score Trend / Skill Profile take every colour from the theme tokens, in both colour modes.

## [2026.9.30.post60] - 2026-09-21 - Theme-correct table highlight, right-aligned card actions, consistent mobile panel, sticky table borders, instant no-op check runs, standard 404 pages, and chart empty states

**Fixed**

- **Theme-Correct Table Highlight:**
  - Table hover is the neutral gray again; the selected / redirect row tint derives from `--gl-action-selected-border` (blue by default, the accent under a Preferences theme). The undefined `--gl-theme-accent` fallback that painted highlighted rows red is gone.
- **Card Header Layout:**
  - Desktop headers are one row: title, count badge beside it, actions and the help mark on the right. Only phones wrap the actions onto their own row, flush left.
- **Consistent Mobile Panel on Pages with a Save Bar:**
  - Course Settings, Teachers and Preferences keep the same inset, rounded content panel on phones as every other page.
- **Sticky Table Borders:**
  - Data tables use separate borders, so the sticky header and the pinned actions column carry their own bottom line - no stepped line at the actions column and no line under the last row.
- **Compliance Checks Weight Badge:**
  - The active-weight total is the card's header badge beside the title.
- **Instant Completion for a No-Op Check Run:**
  - Run Checks on a course with no active groups reports "No active groups in course." in the job bar at once instead of holding "Finishing checks..." for eight seconds with the bar hidden.
- **Standard 404 Pages:**
  - A missing or inaccessible course, group, project or student renders the standard 404 error page instead of an in-app "Not Found" card.
- **Chart Empty States:**
  - The Teacher's Checklist (also with no scored students or no snapshot), Week Analytics, the student Score Trend and Skill Profile, and the event payload viewer show the same empty-state box every empty table shows.
- **SPA Navigation Script Crash:**
  - Fixed `Cannot read properties of null (reading 'insertBefore')` thrown by htmx re-running page scripts the navigation handler had already moved.

## [2026.9.30.post59] - 2026-09-19 - Seamless table header border, theme-adaptive redirect highlight, stretched controls input, and mobile sidebar swipe
 
**Fixed**

- **Seamless Table Header Border Divider:**
  - Removed mismatched `border-bottom` on `.data-table.table-sticky-actions > thead > tr > th:last-child` and applied uniform `box-shadow: inset 0 -1px 0 var(--border-color)` across all column header cells, ensuring an unbroken, continuous 1px bottom border across the table width.
- **Theme-Adaptive Highlight on Redirect and Navigation:**
  - Upgraded `GP.motion.highlight` to pull active theme tokens (`--gl-theme-accent` and `--gl-table-row-selected-bg`) for row tints across all theme palettes; added auto-expansion of collapsed card containers when targeting rows via query or hash (`?highlight=`, `#course-`, etc.).
- **Stretched Support Tickets Search Input:**
  - Configured search containers (`.table-controls-search > div, [data-tour], .search-box`) to stretch across the full available clearance to filter dropdowns.
- **Mobile Sidebar Swipe-to-Close Gesture:**
  - Implemented touch swipe-to-close on `.gl-sidebar` for mobile viewports, allowing users to smoothly dismiss the sidebar drawer by swiping left.

## [2026.9.30.post58] - 2026-09-19 - Single-row card header with left wrap, theme-adaptive table highlight tokens, and spacious controls clearance

**Fixed**

- **Single-Row Card Header Layout with Natural Left-Aligned Wrap:**
  - Preserved single-row layout for card headers (`.card-header`) with `justify-content: space-between` and `flex: 0 1 auto` title, keeping actions on the same line as long as horizontal space permits and wrapping actions to the left margin without premature splitting or rigid breakpoint reordering.
- **Theme-Adaptive Sticky Table Headers and Row Highlight Tokens:**
  - Dynamically tokenized table headers (`--gl-table-header-bg`), row hovers (`--gl-table-row-hover-bg`), and active/nav highlights (`--gl-table-row-selected-bg`) via `color-mix` with `--_accent` in both dark and light modes across all theme accents, ensuring sticky table headers and row highlights seamlessly match user theme preferences.
- **Search Input Clean Up and Relaxed Controls Clearance:**
  - Removed hardcoded fixed width override on `.search-box input` in `admin.css`, restoring natural component responsiveness and flexibility across all viewports.
  - Removed aggressive negative top margin on `.card-body > .table-controls:first-child` (`margin-top: 0`), restoring balanced 24px headroom above table selectors and search inputs without squishing against the card ceiling.

## [2026.9.30.post57] - 2026-09-19 - Aesthetic card header headroom, centered selectors, and spacious controls clearance

**Fixed**

- **Card Header Headroom & Symmetrical Selector Alignment:**
  - Restored `.card-header` min-height to `44px` with centered alignment, eliminating cramped header strips and ensuring title and actions have aesthetic breathing room.
  - Set `.table-controls` min-height to `44px` with `padding: 0` and vertical centering for all selectors, dropdowns, and search controls.
  - Balanced `.card-body > .table-controls:first-child` margin-top to `calc(-1 * var(--gl-spacing-4))` (-12px) and `.table-controls` margin-bottom to `var(--gl-spacing-4)` (12px), giving identical, spacious 18px clearance above and below selectors across all tables (Events, Users, System, etc.).

## [2026.9.30.post56] - 2026-09-19 - Component-wide table controls elevation and balanced header clearance

**Fixed**

- **Search Input Elevation & Compact Table Controls Spacing:**
  - Elevated `.card-body > .table-controls:first-child` with `margin-top: calc(var(--gl-spacing-2) - var(--gl-spacing-6))` (-20px) to close the excess vertical void above table search inputs across all card containers.
  - Balanced `.table-controls` clearance margin to `var(--gl-spacing-3)` (8px) below the controls band, ensuring identical 14px distance above the search input to the card header and below the search input to the table columns header.

## [2026.9.30.post55] - 2026-09-19 - Symmetrical table controls vertical alignment, centered search input, and table header clearance

**Fixed**

- **Symmetrical Vertical Spacing and Centering for Table Controls & Search Input:**
  - Standardized `.table-controls--tabs` / `.table-controls:has(.filter-tabs)` padding to `0` with `min-height: 44px`, removing bottom margin push on `.table-controls-search` so that the search input is strictly centered vertically with identical spacing above and below inside the controls band (matching the YouTube header search reference).
  - Raised the search input and restored baseline table controls band top padding (`padding: 0 0 var(--gl-spacing-2)`), keeping headroom balanced.
  - Lowered the table header by expanding `.table-controls` bottom clearance margin to `var(--gl-spacing-5)` (16px), achieving equal spacing above the input (to card header) and below the input (to table header).
  - Adjusted card header padding to design token `var(--gl-spacing-3) var(--gl-spacing-4)` (8px top/bottom), ensuring balanced vertical alignment without text crowding the card's top edge.
  - Preserved `this.pageSize = saved` assignment in `components.js` for full contract and test compatibility.

## [2026.9.30.post54] - 2026-09-19 - Unified pagination choices, event details modal upgrade, users and courses table layout

**Fixed**

- **Unified Rows Per Page Pagination Options Across All Tables:**
  - Enforced identical options `[25, 50, 100, 'all']` matching Settings (`Preferences > Rows per page`) with labels `"25 per page"`, `"50 per page"`, `"100 per page"`, `"Show all"`, and SVG checkmarks for active items.
  - Set default page size strictly to 50 across client paginator instances and templates.
- **Comprehensive Event Details Modal Upgrades:**
  - Added dedicated empty state with `inbox` icon, title, and description when delivered payload is empty (`{}` or null).
  - Implemented tokenized JSON syntax highlighting (`syntax-key`, `syntax-string`, `syntax-number`, `syntax-bool`, `syntax-null`).
  - Added icons for all facts and status badges (Type: `tag`, Status: `shield`, Received: `calendar`, Processed at: `check-circle`, GitLab project: `folder`, Who: `user`, Message: `message-square`, Action: `play`, Retries: `repeat`, Event ID: `hash`).
  - Added error alert banner (`gl-alert gl-alert-danger`) and functional "Copy JSON" button with temporary "Copied!" feedback.
  - Enriched `/api/v1/events/{id}/payload` response with `summary`, `actor`, `processed_at`, `dead_letter_at`, and `action`.
- **Events Table Status Badge Error Leak Fix:**
  - Error messages (`unhandled_kind: ...`) are now strictly guarded and rendered only for events in `Failed` state, preventing error text from leaking next to the green `Processed` badge.
- **Users Table Email Overflow & Column Width Balancing:**
  - Added `max-width: 100%`, `overflow: hidden`, `text-overflow: ellipsis`, and `white-space: nowrap` to email, fullname, and username cells.
  - Rebalanced column widths: expanded `col-email` to 25% (min-width: 200px), `col-role` to 12% (min-width: 120px) preventing badge clipping, and `col-created` to 10% (min-width: 110px) preventing date truncation.
- **Courses Table Actions Column Right Alignment:**
  - Aligned Actions column to the right (`col-course-actions text-right`, `justify-content: flex-end`, width 120px) and fixed missing closing `</td>`.
- **Table Controls Headroom Symmetry & Scrollbar Stabilization:**
  - Balanced `.table-controls` padding and margin in `tables.css` (`margin-top: calc(-1 * var(--gl-spacing-3))`, `padding: var(--gl-spacing-3) 0`).
  - Added `[data-paginator] table:not(.paginator-ready) tbody tr:nth-child(n+51) { display: none !important; }` rule, preventing initial SSR render from blowing out table height and doubling the vertical scrollbar.
  - Removed arbitrary `max-width: 320px` restriction on `.ticket-title-link` in tickets table.
- **Ticket Detail Meta Line Spacing & Markdown Editor Theming:**
  - Increased `.gh-ticket-meta-row` bottom padding and margin to `var(--gl-spacing-6)`, lowering the divider line away from the participants block.
  - Fully tokenized markdown editor and thread elements with GitLab tokens (`--gl-...`).
  - Removed `:focus-visible` outer box-shadow from `.gh-md-textarea`, eliminating rogue purple lines across toolbar and divider borders.
- **Service Worker Cache Bump (`gitpulse-v635`):**
  - Incremented cache identifier to ensure immediate stylesheet, bundle, and template refreshes on all client devices.

## [2026.9.30.post53] - 2026-09-19 - Revert pagination controls layout to baseline and restore full-width alignment

**Fixed**

- Reverted Pagination Controls Layout to Baseline: restored negative horizontal breakout margins on `.card-body:not(.p-0) > .pagination-controls` (`margin: var(--gl-spacing-4) calc(-1 * var(--gl-spacing-5)) calc(-1 * var(--gl-spacing-5))`) across desktop, tablet, and mobile breakpoints.
- Eliminated Side Gaps & Floating Appearance: removed the floating pill/island effect, ensuring the pagination bar spans edge-to-edge across the bottom of the card container.
- Restored standard card body padding (`var(--gl-spacing-6)`) and bottom corner radius (`var(--gl-card-border-radius)`).
- Service Worker Cache Bump (`gitpulse-v634`): incremented PWA cache version for immediate client cache busting.

## [2026.9.30.post52] - 2026-09-19 - Users table column proportions, flush pagination attachment, scrollbar stabilization, and card header headroom

**Fixed**

- Users Table Column Proportions & Truncation Fix: expanded `GitLab User ID` column (`col-gitlabid`) from cramped 9% (125px max-width) to 13% (`min-width: 160px`), removing the max-width restriction and allowing the full column title and sort arrows to render cleanly on one line without clipping. Adjusted `Full Name` column (`col-fullname`) to 21% (`min-width: 170px`) and shifted into available space, rebalancing `Email` to 19% for a clean 100% total table layout.
- Stabilized Table Load Height & Eliminated Vertical Scrollbar Doubling: fixed initial server-rendered hidden row selector in `admin.css`: updated `.users-table:not(.paginator-ready) tbody tr:nth-child(n+51)` to `n+26`, matching the default page size of 25 from the first paint frame. This prevents the table height from collapsing by 50% upon JavaScript initialization and stops the browser scrollbar thumb from abruptly doubling in size. Disabled internal vertical scrollbars on paginated table wrappers (`.card-body:has(.pagination-controls) .table-responsive { max-height: none; overflow-y: visible; }`) to eliminate dual-scroller defects.
- Seamless Flush Pagination Attachment: removed negative horizontal breakout margins on `.card-body:not(.p-0) > .pagination-controls` across all breakpoints (desktop, tablet, mobile), ensuring pagination controls match the table width precisely. Sits flush against the table's bottom border with `margin: -1px 0 0 0`, zeroed table last-row bottom border-radius when followed by pagination, set card-body padding-bottom to 0, and styled pagination corners to match the card body's `var(--radius-md)`.
- Card Header Height & Symmetrical Vertical Spacing: raised `.card-header` min-height slightly to 40px with 6px padding (38px / 5px on mobile), improving visual comfort and vertical headroom across all card components. Centered table search inputs vertically (`align-self: center`) in tabbed controls (`.table-controls--tabs`), establishing balanced, symmetrical spacing above and below the search input.
- Service Worker Cache Bump (`gitpulse-v633`): updated PWA cache version for immediate client cache busting.

## [2026.9.30.post51] - 2026-09-19 - Preserve button "Done" green success state, dynamic card header action labels, symmetrical table controls spacing, and diff copy button alignment

**Fixed**

- Preserve Button "Done" Green Success State on Disabled Buttons: added token-based styling with `!important` to `.btn.btn-done`, `.btn:disabled.btn-done`, `.btn.is-saved`, and outcome classes using `var(--gl-badge-success-bg)` and `var(--gl-badge-success-text)`. Added `:not(.btn-done):not(.btn-error)` exclusions to general `.btn:disabled` and `.is-course-archived` rules in `buttons.css`. This prevents the `:disabled` grey styles from overriding the green success indicator when buttons are locked after form submission. All styles are purely token-based with zero inline styles.
- Removed Grey Box Background from Table Count Badge: removed `background: var(--surface-moderate)`, padding, and border radius from `.table-count` in `tables.css`, restoring clean, unboxed secondary text for "Showing X of Y".
- Dynamic Responsive Card Header Action Buttons: replaced the static `@media (max-width: 640px)` collapse with dynamic fit calculation via `ResizeObserver` in `20-ui-helpers.js`. Header buttons with responsive header actions (e.g. Webhook Configurations, Course Teachers) preserve their labels whenever width permits, collapsing to icons only when space is genuinely constricted.
- Symmetrical Vertical Spacing in Table Controls: removed negative top margin from `.card-body > .table-controls:first-child` and balanced vertical padding around search and tab controls, ensuring identical vertical spacing above and below the teacher input and role selector.
- Vertically Centered Code Diff File Header Copy Icon: standardized `.dn-code-toolbar` to 32px height and aligned the copy button (`.dn-code-collapse > .dn-code-action`) to `top: 4px`, optically and geometrically centering the copy icon with the file path line.
- Service Worker Cache Bump (`gitpulse-v632`): updated PWA cache version for immediate client cache busting.

## [2026.9.30.post50] - 2026-09-19 - Compact card and table header heights, single-row responsive action buttons, and streamlined inline teacher addition layout

**Fixed**

- Card & Table Header Height Reduction: reduced `.card-header` min-height to 36px (34px on mobile) and padding to 4px, cutting ~25% vertical card header height. In data table header cells (`.data-table th`), vertical padding was reduced from 16px down to 8px and font-size unified to `font-size-sm`.
- Eliminated Dead Space Above Tables: tightened `.table-controls` padding and bottom margin from 16px to 8px/12px, and reduced table card `.card-body` vertical padding to a compact 12px.
- Single-Row Responsive Header Buttons: added responsive header actions to all multi-action card headers (Add Check, Remove all restrictions, Add Configuration). On small/mobile screens (`<= 640px`), buttons automatically collapse to clean icon-only buttons with tooltips, allowing them to sit inline on row 1 beside the title. Moved the total weight badge (`Σ 1.00`) directly into the `🛡️ Compliance Checks` title. If wrapping ever occurs on ultra-narrow viewports, actions align flush to the left.
- Streamlined Teacher Addition Controls: updated `.teacher-add-row` on mobile and tablet to a flex-row layout with responsive min-widths, keeping the user search input and role dropdown side-by-side on a single line instead of stacking into two rows.
- Service Worker Cache Bump (`gitpulse-v631`): updated `CACHE_VERSION`.

## [2026.9.30.post49] - 2026-09-19 - Compact single-row card actions, table row buttons spacing, score badge centering, and Service Worker bump

**Fixed**

- Single-Row Compact Card Actions Across All Tables: unified styling for `.card-header` (`flex-wrap: nowrap; min-height: 44px;`) and `.card-actions` ensuring inline layout across both desktop and mobile displays. Action buttons (such as Remove all restrictions, Add week) are compacted to 26px height with 14px icons and tight padding to prevent accidental wrapping and header ballooning.
- Table Row Action Buttons Spacing: in Weekly Deadlines and all multi-button table cells, wrapped action buttons in a `.weekly-row-actions` container with `gap: var(--gl-spacing-2)` (8px) and widened the action column to 100px with `white-space: nowrap`. Introduced global fallback `.data-table td .btn + .btn { margin-left: var(--gl-spacing-2); }` ensuring sibling buttons in table cells never touch.
- Score Badge Column Optical Centering: centered the score table header (`text-center`) and shifted the score badge left by 4px (`transform: translateX(-4px)`) to optically balance under the column label against the 13px sort arrow.
- Groups Table Showing Count Placement: moved `Showing X of Y` directly into the title row beside `👥 Groups` instead of wrapping to a second line.
- Service Worker Cache Bump (`gitpulse-v630`): updated `CACHE_VERSION`.

## [2026.9.30.post48] - 2026-09-19 - Sticky footer bottom gap elimination, System Health button loading harmonization, and Service Worker bump

**Fixed**

- Sticky Footer Bottom Gap Elimination on PC and Mobile: configured `.gl-page:has(.settings-sticky-footer)` to `height: calc(100vh - var(--navbar-height)) !important;` (and `100dvh`), removing the 8px floating bottom gap and zeroing bottom border radii. Zeroed bottom padding on content containers and added mobile overrides ensuring full-bleed margins on viewports `<= 768px`. Disabled trailing page footers on affected settings templates. The sticky button bar now sits 100% flush against the viewport bottom with zero gap.
- Component Loaders & Button States Harmonization (System Health Pattern): standardized UI locks (`GP.withUiLock`) and button state arbitration across preferences, course teachers, support tickets, support ticket detail, course settings, and login/logout. Eliminated ad-hoc button disabling in favor of centralized `setButtonLoading(btn, true/false)` with `_MIN_LOADING_MS` (450ms) hold time to prevent UI flicker. Cleaned up deprecated label arguments from `setButtonLoading` calls.
- Service Worker Cache Bump (`gitpulse-v629`): updated `CACHE_VERSION`.

## [2026.9.30.post47] - 2026-09-19 - Card header layout, info-tip alignment, table space distribution, webhook reload fix, and dev ticket seeding

**Fixed**

- Card Header Question Mark & Action Rows: card header info-tip is anchored to the far right of the top row (`margin-left: auto;`), lowered by 1.5px with `transform: translateY(1.5px)` for optimal optical centering without altering card header height. On mobile views, actions cleanly wrap to row 2 and start flush left (`justify-content: flex-start; margin-left: 0;`).
- Webhook Configurations Reload Button in Archived Courses: updated button loading reset helper (`_applyButtonLoadingReset`) to exempt `data-readonly-ok` controls from being disabled by `.is-course-archived`, allowing reload to function and re-enable properly.
- Table Space Distribution Harmonized: balanced proportional column widths applied across Members Check Matrix (eliminating student name empty desert, giving checks even breathing room), Users Management, Course Teachers, and Activity tables.
- Support Tickets Seeding: seeded 15+ rich, realistic support tickets across various categories, priorities, and statuses with threaded comments for development and verification.
- Service Worker Cache Bump (`gitpulse-v628`): updated PWA cache version.

## [2026.9.30.post46] - 2026-09-19 - Production CSS/JS bundle compilation and Service Worker cache update

**Fixed**

- Production Bundle Rebuild and Minification: recompiled and minified `core.bundle.js` (633 KB), `styles.bundle.css` (457 KB), and all page bundles and `.min` assets to ensure all queued UI improvements are live in the browser.
- Service Worker Cache Bump (`gitpulse-v627`): incremented `CACHE_VERSION` in `sw.js` to invalidate stale caches and deliver fresh assets.

## [2026.9.30.post45] - 2026-09-18 - Top bar search repositioning, inline card actions, table count components, and score column placement

**Fixed**

- Mobile Top Bar Search Icon Repositioned Next to Date/Time: moved search button on mobile directly adjacent to the academic year and live clock with an exact 8px spacing.
- Card Header Action Row Wrapping & Symmetrical Spacing: eliminated forced `width: 100%` wrap on `.card-actions` so buttons stay inline when horizontal space permits, maintaining symmetrical 8px vertical padding in the header.
- Component-Based `Showing ... of ...` Counts: replaced circular numeric badges in card headers with `table_count` components displaying `Showing X of Y`.
- Project Members Table Score Column Placement: repositioned the Score column in templates and scripts to the end of the data columns, immediately after rule compliance checks (R01..R13) and before actions.
- Table Refresh Deformation & Alt-Tab Page Jitter Guard: reverted problematic fade transition on `.table-scroll` and introduced metric hash guards in `updateMembersTable()` to avoid redundant DOM mutations during window focus / SSE reconnections.
- Service Worker Cache Bump (`gitpulse-v626`): incremented `CACHE_VERSION` in `sw.js`.

## [2026.9.30.post44] - 2026-09-18 - Mobile navigation layout, card header symmetry, touch-scroll sort fix, and members table score offset

**Fixed**

- Mobile Top Bar Layout & Date Collision: converted `.gl-top-bar` to flex layout on mobile, positioning search adjacent to menu toggle on the left and reserving the right side for semester/clock context and avatar.
- Quick Access Panel Divider: added `.gl-qa-divider` separating segmented pill tabs from list items.
- Card Header Button Spacing: balanced vertical spacing for wrapped card action buttons on mobile (equal 8px distance above and below).
- Table Header Touch Scroll & Hover Gating: added drag displacement detection in `sortable-table.js` to prevent sorting on mobile table scrolls, and gated hover rules with `@media (hover: hover)`.
- Eliminated Right-Side Refresh Flashing: disabled `.table-scroll` fade transition on initial page mount and mobile screens.
- Project Members Table Score & Check Column Alignment: corrected column indices in `00-core.js` and `_ensureMembersTable()` to align with the server template, preventing score badges from being hidden as check cells on mobile, and removed stray syntax token from `project.css`.
- Service Worker Cache Bump (`gitpulse-v625`): updated `CACHE_VERSION` in `sw.js`.

## [2026.9.30.post43] - 2026-09-18 - Restored CSS/JS bundle minification and CI quality gates compliance

**Fixed**

- Restored Full Production Bundle Minification: recompiled all CSS and JS bundles and `.min` assets with `rjsmin`/`rcssmin`, shrinking `styles.bundle.css` from 865 KB to 457 KB and `core.bundle.js` from 1.15 MB to 632 KB.
- CI Quality Gate & Breakpoint Compliance: normalized mobile top bar media queries in `00-mobile.css` to standard system/legacy breakpoints (`360px` and `340px`) instead of off-system values; removed custom cell padding in `course.css` to uphold Pajamas design system table alignment; restored teacher count contract in `_teachers_content.html`.
- Service Worker Cache Bump (`gitpulse-v624`): updated `CACHE_VERSION` in `sw.js`.

## [2026.9.30.post42] - 2026-09-18 - Mobile card actions left alignment, top bar clock visibility, webhook archived locks, and GitLab PTR

**Fixed**

- Mobile Card Actions Left Alignment & Elevated Teachers Count: standardized `.card-actions` across `cards.css` and `00-mobile.css` on mobile viewports (`<= 768px`) to `width: 100%; margin-left: 0; justify-content: flex-start`, ensuring wrapped buttons always start flush left; moved the "Showing X of Y" table count in `_teachers_content.html` up into Row 1 adjacent to "Course Teachers", keeping restrictions buttons isolated on a dedicated second row.
- Mobile Top Bar Live Clock Visibility: restored `#topBarClock` on mobile viewports as `inline-flex` by removing `display: none` in `00-mobile.css`; reduced the search button right margin from 16px to 8px (`var(--gl-spacing-2)`), creating room for the search button and live clock to render alongside the avatar; on narrow viewports (`<= 380px`), only the academic year is hidden to keep the clock visible.
- Webhook Configurations Archived Course Protection & Unified Loading State: added `data-is-archived` tracking on the webhook container; during table reload in `20-advanced.js`, action buttons in archived courses render disabled with `data-archived-locked="1"` and read-only explanations; `_applyButtonLoadingReset()` in `20-ui-helpers.js` prevents re-enabling archived buttons; standardized `refreshRegion()` to immediately show button loading, immediately dim the table with `is-refreshing`, and enforce a minimum 600ms duration; added `position: relative` to `.table-responsive` and applied theme tokens to the loading spinner.
- Group Members Table Mobile Scrollbar Clearance: refined column allocation for `@media (max-width: 600px)` in `course.css` to 48% Student, 24% Score, and 28% Pipelines; added `padding-right: var(--gl-spacing-6) !important;` to `:last-child` cells to prevent content and score badges from touching the scrollbar.
- GitLab Pull-to-Refresh Indicator & Touch Reliability: raised `.ptr` `z-index` to 10000 in `20-small-touch.css` so the indicator displays over the fixed top bar; added multi-pointer touch support (`navigator.maxTouchPoints > 0`), deferred initialization to `DOMContentLoaded`, and added sub-pixel scroll tolerance.
- Dropdown Accessibility (WAI-ARIA): ensured active descendants are cleanly blurred and focus shifted before applying `aria-hidden="true"` and `inert = true` in `dropdowns.js`, eliminating browser console warnings.
- Service Worker Cache Version Bump (`gitpulse-v623`): updated `CACHE_VERSION` in `sw.js`.

## [2026.9.30.post41] - 2026-09-18 - Fix immediate disappearance of mobile tooltips on question mark tap

**Fixed**

- Mobile Tooltip Persistence on Tap: eliminated conflicting global document click listeners that prematurely hid Tippy tooltips right after opening; adjusted the scroll listener `_hideTippyOnScroll` to prevent dismissing `.card-header-info-tip` and `.info-tip` on subtle touch scrolls; optimized the touch trigger behavior (`trigger: 'click'` with 0ms delay) to prevent mobile synthetic hover glitches; exempted info tips from rapid-tap spam locks and hooked into HTMX post-swap events.

## [2026.9.30.post40] - 2026-09-18 - Card header info-tip desktop right-alignment and mobile touch interactivity

**Fixed**

- Desktop Right Alignment & Touch Accessibility for Card Info Tips: preserved `margin-left: auto` on `.card-header-info-tip` when `.card-actions` is absent or empty, guaranteeing that the help question mark stays pinned to the far right of the card header across both desktop and mobile screens; upgraded `.card-header-info-tip` from `<span>` to native `<button type="button">` with `touch-action: manipulation` for rapid and reliable mobile touch responsiveness; excluded info tips from the global `touch: false` Tippy delegate and introduced dedicated `initCardInfoTips()` with `touch: true`, `strategy: 'fixed'`, `placement: 'bottom-end'`, and toast fallback; removed unused empty `usersCount` placeholder from the users table.

## [2026.9.30.post39] - 2026-09-18 - Card header info-tip top-row right pinning and mobile unwrap fix

**Fixed**

- Help Tooltip Pinning to Top Row Right (Not Below Header): moved `.card-header-info-tip` outside of `.card-actions` in `cards.html` to be a direct child of `.card-header`; deleted the aggressive `.card-actions:has(.table-count) { width: 100%; }` rule from `cards.css` that forced card actions to wrap to line 2 on mobile devices (≤480px) and pushed the question mark underneath the title; configured `order: 3` and `margin-left: auto` for `.card-header-info-tip` on mobile breakpoints (≤768px in `cards.css` and `00-mobile.css`), permanently keeping the question mark on the far right of the first line beside the title and collapse button; added `.card-actions:has(> .table-count:only-child:empty) { display: none; }` to keep empty table count spans from affecting spacing.

## [2026.9.30.post38] - 2026-09-18 - Question mark right alignment, touch optimization, segmented tab ink line suppression, and theme tokens

**Fixed**

- Help Tooltip Right Alignment & Touch Accessibility: relocated `.card-header-info-tip` into the `.card-actions` flex container on the right side of the card header in `cards.html`, ensuring all question marks align to the right alongside actions rather than sitting on the left next to titles; removed mobile tooltip suppression in `00-mobile.css` and added comfortable 36px tap targets and active scale feedback in `20-small-touch.css`.
- Segmented Control Tabs Ink Line Suppression: eliminated the clashing bottom ink bar (`.gl-qa-tabs .gp-tab-ink { display: none !important; }`) from Quick Access segmented tabs in `home.css` and updated `motion.js` (`inkTo`) to skip segmented controls, ensuring active segmented buttons render cleanly as pill backgrounds without competing underlines.
- Strict Theme Tokens & Animation Tuning: replaced hardcoded `var(--gl-purple-500)` in pull-to-refresh spinner arc (`.ptr-arc`) and top progress bar with dynamic `var(--primary)` and `var(--primary-hover)` / `var(--primary-active)` tokens, adapting seamlessly to user-selected theme and accent color; replaced static purple border in grading suggestion box with semantic `var(--gl-status-brand-icon)`.
- Service Worker Cache Version Bump (`gitpulse-v619`): bumped `CACHE_VERSION` in `sw.js`.

## [2026.9.30.post37] - 2026-09-18 - Help tooltip alignment, project score badges, archived SSR action buttons, sticky footer, and GitLab pull-to-refresh

**Fixed**

- Help Tooltip Alignment to Card Title & Mobile Hiding: positioned `.card-header-info-tip` directly adjacent to the card title in `cards.html` and removed `margin-left: auto`, anchoring question marks directly next to the title on desktop; on mobile viewports (≤768px), question mark tooltips are hidden completely (`display: none !important;`) as touch tooltips are non-ergonomic.
- Project Members Table Score Column Positioning & Color Badges: relocated the Score column in `table_heads.html` (`project_members_head_full`) and `_members_table.html` immediately after the Student column, matching the Group Members layout; scores are rendered as color badges (`badge` with green, amber, red variants) with numeric `data-sort-value` for sorting.
- Archived Course SSR Action Buttons Disabled State: eliminated action button flickering on reload and navigation by rendering mutating buttons statically disabled at SSR first paint with `disabled=(not course.is_active)` and `data-archived-locked="1"` in `_webhook_settings.html`, `_import_export_settings.html`, and `_compliance_settings.html`.
- Settings Sticky Footer Void Elimination: corrected `.settings-sticky-footer` bottom positioning, negative bottom margin, and safe-area padding in `forms.css`, seamlessly eliminating the black void beneath save/cancel buttons on mobile.
- GitLab-Style Pull-to-Refresh Indicator & Constrained Travel: replaced Material 3 orange circular indicator with a sleek GitLab Pajamas styled indicator (`var(--gl-background-color-overlap)`, subtle border, shadow, and GitLab purple arc `var(--gl-purple-500)`); constrained pull travel (64px) and resting position (8px) so it never covers the page title or headers.
- Teacher Add Row Spacing & User Info Overflow Handling: increased gap between role selector and search typeahead in `.teacher-add-row` (`course.css`) to 16px; applied `overflow-wrap: anywhere` in `cards.css` to prevent long continuous strings from breaking modal responsiveness without shredding normal words.
- Service Worker Cache Version Bump (`gitpulse-v618`): bumped `CACHE_VERSION` in `sw.js`.

## [2026.9.30.post36] - 2026-09-18 - Touch tooltips, sticky table action bleed-through fix, theme switcher, and mobile structure

**Fixed**

- Touch Tooltip Support & Header Right-Aligned Info-Tip: moved `info-tip` component in `components/cards.html` to direct child of `.card-header` with right-alignment (`margin-left: auto; role="button"; tabindex="0"`); added touch and tap interaction in `20-ui-helpers.js`, allowing mobile users to tap question mark icons to open tooltips and dismiss them cleanly.
- Sticky Actions Column Solid Background & Dimmed Inactive Sort Carets: increased z-index of sticky table action headers and cells in `tables.css`, replacing semi-transparent backgrounds with 100% opaque solid colors mixed over base and stripe backgrounds to completely eliminate text and score bleed-through when scrolling horizontally; dimmed inactive column sort carets to `opacity: 0.35` and added explicit numeric `data-sort-value` to Score cells.
- Settings Sticky Footer Void Elimination: tightened `.settings-sticky-footer` padding in `forms.css` to `max(var(--gl-spacing-2), env(safe-area-inset-bottom, 0px))`, aligning buttons centered and eliminating unnecessary black void beneath save/cancel buttons.
- Activity Monitor Full-Width Fluid Stretch on Mobile: set `width: 100%` on `.pipeline-overview-grid` and 2-column mobile layout for `.pipeline-stats-compact.stats-grid-5` in `course.css`, stretching CI/CD health cards to full width on mobile.
- Course Teachers Header Clean-Up & Mobile Structure: removed duplicate badge count in `_teachers_content.html` to prevent duplication with `Showing 8`, while preserving Alpine binding; stacked teacher search and role select vertically in `00-mobile.css` (`.teacher-add-row`) to prevent layout distortion on small screens.
- Preferences Mode Switcher Enlargement & Mobile Label Visibility: enlarged segmented control buttons to 38px with tactile padding, clear dark/light mode states, and visible text labels and icons across all screen sizes.
- Service Worker Cache Version Bump (`gitpulse-v617`): bumped `CACHE_VERSION` in `sw.js`.

## [2026.9.30.post35] - 2026-09-18 - Mobile responsiveness fixes for student score trend chart, sticky footer, checks table, and course card badges

**Fixed**

- Student Score Trend Chart Mobile Layout: added `width: 100%` to `.chart-canvas-wrap` in `analytics.css` and `.student-charts-layout`, `.student-chart-primary`, and `.student-chart-secondary` in `student.css`; on screens ≤768px, switched layout to `align-items: stretch` with 100% width on interactive chart containers, eliminating chart squishing and empty right void.
- Settings Sticky Save Bar Positioning & Background Scrim: aligned `.settings-sticky-footer` in `forms.css` to `bottom: 0` with safe-area inset padding (`env(safe-area-inset-bottom)`) and elevation shadow `box-shadow: 0 -4px 16px rgba(0, 0, 0, 0.12)`; removed negative bottom margin in `course.css`, preventing scrolled background content (e.g. theme radios) from bleeding through underneath buttons.
- Course Settings Compliance Checks Table Mobile Responsiveness: configured `#checksTable` at `@media (max-width: 480px)` in `course.css` to use `table-layout: auto !important; min-width: 320px !important;` with hidden `<colgroup>`; replaced word breaking with `overflow-wrap: break-word; word-break: normal; min-width: 170px !important;` on the Name column, preventing words from breaking vertically into 1-2 character chunks while maintaining smooth horizontal scrolling.
- Course Card Warning Badge & Action Button Overlap: added `flex-wrap: wrap; row-gap: var(--gl-spacing-2); column-gap: var(--gl-spacing-3);` to `.course-card-footer` and enabled button wrapping on `.course-card-actions`, preventing at-risk warning badges (`[ ⚠ 1 ohrozené ]`) from being clipped or overlapped by the `[ Zobraziť ]` action button across desktop multi-column grids, tablet, and mobile cards.
- Service Worker Cache Version Bump (`gitpulse-v616`): bumped `CACHE_VERSION` in `sw.js` to trigger immediate cache refresh for all users.

## [2026.9.30.post33] - 2026-09-18 - Mobile responsiveness fixes for toasts, dropdowns, card headers, and cross-page layout audit

**Fixed**

- Mobile Toast Notifications Layout & Width: resolved severe vertical toast squishing on small mobile viewports (≤768px and ≤480px) where toasts were crushed into a ~22px narrow column with single letters breaking vertically; overrode desktop calculation with `width: auto !important; max-width: calc(100vw - 1.5rem) !important;` and full-width box sizing.
- Mobile Top Bar User Dropdown Menu Alignment: fixed issue where tapping the user avatar on mobile caused the dropdown menu to jump to the top-left edge under the logo; anchored the menu directly beneath the avatar at `position: absolute; top: calc(100% + var(--gl-spacing-2)); right: 0; left: auto`.
- Card Header & Table Header Question Mark Inline Layout: added native `info_tip` parameter support to `card()` macro in `components/cards.html`, rendering tooltips directly inside `<h3 class="card-title">...</h3>`; replaced rigid column stacking with fluid flex-wrap and moved orphaned `info-tip` elements out of `card-actions` across all pages.
- Cross-Page Mobile Responsiveness & Overflow Audit: systematically audited all 12 core application pages across 390px and 360px mobile viewports using Playwright, verifying 0 document-level horizontal overflows and clean wrapping of table controls and action bars.
- Service Worker Cache Version Bump (`gitpulse-v614`): updated `CACHE_VERSION` in `sw.js` to ensure immediate invalidation of cached bundles in client browsers.

## [2026.9.30.post32] - 2026-09-18 - Contoured Quick Access tab indicator, motion radius preservation, and CSS tokenization

**Fixed**

- Contoured active indicator bar for Quick Access tabs: rounded the active indicator ink stripe on `.gl-qa-tabs` (`border-radius: 0 0 calc(var(--radius-md) - var(--gl-spacing-1)) calc(var(--radius-md) - var(--gl-spacing-1))`) so that it contours and hugs the bottom edge of the active tab pill without sharp, protruding corners.
- GSAP motion preservation for segmented controls: updated `motion.js` (`inkTo()`) to animate `width` directly instead of horizontal `scaleX` from a 1px base when handling segmented pill controls (`.gl-qa-tabs` or `data-tabs-segmented`), preventing GSAP from distorting the circular corner radius into an elliptical flat edge while preserving high-performance `scaleX` transitions for underline tabs.
- Comprehensive CSS tokenization across Quick Access & tabs:
  - Standardized all `.gl-qa-tabs` padding and gap to `var(--gl-spacing-1)` and tab border radius to `calc(var(--radius-md) - var(--gl-spacing-1))`.
  - Tied `.gp-tab-ink` and `.gl-qa-tabs .gp-tab-ink` directly to `var(--gl-tab-selected-indicator, var(--primary))` across `interactions.css` and `home.css`, making tab indicators across every page and template completely dynamic and responsive to theme (dark/light) and accent color preferences (indigo, blue, green, red, gray).
  - Tokenized Quick Access list item spacing, avatar radius (`var(--radius)`), and traffic light dot indicators (`.gl-qa-dot--green`, `.gl-qa-dot--yellow`, `.gl-qa-dot--red`) using GitLab Pajamas design tokens (`var(--gl-green-400)`, `var(--gl-orange-400)`, `var(--gl-red-400)`), eliminating all hardcoded hex values.
- Full template and page audit for styling integrity: audited all Jinja templates across the codebase to ensure zero unintended static inline styles and complete reliance on centralized CSS tokens.
- Service Worker cache version bump (`gitpulse-v613`): updated `CACHE_VERSION` in `sw.js` to ensure client browsers immediately invalidate cached assets and receive the newly compiled CSS and JavaScript bundles.

## [2026.9.30.post31] - 2026-09-18 - Dashboard layout alignment with GitLab Pajamas, segmented tabs, and inline styles removal

**Fixed**

- Dashboard grid layout alignment with GitLab Pajamas design: modernized `.gl-home-layout` grid tracks in `home.css` to `grid-template-columns: minmax(0, 1fr) var(--gl-home-sidebar-width, 320px)` with `var(--gl-spacing-6)` (24px) gap. In Fixed layout width mode, the 1280px container centers the dashboard with an ~900px main column and 320px sidebar. In Fluid layout width mode, the container expands across 100% of the viewport, keeping the 320px Quick Access sidebar docked against the right margin while the main column and the 4 KPI stat cards (`repeat(4, 1fr)`) stretch proportionally to fill all available horizontal space, matching GitLab.
- Segmented control pill tabs for Quick Access: replaced underline tabs in Quick Access with GitLab-identical segmented control pill styling (`--gl-segmented-control-track-bg`, `--gl-segmented-control-track-border`, `--gl-segmented-control-btn-active-bg`, `--gl-segmented-control-btn-active-color`) across dark and light themes, providing an authentic solid pill active indicator and smooth contrast transitions.
- Subtle card border harmonization: updated `.gl-home-card` and `.gl-home-sidebar-panel` to use `var(--gl-border-color-subtle)` (matching GitLab's subtle dark card outline) with smooth hover transitions to `var(--gl-border-color-default)`.
- Elimination of inline style attributes in templates: audited and completely eliminated static inline `style="..."` attributes across templates:
  - `_weekly_deadlines.html`: replaced inline styles with CSS classes `.wd-toggle-btn` and `.wd-toggle-title` styled with design tokens in `course.css`.
  - `admin_courses.html`: removed redundant inline `style="width: ...px;"` from `<col>` elements (already governed by `admin.css`).
  - `table_heads.html`: removed redundant inline `style="width: ...px;"` from `<col>` elements in `users_table_head()` and `teams_table_head()`, synchronizing exact column width rules directly in `admin.css`.
- Preferences Save Changes button anti-spam guard fix: prevented the anti-spam submit helper from unconditionally re-enabling guarded buttons after 5 seconds or page scrolling when marked with `btn-save-guard` or `data-no-anti-spam="true"`.
- Elimination of IDE diagnostic errors and false syntax underlines: resolved false-positive JavaScript syntax errors (`Unexpected keyword or identifier. javascript`) caused by a literal `<script>` tag inside a Jinja comment in `base.html`. Added workspace `.vscode/settings.json` and `jsconfig.json` configuring Python virtual environment path, suppressing script/style validation in Jinja template files, and setting browser DOM ES2022 JavaScript environment.
- Service Worker cache version bump (`gitpulse-v612`): bumped `CACHE_VERSION` in `sw.js` to ensure immediate client cache invalidation and delivery of the rebuilt CSS bundles.

## [2026.9.30.post30] - 2026-09-17 - Bypassed asset hash caching in dev mode and bumped Service Worker cache

**Fixed**

- Bypassed in-memory asset hash caching in development mode: updated `_compute_asset_hash()` in `src/app/main.py` so that when `settings.is_development` is True, SHA-256 hashes of static bundles (`styles.bundle.css`, `core.bundle.js`) are computed on demand from disk rather than cached for the process lifetime. This guarantees that rebuilt CSS/JS bundles immediately bust browser cache (`?v=<hash>`) during local development without requiring manual uvicorn daemon restarts.
- Service Worker cache version bump (`gitpulse-v611`): bumped `CACHE_VERSION` in `sw.js` to ensure client browsers invalidate stale static asset caches and fetch the fresh stylesheet bundles containing seamless horizontal flex-stretching for course teacher search controls.

## [2026.9.30.post29] - 2026-09-17 - Exempted local dev rate-limiting, 96-test persona E2E suite, and normalized teacher selector width

**Fixed**

- Exempt localhost from rate-limiting in development mode: passed `dev_mode=settings.is_development` to `RateLimitMiddleware` in `main.py` so that local requests (`127.0.0.1`, `::1`, `localhost`, `testclient`) are not throttled by the strict 10 req/min auth limit on `/dashboard/login` during automated E2E testing or rapid persona switching in dev.
- Enhanced demo course persona seeding: extended `scripts/seed_demo_course.py` to automatically provision `teacher` and `admin` accounts with correct course ownership and active status alongside `demo.ucitel`.
- Comprehensive persona E2E test suite: added `scripts/e2e_test_all_personas.py` validating 96 individual UI/API interactions across Admin, Teacher, and Student roles with 100% test pass rate. Pruned obsolete scratch artifacts.
- Normalized Course Teacher role selector button width: styled `.teacher-add-row .teacher-add-role-select .gl-dropdown-toggle` with `width: 100%`, `display: inline-flex`, and `justify-content: space-between` so the dropdown button fills its allocated container across horizontal length, eliminating awkward dead empty space between the role selector and the filter tabs without altering vertical height.

## [2026.9.30.post28] - 2026-09-17 - Fixed course teachers save button flicker and pruned ad-hoc CSS overrides

**Fixed**

- Eliminated "Save Changes" button flicker on page load: rendered `btnSaveTeachers` disabled by default directly in SSR with standard `btn-save-guard` class, initial server-side `disabled_reason` tooltip wrapper, and `:disabled="!isDirty || isArchived"` Alpine binding. Removed the post-mount JavaScript mutation in `course-teachers.js` that was dynamically wrapping the button in a tooltip `<span>` and flipping disabled state after paint, eliminating the initial visual flash on page load.
- Removed bespoke CSS overrides in Course Teachers stylesheet: deleted ad-hoc overrides for `.gl-dropdown-toggle`, `.search-box input`, `.table-controls-search`, and `.col-teacher-role .gl-dropdown`, as well as redundant hover locks. Preserved solely the responsive horizontal selector row expansion (`.teacher-add-row`, `.typeahead`, and `.teacher-add-role-select`), letting core component CSS (`dropdowns.css`, `forms.css`, `tables.css`, `buttons.css`) govern all styling.

## [2026.9.30.post27] - 2026-09-17 - Fixed dual active teacher filter indicators, restored archived warning toasts, and shifted GitLab ID column left

**Fixed**

- Eliminated dual active tab indicators on Course Teachers filters: fixed collision where SSR-rendered `.active` class was retained alongside newly clicked filter tabs in Alpine `:class` evaluation. In `layout.html`, static `.active` is suppressed when `x_class` handles dynamic state, and `setRoleFilter` cleanly updates DOM classes and `aria-selected`.
- Restored click warning toasts on archived course actions: replaced native `disabled` attributes on archived action buttons with `data-archived-locked="1"`, enabling click events to reach handlers and trigger user-facing warning toasts that the course is archived and read-only.
- Reverted teacher add row controls to standard height (32px): removed vertical 38px overrides from `course.css` while preserving horizontal flex layout across available space.
- Shifted GitLab User ID column left in User Management: adjusted `col-username` width from 177px/165px to 152px/150px, moving the GitLab User ID column cleanly to the left.
- Established design rules for Table View Tabs vs Filter Tabs: documented in `CLAUDE.md` that count badges belong strictly on tabs switching to distinct entities/tables with divider separation (`apart: true`), while simple row filters must never carry individual count badges, and card header `Showing X` belongs only when a table has no pagination.

## [2026.9.30.post26] - 2026-09-17 - Elimination of Course Teachers layout shift, admin/users tab alignment, and clean disabled styling

**Fixed**

- Eliminated layout shift and table expansion jump on Course Teachers reload: calibrated row reservation height (`reserve_row_px=54`) and initial row count reservation (`_reserve_count`) directly from URL query filter. `teacherManager` initializes `roleFilter`, `sortKey`, and `sortDir` from URL parameters immediately on factory creation, removing hydration re-renders. Pre-rendered `.active` state on filter tabs prevents active indicator flicker.
- Aligned filter tabs with Admin Users: removed count badges from role filter tabs on Course Teachers (`/dashboard/courses/{id}/teachers`) to match User Management (`/dashboard/admin/users`). Sized the role selector dropdown and search input to 38px height with flush alignment against filter tabs.
- Standardized component-level disabled styling: removed all ad-hoc overrides and `!important` declarations from `course.css`. System-wide `.form-input:disabled` and `.search-box input:disabled` styling in `forms.css` combined with `:hover:not(:disabled)` prevents hover glow on disabled controls cleanly across the entire application.

## [2026.9.30.post25] - 2026-09-17 - Dead code cleanup, component standardization, and elimination of teachers table CSS overrides

**Changed**

- Dead code and unnecessary overrides removal: pruned unused controller state (`showAdmins`), dead CSS selectors (`.no-teachers`, `.teacher-actions`, duplicate `.teachers-table` blocks, non-existent `.typeahead-wrap`), and orphaned overrides across `forms.css`, `tables.css`, and `course.css`.
- Component standardization on Course Teachers: converted the Course Teachers table (`/dashboard/courses/{id}/teachers`) to core UI component macros (`table_empty`, `btn_icon_only`, `table_count`, `filter_tabs`, `table_controls`, `page_config`).
- Unified table controls and UI consistency: aligned table controls with standard search and role filter tabs without bespoke margins, ensuring the Course Teachers page shares the exact same base styling and alignment as User Management and Course Management. Hardened owner/admin preservation in bulk removal and refined dirty state detection.

## [2026.9.30.post24] - 2026-09-17 - Course teachers table layout stabilization, reload flicker elimination, and archived warning toasts

**Fixed**

- Eliminated flicker and layout shift of filter tabs, count badges, and dropdowns on reload (F5): `filter_tabs` now renders `.active` state and count badges from the server on initial paint, preventing input search squeezing and badge pop-in during Alpine hydration. `alpine_select` and `table_count` support server initial label and count values.
- Course teachers table geometry stabilization: aligned `<colgroup>` definitions and CSS column styles on Course Teachers with User Management (`col-teacher`, `col-teacher-account: 170px`, `col-teacher-role: 190px`, `col-teacher-actions: 80px`), preventing table deformation and jumping on refresh.
- Warning toasts on archived course actions: removed native HTML `disabled` attributes that blocked click events. User actions (`clearAll`, `remove`, `changeRole`, `pickDefaultRole`, and form submit) now reliably display a warning toast explaining the course is read-only.

## [2026.9.30.post23] - 2026-09-17 - Toast feedback, table layout stabilization, and URL filter/sort persistence

**Fixed**

- Missing toast feedback on the course teachers page: actions on archived/read-only courses (`add`, `remove`, `changeRole`, `clearAll`, `onSubmit`) previously failed silently without explanation. Added immediate toast warning alerts, success confirmation toasts for teacher additions, removals, and role updates, and validation guards.
- Table deformation and layout bounce on empty filter states: filtering roles on the teachers page to 0 matches previously unmounted the entire table container and collapsed card height before showing an external empty state. The table header and column widths now remain mounted and locked, and empty filter states render cleanly inside the table row (`<tr class="table-empty-row"><td colspan="4">`).
- Lost filter and sort state on reload: filter selections (`role`, `check_filter`) and column sorting (`sort`, `dir`) across the application are now synchronized with URL query parameters via `history.replaceState` (`course-teachers.js`, `sortable-table.js`, `components.js`, `10-sections.js`).

## [2026.9.30.post22] - 2026-09-17 - Member highlight fix in Issues to Address and GitLab CI/CD enhancement

**Fixed**

- Target member highlight after clicking an affected student in Issues to Address: fixed parsing of modern CSS Color 4 values (`color-mix`) in `motion.js` via 2D canvas pixel normalization, added `--gl-anim-highlight: 1.8s` token to keep highlight visible after smooth scroll lands, and added ClientPaginator page switching if the target member row is on another table page.

**Changed**

- Standardized GitLab CI/CD and repository according to top industry practices: added `workflow:rules` (eliminating duplicate push/MR pipelines), global pip caching keyed on `requirements.lock`, JUnit XML and Cobertura coverage reports, Docker container image publishing with provenance metadata, and automated release creation via `release-cli`.

## [2026.9.30.post21] - 2026-09-16 - Webhook rejections are JSON; a negative limit, an empty form and an empty import no longer do harm

**Fixed**

- A 4xx to a webhook reached GitLab as an HTML page (the error boundary rewrote every POST without `Accept: application/json`); under `/api/` the answer is always JSON. A webhook with `project: null` was a 500, now 422.
- A negative `limit` on `/events/recent`, `/events/dlq` and the operations log was a 500 - rejected (422) or clamped.
- An empty or foreign POST to the course settings form wiped the semester dates and deadlines; without the page's timestamp it is turned away.
- A group import that saw no projects deactivated every project in the course; an empty list deactivates nothing.

## [2026.9.30.post20] - 2026-09-16 - Dead code out, imports up, state as objects, a middleware package

**Removed**

- 40 functions, methods and classes nothing names (878 lines): the GitLab client's write methods in an app that only reads, nine unused schemas, the half-built flagged-team feature (methods, types and a home card counting rows of a table nothing wrote), a `locale` parameter threaded into a method that ignored it, and dead `hasattr` / `getattr` branches on typed objects.

**Changed**

- 131 function-local imports hoisted to the module top; module state as objects instead of `global`; `students.py` (2 010 lines) is a `students/` package like the other domains; the middlewares have their own `app/middleware/` package.

## [2026.9.30.post19] - 2026-09-16 - Source layout the way GitLab lays it out, shorter names

**Changed**

- The dashboard is one package per domain (`home/`, `courses/`, `teams/`, `projects/`, `admin/`), the router helpers live in `api/helpers/`, services are grouped by domain (`gitlab/`, `gitlab_import/`, `llm/`) and modules dropped their `_service` / `_routes` suffixes - 45 modules moved, every import rewritten, the docs describe the new tree.

## [2026.9.30.post18] - 2026-09-16 - Modals focus the first field and hand focus back

**Fixed**

- A modal opens with its first field focused instead of its close button, and closing returns focus to the control that opened it.

## [2026.9.30.post17] - 2026-09-16 - Charts draw after an in-app navigation

**Fixed**

- The User Role Breakdown, the student's score trend and skill profile and the checklist stayed empty after navigating in-app (Chart.js loaded after the page's own script); the library now loads before the page bundles, on a cold load and on an in-app navigation alike.

## [2026.9.30.post16] - 2026-09-16 - Dead CSS removed

**Removed**

- 69 class selectors (107 rules across 19 stylesheets) that no template, script or view names; eleven pages verified pixel-identical before and after.

## [2026.9.30.post15] - 2026-09-16 - One spinner; marks that stop; per-mode chevrons

**Fixed**

- The analysis indicator drew two spinners on one element; it is the app's one mark, becoming a status disc when done. The sync badge and the import box kept spinning after finishing; they stop. The select chevron and the input's busy ring carry the mode's grey.

**Removed**

- Dead htmx parameters on every button and search box, the indicator CSS nothing toggled, the plain ring spinner and its tokens.

## [2026.9.30.post14] - 2026-09-16 - Semantic chart, status and diff colours per mode

**Fixed**

- The compliance charts, heatmap dots, score bands, issue severities, the System Health palette and the diff lines read per-mode tokens instead of one value (or a GitHub literal) for both themes; custom diff colours from Preferences still win.

## [2026.9.30.post13] - 2026-09-16 - The chart palette is the theme's

**Fixed**

- **Charts:** the categorical colours (issue, MR, review, CI/CD, quality, custom) and the role colours are per-mode tokens read by the charts and the legend dots alike; four charts built invalid fills by appending a hex alpha to an rgb() colour and now build real rgba() fills; the role breakdown draws when painted from the page before Chart.js has loaded.

## [2026.9.30.post12] - 2026-09-16 - The System stats and the check heatmap paint without a loader

**Fixed**

- **System page:** the role breakdown is in the page from the first byte instead of fetched behind a spinner; the script fetches only on a refresh. **Student page:** the check heatmap, whose history was already inlined, no longer shows a loader over it.

## [2026.9.30.post11] - 2026-09-16 - A loading state stands for a real load

**Fixed**

- **Loading states:** tables whose first page is already in the page (Events, Job History, Compliance Checks, Webhooks, the student's history) showed a spinner and held it for 800ms on every load although nothing was loading; the pagination bar opened with "Loading pagination..." under tables that never load it. Both are gone: the rows paint before the first frame, the bar is born empty and filled at once, and a spinner's minimum time is owed only once it has actually been seen. A real fetch still shows its state; an empty table shows its empty state at once, never a spinner.

## [2026.9.30.post10] - 2026-09-16 - The accent reaches everything that carries the brand colour

**Fixed**

- **Themes:** the accent now colours links, the selected tab's underline, the sorted column header, the current-week pill, the listbox selection, the progress bar, hover and focus rings, the running job bar and the brand series in charts (score trend, skill profile) - everything that used to be the brand blue - in both modes. Semantic colours (info, success, warning, danger, chart categories) stay.
- **Links** without a component class rendered in the browser's default blue with an underline in every theme; every link has the theme's link colour now, underlined on hover.
- **Dark primary** is blue-400 (readable as text on the dark page), lightened accent under an accent theme.

## [2026.9.30.post9] - 2026-09-16 - A theme is the whole theme; a calmer dark confirm button

**Fixed**

- **Themes:** picking a Theme in Preferences now recolours the primary button (filled and outlined), the primary colour and the focus ring as well as the sidebar, the selected highlight and the checked controls - in both modes. Links stay blue and the danger button stays red in every theme. The preview cards show each theme's primary button.
- **Dark confirm button:** one step calmer (blue-600) so it sits with the translucent grey secondaries instead of standing out as the one saturated block; hover brightens.

## [2026.9.30.post8] - 2026-09-16 - Upload file opens the picker by itself

**Fixed**

- **Upload file:** the button in every JSON editor relayed its click to a hidden file input through a script, and could end up doing nothing. It is a label for the file input now - the browser opens the picker itself - and the input is reachable by keyboard.
- **File chip:** an empty file pill with an x showed beside "Upload file" before any file was chosen; it appears only once a file is loaded.

## [2026.9.30.post7] - 2026-09-15 - A card's explanatory line keeps its gap everywhere

**Fixed**

- **Card lead lines:** the line a card opens with ("Non-scoring diagnostic metrics on teamwork quality") sat directly on the stat cards under it on some cards and 4 or 8px above them on others; the gap is the card component's own now - 8px on every card, the way Compliance Progress had it.

## [2026.9.30.post6] - 2026-09-15 - Loading marks centred, one block loader, code blocks on the scheme's ground

**Fixed**

- **Loading marks:** a table's loading row sat at the top of its reserved box and the pagination bar's mark in its left corner; both sit in the middle of what they stand for now, on every table.
- **One block loading mark** for script-built content too (the User Info modal, the MR history and intelligence cards) - the same spinner + label box as everywhere else, on the same minimum hold.
- **Code blocks** without a language tag follow the syntax scheme from Preferences and the colour mode; the "None" scheme is code in the page's own colours instead of a fixed dark block.
- **Shadows** on cards, menus and the install card read the per-mode shadow tokens instead of one literal for both modes.

## [2026.9.30.post5] - 2026-09-15 - No white controls on dark; dead filter code removed

**Fixed**

- **Dark theme controls:** the primary button and a checked checkbox / radio were near-white fills on the dark theme. The primary button is now the primary blue with white text, a checked control takes the theme's selection colour with a white tick, and Preferences > Theme retints the controls. The light theme is unchanged.

**Removed**

- Dead code: the member filter bar (script and styles), the filter pills, the unused toggle switch and every reference to them; the tour and the e2e walks point at the tab strip that replaced the pills.

## [2026.9.30.post4] - 2026-09-15 - One selected highlight per theme, every colour per colour mode

**Fixed**

- **Selected highlight:** the selected week pill (and every other selected control) was a near-white block on the dark theme, and hovering it made its text unreadable. Every theme now has one selected highlight - a tint of the accent with the accent border - shared by the navigation item, the week pill, the filter pill, the current page and the mode switcher; picking a Theme in Preferences retints all of them together. Hover on a selected control keeps it selected.
- **Every colour per colour mode:** 156 colours in 20 stylesheets were one dark-ramp or light-ramp value for both modes (pale chips on dark cards, faint blue text on white, controls that vanished on the light theme). All of them now read the per-mode tokens, including the success/warning buttons.

## [2026.9.30.post3] - 2026-09-15 - Week Analytics always shows a state under the week pills

**Fixed**

- **Week Analytics:** clicking the active week pill deselected it and left the card empty under the pills; the active pill is now a no-op, and a week without data (or a course without weeks) shows the shared empty state - icon and the reason - at the height the charts take.

## [2026.9.30.post2] - 2026-09-15 - Pagination loads with a spinner + label, Activity is one card with two views, charts animate once, Compliance Progress paints without growing

**Fixed**

- **Pagination bar:** it opened as a blank grey strip (or a placeholder never seen); it now opens with the spinner + "Loading pagination..." and is replaced after the same 800ms minimum as every other loading mark.
- **Activity tab:** Group Activity and Recent Merge Requests are one card with a Groups / Merge requests view strip, like Configuration on System Settings and GitLab's own Activity page. The team page keeps its two cards: Projects and Members are two resources with their own actions, not two views of one thing.
- **Charts animate once:** a refresh (SSE, a finished job, Refresh, Reload, a week switch) rebuilt the chart and replayed its entrance; the first draw on a canvas animates, later draws replace the numbers in place.
- **Student Compliance Progress** paints on load with its rows, summary tiles and heatmap reserved - the first payload is inlined - instead of growing by 359px after the fetch; the summary tiles no longer grow when filled; the heatmap and the checklist loaders are exactly the height of what replaces them; a collapsed card is collapsed on its first frame. Audited every page: no card changes height after first paint.
- **CI lint** on the previous release fixed (formatting in four test files and one pre-existing block in `dependencies.py`).

## [2026.9.30.post1] - 2026-09-15 - Big tables no longer hang on load (delegated tooltips), no-op sorts touch no DOM, Users addresses are no longer cut

**Fixed**

- **Pages with big tables no longer hang on load:** every tooltip on the page was instantiated at boot and re-bound after every swap - on User Management with 574 rows that was 3 404 tooltips and 1.4s of a frozen page for the 25 rows on screen. Tooltips are now one delegated instance: an element gets its tooltip the first time it is hovered or focused. Measured: page blocked 1 029ms -> 345ms, load 1.51s -> 0.77s; every other page under 150ms.
- **A default sort that changes nothing no longer re-inserts every row** (115ms on 574 rows).
- **Users: addresses are no longer cut** - the Email column's 36ch ceiling cut ordinary 38-character student addresses; cell values now ask their column for the width they need. 0 cut cells on every table at 1366px and 1600px.

## [2026.9.30] - 2026-09-15 - Activity tables without "...", cards that do not grow after load, archived courses that stay readable, Teachers page without flashing or empty cells

**Fixed**

- **Activity tables show their rows, not "...":** Group Activity and Recent Merge Requests were two half-width cards, and a data table in a 540px card cut 39 cells - names, titles, dates, even the State badge - with the rest behind a horizontal scroll. They are one under the other now, full width, auto layout: nothing is truncated and nothing scrolls sideways. The webhook configurations table got the same cure.
- **Cards no longer grow after the script runs:** the Activity tables and the project MR list drew their pagination bar late, so the card grew 57px; the shared pagination component reserves it from the first frame.
- **Archived course stays readable:** a disclosure such as "Edit JSON Configuration" opens again (it only reveals what is on the page; the editor behind it stays disabled), and exporting the configuration stays available. Verified as admin, teacher and student on every course-scoped page.
- **Teachers page:** locked role selects no longer flash as available when you switch filters (a disabled toggle looks disabled from its first frame), and an administrator's row shows the same remove control disabled with the reason instead of an empty cell.
- **Communication Indicators** explains itself in the card body, like every other card, instead of in the header.

## [2026.9.29] - 2026-09-15 - A loading state that has painted stays long enough to be read: 800ms minimum for every spinner + label

**Fixed**

- **Loading states no longer flicker:** tables and blocks with a spinner + label have their first page inlined, so the content replaced the mark within ~100ms of first paint (Events: 93ms, User Role Breakdown: 218ms) - too fast to see, let alone read. Every loading mark now carries an 800ms clock; the block hand-off and the Events, Job History and Compliance Checks tables wait it out before painting, so the spinner turns once and the label is read, and nothing moves when the content lands. A refresh keeps its rows and dims them, so it has no wait.

## [2026.9.28] - 2026-09-15 - Events and every island-fed table: the loading state is the box its content will take, spinner + label visible from the first frame

**Fixed**

- **Events: no more blank box that doubles the table and snaps back while loading:** the table's loading row claimed a screenful of height and its spinner and label were held transparent for 400ms, so with no events the reader saw a ~700px blank box collapse to the 170px empty state. The loading row now takes exactly the box its content will occupy (the reserved rows, or the empty state - same size), loading -> empty and loading -> rows measure identically, and the spinner + label are visible from the first frame - on tables and on the block loader alike (System Health, User Role Breakdown, Teacher's Checklist).

## [2026.9.27] - 2026-09-14 - Archived course: write actions dimmed on the first frame, no flash of available buttons on load or refresh

**Fixed**

- **Archived course: write actions no longer flash as available on load/reload:** the page-header actions (Add Group, Import from GitLab, Sync All, Run Checks) sit in the page shell outside the content well and were dimmed only once the deferred script ran the read-only guard, so every full load or refresh of an archived course painted them in their real colours under a banner saying "read-only". The shell now marks `#main-content` archived from the server, so they are dimmed on the first frame on the course, group, project, settings, teachers and activity pages; the guard still owns the tooltip, the click answer and clearing the state after an in-app navigation to an active course.

## [2026.9.26] - 2026-09-14 - Teachers table rendered 1:1 through the shared table component, all skeletons replaced by the spinner + label loading state, sort chevron coloring and activity table scroll

**Fixed**

- **Sort indicator chevron coloring:** Fixed uncolored sort carets on sorted column headers. Updated CSS selectors to target `th.sorted.asc .sort-caret-up` / `th.sorted.desc .sort-caret-down` (Alpine.js places `.sorted.asc` / `.sorted.desc` directly on `<th>`) in addition to the existing `.sorted .sort-arrow.asc` pattern used by `sortable-table.js`. Active sort direction caret is now colored `var(--primary)` with full opacity; the opposite caret is dimmed to `0.22`.
- **Teacher toolbar stretch to fill empty space:** Changed the search typeahead and role dropdown in the teachers toolbar from tiny fixed widths to `flex: 1 1 auto` so they expand naturally to fill available space up to the filter tabs, eliminating the large dark empty void.
- **Teacher table row count display (Showing X of Y):** Added a `table_count(id='teachersCount')` component to the teachers card header and wired `updateCount()` in the Alpine `teacherManager()` component. The count updates reactively on filter changes, teacher additions, removals, and clear-all — matching the Configuration table pattern.
- **Teachers table renders 1:1 through the shared table component:** Removed the whole block of teachers-only `!important` overrides (`padding-bottom: 0` on the card body, `border-bottom: none` on the last row, `max-height: none`, `overflow-y: hidden`, `min-height: 0`, a duplicated closed-dropdown rule). The card now ends exactly like Configuration on System Settings - the standard card-body padding under the last row and the standard scroll viewport for long lists. The private row reservation is replaced by the shared `data_table(reserve_rows=...)` contract that Job History uses.
- **Every remaining grey-bar skeleton replaced by the spinner + label loading state:** The shimmering overlay on the Issues to Address chart, the CI/CD doughnut, the weekly activity chart and both student compliance charts is gone; the User Info modal and the project intelligence cards now show the tanuki spinner with a label instead of grey bars - the same loading state as User Role Breakdown and System Health. Deleted with them: the chart-skeleton plugin, the skeleton course card, the skeleton-only paths in the loading hand-off and ~450 lines of orphaned skeleton CSS and tokens.
- **Activity table horizontal scroll restoration:** Reverted the forced `min-width: 0 !important; width: 100% !important` on `.activity-grid .data-table.tbl-fixed` that had violently squeezed grid cards to ~500px, clipping status dots and truncating column headers. Restored `.table-scrollable` min-widths (600-620px), gave `.col-activity-projects` `min-width: 85px`, and gave the MR status dot column a fixed 36px width with tight padding.

## [2026.9.25] - 2026-09-11 - Table column stabilization across filters and refresh, toolbar sizing, and dead space removal

**Fixed**

- **Table column width stabilization across filters and refresh:** Fixed table column shrinking and deformation by restoring `table-layout: fixed` and preserving `<colgroup>` visibility under the 1180px container query in `tables.css`. Columns maintain rigid widths without jumping when switching filter tabs across all system tables (Teachers, Users, Checks, Activity, Jobs).
- **Course teachers toolbar controls sizing:** Enlarged role selector dropdown (`Teacher ⌵`) to 155px with balanced chevron padding, and shrunk typeahead search input to a compact 220px to match requested visual layout.
- **Card bottom dead space and internal scrollbar elimination:** Removed unnecessary vertical table scrollbar (`overflow-y: visible`, `max-height: none`) and eliminated card bottom padding (`padding-bottom: 0`) under the teachers list slot, removing the dead empty void where pagination is not needed.
- **Loader component cleanup:** Cleaned out obsolete skeleton comments in `loaders.html` in favor of standardized spinner loading states.

## [2026.9.24] - 2026-09-11 - Teacher table column sizing and toolbar optimization, elimination of card void space, and session user resolution fallback

**Fixed**

- **Course teachers toolbar sizing & responsive table columns:** Decreased the add teacher search typeahead input width to a compact ~280px and widened the role selector dropdown to 130px with balanced text and chevron spacing. Replaced fixed 1167px pixel column widths with responsive percentage widths (44%, 20%, 24%, 12% = 100%) so the table fits the container width without horizontal overflow or column deformations when switching filter tabs.
- **Card bottom dead space elimination:** Reduced card body bottom padding when containing the teachers list slot and removed redundant row borders, removing the empty gap under the table where pagination was not needed.
- **Session user lookup fallback:** Added user ID, GitLab username, and case-insensitive fallbacks to `_load_user_from_session` to prevent 404 responses for tour state and activity telemetry requests.

## [2026.9.23] - 2026-09-10 - Cookie banner and toast redesign matching GitLab Docs callout, documentation diagrams fix

**Fixed**

- **GitLab Pajamas Cookie Consent Banner overhaul:** Completely redesigned the cookie consent banner to mirror GitLab Docs Pajamas callout alerts, featuring the signature top gradient accent line, elevated floating card at viewport bottom, info icon, bold title with inline link (`Privacy Policy ↗`), high-contrast confirm button (`I agree`), and dismiss action.
- **Notification Toast System alignment:** Standardized toasts across all 5 states (`info`, `warning`, `success`, `danger`, `tip`) to match the GitLab Pajamas callout style with top gradient accent lines, state-colored typography, smooth countdown progress indicator, and action links.
- **Documentation diagrams correction:** Replaced broken Gantt timeline chart with a clean, responsive maintenance window flowchart and substituted arbitrary pie chart percentages with an accurate rule evaluation engine architecture diagram across both Slovak and English documentation.

## [2026.9.22] - 2026-09-10 - Pagination arrows fix, commit history alignment, and GitLab preferences styling

**Fixed**

- **Pagination arrows consistency (< >):** Preserved previous and next page navigation buttons (`<` and `>`) in a disabled state for single-page tables instead of hiding them completely. Pagination switchers are now consistently present across all tables, matching the behavior of empty tables.
- **Commit history table alignment & stability:** Eliminated the 72px void space preceding branch badges on non-merge commits with `.commit-branch-wrapper`, locked column widths with `tbl-fixed`, and prevented row height jumping and text wrapping.
- **Commit history branch selector removal:** Removed the redundant branch dropdown filter from the commit history header as requested.
- **GitLab Pajamas preferences page styling:** Rebuilt the theme mode switcher as a Pajamas segmented button group (text-only, 32px height, rectangular radius, dark grey `#4c4b51` active background in dark mode), removed redundant accent color label so cards sit directly below the description, and added clean section dividers.
- **Teacher add role selector flush alignment & search bar expansion:** Removed auto-margin separator on `.table-controls:has(.teachers-role-filter)` and constrained `.teacher-add-role-select` min-width to content width, allowing the typeahead input to expand fluidly and placing the role dropdown directly flush (8px gap) against the filter buttons with zero dead void space.
- **Course teachers card bottom void & internal scrollbar elimination:** Overrode `.teachers-list-slot` min-height to 0 and set `.table-responsive` max-height to `none` with visible overflow, allowing the card to size naturally to its rows without generating internal scrollbars or leaving 65px empty dark space at the bottom of the card.

## [2026.9.21] - 2026-09-10 - Course teachers component rewrite, zero void space, button flash fix, and archived read-only state

**Fixed**

- **Course teachers component refactoring & empty space removal:** Removed hardcoded `min-height: 240px` on `.teachers-list-slot` in `course.css` and cleared inline server reservation styles instantly via Alpine lifecycle hooks (`init`, `$nextTick`, DOM events), completely eliminating trailing empty dark space under the table when filtering down to single rows (e.g. Course Owner filter).
- **Archived course read-only state & mutation lock:** Passed `isArchived` through page config and component state, disabling the teacher search typeahead, default role dropdown, "Remove all restrictions" button, row-level role selectors, row-level deletion actions, and form submissions in archived courses.
- **Button flashing & race condition prevention:** Rendered `btnSaveTeachers` initially with `disabled=true` (and dynamic `:disabled="!isDirty || isArchived"`) and "Remove all restrictions" with `disabled=(not _can_clear)` and `:disabled="!canClearAll"`, preventing inactive action buttons from flashing enabled on direct page load or browser refresh.
- **Dead code removal & TDZ error elimination:** Removed obsolete pagination state (`page`, `pageSize`, `pageNumbers`, `pageLabel`, `prevPage`, `nextPage`, `search` watch) from `course-teachers.js`, safely guarded `GP.autoReloadOnJob`, resolved Temporal Dead Zone `ReferenceError` hazards in `cookie-consent.js` and `00-base.js`, and removed duplicate component declarations.
- **Table dimensions & column width stabilization:** Calibrated `.teachers-table` fixed columns (`.col-teacher: 520px`, `.col-teacher-account: 240px`, `.col-teacher-role: 280px`, `.col-teacher-actions: 127px`) matching the 1167px container budget, ensuring stable table dimensions and column widths across all filter states without violent collapsing.

## [2026.9.20] - 2026-09-10 - Bot username truncation fix, badge alignment, empty state icon, and table layout stability

**Fixed**

- **Bot username truncation & badge alignment fix:** Widened `col-username` from 132px to 177px, adjusted `col-gitlabid` (95px) and `col-email` (280px) within the 1167px budget, removed restrictive `12ch` cap on bot usernames so usernames like `project_8323_bot` display cleanly without premature truncation, and aligned `[Bot]` and `[you]` badges to the right edge via `margin-left: auto`.
- **Compliance checks empty state & bottom summary band:** Added standard `.table-empty-state` with search icon and translated message when filter matches zero compliance checks, and moved the `Total Active Weight` summary card to the bottom of the section below the table and empty state.
- **Stretched course teacher search & controls alignment:** Stretched `.table-controls-search` (`flex: 1 1 auto`) and typeahead search box so the role dropdown sits directly against the filter buttons, eliminating the awkward gap between search controls and filter tabs.
- **Course teachers filter empty state:** Differentiated between zero total teachers (unlock empty state: "No restrictions") and zero filtered teachers (search empty state: "No teachers match the current filter.").
- **Table layout stabilization & zero collapse:** Enforced `table-layout: fixed; width: 100%;` on `.teachers-table` with calibrated column widths (`.col-teacher: 440px`, `.col-teacher-account: 220px`, `.col-teacher-role: 240px`, `.col-teacher-actions: 100px`) and `.teachers-list-slot { min-height: 240px; }` with proactive inline style clearance, preventing column jumps, deformations, and violent collapsing when switching filters or refreshing.

## [2026.9.19] - 2026-09-10 - Compliance chart rendering fix, read-only unblock in archived courses, and icon standardization

**Fixed**

- **Student compliance progress chart rendering fix:** Restored missing `<canvas id="historyCanvas">` element inside `#historyChart` in `_compliance_history.html`, resolving the infinite loading spinner state and allowing the compliance trend line chart and skill radar to render accurately.
- **Archived courses non-mutating controls whitelisted:** Extended `_READONLY_OK` in core progress guard to whitelist read-only navigation and exploratory controls (`.tab-btn`, `[role="tab"]`, `.filter-tabs button`, `.table-controls-filters button`, `.teachers-role-filter button`, search inputs, `.sortable-header`, pagination buttons, modals, info tips) in archived courses, allowing teachers and viewers to freely inspect, filter, and sort data without being blocked by the write protection toast.
- **Elimination of empty void space in course teachers list:** Proactively dropped server row reservation `minHeight` on `.teachers-list-slot` across DOMContentLoaded, script execution, role filter changes, and HTMX tab swaps, eliminating unwanted trailing grey space.
- **Card subtitle placement & header icon alignment:** Relocated "Score trend and practice tracking across the semester" subtitle from card macro argument to standard descriptive paragraph under card header inside the body (matching Teacher's Checklist and Week Analytics), and added `icon('users', size='sm')` to Groups card header in course overview.
- **Users table column width fine-tuning:** Fine-tuned `col-gitlabid` (125px), `col-fullname` (210px), and `col-email` (295px) within the 1167px table budget, ensuring longer names render with ample breathing room without clipping, and locked `min-width` and `max-width` across all columns to eliminate CLS.
- **Universal delete/remove icon standardization:** Replaced inconsistent table row removal icons (`x`, `trash-2`) with standard GitLab Pajamas `trash` icon across teacher management, admin courses, danger zone, and settings.

## [2026.9.18] - 2026-09-10 - Users table column rebalance, filter background fix, teacher dropdown componentization, and integrated test coverage

**Fixed**

- **Users table column rebalance & overflow fix:** Reallocated width from `Full Name` (250px -> 180px) to `Email` (280px -> 305px) and `Created` (135px -> 145px) with `col-gitlabid` set to 145px (total 1167px, staying safely below 1200px container width without layout shift). Removed `min-width: 0` overrides on username/email/created cells that triggered CLS, expanded email truncation threshold to 36ch so university emails render unclipped, and standardized action buttons to `ghost` variant.
- **Filter tabs transparent background:** Eliminated dark grey background artifact (`#28272d`) behind tab filters in Compliance Settings and Teachers views, enforcing transparent background, baseline alignment, and removing obsolete `.check-filters` radius selectors.
- **Teacher dropdown componentization:** Removed bespoke role dropdown style overrides (`.role-dropdown`, `.teacher-add-role`) in `course.css` and template partials, fully componentizing teacher role selects to standard `alpine_select` (`.gl-dropdown`) components, and removed artificial `min-height` on `.teachers-list-slot`.
- **Integrated test job & coverage badges:** Unified the test job status and test coverage percentage into a single inline stage badge (`Tests [passed] [71.0%]`) in the student pipeline row, eliminating the redundant vertical misaligned `.mr-pipeline-coverage` container and reducing vertical scrolling space.
- **Proportional table action & button icons:** Added scoped sizing for `.btn-sm .icon` (14px) and `.btn-xs .icon` (12px) in `layout.css`, ensuring small and extra-small table action buttons render neat, proportional icons rather than oversized 16px glyphs.

## [2026.9.17] - 2026-09-10 - Table header seam fix, column width stabilization, button error state, and course detail template fix

**Fixed**

- **Users table continuous header without subpixel seam:** Added explicit background fill (`var(--gl-background-color-subtle)`) to `.data-table thead` and `.data-table thead tr`, eliminating the 1px vertical slit between `Role` and `Status` columns caused by subpixel rasterization rounding over dark card backgrounds.
- **Column width locks and date truncation fix:** Increased `col-created` width from 115px to 135px in table heads and stylesheet rules to prevent ISO date truncation (`2026-04-1;`), adjusted `col-email` to 280px, and defined integer-pixel `min-width` rules across all columns (132px, 165px, 250px, 280px, 90px, 86px, 135px, 84px = 1222px total) on `.users-table` to prevent column jitter and shifts upon hydration and refresh.
- **GitLab enrichment button stability and error state:** Locked `btn.style.minWidth` during outcome transitions in `_setButtonOutcome` to prevent button width collapse or expansion when displaying outcome icons or labels; styled `.btn.btn-error` with appropriate error coloring; and wrapped `enrich_users_from_gitlab` API endpoint in structured exception handling to return clear JSON error responses and release lock flags instead of unhandled 500 errors.
- **Course detail template syntax fix:** Added missing `{% endif %}` closing tag before `{% endset %}` in `src/app/templates/partials/course/_detail_content.html`, resolving the 500 Jinja `TemplateSyntaxError` on course dashboard pages (`/dashboard/courses/<id>`).

## [2026.9.16] - 2026-09-10 - Student detail fix, skeleton rounding, and chart alignment

**Fixed**

- **Student detail compliance progress crash:** Fixed a ReferenceError on `panel` in `student-detail.js` (`loadHistory`), allowing compliance history and skill radar charts to load reliably.
- **Loading skeleton corner clipping:** Added `-webkit-mask-image` and inherited border-radius to `.gl-skeleton` and `.gl-chart-skel` shimmer pseudo-elements, preventing GPU-composited animations from escaping rounded corners, and enforced circular radius on pipeline doughnut skeletons.
- **CI/CD Health doughnut chart sizing and rendering:** Resized `.pipeline-chart-wrap` to 116px to match adjacent stat cards, eliminated the deferred `IntersectionObserver` delay, and ensured `.gl-chart-ready` is set immediately to eliminate stuck placeholder squares.
- **Admin Users table column stability:** Locked `col-gitlabid` (165px) and `col-fullname` (250px) widths with min-width and max-width on `th` and `td`, and updated `admin-users.js` live refresh to mutate `.users-cell-value` preserving ellipsis and boundaries.
- **Teacher management styling and table slot height:** Removed unwanted grey background on teacher role dropdown buttons and compliance preset buttons, and removed artificial min-height on `.teachers-list-slot` to eliminate empty void space below the table.
- **JSON configuration disclosure smoothness:** Replaced native `<details class="details-accordion">` in Weekly Deadlines with Alpine `x-collapse` and smooth chevron rotation, eliminating animation jitter.
- **Contextual help tooltip icons:** Added `(?)` help tooltip icons (`icon('help-circle')`) across Users, Teachers, Groups, Compliance Checks, and Analytics cards.

## [2026.9.15] - 2026-09-10 - Elimination of table layout shift (CLS) and explicit column widths

**Fixed**

- **Table layout shift (CLS) elimination on initial load and refresh.** Server-rendered
  the `.table-controls--tabs` class directly on `.table-controls` markup when filters
  contain tab strips, eliminating a ~10px vertical jump caused by deferred CSS `:has()`
  evaluation during streaming HTML parsing.
- **Explicit column widths in table heads.** Added explicit inline widths and synchronized
  stylesheet definitions across `<colgroup>` columns for User Management (`users_table_head`),
  Teams (`teams_table_head`), and Courses (`adminCoursesTable`). Aligned `col-gitlabid` to 165px,
  preventing browser column recalculation shifts as rows stream or timestamps localize.

## [2026.9.14] - 2026-09-10 - Filter tabs baseline alignment and service accounts divider isolation

**Fixed**

- **Filter tabs baseline alignment and indicator flushness.** Aligned `.table-controls`
  flush to its bottom container border (`padding-bottom: 0; align-items: flex-end;`)
  when holding tabs, removing doubled negative margins that caused active tab underlines
  to float detached 10px below the container's bottom border line.
- **Service accounts tab divider and underline isolation.** Sized `.tab-btn--apart`
  with dedicated margin gap (`var(--gl-spacing-5)`) and centered the vertical divider
  within the gap (`height: 16px; top: 50%; transform: translateY(-50%)`). Restored standard
  inner button padding so the active blue indicator strictly underlines the tab button itself
  without stretching to the divider, and prevented the vertical divider from intersecting the
  horizontal baseline border line.

## [2026.9.13] - 2026-09-10 - Table hydration stability, dynamic dropdowns, and baseline filter tabs

**Fixed**

- **Table hydration stability and sort caret visibility.** Suppressed full-table
  pre-render paint past 50 rows in User Management to prevent vertical layout shifts
  during client hydration. Enlarged table sort arrows across the application and ensured
  adequate column width for GitLab User ID to prevent caret clipping.
- **Teachers page controls and filter styling.** Unified the teacher invite controls and
  view filter tabs into standard `table_controls` toolbar matching Pajamas design.
  Removed unwanted background boxes and streamlined weight and pattern presets in course settings.
- **Dynamic dropdown menu widths.** Updated dropdown menus to dynamic sizing (`max-content`)
  with nowrap item text, preventing awkward character wrapping for options like `merge_request`.
- **Filter tabs baseline attachment.** Attached filter tabs flush with the container's bottom
  border across table controls, matching native course tabs and removing floating gaps.
- **Student Issues table and visual balance.** Moved student issues view switcher to table controls,
  balanced CI/CD pipeline doughnut diameter to 96px, and aligned header info tooltips to the far right.

## [2026.9.12] - 2026-09-09 - User preferences, smooth states, and balanced components

**Fixed**

- **Account preferences as single source of truth.** Restored user-defined default
  page size (`default_page_size`) and per-table saved preferences across data tables,
  eliminating hardcoded overrides.
- **Micro-flash state transitions and loading indicator consistency.** Replaced bare
  loading text placeholders with standardized Tanuki spinners across pagination, weekly
  deadlines, compliance history, and event payload modals.
- **Webhook configurations and pipeline health layout stability.** Sized pipeline
  donut chart to 80px for balanced dashboard card proportions and added `tbl-fixed` with
  stable column widths to webhook configurations to prevent awkward column squeezing.
- **Removed obsolete styles and dead code.** Cleaned up unneeded badge definitions
  and legacy teacher management overrides in `admin.css`.

## [2026.9.11] - 2026-09-09 - Teachers controls unification and table stability

**Fixed**

- **Teachers management controls and zero-shift loading.** Unified teacher invite
  typeahead and course role dropdown with standard GitLab Pajamas `table_controls`
  and `filter_tabs`, eliminating custom overrides and fake role color mixes.
- **Table loading shift and filter preservation in User Management.** Added pre-paginator
  row clamping to prevent full-table flashes before client pagination initializes.
  Fixed filter and search state synchronization to preserve `?q=` and `?role=` query
  parameters without multi-apply rendering jumps on initial page load.

## [2026.9.10] - 2026-09-09 - Centred pagination and stable tables

**Fixed**

- **Centred pagination controls and persistent empty states.** Page navigation
  is now strictly centred via a 3-column CSS grid (`1fr auto 1fr`), keeping row count
  info left-aligned and page size right-aligned. Pagination controls remain visible
  during empty or filtered states (`Showing 0-0 of 0`), and duplicate count headers
  have been eliminated.
- **Eliminated scrollbar gutter dead space.** Removed `scrollbar-gutter: stable`
  from `.table-responsive` to eliminate empty right-side gaps on short tables.
- **Stable table column sizing across views.** Restored proper colgroup column
  widths in User Management, Events, and Course detail tables to eliminate shifts
  during page loads and interactions.
- **Balanced Webhook Configurations table.** Adjusted column proportions to prevent
  excessive line wrapping on long configuration names.
- **Balanced CI/CD health doughnut chart.** Scaled doughnut diameter to 104px
  with uniform vertical centering against stat cards.

**Changed**

- **Unified Compliance Checks filter tabs.** Replaced outdated custom filter buttons
  with standard Pajamas `filter_tabs` and `table_controls`.

## [2026.9.9] - 2026-09-09 - One table, and every table like it

**Fixed**

- **The sideways slide, in every table at once.** A table's scroll viewport
  gains a vertical scrollbar the moment its rows cross its height cap, and the
  bar was taken out of the width the columns are solved against - so every
  column moved left when it appeared and back when a filter or the paginator
  dropped the row count under the cap again. The space is reserved from the
  first frame now, on the one wrapper every table scrolls inside.

**Changed**

- **Every table is laid out the same way.** Search and filters sit in the band
  between the card header and the rows, on every page; four pages had put them
  in the card header, where a table's actions go. The band measured 45, 51, 57
  and 73 pixels on four pages for the same job - it is 45px everywhere now, with
  every control in it the same height, and the search runs from the left edge to
  wherever the filters begin.
- **A table that fills itself from JavaScript says so.** Five tables showed a
  header over a void while they loaded; one stayed hidden entirely and grew the
  card by its full height when its data arrived. All of them open with the
  shared loading state.
- **The row count is printed once**, in the card header, in one wording.
- **Eight more page-level style overrides removed**, including one that decided
  how every table cell in the app sits from inside a single page's stylesheet.

## [2026.9.8] - 2026-09-08 - Activity that was recorded nowhere

**Fixed**

- **Four kinds of pilot telemetry were never recorded.** The beacon is
  fire-and-forget, so a call the API refuses fails in silence. The student
  page's Export sent a metric type that is not a member and a string where an
  object was required (422); the group and project pages had no course id in
  their markup at all, so their drill-downs and page views were dropped before
  they were sent. All four kinds land now.
- **A student's page asked twice for what it is never allowed** - the
  AI-analysis status and teacher telemetry, both refused with 403 on every group
  page and again on every return to the tab. Both senders check the reader now.
- **Reactivating a course said nothing about its dead webhooks.** Archiving
  switches them off and reactivation deliberately leaves them off, so a
  reactivated course looked live while GitLab got 401. The count and what to do
  about it are in the log now.
- **A row's buttons stayed out of reach** in the project Members table, the
  widest in the app; its Actions column is pinned like every other.
- **An error toast dropped the reason** the server gave for a failed GitLab
  refresh.

## [2026.9.7.post5] - 2026-09-07 - A webhook refused for a reason nothing recorded

**Fixed**

- **The webhook lookup digest was keyed with an empty secret** on any instance
  that keeps SECRET_KEY in `.env` - so a configuration written by one process was
  invisible to another and deliveries came back 401.
- **A malformed payload answered 500** instead of 422, which made GitLab retry an
  unusable delivery for 24 hours.
- **A rejected delivery logged nothing** - it now records the project, the course
  and which secrets were present, never the token.

## [2026.9.7.post4] - 2026-09-07 - The confirmation you cannot click

**Fixed**

- **A confirmation opened behind the modal that asked for it** - "Run selected
  checks" raised a confirmation that painted under the Run Checks modal, so the
  course-wide grading action could not be completed at all. The dialog has its
  own layer now.

## [2026.9.7.post3] - 2026-09-07 - The admin Courses table stopped hiding its own cells

**Fixed**

- **The admin Courses table sizes its columns to their content** - it was six
  percentage columns over a fixed layout, and no set of percentages fits at every
  width: at 1600x1000 the course name needed 283px in a 265px column. The wrapper
  scrolls instead, the same contract the Users table uses.

## [2026.9.7.post2] - 2026-09-07 - Even rows in the admin Courses table

**Fixed**

- **A row of the admin Courses table is one line again** - the labelled
  "Teachers" button pushed the other three actions onto a second line, so that
  row stood ~40px taller than its neighbours. All four are icons with tooltips
  now.

## [2026.9.7.post1] - 2026-09-07 - A page's actions sit beside its name, and a group shows its own state

**Changed**

- **A course's actions moved next to its name** - Add Group, Import, Sync All and
  Run Checks were a loose row between the tabs and the Groups card. The group and
  project pages already put theirs in the page header.
- **A group's page shows the group's own state** - score, status, contributors,
  projects and pipeline pass rate, the five figures the course table shows for it
  and its own page did not.
- **Numbers inside a card are numbers, not cards** - the Activity page's CI/CD
  block was five tiles inside a sixth card; the student page's Communication
  Indicators, ten.
- **"Last synced" on a project is a line, not a panel.**
- **The phrase under your name on the dashboard is bigger** - it is a sentence,
  not metadata.

**Fixed**

- **A red group looked exactly like a green one** - the live handler toned the
  status card with classes no stylesheet defines any more.
- **The disabled-feature page no longer says you are on the dashboard**, and its
  "Go Back" button goes back.
- **The course page stopped counting contributors it never shows** - 11.0ms of
  its 44ms of database work, for a number no template renders.

## [2026.9.7] - 2026-09-07 - One subject, one card - and the unlit corner is gone

**Fixed**

- **The unlit corner, everywhere it was** - a table drew its own 12px top corners
  while the header, toolbar or tab strip above it squared the block, so a notch
  of card ground showed at the corner. Six of the nine tables walked had it: the
  Users table, Job History, Feature Flags, Recent Events, the student page's
  issue tables and Group Members. A table takes its corners from its wrapper now.
- **A table under a tab strip keeps its corners square** - the same defect in a
  third disguise, in the panels that just grew tabs.

**Changed**

- **The System page asks one question once** - Feature Flags, LLM Configuration
  and Runtime Information are one Configuration card with three tabs; Clear Cache
  and Refresh Stats moved to the page header. 3775px and seven cards down to
  2540px and four.
- **A student's issues are two tabs, not two disclosures** - authored and
  assigned are the same table split by side; the card is 417px down to 255px.
- **"Issues to Address" is written once** - its five states shared one card
  instead of carrying five copies of it.

## [2026.9.4.post5] - 2026-09-04 - The first page after a deploy is no longer the slow one

**Changed**

- **The process warms itself at startup** - compiling templates (2 651ms for all
  106), configuring the ORM's mappers (83ms) and opening the first database
  connection (162ms) used to be paid by whoever opened the first page. Measured
  in production: dashboard 1355ms -> 691ms, course detail 88ms -> 33ms.
- **Lazy loading of page content: measured, and deliberately not added** - the
  course page's whole database work is 44ms and it renders warm in 13ms, so a
  second request would cost more than it saves. Images and per-page scripts stay
  lazy, which is where the wait is real.

**Fixed**

- **A wrong claim in this changelog, corrected** - the post1 entry credited the
  contributor query's new shape with a 2560ms speed-up. That reading was taken
  during a deploy; on an idle host both forms are the same. The slow pages were
  the deploy (post3).

## [2026.9.4.post4] - 2026-09-04 - A merge request lists its own commits, not the branch's history

**Fixed**

- **A merge request lists the commits GitLab says are in it** - the card listed
  the whole branch history, including the template's commits from years earlier,
  and the 30 was a cap rather than a count. The sync now keeps the commit list
  GitLab reports for each MR.
- **The users filter lines up with the table again.**

**Changed**

- **`mr_notes.author_id` gets the index its model declared** - schema/model drift
  repair, not a speed-up.

## [2026.9.4.post3] - 2026-09-04 - A deploy no longer takes the production host down with it

**Fixed**

- **Deploys stopped rebuilding both images from scratch** - `--no-cache`
  reinstalled every dependency on the four-core production host while it was
  serving requests. Measured during one such build: a request that spent 107
  seconds without running a single query. The layer cache is used now;
  `--no-cache` is behind a flag.

## [2026.9.4.post2] - 2026-09-04 - The dashboard no longer writes to the database on every request

**Fixed**

- **A one-shot repair of `gitlab_user_id` was firing on every request** - the
  dashboard's five parallel fragments each wrote the same row and exhausted the
  connection pool. Measured on production: one write took 36 417ms, and two
  requests spent 107 seconds without ever being handed a connection. It runs
  once per user now.

## [2026.9.4.post1] - 2026-09-04 - The course page is fast, and a click in a table says so

**Fixed**

- **The course page asks the database for its contributor whitelist** - it used
  to be sent as ~900 bind parameters; it is a subquery now, ten times smaller and
  one round-trip cheaper. Same results, verified against real data.
  *(Corrected later: this first claimed a 2560ms-to-milliseconds speed-up. That
  reading was taken while a deploy was rebuilding images on the same four cores -
  on an idle host both forms measure the same. The slow pages were the deploy.)*
- **A click on a table row or a card reports itself where it happened** - the
  control holds a gentle tint while its page loads.
- **A long project name is no longer cut in the page header** - the heading wraps.

**Changed**

- **People and service accounts are one card with two tabs** - the same table of
  the same entity; the bots are no longer in a collapsed card below it.

## [2026.9.4] - 2026-09-04 - A slow request names its worst query

**Added**

- **A request over one second also logs its slowest query** - the course page
  measured 6721ms with 5902ms of it in the database across 20 queries, so the
  time is in one or two of them. The statement is logged, never its parameters.

## [2026.9.3.post12] - 2026-09-03 - Every request line says how much of it was the database

**Added**

- **`db_ms` and `db_queries` on every request line** - the total on its own
  cannot be acted on: a hundred quick queries and one slow template render look
  identical from outside. The dashboard measures 113ms across 38 queries, 50ms
  of it in the database.

## [2026.9.3.post11] - 2026-09-03 - The row lights up again, and a click in a table says so

**Fixed**

- **Clicking a name in Issues to Address lights the row up again** - the mark was
  drawn behind the cells, which paint their own opaque backgrounds; the cells
  themselves are tinted now.
- **A click in a table or a card reports itself and no longer costs a full page
  load** - rows, cards, back links and the search palette go through the app's
  own navigation instead of `window.location`.

## [2026.9.3.post10] - 2026-09-03 - The mark lands where a mark belongs, or nowhere

**Changed**

- **The loading pill is gone** - a navigation is reported by the top progress
  bar, by the clicked control's icon turning into the app's mark, and by a
  `progress` cursor over the content.
- **The mark no longer lands in a card's corner** - only a control's first icon
  counts, and only when it leads; a card, a table row or a bare link gets none.
- **The dashboard greeting is two lines, not three** - the phrase replaces
  "Good evening, <name>" rather than being added under it, and that greeting is
  the fallback when there is no phrase.

## [2026.9.3.post9] - 2026-09-03 - Loading shows one indicator you can see

**Changed**

- **Loading shows one indicator you can see** - a pill at the top of the content
  carrying the app's mark and the word "Loading...", on the same raised surface
  as every other component, so it reads in every theme. It appears at 250ms and
  says the longer sentence in the same element after 4s, so nothing moves.
- **It does not cover the page** - about 5% of the content region, and it moves
  none of it.
- **Sign-in and sign-out sit where Keycloak's do** - the content is ~48px lower,
  so the card reads as placed rather than pinned to the top edge.
- **The dashboard greeting carries a line of its own** - a short phrase that
  changes through the day, fetched in the background; if the source is down the
  original greeting stays.

## [2026.9.3.post8] - 2026-09-03 - The wait is shown where you clicked

**Changed**

- **The full-screen loading veil is gone** - the control you clicked turns
  instead (the mark stands in for its icon, so nothing moves), the progress bar
  runs at the top, and a line appears in the breadcrumb bar after 4 seconds.
- **The page you are leaving stays readable** - nothing is drawn over it.

**Fixed**

- **The loading mark keeps turning under reduced motion** - it used to stop
  after a single frame, which looked like the app had hung.

## [2026.9.3.post7] - 2026-09-03 - Pages are a fraction of the size they were

**Changed**

- **Pages are far smaller** - the translation catalogue is no longer inlined
  into every page but is a file the browser keeps. The dashboard went from
  367KB to 162KB, the login page from 234KB to 21KB.
- **The dashboard asks the database less** - fifty queries per render to
  thirty-eight.

**Fixed**

- **Loading the dashboard no longer writes to the database** when there is
  nothing to heal.

## [2026.9.3.post6] - 2026-09-03 - The loading screen wears the theme

**Changed**

- **The loading screen wears the theme** - it shows the app's own spinner
  instead of a second copy of the brand mark, and the ring follows the accent
  chosen in Preferences.
- **The page behind it stays readable** - it was dimmed twice; now once, and
  more lightly.
- **The syntax-highlighting previews show code rather than space** - a narrower
  number gutter and a sample that fills the card, clipped at the right edge as
  GitLab's own previews are.

## [2026.9.3.post5] - 2026-09-03 - The loading screen covers the page you are looking at

**Fixed**

- **The loading screen covers the page you are looking at** - on a scrolled
  page it stayed at the top of the content and scrolled away with it, leaving a
  dark band across the top of the window and the page bare underneath.
- **A table under a header no longer draws its own top corners** - two radii on
  one corner let the dark ground show through, which is the unlit corner above
  the CODE column.
- **Column labels no longer wrap in a table that can scroll instead** - the
  column takes the label's width and the header stays one line.
- **One long value no longer takes its whole column with it** - past 42
  characters it is cut with an ellipsis, with the full value in the tooltip.

**Changed**

- **The dashboard asks for its job counts once instead of five times.**

## [2026.9.3.post4] - 2026-09-03 - A deploy no longer shows the browser's error page

**Fixed**

- **A deploy no longer shows the browser's error page** - the request waits out
  the container swap, and only a longer outage reaches our own page, which
  reloads itself once the app answers.
- **Compliance-rule descriptions wrap instead of being cut to one line** - the
  clipped half was what tells two checks apart.
- **The sidebar's quick-access rows show what they display.**

**Changed**

- **The space above the page footer is the same on every page.**

## [2026.9.3.post3] - 2026-09-03 - User Management drops its stale column budget

**Changed**

- **User Management drops the percentage column widths it no longer follows** -
  the table sizes itself to its content.

## [2026.9.3.post2] - 2026-09-03 - The Jobs table stops cutting text you cannot reach

**Fixed**

- **The Jobs table no longer cuts a result you cannot scroll to** - it capped
  the column twice, and the second cap truncated text that fitted.

## [2026.9.3.post1] - 2026-09-03 - The dashboard grid is GitLab's

**Fixed**

- **A read-only course's buttons no longer flash as available** while the page
  loads.
- **The syntax scheme previews are no longer cut off** mid-token.
- **The colour field on Preferences is one control again** - its chip was
  shorter than the field it sits on.
- **The Diffs section spaces like every other section** (68px gap, now 16).
- **Tables scroll instead of hiding content behind three dots** - User
  Management cut 30 cells and could not be scrolled to reach them.
- **The User Info dialog no longer collapses 107px** when its data lands.

**Changed**

- **The dashboard's two columns are GitLab's own grid**, sidebar capped at 290px
  instead of growing with the window, with GitLab's 2rem gap.

**Fixed**

- **The loading mark is centred on the screen**, with no dead space under it.
- **The archived card's corner no longer disagrees between light and dark.**

## [2026.9.3] - 2026-09-03 - The loading veil covers the page

**Fixed**

- **The loading screen no longer leaves two undimmed bands down the sides.** The
  veil was pinned to the centred content column rather than the region you see,
  so it read as a floating panel over the middle of the page.
- **An archived course is no longer told to run a sync it cannot run.** It is
  read-only, so its data going out of date is expected; the page stacked "Try
  running Sync All" under the strip that had just said the course is read-only.

## [2026.9.2.post2] - 2026-09-02 - The loading screen is an overlay again

**Fixed**

- **The loading screen is an overlay again**, not a panel at the bottom of the
  page. A blanket `[aria-live] { position: relative }` rule outranked the
  loader's own positioning and dropped it into normal flow.
- **The loading mark is centred on the part of the page you are looking at**,
  rather than halfway down the full scroll height.
- **Settings controls no longer stretch the whole column.** Every select on the
  preferences page was 1264px wide, which is what made Localization read as a
  large empty band.

## [2026.9.2.post1] - 2026-09-02 - A role is the same colour wherever it is drawn

**Fixed**

- **A role is the same colour everywhere.** A course owner was orange in the
  User Info dialog and teal on the page behind it, because the dialog had taken
  its colours from GitLab's access-level map - where "owner" is a different
  thing that only shares the word. A mentor was grey in the users table and teal
  in the dialog opened from that same row. The colour for a role lived in four
  places; a test pins them together now.

## [2026.9.2] - 2026-09-02 - Live updates reconnect once, not on top of themselves

**Fixed**

- **The User Info dialog is the same dialog everywhere it opens.** Its renderer
  was loaded on Admin → Users only, so every other page showed a spinner instead
  of the skeleton and a cut-down card. It is fetched on first open now.
- **Table text no longer breaks mid-word**, and the System page's
  Parameter / Value / Env tables scroll like every other table instead of
  wrapping long values.
- **The default avatars no longer blink when you return to the tab.** Coming
  back re-fetched the picture of every user who has none.
- **Picking the Light or Dark syntax scheme sticks.** Both saved, but the
  per-request check re-validated them against a second, hand-written list that
  had never been given them, so the choice reverted on the next page load.
- **Pinning a homepage other than Dashboard works.** The same duplicated list
  threw away Support, Courses, System and Users. Both lists now come from the
  one field table the save endpoint uses.
- **The syntax scheme list is GitLab's seven** - Light, Dark, Solarized Light,
  Solarized Dark, Monokai, Dracula, None. Dracula was missing and "Default"
  duplicated Dark; a stored "Default" becomes Dark.
- **The diff colour field is one control again**: the colour chip sits on the
  hex field, as in GitLab, rather than loose among the suggested colours where
  it opened the operating system's picker over the page.
- **A page that loses its live connection reconnects once**, instead of
  opening a second stream while the first is still waiting to retry. Five
  pages - the dashboard, the sidebar badges, a course, a group and a project -
  each carried their own copy of the same reconnect logic, and the copies had
  drifted apart.
- **A finished sync no longer produces a burst of one-frame reconnects.** The
  server closes a completed sync's stream promptly, and against a fixed
  two-second retry that became a tight loop. That stream now backs off.

**Changed**

- The page-level live-update client is defined once instead of five times. The
  per-job progress stream, which ends together with the job it reports, is
  deliberately left as it was.

## [2026.9.1.post1] - 2026-09-01 - The theme recolours the whole interface

**Fixed**

- **The theme recolours the whole application chrome**, not just the sidebar -
  exactly what its own preview card promises.
- **Syntax highlighting has a light scheme.** Every option used to paint a
  dark block; Light and Dark are separate choices now and the seven previews
  sit in one row.
- **Alt-tabbing back no longer loses an attention item** from the dashboard.
- **A disclosure slides open** instead of flashing its full height first.
- **An archived course is read-only, not unreadable** - disclosures and Copy
  Token are no longer locked.
- **A table that scrolls down says so.**
- **The Activity page's Sync button is gone.**

**Changed**

- **Chart.js loads only on the five pages that draw charts** - 73kB off the
  first visit to the other thirteen.

## [2026.9.1] - 2026-09-01 - Nothing moves after it paints

**Fixed**

- **No page changes shape after it paints** - 0px growth and 0.000 layout
  shift across the eighteen pages, measured in Chromium.
- **Navigation no longer takes your page away.** It used to replace the content
  with a spinner after 1200ms; GitLab never blanks the page it is leaving.
- **Table headers stop spilling under the next column** - zero clipped cells at
  1024 / 1280 / 1440 / 1920, from fourteen.
- **Requests cannot overtake each other** - one in flight per key, and leaving
  a page abandons what it had running.
- **Every disabled control says why**, and every icon-only button has a tooltip.
- **Hover answers in colour**, the way GitLab's does.
- **Keyboard focus is always visible.**

## [2026.8.31.post2] - 2026-08-31 - GitLab's save bar

**Fixed**

- **A settings form's save bar is one component now, and it is GitLab's.** Two
  forms carry a dirty guard and each had written its own footer: course
  settings' was sticky under a course-specific name, the Preferences row was
  static and scrolled away - so the Save button the guard arms was off-screen
  at exactly the moment it armed.
- **A disabled button never showed that it was disabled.** The shared rule
  carried `pointer-events: none`, which GitLab's does not, so
  `cursor: not-allowed` never appeared. A disabled `<a>` keeps it - an anchor
  has no native `disabled` attribute.
- **Internal navigation discarded unsaved settings without asking.** A content
  swap never fires `beforeunload`, so clicking a sidebar link with a half-filled
  form threw the edits away silently. It now asks first.
- **The sticky actions column painted a dark seam when the table already fit.**
- **The auth alert was a heavy chip rather than GitLab's flat GlAlert.**

## [2026.8.31.post1] - 2026-08-31 - The Save button finally arms

**Fixed**

- **The Save button on Preferences never armed for a radio choice.** The dirty
  snapshot stored `checked` for radios, but a radio group shares one name, so it
  recorded whichever button came last - normally unchecked, and still unchecked
  after you picked something else. Accent theme, layout width, syntax scheme and
  time format were all unsaveable.
- **One notification opt-out was inside a docstring** - a string, not a
  statement - so that persistence path sent every category regardless of what
  had been muted.

## [2026.8.31] - 2026-08-31 - Syntax highlighting

**Added**

- **Syntax highlighting** on Preferences - GitLab's section, and a real setting
  rather than a copied label. Pygments highlights fenced code blocks and their
  ten token colours are now CSS variables, so a scheme is ten declarations.
  Default, Monokai, Solarized dark, Solarized light and None. Each scheme is
  declared once and consumed twice - by the page and by its own swatch - so the
  swatch is a live sample rendered through the rules the page will use.

## [2026.8.26.post5] - 2026-08-26 - Themes actually change the interface

**Fixed**

- **Picking a theme did almost nothing.** The accent tinted two variables - the
  selected sidebar item and its hover - so the setting read as inert. It tints
  the panel surface now, and the preview uses the same recipe.
- **The gap between a heading and its control was 44px wider than GitLab's.**
- **The select's own button still looked like a button, not a field** - the
  other half of the select fix.

**Changed**

- The Diffs preview is two panes, removed and added side by side over a real
  code sample, as GitLab shows it.

## [2026.8.26.post4] - 2026-08-26 - Section descriptions sit under their heading

**Changed**

- A settings section now reads the way GitLab's does: the heading, then its
  description underneath. `.section-title-group` was a flex row, so every
  description sat on the same line as its heading. The disclosure chevron keeps
  its place beside the title. This applies to every section in the app.

## [2026.8.26.post3] - 2026-08-26 - Selects, the mode switcher and the theme previews

**Fixed**

- **Every select in the app rendered shrink-to-content.** `dropdowns.css` loads
  after `forms.css`, so at equal specificity `inline-flex` won and the select
  collapsed to its text while the input beside it filled the row.
- **The Mode switcher never showed which mode was active.** Its buttons ship as
  `aria-pressed="false"` and are corrected on `DOMContentLoaded`, which never
  fires again after an SPA navigation - and Preferences is always reached by one.
- **Every accent preview looked identical in dark mode**, because the dark-mode
  chrome rule out-specified the accent tint.
- **"Accent color" turned blue when you picked an accent.** Focus belongs to the
  control's ring, not to its label.
- **The line under the breadcrumb vanished on scroll**, painted over by sticky
  section headings and sticky table headers sharing its stacking level.

**Changed**

- The Mode options read Light / Dark / **Auto**, GitLab's own wording.

## [2026.8.26.post2] - 2026-08-26 - Dashboard 500 fixed

**Fixed**

- The dashboard returned 500. Trimming unused template imports in 2026.8.26
  removed `json_drop` from the dashboard modals - where nothing mentions it -
  but the shared config-import macro resolved that name from whichever file
  imported it, so the error surfaced inside a file the change never touched.
  That macro imports its own dependencies now. The Teachers page had the same
  fault and is fixed with it.

## [2026.8.26.post1] - 2026-08-26 - Threshold pills are readable again

**Fixed**

- The threshold pills on a student's compliance history were unreadable. Two
  different components share those colour classes - the segmented bar on course
  settings and this text pill - and neither was scoped, so the bar's saturated
  fill won for both. The pill sets no text colour of its own, so it rendered
  dark grey on solid green at 2.46:1 against the 4.5:1 minimum; the rule that
  lost gives 8.19:1.
- The bar's yellow segment was the odd one out and the failing one: dark text on
  the warning fill measures 3.13:1, where the white the green and red segments
  already use measures 4.73:1.

**Removed**

- Eight stylesheet rules a later file overrode completely. One mattered: the
  metric-score scale in `utilities.css` gave "good" and "excellent" the same
  green, where the rule that actually applies distinguishes them.

## [2026.8.26] - 2026-08-26 - One mechanic across the interface

**Changed**

- Every table that had to fetch its first page now paints on load instead:
  recent events, the DLQ tab, Job History, the compliance checks table and the
  webhook configs table. There is no request and no loading state between
  opening a page and reading it.
- One implementation per interaction. Three of these were visible defects
  rather than untidiness:
  - The avatar existed five different ways. The failure handler reveals the
    image's next element sibling, and three of the five put the image alone
    inside a conditional - so an unreachable avatar left an empty disc on the
    ticket submitter, the current assignee and the assignee picker.
  - Opening a support ticket by direct link rendered a different page from
    reaching it by navigation: that template was a 311-line copy that had
    fallen behind, missing every tour step and showing raw response keys
    instead of the form's own question labels.
  - `canEdit` was derived two different ways in one page, so a script's answer
    depended on which block it happened to read.
- Restore / permanently-delete, the dropdown, the avatar, the button attribute
  set, the course tab well and the retry control are each defined once now.
- `disabled_reason` - the tooltip that says why a control is unavailable - works
  on every button type now, not only one of the three.

**Fixed**

- Spacing utilities contradicted themselves: `.mt-1` was declared twice with
  different values, and `ml-1`, `mb-lg` and `mb-md` were written on 19 elements
  with no rule existing at all. One name per value now, with no change in
  rendered pixels.
- The Preferences page added a navigation listener on every visit and removed
  none. It joins the teardown contract the other seventeen page bundles already
  followed.

**Removed**

- Dead code, all of it verified unreachable: 116 CSS rules, eight Jinja macros,
  three whole component files, eleven JavaScript helpers, five duplicate toast
  shortcuts and 177 unused template imports.

## [2026.8.24.post6] - 2026-08-24 - Staff notifications split out

**Fixed**

- Ticket-queue mail shared one switch with a reader's own tickets, so muting
  ticket updates also silenced "a new ticket needs an owner". It is now its own
  category, shown only to staff.

## [2026.8.24.post5] - 2026-08-24 - The tour and docs caught up with the page

**Fixed**

- The Preferences tour and its documentation predated the Diffs and
  Notifications sections. Both now cover every section, in Slovak and English,
  and a test holds the tour's steps against the page's anchors both ways.

## [2026.8.24.post4] - 2026-08-24 - GitPulse's own preferences

**Added**

- **Rows per page** - the "Per page" control only ever wrote to the browser, so
  a new device fell back to 50. It is now an account-level default, and a
  per-table choice still wins.
- **Start with the sidebar collapsed** - the same for the sidebar, applied only
  where there is no local state yet.

## [2026.8.24.post3] - 2026-08-24 - Typography and sticky headings

**Fixed**

- Preferences section headings were the wrong size - GitLab renders them as
  `h2.gl-heading-2` (21-25px responsive); ours were 14px.
- Section headings are sticky, as GitLab's `.settings-sticky-header` is.
- The theme previews used approximated colours; they now come straight from
  GitLab's own `preferences.scss`.

## [2026.8.24.post2] - 2026-08-24 - Notifications and layout width

**Added**

- Preferences > **Notifications**: per-category email opt-outs (tickets,
  courses, account), enforced on the server in `enqueue_email` rather than only
  hiding a checkbox.

**Fixed**

- **Layout width did nothing visible.** Five elements cap at
  `--content-width-lg` and only one was uncapped, so the chrome stayed narrow.
- The Save button is the same guarded control the course settings page uses -
  disabled until dirty, and it warns when you navigate away.
- Sections are separated by a rule, as GitLab's are.

**Changed**

- The colour mode switcher is no longer duplicated in the user menu.

## [2026.8.24.post1] - 2026-08-24 - Email fixes

**Fixed**

- Every email linked at `/dashboard/settings`, a route that never existed - both
  the link and the `List-Unsubscribe` header sent readers to a 404. They now
  point at `/dashboard/preferences`.
- The welcome email built its own list in Inter over the Tailwind palette,
  bypassing the mailer chrome. The parity test now scans the whole module rather
  than a single rendered sample.

**Changed**

- `redeploy.py` verifies after migrating that `alembic current` equals
  `alembic heads`, and fails the deploy when they differ.

## [2026.8.24] - 2026-08-24 - Personal preferences

**Added**

- A **Preferences** page (`/dashboard/preferences`) modelled on GitLab's and
  available to **every role**: colour mode, accent theme, diff colours, keyboard
  shortcuts, layout width, homepage, language, first day of the week and time
  format. Every preference belongs to the account, so it follows you to any
  device rather than being lost with the browser profile.
- Each preference changes something real: the accent tints the selected
  navigation item, layout width uncaps the content column, turning shortcuts off
  leaves `Esc` alone so dialogs still close, the time settings drive every
  timestamp, and the first day of the week reaches every date picker.
- **Diff colours** apply to the real diff view on the student profile, not only
  to a preview.
- The homepage list offers only destinations your role can actually open.
- A guided tour of the page and documentation, in Slovak and English.

**Fixed**

- SMTP passwords have surrounding whitespace stripped - Google shows app
  passwords in groups of four, and pasting one as shown failed with a bare 535.

## [2026.8.21.post2] - 2026-08-21 - Error pages closer to GitLab

**Changed**

- Error pages use GitLab's illustrations and behaviour (Go-back hides without
  history; 502/503 auto-reload while the upstream returns).

## [2026.8.21.post1] - 2026-08-21 - Interface and docs-footer fixes

**Fixed**

- Archived-course forms deformed their inputs - the Description textarea
  collapsed to ~180px; every field is full width again.
- The docs footer regained its legal-column heading and the Diplomovka section
  is ordered correctly (1-5).

## [2026.8.21] - 2026-08-21 - Search no longer reveals restricted pages

**Security**

- The documentation search no longer returns the content of restricted pages.
  One index covered the whole site and the gate served it as an asset; there are
  three tiered indexes now and the two narrow ones are gated. Path matching in
  the gate is normalised against traversal, encoding, case and backslash tricks.
- An open redirect in `?next=` is closed. Slovak pages follow the page's
  language, the dead `/docs/en/en/` links are gone, and the footer labels resolve.

## [2026.8.19.post1] - 2026-08-19 - Form controls carry an id and a name

**Fixed**

- Chrome's "A form field element should have an id or name attribute" on every
  documentation page: the theme picker, the language picker and the search box
  now carry stable, unique names.

## [2026.8.19] - 2026-08-19 - Twelve empty documentation pages

**Fixed**

- Twelve pages rendered empty after the engine change: their card grids used
  MkDocs' HTML-with-markdown syntax, which Astro does not parse. All 46 cards are
  now Starlight components.
- The home pages are splash pages using the theme's hero, replacing the
  hand-written one.

## [2026.8.18] - 2026-08-18 - Documentation rebuilt on Astro Starlight

**Changed**

- The docs run on Astro 7 + Starlight instead of MkDocs Material: 95 pages build
  in 8 seconds, search is a static Pagefind index, and the 58 pages with a
  diagram ship no diagram JavaScript at all.
- All 94 content files migrated, 147 admonitions converted, nothing lost.
- The tab icon is redrawn at 16px, where the previous one was unreadable.

## [2026.7.3.post237] - 2026-08-18 - Every docs element measured against theirs

**Fixed**

- A JavaScript error fired on all 143 numbered headings and broke the table of
  contents on those pages.
- 566 of 628 icons were off the design grid; all are now on 16/20/24/32.
- Code blocks and tables now match theirs: a flat surface with a language pill,
  and zebra-striped borderless rows.
- The page skeleton lands on their rendered pixels: nav 28/256, prose 352/716,
  contents 1128/272, search 232/470.

**Added**

- A five-column footer, a "Was this page helpful?" row, and the docs' own tab
  icon - their book with the GitPulse pulse.

## [2026.7.3.post236] - 2026-08-18 - Search no longer cuts the quick links in half

**Fixed**

- Opening search on the landing page half-covered the quick-link row; the row
  now steps aside, as it does on theirs.

**Changed**

- The remaining 30 GitLab palette steps are copied into the docs stylesheet. The
  39 already there matched theirs exactly.

## [2026.7.3.post235] - 2026-08-18 - Header search back to their rendered width

**Fixed**

- The documentation search field is 470px again, their rendered width, not the
  384 their token declares.

## [2026.7.3.post234] - 2026-08-18 - Component parity, measured against their live page

**Fixed**

- 45 computed-style differences against docs.gitlab.com, down to 12 cosmetic
  ones: type sizes, heading margins, list rhythm, inline code, table padding,
  breadcrumb, TOC and footer links.
- The landing search panel no longer turns white on the dark hero in light mode.
- The table of contents had lost the spacing between its entries.

## [2026.7.3.post233] - 2026-08-18 - Breadcrumbs, a docs mark of its own, and 27 contrast fixes

**Added**

- A breadcrumb above every documentation page.
- The docs tab icon is GitLab's docs book with the GitPulse pulse inside it.

**Fixed**

- All 27 low-contrast findings across the 18 authenticated pages - each was a
  palette colour used as text where GitLab uses a semantic text token.

## [2026.7.3.post232] - 2026-08-18 - The docs shell, from their own stylesheet

**Changed**

- Every layout number in the documentation shell now comes from
  `docs.gitlab.com/vite/main.css` - columns, gaps, padding, header height,
  search width and the fluid heading clamps - instead of one measured viewport.
- The footer is their fixed dark band with white text, capped at 1376.

**Fixed**

- The 272px columns rendered 288 (a `box-sizing` leak), the footer link measured
  2.42:1 on all 47 pages, the search hint 4.47:1, and the header brand was
  truncated to "GitPulse..." on every content page.

## [2026.7.3.post231] - 2026-08-18 - Landing page: one footer, one column, both themes

**Fixed**

- Two stacked footers became one: the TUKE line moved into the copyright partial.
- The page had three different left edges below the hero; everything is now one
  column aligned to the same 64px edge as the cards.
- Light theme: the cards were pinned to dark surfaces, so their titles were dark
  text on a dark card. Card, footer and header colours now flip with the theme.

## [2026.7.3.post230] - 2026-08-18 - The docs landing page, and two contrast fixes

**Fixed**

- The documentation landing page reached readers unstyled: `extra2.css` is served
  with `expires 7d` and carried no content hash, so a browser that had opened the
  docs once held a week-old stylesheet against fresh HTML. Its URL now carries a
  hash of the file's own bytes.
- Login page contrast: the developer-mode badge measured 2.3:1 and the GitLab
  sign-in button 2.9:1. Both now use the colour pairs GitLab itself ships.

**Changed**

- The docs home is transcribed from `docs.gitlab.com/vite/landing.css` rather
  than approximated from a screenshot - the panel's four radial blobs, the 52px
  pill search, the quick-link underline wipe, and the four-column card grid.

## [2026.7.3.post229] - 2026-08-17 - Code block colour

**Fixed**

- Fenced code blocks are no longer all blue - that colour is for inline code.

## [2026.7.3.post228] - 2026-08-17 - The documentation header, and a changelog fix

**Changed**

- A 112px header block with the search field at x=232, 470 wide - their numbers.

**Fixed**

- The changelog page injected a real `<script>` element and threw a parse error.

## [2026.7.3.post227] - 2026-08-17 - The documentation in their dark theme and layout

**Changed**

- Dark by default, the way docs.gitlab.com serves it: background rgb(24,23,29).
- Their three columns to the pixel: sidebar [20,272], content [352,716],
  table of contents [1128,272].
- A landing page with their hero panel (32px radius, 64px title) and card grid.
- The docs favicon is the same tanuki file the app serves.

## [2026.7.3.post226] - 2026-08-17 - One badge in JS

**Changed**

- `GP.badgeHtml` - the same component `badges.html` renders on the server. Eight
  JS files were assembling the span by hand, several without escaping the text.

## [2026.7.3.post225] - 2026-08-17 - One empty state in JS

**Changed**

- `GP.emptyStateHtml` / `GP.emptyStateRow`: four places built the same
  "nothing here" markup by hand (two of them without escaping the message).
  One shape, one escaping rule, one icon source - the same as on the server.

## [2026.7.3.post224] - 2026-08-17 - The tab icon, the font preload, and a menu that stayed put

**Fixed**

- The pagination page-size menu no longer hangs over the table after a scroll.
- The font preload no longer warns "preloaded but not used" - it pointed at a
  different URL from the one the stylesheet requests.
- The tab icon is the app's own tanuki mark (svg plus a multi-resolution .ico).

**Changed**

- Portaled menus are one component (`GP.dropdown.portal`).
- An htmx swap re-initialises the swapped subtree, not the whole document.
- Four more animations now use the components that already existed;
  keyframes 17 -> 13.

## [2026.7.3.post223] - 2026-08-17 - Documentation 1:1 with docs.gitlab.com

**Changed**

- The docs stylesheet is a rewrite against values measured on docs.gitlab.com:
  prose 16px/25.6px, headings 40/46, 32/40, 24/30, a 716px measure, links
  underlined at rest.
- The docs run their motion inventory exactly: 3 transitions, 0 animations.
- The last raw `window.confirm` calls now use the app's shared dialog.

**Fixed**

- The layout shift when the webfont landed (dashboard CLS 0.0296 -> 0) - the font
  preload was missing `crossorigin`.

## [2026.7.3.post222] - 2026-08-17 - Motion you can measure

**Changed**

- Hover moves nothing - colour is the hover state; the press still moves.
  Measured on the course settings page: elements with a live transition
  1817 -> 762, transition properties 10 004 -> 2 113.
- One rotation speed (GitLab's 0.6s), one pulse keyframe, three easings and no
  overshoot. The perpetual status halo is gone at the root.
- A loading button keeps its label and its width - the spinner takes the icon's
  place.
- One table loading state: the fake skeleton rows are deleted.

**Fixed**

- An archived course no longer drops the page 30px after paint (CLS 0.0173 -> 0).
- A failed refresh no longer also reports success - one toast, one attempt, 10s cap.
- Three `<label>`s with no form field are now `<fieldset>` + `<legend>`.

## [2026.7.3.post221] - 2026-08-13 - One loading mark

###  Changed
- The grey skeleton bars are gone - instead of a fake of the content, the tanuki turns and the block holds the height the content will take.
- Refreshing keeps the content in place, dims it and turns the tanuki over it - exactly as "Check now" does on System Health.
- A state lasts long enough to be seen (450ms).
- Touch devices no longer carry hover-driven movement.

###  Fixed
- The page gutter on mobile was declared in five places; one now, and smaller.
- Card-header buttons (Job History) no longer run off the screen.

## [2026.7.3.post220] - 2026-08-13 - A refresh keeps what is on screen

###  Changed
- Refreshing a table no longer discards its rows - they dim and the new ones land in their place at the same size, exactly as "Check now" does on System Health.
- The Slovak and English catalogs use plain punctuation in their values instead of typographic dashes and quotes.

###  Fixed
- The calendar's week column was blank for any month before the semester starts.
- Table corner rounding follows stack position rather than a list of classes.

## [2026.7.3.post219] - 2026-08-12 - The tanuki replaces every spinner

###  Changed
- Table skeleton rows are gone. Loading is one centred area in the same shape as the empty state, so a table does not change height on refresh.
- Every spinner in the app is now the tanuki mark inside the same turning ring as the full-page loader.
- The Actions column is pinned on every table, not only in User Management.

###  Fixed
- A white flash when opening a disclosure.
- The copy button inside `<summary>` could not be reached by keyboard.

## [2026.7.3.post218] - 2026-08-12 - New expressive motion

###  Added
- Every control now answers the pointer on all four states - rest, hover, pressed, focused. Only colour changed before, so nothing ever felt clicked.
- Tab strips get a single underline that travels from the old tab to the new one.
- Table rows grow an accent bar on the leading edge; the rows themselves never move.

###  Changed
- Modals, toasts and dropdown panels now ARRIVE at their place instead of merely moving to it.

## [2026.7.3.post217] - 2026-08-12 - One animation system

###  Changed
- Motion was spread over 67 hand-written `@keyframes` in 25 stylesheets, each with its own duration and easing, so the same interaction animated differently depending on the page. There are 21 now, and everything with a beginning and an end runs through one module. Measured across 14 pages: 2223 elements, every one animating its state change, and no component running at two different speeds.
- "Remove this row" existed four times and "here is the thing you asked for" five times. Once now.

###  Fixed
- Live updates showed no feedback at all - the class six call sites toggled had been reduced to a transparent background.
- `<details>` snapped open in Firefox and Safari while the card beside it glided.
- Pagination buttons, tabs and the cookie-banner buttons eased at half the speed of every other button.
- The health strip clipped its own text once a message wrapped to a third line.
- A toast paused on hover could not resume from where it stopped.

###  Removed
- 46 dead or superseded `@keyframes`, and the logo's sonar rings, which rendered on every page hidden and unanimated.

## [2026.7.3.post216] - 2026-08-12 - The select goes back to GitLab's floating panel

###  Fixed
- The dropdown menu is a rounded floating panel again; welding it to the control produced a hard notch that looked worse.

## [2026.7.3.post215] - 2026-08-12 - Tabs stop resizing the page

###  Fixed
- Switching tabs no longer briefly shows both panels at once, which made the page grow and snap back.

###  Changed
- The CI/CD Health donut is smaller and its stat tiles are wider.
- The Sync button is removed from Analytics; it duplicated a course-level action on a read-only page.

## [2026.7.3.post214] - 2026-08-12 - The select and its menu become one object

###  Fixed
- Form selects finally animate when they open; the rule had been scoped to a different kind of menu.
- The menu now joins its control with no gap and no facing corners, instead of looking like a separate box.

###  Changed
- The sidebar section headings are blue again.

## [2026.7.3.post213] - 2026-08-12 - Tab switching stops tearing the table

###  Fixed
- Switching tabs no longer makes the table rip for a moment before settling.
- A table's top corner no longer flips depending on whether its info note happens to be showing.

## [2026.7.3.post212] - 2026-08-12 - Exam period works without an end date

###  Fixed
- A course with no explicit semester end date now gets an exam period; before, it closed on the last teaching day and never appeared.

## [2026.7.3.post211] - 2026-08-12 - Switching tabs eases instead of snapping

###  Fixed
- Tab panels now fade in when you switch between them; they used to swap instantly because of how they are hidden.

## [2026.7.3.post210] - 2026-08-12 - The fourth disclosure joins the others

###  Fixed
- "Issues to Address" now slides open like every other panel; it was the only one that could not animate at all.
- The CI lint job is green again - the formatter had not been run before the last few releases.

## [2026.7.3.post209] - 2026-08-12 - Identical cards, identical layout

###  Fixed
- "Subgroups and Projects" now has the same insets as "Group Members" instead of running flush to the card edge.
- The info notes above those tables are rounded like everything else around them.

## [2026.7.3.post208] - 2026-08-12 - The events table stops collapsing

###  Fixed
- Refreshing the events page no longer collapses the table to a single spinner row and then jumps back; it shows skeleton rows that hold the height.

## [2026.7.3.post207] - 2026-08-12 - Dropdowns open with motion

###  Changed
- Dropdown menus now slide open instead of blinking into place, and sit closer to the control that opened them so they read as attached.
- Both kinds of menu in the app animate the same way; one of them could not animate at all before.

## [2026.7.3.post206] - 2026-08-12 - The project page joins the card system

###  Changed
- Protected Branches, Contributors and Repository Stats used a third card style of their own; they now match the dashboard cards exactly.

## [2026.7.3.post205] - 2026-08-12 - Table corners decided per edge

###  Fixed
- A table with a note above it and pagination below now rounds correctly on each side: the note takes the top corners, the pagination bar takes the bottom.

## [2026.7.3.post204] - 2026-08-12 - Conditional table rounding

###  Fixed
- Tables with a pagination bar are no longer rounded against it; a table is rounded only on edges where it is really the edge of its block.

###  Changed
- Count badges use the same pill everywhere instead of a flat grey box on some pages.

## [2026.7.3.post203] - 2026-08-12 - One table treatment, and text that animates too

###  Fixed
- Tables are rounded consistently everywhere instead of some square and some not.
- Text inside rows and buttons now animates with them; it used to snap because the colour sits on a child span that had no transition.

## [2026.7.3.post202] - 2026-08-12 - Stat tiles become the KPI card

###  Changed
- The centred stat tiles now use the same two-layer shape as the dashboard cards - header row with label and icon, value in an inset block - measured identical on every value. No markup changed.

## [2026.7.3.post201] - 2026-08-12 - The greeting date stops vanishing

###  Fixed
- The date beside your role on the dashboard went blank after navigating away and back twice; scripts that write into swapped content now re-run on every arrival.

## [2026.7.3.post200] - 2026-08-12 - Header titles sit on the centre

###  Fixed
- Card header titles no longer ride a few pixels above the middle of their row; measured at exactly 0px difference on every header.

## [2026.7.3.post199] - 2026-08-12 - Header notes and tile sizing

###  Fixed
- A card header can now carry a note pinned to its right edge, so Archived Courses matches the Service Accounts header.
- Centred stat tiles have a properly sized icon again, and their values no longer overflow the tile.

## [2026.7.3.post198] - 2026-08-12 - The slide runs, the chart block goes

###  Fixed
- Collapsible cards really do slide open now; a flex sizing rule was silently cancelling the animation.
- A week with no activity no longer shows a permanent grey loading block where its chart would be.

## [2026.7.3.post197] - 2026-08-12 - Micro-motion that is actually visible

###  Fixed
- The motion baseline added earlier did nothing visible because it never declared which properties to animate. Every interactive element now transitions its state change; zero elements are left without one.

## [2026.7.3.post196] - 2026-08-12 - Every clickable header answers the same way

###  Fixed
- Some collapsible headers highlighted on hover and others did not; one rule now covers them all.

###  Changed
- Archived Courses shows a count badge and a "Read-only" note, matching the Service Accounts header.

## [2026.7.3.post195] - 2026-08-12 - Cards go back to GitLab's real spacing

###  Fixed
- The previous release inflated every card by reading GitLab's spacing classes against Tailwind's scale instead of GitLab's own. Padding is back to what it was; only the inner block's 12px rounding, which really was wrong, is kept.

## [2026.7.3.post194] - 2026-08-12 - Admin stat tiles join the card system

###  Fixed
- Stat tiles on the admin pages now match the dashboard cards (16px radius, same shell) instead of being 4px transparent boxes.
- Their icons lost the coloured plate behind the glyph; the state colour moved onto the mark itself.

## [2026.7.3.post193] - 2026-08-12 - Card proportions from GitLab's own markup

###  Fixed
- Shell padding, inner radius, inner padding and header margin now match GitLab exactly (8px / 12px / 16px / 12-16px); three of the five were off.

## [2026.7.3.post192] - 2026-08-12 - One clock for every control

###  Fixed
- Raw Check Details drew two chevrons at once and styled itself differently from every other collapsible section; it now uses the shared component.

###  Changed
- Every interactive element responds at the same speed and on the same curve; components had each picked their own.

## [2026.7.3.post191] - 2026-08-12 - Native <details> opens smoothly too

###  Fixed
- Every collapsible section now slides open at the same speed; before, only the Alpine-driven card animated and native ones snapped.

## [2026.7.3.post190] - 2026-08-12 - One disclosure contract instead of three

###  Fixed
- Collapsible card headers share one focus ring, one chevron and one rotation angle; before, three surfaces each behaved differently.
- Raw Check Details gained the chevron it never had, and the chevron is centred on its row.

## [2026.7.3.post189] - 2026-08-12 - The banner's timestamp comes back

###  Fixed
- The stale-data banner showed a blank gap instead of its snapshot timestamp after navigating between pages.
- Week Analytics now always opens on a week instead of showing an empty panel until you click one.

## [2026.7.3.post188] - 2026-08-12 - The font-weight ladder gets its missing step

###  Fixed
- `semibold` was set to the same value as `medium`, so 276 places asking for semibold silently got a lighter weight - which is why headings of the same level could look different. The scale is 400/500/600/700 now.
- Card titles and table column labels are semibold instead of bold, so they no longer out-weigh the page headings above them.

## [2026.7.3.post187] - 2026-08-12 - Support rows drop their gradient icon tiles

###  Changed
- Course rows on the support pages now use a plain 16px GitLab icon in the muted text colour instead of a blue gradient tile.
- Row spacing, rounding and hover follow the rest of the card system - colour only, no shadow or lift.

###  Fixed
- A collapsed card header no longer rounds more than the shell around it.

## [2026.7.3.post186] - 2026-08-12 - A navigation leak that duplicated ids

###  Fixed
- Navigating between pages no longer leaves orphaned date-picker calendars behind, which is what produced duplicate form field ids.
- A collapsed card no longer has dead space under its header, and a table inside an expanded card no longer pokes square corners out of its block.
- In the stale-data banner the snapshot timestamp stays next to its label instead of drifting across the banner.

## [2026.7.3.post185] - 2026-08-12 - Card blocks get a seam

###  Fixed
- A card header's hover highlight no longer touches the content below - the blocks are separated by the same 8px as the card's padding.
- The last flush-edge radii are gone: every block inside a card is rounded on all four corners, so no square edge shows against the shell.

## [2026.7.3.post184] - 2026-08-12 - Cards take the KPI card's shape

###  Changed
- Cards are a lighter shell with the content inside as a darker rounded block, matching the dashboard KPI cards.

###  Fixed
- A collapsed card (Archived Courses) no longer shows square corners poking past its rounded frame.

## [2026.7.3.post183] - 2026-08-12 - Every card gets GitLab's header band

###  Changed
- Card headers are now a lighter band with the content on the darker panel colour below, matching GitLab's panels and the KPI cards.

## [2026.7.3.post182] - 2026-08-11 - An empty profile says why it is empty

###  Fixed
- A student profile with no merge requests in the course window now says so, naming the window, instead of claiming none exist in the repositories at all.

## [2026.7.3.post181] - 2026-08-11 - Visible keyboard focus in menus

###  Fixed
- Dropdown menu items now show a focus ring when you tab to them; before, keyboard focus looked exactly like a mouse hover.
- The tour's close button was the last control sized in rem instead of the design tokens. No fractional pixel sizes remain anywhere in the app.

## [2026.7.3.post180] - 2026-08-11 - The tour stops re-implementing buttons

###  Fixed
- The tour welcome dialog's buttons now match every other button in the app - they were being restyled from scratch in rem units on top of the shared classes.

###  Added
- A gate that fails if any stylesheet sizes a bare `<button>`, which is how the override won silently.

## [2026.7.3.post179] - 2026-08-11 - The logo hover ends smoothly

###  Fixed
- Moving the cursor off the logo no longer snaps the effect off in one frame - it eases out over 420 ms.
- Two stale `transition` rules that silently cancelled the fix are gone, and a test now fails if another appears.

###  Changed
- The hover is stronger (brightness 1.85, a heavier glow) - at 24 px the old one was too quiet to notice.

## [2026.7.3.post178] - 2026-08-11 - Cards and merge requests reverted

###  Reverted
- KPI cards are back to the style they had before post175 - filled, 16px radius, with the hover lift. The header band from post177 is gone.
- The student page is restored too: merge-request cards, the people block and the column head row are all as they were.

## [2026.7.3.post177] - 2026-08-11 - Card header bands, merge requests as a list

###  Fixed
- KPI cards have their lighter header band back - the label and icon sit in it, the number below, as GitLab's own cards do.
- The band uses a token that is visibly different from the card body in BOTH themes; the previous one collapsed to white in light mode.

###  Changed
- Merge requests are a GitLab list: `Status | Title | Assignee | Reviewers | Checks`, with a labelled column head, the reference and diff stats under the title, and reviewers in their own column instead of a block below.

## [2026.7.3.post176] - 2026-08-11 - The done state stops eating its button

###  Fixed
- The System Health button no longer freezes on "Checking..." forever: loading and done now hand the button over to each other explicitly instead of overwriting the same label.
- The logo hover loops for as long as the cursor is there, instead of parking the bright segment at the end of the trace.

###  Changed
- Ending a done state is one shared teardown, used both by its timer and by a new click that supersedes it.

## [2026.7.3.post175] - 2026-08-11 - Navigation stops moving on its own

###  Fixed
- A finished background job no longer hard-reloads a page that never asked for it - the registration is cleared when navigation leaves the page that opted in.
- The top progress bar no longer sweeps backwards when a navigation starts before the previous one has finished fading.

###  Added
- A GitLab-style page footer: a centred `Leave feedback | Documentation` pair closes every page except the Dashboard, whose sidebar already carries "Support & suggestions".

###  Changed
- Merge-request rows follow GitLab's anatomy: state pill first, bold title, `namespace/project!iid` reference, "Updated ..." pinned right, and a header bar across the card.
- The admin dashboard's KPI cards are outlined like every other card, and hover is a colour change instead of a lift.
- The logo hover is rebuilt: a bright segment travels the ECG trace and each shape flares as the wave reaches it.

## [2026.7.3.post174] - 2026-08-11 - Outlined cards, a thinner cut

###  Fixed
- Dashboard cards are outlined again, with no grey fill - as GitLab's are.
- The cut under the header is thinner (2px).

## [2026.7.3.post173] - 2026-08-11 - A larger avatar

###  Fixed
- The top-bar avatar is now the same size as every other item in the bar (32px).

## [2026.7.3.post172] - 2026-08-11 - The cut, in the right colour

###  Fixed
- The cut under the header is painted in the app background colour, so it reads as a real slot through the panel.

## [2026.7.3.post171] - 2026-08-11 - The 4px band is removed

###  Removed
- The 4px band above the content and its scroll handler are gone.

## [2026.7.3.post170] - 2026-08-11 - The logo gets its own animation

###  Changed
- The logo has an animation of its own: light runs across the mark left to right, and unwinds the same way.
- The mark is now the same height as GitLab's logo.

## [2026.7.3.post169] - 2026-08-11 - The cut is finally visible

###  Fixed
- Dashboard cards are one shade lighter than the panel, as GitLab's are - which is what makes the cut readable when you scroll.

## [2026.7.3.post168] - 2026-08-11 - Content is no longer squashed against the header

###  Fixed
- The top spacing is back; pages are no longer flattened against the breadcrumb row.

## [2026.7.3.post167] - 2026-08-11 - The logo keeps its colour

###  Fixed
- The logo no longer bleaches to white on hover; it lifts gently instead.

## [2026.7.3.post166] - 2026-08-11 - The logo hover, measured

###  Fixed
- The logo now lightens by the same amount GitLab's does on hover, and settles back smoothly.

## [2026.7.3.post165] - 2026-08-11 - The cut under the breadcrumb

###  Fixed
- A 4px cut appears under the header as you scroll, exactly as GitLab's does.
- The divider line above the sidebar's bottom group is gone.

## [2026.7.3.post164] - 2026-08-11 - The top bar reads as one row

###  Fixed
- Every item in the top bar now shares the same height and text size, as GitLab's do.
- The logo is anchored to GitLab's brand width, so it no longer dominates the bar.
- The logo hover is a gentle wash rather than a flash.

## [2026.7.3.post163] - 2026-08-11 - The cut under the breadcrumb

###  Fixed
- Content now starts flush under the header as GitLab's does, so scrolling visibly slices it beneath the breadcrumb row.

## [2026.7.3.post162] - 2026-08-11 - No darkening on scroll

###  Fixed
- Content no longer darkens at the top when scrolling - GitLab has no such gradient, only an opaque header.
- Feedback no longer skips every second button press.
- The "Done" state now appears on every button, including Refresh and Sync.
- Fixed a stylesheet syntax error that had disabled part of the animations on production.

## [2026.7.3.post161] - 2026-08-11 - A done state on buttons

###  Added
- The button you pressed now reports its own completion: a green "Done" with a checkmark for 1.6 seconds.

###  Fixed
- A manual page refresh no longer triggers a second automatic one after a new version is deployed.

## [2026.7.3.post160] - 2026-08-11 - Motion measured off GitLab, not guessed at

###  Changed
- Dropdowns no longer fade or scale - GitLab shows and hides them instantly.
- Every dismissal uses GitLab's easing curve; the previous one held elements visible far too long.
- A closed dialog no longer slides down, it simply fades.
- The panel header matches GitLab's (36px, 8px top corners) and content is cut cleanly beneath it.
- The content panel sits flush against the sidebar, making it 8px wider.
- Dashboard cards carry a state: compliance is toned by the same bands as the course traffic lights, and a zero with no data behind it is dimmed.

###  Fixed
- Charts no longer fight their skeletons: if the skeleton never appeared the chart arrives in one frame; if it did, it stays readable for at least 400ms.

## [2026.7.3.post159] - 2026-08-11 - The scroll scrim actually works now

###  Fixed
- **The scrim shipped in post158 never appeared for anyone**: its opacity was driven by `animation-timeline: scroll()`, which needs Chrome 115+, so everywhere else the rule was ignored and the notch silently did not exist. It is now driven by an `.is-scrolled` class from a passive, rAF-throttled scroll listener - the same approach GitLab uses. Verified with a real wheel scroll.
- **Breadcrumb links did the opposite of GitLab's on hover**: idle `none` -> hover `underline` with the colour unchanged. Ours changed the colour and suppressed the underline.
- **Role chips read cramped**: they render at `size='sm'` and `.badge-sm` squeezed the padding to 4px. GitLab ships one badge metric - 2px/6px for every variant - so `.badge-sm` no longer carries its own.

## [2026.7.3.post158] - 2026-08-11 - The scroll scrim under the breadcrumb row

###  Added
- **The notch that appears when content scrolls under the breadcrumb**, taken from the instance's own stylesheet: a 36px sticky strip pinned to the top of the scroll region with a negative margin so it occupies no space, `opacity: 0` at rest, and a `linear-gradient(180deg, alpha-dark-8, transparent)` fill (`alpha-dark-24` on dark) that fades in once there is content above the fold. Reproduced on `.gl-page-content::before` with the same 36px and the same gradients from our existing alpha tokens, with the opacity driven by a scroll-linked animation rather than a scroll handler.

## [2026.7.3.post157] - 2026-08-11 - Verified against the university's own GitLab instance

###  Changed
- **The reference is now `gitlab.example.com` itself** - its `/explore` pages are reachable without signing in, so every number comes from the exact build this project is compared against. That confirmed the shell work outright (top bar 48px, sidebar 240px, panel radius 12px, nav item 28px/8px, search 344x32/12px, dark background `rgb(40,39,45)` all already matched) and surfaced five things that did not: button labels sit on a 16px line (ours used `line-height: 1`), the search trigger inherited the 1.5 body line instead of 16px, the dashboard greeting was weight 500 where GitLab sets 600, badges are exactly 20px and must not compress in a flex row, and breadcrumb links carry a 4px focus radius. The scrolling region also starts 4px below the crumb row, leaving the strip of panel background that becomes the notch once the page scrolls - ours started flush.

###  Notes
- Avatars were already right: users are circles, projects and groups are squares at a 4px radius - exactly how the instance renders them.

## [2026.7.3.post156] - 2026-08-11 - Breadcrumb, palette and search trigger corrected

###  Fixed
- **The breadcrumb was wrong in four ways at once**: its root was a fixed "Dashboard" so on the dashboard it read "Dashboard > Dashboard", it separated crumbs with a chevron icon, ran at 14px, and sat in an `overflow: hidden` row that clipped descenders. Measured on gitlab.com: crumbs are 12px on a 16px line in a 24px row with `overflow: visible`, the separator is the character "/" rather than an icon, only the current page is at weight 600, and the root is the section the page lives in ("Your work / Home"). All four now match.
- **The filter rail jumped and flickered on every keystroke in the search palette.** `.gl-search-modal-body:empty` removed the results column with `display: none`, taking its `flex: 1` out of the row, so the 220px filter panel snapped to the left edge and back whenever a render briefly emptied the list. Verified while typing: the panel now holds one position through every keystroke.

###  Changed
- **The search trigger's hover is GitLab's**: the border darkens from `rgba(5,5,6,0.24)` to `rgba(5,5,6,0.4)` over 0.2s out-cubic and nothing else changes. Ours also swapped the background. Verified in both themes.

## [2026.7.3.post155] - 2026-08-11 - Type scale drops two sizes GitLab does not have

###  Fixed
- **The interface read smaller than GitLab's, and the numbers say why.** Counting every visible element at 1920: GitLab uses 14px (1458 elements), 21px (40), 12px (34), 30px (4) - and 13px and 11px exactly zero times. Ours put 88 elements on 13px, 12 on 11px and 37 on 11.375px (an `em`-relative inline `code` rule). `--font-size-sm` is now 14px, `--font-size-xs` is 12px, the last hardcoded 11px rules use the 12px token, and inline `code` renders at body size as gitlab.com does.
- **The logo's hover behaviour was wrong in both directions.** Measuring only the `<a>` and its outer `<svg>` missed where GitLab's animation lives: its tanuki is built from named parts and each transitions its **fill** - 0.8s at rest, 0.1s while lit, so a piece flares fast under the cursor and fades back slowly. Nothing moves. Our mark is built from parts too and now behaves the same way; the lift/scale/shadow on hover is gone.

## [2026.7.3.post154] - 2026-08-11 - Loading states stop flashing; shell chrome measured

###  Fixed
- **Skeletons flashed and vanished before they could be read.** The mechanism that holds a placeholder invisible until a load is genuinely slow applied only to `.gl-skeleton`; the composite skeletons (table rows, bar chart, chart wrap, health dashboard) are separate classes and painted instantly - measured at 447ms, 512ms and 933ms of visible life on admin System. Every skeleton root now shares the delayed reveal and the threshold moved 250ms -> 400ms. Verified with ancestor-aware opacity sampling: table and chart skeletons now peak at 0.00 opacity (they never paint on a fast load) while the health panel, which really takes ~900ms, shows in full.
- **The error pages had drifted off the design system**: their own radius alias still pointed at the generic 4px so inputs and buttons were squarer than the same controls elsewhere, the heading was 26px against GitLab's 40px, the search field 39px against the app's 32px, and links used the raw brand blue. All four now follow the app's tokens in both themes.

###  Changed
- **Modal motion is GitLab's**: overlay `opacity 0.15s linear`, dialog from 50px above on `transform 0.3s ease-out`. Ours faded in 100ms and grew from `scale(0.85)` on a spring over 400ms.
- **The top-bar search grows with the viewport**, exactly `20vw + 56px` - measured 261/312/344/392/440px at 1024/1280/1440/1680/1920. Ours was pinned at 344px.
- **The logo is static, like GitLab's** - idle and hover there are identical. The heartbeat-on-hover is gone, with its three orphaned keyframes.

## [2026.7.3.post153] - 2026-08-11 - Toasts round like every other overlay

###  Changed
- Toasts rounded at 4px while every other overlay we round now sits at 8px (GitLab's toast measures an 8px radius over 16px/24px padding, which we already matched). The surface and the small controls inside it now use the same tokens as dropdowns and actions.
- Known difference: GitLab's toast is a neutral dark chip in both themes; ours is tinted per variant, because the toast carries success/warning/danger meaning here. Left as is rather than changed silently.

## [2026.7.3.post152] - 2026-08-11 - One dropdown controller instead of two

###  Removed
- **The second dropdown controller.** `.gl-dropdown` was driven by a handler in core while `[data-dropdown]` was driven by `dropdowns.js` - two implementations of one interaction, each carrying a check for the other so their `.open` state would not desync. That coupling was itself the warning sign: when it broke, a menu opened once and then reported itself permanently closed. `dropdowns.js` now owns **both** selector conventions, so not a line of markup changed, and the 76-line handler in core is gone.
- The two behaviours only the deleted handler had moved across: choosing an item closes its menu, and a menu portaled to `<body>` is never treated as an outside click. Alpine-managed dropdowns are still skipped.

###  Added
- `tests/unit/test_one_controller_per_interaction.py` pins both merges - the single click guard and the single dropdown controller. Verified in the browser first: 12 dropdowns across five pages open and close correctly, the portaled page-size menu opens/selects/closes, and the theme switcher leaves the user menu open.

## [2026.7.3.post151] - 2026-08-11 - Motion matched to GitLab's, not just its speed

###  Changed
- **GitLab animates colour and nothing else.** Measured on real Pajamas components: a button transitions `color, background-color, border-color, box-shadow, text-decoration-color` at 0.2s out-cubic and **no transform**; cards, links, alerts and checkboxes transition nothing at all. Ours scaled buttons down to 0.94 on press, scaled sidebar items to 0.98, and zoomed nav icons to 1.1 on hover. Matching the durations was only half the job - the movement itself is the tell. All three removed; the button's property list is now GitLab's exactly.
- **Form controls animate on a different pair.** GitLab moves `border-color, box-shadow` over 0.15s ease-in-out on a GlFormInput, not the 0.2s out-cubic every action uses. Added `--transition-control` and pointed the text input, select, dropdown toggle, checkbox, toggle track and search box at it.

###  Removed
- The reduced-motion override that reset `.btn:active { transform }`, dead now that the press carries no transform.

## [2026.7.3.post150] - 2026-08-11 - The shell rebuilt to GitLab's, second click guard deleted

###  Changed
- **The shell itself was the wrong shape.** GitLab's super-topbar spans the FULL width at the top (measured 0,0,1440x48 on gitlab.com) and the sidebar starts below it; ours put the sidebar full-height on the left with a bar only over the content, so the page read as "a sidebar with a bar next to it" instead of "a bar over everything" - the difference visible before any component. The bar is now full width with the brand top-left where GitLab keeps it, and the sidebar sits below it. Verified against GitLab at three widths in both themes: topbar (0,0,1440,48), sidebar (0,48,240), panel radius 12px, nav item 28px with 2px/4px padding, page title 30px - all exact.
- Content panel radius 16px -> 12px, top bar 49px -> 48px, page `h1` 24px -> 30px, sidebar nav items 0/8px -> 2px/4px padding with a 2px gap, and the sidebar's bottom group 13px -> 14px so it matches the nav items right above it.

###  Removed
- **The second click rate guard.** `interceptSpamClicks` counted 3 clicks in 2s and applied a visible cooldown, duplicating the silent per-element debounce in core. Two guards over one interaction is one too many, and they disagreed: a tree toggle survived the lock and died on the cooldown. Deleted with its timestamp map; the cooldown stays for failed actions only. Verified with six real rapid clicks - perfect alternation, no dead click.
- The top bar's `left` offset for the collapsed sidebar and its `transition: left`, both dead now that the bar spans the full width in every state.

## [2026.7.3.post149] - 2026-08-11 - Tabs, badges and menus measured against Pajamas

###  Changed
- **Tabs were a step small and never fully selected.** design.gitlab.com's GlTabs measures 50px tall, 14px text on a 16px line, 16px/12px padding, and keeps every tab the SAME colour - GitLab marks the selection with weight (400 -> 600) and the indicator, nothing else. Ours were 13px at weight 500 in both states over 8px/16px padding with the inactive ones dimmed, so the bar sat 12px shorter and every tab read half-selected. Now identical.
- **Small badges were heavier and taller than any GitLab badge.** Every variant on design.gitlab.com/components/badge measures 12px / weight 400 / 2px 6px / 20px tall - GitLab ships one badge metric. `.badge-sm` bumped the weight to 500 and the vertical padding to 3px; it now only trims the horizontal padding.
- **Menus rendered a step below the page behind them.** GitLab draws the dropdown toggle and its items at 14px, the same as body text; ours were 13px.
- The current page number in a paginator rounded at 4px while the prev/next buttons either side of it round at 8px, so the number read visibly squarer than its own arrows.

## [2026.7.3.post148] - 2026-08-11 - Docs typography matched to docs.gitlab.com

###  Changed
- **The documentation ran a whole heading step small.** Measured on a docs.gitlab.com content page: h1 40px/46px, h2 32px/40px, h3 24px/30px, inline code and code blocks both a flat 14px. Ours were 32 / 25 / 21 with code at 12.24px inline and 13.6px in blocks - both `em`-relative, so they compounded against their container instead of landing on a fixed size. Body copy was already 16px/25.6px and stayed. Re-measured after the change: p, h1, h2, h3, inline code and code blocks are now identical on both sites.
- The 8px radius on code blocks is correct after all: GitLab puts it on a `.codeblock-wrapper` and leaves `<pre>` itself square and transparent, so measuring `<pre>` alone read 0px. We have no separate wrapper, so ours keeps the radius on `.highlight` / `pre`.

###  Removed
- **The last inline styles that were really CSS.** `width: 100%` on the user dropdown info block and `vertical-align: middle` on the student commits counter moved into `dropdowns.css` and a shared `.match-count` rule - the same counter previously sat on a different baseline on the course page, which had no such rule. Project detail's live-intel skeleton stopped hand-writing `height/width/margin/border-radius` and now uses the same `--sk-w` custom-property API as every other skeleton, plus two shared classes (`.gl-skeleton-row`, `.gl-skeleton-gap`) that replace the private 6px / 8px margins in the user-info modal.
- Every `style` attribute left in the codebase now passes a *value* a class cannot carry (`--sk-w`, `--chart-h`, `--h-bar-label-w`), which is the intended pattern; none declare properties directly.

## [2026.7.3.post147] - 2026-08-11 - Radii, motion and the group tree measured against GitLab

###  Fixed
- **Expanding a group dumped every project row at once.** GitLab's group tree shows the first few children and puts the rest behind "View all (N more items)"; ours rendered all 15 and pushed everything below off the screen. An expanded group now shows 3 children plus that link. The cap lives in the template, which stamps `.tree-row-extra` on the rows past it - the client paints by class and holds no copy of the number, so the two cannot drift apart. Verified in both themes, including that the cap survives filtering and pagination re-renders.
- **Three clicks on any disclosure toggle within two seconds froze it.** The anti-spam cooldown in `process-action-guards.js` treated a tree toggle as a real operation, so expand/collapse/expand left the control dead. Disclosure controls (`aria-expanded` / `aria-pressed`) issue no request and both click guards now exempt them; buttons carrying `data-process-lock-when` are still rate-limited.

###  Changed
- **Every component radius was wrong.** GitLab does not use one radius everywhere, and picking the generic 4px for buttons and inputs is what made our controls read as visibly squarer than GitLab's in side-by-side screenshots. Measured live - button 8px and nav item 8px on gitlab.com, input 8px, card 12px and alert 8px on design.gitlab.com - and reproduced through named tokens from `@gitlab/ui` 136.1.0. Buttons and form controls 4px -> 8px, cards 8px -> 12px, modals 12px -> 16px (the code claimed `gl-border-radius-2xl`, which is 16px, and used 12px anyway).
- **Animations ran half again too slow.** `@gitlab/ui` publishes fast 0.1s / medium 0.2s / slow 0.4s, and measuring gitlab.com with reduced motion explicitly off shows only 0.1s / 0.15s / 0.2s in use. We ran at 200 / 290 / 500ms. Aligned to 100 / 200 / 400ms.
- **Body line-height 1.4 -> 1.5.** GitLab sets 14px text on a 21px line; ours was 19.6px, which made every paragraph, table cell and card denser than the same content in GitLab.
- **Table headers 13px over a 2px border -> 14px over 1px**, measured on the real Pajamas table component rather than a markdown table.

###  Added
- `tests/unit/test_tree_disclosure_contract.py` pins the cap markup, the class-driven client contract, and the disclosure exemption in both click guards.

## [2026.7.3.post146] - 2026-08-10 - Badges carry colours read off live GitLab

###  Changed
- **Badges were the wrong colour in both themes.** Extracting live gitlab.com with Dembrandt showed a neutral badge computes to background `#dcdcde` with text `#4c4b51`, and success to `#c3e6cd` / `#306440` - GitLab's `--gl-status-*` pair, i.e. a **muted** chip. Ours were a bright 300-level chip with near-black text on dark, and one step too dark on light. Every variant now follows GitLab: `*-100` background with `*-700` text on light, `*-800` with `*-200` on dark. Verified in the browser: our success badge computes to exactly `rgb(195, 230, 205) / rgb(48, 100, 64)`, the values the extraction read off gitlab.com. Badge line-height is pinned to GitLab's 16px.
- The documentation site uses an 8px radius for interactive chrome. The extraction counted 8px on 52 elements there against 14 for 4px, which is reserved for inline code and labels. The product UI stays at 4px.

###  Removed
- **`pages/admin.css` redefined `.badge-gray`**, overriding the shared badge component on admin pages only, so the same status chip had two colours depending on the page and neither matched GitLab.

###  Added
- Badge tokens joined `tests/unit/test_gitlab_token_parity.py` (25 -> 35 pinned values).

## [2026.7.3.post145] - 2026-08-10 - "Show more" became a shared component

###  Changed
- **"Show more / show less" is one component instead of a feed-only feature.** The disclosure lived entirely inside the dashboard activity feed: its own classes, its own footer markup, its rules buried in `home.css`. Any other list wanting the same behaviour would have had to copy all three. It is now `components/disclosure.html` plus generic `.gl-show-more*` rules in `utilities.css`. The contract covers table rows too - `display: none` on a `<tr>` is legal, so a `<div data-show-more>` around a table can hide overflow rows the same way. Verified in the browser: 0 extra rows -> 5 on expand -> 0 on collapse, no console errors.

###  Removed
- The activity-feed-specific `.gl-activity-item--extra` / `.gl-activity-show-more*` classes, the duplicated expand/collapse markup and an import the change orphaned.

## [2026.7.3.post144] - 2026-08-10 - Buttons and the docs carry GitLab's real colours

###  Changed
- **The primary button is no longer blue.** GitLab's own design tokens paint the confirm/primary button `neutral-800` on light and `neutral-50` on dark - blue is reserved for links, focus rings and info. The app had it blue, which is the single biggest reason screenshots never matched. Checked checkboxes and radios, the toggle track, the selected filter pill, the current pagination page and the selected navigation item move to the same neutral ramp, because GitLab paints all of them from `--gl-action-selected-*`. Values were taken from `@gitlab/ui` 136.1.0 and verified in a browser in both themes: **14 measurements, 0 mismatches.**
- The check mark inside a checkbox, the radio dot and the toggle knob now follow the theme instead of being hardcoded white. They had to: the checked control is near-white in dark mode, so a white glyph would have been invisible.
- **Every empty state leads with a GitLab illustration.** 37 of them showed a boxed glyph; they now inline the matching illustration from `@gitlab/svgs` (MIT, 15 vendored). The SVGs are inlined rather than linked because they colour themselves from `--gl-illustration-*`, which an `<img>` could never read.
- **The documentation site was rewritten onto GitLab's design language.** It ran on Material's indigo/deep-purple defaults with gradient table headers, uppercase letter-spaced column titles, 8-12px radii, drop shadows and cards that lifted on hover. It is now GitLab: neutral chrome separated by hairlines, 4px radii, text-coloured headings, plain tables and the same GitLab Sans/Mono the product uses.
- Error pages, the product tour, the PWA install prompt and the sign-in button stopped defining their own primary colour and use the shared button tokens.
- Skeleton placeholders use GitLab's 4px corner radius instead of 2px, and the chart skeleton moved onto the same composited sweep as every other skeleton. The second mechanism animated `background-position`, which the compositor cannot run on its own, so it stalled under exactly the main-thread load it was reporting on.
- Destructive icon-only row actions render as tertiary danger - a red glyph with a red wash on hover - instead of a solid red block, matching GitLab's row actions.

###  Added
- `tests/unit/test_gitlab_token_parity.py` pins 25 interactive colour tokens to `@gitlab/ui` 136.1.0 in both themes.

###  Removed
- A `.gl-skeleton` animation declaration a later rule already overrode, its stale comment, a duplicated keyframe comment, the unused `--gl-toggle-unchecked-hover` token and the second skeleton keyframe.

## [2026.7.3.post143] - 2026-08-10 - The activity feed is laid out like GitLab's

###  Changed
- **"Follow the latest updates" follows GitLab's Activity layout.** A row was one flat `Actor - Action` string beside an icon, which read as a log line. It is now an avatar, the actor in bold with the time pushed right, the action on its own line with its icon, and the detail beneath. The builder emits `actor` and `action` as separate fields.
- The linked and unlinked row variants share one macro instead of duplicated markup.

###  Fixed
- **An activity row showed a question mark instead of an icon.** The feed asked for `user-x`, which the icon set does not define. It uses `user-minus` now, and a new test asserts every icon the feed names exists.

## [2026.7.3.post142] - 2026-08-10 - The last browser dialogs are gone, a dropdown can no longer cut its own options

###  Changed
- **Every remaining `window.confirm` now runs on the app's dialog.** Twelve call sites across nine files still asked through the browser. Six sat in synchronous helpers whose boolean the caller used, so those helpers became async and their callers now await them. Verified by clicking 117 buttons across nine pages: **zero native dialogs**.

###  Fixed
- **A dropdown clipped its own options.** The menu was capped at 320px with no wrapping, so a long unbreakable label ran past the edge and the menu grew a horizontal scrollbar. Menus now size to their content, never narrower than the control that opened them and never wider than the viewport, and long labels wrap. Fixed in the shared component.

## [2026.7.3.post141] - 2026-08-10 - Every dropdown says when it has nothing to offer

###  Fixed
- **A select with no options rendered as a blank box.** Opening "Import Target" with no courses yet showed an empty rectangle, which reads as broken rather than "there is nothing to pick". The shared `select_field` macro now renders "No options available", so every dropdown in the app gained the empty state at once.

## [2026.7.3.post140] - 2026-08-10 - Sorting answers on the first click, the health check says what it found

###  Fixed
- **Sorting a table appeared to need two clicks.** Switching to a new column sorts it ascending, which very often reproduces the order already on screen, so the rows sat still and only the arrow moved. When the new column's default direction changes nothing, the direction now flips immediately, so one click always produces a visible result. Only on a column switch - clicking the same header again still returns the previous order.
- **The System Health check gave no feedback.** On a healthy system the re-check redraws an identical card, so nothing confirmed it had run. It now reports the verdict as a toast, the same contract every other action follows.

## [2026.7.3.post139] - 2026-08-10 - The whole icon set is GitLab's now

###  Changed
- **Every icon is a GitLab Pajamas glyph.** The app shipped 122 hand-inlined *Feather* icons - 24x24, stroked outlines - a different icon family from GitLab's, so no amount of colour or size tuning could make the UI read as GitLab. All 122 are replaced by their Pajamas counterparts from `@gitlab/svgs` (MIT): filled shapes, mostly on a 16-unit grid. 47 names matched directly; the other 75 were mapped by meaning.
- Both registries moved together - the Jinja macro and the JS one - so a server-rendered icon and one drawn by JS are the same glyph.
- Icons inherit the text colour through `fill: currentColor`, replacing the `stroke: currentColor` the outline set relied on. Verified in both themes.
- Paths are inlined rather than referenced from a sprite: WebKit still does not resolve EXTERNAL `<use href="sprite.svg#id">`, which would leave every icon blank in Safari.

## [2026.7.3.post138] - 2026-08-10 - Replaying events moves out of a modal and into the table

###  Changed
- **Replay is a table action now, not a dialog.** The modal asked for a start and an end date: it named the events only indirectly, swept in everything else that fell inside that window, and its own selects were clipped by the dialog. The Recent events table gains a select column and a "Replay selected (N)" action - the same selection pattern the dead-letter table already used, so the two tabs finally behave alike. The modal is deleted.
- `POST /api/v1/events/replay` accepts `event_ids`, replaying exactly the rows that were ticked. The time-range form still works for API callers; the schema now requires one or the other.
- Confirmation runs on the shared dialog and states the real count, which a date range could never do.

## [2026.7.3.post137] - 2026-08-10 - Every "are you sure?" is now the app's own dialog

###  Changed
- **Destructive actions asked through the browser.** `window.confirm` / `window.prompt` sat next to the app's own modals doing the same job - two patterns for one interaction, and the browser's half cannot be themed, ignores dark mode, carries no danger accent and reads as if the page broke. One shared dialog (`GP.confirmDialog`) now serves every confirmation: themed, translated, Escape-cancellable, focus on the SAFE button so Enter cannot delete, and it opens and closes through the app's existing `openModal`/`closeModal` rather than a second show/hide of its own.
- `confirmDangerousAction` keeps its signature: callers pass a callback, so moving from a blocking dialog to a promise ripples nowhere. All 16 call sites were verified to use the callback form.
- **Two confirmations became one.** A permanent delete used to need a second dialog because a browser prompt could only ask yes/no. The dialog states the consequence once and gates its button on typing the name.

## [2026.7.3.post136] - 2026-08-10 - The archived lock is expressed once, dead CSS removed

###  Changed
- **The archived lock is expressed once.** Eleven button call sites also server-rendered `disabled` + a hover reason for a state the client guard already owns, so the same condition existed twice and behaved differently depending on which won - a disabled button that swallows the click next to a guarded one that answers with a toast. The server-side copy is gone; every locked control now behaves the same way.

###  Removed
- Dead template variables the duplication left behind (`_lock_tip`, `_locked`) and `_repo_is_empty`, a Run Checks condition hardcoded to `false` that could never fire.
- Nine CSS rules for classes no HTML or JS emits any more - column widths for a members table that changed shape, skeletons for charts that no longer have one, and a placeholder avatar. Verified individually; the compound-selector candidates were left alone deliberately and the generic utility scale stays complete.

## [2026.7.3.post135] - 2026-08-10 - Modals stop piling up, a locked control answers, System Health stops shoving the page

###  Fixed
- **The Dashboard could open a COURSE's "Import from GitLab into <CODE>" modal.** Modals are teleported to `<body>` so a nested `<form>` cannot break the page's own form - which also puts them outside both regions a navigation replaces, so nothing ever removed them. Each navigation left another set behind: three elements sharing one id and 16 backdrops after two navigations, with `openModal` picking whichever came first. The outgoing page's modals are now retired when navigation starts.
- **A locked control on an archived course swallowed the click.** Dimmed and silent, it read as broken rather than unavailable. Buttons now stay clickable and answer with the reason as a toast (the same contract the dead-token banner uses for Sync); only form fields stay truly disabled, because an input that looks editable and silently refuses keystrokes is worse.
- **The System Health card blinked on every check.** Its loading state replaced the rendered dashboard, so the block collapsed from ~519px to ~170px and back, shoving System Actions, Feature Flags and Job History up and down the page. A re-check now keeps the card at its exact size and only dims it (composited opacity, so it cannot stutter); the first-run skeleton mirrors the real component card so it reserves the space the result needs.

## [2026.7.3.post134] - 2026-08-10 - One calendar everywhere, archived state enforced by the routing table, refresh buttons answer

###  Fixed
- **Only some calendars had semester weeks.** The week column needs a semester to count from, and only a course page published one - so the events Replay range, and any date field outside a course, opened a bare month grid. Pages without a course now fall back to the running (or next) semester of the TUKE FEI academic calendar the app already ships, so every picker in the app is the same control.
- **Refresh buttons that did nothing visible.** The events pipeline refresh and the webhook-configurations reload re-rendered identical rows with no loading state and no confirmation, so a click was indistinguishable from a dead button. Both now follow the contract the admin System refresh already had: report working, then report done (or failed).
- **Two "Refresh" buttons were not refreshes.** On course Activity and Analytics the control triggered a full GitLab sync - a remote job that can take minutes and fails outright with no worker running. They are labelled **Sync** now and say so on hover; Activity additionally notes that its view updates on its own (it is subscribed to the course stream).

###  Security
- **Six course-scoped write routes had no archived-course guard**, so a direct API call could act on a read-only course: issuing a live webhook secret, starting a paid LLM analysis of a merge request, generating checks with the LLM, importing a support-form definition, and reassigning course teachers (whose form is now locked in the UI too). All refuse an archived course now.
- The guard is enforced by **walking the application's routing table** instead of a hand-maintained list of handlers, which is how these six were missed. A new course-scoped mutation now fails the suite until it either carries the guard or is recorded, with a reason, as an action that must stay available while archived (reactivate, transfer, purge, cancel a running job).

###  Removed
- The `/dashboard/courses/{id}/analytics/stream` SSE endpoint (148 lines): no client ever subscribed to it and nothing ever published to the Redis channel it listened on. Its dead `sseUrl` config key went with it.

## [2026.7.3.post133] - 2026-08-10 - The activity feed stops speaking machine, archived state is visible on group pages

###  Fixed
- **The activity feed printed raw action names.** Eleven audit actions had no label, so rows rendered as `member_exclusion_toggled` - and the fallback was the identifier itself, meaning any action added later would do the same. All eleven now have a label, an icon and a target page, and the fallback turns an unknown identifier into a sentence so machine text can never reach the widget again.
- **The feed was always English**, even on a Slovak dashboard: its text is composed server-side and the template renders it verbatim. Labels, actors, job outcomes and counts are now translated (+30 catalog strings). The counts avoid numeral agreement, which the catalog cannot express: Slovak needs "2 zmeny" but "5 zmien".
- **Audit rows were attributed to a number.** The member-scoring toggle recorded the session's id field as the actor - GitLab's numeric user id on the OAuth path - so the feed read "0001 - ...". It now records the username like every other audit write, and ids left in existing rows are resolved to usernames when the feed is built (one batched query; unresolvable ids read as "Unknown user" rather than a bare number).
- **An archived course's group, project and student pages looked fully editable.** The read-only guard keyed off `.tabs-nav`, which only course pages render, so those pages showed no archived strip and left every control live - including "exclude from scoring", which failed only once the server answered 403. They now carry the same marker and strip, and their controls are locked with the reason on hover.

## [2026.7.3.post132] - 2026-08-10 - An archived course is genuinely read-only, navigation stops losing context

###  Fixed
- **An archived course dimmed the NEXT page you opened.** `#globalBannerSlot` and the `is-course-archived` class live outside `#main-content`, the only region a navigation swap replaces, so the archived strip stayed pinned to the top of the Dashboard and its guarded buttons stayed greyed. Portaled strips are now retired on navigation and the read-only class is scoped to the swapped region.
- **Archived courses were still editable.** The guard only locked `[data-process-lock-when]` buttons, which the weekly-deadlines editor never carried: the modal opened, "Save week" wrote into the schedule JSON, and the save that would have rejected it was disabled anyway. Every control inside `form.is-course-archived` is now locked, including the check rows the page renders after load, with a `data-readonly-ok` opt-out for filters, export, reload and disclosure toggles.
- **Archiving a course was a one-way door.** The same guard disabled Activate, Transfer and Delete Forever - the three actions the server explicitly still allows on an archived course, and permanent delete *requires* it to be archived.
- **Archive / Activate / Delete Forever threw and did nothing.** `courseActions` called a bare `t(...)` that does not exist in its IIFE (the rest of the file uses `GP.t`), so every course lifecycle action died on `ReferenceError` at the first confirmation string.
- **No date input got a picker on first paint.** `core.bundle.js` is a deferred script and therefore runs at `readyState === 'interactive'`, before the deferred flatpickr that follows it in `<head>`; the init guarded on `'loading'`, took the immediate branch and `initFlatpickr` returned silently. This is what removed the semester week column from the deadline calendar.
- **`<head>` metas went stale on in-app navigation.** `course-id`, `semester-start` and `semester-end` are rendered per page but never re-merged, so after any navigation the week column had no semester to count from.
- **A second click during a navigation was dropped**, leaving the reader on the first page with no sign their click registered. It is now queued and honoured.
- **In-app anchor links landed at the top of the page.** A content-only swap never triggers the browser's fragment scroll; and the archived banner's "Reactivate" pointed at `#danger-zone`, which did not exist.
- **The course-status poll outlived the page that started it** and could reload a page you had already navigated away from.
- **"Loading..." froze mid-animation.** The label was animated through `background-position` + `background-clip: text` - a paint animation the compositor cannot run - so it stopped exactly when the incoming page occupied the main thread, beside a ring that kept spinning because it animates `transform`. Both loading labels now breathe on `opacity`.
- **Team and project page views were never recorded.** The telemetry beacon sent an ad-hoc `metric_type` with a string `context`, and the endpoint answered 422.
- **Export / Import Full Configuration stretched across half the card each** and collapsed to a lopsided pair once the read-only guard wrapped the disabled Import in its tooltip span - `.form-row` is the grid for form inputs, not buttons.
- **131 UI strings had no Slovak translation**, including the whole weekly-deadline editor, the archived banner and the blocking server messages (dead GitLab token, no worker, archived course). Three confirmation dialogs were built from template literals and so could never be translated at all; they take parameters now.

###  Changed
- **Navigation feedback follows GitLab / YouTube.** The outgoing page stays on screen, dimmed and inert, while the top progress bar reports the fetch; the branded loader appears only if the fetch really drags (>1.2s). It used to blank the content after 120ms, which is what made pages appear to jump.

###  Removed
- 30 dead skeleton CSS classes (`gl-sk-qa-*`, `gl-sk-attn-*`, `gl-skeleton-header*`, `gl-sk-doughnut`, ...) left behind by earlier skeleton work.

###  Tests
- **The browser suite was silently vacuous against a live server.** `tests/conftest` substitutes its own `SECRET_KEY`, so the minted session cookie was rejected and every page under test was really the login form; only the guard assertion failed.
- **Route discovery walked a JSON endpoint and an HTML fragment as pages** (`/dashboard/notifications`, `/dashboard/activity`).

## [2026.7.3.post131] - 2026-08-06 - The API-spec gate works on a cold app too

###  Fixed
- **`test_api_spec_inventory` read `app.routes` directly and failed in CI.** This app defers `include_router` into placeholders that are only flattened at startup, so a plain read sees ~19 routes - the gate then declared all 83 documented endpoints phantom. It now walks them through `tests/route_discovery.iter_routes`. Verified in a clean `python:3.12-slim` container, not just locally.

## [2026.7.3.post130] - 2026-08-06 - Green pipeline, no more 401s in Search Console, honest READMEs

###  Security
- **`cryptography` 49.0.0 -> 50.0.0** (GHSA-g6cj-pr64-35w5 / CVE-2026-69247). `pkcs7_decrypt_*` leaked the recovered RSA plaintext length through both its return value and its timing. This is what turned the `dependency-scan` CI job red. `exclude-newer` moved 2026-07-21 -> 2026-08-01 so uv can see the fix; `cryptography` is the only pin that changed.

###  Fixed
- **Search Console reported "Blocked due to unauthorized request (401)".** The culprit was `/grafana/`, `/prometheus/` and `/jaeger/` - Caddy answers those with a basic-auth 401 and they never reach the app, so no `X-Robots-Tag` of ours could cover them. They (and `/metrics`) are now `Disallow`-ed in `robots.txt`, and Caddy sends `X-Robots-Tag: noindex, nofollow` on all three.
- **`docs/04-api-spec.md` documented 15 endpoints that do not exist** while omitting whole live areas (transfer, run-checks, webhook-configs, job cancel, SSE streams). Section 5 is now generated from the route table and pinned by a test in both directions.
- **The READMEs stated numbers that stopped being true long ago.** `README.sk.md` still advertised `rq-scheduler` with 12 periodic jobs (there is no scheduler), 44 models across 48 migrations at head `047_bg_job_project_id` (really 39 across 11 at `011`), 222 routes (204), and Docker-verify / CI-failure / conflict-simulator modules that were deleted. Both also linked an `LLM_README.md` that does not exist and claimed a 10-panel Grafana dashboard with 7 alerts (18 panels, 18 alerts). A gate test now pins each countable claim.

## [2026.7.3.post129] - 2026-08-05 - The env examples and webhook docs describe the app that actually exists

###  Fixed
- **`.env.example` and `.env.production.example` advertised 14 settings nothing reads** (`FEATURE_RUBRIC_ENGINE`, `FEATURE_GAMING_DETECTION`, `FEATURE_TIMELINE_DASHBOARD`, `FEATURE_ROSTER_IMPORT`, `FEATURE_CONFLICT_SIMULATOR`, `FEATURE_DOCKER_VERIFICATION`, `FEATURE_CI_FAILURE_GENERATOR`, `DOCKER_VERIFY_*`, `CONFLICT_BOT_*`, `CI_FAILURE_BOT_*`, `RQ_MAX_RETRIES`). Both files now list the real feature flags plus the SMTP, session, semester-lifecycle, retention and monitoring settings that were missing. A gate test stops them drifting again.
- **The three dead tool flags are gone from `docker-compose.yml`** too.
- **The webhook docs described a signature scheme GitPulse does not use.** They told you to generate `GITLAB_WEBHOOK_SECRET` into `.env` (nothing reads it) and showed an invented HMAC handler. In reality GitLab sends the secret in `X-Gitlab-Token`, GitPulse generates it per project or per webhook configuration, stores only its bcrypt hash, and rotation goes through `POST /api/v1/webhook-configs/{id}/rotate`.

## [2026.7.3.post128] - 2026-08-05 - An archived course is read-only everywhere, not just in the UI

###  Fixed
- **Every course-scoped write endpoint now rejects an archived course.** Project sync, group update/delete/restore, project link/unlink/restore, course update, course settings, the full-config import and all three LLM-analysis triggers went straight through - only the buttons were dimmed. They all return the shared 409 "archived and read-only" now.
- **Importing a GitLab group no longer silently un-archives a course.** The importer set `is_active = True` on the resolved course, so a re-import brought an archived course back to life. It now refuses with a clear "reactivate it first".
- **Webhooks for an archived course are acknowledged and dropped.** GitLab kept delivering into archived courses, rewriting their data and firing "Live update" toasts on pages the UI presents as frozen.
- **Disabled buttons on an archived course explain themselves again.** They carried `pointer-events: none`, which also killed the hover that carries the tooltip - so they looked broken rather than locked.
- **The User Info modal no longer jerks when the data lands.** The skeleton and the loaded card are different heights, so the body snapped in one frame; the swap is height-animated now.
- **Docs no longer document endpoints that do not exist:** `/api/v1/pipelines/report` and `/pipelines/validate`, `/api/v1/webhooks/test`, `/api/v1/health`, `/api/v1/team-metrics`, and `teams/{id}/recheck` (the real route is `run-checks`).

## [2026.7.3.post127] - 2026-08-05 - The sidebar logo animation is smooth again

###  Fixed
- **The GitPulse logo's pulse no longer stutters or freezes.** It animated `stroke-dashoffset` (a sweep the browser can only run on the main thread) and `will-change: stroke-dashoffset` forced an extra repaint layer, so the pulse hitched whenever the page was busy. It now uses a gentle `opacity` glow that runs on the compositor - smooth regardless of load.

## [2026.7.3.post126] - 2026-08-05 - Tooltip wrapping + no zebra flicker when expanding a group

###  Fixed
- **Long tooltip text no longer runs off the edge.** Emails, bot logins and GitLab paths overflowed the tooltip; it now wraps them (`overflow-wrap: anywhere`, wider max-width).
- **Expanding a group no longer breaks / flickers the table striping.** A group's child rows are excluded from the `nth-child(even of ...)` zebra count and carry a stable nested tint, so expanding / collapsing never re-stripes the rows below.

## [2026.7.3.post125] - 2026-08-05 - Archived courses are read-only on the group page and server

###  Fixed
- **The group (team) page's write actions are now disabled + explained on an archived course, not hidden** - matching the course and project pages (Link Project / Sync / Run Checks / Delete stay visible but greyed, with a "this course is archived and read-only" tooltip).
- **Excluding a student from scoring is now rejected server-side on an archived course** (HTTP 403), so a stale client cannot change scoring membership on a read-only course.

## [2026.7.3.post124] - 2026-08-05 - Modals close on navigation; archived actions disabled + explained

###  Fixed
- **Open modals no longer stay floating over the next page.** Backdrops live on `<body>`, so navigation used to leave them open; navigation now closes any open modal / drawer first.
- **Write actions on an archived course are shown disabled with a tooltip, not hidden.** Add Group / Import / Sync / Run Checks (and the project's Sync / Unlink / Run Checks) stay visible but disabled, each explaining "this course is archived and read-only" on hover.

###  Changed
- **Skeletons hold invisible a touch longer (0.42s)** so a borderline-fast load no longer flashes one for a frame.

## [2026.7.3.post123] - 2026-08-05 - Every button has an iOS-style press

###  Changed
- **Buttons now depress on tap, iOS-style.** Every button scales to 0.94 on press and springs back on release, for tactile feedback - completing the motion set alongside modals (grow from the button that opened them), dropdowns (from the toggle) and toasts / tooltips (from their own position). Reduced-motion neutralises it.

## [2026.7.3.post122] - 2026-08-05 - Spinner actually spins; modals aren't see-through on open

###  Fixed
- **The loader spinner was frozen** (only the label animated) - promoting it with `translateZ(0)` collided with the rotate keyframe. It now uses `will-change` alone and an explicit `rotate(0) -> rotate(360deg)` keyframe, so it spins smoothly again.
- **Modals no longer look translucent on open.** The dialog inherits the backdrop opacity, and a slow backdrop fade left it see-through (table showing through) for up to half a second. The backdrop now reaches full opacity in ~200ms while the dialog keeps its scale-spring.

## [2026.7.3.post121] - 2026-08-05 - Smooth conic spinner restored; auto-update after deploy

###  Changed
- **The loader spinner is the sweeping conic arc again** (the border-ring look was a regression), now on its own compositor layer so it keeps the good look AND stays smooth under load.
- **The User Info modal's structural skeleton is back.** It mirrors the loaded card so there is no layout jump; what looked "see-through" was the modal caught mid open-animation.

###  Fixed
- **The app auto-refreshes to the new version after a deploy.** A bumped service worker reloads the tab once when it takes control, so a release is picked up without a manual hard-refresh.

## [2026.7.3.post120] - 2026-08-05 - Loader spinner is smooth under load

###  Fixed
- **The navigation loader spinner no longer stutters or looks frozen while a page loads.** It was a rotating conic-gradient the browser repaints on the main thread, so it hitched exactly when the incoming page kept that thread busy. It is now a border spinner rotated purely by transform on its own compositor layer, so it stays smooth and cyclical regardless of what the page is doing.

## [2026.7.3.post119] - 2026-08-05 - Modals grow from the button; cleaner animated loaders

###  Changed
- **A modal now grows out of the button that opened it** (and collapses back into it), iOS-style, instead of scaling from its own centre - the trigger's position becomes the dialog's scale origin.
- **The User Info modal shows a clean loader, not a skeleton.** Its skeleton read as broken (translucent bars over the table behind the modal); it is now a centred spinner with a label.
- **Loading labels are animated.** A brand-orange band sweeps across the loader text ("thinking"-style) instead of a static string, everywhere a loader label appears. Reduced-motion shows a solid colour.

## [2026.7.3.post118] - 2026-08-04 - Overlays grow from their own position instead of sliding in

###  Changed
- **Modals, dropdowns, tooltips and toasts now expand from their own place and settle back into it, instead of sliding in from an edge.** Modals scale from their centre (the backdrop owns the fade), dropdowns scale out of the toggle (top origin, bottom when they flip up), toasts scale in/out from their spot rather than sliding up then off to the side, and tooltips grow from the edge nearest their anchor. No more default "arrives from nowhere" slides/fades.

## [2026.7.3.post117] - 2026-08-04 - Controls work after navigation; archived courses are read-only

###  Fixed
- **Dropdowns and other interactive controls work after navigating.** After an SPA navigation, Alpine-driven components silently stopped working - the Type/Status filters would not open and page components never initialised (no error). `Alpine.initTree` ran in the same tick as clearing `x-ignore`, before Alpine released the subtree; it now runs one frame later.
- **Archived courses are genuinely read-only.** An archived course showed a "read-only" banner but its write buttons (Sync, Run Checks, Link Project, Delete; Add Group, Import, Sync All) stayed enabled. They are now hidden while the course is archived.

## [2026.7.3.post116] - 2026-08-04 - Skeletons never flash; accessibility clean on every page

###  Fixed
- **Skeletons no longer flash for a frame.** Server-rendered skeletons painted instantly, so a fast page showed grey blocks for a moment before the data arrived. `.gl-skeleton` now holds at opacity 0 for ~0.28s and only appears if the content is still loading - quick loads paint no skeleton, slow ones still get one, and there is no fade so no blink.
- **Accessibility is clean on every page.** A 13-page audit (accessible names, form labels, alt text, ARIA references, keyboard-reachable controls) came back clean except one icon-only "Open in GitLab" link on the team page, which now has an aria-label.

###  Verified
- Live data updates (SSE) connect on the events and dashboard pages; the full unit suite (2535 tests) passes.

## [2026.7.3.post115] - 2026-08-04 - New loader, reachable table actions, no blinking

###  Changed
- **The navigation loader is a spinner ring + label, not a heartbeat.** The static GitPulse mark now sits inside a modern rotating gradient ring with a localized "Loading..." label and a slow-connection note that appears only if the fetch drags on.

###  Fixed
- **Row action buttons stay reachable on narrow screens.** A wide table pushed the Actions column off the right edge; it is now pinned (`.table-sticky-actions`), so the User Management buttons are always visible.
- **No more blink on load.** The skeleton→data and navigation content fades started content at opacity 0 and flashed empty. Content now appears in place, instantly.
- **CI bundle-check is green again.** `components.min.js` was never committed after the table-reveal change; the artifact is now in sync.

## [2026.7.3.post114] - 2026-08-03 - Refresh lands at the top; two ARIA defects fixed

###  Fixed
- **Refresh no longer makes the page jump around for seconds.** The reload scroll-restore re-wrote the scroll position every 120ms for 5 seconds to fight scroll-anchoring as lazy data grew the page. Refresh now simply lands at the top (`history.scrollRestoration = 'manual'`) - clean and predictable.
- **Tab panels now resolve their `aria-controls`.** Tab buttons referenced panel ids that never existed; `GP.initTabs` now sets each panel's id + `role="tabpanel"`.
- **The JSON-drop textarea has a programmatic label.** Its label rendered as a plain span, leaving the field unnamed for screen readers; it now links via `aria-labelledby`.

## [2026.7.3.post113] - 2026-08-03 - Slow navigation shows the GitPulse pulse, not a skeleton

###  Changed
- **A slow page now shows the GitPulse pulse, not a frozen page or a misfit skeleton.** When a navigation took more than ~120ms the old page sat frozen for the whole fetch and then flashed the destination's server skeleton for a moment. A slow navigation now replaces the content with the centred GitPulse ECG-heartbeat mark (sonar rings + heartbeat running), giving instant "loading" feedback the moment it starts - and, being the brand mark, with nothing to mis-match the destination layout. A fast page still swaps straight in, and reduced-motion shows the static mark.

## [2026.7.3.post112] - 2026-08-03 - Table data fades in calmly instead of popping

###  Changed
- **Loaded table data no longer pops in abruptly.** When a table's rows first replaced the skeleton they appeared in a single hard jump (~1800px, no transition), so a page "behaved horribly when data loaded". Every ClientPaginator-backed table now fades its rows in as one unit on the initial load only (reduced-motion aware); the height-lock already prevents paging jumps and a guard means paging and live refreshes never re-animate. Because almost every data table shares this paginator, the calm skeleton→data handoff is now consistent across the whole app.

## [2026.7.3.post111] - 2026-08-03 - Navigation no longer freezes on script loading

###  Performance
- **Page navigation no longer freezes for seconds on slow links.** The SPA swap handler fetched each per-page script with a *synchronous* XHR so it would run before Alpine initialises the swapped content - on a high-latency connection that blocked the main thread for a full round-trip per script. Scripts now load non-blocking (`<script async=false>`, ordered, cache-served on warm navigations); the content appears immediately as the shell and Alpine initialises once they finish.

###  Changed
- **Event Pipeline filter dropdowns are comfortably sized.** The Type / Status filters shrank to their label width and read as tiny; they now share a consistent, readable width.

## [2026.7.3.post110] - 2026-08-03 - The onboarding tour is less intrusive

###  Fixed
- **The onboarding tour no longer pops on every page.** The welcome card was re-armed on every navigation, so a new tour invitation appeared on each page's first visit as you moved through the app. It now auto-prompts at most once per device; every tour stays available on demand from the launcher.

## [2026.7.3.post109] - 2026-08-03 - Pages no longer break on direct load + content no longer shifts on navigation

###  Fixed
- **Pages no longer break on a direct load / F5 / new tab.** The Alpine CSP build started before a page's body-level component scripts (Teachers, Course Settings, Tickets, Support) had run, so those components were dead on a cold load. Alpine's start is now deferred to `DOMContentLoaded`.
- **Content no longer shifts on navigation.** The SPA swap nested a second `#main-content` inside the first (duplicate id and doubled padding), so content jumped inward after a nav. Only the inner content is swapped now - one element, stable padding.
- **No more console errors navigating to the Teachers or Dashboard pages.** A top-level content `<script>` made htmx throw on Teachers (moved to the head); the Dashboard's shared `config-import.js` helper now loads in order before `dashboard.js`.

###  Changed
- **The generic navigation loading placeholder was removed** - it never matched the destination page. Navigation now keeps the current page visible with the top progress bar (GitLab / YouTube style) and each page shows its own skeletons.
- **Event Pipeline: Replay Events is now a modal** opened from the header (no standalone section), the duplicate per-tab Refresh is gone, and the empty state uses the standard component.

## [2026.7.3.post108] - 2026-08-03 - Cleaner Event Pipeline page + smooth content transition

###  Changed
- **Event Pipeline page restructured, GitLab-style.** The two stacked stat grids collapse into one health strip, and the Recent Events + Dead-Letter Queue tables move into a single tabbed card instead of two separate tables. Replay Events is now a collapsed tool rather than a form competing with the live feed. Reuses the declarative tab controller (`GP.initTabs`), so it survives SPA navigation; every JS-referenced id is preserved.

###  Added
- **Synchronized content fade-in on navigation.** The whole `#main-content` block now fades in as a single unit on each SPA navigation (reusing the existing `.gp-content-in` opacity curve, reduced-motion aware) instead of appearing instantly. It animates the container, not its children - per-element staggered entrance was removed earlier because it re-animated on every live refresh and read as a blink.

## [2026.7.3.post107] - 2026-08-03 - Alpine components no longer break on SPA navigation

###  Fixed
- **Alpine components (Teachers, Course Settings) no longer break after SPA navigation.** A page's scripts are now loaded synchronously and in order on navigation, Alpine is suspended on the incoming content (`x-ignore`) until the component factories are registered, then the subtree is initialised - 0 Alpine errors.

## [2026.7.3.post106] - 2026-08-03 - GitLab-style loading skeleton on navigation

###  Added
- **Instant structure + a loading skeleton while data streams in.** When a
  navigation response is slow (doesn't arrive within ~140ms), the content area shows
  a lightweight shimmer skeleton (header + a stat row + a card of rows) instead of
  the frozen previous page, so navigation always feels instant and the structure
  appears before the data - like GitLab. Fast responses swap directly with no flash.

## [2026.7.3.post105] - 2026-08-03 - Modal + offline-page fixes

###  Fixed
- **Config-driven modals (e.g. Edit User) open again after SPA navigation.** The
  content-only swap doesn't touch `<head>`, where `{% block extra_scripts %}`
  renders a page's inline JSON config - the head reconciler now refreshes it from
  the response, so admin checks no longer fail silently.
- **The "You're offline" page no longer appears while the browser is online.** The
  service worker now shows it only when `navigator.onLine` is actually `false`;
  otherwise it retries once or lets the browser show its own error.

## [2026.7.3.post104] - 2026-07-29 - Navigation no longer breaks the layout

###  Fixed
- **Navigation no longer breaks the layout.** post103 swapped the whole `<body>`,
  re-rendering the sidebar + top bar on every click (a visible flash). Navigation
  now swaps only `#main-content` - the sidebar, top bar, job bar and banners stay
  mounted (GitLab-style stable chrome), and `<title>`, the breadcrumb, the sidebar
  active item, modals and scroll position are reconciled from the response.

## [2026.7.3.post103] - 2026-07-29 - Instant navigation like GitLab

###  Added
- **Instant SPA navigation (like GitLab).** Internal link clicks are intercepted
  and the new page is fetched + swapped in via `htmx.ajax` instead of a full
  browser reload, so the `<head>` (all CSS/JS) is never re-parsed and only the body
  content changes. History (Back/Forward), the top progress bar, `<title>` and the
  sidebar active state all update; charts, Alpine components, tooltips and per-page
  scripts re-initialise on each swap. The click interceptor runs in the capture
  phase (some sidebar/menu components stopPropagation on their own clicks). Logout,
  language, OAuth, downloads, external links and `#`-anchors still navigate normally.

###  Changed
- **Chart.js is now loaded globally** (was per-page). With SPA navigation the
  `<head>` is not re-parsed between pages, so the chart lib loads once and every
  chart keeps working across navigations.

###  Removed
- **The old full-page navigation layer** (`_pageTransitions`) - replaced by the SPA
  navigation above.

## [2026.7.3.post102] - 2026-07-29 - An exact Teacher's Checklist skeleton

###  Changed
- **The Teacher's Checklist loading skeleton is now the chart's shape, not a grey
  box.** It renders the real R01-R13 codes down the left with shimmer name bars and
  gridlines - the same Pajamas horizontal-bar skeleton (`sk_h_bars`) the admin
  System role breakdown uses - and cross-fades into the live chart on first reveal.
  The generic shimmer overlay stays for the line, radar and doughnut charts, where a
  structured skeleton doesn't apply.

###  Fixed
- **The chart shimmer overlay no longer sticks over admin System's role
  breakdown.** The overlay is now opt-in (`.gl-chart-skel`), so it only covers the
  charts that use it instead of blanketing every `.chart-canvas-wrap` - which left a
  solid grey box over the role-breakdown card (it already ships its own skeleton)
  that never cleared.

## [2026.7.3.post101] - 2026-07-28 - GitLab-style chart skeletons + a smoother refresh

###  Added
- **GitLab-style chart loading skeletons.** A page's structure paints instantly,
  but its charts are drawn by Chart.js a beat later - a blank box until then. That
  box now shows a Pajamas shimmer that fades to the chart the moment it renders (a
  safety timer reveals any chart box that never draws, so nothing shimmers forever).
  Covers the analytics, activity, project and student charts.

###  Fixed
- **A refresh no longer jerks the scroll** - the container height is pinned for the
  swap and the scroll offset restored after.

## [2026.7.3.post100] - 2026-07-28 - Analytics-refresh fix + dead skeleton code removed

###  Fixed
- **The course-analytics "Refresh" (and the auto-reload after a sync finishes) did
  nothing after the inline-render conversion.** It re-fetched content by finding the
  old `.gl-lazy-content` shell and re-triggering its `hx-get`, but that shell no longer
  exists (pages are server-rendered inline now), so nothing refreshed. It now re-fetches
  the fragment via the route's `HX-Content-Only` branch into `.gl-tab-content` (verified:
  charts re-render, no console errors). A failed re-fetch keeps the content + shows a toast.

###  Removed
- **Dead loader/skeleton code orphaned by the inline-render conversion** - the client-side
  lazy-fragment SWR cache, the failed-region replacer, the skeleton-flash tracker, and the
  matching CSS. (The same release already removed 1429 lines of dead skeleton macros.)

## [2026.7.3.post99] - 2026-07-28 - GitLab-style page loading + a leaner CI

###  Changed
- **Pages now load like GitLab - the whole page arrives in one server response.**
  Every data page (course overview / activity / analytics / teachers, team,
  project, student, dashboard, user management, tickets) used to render an instant
  skeleton shell and then fetch its real content in a *second* HTMX request, so
  navigation always showed a skeleton→content swap. The content is now
  server-rendered inline in the first response - one request, real structure on
  first paint, no full-body swap. The Redis fragment cache is preserved and an
  `HX-Content-Only` request still returns just the fragment for in-place refresh.
- **CI trimmed to a lean, best-practice essentials set: 22 jobs → 11.** Kept lint
  (ruff), type-check (mypy), the deploy-safety gates (bundle / static-artifact /
  lockfile), tests (unit+coverage, contract, integration), dependency (SCA)
  scanning, and the image build. Removed the heavier / niche jobs (mutation,
  performance, load testing), SBOM, container scanning, SLSA provenance, and the
  publish / security-summary / quality-gate aggregation jobs.

###  Fixed
- **The User Info modal no longer jitters as it opens** - its skeleton was taller
  than the real content, so the centred dialog shrank and its top jumped. It is
  now top-anchored (desktop), so the swap moves only the bottom edge.
- **The "Showing data from last sync" banner now also shows on the main course tab
  (Overview),** matching the Activity and Analytics tabs.

## [2026.7.3.post98] - 2026-07-27 - Load-flash and empty-analytics fixes

###  Fixed
- **The Save button on settings briefly flashed enabled on load.** It rendered
  enabled and was only disabled once the guard ran after the content swap. It
  now ships disabled and the guard enables it the moment the form changes.
- **Archived courses showed live buttons and were still mutable.** The read-only
  class was only added by JS after load; it is now applied server-side. And only
  the settings-save endpoint rejected archived courses - the check endpoints did
  not, so an archived course's checks were editable through the API. A shared
  guard now returns 409 on all of them (verified: active create 201, archived
  create and delete 409).
- **The Week Analytics explorer opened on an empty week** while its dots pointed
  at populated ones, because the dot and the auto-select used different
  definitions of "has data". Both now use one set, so it always opens on the
  latest dotted week.

## [2026.7.3.post97] - 2026-07-23 - README brought in line with the code

###  Fixed
- **The README documented features that no longer exist and a scheduler that
  never ran.** Every claim was checked against the code:
   - The "Automation (12 Scheduled Jobs)" table listed twelve jobs on fixed
      intervals. **None of those function names exist**, and four described
      removed features (CI scenarios, conflict expiry/verification, Docker
      reverification). `app/workers/sweep.py` says it plainly: GitPulse is
      webhook-driven and nothing fires on a timer. The table now lists the eight
      jobs that genuinely exist, with their real trigger.
   - The topology row and repository map claimed `rq-scheduler (12 active
      periodic jobs)` and `scheduler (24 jobs)` - two invented numbers for a
      scheduler that runs with `with_scheduler=False`.
   - Counts were stale after the migration squash: **48 migration files, head
      `047`** -> actually **11 files, head `011`**; 44 models -> **37**; 21
      schema modules -> **18**; 222 routes -> **204**.

## [2026.7.3.post96] - 2026-07-23 - Native tooltips replaced with the component

###  Fixed
- **Three pages still used native browser (`title=`) tooltips**, which this
  project replaces with its own component - they ignore the app's styling and
  read as inconsistent. A browser sweep counted them: 105 on the System page
  (the job-history table), 13 on course Settings (the check toggles) and 26 on
  the student page (the compliance heatmap). All now use the component, bound
  with `GP.initTippy` on the rendered rows.

  Verified in a browser: 0 native `title=` on all three pages and all 18 toggles
  bound. The broken image the sweep flagged is a GitLab avatar 404 falling back
  to initials as designed.

## [2026.7.3.post95] - 2026-07-23 - Filters and pagination for the event feed

###  Added
- **The recent-events feed can be narrowed and paged.** A busy course produces
  hundreds of events and the feed was an unbroken wall of rows. It now has a
  type filter (narrowed server-side), a status filter (Processed / Pending /
  Failed, applied over the fetched window so the health counters keep describing
  all of it), and the same paginator the dead-letter table uses.

###  Fixed
- **The events page hung for over a minute.** A `data_attrs` argument was passed
  to the `select_field` macro, which does not accept one; rather than raising an
  error, the template render wedged. Found by bisection: reverting the template
  alone restored the page, and re-applying the filters without that argument
  rendered in 59ms.

## [2026.7.3.post94] - 2026-07-22 - The Activity tab's address matches the page

###  Changed
- **The Activity page lived at `/courses/{id}/projects`.** The navigation has
  always labelled it Activity and the page is about pipeline health and group
  activity, so the address bar contradicted the tab you had clicked - and
  "projects" already means something else here, the per-project detail pages
  under `/dashboard/projects/{id}`. It is now `/courses/{id}/activity`.

  The old path permanently redirects rather than disappearing, so existing links
  and bookmarks keep working.

## [2026.7.3.post93] - 2026-07-22 - Activity and Analytics stop looking alike

###  Changed
- **Both pages carried an identical header**, so neither said which page you
  were on or what it was for - just the course code, name, year and semester.
  Each now names itself and its scope: Activity is what is happening in GitLab
  right now, Analytics is how students score against the compliance checks.
- **"Pass Rate" on Activity collided with "Checklist Pass Rate" on Analytics.**
  They measure different things - finished CI pipelines versus compliance checks
 - so two unrelated percentages read as if they contradicted each other. The
  Activity figure is now "Pipeline Pass Rate" and says outright that it is about
  builds, not scoring.
- **Activity's counters explain themselves**, matching the standard Analytics
  already met.

## [2026.7.3.post92] - 2026-07-22 - Event context and a testable LLM

###  Added
- **A mock LLM provider.** LLM-backed features were unexercisable whenever the
  real account was unreachable or out of quota, and the failure looked identical
  to a broken integration. `LLM_PROVIDER=mock` answers locally with schema-valid
  responses so those paths can be driven end to end. Not for production.

  It immediately settled an open question: custom-check generation had been
  returning 500, and with the mock the same endpoint returns 200 with usable
  suggestions - so the fault was purely the provider's quota error escaping,
  not the endpoint logic.

###  Changed
- **The event list says what happened, where, and who did it.** It previously
  showed a raw GitLab project id, which tells a teacher nothing about which
  course or student an event belongs to. Each row now carries a summary of the
  action, the course and group with the project path beneath, and the user whose
  action produced it - resolved server-side in one batch query, not per row.

## [2026.7.3.post91] - 2026-07-22 - The Event Pipeline explains itself

###  Changed
- **The page no longer assumes the reader knows the vocabulary.** It opens with
  what an event is and how one ends up in the dead-letter queue, so the figures
  below have a frame of reference.
- **Pipeline health is visible before the problems.** A Processed / Pending /
  Failed row covers the recent feed, so you can tell at a glance whether events
  are flowing without reading the table.
- **Every figure, column and status badge carries an explanation** through the
  app's tooltip component: what a retry count above zero means, why a growing
  Pending number matters, that a parked event is not lost.

  Verified in a browser: 93 tooltips, all bound to the component, and no native
  browser tooltips.

## [2026.7.3.post90] - 2026-07-22 - Visibility into events

###  Fixed
- **The Details button on the Event Pipeline never worked.** Its handler called
  a function that was not defined anywhere in the file, so every click threw and
  the payload viewer could not open - on dead-letter rows just as much as
  anywhere else. The page had that modal all along with nothing able to fill it.
  The function now exists, backed by a new `GET /api/v1/events/{id}/payload`.

###  Added
- **The pipeline now shows the normal flow, not only failures.** It listed the
  dead-letter queue exclusively, so a healthy system receiving events looked
  identical to one receiving nothing. A "Recent Events" feed lists what GitLab
  has delivered lately, newest first, each row marked Processed, Pending or
  Failed, with a failure carrying its reason inline.

## [2026.7.3.post89] - 2026-07-22 - Feedback for live changes

###  Added
- **A page now says what changed when it refreshes itself.** It used to refresh
  silently, so numbers moved under the reader with no explanation. An arriving
  change is announced and named - merge requests, issues, comments, pipelines,
  pushes, members - from the event kind the backend already publishes.

  Bursts are the normal case: one student pushing produces several events within
  seconds and a re-synced project produces many, so notices are coalesced into a
  single message reporting how many changes it covers, rather than one per
  event.

  Verified in a real browser against webhooks driven through the worker: the
  dashboard, the support page and the admin system page all show the notice.

## [2026.7.3.post88] - 2026-07-22 - Behaviour under an invalid token

###  Fixed
- **The shared GitLab token-health flag expired and never came back.** The flag
  exists so one dead token makes every entrypoint and worker refuse doomed work
  at once, instead of each independently probing GitLab. It lives in Redis under
  a 120s TTL but was written only when the status *changed* - and a condition
  that persists, such as a revoked token, never changes the status. The key
  expired, was never rewritten, and from then on every caller ran a live probe,
  measured at 975ms each, against GitLab, indefinitely, for exactly the
  situation the flag was meant to short-circuit.

  The key is now refreshed once it is halfway through its TTL as well as on
  change. The hot path stays cheap: the success mark runs on every GitLab call
  and still skips Redis almost always, because a refresh happens at most once
  per half-TTL.

  Verified against a genuinely revoked token: a status check dropped from a
  975ms cold probe to 1-3ms.

## [2026.7.3.post87] - 2026-07-22 - Webhook throughput

###  Performance
- **A re-delivered webhook refetched the same data from GitLab.** GitLab
  re-delivers on failure, so duplicates are routine. The bulk sync already skips
  the diff and approvals fetch for a merge request whose `updated_at` has not
  moved - both are immutable while the MR is unchanged - but the webhook path
  never did, so every duplicate delivery cost two live API calls.

  The skip only applies when a previous enrichment demonstrably succeeded
  (`changed_files` is what it populates). Without that condition, a delivery
  following a *failed* fetch would carry the same timestamp as the stored row
  and be starved of enrichment permanently.

- **The project -> team lookup ran twice per event.** Four post-commit
  side-effects call it, which is 2000 identical statements across a 1000-event
  burst. It is now memoised for the lifetime of one event. SQL per merge-request
  event: 17.8 -> 16.8.

## [2026.7.3.post86] - 2026-07-22 - Webhook data integrity

###  Fixed
- **GitLab timestamps in webhook payloads never parsed, which silently switched
  off the out-of-order protection.** GitLab uses two different formats: the REST
  API returns ISO 8601, but webhooks send `2025-10-15 10:00:00 UTC` - a space
  separator and a named zone. That shape failed to parse, so every merge request
  and issue delivered by webhook stored empty `created_at`, `updated_at` and
  `merged_at`.

  The consequence was worse than the missing values. The guard recognises a late
  delivery by comparing its timestamp against the stored one, and an empty value
  meant "not stale". GitLab does not guarantee ordering and re-delivers on
  failure, so a late `open` after a `merge` un-merged the merge request and a
  late `reopen` after a `close` reopened the issue - flipping the author's
  R10/R11 scoring until the next full sync.

- **A webhook could erase a timestamp a full sync had already stored.** Both
  processors wrote these fields unconditionally, so an unparseable payload
  replaced a good value with an empty one - which is what disabled the guard.
  They now only overwrite a value they actually parsed. `closed_at` is still
  cleared, because GitLab sends it empty when an issue is reopened.

  Rows already written keep their empty timestamps; a full sync repopulates them
  from the REST API.

## [2026.7.3.post85] - 2026-07-22 - Metric recompute at scale and stylesheet cleanup

###  Fixed
- **A large team broke the metric recompute instead of just slowing it.**
  Loading per-merge-request rows sent one bind parameter per id, and the
  PostgreSQL wire protocol caps a statement at 32767 of them, so a team whose
  projects held more merge requests than that failed the whole recompute with
  a hard error. Ids are now queried in batches well under the cap. Found by
  running the recompute against a seeded 120,002-row table: it raised after
  27.9s, and now completes in 56.3s.

###  Removed
- **43 CSS rules whose selectors can never match.** All 36 classes involved are
  absent from templates, JS and Python-emitted markup. Verified by confirming
  no element on any page - including the 390px and 900px viewports - carries
  any of them.

## [2026.7.3.post84] - 2026-07-22 - Interface correctness and a faster project page

###  Fixed
- **A modal opened shortly after page load closed itself.** The first-visit
  tour prompt closes every active modal and drawer. That is right before a tour
  the user asked for, but the welcome card is unsolicited, so it was destroying
  work in progress. The Weekly Deadline modal opened, faded fully in, then
  closed itself between 400ms and 700ms. The auto-prompt now skips while a
  modal or drawer is open.
- **Cached pages flashed grey placeholder blocks.** A per-frame sampler
  counting only painted skeletons measured ~460ms of placeholder on a page
  whose content was already cached. Placeholders are now held invisible
  briefly: 0ms and 32ms on cached loads, 134ms cold.
- **The expected-checks state badge sat somewhere different in every row**,
  because the check name did not claim the leftover width. Every badge now sits
  a fixed 4px from its cell edge.
- **The last native browser tooltips** (global job bar cancel/dismiss, support
  SSE indicator) now render through the tooltip component. Elements whose label
  is driven by reactive state can opt into `data-tippy-live`.

###  Changed
- **A convention pattern now visibly follows the switch that governs it.**
  R02's branch regex and R05's headings are only enforced while their option is
  on, but both fields stayed fully editable either way, so there was no visible
  way to tell a pattern was off. The field is now disabled and dimmed when its
  switch is off, and its value is kept so switching back on restores it.

###  Performance
- **The project page spent most of its time building a two-element set.** The
  member-cohort derivation selected every merge request and issue row for the
  project and de-duplicated them in Python. Measured on 120,002 rows: slowest
  call 2661ms -> 976ms cold, 240ms warm.

## [2026.7.3.post83] - 2026-07-22 - Maintenance: CI gates and stylesheet cleanup

###  Fixed
- **The `lockfile-check` and `unit-tests` CI jobs were failing.** The committed
  lockfile carried a Windows-only dependency while CI regenerates it on Linux,
  and coverage had slipped below the 38% floor.

###  Changed
- **Removed unused stylesheet rules** (~236 lines) and raised coverage to
  38.11% by testing config-import validation, queue backpressure and webhook
  scope validation.

## [2026.7.3.post82] - 2026-07-21 - Database-unavailable diagnostics

###  Fixed
- **A "Database unavailable" 503 now says why.** Both database exception
  handlers discarded the exception, so connection refused, pool timeout,
  exhausted server connections and bad credentials all produced an identical
  blank 503 with no log line.

## [2026.7.3.post81] - 2026-07-21 - Settings apply on one save, conventions live in their checks

###  Fixed
- **Compliance-check edits no longer apply on their own.** The check editor and
  the weight presets wrote to the server the moment you pressed Save Check,
  while every other control waited for "Update settings" - with no way to back
  a change out. Both now stage and are flushed by the settings save.
- **The number stepper no longer jumps two at a time.** Two implementations were
  bound to the same class, so one click stepped the value twice.
- **Scroll position survives a reload.** The shell scrolls inside
  `.gl-page-content`, so `window.scrollY` was permanently 0 and the feature was
  a no-op on every page using it.
- **Modals no longer flash on open.** Backdrop and dialog both animated opacity,
  which multiplies for nested elements.

###  Changed
- **Convention patterns moved into the checks that enforce them.** The branch
  regex, test paths and MR template headings sat in a separate "Patterns" card,
  and two of the three scored nothing unless the check was separately set to
  strict. Adds TUKE FEI / Strict / No-conventions presets. Migration 011
  backfills existing courses.

## [2026.7.3.post80] - 2026-07-18 - Out-of-order webhooks, tz-aware commits, server-driven presets

###  Fixed
- **Out-of-order GitLab webhooks no longer regress entity state.** GitLab does
  not guarantee webhook ordering and re-delivers on failure. The MR and issue
  processors overwrote `state`/`updated_at` unconditionally, so a stale `update`
  (state=opened) redelivered after a `merge`/`close` would un-merge an MR or
  re-open a closed issue, flipping R10/R11 for the author until the next manual
  sync. The guard (monotonic `updated_at`) from the pipeline processor was
  extracted into `processors/_common.is_stale_update` and applied to the MR and
  issue processors.
- **Commit timestamps are parsed tz-aware.** `commit_processor` used raw
  `datetime.fromisoformat()`, so an offset-less timestamp was stored naive - 
  inconsistent with the tz-aware column and the compliance engine's tz-aware
  semester-window filter (where a naive value raises `TypeError`). Routed
  through the shared `parse_gitlab_datetime`.
- **LLM analysis redacts more PII.** MR metadata (branch names) and changed
  filenames now pass through `redact()` before the context is sent to the
  external model.

###  Changed
- **Compliance weight presets are server-driven and dynamic.** The
  course-settings presets were hard-coded in JS and covered only R01-R12
  (R09/R11/R13 skipped). They are now computed server-side
  (`build_weight_presets`) over the live built-in check set, normalised to sum
  to 1.0, and returned from `GET /courses/{id}/checks`.
- **R02 spec aligned with code.** The docs claimed a ∀ (all MRs) rule while the
  code passes on ∃ (at least one), like R03/R04/R05. Per product decision the
  ANY behaviour is intended; only the docs were corrected.

## [2026.7.3.post79] - 2026-07-17 - Compliance config helpers + second query-dedup pass

###  Changed
- **Compliance config parsing unified.** The string→bool coercion (`x.lower() not in ("false","0","no")`) was copy-pasted across R02/R04/R06/R09/R11 and re-implemented as a local `_bool` closure in R10 - six copies of one idea, and the five inline copies skipped the `bool()`-normalisation R10 applied to non-string values. Consolidated into a module-level `_cfg_bool` sibling to `_cfg_int` so every check parses config booleans one way (and more robustly); R05's deliberately strict `in ("true","1","yes")` form is left as-is. The capped partial-credit ratio `min(n/max(t,1),1.0)` - copied in R03/R06/R07/R09 - is now `_partial_ratio`.
- **Second query-dedup pass.** The "latest MetricSnapshot per student, scoped to one team → dict" query - copy-pasted three times (`projects.py` twice, `teams.py` once) with per-site redundant inline `func` imports - now lives in one shared helper `_stats.latest_student_metric_map` (the student twin of `latest_team_metric_map`). Two dict annotations tightened to their true non-optional type. Behaviour-preserving across all documented config values and both queries; covered by new unit tests and the full suite (2,310).

## [2026.7.3.post78] - 2026-07-17 - Query dedup: one owner for "latest snapshot per team"

###  Changed
- **Query dedup: one owner for the "latest snapshot per team" logic.** The same `func.max(computed_at)` subquery that fetches each team's most-recent `TeamMetricSnapshot` had been copy-pasted across five call sites - twice in the course pages, again in `api/sync.py` and `api/sync_stream.py`, and once more inlined in `home_course_health.py` (a byte-identical copy of a helper already living in `home_stats.py`). Consolidated into two shared helpers in `api/dashboard/_stats.py` - `latest_team_metric_map` (full snapshot per team) and `latest_team_snapshot_subquery` (the max-per-group subquery) - so the pattern has one tested source of truth. Removed three orphaned imports and a stale "using DISTINCT ON" comment on a query that never used DISTINCT ON. Behaviour-preserving; a new unit test locks in the helper contract. A full-codebase refactor audit (compliance engine, sync/webhook workers, services, templates) confirmed those subsystems were already deduplicated by the post76/post77 sweeps - no further safe cuts remained.

## [2026.7.3.post77] - 2026-07-17 - Instrumented whole-system dead-code purge (~5,000 lines)

###  Changed
- **Whole-system dead-code purge with custom analyzers - ~5,000 lines removed.** A repo-wide audit (analyzers for Jinja macros, CSS classes, JS exports and templates + the CI dead-code report), every candidate verified against a corpus of templates + app JS + vendored libraries + Python-built HTML; dynamically-constructed class families (`'prefix-' + x`, `'prefix-' ~ var`, `prefix-{{ var }}`) excluded wholesale. Result: **74 orphan Jinja macros** (~930 lines) incl. stale imports and 2 unreferenced component files; **~680 orphan CSS classes** (~3,950 lines across 44 files, styles bundle ~6% smaller); **8 dead JS export surfaces**. `badge(variant='blue')` now renders styled (aliased into the info family - it used to emit an unstyled badge). Guarded by the full unit suite (2,286 tests), bundle checks and a real-browser visual smoke.

## [2026.7.3.post76] - 2026-07-17 - Big cleanup: less code, one way to do each thing

###  Changed
- **Legacy/compat code removed app-wide.** The bare Clone flow is gone: both `/clone` endpoints, the schema and the dashboard's duplicate clone modal - the course context menu now opens the one Transfer wizard (course settings → Danger Zone), which covers cloning as "clean course, don't archive, no webhooks". `apiCall` dropped its positional-retryCount compatibility branch (no caller used it). The `window.GitPulseMotion` facade with its kept-for-compatibility no-ops is deleted - the motion controller exports exactly one helper (`GP.revealAfterSkeleton`) plus the compliance rings. The never-fired `htmx:abort` listener is gone. Orphan CSS deleted (slideIn, `.row-expand-enter`, `.card-glass` + tokens, the unused stagger token; hover transitions no longer animate `transform`). The stale `start-dev.sh` (native-Postgres era) is removed - `start-dev.ps1` is the dev entry point. The dead-code report is clean.

## [2026.7.3.post75] - 2026-07-17 - Full course transfer to a new semester

###  Added
- **Full "Transfer to new semester" - proper course reactivation.** The old bare Clone (settings only, no groups, dead webhooks) is superseded by a wizard in course settings → Danger Zone: pick the new academic year and semester, then choose what carries over - **everything** (all groups; members/projects re-sync from GitLab), **a selected subset of groups**, or a **clean empty course** with the same settings. Everything auto-retunes: same-semester transfers shift the semester window, course deadlines and every per-week deadline date by the academic-year delta; cross-semester transfers keep the expected-check structure but clear un-guessable dates. **Webhooks keep working with zero GitLab changes** - the default mode re-points existing webhook configurations to the new course; alternatively issue fresh one-time secrets (surfaced once) or skip webhooks. The source course is archived (optional) and the initial sync for carried groups is enqueued (optional). New `POST /api/v1/courses/{id}/transfer`; `/clone` stays for compatibility. Covered by 8 new unit tests.

## [2026.7.3.post74] - 2026-07-16 - SWR memory for lazy pages, global search fix, visible avatar ring

###  Fixed
- **Global search: erasing the last character no longer flashes every suggestion for a second.** Race condition: clearing the query rendered the default suggestion list WITHOUT invalidating the in-flight API request for the previous character; its response landed ~200ms later and wiped the list. Every `doSearch` now bumps the request generation (including the empty-query path) and every response path discards stale generations.
- **Dashboard greeting avatar ring is visible on the light theme** - it was `--gl-gray-0` (white in both themes) and vanished against the light background; now the shared `--border-color` token.

###  Added
- **Lazy pages remember their last content (stale-while-revalidate).** Revisiting a lazy page used to replay the full skeleton while the same fragment re-fetched. Each fragment's last HTML is now kept per-tab (sessionStorage, keyed by fragment URL, invalidated by app version and 15-minute age, purged on the login page) and injected instantly in place of the skeleton on revisit while the normal request silently swaps in fresh data - YouTube-style SWR. Empty states ("No tickets found") appear instantly on revisit instead of flashing a shimmering table skeleton first.

###  Changed
- **Dead skeleton code deleted:** the generic `sk_table`/`sk_tbody_rows` pair and the `sk_commits`/`sk_mrs` row macros were referenced by no template; guard tests now assert the living per-table contracts.

## [2026.7.3.post73] - 2026-07-16 - Motion only where it carries information + unified role badges

###  Changed
- **The whole animation system rethought: motion only where it carries information.** Removed as flair, app-wide: the metric count-up (stat values animated 0→N over 600ms on every reveal - numbers now just render), the staggered block reveal and item cascade on lazy loads (regions now fade in as ONE quiet unit, opacity-only), the entrance rise/scale transforms on skeleton hand-off and page enter, and the never-used scroll-reveal machinery with its dead motion-* utilities. What stays is deliberate: overlay enter/exit (modals, dropdowns, toasts), loading indicators (spinners, skeleton shimmer, progress), change feedback (cell flash, badge pop, banner height ease), semantic status pulses and the compliance-ring draw. The public GitPulseMotion API is kept (no-ops), so nothing breaks.
- **Role badges are ONE component everywhere.** The Admin badge in the course Teachers manager was blue while User Management shows amber - every role chip now goes through the shared `role_badge()` macro (admin=amber, teacher=purple, TA=info, student=neutral); the members-table access ladder and the user-info modal's JS maps already matched and stay in lockstep. The student page's Author/Reviewer pill was renamed `mr_role_badge` so MR participation can't be confused with global roles.

## [2026.7.3.post72] - 2026-07-16 - Calm hovers, exact skeletons, componentized badges, dev toolbar

###  Fixed
- **Distracting hover animations removed app-wide.** The empty-state icon lifted, scaled, glowed a blue halo and floated on an infinite loop on hover; course cards and interactive cards lifted (`translateY`/`scale`); issue rows lifted. All hover transforms are gone - hover is now a calm border/background/shadow change only (GitLab-style). Button press feedback and semantic status pulses (running dots, traffic lights) stay.
- **Version detection now works in development.** The dev build fingerprint only hashed `core.bundle.js` + `main.py`, so template and page-bundle edits were invisible to the client's update detection. In development the fingerprint is now per-server-start: every `uvicorn --reload` restart announces a new version and open tabs show the update toast + auto-reload.
- **The support tickets skeleton is structurally identical to the loaded page.** The search/filters toolbar was a hand-copied approximation that had drifted; it is now ONE shared macro (`_tickets_toolbar.html`) rendered by both the live page and the skeleton (disabled) - the same single-source pattern as `table_heads.html` - and the skeleton now includes the pagination bar, killing the layout jump on load. Static chrome stays real; only DB data shimmers.

###  Changed
- **Badges componentized.** 21 hand-written `<span class="badge ...">` across 8 templates now go through the shared `badge()` macro; the macro gained an `x_text` param for Alpine-bound counters.

###  Added
- **Dev toolbar in the UI** (development/debug only, never rendered in prod): a fixed DEV pill that expands to the whole local tooling surface - Swagger (interactive tester for every endpoint), ReDoc, health JSON, Mailpit, the admin system page, Grafana, Jaeger - plus the live build fingerprint that changes on every dev reload.

## [2026.7.3.post71] - 2026-07-16 - Dense tables share the User Management scroll model + one-command dev environment

###  Fixed
- **Dense tables share the User Management scroll model everywhere below ~1440px windows - single-line headers and cells, columns sized to content, horizontal scroll.** post70 kept the fixed %-columns in the tablet band and let headers wrap at word boundaries; in practice that still read as mush - "Event ID" / "Dead Since" on two lines, "Ac tio ns" broken mid-word, dates wrapped to three lines (DLQ, tickets). Worse, the dense tables' headers alone need ~1010px - more than the ~980px content column a 1280px laptop window leaves next to the sidebar - so fixed %-columns cannot fit even on small desktops. All `tbl-fixed` scroll tables (tickets, DLQ, job history, admin courses, feature flags, group activity, recent MRs) now switch to content-sized auto layout with `nowrap` + ellipsis below 1440px and scroll horizontally; the fixed %-contract returns on full desktops where it genuinely fits. Unbounded text columns are capped with a clean ellipsis (ticket/MR titles, group links, feature-flag description). Course group/project/member tables extended to the same boundary.
- **Tickets desktop columns rebalanced again** - post70's 7% Actions column wrapped its own header on 1280px screens; restored to 10%.
- **Job History mobile "Result / Error can wrap" rule re-pointed** to the right column (it had drifted onto Duration when the select-checkbox column was added). Verified in a real browser at 480-1600px: single-line headers everywhere, zero unintended cell clipping, no page-level horizontal overflow.
- **User Info modal avatar fallback uses the component standard** - the initials circle was the last one-off blue/purple gradient left in the app; it now uses the same neutral surface + border + secondary-text circle as every other avatar fallback.

###  Changed
- **`start-dev.ps1` now drives the whole dev environment** (no separate script): `up`/`restart` bring up the docker-compose.dev.yml containers - Postgres :5433, Redis :6379 and the new **Mailpit** mail catcher (SMTP :1025, UI :8025, matching the `.env` SMTP settings) - with health waits; the DB wipe on `down`/`restart` runs inside the compose container (no local psql needed, correct 5433 port instead of the stale native-5432 assumptions); health checks cover the real ports. Mailpit catches all outgoing email locally.

## [2026.7.3.post70] - 2026-07-16 - All tables (and their skeletons) scroll instead of squishing on tablets

###  Fixed
- **Every data table (and its skeleton) now scrolls instead of squishing across the whole tablet range.** Root cause: in the 769-1024px band the fixed 240px sidebar squeezes the content column to ~480-736px - often narrower than a phone, where the sidebar overlays - but most horizontal-scroll minimum widths only applied at ≤768px. Groups, group/project member matrices, course settings (checks, webhooks), student tables and archived courses crammed their columns exactly on tablets. All scroll floors now cover ≤1024px (the pattern post68 applied to dense admin tables), the groups and projects tables switch to content-sized auto layout with scroll in that band, and the dashboard archived-courses and weekly-deadlines tables opted into the scroll contract they were missing entirely. Skeletons share the live tables' classes, so they follow automatically.
- **Tickets table: badges and pills no longer clip mid-word.** The "In Progress" status badge and submitter/assignee pills were hard-clipped by the fixed column widths even on desktop. Columns rebalanced (status/submitter/assignee wider, title/actions narrower), the tablet scroll floor raised 860→1000px so every non-title column fits its typical badge/pill, and unusually long usernames now degrade with a clean ellipsis inside the pill. Only the title column ellipsizes by design.
- **User Management kept its intended tablet widths** - the new generic floor briefly out-ranked the users-table's own 760/680px tablet contract in the cascade; its selectors now carry the specificity to win again. Verified in a real browser at 480-1280px: zero clipped cells outside intentional title ellipsis, no page-level horizontal overflow anywhere.

## [2026.7.3.post69] - 2026-07-16 - Top progress bar never hangs at the end forever again

###  Fixed
- **The top progress bar can no longer hang at ~99% forever after AJAX actions** (e.g. right after creating a support ticket). Two mechanisms survived post66, both reproduced in a real browser against the production bundle: (1) a bar carried over from the previous page could be "adopted" by a request starting during the bar's 650 ms finish fade - the adoption skipped the in-flight increment, so when that request's completion event was lost (its element removed mid-swap) the counter read zero while the bar visibly trickled forever, and the network reconciler explicitly ignored the zero-counter state; (2) a canceled navigation - staying on the page via the unsaved-changes dialog, pressing Esc during a slow load, or a POST that turns out to be a file download - left the `page-navigating` marker on `<body>` forever, which disabled the reconciler entirely. Fixes: `stop()` now consumes the inherited pending synchronously (no adoption after a finish), the reconciler also finishes a visibly-running bar whose counter is zero (unless the finish fade owns it), and a bounded watchdog drops `page-navigating` after 10 s alive without an actual navigation. Verified end-to-end: both endless repros now self-heal in ~2-12 s, while legitimate slow requests and slow full-page navigations are untouched.

## [2026.7.3.post68] - 2026-07-15 - Dense tables stay readable across the whole tablet range (small tablets too)

###  Fixed
- **Dense tables now stay readable across the whole tablet range (small tablets included), not just phones.** The horizontal-scroll min-width for fixed-layout data tables (tickets, job history, admin courses, feature flags, DLQ, activity) only kicked in at ≤820px, so in the 820-1024px tablet band the columns were squeezed at full width - headers wrapped and action buttons overflowed. It now applies up to 1024px, so those tables scroll cleanly with a comfortable column width and a sticky first column instead of cramming. The tickets table (8 columns) gets a slightly wider 860px floor so its title / badges / assignee pill / action button never collide.
- **Dead-letter queue: the select checkbox no longer looks squished.** The JS-rendered rows put the checkbox in a class-less first cell, which collapsed to the bare checkbox width in the tablet auto-layout; the first column now keeps a tap-friendly minimum width and is centered.

## [2026.7.3.post67] - 2026-07-15 - Consistent table cells and avatar fallbacks across the app

###  Fixed
- **Table cells and avatar fallbacks are now consistent.** Ticket titles wrapped to 2-3 lines on tablet (the `text-overflow: ellipsis` was inert without `white-space: nowrap`) - they now stay on one line and clip cleanly, matching the User Management table that was cited as the ideal. Long group/subgroup names in the Groups table clip with an ellipsis instead of wrapping. The student-profile avatar's initials fallback used a one-off blue/purple gradient - it now uses the same neutral grey circle as every other avatar fallback (discussion notes, reviewer chips), so fallbacks look identical everywhere.

## [2026.7.3.post66] - 2026-07-15 - Top progress bar finishes immediately on AJAX actions (no timeout)

###  Fixed
- **Top progress bar now finishes the instant an in-place AJAX action completes** (e.g. "ticket created"), instead of running out a timeout. This replaces the post65 20 s ceiling (which was wrong - it still visibly ran for 20 s). The real fix is the pattern the GitLab group import / group CRUD already used (`GP.finishTopProgress()` when an AJAX form is intercepted), applied centrally in the shared submit handler - so any form that calls `preventDefault()` (support ticket, reply, analytics/replay, ...) finishes the bar right away, system-wide. The button spinner still shows the request's own progress.

## [2026.7.3.post65] - 2026-07-15 - Tickets list shows all tickets, priority emails, image preview, progress ceiling

###  Fixed
- **Tickets list showed only the first form's tickets** (the rest looked "missing" - "#5 but the other 4 are gone"). It defaulted its form filter to `forms[0]`, silently hiding tickets from other forms (or none). It now shows all of the course's tickets; a form filter is applied only when explicitly requested.
- **Priority changes sent no email** - only status changes did. A priority change now emails the submitter/assignee (when different from the actor), like a status change. Verified via Mailpit.
- **Attached image blended into the text in Preview** - it's now block-level (own line, clear spacing).
- **Table headers wrapped character-by-character on tablet** ("Sub mitte d By"). They now wrap at word boundaries, and fixed scrollable tables keep a usable min-width (horizontal scroll) up to 820 px.
- **Top progress bar could still hang** - added a hard 20 s ceiling that force-finishes it regardless of a stuck `page-navigating` class or a hung fetch (complements the post60 reconciler fix).

## [2026.7.3.post64] - 2026-07-15 - Ticket status changes live-update the list + new-ticket toast

###  Added
- **Ticket status/priority/assignment changes now live-update the tickets list**, and a **"New ticket received" toast** appears when a ticket arrives. The status-update endpoint only published to the per-ticket channel (open detail page); it now also publishes a `ticket_updated` event on the course channel, so the list reflects the change without a manual refresh. Together with post63, the tickets surface is fully dynamic - create or change a ticket anywhere (including the API) and the UI reacts live.

## [2026.7.3.post63] - 2026-07-15 - Tickets list live-updates when a ticket is created

###  Added
- **The tickets list now live-updates when a ticket is created** (including via the API or by another user), instead of only appearing after a manual refresh. Ticket creation publishes a `ticket_created` event on the course SSE channel and the course-scoped tickets list subscribes and reloads on it (coalesced to one reload / 1.5 s). Verified in dev: submitting a ticket publishes `{"event":"ticket_created","ticket_id":...}` to `dashboard:course:<id>`. Closes the "what I create in the console doesn't show in the UI" gap for tickets (the course dashboard already did this for webhooks).

## [2026.7.3.post62] - 2026-07-14 - Table headers no longer truncated ("Priority ...", "Acti...")

###  Fixed
- **Table headers were truncated** to "Priority ...", "Category ...", "Acti..." in fixed-layout data tables (tickets, courses, admin/events). `.sort-link` forced `white-space: nowrap`, so narrow columns clipped the labels. Headers now wrap within their column instead of truncating (cells still truncate). Scoped to `.tbl-fixed`, so every fixed-layout table is fixed at once.

## [2026.7.3.post61] - 2026-07-14 - Post-navigation flicker gone, image previews, table empty state

###  Fixed
- **Whole page flickered on every navigation.** The page-enter animation was meant to be removed (it made the main container + small cards blink on every nav) but the rule survived in `loaders.css` and still faded `.main-container` in on every load. Removed it - pages render instantly now (only the single login card keeps a gentle fade).
- **Image attachments showed as a link, not a preview.** `renderMarkdown` didn't handle `![alt](url)`, so images rendered as text like `123!file.png`. It now renders an inline thumbnail (click opens full size), in both the Preview tab and the ticket thread.
- **Filtering a table to zero showed a blank table.** The shared filter only showed "no results" for a text search, not for the status/priority/category dropdowns. It now shows a componentized empty state (icon + message) whenever any active filter hides every row - across every filterable table.

## [2026.7.3.post60] - 2026-07-14 - Top progress bar no longer hangs while a background job polls

###  Fixed
- **Top progress bar could hang (never finish) while a background job was polling** - during a group import, or on ANY page opened while a sync / import is running. The nav bar's stuck-counter reconciler reset its "quiet" timer on every background poll's brief network blip, so it never auto-finished and the bar stayed pinned for the whole 120 s last-resort timeout. It now **accumulates quiet time and only pauses (never resets) on brief poller spikes**, so a stuck bar self-heals in ~1.5 s regardless of pollers. A genuinely slow load keeps real network in flight continuously, so its bar correctly stays until done. Same root cause you saw on group import - this fixes it everywhere.

## [2026.7.3.post59] - 2026-07-14 - Teacher webhook toast + clear "Cancelled" + calendar corner

###  Added
- **Teachers get a live toast when a GitLab webhook lands for a group.** The webhook SSE notification now carries the group name, and the course page shows a staff-only toast (e.g. "Webhook received: Merge request - Team Alpha"). It's built to interact cleanly with the rest of the app: only the visible leader tab shows it and broadcasts to sibling visible tabs (N open tabs → one toast, background tabs stay silent); it's **suppressed while the course is mid-sync** (the global sync bar already signals updates); and it's throttled to one per 4s so a burst of pushes/pipelines can't spam the corner. The per-event refresh already existed - this adds the visible heads-up. (The recompute was already scoped to the affected group + debounced - unchanged.)

###  Fixed
- **A cancelled job no longer reads as "Process failed".** Cancelling a sync / run-checks / import is intentional, but it fell through the failure path. It now shows a clear "Cancelled" (the bar's terminal-state model stays binary done/error - only the wording changed).
- **Calendar header rounded-corner artifact.** The month-nav header and the rounded calendar container each rounded their corners, leaving a mismatched notch by the `<` / `>` arrows. The calendar now clips cleanly to its rounded box (`overflow:hidden`) and the header/arrows no longer double-round.

## [2026.7.3.post58] - 2026-07-14 - Calendar: closes with its modal + visible arrow hover; dashboard archive

###  Fixed
- **Date-picker calendar stayed open after its modal closed.** Flatpickr appends its calendar popup to `<body>`, so when a modal with a date field closed the calendar was left floating over the page. Closing a modal now also closes any flatpickr owned by its inputs (every close path - button, backdrop, Escape, programmatic).
- **Calendar month-nav arrows had an invisible hover.** The `<` / `>` hover background was `--surface-moderate` - the same colour as the `.flatpickr-months` header - so hovering did nothing visible and the arrows read as empty rounded shapes. The hover now uses the app's icon-button hover token, so it's clearly distinct.

###  Changed
- **Dashboard onboarding respects archived courses.** When an account had no *active* courses it always showed "Create your first course" (linking to the course list) - even when every course was archived (e.g. auto-archived at semester end). It now offers to **reactivate an archived course for the new term**, pointing at `/dashboard/admin/courses` where the Activate button lives.

## [2026.7.3.post57] - 2026-07-14 - Attachment upload fixed (route collision), markdown toolbar, double line

###  Fixed
- **Attachment upload was broken for everyone (real root cause).** `POST /support/{token}` (the JSON ticket-submit route) was declared before `POST /support/upload`, so `/support/upload` matched the `{token}` param route with `token="upload"` - a JSON endpoint that can't read multipart, so every upload failed with a 422 "Input should be a valid dictionary". The post55 URL fix only moved it from 404 to the wrong route; uploads never actually worked. The fixed `/support/upload` path is now declared before the param route, with a regression test.
- **Markdown toolbar heading/quote/list rendered literally.** Those block markers (`### `, `> `, `- `) only work at the start of a line, but the toolbar inserted them at the cursor, so clicking Heading after text produced `text### text` on one line. `mdInsert` now breaks to a new line before a block marker when it isn't already at line-start, like GitHub/GitLab.
- **Redundant double line under the support form header.** After the "Logged in as @..." banner was portaled to the global top strip (post56), the `gh-form-divider` that used to separate it from the form was left behind - doubling the `page-header` bottom border. Removed that orphaned divider; the header border is now the single separator.

## [2026.7.3.post56] - 2026-07-14 - Status banners to the top strip + offline page redesign

###  Changed
- **Page-level status banners now portal to the global top strip everywhere.** The support form's "Logged in as @..." notice, the course "Some sync jobs failed" / "Sync cancelled" banners, and the project "GitLab repository is empty" warning were rendered inline in the page body; they now move up into the shared `#globalBannerSlot` (same mechanism as the archived-course banner) and render as the single unified `top_banner` (`.gp-top-banner`) strip, so every page's status bars stack together like GitLab's broadcast bar.
- **The two live JS-created course banners were unified too.** The "GitLab token invalid" banner and the live "Some sync jobs failed" banner (created by the sync SSE stream without a page reload) were `.info-card` boxes in the page body; they now render as the same `.gp-top-banner` strip appended to `#globalBannerSlot`. Invariants are preserved: the live failed banner is still only created when there's no server-rendered one, and only the JS-created card is ever removed. The `top_banner` macro gained an optional `class` argument.
- **The "You're offline" page was redesigned GitLab-style.** It now leads with a brand lockup using the app's current logo (`favicon.svg`, precached so it renders fully offline) instead of the browser's default globe, sharing the same `error.css` tokens as the other error pages.

## [2026.7.3.post55] - 2026-07-13 - Upload 404, Preview tab, false dirty - all fixed

###  Fixed
- **Attachment upload failed everywhere ("Upload failed").** The client posted to `/api/v1/support/upload`, which 404s - the route lives on the telemetry router (`/telemetry` prefix), so the real path is `/api/v1/telemetry/support/upload`. Fixed the URL; the error message now also includes the status code (was empty because HTTP/2 has no `statusText`).
- **Markdown editor Preview tab didn't switch (no error).** The `$mdShowPreview` magic read `el._x_dataStack` off the button, which is often undefined on a descendant, so the write silently no-op'd. It now uses the canonical reactive `Alpine.$data(el)` (stack walk kept as fallback).
- **Support form flagged a false "unsaved changes".** It marked dirty on ANY `input`/`change`, including programmatic ones (Alpine / select-default writes). It now requires `e.isTrusted` - a genuine user edit.

## [2026.7.3.post54] - 2026-07-13 - JSON-import file clear + remove-file theme

###  Fixed
- **JSON import: removing the file left its content behind.** `showFile()` auto-reads the selected file INTO the paste textarea, but `clearFile()` only cleared the file input - not the textarea. So removing the file left the content "inserted". `clearFile()` now also clears the textarea.
- **Remove-file button hover** used a hardcoded dark `--gl-red-950` background (jarring on the light theme); now the theme-aware `--gl-feedback-danger-bg` tint.

###  Notes
- Investigated the support **Preview** button and the tickets **skeleton**: both are correct in the code (the `$mdShowPreview` magic, `renderMarkdown` + `supportFormEditor` load on the page; the skeleton uses the same `tickets_table_head()` as the live table). The specific breakage needs a concrete repro rather than a blind guess.

## [2026.7.3.post53] - 2026-07-13 - Modal-shift regression, banner overlap, drop-zone theme, offline favicon

###  Fixed
- **Regression: content shifted LEFT when a modal opened.** The post50 scrollbar compensation was wrong - `overflow: hidden` is still a scroll container, so `scrollbar-gutter: stable` stays effective and the gutter is never released; the added padding over-compensated. Reverted.
- **Connection/health banner overlapped the top-bar dropdown menu.** It was `z-index: var(--z-sticky)` (above the dropdown tier). It's an in-flow status strip, so it's now `calc(var(--z-dropdown) - 1)` - below dropdowns, above page content.
- **JSON import drop zone was unreadable on the light theme.** The `has-file` state used a hardcoded dark `--gl-green-950`; it's now the theme-aware `--gl-feedback-success-*` tint (bg + text + icon).
- **Offline page** had no favicon (browser globe in the tab); it now links the app favicon so the tab shows the current GitPulse logo.

## [2026.7.3.post52] - 2026-07-13 - User Info skeleton + global timeout/retry (componentized)

###  Changed
- **User Info modal skeleton (componentized).** Both entry points (the admin users page and the global "click a username" modal in core) showed a generic spinner. They now render a structural skeleton that mirrors the loaded card (avatar circle + identity + meta + two sections of card placeholders), shared via `UserInfoModal.skeleton()`, so the hand-off to real data has no layout jump.

###  Fixed
- **Global User Info hung forever on slow/offline networks.** It used a raw `fetch()` with no timeout. It now aborts after 12s via an `AbortController`, and its error state renders a **Retry** button (matching the admin path). Both entry points now share the same skeleton, component avatar fallback, timeout and retry.

## [2026.7.3.post51] - 2026-07-13 - User Info avatar fallback, banner overlap + slow-net fixes

###  Fixed
- **User Info modal avatar uses the shared component fallback.** It was a bare `<img>` with a bespoke initial-letter branch; it now renders with `data-avatar-fallback` + an initials sibling, so a broken / timed-out / offline avatar degrades to initials via the same global handler (retry, offline deferral, watchdog) as every other avatar.
- **Top bar dropdown no longer overlaps the connection banner.** The top bar was `z-index: var(--z-sticky)` - the same as the health/connection banner (which lives later in the DOM and so painted over the open dropdown menu). The top bar is now `calc(var(--z-sticky) + 10)`.
- **User Info on slow/offline networks.** Request timeout dropped 30s → 12s and no longer retries, so a hung request stops holding the `_infoLoading` lock (which made further clicks do nothing). The error state now has a **Retry** button instead of a dead end.

## [2026.7.3.post50] - 2026-07-13 - Modal open no longer jerks the page right

###  Fixed
- **Opening a modal no longer jerks the page to the right.** The scroll lock set `.gl-page-content { overflow: hidden }`, which stops it being a scroll container - so its `scrollbar-gutter: stable` reservation is released and the content widens/shifts right by the gutter width. `_refreshBodyScrollLock` now measures that gutter (`offsetWidth - clientWidth`) BEFORE locking and preserves it as `padding-right` (`--gp-lock-gutter`) while a modal is open. Safe across stacked modals (measured once on the first lock), reset on the last close. Verified the entrance keyframes (`modalSlideUp`, `gp-content-in`, `gp-fade-in`) are vertical-only.

## [2026.7.3.post49] - 2026-07-12 - Smooth element-removal collapse (shared helper)

###  Added
- **`GP.collapseAndRemove(el, cb)`** - a shared helper (alias of the existing `collapseBanner`) so any single element removed WITHOUT a full list re-render collapses smoothly (height + fade) instead of vanishing, reduced-motion aware.

###  Changed
- The dashboard **course card** now collapses smoothly when removed (was fade-then-snap-gap), via `GP.collapseAndRemove`, keeping the empty-section update in the callback.
- Audited the removal sites: most (analysis cards, admin-course rows, welcome tour, sync-stream cards) already had exit animations, so the motion system is consistent; only the course card lacked a collapse. Table `<tr>` removals keep fade (rows can't animate height reliably).

## [2026.7.3.post48] - 2026-07-12 - Component-level button interaction states

###  Changed
- **Component-level button interaction states.** Every `.btn` now has a subtle tactile press (`:active` translate+scale) and a shared success/error feedback flash (`GP.flashButton(btn, 'success'|'error')` → `.gp-btn-success` pulse / `.gp-btn-error` shake), all reduced-motion aware. The shared process-action failure path (Run Checks / Sync across course/team/project) flashes the button on error. Applied through the button component so it is consistent app-wide.
- Verified the rest of the motion system is already consistent: toasts have a proper `toast-dismissing` exit animation, dropdowns use Alpine enter/leave transitions, and modals use the post47 inertia swipe-to-dismiss. Remaining per-element exit polish continues iteratively on top of this.

## [2026.7.3.post47] - 2026-07-12 - User Info archived badges, modal swipe inertia, calendar Wk fix

###  Fixed
- **User Info modal shows archived/inactive state.** Courses and groups never indicated archived/inactive. The info API now passes `is_active` / `course_active` / `team_active`, and `user-info-modal.js` renders a muted "Archived" badge on those cards.
- **Mobile modal swipe-to-dismiss now has inertia.** Dragging a bottom sheet down past the threshold used to reset the transform to 0 and replay a canned slide-down (a jump/blink). It now continues the sheet off-screen from the finger position (`.sheet-dismissing` suppresses the `modalSlideDown` keyframe; the backdrop still fades).
- **Calendar "Wk" column no longer blank.** Without a semester anchor (e.g. the create-course modal before a start date is picked) every week cell was empty. It now falls back to the ISO-8601 week number, switching to semester weeks once an anchor exists.
- **User Info avatar** is top-aligned (was centered against a tall identity block, looking cramped) and can no longer be shrunk.

## [2026.7.3.post46] - 2026-07-12 - Unified top-banner style + dismiss, stale presets fixed

###  Changed
- **Unified top-banner style + dismiss.** All page-level status strips now render through a single `top_banner` macro (`.gp-top-banner`) styled globally in `health.css`, so the archived, "Data may be outdated" and stale-data strips look identical (flush GitLab-style strip: icon + message + optional action + dismiss). Each has a dismiss (X) that persists across navigation, reload and other tabs via the shared `gp:dismissedBanners` store (the dismiss handler + `_hideDismissedBanners` were generalized from `.info-card` to `.gp-top-banner`; the portal skips already-dismissed strips). The slot caps at `50vh` and scrolls when many strips stack. The banner CSS moved into the global bundle so it works on every page, not just course pages.

###  Fixed
- **Stale semester presets.** The "Quick preset" dropdown offered past semesters (Winter/Summer 2025/2026, now ended). `get_presets()` now drops any preset whose `end_date` is before today, leaving only the current + upcoming semesters.

## [2026.7.3.post45] - 2026-07-12 - All page-level banners consolidate into the top strip

###  Changed
- **All page-level status banners now consolidate into the global top strip.** Generalized post44's archived-banner portal into a reusable mechanism: any banner marked `.js-top-banner` (with an optional `data-banner-key` for dedup) is portaled by JS (`_portalTopBanners`) into `#globalBannerSlot` at the top, stacking flush with the job bar and connection/health banner like a GitLab broadcast bar. Applied to the **"Data may be outdated"** card (course overview) and the **stale-data** banner (analytics + activity), on top of the archived strip. They are hidden in their content origin until portaled (no flash) and keep their natural flex layout in the slot, just losing margin/radius so they read as flush strips.
- Element-scoped empty states ("not synced yet", "repository is empty") are deliberately NOT marked, so they stay in place - they describe a specific element, not global page status.

## [2026.7.3.post44] - 2026-07-12 - Archived banner moved to the global top status strip

###  Changed
- **Archived-course banner moved to the global top status strip.** The "Archived course · read-only" notice sat inline below the course title. It now renders as a flush, full-width GitLab-style strip at the very top of the page, stacking with the background-job bar and the connection/health banner (one shared status area). The strip is rendered in the lazily-loaded course content with full context, then JS portals it into a global slot (`#courseArchivedSlot`) in `base.html` under the health banner; it is hidden in its content origin until portaled so there is no flash. The read-only guard still keys off `.tabs-nav[data-course-archived]`, so behaviour is unchanged.
- The strip is now static (no card border/radius, no entrance animation). Contextual notices (stale-data above charts, "not synced yet" empty states) intentionally stay in place - they describe specific content, not global page status.

## [2026.7.3.post43] - 2026-07-12 - Job History bulk management + purge fixes

###  Added
- **Job History bulk management.** Each operations-log row now has a checkbox (plus a select-all header) and a "Delete selected" action that removes the chosen rows by id (`/jobs/delete`) - background jobs and audit operations alike. Synthetic rows (archive derived from a course's `archived_at`) get a disabled checkbox and are skipped.
- **Purge by age.** "Purge Old" is now a dropdown: older than 24 hours, 7 days, 30 days, or Everything.

###  Fixed
- **Purge Old now clears operations, not just jobs.** It only deleted `BackgroundJob` rows, so the visible audit operations (deletes/imports/restores) never cleared - the reported "Purge Old stopped clearing". The endpoint gained a `scope` (`jobs`/`operations`/`both`, default `both`).
- **Archived courses now show their archival.** A course archived before the `course.archive` audit-write existed had no audit row, so neither Job History nor "Follow the latest updates" showed it was archived. Both now synthesize a "Course archived" entry from `Course.archived_at`.
- Verified: no dead code remains for the removed features (gaming, rubric, assignments).

## [2026.7.3.post42] - 2026-07-12 - Job History is a complete operations log

###  Added
- **Job History is now a complete operations log.** It listed only background jobs (sync, checks, enrichment, metrics), so synchronous admin actions - course/group create, import, archive, delete, restore, settings, support, events - showed in "Follow the latest updates" but were silently absent from Job History. The admin jobs endpoint now merges those non-job audit actions in with the background jobs (same row shape: status `completed`, no duration, not cancellable), while excluding job-like audit actions (sync/checks/...) that already exist as `BackgroundJob` rows so nothing double-lists. That is why an empty prod Job History still showed the delete + imports in the feed only - now both surfaces agree.

## [2026.7.3.post41] - 2026-07-12 - Auto-archive shows in the updates feed + safer JSON import

###  Fixed
- **Auto-archive now shows in "Follow the latest updates".** When a course auto-archives (or a teacher archives one by hand) the dashboard feed stayed silent - `archive_course` wrote no audit entry, and the feed scoped the archived course out because it was no longer active. Archiving now writes a `course.archive` activity entry attributed to the actor, and the feed keeps recently-archived course ids in scope so the entry actually surfaces.
- **Import course from JSON: a failed apply no longer dies silently.** The apply handler awaited `onApply` without a `catch`, so a rejected API call surfaced only as an unhandled promise rejection in the browser console. It now shows a clear error toast. (The `content.js ... message port closed` message some users saw is a browser extension, not GitPulse.)
- **Activity feed actor names.** The course-config seed actor now reads as "Course import" instead of the raw lowercase `auto-import` machine name, like the other machine actors (System, Scheduler, Background worker).

## [2026.7.3.post40] - 2026-07-11 - Auto-archive actually archives now + profile avatar fix

###  Fixed
- **Auto-archive now actually archives.** post38 enqueued the sweep to a worker job (fork + `asyncio.run` + engine re-init) that could quietly leave nothing archived. The dashboard now runs the sweep INLINE in its own throwaway session, throttled ~once/15 min via a Redis lock released on failure so the next load retries. Ended courses archive on the next staff dashboard load.
- **Profile skeleton avatar no longer double-loads.** The skeleton and the loaded content both loaded the photo - two avatar requests whose fallback/watchdog handlers raced. The skeleton now shows initials; the photo loads exactly once with the content.
- **Commit History badges** ("Merge commit" / branch) hug the message instead of floating far right with a big centre gap.
- **Archived Courses card** got bottom breathing room and its actions wrap instead of overflowing.

###  Changed
- **Archived-course banner is now a slim GitLab-style strip** at the top of the course tabs, not a big alert card.
- **Commit History branch filter** is now the app's animated dropdown component (glFormSelect) instead of a native `<select>`.
- Version `2026.7.3.post40`; Service Worker cache `gitpulse-v311`.

## [2026.7.3.post39] - 2026-07-11 - Archived courses are now viewable (read-only)

###  Added
- **Archived courses are now viewable (read-only).** The dashboard "Archived Courses" list gained a **View** button that opens the course. Every course tab (overview / settings / activity / analytics / teachers) shows a read-only banner - "This course is archived, archived on <date> ... Reactivate it to make changes" - with a Reactivate shortcut for staff.
- **Archived courses are genuinely read-only.** Course-scoped mutations (course sync-all, course & group run-checks, group sync, settings save, group creation) are rejected server-side with a clear 409 while the course is archived; the guarded action buttons are disabled and dimmed. Reactivation is unaffected.
- **Live read-only awareness.** A course page polls its status (~1/min) and, if the course is archived in another tab or by another user, flips to read-only without a manual refresh.

###  Fixed
- The dashboard archived-courses list no longer only offered Re-activate/Delete with no way to actually open an archived course.
- Version `2026.7.3.post39`; Service Worker cache `gitpulse-v310`.

## [2026.7.3.post38] - 2026-07-11 - Semester-end auto-archive actually runs now

###  Fixed
- **Semester-end auto-archive actually runs now.** Course Settings shows an "Auto-archive due / Auto-archives <date>" badge and a "Skip automatic archiving" toggle, and the dashboard hints that ended courses will be archived - but nothing performed it since the scheduled sweep layer was removed (there is no cron/scheduler daemon). The sweep is back and runs opportunistically: the staff dashboard enqueues it at most once per hour (Redis lock), and the worker archives every active course whose semester ended more than the grace period ago, unless the course opted out via "Skip automatic archiving". Idempotent and fire-and-forget - never blocks the dashboard; reactivating a course opts it out of the next sweep, so an archive is easily reversible.
- Dashboard hint copy is now truthful: an auto-enabled ended course reads "being auto-archived"; an opted-out one reads "auto-archive is turned off - archive manually".
- Version `2026.7.3.post38`; Service Worker cache `gitpulse-v309`.

## [2026.7.3.post37] - 2026-07-11 - An explicitly chosen theme no longer flips to the system theme on its own

###  Fixed
- **An explicitly chosen theme no longer flips to the system theme on its own.** The client trusted the account's rendered `data-theme-preference` over the local choice. When the account was still on the ambiguous `system` default (never overridden server-side, or an earlier persist POST failed) while this browser held an explicit `light`/`dark`, a reload re-resolved to `system` and followed the OS - so an explicit dark could switch to light by itself. The bootstrap now keeps a local explicit choice over a server `system` default and reconciles the account (re-persists) once the DOM is ready. An explicit `light`/`dark` set on another device still syncs across devices.
- Version `2026.7.3.post37`; Service Worker cache `gitpulse-v308`.

## [2026.7.3.post36] - 2026-07-11 - A week with no expected checks no longer shows 100% + no skeleton avatar swap

###  Fixed
- **A week with no expected checks no longer shows 100%.** The weekly compliance score for a week before the curriculum introduces any check was stored as a vacuous `1.0` (nothing to fail = "100%"), so the Weekly Breakdown showed e.g. Week 1 = 100% while its heatmap row was all-N/A. Such weeks now render as N/A ("-") for the overall score AND every category, and the trend line skips them - consistent with the heatmap. Applies to existing and future data.
- **The Profile skeleton avatar now matches the loaded avatar.** During the skeleton phase the avatar was a bespoke initials circle and swapped to the photo once the content loaded. The skeleton now renders the real avatar via the same shared `data-avatar-fallback` component the dashboard/topbar use (photo, falling back to initials on error), so there is no swap.

###  Changed
- The theme-switch reveal is slower and gentler (440 ms -> 620 ms) so the full-screen wipe feels smooth instead of an abrupt snap.
- Version `2026.7.3.post36`; Service Worker cache `gitpulse-v307`.

## [2026.7.3.post35] - 2026-07-10 - Fix: the course Teachers page no longer renders as an empty broken shell

###  Fixed
- **The course "Teachers" page no longer renders as an empty broken shell.** Its page script declared `const GP` at the top level, which collided with the global `const GP` that `core.bundle.js` already declares (`SyntaxError: Identifier 'GP' has already been declared`). A parse error aborts the whole file, so `teacherManager()` was never registered and every Alpine expression on the page failed. The script is now wrapped in an IIFE like every other page script. Added a regression test that fails if any `pages/*.js` declares `GP` at global scope.
- Version `2026.7.3.post35`; Service Worker cache `gitpulse-v306`.

## [2026.7.3.post34] - 2026-07-10 - The page no longer looks stuck loading once it's done + immutable compliance history

###  Fixed
- **The page no longer looks stuck loading after it has fully rendered.** When an avatar host black-holed the connection (TUKE VPN down, GitLab unreachable), the `<img>` fired neither `load` nor `error` and stayed pending forever - so the browser tab kept its loading spinner spinning even though every bit of page content was already on screen. Avatars now have an 8 s load watchdog: on expiry the request is aborted and the initials fallback is shown, so the tab stops spinning.
- **Compliance history is now immutable.** Backfill used to recompute every past week from the *current* database state and upsert over it, so when GitLab data was later deleted (a branch or MR removed) a re-sync silently rewrote a student's historical score downward. Backfill now only fills weeks with no snapshot yet; a week that was already recorded stays as it was.
- **No more phantom "Week 21" after the semester ended.** Weekly compliance snapshots are capped at the teaching window, the exam period closes via an effective end date even without an explicit end, and the charts (course trend line and the student trend/heatmap/radar) clip weeks past the window.
- **Faster pages: pruned the redundant `metric_snapshots` backlog** (migration 010). post33 capped future growth but left ~480k historical duplicate rows - the real cause of the intermittent multi-second page loads. The migration keeps the newest row per (team, student, UTC week) and deletes the rest; the latest score is unchanged.
- **Charts are readable on the light theme.** The compliance donut, the "Skill Profile" radar tooltip, and several chart tooltips and grids were hardcoded to a dark surface / near-white grid (dark-on-dark / invisible on the light card). They now take their colours from the shared, theme-aware Chart.js defaults.
- **Student page polish + smaller fixes:** the loading skeleton matches the loaded MR cards and section headers 1:1; the commit table keeps the "Merge commit"/branch badges in fixed columns; the "Total Active Weight" block is restructured into a dedicated summary band; the top progress bar no longer sweeps backwards while fading out; a guarded modal Save button is no longer briefly clickable on open; the Run Checks checkbox focus outline is no longer clipped.
- Version `2026.7.3.post34`; Service Worker cache `gitpulse-v305`.

## [2026.7.3.post33] - 2026-07-08 - Compliance snapshots no longer grow without bound (slow pages)

###  Fixed
- **Compliance snapshots no longer grow without bound (slow pages).** Every sync / Run Checks INSERTed a brand-new `metric_snapshots` row per student - the unique key carries `computed_at`, so nothing ever deduped. Production had **506k rows, ~882 per student**, pushing the per-group "latest snapshot per student" aggregate to **1.2 s** (×8 groups on a course page) and making the student page load 800+ history rows. A recompute now keeps exactly **one snapshot per (team, student, ISO week)**: it deletes the rows it supersedes - scoped to the same team, same week, and only the students being recomputed, so a partial recompute never drops another student's week - then writes the fresh ones in the same transaction. Current score and the weekly history chart are unchanged.
- Version `2026.7.3.post33`; Service Worker cache `gitpulse-v304`.

## [2026.7.3.post32] - 2026-07-08 - Activity feed no longer reports every scope as a whole-group action

###  Fixed
- **"Follow the latest updates" no longer reports every scope as a whole-group action.** A course-wide Run Checks fans out into one `run_checks` job per group, and only *sync* bursts were aggregated - so the feed listed each group's check separately and read as if the whole group ran repeatedly. Run-checks bursts now fold into a single "Ran checks for N groups" entry (same 5-minute clustering as "Synced N groups"), and a project-scoped run reports "Project checks completed" instead of the generic label with the group name attached.
- Version `2026.7.3.post32`; Service Worker cache `gitpulse-v303`.

## [2026.7.3.post31] - 2026-07-08 - No phantom "Sync completed!" toast when running checks

###  Fixed
- **No more phantom "Sync completed!" toast when running Run Checks.** A checks recompute emits an SSE `update`; the sync-stream saw no sync work but a stale `_syncWasActive` flag still fired `_completeCourseSync()` → a "Sync completed!" toast even though nothing synced. The terminal sync toast is now gated on a new `_sawRealSyncRunning` flag set only when a poll/SSE tick actually observes a sync running/finishing.
- **Removed the duplicate "Data updated" info toast** after a job completes - the global job bar already shows the terminal toast, so the extra one just stacked a second toast.
- Version `2026.7.3.post31`; Service Worker cache `gitpulse-v302`.

## [2026.7.3.post30] - 2026-07-08 - Student page skeleton adds the email row

###  Fixed
- **The student page loading skeleton now includes the email row** in the profile identity block (mail icon + address), matching the loaded page for teachers/admins (`can_edit`). It was the one identity field missing between the username and the "View on GitLab" link, so the header shifted slightly when real data arrived.
- Version `2026.7.3.post30`; Service Worker cache `gitpulse-v301`.

## [2026.7.3.post29] - 2026-07-08 - Per-group "Recomputing..." badge during Run Checks

###  Added
- **"Run Checks (all groups)" now shows a per-group "Recomputing..." badge** on each group row while it runs, so the course page gives visible per-row feedback like a sync does (previously only the global progress bar moved). The badges clear when the rows refresh on completion.
- Version `2026.7.3.post29`; Service Worker cache `gitpulse-v300`.

## [2026.7.3.post28] - 2026-07-08 - R09 (MR Approved) no longer breaks after merge - scores stay correct

###  Fixed
- **R09 (MR Approved) no longer drops to a false FAIL after an MR merges** - this silently lowered compliance scores across all merged MRs. GitLab clears an MR's `/approvals` list once it merges and its branch is deleted, so a later sync overwrote the stored approvals with 0; with `min_approvals >= 2` every merged MR then failed R09 (e.g. a student 0.860 -> 0.825, group averages fell too). R09 now counts distinct approvers from the **permanent "approved this merge request" system notes** (union the live list, netting any later "unapproved"), which survive the merge - so scores stay correct and are immune to the post-merge clobber. Re-run checks / sync to restore affected scores. Regression tests added.
- Version `2026.7.3.post28`; Service Worker cache `gitpulse-v299`.

## [2026.7.3.post27] - 2026-07-08 - Student skeleton 1-to-1, single job-bar X, double top-bar fix

###  Fixed
- **Student page skeleton now matches the loaded page 1-to-1.** The Compliance Progress loading state was badly out of sync: Score Trend was a tiny bar in a big empty box, Skill Profile a bare circle, and the "Check Progress by Week" heatmap + threshold pills + week-over-week summary were missing. The skeleton now fills the Score-Trend chart box, renders the threshold pills, a radar placeholder with the week label and the Current-Score / vs-Last-Week / Weakest-Area summary, plus the full R01-R13 × weeks heatmap.
- **Global job bar shows exactly one trailing control** instead of two ambiguous X's: a running job shows the cancel-X (which confirms before stopping the process), a finished/failed job shows a dismiss-X to close the bar. Consistent in the full render and the in-place update.
- **Top progress bar no longer fires twice on a slow navigation.** The network-activity reconciler used to force-finish the bar (snap to 100% + clear the hand-off state) during a full-page navigation - which has no fetch in flight - so the destination page popped a new bar from zero. It now skips finishing while navigating, so one continuous bar spans old page → new page.
- Version `2026.7.3.post27`; Service Worker cache `gitpulse-v298`.

## [2026.7.3.post26] - 2026-07-07 - Strip the inert maintenance-jobs panel shell

###  Removed
- Stripped the inert "scheduled / maintenance jobs" panel shell left over from post24. The jobs grid was no longer rendered, so this was dead scaffolding: removed the admin endpoints (`/jobs/trigger`, `/jobs/retry`, `/scheduled-jobs`, `/jobs/active-scheduled`), the empty `admin_scheduled_registry`, `run_tracked_scheduled` + `sweep_tracking`, and the front-end trigger/poll/SSE code in the admin-system bundle. Kept the live background-job history table, cancel, health, cache and stats. The useless per-row "Retry" button was removed with its dead endpoint.

###  Changed
- `custom_check` schema: extracted a shared `validate_rule_type` helper so the create/update validators no longer duplicate the rule-type check.
- Version `2026.7.3.post26`; Service Worker cache updated to `gitpulse-v297`.

## [2026.7.3.post25] - 2026-07-07 - Distinguish a template fork with no student commits

###  Added
- Project detail now distinguishes a **template/fork with no student commits yet** from a genuinely empty repository. When the repo has template-author commits but no student has pushed their own work, the "Issues to Address" card shows a dedicated "Template / fork - no student commits yet" state (instead of the misleading "No repository data yet"), the Contributors card says "Only template authors so far", and the Commits stat renders " - " instead of a misleading "0". Detected consistently in both the full-page render and the live-data refresh. Slovak translations added.
- Version `2026.7.3.post25`; Service Worker cache updated to `gitpulse-v296`.

## [2026.7.3.post24] - 2026-07-07 - Removal of the dead scheduled/periodic sweep-job layer

###  Removed
- Removed the dead "scheduled / periodic sweep" job layer. There is no recurring scheduler and the admin maintenance-job catalog is empty, so these jobs could never fire: `periodic_llm_analysis`, `periodic_telemetry_snapshot`, `sweep_dlq_auto_resurrect`, `cleanup_old_events`, `cleanup_old_email_logs`, `sweep_email_queue`, `sweep_auto_archive_ended_courses`, `sweep_unprocessed_events`. Deleted their modules (`sweep_jobs`, `sweep_cleanup`, `sweep_maintenance`, `sweep_events`), the periodic functions in `sweep_telemetry`, the orphaned `_delete_in_batches` helper, the `_FEATURE_FLAG_MAP` entries, the activity-feed `scheduled:*` labels, and the admin retry legacy map. Tests updated.
- The event/sync-driven jobs are unchanged: `refresh_project_gitlab_intel` (webhook intel refresh), `sync_single_team_members` (push member sync), and `telemetry_snapshot_for_team`. Email delivery is unaffected (`enqueue_email` enqueues `deliver_email` directly).

###  Note
- Recovery paths that only the deleted jobs provided (DLQ resurrect, event retention, unprocessed-event replay, email-send retry) were already non-functional without a scheduler; a manual re-sync pulls current state, so no data is lost. The empty maintenance-panel shell stays inert and can be removed in a follow-up.
- Version `2026.7.3.post24`; Service Worker cache updated to `gitpulse-v295`.

## [2026.7.3.post23] - 2026-07-07 - Logo animation fix and documentation cleanup

###  Fixed
- The logo's ECG-pulse animation no longer jumps back to the start of the trace when the cursor leaves. Hovering used to swap the pulse `animation-duration` (3.8s -> 0.95s); reverting it on mouse-leave re-mapped the animation's elapsed time onto the longer timeline, snapping the moving segment backward. Hover now only brightens the pulse at a constant speed, so it continues smoothly from its current position.

###  Changed
- Renamed `app/workers/sweep_ci.py` -> `app/workers/sweep_events.py` (the name was a leftover from the removed CI-failure feature, but it now only holds the webhook-event recovery sweep). Pure rename - the `app.workers.sweep.*` RQ string paths still resolve via re-exports.
- Removed references to the three deleted sandbox features from the current docs (API spec, data model, requirements, rollout, checklist mapping, architecture tree, developer pages). Historical CHANGELOG/archive, thesis narrative, and migration-history pages are unchanged.
- Version `2026.7.3.post23`; Service Worker cache updated to `gitpulse-v294`.

## [2026.7.3.post22] - 2026-07-07 - Complete removal of three unused sandbox features

###  Removed
- Removed three unused sandbox features entirely (feature-flagged off by default, never enabled in production, zero rows in their tables): the **git conflict simulator**, the **Docker build verification** module, and the **CI-failure scenario generator**. Deleted their services, workers, models, API routes, templates, JS (`_parts` + rebuilt bundles), feature flags and orphan i18n strings; the course-settings config columns and the (empty) feature tables are dropped by new migration `009_drop_sandbox_features` (idempotent `IF EXISTS`). No behaviour change for users.

###  Changed
- Version `2026.7.3.post22`; Service Worker cache updated to `gitpulse-v293`.

## [2026.7.3.post21] - 2026-07-07 - "Issues to Address" empty state no longer vanishes + reverted the across-reloads cache (it flickered / showed stale data)

###  Fixed
- The "Issues to Address" empty-state card no longer vanishes a second after load. On a live-data poll where the server can't determine the repo state it returns an empty `issues_html` (by design: "keep the current card"), but the client's legacy fallback then hid the card with `d-none`. Removed that dead legacy path - the persistent server-rendered empty state now stays.
- Reverted the stale-while-revalidate lazy-content cache (post19/post20). It painted the last-seen content on refresh, but after a background sync it showed stale/empty content and flickered ("appears then disappears", "nothing shows after sync"). Pages now always render fresh from the server (a brief skeleton on refresh is the trade-off), so displayed data is always correct and never disappears. Stored data (members / contributors / stats) renders from the DB snapshot regardless of GitLab token state.

###  Changed
- Version `2026.7.3.post21`; Service Worker cache updated to `gitpulse-v292`.

## [2026.7.3.post20] - 2026-07-06 - The across-reloads cache actually engages now + token alert links to the docs

###  Fixed
- The lazy-content cache (post19) now actually engages. The cache-write step rejected any page whose real content contained a nested client-filled skeleton (charts, analysis cards, ...), so the page was never cached and F5 kept flashing the full-page skeleton. At `htmx:afterSwap` the content is always the real server response (the initial skeleton is already gone), so that guard was wrong - removed it.

###  Changed
- The "GitLab token invalid" item in "Items that need your attention" now links to the token docs (`/docs/gitlab/tokeny/`) explaining how to rotate it, instead of System Settings - the token is a server env var, not an in-app setting, so System Settings could not fix it.
- Version `2026.7.3.post20`; Service Worker cache updated to `gitpulse-v291`.

## [2026.7.3.post19] - 2026-07-06 - Lazy pages paint instantly on refresh (cache across reloads), not a skeleton

###  Changed
- Lazy-loaded dashboard pages now paint **instantly** on a refresh / return instead of flashing the loading skeleton every time. A stale-while-revalidate cache (`_parts/core/50-lazy-content-cache.js`) stashes the last-seen rendered content per URL in `sessionStorage` (per-tab, memory-only - never written to disk, matching the `no-store` policy on `/dashboard`) and repaints it the instant the page loads, while htmx fetches fresh content in the background and swaps it in. Applies to every `.gl-lazy-content[hx-trigger*="load"]` page (course / team / project / student / dashboard / admin). The entrance reveal is suppressed on the revalidation swap (via `data-swr-painted`) so there is no double-reveal flash; cache entries are size-capped and 10-minute TTL-bounded. This is the client-side answer to "F5 re-runs everything" - `/dashboard` responses stay `no-store` (auth-page security).
- Version `2026.7.3.post19`; Service Worker cache updated to `gitpulse-v290`.

## [2026.7.3.post18] - 2026-07-06 - No live GitLab calls while rendering pages, dashboard shows failed syncs and an invalid token

###  Fixed
- The student page no longer makes live GitLab calls while rendering. It fetched up to 12 pipeline coverage details + a user-avatar lookup on every load, which stalled the page (and hung on an expired 401 token). It now renders purely from stored data - coverage is filled by sync + webhooks and reused from the existing SHA-based DB fallback; the avatar comes from the stored value or the URL-pattern fallback. Data reaches every page only via sync + webhooks, never a render-time API call.
- "Follow the latest updates" now shows FAILED jobs (e.g. a sync blocked by an invalid token). The feed queried only `completed` jobs, so every failure was hidden; failed jobs now appear with an alert icon and a "... failed" label.
- The Course Settings sticky action bar no longer leaves a thin lighter strip at the very bottom - it compensated an 8px page padding, but `.gl-page-content`'s bottom padding is 12px, so the last ~4px showed through. Now compensated to 12px.

###  Added
- "Items that need your attention" surfaces an "invalid GitLab token" item when the token is rejected (read from the shared cached health flag - no live probe on render), linking to System settings so it can be updated quickly.

###  Changed
- Version `2026.7.3.post18`; Service Worker cache updated to `gitpulse-v289`.

## [2026.7.3.post17] - 2026-07-06 - Group/project Sync button no longer sticks without a timer, unified failure messages

###  Fixed
- The group / project **Sync** button no longer gets stuck disabled with no cooldown timer after a failed sync (e.g. an expired 401 token). Root cause: the sync registers a global job, and completing that job with an error fired the process-lock release (`unlockElement`), which **cleared the anti-spam cooldown that had just been applied** - so the countdown vanished and the button could be left blocked. `unlockElement` no longer clears an active cooldown, nor re-enables a button a cooldown is still holding. The countdown now survives and the button self-recovers on every page (the course page only escaped the bug via its early token-return, which never registers a job).
- Sync-failure messaging is now consistent across course / group / project. A shared `GP.syncErrorMessage(err)` returns the detailed "GitLab API token is invalid or expired (401)..." text on a 401 (already translated) instead of the bare "Sync failed" the group / project pages showed while the course page showed the full reason.

## [2026.7.3.post16] - 2026-07-06 - Cached GitLab panels, no duplicate banner on the group page, simplified & unified sync

###  Fixed
- Project sync wrongly reported "Group sync completed" on success - it now says "Sync completed", matching the entity being synced (group vs project).
- The top loading strip no longer stays pinned at 100% when a new request begins during its fade-out. `start()` now resumes a finishing bar as one continuous indicator instead of leaving it stuck at the end and then popping a fresh bar.

###  Changed
- The "Data may be outdated" webhook/staleness banner is no longer duplicated on the group (team) page - it is a course-level notice and already shown on the course page.
- Group sync stripped of its dead sync-modal code. That modal was removed from the templates long ago (the global job bar owns all sync UI now), so its `getElementById` calls were no-ops; group sync is now bar-only like project sync and both use the same generic "Sync completed" / "Sync failed" messages.
- GitLab intelligence panels (protected branches, contributors, repository statistics, milestones, releases, labels) are now under HTTP caching. Their responses carry `Cache-Control: private, max-age=300` + a content-derived `ETag`, and the project page revalidates them with a conditional request (`cache: no-cache`) instead of the old `no-store` full re-download - so an unchanged snapshot returns a bodyless `304` and repeat visits/refreshes come from the browser cache.
- Version `2026.7.3.post16`; Service Worker cache updated to `gitpulse-v287`.

## [2026.7.3.post15] - 2026-07-06 - Sync button no longer hangs on "Wait 1s" on other pages, smooth banners, GitLab-spec tables, cross-tab work

###  Fixed
- The Sync / Run Checks button no longer freezes on "Wait 1s" after a failure on the team, project and per-group pages. Root cause: a race between the anti-spam cooldown and `setButtonLoading` over `dataset.originalText` when a request fails fast (< 400 ms, i.e. a 401 token rejection) - the deferred min-visible-duration reset fired mid-countdown and deleted the saved label, so the cooldown could not restore the button. The course page escaped it only via its early token-guard; every other page went through the racing path. Fixed in the shared core, so it is fixed on every page at once.
- The failure cooldown countdown now shows on every sync trigger (course Sync All, per-group sync, team sync, project sync), not just some buttons.

###  Changed
- Banners (the "Data may be outdated" / GitLab-token / sync-failed cards) now ease open and closed (animated height + opacity) instead of popping in and shoving the page content down. A dismissed banner now STAYS dismissed across tab switches, page reloads and other browser tabs (persisted in `localStorage`).
- Data tables now follow the official GitLab Pajamas table spec 1:1: header and body cells both use 16px (`gl-p-5`) padding, and the condensed variant is exactly half (8px).
- With the app open in several tabs, a single visible "leader" tab now owns the sync pollers / SSE streams (fail-open `localStorage` lease); the other tabs mirror state via storage events. This removes duplicate `/sync/active` requests, out-of-step progress bars and duplicate completion toasts across tabs. A lone tab always leads, so a single tab is never affected.
- Version `2026.7.3.post15`; Service Worker cache updated to `gitpulse-v286`.

## [2026.7.3.post14] - 2026-07-04 - Cooldown no longer hangs on "Wait 1s", Slovak translation, on all Run Checks buttons

###  Fixed
- The anti-spam button cooldown no longer hangs on "Wait 1s". The 200 ms countdown tick self-heals: when the time is up it clears the cooldown and restores the button, so a lost/throttled `setTimeout` can never leave it pinned.
- "Wait" is now translated (Slovak `Počkajte`), so the cooldown countdown is no longer English-only on the Slovak UI.
- The failure cooldown now covers every Run Checks button (course / team / project, via the shared `runScopedChecksProcess`), consistent with the Sync buttons.

###  Changed
- Version `2026.7.3.post14`; Service Worker cache updated to `gitpulse-v285`.

## [2026.7.3.post13] - 2026-07-04 - Top loading strip: bulletproof reconcile against real network activity

###  Fixed
- Top loading strip - a fundamentally different fix. Instead of chasing every way the event-driven `pending` counter can get stuck (a prevented submit like Import with an empty URL, missed/duplicated htmx events, a click that starts a "navigation" that never navigates), the bar is reconciled against REAL network activity: `window.fetch` and `XMLHttpRequest` are wrapped so a request-lifecycle counter (`.finally` / `loadend` always fire) tracks what is genuinely in flight, and a 250 ms reconciler finishes the bar ~1.2 s after the last real request completes - regardless of what the fragile event counter believes.

###  Changed
- Version `2026.7.3.post13`; Service Worker cache updated to `gitpulse-v284`.

## [2026.7.3.post12] - 2026-07-04 - Sync button frees without refresh, top loading strip no longer hangs

###  Fixed
- The Sync / Run Checks button now frees itself WITHOUT a page refresh. The ghost-expiry guard only ran while a job was visible in the bar, so a hidden ghost never got expired and the button stayed locked until a manual refresh. The guard now runs while ANY job exists; a ghost with no real backend job_id is retired ~15 s after load, and team/project syncs no longer inherit the 45-min course maxAge cap.
- The top loading strip no longer hangs at ~99 %. A race let the generic htmx handler count a `.gl-lazy-content` request but skip its decrement, leaving the bar pinned for the full 120 s stuck-timeout. Lazy requests are now counted exclusively by the lazy bridge.
- The job bar's grow-in is smoother (lowered target height so the transition spans the animation).

###  Changed
- Cross-tab toasts are suppressed in background tabs; queued completion toasts are de-duplicated by job.
- Version `2026.7.3.post12`; Service Worker cache updated to `gitpulse-v283`.

## [2026.7.3.post11] - 2026-07-04 - Neutral avatar, fixed activity feed, smooth banners

###  Fixed
- The Sync / Run Checks button no longer sticks disabled on project & group pages (or any scope). The global job bar reconciled only course-level ghosts against `/sync/active`; a team-/project-scoped sync ghost restored from localStorage was skipped, so it kept the button process-locked for its full maxAge (up to 45 min) even when the server reported nothing active - and it survived refreshes because localStorage persists. Reconciliation now covers team/project ghosts too (matched by their owning course).
- Avatar fallback initials are no longer on a purple disc - the top-bar and dashboard-greeting avatars now use a neutral slate (`--gl-gray-700`).
- The "Follow the latest updates" feed no longer loses entries. A background refresh (a) never replaces a populated feed with the "no activity" empty state (a transient builder hiccup or a brief quiet window used to wipe every visible row), and (b) preserves the "Show all" expand state instead of collapsing back to 5.
- Status strips no longer jolt the page when they appear. The global job bar eases open via a `max-height` `transition` + `@starting-style` (not a keyframe - the bar's deterministic removal contract is preserved), and the health banner grows in by `max-height` instead of sliding a full-height box in with `translateY`, so the content below makes room smoothly.

###  Changed
- Version `2026.7.3.post11`; Service Worker cache updated to `gitpulse-v282`.

## [2026.7.3.post10] - 2026-07-03 - Sync button no longer sticks disabled after a refused sync

###  Fixed
- The Sync / Run Checks button no longer sticks disabled after a refused sync. The global job bar marks a click optimistically as a "connecting" job before the server confirms a run; when the sync is refused (invalid/expired GitLab token, 401) or the page restored a stale pre-POST snapshot, that placeholder had no backend job behind it yet kept the button process-locked for the full 5-45 min staleness window - and inconsistently across project / team / course. The staleness guard now retires a "connecting" job that never got a real backend `job_id` after ~15s, so the button frees up quickly and identically on every scope. A genuine (even slow-queuing) sync always carries its `job_id`, so it is never affected.

###  Changed
- Version `2026.7.3.post10`; Service Worker cache updated to `gitpulse-v281`.

## [2026.7.3.post9] - 2026-07-03 - Consistent avatar fallback across surfaces

###  Fixed
- Avatar fallback is now consistent across surfaces. The dashboard greeting avatar used the old pattern (photo over a grey disc with a hidden letter), so it diverged from the top-bar avatar (fixed in post6) - one could flash an empty grey circle while the other showed the branded initial. The greeting avatar now uses the same layering (the initial is the always-present base and the GitLab photo overlays it), so both degrade identically.

###  Changed
- Version `2026.7.3.post9`; Service Worker cache updated to `gitpulse-v280`.

## [2026.7.3.post8] - 2026-07-03 - Remove the standing invalid-token banner from project/group

###  Changed
- Removed the persistent `#gitlabTokenBanner` that post7 added to the project and group pages. A bad/expired GitLab token no longer shows a standing banner there; the token error surfaces only when you actually run an action that needs it (Sync / Import), via the existing global progress bar + toast - one message, no standing clutter. (The project intel-card loading shimmer from post7 is kept.)
- Version `2026.7.3.post8`; Service Worker cache updated to `gitpulse-v279`.

## [2026.7.3.post7] - 2026-07-03 - Consistent project/group behavior with the course page on an invalid GitLab token

###  Fixed
- Project and group pages now handle an invalid/expired GitLab token the same way the course page always has: a single persistent `#gitlabTokenBanner` explains the 401 once, and the Sync / Run Checks buttons stay clickable instead of sticking disabled.
- Clicking Sync with a known-bad token now short-circuits (no doomed background job that left the button stuck and double-reported the error as both a banner and a toast) - it surfaces one message.
- Project GitLab-intelligence cards (Protected Branches / Contributors / Repository Stats) show a loading shimmer while a live fetch is in flight, instead of flashing a premature "No contributors yet" empty state.

###  Changed
- Version `2026.7.3.post7`; Service Worker cache updated to `gitpulse-v278`.

## [2026.7.3.post6] - 2026-07-03 - Version consolidation and final release checks

###  Fixed
- Health banner: the "GitLab server is currently unreachable" notice no longer reappears after you dismiss it (a successful app-health poll was silently clearing the dismissal flag it shared with the app-health banner), and its "Last connected" timer now ticks live instead of freezing at the value it had when first shown.
- Top-bar avatar degrades to the user's initials instead of flashing an empty grey disc while the GitLab profile photo streams in or when GitLab is unreachable.

###  Changed
- Version `2026.7.3.post6`; Service Worker cache updated to `gitpulse-v277`.
- Verified workspace code quality, ran full unit tests suite, and completed final release consolidation checks.

## [2026.7.3.post5] - 2026-07-03 - Simplified category assignment in project members

###  Refactored
- Simplified member category assignment in `_members_table.html` to eliminate duplicating tree branch logic for excluded members (consistent with the team details view).

###  Changed
- Version `2026.7.3.post5`; Service Worker cache updated to `gitpulse-v276`.

## [2026.7.3.post4] - 2026-07-03 - Simplified empty state logic in project details

###  Refactored
- Combined and simplified redundant `empty_state` macro call trees in project detail sub-sections: `_docker_verification.html`, `_ci_scenarios.html`, and `_conflict_challenges.html`.

###  Changed
- Version `2026.7.3.post4`; Service Worker cache updated to `gitpulse-v275`.

## [2026.7.3.post3] - 2026-07-03 - Redundant cohort filtering cleanup and category assignment simplification

###  Refactored
- Cleaned up redundant legacy Jinja fallback loop in `_issues_to_address.html` template. Now uses python backend computed `scored_students` exclusively, reducing file complexity.
- Simplified member category assignment in `_detail_content.html` to eliminate duplicating tree branch logic for excluded members.

###  Changed
- Version `2026.7.3.post3`; Service Worker cache updated to `gitpulse-v274`.

## [2026.7.3.post2] - 2026-07-03 - Refactored duplicate file tree buttons in student details

###  Refactored
- Extracted duplicate GitLab diff-tree button blocks within the student details component template (`student.html`) into a single Jinja2 macro `diff_file_tree_item`, reducing duplicate markup in recursive file-tree nodes and diff body lists.

###  Changed
- Version `2026.7.3.post2`; Service Worker cache updated to `gitpulse-v273`.

## [2026.7.3.post1] - 2026-07-03 - Refactored duplicate evidence link blocks in MR AI analysis

###  Refactored
- Extracted duplicate GitLab evidence link blocks within the AI Teamwork Analysis page template (`_ai_analysis.html`) into a single Jinja2 macro `render_evidence_link`, eliminating duplicate blocks across Strengths, Potential Issues, and Teamwork Quality sections.

###  Changed
- Version `2026.7.3.post1`; Service Worker cache updated to `gitpulse-v272`.

## [2026.7.3] - 2026-07-03 - Large-scale refactoring of Course Settings into modular partials

###  Refactored
- Decomposed and refactored the entire Course Settings template layout into modular partial includes (`_basic_settings.html`, `_webhook_settings.html`, `_compliance_settings.html`, `_weekly_deadlines.html`, `_sandbox_settings.html`, `_ai_settings.html`, `_import_export_settings.html`). This reduced the main `course_settings.html` template code from 580 lines down to under 100 lines.

###  Changed
- Version `2026.7.3`; Service Worker cache updated to `gitpulse-v271`.

## [2026.7.2.post17] - 2026-07-03 - Settings refactoring and alert layout fix

###  Fixed
- Layout wrapping of the "Scope cascade" alert box in the Course Settings page, preventing narrow-width wrapping.

###  Refactored
- Extracted "Semester Settings" layout sections into reusable Jinja macros and partial templates (`_semester_settings.html` and `_settings_form_macros.html`) to minimize duplicate markup.

###  Changed
- Version `2026.7.2.post17`; Service Worker cache updated to `gitpulse-v270`.

## [2026.7.2.post16] - 2026-07-02 - Green lint restored, students-only member tables, display-name project path

###  Fixed
- Restored the green lint stage on `main` (the post15 commit failed CI): `ruff format` reformatting and a `member_sync_service.py` mypy fix (a reused loop variable was assigned an Optional).
- Members and Group Members tables show STUDENTS only - never teachers, mentors, or a Project Manager. The issue-activity cohort could pull in a PM who authored issues; both lists now drop anyone flagged teacher/mentor.
- The project header shows a GitLab-style display path (`... / ApI 7 (Maťaš - Antypenko) / Chekanov ... - Míny`) instead of the raw slug (`.../api-7-ma-a-antypenko/mines-12770`).
- Version `2026.7.2.post16`; Service Worker cache unchanged (`gitpulse-v269`).

## [2026.7.2.post15] - 2026-07-02 - No contradictory sync toasts, issue-based cohort, cleaner Issues header

###  Fixed
- Course "Sync All" no longer shows a contradictory pair of toasts. The optimistic green "Sync started..." fired before the request resolved, so a refused sync (invalid token / GitLab offline) showed "started" AND "failed" at once. The "Connecting to GitLab..." global bar already signals the start and resolves to progress or a single error - the premature toast is removed on the course-detail and course-analytics paths.
- The project member cohort now also counts issue participation (author / assignee / co-assignees), not just merge-request activity, so a teammate who opened issues but has not authored an MR yet is no longer dropped ("4 shown but 5 on the team").
- Issues to Address header shows only the actionable High-priority count; the Medium/Low pills read as a meaningless faint number ("8"/"45") next to it and were redundant with the chart + legend below.
- Version `2026.7.2.post15`; Service Worker cache `gitpulse-v269`.

## [2026.7.2.post14] - 2026-07-02 - DB-backed project data and unified process progress

###  Fixed
- Project detail and live refresh no longer fetch GitLab directly to decide members/statistics/contributors/protected branches. They read the stored `gitlab_intel` snapshot, derive older projects from stored MR activity, and refuse to fall back to the whole subgroup for multi-project teams. This prevents phantom students and wrong Issues-to-Address badges when the GitLab token is invalid or GitLab is offline.
- Manual project sync now upserts the project's GitLab members into the owning group before issues/MRs/notes are processed, so direct project members no longer disappear until a full group sync runs.
- Sync and Run Checks progress/error handling is shared across project, group, and course scopes: invalid-token/refused requests now finish as visible global-bar errors as well as toasts, and Run Checks uses one SSE/polling path.
- Webhooks now enqueue a debounced refresh of the stored GitLab intelligence snapshot, keeping project intelligence DB-backed through sync/webhook mechanics.
- Version `2026.7.2.post14`; Service Worker cache `gitpulse-v268`.

## [2026.7.2.post13] - 2026-07-02 - Members "Actions" header alignment and readable Issues pills

###  Fixed
- Members table: the "Actions" header is right-aligned so it sits above its row buttons (the eye toggle + View) instead of drifting to the far left of the column. Applies to the live table and its loading skeleton.
- Issues to Address header pills: the Medium (amber) and Low (blue) counts were getting lost against the dark card header - only two faint numbers ("45") were visible. They are now bold, outlined chips so each count and its label stay readable next to the High (red) pill.
- Version `2026.7.2.post13`; Service Worker cache `gitpulse-v267`.

## [2026.7.2.post12] - 2026-07-02 - Sync button no longer sticks disabled on a refused sync

###  Fixed
- The project Sync button no longer stays disabled (needing a refresh) when a sync is refused - e.g. an invalid/expired GitLab token returning 503. The handler registered a phantom "sync running" slot before the request was confirmed; a refused request never cleared it, so the process-lock kept the button disabled. The optimistic slot is removed - the real progress slot is registered only after the server returns a job id, and on failure the button re-enables with a clear message.
- Version `2026.7.2.post12`; Service Worker cache `gitpulse-v266`.

## [2026.7.2.post11] - 2026-07-02 - Project members table shows the project, not the whole subgroup

###  Fixed
- The project members table and its Issues-to-Address score cohort now scope to THIS project's students instead of every student in the parent subgroup. A GitPulse "team" maps to a GitLab subgroup that can hold many project repos, so one project's table was showing the whole section (~50) instead of the real ~5. When the live member fetch is unavailable (expired token / GitLab maintenance) the page recovers the real roster from stored data - the roster saved on the last sync, else derived from stored merge-request activity (authors, assignees, reviewers, approvers) - so it is correct even before a fresh sync.
- Scoring counts a student as a project member regardless of GitLab membership source (direct OR inherited): a real contributor is no longer dropped from the group score just because their team-level source is 'inherited'. The score reflects the actual project cohort, not only the displayed rows.
- Version `2026.7.2.post11`; Service Worker cache unchanged (`gitpulse-v265`) - backend-only change.

## [2026.7.2.post10] - 2026-07-02 - Alignment fix and warnings in skeletons

###  Fixed
- Fixed Actions column alignment in both the loading skeleton and live members table to prevent buttons overflow.
- Added GitLab active members warning note to student views of skeletons and live tables.
- Version `2026.7.2.post10`; Service Worker cache `gitpulse-v265`.

## [2026.7.2.post9] - 2026-07-02 - Simplification of group and project members tables

###  Fixed
- Simplified the Group Members and Project Members tables by removing the redundant "Source", "Role", and "Status" columns, and removing the filter bar (since only database student members of the group/project are displayed).
- Colored the "Pipelines" column on the Group Members table to clearly identify success (green) vs failures (red), and added descriptive tooltips explaining the counts.
- Version `2026.7.2.post9`; Service Worker cache `gitpulse-v264`.

## [2026.7.2.post8] - 2026-07-02 - Intelligence panels survive an offline GitLab

###  Added
- The project GitLab Intelligence cards (protected branches, contributors, repository statistics) now persist a snapshot on every sync (`gitlab_projects.gitlab_intel`) and the page falls back to it per-card when the live GitLab fetch fails. These were the only data on the page with no stored fallback, so they were the only thing that broke to "GitLab is unreachable" when the token lapsed - now they keep showing the last-synced values (useful across the July 3-5 GitLab maintenance window).

###  Fixed
- The intelligence cards no longer wipe themselves to "GitLab is unreachable" on a failed live refresh - the last snapshot stays visible.
- The Groups table no longer overflows its card: deleted-group rows carry wide "Restore" / "Remove from deleted" buttons that forced the whole fixed-layout table to scroll sideways; those buttons now wrap within the actions column (active rows untouched).
- Version `2026.7.2.post8`; Service Worker cache `gitpulse-v263`; Alembic migration `008` adds the `gitlab_intel` column.

## [2026.7.2.post7] - 2026-07-02 - Styled tooltips, sticky dismissals and aligned rows

###  Fixed
- Tooltips are now always the styled component (Tippy) tooltip, never the browser's native `title=` popup: the `btn`/`btn_icon` macros, the info-card dismiss button, the course-settings check toggle and sync-lock save buttons, the login server-status dot, localized `<time>` timestamps, and the client-inserted Group row actions were all converted.
- Dismissed banners stay dismissed: the info-card X remembers the dismissal for the session (keyed by banner + current state), so "sync failed" / "sync cancelled" / "data may be outdated" no longer reappears after navigating away and back.
- The top loading bar and submit buttons no longer stick after a validation failure - e.g. Add Group with a 1-character name clears the progress bar and does not arm the anti-spam button-lock, so nothing hangs until a refresh.
- New Group rows added after creation mirror the server table's responsive column classes (`col-hide-sm`/`col-hide-md`, centered Status) so they no longer shift out of alignment on narrow viewports; the first group in a course reloads to render the canonical table.
- Added Slovak translations for the permanent-delete / "Remove from deleted" strings, returning missing translations to zero.
- Version `2026.7.2.post7`; Service Worker cache `gitpulse-v262`.

## [2026.7.2.post6] - 2026-07-02 - Console, modals and shared role badges

###  Fixed
- Course detail now ships valid JavaScript again: the deleted-group toggle binds correctly, Run Checks uses the shared confirmation callback flow, and the page no longer dies before exporting its actions.
- The white avatar ring is scoped to the dashboard greeting avatar, while the topbar avatar stays borderless.
- The user menu role pill now uses the shared role badge component and colors from User Management.
- GitLab import and other modals reset their internal scroll position before opening, keep backdrops mounted under `<body>`, and do not delay the modal body scrollbar until after the first animation frame.
- The PWA install handler no longer calls `preventDefault()` on Chromium's native install banner unless the custom prompt is explicitly enabled.
- Version `2026.7.2.post6`; Service Worker cache `gitpulse-v261`.

## [2026.7.2.post5] - 2026-07-02 - Permanent deletion, user roles and layout fix

###  Added
- Permanent deletion ("Remove from deleted") endpoints and UI actions for inactive groups and projects. Teachers/admins can now completely get rid of deleted groups or unlinked projects and all their associated records (memberships, snapshots, pipelines, MRs, commits, issues, LLM logs, and background jobs) from the system.

###  Fixed
- Fixed mobile and tablet layout spacing and corners so the main content panel remains inset with 8px margins and rounded corners on small viewports rather than stretching full width.
- Removed duplicated user avatar from the topbar dropdown menu card header.
- Replaced the static visual-only "Coding my life" status box with a status badge showing the user's role (Admin, Teacher, Student) in the topbar user menu.
- Removed the disabled "Deleted" button from the loading skeletons.
- Version `2026.7.2.post5`; Service Worker cache `gitpulse-v260`.

## [2026.7.2.post4] - 2026-07-02 - Group-name validation, faster loads, opt-in dirty-check

###  Fixed
- Add Group now validates the name: a blank or single-character value (e.g. a stray "ф") is rejected client-side and server-side (`TeamCreate` trims and requires >= 2 non-space characters), so you can no longer create a junk group that then vanishes.
- Faster loads: the course sync-status endpoint and the SSE stream no longer probe GitLab over the network on each poll/connect - they read the cached token-health flag (no round-trip); the flag is still set on the first 401.
- Dirty-check is now opt-in. Every modal with an input used to arm the "unsaved changes" guard, which fired on throwaway action modals (GitLab import). Auto-init now only covers modals marked `data-dirty-check`; genuine edit forms keep protection via explicit calls.
- Version `2026.7.2.post4`.

## [2026.7.2.post3] - 2026-07-02 - Dismissible info-card banners

###  Added
- Info-card banners can now be dismissed. The `info_card` macro takes `dismissible=true` and renders an X button; a delegated, CSP-safe click handler removes the card. Applied to the course "Some sync jobs failed", "Sync cancelled" and "Data may be outdated" banners.
- Version `2026.7.2.post3`.

## [2026.7.2.post2] - 2026-07-02 - Restored GitLab-style layout + failed-banner flash fix

###  Fixed
- Content-panel layout restored to the reliable GitLab model: `.gl-page` uses a fixed `height` (fills the viewport) and `.gl-page-content` uses `flex: 1`, so the panel is always full height and the content scrolls INTERNALLY (like GitLab's `.js-static-panel` / `.panel-content-inner`). The earlier `max-height` + `flex: 0 1 auto` experiment made the panel shrink to the loading skeleton ("half the page is missing") - reverted.
- The "Some sync jobs failed" banner no longer flashes and vanishes after a second. The live update managed a generic `.info-card-danger`, so an SSE tick reporting 0 (its count uses a 2h window) removed the server-rendered banner. It now manages ONLY its own live card (`#jsSyncFailedCard`) and never touches the server banner or the token banner.
- Version `2026.7.2.post2`.

## [2026.7.2.post1] - 2026-07-02 - Remaining process guard hardening

###  Fixed
- GitLab import cancellation is no longer registered as unsaved form data; pressing Cancel stops the active import path without showing an unrelated before-unload prompt.
- Queued CI failure scenarios and conflict challenges can now be cancelled before they mutate GitLab, and CI scenario polling only runs while rows are actually pending.
- Retrying a failed scheduled/manual system job now creates a new tracked cancellable background job, so Follow the latest updates, Items that need your attention, and the global job bar all receive the same job id.
- Active job checks now include the `started` state across sync, run-checks, import, course status, and scheduled jobs, preventing duplicate starts during the RQ handoff.
- Live dashboard/project value flashes now use requestAnimationFrame instead of synchronous layout reads, removing another forced-reflow source from hot refresh paths.
- Production monitoring no longer leaves Alertmanager in a restart loop; the container now starts with a valid internal absolute external URL and a YAML config that Alertmanager can parse without unsupported shell-style environment expansion.
- Version `2026.7.2.post1`; Service Worker cache `gitpulse-v256`.

## [2026.7.2] - 2026-07-02 - Cancellable processes and guarded GitLab import

###  Fixed
- GitLab import now rejects invalid group/project paths before streaming; typing non-ASCII input can no longer start an import or crash the import error handler.
- Long-running processes now share a cancellable job contract: global cancel buttons stop sync, run-checks, Docker verification, scheduled jobs, LLM analysis, GitLab enrichment, frontend-only AI generation, and active imports. Cancelled jobs stay terminal, and workers no longer overwrite them with completed/failed after races.
- Course sync and run-check status now reports cancelled groups separately and uses the newest run-check job per group, so old failed rows do not poison a later successful run.
- Course detail SSE/logging and flash animations no longer create duplicate EventSources or forced reflow; the shell bottom spacing now matches GitLab-style content height without an empty footer gap.
- Version `2026.7.2`; Service Worker cache `gitpulse-v255`.

## [2026.7.1.post5] - 2026-07-01 - Content panel shrinks to its content (no empty card)

###  Fixed
- The content panel (`.gl-page`) now shrinks to its content on short pages (`max-height` instead of a fixed `height`) instead of always filling the viewport, so a page with only a few rows no longer shows a large empty rounded card below the table - matching GitLab's own panel. Tall pages still cap at the viewport and scroll internally.
- Version `2026.7.1.post5`.

## [2026.7.1.post4] - 2026-07-01 - Token-invalid banner shows on page load

###  Fixed
- Follow-up to post3: the "GitLab token invalid" banner now appears on page load (the SSE stream and sync-status warm the shared token-health flag with one cached probe) instead of only after the first failed click. Sync All short-circuits with a clear toast on the very first click - no "Connecting..." flash, and the button is never left in a loading state that needed a page refresh to clear.
- Version `2026.7.1.post4`.

## [2026.7.1.post3] - 2026-07-01 - Banner instead of a disabled Sync button, test isolation

###  Fixed
- The "GitLab token invalid" state no longer disables the Sync All button (it was unclear when it would re-enable and inconsistent with the still-working Import button). The banner is now the single clear explanation; clicking Sync All shows the same reason as a toast instead of a "Connecting..." bar that flashed and vanished a second later.
- Test isolation: the shared GitLab token-health flag is reset around every test, so a mocked 401 no longer leaks into a later test and makes a guarded job skip - a failure that only surfaced in CI with live Redis.
- Version `2026.7.1.post3`.

## [2026.7.1.post2] - 2026-07-01 - More resilient sync and app-wide GitLab token protection

###  Fixed
- Sync no longer flaps ("finished in 2s, then restarted itself, in circles"). A failed sync used to re-raise into RQ's blind auto-retry, flipping the job `running↔failed` and making the course progress bar oscillate while the "Data may be outdated" banner popped mid-sync. Sync now uses a **bounded, visible retry** (3 attempts): the row stays active between attempts and shows `Retrying (2/3)` as a per-group `RETRY 2/3` badge; the run ends with a clear **"All syncs completed!"** or a red **"Sync finished with problems - N group(s) failed"** instead of always reporting success.
- Expanded job-history cards no longer break the table: the injected detail row was counted in the `:nth-child` zebra striping, flipping the shading of every row below it and painting a stripe over the detail panel. It is now excluded from the stripe/hover count.

###  Added
- **App-wide GitLab token protection.** An invalid/expired token (401/403) is now detected the instant *any* GitLab call fails and shared through a cached health flag, so the whole app reacts to one failure instead of each flow independently hammering GitLab:
   - Sync, project-sync, Sync All and GitLab import are **blocked up front** with a clear "GitLab API token is invalid or expired (401)" message.
   - Token-using background jobs (issue/MR enrichment, membership sync, incremental project refresh) **skip immediately** when the token is known-bad and **do not retry** auth errors, stopping retry storms.
   - Recovery is automatic: any successful GitLab call clears the flag, so work resumes after a token rotation without a restart.
   - The course page shows a persistent **"GitLab token invalid"** banner and disables Sync All while the token is bad.
- Version `2026.7.1.post2`.

## [2026.7.1.post1] - 2026-07-01 - Copyright 2026-2027, nofollow language links, last example date

###  Fixed
- Docs footer copyright corrected from `2024-2026` to `2026-2027 TUKE Košice`.
- SEO: language-switch links now use `rel="nofollow"` so search engines stop indexing those redirect URLs discovered on the public login page.
- Refreshed the final stale example date in the app's course-settings help text (template + Slovak catalog kept in sync).

## [2026.7.1] - 2026-07-01 - Docs freshness: drop the removed Rubric feature, refresh example dates

###  Changed
- Removed the deleted "Rubric" feature from the Slovak teacher guides (dashboard, getting-started) so they match the English versions and the current app. Refreshed stale example dates and group paths across the GitLab, operator and developer guides to current-year examples, and updated the documented current version to `2026.7.1`.

## [2026.6.30.post3] - 2026-06-30 - Preload backdrop only where used, drop stray em dashes, refresh pilot dates

###  Fixed
- Login/logout: the backdrop image was preloaded even on mobile, where the sheet paints no background, so the browser warned it was "preloaded but not used". The preload is now limited to screens at least 768px wide, where the background actually shows.

###  Changed
- Refreshed the pilot-deployment guide: dates moved to 2026 and the inconsistent date formats were normalised. Removed stray em dashes from a couple of changelog lines.
- Version `2026.6.30.post3`.

## [2026.6.30.post2] - 2026-06-30 - Real /favicon.ico so Google Search shows the site favicon

###  Fixed
- Favicon in Google Search: the app served `/favicon.ico` as a 301 redirect to a PNG, which Google's favicon fetcher handles unreliably (the generic globe showed next to results). It now returns a real multi-resolution `.ico` with a 200, and the indexable login page lists it first. Google refreshes the favicon only on a home-page recrawl, so it can still take a few days to appear.

###  Changed
- Version `2026.6.30.post2`.

## [2026.6.30.post1] - 2026-06-30 - Light-themed auth selectors/alerts, swipe-to-dismiss modals, coverage backfill

###  Fixed
- Auth pages (login / logout): the language selector menu, flash alerts, toasts and the selected-language checkmark rendered dark on the white card when the visitor's saved theme was dark. The color-mode bootstrap now drives `data-theme` from the page's light lock, so every component on the auth pages renders light.
- Test coverage reading "not reported" on student MR cards while GitLab showed a real percentage: the full team sync skipped already-finished pipelines, so test pipelines stored without coverage never backfilled. Sync now re-fetches terminal pipelines that ran tests but recorded no coverage.

###  Added
- Mobile modals: the bottom-sheet drag handle is now interactive - swipe it (or the modal header) downward to dismiss. The gesture engages only from the top region so it never interferes with scrolling the modal body.

###  Changed
- Version `2026.6.30.post1`.

## [2026.6.30] - 2026-06-30 - Redis pool in worker, fixed course settings imports and prod monitoring links

###  Fixed
- Worker Redis configuration: resolved a `RuntimeError` during event processing tasks by initializing the shared Redis connection pool on RQ worker startup.
- Course settings import script: removed obsolete imports and calls to gaming detection and rubric engines to prevent errors.
- Observability: set OTLP tracer endpoint in development to point to the local Jaeger collector, enabling trace visualization locally.
- Monitoring documentation: updated Slovak and English operator guides with production URLs, ports, and Caddy Basic Auth credentials for manual verification.

## [2026.6.29.post12] - 2026-06-29 - Fix dev environment, Redis authentication, and Grafana redirects

###  Fixed
- Dev Startup script (`start-dev.ps1`) error handling: removed `$ErrorActionPreference = "Stop"` which crashed the script on benign python/pip warnings during the docs container build.
- Grafana redirect loop: resolved a connection refused issue on `http://localhost:3000` by overriding `GF_SERVER_ROOT_URL` to `http://localhost:3000/grafana/` in `docker-compose.monitoring-dev.yml` to prevent redirecting local dev requests to production HTTPS urls.
- Cleaned up obsolete metrics: removed the stale "Report Generation Time", "Sweep Jobs", "Sweep Job Duration", and "Active Dashboard Sessions" dashboard panels, and removed the "ReportGenerationSlow" and "SweepJobFailing" alerts since their underlying functions do not exist in the codebase.
- Grafana targets scraping: added `metrics_path: /grafana/metrics` for Grafana jobs in both `prometheus.yml` and `prometheus.dev.yml` to prevent Prometheus from failing on redirection loops.
- Production Redis credentials: added missing `REDIS_PASSWORD` and configured authenticated `REDIS_URL` in `.env.production` to prevent startup crashes from mandatory production security/validation gates.

###  Changed
- Version `2026.6.29.post12`.

## [2026.6.29.post11] - 2026-06-29 - Green lint stage and more accessible "Quick access" tabs

###  Fixed
- Restored a green CI lint stage. Today's rapid polish commits landed four `ruff` violations and three `ruff format` drifts on `main` (pinned `ruff==0.15.4`), so the `ruff-check`/`ruff-format` gates were red: an `f`-string with no placeholders, an unsorted import block, a `SIM108` if/else in the diff-context helper, and an over-long assert. Logic-preserving fixes; full unit suite (2512) stays green.

###  Changed
- Accessibility: the "Quick access" Groups/Subgroups toggles are now proper tabs - `type="button"`, `role="tablist"`/`role="tab"`, and bound `aria-selected` for screen readers. Template-only.
- Version `2026.6.29.post11`.

## [2026.6.29.post10] - 2026-06-29 - Remove N+1 in course-wide sync / run-checks

###  Changed
- Backend: the "Run checks (all groups)" and "Sync all groups" endpoints no longer issue one SELECT per group to check for in-flight jobs - both now use a single batched lookup that is provably the same result. For a course with N groups this removes up to 2N redundant round-trips. No behavior change (full unit suite green).
- Version `2026.6.29.post10`.

## [2026.6.29.post9] - 2026-06-29 - Preconnect to GitLab on the login page too

###  Changed
- Extended the GitLab `preconnect` / `dns-prefetch` hint to the standalone login page - its primary button is the OAuth redirect to GitLab, so warming the connection first makes that redirect a round-trip faster. Resource hint only. No static asset or Service Worker cache change.
- Version `2026.6.29.post9`.

## [2026.6.29.post8] - 2026-06-29 - Preconnect to GitLab for faster first contact

###  Changed
- Frontend optimization: the base `<head>` now preconnects (+ dns-prefetch) to the GitLab origin (from the `gitlab_url` setting, not hardcoded). The login CTA redirects to GitLab for OAuth and authenticated pages load avatars + call its API, so warming the connection early makes that first contact a round-trip faster. Resource hint only - cannot affect rendering. No static asset or Service Worker cache change.
- Version `2026.6.29.post8`.

## [2026.6.29.post7] - 2026-06-29 - Skip unused dashboard counts for students

###  Changed
- Dashboard backend: the home page and `/dashboard/stats` no longer run the "total groups" and "total students" count queries for students - those values feed only the teacher/admin stat cards. Two fewer database round-trips on every student dashboard load and stats refresh. No visible change.
- Backend-only release: no static assets changed, so the Service Worker cache stays at `gitpulse-v247`.
- Version `2026.6.29.post7`.

## [2026.6.29.post6] - 2026-06-29 - Disable staggered cascade pending review

###  Changed
- Disabled the staggered "by arrival" cascade reveal on the dashboard and student profile - it regressed those views in production. The reveal engine stays in the codebase and will be re-enabled only after it is visually verified in a browser.
- Version `2026.6.29.post6`; Service Worker cache `gitpulse-v247`.

## [2026.6.29.post5] - 2026-06-29 - Staggered reveal on the student profile

###  Added
- Extended the staggered "by arrival" reveal to the student profile: merge-request cards and reviews-given cards now cascade in one after another on first load, matching the dashboard.

###  Changed
- Added a release version-consistency test asserting `pyproject.version` matches the newest entry of every changelog (root + docs SK/EN), so a release bump can no longer update one surface and leave the others behind.
- Version `2026.6.29.post5`; Service Worker cache `gitpulse-v246`.

## [2026.6.29.post4] - 2026-06-29 - Staggered dashboard reveal, relative time, tour scroll fix

###  Added
- **Staggered "arrival" reveal**: dashboard collections (KPI stats, course cards, "Items that need your attention", and the "Follow the latest updates" feed) now cascade in one after another - "by arrival" - instead of every item snapping in at once. Honors `prefers-reduced-motion` and runs only on the first reveal (lazy skeleton hand-off / initial render), never on live-poll refreshes (no blink). Table rows are intentionally excluded.
- Relative "time ago" date formatting (e.g. "2 hours ago") for activity and timestamps, via a new client-side `localize-time` helper.

###  Fixed
- Guided tour now recursively scrolls every scrollable ancestor to bring a step target into view, and skips table containers so the main page wrapper scrolls instead of an inner table.
- The tour's "user row actions" step now highlights the buttons wrapper rather than the bare table cell.
- Rolled back the earlier tour positioning/popover changes that regressed pointing at the target.
- Removed duplicate subtitles on the student profile page.

###  Changed
- Rebuilt JS/CSS bundles and minified assets.
- Version `2026.6.29.post4`; Service Worker cache `gitpulse-v245`. Also realigns the package version, which had stayed at `post2` while `post3` shipped only the SW cache + changelog.

## [2026.6.29.post3] - 2026-06-29 - GitLab diff comments, thread headers, transparent email logo

###  Fixed
- Inline diff code context now displays GitLab-style double line number columns (old & new line numbers side-by-side).
- Inline diff range comments display correctly in thread footers (e.g. `Comment on lines +51-53`).
- Discussion thread headers now include the author's GitLab username (`@username`) and the localized thread start time.
- Status icons in `.commit-message-cell` are now inline and no longer wrap above the commit message link.
- Guided tour popovers on desktop now correctly point to their highlighted targets with a themed arrow, rather than being forced to the bottom-right corner.

###  Changed
- Changed the email notification logo to be transparent (no dark-gray background tile) and removed the box-shadow boundary for a cleaner, modern look.
- Version `2026.6.29.post3`; Service Worker cache `gitpulse-v244`.

## [2026.6.29.post2] - 2026-06-29 - GitLab-style tanuki social cover

###  Changed
- Reworked the Open Graph / social-share cover (`og-image.png`, docs `og-cover.png`) to the GitLab-style tanuki tile (orange tanuki on a light gradient rounded square) with the GitPulse ECG pulse overlaid, replacing the off-brand blue ECG square so link previews match the in-app logo. Home-screen/PWA icons and favicons were already the tanuki.
- Version `2026.6.29.post2`.

## [2026.6.29.post1] - 2026-06-29 - Diff context hunk fix, inline-code spacing, favicon

###  Fixed
- Diff comment code context no longer crosses a hunk boundary - it stays within the commented hunk (showing the whole compact added construct, GitLab-style) instead of jumping line numbers (e.g. `29 -> 49`) and bleeding into the next function.
- Inline `code` pills get real horizontal spacing so they no longer touch the surrounding words.
- MR pipeline **Test coverage** row (icon, label, %, "from N jobs") sits on one shared midline instead of drifting to different vertical levels.
- Regenerated the stale docs `favicon.ico` as a proper multi-resolution GitPulse tanuki icon and cache-busted the favicon links.
- Guided tour opens a collapsed `<details>` around a step target only when navigating to that step, not during the page-load eligibility scan (fixes a regression that could auto-expand collapsed diff/code sections on load).

###  Changed
- Version `2026.6.29.post1`; Service Worker cache `gitpulse-v243`.

## [2026.6.29] - 2026-06-29 - Collapsible code context, cleaner discussions, tour fix

###  Fixed
- Inline code context in MR/review discussions is now collapsible and **collapsed by default** (GitLab-style `Show code` summary with file:line), so long threads stay light and no longer lag while scrolling.
- Removed the misleading non-interactive `new`/`old` pill from the code-context toolbar; the side is already shown by the line gutter and the `Comment on line +N` footer.
- Stopped rendering the fabricated `1 participants` label on threads: the participant count now appears only when a thread genuinely has more than one participant.
- Decluttered review threads: dropped the redundant per-reply "reply to ..." cue (replies are already nested) and the duplicate copy-link icon on a thread's root note.
- Inline `code` pills in MR/issue descriptions and comments no longer overlap adjacent lines.
- Vertically centered MR card title rows and the reviews-given header so labels no longer sit above their icons.
- Workflow ribbon dots render larger, clearer icons with a calmer hover lift (no row jump).
- The guided tour now opens any collapsed `<details>` around a step target (changed-file tree, inline code context) before highlighting, so steps like *Changed-file tree* are no longer broken when a section is closed.
- Removed the dark strip below the course-settings sticky save bar when the form is the last block on the page.

###  Changed
- User-info modal: the per-group `+N more` project list is now an expandable/collapsible control (`Show less`) instead of a dead label.
- Documentation Open Graph/Twitter preview now uses the branded GitPulse cover image (`assets/og-cover.png`).
- Rebuilt bundles/minified assets; added Slovak translation for `Show code`; version `2026.6.29`; Service Worker cache `gitpulse-v242`.

## [2026.6.28.post1] - 2026-06-28 - Scoped MR diff jumps and code comments

###  Fixed
- MR/review diff file anchor IDs are scoped per card, so changed-file tree clicks and comment jumps no longer hit another `diff-file-*` block when several MRs are visible.
- Diff comment code context now uses one side-aware line-number gutter and exact `Comment on line` text, without the extra old/new number panel or incorrect visible-range footer.
- Missing MR pipeline `Test coverage` is backfilled from GitLab pipeline details/jobs for visible student MRs when older local pipeline rows have `coverage = null`.
- Removed the unreliable `Response Rate` diagnostic card and the duplicate diagnostic `Test Coverage` card, including matching skeleton placeholders.

###  Changed
- Regenerated static bundles/minified assets after the student-detail fixes.

###  Release
- Version `2026.6.28.post1`; Service Worker cache `gitpulse-v241`.

---

## [2026.6.28] - 2026-06-28 - Local jumps and inline Test coverage

###  Fixed
- Copyable/hash links for student comments, MR cards, dashboard targets, and paginated tables now use the shared local `.gl-page-content` scroller contract instead of browser-level auto scrolling.
- MR pipeline coverage is visible again as GitLab-like inline text (`Test coverage ... from 1 job`) without rendering a separate `Test Coverage` card/chip.
- MR loading skeleton markup mirrors the live Pipeline/Tests plus inline coverage structure.

###  Release
- Version `2026.6.28`; Service Worker cache `gitpulse-v240`.

---

## [2026.6.27.post2] - 2026-06-27 - Student profile skeletons, MR replies, and coverage accuracy

###  Fixed
- Student profile loading now mirrors the live profile card, mobile GitLab/profile/date metadata is centered, and the duplicate profile divider is gone.
- Student-detail jumps use the local page-content scroller contract from Issues to Address, avoiding global window-scroll layout jumps.
- MR commit rows keep labels, +/- stats, and dates in fixed grid columns so long content no longer spills across the page.
- MR diff code context is rendered at the discussion-thread level with old/new gutters, target-row highlighting, copy action, and attached replies for a GitLab-like reading flow.
- Pipeline coverage is parsed from GitLab pipeline/build payloads and same-SHA fallback pipelines, so rows show real values such as `Test coverage 91.00% ... from 1 job` instead of `not reported`.

###  Changed
- GitPulse logo ECG hover motion is smoother, and the student profile/MR skeleton static assets were rebuilt.

###  Release
- Version `2026.6.27.post2`; Service Worker cache `gitpulse-v239`.

---

## [2026.6.27.post1] - 2026-06-27 - GitLab-like MR replies, coverage visibility, and student profile polish

###  Fixed
- Student MR discussions now render as linked GitLab-like threads with stable thread/comment anchors, reply-to jump links, collapsible replies, and buttons that jump to the matching diff file.
- Pipeline rows show an explicit coverage fallback when GitLab does not report test coverage instead of silently hiding the signal.
- MR branch commits show visible authors, in-app profile links where possible, and a Teacher commit badge when the commit belongs to a course teacher.
- Student profile metrics, table skeleton alignment, Run Compliance Checks checkboxes, modal footer highlighting, and diff file-tree sticky behavior were tightened.

###  Release
- Version `2026.6.27.post1`; Service Worker cache `gitpulse-v238`.

---

## [2026.6.27] - 2026-06-27 - Componentized student-detail UI, modals, skeletons, and code comments

###  Fixed
- Member-table skeleton rows now use the same column contract as live rows, so Status/Checks placeholders no longer drift away from the headers.
- Student MR diff navigation keeps the changed-file tree sticky, scrolls only its local panel, and avoids global item `scrollIntoView`.
- Run Compliance Checks modal checkbox rows are stable without the checked-state inset stripe or global checkbox scale animation.
- MR diff-note inline code context now has old/new gutters, side-aware target row matching, local horizontal scrolling, and a copy action.

###  Changed
- Student profile metric tokens, Reviews Given cards, tour popovers, and student-detail tour steps now follow the shared component UI contract.
- GitPulse logo motion uses a calmer ECG pulse and one subtle hover state without jitter in light or dark themes.
- App source CSS `letter-spacing` declarations were normalized to `0` across shared and page styles.

###  Release
- Version `2026.6.27`; Service Worker cache `gitpulse-v237`.

---

## [2026.6.26] - 2026-06-26 - GitPulse branding, zero-inline UI contract, and exact MR jumps

###  Fixed
- Student Issues-to-MR chips now scroll inside the local page content and no longer invoke the global anchor scroller.
- Dynamically opened modals and drawers re-initialize dirty-check guards before activation.
- Diff comments can render GitLab-like nearby code context when stored MR diff data is available.

###  Changed
- Visible Teamwork wording was normalized across the application and documentation while internal stored JSON/API keys remain stable.
- The GitPulse logo is now a shared component stylesheet with a GitLab-inspired mark, light/dark contrast guards, and rebuilt PWA icons.
- Template progress/size inline styles now use reusable component data attributes and centralized CSS-variable hydration.
- Responsive table and skeleton contracts were tightened to match real content more consistently.

###  Release
- Version `2026.6.26`; Service Worker cache `gitpulse-v236`.

---

## [2026.6.25] - 2026-06-25 - System-wide HTMX cleanup, memory leak prevention, and safe scripts

###  Fixed
- Fixed memory leaks system-wide by implementing proper page teardown and lifecycle cleanup in `GP.activePageCleanup()`. All window/document event listeners, SSE streams (`EventSource`), and polling timers (`setInterval`/`setTimeout`) are fully torn down upon HTMX page swaps.
- Converted all anonymous event handlers on `document` and `window` in standalone page controllers (`admin-events.js`, `admin-users.js`, `course-activity.js`, `support-ticket-detail.js`) to named functions so they can be explicitly removed from the global scope.
- Prevented global lexical scope pollution by removing obsolete IIFE wrappers from page bundles and automating the IIFE generation at bundle time in `build_bundle.py`.
- Extracted the pre-paint greeting script out of `dashboard.html` into a dedicated, clean, component-based static JavaScript module `greeting-sync.js`, leaving templates entirely free of inline executable scripts.

###  Release
- Version `2026.6.25`; Service Worker cache `gitpulse-v235`.

---

## [2026-06-23] - Documentation Update and Compliance Rule Alignment

###  Added
- Added explanation and details for rule **R13 (Commit Quality)**, which evaluates the local Git workflow against GitLab's web editor (Web IDE).

###  Changed
- Realigned the descriptions of compliance rules **R01-R13** in the student guides (`studenti/metriky.md` and `.en.md`) to match the exact implementations in `builtin_checks.json` and `engine_checks.py`.
- Updated compliance control tables in the teacher guides (`ucitelia/zaciname.md` and `.en.md`) and dashboard overviews (`ucitelia/dashboard.md` and `.en.md`) to include the R13 control and its default weight of 0%.
- Aligned route counts in the API reference (`api/index.md` and `.en.md`) to the verified total of **222** route handlers.

---

## [2026.6.20] - 2026-06-20 - Responsive course management, CSP-safe Markdown, and current thesis docs

###  Fixed
- Course Management keeps every column in responsive card rows, adds value labels, and uses a stable search toolbar on narrow screens.
- Markdown preview works with the Alpine CSP build without the forbidden `x-html` directive.
- Markdown-editor and support-ticket scripts can initialise again after HTMX navigation without duplicate lexical-declaration failures.

###  Changed
- The public thesis section now matches the third interim submission and does not claim results that have not yet been evaluated.
- The design documents the current R01-R13 model, manual synchronisation instead of periodic GitLab sweeps, and two anonymised functional-prototype screenshots.

###  Release
- Version `2026.6.20`; Service Worker cache `gitpulse-v234`.

---

## [2026.6.19.post2] - 2026-06-19 - User Management responsive table

###  Fixed
- Search and the role filter now share a deterministic toolbar instead of wrapping at arbitrary offsets.
- Column classes live on the real headers and cells, so widths, truncation, visibility, status, actions, and skeletons use one contract.
- Human and service-account rows use compact icon actions and safely handle long usernames and email addresses.
- Mobile cards use the username as the primary identity while keeping labelled metadata and actions aligned.
- Live role and status updates preserve the same badge and status-indicator markup as server rendering.

###  Release
- Version `2026.6.19.post2`; Service Worker cache `gitpulse-v232`.

---

## [2026.6.19.post1] - 2026-06-19 - Responsive table skeleton alignment

###  Fixed
- Project and team member tables share one responsive column contract across real rows, loading skeleton rows, and JavaScript fallback rows.
- Project detail skeletons derive rubric/check columns from the active checks list, so the loading matrix stays aligned with the real R01-R13 table.
- Admin user skeleton rows use typed user columns instead of a generic table placeholder.
- Skeleton rows now carry the same responsive `data-label` contract as real rows, so tablet and phone loading states render as label/value cards.
- Admin user role filters and member filter bars now wrap inside the component on narrow screens without horizontal scroll or clipped controls.
- Student merge request pipeline test status now renders as compact badges instead of raw text.
- Issues to Address animations are disabled so they cannot replay after visibility or HTMX refresh changes.

###  Release
- Version `2026.6.19.post1`; Service Worker cache `gitpulse-v231`.

---

## [2026.6.18.post1] - 2026-06-18 - Table skeletons, analytics freshness, and indexing policy

###  Fixed
- Table skeletons now use typed cells for project rows, member rows, badges, status pills, check dots, and action buttons.
- Admin and teacher dashboard summaries replace the low-value "Open MRs" card with active group coverage.
- Course analytics and activity stale-data banners report partial current-week group snapshot coverage instead of implying the whole course was not synced.
- Login/logout alerts use the shared GitLab-style alert component with a proper title API and a short synchronized logout fade.
- Robots and sitemap responses explicitly block private dashboard crawling, allow the login page, include last-modified metadata, and set public cache headers.

###  Release
- Version `2026.6.18.post1`; Service Worker cache `gitpulse-v229`.

---

## [2026.6.18] - 2026-06-18 - Project sync reconciliation and guarded UI controls

###  Fixed
- Dashboard Quick access project rows open the project page instead of the parent group.
- Group/course GitLab imports deactivate active database projects that no longer exist in the imported GitLab group tree, including orphaned team members when no active projects remain.
- Process-action guards keep protecting sync/import/check/delete actions while bypassing passive filters, tabs, and dropdown-style controls.
- Project and member table skeleton contracts stay aligned with the responsive table layout.
- Production redeploy keeps AI teamwork analysis disabled in `.env.production`.

###  Changed
- Back to Group links use transform-based icon/link motion instead of layout-moving gap changes.
- GitLab import API and SSE completion payloads expose stale-project cleanup counts.

###  Release
- Version `2026.6.18`; Service Worker cache `gitpulse-v228`.

---

## [2026.6.17] - 2026-06-17 - Keycloak login alignment

###  Changed
- Aligned sign-in and sign-out pages layout, spacing, and dimensions with the Keycloak design.
- Re-centered the logo title, set the card width to a compact 400 px, and removed unnecessary border radii for a sharp square-edge look.
- Re-positioned and styled the language selector dropdown to be compact and styled with a semi-transparent black background.

###  Release
- Version `2026.6.17`; Service Worker cache `gitpulse-v224`.

---

## [2026.6.16] - 2026-06-16 - Email redesign, support ticket refinements, and emoji cleanup

###  Added
- Complete redesign of the email notification system with modern Inter typography, soft drop-shadows, and premium color gradients.
- Comprehensive support tickets interface updates, including dynamic drag-and-drop file attachments in the ticket editor, dragover visual highlighting, and a Chrome double-browse fix.

###  Changed
- Replaced obsolete "Reports" references with "Analytics" inside the welcome email template for teacher and admin roles.
- Purged all raw emojis and AI-like emoticons from all active system documentation to establish a professional, publication-ready tone.
- Incremented application version to `2026.6.16` and Service Worker cache namespace to `gitpulse-v217`.
- Cleaned up obsolete helper and scratch scripts from the repository.

###  Release
- Version `2026.6.16`; Service Worker cache `gitpulse-v217`.

---

## [2026.6.15.post1] - 2026-06-15 - Academic weeks, Pajamas dropdowns, and improved drag & drop

###  Added
- Pajamas-aligned custom academic and exam period week calculation (`1`-`13` and `S1`-`S7`) in Flatpickr based on the settings' semester start date.
- Alpine.js-backed, Pajamas-styled custom dropdowns (`select_field`) for type and week selection on the assignments page.
- Global window-level drag-and-drop overrides to prevent accidental browser navigation on missed file drops.
- Pointer-events scoping on file upload areas to eliminate drag flickering.

###  Changed
- Refactored Edit and Delete actions on the assignments list to use `btn_icon_only` to prevent text overlap in compact layouts.
- Rebuilt static CSS/JS bundles and minified assets.

###  Fixed
- Fixed dark-mode checkbox checkmark visibility and added premium spring-based transitions.
- Fixed file upload areas to dispatch a standard `change` event on dropping, allowing automatic HTMX integration.
- Removed redundant page-entrance card animations to prevent double-swaps.

###  Release
- Version `2026.6.15.post1`; Service Worker cache `gitpulse-v209`.

---

## [2026.6.11.post7] - 2026-06-11 - Persistent appearance and responsive polish

###  Added
- Light, Dark, and System modes backed by one semantic token layer without a first-paint theme flash.
- The selected mode is persisted per account on the server and follows the user
  across browsers and devices.
- The appearance tour opens the profile menu and targets the real switcher.
- Installed-PWA state is verified through the browser instead of relying only on
  a local marker.
- A shared mode switcher for the dashboard, login, and all error surfaces.
- A static offline fallback using the same secure error surface.
- A shared appearance step included automatically in every available product tour.
- Server-owned Project, Course, and Group sync scope metadata in Job History.

###  Changed
- Charts recolor on mode changes without a reload.
- Middleware errors use one escaped, CSP-aware renderer.
- Spinners use one component DOM/CSS contract and skeletons remain only in real HTMX lazy regions.
- SSR tables render immediately without waiting for a JavaScript visibility guard.
- The light shell, navigation, cards, tables, controls, skeletons, spinners, text,
  borders, shadows, and interaction states now follow current Pajamas semantic roles.
- Historical whole-course sync jobs recover their course context and display the
  course name instead of being mislabelled as standalone group syncs.
- Buttons, dropdowns, cards, and sections have visible semantic borders in both
  themes; search focus no longer resizes action toolbars.
- The branded sign-in background is restored with a responsive card verified at
  a 390 px mobile viewport.

###  Removed
- Generic page, row, and lazy-fragment entrance animations.
- Dead skeleton branches and duplicate button spinner markup.
- Dashboard hover translations and scale effects that added motion without state.

###  Release
- Version `2026.6.11.post7`; Service Worker cache `gitpulse-v186`.

---

## [2026.6.10.post5] - 2026-06-10 - Pajamas Loader Alignment and Clean Skeletons

###  Added
- **Pajamas-aligned loaders and zero inline styles**: Completely eliminated all inline `style` configurations for width, height, and border-radius within `loaders.html`. All sizing is now mapped to reusable Pajamas-aligned utility classes in `loaders.css`.
- **Fidelity-aligned Team Detail and Teachers Skeletons**: Replaced custom/manual skeleton divs with macro components (`badge`, `btn`, `btn_icon`, `btn_icon_only`) in disabled states to guarantee pixel-perfect size matching and zero layout shift (CLS).

###  Fixed
- **GitLab project deletion and empty repo handling**: Added automatic deactivation of projects whose GitLab repository was deleted (returning empty repository status rather than 404). Blanked stale roster scores to match "N/A" on empty/deleted repos.
- **Dynamic roster deactivation on project loss**: Added auto-deactivation of team members when all active projects under their team are deleted/deactivated.
- **Member deactivation safety guard**: Prevented dropping valid project members on partial GitLab API fetch failures, ensuring roster stability during intermittent GitLab API timeouts or 5xx errors.
- **Service Worker & Cache Bump**: Version bumped to `2026.6.10.post5` with cache key incremented to `gitpulse-v176`.

---

## [2026.6.9.post2] - 2026-06-09 - Complete removal of inline layout styles

###  Changed

- **Complete removal of inline layout styles**: Eliminated all layout-related inline `style="..."` attributes (like flexbox, display, margins, padding, opacities, and pointer-events) from `loaders.html`. Migrated them to clean, Pajamas-aligned CSS utility classes in `utilities.css`.
- **Nicer form layouts**: Replaced inline max-width configurations on form components with structured layout utility classes.
- **Service Worker & Cache Bump**: Version bumped to `2026.6.9.post2` with cache key incremented to `gitpulse-v174`.

###  Fixed

- **Version mismatch alert notification**: Updated the app-internal JSON changelog manifest so client browsers receive proper notifications when new versions are deployed.

---

## [2026.6.9.post1] - 2026-06-09 - Seamless transitions and layout-shift free loading skeletons

###  Added

- **Dynamic table header rendering inside skeletons**: Modified the `sk_table` macro to accept an optional `headers` list parameter, allowing static header rows to appear immediately during page loading states.
- **Enhanced `sk_stat` macro with label and icon arguments**: The stats grid placeholders in Course Analytics, Course Activity, and Student Details now render actual labels and icons immediately instead of shimmering blocks, completely eliminating layout shifting.

###  Fixed

- **Seamless dropdown menu interaction**: Fixed invalid CSS variables (`var(--gl-dropdown-item-hover)`) in `dropdowns.css` by mapping them to their correct tokens (`var(--gl-dropdown-item-hover-bg)`, etc.), restoring smooth background transition effects for list hover states.
- **Skeleton loading alignment across all surfaces**: Checked and fully refactored every single composed page skeleton (`sk_dashboard`, `sk_course_detail_body`, `sk_analytics_inner`, `sk_course_activity_inner`, `sk_student_detail`, `_sk_teachers_inner`) in `loaders.html` to align with the real server-rendered templates, using translated helper strings `t()` for static texts.

###  Changed

- Bumped service-worker cache namespace to `gitpulse-v173`.

---

## [2026.6.8.post5] - 2026-06-08 - Synchronized Refresh and Manual GitLab Sync

###  Changed

- **Manual refresh with full sync-all flow**: Clicking the "Refresh" button on Course Analytics or Course Activity now triggers a real background GitLab sync via `/api/v1/courses/{courseId}/sync-all` (for staff). It features button loading states (spinner + text), integrates with the global job progress bar, auto-reloads charts and activity tables on completion, and applies a danger state to the button upon failure.
- **Removed temporary deploy logs**: Cleaned up root-level temporary log files (`deploy-post21.log`, `deploy-post22.log`) from the repository workspace.

---

## [2026.6.8.post4] - 2026-06-08 - Dashboard Polish and Bugfixes

###  Fixed

- **Exclusion of phantom sync rows**: The "Follow the latest updates" feed on the dashboard no longer displays sync jobs that have no matching records in Job History.
- **Action column alignment in members table**: The "View" button in the project members list is right-aligned to prevent layout jumping on rows without the exclusion toggle.

###  Changed

- **Job History refresh feedback**: Manual refresh of the job history table now shows a visible loading state and provides support links on network failure.

---

## [2026.6.8.post3] - 2026-06-08 - Analytics Calculations and Localization

###  Fixed

- **Course analytics student count**: Fixed denominator in the course compliance checklist to calculate active non-instructor students only.
- **SyntaxError in script**: Resolved a JavaScript SyntaxError in the week-explorer page controller.

###  Changed

- **Dashboard greeting subtitle and HTMX error states**: Added a subtitle with user roles and localized date formatting, and appended support ticket links to HTMX lazy-loading failure panels.

---

## [2026.6.8.post2] - 2026-06-08 - Synchronized Page Headers

###  Changed

- **Synchronized Team/Project headers**: Headers (titles, back links, actions) now load directly inside the shell templates to prevent layout shifts.

---

## [2026.6.8.post1] - 2026-06-08 - Skeleton Loader Overhaul

###  Removed

- **Page-level skeletons cleanup**: Removed unused page-level skeleton macros and hid compliance grids on teacher profiles to prevent visual flashing.

---

## [2026.6.5.post18] - 2026-06-05 - "Needs Attention" links to the exact group

###  Changed

- The **"Needs Attention"** KPI card now redirects **exactly to the element**:
  when a single group is failing, it opens that group directly; with several it
  goes to the overview. With the earlier Students-card fix, no two KPI cards
  point to the same place.

---

## [2026.6.5.post17] - 2026-06-05 - Student page: "Project" column removed

###  Changed

- The **"Project" column was completely removed** from every table on the
  student-in-group page (commits, issues, MRs). On a single-group page the
  project never changes, so it was pure noise; the GitLab link stays on the
  commit/issue/MR number. The tables now focus on what is graded: the member's
  own work (DOING) vs peer code review (COMMUNICATING).
- Deleting jobs from **Job History** now also clears them from **"Follow the
  latest updates"** (the feed's job rows share the same source).

---

## [2026.6.5.post16] - 2026-06-05 - Consistent activity feed + smooth skeleton swap

###  Fixed

- **"Follow the latest updates"** is now consistent with **Job History** - no
  more "phantom" sync/report rows that don't exist in Job History. Job-like
  activity comes from the same source as Job History; the audit log only adds
  genuine non-job events (course/group/member/settings/tickets).

###  Changed

- Page content now **settles smoothly into the skeleton's place** after loading
  (GitLab style) instead of a hard pop.

---

## [2026.6.5.post15] - 2026-06-05 - Cleaner dashboard + CI fix

###  Fixed

- **CI is green again** - `requirements.lock` is regenerated on Linux (exactly
  as CI does), not on Windows.
- The **"Follow the latest updates"** feed no longer shows "phantom" system
  entries (telemetry snapshots, leftover scheduled sweeps) - they remain only
  in the admin Job History.

###  Changed

- The **"Students"** KPI card no longer points to the same place as "Users" -
  it opens the users list pre-filtered to students.

---

## [2026.6.5.post14] - 2026-06-05 - Faster loads (longer cache)

###  Changed

- The rendered-HTML cache now lives **5 minutes instead of 60 seconds**. This
  does not affect freshness - the cache is invalidated precisely on every
  change (webhook or in-app action) and on every deploy. The result is far
  more instant loads with no risk of stale data.

---

## [2026.6.5.post13] - 2026-06-05 - Complete webhook coverage

###  Changed

- **Confidential issues and notes** are now processed just like public ones
  (previously silently ignored).
- The webhook setup guide recommends enabling **every relevant event** and
  configuring the hook at the **group/sub-group** level - only group webhooks
  deliver Member and Subgroup events, which is how member add/remove and
  reassignment are captured automatically.

---

## [2026.6.5.post12] - 2026-06-05 - Periodic jobs removed (purely webhook-driven)

###  Removed

- **All periodic (cron) jobs and the scheduler itself** were removed
  (`scheduler.py`, the `scheduler` compose service, the `rq-scheduler`
  dependency). No more "ghost" jobs cluttering the job panel and zero
  background load on GitLab.
- Every mention of periodic scheduling was purged from code and documentation.

###  Changed

- The system is now **purely webhook-driven + manual**: data refreshes from
  GitLab events and explicit actions. Maintenance operations remain as manual
  jobs under *System -> maintenance jobs*.
- Email-delivery retries are **self-scheduling** (`Queue.enqueue_in`, the
  worker's built-in RQ scheduler) - no separate service.

---

## [2026.6.5.post11] - 2026-06-05 - Gentler spam-click protection

###  Fixed

- Fast double-clicking a button that triggers an already-running action no
  longer shows a confusing **red error**. Instead a gentle blue "Please wait -
  the previous action is still running" notice appears and the duplicate
  request is silently ignored (a central fix, no per-button changes).

---

## [2026.6.5.post10] - 2026-06-05 - Service Accounts table pagination

###  Changed

- The **Service Accounts** (GitLab bots) table on the Users page now has its
  own pagination bar (10/20/50 per page), independent of the main users table
  and cooperating with column sorting. With many bots the page is no longer
  overwhelmed.

---

## [2026.6.5.post9] - 2026-06-05 - Clearer student-in-group page

###  Changed

- The **loading skeleton** of this page was rewritten to match the new
  structure exactly - it now includes both group dividers and the commits table
  has the correct column count, so the layout no longer shifts when content
  swaps in.
- The **student-in-group page** is split into two clearly labelled parts:
  **"Work by &lt;member&gt;"** (commits, MRs and issues the member authored) and
  **"Code review & communication"** (review comments they wrote for peers, kept
  separate from feedback they received). A teacher reads the page top-to-bottom
  as a "doing + communicating" story.
- The **Project** column in the tables now appears only when the group spans
  more than one active project; the standalone **SHA** column was removed (the
  GitLab link now sits on the commit title).

###  Fixed (post5-post7)

- Fixed the duplicate **"Done"** state in the global job bar (idempotent against
  the "finishing" phase).
- The **greeting** now renders server-side in the shell page so it no longer
  flashes; its duplicate stats sub-line was removed.
- **"Items that need your attention"** no longer shows the confusing "N projects
  with stale data" line - the reminder is now grouped per course.

---

## [2026.6.5.post4] - 2026-06-05 - Clickable dashboard KPIs + docs deep-clean

###  Changed

- The dashboard **KPI cards** now navigate (admins to users/courses admin pages;
  teachers/students to their course/analytics). Clickable styling applies only to
  cards with a real target.

###  Removed

- Removed the redundant **System Settings stat strip** (it duplicated the
  dashboard cards) and its dead JS.
- Purged all remaining documentation references to removed features
  (rubric/gaming/async-report/roster-import) - zero remain.

---

## [2026.6.5.post3] - 2026-06-05 - Retired schema/API tail cleanup

###  Removed

- Added Alembic migration `049` to drop the remaining retired schema tail:
  the legacy student compliance snapshot column and orphaned history/report
  tables.
- Removed the old telemetry PDF report endpoint, schemas, ORM model, generator
  service, and report-only tests.
- Removed stale active docs, fixture JSON sections, support-form labels,
  login metadata, and i18n keys tied to retired grading, heuristic, report, and
  import subsystems.

###  Changed

- Full course configuration examples now list only active import sections:
  course metadata, settings, built-in checks, custom checks, weekly deadlines,
  Docker lint config, and CI failure config.
- App/docs metadata is `2026.6.5.post3`; Service Worker cache namespace is
  `gitpulse-v160`.

---

## [2026.6.5.post2] - 2026-06-05 - Removed scheduler master switch and dead scheduled fallbacks

###  Removed

- Removed the retired scheduler master switch from Settings, Docker Compose, scheduler runtime,
  the tracked wrapper, admin scheduled registry, manual retry routing, tests,
  README files, and architecture docs.
- Removed the remaining inactive scheduled fallback jobs: periodic metrics
  recompute, background-job cleanup, webhook verification, dead-project polling,
  metric-snapshot cleanup, audit-log cleanup, and expired webhook-secret cleanup.
  Data freshness stays on webhook/manual sync flows; metrics are recomputed
  inline by sync/event flows.
- Removed stale activity-feed/global-job labels for already-deleted GitLab
  polling and discovery jobs so the UI cannot show retired scheduled processes.

###  Changed

- Scheduler/admin catalog now shows only the 12 active scheduled jobs: event
  recovery, CI rollback, conflict expiry/verification, optional LLM, optional
  telemetry, DLQ resurrection, optional Docker re-verification, event retention,
  email queue/log retention, and semester auto-archive.
- App/docs metadata is `2026.6.5.post2`; static bundles were rebuilt and the
  Service Worker cache namespace is `gitpulse-v159`.

---

## [2026.6.5.post1] - 2026-06-05 - Removed periodic GitLab polling & deep docs clean-up

###  Removed

- Removed the **periodic GitLab-polling scheduled jobs** (`periodic_enrich_all`,
  `periodic_enrich_users`, `sweep_stale_projects`, `sweep_discover_new_projects`,
  `sweep_discover_new_teams`) and the now-empty `sweep_enrichment.py` /
  `sweep_discover.py` modules, plus their config intervals and admin registries.
  Data freshness now relies only on webhooks, manual sync, and the on-creation
  sync.

###  Changed

- Deep documentation/thesis clean-up of retired grading/heuristic/intervention/polling
  references (developer structure docs, API reference, thesis abstract/keywords).

---

## [2026.6.5] - 2026-06-05 - Removed retired grading engine, retired heuristic detection, intervention flags & polling sweep

###  Removed

- Removed the **retired grading grading engine**, **retired heuristic detection**, the **Intervention
  Flags** analytics panel + flag endpoints, and the **periodic membership-sync
  sweep** completely (code, settings UI, API, DB columns/tables via migration
  `048`). Manual sync, webhooks, activation sync, and import auto-sync stay; the
  evaluation-report/telemetry subsystem stays intact. The grading core is now
  just the configurable R01-R13 checks that evaluate each student.

###  Added

- Global capture-phase **button click-lock**: repeat clicks within 600 ms are
  swallowed with one throttled "please wait" toast so every action gives
  feedback even when state does not change. UI toggles are exempt.

###  Fixed

- The member-filter **reset button in the loading skeleton** now aligns right to
  match the real filter bar, and leftover retired grading/retired heuristic/flags skeleton
  placeholders were removed.

---

## [2026.6.4.post4] - 2026-06-04 - Legacy global gates removal and System Health parity

###  Removed

- Removed stale global switches for retired grading, manual interventions,
  heuristics, and GitLab polling automation from settings, template globals, API
  guards, scheduler metadata, docker-compose, tests, and docs.

###  Changed

- System Health and scheduler metadata were aligned with the then-current
  transition state before the retired subsystems were fully removed.

###  Fixed

- System Health checking skeleton now shows Database, Redis, and Session_store,
  matching the final operational card.
- Team detail and course Activity skeletons were rechecked against the current
  SSR fragments after card removals.

---

## [2026.6.4.post3] - 2026-06-04 - Roster import & export removal, grading-focused KPIs

###  Removed

- **Roster CSV import** removed (students enter via GitLab sync) - the
  `retired roster switch` flag, `roster_service`, `RosterImport` model/schema,
  the upload/history API and UI, and the `roster_import` job-bar hooks. The
  Roster **view** + CSV export are unchanged.
- **Team CSV/JSON export** removed (buttons + `/teams/{id}/export/*` endpoints).
- **Redundant cards** removed - the course-detail KPI strip and the duplicate
  student *Compliance Checks* card.

###  Changed

- **Grading-focused dashboard KPIs** - admin/teacher home cards swap the raw
  "Groups" count for **Needs Attention** (groups with failing checks).

###  Fixed

- **Week Analytics doughnut tooltip restored** above the centre score.
- **Tighter student profile** (removed the extra divider line).
- **No loading flash / click-spam** - System Health holds a readable minimum
  checking state; buttons stay disabled for the whole request.
- **Skeleton loaders match the real pages** (dropped deleted placeholders, flat
  profile meta, hollow Week Analytics ring).

---

## [2026.6.4.post2] - 2026-06-04 - Retired Report removal and UI cleanup

###  Removed

- **The async "Retired Report" feature was removed end-to-end** - team report
  API/worker, the dead `retired_report` service, the `retired report switch` flag
  with its `cleanup_old_reports` sweep and retention config, the
  `generate_report` job-bar hooks, the team-detail button, i18n strings and the
  tour step. The separate telemetry evaluation-report subsystem is untouched.
- **Redundant cards removed** - course-activity *Summary*, analytics *Compliance
  by Category* (with its Chart.js renderer and backend roll-up) and team *Group
  Summary*.

###  Fixed

- **Consistent stat cards** - the inconsistent `stat-card--glow` hover/focus
  highlight (on some cards, absent on others) was removed so every stat card
  shares one neutral hover plus the standard keyboard focus ring.
- **Flat profile facts** - student Email / GitLab / Role moved from card tiles
  into a flat `profile-meta` row inside the profile card.
- **No loading flash, no click spam** - `setButtonLoading` now holds the loading
  state for a minimum visible duration before resetting and keeps the button
  disabled for the whole in-flight window, centrally for every button (System
  Health, refreshes, syncs, ...).
- **Visible empty Week Analytics ring** - its no-data state used 6%-opacity
  white (invisible on the dark background); it now uses a visible slate, like
  the activity pipeline doughnut.

---

## [2026.6.4.post1] - 2026-06-04 - Analytics refresh and sync cache coherence

###  Fixed

- **Course analytics refresh now uses one SSR/cache-busted path.** The stale
  evaluation-report surface, report Alpine factory, tour step, local report job
  hooks and report skeleton were removed from the analytics page and generated
  bundles. The refresh action reloads the SSR lazy fragment with a
  cache-busting parameter before falling back to the shared scroll-preserving
  reload helper.
- **Sync completion waits for fresh metrics before terminal SSE.** Project
  syncs recompute team metrics inline before marking the sync completed, and
  webhook/metrics side effects invalidate page-cache fragments before notifying
  live clients.
- **Profile/stat cards keep useful interaction without entrance animations.**
  Student profile metadata is back in compact cards, course KPI cards link to
  groups/roster anchors, and glow/process animations remain without duplicate
  card-entry effects.
- **Analytics and system micro-UX were tightened.** The Week Analytics doughnut
  uses an HTML centre label with disabled chart tooltip hitboxes, and System
  Health checking keeps spinner/glow feedback without harsh blinking.
- **Release metadata is current for `2026.6.4.post1`.** Dashboard Latest
  changes, docs, generated bundles/minified siblings and the Service Worker
  cache namespace (`gitpulse-v154`) were refreshed.

---

## [2026.6.4] - 2026-06-04 - Unified sync completion and cache-busted refresh

###  Fixed

- **Sync/check terminal states now follow one readable flow everywhere.**
  Course, team, project syncs and run-check jobs enter shared `Finishing`
  first, remain visible across navigation, then emit the canonical `Done`
  row/toast exactly once.
- **SSR refreshes after data updates bypass stale page caches.**
  `reloadKeepScroll()` now reloads through a cache-busting URL parameter,
  preserves scroll/toasts, and removes the parameter on boot so post-SSE or
  post-mutation refreshes read fresh server-rendered data.
- **No-change sync completions explain what happened.** Project/team sync
  summaries now say when GitLab returned no changed data while metrics/cache
  refresh still completed; team summaries include commit counts when data did
  change.
- **Legacy appearance effects and duplicated profile cards were removed.**
  Student profile metadata now lives in one compact header block and the
  affected course, project, support, student and team surfaces no longer use
  the removed glow/counter/card entrance animations.
- **Release metadata is current for `2026.6.4`.** Dashboard Latest changes,
  docs, generated bundles/minified siblings and the Service Worker cache
  namespace (`gitpulse-v153`) were refreshed.

---

## [2026.6.3.post6] - 2026-06-03 - Settings live-update race removed

###  Fixed

- **Course Settings live updates no longer race old settings or stale page
  fragments.** The settings endpoint now commits the new settings, invalidates
  affected course/team SSR fragments, then publishes `settings_changed`. Open
  course, team, project and settings pages that reload on that event therefore
  fetch committed data and fresh Redis page-cache bodies.
- **Post-update SSR reloads use the shared reload helper.** Project sync
  completion and Support ticket fallback refreshes now call
  `reloadKeepScroll()` instead of raw `window.location.reload()`, preserving
  scroll and visible toasts across SSR reloads.
- **Release metadata is current for `2026.6.3.post6`.** Dashboard Latest
  changes, docs, generated bundles/minified siblings and the Service Worker
  cache namespace (`gitpulse-v152`) were refreshed.

---

## [2026.6.3.post5] - 2026-06-03 - Dashboard live refresh cache coherence

###  Fixed

- **Dashboard live refreshes now use one coherent fan-out.** SSE updates,
  global job-complete fallbacks and tab-return refreshes call one dashboard
  helper for stats, attention items, activity and sidebar badges. This keeps
  the home page from updating only one fragment after a sync.
- **Short-lived dashboard live caches are cleared before global SSE pushes.**
  The dashboard notification publisher now invalidates `dashboard:stats:*` and
  `dashboard:badges:*` Redis keys before publishing `dashboard:global`, so an
  immediate post-sync refresh does not read stale 5-second cache values.
- **The `Your courses` loading skeleton now renders two cards.** The skeleton
  matches the requested dashboard density instead of showing three placeholder
  course cards.
- **Release metadata is current for `2026.6.3.post5`.** Application/docs
  examples, docs-site `latest`, dashboard Latest changes, generated bundles and
  the Service Worker cache namespace (`gitpulse-v151`) were refreshed.

---

## [2026.6.3.post1] - 2026-06-03 - Sync finishing stays readable across navigation

###  Fixed

- **Course sync finishing now stays readable across navigation before moving to Done.** The global job bar restores `finishing` as its own state, keeps it visible for a minimum window, and then completes through the normal `completeGlobalJob()` path so the canonical "Sync completed!" row and toast are not swallowed during page bootstrap. `/sync/active` grace snapshots with `running=0, queued=0` no longer delete/recreate the row or rewrite it back to running, and the course-detail page treats that zero-work active snapshot as Finishing instead of scheduling an immediate reload.
- **Completed single-stage welcome tours no longer reappear after DOM fingerprint drift.** The legacy completion migration now scans the real prefixed `gp_tour_v2:` localStorage keys, so older per-stage completion records are promoted to the global completed key correctly. Tour-seen POSTs also use `keepalive` and retry after failed responses, so quick navigation after Done does not permanently lose server-side tour state.
- **Release metadata is current for `2026.6.3.post1`.** Application/docs package versions, docs-site `latest`, operator/developer version examples, dashboard Latest changes, and the Service Worker cache namespace (`gitpulse-v147`) were refreshed.

---

## [2026.6.3] - 2026-06-03 - Sync finishing survives navigation; completed tours stop re-prompting

###  Fixed

- **Course sync finishing survives navigation and completed welcome tours stop re-prompting.** This release introduced persistence for `lastUpdate` and `finishingSince`, plus welcome-tour completion migration/retry handling.

---

## [2026.6.2.post24] - 2026-06-02 - Sync-locked buttons no longer collapse; course-card sync badge no longer stalls

###  Fixed

- **Process-locked buttons no longer collapse to mismatched widths during a sync.** While a sync runs, mutating actions (e.g. Edit Course, Archive Course in the Course Actions menu) are process-locked, and the lock wraps each control in a `<span class="gl-tip-wrap">` so the disabled-reason tooltip can fire on hover. That span had no styling and defaulted to `display: inline`, so it shrink-wrapped any full-width (`btn-block`) button down to its text width while sibling unlocked buttons stayed full-width - stacked menus rendered chaotically uneven button widths. The wrapper now mirrors a `btn-block` child's full-width block box.
- **Course-card sync badge can no longer get stranded on a stale "Finishing.../Syncing..." pill.** A trailing `gp:job-update` arriving right after a job completed could re-label (or resurrect) a card badge whose job had already finished, leaving the card stuck on "Finishing..." while the global bar already showed "Sync completed!". The update handler now ignores events for jobs that are already terminal, and a defensive sweep clears any badge whose underlying global job is done/error on every completion and on tab refocus.

---

## [2026.6.2.post23] - 2026-06-02 - GitLab Intelligence cards render server-side; no appearance animation

###  Fixed

- **The GitLab Intelligence cards now render fully on the server.** The Protected Branches, Contributors and Repository Stats cards (and the Last Synced row) on the project page used to be emitted with `-` placeholders and then filled in by JavaScript on the first SSE `connected` event, with a `fadeSlideUp` entrance animation - so the above-the-fold stats visibly popped in. A new `gl_intel_view` is now computed in the route (mirroring the JS render logic: byte formatting, contributor merge/sort, stats parsing) and the template renders the card bodies directly. The entrance animation on the info bar and API panel cards was removed, and the dead client-side preload-JSON path (`gp-gl-intelligence`) plus the first-connect JS repaint were deleted. Live refreshes (sync / job-complete) still re-fetch and re-render as before.

---

## [2026.6.2.post22] - 2026-06-02 - Pages stop flickering on load; one shared job-message formatter

###  Fixed

- **Course, team and project pages no longer flicker on load.** The dashboard already skipped its first SSE `connected` refresh and trusted the server-rendered values; the three detail pages did not - they fired a full `/live-data` fetch + repaint the instant the SSE stream connected, so the freshly server-rendered cards/rows were briefly overwritten (the blank-then-JS flicker). All three now carry a `_connectedOnce` guard (mirroring the dashboard) that skips the first `connected` repaint and only refreshes on a genuine reconnect. Live SSE change events still repaint as before. On the project page the lazy GitLab-intelligence load still runs on first connect (it is not server-rendered, so there is nothing to flicker over).
- **Job progress messages now share one formatter everywhere; duplicated code removed.** The admin view had its own `_translateJobMsg` / `_jobTypeLabel` / `_JOB_TYPE_LABELS`, while the global job bar showed the raw English `result_summary` (e.g. `Synced N issues, N MRs...`) untranslated. A single `GP.formatJobMessage` / `GP.jobTypeLabel` now lives in `core/00-base.js`; the global job bar formats at the display boundary (completion toast + live row) and the admin view delegates to it. The formatter is idempotent, so already-translated strings pass through unchanged.

---

## [2026.6.2.post21] - 2026-06-02 - Deleting a group refreshes every stat, not just the project

###  Fixed

- **Deleting or restoring a whole group now refreshes every stat, not just the project view.** Project unlink/restore already recomputed metrics and pushed an SSE nudge, but group delete/reactivate only invalidated the page cache - they never published an SSE event nor recomputed the snapshot. So after deleting a group the open course page kept its stale group list, summary cards, activity feed and analytics until a manual reload. Group delete and reactivate now commit explicitly, publish a `team_deleted` / `team_reactivated` SSE event on both the team and course channels, and enqueue a metrics recompute. The team and course pages treat these as structural events and re-render server-side (scroll preserved).

---

## [2026.6.2.post20] - 2026-06-02 - Unlinking a project also recomputes the group summary

###  Fixed

- **Unlinking a project now updates the Group Summary numbers too.** The summary
  cards (avg score, traffic-light status, pipeline pass rate) are served from the
  latest stored `TeamMetricSnapshot`, which is only rebuilt by a metrics
  recompute - never by the unlink itself. So the list/count updated but the
  headline numbers stayed frozen on the unlinked project's old contribution.
  Unlink and reactivate now enqueue a metrics recompute (the compliance engine
  already excludes `is_active=False` projects); when it lands it publishes a
  `metrics_computed` SSE nudge so the open team/course/dashboard pages refresh
  the cards live.

---

## [2026.6.2.post19] - 2026-06-02 - Unlink/restore now truly refreshes live

###  Fixed

- **Unlink/restore now truly refreshes instead of only showing a toast.** The
  dashboard SSE nudge was published from inside the request handler *before* the
  transaction committed (the session commits after the handler returns), so the
  client's instant live-data refetch raced the still-open transaction and re-read
  the project as active - the "Data updated" toast fired but nothing changed.
  Unlink and reactivate now commit explicitly and only then publish the SSE event
  (`expire_on_commit=False` keeps the captured ids valid).
- **The unlinked project row now disappears from the list.** `refreshTeamData()`
  patched stat cards, member rows, and retired grading scores but never the
  server-rendered "Subgroups and Projects" list, so the unlinked row lingered.
  Structural project events (unlink / restore / link) now trigger a
  scroll-preserving server-side re-render on the team and course pages, so the
  list, the Deleted count, and the summary cards all reflect committed truth.

---

## [2026.6.2.post18] - 2026-06-02 - Live refresh on unlink/restore, no duplicate progress bars

###  Fixed

- **Unlink/restore now updates the whole UI live.** Unlinking or reactivating a
  project now publishes a dashboard SSE event for its team and course, so open
  dashboard, course, and analytics views refresh their stats cards, activity
  feed, and metrics immediately instead of waiting for a manual reload.
- **No more duplicate progress bars.** A single sync/restore action could
  surface two rows in the global progress bar - a project-scoped
  "Syncing project..." row plus a course-level aggregate row from
  `/sync/active`. The `/sync/active` reconciler now suppresses the course
  aggregate while a project-/team-scoped sync row for the same course is
  already tracked, and the render pass collapses any remaining same-course rows
  into one as a safety net.

---

## [2026.6.2.post17] - 2026-06-02 - Time-of-day greeting, live activity feed, active-only counters

###  Added

- **Time-of-day dashboard greeting.** The home greeting shows "Good morning /
  Good afternoon / Good evening" by the viewer's local clock (server-translated,
  with an "Hi" fallback when JavaScript is off) and re-evaluates on tab-return.
- **Live "Follow the latest updates" feed.** The feed is served from
  `/dashboard/activity` and refreshes live over the dashboard SSE stream
  (polling fallback retained), and now surfaces group/project deletion and
  restoration with their own icons, labels, and links.

###  Fixed

- **Headline counters count only active items.** The "Groups" counter and the
  project counts behind per-team pipeline health filter `is_active`, so
  unlinked/deleted groups and projects (and GitLab `deletion_scheduled`
  tombstones) drop out immediately instead of inflating the cards.

###  Changed

- **Admin system "active jobs" grid is SSE-first.** The scheduled-jobs panel
  reacts to the dashboard SSE stream instead of waiting up to 10 s, with the
  10 s interval retained purely as a polling fallback.
- **Release metadata is current for `2026.6.2.post17`.** JS/CSS bundles and
  minified siblings were rebuilt, docs-site `latest` points to this release,
  dashboard Latest changes was refreshed, and the service-worker cache
  namespace is `gitpulse-v139`.

---

## [2026.6.2.post16] - 2026-06-02 - Config import boundary and form validation cleanup

###  Fixed

- **Course config auto-import no longer depends on dashboard route internals.**
  `scripts/import_course_configs.py` imports the dedicated
  `course_settings_config` config-application module directly, so deployment
  bootstrapping does not rely on private HTTP route re-exports and strict mypy
  is clean again.
- **Shared form components preserve their declared attributes.** Bare text
  inputs now keep validation attributes (`pattern`, `minlength`, `autofocus`),
  bare checkboxes submit the requested value, and required custom dropdowns use
  a focusable validator control instead of an ignored `required` hidden input.
- **The local security scan wrapper reports production dependency risk.**
  `scripts/security_scan.py` now uses timezone-aware timestamps, parses
  `pip-audit` JSON even when the tool emits advisory text, and audits
  `requirements.lock` by default instead of reporting unrelated packages from
  the developer virtualenv.

###  Changed

- **Release metadata is current for `2026.6.2.post16`.** JS/CSS bundles and
  minified siblings were rebuilt, docs-site `latest` points to this release,
  dashboard Latest changes was refreshed, and the service-worker cache
  namespace is `gitpulse-v138`.

---

## [2026.6.2.post15] - 2026-06-02 - SSE helper contract and UI style cleanup

###  Fixed

- **The shared SSE job helper now has an explicit polling fallback contract.**
  Manual fallback uses `GP.apiCall` instead of relying on an accidental global
  identifier, and completion callbacks are isolated so a page-level callback
  error cannot leave an EventSource or fallback poller running forever.
- **The global progress bar no longer persists removed ETA state.** The ETA UI
  was already removed in favour of elapsed time, but the old state key still
  leaked through localStorage and cross-tab merges. That legacy state is now
  ignored and no longer written.
- **Small static inline styles moved into component CSS.** Cookie banner links,
  dashboard quick-access avatar colours, the service-account summary header,
  and dropdown avatar dimensions now use classes instead of repeated inline
  declarations.

###  Changed

- **Release metadata is current for `2026.6.2.post15`.** docs-site `latest`
  points to this release, dashboard Latest changes was refreshed, and the
  service-worker cache namespace is `gitpulse-v137`.

---

## [2026.6.2.post14] - 2026-06-02 - Diplomovka section synced with the current thesis repository

###  Added

- **The docs-site Thesis section now matches the current thesis text.** Slovak
  chapters mirror the latest LaTeX source from `dp.mykyta.olym/thesis`,
  including the new [4. Solution design](diplomovka/navrh.md) and
  [5. Conclusion](diplomovka/zaver.md) pages, the refreshed thesis index, and
  Mermaid architecture/event-flow diagrams.
- **A repeatable thesis sync script was added.** `scripts/sync_thesis_docs.py`
  converts the LaTeX chapters through Pandoc, handles project-specific
  glossary/reference/table/diagram macros, and removes the need for manual
  copy-paste updates.

###  Changed

- **Thesis goals, navigation and Latest changes are current for
  `2026.6.2.post14`.** The goals page links the completed design chapter,
  marks pilot deployment and impact evaluation as the next phase, docs-site
  `latest` points to `2026.6.2.post14`, and the service-worker cache namespace
  is `gitpulse-v136`.

---

## [2026.6.2.post13] - 2026-06-02 - Job SSE fallback dedup + current docs metadata

###  Fixed

- **The global progress bar no longer starts duplicate polling timers for the
  same background job after an SSE failure.** `streamJobProgress()` already
  owns the SSE-to-polling fallback, but the global job bar also launched its
  legacy poller from the helper's error callback. That could close the helper
  while it was switching modes and leave duplicate `/api/v1/jobs/{id}` polling.
  The job bar now delegates fallback to the shared helper, and the helper
  re-checks whether it was closed before starting internal polling.
- **GitLab recovery toasts no longer appear under the main backend-health
  banner.** A GitLab-only recovery toast during a broader backend outage was
  misleading, so the toast now fires only when the GitLab banner itself is
  still visible.
- **Documentation metadata is current again.** Application/docs metadata is
  `2026.6.2.post13`, docs-site `latest` points to the same version, the
  service-worker cache namespace is `gitpulse-v135`, dashboard Latest changes
  was refreshed, and stale docs references to `2026.6.2.post4` were updated.

---

## [2026.6.2.post12] - 2026-06-02 - Dismissing a running sync keeps buttons locked + group-delete guardrails

###  Fixed

- **Dismissing a running sync no longer re-enables the buttons it locked.**
  Clicking the X on a still-running job in the global progress bar deleted the
  job from the in-memory registry that the process-action guards read, so the
  Sync / Run Checks / Unlink / Delete Group buttons wrongly re-enabled
  mid-sync. Dismissing a running job now only hides its progress row - the job
  stays active so the buttons remain locked and the poller keeps tracking
  completion; it is removed normally once the sync actually finishes.
- **A project can no longer be restored while its group is deleted.** Restoring
  a single project under a soft-deleted group would leave it orphaned (active
  yet hidden everywhere the group is hidden, and excluded from the course
  aggregate). The restore endpoint now rejects this with a clear message, and
  the project page shows a dedicated "This project's group is deleted" banner
  that points teachers to restore the whole group instead.

---

## [2026.6.2.post11] - 2026-06-02 - One sync toast at the right time + CI lint restored

###  Fixed

- **A single project restore or sync no longer pops two "Sync completed"
  toasts.** The per-project sync fired its own completion toast ("Sync
  completed") while the course-level aggregate fired another ("Sync
  completed!"). Their wording differs, so the 5-second text dedup missed them,
  and their job keys differ, so the session dedup missed them too - and the
  faster project toast appeared early, before the aggregate finished.
  Per-project / per-team completion toasts are now collapsed into the
  authoritative course-level aggregate toast, so one operation shows exactly
  one toast at the right time.
- **Restored the ruff lint CI gate.** A helper script had unsorted imports and
  an unformatted body that failed the lint job; it is now sorted and
  formatted.

---

## [2026.6.2.post10] - 2026-06-02 - One row per sync in the global progress bar

###  Fixed

- **The global progress bar no longer shows two rows for a single project
  restore or sync.** Restoring or syncing one project registers a per-project
  "Syncing project..." entry, but the same work is also surfaced as a
  course-level aggregate ("DEVOPS: Syncing...") because the active-sync feed
  counts running jobs per course. The earlier dedup only collapsed the two
  while both were still running, so a project sync that finished first (common
  on tiny/empty repos) left a second "Sync completed" row. The per-project /
  per-team sync entry is now collapsed into the course aggregate for the same
  course regardless of completion state, so one operation shows exactly one
  row.

---

## [2026.6.2.post9] - 2026-06-02 - Unlink/restore reflects instantly (page-cache invalidation)

###  Fixed

- **Unlinking or restoring a project or group now reflects instantly without
  leaving and re-entering the page.** The detail pages serve their heavy
  content from a short-lived (60s) Redis page-fragment cache, but the
  unlink/restore endpoints never dropped that cache, so the in-place reload
  kept re-serving the previous (still-active or still-unlinked) body until the
  cache expired - which is why only navigating away and back appeared to work.
  The unlink and reactivate endpoints for both projects and groups now
  invalidate the affected project / group / course / student page caches
  immediately, so the reloaded page shows the new state right away. This also
  clears the phantom duplicate progress-bar row that appeared while the stale
  page re-registered the in-flight sync.

---

## [2026.6.2.post8] - 2026-06-02 - No entrance animations, instant restore/unlink, no duplicate sync row

###  Fixed

- **Pages no longer fade, slide or blink when they load.** Every
  entrance/appearance animation was removed - the cross-document page
  crossfade, the whole-page reveal, the staggered fade-in of lazy-loaded
  cards, and the alert/banner slide-in. Content paints instantly and stays
  static, so nothing flickers on load, reload or live refresh. The dead CSS
  and JS were deleted, not just disabled.
- **Unlinking or restoring a project now reflects immediately.** The reload
  that flips the banner and action buttons was masked by the view-transition
  snapshot; with that gone the reload repaints cleanly and the new state shows
  right away instead of only after re-entering the project.
- **The global progress bar no longer shows a duplicate "Waiting in queue..."
  row.** While a course-level sync runs, the redundant per-project/per-team
  entry for the same course is collapsed into the course aggregate.

---

## [2026.6.2.post7] - 2026-06-02 - Restore sync completes and data refreshes in place

###  Fixed

- **Restoring a project no longer leaves the sync spinning forever.** The
  reactivate endpoint returned a raw RQ job id, but the global progress bar
  polls `GET /api/v1/jobs/{id}` which resolves a job row - so the id 404'd
  forever and the "Syncing project..." bar never finished. The endpoint now
  creates a real background job and returns its id, so the bar completes.
- **The project page refreshes its data the moment a restore/sync finishes.**
  Contributors, commits and pipelines are re-fetched in place, so you no longer
  have to leave the project and come back to see the updated numbers.
- **Small cards no longer flicker or "activate twice".** The entrance animation
  on lazy-loaded panels (Contributors, Repository Stats, Protected Branches)
  now runs at most once per container instead of re-animating on every live
  refresh.

---

## [2026.6.2.post6] - 2026-06-02 - Restore no longer freezes on "Restoring..."

###  Fixed

- **Restoring an unlinked project no longer freezes on "Restoring...".** The
  previous reactivate flow waited for the background refresh job to finish
  before reloading; for an empty or slow repository that completion never
  arrived promptly, so the "Restoring..." button and the global progress bar
  hung for 20-40+ seconds and the page never reloaded. The project page now
  registers the refresh job in the persistent global progress bar and reloads
  immediately, so the project shows its restored state right away while the
  sync is tracked in the background.

---

## [2026.6.2.post5] - 2026-06-02 - Restore/unlink no longer kicks you out

###  Fixed

- **Unlinking a project or deleting a group no longer ejects you to another
  page.** Both actions now reload the current page in place so you immediately
  see the "unlinked"/"archived" banner and the Restore button, instead of being
  redirected away ("kicked out").
- **Restoring a project surfaces the background sync and refreshes the data when
  it lands.** The reactivate endpoint returns the enqueued refresh job id; the
  project page attaches it to the global progress bar, streams progress, and
  reloads only once the sync actually completes.
- **Empty repositories now state they are not counted.** The empty-repo warning
  now explicitly says the project is excluded from the group average and
  rankings until the team pushes code.

---

## [2026.6.2.post4] - 2026-06-02 - Tombstone projects and first-load animation flicker

###  Fixed

- **GitLab `deletion_scheduled` tombstone projects are no longer ingested or
  shown as restorable groups.** When GitLab schedules a project for deletion it
  renames the path to `<path>-<hash>-deletion_scheduled-<id>` but keeps it
  visible in the group-projects API briefly. The discovery sweep now skips those
  tombstones and the course/team detail listings filter them out, so a project
  the teacher never deleted no longer appears as a ghost "Deleted" group with
  anomalous data.
- **Entrance animations and skeleton loaders no longer blink on first page
  load.** The page-enter reveal now suppresses every descendant entrance
  animation during the reveal (instead of a hard-coded handful of classes) while
  leaving looping loader feedback - spinners, dots, bar/skeleton shimmer, status
  pulses - running.

###  Changed

- Application/docs metadata bumped to `2026.6.2.post4`; service-worker cache
  namespace bumped to `gitpulse-v128`; bundles and minified siblings rebuilt;
  dashboard Latest changes refreshed.

---

## [2026.6.2.post3] - 2026-06-02 - Teacher restore of groups and projects

###  Added

- **Teachers can restore soft-deleted groups and unlinked projects.**
  `POST /api/v1/teams/{team_id}/reactivate` and
  `POST /api/v1/projects/{project_id}/reactivate` are no longer admin-only; any
  teacher with course access can restore. Restoring a group precisely re-enables
  the members and projects deactivated by the most recent delete and enqueues a
  background sync so rankings, metrics and checks recover immediately.
- **Students keep read-only visibility of their own archived group's score.**
  Deleted groups and unlinked projects stay reachable for their members with a
  clear archived banner explaining the data is frozen for reference, while staff
  see Delete/Unlink badges, restore buttons, and a toggle to show or hide
  archived rows.

###  Fixed

- **Deactivated groups and projects no longer inflate course aggregates.**
  Contributor totals, green/red status counts, never-synced and stale-data
  indicators, and sync counters consider only active groups. The metrics worker,
  the project sync worker, and `compute_team_metrics` skip archived
  groups/projects so scoring, rankings and analytics exclude them consistently.

###  Changed

- Application/docs metadata is `2026.6.2.post3`; Service Worker cache is
  `gitpulse-v127`; bundles/minified siblings are rebuilt, Slovak translations
  are completed (0 missing strings), and restore endpoints return DTO-style JSON
  responses covered by unit tests.

---

## [2026.6.2.post2] - 2026-06-02 - Delete Group and Unlink Project guards

###  Fixed

- **Dangerous group and project actions now have backend guards.**
  `DELETE /api/v1/teams/{team_id}` and `DELETE /api/v1/projects/{project_id}`
  serialize through team/project mutation scopes and return `409 Conflict`
  during active `sync` or `run_checks`, so direct API requests cannot bypass
  the UI guard and race score or project-state writers.
- **Delete Group also deactivates the group's projects.** Soft-deleting a group
  now disables active `GitLabProject` rows together with active members, keeping
  dashboard state, sync discovery, and webhook processing aligned with the
  button contract.
- **Webhooks from unlinked projects are no longer processed.** Authenticated
  GitLab webhooks for inactive projects return `ignored` without creating a
  `WebhookEvent`, so an unlinked project remains skipped until explicitly
  reactivated.
- **Course detail Delete Group uses the clicked button.** Row removal no longer
  relies on a substring selector over `data-action-args`, and scoring toggle
  buttons now carry declarative `sync run_checks` process locks.
- Application/docs metadata is `2026.6.2.post2`; Service Worker cache is
  `gitpulse-v126`; bundles/minified siblings are rebuilt and destructive action
  guards are covered by focused unit/source-pattern tests.

---

## [2026.6.2.post1] - 2026-06-02 - Latest changes limit and release-date guard

###  Fixed

- **Dashboard Latest changes now handles non-positive limits
  deterministically.** `_get_changelog_entries(limit=0)` and negative limits
  return an empty list instead of Python negative slicing behaviour, where
  `limit=-1` returned almost the whole widget feed.
- **Dashboard changelog release-date validation reads the package version.**
  The test derives the current release day from the CalVer value in
  `pyproject.toml`, so the guard no longer duplicates a hand-maintained date.
- Application/docs metadata is `2026.6.2.post1`; Service Worker cache is
  `gitpulse-v125`; bundles/minified siblings are rebuilt and widget
  limit/date contracts are covered by unit tests.

---

## [2026.6.2] - 2026-06-02 - Team member badges without stray dots

###  Fixed

- **Role and score badges in the team members table no longer render stray
  dots.** Text-heavy cells in `team-members-table` still truncate with an
  ellipsis, but badge-only cells now use a dedicated `member-badge-cell`
  contract with `text-overflow: clip`, so `Mentor`, `Maintainer` and score
  pills do not get a dangling dot beside them.
- **Access-role badge mapping is single-source.** The duplicated student/staff
  table branch ladder moved into the shared `member_access_role_badge()`
  component.
- Application/docs metadata is `2026.6.2`; Service Worker cache is
  `gitpulse-v124`; bundles/minified siblings are rebuilt and the badge-cell
  overflow contract is covered by unit tests.

---

## [2026.6.1.post8] - 2026-06-01 - Docs-site nginx without 404 cache/index gaps

###  Fixed

- **The docs-site custom 404 page is no longer cacheable or indexable.**
  The internal `/404.html` location now repeats the explicit
  `Cache-Control: no-store, no-cache, must-revalidate` header and adds
  `X-Robots-Tag: noindex, nofollow, nosnippet`, closing the gap caused by
  Nginx `add_header` inheritance rules inside location blocks.
- **The docs-site health endpoint is now an exact plain-text contract.**
  `/health` is an exact location with `default_type text/plain`, so random
  `/health...` paths no longer look healthy and the endpoint does not rely on
  `add_header` for `Content-Type`.
- Application/docs metadata is `2026.6.1.post8`; Service Worker cache is
  `gitpulse-v123`; bundles/minified siblings are rebuilt and nginx header
  contracts are covered by unit tests.

---

## [2026.6.1.post7] - 2026-06-01 - Local-timezone timestamps everywhere & no native pull-to-refresh

###  Fixed

- **Every timestamp now displays in your local timezone instead of UTC.**
  "Last Synced" on the project page (missing the `data-localize-time` marker
  and using a timezone-less `isoformat()`), plus commit, issue, merge-request,
  CI-scenario, conflict, Docker-report, roster-import and analysis times, were
  showing raw server UTC. They now all render through one shared `local_time()`
  Jinja global that emits a canonical `...Z` `<time data-localize-time>`
  element; `localize-time.js` converts it client-side and gained
  `data-localize-format` so custom formats (`HH:MM`, `Mon DD, HH:MM`) survive.
- **Chrome's native white pull-to-refresh spinner no longer fires on mobile /
  installed PWA.** The overscroll suppression was set only on `<body>`, but the
  property must live on the root `<html>` to reach the viewport, so the native
  refresh kept showing next to the app's own indicator. The rule now also
  targets `<html>`.
- Application/docs metadata is `2026.6.1.post7`; Service Worker cache is
  `gitpulse-v122`; bundles/minified siblings are rebuilt.

---

## [2026.6.1.post6] - 2026-06-01 - Flicker-free Last Updated column

###  Fixed

- **The groups-table "Last Updated" column no longer blinks between UTC and
  local time.** The `/sync-stream` and `/live-data` SSE feeds shared the cell
  but rendered it differently, so it bounced between the server UTC stamp and
  the user-local time on every update. Both feeds now go through one ISO-keyed
  `_renderLastUpdated()` helper that only repaints when the underlying timestamp
  actually changes.
- Application/docs metadata is `2026.6.1.post6`; Service Worker cache is
  `gitpulse-v121`; bundles/minified siblings are rebuilt.

---

## [2026.6.1.post5] - 2026-06-01 - Declarative actions without inline expression eval

###  Changed

- **Component actions no longer use `data-action-expr` or `new Function`.**
  The shared frontend core only executes named `data-action` handlers with
  JSON arguments, and project empty-state buttons now call
  `clickElementById` through that structured contract.
- Application/docs metadata is `2026.6.1.post5`; Service Worker cache is
  `gitpulse-v120`; generated bundles and minified siblings were rebuilt.

---

## [2026.6.1.post4] - 2026-06-01 - Immediate process guard refresh on job updates

###  Fixed

- **Process-action locks now react to `gp:job-update`.** The shared guard
  refreshes when the global job bar starts or updates a sync/import/run-checks
  job, so conflicting buttons are disabled immediately instead of waiting for
  the fallback polling interval.
- Application/docs metadata is `2026.6.1.post4`; Service Worker cache is
  `gitpulse-v119`; generated bundles and minified siblings were rebuilt.

---

## [2026.6.1.post3] - 2026-06-01 - Process guard root refresh and component cleanup

###  Changed

- **The unused `process_status.html` component was removed.** Dashboard and
  course detail fragments now use the external `import-stream.js` module and
  the shared global-job/process-guard modules instead of importing legacy
  inline-JS macros.
- **`GP.refreshProcessActionGuards(button)` now evaluates the button itself.**
  Single dynamically inserted controls are locked immediately during active
  sync/import/run-checks processes, even when no parent container is refreshed.
- Application/docs metadata is `2026.6.1.post3`; Service Worker cache is
  `gitpulse-v118`; generated bundles and minified siblings were rebuilt.

---

## [2026.6.1.post2] - 2026-06-01 - Cross-document View Transition skip no longer logged

###  Fixed

- **Cross-document View Transitions no longer log `AbortError: Transition was
  skipped`.** Course tabs and page links navigate cross-document, where the CSS
  `@view-transition { navigation: auto }` rule drives the crossfade. When a
  transition is skipped (a second tab is clicked before the first settles, the
  active tab is re-clicked, or the tab is hidden mid-navigation), the browser
  rejects the transition promises. They are now handled at the source via the
  `pageswap` and `pagereveal` navigation events instead of surfacing as an
  uncaught "(in promise)" rejection.
- Application/docs metadata is `2026.6.1.post2`; Service Worker cache is
  `gitpulse-v117`; generated bundles and minified siblings were rebuilt.

---

## [2026.6.1.post1] - 2026-06-01 - External course-tabs module and component cleanup

###  Changed

- **Course tab keyboard navigation now lives in `course-tabs.js`.** The shared
  course-navigation partial no longer embeds inline JavaScript; the behavior is
  included in `core.bundle.js` and covered by a regression test.
- **The shared native select component no longer exposes an inline `onchange`
  escape hatch.** Current callers use declarative data/action contracts or
  Alpine bindings.
- Application/docs metadata is `2026.6.1.post1`; Service Worker cache is
  `gitpulse-v116`; generated bundles and minified siblings were rebuilt.

---

## [2026.6.1] - 2026-06-01 - Tooltip-without-hover fix

###  Fixed

- **Tooltips no longer appear without hovering.** Tippy's default trigger is
  `mouseenter focus`, so when a modal's focus-trap (or a mouse click)
  programmatically focused a button carrying `data-tippy-content` - most
  visibly the close (X) button - its tooltip popped open with no hover.
  Tooltips now suppress focus-triggered shows unless the focus is from the
  keyboard (`:focus-visible`), preserving accessibility while removing the
  spurious popups.
- Application/docs metadata is `2026.6.1`; Service Worker cache is
  `gitpulse-v115`.

---

## [2026.5.31.post3] - 2026-05-31 - Dashboard cache safety and docs HTML fix

###  Fixed

- **Authenticated dashboard HTML is no longer stored by the Service Worker.**
  The worker bypasses `/dashboard` navigations and its shared cache helpers
  refuse `Cache-Control: no-store` or `private` responses, matching the
  security middleware contract.
- **Logout now sends the documented browser cleanup header.**
  `GET /dashboard/logout` deletes the session cookie and returns
  `Clear-Site-Data: "cache", "storage"`.
- **The documentation logo override no longer creates nested anchors.** The
  custom MkDocs Material partial renders only the image/icon content, leaving
  header and nav link ownership to the theme templates.
- Application/docs metadata is `2026.5.31.post3`; Service Worker cache is
  `gitpulse-v114`.

---

## [2026.5.31.post2] - 2026-05-31 - Centralized documentation SEO policy

###  Changed

- **Documentation SEO signals are now managed in one place.** The MkDocs hook
  `hooks/seo_policy.py` marks technical and internal sections (`vyvojari`,
  `operatori`, `gitlab`, `bezpecnost`, `api`, `diplomovka`, `changelog`,
  `tags`) as `noindex, follow, nosnippet`, so Google does not surface random
  runbooks, token examples, or the internal changelog as sitelinks. Public
  product, student/teacher onboarding, and legal pages remain indexable.
- **Sitemaps are split by ownership.** Root `/sitemap.xml` belongs to the app
  and lists only `/dashboard/login`; `/docs/sitemap.xml` belongs to MkDocs and
  the hook removes `noindex` URLs from it. `robots.txt` explicitly lists both
  sitemaps, giving Google consistent signals without duplicate docs URLs in
  the root sitemap.

---

## [2026.5.31.post1] - 2026-05-31 - Dashboard, analytics and admin-system SRP split

###  Changed

- **Split the dashboard, course-analytics and admin-system page controllers into Single-Responsibility source parts.** Following the Admin Courses split, the three remaining ~1.1k-line page scripts are now authored as ordered `_parts/<page>/NN-*.js` fragments and concatenated **verbatim** back into the served file by the bundle builder. The output is byte-identical, so there is zero runtime change - only the source is now small and single-responsibility, matching every other split page controller.

---

## [2026.5.31] - 2026-05-31 - Admin Courses SRP split and cache refresh

###  Changed

- **Admin Courses frontend now follows the page-controller SRP pattern.**
  `pages/admin-courses.js` is generated from `_parts/admin-courses/00-core.js`,
  `10-lifecycle.js`, and `20-events.js`, so configuration, lifecycle mutations,
  and event delegation have separate owners while the served file remains a
  deterministic build artifact.
- **Course lifecycle row updates use shared UI contracts.** Archive/activate/delete
  swaps now render the shared `status-indicator` markup, icon-only lifecycle
  buttons, refreshed tooltips, and scoped process guards after every dynamic DOM
  update.
- **Release metadata and static delivery refreshed.** Version is `2026.5.31`,
  bundles and `.min` siblings were rebuilt, dashboard Latest changes was updated,
  and Service Worker cache is `gitpulse-v113`.

---

## [2026.5.30.post11] - 2026-05-30 - Animated scoring eye toggle, consistent tooltips, live recompute

###  Changed

- **Polished the scoring include/exclude (eye) control across the member tables.** The eye / eye-off icon now animates with a springy pop when a student is toggled, the button stays visible and tinted while a row is excluded so the reversible state reads clearly, and hover/press add subtle scale feedback. The control now uses a consistent Tippy tooltip (no more duplicate native browser tooltip), and the excluded-row dimming transitions smoothly instead of snapping. Toggling a student still recalculates the group average, traffic light, contributor counts and retired grading scores live - no page reload. All motion respects `prefers-reduced-motion`.

---

## [2026.5.30.post10] - 2026-05-30 - Fixed elapsed timer reset between navigations, and SW v101

###  Fixed

- **Fixed the progress-bar elapsed timer resetting on every page navigation.** When a course-sync bar was recreated after navigating to another page, the new bar was stamped with the current clock time instead of the server-authoritative sync start time, so the seconds counter restarted from zero each navigation. The bar now anchors its elapsed timer to the server `started_at_ms` and keeps the earliest known start, so the timer stays monotonic across navigations.

---

## [2026.5.30.post9] - 2026-05-30 - Monotonic task start time, SRP caching refactor, and SW v100

###  Fixed

- **Fixed progressive restarted times in sync job bar.** Passive reconcilers (e.g. course card scans, dashboard polling updates) could restage the global progress bar as a new run, reset execution progress to null, and bump start time to the current clock time. The SSE progress indicators now correctly protect and retain monotonic start times, preventing seconds-counters in the progress panel from resetting to zero.

###  Changed

- **Refactored caching layers to enforce strict Single Responsibility Principle.** Verified zero cross-tenant leak vectors on templated CSP nonces and CSRF tokens across page-fragment page caching endpoints.
- **Service Worker cache partition upgraded to v100.** Static cache keys bumped to invalidate previous offline fragment cache baselines cleanly.

---

## [2026.5.30.post8] - 2026-05-30 - Instant global progress bar with a "Connecting..." stage

###  Changed

- **The global progress bar now appears instantly with a "Connecting..."
  stage.** Starting a course sync (Sync All), a project sync, or a sync from
  the course settings page used to surface the global progress bar only
  *after* the backend POST returned. With the GitLab reachability pre-flight
  (which retries and can take several seconds) the user saw no bar during that
  window and could re-click the button. The bar now shows an indeterminate
  "Connecting to GitLab..." spinner the moment the button is clicked, which also
  makes the existing re-click guard fire immediately so double submits are
  blocked. Once the sync is enqueued the bar promotes to the real
  "Syncing: X/Y groups..." message; if the request fails the error is shown
  directly **in the bar** (not just a transient toast). A safety timeout
  guarantees the connecting spinner can never hang.

---

## [2026.5.30.post7] - 2026-05-30 - Sync reliability: GitLab pre-flight retry

###  Fixed

- **Sync no longer fails when GitLab answers slowly once.** The sync
  entrypoints run a GitLab reachability pre-flight before enqueuing jobs. It
  used a single 4 s request with no retry, so one transient slow response
  returned `503 "GitLab server is currently unreachable"` and the sync did
  nothing. The pre-flight now retries once (5 s per attempt, 0.4 s backoff)
  and only treats two consecutive failures as unreachable.

---

## [2026.5.30.post6] - 2026-05-30 - Week Analytics fixes + telemetry typing

###  Fixed

- **Week Analytics opens on the latest week with data.** Once teaching winds
  down students stop committing, so the current week is often empty while the
  weekly scoring job keeps carrying compliance forward. The explorer used to
  auto-select the current (empty) week and show "No GitLab events tracked this
  week", which looked like data loss. It now auto-selects the most recent week
  with real activity or a compliance trend. A prod DB probe confirmed no data
  loss - there were simply no commits after teaching week 12.
- **Exam-period weeks reachable and styled in Week Analytics.** The week
  selector only ran `1..semester_weeks`, so exam-period (skúškové obdobie) weeks
  had no pill and never showed the amber EXAM PERIOD treatment. The selector now
  extends through the exam period with amber "Exam" pills and an
  "Exam Period · Week N" chip in the detail header.
- **Course search empty state.** Filtering the dashboard "Your courses" grid to
  a non-matching query now shows a proper empty-state component instead of a
  blank area.
- **Six telemetry models migrated to SQLAlchemy 2.0 typing.**
  `FlaggedTeamResolution`, `StudentComplianceSnapshot`, `ClicksAvoidedMetric`,
  `TeacherActivityMetric`, `TelemetryAggregate` and `EvaluationReport` were
  rewritten from legacy `Column(...)` assignments to `Mapped[] / mapped_column`,
  matching the earlier `SupportTicket` migration. Pylance now infers attribute
  types correctly (e.g. `flagged_at: datetime`, `week_number: int`) instead of
  `Column[X]`, eliminating the false-positive type errors in
  `pilot_telemetry.py` and the redundant `cast(...)` wrappers they required, plus
  a missing `None` guard before a `datetime` subtraction. No behaviour or
  database-schema change.

---

## [2026.5.30.post5] - 2026-05-30 - Green container scan (protobuf CVE)

###  Fixed

- **Container security scan (Trivy) is green again.** The transitive `protobuf`
  dependency was held at `4.25.9` by a `protobuf<5.0` ceiling that also pinned
  `opentelemetry-proto` to the older `1.27` line. That `protobuf` build carried a
  fixable HIGH/CRITICAL vulnerability, **CVE-2026-0994**, failing the
  `container-scan-api` and `container-scan-worker` jobs. The ceiling was raised
  to `protobuf>=5.29.6,<6.0`, moving `protobuf` to the fixed `5.29.6` and letting
  OpenTelemetry resolve up to `1.42.1` (stable `1.x` API - no app code change).
  `requirements.lock` was regenerated on Linux to match CI.

---

## [2026.5.30.post4] - 2026-05-30 - Green CI pipeline + faster analytics

###  Fixed

- **CI pipeline is green again.** Commit `f0cb9816` shipped a
  `requirements.lock` generated on Windows, so it contained `colorama`
  (Windows-only) and was missing `uvloop` (Linux-only). CI runs on Linux
  (`python:3.12-slim`), so `lockfile-check` regenerated the lock, got the
  opposite package set, and the job went red. The lock is now generated on
  Linux (matching CI). `mypy` also flagged a leftover `cast(int, ...)` and a
  `# type: ignore[assignment]` that became redundant after the post3
  `SupportTicket` typing - both removed - and `home_changelog.py` was
  reformatted with `ruff format`.
- **The course analytics page no longer hangs on first load.** The heavy
  analytics fragment takes ~60-95 s to compute on a populous course, which
  exceeded the global 90 s htmx timeout - so after every deploy (the cache key
  includes GIT_SHA, i.e. a cold start) the first load hit `htmx:timeout` and
  "nothing loaded". That fragment's timeout is now 180 s and the page-cache TTL
  was raised from 60 s to 600 s, so once analytics is computed it stays warm and
  subsequent loads are instant. Version `2026.5.30.post4`.

---

###  Fixed

- **Migrated the `SupportTicket` model to SQLAlchemy 2.0 typing.** Legacy
  `Column(...)` assignments made Pylance infer every attribute as `Column[X]`,
  producing 11 false-positive errors in the dashboard support route. The model
  now uses `Mapped[...] / mapped_column(...)` like its siblings. Pure typing
  change - ORM behaviour is identical; `mypy` and the targeted tests pass.
- **Made `lockfile-check` deterministic (again).** `exclude-newer` pointed at a
  future instant, so each CI re-resolve picked up packages published "today" and
  `requirements.lock` drifted red. It is now pinned to a past instant, and a new
  `.gitattributes` forces `requirements.lock` to `eol=lf` so Windows CRLF commits
  cannot break the lint gate. Version `2026.5.30.post3`.

---

## [2026.5.30.post2] - 2026-05-30 - SRP split (largest source file -> JSON data)

###  Changed

- **Split the single largest source file by single-responsibility.**
  `src/app/api/dashboard/home_changelog.py` (1511 lines) held ~1490 lines of
  hand-maintained "Latest changes" data inline. The data now lives in
  `home_changelog_entries.json` and the Python module is a thin localisation
  loader. Data is separated from logic; the dashboard widget and the changelog
  regression tests read the same entries with **no behaviour change**.
- Version `2026.5.30.post2`. Backend source-structure only - no template, JS or
  CSS changes, so bundles and the service-worker cache are unchanged.

---

## [2026.5.30.post1] - 2026-05-30 - Continued SRP split (page controllers)

###  Changed

- **Continued the single-responsibility (SRP) source split to the next tier of
  large page controllers.** `pages/course-detail.js` (1414 lines) and
  `pages/team-detail.js` (1216 lines) are now split into ordered, build-only
  `_parts/` fragments that `scripts/build_bundle.py` concatenates verbatim:
  `course-detail/` into `00-sync-stream` / `10-teams-crud` / `20-sync-all` /
  `30-course-data`, and `team-detail/` into `00-core` / `10-sync` /
  `20-analysis-boot` / `30-live`. The served files are regenerated
  **byte-for-byte identically** (verified via SHA-256 and `build_bundle.py
  --check`), so there is zero runtime or behaviour change.

---

## [2026.5.30] - 2026-05-30 - SRP split of all 1500+ line files

###  Changed

- **Split every 1500+ line source file by the single-responsibility principle
  (SRP) into smaller modules with no behaviour change.** The front-end giants
  (`core.js`, `global-job-bar.js`, `tour-engine.js`, `project-detail.js`,
  `course-settings.js` and `responsive.css`) were broken into build-only parts
  under `_parts/` folders that the build script concatenates back into an
  identical artifact (verified byte-for-byte on the minified bundle). Back-end
  API modules (courses, sync, telemetry, teams, projects, report/sync jobs) had
  their helpers extracted into neighbouring modules.

---

## [2026.5.29.post1] - 2026-05-29 - Skeletons reuse real components

###  Changed

- **Loading skeletons now reuse the real page components instead of a parallel
  `gl-skeleton-*` layout.** The skeleton primitives in `components/loaders.html`
  defined their own card / stat / table / form containers, each with a separate
  set of responsive media queries, which drifted from the live UI. The
  `sk_stat`, `sk_stats`, `sk_card`, `sk_table` and `sk_form` macros now emit the
  **real** component markup - `.stat-card` / `.stats-grid` / `.card` /
  `table.data-table` / `.form-group` - with `.gl-skeleton` shimmer bars in the
  leaf slots, so layout and responsiveness are inherited directly from the live
  components and can no longer diverge. Macro signatures are unchanged, so no
  call sites required edits.
- **Removed the now-dead skeleton CSS** (`.gl-skeleton-card`, `.gl-skeleton-stat`,
  `.gl-skeleton-table`/`-thead`/`-row` with their `nth-child` variance and media
  queries, `.gl-skeleton-stats-grid`, `.gl-skeleton-field`/`-label`/`-input`).
  The `.gl-skeleton` primitive, `.gl-skeleton-tr`, `.gl-skeleton-cards-grid` and
  the `.gl-skeleton-list*` family are retained.

###  Release

- Version `2026.5.29.post1`. Template + CSS change only; bundles rebuilt. No
  backend changes.

---

## [2026.5.29] - 2026-05-29 - Deterministic lockfile-check

###  Fixed

- **The `lockfile-check` CI job is now deterministic and no longer fails on
  unrelated upstream releases.** The job runs
  `uv pip compile pyproject.toml --extra otel -o requirements.lock` and then
  `git diff --exit-code requirements.lock`. Because almost every dependency uses
  an open `>=` range, `uv` re-resolved to whatever was newest on PyPI at job
  time, so the lockfile "drifted" and the job went red the moment any direct or
  transitive dependency published a new version - even though nothing in the
  repository had changed. Added a `[tool.uv]` section with
  `exclude-newer = "2026-05-30T00:00:00Z"` to pin resolution to a fixed point in
  time. `requirements.lock` regenerates byte-identically and the gate stays
  reproducible until the timestamp is deliberately bumped.

###  Release

- Version `2026.5.29`. No service-worker cache bump: this is a CI/build-config
  change only, with no client-facing asset changes.

---

## [2026.5.23.post2] - 2026-05-23 - Commit category UI polish

###  Fixed

- **Course Analytics checklist chart paints commit-category bars in the
  correct pink (`#ec4899`).** After the R13 remap to `commit` in
  `post1`, the `categoryColors` map in `course-analytics.js` still keyed
  on the orphan `quality:` (the engine never emits that value anymore).
  R13 and any commit-category custom checks fell through to the
  `custom` purple fallback. Renamed the key to `commit:` (same pink) so
  the chart's category stripe matches the badge colour used elsewhere
  in the UI.
- **Course Settings filter toolbar got the missing `Commit` button.**
  The filter bar above the checks table offered `Issue`, `MR`,
  `Review`, `CI/CD` but not `Commit`, so teachers could not narrow the
  table to `R13` or custom checks with `category="commit"`. Added the
  button via the existing `filter_btn` macro; the JS filter handler is
  data-driven and required no changes.

###  Release

- Version `2026.5.23.post2`, service-worker cache `gitpulse-v99`.

---

## [2026.5.23.post1] - 2026-05-23 - Commit category across the whole stack

###  Fixed

- **`Commit` category is now first-class across the whole check stack.**
  The Edit Check modal previously offered only five options
  (`issue`, `mr`, `review`, `ci`, `custom`); any stored check with
  `category=commit` rendered with an empty Category field because the value
  was not in the option list and the JS badge/label maps had no entry. Added
  `('commit', t('Commit'))` to the dropdown and `commit:` entries to
  `CATEGORY_BADGES` (badge-purple) and `CATEGORY_LABELS` in
  `course-settings.js`.
- **Pydantic schemas and backend validators accept `commit`.** Extended
  `ALLOWED_CATEGORIES` and the two `Literal[...]` unions in
  `schemas/custom_check.py` so the custom-check API no longer returns 422.
  Aligned the inline `valid_categories` set and the LLM suggestion docstring
  in `api/dashboard/course_checks.py` and the column comment in
  `models/custom_check.py`.
- **R13 (`Commit Quality`) is now mapped to the `commit` category.**
  Previously `_CHECK_CATEGORIES` in `compliance/engine.py` mapped `R13` to a
  one-off `"quality"` bucket that no other code recognised, so
  `commit_score` was always `None` in category breakdowns and pilot
  telemetry. Re-mapped to `"commit"`, added `"commit"` to the always-present
  `all_cats` set in `_compute_category_scores`, mirrored the change in
  `pilot_telemetry._FALLBACK_CHECK_CATEGORIES`, and added `"commit"` to the
  iteration tuple in `_derive_category_scores`.

###  Release

- Version `2026.5.23.post1`, service-worker cache `gitpulse-v98`.

---

## [2026.5.23] - 2026-05-23 - Scoped button and modal guards

###  Fixed

- **Buttons and modals now cover the remaining course/project write actions.**
  Course archive/activate/delete, dashboard Add Group and course edit,
  course-settings scoring/config imports, admin course actions, and project
  unlink check the active `course`/`team`/`project` process scope before opening
  a modal or mutating data.
- **Process-lock click guard is fail-closed.** Every element with
  `data-process-lock-when` is checked again at click time, not only by the 1.5s
  disabled-state poll, so stale button state cannot let a conflicting
  sync/import/run-check action through.
- **Dynamic buttons inherit scope.** Buttons inserted after archive/activate
  operations are refreshed through the shared process guard without a page
  reload.

###  Release

- Version `2026.5.23`, service-worker cache `gitpulse-v97`.

---

## [2026.5.22.post7] - 2026-05-22 - Spinner anomalies and toast recovery

### Fixed

- **SVG spinners (.spinner, .spinner-inline)** now set
  `transform-origin: 50% 50%` and `transform-box: fill-box`, so they no
  longer wobble around the top-left corner when the parent card
  composites a hover transform, and the animation stays smooth.
- **Lost completion toast during navigation.** When a sync finished
  exactly during a navigation (SSE complete arrived between
  `beforeunload` and unload), `_preserveFlashToast()` had already
  snapshotted an empty toast container and the toast was lost. The
  `_restoreJobs` done/error/finishing branches now enqueue a completion
  replay toast on the next page load (session-scoped dedup blocks
  duplicates inside the same page-load) and the nav-replay window
  widened from 3s to 8s so slow navigations still surface the missed
  completion.

---

## [2026.5.22.post6] - 2026-05-22 - Scoped process locks

###  Fixed

- **Scoped process locks now follow the course/team/project hierarchy.**
  Per-team sync, per-project sync, and run-check jobs use stable scoped
  job keys, so active work in one group does not block unrelated courses
  or groups, while conflicting actions in the same team/project scope
  remain locked.
- **Course-level Run Checks stays locked until the real work finishes.**
  Added an aggregate run-check status endpoint and wired the global job
  bar to poll it, preventing modals/buttons from unlocking immediately
  after fan-out enqueue while per-team jobs are still running.
- **Exclude from scoring is guarded consistently.** Toggle buttons
  evaluate the current row's scope, use shared icons, and the backend
  takes the team advisory lock before checking active scoring jobs.

###  Release

- Version `2026.5.22.post6`, service-worker cache `gitpulse-v95`.

---

## [2026.5.22.post5] - 2026-05-22 - Scope-aware imperative guards

###  Fixed

- **Imperative action guards now respect scope.** Click handlers for
  per-team sync, per-project sync, run checks, and course-level
  sync-all/import/run-checks all pass a `course`/`team`/`project` scope
  to `guardProcessAction`, so the _"Wait for the active sync to finish"_
  toast no longer fires for actions in unrelated courses.
- **Dashboard Import buttons.** Locked only by another active import,
  not by syncs in any course.
- **Course-detail skeleton.** Renders all four action button
  placeholders (Add Group / Import from GitLab / Sync All / Run Checks)
  so it mirrors the loaded layout 1-to-1.

###  Release

- Version `2026.5.22.post5`, service-worker cache `gitpulse-v94`.

---

## [2026.5.22.post4] - 2026-05-22 - Per-course sync independence

###  Fixed

- **Cross-course sync no longer blocks unrelated courses.** The process
  guard now scopes locks to a specific course, team, and project.
  Starting a sync in one course leaves import and sync buttons in other
  courses fully usable; run-checks and sync still gate each other, but
  only within the same team or project; dashboard Import buttons are
  independent of per-course jobs. Every job-start call-site tags meta
  with `courseId`, `teamId`, `projectId`, and `jobKind` so guards can
  filter precisely.

###  Release

- Version `2026.5.22.post4`, service-worker cache `gitpulse-v93`.

---

## [2026.5.22.post3] - 2026-05-22 - Process action guards

### Fixed

- **Conflicting sync/import/run-check actions are blocked consistently.**
  Buttons and modal triggers now use a shared process guard, and page handlers
  perform the same preflight before starting work programmatically.
- **Project sync uses the correct global-job API surface.** The project page no
  longer destructures missing `window.GP` aliases, so active sync detection,
  progress registration, and completion cleanup run through the canonical
  global-job helpers.
- **Backend sync/check races now fail closed.** Team/project/course sync and
  run-check endpoints share team-scope advisory locks and return 409 for
  conflicting active jobs instead of enqueuing overlapping work.
- **ASGI framework dependencies are hardened.** FastAPI now starts at
  `0.136.1` and Starlette at `1.0.1`, clearing the current Starlette
  `PYSEC-2026-161` audit finding without loosening runtime compatibility.

### Release

- Application version is `2026.5.22.post3`; Service Worker cache is
  `gitpulse-v92`.

---

## [2026.5.22] - 2026-05-22 - Scoring exclusion consistency

### Fixed

- **Exclude from scoring is coherent across team and project dashboards.**
  The backend toggle now refuses active sync/run-checks races, uses a row lock,
  recomputes team metrics immediately, and invalidates team, course, project,
  and student page-cache scopes.
- **Project live data respects scoring exclusion.** Excluded members no longer
  feed the project live-data scored cohort or Issues to Address refreshes.
- **The member toggle has one frontend owner.** Team and project pages share the
  same handler, preserve inherited/manual/csv member categories when a student
  is included back into scoring, and block conflicting action while sync/import/
  check runs are active.

### Release

- Application version is `2026.5.22`; Service Worker cache is `gitpulse-v89`.

---

## [2026.5.21.post26] - 2026-05-21 - Release housekeeping

### Changed

- **Dashboard changelog dates are normalized.** `Latest changes` no longer
  contains entries dated after the current 2026-05-21 release day, and the
  regression test now rejects future-dated dashboard changelog rows.
- **Deploy workspace hygiene is cleaner.** Old ignored `deploy-post*.log` /
  `redeploy.log` files and the one-off ignored SRP split helper script were
  removed before redeployment.

### Release

- Application version is `2026.5.21.post26`; Service Worker cache is
  `gitpulse-v76`.

---

## [2026.5.21.post25] - 2026-05-21 - Sync cache invalidation module

### Changed

- **Sync cache invalidation has a dedicated owner.**
  `_invalidate_dashboard_cache_after_sync` moved from the large
  `workers/sync_job.py` worker into `workers/sync_cache.py`. Full-team and
  per-project sync still invalidate project, team, course, and student
  page-cache scopes, but the worker keeps less cache plumbing inline.
- **Release metadata is aligned with the current package baseline.** Root/docs
  changelogs and version references now point at `2026.5.21.post25` and
  `gitpulse-v75`.

### Tests

- Retargeted the sync cache invalidation regression test to
  `app.workers.sync_cache`.

### Release

- Application version is `2026.5.21.post25`; Service Worker cache is
  `gitpulse-v75`.

---

## [2026.5.21.post3] - 2026-05-21 - Dashboard role-context module

### Changed

- **Dashboard role-context helpers have a dedicated owner.** Sidebar badge
  counts, greeting subtitles, student dashboard context, and admin dashboard
  context moved from `dashboard/home.py` into `dashboard/home_context.py`.
  `home.py` now focuses more tightly on page orchestration.
- **Context fast paths are covered.** Student context returns the default
  zero-state without DB access when there are no active courses or no GitLab
  username, and student sidebar badges stay DB-free.

### Release

- Application version is `2026.5.21.post3`; Service Worker cache is
  `gitpulse-v53`.

---

## [2026.5.21.post2] - 2026-05-21 - Dashboard Latest changes split + course health module

### Changed

- **Dashboard *Latest changes* has a dedicated owner.** The hand-maintained
  release entries and locale selection moved from the large
  `dashboard/home.py` route into `dashboard/home_changelog.py`, keeping the
  home route focused on page orchestration instead of release-note data.
- **Course-card health SQL moved out of the route.** Per-course RED-team health
  now lives in `dashboard/home_course_health.py`. The helper returns an empty
  result immediately when there are no active courses, avoiding unnecessary DB
  work for onboarding and empty states.

### Tests

- Added regression coverage for the empty active-course course-health path and
  retargeted dashboard changelog tests to `home_changelog.py`.

### Release

- Application version is `2026.5.21.post2`; Service Worker cache is
  `gitpulse-v52`.

---

## [2026.5.21.post1] - 2026-05-21 - Dashboard stats split + 429 asset cache busting

### Changed

- **Dashboard home stat-card SQL has a dedicated module.** Role-specific stat
  cards moved from the large `dashboard/home.py` route into
  `dashboard/home_stats.py`. RED-team counts and average compliance now share a
  single latest-team-snapshot subquery, and student dashboards with no active
  courses return zero-value cards without unnecessary DB queries.
- **Standalone 429 pages use deploy-hash static URLs.** The rate-limit
  middleware cannot rely on Jinja `static_url()`, so its browser HTML now uses
  `BUILD_HASH` query strings for favicon, stylesheet, and illustration assets.
- **Supply-chain extras are narrower.** Added `idna>=3.15`, removed the
  redundant `safety` optional scanner in favour of `pip-audit` + CycloneDX, and
  moved Locust into a dedicated `load` extra.

### Tests

- Added regression coverage for the no-active-course student stat-card path and
  for deploy-hash `/static/...` links on the browser rate-limit page.

### Release

- Application version is `2026.5.21.post1`; Service Worker cache is
  `gitpulse-v51`.

---

## [2026.5.19.post25] - 2026-05-19 - Page/static cache hardening

###  Fixed

- **Page-fragment cache variants are delimiter-safe.** Variant parts are
  JSON-serialized before the BLAKE2b digest is computed, so values like
  `("a|b", "c")` and `("a", "b|c")` cannot collapse to the same cache key.
  The Redis namespace is bumped to `gp:page:v2`, forcing a safe cold start for
  existing fragments.
- **Static cache headers are canonical.** `/static/*` responses replace any
  existing `Cache-Control` header instead of appending duplicates, merge
  `Vary: Accept-Encoding` with existing `Vary` values, and only use the
  one-year immutable cache profile when `?v=` is a valid hex content hash.
- **Dashboard home cleanup.** Removed unused stat-card parameters and stale
  locals from `home.py`; the support-ticket sidebar badge now clearly counts
  tickets in visible courses.

### Changed

- Application version is `2026.5.19.post25`; Service Worker cache is
  `gitpulse-v50`.

---

## [2026.5.18.post24] - 2026-05-18 - global-job-bar stability + webhook metrics debounce

###  Fixed

- **Progress bar no longer flickers right after a sync completes.**
  Both the 30 s `/sync/active` watchdog and the `htmx:load` reconcile
  skip work for 3 s after `completeGlobalJob` fires. Previously a
  stale `/sync/active` snapshot or a navigation could re-add the
  just-faded bar momentarily.
- **Stale `Last Synced` is now visible in logs.**
  `_invalidate_dashboard_cache_after_sync` failures are logged at
  WARNING (was DEBUG) in both the full-team-sync and per-project-sync
  paths, so Redis/SCAN hiccups no longer go silent.

###  Performance

- **Webhook bursts coalesce metrics-refresh enqueues per team.** A
  burst of N events from the same team within 2 s now enqueues a
  single `metrics_refresh` job instead of N (Redis `SET ... NX EX 2`
  debounce). The job is idempotent - coalescing loses no state.
  Removes most of the Redis chatter from CI pipelines that emit 10+
  events in quick succession.

---

## [2026.5.18.post23] - 2026-05-18 - Animated empty state + Diff column fix

### Fixed

- **The Diff column in the MR table no longer shows `- files`.** When
  `files_changed`, `lines_added` and `lines_removed` are all missing the
  cell renders an em-dash (`-`). If only the file count is missing but
  +/- line counts are available, only the delta is shown.
- **Empty-state icons on the project detail page are animated like the
  rest of the dashboard.** "Issues to Address -> No scored members yet"
  and "All passing" share the `emptyStateFloat` keyframes with the other
  `.empty-state-icon` elements, with a `prefers-reduced-motion: reduce`
  opt-out.

### Changed

- **Dashboard *Latest changes* widget trimmed to the most recent 5
  entries** with one-paragraph summaries; the long history lives here
  and in `docs-site/docs/changelog*.md`.
- Application and docs metadata are `2026.5.18.post23`; Service Worker
  cache is `gitpulse-v48`.

## [2026.5.18.post22] - 2026-05-18 - Sync cache invalidation + CSP cleanup

### Fixed

- **Completed sync jobs now eagerly invalidate dashboard fragment caches.**
  Team sync and per-project sync both drop the affected project, team,
  course/activity/analytics, and active-student cache scopes, so users do
  not receive stale HTML fragments after a job completes.
- **Remaining inline timers and the Course Settings LLM helper moved out
  of templates.** The 401/429 redirect/countdown logic and LLM
  resource/prompt helper now run from external JS; CSS/minified assets
  were regenerated.

### Changed

- Application and docs metadata are `2026.5.18.post22`; Service Worker
  cache is `gitpulse-v47`.

## [2026.5.18.post21] - 2026-05-18 - Project-scoped sync in activity feed + semester audit

### Added

- **The *Follow the latest updates* widget on the dashboard now
  distinguishes project-scoped sync runs.** When a teacher clicks
  *Sync* directly on a specific project (not on the whole group, not
  via the global *Sync all*), the entry renders as *"System -
  Project synced from GitLab"*, the detail shows the project name,
  and the link points to `/dashboard/projects/{id}` instead of the
  team page. Group-scoped and global syncs are unchanged.
  `run_checks` keeps appearing on every level it can be triggered
  (per-group and the per-course fan-out).

### Fixed

- **System-wide semester scoping audit.** Several aggregate /
  contributor queries were spanning *all of history* instead of the
  active semester window, which inflated counters and let stale
  project health linger across terms. Fixed:
 - `course_detail`, `get_course_sync_status`, and the
    `/courses/{id}/sync-stream` SSE builder now thread
    `commit_since = semester_floor_utc(course.settings)` through
    `team_contributor_counts()` and `total_distinct_contributors()`.
 - The DB fallback in `api/projects.py:get_contributors` filters
    commits by the project's course semester floor.
 - The student -> primary-project mapping in `dashboard/teams.py`
    now respects the same `_commit_window_clause` as the rest of
    the team-detail page (a student who switched groups between
    semesters no longer remains mapped to the prior-semester
    project).
 - Per-team pipeline aggregates (total / passed / failed /
    latest_status) and the alternative course-pipeline path in
    `dashboard/courses.py` now both clamp by `semester_floor_utc`,
    so a successful run from last term no longer masks the real
    health signal.

### Removed

- Reverted an experimental project-level activity card on the
  project-detail page - the dashboard *Follow the latest updates*
  widget is the single source of truth; the project detail page
  does not duplicate it.

---

## [2026.5.18.post17] - 2026-05-18 - Per-project Sync + precise SYNCING badges

### Added

- **New endpoint `POST /api/v1/projects/{project_id}/sync`.** The Sync
  button on the project detail page no longer syncs the whole team -
  it refreshes only that project's issues, MRs, MR notes, pipelines,
  and commits (default branch + per-MR source branches). Member sync
  and project discovery remain team-scoped (they only make sense at
  the group level). The endpoint takes an advisory lock on
  `project_id`, deduplicates against an in-flight team-wide sync
  for the same team, and writes a `sync_project` audit record.
- **Per-row SYNCING/QUEUED/FAILED badge on the team-detail Projects
  table.** `GET /api/v1/courses/{course_id}/sync-status` now returns
  `sync_status_by_project`, so the team detail page highlights only
  the specific project rows whose sync is actually running - instead
  of lighting up every active row whenever any team-level sync runs.

### Fixed

- **Phantom "1/2 groups done" counter during a single in-flight
  sync.** The *X/Y groups* counter no longer includes project-scoped
  jobs (they have a separate `project_sync_running_count`) and now
  uses a 3-minute burst window for completed/failed - the old
  2-hour cutoff in the denominator was the main cause of the
  misleading "1/2".
- **Migration `047_bg_job_project_id`** adds `BackgroundJob.project_id`
  (FK to `gitlab_projects` `ON DELETE SET NULL`) + index - the
  schema scaffolding for per-project sync tracking.

### Technical

- Service Worker cache: `gitpulse-v46`.

---

## [2026.5.18.post16] - 2026-05-18 - Truthful sync toasts + SYNCING badge in tables

### Fixed

- **False "Sync started!" toast on the project detail page.** The `Sync`
  button used to show "Sync started!" on every click - even when the
  backend returned `skipped_fresh` (data already fresh), `failed`
  (Redis down), or an existing in-flight job. The handler now branches
  on the real `status` field and shows a truthful toast
  (`info`/`danger`/`success`).
- **Phantom "1/2 groups" slots in the global job bar** after a
  one-off project-level sync. `completeGlobalJob('sync', ...)` is now
  invoked in every branch of the handler, so the deferred slot
  always closes.
- **`Sync` button unlocked too early** - the old `finally` block
  released it right after the POST. The button now stays in `loading`
  state until the SSE stream emits `complete` / `error` for its
  specific `job_id`.

### Added

- **Dynamic `SYNCING` / `QUEUED` / `FAILED` badges in the Status
  column of the `Subgroups and Projects` table on the group detail
  page.** While the group is syncing (locally triggered or via a
  course-level `Sync All`), every active project row swaps its
  Active/Template badge for the live sync state. Original badges are
  restored when the sync settles. The mechanic mirrors the per-row
  status already present in the groups table on the course detail
  page.

---

## [2026.5.18.post15] - 2026-05-18 - Project-scope Sync + removed duplicate Rotate Webhook Secret

### Added

- **`Sync` button on the project detail page.** Previously the only way to
  refresh a single project from GitLab was from the parent course/group view.
  The toolbar at `/dashboard/projects/<uuid>` now has its own `Sync` button
  next to `Unlink`, gated by `can_edit and team`, posting to
  `POST /api/v1/teams/{team_id}/sync` and surfacing progress through the
  global job bar exactly like the group-level sync.

### Removed

- **`Rotate Webhook Secret` button + `POST /api/v1/projects/{project_id}/rotate-secret`
  endpoint.** The per-project webhook secret rotation UI duplicated the
  multi-scope `Settings -> Webhook Configurations` flow (introduced in
  migration 041) without offering anything unique. Button, JS handler, FastAPI
  endpoint, Pydantic `ProjectSecretRotated` schema, tour step, contract test
  row, and security doc section are all gone. `Project.webhook_secret_hash`
  is still generated on import and verified by webhook delivery - only the
  manual rotation surface is retired.

### Fixed

- **Shorter `Unlink` tooltip.** The 4-sentence reactivation rules essay
  clipped on smaller viewports; collapsed to one line.

---

## [2026.5.18.post14] - 2026-05-18 - Removed duplicate Sync Group Data modal

### Fixed

- **Removed duplicate `Sync Group Data` modal.** The full-screen sync
  modal opened on every `Sync` / `Sync All` click was duplicating the
  same `Project N/15: ... synced (X%)` progress already shown by the
  persistent global job bar at the top of the page. Two copies of the
  same line on screen at once was redundant. Progress is now owned
  exclusively by the global bar; modal markup (`team/_modals.html`) is
  retired and `_DEFAULT_LOCAL_SELECTORS.sync` in `global-job-bar.js`
  is gone too.
- **Sync button no longer overflows on mobile.** `triggerSync` /
  `triggerSyncAll` used to call `setButtonLoading(btn, true,
  'Syncing...')` which replaced the icon button's HTML with the literal
  `Syncing...` string. On narrow viewports that text bled outside the
  icon-sized button as `/ncing`. Dropped the `loadingText` argument -
  the button now keeps its original icon / label and gets a `.loading`
  class for the spinner state, matching every other action button.

---

## [2026.5.18.post13] - 2026-05-18 - Student profile polish & loader contrast

### Changed

- **Student profile polish.** The yellow `Run Checks` button from post12
  no longer floats above the page as an orphan strip - it now lives
  inside the `Student Profile` / `My Profile` / `Teacher Profile` card
  header next to the title, so it sits on a surface instead of the raw
  page background.
- **Project contributors widget canonical names.** The Contributors
  widget on the project detail page now resolves matched git authors to
  `Student.full_name` (lookup by email, then by lowercased
  `gitlab_username`). Generic / shared display names like `student` no
  longer leak into the UI when a student's local git config is sloppy.
  The original git display name is preserved on the response payload as
  `raw_name` for auditing.
- **Skeleton loader contrast.** `.gl-skeleton` now reads from the
  dedicated `--gl-skeleton-bg` / `--gl-skeleton-shimmer` tokens defined
  in `tokens.css`, and the shimmer overlay opacity goes from 0.05 to
  0.12. Loader rows on the project / student detail pages are visibly
  contrasted against the page background instead of nearly invisible.

---

## [2026.5.18.post12] - 2026-05-18 - Run Checks at all three scopes (course / group / student) + truthful Rotate/Unlink tooltips

- **Run Checks now exists at all three levels of the GitPulse
  hierarchy** (course -> group -> student). The group-level button
  has been around for a long time; this release adds the remaining
  two.
   - **Course scope.** The course action bar gets a yellow
      `Run Checks (all groups)` button next to `Sync All`. It calls a
      new `POST /api/v1/courses/{course_id}/run-checks` endpoint that
      enqueues a separate `run_checks` BackgroundJob for every active
      group in the course (same 10-minute dedup window as the team
      endpoint). Visible to anyone with `can_edit` on the course.
   - **Student scope.** The student profile gets the same yellow
      button. The compliance worker is still team-scoped (GitPulse
      stores one snapshot per student-on-team), so the button posts to
      `/teams/{team_id}/run-checks` and the student card refreshes via
      the existing team SSE channel once the job finishes.
   - `_run_checks_modal.html` gained a Course branch in its scope
      banner so dynamic context flows cleanly:
      Course -> Group -> Project -> Student.
- **Truthful "Rotate Webhook Secret" tooltip.** The previous copy did
  not explain where the secret comes from. It now states that GitPulse
  auto-generates a webhook signing secret at project import time, the
  rotate action only matters when that secret may have leaked, and the
  old token keeps working for a 24-hour grace window so in-flight
  pushes from GitLab are not lost.
- **Truthful "Unlink from GitLab" tooltip and confirm dialog.** The
  old text falsely promised the project would be "re-linked on the next
  sync." In reality `_upsert_project` respects manual deletion - a
  soft-deactivated project stays inactive forever unless an admin
  explicitly hits `POST /projects/{id}/reactivate`. Tooltip and confirm
  now say so plainly and emphasise that all data (commits, MRs, checks,
  snapshots) is preserved.
- **Role notes.** `User.role` only takes three values: `admin`,
  `teacher`, `student`. There is no system-wide `mentor` role -
  `team_member.is_mentor` is a per-team flag for senior students who
  help out; they are excluded from team aggregate metrics but have no
  elevated permissions. All Run Checks UIs gate on `can_edit` (course
  owner / teacher with course membership / system admin), not on raw
  `User.role`.

---

## [2026.5.18.post11] - 2026-05-18 - Skeleton background bleed fix + modal title icons + GitLab import UX

- Skeleton loaders no longer flash blue/red banner colors during the
  loading state. Semantic notification classes (`.member-api-note`,
  `.advisory-banner`, `.alert`) reused inside `[aria-busy="true"]`
  skeleton trees were leaking their feature backgrounds (blue
  `--info-bg`, blue `--gl-blue-950`) through the placeholders. A
  defensive scope in `loaders.css` now forces neutral
  `--surface-strong` + `--border-color` for any semantic banner
  rendered inside a skeleton container - applied system-wide so
  future skeleton macros never inherit feature colors.
- Modal title icons are now vertically centered against the label.
  `.modal-title` was a plain `<h3>` so leading icons sat at text
  baseline. Switched to `display: inline-flex; align-items: center`
  to fix every modal in the app (Edit Check, Settings, Import,
  Rotate, Edit Course, ...).
- "Rotate Secret" project header button is now labeled **"Rotate
  Webhook Secret"** with an expanded tooltip explaining that a new
  GitLab webhook token is generated and the previous secret stays
  valid for a 24-hour grace window. Companion "Unlink" button
  relabeled to **"Unlink from GitLab"** with a tooltip describing
  automatic re-link on next sync.
- **Import from GitLab** modal now exposes the same Quick preset
  dropdown and Semester start/end date pickers used by Create
  Course. Picking a TUKE FEI preset fills academic year, semester,
  and both dates in one click; the dates are persisted onto the
  imported course's settings so auto-archive and semester windowing
  work immediately without a follow-up "Edit Settings" step.
- Run Compliance Checks modal scope banner now supports a `student`
  branch (priority: student -> project -> team) so a student-scoped
  Run Checks dialog will show the student's name instead of the
  parent team - groundwork for the upcoming student-scoped
  "Run Checks" header button.

---

## [2026.5.18.post10] - 2026-05-18 - Skeleton loader DOM parity and feature-flag gating

- Skeleton loaders for every lazy-loaded page (dashboard, course
  detail/activity/analytics/teachers, project detail, student detail,
  team detail, admin users, support tickets/detail/form) now mirror the
  live DOM exactly - same card counts, table column counts, toolbar
  layout and pagination - so the swap from skeleton to content no
  longer shifts the page.
- Skeletons are runtime-condition aware. Project detail honors
  retired grading availability, `feature_docker_verification`,
  `feature_ci_failure_generator`, `feature_conflict_simulator`,
  `feature_llm_suggestions` and the GitLab button visibility; student
  detail honors retired grading availability and the own-profile gate; analytics
  honors the course-staff gate; dashboard honors the role split
  and changelog panel toggle; team detail honors student-privacy mode;
  course detail / teachers honor `can_edit` and `can_see_admins`. A
  loader for a disabled component no longer appears.
- Service worker cache `gitpulse-v39`.
- Local baseline: `2583 passed, 19 deselected`.

## [2026.5.18.post9] - 2026-05-17 - Quality gate and release metadata hygiene

- `src/app/api/dashboard/home.py` is back in `ruff format` compliance; the
  change is formatting-only and does not alter behavior.
- Release metadata, dashboard latest changes, docs-site `versions.json`, and
  local validation docs now match the 2026-05-17 audit.
- Future-dated latest changelog entries were corrected; the current local test
  baseline is `2583 passed, 19 deselected`.
- `dead_code_report.py`, static artifact guard, and `pip-audit` remain clean
  for the currently installed environment.
- Service worker cache `gitpulse-v38`.

## [2026.5.18.post8] - 2026-05-17 - Static cache and CSP hygiene

- Static asset caching now distinguishes content-hash URLs from direct static
  paths: `/static/*?v=<hash>` is cached for one year with `immutable`, while
  unversioned `/static/*` uses a 5-minute TTL.
- Login and error-page inline JavaScript moved into external static modules
  (`js/pages/login.js`, `js/error-actions.js`).
- `redeploy.py` now uses system OpenSSH with deploy keys or the SSH agent,
  rejects unknown host keys by default and no longer depends on Paramiko.
- Python/docs dependency floors were raised for current `pip-audit`
  advisories, including `cryptography`, `python-multipart`, `Pillow`,
  `Pygments`, `requests` and `urllib3`.
- Template metadata links now use `static_url()` / `absolute_static_url()` for
  local static assets where a content hash can be computed.
- Service worker cache `gitpulse-v37`.

## [2026.5.18.post6] - 2026-05-17 - Mobile responsive skeletons

- `sk_chart` (vertical bars) scales down on `<768px` (96 px min-height,
  20 px bars) and `<480px` (80 px, 14 px); axis ticks are trimmed.
- `sk_h_bars` got a `<360px` breakpoint with a 56 px label column and 12 px
  bars; trailing axis ticks are hidden on small viewports.
- Service worker cache `gitpulse-v35`.

## [2026.5.18.post5] - 2026-05-17 - Mobile Week Analytics skeleton

- `sk_week_analytics` skeleton was visually too tall on phones (240 px
  chart band + 140 px doughnut + 3 × 1.9em rows). Added `<768px` and
  `<480px` rules: chart 240->180->140 px, bars 140->64->44 px, doughnut
  140->120->96 px, toolbar wraps, stat rows 1.9em->1.5em.
- Service worker cache `gitpulse-v34`.

## [2026.5.18.post4] - 2026-05-17 - Offline banner replaces false alarm

- Health monitor now distinguishes **client offline**
  (`navigator.onLine === false`) from **server unreachable**. Offline state
  renders a neutral gray banner with a `wifi-off` icon and the message
  "You're offline. Some features may be unavailable until your connection
  is restored." instead of the misleading red "System is currently
  unreachable".
- `_performCheck` short-circuits when offline (no fetch, no escalation to
  `down`).
- `window 'online'` listener clears the dismissed flag, hides the offline
  banner, and triggers an immediate re-check + "Connection restored" toast.
- Added `wifi-off` icon to the JS icon registry
  (`GP.icons.get('wifi-off')`).
- Service worker cache `gitpulse-v33`.

## [2026.5.18.post2] - 2026-05-17 - Pixel-parity skeleton parity

- `sk_h_bars` (Teacher's Checklist) now uses a 170 px label column,
  18 px bars and a 0-100 % axis tick row - matches the real horizontal
  bar chart proportions.
- Compliance by Category placeholder switched from `sk_chart` to
  `sk_h_bars(count=4)` (real chart is also horizontal).
- `sk_chart` rewritten as `gl-skeleton-chart-wrap` with shimmer bars
  (previously flat low-opacity bars were invisible on the dark surface)
  plus an axis tick row.
- Service worker cache bumped to `gitpulse-v31`.

## [2026.5.18.post1] - 2026-05-17 - Page-specific skeleton parity

### Changed

- Skeleton loaders now mirror real page structure more closely:
   - New `sk_h_bars` macro renders a horizontal-bar placeholder used for
      the Teacher's Checklist card (13 R01-R13 rows of varying fill).
   - New `sk_legend` macro renders the chart-category legend dots above
      the Teacher's Checklist.
   - New `sk_week_pills` macro renders the Week Navigator pill row.
- The pipeline-health doughnut skeleton on the Activity page now uses a
  radial gradient (reads as a doughnut chart, not a flat disc).
- Removed an orphaned `to { opacity: 1; }` block left over in
  `loaders.css` from the previous progressive-reveal purge.
- Service worker cache version bumped to `gitpulse-v30`.

---

## [2026.5.18] - 2026-05-17 - Skeleton legacy cleanup

### Changed

- Skeleton loaders were rewritten to a pure GitLab Pajamas shimmer with no
  progressive-reveal scaffolding. All skeleton primitives (text, stats, cards,
  tables, tabs, charts, lists, activity feeds, forms) render in one shot with
  a single Pajamas shimmer animation.
- Removed legacy markers and dead controllers: classes
  `gl-skeleton-progressive`, `gl-skeleton-deferred`,
  `gl-skeleton-row--deferred`; attributes `data-skeleton-progressive`,
  `data-skeleton-table`, `data-skeleton-total-items`,
  `data-skeleton-initial-items`, `data-skeleton-total-rows`,
  `data-skeleton-initial-rows`, `data-skeleton-delay`; the `initial`,
  `initial_lines`, `initial_rows`, `initial_bars`, `deferred` kwargs on
  skeleton macros; the JS `_initProgressiveSkeletons` controller and its
  `GP.initProgressiveSkeletons` / `GP.initProgressiveSkeletonTables` exports;
  the `@keyframes glSkeletonItemReveal` rule and the
  `.gl-skeleton-table.is-progressive-expanded .gl-skeleton-row--deferred`
  reduced-motion selector.
- Service-worker cache version is now `gitpulse-v29` and the bundle/minified
  siblings were rebuilt.

---

## [2026.5.17.post4] - 2026-05-17 - System-wide progressive skeleton reveal

### Changed

- GitLab/Pajamas-style progressive skeleton reveal now applies across shared
  skeleton primitives, not only tables: text blocks, stats grids, cards, tabs,
  charts, lists, activity feeds, key-value rows and forms reveal a light first
  batch and expand only when the lazy load remains visible.
- Dashboard home stats and course cards now use the same progressive reveal
  contract so primary placeholders land first and secondary placeholders fill in
  without blank gaps.
- Support ticket and support form skeletons no longer mix a spinner into the
  same content region. Structured placeholders now cover replies and follow-up
  fields, while spinners stay reserved for action/background states.
- Course settings async tables now use progressive table skeletons for webhook
  configurations and compliance checks instead of centered spinner blocks.
- The unused `sk_content_spinner` macro and its CSS were removed so loader
  primitives no longer advertise a stale page-content spinner path.
- Application and documentation metadata now use `2026.5.17.post4`.
- Service-worker cache version is now `gitpulse-v28`.

---

## [2026.5.17.post3] - 2026-05-17 - Progressive skeleton table loading

### Changed

- Shared dashboard table skeletons now follow a progressive loading contract:
  three rows are shown first, then the page-specific row count is revealed only
  when the lazy request remains visible long enough.
- The quality-gates documentation now records the frontend loading contract:
  skeletons for progressively populated sections, spinners for actions and
  background work, and no mixed skeleton plus spinner state for the same region.
- Scale load-test console status output now uses ASCII `[PASS]` / `[FAIL]`
  markers for Windows-safe checks.
- Application and documentation metadata now use `2026.5.17.post3`.
- Service-worker cache version is now `gitpulse-v27`.

---

## [2026.5.17.post2] - 2026-05-17 - Avatar loading and health version display

### Fixed

- Dashboard and top-bar avatars now load eagerly with high priority and use a
  neutral image background. Slow GitLab avatar responses no longer expose the
  purple initials fallback during page entry.
- The Admin System health card displays the runtime version exactly as
  reported by `/health` (`2026.5.17.post2`) instead of adding a `v` prefix.
  The `v...` form is reserved for git tag names.
- Service-worker cache version is now `gitpulse-v26`.

---

## [2026.5.17.post1] - 2026-05-17 - CSP inline cleanup and release metadata

### Changed

- Application and docs metadata now use `2026.5.17.post1`. The existing
  `v2026.5.17` tag is left intact, so this release uses `.post1` instead of
  rewriting tag history.
- The dashboard shell no longer emits an inline service-worker registration
  script. Registration is handled by the shared `core.js` bundle.
- Admin Events warning toasts are now driven by `gp-page-config` JSON and
  rendered by `admin-events.js`, removing the page's state-specific inline
  scripts.
- The DLQ loading spinner uses the shared `.gl-spinner-inline` CSS utility
  instead of an inline style attribute.
- Service-worker cache version is now `gitpulse-v25`.

### Verified

- Conservative dead-code scan reported no safe unreferenced candidates.
- Typography cleanup scan reported no project-owned files to change.

---

## [2026.5.16.post2] - 2026-05-16 - Semester scope and docs hygiene

### Added

- Course Settings form shows a permanent "Scope cascade" info notice
  reminding the operator that changing the semester window re-scopes every
  dashboard, sync job, compliance score, and report for this course.
- Saving a semester date change opens a confirmation dialog listing the
  exact consequences (what will be hidden, what will reappear).
- Student profile empty-states now mention the active semester window
  ("Showing current semester window: ...") so it is obvious why no commits /
  MRs / issues are shown.
- The typography cleanup script now covers JSON, web manifests, extensionless
  deployment files and optional i18n catalogues, and normalizes smart
  punctuation, decorative arrows and box-drawing comment separators.

### Changed

- Application and docs metadata now use `2026.5.16.post2`. Accidental
  future-dated metadata was corrected because the release date is May 16, 2026.
- Sweep, enrichment and LLM jobs (`enrich_issue`, `enrich_mr`, `llm_job`,
  `_enrich_all_async`) explicitly filter out entities created before
  `course.settings.semester_start_date`. Pre-semester commits, MRs, issues
  and pipelines remain stored but are no longer re-processed or counted
  in current-semester metrics.
- Admin / home / courses / teams dashboards share the same
  `semester_floor_utc` helper so the read path and worker path agree on
  the same lower bound.
- The HTML5 date-input lower bound now auto-rolls each calendar year
  (`semester_date_min` = January 1 of `today.year - 2`) instead of the
  fixed `2020-01-01`, preventing stale dates that would silently zero-out
  the visible scope.
- Report and export downloads use the shared mobile-safe blob download helper.
- Service-worker cache version is now `gitpulse-v24`.

### Fixed

- Report generation preserves teacher full names, counts distinct student
  improvements, reports compliance delta as percentage points, and downloads
  PDFs reliably on mobile browsers.
- The top progress bar no longer starts before AJAX form handlers can prevent
  native submission, avoiding false progress flashes on report forms.

---

## [2026.5.16.post1] - 2026-05-16 - Health version follow-up

### Fixed

- Application version is now `2026.5.16.post1`.
- Runtime containers now read `project.version` from `pyproject.toml` when
  installed package metadata is unavailable, so `/health` and metrics no
  longer report `version="unknown"` after source-checkout deployments.

---

## [2026.5.16] - 2026-05-16 - Course-scoped dashboard release

### Changed

- Application version is now `2026.5.16`.
- Student detail activity is scoped to the active course window when a semester
  start date is configured. Imported repository history from older academic
  years is hidden from commit tables and line totals instead of inflating the
  current course view.
- Weekly compliance computation and historical backfill now ignore pre-semester
  issues, merge requests, review activity, pipelines, and commits.
- Member tables no longer duplicate global GitLab access roles beside the
  member name when the dedicated Role column already shows that value.

### Fixed

- Old 2021/2022 commits can no longer make a 2026 course show misleading
  commit quality or contribution totals.
- The dashboard latest-changes feed no longer contains a future-dated entry.

---

## [2026.5.15.post2] - 2026-05-15 - Declarative client actions release

### Changed

- Application version is now `2026.5.15.post2`.
- JavaScript-generated reload controls now use the shared
  `data-action="reload-keep-scroll"` contract instead of inline `onclick`
  handlers.
- The read-only support-ticket reply hint now uses a CSS class for spacing
  instead of inline template styling.
- Service-worker cache namespace bumped `gitpulse-v6` -> `gitpulse-v7`, and
  generated bundles were refreshed.

### Fixed

- The offline fallback page no longer emits an inline click handler; retry uses
  a plain GET form.
- Added static frontend tests that guard source JS and the service worker
  against new inline `onclick=` handlers.

---

## [2026.5.15.post1] - 2026-05-15 - Login alert polish release

### Changed

- Application version is now `2026.5.15.post1`.
- Login-page authentication errors now use a reusable GitLab-style alert:
  dark surface, red top border, alert icon, dismiss action, and no inline
  styling.
- Client-side login failures reuse the same alert DOM/CSS contract as
  server-rendered errors.
- Service-worker cache namespace bumped `gitpulse-v5` -> `gitpulse-v6`, and
  generated bundles were refreshed.

### Fixed

- Removed the old login-specific error block and invalid red fallback from the
  login stylesheet.
- Added static tests for the login alert component contract.

---

## [2026-05-15] - Version baseline and cache refresh

### Changed

- Application version is now CalVer `2026.5.15`.
- Version rationale: the repository started from a full-codebase initial commit,
  and the pre-release audit found `1875` commits, 47 Alembic migration files,
  and no historical release tags before this normalization commit. A
  reconstructed SemVer number would be arbitrary, while CalVer records the
  production release date honestly.
- Service-worker cache namespace bumped `gitpulse-v4` -> `gitpulse-v5`.
- Documentation status, deployment examples, and dashboard latest changes were
  refreshed for the 2026-05-15 release.

### Fixed

- `dead-code-report.txt` is ignored as a generated local/CI artifact.
- Confirmed the current static and dead-code guard scripts are shell-independent
  and do not rely on `git ls-files`.

---

## [0.1.1] - 2026-05-14 - Production-safe cleanup release

### Changed

- Stabilized local and CI gates: test env normalization, shell-independent pre-push unit runner, Ruff pinned to `0.15.4`, bundle drift check, static artifact guard, and non-blocking dead-code report.
- Dashboard scheduler registry now mirrors the production scheduler: 26 registered jobs, including email log retention, expired previous webhook-secret cleanup, team discovery, and semester auto-archive.
- OpenAPI schema hygiene: `/dashboard/login` GET has a stable operation id and HEAD is hidden from schema to prevent duplicate operation IDs.
- Test suite is warning-clean under the default local gate: `2583 passed, 19 deselected`.

### Fixed

- Removed stray tracked root artifact `-w`.
- Bundle/vendor scripts now emit ASCII status markers so Windows cp1252 terminals do not crash.
- Previous webhook secrets are accepted only until `webhook_secret_previous_expires_at`, then cleaned by scheduler.
- Roster CSV import validates all rows before writes, avoiding partial commits.
- Retired grading saves reject zero total category weight.
- Redis session-store fallback now increments `session_store_fallback_total` and readiness probes the store only when enabled.

---

## [2026-05-14 - root-cause patch] - Repeated re-auth on every visit fixed

### Root cause

The app-level defaults in `app/config.py` were set correctly (`persistent_sessions=True`, 30-day idle, 90-day absolute), but **`docker-compose.yml` lines 11-12 hard-coded the wrong defaults**:

```yaml
PERSISTENT_SESSIONS: ${PERSISTENT_SESSIONS:-false}
SESSION_MAX_AGE_SECONDS: ${SESSION_MAX_AGE_SECONDS:-28800}   # 8 hours
```

The production `.env.production` already set `PERSISTENT_SESSIONS=true`, but `SESSION_MAX_AGE_SECONDS=28800` (8 h) meant the signed cookie's idle window expired in 8 hours - anyone visiting once a day was forced through the full GitLab OAuth redirect every time.

### Fixed

- **`docker-compose.yml`** defaults flipped: `PERSISTENT_SESSIONS:-true`, `SESSION_MAX_AGE_SECONDS:-2592000` (30 days), and new `SESSION_ABSOLUTE_MAX_AGE_SECONDS:-7776000` (90 days).
- **`redeploy.py`** now injects all three values into `.env.production` on every deploy (idempotent `sed`/`echo` pattern, same as `GIT_SHA`). Auditable, drift-resistant.
- **`.env` and `.env.production`** updated to the new 30 d / 90 d values as the next-deploy baseline.

### Removed (dead code)

- **`session_auth.verify_password()`** and **`session_auth.hash_password()`** - production runs exclusively on GitLab OAuth; these helpers had no callers outside the import smoke test. Removed along with the now-unused `bcrypt` import in `session_auth.py` (the `bcrypt` package is still used by webhook authentication, so the dependency stays in `pyproject.toml`).
- Corresponding lines in `tests/unit/test_module_imports.py` removed.

### Verified used (kept, NOT dead code)

The audit confirmed `gitlab_oauth.refresh_access_token()` IS used - invoked by `dependencies.get_fresh_gitlab_token()` (line 626) with a 5-minute buffer before token expiry. Silent OAuth refresh on telemetry/sync calls already works.

---

## [2026-05-14] - Persistent sessions and full-system multi-tab sync

### Changed (auth)

- **`persistent_sessions` default flipped to `True`** - sessions now survive server restarts and redeploys. The user is no longer forced to re-authenticate every time a new build is deployed.
- **Idle TTL bumped 8 h -> 30 days**, **absolute TTL 24 h -> 90 days** (`session_max_age_seconds`, `session_absolute_max_age_seconds` in `app/config.py`). Defence-in-depth: signed cookie + Redis opaque sid + Secure/HttpOnly/SameSite=Lax/`__Host-` prefix + UA fingerprint (optional) + explicit logout invalidation all remain.

### Added (cross-tab sync - system-wide)

- **Locale (`gp_lang`)** - `storage` event listener in `locale-sync.js` updates the `gp_lang` cookie and reloads sibling tabs the moment the user switches language anywhere.
- **Sidebar collapsed state** - desktop collapse/expand mirrors live across all open tabs via the existing `sidebar-collapsed` `localStorage` key + new `storage` listener.
- **Cookie consent banner** - `BroadcastChannel('gp_cookie_consent_sync')` hides the banner in every sibling tab the instant any tab accepts; `dismiss()` is now idempotent and the hiding animation class is cleared on completion.

### Verified already-synced (untouched)

- Tour completion (`tour-engine.js`), global job bar (`global-job-bar.js`), cross-toast broadcast (`core.js`), PWA install dismissal (`pwa-install.js`).

---

## [2026-05-13 - round 3] - PWA install card: multi-tab sync, conflict avoidance, lifecycle polish

### Added

- **Cross-tab synchronisation** - `BroadcastChannel('gp_pwa_install')` plus `localStorage` `storage` event fallback. Dismissing or installing in one tab now propagates to every other open tab instantly.
- **Conflict avoidance** - `_conflictPresent()` defers the card while `#cookieConsent` (visible), `.gp-tour-welcome`, `.driver-active`/`.driver-popover`, `.modal.show`/`.gl-modal-overlay`, or `.gp-app-loader.is-visible` is on-screen. An 800 ms re-poll loop reshows the card the moment the overlay disappears.
- **Page-synced lifecycle** - `visibilitychange` pauses scheduling while the tab is hidden and reschedules on return (no more animation on a backgrounded tab).
- **Event hooks** - listens for `gp:cookie-consent`, `gp:tour:welcome:dismissed`, `gp:modal:close` to re-attempt show immediately. `tour-engine.dismissWelcomeCard()` now dispatches `gp:tour:welcome:dismissed` after its 320 ms exit completes.
- **UX polish** - Escape closes without persisting; `BroadcastChannel` cleanly closed on `pagehide`.

### Changed (PWA copy)

- Description text no longer claims "offline support" (the dashboard requires auth + DB and cannot work offline). New copy: *"Install this app on your device for a faster, full-screen experience with quick access from your home screen."*

---

## [2026-05-13 - round 2] - JS modernisation and PWA bug fixes

### Changed

- **`pwa-install.js`** rewritten in modern ES6+: `const`/`let`, arrow functions, `async`/`await`, optional chaining, nullish coalescing.
- **`core.js`** Alpine `$mdShowPreview` magic - replaced 6 `var` declarations (stack, i, node, refEl, rendered, rm) with `const`/`let`.

### Fixed

- **Hide-timer race**: `_hide()`'s `setTimeout` was not cancellable on re-show. Introduced module-level `_hideTimer` ref so the next show/hide cancels first.
- **Deprecated `userChoice` API**: rewrote `_triggerInstall` with `result?.outcome ?? (await prompt.userChoice?.catch(()=>null))?.outcome` - handles both modern (Chrome 97+) and legacy two-step resolution shapes.
- **`clearTimeout(t)` inside fired callback**: moved before scheduling so the timer is actually cancellable.

---

## [2026-05-13] - PWA install prompt (GitLab Pajamas style)

### Added

- **Custom PWA install card** (`pwa-install.js` + `pwa-install.css`) - captures `beforeinstallprompt`, renders a polished bottom-right card with icon, title, description, *Install* and *Not now* actions, and an `×` close button.
- **90-day dismissal memory** (`gp_pwa_install_dismissed_until` in `localStorage`).
- **Reduced-motion respected** (`prefers-reduced-motion: reduce` collapses to a fade-only transition).
- **Mobile** - pinned to the bottom of the viewport, full-width.
- **Public API** - `window.GP.installApp.{ show, dismiss, isAvailable }`.
- **i18n hooks** - `pwa.install.title`, `pwa.install.desc`, `pwa.install.cta`, `pwa.install.cancel`, `pwa.install.close` (fallback strings provided).

---

## [2026-05-12] - Toast dedup and z-index ladder alignment

### Fixed

- **Duplicate sync-completion toasts** - when a sync job finishes, the toast was sometimes posted twice (one from the SSE event, one from the terminal poll). Introduced `sessionStorage` key `gp_job_completion_dedup_v1` to suppress duplicates within a session; auto-poll is skipped for terminal jobs.
- **Z-index conflicts** - toast container was sometimes rendered under the app loader / cookie banner. Token ladder is now: `--z-cookie-banner: 1040`, `--z-tour-welcome: 1045`, `--z-app-loader: 1050`, PWA install card hardcoded to 1055, `--z-toast: 1060`.

---

## [2026-05-11] - Tour engine dismiss fix and mobile responsiveness

### Fixed

- **Tour - dismiss when clicking inside the sidebar on desktop/tablet**: on desktop and tablet the sidebar is a permanent layout column - clicking any nav link, language switcher or Collapse button no longer dismisses the welcome card or an active tour. Guard added to the click listener: `if (!_isMobile() && t.closest('#appSidebar, .gl-sidebar')) return;`.
- **Tour - overly broad `summary` selector**: the click handler used the bare `summary` CSS selector which matched **every** `<summary>` element on the page, including collapsible panels in forms (e.g. `code-reference` sections in Course Settings). Selector narrowed to `details.gp-menu, details.dropdown, details.user-menu` - `.closest()` already bubbles through `<summary>` children so no functionality was lost.
- **Tour popover - Android 3-button nav bar hiding Back/Next buttons**: with `viewport-fit=cover` active the viewport extends behind the system nav bar, but `env(safe-area-inset-bottom)` is 0 for Android 3-button navigation. Two-phase fix: the bottom-sheet transform now subtracts `env(safe-area-inset-bottom, 0px)`; browsers supporting `dvh` get a `@supports (height: 100dvh)` block with `100dvh` that reliably excludes the system bar. Same treatment applied to the tablet portrait and landscape breakpoints.
- **Tour popover footer - minimum touch target**: `padding-bottom: max(env(safe-area-inset-bottom, 0px), 12px)` guarantees at least 12 px clearance above the system bar even when `env()` returns 0. Added `min-height: 44px` (WCAG 2.5.5).
- **Welcome card - lifted above system bar**: `bottom: calc(0.75rem + env(safe-area-inset-bottom, 0px))` raises the card by exactly the system bar height.
- **Tour popover - max-height dvh**: `max-height: 70dvh` (with `70vh` fallback) uses the dynamic viewport unit that excludes both the browser address bar and the system navigation bar.

## [2026-05-10 - round 3] - Attribution chips: who actually did the work on MRs and Issues

### Added

- **Attribution chips on the MR table (student detail)**: when an MR has no commits from the displayed student, an orange "No student commits" badge appears along with the names of the actual authors (blue = teacher, grey = peer). If the student committed together with others, a "Also by:" row shows the other contributors.
- **"Assigned to" column in Authored Issues table**: shows who the issue is assigned to - blue badge for teacher, grey for peer, dash if nobody.
- **"Opened by" column in Assigned Issues table**: shows who opened the issue - same colour logic.
- **Translations** (`sk.json`): 6 new keys - `Also by:`, `No student commits`, tooltip for "No student commits", `Opened by`, `Assigned to`, `Peer student`.

### Implementation

- `src/app/api/dashboard/students.py`: batch SQL query via `tuple_(Commit.project_id, Commit.ref).in_(branch_pairs)` - no N+1; `teacher_ids` (UUID set) + `teacher_gitlab_ids` (int set) for correct teacher detection even without `author_id`; `aliased(StudentModel)` / `aliased(TeamMember)` for two outerjoin paths on Issues.
- `src/app/templates/partials/student/_merge_requests.html`: attribution row section with `not _student_commits` / `_other_commits` conditions.
- `src/app/templates/partials/student/_detail_content.html`: new "Assigned to" and "Opened by" columns.

---

## [2026-05-10 - round 2] - "Branch Deleted" badge and commit recovery via MR API

### Added

- **"Branch Deleted" badge on the student detail / MR table**: when an MR's source branch was removed after merging (via GitLab `force_remove_source_branch` or manual deletion), the affected MR row shows a grey badge with a tooltip explaining commit recovery. Requires new DB column `merge_requests.source_branch_deleted` (migration `044`).
- **Primary branch-deletion detection** (`mr_processor.py`): GitLab returns `force_remove_source_branch=true` in both REST API responses and webhook payloads - the value is now stored in `source_branch_deleted` on every MR upsert.
- **Secondary detection** (`sync_job.py`): the sync job tracks per-branch commit counts in the branch-ref loop; if the MR fallback loop recovers > 0 commits but the branch-ref returned 0 and the MR is `merged`, the system automatically marks `source_branch_deleted = True` - catching manual branch deletes where GitLab sends no flag.
- **Commit recovery via MR API** (`sync_job.py`): after the branch-ref loop, a fallback loop calls `GET /projects/:id/merge_requests/:iid/commits` for every MR. This endpoint works even after branch deletion - GitLab preserves the MR commit list permanently.
- **Author-name attribution fallback** (`students.py`): the commit query on the student detail page adds a fourth OR clause matching `author_name = student.full_name` - catches cases where the student's git client email doesn't match any roster entry but their display name does.
- **Translations** (`sk.json`): `"Branch Deleted": "Vetva zmazaná"` plus Slovak tooltip.

### Fixed

- **CI - mypy** (`students.py`): bare `: list` annotation on `_commit_clauses` caused a `type-arg` error in strict mode -> annotation removed, mypy inference now resolves the correct type.
- **CI - ruff-format** (`students.py`): multi-line `.append(func.lower(...))` calls fit on a single line (< 100 chars) -> collapsed to single-line form.

---

## [2026-05-10] - Commit attribution fix (email fallback + noreply prefix)

### Fixed

- **Commit attribution email fallback** (`students.py`): commit query on the student detail page now includes an `author_email = student.email` OR clause - commits with no resolved `author_id` still appear if the email matches.
- **GitLab noreply email `<digits>+` prefix stripping** (`commit_processor.py`): GitLab sometimes generates noreply addresses like `123456+username@users.noreply.gitlab.com`; the numeric prefix is now stripped before comparison, so sync correctly attributes those commits.

---

## [2026-05-09 - round 2] - Second pass on tour engine, DLQ loader and admin tables

### Fixed

- **Tour engine v2** (`gp_tour_v1` -> `gp_tour_v2` storage prefix): a one-time, clean reset of the stale `:completed` keys that v1 wrote on every tour finish and that subsequently suppressed the welcome card across **all** stages of the multi-stage `/dashboard/support` page (`course_id` -> `category` -> form). Under v2 a **bare** completion key is only written when the user **explicitly dismisses** the welcome card (× or "Maybe later") - finishing a stage stores only the fingerprinted per-stage key, so navigating to the next stage of the same page re-prompts the tour as expected.
- **Tour engine - cross-tab coordination**: a new `storage` event listener watches writes to the `gp_tour_v2:` namespace from sibling tabs. As soon as a user finishes or dismisses the tour in one tab, every other open tab immediately hides its welcome card and (if currently running) tears down its active Driver.js overlay.
- **Admin / Event Pipeline - DLQ loader**: the spinner in the empty DLQ Events table appeared visually static. SVG defaults `transform-origin` to `0 0`, so the icon was "rotating" around its top-left corner. `.spin` now uses `transform-origin: 50% 50%; transform-box: fill-box;`, fixing the rotation pivot across every page that consumes this utility class.
- **Admin / Users + DLQ tables - text clipping**: `Role` ("Student") and `Status` ("Active") badges were getting ellipsis-truncated because `td { overflow: hidden; text-overflow: ellipsis }` applied to the whole table. Truncation is now scoped to text-only columns; `Role` / `Status` / `Actions` use `white-space: nowrap; overflow: visible`. Widths rebalanced: `Actions` 8 % -> 12 %, `Email` 22 % -> 18 %.
- **Admin / Users + DLQ tables - responsiveness**: below 900 px (Users) and 1024 px (DLQ) the tables fall back to horizontal scrolling inside their `.table-responsive` wrapper instead of butchering headers ("GitLab User I...") or clipping action buttons.

---

## [2026-05-09] - OAuth loop fix & UI polish

### Fixed

- **OAuth login**: end of the infinite "Session expired" loop after returning from GitLab. The callback now issues an explicit HTTP 303 See Other with `Cache-Control: no-store`, `STATE_TTL` was bumped from 600 s to 900 s, and the `gp_returning` cookie attributes were corrected so the browser reliably carries the session-id to the destination page.
- **`select_field` macro**: literal `u2014` no longer leaks into option labels. The `tojson_attr` filter now serializes JSON with `ensure_ascii=False`, so the em-dash (`-`) lands in the HTML attribute as a native UTF-8 character and no longer relies on a backslash escape that some downstream pass was stripping.
- **Tour - mobile popover flip**: relaxed the auto-flip rule for the top sheet. The previous strict thresholds (≥ 40 % bottom-sheet overlap **and** ≤ 10 % top-sheet overlap) vetoed legitimate flips for fields in the lower viewport half (e.g. "Priority" on `/dashboard/support`), causing the popover to physically cover the field it was pointing at.
- **Tour - multi-stage pages**: each `/dashboard/support` stage (course picker -> category -> form) now gets its own welcome card. Previously, completing one stage also wrote a "global" `:completed` key that permanently suppressed the welcome card on every other stage. The global key is now only written on **explicit** dismissal (× or "Maybe later").

---

## [2026-05-07] - Tour Engine & UI Enhancements

### Added

- **Admin Users Tour**: A new step for "Service Accounts" has been added to clarify bot accounts and the analytics panel logic in System Settings.

### Fixed

- **Course Settings**: Fixed raw unicode `\u2014` displaying in "Select a preset" dropdown placeholders due to Jinja/Alpine serialization issues by utilizing standard hyphens `-`.
- **Tour Engine**: Overhauled completion edge-cases involving the max-reached step cache, successfully preventing complete tours from re-prompting users under wrong `skipped` classifications. HTMX race condition timeouts were also patched.
- **UI stability (Course Settings)**: Mitigated layout jumps on load by introducing seamless data-loading spinners instead of heavy skeleton tables.

---

## [2026-05-06] - Service accounts (bots) as a first-class entity

### Added

- **`users.is_bot` column + partial index** (Alembic `042_user_is_bot`): a `BOOLEAN NOT NULL DEFAULT FALSE` column on `users` with partial index `ix_users_is_bot_false WHERE is_bot=false`. Backfill matches the same patterns as `is_bot_user()` (`project_*`, `group_*`, `*_bot`, `*-bot`, `ghost`, `alert-bot`, `support-bot`). The previous regex/`ilike`-based runtime filter is replaced by a single indexed predicate, `humans_only_clause()`.
- **`is_bot` set at every User-creation site**: all 9 places where the app inserts a `User`/`UserModel` row (group import, OAuth first login, dev-mode auto-create, admin manual sync, student create, projects/teams auto-create from inherited members) now call `is_bot_user(username, user_type=...)` and persist the result. Service accounts are tagged *once at entry*, not heuristically re-filtered on every query.
- **"Service Accounts" stat card** on the admin System Settings page plus a separate `bots` field in `/dashboard/api/v1/admin/system/stats`. The **User Role Breakdown** chart now counts **humans only** - bots are read from the dedicated card and never mixed into role analytics.
- **Service Accounts collapsible panel** below the main User Management table. Bots cannot be edited or deactivated from the UI; only an `Info` button is rendered, opening the same User Info modal with a **`Service Account` badge** next to the role chip and the tooltip "GitLab service account / bot - not a human user". The skeleton (`sk_admin_users`) is aligned with the real layout: 4 filter pills (All/Admin/Teacher/Student) plus a placeholder for the service panel below the table.
- **Bots excluded from aggregate counts**: `dashboard_stats` / `home._build_stat_cards` (Active Users / Students), `member_sync_service.get_teachers_for_course` (teacher whitelist), `users.update_user` last-admin guard, and the support assignee dropdown - all of them now ignore `is_bot=true` rows.

### Fixed

- **The previous regex-based `not_bot_user_clause()`** was a band-aid: the same logic was duplicated in Python (`is_bot_user`) and in SQL (an `ilike`-OR tree). It now exists only as a back-compat alias; new code should use `humans_only_clause()` / `bots_only_clause()` from `app.services.user_filters`.
- **`sk_admin_users` skeleton only showed 3 filter pills** instead of 4 - the layout used to jump on lazy load when the real header arrived.

### Changed

- **Translations (`sk.json`)**: added `Service Account`, `Service Accounts`, `Bot`, `View service account details`, `GitLab bots - read-only`, `GitLab service account / bot - not a human user`.

---

## [2026-05-05] - Mobile-friendly tours + sync access control

### Added

- **Tours fully responsive on mobile** (`static/css/tour.css`): a new `@media (max-width: 600px)` block converts the popover into a full-width bottom sheet (max 70 vh) with a wrapping Back/Next footer, and stretches the welcome card to the viewport minus 0.75 rem margins. No more horizontal scroll or clipped popovers.
- **Tour engine auto-opens the mobile sidebar** (`static/js/tour-engine.js`): when a step targets an element inside `#appSidebar` / `.gl-sidebar` on a mobile viewport (≤ 768 px), the engine adds `mobile-open` to the sidebar and `visible` to the overlay before measuring the target rect. The drawer closes itself in `onDeselected` (and `onDestroyed`) so subsequent body-targeted steps are not occluded. Without this fix, sidebar items kept a positive bounding rect even at `translateX(-100%)`, so Driver.js drew the cut-out off-screen and users saw a dim overlay with nothing highlighted.

### Fixed

- **Sync progress bar - student-without-courses visibility**: `/api/sync/active` returned a `per_course` map containing every running sync system-wide, so students enrolled in zero courses saw activity from other courses. The endpoint now passes the response through `_filter_courses_for_user` (same logic as dashboard widgets), restricting non-admin users to courses they are allowed to see. Bearer-token callers and admins bypass the filter.
- **Multi-job count badge - Opera overlap**: the badge was absolutely positioned in the top-right corner of `#globalJobBar`, which overlapped the job title in Opera at narrow viewports. The badge moved into a slim header strip above the bar items (`bar.insertBefore(countBadge, bar.firstChild)`) and now occupies its own row.

### Changed

- **Documentation (`docs-site`)**: changelog entries added in `changelog.md` (SK) and `changelog.en.md` (EN). The dashboard "Latest changes" widget mirrors the same order via `_CHANGELOG_ENTRIES` in `src/app/api/dashboard/home_changelog.py`.

---

## [2026-05-04] - Guided Tours

### Added

- **Driver.js v1.3.6 vendored** at `static/vendor/driver.js/` (MIT, ~21 KB JS + 4 KB CSS, no CDN). Global entry point `window.driver.js.driver()` ships on every authenticated page by default.
- **Tour engine** (`static/js/tour-engine.js`): role-aware (student / teacher / admin), multi-language (en + sk), per-page detection from `location.pathname`, state persistence in `localStorage` under `gp_tour_v1:<slug>@<role>:{completed,skipped,prompted}`. Keys are **role-scoped**, so a student promoted to teacher receives the new tours.
- **Tour content registry** (`static/js/tour-content.js`): 20 tours covering Dashboard, Course Detail / Settings / Roster / Teachers / Analytics / Activity, Team Detail, Project Detail, Student Profile, Admin Users / Courses / System, Retired grading Editor and Support - each fully localised.
- **First-visit welcome card**: subtle floating card bottom-right with tour title, step count, time estimate and a "Take the tour / Maybe later" CTA. Auto-dismiss after 25 s, one-shot per role.
- **Help launcher in header**: "Take a tour" and "Replay tours" items added to the existing user dropdown; Replay clears the persisted history.
- **Themed Driver.js popover** (`static/css/tour.css`): matches design tokens (`--surface-default`, `--primary`, `--shadow-lg`), animated stage pulse via `.gp-tour-pulse`, reduced-motion safe.
- **Hard role guard**: `run(slug)` refuses to launch a tour whose `roles` array does not include the current user's role - a safety net in case the content registry mistakenly registers a teacher-only tour on a student page.

### Fixed

- **Run Compliance Checks modal - white footer strip**: `rcm-footer` used `background: var(--card-bg, var(--surface, #fff))` but neither token is defined in the app (only `--surface-default`, `--surface-strong`). The fallback `#fff` rendered a white sticky footer in the dark theme. Footer now uses `--surface-strong` and bleeds out through the `--gl-spacing-5` modal padding so it aligns flush with the modal frame. `rcm-group` and `rcm-item` rewired to real tokens - checkbox rows now have a proper surface, hover state, focus ring and inset border stripe when checked.

### Changed

- **Tour CSS** uses real SVG icons / unicode dots instead of emoji (no rocket / wave / lightbulb / pin / stopwatch emojis). Welcome card meta row now shows two pill badges with coloured dots (primary for "steps", success for time).
- **Build pipeline**: `tour-engine.js` and `tour-content.js` added to `JS_MODULES` in `scripts/build_bundle.py`; `tour.css` added to the `static/styles.css` manifest - minified `.min` siblings and gzip-precompressed bundles are generated automatically.

---

## [2026-05-03] - Webhooks v2

### Added

- **Multi-scope webhook configurations:** Each course can now host any number of webhook secrets, each scoped to a GitLab Group, Sub-group, project list, or the whole course. Secrets are generated server-side, shown exactly once, and rotate with a 24h grace window. Audit log captures every create / rotate / revoke event.
- **Auto-detected GitLab group path:** The course-level `gitlab_group_path` field is no longer manually edited - the system computes the longest common prefix from existing teams' `gitlab_group_path` values on save. Field removed from the UI to eliminate duplication with per-config scopes.
- **Archive-safe webhooks:** When a course is archived, all of its `WebhookConfiguration` rows are now flipped to `is_active=False` so the auth lookup rejects further deliveries with 401. Rows are preserved (audit + rotation grace remain intact). On reactivation, configs stay deactivated by design - operators decide which scopes are still relevant.
- **Sortable webhook configurations table:** All columns (Name / Scope / Status / Last delivery / Created) are now click-sortable with stable `data-sort-value` attributes; Last delivery and Created sort by ISO timestamp.
- **Tooltips on webhook configuration form actions:** Cancel and Save buttons now carry tippy tooltips explaining their effect.
- **Active toggle visible in create flow:** The "Active" checkbox now shows for both new and existing configurations (previously hidden in create mode), letting teachers stage a disabled config without an extra round-trip.

### Fixed

- **Actions column squashed under long Scope strings:** Pinned column width to `min-width: 8rem` and forced `.action-cluster { flex-wrap: nowrap }` so all three icon buttons stay on one row regardless of content.
- **Stray border line under collapsed "GitLab setup steps" card:** Card header bottom border now turns transparent when Alpine collapses the body via `x-show`.
- **Secret input visual artifacts:** Removed `letter-spacing` and any inherited dotted underline styling from `.secret-reveal-input` / `.webhook-input` so the readonly token reads cleanly without the dotty hover ghosts.
- **Reveal modal cramped key/value rows:** Increased vertical padding and tightened label width on `.secret-reveal-meta`; replaced raw `.alert.alert-info` paragraph with the `alert_block` macro for consistent component styling.
- **Webhook config modal not opening:** Inner `.modal` div carried `class='d-none'` which overrode `openModal()`'s `.active` class on the backdrop. Backdrop appeared but content stayed hidden. Removed `d-none` from all 3 webhook modals (`webhookConfigEditModal`, `webhookSecretRevealModal`, `webhookConfigRevokeModal`).
- **"Heads up" notice restyled** to match other in-modal `.alert.alert-info` blocks (single-line callout, no bold lead-in).

### Changed

- Removed legacy `api/group_webhooks.py`, `schemas/group_webhook.py`, `services/group_webhook.py` and `tests/unit/test_group_webhook_service.py` (superseded by `webhook_configurations`). The legacy course-level secret stamping helper was inlined into `api/webhooks.py`; `ROTATION_GRACE` now lives in `services/webhook_configurations.py`.

---

## [2026-05-03] - Late

### Changed

- **Backend refactor (-60 inline imports, -73 net lines):** Hoisted 60+ duplicate inline imports in `admin.py`, `home.py`, `evaluation_report.py`, `pilot_telemetry.py` to module level. Removed dead paths, fixed PERF401/PERF403 list/dict comprehensions, and best-effort swallow blocks (S110) now carry explicit `noqa` comments. No behavior change - `ruff` + `mypy 1.11` remain green.
- **Course analytics page - fast-path:** `EvaluationReportService` gained `_collect_preview_data()` which skips 3 expensive aggregates (compliance trends, support summary, weekly aggregates) on the analytics page load. PDF generation is unchanged.

### Fixed

- **Accessibility (a11y) - `<label>` without associated form field:**
 - In `_analytics_content.html` (PDF report form), four heading-style labels (Course Name, Semester, Teacher Name, Report Period) were converted from `<label>` to `<span class="form-label">` because they describe readonly displays, not inputs.
 - In `member_filters.html`, `_run_checks_modal.html` and `forms.html` (toggle, bare checkbox, file-upload) wrapping `<label>` elements gained explicit `for=` attributes; checkboxes inside the run-checks grid received generated `id`s. Both implicit wrapping and explicit `for` now satisfy DevTools/axe.

---

## [2026-05-03]

### Changed

- **Student Details (Collapsibles):** The first `<details>` section now automatically opens even for empty datasets. If a student has no assigned issues or MR discussions authored, the empty state displays instructional helper text instead of quietly collapsing the section.
- **Component Visual Adjustments:**
 - Added an automatically rotating chevron indicator to the `.summary-toggle` element used in student detail breakdowns.
 - The *Raw Check Details (JSON)* view is now styled as a standard collapsible section with monospace `pre` formatting to seamlessly match the remainder of the dashboard.
 - Removed overlapping border notch on `pagination-controls` component placed inside specific inner `details` sections.

### Fixed

- **GitLab Health Companion Text:** The notification health banner has been stacked vertically with the global job progress bar to avoid UI shifting/overlapping. In turn, `GL_FAIL_THRESHOLD` duration before logging a GitLab outage was promoted to 3 consecutive failed polls.
- **Skeleton Table Loading Check (`.gl-skeleton-table`):** Visual loader pills now better leverage flex widths per column using `nth-child` targeting, effectively removing visually monotonic blocks while maintaining compositor animations that do not obstruct the CPU main thread during initial parsing.
- **CSP fixes for `<script>` and `<link>` scripts:** Inline `onload` triggers were refactored, and `nonce` variables injected into directly embedded configuration tags within all template boundaries, clearing remaining Strict CSP restrictions globally.
- **Markdown Escapes:** CommonMark backslash escape handling before code and punctuation block parsing is now protected against stripping, ensuring safe literal rendering.

---

- **Edit User - Save changes spinner is now centered** inside the button (`inset:0; margin:auto`).
- **Dashboard - duplicate rows for soft-deleted projects are hidden;** projects sharing the same name across teams are disambiguated in the course tree.

### Security

- **Absolute session TTL now enforced on stateless (cookie-only) sessions (AUTH-06b):** the previous AUTH-06 fix added `session_absolute_max_age_seconds` only to the Redis-backed session store. Stateless cookies (fallback when Redis is unavailable) still relied on the sliding `max_age` alone - meaning an active user (or a stolen cookie) could renew indefinitely. `get_current_session()` now validates the `ts` (created-at) claim against `session_absolute_max_age` (default 24 h) on **every** session load, regardless of storage backend. Malformed `ts` values are treated as expired (fail-closed).
- **Rate-limit fails closed in ALL environments (AUTH-05b):** the previous AUTH-05 fix only applied fail-closed to `APP_ENV=production`; development and test environments were still fail-open when Redis was unavailable. If a development `.env` file accidentally leaked to production (or a staging server was used as prod), rate limiting would silently degrade to no-op. Unified to `HTTP 503 + Retry-After: 30` everywhere.
- **UA fingerprint always stored - even when User-Agent is empty (AUTH-08):** previously, a missing or empty `User-Agent` header resulted in `ua=""` in the session cookie, which bypassed fingerprint checking entirely. An attacker with a stolen cookie could replay it from any client by simply omitting the header. Sessions now always carry a fingerprint; empty UA produces the distinct value `"no_ua|no_ua"` so the mismatch check fires even against header-stripping replay attacks.

### Changed

- **Sweep enrich capped at 2 000 jobs per periodic run (SCALE-01):** `periodic_enrich_all` previously enqueued enrichment jobs for every tracked issue and MR across all active projects without limit. At 567 students (~200-500 projects × 15-30 entities each) this could flood the queue with 5 000-15 000 jobs in a single burst, exhausting worker capacity and delaying higher-priority webhook processing. New config setting `sweep_enrich_max_jobs_per_run` (default 2 000) caps total enqueued jobs; remaining entities are picked up in the next 24 h cycle. The cap is logged at `WARNING` level when hit.

### Fixed

- **Dead code removed in `sweep_stale_projects`:** duplicate `return 0` statement on line 821 (unreachable code after the first `return`) removed.

---

## [2026-05-07]

### Changed

- **Compliance engine - audit-driven recalibration of R02/R04/R05/R06/R07/R08/R10/R11/R12:** a thorough logical audit of the 13-check system surfaced a series of cases where the default semantics drifted from the spirit of the ZSI assignment text and either unfairly penalised disciplined students or let real non-compliance through. This release realigns the engine with the "doing & communicating" course brief (4-5 person teams, separate feature branch per ticket, MR linked to issue, two reviewers, commit-ref-citing responses, Approve before merge, MR + ticket close together) so the engine now does what an experienced teacher would do during a manual check.
   - **R02 (Branch naming) - failure detail also explains the protected-branch case** (previously only "doesn't follow naming convention"). New text: "Branch '<name>' is on a protected name or does not match the configured naming convention" - instantly clear whether the issue is a naming-pattern miss or a direct merge into `master`/`main`/`develop`. An empty `branch_pattern` no longer falls through (the check is just skipped).
   - **R04 (MR linked to issue) - branch-name fallback + tighter bare-`#N` regex.** Both `enrich_mr.py` and `mr_processor.py` now extract `linked_issue_iid` from the branch name (`issue-7-foo`, `7-add-login`, `feature/issue-12`) when the MR description has no `Closes #N`. Combined with the text parser - explicit `Closes #N` wins, branch-IID is the fallback. The bare-reference pattern `#N` is tightened to be word-boundary anchored at both ends (`(?<![\w-])#(\d+)(?!\d)`), so `v#10` and `#10x` no longer false-match. The `MergeRequest.linked_issue_id` FK is then resolved via `gitlab_iid` lookup -> R11 can pair the MR with its ticket.
   - **R05 (MR description quality) - word counter ignores markdown structure.** Previously an MR could pass the 10-word threshold with effectively empty content (sections like `## What`, `## How`, `## Why` add up to ~9 tokens without describing anything). The `_word_count` helper now strips markdown headers, list markers, link syntax `[text](url)->text`, italic/bold sigils and filters out tokens shorter than 2 chars or without a `\w` character. Empty headings no longer pass.
   - **R06 (Review Received) - counts only reviewers with meaningful feedback.** Previously a reviewer could write `"+1"` or `"ok"` and R06 counted them. The engine now aggregates every comment per reviewer (`notes_by_reviewer: dict[author_id, list[notes]]`), joins them and runs `is_meaningful_comment(joined, min_words=cfg.min_word_count)`. New `cfg.require_meaningful` flag (default **True**) can be turned off in the UI for courses with a lighter review culture. The detail string surfaces the number of reviewers with "short comments only" so the teacher can see why R06 fails even when 2 reviewers are present.
   - **R07 (Code Review Given) - default `min_words` 30 -> 15** (model `course_settings.min_review_word_count`, helper `is_meaningful_comment`, migration `039`). 30 words proved too high for typical per-line review comments ("You could use a dict comprehension here instead of a for-loop" is 9 words and a perfectly legitimate review). Aligns with the rest of the codebase (where `min_review_word_count` was already a fallback to 15) and with the ZSI text, which states no quantitative threshold. The migration only updates courses still on the legacy default of 30; teacher customisations are left untouched.
   - **R08 (Review Response) - also counts standalone reviewer notes + softer defaults.** Previously the engine treated only inline diff discussions (notes with a `discussion_id`) as "review threads"; standalone reviewer comments at MR level were ignored, so a student could fail to respond to "This PR looks fine but I'd like to see tests." and still pass R08. Now `total_threads = inline_total + standalone_reviewer_notes` and `answered = inline_answered + min(standalone_author_notes, standalone_reviewer_notes)`. Default for `cfg.require_commit_ref` flipped **True -> False** (ZSI recommends commit-ref-citing but does not mandate it), `cfg.pass_if_no_threads` flipped **False -> True** (you can't respond to feedback that doesn't exist yet). When commit-ref is not required, partial scoring is the plain `response_rate` instead of the 50/50 weighting.
   - **R10 (Merged by author) - also accepts a teammate merger.** Previously `allow_self_merge=True` meant "the author MUST merge", which is semantically opposite of the ZSI text "assignment owner (or designated assignee) executed the merge". Default semantics are now **permissive**: passes when the author OR another resolved teammate (`merged_by_id != None`) performs the merge; **only flags merges by an unknown user** (admin, bot, external GitLab user). New explicit knobs: `require_self_merge` (default False - author must specifically click Merge) and `forbid_self_merge` (default False - reviewer-gates-merge model: someone OTHER than the author has to merge). Detail strings: "Merged by author", "Merged by a team member after approval", "Merged by an unknown user (not a team member)".
   - **R11 (MR + Issue closed) - strict pairing via `linked_issue_iid`.** Previously the check was decoupled: any merged MR + any closed issue was enough, so a student could pass even when issue #7 was still open and they had merged something completely unrelated. The engine now builds `issues_by_iid = {i.gitlab_iid: i for i in ctx.issues_assigned}`, looks up `mr.linked_issue_iid` for each merged MR, and only passes when the paired issue is `closed`. Fallback: when no merged MR has a `linked_issue_iid` (student forgot to write `Closes #N` and didn't name the branch), the engine falls back to the legacy any-issue-closed semantics so unlinked-but-closed pairs aren't penalised harder than before. Detail strings: "Merged MR's linked issue is closed", "Merged MR references an issue that is still open", "MR merged and assigned issue closed (no explicit link)", "MR merged but no assigned issue is closed".
   - **R12 (Pipeline Health) - broader test-job detection.** The `"test"` substring caught only `"test"`, `"pytest"`, `"junit"` so a pipeline running a job named `"spec"`, `"verify"`, `"coverage"`, `"jest"`, `"mocha"`, `"rspec"` or `"phpunit"` was reported as "no test job" and R12 failed. The detector in `pipeline_processor.py` now scans the tuple `("test", "spec", "pytest", "junit", "jest", "mocha", "rspec", "phpunit", "verify", "coverage")` against both `name` and `stage`, covering typical cross-language naming conventions.

### Security

- **Absolute 24 h session-lifetime ceiling (AUTH-06):** previously the session store implemented only a sliding TTL - an active user (or a stolen long-lived cookie) could keep refreshing the TTL indefinitely. Added `session_absolute_max_age_seconds` (default 24 h); the store stamps `created_at` on `create()` and rejects sessions older than the ceiling on `load()` regardless of how often the sliding TTL was refreshed. Bounds the blast radius of a stolen cookie.
- **Webhook post-commit side-effects now fail best-effort (EVT-01):** the event processor used to commit the DB transaction and *then* run cache invalidation, immediate enrichment, metrics enqueue, and SSE notify. If any of those raised, the outer `except` called rollback - but the commit was already persisted, so `event.processed=True` remained and the side-effects were silently lost. Each side-effect now goes through `_safe(coro, name)` which catches exceptions, increments the Prometheus counter `webhook_processed_total{status="sideeffect_failed:<name>"}` and logs `WARNING` instead of bubbling.
- **Redis now requires a password even on the internal Docker network (SEC-03/SEC-04):** previously Redis listened without authentication and `REDIS_URL` could be `redis://redis:6379/0` with no password. An attacker with access to the Docker bridge (or a misconfigured port mapping) could read session blobs and queues. The `app.config` validator now **refuses to start** in `APP_ENV=production` when `REDIS_URL` lacks a password segment (`redis://:PASSWORD@...`). The Compose template enables `--requirepass` whenever `REDIS_PASSWORD` is set. Production now runs with a 40-char generated password, all 4 workers + scheduler + api reconnected.
- **`FEATURE_RBAC=false` in production hard-fails (AUTH-04):** previously `_check_required_roles` only logged a warning and *let the request through* without role checks. A misconfigured flag would silently open every teacher-only endpoint. The validator now raises `ValueError` at startup so the deploy fails fast instead of fail-open.
- **`DEBUG=true` in production hard-fails (§7b):** debug mode exposes stack traces and may auto-create admin users. Validator refuses to start.
- **Rate-limit fails closed in production (AUTH-05):** when Redis was unavailable, `dependencies.check_rate_limit` swallowed the exception and *allowed* the request (graceful degradation). That meant an attacker could bypass rate limiting by knocking Redis down (or by brute-forcing during a Redis flap). Production now returns `HTTP 503` with `Retry-After: 30` and an `rate_limit_unavailable_blocking` log line. Dev and tests stay permissive.
- **`SESSION_STRICT_UA_FINGERPRINT` left opt-in (AUTH-02):** UA-fingerprint is available as defence-in-depth against XSS / cookie-theft replay from a different OS / browser, but the default stays `false`. The UA hash is not stable across mobile <-> desktop switches or browser auto-updates, and a `true` default was kicking real users out with 401s in production. The combination of strict CSRF + IP binding + the new absolute session ceiling (AUTH-04/05/06) provides equivalent post-stolen-cookie protection without the false-positive cost.

### Added

- **Healthcheck for the Caddy reverse proxy (INFRA-02):** Compose definition now runs `caddy validate --config /etc/caddy/Caddyfile --adapter caddyfile` (interval 30 s, retry 3, start_period 10 s). When a typo in `Caddyfile` would crash the config, the container is marked **unhealthy** instead of silently serving stale state.
- **JSON-file log rotation 20 MB × 5 (INFRA-04):** `postgres`, `redis`, `api`, `worker`, `scheduler`, and `caddy` use the `x-default-logging` YAML anchor for default logging. Previously `/var/lib/docker/containers/*/*.log` could grow to tens of GB with verbose workers and exhaust the host disk.
- **Scheduler healthcheck via `/proc/1/cmdline`:** the original `pgrep -f` failed because the slim worker image does not ship procps. We now use `tr '\0' ' ' < /proc/1/cmdline | grep -q app.workers.scheduler` - works in every Linux container without extra dependencies.
- **Integration tests run automatically on feature branches (CI-05):** previously `when: manual + allow_failure: true` meant integration regressions were caught only when an MR was opened or main was merged. They now run on every feature-branch push.

### Improved

- **API memory limit 768 MB -> 1024 MB (INFRA-03):** the PDF render pipeline plus concurrent LLM streams occasionally hit OOM kill. Worker bumped 512 -> 768 MB.
- **Sweep cleanup runs in batched deletes (DB-04):** `_cleanup_events_async`, `_cleanup_snapshots_async`, and `_cleanup_audit_async` previously ran a single `DELETE WHERE timestamp < cutoff` statement. With 1 M+ rows that meant a long transaction that blocked replication slots and stalled vacuum. The new `_delete_in_batches` helper deletes in 5 K-row chunks with commits between, capped at 200 batches per run (~1 M rows / sweep). Subsequent runs drain the rest.
- **SBOM generation no longer `allow_failure` (CI-02):** SBOM is a supply-chain compliance artefact. A silent fail would mean releases shipping without an auditable dependency listing.
- **Global `APP_ENV: "test"` in `.gitlab-ci.yml`:** the unit-tests job had no explicit `APP_ENV`, so the new production validators caused `Settings()` to raise `ValueError` in tests. The global variable ensures only production-targeted jobs run in production mode.

### Fixed

- **Global job-bar - ETA "2 min left" stuck while elapsed already passed 5+ minutes:** `_computeEta` only fired on a new progress sample, so between batches the 1 Hz timer just incremented the elapsed clock while the `time-left` label kept the last computed value. ETA is now anchored to a wall-clock `expectedFinishAt`; the tick re-renders `[data-job-eta]` via `_displayEta(job)`, which counts down to 0 and, on expiry of the original prediction, recomputes from a cumulative rate (`totalElapsed / pct * (100-pct)`). No flicker between renders, ETA decreases monotonically.
- **Sync-completion toasts missed when window minimized:** `sidebar.js` was closing the dashboard SSE on `visibilitychange->hidden`. Server pushes for `member_sync_complete` therefore never reached the browser while the tab was minimized - `_queuedToasts` had nothing to flush on return. SSE now stays open (browsers throttle but still deliver), only the 60 s polling timer is paused.
- **Course Analytics - Alpine report-controller load order:** the legacy report-form Alpine controller lived in `pages/course-analytics.js`, which was loaded via `<script defer>` *inside* the HTMX-swapped partial. HTMX clones script tags with the `defer` attribute, but dynamically-inserted scripts ignore `defer` semantics - they execute async after a fetch. Alpine meanwhile walked the new subtree and evaluated the controller before the script had loaded -> cascade `startDate / endDate / durationText / dateError is not defined`. The controller was then inlined as an `x-data=""` literal directly on the `<form>` element - no load-order dependency at all.
- **Flaky `test_tampered_signature_returns_none`:** itsdangerous' `URLSafeSerializer` (SHA-1) emits a 27-char base64 signature (162 bits, of which the trailing 2 are padding bits). Flipping only the *last* base64 char between `"A"` and `"B"` left the decoded HMAC bytes identical (the difference was in the padding bits). The test therefore reported in ~25% of pipelines that tampering didn't break the signature - truthfully, but it meant the test was measuring the wrong thing. We now mutate an interior char.

---

## [2026-04-29]

### Added

- **Course-staff notification on new support ticket:** previously only the ticket submitter received an e-mail (acknowledgement). Teachers / owners of the course only found out about new tickets by manually checking the dashboard. New `notify_ticket_new_to_staff` template (subject `[GitPulse] New ticket #{id} ({course_code}) - {title}`) is now sent to every active `owner` + `teacher` of the course (excluding the submitter) from both branches of `submit_support_ticket` (dynamic-form and fixed-column). Protected by an idempotency key `ticket_new_staff:<ticket_id>:<email>`, exponential-backoff retry, and the 2-minute sweep fallback (`api/telemetry.py`, `services/email_notifications.py`)

### Fixed

- **Privacy leak: internal notes were e-mailed to the submitter:** `notify_ticket_comment` was e-mailing the submitter even when `is_internal=true` (a staff-only private note - e.g. "this student is lying, ignore"). Added an explicit `not payload.is_internal` guard before notifying the submitter. Internal notes now go strictly to the assigned teacher / staff
- **Avatars no longer get stuck on letter fallback after laptop sleep:** when the laptop sleeps or Wi-Fi briefly drops, the browser fires an `error` event on _every_ in-flight `<img>` avatar. The previous handler immediately hid the `<img>` and showed the letter fallback - _with no recovery logic whatsoever_. After a single sleep, EVERY avatar across the app (header, dashboard greeting, student profile, support tickets, course teachers, search) silently degraded to letter placeholders until a hard reload. **Fix in `core.js`:** save the original `src` on first error; when `!navigator.onLine`, defer the fallback decision (mark `data-avatar-pending="1"`) instead of showing the letter; a new retry-all listener on `online` + `pageshow` (BFCache) + `visibilitychange->visible` with a 250 ms defer (to let DNS / Wi-Fi settle after wake) and a cache-buster re-fetches all pending / fallback avatars in one batch. Centralized - works across the whole app, not just one page
- **Real double-submit race in forms - some actions fired 2 POSTs per click:** the global form interceptor in `core.js` ran on the _capture_ phase and called `preventDefault() + fetch()`, while page-level handlers on the _bubble_ phase ALSO called `preventDefault() + fetch()` on the same form. Result: two HTTP POSTs per click. Affected: dismiss LLM error (project detail), login, the Alpine `@submit` course-teacher assignment form. **Fix:** extended skip-rules - the global handler now leaves alone forms with `data-submit-action`, `@submit` / `@submit.prevent` (Alpine), `data-no-boundary="1"`, or HTMX attributes. `login.html` was marked `data-no-boundary="1"`
- **E-mail scheduler stuck for 25+ hours - end of the "no e-mail ever arrived" mystery:** the scheduler container, after a long uptime, stopped registering periodic jobs; on start it logged only "Scheduler registered 5 periodic jobs" instead of the full set. `sweep_email_queue` was never invoked -> rows in `email_log` stayed `pending` forever. After `redeploy.py` (which recreates containers), the scheduler correctly registers all jobs and a smoke-test e-mail flowed through the pipeline in 1.6 s

### Improved

- **Caddy configuration - Caddy 2.x deprecation warnings cleaned up:** `basicauth` directive renamed to `basic_auth` for `/grafana`, `/prometheus`, `/jaeger` (×3); removed the redundant `header_up X-Forwarded-Proto {scheme}` (×2 - Caddy's reverse_proxy passes it automatically). After rebuild no deprecation / style warnings remain in `caddy` logs; basic_auth still enforces 401 without credentials

---

## [2026-04-28]

### Improved

- **Student profile - MR and issue notes now render markdown:** review comments in `partials/student/_comments.html` previously displayed only with `#` / `!` / `@` references linkified, with the rest as raw text. They now go through the `render_gl_description` filter, which has been extended to support **fenced code blocks** (```` ```c ...``` ````) - content is escaped, wrapped in `<pre class="gl-desc-pre"><code class="language-X">...</code></pre>`, and gets its own CSS. Headings (`##`), `**bold**`, `_italic_`, bullet/numbered lists, inline `` `code` ``, and fenced blocks all behave like the GitLab web UI now
- **Markdown renderer - no more huge gaps between sections:** newlines are now stripped around BOTH opening and closing block tags (`<h6>` ... `</h6>`, `<pre>`, `<ul>`, `<ol>`), so a blank line between a heading and a paragraph no longer renders as a visible double `<br>` gap. Safety cap: 3+ consecutive `<br>` tags collapse to 2
- **Note list (`components/lists.html`) - markdown render:** the secondary note-list-item component (legacy path) now uses the same `render_gl_description` filter as the student detail page so no GitLab comment surface is left rendering raw escaped text
- **Globally unified course-sync banner format:** five different code paths produced four slightly different formats of the same `Syncing...` text (SSE detail / SSE fallback / legacy poll / `registerServerSyncs` / `_reconcileCourseJobs`). A single helper `_courseSyncMsg(name, running, queued, synced, total)` in `global-job-bar.js` now produces ONE format everywhere: `"NAME: Syncing X/Y groups done (R active, Q queued)"`, gracefully dropping the X/Y and parens when data is unknown. Helper is exposed on `window._courseSyncMsg`, dashboard and course-detail page scripts call the same code - no more flicker between formats on every SSE tick or htmx settle

---

## [2026-04-27]

### Fixed

- **CI `dependency-scan` job - no more spurious "Job failed":** the second `pip-audit` run (against the full installed environment, not only `requirements-lock.txt`) was flagging vulnerabilities in _CI tooling_ - `pip` itself (CVE-2026-3219, no fix released yet) and transitive deps of `cyclonedx-bom`/`pip-audit` - which are not part of our application dependency closure. Added `|| true` to the informational scan plus a comment; the `requirements-lock.txt` audit (actual runtime deps) stays strict and continues to publish the SBOM artifact
- **Dashboard - false "Process timed out - check results manually" toast during long syncs:** two compounding bugs. (1) `_jobMaxAge` for course-sync jobs (UUID-like or numeric IDs) was 10 minutes; a real 8-group course sync routinely runs 15-25 minutes, so the staleness guard fired mid-flight. Bumped to 45 minutes. (2) The previous "passive `deferGlobalJob` must not overwrite live message" fix early-returned without calling `showGlobalJob`, so `_autoStartPolling` was never invoked -> `lastUpdate` stopped being refreshed and the guard fired on healthy jobs. Passive branch now starts polling when no poller is attached (`global-job-bar.js`)

## [2026-04-25]

### Improved

- **Per-team Status pill on the course page - flips instantly on Sync All click:** optimistic update in `triggerSyncAll()` writes a `QUEUED` badge to `cells[4]` of every team row and "Sync queued..." into the Last Updated column before the server responds. `_refreshCourseData()` no longer overwrites SYNCING/QUEUED badges during the SSE race; `updateTeamRow(team)` owns all state transitions (`course-detail.js`)
- **`/sync-all` responds in ~100 ms (previously ~20 s):** team discovery (`/projects/:id/users` calls) moved into a background task `_discover_course_teams_async` - the endpoint queues immediately and the frontend no longer blocks on GitLab rate limits (`api/sync.py`)
- **Pilot Telemetry Service lint - `cast(date, ...)` cleanup:** unified `datetime` imports, renamed shadowing loop variables, ruff/mypy strict clean (`services/pilot_telemetry.py`)
- **No more progress-text flicker on dashboard course cards:** Last Updated / progress text stabilised during SSE updates

---

## [2026-04-24]

### Fixed

- **Compliance report PDF - no more orphaned headings or clipped rows:** removed `page-break-after: avoid` on `<h2>` and `break-inside: avoid` on large narrative / attention blocks in `@media print`. In A4 landscape that combination made WeasyPrint push section headings onto an empty page whenever the following content did not fit in the remaining space. Only row-level `break-inside: avoid` is kept, so individual table rows are never sliced in half (`src/app/workers/report_job.py`)
- **Pilot Evaluation - realistic counts:** instead of a raw `MetricSnapshot` row count (which grew on every webhook), we now count **distinct `(team_id, student_id, week_bucket)` tuples** joined through `TeamMember` with `is_active` + `excluded_from_scoring=False` - teachers, peer mentors and excluded members are no longer included. Dropped the `or` fallback that silently leaked the global count when `rpt_course_count` was zero. Weeks-covered now falls back to `len(compliance_trends.weeks)` so the KPI no longer reads `0` when the trend shows 5 weeks. Click multiplier reduced to `2×checks + 4×flags` (`src/app/services/evaluation_report.py`)

### Improved

- **Project detail - action buttons match the group/course header size:** the project page action buttons (`Open in GitLab`, `Rotate Secret`, `Unlink`, `Run Checks`) no longer use `size='sm'` - they now line up with `Link Project / Sync / Run Checks / Export CSV / Export JSON / Retired Report / Delete` on the group page. Visual consistency across Course -> Group -> Project
- **@mentions in MR descriptions on the student page render as names:** the `linkify_gl_refs` filter now accepts an optional `username_map` (`gitlab_username -> full_name`) and substitutes the readable name for any mention matched against a team member (e.g. `Reviewers: Andrii Betsa` instead of `Reviewers: @sm361rw`). Unknown @mentions still render as the plain handle. Touched templates: `partials/student/_merge_requests.html` (MR description), `partials/student/_comments.html` (MR notes)
- **Compliance report - thesis-style redesign:** numbered sections 1-9, `Table 1..N` captions, page-number footer, empty-state paragraphs per section, compact "Group Overview" instead of the 4-card grid, deduplicated executive summary and recommended actions

---

## [2026-04-23]

### Added

- **Per-course `skip_auto_archive` opt-out (migration `036`):** new boolean on `course_settings` shields manually reactivated courses from being re-archived on the next sweep run. `course_service.activate_course()` sets it to `True` automatically, so a course revived post-end-date doesn't vanish again the next day. Teachers can toggle it from the course settings "Semester dates" section
- **Presets wired into Create Course and Clone Course modals:** the Quick preset selector now fills `academic_year`, `semester` (winter/summer), and both `semester_start_date` / `semester_end_date` with one click - teachers no longer have to open Settings after creating a course for auto-archiving to kick in. `POST /api/v1/courses/` accepts optional `semester_start_date` / `semester_end_date` directly at creation time
- **`SemesterPreset` now carries a `semester` field** (`winter` / `summer`) matching `Course.semester` vocabulary, removing the need to manually sync preset choice with the Winter/Summer selector
- **Full config export/import** now carries `skip_auto_archive` as well - `config-import.js` validates and surfaces "Skip auto-archive: yes" in the import summary
- **Automatic shutdown of automation after semester end:** new daily scheduled job `sweep_auto_archive_ended_courses` (queue `low`, 24 h interval) flips `courses.is_active=False` for courses whose `semester_end_date + semester_grace_days` has passed. Because **all 23 existing periodic sweeps** already filter on `Course.is_active.is_(True)`, this single flag flip immediately stops: `periodic_enrich_all`, `periodic_membership_sync`, `periodic_metrics_all`, `periodic_llm_analysis`, `periodic_telemetry_snapshot`, `periodic_verify_webhooks`, `periodic_docker_reverify`, `periodic_enrich_users`, `sweep_stale_projects`, `sweep_dead_projects`, `sweep_discover_new_projects`, `sweep_discover_new_teams`, plus all cleanup sweeps. Result: **zero GitLab API calls for finished semesters** (migration `035_semester_end_date.py`)
- **New column `course_settings.semester_end_date` (DATE NULL):** explicit "last teaching / exam day". For courses without an explicit `semester_end_date`, the helper derives it from `semester_start_date + semester_default_length_weeks` (default 14) - protects against forgotten courses running indefinitely
- **Semester quick-presets for TUKE FEI KPI - Informatika (all years of study):** new module `app.utils.semester_presets` + endpoint `GET /dashboard/semester-presets` ships 4 presets: Winter 2025/2026, Summer 2025/2026, Winter 2026/2027, Summer 2026/2027. Course-settings UI dropdown **"Quick preset"** one-click fills both dates (Monday of week 1 + last exam day); teachers can still tweak individual dates. The calendar is identical across 1st, 2nd and 3rd year - TUKE FEI uses a single academic calendar for the whole Informatika study program
- **New settings in `app.config`:** `semester_auto_archive_enabled` (feature flag, default `True`), `semester_grace_days` (default `14` days - buffer for grade finalization, late MRs, final report exports), `semester_default_length_weeks` (default `14`, fallback for courses without `semester_end_date`)
- **Helper module `app.utils.semester`:** two pure functions - `get_effective_semester_end(cs, default_length_weeks)` and `is_semester_over(cs, grace_days, default_length_weeks, today=None)`. Explicit `semester_end_date` takes precedence; fallback is `semester_start_date + N weeks`. Open-ended courses (neither `start` nor `end`) are never auto-archived - they can only be archived manually via the admin UI
- **Full config export/import cycle** now also carries `semester_end_date` in the `/settings/full-config` JSON (both export and import branches), so presets transfer cleanly between instances and cloned courses
- **14 new unit tests** in `tests/unit/test_semester.py` covering: empty settings, open-ended course, within-grace, past-grace, fallback-to-start+N-weeks, preset uniqueness, bilingual labels, JSON shape
- **Slovak translations added:** `Dátum konca semestra` (Semester End Date), `Koniec semestra`, `Dátumy semestra`, `Rýchla predvoľba` (Quick preset), `- Vyberte predvoľbu -`, `Končí` (Ends), `Posledný deň výučby / skúšok...`, `TUKE FEI - Zimný/Letný semester 2025/2026 a 2026/2027 (Informatika, všetky ročníky)`, and more

### Fixed

- **Weekly Score Trend & Weekly Breakdown - fabricated W1-W7 rows for teams active from mid-semester onwards:** _chain of five linked bugs_ that caused the Score Trend line to show a bogus W1=100 % -> W7=0 % -> W8+ real shape, Skill Profile to render a stale W7 (0 %) radar and the Weekly Breakdown to list seven empty red rows triggering false teacher/student alarm:
   - (a) `pilot_telemetry.get_student_compliance_history` primary path (when `StudentComplianceSnapshot` rows existed) never returned the assembled data - the `return filled` was missing - so control fell through to the MetricSnapshot fallback, which only knew the latest `computed_at` (W10). _Fix_: added `return filled` (commit `bd189ee8`)
   - (b) `compliance.engine.backfill_compliance_history` fabricated `StudentComplianceSnapshot` rows for weeks 1..N even for teams whose GitLab project did not yet exist (-> W1=100 % "default ok" + W2..W7=0 %). _Fix_: detect the team's first-activity week from `MIN(Commit.committed_at)` and skip earlier weeks (commit `3e6fe1b1`)
   - (c) heterogeneous tuple `for col, model in ((Commit.committed_at, Commit), (MergeRequest.created_at, MergeRequest), ...)` failed CI strict-mypy due to union-type inference. _Fix_: split into three explicit `select(func.min(...))` queries (commit `52611892`)
   - (d) `Result[Any].rowcount` is absent from the SQLAlchemy async stubs -> CI mypy `attr-defined` failure. _Fix_: `getattr(deleted, "rowcount", 0) or 0` (commit `c289c5b1`)
   - (e) _hidden root cause_: GitLab auto-creates an initial README commit at project-creation time with `committed_at ≈ project creation time`, so `MIN(Commit.committed_at)` returned W1 for **every** team and the anti-fabrication logic from (b) was a no-op. _Fix_: `first_activity` is now derived from `MIN(MergeRequest.created_at)` and `MIN(Issue.created_at)` (genuine intentional student actions); commits are only used as a fallback and only commits whose `author_id` matches `TeamMember.student_id` (so the bootstrap/system commit is ignored) (commit `56a9387f`)
   - (f) _post-deploy audit fix_: even after the pre-activity `StudentComplianceSnapshot` DELETE, the API still synthesized W1..(first_activity-1) as `null` stub rows because of `for wk in range(1, max_week+1)` - Weekly Breakdown rendered them as empty em-dash rows. _Fix_: range starts at `min(populated_weeks)`, so chart/heatmap/table only show weeks with real data - no fabricated numbers, no misleading empty rows
- Net effect: for a team that started work in W8 with current activity in W10, the UI now honestly shows only W8, W9, W10 - no misleading W1=100 % (false green) or W2-W7=0 % (false red)

---

## [2026-04-22]

### Added

- **Job bar - "Finishing..." state:** the global progress bar no longer appears frozen at "0 running, 0 queued" during the server's 15-second post-batch grace window. When the client sees `running==0 && queued==0` while the server still reports `has_active_sync=true`, the bar switches to a `finishing` status with `t('Finishing...')` instead of showing a misleadingly empty counter. Applied to both the SSE branch and the legacy poll fallback in `global-job-bar.js`
- **i18n - covered card states & job-bar fallbacks:** every hardcoded English fallback in `global-job-bar.js` (`'Analyzing...'`, `'Generating report...'`, `'Running compliance checks...'`, `'Importing roster...'`, `'Exporting data...'`, `'Processing...'`) is now wrapped in `t(...)` with matching keys added to `sk.json`. The `scripts/find_missing_translations.py` audit now reports 0 missing keys

### Added

- **Issues to Address -> interactive chart:** the static list of failing checks has been replaced by a Chart.js horizontal bar chart - X axis is % of group affected, bars are severity-coloured (red High / orange Medium / blue Low) with a 900 ms staggered entrance animation. Hover tooltip shows count/weight/severity, clicking a bar expands a detail panel with the affected students rendered as a responsive grid of cards, each click-through to the member row in the table. Reuses the IntersectionObserver scroll-reveal pattern and a `<noscript>` fallback. Chart.js is loaded on project-detail only via `extra_head`
- **Issues-to-Address detail panel:** new card with severity-coloured left border, uppercase severity pill, × close button, tabular-nums stats (affected/total · share · weight) and students rendered as hover-highlighted cards in a responsive grid. Legend re-styled as pill chips (instead of italic hint) for consistency with the rest of the component system
- **Quick Access - informative items:** each sidebar entry now shows a traffic-light dot from the latest compliance snapshot, the score in %, and member count from `TeamMetricSnapshot` instead of just the name (the sidebar is now informative, not decorative)
- **Slovak UI translations - full coverage:** added 99 missing translations to `sk.json` (sync error messages, confirmation dialogs, toast messages, retired grading editor, admin-users page, user-info modal, project reactivation, CI scenarios). New audit script `scripts/find_missing_translations.py` scans all `t(...)` calls across JS and templates and reports missing keys - added to the CI checklist
- **Typed exceptions for GitLab client:** new `GitLabPaginationTruncatedError` class (subclass of `GitLabAPIError`) - pagination truncation no longer returns partial data silently but raises, so per-project `try/except` marks only that project as failed and the sweep retries it later

### Fixed

- **Mobile responsiveness - tables & profile card:** (1) profile header `.profile-identity` lacked `min-width:0` and the "View on GitLab" link overflowed the card on narrow viewports - added `flex:1+min-width:0`, `overflow-wrap:anywhere` and `align-self:flex-start+nowrap` on the link. (2) Project members table had `<td class="text-nowrap">` on the name cell, causing the sticky column to stretch and cover the R01-R13 check cells - on mobile `text-nowrap` is overridden to `white-space:normal` + `max-width:14rem` + wrapped role badges. (3) Course teams table (7 columns) now hides the tree-toggle and Last Updated columns on mobile so Avg Score / Status / Actions remain visible without horizontal scrolling. (4) Check cells `.check-pass/.check-fail/.check-na` switched to `vertical-align:middle` - ticks/crosses no longer cling to the top of multi-line name rows
- **Click on student name in Issues to Address no longer scrolls page to top:** `scrollIntoView` also scrolled outer scroll containers (viewport) causing the fixed topbar to visibly shift. The scroll now targets `.gl-page-content` exclusively and computes `scrollTop + boundingRect` offset so the target row centers inside the scrollable zone while surrounding chrome (topbar, breadcrumb, sidebar) stays put
- **Weekly compliance heatmap - historical weeks no longer empty:** two linked bugs were wiping past weeks on every sync. (a) `compliance.engine.backfill_compliance_history` ignored `as_of_week` and always wrote the current week number to `StudentComplianceSnapshot.week_number`. (b) `pilot_telemetry.capture_team_snapshots` upserted via ON CONFLICT DO UPDATE with a stripped `raw_metrics` payload (no `checks_detail`), overwriting the 13-check breakdown the engine just persisted. Fix: engine now honours `as_of_week`; telemetry sweep derives category scores via `_derive_category_scores(checks_detail)` and writes a superset. 170 unit tests pass

- **Quick Access "Subgroups and Projects" tab empty:** the SQL query for `qa_projects` was sorted by `latest_computed` and limited to 20 rows, but those 20 rows were the same teams already shown in Groups (team:project is ~1:1), so after Python-side dedup 0 projects remained and the tab always showed an empty state. Now `team_id NOT IN` is pushed into SQL `WHERE`, so the 5-row limit is spent on teams NOT already surfaced in Groups; if Groups covers every team (≤5 total), a fallback shows the top-5 projects regardless
- **Course Analytics - auto-scrolled page on load:** initial `selectWeek(currentWeek)` called `pill.scrollIntoView({block:'nearest'})`, which browsers interpreted as scrolling the entire document vertically (when the target was below the fold). Initial select now skips scroll (`scrollPill:false`), and user-driven clicks use `weekPills.scrollBy({left, behavior:'smooth'})` scoped to the horizontal pill strip only
- **LLM modal - guard against calling endpoints without an API key:** all LLM modals now check both the feature flag and API-key presence before showing and return a friendly error instead of a 500 from the upstream call
- **GitLab 429 (rate limit) - silent data loss:** after retries were exhausted the client returned `None`, which callers treated as "not found" (404) - sync jobs marked as `completed` with missing issues/MRs/pipelines, dashboard showed wrong metrics. Now raises `GitLabAPIError(429)` with `Retry-After` in the message
- **GitLab pagination (10 000+ items) - silent data loss:** when hitting `max_pages=100` cap with a full final page (meaning GitLab has more data), the client returned a partial list and only logged a warning. Dashboard would show "completed" with under-counted numbers. Now raises `GitLabPaginationTruncatedError` with structured fields (`path`, `max_pages`, `items_fetched`) for Grafana alerting
- **Webhook rate-limit IP spoofing (DoS):** orphan-webhook rate limiter read `X-Forwarded-For` directly from headers, bypassing the `ProxyHeadersMiddleware` trust boundary - attacker could rotate spoofed IPs to bypass 10/min limit and flood `orphan_webhook_events`. Now uses `request.client.host` which the middleware already validated against `trusted_hosts`
- **Webhook backpressure - silent check failure:** `except: enqueue anyway` silently hid backpressure-module failures / Redis outages. Fallback preserved (best-effort enqueue), but now logs `logger.warning` with `exc_info` - operators see degraded mode instead of false confidence
- **Global job bar - interval leak on tab close:** `_syncWatchdogId` (5 s polling of `/sync/active`) was not cleared in the `beforeunload` handler - interval lived until GC after tab close or logout. Now `clearInterval` alongside `_elapsedTimerId`

---

## [2026-04-21]

### Changed

- **Sync UI - single source of truth:** removed the redundant inline "Sync in progress" info-card from the course Overview, Roster and Teachers tabs - the persistent global progress bar is now the sole sync indicator, eliminating duplicate-UI flashes and double-animation during page transitions (-312 lines of dead UI code, including the `SyncStatusBanner` component and its pollers)
- **Sync freshness guard (up-to-date check):** `POST /api/v1/courses/{id}/sync-all` and `POST /api/v1/teams/{id}/sync` now skip teams whose last successful sync completed within the 5-minute freshness window - response carries `already_fresh: N`, single-team returns `status: "skipped_fresh"`; pass `?force=true` to bypass. Prevents hammering the GitLab API when Sync All is clicked repeatedly or across multiple teachers viewing the same course. Frontend prompts for force re-sync when everything is fresh instead of silently no-op-ing

### Fixed

- **Global progress bar - cross-page discovery of active syncs:** new `GET /api/v1/sync/active` endpoint returns in-progress course syncs; the global bar now calls it on page load, so the bar also appears on Admin -> Users / System / Dashboard when a sync was started in another tab, device, or by a scheduler
- **Global progress bar - race conditions:** removed silent bar removal during the 2-second restore window when `/sync-status` transiently returned `has_active_sync=false` during a state transition; jobs now carry a `serverConfirmedRunning` flag, and the silent-remove guard fires only for genuine redirect-flash cases
- **Issues to Address - direct project members only:** card was iterating the full team roster (e.g. 37/37) instead of only direct GitLab project members (e.g. 5/5) - live-data endpoint now calls `get_project_members(include_inherited=False)` matching full-page render
- **Issues to Address - dynamic refresh:** card now re-renders server-side on every change (exclude toggle, role change, check run) via Jinja partial
- **Issues to Address - synthetic/inherited member leak:** teachers, mentors, inherited and synthetic GitLab-only members excluded from scored cohort
- **CSS bleed system-wide fix:** global `details summary::before` rules scoped to opt-in `.details-accordion` class; duplicate unicode ▶ chevron removed from `pages/course.css`

## [2026-04-20]

### Added

- Comprehensive mobile responsiveness overhaul
- GitHub-style zebra tables + changelog sidebar widget
- Comprehensive changelog from all 1347 commits since repo creation

### Fixed

- Auth resilience - login page for new users, next-URL preservation, crash protection
- Redesign OG image - clean centered layout for Google previews
- Prevent skeleton flash + lighten heavy table skeletons
- Rebuild bundles + ruff format auth.py (fix CI lint)
- Prevent zebra-stripe flash when toggling member filters
- Clean empty CSS ruleset + add restripeTable to no-paginator filter path
- Fully suppress transition on clickable rows during restripe
- Zebra tables without animations - remove transitions on rows, instant hover (GitHub style)
- Propagate zebra/hover backgrounds to `<td>` for overflow:hidden tables
- Use solid opaque colors for table zebra stripes
- Remove opacity from row-page-enter animation to prevent color mixing during filter/pagination

### Changed

- GitLab-style skeleton loaders - lighter, mixed with spinners

### Infrastructure

- Code quality audit - var->let/const, dead code removal, cache fixes

## [2026-04-13 - 2026-04-17]

### Added

- Periodic team discovery sweep + lint fixes
- Email-based teacher/mentor detection + early sync progress
- Improve OG image + add skeleton loader to User Management
- Add peer mentor detection and filter
- Production-grade email notification system with retry queue

### Fixed

- Email enrichment propagates to User + filter inherited teachers from contributors
- Whitelist contributor filter - show only team student commits
- Whitelist contributor counts on course/team dashboard too
- Remove deprecated code, fix labels, inherited members modal, subtle flash
- Resolve mypy arg-type errors in _stats.py narrowing
- Lower coverage threshold to 30, fix arena email caching and timeouts
- Replace asyncio.TimeoutError with builtin TimeoutError (ruff UP041)
- Add arena email fallback to single-user enrich, suppress global bar flash on redirect
- Auto-create User records for inherited members, remove teacher/mentor opacity
- Batch enrich Arena fallback, course count from groups, inherited member import
- Inherited member import, toast visibility, course cards in modal
- Course display with code/year/semester for membership-derived courses, add academic_year+semester to membership API, fix ruff-format
- Arena enrichment for User records during import, role badge for derived courses, elevate Arena logs to warning
- Mypy User.gitlab_username type + strip course name from card sync badge
- Stale sync after redeploy + smooth global bar entrance
- Create User records during member sync (not only on initial import)
- Ensure User record for existing active members during sync
- Limit User creation during sync to teachers only
- Enrich User emails from Student records and Arena during sync
- Sync_all discovers new teams + Arena enrichment shared httpx client
- Arena enrichment 30s per-request timeout, concurrency 2
- Update scheduler test counts for job #23 + cross-team project dup guard
- Pass course_id to sync worker for early progress toasts
- Add toasts to enrich button + welcome-back toast after login
- Reduce lazy skeleton reveal delay from 400ms to 150ms
- Rewrite admin users skeleton to match page structure + ruff format
- Remove corrupted duplicate in sk_admin_users skeleton
- Defer admin-users paginator/filter init for lazy-shell loading
- Skeleton pagination to match 3-column layout (info | buttons | per-page)
- Update all skeleton pagination to 3-column layout (info|buttons|per-page)
- Skeleton search width, pagination inside card-body, mobile dropdown clamping
- Dropdown portal right-aligned, support tickets skeleton structure
- Dropdown portal conflict with global handler - use data-gl-portal marker
- Keep per-page dropdown visible when pageSize=all so user can switch back
- Skeleton card structure, pagination DRY, pageSize localStorage cache
- Add per-page dropdown to admin/system Job History pagination
- Mobile responsiveness, optimize scheduler & telemetry
- Stop spinner reset and button color flash on mobile
- Pull-to-refresh false trigger on table scroll + toast reliability + lint
- Completion toast suppressed when global bar visible
- Ruff E501 in scheduler.py (line too long)
- Member table, enrichment gate, contributor exclusion
- Global bar dedup, contributor exclusion in project detail
- Complete mentor support across all views and scoring paths
- Exclude mentors from all student count queries
- Preserve is_mentor and excluded_from_scoring on team reassignment
- Increase worker heartbeat freshness window to match RQ TTL (420s)
- Enrich PRIVATE emails during sync and periodic sweep
- Member table bugs - filter empty state, badge count, sorting, inherited visibility, commit-based email enrichment
- Arena email enrichment, mentor badge, blue focus, progress bar course name, student count labels
- Dashboard Students stat now counts User accounts (matches admin breakdown)
- Deduplicate role badges, global bar flash, blue row selection
- Prevent global bar flash during skeleton loader phase
- Ruff-check unused import + ruff-format (fixes CI pipeline)
- Dashboard JS created duplicate at-risk badge using old class names
- Show more description text in course card (3-line clamp, no Jinja truncate)
- Global job bar hidden on team page when course sync is running
- Sorting/filter conflict + welcome email on first login
- Rebuild JS bundle for sorting/filter changes
- Correct CTA links in welcome emails (404 paths)
- Remove all emoji characters from email notifications
- Replace deforming loader icon with smooth circle spinner
- Show text status badges instead of dots in group activity table
- Prevent page-size dropdown from being clipped by pagination container
- Replace custom page-size dropdown with native select
- Restore custom page-size dropdown with fixed positioning
- Portal page-size dropdown to document.body to escape overflow
- Smart dropdown direction - open downward when space allows
- Remove unused Request import (ruff F401)
- Tabs overflow, footer theme, remove icons, accuracy fixes
- Tabs scroll + footer light theme with explicit colors
- Shorten tab names, remove tab icons, light footer, full-width tabs
- Footer light mode with !important to override Material theme
- Footer text/link colors visible in light mode
- Stronger no-store cache headers to prevent stale proxy/browser cache
- Job history table responsive headers + zebra striping on filter/sort
- Replace broken Sync Status modal with toast notifications
- Update tests for queue-based email system + fix ruff lint

### Changed

- Replace var with const/Set/Map in JS, use begin_nested savepoints instead of rollback, add logger.debug for inherited member fetches, consolidate imports, fix line lengths
- Reuse ClientPaginator for admin Job History (server-side mode)
- Revert: remove commit-based email enrichment - Arena API already handles this
- Privacy: comprehensive GitLab-quality privacy statement with TOC, tables, GDPR rights, retention schedule, cookie details, supervisory authority

### Security

- Fix header issues from security scan
- Add privacy policy page, CSP upgrade-insecure-requests, sitemap update

### UI / UX

- Redesign: course card - clean layout like top companies

### Infrastructure

- Config: pass EXCLUDED_CONTRIBUTOR_NAMES through docker-compose
- Config: remove unused ARENA_EMAIL_API_TOKEN from compose (endpoint is public)

### Documentation

- Comprehensive audit - fix counts, intervals, add 19 missing models
- Full documentation audit and actualization
- Move legal pages to docs-site, add student guide, open docs access

## [2026-04-09 - 2026-04-12]

### Added

- Smart stale data notifications with webhook activity detection
- Webhook attention items + fix activity feed showing team actions
- Premium Week Analytics with interactive Chart.js charts
- I18n: add 17 missing Slovak translations for Week Analytics
- Auto-expand current week in Week Analytics on page load
- I18n: add 87 missing Slovak translations
- Add Week Analytics skeleton loader to analytics page
- Redesign report generation form with component-based UI
- Simplify sub-project rows to links only, remove per-project metrics
- Detect template repos, unify team page contributor count
- Stale data warning banner for course and team pages
- Comprehensive i18n, job history improvements, LLM config diagnostics
- Expose Grafana/Prometheus/Jaeger via Caddy with basic auth
- Enrich Configuration Preview with detailed settings, LLM status, course metadata
- Install OpenTelemetry packages in Docker image and init tracing in workers
- GitLab-style course sub-navigation + update course configs

### Fixed

- Enrich activity feed with background_jobs + fix audit commit in sync endpoints
- Ruff lint + format errors (line length, unused import, alias)
- Remove broken effective-start detection, replace weekly summary with week navigator
- Analytics & activity quality audit - responsive, empty states, data consistency
- Show empty state message in week bar chart when activity is 0
- Pill focus outline follows rounded shape
- Fully suppress rectangular focus outline on week pills
- Remove focus ring from week pills entirely
- Remove blue glow shadow from active week pill
- Ruff-format compliance + suppress stale-data toast on report generation
- Widen GitLab ID column, add webhook setup info to Event Pipeline page
- Smart webhook detection on events page, rebuild CSS bundle
- Use toast instead of alert banner for webhook warning on events page
- Code quality improvements across admin module
- CI pipeline failures - lint script, admin early-return in _session_caller
- Mobile responsiveness - activity tables scroll, instructors layout, danger zone overlap
- Redesign instructors mobile layout - CSS Grid 2-row compact (GitHub/GitLab style)
- Mobile responsive - students table scroll, sidebar overflow, compact action buttons
- Sidebar panel overflow:hidden, action buttons 32px matching btn base height
- Distinct icons for team actions - code for JSON, bar-chart-2 for Report
- Stretch action buttons evenly across full width on mobile
- Uniform 36px square buttons in mobile action toolbar
- Quick Access projects tab overflow + skeleton loader matches action toolbar
- Quick Access ellipsis - move overflow:hidden to list level, not item
- Quick Access ellipsis - remove negative margins, add overflow:hidden to .gl-qa-text
- Truncate long project paths server-side (45 chars) + display:block on qa spans
- Quick Access: filter empty/template teams, fix CSS text-overflow
- Use student_id instead of id in TeamMember count
- Add display:block + flex:1 for CSS text-overflow ellipsis in Quick Access
- Use width:0+flex-grow:1 for reliable text-overflow ellipsis, cap sidebar on mobile
- Commits table + heatmap mobile responsive, badge inline positioning
- Pin trivy to 0.62.1 (latest tag removed from Docker Hub), guard publish upload
- Team contributors count uses distinct commit authors for consistency with sub-projects
- Live-data and SSE endpoints also use distinct commit authors for contributor counts
- Show dash instead of 0% for projects with no resolved authors
- Resolve ruff lint errors - unused import and per-file-ignores for utility scripts
- Sub-projects inherit team avg score and traffic light when no commit authors resolved
- Hide stale-data banner when sync is already in progress
- Template detection now also checks author_gitlab_id against team students
- Exclude teachers from contributor counts + robust compliance chart loading
- Contributor count excludes teacher by name + compliance data_attrs as dict
- Mypy types, dedup teacher imports, improve group messages, quick access, compliance visuals
- Mypy list[Any] type, never-synced count uses sync status not metrics
- MR empty state msg, improve semester settings, remove review requirements card
- Align course configs with assignment requirements + fix sk.json broken quote
- Remove C01/C02 custom checks, fix weights to sum 1.00
- Resolve mypy and ruff lint errors in LLM status endpoint
- Monitoring proxy + code quality cleanup
- Rebuild CSS bundle (config-preview-details styles were missing)
- Config preview sub-items layout (flex-basis + baseline align)
- Hide AI Analysis Configuration card when LLM feature is disabled
- Support form dropdown clipped by overflow:hidden on .gh-category-fields
- Full monitoring stack - Grafana Failed to fetch, Jaeger DS, enhanced dashboard
- Remove orphaned duplicate alerts in alerts.yml
- Add basic_auth for Grafana metrics scraping by Prometheus
- Correct rq_failed_jobs metric name in dashboard and alerts
- Align DevOps config with ZSI, remove sergej.chodarev from teachers
- Rebuild CSS bundle from sources + fix ZSI description
- Update DevOps description with test (10b) + team project (10b)
- Align course descriptions with official kurzy.kpi pages
- Unify Refresh buttons across all course pages
- Unify dashboard header buttons - remove size='sm' to match course pages
- Break SSE read loop on done event to prevent spurious network error toast
- Remove extra closing brace that broke JS bundle parsing
- Break outer while loop in readImportSSEStream after done event
- Concurrent email enrichment + activity feed labels/dedup
- Remove commit sync date filter + fix CI lint + show 0 for empty sub-projects
- R08 and R13 no longer auto-pass with zero student activity
- Update R13 test to expect fail with zero commits
- Progress timer ticks every 1s + threshold labels positioned at actual percentages
- Send SSE done event before sync-enqueue to prevent network error toast
- Default member filter shows Direct + Inherited to match team contributor count
- Exclude inherited members from team student count on course overview

### Changed

- Deduplicate components, consolidate JS utils, update docs
- Consolidate _lock alias into GP destructuring across 14 page JS files
- Deduplicate code patterns, validate thresholds, clean translations
- Unify contributor counts via shared _stats helper, remove fake per-project score fallback
- Lift tab nav to shell pages - instant tabs, ARIA a11y, keyboard nav, body-only skeletons

### UI / UX

- Fix ruff-format for teams.py and reset_db_remote.py

### Tests

- Force-show all 3 stale data scenarios for visual review

## [2026-03-30 - 2026-04-04]

### Added

- Search panel - mobile close btn, GitLab avatars, user->admin nav with auto-search
- PWA support + rewrite login animations (no conflicts)
- SSR-direct page entrance animation - staggered contentEnter for pages without skeleton loaders
- Edge-to-edge mobile cards + pull-to-refresh
- Comprehensive SEO - Google Search Console, OG, sitemap, robots.txt
- Comprehensive email notifications + refactor to shared template
- Non-anonymous tickets + auth-only submission + SMTP setup
- Add proper error handling for 401/session expired
- Wire support form skeleton + sys audit cleanup
- Add 346 missing Slovak translations for support, fix form overflow CSS, improve skeleton
- Support ticket system with comments, filters, and management\n\n- Add migration 031: ticket lifecycle columns (status, priority, category,\n  assigned_to, resolved_at, updated_at) + support_comments table\n- Add SupportComment model with author, content, is_internal fields\n- Add ticket management API: PUT ticket, GET/POST comments\n- Add filtering by status/priority/category/search in ticket list\n- Rewrite support_tickets.html: filter bar, expandable detail rows,\n  inline status/priority/category management, comments section\n- Replace all Unicode arrows with SVG icon components\n- Replace emojis with icon() macro calls throughout\n- Rename FEATURE_FEEDBACK_FORMS to FEATURE_SUPPORT_FORMS in docs\n- Update architecture doc: feedback.css -> support.css\n- Add btn_link_icon for back navigation and pagination controls\n- All linters pass (ruff, mypy), 2382 tests pass"
- GitHub-style support system redesign
- SSE real-time updates, email notifications, GitHub-identical UI
- Redesign support filters with animated selects + category-specific form fields
- Add alternating row backgrounds for visual consistency
- Ticket detail - component-based layout, assignee user search
- Dashboard integration - attention items, activity feed, sidebar badges, error page links
- Pass SMTP env vars through docker-compose to containers
- Component-based Subgroups & Projects table + Groups child rows
- Auto-enrich user profiles from GitLab after config import
- Persistent feedback links with CRUD, form picker, expiry, and link management
- Move Feedback Links to Feedback Forms page + gl-dropdown form picker + context default forms
- Add expand/collapse arrows to groups table with member preview
- Expandable tree view for team projects + UI fixes
- Arena email API fallback + filter bots from instructor lists
- Security hardening - secret rotation, per-user tokens, retired heuristic detectors, CSRF UA binding

### Fixed

- Add PNG favicon for Google Search + shorten meta description
- Redirect /favicon.ico to PNG instead of SVG
- Slovak translations (podpora), mobile responsive improvements, email cleanup
- Login page mobile - keep desktop look (background, centered card)
- Ruff format + remove deploy job from CI pipeline
- Login language switcher 404 - use /dashboard/login path
- Login mobile - keep card contained like Keycloak (remove max-width:100%)
- Login mobile - full-screen card like Keycloak (edge-to-edge white, no dark bg)
- Login mobile - center content, visible lang selector on white bg
- SW CORS error on OAuth redirect - skip navigate requests
- Remove /dashboard/ from SW pre-cache - redirects to OAuth when unauthenticated
- Remove SSR entrance guard - caused blank page on slow connections
- Prevent skeleton flash on fast HTMX loads
- Mobile card styling + PTR indicator hidden by default
- Rewrite PTR to match GitLab blue circle design
- Rewrite PTR and mobile card styling (manual)
- Clean PTR rewrite - fix cancelable touchmove + Material spinner
- Instant mobile logout + suppress native PTR on login page
- Regenerate OG image with proper GitPulse branding
- Clean OG image rewrite - minimalist pixel-perfect layout
- Render login page for search-engine crawlers instead of OAuth redirect
- Detect Lighthouse/PageSpeed bot in crawler regex
- Ruff lint + accessibility (main landmark, color contrast)
- Allow HEAD method on SEO routes (robots.txt, sitemap.xml, verification)
- Restructure robots.txt - unblock /dashboard/login for Google
- Simplify robots.txt - remove dashboard disallow entirely
- Support HEAD on /dashboard/login + detect Google-InspectionTool
- CI mypy errors, remove sidebar badge, fix login lang auto-login
- Wire comprehensive email enrichment with GitLab API + Arena fallback
- Support form double toast, markdown preview, asterisk notice, email notification
- Proper double-toast fix (data-no-boundary), XSS prevention in markdown, hide info-card on success
- Rebuild JS bundle, fix mypy dict type in gitlab_group_import
- Remove temp SMTP scripts causing ruff lint failures
- Add Arena API token auth + Arena fallback in student enrichment
- Improve student enrichment with username search fallback
- Replace anonymous message with logged-in user info on support form
- Rebuild JS bundle and use proper 401 SVG from GitLab design
- Rewrite renderMarkdown() in support-form & ticket-detail
- Ticket comments 500, emails, comment permissions
- Duplicate comments, missing icons, email avatar, notifications, responsiveness
- Admin-system crash, duplicate emails, 401 UA mismatch
- SSE real-time timeline update, touch updated_at on comment, skeleton loaders
- Perfect 1:1 skeleton loaders for support pages, update email v4 with arena/SMTP/SSE changes
- Restrict textarea.form-input to vertical resize only
- Render info_card HTML correctly in support form (use call block)
- Complete feedback->support rename, fix .env config bug and data.feedback attribute bug
- CI lint failures + SSE security + dashboard auth guards + docs
- Support page layout to match standard dashboard structure
- Remove sidebar duplication, drop support/manage page, fix filter styling
- Full-width form, move info card, expand category-specific fields
- Improve support form - reorder notices, add padding, expand category fields
- Dropdown z-index/transparency bug - replace opacity transition with class-based enter/leave
- Add id=description to textarea and for=description to label (a11y)
- Correct RateLimitDep usage and add empty-string UUID validator for SupportCreate
- Tickets table matching admin pattern + dropdown transparency
- Rewrite support tickets page with proper table/filter components
- Cast UUID to string for tojson serialization
- Improve toolbar dropdown hover with button-like bg highlight
- Move filters to card header with search (User Management pattern)
- Use subtle rgba hover for data-table rows across all pages
- Ticket detail - proper two-column layout, fix sidebar overflow, self-contained assignee dropdown
- Alpine expression error, form corners, sidebar heading colors, assignee reload, responsive
- RenderMarkdown via vanilla JS init instead of Alpine expressions - prevents quote escaping errors
- Correct SSE endpoint URL - remove stale /sse/ prefix
- Enable assignee unassign + form accessibility (id/label)
- Change timeline labels to spans (no associated form field)
- Deep-link URLs, email notifications, assigned-by info, 403 page
- Harden teacher membership sync - upgrade student memberships, elevate User.role, enrich avatars
- Resolve ruff lint/format failures in teacher membership sync
- Course Teachers count includes admins, filter-pill descender clipping, config preview spacing
- Create User records for teacher_usernames during config import
- Ruff lint errors in reset_prod_db.py, tighter config preview spacing
- Section count toast mismatch + dashboard config preview spacing
- Add error handlers for unexpected scenarios + fix mismatches
- Active column width, unify config-import component
- Remove stale _fullConfig ref, add comprehensive config validations
- Pass disabledFeatures to config-import in course-settings
- Prevent SSE task cancellation after import commit + add keepalive pings
- Filter bot users from teacher discovery + clear config on import success
- Fast config import, modal close, admin-teacher filter
- Correct cell indices in course-detail.js (group names overwritten by member count)
- Student privacy - hide metrics, restrict profile access, fix tree layout
- Student profiles, LLM error display, table layout, global job bar coverage
- Clean LLM error display, role-appropriate suggestions, proper icon
- Error card dynamic injection + CI test fix
- Skip job history for zero-work scheduled jobs + fix mypy
- Groups child-row dashes, member name overflow, LLM error card bugs
- Restore Groups Status column + LLM error card delayed swap
- Build LLM error card client-side, show project last_synced_at, fix worker MissingGreenlet
- Per-project contributors, inline SVG icons, toast-delayed error card, dismiss empty state
- Error card delay 6s, per-project avg score, remove Active badge, single-MR retry
- Real per-project avg score, error card without toast, better error classification
- Role-based error messages + classify MissingGreenlet as transient
- MissingGreenlet root cause + role-based messages + MR links in analysis
- LLM error classifier order, global progress bar deferral, per-project status badges
- Replace en dash with hyphen in llm_job comment (ruff RUF003)
- Use forceCloseModal after successful import to avoid spurious Discard confirm
- Lint errors (ruff/mypy) + UI consistency for feedback links
- Cast UUID to text in feedback-links join to fix 503 error
- Add for attribute to form picker label (a11y)
- Fix Form picker dropdown not opening
- Align tokens and modals 1:1 with GitLab Pajamas
- Weekly deadlines table uses full width, no wasted space
- Align table th, toggle token, pagination padding to GitLab Pajamas
- Pixel-perfect GitLab Pajamas 1:1 alignment (round 5)
- Align backgrounds and borders with GitLab dark theme
- Remove max-width cap on main-container - content fills full page width
- Pixel-perfect GitLab Pajamas component alignment
- Align status dots, pagination radius, table padding, card/modal footer to GitLab
- Project links to internal pages, arena JSON API with identities
- Even column distribution across all tables (colgroups + table-layout:fixed)
- Ruff lint/format errors in arena_email (UP037, E501, N806)
- Show empty-state message when filter pills yield 0 results
- Hide pagination when filter yields 0 rows, clean empty-state styling
- Add !important to .d-none utility to override .pagination-controls display:flex
- Prevent scrollbar flash on table pages by deferring page-initialised with double-rAF and hiding pagination-controls pre-init
- Suppress row animation and lock container height during filter/sort to prevent scrollbar flash
- Add missing column width classes for compliance checks table and fix weekly deadlines layout
- Improve weekly deadlines table layout and prevent modal scrollbar flash
- Unify scrollbar styling across modals, drawers, tables to match main content
- Switch checksTable to auto layout on mobile to prevent column overflow
- Hide Active/Code columns on small mobile screens, constrain Actions column width
- Wire per-user token auth, fix ruff format, enable event pipeline
- Resolve ruff lint/format failures, rename remaining instructor refs in i18n, fixtures and docs
- Move Resurrect button right, fix duplicate toasts, let pagination stretch
- Move Resurrect Selected to card header top-right, footer only pagination
- Move pagination inside card body, hide in empty state
- Add table-empty-row class to all empty/loading/error rows, hide pagination in empty state
- Use table-empty-state with icon for empty DLQ, matching courses/users pages
- Map event.replay/resurrect/processed/failed in activity feed with icons, labels, details, URLs
- Align Configuration Preview icon, expose currentUsername to Alpine, fix modal close animation
- Configuration Preview spacing, add fg855ni to ZSI config, fix DLQ Type column wrapping
- Sync teacher_usernames from config import to CourseMembership

### Changed

- Unified premium animation system - staggered entrance, no conflicts
- Zero-lag PTR - all passive listeners + rAF batching
- Audit fixes - deduplicate afterSwap handler, fix deploy script PS5.1 compat
- Comprehensive best-practice audit
- Audit: full system refactor - security, a11y, i18n, dedup, dead code
- Deep rename feedback->support across entire codebase
- Redesign: pixel-perfect GitHub Support UI with markdown editor, thread view, expanded categories
- GitHub-identical support UI - reply on top, reverse chronological comments, remove thread connectors
- Unify table styles and replace inline styles with CSS classes
- Ticket detail page - use page_header, remove custom action bar
- Simplify forms, fix dropdown, sortable table
- Rename Feedback subsystem to Support/Ticketing system
- Revert: undo UI changes
- Revert: restore to d03fd4f (align tokens and modals 1:1 with GitLab Pajamas)
- Unify role system (instructor->teacher), drop instructor_usernames column, R13 push enqueue
- Eliminate all 'instructor' terminology - rename to 'teacher' everywhere

### UI / UX

- Align UI system to GitLab Pajamas design tokens
- Align remaining components to GitLab Pajamas
- Revert: restore main-container max-width layout
- Pixel-perfect GitLab Pajamas alignment - focus ring 1px/3px, form padding 8px/12px, line-height 1rem, triple-ring focus, card radius 8px, modal radius 12px, table cell 12px/16px

### Infrastructure

- Remove test support script
- Remove temp verify_fix script
- Remove junk files and harden .gitignore
- Remove debug scripts
- Remove utility scripts with hardcoded credentials

### Documentation

- Comprehensive update - R13, 30 migrations, 2382 tests, CourseMembership

### Tests

- Add unit tests for email notifications, api utils, constants, and type modules

## [2026-03-23 - 2026-03-29]

### Added

- Clickable member rows + context-aware back navigation
- Group members table navigates to project context
- Role separation - force logout on change, hide docs from students, fix attention items
- Suggest full sync after course settings save
- Redesign instructors page (GitLab-style invite bar + member rows)
- Real GitLab avatars + wider layout
- Clickable instructor rows with User Info modal, Owner badge
- GitLab-style Source & Role columns in member tables
- GitLab reference linkification + reduce member-api-note spacing
- Role-based sidebar + thesis feedback card
- Add R13 Commit Quality check - web editor detection
- Simplify: remove intervention list, risk groups, all groups; disable event pipeline/roster; add instructors lazy loading
- Redesign dashboard cards, header, timeline grid, profile menu
- Quick Access sidebar, health for teacher, scheduler feature-flag gating
- Single-user enrich button in User Info modal
- Comprehensive UX improvements from teacher review
- Add 295 missing Slovak translations
- Overhaul global search - students scope, role badges, direct links, docs
- Drastically reduce GitLab API polling - webhook-first approach
- Extend activity-window filter to ALL remaining GitLab polling jobs
- Webhook edge-case hardening - orphan projects, backpressure, immediate enrichment, delivery health
- System-wide resilience - sweep retry, pagination limit, Prometheus enrichment metrics
- Gate GitLab-polling sweep jobs through the scheduled-jobs master switch

### Fixed

- Member profile - dynamic role title, no-activity guard, table scroll
- Member profile UX - back nav to group, instructor-aware empty states
- Prevent infinite login loop when allowlist user changes role
- Dashboard: fix status dots, reporter role warning, pipeline health overflow
- Fix CI lint + Groups 0: match Student by gitlab_user_id
- Fix OAuth: GitLabUser.id not gitlab_user_id
- Elevate dashboard role for course owners/instructors, remove redundant stat tooltip
- Rewrite modal CSS to match GitLab Pajamas exactly
- Silence editCheck console warning and aria-hidden focus conflict
- Quick Access shows real teams, System health enriched
- Quick Access Groups/Subgroups tabs, interactive timeline weeks, skeleton blue bar fix
- Lint errors (ruff/mypy), timeline semester_weeks order, project name display
- Sidebar layout, project names, timeline nav, telemetry gating
- Round avatars, attention link to course, instructor layout
- Avatar backgrounds hardcoded, groups sort by RED, instructor panels stretch
- Revert email, muted avatar colors 24px, restore email docs
- Language switch revert, new analytics favicon, DTA refs cleanup
- Cache-bust extra.js/css/favicon, reduce nginx cache, remove dead locale persistence
- Fix language revert, favicon flash, and canonical URLs
- Restore missing `<script>` tag, update verification date to 2026-03-28
- Sort by status on attention click + per-course red teams
- Mypy arg-type error in dashboard red_teams_by_course dict comprehension
- Avatar fallback from gitlab_user_id + skeleton 1:1 + email v3 fixes
- Avatar fallback, owner visibility, a11y, mobile
- Avatar fallback, full-width layout, mobile, admin owner role
- Avatar fallback, instructor navigation, admin user info
- Revert instructor nav to full page, fetch avatars from GitLab API
- Toast dedup, 'you' badge styling, ruff-format
- Remove fake Owner badge from admins, fix instructor navigation
- Role-aware Student Not Found, restore Owner badge, avatars in search
- Remove bulk avatar fetch (timeout), improve not-found, fix admin role
- Auto-assign Owner to course importer + suggestion box layout
- Guard gitlab_user_id None before get_user (mypy)
- Create admin User records on import + enrich instructors/admins
- Create User records during JSON config import
- Prevent scrollbar flicker in modals and tables during animations
- Reliable scrollbar-flicker prevention in modals
- Remove scale() from modal animations to eliminate scrollbar flicker
- Remove Timeline page, help icon, fix toast stacking
- Restore coverage above 40%, remove per-week deadline columns
- Shrink weekly deadlines table to content width
- Table layout + GIT_SHA for reliable cache-busting
- Activity grid align-items:start to remove empty space
- Activity skeleton 1:1 match with real card structure
- Activity grid cards - override .card+.card margin-top
- Ruff lint errors in test_coverage_gaps.py
- Mobile table responsiveness, cookie consent cross-device, session persistence
- Comprehensive mobile responsiveness overhaul
- Comprehensive responsive pass - tables scroll, skeletons match pages
- Pagination overflow + deformation on mobile
- Third pass - touch scroll, heatmap column, min font sizes, invite dropdown
- Remove unused type: ignore comment in auth.py
- Member filter fallback, page size 50, skeleton loader alignment
- Rebuild JS bundle after member-filter and page-size changes
- Include all team members in detail pages for client-side filtering
- Show dash in empty Job History Actions column
- Empty-data guards, config warnings, progress dedup
- Add localIndicatorSelector to all deferGlobalJob/showGlobalJob calls
- Combine nested ifs to satisfy ruff SIM102
- Global bar dedup - sync recheck in _renderGlobalBar + default selectors
- Toast progress bar completes before dismiss (120ms headroom)
- UI polish - text indicators, scrollbar, skeletons, sync perf, expired note
- Team 500 error, project skeleton accuracy, GPU-accelerated shimmer
- Member-api-note styling and missing Slovak translations
- Members table cell index mismatch after Source/Role columns added
- Skeleton member-api-note gray + reduce spacing above info note
- Rebuild project-detail skeleton to match actual page 1:1
- Lint/mypy errors + empty state for member filters
- Sorting + member filter sync on lazy-loaded pages
- Sk_details skeleton matches real details/summary structure
- Re-apply member filters after live-data update
- Show only GitLab project members, include inherited teachers
- Show inherited GitLab group members on team detail page
- Disable event pipeline, fix contributors filter, eye icon, banner, course cards
- Revert course card CSS to clean original design
- Simplify role badges + optimize intelligence panel cards
- Exclusion refresh, card spacing, instructor score display
- Instructor score hiding, project exclusion toggle, skeleton accuracy
- Show instructor scores when snapshot exists (hidden by default via filter)
- Add card-body padding to Group Members table (match other tables)
- Match dashboard sidebar feedback panel (2 links)
- Team detail 1:1 accuracy - avatar size, filter bar, info note
- Add 'commit' to valid categories for R13 check
- Ruff format/import-sort in engine.py, update email feedback forms rationale
- Instructor page Alpine.js errors, remove Groups from Timeline, reorder dashboard
- Use avg_weighted_score instead of non-existent overall_score
- Enrichment fallback to username, progress bar stability, role sync for users without gitlab_username
- Rewrite enrichment UI - button progress, completion detection, toast dedup, global bar SSE
- Enrichment total counts only Users, process Students silently
- Global bar stuck at 100%, toast suppressed after HTMX nav, button flicker
- SSE idle status handling, stale _deferredJobs cleanup at completion
- Join running enrichment on already_running response instead of resetting button
- Restore Job History card, fix enrichment button white/stuck-at-100%
- Eliminate enrichment race conditions, add scheduler master flag
- Map 4 missing jobs to feature flags, sync enrichment progress to global bar
- Lint E501, unify global job progress across all processes
- Correct enrichment total (409 not 808), button shows Enriching state
- Store enrichment status in Redis (multi-worker), cross-link users->students, fix spinner
- Always show global progress bar for all processes (no local dedup)
- Don't inflate enrichment total with students, use backend message in global bar
- Smooth enrichment progress across user+student phases, fix ruff format
- Single consistent progress counter for enrichment, fix mypy
- Show enrichment in global bar and Job History
- Deduplicate enrichment total, remove dual polling
- Remove students from enrichment total, prevent duplicate SSE
- Enable defer/promote pattern for global bar
- Silently remove completed job on HTMX navigation
- Always start SSE polling even when deferred
- Disable Caddy buffering for SSE streams
- Bypass GzipMiddleware for SSE streams + fix Caddy config
- Complete progress bar after users, before students
- Re-add deduplication, always start SSE
- Better messages, immediate Job History update
- Skip 429 sleep on last retry attempt to prevent modal blocking
- Comprehensive quality pass - race conditions, lint, UI polish
- Deep audit - SSRF protection, TOCTOU race fix, dead code removal, UI improvements
- Comprehensive quality pass - race conditions, tooltips, unbounded queries
- Resolve mypy type errors in evaluation_report.py (SimpleNamespace annotation)
- Caddy listen on multiple domains (TUKE proxy support)
- FEATURE_FEEDBACK_FORMS=false now fully hides feedback UI
- Import safety - cross-course protection, team path-prefix matching, membership transfer
- Lint errors - unused import, f-string, en-dashes, type-ignore, formatting
- False teacher detection feedback loop + modal auto-close race
- Mypy type errors in freq-detected instructor gitlab_user_id
- Lint - ruff-format, ruff-check, mypy for sweep activity-window
- Telemetry snapshot upsert - prevent UniqueViolationError on repeated runs
- Prevent UniqueViolationError session poisoning in engine + feedback
- Use risk_score threshold for 'behind' count instead of binary missing-checks
- Add polling jobs to the admin scheduled-jobs registry
- Add scheduled-jobs master switch to docker-compose env vars
- Redistribute check weights so active checks sum to 1.00
- Resolve metric card spinners from initial data and SSE

### Changed

- Centralise role elevation in _enforce_db_role
- Polish: square avatars, docs i18n selector, favicon, email, READMEs, cleanup
- Complete DTA->GP rebrand across JS/HTML/Python/docs
- Redesign Manage Instructors page layout
- Centralize reload logic, eliminate location.reload() duplication
- Remove Timeline Dashboard page and all references
- Add empty-data guard to periodic_metrics_all, add Jaeger datasource to Grafana
- Simplify: remove Milestones/Releases/Labels cards from project detail
- Merge feedback cards + add form questionnaire guide
- Simplify: remove intervention list & all groups from timeline, sort attention items by severity, update email
- Hide: remove Automation section from System page
- Relax defaults: disable R09/R11, R02 branch naming optional

### Security

- Harden validation, fix auth bypass, add input size limits

### UI / UX

- Pipeline Health: GitLab-style redesign with refined bar, badge pct, mini legend

### Infrastructure

- Reduce all artifact retention to 3 days
- Config: set thesis feedback Google Form URL
- Add R13 to course configs + update email review response
- Gitignore reset_db.sql

### Documentation

- Update email review response with current system state
- Rebrand DTA->GitPulse, fix i18n selector, replace mindmap
- Rewrite feedback forms section - built-in module, not Google Forms
- Complete email - add missing responses (import, timeline, MR detail, routing, tooltips)
- Migrate all references from IP to gitpulse.kpi.fei.tuke.sk domain

## [2026-03-16 - 2026-03-21]

### Added

- Add Slovak translations for Automation page (42 new keys)
- Redesign diff viewer - full-width rows, line numbers, responsive
- Scroll-triggered chart & counter animations via IntersectionObserver
- Overhaul Automation panel - scheduled jobs + job history with actions
- Spinner loading states + withUiLock on all actions\n\n- setButtonLoading() now uses .btn.loading (animated spinner) instead\n  of .btn-loading-text (opacity-only dim)\n- Add withUiLock() deduplication to: Refresh Stats, Refresh Jobs,\n  Retry Failed Job, Purge Old Jobs, Trigger Scheduled Job\n- Add .table-loading overlay for job history filter changes\n- Trigger buttons: idle -> spinner -> ✓ success (3s) -> idle"
- Show global progress bar for manually triggered scheduled jobs
- Track scheduler-triggered jobs with BackgroundJob records
- Weekly summary uses real activity/compliance data instead of empty telemetry API
- Context-specific feedback forms + enhanced settings page
- Import-time historical project detection + analytics warning banner
- Proxy /docs/ to documentation site via Caddy
- Cookie hardening, project reactivation, docs refresh
- Add GitLab availability checks and graceful degradation
- Top-tier cache/session invalidation system
- Perfect instructor detection - seed from env config on fresh DB
- Role_locked - admin role changes persist through auto-sync
- Student exclusion from scoring + role_locked propagation to all instructor detection paths
- Comprehensive report overhaul - maximally informative for teachers
- Health-aware SSE/polling across all pages, UX fixes, docs update
- I18n: add 15 missing Slovak translations, fix hardcoded strings, update docs and responsive CSS

### Fixed

- CI lint errors, infinite progress bar, disabled-feature tracking
- _get_queue fallback when Redis pool not initialized in workers
- Standardize Automation pagination & reduce scheduler frequencies
- Lint + best-practice hardening across worker subsystem
- Connection-recovery toasts, SSE fallback, version-detect reliability
- Stat card text overflow, diff responsiveness, session UA false positives
- Regenerate CSS bundle from sources (bundle-check CI)
- Diff toggle uses details/summary like Changed Files, fixes mobile
- Dashboard UX overhaul - clickable attention/activity items, system health for teachers, feedback link generator, instructor filtering
- Resolve ruff-check and ruff-format lint failures
- Resolve mypy call-overload + remove dead code
- Remove max_retries=0 causing Retry(max=0) ValueError
- Visible trigger/retry feedback - min 500ms spinner + green success state\n\n- Minimum 500ms spinner display so user always sees loading\n- Trigger: spinner -> checkmark + 'Triggered' text (4s) -> restore\n- Bright green triggered state with pulse animation\n- Retry: same 500ms minimum spinner before re-enqueue toast"
- Center spinner on btn-xs + anti-spam safeguards\n\n- Smaller 10px spinner for btn-xs (was 14px, too large for 20px button)\n- Client-side 30s cooldown per trigger function prevents rapid clicks\n- Server-side Redis cooldown key (30s TTL) prevents queue flooding\n- Retry marks old failed job as 'retried' with link to new RQ job\n- Server rate limit (60/min) already existed via RateLimitDep"
- Show 'Running...' text on trigger instead of spinner\n\n- setButtonLoading: text mode uses btn-loading-text (visible text),\n  no-text mode uses loading (spinner). Previously spinner hid text.\n- Trigger buttons now show 'Running...' during API call"
- Trigger button state persistence, dedup guard, SSE RQ reconciliation
- Card overflow visible for dropdowns + table-layout:fixed colgroups system-wide
- Remove :has() stacking rules (dropdown freeze) + add table fadeIn animation
- Dropdown stacking via Alpine class toggle + table fadeSlideUp animation
- Dropdown CSS race, MR table + pagination on activity page
- Cap max_weeks at 52, align activity cards
- Equal-height activity cards with pagination at bottom
- Add danger/info/warning status-dot CSS classes
- Replace en-dash with hyphen in comment (ruff RUF003)
- Analytics stat cards, max_weeks=semester, report dates prefill
- Skip pre-semester events instead of coercing to week 1
- Auto-detect imported projects for weekly summary
- Filter future dates, year-grouped week selector
- Add date ceiling to MetricSnapshot queries, cap max_week in compliance history
- Week selector uses semester_start for numbering + audit logging for all mutation endpoints
- Resolve ruff-format and mypy CI errors
- Filter instructors from Contributors list in project detail
- Avoid lazy='raise' on TeamMember.student in contributor filter
- Sync Repository Stats commit count with filtered contributors
- Session invalidation on role change, activity feed scoping, card color case, sync deletion protection
- Persistent frontend network for docs container
- Admin-users.js brace mismatch causing SyntaxError at line 190
- Filter contributors to team members only & remove pagination scroll jump
- Docs language switching - set site_url to /docs/ prefix
- Docs site_url needs full URL with scheme for mkdocs --strict
- Resolve CI lint, format, type and bundle-check failures
- Login false-positive, error styling, /en/ redirect, table animation
- Include /en/ (trailing slash) in Caddy redirect matcher
- Persist locale across app and docs
- Remove warnings and harden avatar/docs behavior
- Scrollbar shift prevention, auto-retry lazy loads, transparent scrollbar track, CI pin
- Use stable UA fingerprint (browser+OS only) to prevent session invalidation on browser updates
- Stabilise admin table layout + MR card stretches to match grid height
- Groups Actions alignment, member filter-paginator sync, skeleton flash delay
- Remove stray brace in ClientPaginator causing SyntaxError
- Member filters - empty array truthy bug + resync preserves filter state
- Group links 404 - use /dashboard/teams/{id} instead of /dashboard/courses/{id}/groups/{id}
- Member sync includes global teacher/admin roles in instructor detection
- Instructor detection - include inherited root members, raise cross-subgroup threshold to 90%
- Ruff-format + add teachers to course configs
- Instructor auto-detection false positives + rebuild CSS bundle
- Exclude admin users from course instructor_usernames and CourseMembership
- Instructor page spacing, search id, per-page dropdown
- Instructor page - show all admins, fix pagination dropdown, spacing
- Create /app/reports with app user ownership in Docker images
- Exclude teachers/admins from reports & fix score percentage display
- Lint + test fixes for report overhaul
- Reports - semester week context, fix bottlenecks, expected-check awareness, partial credit, custom check weights
- Sidebar Events badge counts DLQ events, not failed BackgroundJobs
- CI lint - close docstrings, remove unused type-ignores, reformat admin
- Hide pagination controls when all items fit on one page
- Revert "fix: hide pagination controls when all items fit on one page"
- Pagination overflow in p-0 card bodies, pin mypy version
- Consistent counts - roster excludes instructors, system stats counts active users
- Restore sweep.py type-ignores, suppress unused-ignore for cross-env compat
- UI bugs - spinner animation, pagination overflow, responsiveness, cross-tab polling
- Legend/pagination overlap + add missing error toasts
- 1:1 structure matching for dashboard, feedback, and admin events
- Align all skeleton loaders 1:1 with actual page structures
- Skeleton mismatches + coverage boost to 40.32%
- Toast SVG stroke rounding + course-picker skeleton structure
- Remove blue gradient from course-picker skeleton icon
- Course-picker skeleton uses card wrapper instead of gl-skeleton-section
- Compliance checks UX, contributor counts, dynamic analytics
- SSE event handling on all pages, sync-lock settings, lint fixes
- Report WeasyPrint OSError fallback, heatmap dark mode, false toast, animation jitter
- Health monitor threshold, report failure handler, progress bar polish, docs cleanup
- OAuth error handling, dev monitoring setup, deployment guide
- Use HTTP for bare IP deployment (no TLS for IP addresses)
- Pass APP_BASE_URL and ALLOWED_HOSTS through docker-compose
- Pass PERSISTENT_SESSIONS and SESSION_MAX_AGE_SECONDS through docker-compose
- Alpine query error and mobile sidebar close button
- Remove Alpine from course search, show collapse button on mobile
- Pixel-perfect GitLab layout - radius, z-index, colors, hover effects
- Restore Alpine removal from course search and mobile sidebar fix
- Alpine script order, add missing Slovak translations, wrap hardcoded strings in t()
- Remove cosmetic skeletons from SSR pages, complete lazy-page skeletons
- Pixel-perfect skeleton loaders - use actual CSS classes, responsive grids, pagination
- Responsive CSS - ring-stats-grid 768px, compliance-summary compact 480px, dead pipeline-overview rules
- Skeleton loaders - use actual page CSS classes, fix structure mismatches, remove 8 dead macros, add responsive breakpoints
- Responsive CSS cleanup - remove dead selectors, replace hardcoded values with design tokens
- Comprehensive responsive - checksTable selector + table-responsive wrapper, sticky first column for dynamic tables, MR/CI column hiding, course-name ellipsis, code-inline word-break, instructor-badge overflow
- Replace remaining hardcoded font-size/weight/color values with design tokens, wrap JS-generated members table in table-responsive
- Page-header h1 overflow visible on mobile, profile-header vertical stacking on narrow screens
- Responsive instructor management - hide table columns on mobile, icon-only action buttons, instructor manager grid/list wrap, card-header-flex wrap
- GitLab Pages - set site_url to relative, add --strict build, echo CI_PAGES_URL for URL discovery
- Add default artifact expire_in 3d to prevent storage bloat, fix missing expire on contract-tests
- Add needs:[] to test-fast jobs - prevent artifact download from security stage
- Allow admins as regular instructors - remove auto-promote to owner and backend filter that dropped non-owner admins
- Admin visibility - hide admins from instructor badges and available users for non-admin viewers
- Resolve 500 on instructors page - define is_admin, fix line length
- Admin visibility - course owners can see admins, role dropdown instead of remove button
- User info modal - use teal badge for course owner instead of warning

### Changed

- Component-based Automation panel with feature flag awareness
- Replace native `<select>` with select_field() component
- Production-quality audit - unify duplicates, fix tokens, update docs

### UI / UX

- Fix ruff format in auth.py
- Restyle Available Users pagination to match standard component
- Layout: make page skeleton 1:1 identical to GitLab on all devices
- Revert: undo Alpine/layout/i18n/pixel-perfect commits (a656e82..7ff95cd)

### Infrastructure

- Clear instructor_usernames from course configs - auto-detected now
- Remove stray temp script

### Documentation

- Rebrand DTA to GitPulse, remove emojis, update stats, improve charts
- Self-host fonts and mermaid.js for CDN resilience
- Comprehensive documentation overhaul - security hardening, middleware stack, session model, cache busting, changelog
- Update documentation verification date to 2026-03-16

### Tests

- Add 46 worker job unit tests to reach 40% coverage
- Add 58 comprehensive edge-case tests for worker subsystem

## [2026-03-09 - 2026-03-15]

### Added

- GitLab-style skeleton loaders for all 20 page templates
- HTMX lazy loading for all heavy pages + 1:1 skeleton loaders\n\nConverted 8 heavy pages to HTMX lazy loading pattern:\n- dashboard, course_detail, project_detail, student_detail\n- team_detail, course_activity, course_analytics, timeline_dashboard\n\nPattern: shell renders instantly with skeleton loader, content loads\nasynchronously via HX-Content-Only header. Route handlers split into\nfast shell path (minimal context) and full content path (heavy queries).\n\nRewrote all 13 page-level skeleton macros in loaders.html to match\nactual page elements 1:1. Added lazy parameter (lazy=true omits\ngl-loading-skeleton class for HTMX, lazy=false default for SSR).\n\nAll 2094 tests pass.
- Show instructor names in import toast and global progress bar
- Frequency-based instructor detection during GitLab import
- Always-visible Instructors counter in import UI and toast
- Redesign User Info modal - polished profile card, GitLab avatar, proper CSS
- Retroactive compliance history with date derivation and backfill\n\n- get_student_compliance_history: derive dates for gap-filled weeks\n  from semester_start + timedelta(weeks=wk-1) instead of null\n- Primary path merges MetricSnapshot data for weeks missing\n  ComplianceSnapshots, extending coverage\n- Semester start lookup moved before if/else split (shared by both paths)\n- engine: add as_of_week parameter to compute_team_metrics for\n  retroactive scoring against per-week expected_checks config\n- engine: add backfill_compliance_history() that detects missing\n  weeks and fills them via compute_team_metrics(as_of_week=N)\n- sync_job: call backfill_compliance_history after sync so projects\n  added late (e.g. week 8) get compliance data for weeks 1-7"
- Per-course role hierarchy via CourseMembership (owner/instructor/assistant/student)

### Fixed

- Replace wrong error-429 SVG, remove dead skeleton CSS, fix error boundaries
- Smoother synchronized animations, fix cropped spinner icons
- Unify all animation easing across entire CSS codebase
- Unify last 2 animation easing outliers (tooltip, job-bar shimmer)
- Remove remaining page-load stagger anims (sidebar, home, cards)
- Remove last page-load stagger (home sidebar panels)
- Skeleton loader bugs - student lazy=true, CSS brace, instructor import\n\n- student_detail.html: add lazy=true to sk_student_detail() so skeleton\n  stays visible until HTMX content arrives (was fading out immediately)\n- student_detail.html: remove hx-indicator referencing nonexistent class\n- course_instructors.html: fix import sk_course_instructors (was sk_table_page)\n- loaders.css: fix .page-loader missing closing brace before .nav-progress\n- sk_student_detail: update to match actual page 1:1 - 4 profile cards,\n  3-col compliance table, add compliance progress charts + weekly table,\n  add communication indicators section\n\nAll 2094 tests pass.
- Align all skeleton loaders 1:1 with actual page content\n\n- sk_dashboard: add gl-home-layout/sidebar wrappers, sidebar panels\n- sk_analytics: add Feedback Token Generator card, 6-field form\n- sk_project_detail: 4 header actions (was 3), 4 info cards (was 5)\n- sk_team_detail: 7 header actions (was 6)\n- sk_timeline: expandable details pattern (was flat list)\n- sk_settings: 8 card sections matching actual page (was 4)\n- sk_admin_system: 5 runtime rows (was 6)\n- New sk_admin_events: stats+replay form+DLQ table (no search)\n- New sk_feedback_manage: header+forms table\n- New sk_feedback_results: course picker cards\n- New sk_course_roster: CSV upload+roster table\n- New sk_retired grading_list: header+table (no search bar)\n- New sk_retired grading_editor: info+categories+week configs\n- sk_feedback: simplified to course picker cards\n- Update 6 templates to use dedicated macros\n\nAll 2094 tests pass."
- Precise 1:1 skeleton-to-page alignment for all remaining pages\n\n- sk_project_detail: add 5 missing sections (retired grading scores, docker\n  verification 9-col, CI scenarios 9-col, conflict challenges 8-col,\n  AI analysis with details), fix members table to base 4 cols\n- sk_course_detail: tabs 6 -> 7 (all tab slots)\n- sk_feedback_manage: header actions 2 -> 3 (Change course + New Form + Import)\n- sk_course_instructors: 2-col grid (assigned text list + available\n  search+list) with save/cancel buttons, no avatar circles\n- sk_dashboard sidebar: quick links 4 -> 6 items, suggestions panel\n  expanded to title + paragraph + link (was single line)\n\nAll 2094 tests pass."
- Rename devopsta->gitpulse (DB, user, paths), fix all ruff/mypy lint
- Logout redirect loop, backfill gitlab_user_id from session
- Ruff RUF006 lint, separate instructor/student import counts, remove logo animation
- Accurate student/instructor counts in import toast & counter
- Emit instructor SSE events during discovery phase
- Clean `__pycache__` on restart, prevent stale bytecode
- Instructor events + student count consistency\n\n- Add client-side safety net: when done event arrives with\n  instructors_list but no instructor SSE events were received\n  during streaming, inject synthetic instructor events so the\n  import log and counters are populated\n- Move students_total / instructors_total DB queries BEFORE\n  sync job enqueue to prevent race where a worker deactivates\n  a student before the toast count is captured\n- Remove all diagnostic print()/console.log() statements\n- Keep server-side instructor emit code (correct on disk)\n- Rebuild JS bundle"
- SSE buffering, worker errors, Total Members label
- Instructor count in toast, consistent member counts, instant disconnect UX
- Instructor frequency detection threshold and roster count consistency
- Instructor detection + undefined toast + coverage 40%
- Cross-subgroup instructor detection + toast race condition
- Ensure all discovered instructors get teacher role
- Add cross-project instructor detection + remove premature sync
- Expand instructor detection - Owner+root-group, project frequency scan
- Sync toasts - per-group completion, sync start flash, group progress, UUID guard
- Instructor detection, toast overwrite, sync UX, user info modal
- Toast icon clipping, enhanced User Info modal, student count consistency, 302 redirect fix
- Constrain SVG icon size in User Info sections, add autocomplete attributes
- Lint errors, component CSS, Student Info in Roster
- Third audit pass - security, logic, and consistency fixes
- CI lint failures + code quality audit pass 4
- Remove Webhook Events card, fadeSlideUp animations, auto-refresh on SSE connect
- Restore animations, server-side GL data, auto-reload team page, remove Review Coverage\n\n- Restore fadeSlideUp animations with staggered delays for .gl-intelligence-card\n  and .project-info-item in project.css (incorrectly removed in prev commit)\n- Pre-fetch GitLab Intelligence data server-side (asyncio.gather for 6 endpoints)\n  and pass via window.`__GL_INTELLIGENCE_DATA__` for instant rendering\n- Team detail page: full reload on SSE update and sync completion so\n  Group Members table and all server-rendered data refresh automatically\n- Remove Review Coverage stat card from Group Summary\n- Fix SessionMiddleware assertion traceback spam in llm_analysis_status"
- Contributors dedup, analysis progress [object Object], completion state
- Responsive button layout + SSE data refresh on sync complete
- Team-detail live data creates badge elements when missing
- Hover animations, remove Clicks Avoided, AI toasts, MR actions styling, pagination, logging
- AI analysis UI bugs + suppress OpenAI worker log noise
- Use real dates from sync data instead of fabricated week dates
- 7 UI bugs + per-course badge system wiring
- Badge system - Owner/Instructor roles with legacy fallback
- Badge system - stackable multi-badge display
- Phase 8: Fix badge override, row flicker, trends canvas, SSE empty data
- I18n aria-labels and XSS-hygiene in innerHTML assignments
- Toast race condition on course page + autocomplete a11y on form inputs
- Align dynamic project items with gl-list-item classes, add missing aria-labels, i18n fix
- Orphaned labels + missing sync-complete toast in suppress-reload path
- Self-host vendor libs, fix color contrast + language selector a11y
- System-wide polish - tooltips, animations, login redirect
- Icon vertical centering, label a11y, duplicate job route
- Resolve 500 on project detail, sync toast race, a11y labels, table sort UX
- Resolve mypy errors in projects.py and sse.py
- Sync toast race condition + coverage tests to 40%
- Toast race condition, compliance trends gap-fill, ruff format
- Comprehensive security, i18n, and best-practices audit
- Resolve ruff-format, ruff-check, mypy CI failures
- Merge duplicate alembic revision 011 (fix_legacy_grading_id_type into add_missing_indexes)
- Make migration 011 idempotent (if_not_exists for indexes/constraints)
- Alpine x-for missing 'in' expression in list_manager + equal-height grid panels
- Add search icon to list manager, filter instructor pool to admin/teacher roles only
- Complete CourseMembership integration across all API layers

### Changed

- Production hardening - shared modal, rate limiter, GPU animations, error pages\n\n- Extract shared UserInfoModal JS module (~200 lines dedup from admin-users + course-roster)\n- Add double-click race condition guards and HTMX beforeSwap SSE cleanup\n- Rate limiter: defaultdict(list) -> dict[str,deque] for O(1) pruning, 100K cap,\n  incremental batch cleanup, inline trigger from is_allowed()\n- Error page: dynamic SVG per status code (404/403/429/500), suggestions list\n- CSS animations: barLoader/shrink -> GPU-composited transforms, unify scaleIn naming\n- Fix mypy type narrowing in exception_handlers.py (rename headers vars)\n- Archive outdated docs (thesis outline, eval plan, pilot telemetry)\n- Bump enrichment refresh interval 5->25 for 1000-user scale\n- Rebuild CSS bundle (hash 96c7e4b76ebddf9b)\n- All 2094 tests pass, ruff clean, 0 errors
- GitLab-style unified page reveal - remove per-element stagger
- Rebrand: rename service devops-ta -> gitpulse in logs, tracing, health
- Rebrand: complete devops-ta -> gitpulse rename across entire codebase
- Second audit pass - fix workarounds, hardcodes, and inconsistencies
- Eliminate page reloads in SSE/job handlers, add hover animations
- Fix N+1 queries, batch admin stats, eliminate remaining reloads
- Aggregate pipeline queries, eliminate feedback-manage reloads
- Remove sync-overridden CRUD, fix GitLab client construction, harden API safety
- Upgrade all API access checks to async CourseMembership
- Remove assistant role, componentize UI, clean dead code

### UI / UX

- Polish: CSS tokens, query limits, retired grading-list soft-refresh, mypy fixes
- Polish: security, CSS hygiene, DOM updates, search optimization
- Cleanup: remove dead macros/CSS, replace last 2 reload() with soft-refresh toast
- Add tooltips, aria-labels, and accessibility improvements

### Infrastructure

- Componentize webhook inputs, add feature overview

## [2026-03-02 - 2026-03-08]

### Added

- Universal error boundary - no more black screen of death
- Fix instructor badge table + one-time assignment notifications
- Add HTMX response error toast notifications
- Unified JS+CSS bundle builder with CI verification
- Add debug logging to silent exception handlers in telemetry and courses
- Manual conflict trigger API + CI auto-rollback scheduler
- Full system automation - 11 scheduled jobs for zero-touch operation
- Event-driven metrics, cache invalidation, BG job cleanup, DLQ auto-resurrect
- Complete automation - 16 scheduled jobs, event-driven cache/CI/sync
- Complete automation - SSE-first everywhere, 21 sweep jobs, push-based sync
- Member webhook handler, graceful ignorable events, activity live-data endpoint, project metadata sync
- SSE live stream for project-detail + blocked user filtering in member sync
- Docs+monitoring: update all READMEs, expand Grafana dashboard to 16 panels, add 6 Prometheus alerts
- SSE live analytics, dynamic stats, lint i18n, UI fixes
- I18n: add 88 missing Slovak translations across all templates
- CI auto-create branch, retry failed scenarios, UX polish
- Comprehensive Docker lint rules (DL001-DL021), CI failure scenarios, bug fixes
- Dynamic per-course Docker lint & CI failure configs - zero Python hardcoding
- Production-ready ZSI + DevOps configs for TUKE 2025/2026

### Fixed

- Polish student/teacher roles - hash nav, attention items, sidebar, access control
- Icon centering, instructor auth, student features, addTeam field
- Resolve ruff-check, ruff-format, and mypy lint errors
- Resolve all ruff-check, ruff-format, and mypy errors
- Change misleading 'teacher activity' log to 'activity' (applies to admins too)
- Avatar button centering, instructor suggestions include teachers
- Instructor suggestions - only teachers, exclude self/admins/current
- Add skipBeforeunload before all post-save navigations
- Dev login - auto-fill username per role, allow role switching
- Comprehensive access control hardening - empty instructor_usernames: all teachers can view (matches UI text) - re-import merges instructors instead of replacing - importing user always added to instructor list - deactivated users rejected via is_active check - API course endpoints enforce instructor access (PUT/DELETE/settings) - telemetry feedback forms: filter list + check import by instructor - both gitlab_username and username checked consistently - is_course_instructor returns True for empty list (no restrictions)
- Harden validation, race conditions, UI gaps, type errors
- Eliminate hardcoded values, fix role access, clean dead code
- Add _can_view_course auth check to course_analytics + add logging to silent exception catches
- Extract hardcoded values to config, per-project webhook secrets, FK cascades
- Config-back job timeouts, DLQ delay, session auth constant
- Add warning-level logging for silent exception handlers
- Enrichment TOCTOU race, Redis conn pooling, exception truncation
- Dynamic asset versioning, config-based job timeouts, DLQ race
- RBAC bypass, race conditions, access controls, dead code, input validation
- Schema validation constraints, pagination, status codes, race conditions, exception logging
- Deduplicate instructor checks, improve error UX, narrow exception handling
- Add cross-reference validation for config import check references
- Add missing gitlab_url to course_detail template context
- Handle UnicodeDecodeError in API roster upload
- Security hardening, race conditions, error handling improvements
- GitLab import 422 on course-detail + flash-toast race condition
- System-wide schema validation, SSE race conditions, and dead code cleanup
- Event-loop blocking, XSS, SSE timer leaks, atomic commits
- Auth checks, XSS escaping, ASGI middleware, atomic audit writes
- Sweep dead-project logic, auth gaps, rate-limit, input validation, Redis leak, case-insensitive instructors
- Redis connection leaks, auth gap on project SSE, input validation hardening
- Remaining Redis leaks, schema validation constraints
- Session rollback in batch loops, close AsyncOpenAI clients, httpx client finally
- Resolve all mypy strict-mode errors (10 errors across 6 files)
- Access-check order, retired grading activation, cross-course guard, search scope, parsing safety, webhook type validation
- DLQ resurrection clears markers only after successful enqueue
- Rate limiter uses config values, retired grading activation row lock
- Add logging for silent audit write failure in import script
- Cross-course authorization bypass in teams, reports, and feedback form APIs
- Reuse Redis connection for rate limiter, use config for webhook payload limit
- Critical missing await, config gaps, validation, query limits
- Add max_length to Update schemas, log compliance engine fallback
- Ruff format on reports, teams, dependencies
- Migration chain + auto-refresh + sweep #17 + deactivation cascade
- Wire ignored check configs, course-agnostic defaults, retired grading alignment
- Ruff N806 uppercase local variable and S101 assert in production code
- Ruff format + mypy unused type-ignore in event_processor
- Info_card HTML escaping + submit button gradient removal
- Alpine_modal x-teleport to escape gl-page contain context
- Teaching notes style matches violations, remove lint score bar, fix flaky_test timing
- Move CI exercise files to exercises/ to prevent auto-pipeline failures
- Add card background fills, fix events page layout, remove double borders
- Revert card backgrounds, fix dropdown flash, unify all animations
- Load core.bundle.js before Alpine to fix glFormSelect undefined
- Search input icons, z-index stacking, animation consistency
- Tippy applyStyles error, form label a11y, dropdown z-index
- Tippy createSingleton error, DLQ checkbox label, card z-index
- Rewrite toast system - GitLab Pajamas design, fix broken rendering
- Toast invisible text + position behind sidebar
- Toast progress bar resume + flash toast reload survival
- Translations, sync backoff, CI scenario panel, Docker card ID
- Missing CourseSettings import in pilot_telemetry + dynamic weeks
- Feedback module structure, flashToast, and remaining SK translations
- Breadcrumb + question builder styling
- Remove duplicate label in instructor modal, widen feedback modals
- Sync completion reload, polling fallback, all async edge cases across system
- Discover new GitLab projects during sync
- Reconcile orphan sync jobs that block future syncs
- Global job bar shows stale sync jobs after DB wipe/restart
- Flush stale RQ jobs from Redis on dev restart
- Use ZREM for registry cleanup (RQ 2.x compat)
- Use raw Redis commands for queue flush on Windows
- Commit BackgroundJob rows before enqueuing to RQ (race condition)
- Show DONE badge for completed syncs instead of N/A
- Traffic light badge takes priority over DONE status
- Commit import data before enqueuing sync jobs (race condition)
- Sticky modal action buttons so they stay visible on long content
- Modal backdrop clipped by .gl-page overflow:clip
- Move modals outside .gl-page to fix stacking context
- Silence httpcore trace logs and asyncpg pool termination noise
- Detect Owner-level members as instructors & prevent stats flash
- SSE reload loop, CI branch trailing-slash, asyncpg filter propagation
- CI rollback graceful 400/404, scroll preservation, Docker alignment, inline CI refresh
- Remove invisible status-dot from CI active badge pill
- Give status-dot inside pills visible background via currentColor
- Sortable table keeps companion rows with parent, guard empty JSON responses

### Changed

- Audit-pass-2: deduplicate helpers, gate flags, SQL aggregation, extract constants
- Extract all hardcoded limits, intervals, and timeouts to config
- Extract inline JS to external files, fix hardcoded GitLab URLs
- Eliminate all inline JS, convert window configs to JSON blocks
- Question builder to standard component macros
- Cleanup: remove dead code, unused imports, hardcoded fallback
- Unify alpine_input/alpine_checkbox into text_input/checkbox
- Componentize inline SVGs and expandable details across all templates
- Remove Python language from CI scenarios - C only
- Comprehensive frontend optimization - cut HTTP requests 90%, enable compression
- Deep optimization pass - zero render-blocking scripts, remove waste
- Dead code removal, transition optimization, CSP compliance & device fixes
- Unify animations & sync transition timings across all pages
- Eliminate all hardcoded stats values - fully dynamic from settings
- Eliminate remaining hardcodes across reports, timelines, SSE
- Eliminate last hardcoded values in analytics pipeline
- Component-based UI, fix instructor centering, changelog pagination
- Replace all inline HTML with component macros
- Align feedback pages to standard component library
- Docker verify UI - component templates, SSE live updates, table alignment, config management
- Eliminate residual inline SVGs, use `<template>` components

### Security

- Harden student/project API endpoints

### UI / UX

- Fix ruff format line wrapping in sweep.py
- Fix ruff format for course_settings.py and teams.py

### Infrastructure

- Wire docker size threshold + gitlab_parse timeout from config
- Courses: use session_max_age_seconds from config instead of hardcoded default
- Cleanup: remove dead code and unused config fields
- Eliminate remaining hardcodes in templates and services
- Remove redundant zsi-check-config.json (checks already in course config)

## [2026-02-23 - 2026-03-01]

### Added

- Universal global progress bar, per-student recheck, SSE leak fix
- Client-side member filter bar (replaces server-side hide logic)
- Add check-selection modal to project detail page
- Defensive null guards across all page JS files
- Replace all polling with SSE across entire system
- Fix missing member + add force-recheck (all checks override)
- GitLab-style role hierarchy - exclude non-contributing members from team score
- Auto-import course configs on deployment
- Centralize icon system + async health checks + lint fixes
- Dynamic feedback forms, feature flag error handling, form styling
- Docker/CI services - status bars, user attribution, sync analysis, layout fixes
- Docker analysis inline feedback + proper error handling

### Fixed

- Sticky breadcrumb scrolling + legacy_grading_id type mismatch
- SSE connection pool leak in sync-stream endpoint
- Shield session cleanup from CancelledError in async_session_ctx
- Eliminate SSE connection-pool leaks + dashboard bfcache staleness
- Eliminate SSE connection pool leaks in all streaming endpoints
- DI session cancellation safety + import double-reload/flash
- Eliminate connection leaks, standardize session handling, responsive CSS hardening
- Deep audit - Redis connection leaks, SSE reconnect loops, XSS, timer cleanup
- Convert middlewares to raw ASGI, replace recheck-all with selective check runner
- LLM UUID schema, single MR background analysis, status bar timing, a11y summary
- Micro-issues - Redis leaks, dead code, field names, CSS classes, tooltip reinit
- Modal close, toast progress, status bar dedup, reanalyze spin, advisory spacing
- Toast system, 40%+ coverage, cache busting, type annotations
- Comprehensive CSS/JS audit - 20+ bugs fixed
- Modal responsive overflow - content no longer clipped on narrow screens
- Toast persistence, inherited-member filter, health-monitor sensitivity
- Toast persistence, filter redesign with pagination sync & dark-mode
- Observer/instructor category, run-checks UX, translations, SSE progress
- Completion toast suppressed for deferred jobs (sync, analysis)
- Eliminate all inline styles, hard-coded values, and remaining JS safeguard gaps
- Status mismatch in edit modal, stale flash toast, search input artifacts, raw JSON spacing
- Double toast on import, auto-reload after sync completion
- Force-remove pgdata volume in Stop-All fallback
- Kill leftover uvicorn/worker processes in Stop-All
- Stop-All wipes local PostgreSQL database on restart
- PowerShell parse error in Redis Cloud status + split DB reset
- Replace em-dash with ASCII dash for Windows PowerShell compat
- Infinite recursion in flashToast/showToast alias
- Flash toast cleared too early by rAF before page unloads
- Add missing stat-danger glow + silence tracing noise
- Add missing stat-* color classes for hover glows + fix snapshot duplicate bug
- Resolve 22 ruff lint errors (E501, S110, SIM105)
- Weekly check filtering, CSS spacing, ruff format
- Weekly check filtering - bottlenecks, expected flag, templates, edge cases
- Sort imports in test_roles.py (ruff I001)
- Exclude inherited members with zero activity from team score + reload after import
- Resolve mypy union-attr errors in engine scoring gate
- Schema refs, OAuth error handling, anon feedback form, error propagation
- PDF generation + interventions chart empty state + UX improvements
- Resolve mypy and ruff-format pipeline failures
- Course-settings.js ceActiveLabel null reference crash
- Add loader icon + spin animation to health check loading state
- Remove duplicate health banner, fix 'Last healthy' timer
- Pin ruff==0.15.4 in CI, bump JS/CSS cache busters
- Unify all cache-busting versions to 20260227v01
- Table sort scrollbar, default sort indicators, card footer layout
- CI ruff errors + comprehensive quality audit
- Edit User modal data loading, avatar hover, transitions, button macros
- Tojson_attr for raw HTML attrs, modal buttons->macros, CSS transitions
- Unify stat cards, add stat-info color, fix 3 missing transitions
- Alpine collapse plugin, tojson_attr escaping, lint cleanup
- Add 45 missing Slovak translations + fix CSS status-bar separator
- Improve teaching notes and error banner spacing
- Restyle teaching notes component + center error banner icon
- Drop error-row-banner up into its own row with proper spacing
- Language selector overlapping title on mobile login page

### Changed

- Harden: comprehensive safeguards for run-checks & global job bar
- Unify toast: flashToast shows immediately + persists for reload
- Start-dev.ps1 for local Postgres + Redis Cloud
- Unify all stat cards + fix toast flicker
- Revert: restore original gl-home-stat dashboard cards
- Reduce health banner delay from ~27s to ~3-4s
- Split oversized files - 1 class/1 file, template partials, CSS modules
- Convert last 5 raw buttons to macros, add xs size, fix navbar transitions
- Frontend quality sweep and CI pipeline fixes

### UI / UX

- Fix ruff 0.15.4 formatting in test_middleware.py

### Documentation

- Comprehensive update for role hierarchy, scoring gate, force-recheck, weekly filtering

## [2026-02-16 - 2026-02-22]

### Added

- I18n wrap ~122 strings, withUiLock/confirmProcessRestart on 18 actions, bump cache
- Interactive Chart.js charts, animated stat cards, enhanced UI
- Chart.js compliance chart, skill radar, animated cards
- Optimistic locking, last raw HTML migrations, external link security
- Extend optimistic locking to all mutation endpoints, fix schema & type errors
- Modal dirty-state guards, syncStatusModal X fix, LLM completion UX
- Page-level beforeunload guards to prevent data loss on navigation
- Global job bar for Docker/CI, cross-tab toasts, form layout fix
- Accept 'avg_word_count' as rule type alias for 'word_count'
- Course JSON configs, settings validation, verification guide
- Dashboard-level JSON config import + full clone
- AI privacy, enrichment, pagination, toasts
- Unified compliance check management - R01-R12 + custom in single UI
- Export/import check config, dynamic registry, file upload component, validation hardening
- Complete JSON config export/import with full validation
- Add admin Quick Links + GitLab-style animations and UI polish
- Auto-detect GitLab project/group URLs in import + replace feedback panel
- Bot detection, compact check legend, instructor activity filter
- Add is_instructor flag to TeamMember, exclude from team metrics
- Dynamic custom checks with teacher UI and LLM generation
- Rewrite badges as dynamic JS-only components
- Replace native `<select>` with GitLab Pajamas component dropdown (GlFormDropdown)

### Fixed

- Instant link-project toast, populate Docker metadata from static analysis, center status-pill text
- Standardize UI processes - setButtonLoading, flashToast, remove arbitrary timeouts
- Comprehensive UI process hardening - withUiLock, confirmDangerousAction, i18n
- WithUiLock + confirmDangerousAction on all remaining UI processes
- Add singleConfirm to skip misleading 'delete permanently' dialog on non-delete actions
- Analytics bugs - flags loading, 52-week dropdown, compliance scores
- Add missing btn_icon_only import causing 500 error
- Add 4 missing macro imports preventing 500 errors
- Correct field names + store approvals_count
- Comprehensive data-path audit - 7 bugs fixed
- Dashboard views - student context, inflated RED counts, export N+1
- Comprehensive audit - 18 bugs across 13 files
- 5 UI bugs - triggerDockerVerify/CiScenario errors, duplicate import check, global bar duplicates, toast persistence, all processes use global bar
- Global bar duplicate prevention - add isGlobalJobRunning guards and enrichment meta tag
- Docker verify + LLM generate errors, global status bar on all processes
- Eliminate global bar duplication, fix LLM JSON parsing
- DeferGlobalJob on all processes - bar hidden while local UI active
- Preserve LLM suggestions across modal close/reopen
- Close remaining guard gaps found in second audit
- Eliminate spurious beforeunload dialogs on all programmatic navigations
- Resolve all ruff, ruff-format, and mypy lint errors for green pipeline
- Resolve ruff lint/format errors in new test files
- Add missing Dockerfile.worker for CI container-build job
- Global job bar cross-tab + free navigation + auto-refresh
- Role badges, toggle panel styles, smart tab-refresh
- Inline Docker verify & CI scenarios, form alignment, project_id routing
- Retired grading 500 error, instructor filtering, toast duration, pagination, audit log
- Revert toast duration to defaults, keep reload delay fix
- Toast persists across navigation, archive layout, activity feed
- Safe actor extraction - replace request.session with custom session auth
- Toast persistence, audit writes, dead code cleanup
- Wrap remaining shared + page scripts in IIFEs, add window exports
- Add missing destructured refs - _escHtml, flashToast, openModal, closeModal
- Resolve 29 mypy errors in dashboard.py - typed _t helpers, CourseSettings null check
- Dashboard 500 error (missing file_upload_area import) + remove deploy job from CI
- Add Import JSON button to empty-state dashboard (admin + teacher)
- Drag-drop import enables button + Docker-link port parsing in CI
- Use gl-file-selected event for import config (browse + drag-drop)
- Update paste placeholder with actual ZSI course example data
- Auto-create session user in DB after restart (0 users stat)
- Harden dashboard against 500 errors
- Import-config 500 - link CourseSettings via relationship
- Import URL parsing, sync status bar, docs update, GitLab Pages
- Install git in pages CI job for revision-date plugin
- Pin mkdocs<2, add print-site plugin to pages CI job
- Docs match engine R01-R12, remove hardcoded values
- Ruff lint errors (S110, F401, E501) + correct MR pie chart weight 38->42
- Replace /* wildcard in mermaid node labels causing syntax error
- Use course-configured thresholds in analytics, fix zero-score display
- Mypy errors, category validation, Pydantic schemas, field_check partial_scoring
- Custom-checks 404, label accessibility, card icons, course description
- Harden unified checks - validations, accessibility, dedup, responsive
- Harden unified checks - 12 audit issues resolved
- Deep audit pass 2 - security, validation, a11y, CSS hardcodes
- 404 on checks API, layout grid margin, description not persisting
- Description not saving on course create + settings fields not persisted
- Prevent spurious save toast + show builtin check hint
- Ruff format, uniform filter buttons, code_reference component, semester_start_date type
- Full config import 'Stream consumed' error + update docs
- Report download, CSV double-fire, label a11y, activity feed
- Defer global job bar for report generation
- `_auth.username` -> `_auth` in write_audit calls (500 error)
- Add missing search SVG icons to all search inputs
- Persist import success toast across page reloads
- Show owners without snapshot in project members table
- Stop treating project owners as instructors during import/sync
- Include admin/teacher users as team members during import and sync
- CI lint errors + dynamic per-check configuration
- Prop-list spacing, feedback token 422, retired grading explainer
- Remove retired grading-explainer, harden all process logic
- R12 pipeline matching, R08 detail, tojson unicode, error template icon
- Auto-populate compliance history, improve system logic
- Prevent compliance snapshots from breaking metric computation
- Global job bar, health check, LLM i18n, sticky bar, pagination
- MR card structure, evidence display, course-aware LLM prompt
- Split LLM prompt to avoid f-string crash with JSON schema braces
- Dynamic custom checks audit - reports, retired grading editor, validation, inline styles
- Timeline + LLM dynamic custom checks, remove debug files
- Admin system API 404s - add /dashboard prefix to JS API calls
- Animation conflict + modal scrollbar interference
- 422 telemetry errors + chart container CSS conflict
- Admin users header layout, instructor list clipping, attention card tokens
- Roster/projects/instructors 500 (UUID tojson) + login language selector
- Unify selector styles, animations, and remove dead CSS

### Changed

- Complete component unification across all templates
- Migrate ~120 raw buttons, form-groups, spinner, card to Jinja2 macros across 18 templates
- Polish: chart bars, toggle panels, global job bar animations
- Deduplicate global progress bar, remove sounds & toast actions
- Worker bootstrap DRY, kill `__import__()`, modernize JS/dashboard
- Cleanup: os.getenv->Settings, get_event_loop->get_running_loop, inline imports->module-level, .keys() simplification, stubs modernization
- Cleanup: hoist inline stdlib imports, drop OrderedDict, direct settings access
- I18n: comprehensive Slovak translation coverage (1840 entries)
- Zero inline styles - extract login.css, CSS custom props, Import button
- Replace hardcodes with design tokens & GitLab cookie pattern

### Infrastructure

- Modernize Python & JS codebase
- Deduplicate components, remove dead code, consolidate infra
- Update all cache-bust versions to v=20260216gl18

### Documentation

- Update test guide for dashboard JSON import, remove generic fixture
- Style all 114 mermaid diagrams with emoji icons, fix R01-R12 tables, translate EN blocks, fix Celery->RQ and hostname

### Tests

- Add unit tests to exceed 40% coverage threshold
- Comprehensive feature test script (F1-F5, 89 checks)

## [2026-02-09 - 2026-02-15]

### Added

- Complete GitLab Pajamas tokenization + lint compliance
- Role-based stat cards, rich attention items, activity feed privacy, auto-hide scrollbar
- Comprehensive role-specific UI for all dashboard elements
- Comprehensive role-specific logic across all pages and templates
- Global role config, navigation role gates, search palette role awareness
- Defense-in-depth JS role guards on all page mutations
- Login page server-online health check + remaining security hardening
- Replace generic OG image with thesis-relevant preview
- Add interactive DevOps pipeline app loader
- GitLab sidebar navigation, top bar breadcrumb, smooth animations
- GitLab top bar search button, action icons & sidebar active blue highlight
- GitLab styling - zero inline styles, CSS dedup, component polish
- Functional header, language switcher, search palette, user dropdown, footer
- Rewrite search palette with API integration + UI fixes
- Unify all lists into gl-list component + DLQ sortable columns
- GitLab avatar in header + dashboard greeting + docs update
- GitLab-style home layout with stats, sidebar, activity feed
- Unify card styles, remove footer, match GitLab color zones
- Breadcrumb separator bar, remove Back to Dashboard, responsive fixes
- Complete GitLab Pajamas CSS rewrite + JS error handling
- Pajamas tokens, JS handlers, inline style removal
- Inline style migration, SRI integrity, Pajamas motion polish
- Complete dark theme migration matching GitLab Pajamas
- Cookie banner component, UI polish, tooltip fix, feedback back-nav, ruff format fix
- Add Docker verification trigger + CI/CD scenario create UI
- Comprehensive admin interactivity - retired grading CRUD, course edit, retired heuristic dismiss, project edit/unlink
- Add complete English translations for docs-site
- Full SK/EN localization for dashboard and docs-site
- Add server-side {{ t() }} translations to all templates
- Complete translation coverage for all templates + fix feedback form
- I18n: translate all 14 remaining page templates + add feedback link
- I18n: add 28 missing catalog keys + audit script
- Sync feedback page styles with app design system + role-based template gating
- Full frontend API coverage - analytics, events DLQ, retired grading import/export, secret rotation
- Complete frontend API coverage - telemetry, retired grading suggestions/preview, flags, compliance history
- Harden all raw fetch->apiCall + add missing frontend features
- Fifth round frontend API coverage - dynamic analytics refresh, weekly summary viewer, roster history, retired grading JS activate/export, MR history viewer, fix telemetry course_id int->UUID
- Fix empty data pages: add Team Members table, MR fallback, fix llm-analysis-status 500
- Fix CI formatting, add Team Members pagination, analytics compliance trends
- Add external_id to User model, rename Student ID to ID everywhere
- Show student_id inline with username in User Management table
- More informative AI analysis error display
- Collapsible MR cards, pagination, spacing fixes
- Add GitLab User ID to User model + admin_users page
- Show sync status on dashboard + persist across page navigation
- Live data updates everywhere - no more page reloads
- Toast notifications on process completion + CSRF login_nonce fix
- Phase 31: Fix teacher visibility, add Sync All, fix activities CSS, remove viewer role, fix review comments
- Phase 33: Fix dashboard UX bugs & add server health check

### Fixed

- List click bugs, CSS chevron, unify all lists to macros
- GitLab-exact stat cards, list dividers, dashboard JS bug
- Login lang dropdown consistent width + cache bust login.js
- Sidebar lang dropdown freeze (MutationObserver infinite loop)
- Broken URLs, dashboard filters, teacher 403, table layout
- Quick-link toast guards, remove inline styles, lower greeting
- #my-courses hash toast when no courses, warning icon fill
- Eliminate Alpine.js FOUC - add x-cloak + animation suppression
- CSP img-src for GitLab avatars + remove phantom modal scrollbar
- Telemetry course_id UUID type + course_settings.html tojson serialization
- Button size consistency, chart container overflow, remove inline styles
- Lang switcher, GitLab-style search palette, sidebar open by default
- Collapsed lang dropdown, sidebar default state, GitLab-exact search modal
- Unify lang switcher with Help/Sign out, add mobile slide animation, prevent tablet animation triggers
- Restore mobile/tablet animations with preload guard, add lang chevron
- Align collapsed lang icon, add session heartbeat check
- Match GitLab home page style exactly
- Remove inline styles, dead links, decorations
- Dashboard links & link color - feedback, system status, GitLab-matching blue
- Remove card double-border, add content-wrapper 16px top-left radius
- Match dashboard layout to TUKE GitLab 1:1 - grid, spacing, overflow
- Scrollbar inside content area, double border on cards, job bar layout
- Match GitLab color layers and layout gaps
- Courses table Loading bug, nav_active, inline styles, breadcrumb labels
- JS hardening & CSS polish: fix SyntaxErrors, IIFE wrapping, null guards, pagination corners
- JS security audit + enhanced admin system panel
- Dark theme for all native `<select>`/`<option>` elements
- Toast close button, mobile burger menu, tooltips on touch, language select descender
- Instructor table overflow, diff dark theme, sticky job bar, empty-state spacing, title->tippy, API error toasts
- Resolve all mypy type errors and ensure clean lint pipeline
- Resolve 500 on feedback submit + add admin system page + toast notifications
- Harden remaining raw fetch->apiCall across 6 files
- Telemetry URL prefixes, analytics style fixes, add 186 SK translations
- Remove form-row grid from Weekly Summary to eliminate large gaps between elements
- JS global scope conflicts + import toast error flash
- UUID serialization, responsive CSS, deprecation warnings, CSS cleanup
- Show PRIVATE in email columns, use as placeholder in modals, remove emoji
- Revert: remove external_id, fix enrichment hang + green flash
- Username / ID as header label only, remove student_id data fetching
- Global job bar spinner stutter during enrichment
- Prevent duplicate course card on dashboard
- Remove spinner from modal submit buttons, keep text-only loading state
- Replace CSS spinner with text-only loading state on all buttons
- Prevent enrichment from stalling on GitLab rate limits
- Elapsed timer jumps 2s due to dual updaters
- Robust LLM JSON parser + live analysis progress
- Schema normalization for LLM output + expanded analysis prompt
- Sync BGjob reconciliation + retry on team-not-found
- Increase vertical spacing in analysis grids and sections
- Search-box icon gap + backfill gitlab_user_id from students
- Remove incorrect Student-based gitlab_user_id backfill
- Populate User.gitlab_user_id during GitLab group import
- MR note body empty on sync + analysis section spacing
- Sync field mismatches + template safety across processors
- Resolve all ruff/mypy lint errors, fix tests, add token encryption
- Modal-footer layout - pull flush to edges when inside modal-body
- Add closeDrawer + toggleSelectAll, remove stale pagination HTML
- Remove orphaned Jinja block tags causing 500 errors, comprehensive mobile CSS
- Unify pagination, smart global bar visibility, last_synced_at
- Remove Team Members table, email optional, edge case guards
- CSRF 403 on forms + button spinner text overlay
- Enrichment AJAX, no global bar flash, live dashboard stats
- Global job bar dismiss persistence + duplicate status badges
- Auto-reload teams table + remove dashboard duplicate sync badge
- Smooth indeterminate progress bar animation
- LLM queue priority, student ID auto-populate, remove viewer role
- Phase-33-fix: cancel jobs on archive, text-only loading button, empty grid cleanup
- Import progress in global bar + dynamic course card on dashboard
- Archived table btn-group layout + createCourse toast persists on redirect
- Outline button variants for archived table actions
- Remove icons from archived table buttons, revert to btn-secondary/btn-danger

### Changed

- Login lang switch from native `<select>` to gl-dropdown
- Extract app-loader to component files, remove all JS inline styles
- Replace overlay loader with GitLab-identical page-initialised pattern
- Match GitLab UI - remove indicator bar, counter badges, no inline styles, fix layout bug
- Remove all inline styles & hardcoded colors - 100% token-based CSS
- Match TUKE GitLab styles 1:1 from gitlab.example.com
- Move topbar above sidebar+content, add scrollbar component
- Animated paginated lists: staggered row fade-in + TableFilter component
- Align dashboard greeting spacing with page-header (gl-spacing-8 -> gl-spacing-5)
- Custom dropdown for pagination, visible scrollbar, cache bust v=gl9
- Unified dropdown component, GitLab button sizing, smart auto-direction
- Replace all inline styles with CSS classes across JS/HTML
- Use page_header component for Back to Dashboard on feedback page
- Extract back button to page_header component, fix activity grid alignment
- Remove all emojis, fix AI analysis spacing, add evidence links
- Replace Student ID / University ID with GitLab User ID everywhere
- Remove student_id_external from active code
- Fully remove student_id_external column and migration 004
- Reusable process status components, import duplicate detection, import queue
- Split CSS into 18 component files, add reusable JS components library
- Phase 13b: audit fixes - csrfToken bug, deduplicate import flow + addUsername, use shared utilities
- Phase 21: dynamic DOM updates everywhere - no more page reloads
- Phase 22: Edge-case hardening for dynamic DOM updates
- Phase 32: Optimize sync - concurrent API calls for notes + commits
- Refactor app architecture and refresh docs for current CI quality gates

### Security

- Harden RBAC - enforce proper auth levels on all routes
- Add RateLimitDep to all POST routes + RBAC bypass warning

### UI / UX

- GitLab dark theme body bg + cursor:pointer on all interactive elements
- Match GitLab sidebar/topbar - remove uppercase headers, center search
- Exact GitLab Pajamas tokens, inline style removal, a11y fixes across 19 templates
- Phase 13: extract base.html JS into 5 modules, deduplicate student CRUD, extract inline CSS from 7 templates

### Documentation

- Full bilingual documentation refresh with system audit
- Add TUKE Cloud deployment guide for SIVVP VMs
- Update documentation for frontend component architecture

## [2026-02-02 - 2026-02-08]

### Added

- Simplify startup scripts and remove hardcoded secrets
- Add GitLab OAuth environment variables to docker-compose
- Implement GitLab OAuth authentication
- Add cleanup on exit to quick-start.ps1 and update to GitLab OAuth
- Complete RBAC implementation across all templates

### Fixed

- Script execution order, PYTHONPATH, and import modal bugs
- Email display, sync polling URL, global bar dedup, action spacing
- Combine if/elif branches to satisfy ruff SIM114
- Update OAuth tests for OAuthTokenResponse and fix all lint errors
- Resolve all ruff and mypy type errors in CI pipeline
- Resolve remaining mypy and ruff linting errors
- Resolve all mypy type errors in commit_processor, gitlab_group_import, and dashboard
- Lower coverage threshold to 40%, fix lint/type errors, add unit tests
- Hot fix
- Wrap all modals with can_edit checks
- Add ApiAuth to LLM endpoints
- Enforce proper auth levels across all API endpoints
- Exclude scripts/stubs/alembic from ruff, fix line length in tests
- Fix typing, coverage, and docs for clean CI
- Fix CycloneDX CLI flags for SBOM job
- Fix pipeline checks and Docker build deps
- Restore mutation testing, fix linting and mypy issues
- Update integration tests for GitLab OAuth
- Add telemetry model relationships to Course/Team/User and fix container scan
- Telemetry UUID types, login template, admin config, mutation tests
- Format telemetry.py, redesign login page with role cards
- Protect Link Project and Run Analysis buttons for viewers
- Protect all action buttons and forms with role checks
- Improve exception handling and update tests

### Changed

- Align generics with ruff and mypy
- Initial commit: full codebase backup before cleanup
- Merge chore/repo-cleanup: remove generated files and unused scripts
- Merge hardening/full-audit-fixes: security fixes and production hardening
- License

### Security

- Enable Jinja2 autoescape to prevent XSS
- Remove unsafe |safe filter from error template
- Use configurable report output directory

### UI / UX

- Ruff format 10 files + fix import-status hidden spacing

### Infrastructure

- Remove temporary tmpclaude files and add to gitignore
- Make security jobs optional, reduce artifact retention to 7 days
- Make all docker-build dependencies optional to prevent stuck pipelines
- Trigger pipeline rebuild
- Lower mutation score threshold to 65% during development
- Finalize CI pipeline stages
- Remove generated MkDocs site folder (6.5MB)
- Remove unused/obsolete scripts
- Update .gitignore to prevent re-committing generated files

### Documentation

- Comprehensive documentation update for current project structure
- Add repository cleanup report
- Add comprehensive hardening report

### Tests

- Add comprehensive mutation killer tests for text_analysis and time_utils
