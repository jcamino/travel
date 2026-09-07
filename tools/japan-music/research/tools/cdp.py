#!/usr/bin/env python
"""cdp.py URL [--wait ms] [--sel css] [--html] : open in CDP chrome :9333, print innerText, close tab."""
import sys, re, asyncio
from playwright.sync_api import sync_playwright
url=sys.argv[1]; wait=2500; sel=None; want_html="--html" in sys.argv; mx=200000
for i,a in enumerate(sys.argv):
    if a=="--wait": wait=int(sys.argv[i+1])
    if a=="--sel": sel=sys.argv[i+1]
    if a=="--max": mx=int(sys.argv[i+1])
with sync_playwright() as p:
    b=p.chromium.connect_over_cdp("http://127.0.0.1:9333")
    ctx=b.contexts[0]
    pg=ctx.new_page()
    try:
        pg.goto(url,wait_until="domcontentloaded",timeout=45000)
        pg.wait_for_timeout(wait)
        if sel:
            try: pg.wait_for_selector(sel,timeout=8000)
            except Exception as e: print("(sel timeout)")
        print("###",pg.url,"|",pg.title())
        if want_html: print(pg.content()[:mx])
        else:
            t=pg.evaluate("document.body.innerText")
            t=re.sub(r"\n\s*\n+","\n",t); print(t[:mx])
    finally:
        pg.close()
