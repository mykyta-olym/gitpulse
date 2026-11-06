import json
from pathlib import Path


def create_row(title, y, id_val):
    return {
        "title": title,
        "type": "row",
        "collapsed": False,
        "gridPos": {"h": 1, "w": 24, "x": 0, "y": y},
        "id": id_val,
        "panels": [],
    }


def apply_timeseries_style(panel):
    # Set default styling for modern premium look
    if "fieldConfig" not in panel:
        panel["fieldConfig"] = {}
    if "defaults" not in panel["fieldConfig"]:
        panel["fieldConfig"]["defaults"] = {}

    panel["fieldConfig"]["defaults"]["custom"] = {
        "drawStyle": "line",
        "lineInterpolation": "smooth",
        "gradientMode": "opacity",
        "fillOpacity": 12,
        "lineWidth": 2,
        "showPoints": "never",
    }
    return panel


def main():
    dashboard_path = Path("monitoring/grafana/dashboards/gitpulse.json")

    # Let's rebuild the panels array with rows and beautiful styling
    panels = []
    id_counter = 1

    # ── Row 1: SYSTEM OVERVIEW ──
    panels.append(create_row("🖥️ System Overview & Health", 0, id_counter))
    id_counter += 1

    # Service Health
    panels.append(
        {
            "title": "Service Health Status",
            "type": "stat",
            "gridPos": {"h": 4, "w": 24, "x": 0, "y": 1},
            "id": id_counter,
            "datasource": {"type": "prometheus", "uid": "prometheus"},
            "fieldConfig": {
                "defaults": {
                    "mappings": [
                        {
                            "options": {
                                "0": {"color": "red", "text": "DOWN"},
                                "1": {"color": "green", "text": "UP"},
                            },
                            "type": "value",
                        }
                    ],
                    "thresholds": {
                        "steps": [{"color": "red", "value": None}, {"color": "green", "value": 1}]
                    },
                }
            },
            "options": {
                "graphMode": "none",
                "textMode": "value",
                "colorMode": "background",
                "justifyMode": "center",
            },
            "targets": [
                {"expr": 'up{job="gitpulse-api"}', "legendFormat": "API Server"},
                {"expr": 'up{job="prometheus"}', "legendFormat": "Prometheus"},
                {"expr": 'up{job="grafana"}', "legendFormat": "Grafana"},
                {"expr": 'up{job="jaeger"}', "legendFormat": "Jaeger Tracing"},
            ],
        }
    )
    id_counter += 1

    # Active Workers
    panels.append(
        {
            "title": "Active Workers",
            "type": "stat",
            "gridPos": {"h": 4, "w": 8, "x": 0, "y": 5},
            "id": id_counter,
            "datasource": {"type": "prometheus", "uid": "prometheus"},
            "fieldConfig": {
                "defaults": {
                    "thresholds": {
                        "steps": [{"color": "red", "value": None}, {"color": "green", "value": 1}]
                    }
                }
            },
            "options": {"graphMode": "area", "textMode": "value", "colorMode": "value"},
            "targets": [{"expr": "rq_workers_active", "legendFormat": "Workers online"}],
        }
    )
    id_counter += 1

    # RQ Failed Jobs
    panels.append(
        {
            "title": "Failed Jobs Count",
            "type": "stat",
            "gridPos": {"h": 4, "w": 8, "x": 8, "y": 5},
            "id": id_counter,
            "datasource": {"type": "prometheus", "uid": "prometheus"},
            "fieldConfig": {
                "defaults": {
                    "unit": "short",
                    "thresholds": {
                        "steps": [
                            {"color": "green", "value": None},
                            {"color": "yellow", "value": 1},
                            {"color": "red", "value": 5},
                        ]
                    },
                }
            },
            "options": {"graphMode": "area", "textMode": "value", "colorMode": "value"},
            "targets": [{"expr": "rq_failed_jobs_total", "legendFormat": "Failed"}],
        }
    )
    id_counter += 1

    # Uptime
    panels.append(
        {
            "title": "API Uptime",
            "type": "stat",
            "gridPos": {"h": 4, "w": 8, "x": 16, "y": 5},
            "id": id_counter,
            "datasource": {"type": "prometheus", "uid": "prometheus"},
            "fieldConfig": {
                "defaults": {
                    "unit": "s",
                    "thresholds": {
                        "steps": [
                            {"color": "yellow", "value": None},
                            {"color": "green", "value": 3600},
                        ]
                    },
                }
            },
            "options": {"graphMode": "none", "textMode": "value", "colorMode": "value"},
            "targets": [
                {
                    "expr": 'time() - process_start_time_seconds{job="gitpulse-api"}',
                    "legendFormat": "API uptime",
                }
            ],
        }
    )
    id_counter += 1

    # ── Row 2: WEBHOOK PIPELINE ──
    panels.append(create_row("⚡ Webhook Processing Pipeline", 9, id_counter))
    id_counter += 1

    # Webhook Rate
    panels.append(
        apply_timeseries_style(
            {
                "title": "Webhook Traffic (received / processed)",
                "type": "timeseries",
                "gridPos": {"h": 8, "w": 12, "x": 0, "y": 10},
                "id": id_counter,
                "datasource": {"type": "prometheus", "uid": "prometheus"},
                "fieldConfig": {"defaults": {"unit": "reqps"}},
                "targets": [
                    {
                        "expr": "rate(webhook_events_received_total[1m])",
                        "legendFormat": "Received: {{event_type}}",
                    },
                    {
                        "expr": "rate(webhook_events_processed_total[1m])",
                        "legendFormat": "Processed: {{event_type}} ({{status}})",
                    },
                ],
            }
        )
    )
    id_counter += 1

    # Processing Latency
    panels.append(
        apply_timeseries_style(
            {
                "title": "Webhook Processing Latency (p50 / p95 / p99)",
                "type": "timeseries",
                "gridPos": {"h": 8, "w": 12, "x": 12, "y": 10},
                "id": id_counter,
                "datasource": {"type": "prometheus", "uid": "prometheus"},
                "fieldConfig": {"defaults": {"unit": "s"}},
                "targets": [
                    {
                        "expr": "histogram_quantile(0.50, rate(webhook_processing_duration_seconds_bucket[5m]))",
                        "legendFormat": "p50: {{event_type}}",
                    },
                    {
                        "expr": "histogram_quantile(0.95, rate(webhook_processing_duration_seconds_bucket[5m]))",
                        "legendFormat": "p95: {{event_type}}",
                    },
                    {
                        "expr": "histogram_quantile(0.99, rate(webhook_processing_duration_seconds_bucket[5m]))",
                        "legendFormat": "p99: {{event_type}}",
                    },
                ],
            }
        )
    )
    id_counter += 1

    # Queue Depth
    panels.append(
        apply_timeseries_style(
            {
                "title": "Background Job Queue Depths",
                "type": "timeseries",
                "gridPos": {"h": 8, "w": 12, "x": 0, "y": 18},
                "id": id_counter,
                "datasource": {"type": "prometheus", "uid": "prometheus"},
                "fieldConfig": {"defaults": {"unit": "short"}},
                "targets": [{"expr": "rq_queue_depth", "legendFormat": "Queue: {{queue_name}}"}],
            }
        )
    )
    id_counter += 1

    # Job success/failure rate
    panels.append(
        apply_timeseries_style(
            {
                "title": "Processing Outcome Success Rate",
                "type": "timeseries",
                "gridPos": {"h": 8, "w": 12, "x": 12, "y": 18},
                "id": id_counter,
                "datasource": {"type": "prometheus", "uid": "prometheus"},
                "fieldConfig": {"defaults": {"unit": "reqps"}},
                "targets": [
                    {
                        "expr": 'rate(webhook_events_processed_total{status="ok"}[5m])',
                        "legendFormat": "Webhook success",
                    },
                    {
                        "expr": 'rate(webhook_events_processed_total{status="error"}[5m])',
                        "legendFormat": "Webhook failure",
                    },
                    {
                        "expr": 'rate(metrics_compute_total{status="ok"}[5m])',
                        "legendFormat": "Metrics recompute success",
                    },
                    {
                        "expr": 'rate(metrics_compute_total{status="error"}[5m])',
                        "legendFormat": "Metrics recompute failure",
                    },
                ],
            }
        )
    )
    id_counter += 1

    # ── Row 3: APPLICATION HTTP TRAFFIC ──
    panels.append(create_row("🌐 HTTP Web Traffic & Performance", 26, id_counter))
    id_counter += 1

    # HTTP Rate by Status
    panels.append(
        apply_timeseries_style(
            {
                "title": "HTTP Requests per Second (by status)",
                "type": "timeseries",
                "gridPos": {"h": 8, "w": 12, "x": 0, "y": 27},
                "id": id_counter,
                "datasource": {"type": "prometheus", "uid": "prometheus"},
                "fieldConfig": {"defaults": {"unit": "reqps"}},
                "targets": [
                    {
                        "expr": "sum by (status) (rate(http_requests_total[5m]))",
                        "legendFormat": "HTTP {{status}}",
                    }
                ],
            }
        )
    )
    id_counter += 1

    # HTTP Latency
    panels.append(
        apply_timeseries_style(
            {
                "title": "HTTP Latency (p50 / p95 / p99)",
                "type": "timeseries",
                "gridPos": {"h": 8, "w": 12, "x": 12, "y": 27},
                "id": id_counter,
                "datasource": {"type": "prometheus", "uid": "prometheus"},
                "fieldConfig": {"defaults": {"unit": "s"}},
                "targets": [
                    {
                        "expr": "histogram_quantile(0.50, sum by (le) (rate(http_request_duration_seconds_bucket[5m])))",
                        "legendFormat": "p50 (median)",
                    },
                    {
                        "expr": "histogram_quantile(0.95, sum by (le) (rate(http_request_duration_seconds_bucket[5m])))",
                        "legendFormat": "p95 (slowest 5%)",
                    },
                    {
                        "expr": "histogram_quantile(0.99, sum by (le) (rate(http_request_duration_seconds_bucket[5m])))",
                        "legendFormat": "p99 (slowest 1%)",
                    },
                ],
            }
        )
    )
    id_counter += 1

    # ── Row 4: COMPUTATION & ENRICHMENT ──
    panels.append(create_row("📊 Evaluation Metrics & GitLab Sync", 35, id_counter))
    id_counter += 1

    # Metrics Compute Duration
    panels.append(
        apply_timeseries_style(
            {
                "title": "Metrics Compute Duration",
                "type": "timeseries",
                "gridPos": {"h": 8, "w": 12, "x": 0, "y": 36},
                "id": id_counter,
                "datasource": {"type": "prometheus", "uid": "prometheus"},
                "fieldConfig": {"defaults": {"unit": "s"}},
                "targets": [
                    {
                        "expr": "histogram_quantile(0.95, rate(metrics_compute_duration_seconds_bucket[5m]))",
                        "legendFormat": "p95 duration",
                    },
                    {
                        "expr": "histogram_quantile(0.50, rate(metrics_compute_duration_seconds_bucket[5m]))",
                        "legendFormat": "p50 duration",
                    },
                ],
            }
        )
    )
    id_counter += 1

    # Enrichment Jobs
    panels.append(
        apply_timeseries_style(
            {
                "title": "GitLab Enrichment API Jobs",
                "type": "timeseries",
                "gridPos": {"h": 8, "w": 12, "x": 12, "y": 36},
                "id": id_counter,
                "datasource": {"type": "prometheus", "uid": "prometheus"},
                "fieldConfig": {"defaults": {"unit": "reqps"}},
                "targets": [
                    {
                        "expr": 'rate(enrichment_jobs_total{status="ok"}[5m])',
                        "legendFormat": "Enrich success: {{entity_type}}",
                    },
                    {
                        "expr": 'rate(enrichment_jobs_total{status="error"}[5m])',
                        "legendFormat": "Enrich failure: {{entity_type}}",
                    },
                ],
            }
        )
    )
    id_counter += 1

    # Enrichment Duration
    panels.append(
        apply_timeseries_style(
            {
                "title": "GitLab Enrichment Duration (p95)",
                "type": "timeseries",
                "gridPos": {"h": 8, "w": 24, "x": 0, "y": 44},
                "id": id_counter,
                "datasource": {"type": "prometheus", "uid": "prometheus"},
                "fieldConfig": {"defaults": {"unit": "s"}},
                "targets": [
                    {
                        "expr": "histogram_quantile(0.95, rate(enrichment_duration_seconds_bucket[5m]))",
                        "legendFormat": "p95: {{entity_type}}",
                    }
                ],
            }
        )
    )
    id_counter += 1

    # ── Row 5: INTEGRATIONS & RESOURCE POOLS ──
    panels.append(create_row("🔌 Database Pools & Internal Integration API", 52, id_counter))
    id_counter += 1

    # DB Pool Utilization
    panels.append(
        {
            "title": "Postgres Connection Pool Utilization",
            "type": "gauge",
            "gridPos": {"h": 8, "w": 8, "x": 0, "y": 53},
            "id": id_counter,
            "datasource": {"type": "prometheus", "uid": "prometheus"},
            "fieldConfig": {
                "defaults": {
                    "unit": "short",
                    "thresholds": {
                        "steps": [
                            {"color": "green", "value": None},
                            {"color": "yellow", "value": 15},
                            {"color": "red", "value": 19},
                        ]
                    },
                    "max": 20,
                }
            },
            "targets": [
                {"expr": "db_pool_checked_out", "legendFormat": "Active Connections (Checked Out)"}
            ],
        }
    )
    id_counter += 1

    # DB Connection Pool Detail
    panels.append(
        apply_timeseries_style(
            {
                "title": "Database Connection Pool Allocation Detail",
                "type": "timeseries",
                "gridPos": {"h": 8, "w": 16, "x": 8, "y": 53},
                "id": id_counter,
                "datasource": {"type": "prometheus", "uid": "prometheus"},
                "fieldConfig": {"defaults": {"unit": "short"}},
                "targets": [
                    {"expr": "db_pool_size", "legendFormat": "Pool Size Limit"},
                    {"expr": "db_pool_checked_out", "legendFormat": "Checked Out (Active)"},
                    {"expr": "db_pool_checked_in", "legendFormat": "Checked In (Idle)"},
                    {"expr": "db_pool_overflow", "legendFormat": "Overflow Count"},
                ],
            }
        )
    )
    id_counter += 1

    # GitLab API Latency
    panels.append(
        apply_timeseries_style(
            {
                "title": "GitLab API Latency (p50 / p95)",
                "type": "timeseries",
                "gridPos": {"h": 8, "w": 12, "x": 0, "y": 61},
                "id": id_counter,
                "datasource": {"type": "prometheus", "uid": "prometheus"},
                "fieldConfig": {"defaults": {"unit": "s"}},
                "targets": [
                    {
                        "expr": "histogram_quantile(0.95, rate(gitlab_api_duration_seconds_bucket[5m]))",
                        "legendFormat": "p95: {{endpoint}}",
                    },
                    {
                        "expr": "histogram_quantile(0.50, rate(gitlab_api_duration_seconds_bucket[5m]))",
                        "legendFormat": "p50: {{endpoint}}",
                    },
                ],
            }
        )
    )
    id_counter += 1

    # GitLab API Call Rate
    panels.append(
        apply_timeseries_style(
            {
                "title": "GitLab API Call Rate",
                "type": "timeseries",
                "gridPos": {"h": 8, "w": 12, "x": 12, "y": 61},
                "id": id_counter,
                "datasource": {"type": "prometheus", "uid": "prometheus"},
                "fieldConfig": {"defaults": {"unit": "reqps"}},
                "targets": [
                    {
                        "expr": "sum by (endpoint, status) (rate(gitlab_api_requests_total[5m]))",
                        "legendFormat": "API: {{endpoint}} ({{status}})",
                    }
                ],
            }
        )
    )
    id_counter += 1

    # Prometheus Scrape Duration
    panels.append(
        apply_timeseries_style(
            {
                "title": "Prometheus Scraper Performance (scrape duration)",
                "type": "timeseries",
                "gridPos": {"h": 8, "w": 24, "x": 0, "y": 69},
                "id": id_counter,
                "datasource": {"type": "prometheus", "uid": "prometheus"},
                "fieldConfig": {"defaults": {"unit": "s"}},
                "targets": [
                    {"expr": "scrape_duration_seconds", "legendFormat": "Scrape target: {{job}}"}
                ],
            }
        )
    )

    # Build complete dashboard structure
    dashboard_data = {
        "annotations": {"list": []},
        "editable": True,
        "fiscalYearStartMonth": 0,
        "graphTooltip": 1,
        "id": None,
        "links": [],
        "panels": panels,
        "schemaVersion": 39,
        "tags": ["gitpulse"],
        "templating": {"list": []},
        "time": {"from": "now-1h", "to": "now"},
        "timepicker": {},
        "timezone": "browser",
        "title": "GitPulse Overview",
        "uid": "gitpulse-overview",
        "version": 4,
    }

    with open(dashboard_path, "w", encoding="utf-8") as f:
        json.dump(dashboard_data, f, indent=2, ensure_ascii=False)
    print(
        "Successfully generated premium Grafana dashboard with rows, gradients, and smooth line curves!"
    )


if __name__ == "__main__":
    main()
