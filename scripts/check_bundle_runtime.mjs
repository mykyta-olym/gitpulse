/**
 * Execute core.bundle.js against a stub DOM and report anything it throws.
 *
 * `node --check` only parses. It cannot tell you that the bundle throws the
 * moment a browser runs it - a typo'd global, a call on an undefined export, a
 * bad destructure at module top level. That class of failure takes the WHOLE
 * bundle down, so every feature on every page dies at once, and nothing in the
 * Python test suite notices.
 *
 * Deliberately dependency-free (node's built-in `vm`, no package.json, no
 * npm install). The stub is therefore shallow: it is enough to let top-level
 * module code run, not to emulate a browser. Treat a pass as "the bundle
 * loads", not "the UI works".
 *
 * Usage:  node scripts/check_bundle_runtime.mjs [bundle.js ...]
 * Exits non-zero and prints one line per failure.
 */
import { readFileSync } from 'node:fs';
import { createContext, runInContext } from 'node:vm';

const targets = process.argv.slice(2);
if (targets.length === 0) {
  console.error('usage: node check_bundle_runtime.mjs <bundle.js> [...]');
  process.exit(2);
}

/** A DOM node that answers every call with something plausible. */
function makeElement(tag = 'div') {
  const el = {
    tagName: String(tag).toUpperCase(),
    nodeType: 1,
    style: {},
    dataset: {},
    children: [],
    childNodes: [],
    attributes: {},
    classList: {
      add() {}, remove() {}, toggle() {}, contains: () => false, replace() {},
    },
    hidden: false,
    disabled: false,
    value: '',
    textContent: '',
    innerHTML: '',
    scrollTop: 0,
    scrollLeft: 0,
    scrollHeight: 0,
    clientHeight: 0,
    offsetHeight: 0,
    files: [],
    content: null,
    addEventListener() {}, removeEventListener() {}, dispatchEvent: () => true,
    appendChild: (c) => c, removeChild: (c) => c, insertBefore: (c) => c,
    replaceChildren() {}, remove() {}, cloneNode: () => makeElement(tag),
    setAttribute() {}, getAttribute: () => null, removeAttribute() {},
    hasAttribute: () => false, closest: () => null, matches: () => false,
    querySelector: () => null, querySelectorAll: () => [],
    getBoundingClientRect: () => ({ top: 0, left: 0, right: 0, bottom: 0, width: 0, height: 0 }),
    focus() {}, blur() {}, click() {}, scrollTo() {}, scrollIntoView() {},
    getContext: () => null, animate: () => ({ finished: Promise.resolve(), cancel() {} }),
    insertAdjacentHTML() {}, submit() {}, reset() {}, select() {},
  };
  el.parentElement = null;
  el.parentNode = null;
  el.firstElementChild = null;
  el.ownerDocument = null;
  return el;
}

