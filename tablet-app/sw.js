/* Offline cache for the tablet PWA — study data stays in IndexedDB/localStorage. */
const CACHE = "srt-tablet-v3";

// Resolve every asset relative to this service worker (works on GitHub Pages subpaths).
const BASE = self.location.href.replace(/sw\.js(?:\?.*)?$/, "");
const ASSETS = [
  "",
  "index.html",
  "css/app.css",
  "js/db.js",
  "js/logic.js",
  "js/garden.js",
  "js/app.js",
  "manifest.webmanifest",
  "icons/icon.svg",
  "icons/icon-192.png",
  "icons/icon-512.png",
].map((path) => new URL(path, BASE).href);

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches
      .open(CACHE)
      .then((cache) => cache.addAll(ASSETS))
      .then(() => self.skipWaiting())
      .catch(() => self.skipWaiting())
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (event) => {
  const req = event.request;
  if (req.method !== "GET") return;

  event.respondWith(
    caches.match(req).then((cached) => {
      const network = fetch(req)
        .then((res) => {
          if (res && res.ok && req.url.startsWith(self.location.origin)) {
            const copy = res.clone();
            caches.open(CACHE).then((cache) => cache.put(req, copy));
          }
          return res;
        })
        .catch(() => cached || caches.match(new URL("index.html", BASE).href));
      return cached || network;
    })
  );
});
