/* Yunnan page, offline cache. Scope is this folder only, so no other page
   on the site is affected. The cache name carries a hash of index.html:
   publishing a new build changes this file, which is what tells the browser
   to fetch the new page instead of serving the old one forever. */
var C = 'yunnan-879ef3a96b';
var ASSETS = ['./', './index.html', './manifest.webmanifest'];

self.addEventListener('install', function (e) {
  e.waitUntil(caches.open(C).then(function (c) { return c.addAll(ASSETS); })
    .then(function () { return self.skipWaiting(); }).catch(function () {}));
});

self.addEventListener('activate', function (e) {
  e.waitUntil(caches.keys().then(function (k) {
    return Promise.all(k.map(function (n) { return n === C ? null : caches.delete(n); }));
  }).then(function () { return self.clients.claim(); }));
});

self.addEventListener('fetch', function (e) {
  var r = e.request, url;
  if (r.method !== 'GET') return;
  try { url = new URL(r.url); } catch (err) { return; }
  if (url.origin !== location.origin) return;
  e.respondWith(caches.match(r, {ignoreSearch: true}).then(function (hit) {
    return hit || fetch(r).then(function (res) {
      if (res && res.ok && res.type === 'basic') {
        var copy = res.clone();
        caches.open(C).then(function (c) { c.put(r, copy); });
      }
      return res;
    }).catch(function () {
      return r.mode === 'navigate' ? caches.match('./index.html') : Response.error();
    });
  }));
});
