# 9. Thesis Documentation Outline & Content Plan

> **Documentation Status (2026-02-09):** Verified against current implementation.
> - **Source of truth (API):** `src/app/api/*`, `src/app/schemas/*`, runtime `/openapi.json`.
> - **Source of truth (CI/quality gates):** `.gitlab-ci.yml`, `pyproject.toml`.
> - **Local gate baseline:** `ruff check src tests`, `ruff format --check src tests`, `mypy src/app`.


## Thesis Title

**DevOps Teaching Support Tools: Automated Evaluation of Student
Collaboration in GitLab-based Teamwork**

## Thesis Objectives Alignment

| # | Objective | Chapter(s) |
| - | --------- | ---------- |
| 1 | Analyze course content and teaching requirements | Ch. 2, Ch. 3 |
| 2 | Design and implement the support tools | Ch. 4, Ch. 5, Ch. 6 |
| 3 | Verify the tools during teaching | Ch. 7 |
| 4 | Improve based on findings | Ch. 8 |
| 5 | Produce documentation | Entire thesis + appendices |

---

## Chapter Structure

### Chapter 1: Introduction (5-7 pages)

| Section | Content |
| ------- | ------- |
| 1.1 Motivation | Teaching collaborative software engineering at scale; manual evaluation bottleneck; need for automated objective metrics |
| 1.2 Problem Statement | How to objectively evaluate student GitLab-based teamwork (issues, MRs, code review, CI/CD) with minimal teacher overhead? |
| 1.3 Goals | 5 thesis objectives listed above |
| 1.4 Methodology | Design Science Research: design -> build -> evaluate -> improve cycle |
| 1.5 Thesis Structure | Brief summary of each chapter |

**Key diagram:** None (introductory text only)

### Chapter 2: Theoretical Background (10-15 pages)

| Section | Content |
| ------- | ------- |
| 2.1 DevOps Principles | CI/CD, collaboration, automation, infrastructure as code; relevance to education |
| 2.2 GitLab as Educational Platform | Git workflow, issues, MRs, code review, pipelines; GitLab-specific features (webhooks, API, approvals) |
| 2.3 Software Process Assessment | Existing approaches to evaluating collaborative software development; limitations of manual rubrics |
| 2.4 Related Work | Academic tools for evaluating Git-based student work (GitInspector, GHTorrent, similar); gaps in existing solutions |
| 2.5 Webhook-Driven Event Architectures | Event sourcing, at-least-once delivery, idempotency; relevance to real-time process monitoring |
| 2.6 Technology Stack Overview | FastAPI, PostgreSQL, Redis, RQ, Docker Compose; justification of choices |

**Key diagrams:**
- Fig. 2.1 - Git branching workflow (feature branch -> MR -> review -> merge)
- Fig. 2.2 - GitLab webhook delivery model
- Fig. 2.3 - Comparison table of related tools

### Chapter 3: Requirements Analysis (8-12 pages) - *Objective 1*

| Section | Content |
| ------- | ------- |
| 3.1 Course Context | ZSI course structure, semester plan, team assignment requirements; reference to kurzy.kpi.fei.tuke.sk/zsi/ |
| 3.2 ZSI Team Assignment Analysis | Detailed breakdown of week-12 assignment: issues, branches, MRs, reviews, approvals, merges, CI |
| 3.3 Základy DevOps Course Analysis | Semester plan topics (Git, Docker, CI/CD, testing, MR/review); shared requirements with ZSI |
| 3.4 Stakeholder Analysis | Teacher needs, student needs, department needs |
| 3.5 Functional Requirements | Requirements mapping table: course requirement -> system feature -> check ID -> acceptance criterion (12 rows) |
| 3.6 Non-Functional Requirements | Performance (150 students), reliability (99% uptime), security (least privilege, HTTPS, secrets), data privacy (GDPR) |
| 3.7 MVP Scope Definition | In-scope vs out-of-scope; prioritization rationale |
| 3.8 Risks and Mitigations | 10 identified risks with impact/likelihood/mitigation |

**Key diagrams:**
- Fig. 3.1 - ZSI team assignment workflow (issue -> branch -> MR -> review -> approve -> merge -> close)
- Fig. 3.2 - Requirements traceability matrix (course requirement <-> system check <-> test case)
- Table 3.1 - Functional requirements mapping (12 checks)
- Table 3.2 - Risk register

