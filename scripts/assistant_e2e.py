"""The classroom assistant, end to end, against a real GitLab CE.

The unit and integration tests drive the assistant with a GitLab kept in
memory. This drives it with a real one, of the version the department runs:
real webhooks, a real ``git merge`` for the conflict exercise, GitLab's own
merge, approval and pipeline status. Every step prints PASS or FAIL, and
what is checked is what a student sees in GitLab.

    docker compose -f docker-compose.gitlab-e2e.yml up -d   # GitLab on :8929, ~5 min
    python scripts/assistant_e2e.py provision                # users, a course group, tokens
    python scripts/assistant_e2e.py env                      # GitPulse's environment for it

Start GitPulse with that environment on a database of its own (run
``alembic upgrade head`` on it first): the API with
``uvicorn app.main:create_app --factory --host 0.0.0.0 --port 8020`` and a
worker with ``python -m app.workers.main``. GitLab reaches the API at
host.docker.internal:8020. Then:

    python scripts/assistant_e2e.py setup                    # import, webhook, connect the bot
    python scripts/assistant_e2e.py run                      # every scenario
    python scripts/assistant_e2e.py accounts                 # logins, to try it by hand

``provision`` again makes a new course group, so the run repeats on the same
GitLab and database. State (tokens included) is kept in the system temp dir.
"""

import argparse
import base64
import json
import re
import secrets
import subprocess
import sys
import tempfile
import time
import urllib.parse
from collections.abc import Callable
from pathlib import Path
from typing import Any

import httpx

GITLAB = "http://127.0.0.1:8929"
GITPULSE = "http://127.0.0.1:8020"
HOOK_URL = "http://host.docker.internal:8020/api/v1/webhooks/gitlab"
CONTAINER = "gitpulse-e2e-gitlab"
HOME = Path(tempfile.gettempdir()) / "gitpulse-assistant-e2e"
STATE = HOME / "state.json"

TEACHER = ("ucitel.e2e", "Učiteľ Testovací")
TEAMS = {
    "tim-01": [
        ("anna.kovacova", "Anna Kováčová"),
        ("boris.novak", "Boris Novák"),
        ("cyril.horvath", "Cyril Horváth"),
    ],
    "tim-02": [("dana.mala", "Dana Malá")],
}
README = (
    "# Tímový projekt\n\nTento projekt slúži na tímové zadanie z predmetu.\n\n"
    "## Členovia tímu\n\n- doplní každý člen\n\n## Ako spustiť\n\n"
    "Projekt sa spúšťa príkazom `make run`.\n\n## Poznámky\n\nSem pridávame poznámky k práci.\n"
)
# The sections a new course's R05 asks for; the issue now says so.
SECTIONS = "## Description\n\nVyplnil som svoj súbor.\n\n## Testing\n\nSkontroloval som obsah."
TOOLS = {
    "push_review_enabled": "true",
    "min_commit_title_length": "10",
    "conflict_enabled": "true",
    "conflict_file_path": "README.md",
    "mr_review_enabled": "true",
    "exercise_file_template": "ulohy/{username}.txt",
    "comment_language": "sk",
}

RESULTS: list[tuple[str, bool, str]] = []


# -- Bookkeeping ------------------------------------------------------------------


def load() -> dict[str, Any]:
    return json.loads(STATE.read_text(encoding="utf-8")) if STATE.exists() else {}


def save(state: dict[str, Any]) -> None:
    HOME.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")


def check(name: str, ok: Any, detail: Any = "") -> bool:
    RESULTS.append((name, bool(ok), str(detail)[:300]))
    print(f"[{'PASS' if ok else 'FAIL'}] {name}" + ("" if ok else f"  -- {str(detail)[:300]}"))
    return bool(ok)


def summary() -> int:
    failed = [r for r in RESULTS if not r[1]]
    print(f"\n{len(RESULTS) - len(failed)}/{len(RESULTS)} checks passed")
    return 1 if failed else 0


def wait_for(probe: Callable[[], Any], timeout: float = 90) -> Any:
    """Poll until ``probe`` answers something truthy, or time runs out."""
    deadline = time.monotonic() + timeout
    value = probe()
    while not value and time.monotonic() < deadline:
        time.sleep(2)
        value = probe()
    return value


def says(body: str, *words: str) -> bool:
    """The comment says one of ``words`` (Slovak or English), any case."""
    return any(word.lower() in body.lower() for word in words)


# -- GitLab -------------------------------------------------------------------------


