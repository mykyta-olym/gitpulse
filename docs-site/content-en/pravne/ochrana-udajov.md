---
title: "Privacy Statement"
description: "GitPulse Privacy Statement - how we collect, use, and protect your personal data"
---
{{< details >}}
- For: Everyone
- Requires: Nothing
{{< /details >}}
*Last updated: October 20, 2026*

---

## Introduction

At GitPulse, we take the privacy and security of your information seriously. This privacy statement ("Privacy Statement") explains how the Department of Computers and Informatics (KPI), Faculty of Electrical Engineering and Informatics (FEI), Technical University of Kosice (TUKE) ("Data Controller", "we", "our", "us") handles your personal data when you use the GitPulse platform ("Service").

"Personal Data," as used in this Privacy Statement, is information that identifies or can reasonably be linked directly or indirectly to an identifiable person.

This Privacy Statement applies to the GitPulse web application available at [gitpulse.kpi.fei.tuke.sk](https://gitpulse.kpi.fei.tuke.sk) and all associated services, including webhook integrations, email notifications, and API endpoints.

---

## What Personal Data Does GitPulse Collect?

### Information You Provide Through Authentication

When you sign in to GitPulse via GitLab OAuth (Single Sign-On), we receive the following from the university GitLab instance:

- Full name and display name
- Email address
- GitLab username and user ID
- Profile avatar URL

{{< alert type="note" >}}
**Passwords.** GitPulse does not collect, store, or have access to your GitLab password. Authentication is handled entirely by the university GitLab OAuth provider.
{{< /alert >}}
### Course and Activity Data Synced from GitLab

To provide course management and assessment functionality, GitPulse synchronizes the following data from GitLab repositories linked to your courses:

| Data Category | Examples |
|---|---|
| Git commits | Author, message, timestamp, diff statistics |
| Merge requests | Title, description, reviews, comments |
| Issues | Title, description, labels, participants |
| CI/CD pipelines | Run results, job logs |
| Repository metadata | Branches, tags, milestones |
| Membership | Group and project membership |

### Information Collected Automatically

When you use the Service, we automatically collect limited technical information necessary for operation:

- **IP address** - retained in server logs for security and abuse prevention
- **Browser type** - from the User-Agent header
- **Language preference** - for displaying the correct language
- **Timestamps** - of access and actions performed
- **HTTP request metadata** - method, path, status code, response time

{{< alert type="note" >}}
**No tracking.** GitPulse does not use any analytics services, tracking pixels, session replay tools, or fingerprinting technologies.
{{< /alert >}}
### Email Notifications

If email notifications are enabled for your course, we process your email address to deliver:

- Welcome emails upon course enrollment
- Periodic assessment and feedback reports
- Administrative notifications from your course instructor

All emails include an unsubscribe mechanism. We do not track email opens or link clicks.

---

## What Personal Data Is Not Collected?

GitPulse does not intentionally collect sensitive personal data, such as:

- Passwords or authentication credentials
- Financial or payment information
- Biometric data, health information, or genetic data
- Political opinions, religious beliefs, or trade union membership
- Data revealing racial or ethnic origin

{{< alert type="warning" >}}
**Data in repositories.** We realize that users might include sensitive personal data within commit messages, issue descriptions, or other free-form content in their GitLab repositories. If sensitive personal data exists in synced repository content, the repository owner (your course instructor) is responsible for its handling.
{{< /alert >}}
GitPulse is not directed at individuals under the age of 16. See the [Children's Privacy](#childrens-privacy) section for more details.

---

## How Does GitPulse Use My Personal Data?

GitPulse collects and processes personal data for the following purposes:

| Purpose of Processing | Categories of Data Used |
|---|---|
| To authenticate your identity and provide access to the Service | Account information (name, email, GitLab ID) |
| To display your profile within courses you are enrolled in | Account information, avatar URL |
| To synchronize and display course activity and progress | Course and activity data from GitLab |
| To generate automated assessment feedback on DevOps practices | Commits, merge requests, CI/CD pipeline data |
| To give the classroom assistant's feedback in GitLab, when the teacher turns it on for the course | Commits, merge requests, issues, GitLab username |
| To enable instructors to evaluate student work through course assessment rules | Course activity data, assessment results |
| To send email notifications about course progress and assessments | Email address, course enrollment data |
| To maintain the security of the Service and prevent abuse | IP address, access logs, request metadata |
| To improve the reliability and performance of the Service | Aggregated, non-identifying usage metrics |

---

## Legal Basis for Processing

When our processing is subject to the General Data Protection Regulation ("GDPR"), we rely on the following legal bases:

### Legitimate Interest (Article 6(1)(f) GDPR)

- Providing educational assessment and course management functionality as part of the university curriculum
- Ensuring the security, availability, and integrity of the Service
- Generating aggregated, non-identifying analytics to improve the Service

### Consent (Article 6(1)(a) GDPR)

- Sending optional email notifications about course progress (you may withdraw consent at any time by unsubscribing)
- Storing non-essential cookies (language preference)

### Performance of a Task Carried Out in the Public Interest (Article 6(1)(e) GDPR)

- Processing data for educational assessment purposes as part of the university's public mission

You may object to processing based on legitimate interest at any time by contacting us at the address listed in the [Contact Us](#contact-us) section.

---

## With Whom Does GitPulse Share My Data?

### Course Instructors and Administrators

Your name, email, GitLab username, course activity, and assessment results are visible to instructors and administrators of the courses you are enrolled in. This is necessary for the educational assessment purpose of the Service.

### Other Students

Within a course, other enrolled students may see your name and avatar. Detailed activity data and assessment results are visible only to instructors unless the course settings explicitly allow peer visibility.

### University GitLab Instance

GitPulse communicates with the university GitLab instance at [gitlab.example.com](https://gitlab.example.com) to synchronize course data. This communication uses encrypted connections and authenticated API tokens.

When a teacher turns on the classroom assistant for a course, GitPulse also writes to the teams' projects, through a bot account the course creates in GitLab. The bot comments on commits and merge requests, opens and closes the exercise issues, adds a commit to a branch for the merge-conflict exercise and, if the teacher allows it, approves and merges a merge request. The bot account's token is stored encrypted and students never see it.

### No Third-Party Sharing

{{< alert type="note" >}}
**Your data is safe.** GitPulse does not sell, rent, trade, or otherwise share your personal data with any third-party companies, advertisers, data brokers, or external services. All data processing occurs exclusively within the university infrastructure hosted at the Technical University of Kosice.
{{< /alert >}}

The Support & suggestions panel links to voluntary diploma thesis questionnaires in Google Forms. GitPulse sends them no data, and the questionnaires collect no name, email or login.

### Legal Disclosure

We may disclose your personal data if required by law, in response to a valid legal process, or to protect the rights, property, or safety of the university, its students, or the public.

---

## How Does GitPulse Secure My Data?

We employ technical and organizational measures to protect your personal data:

| Measure | Description |
|---|---|
| **Transport encryption** | All connections are encrypted with TLS (HTTPS) |
| **Secure cookies** | Session cookies are marked HttpOnly, Secure, and SameSite=Lax |
| **CSRF protection** | On all state-changing operations |
| **Security headers** | Content Security Policy (CSP), HSTS, X-Frame-Options, X-Content-Type-Options |
| **Rate limiting** | On authentication and API endpoints |
| **Input validation** | Server-side validation and output encoding |
| **Secret encryption** | Database credentials and API tokens are encrypted at rest |
| **Security scanning** | Regular security scanning and dependency updates |
| **Restricted access** | Access to production infrastructure is restricted to authorized personnel |

{{< alert type="warning" >}}
**No system is 100% secure.** Despite these measures, no system is completely secure. If you discover a vulnerability, please report it to [mykyta.olym.work@gmail.com](mailto:mykyta.olym.work@gmail.com).
{{< /alert >}}
---

## Data Retention

GitPulse retains your personal data only for as long as necessary to fulfill the purposes described in this Privacy Statement:

| Data Category | Retention Period |
|---|---|
| Account information | Until account deletion or 12 months after last sign-in |
| Course activity data | Duration of the academic course + 6 months for grade appeals |
| Assessment results | Duration of the academic course + 6 months |
| Server access logs | 90 days (rolling) |
| Session cookies | Until browser session ends or manual sign-out |

After the retention period, data is permanently deleted or anonymized. You may request early deletion at any time (see [Your Rights and Choices](#what-are-my-rights-and-choices)).

---

## Cookies and Similar Technologies

GitPulse uses only essential cookies necessary for the Service to function. We do not use any tracking, advertising, or third-party cookies.

| Cookie | Purpose | Type | Duration | Attributes |
|---|---|---|---|---|
| `gp_session` | Session authentication - keeps you signed in | Essential | Session | HttpOnly, Secure, SameSite=Lax |
| `gp_lang` | Language preference - remembers your chosen language | Functional | 365 days | SameSite=Lax |
| `gp_cookie_consent` | Records your cookie consent choice | Essential | 365 days | SameSite=Lax |

You can manage cookies through your browser settings. Disabling essential cookies may prevent the Service from functioning correctly.

---

## What Are My Rights and Choices?

Under the GDPR and applicable Slovak data protection law, you have the following rights. We provide these rights free of charge unless requests are manifestly unfounded or excessive.

| Right | Description |
|---|---|
| **Access** | Request a copy of the personal data GitPulse holds about you |
| **Rectification** | Request correction of inaccurate or incomplete data |
| **Erasure** | Request deletion of your personal data ("right to be forgotten") |
| **Restriction** | Request that we limit how we process your data |
| **Portability** | Receive your data in a structured, machine-readable format |
| **Objection** | Object to processing based on legitimate interest |
| **Withdraw Consent** | Withdraw consent at any time where processing is based on consent |

### How to Exercise Your Rights

1. **Contact your course instructor** - they can remove your enrollment and associated data
2. **Email us** at [mykyta.olym.work@gmail.com](mailto:mykyta.olym.work@gmail.com) with the subject line "Privacy Request"

We will respond to your request within 30 days. If we need additional time, we will notify you of the extension and the reason.

### Supervisory Authority

If you believe your data protection rights have been violated, you have the right to lodge a complaint with the relevant supervisory authority:

{{< alert type="note" >}}
**Office for Personal Data Protection of the Slovak Republic.** (Úrad na ochranu osobných údajov Slovenskej republiky)   Hraničná 12, 820 07 Bratislava 27   Phone: +421 2 3231 3214   Web: [dataprotection.gov.sk](https://dataprotection.gov.sk)
{{< /alert >}}
---

## Children's Privacy

GitPulse is designed for university-level students and is not directed at individuals under the age of 16. We do not knowingly collect personal data from children under 16. If we discover that we have inadvertently collected data from a child under 16, we will promptly delete that data.

---

## Statement Changes

We may update this Privacy Statement from time to time to reflect changes in our practices, the Service, or applicable law. When we make material changes, we will:

- Update the "Last updated" date at the top of this page
- Post a notice within the Service for significant changes
- Where required by law, seek your consent before applying changes

---

## Contact Us

Your information is controlled by the Department of Computers and Informatics (KPI), Faculty of Electrical Engineering and Informatics (FEI), Technical University of Kosice.

**Data Controller:**  
Department of Computers and Informatics (KPI)  
Faculty of Electrical Engineering and Informatics (FEI)  
Technical University of Kosice (TUKE)  
Letná 1/9, 042 00 Košice, Slovakia  
Email: [mykyta.olym.work@gmail.com](mailto:mykyta.olym.work@gmail.com)  
Web: [kpi.fei.tuke.sk](https://kpi.fei.tuke.sk)

When contacting us, please include "Privacy Request" or "Privacy Concern" in the subject line so we can route your inquiry appropriately.
