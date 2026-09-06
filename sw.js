/* Service worker — calendrier de culture
   App shell is precached, Google Fonts are cached on first use.
   Bump CACHE when index.html changes so clients pick up the new version. */

const CACHE = 'calendrier-v5';

const SHELL = [
  './',
  './index.html',
  './potager.html',
  './fleurs.html',
  './data-potager.json',
  './data-fleurs.json',
  './manifest.webmanifest',
  './icon.svg'
];

// Chaque page navigable a sa propre copie en cache : la page d'accueil ne peut
// pas servir de repli pour le potager, elle n'en a pas le contenu.
const PAGES = ['/index.html', '/potager.html', '/fleurs.html'];

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

  // Garden data: network first, so an edit to a data file shows up on the next
  // load without a hard refresh. The cached copy is the offline fallback.
  if (/\/data-(potager|fleurs)\.json$/.test(url.pathname)) {
    event.respondWith(
      fetch(req.url, { cache: 'no-store', credentials: 'same-origin' })
        .then(res => {
          if (res.ok) {
            const copy = res.clone();
            caches.open(CACHE).then(cache => cache.put(url.pathname, copy));
          }
          return res;
        })
        .catch(() => caches.match(url.pathname))
    );
    return;
  }

  // Navigations: network first so a fresh deploy shows up, cache as fallback.
  // GitHub Pages serves HTML with max-age=600, so a plain fetch() can be answered
  // from the HTTP cache with a copy up to ten minutes old — no-store skips that.
  if (req.mode === 'navigate') {
    // '/gardening/' and '/gardening/index.html' are the same document.
    const page = PAGES.find(p => url.pathname.endsWith(p)) ||
                 (url.pathname.endsWith('/') ? '/index.html' : null);
    event.respondWith(
      fetch(req.url, { cache: 'no-store', credentials: 'same-origin' })
        .then(res => {
          if (res.ok && page) {
            const copy = res.clone();
            caches.open(CACHE).then(cache => cache.put('.' + page, copy));
          }
          return res;
        })
        .catch(() => caches.match(page ? '.' + page : req)
                       .then(hit => hit || caches.match('./index.html')))
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
