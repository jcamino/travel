/* Offline copy of /japan/ only. Nothing external (fonts, maps) is cached.
   Navigations to /japan/ go network-first and fall back to the cached page. */
var C = 'japan-guide-v1';
var PAGE = '/japan/';
self.addEventListener('install', function (e) {
  self.skipWaiting();
  e.waitUntil(caches.open(C).then(function (c) { return c.add(new Request(PAGE, { cache: 'reload' })); }));
});
self.addEventListener('activate', function (e) {
  e.waitUntil(caches.keys().then(function (keys) {
    return Promise.all(keys.filter(function (k) { return k.indexOf('japan-guide-') === 0 && k !== C; }).map(function (k) { return caches.delete(k); }));
  }).then(function () { return self.clients.claim(); }));
});
self.addEventListener('fetch', function (e) {
  var url = new URL(e.request.url);
  if (url.origin !== location.origin || url.pathname !== PAGE) return;
  e.respondWith(fetch(e.request).then(function (r) {
    if (r && r.ok) { var copy = r.clone(); caches.open(C).then(function (c) { c.put(PAGE, copy); }); }
    return r;
  }).catch(function () { return caches.match(PAGE); }));
});
