"""Load the real progress owner and motion fallback for Node lifecycle checks."""

from pathlib import Path


def top_progress_runtime() -> str:
    scripts = Path(__file__).resolve().parents[1] / "src/app/templates/static/js"
    return r"""
global.window = { GP: {}, addEventListener() {} };
global.GP = window.GP;
global.requestAnimationFrame = callback => setTimeout(callback, 0);
global.cancelAnimationFrame = clearTimeout;
function progressElement() {
  const classes = new Set(), attributes = new Map();
  return {style: {removeProperty(name) {delete this[name];}}, children: [],
    appendChild(el) { this.children.push(el); },
    setAttribute: (name, value) => attributes.set(name, value),
    getBoundingClientRect: () => ({left: 0, right: 100, width: 100}),
    classList: {add: name => classes.add(name), remove: name => classes.delete(name),
      contains: name => classes.has(name),
      toggle(name, active) {if (active) classes.add(name); else classes.delete(name);}}
  };
}
global.document = {readyState: 'loading', documentElement: progressElement(),
  body: {addEventListener() {}}, addEventListener() {}, createElement: progressElement};
global.getComputedStyle = () => ({getPropertyValue: () => ''});
""" + "\n".join(
        (scripts / name).read_text(encoding="utf-8")
        for name in ["_parts/core/00-namespace.js", "motion.js", "_parts/core/40-top-progress.js"]
    )