class GitLab:
    """GitLab's API as one user - or, with ``sudo``, as anyone (admin token)."""

    def __init__(self, token: str, sudo: str | None = None) -> None:
        headers = {"PRIVATE-TOKEN": token, **({"Sudo": sudo} if sudo else {})}
        self.http = httpx.Client(base_url=f"{GITLAB}/api/v4", headers=headers, timeout=60)

    def get(self, path: str, /, **params: Any) -> Any:
        response = self.http.get(path, params=params)
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return response.json()

    def send(self, method: str, path: str, /, **data: Any) -> Any:
        response = self.http.request(method, path, json=data)
        if response.status_code >= 400:
            raise RuntimeError(f"{method} {path}: {response.status_code} {response.text[:300]}")
        return response.json() if response.content else None

    def file(self, pid: int, path: str, ref: str) -> str | None:
        found = self.get(
            f"/projects/{pid}/repository/files/{urllib.parse.quote(path, safe='')}", ref=ref
        )
        return base64.b64decode(found["content"]).decode("utf-8") if found else None

    def commit(self, pid: int, branch: str, message: str, files: dict[str, str]) -> dict[str, Any]:
        actions = [
            {
                "action": "update" if self.file(pid, path, branch) is not None else "create",
                "file_path": path,
                "content": text,
            }
            for path, text in files.items()
        ]
        return self.send(
            "POST",
            f"/projects/{pid}/repository/commits",
            branch=branch,
            commit_message=message,
            actions=actions,
        )

    def branch(self, pid: int, name: str, files: dict[str, str], message: str) -> str:
        self.send("POST", f"/projects/{pid}/repository/branches", branch=name, ref="main")
        return str(self.commit(pid, name, message, files)["id"])

    def open_mr(self, pid: int, branch: str, title: str, description: str) -> int:
        mr = self.send(
            "POST",
            f"/projects/{pid}/merge_requests",
            source_branch=branch,
            target_branch="main",
            title=title,
            description=description,
        )
        return int(mr["iid"])

    def head(self, pid: int, branch: str) -> str:
        return str(self.get(f"/projects/{pid}/repository/branches/{branch}")["commit"]["id"])


def notes_by(gitlab: GitLab, author: str, pid: int, *, iid: int = 0, sha: str = "") -> list[str]:
    """What ``author`` wrote on a merge request (``iid``) or a commit (``sha``)."""
    if iid:
        found = gitlab.get(f"/projects/{pid}/merge_requests/{iid}/notes", sort="asc", per_page=100)
        # GitLab's own system notes ("approved this merge request") are not
        # what the bot wrote.
        return [
            n["body"] for n in found or [] if n["author"]["username"] == author and not n["system"]
        ]
    found = gitlab.get(f"/projects/{pid}/repository/commits/{sha}/comments")
    return [c["note"] for c in found or [] if c["author"]["username"] == author]


def next_note(gitlab: GitLab, author: str, pid: int, iid: int, seen: int) -> str:
    """The first comment ``author`` writes after the ``seen`` ones ("" if none)."""
    found = wait_for(lambda: (n := notes_by(gitlab, author, pid, iid=iid)) and len(n) > seen and n)
    return found[seen] if found else ""


def root_token(state: dict[str, Any]) -> str:
    """An admin API token, made inside the container: the run never needs
    GitLab's root password."""
    if "root_token" not in state:
        token = "token_prefix_" + secrets.token_urlsafe(15)[:20]
        ruby = (
            "t = User.find_by_username('root').personal_access_tokens.create!("
            "name: 'assistant-e2e', scopes: ['api', 'sudo', 'admin_mode'], "
            "expires_at: 300.days.from_now, organization: Organizations::Organization.first); "
            f"t.set_token('{token}'); t.save!; puts 'TOKEN_OK'"
        )
        out = subprocess.run(
            ["docker", "exec", CONTAINER, "gitlab-rails", "runner", ruby],
            capture_output=True,
            text=True,
            check=False,
        )
        if "TOKEN_OK" not in out.stdout:
            sys.exit(f"could not make the admin token:\n{out.stdout}\n{out.stderr}")
        state["root_token"] = token
        save(state)
    return str(state["root_token"])


def user(root: GitLab, username: str, name: str, *, admin: bool = False) -> dict[str, Any]:
    found = root.get("/users", username=username)
    if found:
        return dict(found[0])
    return dict(
        root.send(
            "POST",
            "/users",
            username=username,
            name=name,
            email=f"{username}@e2e.example.edu",
            password="Pw-" + secrets.token_hex(12),
            skip_confirmation=True,
            admin=admin,
        )
    )


# -- provision ----------------------------------------------------------------------


