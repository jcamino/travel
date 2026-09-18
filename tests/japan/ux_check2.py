#!/usr/bin/env python3
"""Browser check for /japan2/, the typhoon copy of the trip.

/japan's own check counts that trip's items, so it cannot be pointed here.
This one asks only what holds for any trip built from page.html, plus the one
thing /japan2 adds: the alert above the days.

usage: python tests/japan/ux_check2.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ux_check as ux  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

check, fails = ux.check, ux.fails
NOW = "/japan2/?now=2026-09-19T10:00"


def run():
    srv, base = ux.serve()
    src = (ux.PUB / "japan2" / "index.html").read_text(encoding="utf-8")
    check("—" not in src, "no em dashes in the page")
    check('"japan2-picks"' in src, "picks are stored apart from /japan's")
    with sync_playwright() as p:
        b = p.chromium.launch()
        for width, height, name in [(380, 800, "phone-380"), (1280, 900, "desktop-1280")]:
            ctx = b.new_context(viewport={"width": width, "height": height}, device_scale_factor=2,
                                timezone_id="Asia/Tokyo", reduced_motion="reduce")
            page = ctx.new_page()
            errors = []
            page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.goto(base + NOW, wait_until="networkidle")
            check(not errors, f"{name}: no console errors {errors[:2]}")
            check(page.locator(".day-tab").count() == 8, f"{name}: eight day tabs")
            check(page.locator(".day-tab[aria-current=date]").get_attribute("data-day") == "2026-09-19",
                  f"{name}: today (19th) selected on load")
            check(page.locator("#trip-alert").is_visible(), f"{name}: the alert shows")
            check(page.locator("#trip-alert .cell").count() == 5, f"{name}: five days in the outlook")
            check(page.locator("#trip-alert .cell[data-risk=high]").count() >= 1, f"{name}: a day is marked high risk")
            check(page.locator("#trip-alert .links a").count() >= 2, f"{name}: the alert links out to the live sources")
            check(page.locator("#trip-source").inner_text() == "tools/japan/trip2.md", f"{name}: footer names trip2.md")
            ux.no_overflow(page, name, "collapsed")
            page.screenshot(path=str(ux.SHOTS / f"japan2-{name}-light.png"), full_page=False)
            for tab in page.locator(".day-tab").all():
                d = tab.get_attribute("data-day")
                tab.click()
                ux.no_overflow(page, name, "day " + d)
                strip_list = page.evaluate(
                    "d => [...document.querySelectorAll(`.day-tab[data-day='${d}'] .dots svg`)].map(e => e.dataset.status)", d)
                rail_list = page.evaluate(
                    "() => [...document.querySelectorAll('.day .item .stop svg')].map(e => e.dataset.status)")
                check(strip_list == rail_list and strip_list != [],
                      f"{name}: {d} strip glyphs match the rail one for one")
            page.click(".day-tab[data-day='2026-09-19']")
            for btn in page.locator(".card-head").all():
                btn.click()
            ux.no_overflow(page, name, "Sat 19, all cards expanded")
            page.screenshot(path=str(ux.SHOTS / f"japan2-{name}-sat19-expanded.png"), full_page=True)
            page.click(".day-tab[data-day='2026-09-21']")
            for btn in page.locator(".card-head").all():
                btn.click()
            ux.no_overflow(page, name, "Mon 21, all cards expanded")
            page.screenshot(path=str(ux.SHOTS / f"japan2-{name}-mon21-expanded.png"), full_page=True)
            page.click("#theme")
            ux.no_overflow(page, name, "dark mode")
            page.screenshot(path=str(ux.SHOTS / f"japan2-{name}-dark.png"), full_page=False)
            ctx.close()
        b.close()
    srv.shutdown()
    print(f"\n{len(fails)} failure(s)")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    run()
