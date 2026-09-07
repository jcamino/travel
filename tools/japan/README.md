# /japan — source and build

The page at `public/japan/index.html` is generated. Edit the markdown, not
the HTML.

| File | What it is |
|---|---|
| `trip.md` | **The source of truth.** JSON front matter for what describes the whole week (title, dates, who, the about lines, the status legend, the holidays, the open items) then one section per day and one block per item. |
| `page.html` | The page itself: markup, styles, and the script that renders a day. One marker line, `/* TRIP GOES HERE, FROM trip.md */`, says where the trip goes. |
| `tripbook.py` | The dialect, and the only file that knows it. Reads `trip.md` into the trip, writes the trip back out as the TRIP object literal. |
| `build.py` | Puts the second inside the first. `python tools/japan/build.py [output.html]`. |

    python tools/japan/build.py
    python tests/japan/ux_check.py     # renders and screenshots the result

## The dialect

    ## 2026-09-19 | Sat | 19 | Tokyo | Arrive Tokyo
    {base} Hotel Son Shibuya
    {daynote} ...                      repeatable, optional

    ### 15:00 | Both in Tokyo by about 15:00
    {status} decided
    {end} 16:44                        optional
    {approx} {music} {travel}          flags, present or absent
    {ticket} pending                   optional
    {detail} ...                       always present, may be empty
    {place} ... {map} ... {url} ...    always present, may be empty
    {musicref} ...                     optional, the line on /japan/music
    {extramap} label | query           optional, a second map pin
    {conf} ... {via} ... {car} ...     optional booking fields, may be empty
    - a note                           repeatable

None of `* ` [ ] { } |` occurs in the trip's own text, so the markers need no
escaping; a `"` is written plainly and escaped on the way into JS.

## On the JS layout

The TRIP object used to be hand-formatted, and its line breaks followed no
rule: one item kept a 141-character line, another split at 105. `tripbook.py`
writes one fixed shape instead — a key group per line, every note on its own
line — so editing a note is a one-line diff. Converting to it re-wrapped 250
lines of literal into 300 and changed nothing else: the parsed TRIP is
deep-equal to what it was, the rendered text is identical, and every byte
outside the literal is unchanged.
