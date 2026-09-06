#!/usr/bin/env python3
"""Browser check for /japan/: overflow at 380 and 1280, console errors, filters, hash state,
now-marker, bookings view, dark mode, print, and screenshots into screenshots/.

usage: python tests/japan/ux_check.py
"""
import functools
import http.server
import re
import sys
import threading
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
PUB = ROOT / "public"
SHOTS = ROOT / "screenshots"
SHOTS.mkdir(exist_ok=True)


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


def serve():
    handler = functools.partial(Quiet, directory=str(PUB))
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, f"http://127.0.0.1:{srv.server_address[1]}"


fails = []


def check(cond, msg):
    print(("ok   " if cond else "FAIL ") + msg)
    if not cond:
        fails.append(msg)


OVERFLOW_JS = """() => {
  const w = document.documentElement.clientWidth;
  const bad = [];
  for (const el of document.querySelectorAll('body *')) {
    const r = el.getBoundingClientRect();
    if (r.width === 0) continue;
    if (el.closest('.strip')) continue;
    if (r.right > w + 1 || r.left < -1) bad.push(el.tagName + '.' + el.className + ' ' + Math.round(r.left) + '..' + Math.round(r.right));
  }
  return { scrollW: document.documentElement.scrollWidth, w, bad: bad.slice(0, 8) };
}"""


def no_overflow(page, name, what):
    o = page.evaluate(OVERFLOW_JS)
    check(o["scrollW"] <= o["w"] and not o["bad"], f"{name}: no horizontal overflow, {what} {o['bad']}")


BG = "getComputedStyle(document.body).backgroundColor"
DARK_BG, LIGHT_BG = "rgb(18, 19, 23)", "rgb(239, 234, 224)"


def theme_follows_system(b, base):
    """A manual toggle overrides the system only until the phone itself changes scheme."""
    def load(scheme, state=None):
        kw = {"color_scheme": scheme, "viewport": {"width": 380, "height": 800}}
        if state:
            kw["storage_state"] = state
        ctx = b.new_context(**kw)
        pg = ctx.new_page()
        pg.goto(base + "/japan/")
        return ctx, pg
    ctx, pg = load("dark")
    check(pg.evaluate(BG) == DARK_BG, "theme: fresh load follows system dark")
    ctx.close()
    ctx, pg = load("light")
    check(pg.evaluate(BG) == LIGHT_BG, "theme: fresh load follows system light")
    pg.click("#theme")
    check(pg.evaluate(BG) == DARK_BG, "theme: toggle flips to dark")
    state = ctx.storage_state()
    ctx.close()
    ctx, pg = load("light", state)
    check(pg.evaluate(BG) == DARK_BG, "theme: manual dark survives a reload while the phone is still light")
    state = ctx.storage_state()
    ctx.close()
    ctx, pg = load("dark", state)
    check(pg.evaluate(BG) == DARK_BG, "theme: phone goes dark, page is dark")
    state = ctx.storage_state()
    ctx.close()
    ctx, pg = load("light", state)
    check(pg.evaluate(BG) == LIGHT_BG, "theme: phone back to light, page follows (override dropped)")
    ctx.close()
    # a phone pinned by the old build (plain string in storage) must follow the system again
    ctx, pg = load("dark")
    pg.evaluate("localStorage.setItem('japan-theme', 'light')")
    pg.reload()
    check(pg.evaluate(BG) == DARK_BG, "theme: legacy stored value is discarded")
    ctx.close()
    # live change while the page is open
    ctx, pg = load("light")
    pg.click("#theme")
    pg.emulate_media(color_scheme="dark")
    pg.wait_for_timeout(50)
    pg.emulate_media(color_scheme="light")
    pg.wait_for_timeout(50)
    check(pg.evaluate(BG) == LIGHT_BG, "theme: live system change while open drops the override")
    ctx.close()


