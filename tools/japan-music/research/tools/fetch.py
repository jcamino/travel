#!/usr/bin/env python
"""fetch.py URL [--raw] [--max N] : fetch URL, decode charset, strip to text."""
import sys, re, html, urllib.request, urllib.error, ssl, gzip, io
from html.parser import HTMLParser
UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0.0.0 Safari/537.36"
class T(HTMLParser):
    def __init__(s):
        super().__init__(); s.out=[]; s.skip=0; s.links=[]
    def handle_starttag(s,tag,attrs):
        if tag in("script","style","noscript","svg"): s.skip+=1
        if tag in("p","div","br","li","tr","h1","h2","h3","h4","h5","dt","dd","section","article","table"): s.out.append("\n")
        if tag=="td" or tag=="th": s.out.append(" | ")
        if tag=="a":
            for k,v in attrs:
                if k=="href": s.links.append(v)
    def handle_endtag(s,tag):
        if tag in("script","style","noscript","svg"): s.skip=max(0,s.skip-1)
        if tag in("p","div","li","tr","h1","h2","h3","h4","h5","dd","section","article","table"): s.out.append("\n")
    def handle_data(s,d):
        if not s.skip: s.out.append(d)
def get(url,timeout=25):
    ctx=ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE
    req=urllib.request.Request(url,headers={"User-Agent":UA,"Accept-Language":"ja,en;q=0.8","Accept":"text/html,*/*","Accept-Encoding":"gzip"})
    r=urllib.request.urlopen(req,timeout=timeout,context=ctx)
    data=r.read()
    if r.headers.get("Content-Encoding")=="gzip": data=gzip.decompress(data)
    ct=r.headers.get("Content-Type","")
    m=re.search(r"charset=([\w-]+)",ct,re.I); cs=m.group(1) if m else None
    if not cs:
        m=re.search(rb'charset=["\']?([\w-]+)',data[:4000],re.I); cs=m.group(1).decode() if m else "utf-8"
    cs=cs.lower().replace("shift_jis","cp932").replace("shift-jis","cp932").replace("x-sjis","cp932").replace("euc-jp","euc_jp")
    try: txt=data.decode(cs,errors="replace")
    except LookupError: txt=data.decode("utf-8",errors="replace")
    return r.geturl(), r.status, txt
if __name__=="__main__":
    url=sys.argv[1]; raw="--raw" in sys.argv; links="--links" in sys.argv
    mx=200000
    for i,a in enumerate(sys.argv):
        if a=="--max": mx=int(sys.argv[i+1])
    try:
        final,st,txt=get(url)
    except urllib.error.HTTPError as e:
        print(f"HTTP {e.code} {url}"); sys.exit(1)
    except Exception as e:
        print(f"ERR {type(e).__name__}: {e} {url}"); sys.exit(1)
    print(f"### {st} {final}")
    if raw: print(txt[:mx]); sys.exit()
    p=T(); p.feed(txt)
    out=html.unescape("".join(p.out))
    out=re.sub(r"[ \t\u3000]+"," ",out); out=re.sub(r"\n\s*\n+","\n",out)
    print(out[:mx])
    if links:
        print("### LINKS"); 
        seen=set()
        for l in p.links:
            if l not in seen: seen.add(l); print(l)
