#!/usr/bin/env python3
"""Tier D: three requests against the live site after a deploy.

usage: python3 tests/yunnan/smoke.py [https://travel.jcamino.net/yunnan/] [public/yunnan]

D1 build.txt is live and equals the committed build id, with a cache-control an edge will honour.
D2 sw.js and manifest.webmanifest are served with the right types; /yunnan redirects to /yunnan/.
D3 og.jpg is a 1200x630 JPEG under 300 KB.
Standard library only. Exits 1 on any failure.
"""
import os
import re
import struct
import sys
import urllib.error
import urllib.request

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BASE = (sys.argv[1] if len(sys.argv) > 1 else "https://travel.jcamino.net/yunnan/").rstrip("/") + "/"
FOLDER = os.path.abspath(sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, "public", "yunnan"))
fails = []


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


opener = urllib.request.build_opener(NoRedirect)


def get(url, method="GET"):
    req = urllib.request.Request(url, method=method, headers={"User-Agent": "fourteen-nights-smoke/1", "Cache-Control": "no-cache"})
    try:
        with opener.open(req, timeout=20) as r:
            return r.status, dict((k.lower(), v) for k, v in r.headers.items()), r.read()
    except urllib.error.HTTPError as e:
        return e.code, dict((k.lower(), v) for k, v in e.headers.items()), b""
    except Exception as e:
        return 0, {"error": str(e)}, b""


def check(cid, cond, msg, detail=""):
    if cond:
        print(f"ok   {cid:<3} {msg}")
    else:
        fails.append(cid)
        print(f"FAIL {cid:<3} {msg}" + (f": {detail}" if detail else ""))


def jpeg_size(b):
    i = 2
    while i + 4 <= len(b):
        if b[i] != 0xFF:
            return None
        marker = b[i + 1]
        i += 2
        if marker in (0x01, 0xD8) or 0xD0 <= marker <= 0xD7:
            continue
        length = struct.unpack(">H", b[i:i + 2])[0]
        if marker in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
            h, w = struct.unpack(">HH", b[i + 3:i + 7])
            return w, h
        i += length
    return None


local = open(os.path.join(FOLDER, "build.txt"), encoding="utf-8").read().strip()

s, hd, body = get(BASE + "build.txt")
live = body.decode("utf-8", "replace").strip()
check("D1", s == 200 and live == local, f"build.txt is live and equals the committed {local}", f"status {s}, live '{live}'")
cc = hd.get("cache-control", "")
check("D1", s == 200 and (not re.search(r"max-age=(\d+)", cc) or int(re.search(r"max-age=(\d+)", cc).group(1)) <= 300 or "no-cache" in cc or "must-revalidate" in cc),
      f"build.txt cache-control lets an edge revalidate ({cc or 'none'})")

s, hd, body = get(BASE + "sw.js")
check("D2", s == 200 and "javascript" in hd.get("content-type", "") and f"var C = '{local}'" in body.decode("utf-8", "replace"),
      "sw.js served as JavaScript on the same build", f"status {s}, type {hd.get('content-type')}")
s, hd, body = get(BASE + "manifest.webmanifest")
check("D2", s == 200 and ("manifest" in hd.get("content-type", "") or "json" in hd.get("content-type", "")) and b'"start_url"' in body,
      "manifest served as JSON", f"status {s}, type {hd.get('content-type')}")
s, hd, _ = get(BASE.rstrip("/"))
check("D2", s in (301, 302, 307, 308) and hd.get("location", "").rstrip("/").endswith(BASE.rstrip("/").split("//", 1)[1].split("/", 1)[1]),
      f"/{BASE.rstrip('/').rsplit('/', 1)[1]} redirects to the folder", f"status {s}, location {hd.get('location')}")

s, hd, body = get(BASE + "og.jpg")
check("D3", s == 200 and "image/jpeg" in hd.get("content-type", "") and jpeg_size(body) == (1200, 630) and len(body) <= 300 * 1024,
      f"og.jpg is a 1200x630 JPEG under 300 KB ({len(body) // 1024} KB)", f"status {s}, type {hd.get('content-type')}, size {jpeg_size(body)}")

print()
if fails:
    print(f"{len(fails)} check(s) failed")
    sys.exit(1)
print(f"live site serves build {live}")
