#!/usr/bin/env python3
"""Tier B browser regression for the Yunnan page (Fourteen Nights).

usage: python3 tests/yunnan/ux_test.py [-k pattern] [--all] [--update-golden] [--headed] [-v]

Serves public/ over http://127.0.0.1 from a thread so the worker can register, pins the clock, the
timezone and the network per test, mocks Open-Meteo with a generated fixture, and walks the page in
Chromium at phone, tablet and wide sizes. The core set runs by default; --all adds the extended checks.
Check IDs (B1 … B20) match the proposal and README.
"""
import argparse
import datetime
import functools
import http.server
import json
import os
import re
import shutil
import sys
import tempfile
import threading
import time
import unittest

from playwright.sync_api import expect, sync_playwright

try:
    from PIL import Image
except ImportError:      # the postcard pixel checks are skipped without Pillow
    Image = None

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
PUBLIC = os.path.join(ROOT, "public")
PAGE = "yunnan"
GOLDEN = os.path.join(HERE, "golden")

CLOCK = {
    "before": "2026-09-02T12:00:00Z",     # twenty-two nights before Dali
    "moon26": "2026-09-26T13:00:00Z",     # 21:00 CST on 26 Sep, four hours before the full moon
    "night7": "2026-09-30T13:00:00Z",     # 21:00 CST, night VII, Shangri-La
    "day15": "2026-10-08T02:00:00Z",      # 10:00 CST on the last day
    "after": "2026-10-20T12:00:00Z",
}
PHONE = dict(viewport={"width": 390, "height": 844}, device_scale_factor=2, is_mobile=True, has_touch=True)
NARROW = dict(viewport={"width": 320, "height": 568}, is_mobile=True, has_touch=True)
TABLET = dict(viewport={"width": 768, "height": 1024})
WIDE = dict(viewport={"width": 1280, "height": 800})
LOCS = ["dali", "lijiang", "shangrila", "shaxi", "baoshan", "tengchong"]     # the order of WX_LOC in the page
ROMAN = ["", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII", "XIII", "XIV", "XV"]

HTML = open(os.path.join(PUBLIC, PAGE, "index.html"), encoding="utf-8").read()
BUILD = re.search(r'<meta name="build" content="([^"]+)"', HTML).group(1)
DAYS = [dict(n=int(n), d=d, place=p, stop=s, alt=int(a)) for n, d, p, s, a in
        re.findall(r'\{n:(\d+),\s*d:"([^"]+)",\s*place:"([^"]+)",\s*stop:"([^"]+)",\s*alt:(\d+)', HTML)]
POSTCARD = {int(k): v for k, v in re.findall(r'(\d+):"([A-Z_0-9]+)"', re.search(r"var POSTCARD = \{(.*?)\};", HTML, re.S).group(1))}
SW = open(os.path.join(PUBLIC, PAGE, "sw.js"), encoding="utf-8").read()
HIRES = [u[2:] for u in json.loads(re.search(r"var HIRES = (\[.*?\]);", SW, re.S).group(1))]     # galleries and plates: fetched only as used
WARM_MB = 8.0        # what a phone may warm for offline after the first open

ARGS = None
PW = BROWSER = SERVER = None
BASE = ""

# The browser gives up on a local request when Windows runs out of socket buffers, which says nothing about the page:
# it surfaces as a failed request plus a console line, on whichever file happened to be in flight. Keep-alive on the
# test server makes it rare, but a busy machine can still hit it. Tier A already proves every referenced file exists.
LOCAL_EXHAUSTION = ("ERR_NO_BUFFER_SPACE", "ERR_INSUFFICIENT_RESOURCES")


# ---------------------------------------------------------------- a quiet static server
class Quiet(http.server.SimpleHTTPRequestHandler):
    # Keep-alive: the default HTTP/1.0 opens a fresh connection per file, and a full run asks for thousands of
    # images, which on Windows piles up TIME_WAIT sockets until the browser gets ERR_NO_BUFFER_SPACE. send_head
    # always sets Content-Length, so 1.1 is safe. The timeout keeps a thread from hanging on a dropped connection.
    protocol_version = "HTTP/1.1"
    timeout = 10

    def log_message(self, *a):
        pass

    def guess_type(self, path):
        for ext, t in ((".webmanifest", "application/manifest+json"), (".webp", "image/webp"), (".js", "text/javascript"), (".txt", "text/plain")):
            if path.endswith(ext):
                return t
        return super().guess_type(path)


def serve(directory):
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Quiet, directory=directory))
    srv.daemon_threads = True
    srv.handle_error = lambda *a: None      # the browser drops connections when it goes offline or a context closes
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, f"http://127.0.0.1:{srv.server_address[1]}/"


def setUpModule():
    global PW, BROWSER, SERVER, BASE
    PW = sync_playwright().start()
    BROWSER = PW.chromium.launch(headless=not ARGS.headed)
    SERVER, root = serve(PUBLIC)
    BASE = root + PAGE + "/"


def tearDownModule():
    BROWSER.close()
    PW.stop()
    SERVER.shutdown()


# ---------------------------------------------------------------- fixtures and helpers
def open_meteo(start, override=None):
    """Sixteen days for the six stops, Open-Meteo's multi-location shape. lo = 10 + stop index, hi = 20 + it."""
    override = override or {}
    out = []
    for li, loc in enumerate(LOCS):
        daily = {"time": [], "weather_code": [], "temperature_2m_max": [], "temperature_2m_min": [], "precipitation_probability_max": []}
        for k in range(16):
            iso = (start + datetime.timedelta(days=k)).isoformat()
            o = override.get((loc, iso), {})
            daily["time"].append(iso)
            daily["weather_code"].append(o.get("code", 1))
            daily["temperature_2m_max"].append(o.get("hi", 20 + li))
            daily["temperature_2m_min"].append(o.get("lo", 10 + li))
            daily["precipitation_probability_max"].append(o.get("pp", 10))
        out.append({"daily": daily})
    return out


def clock_ms(name):
    return datetime.datetime.fromisoformat(CLOCK[name].replace("Z", "+00:00")).timestamp() * 1000


def label(n):
    return f"Day {n}" + (" · Shanghai" if n == 15 else "")


def bar_text(n):
    return f"{label(n)} · {DAYS[n - 1]['d']}".upper()


def settle(page):
    """Wait until the scroll position has held still for 150 ms (evaluate awaits the promise; wait_for_function would not)."""
    page.evaluate("() => new Promise(r => { const t0 = performance.now(); let y = scrollY, t = t0; (function tick(){ if (scrollY !== y) { y = scrollY; t = performance.now(); } if (performance.now() - t > 150 || performance.now() - t0 > 6000) r(true); else requestAnimationFrame(tick); })(); })")


