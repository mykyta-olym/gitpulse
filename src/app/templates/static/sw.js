/* ===============================================================
   GitPulse - Service Worker (PWA)
   Strategy:
     * Static assets (CSS/JS/images/fonts) -> Cache-first
     * HTML pages                          -> Network-first (offline fallback)
     * API calls                           -> Network-only
   =============================================================== */
const CACHE_VERSION = 'gitpulse-v831';
const STATIC_CACHE = `${CACHE_VERSION}-static`;
const PAGES_CACHE  = `${CACHE_VERSION}-pages`;

/* Assets pre-cached on install (app shell) - only static assets;
   HTML pages may redirect to OAuth so they cannot be pre-cached. */
const APP_SHELL = [
  '/static/favicon.svg',
  '/static/offline.html',
  '/static/css/tokens.css',
  '/static/css/theme.css',
  '/static/css/error.css',
  '/static/js/theme-bootstrap.js',
  '/static/img/icons/icon-192x192.png',
  '/static/img/icons/icon-512x512.png',
];

/* -- Install: pre-cache app shell -- */
self.addEventListener('install', (e) => {
  e.waitUntil(
    caches.open(STATIC_CACHE)
      .then(cache => cache.addAll(APP_SHELL))
      .then(() => self.skipWaiting())
  );
});

/* -- Activate: clean old caches -- */
self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys().then(keys =>
      Promise.all(
        keys
          .filter(k => k.startsWith('gitpulse-') && k !== STATIC_CACHE && k !== PAGES_CACHE)
          .map(k => caches.delete(k))
      )
    ).then(() => self.clients.claim())
  );
});

/* -- Fetch strategies -- */
self.addEventListener('fetch', (e) => {
  const { request } = e;
  const url = new URL(request.url);

  /* Skip non-GET, API calls, and cross-origin */
  if (request.method !== 'GET') return;
  if (url.pathname.startsWith('/api/')) return;
  /* The documentation is a separate site behind its own nginx, with its own
     cache headers and its own fingerprinted assets. Caching it here meant a
     reader kept being served a copy this worker had stored, no matter what
     was deployed - including one whose markup was later found to be broken.
     It must not be intercepted at all. */
  if (url.pathname === '/docs' || url.pathname.startsWith('/docs/')) return;
  if (url.origin !== self.location.origin) return;

  /* Authenticated dashboard pages carry Cache-Control: no-store and must
     never be copied into the Service Worker Cache API. The SW still serves
     cache-first static assets referenced by those pages. We only intercept
     navigations to allow offline fallback routing. */
  if (request.mode !== 'navigate' && (url.pathname === '/dashboard' || url.pathname.startsWith('/dashboard/'))) return;

  /* Navigations - network-first with offline fallback. We deliberately
     skip the OAuth callback (preserves redirect chain) and any URL
     that explicitly opted out via ?nocache. */
  if (request.mode === 'navigate') {
    if (url.pathname.startsWith('/auth/') || url.pathname.startsWith('/login')) return;
    e.respondWith(networkFirst(request, PAGES_CACHE));
    return;
  }

  /* Static assets -> Cache-first (versioned by ?v= hash) */
  if (url.pathname.startsWith('/static/')) {
    e.respondWith(cacheFirst(request, STATIC_CACHE));
    return;
  }

  /* HTML pages -> Network-first with cache fallback */
  if (request.headers.get('accept')?.includes('text/html')) {
    e.respondWith(networkFirst(request, PAGES_CACHE));
    return;
  }
});

/* -- Cache-first: return cached if available, else fetch & cache -- */
async function cacheFirst(request, cacheName) {
  const cached = await caches.match(request);
  if (cached) return cached;
  try {
    const response = await fetch(request);
    if (isCacheableResponse(response)) {
      const cache = await caches.open(cacheName);
      cache.put(request, response.clone());
    }
    return response;
  } catch {
    return new Response('', { status: 503, statusText: 'Offline' });
  }
}

/* -- Network-first: try network (one transient retry), fall back to cache, and
   only show the full-screen offline page when the browser is ACTUALLY offline. -- */
async function networkFirst(request, cacheName) {
  for (let attempt = 0; attempt < 2; attempt++) {
    try {
      const response = await fetch(request);
      if (isCacheableResponse(response)) {
        const cache = await caches.open(cacheName);
        cache.put(request, response.clone());
      }
      return response;
    } catch (err) {
      // First failure while online is usually a transient blip - retry once.
      if (attempt === 0 && !(self.navigator && self.navigator.onLine === false)) continue;
      const cached = await caches.match(request);
      if (cached) return cached;
      /* Only hijack the page with "You're offline" when the browser is genuinely
         offline. A failed request while onLine === true (a blip, an aborted
         navigation, a momentarily unreachable backend) must NOT show the offline
         page - re-raise so the browser shows its own error / the retry lands. */
      if (self.navigator && self.navigator.onLine === false) {
        const offlinePage = await caches.match('/static/offline.html');
        if (offlinePage) return offlinePage;
        return new Response('Offline', { status: 503, headers: { 'Content-Type': 'text/plain' } });
      }
      throw err;
    }
  }
}

function isCacheableResponse(response) {
  if (!response || !response.ok) return false;
  const cacheControl = response.headers.get('cache-control') || '';
  return !/(^|,\s*)(no-store|private)(\s|,|$)/i.test(cacheControl);
}
