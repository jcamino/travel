/* Offline cache for this page, scoped to this folder only. Two caches: the page cache is named
   after a hash of index.html, so every build replaces it; the image cache is stable and keyed by
   the images' content-hashed file names, so an update only fetches images that changed.

   Opening the page: the worker first asks the server for build.txt (a few bytes, never cached).
   If it names this build, the cached page is shown at once; if it names a newer one, the new page
   is fetched and shown, no reload needed. No answer within WAIT ms, or offline: the cached page. */
var C = 'yunnan-ea14d263a9';
var IMG = 'yunnan-img';
var PAGE = ['./', './manifest.webmanifest'];
var IMAGES = ["./img/NEW_28-7eece22f.webp", "./img/NEW_27-d26ca027.webp", "./img/NEW_29-d7c38418.webp", "./img/NEW_20-e8a0f2ac.webp", "./img/NEW_04-bcbb857e.webp", "./img/NEW_05-6352f5c5.webp", "./img/PHOTO_05-28ca7238.webp", "./img/NEW_18-f2033037.webp", "./img/NEW_21-698424ea.webp", "./img/NEW_12-cd3fbd30.webp", "./img/NEW_07-793be841.webp", "./img/NEW_06-7e130a5d.webp", "./img/NEW_30-11323114.webp", "./img/NEW_15-22cd0e46.webp", "./img/NEW_09-6673f6b9.webp", "./img/NEW_31-831d14c5.webp", "./img/NEW_26-f7dd39e2.webp", "./img/PHOTO_11-a05f2be9.webp", "./img/NEW_17-e6a131fe.webp", "./img/NEW_32-25249f62.webp", "./img/NEW_35-48ac7c6f.webp", "./img/NEW_22-b8ac8a82.webp", "./img/NEW_36-d2734325.webp", "./img/NEW_37-c09d79b8.webp", "./img/NEW_13-1af9e1c0.webp", "./img/NEW_25-19639e45.webp", "./img/NEW_03-3e125c8b.webp", "./img/NEW_34-79adec9f.webp", "./img/NEW_24-79e3d08a.webp", "./img/NEW_33-a711be91.webp", "./img/PHOTO_15-ac50b535.webp", "./img/PHOTO_16-fce113b3.webp", "./img/NEW_01-e5ae31a5.webp"];
var HIRES = ["./img/hires-NEW_20-9b2158f2.jpg", "./img/hires-NEW_21-7c6c627d.jpg", "./img/hires-NEW_26-df62bc14.jpg", "./img/hires-NEW_22-739ced55.jpg", "./img/hires-NEW_25-d2fa8f93.jpg", "./img/GAL_07-0e96386a.webp", "./img/PHOTO_04-21956eea.webp", "./img/GAL_02-bee954bb.webp", "./img/GAL_01-c4e2752e.webp", "./img/PHOTO_07-fb4982a5.webp", "./img/PHOTO_08-6b4b7773.webp", "./img/GAL_03-a131e661.webp", "./img/PHOTO_12-1e717500.webp", "./img/PHOTO_09-7f856a59.webp", "./img/GAL_04-ff014b4b.webp", "./img/GAL_05-f025fab3.webp", "./img/PHOTO_14-4537572c.webp", "./img/PHOTO_13-55782a6d.webp", "./img/GAL_06-00c0f3c3.webp", "./img/NEW_08-0b012f16.webp"];     /* the full-resolution plates: fetched only when a plate is opened, then kept */
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
