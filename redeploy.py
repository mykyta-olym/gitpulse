"""Full rebuild + restart for the production deployment host."""

from __future__ import annotations

import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

# Force UTF-8 on our own stdout/stderr. The remote build steps (Hugo, Pagefind,
# BuildKit) print box-drawing characters like `│`; on a Windows console whose
# default is cp1252, relaying that output raised UnicodeEncodeError and killed
# the deploy mid-way - after the images were rebuilt but before the containers
# were restarted, leaving prod on the old version. `errors="replace"` means an
# unencodable glyph degrades to `?` instead of crashing the release.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)  # type: ignore[attr-defined]


SSH_TIMEOUT_SECONDS = 30
FALSE_VALUES = {"0", "false", "no", "off"}
# An api + worker build needs a few GB; postgres must keep room to write.
MIN_FREE_GB = 10
# The static files the last pull deleted, kept serving until the next deploy.
STATIC_KEPT = "/root/.gitpulse-static-kept.tar"
# Services whose config docker-compose.yml mounts as single files.
MOUNTED_CONFIGS = {
    "prometheus": ("monitoring/prometheus.yml", "monitoring/prometheus/alerts.yml"),
    # The templates are a directory mount, but Alertmanager reads them at start.
    "alertmanager": (
        "monitoring/alertmanager.yml",
        "monitoring/alertmanager-templates/gitpulse.tmpl",
    ),
}


def env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() not in FALSE_VALUES


def env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError as exc:
        raise SystemExit(f"{name} must be an integer") from exc


def build_ssh_command() -> list[str]:
    """Build a non-interactive OpenSSH command prefix."""
    if os.getenv("DEPLOY_SSH_PASSWORD"):
        raise SystemExit(
            "DEPLOY_SSH_PASSWORD is intentionally unsupported. Use a deploy key "
            "or SSH agent instead of passing production passwords to a process."
        )

    host = os.getenv("DEPLOY_HOST", "147.232.205.227")
    port = env_int("DEPLOY_SSH_PORT", 22)
    username = os.getenv("DEPLOY_USER", "root")
    key_filename = os.getenv("DEPLOY_SSH_KEY_FILENAME")
    strict_host_key = env_bool("DEPLOY_SSH_STRICT_HOST_KEY", True)

    cmd = [
        "ssh",
        "-4",
        "-p",
        str(port),
        "-o",
        "BatchMode=yes",
        "-o",
        f"ConnectTimeout={SSH_TIMEOUT_SECONDS}",
        "-o",
        "ServerAliveInterval=30",
        "-o",
        "ServerAliveCountMax=2",
        "-o",
        f"StrictHostKeyChecking={'yes' if strict_host_key else 'accept-new'}",
    ]
    if not key_filename:
        default_key = os.path.expanduser("~/.ssh/gitpulse_deploy")
        if os.path.exists(default_key):
            key_filename = default_key

    if key_filename:
        cmd.extend(["-i", key_filename])
    cmd.append(f"{username}@{host}")

    print(f"=== SSH target: {username}@{host}:{port} ===")
    return cmd


def free_gb_of(df_output: str) -> int:
    """The `df --output=avail -BG` figure. The session prints the host's login
    banner before any output, so the figure is the last line that is one."""
    figures = re.findall(r"^\s*(\d+)G\s*$", df_output, flags=re.MULTILINE)
    if not figures:
        raise SystemExit(f"Could not read the free disk space from: {df_output[-200:]!r}")
    return int(figures[-1])


def run_cmd(ssh_cmd: list[str], remote_cmd: str, timeout: int = 900) -> tuple[str, str]:
    result = subprocess.run(
        [*ssh_cmd, "bash", "-seuo", "pipefail"],
        input=remote_cmd.encode("utf-8"),
        capture_output=True,
        timeout=timeout,
        check=False,
    )
    out = result.stdout.decode("utf-8", errors="replace") if result.stdout else ""
    err = result.stderr.decode("utf-8", errors="replace") if result.stderr else ""
    if out.strip():
        print(out[-2000:].rstrip())
    if err.strip():
        print(err[-2000:].rstrip())
    if result.returncode != 0:
        raise SystemExit(result.returncode)
    return out, err