function buildWindow() {
  const documentElement = makeElement('html');
  const body = makeElement('body');

  const document = {
    documentElement,
    body,
    head: makeElement('head'),
    readyState: 'loading',
    cookie: '',
    title: '',
    hidden: false,
    visibilityState: 'visible',
    createElement: (tag) => makeElement(tag),
    createElementNS: (_ns, tag) => makeElement(tag),
    createTextNode: (t) => ({ nodeType: 3, textContent: t }),
    createDocumentFragment: () => makeElement('fragment'),
    getElementById: () => null,
    getElementsByTagName: () => [],
    getElementsByClassName: () => [],
    querySelector: () => null,
    querySelectorAll: () => [],
    addEventListener() {}, removeEventListener() {}, dispatchEvent: () => true,
    createEvent: () => ({ initEvent() {} }),
    activeElement: body,
  };

  const storage = () => {
    const data = new Map();
    return {
      getItem: (k) => (data.has(k) ? data.get(k) : null),
      setItem: (k, v) => data.set(k, String(v)),
      removeItem: (k) => data.delete(k),
      clear: () => data.clear(),
      key: () => null,
      get length() { return data.size; },
    };
  };

  const win = {
    document,
    location: {
      href: 'http://localhost/dashboard/', protocol: 'http:', host: 'localhost',
      hostname: 'localhost', port: '', pathname: '/dashboard/', search: '', hash: '',
      origin: 'http://localhost', assign() {}, replace() {}, reload() {}, toString() { return this.href; },
    },
    history: { pushState() {}, replaceState() {}, back() {}, forward() {}, go() {}, state: null, scrollRestoration: 'auto' },
    navigator: { userAgent: 'node', language: 'en', languages: ['en'], onLine: true, clipboard: { writeText: () => Promise.resolve() }, sendBeacon: () => true },
    screen: { width: 1280, height: 800 },
    innerWidth: 1280,
    innerHeight: 800,
    scrollX: 0,
    scrollY: 0,
    devicePixelRatio: 1,
    localStorage: storage(),
    sessionStorage: storage(),
    matchMedia: () => ({ matches: false, media: '', addEventListener() {}, removeEventListener() {}, addListener() {}, removeListener() {} }),
    addEventListener() {}, removeEventListener() {}, dispatchEvent: () => true,
    requestAnimationFrame: (cb) => { void cb; return 1; },
    cancelAnimationFrame() {},
    requestIdleCallback: (cb) => { void cb; return 1; },
    cancelIdleCallback() {},
    getComputedStyle: () => ({ getPropertyValue: () => '', overflowX: 'visible', overflowY: 'visible' }),
    scrollTo() {}, scrollBy() {}, open: () => null, close() {}, focus() {}, blur() {},
    alert() {}, confirm: () => true, prompt: () => null,
    fetch: () => Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve({}), text: () => Promise.resolve('') }),
    EventSource: class { constructor() { this.close = () => {}; this.addEventListener = () => {}; } },
    WebSocket: class { constructor() { this.close = () => {}; this.addEventListener = () => {}; } },
    IntersectionObserver: class { observe() {} unobserve() {} disconnect() {} },
    MutationObserver: class { observe() {} disconnect() {} takeRecords() { return []; } },
    ResizeObserver: class { observe() {} unobserve() {} disconnect() {} },
    performance: { now: () => 0, mark() {}, measure() {}, getEntriesByType: () => [] },
    CustomEvent: class { constructor(type, init) { this.type = type; this.detail = init && init.detail; } },
    Event: class { constructor(type) { this.type = type; } },
    FormData: class { append() {} get() { return null; } },
    FileReader: class { readAsText() {} readAsDataURL() {} },
    URL,
    URLSearchParams,
    console,
    setTimeout: () => 0,
    AbortController,
    AbortSignal,
    clearTimeout() {},
    setInterval: () => 0,
    clearInterval() {},
    queueMicrotask: (cb) => { void cb; },
    Promise,
    JSON,
    Math,
    Date,
    Intl,
    crypto: { randomUUID: () => '00000000-0000-4000-8000-000000000000', getRandomValues: (a) => a },
  };
  win.window = win;
  win.self = win;
  win.globalThis = win;
  win.top = win;
  win.parent = win;
  document.defaultView = win;
  return win;
}

/* One shared sandbox, files in the order given - a page bundle is written
   against the globals core.bundle.js has already installed, so running it in a
   fresh context would fail for a reason the browser never sees. */
const sandbox = buildWindow();
createContext(sandbox);

let failures = 0;
for (const file of targets) {
  try {
    runInContext(readFileSync(file, 'utf8'), sandbox, { filename: file });
    console.log(`${file}: OK`);
  } catch (err) {
    failures += 1;
    const detail = err && err.stack ? err.stack.split('\n').slice(0, 3).join(' | ') : String(err);
    console.error(`${file}: ${detail}`);
  }
}

// A run that loads everything but installs nothing means the stub swallowed the
// work - report it rather than pass for the wrong reason.
const exports = sandbox.GP ? Object.keys(sandbox.GP).length : 0;
if (failures === 0 && exports === 0) {
  console.error('executed without error but window.GP is empty - the check proved nothing');
  failures += 1;
} else if (failures === 0) {
  console.log(`all OK (${exports} GP exports)`);
}
process.exit(failures === 0 ? 0 : 1);
