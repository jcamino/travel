#!/usr/bin/env python3
"""Tier A build gate for the Yunnan page (Fourteen Nights).

usage: python3 tests/yunnan/check.py [public/yunnan]

Static invariants over the files assemble.py wrote: the build id triad, the image inventory against
the worker's precache lists, the manifest, the link-preview tags, text hygiene, the fifteen day cards
and their dates, every internal target, nothing private, size budgets, names and alt text, the worker,
and the CSS rules that have silently vanished before. Standard library only; no browser.
Prints one line per check and exits 1 if any failed.
"""
import datetime
import html as htmlmod
import json
import os
import re
import shutil
import struct
import subprocess
import sys
import urllib.parse

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FOLDER = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "public", "yunnan"))
NAME = os.path.basename(FOLDER)

T0 = datetime.date(2026, 9, 24)      # night I
NDAYS = 15
HTML_BUDGET = 450 * 1024             # bytes
PRECACHE_MB = 8.0                    # what a phone warms for offline after the first open, on hotel wifi
OG_BUDGET = 300 * 1024

fails = []


def ok(cid, msg):
    print(f"ok   {cid:<4} {msg}")


def fail(cid, msg, detail=""):
    fails.append(cid)
    print(f"FAIL {cid:<4} {msg}" + (f": {detail}" if detail else ""))


def check(cid, cond, msg, detail=""):
    (ok if cond else lambda c, m: fail(c, m, detail))(cid, msg)


def read(name, mode="r"):
    p = os.path.join(FOLDER, name)
    if not os.path.exists(p):
        return None
    if mode == "rb":
        return open(p, "rb").read()
    return open(p, encoding="utf-8", newline="").read()


def jpeg_size(b):
    """(width, height) from a JPEG's first SOF marker, or None."""
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


def date_label(d):
    return f"{d.strftime('%a')} {d.day} {d.strftime('%b')}"


# ---------------------------------------------------------------- files
raw = read("index.html", "rb")
if raw is None:
    print(f"no index.html under {FOLDER}")
    sys.exit(2)
try:
    html = raw.decode("utf-8")
    utf8_ok = True
except UnicodeDecodeError as e:
    html = raw.decode("utf-8", "replace")
    utf8_ok = False
sw = read("sw.js") or ""
build_txt = (read("build.txt") or "").strip()
manifest_txt = read("manifest.webmanifest")
og = read("og.jpg", "rb")

head = html[:html.find("</head>")]
scripts = "\n".join(re.findall(r"<script\b[^>]*>(.*?)</script>", html, re.S))
css = "\n".join(re.findall(r"<style\b[^>]*>(.*?)</style>", html, re.S))
markup = re.sub(r"<script\b[^>]*>.*?</script>|<style\b[^>]*>.*?</style>", "", html, flags=re.S)
text = htmlmod.unescape(re.sub(r"<[^>]+>", " ", markup))


def js_list(name):
    m = re.search(r"var %s = (\[.*?\]);" % name, sw, re.S)
    return [u[2:] if u.startswith("./") else u for u in json.loads(m.group(1).replace("'", '"'))] if m else None


# ---------------------------------------------------------------- A1 build id triad
meta_build = re.search(r'<meta name="build" content="([^"]+)"', head)
sw_build = re.search(r"var C = '([^']+)'", sw)
triad = (meta_build.group(1) if meta_build else None, build_txt or None, sw_build.group(1) if sw_build else None)
check("A1", all(triad) and len(set(triad)) == 1, f"build id agrees in meta, build.txt and sw.js ({triad[1]})", f"meta={triad[0]} build.txt={triad[1]} sw={triad[2]}")
check("A1", bool(re.fullmatch(NAME + r"-[0-9a-f]{10}", build_txt)), f"build id is {NAME}-<10 hex>", build_txt)