def provision() -> int:
    state = load()
    root = GitLab(root_token(state))
    if not root.get("/application/settings")["allow_local_requests_from_web_hooks_and_services"]:
        root.send(
            "PUT",
            "/application/settings",
            allow_local_requests_from_web_hooks_and_services=True,
            signup_enabled=False,
        )
        # Sidekiq, which sends the webhooks, keeps the old setting cached and
        # refuses GitPulse as "the local network" until it restarts.
        subprocess.run(
            ["docker", "exec", CONTAINER, "gitlab-ctl", "restart", "sidekiq"], check=True
        )
    teacher = user(root, *TEACHER)
    state["teacher"] = teacher["username"]
    for members in TEAMS.values():
        for username, name in members:
            known = state.setdefault("students", {}).get(username)
            if known is None:
                found = user(root, username, name)
                token = root.send(
                    "POST",
                    f"/users/{found['id']}/impersonation_tokens",
                    name="assistant-e2e",
                    scopes=["api", "write_repository"],
                    expires_at=time.strftime("%Y-%m-%d", time.gmtime(time.time() + 200 * 86400)),
                )["token"]
                state["students"][username] = {"id": found["id"], "name": name, "token": token}
    if "sync_token" not in state:
        # GitPulse's read-only sync account: an admin outside the course
        # group, so the import does not take it for a student.
        sync = user(root, "gitpulse.sync", "GitPulse Sync", admin=True)
        state["sync_token"] = root.send(
            "POST",
            f"/users/{sync['id']}/personal_access_tokens",
            name="gitpulse-sync",
            scopes=["read_api", "read_repository", "read_user"],
            expires_at=time.strftime("%Y-%m-%d", time.gmtime(time.time() + 200 * 86400)),
        )["token"]
    state.setdefault("teacher_api_token", secrets.token_urlsafe(24))

    # A new course group each time, so a run can be repeated.
    stamp = time.strftime("%m%d-%H%M%S")
    as_teacher = GitLab(state["root_token"], sudo=teacher["username"])
    group = as_teacher.send(
        "POST", "/groups", path=f"assistant-e2e-{stamp}", name=f"Assistant E2E {stamp}"
    )
    run: dict[str, Any] = {"group": group["full_path"], "group_id": group["id"], "projects": {}}
    for team, members in TEAMS.items():
        sub = as_teacher.send(
            "POST", "/groups", path=team, name=team.upper(), parent_id=group["id"]
        )
        project = as_teacher.send(
            "POST",
            "/projects",
            name="projekt",
            namespace_id=sub["id"],
            initialize_with_readme=True,
            default_branch="main",
        )
        as_teacher.commit(project["id"], "main", "Pripraviť README projektu", {"README.md": README})
        for username, _ in members:
            root.send(
                "POST",
                f"/projects/{project['id']}/members",
                user_id=state["students"][username]["id"],
                access_level=40,
            )
        run["projects"][team] = {"id": project["id"], "path": project["path_with_namespace"]}
    bot = as_teacher.send(
        "POST",
        f"/groups/{group['id']}/access_tokens",
        name="Asistent cvičení",
        scopes=["api"],
        access_level=40,
        expires_at=time.strftime("%Y-%m-%d", time.gmtime(time.time() + 200 * 86400)),
    )
    run["bot_token"], run["bot_token_id"] = bot["token"], bot["id"]
    # GitLab grants a new member access in the background.
    for team, members in TEAMS.items():
        pid = run["projects"][team]["id"]
        for username, _ in members:
            student = GitLab(state["students"][username]["token"])
            if not wait_for(lambda student=student, pid=pid: student.get(f"/projects/{pid}"), 120):
                sys.exit(f"{username} still cannot see project {pid}")
    state["run"] = run
    save(state)
    print(f"provisioned {run['group']} (state in {STATE})")
    return 0


def env() -> int:
    state = load()
    values = {
        "GITLAB_URL": GITLAB,
        "GITLAB_API_TOKEN": state["sync_token"],
        "TEACHER_API_TOKEN": state["teacher_api_token"],
        "GITLAB_TEACHER_USERNAMES": json.dumps([state["teacher"]]),
        "APP_BASE_URL": GITPULSE,
        "ALLOWED_HOSTS": '["*"]',
        "DEBUG": "true",
        "FEATURE_CLASSROOM_ASSISTANT": "true",
        "DATABASE_URL": "postgresql+asyncpg://gitpulse:gitpulse@127.0.0.1:5433/gitpulse_e2e",
        "REDIS_URL": "redis://127.0.0.1:6379/3",
    }
    for key, value in values.items():
        print(f"export {key}='{value}'")
    return 0


def accounts() -> int:
    """The logins for trying it by hand. GitLab's users get a password of
    their own once (kept with the state); GitPulse is the dev login."""
    state = load()
    passwords: dict[str, str] = state.setdefault("passwords", {})
    people = [state["teacher"], *state["students"]]
    missing = [username for username in people if username not in passwords]
    if missing:
        for username in missing:
            passwords[username] = f"Gp-{secrets.token_hex(8)}-e2e"
        # Through rails, not the API: a password an admin sets over the API
        # has to be changed at the first sign-in.
        ruby = "; ".join(
            f"u = User.find_by_username('{username}'); u.password = '{passwords[username]}'; "
            f"u.password_confirmation = u.password; u.password_expires_at = nil; u.save!"
            for username in missing
        )
        out = subprocess.run(
            ["docker", "exec", CONTAINER, "gitlab-rails", "runner", ruby + "; puts 'PW_OK'"],
            capture_output=True,
            text=True,
            check=False,
        )
        if "PW_OK" not in out.stdout:
            sys.exit(f"could not set the passwords:\n{out.stdout}\n{out.stderr}")
        save(state)
    run = state.get("run", {})
    print(f"GitLab   {GITLAB}  (course group: {GITLAB}/{run.get('group', '?')})")
    for username in people:
        role = "teacher" if username == state["teacher"] else "student"
        print(f"  {role:8} {username:16} {passwords[username]}")
    print(f"  root     docker exec {CONTAINER} cat /etc/gitlab/initial_root_password")
    print(
        f"GitPulse {GITPULSE}/dashboard/login  (dev login: role Teacher, username {state['teacher']})"
    )
    if run.get("course_id"):
        print(f"  the Assistant page: {GITPULSE}/dashboard/courses/{run['course_id']}/assistant")
    return 0


