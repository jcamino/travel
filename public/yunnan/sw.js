/* Offline cache for this page, scoped to this folder only. Two caches: the page cache is named
   after a hash of index.html, so every build replaces it; the image cache is stable and keyed by
   the images' content-hashed file names, so an update only fetches images that changed.

   Opening the page: the worker first asks the server for build.txt (a few bytes, never cached).
   If it names this build, the cached page is shown at once; if it names a newer one, the new page
   is fetched and shown, no reload needed. No answer within WAIT ms, or offline: the cached page. */
var C = 'yunnan-4042dab18b';
var IMG = 'yunnan-img';
var PAGE = ['./', './manifest.webmanifest'];
var IMAGES = ["./img/PHOTO_03-4d696e3c.jpg", "./img/NEW_16-f96e2679.jpg", "./img/PHOTO_02-3a38f222.jpg", "./img/NEW_20-3ffc79de.jpg", "./img/NEW_04-24cd6d07.jpg", "./img/NEW_05-3f42dbf0.jpg", "./img/PHOTO_05-dfb7229a.jpg", "./img/NEW_18-afe8713b.jpg", "./img/NEW_21-802cb6ec.jpg", "./img/NEW_12-4287559f.jpg", "./img/NEW_07-063cc28d.jpg", "./img/NEW_06-ea3bb926.jpg", "./img/PHOTO_06-dae33b5a.jpg", "./img/NEW_15-fa832e6c.jpg", "./img/NEW_09-cc97eb93.jpg", "./img/PHOTO_10-8e449d73.jpg", "./img/NEW_26-138c2c5e.jpg", "./img/PHOTO_11-d6e8758c.jpg", "./img/NEW_17-32b49891.jpg", "./img/PHOTO_09-5359cf00.jpg", "./img/NEW_11-50448bb1.jpg", "./img/NEW_22-782f4d04.jpg", "./img/PHOTO_13-bf841286.jpg", "./img/NEW_13-61e4cd0e.jpg", "./img/NEW_25-ffa4f529.jpg", "./img/NEW_03-ad3ed1db.jpg", "./img/NEW_02-5a5c3359.jpg", "./img/NEW_24-c14c1b6a.jpg", "./img/NEW_08-a0f19cf2.jpg", "./img/PHOTO_15-d8a09da2.jpg", "./img/PHOTO_16-fa595ceb.jpg", "./img/NEW_01-725af3dd.jpg"];
var HIRES = ["./img/hires-NEW_20-9b2158f2.jpg", "./img/hires-NEW_21-7c6c627d.jpg", "./img/hires-NEW_26-df62bc14.jpg", "./img/hires-NEW_22-739ced55.jpg", "./img/hires-NEW_25-d2fa8f93.jpg"];     /* the full-resolution plates: fetched only when a plate is opened, then kept */
var WAIT = 1500;        /* ms to wait for build.txt before showing the cached page */
var WAIT_NEW = 6000;    /* ms to wait for a newer page once we know there is one */

function reload(u) { return new Request(u, {cache: 'reload'}); }

self.addEventListener('install', function (e) {
  self.skipWaiting();
  e.waitUntil(Promise.all([
    caches.open(C).then(function (c) { return c.addAll(PAGE.map(reload)); }),   /* bypass the HTTP cache: never precache a stale page */
    caches.open(IMG).then(function (c) {
      return Promise.all(IMAGES.map(function (u) {
        return c.match(u).then(function (hit) { return hit ? null : c.add(u).catch(function () {}); });   /* images are fetched on demand anyway */
      }));
    })
  ]));
});

self.addEventListener('activate', function (e) {
  e.waitUntil(Promise.all([
    caches.keys().then(function (k) {
      var mine = C.slice(0, C.lastIndexOf('-') + 1);   /* only this page's own old page caches */
      return Promise.all(k.map(function (n) { return (n !== C && n !== IMG && n.indexOf(mine) === 0 && /^[0-9a-f]{10}$/.test(n.slice(mine.length))) ? caches.delete(n) : null; }));
    }),
    caches.open(IMG).then(function (c) {   /* drop images this build no longer uses */
      return c.keys().then(function (reqs) {
        return Promise.all(reqs.map(function (rq) {
          var path = new URL(rq.url).pathname, keep = IMAGES.concat(HIRES).some(function (u) { return path.slice(-u.length + 1) === u.slice(1); });
          return keep ? null : c.delete(rq);
        }));
      });
    })
  ]).then(function () { return self.clients.claim(); }));
});

function timeout(ms) { return new Promise(function (_, rej) { setTimeout(function () { rej(new Error('timeout')); }, ms); }); }

/* the page itself: cached copy unless the server says there is a newer build */
function page(r, hit) {
  var check = fetch('./build.txt', {cache: 'no-store'}).then(function (res) {
    if (!res.ok) throw new Error('no build.txt');
    return res.text();
  }).then(function (b) {
    if (b.trim() === C) return hit;
    var fresh = fetch(new Request(r.url, {cache: 'no-store'})).then(function (res) {
      if (!res.ok || res.redirected) throw new Error('bad page');
      var copy = res.clone();
      caches.open(C).then(function (c) { c.put('./', copy); });
      return res;
    });
    return Promise.race([fresh, timeout(WAIT_NEW)]);
  });
  return Promise.race([check, timeout(WAIT)]).catch(function () { return hit; });
}

self.addEventListener('fetch', function (e) {
  var r = e.request, url;
  if (r.method !== 'GET') return;
  try { url = new URL(r.url); } catch (err) { return; }
  if (url.origin !== location.origin) return;
  if (r.mode === 'navigate') {
    e.respondWith(caches.match('./').then(function (hit) {
      return hit ? page(r, hit) : fetch(r);
    }));
    return;
  }
  e.respondWith(caches.match(r, {ignoreSearch: true}).then(function (hit) {
    return hit || fetch(r).then(function (res) {
      if (res && res.ok && res.type === 'basic') {
        var copy = res.clone(), isImg = /\/img\//.test(url.pathname);
        caches.open(isImg ? IMG : C).then(function (c) { c.put(r, copy); });
      }
      return res;
    });
  }));
});

/* the page asks which build the worker serves, to decide whether it needs to reload itself */
self.addEventListener('message', function (e) {
  if (e.data && e.data.type === 'build' && e.ports && e.ports[0]) e.ports[0].postMessage({build: C});
});