# ---------------------------------------------------------------- A2 image inventory
img_dir = os.path.join(FOLDER, "img")
refs = set(re.findall(r"\bimg/[A-Za-z0-9_.-]+", html))
disk = set("img/" + f for f in os.listdir(img_dir)) if os.path.isdir(img_dir) else set()
IMAGES, HIRES = js_list("IMAGES") or [], js_list("HIRES") or []
precache, ondemand = set(IMAGES), set(HIRES)
check("A2", refs <= disk, f"every referenced image exists ({len(refs)} references)", "missing " + ", ".join(sorted(refs - disk)[:5]))
check("A2", disk <= refs, "no unreferenced file under img/", "orphans " + ", ".join(sorted(disk - refs)[:5]))
check("A2", refs == precache | ondemand, "sw.js IMAGES + HIRES is exactly the referenced set",
      f"not in sw {sorted(refs - precache - ondemand)[:4]}; sw only {sorted((precache | ondemand) - refs)[:4]}")
check("A2", not (precache & ondemand), "no file is both in IMAGES and in HIRES", ", ".join(sorted(precache & ondemand)[:5]))
# every picture: a WebP per width in srcset (or data-srcset in a folded gallery), data-full the largest, sizes set, one JPEG twin with the same stem
main_files, gal_files, pictures, twin_bad, srcset_bad, phone_set = set(), set(), 0, [], [], []
for tag in re.findall(r"<img\b[^>]*>", markup):
    files = set(re.findall(r"img/[A-Za-z0-9_.-]+", tag))
    if not files:
        continue
    pictures += 1
    (gal_files if "data-src=" in tag else main_files).update(files)
    jpg = re.search(r'data-jpg="img/([^"]+)\.jpg"', tag)
    stem = jpg.group(1) if jpg else None
    if not stem or any(not re.fullmatch(re.escape(stem) + r"(-\d+)?\.(webp|jpg)", f[4:]) for f in files):
        twin_bad.append(tag[:50])
    ss = re.search(r'\b(?:data-)?srcset="([^"]+)"', tag)
    if ss:
        cands = [(c.split()[0], int(c.split()[1].rstrip("w"))) for c in ss.group(1).split(",")]
        widths = [w for _, w in cands]
        full = re.search(r'data-full="([^"]+)"', tag)
        if widths != sorted(widths) or " sizes=" not in tag or not full or full.group(1) != cands[-1][0]:
            srcset_bad.append(tag[:50])
        if "data-src=" not in tag:      # what a 390 px phone at 2x picks: the smallest candidate that covers about 700 device pixels
            phone_set.append(next((u for u, w in cands if w >= 700), cands[-1][0]))
    else:
        srcset_bad.append(tag[:50])
hires = set(re.findall(r'data-hires="(img/[^"]+)"', markup))
check("A2", main_files <= precache, f"every file of the {len(phone_set)} pictures on the page is in IMAGES", ", ".join(sorted(main_files - precache)[:4]))
check("A2", (gal_files | hires) <= ondemand, f"every gallery file and full-resolution plate is in HIRES ({len(gal_files | hires)} files)", ", ".join(sorted((gal_files | hires) - ondemand)[:4]))
check("A2", pictures and not twin_bad, f"every picture's files share one stem with its JPEG twin ({pictures} pictures)", "; ".join(twin_bad[:3]))
check("A2", not srcset_bad, "every picture has ascending srcset widths, a sizes attribute and data-full = the largest", "; ".join(srcset_bad[:3]))
check("A2", og is not None, "og.jpg exists")

# ---------------------------------------------------------------- A3 manifest
inline_m = re.search(r'<link rel="manifest" href="data:application/manifest\+json;charset=utf-8,([^"]+)"', head)
inline_json = hosted_json = None
try:
    inline_json = json.loads(urllib.parse.unquote(inline_m.group(1))) if inline_m else None
    hosted_json = json.loads(manifest_txt) if manifest_txt else None
except ValueError as e:
    fail("A3", "manifest parses", str(e))
