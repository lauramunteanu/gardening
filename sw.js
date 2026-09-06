/* Service worker — calendrier de culture
   App shell is precached, Google Fonts are cached on first use.
   Bump CACHE when index.html changes so clients pick up the new version. */

const CACHE = 'calendrier-v4';

const SHELL = [
  './',
  './index.html',
  './data.json',
  './manifest.webmanifest',
  './icon.svg'
];

const FONT_HOSTS = ['fonts.googleapis.com', 'fonts.gstatic.com'];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE)
      .then(cache => cache.addAll(SHELL))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys()
      .then(keys => Promise.all(
        keys.filter(k => k !== CACHE).map(k => caches.delete(k))
      ))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', event => {
  const req = event.request;
  if (req.method !== 'GET') return;

  const url = new URL(req.url);

  // Fonts: serve from cache if we have them, otherwise fetch and stash a copy.
  if (FONT_HOSTS.includes(url.hostname)) {
    event.respondWith(
      caches.match(req).then(hit => hit || fetch(req).then(res => {
        const copy = res.clone();
        caches.open(CACHE).then(cache => cache.put(req, copy));
        return res;
      }))
    );
    return;
  }

  if (url.origin !== self.location.origin) return;

  // Garden data: network first, so an edit to data.json shows up on the next
  // load without a hard refresh. The cached copy is the offline fallback.
  if (url.pathname.endsWith('/data.json')) {
    event.respondWith(
      fetch(req.url, { cache: 'no-store', credentials: 'same-origin' })
        .then(res => {
          if (res.ok) {
            const copy = res.clone();
            caches.open(CACHE).then(cache => cache.put('./data.json', copy));
          }
          return res;
        })
        .catch(() => caches.match('./data.json'))
    );
    return;
  }

  // Navigations: network first so a fresh deploy shows up, cache as fallback.
  // GitHub Pages serves HTML with max-age=600, so a plain fetch() can be answered
  // from the HTTP cache with a copy up to ten minutes old — no-store skips that.
  if (req.mode === 'navigate') {
    event.respondWith(
      fetch(req.url, { cache: 'no-store', credentials: 'same-origin' })
        .then(res => {
          const copy = res.clone();
          caches.open(CACHE).then(cache => cache.put('./index.html', copy));
          return res;
        })
        .catch(() => caches.match('./index.html').then(hit => hit || caches.match('./')))
    );
    return;
  }

  // Everything else same-origin: cache first.
  event.respondWith(
    caches.match(req).then(hit => hit || fetch(req).then(res => {
      if (res.ok && res.type === 'basic') {
        const copy = res.clone();
        caches.open(CACHE).then(cache => cache.put(req, copy));
      }
      return res;
    }))
  );
});