def wait_for(page, js, arg=None, timeout=10.0, what="condition"):
    """Poll an async page expression until truthy. page.wait_for_function does not await a returned promise, so this does."""
    deadline = time.monotonic() + timeout
    while True:
        if page.evaluate(js, arg):
            return
        if time.monotonic() > deadline:
            raise TimeoutError(f"gave up after {timeout:.0f} s waiting for {what}")
        time.sleep(0.2)


def wait_images(page):
    """Scroll once through the page so the lazily loaded pictures start, wait for every picture with a src, return to the top."""
    page.evaluate("() => new Promise(r => { const step = innerHeight; let y = 0; (function go(){ y += step; window.scrollTo(0, y); if (y < document.documentElement.scrollHeight) setTimeout(go, 60); else r(true); })(); })")
    page.wait_for_function("() => Array.from(document.images).filter(i => i.getAttribute('src')).every(i => i.complete && i.naturalWidth > 0)", timeout=60000)
    page.evaluate("window.scrollTo(0, 0)")
    settle(page)


def top(page, sel):
    return page.evaluate("s => document.querySelector(s).getBoundingClientRect().top", sel)


def has_class(page, sel, cls):
    return page.evaluate("([s, c]) => document.querySelector(s).classList.contains(c)", [sel, cls])


def extended(cls):
    cls._extended = True
    return cls


class Base(unittest.TestCase):
    ctx_opts = PHONE
    tz = "Europe/Madrid"
    clock = "before"
    sw = "block"
    reduced_motion = "no-preference"
    weather_start = datetime.date(2026, 9, 24)   # the fixture's first day; None aborts the request
    weather_override = None
    allow_errors = False

    def setUp(self):
        if getattr(self, "_extended", False) and not ARGS.all:
            self.skipTest("extended check; run with --all")
        self.wx_calls, self.errors, self.contexts = [], [], []
        self.ctx = self.new_context()

    def new_context(self, **kw):
        opts = dict(self.ctx_opts)
        opts.update(timezone_id=self.tz, service_workers=self.sw, reduced_motion=self.reduced_motion, accept_downloads=True)
        opts.update(kw)
        ctx = BROWSER.new_context(**opts)
        ctx.set_default_timeout(10000)
        if opts["service_workers"] == "block":
            # Playwright's block mode resolves register() with undefined, which the page does not expect; a rejection is what it handles
            ctx.add_init_script("navigator.serviceWorker.register = () => Promise.reject(new Error('service worker disabled by the test'));")

        def weather(route):
            self.wx_calls.append(route.request.url)
            if self.weather_start is None:
                route.abort()
            else:
                route.fulfill(status=200, content_type="application/json", body=json.dumps(open_meteo(self.weather_start, self.weather_override)))
        ctx.route(re.compile(r"^https://api\.open-meteo\.com/"), weather)
        self.contexts.append(ctx)
        return ctx

    def open(self, ctx=None, clock=None, query="", base=None):
        page = (ctx or self.ctx).new_page()
        page.on("pageerror", lambda e: self.errors.append(f"pageerror: {e}"))
        page.on("console", lambda m: self.errors.append(f"console: {m.text}") if m.type == "error" and "open-meteo" not in (m.location or {}).get("url", "")
                and not any(e in m.text for e in LOCAL_EXHAUSTION) else None)
        # Chromium reports a HEAD response (headers, no body) as an aborted load even though fetch() resolved; B15 proves the HEAD works
        page.on("requestfailed", lambda r: self.errors.append(f"requestfailed: {r.url} {r.failure} [{r.resource_type}]")
                if "open-meteo" not in r.url and not (r.method == "HEAD" and "ERR_ABORTED" in (r.failure or ""))
                and not any(e in (r.failure or "") for e in LOCAL_EXHAUSTION) else None)
        page.clock.install(time=CLOCK[clock or self.clock])
        page.goto((base or BASE) + query, wait_until="load")
        return page

    def tearDown(self):
        for c in self.contexts:
            try:
                c.close()
            except Exception:
                pass
        if self.errors and not self.allow_errors:
            self.fail("page errors: " + "; ".join(self.errors[:5]))


# ---------------------------------------------------------------- B1 clean console
class B01_Console(Base):
    def walk(self, page):
        wait_images(page)
        page.evaluate("window.scrollTo(0, document.documentElement.scrollHeight)")
        page.wait_for_timeout(400)
        page.evaluate("window.scrollTo(0, 0)")
        if page.locator("#barMain").is_visible():
            page.click("#barMain")
            page.keyboard.press("Escape")
            page.click("#barMap")
            page.keyboard.press("Escape")
        else:                                   # wide: the rail stands in for the bar
            page.click(".rail-list a[data-go='9']")
            settle(page)
            page.evaluate("window.scrollTo(0, 0)")
        page.locator(".win .photo").first.click()
        page.wait_for_selector("#lbImg[src]:not(.wait)")
        page.keyboard.press("Escape")
        self.assertEqual(self.errors, [])

    def test_B1_phone(self):
        self.walk(self.open())

    def test_B1_wide(self):
        self.walk(self.open(self.new_context(**WIDE)))


# ---------------------------------------------------------------- B2 nothing wider than the screen
class B02_Overflow(Base):
    def measure(self, opts):
        page = self.open(self.new_context(**opts))
        wait_images(page)
        w = opts["viewport"]["width"]
        self.assertLessEqual(page.evaluate("document.documentElement.scrollWidth"), w, "the page scrolls sideways")
        if w >= 390:      # the page is laid out for 390 and up; at 320 only sideways scrolling counts
            wide = page.evaluate("""() => Array.from(document.querySelectorAll('body *')).filter(el => {
                if (el.ownerSVGElement) return false;      // drawn inside an svg, clipped by its viewBox
                const r = el.getBoundingClientRect();
                return r.width > 0 && r.right > innerWidth + 1 && r.left < innerWidth && el.checkVisibility({visibilityProperty: true}) && !el.closest('.panel, .sheet, .lb');
            }).slice(0, 6).map(el => el.tagName.toLowerCase() + (el.id ? '#' + el.id : '') + '.' + String(el.className).split(' ')[0])""")
            self.assertEqual(wide, [], f"wider than {w}px")
        clipped = page.evaluate("""() => Array.from(document.querySelectorAll('.day')).filter(card => {
            const cr = card.getBoundingClientRect();
            return Array.from(card.querySelectorAll('.log-row input, .log-row button')).some(el => el.getBoundingClientRect().right > cr.right + 1);
        }).map(c => c.id)""")
        self.assertEqual(clipped, [], "night-log controls overflow their card")
        heights = page.evaluate("Array.from(document.querySelectorAll('.cal a')).map(a => a.getBoundingClientRect().height)")
        self.assertEqual(len(heights), 15)
        self.assertLessEqual(max(heights) - min(heights), 1, f"calendar cells of unequal height: {heights}")

    def test_B2_320(self):
        self.measure(NARROW)

    def test_B2_390(self):
        self.measure(PHONE)

    def test_B2_768(self):
        self.measure(TABLET)

    def test_B2_1280(self):
        self.measure(WIDE)