check("A3", inline_json is not None and inline_json == hosted_json, "inline manifest equals manifest.webmanifest")
if hosted_json:
    sizes = {i.get("sizes") for i in hosted_json.get("icons", [])}
    check("A3", hosted_json.get("start_url") == "." and hosted_json.get("scope") == ".", "manifest start_url and scope are '.'")
    check("A3", hosted_json.get("id") == f"{NAME}-2026" and hosted_json.get("display") == "standalone" and hosted_json.get("lang") == "en",
          f"manifest id {NAME}-2026, standalone, lang en", str({k: hosted_json.get(k) for k in ("id", "display", "lang")}))
    check("A3", {"192x192", "512x512"} <= sizes, "manifest carries 192 and 512 icons", str(sizes))
    icon_bad = []
    for icon in hosted_json.get("icons", []):
        src = icon.get("src", "")
        if src.startswith("data:"):
            continue
        b = read(src, "rb")
        dims = struct.unpack(">II", b[16:24]) if b and b[:8] == b"\x89PNG\r\n\x1a\n" else None
        if not dims or "%dx%d" % dims != icon.get("sizes"):
            icon_bad.append(f"{src} {dims} vs {icon.get('sizes')}")
    check("A3", not icon_bad, "every icon file exists as a PNG of the size the manifest claims", "; ".join(icon_bad))
    check("A3", bool(hosted_json.get("name")) and bool(hosted_json.get("description")), "manifest name and description filled")

# ---------------------------------------------------------------- A4 link preview
first4k = raw[:4096].decode("utf-8", "replace")
for tag in ("og:title", "og:description", "og:image", "og:url", "og:image:width", "og:image:height", "twitter:card", "twitter:image"):
    check("A4", f'"{tag}"' in first4k, f"{tag} within the first 4 KB")
og_image = re.search(r'property="og:image" content="([^"]+)"', head)
check("A4", og_image and og_image.group(1).startswith("https://") and og_image.group(1).endswith(f"/{NAME}/og.jpg"), "og:image is an absolute https URL to og.jpg",
      og_image.group(1) if og_image else "none")
og_url = re.search(r'property="og:url" content="([^"]+)"', head)
check("A4", og_url and og_url.group(1).endswith(f"/{NAME}/"), f"og:url ends with /{NAME}/", og_url.group(1) if og_url else "none")
w = re.search(r'property="og:image:width" content="(\d+)"', head)
h = re.search(r'property="og:image:height" content="(\d+)"', head)
dims = jpeg_size(og) if og else None
check("A4", dims == (1200, 630) and w and h and (int(w.group(1)), int(h.group(1))) == dims, "og.jpg is 1200x630 and the tags say so", f"file {dims}")
check("A4", 'card" content="summary_large_image"' in head, "twitter:card is summary_large_image")
check("A4", bool(re.search(r"<title>[^<]+</title>", head)) and bool(re.search(r'<meta name="description" content="[^"]{20,}"', head)), "title and description present")

# ---------------------------------------------------------------- A5 hygiene
check("A5", utf8_ok, "index.html is valid UTF-8")
check("A5", "\r" not in html, "LF line endings only")
leftover = re.findall(r"\{\{[A-Z_0-9]+\}\}", html)
check("A5", not leftover, "no leftover {{TOKEN}}", ", ".join(leftover[:5]))
bad_words = re.findall(r"\b(undefined|NaN|lorem ipsum|TODO|FIXME)\b", text)
check("A5", not bad_words, "no 'undefined', 'NaN', 'lorem', TODO in visible text", ", ".join(bad_words[:5]))
stray_amp = re.findall(r"&(?![a-zA-Z][a-zA-Z0-9]*;|#\d+;|#x[0-9a-fA-F]+;)", markup)
check("A5", not stray_amp, "every & in the markup is an entity", f"{len(stray_amp)} stray")

# ---------------------------------------------------------------- A6 fifteen days
cards = re.findall(r'<li class="day( dawn)?" id="day-(\d+)" data-day="(\d+)">', markup)
check("A6", [int(n) for _, n, _ in cards] == list(range(1, NDAYS + 1)) and all(n == d for _, n, d in cards), f"day-1 … day-{NDAYS} present once each, in order",
      str([n for _, n, _ in cards]))
