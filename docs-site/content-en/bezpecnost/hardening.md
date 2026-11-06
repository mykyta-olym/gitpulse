---
title: "Hardening"
description: "Safety recommendations for production"
---
{{< details >}}
- For: Operator
- Requires: Access to the deployment settings
{{< /details >}}
Security recommendations and checklist for production deployment of GitPulse.

## System hardening

### Operating system

```bash
# Ubuntu/Debian hardening

# 1. Aktualizácia systému
sudo apt update && sudo apt upgrade -y

# 2. Automatické security updates
sudo apt install unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades

# 3. Disable root SSH login
sudo sed -i 's/PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config
sudo systemctl restart sshd

# 4. SSH key-only auth
sudo sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config

# 5. Firewall
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS
sudo ufw enable

# 6. Fail2ban
sudo apt install fail2ban
sudo systemctl enable fail2ban
```

### Firewall rules

```bash
# /etc/ufw/applications.d/gitpulse
[GitPulse]
title=GitPulse
description=GitPulse web application
ports=80,443/tcp

# Aplikovať
sudo ufw app update GitPulse
sudo ufw allow GitPulse
```

## Docker hardening

### Dockerfile best practices

```dockerfile
# Dockerfile
# 1. Použiť slim base image
FROM python:3.12-slim AS base

# 2. Non-root user
RUN groupadd -r app && useradd -r -g app app

# 3. Minimálne závislosti
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# 4. Copy len potrebné súbory
COPY --chown=app:app requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=app:app src/ ./src/

# 5. Switch to non-root
USER app

# 6. Read-only filesystem (ak možné)
# V docker-compose: read_only: true

# 7. No new privileges
# V docker-compose: security_opt: ["no-new-privileges:true"]

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Docker Compose security

```yaml
# docker-compose.yml
services:
  api:
    image: gitpulse-api:latest
    read_only: true
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE  # Ak potrebné
    tmpfs:
      - /tmp
    user: "1000:1000"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
```

### Docker daemon

```json
// /etc/docker/daemon.json
{
  "icc": false,
  "userns-remap": "default",
  "no-new-privileges": true,
  "live-restore": true,
  "userland-proxy": false,
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
```

## Database hardening

### PostgreSQL

```sql
-- 1. Silné heslo
ALTER USER gitpulse PASSWORD 'VeryStrongPassword123!';

-- 2. Obmedzené oprávnenia pre aplikáciu
CREATE ROLE app_user WITH LOGIN PASSWORD 'AppPassword123!';
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_user;
REVOKE CREATE ON SCHEMA public FROM app_user;

-- 3. Read-only user pre reporting
CREATE ROLE report_user WITH LOGIN PASSWORD 'ReportPassword123!';
GRANT SELECT ON ALL TABLES IN SCHEMA public TO report_user;

-- 4. SSL povinné
ALTER SYSTEM SET ssl = 'on';
ALTER SYSTEM SET ssl_cert_file = '/etc/ssl/certs/server.crt';
ALTER SYSTEM SET ssl_key_file = '/etc/ssl/private/server.key';
```

```bash
# pg_hba.conf - len SSL spojenia
hostssl all all 0.0.0.0/0 scram-sha-256
```

### Redis

```bash
# redis.conf
# 1. Heslo
requirepass VeryStrongRedisPassword123!

# 2. Disable dangerous commands
rename-command FLUSHDB ""
rename-command FLUSHALL ""
rename-command DEBUG ""
rename-command CONFIG ""

# 3. Bind len na localhost
bind 127.0.0.1

# 4. TLS
tls-port 6379
port 0
tls-cert-file /etc/ssl/redis.crt
tls-key-file /etc/ssl/redis.key
```

## Application hardening

### Environment variables

```bash
# Nikdy v kóde!
# Správne
DATABASE_URL=${DATABASE_URL}

# Zle
DATABASE_URL="postgresql://user:password@host/db"
```

### Secrets management

```yaml
# docker-compose.yml s Docker secrets
services:
  api:
    secrets:
      - db_password
      - gitlab_token
      - secret_key
    environment:
      DATABASE_PASSWORD_FILE: /run/secrets/db_password
      GITLAB_TOKEN_FILE: /run/secrets/gitlab_token
      SECRET_KEY_FILE: /run/secrets/secret_key

secrets:
  db_password:
    file: ./secrets/db_password.txt
  gitlab_token:
    file: ./secrets/gitlab_token.txt
  secret_key:
    file: ./secrets/secret_key.txt
```

```python
# Načítanie secrets
import os
from pathlib import Path

def get_secret(name: str) -> str:
    """Load secret from file or environment."""
    file_path = os.environ.get(f"{name.upper()}_FILE")
    if file_path and Path(file_path).exists():
        return Path(file_path).read_text().strip()
    return os.environ.get(name.upper(), "")
```

### Security headers

```python
# src/app/middleware/security.py
SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
    "Content-Security-Policy": (
        "default-src 'self'; "
        "script-src 'self'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; "
        "font-src 'self'; "
        "frame-ancestors 'none'"
    ),
}
```

## TLS hardening

### Caddy configuration

```caddyfile
# Caddyfile

