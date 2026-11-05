// Service worker (P11.1): keeps every file of this version so the game starts and plays with no
// network (in a plane, on the subway). Built by vite.config.js, which fills in the version and the
// exact file list. Not a module, no imports: it runs on its own.
const VERSION = __SW_VERSION__;
const FILES = __SW_FILES__;
const CACHE = `seimyaku-${VERSION}`;
// By address only: servers add "Vary: Origin", and module scripts are requested with an Origin
// header the stored copies were fetched without — a strict match would miss them offline.
const MATCH = { ignoreSearch: true, ignoreVary: true };

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches
      .open(CACHE)
      .then((cache) => cache.addAll(FILES))
      .then(() => self.skipWaiting()),
  );
});

self.addEventListener('activate', (event) => {
  // Older versions' files are let go.
  event.waitUntil(
    caches
      .keys()
      .then((keys) => Promise.all(keys.filter((k) => k.startsWith('seimyaku-') && k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim()),
  );
});

self.addEventListener('fetch', (event) => {
  const req = event.request;
  if (req.method !== 'GET' || new URL(req.url).origin !== self.location.origin) return;
  // Pages: the network first (a new version is picked up), the kept copy when offline.
  if (req.mode === 'navigate') {
    event.respondWith(fetch(req).catch(() => caches.match('index.html', MATCH)));
    return;
  }
  // Everything else is versioned by its file name: the kept copy first.
  event.respondWith(caches.match(req.url, MATCH).then((hit) => hit ?? fetch(req)));
});
