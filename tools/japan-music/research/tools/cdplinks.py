import sys,re
from playwright.sync_api import sync_playwright
url=sys.argv[1]; rx=sys.argv[2] if len(sys.argv)>2 else "."
with sync_playwright() as p:
    b=p.chromium.connect_over_cdp("http://127.0.0.1:9333"); ctx=b.contexts[0]; pg=ctx.new_page()
    try:
        pg.goto(url,wait_until="domcontentloaded",timeout=45000); pg.wait_for_timeout(3500)
        links=pg.evaluate("Array.from(document.querySelectorAll('a')).map(a=>[a.href,(a.innerText||'').replace(/\s+/g,' ').trim().slice(0,80)])")
        seen=set()
        for h,t in links:
            if h in seen: continue
            seen.add(h)
            if re.search(rx,h+" "+t,re.I): print(h,"|",t)
    finally: pg.close()
