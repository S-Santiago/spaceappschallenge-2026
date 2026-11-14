// FarmLens service worker (decision 0005: hand-written, no Workbox).
// - App shell: served from the cache first and refreshed in the background (bump VERSION to force an update).
// - GET /api/fields, /api/crops and /api/predictions: stale-while-revalidate, so the form and "What to expect"
//   open offline after one visit.
// - POST /api/analyze: network first; the last answer for each normalized input combination is kept under a
//   synthetic GET key (the Cache API can't key POST requests). The page computes the key (format.analysisKey)
//   and sends it in the X-FarmLens-Key header. Offline, the saved answer is returned with X-FarmLens-Offline: 1.
// - Every cached API response carries X-FarmLens-Saved-At (when it was saved), shown as "Saved result from <date>".
// - Map tiles and the map library: network only.

const VERSION = "v8";
const SHELL = `farmlens-shell-${VERSION}`;
// Data caches keep their names across app updates, so saved results survive a new version of the app.
const DATA = "farmlens-data-v1";
const ANALYSES = "farmlens-analyses-v1";
const MAX_ANALYSES = 30;
const SHELL_FILES = [
  "./", "index.html", "styles.css", "manifest.webmanifest",
  "js/app.js", "js/api.js", "js/format.js", "js/map.js", "js/expect.js", "js/expect-format.js",
  "icons/icon.svg", "icons/icon-192.png", "icons/icon-512.png", "icons/icon-maskable-512.png",
];
const DATA_PATHS = ["/api/fields", "/api/crops", "/api/predictions"];
const SAVED = "X-FarmLens-Saved-At";

self.addEventListener("install", (event) => {
  // cache: "reload" skips the browser HTTP cache, so a new version never precaches an old file.
  event.waitUntil(caches.open(SHELL)
    .then((c) => c.addAll(SHELL_FILES.map((f) => new Request(f, { cache: "reload" }))))
    .then(() => self.skipWaiting()));
});

self.addEventListener("activate", (event) => {
  const keep = [SHELL, DATA, ANALYSES];
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k.startsWith("farmlens-") && !keep.includes(k)).map((k) => caches.delete(k))))
      .then(() => self.clients.claim()),
  );
});

/** Copy of a response with extra headers (cached responses are immutable). */
async function withHeaders(resp, extra) {
  const headers = new Headers(resp.headers);
  for (const [k, v] of Object.entries(extra)) headers.set(k, v);
  return new Response(await resp.blob(), { status: resp.status, statusText: resp.statusText, headers });
}

async function save(cache, key, resp) {
  await cache.put(key, await withHeaders(resp, { [SAVED]: new Date().toISOString() }));
}

function staleWhileRevalidate(event, cacheName) {
  return caches.open(cacheName).then(async (cache) => {
    const cached = await cache.match(event.request, { ignoreSearch: cacheName === SHELL });
    const fresh = fetch(event.request)
      .then(async (resp) => {
        if (resp.ok) {
          if (cacheName === SHELL) await cache.put(event.request, resp.clone());
          else await save(cache, event.request, resp.clone());
        }
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

async function analyze(event) {
  const key = event.request.headers.get("X-FarmLens-Key");
  const keyUrl = key ? new URL(`/__saved/analyze?${encodeURIComponent(key)}`, self.location.origin).href : null;
  const cache = await caches.open(ANALYSES);
  try {
    const resp = await fetch(event.request);
    if (resp.ok && keyUrl) {
      // Saved before answering (a few ms): a waitUntil started after an await is not reliable in every browser.
      try {
        await cache.delete(keyUrl); // re-insert so the newest entries are last
        await save(cache, keyUrl, resp.clone());
        const keys = await cache.keys();
        await Promise.all(keys.slice(0, Math.max(0, keys.length - MAX_ANALYSES)).map((k) => cache.delete(k)));
      } catch { /* storage full or blocked: answer anyway, just not saved for offline */ }
    }
    return resp;
  } catch (err) {
    const cached = keyUrl && (await cache.match(keyUrl));
    if (cached) return withHeaders(cached, { "X-FarmLens-Offline": "1" });
    throw err; // the page shows its own "You're offline" message
  }
}

self.addEventListener("fetch", (event) => {
  const { request } = event;
  const url = new URL(request.url);
  if (url.origin !== self.location.origin) return; // map tiles: network only
  if (request.method === "POST" && url.pathname === "/api/analyze") {
    event.respondWith(analyze(event));
    return;
  }
  if (request.method !== "GET") return;
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