# -- GitPulse -----------------------------------------------------------------------


class Dashboard:
    """GitPulse's dashboard after the dev login (DEBUG=true)."""

    def __init__(self) -> None:
        self.http = httpx.Client(base_url=GITPULSE, timeout=60)
        page = self.http.get("/dashboard/login").text
        csrf = re.search(r'name="csrf_token"\s+value="([^"]+)"', page)
        if csrf is None:
            sys.exit("no dev login - is GitPulse running with DEBUG=true?")
        self.http.post(
            "/dashboard/login",
            data={"csrf_token": csrf.group(1), "role": "admin", "username": "e2e_admin"},
        )
        self.csrf = ""

    def page(self, path: str) -> str:
        html = self.http.get(path, cookies={"gp_lang": "en"}).text
        found = re.search(r'name="csrf-token"\s+content="([^"]+)"', html)
        self.csrf = found.group(1) if found else self.csrf
        return html

    def post(self, path: str, data: Any) -> httpx.Response:
        return self.http.post(
            path, data=data, headers={"X-CSRF-Token": self.csrf, "Accept": "application/json"}
        )


def assistant_url(state: dict[str, Any], action: str = "") -> str:
    return f"/dashboard/courses/{state['run']['course_id']}/assistant" + (
        f"/{action}" if action else ""
    )


def save_tools(state: dict[str, Any], **overrides: str) -> bool:
    board = Dashboard()
    board.page(assistant_url(state))
    response = board.post(assistant_url(state, "tools"), {**TOOLS, **overrides})
    return check(
        f"tools saved {overrides or ''}".strip(), response.status_code == 200, response.text
    )


def setup() -> int:
    state = load()
    run = state["run"]
    api = httpx.Client(
        base_url=f"{GITPULSE}/api/v1",
        headers={"Authorization": f"Bearer {state['teacher_api_token']}"},
        timeout=180,
    )
    response = api.post(
        "/courses/import/gitlab-group",
        json={
            "group_url": run["group"],
            "course_code": f"E2E-{run['group_id']}",
            "course_name": run["group"],
            "teacher_usernames": [state["teacher"]],
            "auto_sync": True,
        },
    )
    if not check("the course group is imported", response.status_code == 200, response.text):
        return summary()
    run["course_id"] = response.json()["course_id"]
    response = api.post(
        f"/courses/{run['course_id']}/webhook-configs",
        json={"name": "E2E course webhook", "scope_type": "course"},
    )
    if not check("a course webhook secret is issued", response.status_code == 201, response.text):
        return summary()
    secret = response.json()["webhook_secret"]
    root = GitLab(state["root_token"])
    for project in run["projects"].values():
        hook = root.send(
            "POST",
            f"/projects/{project['id']}/hooks",
            url=HOOK_URL,
            token=secret,
            enable_ssl_verification=False,
            push_events=True,
            issues_events=True,
            merge_requests_events=True,
            note_events=True,
            pipeline_events=True,
            job_events=True,
        )
        project["hook_id"] = hook["id"]
    save(state)
    first = run["projects"]["tim-01"]
    response = root.http.post(f"/projects/{first['id']}/hooks/{first['hook_id']}/test/push_events")
    check(
        "the course secret authenticates an imported project (GitLab's test delivery)",
        response.status_code == 201,
        response.text,
    )

    board = Dashboard()
    board.page(assistant_url(state))
    refused = board.post(assistant_url(state, "token"), {"token": state["sync_token"]})
    check(
        "connect refuses the read-only sync token",
        refused.status_code == 422 and refused.json().get("error") == "read_token",
        refused.text,
    )
    refused = board.post(assistant_url(state, "token"), {"token": "glpat_placeholder_token"})
    check("connect refuses a token GitLab does not know", refused.status_code == 422, refused.text)
    response = board.post(assistant_url(state, "token"), {"token": run["bot_token"]})
    if not check(
        "connect accepts the bot's group token", response.status_code == 200, response.text
    ):
        return summary()
    run["bot_username"] = response.json()["bot_username"]
    save(state)
    save_tools(state)
    return summary()


# -- run ----------------------------------------------------------------------------


