# Product

<!-- impeccable:product-schema 1 -->

<!-- Written during `/impeccable init` on 2026-08-18 WITHOUT a live interview:
     the user had explicitly instructed the session to continue without asking
     further questions. Per init's own rule, every fact below is therefore drawn
     from repository evidence (README.md, src/app/*, docs-site/*, CLAUDE.md,
     .env.example, docker-compose*.yml) or from decisions the user stated in this
     working session. Nothing here is guessed: where the repository was silent -
     for example on how teachers actually work between labs - the section says
     what the code proves and no more. Confirm the Users section with the user
     when they are next available; it is the one place a real interview would
     add something the repository cannot. -->

## Platform

web

## Users

- **Teachers (primary).** University staff running a DevOps course, working from
  a laptop between and during labs. Their job: see which student teams are
  actually collaborating on GitLab, spot the ones at risk early, and defend a
  grade with evidence rather than impression.
- **Students.** Members of a team, checking how their own contribution and their
  team's collaboration is being read by the system.
- **Admins / operators.** Run the instance: users and roles, courses, GitLab
  connectivity, background jobs, the event pipeline, and health.

## Product Purpose

GitPulse ingests a course's GitLab activity - pushes, merge requests, issues,
notes, pipelines, member changes - and turns it into teaching insight: per-team
and per-student compliance scores against explicit rules, an activity trail, and
exports. It exists so that assessing teamwork on a real Git workflow is evidence-
based and repeatable instead of manual and anecdotal. Success is a teacher who
can answer "how is this team doing, and why" in one screen, and a student who can
see the same answer.

## Positioning

The mechanism a neighbouring analytics dashboard could not truthfully copy: a
**named, configurable compliance engine (R01-R13)** - issue assignment, branch
naming, test changes, MR/issue linkage, MR template, reviews received, review
duty, response quality, approvals, merged-by-author, closure state, pipeline
health - scored per course with per-check weights, computed from ingested GitLab
events rather than from GitLab's own aggregate statistics. The scoring rules are
the product; the dashboard is how they are read.

## Operating Context

- Deployed for KPI FEI TUKE; production sits behind the university network and is
  reached over SSH for deploys (`redeploy.py`, `git pull` on the host).
- Authentication is GitLab OAuth against the faculty GitLab
  (`gitlab.example.com`); there is no local password login.
- Data reaches pages **only** through sync + webhooks (or an explicit manual
  Enrich / Sync / Import). No page render calls the GitLab API live.
- Event-driven throughout: webhook -> event processing -> metrics recomputation ->
  cache invalidation -> SSE notification. Background work runs on RQ with three
  priority levels; there is no timer daemon - sweeps are opportunistic.
- Two languages ship together, Slovak and English, in the app and the docs site.
- The documentation is a separate MkDocs Material site served under `/docs/`.

## Capabilities and Constraints

- Multi-tenant by course; a course can be archived, and an archived course is
  **read-only** - the client guard locks its forms and the server enforces it by
  walking the routing table. Lifecycle actions stay enabled.
- Compliance snapshots are immutable: a backfill fills only MISSING weeks, and
  snapshots are capped at the teaching window.
- Optional LLM analysis of merge requests through any OpenAI-compatible provider
  (plus Gemini and Groq); author handles are redacted before anything leaves the
  instance.
- Every private page and API carries a strict `X-Robots-Tag`; only the login page
  is indexable, which is a student-privacy requirement, not an SEO preference.
- Stack (existing, not a greenfield decision): FastAPI + async SQLAlchemy +
  PostgreSQL + Redis/RQ behind Caddy; Jinja templates with htmx, the
  @alpinejs/csp build, and GSAP as the single motion owner; MkDocs Material for
  the docs.
- Terminology: a **course** contains **teams** (a GitLab subgroup) which contain
  **students** and **projects**; a **check** is one R-rule; a **snapshot** is one
  week's computed metrics.
- The Assignments feature was removed on 2026-06-17 and must not return.

## Brand Commitments

- The product is called **GitPulse**; the mark is the GitLab tanuki crossed by an
  ECG pulse, and the same file serves the app and the documentation.
- The interface follows **GitLab's Pajamas design language**, verified against
  `@gitlab/ui` and against live GitLab pages rather than from memory - colours,
  radii, spacing, motion, and the documentation site's layout are all matched to
  measured values. This is a standing instruction from the user, not a
  preference.
- Typefaces are self-hosted GitLab Sans and GitLab Mono.
- One pattern per interaction: a single confirmation dialog, one loading state,
  one refresh contract, one motion owner. Duplicate implementations are treated
  as defects.

## Evidence on Hand

- `README.md` / `README.sk.md`, verified against code on 2026-08-06.
- The docs site under `docs-site/docs/` (Slovak + English), including an API
  reference verified against the implementation.
- A production instance at `gitpulse.kpi.fei.tuke.sk` with real course data.
- A test suite of 2 645 unit tests plus integration and Playwright e2e suites.
- **No** customer testimonials, pricing, case studies, or third-party benchmarks
  exist. Future work must not invent them - this is a university thesis project,
  not a commercial product.

## Product Principles

1. **Evidence over impression.** Every number shown must be traceable to ingested
   GitLab activity and to a named rule.
2. **Ingested, never live.** A page renders from stored data; GitLab is reached
   by sync and webhooks, so a dead token degrades freshness, never the interface.
3. **One pattern per interaction.** The second implementation of a behaviour is a
   defect, however small.
4. **Match GitLab by measurement.** Parity claims carry the number and where it
   was taken; "looks about right" is not parity.
5. **Student privacy is a constraint, not a setting.** Nothing private is
   indexable, and nothing identifying leaves the instance for an LLM.

## Accessibility & Inclusion

- Every form field must have an associated label; group captions are
  `<fieldset>` + `<legend>`, never a field-less `<label>`.
- Motion respects `prefers-reduced-motion` throughout; the loading and busy
  states carry `aria-busy` and live regions.
- Both interface languages must stay complete; Slovak is the default.