# ---------------------------------------------------------------- B3 photographs shown whole
class B03_Pictures(Base):
    def crops(self, page):
        wait_images(page)
        return page.evaluate("""() => Array.from(document.querySelectorAll('.win .photo img')).filter(i => i.getAttribute('src') && i.offsetParent !== null && i.naturalWidth).map(i => {
            const r = i.getBoundingClientRect(), fit = getComputedStyle(i).objectFit;
            const s = Math.max(r.width / i.naturalWidth, r.height / i.naturalHeight);
            const vis = fit === 'cover' ? (r.width * r.height) / (i.naturalWidth * s * i.naturalHeight * s) : 1;
            return {tok: i.dataset.tok, crop: Math.round((1 - vis) * 1000) / 1000, plate: !!i.closest('.win.plate'), pair: !!i.closest('.pair')};
        })""")

    def check(self, page, pairs=True):
        cs = self.crops(page)
        self.assertGreaterEqual(len(cs), 30)
        bad = [c for c in cs if (pairs or not c["pair"]) and (c["crop"] > 0.25 or (c["plate"] and c["crop"] > 0.01))]
        self.assertEqual(bad, [], "more than a quarter of the picture cropped")

    def test_B3_phone(self):
        page = self.open()
        self.check(page)
        ratios = page.evaluate("Array.from(document.querySelectorAll('.pair')).map(p => { const w = p.getBoundingClientRect().width; return Array.from(p.querySelectorAll(':scope > .win')).map(f => Math.round(f.getBoundingClientRect().width / w * 100) / 100); })")
        self.assertTrue(ratios, "no paired figures found")
        self.assertTrue(all(r >= 0.9 for p in ratios for r in p), f"paired pictures do not stack full-width on phones: {ratios}")

    def test_B3_wide(self):
        # side-by-side pairs are cut to 4:5 by design on wide screens; every other picture keeps its proportions
        self.check(self.open(self.new_context(**WIDE)), pairs=False)


# ---------------------------------------------------------------- B4 the bar knows the night
class B04_Bar(Base):
    def test_B4_scroll_spy(self):
        page = self.open()
        wait_images(page)
        for n in range(1, 16):
            page.evaluate("n => { const el = document.getElementById('day-' + n); window.scrollTo(0, scrollY + el.getBoundingClientRect().top - Math.round(innerHeight * 0.38) + 2); }", n)
            d = DAYS[n - 1]
            expect(page.locator("#barL1")).to_have_text(bar_text(n))
            expect(page.locator("#barL2")).to_have_text(f"{d['place']} · {d['alt']:,} m")
            self.assertEqual(page.evaluate("document.querySelectorAll('.cell.past').length"), n - 1)
            self.assertEqual(page.locator(".cell.now").get_attribute("data-n"), str(n))
            self.assertEqual(page.locator(".bar-cells i.now").get_attribute("data-n"), str(n))
            self.assertTrue(has_class(page, f"#day-{n}", "now"))
            self.assertEqual(page.locator(".cal a.now").get_attribute("data-go"), str(n))
        everything = page.locator("#bar").inner_text() + page.locator("#panel").inner_text() + page.locator("#cal").inner_text()
        self.assertNotIn("undefined", everything)
        self.assertNotIn("NaN", everything)


# ---------------------------------------------------------------- B5 scrolls land where they aim
class B05_Landing(Base):
    def land(self, page, n):
        if page.locator("#barMain").is_visible():
            page.click("#barMain")
            expect(page.locator("#panel")).to_have_class(re.compile(r"\bopen\b"))
            page.click(f".cell[data-n='{n}']")
        else:                                   # wide: the rail's list of nights
            page.click(f".rail-list a[data-go='{n}']")
        settle(page)
        t = top(page, f"#day-{n}")
        self.assertTrue(-1 <= t <= 40, f"day {n} landed with its top at {t:.0f}px")
        self.assertEqual(page.get_attribute("#barMain", "aria-expanded"), "false")
        self.assertFalse(has_class(page, "#panel", "open"))
        expect(page.locator("#barL1")).to_have_text(bar_text(n))
        if not page.locator("#barMain").is_visible():
            self.assertEqual(page.evaluate("Array.from(document.querySelectorAll('.rail-list li')).findIndex(li => li.classList.contains('on'))"), n - 1)

    def test_B5_phone(self):
        page = self.open()
        wait_images(page)
        for n in range(1, 16):
            self.land(page, n)

    def test_B5_wide(self):
        page = self.open(self.new_context(**WIDE))
        wait_images(page)
        for n in (1, 5, 9, 15):
            self.land(page, n)

    def test_B5_calendar_and_lamp(self):
        page = self.open()
        wait_images(page)
        page.click(".cal a[data-go='9']")
        settle(page)
        t = top(page, "#day-9")
        self.assertTrue(-1 <= t <= 40, f"calendar cell landed at {t:.0f}px")
        page.click("#barMap")
        expect(page.locator("#sheet")).to_have_class(re.compile(r"\bopen\b"))
        page.click("#sheet .lamp[data-stop='shaxi']")
        settle(page)
        t = top(page, "#ch3")
        self.assertTrue(-1 <= t <= 40, f"lamp landed at {t:.0f}px")
        self.assertFalse(has_class(page, "#sheet", "open"))
        expect(page.locator("#barL1")).to_have_text(bar_text(9))