class Run:
    def __init__(self, state: dict[str, Any]) -> None:
        self.state = state
        self.run = state["run"]
        self.bot = self.run["bot_username"]
        self.p1 = self.run["projects"]["tim-01"]
        self.p2 = self.run["projects"]["tim-02"]
        self.root = GitLab(state["root_token"])
        self.teacher = GitLab(state["root_token"], sudo=state["teacher"])
        self.issues: dict[str, int] = {}

    def student(self, username: str) -> GitLab:
        return GitLab(self.state["students"][username]["token"])

    def git(self, username: str, project: dict[str, Any]) -> "Clone":
        student = self.state["students"][username]
        return Clone(username, student["name"], student["token"], project["path"])

    def bot_said(self, pid: int, *, iid: int = 0, sha: str = "") -> list[str]:
        return notes_by(self.root, self.bot, pid, iid=iid, sha=sha)

    # -- push review --

    def push_review(self) -> None:
        anna, pid = self.student("anna.kovacova"), self.p1["id"]
        # GitLab's "New branch": a push of no commits, its head a teacher's commit.
        anna.send(
            "POST", f"/projects/{pid}/repository/branches", branch="anna-poznamky", ref="main"
        )
        main_head = anna.head(pid, "main")
        sha = anna.commit(
            pid, "anna-poznamky", "Update poznamky.md", {"poznamky.md": "Moje poznámky\n"}
        )["id"]
        said = wait_for(lambda: self.bot_said(pid, sha=sha))
        check(
            "a web-editor commit title gets a comment",
            said and "Update poznamky.md" in said[0],
            said,
        )
        check(
            "a branch created with no commits is not commented on",
            not self.bot_said(pid, sha=main_head),
        )
        sha = anna.commit(
            pid, "anna-poznamky", "Doplniť poznámky z prvého cvičenia", {"poznamky.md": "- Git\n"}
        )["id"]
        time.sleep(15)
        check("a clean push to an existing branch is left alone", not self.bot_said(pid, sha=sha))
        boris = self.student("boris.novak")
        sha = boris.commit(pid, "main", "fix", {"boris.txt": "ahoj\n"})["id"]
        said = wait_for(lambda: self.bot_said(pid, sha=sha))
        check(
            "a direct push to main with a short title gets both points",
            said and "`main`" in said[0] and "„fix“" in said[0],
            said,
        )

    # -- merge conflict --

    def colleague_line(self, pid: int) -> str:
        """The line the bot's colleague commit wrote on main (it carries GP-)."""

        def line() -> str:
            readme = self.root.file(pid, "README.md", "main") or ""
            return next((row for row in readme.splitlines() if "(GP-" in row), "")

        return str(wait_for(line))

    def conflict_resolved(self) -> None:
        clone = self.git("cyril.horvath", self.p1)
        clone.run("checkout", "-b", "cyril-readme")
        clone.write(
            "README.md",
            clone.read("README.md").replace(
                "Sem pridávame poznámky k práci.", "Sem pridávame poznámky k práci tímu."
            ),
        )
        clone.run("commit", "-am", "Doplniť poznámku do README")
        clone.run("push", "-u", "origin", "cyril-readme")
        check("the colleague's line lands on main", self.colleague_line(self.p1["id"]))
        clone.run("fetch", "origin")
        merge = clone.run("merge", "origin/main", check=False)
        check(
            "git reports a real conflict", "CONFLICT" in merge.stdout + merge.stderr, merge.stdout
        )
        kept = [
            r
            for r in clone.read("README.md").splitlines()
            if not r.startswith(("<<<<<<<", "=======", ">>>>>>>"))
        ]
        clone.write("README.md", "\n".join(kept) + "\n")
        clone.run("add", "README.md")
        clone.run("commit", "--no-edit")
        clone.run("push")
        head = self.root.head(self.p1["id"], "cyril-readme")
        said = wait_for(lambda: self.bot_said(self.p1["id"], sha=head))
        check(
            "keeping both sides is praised", said and says(said[0], "vyriešený", "resolved"), said
        )

    def conflict_line_dropped_then_restored(self) -> None:
        clone = self.git("dana.mala", self.p2)
        clone.run("checkout", "-b", "dana-readme")
        clone.write(
            "README.md", clone.read("README.md").replace("- doplní každý člen", "- Dana Malá")
        )
        clone.run("commit", "-am", "Zapísať sa medzi členov tímu")
        clone.run("push", "-u", "origin", "dana-readme")
        line = self.colleague_line(self.p2["id"])
        if not check("the colleague's line lands on the second team's main", line):
            return
        clone.run("fetch", "origin")
        clone.run("merge", "origin/main", check=False)
        mine, side = [], None
        for row in clone.read("README.md").splitlines():
            if row.startswith("<<<<<<<"):
                side = "mine"
            elif row.startswith("=======") and side:
                side = "theirs"
            elif row.startswith(">>>>>>>"):
                side = None
            elif side != "theirs":
                mine.append(row)
        clone.write("README.md", "\n".join(mine) + "\n")
        clone.run("add", "README.md")
        clone.run("commit", "--no-edit")
        clone.run("push")
        head = self.root.head(self.p2["id"], "dana-readme")
        said = wait_for(lambda: self.bot_said(self.p2["id"], sha=head))
        check(
            "dropping the colleague's line is pointed out, quoted",
            said and line.strip() in said[0],
            said,
        )
        clone.write(
            "README.md", clone.read("README.md").replace("- Dana Malá", "- Dana Malá\n" + line, 1)
        )
        clone.run("commit", "-am", "Vrátiť riadok kolegu po konflikte")
        clone.run("push")
        head = self.root.head(self.p2["id"], "dana-readme")
        said = wait_for(lambda: self.bot_said(self.p2["id"], sha=head))
        check("putting it back is praised", said and says(said[0], "vyriešený", "resolved"), said)

    # -- issues and merge requests --

    def prepare_exercise(self) -> None:
        board = Dashboard()
        html = board.page(assistant_url(self.state))
        projects = re.findall(r'name="project_ids"[^>]*?value="([^"]+)"', html, re.DOTALL)
        response = board.post(assistant_url(self.state, "exercise"), {"project_ids": projects})
        check("Prepare exercise is queued", response.status_code == 200, response.text)
        again = board.post(assistant_url(self.state, "exercise"), {"project_ids": projects})
        check(
            "a second run while one runs is refused",
            again.status_code == 409 and again.json().get("error") == "already_running",
            again.text,
        )
        for username in self.state["students"]:
            pid = self.project_of(username)["id"]
            found = wait_for(
                lambda pid=pid, username=username: self.root.get(
                    f"/projects/{pid}/issues", assignee_username=username, state="opened"
                )
            )
            if check(f"{username} is assigned one issue", found and len(found) == 1, found):
                self.issues[username] = int(found[0]["iid"])
                body = found[0]["description"]
                check(
                    f"{username}'s issue names the sections the review asks for",
                    "`## Description`, `## Testing`" in body,
                    body,
                )
            check(
                f"{username}'s file is on main",
                self.root.file(pid, f"ulohy/{username}.txt", "main"),
            )
        time.sleep(5)
        board.page(assistant_url(self.state))
        board.post(assistant_url(self.state, "exercise"), {"project_ids": projects})
        time.sleep(15)
        for username in self.issues:
            pid = self.project_of(username)["id"]
            issues = self.root.get(f"/projects/{pid}/issues", assignee_username=username)
            check(
                f"preparing again gives {username} no second issue", len(issues) == 1, len(issues)
            )

    def project_of(self, username: str) -> dict[str, Any]:
        team = next(t for t, members in TEAMS.items() if username in dict(members))
        return dict(self.run["projects"][team])

    def student_merges(self) -> None:
        anna, pid, issue = (
            self.student("anna.kovacova"),
            self.p1["id"],
            self.issues["anna.kovacova"],
        )
        anna.branch(
            pid,
            f"{issue}-uloha-anna",
            {"ulohy/anna.kovacova.txt": "Meno: Anna Kováčová\nPríkaz: git log\n"},
            "Vyplniť svoj súbor s úlohou",
        )
        iid = anna.open_mr(pid, f"{issue}-uloha-anna", "Vyplnená úloha", "Doplnila som svoj súbor.")
        said = next_note(self.root, self.bot, pid, iid, 0)
        check(
            "the review asks for the issue link and the sections",
            f"`Closes #{issue}`" in said and "## Testing" in said,
            said,
        )
        anna.send(
            "PUT",
            f"/projects/{pid}/merge_requests/{iid}",
            description=f"{SECTIONS}\n\nCloses #{issue}",
        )
        said = next_note(self.root, self.bot, pid, iid, 1)
        approvals = anna.get(f"/projects/{pid}/merge_requests/{iid}/approvals")["approved_by"]
        check(
            "once fixed it is approved in GitLab",
            any(a["user"]["username"] == self.bot for a in approvals),
            approvals,
        )
        check(
            "and the student is asked to merge", says(said, "zlúč", "merge the merge request"), said
        )
        main_before = anna.head(pid, "main")
        anna.send("PUT", f"/projects/{pid}/merge_requests/{iid}/merge")
        said = next_note(self.root, self.bot, pid, iid, 2)
        check("her merge is praised", said, said)
        check(
            "the issue is closed", anna.get(f"/projects/{pid}/issues/{issue}")["state"] == "closed"
        )
        time.sleep(15)
        merge_head = anna.head(pid, "main")
        check(
            "GitLab's merge push to main is not called a direct push",
            merge_head != main_before and not self.bot_said(pid, sha=merge_head),
            self.bot_said(pid, sha=merge_head),
        )

    def review_answers_and_lets_go(self) -> None:
        boris, pid, issue = self.student("boris.novak"), self.p1["id"], self.issues["boris.novak"]
        path = "ulohy/boris.novak.txt"
        template = boris.file(pid, path, "main") or ""
        boris.branch(pid, f"{issue}-boris", {"poznamka.txt": "x\n"}, "Pridať poznámku k úlohe")
        iid = boris.open_mr(pid, f"{issue}-boris", "Úloha Boris", f"{SECTIONS}\n\nCloses #{issue}")
        said = next_note(self.root, self.bot, pid, iid, 0)
        check(
            "an untouched file and an extra one are named",
            path in said and "poznamka.txt" in said,
            said,
        )
        boris.send(
            "POST", f"/projects/{pid}/merge_requests/{iid}/notes", body="Opravené, pozri prosím."
        )
        check(
            "a comment is answered even when nothing moved",
            next_note(self.root, self.bot, pid, iid, 1),
        )
        boris.send("PUT", f"/projects/{pid}/merge_requests/{iid}", state_event="close")
        time.sleep(8)
        # A fresh merge request: a draft, with a failed pipeline (an external status).
        half = template.replace("???", "Boris Novák", 1)
        sha = boris.branch(
            pid,
            f"{issue}-boris-2",
            {path: half.replace("???", "git rebase")},
            "Vyplniť súbor úlohy celý",
        )
        self.root.send(
            "POST",
            f"/projects/{pid}/statuses/{sha}",
            state="failed",
            name="test",
            ref=f"{issue}-boris-2",
        )
        iid = boris.open_mr(
            pid, f"{issue}-boris-2", "Draft: Úloha Boris", f"{SECTIONS}\n\nCloses #{issue}"
        )
        said = next_note(self.root, self.bot, pid, iid, 0)
        check("after closing, the next merge request is reviewed afresh", said, said)
        check(
            "a draft and a failed pipeline hold the approval",
            says(said, "draft") and says(said, "pipeline"),
            said,
        )
        self.root.send(
            "POST",
            f"/projects/{pid}/statuses/{sha}",
            state="success",
            name="test",
            ref=f"{issue}-boris-2",
        )
        boris.send("PUT", f"/projects/{pid}/merge_requests/{iid}", title="Úloha Boris")
        approved = wait_for(
            lambda: any(
                a["user"]["username"] == self.bot
                for a in boris.get(f"/projects/{pid}/merge_requests/{iid}/approvals")["approved_by"]
            )
        )
        check("ready, with a green pipeline, it is approved", approved)
        time.sleep(10)
        bodies = self.bot_said(pid, iid=iid)
        check(
            "the approval is said once",
            sum(says(b, "zlúč", "merge the merge request") for b in bodies) == 1,
            bodies,
        )

    def someone_elses_issue_and_an_early_merge(self) -> None:
        boris, cyril, pid = (
            self.student("boris.novak"),
            self.student("cyril.horvath"),
            self.p1["id"],
        )
        issue, path = self.issues["cyril.horvath"], "ulohy/cyril.horvath.txt"
        boris.branch(
            pid, "boris-pre-cyrila", {path: "Meno: Cyril\n"}, "Vyplniť Cyrilovi jeho súbor"
        )
        iid = boris.open_mr(
            pid, "boris-pre-cyrila", "Pomôžem Cyrilovi", f"{SECTIONS}\n\nCloses #{issue}"
        )
        said = next_note(self.root, self.bot, pid, iid, 0)
        check(
            "a merge request for someone else's issue is told whose it is",
            "cyril.horvath" in said,
            said,
        )
        boris.send("PUT", f"/projects/{pid}/merge_requests/{iid}", state_event="close")
        cyril.branch(
            pid, "cyril-uloha", {path: "Meno: Cyril Horváth\n"}, "Vyplniť svoju úlohu do súboru"
        )
        iid = cyril.open_mr(pid, "cyril-uloha", "Moja úloha", "Hotovo.")
        next_note(self.root, self.bot, pid, iid, 0)
        cyril.send("PUT", f"/projects/{pid}/merge_requests/{iid}/merge")
        said = next_note(self.root, self.bot, pid, iid, 1)
        check("a merge before the approval is said to be one", says(said, "skôr", "before"), said)

    def conflict_in_the_mr_then_the_bot_merges(self) -> None:
        save_tools(self.state, mr_bot_merges="true")
        dana, pid, issue = self.student("dana.mala"), self.p2["id"], self.issues["dana.mala"]
        path = "ulohy/dana.mala.txt"
        dana.branch(
            pid,
            f"{issue}-dana",
            {path: "Meno: Dana Malá\nPríkaz: git switch\n"},
            "Vyplniť svoj súbor s úlohou",
        )
        self.teacher.commit(
            pid,
            "main",
            "Upraviť zadanie v súbore Dany",
            {path: "Meno: (doplň)\nPríkaz: (doplň)\nNovinka: ???\n"},
        )
        iid = dana.open_mr(pid, f"{issue}-dana", "Úloha Dana", f"{SECTIONS}\n\nCloses #{issue}")
        said = next_note(self.root, self.bot, pid, iid, 0)
        check(
            "a merge request in conflict with main is not approved",
            says(said, "konflikt", "conflict"),
            said,
        )
        clone = self.git("dana.mala", self.p2)
        clone.run("checkout", "-b", f"{issue}-dana", f"origin/{issue}-dana")
        clone.run("merge", "origin/main", check=False)
        clone.write(path, "Meno: Dana Malá\nPríkaz: git switch\nNovinka: git restore\n")
        clone.run("add", path)
        clone.run("commit", "--no-edit")
        clone.run("push")
        merged = wait_for(
            lambda: dana.get(f"/projects/{pid}/merge_requests/{iid}")["state"] == "merged", 120
        )
        mr = dana.get(f"/projects/{pid}/merge_requests/{iid}")
        check(
            "resolved, the bot approves and merges it itself",
            merged and (mr.get("merged_by") or {}).get("username") == self.bot,
            mr["state"],
        )
        check(
            "and closes the issue", dana.get(f"/projects/{pid}/issues/{issue}")["state"] == "closed"
        )
        save_tools(self.state)

    def english(self) -> None:
        save_tools(self.state, comment_language="en")
        boris, pid = self.student("boris.novak"), self.p1["id"]
        sha = boris.commit(pid, "main", "Update notes.txt", {"notes-en.txt": "x\n"})["id"]
        said = wait_for(lambda: self.bot_said(pid, sha=sha))
        check(
            "a course set to English is answered in English",
            said and said[0].startswith("Push to the branch"),
            said,
        )
        save_tools(self.state)

    def revoked_then_reconnected(self) -> None:
        response = self.root.http.delete(
            f"/groups/{self.run['group_id']}/access_tokens/{self.run['bot_token_id']}"
        )
        check("GitLab revokes the bot's token", response.status_code == 204, response.text)
        anna, pid = self.student("anna.kovacova"), self.p1["id"]
        anna.commit(pid, "main", "fix2", {"po-revokacii.txt": "x\n"})
        board = Dashboard()
        shown = wait_for(
            lambda: (
                "GitLab no longer accepts the bot token" in board.page(assistant_url(self.state))
            )
        )
        check("the Assistant page says GitLab refuses the token", shown)
        refused = board.post(assistant_url(self.state, "exercise"), {"project_ids": ["x"]})
        check(
            "Prepare exercise is refused with the reason",
            refused.status_code == 409 and refused.json()["error"] == "token_unusable",
            refused.text,
        )
        bot = self.teacher.send(
            "POST",
            f"/groups/{self.run['group_id']}/access_tokens",
            name="Asistent cvičení 2",
            scopes=["api"],
            access_level=40,
            expires_at=time.strftime("%Y-%m-%d", time.gmtime(time.time() + 200 * 86400)),
        )
        board.page(assistant_url(self.state))
        response = board.post(assistant_url(self.state, "token"), {"token": bot["token"]})
        check("a new token connects", response.status_code == 200, response.text)
        self.bot = response.json()["bot_username"]
        check(
            "and the refusal is gone from the page",
            "no longer accepts" not in board.page(assistant_url(self.state)),
        )
        sha = anna.commit(pid, "main", "fix3", {"po-novom-tokene.txt": "x\n"})["id"]
        check("the assistant acts again", wait_for(lambda: self.bot_said(pid, sha=sha)))