def main() -> None:
    repo = Path(__file__).resolve().parent
    git = shutil.which("git")
    if git is None:
        raise SystemExit("Git is required to identify the release commit.")
    expected_sha = subprocess.check_output([git, "rev-parse", "HEAD"], cwd=repo, text=True).strip()
    expected_version = tomllib.loads((repo / "pyproject.toml").read_text(encoding="utf-8"))[
        "project"
    ]["version"]
    app = shlex.quote(os.getenv("DEPLOY_APP_PATH", "/root/devops-teaching-assistant"))
    ssh_cmd = build_ssh_command()

    print("=== Git pull ===")
    # The running containers serve static/ from this checkout until they are
    # replaced, minutes from now - and pages already open, or cached, keep
    # asking for what they linked. A file the pull deletes would 404 for all of
    # them in between, so raw assets stay untracked for one deploy cycle:
    # the next deploy removes it (unless it has become tracked again).
    run_cmd(
        ssh_cmd,
        f"cd {app}\n"
        'if [ -n "$(git status --porcelain --untracked-files=no)" ]; then\n'
        "  printf '%s\\n' 'Production checkout has tracked changes; resolve them before deploying.' >&2\n"
        "  exit 1\n"
        "fi\n"
        f"if [ -f {STATIC_KEPT} ]; then tar -tf {STATIC_KEPT} | while read -r f; do "
        'git ls-files --error-unmatch "$f" >/dev/null 2>&1 || rm -f "$f"; done; fi; '
        "git fetch -q origin main && git diff --name-only --diff-filter=D HEAD FETCH_HEAD "
        "-- src/app/templates/static "
        "':(exclude)src/app/templates/static/js/**' "
        "':(exclude)src/app/templates/static/css/**' "
        f"| tar -cf {STATIC_KEPT} -T -",
    )
    previous_sha = run_cmd(ssh_cmd, f"cd {app} && git rev-parse HEAD")[0].strip()
    run_cmd(
        ssh_cmd,
        f'cd {app} && git pull --ff-only origin main && test "$(git rev-parse HEAD)" = {expected_sha}',
    )
    run_cmd(ssh_cmd, f"cd {app} && tar -xf {STATIC_KEPT}")
    pulled = (
        set(
            run_cmd(ssh_cmd, f"cd {app} && git diff --name-only {shlex.quote(previous_sha)} HEAD")[
                0
            ].split()
        )
        if previous_sha
        else set()
    )

    print("\n=== Inject GIT_SHA ===")
    run_cmd(
        ssh_cmd,
        (
            f'cd {app} && sed -i "/^GIT_SHA=/d" .env.production '
            '&& echo "GIT_SHA=$(git rev-parse HEAD)" >> .env.production'
        ),
    )

    print("\n=== Inject session policy (idempotent) ===")
    # Ensure persistent_sessions=true and 30d/90d TTLs are present in
    # .env.production so users are not forced to re-authenticate on every
    # redeploy or after 8 hours of idle. Defaults in docker-compose.yml line
    # up with these values, but explicit env entries make the policy
    # auditable and resistant to docker-compose default drift.
    session_env_lines = (
        "PERSISTENT_SESSIONS=true",
        "SESSION_MAX_AGE_SECONDS=2592000",  # 30 days idle TTL
        "SESSION_ABSOLUTE_MAX_AGE_SECONDS=7776000",  # 90 days absolute ceiling
    )
    for line in session_env_lines:
        key = line.split("=", 1)[0]
        run_cmd(
            ssh_cmd,
            f'cd {app} && sed -i "/^{key}=/d" .env.production && echo "{line}" >> .env.production',
        )

    print("\n=== Disable production LLM analysis feature (idempotent) ===")
    # Keep AI collaboration analysis off in production. The code also gates the
    # effective setting by environment, but the deployed env file should reflect
    # the intended production policy directly.
    run_cmd(
        ssh_cmd,
        f'cd {app} && sed -i "/^FEATURE_LLM_SUGGESTIONS=/d" .env.production '
        '&& echo "FEATURE_LLM_SUGGESTIONS=false" >> .env.production',
    )

    print("\n=== Enable the classroom assistant (idempotent) ===")
    # On in production: the Assistant tab and its bot. Each course still has to
    # connect a bot token and switch its tools on, so nothing acts until a
    # teacher sets it up. docker-compose.yml passes the flag through.
    run_cmd(
        ssh_cmd,
        f'cd {app} && sed -i "/^FEATURE_CLASSROOM_ASSISTANT=/d" .env.production '
        '&& echo "FEATURE_CLASSROOM_ASSISTANT=true" >> .env.production',
    )

    print("\n=== Free superseded build cache, check disk ===")
    # Every deploy leaves its superseded build cache and the image it replaced
    # behind. By 2026-10-01 that was 230 GB of the 244 GB disk: the post100
    # build took the last of it, postgres crash-looped on "No space left on
    # device", and the site answered 503 for hours. Cache a build used within
    # the last week stays - the dependency layers every routine deploy reuses -
    # and an image no tag points at any more goes.
    run_cmd(
        ssh_cmd,
        "docker builder prune -a -f --filter until=168h >/dev/null\n"
        "docker image prune -f >/dev/null",
        timeout=1800,
    )
    avail, _ = run_cmd(ssh_cmd, "df --output=avail -BG / | tail -1")
    free_gb = free_gb_of(avail)
    if free_gb < MIN_FREE_GB:
        raise SystemExit(
            f"Only {free_gb} GB free on the production disk (< {MIN_FREE_GB} GB). A build "
            "now could fill it and take postgres down with it - free space first."
        )

    full = "--no-cache" in sys.argv
    print(f"\n=== Rebuild API + Worker ({'no-cache' if full else 'cached layers'}) ===")
    # CACHED BY DEFAULT, and this matters more than it sounds.
    #
    # The production host has FOUR cores and runs the application on them. A
    # `--no-cache` build reinstalls every dependency from scratch and pegs those
    # cores for minutes - while the app is still serving requests. Measured
    # during one such build: load average 5.03 on 4 cores, a sequential scan
    # over 7924 rows that live entirely in shared buffers taking 1229ms, an
    # `UPDATE users` taking 36 417ms, and two requests that waited 107 SECONDS
    # without ever being handed a database connection. Every "the pages take
    # forever on production" report today arrived while a deploy was rebuilding
    # images underneath the reader.
    #
    # A code-only deploy - which is nearly all of them - changes one COPY layer,
    # so a cached build reuses the dependency layers and finishes in seconds.
    # Pass --no-cache when the base image or the dependency set really changed
    # and the cache would hide it. The generous timeout stays either way: on a
    # slow VPN even a cached build can outlive the default SSH deadline, and a
    # build killed halfway leaves the container on the old image.
    cache_flag = " --no-cache" if full else ""
    run_cmd(
        ssh_cmd,
        f"cd {app} && docker compose --env-file .env.production build api worker{cache_flag}",
        timeout=2400,
    )

    print("\n=== Rebuild + restart docs-site (compose-managed) ===")
    # docs-site is now a first-class compose service (`gitpulse-docs`) that
    # Caddy depends on. Remove any container whose name contains gitpulse-docs
    # before the `up` below - not just the legacy exactly-named `gitpulse-docs`,
    # but the compose-managed `<project>-gitpulse-docs-1` and docker's
    # half-renamed `<hash>_<project>-gitpulse-docs-1` backup that an interrupted
    # recreate leaves behind. The 2026-08-24 deploy failed exactly here: the
    # narrow `docker rm -f gitpulse-docs` did not match the prefixed names, so
    # `up` hit "container name ... is already in use".
    run_cmd(
        ssh_cmd,
        f"cd {app} && docker compose --env-file .env.production build gitpulse-docs",
        timeout=1800,
    )
    run_cmd(ssh_cmd, "docker ps -aq --filter name=gitpulse-docs | xargs -r docker rm -f")
    run_cmd(
        ssh_cmd,
        f"cd {app} && docker compose --env-file .env.production up -d gitpulse-docs",
    )

    print("\n=== Graceful worker drain (SIGTERM, up to 180s) ===")
    # `docker compose up -d` alone triggers a --force-recreate style restart
    # with the default 10 s stop timeout, which kills in-flight sync jobs and
    # marks them as "Worker died - job interrupted." Stop workers first with
    # a generous timeout so RQ has room to finish whatever is running, then
    # start them back up in the next step.
    run_cmd(
        ssh_cmd,
        f"cd {app} && docker compose --env-file .env.production stop -t 180 worker",
        timeout=300,
    )

    print("\n=== Alembic upgrade head ===")
    # Use the newly built image before replacing the serving API. Running this
    # through `exec api` applied migrations only after new code was serving.
    run_cmd(
        ssh_cmd,
        f"cd {app} && docker compose --env-file .env.production run --rm --no-deps api python -m alembic upgrade head",
        timeout=300,
    )

    # Check the revision against the new image, not the API it will replace.
    print("\n=== Verify schema reached head ===")
    current, _ = run_cmd(
        ssh_cmd,
        f"cd {app} && docker compose --env-file .env.production run --rm --no-deps api "
        "python -m alembic current | tail -1",
        timeout=120,
    )
    heads, _ = run_cmd(
        ssh_cmd,
        f"cd {app} && docker compose --env-file .env.production run --rm --no-deps api "
        "python -m alembic heads | tail -1",
        timeout=120,
    )

    def _revision(text: str) -> str:
        # "013 (head)" / "013" -> "013"
        line = [ln for ln in text.strip().splitlines() if ln.strip()]
        return line[-1].split()[0].strip() if line else ""

    current_rev, head_rev = _revision(current), _revision(heads)
    print(f"alembic current={current_rev!r} heads={head_rev!r}")
    if not head_rev or current_rev != head_rev:
        raise SystemExit(
            f"DB is at {current_rev!r} but the code expects {head_rev!r}. "
            "Stopping before replacing the serving API. Fix the migration before retrying."
        )

    # Apply startup recovery settings while the old API is still serving.
    # Waiting until `up api worker` returns applied a longer proxy retry window
    # only AFTER the very startup gap it was intended to cover.
    running_caddy, _ = run_cmd(
        ssh_cmd,
        f"cd {app} && docker compose --env-file .env.production ps --status running -q caddy",
    )
    if any(re.fullmatch(r"[0-9a-f]{12,64}", line.strip()) for line in running_caddy.splitlines()):
        run_cmd(
            ssh_cmd,
            f"cd {app} && docker compose --env-file .env.production exec -T caddy "
            "caddy reload --config /dev/stdin --adapter caddyfile < Caddyfile",
        )

    print("\n=== Restart API + Workers + Caddy ===")
    # --remove-orphans deletes containers for services no longer in the compose
    # file - notably the old `scheduler` (rq-scheduler) service we removed, so
    # its container stops polling and is cleaned up on this deploy.
    run_cmd(
        ssh_cmd,
        f"cd {app} && docker compose --env-file .env.production up -d --remove-orphans api worker",
    )
    # Caddy is RELOADED, not recreated. It used to be force-recreated on every
    # deploy, which took the proxy itself down for a few seconds - and since the
    # outage page is served BY Caddy, that was the one window where a reader got
    # the upstream proxy's bare "Bad Gateway" instead. Measured on the
    # 2026.9.3.post4 deploy: six such responses in ~0.2s each, between one
    # request that correctly waited 15s for our page and another that waited
    # 15.7s and got the real one.
    #
    # `up -d` still recreates it when the compose definition itself changed (a
    # new volume, a new image); it just no longer does so when nothing did.
    # A Caddyfile edit is a bind-mounted file, invisible to that check, so the
    # config is reloaded explicitly - which Caddy applies with no downtime.
    #
    # From the checkout, through stdin. A file mounted on its own is pinned to
    # the inode it had when the container started, and the pull writes a
    # changed file as a new one, so /etc/caddy/Caddyfile inside still reads
    # the old text: reloading it applied nothing (reproduced: "v1" served on
    # after the file said "v2").
    run_cmd(
        ssh_cmd,
        f"cd {app} && docker compose --env-file .env.production up -d caddy",
    )
    run_cmd(
        ssh_cmd,
        f"cd {app} && docker compose --env-file .env.production exec -T caddy "
        "caddy reload --config /dev/stdin --adapter caddyfile < Caddyfile",
    )

    print("\n=== Redis + monitoring ===")
    # Recreated only when their compose definition changed (Redis's maxmemory,
    # Jaeger's trace limit, Grafana's auth proxy); otherwise `up -d` leaves
    # them running.
    run_cmd(
        ssh_cmd,
        f"cd {app} && docker compose --env-file .env.production "
        "up -d redis jaeger prometheus alertmanager grafana",
    )
    # Their configs are mounted file by file too, and neither reloads from
    # stdin: a restart mounts the path afresh. Only when the pull changed one.
    for service, configs in MOUNTED_CONFIGS.items():
        if pulled & set(configs):
            run_cmd(
                ssh_cmd,
                f"cd {app} && docker compose --env-file .env.production restart {service}",
            )

    print("\n=== Verify running release ===")
    probe = (
        "import json,os; from app.config import get_settings; "
        "print(json.dumps({'sha': os.environ.get('GIT_SHA'), "
        "'version': get_settings().app_version}))"
    )
    runtime, _ = run_cmd(
        ssh_cmd,
        f"cd {app} && docker compose --env-file .env.production exec -T api "
        f"python -c {shlex.quote(probe)}",
    )
    running = json.loads(runtime.strip().splitlines()[-1])
    if running != {"sha": expected_sha, "version": expected_version}:
        raise SystemExit(f"Running release does not match the requested commit: {running}")

    print("=== Health check ===")
    run_cmd(
        ssh_cmd,
        "curl --fail --silent --show-error --retry 12 --retry-delay 2 "
        "--retry-connrefused --retry-all-errors --max-time 10 "
        'http://localhost:8000/health/ready -H "Host: gitpulse.kpi.fei.tuke.sk"',
        timeout=240,
    )

    print("\n=== Container status ===")
    run_cmd(ssh_cmd, f"cd {app} && docker compose --env-file .env.production ps")

    print("\n=== DONE ===")


if __name__ == "__main__":
    main()
