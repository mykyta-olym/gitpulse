"""Release failures must stop before they can be reported as success."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import tomllib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SHA = "a" * 40


@pytest.fixture
def deploy(monkeypatch):
    spec = importlib.util.spec_from_file_location("redeploy_under_test", ROOT / "redeploy.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    version = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"][
        "version"
    ]
    calls = []

    def remote(_ssh, command, timeout=900):
        calls.append(command)
        if "df --output=avail" in command:
            return "200G\n", ""
        if "alembic current" in command or "alembic heads" in command:
            return "022 (head)\n", ""
        if "get_settings().app_version" in command:
            return json.dumps({"sha": SHA, "version": version}), ""
        return "", ""

    monkeypatch.setattr(module, "build_ssh_command", lambda: ["ssh", "test-host"])
    monkeypatch.setattr(module.shutil, "which", lambda executable: "/usr/bin/git")
    monkeypatch.setattr(module.subprocess, "check_output", lambda *args, **kwargs: SHA)
    monkeypatch.setattr(module.sys, "argv", ["redeploy.py"])
    monkeypatch.setattr(module, "run_cmd", remote)
    return module, calls, remote


@pytest.mark.parametrize("status", [1, 22])
def test_failed_remote_commands_are_not_swallowed(monkeypatch, deploy, status):
    module, _, _ = deploy
    commands = []

    def execute(args, **kwargs):
        commands.append(args)
        return subprocess.CompletedProcess(args, status, b"", b"remote failure")

    monkeypatch.setattr(module.subprocess, "run", execute)
    # Exercise the real runner, rather than the main() fixture's stub.
    runner = importlib.util.spec_from_file_location("redeploy_runner", ROOT / "redeploy.py")
    actual = importlib.util.module_from_spec(runner)
    runner.loader.exec_module(actual)
    with pytest.raises(SystemExit) as error:
        actual.run_cmd(["ssh", "test-host"], "false | true")
    assert error.value.code == status
    assert commands[0][-3:] == ["bash", "-seuo", "pipefail"]


def test_checkout_changes_are_preserved_and_pull_is_fast_forward_only(deploy):
    module, calls, _ = deploy
    module.main()
    assert "git status --porcelain --untracked-files=no" in calls[0]
    assert "exit 1" in calls[0]
    assert any("git pull --ff-only origin main" in command and SHA in command for command in calls)
    assert not any("git stash" in command for command in calls)


def test_failed_documentation_build_keeps_the_current_container(monkeypatch, deploy):
    module, calls, remote = deploy

    def fail_build(ssh, command, timeout=900):
        result = remote(ssh, command, timeout)
        if "build gitpulse-docs" in command:
            raise SystemExit(1)
        return result

    monkeypatch.setattr(module, "run_cmd", fail_build)
    with pytest.raises(SystemExit):
        module.main()
    assert not any("docker rm -f" in command for command in calls)
    assert not any("stop -t 180 worker" in command for command in calls)


def test_migrations_finish_before_the_serving_api_is_replaced(deploy):
    module, calls, _ = deploy
    module.main()
    migrate = next(i for i, command in enumerate(calls) if "alembic upgrade head" in command)
    restart = next(i for i, command in enumerate(calls) if "up -d --remove-orphans api" in command)
    assert migrate < restart
    assert "run --rm --no-deps api" in calls[migrate]


@pytest.mark.parametrize("field", ["sha", "version"])
def test_an_old_running_release_cannot_pass_verification(monkeypatch, deploy, field):
    module, calls, remote = deploy

    def old_release(ssh, command, timeout=900):
        output, error = remote(ssh, command, timeout)
        if "get_settings().app_version" in command:
            state = json.loads(output)
            state[field] = "old-release"
            return json.dumps(state), error
        return output, error

    monkeypatch.setattr(module, "run_cmd", old_release)
    with pytest.raises(SystemExit, match="Running release does not match"):
        module.main()
    assert not any("curl " in command for command in calls)


def test_a_failed_readiness_check_does_not_complete_the_release(monkeypatch, deploy, capsys):
    module, calls, remote = deploy

    def failed_health(ssh, command, timeout=900):
        result = remote(ssh, command, timeout)
        if command.startswith("curl "):
            raise SystemExit(22)
        return result

    monkeypatch.setattr(module, "run_cmd", failed_health)
    with pytest.raises(SystemExit):
        module.main()
    health = calls[-1]
    assert "--fail" in health
    assert "--retry-connrefused" in health
    assert "--max-time" in health
    assert "=== DONE ===" not in capsys.readouterr().out


def _pulling(remote, changed):
    """The fixture's host, with a checkout that was one commit behind."""

    def host(ssh, command, timeout=900):
        answer = remote(ssh, command, timeout)  # records the call
        if command.endswith("git rev-parse HEAD"):
            return "b" * 40 + "\n", ""
        if "git diff --name-only" in command:
            return "".join(f"{path}\n" for path in changed), ""
        return answer

    return host