class Clone:
    """A real clone, for what the API cannot do: a merge commit."""

    def __init__(self, username: str, name: str, token: str, path: str) -> None:
        # A clone of its own each time: Windows will not delete the read-only
        # objects of an earlier one.
        self.dir = HOME / "clones" / f"{username}-{path.replace('/', '_')}-{time.time_ns()}"
        self.dir.parent.mkdir(parents=True, exist_ok=True)
        url = f"http://oauth2:{token}@127.0.0.1:8929/{path}.git"
        subprocess.run(
            ["git", "clone", "-q", "-c", "core.autocrlf=false", url, str(self.dir)], check=True
        )
        self.run("config", "user.name", name)
        self.run("config", "user.email", f"{username}@e2e.example.edu")

    def run(self, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", *args],
            cwd=self.dir,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=check,
        )

    def read(self, path: str) -> str:
        return (self.dir / path).read_text(encoding="utf-8")

    def write(self, path: str, text: str) -> None:
        (self.dir / path).write_bytes(text.encode("utf-8"))


SCENARIOS = (
    "push_review",
    "conflict_resolved",
    "conflict_line_dropped_then_restored",
    "prepare_exercise",
    "student_merges",
    "review_answers_and_lets_go",
    "someone_elses_issue_and_an_early_merge",
    "conflict_in_the_mr_then_the_bot_merges",
    "english",
    "revoked_then_reconnected",
)


def run_scenarios(names: list[str]) -> int:
    scenarios = Run(load())
    for name in names or SCENARIOS:
        print(f"\n== {name}")
        getattr(scenarios, name)()
    return summary()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("command", choices=["provision", "env", "setup", "run", "accounts"])
    parser.add_argument("scenarios", nargs="*", help=f"for run: some of {', '.join(SCENARIOS)}")
    args = parser.parse_args()
    if args.command == "run":
        return run_scenarios(args.scenarios)
    commands = {"provision": provision, "env": env, "setup": setup, "accounts": accounts}
    return commands[args.command]()


if __name__ == "__main__":
    sys.exit(main())