# ---------------------------------------------------------------- B6 panel and sheet
class B06_Panel(Base):
    def test_B6_toggles_focus_escape(self):
        page = self.open()
        page.click("#barMain")
        self.assertEqual(page.get_attribute("#barMain", "aria-expanded"), "true")
        self.assertEqual(page.evaluate("document.activeElement.dataset.n"), "1", "focus goes to tonight's window")
        page.keyboard.press("Escape")
        self.assertEqual(page.get_attribute("#barMain", "aria-expanded"), "false")
        self.assertFalse(has_class(page, "#panel", "open"))
        page.click("#barMap")
        self.assertEqual(page.get_attribute("#barMap", "aria-expanded"), "true")
        self.assertEqual(page.evaluate("document.activeElement.id"), "sheetX")
        page.click("#barMain")
        self.assertTrue(has_class(page, "#panel", "open"))
        self.assertFalse(has_class(page, "#sheet", "open"), "opening the panel closes the sheet")
        self.assertEqual(page.get_attribute("#barMap", "aria-expanded"), "false")
        page.click("#barMap")
        self.assertFalse(has_class(page, "#panel", "open"), "opening the sheet closes the panel")
        page.click("#sheetX")
        self.assertFalse(has_class(page, "#sheet", "open"))

    def test_B6_keyboard(self):
        page = self.open()
        page.click("#barMain")
        for key, want in (("ArrowRight", "2"), ("ArrowDown", "7"), ("End", "15"), ("ArrowRight", "15"), ("Home", "1"), ("ArrowLeft", "1"), ("ArrowRight", "2"), ("ArrowRight", "3")):
            page.keyboard.press(key)
            self.assertEqual(page.evaluate("document.activeElement.dataset.n"), want, key)
        page.keyboard.press("Enter")
        expect(page.locator("#barL1")).to_have_text(bar_text(3))
        self.assertFalse(has_class(page, "#panel", "open"))
        settle(page)
        t = top(page, "#day-3")
        self.assertTrue(-1 <= t <= 40, f"Enter landed at {t:.0f}px")

    def test_B6_drag(self):
        page = self.open()
        page.click("#barMain")
        expect(page.locator("#panel")).to_have_class(re.compile(r"\bopen\b"))
        page.wait_for_timeout(500)              # let the panel finish sliding up before measuring the windows
        b2 = page.locator(".cell[data-n='2']").bounding_box()
        b5 = page.locator(".cell[data-n='5']").bounding_box()
        page.mouse.move(b2["x"] + b2["width"] / 2, b2["y"] + b2["height"] / 2)
        page.mouse.down()
        page.mouse.move(b5["x"] + b5["width"] / 2, b5["y"] + b5["height"] / 2, steps=8)
        expect(page.locator("#panelLab")).to_contain_text("Day 5")
        self.assertEqual(page.locator(".cell.now").get_attribute("data-n"), "5", "the drag previews the window under the finger")
        page.mouse.up()
        expect(page.locator("#barL1")).to_have_text(bar_text(5))
        self.assertFalse(has_class(page, "#panel", "open"))


# ---------------------------------------------------------------- B8 lightbox and galleries
class B08_Lightbox(Base):
    def open_lb(self, page, sel):
        page.click(sel)
        expect(page.locator("#lb")).to_have_class(re.compile(r"\bopen\b"))
        page.wait_for_selector("#lbImg[src]:not(.wait)")

    def visible_shots(self, page):
        return page.evaluate("document.querySelectorAll('.win .photo').length - document.querySelectorAll('.gal .win .photo').length")

    def test_B8_open_navigate_close(self):
        page = self.open()
        wait_images(page)
        n = self.visible_shots(page)
        self.open_lb(page, ".win .photo >> nth=0")
        self.assertEqual(page.get_attribute("#lb", "role"), "dialog")
        self.assertEqual(page.get_attribute("#lb", "aria-modal"), "true")
        self.assertEqual(page.evaluate("document.activeElement.id"), "lbX")
        self.assertEqual(page.evaluate("document.body.style.overflow"), "hidden")
        expect(page.locator("#lbCount")).to_have_text(f"1 / {n}")
        page.keyboard.press("ArrowRight")
        expect(page.locator("#lbCount")).to_have_text(f"2 / {n}")
        page.wait_for_selector("#lbImg[src]:not(.wait)")
        page.keyboard.press("ArrowLeft")
        page.keyboard.press("ArrowLeft")
        expect(page.locator("#lbCount")).to_have_text(f"{n} / {n}")
        page.wait_for_selector("#lbImg[src]:not(.wait)")
        boxes = page.evaluate("() => ['#lbCap', '#lbImg'].map(s => { const r = document.querySelector(s).getBoundingClientRect(); return [r.left, r.top, r.right, r.bottom]; })")
        cap, img = boxes
        if page.locator("#lbCap").inner_text().strip():
            overlap = not (cap[2] <= img[0] or img[2] <= cap[0] or cap[3] <= img[1] or img[3] <= cap[1])
            self.assertFalse(overlap, f"the caption covers the picture: cap {cap} img {img}")
        page.keyboard.press("Escape")
        self.assertFalse(has_class(page, "#lb", "open"))
        self.assertEqual(page.evaluate("document.body.style.overflow"), "")
        self.assertTrue(page.evaluate("document.activeElement === document.querySelector('.win .photo')"), "focus returns to the picture")
        self.assertIsNone(page.get_attribute("#lbImg", "src"))

    def test_B8_hires_plate(self):
        page = self.open()
        wait_images(page)
        self.open_lb(page, ".win .photo[data-hires] >> nth=0")
        expect(page.locator("#lbHd")).to_have_text(re.compile(r"full resolution · [\d,]+ px wide"), timeout=60000)
        self.assertGreaterEqual(page.evaluate("document.getElementById('lbImg').naturalWidth"), 3000)

    def test_B8_gallery_unfolds(self):
        page = self.open()
        wait_images(page)
        n = self.visible_shots(page)
        btn = page.locator(".more-btn").first
        text = btn.text_content()
        gal = btn.get_attribute("data-gal")
        count = int(re.search(r"(\d+)\s*$", text).group(1))
        self.assertTrue(page.locator(f"#{gal}").is_hidden())
        btn.click()
        expect(page.locator(f"#{gal}")).to_be_visible()
        self.assertEqual(btn.get_attribute("aria-expanded"), "true")
        expect(btn).to_have_text("Fewer photographs")
        self.assertEqual(page.evaluate(f"document.querySelectorAll('#{gal} img[data-src]').length"), 0, "gallery pictures get their src when unfolded")
        self.assertEqual(page.evaluate(f"document.querySelectorAll('#{gal} img[src]').length"), count)
        wait_images(page)
        self.open_lb(page, f"#{gal} .win .photo >> nth=0")
        expect(page.locator("#lbCount")).to_have_text(re.compile(rf"^\d+ / {n + count}$"))
        page.keyboard.press("Escape")
        btn.click()
        self.assertTrue(page.locator(f"#{gal}").is_hidden())
        self.assertEqual(btn.get_attribute("aria-expanded"), "false")
        expect(btn).to_have_text(text.strip())

    def test_B8_black_marble_overlay(self):
        page = self.open()
        wait_images(page)
        self.open_lb(page, ".lights-wrap .photo")
        self.assertTrue(has_class(page, "#lbPic", "lights-wrap"))
        self.assertEqual(page.locator("#lbPic svg").count(), 1, "the lights overlay comes along into the lightbox")

    def test_B8_swipe(self):
        page = self.open()
        wait_images(page)
        self.open_lb(page, ".win .photo >> nth=0")
        cdp = self.ctx.new_cdp_session(page)
        cdp.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{"x": 300, "y": 400}]})
        cdp.send("Input.dispatchTouchEvent", {"type": "touchMove", "touchPoints": [{"x": 110, "y": 404}]})
        cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})
        expect(page.locator("#lbCount")).to_have_text(re.compile(r"^2 / "))
        self.assertTrue(has_class(page, "#lb", "open"), "a swipe must not close the lightbox")