**Source artifact:** `docs/01-requirements.md`

### Chapter 4: Architecture Design (10-15 pages) - *Objective 2*

| Section | Content |
| ------- | ------- |
| 4.1 System Architecture Overview | Component diagram; services (API, Worker, Scheduler, DB, Redis, Proxy) |
| 4.2 Event Flow Design | Webhook -> ingestion -> enrichment -> metrics -> reports pipeline |
| 4.3 Idempotency Strategy | Three-layer dedup: event UUID -> entity UPSERT -> Redis job lock |
| 4.4 Queue Architecture | RQ with 3 priority queues (high, default, low); job types; retry policy |
| 4.5 Authentication Model | Three auth flows: webhook token, bearer API, session dashboard |
| 4.6 Security Architecture | HTTPS via Caddy, security headers, CSP, least-privilege DB, secret management |
| 4.7 Observability Design | Structured logging, Prometheus metrics, OpenTelemetry tracing, correlation IDs |
| 4.8 Deployment Architecture | Docker Compose topology; resource constraints; backup strategy |
| 4.9 Technology Decisions | RQ vs Celery justification; WeasyPrint vs Playwright justification; Caddy vs Traefik |

**Key diagrams:**
- Fig. 4.1 - Component diagram (all services and their connections)
- Fig. 4.2 - Sequence diagram: webhook -> enqueue -> process -> enrich -> metrics
- Fig. 4.3 - Sequence diagram: teacher dashboard request flow
- Fig. 4.4 - Idempotency layers diagram
- Fig. 4.5 - Queue priority architecture
- Fig. 4.6 - Authentication flow diagram (3 flows)
- Fig. 4.7 - Docker Compose service topology
- Table 4.1 - Technology decision matrix (alternatives compared)

**Source artifact:** `docs/02-architecture.md`

### Chapter 5: Data Model (8-10 pages) - *Objective 2*

| Section | Content |
| ------- | ------- |
| 5.1 Entity-Relationship Model | ER diagram covering all 17 tables; relationship cardinalities |
| 5.2 Core Entities | Course, Team, Student, GitLabProject - structure and relationships |
| 5.3 GitLab Entities | Issue, MergeRequest, MRNote, MRApproval, Pipeline, ReviewActivity - fields and constraints |
| 5.4 Metrics Entities | MetricSnapshot, TeamMetricSnapshot - per-student and per-team scoring |
| 5.5 Operational Entities | WebhookEvent, BackgroundJob, AuditLog - event sourcing and job tracking |
| 5.6 Indexes and Performance | Index strategy for common query patterns; dedup keys |
| 5.7 Migration Strategy | Alembic versioning; existing migrations; how to add new columns |
| 5.8 Data Volume Projections | Estimated row counts and storage for 150 students over 1 semester |

**Key diagrams:**
- Fig. 5.1 - Full ER diagram (Mermaid)
- Table 5.1-5.17 - Column definitions for each table
- Table 5.18 - Index reference
- Table 5.19 - Data volume estimates

**Source artifact:** `docs/03-data-model.md`

### Chapter 6: Implementation (15-20 pages) - *Objective 2*

| Section | Content |
| ------- | ------- |
| 6.1 Project Structure | Repository layout; module organization |
| 6.2 API Layer | FastAPI routers; endpoint summary; Pydantic schemas; auth dependencies |
| 6.3 Webhook Receiver | Ingestion flow; dedup; payload parsing; enqueue |
| 6.4 GitLab Client | httpx-based client; enrichment data fetching; error handling |
| 6.5 Background Workers | RQ jobs: process_event, enrich_issue, enrich_mr, compute_metrics, generate_report |
| 6.6 Compliance Engine | 12 checks (R01-R12) with formulas and pseudocode; partial scoring; weight system |
| 6.7 Communication Indicators | 6 non-scoring diagnostic metrics; implementation details |
| 6.8 Teacher Dashboard | Jinja2 + htmx + Alpine.js; component macro system (15 macro files); 6 JS modules; 18 CSS component files; export endpoints (CSV, JSON, PDF) |
| 6.9 Report Generation | HTML/PDF/CSV/JSON renderers; WeasyPrint integration; self-contained HTML |
| 6.10 Observability Implementation | structlog configuration; Prometheus metrics (18 metrics); OpenTelemetry tracing; correlation IDs |
| 6.11 Security Implementation | Webhook token verification; bearer auth; session auth; security headers middleware; CSP |
| 6.12 DevOps Tooling | Pre-commit hooks; Ruff + mypy; GitLab CI pipeline (lint -> test -> build -> publish) |
| 6.13 Docker Packaging | Dockerfile (API); Dockerfile.worker; docker-compose.yml (7 core + 2 monitoring services) |