check("A6", all((dawn == " dawn") == (int(n) == 15) for dawn, n, _ in cards), "only day 15 is the dawn card")
starts = [m.start() for m in re.finditer(r'<li class="day(?: dawn)?" id="day-\d+"', markup)] + [len(markup)]
cards_ok = True
for k, (dawn, n, _) in enumerate(cards):
    n = int(n)
    block = markup[starts[k]:starts[k + 1]]
    end = block.find("</section>")
    if end > 0:
        block = block[:end]
    parts = {
        "dnum": 'class="dnum"' in block, "astro": f'class="astro" data-day="{n}"' in block, "h3": "<h3>" in block,
        "wx": f'class="wx" data-day="{n}"' in block, "log": f'class="log" data-day="{n}"' in block,
        "input": f'<input id="log{n}"' in block and 'maxlength="110"' in block, "label": f'<label for="log{n}"' in block, "msg": 'class="msg"' in block,
        "button": "<button" in block,
    }
    missing = [p for p, v in parts.items() if not v]
    if missing:
        cards_ok = False
        fail("A6", f"day {n} card complete", "missing " + ", ".join(missing))
    m = re.search(r'<span class="dnum">Day (\d+)(?: &middot; Shanghai)? <span class="dd">&middot; ([^<]+)</span>', block)
    want = date_label(T0 + datetime.timedelta(days=n - 1))
    if not m or int(m.group(1)) != n or htmlmod.unescape(m.group(2)).strip() != want:
        cards_ok = False
        fail("A6", f"day {n} card is dated {want}", m.group(0)[:80] if m else "no dnum")
if cards_ok:
    ok("A6", "every day card has its number, date, sky line, title, weather, log, label and Postcard")
js_days = re.findall(r'\{n:(\d+),\s*d:"([^"]+)",\s*place:"([^"]+)",\s*stop:"([^"]+)",\s*alt:(\d+)', scripts)
bad_js = [(n, d) for n, d, *_ in js_days if d != date_label(T0 + datetime.timedelta(days=int(n) - 1))]
check("A6", len(js_days) == NDAYS and not bad_js, "the JS DAYS table has 15 entries with the right weekdays", str(bad_js[:3] or len(js_days)))
check("A6", "DAY 1 &middot; THU 24 SEP" in markup, "the bar starts on DAY 1 · THU 24 SEP")

# ---------------------------------------------------------------- A7 internal targets
ids = set(re.findall(r'\sid="([^"]+)"', markup))
gos = set(re.findall(r'data-go="(\d+)"', markup))
check("A7", all(f"day-{g}" in ids for g in gos), f"every data-go points at a day card ({len(gos)} links)", str([g for g in gos if f"day-{g}" not in ids]))
for attr in ("aria-controls", "for", "aria-labelledby"):
    vals = re.findall(rf'\s{attr}="([^"]+)"', markup)
    miss = [v for v in vals if v not in ids]
    check("A7", not miss, f"every {attr} resolves ({len(vals)})", ", ".join(miss[:5]))
anchors = re.findall(r'href="#([^"]+)"', markup)
miss = [a for a in anchors if a not in ids]
check("A7", not miss, f"every #anchor resolves ({len(anchors)})", ", ".join(miss[:5]))
sections = re.findall(r'<section class="chapter" id="ch(\d+)" data-ch="(\d+)" data-first="(\d+)" data-last="(\d+)"', markup)
ranges = [(int(f), int(l)) for _, _, f, l in sections]
tiles = ranges and ranges[0][0] == 1 and ranges[-1][1] == NDAYS and all(ranges[i][1] + 1 == ranges[i + 1][0] for i in range(len(ranges) - 1))
check("A7", len(sections) == 7 and [int(a) for a, b, *_ in sections] == list(range(7)) and tiles, "chapters ch0 … ch6 tile days 1 … 15", str(ranges))
js_ch = [(int(a), int(b)) for a, b in re.findall(r"\{first:(\d+),\s*last:(\d+),", scripts)]
check("A7", js_ch == ranges, "the JS CH table matches the chapter sections", f"js {js_ch}")
postcard = dict((int(k), v) for k, v in re.findall(r'(\d+):"([A-Z_0-9]+)"', re.search(r"var POSTCARD = \{(.*?)\};", scripts, re.S).group(1))) if "var POSTCARD" in scripts else {}
loaded_toks = set(re.findall(r'<img\b[^>]*\ssrc="img/[^"]+"[^>]*data-tok="([^"]+)"', markup))
miss = [n for n in range(1, NDAYS + 1) if postcard.get(n) not in loaded_toks]
check("A7", len(postcard) == NDAYS and not miss, "every night's postcard picture is a loaded (not gallery) picture", f"nights {miss}")