# ---------------------------------------------------------------- B9 postcards
class B09_Postcards(Base):
    def test_B9_every_night_has_its_picture(self):
        page = self.open()
        for n in range(1, 16):
            hits = page.evaluate("t => document.querySelectorAll('.win img[data-tok=\"' + t + '\"][src]').length", POSTCARD[n])
            self.assertEqual(hits, 1, f"night {n}: picture {POSTCARD[n]} is not a loaded picture on the page")

    def test_B9_saved_picture(self):
        ctx = self.new_context()
        ctx.add_init_script("Object.defineProperty(navigator, 'canShare', {value: () => false, configurable: true});")
        page = self.open(ctx)
        wait_images(page)
        for n, line in ((1, "Landed in the dark, walked to the south gate."), (8, "Snow on the pass, the monastery gold at four."), (15, "")):
            page.fill(f"#log{n}", line)
            with page.expect_download() as dl:
                page.click(f".log[data-day='{n}'] button")
            expect(page.locator(f".log[data-day='{n}'] .msg")).to_have_text("Saved as a picture you can send.")
            self.assertEqual(dl.value.suggested_filename, f"night-{n}.jpg")
            path = dl.value.path()
            self.assertGreater(os.path.getsize(path), 20000)
            if Image is None:
                continue
            im = Image.open(path)
            self.assertEqual(im.format, "JPEG")
            self.assertEqual(im.size, (1200, 900))
            px = im.convert("RGB").load()

            def amber(x, y):
                r, g, b = px[x, y]
                return r > 190 and g > 140 and b < 130 and r - b > 80
            self.assertFalse(any(amber(x, y) for y in range(0, 40, 2) for x in range(0, 1200, 4)), f"night {n}: something amber in the top 40 px (numeral clipped?)")
            self.assertTrue(any(amber(x, y) for y in range(60, 166, 2) for x in range(60, 260, 2)), f"night {n}: no numeral in the header")

    def test_B9_share_sheet(self):
        ctx = self.new_context()
        ctx.add_init_script("""Object.defineProperty(navigator, 'canShare', {value: () => true, configurable: true});
            Object.defineProperty(navigator, 'share', {value: d => { window.__shared = {files: d.files.map(f => f.name), title: d.title}; return Promise.resolve(); }, configurable: true});""")
        page = self.open(ctx)
        wait_images(page)
        page.click(".log[data-day='8'] button")
        expect(page.locator(".log[data-day='8'] .msg")).to_have_text("Sent.")
        self.assertEqual(page.evaluate("window.__shared"), {"files": ["night-8.jpg"], "title": "Night VIII from Yunnan"})


# ---------------------------------------------------------------- B10 night log
class B10_NightLog(Base):
    def test_B10_persists(self):
        page = self.open()
        page.fill("#log3", "Moon over the lake")
        self.assertEqual(page.evaluate("localStorage.getItem('fn-log-3')"), "Moon over the lake")
        page.reload()
        expect(page.locator("#log3")).to_have_value("Moon over the lake")
        self.assertIsNone(page.evaluate("localStorage.getItem('fn-log-4')"))
        page.locator("#log4").press_sequentially("x" * 115)
        self.assertEqual(len(page.input_value("#log4")), 110, "maxlength 110")


# ---------------------------------------------------------------- B11 weather in three states
class B11_Weather(Base):
    def test_B11a_climate_until_the_forecast_opens(self):
        self.weather_start = datetime.date(2026, 9, 2)       # a real answer, but without the trip's dates yet
        page = self.open()
        page.wait_for_timeout(500)
        expect(page.locator(".wx.stand")).to_have_count(15)
        expect(page.locator(".wx[data-day='1'] .asof")).to_have_text(re.compile(r"^forecast opens 9 Sept?$"))      # ICU writes "Sept" in en-GB
        expect(page.locator(".wx[data-day='15'] .asof")).to_have_text(re.compile(r"^forecast opens 23 Sept?$"))
        t7 = page.locator(".wx[data-day='7']").inner_text()
        self.assertIn("usually 8 to 18 °C", t7)
        self.assertIn("cold once the sun is down", t7)
        self.assertEqual(page.locator(".wx[data-day='8'] .frz").count(), 1, "Shangri-La in October is near freezing")
        self.assertIn("wettest stop", page.locator(".wx[data-day='12']").inner_text())
        self.assertIn("Dali in early October", page.locator(".wx[data-day='15']").inner_text())

    def test_B11b_forecast(self):
        self.clock = "night7"
        self.weather_override = {("shangrila", "2026-09-30"): dict(hi=15, lo=-2, code=0, pp=40), ("dali", "2026-10-08"): dict(hi=22), ("lijiang", "2026-09-26"): dict(code=61, pp=20)}
        page = self.open()
        expect(page.locator(".wx.stand")).to_have_count(0)
        self.assertTrue(page.locator(".wx[data-day='7']").inner_text().startswith("tonight -2° · day 15° · clear · rain 40% · near freezing"), page.locator(".wx[data-day='7']").inner_text())
        self.assertTrue(page.locator(".wx[data-day='15']").inner_text().startswith("Dali by day 22°"))
        t3 = page.locator(".wx[data-day='3']").inner_text()
        self.assertTrue(t3.startswith("tonight 11° · day 21° · light rain"), t3)
        self.assertEqual(page.locator(".wx[data-day='3'] .rain").count(), 0, "rain under 30% is not shown")
        self.assertRegex(page.locator(".wx[data-day='7'] .asof").inner_text(), r"^forecast as of \d{1,2} [A-Za-z]{3,5},? \d{2}:\d{2}$")
        store = page.evaluate("JSON.parse(localStorage.getItem('fn-wx'))")
        self.assertEqual(store["data"]["shangrila"]["2026-09-30"]["lo"], -2)
        self.assertEqual(len(self.wx_calls), 1)
        url = self.wx_calls[0]
        for part in ("latitude=25.69,26.87,27.83,26.32,25.11,25.02", "longitude=100.16,100.23,99.7,99.85,99.16,98.49", "timezone=Asia%2FShanghai", "forecast_days=16",
                     "daily=weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max"):
            self.assertIn(part, url)

    def test_B11c_offline_keeps_the_forecast(self):
        self.clock = "night7"
        page = self.open()
        expect(page.locator(".wx.stand")).to_have_count(0)
        self.ctx.set_offline(True)
        expect(page.locator(".wx[data-day='7'] .asof")).to_contain_text("offline")
        expect(page.locator(".wx[data-day='7'] .asof")).to_contain_text("forecast kept from")
        self.assertIn("tonight", page.locator(".wx[data-day='7']").inner_text())
        self.ctx.set_offline(False)
        expect(page.locator(".wx[data-day='7'] .asof")).to_contain_text("forecast as of")

    def test_B11d_refetch_only_when_stale(self):
        self.clock = "night7"
        now = clock_ms(self.clock)      # the init script runs before the fake clock is installed, so the time is written as a literal
        fresh = self.new_context()
        fresh.add_init_script(f"localStorage.setItem('fn-wx', JSON.stringify({{at: {now - 3600e3:.0f}, data: {{}}}}))")
        page = self.open(fresh)
        page.wait_for_timeout(800)
        self.assertEqual(len(self.wx_calls), 0, "a one-hour-old forecast is not refetched")
        stale = self.new_context()
        stale.add_init_script(f"localStorage.setItem('fn-wx', JSON.stringify({{at: {now - 4 * 3600e3:.0f}, data: {{}}}}))")
        page = self.open(stale)
        expect(page.locator(".wx.stand")).to_have_count(0)
        self.assertEqual(len(self.wx_calls), 1, "a four-hour-old forecast is refetched")

    def test_B11e_legacy_key_still_read(self):
        self.clock = "night7"
        ctx = self.new_context()
        ctx.add_init_script(f"localStorage.setItem('yn-wx', JSON.stringify({{at: {clock_ms(self.clock):.0f}, data: {{dali: {{'2026-09-24': {{hi: 24, lo: 14, code: 2, pp: 0}}}}}}}}))")
        page = self.open(ctx)
        page.wait_for_timeout(500)
        self.assertTrue(page.locator(".wx[data-day='1']").inner_text().startswith("tonight 14° · day 24° · partly cloudy"))
        expect(page.locator(".wx.stand")).to_have_count(14)
        self.assertEqual(len(self.wx_calls), 0)


