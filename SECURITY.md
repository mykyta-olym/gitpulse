# Security Policy

## Supported Versions

GitPulse provides security updates for the current active release line:

| Version | Supported          |
| ------- | ------------------ |
| 2026.9.x | :white_check_mark: |
| < 2026.9 | :x:                |

---

## Reporting a Vulnerability

If you discover a security vulnerability in GitPulse, please report it responsibly:

1. **Do not create a public issue.**
2. Send an email to the maintainer: `mykyta.olym.work@gmail.com` or open a **Confidential Issue** directly on the TUKE GitLab repository (`gitlab.example.com`).
3. Include:
   - Description of the vulnerability
   - Steps to reproduce or proof-of-concept (PoC)
   - Potential impact and affected components

You will receive an initial response within 48 hours with an assessment and remediation plan.

---

## Built-in Security Architecture

- **HMAC Signature Verification**: All GitLab webhook payloads require valid `X-Gitlab-Token` header verification using constant-time `hmac.compare_digest`.
- **Secret Encryption**: Stored tokens and credentials use Fernet symmetric encryption.
- **Session Security**: Session cookies use `HttpOnly`, `SameSite=Lax`, and `Secure` attributes with strict idle (30 days) and absolute (90 days) TTLs.
- **CSRF Protection**: Double-submit cookie pattern applied to all mutation requests.
- **Privacy & GDPR Compliance**: Educational records and student metrics are protected by role-based access control (RBAC). All student handles are redacted before submission to third-party LLM providers.