gitpulse.kpi.fei.tuke.sk 
    
    # Security headers
    header {
        Strict-Transport-Security "max-age=31536000; includeSubDomains; preload"
        X-Content-Type-Options "nosniff"
        X-Frame-Options "DENY"
        Referrer-Policy "strict-origin-when-cross-origin"
        -Server
    }
    
    # Rate limiting
    rate_limit {
        zone api {
            key {remote_host}
            events 100
            window 1m
        }
    }
    
    reverse_proxy api:8000
}
```

## Logging and monitoring

### Audit logging

```python
# Všetky security-relevantné udalosti
AUDIT_EVENTS = [
    "login_success",
    "login_failure",
    "logout",
    "password_change",
    "permission_denied",
    "resource_access",
    "admin_action",
    "api_key_created",
    "api_key_revoked",
]

async def log_security_event(
    event_type: str,
    user_id: str | None,
    details: dict,
    severity: str = "info"
):
    """Log security event."""
    logger.log(
        logging.INFO if severity == "info" else logging.WARNING,
        f"SECURITY_EVENT: {event_type}",
        extra={
            "event_type": event_type,
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat(),
            "details": details,
            "severity": severity,
        }
    )
```

### Security monitoring

```yaml
# Prometheus alerts
groups:
  - name: security
    rules:
      - alert: MultipleLoginFailures
        expr: rate(login_failures_total[5m]) > 10
        labels:
          severity: warning
        annotations:
          summary: "Multiple login failures detected"
      
      - alert: PermissionDenied
        expr: rate(permission_denied_total[5m]) > 5
        labels:
          severity: warning
        annotations:
          summary: "Multiple permission denied events"
      
      - alert: UnusualAdminActivity
        expr: rate(admin_actions_total[1h]) > 50
        labels:
          severity: warning
        annotations:
          summary: "Unusual admin activity"
```

## Security Checklist

### Pre-deployment

- [ ] All default passwords changed
- [ ] SECRET_KEY is unique and strong (min. 32 bytes)
- [ ] DEBUG=false in production
- [ ] HTTPS enforced (HSTS)
- [ ] Security headers configured
- [ ] Rate limiting active
- [ ] Input validation on all endpoints
- [ ] SQL injection protection (ORM/parameterized queries)
- [ ] XSS protection (CSP, output encoding)
- [ ] CSRF protection
- [ ] Audit logging active

### Infrastructure

- [ ] Firewall configured
- [ ] SSH hardened (key-only, no root)
- [ ] Automatic security updates
- [ ] Docker running as non-root
- [ ] Minimal container privileges
- [ ] Database SSL enabled
- [ ] Redis password protected
- [ ] Secrets are not in Git

### Operational

- [ ] Backups encrypted
- [ ] Log retention policy
- [ ] Incident response plan
- [ ] Security monitoring active
- [ ] Vulnerability scanning
- [ ] Penetration testing (annually)

## Vulnerability Management

### Dependency scanning

```bash
# Python dependencies
pip install -e ".[security]"
pip-audit

# Docker image scanning
docker scout cves gitpulse-api:latest

# Trivy scanner
trivy image gitpulse-api:latest
```

### Regular tasks

| Task | Frequency |
|-------|------------|
| Dependency updates | Weekly |
| Security patches | Immediately |
| Vulnerability scan | Weekly |
| Penetration test | Annually |
| Access review | Quarterly |
| Key rotation | Quarterly |

## Further reading

- [Security Model](model.md)
- [Threats and Mitigation](hrozby.md)
- [CIS Benchmarks] (https://www.cisecurity.org/cis-benchmarks)
- [OWASP ASVS](https://owasp.org/www-project-application-security-verification-standard/)

