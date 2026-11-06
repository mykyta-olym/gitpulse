"""GitPulse - GitLab Teamwork & Assessment Platform."""

# ---------------------------------------------------------------------------
# Monkey-patch: rq.scheduler calls ``get_context('fork').Process`` at import
# time, which crashes on Windows where only the 'spawn' context is available.
# We make ``get_context`` fall back to 'spawn' when 'fork' is requested on a
# platform that doesn't support it.
# ---------------------------------------------------------------------------
import os as _os

if _os.name == "nt":
    import multiprocessing as _mp

    _orig_get_context = _mp.get_context

    def _safe_get_context(method=None):  # type: ignore[no-untyped-def]
        try:
            return _orig_get_context(method)
        except ValueError:
            # 'fork' is unavailable on Windows - fall back to 'spawn'
            return _orig_get_context("spawn")

    _mp.get_context = _safe_get_context
    del _mp
