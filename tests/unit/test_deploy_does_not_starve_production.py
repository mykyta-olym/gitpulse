"""A deploy must not take the production host down with it.

`redeploy.py` built the API and worker images with `--no-cache` on every deploy:
a from-scratch reinstall of every dependency, on the production host, which has
four cores and is serving the application on them at the same time.

What that looked like from inside the app, measured during one such build (the
request log carries the database split now, which is how this became visible at
all):

    load average 5.03 on 4 cores
    a sequential scan over 7924 rows that live entirely in shared buffers: 1229ms
    UPDATE users ...: 36 417ms
    /dashboard/attention-items: 107 442ms with db=0ms and q=0 - 107 seconds
        without ever being handed a connection

Every "the pages take forever on production" report that day arrived while a
deploy was rebuilding images underneath the reader.

The Dockerfile is layered so the cache is safe to use: dependencies are
installed from `requirements.lock` BEFORE the source is copied, so a code-only
deploy reuses the expensive layer and a dependency change invalidates it on its
own. `--no-cache` stays available for when that is really wanted.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
REDEPLOY = REPO / "redeploy.py"
DOCKERFILE = REPO / "Dockerfile"


def _build_command_line() -> str:
    src = REDEPLOY.read_text(encoding="utf-8")
    line = next(
        (ln for ln in src.splitlines() if "build api worker" in ln),
        "",
    )
    assert line, "redeploy.py no longer builds the api and worker images"
    return line


def test_the_routine_deploy_reuses_the_layer_cache() -> None:
    assert "--no-cache" not in _build_command_line(), (
        "every deploy rebuilds both images from scratch on the production host again"
    )


def test_a_full_rebuild_is_still_one_flag_away() -> None:
    src = REDEPLOY.read_text(encoding="utf-8")
    assert '"--no-cache" in sys.argv' in src, (
        "there is no way left to ask for a from-scratch rebuild when one is needed"
    )
    assert "cache_flag" in _build_command_line(), "the flag is read but never applied"


def test_the_dockerfile_earns_that_cache() -> None:
    """Dependencies before source, or the cache would save nothing: every code
    change would invalidate the layer that installs them."""
    lines = DOCKERFILE.read_text(encoding="utf-8").splitlines()
    deps = next(i for i, ln in enumerate(lines) if re.search(r"^COPY .*requirements\.lock", ln))
    install = next(i for i, ln in enumerate(lines) if "uv pip sync" in ln)
    source = next(i for i, ln in enumerate(lines) if re.search(r"^COPY src/", ln))
    assert deps < install < source, (
        "the source is copied before the dependencies are installed, so any code "
        "change reinstalls everything"
    )


def test_the_build_cache_cannot_fill_the_disk() -> None:
    """Prune superseded cache before builds; stop deployment if disk space is still low."""
    src = REDEPLOY.read_text(encoding="utf-8")
    build = src.index("build api worker")
    prune = src.find("docker builder prune")
    floor = src.find("free_gb < MIN_FREE_GB")
    assert 0 <= prune < build, "the build cache is no longer pruned before the build"
    assert "until=" in src[prune : prune + 80], (
        "the prune drops the cache every routine deploy reuses - keep the recent part"
    )
    assert 0 <= floor < build, "nothing stops a build when the disk is nearly full"


def test_the_free_space_is_read_past_the_login_banner() -> None:
    """Parse the disk-space value after any remote login banner."""
    import importlib.util

    spec = importlib.util.spec_from_file_location("redeploy", REDEPLOY)
    assert spec is not None
    assert spec.loader is not None
    redeploy = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(redeploy)
    banner = (
        "Welcome to Ubuntu 24.04.5 LTS\n\n * Documentation: https://help.ubuntu.com\n\n"
        "New release '26.04.1 LTS' available.\nRun 'do-release-upgrade' to upgrade to it.\n\n\n"
    )
    assert redeploy.free_gb_of(banner + " 207G\n") == 207
    assert redeploy.free_gb_of("  9G\n") == 9


def test_a_static_file_the_pull_deletes_keeps_serving_until_the_next_deploy() -> None:
    """The running containers serve static/ from the checkout for minutes after
    the pull, and open or cached pages keep asking for what they linked. When
    the build outputs moved to dist/, the pull deleted core.bundle.js and every
    .min file before the new image was even built. So the files a pull deletes
    are archived before it, put back (untracked) after it, and removed by the
    next deploy - unless they have become tracked again."""
    src = REDEPLOY.read_text(encoding="utf-8")
    keep = src.index("--diff-filter=D HEAD FETCH_HEAD")
    pull = src.index("git pull --ff-only origin main")
    restore = src.index("tar -xf {STATIC_KEPT}")
    build = src.index("build api worker")
    assert keep < pull < restore < build
    assert "git ls-files --error-unmatch" in src[:keep], (
        "the kept files of the last deploy are removed even when tracked again"
    )


def test_release_metadata_does_not_invalidate_locked_dependencies() -> None:
    source = DOCKERFILE.read_text(encoding="utf-8")
    install = source.index("RUN uv pip sync")
    metadata = source.index("COPY pyproject.toml")
    assert install < metadata, "a version-only release reinstalls every dependency"
