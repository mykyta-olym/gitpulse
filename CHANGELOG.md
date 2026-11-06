# Changelog

All notable production changes are tracked here. The published docs changelog is
kept in `docs-site/content/changelog.md` and `docs-site/content-en/changelog.md`.

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

- Share the native upload control between JSON imports and Markdown attachments, including keyboard access, focus and disabled styling. Remove the separate scripted Markdown file picker.
- Keep full upload labels, attachment hints and course teacher headings on desktop; use compact equivalents on narrow screens through shared responsive components.
- Truncate long selected JSON filenames so the upload control stays inside the editor on narrow screens.
- File selection alone does not mark a form as edited. Successful JSON loads and attachment insertions notify the shared dirty-state guard; rejected uploads keep an untouched form clean.

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

- Tie shared button, table and card loading states to pending work. Delay spinners for fast responses, announce busy state immediately, and remove artificial 450–800 ms completion holds and the invisible animation clock. Cached data and server-rendered rows are available without a cosmetic wait.
- Release retry controls when requests finish, preserve existing content on failed refreshes, and measure natural content height when retargeting an active transition. Bound loading of the shared User Info renderer and allow retry after an asset failure.
- Show a degraded System Health summary when a displayed GitLab or email check fails, while keeping the infrastructure readiness probe independent.
- Keep Assistant search and filters interactive during activity reads; defer replacing results while the reader is typing and release only the current read's table state.

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

## [2026.10.29.post6] - 2026-10-29

### Fixed

- Render readable task labels in the failure log without an inline code block forcing long names into adjacent cells on mobile. Use the shared badge component's default gray variant for queue names.

## [2026.10.29.post5] - 2026-10-29

### Fixed

- Distinguish retained RQ failure history from new execution errors. The worker exception handler records errors, including retry attempts, in a Redis-backed counter; Grafana and the one-hour alert use that counter instead of the change in registry size.
- Add an administrator-only failure log to Service status, with bounded reads, last activity, causes, remediation hints and expandable diagnostic references. Keep arguments, exception messages and credentials out of the page; retain historical records.
- Reuse shared tables, badges, pagination, disclosures and refresh states. Move the existing code-reference component styles from the course page into shared forms; preserve pagination during refresh.

## [2026.10.29.post4] - 2026-10-29

### Fixed

- Upgrade Alpine CSP and collapse to integrity-pinned 3.17.5. Apply a documented, verified exclusion for the deprecated window.fence getter that upstream still reads during initialization. Remove the old standard Alpine runtime, rollout flag and weaker CSP fallback.
- Use the shared Clipboard API path for code context and revealed webhook secrets. Remove execCommand, temporary textarea fallbacks and duplicate copy handlers. Buttons and links inside a disclosure summary no longer toggle its contents.
- Delete the uninstantiated Redis project limiter, adaptive circuit breaker, request batcher, unconsumed cache statistics and inactive metric registrations. Retain the active API retry, response cache, queue backpressure and observability collectors.
- Remove test-only reset functions, the unused CSRF-only page projection and obsolete model re-exports. Import models from their owning modules, use test fixtures for isolation, and trim descriptions and tests for retired implementations.
- Apply configured queue watermarks to webhook admission and document the cache and queue paths that actually run.

## [2026.10.29.post3] - 2026-10-29

### Fixed

- Preserve outgoing page geometry during navigation: component selectors, table column widths, horizontal scroll, sticky controls and chart canvases stay intact until the incoming page is ready. Restore interaction and focus after success or failure.
- Keep user-info modal loading visible through the shared handoff; ignore canceled and superseded responses. Prevent an earlier table read from clearing a newer read's busy state.
- Use shared button outcomes for HTMX and ordinary POST forms, including bounded network requests and errors. Refresh project intelligence and optional AI cards from one server projection instead of separate client renderers and caches.

## [2026.10.29.post2] - 2026-10-29

### Fixed

- Use the shared refresh lifecycle for System Health, background jobs, Events, service status, assistant activity, webhook configurations and Compliance Progress. Keep the rendered content, show one busy state for the region, and prevent interaction until the request ends.
- Preserve the last data on a failed refresh, restore controls after failure or cancellation, and ignore duplicate refresh calls. Use shared error states with Retry when an initial load fails.
- Remove separate table and health refresh styles. Keep compliance charts visible during reload and reject superseded history responses.

## [2026.10.29.post1] - 2026-10-29

### Fixed

- Keep control shadows and keyboard focus rings behind shared sticky settings headings while scrolling. Preserve section spacing and allow dropdown menus to open above the headings.

## [2026.10.29] - 2026-10-29

### Fixed

- Make table rows passive everywhere: open records through native identity links or shared Actions buttons. Remove row-wide navigation and pressed styling so selecting text and horizontal swipes cannot open a record.
- Add explicit project links and shared View/GitLab actions to group project tables. Preserve student link context during live metric updates and identify group members by their stored ID.
- Reload the server-rendered group table after linking a project instead of constructing a separate list. Remove the unused client-side member table builder.
- Invalidate group and course caches after linking or restoring a project, including its previous group after reassignment. Match initial course-code ordering to the shared table's numeric sort.
- Use shared teacher badges and disclosure buttons in Course Management. Replace unsupported table shortcuts in the tour with the actual link and keyboard behavior.

## [2026.10.28.post7] - 2026-10-28

### Fixed

- Refresh Service status in place through the shared loading and outcome states. Keep the last response on network failure, cancel outgoing requests on navigation and initialize shared table scrolling after replacement.
- Seat Markdown editor tabs on the header divider at every width. Keep membership badges beside their text when space permits and align wrapped badges left.
- Start the Teacher's Checklist chart only after its container is visible; respect reduced motion for chart entrances. Render the initial Week Analytics summary on the server to prevent layout shifts.

## [2026.10.28.post6] - 2026-10-28

### Fixed

- Align wrapped support badges, merge-request and discussion metadata, check actions and issue-chart captions to the left on mobile. Stack User Info membership badges below their content on narrow screens; retain desktop alignment.
- Consolidate mobile alignment rules and remove their narrower duplicates. Replace obsolete build/release commentary with current component contracts and concise implementation notes; preserve tour completion migration and application behavior.

## [2026.10.28.post5] - 2026-10-28

### Fixed

- Give support ticket details one responsive reading order: request, attributes, conversation and reply. Keep attributes on the right on desktop and before the discussion on phones.
- Remove repeated author, course and period metadata, the redundant participant strip and misaligned timestamp icons. Consolidate ticket attributes into one shared Details card; keep mobile reply actions left-aligned and wrapping.
- Update the ticket tour to the current layout and staff permissions; remove its obsolete participant step and inaccurate reopening description.
- Use one loop-owned database engine for email preferences and persistence. Offload support email work from the request event loop; avoid unawaited coroutines and cross-loop asyncpg failures while retaining opt-outs and idempotent delivery.

## [2026.10.28.post4] - 2026-10-28

### Fixed

- Probe GitLab reachability through its public sign-in page instead of requesting the version API without authentication. Healthy page visits no longer generate expected HTTP 401 error traces. Keep authenticated API-token validation and genuine connection/outage errors visible.

## [2026.10.28.post3] - 2026-10-28

### Fixed

- Contain absolute accessibility labels within the shared dashboard scrollport. Long mobile pages no longer leave an empty document below the application panel.
- Render ticket details with shared cards, alerts, form labels and labeled avatars. Omit unanswered optional response fields and remove the replaced page styles.
- Preserve support drafts after failed submissions, prevent live dropdown updates from issuing duplicate writes, and restore the committed selection after a failed update.
- Offer and accept only active human administrators or staff of the ticket's course as assignees. Reject null status, priority and category before database writes.
- Bound Jaeger retention to 10,000 traces and its Go runtime memory target to 384 MiB below the 512 MiB container limit.

## [2026.10.28.post2] - 2026-10-28

### Fixed

- Extend HTTP, webhook-processing and GitLab API duration histograms beyond their 5/10/15-second alert thresholds. Slow requests can now be represented instead of being clipped below an alert's firing condition.
- Retain only raw deleted static assets during deployment. Exclude JS/CSS build sources so retired scripts cannot be recompiled into the new image's manifest.

## [2026.10.28.post1] - 2026-10-28

### Changed

- Remove retired pilot browser tracking, click/time-saving estimates, flag-resolution tracking, their API, worker tasks and four usage tables. Preserve weekly compliance history, activity analytics, support records and LLM analysis.
- Use one support-form service instead of the unused legacy survey API. Bind new tickets to the session author, active course form and course access; require CSRF and honor the support feature switch.
- Add a role-aware Service status page and shared service notices from the existing Prometheus stack. Admins can inspect metrics/alerts and open Grafana, Prometheus, Jaeger and Alertmanager; students and teachers receive service-impact notices without internal details.
- Bound monitoring reads to 1.5 seconds, share results for 20 seconds per process and report unavailable monitoring as unknown. Keep monitoring optional with PROMETHEUS_URL, independently of course tools.
- Consolidate avatar labels, chart legends, badges and responsive header buttons into shared components, remove local restyling, and retain the centered sign-in language selector.

## [2026.10.28] - 2026-10-28

### Fixed

- Save course metadata, scoring settings and staged check edits in one transaction. A stale or invalid check leaves the entire draft unchanged; native forms and enhanced saves use the same validation.
- Preserve configuration for hidden optional modules, including LLM analysis, and interpret an explicitly empty built-in check selection as disabled checks.
- Render compliance rows with shared Jinja components on the first frame and refresh through the same template. Preserve staged edits during table refresh and ignore notifications for the page's own save.
- Use shared badge variants and checkbox/button components instead of course-specific restyling.

## [2026.10.27.post5] - 2026-10-27

### Fixed

- Keep pytest below 9.2 while pytest-benchmark 5.3 depends on the removed private Node._nodeid field. CI installs a compatible pytest version and runs all benchmark tests without a compatibility shim.

## [2026.10.27.post4] - 2026-10-27

### Removed

- Remove unused GitLab product-release, repository-cloning, Elasticsearch and content-generation tooling from the documentation build. Retain and test the navigation generator; its Slovak and English output is unchanged.
- Remove unused Firebase feedback/contact forms, GitLab feature walkthroughs, deprecation pages and archive-version handling. Build only the documentation's actual JavaScript entry points and prune their unused dependencies.
- Documentation search uses Pagefind and names GitPulse rather than fetching a GitLab product version. LLM analysis, activity analytics and compliance history remain available.

## [2026.10.27.post3] - 2026-10-27

### Fixed

- Centre the shared language selector on sign-in and sign-out, including the mobile authentication sheet.
- Course freshness uses a composite snapshot index instead of scanning the snapshot history to find the latest date. The database migration and ORM metadata declare the same index; an integration test verifies the actual PostgreSQL plan and empty-course result.

## [2026.10.27.post2] - 2026-10-27

### Fixed

- The CI unit-test job installs Node.js so JavaScript contract tests execute instead of being skipped or failing because the runtime is missing.
- MR analysis filters use the shared table toolbar so the search and risk dropdown align without custom wrappers or sizing rules. The confidence label uses the standard info badge. Shared select fields reserve their widest option from the server-rendered frame, including dynamically added options, so changing a filter does not resize adjacent controls.

## [2026.10.27.post1] - 2026-10-27

### Changed

- Sign-in language selection uses GitLab's small tertiary listbox on the existing white authentication surface, with no page-specific dropdown styling.
- Reviewer and sync indicators, issue legends and MR risk labels use shared badges. Week and Markdown navigation use shared tabs; diff file navigation uses shared list items. Text actions and the MR risk filter use the common button and select components.
- Removed component restyling in card headers and table controls, the unused header-fit observer, duplicate font-size aliases and dead core helper guards. Visible text and chart labels are at least 12 px. Week selection is server-rendered before page scripts run.

## [2026.10.27] - 2026-10-27

### Changed

- The search palette is built from the shared components: the borderless search box, dropdown group headers, the close button and avatars. Close buttons, avatars, badges, alerts, the person typeahead and the support ticket thread follow the same rule on the server and in the browser, so their page-specific copies and about 2,000 lines of overriding CSS are removed.
- Avatars follow GitLab's GlAvatar: fixed sizes, a per-name identicon colour and the initial under the picture until it loads. Badges, alerts and close buttons follow GlBadge, GlAlert and GitLab's close button; the sign-in alerts are the standard alert.
- Browser code calls the core helpers directly. Hundreds of local copies and dead fallbacks for translation, HTML escaping, toasts and other always-present functions are removed, together with the unused drawer component. Pagination arrows and dropdown checks come from the icon registry.

### Fixed

- Leaving a page runs its cleanup once; the next page no longer repeats the previous page's teardown.
- Pagination buttons carry translated labels from the first frame instead of English until scripts load.
- Project score colours use the course thresholds. Disabled tertiary buttons no longer show a grey fill, and the link hover and focus ring rules no longer override the colour or corner radius of components that are links or buttons.

## [2026.10.26.post12] - 2026-10-26

### Fixed

- Finishing a table search updates its URL without replacing controls during a pointer press. Client pagination commits pending filters inside its click handler, then resolves Next and Previous from the filtered page. Fast clicks remain actionable instead of losing their target during blur.

## [2026.10.26.post11] - 2026-10-26

### Fixed

- Shared table searches commit pending input when editing ends, before Refresh reads the current filters. Quickly refreshing Assistant activity no longer drops the latest query.
- Committing a filter consumes its pending typing update, so the old timer cannot reset a later page selection. Detached inputs and outgoing pages remain unable to overwrite the current search URL.

## [2026.10.26.post10] - 2026-10-26

### Fixed

- Assistant activity uses the shared keyed request transport with a ten-second timeout and no automatic retries. Retired or older responses cannot overwrite another page or a newer snapshot. Updates defer while the reader types or changes the activity view, preserving focus and the current query.
- Delayed Assistant reloads are canceled when leaving their page and recheck unsaved edits when they run. Exercise completion events identifying another course are ignored.
- Shared Refresh controls suppress feedback for superseded, deferred or retired actions, so old requests cannot announce success or failure on the destination page.

## [2026.10.26.post9] - 2026-10-26

### Fixed

- Completing a background process or retry cooldown restores Save from the current form draft. Edits made during a lock become saveable when it ends; reverted or unchanged forms remain disabled, without stale disabled styling or accessibility attributes.
- Loading, process, synchronization, archive and cooldown locks share one button-state restoration path. Finishing one lock cannot enable an action still held by another or prematurely cancel its retry countdown. Settings also recheck their Save guard when server synchronization polling releases its lock.
- Process guards no longer create a separate tooltip instance after unlocking; restored controls use the shared delegated tooltip behavior.

## [2026.10.26.post8] - 2026-10-26

### Fixed

- Shared form guards acknowledge the values submitted to the server and retain later edits as unsaved. Save buttons respect active loading, process, sync, archive and cooldown locks, then re-evaluate remaining edits when loading finishes, including fast responses whose spinner never appeared.
- Preferences restore the last submitted preview on navigation and defer language reloads while a later draft remains. Settings and Assistant save responses belong to their original form; late responses cannot reset a replacement form, open a sync prompt or reload over another draft.
- Native diff-color pickers use the existing derived-field exclusion shared with modal dirty tracking, so reverting a color immediately returns the form to its saved state.

## [2026.10.26.post7] - 2026-10-26

### Fixed

- Shared calendars parse semester dates as local calendar days through Flatpickr instead of UTC timestamps. Teaching and exam weeks keep the same numbering in every browser time zone, including across daylight-saving changes and live edits to a paired start date.
- Empty deadline calendars open in the future semester's actual month. A semester starting on the first day of a month no longer opens in the previous month in time zones west of UTC; opening the calendar leaves the deadline empty.

## [2026.10.26.post6] - 2026-10-26

### Fixed

- Removing a page modal retires its animation, open-stack entry, close guard and dirty-field snapshot before its ID can be reused. Fast SPA arrivals can immediately open the replacement dialog without inheriting the removed dialog's state or leaving the page scroll-locked.
- Modal exit callbacks belong to their original opening and DOM node. A late completion cannot hide or unlock a reopened/replacement dialog or notify its listeners that it closed.
- Removed obsolete per-dialog scale-origin calculations and inline animation overrides. Modal entrances retain the shared translation motion without unnecessary layout reads or inline transform origins.

## [2026.10.26.post5] - 2026-10-26

### Fixed

- Calendars initialise after SPA navigation reconciles the incoming course's semester metadata. Inline fields and teleported deadline dialogs use the new course's week numbers and week-column policy instead of retaining the previous page's context.
- Semester-end calendars resolve their anchor from their own academic-period component, including form-less Transfer dialogs and multiple date pairs in one form. Editing that pair's start date updates its week numbers without using another pair or the source course.

## [2026.10.26.post4] - 2026-10-26

### Fixed

- Failed SPA requests preserve the current page's URL, modals, event handlers and unsaved-change protection. Cleanup and Alpine suspension occur only before a successful content swap; HTTP errors and empty responses cannot create history entries for pages that never arrived.
- Failed Back/Forward navigation restores the rendered page's address. Queued history navigation compares destinations with the rendered page instead of skipping a request whose URL is already in the address bar.
- HTMX removal destroys each date picker through Flatpickr's lifecycle API, releasing its popup and global listeners. Removed an incorrect orphan-calendar sweep that relied on a property Flatpickr does not provide and could detach live calendars.

## [2026.10.26.post3] - 2026-10-26

### Fixed

- Fast calendar selections and number-stepper actions remain unsaved edits while modal fields initialise. Cancel warns before discarding and restores the opening values, including the calendar selection.
- Standard form save guards retain their original baseline after user input, dropdown selections or calendar interactions. Follow-up synthetic events cannot disable Save or silently adopt an unsaved edit; untouched programmatic population still settles normally.

## [2026.10.26.post2] - 2026-10-26

### Fixed

- Shared calendars fit narrow screens without clipping weekdays, hiding semester weeks or enlarging the mobile layout viewport. Resizing back to desktop preserves the standard calendar width.
- Body-mounted calendars follow their input when an ancestor page or modal body scrolls, using Flatpickr's existing positioning helper instead of duplicating its geometry.
- Viewport-width changes close an open calendar without changing its date; reopening clears stale positioning offsets. Height-only changes from an on-screen keyboard keep it open.

## [2026.10.26.post1] - 2026-10-26

### Fixed

- Delayed modal autofocus only applies to the current, open, topmost dialog and preserves an already chosen field. Closed or background dialogs cannot steal focus; confirmation dialogs retain their safe initial control.
- Opening timers and confirmation animation-frame callbacks belong to their original opening. Rapid reopening preserves the new animation state, and a replaced confirmation cannot focus its previous control.

## [2026.10.26] - 2026-10-26

### Fixed

- Modal autofocus and Tab wrapping exclude controls with a negative tabindex, disabled controls (including disabled fieldsets), and inert subtrees. The semester transfer dialog focuses the visible academic-period selector instead of its hidden validator.
- Browser regression checks cover transfer keyboard navigation, inactive controls at both dialog boundaries, and the accessible JSON file picker on desktop, touch and reduced-motion layouts.

## [2026.10.25.post10] - 2026-10-25

### Fixed

- JSON imports immediately invalidate an edited preview and share draft protection, discard, timer cancellation and page cleanup across dashboard, full-course and check configuration imports. Invalid root arrays are rejected.
- File uploads cannot overwrite a newer file or manual edit; discarded imports clear the file chip and pending reads. Reopening a closing dialog starts a fresh dirty-state baseline.

## [2026.10.25.post9] - 2026-10-25

### Fixed

- Responsive tables disable native horizontal edge bounce/stretch instead of allowing it with `overscroll-behavior-x: contain`. Vertical scrolling retains its default behavior.
- Native touch regression checks now reverse one continuous contact and drag beyond both horizontal edges, across five mobile widths, both themes and reduced-motion settings.

## [2026.10.25.post8] - 2026-10-25

### Fixed

- Removed `will-change: transform` from touch sticky Actions cells. Chrome retains native compositor sticky constraints during horizontal panning.
- Touch regression checks cover the reported Pixel 9 Pro viewport (427 by 952) and verify native sticky constraints for every pinned Actions cell, alongside scroll geometry and pinning state.

## [2026.10.25.post7] - 2026-10-25

### Fixed

- Tooltips are destroyed when their reference leaves the document after a page swap or row replacement. Open, hidden and pending instances release their popups and handlers; moving a live reference preserves its instance.
- Card explanations use the same current-content and one-open-tooltip rules as delegated tooltips. Removed an unreachable info-tip branch from the ordinary tooltip handler.
- Tooltip cleanup checks created instances without scanning every possible target or eagerly creating ordinary tooltips.
- Horizontal scrolling no longer remeasures or switches the Actions pinning mode on every scroll event. Geometry changes still update pinning through resize observation, including changes to the Actions header width.
- Overflowing pinned Actions cells use separate compositor layers on touch devices. Removed unused mobile scroll snapping; the themed separator still fades at the right edge.

## [2026.10.25.post6] - 2026-10-25

### Fixed

- Course, group, project and student job refreshes share scope matching. Unrelated completions no longer request live data or invalidate project GitLab caches; actual course/group scopes take precedence over the originating project.
- Project detail uses one job-completion listener. Relevant analysis completions from another tab refresh result cards, while hidden pages defer their refresh.
- Analysis jobs carry course/group/project metadata. Stored job metadata, legacy course keys and existing analysis polling URLs remain supported.
- Narrow top bars keep the clock and avatar visible in both time formats. The academic year and separator yield space first.


## [2026.10.25.post5] - 2026-10-25

### Fixed

- Group sync, project sync and group check responses report the persisted enqueue error instead of claiming that a failed job was queued.
- Course check launches clear per-group recomputing indicators when queueing fails or no work is accepted, independently of live-data refresh.
- Course checks revalidate the process scope after the confirmation dialog, preventing a redundant launch when another run starts while the dialog is open.

## [2026.10.25.post4] - 2026-10-25

### Fixed

- Student Run Checks uses the shared group process lifecycle: enqueue failures retire the progress indicator, cancelled jobs report an error, and a disconnected progress stream falls back to status polling.
- The check picker and progress message on student and project pages show the group actually recomputed by the API, rather than suggesting a narrower scope.
- Student profiles refresh only after successful jobs in their group or course. Unrelated and failed jobs no longer reload the page; bursts of completion events share one refresh.

## [2026.10.25.post3] - 2026-10-25

### Fixed

- Run Compliance Checks protects early bulk selection changes. Transient check filtering does not count as unsaved work and resets on reopening.
- The selected-check counter and Run button use the whole selection, matching the request payload even when some selected checks are hidden by the filter. Refreshing the selection preserves archived, process, loading and cooldown locks.
- An intentional check run accepts its selected parameters before closing the modal. It no longer sends the request while showing a second Discard prompt. The unused run-success listener was removed.

## [2026.10.25.post2] - 2026-10-25

### Fixed

- Escape acts only on the top dialog. The key that opens a discard confirmation no longer immediately dismisses that confirmation, and Tab stays inside it.
- Confirmed navigation closes outgoing dialogs without asking for the same discarded changes a second time.
- Closing a changed GitLab import draft asks before discarding it. Cancel, the close button, Escape and the backdrop use the same guard, and leaving the page protects the draft too. Starting the import keeps its separate process cancellation behavior.
- Confirming Discard restores the opening form values, including custom selects, checkboxes, derived academic-period fields and date pickers, instead of retaining a discarded draft on reopening. A late confirmation cannot discard a newer opening.
- Import progress uses shared modal lifecycle events instead of replacing openModal/closeModal, preserving opener animations, close-guard results and lifecycle behavior for both GP and window callers.

## [2026.10.25.post1] - 2026-10-25

### Fixed

- Debounced table searches stop when their input or table is detached or its page is being left. A fast navigation can no longer copy the outgoing search into the destination URL.
- Users, Course Teachers and Assistant activity configure the shared TableFilter with their row predicate and URL parameters instead of replacing apply() with page-specific implementations. Search, pagination, empty states and URL updates follow one implementation.
- Table filtering retains the current URL fragment and history state, including when switching the Users role tabs or searching the user list.

## [2026.10.25] - 2026-10-25

### Fixed

- Table refreshes dismiss open tooltips before replacing their rows, preventing orphaned explanations over empty results.
- Event details keep the selected event when an older payload request finishes later. Closing or reopening the dialog prevents late successes and failures from replacing its current contents.
- Leaving Events cancels its reads and invalidates delayed table renders. Returning to the page cannot receive a previous visit's event rows or dead-letter counters.
- Event-table and empty-payload states use the shared themed illustrations. Keyed API reads remove their caller's abort listener after completion instead of retaining every completed request until the page closes.

## [2026.10.24.post9] - 2026-10-24

### Fixed

- Shared dropdowns support arrow keys, Home/End, Tab and Escape, including menus portaled outside scrolling tables. Disabled options are skipped and existing button/link actions remain responsible for selection.
- Escape finds the actual open dropdown instead of a preceding closed data-dropdown element. It dismisses the menu before its containing dialog; Tab returns a portaled menu to its original container and continues normal focus navigation.
- Changing rows per page restores focus to the replacement dropdown button after pagination controls rerender, preserving keyboard operation across repeated size changes.

## [2026.10.24.post8] - 2026-10-24

### Fixed

- Shared modal forms capture their payload before temporarily disabling editable fields and custom select controls. Users can still cancel or close the dialog, but cannot change values while a pending save's callback expects the submitted form state.
- Errors restore editing without enabling fields that were already disabled. Reopening immediately releases the previous interaction's fields; an older completion cannot unlock a newer save. Modal Save guards recognize a pending submission before its delayed spinner appears.
- A modal save failure already reported to the user no longer escapes as an unhandled promise rejection. The error callback and visible message remain available for recovery and retry.

## [2026.10.24.post7] - 2026-10-24

### Fixed

- Delayed modal form responses cannot close a newly opened dialog, update another user's row or show stale success/error feedback after navigation. The shared submit handler checks the original form and dialog opening before applying the response.
- Reopening a form clears its previous loading and result feedback. A new interaction can submit independently while the earlier write finishes; that write cannot reset the new submit button.

## [2026.10.24.post6] - 2026-10-24

### Fixed

- Filtering a table no longer measures Actions from a hidden first row as zero pixels. The shared scroll component uses the visible column header, preserving room for row information on narrow screens.
- HTMX swaps initialize table and navigation-strip roots as well as their descendants. Replacing a table viewport or its inner table reconnects scroll and resize tracking to the current nodes and disconnects the previous binding.
- Horizontal scroll indicators and the sticky Actions separator keep updating after fragment replacements, including swaps inside an existing table wrapper.

## [2026.10.24.post5] - 2026-10-24

### Fixed

- Users table refreshes update Edit with the displayed role and active status, so reopening the form no longer restores stale values after another administrator's change.
- Saving a service account preserves its Bot badge and account type when Edit is reopened. Live refresh and save now share one row-state update path instead of updating the visible row and action payload separately.
- Modal Save guards share the unsaved-changes baseline instead of taking their own snapshots during entrance animations and settling timers. Fast checkbox and dropdown edits stay saveable; reverting them disables Save again.
- Modal dirty checks exclude the custom dropdown's asynchronous validation mirror. Restoring a course field to its original value no longer leaves Save enabled or prompts to discard an unchanged form.

## [2026.10.24.post4] - 2026-10-24

### Fixed

- Sticky Actions columns share a theme-colored separator at their left edge while columns scroll beneath them. It fades out at the right scroll end and back in when hidden columns remain, without affecting button positions or click targets. Unpinned and non-overflowing tables stay clear; reduced motion uses the shared policy.
- Deployment loads updated recovery settings into an existing Caddy before replacing the API. Previously a startup retry-window change was applied only after the startup gap it was intended to cover. A failed early reload stops API replacement.

## [2026.10.24.post3] - 2026-10-24

### Fixed

- Production images compile dependency and standard-library bytecode during the build. New read-only API and background processes reuse it instead of recompiling hundreds of modules on every start. Dependency and standard-library layers remain independent of release metadata.
- Gunicorn disables its unused control socket, removing the attempt to create `/app/.gunicorn` on the read-only filesystem. Container signals continue to control deployment and shutdown.
- Caddy's bounded upstream retry window now covers the API's 20-second startup period; the previous 15-second window could return 503 just before a slow startup completed.
- Documented image bytecode preparation, read-only startup and the distinction between startup, proxy retry time and warm route execution.

## [2026.10.24.post2] - 2026-10-24

### Fixed

- Both User Info dialogs release pending reads when closed and immediately load another selected person. Duplicate clicks on the same pending profile still share one read; late responses cannot overwrite the current profile.
- Closing during the shared renderer download no longer starts an obsolete profile request. Profile reads use the shared timeout and navigation cancellation rather than a separate fetch implementation.
- User enrichment refreshes only the profile that remains open. Its delayed refresh cannot reopen a dismissed dialog, replace another selected person or act after navigation.
- User table refreshes retain ownership of their original table and ignore outdated responses, including after leaving and returning to Users. Updated names, emails and roles immediately obey the active search and role filter. Desktop and touch-browser regressions cover these request races.

## [2026.10.24.post1] - 2026-10-24

### Fixed

- Background workers wait for API readiness during Compose startup, preventing four concurrent RQ imports from competing with API initialization on the same host. Existing workers remain independent of subsequent API health changes.
- API container health now checks database/Redis/session readiness rather than liveness. Startup checks run every second for the first 20 seconds, then return to the normal 15-second interval.
- Page transition copies retain unique identities for dropdown buttons and other labelable controls. Labels remain associated with their copied control, fixing Chrome form-label warnings when leaving Preferences and Assistant.
- Documented the startup gate, its host-reboot limitation, and measurement of cold responses separately from route execution and warm requests.

## [2026.10.23.post11] - 2026-10-23

### Fixed

- Course Analytics now shares one current student cohort across the checklist, weekly trends and fallback history. Inactive memberships, inactive teams and manually excluded students no longer leave stale results in aggregates; archived courses retain their final reports.
- Simultaneous snapshots from two teams count a student once in the checklist, preventing percentages above 100% and duplicate at-risk counts.
- At-risk classification respects each student's expected built-in and custom checks, rather than penalising checks introduced later for other students. Regression tests exercise real SQL, exclusion/restoration and multiple memberships.

## [2026.10.23.post10] - 2026-10-23

### Fixed

- Course Analytics excludes teachers and mentors through membership in the requested course. A staff role in another course no longer removes a student's scores, and the exclusion subquery no longer rescans snapshot history.
- Added course/student/date and covering course/week indexes for latest-checklist and weekly-trend queries. Cache misses can read small indexes instead of fetching history heap pages; model metadata and Alembic migration 025 stay aligned.
- Added executable regression cases for teacher and mentor roles across courses, and documented the query plans and distinction between cold requests and page-cache hits.

## [2026.10.23.post9] - 2026-10-23

### Fixed

- Escape closes an open calendar before its parent dialog. Visible toast text no longer blocks modal fields or Save; toast close buttons and actions remain interactive.
- Project member actions remain available on phones. Removed a page rule that hid the entire Actions column and global project-page button margins that changed shared action gaps from 4 px to 12 px.
- Weekly deadline editing synchronises Flatpickr's selected dates, visible month and input values, and clears dates for another or new week. Initial and regenerated rows use the same action variants, badges and archived-course locks; archived Add week is disabled in server-rendered HTML.
- Removed custom priority badge borders, weights and padding, duplicate responsive badge metrics, obsolete course-header layout overrides and redundant badge classes. Analysis error dismissal uses the secondary button variant consistently.
- GitLab status polling reads a cached HTTP 200 connectivity report and handles its actual status. Outages still drive the existing banner/recovery flow; the monitoring probe retains HTTP 503. Poll timeouts are cleared on failure as well as success. Documented the status report and added endpoint and browser regressions.

## [2026.10.23.post8] - 2026-10-23

### Fixed

- Background Jobs aligns row actions with the Actions header and uses standard table spacing. Completed and active jobs share the same action layout, including refreshes and narrow screens.
- Archived Courses uses the shared card and table typography, padding and corners. Removed dashboard-specific uppercase headers, muted colors and flush-body overrides.
- Courses, groups, projects and webhooks use the existing shared row-actions component. Removed duplicate page rules and inline alignment; the component owns gaps without adding legacy button margins. Browser regression coverage checks desktop fixed/fluid layouts, touch screens and both themes.

## [2026.10.23.post7] - 2026-10-23

### Fixed

- Cold restart: Caddy checks API liveness every second instead of retaining a failed startup probe for up to another fifteen seconds. First public requests can resume promptly after startup instead of exhausting the retry window with 502 responses.
- The production API preloads its application through Gunicorn before forking four Uvicorn workers. Routers and models are imported once; database/Redis pools and asynchronous warm-up still initialise separately in each worker's lifespan. Keep-alive remains five seconds, longer than Caddy's four-second idle reuse.
- Documented the distinction between first-request cold-start measurements and requests made after readiness checks. Validated the actual Linux process model, multiprocess metrics and browser flows before deployment.

## [2026.10.23.post6] - 2026-10-23

### Fixed

- Shared tabs reserve the selected label's width, keeping table search fields and neighbouring filters in place when selection changes. The same sizing applies to course navigation.
- Added stable identifiers to generated job/event/check/suggestion selections, ticket and course-transfer checkboxes, and preference color pickers. Temporary attachment and clipboard fields are named too.
- Transition covers give copied controls separate identifiers and reconnect their labels, preventing anonymous or duplicate fields during navigation while keeping the copy inert.
- Analytics loads only check outcomes and their details from the latest snapshots, avoiding unused diagnostic counters and arrays. Browser coverage verifies chart rendering, form identities and filter geometry on phones and fixed/fluid desktop layouts.

## [2026.10.23.post5] - 2026-10-23

### Fixed

- Expanded job rows use the shared table-details component, with left-aligned labels, normal typography and precise local timestamps. Short results appear once; long messages remain readable in the details.
- Sticky action columns and their width detection exclude spanning cells, preventing expanded details and empty states from inheriting action alignment or pinning. Detail content fits the visible table width on phones.
- Removed System-specific detail grids, backgrounds, code panels, padding overrides and row-click handlers. The shared disclosure supports keyboard input and remains independent of checkbox selection.

## [2026.10.23.post4] - 2026-10-23

### Changed

- System focuses on service health, actual RQ queues and workers, background jobs and deployment configuration. User-role analytics and user-action audit rows are no longer duplicated here; monitoring tools are linked when deployed.
- Background jobs use database pagination and filtered totals, support every status, preserve newest-first ordering and expose keyboard-accessible details. Cleanup removes terminal jobs only and retains active jobs and the activity audit.

### Fixed

- Compliance charts normalize modern CSS colors through the browser, use shared alpha handling, repaint their gradients when the theme changes and destroy charts and listeners on navigation.
- Empty assistant activity keeps the shared table, filters and pagination. Project folder icons use the shared icon size without custom colored tiles.
- SSE uses the same upstream restart retries as normal requests. Proxy connections expire before Uvicorn's idle timeout, and disconnected clients release streams. Reconnect attempts back off and short-lived greetings do not reset the failure budget; student detail uses the shared client.
- Cache clearing reports server failures and preserves sessions, job locks and rate limits. System health reports degraded external dependencies instead of claiming that every service is operational.

## [2026.10.23.post3] - 2026-10-23

### Fixed

- System Job History reads only the archived-course fields it displays and does not eagerly load course settings or other relationships. The operations payload is unchanged.
- Database health and readiness timeouts cover connection-pool acquisition and connection establishment as well as query execution, preventing exhausted pools from extending the probe beyond its limit.
- Regression tests verify cancellation during both connection acquisition and query execution for health and readiness probes.

## [2026.10.23.post2] - 2026-10-23

### Fixed

- Docker builds Jinja and application Python bytecode once, so API processes reuse it after restarts instead of compiling the same templates while serving requests.
- Every API process completes template and ORM warm-up before accepting requests. The database warm-up has a five-second limit so an unavailable database cannot hold startup indefinitely; readiness still checks the database.
- Image template bytecode is readable by the unprivileged runtime user and lives outside the host-mounted templates directory. Changed, missing or invalid cache entries fall back to source compilation without writes on the read-only filesystem.
- Regression checks cover fresh-process cache reuse, source invalidation, escaping, cache misses, bounded database warm-up and the startup barrier.

## [2026.10.23.post1] - 2026-10-23

### Fixed

- Deep links reveal every enclosing native disclosure and shared Alpine `glCollapse` component, keeping their reactive state and expanded controls synchronized.
- Scrolling waits for disclosure height transitions to finish and follows the newest target when another link is selected during opening. Closing a parent or leaving the page cancels the pending scroll.
- Re-selecting the current fragment reopens a collapsed destination without adding a duplicate history entry. Named anchors share the same reveal behavior.
- Deferred SPA pages resolve their navigation target after Alpine initialization. Hidden destinations no longer trigger an initial jump to an empty position.
- Browser fallback checks match cache-busted GSAP URLs and assert the library is absent, so modal, select and page-arrival fallback paths are actually exercised.

## [2026.10.23] - 2026-10-23

### Fixed

- Back and Forward between fragments of the current page preserve the form, its unsaved edits and its loaded content instead of fetching a replacement or asking to leave.
- Fragment links with a full URL share the local scrolling component, including after client-side query changes. Modified clicks, downloads and links targeting another window retain their browser behavior.
- Client-side history writes keep the navigation guard's current address synchronized. Cancelling Back restores the full query and fragment, while Back to a different filter still loads it.
- Cross-page fragments use the same decoded ID and named-anchor lookup and scroll only the content pane.
- Destination highlighting no longer recentres a real fragment anchor or repeats when another lazy region settles.
- Delayed anchor lookups stop when navigating away or choosing another fragment. Missing anchors no longer reset the scroll position of a later page.

## [2026.10.22.post10] - 2026-10-22

### Fixed

- Shared sticky save bars leave a small gap before a following card without adding empty space below a final save bar.
- In-app navigation preserves the outgoing frame while incoming scripts and Alpine initialize, then fades the inert cover away over the ready page using the shared motion duration.
- Full-document redirects and reloads use a short browser transition that retains the old frame until the incoming first-frame gate opens. Reduced motion disables the transition.
- Browser regressions cover delayed scripts, transition completion, reduced motion, missing GSAP, and save-bar spacing on fixed desktop and narrow layouts.

## [2026.10.22.post9] - 2026-10-22

### Fixed

- HTTP client errors no longer enter the network retry path. Transient statuses and real network failures retain bounded retries; explicitly allowing mutation retries still respects the status policy.
- Cancelled requests wrap read-only browser exceptions so translated or caller-provided messages are preserved. Custom abort reasons are treated as cancellation without retrying.
- A single delegated page-size handler follows the clicked menu's paginator, including portaled menus, instead of changing other tables or retaining document listeners for old SPA pages.
- Pagination refreshes return an open page-size menu from its portal before replacing controls, preventing floating orphan menus.

## [2026.10.22.post8] - 2026-10-22

### Fixed

- Escape dismisses an open form select before its containing dialog. Arrow keys, Home and End navigate options; Tab leaves the control without keeping focus in the hidden menu.
- Server-rendered and dynamically loaded options share selected styling and accessible selection state, including numeric values and externally assigned archived values. Adding options removes the empty placeholder.
- Selecting an option returns focus to its toggle, and closing a dialog resets its open selects before the next visit. Closed menus become inert while their exit animation finishes.
- A custom-select choice made during modal opening remains an unsaved edit after delayed initialization, including keyboard activation.
- Remove the form-select nowrap override so the shared dropdown wraps long course names and unbroken labels within the menu on mobile.
- Browser regressions cover desktop and narrow layouts, reduced motion, missing GSAP and dialog reopening, alongside the existing modal and tour checks.

## [2026.10.22.post7] - 2026-10-22

### Security

- Require OpenTelemetry API 1.45.1 or newer and refresh the matching SDK, exporters and instrumentation in the lockfile. This fixes CVE-2026-114603 / GHSA-xcq7-p3pf-p88h, excessive CPU consumption while parsing malformed inbound `tracestate` headers.
- Add regression coverage for preserving valid trace state while rejecting oversized headers before parsing.

## [2026.10.22.post6] - 2026-10-22

### Fixed

- Modal entrance cleanup no longer replaces the unsaved-change baseline with text entered during opening. Both delayed initialization snapshots preserve trusted edits.
- Mobile swipes check unsaved-change guards before moving a sheet off-screen. A vetoed close settles back smoothly, and gestures target the dialog actually touched instead of a lower dialog in DOM order.
- Swiping or programmatically closing a confirmation resolves its pending answer as cancellation. Confirming still returns success under reduced motion and without GSAP.
- Tab and Shift+Tab stay inside a modal when its container initially has focus, instead of moving to the page underneath it.
- The question-mark key opens keyboard help with or without Shift. Ctrl+S recognizes shared guarded forms, including Preferences, and avoids submitting a background form while a dialog is open.

## [2026.10.22.post5] - 2026-10-22

### Fixed

- Next and Back resize tour cards at their fixed anchor, keeping navigation buttons still when descriptions change length. The shared motion component interpolates height and position together without scaling text or briefly exposing scrollbars.
- Tour cards slide between top and bottom placements on tablets and landscape phones instead of jumping. Closing during a placement transition continues from the visible position without a pixel-to-percentage jump. First appearance, reverse exit and highlight timing remain intact, including reduced-motion and missing-GSAP fallbacks.
- Added browser regression coverage for action positioning during Next and Back on desktop, phone, tablet and landscape layouts.

## [2026.10.22.post4] - 2026-10-22

### Fixed

- The teacher profile menu no longer links to the administrator-only System page. Student compliance alerts open the course instead of restricted settings. Routine tour and team stream diagnostics require debug mode.
- Profiles, staff lists, user cards and assistant activity use stored avatar URLs; missing photographs show initials instead of fetching invented GitLab upload paths.
- Page startup reads public preference cookies from escaped server-rendered data. Consent, language and theme writes use Cookie Store where supported, retaining the standard fallback. Dashboard and auth pages share the same cookie implementation instead of separate copies.
- The offline shell receives a matching CSP nonce for its theme bootstrap, so cached offline navigation can apply the theme without a blocked-script warning.

## [2026.10.22.post3] - 2026-10-22

### Fixed

- Shared tour gestures no longer try to cancel non-cancelable touch events. Mobile modal dragging yields when the browser owns scrolling, preventing touch intervention warnings throughout the application.
- PWA installation keeps the browser's native promotion available while retaining the in-app Install button. A native prompt result clears the saved event and hides the card, avoiding stale install controls and the suppressed-banner message.

## [2026.10.22.post2] - 2026-10-22

### Fixed

- The tour close control uses the compact transparent button component instead of a large filled square, while retaining its larger touch target on phones.

## [2026.10.22.post1] - 2026-10-22

### Fixed

- Mobile pages no longer count browser toolbar height as bottom padding. Settings actions count the safe area once, and the shared settings form keeps sections compact on phones.
- Table stripes, hover, press, selection and navigation feedback now have one owner and use theme accent tokens. Pinned actions inherit the same opaque row background; group children and expanded jobs no longer override it.
- Tours use measured card height to keep targets visible. Mobile cards slide in and out, highlights follow the moving sidebar, and closing folds the highlight while dismissing the card and drawer together. Tour and tree-disclosure buttons reuse the shared button component; theme segments and selected files follow the shared selection and focus tokens.

## [2026.10.21.post5] - 2026-10-21

### Changed

- Monitoring opens with the GitPulse sign-in. Grafana, Prometheus, Jaeger and Alertmanager asked for a Basic Auth password of their own, one shared by all four; now a signed-in GitPulse administrator walks straight in and nobody else does. Caddy asks the application before each request (`/internal/monitoring-authz`, as for the documentation): an administrator is served, a reader without a session is sent to sign in and back to the same page, any other role gets a page saying who may open it. Grafana signs the administrator in under their GitPulse login (its auth proxy; Admin of the main org), and a client cannot name itself - Caddy overwrites the header. Unlike the documentation the gate fails closed. Checked end to end through Caddy with Grafana 11.1: anonymous, a spoofed header, a teacher and an administrator.

## [2026.10.21.post4] - 2026-10-21

### Fixed

- The alert email reads like GitPulse's other mail. It was Alertmanager's default: raw labels (`alertname=... component=...`), a "View in Alertmanager" button to `http://alertmanager:9093` and a "Source" link to the Prometheus container, neither of which opens from a mailbox. Now it is the application's mail chrome with GitLab's pipeline status bar - red with a cross while an alert fires, green with a check once it is resolved - the summary as its headline, a table of what happened, the alert, its severity, the label that matters (a queue, an event type) and the times in Bratislava time, and links that work: the alert's query in Prometheus, all alerts, the dashboard and a Silence link. The subject is the summary: `Firing: RQ jobs are failing (10 in the last hour) | GitPulse`.
- Alertmanager is reachable at `/alertmanager/`, behind the monitoring password, for that Silence link; Prometheus and Alertmanager know their public addresses, so the links an alert carries are absolute.

## [2026.10.21.post3] - 2026-10-21

### Fixed

- Alerts reach the inbox: Alertmanager reads the SMTP password without its whitespace, as the application does (`config.py`). Google shows an app password in groups of four, and Gmail answered the spaced form with a bare `535 Username and Password not accepted` - the first test alert on production was refused that way.

## [2026.10.21.post2] - 2026-10-21

### Fixed

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

## [2026.10.21.post1] - 2026-10-21

### Fixed

- **Security:** `certifi` 2026.6.17 -> 2026.10.19 (PYSEC-2026-4320 / GHSA-6q48-6c7w-9gw2: the bundled CA store trusted `emSign ECC Root CA - G3`, whose intermediates' private keys were compromised and revoked), which un-breaks the `dependency-scan` CI job. `exclude-newer` moved to 2026-10-20 12:00 UTC so uv can see the fix (uploaded 2026-10-20 02:24 UTC); certifi is the only pin that moved.

## [2026.10.21] - 2026-10-21

### Fixed

- An in-app navigation shows the incoming page once it is finished, as a full load does. The page's scripts - which paint its rows, charts and counts - were loaded only after the new content was already on screen, so Admin > Events showed its table 39px tall with every column at its header's width for a few frames before the rows landed and it opened out to full size with other column widths; longest on the first visit, before the page script was cached. The swapped content stays laid out but unpainted until the scripts and Alpine are done (3 s safety net); a filter or sort that stays on the page keeps its controls on screen.
- Dashboard: the courses header's Import, Import JSON and New course no longer run out of their row at 1024-1280px (New course lay 101px over the Quick access card); the three are one group that wraps under the search together.
- Users: every column is at least as wide as its own label in both languages, so the header row is one line (36px) - "Používateľské meno" wrapped and made it 56px tall.
- Admin > System, Job History: the "Enqueued" header is no longer cut ("Zaradené do fronty" needs 180px, the column had 142px).
- A table header holding a select-all checkbox (Job History, Events) is 36px like every other, not 39px: the checkbox sits on the middle of the line, not on its baseline.
- The content security policy names GitLab's origin with its port, so a GitLab on a port of its own (https://git.example:8443) gets its avatars and API calls through, and it allows GitLab's default avatars on both gravatar hosts.

### Tests

- The browser scenarios run clean (53 of 53): the two that change the e2e admin's preferences put them back (a collapsed sidebar left behind was most of four walks' findings), the per-page menu test closes the first-visit tour card that covers the selector, and three tests follow the current design (people's names wrap in the users table, card bodies are padded, a page ending in a sticky save bar has no footer).

## [2026.10.20.post3] - 2026-10-20

### Fixed

- The Assistant activity card's Refresh goes through the states every Refresh does - working, "Done", back - as on Job History. The redraw replaced the whole card, the header too, so the working button was swapped for a fresh idle one at once and no state was ever seen; only the card's body is redrawn now.
- Saving the assistant's tools (and connecting or replacing the bot) shows "Done" on the button before the page comes back, as Settings' Save does. The success toast was handed to the next page only and the page reloaded at once, so the button never reported its own end; the toast is raised on the page now and carried over by the reload.
- On a development server the fonts are cached as in production (one year, immutable). Revalidated on every page load, GitLab Sans sometimes arrived after `font-display: optional` had given up on it: that page stayed in the system font and the next one did not, so the search box's text (and every other) jumped between pages - 113.8 px wide in GitLab Sans, 104.2 px and 1 px higher in Segoe UI.

## [2026.10.20.post2] - 2026-10-20

### Changed

- Prepare exercise runs as a background job, like a sync: the top bar follows it from the queue to its end, a toast says when it is done, and the Assistant page then shows the result by itself - no more "reload the page in a moment". With unsaved tool settings on the page, only the activity card is redrawn, so the edit is not lost. A run that cannot start (the course archived, the bot gone, its token refused since the click) fails at once and says why, instead of "Preparing" for a quarter of an hour. Every run is one row in Admin -> System's Job History ("Assistant exercise"), with its duration.
- The Assistant activity card keeps itself current: the course's live stream redraws it when the bot acts in GitLab, and a Refresh button in its header reloads it, as on Job History and Webhooks. The group has a column of its own (sortable, searchable) instead of wrapping under the username, and an empty card shows the small empty state every empty list shows, not the page-sized one.
- The Assistant page also warns about a webhook that has received nothing from GitLab for 48 hours, the Events page's second case, not only about a missing one.
- Every chart enters the same way as Admin -> System's role chart: its first draw waits until it is on screen, bars grow over 900 ms each 80 ms after the one before, a ring sweeps round in 900 ms. Analytics' compliance ring and weekly chart used to animate while still below the fold and were seen standing still; the five hand-written copies of "draw when visible" (System, Analytics, the student detail, the project detail) are one function, `GP.drawOnEntry`.

### Fixed

- An avatar that failed before the page script was listening (a quick 404, a source the image policy refuses) showed a broken picture and its alt text for eight seconds after it scrolled in, on every page with avatars; it now shows the initials at once.
- The course role badge in every course page's header ("Teacher", "Course Owner") and the user role badge were English in the first frame and translated a moment later; they are translated on the server.

## [2026.10.20.post1] - 2026-10-20

### Fixed

- The classroom assistant is for whoever runs the course: its tab, its page and its four actions are open to the course's owner and teachers and to admins, not to a teacher who sees the course only as a team's mentor (such a teacher used to get the tab and the page, the bot token form included). Its items in **Items that need your attention** and its rows in **Follow the latest updates** follow the same rule.
- Check R08 no longer counts a bot account's comments as review threads the author has to answer. The assistant writes "approved - merge it" after its review, so every exercise merge request was left with a thread nobody is meant to answer and R08 failed for students who did everything right; a CI bot's report counted the same way. R06's hint still counts those comments among the ones that are no team member's.
- Admin -> System's Job History names the assistant's operations as the dashboard feed does ("Assistant tools updated", translated, instead of an untranslated "Assistant tools saved").

### Documentation

- The privacy statement says what the assistant writes to the teams' projects and under which account; the student FAQ says who the bot commenting on commits is; the assistant guide and the R08 description say who controls the assistant and that a bot's comments need no reply.

## [2026.10.20] - 2026-10-20

### Changed

- The assistant is part of the dashboard: **Items that need your attention** say what its page says at the top (a token GitLab refuses or that has expired, tools on without a bot, a token about to expire, an exercise run that never finished; one function, `account.problems()`, answers both) and count the actions GitLab refused it in the last 7 days; **Follow the latest updates** names its actions (bot connected or disconnected, tools updated, exercise prepared, token refused) and links them to the Assistant page, with none of them shown to students. A refused token is written to the audit log once.
- The course configuration file (export / import) carries the assistant's tool settings in an `assistant` section, never the bot or its token; the import checks them as the tools form does, and skips them while the assistant is switched off, as its preview now says.
- The Assistant page says that a course has no webhook the way the Events page says it: a warning toast raised once when the page opens, not a block in the page (none on an archived course, whose webhooks are dropped by design).
- Nothing on the Assistant page is said twice: an expired token is announced by the alert at the top only (the card no longer adds a "Token expired" badge), the course's default branch rule is no longer printed in two cards (as in the exercise's issue, only a stricter rule is named), and the activity card is "Assistant activity", not "Activity" like the course tab next to it.
- The tour prompt counts its steps as "Steps: 4", grammatical in Slovak for every number ("4 krokov" was wrong).
- `scripts/assistant_e2e.py accounts` prints logins for trying the assistant by hand on the local GitLab: the teacher's and the students' GitLab passwords and the GitPulse dev login.

## [2026.10.19.post10] - 2026-10-19

### Fixed

- A course's webhook configuration (the only secret the Settings page issues) authenticates the course's imported projects. Every imported project carries a secret of its own that nobody ever sees, and the receiver stopped at it, so every delivery from an imported project was refused with 401. The project's own secret is still tried first, and a token that matches nothing is still refused.
- Merge request webhooks from GitLab are received. A merge request event's `object_attributes.source` is the source project, not a word, and the schema refused every one with 422; merge requests reached GitPulse only through sync. The hand-written contract fixture had no such field.
- A pipeline webhook outside a merge request (`"merge_request": null`) no longer crashes the processor.
- The classroom assistant, run end to end against GitLab CE 19.4.2: a branch created in GitLab with no commits is not commented on (the comment landed on main's last commit) - its first commits are greeted and its name judged then; GitLab's push of a merged merge request to main is not called a direct push; the issue says what the review will also ask for (the course's description sections, a stricter branch rule) and who merges; the review waits while GitLab still checks whether the merge request can merge, so it never approves a conflict; a comment the review already answered is not answered twice; a member excluded from scoring gets no issue and no comments; a quoted line in a conflict comment no longer ends in a second full stop.

### Added

- The Assistant page has a guided tour like every other course tab, Cancel next to Save as on the Settings page, and a note that the exercise's issues and merge requests count in R01-R13; a team name in the activity table no longer breaks across lines.
- `scripts/assistant_e2e.py` with `docker-compose.gitlab-e2e.yml` runs the assistant end to end against a real GitLab CE 19.4.2 (56 checks). The deliveries such a run captured are contract fixtures in `tests/fixtures/payloads/gitlab_19_4/`.

## [2026.10.19.post9] - 2026-10-19

### Fixed

- Tour highlights fold vertically closed over 400 ms, reversing the first-step reveal when closing the tour or returning to a centred step. Close, Escape and mobile swipe share the same exit; closing during a reveal continues from the visible shape, and repeated Escape no longer interrupts the animation.

## [2026.10.19.post8] - 2026-10-19

### Fixed

- The first guided-tour highlight now opens vertically at the target over 400 ms instead of appearing instantly or growing from a point at the viewport centre. This also covers tours without an introduction and returning from a centred step. Animation starts after Driver.js measures the target; the stable-DOM refresh no longer restarts an already valid step or reopens a closed tour.

## [2026.10.19.post7] - 2026-10-19

### Fixed

- Tour highlights retain their 400 ms transition when Next or Back scrolls to another element. The shared motion module interpolates towards Driver.js' live target without scroll refreshes replacing the visible highlight. Cards also start from their previous visible position when the next description has a different height. Reduced motion, interrupted steps and solid introduction/closing backdrops remain supported.

## [2026.10.19.post6] - 2026-10-19

### Added

- The classroom assistant is on in production (`redeploy.py` sets `FEATURE_CLASSROOM_ASSISTANT=true`; `docker-compose.yml` now passes the flag to the API and the workers, which it did not). Each course still connects its own bot and switches its tools on.
- The assistant follows the course's own rules: with R02 on, a new branch and a merge request's branch are checked against the course's branch-naming rule; with R05 on, the review asks for the required description sections. A check the course switched off is never asked for. The review also reports a failed pipeline.
- A course chooses the language its assistant writes in (Slovak or English): comments, issues and the colleague's line.
- A course transferred to a new semester keeps its assistant's tool settings; the bot token stays with the old course.

### Fixed

- A merge request closed without merging no longer holds its issue: the next merge request for it is reviewed from the start.
- A bot token that expired or that GitLab refuses (confirmed with `GET /user`, since GitLab also answers 401 to a repeated approval) stops the assistant instead of failing every event; the Assistant page says so at the top and asks for a new token.
- The Assistant page says what keeps the assistant from acting: no course webhook, tools on without a bot, an unusable token. A waiting conflict task says what it waits for; "Prepare exercise" shows its run while it is in progress, refuses a second one, and counts students who have no GitLab account in GitPulse yet.

## [2026.10.19.post5] - 2026-10-19

### Fixed

- Mobile search reveals a fixed-size panel using clipping and translation instead of resizing its layout each frame. The backdrop uses its own opacity layer, the transition starts after preparation and focus, and keyboard height changes no longer interrupt it. Text, scrolling, rapid reopening and rotation remain stable.
- Guided-tour highlight and popover transitions use their previous 400 ms duration. Introduction and closing steps retain the circular cut-out fix.

## [2026.10.19.post4] - 2026-10-19

### Fixed

- Restored guided-tour highlight morphs between real targets and popover slides between anchors. Introduction and closing steps keep their solid backdrop without a circular cut-out. Scrolling tracks targets directly, rapid navigation discards detached popovers, and reduced motion disables transitions.

## [2026.10.19.post3] - 2026-10-19

### Fixed

- Search opens in 200 ms and closes in 100 ms. Its input and results retain their full dimensions as the shell expands, preventing text reflow and temporary scrollbars. Long result lists regain normal scrolling once the transition finishes.

## [2026.10.19.post2] - 2026-10-19

### Changed

- Search expands from its top-bar field into the palette and contracts back on close. Results reveal inside the growing panel without scaling text. Interrupted transitions, viewport changes, keyboard focus and reduced-motion/no-GSAP fallbacks are handled by the shared motion module.

## [2026.10.19.post1] - 2026-10-19

### Fixed

- Guided tours show a solid backdrop on introduction and closing steps. Highlight cut-outs and popover anchors update together, removing circular SVG sweeps and cross-screen slides. The opening and closing fade is preserved.

## [2026.10.19] - 2026-10-19

### Added

- Classroom assistant, behind `FEATURE_CLASSROOM_ASSISTANT` (off by default): a bot that works on a course's projects as a colleague, which students meet only in GitLab. A teacher connects its token on the course's new **Assistant** tab - a group access token with the Maintainer role and the `api` scope, checked with GitLab and stored encrypted. The analytics keep their read-only token: the bot has its own client, and a 401 on its token never pauses the course's sync.
- Push review: after a student's push, a comment on the pushed commit when it went straight to the default branch, when the GitLab web editor wrote the message (the R13 rule) or when the message is too short. A new branch is encouraged; a clean push to an existing branch gets no comment; a redelivered webhook is never answered twice.
- Merge conflict: the first time a student's branch changes the exercise file, a colleague's commit on the default branch edits exactly those lines, so merging the branch conflicts - also when the default branch moved on, verified with real git. Once the default branch is merged in, each push is checked for leftover conflict markers and for both sides kept, and the result goes to the merge request or the commit.
- Issues and merge requests: **Prepare exercise** gives every student of the chosen projects a file and an assigned issue; running it again adds only new students. The student's merge request is reviewed - own branch, a link to the issue, only the assigned file, nothing left to fill in, not a draft, no conflicts - with one comment asking for exactly what is missing and an answer to the student's comments. Once nothing is missing it is approved, and the student merges it (R10 does not count a bot's merge as the student's) or, if the course chooses, the assistant merges it. GitLab's merge event closes the issue and says well done; a merge before the approval is said to be so.
- The Assistant tab shows the bot and its token expiry, the three tools on the shared save bar, the last exercise run per project, and an activity table - tool tabs, search, pagination - of what the bot did, with links into GitLab. An archived course is read-only. A guide for teachers in Slovak and English.

### Changed

- R13 and the push review share one web-editor commit rule (`app.utils.gitlab_patterns.is_web_editor_commit`).

## [2026.10.16.post3] - 2026-10-16

### Fixed

- The shared Settings and Preferences save bar paints through the scroll area's bottom gutter, hiding content below its buttons while scrolling. Buttons keep their position; the final page gutter, including below Danger Zone, is preserved.

## [2026.10.16.post2] - 2026-10-16

### Fixed

- Deployment stops on remote command, pipeline, Git and HTTP readiness failures. A production checkout with tracked changes is preserved and rejected; pulls must fast-forward to the requested commit. The running API's commit and version are checked before reporting success.
- Migrations run and are verified in the newly built image before the serving API is replaced. Documentation is built successfully before its current container is removed.
- Version-only releases reuse the Docker dependency layer: only `requirements.lock` is copied before installing dependencies; release metadata is copied into the runtime image afterwards.

### Changed

- Local agent configuration, runtime uploads, scratch files and tool caches are excluded from the Docker build context. Deployment instructions describe the checks and release order.

## [2026.10.16.post1] - 2026-10-16

### Fixed

- Selectors preview unselected options with a subdued check on hover and keyboard focus. Selected options keep a solid check; disabled options and menus opened under a resting pointer do not gain a preview. The shared rule covers period, form, language and page-size menus without moving their labels.

### Removed

- An unused 716 KB GitLab documentation CSS snapshot from the repository root.

## [2026.10.16] - 2026-10-16

### Fixed

- Users gives spare horizontal space to Email instead of stretching short fields. Fixed mode keeps its existing column widths; filtering and pagination keep the fixed table layout.
- Settings and Preferences retain the shared page gutter below their last block. The save bar no longer removes its ancestors' padding, which left a nested Danger Zone against the panel edge.

### Changed

- User and member tables share the row-actions component. Danger Zone styles live with cards, and Users layout rules live together in the admin stylesheet; duplicate ID selectors and obsolete overrides are removed.

## [2026.9.30.post110] - 2026-09-30

### Fixed

- **Security:** `urllib3` 2.7.0 -> 2.8.0 (CVE-2026-97687, CVE-2026-97688, CVE-2026-97689: proxy and target TLS settings mixed up, and two flaws in streaming chunked / compressed responses), which un-breaks the `dependency-scan` CI job - red on every pipeline since 2026-10-01. `exclude-newer` moved to 2026-10-05 so uv can see the fix; urllib3 is the only pin that moved.

## [2026.9.30.post109] - 2026-09-30

### Changed

- **Course Teachers is a list page like every other one.** It was an Alpine app: the server inlined the list and the browser drew the rows after first paint, so the page opened on a header over an empty table, and then the rows, the count ("Showing 54 of 54" became "Showing 54"), the sort arrow, the active tab and the Remove all restrictions button (enabled, then disabled - the server and the script decided it differently) all changed in front of the reader. It sorted, filtered and counted with code of its own, had no search and no pagination, and drafted changes behind a Save bar no other list has. Now the server renders the rows, in the order the Teacher header says, and the Users page's components work them: the search and the role tabs in the controls band, sortable headers, and the pager carrying the count. A change applies when it is made, as on GitLab's members page - a course role picked in the row's menu, a teacher removed with the trash, Add teacher in a dialog, Remove all restrictions - each sends the course's list to the endpoint the form always posted to (which answers JSON when asked: ok, 409 conflict, 422 no owner) and the page comes back from the server. Measured with the deferred scripts held back: the first frame and the settled page are the same - nothing appears, vanishes or moves.

### Fixed

- **The pager under every list is in the first frame.** `pagination_controls` was born empty and ClientPaginator drew "Showing 1-25 of 54", the page buttons, the arrows and the per-page menu after paint - on the course's groups, a group's members, Support, Tickets, Admin Courses, Users, Activity and Teachers. Given the rows the table opens with and the reader's Rows per page, it renders page 1 itself - the markup the paginator writes - so nothing moves when the paginator takes over.
- **A list opens with the reader's own page of rows.** Until the script ran, rows past a fixed 50 were hidden - past 25 on the Users page, so it opened with 25 rows and grew to 50, 1265px, when the script ran. They wait at the reader's Rows per page now (`html[data-page-size]`).
- **Course Settings with no webhook configurations opens on the empty state**, instead of a table header the script swapped for it after paint (the card grew 272px).
- **The typeahead fills its field, and in a dialog its suggestions open in the flow** instead of being cut off at the dialog's edge.

### Removed

- What only the old Teachers page used: the `alpine_select` macro, the Alpine hooks in `filter_tabs` and `sortable_header`, the `.teacher-add-row` rules and the Users page's own 25-row rule.

## [2026.9.30.post108] - 2026-09-30

### Fixed

- **Every table's row actions are the same buttons.** An audit of every table on every page, for each role, at 1440px and at 390px on a touch screen, found row actions in six shapes. They are all `btn_icon_only` / `btn_link_icon_only` now - 24px squares, 36px on touch; neutral actions secondary, a delete the red trash, "view / open" the eye:
  - the course's groups table ended each row in a filled blue "View" beside 24px icons; a deleted group's row had worded "Restore" / "Remove from deleted" buttons, and the CSS that let them wrap and hid their words below 1440px (and hid "View" below 480px) is gone with them; a group added without a reload got 14px glyphs in padded boxes and a filled delete;
  - the tickets and project members tables had a worded "View";
  - the events table's "Details" and "Resurrect" were worded buttons (now the eye, and Restore's green arrows), the job history's "Cancel" a filled red button with a 12px glyph;
  - course Teachers' remove was a grey trash where every other delete is red; the weekly deadlines' delete and edit were borderless; the Users table's info and edit were borderless beside bordered actions everywhere else;
  - the scoring toggle in the group and project member tables was 34px wide and rested at 40% opacity until its row was hovered - on a phone, always. It is a plain row action now, and its glyph says what a press does (a person with a minus: leave out of the score; with a plus: count again) instead of an eye, which next to "View" was the same glyph twice.
  Measured after: no row action off the row size, no glyph in two looks except a disabled one, no label hidden by a rule, no cell spilling over its neighbour. `test_row_actions_are_icon_buttons.py` scans every `<td>` in the templates.

### Changed

- **A course's tabs share one header.** Activity and Analytics had headers of their own ("... · Activity" with a line on what the page is for), Settings and Teachers the course's without its description or the reader's role. All five tabs - the course, Activity, Analytics, Settings, Teachers - now carry the course page's header: code and name, the term, the Course Owner / Teacher badge and the description, so switching tabs changes only the tab. Settings sits in the same tab frame as the others; the Teachers card's count moved from its title to beside its actions; a reader who may not manage a course's teachers gets the Access Denied page with a way back to the course. Browser titles are the tab's name ("Activity", "Teachers") and the course code.

## [2026.9.30.post107] - 2026-09-30

### Fixed

- **One press never reads "x2".** A toast raised again while it is up is not stacked: it replays and counts, "x2", "x3" - the answer to "did my second click do anything?". But every raise counted, and one press can raise the same message twice: the action's own answer and an echo of it (the server's event for the same job, a second listener). So a single click read "x2". A toast now remembers the press it was said for - a pointer going down anywhere but on a toast, or Enter / Space - and only a new press counts; an echo or a poll repeating it is absorbed. Checked in a browser: one press raising the message twice shows it once, a poll raising it again changes nothing, a second press reads "x2".
- **An archived course's row actions look the same in both places they appear, at GitLab's small icon-button size.** On Admin > Courses, Assign teachers and Settings were labelled buttons with no words - 34px wide, beside 24px squares; on the dashboard's Archived Courses card all three actions were labelled buttons with the words hidden by a page rule, 26px wide, and Re-activate was a grey refresh where the admin table had a green check, Delete a filled red button where it had the red trash. All are icon-only buttons now (`btn_icon_only` / `btn_link_icon_only`): 24px squares, 36px on a touch screen, the same glyph and colour for the same action. The two page rules that hid the labels are gone.

## [2026.9.30.post106] - 2026-09-30

### Fixed

- **User Management's service-account rows stay inside their columns.** Above 1180px the Users table is `table-layout: fixed`, but a service account's name, full name and address kept the 20ch / 28ch caps written for the widths where the columns size to their content - wider than the fixed columns (126px Full name, 189px Email). A bot's full name ran up to 120px past its cell and printed over the address beside it ("Triedenie hráčov podľa skóre" over "PRIVATE"), and the address ran under the Role badge. The caps now apply at 1180px and below only; above that a value is cut at its cell's edge, its tooltip holding the whole value. A bot row also said Bot twice - beside the name and in the Role column - and the second badge took 40px of the name's 150px column; the Role column says it alone now. Measured at 1530, 1366, 1200, 1100 and 390px: no cell's content crosses into its neighbour.

## [2026.9.30.post105] - 2026-09-30

### Fixed

- **A disabled control is visible and reads as disabled - GitLab's disabled tokens, no fades.** A disabled checkbox was GitLab's disabled box at 40% opacity: on the light theme its outline was 1.1:1 against the page, so an archived course's check list showed an Active column of empty boxes whether a check was on or off. It is now GitLab's disabled checkbox (`form_checkbox.scss`): the disabled box colours and, when ticked, the same box with the tick in `control.indicator.color.disabled` (new token `--gl-control-indicator-disabled`). The pager sat on the card shell's grey, where a dead arrow - GitLab's near-white disabled button - all but vanished; it now sits on the body's white under a line, where GitLab's CrudComponent puts it, and a dead arrow is GitLab's disabled pagination item: no border or fill, the glyph in `action.disabled.foreground.color` (new token `--gl-action-disabled-text`).
- **A disabled control says why - on a phone too.** Tooltips are hover-only, and most reasons sat on the disabled control's own `data-tippy-content`, which a disabled control never receives an event for. A control now declares `data-disabled-reason`; while it is disabled, `process-action-guards.js` wraps it in `.gl-tip-wrap` (a MutationObserver follows whatever toggles `disabled`), which shows the reason on hover and as a toast on tap, and unwraps it when it is enabled again. With reasons now: the pager arrows ("You are on the first page." / "...last page."), every bulk action ("Tick at least one row first."), Apply Configuration in both import dialogs ("Load a configuration file first."), Delete Forever, Generate without an LLM key and course Teachers' Clear all.
- **Phones: touch targets of at least 32px, no text under 12px, nothing half off screen.** On a touch screen (`hover: none` and `pointer: coarse`) the card header's buttons, its info mark, the banner's close button, the Q&A tabs, `summary` rows and ghost buttons are 32px tall; a checkbox and the small text links (breadcrumbs, Back, home panel links, profile and e-mail links, chips, refs, MR numbers, the error and sign-out pages' links) get a 32px hit area from a positioned pseudo-element, without moving the layout. The tablet sheet set small badges, job labels and the search badge to 11px and stat labels to 10px, the analytics threshold pills were 10px and the pipeline donut's labels 9px - all are 12px now. An empty table's message ("No events recorded yet") was centred across the whole table, half off a phone's screen; it is centred in the visible part of the scroller. A link-styled button ("Use the official TUKE dates (...)") wraps instead of running 36px past the screen's edge. Measured on all 28 pages x roles at 390px and 360px, light and dark: no control under 32px, no text under 12px, no sideways scroll or off-screen box, no disabled control without a reason.

## [2026.9.30.post104] - 2026-09-30

### Removed

- **The `HX-Content-Only` fragment branches.** Six routes - the dashboard, User Management, course Teachers and the three Support pages - and `page_cache.render_inline_or_fragment`, behind the course, activity, analytics, group, project and student pages, answered a request carrying that header with a bare content fragment instead of the page: the lazy-loading and in-place-refresh design of the summer. Pages have arrived whole in one response since post99, and the last client that sent the header (the analytics refresh) stopped in post215, so the branches only ran for a hand-made request - and the Support page's was wrong even then: it rendered the ticket form for every step and answered the course and category steps with a 500. Every page now answers with the page; the helper is `render_inline`, `serve_personalized` (used only by the removed branch) is gone, and the dashboard's Homepage redirect skips an HTMX request alone. Verified on 37 URLs x three roles x two languages: normal requests return byte-for-byte what they did, and a request with the header gets the same full page. `page_cache`'s module docstring and `docs/18_scale_optimizations.md` described the lazy loading of before post99 and two routes that have since moved; both are current.

## [2026.9.30.post103] - 2026-09-30

### Fixed

- **The image builds the served CSS and JS from the sources, whatever else is in the checkout.** The post102 deploy kept the files its pull deleted - the old `styles.bundle.css`, `core.bundle.js`, page bundles and `.min` twins - in place for the containers still running, and the image was built from that same checkout: `build_bundle.py` read the stale files as sources and let them replace what it had just built, so production went on serving the post101 stylesheet, without the post102 save-bar and pinned-cell fixes. A file named like a build output (`.min.`, `.bundle.`) or like one of the build's own outputs is no longer a source. Replayed with all 53 kept files in a checkout: the image now builds the same `manifest.json` as a clean build.

## [2026.9.30.post102] - 2026-09-30

### Fixed

- **The settings save bar is GitLab's: the page's own background under a top border, flush with the content.** On course Settings, Preferences and course Teachers it carried a shadow and was pulled 16px out into the container's padding on each side, so on the light theme it floated as a white box wider than the cards above it (at 1920px: 431-1711 against content at 447-1695). The shadow and the pull-out are gone, and with them two course-page rules that only restated the bar's own margins and the `--mc-pad-x` variable nothing else read. An audit of every sticky and fixed element on every page (light and dark, 1440 and 390) finds no other one whose background differs from what it sits on; the remaining shadows are the pinned Actions column's edge while columns scroll under it.
- **An excluded member's row keeps its tint into the pinned Actions cell.** The pinned cell paints its own background so the cells sliding under it do not show through, and every tinted row needs its own pinned-cell rule - the excluded row had none, so it ended in a white (on the dark theme, lighter) block.

### Changed

- **The JS and CSS the browser receives are build outputs in `dist/`, no longer committed - Vite's model.** `scripts/build_bundle.py` writes them into `dist/` under content-hashed names (`js/core.bundle.1005fb0c.js`) with a `dist/manifest.json`; `static_url()` - now `app/assets.py` - resolves the logical name a template asks for through it and serves the file from `/static/dist/`, cached as immutable (the name is the version). Vendored builds, images and fonts are still served from the source tree with `?v=`. The Docker image builds `dist/` in an `assets` stage (rjsmin 1.2.5 and rcssmin 1.2.2 pinned) and places it beside `src/`, outside the templates directory production mounts from the host. In CI, `bundle-check` builds into a scratch directory and fails when a `static_url('...')` resolves to nothing, and `check_static_artifacts.py` fails on a build output left in the source tree; pytest builds `dist/` at session start. Verified: each of the 41 built files is byte-identical to the file served before, the image builds the same manifest as a local build, every asset of every page answers 200 with the same bytes as before, and the pages render identically (computed styles).
- **A deploy keeps serving the static files its pull deletes.** The running containers serve `static/` from the host checkout until the new image is up - minutes after the pull - and open or cached pages keep requesting what they linked, so a deleted or renamed file answered 404 in between. `redeploy.py` now archives the files the pull will delete, puts them back untracked after it, and removes them at the next deploy unless they have become tracked again (simulated on throwaway repositories: kept, removed a deploy later, untouched when re-added).

### Removed

- The 53 generated files from the repository: `core.bundle.js`, `styles.bundle.css` and their `.gz` copies (nothing served those), the eight page bundles, `tours.js`, the Slovak client catalogue and the `.min` twin of every standalone script and stylesheet; `static_url()`'s `.min` lookup; the test filters that skipped them.

## [2026.9.30.post101] - 2026-09-30

### Fixed

- **No blank space under a table once its rows are in.** `data_table(reserve_rows=)` held the expected height as an inline `min-height` on the wrapper, and nothing released it when the first render drew the rows - only a re-render did. So a short table stood over empty space (41px under a student's two issues, 47px under the Events table on a phone) until a filter switch cleared it, and it came back on every reload. The reservation is now a `--table-reserve` value that `tables.css` applies only while the body is empty or shows just the loader (`.table-loading-row`); the rows or the empty state take over the moment they are there.
- **"Import full configuration" on a course's Settings page works.** The page posts the configuration as JSON with the CSRF token in a header; the import into an existing course only looked for a form body the CSRF check had cached, so every import answered 400 "No configuration provided". Both imports (into an existing course and creating one) now read the request through one helper and validate the file the same way - the import into an existing course also skipped the nesting-depth limit.
- **A webhook event that fails processing is recorded as failed.** After the rollback the failure path read the expired event (a lazy load an async session cannot do), raised `MissingGreenlet` inside the error handler, and the event never got its retry count, its error or the dead-letter queue - it stayed unprocessed with no trace and was retried for ever. The event is re-read after the rollback now.
- **A page's live refresh reads exactly what the page rendered.** Each refresh endpoint had its own copy of the page's queries, and they had drifted, so numbers changed on the first refresh without anything having happened:
  - course page: the Contributors column switched from this semester's authors to all-time ones;
  - course Activity Monitor: a group's pipeline badge switched to "running" (the refresh took the newest pipeline of any state; the page skips in-flight ones, which without pipeline webhooks can stay "running" for good);
  - project page: members excluded from scoring dropped out of the refresh (so their greyed rows never updated), and the empty-repository / template-fork states were counted against a narrower roster without the configured exclusions;
  - course sync badges: the stream merged a group's jobs by priority while the poll took the newest, so a stale `running` row from a crashed worker kept a group on SYNCING and an older `completed` hid a newer `failed`. Both read one state now (newest job wins).
- **The streamed course import locks each group like the plain import does**, so two imports cannot write the same group at once.
- **The team AI-analysis status counts an expired job as finished**, as its live stream already did (RQ drops a finished job after its result TTL but keeps a failed one), instead of reporting it as failed once the result expired.

### Changed

- **Every function over 200 lines is split into its parts** - 39 of them, among them the course settings save and both configuration imports, the course import and its stream, member sync, the sync status, stream and "sync all", the MR / note / event processors and the metrics job, MR and issue enrichment (which now share `workers/enrich_common.py`), the admin user details and GitLab enrichment, the dashboard and the student's context, the course, group and project pages with their refreshes, the compliance engine, pilot telemetry history, the Markdown filter, GitLab parsing, the app's middleware and static setup, and the LLM analysis (prompt building, the project job and the team status stream). Each was checked old against new: rendered pages byte for byte for three roles in both languages, JSON responses, database snapshots after running the jobs against a fake GitLab on copies of the dev database, and a scripted model for the LLM paths (prompts, contexts, stored results and every error path).
- **`redeploy.py` keeps the production disk from filling.** Before rebuilding it prunes Docker build cache older than a week and dangling images, and stops if less than 10 GB is free - the build cache had grown to 230 GB and filled the disk, and PostgreSQL crash-looped.
- **29 CSS declarations that could never apply are removed** - each overridden, at every width and state, by a later rule with the same selector in a context that covers its own (e.g. a 640px rule restated by the 768px mobile layer) - and a login-page rule that only restated the one above it. The mobile modal close button stays 32px and the users table keeps its 1190px floor, as they already rendered; the comments that described the dead values are corrected.

### Removed

- The course page's KPI counter updates and their tour step - the counters left the page earlier, the code still wrote to them.

## [2026.9.30.post100] - 2026-09-30

### Changed

- **Error pages offer only what can still work, and are one template.** A 503 offered a search box and links to Home, Support and Sign out while the app behind them was down, and its heading and paragraph were one sentence twice ("503: Authentication backend temporarily unavailable..." over the same text). The pages were nine templates plus a Python-built copy in the error-boundary middleware with its own English-only wording, and the 502/503 templates ignored the message their handlers passed, so a database outage read "a required service (cache or queue) is unavailable". Now `app/middleware/error_pages.py` holds one table - title, description, illustration and what the page offers per status - and `errors/error.html` renders every error page from it, the middleware included. 403/404 offer search and the way around; 500 Retry and the way around; 502/503/504 Retry and an automatic reload only; 401 signing in; 429 a countdown. The heading names the status and the error's own detail goes under it. On a phone the search stays one row and Retry keeps its width (the column layout stretched every button and squeezed the field). Every page head carries the standard `mobile-web-app-capable` next to Apple's, which Chrome reported as deprecated on the error pages. The missing Slovak for their messages is added. The proxy's static outage page (`deploy/errors/maintenance.html`) drops its Home and Documentation links for the same reason - it already checks and returns the reader by itself.
- **Tables give each column the room its content needs.** The project Members check matrix takes declared shares (a check 44px, Score 92px, Actions 129px at a 1 190px card) instead of shrink-to-fit columns that left the name 200px of air while the codes touched; User Management wraps a person's name, login and address instead of cutting them to "barbora.cierna@dev.l..."; Job History reads its type whole and wraps the result to three lines instead of truncating it at 80 characters; a team's Projects table gives the name the room the short path did not need.
- **The guided tours load when the page is idle.** The tour engine, its tours and Driver.js (~270 KB) were a third of `core.bundle.js`, which blocks the first paint of every page. They are now `js/tours.js` plus the vendored Driver.js, fetched by `_parts/core/49-tours.js` once the page is idle; a click on Take a tour / Replay tours before that loads them at once. `core.bundle.js` goes from 182 KB to 131 KB gzipped. The first-visit prompt, Take a tour and Replay tours behave as before (checked in a browser, including a click before the tours had loaded).
- **A project sync and a team sync are the same sync.** The project sync re-implemented the per-project stages and had drifted: it re-fetched every note, diff and finished pipeline on every run, and never recovered the commits of a merged MR whose branch was deleted nor stored an MR's own commit list - so a project read differently after a project sync than after a team sync. Both jobs now run `app/workers/project_sync.py`, and share their job bookkeeping (`sync_lifecycle.py`: attempt, cancel, start, inline metrics, completion, failure). Verified against a fake GitLab on copies of the dev database: the team sync writes identical data before and after for every team, including every edge path (a 404 project, deactivated team, archived course, cancelled job, a failure); the project sync now writes exactly what the team sync writes. One deliberate change: an empty repository that does not exist at all is deactivated by the team sync too, as the project sync already did.
- **The largest functions are split into their parts** - the team sync (1 559 lines), the GitLab course import (1 428), the dashboard's attention list (1 034) and activity feed (868), the project sync (844), course analytics (742), the compliance engine's `compute_team_metrics` (710) and the webhook receiver (637). The import's four copies of member handling, three of frequency-based teacher detection and three of inherited-member users are one each. Each was checked old against new: attention and feed items over 900 scenarios on the dev and seeded data, metrics row for row over 21 runs per team, every import scenario (events, results, database, API calls), 21 webhook deliveries (responses and database), and the rendered pages byte for byte.
- **115 CSS declarations that restated an earlier rule are removed** - the same selector, property and value in a context the earlier one already covers (the base rule, or a wider breakpoint), with nothing in between on that element and property. Almost all were in the responsive override layer.

### Fixed

- **The dashboard's live activity refresh keeps the "Course created" and "Course archived" rows.** Its course query loaded neither `created_at` nor `archived_at`, so each refresh raised on the lazy load - hidden by a swallowing `try` - and the rows the page showed vanished. A test now checks the refresh loads every column the feed reads.
- **The activity feed of a course without groups shows that course's jobs only.** The job query hung its scope on there being groups, so without any it applied no scope and listed every course's jobs.

### Removed

- The per-status error templates, `errors/error_base.html`, `errors/feature_disabled.html` and the middleware's own error HTML; stale comments about a commit-history branch picker removed in 2026.9.22; the unread `student_members_observed_by_team` state in the import; the `_is_gitlab_auth_error` alias.

## [2026.9.30.post99] - 2026-09-30

### Changed

- **The project Members check matrix is styled in one place.** Its rules were spread over four files that overrode each other: `pages/project.css` (a page file styling another page's component), the member block of `pages/course.css`, a phone rule in `_parts/responsive/00-mobile.css` and the result marks in `badges.css`. Of those, only the tabular figures and the 8px column padding ever applied - `.data-table th/td` out-ranked the rest - so the codes and ticks were left-aligned in their columns although every copy asked for centred. One rule on the matrix now does what they meant: each code is centred over its column of ticks. Widths, padding and fonts are unchanged (measured against post98 on every page).

## [2026.9.30.post98] - 2026-09-30

### Changed

- **The shared front-end core is one file per component.** `core.bundle.js` was concatenated from four files of 1 600-3 500 lines each - `20-ui-helpers.js` alone held buttons, content states, tooltips, date pickers, data actions, banners, scrolling, the anti-spam guards, tabs and the boot. It is 49 files now, `_parts/core/NN-<component>.js`: 0x primitives (namespace, job messages, HTTP, auth sync, API, SSE, toasts), 1x modals and navigation, 2x-3x UI components, 4x the SPA shell. Only function declarations moved; the minified bundle carries the same statements and is the same size. Course settings' 1 500-line `20-advanced.js` is seven feature parts (checks import, LLM generate, full config, danger zone, live state, webhooks, weekly deadlines); the served `pages/course-settings.js` is byte-identical.
- **The student page is built section by section.** `student_detail` was one 1 334-line function. `students/routes.py` keeps access, the content cache and rendering (~180 lines); each section - activity counts, the issue list, the MR cards (pipelines, diffs, commits, reviewers, threads, activity), reviews given, commit history, compliance history - is a function in `students/profile.py`, and the commit-attribution logic that was written out three times is one helper. The rendered HTML is byte-identical on every student page (18 students x admin / teacher / student x EN / SK, full page and fragment).
- **Support pages have their own module** (`dashboard/support.py`) instead of living in `auth.py`.
- **No module patches another module's function any more.** The mutation throttle is part of `apiCall` rather than a second `apiCall` assigned over the first, and the `openModal` wrapper in `process-action-guards.js` - which consulted a lock map nothing ever filled - is gone. `test_bundle_scope_collisions.py` no longer allows any `GP` export to be defined twice.
- **`.min` files only for what is served on its own.** The build minified every source, including those that only ever reach the browser inside a bundle; it now minifies the 38 files a template loads by `static_url()`, deletes the 64 `.min` files nothing loaded, and writes LF on every OS.

### Removed

- Code nothing called: `ComplianceSnapshotCreate`, `SupportFormService.create_form/update_form/delete_form`, `get_async_session_no_autocommit`, `load_checks_from_file`, `require_course_role`, `run_auto_archive_sweep`, `process_commits_batch`, `enqueue_llm_analysis`, `get_all_queue_depths`, `sync_course_members`, `app.services.user_filters`; in JS `GP.installApp`, `window.GPTheme`, the manual top-progress driver, four `GP.health` members, the password-strength component (sign-in is GitLab only), `countFor` (filter tabs carry no counts) and `showReplyPreview`; the `feature_card` macro and its styles; `static/docker-verify-ci.yml`, which reported to an endpoint that no longer exists.
- 59 CSS declarations a later rule with the same selector, in the same media context, always overrode.
- 129 Slovak catalogue strings no template, script or view asks for.
- Values the student page computed and never rendered - two of them whole SQL queries (the membership row and the issue-comment counts) - and `check_descriptions` on the course and team pages.

### Fixed

- **A ticket page is for its course's staff.** Any teacher could open any course's support ticket by its number, internal notes included, while the page's own live stream was refused with a 403. The page now applies the rule the ticket API and its stream already had, and answers a 404 otherwise.
- **The project Members table cut its check headers to "R..." and its View buttons in half.** It was a fixed layout with percentage columns: 49px for a check whose header needs 51px, 109px for actions that need 141px. The check, Score and Actions columns now take what their content needs and the name the rest; codes use tabular figures so the thirteen columns are one width; a one-glyph column has 8px either side. The whole matrix fits its card from a 1 440px window up and scrolls, never clips, below that.
- "Member" and "Ticket" were English on the Slovak 404 page.

## [2026.9.30.post97] - 2026-09-28

### Changed

- **Every table's controls band is the one on User Management.** A band holding tabs laid itself out by its own rule (`table-controls--tabs` plus two `:has()` copies: no padding, aligned to the line), a band holding only a search or dropdowns kept 16px under them - so Job History put its controls 16px from the body's top and 17px over the line, Users 22px and 7px. Every band is Users' now: rows of 43px (the tab strip's height) with the controls centred and the line under the last one, 44px with the line; a tab strip alone rests on the line. The row height sits on the band's two groups, so a band that wraps on a phone gives its second row the same air over the line instead of setting the dropdowns on it. A band that opens its card inside the `[data-tabs]` wrapper (course Activity) gets the same 16px above it as every other band - it had 24px. Measured on 30 pages: every band 44px, controls 22px below the body's top and 7px above the line, the table 12px under it.

## [2026.9.30.post96] - 2026-09-28

### Changed

- **Every card header is one header: icon, then title.** There were three layouts of one component - no icon ("All Courses"), an icon inside the title ("Users") and an icon beside it ("Archived Courses") - so the title started 12, 32 or 36px from the header's edge, and the settings cards drew a 20px icon where the rest drew 16px. The icon is the card macro's `icon_name` slot everywhere now (38 cards; the 11 that had none take the icon the app already uses for the same thing - `book` for courses, `inbox` for tickets, `users` for members), a title is words, and every header measures the same on every page (53 headers, one geometry). The `.card-title .icon` rule, `.card-header-flex` and the 8px gap `.card-header--interactive` re-declared are gone. Pinned by `test_every_card_header_is_one_header.py`.

### Fixed

- **The Users table's "GitLab User ID" header was cut to "GitLab Us".** `pages/admin.css` held two contradictory layouts for the table - `table-layout: auto` with a 160px floor for that column, and further down `table-layout: fixed` with it at 7% (83px for a 149px label); the later one won and a fixed layout ignores the floor. One layout now (fixed, so columns do not move when a filter hides rows), each share measured to fit its header in English and Slovak and its badge, date or buttons (Status and Actions were short too), and a 1190px floor below which the table scrolls instead of clipping. A header that still does not fit wraps at a word, as GlTable's do, instead of being cut: the auto-layout-only `nowrap` no longer reaches this fixed table. The unit test that pinned the dead `auto` rule now pins the one layout.

## [2026.9.30.post95] - 2026-09-27

### Fixed

- **A tab switch no longer blinks what both panels share.** The incoming tab panel faded up from opacity 0, so Quick access's empty-state illustration - drawn in the same place under both tabs - vanished and came back on every switch. A panel now swaps at once, as GlTabs does (`:no-fade="true"`); the travelling underline is the switch's motion. Pinned in `test_one_motion_per_role.py`.

## [2026.9.30.post94] - 2026-09-27

### Changed

- **Every empty state leads with a GitLab illustration.** Page-level empty states had GitLab art; empty tables, lists, charts, panels and filtered-to-zero results were a grey line with nothing above it. All of them are GlEmptyState now, with the sm illustrations from `@gitlab/svgs` 3.165.0 (byte copies, hashes pinned): `status-nothing-sm` for "nothing yet", `search-sm` when a filter matched nothing, `chart-bar-sm` for an empty chart, and `status-fail-sm` for a failure (replacing the alert-triangle glyph). The illustration sits in the 72px slot the loading spinner takes, so loading -> empty still moves nothing. JS-built states read the same vendored files from one `<template>` in `base.html`; the server gets `block_empty()` next to `table_empty()` / `chart_empty()`.
- **Hand-written empties moved onto that one state**: the dashboard activity feed and sidebar panels, the project's protected-branches / contributors / repository-stats cards (server and live refresh), weekly deadlines, the run-checks filter, a student's issues card and the user-info dialog's sections. Small containers keep the art and drop the page-sized padding.
- **Less air round a table's search row**: the band has 16px above and 16px below the controls (was 24px and 24px), one property for both.

### Fixed

- **Two tooltips at once**: a table cell with its own tooltip holding a time stamp with another (Job History, Enqueued) showed both, stacked. There is one tooltip at a time everywhere now: the innermost target wins while the pointer is on it, and showing a tooltip hides any other. The redundant cell tooltip is gone.
- **A time stamp's UTC tooltip showed the server's raw spelling** (`2026-09-25 16:55:17.605651+00:00`); every stamp now reads `2026-09-25 16:55:17 UTC`.
- **Two dropdowns open at once** (Support: status, then period): opening an Alpine-driven dropdown closes the plain ones, as opening a plain one already did.

## [2026.9.30.post93] - 2026-09-27

### Changed

- **Alike elements move alike: one timing per role, GitLab's for that role** (`@gitlab/ui` 137.3.1), written down in `tokens.css` and pinned by `test_one_motion_per_role.py`:
  - a control - button, close / dismiss / icon button, badge, tab, pagination, toggle, link, card hover, chevron - eases colour and shadow over 200ms out-cubic; dozens of them ran at 100ms beside 200ms buttons;
  - a dropdown / menu / list item and a table row: 100ms, like `gl-new-dropdown-item`;
  - a form field and a checkbox: `.15s ease-in-out`, GitLab's `$input-transition`; the checkbox tick no longer grows in;
  - every disclosure - chevron and collapse - on 200ms out-cubic, Alpine's `x-collapse` (250ms, its own curve) included;
  - every panel opens with the same 4px / 100ms rise (dropdown, date picker, mobile filter panel), tooltips fade over 150ms linear, the cookie banner enters like every other banner;
  - every fill - progress bar, meter, compliance ring, job bar, toast countdown - runs 600ms (was 300, 500 or 600);
  - one pulse for every live mark (was 1.5s or 2s);
  - **a press moves nothing**: seven different press scales (0.97 to 0.88) are gone - a GlButton's `:active` is a colour.
- **Control sizes are GitLab's**: a button is 32px (was 34, beside 32px icon buttons); every small button is 24px with 14px text, card-header actions included (they had 12px text and their own padding); `.btn-xs` is GlButton small (it was a 20px size GitLab does not have); pagination arrows are 32px like the page numbers between them; every dropdown toggle sits on a 16px line; a filter tab with a count badge is as tall as the tabs beside it.
- **README (EN / SK) rewritten**: new screenshots of the current interface (light and dark, English and Slovak), GitLab's own pipeline and coverage badges instead of third-party logo badges and a hand-written "tests passed", a role overview, a tour, the thirteen checks, and numbers checked against the code.

### Fixed

- **The system-health "down" icon never pulsed**: its animation named a keyframe that did not exist.
- **The tour opened the mobile sidebar at a different speed** from the sidebar's own slide.

## [2026.9.30.post92] - 2026-09-27

### Security

- **Every state-changing request that rides on the session cookie checks the CSRF token** - twelve did not: retrying and replaying webhook events; deleting, purging and updating support tickets, commenting on one and uploading an attachment; recomputing a weekly telemetry snapshot; and the four telemetry beacons. The app's own requests already carried the token (the beacons in their JSON body, since `sendBeacon` cannot set a header), so nothing changes for a reader; a request without one is refused with 403. An audit that walks the real routing table found them and now reports none.

### Fixed

- **Opening a dialog no longer lights up a select as if the pointer were on it.** The dialog slides 50px into place (GitLab's modal motion) and carried whatever lay under the resting pointer - often a select - through its hover state for a few frames. Its contents take the pointer once it has landed; a click in that window hits the dialog, never the backdrop.
- **CI runs the integration tests again.** Their probe looked for Postgres and Redis on `localhost`, while the pipeline's services answer as `postgres` and `redis`, so every integration test was skipped and the job passed on nothing. The probe reads the hosts from `DATABASE_URL` / `REDIS_URL` now, and the 14 event-pipeline tests that had been failing unnoticed (their client sent no CSRF token) pass: 64 of 64, locally and in a replica of the CI job.

### Changed

- **Migration `022_drop_remember_period`** drops `users.remember_period` - the contract step of 021: its value lives in `default_period`, and no release since post89 reads it. The downgrade restores it from `default_period`.

## [2026.9.30.post91] - 2026-09-27

### Changed

- **Empty states are laid out as GlEmptyState, class for class**: the 144px illustration, then one content block (16px padding, at most 65ch) with the title at 28px on a 36px line, the description 12px below in the subtle colour and the actions 16px below that (buttons `0 4px 8px`). The page-specific 320px cap under AI analysis is gone.
- **The date picker's month arrows** are GlDatepicker's (`$gl-icon-chevron-left/right`), not flatpickr's own.
- **A running pipeline** shows Pajamas `status_running`; `spinner` is a 10%-opacity sprite placeholder and drew almost nothing.
- **No more text characters as icons**: the project members table (✓ / ✗) and the week explorer's improved / declined chips (↑ / ↓) draw Pajamas icons, the MR card's branch arrow is `arrow-right`, the PWA banner's and the issues chart's close buttons are `close`, the import dialog lost its ⚠, and the R08 detail says "commit ref cited" instead of ✓. The icon test now reads HTML entities and `\u` escapes too.

### Fixed

- **Course Analytics answered 500** where the checklist chart had no data: `chart_empty()` still received an icon argument after post90 removed it. A test now checks every empty-state macro call against its signature.

## [2026.9.30.post90] - 2026-09-26

### Changed

- **Every icon and illustration is GitLab's own, used the way GitLab uses it** - copied unchanged from `@gitlab/svgs` 3.165.0 and `@gitlab/ui` 137.3.1 and pinned by `test_every_icon_and_illustration_is_gitlabs.py`. The GitPulse logo and the loading tanuki stay the app's own.
  - **Empty states lead with a GitLab illustration, never a glyph in a tile.** The Dashboard's "No courses in <term>" draws `empty-schedule` instead of a calendar icon in a grey box; `empty_state()` lost its icon fallback, so a call without an illustration no longer renders.
  - **An empty table or chart says so in words alone**, like GlTable's empty row; the message keeps the loading label's place, so loading -> empty still moves nothing.
  - **Items that need your attention** use GitLab's system to-do mark (a 32px circle in the feedback colour, 16px status icon), and "Good job!" is the to-do widget's `status-success-sm` row.
  - **Sorting** shows GlTable's text arrow (↑ / ↓) on the sorted column and under the pointer, instead of a stroked caret pair.
  - Pajamas `close`, `check`, `chevron-lg-left/right`, `lock` and `warning` replace the hand-drawn dismiss cross, dropdown tick, pagination chevrons, protected-branch lock and the login page's Feather warning; disclosure chevrons are `GlAnimatedChevronRightDownIcon`; the select chevron, checkbox tick, radio dot, CSS chevron masks and the input's busy dots are `@gitlab/ui`'s own.
  - **No text character stands in for an icon** any more: the job bar, the AI model status, the tour's close button, the config-import preview and the student heatmap, legend and week deltas draw Pajamas icons.
  - **Error pages** use GitLab's current error illustrations (502 and 503 their own); the offline page drops its Feather icon - GitLab's offline page has none.

### Fixed

- **Icon-only buttons below 768px lost their icon**: the text padding left a 24px button no room, so the pagination chevrons were invisible in a narrow window.

## [2026.9.30.post89] - 2026-09-26

### Changed

- **Preferences > Behavior > "Default period"** replaces the "Remember the period I pick" checkbox - where every page with a period selector opens, the way *Homepage* picks the page: *The period I picked last* (the default - a term picked on any page is kept on every page until the next term starts), *The newest term with my courses*, *The term running now* or *All periods*. With any but the first, a pick changes only the page it is made on and nothing is remembered; a link that names a period always wins. Migration `021_default_period` carries every account over (the checkbox off becomes *newest*) and leaves `remember_period` in place until a later release drops it, so a deploy never removes a column the previous release still reads.

### Fixed

- **Teacher and admin pages apply the account's language on a device with no language cookie**, like every other page - the role guards skipped that step.

## [2026.9.30.post88] - 2026-09-26

### Fixed

An ESLint audit of every script the app ships - the core as the build concatenates it, each page bundle inside its IIFE, every standalone script - found four real defects:

- **The Dashboard rebuilt its lists on every refresh.** A raw backspace byte stood where a regex meant `\b` (an edit script had written it without a raw string), so the refresh key never normalised `<time>` and every tab return and SSE tick re-rendered the attention list and the feed.
- **The course page's fallback sync poll threw on its first answer.** It counted errors in two names that an earlier cleanup had stopped declaring; in strict mode the first assignment was a ReferenceError, so without the live stream the sync status never refreshed.
- **Tabs and filter pills were taken for the button the next toast reports to.** "Passive controls are excluded" went through a helper private to another script's closure, so the check was always false; the helper is on `GP` now.
- **`ClientPaginator` declared `register()` twice**, and the second, poorer copy won.

### Changed

- **No `var` left in the JavaScript sources, and no binding that could be `const` declared with `let`** (146 and 75 of them). Converted with ESLint's own fixers, which change a declaration only where `let`/`const` behaves the same - each unit fixed in the scope it really runs in; the one global `var GP` became the `window.GP` it always was. Dead variables, a sparse array, needless regex escapes, two function-declaration reassignments and stale `/* global */` notes went with them. A test keeps `var` and raw control bytes out.

## [2026.9.30.post87] - 2026-09-26

### Added

- **Preferences > Behavior > "Remember the period I pick".** On (the default, today's behaviour): the period picked on one page is kept on every page until the next term starts. Off: nothing is stored and each page opens on the newest term with the reader's courses - saving it forgets the current pick at once. Migration `020_remember_period`.
- **Course Management has a Status filter** (all, active, archived) beside the period, and a course's row - or its code - opens the course; an archived one opens read-only.

### Fixed

- **A link opens the view it is about.** "N archived courses, reactivate one" opens Course Management on those courses' term with the Archived filter set, instead of whatever term the reader last picked. The support ticket items open the course's own ticket list (with Status set when the tickets are all open) or the overview across every term - their `?status=open` on the course overview had filtered nothing since it became a table of courses.
- **Archived courses can always be reached.** The Dashboard counted only active courses when deciding whether the reader "has courses", so once every course was archived its period selector vanished, it offered "create your first course" and the activity feed said the same. It now counts every course; a term with no courses names the newest one that has them, with a button to go there, and a term whose courses all ended says so above its Archived Courses card. Students reach their finished courses the same way.
- **A filter a link sets is applied, not only shown.** Dropdown filters are written to the address as they change (as the search is) and read back on load; the select component renders its value before Alpine starts, so a table filter reading it on load no longer saw an empty value. The ticket list stopped filtering on the server as well, where "All Statuses" could not bring back the rows it had dropped.
- **The selected filter no longer blinks when a page is swapped in.** htmx's attribute settling gave every element whose id existed on the page before its OLD class for ~20ms, then the new one - a selected tab, filter or period box turned off and back on, and a row the table filter hid right after the swap came back. Nothing used the settle transitions, so settling is off.
- **The Academic period field fills its row on an archived course's settings.** The read-only guard wrapped the field's two hidden inputs for a tooltip, and the wrappers took two thirds of the row; hidden inputs are never wrapped now.

- **The search and filters of a table sit in the middle of their band.** The band left 8px under its controls while the card body left 24px above them, so the search sat 26px below the card's edge and 11px above the line under it. The room under the controls is now the card body's own padding (`--card-body-pad-y`): 24px above and below on a desktop, 12px on a phone - where the band's own 4px copy is gone. Bands with tabs keep their tabs resting on the line.

## [2026.9.30.post86] - 2026-09-26

### Added

- **The support tickets overview filters by period and status.** The period selector every list of courses has - the remembered pick, *All periods* one click away - and a Status filter that keeps only the running or only the archived courses; a term with no courses says so in the table.

### Changed

- **Support opens with the same table of courses as Support Tickets** - one component for both pages (`partials/support/_course_table.html`): term, status, the period and Status filters, and the reader's OWN requests per course (open, total, the last one), so a student sees that last week's question is still waiting before writing it again. A *New request* button starts one. It replaces the card picker and its collapsible *Archived Courses* card.
- **The Events webhook warning is a toast again, raised once.** Post85 moved it to an inline alert that showed only for active courses, so a deployment with no active course (production) had no warning at all. It is a toast on arrival again, and never a second copy: still on screen - carried over from the page before, reopened or reloaded - it is left as it is.

### Fixed

- **A selected filter no longer blinks while its page loads.** Every in-app navigation stepped the whole content back until the next page landed, including one that only changes the query - the period, a sort, a page of the same list - so the filter just picked faded out and came back. A navigation within the same page now keeps the controls at full strength and steps back only the rows; a different page still steps back as a whole.
- **The period box says the pick at once**, the way a select does - it kept the old term until the page landed - and the focus comes back to it after the page lands instead of dropping to the top of the page.
- **A repeated toast is visible again.** Raised again while it was still up, a toast only knocked 8px and read as "nothing happened"; it now replays its entrance, rings in its own colour and counts *x2*, *x3* beside its title - still one toast, never a pile.
- **Every table card has the same frame on all four sides.** The card body pads 24px, but the pagination bar under a table still assumed 16px: it sat 8px inside the body's edges and only 12px under the last row, against 24px above the table's controls - on every paginated table, with a stale copy of the bar's margins at each breakpoint. The card body now publishes its padding (`--card-body-pad-y` / `-x`), breakpoints change those, and the bar takes its margins from them: 24px on desktop, 12px on a phone, 8px on a small one, the bar flush to the edges.
- **The support course tables' row action is an icon with its tooltip**, as every row action in the app (a new `btn_link_icon_only` - the link twin of `btn_icon_only`). Spelled out, *New request* made the column too wide to stay pinned on a phone and it scrolled out of reach.

## [2026.9.30.post85] - 2026-09-26

### Changed

- **The support tickets overview is a table of courses.** One row per course: its term (a badge, highlighted for the running term), Active or Archived, open tickets, total, the last ticket and a View link. Active courses first, archived after them - an open ticket on last summer's course is still an open ticket, so nothing is hidden behind a disclosure. Every column sorts; search narrows by code, name or term. It replaces the card picker whose *Archived Courses* card stalled when it opened and closed.
- **The webhook state on Events is an alert on the page, not a toast on every visit.** Active courses only - an archived course receives no events by design, so it made the warning permanent - and each silent course is named with its term and linked to its webhook settings.
- **A toast already on screen is not raised a second time.** Asked for again (a poll, a refresh, a second click), the one on screen knocks and rings in its own colour and its countdown starts over, so it gets the full time to be read; under reduced motion only the ring fades.

### Fixed

- **Collapsible cards open and close smoothly.** `x-collapse` measured the padded card body and stalled at the height of its own padding before snapping shut; it now animates a bare wrapper around the body - every collapsible card, and the weekly deadlines disclosure.
- **The term is named wherever a course is listed**: User Info (each course and each group's course, as badges), the Events *Where* column, team results in the search palette, the Support ticket and form headers, the Run Checks dialog, the dashboard's lifecycle items, and the archive, activate and delete confirmations.
- **Support says when the course is archived** - the archived strip, saying that requests still reach its teachers rather than "read-only".
- **Purge Old on a course's tickets clears that course only.** It deleted the finished tickets of every course of every term while the dialog named none; the dialog now names the course and its term.
- **Deleting a course from its Settings asks for the course code.** The button carried no code, so the dialog asked the reader to type the course's UUID.
- **No "assigned to you" toast on a ticket** - the banner at the top of the page already says it, for as long as it is true.

## [2026.9.30.post84] - 2026-09-26

### Fixed

- **Every row of User Management says which term a person is in.** The Period column printed a dash for every teacher, administrator and service account, so "no term" and "every term" looked the same. A student shows the terms of their groups' courses (or *No period*), a teacher the terms of the courses they own or teach (or *No courses*), an administrator and a service account *All periods* - each with a tooltip saying why.
- **A service account no longer reads as a student.** Its Role cell showed the role GitLab sync stored for it; it says *Bot* now, like the badge beside its name.
- **Support tickets say who is who.** The submitter, the assignee and every comment author carry the same role badge User Management uses - Teacher, Admin, Student or Bot - instead of a bare username. One lookup per page, by the GitPulse or the GitLab username.
- **The Support course picker keeps archived courses apart.** Active courses first; archived ones in a collapsed *Archived Courses* card - the Dashboard's own component - still reachable for a question about last term, but no longer between the courses running now.
- **A card header no longer spreads its own items apart.** With nothing at its right edge, `space-between` put the icon left, the title in the middle and the count at the far right; the header starts at the left, and the parts that belong at the right keep their `margin-left: auto`.
- **No dead strip under a collapsed disclosure.** A closed `<details>` card kept 4px of gap under its header (9px below *Raw Check Details*, 5px above); the gap now lives on the body and goes with it.

## [2026.9.30.post83] - 2026-09-25

### Changed

- **One "Academic period" field instead of three.** Create Course, Import from GitLab, Edit Course, Transfer to New Semester and the course Settings each had a year list, a semester list and a "Quick preset" list - three controls for one choice - and the year list offered a fixed six-year span, two of those years already over, with nothing saying which one was now. Every one of them now asks the same way: one field listing the term the TUKE calendar is in (marked *current*, or *upcoming* between semesters) and the terms after it. Import alone also offers the last year's two terms, marked *ended*, to bring in a finished course for its history. Transfer never offers the term the course is already in.
- **A term and its dates are one fact.** Picking a term fills its official TUKE dates. Change the term and the dates move with it - as long as they are still the official ones; dates the teacher typed stay, and a start date that then falls in another term is pointed out under the fields, as is an end before the start. **Use the official TUKE dates** puts the calendar back after a manual change; a term the calendar does not publish yet says so instead of leaving two silent blanks. One component (`period_fields`) and one script (`academic-period.js`) replace the three private copies of this logic.
- **The period selector is a filter like the others.** It wears the same control as the Events type/status filters instead of a secondary button with its own look, and every option says what it means on hover - *All periods*, *No period* (students not in a group yet), *Current*, *No courses*. A finished term that holds nothing is no longer listed; terms with courses stay, however old.
- **The pick is remembered** - in localStorage, the way the interface language is, mirrored into a cookie so the page arrives already scoped instead of jumping - until the next term starts; then the pages follow the calendar again. A link that names a period always wins.
- **The top bar names the term**, *2026/2027 · Winter*, from the same rule as the selector (its tooltip says Current or Upcoming); on a phone only the year fits beside the clock.

### Fixed

- **Transfer to New Semester ended in a server error.** The service read the new course's settings through a relationship the async session could not load (MissingGreenlet), after the clone was already written. It reads them with a query now; a regression test fails the way the real relationship did.
- **A transferred course's deadlines moved to the weekend.** Dates were shifted by calendar years - a Monday start became a Tuesday, a Friday deadline a Saturday. The new term gets its official dates, and every deadline moves by exactly as much as the start did, so the Friday of week 5 stays the Friday of week 5; across a change of term the week structure is now kept instead of dropped.
- **The Dashboard's live refresh described a different term than the page.** The stats cards and the activity feed re-fetched on every SSE push and tab return without the period, so they switched to every term at once beside a grid of one. All three refreshers and the page now scope through one function, and the stats cache key carries the period.
- **The "Students" card counted every student account in the installation** - for a teacher too, under their own two courses. It counts the students of the courses on screen, captions every scoped card with its period instead of "Current semester", and links to the page that shows the same number.
- **An empty term told the reader they had nothing.** "Create your first course" and "You are not enrolled yet" appeared on a term that was merely empty; the housekeeping items (a semester that ended, last year's course to transfer) vanished whenever the page opened on the newest term. They now look at all the reader's courses, and "new academic year" suggests Transfer - reactivating last year's course would have filed this year's students under last year.
- **The period badges ran over the Status column** of User Management. They have a column of their own, and wrap.
- **Menus were cut off by the page, not only by the screen.** A menu that opened inside the screen but past the edge of the content area lost its first letters. Every dropdown now fits the box that clips it and flips to the toggle's other edge before being pressed against it.
- **No validation of a period on the way in.** Any string was accepted as a year or a semester by the REST API, the GitLab import and the JSON config import - "2026/2028" or "Winter" put a course into no period at all. One rule now (two consecutive years, `winter` / `summer`) on every way in; a stored semester date is no longer re-judged by the moving two-year floor, which blocked saving any setting of an older course; the create and REST settings endpoints check the date window like the settings page does.
- **Import into an existing course** only offered the courses of the term on screen; it offers every active course.
- **Two confirmation texts stayed English** on the Slovak settings page (the semester-window warning and the full-sync prompt): their catalogue keys carried the line breaks. One key per sentence now, with a test.

## [2026.9.30.post82] - 2026-09-25

### Added

- **Academic period scope.** The Dashboard, Course Management and User Management each carry a period selector - one academic year and one semester, e.g. *2026/2027 · Winter* - that decides which courses and which students the page is about. It lives in the URL (`?period=2026-2027-winter`), so a cohort can be linked to and bookmarked, and the page works with no JavaScript. Every term of every year is listed, winter and summer, including ones with no courses (marked **No courses** rather than left out); **All periods** shows everything; and on User Management **No period** lists the students who are in no group of any course yet - the one who signed in through GitLab before their group was synced, who was otherwise invisible in every period.
- **Only students are narrowed.** Administrators, teachers and service accounts appear in every period: they are not tied to a cohort, and a User Management that lost its own admins when the term turned over would be worse than no scope at all. Measured on the dev data the partition is exact - every student lands in exactly one of "a period" or "No period", none in neither.
- **The term on every course-scoped page.** Group, student and project pages had no term on them at all, so with the same course running in two terms "tim-03 · ZSI-DEMO" was ambiguous. Each now carries the term as a badge next to its title, highlighted when it is the one running. Every period string in the app - nine of them, built by hand in eight templates with two different separators - now goes through one component.

### How the period is decided

- **The page opens on the newest term that holds courses *the reader can see*** - not the calendar's. A deployment running only summer courses is in "winter" for half the year by the calendar, and opening every page on an empty table would be technically right and useless; and computed from the whole database, a student whose only course is last summer's would have opened their dashboard on somebody else's newer term and seen nothing. The calendar's answer is still shown, as **Current** next to whichever term it is - or **Upcoming** between two semesters - so the two are never confused.
- **A period is defined at every date.** The TUKE preset table ends on 2027-06-25 and `current_semester()` returns nothing after it; between two semesters it names the next one. The new `calendar_period()` keeps answering past the table by the shape of the TUKE year, so no page loses its period the day the table runs out.
- **A student is matched to their course the way the rest of the app already does it.** Students reach a course through `Team -> TeamMember -> Student`, not through `course_memberships` (which held no student rows at all), and are matched to their user account by username - the rule the User Info modal uses - so the table and the modal cannot disagree about who belongs where.

### Fixed

- **Two dialogs on the same page disagreed about the default semester.** Import from GitLab pre-filled *summer* and Create Course *winter* (its first option). Both now pre-fill the term the page is showing, or the calendar's.
- **New courses defaulted to the year the server booted in.** The import dialog read `suggested_academic_year`, a string captured at startup - a process started in July kept offering the previous academic year all autumn. The default is recomputed on every render now.
- **Transfer to New Semester proposed the term the course is already in.** It used the source course's own semester plus that boot-frozen year, which before the August rollover is a duplicate the create API refuses. It now proposes the same term one year later.
- **The User Info card and the config-import preview printed the raw column** - *2026/2027 · winter*, lowercase and English on a Slovak page. Both use the translated label now; *Summer* was also lowercase (*leto*) in the Slovak catalogue next to a capitalised *Zima*.
- **Dropdown menus could open off the screen.** A menu is anchored to one edge of its toggle and nothing asked whether the other side fitted: on a phone, a toggle at the left of the screen opened its menu 34-51px past the left edge. Every menu - portaled or not - is now kept inside the viewport, without touching the `transform` the open animation owns.
- **An empty term would have stranded the reader on the Dashboard.** The "create your first course" branch hides the section header, and the period selector with it; an empty term now keeps the header and says *No courses in 2025/2026 · Winter*, not "create your first course".

## [2026.9.30.post81] - 2026-09-23

### Fixed

- **The date and time in the header did not sit on the row.** Every box up there is centred by the layout engine, so nothing looked wrong in the CSS - the misalignment was INSIDE the boxes. `align-items: center` lines up boxes, and a 21px line box around 14px digits carries the font's full ascent, room for accents that "2026/2027" and "23.09. 14:03" never use, so the ink of those digits landed about a pixel below the middle of its own box. Measured from the rendered pixels: the search button, the avatar and the chips' own icons all had their ink centred on 23.75 and the text alone sat at 25.0. `line-height: 1` collapses the box onto the em and the ink lands where the box already is - checked with the web font and with it blocked, since `font-display: optional` means a phone without it cached renders the page in the fallback.
- **Pressing an unavailable control now says why, whatever made it unavailable.** The reason rides on a wrapper around the control, because a disabled control emits no pointer events of its own - and the tooltip carrying it is hover-only, so on a phone a press is the ONLY way to ask. The handler answered for exactly one cause, the archived-course lock; anything disabled by a running process or a permission had its reason sitting on the wrapper with nothing to read it out, so it stayed mute and the reader could not tell "not allowed yet" from "broken".

## [2026.9.30.post80] - 2026-09-23

### Fixed

- **Four stylesheets each silently dropped their first rule.** A sweep that removed dead selectors left a lone `/` on line 1 of five files where the rule it opened used to be. CSS error recovery does not stop at a stray character - it swallows it TOGETHER WITH the next selector and carries on - so `.badge-beta`, `.badge-check`, `.analysis-progress-success` and `.icon-32` never applied at all, on production, with no error anywhere and every other rule in the file working normally. The strays are gone, and `test_stylesheets_parse.py` now checks every stylesheet for the whole class of leftover: stray text between rules, unbalanced braces, an unterminated comment. Every JS source, every built artifact and all 107 templates were checked the same way; nothing else was broken.
- **Opening any modal on a phone raised the on-screen keyboard.** Focus went to the first field on every device, which is a hardware-keyboard affordance - on touch it covers half the dialog before the reader has decided to type, and on a modal with nothing to type into (Run Checks is tick-the-boxes-and-press-Run) it hid the very list being picked from. A focused field also collects whatever the keyboard then emits, so closing answered "You have unsaved changes. Discard?" for something never typed. On a coarse pointer the dialog itself takes focus now; Escape, the focus trap and the screen-reader announcement are unchanged, and the desktop behaviour is exactly as before.
- **A tooltip gave a disabled button a live cursor.** `[data-tippy-content]` sets `cursor: pointer` at the same specificity as `.btn:disabled` and later in the cascade, so every disabled button that carries a tooltip - which is every bulk action over a selection - showed the pointer of a working control while its colours said disabled.
- **The tour's Back button on step 1 looked enabled and did nothing.** Driver.js disables it on the first step and Next on the last but ships no styling for that state. Both now use the same disabled tokens as every other control in the app.
- **The dirty guard swallowed the edits made fastest.** Its late re-snapshot was documented to skip a modal the user had already started editing and never checked it, so a value typed within 600 ms of opening became the baseline and closing asked nothing.

### Changed

- **Icons are back on the scale.** layout.css defines five steps (12/16/20/24/32) and the Jinja macro and `GP.iconSvg` both emit them - but thirteen one-off sizes had grown around them: 10, 11, 13, 14, 15 and 18px, plus a second pixel-named scale in pages/shared.css (`.icon-12/14/16/20/22/32`) of which nothing used a single step except `.icon-22`, itself a size the real scale does not have. Every one is snapped to the nearest step and the duplicate scale is gone.
- **The top bar's date and clock icons sit on their text.** They were 12px beside 14px text; the pairing this app follows, stated in layout.css and again in cards.css, is 16 beside 14 - GitLab's own. The MR section labels (Description, Commits, Changes, Activity, Discussions) had the same mismatch and the same fix, and the LLM error card's mark now matches the size its JS-built twin draws.

## [2026.9.30.post79] - 2026-09-23

### Fixed

- **Every failure mark in the app was drawn grey.** `.table-empty-icon--danger` sat ABOVE `.table-empty-icon` in tables.css and the two carry the same specificity, so the base `color: var(--text-tertiary)` won and the red never applied - the alert triangle on a failed table, chart, modal or card was the same colour as the "nothing here" mark beside it. The modifier now follows the base rule.
- **The course-card sync badge drew two spinners.** When the shared spinner was put in front of the JS-injected badge, the hand-drawn ring behind it was left in place - along with a `</span>` that closes nothing. A badge injected by a live update carried two marks and malformed markup; one rendered by the server carried the correct single one. The badge is now exactly what `components/cards.html` renders.
- **Three strings reached the screen untranslated** on a Slovak page: the sync failure detail ("Unknown error"), the queued-sync cell ("Sync queued...") and the "Not yet required" aria-label. The Slovak was already in the catalogue in all three cases. A fourth, "Failed to upload attachment.", was missing from the catalogue outright and is now in it.

### Changed

- **One JS icon registry, not four.** `GP.icons` (icons.js, 122 Pajamas glyphs generated from `components/icons.html`) has been in the bundle all along, and three more tables had grown beside it: `GP._ICON_PATHS` in core/00-base.js, `_toastIcon` - seven hand-written Feather glyphs on the component every page shows most - and the Done/Failed button marks, one of which had drifted into a hand-drawn tick rather than the `check` every other confirmation uses. All of them are gone; `GP.iconSvg` is now the size-token front door onto the one registry, and the dropdown chevron that was inlined at 12x12 comes from it too. `test_every_icon_name_resolves.py` now fails on any private icon table.
- **Three more hand-rolled empty states** became the app's one empty block, with a mark: a check with no configurable parameters, a course section filtered to zero, and an MR with no analysis history. "No courses in this section" also spans the grid now instead of sitting in its first column, which read as left-aligned under a full-width heading.
- **Two error states gained a way back.** The event-detail modal and the MR-history modal both failed to a dead end - the only exit was closing the modal and finding the row again. Both now carry the Retry the User Info modal got, with its loading state. The event modal also uses the shared loading block rather than a row of utility classes around a spinner.

### Verified

- Every page walked as every role at 1440 and 390: no empty icon boxes, no leftover 24x24 glyphs, no duplicate ids, no horizontal overflow, no stuck loaders, no JS errors.
- Every safe control pressed and watched through its whole cycle: each shows a state and recovers it.
- All nine declarative modals opened and their openers pressed again while open: none re-opens or replays its entrance.
- Toast marks, button outcomes and the error block checked in both themes.

## [2026.9.30.post78] - 2026-09-23

### Fixed

- **The User Info modal opens again.** Last release's dead-code sweep counted uses of `GP.ensureUserInfoModule` without reading the page scripts, so it removed an export that `pages/admin-users.js` calls - and User Info answered "Failed to load user info" without making a single request. The export is back, with a comment saying who calls it, and every other symbol that sweep removed was re-checked against source, templates, scripts, tests, the docs site and the Caddyfile.
- **A modal no longer re-opens under you.** `openModal` had no idea whether its modal was already open, so every path that re-enters it to repaint the body - Retry in an error state, a reload inside a modal, a second click on the control that opened it - scrolled the body back to the top, restarted the grow-from-the-trigger animation, faded the backdrop in a second time and pulled focus back to the first field. It is a no-op on an open modal now; a modal mid-close still re-opens properly.
- **Icons that drew nothing now draw.** `GP.iconSvg` is the mirror of `components/icons.html` for JS-rendered markup, and it had drifted: four of the names asked for it (`alert-circle`, `alert-triangle`, `clock`, `search`) were simply absent, and an absent name answers with an empty string - an empty, padded icon box where an error state's alert mark belongs. 15 of the 25 icon requests in the app's JS were hitting that gap.

### Changed

- **One icon set, everywhere.** The JS mirror had also stayed on the 24x24 stroked Feather glyphs the app moved off, and five more files carried private icon tables of their own - the User Info card, the global job bar, the support-ticket page, the LLM error card and the webhook rows. A JS-rendered icon and the server-rendered one beside it were two different icon families. All of them now resolve through the one mirror, regenerated from `icons.html` (Pajamas 16x16, filled), and `test_every_icon_name_resolves.py` fails if the two ever drift again.
- **One error state in the User Info modal, with a working Retry.** Both copies rendered a bare red paragraph and a hand-built button; they now render the app's error block - alert mark, message, retry - and the Retry button carries the loading state while it re-fetches. The modal also paints its spinner *before* fetching the card renderer rather than after, so a click on a slow connection is answered immediately instead of showing nothing until the script lands.
- **The error pages' buttons have a state.** Retry and Search both navigate, which on the connection that produced the error is not instant - and they went silent on press, which reads as a dead button and invites a second press. Both show the app's spinner now, sharing its one `spin` keyframe (`animations.css`, newly loaded there for it) rather than defining a second, and a bfcache restore clears the state instead of handing back a disabled button.
- **The support-ticket page speaks Slovak.** Every label it paints from JS - Timeline, Last updated, Reopen and comment, Close with comment, Comment, the assignment toast - was English on a page whose server-rendered half is translated. The Slovak was already in the catalogue; there was simply no `t()` in the file to reach it.

### Removed

- **The scroll offset no reload reads.** `reloadKeepScroll` saved the page's scroll position to `sessionStorage` before every reload and `clearReloadScroll` cleared it before every row navigation, but the restore they fed was replaced some time ago by `_resetScrollOnLoad`, which starts every load at the top on purpose. Reading the offset also forced a layout on the way out of the page. The write, the two readers, the clearing helper and its two exports are gone; the silent-reload flag theme-bootstrap reads pre-paint stays.
- **A deeper pass over what nothing reads:** 166 orphaned Slovak translation keys left behind when three sandbox features were deleted, 11 phantom routes in the API spec, 9 unused support schemas, 3 unused template macros with their imports, and the CSS for the classes those changes orphaned.

## [2026.9.30.post77] - 2026-09-22

### Removed

- **Dead Code Swept Out of the Repository (about 1 000 lines):** every top-level function, class and method in `src/app` was checked for a reference anywhere in the codebase (source, templates, JS, tests, compose files, scripts), and the CSS classes against every template, script and Python file. What went:
  - **22 settings for machinery that does not exist**, led by the `SCHEDULER_*` intervals: GitPulse is webhook-driven and the worker states it outright ("There are no recurring/cron jobs"), so the five scheduler intervals, the two sweep batch sizes, the DLQ resurrection pair, the unprocessed-event threshold, the three retention/interval knobs, `WORKER_MAX_RETRIES`, the three GitLab cache TTLs and the four rate-limit/socket-timeout leftovers had no reader at all. Also dropped from `.env.example` and `.env.production.example`.
  - **Six write helpers on the GitLab client** (`_post`, `_put`, `_delete` and their dict wrappers). GitPulse never writes to a student repository, so nothing called them - and they were the only way the client could have. The class is GET-only now, which is the read-only promise in code rather than in a comment.
  - **Four event-repository methods** (`mark_processed`, `mark_failed`, `move_to_dead_letter`, `get_unprocessed`) left over from a polling design that webhooks replaced, and the per-user session index that existed solely for a force-logout nobody calls.
  - **The hex colour palette in `constants.py`** (traffic light, severity, pass/fail) - those colours come from CSS tokens now - plus `traffic_light_color`, `has_closing_reference`, `contains_commit_reference`, `is_before_deadline`, `raise_too_many_requests`, `_gitlab_preflight_status`, `_is_job_like_audit_action` and the deprecated `_compute_build_hash` wrapper.
  - **Two unreachable "legacy viewer role" branches** - the schema has rejected that value since the role was renamed, so neither could ever run.
  - **Five dead JS entry points** (`GP.ensureUserInfoModule`, `window.clearGlobalJobDismissals`, the tour's `isPageBusy` alias, the import queue, `_isOnCooldown`) and **26 CSS rules** for classes no template, script or macro produces.

  Every removal was verified by search before deletion and the whole suite, the type checker and a screenshot pass over every page in both themes at desktop and phone width ran after it.

## [2026.9.30.post76] - 2026-09-22

### Changed

- **Home Greeting Is GitLab's, on the PC and on the Phone:** measured on the department's GitLab (its Your work > Home page): a 64px avatar, the name at 20px semibold (18px on a phone - Pajamas heading-scale-500), the one-line sentence at 16px, the pair centred on the avatar with a 16px gap - and the same on both. GitPulse drew the name as a 30px page title, and on a phone shrank it to 24px with a 48px avatar and then re-aligned it on its own. Now the greeting is the same shape as GitLab's everywhere.

## [2026.9.30.post75] - 2026-09-22

### Fixed

- **Home Greeting on Phones Matches Every Other Page Header:** every page title keeps its 30px on a phone (20px below 360px) - the home greeting was the one title that shrank to 24px, and its avatar was vertically centred on a block whose phrase wraps to two or three lines, so it floated between the name and the sentence. The name is now the same size as every other page title, and the avatar sits on the name's line, both at 390px and on the narrowest phones.

## [2026.9.30.post74] - 2026-09-22

### Fixed

- **The Focus Ring No Longer Disappears Under the Pointer:** `.form-input:hover:not(:disabled)` outranked `.form-input:focus`, so the pointer resting on the field being typed in swapped the blue focus ring for the grey hover border - and the same on checkboxes, radios and search boxes, while buttons kept theirs, which is why "somewhere it disappears, somewhere not". Hover now yields to focus on every control that has both (measured by keyboard-focusing every control on every page, then hovering it). Two controls drew no keyboard focus ring at all - the filter tabs above tables (a `box-shadow: none !important` reset) and the Light / Dark / Auto segments on Preferences (page overrides at higher specificity) - both ring now; the quick-access segments on the dashboard use the inset ring every tab strip uses.
- **Empty States:** the Markdown editor's Preview tab on an empty description was a blank 200px box; it now says "Nothing to preview." like GitLab's. Every server-rendered table was checked for an empty branch - all have one.
- **Consistency Sweep (every page, every shared component measured):** four JS-rendered checkboxes (check on/off in Compliance Checks, the weekly-deadline check picker, LLM suggestions, event rows on Events) were the browser's native control beside the GitLab-styled one; they use `form-check-input` now. The weight-preset buttons on Course Settings re-implemented the secondary button with a transparent background and their own hover - the override is gone. The filter tabs above tables carried a 44px minimum height on the desktop (the touch target, written outside the touch stylesheet), standing taller than the tabs in every card header.

## [2026.9.30.post73] - 2026-09-22

### Fixed

- **One Manual Refresh After a Deploy Became Two, and the Second Landed Mid-Scroll:** when a release ships a new service worker, it claims the open page and `controllerchange` fires; the page reloaded itself on that alone, held back only by a ten-second settle window. Right after a server restart the worker's install runs past any window, so a page the reader had just refreshed reloaded again fifteen seconds later - out from under them while scrolling. Taking control of a page says nothing about that page being behind; the server's `X-App-Version` does. A new worker now asks `/dashboard/session-check` and hands the answer to the existing version check, which reloads once, only when the page is actually behind, at a quiet moment, with the "new version" notice. A page that is already current never reloads twice.

## [2026.9.30.post72] - 2026-09-22

### Fixed

- **Charts Follow the Theme, on the First Frame:** Chart.js is a per-page script that loads after the core bundle, so the theme's chart defaults were applied to nothing - every chart drew its ticks in Chart.js's own `#666`, its labels in Helvetica and its tooltips in the library's black box until the reader toggled the theme. The defaults are re-applied on `DOMContentLoaded`. In dark mode the grid and the skill radar's web were invisible: they took `--gl-border-color-subtle`, which is exactly the chart surface's colour there; a per-mode `--chart-grid` token keeps them one step lighter.
- **Score Trend, Made Readable:** the dashed threshold lines sat at a hardcoded 70/40 while the pills under the chart printed the course's 80/50 - the lines, the point colours and the legend now all come from the course (`green_pct` / `yellow_pct`), and each threshold line is labelled with its value at the right edge. The zone bands, threshold lines and point rings resolve the theme's colours at draw time, so a mode switch repaints them; the area under the line is the brand colour the line is drawn in (accent themes filled under a blue that belonged to no theme). The Skill Profile uses the app's category tokens (Issues / MRs / Review / CI/CD) instead of a traffic-light palette that read as good/bad.
- **The Install Card Is Back:** the app's own "Install GitPulse" card was gated behind a flag nothing set since July, so only Chromium's omnibox icon remained and "the install popup stopped appearing". It is on again (`data-custom-pwa-install` on `<html>`), and its strings go through the catalogue - they were looked up by dotted keys the catalogue never had, so the card was English on a Slovak page.
- **Language Names Stay in Their Own Language:** the switcher listed "Angličtina" on a Slovak page; the client-side translator now honours the HTML `translate="no"` attribute and the switcher carries it, so "English" and "Slovenčina" read the same whatever the page language.
- **Twenty-nine Untranslated Toasts and Prompts:** the HTTP error toasts ("Access denied", "Network error - check your connection", "Server error - please try again", "Too many requests...", "Validation error", timeouts, conflicts), "Tour history cleared.", the import cancel dialog and a few more reached a Slovak reader in English. All added to the catalogue, and `find_missing_translations.py` now scans the JS aliases (`tx`, `_t`, `GP.t`, `_translateUiText`) that hid them.

## [2026.9.30.post71] - 2026-09-22

### Fixed

- **On an Archived Course Every Read-Only Button Died After One Use:** the loading reset locked *every* button under `.is-course-archived` after its first use unless someone had remembered to tag it `data-readonly-ok` - while the read-only guard itself (which decides what is a write on an archived course and marks it) had left those buttons live. So Reload on the student's Compliance Progress card, and any other untagged read-only action, worked once, showed its tick and then sat greyed out with the disabled colours - "after the done state the button is unavailable", on every archived course, wherever a tag was missed. The reset now keeps disabled only what the guard marked (`data-archived-locked`); the guard remains the single owner of the read-only rule.
- **The Green Tick Had a "Strip" on Its Right:** the outcome word ("Done"/"Failed") was only hidden below 768px, so inside a 24px icon-only button it shrank to a 2px sliver of its first letter beside the mark and pushed the mark off centre. A control whose resting label has no text now carries the word as accessible name only, at every width.
- **Demo Course Seed - a Whole Semester of History:** `scripts/seed_demo_course.py` let the compliance engine write one snapshot (the current week), so the student's Compliance Progress card in the demo course was a lone dot at W11 - the "incomplete chart" in the screenshots. Weeks 1..N-1 are now derived from that result: the checks the student passes today pass one after another in earlier weeks, and each week's score is the sum of the passed weights, exactly as the engine computes it.

## [2026.9.30.post70] - 2026-09-22

### Fixed

- **Button Icons Were Too Small - the Card-Header Reload Was a 6px Glyph in an Empty Square:** `.card-header .card-actions .btn` padded every header action 8px a side and beat `.btn-icon-only { padding: 0 }`, so the 24px Reload on the student's Compliance Progress card had 6px of content width and its icon rendered 6px wide - an empty grey square that read as a disabled control before and after every reload (the button itself was fine: measured enabled with its resting look restored). On top of that the app carried a ladder of icon sizes inside buttons - 13px in card headers, 14px on `.btn-sm`, 14px on phones - where GlButton draws 16px at every size. Every button icon is now 16px (`.btn-xs` keeps 12px), the macros ask for the same, and an icon-only header action is a 24px square on touch too. A small button no longer changes width while loading, since the 16px spinner now replaces a 16px icon.

## [2026.9.30.post69] - 2026-09-21

### Fixed

- **Buttons Stayed Locked Through the "Finishing" Hold - Also After a Reload:** the job bar holds a finished sync or check run on "Finishing..." for eight seconds so it can be read, and a reload restarts that hold. The process locks counted it as a running job, so Link Project / Sync / Run Checks / Delete stayed disabled for the whole hold - a four-second check run left the header dead for a quarter of a minute - and a reload during the hold ended with a generic "Sync completed!" for a check run. A finishing job now holds no lock (`isJobActive`, `isGlobalJobRunning`), the Run Checks button stops spinning when its job enters the hold, a restored hold finishes with its own wording ("Checks completed!"), and a late progress answer can no longer overwrite "Finishing..." with the run summary while the spinner is still turning. Dismissing the bar during the hold still lets the completion fire.
- **A Failed Sync Came Back Reading "Failed" for Good:** the failure toast painted the button's red outcome before the handler applied the 5 s cooldown, so the cooldown snapshotted that outcome as the label and restored it when the countdown ended - "Failed" as text inside the icon-only row button, its icon gone, its accessible name and tooltip removed. The cooldown now retires the outcome first and hands back the button's own aria-label and tooltip after "Wait Ns".
- **Submit Buttons Went Dead for Five Seconds With No Loading State:** the double-submit guard deferred its check to a microtask, which the browser runs *between* the listeners of a user-fired event - so it saw `defaultPrevented=false` for every AJAX form and disabled the submit button (with a `btn-loading` class no stylesheet defines) until its 5 s fallback. It now defers past the dispatch and uses the app's one loading state, so a navigating submit looks like every other working button.
- **Finished Jobs in the Bar Wore the Default Clock:** scoped job keys (`sync:team:<id>`, `run_checks:course:<id>`, a course sync keyed by its id) had no entry in the icon table; a completed sync or check run now shows its own mark.

## [2026.9.30.post68] - 2026-09-21

### Fixed

- **"Refresh stats" Never Said It Worked:** the shared `coalesce()` helper resolved to `undefined` instead of the loader's answer, so `loadSystemStats()` always read as a failure and the System page's refresh ran silently. It now resolves to the loader's result (a rejected loader reads as `false`), with a node-backed test pinning it. Every coalesced live refresher (dashboard stats, attention items, activity feed, course/team/project live data) gets a truthful result too.
- **Check Details in Slovak:** the compliance engine's detail texts ("0/2 distinct reviewers on own MR", "MR not yet merged", ...) reached the reader in English inside a Slovak page - the student's attention item, the project page's Issues to Address card and its live-data bottleneck list. Every detail form the engine produces now has a catalogue pattern (numbers substituted by position), and those three surfaces translate through it.
- **Slovak Catalogue Gaps Closed:** 28 source strings had no translation (card help texts on Groups, Teachers, Users and Analytics, "Loading jobs...", "Copy JSON", "Processing Error", "Tickets", "per page", ...) - all added; `find_missing_translations.py` reports zero.
- **Phones - Consistency Pass Across Every Page:**
  - Course card footer: once the at-risk chip pushes the buttons onto their own row they sit flush left, like every other wrapped action row, instead of hanging off the right edge.
  - Tables whose actions column is too wide to stay pinned (`sticky-column-off`) show the right-edge scroll fade again - it was hidden for every sticky-actions table, so admin Courses at 375px cut "Základy softvérového inžinier" with no hint that it scrolls.
  - Tab strips (page tabs, filter tabs, card-header tabs) fade at the right edge when they run past a phone's width; the last tab used to be cut in half with nothing to say more follow. `table-scroll.js` marks `.tabs-nav` with the same two classes as tables.
  - Student page: commit rows are two lines (message, then "+n -n" and the time on one meta line) instead of three, and the message is no longer cut at twenty characters - the two empty badge slots kept their desktop 4.5rem each; the "+n / -n" pair in the profile strip is one stat, so it never splits across the two-column grid.
  - Analytics: the teacher's checklist chart labels are two lines (code, then name) below 480px with auto-skip off - "R07 Recenzia kódu poskytnutá" lost its "R0" at the canvas edge and every other label was skipped.
  - System page: "Purge old", "Refresh", "Check now" and "Check status" fold their labels into icons on phones like every other card header action (the Events page already did).
- **Tooltips Where They Were Missing:** the course card's "View" and "+ Group", the group rows' "View", the "Show all (n)" / "Show less" disclosure, the weekly-deadline JSON toggle and the health card's "Raw JSON" toggle; the disabled remove button on the Teachers page has an accessible name.
- **Rotate Webhook Secret** shows the row button's loading state while the server rotates.

## [2026.9.30.post67] - 2026-09-21

### Fixed

- **Slovak Interface Completed on the Home and System Pages:**
  - The greeting phrase under the reader's name is translated through the catalogue (30 Slovak entries), so a Slovak dashboard no longer opens with an English aphorism.
  - Every job type and audit action in Job History and in the activity feed has a Slovak label (42 catalogue entries, 17 job types added to the JavaScript label map, purge/delete/project-sync actions added to the feed map); "Score" column header is capitalised like its neighbours.
  - The checks card, the weekly deadlines card and the import dialog say R01-R13 instead of the outdated R01-R12.
- **Dev Login Keeps the Stored Full Name:** a seeded account logging in through the development form is greeted by its full name instead of its username.
- **Security:** `anyio` 4.14.0 -> 4.14.2 (CVE-2026-63374, CVE-2026-64847, CVE-2026-63349), which un-breaks the `dependency-scan` CI job.

### Changed

- **README Screenshots and Demo Course:** the three README screenshots (teacher overview, group, student's own view) are retaken from the current build in the light theme and Slovak; the demo seed creates a `ZSI-DEMO` course for 2026/2027 instead of `ZDEVOPS-DEMO` for 2025/2026; documentation status date 2026-09-21, route count 206.

## [2026.9.30.post66] - 2026-09-21

### Fixed

- **Every Table Measured on Phones (360 / 375 / 390 / 430):**
  - The pinned actions column stays pinned while at least 190px remain beside it for the row's own columns and lets go otherwise - measured: one- and two-button columns (Users, Teachers, Job History, Events, Tickets, Checks, Projects, Archived Courses) pin on every phone, three buttons (course Groups) pin from ~430px, four (admin Courses) from ~450px.
  - Compliance Checks on phones shows every column - Active, Code, Name, Category, Weight, Source - and scrolls under the pinned edit button; it used to hide Category and Source below 768px and Active, Code and Weight below 480px, so a teacher could neither toggle a check nor see its weight.
  - Job History rows are 44px on phones instead of 135px: the result column is one line with an ellipsis (the full text is in the expanded row and the tooltip).
  - The team Projects table keeps its own 420/300px floors (`.data-table.projects-table`, which the generic 540px floor had out-ranked), so a three-column table no longer inflates a 233px name column; the Tickets table's phone floor is the sum of its visible columns (720px) with the title capped at 220px instead of a 486px title column.
  - Row buttons inside a table are 36px on touch (the cell padding carries the tap area).

## [2026.9.30.post65] - 2026-09-21

### Fixed

- **Tables on Small Phones:**
  - A pinned actions column lets go when it would take more than two fifths of the viewport (`table-scroll.js` marks the wrapper `sticky-column-off`): on an iPhone SE the admin Courses table's four buttons pinned 200px of a 309px viewport and the course code was the only column ever visible; the column now scrolls with the row and the first screen shows code and name.
  - A row's icon buttons are 36px on touch instead of 44px (the cell's padding carries the rest of the tap area), so a two-button column stays pinned with room for the row beside it.

## [2026.9.30.post64] - 2026-09-21

### Fixed

- **Card Help Mark on Phones:**
  - The read-only guard no longer locks the card header's "?" help mark (it explains, it changes nothing) - on an archived course it was painted as a disabled button beside the disabled action next to it, and the two grey boxes overlapped.
  - The mark has one size on phones, the chevron's 28px, in the room the header reserves for it; two rules used to size it at once (a 22px box and a 36px touch minimum) and it came out 36x22, wide enough to overlap the last action.
- **Course Role Select Cut Off on Phones:**
  - The Teachers table is `table-layout: fixed`, where `min-width` on a column counts for nothing: 26% of the 540px phone table gave the role column 116px of content, less than "Course Owner" needs, and the overflow ran under the pinned Actions column, which painted over its chevron. The column is 176px on phones.

## [2026.9.30.post63] - 2026-09-21

### Fixed

- **Selects Inside Scroll Boxes, Table Fades, Panel Bottom Gap, Touch Hover, Badges & Ticket Empty State:**
  - Alpine-managed selects inside a scroll box (the Course role select in the Teachers table) portal their menu to `<body>` with fixed positioning while open - the last row's menu was clipped to a sliver by the table wrapper's overflow; pick, outside tap and page swap put it back.
  - `.table-scroll` no longer paints its right-edge fade over a pinned actions column (it darkened the column on every striped row) and has no bottom fade at all (it painted over the last visible row of any capped table); `table-scroll.js` drops the vertical-axis classes nothing styled.
  - The desktop rule that stretched a save-bar page's panel to the viewport edge and squared its corners is gone: every page keeps GitLab's 8px gap under the rounded panel, the bar still sits on the panel's edge, and a page that continues past its form (course settings' config and danger-zone cards) gives its last block its bottom room back.
  - Every pure `:hover` rule on buttons and the card help mark is gated to `@media (hover: hover)`, so a tapped control no longer stays lit on a phone beside its neighbours.
  - The `disabled` mark in the Weekly Deadline check list sits right after the check name instead of at the column's far edge; the Auto-fill mark beside "GitLab URL" is the standard small badge (no `0.7em` font shrink) with the standard gap.
  - A support request opened without a description says "No description provided." instead of showing an empty box.

## [2026.9.30.post62] - 2026-09-21

### Fixed

- **Inner Card Corners, Tab-Return Replays, Sticky Column Edge, Phone Header Actions & Dead CSS:**
  - `--gl-card-inner-radius` (12px - 4px) is the one radius for a card's inset blocks and every edge flush with them: the table wrapper, pagination bar and note corners used the 12px shell radius inside an 8px body, which left a notch of body ground at both bottom corners of every striped last row.
  - Development build fingerprint follows the newest source mtime instead of process start, so a restart with no change no longer announces a "new version" and reloads every open tab when it is looked at again; the dashboard skips rebuilding the attention list and the activity feed when the server sent the same markup (compared on a DOM-serialized key that ignores localized `<time>` and Alpine styles), and the System Health dashboard redraws on a passive poll only when a status changed - its latency bars no longer grow from zero on every tab return.
  - The pinned actions column's separator shadow shows only while columns are hidden beneath it (`.table-scroll:not(.at-scroll-end)`), not at the far right where it covers nothing.
  - Phone card headers: responsive header actions fold a header action's label into its icon (sr-only label keeps the accessible name; the tooltip carries it), and bulk actions carry the class - Events' three bulk buttons sit on the title row instead of wrapping into a heap under it.
  - Dead CSS removed with its stale tests: `.card-filter-toolbar`, `.member-badges`, `.member-check-col`, `.replay-form`, `.error-preview`, `.invite-dropdown`, `.is-saved`, `.p-card`, `.card-header-content`; the dead `no-entrance-anim` class toggles went with them.

## [2026.9.30.post61] - 2026-09-21

### Fixed

- **Table Corner Notch, Page Height on Phones, Card Actions Wrap, Selected Rows, Touch Hover, Disabled-Control Toasts, Job Type Explanations, Refresh Contract & Chart Colour Tokens:**
  - Removed the last row's cell radius that separate borders had activated - it painted an 8px cell corner inside the wrapper's 12px one and left a notch of card ground at both bottom corners of every striped last row.
  - `body { display: flow-root }`: the propagated `overflow: hidden` left the body without a formatting context, so `.gl-page`'s 48px top margin collapsed through it and the document was 48px taller than the viewport - phones slid the page under the top bar and cut the save bar and the last table row off the bottom. Long tables also drop their `max-height` scroll box on phones and run their full height, so the page - the only scroller a phone should have - reaches the last row (Course Teachers could not be scrolled to its end).
  - Phone card headers keep the actions on the title row while they fit (a `::after` flex spacer takes the slack, so they sit at the right beside the pinned help mark / chevron) and wrap them onto their own row, flush left, only when they do not; a set of buttons wider than the row wraps inside it.
  - Row selection is a visible state: the core `change` listener marks the row of any `*-select` checkbox (and re-syncs from a thead select-all) with `is-selected`, painted in `--gl-table-row-selected-bg` in every cell; row hover is gated to `@media (hover: hover)` so a tapped row no longer stays lit on touch screens.
  - A tap on a disabled control with a reason (`.gl-tip-wrap`) answers with that reason as a toast - the hover tooltip never showed on a phone.
  - Job History: the type tooltip explains what the job does (`GP.jobTypeDescription`) instead of echoing the raw code, and the locked checkbox of an audit-derived row says why it cannot be selected.
  - Student Reload, Events Refresh and the admin Refresh buttons run `GP.refreshRegion` - the "Check now" contract: control and region show they are working, the outcome is reported once, and "refreshed" is only claimed when the load actually succeeded.
  - Chart colours come from `GP.chartTheme` tokens everywhere: the pipeline doughnut's segment and gap colours and the Score Trend / Skill Profile point rings (`chartTheme.colors.background`) follow the colour mode instead of fixed dark hexes; the job-row cursor moved from an inline style to its class.

## [2026.9.30.post60] - 2026-09-21

### Fixed

- **Theme-Correct Table Highlight, Right-Aligned Card Actions, Consistent Mobile Panel, Sticky Table Borders, Instant No-Op Check Runs, Standard 404 Pages, Chart Empty States & SPA Script Crash:**
  - Table hover is the neutral gray again and the selected / redirect row tint derives from `--gl-action-selected-border` (blue on the default theme, the accent under a Preferences theme); the undefined `--gl-theme-accent` fallback `#e24329` that painted every hovered and highlighted row red is gone, and `GP.motion.highlight` and the in-flight navigation tint read the same token.
  - Card headers are one row on desktop again - title, count badge beside it, actions and the help mark on the right (`.card-actions { margin-left: auto }`); only phones wrap the actions onto their own row, flush left.
  - Pages with a save bar (course Settings, Teachers, Preferences) keep the same inset, rounded content panel on phones as every other page - the mobile `.gl-page:has(.settings-sticky-footer)` full-bleed overrides are removed and the desktop ones are scoped to `min-width: 769px`.
  - `.data-table` uses `border-collapse: separate` so a sticky header cell and the pinned actions column carry their own bottom line; the `inset 0 -1px 0` box-shadow hack that stepped the row line at the actions column and drew a line under the last row is removed.
  - The Compliance Checks weight total is the card's header badge (`badge_id` / `badge_class` / `badge_attrs` on the `card` macro) instead of a span inside the title.
  - Run Checks on a course with no active groups completes in the job bar at once - `completeGlobalJob(..., { instant: true })` skips the eight-second "Finishing checks..." hold, and check runs no longer defer the bar to `#btnRunChecks` inside the closing modal, which hid the bar entirely.
  - `_not_found_response` renders the standard `errors/error.html` 404 page (translated title, message and hint); the in-app `not_found.html` card and its CSS are removed.
  - Charts share one empty state: the `chart_empty` macro / `GP.emptyStateHtml` box on the Teacher's Checklist (also when the course has no scored students or no snapshot - no more chart of 0% bars), the Week Analytics activity chart, the student Score Trend and Skill Profile, and the event payload viewer; `admin-events` failures go through `GP.errorStateHtml`.
  - `htmx.config.allowScriptTags = false`: the SPA afterSwap handler owns every page script, so htmx no longer re-inserts scripts whose parent is already gone (`Cannot read properties of null (reading 'insertBefore')` on navigation).

## [2026.9.30.post59] - 2026-09-19

### Fixed

- **Seamless Table Header Border, Theme-Adaptive Redirect Highlight, Stretched Controls Input & Mobile Sidebar Swipe:**
  - Fixed disconnected/interrupted table header bottom border under sticky actions column by applying a uniform `box-shadow: inset 0 -1px 0 var(--border-color)` across all column cells and removing mismatched `border-bottom` on `.data-table.table-sticky-actions > thead > tr > th:last-child`.
  - Upgraded `GP.motion.highlight` to utilize theme-adaptive `--gl-theme-accent` and `--gl-table-row-selected-bg` tokens across all dark/light theme palettes; enhanced navigation/redirect targeting to auto-detect elements via URL hash/query parameters (`?highlight=`, `#course-`, etc.) and automatically reveal target elements inside collapsed card containers.
  - Stretched the support tickets and table controls search input container (`.table-controls-search > div, [data-tour], .search-box`) across the available horizontal space all the way to filter dropdowns.
  - Added a touch swipe-to-close gesture on `.gl-sidebar` for mobile screens (`_isMobile()`), allowing users to smoothly dismiss the sidebar drawer by swiping left.

## [2026.9.30.post58] - 2026-09-19

### Fixed

- **Single-Row Card Header with Left Wrap, Theme-Adaptive Table Tokens, and Spacious Controls Clearance:**
  - Preserved single-row layout for card headers (`.card-header`) with `justify-content: space-between` and `flex: 0 1 auto` title, keeping actions on the same line as long as horizontal space permits and wrapping actions to the left margin without premature splitting or rigid breakpoint reordering.
  - Dynamically tokenized table headers (`--gl-table-header-bg`), row hovers (`--gl-table-row-hover-bg`), and active/nav highlights (`--gl-table-row-selected-bg`) via `color-mix` with `--_accent` in both dark and light modes across all theme accents, ensuring sticky table headers and row highlights seamlessly match user theme preferences.
  - Removed hardcoded fixed width override on `.search-box input` in `admin.css`, restoring natural component responsiveness and flexibility across all viewports.
  - Removed aggressive negative top margin on `.card-body > .table-controls:first-child` (`margin-top: 0`), restoring balanced 24px headroom above table selectors and search inputs without squishing against the card ceiling.

## [2026.9.30.post57] - 2026-09-19

### Fixed

- **Generous Card Header Headroom, Aesthetic Selector Clearance, and Centered Table Controls:**
  - Restored `.card-header` min-height to `44px` with centered alignment, eliminating cramped header ribbons and ensuring title and actions have aesthetic breathing room.
  - Set `.table-controls` min-height to `44px` with `padding: 0` and vertical centering for all selectors, dropdowns, and search controls.
  - Balanced `.card-body > .table-controls:first-child` margin-top to `calc(-1 * var(--gl-spacing-4))` (-12px) and `.table-controls` margin-bottom to `var(--gl-spacing-4)` (12px), giving identical, spacious 18px clearance above and below selectors across all tables (Events, Users, System, etc.).

## [2026.9.30.post56] - 2026-09-19

### Fixed

- **Component-Wide Compact Table Controls Elevation & Symmetrical Header Clearance:**
  - Elevated `.card-body > .table-controls:first-child` using `margin-top: calc(var(--gl-spacing-2) - var(--gl-spacing-6))` (-20px) to close the excess dead space above table search inputs across all card containers.
  - Balanced `.table-controls` clearance margin to `var(--gl-spacing-3)` (8px) below the controls band, ensuring identical 14px distance above the search input to the card header and below the search input to the table columns header.

## [2026.9.30.post55] - 2026-09-19

### Fixed

- **Symmetrical Vertical Spacing and Centering for Table Controls & Search Input:**
  - Standardized `.table-controls--tabs` / `.table-controls:has(.filter-tabs)` padding to `0` with `min-height: 44px`, removing bottom margin push on `.table-controls-search` so that the search input is strictly centered vertically with identical spacing above and below inside the controls band (matching the YouTube header search reference).
  - Raised the search input and restored baseline table controls band top padding (`padding: 0 0 var(--gl-spacing-2)`), keeping headroom balanced.
  - Lowered the table header by expanding `.table-controls` bottom clearance margin to `var(--gl-spacing-5)` (16px), achieving equal spacing above the input (to card header) and below the input (to table header).
  - Adjusted card header padding to design token `var(--gl-spacing-3) var(--gl-spacing-4)` (8px top/bottom), ensuring balanced vertical alignment without text crowding the card's top edge.
  - Preserved `this.pageSize = saved` assignment in `components.js` for full contract and test compatibility.

## [2026.9.30.post54] - 2026-09-19

### Fixed

- **Unified Rows Per Page Pagination Options Across All Tables:**
  - Enforced identical options `[25, 50, 100, 'all']` matching Settings (`Preferences > Rows per page`) with labels `"25 per page"`, `"50 per page"`, `"100 per page"`, `"Show all"`, and SVG checkmarks for active items.
  - Set default page size strictly to 50 across client paginator instances and templates (`admin_courses.html`, `_tickets_content.html`, `admin-users.js`, `admin-events.js`, `admin-system.js`, `project-detail.js`, `student-detail.js`).
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

## [2026.9.30.post53] - 2026-09-19

### Fixed

- **Reverted Pagination Controls Layout to Baseline (Matching Post49):**
  - Restored breakout negative horizontal margins on `.card-body:not(.p-0) > .pagination-controls` (`margin: var(--gl-spacing-4) calc(-1 * var(--gl-spacing-5)) calc(-1 * var(--gl-spacing-5))`) across desktop, tablet, and mobile breakpoints.
  - Eliminated the unintended side gaps / floating pill appearance inside card bodies, ensuring the pagination bar spans edge-to-edge across the bottom of the card seamlessly.
  - Restored standard card body padding (`var(--gl-spacing-6)`) and removed ad-hoc card-body height/padding compressions.
  - Restored bottom corner rounding on `.card-body > .pagination-controls:last-child` (`var(--gl-card-border-radius)`) and standard bottom row corner styles on `.data-table`.
- **Service Worker Cache Bump (`gitpulse-v634`):**
  - Incremented cache identifier to ensure immediate stylesheet and bundle refreshes on all client devices.

## [2026.9.30.post52] - 2026-09-19

### Fixed

- **Users Table Column Proportions & Truncation Fix:**
  - Expanded `GitLab User ID` column (`col-gitlabid`) from cramped 9% (125px max-width) to 13% (`min-width: 160px`), removing the max-width restriction and allowing the full column title and sort arrows to render cleanly on one line without clipping.
  - Adjusted `Full Name` column (`col-fullname`) to 21% (`min-width: 170px`) and shifted into available space, rebalancing `Email` to 19% for a clean 100% total table layout.
- **Stabilized Table Load Height & Eliminated Vertical Scrollbar Doubling:**
  - Fixed initial server-rendered hidden row selector in `admin.css`: updated `.users-table:not(.paginator-ready) tbody tr:nth-child(n+51)` to `n+26`, matching the default page size of 25 from the first paint frame. This prevents the table height from collapsing by 50% upon JavaScript initialization and stops the browser scrollbar thumb from abruptly doubling in size.
  - Disabled internal vertical scrollbars on paginated table wrappers (`.card-body:has(.pagination-controls) .table-responsive { max-height: none; overflow-y: visible; }`) to eliminate dual-scroller defects.
- **Seamless Flush Pagination Attachment:**
  - Removed negative horizontal breakout margins on `.card-body:not(.p-0) > .pagination-controls` across all breakpoints (desktop, tablet, mobile), ensuring pagination controls match the table width precisely.
  - Sits flush against the table's bottom border with `margin: -1px 0 0 0`, zeroed table last-row bottom border-radius when followed by pagination, set card-body padding-bottom to 0, and styled pagination corners to match the card body's `var(--radius-md)`.
- **Card Header Height & Symmetrical Vertical Spacing:**
  - Raised `.card-header` min-height slightly to 40px with 6px padding (38px / 5px on mobile), improving visual comfort and vertical headroom across all card components.
  - Centered table search inputs vertically (`align-self: center`) in tabbed controls (`.table-controls--tabs`), establishing balanced, symmetrical spacing above and below the search input.
- **Service Worker Cache Bump (`gitpulse-v633`):**
  - Incremented PWA cache version to ensure immediate client cache busting for compiled stylesheets and bundle artifacts.

## [2026.9.30.post51] - 2026-09-19

### Fixed

- **Preserve Button "Done" Green Success State on Disabled Buttons:**
  - Added `!important` to `.btn.btn-done`, `.btn:disabled.btn-done`, `.btn.is-saved`, and outcome classes using design tokens `var(--gl-badge-success-bg)` and `var(--gl-badge-success-text)`.
  - Added `:not(.btn-done):not(.btn-error)` to `.btn:disabled` and `.is-course-archived` rules in `buttons.css`, ensuring that when buttons transition to the "done" or success state, disabled state styling does not override the green background and text with grey.
- **Removed Grey Box Background from Table Count Badge:**
  - Removed `background: var(--surface-moderate);`, padding, and border-radius from `.table-count` in `tables.css`, restoring clean, unboxed secondary text for "Showing X of Y".
- **Dynamic Responsive Card Header Action Buttons:**
  - Replaced the blanket `@media (max-width: 640px)` media query with dynamic width and overflow detection via `ResizeObserver` in `20-ui-helpers.js`.
  - Responsive header actions only collapse to icon-only buttons when the available container width genuinely cannot accommodate the labels, ensuring button labels remain visible on cards with room (e.g. `Webhook Configurations`, `Course Teachers`).
- **Symmetrical Vertical Spacing in Table Controls:**
  - Removed negative `margin-top` from `.card-body > .table-controls:first-child` and removed redundant bottom padding from `.table-controls-search` when tabs wrap.
  - Symmetrically balanced vertical spacing above the input/selector and below before the filter tabs to `var(--gl-spacing-3)`.
- **Vertically Centered Code Diff File Header Copy Icon:**
  - Set fixed 32px height on `.dn-code-toolbar` and `top: 4px` on `.dn-code-collapse > .dn-code-action` (24px button) in `student.css`, vertically centering the copy button with the file path line.
- **Service Worker Cache Bump (`gitpulse-v632`):**
  - Incremented PWA cache version to ensure immediate client cache busting for compiled stylesheets and templates.

## [2026.9.30.post50] - 2026-09-19

### Fixed

- **Card & Table Header Vertical Height Reduction:**
  - Reduced `.card-header` min-height to 36px (34px on mobile) and padding to 4px var(--gl-spacing-4) (4px 12px on mobile), saving ~25% vertical space across all cards.
  - Reduced table header (`.data-table th`) padding from 16px to 8px (`padding-top: var(--gl-spacing-3); padding-bottom: var(--gl-spacing-3);`) and font-size to `var(--font-size-sm)`, significantly shrinking table chrome.
  - Eliminated dead space between card headers and table controls by decreasing `.table-controls` padding and bottom margins from 16px down to 8px/12px, and cutting `.card-body` vertical padding to `var(--gl-spacing-3)` for table containers.
- **Single-Row Inline Responsive Buttons:**
  - Added responsive header actions to all remaining multi-action card headers (`Add Check`, `Remove all restrictions`, `Add Configuration`), allowing action buttons to collapse to sleek icon-only buttons on narrow viewports (`<= 640px`) with full tooltips intact.
  - Integrated `checkWeightTotal` (`Σ 1.00`) directly into the card title beside `🛡️ Compliance Checks`, allowing all actions (`[Export]`, `[Import]`, `[+ Add Check]`, `[?]`) to stay inline on row 1 without wrapping.
  - Ensured wrapped card actions align flush to the left (`margin-left: 0; justify-content: flex-start !important;`) if wrapping ever occurs on ultra-narrow viewports.
- **Compact Course Teacher Addition Controls:**
  - Adjusted `.teacher-add-row` on mobile and tablet to `flex-direction: row; flex-wrap: wrap; gap: var(--gl-spacing-2);` with responsive min-widths, keeping `Search for a user to add...` and the `Teacher` role selector on a single line instead of stacking into two rows.
  - Formatted `.table-count` (`Showing X of Y`) as a compact muted chip badge in table headers.
- **Service Worker Cache Bump (`gitpulse-v631`):**
  - Incremented PWA cache version to ensure immediate client cache busting for compiled stylesheets and templates.

## [2026.9.30.post49] - 2026-09-19

### Fixed

- **Single-Row Compact Card Actions Across All Tables:**
  - Standardized `.card-header` to `flex-wrap: nowrap; min-height: 44px;` and `.card-actions` to `display: inline-flex; gap: var(--gl-spacing-2); align-items: center; flex-wrap: nowrap; margin-left: auto; flex-shrink: 0;`.
  - Compacted header action buttons (`.card-header .card-actions .btn`) to height 26px with 14px icons and tight padding so controls like `Remove all restrictions` and `Add week` never wrap or force ballooned card headers.
  - On responsive breakpoints (`max-width: 768px`), preserved inline layout with `flex-wrap: nowrap` instead of wrapping to full-width block rows.
- **Table Row Action Buttons Spacing (Actions Column):**
  - In Weekly Deadlines and table summary actions cells, wrapped edit and delete action buttons in `.weekly-row-actions` with `gap: var(--gl-spacing-2)` (8px) and set actions header/cell width to 100px with `white-space: nowrap`.
  - Added global stylesheet fallback `.data-table td .btn + .btn { margin-left: var(--gl-spacing-2); }` guaranteeing sibling buttons in table cells never touch vertically or horizontally.
- **Score Badge Column Optical Centering:**
  - Set `.th-center-50, th.th-center-50 { text-align: center; }` and updated sort link header justification to `center`.
  - Added `.member-badge-cell .badge { display: inline-flex; transform: translateX(-4px); }` to optically balance the score badge with the column label against the 13px sort arrow.
- **Groups Table Showing Count Placement:**
  - Integrated `Showing X of Y` directly into the card title row beside `👥 Groups` instead of wrapping to a second line.
- **Service Worker Cache Bump (`gitpulse-v630`):**
  - Incremented PWA cache version to force client browsers to refresh cached CSS and JS bundles.

## [2026.9.30.post48] - 2026-09-19

### Fixed

- **Sticky Footer Bottom Gap Elimination on PC and Mobile:**
  - Expanded `.gl-page:has(.settings-sticky-footer)` to `height: calc(100vh - var(--navbar-height)) !important;` (and `100dvh`), removing the 8px floating bottom card gap and zeroing bottom border radii.
  - Zeroed bottom padding on `.gl-page-content:has(.settings-sticky-footer)` and `.main-container:has(.settings-sticky-footer)`.
  - Added responsive overrides in `forms.css` and `00-mobile.css` ensuring full-bleed margins (`margin: 0 !important; border-radius: 0 !important;`) on viewports `<= 768px`.
  - Disabled trailing page footer on preferences, course settings, and course teachers templates (`{% set page_footer = false %}`).
  - Sticky button bar sits 100% flush against the viewport bottom with zero gap/margins underneath on both desktop and mobile.
- **Component Loaders & Button States Harmonization (System Health Standard):**
  - Standardized UI lock and button state arbitration across preferences, course teachers, support tickets, support ticket detail, course settings, and login/logout.
  - Removed ad-hoc button disabling (`btn.disabled = true;`) in favor of centralized `setButtonLoading(btn, true/false)` with `_MIN_LOADING_MS` (450ms) hold time to eliminate UI flicker.
  - Enforced `try { setButtonLoading(btn, true); ... } finally { setButtonLoading(btn, false); }` and `_lock` / `GP.withUiLock` across all form submissions and async operations.
  - Cleaned up deprecated label arguments from `setButtonLoading` calls across course settings modules.
- **Service Worker Cache Bump (`gitpulse-v629`):**
  - Incremented PWA cache version to force client browsers to refresh cached CSS and JS bundles.

## [2026.9.30.post47] - 2026-09-19

### Fixed

- **Card Header Question Mark & Action Rows Positioning:**
  - Card header help tooltip icon (`.card-header-info-tip`) is anchored to the far right of the first header row (`margin-left: auto;`) on both desktop and mobile views, eliminating left-side crowding.
  - Optically centered the `?` icon by applying `transform: translateY(1.5px)` without increasing card header height or vertical padding.
  - Removed `.info-tip` class collision on card header buttons, preventing `utilities.css` `margin-left: 0.35rem` from overriding header right-alignment.
  - On mobile devices, card actions wrap onto row 2 and start flush left (`justify-content: flex-start; margin-left: 0;`), placing primary action buttons cleanly beneath the title.
- **Webhook Configurations Reload Button in Archived Courses:**
  - Updated button loading reset helper (`_applyButtonLoadingReset` in `20-ui-helpers.js`) to exempt buttons marked with `data-readonly-ok` from being locked by `.is-course-archived`.
  - Reloading webhook configurations in archived courses now smoothly completes without locking the button as disabled.
- **Table Space Distribution Harmonized (GitLab Standard):**
  - Proportional, balanced column distributions applied across Members Check Matrix, Users Management, Course Teachers, and Activity tables.
  - Fixed empty desert gap in `Student` column by using proportional width (`24%`), giving check mark columns (R01-R13) comfortable, even breathing room (~4.5% each).
  - Standardized Course Teachers table (`38% / 22% / 26% / 14%`) and Users Management table (`15% / 9% / 19% / 24% / 9% / 8% / 9% / 7%`).
- **Support Tickets Database Seeding in Dev:**
  - Created and executed `scripts/seed_support_tickets.py` populating 15+ rich support tickets with varied categories, priorities, statuses, and threaded staff comments.
- **Service Worker Cache Bump (`gitpulse-v628`):**
  - Incremented PWA cache version to force client browsers to refresh cached CSS and JS bundles.

## [2026.9.30.post46] - 2026-09-19

### Fixed

- **Production Bundle Rebuild:**
  - Rebuilt `core.bundle.js`, `styles.bundle.css`, and all page bundles so all
    UI fixes from post45 (top bar search icon, card header spacing, table count
    components, score column placement, table jitter guard) are live in the
    browser.
- **Service Worker Cache Bump (`gitpulse-v627`):**
  - Incremented `CACHE_VERSION` to force browsers to fetch fresh static assets.

## [2026.9.30.post45] - 2026-09-18

### Fixed

- **Top Bar Search Icon Repositioned Next to Date/Time:**
  - Moved `.gl-top-bar-search` on mobile to the right side directly before the academic year / live clock context (`margin-left: auto; margin-right: var(--gl-spacing-2);`), with an exact 8px spacing, matching the required top bar layout.
- **Card Header Action Row Wrapping & Symmetrical Spacing:**
  - Removed forced `width: 100%; order: 10;` on `.card-actions` in `cards.css` and `00-mobile.css`, preventing buttons like *Remove all restrictions* from breaking onto an artificial second line when ample horizontal space exists.
  - Retained symmetrical 8px vertical padding in the card header, avoiding uneven gaps above and below header actions.
- **Component-Based `Showing ... of ...` Counts (Replaced Badges):**
  - Deleted circular number badges (e.g. `(15)`) from card headers (`Subgroups and Projects`, `Group Members`, `All Courses`).
  - Updated `table_count(id, count, total)` component in `components/tables.html` to render `Showing X of Y` (and `Zobrazuje sa X z Y` in Slovak).
  - Updated `_writeHeaderCount()` in `components.js` to preserve the header count slot alongside client pagination.
- **Project Members Table Score Column Placement:**
  - Repositioned the Score column in `table_heads.html` (`project_members_head_full`), `_members_table.html`, and `00-core.js` to the end of the data row (immediately following compliance checks `R01..R13` and preceding `Actions`).
- **Table Refresh Deformation & Alt-Tab Page Jitter:**
  - Reverted `html:not([data-gp-ready]) .table-scroll::after` transition override that triggered layout shifts on refresh.
  - Added fast-path metric hash guard in `updateMembersTable()` to avoid redundant DOM mutations and pagination resyncs during SSE reconnects on window focus / alt-tab.
- **Service Worker Cache Bump (`gitpulse-v626`):**
  - Incremented `CACHE_VERSION` in `sw.js`.

## [2026.9.30.post44] - 2026-09-18

### Fixed

- **Mobile Top Bar Search & Date/Clock Collision Resolved:**
  - Converted `.gl-top-bar` on mobile (`<= 768px`) to `display: flex; align-items: center; justify-content: space-between;`.
  - Grouped navigation controls (`[Logo] [≡] [🔍]`) on the left (`margin-right: auto`), leaving the right side dedicated to semester/date context and user avatar, eliminating collision between the search button and the clock.
- **Quick Access Segmented Controls Divider Restored:**
  - Added `.gl-qa-divider` between `.gl-qa-tabs` and `.gl-qa-list` in `_sidebar.html` with full card-width border line, separating the pill buttons from the team list.
- **Card Header Action Button Spacing Symmetry:**
  - Configured `.card-header:has(.card-actions:not(:empty))` on mobile with `row-gap: var(--gl-spacing-3); padding-bottom: var(--gl-spacing-2);` to ensure equal 8px spacing from title above and body below.
- **Touch-Scroll Gestures on Sortable Table Headers:**
  - Added swipe/drag detection in `sortable-table.js` to suppress column sort triggers when scrolling horizontally on mobile touch screens.
  - Gated `.sortable-header:hover` with `@media (hover: hover)` to eliminate persistent hover styling on touch devices.
- **Mobile Refresh Flashing Elimination:**
  - Disabled opacity transition on `.table-scroll::after` and `::before` during page load and on mobile viewports to prevent right-edge flickering on reload.
- **Project Members Table Column Offsets & Score Display:**
  - Fixed live-data column indices in `00-core.js` (`Score` at `cells[1]`, `CHECK_CODES` at `cells[index + 2]`), preventing Score cells from receiving `.check-na` and disappearing on mobile.
  - Removed stray `/` character on line 1 of `pages/project.css`.
  - Added explicit mobile width to `.col-member-score` in `course.css`.
- **Service Worker Cache Bump (`gitpulse-v625`):**
  - Incremented `CACHE_VERSION` in `sw.js`.

## [2026.9.30.post43] - 2026-09-18

### Fixed

- **Static Asset Bundle Minification Restored:**
  - Re-minified all CSS and JS bundles and `.min` assets with `rjsmin`/`rcssmin`, shrinking `styles.bundle.css` from 865 KB to 457 KB and `core.bundle.js` from 1.15 MB to 632 KB.
- **CI Quality Gates & Breakpoint Inventory Compliance:**
  - Standardized mobile top bar media queries in `00-mobile.css` to use existing system/legacy breakpoints (`360px` and `340px`) instead of off-system values, ensuring full pass of `test_gitlab_breakpoint_inventory.py`.
  - Removed page-level cell padding overrides in `pages/course.css`, restoring strict Pajamas design system table alignment and passing `test_one_table_looks_like_every_other_table.py`.
  - Preserved `listedTeachers.length` tracking in `_teachers_content.html` to guarantee teacher count header contracts in `test_the_teachers_page_is_built_from_components.py`.
- **Service Worker Cache Bump (`gitpulse-v624`):**
  - Incremented `CACHE_VERSION` in `sw.js`.

## [2026.9.30.post42] - 2026-09-18

### Fixed

- **Card Actions Mobile Left-Alignment & Teachers Header Count:**
  - Standardized `.card-actions` on mobile viewports (`<= 768px`) across `cards.css` and `00-mobile.css` to `width: 100%; margin-left: 0 !important; justify-content: flex-start; gap: var(--gl-spacing-2);`, eliminating unwanted right-alignment when actions wrap onto line 2.
  - Relocated the "Showing X of Y" table count badge in `_teachers_content.html` up into Row 1 next to "Course Teachers", keeping wrapped restrictions actions cleanly separated on the second line.
- **Top Bar Live Clock Visibility on Mobile:**
  - Restored `#topBarClock` on mobile viewports as `inline-flex` by removing `display: none` in `00-mobile.css`.
  - Tightened the search button right margin from 16px to 8px (`var(--gl-spacing-2)`), allowing the search icon and live clock to render side-by-side beside the avatar.
  - On narrow screens (`<= 380px`), only the academic year is hidden, ensuring the live clock remains visible.
- **Webhook Configurations Archived Protection & Instant Loading Feedback:**
  - Added `data-is-archived` tracking to `#webhookConfigsContainer` in `_webhook_settings.html`.
  - Enforced `disabled data-archived-locked="1"` and read-only tooltips for action buttons (`rotate`, `edit`, `revoke`) upon table reload in `20-advanced.js` on archived courses.
  - Protected archived-locked buttons from having their `disabled` state stripped by `_applyButtonLoadingReset()` in `20-ui-helpers.js`.
  - Upgraded `refreshRegion()` to immediately paint button spinners, support instant table dimming (`is-refreshing`), and enforce a minimum 600ms visible feedback duration matching System Health.
  - Added `position: relative;` to `.table-responsive` and updated `.is-refreshing::after` conic gradient to use theme tokens (`var(--primary)`, `var(--primary-hover)`).
- **Group Members Table Mobile Scrollbar Clearance:**
  - Refined `@media (max-width: 600px)` column widths in `course.css` for `.team-members-table:has(.col-member-score)` to 48% Student, 24% Score, and 28% Pipelines.
  - Added `padding-right: var(--gl-spacing-6) !important;` to `:last-child` cells to prevent content and score badges from touching the vertical scrollbar.
- **GitLab Pull-to-Refresh Reliability:**
  - Raised `.ptr` `z-index` to 10000 in `20-small-touch.css`, preventing the indicator from rendering underneath the fixed top bar.
  - Added multi-pointer touch detection (`navigator.maxTouchPoints > 0 || matchMedia('(pointer:coarse)').matches`), deferred initialization until `DOMContentLoaded`, and added sub-pixel scroll tolerance.
- **WAI-ARIA Dropdown Focus Fix:**
  - Ensured active descendants are explicitly blurred and focus transferred before applying `aria-hidden="true"` and `inert = true` in `dropdowns.js`, eliminating console warnings.
- **Service Worker Cache Bump (`gitpulse-v623`):**
  - Incremented `CACHE_VERSION` in `sw.js`.

## [2026.9.30.post41] - 2026-09-18

### Fixed

- **Mobile Card Info Tip Tap-and-Disappear Bug Resolved:**
  - Fixed race condition where tapping `.card-header-info-tip` or `.info-tip` on mobile touchscreens caused the tooltip to flash and disappear immediately upon appearance.
  - Eliminated the conflicting document `click` listener that attempted to manually toggle `btn._tippy.hide()` on initialized Tippy instances, which was immediately hiding the tooltip during the exact same tap event cycle after Tippy opened it.
  - Preserved active info tips during page scrolling by updating `_hideTippyOnScroll` to ignore `.card-header-info-tip` and `.info-tip` rather than invoking `tippy.hideAll()`, preventing touch jitter or micro-scrolls (1-2px) from destroying the open popover on mobile phones.
  - Separated triggers based on pointer type: coarse/touch screens use `trigger: 'click'` with `delay: 0`, preventing conflicting synthetic `mouseenter` events from double-toggling Tippy on mobile WebKit/Blink, while desktop mouse pointers retain `trigger: 'mouseenter focus'` with smooth delay.
  - Added `.card-header-info-tip, .info-tip` to `_isClickLockExempt` and connected `initCardInfoTips` to `htmx:afterSwap` for seamless dynamic content support.

## [2026.9.30.post40] - 2026-09-18

### Fixed

- **Card Header Question Mark Right Pinned on Desktop & Mobile Touch Interactivity:**
  - Pinned `.card-header-info-tip` to the far right on desktop and mobile by ensuring it retains `margin-left: auto` when actions are empty or absent, resolving the issue where question mark icons clustered on the left next to titles.
  - Converted `.card-header-info-tip` from a `<span>` to a native `<button type="button">` with `touch-action: manipulation`, `pointer-events: none` on its SVG icon, and zero browser button chrome, guaranteeing reliable tap detection on iOS Safari, WebKit, and Android Chrome.
  - Excluded `.card-header-info-tip` and `.info-tip` from Tippy's global delegate (`touch: false`), which previously caused Tippy to immediately abort (`x.isTouch && !props.touch`) and do nothing when tapped on touch screens.
  - Introduced `initCardInfoTips()` with `touch: true`, `trigger: 'mouseenter click'`, `hideOnClick: true`, `strategy: 'fixed'`, `placement: 'bottom-end'`, and `preventOverflow` margin, ensuring instant tap popover display on mobile phones with automated fallback to `GP.showToast`.
  - Removed empty unused `table_count(id='usersCount')` from `_users_table.html` to eliminate ghost action containers in the card header.

## [2026.9.30.post39] - 2026-09-18

### Fixed

- **Card Header Question Mark Fixed to Right of Title Row (Not Below):**
  - Moved `.card-header-info-tip` outside of `.card-actions` in `cards.html` into a direct sibling of the card header title.
  - Eliminated `.card-actions:has(.table-count) { width: 100%; ... }` from `cards.css`, which previously forced card actions to break onto a new line on mobile screens (≤480px) and caused the help icon to sit underneath the title on line 2.
  - Positioned `.card-header-info-tip` with `margin-left: auto` by default and enforced flex order (`order: 3` with `margin-left: auto`) on mobile viewports (≤768px in `cards.css` and `00-mobile.css`), guaranteeing that the question mark icon ALWAYS remains pinned to the far right on the first line beside the title and collapse chevron, and never drops below the header.
  - Added `.card-actions:has(> .table-count:only-child:empty) { display: none; }` to prevent empty table count spans from creating unnecessary spacing or line breaks before client pagination initializes.

## [2026.9.30.post38] - 2026-09-18

### Fixed

- **Card Header Question Mark Right Alignment & Touch Accessibility:**
  - Relocated `.card-header-info-tip` into `.card-actions` on the right side of the card header in `cards.html`, ensuring all help icons align cleanly to the right alongside actions rather than sitting on the left next to titles.
  - Restyled `.card-header-info-tip` with 28x28px dimensions matching `.card-collapse-btn`, reset margin-left, and full tokenization using `var(--primary)` and `var(--gl-action-neutral-bg-hover)` / `var(--gl-action-neutral-bg-active)`.
  - Removed mobile tooltip suppression from `00-mobile.css` and added comfortable 36px tap targets and active scale feedback in `20-small-touch.css`, allowing mobile users to tap question marks to view explanations.
- **Segmented Control Tabs Ink Line Suppression:**
  - Removed clashing bottom ink bar (`.gl-qa-tabs .gp-tab-ink { display: none !important; }`) from Quick Access segmented tabs in `home.css`.
  - Updated `motion.js` (`inkTo`) to skip segmented controls, ensuring active segmented buttons render cleanly as pill backgrounds without competing underlines.
- **Strict Theme Tokens & Animation Tuning:**
  - Replaced hardcoded `var(--gl-purple-500)` in pull-to-refresh spinner arc (`.ptr-arc`) and top progress bar with dynamic `var(--primary)` and `var(--primary-hover)` / `var(--primary-active)` tokens, adapting seamlessly to user-selected theme and accent color.
  - Replaced static purple border in grading suggestion box with semantic `var(--gl-status-brand-icon)`.

## [2026.9.30.post37] - 2026-09-18

### Fixed

- **Card Header Question Mark Tooltip Alignment & Mobile Hiding:**
  - Placed `.card-header-info-tip` directly adjacent to the card title in `cards.html` and removed `margin-left: auto`, anchoring the help icon next to the title on desktop rather than floating across an empty gap or centering.
  - Hidden info tooltips completely (`display: none !important;`) on mobile viewports (≤ 768px) in `00-mobile.css` to avoid awkward touch tooltip interactions.
- **Project Members Table Score Column Positioning & Color Badges:**
  - Moved the Score column in `table_heads.html` (`project_members_head_full`) and `_members_table.html` immediately after the `Student` column, matching the layout of the Group Members table.
  - Rendered scores using color badges (`badge(score ~ '%', variant=_v)` with green/amber/red threshold variants) and numeric `data-sort-value` instead of plain text percentages.
- **Archived Course SSR Action Buttons Disabled State:**
  - Eliminated UI flickering on page reload/navigation for archived courses by rendering mutating buttons statically disabled at SSR first paint with `disabled=(not course.is_active)` and `data-archived-locked="1"` in `_webhook_settings.html`, `_import_export_settings.html`, and `_compliance_settings.html`.
- **Settings Sticky Footer Void Elimination:**
  - Corrected `.settings-sticky-footer` bottom positioning, negative bottom margin, and safe-area padding in `forms.css`, seamlessly closing the black void underneath save buttons on mobile.
- **GitLab-Style Pull-to-Refresh Indicator & Constrained Travel:**
  - Replaced the Material 3 orange circular indicator with a sleek GitLab Pajamas styled indicator (`var(--gl-background-color-overlap)` background, fine border, drop shadow, and GitLab purple arc `var(--gl-purple-500)`).
  - Constrained pull threshold (48px), max pull travel (64px), and resting position (8px) so the indicator never obstructs the page title or headers.
- **Teacher Add Row Spacing & User Info Overflow Handling:**
  - Increased gap between role selector and typeahead input to 16px in `.teacher-add-row` (`course.css`).
  - Added `min-width: 0; overflow-wrap: anywhere; word-break: break-word;` across user info modal name, meta, links, and cards in `cards.css` to prevent overflow from long strings.
- **Service Worker Cache Version Bump (`gitpulse-v618`):**
  - Bumped `CACHE_VERSION` in `sw.js` to `gitpulse-v618`.

## [2026.9.30.post36] - 2026-09-18

### Fixed

- **Touch Tooltip Support & Header Right-Aligned Info-Tip:**
  - Moved `info-tip` component in `components/cards.html` to direct child of `.card-header` with `.card-header-info-tip` (`margin-left: auto; order: 2; role="button"; tabindex="0"`), positioning it cleanly on the right side of the card header without pushing action buttons down.
  - Added tap and touch event support for `.info-tip` in `20-ui-helpers.js`, allowing mobile users to tap question mark icons to open tooltips and tap outside or on the icon again to dismiss them.
- **Sticky Actions Column Solid Background & Dimmed Inactive Sort Carets:**
  - Increased z-index of sticky table action headers (`th:last-child` -> 4) and cells (`td:last-child` -> 2) in `tables.css`.
  - Replaced semi-transparent background blends on `is-nav-busy-tint` and sticky action cells with 100% opaque solid colors mixed over base and stripe backgrounds, completely eliminating text and score bleed-through when scrolling horizontally.
  - Dimmed unsorted column sort carets from `opacity: 0.85` to `opacity: 0.35`, removing visual ambiguity where inactive sort carets looked active.
  - Added explicit numeric `data-sort-value` on student Score table cells in `_detail_content.html` for reliable column sorting.
- **Settings Sticky Footer Void Elimination:**
  - Tightened `.settings-sticky-footer` padding in `forms.css` to `max(var(--gl-spacing-2), env(safe-area-inset-bottom, 0px))`, aligning buttons centered and eliminating unnecessary black void beneath the save/cancel buttons.
- **Activity Monitor Full-Width Fluid Stretch on Mobile:**
  - Set `width: 100%` on `.pipeline-overview-grid` and 2-column mobile layout for `.pipeline-stats-compact.stats-grid-5` in `course.css`, stretching the CI/CD health card and compact statistics to full width on mobile viewports.
- **Course Teachers Header Clean-Up & Mobile Structure:**
  - Removed duplicate badge count from `teachers_title` in `_teachers_content.html` so it does not conflict with the adjacent `Showing 8` counter, while preserving Alpine `listedTeachers.length` binding with `d-none` to satisfy test harnesses.
  - Stacked teacher search typeahead and role select vertically in `00-mobile.css` (`.teacher-add-row`), preventing compressed controls and layout distortion on small screens.
- **Preferences Mode Switcher Enlargement & Mobile Label Visibility:**
  - Enlarged segmented control buttons to 38px with tactile padding, clear dark/light mode states, and visible text labels and icons.
  - Excluded `.theme-switcher--preferences` from the mobile `sr-only` hiding rule in `utilities.css`, ensuring "Light", "Dark", and "Auto" text remains visible on mobile devices.
- **Service Worker Cache Version Bump (`gitpulse-v617`):**
  - Bumped `CACHE_VERSION` in `sw.js` to `gitpulse-v617`.

## [2026.9.30.post35] - 2026-09-18

### Fixed

- **Student Score Trend Chart Mobile Layout:**
  - Added `width: 100%` to `.chart-canvas-wrap` in `analytics.css` and `.student-charts-layout`, `.student-chart-primary`, `.student-chart-secondary` in `student.css`.
  - Updated `@media (max-width: 768px)` in `student.css` to `align-items: stretch` with `width: 100%; min-width: 100%` on chart wrappers and `#complianceHistoryPanel .chart-container--interactive`, eliminating empty right void and squished charts on mobile viewports.
- **Settings Sticky Footer Positioning & Scrim:**
  - Updated `.settings-sticky-footer` in `forms.css` with `bottom: 0`, safe-area-inset padding `max(var(--gl-spacing-3), env(safe-area-inset-bottom, 0px), 12px)`, and elevation shadow `box-shadow: 0 -4px 16px rgba(0, 0, 0, 0.12)`.
  - Removed negative bottom margin in `course.css` (`margin-bottom: 0`), ensuring sticky save bars sit flush against the viewport bottom across preferences and course settings without background content bleeding through underneath buttons.
- **Course Settings Compliance Checks Table Mobile Responsiveness:**
  - Updated `#checksTable` at `@media (max-width: 480px)` in `course.css` to use `table-layout: auto !important; min-width: 320px !important;` and hidden `<colgroup>`.
  - Replaced `word-break: break-word` with `overflow-wrap: break-word; word-break: normal; min-width: 170px !important;` on the Name column and `.check-name`, preventing words from breaking vertically into 1-2 character fragments while maintaining smooth horizontal table scrollability.
- **Course Card Action Buttons & Status Badge Overlap:**
  - Added `flex-wrap: wrap; row-gap: var(--gl-spacing-2); column-gap: var(--gl-spacing-3);` to `.course-card-footer` and `flex: 1 1 auto;` to `.course-card-indicators` in `cards.css`.
  - Added `flex-wrap: wrap;` to `.course-card-actions` in `cards.css`, `course.css`, and `00-mobile.css`, preventing the warning chip badge (`[ ⚠ 1 ohrozené ]`) from being clipped or overlapped by the `[ Zobraziť ]` action button across desktop multi-column grids, tablet, and mobile cards.
- **Service Worker Cache Version Bump (`gitpulse-v616`):**
  - Bumped `CACHE_VERSION` in `sw.js` to `gitpulse-v616`.

## [2026.9.30.post34] - 2026-09-18

### Fixed

- **Archived Course Action Buttons (SSR First Paint):**
  - Configured `disabled` and `disabled_reason` directly in server-side Jinja templates (`course_detail.html`, `team_detail.html`, `project_detail.html`) when `not course.is_active`. Action buttons (`Add Group`, `Import from GitLab`, `Sync All`, `Run Checks`, etc.) now render with native `disabled` attributes and `.gl-tip-wrap` tooltip wrappers from the very first paint, preventing clickability and visual flash before client-side JS evaluates.
  - Added `!important` to `.is-course-archived .btn[data-process-lock-when]` and `.btn:disabled` rules in `buttons.css` to guarantee disabled styling overrides button variant backgrounds (`.btn-primary`, `.btn-warning`) immediately on load.
- **Page Header & Card Header Button Wrapping:**
  - Added an optional `badge` parameter to `page_header` macro in `components/layout.html` and wrapped the heading in `.page-header-title-row` (`display: flex; align-items: center; gap: var(--gl-spacing-3); flex-wrap: wrap;`).
  - Moved the `Course Owner` badge in `course_detail.html` out of `.page-header-actions` and into the title row beside `<h1>`, ensuring header action buttons have full horizontal space and do not wrap into a ragged 3-line layout.
  - Replaced unconditional `.card-actions { width: 100%; }` on mobile in `cards.css` with `.card-actions:has(.search-box, .search-box-inline, .form-group, input, select) { width: 100%; }`, preventing button-only card headers (such as `Run Checks` and `Export`) from wrapping beneath short card titles.
- **Filter Whitespace Band & Tab Ink Flicker:**
  - Updated `table_controls` macro in `components/tables.html` to trim and verify whether `filters` and `search` are non-empty before rendering their container elements, eliminating empty `.table-controls-filters` `<div>` tags that expanded into full-width blank bands on mobile.
  - Added `.tabs-nav:has(.gp-tab-ink) .tab-btn::before, .tabs-nav:has(.gp-tab-ink) .tab-btn.active::before { border-bottom-color: transparent !important; }` in `interactions.css` to prevent duplicate underline rendering when switching tabs.
  - Updated `inkTo(tab)` in `motion.js` to synchronously snap with `G.set()` on the first activation or when reduced motion is preferred, preventing the tab ink line from swiping across the screen from `x: 0`.
- **Table Row Highlight Conflicting with Sticky Actions:**
  - Removed destructive `.data-table tbody tr:hover > td { background: transparent; }` override on touch devices in `20-small-touch.css` that created a visual seam against opaque sticky action cells.
  - Synchronized sticky `td:last-child` cell backgrounds across all row states in `tables.css` (`tr:hover`, `tr:active`, `tr[data-navigate]:active`, `tr.is-nav-busy-tint`, `tr.is-selected`, and `tr[data-parent-team]`).
- **Mobile & Tablet Pagination Layout:**
  - Replaced the 3-row centered column stacking in `navbar.css` (≤900px) and `00-mobile.css` with a compact, balanced 2-row layout: top row displays record count on the left and page size on the right (`order: 1` and `order: 2, margin-left: auto`), while pagination navigation centers cleanly on the bottom row (`order: 3, width: 100%`).
- **Mobile Fluid Width Container Enforcement:**
  - Reinforced `.main-container { width: 100% !important; max-width: 100% !important; box-sizing: border-box; }` in `00-mobile.css` to ensure full-bleed layout on mobile viewports without container clipping or horizontal margins.
- **Commit Message Truncation in Student Tables:**
  - Set `min-width: 180px` on `.col-commit-message` and `min-width: 160px; max-width: 48ch;` on `.commit-message-cell` in `student.css`.
  - Added `min-width: 460px` on `#commitsTable` and updated `.commit-message-cell` in `00-mobile.css`, preventing 2-3 character premature text truncation (`Me...`, `Up...`) and allowing smooth horizontal scrolling instead.
- **Service Worker Cache Version Bump (`gitpulse-v615`):**
  - Bumped `CACHE_VERSION` in `sw.js` to `gitpulse-v615`.

## [2026.9.30.post33] - 2026-09-18

### Fixed

- **Mobile Toast Notifications Layout & Width:**
  - Resolved severe toast squishing on viewports ≤768px and ≤480px where toasts shrank into a ~22px narrow column with single letters breaking vertically.
  - Overrode desktop `width: min(24rem, calc(100vw - var(--sidebar-width) - var(--gl-spacing-7)))` in both `00-mobile.css` and `10-tablet.css` with `width: auto !important; max-width: calc(100vw - 1.5rem) !important;` and `.toast { width: 100% !important; min-width: 0 !important; box-sizing: border-box !important; }`.
- **Mobile Top Bar User Dropdown Menu Alignment:**
  - Fixed issue where clicking the user avatar in the top-right corner caused `.gl-user-dropdown` to detach and jump to the top-left edge of the screen.
  - Replaced `position: fixed; left: var(--gl-spacing-3); right: var(--gl-spacing-3);` in `00-mobile.css` with `position: absolute; top: calc(100% + var(--gl-spacing-2)); right: 0; left: auto; min-width: 220px; max-width: min(280px, calc(100vw - var(--gl-spacing-4)));`, anchoring the menu directly beneath the avatar.
- **Card Header & Table Header `info-tip` Question Mark Inline Layout:**
  - Added native `info_tip` parameter support to `card()` macro in `components/cards.html`, rendering tooltips directly inside `<h3 class="card-title">...</h3>`.
  - Replaced rigid `flex-direction: column; align-items: stretch;` on `.card-header` in `00-mobile.css` with `display: flex; flex-direction: row; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: var(--gl-spacing-2) var(--gl-spacing-3);`.
  - Removed orphaned `info-tip` elements from `card-actions` across `_users_table.html`, `_compliance_settings.html`, `_teachers_content.html`, `_detail_content.html`, `_analytics_content.html`, and `_activity_content.html`, eliminating orphan line breaks.
- **Cross-Page Mobile Responsiveness & Overflow Audit:**
  - Audited all 12 core application pages across 390px and 360px mobile viewports using Playwright, verifying 0 document-level horizontal overflows and clean wrapping of table controls and action bars.
- **Service Worker Cache Version Bump (`gitpulse-v614`):**
  - Updated `CACHE_VERSION` in `sw.js` to ensure immediate invalidation of cached bundles in client browsers.

## [2026.9.30.post32] - 2026-09-18

### Fixed

- **Contoured active indicator bar for Quick Access tabs:** rounded the active indicator ink stripe on `.gl-qa-tabs` (`border-radius: 0 0 calc(var(--radius-md) - var(--gl-spacing-1)) calc(var(--radius-md) - var(--gl-spacing-1))`) so that it contours and hugs the bottom edge of the active tab pill without sharp, protruding corners.
- **GSAP motion preservation for segmented controls:** updated `motion.js` (`inkTo()`) to animate `width` directly instead of horizontal `scaleX` from a 1px base when handling segmented pill controls (`.gl-qa-tabs` or `data-tabs-segmented`), preventing GSAP from distorting the circular corner radius into an elliptical flat edge while preserving high-performance `scaleX` transitions for underline tabs.
- **Comprehensive CSS tokenization across Quick Access & tabs:**
  - Standardized all `.gl-qa-tabs` padding and gap to `var(--gl-spacing-1)` and tab border radius to `calc(var(--radius-md) - var(--gl-spacing-1))`.
  - Tied `.gp-tab-ink` and `.gl-qa-tabs .gp-tab-ink` directly to `var(--gl-tab-selected-indicator, var(--primary))` across `interactions.css` and `home.css`, making tab indicators across every page and template completely dynamic and responsive to theme (dark/light) and accent color preferences (indigo, blue, green, red, gray).
  - Tokenized Quick Access list item spacing, avatar radius (`var(--radius)`), and traffic light dot indicators (`.gl-qa-dot--green`, `.gl-qa-dot--yellow`, `.gl-qa-dot--red`) using GitLab Pajamas design tokens (`var(--gl-green-400)`, `var(--gl-orange-400)`, `var(--gl-red-400)`), eliminating all hardcoded hex values.
- **Full template and page audit for styling integrity:** audited all Jinja templates across the codebase to ensure zero unintended static inline styles and complete reliance on centralized CSS tokens.
- **Service Worker cache version bump (`gitpulse-v613`):** updated `CACHE_VERSION` in `sw.js` to ensure client browsers immediately invalidate cached assets and receive the newly compiled CSS and JavaScript bundles.

## [2026.9.30.post31] - 2026-09-18

### Fixed

- **Dashboard grid layout alignment with GitLab Pajamas design:** modernized `.gl-home-layout` grid tracks in `home.css` to `grid-template-columns: minmax(0, 1fr) var(--gl-home-sidebar-width, 320px)` with `var(--gl-spacing-6)` (24px) gap. In Fixed layout width mode, the 1280px container centers the dashboard with an ~900px main column and 320px sidebar. In Fluid layout width mode, the container expands across 100% of the viewport, keeping the 320px Quick Access sidebar docked against the right margin while the main column and the 4 KPI stat cards (`repeat(4, 1fr)`) stretch proportionally to fill all available horizontal space, matching GitLab.
- **Segmented control pill tabs for Quick Access:** replaced underline tabs in Quick Access with GitLab-identical segmented control pill styling (`--gl-segmented-control-track-bg`, `--gl-segmented-control-track-border`, `--gl-segmented-control-btn-active-bg`, `--gl-segmented-control-btn-active-color`) across dark and light themes, providing an authentic solid pill active indicator and smooth contrast transitions.
- **Subtle card border harmonization:** updated `.gl-home-card` and `.gl-home-sidebar-panel` to use `var(--gl-border-color-subtle)` (matching GitLab's subtle dark card outline) with smooth hover transitions to `var(--gl-border-color-default)`.
- **Elimination of inline style attributes in templates:** audited and completely eliminated static inline `style="..."` attributes across templates:
  - `_weekly_deadlines.html`: replaced inline styles with CSS classes `.wd-toggle-btn` and `.wd-toggle-title` styled with design tokens in `course.css`.
  - `admin_courses.html`: removed redundant inline `style="width: ...px;"` from `<col>` elements (already governed by `admin.css`).
  - `table_heads.html`: removed redundant inline `style="width: ...px;"` from `<col>` elements in `users_table_head()` and `teams_table_head()`, synchronizing exact column width rules directly in `admin.css`.
- **Preferences Save Changes button anti-spam guard fix:** prevented the anti-spam submit helper from unconditionally re-enabling guarded buttons after 5 seconds or page scrolling when marked with `btn-save-guard` or `data-no-anti-spam="true"`.
- **Elimination of IDE diagnostic errors and false syntax underlines:** resolved false-positive JavaScript syntax errors (`Unexpected keyword or identifier. javascript`) caused by a literal `<script>` tag inside a Jinja comment in `base.html`. Added workspace `.vscode/settings.json` and `jsconfig.json` configuring Python virtual environment path, suppressing script/style validation in Jinja template files, and setting browser DOM ES2022 JavaScript environment.
- **Service Worker cache version bump (`gitpulse-v612`):** bumped `CACHE_VERSION` in `sw.js` to ensure immediate client cache invalidation and delivery of the rebuilt CSS bundles.

## [2026.9.30.post30] - 2026-09-17

### Fixed

- **Bypass in-memory asset hash caching in development mode:** updated `_compute_asset_hash()` in `src/app/main.py` so that when `settings.is_development` is True, SHA-256 hashes of static bundles (`styles.bundle.css`, `core.bundle.js`) are computed on demand from disk rather than cached for the process lifetime. This guarantees that rebuilt CSS/JS bundles immediately bust browser cache (`?v=<hash>`) during local development without requiring manual uvicorn daemon restarts.
- **Service Worker cache version bump (`gitpulse-v611`):** bumped `CACHE_VERSION` in `sw.js` to ensure client browsers invalidate stale static asset caches and fetch the fresh stylesheet bundles containing seamless horizontal flex-stretching for course teacher search controls.

## [2026.9.30.post29] - 2026-09-17

### Fixed

- **Exempt localhost from rate-limiting in development mode:** passed `dev_mode=settings.is_development` to `RateLimitMiddleware` in `main.py` so that local requests (`127.0.0.1`, `::1`, `localhost`, `testclient`) are not throttled by the strict 10 req/min auth limit on `/dashboard/login` during automated E2E testing or rapid persona switching in dev.
- **Enhanced demo course persona seeding:** extended `scripts/seed_demo_course.py` to automatically provision `teacher` and `admin` accounts with correct course ownership and active status alongside `demo.ucitel`.
- **Comprehensive persona E2E test suite:** added `scripts/e2e_test_all_personas.py` validating 96 individual UI/API interactions across Admin, Teacher, and Student roles with 100% test pass rate. Pruned obsolete scratch artifacts.
- **Normalized Course Teacher role selector button width:** styled `.teacher-add-row .teacher-add-role-select .gl-dropdown-toggle` with `width: 100%`, `display: inline-flex`, and `justify-content: space-between` so the dropdown button fills its allocated container across horizontal length, eliminating awkward dead empty space between the role selector and the filter tabs without altering vertical height.

## [2026.9.30.post28] - 2026-09-17

### Fixed

- **Elimination of "Save Changes" button flicker on page load:** rendered `btnSaveTeachers` disabled by default directly in SSR with standard `btn-save-guard` class, initial server-side `disabled_reason` tooltip wrapper, and `:disabled="!isDirty || isArchived"` Alpine binding. Removed the post-mount JavaScript mutation in `course-teachers.js` that was dynamically wrapping the button in a tooltip `<span>` and flipping disabled state after paint, eliminating the initial visual flash on page load.
- **Removed bespoke CSS overrides in Course Teachers stylesheet:** deleted ad-hoc overrides for `.gl-dropdown-toggle`, `.search-box input`, `.table-controls-search`, and `.col-teacher-role .gl-dropdown`, as well as redundant hover locks. Preserved solely the responsive horizontal selector row expansion (`.teacher-add-row`, `.typeahead`, and `.teacher-add-role-select`), letting core component CSS (`dropdowns.css`, `forms.css`, `tables.css`, `buttons.css`) govern all styling.

## [2026.9.30.post27] - 2026-09-17

### Fixed

- **Elimination of dual active tab indicators on Course Teachers filters:** resolved Alpine `:class` dynamic binding collision where static SSR `.active` class persisted alongside newly clicked filter tabs, causing multiple tabs to show active underlines simultaneously. In `layout.html`, static `.active` is suppressed when `x_class` handles dynamic states, and `setRoleFilter` synchronizes DOM classes and `aria-selected` attributes cleanly.
- **Restoration of click warning toasts on archived course actions:** replaced native `disabled` attributes on archived course action buttons (role dropdown toggles, trash buttons, clear-all action) with `data-archived-locked="1"`. This allows click events to reach `30-htmx-progress.js` and Alpine handlers to show the user-facing warning toast explaining that the course is archived and read-only.
- **Reversion of teacher add row controls to standard height (32px):** removed vertical 38px height overrides from `course.css` while preserving horizontal flex layout across available space.
- **Shifted GitLab User ID column left in User Management:** tightened `col-username` width from 177px/165px to 152px/150px across `<colgroup>` and CSS rules, repositioning the GitLab User ID column cleanly to the left.
- **Established architectural rules for Table View Tabs vs Filter Tabs:** documented in `CLAUDE.md` that count badges belong strictly on tabs switching to distinct entities/tables with divider separation (`apart: true`), while simple row filter tabs must never carry individual count badges, and card header `Showing X` belongs only when a table has no pagination.

## [2026.9.30.post26] - 2026-09-17

### Fixed

- **Elimination of Course Teachers reload layout shifts and 2x table growth:** aligned table row height reservation (`reserve_row_px=54` for 54px teacher row height) and initial row reservation (`_reserve_count`) directly with the initial query filter (`?role=...`). Alpine factory (`teacherManager`) initializes `roleFilter`, `sortKey`, and `sortDir` directly from URL search parameters on instantiation, eliminating client-side double-render cycles and preventing table jumping/flickering. Pre-rendered `.active` class in `filter_tabs` eliminates first-frame active line flickers.
- **Alignment with Admin Users tab patterns:** removed count badges from role filter tabs on Course Teachers (`/dashboard/courses/{id}/teachers`) to match the clean navigation pattern of User Management (`/dashboard/admin/users`). Sized the role selector dropdown and search input to 38px height with flush alignment against filter tabs.
- **Standardized component-level disabled styling:** eliminated ad-hoc CSS overrides and `!important` declarations in `course.css`. System-wide `.form-input:disabled` and `.search-box input:disabled` styling in `forms.css` combined with `:hover:not(:disabled)` prevents hover glow on disabled controls cleanly across the application.

## [2026.9.30.post25] - 2026-09-17

### Changed

- **Dead code removal and component standardization across Course Teachers:** cleaned up unused component overrides, dead CSS rules (`.no-teachers`, `.teacher-actions`, duplicate `.teachers-table` blocks, non-existent `.typeahead-wrap`), and orphaned overrides in `forms.css`, `tables.css`, and `course.css`. Standardized Course Teachers table (`/dashboard/courses/{id}/teachers`) to use core UI component macros (`table_empty`, `btn_icon_only`, `table_count`, `filter_tabs`, `table_controls`, and `page_config`).
- **Table controls and UI consistency alignment:** unified table controls layout with standard search and role filter tabs, eliminating bespoke margins and overrides so the Course Teachers page shares the exact same base styling and alignment as User Management and Course Management. Hardened `canClearAll` and `clearAll()` to safeguard course owners and admins, and refined `isDirty` state tracking.

## [2026.9.30.post24] - 2026-09-17

### Fixed

- **Flicker-free tabs, badges, and dropdowns on page reload:** resolved initial paint layout shifts and flashing on page refresh across course management. Filter tabs (`filter_tabs`) now retain server-rendered `.active` state and pre-rendered count badges from frame 0 even when Alpine bindings are present, preventing search bar compression and badge pop-in during client hydration. Role selection dropdown (`alpine_select`) and header counter (`table_count`) now support server initial labels and counts.
- **Table geometry stabilization on Course Teachers:** standardized `<colgroup>` and column styles on Course Teachers (`/dashboard/courses/{id}/teachers`) to match the fixed-width pattern from User Management (`col-teacher` auto min 200px, `col-teacher-account` 170px, `col-teacher-role` 190px, `col-teacher-actions` 80px), eliminating column deformation and width snapping on F5 refresh.
- **Archive warning toasts on read-only course action buttons:** removed native HTML `disabled` attributes that blocked click events on archived course buttons. Actions (`clearAll`, `remove`, `changeRole`, `pickDefaultRole`, `toggleRoleMenu`, and form submit) now capture user clicks and display clear warning toasts explaining that the course is archived and read-only.

## [2026.9.30.post23] - 2026-09-17

### Fixed

- **Course teachers page missing toasts & archived action feedback:** on course teachers management (`/dashboard/courses/{id}/teachers`), actions on archived or read-only courses (`add`, `remove`, `changeRole`, `clearAll`, `onSubmit`) silently returned without user-facing toasts or explanation. Added immediate toast feedback alerts (`Course is archived and read-only`), confirmation toasts for successful teacher add, remove, and role changes, and validation guards.
- **Table deformation, jumping and layout shift on empty filter states:** switching role filter tabs on the teachers page to an empty category previously unmounted the entire table container, destroying column geometry and collapsing card height before rendering an external empty state. Stabilized table rendering: the table header and column widths stay mounted and locked, and filtered empty states render cleanly as `<tr class="table-empty-row"><td colspan="4">...</td></tr>` inside `<tbody>`.
- **Filter tab and column sort state lost on page refresh:** across the application (including course teachers, compliance checks, and sortable tables), table filter selection (`role`, `check_filter`) and column sorting (`sort`, `dir`) were stored only in ephemeral component memory and wiped on browser reload. Integrated bidirectional URL query parameter synchronization (`URLSearchParams` via `history.replaceState`) in `course-teachers.js`, `sortable-table.js`, `components.js` (`TableFilter`), and `10-sections.js` so user filter and sort state persists seamlessly across reloads and shares.

## [2026.9.30.post22] - 2026-09-17

### Fixed

- **Issues-to-Address member highlight was invisible on target arrival:** clicking an affected student link in the Issues to Address panel smoothly scrolled up to the members table, but the highlight effect appeared invisible or disappeared before the scroll arrived. In `motion.js`, `_rgbOf` failed to parse modern CSS Color 4 formats (such as `color-mix(in srgb, #7b58cf 80%, #fff)` used for `--primary`) where Chromium returns `color(srgb 0.58 0.47 0.84)`, resulting in `rgba(1, 0, 1, 0.22)` (effectively black). In addition, smooth scroll duration (400-500ms) raced with the previous 600ms flash duration. Resolved with robust 2D canvas pixel normalization in `_rgbOf`, dedicated `--gl-anim-highlight: 1.8s` token, and ClientPaginator page switching when the target member row is on another table page.

### Changed

- **GitLab CI/CD and repository workflow standardized to industry best practices:** added `workflow:rules` to avoid redundant MR + branch pipeline runs, configured global pip wheel caching keyed on `requirements.lock`, integrated JUnit XML test reporting and Cobertura coverage artifacts into `unit-tests` and `integration-tests`, added container registry image publishing with OpenContainers provenance labels, automated release creation via GitLab `release-cli` on git tags, and added repository `.gitattributes` generated file handling along with structured GitLab Issue and Merge Request templates.

## [2026.9.30.post21] - 2026-09-16

### Fixed

- **A webhook rejection reached GitLab as an HTML page:** the error boundary rewrote every 4xx from a POST without `Accept: application/json` into the browser error page - the rule meant for a plain form submit. GitLab's deliveries send no Accept header, so the 422 the receiver describes ("Payload is not a GitLab webhook (bad or missing: project.id)") landed in GitLab's delivery log as a `<!DOCTYPE html>` document, and the same happened to every script talking to `/api/v1` with curl. Anything under `/api/` answers JSON whatever the caller accepts.
- **A webhook with `project: null` was a 500** (`{}.get` on None after the schema had admitted the null) - GitLab retries a 5xx for 24 hours. The receiver reads the validated payload and answers 422.
- **A negative `limit` was a 500:** `/api/v1/events/recent`, `/api/v1/events/dlq` and the operations log passed `limit=-5` into `LIMIT` and answered with asyncpg's "LIMIT must not be negative". The two API endpoints reject it with 422 (`ge=1`); the operations log, which parses by hand, clamps limit to 1..500 and offset to 0 or more.
- **An empty, truncated or foreign POST to the course settings form wiped the dates:** every blank field on that form means "clear", so a body without the page's fields answered 200 and nulled the semester dates, the deadlines and the auto-archive flag. The page always posts the `expected_settings_updated_at` it was rendered from; a body without it is turned away with the conflict redirect. The UI's own save (JSON PUTs) is unaffected.
- **A group import that saw no projects deactivated every project in the course:** GitLab returns 200 [] for a group whose projects the token cannot see, and the reconciliation read that as "everything was deleted". With nothing observed there is nothing to reconcile against - it logs and leaves the projects alone.

Found by sweeping every route (2 322 GET requests as admin, teacher and student with real, unknown and malformed ids and hostile query strings; 380 writes with empty, wrong-typed and garbage bodies; the webhook receiver with non-object payloads), clicking every control on every page in both themes, and running the metrics, telemetry and auto-archive jobs against the local database. Each fix carries a test that exercises the code, not its text.

## [2026.9.30.post20] - 2026-09-16

### Removed

- **Dead code the type checker cannot see - 40 functions, methods and classes nothing names (878 lines):** the GitLab client's write methods (`create_branch`, `create_file`, `update_file`, `delete_file`, `create_merge_request`, `merge_merge_request`, `create_mr_note`, `create_issue_note`, `add_project_hook`, `lint_ci_config`, ...) in an app that only ever reads GitLab; nine Pydantic schemas no route returns (`MessageResponse`, `CustomCheckRead`, `JobStatus`, `SupportTicketDetail`, ...); `has_course_role` / `get_course_memberships`, the `with_backpressure` decorator, `cached_fragment`, `enqueue_auto_archive_sweep`, `batch_get`, `check_reachable`, `get_membership_changes` / `get_inactive_members`, the bulk-action telemetry trackers; and the flagged-team feature that was only half there - service methods nothing called, record and enum types, and the home page's "unresolved group flags" card that counted rows of a table nothing ever wrote (two catalogue strings with it; the table and model stay for a migration to drop).
- **A parameter threaded through three routes and two RQ entrypoints into a method that ignored it:** the LLM analysis deliberately answers in the configured language, not the UI locale, yet every enqueue passed the locale along. Gone end to end.
- **Dead branches on typed objects:** `hasattr(settings.secret_key, "get_secret_value")` on a `str`, `hasattr(u, "avatar_url")` on a `User`, `hasattr(_err_type, "value")` on an enum, `hasattr(computed_at, "date")` on a datetime, `hasattr(cs, "course")` on a mapped relationship; `getattr(settings, "llm_analysis_enabled", getattr(settings, "feature_llm_suggestions", False))` at 21 sites for a property that always exists - the surfaces read `settings.llm_analysis_enabled` and the contract test now forbids a fallback to the raw flag (which would have let production expose what the gate hides); the same for `teacher_api_token_role`, `arena_email_api_token`, `semester_grace_days`, `semester_default_length_weeks`, `semester_auto_archive_enabled`.

### Changed

- **131 function-local imports of stdlib and required libraries hoisted to the module top** (51 modules): `from sqlalchemy import select` inside a request handler, `from datetime import datetime as _dt` inside a loop - habit, not cycle avoidance; optional and heavy dependencies (OpenTelemetry, Pygments, OpenAI, httpx) stay lazy, as does anything inside a try block. One test patched `sys.modules["rq.job"]` to reach a lazy import; it patches the name where it is used now.
- **Module state as objects, not `global` statements:** the GitLab token-health mirror is one `_LocalMirror` dataclass with a `reset()` (the tests stop poking three module attributes by name); the rate-limit Redis client is a one-entry `lru_cache` keyed by URL instead of two globals and a `type: ignore`; the two health-endpoint caches share one `_Recent[T]` class.
- **`api/dashboard/students.py` (2 010 lines, one route) is a package like the other dashboard domains:** `routes.py` keeps the page, `diffs.py` holds the diff rendering (line stats, file views, tree, syntax highlight, note code context), `notes.py` the discussion view (note views, threads, MR event classification).
- **`app/middleware/`:** the seven ASGI middlewares and the error pages they render move out of `observability/` (which keeps logging, metrics, tracing) into their own package without the `_middleware` suffix - `middleware/security.py`, `rate_limit.py`, `correlation.py`, `locale.py`, `logging.py`, `performance.py`, `error_boundary.py`, `error_pages.py`. Docs updated (`02-architecture.md`, `13_observability.md`, the docs-site structure page).
- The support form redirect no longer opens a database session to issue a 303.

## [2026.9.30.post19] - 2026-09-16

### Changed

- **Source layout the way GitLab lays out its application; shorter names:** the dashboard is one package per domain (`api/dashboard/home/`, `courses/`, `teams/`, `projects/`, `admin/` - `routes.py` composes the page, the sibling modules hold the SQL and view models, the package `__init__` exposes the router), like `app/controllers/<domain>/`. The router helpers that register no route moved to `api/helpers/` (`sync.py`, `job_guards.py`, `telemetry.py`, `telemetry_deps.py`, `utils.py`), like `lib/api/helpers/`. Services are grouped by domain like `app/services/<domain>/`: `gitlab/` (client, cache, token health), `gitlab_import/` (the group import and its persistence, email enrichment, normalisation, helpers - five underscore-prefixed siblings before), `llm/` (service, redaction, course context, types); `course_service` / `event_service` / `audit_service` / `member_sync_service` dropped their suffix, `webhook_configurations` is `webhook_configs` in services and schemas, `courses_gitlab_import` is `course_import`, `admin_system_routes` is `admin/system`. 45 modules moved, every import, patch target and path string rewritten; the module docstrings, `docs/02-architecture.md` (section 2.0 maps each GitLab directory to its GitPulse package) and the docs-site structure page describe the new tree. The support upload endpoint computed its target directory from its own `__file__` and, one level deeper after the move, wrote uploads to a directory nothing serves - fixed and pinned by a test. Type-checked strict: mypy reports no issues in 244 files; 3 843 unit tests pass.

## [2026.9.30.post18] - 2026-09-16

### Fixed

- **A modal puts focus where the reader will type and gives it back when it closes:** every modal opened with its header "x" highlighted - the first focusable element in DOM order - one Enter from closing; it focuses the first field in its body now (the dialog itself, which carries `tabindex=-1`, when there is none), and on close focus returns to the control that opened it - a keyboard user was dropped at the top of the document after every modal. A confirm dialog over a form does not steal focus from it. Audited every modal on the dashboard, course, settings, users, courses and team pages: `role=dialog`, `aria-modal`, scroll lock, Escape and backdrop close, focus in and back.

## [2026.9.30.post17] - 2026-09-16

### Fixed

- **Charts empty after an in-app navigation (User Role Breakdown on System, the score trend and skill profile on a student, the Teacher's Checklist):** base.html put the per-page vendor libraries (`extra_head`: Chart.js) at the very END of `<head>`, after the page bundles (`extra_scripts`). Deferred scripts execute in document order and the in-app navigation loader (`_loadScriptsSeq`) keeps that order, so every chart's init ran with `Chart` undefined. On a cold load the inits waited for the `load` event, which an in-app navigation never fires - so after clicking System in the sidebar the role card showed its subtitle over an empty box, and the same on the student page. The vendor blocks come before the page bundles now. Verified: every chart draws on a cold load and after an in-app navigation (role breakdown; checklist, week bar and ring; history and skill radar), and a full in-app walk of fifteen pages reports no table without rows or an empty state, no empty paginator, no loading mark left on screen, no undrawn canvas, no modal that fails to open and no script error.

## [2026.9.30.post16] - 2026-09-16

### Removed

- **Dead CSS - 69 class selectors, 107 rules, 19 stylesheets:** every class no template, script or view names (the corpus scan treats Jinja and string-built families as live and keeps anything a test pins): the `expandable-details` component (seven rules), `courses-filter-toolbar`, `dlq-header-actions`, `col-dlq-id`, the `stat-pill` family, `commit-branch-badge/-filter`, `commit-message-badges`, `mr-activity-av--img`, `meta-label`, the `theme-switcher--menu` variant and the `:not()` clauses that guarded against it, `gl-dropdown-header`, `gl-dropdown-item-description`, `gl-home-count`, `gl-activity-icon`, `health-dot`, `gl-filtered-search-bar`, `table-note`, `col-env` / `col-label` / `stat-grid-4` / `gl-page-header` in the responsive sheets, `tag-remove`, the `dot-*` status dots, `nav-item`, `tree-toggle-icon`, `disclosure-chevron` in the shared transition lists, `action-bar` in the print rules, and twenty-five unused utilities (`opacity-*`, `container--*`, `border-bottom*`, `flex-fill`, `gap-4`, `ml-3`, `overflow-hidden`, `pointer-events-none`, `rounded-50`, `sr-only-xs`, ...). A multi-selector rule keeps its live selectors; a `:not(.dead)` clause is dropped (it always matched). Verified pixel for pixel: eleven pages screenshotted before and after differ only in the clock digits in the top bar.

## [2026.9.30.post15] - 2026-09-16

### Fixed

- **One spinner in the app:** the project page's analysis indicator rendered the app's tanuki mark and then ADDED `.spinner` - the retired plain ring - on top of it while a run was in progress: two spinners drawn on one element. It stays the tanuki while running and becomes the success / failure disc when done (the ring is the mark's `::before`, switched off with the status class). The plain ring, its one size and its tokens (`--gl-spinner-track/-segment`, `--gjb-spinner-track`) are gone.
- **Two marks that never stopped:** the course card's sync badge kept spinning beside "Sync completed!" for the four seconds it lingers, and the import status box kept spinning under a finished or failed import - both stop rules named `.spinner-sm` / `.spinner`, the ring those boxes stopped drawing when they moved to the app's mark. They name `.gp-spinner` now.
- **The select chevron and the input's busy ring are per mode:** both were data-URI images with one grey (`#737278`) baked in for both themes; `--gl-select-chevron` and `--gl-input-busy-icon` carry the mode's icon grey (gray-300 on dark, gray-500 on light), and the date picker's month select reads the same token.

### Removed

- **Dead htmx plumbing:** the six `hx_*` parameters every button macro threaded through `button_attrs()`, the `hx_get` / `hx_target` / `hx_trigger` parameters of `search_input` (whose default put an `hx-trigger` on every search box for nothing - htmx in this app is driven from script, for navigation), the `.htmx-indicator` rules nothing toggled, and the unused `.btn-saving-text`.

## [2026.9.30.post14] - 2026-09-16

### Fixed

- **Semantic chart, status and diff colours per mode:** the compliance charts read `--gl-green-500` / `--gl-orange-400` / `--gl-red-400` for both modes (the 500 green is 3.5:1 on the dark page); they read `--chart-success` / `--chart-warning` / `--chart-danger` now - the -400/-300 steps on dark, the -500 on light - and so do the heatmap dots, the score-band fills and the issues chart's severity dots, stripes and badges (which were three literal hex values in project.css). The System Health palette reads the feedback icon tokens per mode. The diff lines carried GitHub's greens, reds and blues as rgba literals (`rgba(46, 160, 67, .12)`, `rgba(248, 81, 73, .12)`, `rgba(56, 132, 255, .08)`) on both themes; `--gl-diff-color-added/removed` and the six diff backgrounds are tokens per mode now (a tint of GitLab's green/red/blue on dark, the -50/-100 steps on light), and Preferences' custom diff colours still win as the inline override they are. Measured: heatmap pass/fail `rgb(45, 161, 96)` / `rgb(246, 128, 109)` on dark, `rgb(16, 133, 72)` / `rgb(221, 43, 14)` on light, the chart theme's green/red the same.

## [2026.9.30.post13] - 2026-09-16

### Fixed

- **The chart palette is the theme's:** the six categorical colours (issue, MR, review, CI/CD, quality, custom - the Teacher's Checklist bars, the week explorer bars and the legend dots) were six literal hex values written into three files, the same on both modes and two of them off GitLab's palette; they are `--chart-cat-*` tokens per mode now (dark takes the -400/-300 steps of GitLab's ramps, light the -500 to -700), read by `GP.chartTheme.colors` and by the legend CSS from the same place so a dot and its bars cannot drift. The role breakdown's five colours read the feedback tokens per mode (`--gl-feedback-danger-icon` for admins, info for teachers, success for students, brand for bots).
- **Chart fills that were not colours at all:** four charts appended a hex alpha (`'cc'`) to a colour resolved from a token - and a resolved colour is `rgb(r, g, b)`, which cannot take one, so `rgb(45, 161, 96)cc` reached Chart.js as an invalid colour. `GP.chartTheme.alpha(colour, a)` builds the `rgba()` for either notation; the checklist, the week explorer, the role breakdown and the issues chart use it. Measured: the role bars are `rgba(221, 43, 14, 0.8)` and friends, the week bars `rgba(236, 72, 153, 0.8)` on dark and `rgba(190, 24, 93, 0.8)` on light.
- **The role breakdown drew nothing when painted from the page:** its renderer returned early when Chart.js was not yet defined - the deferred library loads after the page bundle, which the fetch used to hide - and never came back. It retries once the page has loaded.

## [2026.9.30.post12] - 2026-09-16

### Fixed

- **Two more loaders that stood for no load:** the System page fetched its stats after first paint and showed "Loading role breakdown..." on every visit - a wait for one batched COUNT query the page can run itself. `build_system_stats(db)` now serves both the endpoint and the page, the stats are inlined (`#gp-system-stats`) and the role chart draws before the first frame; the script fetches only on a refresh, an SSE tick or a returning tab. The student's check heatmap had its history inlined already but still rendered "Loading check progress..." over it; the loader is rendered only when the island is absent and the wrap carries the reserved height itself. Measured: no stats request and no history request on load, no block loader visible in any frame, the role chart and the 13-row heatmap on screen at the reserved 395px.

## [2026.9.30.post11] - 2026-09-16

### Fixed

- **A loading state stands for a load that is actually happening.** Audited every spinner in the app against the path its data takes. The five tables whose first page is INLINED as an island - Events, Job History, Compliance Checks, Webhook Configurations, the student's history - rendered a "Loading..." row anyway and then held it for the 800ms minimum on every page load: a spinner for a load that never happened. The row is rendered only when the island is absent and the script has to fetch (`{% if not <first_page>_json %}`); with the island, the rows are in the page from the first byte and paint before the first frame - measured on Jobs and Events: no loading row in the HTML, no mark painted in any frame, rows and pagination on screen. The pagination bar opened with "Loading pagination..." under tables whose rows are in the page from the first byte - every one of them; it is born empty (an invisible placeholder keeps its 57px so the footer never moves) and `ClientPaginator` fills it at once; the mark, its clock rule and its translation are gone. The minimum hold is owed only to a mark the reader has seen: until the document has painted a frame `GP.loadingHoldRemaining` returns 0, so an inlined heatmap or checklist that paints before the first frame is not held either. What stays, because a fetch is real: the loading row a fetch writes into an empty table, the dimmed rows of a refresh (measured: the Events type filter with its request held dims the rows and keeps them), the System Health, User Role Breakdown and User Info loaders, and the minimum once one of those has painted - a request that answers 40ms after the mark painted would otherwise flash it. A course with no groups, no checks or no history gets the empty state at once, never a spinner.

## [2026.9.30.post10] - 2026-09-16

### Fixed

- **The accent reaches everything that carries the brand colour, not only the buttons:** links (`--gl-text-color-link`: the breadcrumbs, the sidebar section headings, every anchor, `.btn-link`), the selected tab's underline (`--gl-tab-selected-indicator`), the sorted column header and the current-week pill (`--primary`), the listbox selection (`--gl-dropdown-item-selected-bg`), the search palette's active filter, the page-load progress bar, the course-card and stat hover/focus borders, the avatar hover ring, the running job bar, the diff's target row, the motion highlight ring, the rings on the home stats (`--gl-color-alpha-blue-*`) and the brand series in charts (a new per-mode `--chart-brand` read into `GP.chartTheme.colors.brand`: the score trend line, the skill profile, the live-intelligence line; a mode or accent switch repaints a series drawn in the previous brand colour). Nine components painted `--gl-blue-*` for themselves; all read the theme now. The semantic colours are untouched: info badges/alerts/toasts, success/warning/danger, the categorical chart palettes.
- **Every link had the browser's default colour:** there was no base `a` rule at all, so any anchor without a component class of its own - a group name in the course table, "contact support" on an error page, a language link - rendered in `#0000EE` with a permanent underline, in every theme. `a { color: var(--gl-text-color-link); text-decoration: none }`, underlined on hover, as GitLab's.
- **Dark primary is blue-400:** `--primary` on dark was blue-500, 3.9:1 as text (the sorted column header, the current-week pill) on the gray-900 page; it is blue-400 now - GitLab's own dark step for the tab indicator - hover blue-300, :active blue-500, and under an accent theme the accent lightened 80% toward white. The confirm button keeps its own tokens (blue-600 on dark).

## [2026.9.30.post9] - 2026-09-16

### Fixed

- **A theme is the whole theme:** Preferences > Theme used to retint the sidebar, the selected highlight and the checked controls and stop there - the confirm button, the primary colour and the focus ring stayed blue under Indigo, Green, Red and Gray. The accent now drives `--primary` (the current-week pill, the tab underline, progress), the confirm button filled and outlined (light: the accent, hover/active mixed toward black; dark: the accent laid 78% over the page, hover the accent itself, the outlined one the accent tint) and the focus ring, in both modes, all derived from the one accent colour with `color-mix`. Links stay blue in every theme, as GitLab's do, and the danger button stays red - under the Red theme the confirm fill is a deeper red than the danger one and every danger action carries its icon. The preview cards in Preferences draw a primary-button mark in each card's own accent, so the setting promises what it delivers. Rendered and read for all six accents in both modes: dashboard header, sidebar, preference cards.
- **The dark confirm button sits with the rest:** blue-500 was the one saturated block on a dark page beside the translucent grey secondaries ("the blue button does not go with them"). Six candidates rendered side by side on the dashboard header; blue-600 with white text (5.5:1) is one step calmer and still reads as the primary action. Hover brightens to blue-500 - on a dark page a hover goes lighter - and :active settles on blue-700. Light keeps GitLab's neutral-800.

## [2026.9.30.post8] - 2026-09-16

### Fixed

- **"Upload file" opens the picker by itself:** the button in every JSON editor (Import Course from JSON, Import Full Configuration, the checks config and weekly deadlines editors, the custom-check rule) was a `<button>` whose click a script relayed to a hidden `<input type=file>` with `fileInput.click()` - one more step between the click and the browser, and a step the reader reported dead: "I click Upload file and nothing opens, in every modal". It is a `<label for>` the input now, drawn as the same button: the label's own activation opens the native picker, with no script, guard, cooldown or listener in between. The input is visually hidden (`sr-only`) rather than `hidden` - a label cannot activate an input the browser does not render - and it is focusable: Tab reaches it, Enter/Space opens the picker, and the label carries its focus ring and its disabled look (the archived-course guard disables inputs). Verified in Chromium and Firefox: click opens the picker, the chosen file lands in the editor, Enter on the focused input opens it too.
- **The file chip appeared before any file was chosen:** `.gl-json-drop-file { display: inline-flex }` out-ranked the `hidden` attribute the script toggles, so an empty pill with a file icon and an x sat beside "Upload file" in every JSON editor from the first paint. `[hidden]` is honoured now; the chip appears with the file's name once one is loaded.

## [2026.9.30.post7] - 2026-09-15

### Fixed

- **A card's explanatory line keeps one step above what it explains, everywhere:** the stat cards of Communication Indicators and the chart of User Role Breakdown sat directly on their line (0px), the webhook card had 4px, Compliance Progress and the settings cards 8px - each template picked its own utility (`mb-3`, `mb-2`, none). The gap is the card component's now (`.card-body > p.muted:first-child:not(:last-child)` in cards.css, `--gl-spacing-3`), the nine per-template utilities are gone, and a line that is the whole body (an empty-state note) keeps no margin. Measured after: 8px on all ten cards that open with a line, across the student, System, course settings and analytics pages; `test_a_card_lead_line_keeps_its_gap.py` pins it.

## [2026.9.30.post6] - 2026-09-15

### Fixed

- **A loading mark sits in the middle of what it stands for:** the table's loading row sat at the top of its reserved box with the rest of the box empty under it (Job History: a 52px row at the top of a 130px box; Events, every reserved table), and the pagination bar's mark was pinned to the left corner where the row count goes. `height: 100%` on the table resolved against nothing - a percentage needs a definite height and `min-height` is not one. The reserved box is a flex column for exactly as long as the loading row is in it (`:has(.table-loading-state)`), the table grows to the box and the extra height goes to the tbody row, not the head (measured: head 35px, row 264px in a 300px box); the pagination mark spans the bar and centres (`.gp-pagination-loading`). Measured after: the table mark centred in the space under the head on System and Events, the pagination mark at the bar's centre (811 = 811).
- **One block loading mark, also for script-built content:** `GP.renderLoaderHtml` (the User Info modal, the MR history and the live-intelligence cards) rendered a mark of its own - `.user-info-loading`, an italic caption in a different box, off the 800ms loading clock. It renders the same `.gp-block-loading` the `block_loading` macro does; the User Info modal's server-side placeholder uses `block_loading` directly and the `loader` macro, `.user-info-loading`, `.gp-loading` and `.gp-loading--block` are gone. Measured: the modal's mark is 120px, centred, upright.
- **Code blocks follow the syntax scheme and the colour mode:** a fenced block without a language tag was a fixed dark `#18171d` with light ink whatever the scheme in Preferences and whatever the colour mode; every fenced block is on the scheme's ground and ink now (`--syn-bg` / `--syn-fg`). The "None" scheme is code in the page's own colours - `--gl-background-color-strong` and `--gl-text-color-default`, so a dark block on a dark page and a light one on a light page (measured `#3a383f`/`#ececef` and `#ececef`/`#3a383f`) - instead of a fixed dark block in both modes.
- **Shadows and washes are the per-mode tokens:** the course card hover/active, the checkbox hover, the search suggestions and the support editor menus, the pull-to-refresh disc, the PWA install card and the pipeline health bar ring each carried a literal `rgba(0,0,0,…)` or `rgba(255,255,255,…)` - one value for both modes, and a white ring is invisible on a light page. They read `--shadow-sm/md/lg/xl` and `--gl-hover-subtle`, which tokens.css already defines per mode.

## [2026.9.30.post5] - 2026-09-15

### Fixed

- **No control is a white block on the dark theme:** the confirm button (`--gl-btn-confirm-*`), the outlined confirm button and the checked checkbox / radio (`--gl-control-bg-selected`, `-border-selected`, `-indicator-selected`) were GitLab's dark tokens - the light ones inverted, neutral-50 - so every primary action and every ticked box was a near-white fill on a dark page, the same thing the selected week pill was. On dark the confirm button is the primary blue with white text (4.6:1), the outlined one the selected tint, and a checked control is the theme's selection colour - blue-500 by default - with a white tick. Light keeps GitLab's neutral-800 for all three (pinned in `test_gitlab_token_parity.py` as light-only now). Preferences > Theme retints the checked controls in both modes; the confirm button is deliberately NOT on the accent, so a red theme cannot make Save and Delete the same button.

### Removed

- **Dead member-filter and pill code:** `member-filters.js` (in the core bundle; it bound `.member-filter-bar`, which no template renders), the bar / label / chip / count / reset rules in `member-filters.css` and their mobile and small-touch rules, the `.filter-pills` / `.filter-pill` rules in `forms.css` (the Users role filter is the tab strip), the `.member-filtered-out` clause in the zebra selectors, the paginator's member-filter sync, the pill and chip entries in the passive-control guard and the tooltip ignore list, the `.member-filter-bar` corner rules, and the toggle switch (`.form-toggle`, `.toggle-*`, `--gl-toggle-*`) that nothing renders. The Users tour step and both e2e control walks pointed at the pills that no longer exist; they point at the tab strip. The 420px breakpoint lived only in the dead bar and is retired from the breakpoint debt list.

## [2026.9.30.post4] - 2026-09-15

### Fixed

- **The selected highlight is a tint of the theme, not a white block:** GitLab's own `--gl-action-selected-*` is the confirm ramp inverted - near-white on dark - so on a dark page the selected week pill in Week Analytics was a white box, and hovering it swapped its text for the idle hover colour (the hover selector outranked the selected selector): light grey on white, unreadable. There is now ONE selected highlight per theme, the super-sidebar's: the accent at an alpha (`alpha-blue-25/32` on dark, blue-500 at 16/20% on light), the nav item's selected text, the accent as border. The active navigation item, the week pill, the filter pill, the member chip, the current pagination page and the mode switcher all read it, and Preferences > Theme retints all of them at once through `color-mix` (30/38/46% of the accent, text mixed 30% into the strong text colour) - the accent colour and the shell tint moved from sidebar.css to tokens.css so every theme is defined in one place. Hover on a selected pill keeps it selected (the selected week tab, `.filter-pill.active:hover`, the checked member chip). The selected exam week is the same highlight in the warning hue instead of a solid orange block with `#fff` on it.
- **Every colour is per colour mode:** 156 declarations in 20 stylesheets used ONE raw hue step for both modes - `--gl-blue-300` text (dark ramp, 2.6:1 on white), `--gl-green-50` chips with `--gl-green-700` text (light ramp, a pale block on a dark card), `--gl-red-400` icons, `rgba(255,255,255,.08)` washes that vanish on a light page (the Raw JSON toggle on System Health, the top-bar action discs). All of them now read the per-mode semantic tokens GitLab ships: `--gl-text-color-{link,success,warning,danger}`, `--gl-feedback-*-icon`, `--gl-status-*-{bg,text,icon}`, `--gl-status-brand-*`, `--gl-btn-default-*`, `--gl-topbar-search-bg`. The success and warning buttons get `--gl-btn-{success,warning}-*` per mode (bright fill + dark text on dark, -500 fill + white text on light) instead of the dark ramp hard-coded for both. Verified in the browser on the student, course, Week Analytics, Users, System and Preferences pages in both modes and with the Red accent; `test_theme_highlights.py` pins the contract.

## [2026.9.30.post3] - 2026-09-15

### Fixed

- **Week Analytics always shows a state under the pills:** clicking the active week pill used to DESELECT it and hide the whole detail panel - the card collapsed to the toolbar and the pills with nothing under them and no word about why. A week explorer always shows a week (the rule the auto-select already follows), so the active pill is a no-op like every other pill strip in the app. The detail panel's empty state - a selected week with no data, or a course with no weeks at all - is the shared empty box every empty table shows (`GP.emptyStateHtml`: icon + the reason: future week / before tracking started / awaiting sync / no activity) at the height the charts would take, so the card is the same size whether a week has data or not. It was a bare grey paragraph in a dashed frame, and nothing at all in the no-week case.

## [2026.9.30.post2] - 2026-09-15

### Fixed

- **The pagination bar loads with the spinner + label, held like every other loading mark:** the bar under a table opened either as a placeholder held transparent for 400ms (replaced within that window on every page) or, with `placeholder=false`, as a bare strip of the bar's height - a grey band saying nothing while the rows above it said "loading". `pagination_controls()` now always opens with the tanuki and "Loading pagination..." (`.gp-pagination-loading`, on the same 800ms `gp-loading-clock`), and `ClientPaginator` paints the bar through `GP.afterLoadingMinimum` - only the first paint waits, a render that arrives during the hold just updates what will be painted, every later render writes at once. Measured: the bar's mark visible 920ms on the Activity tab.
- **Activity tab is one card with two views:** Group Activity and Recent Merge Requests are two readings of one subject - what happened in this course - so they share one card and one view strip (Groups N | Merge requests N), the way Configuration on System Settings and the student's Issues card switch views (and the way GitLab's own Activity page switches Push / Merge / Issue events). `filter_tabs(panels=true)` makes the shared pill strip switch `[data-tab-panel]`s through the declarative tabs controller instead of filtering rows; each view keeps its own table, empty state and pagination. The table's top corners are squared under the strip inside the panel (`[data-tab-panel] > [data-paginator]` case). The team page keeps its two cards on purpose: Projects and Members are two resources of the group with their own actions, notes, tour steps and empty states, not two views of one thing - GitLab keeps them on separate pages.
- **Chart entrance animations play once:** every refresh path (an SSE tick, a finished job, Refresh Stats, Reload, a week switch) re-ran the page's chart init, which destroyed and rebuilt the chart, and the bars grew out of nothing a second time. `GP.chartEntrance(canvas, animation)` gives the first draw on a canvas the entrance it asked for and every later draw on the same canvas none; wired into the CI/CD doughnut, Score Trend, Skill Profile, User Role Breakdown, Teacher's Checklist and both Week Analytics charts (Issues to Address already had its own flag). Verified: role breakdown 900ms -> off after Refresh Stats, Score Trend 800ms -> off after Reload, week explorer 700/900ms -> off after a week switch.
- **Student Compliance Progress paints on load without growing:** the card fetched its history after paint and grew by the table, the summary tiles and the heatmap once the answer landed (771px -> 1130px, measured). The first payload is inlined (`#gp-student-history`, the same rows the telemetry endpoint returns), the Weekly Breakdown reserves its rows, the summary tiles are on screen from the first frame with "-" until the numbers land (value now stacked over label - both were inline spans, so a short value shared a line with its label and the tile grew 21px when filled), and the heatmap box is reserved at its final height (28px per check) with the block loader in it, handed off through the shared cross-fade. Reload and live refreshes still fetch. Inside a reserved box the table's loading mark lies in one line (spinner beside label, 52px) so it never asks for more than the rows it stands in for - the one-row Weekly Breakdown held a 228px loading table for a 103px reservation.
- **Two more first-paint shifts closed:** a card rendered `collapsed=true` (Archived Courses on the dashboard) showed its body until Alpine initialised and then snapped shut (207px -> 54px) - the body carries `display: none` from the server; the Teacher's Checklist loader wrap was fixed at 340px while the chart wrap grows 34px per check, so a 13-check chart landed 34px taller than the loader it replaced - the wrap carries the chart's height. Audited every page for cards that change height after first paint: none left.
- **CI lint (ruff-check / ruff-format):** the pipeline on `ce029fd2` failed on four test files over 100 columns / compound asserts and one pre-existing unformatted block in `app/dependencies.py` (from 2026.9.24); all formatted, `ruff check` and `ruff format --check` clean on `src/ tests/ scripts/`.

## [2026.9.30.post1] - 2026-09-15

### Fixed

- **Pages with big tables no longer hang on load - tooltips are delegated:** every `[data-tippy-content]` got its own tippy instance at boot, and every later `initTippy(scope)` pass (after each HTMX swap, after every `localizeTimes()`) re-walked the scope and called `setContent` on all of them. Profiled on User Management with 574 rows (production's size): 822ms in `initTippy` plus 524ms in `localizeTimes`, of a 1.4s main-thread block on load - 3 404 tooltips instantiated for the 25 visible rows. `GP.initTippy` is now ONE `tippy.delegate` on `<body>`: an element's instance is created the first time the pointer or keyboard focus reaches it and shown at once; rows added by a swap or by Alpine need no init call; `el._tippy` still exists for anything that has been hovered, so callers that `setContent` keep working; content is re-read from the attribute at every show; native `title` is dropped when the instance is made. Same scroll/focus rules as before. Measured after: 1 instance at boot, long tasks 1 029ms -> 345ms, load 1.51s -> 0.77s on the same 574-row page; every other page under 150ms.
- **A default sort that changes nothing touches no DOM:** `SortableTable._doSort` moved every row through a fragment even when the server had already rendered them in that order - 115ms of the same load for 574 rows. The order is compared first; only a change re-appends.
- **Users: addresses are no longer cut:** a 36ch ceiling on the Email column, put there to win back 22px of table width, cut ordinary 38-character student addresses on every page (`anton.besshaposhnikov@student.tu...`). It is gone, and the cell values are `inline-block` rather than a block with `overflow: hidden` - a block asks its column for no width, so the column stayed at its width hint and clipped even names (`Demonštračný účet vyučujúceho` in the 195px Full name column). Scanned every table on 12 pages at 1366px and 1600px: 0 cut cells; the users table scrolls 149px inside its wrapper at 1366px and fits at 1600px.

## [2026.9.30] - 2026-09-15

### Fixed

- **Activity tables show their rows, not "...":** Group Activity and Recent Merge Requests shared one row as two half-width cards, and a fixed-layout data table in a 540px card cut 39 cells - group names, MR titles, project names, dates, even the State badge - to "..." with the rest behind a horizontal scroll (measured at 1366px and again at 1600px). They are one under the other now, full width, auto layout (no `tbl-fixed`), so a column takes the width its content needs: 0 cut cells, no horizontal scroll. Dates and badges are `text-nowrap`. The webhook configurations table got the same cure (its Scope and Status cells were cut mid-word). The 1000px activity-grid breakpoint retired with the grid.
- **Cards no longer grow 57px after the script runs:** the Activity tables and the project MR list wrote their own empty `<div class="pagination-controls">`, which is `:empty`, display:none - so the card was drawn without the bar and grew when the paginator painted it. They use the `pagination_controls()` component, which reserves the bar from the first frame (measured: Group Activity 350px and Recent MRs 854px from first paint to settled, against 297 -> 350 / 801 -> 854 before).
- **Archived course stays readable:** the read-only guard locked "Edit JSON Configuration" on the settings page - a disclosure that only reveals the schedule editor - and answered "this course is read-only" to a click that changed nothing. Anything with `aria-expanded` that is not a listbox toggle (`aria-haspopup`) is now on the guard's read-only list, along with `[data-modal-close]`; the textarea behind the disclosure stays disabled. "Export Full Configuration" is marked `readonly-ok` like the checks export beside it. Verified as admin, teacher and student on the course, group, project, student, settings, teachers and activity pages: no disclosure or read control locked, every write still locked.
- **Teachers page: locked controls no longer light up on a filter switch:** the role selects are rendered `disabled`, but `.gl-dropdown-toggle` had no `:disabled` style at all, so every re-rendered row painted a white, available-looking select until the guard's observer marked it a frame later and the colour transition greyed it (~60ms flash per switch, measured frame by frame). A disabled toggle now carries the disabled tokens from its first frame, no transition.
- **Teachers page: no empty Actions cells:** an administrator's row rendered nothing in Actions, so a filter that leaves only admins (Course Owner) showed an empty column. The row carries the same remove control, disabled, with the reason: administrators always have access and cannot be removed here.
- **Communication Indicators explains itself in the body, not the header:** it was the only card passing `subtitle=` to `card()`, so its header laid out differently from every other card. The line is the first body child (`<p class="muted text-sm">`) like User Role Breakdown; the unused `subtitle` parameter, `.card-header-content` wrapper and `.card-subtitle` rule are gone.

## [2026.9.29] - 2026-09-15

### Fixed

- **A loading state that has painted stays long enough to be read (800ms minimum):** the tables and blocks with a spinner + label have their first page inlined, so the content replaced the mark within ~100ms of first paint - the Events loading row measured 93ms on screen, System's role breakdown 218ms - a flicker nobody could read ("I never get to see the state"). Every loading mark (`.gp-block-loading`, `.table-loading-state`) now runs a `gp-loading-clock` animation whose duration IS the minimum; `GP.loadingHoldRemaining` reads `duration - currentTime` off it, so the exact time still owed is known for a server-rendered mark and for one a script wrote a moment ago alike, with no timestamps or bookkeeping. The block hand-off (`GP.revealAfterLoading`) and the three island-fed tables (Events, Job History, Compliance Checks) wait it out through `GP.afterLoadingMinimum` before painting; a refresh keeps its rows and dims them, so it has no mark and no wait. Measured after: Events 932ms, Job History ~800ms, Checks ~800ms, role breakdown 987ms, System Health 1370ms (its own check). The tanuki turns once and the label is read; nothing moves when the content lands.

## [2026.9.28] - 2026-09-15

### Fixed

- **Events (and every island-fed table): the loading state is the box its content will take, with the spinner + label visible from the first frame:** the server-rendered `sk_table_loading` row carried `min-height: min(78vh, 820px)` of its own and its contents were held transparent for 400ms (`animations.css`), so on the Events page with no events - production's state - the reader saw a ~700px BLANK box that collapsed to the 170px "No events received yet" empty state the moment the deferred script ran: "the table stretches to double while loading and snaps back, and there is no spinner". The loading row now has no height of its own (when rows are coming, `data_table(reserve_rows=...)` already reserves them on the scroll viewport; when the first page is empty, what lands is the empty state, which is the same box), the icon slot is 28px in both states so loading -> empty measures identically (176px = 176px, card 231px = 231px), the Events table reserves its measured 65px two-line rows (card 458px before and after), and the table loading state and the block loader (`.gp-block-loading` - System Health, User Role Breakdown, Teacher's Checklist) are no longer held blank for 400ms: the spinner and its label are legible from the first frame, which is what tells the reader a box is waiting rather than broken. The single-frame guard stays only on the pagination placeholder, which is replaced within a frame.

## [2026.9.27] - 2026-09-14

### Fixed

- **Archived course: write actions no longer flash as available on load/reload:** `tab_content()` already marked the content well `is-course-archived` from the server, but the page-header actions (Add Group, Import from GitLab, Sync All, Run Checks) live in the page shell outside it and were dimmed only once the deferred core bundle ran the read-only guard - so on every full load or `reloadKeepScroll()` refresh of an archived course they painted in their real colours under a banner saying "read-only", then greyed a beat later. `base.html` now emits `is-course-archived` on `#main-content` itself whenever the page's course is archived (the same element the guard toggles), so the buttons are dimmed on the first frame on the course, group, project, settings, teachers and activity pages; the guard still owns the tooltip, the click answer and clearing the class after an SPA swap to an active course.

## [2026.9.26] - 2026-09-14

### Fixed

- **Sort indicator chevron coloring:** Fixed uncolored sort carets on sorted column headers. Updated CSS selectors to target `th.sorted.asc .sort-caret-up` / `th.sorted.desc .sort-caret-down` (Alpine.js places `.sorted.asc` / `.sorted.desc` directly on `<th>`) in addition to the existing `.sorted .sort-arrow.asc` pattern used by `sortable-table.js`. Active sort direction caret is now colored `var(--primary)` with full opacity; the opposite caret is dimmed to `0.22`.
- **Teacher toolbar stretch to fill empty space:** Changed the search typeahead and role dropdown in the teachers toolbar from tiny fixed widths to `flex: 1 1 auto` so they expand naturally to fill available space up to the filter tabs, eliminating the large dark empty void.
- **Teacher table row count display (Showing X of Y):** Added a `table_count(id='teachersCount')` component to the teachers card header and wired `updateCount()` in the Alpine `teacherManager()` component. The count updates reactively on filter changes, teacher additions, removals, and clear-all — matching the Configuration table pattern.
- **Teachers table renders 1:1 through the shared table component:** Removed the whole block of teachers-only `!important` overrides in `course.css` (`.card-body:has(.teachers-list-slot) { padding-bottom: 0 }`, `tr:last-child td { border-bottom: none }`, `max-height: none`, `overflow-y: hidden`, `min-height: 0`, the duplicated closed-dropdown rule). The card now ends the way Configuration on System Settings ends - the standard 24px card-body padding under the last row, the standard `max-height` scroll viewport for long lists. The private `.teachers-list-slot` reservation (and the six `clearTeachersSlotMinHeight` calls that fought it) is replaced by `data_table(reserve_rows=..., reserve_row_px=65)`, released through `GP.tableLoaded` - the same reservation Job History uses.
- **Every remaining grey-bar skeleton replaced by the spinner + label loading state:** The shimmering `.gl-chart-skel` overlay on the Issues to Address chart, the CI/CD doughnut, the weekly activity chart and both student compliance charts is gone (the compliance chart already had a spinner + label underneath it - two loading states for one box); the User Info modal and the project intelligence cards now show the tanuki spinner with a label (`GP.renderLoaderHtml`) instead of grey bars. Deleted with them: `GP.ensureChartSkeleton` and its Chart.js plugin, the `course_card(is_skeleton)` branch, the skeleton-only paths in the loading hand-off (`motion.js`), `UserInfoModal.skeleton`, and ~450 lines of orphaned skeleton CSS (`.gl-skeleton*`, `.gl-chart-skel*`, `.gl-skeleton-h-bar*`, `.gl-sk-*` utilities, `.health-skeleton-*`, `.status-dot--skeleton`, the `--gl-skeleton-*` / `--gl-anim-shimmer` tokens). One waiting state everywhere: `block_loading` / `sk_table_loading` / `GP.renderLoaderHtml`.
- **Activity table horizontal scroll restoration:** Reverted the forced `min-width: 0 !important; width: 100% !important` on `.activity-grid .data-table.tbl-fixed` that had violently squeezed grid cards to ~500px, clipping status dots and truncating column headers. Restored `.table-scrollable` min-widths (600-620px), gave `.col-activity-projects` `min-width: 85px`, and gave the MR status dot column a fixed 36px width with tight padding.

## [2026.9.25] - 2026-09-11

### Fixed

- **Table column width stabilization across filters and refresh:** Fixed table column shrinking and deformation by restoring `table-layout: fixed` and preserving `<colgroup>` visibility under the 1180px container query in `tables.css`. Columns maintain rigid widths without jumping when switching filter tabs across all system tables (Teachers, Users, Checks, Activity, Jobs).
- **Course teachers toolbar controls sizing:** Enlarged role selector dropdown (`Teacher ⌵`) to 155px with balanced chevron padding, and shrunk typeahead search input to a compact 220px to match requested visual layout.
- **Card bottom dead space and internal scrollbar elimination:** Removed unnecessary vertical table scrollbar (`overflow-y: visible`, `max-height: none`) and eliminated card bottom padding (`padding-bottom: 0`) under the teachers list slot, removing the dead empty void where pagination is not needed.
- **Loader component cleanup:** Cleaned out obsolete skeleton comments in `loaders.html` in favor of standardized spinner loading states.

## [2026.9.24] - 2026-09-11

### Fixed

- **Course teachers toolbar sizing & responsive table columns:** Decreased the add teacher search typeahead input width to a compact ~280px and widened the role selector dropdown to 130px with balanced text and chevron spacing. Replaced fixed 1167px pixel column widths with responsive percentage widths (44%, 20%, 24%, 12% = 100%) so the table fits the container width without horizontal overflow or column deformations when switching filter tabs.
- **Card bottom dead space elimination:** Reduced card body bottom padding when containing the teachers list slot and removed redundant row borders, removing the empty gap under the table where pagination was not needed.
- **Session user lookup fallback:** Added user ID, GitLab username, and case-insensitive fallbacks to `_load_user_from_session` to prevent 404 responses for tour state and activity telemetry requests.

## [2026.9.23] - 2026-09-10

### Fixed

- **GitLab Pajamas Cookie Consent Banner overhaul:** Completely redesigned the cookie consent banner to mirror GitLab Docs Pajamas callout alerts, featuring the signature top gradient accent line, elevated floating card at viewport bottom, info icon, bold title with inline link (`Zásady ochrany osobných údajov ↗`), high-contrast confirm button (`Súhlasím`), and dismiss action.
- **Notification Toast System alignment:** Standardized toasts across all 5 states (`info`, `warning`, `success`, `danger`, `tip`) to match the GitLab Pajamas callout style with top gradient accent lines, state-colored typography, smooth countdown progress indicator, and action links.
- **Documentation diagrams correction:** Replaced broken Gantt timeline chart with a clean, responsive maintenance window flowchart and substituted arbitrary pie chart percentages with an accurate rule evaluation engine architecture diagram across both Slovak and English documentation.

## [2026.9.22] - 2026-09-10

### Fixed
- **Pagination arrows consistency:** Maintained navigation buttons (`<` and `>`) in a disabled state on single-page tables rather than hiding them, ensuring pagination arrow controls remain visually consistent across all result counts and matching empty table states.
- **Commit history table alignment & stability:** Eliminated 72px indentation void on non-merge commits by standardizing `.commit-branch-wrapper`, locked columns with `tbl-fixed`, and ensured zero line-wrapping or row height shifting across merge and non-merge commits.
- **Removed commit history branch selector:** Removed redundant branch dropdown selector from the commit history panel as requested.
- **GitLab Pajamas preferences overhaul:** Redesigned Mode switcher to match GitLab's segmented button group (text-only, 32px height, rectangular radius, dark grey `#4c4b51` active state in dark mode), removed redundant accent color label to align theme cards directly under section descriptions, and structured clean section dividers.
- **Teacher add role selector flush alignment & search bar expansion:** Removed auto-margin separator on `.table-controls:has(.teachers-role-filter)` and constrained `.teacher-add-role-select` min-width to content width, allowing the typeahead input to expand fluidly and placing the role dropdown directly flush (8px gap) against the filter buttons with zero dead void space.
- **Course teachers card bottom void & internal scrollbar elimination:** Overrode `.teachers-list-slot` min-height to 0 and set `.table-responsive` max-height to `none` with visible overflow, allowing the card to size naturally to its rows without generating internal scrollbars or leaving 65px empty dark space at the bottom of the card.

## [2026.9.21] - 2026-09-10

### Fixed

- **Course teachers component refactoring & empty space removal:** Removed hardcoded `min-height: 240px` on `.teachers-list-slot` in `course.css` and cleared inline server reservation styles instantly via Alpine lifecycle hooks (`init`, `$nextTick`, DOM events), completely eliminating trailing empty dark space under the table when filtering down to single rows (e.g. Course Owner filter).
- **Archived course read-only state & mutation lock:** Passed `isArchived` through page config and component state, disabling the teacher search typeahead, default role dropdown, "Remove all restrictions" button, row-level role selectors, row-level deletion actions, and form submissions in archived courses.
- **Button flashing & race condition prevention:** Rendered `btnSaveTeachers` initially with `disabled=true` (and dynamic `:disabled="!isDirty || isArchived"`) and "Remove all restrictions" with `disabled=(not _can_clear)` and `:disabled="!canClearAll"`, preventing inactive action buttons from flashing enabled on direct page load or browser refresh.
- **Dead code removal & TDZ error elimination:** Removed obsolete pagination state (`page`, `pageSize`, `pageNumbers`, `pageLabel`, `prevPage`, `nextPage`, `search` watch) from `course-teachers.js`, safely guarded `GP.autoReloadOnJob`, resolved Temporal Dead Zone `ReferenceError` hazards in `cookie-consent.js` and `00-base.js`, and removed duplicate component declarations.
- **Table dimensions & column width stabilization:** Calibrated `.teachers-table` fixed columns (`.col-teacher: 520px`, `.col-teacher-account: 240px`, `.col-teacher-role: 280px`, `.col-teacher-actions: 127px`) matching the 1167px container budget, ensuring stable table dimensions and column widths across all filter states without violent collapsing.

## [2026.9.20] - 2026-09-10

### Fixed

- **Bot username truncation & badge alignment fix:** Widened `col-username` from 132px to 177px, adjusted `col-gitlabid` (95px) and `col-email` (280px) within the 1167px budget, removed restrictive `12ch` cap on bot usernames so usernames like `project_8323_bot` display cleanly without premature truncation, and aligned `[Bot]` and `[you]` badges to the right edge via `margin-left: auto`.
- **Compliance checks empty state & bottom summary band:** Added standard `.table-empty-state` with search icon and translated message when filter matches zero compliance checks, and moved the `Total Active Weight` summary card to the bottom of the section below the table and empty state.
- **Stretched course teacher search & controls alignment:** Stretched `.table-controls-search` (`flex: 1 1 auto`) and typeahead search box so the role dropdown sits directly against the filter buttons, eliminating the awkward gap between search controls and filter tabs.
- **Course teachers filter empty state:** Differentiated between zero total teachers (unlock empty state: "No restrictions") and zero filtered teachers (search empty state: "No teachers match the current filter.").
- **Table layout stabilization & zero collapse:** Enforced `table-layout: fixed; width: 100%;` on `.teachers-table` with calibrated column widths (`.col-teacher: 440px`, `.col-teacher-account: 220px`, `.col-teacher-role: 240px`, `.col-teacher-actions: 100px`) and `.teachers-list-slot { min-height: 240px; }` with proactive inline style clearance, preventing column jumps, deformations, and violent collapsing when switching filters or refreshing.

## [2026.9.19] - 2026-09-10

### Fixed

- **Student compliance progress chart rendering fix:** Restored missing `<canvas id="historyCanvas">` element inside `#historyChart` in `_compliance_history.html`, which had previously caused `initHistoryChart` to abort prematurely and leave the spinner spinning indefinitely.
- **Archived courses non-mutating controls whitelisted:** Extended `_READONLY_OK` in core progress guard to whitelist read-only navigation and exploratory controls (`.tab-btn`, `[role="tab"]`, `.filter-tabs button`, `.table-controls-filters button`, `.teachers-role-filter button`, search inputs, `.sortable-header`, pagination buttons, modals, info tips) in archived courses, allowing teachers and viewers to freely inspect, filter, and sort data without being blocked by the write protection toast.
- **Elimination of empty void space in course teachers list:** Proactively dropped server row reservation `minHeight` on `.teachers-list-slot` across DOMContentLoaded, script execution, role filter changes, and HTMX tab swaps, eliminating unwanted trailing grey space.
- **Card subtitle placement & header icon alignment:** Relocated "Score trend and practice tracking across the semester" subtitle from card macro argument to standard descriptive paragraph under card header inside the body (matching Teacher's Checklist and Week Analytics), and added `icon('users', size='sm')` to Groups card header in course overview.
- **Users table column width fine-tuning:** Fine-tuned `col-gitlabid` (125px), `col-fullname` (210px), and `col-email` (295px) within the 1167px table budget, ensuring longer names render with ample breathing room without clipping, and locked `min-width` and `max-width` across all columns to eliminate CLS.
- **Universal delete/remove icon standardization:** Replaced inconsistent table row removal icons (`x`, `trash-2`) with standard GitLab Pajamas `trash` icon across teacher management, admin courses, danger zone, and settings.

## [2026.9.18] - 2026-09-10

### Fixed

- **Users table column rebalance & overflow fix:** Reallocated width from `Full Name` (250px -> 180px) to `Email` (280px -> 305px) and `Created` (135px -> 145px) with `col-gitlabid` set to 145px (total 1167px, staying safely below 1200px container width without layout shift). Removed `min-width: 0` overrides on username/email/created cells that triggered CLS, expanded email truncation threshold to 36ch so university emails render unclipped, and standardized action buttons to `ghost` variant.
- **Filter tabs transparent background:** Eliminated dark grey background artifact (`#28272d`) behind tab filters in Compliance Settings and Teachers views, enforcing transparent background, baseline alignment, and removing obsolete `.check-filters` radius selectors.
- **Teacher dropdown componentization:** Removed bespoke role dropdown style overrides (`.role-dropdown`, `.teacher-add-role`) in `course.css` and template partials, fully componentizing teacher role selects to standard `alpine_select` (`.gl-dropdown`) components, and removed artificial `min-height` on `.teachers-list-slot`.
- **Integrated test job & coverage badges:** Unified the test job status and test coverage percentage into a single inline stage badge (`Tests [passed] [71.0%]`) in the student pipeline row, eliminating the redundant vertical misaligned `.mr-pipeline-coverage` container and reducing vertical scrolling space.
- **Proportional table action & button icons:** Added scoped sizing for `.btn-sm .icon` (14px) and `.btn-xs .icon` (12px) in `layout.css`, ensuring small and extra-small table action buttons render neat, proportional icons rather than oversized 16px glyphs.

## [2026.9.17] - 2026-09-10

### Fixed

- **Users table continuous header without subpixel seam:** Added explicit background fill (`var(--gl-background-color-subtle)`) to `.data-table thead` and `.data-table thead tr`, eliminating the 1px vertical slit between `Role` and `Status` columns caused by subpixel rasterization rounding over dark card backgrounds.
- **Column width locks and date truncation fix:** Increased `col-created` width from 115px to 135px in table heads and stylesheet rules to prevent ISO date truncation (`2026-04-1;`), adjusted `col-email` to 280px, and defined integer-pixel `min-width` rules across all columns (132px, 165px, 250px, 280px, 90px, 86px, 135px, 84px = 1222px total) on `.users-table` to prevent column jitter and shifts upon hydration and refresh.
- **GitLab enrichment button stability and error state:** Locked `btn.style.minWidth` during outcome transitions in `_setButtonOutcome` to prevent button width collapse or expansion when displaying outcome icons or labels; styled `.btn.btn-error` with appropriate error coloring; and wrapped `enrich_users_from_gitlab` API endpoint in structured exception handling to return clear JSON error responses and release lock flags instead of unhandled 500 errors.
- **Course detail template syntax fix:** Added missing `{% endif %}` closing tag before `{% endset %}` in `src/app/templates/partials/course/_detail_content.html`, resolving the 500 Jinja `TemplateSyntaxError` on course dashboard pages (`/dashboard/courses/<id>`).

## [2026.9.16] - 2026-09-10

### Fixed

- **Student detail compliance progress crash:** Fixed a ReferenceError on `panel` in `student-detail.js` (`loadHistory`), allowing compliance history and skill radar charts to load reliably.
- **Loading skeleton corner clipping:** Added `-webkit-mask-image` and inherited border-radius to `.gl-skeleton` and `.gl-chart-skel` shimmer pseudo-elements, preventing GPU-composited animations from escaping rounded corners, and enforced circular radius on pipeline doughnut skeletons.
- **CI/CD Health doughnut chart sizing and rendering:** Resized `.pipeline-chart-wrap` to 116px to match adjacent stat cards, eliminated the deferred `IntersectionObserver` delay, and ensured `.gl-chart-ready` is set immediately to eliminate stuck placeholder squares.
- **Admin Users table column stability:** Locked `col-gitlabid` (165px) and `col-fullname` (250px) widths with min-width and max-width on `th` and `td`, and updated `admin-users.js` live refresh to mutate `.users-cell-value` preserving ellipsis and boundaries.
- **Teacher management styling and table slot height:** Removed unwanted grey background on teacher role dropdown buttons and compliance preset buttons, and removed artificial min-height on `.teachers-list-slot` to eliminate empty void space below the table.
- **JSON configuration disclosure smoothness:** Replaced native `<details class="details-accordion">` in Weekly Deadlines with Alpine `x-collapse` and smooth chevron rotation, eliminating animation jitter.
- **Contextual help tooltip icons:** Added `(?)` help tooltip icons (`icon('help-circle')`) across Users, Teachers, Groups, Compliance Checks, and Analytics cards.

## [2026.9.15] - 2026-09-10

### Fixed

- **Table layout shift (CLS) elimination on initial load and refresh.** Server-rendered
  the `.table-controls--tabs` class directly on `.table-controls` markup when filters
  contain tab strips, eliminating a ~10px vertical jump caused by deferred CSS `:has()`
  evaluation during streaming HTML parsing.
- **Explicit column widths in table heads.** Added explicit inline widths and synchronized
  stylesheet definitions across `<colgroup>` columns for User Management (`users_table_head`),
  Teams (`teams_table_head`), and Courses (`adminCoursesTable`). Aligned `col-gitlabid` to 165px,
  preventing browser column recalculation shifts as rows stream or timestamps localize.

## [2026.9.14] - 2026-09-10

### Fixed

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

## [2026.9.13] - 2026-09-10

### Fixed

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

## [2026.9.12] - 2026-09-09

### Fixed

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

## [2026.9.11] - 2026-09-09

### Fixed

- **Teachers management controls and zero-shift loading.** Unified the teacher invite
  typeahead and course role dropdown with standard GitLab Pajamas `table_controls`
  and `filter_tabs`, eliminating custom overrides and fake role color mixes.
- **Table loading shift and filter preservation in User Management.** Added pre-paginator
  row clamping to prevent full-table flashes before client pagination initializes.
  Fixed filter and search state synchronization to preserve `?q=` and `?role=` query
  parameters without multi-apply rendering jumps on initial page load.

## [2026.9.10] - 2026-09-09

### Fixed

- **Centred pagination controls and persistent empty states.** The pagination
  navigation (`<nav class="pagination">`) is now strictly centred using a 3-column
  grid layout (`1fr auto 1fr`), pinning row count info to the left and page size
  to the right without skewing the page switcher. Pagination controls remain
  visible and active with `Showing 0-0 of 0` when tables are empty or filtered to
  nothing, and duplicate count headers are eliminated.
- **Removed artificial scrollbar-gutter dead space.** Removed `scrollbar-gutter: stable`
  from `.table-responsive`, eliminating empty right-side gaps on short tables.
- **Stable table column widths across all views.** Restored full colgroup sizing
  in User Management, Events, and Course detail tables so columns no longer shift
  or recalculate dynamically during loads, filtering, or pagination.
- **Webhook configuration and teachers table proportions.** Rebalanced column widths
  in Webhook Configurations to eliminate narrow 6-line wrapping for long names.
- **CI/CD health donut proportions.** Reduced the latest pipeline doughnut chart
  diameter to 104px and aligned stats cards with balanced vertical spacing.

### Changed

- **Unified Compliance Checks filter tabs.** Converted outdated pill filter
  buttons into standard GitLab Pajamas `table_controls` and `filter_tabs`, removing
  legacy styling overrides.

## [2026.9.9] - 2026-09-09

### Fixed

- **The sideways slide, in every table at once.** Content shifted left as a
  table loaded and shifted back. `.table-responsive` is a scroll container with
  a height cap, so it gains a vertical scrollbar the moment its rows cross that
  cap - and under `scrollbar-gutter: auto` the bar comes out of the content box,
  which is the width the columns are solved against. Every column moved left by
  the bar's width, and moved back when anything dropped the row count under the
  cap again: the paginator cutting 68 rows to 50, a filter, a search. Measured
  at 1920px the bar is 10px, and the Users and system-config tables both cross
  the cap while loading.

  The gutter is reserved from the first frame now, so the bar's arrival and
  departure change nothing. It is one declaration on the one wrapper every table
  scrolls inside - there is no table this is true of and no table it is not.
  `.gl-page-content` already carried the same declaration, for the same reason,
  for the page as a whole.

### Changed

- **Every table is laid out the same way, because the layout is declared once.**
  Search and filters go in `table_controls` - the band between the card header
  and the rows - on every page. Four pages put them in the card header instead,
  which is where a table's ACTIONS go: the Groups card carried its title, its
  search box and its row count in one header row; the tickets card carried a
  search, three dropdowns, a Reset, a bulk-delete and a purge menu in that same
  row and wrapped to three lines; the student page's branch picker sat beside a
  hand-rolled count span.

  The band itself measured 45px on Users, 51px on the system config table, 57px
  on Job History and 73px on the Event Pipeline - one band, four heights,
  because a `.form-group` wrapper kept its 16px bottom margin inside a flex row,
  dropdowns were asked for at `-sm` (28px) on one page and default (32px) on the
  next, and tab buttons arrived at 26px or 30px. All of them measure 45px now,
  with every control in them at 32px.

  The search runs from the left edge to wherever the filters begin; it was
  capped at 28rem inside a slot that stretches, so a 699px slot held a 261px box
  and the gap between them belonged to nothing. With no search, the filters take
  the left edge instead of hiding in the far corner of an empty band.

- **A table that fills itself from JavaScript says so.** Five tables rendered a
  header over a void until a fetch returned - Job History, the Event Pipeline,
  the course checks and webhook tables, and the student's weekly breakdown,
  which went further and stayed hidden until its data landed, so the card grew
  by the table's full height (0 to 1092px) the moment it did. All of them open
  with the shared loading state now, and the weekly breakdown carries its own
  empty and failure states in the same box rather than borrowing the chart's
  message.

- **The row count is printed once.** The Groups table said "3 group(s)" beside
  its search while the card header said "Showing 1-3 of 3", and the student's
  commit history wrote its own wording over the one the paginator had just put
  there.

- **The per-page control keeps the right edge.** With one page of rows the page
  buttons are hidden, and the lone dropdown slid to the left of a 1200px bar -
  the bottom of the card empty to the right of it while the filter band above
  was empty to the left. The two bands mirror each other now.

- **Eight more per-page overrides removed.** `pages/admin.css` set
  `vertical-align: middle` on `.data-table tbody td` - an unscoped rule for
  every table in the app, written in one page's stylesheet, so a badge beside a
  two-line cell sat differently depending on which sheet happened to be loaded.
  Four tables set their own text size, two of them only on a phone. One restated
  the shared row hover in a different colour. The decisions live in `tables.css`
  now, once each.

## [2026.9.8] - 2026-09-08

### Fixed

- **Four kinds of activity the pilot telemetry never recorded.** `beacon()` is
  fire-and-forget by design - "telemetry must never break the page" - so a call
  the API refuses fails in complete silence, and these had been failing since
  they were written.

  *The student page's Export.* It sent `metric_type: "student_data_export"`,
  which is not a MetricType member, with `context: "student_detail"`, a bare
  string where the schema declares an object. Two faults in one line, answered
  422. It now sends `export_action` - the member that exists for exactly this -
  with `{ source: 'student_detail' }`.

  *The group and project pages.* Both had the right call and no course to
  attach it to: `tab_content()` emitted `data-course-id` only on its archived
  branch, as if the id were a property of being archived, and the telemetry
  client gives up silently when it finds none. `team_drill_down`,
  `project_drill_down` and the `dashboard_access` rows for both page kinds were
  assembled and dropped before they were ever sent. The id is emitted whenever
  the page has a course now; `data-course-archived`, which the read-only guard
  and the live-status poll key off, still rides only on the archived branch.

  Measured on a local instance before: `teacher_activity_metrics` held
  `dashboard_access` for course, student and settings pages and nothing else.
  After: all four kinds land, with their context.

  A test now walks every `trackActivity` call in the JS sources and checks the
  metric type and the context shape against the enum the API validates with.

- **A student's page asked twice for what it is never allowed.** Driving the app
  as a real student - not the shared `dev_user` row, which carries a teacher
  membership and so answers as staff - every group page sent
  `GET .../llm-analysis-status` (403, `TeacherAuth`) and, after the fix above,
  `POST /api/v1/telemetry/activity` (403, teacher-only by definition). Both
  rejections were swallowed on the client, so the only trace was a red line in
  the reader's console and a 403 in the log, once per page and again on every
  return to the tab. Both senders check the reader now: the telemetry guard sits
  with the four exported trackers rather than only in `autoTrack`, and
  `MAY_SEE_ANALYSIS` mirrors the endpoint's own rule - the role, not `canEdit`,
  because `canEdit` is also false for a teacher on an archived course who may
  still be watching an analysis that was already running.

- **Reactivating a course said nothing about its dead webhooks.** Archiving
  switches every webhook configuration off and reactivation deliberately leaves
  them off - the operator decides which scopes still apply - but nothing said
  so, so a reactivated course looked live while GitLab got 401 for every
  delivery. The archive already logged `course_webhooks_deactivated`; the other
  half was missing. Reactivation now counts what stayed disabled and logs
  `course_activated_webhooks_still_disabled` with the count and where to fix it.
  Behaviour is unchanged - only the record of it.

- **A row's buttons stayed out of reach in the widest table in the app.** The
  project Members table - a 16-column check matrix - scrolled its View buttons
  off the right edge; it and Support Tickets were the two Actions tables without
  `table-sticky-actions`. Both pin it now, and `table-sticky-first`, a class
  nothing has defined since June, is gone from seventeen call sites that looked
  as though their columns were managed.

- **An error toast dropped the one fact the reader needed.** "Refresh from
  GitLab" answered `400 {"message": "GitLab API token not configured"}` and the
  toast said only "Failed to start enrichment": the fallback carrying the reason
  sat on the right of a `||` whose left side was a translated string, so it was
  unreachable in every language.

## [2026.9.7.post5] - 2026-09-07

### Fixed

- **A webhook could be refused for a reason nothing recorded.** Three findings
  from driving a real GitLab repository through the app end to end.

  *The lookup digest was computed with an empty secret.*
  `compute_webhook_lookup_key` fell back to `os.environ.get("SECRET_KEY", "")`,
  and that is not where this app's configuration lives: pydantic-settings reads
  `.env` into the Settings object and exports nothing to the environment. An
  instance keeping SECRET_KEY in `.env` therefore keyed every digest with an
  EMPTY string, while a process that happened to have the variable exported (a
  container with an `environment:` block, a script calling `load_dotenv`) used
  the real one - so a configuration written by one was invisible to the other
  and every delivery came back 401. It also undid the point of keying it: with
  an empty key the digest is identical on every installation. Verified by
  replaying issue, push, merge-request and pipeline hooks: all four refused
  before, all four accepted after, with the issue landing in the database.

  *A malformed payload answered 500.* The webhook model is permissive about
  extra fields, not about the nested ids, so a slightly different delivery
  raised a bare `ValidationError` - the only path in that handler that did not
  describe its own rejection. GitLab treats 5xx as "try again" and would
  redeliver an unusable payload for 24 hours. It is a 422 naming the failing
  fields now - the field names, never their values, because a webhook body
  carries student names, emails and commit messages.

  *A rejection left no trace.* "Project has no webhook secret configured"
  returned 401 and logged nothing, while its sibling path logs
  `webhook_auth_failed`; the caller sees only a generic "Authentication
  required". It now logs the project, the course, whether the project had its
  own secret and whether the course had a legacy one - the four facts that tell
  the three real causes apart.

## [2026.9.7.post4] - 2026-09-07

### Fixed

- **A confirmation opened behind the modal that asked for it.** Found by
  clicking the course page through end to end: "Run selected checks", inside the
  Run Compliance Checks modal, raises a confirmation - and it opened UNDER that
  modal. The screenshot showed no dialog at all; in the DOM it was visible with
  opacity 1, and `elementFromPoint` at the Confirm button's centre returned
  `#runChecksGrid`. So the course-wide Run Checks, the grading action on that
  page, could not be completed by anyone: clicking the button appeared to do
  nothing.

  Every dialog is `.modal-backdrop` at 1000 and a page modal moves to the end of
  `<body>` when it opens, so at equal z-index the last one in the document won.
  The confirmation has its own layer now (1005: above the modals, below popovers
  and tooltips). Verified by running the whole flow afterwards - three group jobs
  completed and the course table moved from 80/64/39% to 94/75/46%.

## [2026.9.7.post3] - 2026-09-07

### Fixed

- **The admin Courses table stopped hiding its own cells.** Making its row
  actions fit on one line (post2) uncovered what was underneath: the table was
  `table-layout: fixed` over six percentage columns, and no set of percentages
  fits at every width. Measured at 1600x1000, the course name needed 283px in a
  265px column while the teacher cell needed 326px - moving points between them
  only moved which cell was cut. It sizes its columns to their content now and
  the wrapper scrolls, which is the contract the Users table already uses and
  the one this page itself used below 1180px. Measured after, at 1180 / 1440 /
  1600 / 1920: nothing clipped, and the four action buttons inside their group
  at every width.

## [2026.9.7.post2] - 2026-09-07

### Fixed

- **A row of the admin Courses table is one line again.** Its actions column
  holds up to four controls in 12% of the table, and one of them - "Teachers" -
  carried a label, so the group wrapped and that row stood about 40px taller
  than its neighbours: 85px against 45px, measured at 1440x900. All four are
  icons with tooltips now, the shape the Settings button beside them always had,
  and the rule that keeps them on one line applies at every width instead of
  only on tablets.

## [2026.9.7.post1] - 2026-09-07

### Changed

- **A course's actions moved next to its name.** Add Group, Import from GitLab,
  Sync All and Run Checks were a loose row between the tab strip and the Groups
  card, belonging to neither - too far from the table they act on to read as its
  toolbar, and not where a reader looks for what a page can do. The group page
  and the project page already put theirs in the page header; the course page
  was the odd one out among its own siblings. GitLab puts "New subgroup" and
  "New project" beside the group's name.

- **A group's page shows the group's own state.** The course table gives every
  group a score, a traffic light and a contributor count; the group's own page
  showed none of them and opened straight into "Subgroups and Projects". It
  opens with those five figures now. Nothing had to be computed for it: the
  live-data endpoint already returned them, the handler already counted the
  contributors (and handed the number to a template that ignored it), and the
  page script was already updating elements that no page rendered.

- **Numbers inside a card are numbers, not cards.** The Activity page's CI/CD
  block was five bordered tiles inside a sixth bordered card, and the student
  page's Communication Indicators was ten of them. Same component, same live
  hooks, without the chrome - which is how GitLab writes a stat row inside a
  card.

- **"Last synced" on a project is a line, not a panel.** It was a full-width
  bordered box holding one label and one date.

- **The phrase under your name on the dashboard is bigger.** It is a sentence
  somebody reads; at the metadata size (14px) it sat too quietly under a 30px
  name. The fallback line under it - role, then date - keeps the metadata size,
  because that is what it is.

### Fixed

- **A red group looked exactly like a green one on the group page.** The live
  handler toned the status card by swapping `stat-success` / `stat-warning` /
  `stat-danger` classes, which no stylesheet has defined since these became the
  shared `stat_card` component - the tone is `data-state`. The bug had been
  invisible because the card it updates was not on the page either.

- **The disabled-feature page no longer says you are on the dashboard.** It set
  no breadcrumb, so it inherited "Your work / Dashboard" - shown to anyone
  opening course Analytics with telemetry off, or Support with the forms off.
  Its two buttons were also two labels for one destination; "Go Back" goes back
  now.

- **The course page stopped counting contributors it never shows.** A
  `count(DISTINCT ...)` over the course's commits ran on every render - 11.0ms
  of the page's 44ms of database work - for a number no template has rendered
  since the KPI strip was removed in June. The helper stays for the callers that
  read theirs.

## [2026.9.7] - 2026-09-07

### Fixed

- **The unlit corner, everywhere it was.** A table draws its own top corners at
  12px, and the block above it - a card header, a toolbar, a tab strip - is
  square. Where both round, nothing shows; the moment the block above squares
  the table's wrapper, 12px of card ground shows through at the corner. That is
  the notch reported as "an unlit corner above CODE".

  The cause was one class in the wrong place: `data_table(class='...
  table-scrollable')` puts that class on the `<table>` element, and
  `.table-scrollable:first-child` - written for the scroll WRAPPER - matched the
  table too, because a table is always the first child of its wrapper. So the
  rules that decide whether a block should round were being applied to the
  wrapper while the table inside rounded regardless. Measured at 1440x900:
  **six of the nine tables walked** - the Users table, Job History, Feature
  Flags, Recent Events, the student page's issue tables and Group Members.

  A table now takes its corners from its wrapper (`border-radius: inherit`),
  written at a specificity that beats the rule it overrides - the detail that
  made two earlier attempts at this bug read correctly and do nothing.

- **A table under a tab strip keeps its corners square.** The same defect in a
  third disguise: the strip is not the table's sibling but the panel's, so none
  of the "is anything above me" rules could see it. The walk that checks this
  could not see tab panels either, which is why it passed while three of them
  were wrong; it looks at them now.

### Changed

- **The System page asks one question once.** Feature Flags, LLM Configuration
  and Runtime Information were three stacked cards - 1928px of them - each a
  read-only table of parameter, value and the environment variable behind it,
  none editable from this page. They are one Configuration card with three tabs
  now. "System Actions", a card header and a border around two buttons, is gone:
  Clear Cache and Refresh Stats sit in the page header, where a page's own
  actions belong and where an empty `.page-header-actions` div was already being
  rendered. Measured: **3775px and seven cards down to 2540px and four**.

- **A student's issues are two tabs, not two disclosures.** Authored and
  assigned are the same table of the same entity, split by which side of it the
  member is on. They were two `<details>`, one open and one closed depending on
  the counts, so the card's height changed with the data. Same shape as the
  Users and Event Pipeline pages now: 417px down to 255px.

- **"Issues to Address" is written once.** Its five states each carried their own
  copy of the card - five `{% call card %}` blocks repeating one title and one
  `id='projectBottlenecksCard'`, the handle the live-data refresh replaces. The
  branch picks what to say; the card is written once.

- **The Preferences page stopped rendering an empty actions box.** Its header was
  called as a block with nothing in it; its actions are in the sticky footer,
  where GitLab keeps them.

## [2026.9.4.post5] - 2026-09-04

### Changed

- **The first page after a deploy no longer waits for the process to finish
  starting.** Three costs were lazy and all three landed on whoever opened the
  first page: Jinja compiles each template on first use (2 651ms for all 106 in
  the production container, 108ms of it the course page's own partial),
  SQLAlchemy configures its mappers on the first ORM query (83ms), and asyncpg
  connects on first use (162ms). The process does all of it itself now, in a
  background task that yields between templates, so it never delays the
  container becoming healthy and never sits in front of a request for longer
  than one template takes. Measured in production, same process, same data,
  first render of a page: dashboard **1355ms -> 691ms**, course detail
  **88ms -> 33ms**, team detail **90ms -> 73ms**.

- **Lazy loading of page content: measured, and deliberately not added.** Every
  query behind the course page, timed in the production container against the
  largest course: 44ms of database work in total, and the page renders warm in
  13ms. A deferred second request costs more than that to make. Lazy loading is
  kept where the wait is real - the images (already `loading="lazy"`) and the
  per-page JS bundles - and the numbers are now written next to the code that
  decided it.

### Fixed

- **A wrong claim in this changelog, corrected.** The 2026.9.4.post1 entry said
  the contributor filter's shape took a query from 2560ms to milliseconds. It
  did not. That 2560ms reading was taken while a deploy rebuilt container images
  on the same four cores; measured on an idle host, the two forms are 15.2ms and
  16.2ms with 0.8ms of planning either way. The slow pages were the deploy, which
  post3 fixed. The subquery is kept for the smaller statement and the round-trip
  it saves, and the entry, the code comment and the test that repeated the claim
  now say so.

## [2026.9.4.post4] - 2026-09-04

### Fixed

- **A merge request lists the commits GitLab says are in it.** An MR whose
  GitLab page shows 7 commits showed **30** here, 23 of them "Teacher commit"
  entries from four to six years before the assignment existed - the template
  repository's history, inherited by the fork. Two things were wrong and both
  are in that number: the card listed every commit stored under
  `ref = <source branch>`, which is the branch's whole history; and 30 was not
  a count at all but `_branch_commit_cap`, the per-branch ceiling.

  It could not be derived from what was stored - `git_commits` keeps ONE ref per
  commit and the sync skips the default branch, so GitLab's rule ("on the source
  branch, not on the target") had nothing to work with. The sync already fetched
  the right answer per MR and used it only to backfill missing commits; it keeps
  it now, and the page asks for those commits by sha rather than filtering the
  capped branch bucket, which could otherwise drop them.

  Verified on real data: a merge request with ten commits on its branch and a
  stored list of two rendered a card reading 2, while one with no stored list
  rendered its branch listing exactly as before.

- **The users filter lines up with the table again.** It carried 12px to make up
  the difference between the card header and the card body; now that it sits
  inside the People panel - the same body as the table - that correction pushed
  it 12px past the table's edge instead.

### Changed

- **`mr_notes.author_id` gets the index its model always declared.** `NoteMixin`
  declares `index=True`, `issue_notes` has it and `mr_notes` did not. Drift
  repair, not a speed-up, and said plainly in the migration: the query that
  raised the question is scoped by two joins down to ~103 rows and measures
  1.24ms on production. The seconds seen on it earlier were a deploy rebuilding
  images on the same four cores.

## [2026.9.4.post3] - 2026-09-04

### Fixed

- **A deploy no longer takes the production host down with it.** `redeploy.py`
  built the API and worker images with `--no-cache` every time: a from-scratch
  reinstall of every dependency, on the production host, which has FOUR cores and
  is serving the application on them at the same moment.

  What that did to the app, measured while one such build was running - the
  request log carries the database split now, which is how this became visible:

      load average 5.03 on 4 cores
      a sequential scan over 7924 rows already in shared buffers: 1229ms
      UPDATE users ...: 36 417ms
      /dashboard/attention-items: 107 442ms, db=0ms, q=0

  The last line is the one that gives it away: 107 seconds without running a
  single query. Every "the pages take forever on production" report arrived while
  a deploy was rebuilding images underneath the reader - and there were twelve
  deploys that day.

  The build reuses its layer cache now. The Dockerfile earns that: dependencies
  are installed from `requirements.lock` BEFORE `src/` is copied, so a code-only
  deploy rebuilds one COPY layer in seconds while a dependency change still
  invalidates the install layer on its own. `python redeploy.py --no-cache` is
  there for when a from-scratch rebuild is actually what you want.

## [2026.9.4.post2] - 2026-09-04

### Fixed

- **The dashboard stopped writing to the database on every request, and stopped
  starving its own connection pool.** `_require_dashboard_session` fires a
  one-shot repair that fills `users.gitlab_user_id` for sessions minted before
  login started writing it - and it was firing on EVERY dashboard request. Each
  firing opened its own session, so a request already holding a pool connection
  took a second one, and the dashboard opens five fragments at once (stats,
  badges, attention items, activity, notifications): five writes raced for the
  same row lock, five times per page.

  Measured on production, from the request log during one burst:

      /dashboard/sidebar-badges  total=128991ms  db=76880ms
          worst 36417ms: UPDATE users SET gitlab_user_id=... WHERE gitlab_username=...
      /dashboard/stats           total=128965ms  db=87053ms
      /dashboard/attention-items total=107442ms  db=0ms  q=0
      /dashboard/activity        total=108795ms  db=0ms  q=0

  The last two are the tell: 107 seconds without running a single query, because
  no connection was free to run one.

  The repair now runs once per user per process, and the mark goes down before
  the task is scheduled, so a burst of parallel fragments schedules one write
  between them rather than one each. A restart retries it, which is the right
  amount of retrying for something that has nothing to do once it has run.

## [2026.9.4.post1] - 2026-09-04

### Fixed

- **The course page asks the database for its contributor whitelist instead of
  shipping one.** The whitelist of every course member was built in Python and
  sent back as two `IN` lists - ~900 bind parameters for a 459-member course,
  20 129 characters of SQL - plus the round-trip that fetched it. It is a
  subquery now: 1 954 characters, one query fewer, and the same counts group for
  group, verified against production data.

  **Correction (2026.9.4.post5).** This entry first claimed the change took that
  query from 2560ms to 15.6ms. That was wrong, and the way it was wrong is worth
  recording. The 2560ms reading was real but was taken while a deploy was
  rebuilding container images on the same four cores; measured later on an idle
  host, both forms are the same speed - 15.2ms as a subquery, 16.2ms as a bind
  list, planning 0.8ms either way. The slow pages were the deploy, not the query
  shape (see 2026.9.4.post3). The change is worth keeping for the 10x smaller
  statement and the round-trip it saves; it did not make the page fast.

- **A click in a table or on a card says so where it happened.** A control with
  no icon slot for the loading mark - a table row, a link inside a cell, a card
  - now holds an accent tint for as long as the fetch runs, the same wash the
  row highlight flashes. Background only, so nothing moves; the row's box is
  identical before and during.

- **A long project name is no longer cut in the page header.** `.page-header h1`
  carried `white-space: nowrap` with an ellipsis, so a group project named after
  its five members came out as "Butenko Voroniuk Hushchyn Didkivskyi Havryliu..."
  and the reader could not tell whose project they had opened. The heading wraps
  now - there is a whole line free to its right and nothing below it that a
  second line disturbs.

### Changed

- **People and service accounts are one card with two tabs.** They are the same
  table of the same entity, split only by what kind of account each row is, and
  they used to be two cards - the bots in a collapsed `<details>` below the whole
  human table, so reaching them meant scrolling past every person. One card now,
  two tabs with their counts, which is the shape the Event Pipeline page uses
  for the same reason. The search box and the role filter live inside the People
  panel: a filter of Admin / Teacher / Student says nothing about a bot.

  The other pages with several tables were checked and left alone, because
  merging them would be worse: Courses is already ONE table holding active and
  archived rows, System's six tables are six different things (jobs, feature
  flags, parameters), and on Support and the dashboard the tables next to each
  other are different entities read together.

## [2026.9.4] - 2026-09-04

### Added

- **A slow request names its worst query.** The split added in post12 answered
  the first question the moment it reached production: a course page measured
  6721ms total with **5902ms of it in the database across only 20 queries**, and
  the pattern held on the other heavy pages (a group page 1852ms of 2059ms, a
  student page 1223ms of 1819ms). Eighty-eight per cent database over twenty
  statements is not a hundred small round-trips and not template rendering - it
  is one or two very expensive queries.

  So a request over one second now also logs `db_slowest_ms` and
  `db_slowest_sql`: the single worst statement it ran, truncated to 240
  characters. The statement only - SQLAlchemy passes parameters separately and
  they can carry student names and emails, which have no business in a log line.
  Faster requests log neither, because a fast request is not a mystery.

## [2026.9.3.post12] - 2026-09-03

### Added

- **Every request line now says how much of it was the database.**
  `request_completed` reported that a course page took 13 seconds and nothing
  else, and that number cannot be acted on: a hundred quick queries in sequence
  and one slow template render look exactly the same from outside. Each line
  carries `db_ms` and `db_queries` beside `duration_ms` now, from a counter the
  request already owns (a `ContextVar` fed by SQLAlchemy's cursor events, one
  `perf_counter` pair per statement).

  It answers immediately on the pages that can be measured here: the dashboard
  is 113ms with 38 queries of which 50ms is the database, and the project page
  is 31ms with 6. It is meant for the ones that cannot - the slow course is 8
  groups, 96 projects and 459 members, which does not exist outside production,
  and the facts gathered so far rule the obvious causes out: the database
  answers `SELECT 1` in 1.3ms, its largest table holds 14 305 rows, the VM has
  5GB of memory free, and the page's own helpers are set-based with no N+1.
  The next slow render will say which half to look in.

  Not a tracer: OpenTelemetry is still there for following one request through
  its spans. This is the always-on summary that makes a line in a log file
  useful without turning tracing on for everyone.

## [2026.9.3.post11] - 2026-09-03

### Fixed

- **Clicking a name in Issues to Address lights the row up again.** It scrolled
  to the member and marked them - `GP.motion.highlight` ran on every click - but
  the mark was a box-shadow on the `<tr>`, and every cell in these tables paints
  its own opaque background (tables.css puts the zebra and the hover on the
  `<td>` so containment cannot swallow them). The shadow was drawn behind the
  cells. Measured on the project page: the tween ran, the row's computed
  box-shadow went 0.675 -> 0 over 600ms, and not one pixel of it was visible.
  A row is marked by tinting its CELLS now - the surface that is actually on top
  - so the whole row lights and fades, and `clearProps` hands the zebra and the
  hover back when it is done. A lone `<td>` keeps the inset ring.

- **A click in a table or a card reports itself, and stops costing a full page
  load.** Three handlers navigated by setting `window.location`: a members-table
  row and a team card (`data-navigate`), a back link (`data-nav-back`), and a
  jump from the search palette. None of them ran the progress bar, dimmed the
  page or turned the clicked control's icon - "I click buttons in tables and in
  cards and there is no loader" - and each re-downloaded and re-rendered the
  entire shell for what is a content swap. They go through the app's own
  navigation now (`GP.navigateTo`), which asks the same question the anchor path
  asks and hands back a `false` the caller falls back on, so a download, another
  origin, the locale switch and `/logout` still get the hard navigation they
  need. Measured on a members-table row: 1 full document load -> 0, and the
  click now carries the bar, the inert dimmed page and the busy cursor.

## [2026.9.3.post10] - 2026-09-03

### Changed

- **The loading pill is gone; the mark lands where a mark belongs, or nowhere.**
  The pill was visible, which was the point of it, but it was one more thing on
  the screen saying what the progress bar was already saying. What reports a
  navigation now is the bar, the clicked control's own icon turning into the
  app's spinner, and a `progress` cursor over the content region - the signal
  every browser and desktop app uses for exactly this, and the one that covers a
  click on something with no icon to stand in for.

  The placement rule is the real fix. It used to be "the first icon anywhere
  inside the control", which found a stat card's category icon in its top-right
  corner and put the spinner there, on top of it - "chaotically placed, not where
  it should be". The rule is now the control's FIRST child, and only if it sits
  in the control's leading quarter: a sidebar item, a tab, a menu row and a
  button qualify; a card, a table row and a bare link do not and are left alone.
  Measured: the sidebar item's mark sits at its icon (4/6 inside a 224x28 box,
  which does not change size), and the stat card that used to carry a corner
  spinner now carries none at all.

- **The dashboard greeting is two lines, not three.** The fetched phrase takes
  the place of "Good evening, <name>" instead of being added under it, which is
  GitLab's own shape: the name, and one line beneath. The time-of-day greeting
  with the role and the date is what shows when there is no phrase to show - the
  fallback it was always meant to be - so the page carries one piece of writing
  under the name either way.

## [2026.9.3.post9] - 2026-09-03

### Changed

- **There is one loader again, and it is one you can see.** The previous release
  retired the full-screen veil and left the whole signal to a 16px mark inside
  the clicked control plus a line in the breadcrumb bar - reported, correctly, as
  "the loader is almost invisible, chaotic": nothing on the screen actually said
  "loading", and what there was sat in three different places.

  The loader is now a pill at the top of the content region, carrying the app's
  own spinner and the word "Loading..." on the standard raised surface - card
  background, default border, standard shadow, default text colour - so it reads
  in all six themes and every accent instead of being the one brand-orange thing
  on a tinted screen. It appears at 250ms, so a navigation the reader
  experiences as instant still shows nothing but the progress bar, and at 4s it
  says the longer sentence IN THE SAME ELEMENT rather than growing a second one
  underneath (which is what moved the old veil's mark 13px).

  It is mounted on the panel rather than in the content, so it covers about 5%
  of the content region and moves none of it: measured across a 6s fetch, the
  pill holds its y position when its text changes, and the clicked sidebar item
  keeps its exact box - 8/175/224/28 - before, during and after.

  The two quieter signals stay as they were: the progress bar from the first
  millisecond, and the clicked control's own mark, which is the only part of
  this that can say WHICH of a dozen links is being answered.

- **The sign-in and sign-out pages sit where Keycloak's do.** Measured against
  the page this shell is modelled on (gitlab.example.com at 1920x1000): its
  title sits at y=104 and its card at y=188, while ours were at 62 and 137 - the
  whole block rode ~48px high, which is what makes a centred card look pinned to
  the top edge rather than placed. Ours now measure 110 and 185. Desktop only; a
  phone has no room to spend on it.
- **The dashboard greeting carries a line of its own.** GitLab writes a fixed
  tagline under your name there; this one is fetched, cached for an hour and the
  same for everyone, so it changes through the day. It never touches the request
  path: the page reads Redis and nothing else, and a miss renders the heading
  exactly as it did before - the time-of-day greeting and your name - while ONE
  background refresh is scheduled for the next reader. Every failure the third
  party can produce (down, slow, gone, answering a paragraph or markup) comes
  out as "no line", never as a slow page or a broken one.

## [2026.9.3.post8] - 2026-09-03

### Changed

- **The navigation loader is gone; the wait is shown where the click was.** A
  page-level loader has now been tried in three shapes and every one of them was
  reported from a screenshot: blanking the content for a centred mark, a toast
  beside the page, and a full-screen veil carrying a second copy of the brand
  mark in a 92px ring. The veil covered the page it was reporting on, it stayed
  brand-orange on an accented theme where the shell, sidebar and top bar are all
  tinted, its mark jumped 13px the moment the slow note appeared underneath it,
  and under `prefers-reduced-motion` it did not turn at all.

  What is there instead is the combination the app had before the veil, with the
  signal moved to where the reader is already looking: the top progress bar from
  the first millisecond, the CLICKED control turning in place - the app's own
  spinner stands in for that control's icon, so it costs the control no width
  and covers no label - and, after 4s, one line in the breadcrumb bar. Measured
  in Chromium: the clicked sidebar item's box is identical before the click,
  during the fetch, and when the 4s line appears.

  That line goes in the breadcrumb rather than in a toast because `showToast`
  persists every toast to sessionStorage, so a toast about a navigation can
  outlive the navigation it describes.

### Fixed

- **Every loading mark in the app keeps turning under reduced motion.** The
  blanket `* { animation-duration: 0.01ms !important; animation-iteration-count:
  1 !important }` in animations.css beat the spinner's own rule, so a reader who
  asks for less motion got a mark that rendered one frame and then stood still -
  measured `spin 1e-05s 1`. A frozen spinner says the app has hung, which is the
  opposite of what it is there for. It turns at 2.4s now, the same exception
  `.global-job-spinner` already carries.
- **The page you are leaving stays readable.** It was dimmed to 0.6 AND covered
  by a veil at 82% of the shell colour; it is stepped back to 0.75 now and
  nothing is drawn over it.

## [2026.9.3.post7] - 2026-09-03

### Changed

- **Pages are a fraction of the size they were.** The Slovak translation
  catalogue was serialised into every page: 205KB, about ninety per cent of
  what a compressed page weighed, re-sent on every load because inline content
  has no URL to cache. It is now a content-hashed file the browser keeps until
  the translations change. The dashboard went from 367KB to 162KB, and the
  login page from 234KB to 21KB.
- **The dashboard asks the database less.** Fifty queries per render became
  thirty-eight: the job counts, the course settings, the support-ticket panels
  and the red-team list were each asked several times for the same answer, and
  the activity feed re-read courses the page already had.

### Fixed

- **Loading the dashboard no longer writes to the database.** The stale-job
  self-heal issued its UPDATE on every render, taking row locks for a set that
  is almost always empty. It looks first now, and writes only when there is
  something to heal.

## [2026.9.3.post6] - 2026-09-03

### Changed

- **The loading screen wears the theme instead of the brand.** It carried a
  second copy of the tanuki - a 48-line inline SVG in its own 92px ring, its
  heartbeat trace looping, in colours written into the CSS - so with an accent
  chosen in Preferences (the shell, sidebar and top bar all tinted indigo) the
  loader was the only orange thing on the screen, and the biggest. It shows the
  app's own `.gp-spinner` now, at the size that component already defines, and
  the ring follows `--_accent` - the same colour the chrome is tinted with. The
  `default` accent keeps the brand pair exactly as it was.
- **The page behind the loader stays readable.** It was dimmed twice: the veil
  over it AND `opacity: 0.6` on the content itself, which together took a slow
  navigation to the edge of unreadable - a busy page that looked like a broken
  one. One dim now, and a lighter one (82% -> 62%).
- **The syntax-highlighting previews show code rather than space.** The line
  numbers sat in a 32px track with 12px of margin and 8px of padding, so the
  code began 46px into a 151px swatch and the sample - deliberately short so no
  line would be cut - left the rest empty. The gutter is 16px with a 6px gap and
  the sample fills the card, clipped at the right edge, which is what GitLab's
  own previews do.

## [2026.9.3.post5] - 2026-09-03

### Fixed

- **The loading screen covers the page you are looking at.** The veil was
  mounted inside the scroll container, where an absolutely positioned element
  is laid out against the scroll origin rather than the visible area - so on a
  page that had been scrolled it sat at the top of the content and scrolled
  away with it. Measured at `scrollTop` 597: the veil at `y=-513`, the mark
  81px above the window, and 597px of the page left undimmed under a dark band.
  It is mounted on the panel now, which does not scroll, and starts below the
  breadcrumb so the crumbs and the job bar stay readable.
- **A table under a header no longer draws its own top corners.** The rule was
  there but lost the cascade to `.table-scroll > *:first-child`, so every table
  a `data_table` renders kept a 12px corner under a square header. In the
  Archived Courses card both radii were drawn at once - the card body clips at
  8px, the table rounded at 12px - and the 4px of arc between them showed the
  dark ground through the corner of the header row, which is the unlit corner
  that appears above CODE the moment the column is hovered.
- **Column labels no longer wrap in a table that can scroll instead.** "GitLab
  User ID" over an 80px column made the users table's header row 92px tall
  while the table was already 75px wider than its viewport; the column takes
  the label's width now (133px) and the header is one 52px line. The Archived
  Courses rows are one line each for the same reason. Fixed-layout tables keep
  the wrap - their columns cannot grow, so there the label really would be cut.
- **One long value no longer takes its whole column with it.** Auto layout
  sizes a column to its widest cell, so a single 70-character name pushed every
  column after it off the right edge. Past 42 characters - clear of every
  ordinary name and email - it is cut with an ellipsis, with the full value in
  the tooltip the cell already carried.

### Changed

- **The dashboard asks for its job counts once instead of five times.**

## [2026.9.3.post4] - 2026-09-03

### Fixed

- **A deploy no longer shows the browser's error page.** While the api
  container was being replaced the proxy answered with an empty body, so the
  browser drew its own "This page isn't working". Requests now wait out the
  swap and retry for up to 15s, and only an outage that outlasts that reaches
  our own page - which is served with the original status code, carries the
  5xx illustration, and reloads itself once the app answers again.
- **Compliance-rule descriptions wrap instead of being cut to one line.** The
  clipped half was the part that tells two checks apart, and the text was also
  being truncated to 80 characters in JavaScript - the same double truncation
  already fixed in the Jobs table.
- **The sidebar's quick-access rows show what they display.** The groups list
  truncated a course code with no tooltip behind it, and the projects list had
  a tooltip that named only the path, omitting the score beside it.

### Changed

- **The space above the page footer is the same on every page.** It was 32px
  after a card and 24px after a form, because the footer's margin collapsed
  with whatever the page happened to end with.

## [2026.9.3.post3] - 2026-09-03

### Changed

- **User Management drops the percentage column budget it no longer follows.**
  The table sizes itself to its content now, and `width` is still a hint under
  that layout, so the leftover percentages were a second and contradictory
  opinion about how wide each column should be.

## [2026.9.3.post2] - 2026-09-03

### Fixed

- **The Jobs table no longer cuts a result you cannot scroll to.** The Result
  column was capped at 200px and ellipsised on top of the 80-character limit
  the page already applies, so an ordinary course name needing 275px was shown
  at 196 with no way to reach the rest. The character limit is what stops a
  runaway error message blowing the layout; the second cap only truncated text
  that fitted.

## [2026.9.3.post1] - 2026-09-03

### Fixed

- **A read-only course's buttons no longer flash as available while the page
  loads.** The server already marks the content well `is-course-archived` so
  they can be dimmed on the first frame - but no CSS rule ever matched that
  class, so the only thing that dimmed them was the guard setting `disabled`
  after paint. Every write action on an archived course lit up in its normal
  colour and greyed a beat later.
- **The syntax scheme previews are no longer cut off.** The sample measured
  226px of code inside a 157px card, so every one of the seven was clipped
  mid-token ("return mr.we"). The sample is short enough to fit now, and still
  shows the whole palette.
- **The colour field on Preferences is one control again.** Its chip rendered
  27px tall against a 32px field, so it read as a square floating beside the
  input rather than part of it.
- **The Diffs section spaces like every other section.** The suggested-colour
  row sat outside the field's group and its margins stacked on top of the
  group's, so the gap between the two colour fields measured 68px where every
  other section on the page uses 16.
- **Tables scroll instead of hiding their content behind three dots.** User
  Management sized its columns by percentage and clipped the overflow: measured
  on a 1573px window, 30 cells cut, an e-mail needing 277px inside a 245px
  column - and the wrapper could not scroll, so the hidden half of every long
  address and date was unreachable.
- **The User Info dialog no longer collapses when its data lands.** Its
  placeholder reserved two cards per section and measured 384px against a 277px
  card, so the dialog dropped 107px on every open. It settles by 4px now.

### Changed

- **The dashboard's two columns are GitLab's own grid.** Taken from
  `layouts/detail_layout.scss`: `minmax(67%, 1fr) minmax(13rem, 18.125rem)` with
  a 2rem gap. The difference that showed was the right column - ours grew with
  the window, measured at ~395px on a 1210px layout, where GitLab caps its
  sidebar at 290px and gives every extra pixel to the content.

### Fixed

- **The loading mark is centred on the screen, with no dead space under it.**
  The veil carried 24px of padding while the box that centres the mark was
  given the full height of the visible area, so it overflowed and sat low. And
  the "still loading" note reserved two lines while invisible, pushing the mark
  and its label further up - an element nobody can see moving the ones they can.
- **The archived card's corner no longer disagrees between themes.** It set a
  border colour of its own, and in dark mode that value is identical to the
  card's background, so the rule could never be seen as a rule. A card is told
  apart from the page by its background, which is what every other card does.

## [2026.9.3] - 2026-09-03

### Fixed

- **The loading screen no longer leaves two undimmed bands down the sides.**
  The veil was pinned to the centred, width-capped content column rather than
  the region you actually see - on a 1920px window that is 1296px inside a
  1672px area, so roughly 190px stayed undimmed on each side and the whole
  thing read as a floating panel over the middle of the page instead of a veil
  over it. It now covers the full content region, and the mark is centred on
  the visible area rather than a little below it.
- **An archived course is no longer told to run a sync it cannot run.**
  Archiving makes a course read-only - Sync All is blocked - and its data going
  out of date is the expected consequence of that. The page said so anyway,
  stacking "Data may be outdated ... Try running Sync All to refresh the data"
  directly under the strip that had just explained the course is read-only.
  The freshness banners are gone on an archived course, on Overview, Activity
  and Analytics alike; the archived strip already says everything they did.

## [2026.9.2.post2] - 2026-09-02

### Fixed

- **The loading screen is an overlay again, not a panel at the bottom of the
  page.** A blanket `[aria-live] { position: relative }` rule sat in the
  utilities sheet. As a bare attribute selector it has the same weight as a
  class and came later in the bundle, so it quietly beat the loader's own
  `position: absolute` - and because the loader IS a live region, the veil that
  should cover the outgoing page was dropped into normal flow as a 203px block
  below the footer. Position has no accessibility function on a live region;
  the rule is gone. It had been silently positioning every "done" button too.
- **The loading mark is centred on what you are looking at.** The veil spans
  the whole outgoing page, which on a long one is thousands of pixels, so
  centring the mark inside it put it far below the viewport. It sits in a
  sticky box now.
- **Settings controls no longer stretch the whole column.** Every select on the
  preferences page rendered at the full width of the settings column - measured
  at 1264px - with the value pinned left and the chevron a thousand pixels
  away. Two of them stacked in Localization is what read as a large empty band
  under the heading. GitLab caps exactly these selects; so does this page now.

## [2026.9.2.post1] - 2026-09-02

### Fixed

- **A role is the same colour wherever it is drawn.** The colour for a role was
  written down in four places, each with a comment saying it had to stay in
  step with the others, and two had drifted anyway. A course owner was drawn
  orange in the User Info dialog and teal on the page behind it - the dialog had
  taken its colours from GitLab's *access level* map, where "owner" is a
  different thing that only shares the word. And a mentor was grey in the users
  table but teal in the dialog opened from that very row. A test pins all four
  together now.

## [2026.9.2] - 2026-09-02

### Fixed

- **The User Info dialog is the same dialog everywhere it opens.** Its renderer
  was loaded by Admin → Users and by no other page, while the dialog itself
  opens from member tables, discussion notes, project pages and the sidebar.
  Everywhere else it fell back to a plain spinner instead of the structural
  skeleton, and to a cut-down card with no avatar and two headings that never
  translated. The renderer is now fetched on first open, from anywhere, and
  both fallbacks are gone.
- **Table text no longer breaks mid-word.** Cells wrapped with a rule that
  breaks inside a word whenever the line is full, so names split as
  "Mykyta Ol / ym" and e-mails broke at an arbitrary letter. The column headers
  right above them had already been corrected for exactly this; the cells were
  left behind.
- **Two tables on the System page scroll like every other table.** The
  Parameter / Value / Env tables had the scroll wrapper but no minimum width to
  scroll, so the Value column absorbed the squeeze and wrapped long values over
  several lines instead.
- **The default avatars no longer blink every time you come back to the tab.**
  Returning to the window re-fetched the picture of every user who simply has
  no picture - twice each - and blanked their initials while it tried. Only a
  genuine reconnection retries now.
- **The System page's tables load the way the rest of the app does.** They
  carried a second, admin-only dimming layer on top of the shared one.
- **Picking the Light or Dark syntax scheme now sticks.** Both were offered on
  the preferences page and both saved, but the per-request hydration
  re-validated the stored value against a second, hand-written list that had
  never been given them - so on the very next page load the scheme silently
  reverted. Outside its own preview the setting had never worked at all.
- **Pinning a homepage other than Dashboard now works.** The same duplicated
  list re-validated `default_homepage` against "courses" and "activity" - two
  names the page does not offer - and threw away every real option except
  "dashboard". Support, Courses, System and Users all silently did nothing.
  Both lists are now read from the one field table the save endpoint validates
  against, so they cannot drift apart again.
- **The syntax scheme list is GitLab's.** Light, Dark, Solarized Light,
  Solarized Dark, Monokai, Dracula, None - in that order
  (`lib/gitlab/color_schemes.rb`). Dracula was missing; "Default" was a
  seventh palette no upstream scheme corresponds to and close enough to Dark
  that the two previews read as one swatch. A stored "Default" degrades to
  Dark, the palette it copied.
- **The diff colour field is one control again.** The colour chip is the hex
  field's prepend, sharing its edge, as in GitLab's own colour picker. It had
  been standing loose in the row of suggested colours, where it rendered the
  platform's native colour-well - it read as an eighth suggestion, and clicking
  it dropped the OS picker panel over the page instead of opening it on the
  field it edits.
- **A retired preference value no longer leaves a group with nothing selected.**
  The page echoed a stored value back even when it was no longer offered, so
  the reader could not tell what was in force.
- **A page that loses its live connection now reconnects once, not on top of
  itself.** Five pages - the dashboard, the sidebar badges, a course, a group
  and a project - each kept their own copy of the same twenty lines of
  reconnect logic, and the copies had drifted. Each held its retry timer
  outside the connection it belonged to, so "is this stream still trying?"
  needed a three-way test, and a page that checked only two of the three
  opened a second stream while the first was still waiting to retry.
- **A finished sync no longer produces a burst of one-frame reconnects.** The
  server closes a completed sync's stream promptly; against a fixed two-second
  retry that turned into a tight loop of connections that lived a few
  milliseconds each. That stream now backs off (4s, 8s, ... to 20s).

### Changed

- The page-level live-update client is defined once (`GP.sse`) instead of
  five times. A stream that ends with the job it reports - the per-job
  progress stream - is deliberately left as it was, and is covered by a test
  that says so.

### Internal

- `ruff check` passes again: a test name capitalised for emphasis tripped
  pep8-naming's N802 and had been failing the lint gate on `main`.
- The page live-update tests assert the shared client rather than a literal
  `EventSource`, which three of the four had stopped meaningfully testing.

## [2026.9.1.post1] - 2026-09-01

### Fixed

- **The theme now recolours the whole application chrome**, not just the
  sidebar - which is what its own preview card has always promised. The rule
  was scoped to the sidebar, so picking a theme left the entire top of the
  window unchanged.
- **Syntax highlighting has a light scheme.** Every option painted a dark
  block, so on a light page there was no way to get light code at all. Light
  and Dark are separate choices now, as in GitLab, and the seven previews sit
  in one row with seven visibly different grounds.
- **Alt-tabbing back no longer loses an attention item.** The live refresh
  built a genuinely shorter list than the page it refreshed - it loaded fewer
  columns than the builder reads, and omitted the count that gates the
  "groups at critical risk" item. The dashboard was silently dropping an item
  and 91px of height on every return to the tab.
- **A disclosure slides open instead of flashing.** Every `<details>` in the
  app painted one frame at full height before collapsing to start the slide.
- **An archived course is read-only, not unreadable.** Collapsible card
  headers, the admin-list disclosure and the Copy Token button were all
  locked; none of them can change anything.
- **A table that scrolls down says so.** Vertical overflow had no affordance
  at all - 369 hidden pixels on admin users, 778 on admin events.
- **The Activity page's Sync button is gone**, at the user's request; the
  course overview owns that action and the feed is live over SSE anyway.

### Changed

- **Chart.js loads only on the five pages that draw charts**, taking 73kB off
  the first visit to the other thirteen.

## [2026.9.1] - 2026-09-01

### Fixed

- **No page changes shape after it paints.** Post-paint growth is 0px across
  all eighteen pages and layout shift is 0.000 on sixteen of them, measured in
  Chromium. The System page grew 546px, the Teachers panel 37px per member row.
  Three causes: the shared skeleton hand-off faded the skeleton while it still
  took up its full height, so every card in the app was briefly
  skeleton-plus-content tall; two blocks whose rows arrive from an inlined
  island reserved nothing while the deferred page bundle loaded; and the
  Teachers rows are drawn by Alpine from data the server already had.
- **Navigation no longer takes your page away.** After 1200ms it replaced the
  content with a centred spinner and scrolled to the top, so any navigation
  slower than 1.2s cost you the page, a spinner and two jumps. GitLab never
  blanks the page it is leaving; nor does this now. A genuinely long fetch says
  so in a toast at 4s.
- **Table headers stop spilling under the next column.** "GitLab User I",
  "Projec" and a sliced State badge were all one cause: a fixed-layout header
  wider than its column overflows, and the neighbour's own background paints
  over it. Zero clipped cells at 1024 / 1280 / 1440 / 1920 now, from fourteen.
- **Requests cannot overtake each other.** A filter changed twice, a poll
  overlapping its own tick, or a page left mid-fetch could all let an older
  answer paint over a newer one. One in-flight request per key now, and an
  internal navigation abandons what the page it left had in flight.
- **Every disabled control says why it is disabled**, and every icon-only
  button has a tooltip - audited across all eighteen pages.
- **Hover answers in colour, the way GitLab's does.** Eighteen hover states
  moved something; none does now.
- **Keyboard focus is always visible.** The support page's markdown textarea
  removed its outline and put nothing back.
- **Tabs no longer hop**, and the syntax-highlighting preview shows each
  scheme's own background rather than five variations of one.

## [2026.8.31.post2] - 2026-08-31

### Fixed

- **A settings form's save bar is one component now, and it is GitLab's.** Two
  forms carry a dirty guard and each had written its own footer: course
  settings' was sticky under a course-specific name, the Preferences row was
  static and scrolled away with the page - so the Save button the guard arms
  was off-screen at exactly the moment it armed, which is what made the guard
  read as decorative. Both are now `.settings-sticky-footer`, the rule GitLab
  uses in `app/assets/stylesheets/pages/settings.scss`.
- **A disabled button never showed that it was disabled.** The shared rule
  carried `pointer-events: none`, which GitLab's does not: an element that is
  not a hit target takes no cursor from its own rules, so `cursor: not-allowed`
  never appeared. A disabled `<a>` keeps it - an anchor has no native
  `disabled` attribute, so nothing else stops the navigation.
- **Internal navigation discarded unsaved settings without asking.** A content
  swap never fires `beforeunload`, and the navigation dropped every dirty
  reason on the way out, so clicking a sidebar link with a half-filled settings
  form threw the edits away silently. It now asks through the app's one
  confirmation component; a cancelled Back puts the address bar back.
- **The sticky actions column painted a dark seam when the table already fit.**
- **The auth alert was a heavy chip rather than GitLab's flat GlAlert.**

## [2026.8.31.post1] - 2026-08-31

### Fixed

- **The Save button on Preferences never armed for a radio choice.** The dirty
  snapshot keyed every control by name and stored `checked` for radios - but a
  radio group shares one name, so it recorded whichever button came last,
  normally unchecked, and still unchecked after you picked something else.
  Nothing appeared to change, so Save stayed disabled: the accent theme, the
  layout width, the syntax scheme and the time format were all unsaveable.
- **One notification opt-out was inside a docstring.** Emails are persisted
  through one of two functions; on the second the guard was a string rather
  than a statement, so that path sent every category regardless of what had
  been muted.

## [2026.8.31] - 2026-08-31

### Added

- **Syntax highlighting** on Preferences - GitLab's section, and a real setting
  rather than a copied label. Fenced code blocks with a recognised language are
  highlighted by Pygments, and their ten token colours are now CSS variables, so
  a scheme is ten declarations instead of a second copy of the token table.
  Default, Monokai, Solarized dark, Solarized light and None. Each scheme is
  declared ONCE and consumed twice - by the page root and by its own swatch - so
  the swatch is a live sample rendered through the exact rules the page will
  use, not a checked-in screenshot that can drift from them.

## [2026.8.26.post5] - 2026-08-26

### Fixed

- **Picking a theme did almost nothing.** The accent tinted two variables - the
  selected sidebar item's background and its hover - so unless you happened to
  be looking at that one 28px row, the setting read as inert. It tints the
  panel surface now: background, border and hover, the way GitLab's own
  `gl-*-scope` classes retint the neutral ramp inside a theme scope. The
  preview uses the same recipe, so the swatch promises what the app delivers.
- **The gap between a heading and its control was 44px too wide.** Measured
  against GitLab's `SettingsSectionComponent`: `h2.gl-heading-2.gl-mb-0`, the
  description at `gl-mb-6` (24px), the body at `gl-mt-3` (8px), and nothing
  else. Ours added 24px above the header, 16px below it and a 4px gap between
  the heading and its description on top of that.
- **The select's own button still looked like a button, not a field** - the
  other half of the select fix: `dropdowns.css` loads after `forms.css`, so at
  equal specificity it won six properties, giving the control a button
  background, a 1px border and the action radius beside text inputs wearing
  none of those.

### Changed

- The Diffs preview is two panes, removed on the left and added on the right,
  over a real code sample - the arrangement GitLab uses. The rows are the same
  `.dn-code-*` markup the student profile renders a diff with, so the preview
  cannot drift from the thing it previews.

## [2026.8.26.post4] - 2026-08-26

### Changed

- A settings section now reads the way GitLab's does: the heading, then its
  description underneath. `.section-title-group` was a flex ROW, so every
  description sat on the same line as its heading - a whole sentence beside a
  21px title, with neither reading as the other's caption. The disclosure
  chevron keeps its place beside the title. This applies to every section in the
  app, not only Preferences.

## [2026.8.26.post3] - 2026-08-26

### Fixed

- **Every select in the app rendered shrink-to-content.** `dropdowns.css` loads
  after `forms.css`, so at equal specificity `.gl-dropdown { display: inline-flex }`
  beat `.gl-form-dropdown { display: block; width: 100% }` - the select collapsed
  to its text and drifted to the end of its form cell while the input beside it
  filled the row. Most visible on course settings.
- **The Mode switcher never showed which mode was active.** Its buttons are
  server-rendered `aria-pressed="false"` and corrected by script on
  `DOMContentLoaded` - which never fires again after an SPA navigation, and
  Preferences is always reached by one. It re-syncs after each swap now.
- **Every accent preview looked identical in dark mode.** The dark-mode chrome
  rule out-specified the accent tint (0,2,1 against 0,2,0), so all six previews
  painted the same grey and the setting looked inert.
- **"Accent color" turned blue when you picked an accent.** A
  `:focus-within` rule recoloured the caption of any field group containing a
  focused control. Focus belongs to the control's ring, not to its label.
- **The line under the breadcrumb vanished on scroll.** That 2px strip is
  sticky at `z-index: 2`, and sticky section headings and sticky table headers
  sat at 2 as well - later in the DOM, so they painted over it.

### Changed

- The Mode options read Light / Dark / **Auto**, GitLab's own wording, and the
  section is heading, description, control with no extra hint line.

## [2026.8.26.post2] - 2026-08-26

### Fixed

- The dashboard returned 500. Trimming unused template imports in 2026.8.26
  removed `json_drop` from the dashboard modals - where nothing mentions it -
  but the shared config-import macro resolved that name from whichever file
  imported it, so the error was raised inside a file the change never touched.
  That macro imports its own dependencies now, so it cannot be broken from
  outside. The Teachers page had the same fault and is fixed with it.

## [2026.8.26.post1] - 2026-08-26

### Fixed

- The threshold pills on a student's compliance history were unreadable. Two
  different components share those colour classes - the segmented bar on course
  settings and this text pill - and neither was scoped, so the bar's saturated
  fill won for both. The pill sets no text colour of its own, so it rendered
  dark grey on solid green at 2.46:1 against the 4.5:1 minimum; the rule that
  lost gives 8.19:1. Both components own their colours now.
- The bar's yellow segment was the odd one out and the failing one: dark text on
  the warning fill measures 3.13:1, where the white the green and red segments
  already use measures 4.73:1.

### Removed

- Eight stylesheet rules a later file overrode completely, found with a real CSS
  parser. One of them mattered: the metric-score scale in `utilities.css` gave
  `good` and `excellent` the same green, where the rule that actually applies
  distinguishes them.

## [2026.8.26] - 2026-08-26

### Changed

- Every table that had to fetch its first page now paints on load instead:
  recent events, the DLQ tab, Job History, the compliance checks table and the
  webhook configs table. The first page is rendered into the document, so there
  is no request and no loading state between opening a page and reading it.
- One implementation per interaction, across the interface. Three of these were
  visible defects rather than untidiness:
  - The avatar existed five different ways. The failure handler reveals the
    image's next element sibling, and three of the five put the image alone
    inside a conditional - so a 404 avatar, an expired GitLab URL or a dropped
    connection left an empty disc on the ticket submitter, the current assignee
    and the assignee picker.
  - Opening a support ticket by direct link rendered a different page from
    reaching it by navigation: that template was a 311-line copy of the partial
    and had fallen behind it, missing every tour anchor and titling raw response
    keys instead of reading the form's own question labels.
  - `canEdit` was derived two different ways in one page - from the
    server-computed permission in one place and from the account role in
    another - so a script's answer depended on which block it happened to read.
- The restore / permanently-delete pair, the dropdown, the avatar, the button
  attribute set, the course tab well and the retry control are each defined
  once now. Along the way: a restore button that rendered full-width beside an
  icon-only delete, two role pickers that blinked open while an identical third
  animated, and read-only dimming that arrived instantly on one tab and a beat
  late on the next.
- `disabled_reason` - the tooltip that says why a control is unavailable - works
  on every button type now, not only one of the three.

### Fixed

- Spacing utilities contradicted themselves: `.mt-1` was declared twice with
  different values, so every use silently took the second one, and `ml-1`,
  `mb-lg` and `mb-md` were written on 19 elements without any rule existing at
  all. One name per value now, with no change in rendered pixels.
- The Preferences page added a navigation listener on every visit and removed
  none, so after N visits every page swap in the app ran its initialiser N
  times. It joins the teardown contract the other seventeen page bundles
  already followed.

### Removed

- Dead code, all of it verified as unreachable rather than assumed: 116 CSS
  rules generated for a macro with no callers, eight Jinja macros, three whole
  component files whose real implementations live elsewhere, eleven JavaScript
  helpers, five per-variant toast aliases duplicating `showToast(message,
  variant)`, and 177 template imports nothing in the file used.

## [2026.8.24.post6] - 2026-08-24

### Fixed

- Staff ticket-queue mail shared one switch with a reader's own tickets, so an
  admin who muted ticket updates also stopped being told that a new ticket had
  arrived with nobody on it - silencing an operational duty along with a
  personal preference. It is now its own category, shown only to staff, since
  a student never receives that mail and a switch that does nothing is worse
  than no switch.

## [2026.8.24.post5] - 2026-08-24

### Fixed

- The Preferences tour and its documentation had fallen behind the page. Both
  were written before the Diffs and Notifications sections existed, so the page
  carried two anchors nothing walked to and the docs described a page that no
  longer matched. Both now cover every section, in Slovak and English, and a
  test holds the tour's steps against the page's anchors in both directions -
  a step pointing at a missing anchor is silently dropped, so the tour would
  otherwise just get shorter instead of failing.
- The toast width test pinned GitLab's 586px maximum, which contradicted the
  deliberate change to one fixed width for the whole stack. Recorded as a
  divergence with its reason rather than reverted.

## [2026.8.24.post4] - 2026-08-24

### Added

- Two preferences that are GitPulse's own rather than copied from GitLab, both
  chosen because the app **already** offers the choice and then forgets it:
  - **Rows per page** - the per-table "Per page" control writes
    `localStorage`, so a new device silently fell back to 50 however the reader
    had it set. This is now the account-level default; a choice made on a
    specific table still wins for that table, being both more specific and more
    recent.
  - **Start with the sidebar collapsed** - same story with `sidebar-collapsed`.
    Applied only on a device that has no stored state yet, so collapsing it
    locally still wins afterwards.

## [2026.8.24.post3] - 2026-08-24

### Fixed

- **Preferences section headings were the wrong size.** GitLab renders each as
  `h2.gl-heading-2` - a RESPONSIVE clamp from 21px to 25px with a 1.25 line
  height and -0.01em tracking. Ours were the base 14px, which is why the page
  did not read as GitLab's beside it. The three type tokens are now taken
  verbatim from `@gitlab/ui` 136.3.0.
- **Section headings are sticky**, as GitLab's `.settings-sticky-header` is:
  the heading stays put while its own section scrolls past, over an opaque
  background so body text cannot show through it.
- **The theme previews used approximated colours.** GitLab's own
  `page_bundles/profiles/preferences.scss` sets them explicitly: neutral-50
  over neutral-0 with alpha-DARK ink in light, neutral-900 over a hardcoded
  `#18171e` with alpha-LIGHT ink in dark. GitLab hardcodes that one value on
  purpose, so a tinted theme scope cannot drag the panel colour with it. The
  card also takes `font-size: 0`, an 8px radius and `overflow: hidden`, as
  `.application-theme .preview` does.

## [2026.8.24.post2] - 2026-08-24

### Added

- Preferences > **Notifications**: per-category opt-outs for support-ticket,
  course and account email. Enforced in `enqueue_email` on BOTH persistence
  paths, so turning one off stops the mail on the server rather than only
  hiding a checkbox. It fails open - an unreachable database still sends,
  because a missed ticket notification is worse than an unwanted one. The
  welcome mail has no toggle: it is sent before a new account has ever seen
  this page.

### Fixed

- **Layout width did nothing visible.** Five elements cap themselves at
  `--content-width-lg` - the main container, the job bar, the cookie banner and
  both global banners - and only the main container was uncapped, so the chrome
  above it stayed narrow while the content spread. The token itself is now
  flipped, which moves all five together.
- The Save button on Preferences is the same guarded control the course
  settings page uses: disabled until the form is actually dirty, registering an
  unsaved-changes reason so navigating away warns, and re-baselining after a
  successful save.
- Sections on the Preferences page are separated by a rule, as GitLab's are.

### Changed

- The colour mode switcher is no longer duplicated in the user menu; it lives
  on the Preferences page, which is the one place that also carries its label,
  help text and the rest of the appearance settings.

## [2026.8.24.post1] - 2026-08-24

### Fixed

- Every email linked "Manage notifications" and its `List-Unsubscribe` header
  at `/dashboard/settings`, a route that has never existed - so both sent the
  reader to a 404. They now point at `/dashboard/preferences`, the page that
  actually holds those controls.
- The welcome email built its own bullet list in Google-hosted Inter over the
  Tailwind slate palette, and its support link in Tailwind blue. It composed
  that HTML itself and passed it in as a body line, so it bypassed the mailer
  chrome entirely and no parity check saw it. The email parity test now scans
  the whole module, not just one rendered sample, and separately asserts that
  every `/dashboard/...` link in it resolves to a real route.

### Changed

- `redeploy.py` verifies after migrating that `alembic current` equals
  `alembic heads`, and fails the deploy when they differ. A failed upgrade was
  already caught, but a subtler case was not: the container `exec` runs in can
  be an older image than the one just built, so alembic applies migration code
  that is no longer in the repo - which is exactly how 2026.8.24 shipped new
  ORM code against a schema that had never advanced.

## [2026.8.24] - 2026-08-24

### Added

- Personal **Preferences** page (`/dashboard/preferences`), modelled on GitLab's
  `/-/profile/preferences` and available to **every role** - these are the
  reader's own settings, so it sits behind plain authentication rather than a
  role gate. Colour mode, accent theme, diff colours, keyboard shortcuts,
  layout width, homepage, language, first day of the week, relative times and
  time format. Every value is stored against the account, so it follows the
  user to any device instead of being lost with the browser profile.
- Each preference is wired to something real rather than merely stored: the
  accent tints the selected navigation item and its preview card, layout width
  uncaps the content column, the shortcuts toggle gates the single keydown
  dispatcher (`Esc` is unaffected, so dialogs still close), the time settings
  drive every rendered timestamp, and the first day of the week reaches every
  date picker.
- **Diff colours** apply to the real diff renderer on the student profile - the
  tinted `+`/`-` rows and the additions/deletions counters - not just to a
  preview. The preview on the settings page is that same component.
- The homepage list offers only destinations the signed-in role can actually
  open, and the redirect re-checks the role, so a demoted account falls back to
  the dashboard instead of bouncing off the role gate on every sign-in.
- Guided tour for the Preferences page, in Slovak and English, plus a
  documentation page in both languages.

### Fixed

- SMTP passwords now have surrounding whitespace stripped. Google displays an
  app password as four groups of four, and pasting it exactly as shown failed
  authentication with a bare `535` that named no cause.

## [2026.8.21.post2] - 2026-08-21

### Changed
- Error pages match GitLab's more closely: they use GitLab's own error
  illustrations (404, 403/401, 500, 422→forbidden, 503→rate-limit), shown at
  GitLab's larger size; the "Go back" link is hidden when there is no history to
  return to (GitLab's behaviour); and the 502/503 pages reload themselves while
  the upstream comes back, the way GitLab's boot page does.

## [2026.8.21.post1] - 2026-08-21

### Fixed
- Archived-course forms deformed every input: locking a control wrapped it in an
  inline span that shrink-wrapped a block field, collapsing the Description
  textarea from full width to ~180px (and every other input with it). The
  wrapper now mirrors a block control's box. Verified in the running app.
- Commit History table: the message truncated early with a fixed 640px cap while
  the column had room to spare, and a long branch badge could expand the column.
  The message now fills the column, the badges pin to its right edge on every
  row, and the branch badge truncates. Verified in the running app.
- A group's member table flashed a whole column green on every poll/SSE tick
  (and on tab refocus) because four cells were re-written and flashed
  unconditionally. They flash only when their value actually changed now.
- A table nested in a `<details>` (Show all commits) kept rounded top corners
  under its square toolbar - the disclosure rule lost a specificity battle to
  `:first-child`. Raised so the table squares under the summary.
- The documentation footer's legal column lost its heading (`footer.legalTitle`
  was never defined) and the Diplomovka section listed its pages out of order
  (2, 4, 3, 1, 5) - the nav sorted by slug, ignoring the numbered titles. The
  nav now honours a `weight`, and the i18n completeness test catches keys built
  by `printf`.

## [2026.8.21] - 2026-08-21

### Security
- The documentation search no longer reveals restricted pages. One Pagefind index
  covered the whole site and the role gate served it as an asset, so a signed-out
  reader searching for a word from the operations runbook got its full text back.
  There are three indexes now - public, staff, admin - each built from only the
  pages its tier may read, and the two narrow ones are gated. Path matching in the
  gate is normalised (traversal, percent-encoding, case, backslash) so a disguised
  URL cannot slip a gated section past it.
- Closed an open redirect in `?next=`. `safe_redirect_target` refused `//evil` but
  returned `/\evil` unchanged, and a browser reads those as the same off-site
  address; it was reachable unauthenticated through the language switch. The target
  is normalised the way a browser does before the decision, not after.

### Fixed
- Slovak documentation pages rendered English chrome - "Table of Contents",
  "Skip to main content", the breadcrumb - because the docs interface was pinned
  to one locale and the sidebar loaded the English navigation tree beside Slovak
  content. The interface now follows the page's language, and the dead
  `/docs/en/en/` links and Slovak-under-redirect links are gone.
- The documentation footer showed blank labels: an empty logo alt, no tagline,
  raw link text. It referenced i18n keys that were never defined; all of them now
  exist in both languages, pinned by a completeness test.

### Changed
- Tabs animate their underline the way GitLab's do - a 2px indicator that slides
  up from under the row and previews on hover - instead of a colour appearing in
  place. Portaled dropdowns follow their toggle on scroll rather than closing.
- Componentised the per-page config island: six pages hand-wrote the same
  `<script id="gp-page-config">` wrapper, now one macro owns it. Folded 14
  duplicate CSS rules into shared selector lists, verified byte-identical.

### Removed
- GitLab's leftover documentation strings (feature flags, release posts,
  reference architectures, "Get free trial"), the GitLab logo SVGs and dead social
  icons, and the structured-data claim that GitLab authored these thesis pages.

## [2026.8.19.post1] - 2026-08-19

### Fixed
- Chrome reported "A form field element should have an id or name attribute" on
  every documentation page. The three controls involved belong to dependencies -
  Starlight's theme and language pickers and Pagefind's search box - so rather
  than vendor a component from the theme to add two attributes, one script names
  any control that arrives without them, including the one Pagefind builds only
  when the search dialog first opens. They resolve to `gp-search`,
  `gp-select-theme` and `gp-select-language`: derived from what each control
  already says about itself, so they stay stable across reloads instead of being
  a counter, and de-duplicated so no two controls share a name.

## [2026.8.19] - 2026-08-19

### Fixed
- Twelve documentation pages rendered EMPTY. They carried MkDocs' `md_in_html`
  card markup (`<div class="grid-cards" markdown>`), and Astro treats a raw HTML
  block as HTML - so it stopped parsing markdown at the opening tag and
  everything inside vanished. `en/ucitelia/index` had 105 lines of source and
  rendered nothing. All 46 cards are now Starlight `<LinkCard>`s inside a
  `<CardGrid>`.
- The two home pages are Starlight splash pages, replacing ~60 lines each of
  hand-written hero markup - four gradient blob divs, a fake search slot and a
  quick-link list - with the theme's own hero and card components.
- MDX requires void tags self-closed; eight `<br>` tags were breaking two builds.

### Removed
- 30 lines of footer CSS styling `.gp-footer*` classes that no page emits.
  Starlight renders its own footer and overriding it needs a component, not a
  stylesheet.

## [2026.8.18] - 2026-08-18

### Changed
- The documentation is rebuilt on Astro 7 + Starlight, replacing MkDocs
  Material. The old tree is deleted; the nginx stage and the `/docs/` URL are
  unchanged, so nothing downstream had to move.
  - build 30s -> 8s for 95 pages
  - search: Pagefind, a static index built at compile time, no server
  - the 58 pages carrying a mermaid diagram now ship NO diagram JavaScript -
    `rehype-mermaid` renders them to inline SVG at build time
  - GitLab Sans and GitLab Mono are self-hosted and preloaded
  - the theme is custom properties only, so the Pajamas palette, their type
    clamps, their striped tables and their motion vocabulary are values rather
    than a fight with the previous theme's `[dir=ltr]` rules, em-based icon
    scale, 20px root and duplicated table of contents
- All 94 content files migrated: 147 admonitions converted to Starlight asides,
  4 tab groups to `<Tabs>`, nothing left unconverted.
- The docs mark is redrawn AT 16px rather than scaled down to it. Rendered on a
  real tab-bar grey the previous one was a blob: a deep centre notch plus a
  1.15-wide stroke leaves no negative space at that size.

## [2026.7.3.post237] - 2026-08-18

### Fixed
- Numbered headings threw `Failed to execute 'querySelector': '#1-cloning-the-repository'
  is not a valid selector` on every page carrying one - 143 headings across the
  docs. An id may start with a digit; a CSS selector may not, and Material
  resolves anchors with `querySelector`, so the handler aborted and took the
  table-of-contents tracking with it. Fixed at the slug.
- Icons were off the grid: 566 of 628 rendered at 27x27, 18.19 or 45, because
  Material sizes them in em and this theme's root is 20-22px, not the 16px that
  scale assumes. All 628 are now on 16/20/24/32.
- Code blocks had a bordered card, a caption bar and a line gutter, and long
  lines ran into the copy button. Theirs is a flat surface with a small language
  pill and a copy button; lines scroll inside the block.
- Tables had a rule under every cell and no striping. Theirs is zebra-striped
  (neutral-900 / neutral-950 alternating) with borderless cells.
- The page skeleton now lands on their rendered pixels at 1440: left nav 28/256,
  prose 352/716, table of contents 1128/272, search field 232/470x32, tab row
  40/1360, header 112.

### Added
- A five-column footer matching theirs - brand, social links and four link
  groups - in place of a single centred copyright line.
- A "Was this page helpful?" row above the footer. Theirs posts to their own
  telemetry; both answers here open the support form with the page identified,
  rather than rendering a control that does nothing.
- The docs tab icon is their open book with the GitPulse pulse knocked out where
  their tanuki sits, plus an apple-touch icon on brand charcoal.

## [2026.7.3.post236] - 2026-08-18

### Fixed
- Opening search on the documentation landing page cut the quick-link row in
  half: an empty query gives a short panel and the row sits directly under it.
  Theirs never shows that state - their empty panel is a full "Recently viewed /
  Popular" list that covers the row - so the row now steps aside.

### Changed
- The 30 palette steps the documentation stylesheet did not define are copied in
  from their stylesheet, so no value in the file can fall back to a guess. The
  39 steps already defined were checked against theirs first and every one was
  identical; the application's 69 match theirs as well.

## [2026.7.3.post235] - 2026-08-18

### Fixed
- The documentation header's search field is back to the 470px their content
  page actually renders, with their `padding: 8px 32px 8px 28px` and 16px line
  height. It had been narrowed to 384 on the strength of their declared
  `--search-lg-width: 24rem`, which is not the width the page uses.

## [2026.7.3.post234] - 2026-08-18

### Fixed
- Component-by-component parity with docs.gitlab.com, established by loading
  their page and ours in the same browser at the same size and theme and
  diffing `getComputedStyle` for one element per component. 45 differing
  properties, now 12 - and those twelve are a font-stack ordering, two border
  colours on a zero-width border, and elements one page happens not to have.
  Corrected: body size and line height, h1/h2-h6 margins, list size, line
  height and rhythm, inline code (page-coloured inside a hairline, not
  link-blue), table cell padding and line height, breadcrumb size, TOC line
  height, and footer link size and decoration.
- The landing search panel followed the page theme and so turned white on the
  charcoal hero in light mode. The panel belongs to the hero, and the hero is
  charcoal in both themes, so the panel is now dark in both.
- The table of contents had collapsed into one solid block: matching their link
  padding without also carrying their `--toc-item-spacing: .625rem` left no gap
  between entries, and Material's sticky caption clipped the first one.

## [2026.7.3.post233] - 2026-08-18

### Added
- The documentation has a breadcrumb above every content page, the way
  docs.gitlab.com does - built from `page.ancestors` server-side rather than
  from client-side page metadata.
- The docs tab icon is now its own mark: GitLab's docs favicon is an open book
  in brand orange with the tanuki inside it, so this is the same book with the
  GitPulse pulse inside instead. The app keeps the tanuki.

### Fixed
- Every low-contrast finding on the 18 authenticated pages, 27 in total. They
  were all the same mistake: a colour taken from the PALETTE (a 300/400 step, or
  a raw Tailwind hex) used as text. GitLab reserves those for icons, dots and
  chart arcs; text uses `--gl-feedback-*-text-color`. Worst were the compliance
  ring's centre label at 2.15:1 (`#f59e0b`, a Tailwind amber), the required-field
  asterisk and the delete-course label at 2.55:1, and the quick-avatar initials
  at 3.66:1.
- The compliance ring's arc colour came from three hard-coded Tailwind hexes in
  JavaScript; it now reads the same tokens as the rest of the app, and the
  centre label takes its colour from a state class instead of an inline style.

## [2026.7.3.post232] - 2026-08-18

### Changed
- The whole documentation shell is now transcribed from
  `docs.gitlab.com/vite/main.css` rather than measured off one viewport. Their
  declarations: `--max-width: 86rem`, `--column-left-wide-width: 17rem`,
  `--column-right-wide-width: 17rem`, `--column-center-max: 52rem`,
  `--column-center-min: 22rem`, `gap: 3.75rem`, `padding: 0 2.5rem`,
  `--header-height-lg: 7rem`, `--search-lg-width: 24rem`, and the fluid heading
  clamps. The previous values were what a 1440px window happened to produce.
- The footer matches theirs: `footer{background-color:var(--gl-color-neutral-900)}`
  is a PALETTE value, so it stays the same dark band under a white page as under
  a dark one, with white text, capped at 1376 and padded 32px.

### Fixed
- The 272px columns were rendering 288: `box-sizing: content-box` on the row
  leaked into every descendant, because Material sets `*{box-sizing:inherit}`.
- The footer's TUKE link measured 2.42:1 on all 47 pages - Material's own
  `html .md-footer-meta.md-typeset a` is (0,2,2) and beat every rule written for
  it, so the fix moved to `--md-footer-fg-color--light`.
- The search overlay hint measured 4.47:1 in light mode on 45 pages.
- The header brand rendered as "GitPulse..." on content pages and vanished
  entirely when sized to `max-content` - Material holds the wordmark in an
  absolutely positioned element, so the block has to be pinned.
- The landing hero was squeezed to 768px at every width below 1900 once the
  prose column gained its 832px cap.

## [2026.7.3.post231] - 2026-08-18

### Fixed
- The documentation landing page had two footers stacked on top of each other:
  Material's own `.md-footer-meta` plus a second `.md-footer-custom` region
  appended after `{{ super() }}`. The TUKE line now lives inside the copyright
  partial, so there is one footer.
- Below the hero, the page had three different left edges - prose centred at
  592, rules and mermaid diagrams full-bleed at 0, and Material's table wrapper
  at -18, wider than the window. The landing column now caps everything by
  default, with the hero and the card grid as the only opt-outs, and aligns to
  the same 64px edge the cards use.
- Light theme on the landing was unreadable: the cards were pinned to dark
  surfaces while Material flipped the heading colour, so the card titles were
  dark text on a dark card, and the footer was a near-black band under a white
  page. Both now use GitLab's semantic tokens, which flip with the theme.
- The header floated 33px above the hero panel (Material's `.md-main__inner`
  carries a 1.5rem top margin) so the brand was cut by the page edge, and the
  tab row hung off the panel's left edge.

## [2026.7.3.post230] - 2026-08-18

### Fixed
- The documentation landing page reached readers unstyled: `extra2.css` is served
  with `expires 7d` and has no content hash in its URL, so a browser that had
  opened the docs once kept a week-old stylesheet against fresh HTML. A build
  hook now appends `?v=<sha256[:8]>` of the file's own bytes.
- Login page contrast: the developer-mode badge measured 2.3:1 (orange-300 is
  GitLab's ICON step, not a text colour) and the GitLab sign-in button 2.9:1
  (white on `#fc6d26`, which in @gitlab/ui is `--gl-color-brand-orange-02p` and
  is applied to no component - it is the tanuki's colour). Both now use the
  pairs GitLab ships: orange-800 on orange-50, and the confirm button.

### Changed
- The docs landing page is rebuilt from `docs.gitlab.com/vite/landing.css`
  itself rather than from a screenshot: the panel's four radial blobs, the
  52px pill search with its `/` hint, the quick-link underline wipe, and the
  four-column card grid with GitLab's per-position icon-tile colours.
- The GitLab sign-in button is now the shared `.btn .btn-confirm .btn-block`,
  so its height, radius, focus ring and motion come from `buttons.css`.

### Removed
- Ten decorative left-edge stripes and the dead 133-line `.issue-row` block:
  nothing rendered it, and the tint plus the label already carried the meaning.

## [2026.7.3.post229] - 2026-08-17

### Fixed
- Fenced code blocks rendered every line in link-blue: the inline-code colour was
  reaching `pre > code` too. Inline code stays blue; a code block is the page's
  own `rgb(236,236,239)` with the highlighter owning the rest - measured on
  docs.gitlab.com.

## [2026.7.3.post228] - 2026-08-17

The documentation header, search and chrome measured against theirs, and a
changelog line that had been injecting a live `<script>` into the page.

### Changed
- **Header block 112px, exactly theirs**, with the brand pinned so the search
  field starts at x=232 and runs 470 wide - the numbers measured on their
  content page. The search sits after the brand rather than pinned right the way
  Material places it, and carries their `rgba(5,5,6,0.4)` fill at an 8px radius.
- Sidebar and TOC headings, and the footer's `56px 40px` block, match their
  measurements.

### Fixed
- **The changelog page threw `Unexpected identifier 'verification'`.** One entry
  wrote `<script>` outside backticks, so markdown passed a REAL script element
  into the page and the browser parsed the prose after it as JavaScript. Both
  language changelogs are clean now, and all 12 docs pages report zero errors.

## [2026.7.3.post227] - 2026-08-17

The documentation is now measured against the theme docs.gitlab.com actually
serves - dark - and laid out in their three columns. No migration.

### Changed
- **Dark by default, because theirs is.** The first parity pass measured their
  LIGHT content page; their site serves dark. Body rgb(24,23,29) on
  rgb(236,236,239) text with white headings, code on rgb(40,39,45) inside a
  rgb(76,75,81) hairline, alerts on rgb(40,39,45), footer rgb(40,39,45), the
  active TOC pill rgb(58,56,63) - each measured, and each already a Pajamas
  token this stylesheet carried.
- **Their three columns, to the pixel.** Measured at 1440:
  `20 | sidebar 272 | 60 | content 716 | 60 | toc 272 | 40`. Ours now reports
  sidebar [20,272], content [352,716], TOC [1128,272] - identical. The TOC had
  been folded into the left sidebar by the `toc.integrate` feature, which is why
  the entire right half of every page was empty.
- **A landing page like theirs**: the hero is a 32px-radius panel inset 40px
  from each edge (measured 1360 wide at 1440), its title 64px/73.6px in white,
  a search pill and a row of quick links, with the header sitting ON the panel
  rather than above it. Under it, four cards of ~307px with coloured 32px icon
  tiles.
- The docs favicon is the app's own tanuki - the same file the app serves, so
  the two cannot drift.

## [2026.7.3.post226] - 2026-08-17

One badge in JS, the way there is one on the server. No migration.

### Changed
- **`GP.badgeHtml(text, variant, opts)`** - the same component
  `components/badges.html` renders, for the renderers that were assembling the
  span by hand. Eight JS files decided the class order, the size suffix and the
  escaping per call site; several interpolated untrusted text straight into the
  string. The helper escapes its own text, so the `_esc` wrappers around every
  one of those went with the hand-built markup.

## [2026.7.3.post225] - 2026-08-17

One empty state in JS, the way there is one on the server. No migration.

### Changed
- **`GP.emptyStateHtml` / `GP.emptyStateRow`.** Four places built the same
  "nothing here" markup by hand - core's table loader, the compliance-checks
  error branch, the paginator's filtered-to-zero state and the member filters -
  each with its own idea of whether there is an icon, which icon, and whether
  the message was escaped (two of them did not escape it). One shape, one
  escaping rule, one icon source, so a JS-rendered empty state and a
  server-rendered one are the same thing. The member filters also carried a
  hand-inlined `<svg>` copy of an icon the shared set already has.

## [2026.7.3.post224] - 2026-08-17

The tab icon is the app's own mark, the font preload finally matches the request
it was meant for, and a menu no longer hangs in mid-table after a scroll.
No migration.

### Fixed
- **A portaled dropdown stayed pinned to the viewport while the page scrolled.**
  The paginator's page-size menu is `position: fixed` at coordinates measured
  once, and this app scrolls inside `.gl-page-content` rather than the window -
  so a scroll moved the toggle and left the menu floating over unrelated rows
  until it was clicked away. A menu whose anchor has moved now closes.
- **The font preload warned on every page.** It emitted
  `/static/fonts/GitLabSans.woff2?v=<hash>` while `fonts.css` requests the same
  file with no query: a preload is matched by exact URL, so nothing was reused,
  the face was fetched twice, and Chrome reported "preloaded but not used". The
  href is now the literal path the stylesheet uses.
- **The tab icon is the app's tanuki.** The favicon drew its own 2.6-wide SOLID
  GREEN pulse - a colour the mark uses nowhere else - which at 16px covered the
  face and left an orange blob with a scribble through it. It now carries the
  five tanuki paths and gradients from components/logo.html verbatim, and draws
  the pulse the way that logo draws it (a white guard under a dark core). The
  multi-resolution favicon.ico (16/24/32/48/64/128/256) is generated FROM that
  svg, so the two cannot drift.

### Changed
- **Portaled menus are ONE component** (`GP.dropdown.portal` / `.unportal`).
  The paginator carried a second copy - ~60 lines that moved the menu to
  `<body>`, measured the toggle, pinned it, chose up or down and undid it all on
  close - and that copy is where the scroll bug lived.
- **Every htmx swap re-initialised the WHOLE document**: tippy rescanning every
  tooltip on the page, flatpickr rechecking every date input, and the table
  label / data-style passes walking every table to find nothing new. Each of
  those now runs on the swapped subtree only (modals, which move to `<body>`,
  are initialised after the teleport that moves them).
- **The dropdown direction observer is gone.** It was a MutationObserver over
  the whole body watching `style` and `class`, so every GSAP tween - which
  writes inline styles every frame - woke it dozens of times per frame to
  discover the target was not a dropdown. Direction is decided where it is
  known: at the moment a panel opens.
- **Four more animations became the components that already existed**: the
  modal body's height swap is `GP.motion.resize`, the bottom sheet's release is
  `GP.motion.sheetSettle` / `sheetDismiss` (it was two inline transition strings
  plus two setTimeouts restating their durations, one asking for a token that no
  longer exists), and the dashboard's highlight flash is `GP.motion.highlight` -
  the sixth copy of the class-plus-setTimeout pattern that helper replaced.
- Keyframes 17 -> 13, with no duplicates left: `gl-skeleton-appear` and
  `gp-page-enter` were `fadeIn`, `health-skeleton-shimmer` was
  `gl-skeleton-shimmer`, `trigger-pulse` belonged to a dead button that nothing
  rendered, and `spin-bg` - which spins nothing - is now `gp-input-busy`.

## [2026.7.3.post223] - 2026-08-17

The documentation now matches docs.gitlab.com by measurement, and the last three
layout shifts turned out to be one missing attribute. No migration.

### Changed
- **The docs stylesheet is a rewrite against measured values**, not Pajamas rules
  of thumb: prose 16px on 25.6px (was 14/22.4) in rgb(58,56,63), p margins 20/8,
  h1 40/46 with 24px under it and NO rule, h2 32/40 on 40/20, links underlined at
  rest, inline code 14px on the subtle surface, the code block's box on the
  wrapper with a transparent `<pre>` inside, tables at 14px with 16px cells, and
  a 716px measure. Every colour it uses already resolved to a token the file had.
- **The docs run GitLab's motion inventory: 3 transitions, 0 animations** - their
  colour set on 0.2s out-cubic, form controls on 0.15s ease-in-out, the nav's
  `max-height` on 0.5s cubic-bezier(0,1,0,1). MkDocs Material's 0.25s ease,
  cubic-bezier(0.1,0.7,0.1,1) and its transform transitions are gone, along with
  `scroll-behavior: smooth`. Two narrower attempts leaked (a `:where()` pass left
  20 of 22, an explicit-selector pass left 12), so the contract is universal with
  its exceptions restated under it.
- Every remaining raw `window.confirm` now runs on `GP.confirmDialog` - seven
  sites, three of which an earlier grep had missed. A synchronous modal guard
  vetoes the close and re-issues it through `GP.forceCloseModal` once the promise
  answers; `showDuplicateWarning` became async because its only caller already
  awaited. Two hand-rolled button loading states went with them.

### Fixed
- **The last three layout shifts, all one cause.** `font-display: swap` laid the
  first frame out in fallback metrics and GitLab Sans is wider: on the dashboard
  the courses toolbar grew 610px -> 664px when the face landed, stopped fitting
  beside the heading, wrapped, and dropped everything below it by 33px. The fix
  is `<link rel="preload" as="font" crossorigin>`. A previous attempt added that
  preload WITHOUT `crossorigin`, got Chrome's "preloaded but not used" warning -
  which is exactly what an anonymous preload of a CORS-fetched font produces -
  and reverted the preload instead of adding the attribute. Dashboard CLS
  0.0296 -> 0.0000, course activity 0.0252 -> 0.0000, admin system 0.0011 ->
  0.0000.

## [2026.7.3.post222] - 2026-08-17

Motion is measured again, a loading button keeps its label, and a refresh that
fails says so. No migration.

### Changed
- **Hover moves nothing; the press still does.** The 1px hover lift on every
  button, the 6% scale on every icon button, the 12% scale on the glyph inside a
  sidebar item and the 2px lift on every card are gone - all four contradicted
  rules this repo had already written down, and all four existed only because
  `transform` sat in the app-wide transition list. @gitlab/ui 136.2.0's entire
  transition inventory for a control is `color, background-color, border-color,
  box-shadow` at 0.2s out-cubic. Measured on the course-settings page: elements
  carrying a live transition 1817 -> 762, transition properties 10 004 -> 2 113
  (`box-shadow` 1177 -> 259, `transform` 1153 -> 169).
- **One rotation speed, one pulse, one easing set.** Spinners turned at three
  different speeds (800ms / 1s / 600ms) plus a dead 1.2s token; they now all use
  GitLab's `spin 0.6s linear`. `health-icon-pulse` and `ssePulse` were
  byte-identical copies of `pulse`. `back.out` / `elastic.out` / the two spring
  cubic-beziers are gone: GitLab has three easings and no overshoot.
- **The traffic-light halo is deleted at the root** - an infinite animation of
  `transform` + `opacity` on an `::after` carrying a 12px blurred shadow, running
  once per course card for as long as the dashboard was open.
- **No global `scroll-behavior: smooth`**, which animated every programmatic
  scroll in the app. GitLab sets none.
- **A loading button keeps its label and its size.** The spinner takes the
  leading icon's place (16px for 16px), which is GlButton's own contract; the
  label is untouched. It used to go `color: transparent`, hide every child and
  drop to `opacity: .7` - measured now at 90.2x24 idle, 90.2x24 loading,
  90.2x24 restored. The second loading mechanism (`btn-loading-text`, which
  swapped the label and resized the control) is gone.
- **An archived-course button looks disabled the way every other disabled
  control does** - the disabled token colours, not `opacity: 0.55`.
- **One table loading state, everywhere.** The last two fake-table skeletons
  (webhook configs, compliance checks) are deleted along with `sk_table_cell` and
  the `.gl-table-skeleton-*` CSS: each drew a second copy of its table's markup
  with a guessed row count. Both tables now use `GP.tableSkeleton`, which keeps
  the rows already on screen and dims them.

### Fixed
- **An archived course no longer drops the page 30px after it paints.** The
  status strip is rendered straight into `#globalBannerSlot` instead of being
  portaled there once the parser reaches the tail script - on a 460 KB document
  Chromium has already painted by then. CLS on the archived settings page
  0.0173 -> 0.0000.
- **A failed reload no longer also reports success.** The webhook loader caught
  its own error and returned normally, so the Reload button's wrapper toasted
  "reloaded" on top of the error. `GP.refreshRegion` is now the one refresh
  contract: the control shows it is working, the region shows it is working,
  exactly one toast follows, and an interactive refresh runs ONE attempt on a 10s
  cap instead of apiCall's 3 attempts over 60s+.
- **Three `<label>`s with no form field** (the transfer modal's two group
  captions, the support form's rating caption) are `<fieldset>` + `<legend>` via
  the new `field_group()` macro - Chrome's "A <label> isn't associated with a form
  field" is now zero on every page swept.
- The top-bar clock reserved no width, so the whole right-hand cluster slid
  sideways on every page once JS filled it in.

### Removed
- 12 copy-pasted `GP.confirmDialog || window.confirm` ladders (the shared dialog
  already carries that fallback), plus the raw `window.confirm` in the teachers
  manager and the activity sync prompt.

## [2026.7.3.post221] - 2026-08-13

One loading mark, one page gutter, and a phone layout that stops fighting the
pointer it does not have. No migration.

### Changed
- **The grey-bar skeletons are gone.** `sk_h_bars` (User Role Breakdown, the
  analytics checklist) and `sk_health_dashboard` drew a FAKE version of the
  content. A fake that never resolves is indistinguishable from a broken render,
  and a fake whose shape is a guess resizes the block when the real thing lands.
  Both are replaced by `block_loading`: the tanuki, a label, and the height the
  content will occupy.
- **Refresh is the System Health contract plus the tanuki.** Keep what is on
  screen, dim it, turn the app's one loading mark over it, swap at the same
  size. A pseudo-element on a wrapper that already exists, so no markup changes.
- **A state lasts long enough to see.** A fast response used to flip a table
  busy and back inside a frame or two - a flicker rather than "this refreshed".
  Held 450ms, measured from when it actually started.
- Touch devices drop hover-driven MOVEMENT. A touch screen has no hover, only a
  sticky one that latches after a tap, so a lift meant as a pointer affordance
  becomes a control stuck raised. Colour still answers a press.

### Fixed
- **Mobile spacing edits kept doing nothing** because `.main-container` padding
  was declared in FIVE places across four responsive files - and the one that
  won at phone widths lived inside a `max-width: 480px` block in the TABLET
  file. One declaration now. The gutter goes 12px -> 8px: the card shell (4px)
  and body (12px) already inset the content twice more, so a phone was paying
  28px a side out of 390. Content 340px -> 348px.
- **Card-header action clusters ran off the screen.** `.card-actions` wraps but
  the hand-rolled `.d-flex` wrappers inside it did not: Job History measured
  436px of buttons inside a 348px header. They wrap now, and a button that has
  to shrink truncates its label instead of pushing the row wider. 436 -> 324px.
- The Service Accounts note was a hand-rolled `muted font-sm ml-auto` rather
  than `.card-header-note`, so it kept its own size and missed every fix made to
  the real component.

## [2026.7.3.post220] - 2026-08-13

Refreshing anything keeps what is on screen. No migration.

### Changed
- **A refresh no longer tears down the thing it is refreshing.** The System
  Health card's "Check now" was the one refresh in the app that never made
  anything move: it keeps the rendered dashboard, marks it busy, and swaps it at
  the same size. Every table follows that contract now - rows that are already
  there dim to 0.6 and report `aria-busy` instead of being replaced by a
  placeholder. Throwing away a correct, readable table to announce that it is
  being replaced was the churn behind most of the "everything jumps" reports.
  Measured: 36 rows and 702px before, during and after.
- The Slovak and English catalogs carry plain ASCII punctuation in their values -
  14 en dashes, em dashes, curly quotes and single-glyph ellipses normalised.
  Values only: the keys are the lookup strings `t()` is called with.

### Fixed
- **The calendar's week column went blank** for any month before the semester
  starts - a "Wk" header over six empty cells, which reads as a broken picker
  rather than as "these weeks are outside the semester". Those weeks show their
  ISO number, which is what the code's own fallback already did when no semester
  anchor existed at all.
- **Table corners follow stack position** instead of a list of note classes.
  Anything not on that list - a `<details>` toolbar, a filter bar, a table
  toolbar - rounded the table underneath it while staying square itself.

### Notes
- A CSS minifier finding worth keeping: a selector that BEGINS with a
  pseudo-class is dropped during minification. `:not(.d-none) + x` was in the
  source and never reached the bundle - the rule read correctly and did nothing
  in the browser. A test now fails on any such selector.

## [2026.7.3.post219] - 2026-08-12

Table skeletons are gone, the tanuki is the app's only loading mark, and the
Actions column is reachable on every table. No migration.

### Changed
- **Skeleton ROWS are removed from the tables that load their own data.** They
  were an attempt to hold a table's height and they never could: the row count
  is a guess and the row height is a guess, and a guess that misses is a lurch.
  Worse, only some tables had them, so the same interaction behaved differently
  page to page. Loading is now ONE centred box in the same shape as the empty
  state - so loading, empty and loaded are three states of one layout. The box
  claims the same height cap the loaded container hits, and on a refresh the
  container simply holds the height it already had.
- **Every spinner in the app is the brand tanuki** inside the same turning ring
  the full-page navigation loader uses, at one of four sizes. A table waiting
  for rows and a page waiting to arrive are the same event and now look like it.
  The mark uses flat fills rather than the header logo's gradients: a page can
  hold several spinners at once and duplicate gradient ids resolve to whichever
  rendered first, so the rest would borrow another spinner's colours.
- The Actions column is pinned on every table that has one, not just User
  Management - seven more tables. On anything narrower than the full table the
  row buttons were scrolled off the right edge.

### Fixed
- **A white flash when opening a disclosure.** The focus ring was being animated
  from a 6px transparent shadow, and in dark mode the ring starts with a 1px
  WHITE inset - so clicking a summary flared white across the whole control. The
  ring appears instantly now, which is what a focus indicator is for.
- **A control inside `<summary>` cannot be reached by keyboard** - Enter and
  Space belong to the disclosure, so the copy button on every code-context block
  could be focused and never activated. It is a sibling now, positioned back
  onto the toolbar. Zero such elements across every page.

## [2026.7.3.post218] - 2026-08-12

Motion parity with GitLab is dropped on purpose. Geometry, colour and spacing
stay measured against it; how things MOVE is now the app's own. No migration.

### Added
- **Every control answers the pointer on all four states** - rest, hover,
  pressed, focused. The app only ever changed colour before, because GitLab's
  controls do not move, so nothing ever felt clicked: buttons lift 1px and yield
  to `scale(0.97)` under the finger, icon buttons grow instead of lifting (a
  28px square that rises looks detached from its row), sidebar glyphs scale, and
  a directional arrow moves in its own direction.
- **A travelling underline for tab strips.** One bar slides from the old tab to
  the new one instead of each tab drawing and erasing its own border - which is
  what makes a strip read as a single control, and it holds the eye while the
  panel underneath swaps.
- **Table rows grow an accent bar** from the leading edge on hover. Rows
  deliberately do not move: a grid whose lines shift while you scan it is
  unreadable.
- Focus rings arrive rather than appear, so the focus position stays trackable
  across a long form.

### Changed
- Overlays, toasts and popovers now ARRIVE instead of merely moving: the modal
  dialog settles a hair past its resting place, toasts spring in from the edge
  they dock to and stagger when several land together, and dropdown panels rise
  the last 4px into place.

### Performance
- Every new state animates `transform` or `opacity` only. Both composite, so
  hover costs nothing per frame no matter how many elements the pointer crosses
 - measured after the change, the interaction layer adds no style recalculation
  to any of the profiled animations.

## [2026.7.3.post217] - 2026-08-12

One animation system. GSAP owns every animation that has a beginning and an end;
CSS keeps hover colours and the continuous loops. No migration.

### Changed
- **Motion had 67 hand-written `@keyframes` across 25 stylesheets**, each with its
  own duration, easing and lifecycle, so the same interaction animated
  differently depending on the page. There are now 21, all referenced, and every
  animation with a lifecycle goes through one module (`static/js/motion.js`,
  driving vendored GSAP 3.15). Measured across 14 pages: 2223 visible interactive
  elements, every one animating its state change, every duration a motion token,
  and zero components animating at two different speeds.
- **"Remove this row" existed four times** - `.fade-out` plus a 300 ms timer,
  `.card-dismissing` plus a 300 ms timer, `collapseAndRemove`, and a bare
  `.remove()`. One contract now, which fades and then collapses the space so the
  list closes up instead of leaving a hole.
- **"Here is the thing you asked for" existed five times.** Three were `:target`
  rules, which fire only on the FIRST arrival: following the same anchor twice,
  or arriving through the in-app content swap, highlighted nothing at all.

### Fixed
- **Live updates showed no feedback.** The `.value-updated` class six call sites
  toggled had been reduced to `background-color: transparent`, so a number that
  changed under the user simply changed.
- **`<details>` snapped open in Firefox and Safari** while the card beside it
  glided - the CSS-only disclosure needed Chromium 129+ and did nothing
  elsewhere. Height is animated directly now, so every disclosure in the app
  opens the same way in every browser.
- **A bare `[data-team-id]` selector** matched the action buttons inside a
  group-activity row and replaced their button contract, so those buttons eased
  at half the speed of every other button and stopped animating their
  background. Pagination buttons, tab buttons and the cookie-banner buttons had
  the same problem from their own restated shorthands.
- **The health strip clipped its own text.** It animated `max-height` to a
  hard-coded 120px; a message wrapping to a third line was cut off. It opens its
  real height now.
- **A toast paused on hover could not resume** from where it stopped, and the
  progress-toast appeared with no entrance at all.
- Colour fades no longer drift towards grey: a blue ring or green wash now fades
  to its own transparent form instead of transparent black.

### Removed
- 46 dead or superseded `@keyframes`, the sonar rings in the logo (rendered on
  every page, hidden and unanimated), and `spin-bg`, which hue-rotated a grey
  icon and was therefore invisible.

## [2026.7.3.post216] - 2026-08-12

The select goes back to GitLab's floating panel. No migration.

### Fixed
- **"Make the menu one object with its control" was implemented too literally.**
  Closing the gap and squaring the two meeting corners produced a hard notch that
  looked worse than the gap it replaced. GitLab's listbox is a FLOATING panel: a
  small gap, all four corners rounded, its own shadow. Restored.
- The test guarding this was matching `[x-data]` inside a code COMMENT rather
  than in a rule - the same "prose satisfies the assertion" trap already fixed in
  two other test files. It strips comments before asserting now.

## [2026.7.3.post215] - 2026-08-12

Switching tabs stops resizing the page, and the CI card gets its proportions
back. No migration.

### Fixed
- **post211's tab transition kept BOTH panels in the layout at once.** `display`
  with `allow-discrete` holds the outgoing panel in flow for the whole fade, so
  for a moment two full tables occupied space, the page grew and then snapped
  back - caught exactly in the author's screenshot. The outgoing panel leaves the
  layout immediately now; only the INCOMING one fades, over a layout that is
  already final.

### Changed
- **The CI/CD Health donut was 180px beside five squeezed stat tiles.** It is
  140px now and the tiles take the freed width instead of the row centring itself
  with air at both ends - one number should not be the loudest thing in a card
  that carries six.
- **The Sync button is gone from Analytics.** It fired a full GitLab sync - a
  course-level action that already lives on the course page and on Activity -
  offered from a page that only reads data. Its 178-line handler went with it,
  and so did the tour step pointing at `#btnRefreshAnalytics`, which would
  otherwise have targeted a missing element and stalled the course tour.

## [2026.7.3.post214] - 2026-08-12

The select and its menu become one object. No migration.

### Fixed
- **The animation never reached the menus that matter.** post207 scoped the
  entrance to `.gl-dropdown[x-data]`, but the form `<select>` replacement renders
  its own wrapper classes - so every select in the app, which is what the author
  actually opens, still had no motion at all. The rule covers `.gl-dropdown
  .gl-dropdown-menu` now, whichever mode drives it.
- **The panel and its trigger read as two boxes.** Any gap at all - 4px, then
  2px - left them looking stacked rather than joined. The gap is zero now, and
  while the menu is open the two edges that MEET lose their radius, so the join
  is one continuous edge instead of two rounded corners facing each other.

### Changed
- **The sidebar section headings ("Your work", "Administration") are blue
  again**, on the author's explicit instruction. An earlier measurement read the
  LIGHT theme's `rgb(58,56,63)` and concluded the heading is ordinary text; in
  the dark theme they use, GitLab's reads distinctly cooler than the items under
  it. The weight stays at 425, so only the hue separates it.

## [2026.7.3.post213] - 2026-08-12

Tab switching stops tearing the table. No migration.

### Fixed
- **post211's tab animation tore the table mid-switch.** A tab panel wraps a
  whole data table, and animating `transform` on it promotes that table to its
  own compositor layer and repaints it - visible as the table ripping for a
  moment before settling. Opacity only for tab panels now. A dropdown is small
  enough to slide; a full table is not, and that difference belongs in the rule
  rather than in whoever notices it next.
- **A table's top corner flipped with the DATA.** The notes above these tables
  are rendered conditionally - only when there are unlinked projects, expired
  members and so on - so `:first-child` made the table round on one load and
  square on the next. The test is now an adjacent-sibling one, which says what is
  actually meant: a note immediately above me owns the top, so I do not round it.
  Covers both shapes, the wrapper straight after the note and the wrapper inside
  a `.table-scroll` after it.

## [2026.7.3.post212] - 2026-08-12

A course with no end date can have an exam period again. No migration.

### Fixed
- **The exam period never opened for a course without an explicit end date.**
  `_eff_end` fell back to `semester_start_date + teaching_weeks` - the last day
  of TEACHING - and the exam period is closed as soon as today passes that, so it
  was shut the moment it should have opened. No "Exam Period" card, no exam week
  pills, ever. New `exam_period_default_weeks` setting (default 6, roughly TUKE
  FEI's) is added to the fallback. An explicit `semester_end_date` already covers
  teaching AND exams per its own help text, so that path is unchanged.

## [2026.7.3.post211] - 2026-08-12

Switching tabs eases instead of snapping. No migration.

### Fixed
- **Tab panels swapped instantly** - the Events page's "Recent events" /
  "Dead-letter queue" switch, and every other `[data-tab-panel]`. They are hidden
  with the `hidden` ATTRIBUTE, and `display: none` is not an animatable state, so
  no transition declared on them could ever run. That was the fifth surface in
  the app using this mechanism, so the rule lives in `animations.css` and covers
  all of them at once rather than becoming a sixth local copy: `display` in the
  transition with `allow-discrete`, `@starting-style` for the first frame,
  matching the dropdown and the issue panel exactly.

  Every disclosure in the app now animates the same way, whichever mechanism it
  happens to use: Alpine `x-collapse`, native `<details>`, a class-toggled
  dropdown, and an attribute-toggled panel.

## [2026.7.3.post210] - 2026-08-12

The fourth disclosure joins the other three. No migration.

### Fixed
- **"Issues to Address" opened with no motion at all** - it was the one panel in
  the app that could not animate. It toggles the `hidden` ATTRIBUTE, and
  `display: none` is not an animatable state on its own, so no transition
  declared on it could ever run. It gets the same treatment the dropdown panel
  got in post207: `display` in the transition with `allow-discrete`, plus
  `@starting-style` for the entrance. Opening an issue now slides in like every
  other panel. Guarded by `@supports`, so a browser without it keeps today's
  instant open rather than a half-animated one, and disabled under
  `prefers-reduced-motion`.

  That makes four disclosure mechanisms in the app now behaving identically:
  Alpine `x-collapse`, native `<details>`, the class-toggled dropdown, and this
  attribute-toggled panel.

### Fixed (CI)
- **The lint job failed on 7695e76d.** `ruff check` was run before each of the
  last releases but `ruff format --check` was not - the exact silent gate rot
  this repo has been bitten by before. Formatted, and the formatter is part of
  the pre-release check from here on.

## [2026.7.3.post209] - 2026-08-12

Two cards with identical content stop having two layouts. No migration.

### Fixed
- **"Subgroups and Projects" ran flush to its card edge** while "Group Members" -
  the same card, with the same note-above-a-table content, right beside it - was
  inset. The difference was a `body_class='p-0'` on one of them. Dropped, so both
  keep the body's padding and read as one component.
- **The notes above those tables were square** while the table under them was
  rounded. Every note component is now listed on the rule that gives the block's
  top corners to whatever sits at its top - `.gp-deleted-note` and
  `.member-api-note` were the two that had been missed. Measured: 12px top
  radius, inset 24px, matching the card body's own padding.

## [2026.7.3.post208] - 2026-08-12

The events table stops collapsing while it loads. No migration.

### Fixed
- **A refresh made the table blink through a one-row state.** The loading state
  existed but was a SINGLE centred spinner row, so the table collapsed to one
  row's height and then jumped back to full when the data arrived. Measured
  before: the row count went 1 -> 36 across a refresh. It renders skeleton ROWS
  now - the same shape, the page's own count - so the table is already the size
  it is about to be and the real rows replace them in place. Re-measured: one
  state across the whole refresh, no collapse. This is the app's own documented
  rule (skeletons render the static chrome for real; only fetched data shimmers)
  which this page was not following.

## [2026.7.3.post207] - 2026-08-12

Dropdowns open with motion and stay attached to their control. No migration.

### Changed
- **The dropdown now animates open, deliberately departing from GitLab.** Their
  panel does not animate in either direction - measured, `transition: all 0s`,
  opacity 1 on the first frame - and this app pinned that with a test. The author
  asked for a visible open/close repeatedly and reported the panel reading as
  "not joined" to the control that opened it, so it now slides down 4px over
  120ms. The parity measurement stays recorded in the CSS and in the test, so the
  departure reads as a decision rather than an oversight.
- **Both toggling modes behave identically.** Class-based menus transition
  opacity and transform; Alpine `x-show` menus toggle `display`, which normally
  cannot animate, so they use `transition-behavior: allow-discrete` with
  `@starting-style` to get the same entrance. A select on the Events page and a
  menu in the top bar now open the same way.
- The panel sits 4px below its trigger instead of 2px - with the slide, that is
  the distance at which it reads as hanging FROM the control rather than
  floating near it. Disabled under `prefers-reduced-motion`.

## [2026.7.3.post206] - 2026-08-12

The project page's cards stop being a third card system. No migration.

### Changed
- **`.gl-intelligence-card` was a parallel implementation of `.card`.** Its own
  4px radius, its own header and body, a shadow on hover - sitting beside `.card`
  and `.gl-home-stat`, which is exactly why the project page (Protected Branches,
  Contributors, Repository Stats) read as an older screen. It now uses the same
  values as both: lighter shell at 16px with 4px padding, header ON the shell
  with no band and no divider, content as a darker inset block at 12px, and
  colour-only hover instead of a shadow. Measured: shell `rgb(236,236,239)`,
  16px, 4px - identical to a Dashboard card. No markup changed.

## [2026.7.3.post205] - 2026-08-12

Table corners are decided per EDGE, not per block. No migration.

### Fixed
- **A table can have a note above it AND a pagination bar below it**, and each of
  those owns the edge on its own side. Deciding by "does this block contain
  pagination" - post204's approach - squared off the TOP as well, which nobody
  asked for. Now: the top is rounded unless a note sits above it (the note takes
  it instead), the bottom is rounded unless a pagination bar follows (it takes
  it instead), and the note and the pagination bar carry those corners
  themselves. Verified on every table across all 14 pages - each one matches the
  rule for its own combination.

## [2026.7.3.post204] - 2026-08-12

Table rounding becomes conditional instead of blanket, and count badges converge.
No migration.

### Fixed
- **post203's blanket table rounding broke every paginated table.** "Subgroups
  and Projects" ended up with a curved table edge sitting against a square
  pagination bar. The wrapper is rounded only on edges where it really IS the
  edge of its block: all four corners when it stands alone, bottom corners only
  when an info note sits above it (the note takes the top rounding), and none at
  all when a pagination bar follows.
- **The pagination test had to look at the CONTAINER.** Pagination is not a
  sibling of the scroll wrapper - it lives a level up - so `:last-child` never
  saw it and every paginated table came back rounded. Testing the card body for a
  pagination bar fixes it: measured `radius: 0` on Users and Events, rounded
  everywhere else.

### Changed
- **Count badges use one variant.** The team page's project and member counts
  were `secondary`, which renders as a flat grey box, while Service Accounts and
  Archived Courses use the pill-shaped `muted` - the "just a number on a
  background" difference. All counts are `muted` at `sm` now.

## [2026.7.3.post203] - 2026-08-12

Answers two "why is it different everywhere" complaints with an inventory rather
than another screenshot fix. No migration.

### Fixed
- **Tables: one treatment, not two.** An inventory across all 14 pages found
  exactly ONE table style - `radius 0` in a square `.table-responsive` wrapper.
  The "some rounded, some square" split came from tables dropped straight into a
  `.card-body`, which showed the body's 12px corners while the wrapped ones
  stayed square. The wrapper is rounded now; its `overflow: auto` already clips
  to the radius, so no second clip is needed.
- **Half the app looked unanimated because the colour lives on a CHILD.** A row
  or button transitions, but the text inside it is a `<span>` - and those had no
  transition, so they snapped while their parent eased. Measured before:
  `gl-dropdown-item-title` 148x, `gl-dropdown-item-content` 148x, `.muted` 139x,
  `.users-cell-value` 60x, `.btn-text` 47x, `.sort-link` 27x, `.sort-arrow` 20x -
  all without one. They are in the baseline now and all of them are gone from
  the list; what remains are SVG internals and pure layout wrappers, which never
  change colour.

## [2026.7.3.post202] - 2026-08-12

The centred stat tiles become the dashboard KPI card. No migration.

### Changed
- **`.stat-card--centered` was a different component wearing the same name.** A
  centred stack - icon floating on top, a number, an uppercase caption - sharing
  nothing with the Dashboard's cards but the word "stat". It is now the same
  two-layer shape: a header row (label left, icon right) on the lighter shell,
  then the value in a darker inset block.
- Done with `display: contents` on `.stat-card-content`, which lifts the label
  and value into the grid directly - so **no markup changed** and every existing
  `stat_card()` call keeps working.
- The label reads as a heading on the shell now: sentence case at body size,
  muted, exactly `.gl-home-stat-label`, instead of a tiny uppercase caption.

  Measured side by side against a Dashboard card - identical on every value:
  shell `rgb(236,236,239)` / 16px / 4px, inner `rgb(255,255,255)` / 12px / 12px.

## [2026.7.3.post201] - 2026-08-12

The greeting date stops vanishing on the second visit. No migration.

### Fixed
- **The date under the dashboard greeting was blank from the second arrival on.**
  Reproduced by navigating away and back three times: filled, filled, EMPTY,
  EMPTY. `greeting-sync.js` ships inside `#main-content`, and the SPA loader
  skips any content script already present in `<head>` - correct for a library,
  wrong for a script that writes into the swapped markup, because on the second
  return the markup is fresh and empty and nothing fills it. Scripts can now opt
  in with `data-rerun`: the stale copy is dropped from `<head>` and the script
  executes again. Re-measured: the date holds across all three laps.

## [2026.7.3.post200] - 2026-08-12

Card header titles sit exactly on the row's centre. No migration.

### Fixed
- **A card header's title sat ~5px above centre.** Two causes, both measured, and
  neither was the one I guessed twice (`align-items` was already `center`, and
  the header's own children were balanced 12/12):
  1. `.card-title { line-height: 1 }` made the text box 14px while the icon
     beside it is 16px, so the flex row centred on the ICON and the label rode
     high. A line box at least as tall as the icon makes them agree.
  2. The title/subtitle wrapper is a bare `<div>`, so its box hugged the text
     instead of filling and centring inside the header content row.

  Measured across every card header on three pages: the difference between the
  space above the title and below it is now **0px** on all of them, down from -5.

## [2026.7.3.post199] - 2026-08-12

Header notes reach the right edge, and the centred tiles stop looking bare.
No migration.

### Fixed
- **A header note could not reach the header's right edge.** Writing `ml-auto`
  into the title string only pushed within `.card-title`; the title is wrapped
  twice more before the header itself. The `card()` macro takes a `header_note`
  now and renders it as a SIBLING of `.card-header-content`, which is the only
  place `margin-left: auto` means what it looks like it means. Archived Courses
  reads "Read-only" pinned right - measured 16px from the edge, the header's own
  padding - matching "GitLab bots - read-only" on Service Accounts.
- **The centred stat tiles looked bare** after post194 removed the coloured plate
  behind their icons: a 16px glyph alone above a number, in a tile sized for
  something bigger. The glyph is 20px on these tiles - it is the only thing above
  the value, not a list icon.
- **Tile values ran out of their box.** These sit 5-7 to a row and their value is
  often a PHRASE ("25 words", "11.9 d"), which at `2xl` overflowed. One step down,
  allowed to wrap and to break a long token. Measured: value 81-143px inside a
  178px tile, no overflow.

## [2026.7.3.post198] - 2026-08-12

The disclosure slide actually runs, and an activity-free week stops showing a
loading block. No migration.

### Fixed
- **`<details class="card">` still snapped open.** `.card` is a flex column, and
  `::details-content` becomes a flex ITEM - whose `min-block-size: auto` refuses
  to shrink below its content, so the `block-size: 0` that drives the animation
  was ignored. With `min-block-size: 0` the panel animates: measured heights
  97 -> 195 -> 235 -> 249 -> 251 px across five frames.
- **Week Analytics showed a grey block instead of its chart** on a week with
  compliance data but no activity. The wrapper carries `gl-chart-skel`, which
  paints the loading shimmer until a chart replaces it - and on such a week no
  chart is ever drawn, so the block stayed forever and read as "the chart will
  not load". The empty message was underneath it the whole time. The skeleton is
  cleared when that branch runs.

## [2026.7.3.post197] - 2026-08-12

The micro-motion baseline actually does something now. No migration.

### Fixed
- **post192's motion baseline was invisible.** It set only `transition-duration`
  and `transition-timing-function`, deliberately leaving `transition-property`
  alone - which meant it synchronised whatever already moved and could not
  animate anything that snapped, and most of the app snapped. Declaring the
  property list is the whole point of the rule. Measured before: plain `td`,
  `tr`, `th` and `.badge` had no transition at all. After: **zero** elements
  without one - 149 on the Dashboard, 298 on Admin > Users.

### Changed
- The list is colour, background, border, shadow, opacity, SVG fill/stroke and
  `transform`. `transform` is there NOT to add movement but so components that
  already rotate a chevron keep doing so - this rule sits at the end of the
  bundle and would otherwise freeze them.
- Written with `:where()`, so it carries **zero specificity**: any component's
  own transition still wins, and the baseline only fills in where nothing else
  applies. A property still animates only if something actually changes it, so
  this makes existing state changes smooth without reintroducing the entrance
  animations removed app-wide.

## [2026.7.3.post196] - 2026-08-12

Archived Courses takes the Service Accounts header, and every clickable header
answers the cursor the same way. No migration.

### Fixed
- **Only some clickable headers lit up on hover.** `.card-header--interactive`
  (Service Accounts) had NO hover rule at all, while `.gl-home-archived
  .card-header` carried its own - two identical-looking rows answering the cursor
  differently. One rule now covers both, on the shared selector, and the local
  copy in `home.css` is deleted so it cannot drift back. Colour only: a header is
  a row, not a button.

### Changed
- **Archived Courses uses the same header anatomy as Service Accounts**: icon,
  label, a count BADGE instead of a bare `(2)`, and a muted right-aligned note.
  The note reads "Read-only", which is what an archived course actually is - the
  same shape as "GitLab bots - read-only" beside it.

## [2026.7.3.post195] - 2026-08-12

Undoes post193's bloat: GitLab's spacing scale is not Tailwind's. No migration.

### Fixed
- **post193 read GitLab's classes against the wrong scale and inflated every
  card.** `gl-p-2` / `gl-p-4` were converted as Tailwind (8px / 16px), but
  GitLab's scale is Pajamas' - and it maps 1:1 onto this app's own tokens:
  `-2` = 4px, `-3` = 8px, `-4` = 12px, `-5` = 16px. So `gl-p-2` is 4px and
  `gl-p-4` is 12px, which is exactly what the cards already had. Shell padding,
  inner padding and header margin are back to 4px / 12px / 8px+12px. The ONE
  value genuinely wrong is kept: the inner block's radius, `rounded-[.75rem]` =
  12px, where ours had 8px. The generic `.card` and the admin tiles follow.

## [2026.7.3.post194] - 2026-08-12

The admin stat tiles join the card system. No migration.

### Fixed
- **The admin tiles were a different product.** `.stat-card` (Events, System)
  measured a 4px radius on a transparent box while the dashboard's `.gl-home-stat`
  were 16px shells - and its `.stat-icon` was a **40px coloured plate** behind the
  glyph, the same pattern already removed from the support rows. That plate is
  the empty blue block under "0 RUNNING". Tiles now measure 16px radius, 8px
  padding, the same shell colour, and a 16px monochrome glyph.
- **State colours moved from the plate to the glyph.** `.stat-icon-success` and
  friends filled a tinted background; they colour the mark itself now, which is
  how GitLab signals state - the reading is unchanged, the block is gone.

## [2026.7.3.post193] - 2026-08-12

Card proportions taken from GitLab's own DevTools output. No migration.

### Fixed
- **Three of the five card measurements were wrong.** Read straight off GitLab's
  markup for this exact card (`gl-rounded-[1rem] gl-p-2` on the shell,
  `gl-rounded-[.75rem] gl-p-4` on the inner block, `gl-mx-4 gl-my-3` on the
  header):

  | | GitLab | was | now |
  |---|---|---|---|
  | shell radius | 16px | 16px | 16px |
  | shell padding | 8px | 4px | 8px |
  | inner radius | 12px | 8px | 12px |
  | inner padding | 16px | 12px | 16px |
  | header margin | 12/16px | 8/12px | 12/16px |

  The generic `.card` mirrors the same numbers, so both card families stay one
  system. Verified in a browser: 16px/8px shell, 12px/16px inner, 12px/16px
  header, label at weight 400 exactly as GitLab's `gl-font-normal`.

## [2026.7.3.post192] - 2026-08-12

Raw Check Details becomes the shared component, and every control moves on one
clock. No migration.

### Fixed
- **Raw Check Details drew TWO chevrons.** It was a bare `<details>` with a local
  `.json-toggle` summary that kept the browser's native marker AND painted a
  second arrow from a HAND-WRITTEN SVG mask on the left, while the component's
  own chevron sat on the right. It also coloured its label link-blue and carried
  its own background and padding. It is now the same
  `<details class="card"> + <summary class="card-header">` as Service Accounts,
  and the 34-line `.json-toggle` block is deleted.

### Changed
- **One clock for every interactive surface.** Components had each picked their
  own `--transition-fast/-normal/-slow` and easing, so two controls side by side
  responded at visibly different speeds. A baseline now sets only
  `transition-duration` and `transition-timing-function` - never
  `transition-property`, so it cannot animate anything that was static. Measured:
  48-74 elements per page now share `0.1s` on
  `cubic-bezier(0.22, 0.61, 0.36, 1)`.
- `--transition-control` (form fields) was the last outlier at `150ms ease-in-out`
  and is on the same pair as everything else.

## [2026.7.3.post191] - 2026-08-12

Native <details> opens as smoothly as the Alpine card. No migration.

### Fixed
- **Only one disclosure in the app slid open.** `card(collapsible=true)` animates
  its height through Alpine's `x-collapse`, so Archived Courses glides - while a
  native `<details>` snaps, which is what Service Accounts and Raw Check Details
  did right beside it. Native `<details>` now animates on the same
  `--motion-duration-normal` / `--motion-ease-standard` pair, via
  `interpolate-size: allow-keywords` (what makes `height: auto` animatable at
  all) and `::details-content` with `allow-discrete` so the content is not
  clipped away on frame one. Guarded by `@supports`, so a browser without them
  keeps today's instant open rather than a half-animated one, and disabled under
  `prefers-reduced-motion`.

## [2026.7.3.post190] - 2026-08-12

One disclosure contract instead of three. No migration.

### Fixed
- **The same collapsible header behaved three different ways.** Archived Courses
  drew a white ring, Service Accounts drew nothing, and Raw Check Details drew a
  blue one - three markup shapes (`card(collapsible=true)`,
  `<details class="card"><summary class="card-header">`, and a bare `<details>`
  with `.json-toggle`) that had each grown their own focus treatment. They share
  ONE keyboard-only `--focus-ring` now, the same token 29 other selectors use.
- **Raw Check Details had no chevron at all** - the only disclosure in the app
  with nothing to animate. It has one, and the rotation rule is no longer scoped
  to `details.card`, which is why a plain `<details>` inside a card would have
  sat frozen anyway.
- **Two disclosures animated at different angles**: the collapse BUTTON swung
  -90deg while every `<details>` chevron swung 180. Both rest at 0 and open to
  180 now - one angle, one duration.
- **The chevron sat off the row's optical centre** next to "Archived Courses".
  `align-self: center` plus its own line box removes the drift.

## [2026.7.3.post189] - 2026-08-12

The banner's timestamp comes back, and the week explorer always opens on a week.
No migration.

### Fixed
- **The stale-data banner had a timestamp-shaped hole where its date should be.**
  `time[data-localize-time]:not([data-localized="1"])` is `visibility: hidden`
  (utilities.css) so the server's UTC value never flashes before JS converts it -
  which means a `<time>` the localiser never visits stays invisible FOREVER while
  still occupying its box. Top banners are portaled into `#globalBannerSlot`,
  which lives OUTSIDE `#main-content`, so a navigation's scoped localise pass
  never reached them: "Most recent snapshot:" was followed by a hole and then
  "(7 day(s) ago)". The portal localises the banner as it lands. Verified after
  an SPA navigation AND a full load: `data-localized="1"`, visible, 129 px wide.
- **Week Analytics opened with nothing selected.** The explorer picks the newest
  week that has data, falling back to the pill marked "now" - and BOTH come up
  empty once a course runs past its teaching window, leaving an empty panel that
  only came alive if the reader happened to click a pill. It now falls back to
  the newest week that exists. A week explorer must always be showing a week.

## [2026.7.3.post188] - 2026-08-12

The font-weight ladder gets its missing step. No migration.

### Fixed
- **`--font-weight-semibold` was 500 - identical to `medium`.** Four names, three
  values: every one of the 276 places asking for semibold silently got medium.
  That is why two headings of the same level could render at different weights -
  one asked for semibold (got 500), the other for bold (got 600), and the step
  between them did not exist. The ladder is GitLab Pajamas' now: 400 / 500 /
  600 / 700. GitLab Sans is a VARIABLE font with a 100-900 axis, so 600 and 700
  render natively - nothing is synthesised.
- **Two places that asked for `bold` meant `semibold`.** With the ladder fixed,
  `.card-title` (700) out-weighted the `h2` section heading above it (600), and a
  table's `th` out-weighted every page heading on screen. Headings and column
  labels take semibold; bold is for emphasis inside running text. Measured after:
  `h1` 700, every `h2`/`h3`/`.card-title`/`th` 600, body 400/500.

## [2026.7.3.post187] - 2026-08-12

Support list rows drop their gradient icon tiles. No migration.

### Changed
- **The support pages' course rows use a plain GitLab icon, not a coloured
  tile.** Each row carried its glyph in a 36 px blue GRADIENT square with a white
  icon at 4 px radius - the loudest non-GitLab element on those pages. GitLab
  puts a 16 px monochrome glyph in the muted text colour on a list row and
  reserves colour for status. The registry's icons were already real Pajamas
  paths; only the tile was invented. Now: transparent, no radius, 16 px,
  `rgb(98,97,104)`.
- **Row proportions follow the rest of the card system.** 8 px radius like every
  other inset block (was already), 4 px between rows (was 12 px stacked on top of
  the card's own gap, which is what made the spacing read as arbitrary), and hover
  is colour only - the shadow and the blue border are gone, because GitLab does
  not lift or shadow a list row.

### Fixed
- **The last flush-edge radius.** `details.card:not([open]) > summary.card-header`
  still restored the 12 px SHELL radius on a collapsed card, leaving the header
  rounder than the shell's own inner corner. It takes 8 px like every other block.
- Comments in `cards.css` claimed 8 px where `--gl-spacing-2` is 4 px. Wrong
  numbers in comments are exactly the drift these comments exist to prevent.

## [2026.7.3.post186] - 2026-08-12

A navigation leak that duplicated element ids, and three card-shape fixes.
No migration.

### Fixed
- **Duplicate form field ids piled up as you navigated.** Reproduced by clicking
  around the sidebar in laps: after three laps the page held THREE copies of four
  ids (`courseSemesterStart-fp-0` and friends), which is what DevTools reported
  as duplicate form field ids on the analytics page. flatpickr appends its
  calendar to `<body>` BESIDE the modal rather than inside it, so dropping the
  outgoing page's teleported modals orphaned the calendar and every navigation
  minted another set. `_dropPageModals` now destroys the instances first (that is
  what removes the calendar) and sweeps any calendar whose input has left the
  document. Re-measured: three laps, zero duplicates.
- **Dead space under the header of a collapsed card.** post185 separated the
  card's blocks with a margin on the header, but a collapsed card's body is
  hidden and still present, so the header was never `:last-child` and the margin
  applied anyway. It is a flex `gap` on `.card` now - a `display: none` child
  takes no gap at all. Archived Courses measures a symmetric 5 px inset again.
- **Table corners poking out when a card expands.** `.gl-home-archived .card-body`
  has `padding: 0`, so the table runs flush to that block's edges and its square
  corners sat on top of the block's 8 px rounding. Clipped to the block; its
  divider went with it, since the card's gap already separates the two.
- **The snapshot label and its value drifted apart** in the stale-data banner.
  Label, timestamp and age are one `nowrap` unit now, so the value stays welded
  to its colon instead of ending up on the far side of a full-width banner.

## [2026.7.3.post185] - 2026-08-12

Card blocks get a seam, and the last flush-edge radii are gone. No migration.

### Fixed
- **The header's hover highlight ran straight into the body.** Two inset blocks
  touching with no seam read as one smudged shape. They are separated by 8 px
  now - the same value as the shell's own padding, so the gaps around and
  between every block are equal.
- **The last two flush-edge radii.** `.card > .card-body:last-child` still had
  `0 0 12px 12px` and `.card-footer` the same: square TOP corners, correct only
  while a child finished the card's own rounding. Inset, those square edges show
  against the shell exactly like the header's did. Every direct child now takes
  8 px on all four corners, and the footer's divider went with them - the gap
  above it already separates it.

Swept in a browser across three pages: every card child reports an 8 px radius
and a symmetric 5 px inset on all four sides. No mismatches left.

## [2026.7.3.post184] - 2026-08-12

Cards take the dashboard KPI card's shape. No migration.

### Changed
- **`.card` is a lighter shell with a darker inset block**, not a full-bleed band
  with content pressed to the edges. post183 gave the header a band and read as
  GitLab's PANEL; the reference is the dashboard KPI card - lighter shell
  (`--gl-background-color-strong`) at 16 px with 8 px padding all round, content
  inside it as a darker block (`--gl-background-color-default`) with its own
  8 px radius. `.gl-home-stat` already had exactly this, so `.card` now mirrors
  its values and the two card families are one system.

### Fixed
- **Corners poking out of the frame on a collapsed card.**
  `.card > .card-header:first-child` still forced `12px 12px 0 0`, written for a
  header flush with the card edge. Inset by the shell's 8 px padding its top was
  too round and its bottom was square, so a header-only card - Archived Courses
  when collapsed - showed square corners past the rounded shell. It takes the
  inner block's 8 px on all four corners now.

## [2026.7.3.post183] - 2026-08-12

Every card gets GitLab's header band. No migration.

### Changed
- **`.card-header` is a lighter band, like GitLab's panel headers.** GitLab's
  panels carry the title and its count on a distinct lighter strip with the
  content on the panel's own darker colour below - the shape the KPI cards
  already had (lighter shell, darker inner block). The generic `.card` was the
  last surface without it, so a `.card` and a `.gl-home-stat` side by side read
  as two different systems. The band spans the card's full width and its top
  corners follow the card's 12 px radius (the measured GitLab card value, which
  ours already matched). Uses `--gl-background-color-subtle`: the only
  background token that steps off `default` in BOTH themes - `overlap` collapses
  to the card colour in light mode and the band would simply vanish there.

## [2026.7.3.post182] - 2026-08-11

An empty student profile stops lying about why it is empty. No migration.

### Fixed
- **"No merge requests found in the synced repositories" was a claim the page
  could not make.** The list is scoped to the course's activity window
  (`_course_activity_window`), so merge requests dated before the semester starts
  are filtered out and the reader was told nothing existed. Reproduced against
  the dev database: course ZDEVOPS-DEMO runs 2026-09-21 -> 2026-12-20, the
  student's merge request is dated 2026-06-23, and the profile reported no work
  at all. When a window is active the empty state now names it, so a teacher can
  tell "did no work" apart from "worked outside the course run".

## [2026.7.3.post181] - 2026-08-11

Keyboard focus is visible in menus, and the last off-system control is gone.
No migration.

### Fixed
- **Dropdown menu items had no focus ring.** `:focus-visible` killed the outline
  and then only repeated the hover background, so tabbing through the user menu,
  the language picker or the tour entry gave no "you are here" signal - the one
  control family in the app without a ring, while 29 other selectors use the
  `--focus-ring` token. The ring is INSET (`inset 0 0 0 2px`) rather than that
  token, because `--focus-ring` is an outer box-shadow and a dropdown item is a
  full-bleed row whose outer ring the menu's own edges would clip. Verified with
  a real Tab press: `:focus-visible` matches and the ring paints.
- **The tour's close button was the last control sized outside the system.**
  `font-size: 1.1rem` computed to 17.6 px and `border-radius: var(--radius)` to
  4 px. Now `--font-size-lg` on a 24 px box at 8 px radius. A sweep of every
  visible `.btn`, `button`, `input`, `select`, `.badge` and `.state-pill` across
  six pages now reports **zero** fractional pixel values app-wide - fractional
  sizes being the reliable tell that a control was sized in rem instead of the
  design system.

## [2026.7.3.post180] - 2026-08-11

The tour's buttons stop re-implementing the button system. No migration.

### Fixed
- **The tour welcome dialog's buttons are real buttons again.** Found by
  measuring the same component on every page: the markup already ships
  `.btn .btn-primary .btn-sm`, and `tour.css` then restyled it from scratch in
  rem units that silently won - `font-size: 0.86rem` (13.76 px vs the token's
  14), `padding: 0.45rem 0.95rem` (7.2 x 15.2 px vs 0 12 px on a fixed height)
  and `border-radius: var(--radius)` (4 px vs 8). Fractional pixel values are the
  tell; nothing in the design system produces them. The overrides are gone, only
  the `flex: 1` that is genuinely this component's own is kept, and the hover
  `translateY(-1px)` went with them - GitLab animates colour on a control, never
  transform. Re-measured: 24 px tall, 0 8 px padding, 14 px, 8 px radius -
  identical to every other `btn-sm` in the app.

### Added
- A gate that fails if any stylesheet sizes a bare `<button>`, which is how this
  override beat `.btn` in the first place, plus one that keeps the tour markup on
  the shared classes so removing the override cannot strand it.

## [2026.7.3.post179] - 2026-08-11

The logo hover ends as smoothly as it starts. No migration.

### Fixed
- **No more jerk when the cursor leaves the logo.** You cannot transition OUT of
  a removed animation - the spec does not treat animation output as a
  transition's before-change style. Measured in a browser: brightness dropped
  1.66 -> 1.00 between two consecutive samples, whatever transition was declared.
  So the animation is never removed now. It stays applied and PAUSED at rest, and
  a separate registered amplitude property (`--gp-amp`) carries the effect in and
  out. Re-measured: 1.47 -> 1.13 -> 1.07 -> 1.03 -> 1.01 -> 1.00 over 420 ms.
- **A stale rule was silently clobbering the fix.** `transition: filter 0.8s ease`
  appeared twice more for the same five shapes, later in the file than
  `.gp-part`. The `transition` shorthand REPLACES rather than merges, so it
  dropped `--gp-amp` from the declaration and the snap came straight back with
  the rest of the fix already in place. Both copies are gone; a test now fails if
  a second one appears.

### Changed
- The hover peak is `brightness(1.85)`, up from 1.5, and the wave carries a
  double drop-shadow - at 24 px the old lift was too quiet to notice.
- The wave layer rests at `opacity: 0`. A paused sweep freezes mid-trace, and at
  any visible opacity that would park a bright stub somewhere on the mark; the
  halo, guard and core layers draw the ECG at rest.

## [2026.7.3.post178] - 2026-08-11

Reverts post177's card and merge-request restyling. No migration.

### Reverted
- **The KPI cards go back to the style they had before post175.** Restored
  byte-for-byte from a4b58dd5: filled on `--gl-background-color-strong`, 16px
  radius, transparent border, the inner block on the panel colour, and the hover
  lift with its shadow. The header band added in post177 is gone.
- **The student page goes back too** - `pages/student.css`,
  `components/student.html` and `partials/student/_detail_content.html` are
  restored to a4b58dd5, so the merge-request cards, their people block and the
  column head row are all as they were.
- The unit test pinning "outlined, colour-only, no transform" on the KPI cards is
  removed with them; a test asserting a rejected style only re-breaks it later.

## [2026.7.3.post177] - 2026-08-11

KPI cards get their header band back and merge requests become a GitLab list.
No migration.

### Fixed
- **The KPI card is two bands, not one flat box.** GitLab's own cards carry a
  lighter header bar with the muted label and its icon, then the number on the
  panel's darker colour below. "Outlined, not filled" was taken to mean flatten
  the header into the body, which removed the one thing giving the card its
  shape. The band is back: full-bleed, clipped by the card's 8px radius.
- **The band uses `--gl-background-color-subtle`, not `-overlap`.** Measured in a
  browser before shipping: `overlap` resolves to the SAME value as `default` in
  light mode (both `gray-0`), so the header would have been invisible on half the
  app. `subtle` steps off `default` in both themes. The merge-request card header
  had the same latent bug and is fixed with it.

### Changed
- **Merge requests are a GitLab list, column for column.** `Status | Title |
  Assignee | Reviewers | Checks`, with a labelled column head above the list. The
  title cell stacks the title over its `namespace/project!iid` reference, commit
  count and `+N -N` diff stats. Assignee and Reviewers moved out of the labelled
  block below the header and into their own columns, showing an em-dash when
  empty so the columns stay readable down the list. The head row and the card
  rows share ONE grid track definition, so they cannot drift out of alignment;
  below 1100px the row stacks and the head is hidden, because misaligned column
  labels are worse than none.

## [2026.7.3.post176] - 2026-08-11

The done state stops eating the button it decorates. No migration.

### Fixed
- **The System Health button no longer freezes on "Checking..." forever.**
  Loading and done are two states competing for one button's `innerHTML`, and
  nothing arbitrated between them. The success toast handed the button a done
  state, which snapshotted `innerHTML` to restore later - but at that moment the
  resting label lived in `dataset.originalText` and `innerHTML` still held
  "Checking...", so 1.6s later the button was painted with its own loading text
  and nothing ever ran again. `setButtonDone` now resets the loading state first
  (making the snapshot correct by construction), `setButtonLoading(btn, false)`
  defers to a done state already showing instead of wiping it one frame in, and a
  new click tears the done state down before taking its own snapshot. Verified in
  a browser: `Skontrolovať teraz -> Kontrolujem... -> Hotovo -> Skontrolovať
  teraz`, twice back to back, on both actions on the page.
- **The logo hover loops instead of stopping in the wrong place.** A single pass
  had to end somewhere and `forwards` parked the bright segment at the right-hand
  end of the trace - a lit stub off to one side, which reads as broken rather
  than finished. Sweep and flare now share one 0.9s period so the per-shape
  delays stay in phase, and the sweep is `linear` because an eased loop hitches
  at every wrap. It still runs only under the cursor.

### Changed
- Ending a done state is now one shared teardown (`_clearButtonDone`), used both
  by the timer that ends it and by a new click that supersedes it.

## [2026.7.3.post175] - 2026-08-11

Two navigation bugs closed, a GitLab page footer, and the merge-request list gets
GitLab's row anatomy. No migration.

### Fixed
- **A finished background job no longer hard-reloads a page that never asked
  for it.** `GP.autoReloadOnJob` lives in `core.bundle.js`, which SPA navigation
  never re-runs, so patterns registered by Admin > Courses outlived that page: a
  sync completing while the reader sat on the Dashboard reloaded *that* page via
  `window.location.assign`, URL visibly gaining `?_gp_refresh=`. Navigation now
  clears the registration (`GP.clearJobReload`); each page re-registers on
  arrival.
- **The top progress bar no longer sweeps backwards on fast navigation.** When a
  navigation started while the previous bar was still fading, the rewind to 8 %
  ran *with* its transform transition - and removing `.is-active` only starts a
  630 ms opacity fade, so the backwards sweep was visible for that whole window.
  The rewind is now committed with transitions off.

### Added
- **GitLab's page footer.** A centred `Leave feedback | Documentation` pair
  closes the content panel on every page. The Dashboard opts out
  (`page_footer = false`): its sidebar already ends with "Support &
  suggestions", so a second feedback link would duplicate it.

### Changed
- **Merge-request rows follow GitLab's anatomy.** The state pill leads, the bold
  title takes the slack, the "Updated ..." stamp is pinned right, and a muted
  `namespace/project!iid` reference replaces the bare `!9` plus folder chip.
  Cards get GitLab's panel chrome: a full-width header bar on the overlap
  colour, and a border-only hover - GitLab's list rows do not lift.
- **The admin dashboard's KPI cards join the rest of the app.** They kept the
  grey fill and a `translateY(-2px)` lift while every other surface moved to
  outlined-on-panel; both are gone, and hover is a colour change, which is the
  only thing GitLab animates on a card.
- **The logo hover is rebuilt around what the mark is.** GitPulse is an ECG
  trace across the tanuki, so the hover plays that pulse: a bright segment
  travels the trace over 0.9 s and each shape flares as the wave reaches it,
  90 ms apart. One pass per hover, colour and stroke only.

## [2026.7.3.post174] - 2026-08-11

Cards go back to being outlined, and the cut is thinner. No migration.

### Fixed
- **The card fill added in post169 is reverted.** GitLab's dashboard cards are
  OUTLINED, not filled - they sit on the panel's own colour and are read by their
  border alone. post169 filled them with `--gl-background-color-overlap` on the
  theory that surface contrast was what made the cut under the crumb row
  readable. It was not; the cut comes from the band, and the fill only put a grey
  block where GitLab has none. Cards are rgb(24,23,29) with a rgb(76,75,81)
  border again.
- **The cut is 2px instead of 4px.** GitLab's own band measures 4px, but theirs is
  painted in the panel colour and does not read as a line at all; ours is painted
  in the shell colour so it is visible, and at 4px that reads heavier than
  GitLab's separation. 2px in the shell colour lands where theirs does visually.

## [2026.7.3.post173] - 2026-08-11

The avatar fills its control. No migration.

### Fixed
- **The top-bar avatar was 24px inside a 32px button.** Every other item in the
  bar is a 32px box centred on the 24px midline, so the avatar was the one thing
  reading undersized. It fills its control now - 32x32, still centred on 24.

## [2026.7.3.post172] - 2026-08-11

The cut, in the colour that makes it a cut. No migration.

### Fixed
- **The band is painted in the shell colour, not the panel's.** Every previous
  attempt gave it `--gl-background-color-default` - rgb(24,23,29), the panel's
  own colour - so it merged into the panel and did nothing visible, and I then
  argued it was invisible by design. It is not: the band reads as a slot cut
  clean through the panel, continuous with the background around it, and that
  continuity is what separates the header from the content sliding underneath.
  It is `--app-shell-bg` now: rgb(40,39,45) on a rgb(24,23,29) panel, 4px, full
  width, sticky at the top of the scroll region, fading in over 200ms once the
  region scrolls.

## [2026.7.3.post171] - 2026-08-11

The 4px masking band and its scroll controller are removed. No migration.

### Removed
- **`.gl-page-content::before` and `_initScrollScrim`.** The band matched GitLab's
  `.panel-content-inner::before` exactly - 1123x4, opacity 0 -> 1, painted in the
  panel's own colour - but it is invisible on its own in both apps (its colour IS
  the panel's), so it only ever masked 4px of content. Removed on request, along
  with the `.is-scrolled` class, the scroll listener and the test that pinned it.
  What actually makes the cut readable is the surface contrast shipped in
  post169: cards at rgb(40,39,45) on a rgb(24,23,29) panel, so content sliding
  under the opaque 36px header is sliced against a darker band.

## [2026.7.3.post170] - 2026-08-11

The logo gets its own signature, and its size matches GitLab's mark. No
migration.

### Changed
- **A hover of our own instead of a copy of GitLab's.** Their fill swap never
  transferred: the tanuki is one flat deep red, ours is five gradient-filled
  shapes, and matching their number either flashed (post160) or bleached the mark
  to white (post166). The mark now runs a pulse across itself, left to right -
  each shape lights 60ms after the one before, at brightness 1.45, and unwinds in
  the same order over 0.45s. Colour only: nothing moves, nothing reflows, and it
  reads clearly at 24px because the eye follows the sequence rather than a single
  step. Measured mid-flight: +40ms left ear 1.32 while the centre is still 1.00,
  +130ms left ear 1.45 / centre 1.18, +260ms the wave reaches the right ear.
- **The mark is GitLab's height again.** Ink 24px tall, the exact height of their
  tanuki (ours stays wider at 29px - it is a wide-format drawing, and the height
  is what the eye reads as size). The wordmark keeps its 16px step; GitLab ships
  no brand text, so there is no number of theirs to copy there.
- **Header geometry confirmed against their DevTools reading:** 1371x48 at the
  same viewport, `gap: 16px`.

## [2026.7.3.post169] - 2026-08-11

The cut is visible, and the reason it never was is fixed. No migration.

### Fixed
- **Dashboard cards were painted the panel's own colour.** `.gl-home-card` used
  `--gl-background-color-default` - rgb(24,23,29), byte for byte the panel behind
  it. GitLab's cards sit one step lighter, on `--gl-background-color-overlap`,
  and that contrast is the whole reason its cut under the crumb row reads: a card
  sliding under the header is sliced against a darker band. Ours was invisible
  because there was no difference to see. Six attempts went into the 4px band
  itself, which had been correct since post165 - the missing piece was the
  surface it cuts. Cards are rgb(40,39,45) on a rgb(24,23,29) panel now.

## [2026.7.3.post168] - 2026-08-11

Pages are not squashed against the header any more. No migration.

### Fixed
- **The top spacing removed in post163 is back.** That change was based on a bad
  reading: GitLab's dashboard leaves a clear band between the crumb row and its
  first content block, and its cut reads precisely BECAUSE the content has
  somewhere to start from. Flattening every page against the header did not make
  the cut any more visible, it just squashed the layout. `.main-container` keeps
  its 24px top padding and the greeting its 16px again.

## [2026.7.3.post167] - 2026-08-11

The logo keeps its colour on hover. No migration.

### Fixed
- **The logo bleached to near-white on hover.** post166 copied GitLab's "+52% of
  the way to white" as a NUMBER, but that number belongs to their mark, not ours:
  their tanuki starts at a deep red rgb(226,67,41), so 52% lands on a pink that
  still reads as the logo. Our shapes are light multi-hue gradients and the same
  52% washed them out entirely. What transfers from GitLab is the behaviour - a
  small lift, 0.1s in, 0.8s back - not the percentage. A plain
  `brightness(1.12)` holds the mark's colour: measured saturation is 0.17 both
  at rest and on hover, where the wash had driven it toward grey.

## [2026.7.3.post166] - 2026-08-11

The logo hover, tuned against GitLab's own numbers. No migration.

### Fixed
- **The logo lift is measured, not guessed.** GitLab's hover, read part by part
  on gitlab.example.com: only `.tanuki` changes - rgb(226,67,41) ->
  rgb(241,166,153), which is 52% of the way to white - in 0.1s, while the cheeks
  and chin hold their colour and return over 0.8s. Ours lit every shape with
  `brightness/saturate`, which is why it read as a flash. Our shapes are
  gradient-filled so `fill` cannot be transitioned the way GitLab's flat fills
  are; `filter` is the equivalent, and `brightness/saturate` cannot reach the
  target at all - it tops out near +30% and drives the centre shape DARKER,
  because `saturate` moves colour toward grey rather than white.
  `contrast(0.07) brightness(2.3)` collapses toward mid and lifts from there,
  landing at +45..51% against GitLab's +52%, verified by sampling the painted
  pixels of the mark before and after hover. The return measures exactly 0%.

## [2026.7.3.post165] - 2026-08-11

The cut under the breadcrumb, copied from the element itself. No migration.

### Fixed
- **The cut is `.panel-content-inner::before`, and it is 4px.** Every earlier
  attempt looked for a "scrim" - GitLab does not call it that, which is why a
  stylesheet search for the word kept coming back with the sidebar's gradient.
  The real element measures 1111x4 and reads: `content ""; height 4px; position
  sticky; top 0; z-index 2; margin 0 0 -4px; background <panel colour>;
  opacity 0 -> 1; transition opacity .2s`. Solid, not a gradient: a 4px band of
  the panel's own colour that switches on once the region scrolls, holding a
  clean gap between the header and the sliced content. Ours now matches it field
  for field. GitLab drives it from a `scroll-state` container query, which only
  Chrome supports; a scroll listener does the same everywhere.
- **The line above the sidebar's bottom group is gone.** GitLab draws no divider
  there.

## [2026.7.3.post164] - 2026-08-11

The top bar reads as one row again. No migration.

### Fixed
- **One item in the header was off the rhythm.** Measured on
  gitlab.example.com, every top-bar item is a 32px box centred on the bar's 24px
  midline at 14px text. Ours matched that everywhere except the academic-year /
  clock chip, which sat at 18px and 12px - the "one thing bigger than another"
  look. It is a 32px, 14px item now, and the brand text drops 16px -> 14px so
  nothing in the bar is a different size from the row it lives in.
- **The brand mark is anchored to GitLab's width, not its height.** GitLab's
  tanuki is near-square (25x24) and fills its box; ours is wide-format with ink
  spanning 44x36 of a 48-unit viewBox, so matching the 24px HEIGHT drew a 29px
  wide mark - the heaviest object in the bar. A 27px box puts the ink at
  25x20: GitLab's width exactly, and under the 32px control rhythm.
- **The logo hover is a wash, not a flash.** `brightness(1.42) saturate(0.55)`
  blew the mark out on contact; 1.18/0.85 lifts it toward a lighter tint of its
  own colour, which is what GitLab's per-part fill change actually looks like.

## [2026.7.3.post163] - 2026-08-11

The cut under the breadcrumb finally appears, because the dead band above the
content is gone. No migration.

### Fixed
- **The brand mark was drawing at 18px next to GitLab's 24px.** Our artwork only
  spans 36 of its 48 viewBox units vertically, so a 24px box rendered a 24 * 0.75
  = 18px mark. The box is 32px now, which puts exactly 24px of visible logo in
  the bar. The top bar's gap also moves 12px -> 16px, GitLab's measured value.
- **Logo hover no longer flickers.** The highlight was bound to each shape's own
  `:hover`, so only the piece under the cursor lit up and crossing a seam between
  two overlapping shapes flipped between them. Hovering the logo now lights the
  whole mark at once - 0.1s in, 0.8s back, colour only.

- **Content is flush with the top of its scroll region, as GitLab's is.**
  Measured on gitlab.example.com: `.panel-content-inner` and its first child
  both report `padding-top: 0`, so the first pixel of scroll already slides
  content under the header. Ours held 40px of empty space there - 24px of
  `.main-container` padding plus 16px on the dashboard greeting - so a scroll had
  to consume that band before anything was visibly cut. On a page whose content
  only overflows by ~540px that band is most of what a user scrolls through,
  which is why the cut under the crumb row never showed up.

## [2026.7.3.post162] - 2026-08-11

The darkening under the breadcrumb is gone, feedback stops skipping every second
press, and a stray brace that had been disabling half a stylesheet on production
is fixed. No migration.

### Fixed
- **A stray `}` in animations.css shipped in post160.** Removing the modal
  slide-down keyframe left one closing brace behind, and a browser drops every
  rule after a syntax error - so everything below `modalSlideUp` in that file was
  inert on production. Found by balancing braces across all 42 stylesheets;
  `test_every_stylesheet_has_balanced_braces` now guards it, because nothing else
  did: the bundle gate only compares concatenation and the minifier passes the
  damage straight through.
- **No more darkening at the top of the content on scroll.** GitLab's
  `.panel-content-inner` has no scrim at all - `.gl-scroll-scrim` is an opt-in
  component and only its sidebar, dropdowns, drawers and search results carry it.
  The cut under the crumb row is the opaque 36px header block, nothing more. Our
  gradient and its scroll listener are both deleted.
- **Feedback no longer skips every second press.** The toast deduplicator
  suppresses an identical message for 5s, which is right for a burst from one
  operation and wrong for a second deliberate press of Refresh - the user saw
  nothing at all. A new press now clears the dedup slate, and a suppressed toast
  still hands the button its done state.
- **The done state now reaches every button.** It was wired to the shared
  `[data-action]` runner, but Refresh, Sync and many others bind their own
  handlers and never go through it. A single capture-phase listener records the
  pressed control instead, so completion is reported wherever the user clicked.

## [2026.7.3.post161] - 2026-08-11

A third state for every action, and the page stops refreshing itself after you
refresh it. No migration.

### Added
- **A done state on the control you pressed.** Every action shipped two states
  and owed three: loading, then a toast. The toast says the SYSTEM did
  something - it never said THIS BUTTON finished. The button that started an
  operation now turns green with a check and "Done" for 1.6s before returning to
  its label. One mechanism, no per-call-site opt-in: the shared action runner
  remembers which control started the operation and the success toast - the
  signal every finished action already emits - hands it its done state.

### Fixed
- **A manual refresh no longer refreshes a second time.** When a deploy ships a
  new service worker it claims the tab and fires `controllerchange`, and we
  reloaded unconditionally - so a page the user had JUST loaded reloaded again a
  moment later. A fresh navigation is never stale (its HTML already points at
  the new content-hashed assets), so the reload now only happens for a tab that
  was already open when the deploy landed.

## [2026.7.3.post160] - 2026-08-11

Motion measured off the university's own GitLab instead of guessed at, and stat
cards that say what their number means. No migration.

### Changed
- **Dropdowns no longer fade or scale.** Measured on gitlab.example.com: the
  panel is fully opaque on the first frame after the click and goes
  `display: none` 2ms after the dismiss - GitLab animates nothing in either
  direction. Ours scaled 0.94 -> 1 and faded over 100ms both ways.
- **Every exit uses GitLab's ease-out.** `--motion-ease-exit` was
  `cubic-bezier(0.4, 0, 1, 1)`, an ease-IN we invented: it holds an element at
  full opacity for the first third of its duration, which is what read as a slow
  fade-out. GitLab's modal dismiss measures
  `opacity 0.2s cubic-bezier(0.22, 0.61, 0.36, 1)` - 57% gone at 7ms, 99% at
  73ms - so the token is now an alias of `--motion-ease-standard`, the same
  curve. Applies to modals, drawers, banners, alerts and the tour at once.
- **A dismissed modal no longer slides.** GitLab fades it and leaves
  `transform: none` throughout; the 200ms slide-down keyframe is gone.
- **The panel header is GitLab's 36px block.** Flush with the panel's top edge,
  rounded 8px on its top corners, 8px above the crumb row and 4px below - the
  same geometry, but the header owns the strip instead of leaking margins.
- **The content panel sits flush against the sidebar.** GitLab measures
  `.paneled-view` at x=240 with a 240px sidebar; our extra 8px gutter made the
  content column 8px narrower than GitLab's on every screen.
- **Dashboard stat cards carry a state.** Compliance is toned by the same bands
  the course traffic lights use (red under 50, amber under 75), and a zero with
  nothing behind it reads as empty rather than as a real result. The live poll
  ships the state with the number, so a card can never stay green over a score
  that just fell into the red.

### Fixed
- **Chart reveals no longer fight their skeletons.** The hand-off always ran a
  cross-fade, including when the skeleton was still inside its reveal delay and
  had never painted - fading OUT something at opacity 0 while fading IN the
  chart. It now hands off in a single frame when the skeleton was never seen,
  and a skeleton that IS on screen is guaranteed 400ms before it is replaced.
  Verified on the admin System and course Analytics pages: zero frames with both
  elements mid-fade.

## [2026.7.3.post159] - 2026-08-11

The scroll scrim actually works now, plus two things measured off the instance.
No migration.

### Fixed
- **The scrim shipped in post158 never appeared for anyone.** Its opacity was
  driven by `animation-timeline: scroll()`, which needs Chrome 115+; everywhere
  else the rule was simply ignored and the notch silently did not exist. It is
  now driven by an `.is-scrolled` class from a passive, rAF-throttled scroll
  listener - the same approach GitLab uses - so it works regardless of browser.
  Verified with a real wheel scroll: class off and opacity 0 at the top, class
  on and opacity 1 once scrolled.
- **Breadcrumb links did the opposite of GitLab's on hover.** Measured on the
  instance: idle `text-decoration: none` -> hover `underline`, with the colour
  unchanged at `rgb(191,191,195)`. Ours changed the colour and explicitly
  suppressed the underline.
- **Role chips read cramped against their own edges.** They render at
  `size='sm'`, and `.badge-sm` squeezed the horizontal padding to 4px. GitLab
  ships one badge metric - 2px/6px for every variant and size - so `.badge-sm`
  no longer carries a metric of its own.

## [2026.7.3.post158] - 2026-08-11

The scroll scrim under the breadcrumb row. No migration.

### Added
- **The notch that appears when content scrolls under the breadcrumb.** Taken
  from the instance's own stylesheet: `.gl-scroll-scrim .top-scrim-wrapper` is a
  36px sticky strip pinned to the top of the scroll region with
  `margin-bottom: -2.25rem` so it occupies no space, `opacity: 0` at rest, and a
  `linear-gradient(180deg, alpha-dark-8, transparent)` fill - `alpha-dark-24` on
  dark. It fades in once there is content above the fold, which is the soft
  separation visible between the crumb row and the scrolled content.
  Reproduced on `.gl-page-content::before` with the same 36px, the same
  gradients from our existing `--alpha-dark-8` / `--alpha-dark-24` tokens, and
  the opacity driven by a scroll-linked animation rather than a scroll handler,
  so it costs the main thread nothing. Verified: 36px tall, opacity 0 at the top
  and 1 once scrolled.

## [2026.7.3.post157] - 2026-08-11

Verified against the university's own GitLab instance, not gitlab.com by proxy.
No migration.

### Changed
- **The reference is now `gitlab.example.com` itself.** Its `/explore` pages
  are reachable without signing in, so every number below comes from the exact
  build this project is compared against. That check confirmed the shell work
  outright - top bar 48px, sidebar 240px, panel radius 12px, nav item 28px at
  8px radius, search 344x32 at 12px radius and dark background `rgb(40,39,45)`
  all already matched - and surfaced five things that did not:
 - button labels sit on a **16px line**; ours used `line-height: 1` (14px),
    which is why the same 32px button read tighter than GitLab's
 - the top-bar search trigger inherited the 1.5 body line (21px) instead of 16px
 - the dashboard greeting was weight 500; GitLab sets headings at **600**
 - badges are exactly **20px** tall and must not compress in a flex row
 - breadcrumb links carry a 4px radius on their focus target
 - the scrolling region starts **4px below** the crumb row, leaving a strip of
    panel background between them - the notch that becomes visible once the page
    scrolls and content slides under the row. Ours started it flush at 80px, so
    the notch never appeared.

### Notes
- Avatars were already right: users are circles (32px button around a 24px
  image, as in the top bar) and projects/groups are squares at a 4px radius,
  which is exactly how the instance renders them.
- A badge measuring 19px turned out to be an artifact - the sampled chip lives
  inside a closed dropdown, and the closed state carries `scale(0.94)`:
  20 x 0.94 = 18.8. Visible badges measure 20px.

## [2026.7.3.post156] - 2026-08-11

Three things the breadcrumb, the palette and the search trigger were each
getting wrong. No migration.

### Fixed
- **The breadcrumb was wrong in four ways at once.** Its root was a fixed
  "Dashboard", so on the dashboard itself it read "Dashboard > Dashboard" - the
  same word twice. It separated crumbs with a chevron icon, ran at 14px, and
  sat in an `overflow: hidden` row that clipped descenders along the bottom.
  Measured on gitlab.com: crumbs are **12px on a 16px line** in a 24px row with
  **`overflow: visible`**, the separator is the **character "/"** rather than an
  icon, only the current page is at weight 600, and the root is the section the
  page lives in ("Your work / Home"). All four now match: the root is the
  sidebar section - Your work, Teaching or Administration - so the page name
  can never repeat it, and the row reads "Vaša práca / **Prehľad**".
- **The filter rail jumped and flickered on every keystroke in the search
  palette.** `.gl-search-modal-body:empty` removed the results column with
  `display: none`, which took its `flex: 1` out of the row, so the 220px filter
  panel snapped to the left edge and back whenever a render briefly emptied the
  list. The column now stays in the layout and only drops its padding.
  Verified while typing: the panel holds x=883 through every keystroke.

### Changed
- **The search trigger's hover is GitLab's.** Measured on gitlab.com: hovering
  darkens the border from `rgba(5,5,6,0.24)` to `rgba(5,5,6,0.4)` over the
  standard 0.2s out-cubic, and nothing else changes - the fill and label stay
  put. Ours also swapped the background, a heavier state change than GitLab's.
  Both themes verified: 0.24 -> 0.4 on light, 0.16 -> 0.4 on dark.

## [2026.7.3.post155] - 2026-08-11

The type scale drops two sizes GitLab does not have, and the logo gets GitLab's
actual hover behaviour. No migration.

### Fixed
- **The interface read smaller than GitLab's, and the numbers say why.**
  Counting every visible element at 1920: GitLab uses 14px (1458 elements),
  21px (40), 12px (34), 30px (4) - and **13px and 11px exactly zero times**.
  Ours put 88 elements on 13px, 12 on 11px and 37 on 11.375px (an `em`-relative
  inline `code` rule). `--font-size-sm` is now 14px, `--font-size-xs` is 12px,
  the last three hardcoded 11px rules use the 12px token, and inline `code`
  renders at body size the way gitlab.com does. Every size on screen is now one
  GitLab actually uses.
- **The logo's hover behaviour was wrong in both directions.** post151 removed a
  perpetual glow, and post154 made the mark completely static - but measuring
  only the `<a>` and its outer `<svg>` missed where GitLab's animation actually
  lives. Its tanuki is built from named parts (`.tanuki`, `.left-cheek`,
  `.chin`, `.right-cheek`) and each transitions its **fill**: 0.8s at rest,
  dropping to 0.1s while lit, so a piece flares fast under the cursor and fades
  back slowly - the main shape goes `rgb(226,67,41)` -> `rgb(241,166,153)`.
  Nothing moves. Our mark is built from parts too, so it now behaves the same
  way, and the lift/scale/drop-shadow it used to do on hover is gone.

## [2026.7.3.post154] - 2026-08-11

Loading states stop flashing, and the shell chrome is measured against GitLab
rather than approximated. No migration.

### Fixed
- **Skeletons flashed and vanished before they could be read.** The mechanism
  that holds a placeholder invisible until a load is genuinely slow existed,
  but applied only to `.gl-skeleton` - the composite skeletons (table rows, the
  horizontal-bar chart, the chart wrap, the health dashboard) are separate
  classes and painted instantly. Measured on admin System: 447ms of visible
  life for the table, 512ms for the chart, 933ms for health, each a blink
  rather than feedback. Every skeleton root now shares the delayed reveal, and
  the threshold moved from 250ms to **400ms** (the System table lands at
  ~360ms, which used to leave a ~110ms flash). Verified with ancestor-aware
  opacity sampling: the table and chart skeletons now reach a peak opacity of
  **0.00** - they never paint at all on a fast load - while the health panel,
  which really does take ~900ms, shows in full. No flashes remain on the
  dashboard, courses, course settings (webhooks), activity, analytics, team,
  users or System.
- **The error pages had drifted off the design system.** Their own
  `--err-radius` still aliased the generic 4px, so inputs and buttons there
  were visibly squarer than the identical controls everywhere else; the
  heading was 26px against GitLab's 40px; the search field was 39px tall
  against the app's 32px; and links used the raw brand blue instead of the
  app's link colour. All four now follow the same tokens as the rest of the
  app, in both themes.

### Changed
- **Modal motion is GitLab's.** Measured on an open GitLab modal: the overlay
  fades with `opacity 0.15s linear` and the dialog travels from 50px above on
  `transform 0.3s ease-out`. Ours faded in 100ms and grew from `scale(0.85)`
  on a spring over 400ms - a different motion entirely. The backdrop dim was
  already right at `rgba(5, 5, 6, 0.24)`.
- **The top-bar search grows with the viewport, as GitLab's does.** Measured at
  five widths - 261px at 1024, 312 at 1280, 344 at 1440, 392 at 1680, 440 at
  1920 - which is exactly `20vw + 56px`. Ours was pinned at 344px and looked
  stunted on a wide screen. Now identical at all five, and still centred on the
  viewport rather than on the leftover space.
- **The logo is static, like GitLab's.** Idle and hover on gitlab.com are
  identical - same transform, opacity, filter and background, nothing moves.
  Ours ran a heartbeat on hover (centre, ears and cheeks each on their own
  0.95s spring) on top of the perpetual glow removed in post151. Both are gone,
  along with the three keyframes that became orphans.

## [2026.7.3.post153] - 2026-08-11

Toasts round like every other overlay. No migration.

### Changed
- Toasts rounded at 4px while every other overlay we round now sits at 8px
  (GitLab's toast measures an 8px radius over 16px/24px padding, which we
  already matched). The surface and the small controls inside it now use the
  same tokens as dropdowns and actions.

### Known difference
- GitLab's toast is a **neutral dark chip** (`#3a383f`) in both themes; ours is
  tinted per variant. That is a deliberate difference in this app - the toast
  carries success/warning/danger meaning - and is left as is rather than
  changed silently.

## [2026.7.3.post152] - 2026-08-11

One dropdown controller instead of two. No migration.

### Removed
- **The second dropdown controller.** `.gl-dropdown` was driven by a handler in
  `core/20-ui-helpers.js` while `[data-dropdown]` was driven by
  `dropdowns.js` - two implementations of one interaction, each carrying a
  `_isAlpineManaged`-style check for the other so their `.open` state would not
  desync. That coupling was itself the warning sign: when it broke, a menu
  opened once and then reported itself permanently closed. `dropdowns.js` now
  owns **both** selector conventions, so not a line of markup changed, and the
  76-line handler in core is gone.
- The two behaviours that only the deleted handler had moved across: choosing
  an item closes its menu, and a menu portaled to `<body>` (the page-size
  selector, moved there to escape `overflow: hidden`) is never treated as an
  outside click. Alpine-managed dropdowns are still skipped - Alpine owns their
  `.open` through `:class` and a second writer would fight it.

### Added
- `tests/unit/test_one_controller_per_interaction.py` pins both merges - the
  single click guard and the single dropdown controller - and the behaviours
  each absorbed. Verified in the browser first: 12 dropdowns across five pages
  open and close with correct `.open`, `aria-expanded` and visibility; the
  portaled page-size menu opens, selects and closes; and the theme switcher
  inside the user menu leaves it open, which is the bug the split originally
  caused.

## [2026.7.3.post151] - 2026-08-11

Motion matched to GitLab's, not just its speed. No migration.

### Changed
- **GitLab animates colour and nothing else.** Measured on real Pajamas
  components: a button transitions `color, background-color, border-color,
  box-shadow, text-decoration-color` at 0.2s out-cubic and **no transform**;
  cards, links, alerts and checkboxes transition nothing at all. Ours scaled
  buttons down to 0.94 on press, scaled sidebar items to 0.98, and zoomed nav
  icons to 1.1 on hover. Matching the durations in post147 was only half the
  job - the movement itself is the tell, the way a 2px radius was in shape.
  All three removed; the button's property list is now GitLab's exactly.
- **Form controls animate on a different pair.** GitLab moves `border-color,
  box-shadow` over **0.15s ease-in-out** on a GlFormInput, not the 0.2s
  out-cubic every action uses. Added `--transition-control` and pointed the
  text input, select, dropdown toggle, checkbox, toggle track and search box
  at it.

### Removed
- The reduced-motion override that reset `.btn:active { transform }`, dead now
  that the press carries no transform.

## [2026.7.3.post150] - 2026-08-11

The application shell rebuilt to GitLab's, and the second click guard deleted.
No migration.

### Changed
- **The shell itself was the wrong shape.** GitLab's super-topbar spans the
  FULL width at the top (measured 0,0,1440x48 on gitlab.com) and the sidebar
  starts below it; ours put the sidebar full-height on the left with a bar only
  over the content, so the page read as "a sidebar with a bar next to it"
  instead of "a bar over everything" - the difference visible before any
  component. The bar is now full width with the brand top-left where GitLab
  keeps it, the sidebar sits below it, and the sidebar's own brand header is
  hidden on desktop (the mobile drawer keeps it). Verified against GitLab at
  three widths in both themes: topbar (0,0,1440,48), sidebar (0,48,240), panel
  radius 12px, nav item 28px with 2px/4px padding, page title 30px - all exact.
- Content panel radius 16px -> 12px, top bar 49px -> 48px, page `h1` 24px ->
  30px, sidebar nav items 0/8px -> 2px/4px padding with a 2px gap, and the
  sidebar's bottom group 13px -> 14px so it matches the nav items right above
  it. Every one of those is a measured GitLab value.

### Removed
- **The second click rate guard.** `interceptSpamClicks` in
  `process-action-guards.js` counted 3 clicks in 2s and applied a visible
  cooldown, duplicating the silent per-element debounce in
  `core/20-ui-helpers.js`. Two guards over one interaction is one too many, and
  they disagreed: a tree toggle survived the lock and died on the cooldown.
  Deleted, along with its per-element timestamp map. The cooldown machinery
  stays - but only as something a *failed action* applies on purpose via
  `GP.applyCooldown`. Verified with six real rapid clicks: perfect alternation,
  no dead click, no cooldown.
- The top bar's `left` offset for the collapsed sidebar and its `transition:
  left`, both dead now that the bar spans the full width in every state.

## [2026.7.3.post149] - 2026-08-11

Tabs, badges and menus measured against the Pajamas components themselves.
No migration.

### Changed
- **Tabs were a step small and never fully selected.** design.gitlab.com's
  GlTabs measures 50px tall, 14px text on a 16px line, 16px/12px padding, and
  keeps every tab the SAME colour - GitLab marks the selection with weight
  (400 -> 600) and the indicator, nothing else. Ours were 13px at weight 500 in
  both states over 8px/16px padding with the inactive ones dimmed, so the bar
  sat 12px shorter and every tab read half-selected. Now identical: 50px,
  14px/16px, 16px/12px, 400 inactive and 600 active.
- **Small badges were heavier and taller than any GitLab badge.** Every variant
  on design.gitlab.com/components/badge measures 12px / weight 400 / 2px 6px /
  20px tall - GitLab ships one badge metric. `.badge-sm` bumped the weight to
  500 and the vertical padding to 3px; it now only trims the horizontal
  padding.
- **Menus rendered a step below the page behind them.** GitLab draws the
  dropdown toggle and its items at 14px, the same as body text; ours were 13px.
- The current page number in a paginator rounded at 4px while the prev/next
  buttons either side of it round at 8px, so the number read visibly squarer
  than its own arrows.

## [2026.7.3.post148] - 2026-08-11

Docs typography matched to docs.gitlab.com, and the last hand-written inline
styles are gone. No migration.

### Changed
- **The documentation ran a whole heading step small.** Measured on a
  docs.gitlab.com content page: h1 40px/46px, h2 32px/40px, h3 24px/30px,
  inline code and code blocks both a flat 14px. Ours were 32 / 25 / 21 with
  code at 12.24px inline and 13.6px in blocks - both `em`-relative, so they
  compounded against their container instead of landing on a fixed size. Body
  copy was already 16px/25.6px and stayed. Re-measured after the change: p, h1,
  h2, h3, inline code and code blocks are now identical on both sites.
- The 8px radius on code blocks is correct after all: GitLab puts it on a
  `.codeblock-wrapper` and leaves `<pre>` itself square and transparent, so
  measuring `<pre>` alone read 0px. We have no separate wrapper, so ours keeps
  the radius on `.highlight` / `pre`.

### Removed
- **The last inline styles that were really CSS.** `width: 100%` on the user
  dropdown info block and `vertical-align: middle` on the student commits
  counter moved into `dropdowns.css` and a shared `.match-count` rule - the
  same counter previously sat on a different baseline on the course page,
  which had no such rule. Project detail's live-intel skeleton stopped
  hand-writing `height/width/margin/border-radius` and now uses the same
  `--sk-w` custom-property API as every other skeleton, plus two shared classes
  (`.gl-skeleton-row`, `.gl-skeleton-gap`) that replace the private 6px / 8px
  margins in the user-info modal.
- Every `style` attribute left in the codebase now passes a *value* a class
  cannot carry (`--sk-w`, `--chart-h`, `--h-bar-label-w`), which is the
  intended pattern; none declare properties directly.

## [2026.7.3.post147] - 2026-08-11

Component radii, motion and the group tree measured against GitLab instead of
recalled. No migration.

### Fixed
- **Expanding a group dumped every project row at once.** GitLab's group tree
  shows the first few children and puts the rest behind "View all (N more
  items)"; ours rendered all 15 at once and pushed everything below off the
  screen. An expanded group now shows 3 children plus that link. The cap lives
  in the template, which stamps `.tree-row-extra` on the rows past it - the
  client paints by class and holds no copy of the number, so the two cannot
  drift apart. Verified in the browser in both themes, including that the cap
  survives filtering and pagination re-renders.
- **Three clicks on any disclosure toggle within two seconds froze it.**
  `interceptSpamClicks` in `process-action-guards.js` treated a tree toggle as a
  real operation and applied the anti-spam cooldown, so expand/collapse/expand
  left the control dead. Disclosure controls (`aria-expanded` / `aria-pressed`)
  issue no request; both click guards now exempt them, the way the click lock in
  `core/20-ui-helpers.js` already did. Buttons that carry
  `data-process-lock-when` are still rate-limited.

### Changed
- **Every component radius was wrong.** GitLab does not use one radius
  everywhere, and picking the generic 4px for buttons and inputs is what made
  our controls read as visibly squarer than GitLab's in side-by-side
  screenshots. Measured live - button 8px and nav item 8px on gitlab.com, input
  8px, card 12px and alert 8px on design.gitlab.com - and reproduced through
  named tokens taken from `@gitlab/ui` 136.1.0: `--gl-action-border-radius`,
  `--gl-control-border-radius`, `--gl-card-border-radius`,
  `--gl-modal-border-radius`, `--gl-dropdown-border-radius`,
  `--gl-alert-border-radius`. Buttons and form controls 4px -> 8px, cards
  8px -> 12px, modals 12px -> 16px (the code claimed `gl-border-radius-2xl`,
  which is 16px, and used 12px anyway).
- **Animations ran half again too slow.** `@gitlab/ui` publishes
  `$gl-transition-duration-fast: 0.1s`, `-medium: 0.2s`, `-slow: 0.4s`, and
  measuring gitlab.com with reduced motion explicitly off shows only 0.1s /
  0.15s / 0.2s in use. We ran at 200ms / 290ms / 500ms, so every hover, reveal
  and state change took longer than the same interaction in GitLab. Aligned to
  100 / 200 / 400ms.
- **Body line-height 1.4 -> 1.5.** GitLab sets 14px text on a 21px line;
  ours was 19.6px, which made every paragraph, table cell and card denser than
  the same content in GitLab.
- **Table headers 13px over a 2px border -> 14px over 1px**, measured on the
  real Pajamas table component rather than a markdown table (which renders at
  700 and would have been the wrong thing to copy).

### Added
- `tests/unit/test_tree_disclosure_contract.py` pins the cap markup, the
  class-driven client contract, and the disclosure exemption in both click
  guards.

## [2026.7.3.post146] - 2026-08-10

Badges match live GitLab, measured with a real extraction rather than recall.
No migration.

### Changed
- **Badges were the wrong colour in both themes.** Extracting live gitlab.com
  with Dembrandt showed a neutral badge computes to background `#dcdcde` with
  text `#4c4b51`, and a success badge to `#c3e6cd` / `#306440` - GitLab's
  `--gl-status-*` pair, i.e. a **muted** chip. Ours were a bright 300-level chip
  with near-black text on dark, and one step too dark on light. Every variant
  now follows GitLab: `*-100` background with `*-700` text on light, `*-800`
  with `*-200` on dark. Verified in the browser: our success badge now computes
  to exactly `rgb(195, 230, 205) / rgb(48, 100, 64)`, the same values the
  extraction read off gitlab.com. Badge line-height is pinned to GitLab's 16px.
- The documentation site uses an 8px radius for its interactive chrome. The
  extraction counted 8px on 52 elements there - search box, buttons,
  comboboxes, cards - against 14 for 4px, which is reserved for inline code and
  labels. The product UI stays at 4px; the docs site is deliberately softer, and
  post144 had flattened both to 4px on an assumption.

### Removed
- **`pages/admin.css` redefined `.badge-gray`.** It overrode the shared badge
  component with surface/text colours on admin pages only, so the same status
  chip had two different colours depending on which page you were on, and
  neither matched GitLab. Deleted; the shared token now applies everywhere.

### Added
- Badge tokens joined `tests/unit/test_gitlab_token_parity.py` (25 -> 35 pinned
  values), with the live-extraction hexes recorded in the test.

## [2026.7.3.post145] - 2026-08-10

"Show more" became a shared component. No migration.

### Changed
- **"Show more / show less" is one component instead of a feed-only feature.**
  The disclosure lived entirely inside the dashboard activity feed: its own
  classes, its own footer markup, its rules buried in `home.css`. Any other list
  wanting the same behaviour would have had to copy all three. It is now
  `components/disclosure.html` plus generic `.gl-show-more*` rules in
  `utilities.css`, and the feed calls the macro. The contract covers table rows
  too - `display: none` on a `<tr>` is legal, so a `<div data-show-more>` around
  a table can hide overflow rows the same way.
  Verified in the browser: 0 extra rows -> 5 on expand -> 0 on collapse, no
  console errors.

### Removed
- The activity-feed-specific `.gl-activity-item--extra` /
  `.gl-activity-show-more*` classes and the duplicated expand/collapse markup,
  plus an import the change orphaned.

## [2026.7.3.post144] - 2026-08-10

Buttons, checkboxes and selected states now carry GitLab's real colours; the
documentation site and the empty states follow. No migration.

### Changed
- **The primary button is no longer blue.** GitLab's own design tokens paint the
  confirm/primary button `neutral-800` on light and `neutral-50` on dark - blue
  is reserved for links, focus rings and info. The app had it blue, which is the
  single biggest reason screenshots never matched. Checked checkboxes and radios,
  the toggle track, the selected filter pill, the current pagination page and the
  selected navigation item move to the same neutral ramp, because GitLab paints
  all of them from `--gl-action-selected-*`. Values were taken from
  `@gitlab/ui` 136.1.0, resolved to hex and verified in a browser in both themes:
  **14 measurements, 0 mismatches.**
- The check mark inside a checkbox, the radio dot and the toggle knob now follow
  the theme instead of being hardcoded white. They had to: the checked control is
  near-white in dark mode, so a white glyph would have been invisible.
- **Every empty state leads with a GitLab illustration.** 37 of them showed a
  boxed glyph; they now inline the matching illustration from `@gitlab/svgs`
  (MIT, 15 vendored). The SVGs are inlined rather than linked because they colour
  themselves from `--gl-illustration-*`, which an `<img>` could never read.
- **The documentation site was rewritten onto GitLab's design language.** It ran
  on Material's indigo/deep-purple defaults with gradient table headers, uppercase
  letter-spaced column titles, 8-12px radii, drop shadows and cards that lifted on
  hover. It is now GitLab: neutral chrome separated by hairlines, 4px radii,
  text-coloured headings, plain tables and the same GitLab Sans/Mono the product
  uses. The Material palette is set to `custom` so the theme can no longer
  reintroduce its own hues.
- Error pages, the product tour, the PWA install prompt and the sign-in button
  stopped defining their own primary colour and use the shared button tokens.
  Four private definitions of "the primary button" is four chances to drift.
- Skeleton placeholders use GitLab's 4px corner radius instead of 2px, and the
  chart skeleton was moved onto the same composited sweep as every other
  skeleton. There were two shimmer mechanisms; the second one animated
  `background-position`, which the compositor cannot run on its own, so it stalled
  under exactly the main-thread load it was reporting on.
- Destructive icon-only row actions render as tertiary danger - a red glyph that
  picks up a red wash on hover - instead of a solid red block shouting over a
  table row, matching GitLab's row actions.

### Added
- `tests/unit/test_gitlab_token_parity.py` pins 25 interactive colour tokens to
  `@gitlab/ui` 136.1.0 in both themes. Nothing else in the suite would have
  noticed them drifting back to blue.

### Removed
- A `.gl-skeleton` animation declaration that a later rule already overrode, its
  stale comment, a duplicated keyframe comment, the now-unused
  `--gl-toggle-unchecked-hover` token and the second skeleton keyframe.

## [2026.7.3.post143] - 2026-08-10

The activity feed is laid out like GitLab's. No migration.

### Changed
- **"Follow the latest updates" follows GitLab's Activity layout.** A row was one
  flat `Actor - Action` string beside an icon, which read as a log line. It is
  now an avatar, the actor in bold with the time pushed to the right, the action
  on its own line with its icon, and the detail beneath - the shape GitLab uses.
  The builder emits `actor` and `action` as separate fields instead of one
  pre-joined string, which could not be split back apart once a name contained
  " - ".
- The linked and unlinked row variants share one macro. They previously carried
  duplicated markup that could drift apart.

### Fixed
- **An activity row showed a question mark instead of an icon.** The feed asked
  for `user-x`, which the icon set does not define, so the member-scoring row
  rendered the fallback glyph. It uses `user-minus` now, and a new test asserts
  every icon the feed names actually exists - the only thing that would catch a
  silent fallback.

## [2026.7.3.post142] - 2026-08-10

The last browser dialogs are gone, and a dropdown can no longer cut its own
options. No migration.

### Changed
- **Every remaining `window.confirm` now runs on the app's dialog.** Twelve call
  sites across nine files still asked through the browser - cancelling a job, a
  sync, an import or an AI run, rotating a webhook secret, deleting a week,
  changing course identity or the semester window. Six of them sat in
  synchronous helpers whose boolean the caller used, so those helpers
  (`confirmProcessRestart` with five call sites, `cancelActiveLLMGeneration`,
  `cancelActiveImport`, the weekly-deadline handler) became async and their
  callers now await them. Verified by clicking 117 buttons across nine pages:
  **zero native dialogs**. The only `window.confirm` left is the deliberate
  fallback inside the shared dialog, for pages that do not render it.

### Fixed
- **A dropdown clipped its own options.** The menu was capped at 320px with no
  wrapping, so a long, unbreakable label - a branch name like
  `kyryl_ticket_num_2...` - ran past the edge and the menu grew a horizontal
  scrollbar. Menus now size to their content (`width: max-content`), never
  narrower than the control that opened them and never wider than the viewport,
  and long labels wrap instead of being cut. Fixed in the shared component, so
  it holds for every dropdown in the app rather than the one that was reported.

## [2026.7.3.post141] - 2026-08-10

Every dropdown says when it has nothing to offer. No migration.

### Fixed
- **A select with no options rendered as a blank box.** Opening "Import Target"
  with no courses yet showed an empty rectangle, which reads as broken rather
  than "there is nothing to pick". The shared `select_field` macro now renders
  "No options available", so every dropdown in the app gained the empty state at
  once instead of each caller inventing its own.

## [2026.7.3.post140] - 2026-08-10

Sorting answers on the first click, and the health check says what it found.
No migration.

### Fixed
- **Sorting a table appeared to need two clicks.** Switching to a new column
  sorts it ascending, which very often reproduces the order already on screen -
  courses sorted by name land in the same sequence as by code - so the rows sat
  still and only the arrow moved. It read as "the first click just focused the
  header". When the new column's default direction changes nothing, the
  direction now flips immediately, so one click always produces a visible
  result. Only on a column SWITCH: clicking the same header again must still be
  free to put the table back the way it was.
- **The System Health check gave no feedback.** On a healthy system the re-check
  redraws an identical card, so nothing confirmed it had run. It now reports the
  verdict - operational, degraded or unavailable - as a toast, the same contract
  every other action follows.

## [2026.7.3.post139] - 2026-08-10

The whole icon set is GitLab's now. No migration.

### Changed
- **Every icon is a GitLab Pajamas glyph.** The app shipped 122 hand-inlined
  *Feather* icons - 24x24, stroked outlines - which is a different icon family
  from GitLab's, so no amount of colour or size tuning could make the UI read as
  GitLab. All 122 are replaced by their Pajamas counterparts from `@gitlab/svgs`
  (MIT): filled shapes, mostly on a 16-unit grid. 47 names matched directly; the
  other 75 were mapped by meaning and the mapping is recorded in the generator.
- Both registries moved together - the Jinja macro (`components/icons.html`) and
  the JS one (`static/js/icons.js`) - so a server-rendered icon and one drawn by
  JS are the same glyph.
- Icons inherit the text colour through `fill: currentColor` (Pajamas shapes
  carry no fill of their own), replacing the `stroke: currentColor` the outline
  set relied on. Verified in both themes.
- Paths are inlined rather than referenced from a sprite: WebKit still does not
  resolve EXTERNAL `<use href="sprite.svg#id">`, which would have left every
  icon blank in Safari.

## [2026.7.3.post138] - 2026-08-10

Replaying events moves out of a modal and into the events table. No migration.

### Changed
- **Replay is a table action now, not a dialog.** The modal asked for a start
  and an end date: it named the events only indirectly, swept in everything else
  that fell inside that window, and its own selects were clipped by the dialog.
  The Recent events table gains a select column and a "Replay selected (N)"
  action - the same selection pattern the dead-letter table already used, so the
  two tabs finally behave alike. The modal is deleted.
- `POST /api/v1/events/replay` accepts `event_ids`, replaying exactly the rows
  that were ticked. The time-range form still works for API callers; the schema
  now requires one or the other.
- Confirmation runs on the shared dialog and states the real count ("Re-process
  2 selected events?"), which a date range could never do.

## [2026.7.3.post137] - 2026-08-10

Every "are you sure?" in the app is now the app's own dialog. No migration.

### Changed
- **Destructive actions asked through the browser.** `window.confirm` /
  `window.prompt` sat next to the app's own modals doing the same job - two
  patterns for one interaction, and the browser's half cannot be themed, ignores
  dark mode, carries no danger accent and reads as if the page broke. One shared
  dialog (`GP.confirmDialog`, markup in base.html) now serves every confirmation:
  themed, translated, Escape-cancellable, focus on the SAFE button so Enter
  cannot delete, and it opens and closes through the app's existing
  `openModal`/`closeModal` - not a second show/hide of its own.
- `confirmDangerousAction` keeps its signature: callers pass a callback, so
  moving from a blocking dialog to a promise ripples nowhere. All 16 call sites
  were verified to use the callback form.
- **Two confirmations became one.** A permanent delete used to need a second
  dialog because a browser prompt could only ask yes/no. The dialog states the
  consequence once and gates its button on typing the name - the safeguard the
  extra click only imitated.

## [2026.7.3.post136] - 2026-08-10

One mechanism for the archived read-only state instead of two, and the dead CSS
that survived removed features. No migration.

### Changed
- **The archived lock is expressed once.** Eleven button call sites also
  server-rendered `disabled` + a hover reason for a state the client guard
  already owns, so the same condition existed twice and behaved differently
  depending on which won - a disabled button that swallows the click next to a
  guarded one that answers with a toast. The server-side copy is gone; every
  locked control now behaves the same way.

### Removed
- Dead template variables the duplication left behind (`_lock_tip`, `_locked`)
  and `_repo_is_empty`, a Run Checks condition hardcoded to `false` that could
  never fire.
- Nine CSS rules for classes no HTML or JS emits any more - column widths for a
  members table that changed shape, skeletons for charts that no longer have
  one, and a placeholder avatar. Verified individually; the compound-selector
  candidates were left alone deliberately (a substring match has broken this
  file before) and the generic utility scale stays complete, so a template can
  still use it.

## [2026.7.3.post135] - 2026-08-10

Modals no longer pile up behind the page, a locked control answers instead of
swallowing the click, and the System Health card stops shoving the page around.
No migration.

### Fixed
- **The Dashboard could open a COURSE's "Import from GitLab into <CODE>" modal.**
  Modals are teleported to `<body>` so a nested `<form>` cannot break the page's
  own form - which also puts them outside both regions a navigation replaces, so
  nothing ever removed them. Each navigation left another set behind: three
  elements sharing one id and 16 backdrops after two navigations, with
  `openModal` picking whichever came first. The outgoing page's modals are now
  retired when navigation starts.
- **A locked control on an archived course swallowed the click.** Dimmed and
  silent, it read as broken rather than unavailable. Buttons now stay clickable
  and answer with the reason as a toast (the same contract the dead-token banner
  uses for Sync); only form fields stay truly disabled, because an input that
  looks editable and silently refuses keystrokes is worse.
- **The System Health card blinked on every check.** Its loading state replaced
  the rendered dashboard, so the block collapsed from ~519px to ~170px and back,
  shoving System Actions, Feature Flags and Job History up and down the page. A
  re-check now keeps the card at its exact size and only dims it (composited
  opacity, so it cannot stutter); the first-run skeleton mirrors the real
  component card - badge, latency bar and detail rows - so it reserves the space
  the result needs.

## [2026.7.3.post134] - 2026-08-10

Every date field in the app now opens the same calendar, an archived course is
enforced as read-only by the routing table rather than by memory, and a refresh
button tells you what it did. No migration.

### Fixed
- **Only some calendars had semester weeks.** The week column needs a semester
  to count from, and only a course page published one - so the events Replay
  range, and any date field outside a course, opened a bare month grid. Pages
  without a course now fall back to the running (or next) semester of the TUKE
  FEI academic calendar the app already ships, so every picker in the app is the
  same control.
- **Refresh buttons that did nothing visible.** The events pipeline refresh and
  the webhook-configurations reload re-rendered identical rows with no loading
  state and no confirmation, so a click was indistinguishable from a dead
  button. Both now follow the contract the admin System refresh already had:
  report working, then report done (or failed).
- **Two "Refresh" buttons were not refreshes.** On course Activity and Analytics
  the control triggered a full GitLab sync - a remote job that can take minutes
  and fails outright with no worker running. They are labelled **Sync** now and
  say so on hover; Activity additionally notes that its view updates on its own
  (it is subscribed to the course stream).

### Security
- **Six course-scoped write routes had no archived-course guard**, so a direct
  API call could act on a read-only course: issuing a live webhook secret,
  starting a paid LLM analysis of a merge request, generating checks with the
  LLM, importing a support-form definition, and reassigning course teachers
  (whose form is now locked in the UI too). All refuse an archived course now.
- The guard is enforced by **walking the application's routing table** instead
  of a hand-maintained list of handlers, which is how these six were missed. A
  new course-scoped mutation now fails the suite until it either carries the
  guard or is recorded, with a reason, as an action that must stay available
  while archived (reactivate, transfer, purge, cancel a running job).

### Removed
- The `/dashboard/courses/{id}/analytics/stream` SSE endpoint (148 lines): no
  client ever subscribed to it and nothing ever published to the Redis channel
  it listened on. Its dead `sseUrl` config key went with it.

## [2026.7.3.post133] - 2026-08-10

The "Follow the latest updates" feed stops speaking machine, and a group,
project or student page of an archived course now says so instead of letting
you find out by clicking. No migration.

### Fixed
- **The activity feed printed raw action names.** Eleven audit actions had no
  label, so rows rendered as `member_exclusion_toggled` - and the fallback was
  the identifier itself, meaning any action added later would do the same.
  All eleven now have a label, an icon and a target page, and the fallback
  turns an unknown identifier into a sentence so machine text can never reach
  the widget again.
- **The feed was always English**, even on a Slovak dashboard: its text is
  composed server-side and the template renders it verbatim. Labels, actors,
  job outcomes and counts are now translated (+30 catalog strings). The counts
  avoid numeral agreement, which the catalog cannot express: Slovak needs
  "2 zmeny" but "5 zmien".
- **Audit rows were attributed to a number.** The member-scoring toggle recorded
  the session's id field as the actor - GitLab's numeric user id on the OAuth
  path - so the feed read "0001 - ...". It now records the username like every
  other audit write, and ids left in existing rows are resolved to usernames
  when the feed is built (one batched query; unresolvable ids read as
  "Unknown user" rather than a bare number).
- **An archived course's group, project and student pages looked fully
  editable.** The read-only guard keyed off `.tabs-nav`, which only course pages
  render, so those pages showed no archived strip and left every control live -
  including "exclude from scoring", which failed only once the server answered
  403. They now carry the same marker and strip, and their controls are locked
  with the reason on hover.

## [2026.7.3.post132] - 2026-08-10

An archived course is now genuinely read-only *and* still escapable, in-app
navigation stops losing state between pages, and the date picker works on first
paint again. Browser-verified: every dashboard page, 290 buttons, 20 modals, 77
internal links. No migration.

### Fixed
- **An archived course dimmed the NEXT page you opened.** `#globalBannerSlot` and
  the `is-course-archived` class live outside `#main-content`, the only region a
  navigation swap replaces, so the archived strip stayed pinned to the top of the
  Dashboard and its guarded buttons stayed greyed. Portaled strips are now retired
  on navigation and the read-only class is scoped to the swapped region.
- **Archived courses were still editable.** The guard only locked
  `[data-process-lock-when]` buttons, which the weekly-deadlines editor never
  carried: the modal opened, "Save week" wrote into the schedule JSON, and the
  save that would have rejected it was disabled anyway. Every control inside
  `form.is-course-archived` is now locked, including the check rows the page
  renders after load (MutationObserver), with a `data-readonly-ok` opt-out for
  filters, export, reload and disclosure toggles.
- **Archiving a course was a one-way door.** The same guard disabled Activate,
  Transfer and Delete Forever - the three actions the server explicitly still
  allows on an archived course, and permanent delete *requires* it to be archived.
- **Archive / Activate / Delete Forever threw and did nothing.** `courseActions`
  called a bare `t(...)` that does not exist in its IIFE (the rest of the file uses
  `GP.t`), so every course lifecycle action died on `ReferenceError` at the first
  confirmation string.
- **No date input got a picker on first paint.** `core.bundle.js` is a deferred
  script and therefore runs at `readyState === 'interactive'`, before the deferred
  flatpickr that follows it in `<head>`; the init guarded on `'loading'`, took the
  immediate branch and `initFlatpickr` returned silently. This is what removed the
  semester week column from the deadline calendar.
- **`<head>` metas went stale on in-app navigation.** `course-id`,
  `semester-start` and `semester-end` are rendered per page but never re-merged, so
  after any navigation the week column had no semester to count from.
- **A second click during a navigation was dropped**, leaving the reader on the
  first page with no sign their click registered. It is now queued and honoured.
- **In-app anchor links landed at the top of the page.** A content-only swap never
  triggers the browser's fragment scroll; and the archived banner's "Reactivate"
  pointed at `#danger-zone`, which did not exist.
- **The course-status poll outlived the page that started it** and could reload a
  page you had already navigated away from.
- **"Loading..." froze mid-animation.** The label was animated through
  `background-position` + `background-clip: text` - a paint animation the
  compositor cannot run - so it stopped exactly when the incoming page occupied
  the main thread, beside a ring that kept spinning because it animates
  `transform`. Both loading labels now breathe on `opacity`.
- **Team and project page views were never recorded.** The telemetry beacon sent
  an ad-hoc `metric_type` with a string `context`, and the endpoint answered 422.
- **Export / Import Full Configuration stretched across half the card each** and
  collapsed to a lopsided pair once the read-only guard wrapped the disabled
  Import in its tooltip span - `.form-row` is the grid for form inputs, not buttons.
- **131 UI strings had no Slovak translation**, including the whole weekly-deadline
  editor, the archived banner and the blocking server messages (dead GitLab token,
  no worker, archived course). Three confirmation dialogs were built from template
  literals and so could never be translated at all; they take parameters now.

### Changed
- **Navigation feedback follows GitLab / YouTube.** The outgoing page stays on
  screen, dimmed and inert, while the top progress bar reports the fetch; the
  branded loader appears only if the fetch really drags (>1.2s). It used to blank
  the content after 120ms, which is what made pages appear to jump.

### Removed
- 30 dead skeleton CSS classes (`gl-sk-qa-*`, `gl-sk-attn-*`, `gl-skeleton-header*`,
  `gl-sk-doughnut`, ...) left behind by earlier skeleton work.

### Tests
- **The browser suite was silently vacuous against a live server.** `tests/conftest`
  substitutes its own `SECRET_KEY`, so the minted session cookie was rejected and
  every page under test was really the login form; only the guard assertion failed.
- **Route discovery walked a JSON endpoint and an HTML fragment as pages**
  (`/dashboard/notifications`, `/dashboard/activity`).

## [2026.7.3.post131] - 2026-08-06

Follow-up to post130: the new API-spec gate only worked on a warm app. No migration.

### Fixed
- **`test_api_spec_inventory` read `app.routes` directly and failed in CI.** This
  app defers `include_router` into placeholders that are only flattened at
  startup, so a plain read sees ~19 routes - the gate then declared all 83
  documented endpoints phantom. It now walks them through
  `tests/route_discovery.iter_routes`, the same unwrapping the page-walk suites
  use. Verified in a clean `python:3.12-slim` container, not just locally.

## [2026.7.3.post130] - 2026-08-06

Green pipeline, no more 401s in Search Console, and the READMEs stopped lying.
No migration.

### Security
- **`cryptography` 49.0.0 -> 50.0.0** (GHSA-g6cj-pr64-35w5 / CVE-2026-69247).
  `pkcs7_decrypt_*` leaked the recovered RSA plaintext length through both its
  return value and its timing. This is what turned the `dependency-scan` CI job
  red. `exclude-newer` moved 2026-07-21 -> 2026-08-01 so uv can see the fix;
  `cryptography` is the only pin that changed.

### Fixed
- **Search Console reported "Blocked due to unauthorized request (401)".** The
  culprit was `/grafana/`, `/prometheus/` and `/jaeger/` - Caddy answers those
  with a basic-auth 401 and they never reach the app, so no `X-Robots-Tag` of
  ours could cover them. They (and `/metrics`) are now `Disallow`-ed in
  `robots.txt`, and Caddy sends `X-Robots-Tag: noindex, nofollow` on all three.
- **`docs/04-api-spec.md` documented 15 endpoints that do not exist**
  (`teams/{id}/recheck`, `reports/{filename}`, `telemetry/flags*`,
  `telemetry/report/*`, `telemetry/support/forms*`, `courses/{id}/clone`, ...)
  while omitting whole live areas (transfer, run-checks, webhook-configs, job
  cancel, SSE streams). Section 5 is now generated from the route table and
  pinned by a test in both directions.
- **The READMEs stated numbers that stopped being true long ago.** `README.sk.md`
  still advertised `rq-scheduler` with 12 periodic jobs (there is no scheduler),
  44 models across 48 migrations at head `047_bg_job_project_id` (really 39
  across 11 at `011`), 222 routes (204), and Docker-verify / CI-failure /
  conflict-simulator modules that were deleted. Both READMEs also linked an
  `LLM_README.md` that does not exist, and claimed a 10-panel Grafana dashboard
  with 7 alerts (18 panels, 18 alerts). A gate test now pins each countable
  claim.

## [2026.7.3.post129] - 2026-08-05

The env examples and the webhook docs describe the app that actually exists.
No migration.

### Fixed
- **`.env.example` and `.env.production.example` advertised 14 settings nothing
  reads:** `FEATURE_RUBRIC_ENGINE`, `FEATURE_GAMING_DETECTION`,
  `FEATURE_TIMELINE_DASHBOARD`, `FEATURE_ROSTER_IMPORT`,
  `FEATURE_CONFLICT_SIMULATOR`, `FEATURE_DOCKER_VERIFICATION`,
  `FEATURE_CI_FAILURE_GENERATOR`, `DOCKER_VERIFY_*`, `CONFLICT_BOT_*`,
  `CI_FAILURE_BOT_*` and `RQ_MAX_RETRIES`. Setting any of them did nothing.
  Both files now list the real feature flags (all 11 of them) plus the SMTP,
  session, semester-lifecycle, retention and monitoring settings that were
  missing entirely. A new gate test fails if they drift again.
- **The three dead tool flags are gone from `docker-compose.yml`** as well.
- **The webhook docs described a signature scheme GitPulse does not use.** They
  told you to generate `GITLAB_WEBHOOK_SECRET` into `.env` (nothing reads it)
  and showed an invented HMAC `verify_gitlab_signature` handler. In reality
  GitLab sends the secret in `X-Gitlab-Token`, GitPulse generates that secret
  per project or per webhook configuration, stores only its bcrypt hash, and
  rotation happens through `POST /api/v1/webhook-configs/{id}/rotate`.

## [2026.7.3.post128] - 2026-08-05

An archived course is now read-only everywhere, not just in the UI. No migration.

### Fixed
- **Every course-scoped write endpoint now rejects an archived course.** Project
  sync, group update/delete/restore, project link/unlink/restore, course update,
  course settings, the full-config import and all three LLM-analysis triggers
  went straight through - only the buttons were dimmed. They all return the
  shared 409 "archived and read-only" now, and a gate test fails if a new write
  handler forgets the guard.
- **Importing a GitLab group no longer silently un-archives a course.** The
  importer set `is_active = True` on the resolved course, so re-importing (or
  even matching one by code/year/semester) quietly brought an archived course
  back to life. It now refuses with a clear "reactivate it first".
- **Webhooks for an archived course are acknowledged and dropped.** GitLab kept
  delivering into archived courses, rewriting their data and firing "Live
  update" toasts on pages the UI presents as frozen.
- **Disabled buttons on an archived course explain themselves again.** They were
  dimmed with `pointer-events: none`, which also killed the hover that carries
  the tooltip - so they looked broken rather than locked.
- **The User Info modal no longer jerks when the data lands.** The skeleton and
  the loaded card are different heights, so the body snapped in one frame; the
  swap is height-animated now.
- **Docs no longer document endpoints that do not exist:** `/api/v1/pipelines/report`
  and `/pipelines/validate` (invented CI job), `/api/v1/webhooks/test`,
  `/api/v1/health`, `/api/v1/team-metrics`, and `teams/{id}/recheck` (the real
  route is `run-checks`).

## [2026.7.3.post127] - 2026-08-05

The sidebar logo animation is smooth again. No migration.

### Fixed
- **The GitPulse logo's pulse no longer stutters / freezes.** It animated
  `stroke-dashoffset` (a sweep the browser can only run on the main thread) with
  `will-change: stroke-dashoffset` forcing a repaint layer, so the pulse hitched
  whenever the page was busy. It now uses a gentle opacity glow that runs on the
  compositor - smooth regardless of load. Removed the now-dead sweep keyframe.

## [2026.7.3.post126] - 2026-08-05

Tooltip wrapping + no zebra flicker when expanding a group. No migration.

### Fixed
- **Long tooltip text no longer runs off the edge.** Emails, bot logins and
  GitLab paths (unbroken strings) overflowed the tooltip; it now wraps them
  (`overflow-wrap: anywhere`, wider max-width).
- **Expanding a group no longer breaks / flickers the table striping.** A group's
  child project rows are shown by un-hiding them, which shifted the
  `nth-child(even of ...)` zebra parity of every row below. Child rows
  (`[data-parent-team]`) are now excluded from the zebra count and carry a stable
  nested tint, so expanding / collapsing never re-stripes the table.

## [2026.7.3.post125] - 2026-08-05

Archived courses are read-only on the group page and the server. No migration.

### Fixed
- **The group (team) page's write actions are now disabled + explained on an
  archived course, not hidden** - matching the course and project pages (Link
  Project / Sync / Run Checks / Delete stay visible but greyed, with a
  "this course is archived and read-only" tooltip).
- **Excluding a student from scoring is now rejected server-side on an archived
  course** (HTTP 403), so a stale client that still shows the control enabled
  cannot change scoring membership on a read-only course.

## [2026.7.3.post124] - 2026-08-05

Modals close on navigation; archived actions are disabled + explained. No migration.

### Fixed
- **Open modals no longer stay floating over the next page.** Modal backdrops are
  moved to `<body>` (out of forms), so they lived outside the swapped content and
  a navigation left them open on top of the new page. Navigation now closes any
  open modal / drawer first.
- **Write actions on an archived course are shown disabled with a tooltip, not
  hidden.** They used to vanish (reading as "half the buttons randomly missing");
  now Add Group / Import / Sync / Run Checks (and the project's Sync / Unlink /
  Run Checks) stay visible but disabled, each explaining "this course is archived
  and read-only" on hover. A reusable `disabled_reason` on the button macro wraps
  a disabled control so its tooltip still shows.

### Changed
- **Skeletons hold invisible a touch longer (0.42s)** before painting, so a
  borderline-fast load no longer flashes one for a frame.

## [2026.7.3.post123] - 2026-08-05

Every button has an iOS-style press. No migration.

### Changed
- **Buttons now depress on tap, iOS-style.** They had an almost invisible active
  state; every `.btn` now scales to 0.94 on press and springs back on release,
  for tactile feedback. This completes the motion set alongside modals (grow from
  the button that opened them), dropdowns (from the toggle), and toasts / tooltips
  (from their own position). Reduced-motion neutralises it.

## [2026.7.3.post122] - 2026-08-05

Spinner actually spins; modals aren't see-through on open. No migration.

### Fixed
- **The loader spinner was frozen** (only the label animated). Promoting it to a
  compositor layer with `transform: translateZ(0)` collided with the spin
  keyframe (interpolating translateZ -> rotate froze it). It now uses
  `will-change` alone and an explicit `rotate(0deg) -> rotate(360deg)` keyframe -
  it spins smoothly and cyclically again.
- **Modals no longer look translucent / "broken" on open.** The dialog inherits
  the backdrop's opacity, and a slow backdrop fade left the whole dialog (and its
  skeleton) see-through - with the table showing through - for up to half a
  second. The backdrop now reaches full opacity in ~200ms while the dialog keeps
  its scale-spring, so it is solid almost immediately.

## [2026.7.3.post121] - 2026-08-05

Smooth conic spinner restored; auto-update after deploy. No migration.

### Changed
- **Loader spinner is the sweeping conic arc again** (the border-ring look was a
  regression), now promoted to its own compositor layer (`will-change: transform`
  + `translateZ`) so it keeps the good look AND stays smooth under load.
- **The User Info modal's structural skeleton is back.** It mirrors the loaded
  card so there is no layout jump; what read as "translucent / see-through" was
  the modal caught mid open-animation, not the skeleton.

### Fixed
- **The app auto-refreshes to the new version after a deploy.** A bumped service
  worker now reloads the tab once when it takes control, so a release is picked up
  without a manual hard-refresh (the recurring "I still see the old version").

## [2026.7.3.post120] - 2026-08-05

Loader spinner is smooth under load. No migration.

### Fixed
- **The navigation loader spinner no longer stutters / looks frozen while a page
  loads.** It was a rotating conic-gradient + mask, which the browser repaints on
  the main thread - so exactly when the incoming page kept the main thread busy,
  the spin hitched and looked stuck. It is now a border spinner rotated purely by
  transform on its own compositor layer (`will-change: transform`), so it stays
  perfectly smooth and cyclical regardless of what the page is doing.

## [2026.7.3.post119] - 2026-08-05

Modals grow from the button; cleaner, animated loaders. No migration.

### Changed
- **A modal now grows out of the button that opened it** (and collapses back
  into it), iOS-style, instead of scaling from its own centre - the trigger's
  position becomes the dialog's scale origin.
- **The User Info modal shows a clean loader, not a skeleton.** Its structural
  skeleton read as broken (translucent bars over the table behind the modal); it
  is now a centred spinner with a label.
- **Loading labels are animated.** A brand-orange band sweeps across the loader
  text ("thinking"-style) instead of a static string, everywhere a loader label
  appears. Reduced-motion shows a solid colour.

## [2026.7.3.post118] - 2026-08-04

Overlays grow from their own position instead of sliding in. No migration.

### Changed
- **Modals, dropdowns, tooltips and toasts now expand from their own place and
  settle back into it, instead of sliding in from an edge.** Modals scale from
  their centre (the backdrop owns the fade), dropdowns scale out of the toggle
  (top origin, or bottom when they flip up), toasts scale in/out from their spot
  rather than sliding up then off to the side, and tooltips grow from the edge
  nearest their anchor. No more "arrives from nowhere" default slides/fades.

## [2026.7.3.post117] - 2026-08-04

Interactive controls work after navigation; archived courses are read-only. No migration.

### Fixed
- **Dropdowns and other interactive controls work after navigating.** After an
  SPA navigation, Alpine-driven components silently stopped working - the Event
  Pipeline Type/Status filters would not open, and page components were present
  but never initialised (no error, so it slipped past console checks). The cause
  was `Alpine.initTree` running in the same tick as clearing `x-ignore`, before
  Alpine released the subtree; it now runs one frame later.
- **Archived courses are genuinely read-only.** An archived course showed a
  "read-only" banner but its write buttons stayed enabled (Sync, Run Checks, Link
  Project, Delete on the team/project pages; Add Group, Import, Sync All on the
  course page). They are now hidden while the course is archived.

## [2026.7.3.post116] - 2026-08-04

Skeletons never flash; accessibility clean on every page. No migration.

### Fixed
- **Skeletons no longer flash for a frame.** Server-rendered skeletons painted
  instantly, so a fast page showed grey blocks for a moment before the data
  arrived. `.gl-skeleton` now holds at opacity 0 for ~0.28s (step-end) and only
  appears if the content is still loading - quick loads paint no skeleton at all,
  slow ones still get one, and there is no fade so no blink.
- **Accessibility is clean on every page.** A 13-page audit (accessible names,
  form labels, alt text, ARIA references, keyboard-reachable controls) came back
  clean except one icon-only "Open in GitLab" link on the team page, which now
  has an aria-label.

### Verified
- Live data updates (SSE `/api/v1/dashboard/stream`) connect on the events and
  dashboard pages; the full unit suite (2535 tests) passes.

## [2026.7.3.post115] - 2026-08-04

Loader redesign, reachable table actions, no more blink. No migration.

### Changed
- **Navigation loader is a spinner ring + label, not a heartbeat.** The static
  GitPulse mark now sits inside a modern rotating gradient ring with a localized
  "Loading..." label and a "taking longer than usual - your connection may be slow"
  note that appears only if the fetch drags past ~3.5s. The heartbeat/sonar stay
  a hover-only flourish elsewhere.

### Fixed
- **Row action buttons stay reachable on narrow screens.** A wide table scrolled
  sideways and pushed the whole Actions column off the right edge; it is now
  pinned (`.table-sticky-actions`), so the User Management buttons are always
  visible.
- **No more blink on load.** The skeleton→data reveal fade and the navigation
  content fade both started content at opacity 0, flashing empty after the opaque
  skeleton/loader ("tables blink, reload blinks"). Content now appears in place,
  instantly.
- **CI bundle-check is green again.** `components.min.js` had been regenerated but
  never staged since the table-reveal change, so the gate failed on every
  pipeline (the deploy path bypasses CI); the artifact is now committed.

## [2026.7.3.post114] - 2026-08-03

Refresh lands at the top; two ARIA defects fixed. No migration.

### Fixed
- **Refresh no longer makes the page jump around for seconds.** The reload
  scroll-restore re-wrote the scroll position every 120ms for 5 seconds to fight
  scroll-anchoring as lazy data grew the page. Refresh now simply lands at the
  top (`history.scrollRestoration = 'manual'`, saved offsets dropped) - clean and
  predictable.
- **Tab panels now resolve their `aria-controls`.** Tab buttons referenced
  `tab-panel-<name>` ids that never existed on the panels; `GP.initTabs` now sets
  each panel's id + `role="tabpanel"`, so assistive tech follows the tab → panel
  relationship on every tabbed page.
- **The JSON-drop textarea has a programmatic label.** Its label rendered as a
  plain span, leaving the field unnamed for screen readers; it now links via
  `aria-labelledby`.

## [2026.7.3.post113] - 2026-08-03

Branded loading pulse during slow navigation. No migration.

### Changed
- **A slow page now shows the GitPulse pulse, not a frozen page or a misfit
  skeleton.** When a navigation took more than ~120ms the old page used to sit
  frozen for the whole fetch and then flash the destination's server skeleton for
  a moment. A slow navigation now replaces the content with the centred GitPulse
  ECG-heartbeat mark (sonar rings + heartbeat running), giving instant "loading"
  feedback the moment the navigation starts - and, being the brand mark, with
  nothing to mis-match the destination layout. A fast page still swaps straight
  in with no loader, and reduced-motion shows the static mark.

## [2026.7.3.post112] - 2026-08-03

Data tables fade in calmly instead of popping. No migration.

### Changed
- **Loaded table data no longer pops in abruptly.** When a table's rows first
  replaced the server-rendered skeleton they appeared in a single hard jump
  (~1800px, no transition), so a page "behaved horribly when data loaded". Every
  ClientPaginator-backed table now fades its rows in as one unit on the initial
  load only (reduced-motion aware); the existing height-lock already keeps paging
  from jumping, and a guard means paging and live refreshes never re-animate.
  Because almost every data table shares this paginator, the calm skeleton→data
  handoff is now consistent across the whole app.

## [2026.7.3.post111] - 2026-08-03

Navigation is no longer blocked by synchronous script loading. No migration.

### Performance
- **Page navigation no longer freezes for seconds on slow links.** The SPA swap
  handler used to fetch each per-page script with a *synchronous* XHR so it would
  run before Alpine initialises the swapped content - on a high-latency
  connection that blocked the main thread for a full round-trip per script, so a
  page with several scripts visibly hung. Scripts are now collected into one
  ordered list and loaded with non-blocking `<script async=false>` (ordered
  execution, cache-served on warm navigations); the swapped block fades in
  immediately as the shell and Alpine initialises once the scripts finish (a
  generation guard drops the callback if a newer navigation supersedes it).

### Changed
- **Event Pipeline filter dropdowns are comfortably sized.** The Type / Status
  filters shrank to their label width and read as tiny; they now share a
  consistent, readable width in the filter bar.

## [2026.7.3.post110] - 2026-08-03

Onboarding tour is less intrusive. No migration.

### Fixed
- **The onboarding tour no longer pops on every page.** The welcome card was
  re-armed on every navigation, so a new tour invitation appeared on each page's
  first visit as you moved through the app ("appearing everywhere"). It now
  auto-prompts at most once per device; every tour stays available on demand from
  the launcher.

## [2026.7.3.post109] - 2026-08-03

Navigation/loading correctness pass. No migration.

### Fixed
- **Pages no longer break on a direct load / F5 / new tab.** The Alpine CSP build
  self-starts in a microtask before a page's `{% block content %}` factory scripts
  run, so components defined there (Teachers, Course Settings, Tickets, Support)
  were unregistered at `alpine:init` and rendered as a dead shell on a cold load.
  Alpine's start is now deferred to `DOMContentLoaded`, after every deferred script
  has defined its factory.
- **Content no longer shifts on navigation.** The SPA swap nested a second
  `<main id="main-content">` inside the first on every navigation (duplicate id
  and doubled page padding, so content jumped inward after a nav). Only the inner
  content is swapped now - one element, stable padding.
- **No more console errors navigating to the Teachers or Dashboard pages.** A
  top-level page `<script>` in the content made htmx throw on the Teachers page
  (moved to the head like every other page bundle); the Dashboard's shared
  `config-import.js` helper is now loaded in order before `dashboard.js`.

### Changed
- **The navigation loading placeholder was removed.** A generic full-page skeleton
  never matched the destination page. Navigation now keeps the current page visible
  with the top progress bar until the new page arrives (GitLab / YouTube style),
  and each page shows its own structure-matching skeletons as its data loads.
- **Event Pipeline: Replay Events is now a modal** opened from the header (no
  standalone section), the duplicate per-tab Refresh is gone, and the recent-events
  empty state uses the standard empty-state component.

## [2026.7.3.post108] - 2026-08-03

GitLab-style polish for the Event Pipeline page and page navigation. No migration.

### Changed
- **Event Pipeline page restructured, GitLab-style.** The two stacked stat grids
  collapse into one health strip, and the Recent Events + Dead-Letter Queue tables
  move into a single card with tabs (Recent events / Dead-letter queue) instead of
  two separate tables the eye had to untangle. Replay Events is now a collapsed
  tool rather than a form competing with the live feed. Reuses the existing
  declarative tab controller (`GP.initTabs`), so it survives SPA navigation; every
  JS-referenced id is preserved.

### Added
- **Synchronized content fade-in on navigation.** The whole `#main-content` block
  now fades in as a single unit on each SPA navigation (reusing the existing
  `.gp-content-in` opacity curve, reduced-motion aware) instead of appearing
  instantly. Deliberately animates the container, not its children - per-element
  staggered entrance was removed earlier because it re-animated on every live
  refresh and read as a blink.

## [2026.7.3.post107] - 2026-08-03

Fixes Alpine components breaking on SPA navigation. No migration.

### Fixed
- **Alpine.js components no longer break after SPA navigation** (the "Undefined
  variable: teacherManager / llmResourceUrls" errors and dead Teachers / Course
  Settings pages). Three causes: (1) a page's shared helper (`js/config-import.js`,
  defining `GP.ConfigImport`) was in `<head>` but not re-loaded on nav, so the page
  bundle threw at `GP.ConfigImport.init`; (2) page bundles run async on nav, but the
  Alpine CSP build resolves `x-data="teacherManager()"` from its `Alpine.data()`
  registry (populated once, at `alpine:init`), not from `window.*`; (3) some bundles
  (course-teachers.js) live in `{% block content %}`, which htmx runs only after the
  swap. Now, on each navigation the handler synchronously (re-)loads every per-page
  `<head>` and content `js/pages/*.js` bundle plus shared helpers in order,
  suppresses Alpine on the incoming content (`x-ignore`) until they are loaded,
  re-registers the page's `Alpine.data()` factories, then inits the subtree.
  Verified: Teachers, Course Settings, Analytics, Events and System all init with 0
  Alpine errors after navigation.

## [2026.7.3.post106] - 2026-08-03

GitLab-style loading skeleton during navigation. No migration.

### Added
- **Instant structure + a loading skeleton while the data streams in.** When a
  navigation response is slow (does not arrive within ~140ms), the content area now
  shows a lightweight shimmer skeleton (page header + a stat row + a card of rows)
  instead of the frozen previous page - so navigation always feels instant and the
  page structure appears before its data, exactly like GitLab. Fast responses swap
  directly with no skeleton flash. The outgoing page is cleaned up before the
  skeleton replaces it, so no SSE / listeners leak. The sidebar, top bar and top
  progress bar stay mounted throughout.

## [2026.7.3.post105] - 2026-08-03

Two SPA-navigation follow-up fixes. No migration.

### Fixed
- **Config-driven modals (e.g. Edit User) now open after SPA navigation.** The
  content-only swap does not touch `<head>`, where `{% block extra_scripts %}`
  renders a page's inline JSON config (`gp-page-config`). A page bundle re-run on
  navigation read the PREVIOUS page's (or a missing) config, so admin checks failed
  silently and the Edit-User modal never opened. The head reconciler now also
  refreshes those per-page inline configs from the response.
- **The "You're offline" page no longer appears while the browser is online.** The
  service worker showed the full-screen offline fallback on ANY failed navigation
  fetch (a transient blip, an aborted navigation, a momentarily unreachable
  backend). It now retries once and only serves the offline page when
  `navigator.onLine` is actually `false`; otherwise it serves cache or lets the
  browser show its normal error.

## [2026.7.3.post104] - 2026-07-29

Follow-up to the SPA navigation: it now swaps only the content region, so
navigation no longer flashes/reflows the layout. No migration.

### Fixed
- **Navigation no longer breaks the layout.** post103 swapped the whole `<body>`,
  which re-rendered the sidebar + top bar on every click - a visible flash/reflow
  (and it wiped body-parented state like toasts + the job-bar container each nav).
  Navigation now swaps only `#main-content`; the sidebar, top bar, job bar and
  banners stay mounted (GitLab-style stable chrome), and the afterSwap handler
  reconciles what lives outside the content from the response: `<title>`, the
  breadcrumb, the sidebar active item, the `#gp-modals` block, and the scroll
  position (a fresh page starts at the top). Verified: charts render, Alpine
  (22/22) initialises on swapped pages, interaction + modals work, Back/Forward
  works, the sidebar element is never replaced (no flash), 0 console errors.

## [2026.7.3.post103] - 2026-07-29

GitLab-style instant page navigation. Clicking through the app no longer does a
full-page reload - only the page body is swapped, so the sidebar, top bar and all
CSS/JS stay put and transitions are instant. No migration.

### Added
- **Instant SPA navigation (like GitLab).** Internal link clicks are intercepted
  and the new page is fetched + swapped in via `htmx.ajax` instead of a full
  browser navigation, so the `<head>` (all CSS/JS) is never re-parsed and only the
  body content changes. History (Back/Forward), the top progress bar, `<title>`
  and the sidebar active state all update correctly. Chart pages, Alpine
  components, tooltips, date pickers and per-page scripts re-initialise on each
  swap; the top progress bar now lives on `<html>` so it survives the body swap.
  The click interceptor runs in the **capture** phase because some sidebar/menu
  components `stopPropagation` on their own clicks, which would otherwise starve a
  bubble-phase handler. Links that change server state or i18n (logout, language,
  OAuth), downloads, external links and `#`-anchors still do a normal navigation.

### Changed
- **Chart.js is now loaded globally** (was per-page in `{% block extra_head %}`).
  With SPA navigation the `<head>` is not re-parsed between pages, so a per-page
  chart lib would never load when moving from a non-chart page to a chart page;
  loading it once keeps every chart working across navigations.

### Removed
- **The old full-page navigation layer** (`_pageTransitions`: the link-click
  interceptor that only surfaced the progress bar before letting the browser do a
  full reload, plus its view-transition fallback and form-submit progress hook).
  It is replaced by the SPA navigation above.

## [2026.7.3.post102] - 2026-07-29

The Teacher's Checklist chart loads with a structured skeleton instead of a plain
shimmer box, and the shimmer overlay no longer sticks over admin System. No migration.

### Changed
- **The Teacher's Checklist loading skeleton is now the chart's shape, not a grey
  box.** It renders the real R01-R13 codes down the left with shimmer name bars and
  gridlines - the same Pajamas horizontal-bar skeleton (`sk_h_bars`) the admin
  System role breakdown uses - and cross-fades into the live chart on first reveal
  (`revealAfterSkeleton`, observing the visible skeleton so the hand-off never
  hangs on a zero-sized canvas). `sk_h_bars` now takes any height/label-width via
  inline CSS vars, so it matches the checklist's dynamic per-check height exactly.
  The generic shimmer overlay stays for the line, radar and doughnut charts, where
  a structured skeleton doesn't apply.

### Fixed
- **The chart shimmer overlay no longer sticks over admin System's role
  breakdown.** The overlay is now opt-in (`.gl-chart-skel`) so it only covers the
  charts that use it, instead of blanketing every `.chart-canvas-wrap` - which left
  a solid grey box over the role-breakdown card (it already ships its own skeleton)
  that never cleared.

## [2026.7.3.post101] - 2026-07-28

GitLab-style chart loading skeletons and a scroll-preserving refresh. No migration.

### Added
- **GitLab-style chart loading skeletons.** A page's structure paints instantly
  (inline), but its charts are drawn by Chart.js a beat later, leaving a blank
  canvas box in the meantime. That box now shows a Pajamas shimmer that fades to
  the chart the moment it renders (an `afterRender` plugin marks the wrapper ready;
  a safety timer reveals any chart box that never draws, so nothing shimmers
  forever). Covers the analytics, activity, project and student charts.

### Fixed
- **A refresh no longer jerks the scroll position.** The in-place content swap
  briefly emptied the container, collapsing its height and yanking the page up;
  the height is now pinned for the swap and the exact scroll offset restored after.

## [2026.7.3.post100] - 2026-07-28

Follow-up to the inline-render release: fixes a refresh regression it introduced,
and removes the loader/skeleton code it left behind. No migration.

### Fixed
- **The course-analytics "Refresh" (and the auto-reload after a sync finishes) did
  nothing after the inline-render conversion.** It re-fetched content by finding
  the old `.gl-lazy-content` shell and re-triggering its `hx-get` - but that shell
  no longer exists (pages are server-rendered inline now), so the query returned
  null and the content never refreshed. It now re-fetches the content fragment via
  the route's `HX-Content-Only` branch and swaps it into `.gl-tab-content`
  (verified: one fragment request fires, the charts re-render, no console errors).
  A failed re-fetch keeps the existing content and shows a toast instead of wiping
  the region to a "retry" card.

### Removed
- **Dead loader/skeleton code orphaned by the inline-render conversion.** The
  client-side lazy-fragment SWR cache (`25-fragment-cache.js`, ~120 lines) only
  ever cached `.gl-lazy-content` fragments that no longer exist; the `_lazyLoadFailed`
  region-replacer, the skeleton-flash timestamp tracker, and the `.gl-lazy-content`
  / `.gl-lazy-failed` CSS are all gone too. (Earlier the same release removed 1429
  lines of dead skeleton macros from `loaders.html`.)

## [2026.7.3.post99] - 2026-07-28

GitLab-style page loading + a leaner CI pipeline. No migration.

### Changed
- **Pages now load like GitLab: the whole page arrives in one server response.**
  Every data page (course overview / activity / analytics / teachers, team,
  project, student, dashboard, user management, support tickets) used to render
  an instant shell with a skeleton and then fetch its real content in a *second*
  HTMX request (`hx-trigger="load"`), so navigation always showed a
  skeleton→content swap. The content is now server-rendered inline in the first
  response - one request, real structure on first paint, no full-body swap. The
  Redis fragment cache is preserved, and an `HX-Content-Only` request still
  returns just the fragment for in-place refresh / SSE. A new shared
  `render_inline_or_fragment` helper drives this for every page (no duplication).
- **CI trimmed to a lean, best-practice essentials set: 22 jobs → 11.** Kept
  lint (ruff check/format), type-check (mypy), the deploy-safety gates
  (bundle-check, static-artifact-guard, lockfile-check), tests (unit+coverage,
  contract, integration), dependency (SCA) vulnerability scanning, and the image
  build. Removed the heavier / niche jobs (mutation, performance, load testing),
  SBOM generation, container image scanning, SLSA provenance, and the
  publish / security-summary / quality-gate aggregation jobs.

### Fixed
- **The User Info modal no longer jitters as it opens.** Its loading skeleton was
  taller than the real content, so the vertically-centred dialog shrank and its
  top jumped ~50px when the data swapped in. The dialog is now top-anchored (on
  desktop), so the swap moves only the bottom edge - the box no longer jumps.
- **The "Showing data from last sync" freshness banner now also shows on the main
  course tab (Overview),** matching the Activity and Analytics tabs, shown to
  everyone (not only editors) and mutually exclusive with the editor-only
  "Data may be outdated" banner so the two never stack.

## [2026.7.3.post98] - 2026-07-27

Load-flash and empty-analytics fixes. No migration.

### Fixed
- **The Update-settings button briefly flashed enabled on load.** It rendered
  enabled and was only disabled once `initSaveGuard` ran after the HTMX content
  swap. It now ships with the `disabled` attribute (verified in both the full
  page and the HX-Content-Only fragment); the guard still enables it the instant
  the form becomes dirty.
- **Archived courses showed live action buttons and could still be mutated.**
  The `is-course-archived` read-only class was only added by JS after load, so
  the guarded buttons flashed enabled first and were fully live if the JS never
  ran. It is now applied server-side on the settings form and every course tab
  wrapper. More importantly, only the settings-save endpoint rejected archived
  courses; the check endpoints (import, update check, create/update/delete
  custom check) did not, so an archived course's checks were mutable through the
  API. A shared guard now returns 409 on all of them - verified end to end
  against a temporarily-archived course (active create 201, archived create and
  delete 409).
- **The Week Analytics explorer opened on an empty week while its dots pointed
  at populated ones.** The pill dot and the initial auto-select used different
  definitions of "has data", so weeks with a zero-activity row got a dot but
  were skipped by auto-select, and the explorer fell through to the current
  week - which had no snapshot yet - and showed nothing. Both now derive from
  one set, so the explorer always opens on the latest dotted week.

## [2026.7.3.post97] - 2026-07-23

README corrected to match the code. No migration.

### Fixed
- **The README documented features that no longer exist and a scheduler that
  never ran.** Every claim was checked against the code rather than edited by
  eye:
   - The "Automation (12 Scheduled Jobs)" table listed twelve jobs on fixed
      intervals. **None of those twelve function names exist**, and four of them
      described removed features - CI failure scenarios, conflict expiry,
      conflict verification and Docker reverification, whose models are gone.
      `app/workers/sweep.py` states it plainly: *"GitPulse is webhook-driven:
      there is no recurring scheduler, so nothing here fires on a timer."* The
      table now lists the eight jobs that genuinely exist, with their real
      trigger, and every path was import-checked.
   - The topology row and repository map claimed `rq-scheduler (12 active
      periodic jobs)` and `scheduler (24 jobs)` - two different invented
      numbers for a scheduler that runs with `with_scheduler=False`. The
      architecture diagram had a matching `rq-scheduler 12 jobs` node.
   - The teaching-tools line still advertised Docker verify, CI failure
      scenarios and the conflict simulator.
   - Counts were stale after the migration squash: **48 migration files, head
      `047_bg_job_project_id`** -> actually **11 files, head
      `011_patterns_into_check_configs`**; 44 models -> **37**; 21 schema
      modules -> **18**; 222 routes -> **204** counted through the lazily
      included routers.

## [2026.7.3.post96] - 2026-07-23

Native browser tooltips replaced with the component across three pages. No migration.

### Fixed
- **Three pages still used native `title=` tooltips**, which this project bans in
  favour of the component (they ignore the app's styling, can't be themed, and
  read as inconsistent). A browser sweep counted them: 105 on the admin System
  page (the job-history table's type, timestamp, error and result cells plus the
  cancel button), 13 on course Settings (the enable/disable check toggles), and
  26 on the student page (the compliance heatmap cells). All now emit
  `data-tippy-content` and are bound with `GP.initTippy` on the freshly rendered
  rows.

  Verified in a browser after the change: 0 native `title=` on all three pages,
  and hovering renders a real component tooltip (heatmap cell -> "Zlyhanie", job
  cell -> its timestamp, and all 18 setting toggles bound). The one broken image
  the sweep flagged on the student page is the GitLab avatar 404 falling back to
  initials as designed - the img is hidden, not shown broken.

## [2026.7.3.post95] - 2026-07-23

Filters and pagination for the recent-events feed. No migration.

### Added
- **The recent-events feed can be narrowed and paged.** A busy course produces
  hundreds of events, and the feed was an unbroken wall of rows. It now has a
  type filter (narrowed server-side), a status filter (Processed / Pending /
  Failed, applied over the fetched window so the health counters keep describing
  all of it), and the same paginator the dead-letter table uses. Verified in a
  browser: the page caps at 25 rows, each filter changes the visible set
  correctly, and there are no JS errors.

### Fixed
- **The events page hung for over a minute.** A `data_attrs` argument was passed
  to the `select_field` macro, which does not accept one; rather than surfacing
  an error, the template render wedged, and the page never returned. Found by
  bisection: reverting the template alone restored the page, and re-applying the
  filters without that argument rendered in 59ms. The tooltip those attributes
  carried moved to the field label, which the dropdown already supports.

## [2026.7.3.post94] - 2026-07-22

The Activity tab's address matches the page. No migration.

### Changed
- **The Activity page lived at `/courses/{id}/projects`.** The navigation has
  always labelled it Activity and the page is about pipeline health and group
  activity, so the address bar contradicted the tab you had clicked - and
  "projects" already means something else in this app, the per-project detail
  pages under `/dashboard/projects/{id}`. It is now
  `/courses/{id}/activity`.

  The old path returns a permanent redirect rather than disappearing, so
  existing links and bookmarks keep working. Verified: the new path serves 200,
  the old one answers 301 to it, and following the redirect lands on the page.

## [2026.7.3.post93] - 2026-07-22

Activity and Analytics no longer look like the same page. No migration.

### Changed
- **Activity and Analytics carried an identical header**, so neither said which
  page you were on or what it was for - the course code, name, year and
  semester, and nothing else. Each now names itself and its scope: Activity is
  what is happening in GitLab right now, Analytics is how students score against
  the compliance checks and how that moved over the semester.
- **"Pass Rate" on Activity collided with "Checklist Pass Rate" on Analytics.**
  They measure different things - finished CI pipelines versus compliance
  checks - so two unrelated percentages read as if they contradicted each other.
  The Activity figure is now "Pipeline Pass Rate" and says outright that it is
  about builds, not scoring.
- **Activity's counters explain themselves**, matching the standard Analytics
  already met: what Passed and Failed count, that Running moves on its own, that
  Pending usually means waiting for a GitLab runner, and that every figure is
  aggregated across the linked projects.

  Verified in a browser: the two headers are no longer identical, 75 and 13
  tooltips present and all bound to the component, no JS errors.

## [2026.7.3.post92] - 2026-07-22

Event context and a testable LLM. No migration.

### Added
- **A mock LLM provider.** Every LLM-backed feature was unexercisable whenever
  the real account was unreachable or out of quota, and the failure looked
  identical to a broken integration - impossible to tell whether the
  surrounding code worked. `LLM_PROVIDER=mock` answers locally with shaped,
  schema-valid responses so those paths can be driven end to end. Not for
  production.

  This immediately settled an open question: custom-check generation had been
  returning 500, and with the mock the same endpoint returns 200 with usable
  suggestions - so the endpoint logic was correct and the failure was purely
  the provider's quota error escaping. The full custom-check flow now passes
  end to end: create, list, LLM-generate, run checks, delete.

### Changed
- **The event feed says what happened, where, and who did it.** It previously
  showed a raw GitLab project id, which tells a teacher nothing about which
  course or student an event belongs to, and an event type alone does not say
  whether something was opened, merged or closed. Each row now carries a
  one-line summary of the action, the course and group it belongs to with the
  GitLab path beneath, and the user whose action produced it - all resolved
  server-side in one batch query rather than per row.

  The new strings are translated, so the table no longer mixes languages.

## [2026.7.3.post91] - 2026-07-22

Event Pipeline made self-explanatory. No migration.

### Changed
- **The Event Pipeline now explains itself instead of assuming the reader knows
  the vocabulary.** The page opens with what an event actually is and how one
  ends up in the dead-letter queue, so the counters below have a frame of
  reference rather than being bare digits.
- **Pipeline health is visible before the problems.** A Processed / Pending /
  Failed row covers the recent feed, so a reader can tell at a glance whether
  events are flowing without parsing the table. The page previously led with
  failure counts alone.
- **Every counter, column and status badge carries an explanation** through the
  tooltip component - what a retry count above zero means, why a growing Pending
  number matters, that a parked event is not lost. The page header no longer
  claims the page is only about the dead-letter queue, which stopped being true
  when the recent feed was added.

  Verified in a browser: 93 tooltips present and all 93 bound to the component,
  zero native browser tooltips, counters populated (34 processed), and a hover
  renders the explanation text.

## [2026.7.3.post90] - 2026-07-22

Event Pipeline visibility. No migration.

### Fixed
- **The Details button on the Event Pipeline never worked.** Its handler called
  `viewEventDetail`, a function that was not defined anywhere in the file, so
  every click threw `viewEventDetail is not defined` and the payload viewer
  could not open - on dead-letter rows just as much as anywhere else. The page
  has had that modal all along with nothing able to fill it. The function now
  exists, backed by a new `GET /api/v1/events/{id}/payload`.

### Added
- **The pipeline now shows the normal flow, not only failures.** It listed the
  dead-letter queue exclusively, so a healthy system receiving events looked
  identical to one receiving nothing at all. A "Recent Events" feed lists what
  GitLab has delivered lately, newest first, with each row marked Processed,
  Pending or Failed, and a failure carrying its reason inline so the row
  explains itself.

  Verified in dev by driving real merge-request events through the worker and
  loading the page: 27 events listed with Processed badges, the Details modal
  opens with the raw payload, no HTTP errors and no JS errors.

## [2026.7.3.post89] - 2026-07-22

Live-update feedback. No migration.

### Added
- **A page now says what changed when it refreshes itself.** A live update
  refreshed the page silently, so numbers moved under the reader with no
  explanation of why. An arriving change is announced instead, naming what it
  was - merge requests, issues, comments, pipelines, pushes, members - from the
  event kind the backend already publishes.

  Bursts are the normal case: one student pushing produces several events within
  seconds and a re-synced project produces many, so notices are coalesced over
  2.5s into a single message reporting how many changes it covers, rather than
  one toast per event.

  It lives in core rather than on one page, because every page holds the
  dashboard stream - the sidebar owns it for badges and the dashboard page takes
  that same connection over - so both callers share one path and only one of
  them is ever connected.

  Verified in a real browser against webhooks driven through the worker, with
  both the EventSource and the announce call instrumented: the dashboard, the
  support page and the admin system page each receive the update and render the
  notice, coalesced and translated.

## [2026.7.3.post88] - 2026-07-22

Emergency-path fix found by testing a revoked GitLab token. No migration.

### Fixed
- **The shared GitLab token-health flag expired and never came back.** The flag
  exists so one dead token makes every entrypoint and worker refuse doomed work
  instead of each independently probing GitLab and spawning a storm. It lives in
  Redis under a 120s TTL, but the setter wrote Redis only when the status
  *changed* - and a condition that persists, such as a revoked token, never
  changes the status. The key expired, was never rewritten, and from then on
  every caller fell back to a live probe measured at 975ms each, against GitLab,
  indefinitely, for exactly the situation the flag was meant to short-circuit.

  The key is now refreshed once it is halfway through its TTL as well as on
  change. The hot path stays cheap: `mark_ok()` runs on every successful GitLab
  call and still skips Redis almost always, because a refresh happens at most
  once per half-TTL.

  Verified against a genuinely revoked token: the key is written with a live
  TTL, and a status check drops from a 975ms cold probe to 1-3ms once the flag
  is present.

## [2026.7.3.post87] - 2026-07-22

Webhook throughput. No migration.

### Performance
- **A re-delivered webhook paid for the GitLab fetch all over again.** GitLab
  re-delivers on failure, so duplicates are routine. The bulk sync already skips
  the diff and approvals fetch for a merge request whose `updated_at` has not
  moved - both are immutable while the MR is unchanged - but the webhook path
  never did, so every duplicate delivery cost two live API calls.

  The skip only applies when a previous enrichment demonstrably succeeded
  (`changed_files` is what it populates). Without that condition a delivery
  following a *failed* fetch would carry the same timestamp as the stored row
  and be starved of enrichment permanently.

  Verified with the client patched to count calls: the first delivery fetches
  changes and approvals once, five duplicate re-deliveries add nothing, and a
  delivery whose `updated_at` actually moved enriches again.
- **The project -> team lookup ran twice per event.** `_resolve_team_id` is
  called by four post-commit side-effects (metrics enqueue, dashboard notify,
  member syncs), which is 2000 identical statements across a 1000-event burst.
  It is now memoised on the session, and `_process_async` opens one session per
  event, so the cache is scoped to exactly that event - a project moved between
  teams is picked up by the next one rather than cached process-wide. SQL per
  merge-request event measured 17.8 -> 16.8.

## [2026.7.3.post86] - 2026-07-22

Data-integrity fix in the webhook path. No migration.

### Fixed
- **GitLab timestamps in webhook payloads never parsed, which silently switched
  off the out-of-order protection.** GitLab is not consistent about datetime
  formats: the REST API returns ISO 8601, but webhook payloads render
  `object_attributes` timestamps through Rails' default `to_s`
  (`2025-10-15 10:00:00 UTC` - space separator, named zone).
  `datetime.fromisoformat` rejects that shape, so every webhook-delivered merge
  request and issue stored NULL `created_at`, `updated_at` and `merged_at`.

  The consequence was worse than the missing values. The stale-event guard
  decides whether a delivery is out of order by comparing its timestamp against
  the stored one, and a stored NULL makes it conclude "not stale". GitLab does
  not guarantee webhook ordering and re-delivers on failure, so a late `open`
  arriving after a `merge` un-merged the merge request, and a late `reopen`
  after a `close` reopened the issue - flipping the author's R10/R11 scoring
  until the next full sync.

  Found by driving real payload shapes through the worker entry point: after
  open -> update -> merge, replaying the original open event reverted the state
  to opened. The same replay is now correctly skipped.
- **A webhook could erase a timestamp a full sync had already stored.** Both
  the merge-request and issue processors assigned these fields unconditionally,
  so an unparseable payload overwrote a good value with NULL - which is exactly
  what disables the guard above. They now only overwrite a value they actually
  parsed. `closed_at` is deliberately still cleared, because GitLab sends it as
  null when an issue is reopened.

  Rows already written by webhooks keep their NULL timestamps; a full sync
  repopulates them from the REST API.

## [2026.7.3.post85] - 2026-07-22

Load-testing fix and dead-rule removal. No migration.

### Fixed
- **A large team broke the metric recompute instead of just slowing it.**
  `_load_by_mr` filtered on `merge_request_id IN (...)`, which sends one bind
  parameter per id, and the PostgreSQL wire protocol caps a statement at 32767
  of them. A team whose projects held more merge requests than that failed the
  whole recompute with asyncpg's "the number of query arguments cannot exceed
  32767" - a hard crash, not degradation. Ids are now queried in batches well
  under the cap. Found by running `compute_team_metrics` against a seeded
  120,002-row table: it raised after 27.9s, and now completes in 56.3s. The
  engine's other `IN` clauses are bounded by team size or project count, or
  are subqueries, which send no parameter list at all.

### Removed
- **43 CSS rules whose selectors can never match.** All 36 classes involved are
  absent from templates, JS, Python-emitted markup and dynamic class
  construction. A selector dies if *any* class in it is dead, not only when all
  are: `.nr-body.gl-description` is exactly as unreachable as a bare
  `.status-pill`, since every class in a compound selector must be present to
  match. Negation and match-family pseudos were excluded, because a dead class
  inside `:not()` widens the match. Verified by confirming no element in any
  live DOM carries any of the 36 classes, across every dashboard page plus the
  390px and 900px viewports whose media queries owned several of the rules.

## [2026.7.3.post84] - 2026-07-22

UI correctness and a query fix found by load-testing. No migration.

### Fixed
- **A modal opened shortly after page load closed itself.** The first-visit
  tour prompt calls `closeCompetingOverlays`, which closes every active modal
  and drawer. That is right before a tour the user asked for, but the welcome
  card is unsolicited, so it was destroying work in progress. Traced with a
  wrapped `GP.closeAllModals`: the Weekly Deadline modal opened, faded fully
  in, then closed itself between 400ms and 700ms. The auto-prompt now skips
  while a modal or drawer is open.
- **Cached pages flashed grey placeholder blocks.** A per-frame sampler
  counting only painted skeletons measured ~460ms of placeholder on a page
  whose content was already cached. Placeholders are now held invisible
  briefly and revealed only if the content really is slow: 0ms and 32ms on
  cached loads, 134ms cold.
- **The "expected checks" state badge sat at a different place in every row**,
  because the check name did not claim the leftover width. Measured badge left
  edges 906/503/544/522 against cell right edges 1069/713/713/713; every badge
  now sits a fixed 4px from its cell edge.
- **The last native browser tooltips** (global job bar cancel/dismiss, support
  SSE indicator) now render through the tooltip component. Elements whose
  label is driven by reactive state can opt into `data-tippy-live`, which
  re-reads the content when the tooltip is shown.

### Changed
- **A convention pattern now visibly follows the switch that governs it.**
  R02's branch regex and R05's headings are only enforced while their option is
  on, but both fields stayed fully editable either way, so there was no visible
  way to tell a pattern was off. The relationship is declared in the check
  registry and the field is disabled and dimmed when its switch is off. The
  value is deliberately kept, so switching back on restores the pattern.

### Performance
- **The project page spent most of its time building a two-element set.**
  `_derive_project_member_usernames_from_activity` selected every merge request
  and issue row for the project and de-duplicated them in Python. Measured on a
  seeded 120,002-row table: slowest call 2661ms -> 976ms cold, 240ms warm. Set
  equivalence with the old row-scan was verified across NULL authors,
  NULL/empty arrays, duplicate ids within an array, ids in both arrays, and
  cross-project isolation.

### Developer experience
- `start-dev.ps1` now passes `--reload-include "*.json"`. `uvicorn --reload`
  only watches `*.py`, so edits to `compliance/builtin_checks.json` (read at
  import) were silently ignored until a manual restart.

## [2026.7.3.post83] - 2026-07-22

Maintenance release: no runtime behaviour changes, no migration.

### Fixed
- **The `lockfile-check` and `unit-tests` CI jobs were failing.** The committed
  `requirements.lock` carried `colorama`, a Windows-only dependency; CI
  regenerates the lock in `python:3.12-slim` and compares byte-for-byte, so the
  two could never agree. Coverage had also slipped to 37.33% against a 38%
  floor. Both reproduced locally in the CI image before fixing.

### Changed
- **Dead stylesheet rules removed** (~236 lines): the `callout` component,
  whose macro had no callers and whose CSS had drifted from the markup it
  emitted; the compliance-violations styles for a feature that is gone; and the
  upload component that preceded `json_drop`.
- **Coverage raised to 38.11%** by testing previously unverified logic:
  configuration-import validation, queue backpressure, job cancellation,
  webhook scope validation and the optional tracing shims.

### Added
- `scripts/dead_css_report.py` - advisory report for unused CSS classes, with
  the four ways a naive version of the check produced false positives written
  into its docstring.

## [2026.7.3.post82] - 2026-07-21

### Fixed
- **A "Database unavailable" 503 now says why.** Both database exception
  handlers accepted the exception and discarded it, so connection refused,
  pool timeout, exhausted server connections and bad credentials all produced
  an identical blank 503 with no log line - unactionable in production. The
  cause, request method and path are now recorded, with the original exception
  attached explicitly (these run as handlers, not inside an `except` block, so
  `logger.exception()` alone would drop the message).

## [2026.7.3.post81] - 2026-07-21

### Fixed
- **Compliance-check edits no longer apply on their own.** The check editor and
  the weight presets wrote straight to the server the moment you pressed Save
  Check, while every other control on the settings page waited for "Update
  settings" - and there was no way to back a change out. Both now stage into a
  pending map that the settings save flushes last, so the page applies in one go.
- **The number stepper no longer jumps two at a time.** Two implementations were
  bound to the same class - the macro's Alpine handler and a document-level
  handler in the check editor - so one click stepped the value twice. Replaced
  by a single framework-free control the check editor clones.
- **Scroll position survives an in-place reload.** The app shell scrolls inside
  `.gl-page-content`, so `window.scrollY` was permanently 0: every
  `reloadKeepScroll` saved 0 and the restore was rejected. It was a no-op on
  every page using the shell.
- **Modals no longer flash on open.** The backdrop and the dialog both animated
  opacity, which multiplies for nested elements, and the dialog's spring curve
  overshot past 1 - a visible double-expose of everything inside.
- **The admin system page survives a Pydantic V3 upgrade.** It read
  `model_fields` off the settings instance, which V3 removes.

### Changed
- **Convention patterns moved into the checks that enforce them.** The branch
  regex, test-file globs and MR template headings were course-level settings
  edited in a separate "Patterns" card, and two of the three scored nothing
  unless the matching check was separately set to strict. They now live in each
  check's own configuration, with TUKE FEI / Strict / No-conventions presets
  that always carry the strict-mode flags. Migration 011 backfills existing
  courses; the old columns are kept for rollback.
- **One JSON surface per field.** A dashed upload box stacked on a textarea gave
  each value two controls that cleared each other; the editor is now itself the
  drop target.

## [2026.7.3.post80] - 2026-07-18

### Fixed
- **Out-of-order GitLab webhooks no longer regress entity state.** GitLab does
  not guarantee webhook ordering and re-delivers on failure. The MR and issue
  processors overwrote `state`/`updated_at` unconditionally, so a stale
  `update` (state=opened) redelivered after a `merge`/`close` would un-merge an
  MR or re-open a closed issue, flipping R10/R11 for the author until the next
  manual full sync (the system is webhook-driven, no periodic scheduler). The
  pipeline processor already had this guard; extracted it into
  `processors/_common.is_stale_update` (monotonic `updated_at`) and applied it
  to both the MR and issue processors. Unit-tested; new MRs/issues and
  equal-timestamp full syncs still apply normally.
- **Commit timestamps parsed tz-aware.** `commit_processor` used raw
  `datetime.fromisoformat()`, so an offset-less timestamp was stored naive - 
  inconsistent with the tz-aware `committed_at` column and the compliance
  engine's tz-aware semester-window filter, where a naive value raises
  `TypeError` at scoring time. Routed through the shared `parse_gitlab_datetime`
  like every other entity.
- **LLM analysis redacts more PII.** `minimize_mr_context` redacted titles,
  descriptions, comment bodies and diffs and anonymised authors, but inserted
  MR metadata string values (branch names) and changed filenames verbatim.
  A branch name or file path embedding a student email/handle/token now passes
  through `redact()` before the context is sent to the external model.

### Changed
- **Compliance weight presets are server-driven and dynamic.** The
  course-settings presets (Balanced/Review/CI/Minimal) were a hard-coded JS
  object enumerating only R01-R12 (R09/R11/R13 skipped, so applying a preset
  left stored weights summing above 1.0, and a new built-in check never
  appeared). Presets are now computed server-side (`build_weight_presets`) over
  the live built-in check set from the registry, normalised to sum to 1.0, and
  returned from `GET /courses/{id}/checks`; the client just fetches and applies.
- **R02 spec aligned with code.** The R02 docstrings/model comment claimed a ∀
  (all authored MRs must comply) rule while the code passes on ∃ (at least one),
  consistent with R03/R04/R05. Per product decision the ANY behaviour is
  intended; corrected the docs. No behaviour change, no student scores affected.
- `MetricSnapshot.checks_total` fallback default 12 → 13 (the live count is
  always passed dynamically; the constant only mattered as a stale label).

## [2026.7.3.post79] - 2026-07-17

### Changed
- **Compliance config parsing unified.** The string→bool coercion
  (`x.lower() not in ("false","0","no")`) was copy-pasted across R02/R04/R06/
  R09/R11 and re-implemented as a local `_bool` closure in R10 - six copies of
  one idea, and the five inline copies skipped the `bool()`-normalisation that
  R10's closure applied to non-string values. Consolidated into a module-level
  `_cfg_bool` sibling to `_cfg_int`, so every check parses config booleans one
  way (and more robustly). R05's deliberately strict `in ("true","1","yes")`
  form is left as-is. The capped partial-credit ratio `min(n/max(t,1),1.0)` - 
  copied in R03/R06/R07/R09 - is now `_partial_ratio`.
- **Second query-dedup pass.** The "latest MetricSnapshot per student, scoped
  to one team → dict" query - copy-pasted three times (`projects.py` twice,
  `teams.py` once) with per-site redundant inline `func` imports - now lives in
  one shared helper `_stats.latest_student_metric_map` (the student twin of
  `latest_team_metric_map`). Two dict annotations tightened to their true
  non-optional type.
- Behaviour-preserving across all documented config values and both queries;
  covered by new unit tests and the full suite (2,310).

## [2026.7.3.post78] - 2026-07-17

### Changed
- **Query dedup: one owner for the "latest snapshot per team" logic.** The
  same `func.max(computed_at)` subquery that fetches each team's most-recent
  `TeamMetricSnapshot` had been copy-pasted across five call sites - twice in
  the course pages, again in `api/sync.py` and `api/sync_stream.py`, and once
  more inlined in `home_course_health.py` (a byte-identical copy of a helper
  that already lived in `home_stats.py`). Consolidated into two shared helpers
  in `api/dashboard/_stats.py` - `latest_team_metric_map` (full snapshot per
  team) and `latest_team_snapshot_subquery` (the max-per-group subquery) - so
  the pattern has a single tested source of truth. Removed three orphaned
  imports and a stale "using DISTINCT ON" comment on a query that never used
  DISTINCT ON. Behaviour-preserving; new unit test locks in the helper
  contract (empty-input short-circuit, keyed-by-team mapping). The rest of a
  full-codebase refactor audit (compliance engine, sync/webhook workers,
  services, templates) confirmed those subsystems were already deduplicated by
  the post76/post77 sweeps - no further safe cuts remained.

## [2026.7.3.post77] - 2026-07-17

### Changed
- **Instrumented whole-system dead-code purge - ~5,000 lines removed.** A
  repo-wide audit (custom analyzers for Jinja macros, CSS classes, JS
  exports and templates, plus the CI dead-code report) found and deleted,
  with every candidate verified against a corpus of templates + app JS +
  vendored libraries + Python-built HTML, and with dynamic class-name
  construction families (`'prefix-' + x`, `'prefix-' ~ var`,
  `prefix-{{ var }}`) excluded wholesale:
  * **74 orphan Jinja macros** (~930 lines) across the component library - 
    unused form fields, modal/layout/table helpers, alert and toast
    variants - plus their stale imports, and 2 fully-unreferenced component
    files.
  * **~680 orphan CSS classes** (~3,950 lines across 44 files) - rules
    whose every selector rooted in a class no template, script or vendored
    library ever applies (mostly cascade-orphans of long-removed features
    and the macros above). The styles bundle shrank ~6%.
  * **8 dead JS export surfaces** (unused `window.*`/`GP.*` compatibility
    handles) whose internals stay in use privately.
- **`badge(variant='blue')` now renders styled** - `blue` joins the
  info-family alias list; it used to emit an unstyled badge (e.g. the
  "Commit Ref" and "Issue Link" chips).
- Guarded by the full unit suite (2,286 tests green), bundle checks, JS
  parse checks and a real-browser visual smoke of the component surface.

## [2026.7.3.post76] - 2026-07-17

### Changed
- **Legacy/compat sweep - less code, one way to do each thing.** The bare
  Clone flow is fully gone: both `/clone` endpoints (API + dashboard form),
  the `CourseCloneRequest` schema, and the dashboard's duplicate clone modal
  and JS are removed - the course context menu now opens the one Transfer
  wizard (course settings → Danger Zone), which covers cloning as
  "clean course, don't archive, no webhooks". `apiCall` dropped its
  positional-retryCount compatibility branch (no caller used it). The
  `window.GitPulseMotion`/`GP.motion` facade and its kept-for-compatibility
  no-ops (count-ups, scroll reveals, blanket traffic lights) are deleted - 
  the motion controller now exposes exactly one helper
  (`GP.revealAfterSkeleton`) plus the compliance rings it owns. The
  never-fired legacy `htmx:abort` listener is gone. Orphan CSS deleted:
  `slideIn` keyframes, `.row-expand-enter`, `.card-glass` (+ its
  `--surface-glass` tokens), the unused stagger token; card hover
  transitions no longer animate `transform` (hover transforms were removed
  earlier). The stale `start-dev.sh` (native-Postgres/Redis-Cloud era,
  referenced nowhere) is removed - `start-dev.ps1` is the dev entry point.
  The repo's dead-code report is clean.

## [2026.7.3.post75] - 2026-07-17

### Added
- **Full "Transfer to new semester" - proper course reactivation.** The old
  bare Clone (settings only, no groups, dead webhooks) is superseded by a
  wizard in course settings → Danger Zone: pick the new academic year and
  semester, then choose what carries over - **everything** (all groups;
  members/projects re-sync from GitLab), **a selected subset of groups**, or
  a **clean empty course** with the same settings. Everything auto-retunes:
  same-semester transfers shift the semester window, course deadlines and
  every per-week deadline date by the academic-year delta (the university
  calendar barely moves), cross-semester transfers keep the expected-check
  structure but clear un-guessable dates. **Webhooks keep working with zero
  GitLab changes** - the default mode re-points the existing webhook
  configurations to the new course (the GitLab-side hook resolves its course
  purely through the configuration); alternatively issue fresh one-time
  secrets (surfaced once in the wizard) or skip webhooks. The source course
  is archived (optional) and the initial sync for carried groups is enqueued
  (optional). New `POST /api/v1/courses/{id}/transfer`; `/clone` stays for
  compatibility. Service-level behavior covered by 8 new unit tests
  (carry modes, ownership validation, webhook move vs fresh, date shifting,
  cross-semester clearing, archive toggle).

## [2026.7.3.post74] - 2026-07-16

### Fixed
- **Global search: erasing the last character no longer flashes every
  suggestion for a second.** Race condition: clearing the query rendered the
  default suggestion list WITHOUT invalidating the still-in-flight API
  request for the previous character; when that response landed ~200ms later
  its callback wiped/replaced the list. Every `doSearch` now bumps the
  request generation (including the empty-query path) and every response
  path discards stale generations. Verified frame-by-frame in a real browser
  that the tables' own filter+paginator pipeline is clean (20→10→20 rows
  with zero intermediate flashes).
- **Dashboard greeting avatar ring is visible on the light theme** - it was
  `--gl-gray-0` (white in both themes) and vanished against the light
  background; now the shared `--border-color` ring token every other avatar
  uses.

### Added
- **Lazy pages remember their last content (stale-while-revalidate).**
  Revisiting a lazy page used to replay the full skeleton while the same
  fragment re-fetched - the "everything reloads on every visit" complaint.
  Each `.gl-lazy-content` fragment's last HTML is now kept per-tab
  (sessionStorage, keyed by fragment URL, invalidated by app version and
  15-minute age, purged on the login page, LRU-capped) and injected
  instantly in place of the skeleton on revisit while the normal request
  still fires and swaps in fresh data silently - YouTube-style SWR. This
  also means empty states ("No tickets found") appear instantly on revisit
  instead of flashing a shimmering table skeleton first. Verified in a real
  browser: first visit skeleton→content, revisit instant cached content →
  silent revalidation.

### Changed
- **Dead skeleton code deleted:** the generic `sk_table`/`sk_tbody_rows`
  pair and the `sk_commits_tbody_rows`/`sk_mrs_tbody_rows` row macros were
  referenced by no template (leftovers of the old student page); guard tests
  now assert the living per-table contracts instead.

## [2026.7.3.post73] - 2026-07-16

### Changed
- **The whole animation system rethought: motion only where it carries
  information.** Removed as flair, app-wide: the metric count-up (stat values
  animated 0→N over 600ms on every reveal - numbers now just render), the
  staggered block reveal and the item cascade on lazy-content loads (regions
  now fade in as ONE quiet unit, opacity-only, one short duration), the
  entrance rise/scale transforms on skeleton hand-off and page enter, and the
  never-used scroll-reveal machinery (.motion-soft-reveal +
  IntersectionObserver) with the dead .motion-scale-in / .motion-fade-slide /
  .motion-htmx-enter/-exit / .motion-page-enter utilities. What stays is
  deliberate: overlay enter/exit (modals, dropdowns, toasts), loading
  indicators (spinners, skeleton shimmer, progress), change feedback
  (cell flash, badge pop, banner height ease), semantic status pulses and the
  compliance-ring draw. Public GitPulseMotion API kept (no-ops), so nothing
  breaks.
- **Role badges are ONE component everywhere.** The Admin badge in the course
  Teachers manager was blue while User Management shows amber - every role
  chip now goes through the shared `role_badge()` macro (admin=amber,
  teacher=purple, TA=info, student=neutral); the members-table access ladder
  (`member_access_role_badge`) and the user-info modal's JS maps already
  matched and stay in lockstep. The student page's Author/Reviewer pill was
  renamed `mr_role_badge` so the MR-participation concept can't be confused
  with global roles.

## [2026.7.3.post72] - 2026-07-16

### Fixed
- **Distracting hover animations removed app-wide.** The empty-state icon
  lifted, scaled, glowed a blue halo and floated on an infinite loop on
  hover; course cards and interactive cards lifted (`translateY`/`scale`);
  issue rows lifted. All hover transforms are gone - hover is now a calm
  border/background/shadow change only (GitLab-style). Press feedback on
  buttons and semantic status pulses (running dots, traffic lights) stay.
- **Version detection now works in development.** The dev build fingerprint
  only hashed `core.bundle.js` + `main.py`, so template and page-bundle
  edits were invisible to the client's update detection. In development the
  fingerprint is now per-server-start: every `uvicorn --reload` restart
  announces a new version and open tabs show the update toast + auto-reload.
- **Support tickets skeleton is now structurally identical to the loaded
  page.** The search/filters toolbar was a hand-copied approximation that
  had drifted; it is now ONE shared macro (`_tickets_toolbar.html`) rendered
  by both the live page and the skeleton (disabled) - the same single-source
  pattern as `table_heads.html` - and the skeleton now includes the
  pagination bar the live page renders, killing the layout jump on load.
  Static chrome stays real; only DB data shimmers.

### Changed
- **Badges componentized.** 21 hand-written `<span class="badge ...">` across
  8 templates (teachers manager, webhook settings, weekly deadlines, student
  detail, admin courses, list/loaders components) now go through the shared
  `badge()` macro; the macro gained an `x_text` param for Alpine-bound
  counters. Two parameterized one-offs (dynamic status class, risk badge)
  intentionally remain.

### Added
- **Dev toolbar in the UI** (development/debug only, never rendered in
  prod): a fixed DEV pill that expands to the whole local tooling surface - 
  Swagger (interactive tester for every endpoint), ReDoc, health JSON,
  Mailpit (caught emails), Admin system page, Grafana, Jaeger - plus the
  live build fingerprint, which changes on every dev reload so you can see
  exactly which server process a tab is talking to.

## [2026.7.3.post71] - 2026-07-16

### Fixed
- **Dense tables share the User Management scroll model everywhere below
  ~1440px windows - single-line headers and cells, columns sized to content,
  horizontal scroll.** post70 kept the fixed %-columns in the tablet band and
  let headers wrap at word boundaries; in practice that still read as mush - 
  "Event ID" / "Dead Since" on two lines, "Ac tio ns" broken mid-word, dates
  wrapped to three lines (DLQ, tickets). Worse, the dense tables' headers
  alone need ~1010px, more than the ~980px content column a 1280px laptop
  window leaves next to the sidebar - so fixed %-columns cannot fit even on
  small desktops. All `tbl-fixed` scroll tables (tickets, DLQ, job history,
  admin courses, feature flags, group activity, recent MRs) now switch to
  content-sized auto layout with `nowrap` + ellipsis below 1440px and scroll
  horizontally in their wrapper; the fixed %-contract returns on full
  desktops where it genuinely fits. Unbounded text columns are capped with a
  clean ellipsis (ticket/MR titles, group links, feature-flag description);
  error/result previews were already capped. Group/project/member course
  tables extended to the same boundary.
- **Tickets desktop columns rebalanced again** - post70's 7% Actions column
  wrapped its own header on 1280px screens; restored to 10%.
- **Job History mobile "Result / Error can wrap" rule re-pointed** to the
  right column (it had drifted onto Duration when the select-checkbox column
  was added).
  Verified in a real browser at 480/600/769/820/900/1024/1280/1600px:
  single-line headers everywhere, zero unintended cell clipping, no
  page-level horizontal overflow.
- **User Info modal avatar fallback uses the component standard** - the
  initials circle was the last one-off blue/purple gradient left in the app;
  it now uses the same neutral surface + border + secondary-text circle as
  every other avatar fallback (profile header, discussion notes, reviewers).

### Changed
- **`start-dev.ps1` now drives the whole dev environment** (no separate
  script): `up`/`restart` bring up the docker-compose.dev.yml containers - 
  Postgres :5433, Redis :6379 and the new **Mailpit** mail catcher
  (SMTP :1025, UI :8025, matching the `.env` SMTP settings) - with health
  waits; the DB wipe on `down`/`restart` runs inside the compose container
  (no local psql needed, correct 5433 port instead of the stale native-5432
  assumptions); health checks cover the real ports. Mailpit catches all
  outgoing email locally.

## [2026.7.3.post70] - 2026-07-16

### Fixed
- **Every data table (and its skeleton) now scrolls instead of squishing across
  the whole tablet range.** Root cause: in the 769-1024px band the fixed 240px
  sidebar squeezes the content column to ~480-736px - often narrower than a
  phone, where the sidebar overlays - but most horizontal-scroll minimum widths
  only applied at ≤768px, so groups, group/project member matrices, course
  settings (checks, webhooks), student and archived-course tables crammed their
  columns exactly on tablets. All scroll floors now cover ≤1024px (the pattern
  post68 applied to dense admin tables), the groups and projects tables switch
  to content-sized auto layout with scroll in that band, and the dashboard
  archived-courses and weekly-deadlines tables opted into the scroll contract
  they were missing entirely. Skeletons share the live tables' classes, so they
  follow automatically.
- **Tickets table: badges and pills no longer clip mid-word.** The "In
  Progress" status badge and submitter/assignee pills were hard-clipped by the
  fixed column widths even on desktop. Columns rebalanced (status/submitter/
  assignee wider, title/actions narrower), the tablet scroll floor raised
  860→1000px so every non-title column fits its typical badge/pill, and
  unusually long usernames now degrade with a clean ellipsis inside the pill.
  Only the title column ellipsizes by design.
- **User Management kept its intended tablet widths** - the new generic floor
  briefly out-ranked the users-table's own 760/680px tablet contract in the
  cascade; its selectors now carry the specificity to win again.
  Verified in a real browser at 480-1280px: zero clipped cells outside
  intentional title ellipsis, no page-level horizontal overflow anywhere.

## [2026.7.3.post69] - 2026-07-16

### Fixed
- **The top progress bar can no longer hang at ~99% forever after AJAX actions**
  (e.g. right after creating a support ticket). Two mechanisms survived post66,
  both reproduced in a real-browser harness against the production bundle:
  (1) a bar carried over from the previous page could be "adopted" by a request
  starting during the bar's 650 ms finish fade - the adoption skipped the
  in-flight increment, so when that request's completion event was lost (its
  element removed mid-swap) the counter read zero while the bar visibly
  trickled forever, and the network reconciler explicitly ignored the
  zero-counter state; (2) a canceled navigation - staying on the page via the
  unsaved-changes dialog, pressing Esc during a slow load, or a POST that turns
  out to be a file download - left the `page-navigating` marker on `<body>`
  forever, which disabled the reconciler entirely. Fixes: `stop()` now consumes
  the inherited pending synchronously (no adoption after a finish), the
  reconciler also finishes a visibly-running bar whose counter is zero (unless
  the finish fade owns it), and a bounded watchdog drops `page-navigating`
  after 10 s alive without an actual navigation. Verified end-to-end: both
  endless repros now self-heal in ~2-12 s, while legitimate slow requests and
  slow full-page navigations are untouched.

## [2026.7.3.post68] - 2026-07-15

### Fixed
- **Dense tables now stay readable across the whole tablet range (small tablets
  included), not just phones.** The horizontal-scroll min-width for fixed-layout
  data tables (tickets, job history, admin courses, feature flags, DLQ, activity)
  only kicked in at ≤820px, so in the 820-1024px tablet band the columns were
  squeezed at full width - headers wrapped and action buttons overflowed. It now
  applies up to 1024px, so those tables scroll cleanly with a comfortable column
  width and a sticky first column instead of cramming. The tickets table (8
  columns) gets a slightly wider 860px floor so its title / badges / assignee
  pill / action button never collide.
- **Dead-letter queue: the select checkbox no longer looks squished.** The
  JS-rendered rows put the checkbox in a class-less first cell, which collapsed
  to the bare checkbox width in the tablet auto-layout; the first column now
  keeps a tap-friendly minimum width and is centered.

## [2026.7.3.post67] - 2026-07-15

### Fixed
- **Table cells and avatar fallbacks made consistent across the app.** Ticket
  titles were wrapping to 2-3 lines on tablet (the `text-overflow: ellipsis` was
  inert without `white-space: nowrap`); they now stay on one line and clip
  cleanly, matching the User Management table that was cited as the ideal. Long
  group/subgroup names in the Groups table clip with an ellipsis instead of
  wrapping. The student-profile avatar's initials fallback used a one-off
  blue/purple gradient; it now uses the same neutral grey circle as every other
  avatar fallback (discussion notes, reviewer chips), so fallbacks look identical
  everywhere.

## [2026.7.3.post66] - 2026-07-15

### Fixed
- **Top progress bar now finishes the instant an in-place AJAX action completes**
  (e.g. "ticket created"), instead of running out a timeout. Replaces the post65
  20 s ceiling - which was wrong: it still visibly ran for 20 s. The real fix is
  the pattern the GitLab group import / group CRUD already used
  (`GP.finishTopProgress()` when an AJAX form is intercepted), applied **centrally**
  in the shared submit handler: any form whose handler calls `preventDefault()`
  (support ticket, ticket reply, analytics/replay forms, ...) finishes the top bar
  right away. Because it lives in the one core submit listener, it fixes this
  system-wide, and the button spinner still shows the request's own progress.

## [2026.7.3.post65] - 2026-07-15

### Fixed
- **Tickets list showed only one form's tickets (the rest looked "missing").**
  The list defaulted its form filter to `forms[0]`, so it silently hid every
  ticket that belonged to any other form (or to none) - you saw "#5 but the
  other 4 are gone". The list now shows **all** of the course's tickets; a form
  filter is applied only when one is explicitly requested. Verified: the query
  returns all 5 seeded tickets.
- **Priority changes sent no email.** Only status changes emailed the user; a
  priority change was silent. It now emails the submitter / assignee (when
  different from the actor), like a status change. Verified end-to-end (Mailpit
  caught the "Low priority" mail).
- **Attached image blended into the surrounding text in Preview.** The image is
  now block-level (its own line, clear spacing) instead of inline against text.
- **Table headers wrapped character-by-character on tablet** ("Sub mitte d By").
  Headers now wrap at word boundaries, and fixed scrollable tables keep a usable
  min-width (scroll horizontally) up to 820 px instead of squeezing to shreds.
- **Top progress bar could still hang.** Added a hard 20 s ceiling that
  force-finishes the bar regardless of a stuck `page-navigating` class or a hung
  fetch - it can no longer stay pinned "on any action". (Complements the post60
  reconciler fix.)

## [2026.7.3.post64] - 2026-07-15

### Added
- **Ticket status/priority/assignment changes now live-update the tickets list**,
  and a **"New ticket received" toast** shows when a ticket arrives. The
  status-update endpoint previously only published to the per-ticket channel
  (the open detail page); it now also publishes a `ticket_updated` event on the
  course channel, so the list reflects the change without a manual refresh. The
  new-ticket reload sets a reload-surviving flash toast so the heads-up is
  visible. Together with post63 this makes the tickets surface fully dynamic - 
  create/change a ticket anywhere (incl. the API) and the UI reacts live.

## [2026.7.3.post63] - 2026-07-15

### Added
- **The tickets list now live-updates when a ticket is created** - including via
  the API / another user - instead of only showing up after a manual refresh.
  Ticket creation now publishes a `ticket_created` event on the course SSE
  channel (`_publish_ticket_created` in `telemetry_support.py`, both the dynamic
  and legacy submit paths), and the course-scoped tickets list subscribes to
  that stream and reloads on the event (coalesced to one reload / 1.5 s, cleaned
  up on navigation). Verified end-to-end in dev: submitting a ticket publishes
  `{"event":"ticket_created","ticket_id":...}` to `dashboard:course:<id>`. (The
  course dashboard already live-updated on webhooks; this closes the same gap for
  tickets - "what I create in the console now shows in the UI dynamically".)

## [2026.7.3.post62] - 2026-07-14

### Fixed
- **Table headers were truncated to "Priority ...", "Category ...", "Acti...".** In
  fixed-layout data tables (tickets, courses, admin/events, ...) `.sort-link`
  forced `white-space: nowrap`, so narrow columns clipped the header labels with
  an ellipsis. Headers now **wrap** within their column instead of truncating
  (data cells still truncate). Scoped to `.tbl-fixed`, so it fixes every
  fixed-layout table at once without touching other tables.

## [2026.7.3.post61] - 2026-07-14

### Fixed
- **Whole page flickered on every navigation.** The page-enter animation was
  supposed to be removed (it made the main container + its small cards blink /
  double-expose on every nav), but the rule survived in `loaders.css` and still
  faded `.main-container` in (opacity 0→1 + slide) on every load. Removed it;
  pages now render instantly (only the single login card keeps a gentle fade,
  which never flickered).
- **Image attachments showed as a link, not a preview.** `renderMarkdown` didn't
  handle `![alt](url)`, so an uploaded image rendered as text like
  `123!file.png`. It now renders an inline **thumbnail** (bordered, click opens
  full size). Applies to both the markdown Preview tab and the ticket thread
  (both use the same client renderer).
- **Filtering a table to zero results showed a blank table with no message.**
  The shared table filter only rendered its "no results" state for a text
  search, not for the status / priority / category **dropdown** filters. It now
  shows a **componentized** empty state (inbox icon + message, matching the
  `table_empty` macro) whenever any active filter hides every row - systemic
  across every filterable table.

## [2026.7.3.post60] - 2026-07-14

### Fixed
- **Top progress bar could hang (never finish) while a background job was
  polling** - during a group import, or on ANY page opened while a sync / import
  is running. The nav bar's stuck-counter reconciler reset its "quiet" timer on
  every background poll's brief network blip, so it never auto-finished and the
  bar stayed pinned for the whole 120 s last-resort timeout. It now **accumulates
  quiet time and only pauses (never resets) on brief poller spikes**, so a stuck
  bar self-heals in ~1.5 s regardless of pollers. A genuinely slow load keeps
  real network in flight continuously, so its bar correctly stays until done.
  Same root cause you saw on group import - this fixes it everywhere.

## [2026.7.3.post59] - 2026-07-14

### Added
- **Teachers get a live toast when a GitLab webhook lands for a group.** The
  webhook SSE notification now carries the group name, and the course page shows
  a staff-only toast (e.g. "Webhook received: Merge request - Team Alpha"). It's
  designed to interact cleanly with the rest of the app: only the visible leader
  tab shows it and broadcasts to sibling visible tabs (N open tabs → one toast,
  background tabs stay silent); it's **suppressed while the course is mid-sync**
  (the global sync bar already signals updates); and it's throttled to one per
  4s so a burst of pushes/pipelines can't spam the corner. The per-event data
  refresh already existed - this adds the visible heads-up. (The recompute was
  already scoped to just the affected group + debounced - unchanged.)

### Fixed
- **A cancelled job no longer reads as "Process failed".** Cancelling a sync /
  run-checks / import is intentional, but it fell through the failure path and
  could show "Process failed". It now shows a clear "Cancelled". The bar's
  terminal-state model stays binary (done/error) - only the wording changed.
- **Calendar header rounded-corner artifact.** The month-nav header and the
  rounded calendar container each rounded their corners, leaving a mismatched
  notch by the `<` / `>` arrows. The calendar now clips cleanly to its rounded
  box (`overflow:hidden`) and the header/arrows no longer double-round.

## [2026.7.3.post58] - 2026-07-14

### Fixed
- **Date-picker calendar stayed open after its modal closed.** Flatpickr appends
  its calendar popup to `<body>`, so when a modal with a date field closed the
  calendar was left floating over the page. Closing a modal now also closes any
  flatpickr owned by its inputs (covers every close path - button, backdrop,
  Escape, programmatic).
- **Calendar month-nav arrows had an invisible hover.** The `<` / `>` hover
  background was `--surface-moderate` - the exact same colour as the
  `.flatpickr-months` header - so hovering did nothing visible and the arrows
  read as empty rounded shapes. The hover now uses the app's icon-button hover
  token, so it's clearly distinct.

### Changed
- **Dashboard onboarding respects archived courses.** When an account had no
  *active* courses it always showed "Create your first course" (linking to the
  course list) - even when every course was archived (e.g. auto-archived at
  semester end). It now offers to **reactivate an archived course for the new
  term**, pointing at `/dashboard/admin/courses` where the Activate button lives.

## [2026.7.3.post57] - 2026-07-14

### Fixed
- **Attachment upload was broken for everyone (real root cause).** `POST
  /support/{token}` (the JSON ticket-submit route) was declared before `POST
  /support/upload`, so `/support/upload` matched the `{token}` param route with
  `token="upload"` - a JSON-body endpoint that can't read multipart, so every
  upload failed with a 422 "Input should be a valid dictionary or object to
  extract fields from". The post55 URL fix only moved it from 404 to the *wrong*
  route; uploads never actually worked. Declared the fixed `/support/upload`
  path before the `{token}` param route (with a guard comment) and added a
  regression test - multipart uploads now hit the upload endpoint and return the
  file URL.
- **Markdown toolbar heading/quote/list rendered literally.** Those block
  markers (`### `, `> `, `- `) only work at the start of a line, but the toolbar
  inserted them at the cursor, so clicking Heading after existing text produced
  `text### text` on one line (rendered as plain text, not a heading). `mdInsert`
  now breaks to a new line before a block marker when it isn't already at
  line-start, like GitHub/GitLab.
- **Redundant double line under the support form header.** After the "Logged in
  as @..." banner was portaled to the global top strip (post56), the
  `gh-form-divider` that used to separate it from the form was left behind - so
  it doubled the `page-header` bottom border into two stacked lines with a gap
  and nothing between them. Removed that orphaned divider; the header border is
  now the single separator. Applies to every support category (they all render
  `_form_content.html`). The two remaining dividers (between Description /
  category fields / Priority) are real section separators and stay.

## [2026.7.3.post56] - 2026-07-14

### Changed
- **Page-level status banners now portal to the global top strip everywhere.**
  The support form's "Logged in as @..." notice, the course "Some sync jobs
  failed" / "Sync cancelled" banners, and the project "GitLab repository is
  empty" warning were rendered inline in the page body; they now move up into
  the shared `#globalBannerSlot` (same mechanism as the archived-course banner)
  and render as the single unified `top_banner` (`.gp-top-banner`) strip, so
  every page's status bars stack together like GitLab's broadcast bar.
- **The two live JS-created course banners were unified too.** The "GitLab token
  invalid" banner and the live "Some sync jobs failed" banner (created by the
  sync SSE stream without a page reload) were `.info-card` boxes inserted into
  the page body; they now render as the same `.gp-top-banner` strip appended to
  `#globalBannerSlot`. Their invariants are preserved: the live failed banner is
  still only created when there's no server-rendered one, and only the
  JS-created card is ever removed. Added an optional `class` argument to the
  `top_banner` macro (carries the `js-sync-failed-banner` hook).
- **The "You're offline" page was redesigned GitLab-style.** It now leads with a
  brand lockup using the app's current logo (`favicon.svg`, precached so it
  renders fully offline) instead of the browser's default globe, sharing the
  same `error.css` tokens as the other error pages.

## [2026.7.3.post55] - 2026-07-13

### Fixed
- **Attachment upload failed everywhere ("Upload failed").** The client posted to
  `/api/v1/support/upload`, which 404s - the route lives on the telemetry router
  (`/telemetry` prefix), so the real path is `/api/v1/telemetry/support/upload`.
  Fixed the URL. The error message now also includes the status code (was empty
  because HTTP/2 has no `statusText`).
- **Markdown editor Preview tab didn't switch (no error).** The `$mdShowPreview`
  magic read `el._x_dataStack` off the Preview button, which is often undefined
  on a descendant, so the write silently no-op'd. It now uses the canonical
  reactive `Alpine.$data(el)` (with the stack walk kept as a fallback) so the tab
  and preview update reactively.
- **Support form flagged false "unsaved changes".** It marked the form dirty on
  ANY `input`/`change`, including programmatic ones (Alpine / `glFormSelect`
  writing a select's default value). It now requires `e.isTrusted` - a genuine
  user edit - so the reload guard no longer fires on a form you never touched.

## [2026.7.3.post54] - 2026-07-13

### Fixed
- **JSON import: removing the file left its content behind.** `showFile()`
  auto-reads the selected `.json/.csv/.txt/.yaml` INTO the paste textarea, but
  `clearFile()` only cleared the `<input type=file>` - not the textarea. So after
  removing the file the content stayed "inserted". `clearFile()` now also clears
  the paste textarea.
- **Remove-file button hover** used a hardcoded dark `--gl-red-950` background
  (jarring on the light theme, same class of bug as the drop-zone). Now the
  theme-aware `--gl-feedback-danger-bg` tint.

### Notes
- Investigated the support **Preview** button and the tickets-list **skeleton**:
  both are correct in the code (the Preview magic `$mdShowPreview` wires the
  shared editor, `renderMarkdown` + `supportFormEditor` load on the page; the
  skeleton uses the same `tickets_table_head()` as the live table). The specific
  breakage isn't reproducible from the code alone and needs a concrete repro
  (what exactly happens on click) rather than another blind guess.

## [2026.7.3.post53] - 2026-07-13

### Fixed
- **Regression: content shifted LEFT when a modal opened.** The post50 scrollbar
  compensation (`--gp-lock-gutter` padding-right) was wrong - `overflow: hidden`
  is still a scroll container, so `scrollbar-gutter: stable` stays effective and
  the gutter is never released. The added padding over-compensated. Reverted; the
  content no longer moves on modal open.
- **Connection/health banner overlapped the top-bar dropdown menu.** It was
  `z-index: var(--z-sticky)` (200), above the dropdown tier (100). It's an
  in-flow status strip (it pushes content down, never overlaps), so it's now
  `calc(var(--z-dropdown) - 1)` - below dropdowns, still above page content.
- **JSON import drop zone was unreadable on the light theme.** The `has-file`
  state used a hardcoded dark `--gl-green-950` background (text invisible on
  light). It's now the theme-aware `--gl-feedback-success-*` tint (bg + text +
  icon), matching the dragover state.
- **Offline page showed the browser's default globe in the tab.** It had no
  favicon; it now links the app favicon (svg + png + apple-touch), so the offline
  tab shows the current GitPulse logo.

## [2026.7.3.post52] - 2026-07-13

### Changed
- **User Info modal skeleton (componentized).** Both entry points (the admin
  users page and the global "click a username" modal in core) showed a generic
  spinner. They now render a structural skeleton that mirrors the loaded card
  (avatar circle + identity + meta + two sections of card placeholders), shared
  via `UserInfoModal.skeleton()`, so the hand-off to real data has no layout
  jump - per the app's skeleton-fidelity principle.

### Fixed
- **Global User Info hung forever on slow/offline networks.** It used a raw
  `fetch()` with no timeout. It now aborts after 12s via an `AbortController`,
  and its error state renders a **Retry** button (matching the admin path). Both
  User Info entry points now share the same skeleton, component avatar fallback,
  timeout and retry.

## [2026.7.3.post51] - 2026-07-13

### Fixed
- **User Info modal avatar uses the shared component fallback.** It was a bare
  `<img>` with a bespoke initial-letter branch; it now renders with
  `data-avatar-fallback` + an initials sibling, so a broken / timed-out / offline
  avatar degrades to initials via the same global handler (retry, offline
  deferral, watchdog) as every other avatar in the app.
- **Top bar dropdown no longer overlaps the connection banner.** The top bar was
  `z-index: var(--z-sticky)` - the same as the health/connection banner, which
  lives later in the DOM (inside `.gl-page`) and so painted over the top bar's
  open dropdown menu. The top bar is now `calc(var(--z-sticky) + 10)` so its
  menus open above the status strips.
- **User Info on slow/offline networks.** The request timeout dropped 30s → 12s
  and no longer retries, so a hung request stops holding the `_infoLoading` lock
  (which previously made further clicks do nothing / "modal won't open"). The
  error state now renders a **Retry** button instead of a dead-end message.

## [2026.7.3.post50] - 2026-07-13

### Fixed
- **Opening a modal no longer jerks the page to the right.** The scroll lock set
  `.gl-page-content { overflow: hidden }`, which stops it being a scroll
  container - so its `scrollbar-gutter: stable` reservation is released and the
  content widens/shifts right by the gutter width. `_refreshBodyScrollLock` now
  measures that gutter (`offsetWidth - clientWidth`) BEFORE locking and preserves
  it as `padding-right` (`--gp-lock-gutter`) while a modal is open, so nothing
  moves. Safe across stacked modals (measured once, on the first lock) and reset
  on the last close. Verified the entrance keyframes (`modalSlideUp`,
  `gp-content-in`, `gp-fade-in`) are vertical-only, so there is no other
  horizontal component.

## [2026.7.3.post49] - 2026-07-12

### Added
- **`GP.collapseAndRemove(el, cb)`** - a shared helper (alias of the existing
  `collapseBanner`) so any single element removed WITHOUT a full list re-render
  collapses smoothly (height + fade) instead of vanishing, reduced-motion aware.

### Changed
- The dashboard **course card** now collapses smoothly when removed (was
  fade-then-snap-gap), via `GP.collapseAndRemove`, keeping the empty-section
  update in the callback.
- Audited the removal sites: most (analysis cards, admin-course rows, welcome
  tour, sync-stream cards) already had exit animations, so the motion system is
  consistent; only the course card lacked a collapse. Table `<tr>` removals keep
  fade (rows can't animate height reliably).

## [2026.7.3.post48] - 2026-07-12

### Changed
- **Component-level button interaction states.** Every `.btn` now has a subtle
  tactile press (`:active` translate+scale) and a shared success/error feedback
  flash (`GP.flashButton(btn, 'success'|'error')` → `.gp-btn-success` pulse /
  `.gp-btn-error` shake), all reduced-motion aware. The shared process-action
  failure path (Run Checks / Sync across course/team/project) now flashes the
  button on error. Applied through the button component so it is consistent
  app-wide rather than per-page.
- Verified the rest of the motion system is already consistent: toasts have a
  proper `toast-dismissing` exit animation, dropdowns use Alpine enter/leave
  transitions, and modals use the post47 inertia swipe-to-dismiss. The remaining
  per-element exit-animation polish continues iteratively on top of this.

## [2026.7.3.post47] - 2026-07-12

### Fixed
- **User Info modal shows archived/inactive state.** Courses and groups in the
  User Info modal never indicated that they were archived/inactive. The info API
  now passes `is_active` / `course_active` / `team_active`, and
  `user-info-modal.js` renders a muted "Archived" badge on those cards.
- **Mobile modal swipe-to-dismiss now has inertia.** Dragging a bottom sheet down
  past the threshold used to reset the transform to 0 and replay a canned
  slide-down (a jump/blink). It now continues the sheet off-screen from the
  finger position with an easing transition (`.sheet-dismissing` suppresses the
  `modalSlideDown` keyframe; the backdrop still fades).
- **Calendar "Wk" column no longer blank.** Without a semester anchor (e.g. the
  create-course modal before a start date is picked) every week cell was empty,
  which read as broken. It now falls back to the standard ISO-8601 week number,
  and switches to semester weeks (1..N, then S1..) once an anchor exists.
- **User Info avatar** is top-aligned (was vertically centered against a tall
  identity block, leaving it looking cramped) and can no longer be shrunk.

## [2026.7.3.post46] - 2026-07-12

### Changed
- **Unified top-banner style + dismiss.** All page-level status strips now
  render through a single `top_banner` macro (`.gp-top-banner`) styled globally
  in `health.css`, so the archived, "Data may be outdated" and stale-data strips
  look identical (flush GitLab-style strip: icon + message + optional action +
  dismiss) instead of three different card/alert shapes. Each carries a dismiss
  (X) that persists across navigation, reload and other tabs via the shared
  `gp:dismissedBanners` store (the dismiss handler + `_hideDismissedBanners` were
  generalized from `.info-card` to `.gp-top-banner`; the portal skips
  already-dismissed strips). The slot caps at `50vh` and scrolls when many strips
  stack, so a burst never takes over the screen. The banner CSS moved from the
  course-only stylesheet into the global bundle so the mechanism works on every
  page, not just course pages.

### Fixed
- **Stale semester presets.** The "Quick preset" dropdown offered past semesters
  (Winter/Summer 2025/2026, now ended). `get_presets()` now drops any preset
  whose `end_date` is before today, leaving only the current + upcoming
  semesters.

## [2026.7.3.post45] - 2026-07-12

### Changed
- **All page-level status banners now consolidate into the global top strip.**
  Generalized post44's archived-banner portal into a reusable mechanism: any
  banner marked `.js-top-banner` (with an optional `data-banner-key` for
  dedup) is portaled by JS (`_portalTopBanners`) into `#globalBannerSlot` at the
  top of the page, stacking flush with the job bar and connection/health banner
  like a GitLab broadcast bar. Applied to the **"Data may be outdated"** card
  (course overview) and the **stale-data** banner (analytics + activity), on top
  of the archived strip. They are hidden in their content origin
  (`.js-top-banner:not(#globalBannerSlot *)`) until portaled - no flash - and
  keep their natural flex layout in the slot, just losing margin/radius so they
  read as flush strips.
- Element-scoped empty states ("not synced yet", "repository is empty") are
  deliberately NOT marked, so they stay in place - they describe a specific
  element, not global page status.

## [2026.7.3.post44] - 2026-07-12

### Changed
- **Archived-course banner moved to the global top status strip.** The
  "Archived course · read-only" notice sat inline below the course title. It now
  renders as a flush, full-width GitLab-style strip at the very top of the page,
  stacking together with the background-job bar and the connection/health banner
  (one shared status area) instead of being scattered. The strip is rendered in
  the (lazily-loaded) course content with full context, then JS portals it into
  a global slot (`#courseArchivedSlot`) in `base.html` right under the health
  banner; it is hidden in its content origin until portaled so there is no
  flash. The read-only guard still keys off `.tabs-nav[data-course-archived]`, so
  moving the visual strip does not change behaviour.
- The strip is now static (no card border/radius, no entrance animation) - a
  plain amber top strip. Contextual notices (stale-data above charts, "not
  synced yet" empty states) intentionally stay in place; they describe specific
  content, not global page status.

## [2026.7.3.post43] - 2026-07-12

### Added
- **Job History bulk management.** Each operations-log row now has a checkbox
  (plus a select-all header) and a "Delete selected" action that removes the
  chosen rows by id (`/jobs/delete`) - background jobs and audit operations
  alike. Synthetic rows (archive derived from a course's `archived_at`, not a
  stored log row) get a disabled checkbox and are skipped.
- **Purge by age.** "Purge Old" is now a dropdown: older than 24 hours, 7 days,
  30 days, or Everything.

### Fixed
- **Purge Old now clears operations, not just jobs.** It only deleted
  `BackgroundJob` rows, so the visible audit operations (deletes/imports/
  restores) never cleared - the reported "Purge Old stopped clearing". The purge
  endpoint gained a `scope` (`jobs`/`operations`/`both`, default `both`) and now
  removes old audit operations too.
- **Archived courses now show their archival.** A course archived before the
  `course.archive` audit-write existed had no audit row, so neither Job History
  nor "Follow the latest updates" showed it was archived. Both now synthesize a
  "Course archived" entry from `Course.archived_at` (skipping courses that
  already have a real audit row).
- Verified: no dead code remains for the removed features (gaming, rubric,
  assignments) - all references are already gone; the only "assignment" hits are
  legitimate (support-ticket assignment, issue-assignment R01, MR assignees).

## [2026.7.3.post42] - 2026-07-12

### Added
- **Job History is now a complete operations log.** It listed only background
  jobs (sync, checks, enrichment, metrics), so synchronous admin actions -
  course/group create, import, archive, delete, restore, settings, support,
  events - showed in "Follow the latest updates" but were silently absent from
  Job History. The admin jobs endpoint now merges those non-job audit actions
  in with the background jobs (same row shape: status `completed`, no duration,
  not cancellable), while excluding job-like audit actions (sync/checks/...) that
  already exist as `BackgroundJob` rows so nothing double-lists. This is why an
  empty prod Job History still showed the delete + imports in the feed only -
  now both surfaces agree.

## [2026.7.3.post41] - 2026-07-12

### Fixed
- **Auto-archive now shows in "Follow the latest updates".** When a course
  auto-archives (or a teacher archives one by hand) the dashboard feed stayed
  silent - `archive_course` wrote no audit entry, and even if it had, the feed
  scoped the archived course out because it was no longer active. Archiving now
  writes a `course.archive` activity entry attributed to the actor, and the feed
  keeps recently-archived course ids in scope so the entry actually surfaces.
- **Import course from JSON: a failed apply no longer dies silently.** The apply
  handler awaited `onApply` without a `catch`, so a rejected API call surfaced
  only as an unhandled promise rejection in the browser console. It now shows a
  clear error toast. (The `content.js ... message port closed` message some users
  saw is a browser extension, not GitPulse.)
- **Activity feed actor names.** The course-config seed actor now reads as
  "Course import" instead of the raw lowercase `auto-import` machine name, like
  the other machine actors (System, Scheduler, Background worker).

## [2026.7.3.post40] - 2026-07-11

### Fixed
- **Auto-archive now actually archives.** post38 enqueued the sweep to a worker
  job (fork + `asyncio.run` + engine re-init) that could quietly leave nothing
  archived. The dashboard now runs the sweep INLINE in its own throwaway session
  (`archive_due_courses`), throttled ~once/15 min via a Redis lock that is
  released on failure so the next load retries. So ended courses (past
  end + grace, not opted out) archive on the next staff dashboard load.
- **Profile skeleton avatar no longer double-loads.** The skeleton showed the
  real photo AND the loaded content showed it again - two avatar requests per
  open whose fallback/watchdog handlers raced and re-swapped when the shell's
  guessed URL differed from the DB avatar. The skeleton now shows the initials
  placeholder; the real photo loads exactly once with the content.
- **Commit History badges** ("Merge commit" / branch) now hug the message
  instead of floating far right with a big centre gap.
- **Archived Courses card** (dashboard) got bottom breathing room and its
  actions wrap instead of overflowing.

### Changed
- **Archived-course read-only banner is now a slim GitLab-style strip** at the
  top of the course tabs, not a big alert card.
- **Commit History branch filter** is now the app's animated dropdown component
  (glFormSelect) instead of a native `<select>`.

- Version `2026.7.3.post40`; Service Worker cache `gitpulse-v311`.

## [2026.7.3.post39] - 2026-07-11

### Added
- **Archived courses are now viewable (read-only).** The dashboard "Archived
  Courses" list gained a **View** button that opens the course. Every course tab
  (overview / settings / activity / analytics / teachers) shows a read-only
  banner - "This course is archived, archived on <date> ... Reactivate it to make
  changes" - with a Reactivate shortcut for staff.
- **Archived courses are genuinely read-only.** Course-scoped mutations (course
  sync-all, course & group run-checks, group sync, settings save, group
  creation) are rejected server-side with a clear 409 while the course is
  archived; the guarded action buttons are disabled and dimmed client-side.
  Reactivation is unaffected.
- **Live read-only awareness.** A course page polls its status (~1/min) and, if
  the course is archived in another tab or by another user, flips to read-only
  without a manual refresh; any action attempted meanwhile returns the same
  "archived" message.

### Fixed
- The dashboard archived-courses list no longer only offered Re-activate/Delete
  with no way to actually open an archived course.

- Version `2026.7.3.post39`; Service Worker cache `gitpulse-v310`.

## [2026.7.3.post38] - 2026-07-11

### Fixed
- **Semester-end auto-archive actually runs now.** Course Settings shows an
  "Auto-archive due / Auto-archives <date>" badge and a "Skip automatic
  archiving" toggle, and the dashboard hints that ended courses will be
  archived - but nothing performed it since the scheduled sweep layer was
  removed (there is no cron/scheduler daemon). The sweep is back
  (`sweep_auto_archive.run_auto_archive_sweep`) and runs opportunistically: the
  staff dashboard enqueues it at most once per hour (Redis lock), and the worker
  archives every active course whose semester ended more than the grace period
  ago, unless the course opted out via "Skip automatic archiving". Idempotent
  and fire-and-forget - it never blocks or fails the dashboard. Reactivating a
  course still opts it out of the next sweep, so an archive is easily reversible.
- Dashboard hint copy is now truthful: an auto-enabled ended course reads "being
  auto-archived"; an opted-out one reads "auto-archive is turned off - archive
  manually".

- Version `2026.7.3.post38`; Service Worker cache `gitpulse-v309`.

## [2026.7.3.post37] - 2026-07-11

### Fixed
- **An explicitly chosen theme no longer flips to the system theme on its own.**
  The client trusted the account's rendered `data-theme-preference` over the
  local choice. When the account was still on the ambiguous `system` default
  (never overridden server-side, or an earlier persist POST failed) while this
  browser held an explicit `light`/`dark`, a reload re-resolved to `system` and
  followed the OS - so an explicit dark could switch to light by itself. The
  bootstrap now keeps a local explicit choice over a server `system` default and
  reconciles the account (re-persists) once the DOM is ready. An explicit
  `light`/`dark` set on another device still syncs across devices as before.

- Version `2026.7.3.post37`; Service Worker cache `gitpulse-v308`.

## [2026.7.3.post36] - 2026-07-11

### Fixed
- **A week with no expected checks no longer shows 100%.** The weekly compliance
  score for a week before the curriculum introduces any check was stored as a
  vacuous `1.0` (nothing to fail = "100%"), so the Weekly Breakdown showed e.g.
  Week 1 = 100% while its heatmap row was all-N/A. Such weeks now render as N/A
  ("-") for the overall score AND every category, and are skipped by the trend
  line - consistent with the heatmap. Applies to existing and future data (the
  fix is in the history serialiser, keyed off `checks_total == 0`).
- **The Profile skeleton avatar now matches the loaded avatar.** During the
  skeleton phase the avatar was a bespoke initials circle; when the content
  loaded it swapped to the photo. The skeleton now renders the real avatar via
  the same shared `data-avatar-fallback` component the dashboard/topbar use
  (photo, falling back to initials on error/timeout), so there is no swap.

### Changed
- The theme-switch reveal is slower and gentler (440 ms -> 620 ms) so the
  full-screen wipe feels smooth instead of an abrupt snap.

- Version `2026.7.3.post36`; Service Worker cache `gitpulse-v307`.

## [2026.7.3.post35] - 2026-07-10

### Fixed
- **The course Teachers page no longer renders as a dead shell.** Its page
  script (`course-teachers.js`) declared `const GP` at the top level, which
  collided with the global `const GP` that `core.bundle.js` already declares -
  `SyntaxError: Identifier 'GP' has already been declared`. A parse error aborts
  the WHOLE file, so `teacherManager()` was never registered and every Alpine
  expression on the page failed (`Undefined variable: teacherManager`, `search`,
  `visibleTeachers`, ...), leaving an empty broken page. The script is now wrapped
  in an IIFE like every other page script, so its `GP` binding is function-scoped.
- Added a regression test that fails if any `pages/*.js` script declares `GP` at
  global scope, so this class of "one bad script kills the page" cannot recur.

- Version `2026.7.3.post35`; Service Worker cache `gitpulse-v306`.

## [2026.7.3.post34] - 2026-07-10

### Fixed
- **The page no longer looks stuck loading after it has fully rendered.** When an
  avatar host black-holed the connection (TUKE VPN down, GitLab unreachable), the
  `<img>` fired neither `load` nor `error` and stayed pending forever, so the
  browser tab kept its loading spinner spinning even though every bit of page
  content was already on screen. Avatars now have an 8 s load watchdog: on expiry
  the request is aborted and the initials fallback is shown, so the tab stops
  spinning. Off-screen lazy avatars are only armed once they scroll into view, so
  a slow-but-working avatar is never degraded prematurely.
- **Compliance history is now immutable.** Backfill used to recompute every past
  week from the *current* database state and upsert over it, so when GitLab data
  was later deleted (a branch or MR removed) a re-sync silently rewrote a
  student's historical score downward. Backfill now only fills weeks that have no
  snapshot yet; a week that was already recorded stays as it was.
- **No more phantom "Week 21" after the semester ended.** Weekly compliance
  snapshots are capped at the teaching window (a live recompute past the last
  teaching week no longer writes a W14..W21 row), the Week Analytics exam-period
  now closes via an effective end date when no explicit end is set, and both the
  course trend line and the student trend/heatmap/radar clip weeks past the
  window - so stale post-semester rows never plot.
- **Faster pages: pruned the redundant `metric_snapshots` backlog** (migration
  010). post33 capped future growth but left ~480k historical duplicate rows
  (prod had 506k), the real cause of the intermittent multi-second page loads.
  The migration keeps the newest row per (team, student, UTC week) and deletes
  the rest - the same row the going-forward dedup keeps, so the latest score is
  unchanged.
- **Charts are readable on the light theme.** The compliance donut, the Skill
  Profile radar tooltip, and several bar/line tooltips and grid lines were
  hardcoded to a dark surface / near-white grid, which rendered dark-on-dark or
  invisible on the light card. They now take their colours from the shared,
  theme-aware Chart.js defaults.
- **Student page polish.** The loading skeleton now matches the loaded MR cards,
  profile card and section headers 1:1 (real avatar initials + name while
  loading, no phantom divider, correctly-sized bars); the Commit History table
  keeps the "Merge commit" / branch badges in fixed columns instead of drifting
  with message length.
- **Compliance Checks: "Total Active Weight" restructured** from a bare table
  footer row into a dedicated summary band below the table.
- **Smaller UI fixes:** the top navigation progress bar no longer sweeps
  backwards while fading out; a guarded (dirty-check) modal Save button is no
  longer briefly clickable for ~120 ms when the modal opens; the Run Checks check
  boxes' focus outline is no longer clipped at the grid edges.

### Changed
- The dashboard "semester ended" hint no longer implies an automatic archive job
  exists (there is no scheduler; archival is manual) - the wording now says so.

- Version `2026.7.3.post34`; Service Worker cache `gitpulse-v305`.

## [2026.7.3.post33] - 2026-07-08

### Fixed
- **Compliance snapshots no longer grow without bound (slow pages).** Every sync /
  Run Checks INSERTed a brand-new `metric_snapshots` row per student - the unique
  key carries `computed_at`, so nothing ever deduped. Production had **506k rows,
  ~882 per student**, which pushed the per-group "latest snapshot per student"
  aggregate to **1.2 s** (x8 groups on a course page) and made the student page
  load 800+ history rows. A recompute now keeps exactly **one snapshot per
  (team, student, ISO week)**: it deletes the rows it is about to supersede -
  scoped to the same team, the same week, and only the students being recomputed,
  so a partial recompute never drops another student's week - then writes the
  fresh ones in the same transaction. Current score (latest row) and the weekly
  history chart are unchanged.

## [2026.7.3.post32] - 2026-07-08

### Fixed
- **"Follow the latest updates" no longer reports every scope as a whole-group
  action.** A course-wide Run Checks fans out into one `run_checks` job per group,
  and only *sync* bursts were aggregated - so the feed listed each group's check
  separately and read like the whole group ran repeatedly. Run-checks bursts are
  now folded into a single "Ran checks for N groups" entry (same 5-minute
  clustering as "Synced N groups"), and a project-scoped run now says "Project
  checks completed" instead of the generic label with the group's name attached.

## [2026.7.3.post31] - 2026-07-08

### Fixed
- **No more phantom "Sync completed!" toast when running checks.** On the course
  page, a Run Checks recompute emits an SSE `update`; the sync-stream saw no sync
  work but a stale `_syncWasActive` flag still fired `_completeCourseSync()` → a
  "Sync completed!" toast even though no sync ran. The terminal sync toast is now
  gated on a new `_sawRealSyncRunning` flag that is only set when a poll/SSE tick
  actually observes a sync running/finishing, and reset on completion.
- **Removed the duplicate "Data updated" info toast** after a job completes - the
  global job bar already shows the terminal "Sync completed!" / "Checks completed"
  toast, so the extra one just stacked a second toast on every sync/import/run.

## [2026.7.3.post30] - 2026-07-08

### Fixed
- **Student page loading skeleton now includes the email row** in the profile
  identity block (mail icon + address), matching the loaded page for teachers/
  admins (`can_edit`). It was the one identity field missing between the username
  and the "View on GitLab" link, so the header shifted slightly when real data
  arrived.

## [2026.7.3.post29] - 2026-07-08

### Added
- **"Run Checks (all groups)" now shows a per-group "Recomputing..." badge** on
  each group row while the recompute runs, so the course page gives visible
  per-row feedback like a sync does (previously only the global progress bar
  moved). The badges clear when the rows refresh on completion.

## [2026.7.3.post28] - 2026-07-08

### Fixed
- **R09 (MR Approved) no longer drops to a false FAIL after an MR merges** -
  this was silently lowering compliance scores across all merged MRs. GitLab
  clears an MR's `/approvals` list once it merges and its branch is deleted, so a
  later sync overwrote the stored approvals with 0; with `min_approvals >= 2`
  every merged MR then failed R09 (e.g. a student went 0.860 -> 0.825, and group
  averages fell). R09 now counts distinct approvers from the **permanent
  "approved this merge request" system notes** (union the live list, netting any
  later "unapproved" note) - these survive the merge, so scores stay correct and
  are immune to the post-merge clobber. Re-run checks / sync to restore affected
  scores. Regression tests added.

## [2026.7.3.post27] - 2026-07-08

### Fixed
- **Student page skeleton now matches the loaded page 1-to-1.** The Compliance
  Progress loading state was badly out of sync: the Score Trend was a tiny bar in
  a large empty box, the Skill Profile was a bare circle, and the "Check Progress
  by Week" heatmap + the threshold pills + the week-over-week summary stats were
  missing entirely. The skeleton now fills the Score-Trend chart box, renders the
  threshold pills, a radar placeholder with the week label and the
  Current-Score / vs-Last-Week / Weakest-Area summary, and the full R01-R13 x
  weeks heatmap.
- **Global job bar shows exactly one trailing control** instead of two ambiguous
  X's: a running job shows the cancel-X (which confirms before stopping the
  process); a finished/failed job shows a dismiss-X to close the bar. Applied
  consistently in both the full render and the in-place update.
- **Top progress bar no longer fires twice on a slow navigation.** The
  network-activity reconciler used to force-finish the bar (snap to 100% + clear
  the persisted hand-off state) during a full-page navigation - which has no
  fetch in flight - so the destination page popped a brand-new bar from zero. It
  now skips finishing while a navigation is in progress, so one continuous bar
  spans the old page -> new page.

## [2026.7.3.post26] - 2026-07-07

### Removed
- Stripped the inert "scheduled / maintenance jobs" panel shell that survived
  the post24 job removal. The jobs grid was no longer rendered, so this was dead
  scaffolding: removed the admin endpoints (`/jobs/trigger`, `/jobs/retry`,
  `/scheduled-jobs`, `/jobs/active-scheduled`), the empty `admin_scheduled_registry`,
  `run_tracked_scheduled` + `sweep_tracking`, and the front-end trigger/poll/SSE
  code in the admin-system bundle (kept the live background-job history table,
  cancel, health, cache and stats). The now-useless per-row "Retry" button was
  removed with its dead endpoint.

### Changed
- `custom_check` schema: extracted the shared `validate_rule_type` helper so the
  create/update validators no longer duplicate the rule-type check.

## [2026.7.3.post25] - 2026-07-07

### Added
- Project detail now distinguishes a **template/fork with no student commits
  yet** from a genuinely empty repository. When the repo has upstream
  (template-author) commits but no student has pushed their own work, the
  "Issues to Address" card shows a dedicated "Template / fork - no student
  commits yet" state (instead of the misleading "No repository data yet"), the
  Contributors card says "Only template authors so far", and the Commits stat
  renders " - " instead of a misleading "0". Detected consistently in both the
  full-page render and the live-data refresh (`student commits == 0` while total
  repo commits > 0). Slovak translations added.

## [2026.7.3.post24] - 2026-07-07

### Removed
- Removed the dead "scheduled / periodic sweep" job layer. There is no
  recurring scheduler and the admin maintenance-job catalog is empty, so these
  jobs could never fire and were only reachable (if at all) by retrying an old
  failed row: `periodic_llm_analysis`, `periodic_telemetry_snapshot`,
  `sweep_dlq_auto_resurrect`, `cleanup_old_events`, `cleanup_old_email_logs`,
  `sweep_email_queue`, `sweep_auto_archive_ended_courses`,
  `sweep_unprocessed_events`. Deleted their modules (`sweep_jobs`,
  `sweep_cleanup`, `sweep_maintenance`, `sweep_events`) and the periodic
  functions in `sweep_telemetry`, plus the now-orphaned `_delete_in_batches`
  helper, the `_FEATURE_FLAG_MAP` entries, the activity-feed `scheduled:*`
  labels, and the admin retry legacy map. Updated the tests accordingly.
- The **event/sync-driven** jobs are unchanged and still enqueued directly:
  `refresh_project_gitlab_intel` (webhook intel refresh),
  `sync_single_team_members` (push member sync), and
  `telemetry_snapshot_for_team` (post-team-sync snapshot). Email delivery is
  unaffected - `enqueue_email` enqueues `deliver_email` directly.

### Note
- Recovery paths that only the deleted jobs provided (DLQ auto-resurrect, event
  retention cleanup, orphan/unprocessed-event replay, email-send retry) were
  already non-functional without a scheduler; a manual re-sync pulls current
  state, so no data is lost. The (now empty) admin maintenance-panel shell
  remains inert and can be removed in a follow-up.

## [2026.7.3.post23] - 2026-07-07

### Fixed
- The brand logo's ECG-pulse animation no longer jumps backward along the trace
  when the cursor leaves it. Hovering used to swap the pulse `animation-duration`
  (3.8s -> 0.95s); reverting it on mouse-leave re-mapped the animation's elapsed
  time onto the longer timeline, snapping the moving segment back toward the start
  of the trace. Hover now only brightens/glows the pulse at a constant speed, so
  it continues smoothly from wherever it was.

### Changed
- Renamed `app/workers/sweep_ci.py` -> `app/workers/sweep_events.py`: the file was
  a leftover name from the removed CI-failure feature but now only holds the
  generic webhook-event recovery sweep (`sweep_unprocessed_events`). Pure rename -
  the `app.workers.sweep.*` RQ string paths still resolve via the re-exports.
- Removed references to the three deleted sandbox features from the current docs
  (API spec, data model, requirements, rollout, teacher-checklist mapping,
  architecture tree, developer structure/testing pages, API index). Historical
  CHANGELOG/archive, thesis narrative, and migration-history pages are unchanged.
- Version `2026.7.3.post23`; Service Worker cache updated to `gitpulse-v294`.

## [2026.7.3.post22] - 2026-07-07

### Removed
- Removed three unused sandbox features entirely (they were feature-flagged off
  by default and never enabled in production, with zero rows in their tables):
  the **git conflict simulator**, the **Docker build verification** module, and
  the **CI-failure scenario generator**. Deleted their services, workers, models,
  API routes, templates, JS (`_parts` + rebuilt bundles), feature flags and
  orphan i18n strings; the course-settings config columns and the (empty) feature
  tables are dropped by new migration `009_drop_sandbox_features` (idempotent
  `IF EXISTS`). No behaviour change for users - nothing referenced these in prod.

### Changed
- Version `2026.7.3.post22`; Service Worker cache updated to `gitpulse-v293`.

## [2026.7.3.post21] - 2026-07-07

### Fixed
- The "Issues to Address" empty-state card no longer vanishes a second after
  load. On a live-data poll where the server can't determine the repo state it
  returns an empty `issues_html` (by design: "keep the current card"), but the
  client's legacy fallback path then hid the card with `d-none`. Removed that
  dead legacy path - the persistent server-rendered empty state now stays.
- Reverted the stale-while-revalidate lazy-content cache (post19/post20). It
  painted the last-seen content on refresh, but after a background sync it showed
  stale/empty content and flickered ("appears then disappears", "nothing shows
  after sync"). Pages now always render fresh from the server (a brief skeleton
  on refresh is the trade-off), so displayed data is always correct and never
  disappears. Stored data (members / contributors / stats) renders from the DB
  snapshot regardless of GitLab token state.

### Changed
- Version `2026.7.3.post21`; Service Worker cache updated to `gitpulse-v292`.

## [2026.7.3.post20] - 2026-07-06

### Fixed
- The lazy-content refresh cache (post19) now actually engages. The cache-write
  step rejected any page whose real content contained a nested client-filled
  skeleton (charts, analysis cards, ...), so the page was never cached and F5
  kept flashing the full-page skeleton. At `htmx:afterSwap` the content is always
  the real server response (the initial skeleton is already gone), so that guard
  was wrong - removed it.

### Changed
- The "GitLab token invalid" item in "Items that need your attention" now links
  to the token docs (`/docs/gitlab/tokeny/`) explaining how to rotate it, instead
  of System Settings - the token is a server env var, not an in-app setting, so
  System Settings could not fix it.
- Version `2026.7.3.post20`; Service Worker cache updated to `gitpulse-v291`.

## [2026.7.3.post19] - 2026-07-06

### Changed
- Lazy-loaded dashboard pages now paint **instantly** on a refresh / return
  instead of flashing the loading skeleton every time. A stale-while-revalidate
  cache (`_parts/core/50-lazy-content-cache.js`) stashes the last-seen rendered
  content per URL in `sessionStorage` (per-tab, memory-only - never written to
  disk, matching the `no-store` policy on `/dashboard`) and repaints it the
  instant the page loads, while htmx fetches fresh content in the background and
  swaps it in. Applies to every `.gl-lazy-content[hx-trigger*="load"]` page
  (course / team / project / student / dashboard / admin). The entrance reveal is
  suppressed on the revalidation swap (via `data-swr-painted`) so there is no
  double-reveal flash; cache entries are size-capped and 10-minute TTL-bounded.
  This is the client-side answer to "F5 re-runs everything" - `/dashboard`
  responses stay `no-store` (auth-page security) so the server never caches them.
- Version `2026.7.3.post19`; Service Worker cache updated to `gitpulse-v290`.

## [2026.7.3.post18] - 2026-07-06

### Fixed
- The student page no longer makes live GitLab calls while rendering. It fetched
  up to 12 pipeline coverage details + a user-avatar lookup on every load, which
  stalled the page (and hung on an expired 401 token). It now renders purely from
  stored data - coverage is filled by sync + webhooks and reused from the existing
  SHA-based DB fallback; the avatar comes from the stored value or the URL-pattern
  fallback. Data reaches every page only via sync + webhooks, never a render-time
  API call.
- The teachers tab and the admin user-detail page dropped their render-time GitLab
  avatar fetches too (same fix). Project milestones, releases and labels are now
  captured during sync into the stored snapshot and served from it, instead of a
  live GitLab call on demand - so every page path is snapshot-only.
- "Follow the latest updates" now shows FAILED jobs (e.g. a sync blocked by an
  invalid token). The feed queried only `completed` jobs, so every failure was
  hidden; failed jobs now appear with an alert icon and a "... failed" label.
- The Course Settings sticky action bar no longer leaves a thin lighter strip at
  the very bottom - it compensated an 8px page padding, but `.gl-page-content`'s
  bottom padding is 12px, so the last ~4px showed through. Now compensated to 12px.

### Added
- "Items that need your attention" surfaces an "invalid GitLab token" item when
  the token is rejected (read from the shared cached health flag - no live probe
  on render), linking to System settings so it can be updated quickly.

### Changed
- Version `2026.7.3.post18`; Service Worker cache updated to `gitpulse-v289`.

## [2026.7.3.post17] - 2026-07-06

### Fixed
- The group / project **Sync** button no longer gets stuck disabled with no
  cooldown timer after a failed sync (e.g. an expired 401 token). Root cause: the
  sync registers a global job, and completing that job with an error fired the
  process-lock release (`unlockElement`), which **cleared the anti-spam cooldown
  that had just been applied** - so the countdown vanished and the button could
  be left blocked. `unlockElement` no longer clears an active cooldown, and no
  longer re-enables a button a cooldown is still holding. The countdown now
  survives and the button self-recovers on every page (the course page only
  escaped the bug via its early token-return, which never registers a job).
- Sync-failure messaging is now consistent across course / group / project. A
  shared `GP.syncErrorMessage(err)` returns the detailed "GitLab API token is
  invalid or expired (401)..." text on a 401 (already translated) instead of the
  bare "Sync failed" that the group / project pages showed while the course page
  showed the full reason.

## [2026.7.3.post16] - 2026-07-06

### Fixed
- Project sync wrongly reported "Group sync completed" on success - it now says
  "Sync completed", matching the entity being synced (group vs project).
- The top loading strip no longer stays pinned at 100% when a new request begins
  during its fade-out. `start()` now resumes a finishing bar as one continuous
  indicator instead of leaving it stuck at the end and then popping a fresh bar.

### Changed
- The "Data may be outdated" webhook/staleness banner is no longer duplicated on
  the group (team) page - it is a course-level notice and already shown on the
  course page.
- Group sync stripped of its dead sync-modal code. That modal was removed from
  the templates long ago (the global job bar owns all sync UI now), so its
  `getElementById` calls were no-ops; group sync is now bar-only like project
  sync and both use the same generic "Sync completed" / "Sync failed" messages.
- GitLab intelligence panels (protected branches, contributors, repository
  statistics, milestones, releases, labels) are now under HTTP caching. Their
  responses carry `Cache-Control: private, max-age=300` + a content-derived
  `ETag`, and the project page revalidates them with a conditional request
  (`cache: no-cache`) instead of the old `no-store` full re-download - so an
  unchanged snapshot returns a bodyless `304` and repeat visits/refreshes come
  from the browser cache.
- Version `2026.7.3.post16`; Service Worker cache updated to `gitpulse-v287`.

## [2026.7.3.post15] - 2026-07-06

### Fixed
- The Sync / Run Checks button no longer freezes on "Wait 1s" after a failure on
  the team, project and per-group pages. Root cause: a race between the anti-spam
  cooldown and `setButtonLoading` over `dataset.originalText` when a request fails
  fast (< 400 ms, i.e. a 401 token rejection) - the deferred min-visible-duration
  reset fired mid-countdown and deleted the saved label, so the cooldown could not
  restore the button and it stuck on the last painted "Wait 1s". The course page
  escaped it only via its early token-guard; every other page went through the
  racing path. Fixed in the shared core (a dedicated cooldown-owned label slot +
  `setButtonLoading` now yields to an active cooldown), so it is fixed on every
  page at once.
- The failure cooldown countdown now shows on every sync trigger (course Sync All,
  per-group sync, team sync, project sync) and their streamed-failure paths, not
  just some buttons.

### Changed
- Banners (the "Data may be outdated" / GitLab-token / sync-failed cards) now ease
  open and closed (animated height + opacity) instead of popping in and shoving
  the page content down. A dismissed banner now STAYS dismissed across tab
  switches, page reloads and other browser tabs (persisted in `localStorage` and
  pruned live cross-tab), instead of reappearing.
- Data tables now follow the official GitLab Pajamas table spec 1:1: header and
  body cells both use 16px (`gl-p-5`) padding, and the condensed variant is exactly
  half (8px).
- With the app open in several tabs, a single visible "leader" tab now owns the
  sync pollers / SSE streams (fail-open `localStorage` lease); the other tabs
  mirror job state via storage events. This removes duplicate `/sync/active`
  requests, out-of-step progress bars and duplicate completion toasts across tabs.
  A lone tab always leads, so a single tab is never affected.
- Version `2026.7.3.post15`; Service Worker cache updated to `gitpulse-v286`.

## [2026.7.3.post14] - 2026-07-04

### Fixed
- Anti-spam button cooldown no longer hangs on "Wait 1s". The countdown tick now
  self-heals - when the time is up the 200 ms tick itself clears the cooldown
  and restores the button, so a lost/throttled `setTimeout` can never leave the
  button pinned on "Wait 1s".
- "Wait" is now translated (Slovak `Počkajte`), so the cooldown countdown is no
  longer English-only on the Slovak UI.
- The failure cooldown now covers every Run Checks button (course / team /
  project all run through the shared `runScopedChecksProcess`), consistent with
  the Sync buttons, instead of appearing on only some buttons.

### Changed
- Version `2026.7.3.post14`; Service Worker cache updated to `gitpulse-v285`.

## [2026.7.3.post13] - 2026-07-04

### Fixed
- Top loading strip: a fundamentally different, bulletproof fix. Instead of
  chasing every way the event-driven `pending` counter can get stuck (prevented
  submits like Import-with-empty-URL, missed/duplicated htmx events, clicks that
  start a "navigation" that never navigates), the bar is now reconciled against
  REAL network activity. `window.fetch` and `XMLHttpRequest` are wrapped so a
  request-lifecycle counter (`.finally` / `loadend` always fire) tracks what is
  genuinely in flight; a 250 ms reconciler finishes the bar ~1.2 s after the
  last real request completes, regardless of what the fragile event counter
  believes. The 120 s stuck-timeout is now only a last resort.

### Changed
- Version `2026.7.3.post13`; Service Worker cache updated to `gitpulse-v284`.

## [2026.7.3.post12] - 2026-07-04

### Fixed
- Sync / Run Checks button now frees itself WITHOUT a page refresh. The
  staleness/ghost-expiry guard lived in a timer that only ran while a job was
  VISIBLE in the bar; a hidden ghost (deduped, or one that only locks the button
  via process-guards) never got expired, so the button stayed locked until a
  manual refresh. The guard now runs while ANY job exists in `_globalJobs`. A
  ghost with no real backend `job_id` (and not server-confirmed, no fresh SSE
  heartbeat) is retired ~15 s after load; team/project syncs no longer inherit
  the 45-min course maxAge cap.
- Top loading strip no longer hangs at ~99 %. `.gl-lazy-content` requests are
  counted exclusively by the lazy bridge; a DCL-ordering race let the generic
  htmx handler increment a lazy request before it was tagged, then skip the
  matching decrement - leaving `pending` stuck +1 and the bar pinned for the
  full 120 s stuck-timeout. The generic handler now skips lazy elements outright.
- Status-strip appearance is smoother: the job bar's grow-in target height was
  lowered so the `max-height` transition spans the animation instead of finishing
  in the first frame.

### Changed
- Cross-tab toasts are suppressed in background tabs, and queued completion
  toasts are de-duplicated by job.
- Version `2026.7.3.post12`; Service Worker cache updated to `gitpulse-v283`.

## [2026.7.3.post11] - 2026-07-04

### Fixed
- Sync / Run Checks button no longer sticks disabled on project & group pages
  (and any scope). The global job bar reconciled only COURSE-level ghosts
  against `/sync/active`; a team-/project-scoped sync ghost restored from
  localStorage was skipped, so it kept the button process-locked for its full
  maxAge (up to 45 min) even when the server reported nothing active - and it
  survived refreshes because localStorage persists. Reconciliation now covers
  team/project sync ghosts too (matched by their owning course), so a stale
  ghost is dropped everywhere. (Complements the post10 optimistic-"connecting"
  cleanup, which only handled the pre-POST phase.)
- Avatar fallback initials are no longer on a purple disc - the top-bar and
  dashboard-greeting avatars now use a neutral slate (`--gl-gray-700`).
- "Follow the latest updates" feed no longer loses entries. A background refresh
  (a) never replaces a populated feed with the "no activity" empty state (a
  transient builder hiccup or a brief quiet window used to wipe every visible
  row), and (b) preserves the "Show all" expand state instead of collapsing back
  to 5.
- Status strips no longer jolt the page when they appear. The global job bar
  eases open via a `max-height` `transition` + `@starting-style` (not a keyframe -
  the bar's deterministic removal contract is preserved), and the health banner
  grows in by `max-height` instead of sliding a full-height box in with
  `translateY`, so the content below makes room smoothly instead of snapping down.

### Changed
- Version `2026.7.3.post11`; Service Worker cache updated to `gitpulse-v282`.

## [2026.7.3.post10] - 2026-07-03

### Fixed
- Sync / Run Checks button no longer sticks disabled after a refused sync. The
  global job bar marks a click optimistically as a "connecting" job before the
  server confirms a run; when the sync is refused (invalid/expired GitLab token,
  401) or the page restored a stale pre-POST snapshot, that placeholder had no
  backend job behind it yet kept the button process-locked for the full 5-45 min
  staleness window - and inconsistently across project / team / course. The
  staleness guard now retires a "connecting" job that never got a real backend
  `job_id` after ~15s, so the button frees up quickly and identically on every
  scope. A genuine (even slow-queuing) sync always carries its `job_id`, so it is
  never affected.

### Changed
- Version `2026.7.3.post10`; Service Worker cache updated to `gitpulse-v281`.

## [2026.7.3.post9] - 2026-07-03

### Fixed
- Avatar fallback is now consistent across surfaces. The dashboard greeting
  avatar used the old pattern (photo over a grey disc with a hidden letter),
  so it diverged from the top-bar avatar (fixed in post6): one could flash an
  empty grey circle while the other showed the branded initial. The greeting
  avatar now uses the same layering - the initial is the always-present base
  and the GitLab photo overlays it - so both degrade identically.

### Changed
- Version `2026.7.3.post9`; Service Worker cache updated to `gitpulse-v280`.

## [2026.7.3.post8] - 2026-07-03

### Changed
- Reverted the persistent `#gitlabTokenBanner` that post7 added to the project
  and group pages. A bad/expired GitLab token no longer shows a standing banner
  there; the token error surfaces only when you actually run an action that
  needs it (Sync / Import), via the existing global progress bar + toast - one
  message, no standing clutter. (The project intel-card loading shimmer from
  post7 is kept.)
- Version `2026.7.3.post8`; Service Worker cache updated to `gitpulse-v279`.

## [2026.7.3.post7] - 2026-07-03

### Fixed
- Project & group pages now handle an invalid/expired GitLab token the same way
  the course page always has, instead of diverging:
 - A single persistent `#gitlabTokenBanner` explains the 401 once; the Sync /
    Run Checks buttons stay clickable rather than sticking disabled.
 - Clicking Sync with a known-bad token short-circuits (no doomed background
    job that left the button stuck "loading" and double-reported the error as
    both a job-bar banner and a toast) - it now surfaces one message.
- Project GitLab-intelligence cards (Protected Branches / Contributors /
  Repository Stats) show a loading shimmer while a live fetch is in flight,
  instead of flashing a premature "No contributors yet" empty state.

### Changed
- Version `2026.7.3.post7`; Service Worker cache updated to `gitpulse-v278`.

## [2026.7.3.post6] - 2026-07-03

### Fixed
- Health banner: the "GitLab server is currently unreachable" notice no longer
  reappears after you dismiss it (a successful app-health poll was silently
  clearing the dismissal flag it shared with the app-health banner), and its
  "Last connected" timer now ticks live instead of freezing at the value it had
  when first shown.
- Top-bar avatar degrades to the user's initials instead of flashing an empty
  grey disc while the GitLab profile photo streams in or when GitLab is
  unreachable.

### Changed
- Version `2026.7.3.post6`; Service Worker cache updated to `gitpulse-v277`.
- Verified workspace code quality, ran full unit tests suite, and completed final release consolidation checks.

## [2026.7.3.post5] - 2026-07-03

### Refactored
- Simplified member category assignment in `_members_table.html` to eliminate duplicating tree branch logic for excluded members (consistent with the team details view).

### Changed
- Version `2026.7.3.post5`; Service Worker cache updated to `gitpulse-v276`.

## [2026.7.3.post4] - 2026-07-03

### Refactored
- Combined and simplified redundant `empty_state` macro call trees in project detail sub-sections: `_docker_verification.html`, `_ci_scenarios.html`, and `_conflict_challenges.html`.

### Changed
- Version `2026.7.3.post4`; Service Worker cache updated to `gitpulse-v275`.

## [2026.7.3.post3] - 2026-07-03

### Refactored
- Cleaned up redundant legacy Jinja fallback loop in `_issues_to_address.html` template. Now uses python backend computed `scored_students` exclusively, reducing file complexity.
- Simplified member category assignment in `_detail_content.html` to eliminate duplicating tree branch logic for excluded members.

### Changed
- Version `2026.7.3.post3`; Service Worker cache updated to `gitpulse-v274`.

## [2026.7.3.post2] - 2026-07-03

### Refactored
- Extracted duplicate GitLab diff-tree button blocks within the student details component template (`student.html`) into a single Jinja2 macro `diff_file_tree_item`, reducing duplicate markup in recursive file-tree nodes and diff body lists.

### Changed
- Version `2026.7.3.post2`; Service Worker cache updated to `gitpulse-v273`.

## [2026.7.3.post1] - 2026-07-03

### Refactored
- Extracted duplicate GitLab evidence link blocks within the AI Teamwork Analysis page template (`_ai_analysis.html`) into a single Jinja2 macro `render_evidence_link`, eliminating duplicate blocks across Strengths, Potential Issues, and Teamwork Quality sections.

### Changed
- Version `2026.7.3.post1`; Service Worker cache updated to `gitpulse-v272`.

## [2026.7.3] - 2026-07-03

### Refactored
- Decomposed and refactored the entire Course Settings template layout into modular partial includes (`_basic_settings.html`, `_webhook_settings.html`, `_compliance_settings.html`, `_weekly_deadlines.html`, `_sandbox_settings.html`, `_ai_settings.html`, `_import_export_settings.html`). This reduced the main `course_settings.html` template code from 580 lines down to under 100 lines.

### Changed
- Version `2026.7.3`; Service Worker cache updated to `gitpulse-v271`.

## [2026.7.2.post17] - 2026-07-03

### Fixed
- Layout wrapping of the "Scope cascade" alert box in the Course Settings page, preventing narrow-width wrapping.

### Refactored
- Extracted "Semester Settings" layout sections into reusable Jinja macros and partial templates (`_semester_settings.html` and `_settings_form_macros.html`) to minimize duplicate markup.

### Changed
- Version `2026.7.2.post17`; Service Worker cache updated to `gitpulse-v270`.

## [2026.7.2.post16] - 2026-07-02

### Fixed
- Restored the green lint stage on `main` (the post15 commit failed CI): reformatted `projects.py` (and drifted `sweep.py` / `test_frontend_resilience.py`) with `ruff format`, and fixed a `member_sync_service.py` mypy error where a reused loop variable `tm` was assigned an `Optional` (now a dedicated `_existing_tm` narrows to the non-optional membership).
- Members table and Group Members table now show STUDENTS only - never teachers, mentors, or a Project Manager. The issue-activity cohort derivation could pull in a PM who authored issues, and inherited instructors rode along in the roster; both the project and team member lists now drop anyone flagged teacher/mentor on their team membership.
- The project header no longer shows the raw slug path (`.../api-7-ma-a-antypenko/mines-12770`). It renders a GitLab-style display path where the subgroup slug becomes the group's display name and the project slug becomes the project's display name (`... / ApI 7 (Maťaš - Antypenko) / Chekanov ... - Míny`).

### Changed
- Version `2026.7.2.post16`; Service Worker cache unchanged (`gitpulse-v269`) - backend + template change, no static-asset updates.

## [2026.7.2.post15] - 2026-07-02

### Fixed
- Course "Sync All" no longer shows a contradictory pair of toasts. The optimistic green "Sync started..." toast fired before the request resolved, so a refused sync (invalid token / GitLab offline) displayed "started" AND "failed" at the same time. The "Connecting to GitLab..." global-bar already signals the action began and resolves to progress or a single error - the premature toast is removed on both the course-detail and course-analytics paths.
- The project member cohort derivation now also counts issue participation (author / assignee / co-assignees), not just merge-request activity, so a teammate who opened issues but has not authored an MR yet is no longer dropped ("4 shown but 5 on the team").
- Issues to Address header now surfaces only the actionable High-priority count. The Medium/Low pills read as a meaningless faint number ("8"/"45") next to it; the chart and legend below already convey the full severity breakdown, so the extra pills were redundant clutter.

### Changed
- Version `2026.7.2.post15`; Service Worker cache `gitpulse-v269`.

## [2026.7.2.post14] - 2026-07-02

### Fixed
- Project detail and live refresh no longer fetch GitLab directly to decide members/statistics/contributors/protected branches. They read the stored `gitlab_intel` snapshot, derive older projects from stored MR activity, and refuse to fall back to the whole subgroup for multi-project teams. This prevents phantom students and wrong Issues-to-Address badges when the GitLab token is invalid or GitLab is offline.
- Manual project sync now upserts the project's GitLab members into the owning group before issues/MRs/notes are processed, so direct project members no longer disappear until a full group sync runs.
- Sync and Run Checks progress/error handling is shared across project, group, and course scopes: invalid-token/refused requests now finish as visible global-bar errors as well as toasts, and Run Checks uses one SSE/polling path.

### Changed
- Webhooks now enqueue a debounced refresh of the stored GitLab intelligence snapshot, keeping project intelligence DB-backed through sync/webhook mechanics.
- Version `2026.7.2.post14`; Service Worker cache `gitpulse-v268`.

## [2026.7.2.post13] - 2026-07-02

### Fixed
- Members table: the "Actions" header is now right-aligned so it sits directly above its row buttons (the eye toggle + View) instead of drifting to the far left of a wide column. Applies to the live table and its loading skeleton (shared head macro).
- Issues to Address header pills: the Medium (amber) and Low (blue) counts were getting lost against the dark card header - the user only saw two faint numbers ("45"). They are now bold, outlined chips so each count and its label stay clearly readable next to the High (red) pill.

### Changed
- Version `2026.7.2.post13`; Service Worker cache `gitpulse-v267`.

## [2026.7.2.post12] - 2026-07-02

### Fixed
- The project Sync button no longer sticks disabled (needing a page refresh) when a sync is refused - e.g. an invalid/expired GitLab token returning 503. The handler used to register a phantom "sync running" global-job slot BEFORE the request was confirmed; a refused request never resolved that slot, so the process-lock kept the button disabled. The optimistic slot is gone: the button-loading spinner is the only feedback during the request, and the real progress slot is registered only once the server returns a job id. On failure the button re-enables and a clear message is shown.

### Changed
- Version `2026.7.2.post12`; Service Worker cache `gitpulse-v266`.

## [2026.7.2.post11] - 2026-07-02

### Fixed
- The project members table (and its Issues-to-Address score cohort) now scopes to THIS project's students instead of every student in the parent subgroup. A GitPulse "team" maps to a GitLab subgroup that can hold many project repos, so a single project's members table was showing the whole section (~50) rather than the project's real ~5. With the live member fetch unavailable (expired token / GitLab maintenance) the page recovers the real roster from stored data: the per-project roster saved on the last sync, else derived from stored merge-request activity (authors, assignees, reviewers, approvers) so it is correct even before a fresh sync.
- Scoring counts a student as a project member regardless of GitLab membership source (direct OR inherited): a real contributor is no longer dropped from the group score just because their team-level source is 'inherited'. The score reflects the actual project cohort, not only the displayed rows.

### Changed
- The sync now stores each project's GitLab member roster alongside its intelligence snapshot (`gitlab_projects.gitlab_intel.members` / `direct_members`).
- Version `2026.7.2.post11`; Service Worker cache unchanged (`gitpulse-v265`) - backend-only change, no static-asset updates.

## [2026.7.2.post10] - 2026-07-02

### Fixed
- Fixed layout alignment of the members table Actions column in the loading skeleton and live table.
- Added GitLab active members warning note to the student views of both skeletons and live tables.

### Changed
- Version `2026.7.2.post10`; Service Worker cache `gitpulse-v265`.

## [2026.7.2.post9] - 2026-07-02

### Changed
- Version `2026.7.2.post9`; Service Worker cache `gitpulse-v264`.
- Simplified the Group Members and Project Members tables by removing the redundant "Source", "Role", and "Status" columns, and removing the filter bar (since only database student members of the group/project are displayed).
- Colored the "Pipelines" column on the Group Members table to clearly identify success (green) vs failures (red), and added descriptive tooltips explaining the counts.

## [2026.7.2.post8] - 2026-07-02

### Added
- GitLab Intelligence panels now survive an unreachable GitLab. A new `gitlab_projects.gitlab_intel` JSONB snapshot (protected branches, contributors, repository statistics) is written on every project/team sync, and the project-detail route falls back to it per-card when the live GitLab fetch fails (expired token / maintenance window). Previously these three cards were the only data on the page with no stored fallback, so they collapsed to "GitLab is unreachable" whenever the token lapsed.

### Fixed
- The project-detail intelligence cards no longer blank themselves to "GitLab is unreachable" when a live refresh fails - the last rendered/synced snapshot is preserved instead of being wiped.
- The Groups table no longer overflows its card ("out of frame"): deleted-group rows carry wide full-text action buttons ("Restore", "Remove from deleted") that, in the fixed-layout table, forced the whole table to scroll horizontally. Those buttons now wrap within the actions column; active rows are untouched.

### Changed
- Version `2026.7.2.post8`; Service Worker cache `gitpulse-v263`.
- New Alembic migration `008` adds the nullable `gitlab_intel` column.

## [2026.7.2.post7] - 2026-07-02

### Fixed
- Tooltips are now always the styled component (Tippy) tooltip, never the browser's native `title=` popup: converted the `btn`/`btn_icon` macros, the info-card dismiss button, the course-settings check toggle and sync-lock save buttons (via the disabled-control wrapper), the login server-status dot, localized `<time>` timestamps, and the client-inserted Group row action buttons.
- Dismissed banners now stay dismissed: the info-card X remembers the dismissal in `sessionStorage` (keyed by banner + current state) so a "sync failed" / "sync cancelled" / "data may be outdated" banner no longer reappears after navigating away and back.
- The top loading bar and submit buttons no longer stick after a validation failure: the non-navigation submit path (e.g. Add Group with a 1-character name) now clears the progress bar and no longer arms the anti-spam button-lock, so nothing hangs until a manual refresh.
- New Group rows inserted after creation now mirror the server table's responsive column classes (`col-hide-sm`/`col-hide-md`, centered Status), so the row no longer shifts out of alignment on narrow viewports; the first group in a course reloads to render the canonical table.

### Changed
- Version `2026.7.2.post7`; Service Worker cache `gitpulse-v262`.
- Added Slovak translations for the permanent-delete / "Remove from deleted" strings (12 keys), returning missing translations to zero.

## [2026.7.2.post6] - 2026-07-02

### Fixed
- Fixed the course-detail JavaScript syntax error that stopped the page script from loading, which also restored the `toggleDeletedTeams` data-action binding and stopped the missing-action console spam.
- Fixed Run Checks confirmation on course detail to use the shared callback-based confirmation helper, so the process can enqueue jobs and report progress instead of returning before the API call.
- Scoped the white avatar ring to the dashboard greeting avatar only, removed it from the topbar avatar, and switched the topbar role pill to the shared `role_badge` component used by User Management.
- Stabilized modal opening by resetting modal scrollers before display, keeping modal/drawer backdrops teleported to `<body>`, and no longer hiding the modal body scrollbar during the entrance animation.
- Stopped suppressing Chromium's native PWA install banner by default; the custom PWA prompt now calls `preventDefault()` only when explicitly enabled.

### Changed
- Version `2026.7.2.post6`; Service Worker cache `gitpulse-v261`.

## [2026.7.2.post5] - 2026-07-02

### Added
- Permanent deletion ("Remove from deleted") endpoints and UI actions for inactive teams and projects. Teachers/admins can now completely get rid of deleted groups or unlinked projects and all their associated records (memberships, snapshots, pipelines, MRs, commits, issues, LLM logs, and background jobs) from the system.

### Fixed
- Fixed mobile and tablet layout spacing and corners so the main content panel remains inset with 8px margins and rounded corners on small viewports rather than stretching full width.
- Removed duplicated user avatar from the topbar dropdown menu card header.
- Replaced the static visual-only "Coding my life" status box with a status badge showing the user's role (Admin, Teacher, Student) in the topbar user menu.
- Removed the disabled "Deleted" button from the loading skeletons.

### Changed
- Version `2026.7.2.post5`; Service Worker cache `gitpulse-v260`.

## [2026.7.2.post4] - 2026-07-02

### Fixed
- Add Group now validates the name: a blank or single-character value (e.g. a stray "ф") is rejected client-side (immediate field error) and server-side (`TeamCreate` trims and requires >= 2 non-space characters), so you can no longer create a junk group that then vanishes.
- Faster page/status loads: the course sync-status endpoint and the SSE stream no longer probe GitLab over the network on each poll/connect. They read the cached token-health flag (in-process/Redis, no round-trip); the flag is still poisoned by GitLabClient on the first 401, so the invalid-token banner still appears - without adding a network round-trip to every status tick.
- Dirty-check is now opt-in. Every modal with any input used to arm the "You have unsaved changes. Discard?" guard, which fired on throwaway action modals (GitLab import, run-checks) where a typed value is worthless. Auto-init now only covers modals marked `data-dirty-check`; genuine edit forms keep protection via their explicit `enableFormDirtyGuard()` calls.

## [2026.7.2.post3] - 2026-07-02

### Added
- Info-card banners can now be dismissed. The `info_card` macro takes `dismissible=true` and renders an X button; a delegated, CSP-safe click handler removes the card. Applied to the course "Some sync jobs failed", "Sync cancelled" and "Data may be outdated" banners so teachers can clear them.

## [2026.7.2.post2] - 2026-07-02

### Fixed
- Content-panel layout restored to the reliable GitLab-style model: `.gl-page` uses a fixed `height` (fills the viewport) and `.gl-page-content` uses `flex: 1` so the panel is always full height and the content scrolls INTERNALLY (mirrors GitLab's `.js-static-panel` / `.panel-content-inner`). The earlier `max-height` + `flex: 0 1 auto` experiment made the panel shrink to the loading skeleton, which read as "half the page is missing" - reverted.
- The "Some sync jobs failed" banner no longer flashes and vanishes after a second. The live sync-status update managed a generic `.info-card-danger`, so an SSE tick reporting 0 (its count uses a 2h window that excludes older failures) removed the server-rendered banner - and could also remove the token banner. It now manages ONLY its own live card (`#jsSyncFailedCard`) and never touches the server banner (`.js-sync-failed-banner`) or `#gitlabTokenBanner`.

## [2026.7.2.post1] - 2026-07-02

### Fixed
- GitLab import cancellation is no longer registered as unsaved form data; pressing Cancel stops the active import path without showing an unrelated before-unload prompt.
- Queued CI failure scenarios and conflict challenges can now be cancelled before they mutate GitLab, and CI scenario polling only runs while rows are actually pending.
- Retrying a failed scheduled/manual system job now creates a new tracked cancellable background job, so Follow the latest updates, Items that need your attention, and the global job bar all receive the same job id.
- Active job checks now include the `started` state across sync, run-checks, import, course status, and scheduled jobs, preventing duplicate starts during the RQ handoff.
- Live dashboard/project value flashes now use requestAnimationFrame instead of synchronous layout reads, removing another forced-reflow source from hot refresh paths.
- Production monitoring no longer leaves Alertmanager in a restart loop; the container now starts with a valid internal absolute external URL and a YAML config that Alertmanager can parse without unsupported shell-style environment expansion.

### Changed
- Version `2026.7.2.post1`; Service Worker cache `gitpulse-v256`.

## [2026.7.2] - 2026-07-02

### Fixed
- GitLab import now rejects invalid group/project paths before streaming; typing non-ASCII input can no longer start an import or crash the import error handler.
- Long-running processes now share a cancellable job contract: global cancel buttons stop sync, run-checks, Docker verification, scheduled jobs, LLM analysis, GitLab enrichment, frontend-only AI generation, and active imports. Cancelled jobs stay terminal, and workers no longer overwrite them with completed/failed after races.
- Course sync and run-check status now reports cancelled groups separately and uses the newest run-check job per group, so old failed rows do not poison a later successful run.
- Course detail SSE/logging and flash animations no longer create duplicate EventSources or forced reflow; the shell bottom spacing now matches GitLab-style content height without an empty footer gap.

### Changed
- Version `2026.7.2`; Service Worker cache `gitpulse-v255`.

## [2026.7.1.post5] - 2026-07-01

### Fixed
- The content panel (`.gl-page`) now shrinks to its content on short pages (`max-height` instead of a fixed `height`) instead of always filling the viewport, so a page with only a few rows no longer shows a large empty rounded card below the table - matching GitLab's own panel behaviour. Tall pages still cap at the viewport and scroll internally; the `flex: 1` content child resolves its basis to content-size under the now-indefinite height, so nothing collapses.

## [2026.7.1.post4] - 2026-07-01

### Fixed
- Follow-up to post3: the "GitLab token invalid" banner now appears on page load (the SSE stream and the sync-status poll warm the shared token-health flag with one cached probe) instead of only after the first failed click. So Sync All short-circuits with a clear toast on the very first click - no "Connecting..." flash, and the button is never left in a loading state that needed a page refresh to clear. The frontend also mirrors `gitlab_token_ok` to short-circuit in the split second before the banner DOM mounts.

## [2026.7.1.post3] - 2026-07-01

### Fixed
- The "GitLab token invalid" state no longer greys out the Sync All button (which left users guessing when it would re-enable and was inconsistent with the still-clickable Import button). The banner is now the single clear explanation; clicking Sync All surfaces the same reason as a toast instead of flashing a "Connecting..." progress bar that vanishes a second later.
- Test isolation: the shared GitLab token-health flag is reset around every test, so a mocked 401 in one test can no longer leak into a later one and make a guarded job skip - a failure that only surfaced in CI (live Redis), not on a dev box.

## [2026.7.1.post2] - 2026-07-01

### Fixed
- Sync no longer flaps ("finished in 2s, then restarted itself, in circles"). A failed sync used to re-raise into RQ's blind auto-retry, flipping the job `running↔failed` and making the course progress bar oscillate while the "Data may be outdated" banner popped mid-sync. Sync now uses a **bounded, visible retry** (3 attempts): the worker keeps the row active between attempts and surfaces `Retrying (2/3)` as a per-group `RETRY 2/3` badge; the run ends with a definitive **"All syncs completed!"** or a red **"Sync finished with problems - N group(s) failed"** (with per-group failure toasts and a support pointer) instead of always reporting success.
- Expanded job-history cards no longer break the table: the injected detail row was counted in the `:nth-child` zebra striping, flipping the shading of every row below it and painting a stripe over the detail panel. It is now excluded from the stripe/hover count.

### Added
- **App-wide GitLab token protection.** An invalid/expired token (401/403) is now detected the instant *any* GitLab call fails and shared through a cached health flag, so the whole app reacts to one failure instead of each flow independently hammering GitLab:
 - Sync, project-sync, Sync All and GitLab import are **blocked up front** with a clear "GitLab API token is invalid or expired (401)" message (the old pre-flight treated 401 as "reachable" and let doomed jobs enqueue).
 - Token-using background jobs (issue/MR enrichment, membership sync, incremental project refresh) **skip immediately** when the token is known-bad and **do not retry** auth errors, stopping retry storms.
 - Recovery is automatic: any successful GitLab call clears the flag, so work resumes after a token rotation without a restart.
 - The course page shows a persistent **"GitLab token invalid"** banner and disables Sync All while the token is bad.

## [2026.7.1.post1] - 2026-07-01

### Fixed
- Docs footer copyright read `2024-2026`; corrected to `2026-2027 TUKE Košice` (the thesis runs 2026-2027).
- SEO: the language-switch links (`/dashboard/language/...`) now carry `rel="nofollow"` so search engines stop discovering and indexing those stateful redirect URLs from the public login page.
- Refreshed the last stale example date in the course-settings help text (`2024-09-23` -> `2026-09-21`, still a Monday), keeping the template and the Slovak i18n catalog key in sync.

## [2026.7.1] - 2026-07-01

### Changed
- Docs: removed the deleted "Rubric" feature from the Slovak teacher guides (dashboard, getting-started) so they match the already-cleaned English versions and the current app (which has no rubric engine). Refreshed stale example dates and group paths (`2024-...` timestamps, `kpi/tp-2024`, `assignments-2025`) to current-year examples across the GitLab, operator and developer guides, and updated the documented current version to `2026.7.1`.

## [2026.6.30.post3] - 2026-06-30

### Fixed
- Login/logout: the textured backdrop (`keycloak-bg.png`) was preloaded unconditionally, but the mobile sheet renders `background-image: none`, so the browser warned "preloaded but not used". The preload is now gated with `media="(min-width: 768px)"`, matching where the background is actually painted.
- Removed stray em dashes from user-facing copy (the MR-workflow step tooltip and two published changelog lines) so the text reads consistently.

### Changed
- Docs: refreshed the pilot-deployment guide to 2026 and normalised the inconsistent `7/9` / `4/12` date formats; bumped the "DevOps" example course year.
- Version `2026.6.30.post3`.

## [2026.6.30.post2] - 2026-06-30

### Fixed
- Favicon in Google Search: the site served `/favicon.ico` as a 301 redirect to a PNG, which Google's favicon fetcher handles unreliably (it was surfacing the generic globe next to results). `/favicon.ico` now returns a real multi-resolution `.ico` (16-256px, generated from the app icon set) with a 200, and the indexable login page lists it first. Google refreshes the favicon only when it recrawls the home page, so it can take days to appear.

### Changed
- Version `2026.6.30.post2`.

## [2026.6.30.post1] - 2026-06-30

### Fixed
- Auth pages (login / logout): the language selector menu, flash alerts, toasts and the selected-language checkmark rendered dark on the white card for visitors whose saved theme was dark. `theme-bootstrap.js` now drives `data-theme` from `data-color-scheme-lock` (not just `color-scheme`), so every token-driven component on the light-locked auth pages renders light in one place.
- Test coverage shown as "not reported" on student MR cards while GitLab reported a real percentage: the full team sync (`sync_job.py`) skipped already-finished pipelines, so a test pipeline stored without coverage never backfilled. Sync now re-fetches terminal pipelines that ran tests but recorded no coverage (`coverage` stays sticky, so a blank re-fetch never erases a known value).

### Added
- Mobile modals: the bottom-sheet drag handle is now functional - swipe it (or the modal header) down to dismiss, mirroring the iOS / GitLab bottom-sheet gesture. The gesture engages only from the top region, so it never competes with scrolling the modal body, and is inactive on desktop.

### Changed
- Version `2026.6.30.post1`.

## [2026.6.30] - 2026-06-30

### Fixed
- Webhook metrics: resolved Redis ConnectionPool RuntimeError in the RQ worker when processing events by initializing the pool during worker startup.
- Course settings import script: removed obsolete imports and calls to gaming detection and rubric engines to prevent errors.
- Observability: pointed OTLP tracer endpoint to local Jaeger collector, enabling trace visualization locally.
- Documentation: updated Slovak and English operator monitoring guides with production endpoints, ports, and Caddy Basic Auth credentials for manual verification.

## [2026.6.29.post12] - 2026-06-29

### Fixed
- Dev Startup script (`start-dev.ps1`) error handling: removed `$ErrorActionPreference = "Stop"` which crashed the script on benign python/pip warnings during the docs container build.
- Grafana redirect loop: resolved a connection refused issue on `http://localhost:3000` by overriding `GF_SERVER_ROOT_URL` to `http://localhost:3000/grafana/` in `docker-compose.monitoring-dev.yml` to prevent redirecting local dev requests to production HTTPS urls.
- Cleaned up obsolete metrics: removed the stale "Report Generation Time", "Sweep Jobs", "Sweep Job Duration", and "Active Dashboard Sessions" dashboard panels, and removed the "ReportGenerationSlow" and "SweepJobFailing" alerts since their underlying functions do not exist in the codebase.
- Grafana targets scraping: added `metrics_path: /grafana/metrics` for Grafana jobs in both `prometheus.yml` and `prometheus.dev.yml` to prevent Prometheus from failing on redirection loops.
- Production Redis credentials: added missing `REDIS_PASSWORD` and configured authenticated `REDIS_URL` in `.env.production` to prevent startup crashes from mandatory production security/validation gates.

### Changed
- Version `2026.6.29.post12`.

## [2026.6.29.post11] - 2026-06-29

### Fixed
- Restored a green lint stage on `main`. Today's rapid polish commits landed four `ruff` violations and three `ruff format` drifts under the pinned `ruff==0.15.4` toolchain, so the `ruff-check`/`ruff-format` CI gates were red: an `f`-string with no placeholders (`compile_pwa_icons.py`), an unsorted import block (`generate_og_image.py`), a `SIM108` if/else in the diff-context window helper (`dashboard/students.py`), an over-long assert (`test_frontend_resilience.py`), plus whitespace/quote drift in `template_helpers.py` and `generate_og_image.py`. All fixes are logic-preserving (ternary, import sort, line wrap, formatting); full unit suite (2512) stays green.

### Changed
- Accessibility: the dashboard "Quick access" Groups/Subgroups toggles are now real tabs - explicit `type="button"` (so they can never act as implicit form submits), `role="tablist"`/`role="tab"`, and a bound `aria-selected` that reflects the active panel for screen readers. Template-only; the `.gl-qa-tab` guard-selector contract test is unchanged.
- Version `2026.6.29.post11`.

## [2026.6.29.post10] - 2026-06-29

### Changed
- Backend N+1 removal in the two course-wide endpoints. "Run checks (all groups)" re-checked each group for an in-flight run-checks job with one SELECT per group, even though the identical set is already computed and guarded up front - it now reuses that set in memory (zero extra queries). "Sync all groups" likewise issued one "is a sync already running?" SELECT per group - now a single batched query via the existing `_active_sync_team_ids` helper (same criteria, and the up-front set is provably equivalent since each per-group query only ever matched that group's own pre-existing jobs). For a course with N groups this drops up to 2N redundant round-trips to ≤1. No behavior change - full unit suite (2512) green.
- Version `2026.6.29.post10`.

## [2026.6.29.post9] - 2026-06-29

### Changed
- Extended the GitLab `preconnect` / `dns-prefetch` hint to the standalone login page (`login.html` does not extend `base.html`, so it needed the hint repeated). This is the highest-value case: the login page's primary CTA is the OAuth redirect to GitLab, so warming the connection beforehand makes that redirect a round-trip faster. Resource hint only; origin from the `gitlab_url` setting. No static asset or SW cache change.
- Version `2026.6.29.post9`.

## [2026.6.29.post8] - 2026-06-29

### Changed
- Frontend optimization: added `<link rel="preconnect">` + `<link rel="dns-prefetch">` to the GitLab origin in the base `<head>` (sourced from the `gitlab_url` setting, not hardcoded). It warms DNS/TCP/TLS to GitLab before it is needed - the login page's primary CTA redirects there for OAuth, and authenticated pages load user avatars and call its API - so first contact with GitLab is a round-trip faster. Resource hint only: it cannot affect rendering or behavior. No static asset changed, so the bundles and Service Worker cache (`gitpulse-v247`) are untouched.
- Version `2026.6.29.post8`.

## [2026.6.29.post7] - 2026-06-29

### Changed
- Dashboard backend optimization: the home page and `/dashboard/stats` no longer issue the "total groups" and "total students" COUNT queries for students - those values populate only the teacher/admin stat cards (`_build_student_stat_cards` ignores them, and no template reads the raw context vars). Two fewer DB round-trips on every student dashboard load and on every polled stats refresh - the majority-role, highest-frequency path. No behavior or markup change.
- Backend-only release: no static assets changed, so the Service Worker cache is intentionally left at `gitpulse-v247` (bumping it would force every client to re-download cached assets for nothing).
- Version `2026.6.29.post7`.

## [2026.6.29.post6] - 2026-06-29

### Changed
- Disabled the staggered "by arrival" cascade reveal on the dashboard and student profile (removed the `data-gp-cascade` markers): it regressed those views in production. The `.gp-cascade` engine and the version-consistency gate stay in place; the cascade will be re-enabled only after it is visually verified in a browser.
- Version `2026.6.29.post6`; Service Worker cache `gitpulse-v247` (also force-invalidates any stale cached assets).

## [2026.6.29.post5] - 2026-06-29

### Added
- Extended the staggered "by arrival" reveal to the student profile: the merge-request cards (`.mr-card-list`) and the reviews-given cards (`.rg-card-list`) now cascade in one after another on first load, matching the dashboard. Attribute-only (`data-gp-cascade`) - reuses the already-shipped `.gp-cascade` engine, so no bundle change.

### Changed
- Added a release version-consistency test (`tests/unit/test_release_version_consistency.py`) asserting `pyproject.version` matches the newest entry of the root + docs (SK/EN) changelogs, so a release bump can no longer update one surface and leave the others behind (the post3 drift that left pyproject at post2).
- Version `2026.6.29.post5`; Service Worker cache `gitpulse-v246`.

## [2026.6.29.post4] - 2026-06-29

### Added
- **Staggered "arrival" reveal**: dashboard collections (KPI stats, course cards, "Items that need your attention", and the "Follow the latest updates" feed) now cascade in one after another - "by arrival" - instead of every item snapping in at once. Implemented as an item-level cascade (`.gp-cascade` / `--gp-ci`) layered on the existing block stagger (`.gp-stagger` / `--gp-i`) via a distinct index so the two compose without conflict; honors `prefers-reduced-motion`, runs only on the first reveal (lazy skeleton hand-off / initial render) and never on live-poll refreshes, and deliberately excludes table rows (whose transform reveal was removed for the td-background paint artefact).
- Relative "time ago" date formatting (e.g. "2 hours ago") for activity and timestamps, via the client-side `localize-time` helper.

### Fixed
- Guided tour now recursively scrolls every scrollable ancestor to bring a step target into view, and skips table containers so the main page wrapper scrolls instead of an inner table.
- The tour's "user row actions" step now highlights the buttons wrapper rather than the bare table cell.
- Rolled back the earlier tour positioning/popover changes that regressed pointing at the target.
- Removed duplicate subtitles on the student profile page.

### Changed
- Rebuilt JS/CSS bundles and minified assets.
- Version `2026.6.29.post4`; Service Worker cache `gitpulse-v245`. Also realigns the package version, which had stayed at `post2` while `post3` shipped only the SW cache + changelog.

## [2026.6.29.post3] - 2026-06-29

### Fixed
- Inline diff code context now displays GitLab-style double line-number columns (old & new line numbers side-by-side).
- Inline diff range comments display correctly in thread footers (e.g. `Comment on lines +51-53`).
- Discussion thread headers now include the author's GitLab username (`@username`) and the localized thread start time.
- Status icons in `.commit-message-cell` are now inline and no longer wrap above the commit message link.
- Guided tour popovers on desktop now point to their highlighted targets with a themed arrow instead of being forced to the bottom-right corner.

### Changed
- Email notification logo is now transparent (no dark-gray background tile) with the box-shadow boundary removed for a cleaner, modern look.
- Version `2026.6.29.post3`; Service Worker cache `gitpulse-v244`.

## [2026.6.29.post2] - 2026-06-29

### Changed
- Reworked the Open Graph / social-share cover (`og-image.png`, docs `og-cover.png`) to use the GitLab-style tanuki tile (orange tanuki on a light gradient rounded square) with the GitPulse ECG pulse overlaid, replacing the off-brand blue ECG square so link previews match the in-app logo. The home-screen/PWA icons and favicons were already the tanuki.
- Version `2026.6.29.post2`.

## [2026.6.29.post1] - 2026-06-29

### Fixed
- Diff comment code context no longer crosses a hunk boundary: the snippet stays within the commented hunk (showing the whole compact added construct, GitLab-style) instead of jumping line numbers (e.g. `29 → 49`) and bleeding into the next function.
- Inline `code` pills in descriptions/comments get real horizontal breathing room so they no longer visually touch the surrounding words.
- MR pipeline **Test coverage** row (icon · label · % · "from N jobs") is now forced onto one shared midline so the parts no longer drift to different vertical levels.
- Regenerated the stale 536-byte docs `favicon.ico` as a proper multi-resolution GitPulse tanuki icon and cache-busted the docs favicon links (`?v=2`).
- Guided tour now opens a collapsed `<details>` around a step target **only when navigating to that step** (driver `element()`/`onHighlightStarted`), not during the page-load eligibility scan - fixes the regression where evaluating tour availability could auto-expand the collapsed diff/code sections.

### Changed
- Version `2026.6.29.post1`; Service Worker cache `gitpulse-v243`.

## [2026.6.29] - 2026-06-29

### Fixed
- Made inline code context in MR/review discussions collapsible and **collapsed by default** (GitLab-style `Show code` summary with file:line), so long threads stay light and no longer lag while scrolling.
- Removed the misleading non-interactive `new`/`old` pill from the code-context toolbar; the side is already conveyed by the line gutter and the `Comment on line +N` footer.
- Stopped rendering the fabricated `1 participants` label on discussion threads - the participant count now shows only when a thread genuinely has more than one participant.
- Decluttered review threads: dropped the redundant per-reply "reply to ..." cue (replies are already visually nested) and the duplicate copy-link icon on a thread's root note (the thread already carries one).
- Prevented inline `code` pills in MR/issue descriptions and comments from overlapping adjacent lines (`box-decoration-break: clone`, slimmer padding, roomier line-height).
- Vertically centered MR card title rows and the reviews-given header so labels no longer sit above their icons.
- Workflow ribbon dots render larger, clearer icons with a calmer hover lift (no row jump).
- Guided tour now opens any collapsed `<details>` around a step target (changed-file tree, inline code context) before highlighting, so steps like *Changed-file tree* are no longer broken when a section is closed.
- Removed the dark strip below the course-settings sticky save bar when it is the last block on the page.

### Changed
- User-info modal: the per-group `+N more` project list is now an expandable / collapsible control (`Show less`) instead of a dead label.
- Docs Open Graph/Twitter card now uses the branded GitPulse cover image (`assets/og-cover.png`) so link previews match the app.
- Rebuilt generated bundles/minified assets; added Slovak translation for `Show code`.
- Version `2026.6.29`; Service Worker cache `gitpulse-v242`.

## [2026.6.28.post1] - 2026-06-28

### Fixed
- Scoped student MR/review diff file anchors per card so changed-file tree clicks and comment jumps no longer target the wrong `diff-file-*` block when several MRs share file indexes.
- Simplified GitLab-like diff comment code context to one side-aware line-number gutter and exact `Comment on line` text, removing the extra old/new number panel and incorrect visible-range footer.
- Backfilled missing MR pipeline `Test coverage` from GitLab pipeline details/jobs for visible student MRs when older local pipeline rows have `coverage = null`.
- Removed the unreliable `Response Rate` diagnostic card and the duplicate diagnostic `Test Coverage` stat card, including matching skeleton placeholders.

### Changed
- Rebuilt generated bundles/minified assets after the student-detail fixes.
- Version `2026.6.28.post1`; Service Worker cache `gitpulse-v241`.

## [2026.6.28] - 2026-06-28

### Fixed
- Kept copyable/hash links for student comments, MR cards, dashboard targets, and paginated tables on the shared local `.gl-page-content` scroller contract instead of browser-level auto scrolling.
- Restored MR pipeline test coverage as a GitLab-like inline row (`Test coverage ... from 1 job`) while removing the old `Test Coverage` card/chip treatment and matching the MR skeleton to that structure.

### Changed
- Version `2026.6.28`; Service Worker cache `gitpulse-v240`.

## [2026.6.27.post2] - 2026-06-27

### Fixed
- Matched the student profile loading skeleton to the live profile card, centered the GitLab/profile/date metadata on mobile, and removed the duplicate profile divider.
- Reworked student-detail jumps to use the local `.gl-page-content` scroller contract from Issues to Address, preventing global window-scroll layout jumps.
- Made MR commit rows grid-based so commit labels, +/- stats, and dates stay aligned instead of spilling across the page.
- Moved MR diff code context to the discussion-thread level with old/new gutters, target-row highlighting, copy action, and attached replies so code comments read like GitLab threads.
- Parsed GitLab test coverage from pipeline object/build data and same-SHA fallback pipelines so rows show real values like `Test coverage 91.00% ... from 1 job` instead of `not reported`.

### Changed
- Smoothed the GitPulse logo ECG hover interaction and rebuilt the student profile/MR skeleton static assets.
- Version `2026.6.27.post2`; Service Worker cache `gitpulse-v239`.

## [2026.6.27.post1] - 2026-06-27

### Fixed
- Rebuilt student MR discussions into linked GitLab-like threads with stable thread/comment anchors, reply-to jump links, collapsible replies, and diff-file jump buttons.
- Added explicit pipeline coverage fallback text when GitLab does not report coverage, while keeping real coverage percentages inline with pipeline status.
- Decorated MR branch commits with visible authors, in-app profile links where available, and a Teacher commit badge when the commit belongs to a course teacher.
- Tightened student profile metrics, diff file-tree sticky scrolling, centered table skeleton placeholders, Run Compliance Checks checkbox rendering, and modal footer selection styling.

### Changed
- Version `2026.6.27.post1`; Service Worker cache `gitpulse-v238`.

## [2026.6.27] - 2026-06-27

### Fixed
- Aligned member-table skeleton rows with the live column contract so Status/Checks placeholders no longer drift.
- Reworked student MR diff navigation so the changed-file tree stays sticky, scrolls locally, and no longer uses item-level global scrolling.
- Stabilized Run Compliance Checks modal selection rows and checkbox rendering without the checked-state inset stripe or global checkbox scale animation.
- Rebuilt inline MR diff-note code context with old/new gutters, side-aware target matching, local scrolling, and a copy action.

### Changed
- Polished student profile metric tokens, Reviews Given cards, tour popovers, and student-detail tour steps for MR workflow, code comments, changed files, and reviews given.
- Simplified GitPulse logo motion to a smooth ECG pulse with one subtle hover transform, avoiding jitter in light and dark themes.
- Normalized app source CSS `letter-spacing` declarations to `0` across shared and page styles for consistent typography.
- Version `2026.6.27`; Service Worker cache `gitpulse-v237`.

## [2026.6.26] - 2026-06-26

### Fixed
- Fixed the student Issues-to-MR jump so MR chips use a local page-content scroll target and no longer trigger the global anchor scroller or break layout.
- Fixed modal dirty-check initialization for dynamically opened modals and drawers by re-attaching the guard when a modal is opened.
- Added GitLab-like inline code context for diff comments so review notes show the exact nearby file lines when diff data is available.

### Changed
- Rebranded visible Collaboration wording to Teamwork across the app and docs while keeping existing internal JSON/API keys stable.
- Moved logo styling into a shared component stylesheet, added a GitLab-inspired GitPulse mark with light/dark contrast guards, and rebuilt PWA icons.
- Centralized former template inline sizing/progress styles through component data attributes and shared runtime CSS-variable hydration.
- Improved responsive table/skeleton parity and hover/leave motion polish in shared UI styles.
- Version `2026.6.26`; Service Worker cache `gitpulse-v236`.

## [2026.6.25] - 2026-06-25

### Fixed
- Fixed memory leaks system-wide by implementing proper page teardown and lifecycle cleanup in `GP.activePageCleanup()`. All window/document event listeners, SSE streams (`EventSource`), and polling timers (`setInterval`/`setTimeout`) are fully torn down upon HTMX page swaps.
- Converted all anonymous event handlers on `document` and `window` in standalone page controllers (`admin-events.js`, `admin-users.js`, `course-activity.js`, `support-ticket-detail.js`) to named functions so they can be explicitly removed from the global scope.
- Prevented global lexical scope pollution by removing obsolete IIFE wrappers from page bundles and automating the IIFE generation at bundle time in `build_bundle.py`.
- Extracted the pre-paint greeting script out of `dashboard.html` into a dedicated, clean, component-based static JavaScript module `greeting-sync.js`, leaving templates entirely free of inline executable scripts.

### Changed
- Version `2026.6.25`; Service Worker cache `gitpulse-v235`.

## [2026.6.20] - 2026-06-20

### Fixed
- Course Management now keeps every column available in responsive card rows, with explicit labels and a stable filter toolbar on narrow screens.
- Markdown editor previews work with the Alpine CSP build without relying on the forbidden `x-html` directive.
- Markdown and support-ticket scripts are safe to initialise again after HTMX or SPA-style navigation instead of failing on duplicate lexical declarations.

### Changed
- The public thesis documentation now matches the third interim submission: no provisional result claims, no outdated periodic-scheduler or Quality Gate model, and an explicit description of the current R01-R13 prototype.
- Added the same two anonymised prototype screenshots used in the thesis and documented why individual student views are not published.
- Version `2026.6.20`; Service Worker cache `gitpulse-v234`.

## [2026.6.19.post2] - 2026-06-19

### Fixed
- User Management now keeps search and the role filter in a deterministic toolbar instead of wrapping controls at arbitrary offsets.
- User table column classes now live on the actual headers and cells, so width, truncation, visibility, status, and action rules apply to live rows and skeleton rows equally.
- Human and service-account rows use compact icon actions, safe truncation for long usernames and emails, and a primary identity row in mobile card mode.
- Live role/status updates preserve the same badge and status-indicator DOM contract as the server-rendered table.

### Changed
- The mutually-exclusive role filter uses an accessible attached segmented control with synchronized `aria-pressed` state.
- Version `2026.6.19.post2`; Service Worker cache `gitpulse-v232`.

## [2026.6.19.post1] - 2026-06-19

### Fixed
- Project and team member tables now share one responsive column contract across real rows, loading skeleton rows, and JavaScript fallback rows.
- Project detail skeletons derive rubric/check columns from the active checks list, so the loading matrix no longer drifts away from the real R01-R13 table.
- Admin user skeleton rows now use typed user columns instead of a generic table placeholder.
- Skeleton rows now carry the same responsive `data-label` contract as real rows, so tablet and phone loading states render as label/value cards instead of broken table fragments.
- Admin user role filters and member filter bars now wrap in-place on narrow screens instead of creating horizontal scroll or clipped controls.
- Student merge request pipeline test status now renders as compact badges instead of raw `tests: success` text.
- Issues to Address chart animations are disabled to prevent double entrance playback after tab visibility or HTMX refresh changes.

### Changed
- Version `2026.6.19.post1`; Service Worker cache `gitpulse-v231`.

## [2026.6.18.post1] - 2026-06-18

### Fixed
- Table skeletons now use typed cells for project rows, member rows, badges, status pills, check dots, and action buttons so loading rows keep the same structure as the real tables.
- Dashboard admin and teacher summaries replace the low-value "Open MRs" card with active group coverage.
- Course analytics and activity stale-data banners now report partial current-week group snapshot coverage instead of implying the whole course was not synced.
- Login/logout alerts use the shared GitLab-style alert component with a proper title API and a short synchronized logout fade.
- Robots and sitemap responses explicitly block private dashboard crawling, allow the login page, include last-modified metadata, and set public cache headers.

### Changed
- Version `2026.6.18.post1`; Service Worker cache `gitpulse-v229`.

## [2026.6.18] - 2026-06-18

### Fixed
- Dashboard Quick access project rows now open the project page instead of the parent group.
- Group/course GitLab imports now deactivate active database projects that no longer exist in the imported GitLab group tree, including orphaned team members when no active projects remain.
- Process-action guards keep protecting sync/import/check/delete actions while bypassing passive filters, tabs, and dropdown-style controls.
- Project and member table skeleton contracts stay aligned with the responsive table layout.
- Production redeploy keeps AI collaboration analysis disabled in `.env.production`.

### Changed
- Replaced the layout-moving Back to Group hover gap animation with transform-based icon/link motion.
- Exposed stale-project cleanup counts in GitLab import API and SSE completion payloads.
- Version `2026.6.18`; Service Worker cache `gitpulse-v228`.

## [2026.6.17] - 2026-06-17

### Changed
- Aligned sign-in and sign-out pages layout, spacing, and dimensions with the Keycloak design.
- Re-centered the logo title, set the card width to a compact 400 px, and removed unnecessary border radii for a sharp square-edge look.
- Re-positioned and styled the language selector dropdown to be compact and styled with a semi-transparent black background.
- Incremented application version to `2026.6.17` and Service Worker cache namespace to `gitpulse-v224`.

## [2026.6.16] - 2026-06-16

### Added
- Complete redesign of the email notification system with modern Inter typography, soft drop-shadows, and premium color gradients.
- Comprehensive support tickets interface updates, including dynamic drag-and-drop file attachments in the ticket editor, dragover visual highlighting, and a Chrome double-browse fix.

### Changed
- Replaced obsolete "Reports" references with "Analytics" inside the welcome email template for teacher and admin roles.
- Purged all raw emojis and AI-like emoticons from all active system documentation to establish a professional, publication-ready tone.
- Incremented application version to `2026.6.16` and Service Worker cache namespace to `gitpulse-v217`.
- Cleaned up obsolete helper and scratch scripts from the repository.

## [2026.6.15.post2] - 2026-06-15

### Added
- Integrated Assignments Tracker and group progress bar cards on both Course Assignments page and Team Detail page.
- Smart GitLab MR/Issue title matching heuristics to dynamically track custom assignments completion.
- Global deadline warning banners at the top of the Project Detail page for approaching or overdue assignment milestones.

### Changed
- Exposed the Course Assignments tab to students.
- Replaced raw inline width styles on the contributor progress bar with CSS custom properties (`--progress`).
- Version `2026.6.15.post2`; Service Worker cache `gitpulse-v210`.

## [2026.6.15.post1] - 2026-06-15

### Added
- Pajamas-aligned custom academic and exam period week calculation (`1`-`13` and `S1`-`S7`) in Flatpickr based on the settings' semester start date.
- Alpine.js-backed, Pajamas-styled custom dropdowns (`select_field`) for type and week selection on the assignments page.
- Global window-level drag-and-drop overrides to prevent accidental browser navigation on missed file drops.
- Pointer-events scoping on file upload areas to eliminate drag flickering.

### Changed
- Refactored Edit and Delete actions on the assignments list to use `btn_icon_only` to prevent text overlap in compact layouts.
- Rebuilt static CSS/JS bundles and minified assets.

### Fixed
- Fixed dark-mode checkbox checkmark visibility and added premium spring-based transitions.
- Fixed file upload areas to dispatch a standard `change` event on dropping, allowing automatic HTMX integration.
- Removed redundant page-entrance card animations to prevent double-swaps.

### Release
- Version `2026.6.15.post1`; Service Worker cache `gitpulse-v209`.

## [2026.6.11.post7] - 2026-06-11

### Added
- Account-level Light, Dark, and System preference persistence through migration
  `052` and `/dashboard/api/theme`.
- Installed-PWA verification through `getInstalledRelatedApps()` with a
  same-origin web-app manifest relationship.
- A product-tour appearance step that opens the profile menu and targets the
  real switcher.

### Fixed
- Restored visible semantic borders for buttons, dropdowns, cards, and sections
  in both light and dark modes.
- Removed search-input width expansion on focus, preventing toolbar wrapping and
  responsive layout shifts.
- Restored the branded login background and made the card responsive at a real
  390 px mobile viewport.
- Prevented stale PWA installation markers from suppressing or showing the
  install prompt incorrectly.
- Restored meaningful dashboard hover/focus feedback without generic page
  entrance animations.

### Release
- Version `2026.6.11.post7`; Service Worker cache `gitpulse-v186`.

## [2026.6.11.post4] - 2026-06-11

### Added
- Light, Dark, and System color modes backed by one semantic token layer and
  resolved before first paint.
- A shared theme switcher for the dashboard, login, template errors, and
  middleware fallback errors.
- A static, theme-aware offline error surface.
- A shared appearance step that is appended to every available product tour.
- Server-owned sync scope metadata in Job History, including course names.

### Changed
- Charts react to color-mode changes without a page reload.
- Middleware errors now use one escaped, CSP-aware renderer instead of
  duplicated embedded HTML and CSS.
- Spinner rendering now has one empty-element component contract across
  templates and JavaScript.
- Skeletons are scoped to real HTMX lazy regions; SSR tables render immediately
  without a JavaScript visibility gate.
- Light-mode shell, navigation, cards, tables, controls, skeletons, spinners,
  typography, borders, shadows, and interaction states now use current Pajamas
  semantic roles instead of page-specific overrides.
- Job History resolves Project, Course, and Group sync labels on the server.
- Historical whole-course sync rows recover their missing course context during
  migration.

### Removed
- Generic page, row, and lazy-fragment entrance animations.
- Dead `lazy=false` page-skeleton branches and duplicate button spinner markup.
- Dashboard hover translations and scale effects that caused unnecessary
  movement without communicating state.

### Release
- Version `2026.6.11.post4`; Service Worker cache bumped to `gitpulse-v183`.

## [2026.6.10.post5] - 2026-06-10

### Added
- **Pajamas-aligned loaders and zero inline styles**: Completely eliminated all inline `style` configurations for width, height, and border-radius within `loaders.html`. All sizing is now mapped to reusable Pajamas-aligned utility classes in `loaders.css`.
- **Fidelity-aligned Team Detail and Teachers Skeletons**: Replaced custom/manual skeleton divs with macro components (`badge`, `btn`, `btn_icon`, `btn_icon_only`) in disabled states to guarantee pixel-perfect size matching and zero layout shift (CLS).

### Fixed
- **GitLab project deletion and empty repo handling**: Added automatic deactivation of projects whose GitLab repository was deleted (returning empty repository status rather than 404). Blanked stale roster scores to match "N/A" on empty/deleted repos.
- **Dynamic roster deactivation on project loss**: Added auto-deactivation of team members when all active projects under their team are deleted/deactivated.
- **Member deactivation safety guard**: Prevented dropping valid project members on partial GitLab API fetch failures, ensuring roster stability during intermittent GitLab API timeouts or 5xx errors.
- **Service Worker & Cache Bump**: Version bumped to `2026.6.10.post5` with cache key incremented to `gitpulse-v176`.

## [2026.6.9.post2] - 2026-06-09

### Changed

- **Complete removal of inline layout styles**: Eliminated all layout-related
  inline `style="..."` attributes (like flexbox, display, margins, padding,
  opacities, and pointer-events) from `loaders.html`. Migrated them to clean,
  Pajamas-aligned CSS utility classes in `utilities.css`.
- **Nicer form layouts**: Replaced inline max-width configurations on form
  components with structured layout utility classes.
- **Service Worker & Cache Bump**: Version bumped to `2026.6.9.post2` with cache key
  incremented to `gitpulse-v174`.

### Fixed

- **Version mismatch alert notification**: Updated the app-internal JSON changelog
  manifest so client browsers receive proper notifications when new versions
  are deployed.

## [2026.6.9.post1] - 2026-06-09

### Added

- **Dynamic table header rendering inside skeletons**: Modified `sk_table` macro
  to accept optional `headers` argument so static columns immediately appear
  during page loadings.
- **Enhanced `sk_stat` macro with label and icon arguments**: The stats grid
  placeholders in Course Analytics, Course Activity, and Student Details now
  render actual titles and icons immediately instead of shimmering blocks,
  completely eliminating layout shifting.

### Fixed

- **Seamless dropdown menu interaction**: Fixed invalid CSS variables
  (`var(--gl-dropdown-item-hover)`) in `dropdowns.css` by mapping them to their
  correct tokens (`var(--gl-dropdown-item-hover-bg)`, etc.), restoring smooth
  background transition effects for list hover states.
- **Skeleton loading alignment across all surfaces**: Checked and fully
  refactored every composed page skeleton (`sk_dashboard`,
  `sk_course_detail_body`, `sk_analytics_inner`, `sk_course_activity_inner`,
  `sk_student_detail`, `_sk_teachers_inner`) in `loaders.html` to align with the
  real server-rendered templates, using translated helper strings `t()` for
  static texts.

### Release

- Version `2026.6.9.post1`; SW cache bumped to `gitpulse-v173`.

## [2026.6.8.post10] - 2026-06-08

### Fixed

- **False "8 groups never synced" after the job cleanup.** post9's migration
  truncated `background_jobs`, but `courses.py` derived "never synced" from the
  presence of a sync **job record** - so every already-synced group suddenly
  reported "never synced". It now uses the durable per-project
  `last_synced_at` timestamp (same signal `home_attention` already uses), so a
  group counts only when it has active projects that have genuinely never
  synced.
- **Static skeleton headings flashed as grey bars.** "Your courses", "Items
  that need your attention", "Follow the latest updates" and the sidebar panel
  titles (Your progress / Quick access / System health / Latest changes) are
  static, so the dashboard skeleton now renders the real text immediately
  instead of a placeholder. `sk_sidebar_panel` gained a `title` param;
  `<meta robots>` is now a `{% block robots %}` so public pages can opt into
  indexing (the dashboard stays `noindex`).

### Release

- Version `2026.6.8.post10` (no static-asset change; SW cache stays
  `gitpulse-v172`).

## [2026.6.8.post9] - 2026-06-08

### Added

- **Topic-specific support forms.** Support feedback forms now carry a
  `category` (migration `050`), so the form a user fills in matches the chosen
  topic (bug report vs feature request vs other) instead of one generic form.

### Changed

- **Email notifications overhauled.** All `notify_*` builders now share one
  production-grade HTML template (branded header, footer, gradient action
  button, consistent meta tables) in the style of top companies.
- **Subtle global smoothness.** Added/cohered transitions on cards and
  interactive elements (`animations.css`, `cards.css`).

### Removed

- **One-time prod cleanup.** Migration `050` truncates `background_jobs` and
  `audit_log`, clearing the stale "phantom" records that lingered in the feed
  and Job History. (Combined with post8's 14-day feed window, the feed stays
  clean going forward.)

### Release

- Version `2026.6.8.post9`; SW cache bumped to `gitpulse-v171` (cards /
  animations CSS changed).

## [2026.6.8.post8] - 2026-06-08

### Fixed

- **"Follow the latest updates" lingered on months-old rows.** Neither feed
  source actually had a time window (the BackgroundJob comment said "last 30
  days" but the query had no date filter), so once activity went quiet the feed
  showed stale rows - a course created in April, events replayed in May - that
  read as phantom jobs. Both the audit-log and BackgroundJob sources are now
  capped to the last 14 days (`_recent_cutoff`).

### Release

- Version `2026.6.8.post8` (Python-only; SW cache stays `gitpulse-v170`).

## [2026.6.8.post7] - 2026-06-08

### Changed

- **Job History distinguishes the sync scope.** All GitLab syncs share
  `job_type="sync"`, so the Type column showed "GitLab sync" for everything.
  The jobs API now returns `project_id`, and the renderer labels a sync by its
  scope - `Project sync` (project_id), `Group sync` (team_id), `Course sync`
  (course_id) - so a course-wide sync reads differently from a single
  group/project sync.

### Fixed

- **"Follow the latest updates" showed phantom project rows.** The feed pulled
  `project_delete` / `project_reactivate` (Project unlinked / restored) from the
  audit log - admin housekeeping that lingered for days after the project was
  gone. These are now excluded (`AuditLog.action.notin_(...)`), leaving only
  genuine activity.

### Release

- Version `2026.6.8.post7`; SW cache bumped to `gitpulse-v170` (admin-system
  bundle changed).

## [2026.6.8.post6] - 2026-06-08

### Fixed

- **Student-in-group page double-counted data from inactive project copies.**
  When the same repository is linked to a group twice (e.g. an active `master`
  project + a stale inactive `main` re-link, as seen on the team detail page),
  the student page's queries joined `GitLabProject` and filtered only by
  `team_id`, so commits / issues / MRs / notes were pulled from BOTH copies and
  shown doubled. Every one of the 15 queries now also requires
  `GitLabProject.is_active.is_(True)`, so the page shows only the student's real
  work in the active project - no duplication.
- **CI green again.** `home_sync_info.py` was committed unformatted; reran
  `ruff format`.

### Release

- Version `2026.6.8.post6` (Python-only; SW cache stays `gitpulse-v169`).

## [2026.6.8.post5] - 2026-06-08

### Changed

- **Full GitLab sync flow on page refresh.** Clicking the "Refresh" button on Course Analytics or Course Activity now triggers a real background GitLab sync via `/api/v1/courses/{courseId}/sync-all` (for staff). It features button loading states, integrates with the global job progress bar, auto-reloads charts and activity tables on completion, and applies a danger state to the button upon failure.
- **Removed temporary deploy logs.** Deleted root-level temporary log files (`deploy-post21.log`, `deploy-post22.log`) from the repository workspace.

### Release

- Version `2026.6.8.post5`; SW cache bumped to `gitpulse-v169` (core bundle and page-specific JS changed).

## [2026.6.8.post4] - 2026-06-08

### Fixed

- **"Follow the latest updates" still showed phantom sync rows.** The post16
  audit-source exclusion used an exact `notin_(["sync", ...])` list, but the
  feed labels actions by `startswith(prefix)`, so variants like `sync_project`
  / `sync_single` leaked through as "Synced data from GitLab" - rows with no
  matching job in Job History. Now excluded by PREFIX
  (`~AuditLog.action.like("sync%")` etc.) so every sync/check/report/enrich/
  metrics/membership variant is caught and the feed matches Job History.
- **Project members table - misaligned action column.** The optional
  include/exclude toggle (eye) renders only for excludable students, so on
  teacher/mentor rows the "View" button jumped left. Wrapped the actions in a
  right-aligned flex cell (`.gl-row-actions`) so "View" lines up on every row.

### Changed

- **Job History refresh gives visible feedback.** `loadBackgroundJobs` now
  shows a `table-loading` state while fetching (so a manual Refresh always
  looks like it did something even when rows are unchanged), and its error
  state shows a toast plus a "contact support / open a ticket" link.

### Release

- Version `2026.6.8.post4`; SW cache bumped to `gitpulse-v168` (shared.css +
  admin-system bundle changed).

## [2026.6.8.post3] - 2026-06-08

### Fixed

- **Course analytics student count discrepancy.** Corrected the denominator in the analytics checklist to use the total count of active, non-instructor students enrolled in the course's active teams, instead of the count of students with existing metric snapshots.
- **JavaScript SyntaxError.** Fixed an uncaught SyntaxError in `20-week-explorer.js` by correctly closing the IIFE block.

### Changed

- **Enhanced dashboard greeting header.** Added a subtitle below the greeting header that displays the user's role (Administrator, Teacher, Student) and a client-side dynamically formatted and localized date.
- **Improved error states with support ticket links.** Added a secondary "Create Support Ticket" button pointing to `/dashboard/support` to all HTMX lazy-load error states in `30-htmx-progress.js`.
- **Slovak translations parity.** Resolved all missing translation keys in the Slovak catalog (`sk.json`) to achieve 100% localization parity.

### Release

- Version `2026.6.8.post3` (includes updated assets compilation and complete translation parity).

## [2026.6.8.post2] - 2026-06-08

### Changed

- **Synchronized page headers.** Team and Project detail pages now render their page headers (titles, back links, and action buttons) synchronously in the shell templates, avoiding layout shifts and visual delay in drawing page metadata. Skeletons for these pages are cleaned up to exclude duplicate page headers.

### Release

- Version `2026.6.8.post2` (includes asset bundle compilation and unit tests verification).

## [2026.6.8.post1] - 2026-06-08

### Changed

- **Overhauled the skeleton loader system.** Aligned loading placeholder elements 1:1 with real page layouts to prevent layout shifts. Deleted dead/unused page-level skeleton macros (`sk_course_detail`, `sk_analytics`, `sk_course_activity`, `sk_teachers`). Deduplicated teacher manager skeletons by extracting common markup into `_sk_teachers_inner`.
- **Improved teacher profile loading.** Updated the student detail skeleton to support `is_teacher_profile=false` configuration to prevent compliance and diagnostic metrics from rendering when loading teacher profiles, eliminating visual pop-in.
- **Removed legacy duplicate files.** Deleted `src/app/static/favicon.svg` (active version is served from templates/static).

### Release

- Version `2026.6.8.post1` (includes assets rebuild and code deduplication).

## [2026.6.5.post19] - 2026-06-05

### Changed

- **Removed the duplicate "Needs Attention" KPI card; replaced with "Open
  MRs".** The card showed the same RED group count and linked to the same
  place as the "Items that need your attention" feed - pure duplication. It is
  now an `Open MRs` card (new `_count_open_mrs` helper: open merge requests
  across the user's courses, "awaiting review") - an actionable figure shown
  nowhere else and aligned with the assignment's MR/review focus. Dropped the
  now-unused `_needs_attention_link` helper.
- **At-risk navigation moved to where the at-risk info lives.** "Items that
  need your attention" now links straight to the offending group
  (`/dashboard/teams/{id}`) when exactly one group is RED (reusing
  `_red_team_ids`); with several it keeps the course view sorted by status.

### Release

- Version `2026.6.5.post19` (Python-only; SW cache stays `gitpulse-v167`).

## [2026.6.5.post18] - 2026-06-05

### Changed

- **"Needs Attention" KPI card now redirects exactly to the element.** New
  `_red_team_ids` + `_needs_attention_link` helpers: when exactly one group is
  RED, the card deep-links straight to `/dashboard/teams/{id}` instead of the
  generic courses list; with several it keeps the overview (admin: courses,
  teacher: course analytics) where they can all be triaged. `red_teams` is now
  `len(red_ids)`. Together with the earlier Students-card fix, no two KPI cards
  share a destination.

### Release

- Version `2026.6.5.post18` (Python-only; SW cache stays `gitpulse-v167`).

## [2026.6.5.post17] - 2026-06-05

### Changed

- **Student-in-group page: the "Project" column is gone from every table.**
  Removed the `{% if show_project_col %}` header + cell from the commits,
  authored-issues, assigned-issues and merge-request tables (and dropped the
  now-unused `show_project_col` context value + the `?`-conditional in
  `sk_student_detail`, commits skeleton 4->3 cols). On a single-group page the
  project never changes, so the column was pure noise; the GitLab link stays on
  the commit/issue/MR number. Tables now focus on what the ZSI assignment grades
 - the member's own work (DOING) vs peer code review (COMMUNICATING).
- Deleting jobs from **Job History** now also clears them from
  **"Follow the latest updates"**: since post16 the feed's job rows come from
  the same `BackgroundJob` source, and `Purge Old` deletes those rows, so the
  two views stay in lock-step.

### Release

- Version `2026.6.5.post17` (template-only; SW cache stays `gitpulse-v167`).

## [2026.6.5.post16] - 2026-06-05

### Fixed

- **"Follow the latest updates" is now consistent with Job History.** The feed
  used to merge audit-log rows AND BackgroundJob rows, so it showed job-like
  entries ("Synced data from GitLab", "report_generate") that have no matching
  record in the admin Job History - the reported "phantom" rows. Job-like
  actions (`sync`/`sync_team`/`sync_all`/`run_checks`/`import`/`report*`/
  `enrich*`/`metrics`/`membership_sync`) are now excluded from the audit source
  and surfaced only from the SAME BackgroundJob source Job History reads; the
  audit log contributes only genuine non-job events (course/group/member/
  settings/support/event lifecycle).

### Changed

- **Historical lazy-swap transition.** This release introduced an entrance
  transition for lazy fragments. It was retired in `2026.6.11` so swapped SSR
  content appears immediately without blinking.

### Release

- Version `2026.6.5.post16`; SW cache bumped to `gitpulse-v167` (core bundle +
  loaders.css changed).

## [2026.6.5.post15] - 2026-06-05

### Fixed

- **CI is green again.** `requirements.lock` had been regenerated on Windows
  (post12), which added `colorama` and dropped Linux-only `uvloop`, so the
  `lockfile-check` job (which regenerates on Linux and compares byte-for-byte)
  failed and `pip install -r requirements.lock` was wrong for CI's platform.
  Regenerated the lock in a `python:3.12-slim` Linux container with the exact
  CI command (`uv pip compile pyproject.toml --extra otel`).
- **Coverage floor recalibrated 39 -> 38** to reflect deleting the
  well-tested `scheduler.py` (~100 fully-covered statements). Added unit tests
  for every `notify_*` email builder.
- **Dashboard "Follow the latest updates" no longer shows phantom system
  entries.** Telemetry snapshots (which feed the compliance charts) and any
  leftover `scheduled:*` sweep jobs are filtered out of the user activity feed
  for everyone; they remain in the admin Job History.

### Changed

- **"Students" KPI card is no longer a duplicate of "Users".** Both used to
  link to `/dashboard/admin/users`; the Students card now deep-links to
  `?role=student`, and the admin users page reads `?role=` to pre-activate the
  matching role filter pill, so the card lands on a real filtered view.

### Release

- Version `2026.6.5.post15`; SW cache bumped to `gitpulse-v166`
  (`admin-users.js` changed).

## [2026.6.5.post14] - 2026-06-05

### Changed

- **Page-fragment cache TTL raised 60s -> 300s for more instant loads.**
  `page_cache.DEFAULT_TTL_SECONDS` is now 300. Freshness is event-driven, not
  TTL-driven: every data change already invalidates the affected fragments
  precisely - both GitLab webhooks (`event_processor._invalidate_page_cache`)
  and in-app mutations (course/settings/team/project/member edits call
  `invalidate_cascade`/`invalidate_many`), and the whole namespace is busted
  per-deploy via the GIT_SHA suffix. The TTL is only a safety net for a change
  that bypasses both paths, so a longer window simply means far more cache hits
  (instant loads) when a teacher clicks around, with no added staleness risk on
  any real change.

### Release

- Version `2026.6.5.post14` (no static-asset change; SW cache stays
  `gitpulse-v165`).

## [2026.6.5.post13] - 2026-06-05

### Changed

- **Webhook coverage is now complete.** Confidential issues
  (`confidential_issue`) and confidential notes (`confidential_note`) are now
  routed to the same issue/note processors as their public counterparts
  instead of being silently ignored - a confidential issue is still student
  work. `add_project_hook` subscribes to `confidential_issues_events` and
  `confidential_note_events`, and the webhook setup guide
  (`_build_setup_instructions`) now lists every relevant trigger
  (push, tag_push, issues, confidential_issues, merge_requests, note,
  confidential_note, pipeline, member, subgroup) and tells the teacher to
  configure the hook at the **group/sub-group** level - only group webhooks
  deliver Member and Subgroup events, which is how member add/remove and
  reassignment are captured automatically.
- `subgroup` events are now explicitly accepted-and-ignored (no more
  "unhandled kind" warnings); team creation stays a deliberate manual action.

### Release

- Version `2026.6.5.post13` (no static-asset change; SW cache stays
  `gitpulse-v165`).

## [2026.6.5.post12] - 2026-06-05

### Removed

- **All periodic (cron) jobs and the scheduler itself are gone.** Deleted
  `app/workers/scheduler.py`, the `scheduler` Docker Compose service, and the
  `rq-scheduler` dependency (lockfile regenerated). The 2-minute email sweep,
  event-recovery/DLQ/cleanup sweeps and the daily course-archive sweep no
  longer run, so the admin job panel / global job bar are no longer flooded
  with "ghost" jobs that don't map to any user action, and there is zero
  background polling load on GitLab.
- Purged every "periodic scheduling / rq-scheduler" reference from code
  comments, docstrings and the docs site (architecture, deployment, index
  diagrams).

### Changed

- **The system is now purely webhook-driven + manual.** Data refreshes come
  from GitLab webhooks (processed inline) and explicit sync/actions in the UI.
  The maintenance functions (`app.workers.sweep.*`) are kept and remain
  runnable on demand from *System -> maintenance jobs* (`POST .../jobs/trigger`)
 - so anything that used to be periodic is now an admin-controlled action.
- **Email-delivery retries are self-rescheduling.** `deliver_email` now
  re-enqueues itself with an exponential backoff via `Queue.enqueue_in`,
  executed by the worker's built-in RQ scheduler (`with_scheduler=True`) - no
  separate scheduler service required.
- `redeploy.py` now passes `--remove-orphans` so the retired `scheduler`
  container is cleaned up on deploy.

### Release

- Version `2026.6.5.post12` (no static-asset change; SW cache stays
  `gitpulse-v165`).

## [2026.6.5.post11] - 2026-06-05

### Fixed

- **Spam-click protection no longer surfaces a scary error.** The
  `_throttledApiCall` wrapper rejected duplicate in-flight mutations with
  `err.code = 'THROTTLED'`, but callers only special-case `'LOCKED'` (the
  `withUiLock` code), so a fast double-click produced a red "X failed: request
  already in progress" toast. The wrapper now (a) shows the same gentle,
  1.5s-throttled blue "Please wait - the previous action is still running"
  notice the click-lock uses, and (b) throws with `err.code = 'LOCKED'`
  (plus `throttled: true`) so every existing `!== 'LOCKED'` guard across the
  app swallows it. Central fix - no per-button edits.

### Release

- Version `2026.6.5.post11`; SW cache bumped to `gitpulse-v165` (core bundle
  changed).

## [2026.6.5.post10] - 2026-06-05

### Changed

- **Service Accounts table now paginates.** The "Service Accounts" (GitLab
  bots) panel on the Users page got its own `ClientPaginator` (10/20/50 per
  page, default 10), scoped to `#serviceAccountsPanel .users-table tbody` so it
  never collides with the human users table above (which shares the
  `.users-table` class). It reuses the existing pagination component (no
  bespoke logic) and cooperates with column sorting via the standard
  `tbody._clientPaginator.resyncOrder()` hook. A `pagination_controls`
  placeholder was added inside the panel body.

### Release

- Version `2026.6.5.post10`; SW cache bumped to `gitpulse-v164`
  (`admin-users.js` changed).

## [2026.6.5.post9] - 2026-06-05

### Changed

- **Student-in-group loading skeleton now mirrors the restructured page.**
  `sk_student_detail` gained the two group-divider placeholders (`Work by
  <member>` and `Code review & communication`, using `student-group-heading` /
  `student-group-sub`) so the dividers no longer pop in / shift the layout when
  the lazy content swaps. The commits-table skeleton was corrected from 5 to 4
  columns and its comment updated to drop the removed `SHA` column.

### Release

- Version `2026.6.5.post9` (template-only; bundles and SW cache `gitpulse-v163`
  unchanged - no static asset changed).

## [2026.6.5.post8] - 2026-06-05

### Changed

- **Student-in-group page - restructured around the assignment's
  "doing + communicating" split.** The page now opens with two clearly
  labelled group headings so a teacher reads it top-to-bottom as a story:
 - **"Work by &lt;member&gt;"** (`git-commit` icon) - what the member
    *personally produced*: commits, authored/assigned issues and merge
    requests they opened. When viewing your own profile it reads "Work by you".
 - **"Code review & communication"** (`message-square` icon) - the
    *communicating* half: review comments the member wrote on peers' work,
    kept visually separate from feedback others left on the member's own MRs
    (the underlying partial already split "by student" vs "received").
  Headings/sub-text are translatable (`student-group-heading` /
  `student-group-sub`, styled in `pages/student.css`, no inline CSS).
- **Less redundant tables.** The per-row `Project` column in the commits,
  authored/assigned issues and merge-request tables now renders only when the
  group actually spans more than one active project (`show_project_col`); for
  the common single-project group it is dropped since it never changes down the
  page. The standalone `SHA` column in the commits table was removed - the
  GitLab commit link now sits on the commit title.

### Release

- Version `2026.6.5.post8`; SW cache bumped to `gitpulse-v163` (page CSS
  changed for the new group dividers).

## [2026.6.5.post7] - 2026-06-05

### Fixed

- **"Items that need your attention" - stale-sync reminder is now per-course.**
  The old single line ("N projects with stale data", linking to the System
  page) was misleading after periodic sync was removed: with freshness now
  webhook + manual-sync driven, `last_synced_at` age flags most projects. It is
  now grouped per course (e.g. "DEVOPS: 12 projects to sync"), uses a 7-day
  threshold, and each entry links directly to its course where the sync action
  lives.

### Release

- Version `2026.6.5.post7` (no static-asset change; SW cache stays
  `gitpulse-v162`).

## [2026.6.5.post6] - 2026-06-05

### Fixed

- **No-flash greeting (server-side render).** The dashboard greeting
  (`Good morning/afternoon/evening, <name>` + avatar) was rendered inside the
  HTMX-loaded content fragment, so on reload it popped in after the skeleton.
  It now renders in the shell page (`dashboard.html`) from session role context
  with zero DB work, so it paints with the first byte. Its old stats sub-line
  (`N courses · N groups · N students`) was removed - it duplicated the KPI
  cards directly below it.
- **Group-detail skeleton parity.** `sk_team_detail` no longer renders a
  "Group summary" 5-stat card; the real team page has no such card (it was
  removed earlier), so the skeleton no longer shows a block that never arrives.

### Removed

- Deleted the dead `app/compliance/check_defs.py` re-export shim (nothing
  imported it; all callers use `check_registry` directly) and the now-unused
  `_build_greeting_subtitle` helper + its tests.

### Release

- Version `2026.6.5.post6` (no static-asset change; SW cache stays
  `gitpulse-v162`).

## [2026.6.5.post5] - 2026-06-05

### Fixed

- Fixed the **duplicate "Done" state** in the global job bar. When a job's SSE
  `complete` event and the status poller both reported the same completion
  *during* the readable "Finishing" phase, a second readable-terminal sequence
  was started, so the terminal row + completion toast appeared twice.
  `completeGlobalJob()` now treats `finishing` as terminal-in-progress (only the
  scheduled finalizer, which registers itself in `_finishingFinalizers`, may pass
  through; an incoming error can still override), and `_beginReadableTerminalJob()`
  is idempotent against `finishing`.

### Release

- Version `2026.6.5.post5`, Service Worker cache `gitpulse-v162`, core bundle
  regenerated.

## [2026.6.5.post4] - 2026-06-05

### Changed

- **Dashboard KPI cards** (Users/Students/Compliance/Needs Attention) are now real
  navigation links for every role: admin -> `/dashboard/admin/users` and
  `/dashboard/admin/courses`; teacher/student with a single active course ->
  that course detail / analytics. Added a `href` to the `dashboard_stat` macro;
  the clickable styling (cursor/hover/arrow) now applies only to cards that have
  a target, so static cards no longer look misleadingly clickable.

### Removed

- Removed the redundant **System Settings stat strip**
  (Users/Service Accounts/Courses/Groups/Students/Projects) that duplicated the
  dashboard KPI cards, plus the dead JS that populated it. The Role Breakdown
  chart and Refresh Stats button are kept.
- Deep documentation clean-up: all remaining `docs-site` prose references to the
  removed rubric / gaming / async-report / roster-import features were purged
  (uvod, ucitelia, pravne, vyvojari, diplomovka). Zero references remain.

### Release

- Version `2026.6.5.post4`, Service Worker cache `gitpulse-v161`, bundles
  regenerated.

## [2026.6.5.post3] - 2026-06-05

### Removed

- Removed the last retired schema tail via Alembic migration `049`: the legacy
  student compliance snapshot column and orphaned history/report tables.
- Removed the old telemetry PDF report endpoint, schemas, ORM model, generator
  service, and report-only tests.
- Removed stale fixture sections and active docs/i18n/template references for
  retired grading, heuristic, report, and import subsystems.

### Changed

- Full course configuration examples now include only the active sections:
  course metadata, settings, built-in checks, custom checks, weekly deadlines,
  Docker lint config, and CI failure config.
- Updated app/docs metadata to `2026.6.5.post3` and bumped the Service Worker
  cache namespace to `gitpulse-v160`.

## [2026.6.5.post2] - 2026-06-05

### Removed

- Removed the retired **scheduler master switch** from Settings, Docker Compose, scheduler runtime,
  tracked-wrapper checks, admin scheduled registry, manual retry routing, tests,
  README files, and architecture docs.
- Removed the remaining inactive scheduled fallback jobs and their entry points:
  periodic metrics recompute, background-job cleanup, webhook verification,
  dead-project polling, metric-snapshot cleanup, audit-log cleanup, and expired
  webhook-secret cleanup. Runtime freshness now stays on webhook/manual sync
  paths; compliance metrics are recomputed inline by sync/event flows.
- Removed stale activity-feed and global-job label mappings for already-deleted
  periodic GitLab polling/discovery jobs so the UI cannot display retired
  scheduled process names.

### Changed

- Scheduler/admin catalog now lists the 12 active scheduled jobs only:
  event recovery, CI rollback, conflict expiry/verification, optional LLM,
  optional telemetry, DLQ resurrection, optional Docker re-verification, event
  retention, email queue/log retention, and semester auto-archive.
- Updated app/docs metadata to `2026.6.5.post2`, rebuilt static bundles, and
  bumped the Service Worker cache namespace to `gitpulse-v159`.

## [2026.6.5.post1] - 2026-06-05

### Removed

- Removed the **periodic GitLab-polling scheduled jobs** that re-fetched data on
  a timer: `periodic_enrich_all`, `periodic_enrich_users`, `sweep_stale_projects`,
  `sweep_discover_new_projects`, `sweep_discover_new_teams` (plus the now-empty
  `sweep_enrichment.py` and `sweep_discover.py` modules, their `scheduler`
  registrations, `admin_scheduled_registry` / manual-trigger entries, and the
  `scheduler_enrich_interval` / `scheduler_stale_interval` /
  `sweep_enrich_max_jobs_per_run` / `sweep_user_enrichment_batch` settings).
  Data freshness now comes solely from webhooks, manual sync, and the sync that
  runs on course creation.
- Cascade dead-code cleanup of the activity-feed labels tied to the removed jobs.

### Changed

- Deep documentation/thesis clean-up: removed retired grading/retired heuristic/intervention/polling
  references from the developer structure docs, the API reference, and the thesis
  abstract + keywords (`docs-site/docs/diplomovka`, `vyvojari/struktura`,
  `api/index`). The scheduler now registers 19 periodic jobs.

### Release

- Version `2026.6.5.post1`; no static-asset changes (Service Worker cache stays
  `gitpulse-v158`).

## [2026.6.5] - 2026-06-05

### Removed

- Removed the **retired grading grading engine** end-to-end: `Retired grading`/`Retired gradingSuggestion`
  models, `schemas/retired gradings`, `compliance/retired grading_engine*`, `example_retired gradings`,
  the public + dashboard retired grading routers, the retired grading editor/list pages and
  partials, the per-course `active_legacy_grading_id`, and all retired grading scoring blocks in
  the team/student/project dashboards.
- Removed **retired heuristic detection** end-to-end: `compliance/retired heuristic_detection.py` and
  `retired heuristic_types.py`, the engine integration, the `retired heuristic_detection_config`
  course setting + settings UI/endpoint, and the per-student/team retired heuristic-flag
  cards and `retired heuristic_flags` snapshot columns.
- Removed the **Intervention Flags** analytics panel and its `/telemetry/flags`
  create/list/resolve endpoints. The rest of the pilot-telemetry and evaluation
  report subsystem is kept intact.
- Removed the **periodic membership-sync sweep** (`periodic_membership_sync` /
  scheduler registration / `scheduler_membership_interval` /
  `membership_sync_interval_minutes`). Manual sync, GitLab webhooks, course-
  activation sync, and the import-time "Auto-sync after import" option remain.
- Added Alembic migration `048` dropping the now-orphaned `retired heuristic_flags`,
  `retired heuristic_detection_config`, and `active_legacy_grading_id` columns and the `retired gradings` /
  `retired grading_suggestions` tables.

### Added

- Global capture-phase **button click-lock** anti-spam: the first click on any
  action button/link goes through, repeat clicks within 600 ms are swallowed
  with a single throttled "please wait" toast so the user always gets feedback,
  even when nothing changes. Pure UI toggles (dropdowns, tabs, modal open/close)
  are exempt.

### Fixed

- The member-filter **reset button in the skeleton** now sits on the right
  (margin-left:auto) to match the real filter bar instead of floating beside the
  chips.
- Removed leftover retired grading/retired heuristic/flags placeholders from the skeleton loaders so
  loading pages match the real (slimmer) pages.

### Release

- Version `2026.6.5`, Service Worker cache `gitpulse-v158`, regenerated
  bundles/minified siblings, dashboard Latest changes refreshed.

## [2026.6.4.post4] - 2026-06-04

### Removed

- Removed the legacy global gates for retired grading scoring, manual intervention
  flags, retired heuristic heuristics, and GitLab polling automation from settings,
  template globals, API guards, scheduler metadata, docker-compose, tests, and
  documentation. These flows now rely on role access, course settings, and the
  scheduler master switch instead of stale per-feature switches.

### Changed

- Retired grading and retired heuristic configuration imports now apply whenever the course config
  includes those sections; retired grading dashboard routes require teacher/course
  access only.
- Core periodic GitLab polling and cleanup jobs are controlled by the existing
  scheduled-jobs master switch, with compose exposing that switch explicitly.

### Fixed

- System Health now renders `Database`, `Redis`, and `Session_store` in the
  checking skeleton, matching the final operational card and avoiding a layout
  jump.
- Course/team skeletons were rechecked against the current SSR fragments so
  deleted cards do not leave matching placeholder shells behind.

### Release

- Version `2026.6.4.post4`, Service Worker cache `gitpulse-v157`, regenerated
  bundles/minified siblings, dashboard Latest changes refreshed.

## [2026.6.4.post3] - 2026-06-04

### Removed

- **The roster CSV-import feature was removed** (students enter via GitLab
  group/project sync). Dropped the `retired roster switch` flag +
  `roster_max_upload_bytes`, the `/courses/{id}/roster` upload/history API,
  the `roster_service`, the `RosterImport` model + `roster` schema, the import
  UI on the roster page, and the `roster_import` global-job-bar hooks. The
  Roster **view** (enrolled students + CSV export) is unchanged.
- **Team CSV/JSON export removed end-to-end** - the team-detail buttons and the
  `/teams/{id}/export/{csv,json}` endpoints (and the now-unused
  `_filter_scoreable_students` helper).
- **Redundant cards removed**: the course-detail KPI strip (Groups /
  Contributors / Green Status / Needs Attention) and the duplicate student
  **Compliance Checks** card (the Compliance Progress card already covers it).

### Changed

- **Dashboard KPIs are grading-focused.** Admin and teacher home cards replace
  the raw "Groups" count with **Needs Attention** (groups with failing checks).

### Fixed

- **Week Analytics doughnut tooltip restored.** The chart had all mouse events
  disabled; hovering an arc now shows the compliance % in a tooltip anchored
  above the centre score.
- **Student profile is tighter.** Removed the extra divider line above the
  email/GitLab/role meta row.
- **Loading states no longer flash.** The System Health check holds its
  "checking" panel for a readable minimum instead of vanishing in a few ms;
  buttons stay disabled for the whole request (anti-spam).
- **Skeleton loaders match the real pages again** - dropped the deleted
  stat-card/category-chart/compliance-checks placeholders, switched the student
  profile skeleton to the flat meta row, and made the Week Analytics skeleton a
  hollow ring instead of a filled disc.

### Docs

- Removed the roster CSV-import section from the teacher getting-started guide
  (kept the automatic GitLab detection + roster export note).

### Release

- Version `2026.6.4.post3`, Service Worker cache `gitpulse-v156`, regenerated
  bundles/minified siblings, dashboard Latest changes refreshed.

## [2026.6.4.post2] - 2026-06-04

### Removed

- **The async "Retired Report" feature was removed end-to-end.** The team
  report API (`/teams/{id}/report`, `/reports/{file}`), the `report_job`/
  `report_html` workers, the orphaned `retired_report` service, the
  `retired report switch` flag with its `cleanup_old_reports` sweep + retention
  config, the `generate_report` global-job-bar registrations, the team-detail
  button, the related i18n strings and the tour step were all deleted. The
  separate telemetry evaluation-report subsystem is untouched.
- **Redundant dashboard cards were dropped.** Course-activity "Summary",
  course-analytics "Compliance by Category" (incl. its Chart.js renderer and the
  backend category roll-up) and the team "Group Summary" card were removed.

### Fixed

- **Stat cards render one consistent way.** The inconsistent `stat-card--glow`
  hover/focus highlight (present on some cards, absent on others) was removed so
  every stat card shares the same neutral hover plus the standard keyboard
  focus ring.
- **Student profile facts are no longer nested cards.** Email / GitLab / Role
  moved from card tiles into a flat `profile-meta` row inside the profile card.
- **Button loading states no longer flash and resist spam.** `setButtonLoading`
  now holds the loading state for a minimum visible duration before resetting
  (so fast responses don't blink) while keeping the button disabled for the
  whole in-flight window - applied centrally to every button (System Health,
  refreshes, syncs, etc.).
- **The empty Week Analytics compliance ring is visible again.** Its no-data
  state used 6%-opacity white (invisible on the dark background); it now uses a
  visible slate, matching the activity pipeline doughnut.

### Changed

- **Release metadata refreshed for `2026.6.4.post2`.** Version bump, regenerated
  bundles/minified siblings, dashboard Latest changes, and the Service Worker
  cache namespace (`gitpulse-v155`).

## [2026.6.4.post1] - 2026-06-04

### Fixed

- **Course analytics refresh now uses one SSR/cache-busted path.** The stale
  evaluation-report surface, report Alpine factory, tour step, local report
  job hooks and report skeleton were removed from the course analytics page and
  generated bundles. The analytics refresh action now reloads the SSR lazy
  fragment with a cache-busting parameter before falling back to the shared
  scroll-preserving reload helper.
- **Sync completion now waits for fresh metrics before terminal SSE.** Project
  syncs recompute team metrics inline before marking the sync completed, and
  webhook/metrics side effects invalidate SSR/page-cache fragments before
  notifying live clients. No-change summaries now say that no GitLab records
  were found in the configured course window while metrics/cache refresh still
  completed.
- **Profile/stat cards keep useful interaction without entrance animations.**
  Student profile metadata is back in compact cards without appearance
  animations, course KPI cards now link to the relevant groups/roster sections,
  and glow/process animations remain available without duplicate card-entry
  effects.
- **Analytics and system micro-UX were tightened.** The Week Analytics doughnut
  now uses an HTML centre label with disabled chart tooltip hitboxes, and the
  System Health checking state keeps a spinner/glow without harsh blinking.
- **Release metadata is current for `2026.6.4.post1`.** Dashboard Latest
  changes, docs, generated bundles/minified siblings and the Service Worker
  cache namespace (`gitpulse-v154`) were refreshed.

## [2026.6.4] - 2026-06-04

### Fixed

- **Sync/check terminal states are now one readable flow everywhere.** Direct
  SSE/polling completions for course, team, project syncs and run-check jobs
  enter the shared `Finishing` state first, stay visible for the minimum
  readable window across navigation, and only then move to the canonical
  `Done` row/toast. The finalizer guard prevents the Finishing timer from
  re-entering Finishing, so `Done` is emitted once instead of being skipped or
  duplicated.
- **SSR refreshes after data updates now bypass stale page caches.**
  `reloadKeepScroll()` preserves scroll/toasts but reloads through a
  cache-busting URL parameter and removes it on boot, so pages that refresh
  after SSE/mutation/job completion fetch fresh server-rendered data instead of
  reusing an old page-cache body.
- **No-change sync completions are explicit.** Project and team sync workers now
  report that no GitLab changes were found while metrics/cache refresh still
  completed; team summaries also include commit counts in the normal changed
  path.
- **Appearance animation duplicates were removed from the affected SSR views.**
  The student detail profile no longer renders four separate Email/GitLab
  access cards; the same metadata is compactly shown in the profile header.
  Legacy counter/glow/card entrance animations were removed from the touched
  course, project, support, student and team surfaces.
- **Release metadata is current for `2026.6.4`.** Dashboard Latest changes,
  docs, generated bundles/minified siblings and the Service Worker cache
  namespace (`gitpulse-v153`) were refreshed.

## [2026.6.3.post6] - 2026-06-03

### Fixed

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

## [2026.6.3.post5] - 2026-06-03

### Fixed

- **Dashboard post-sync refreshes now use one live-data path.** Dashboard SSE
  updates, global job-complete fallbacks and tab-return refreshes now fan out
  through one helper for stats, attention items, activity and sidebar badges,
  so the home page does not refresh only part of its data after sync.
- **Dashboard short-TTL live caches are invalidated before SSE pushes.** The
  worker dashboard notification path now clears `dashboard:stats:*` and
  `dashboard:badges:*` Redis keys before publishing `dashboard:global`, so an
  immediate post-sync refresh does not read stale 5-second cache values.
- **Dashboard loading skeleton matches the requested course density.** The
  `Your courses` skeleton now renders two course cards instead of three.
- **Release metadata is current for `2026.6.3.post5`.** Application/docs
  examples, dashboard Latest changes, generated bundles/minified siblings and
  the Service Worker cache namespace (`gitpulse-v151`) were refreshed.

## [2026.6.3.post1] - 2026-06-03

### Fixed

- **Course sync finishing now stays readable across navigation before moving to
  Done.** The global job bar now restores `finishing` as its own state, keeps it
  visible for a minimum window, and then completes through the normal
  `completeGlobalJob()` path so the canonical "Sync completed!" row and toast
  are not swallowed during page bootstrap. `/sync/active` grace snapshots with
  `running=0, queued=0` no longer delete/recreate the row or rewrite it back to
  running, and the course-detail page treats that zero-work active snapshot as
  Finishing instead of scheduling an immediate reload.
- **Completed welcome tours no longer reappear after DOM fingerprint drift.**
  Single-stage tour completion migration now scans the actual prefixed
  `gp_tour_v2:` localStorage keys, so older per-stage completion records are
  promoted to the global completed key correctly. Tour-seen POSTs also use
  `keepalive` and retry after failed responses, so a fast navigation after Done
  does not permanently lose server-side tour state.
- **Release metadata is current for `2026.6.3.post1`.** Application/docs package
  versions, docs-site `latest`, operator/developer version examples, dashboard
  Latest changes, and the Service Worker cache namespace (`gitpulse-v147`) were
  refreshed.

## [2026.6.3] - 2026-06-03

### Fixed

- **Course sync finishing survives navigation and completed welcome tours stop
  re-prompting.** This release introduced persistence for `lastUpdate` and
  `finishingSince`, plus welcome-tour completion migration/retry handling.

## [2026.6.2.post24] - 2026-06-02

### Fixed

- **Process-locked buttons no longer collapse to mismatched widths during a
  sync.** While a sync runs, mutating actions (e.g. Edit Course, Archive Course
  in the Course Actions menu) are process-locked, and the lock wraps each control
  in a `<span class="gl-tip-wrap">` so the disabled-reason tooltip can fire on
  hover. That span had no styling and defaulted to `display: inline`, so it
  shrink-wrapped any full-width (`btn-block`) button down to its text width while
  sibling unlocked buttons stayed full-width - stacked menus rendered
  chaotically uneven button widths. The wrapper now mirrors a `btn-block`
  child's full-width block box.
- **Course-card sync badge can no longer get stranded on a stale
  "Finishing.../Syncing..." pill.** A trailing `gp:job-update` arriving right
  after a job completed could re-label (or resurrect) a card badge whose job had
  already finished, leaving the card stuck on "Finishing..." while the global bar
  already showed "Sync completed!". The update handler now ignores events for
  jobs that are already terminal, and a defensive sweep clears any badge whose
  underlying global job is done/error on every completion and on tab refocus.

## [2026.6.2.post23] - 2026-06-02

### Fixed

- **GitLab Intelligence cards now render fully server-side.** The Protected
  Branches, Contributors and Repository Stats cards (and the Last Synced row)
  on the project page used to be emitted with `-` placeholders and then filled
  in by JavaScript on the first SSE `connected` event, with a `fadeSlideUp`
  entrance animation - so the above-the-fold stats visibly popped in. A new
  `gl_intel_view` is now computed in the route (mirroring the JS render logic:
  byte formatting, contributor merge/sort, stats parsing) and the template
  renders the card bodies directly. The entrance animation on the info bar and
  API panel cards was removed, and the dead client-side preload-JSON path
  (`gp-gl-intelligence`) plus the first-connect JS repaint were deleted. Live
  refreshes (sync / job-complete) still re-fetch and re-render as before.

## [2026.6.2.post22] - 2026-06-02

### Fixed

- **Course, team and project pages no longer flicker on load.** The dashboard
  already skipped its first SSE `connected` refresh and trusted the
  server-rendered values; the three detail pages did not - they fired a full
  `/live-data` fetch + repaint the instant the SSE stream connected, so the
  freshly server-rendered cards/rows were briefly overwritten (the
  blank-then-JS flicker). All three now carry a `_connectedOnce` guard
  (mirroring the dashboard) that skips the first `connected` repaint and only
  refreshes on a genuine reconnect. Live SSE change events still repaint as
  before. On the project page the lazy GitLab-intelligence load still runs on
  first connect (it is not server-rendered, so there is nothing to flicker
  over).
- **Job progress messages now share one formatter everywhere; duplicated code
  removed.** The admin view had its own `_translateJobMsg` / `_jobTypeLabel` /
  `_JOB_TYPE_LABELS`, while the global job bar showed the raw English
  `result_summary` (e.g. `Synced N issues, N MRs...`) untranslated. A single
  `GP.formatJobMessage` / `GP.jobTypeLabel` now lives in `core/00-base.js`; the
  global job bar formats at the display boundary (completion toast + live row)
  and the admin view delegates to it. The formatter is idempotent, so
  already-translated strings pass through unchanged.

## [2026.6.2.post21] - 2026-06-02

### Fixed

- **Deleting or restoring a whole group now refreshes every stat, not just the
  project view.** Project unlink/restore already recomputed metrics and pushed
  an SSE nudge, but group delete/reactivate only invalidated the page cache -
  they never published an SSE event nor recomputed the snapshot. So after
  deleting a group the open course page kept its stale group list, summary
  cards, activity feed and analytics until a manual reload. Group delete and
  reactivate now commit explicitly, publish a `team_deleted` /
  `team_reactivated` SSE event on both the team and course channels, and
  enqueue a metrics recompute. The team and course pages treat these as
  structural events and re-render server-side (scroll preserved).

## [2026.6.2.post20] - 2026-06-02

### Fixed

- **Unlinking a project now updates the Group Summary numbers too.** The
  summary cards (avg score, traffic-light status, pipeline pass rate) are
  served from the latest stored `TeamMetricSnapshot`, which is only rebuilt by
  a metrics recompute - never by the unlink itself. So the list/count updated
  but the headline numbers stayed frozen on the unlinked project's old
  contribution. Unlink and reactivate now enqueue a metrics recompute (the
  compliance engine already excludes `is_active=False` projects); when it lands
  it publishes a `metrics_computed` SSE nudge so the open team/course/dashboard
  pages refresh the cards live.

## [2026.6.2.post19] - 2026-06-02

### Fixed

- **Unlink/restore now truly refreshes instead of only showing a toast.** The
  dashboard SSE nudge was published from inside the request handler *before*
  the transaction committed (the session commits after the handler returns), so
  the client's instant live-data refetch raced the still-open transaction and
  re-read the project as active - the "Data updated" toast fired but nothing
  changed. Unlink and reactivate now commit explicitly and only then publish the
  SSE event (`expire_on_commit=False` keeps the captured ids valid).
- **The unlinked project row now disappears from the list.** `refreshTeamData()`
  patched stat cards, member rows, and retired grading scores but never the
  server-rendered "Subgroups and Projects" list, so the unlinked row lingered.
  Structural project events (unlink / restore / link) now trigger a
  scroll-preserving server-side re-render on the team and course pages, so the
  list, the Deleted count, and the summary cards all reflect committed truth.

## [2026.6.2.post18] - 2026-06-02

### Fixed

- **Unlink/restore now updates the whole UI live.** Unlinking or reactivating
  a project now publishes a dashboard SSE event for its team and course, so
  open dashboard, course, and analytics views refresh their stats cards,
  activity feed, and metrics immediately instead of waiting for a manual
  reload.
- **No more duplicate progress bars.** A single sync/restore action could
  surface two rows in the global progress bar - a project-scoped
  "Syncing project..." row plus a course-level aggregate row from
  `/sync/active`. The `/sync/active` reconciler now suppresses the course
  aggregate while a project-/team-scoped sync row for the same course is
  already tracked, and the render pass collapses any remaining same-course
  rows into one as a safety net.

## [2026.6.2.post17] - 2026-06-02

### Added

- **Time-of-day dashboard greeting.** The home greeting now shows "Good
  morning / Good afternoon / Good evening" based on the viewer's local clock
  (server-translated, with an "Hi" fallback when JavaScript is off), and
  re-evaluates on tab-return so a tab left open past noon/midnight updates
  instead of showing a stale word.
- **Live "Follow the latest updates" feed.** The activity feed was extracted
  into a standalone fragment served from `/dashboard/activity` and now
  refreshes live over the dashboard SSE stream (polling fallback retained),
  re-initialising Alpine on the injected node so the show-more toggle keeps
  working. The feed also gained group/project lifecycle events - group and
  project deletion and restoration now appear with their own icons, labels,
  and links.

### Fixed

- **Headline counters count only active items.** The "Groups" counter
  (`/dashboard/` and `/dashboard/stats`) and the project counts driving
  per-team pipeline health now filter `is_active`, so unlinked/deleted groups
  and projects (and GitLab `deletion_scheduled` tombstones) drop out
  immediately instead of inflating the cards.

### Changed

- **Admin system "active jobs" grid is SSE-first.** The scheduled-jobs panel
  now reacts to the dashboard SSE stream instead of waiting up to 10 s, with
  the existing 10 s interval retained purely as a polling fallback and the
  standard reconnect / visibilitychange / health-change handling.
- **Static assets and release metadata are current for `2026.6.2.post17`.**
  JS/CSS bundles and minified siblings were rebuilt, the service-worker cache
  namespace is `gitpulse-v139`, and dashboard Latest changes was refreshed.

## [2026.6.2.post16] - 2026-06-02

### Fixed

- **Course config auto-import no longer depends on dashboard route internals.**
  `scripts/import_course_configs.py` now imports the dedicated
  `course_settings_config` config-application module directly, keeping CLI
  bootstrapping out of HTTP route re-exports and restoring strict mypy.
- **Shared form components preserve their declared API.** Bare text inputs now
  keep validation attributes such as `pattern`, `minlength`, and `autofocus`;
  bare checkboxes submit the caller-provided value; and required custom
  dropdowns validate through a focusable proxy control instead of an ignored
  `required` hidden input.
- **The local security scan wrapper reports production dependency risk.**
  `scripts/security_scan.py` now uses timezone-aware timestamps, parses
  `pip-audit` JSON even when the tool emits advisory text, and audits
  `requirements.lock` by default instead of reporting unrelated packages from
  the developer virtualenv.

### Changed

- **Static assets and release metadata are current for `2026.6.2.post16`.**
  JS/CSS bundles and minified siblings were rebuilt, the service-worker cache
  namespace is `gitpulse-v138`, docs-site `latest` points to this release, and
  dashboard Latest changes was refreshed.

## [2026.6.2.post15] - 2026-06-02

### Fixed

- **The shared SSE job helper now has an explicit polling fallback contract.**
  Manual fallback uses `GP.apiCall` instead of relying on an accidental global
  identifier, and completion callbacks are isolated so a page-level callback
  error cannot leave an EventSource or fallback poller running forever.
- **The global progress bar no longer persists removed ETA state.** The ETA
  UI was already removed in favour of elapsed time, but the old `eta` field
  still leaked through localStorage and cross-tab merges. That legacy state is
  now ignored and no longer written.
- **Small static inline styles were moved into component CSS.** Cookie banner
  links, dashboard quick-access avatar colours, the service-account summary
  header, and the dropdown avatar dimensions now use classes instead of
  repeated inline declarations.

### Changed

- **Release metadata is current for `2026.6.2.post15`.** docs-site `latest`
  points to this release, dashboard Latest changes was refreshed, and the
  service-worker cache namespace is `gitpulse-v137`.

## [2026.6.2.post14] - 2026-06-02

### Added

- **The docs-site Diplomovka section is synced with the current thesis
  repository.** Slovak chapters now mirror the latest LaTeX source from
  `dp.mykyta.olym/thesis`, including the new solution-design and conclusion
  pages, thesis index metadata, Mermaid architecture/event-flow diagrams, and
  refreshed chapter navigation.
- **A repeatable thesis-to-docs sync script now exists.**
  `scripts/sync_thesis_docs.py` converts the thesis LaTeX chapters through
  Pandoc, handles project-specific glossary/reference/table/diagram macros, and
  keeps the docs mirror deterministic instead of relying on manual copy-paste.

### Changed

- **Thesis goal/status docs and Latest changes are current for this release.**
  The goals page now links the completed design chapter, records deployment and
  impact evaluation as the next phase, dashboard Latest changes includes this
  docs refresh, docs-site `latest` points to `2026.6.2.post14`, and the
  service-worker cache namespace is `gitpulse-v136`.

## [2026.6.2.post13] - 2026-06-02

### Fixed

- **Generic job progress no longer starts duplicate fallback pollers after an
  SSE failure.** `streamJobProgress()` already owns the SSE-to-polling
  transition, but the global job bar also started its legacy poller from the
  error callback. That could close the helper while it was switching modes and
  leave duplicate timers or redundant `/api/v1/jobs/{id}` requests. The job
  bar now delegates fallback to the shared streaming helper, and the helper
  re-checks whether it was closed before starting internal polling.
- **GitLab recovery toasts no longer appear under the main backend-health
  banner.** A GitLab-only "connection restored" toast during a broader backend
  outage was misleading; the toast now fires only when the GitLab banner itself
  is still the visible health state.
- **Release metadata and docs-site versions are current again.** The
  application version is `2026.6.2.post13`, docs-site latest points to the same
  version, service-worker cache namespace is `gitpulse-v135`, dashboard Latest
  changes is refreshed, and stale docs references to `2026.6.2.post4` were
  updated.

## [2026.6.2.post12] - 2026-06-02

### Fixed

- **Dismissing a running sync no longer re-enables the buttons it locked.**
  Clicking the X on a still-running job in the global progress bar deleted the
  job from the in-memory registry that the process-action guards read, so the
  Sync / Run Checks / Unlink / Delete Group buttons (which carry
  `data-process-lock-when`) wrongly re-enabled mid-sync. Dismissing a running
  job now only hides its progress row - the job stays active so the buttons
  remain locked and the poller keeps tracking completion; it is removed
  normally once the sync actually finishes.
- **A project can no longer be restored while its group is deleted.** Restoring
  a single project under a soft-deleted group would leave it orphaned (active
  yet hidden everywhere the group is hidden, and excluded from the course
  aggregate). The restore endpoint now rejects this with a clear message, and
  the project page shows a dedicated "This project's group is deleted" banner
  that points teachers to restore the whole group instead.

## [2026.6.2.post11] - 2026-06-02

### Fixed

- **A single project restore or sync no longer pops two "Sync completed"
  toasts.** The per-project sync fired its own completion toast ("Sync
  completed") while the course-level aggregate fired another ("Sync
  completed!"). Their wording differs, so the 5-second text dedup missed them,
  and their job keys differ, so the session dedup missed them too - and the
  faster project toast appeared early, before the aggregate finished.
  Per-project / per-team completion toasts are now collapsed into the
  authoritative course-level aggregate toast, so one operation shows exactly
  one toast at the right time.
- **Restored the `ruff-check` / `ruff-format` CI lint gate.** A helper script
  (`scripts/extract_pdf_annots.py`) had unsorted imports and an unformatted
  body that failed the lint job; it is now sorted and formatted.

## [2026.6.2.post10] - 2026-06-02

### Fixed

- **The global progress bar no longer shows two rows for a single project
  restore or sync.** Restoring/syncing one project registers a per-project
  "Syncing project..." entry, but the same work is also surfaced as a
  course-level aggregate ("DEVOPS: Syncing...") because `/sync/active` counts
  running jobs per course. The earlier dedup only collapsed the two while
  *both* were still running, so a project sync that finished first (common on
  tiny/empty repos) left a second "Sync completed" row. The per-project /
  per-team sync entry is now collapsed into the course aggregate for the same
  course regardless of completion state, so one operation shows exactly one
  row.

## [2026.6.2.post9] - 2026-06-02

### Fixed

- **Unlinking or restoring a project or group now reflects instantly without
  having to leave and re-enter the page.** The detail pages serve their heavy
  content from a short-lived (60s) Redis page-fragment cache, but the
  unlink/restore endpoints never dropped that cache - so the in-place reload
  kept re-serving the previous (still-active or still-unlinked) body until the
  TTL expired, which is why only navigating away and back appeared to work.
  `DELETE /projects/{id}`, `POST /projects/{id}/reactivate`,
  `DELETE /teams/{id}` and `POST /teams/{id}/reactivate` now invalidate the
  affected project / group / course / student page caches immediately, so the
  reloaded page shows the new state right away (this also clears the phantom
  duplicate progress-bar row that lingered while the stale page re-registered
  the in-flight sync).

## [2026.6.2.post8] - 2026-06-02

### Fixed

- **Pages no longer fade, slide or blink when they load.** Removed every
  entrance/appearance animation: the cross-document page crossfade
  (`@view-transition`), the whole-page "page-enter" reveal, the staggered
  fade-in of lazy-loaded cards, and the alert/banner slide-in. Content now
  paints instantly and stays static, so nothing flickers or double-exposes on
  load, reload or live refresh. The matching dead CSS and JS were deleted
  rather than just disabled.
- **Unlinking or restoring a project now reflects immediately.** The page
  reload that flips the server-rendered banner and action buttons was being
  masked by the cross-document view-transition snapshot, which kept the old
  page painted on top - so the change only appeared after leaving and
  re-entering the project. With the view transition gone the reload repaints
  cleanly and the unlinked/restored state shows right away.
- **The global progress bar no longer shows a duplicate "Waiting in queue..."
  row.** While a course-level sync is running, the redundant per-project /
  per-team sync entry for the same course is now collapsed into the course
  aggregate, so a single restore/sync shows one row instead of two.

## [2026.6.2.post7] - 2026-06-02

### Fixed

- **Restoring a project no longer leaves the sync job spinning forever.** The
  reactivate endpoint previously enqueued the refresh directly on RQ and
  returned the raw RQ job id, but the global progress bar polls
  `GET /api/v1/jobs/{id}` which resolves a `BackgroundJob` row - so the opaque
  RQ id 404'd forever and the "Syncing project..." bar never completed. The
  endpoint now creates a real `BackgroundJob` (mirroring the normal project
  sync) and returns its id, so the bar tracks progress and finishes cleanly.
- **The project page now refreshes its data the moment a restore/sync
  finishes.** Added a `gp:job-complete` handler that re-fetches contributors,
  commits and pipelines in place, so you no longer have to leave the project
  and come back to see the updated numbers.
- **Small cards no longer flicker / "activate twice".** The staggered entrance
  animation on lazy-loaded panels (Contributors, Repository Stats, Protected
  Branches) re-ran on every live data refresh; it now runs at most once per
  container, so refreshes update the content without re-animating.

## [2026.6.2.post6] - 2026-06-02

### Fixed

- **Restoring an unlinked project no longer freezes on "Restoring...".** The
  post5 reactivate flow waited for the background refresh job to stream to
  completion before reloading the page; for an empty or slow repository that
  completion never arrived promptly, so the "Restoring..." button and the
  global progress bar hung for 20-40+ seconds and the page never reloaded
  (forcing the teacher to navigate away and back to see the restored state).
  The project page now registers the refresh job in the persistent global
  progress bar (with its job id/kind) and reloads immediately, so the project
  shows its restored/active state right away while the sync is tracked in the
  background across the reload.

## [2026.6.2.post5] - 2026-06-02

### Fixed

- **Unlinking a project or deleting a group no longer ejects you to another
  page.** Both actions now reload the current page in place so the teacher/admin
  immediately sees the "unlinked"/"archived" banner and the Restore button,
  instead of being redirected to the group or course page ("kicked out").
- **Restoring a project now surfaces the background sync and refreshes the data
  when it lands.** The reactivate endpoint returns the enqueued refresh job id;
  the project page attaches it to the global progress bar, streams progress, and
  reloads only once the sync actually completes (instead of a blind 500 ms
  reload that showed stale numbers).
- **Empty repositories now state they are not counted.** The empty-repo warning
  on the project page now explicitly says the project is excluded from the group
  average and rankings until the team pushes code, so a zero-commit project that
  leaves the average unchanged is no longer confusing.

## [2026.6.2.post4] - 2026-06-02

### Fixed

- **GitLab `deletion_scheduled` tombstone projects are no longer ingested or
  shown as restorable groups.** When GitLab schedules a project for deletion it
  renames the path to `<path>-<hash>-deletion_scheduled-<id>` but keeps it
  visible in the group-projects API for a short window. The project-discovery
  sweep now skips those tombstones, and the course and team detail listings
  filter them out, so a project the teacher never deleted no longer appears as a
  ghost "Deleted" group with anomalous/empty data.
- **Entrance animations and skeleton loaders no longer blink on first page
  load.** The page-enter reveal previously suppressed only a hard-coded handful
  of child element classes, so other simple cards and skeletons still ran their
  own fade/slide at the same time as the page reveal and read as a double-
  exposure flicker. The suppression now covers all descendants during the reveal
  while leaving looping loader feedback (spinners, dots, bar/skeleton shimmer,
  status pulses) untouched.

### Changed

- Application/docs metadata is bumped to `2026.6.2.post4`; the service-worker
  cache namespace is bumped to `gitpulse-v128`, generated bundles/minified
  siblings are rebuilt, and dashboard Latest changes is refreshed.

## [2026.6.2.post3] - 2026-06-02

### Added

- **Teachers can now restore soft-deleted groups and unlinked projects.**
  `POST /api/v1/teams/{team_id}/reactivate` and
  `POST /api/v1/projects/{project_id}/reactivate` are no longer admin-only;
  any teacher with course access can restore. Restoring a group precisely
  re-enables the members and projects that the most recent delete deactivated
  and enqueues a background sync so rankings, metrics and checks pick the group
  back up immediately.
- **Students keep read-only visibility of their own archived group's score.**
  Deleted groups and unlinked projects stay reachable for their members with a
  clear archived banner explaining the data is frozen for reference, while
  staff see Delete/Unlink badges plus restore buttons and a toggle to show or
  hide archived rows.

### Fixed

- **Deactivated groups and projects no longer inflate course aggregates.**
  Contributor totals, green/red status counts, never-synced and stale-data
  indicators, and sync counters on the course page now consider only active
  groups. `compute_team_metrics`, the metrics worker, and the project sync
  worker all skip archived groups/projects so scoring, rankings and analytics
  exclude them consistently.

### Changed

- Application/docs metadata is bumped to `2026.6.2.post3`; the service-worker
  cache namespace is bumped to `gitpulse-v127`, generated bundles/minified
  siblings are rebuilt, dashboard Latest changes is refreshed, Slovak
  translations are completed (0 missing strings), and restore endpoints return
  DTO-style JSON responses covered by unit tests.

## [2026.6.2.post2] - 2026-06-02

### Fixed

- **Dangerous group/project actions now have backend job guards.**
  `DELETE /api/v1/teams/{team_id}` and `DELETE /api/v1/projects/{project_id}`
  serialize against team/project mutation scopes and return `409 Conflict`
  while `sync` or `run_checks` is active, so direct API calls cannot bypass the
  UI process guard and race score or project-state writers.
- **Delete Group now also unlinks the group's projects.** Soft-deleting a group
  deactivates its active `GitLabProject` rows as well as active members, keeping
  dashboard state, sync discovery, and webhook handling aligned with the UI
  contract.
- **Unlinked projects no longer keep processing webhooks.** Authenticated
  GitLab webhooks for inactive projects now return `ignored` without creating a
  `WebhookEvent`, so an unlinked project stays skipped until explicitly
  reactivated.
- **Course detail Delete Group uses the clicked button context.** Row removal no
  longer relies on a substring selector over `data-action-args`, and scoring
  toggle buttons now carry declarative `sync run_checks` process locks.
- Application/docs metadata is bumped to `2026.6.2.post2`; the service-worker
  cache namespace is bumped to `gitpulse-v126`, generated bundles/minified
  siblings are rebuilt, dashboard Latest changes is refreshed, and destructive
  action guards are covered by focused unit/source-pattern tests.

## [2026.6.2.post1] - 2026-06-02

### Fixed

- **Dashboard Latest changes now handles non-positive limits deterministically.**
  `_get_changelog_entries(limit=0)` and negative limits return an empty list
  instead of relying on Python's negative slicing semantics, which previously
  made `limit=-1` return almost the whole widget feed.
- **Dashboard changelog release-date validation follows the package version.**
  The regression test derives the current release day from `pyproject.toml`
  CalVer metadata instead of carrying a hand-maintained duplicate date, so
  same-day and dated releases cannot drift from the package version.
- Application/docs metadata is bumped to `2026.6.2.post1`; the service-worker
  cache namespace is bumped to `gitpulse-v125`, generated bundles/minified
  siblings are rebuilt, dashboard Latest changes is refreshed, and widget
  limit/date contracts are covered by unit tests.

## [2026.6.2] - 2026-06-02

### Fixed

- **Team member role/score badges no longer show stray ellipsis dots on narrow
  tables.** The team members table still truncates text-heavy cells, but
  badge-only cells now opt out of `text-overflow: ellipsis` with a dedicated
  `member-badge-cell` contract, so `Mentor`, `Maintainer` and score badges do
  not render a dangling dot beside the pill.

### Changed

- **Team member access-role badge logic is now single-source.** The duplicated
  Role-column branch ladder in the student and staff table variants moved into
  the shared `member_access_role_badge()` member component.
- Application/docs metadata is bumped to `2026.6.2`; the service-worker cache
  namespace is bumped to `gitpulse-v124`, generated bundles/minified siblings
  are rebuilt, dashboard Latest changes is refreshed, and the badge overflow
  contract is covered by unit tests.

## [2026.6.1.post8] - 2026-06-01

### Fixed

- **Docs-site Nginx no longer leaves custom 404 responses cacheable or
  indexable.** The internal `/404.html` error-page location now repeats the
  explicit `Cache-Control: no-store, no-cache, must-revalidate` header and adds
  `X-Robots-Tag: noindex, nofollow, nosnippet`, closing the header-inheritance
  gap introduced by Nginx `add_header` location scoping.
- **Docs-site health checks are exact and plain text.** `/health` is now an
  exact location with `default_type text/plain`, so arbitrary `/health...`
  paths no longer look healthy and the endpoint does not rely on `add_header`
  for `Content-Type`.
- Application/docs metadata is bumped to `2026.6.1.post8`; the service-worker
  cache namespace is bumped to `gitpulse-v123`, generated bundles/minified
  siblings are rebuilt, dashboard Latest changes is refreshed, and nginx header
  contracts are covered by unit tests.

## [2026.6.1.post7] - 2026-06-01

### Fixed

- **Every timestamp now renders in the viewer's local timezone instead of
  UTC.** "Last Synced" on the project page (which was missing the
  `data-localize-time` marker and used a timezone-less `isoformat()`), plus
  commit, issue, merge-request, CI-scenario, conflict, Docker-report, roster
  import and analysis times, were emitting raw server UTC. They now all route
  through one shared `local_time()` Jinja global that renders a canonical
  `...Z` `<time data-localize-time>` element; the client `localize-time.js`
  converts it in place and gained `data-localize-format` support so custom
  formats (`HH:MM`, `Mon DD, HH:MM`) survive localization. This removes ~19
  ad-hoc `strftime` inlines in favour of a single source of truth.
- **The browser's native white pull-to-refresh spinner no longer appears on
  mobile and installed PWA.** The `overscroll-behavior-y: contain`
  suppression lived only on `<body>`, but per spec the property must sit on
  the root `<html>` element to reach the viewport, so Chrome's native
  pull-to-refresh kept firing alongside the app's own indicator. The rule now
  also targets `<html>`.
- Application/docs metadata is bumped to `2026.6.1.post7`; the service-worker
  cache namespace is bumped to `gitpulse-v122`, generated bundles/minified
  siblings are rebuilt, and dashboard Latest changes is refreshed.

## [2026.6.1.post6] - 2026-06-01

### Fixed

- **The "Last Updated" column in the course groups table no longer flickers
  between UTC and local time.** Two independent SSE feeds (`/sync-stream` and
  the `/live-data` poll) were writing the same cell with different formats - one
  rendered a localized `<time>` (user-local), the other stomped it with the raw
  server UTC string - so the value visibly bounced on every tick. Both feeds now
  route through a single `_renderLastUpdated()` helper that is idempotent and
  keyed off the canonical UTC ISO timestamp: once a value is rendered and
  localized it is never rewritten until `computed_at` actually changes.
- Application/docs metadata is bumped to `2026.6.1.post6`; the service-worker
  cache namespace is bumped to `gitpulse-v121`, generated bundles/minified
  siblings are rebuilt, and dashboard Latest changes is refreshed.

## [2026.6.1.post5] - 2026-06-01

### Changed

- **The declarative action layer no longer supports inline expression
  execution.** The legacy `data-action-expr` / `data-*-expr` path and its
  `new Function(...)` runner were removed from the shared frontend core and
  component macros. Project empty-state buttons now use the structured
  `data-action="clickElementById"` contract instead of embedding JavaScript
  snippets.
- Application/docs metadata is bumped to `2026.6.1.post5`; the service-worker
  cache namespace is bumped to `gitpulse-v120`, generated bundles/minified
  siblings are rebuilt, and dashboard Latest changes is refreshed.

## [2026.6.1.post4] - 2026-06-01

### Fixed

- **Process-action locks now refresh as soon as a global job updates.** The
  shared guard listens to `gp:job-update` as well as completion/storage events,
  so sync/import/run-checks buttons are disabled immediately when the global job
  bar starts or refreshes a job instead of waiting for the 1.5 s polling tick.
- Application/docs metadata is bumped to `2026.6.1.post4`; the service-worker
  cache namespace is bumped to `gitpulse-v119`, generated bundles/minified
  siblings are rebuilt, and dashboard Latest changes is refreshed.

## [2026.6.1.post3] - 2026-06-01

### Changed

- **Legacy inline process-status macros were removed from the component
  layer.** Dashboard and course detail fragments now rely on the external
  `import-stream.js` module and the shared global-job/process-guard modules
  instead of importing an unused Jinja component that only emitted inline
  JavaScript helpers.
- **Process-action guard refresh now includes the root element passed to it.**
  Dynamically inserted buttons can be refreshed directly with
  `GP.refreshProcessActionGuards(button)`, not only through a parent container,
  so active sync/import/run-checks locks apply immediately to single inserted
  controls.
- Application/docs metadata is bumped to `2026.6.1.post3`; the service-worker
  cache namespace is bumped to `gitpulse-v118`, generated bundles/minified
  siblings are rebuilt, and dashboard Latest changes is refreshed.

## [2026.6.1.post2] - 2026-06-01

### Fixed

- **Cross-document View Transitions no longer log `AbortError: Transition was
  skipped`.** Course tabs and page links navigate cross-document, where the CSS
  `@view-transition { navigation: auto }` rule drives the crossfade. When a
  transition is skipped - a second tab/link is clicked before the first
  settles, the already-active tab is re-clicked (a same-URL navigation), or the
  tab is hidden mid-navigation - the browser rejects the transition promises
  with `AbortError`. They are now handled at the source via the `pageswap`
  (outgoing) and `pagereveal` (incoming) navigation events, so the skip is
  never an uncaught "(in promise)" rejection. The pre-existing global
  `unhandledrejection`/`error` sweep is retained as defense-in-depth.
- Application/docs metadata is bumped to `2026.6.1.post2`; the service-worker
  cache namespace is bumped to `gitpulse-v117`, and generated bundles/minified
  siblings are rebuilt.

## [2026.6.1.post1] - 2026-06-01

### Changed

- **Course tab keyboard navigation now lives in an external frontend module.**
  The shared course-navigation partial no longer embeds inline JavaScript; the
  arrow/Home/End tab behavior is handled by `course-tabs.js`, included in
  `core.bundle.js`, and covered by a regression test.
- **Legacy inline `onchange` support was removed from the shared native select
  component.** Current callers already use declarative data/action contracts or
  Alpine bindings, so the unused escape hatch is gone and guarded by tests.
- Application/docs metadata is bumped to `2026.6.1.post1`; the service-worker
  cache namespace is bumped to `gitpulse-v116`, generated bundles/minified
  siblings are rebuilt, and the dashboard Latest changes feed is refreshed.

## [2026.6.1] - 2026-06-01

### Fixed

- **Tooltips no longer pop open without hovering.** Tippy's default trigger is
  `mouseenter focus`, so when a modal's focus-trap (or a mouse click)
  programmatically focused a button carrying `data-tippy-content` - most
  visibly the modal close (X) - its tooltip appeared with no pointer hover.
  Tooltips now suppress focus-triggered shows unless the focus is from the
  keyboard (`:focus-visible`), preserving keyboard accessibility while removing
  the spurious popups.

### Changed

- Application/docs metadata is bumped to `2026.6.1`; the service-worker cache
  namespace is bumped to `gitpulse-v115` so clients pick up the rebuilt
  `core.bundle.js`, and the dashboard Latest changes feed is refreshed.

## [2026.5.31.post3] - 2026-05-31

### Fixed

- **Service Worker no longer caches authenticated dashboard HTML.** `/dashboard`
  navigations are bypassed by the worker, and shared cache helpers now refuse
  responses carrying `Cache-Control: no-store` or `private`, keeping the browser
  Cache API aligned with the dashboard's security headers.
- **Logout now performs the documented browser cleanup.** `GET /dashboard/logout`
  sends `Clear-Site-Data: "cache", "storage"` in addition to deleting the
  session cookie, so stale offline fragments and per-tab state are purged.
- **Docs logo override no longer emits invalid nested links.** The MkDocs
  Material logo partial now renders only logo content, letting Material's
  header/nav templates own the surrounding anchor.

### Changed

- Application/docs metadata is bumped to `2026.5.31.post3`; the service-worker
  cache namespace is bumped to `gitpulse-v114`, dashboard Latest changes and
  security docs are refreshed, and new unit tests guard the SW/logout/docs-logo
  contracts.

## [2026.5.31.post2] - 2026-05-31

### Changed

- **Centralised documentation SEO policy and sitemap ownership.** MkDocs now
  applies a single `hooks/seo_policy.py` policy that marks technical/internal
  documentation sections as `noindex, follow, nosnippet` while keeping public
  product, onboarding and legal pages indexable. The docs sitemap is filtered
  to exclude those noindex URLs, root `/sitemap.xml` now only lists the
  application-owned login page, and `robots.txt` advertises both the app and
  docs sitemaps without duplicating docs URLs.

## [2026.5.31.post1] - 2026-05-31

### Changed

- **Split the dashboard, course-analytics and admin-system page controllers
  into Single-Responsibility source parts.** Following the Admin Courses split,
  the three remaining ~1.1k-line page scripts are now authored as ordered
  `_parts/<page>/NN-*.js` fragments (core / CRUD / live-updates / SSE for the
  dashboard; charts / reports / week-explorer / flags for analytics; format /
  stats / jobs / maintenance for admin) and concatenated **verbatim** back into
  the served `pages/*.js` by `scripts/build_bundle.py`. The output bundles are
  byte-identical, so there is zero runtime change - only the source is now
  small and single-responsibility, matching every other split page controller.

## [2026.5.31] - 2026-05-31

### Changed

- **Admin Courses frontend split into single-responsibility source parts.**
  `pages/admin-courses.js` is now generated from
  `_parts/admin-courses/00-core.js`, `10-lifecycle.js`, and `20-events.js`,
  matching the established page-controller pattern in `scripts/build_bundle.py`.
- **Course lifecycle DOM updates now reuse shared UI contracts.** Archive,
  activate, and permanent-delete row mutations render the shared
  `status-indicator` markup, consistent icon-only buttons, refreshed tooltips,
  and scoped process guards after every dynamic button swap.
- **Release metadata and static delivery refreshed.** Application/docs metadata
  is bumped to `2026.5.31`, generated bundles and `.min` siblings were rebuilt,
  dashboard `Latest changes` was updated, and the service-worker cache namespace
  is bumped to `gitpulse-v113`.

## [2026.5.30.post22] - 2026-05-30

### Changed

- **Dashboard "Latest changes" widget + docs refreshed** to reflect the
  declarative-component standardisation shipped in post21, and pruned back to
  the newest five short entries per the widget rule.

## [2026.5.30.post21] - 2026-05-30

### Changed

- **Standardised the Course Roster, Support Tickets and Admin Courses tables on
  the declarative component engine.** These pages previously hand-wired their
  own `ClientPaginator` / `TableFilter` instances in page JS. They now opt in
  purely through markup:
 - `data-paginator="<tableId>"` (+ `data-controls`, `data-page-size`,
    `data-storage-key`) on the table wrapper.
 - `data-filter="<tableId>"` (+ `data-filter-count`) on the search input.
 - a new `data-filter-dropdowns="name:#sel@data-attr,..."` attribute teaches
    `_autoInitComponents` to wire dropdown filters (status / priority /
    category) with no bespoke JavaScript.
- This removes ~per-page pagination/filter boilerplate, eliminates duplicated
  init code, and makes the tables auto-reinitialise on HTMX swaps through the
  shared `htmx:afterSwap` hook. Complex tables that need server-side fetch,
  tree-child row syncing or dynamic row loading (admin system jobs, DLQ,
  course/team/project/student detail) intentionally keep their custom
  instances. Bundles rebuilt + minified; service worker cache bumped to
  `gitpulse-v112`.

## [2026.5.30.post20] - 2026-05-30

### Fixed

- **Resolved "Loading pagination..." infinite loading bug on Admin Users page table.**
 - When the real user table replaced the skeleton/loading container via HTMX lazy-loading, the table initiation flag was preventing proper re-evaluation, leaving the `#paginationControls` component unresponsive and frozen in its loading state.
 - Refactored [src/app/templates/static/js/pages/admin-users.js](src/app/templates/static/js/pages/admin-users.js) to discard the stale initialization flag. Introduced robust DOM-presence verification routines that intelligently detect and cleanly recreate paginators and table filters upon dynamic HTMX swaps.
 - Restricted the initializer's target queries to target `.users-table` specifically, guaranteeing flawless component updates on user operations (such as role and active status modifications or toggling service accounts) without visual or functional leakage onto unrelated tables across different routed sections.
 - Re-bumped static asset versioning in `sw.js` to `gitpulse-v111` for clean client delivery.

## [2026.5.30.post19] - 2026-05-30

### Fixed

- **Fixed "Loading pagination..." infinite loading bug on tables during dynamic HTMX actions.** SPA navigation and dynamic updates using HTMX partial swaps previously severed and detached pagination controls from the `ClientPaginator` instances stored in the global registry `window._paginators`. This caused the table to get stuck displaying the "Loading pagination..." state.
 - Enhanced the automated components initializer `_autoInitComponents` to actively garbage collect stale paginator records from the registry when their corresponding table/control selectors are no longer present in the active DOM.
 - Refactored student record table pagination and course landing metrics tree-grid table to wrap manual initialization details in robust functions. Registered these functions to execute on dynamic HTMX swaps (`htmx:afterSwap` event listener) to ensure perfect, smooth pagination and table filtering live updates.
 - Bumped the service worker cache version to `gitpulse-v110` so that clients pick up the rebuilt static bundles cleanly.

## [2026.5.30.post18] - 2026-05-30

### Changed

- **Sync worker internals tidied:** the per-pipeline, per-MR-commit and
  per-commit-detail fetch helpers were hoisted out of the project loop into
  module-level functions. They were previously redefined on every project
  iteration; hoisting removes that churn and clears three long-standing
  static-analysis warnings (Pylance "refers to itself" false positives on the
  loop-local async closures). No behavioural change.

## [2026.5.30.post17] - 2026-05-30

### Changed

- **Team sync re-runs are dramatically faster: unchanged merge requests no
  longer re-fetch their diffs and approvals.** After the post16 pipeline and
  MR-notes dedup, fresh profiling showed the cost had shifted entirely to the
  `merge_requests` stage (50-84 s for only 8-10 MRs, ~8 s/MR). Each MR was
  triggering two expensive GitLab API calls every sync - `get_mr_changes`
  (the full per-file diff, often megabytes on the CI-heavy fork repos) and
  `get_mr_approvals` - even when the MR had not changed. The diff and
  approvals of an MR whose `updated_at` is unchanged are immutable, so the
  worker now skips that enrichment for unchanged MRs (the cheap local
  compliance checks still run). On a typical re-sync this collapses the MR
  stage from tens of seconds to near-zero per project.
- **Issue notes are likewise skipped for unchanged issues.** The same
  `updated_at` snapshot now gates the concurrent issue-notes fetch, so a
  re-sync only pulls notes for issues that are new or actually changed.

## [2026.5.30.post16] - 2026-05-30

### Changed

- **Team sync re-runs are much faster: finished pipelines are no longer
  re-fetched.** Profiling (per-stage timings added in post15) showed the
  `pipelines` stage was the single biggest cost per project (7-15 s each),
  and these assignment groups carry 9-15 CI-heavy project repos per team, so
  a full sync legitimately took several minutes - the progress bar genuinely
  sat at a low percentage because it was still working through the first of
  many projects, not because it was stuck. The worker now skips the expensive
  per-pipeline detail + jobs re-fetch for pipelines already stored in a
  terminal status (success / failed / canceled / skipped), which are
  immutable. New and still-running pipelines (and retried ones) are always
  fetched so their final status and jobs still land. First sync is unchanged;
  subsequent syncs - the common case when a teacher refreshes a course -
  avoid the bulk of the pipeline API round-trips.
- **Team sync also skips re-fetching notes for unchanged merge requests.**
  GitLab bumps an MR's `updated_at` whenever a note is added, so the worker
  now snapshots each MR's stored `updated_at` before processing and only
  re-fetches the (concurrent) MR notes for MRs that are new or whose
  `updated_at` advanced since the last sync. On a re-sync where most MRs are
  untouched this removes the bulk of the per-MR notes round-trips, the second
  cost centre after pipelines.

### Fixed

- **CI unit-tests:** updated the toast-restore assertion to match the post15
  minimum-visible-window behaviour (the old test pinned the removed
  `remaining <= 0` discard line).

## [2026.5.30.post15] - 2026-05-30

### Fixed

- **Sync success toasts no longer vanish when you navigate to another page.**
  Toasts are persisted across navigation in a `sessionStorage` queue and
  re-shown on the next page. A short (4 s) toast such as "Group synced" or
  "Sync completed!" created shortly before clicking a link had its remaining
  lifetime driven negative by the destination page's load time, so the
  confirmation was silently discarded - the intermittent "the toast
  disappears on navigation" bug. A toast still on screen when you leave was
  cut short, so it is now guaranteed a minimum visible window (2.5 s) on the
  destination page; only genuinely stale entries (left behind by a
  long-abandoned tab) are dropped. Bumped the service-worker cache to
  `gitpulse-v108`.

### Added

- **Per-stage timing for team sync.** A team whose repository carries a large
  inherited history (e.g. a fork of the course template) can legitimately
  take minutes to sync because each issue, MR, note and commit is fetched
  individually from the GitLab API, while a lighter team finishes in seconds.
  The worker previously logged only a single per-project total, so a
  multi-minute sync could not be attributed to the slow stage. Each project
  now logs a per-stage breakdown (`issues`, `merge_requests`, `mr_notes`,
  `pipelines`, `commits`) so the bottleneck behind a stuck/slow sync can be
  pinpointed from the logs.

## [2026.5.30.post14] - 2026-05-30

### Fixed

- **Issues to Address no longer shows students on a repository with no
  student work.** The project page renders the Issues to Address card blank
  when the team has not pushed any commits of their own, but the periodic
  live-data refresh was repopulating it. Three causes, all fixed:
 - A freshly forked assignment inherits the upstream template's commit
    history, so the raw GitLab `commit_count` is non-zero (e.g. 33 commits)
    even though no student has committed anything. Empty-repo detection now
    uses the *student-only* commit count - commits whose author matches a
    member of the project's student cohort - so an untouched fork correctly
    counts as empty.
 - The full-page banner and the live-data refresh derived "repo empty" from
    different signals, so the two paths could disagree (banner blank, poll
    repopulated). Both now use the same student commit count.
 - When the live-data poll could not determine the commit counts from
    GitLab it fell back to "empty only if there are zero snapshots" - but
    stale snapshots from a previous repo state made it report "not empty" and
    re-render the card full of students. The poll now treats an
    undeterminable state as *unknown* and leaves the correctly-rendered card
    in place instead of clobbering it. The Run Checks button is likewise left
    untouched when the state is unknown. Bumped the service-worker cache to
    `gitpulse-v107`.

## [2026.5.30.post13] - 2026-05-30

### Fixed

- **Loading skeletons no longer look clickable.** The Week Analytics (and
  other) loading placeholders reuse interactive sizing classes such as
  week tabs, which made the skeleton pills highlight and show a pointer
  cursor on hover while data was still loading. `.gl-skeleton` is now
  `pointer-events: none; cursor: default` so placeholders stay inert.
- **Tooltips now work on disabled buttons.** Disabled form controls do not
  emit pointer events, so the "why is this disabled" Tippy tooltip never
  fired (e.g. process-lock guards and the course-settings save buttons while
  a sync is running). Disabled controls are now wrapped in an inline
  `.gl-tip-wrap` span that hosts the tooltip, so the reason shows on hover;
  the wrapper is removed and the control's own tooltip re-bound when it is
  re-enabled.

### Changed

- **Replaced raw native `title=` tooltips with the Tippy component
  app-wide.** Open-in-GitLab links (merge requests, issues, commits),
  project-path hints, the run-checks passing ratio, support ticket dates,
  the member-filter reset button, the course-analytics exam-period week pills
  and the scoring include/exclude toggles now use `data-tippy-content` for a
  consistent, translatable, styled tooltip instead of the browser default.
  Added `Close` tooltips to the icon-only modal close (×) buttons that
  previously only carried an `aria-label`. Bumped the service-worker cache to
  `gitpulse-v106` so clients pick up the rebuilt bundles.

## [2026.5.30.post12] - 2026-05-30

### Fixed

- **Compliance Progress now shows the exam period (skúškové obdobie), not
  just the 13 teaching weeks.** The student Compliance Progress chart, weekly
  breakdown table and check heatmap requested only the teaching-week window,
  which slid a fixed 13-wide window forward and dropped the earliest weeks as
  exam-period snapshots arrived - so the panel never visibly extended past
  week 13. It now requests the full history window (the backend already caps
  to the current academic week and trims empty padding), so exam-period weeks
  appear alongside the teaching weeks. The course-level compliance trends
  (admin analytics + live SSE snapshot) had the same clipping and now cover
  the full semester including the exam period. Bumped the service-worker
  cache to `gitpulse-v105` so clients pick up the rebuilt bundle.

## [2026.5.30.post11] - 2026-05-30

### Changed

- **Polished the scoring include/exclude (eye) control across the member
  tables.** The eye / eye-off icon now animates with a springy pop when a
  student is toggled, the button stays visible and tinted while a row is
  excluded so the reversible state reads clearly, and hover/press add subtle
  scale feedback. The control now uses a consistent Tippy tooltip (no more
  duplicate native browser tooltip), and the excluded-row dimming transitions
  smoothly instead of snapping. Toggling a student still recalculates the
  group average, traffic light, contributor counts and retired grading scores live -
  no page reload. All motion respects `prefers-reduced-motion`.

## [2026.5.30.post10] - 2026-05-30

### Fixed

- **Fixed the progress-bar elapsed timer resetting on every page
  navigation.** When a course-sync bar was recreated after navigating to
  another page, the new bar was stamped with the current clock time instead
  of the server-authoritative sync start time, so the seconds counter
  restarted from zero each navigation. The bar now anchors its elapsed timer
  to the server `started_at_ms` and keeps the earliest known start, so the
  timer stays monotonic across navigations.

## [2026.5.30.post9] - 2026-05-30

### Fixed

- **Fixed transient restarted start-times in progress bar ticking.** Passive
  reconcilers (e.g. course card scans, background polling updates) could
  restage the global progress bar as a new run, reset execution progress to
  null, and bump start time to the current clock time. The SSE progress
  indicators now correctly protect and retain monotonic start times, preventing
  seconds-counters in the progress panel from resetting to zero.

### Changed

- **Refactored caching layers to enforce strict Single Responsibility Principle.** Verified zero cross-tenant leak vectors on templated CSP nonces and CSRF tokens across page-fragment page caching endpoints.
- **Service Worker cache partition upgraded to v100.** Static cache keys bumped to invalidate previous offline fragment cache baselines cleanly.

## [2026.5.30.post8] - 2026-05-30

### Changed

- **The global progress bar now appears instantly with a "Connecting..."
  stage.** Starting a course sync (Sync All), a project sync, or a sync from
  the course settings page used to surface the global progress bar only
  *after* the backend POST returned. With the GitLab reachability pre-flight
  (which retries and can take several seconds), the user saw no progress bar
  during that window and could re-click the button. The bar now shows an
  indeterminate "Connecting to GitLab..." spinner the moment the button is
  clicked, which also makes the existing re-click guard fire immediately so
  double submits are blocked while the request is in flight. Once the sync is
  enqueued the bar promotes to the real "Syncing: X/Y groups..." message; if the
  request fails the error is shown directly **in the bar** (not just a
  transient toast) and auto-dismisses. A safety timeout guarantees the
  connecting spinner can never hang if the request unexpectedly throws.

## [2026.5.30.post7] - 2026-05-30

### Fixed

- **Sync no longer fails when GitLab answers slowly once.** The `/sync-all`
  and per-group/per-project sync entrypoints run a GitLab reachability
  pre-flight check before enqueuing jobs. That check used a single 4 s
  request with no retry, so one transient slow response (a GitLab GC pause,
  or the API event loop being momentarily starved by concurrent SSE streams)
  returned `503 "GitLab server is currently unreachable"` and the sync simply
  did nothing. The pre-flight now retries once (5 s per attempt, 0.4 s
  backoff) and only treats two consecutive failures as unreachable, and logs
  `gitlab_preflight_unreachable` with the underlying error when it gives up.

## [2026.5.30.post6] - 2026-05-30

### Fixed

- **Week Analytics now opens on the latest week that has data.** Once teaching
  winds down, students stop committing, so the *current* semester week is often
  empty while the weekly scoring job keeps carrying compliance scores forward.
  The explorer previously auto-selected the current (empty) week and surfaced an
  unhelpful "No GitLab events tracked this week" panel, which read like data
  loss. It now auto-selects the most recent week that actually has activity or a
  compliance trend (falling back to the current week). A prod DB probe confirmed
  there was no data loss - simply no commits after teaching week 12.
- **Exam-period weeks are now reachable and styled in Week Analytics.** The
  week-selector loop only ran `1..semester_weeks`, so weeks in the exam period
  (skúškové obdobie) had no pill at all and were unreachable, and never carried
  the amber EXAM PERIOD treatment shown on the stat card. The selector now
  extends through the exam period, renders amber "Exam" pills, and the detail
  header shows an "Exam Period · Week N" chip.
- **Course search now shows an empty state.** Filtering the dashboard "Your
  courses" grid to a query with no matches (e.g. `hel`) hid every card but left
  a blank area. A proper `empty_state` component now appears, consistent with
  the rest of the app.

### Changed

- **Migrated six telemetry models to SQLAlchemy 2.0 typing.**
  `FlaggedTeamResolution`, `StudentComplianceSnapshot`, `ClicksAvoidedMetric`,
  `TeacherActivityMetric`, `TelemetryAggregate` and `EvaluationReport` were
  rewritten from legacy `Column(...)` assignments to `Mapped[] / mapped_column`,
  matching the earlier `SupportTicket` migration. Pylance now infers attribute
  types correctly (e.g. `flagged_at: datetime`, `week_number: int`) instead of
  `Column[X]`, eliminating the false-positive type errors in
  `pilot_telemetry.py` and the redundant `cast(...)` wrappers they required. A
  missing `None` guard before a `datetime` subtraction was also added. No
  behaviour or database-schema change.

## [2026.5.30.post5] - 2026-05-30

### Fixed

- **Restored a green container security scan (Trivy).** The transitive
  `protobuf` dependency was held at `4.25.9` by a `protobuf<5.0` ceiling that
  also pinned `opentelemetry-proto` to the older `1.27` line. That `protobuf`
  build carried a fixable HIGH/CRITICAL vulnerability, **CVE-2026-0994**, so the
  `container-scan-api` and `container-scan-worker` jobs failed. The ceiling was
  raised to `protobuf>=5.29.6,<6.0`, moving `protobuf` to the fixed `5.29.6` and
  letting OpenTelemetry resolve up to `1.42.1` (stable `1.x` API - no app code
  change). `requirements.lock` was regenerated on Linux to match CI.

## [2026.5.30.post4] - 2026-05-30

### Fixed

- **Restored a green CI pipeline.** Commit `f0cb9816` committed a
  `requirements.lock` generated on Windows, which contained `colorama`
  (Windows-only) and lacked `uvloop` (Linux-only). CI runs on Linux
  (`python:3.12-slim`), so `lockfile-check` regenerated the lock, produced the
  opposite platform set, and failed. The lock is now generated on Linux so it
  matches CI byte-for-byte. `mypy` also reported a redundant `cast(int, ...)`
  (in `pilot_telemetry.py`) and an unused `# type: ignore[assignment]` (in
  `telemetry_support.py`) that became dead after the post3 `SupportTicket`
  typing migration - both removed - and `home_changelog.py` was reformatted
  with `ruff format`.
- **Stopped the course analytics page from timing out on first load.** The
  heavy analytics fragment is htmx-lazy-loaded and takes ~60-95 s to compute on
  a populous course, exceeding the global 90 s htmx timeout. The page-cache key
  includes `GIT_SHA`, so every deploy starts cold and the first load aborted
  with `htmx:timeout` ("nothing loaded"). The fragment now overrides its htmx
  timeout to 180 s (`hx-request`), and its page-cache TTL was raised from the
  default 60 s to 600 s so it stays warm once computed instead of expiring
  before the ~94 s compute could ever serve a hit.

### Release

- Version `2026.5.30.post4`. Backend/CI + one template attribute; no JS or CSS
  changes, so bundles and the service-worker cache are unchanged.

## [2026.5.30.post3] - 2026-05-30

### Fixed

- **Migrated the `SupportTicket` model to SQLAlchemy 2.0 typing.**
  `src/app/models/support_ticket.py` used legacy `Column(...)` assignments
  without `Mapped[]` annotations, so Pylance inferred every attribute as
  `Column[X]` and reported 11 false-positive errors in the dashboard support
  route (`src/app/api/dashboard/auth.py`). The model now uses
  `Mapped[...] / mapped_column(...)` like its sibling models. Pure typing
  change - ORM behaviour is identical; `mypy` and the targeted unit tests pass.
- **Made the `lockfile-check` CI job deterministic (again).** The
  `[tool.uv] exclude-newer` pin pointed at a *future* instant, so each CI
  re-resolve picked up packages published "today" and `requirements.lock`
  drifted red. It is now pinned to a past instant, and a new `.gitattributes`
  forces `requirements.lock` to `eol=lf` so Windows CRLF commits cannot break
  the lint gate.

### Release

- Version `2026.5.30.post3`. Backend typing + CI/build only; no template, JS,
  CSS, or logic changes, so bundles and the service-worker cache are unchanged.

## [2026.5.30.post2] - 2026-05-30

### Changed

- **Split the single largest source file by single-responsibility.**
  `src/app/api/dashboard/home_changelog.py` (1511 lines) held ~1490 lines of
  hand-maintained "Latest changes" data inline. The data now lives in
  `home_changelog_entries.json` and the Python module is a thin localisation
  loader (`_CHANGELOG_ENTRIES` is loaded from JSON, `_get_changelog_entries`
  unchanged). Data is separated from logic; the dashboard widget and
  `tests/unit/test_changelog_entries.py` read the same entries with no
  behaviour change.

### Release

- Version `2026.5.30.post2`. Backend source-structure only; no template, JS,
  CSS, or logic changes, so bundles and the service-worker cache are unchanged.

## [2026.5.30.post1] - 2026-05-30

### Changed

- **Continued the single-responsibility (SRP) source split to the next tier of
  large page controllers.** `pages/course-detail.js` (1414 lines) and
  `pages/team-detail.js` (1216 lines) - both below the 1500-line threshold the
  `2026.5.30` pass targeted - are now split into ordered, build-only `_parts/`
  fragments concatenated verbatim by `scripts/build_bundle.py`:
 - `course-detail/` -> `00-sync-stream`, `10-teams-crud`, `20-sync-all`,
    `30-course-data`.
 - `team-detail/` -> `00-core`, `10-sync`, `20-analysis-boot`, `30-live`.
  The served files are regenerated **byte-for-byte identically** (verified via
  SHA-256 before/after and `build_bundle.py --check`), so there is zero runtime
  or behaviour change - only smaller, single-responsibility source modules.

### Release

- Version `2026.5.30.post1`. Source-structure only; bundles and per-file `.min`
  siblings rebuilt and verified. No backend, template, or logic changes.

## [2026.5.30] - 2026-05-30

### Changed

- **Split every 1500+ line source file by the single-responsibility principle
  (SRP) into smaller modules with no behaviour change.** The front-end giants
  (`core.js`, `global-job-bar.js`, `tour-engine.js`, `pages/project-detail.js`,
  `pages/course-settings.js` and `responsive.css`) were broken into build-only
  parts under `_parts/` folders that `scripts/build_bundle.py` concatenates back
  into an identical artifact (verified byte-for-byte on the minified bundle).
  Back-end API modules (courses, sync, telemetry, teams, projects, report/sync
  jobs) had their helpers extracted into neighbouring modules.

### Release

- Version `2026.5.30`. Source-structure only; bundles rebuilt. No UI or logic
  change.

## [2026.5.29.post1] - 2026-05-29

### Changed

- **Loading skeletons now reuse the real page components instead of a parallel
  `gl-skeleton-*` layout.** The skeleton primitives in
  `components/loaders.html` defined their own card / stat / table / form
  containers (`.gl-skeleton-card`, `.gl-skeleton-stat`, `.gl-skeleton-table` +
  `.gl-skeleton-thead`/`.gl-skeleton-row`, `.gl-skeleton-stats-grid`,
  `.gl-skeleton-field`) each with a separate set of responsive media queries.
  Those parallel structures drifted from the live UI, so the placeholders did
  not match the real layout once content loaded. The `sk_stat`, `sk_stats`,
  `sk_card`, `sk_table` and `sk_form` macros now emit the **real** component
  markup - `.stat-card` / `.stats-grid` / `.card` / `table.data-table` /
  `.form-group` - with `.gl-skeleton` shimmer bars in the leaf slots. Layout,
  spacing and responsiveness are therefore inherited directly from the live
  components and can no longer diverge. Macro signatures are unchanged, so no
  call sites required edits.
- **Removed the now-dead skeleton CSS.** Deleted `.gl-skeleton-card`,
  `.gl-skeleton-stat` (+ children), `.gl-skeleton-table` /
  `.gl-skeleton-thead` / `.gl-skeleton-row` (+ all `nth-child` width-variance
  rules and the 768px/480px media queries), `.gl-skeleton-stats-grid`
  (+ media queries) and `.gl-skeleton-field` / `-label` / `-input`
  (+ form responsive media query) from `loaders.css`. The `.gl-skeleton`
  primitive, `.gl-skeleton-tr` (used by `sk_tbody_rows`),
  `.gl-skeleton-cards-grid` and the `.gl-skeleton-list*` family are retained.

### Release

- Version `2026.5.29.post1`. Template + CSS change only; bundles rebuilt
  (`styles.bundle.css`, per-file `.min` siblings). No backend changes.

## [2026.5.29] - 2026-05-29

### Fixed

- **`lockfile-check` CI job is now deterministic and no longer fails on
  unrelated upstream releases.** The job runs
  `uv pip compile pyproject.toml --extra otel -o requirements.lock` then
  `git diff --exit-code requirements.lock`. Because almost every dependency
  uses an open `>=` range, `uv` re-resolved to whatever was newest on PyPI at
  job time, so the lockfile "drifted" - and the job went red - the moment any
  direct or transitive dependency published a new version, even though nothing
  in the repository had changed. Added a `[tool.uv]` section with
  `exclude-newer = "2026-05-30T00:00:00Z"` to pin resolution to a fixed point in
  time. `requirements.lock` regenerates byte-identically, and the gate stays
  reproducible until the timestamp is deliberately bumped to pull in newer deps.

### Release

- Version `2026.5.29`. No service-worker cache bump: this is a CI/build-config
  change only, with no client-facing asset changes.

## [2026.5.23.post2] - 2026-05-23

### Fixed

- **Course Analytics checklist chart now paints commit-category bars the correct
  pink (#ec4899).** After the R13 remap to `commit` in `post1`, the
  `categoryColors` map in `course-analytics.js` still keyed on the orphan
  `quality:` (the engine never emits that anymore). `R13` and any
  commit-category custom checks fell through to the `custom` purple
  fallback. Renamed the key to `commit:` (kept the same pink colour) so the
  chart's category stripe matches the badge colour used elsewhere in the UI.
- **Course Settings filter toolbar got the missing `Commit` button.** The
  filter bar above the checks table offered `Issue`, `MR`, `Review`, `CI/CD`
  but not `Commit`, so teachers could not narrow the table to `R13` or
  custom checks with `category="commit"`. Added the button via the existing
  `filter_btn` macro; the JS filter handler is data-driven and required no
  changes.

## [2026.5.23.post1] - 2026-05-23

### Fixed

- **`Commit` category is now a first-class citizen across the whole check stack.**
  The Edit Check modal dropdown previously offered only five options
  (`issue`, `mr`, `review`, `ci`, `custom`); any stored check with `category=commit`
  rendered with an empty Category field because the value was not in the option
  list and the JS badge/label maps had no entry for it. Added `('commit', t('Commit'))`
  to the dropdown options and `commit:` entries to `CATEGORY_BADGES` (badge-purple)
  and `CATEGORY_LABELS` in `course-settings.js`.
- **Pydantic schemas and backend validators accept `commit`.** Extended
  `ALLOWED_CATEGORIES` and the two `Literal[...]` unions in
  `schemas/custom_check.py` so the custom-check API no longer rejects
  `category="commit"` with HTTP 422. Aligned the inline
  `valid_categories` set and the LLM suggestion docstring in
  `api/dashboard/course_checks.py`, and the column comment in
  `models/custom_check.py`.
- **R13 (`Commit Quality`) is now mapped to the `commit` category.**
  Previously `_CHECK_CATEGORIES` in `compliance/engine.py` mapped `R13` to a
  one-off `"quality"` bucket that no other code recognised, so
  `commit_score` was always `None` in category breakdowns and pilot telemetry.
  Re-mapped to `"commit"`, added `"commit"` to the always-present `all_cats`
  set in `_compute_category_scores`, mirrored the change in
  `pilot_telemetry._FALLBACK_CHECK_CATEGORIES`, and added `"commit"` to the
  iteration tuple in `_derive_category_scores`.

### Release

- Version `2026.5.23.post1`, service-worker cache `gitpulse-v98`.

## [2026.5.23] - 2026-05-23

### Fixed

- **Scoped button and modal locks cover the remaining course/project writes.**
  Course archive/activate/delete, dashboard Add Group and course edit,
  course-settings scoring/config imports, admin course actions, and project
  unlink now all check the active `course`/`team`/`project` process scope before
  opening a modal or mutating data.
- **Process-lock click guard is now fail-closed.** Any element with
  `data-process-lock-when` is checked again at click time, not only by the
  1.5s disabled-state poll, so a stale button state cannot let a conflicting
  sync/import/run-check action through.
- **Dynamic buttons inherit process scope.** Buttons inserted after archive or
  activate operations are refreshed through the shared process guard, preserving
  correct locking without a page reload.

### Release

- Version `2026.5.23`, service-worker cache `gitpulse-v97`.

## [2026.5.22.post7] - 2026-05-22

### Fixed

- **SVG spinners no longer wobble on parent hover.** `.spinner` and
  `.spinner-inline` now set `transform-origin: 50% 50%` and
  `transform-box: fill-box`, so the rotation stays anchored to the visual
  centre even when the parent card composites a hover transform.
- **Sync-completion toast no longer lost during navigation.** When a sync
  finished between `beforeunload` and the actual unload, the toast was
  appended to a DOM that `_preserveFlashToast()` had already snapshotted
  as empty, leaving the user with no feedback. The `_restoreJobs`
  done/error/finishing branches now enqueue a replay completion toast on
  the next page load (session-scoped dedup blocks duplicates inside the
  same page-load), and the nav-replay window widened from 3s to 8s so
  slow navigations still surface the missed completion.

## [2026.5.22.post6] - 2026-05-22

### Fixed

- **Scoped process locks now follow the course/team/project hierarchy.**
  Per-team sync, per-project sync, and run-check jobs use stable scoped
  job keys, so active work in one group does not block unrelated courses
  or groups, while conflicting actions in the same team/project remain
  locked.
- **Course-level Run Checks stays locked until the real work finishes.**
  Added an aggregate run-check status endpoint and wired the global job
  bar to poll it, preventing modals/buttons from unlocking immediately
  after fan-out enqueue while per-team jobs are still running.
- **Exclude from scoring is guarded consistently.** Member toggle buttons
  evaluate the current row's scope, use shared icons, and the backend
  takes the team advisory lock before checking active scoring jobs.

### Release

- Version `2026.5.22.post6`, service-worker cache `gitpulse-v95`.

## [2026.5.22.post5] - 2026-05-22

### Fixed

- **Imperative guards now respect scope.** Click handlers for per-team
  sync, per-project sync, run checks, and course-level
  sync-all/import/run-checks all pass a `course`/`team`/`project` scope
  to `guardProcessAction`, so the "Wait for the active sync to finish"
  toast no longer fires for actions in unrelated courses.
- **Dashboard Import buttons.** Locked only by another active import,
  not by syncs in any course.
- **Course-detail skeleton.** Now renders four action button
  placeholders (Add Group / Import from GitLab / Sync All / Run Checks)
  to mirror the loaded layout 1-to-1.

## [2026.5.22.post4] - 2026-05-22

### Fixed

- **Per-course/team/project sync independence.** The process guard now
  scopes locks to a specific course, team, and project. Running a sync in
  one course leaves import and sync buttons in other courses fully
  responsive. Run-checks and sync still gate each other, but only within
  the same team or project; dashboard Import buttons are independent of
  per-course jobs. Every job-start call-site tags meta with `courseId`,
  `teamId`, `projectId`, and `jobKind` so guards can filter precisely.

### Release

- Version `2026.5.22.post4`, service-worker cache `gitpulse-v93`.

## [2026.5.22.post3] - 2026-05-22

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

- Bumped application/docs metadata to `2026.5.22.post3` and service worker
  cache to `gitpulse-v92`.

## [2026.5.21.post26] - 2026-05-21

### Changed

- **Dashboard release dates are normalized to the actual release day.**
  `Latest changes` no longer contains future-dated rows, and the changelog
  regression test now rejects entries dated after 2026-05-21.
- **Local deploy workspace hygiene is cleaner before redeploy.** Old ignored
  `deploy-post*.log`/`redeploy.log` files and the one-off ignored SRP split
  helper script were removed from the working tree before the release deploy.

### Release

- Bumped application/docs metadata to `2026.5.21.post26` and service worker
  cache to `gitpulse-v76`.

## [2026.5.21.post25] - 2026-05-21

### Changed

- **Sync cache invalidation now has a dedicated module.**
  `_invalidate_dashboard_cache_after_sync` moved from the large
  `workers/sync_job.py` worker into `workers/sync_cache.py`. Full-team and
  per-project sync still invalidate the affected project, team, course, and
  student dashboard page-cache scopes, but the sync worker keeps less cache
  plumbing inline.
- **Current release metadata is aligned again.** Root/docs changelogs and
  version references now point at `2026.5.21.post25` / `gitpulse-v75`, matching
  the package metadata and service worker cache namespace.

### Tests

- Retargeted the sync cache invalidation regression test to
  `app.workers.sync_cache`.

### Release

- Bumped application/docs metadata to `2026.5.21.post25` and service worker
  cache to `gitpulse-v75`.

## [2026.5.21.post3] - 2026-05-21

### Changed

- **Dashboard role-context helpers now have a dedicated module.** Sidebar badge
  counts, greeting subtitles, student dashboard context, and admin dashboard
  context moved from `dashboard/home.py` into `dashboard/home_context.py`.
  `home.py` is now closer to a page orchestration layer instead of owning every
  role-specific data helper.
- **Context fast paths are covered.** Student context returns the default
  zero-state without DB access when there are no active courses or no GitLab
  username, and student sidebar badges stay DB-free.

### Release

- Bumped application metadata to `2026.5.21.post3` and service worker cache to
  `gitpulse-v53`.

## [2026.5.21.post2] - 2026-05-21

### Changed

- **Dashboard `Latest changes` now has its own module.** The hand-maintained
  release entries and locale selection moved from the large
  `dashboard/home.py` router into `dashboard/home_changelog.py`, so the home
  route keeps page orchestration separate from release-note data.
- **Course-card health SQL now has its own module.** Per-course RED-team health
  moved into `dashboard/home_course_health.py`; the helper now returns an empty
  result immediately when there are no active courses instead of building a
  pointless SQL query.

### Fixed

- Added regression coverage for the empty active-course course-health path and
  retargeted dashboard changelog tests to the new `home_changelog.py` owner.

### Release

- Bumped application metadata to `2026.5.21.post2` and service worker cache to
  `gitpulse-v52`.

## [2026.5.21.post1] - 2026-05-21

### Changed

- **Dashboard home stat-card logic now has a dedicated module.** The role-based
  card SQL moved from the large `dashboard/home.py` router into
  `dashboard/home_stats.py`, with one shared latest-team-snapshot subquery for
  RED-team counts and average compliance. Student dashboards with no active
  courses now return zero-value cards without issuing unnecessary DB queries.
- **Standalone rate-limit HTML now cache-busts its assets.** The 429 browser
  response uses the deploy `BUILD_HASH` in `/static/...?...` links for favicon,
  stylesheet, and illustration assets so it follows the same static-cache
  invalidation model as template-rendered pages.
- **Supply-chain extras are narrower.** Added an explicit `idna>=3.15`
  security floor, removed the redundant `safety` optional scanner in favour of
  the CI-standard `pip-audit` + CycloneDX pair, and moved Locust into a separate
  `load` extra so normal dev/security installs do not pull load-test-only
  dependencies.

### Fixed

- Added regression coverage for the no-active-course student stat-card path and
  deploy-hash static links on the rate-limit page.

### Release

- Bumped application metadata to `2026.5.21.post1` and service worker cache to
  `gitpulse-v51`.

## [2026.5.19.post25] - 2026-05-19

### Fixed

- **Page-fragment cache keys are now delimiter-safe.** Variant parts are
  JSON-serialized before the BLAKE2b digest is computed, so values such as
  `("a|b", "c")` and `("a", "b|c")` cannot collapse to the same cache key.
  The Redis namespace is bumped to `gp:page:v2`, forcing a safe cold start for
  existing fragments.
- **Static cache headers are canonical.** `/static/*` responses now replace any
  existing `Cache-Control` header instead of appending duplicates, merge
  `Vary: Accept-Encoding` without losing existing `Vary` values, and only grant
  the one-year immutable profile when `?v=` is a valid hex content hash.
- **Dashboard home cleanup.** Removed unused stat-card parameters and stale
  local variables from `home.py`; support-ticket sidebar badge logic now states
  that it counts visible-course tickets.

### Changed

- Bumped application metadata to `2026.5.19.post25` and service worker cache to
  `gitpulse-v50`.

## [2026.5.18.post24] - 2026-05-18

### Fixed

- **Progress bar no longer flickers right after a sync completes.** Both
  the 30-second `/sync/active` watchdog and the `htmx:load` reconcile
  now skip work for 3 s after `completeGlobalJob` fires. Previously a
  stale `/sync/active` snapshot or a navigation could re-add the
  just-faded bar momentarily.
- **Stale `Last Synced` after a successful sync is now visible in
  logs.** `_invalidate_dashboard_cache_after_sync` failures are logged
  at WARNING (was DEBUG) in both the full-team-sync and per-project-sync
  paths, so a Redis/SCAN hiccup that would otherwise silently leave the
  page-cache populated with stale data surfaces in `docker logs` and
  Grafana.

### Performance

- **Webhook bursts coalesce metrics-refresh enqueues per team.** A
  burst of N events from the same team within 2 seconds now enqueues a
  single `metrics_refresh` job instead of N (Redis `SET ... NX EX 2`
  debounce). The job itself is idempotent, so coalescing does not lose
  any state. Removes the bulk of the Redis chatter previously caused by
  CI pipelines emitting 10+ events in quick succession.

## [2026.5.18.post23] - 2026-05-18

### Fixed

- **Diff column on the MR table no longer shows `- files`.** When
  `files_changed`, `lines_added` and `lines_removed` are all missing the
  cell now renders an em-dash (`-`) instead of a stray dash with the
  `files` label. When file count is missing but a +/- delta is present,
  only the delta is shown.
- **Empty-state icons on the project page are animated like the rest of
  the dashboard.** The "Issues to Address -> No scored members yet" and
  "All passing" icons share the same `emptyStateFloat` keyframes as
  every other `.empty-state-icon` (with a `prefers-reduced-motion: reduce`
  opt-out for accessibility).

### Changed

- **Dashboard `_CHANGELOG_ENTRIES` trimmed to the most recent 5 entries
  and shortened to one-paragraph summaries**, so the homepage widget
  stays short and readable. The long-form changelog lives here and in
  `docs-site/docs/changelog*.md`.
- Bumped application/docs metadata to `2026.5.18.post23` and service
  worker cache to `gitpulse-v48`.

## [2026.5.18.post22] - 2026-05-18

### Fixed

- **Sync completion now eagerly invalidates dashboard fragment caches.**
  Full team sync and single-project sync both drop the affected project,
  team, course/activity/analytics, and active student page-cache scopes
  after a successful job. This closes the short stale-HTML window that
  could remain after inline metric recomputation or fast project syncs.
- **CSP/inline cleanup pass.** Course Settings LLM helper logic and the
  401/429 error-page redirect/countdown timers now live in external JS;
  the related styles moved to CSS and regenerated `.min` assets.

### Changed

- Bumped application/docs metadata to `2026.5.18.post22` and service
  worker cache to `gitpulse-v47`.

## [2026.5.18.post21] - 2026-05-18

### Added

- **Dashboard activity feed now distinguishes project-scoped sync
  runs.** When a teacher clicks *Sync* on a specific project (not on
  the whole group / not the global *Sync all*), the resulting entry
  in the "Follow the latest updates" widget renders as
  *"System - Project synced from GitLab"* with the project name as
  the detail and the link pointing to `/dashboard/projects/{id}`
  instead of the team page. Group-scoped and global sync entries are
  unchanged. `run_checks` continues to surface at every level it can
  be triggered (group + course fan-out).

### Fixed

- **System-wide semester scoping audit.** Several aggregate /
  contributor queries were spanning *all of history* instead of the
  active semester window, which inflated counts and made stale
  project health linger across terms. Fixed:
 - `course_detail` + `get_course_sync_status` + the
    `/courses/{id}/sync-stream` SSE builder now thread
    `commit_since = semester_floor_utc(course.settings)` through
    `team_contributor_counts()` and
    `total_distinct_contributors()`.
 - `api/projects.py:get_contributors` DB fallback now filters
    commits by the project's course semester floor.
 - `dashboard/teams.py` student -> primary-project mapping now
    respects the same `_commit_window_clause` as the rest of the
    team-detail page (a student who switched groups between
    semesters no longer keeps mapping to the prior-semester
    project).
 - `dashboard/courses.py` per-team pipeline aggregates (total /
    passed / failed / latest_status) and the alternate
    course-pipeline path now both clamp by `semester_floor_utc`
    so a successful run from last term no longer masks current
    health.

### Removed

- Reverted an experimental project-level activity card on the
  project-detail page - the dashboard "Follow the latest updates"
  widget is the single source of truth; the project page does not
  duplicate it.

## [2026.5.18.post17] - 2026-05-18

### Added

- **New endpoint `POST /api/v1/projects/{project_id}/sync`.** The
  Sync button on the project-detail page no longer triggers a
  whole-team sync - it refreshes only the issues, MRs, MR notes,
  pipelines, and commits (default branch + per-MR source branches)
  for that single project. Member sync and project discovery
  remain team-scoped (they only make sense at the group level).
  The endpoint takes an advisory lock on `project_id`, deduplicates
  against an in-flight team-wide sync for the same team, and
  writes an `sync_project` audit entry.
- **Per-project SYNCING/QUEUED/FAILED badges in the team-detail
  Projects table.** `GET /api/v1/courses/{course_id}/sync-status`
  and the `/courses/{id}/sync-stream` SSE now return
  `sync_status_by_project` (plus `project_sync_running_count` /
  `project_sync_queued_count`). The team-detail JS uses this map
  to paint only the rows of projects whose sync actually runs -
  instead of lighting up every project row whenever the team has
  any sync job.

### Fixed

- **Phantom `1/2 groups` counter during a single in-flight sync.**
  The `total_groups` denominator in both `/sync-status` and the
  SSE snapshot now only counts team-wide jobs (project-scoped jobs
  get their own counter) and uses a 3-minute burst window on
  completed/failed; the previous 2-hour cutoff dragged stale
  completions from earlier in the day into the denominator.

### Schema

- Migration `047_bg_job_project_id` adds nullable
  `BackgroundJob.project_id` (FK to `gitlab_projects.id`
  `ON DELETE SET NULL`) + `ix_background_jobs_project_id`.

### Technical

- Service Worker cache: `gitpulse-v46`.
- New worker entry point: `app.workers.sync_job.sync_single_project`.
- New event-service helper: `enqueue_project_sync_job(project_id, job_id, course_id)`.

## [2026.5.18.post16] - 2026-05-18

### Fixed

- **Project-detail `Sync` button no longer lies about progress.**
  The post15 handler unconditionally showed `Sync started!` and
  released its global-job-bar slot via `deferGlobalJob` without
  inspecting the API response, so:
 - When the backend returned `status="running"` or
    `status="enqueued"` for an existing job (e.g. when the parent
    course was already mid-sync), the toast still said
    `Sync started!` - visibly false.
 - When `enqueue_sync_job` failed (Redis unavailable) and the
    server set `status="failed"`, the same false success toast
    fired.
 - The deferred global-job-bar slot was never finalised with
    `completeGlobalJob`, leaving a phantom item that combined with
    the real running sync to display counts like `1/2 groups`.

  The click handler now branches on every documented status:
 - `skipped_fresh` -> info toast `Already up-to-date`, bar
    completed with `done`.
 - `failed` (or missing `job_id`) -> danger toast surfaced from
    `result.message`, bar completed with `error`.
 - `running` / `enqueued` returned for an EXISTING job (detected
    via the server's `Sync already <status> for group ...`
    message) -> info toast `Sync already in progress`, attaches
    SSE to the existing `job_id`.
 - `enqueued` for a FRESH job -> success toast `Sync started!`,
    attaches SSE.

  Whenever the SSE stream attaches the button stays in the loading
  state for the full lifetime of the job (replicating the
  course-detail / team-detail pattern). `onComplete` /
  `onError` finalises the global job bar with the correct kind
  (`done` / `error`), unlocks the button exactly once, and on
  success reloads the page so freshly synced members, pipelines,
  MRs and commits appear without manual refresh.

  Backend `POST /api/v1/teams/{team_id}/sync` already provided
  TOCTOU-safe idempotency via `pg_advisory_xact_lock` plus a
  `BackgroundJob.status IN ('enqueued','running')` lookup, so this
  is a pure client correctness fix - no DB or API contract
  changes were needed. Service worker cache -> `gitpulse-v45`.

### Added

- **Per-row `SYNCING` / `QUEUED` / `FAILED` badges in the
  `Subgroups and Projects` table on team detail.** Projects don't
  sync individually - they inherit their parent group's sync
  state. When the group is syncing (locally triggered, or via a
  course-level `Sync All`), every active project row now swaps its
  `Active` / `Template` badge for the live sync state badge so the
  table reflects the work in progress at the group level. Original
  badges are restored after the SSE stream completes; FAILED is
  shown briefly before reverting. Inactive rows are left untouched.
  Cross-page coverage: on page load we poll
  `/api/v1/courses/{course_id}/sync-status` once for THIS team's
  `sync_status`; if a sync is already running (e.g. the user
  navigated here mid Sync All), the badges are painted immediately
  and a lightweight 4 s poller continues until the team's sync
  settles. This mirrors the per-row team status pattern already in
  place on the course detail page.

## [2026.5.18.post15] - 2026-05-18

### Added

- **`Sync` button on project detail page.** Previously the only way
  to refresh a single project's data from GitLab (members, projects,
  pipelines, MRs, issues, commits) was from the parent course/group
  view. The project detail toolbar at
  `/dashboard/projects/<uuid>` now has its own `Sync` button next to
  `Unlink`, gated by `can_edit and team`, which posts to
  `/api/v1/teams/{team_id}/sync` and surfaces progress through the
  global job bar exactly like the group-level sync.

### Removed

- **`Rotate Webhook Secret` button + `POST /api/v1/projects/{project_id}/rotate-secret`
  endpoint.** The per-project webhook secret rotation UI duplicated the
  multi-scope `Settings -> Webhook Configurations` flow (introduced in
  migration 041) without offering anything unique. Two ways to do the
  same thing on the same page is exactly the duplication the user
  flagged. The button, JS handler, FastAPI endpoint
  (`projects.rotate_project_secret`), Pydantic
  `ProjectSecretRotated` schema, tour step, contract test row, and
  security-doc section are all gone. Per-project
  `Project.webhook_secret_hash` is still generated on import and
  verified by webhook delivery - only the manual rotation surface
  is retired.

### Fixed

- **`Unlink` tooltip shortened.** The 4-sentence essay on
  reactivation rules in the project toolbar tooltip was clipping on
  smaller viewports; collapsed to one line: `Soft-deactivate this
  project. History is preserved; an admin must explicitly reactivate
  it.`

## [2026.5.18.post14] - 2026-05-18

### Fixed

- **Removed duplicate `Sync Group Data` modal.** The full-screen sync
  modal opened on every `Sync` / `Sync All` click already had a
  persistent global job bar showing the exact same
  `Project N/15: ... synced (X%)` progress at the top of the page. Two
  copies of the same progress line on screen at once was redundant and
  noisy. Now only the global bar shows progress; the modal markup is
  retired (`team/_modals.html`) and `_DEFAULT_LOCAL_SELECTORS.sync` in
  `global-job-bar.js` is gone too.
- **Sync button no longer overflows on mobile.** `triggerSync` /
  `triggerSyncAll` previously called `setButtonLoading(btn, true,
  'Syncing...')` which replaced the icon button's HTML with the
  literal `Syncing...` string. On narrow viewports that text bled
  outside the small icon-sized button as `/ncing`. Dropped the
  `loadingText` argument - the button now keeps its original icon /
  label and gets a `.loading` class for the spinner state, matching
  every other action button on the page.

## [2026.5.18.post13] - 2026-05-18

### Changed

- **Student profile polish.** Three small fixes for the post12 Student
  Run Checks rollout flagged from prod review:
 - The yellow `Run Checks` button no longer floats above the page as
    an orphan strip; it now lives inside the `Student Profile` /
    `My Profile` / `Teacher Profile` card header, next to the title,
    so it sits on a surface instead of the raw page background.
 - Project contributors widget now resolves matched git authors to
    the canonical `Student.full_name` (looked up by email, then by
    lowercased `gitlab_username`).  Prevents shared / placeholder
    author names like `student` from leaking into the UI when a
    student's local git config is sloppy.  The original git display
    name is preserved on the response payload as `raw_name` for
    auditing.
 - Skeleton loader bars (`.gl-skeleton`) now read from the dedicated
    `--gl-skeleton-bg` / `--gl-skeleton-shimmer` tokens defined in
    `tokens.css`, and the shimmer overlay opacity goes from 0.05 to
    0.12.  Loader rows on the project / student detail pages are
    visibly contrasted against the page background instead of nearly
    invisible.

## [2026.5.18.post12] - 2026-05-18

### Added

- **Run Checks now exists at all three scopes.** GitPulse has a course
  (whole-cohort) -> group -> student hierarchy.  The team / group view
  had a Run Checks button since post0; this release adds it at the
  remaining two levels.
 - **Course-level.** Course detail action bar gets a yellow
    `Run Checks (all groups)` button next to `Sync All`.  It calls a
    new `POST /api/v1/courses/{course_id}/run-checks` endpoint that
    fans out one `run_checks` BackgroundJob per active group (same
    10-minute dedup window as the team-level endpoint).  Visible to
    anyone with `can_edit` on the course (course owner / teacher /
    admin - the only roles `User.role` may take).
 - **Student-level.** Student profile gets the same yellow button.
    The compliance worker is still team-scoped (GitPulse stores one
    snapshot per student-on-team), so the button POSTs to
    `/teams/{team_id}/run-checks` and lets the existing SSE on the
    team stream refresh the student card when the job finishes.
 - `_run_checks_modal.html` learned a Course branch for its scope
    banner so the dynamic context flows through cleanly:
    Course -> Group -> Project -> Student.

### Fixed

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

### Notes on roles

- `User.role` only takes three values: `admin`, `teacher`, `student`.
  There is no system-wide `mentor` role.  `team_member.is_mentor` is a
  per-team flag that auto-tags senior students who help with a group;
  they are excluded from team aggregate metrics but they have no
  elevated permissions.  All Run Checks UIs gate on `can_edit`
  (course owner / teacher with course membership / system admin), not
  on raw `User.role`.

## [2026.5.18.post11] - 2026-05-18

### Fixed

- **Skeleton loaders no longer flash blue/red banner colors.** Semantic
  notification classes (`.member-api-note`, `.advisory-banner`, `.alert`)
  reused inside `[aria-busy="true"]` skeleton trees were leaking their
  feature backgrounds (blue `--info-bg`, blue `--gl-blue-950`) through the
  loading placeholders. Added a defensive scope in `loaders.css` that
  forces neutral `--surface-strong` + `--border-color` for any semantic
  banner rendered inside a skeleton container, applied system-wide.
- **Modal title icons now vertically center against the label.** `.modal-title`
  was a plain `<h3>` so leading `icon('edit') ~ ' ' ~ t('Edit Check')`
  SVGs sat at text baseline (icon below text center). Switched
  `.modal-title` to `display: inline-flex; align-items: center; gap`,
  fixing every modal in the app that puts an icon next to the title
  (Edit Check, Settings, Import, Rotate, etc.).

### Changed

- **"Rotate Secret" -> "Rotate Webhook Secret"** on the project detail
  header, with an expanded tooltip explaining that a new GitLab webhook
  token is generated and the previous secret stays valid for a 24-hour
  grace window so deliveries are not lost while you update the GitLab
  webhook configuration. Companion "Unlink" button relabeled to
  **"Unlink from GitLab"** with a longer tooltip describing automatic
  re-link on next sync.
- **Import from GitLab modal** now exposes the same Quick preset
  selector and Semester start/end date pickers used by Create Course.
  Picking a TUKE FEI preset fills academic year, semester, and both
  dates in one click; the dates are persisted onto the imported
  course's settings so auto-archive and semester windowing work
  immediately without a follow-up "Edit Settings" step. New schema
  fields `semester_start_date` / `semester_end_date` on
  `GitLabGroupImportRequest` are optional and only fill empty values
  when re-importing into an existing course (never overwrite
  teacher-configured dates).
- **Run Compliance Checks modal** scope banner now supports a `student`
  branch alongside `team` / `project`, with a stable priority order
  (student -> project -> team) so a student-scoped Run Checks dialog
  shows the student's name instead of the parent team. Template-side
  groundwork for the upcoming student-scoped "Run Checks" header
  button.

## [2026.5.18.post10] - 2026-05-18

### Changed

- Skeleton loaders now mirror the live DOM of every lazy-loaded page
  (dashboard, course detail/activity/analytics/teachers, project detail,
  student detail, team detail, admin users, support tickets/detail/form).
  Each `sk_*` macro reproduces the real card grid, table column count,
  toolbar layout, role badges, and pagination so the swap from skeleton
  to real content no longer shifts the page.
- Skeletons are now runtime-condition aware. Conditional sections render in
  the placeholder only when the corresponding integration or role gate is
  active, so users no longer see a loader for a panel that will not appear:
 - `sk_project_detail` honors retired grading availability,
    `feature_docker_verification`, `feature_ci_failure_generator`,
    `feature_conflict_simulator`, `feature_llm_suggestions`, and the
    GitLab action button visibility.
 - `sk_student_detail` honors retired grading availability and the "own profile /
    can edit" gates for compliance history and weekly detail.
 - `sk_analytics_body` honors the course staff gate for the
    manual-intervention table.
 - `sk_dashboard` honors the student / teacher / admin role split and
    the changelog panel toggle.
 - `sk_team_detail` honors student-privacy mode vs teacher full view.
 - `sk_course_detail_body` and `sk_teachers_body` honor `can_edit` and
    `can_see_admins` for the action bar and admin sub-section.
- Service worker cache version bumped to `gitpulse-v39` so all clients
  fetch the refreshed skeleton markup and bundles.

### Verified

- `python scripts/build_bundle.py` rebuilt core.bundle.js / styles.bundle.css
  with `node --check` passing on the bundle.
- `python -m pytest tests/unit -q`: 2583 passed, 19 deselected.

## [2026.5.18.post9] - 2026-05-17

### Changed

- Quality-gate hygiene pass: `src/app/api/dashboard/home.py` is back in
  `ruff format` compliance with no behavioral change.
- Release metadata, dashboard latest-changes entries, docs-site version
  metadata, and local verification docs now match the current 2026-05-17
  audit instead of carrying future-dated changelog entries.
- Current local test baseline updated to `2583 passed, 19 deselected`.
- Dead-code scanner and static artifact guard remain clean; dependency audit
  reports no known vulnerabilities in the installed environment.
- Service worker cache version bumped to `gitpulse-v38`.

## [2026.5.18.post8] - 2026-05-17

### Changed

- Static asset caching now follows the versioned-asset contract:
  `static_url()` / `?v=<hash>` responses get one-year immutable caching, while
  direct unversioned `/static/*` requests get a short 5-minute TTL.
- Login/error page inline JavaScript was moved into external static modules
  (`js/pages/login.js`, `js/error-actions.js`) so CSP remains nonce-based
  without template-local executable snippets.
- `redeploy.py` now uses system OpenSSH with deploy keys or the SSH agent,
  rejects unknown host keys by default, and no longer depends on Paramiko.
- Python and docs dependency floors were raised for current `pip-audit`
  advisories (`cryptography`, `python-multipart`, `Pillow`, `Pygments`,
  `requests`, `urllib3`, and related transitive packages).
- Local static metadata links now use `static_url()` / `absolute_static_url()`
  instead of hardcoded `/static/...` paths where the template can compute a
  content hash.
- Service worker cache version bumped to `gitpulse-v37`.

## [2026.5.18.post6] - 2026-05-17

### Changed

- Mobile responsiveness pass for skeleton loaders:
 - `sk_chart` (vertical bars) now scales down on `<768px` (96 px min-height,
    20 px bars) and `<480px` (80 px, 14 px bars), and trims axis ticks.
 - `sk_h_bars` adds a `<360px` breakpoint with 56 px label column and 12 px
    bars; very-small viewports also drop trailing axis ticks.
- Service worker cache version bumped to `gitpulse-v35`.

## [2026.5.18.post5] - 2026-05-17

### Fixed

- `sk_week_analytics` skeleton was visually too tall on phones (240 px chart
  band + 140 px doughnut + 3 full-width 1.9em stat rows). Added `<768px`
  and `<480px` rules:
 - chart `min-height` 240->180->140 px, bar `max-width` 140->64->44 px;
 - doughnut 140->120->96 px;
 - toolbar wraps; stat rows compressed to 1.5em on very small screens.
- Service worker cache version bumped to `gitpulse-v34`.

## [2026.5.18.post4] - 2026-05-17

### Fixed

- Health monitor now distinguishes **client offline** (`navigator.onLine === false`)
  from **server unreachable**. Offline state renders a neutral gray banner with
  a `wifi-off` icon and the message "You're offline. Some features may be
  unavailable until your connection is restored." instead of the misleading
  red "System is currently unreachable" banner.
- `_performCheck` short-circuits when offline (no fetch, no escalation to
  `down` after the failure threshold).
- `window 'online'` listener clears the dismissed flag, hides the offline
  banner, and triggers an immediate re-check + "Connection restored" toast.
- Added `wifi-off` icon to the JS icon registry (`GP.icons.get('wifi-off')`)
  to match the existing Jinja icon macro.
- Service worker cache version bumped to `gitpulse-v33`.

## [2026.5.18.post3] - 2026-05-17

### Changed

- Pixel-level skeleton parity for the Course Analytics page:
 - `sk_h_bars` (Teacher's Checklist) now has a 170 px label column,
    18 px bars and a 0-100 % axis tick row underneath, matching the
    real horizontal-bar chart proportions.
 - Compliance by Category placeholder now uses `sk_h_bars(count=4)`
    instead of `sk_chart` (the real chart is also horizontal).
 - `sk_chart` rewritten as `gl-skeleton-chart-wrap` with shimmer bars
    (previously bars were a flat low-opacity block invisible against
    the dark surface) plus a bottom-axis tick row.
- Service worker cache version bumped to `gitpulse-v31`.

## [2026.5.18.post1] - 2026-05-17

### Changed

- Skeleton loaders now mirror real page structure more closely:
 - New `sk_h_bars` macro renders a horizontal-bar placeholder used for the
    Teacher's Checklist card (13 R01-R13 rows of varying bar fill).
 - New `sk_legend` macro renders the chart-category legend dots above the
    Teacher's Checklist.
 - New `sk_week_pills` macro renders the Week Navigator pill row.
 - The pipeline-health doughnut skeleton on the Activity page now uses a
    radial-gradient ring (reads as a doughnut chart, not a flat disc).
- Removed an orphaned `to { opacity: 1; }` block left over in
  `loaders.css` from the previous progressive-reveal purge.
- Service worker cache version bumped to `gitpulse-v30`.

## [2026.5.18] - 2026-05-17

### Changed

- Skeleton loaders were rewritten to a pure GitLab Pajamas shimmer with no
  progressive-reveal scaffolding. All skeleton primitives (text, stats, cards,
  tables, tabs, charts, lists, activity feeds, forms) render in one shot with a
  single Pajamas shimmer animation.
- Removed legacy markers and dead controllers:
  `gl-skeleton-progressive`, `gl-skeleton-deferred`, `gl-skeleton-row--deferred`
  classes; `data-skeleton-progressive`, `data-skeleton-table`,
  `data-skeleton-total-items`, `data-skeleton-initial-items`,
  `data-skeleton-total-rows`, `data-skeleton-initial-rows`,
  `data-skeleton-delay` attributes; `initial`, `initial_lines`, `initial_rows`,
  `initial_bars`, `deferred` skeleton macro kwargs; the JS
  `_initProgressiveSkeletons` controller and its `GP.initProgressiveSkeletons` /
  `GP.initProgressiveSkeletonTables` exports; the dead
  `@keyframes glSkeletonItemReveal` rule and the
  `.gl-skeleton-table.is-progressive-expanded .gl-skeleton-row--deferred`
  reduced-motion selectors.
- Service-worker cache namespace is bumped `gitpulse-v28` -> `gitpulse-v29` and
  bundles/minified siblings were rebuilt.

## [2026.5.17.post4] - 2026-05-17

### Changed

- GitLab/Pajamas-style progressive skeleton reveal now applies across shared
  skeleton primitives, not only tables: text blocks, stats grids, cards, tabs,
  charts, lists, activity feeds, key-value rows and forms reveal the smallest
  useful structure first, then expand only when the lazy load remains visible.
- Dashboard home cards and course cards now participate in the same progressive
  reveal contract, so slow dashboard loads place primary content first and add
  secondary placeholders without leaving blank gaps.
- Support ticket and support form skeletons no longer mix a spinner into the
  same content region. They use structured placeholders for replies and follow-up
  fields; spinners remain reserved for action/background states.
- Course settings async tables now use progressive table skeletons for webhook
  configurations and compliance checks instead of centered spinner blocks.
- Removed the unused `sk_content_spinner` macro and its CSS, keeping spinners
  scoped to real inline actions, background jobs and component-local refresh.
- Application/docs metadata now point at `2026.5.17.post4`, service-worker
  cache namespace is bumped `gitpulse-v27` -> `gitpulse-v28`, and generated
  bundles/minified siblings were rebuilt.

## [2026.5.17.post3] - 2026-05-17

### Changed

- Shared table skeletons now render a GitLab/Pajamas-style progressive loading
  state: three rows appear first, then the page-specific row count is revealed
  only when the lazy request is slow enough for the skeleton to stay visible.
- Frontend loading guidance was documented in the quality-gates guide so new
  pages use skeletons for section loading and spinners for action/background
  work without mixing both indicators in the same region.
- Scale load-test console status output now uses ASCII `[PASS]` / `[FAIL]`
  markers so Windows terminals do not depend on Unicode glyph support.
- Application/docs metadata now point at `2026.5.17.post3`, service-worker
  cache namespace is bumped `gitpulse-v26` -> `gitpulse-v27`, and generated
  bundles/minified siblings were rebuilt.

## [2026.5.17.post2] - 2026-05-17

### Fixed

- Dashboard and top-bar avatars now load eagerly with high priority and use a
  neutral image background. Slow GitLab avatar responses no longer expose the
  purple initials fallback for several seconds during page entry.
- The Admin System health card now displays the runtime version exactly as
  reported by `/health` (`2026.5.17.post2`) instead of adding a `v` prefix.
  The `v...` form is reserved for git tag names.
- Service-worker cache namespace bumped `gitpulse-v25` -> `gitpulse-v26`, and
  generated bundles/minified siblings were rebuilt.

## [2026.5.17.post1] - 2026-05-17

### Changed

- Application and documentation metadata now point at `2026.5.17.post1`.
  The existing `v2026.5.17` tag is preserved, so this release uses the
  `.post1` suffix instead of rewriting tag history.
- Remaining executable inline scripts in the shared dashboard shell and
  Admin Events page were moved into `core.js` / `admin-events.js`. The page now
  passes warning-toast data through `gp-page-config` JSON instead of emitting
  per-state inline scripts.
- The DLQ loading spinner no longer carries inline style attributes; alignment
  is handled by the shared `.gl-spinner-inline` CSS utility.
- Service-worker cache namespace bumped `gitpulse-v24` -> `gitpulse-v25`, and
  generated bundles/minified siblings were rebuilt.

### Verified

- Conservative dead-code audit found no safe unreferenced candidates.
- Typography cleanup audit found no remaining project-owned files to change.

## [2026.5.16.post2] - 2026-05-16

### Added

- Shared semester helper `app.utils.semester` with `semester_floor_utc`,
  `validate_semester_date`, `validate_semester_window`, and explicit
  `SemesterDateError`. Single source of truth for "is this date inside the
  active semester" used by sync, dashboards, workers and validation.
- Course Settings now shows a persistent scope-cascade notice, confirms
  semester-date changes before save, and explains which dashboards, jobs and
  scores will be re-scoped.
- `scripts/strip_ai_typography.py` now covers JSON, web manifests,
  extensionless deployment files and optional i18n catalogues, and normalizes
  smart punctuation, decorative arrows and box-drawing comment separators.

### Changed

- Corrected accidental future-dated release metadata back to the current
  production date as same-day follow-up `2026.5.16.post2`.
- Dashboard read paths now consistently apply the per-course semester floor:
 - Admin course analytics (commits, MRs, pipelines, issues, MR notes - 6
    aggregates).
 - Home dashboard "open MRs" and "failed pipelines" widgets.
 - Course recent-activity feed (cutoff clamped to semester floor).
 - Team list "template only" detection (commit window scoped).
- Worker jobs are now semester-scoped end-to-end:
 - `enrich_issue` and `enrich_mr` skip and log webhook deliveries for entities
    whose `created_at` predates the semester floor (saves GitLab API quota and
    keeps the DB consistent with the configured scope).
 - `analyze_project_mrs` (LLM) restricts the candidate MR set to the active
    semester window so tokens are never spent on stale work.
 - `periodic_enrich_all` now pre-loads the per-project semester floor and
    skips pre-semester issues and MRs before they ever reach the queue.
- Report/download flows now use the shared blob-download helper so mobile
  browsers get a usable fallback instead of silently ignoring `download` on
  `blob:` URLs.
- Documentation, dashboard latest changes, docs-site version metadata and
  operator update notes now point at `2026.5.16.post2` as the latest release.

### Fixed

- `CourseSettings` POST handlers (both AJAX `PUT /settings` and the
  `/courses/import-config` form path) now validate `semester_start_date` /
  `semester_end_date` against a sensible window (`2020-01-01 ..` today + 2
  years, strict ordering, parseable ISO) and reject invalid input before
  writing.
- After a settings save, the multi-kind page cache is now invalidated for the
  affected course (`course`, `course-analytics`, `course-activity`, `team`,
  `project`, `student`) so the new semester scope is visible immediately
  instead of after the per-kind TTL expires.
- Report generation now preserves teacher full names, counts distinct student
  improvements, reports compliance delta as percentage points, and uses a
  mobile-safe PDF download path.
- The top progress bar no longer starts before AJAX form handlers can call
  `preventDefault`, which stopped false progress flashes on report forms.

### UX

- Semester start / end inputs in both the course settings page and the
  "Create course" modal now carry `min="2020-01-01"` and (in settings) a
  computed `max` matching server-side validation, plus expanded help text
  that explains the cascade effect on dashboards, sync and scoring.
- Submitting the settings form with a changed semester start or end date
  triggers a separate confirmation dialog summarising the impact (new sync
  window, dashboard scope shift, older activity hidden, data preserved).
- Profile empty states for "No commits" now display the active semester
  window label so it is obvious why a member has no activity.
- The service-worker cache is bumped to `gitpulse-v24` so normalized static
  assets and manifest text are picked up cleanly.

## [2026.5.16.post1] - 2026-05-16

### Fixed

- Runtime containers now expose the release version from `pyproject.toml` when
  installed package metadata is unavailable, so `/health` and Prometheus
  `app_info` no longer report `version="unknown"` after source-checkout
  deployments.
- Production images now copy `pyproject.toml` into `/app` to make version
  detection deterministic.

## [2026.5.16] - 2026-05-16

### Changed

- Student detail activity now uses the active course window when
  `CourseSettings.semester_start_date` is configured. Commit tables, commit
  counts and line totals no longer mix older template/fork history into the
  current course run.
- Compliance metric computation and historical backfill now filter issues,
  merge requests, notes, approvals, review activity, pipelines and commits to
  the current semester before evaluating weekly checks.
- Member table name cells no longer duplicate global GitLab roles that are
  already represented by the dedicated Role column.

### Fixed

- Old 2021/2022 commits can no longer make a 2026 dashboard show misleading
  contribution totals or green commit-quality checks.
- Dashboard latest changes were refreshed for `2026.5.16` and future-date drift
  was removed.

## [2026.5.15.post9] - 2026-05-15

### Added

- **Auto-archive lifecycle attention items.** The dashboard "Items that need
  your attention" widget now surfaces the full course lifecycle so teachers
  and admins never have to remember semester boundaries:
 - Course with semester ended and auto-archive opted-out
    (`skip_auto_archive = true`): a warning suggesting a manual archive to
    free up resources.
 - Course with semester ended and auto-archive enabled: an informational
    heads-up that the next scheduled sweep will archive it, with a link to
    settings if the teacher wants to keep it active.
 - Archived course from a previous academic year, archived recently
    (< 6 months): a suggestion to reactivate and reconfigure for the new
    academic year (semester dates, deadlines, weekly schedule).
 - Course archived for more than a year (but less than two): a soft
    reminder to review the course.
 - Course archived more than two years ago: a suggestion to delete the
    course to free up storage.
- All new attention items are role-aware (admin/teacher), capped to avoid
  widget overflow, and translated into Slovak.

## [2026.5.15.post8] - 2026-05-15

### Fixed

- **Toasts stuck after returning from a background tab.**  `_startToastTimer`
  scheduled dismissal via `setTimeout` only.  In a hidden tab Chromium
  throttles setTimeout to roughly once per minute, so a 5-second success
  toast could linger for minutes after the user came back.  Each toast now
  stores a wall-clock `dismissAt` timestamp; a document-level
  `visibilitychange` handler sweeps any toast past its deadline as soon as
  the tab regains focus.  Hover-paused toasts are correctly skipped.
- **Course-card "Sync completed!" badges lingering on the dashboard.**
  Same setTimeout / background-tab interaction - the 4-second auto-remove
  could stretch arbitrarily.  Each badge now records a `data-remove-at`
  wall-clock deadline and the existing dashboard `visibilitychange` handler
  removes any past-deadline badges on tab focus.
- **Top-bar clock drifting up to a minute behind after returning to a
  background tab.**  The 30-second `setInterval` was throttled while hidden.
  Added a `visibilitychange` listener that forces an immediate re-render on
  tab focus.

### Changed

- Service-worker cache namespace bumped `gitpulse-v12` -> `gitpulse-v13`.

## [2026.5.15.post7] - 2026-05-15

### Fixed

- **Global job bar: runaway elapsed counter after completion.**  Once a
  job reached `done` or `error` the per-second tick kept widening the
  "Sync completed" elapsed label using `now - startedAt`, so a banner
  that lingered while the tab was backgrounded would eventually show
  absurd values like `97m 23s` for a 30-second sync.  The tick now
  freezes elapsed at `completedAt - startedAt` for terminal jobs.
- **Global job bar: auto-hide stuck open across background tabs.**
  Chromium throttles `setTimeout` in hidden tabs to roughly once per
  minute, which delayed `_scheduleAutoHide` indefinitely for users who
  switched away while a sync finished.  Each completed job now also
  records a wall-clock `hideAt` deadline, and the existing
  `visibilitychange` handler force-hides any job past its deadline as
  soon as the tab regains focus - no more ghost banners after coming
  back from another tab.

### Changed

- Service-worker cache namespace bumped `gitpulse-v11` -> `gitpulse-v12`.

## [2026.5.15.post6] - 2026-05-15

### Added

- **Site-wide auth cross-tab sync.**  The login-page-only BroadcastChannel
  logic introduced in `post5` is now mirrored in `core.js` so it covers
  every authenticated page in the system.  When the user clicks
  `/dashboard/logout` in tab A, every other open GitPulse tab
  immediately navigates to `/dashboard/login` instead of sitting on a
  ghost-authed surface that would 401 on its next request.  Modifier
  clicks (Ctrl/Cmd/middle-click -> "open in new tab") are explicitly
  ignored - they don't actually log the current tab out.
- **Server-driven session-expiry broadcast.**  When the global HTMX
  error handler intercepts a 401 it now broadcasts a
  `session-expired` event over the same channel, so siblings join the
  redirect rather than each discovering the dead session one XHR at
  a time.
- **`GP.auth` namespace** (`GP.auth.broadcast(type)`, `GP.auth.channel`)
  exposed for pages that need to participate in auth sync explicitly
  (e.g. a future "force-logout from admin" flow).

### Changed

- Service-worker cache namespace bumped `gitpulse-v10` -> `gitpulse-v11`
  so the new `core.bundle.js` is fetched fresh on first load.

## [2026.5.15.post5] - 2026-05-15

### Added

- **Login: cross-tab session sync.**  When the user signs in successfully
  in another browser tab the login form no longer sits there as a stale
  artefact - the page broadcasts a `gitpulse-auth-v1` message (via
  `BroadcastChannel` with a `localStorage` fallback for Safari/private
  windows) and any other open login tab immediately navigates to
  `/dashboard/`.
- **Login: BFCache `pageshow` recovery.**  Hitting browser back to the
  login page after a failed attempt no longer leaves a permanently
  disabled "Signing in..." button - persisted page restores reset the
  in-flight flag and the button label / `aria-busy` state.
- **Login: status-aware error messages.**  401/403 -> "Invalid username
  or password"; 422 -> "Please check the form..."; 5xx -> "Server error.
  Please try again in a moment"; everything else -> "Sign in failed.
  Please try again."  Previously every non-OK response triggered a
  full page reload, losing the typed username and the alert context.
- **Login: explicit loading state on submit.**  The Sign-in button now
  flips to a localized "Signing in..." caption with `aria-busy="true"`,
  `cursor: progress`, and reduced opacity while the request is in
  flight.  A re-entrancy guard (`_submitInFlight`) prevents double
  submission from Enter spam, mouse double-click, or accidental form
  resubmission.
- **Login: offline submit guard.**  When the health-banner has flagged
  the server as down (`body.is-offline`) the submit handler short-
  circuits with the unreachable-server alert instead of firing a
  doomed fetch.
- **Login: autofocus on the first input** so keyboard users can start
  typing immediately on page load.
- **Login: invalid-field focus.**  Empty required fields receive
  `aria-invalid="true"` and the first invalid field is focused on
  failed validation.

### Fixed

- Six hardcoded toast messages in
  `static/js/pages/support-ticket-detail.js` (`Comment added`,
  `Failed to add comment`, `Ticket updated` ×2, `Failed to update` ×2)
  now go through `window.GP.t(...)` so non-English UI users see
  localized feedback instead of English strings.
- Slovak catalog gains nine new entries covering the support-ticket
  toasts and the new login error / loading messages.

### Changed

- Bumped the service-worker cache namespace from `gitpulse-v9` to
  `gitpulse-v10`.

## [2026.5.15.post4] - 2026-05-15

### Changed

- Replaced the bespoke full-width fixed-strip login alert with an inline
  GitLab Pajamas-style `gitlab-alert-danger` placed at the top of the
  login card itself - identical placement and look to GitLab's own
  sign-in flash messages.  Animations are now synchronized with the rest
  of the app's alert lifecycle: a 220 ms fade + down-slide entrance,
  180 ms fade + up-slide dismiss, and a 380 ms gentle shake when the same
  error re-fires.  The removed CSS includes four custom keyframes
  (`alertSlideIn` / `alertSlideInMobile` / `alertSlideOut` / `alertShake`),
  the fixed-position `.login-alert-region` strip, the desktop-only
  flush-edge override, the `has-login-alert` body class shift on the
  language switcher, and the mobile-only static-position branch.
- The runtime error-injection path (`login.js` `_showLoginError`) now
  inserts the alert region inside `.login-card` above the heading so the
  client-side and server-rendered alerts share an identical layout.
- Bumped the service-worker cache namespace from `gitpulse-v8` to
  `gitpulse-v9`.

### Fixed

- Reformatted `src/app/compliance/engine.py` to satisfy `ruff format` after
  the cumulative-semantics refactor in `post3` (CI lint failure on pipeline
  #542911).

## [2026.5.15.post3] - 2026-05-15

### Changed

- Login-page authentication alerts now slide in from the top of the viewport
  as a flush full-width strip with synchronized GitLab-style timing curves,
  animate a polished slide-out on dismiss, and shake when a second error
  retriggers the same alert.  The language switcher slides down out of the
  way and back up in sync with the alert lifecycle.  Mobile layouts fall
  back to in-flow placement and `prefers-reduced-motion` disables every
  keyframe.
- Bumped the service-worker cache namespace from `gitpulse-v7` to
  `gitpulse-v8`.

### Fixed

- Compliance Progress history snapshots now use *cumulative as-of-end-of-week*
  semantics instead of a sliding one-week window.  Previously the retroactive
  backfill filtered every entity by `week_start <= created_at <= cutoff`, so an
  issue assigned in W10 would silently flip R01 to fail in W11/W12 even though
  the issue was still assigned, and an MR created in W11 would no longer count
  toward W12's score the week it was merged.  Each weekly snapshot now answers
  the intended question - "what does compliance look like by the end of week
  N?" - making per-week scores monotonic with project progress and giving the
  improvement delta a meaningful interpretation.
- Existing history rows written by the old algorithm will be overwritten the
  next time `backfill_compliance_history` runs for a team (via upsert).

## [2026.5.15.post2] - 2026-05-15

### Changed

- Released same-day CalVer follow-up `2026.5.15.post2`.
- Replaced the remaining JavaScript-generated reload `onclick` handlers with a
  single delegated `data-action="reload-keep-scroll"` contract.
- Moved the support-ticket read-only reply hint spacing into
  `.gh-md-hint--standalone` instead of inline template styling.
- Bumped the service-worker cache namespace from `gitpulse-v6` to
  `gitpulse-v7` and rebuilt generated JS/CSS assets.

### Fixed

- The service-worker offline fallback no longer emits an inline click handler;
  retry now uses a plain GET form that works without JavaScript.
- Added frontend static tests that guard the source JavaScript and service
  worker against reintroducing inline `onclick=` handlers.

## [2026.5.15.post1] - 2026-05-15

### Changed

- Released same-day CalVer follow-up `2026.5.15.post1`.
- Replaced the login-page authentication error block with a reusable
  GitLab-style alert component: dark surface, red top border, alert icon,
  dismiss action, and no inline styling.
- Runtime login errors from rate limits or network failures now render through
  the same DOM/CSS contract as server-rendered login errors.
- Bumped the service-worker cache namespace from `gitpulse-v5` to
  `gitpulse-v6` and rebuilt generated JS/CSS assets.

### Fixed

- Removed the old login-only error CSS and its invalid red fallback, replacing
  it with shared component styling and static tests that guard the contract.

## [2026.5.15] - 2026-05-15

### Changed

- Rebased application versioning from the temporary `0.1.1` cleanup marker to
  CalVer `2026.5.15`.
- Version rationale: the repository started from a full-codebase initial commit,
  and the pre-release audit found `1875` commits, 47 Alembic migration files,
  and no historical release tags before this normalization commit. A
  reconstructed SemVer number would be arbitrary, while CalVer records the
  production release date honestly.
- Bumped the service-worker cache namespace from `gitpulse-v4` to `gitpulse-v5`
  so clients pick up the release cleanly.
- Updated docs, docs-site changelog, dashboard latest changes, and deployment
  examples to the 2026-05-15 production state.

### Fixed

- Ignored the generated `dead-code-report.txt` artifact so local dead-code
  audits no longer dirty the worktree.
- Verified the latest CI guard fixes that replaced shell-dependent `git
  ls-files` calls in static/dead-code checks with repository tree walks.

## [0.1.1] - 2026-05-14

### Changed

- Stabilized local/CI gates with test environment normalization, shell-independent
  pre-push unit tests, Ruff `0.15.4`, bundle drift check, static artifact guard,
  and a non-blocking dead-code report.
- Updated dashboard latest changes and docs to the current production baseline:
  26 scheduled jobs, 45 ORM model files, 47 Alembic migration files, and head
  `046`.
- Aligned the admin scheduled-jobs registry with the production scheduler.
- Bumped application version from `0.1.0` to `0.1.1`.

### Fixed

- Removed stray tracked root artifact `-w`.
- Made bundle/vendor scripts Windows-safe by replacing Unicode status glyphs with
  ASCII markers.
- Prevented duplicate OpenAPI operation IDs on `/dashboard/login`.
- Made tests warning-clean and fail on unawaited coroutine warnings.
- Enforced expiry for previous webhook secrets and added cleanup for expired
  previous hashes/lookups.
- Added email log retention cleanup for terminal `sent`/`failed` entries only.
- Avoided partial writes in legacy roster upload by validating all rows before
  committing.
- Rejected retired grading saves whose total category weight is `0`.
- Added Redis session-store fallback metrics and readiness probing when the
  Redis session store is enabled.

### Verified

- `ruff check src tests scripts`
- `ruff format --check src tests scripts`
- `mypy src/app`
- `pytest -q` (`2521 passed, 19 deselected`)
- `python scripts/build_bundle.py --check`
- `python scripts/vendor_alpine_csp.py --check`
- `python scripts/check_static_artifacts.py`
- `alembic heads` (`046 (head)`)
