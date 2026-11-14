// FarmLens service worker (decision 0005: hand-written, no Workbox).
// - App shell: served from the cache first and refreshed in the background (bump VERSION to force an update).
// - GET /api/fields and /api/crops: stale-while-revalidate, so the form opens offline after one visit.
// - Everything else (POST /api/analyze, map tiles, the map library) goes to the network.
//   Cached analyses for offline demo fields come in a later step (#14, PR 2).

const VERSION = "v1";
const SHELL = `farmlens-shell-${VERSION}`;
const DATA = `farmlens-data-${VERSION}`;
const SHELL_FILES = [
  "./", "index.html", "styles.css", "manifest.webmanifest",
  "js/app.js", "js/api.js", "js/format.js", "js/map.js",
  "icons/icon.svg", "icons/icon-192.png", "icons/icon-512.png", "icons/icon-maskable-512.png",
];
const DATA_PATHS = ["/api/fields", "/api/crops"];

self.addEventListener("install", (event) => {
  event.waitUntil(caches.open(SHELL).then((c) => c.addAll(SHELL_FILES)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k.startsWith("farmlens-") && ![SHELL, DATA].includes(k)).map((k) => caches.delete(k))))
      .then(() => self.clients.claim()),
  );
});

function staleWhileRevalidate(event, cacheName) {
  return caches.open(cacheName).then(async (cache) => {
    const cached = await cache.match(event.request, { ignoreSearch: cacheName === SHELL });
    const fresh = fetch(event.request)
      .then((resp) => {
        if (resp.ok) cache.put(event.request, resp.clone());
        return resp;
      })
      .catch(() => cached || Response.error());
    if (cached) {
      event.waitUntil(fresh.catch(() => {}));
      return cached;
    }
    return fresh;
  });
}

self.addEventListener("fetch", (event) => {
  const { request } = event;
  if (request.method !== "GET") return;
  const url = new URL(request.url);
  if (url.origin !== self.location.origin) return; // map tiles: network only
  if (DATA_PATHS.includes(url.pathname)) {
    event.respondWith(staleWhileRevalidate(event, DATA));
    return;
  }
  if (url.pathname.startsWith("/api/") || url.pathname.startsWith("/vendor/")) return;
  if (request.mode === "navigate") {
    // Any page load gets the app shell (the router lives in the page).
    event.respondWith(fetch(request).catch(() => caches.match("index.html")));
    return;
  }
  event.respondWith(staleWhileRevalidate(event, SHELL));
});
