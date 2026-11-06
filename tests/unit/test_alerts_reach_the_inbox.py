"""An alert has to arrive somewhere a person reads.

Until 2026-10-21 Alertmanager mailed ops@example.com through localhost:25:
64 221 delivery errors in six days on production, and not one alert received.
Then, pointed at the application's Gmail account, it was refused with a bare
``535 Username and Password not accepted`` - the password as Google shows it,
in groups of four, which config.py already strips for the application.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

REPO = Path(__file__).resolve().parents[2]


def _alertmanager() -> tuple[dict[str, Any], str]:
    compose = yaml.safe_load((REPO / "docker-compose.yml").read_text(encoding="utf-8"))
    config = (REPO / "monitoring/alertmanager.yml").read_text(encoding="utf-8")
    return compose, config


def test_no_receiver_is_a_placeholder_address() -> None:
    _, config = _alertmanager()
    assert "example.com" not in config
    assert "localhost:25" not in config
    for receiver in yaml.safe_load(config)["receivers"]:
        for email in receiver["email_configs"]:
            assert email["to"] == "@ALERT_EMAIL_TO@", receiver["name"]


def test_every_placeholder_is_filled_from_the_environment() -> None:
    compose, config = _alertmanager()
    service = compose["services"]["alertmanager"]
    command = " ".join(service["command"])
    placeholders = set(re.findall(r"@([A-Z_]+)@", config)) - {"NAME"}
    assert placeholders, "the config no longer reads anything from the environment"
    for name in placeholders:
        assert f"s|@{name}@|$${name}|g" in command, name
        assert name in service["environment"], name


def test_the_password_is_a_secret_read_without_its_spaces() -> None:
    compose, config = _alertmanager()
    assert compose["secrets"]["smtp_password"] == {"environment": "SMTP_PASSWORD"}
    service = compose["services"]["alertmanager"]
    assert "smtp_password" in service["secrets"]
    assert "SMTP_PASSWORD" not in service["environment"], "the secret, not the variable"
    command = " ".join(service["command"])
    stripped = "/tmp/smtp_password"  # noqa: S108 - a path inside the container
    assert f'tr -d "[:space:]" < /run/secrets/smtp_password > {stripped}' in command
    assert yaml.safe_load(config)["global"]["smtp_auth_password_file"] == stripped


# The first email that did arrive was Alertmanager's default one: raw labels,
# "View in Alertmanager" to http://alertmanager:9093 and a "Source" link to the
# Prometheus container - neither opens from a mailbox.

_TEMPLATE = REPO / "monitoring/alertmanager-templates/gitpulse.tmpl"


def test_every_receiver_sends_the_gitpulse_email() -> None:
    compose, config = _alertmanager()
    parsed = yaml.safe_load(config)
    assert parsed["templates"] == ["/etc/alertmanager/templates/*.tmpl"]
    mounts = compose["services"]["alertmanager"]["volumes"]
    assert "./monitoring/alertmanager-templates:/etc/alertmanager/templates:ro" in mounts
    template = _TEMPLATE.read_text(encoding="utf-8")
    for receiver in parsed["receivers"]:
        for email in receiver["email_configs"]:
            for part, name in (
                (email["html"], "gitpulse.email.html"),
                (email["text"], "gitpulse.email.text"),
                (email["headers"]["Subject"], "gitpulse.email.subject"),
            ):
                assert f'template "{name}"' in part, receiver["name"]
                assert re.search(rf'\{{\{{ define "{re.escape(name)}" -?\}}\}}', template), name


def test_the_links_in_an_alert_open_from_a_mailbox() -> None:
    compose, _ = _alertmanager()
    services = compose["services"]
    prometheus = " ".join(services["prometheus"]["command"])
    alertmanager = " ".join(services["alertmanager"]["command"])
    # An alert's "Query" link is Prometheus' external URL; the "Silence" link
    # and the template's base are Alertmanager's.
    assert "--web.external-url=${APP_BASE_URL}/prometheus/" in prometheus
    assert "--web.external-url=${APP_BASE_URL}/alertmanager/" in alertmanager
    # Caddy serves it there, for an administrator's session (see
    # test_monitoring_opens_for_admins.py), and can reach it.
    caddy = (REPO / "Caddyfile").read_text(encoding="utf-8")
    block = caddy[caddy.index("handle_path /alertmanager/*") :]
    block = block[: block.index("\n    }\n")]
    assert "uri /internal/monitoring-authz?service=alertmanager" in block
    assert "reverse_proxy alertmanager:9093" in block
    assert set(services["caddy"]["networks"]) & set(services["alertmanager"]["networks"])


def test_the_email_s_images_are_served_by_the_app() -> None:
    template = _TEMPLATE.read_text(encoding="utf-8")
    images = set(re.findall(r"\$base \}\}(/static/[\w/.-]+\.png)", template))
    assert images >= {"/static/img/mail/x.png", "/static/img/mail/check.png"}
    for path in images:
        assert (REPO / "src/app/templates" / path.lstrip("/")).is_file(), path


def test_alert_times_are_the_department_s() -> None:
    compose, _ = _alertmanager()
    assert compose["services"]["alertmanager"]["environment"]["TZ"] == "Europe/Bratislava"
    assert ".Local.Format" in _TEMPLATE.read_text(encoding="utf-8")