# ---------------------------------------------------------------- B12 sunset and moonrise golden file
class B12_Sky(Base):
    def test_B12_golden(self):
        page = self.open()
        lines = page.evaluate("Array.from(document.querySelectorAll('.astro')).map(a => a.dataset.day + ' ' + a.innerText.replace(/\\s+/g, ' ').trim())")
        self.assertEqual(len(lines), 15)
        self.assertTrue(all(re.search(r"sunset \d{2}:\d{2}", l) for l in lines), lines[:2])
        path = os.path.join(GOLDEN, "astro.txt")
        if ARGS.update_golden or not os.path.exists(path):
            os.makedirs(GOLDEN, exist_ok=True)
            open(path, "w", encoding="utf-8", newline="\n").write("\n".join(lines) + "\n")
            self.skipTest(f"golden written to {os.path.relpath(path, ROOT)}")
        want = open(path, encoding="utf-8").read().splitlines()
        self.assertEqual(lines, want, "sunset, moonrise or phase changed; rerun with --update-golden if deliberate")


# ---------------------------------------------------------------- B13 cover, tile and Tonight
class B13_Cover(Base):
    def tonight_hidden(self, page):
        return page.evaluate("document.getElementById('tonightBtn').hidden")

    def test_B13_before(self):
        page = self.open(clock="before")
        expect(page.locator("#tileTop")).to_have_text("Before the trip")
        expect(page.locator("#tileMain")).to_have_text("Twenty-two nights until Dali · tap to start")
        expect(page.locator("#coverDate")).to_have_text("24 SEP 2026")
        self.assertTrue(self.tonight_hidden(page))
        expect(page.locator("#barL1")).to_have_text(bar_text(1))

    def test_B13_night7(self):
        page = self.open(clock="night7")
        expect(page.locator("#tileTop")).to_have_text("Tonight · Wed 30 Sep")
        expect(page.locator("#tileMain")).to_have_text("Night VII · Shangri-La · tap to go")
        expect(page.locator("#coverDate")).to_have_text("30 SEP 2026")
        self.assertFalse(self.tonight_hidden(page))
        expect(page.locator("#tonightBtn")).to_have_text("Tonight · Night VII · Shangri-La")
        page.click("#barMain")
        expect(page.locator("#tonightBtn")).to_be_visible()
        page.click("#tonightBtn")
        settle(page)
        t = top(page, "#day-7")
        self.assertTrue(-1 <= t <= 40, f"Tonight landed at {t:.0f}px")
        expect(page.locator("#barL1")).to_have_text(bar_text(7))
        page.evaluate("window.scrollTo(0, 0)")
        settle(page)
        page.click("#tile")
        settle(page)
        t = top(page, "#day-7")
        self.assertTrue(-1 <= t <= 40, f"the tile landed at {t:.0f}px")

    def test_B13_day15(self):
        page = self.open(clock="day15")
        expect(page.locator("#tileTop")).to_have_text("Today · Thu 8 Oct")
        expect(page.locator("#tileMain")).to_have_text("Day 15 · Tengchong to Dali, then Shanghai · tap to open")
        self.assertFalse(self.tonight_hidden(page))
        expect(page.locator("#tonightBtn")).to_have_text("Today · Day 15 · to Shanghai")
        page.click("#barMain")
        page.click("#tonightBtn")
        expect(page.locator("#barL1")).to_have_text("DAY 15 · SHANGHAI · THU 8 OCT")

    def test_B13_bar_reads_tonight_on_open(self):
        # The start block sets the bar to tonight in a setTimeout(0); the initial syncNight now only runs when the
        # page was restored partway down, so it no longer puts day 1 back over tonight when the page opens at the top.
        page = self.open(clock="night7")
        expect(page.locator("#barL1")).to_have_text(bar_text(7))

    def test_B13_after(self):
        page = self.open(clock="after")
        expect(page.locator("#tileTop")).to_have_text("After the trip")
        expect(page.locator("#tileMain")).to_have_text("Fourteen nights, kept here · tap to read again")
        expect(page.locator("#coverDate")).to_have_text("24 SEP 2026")
        self.assertTrue(self.tonight_hidden(page))

    def test_B13_moon(self):
        page = self.open(clock="moon26")
        expect(page.locator("#moonCap")).to_contain_text("full 27 Sep 00:49")
        self.assertTrue(page.get_attribute("#moonLit", "d") and page.get_attribute("#barMoon", "d"))
        page = self.open(clock="night7")
        expect(page.locator("#moonCap")).not_to_contain_text("full 27 Sep")