**Key diagrams:**
- Fig. 6.1 - Repository file tree
- Fig. 6.2 - API endpoint map
- Fig. 6.3 - Compliance engine check flowchart
- Fig. 6.4 - Check scoring formulas (R01-R12)
- Fig. 6.5 - Dashboard screenshots (course list, team detail, student detail)
- Fig. 6.6 - Sample HTML report screenshot
- Fig. 6.7 - Sample PDF report page
- Fig. 6.8 - GitLab CI pipeline stages diagram
- Listing 6.1 - Webhook handler code (key excerpt)
- Listing 6.2 - Compliance engine `run_all_checks()` (key excerpt)
- Listing 6.3 - `@idempotent_job` decorator implementation
- Listing 6.4 - docker-compose.yml (abbreviated)

**Source artifacts:** `src/app/` (full source), `docs/04-api-spec.md`

### Chapter 7: Verification & Evaluation (10-15 pages) - *Objective 3*

| Section | Content |
| ------- | ------- |
| 7.1 Test Strategy | Unit / integration / E2E levels; tools (pytest, testcontainers) |
| 7.2 Unit Test Results | 1546 tests across compliance engine, roles, gaming detection, and more; coverage analysis |
| 7.3 Pilot Deployment | Setup steps; timeline (weeks 1-13); technical observations |
| 7.4 Evaluation Methodology | Data collection plan; comparison baseline; analysis methods |
| 7.5 Accuracy Results | Score correlation (Pearson r); per-check agreement; FP/FN rates; MAE |
| 7.6 Efficiency Results | Time savings per team; total semester savings |
| 7.7 Reliability Results | Uptime; event completeness; processing latency; failed jobs |
| 7.8 Usability Results | Teacher feedback summary (Form #1 and #2); qualitative observations |
| 7.9 Threats to Validity | Internal, external, construct validity threats and mitigations |
| 7.10 Discussion | Interpretation of results; comparison with expectations; lessons learned |

**Key diagrams:**
- Fig. 7.1 - Test coverage report (screenshot)
- Fig. 7.2 - Score correlation scatter plot (GitPulse vs manual)
- Fig. 7.3 - Per-check agreement heatmap (R01-R12)
- Fig. 7.4 - Processing latency histogram (p50/p95/p99)
- Fig. 7.5 - System uptime timeline (weeks 10-12)
- Table 7.1 - Accuracy metrics summary
- Table 7.2 - Teacher feedback summary (Likert averages)
- Table 7.3 - False positive/negative analysis per check

**Source artifacts:** `docs/10-evaluation-plan.md`, `docs/06-test-plan.md`, `docs/07-pilot-plan.md`

### Chapter 8: Improvements & Future Work (5-8 pages) - *Objective 4*

| Section | Content |
| ------- | ------- |
| 8.1 Weight Recalibration | How accuracy data informs weight adjustment; before/after comparison |
| 8.2 Check Refinements | Specific checks that need tuning (threshold, formula, or scope changes) |
| 8.3 Prioritized Improvement Backlog | MoSCoW-prioritized list of 15 improvements with effort estimates |
| 8.4 Task & Assignment Changes | Recommendations for adjusting student assignments based on tool findings |
| 8.5 Technical Debt | Items to address before next deployment (config naming, N+1 queries, shared constants) |
| 8.6 Extension to Other Courses | How GitPulse can serve Základy DevOps; additional check types needed |
| 8.7 LLM Integration Roadmap | Optional module for review quality analysis; privacy considerations; architecture sketch |
| 8.8 Long-Term Vision | Multi-course analytics; cross-semester student progress; department-level reporting |

**Key diagrams:**
- Table 8.1 - Improvement backlog (MoSCoW)
- Fig. 8.1 - Weight recalibration comparison (before/after radar chart)
- Fig. 8.2 - LLM integration architecture sketch

**Source artifact:** `docs/08-post-pilot.md`

### Chapter 9: Conclusion (2-3 pages)

| Section | Content |
| ------- | ------- |
| 9.1 Summary of Contributions | What was built, verified, and improved |
| 9.2 Objective Fulfillment | Table mapping each objective to evidence (chapter + artifact) |
| 9.3 Key Findings | Most impactful results from pilot |
| 9.4 Limitations | Acknowledged constraints (single course, single teacher, small sample) |
| 9.5 Final Remarks | Value of automated evaluation tools for DevOps education |

---

## Appendices

| Appendix | Content | Source |
| -------- | ------- | ------ |
| A | Full repository file tree | `tree` command output |
| B | Database ER diagram (full size) | `docs/03-data-model.md` Fig. 5.1 |
| C | API endpoint reference (all endpoints with examples) | `docs/04-api-spec.md` |
| D | Compliance check formulas (R01-R12) with pseudocode | `src/app/compliance/engine.py` docstrings |
| E | Sample generated reports (HTML screenshot, PDF page, CSV excerpt, JSON excerpt) | Generated from pilot data |
| F | GitLab integration guide (step-by-step) | `docs/05-gitlab-integration.md` |
| G | MR template and branch naming policy | `docs/05-gitlab-integration.md` §5.5 |
| H | Teacher feedback forms (#1 and #2) | `docs/10-evaluation-plan.md` §10.8 |
| I | Student feedback survey | `docs/10-evaluation-plan.md` §10.8.3 |
| J | Prometheus metrics reference (18 metrics) | `README.md` metrics table |
| K | Docker Compose configuration | `docker-compose.yml` |
| L | GitLab CI pipeline configuration | `.gitlab-ci.yml` |
| M | Pre-commit hook configuration | `.pre-commit-config.yaml` |
| N | Environment variables reference | `.env.example` |
| O | Backup and restore procedures | `scripts/backup.sh`, `scripts/restore.sh` |

---

## Diagrams Inventory

Complete list of all diagrams to produce for the thesis.

| # | Diagram | Type | Chapter | Tool |
| - | ------- | ---- | ------- | ---- |
| Fig. 2.1 | Git branching workflow | Flowchart | Ch. 2 | Mermaid / draw.io |
| Fig. 2.2 | GitLab webhook delivery model | Sequence | Ch. 2 | Mermaid |
| Fig. 2.3 | Related tools comparison | Table | Ch. 2 | LaTeX table |
| Fig. 3.1 | ZSI assignment workflow | Flowchart | Ch. 3 | Mermaid / draw.io |
| Fig. 3.2 | Requirements traceability matrix | Matrix | Ch. 3 | LaTeX table |
| Fig. 4.1 | System component diagram | Architecture | Ch. 4 | draw.io / PlantUML |
| Fig. 4.2 | Webhook processing sequence | Sequence | Ch. 4 | Mermaid |
| Fig. 4.3 | Dashboard request flow | Sequence | Ch. 4 | Mermaid |
| Fig. 4.4 | Idempotency layers | Layer diagram | Ch. 4 | draw.io |
| Fig. 4.5 | Queue priority architecture | Block diagram | Ch. 4 | draw.io |
| Fig. 4.6 | Authentication flows | Flow diagram | Ch. 4 | Mermaid |
| Fig. 4.7 | Docker Compose topology | Deployment | Ch. 4 | draw.io |
| Fig. 5.1 | Entity-Relationship diagram | ER | Ch. 5 | Mermaid / dbdiagram.io |
| Fig. 6.1 | Repository file tree | Tree | Ch. 6 | Text listing |
| Fig. 6.2 | API endpoint map | Table | Ch. 6 | LaTeX table |
| Fig. 6.3 | Compliance engine flowchart | Flowchart | Ch. 6 | Mermaid |
| Fig. 6.4 | Check scoring formulas | Formula table | Ch. 6 | LaTeX |
| Fig. 6.5 | Dashboard screenshots (3) | Screenshot | Ch. 6 | Browser capture |
| Fig. 6.6 | HTML report screenshot | Screenshot | Ch. 6 | Browser capture |
| Fig. 6.7 | PDF report page | Screenshot | Ch. 6 | PDF viewer capture |
| Fig. 6.8 | GitLab CI pipeline stages | Pipeline | Ch. 6 | Mermaid / draw.io |
| Fig. 7.1 | Test coverage report | Screenshot | Ch. 7 | pytest-cov output |
| Fig. 7.2 | Score correlation scatter plot | Chart | Ch. 7 | matplotlib / Excel |
| Fig. 7.3 | Per-check agreement heatmap | Heatmap | Ch. 7 | seaborn / Excel |
| Fig. 7.4 | Processing latency histogram | Histogram | Ch. 7 | Prometheus / Grafana |
| Fig. 7.5 | Uptime timeline | Timeline | Ch. 7 | Prometheus / Grafana |
| Fig. 8.1 | Weight recalibration radar chart | Radar | Ch. 8 | matplotlib |
| Fig. 8.2 | LLM integration architecture | Architecture | Ch. 8 | draw.io |

**Total: 28 diagrams** (10 generated from data after pilot; 18 designable before pilot)

---

## Artifacts Inventory

All artifacts produced as part of the thesis work.

| # | Artifact | Type | Location |
| - | -------- | ---- | -------- |
| A1 | Source code (FastAPI backend) | Code | `src/app/` (62 Python files) |
| A2 | Compliance engine (12 checks) | Code | `src/app/compliance/engine.py` |
| A3 | Unit tests (1546 tests) | Code | `tests/unit/` |
| A4 | Alembic migrations (2 versions) | Code | `alembic/versions/` |
| A5 | Jinja2 templates (6 files) | Code | `src/app/templates/` |
| A6 | Docker packaging | Config | `Dockerfile`, `Dockerfile.worker`, `docker-compose.yml` |
| A7 | Caddy reverse proxy config | Config | `Caddyfile` |
| A8 | Prometheus monitoring config | Config | `monitoring/prometheus.yml` |
| A9 | GitLab CI pipeline | Config | `.gitlab-ci.yml` |
| A10 | Pre-commit hooks | Config | `.pre-commit-config.yaml` |
| A11 | PostgreSQL init script | SQL | `scripts/pg-init.sql` |
| A12 | Backup/restore scripts | Bash | `scripts/backup.sh`, `scripts/restore.sh` |
| A13 | Password hashing utility | Python | `scripts/hash_password.py` |
| A14 | Environment template | Config | `.env.example` |
| A15 | Requirements analysis document | Markdown | `docs/01-requirements.md` |
| A16 | Architecture document | Markdown | `docs/02-architecture.md` |
| A17 | Data model document | Markdown | `docs/03-data-model.md` |
| A18 | API specification | Markdown | `docs/04-api-spec.md` |
| A19 | Deployment & GitLab integration guide | Markdown | `docs/05-gitlab-integration.md` |
| A20 | Test plan & CI pipeline docs | Markdown | `docs/06-test-plan.md` |
| A21 | Pilot execution plan | Markdown | `docs/07-pilot-plan.md` |
| A22 | Post-pilot improvements plan | Markdown | `docs/08-post-pilot.md` |
| A23 | Thesis outline (this document) | Markdown | `docs/09-thesis-outline.md` |
| A24 | Evaluation plan | Markdown | `docs/10-evaluation-plan.md` |
| A25 | README with exact commands | Markdown | `README.md` |
| A26 | Teacher feedback forms (2) | Text | `docs/10-evaluation-plan.md` §10.8 |
| A27 | Student feedback survey | Text | `docs/10-evaluation-plan.md` §10.8.3 |
| A28 | Manual grading spreadsheet | Excel/CSV | Produced during pilot (week 12) |
| A29 | Prometheus metrics export | CSV | Produced during pilot (week 13) |
| A30 | Evaluation results report | Chapter | Thesis Ch. 7 (produced after pilot) |

**Total: 30 artifacts** (25 produced pre-pilot; 5 produced during/after pilot)

---

## Estimated Page Counts

| Chapter | Pages | Status |
| ------- | ----- | ------ |
| 1. Introduction | 5-7 | Write after all other chapters |
| 2. Theoretical Background | 10-15 | Research + write |
| 3. Requirements Analysis | 8-12 | Content in `docs/01-requirements.md` |
| 4. Architecture Design | 10-15 | Content in `docs/02-architecture.md` |
| 5. Data Model | 8-10 | Content in `docs/03-data-model.md` |
| 6. Implementation | 15-20 | Code walkthroughs + listings |
| 7. Verification & Evaluation | 10-15 | After pilot (weeks 10-13) |
| 8. Improvements & Future Work | 5-8 | Content in `docs/08-post-pilot.md` |
| 9. Conclusion | 2-3 | Write last |
| Appendices | 15-20 | Generated from artifacts |
| **Total** | **88-125** | |

