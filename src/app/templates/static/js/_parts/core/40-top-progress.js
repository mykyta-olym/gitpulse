/* Requests and page initialisation own separate tokens. The last release
   completes the continuous fill before it fades. */
(function () {
  const pending = new Set();
  const requests = new Map();
  const bar = document.createElement('div');
  bar.id = 'gp-top-progress';
  bar.setAttribute('role', 'progressbar');
  bar.setAttribute('aria-label', GP.t('Loading...'));
  bar.setAttribute('aria-hidden', 'true');
  const inner = document.createElement('div');
  inner.className = 'gp-top-progress-bar';
  bar.appendChild(inner);
  document.documentElement.appendChild(bar);
  const motion = GP.motion.topProgress(bar, inner);
  let busy = false;

  function render() {
    const active = pending.size > 0;
    if (active === busy) return;
    busy = active;
    bar.classList.toggle('is-active', busy);
    bar.setAttribute('aria-hidden', String(!busy));
    if (busy) motion.start();
    else motion.finish();
  }

  GP.beginTopProgress = function () {
    const token = {};
    pending.add(token);
    render();
    return function () {
      pending.delete(token);
      render();
    };
  };

  function finishRequest(event) {
    const xhr = event.detail?.xhr;
    const release = requests.get(xhr);
    if (!release) return;
    requests.delete(xhr);
    release();
  }

  document.body.addEventListener('htmx:beforeRequest', function (event) {
    const { xhr, elt, target } = event.detail || {};
    const source = elt || target;
    if (!xhr || requests.has(xhr) || event.defaultPrevented) return;
    if (source?.closest('[data-no-progress]') || /\bevery\b/i.test(source?.getAttribute('hx-trigger') || '')) return;
    const release = GP.beginTopProgress();
    requests.set(xhr, release);
    const finish = () => finishRequest({ detail: { xhr } });
    xhr.addEventListener('loadend', finish, { once: true });
    // A later listener can prevent dispatch, in which case loadend never fires.
    setTimeout(function () {
      if (event.defaultPrevented) {
        xhr.removeEventListener('loadend', finish);
        finish();
      }
    }, 0);
  });
  ['afterRequest', 'responseError', 'sendError', 'timeout', 'xhr:abort'].forEach(function (name) {
    document.body.addEventListener('htmx:' + name, finishRequest);
  });

  window.addEventListener('pageshow', function (event) {
    if (!event.persisted) return;
    requests.clear();
    pending.clear();
    busy = false;
    bar.classList.remove('is-active');
    bar.setAttribute('aria-hidden', 'true');
    motion.reset();
  });
})();
