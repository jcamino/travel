/* Offline cache for this page, scoped to this folder only. Two caches: the page cache is named
   after a hash of index.html, so every build replaces it; the image cache is stable and keyed by
   the images' content-hashed file names, so an update only fetches images that changed. */
var C = 'yunnan-4996bcc31b';
var IMG = 'yunnan-img';
var PAGE = ['./', './index.html', './manifest.webmanifest'];
var IMAGES = ["./img/PHOTO_03-4d696e3c.jpg", "./img/NEW_16-f96e2679.jpg", "./img/PHOTO_02-3a38f222.jpg", "./img/NEW_20-3ffc79de.jpg", "./img/NEW_04-24cd6d07.jpg", "./img/NEW_05-3f42dbf0.jpg", "./img/PHOTO_05-dfb7229a.jpg", "./img/NEW_18-afe8713b.jpg", "./img/NEW_21-802cb6ec.jpg", "./img/NEW_12-4287559f.jpg", "./img/NEW_07-063cc28d.jpg", "./img/NEW_06-ea3bb926.jpg", "./img/PHOTO_06-dae33b5a.jpg", "./img/NEW_15-fa832e6c.jpg", "./img/NEW_09-cc97eb93.jpg", "./img/PHOTO_10-8e449d73.jpg", "./img/NEW_26-138c2c5e.jpg", "./img/PHOTO_11-d6e8758c.jpg", "./img/NEW_17-32b49891.jpg", "./img/PHOTO_09-5359cf00.jpg", "./img/NEW_11-50448bb1.jpg", "./img/NEW_22-782f4d04.jpg", "./img/PHOTO_13-bf841286.jpg", "./img/NEW_13-61e4cd0e.jpg", "./img/NEW_25-ffa4f529.jpg", "./img/NEW_03-ad3ed1db.jpg", "./img/NEW_02-5a5c3359.jpg", "./img/NEW_24-c14c1b6a.jpg", "./img/NEW_08-a0f19cf2.jpg", "./img/PHOTO_15-d8a09da2.jpg", "./img/PHOTO_16-fa595ceb.jpg", "./img/NEW_01-725af3dd.jpg"];

self.addEventListener('install', function (e) {
  e.waitUntil(Promise.all([
    caches.open(C).then(function (c) { return c.addAll(PAGE); }),
    caches.open(IMG).then(function (c) {
      return Promise.all(IMAGES.map(function (u) {
        return c.match(u).then(function (hit) { return hit ? null : c.add(u); });
      }));
    })
  ]).then(function () { return self.skipWaiting(); }).catch(function () {}));
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
          var path = new URL(rq.url).pathname, keep = IMAGES.some(function (u) { return path.slice(-u.length + 1) === u.slice(1); });
          return keep ? null : c.delete(rq);
        }));
      });
    })
  ]).then(function () { return self.clients.claim(); }));
});

self.addEventListener('fetch', function (e) {
  var r = e.request, url;
  if (r.method !== 'GET') return;
  try { url = new URL(r.url); } catch (err) { return; }
  if (url.origin !== location.origin) return;
  e.respondWith(caches.match(r, {ignoreSearch: true}).then(function (hit) {
    return hit || fetch(r).then(function (res) {
      if (res && res.ok && res.type === 'basic') {
        var copy = res.clone(), isImg = /\/img\//.test(url.pathname);
        caches.open(isImg ? IMG : C).then(function (c) { c.put(r, copy); });
      }
      return res;
    }).catch(function () {
      return r.mode === 'navigate' ? caches.match('./index.html') : Response.error();
    });
  }));
});
