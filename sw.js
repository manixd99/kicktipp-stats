// Minimaler Service Worker, damit die Seite als App installierbar ist.
// Die Seite selbst kommt immer frisch aus dem Netz; nur ohne Netz wird die zuletzt geladene Version gezeigt.
// Daten (data.json, GitHub-API) werden nie zwischengespeichert.
const CACHE = 'tipprunde-v1';
self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', (e) => e.waitUntil(self.clients.claim()));
self.addEventListener('fetch', (e) => {
  if (e.request.mode !== 'navigate') return;
  e.respondWith(
    fetch(e.request)
      .then((r) => { const k = r.clone(); caches.open(CACHE).then((c) => c.put('./', k)); return r; })
      .catch(() => caches.match('./'))
  );
});
