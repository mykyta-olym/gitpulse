"""Image bytecode is loaded and startup finishes before accepting requests."""

from __future__ import annotations

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, Mock

import pytest
from jinja2 import DictLoader, Environment, TemplateSyntaxError

from app.services.warmup import _FIRST, _ordered, warm_process, warm_template_cache
from app.template_cache import build_template_cache, template_environment

REPO = Path(__file__).resolve().parents[2]
TEMPLATES = REPO / "src/app/templates"


def _env(**templates: str) -> Environment:
    return Environment(loader=DictLoader(templates), autoescape=True)


class TestItWarms:
    async def test_every_template_is_compiled_and_cached(self) -> None:
        env = _env(**{f"p{i}.html": f"<p>{i}</p>" for i in range(5)})
        assert not env.cache, "nothing should be compiled before the warm-up runs"

        warmed = await warm_template_cache(env)

        assert warmed == 5
        assert env.cache is not None
        assert len(env.cache) == 5

    async def test_a_broken_template_does_not_stop_the_others(self) -> None:
        """A warm-up must never be the reason the application fails to start."""
        env = _env(**{"good.html": "<p>ok</p>", "broken.html": "{% for %}", "b.html": "<p>2</p>"})

        warmed = await warm_template_cache(env)

        assert warmed == 2, "the two valid templates should still be compiled"

    async def test_it_hands_the_loop_back_between_templates(self) -> None:
        """The point of the background task: a request that arrives mid-warm-up
        is served after ONE template compiles, not after all hundred."""
        env = _env(**{f"p{i}.html": f"<p>{i}</p>" for i in range(10)})
        ticks = 0

        async def competing_request() -> None:
            nonlocal ticks
            while True:
                ticks += 1
                await asyncio.sleep(0)

        other = asyncio.create_task(competing_request())
        await warm_template_cache(env)
        other.cancel()

        assert ticks >= 10, f"the warm-up yielded {ticks} times for 10 templates"

    async def test_a_database_that_is_not_up_yet_does_not_stop_the_warm_up(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Postgres can still be starting when the API does. The templates are
        compiled either way, and the pool reconnects on its own."""
        import app.services.warmup as warmup

        async def _boom() -> None:
            raise ConnectionRefusedError("postgres is not up yet")

        monkeypatch.setattr(warmup, "warm_orm", _boom)
        env = _env(**{"a.html": "<p>a</p>", "b.html": "<p>b</p>"})

        assert await warm_process(env) == 2

    async def test_an_unresponsive_database_cannot_hold_startup_indefinitely(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        import app.services.warmup as warmup

        cancelled = asyncio.Event()

        async def unavailable() -> None:
            try:
                await asyncio.Event().wait()
            finally:
                cancelled.set()

        monkeypatch.setattr(warmup, "warm_orm", unavailable)
        monkeypatch.setattr(warmup, "_ORM_WARMUP_TIMEOUT_S", 0.01)
        env = _env(**{"page.html": "ok"})

        assert await asyncio.wait_for(warm_process(env), 2) == 1
        assert cancelled.is_set()


class TestItWarmsTheRightThingsFirst:
    @pytest.mark.parametrize("name", _FIRST)
    def test_the_head_of_the_order_names_real_templates(self, name: str) -> None:
        """A renamed template would silently drop out of the priority list and
        the page behind it would go back to compiling on demand."""
        assert (TEMPLATES / name).is_file(), f"{name} is not a template any more"

    def test_the_listed_pages_come_before_the_rest(self) -> None:
        env = _env(**{"zzz.html": "", "base.html": "", "dashboard.html": ""})
        order = _ordered(env)
        assert order.index("base.html") < order.index("zzz.html")
        assert order.index("dashboard.html") < order.index("zzz.html")

    def test_the_rest_are_warmed_in_a_stable_order(self) -> None:
        env = _env(**{"b.html": "", "a.html": "", "c.html": ""})
        assert _ordered(env) == ["a.html", "b.html", "c.html"]


class TestItIsWiredIntoStartup:
    @pytest.mark.parametrize("development", [False, True])
    async def test_only_a_warmed_production_process_accepts_requests(
        self, monkeypatch: pytest.MonkeyPatch, development: bool
    ) -> None:
        import app.main as main
        import app.observability.tracing as tracing
        import app.services.warmup as warmup
        from app.config import AppEnv, get_settings

        settings = get_settings().model_copy(
            update={
                "app_env": AppEnv.DEVELOPMENT if development else AppEnv.PRODUCTION,
                "feature_redis_sessions": False,
            }
        )
        monkeypatch.setattr(main, "get_settings", lambda: settings)
        for name in ("setup_logging", "init_engine", "init_redis_pool", "close_redis_pool"):
            monkeypatch.setattr(main, name, Mock())
        monkeypatch.setattr(tracing, "setup_tracing", Mock())
        monkeypatch.setattr(main, "dispose_engine", AsyncMock())
        started, finish, accepting = asyncio.Event(), asyncio.Event(), asyncio.Event()

        async def prepare(env: Environment) -> int:
            assert env is main.templates.env
            started.set()
            await finish.wait()
            return 1

        monkeypatch.setattr(warmup, "warm_process", prepare)

        async def run() -> None:
            async with main.lifespan(main.create_app()):
                accepting.set()

        task = asyncio.create_task(run())
        try:
            if development:
                await asyncio.wait_for(task, 5)
                assert not started.is_set()
            else:
                await asyncio.wait_for(started.wait(), 5)
                assert not accepting.is_set(), "startup returned while the process was still cold"
                finish.set()
                await asyncio.wait_for(task, 5)
            assert accepting.is_set()
            main.dispose_engine.assert_awaited_once()
        finally:
            task.cancel()


class TestImageBytecode:
    def test_a_fresh_process_loads_templates_without_compiling(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        templates, cache = tmp_path / "templates", tmp_path / "bytecode"
        templates.mkdir()
        (templates / "page.html").write_text("{{ value }} {{ data|tojson_attr }}", encoding="utf-8")
        assert build_template_cache(templates, cache) == 1
        assert next(cache.iterdir()).stat().st_mode & 0o444 == 0o444

        def compile_in_request(*args: object, **kwargs: object) -> None:
            pytest.fail("the image's bytecode was not reused")

        env = template_environment(templates, cache)
        monkeypatch.setattr(env, "compile", compile_in_request)
        rendered = env.get_template("page.html").render(value="<unsafe>", data={"name": "Žofia"})
        assert "&lt;unsafe&gt;" in rendered
        assert "Žofia" in rendered

    @pytest.mark.parametrize("state", ["changed", "missing", "invalid"])
    def test_source_changes_and_cache_misses_work_without_runtime_writes(
        self, tmp_path: Path, state: str
    ) -> None:
        templates, cache = tmp_path / "templates", tmp_path / "bytecode"
        templates.mkdir()
        source = templates / "page.html"
        source.write_text("old {{ value }}", encoding="utf-8")
        build_template_cache(templates, cache)
        entry = next(cache.iterdir())
        if state == "changed":
            source.write_text("new {{ value }}", encoding="utf-8")
        elif state == "missing":
            entry.unlink()
        else:
            entry.write_bytes(b"invalid bytecode")
        before = {p.name: p.read_bytes() for p in cache.iterdir()}

        env = template_environment(templates, cache)
        expected = "new &lt;x&gt;" if state == "changed" else "old &lt;x&gt;"
        assert env.get_template("page.html").render(value="<x>") == expected
        assert {p.name: p.read_bytes() for p in cache.iterdir()} == before

    def test_missing_image_cache_keeps_source_checkouts_working(self, tmp_path: Path) -> None:
        (tmp_path / "page.html").write_text("{{ value }}", encoding="utf-8")
        env = template_environment(tmp_path, tmp_path / "absent")
        assert env.get_template("page.html").render(value="ok") == "ok"
        assert not (tmp_path / "absent").exists()

    def test_bad_templates_fail_the_image_build(self, tmp_path: Path) -> None:
        templates = tmp_path / "templates"
        templates.mkdir()
        (templates / "bad.html").write_text("{% for %}", encoding="utf-8")
        with pytest.raises(TemplateSyntaxError):
            build_template_cache(templates, tmp_path / "cache")