# ---------------------------------------------------------------- B14 wording flag
class B14_Wording(Base):
    CASES = (("Asia/Shanghai", True), ("Asia/Yangon", True), ("Etc/GMT-8", True), ("Asia/Taipei", False), ("Europe/Madrid", False))

    def state(self, page):
        return page.evaluate("""() => ({cn: document.documentElement.classList.contains('cn'),
            cnOnly: getComputedStyle(document.querySelector('.cn-only')).display, intl: getComputedStyle(document.querySelector('.intl-only')).display,
            ls: localStorage.getItem('fn-cn'), cookie: document.cookie})""")

    def test_B14_timezones(self):
        for tz, on in self.CASES:
            page = self.open(self.new_context(timezone_id=tz))
            s = self.state(page)
            self.assertEqual(s["cn"], on, f"{tz}: {s}")
            self.assertEqual(s["cnOnly"], "inline" if on else "none", tz)
            self.assertEqual(s["intl"], "none" if on else "inline", tz)
            self.assertEqual(s["ls"], "1" if on else "0", tz)
            self.assertIn(f"fn-cn={'1' if on else '0'}", s["cookie"], tz)
        self.assertEqual(page.locator(".cn-only").count(), 4)
        self.assertEqual(page.locator(".intl-only").count(), 4)

    def test_B14_override_is_remembered(self):
        page = self.open(query="?cn=1")
        self.assertTrue(self.state(page)["cn"])
        page.goto(BASE)
        self.assertTrue(self.state(page)["cn"], "?cn=1 is remembered on the next plain open")
        page.goto(BASE + "?cn=0")
        self.assertFalse(self.state(page)["cn"])
        page.goto(BASE)
        self.assertFalse(self.state(page)["cn"])


# ---------------------------------------------------------------- B15 offline and the new-build handover
class B15_Worker(Base):
    sw = "allow"

    def setUp(self):
        super().setUp()
        self.tmp = tempfile.mkdtemp(prefix="fn-sw-")
        d = os.path.join(self.tmp, PAGE)
        os.makedirs(d)
        for f in ("index.html", "sw.js", "build.txt", "manifest.webmanifest", "og.jpg"):
            shutil.copy(os.path.join(PUBLIC, PAGE, f), d)
        os.symlink(os.path.join(PUBLIC, PAGE, "img"), os.path.join(d, "img"))
        self.srv, root = serve(self.tmp)
        self.base = root + PAGE + "/"
        self.addCleanup(self.srv.shutdown)
        self.addCleanup(lambda: shutil.rmtree(self.tmp, ignore_errors=True))

    def new_build(self, suffix):
        new = f"{PAGE}-{suffix}"
        for f in ("index.html", "sw.js", "build.txt"):
            p = os.path.join(self.tmp, PAGE, f)
            s = open(p, encoding="utf-8", newline="").read().replace(BUILD, new)
            open(p, "w", encoding="utf-8", newline="").write(s)
        return new

    def controller_build(self, page):
        return page.evaluate("""() => new Promise(r => { const c = navigator.serviceWorker.controller; if (!c) return r(null);
            const ch = new MessageChannel(); ch.port1.onmessage = e => r(e.data.build); c.postMessage({type: 'build'}, [ch.port2]); setTimeout(() => r(null), 2000); })""")

    def cached(self, page):
        return page.evaluate("""async () => { const c = await caches.open('yunnan-img'); const ks = await c.keys(); let bytes = 0;
            for (const k of ks) { const r = await c.match(k); bytes += (await r.blob()).size; }
            return {paths: ks.map(k => new URL(k.url).pathname.replace(/^.*\\/img\\//, 'img/')), mb: bytes / 1048576}; }""")

    def test_B15_offline_and_handover(self):
        page = self.open(base=self.base)
        page.wait_for_function("navigator.serviceWorker.controller !== null", timeout=20000)
        n = page.evaluate("Array.from(document.querySelectorAll('.win .photo img')).filter(i => i.offsetParent !== null && (i.getAttribute('src') || i.getAttribute('srcset'))).length")
        self.assertGreaterEqual(n, 30)
        # once the worker has taken over, the page names the file each picture uses on this screen and the worker fetches them one by one
        wait_for(page, "n => caches.open('yunnan-img').then(c => c.keys()).then(k => k.length >= n)", arg=n, timeout=90, what="the worker to warm the pictures")
        keys = page.evaluate("caches.keys()")
        self.assertIn(BUILD, keys)
        self.assertIn("yunnan-img", keys)
        got = self.cached(page)
        self.assertEqual(len(got["paths"]), n, "one file per picture on screen, nothing more")
        self.assertEqual([p for p in got["paths"] if p in HIRES], [], "no gallery or plate file is warmed")
        self.assertLessEqual(got["mb"], WARM_MB, f"a phone warms {got['mb']:.1f} MB")
        page.wait_for_function("document.querySelector('link[rel=manifest]').getAttribute('href') === 'manifest.webmanifest'")
        self.assertEqual(self.controller_build(page), BUILD)

        self.ctx.set_offline(True)
        page.reload(wait_until="load")
        self.assertEqual(page.evaluate("document.querySelector('meta[name=build]').content"), BUILD, "the cached page comes up offline")
        wait_images(page)
        expect(page.locator("#barL1")).to_have_text(bar_text(1))
        page.click(".win .photo[data-hires] >> nth=0")
        page.wait_for_selector("#lbImg[src]:not(.wait)")
        expect(page.locator("#lbHd")).to_have_text("", timeout=15000)      # the full-resolution fetch fails quietly offline
        page.keyboard.press("Escape")
        self.ctx.set_offline(False)
        # while offline the hi-res plate, build.txt and the forecast are meant to fail; anything else still counts
        self.errors = [e for e in self.errors if not re.search(r"requestfailed|ERR_INTERNET_DISCONNECTED|ERR_FAILED", e)]

        new = self.new_build("b2b2b2b2b2")
        loads = []
        page.on("load", lambda _: loads.append(1))
        page.goto(self.base, wait_until="load")
        self.assertEqual(page.evaluate("document.querySelector('meta[name=build]').content"), new, "the worker serves the newer build on the next open")
        wait_for(page, "([n, o]) => caches.keys().then(k => k.includes(n) && !k.includes(o))", arg=[new, BUILD], timeout=20, what="the new worker to replace the old page cache")
        wait_for(page, "b => new Promise(r => { const c = navigator.serviceWorker.controller; if (!c) return r(false); const ch = new MessageChannel(); ch.port1.onmessage = e => r(e.data.build === b); c.postMessage({type: 'build'}, [ch.port2]); setTimeout(() => r(false), 1500); })", arg=new, timeout=20, what="the new worker to take control")
        page.wait_for_timeout(2500)
        self.assertEqual(len(loads), 1, "the page reloaded during the handover")
        self.assertEqual(page.evaluate("document.querySelector('meta[name=build]').content"), new)
        self.assertGreaterEqual(len(self.cached(page)["paths"]), n, "unchanged pictures are kept across the update")


