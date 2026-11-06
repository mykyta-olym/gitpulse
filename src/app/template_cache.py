"""Build Jinja bytecode into the image; load it without runtime writes."""

from pathlib import Path

from jinja2 import Environment, FileSystemBytecodeCache, FileSystemLoader, select_autoescape
from jinja2.bccache import Bucket

from app.i18n import register_jinja_i18n

TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"
CACHE_DIR = Path(__file__).resolve().parents[2] / "template-cache"


class _ImageBytecodeCache(FileSystemBytecodeCache):
    def dump_bytecode(self, bucket: Bucket) -> None:
        # A missing, outdated or invalid entry falls back to compilation, without
        # trying to write to the production container's read-only filesystem.
        pass


def template_environment(
    template_dir: Path = TEMPLATE_DIR,
    cache_dir: Path = CACHE_DIR,
    *,
    read_only: bool = True,
) -> Environment:
    cache = None
    if cache_dir.is_dir():
        cache_type = _ImageBytecodeCache if read_only else FileSystemBytecodeCache
        cache = cache_type(str(cache_dir))
    env = Environment(
        loader=FileSystemLoader(template_dir),
        autoescape=select_autoescape(),
        bytecode_cache=cache,
    )
    register_jinja_i18n(env)
    env.policies["json.dumps_kwargs"] = {"ensure_ascii": False}
    return env


def build_template_cache(template_dir: Path = TEMPLATE_DIR, cache_dir: Path = CACHE_DIR) -> int:
    """Compile with the runtime paths and filters; fail the image on bad syntax."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    env = template_environment(template_dir, cache_dir, read_only=False)
    names = env.list_templates(extensions=["html"])
    for name in names:
        env.get_template(name)
    # Jinja writes private temporary files as root during the image build;
    # the runtime's unprivileged app user must be able to read the result.
    for entry in cache_dir.glob("*.cache"):
        entry.chmod(0o644)
    return len(names)


if __name__ == "__main__":
    print(f"Built bytecode for {build_template_cache()} templates.")  # noqa: T201 - build CLI
