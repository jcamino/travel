import sys,re
from playwright.sync_api import sync_playwright
url=sys.argv[1]
with sync_playwright() as p:
    b=p.chromium.connect_over_cdp("http://127.0.0.1:9333"); ctx=b.contexts[0]; pg=ctx.new_page()
    try:
        pg.goto(url,wait_until="load",timeout=45000); pg.wait_for_timeout(3000)
        for f in pg.frames:
            try:
                t=f.evaluate("document.body?document.body.innerText:''")
            except Exception as e: t=""
            t=re.sub(r"\n\s*\n+","\n",t or "")
            print("### FRAME",f.url); print(t[:6000])
    finally: pg.close()
