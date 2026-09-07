#!/usr/bin/env python
"""follow.py savedfile regex base_url [n] -> prints matching links (absolute), first n"""
import sys,re,urllib.parse
f,rx,base=sys.argv[1],sys.argv[2],sys.argv[3]; n=int(sys.argv[4]) if len(sys.argv)>4 else 5
txt=open(f,encoding='utf-8',errors='replace').read()
links=txt.split('### LINKS')[1].split('\n') if '### LINKS' in txt else []
seen=[];
for l in links:
    l=l.strip()
    if not l: continue
    if re.search(rx,l,re.I):
        a=urllib.parse.urljoin(base,l)
        if a not in seen: seen.append(a)
for a in seen[:n]: print(a)