def run():
    srv, base = serve()
    src = (PUB / "japan" / "index.html").read_text(encoding="utf-8")
    check("—" not in src, "no em dashes in the page")
    with sync_playwright() as p:
        b = p.chromium.launch()
        theme_follows_system(b, base)
        for width, height, name in [(380, 800, "phone-380"), (1280, 900, "desktop-1280")]:
            ctx = b.new_context(viewport={"width": width, "height": height}, device_scale_factor=2,
                                timezone_id="Asia/Tokyo", reduced_motion="reduce")
            page = ctx.new_page()
            errors = []
            page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.goto(base + "/japan/?now=2026-09-23T15:00", wait_until="networkidle")
            check(not errors, f"{name}: no console errors {errors[:2]}")
            check(page.locator(".day-tab").count() == 8, f"{name}: eight day tabs")
            check(page.locator(".day-tab[aria-current=date]").get_attribute("data-day") == "2026-09-23",
                  f"{name}: today (23rd) selected on load")
            check(page.locator(".item.is-now").count() == 1, f"{name}: one item marked now")
            check("Nozomi" in page.locator(".item.is-now .title").inner_text(),
                  f"{name}: now item is the 14:30 Nozomi at 15:00")
            no_overflow(page, name, "collapsed")
            for btn in page.locator(".card-head").all():
                btn.click()
            no_overflow(page, name, "all cards expanded")
            page.screenshot(path=str(SHOTS / f"japan-{name}-expanded.png"), full_page=True)
            for btn in page.locator(".card-head").all():
                btn.click()
            page.click(".chip[data-filter=pending]")
            check("filter=pending" in page.url, f"{name}: pending filter in hash")
            vis = page.locator(".item:not(.hidden)").count()
            check(vis == 1, f"{name}: Wed 23 pending filter shows one item (got {vis})")
            page.click(".chip[data-filter=music]")
            check(page.locator(".item:not(.hidden)").count() == 1, f"{name}: music filter shows the Tatsuro item")
            page.click(".chip[data-filter=all]")
            for tab in page.locator(".day-tab").all():
                tab.click()
                no_overflow(page, name, "day " + tab.get_attribute("data-day"))
            # the strip glyphs must be exactly the statuses the day's rail shows
            for tab in page.locator(".day-tab").all():
                d = tab.get_attribute("data-day")
                tab.click()
                strip_set = sorted(set(page.evaluate(
                    "d => [...document.querySelectorAll(`.day-tab[data-day='${d}'] .dots svg`)].map(e => e.dataset.status)", d)))
                rail_set = sorted(set(page.evaluate(
                    "() => [...document.querySelectorAll('.day .item .stop svg')].map(e => e.dataset.status)")))
                check(strip_set == rail_set and strip_set != [],
                      f"{name}: {d} strip glyphs match the rail ({strip_set} vs {rail_set})")
            page.click(".day-tab[data-day='2026-09-25']")
            g = page.locator("a[data-map=google]").count()
            a = page.locator("a[data-map=apple]").count()
            check(g >= 6 and a >= 6, f"{name}: map links on Fri 25 ({g} google, {a} apple)")
            check(all(x.get_attribute("target") == "_blank" for x in page.locator("a[data-map]").all()),
                  f"{name}: map links open in a new tab")
            page.click(".view-btn[data-view=bookings]")
            check("view=bookings" in page.url, f"{name}: bookings view in hash")
            n = page.locator(".bk").count()
            check(n == 7, f"{name}: seven booked items (got {n})")
            check(page.locator(".bk .blank").count() >= 14, f"{name}: blank confirmation fields present")
            no_overflow(page, name, "bookings")
            page.screenshot(path=str(SHOTS / f"japan-{name}-bookings.png"), full_page=True)
            page.click(".view-btn[data-view=days]")
            page.goto(base + "/japan/#day=2026-09-25&filter=walkup", wait_until="networkidle")
            check(page.locator(".day-tab[aria-current=date]").get_attribute("data-day") == "2026-09-25",
                  f"{name}: hash selects Fri 25")
            check(page.locator(".chip[data-filter=walkup]").get_attribute("aria-pressed") == "true",
                  f"{name}: hash selects walk-up chip")
            page.goto(base + "/japan/?now=2026-09-23T15:00", wait_until="networkidle")
            page.screenshot(path=str(SHOTS / f"japan-{name}-light.png"), full_page=False)
            page.keyboard.press("Tab")
            page.keyboard.press("Tab")
            page.keyboard.press("Tab")
            focused = page.evaluate("() => document.activeElement.tagName + ' ' + getComputedStyle(document.activeElement).outlineStyle")
            check(focused.startswith(("BUTTON", "A")) and "none" not in focused, f"{name}: keyboard focus lands on a control with a visible outline ({focused})")
            page.click("#theme")
            check(page.evaluate("() => document.documentElement.getAttribute('data-theme')") == "dark",
                  f"{name}: manual dark toggle")
            page.screenshot(path=str(SHOTS / f"japan-{name}-dark.png"), full_page=False)
            no_overflow(page, name, "dark mode")
            page.emulate_media(media="print")
            page.evaluate("() => window.dispatchEvent(new Event('beforeprint'))")
            check(page.locator(".day").count() == 8, f"{name}: print renders all eight days")
            page.emulate_media(media="screen")
            page.evaluate("() => window.dispatchEvent(new Event('afterprint'))")
            check(page.locator(".day").count() == 1, f"{name}: back to one day after print")
            ctx.close()
        b.close()
    srv.shutdown()
    print(f"\n{len(fails)} failure(s)")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    run()