# ---------------------------------------------------------------- A8 nothing private
private = []
private += re.findall(r"[\w.+-]+@[\w-]+\.[\w.-]+", text)
private += re.findall(r"(?<![\d,.:])\d{9,}(?![\d,.:])", text)
private += re.findall(r"(?i)\b(confirmation (?:code|number)|booking ref\w*|reservation code|password|voucher)\b", markup)
private += re.findall(r"[A-Z]:\\Users", html)
check("A8", not private, "no e-mail, long number, confirmation code or local path", ", ".join(map(str, private[:5])))

# ---------------------------------------------------------------- A9 budgets
def mb(paths):
    return sum(os.path.getsize(os.path.join(FOLDER, p)) for p in paths if os.path.exists(os.path.join(FOLDER, p))) / 1048576


phone_mb, all_mb, hi_mb = mb(phone_set), mb(IMAGES), mb(HIRES)
check("A9", len(raw) <= HTML_BUDGET, f"index.html {len(raw) // 1024} KB ≤ {HTML_BUDGET // 1024} KB")
check("A9", phone_mb <= PRECACHE_MB, f"what a phone warms for offline: {phone_mb:.1f} MB in {len(phone_set)} files ≤ {PRECACHE_MB:.0f} MB")
ok("A9", f"all picture files {all_mb:.1f} MB in {len(IMAGES)}, galleries and plates {hi_mb:.1f} MB in {len(HIRES)} (fetched only as used; no budget)")
check("A9", og is not None and len(og) <= OG_BUDGET, f"og.jpg {len(og or b'') // 1024} KB ≤ {OG_BUDGET // 1024} KB")

# ---------------------------------------------------------------- A10 names and alt text
imgs = re.findall(r"<img\b[^>]*>", markup)
check("A10", all(" alt=" in i for i in imgs), f"every img has alt ({len(imgs)})", f"{sum(' alt=' not in i for i in imgs)} without")
gal_imgs = [i for i in imgs if "data-src=" in i]
check("A10", gal_imgs and all(all(a in i for a in ("data-jpg=", " alt=", " width=", " height=")) for i in gal_imgs), f"gallery pictures carry data-jpg, alt, width, height ({len(gal_imgs)})")
unnamed = []
for m in re.finditer(r"<button\b([^>]*)>(.*?)</button>", markup, re.S):
    attrs, inner = m.group(1), re.sub(r"<[^>]+>", "", m.group(2)).strip()
    if not inner and "aria-label" not in attrs and " hidden" not in attrs:
        unnamed.append(m.group(0)[:60])
check("A10", not unnamed, f"every button has a name ({len(re.findall('<button', markup))})", "; ".join(unnamed[:3]))
ext = re.findall(r'<a\b[^>]*href="https?://[^>]*>', markup)
check("A10", all("noopener" in a for a in ext), f"every external link has rel=noopener ({len(ext)})", f"{sum('noopener' not in a for a in ext)} without")
check("A10", bool(re.search(r'<html[^>]*\slang="[a-z]{2}', html)), "html has lang")
check("A10", 'role="dialog"' in markup and 'aria-modal="true"' in markup, "the lightbox is a modal dialog")
check("A10", bool(re.search(r'<nav class="bar" id="bar" aria-label="', markup)), "the bar is a labelled nav")

