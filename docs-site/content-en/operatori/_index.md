---
title: "Operator Guide"
nav_title: "Operations"
description: "Guide for deploying and operating GitPulse"
---
{{< details >}}
- For: Operator
- Requires: Server and deployment access
{{< /details >}}
This section is intended for administrators and DevOps engineers responsible for deploying and operating GitPulse.

## Overview

```mermaid
graph TB
    subgraph "Infrastructure"
        LB["Load Balancer / Caddy"]
        API["GitPulse API<br />FastAPI"]
        WORKER["Background Workers<br />RQ"]
        DB[("PostgreSQL")]
        REDIS[("Redis")]
        PROM["Prometheus"]
        GRAF["Grafana"]
    end
    
    LB --> API
    API --> DB
    API --> REDIS
    WORKER --> DB
    WORKER --> REDIS
    PROM --> API
    GRAF --> PROM
```

## What You'll Find in This Section

  - [Deployment](./nasadenie/) - Installation and configuration on a production server
  - [Updates](./aktualizacie/) - Process for updating to a new version
  - [Backup](./zalohovanie/) - Backup and recovery strategy
  - [Monitoring](./monitoring/) - Prometheus, Grafana, alerting
  - [Troubleshooting](./troubleshooting/) - Solving common problems

## Minimum Requirements

### Hardware

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| CPU | 2 cores | 4 cores |
| RAM | 4 GB | 8 GB |
| Disk | 20 GB SSD | 50 GB SSD |
| Network | 100 Mbps | 1 Gbps |

### Software

| Component | Version |
|-----------|---------|
| Docker | 24.0+ |
| Docker Compose | 2.20+ |
| PostgreSQL | 16+ |
| Redis | 7+ |

### Network Requirements

| Port | Service | Access |
|------|---------|--------|
| 443 | HTTPS (Caddy) | Public |
| 80 | HTTP redirect | Public |
| 5432 | PostgreSQL | Internal |
| 6379 | Redis | Internal |
| 8000 | API (internal) | Internal |
| 9090 | Prometheus | Internal |
| 3000 | Grafana | Internal/VPN |

## Deployment Architecture

### Simple Deployment (1 server)

```mermaid
graph TB
    subgraph "Server"
        CADDY["Caddy<br />:443"]
        subgraph "Docker"
            API["GitPulse API<br />:8000"]
            WORKER["Worker"]
            PG[("PostgreSQL")]
            RED[("Redis")]
        end
    end
    
    INET["Internet"] --> CADDY
    CADDY --> API
    API --> PG
    API --> RED
    WORKER --> PG
    WORKER --> RED
```

### Scalable Deployment

```mermaid
graph TB
    subgraph "Load Balancer"
        LB["HAProxy / Nginx"]
    end
    
    subgraph "App Tier"
        API1["API Instance 1"]
        API2["API Instance 2"]
        WORKER1["Worker 1"]
        WORKER2["Worker 2"]
    end
    
    subgraph "Data Tier"
        PG[("PostgreSQL<br />Primary")]
        PG_REP[("PostgreSQL<br />Replica")]
        RED[("Redis Cluster")]
    end
    
    LB --> API1
    LB --> API2
    API1 --> PG
    API2 --> PG
    API1 --> RED
    API2 --> RED
    WORKER1 --> PG
    WORKER2 --> PG
    PG --> PG_REP
```

## Quick Start

### 1. Server Preparation

```bash
# System update
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo apt install docker-compose-plugin
```

### 2. Clone the Repository

```bash
git clone https://gitlab.example.com/kpi-zp/2027/dp.mykyta.olym/workspace/workspace.git gitpulse
cd gitpulse
```

### 3. Configuration

```bash
# Copy template
cp .env.example .env

# Edit configuration
nano .env
```

### 4. Start

```bash
docker compose up -d
```

### 5. Verification

```bash
# Health check
curl http://localhost:8000/health

# Logs
docker compose logs -f
```

## Next Steps

1. [Detailed Deployment](nasadenie.md) - Complete guide
2. [TLS Configuration](nasadenie.md) - HTTPS setup
3. [GitLab Integration](../gitlab/tokeny.md) - Connecting to GitLab
4. [Monitoring](monitoring.md) - Setting up alerts
