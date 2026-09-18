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
    python tests/japan/dialect_check.py # trip.md round-trips, branches are sound
    python tests/japan/ux_check.py      # renders and screenshots the result

## /japan2, the typhoon copy

`trip2.md` is the same week replanned around Typhoon No. 25 (Dujuan), written
on the night of Fri 18 Sept 2026, and it builds through the same page:

    python tools/japan/build.py public/japan2/index.html tools/japan/trip2.md
    python tests/japan/dialect_check.py tools/japan/trip2.md
    python tests/japan/ux_check2.py

Three front-matter keys exist for it, and a trip that leaves them out builds
exactly as before. `alert` is the box above the days: a title, an `issued`
line saying when the forecast was read, an `outlook` of day cells with a
`risk` of low, mid or high, the `lines`, and `links` to the live sources. The
box is static on purpose, so the `issued` line has to be true. `source` names
the file in the footer. `picksKey` is the localStorage key for branch picks,
because two trips on one origin would otherwise share `japan-picks`, and both
have a fork on the 19th. `public/japan2/sw.js` is its own worker for the same
reason: its own cache name and its own page.

A page with an alert opens at the top instead of scrolling to the current
item, so the alert is read first.

## The dialect

    ## 2026-09-19 | Sat | 19 | Tokyo | Arrive Tokyo
    {base} Hotel Son Shibuya
    {daynote} ...                      repeatable, optional
    {branchgroup} id | label           repeatable, optional

    ### 15:00 | Both in Tokyo by about 15:00
    {branch} groupId | optionId        optional, joins a branch group
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

## On branches

A branch is a set of items on one day of which only one can happen: on the
24th it is the Inari summit, the Fushimi sake tasting, or the Uji tea stop,
and there is time for one. The day declares the fork with `{branchgroup}` and
each item joins it with `{branch}`, so the conflict lives in the data rather
than in a note reading "one or the other".

Two things follow from the shape. Option ids are slugs, not positions, so a
choice already made survives an edit to this file — and an option id that has
since disappeared reads as *no choice*, never as a day with every option
struck through. And one option may cover several items: on the 23rd, `gion`
is both the dusk walk and the dinner after it, because they are one plan.

The rail draws this literally. A branch line leaves the trunk just above a
group's first item, runs alongside carrying that group's stops, and rejoins
just below its last. Members need not be adjacent: on the 24th the JR to
Nara sits between the sake and Uji and belongs to no option, so it stays on
the trunk while the branch runs past it. Two forks on one day may therefore
not overlap — the second would paint over the first — and `dialect_check.py`
asserts they don't. The junctions are drawn clear of `--stop-r`, the glyph
radius, because a stop's disc is opaque and would otherwise swallow them.

Choosing is the browser's business, not the trip's. Picks live in
`localStorage` under `japan-picks`, keyed `date/group`, and nothing is dimmed
until you pick; tapping the chosen option again undecides the fork. `trip.md`
stays the source of truth, so a fork that settles for good gets written back
here as `{status} decided` and its `{branch}` lines deleted.

## On the JS layout

The TRIP object used to be hand-formatted, and its line breaks followed no
rule: one item kept a 141-character line, another split at 105. `tripbook.py`
writes one fixed shape instead — a key group per line, every note on its own
line — so editing a note is a one-line diff. Converting to it re-wrapped 250
lines of literal into 300 and changed nothing else: the parsed TRIP is
deep-equal to what it was, the rendered text is identical, and every byte
outside the literal is unchanged.