# ---------------------------------------------------------------- A11 worker
if shutil.which("node"):
    r = subprocess.run(["node", "--check", os.path.join(FOLDER, "sw.js")], capture_output=True, text=True)
    check("A11", r.returncode == 0, "sw.js parses (node --check)", r.stderr.strip()[:200])
else:
    ok("A11", "sw.js parse check skipped (no node on PATH)")
sw_code = re.sub(r"/\*.*?\*/", "", sw, flags=re.S)
check("A11", not re.search(r"https?://", sw_code), "sw.js has no absolute URLs")
page_list = js_list("PAGE") or []
check("A11", "./" in ["./" + p if not p.startswith("./") else p for p in page_list] or "" in page_list, "sw.js precaches './' (the page)")
check("A11", any(p.endswith("manifest.webmanifest") for p in page_list), "sw.js precaches the manifest")
wait = re.search(r"var WAIT = (\d+)", sw)
wait_new = re.search(r"var WAIT_NEW = (\d+)", sw)
check("A11", wait and wait_new and 500 <= int(wait.group(1)) <= 10000 and int(wait_new.group(1)) >= int(wait.group(1)), "WAIT within 0.5–10 s and WAIT_NEW ≥ WAIT",
      f"{wait and wait.group(1)} / {wait_new and wait_new.group(1)}")
check("A11", all(f"e.data.type === '{t}'" in sw for t in ("build", "prune", "warm")), "worker answers 'build', 'prune' and 'warm' messages")
check("A11", 'type: "warm"' in scripts and "function pickFor" in scripts, "the page asks the worker to warm the files this screen uses")
check("A11", 'register("sw.js", {scope: "./"})' in scripts, "the page registers sw.js with scope ./")
check("A11", "cache: 'no-store'" in sw and "./build.txt" in sw, "worker polls build.txt with no-store")

# ---------------------------------------------------------------- A12 CSS invariants
rules = {
    "@media print": "@media print{" in css,
    "prefers-reduced-motion": "@media (prefers-reduced-motion:reduce){" in css,
    "touch-action on everything": bool(re.search(r"html,body[^{]*\{touch-action:manipulation\}", css)),
    ".day scroll-margin-top": bool(re.search(r"\n\.day\{[^}]*scroll-margin-top", css)),
    "html scroll-padding-bottom clears the bar": bool(re.search(r"\nhtml\{[^}]*scroll-padding-bottom:calc\(var\(--barh\)", css)),
    ".cn-only hidden by default": ".cn-only{display:none}" in css,
    "html.cn shows .cn-only": bool(re.search(r"html\.cn \.cn-only\{display:inline", css)),
    "html.cn hides .intl-only": "html.cn .intl-only{display:none}" in css,
    ".log rule": bool(re.search(r"\n\.log\{", css)),
    ".log-row rule": bool(re.search(r"\n\.log-row\{display:flex", css)),
    ".pair grid": bool(re.search(r"\n\.pair\{display:grid", css)),
    ".lb-cap bounded": bool(re.search(r"\.lb-cap\{[^}]*max-height", css)),
    ".win.plate keeps its ratio": bool(re.search(r"\.win\.plate \.photo img\{aspect-ratio:var\(--ar\)", css)),
    "safe-area inset on the bar": "env(safe-area-inset-bottom)" in css,
}
phone = "\n".join(re.findall(r"@media \(max-width:599px\)\{(.*?)\n\}", css, re.S))
rules["pairs stack on phones"] = bool(re.search(r"\.pair\{grid-template-columns:1fr\}", phone))
rules["paired pictures whole on phones"] = ".pair .win .photo img{aspect-ratio:var(--ar)" in phone
gone = [k for k, v in rules.items() if not v]
check("A12", not gone, f"{len(rules)} CSS rules that have vanished before are all present", ", ".join(gone))

# ---------------------------------------------------------------- done
print()
if fails:
    print(f"{len(fails)} check(s) failed: {', '.join(sorted(set(fails)))}")
    sys.exit(1)
print(f"all checks passed for {NAME} build {build_txt}")