def test_the_pulled_caddyfile_is_the_one_caddy_reloads(deploy):
    """A file mounted on its own keeps the inode it had when the container
    started; the pull writes a changed Caddyfile as a new file, so reloading
    /etc/caddy/Caddyfile re-read the old text. The reload reads the checkout."""
    module, calls, _ = deploy
    module.main()
    reload = next(command for command in calls if "caddy reload" in command)
    assert "--config /dev/stdin" in reload
    assert reload.endswith("< Caddyfile")


def test_running_proxy_loads_recovery_settings_before_api_replacement(monkeypatch, deploy):
    module, calls, remote = deploy

    def running_proxy(ssh, command, timeout=900):
        answer = remote(ssh, command, timeout)
        if "ps --status running -q caddy" in command:
            return "Welcome to the host\n" + "c" * 64 + "\n", ""
        return answer

    monkeypatch.setattr(module, "run_cmd", running_proxy)
    module.main()
    replacement = next(
        i for i, command in enumerate(calls) if "up -d --remove-orphans api worker" in command
    )
    reload = next(i for i, command in enumerate(calls) if "caddy reload" in command)
    assert reload < replacement


def test_failed_proxy_reload_keeps_the_serving_api(monkeypatch, deploy):
    module, calls, remote = deploy

    def failed_reload(ssh, command, timeout=900):
        answer = remote(ssh, command, timeout)
        if "ps --status running -q caddy" in command:
            return "c" * 64 + "\n", ""
        if "caddy reload" in command:
            raise SystemExit(1)
        return answer

    monkeypatch.setattr(module, "run_cmd", failed_reload)
    with pytest.raises(SystemExit):
        module.main()
    assert not any("up -d --remove-orphans api worker" in command for command in calls)


@pytest.mark.parametrize("output", ["", "Welcome to the host\n"])
def test_first_deployment_does_not_treat_a_banner_as_a_running_proxy(monkeypatch, deploy, output):
    module, calls, remote = deploy

    def absent_proxy(ssh, command, timeout=900):
        answer = remote(ssh, command, timeout)
        if "ps --status running -q caddy" in command:
            return output, ""
        return answer

    monkeypatch.setattr(module, "run_cmd", absent_proxy)
    module.main()
    replacement = next(
        i for i, command in enumerate(calls) if "up -d --remove-orphans api worker" in command
    )
    reload = next(i for i, command in enumerate(calls) if "caddy reload" in command)
    assert replacement < reload


def test_a_changed_alert_rule_restarts_prometheus(monkeypatch, deploy):
    module, calls, remote = deploy
    monkeypatch.setattr(
        module, "run_cmd", _pulling(remote, ["monitoring/prometheus/alerts.yml", "src/app/x.py"])
    )
    module.main()
    previous = "b" * 40
    assert any(f"git diff --name-only {previous} HEAD" in command for command in calls)
    assert any(command.endswith("restart prometheus") for command in calls)
    assert not any(command.endswith("restart alertmanager") for command in calls)


def test_a_code_only_deploy_restarts_no_monitoring(monkeypatch, deploy):
    module, calls, remote = deploy
    monkeypatch.setattr(module, "run_cmd", _pulling(remote, ["src/app/x.py"]))
    module.main()
    assert not any(" restart " in command for command in calls)
    # Recreated only if their compose definition changed - `up -d` decides.
    assert any(
        command.endswith("up -d redis jaeger prometheus alertmanager grafana") for command in calls
    )
