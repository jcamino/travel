# /japan/music — the research behind the book

What `../japan-only-music-book.md` was written from, in the state it was read
on 5–6 September 2026. Nothing here is built or published; it is the evidence
for the VERIFIED and SECONDARY badges on the page, and the kit to sweep again.

| | |
|---|---|
| `brief.md` | The self-contained brief the book answers: what live music in Silver Week could two Brooklyn residents not see at home. Defines the ranking test (distance from Brooklyn first, then whether you can get in) and the tier scheme. |
| `grok-plan.md` | The parallel non-jazz brief, ranked by irreproducibility in New York with jazz flagged only for collisions. Pass 10 reviewed it against the organisers' own pages and took the candle noh at 御香宮, the Matsuo and Hirano moon rites, the Uneme times and the BALZAC revival into the book. |
| `pages/` | 390 dated snapshots of organisers' and venues' own pages, each headed `### <status> <url>`. These are the receipts: venue pages change, and after September there is no other way to show what was read. Safe to delete once the trip is over. |
| `lists/` | The `name\|url` sweeps `tools/batch.sh` was pointed at, A through E and J. They record what was checked, including what came back empty. |
| `sources/` | The primary documents that are not HTML: the Cabinet Office holiday CSV behind the three-holiday claim, and the Tsukiji, Higashi and Hōshō concert PDFs and flyer. |
| `plans/` | Three redesign briefs written 2026-09-06 and given to subagents — moon week, flyer wall, route diagram. The flyer wall won, was published, and was itself replaced by the Akira design; the other two were built and removed. This is the only record of what they were. |

## tools/

The harvest kit, kept because the next sweep would otherwise rewrite it.

- `fetch.py URL [--links] [--raw]` — urllib fetch with charset detection
  (Shift-JIS and EUC both turn up on shrine sites), tag stripping, link list.
- `batch.sh listfile regex [n]` — fetch a `name|url` list into `p_name.txt`
  and grep each one.
- `follow.py savedfile regex base [n]` — pick links out of a saved page.
- `cdp.py URL [--wait ms] [--html]` — innerText through the logged-in Chrome
  on :9333, for the pages that render nothing without JS: e+, Loft, La.mama,
  Dommune, Quattro.
- `cdplinks.py URL regex` / `cdpframes.py URL` — anchor list and frameset
  text via CDP. Shinjuku Pit Inn's neighbour, the Lion, is still a frameset.

## Not kept

The nine superseded HTML passes, the `pass*.py` one-shot edit scripts that
produced them, the Declaude run output, the design screenshots and the
working scraps stay outside this repo in `Code/japan/music/japan-only/`.
The book's own history is in git now, which is what those recorded.
