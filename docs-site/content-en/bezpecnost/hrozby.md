---
title: "Threat model"
description: "Threat model and mitigations for GitPulse"
---
{{< details >}}
- For: Operator
- Requires: Access to the deployment settings
{{< /details >}}
## STRIDE overview

| Category | Risk | Mitigation |
|---|---|---|
| Spoofing | forged webhook | `X-Gitlab-Token` + bcrypt verification |
| Tampering | manipulated session/tokens | signed cookies, constant-time comparisons |
| Repudiation | insufficient auditability | structured logs + correlation IDs |
| Information disclosure | sensitive data leak | security headers, limited endpoint exposure |
| DoS | webhook/API flooding | rate limiting + queue backpressure controls |
| Elevation of privilege | unauthorized admin access | RBAC dependency checks |

## Critical flows

```mermaid
sequenceDiagram
    participant A as Attacker
    participant API as API
    participant SEC as Security checks

    A->>API: POST webhook without valid token
    API->>SEC: verify X-Gitlab-Token
    SEC-->>API: reject
    API-->>A: 401/403
```

## Risks to monitor

1. repeated 401/403 attempts on sensitive endpoints
2. sudden rise in `rq_queue_depth`
3. elevated `5xx` and webhook processing error rates
4. long-running worker failure alerts

## Minimum incident response

1. identify impacted endpoints and time window
2. correlate metrics + logs + traces via `correlation_id`
3. if credentials leak is suspected, rotate tokens immediately
4. restore service and document postmortem