# ---------------------------------------------------------------- extended checks (--all)
@extended
class B16_Reveal(Base):
    def test_B16_chapters_reveal_in_order(self):
        page = self.open()
        self.assertGreater(page.locator("[data-id='air-in'].on").count(), 0)
        self.assertEqual(page.locator("[data-id='seg6'].on").count(), 0, "later legs are not drawn yet")
        page.click("#barMain")
        page.click(".cell[data-n='14']")
        settle(page)
        self.assertGreater(page.locator("[data-id='seg6'].on").count(), 0, "the Tengchong leg is drawn by night XIV")
        self.assertEqual(page.locator("[data-id='seg7'].on").count(), 0, "the last day's leg waits for day 15")
        self.assertTrue(page.evaluate("document.querySelectorAll('.lamp.cur').length > 0"))
        page.click("#barMain")
        page.click(".cell[data-n='15']")
        settle(page)
        self.assertEqual(page.evaluate("document.querySelectorAll('[data-id]:not(.on)').length"), 0, "every leg is drawn by day 15")


@extended
class B17_ReducedMotion(Base):
    reduced_motion = "reduce"

    def test_B17_everything_at_rest(self):
        page = self.open()
        wins = page.evaluate("[document.querySelectorAll('.win').length, document.querySelectorAll('.win.lit').length]")
        self.assertEqual(wins[0], wins[1], "every window is lit at once under reduced motion")
        self.assertEqual(page.evaluate("getComputedStyle(document.querySelector('.nm-seg')).strokeDashoffset"), "0px")


@extended
class B19_SourcesCreditsPrint(Base):
    def test_B19_toggles_and_print(self):
        page = self.open()
        for btn, lst, word in (("#sourcesBtn", "#sourcesList", "sources"), ("#creditsBtn", "#creditsList", "credits")):
            self.assertTrue(page.locator(lst).is_hidden())
            page.click(btn)
            expect(page.locator(lst)).to_be_visible()
            self.assertEqual(page.get_attribute(btn, "aria-expanded"), "true")
            expect(page.locator(btn)).to_have_text(f"Hide {word}")
            page.click(btn)
            self.assertTrue(page.locator(lst).is_hidden())
        page.emulate_media(media="print")
        css = page.evaluate("""() => ({bar: getComputedStyle(document.querySelector('.bar')).display, panel: getComputedStyle(document.querySelector('.panel')).display,
            log: getComputedStyle(document.querySelector('.log')).display, body: getComputedStyle(document.body).backgroundColor,
            chapter: getComputedStyle(document.querySelector('.chapter')).breakBefore, credits: getComputedStyle(document.querySelector('.credits')).display})""")
        self.assertEqual((css["bar"], css["panel"], css["log"]), ("none", "none", "none"))
        self.assertEqual(css["body"], "rgb(255, 255, 255)")
        self.assertEqual(css["chapter"], "page")
        self.assertNotEqual(css["credits"], "none", "credits open in print")


@extended
class B20_WideLayout(Base):
    def test_B20_rail(self):
        page = self.open(self.new_context(**WIDE))
        wait_images(page)
        expect(page.locator(".rail")).to_be_visible()
        self.assertEqual(page.locator(".rail-list li").count(), 15)
        self.assertGreaterEqual(page.evaluate("document.querySelector('main').getBoundingClientRect().left"), 380)
        page.evaluate("() => { const el = document.getElementById('day-9'); window.scrollTo(0, scrollY + el.getBoundingClientRect().top - Math.round(innerHeight * 0.38) + 2); }")
        expect(page.locator(".rail-list li").nth(8)).to_have_class(re.compile(r"\bon\b"))
        expect(page.locator(".rail-list li.on")).to_have_count(1)

    def test_B20_tablet(self):
        page = self.open(self.new_context(**TABLET))
        self.assertTrue(page.locator(".rail").is_hidden())
        expect(page.locator("#bar")).to_be_visible()


@extended
class B18_Keyboard(Base):
    def test_B18_focus_order_and_rings(self):
        page = self.open(self.new_context(**WIDE))
        wait_images(page)
        seen = []
        for _ in range(240):        # the rail, the cover, the calendar and the first chapter's prose links, up to its second picture
            page.keyboard.press("Tab")
            info = page.evaluate("""() => { const el = document.activeElement; if (!el || el === document.body) return null; const cs = getComputedStyle(el);
                return {id: el.id, cls: String(el.className).split(' ')[0], tag: el.tagName, cal: !!el.closest('#cal'),
                        ring: (cs.outlineStyle !== 'none' && parseFloat(cs.outlineWidth) > 0) || cs.boxShadow !== 'none', fv: el.matches(':focus-visible')}; }""")
            if info:
                seen.append(info)
            if sum(1 for s in seen if (s["id"] or s["cls"]) == "photo") >= 2:
                break
        names = [(s["id"] or s["cls"]) for s in seen]
        self.assertIn("tile", names)
        photos = [i for i, n in enumerate(names) if n == "photo"]
        cal_first = next(i for i, s in enumerate(seen) if s["cal"])
        self.assertLess(photos[0], names.index("tile"), "the cover picture, then the tile")
        self.assertLess(names.index("tile"), cal_first, "the tile, then the calendar")
        self.assertLess(cal_first, photos[1], "the calendar, then the first chapter's picture")
        no_ring = [n for s, n in zip(seen, names) if s["fv"] and not s["ring"] and s["tag"] in ("BUTTON", "A")]
        self.assertEqual(no_ring, [], "focused controls without a visible ring")


# ---------------------------------------------------------------- main
def main():
    global ARGS
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("-k", help="only tests whose id contains this")
    ap.add_argument("--all", action="store_true", help="include the extended checks")
    ap.add_argument("--update-golden", action="store_true", help="rewrite golden/astro.txt")
    ap.add_argument("--headed", action="store_true", help="show the browser")
    ap.add_argument("-v", "--verbose", action="store_true")
    ARGS = ap.parse_args()
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(sys.modules[__name__])
    if ARGS.k:
        flat = unittest.TestSuite()
        for group in suite:
            for t in group:
                if ARGS.k.lower() in t.id().lower():
                    flat.addTest(t)
        suite = flat
    result = unittest.TextTestRunner(verbosity=2 if ARGS.verbose else 1).run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)


if __name__ == "__main__":
    main()
