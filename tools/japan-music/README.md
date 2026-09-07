# /japan/music — source and build

The page at `public/japan/music/index.html` is generated. Edit the markdown,
not the HTML.

The published page is the traveler book: the five plates, what to book
before the flight, the week as a calendar, and two reference tables. The
uncut research dump — every room checked, including misses — is
`research/japan-only-music-book.full.md`.

| File | What it is |
|---|---|
| `japan-only-music-book.md` | **The source of truth.** JSON front matter (page title, the trip shape day by day, the five flyer faces) then the traveler book in the markdown dialect below. |
| `mdbook.py` | The dialect, and the only file that knows it. `python tools/japan-music/mdbook.py` renders the source and reads it back; the markdown must come out the same. Run it before building. |
| `akira-build.py` | The design. Reads the markdown, writes the page. Defaults to the `public/japan/music-akira/` staging path, so pass the real path only once the gate is green. |
| `HANDOFF.md` | The one copy pass still owed on the source, and why it is only 41 lines. |
| `research/` | The uncut book, the brief, the Grok brief, the 390 dated page snapshots behind the VERIFIED badges, the primary-source PDFs, the sweep lists, the redesign plans and the harvest kit. Nothing here is built. |

Build and check:

    python tools/japan-music/mdbook.py
    python tools/japan-music/akira-build.py public/japan/music/index.html
    python tests/japan-music/content_check.py public/japan/music/index.html

## The design, and the candidates

`akira-build.py` now emits the **4-6 design** — the sticky rail with the
seven-night film strip — plus two things lifted from the 3-8 candidate:

- the **scroll-progress line** (cyan → red) along the rail's bottom edge, and
- the **live filter**: search box, category chips, `/` to focus, `Esc` to clear.

`/japan/music-3-1/` and `/japan/music-3-8/` are frozen static HTML kept for
comparison; nothing generates them, so **they are not rebuildable** — edit the
HTML or throw the page away. `/japan/music-4-6/` is the 4-6 design *before* the
two 3-8 borrowings, and is still reproducible from `9e4c992`'s builder.

Two traps, both found the hard way:

- **`.day` is two different things.** It is the calendar's
  `<details class="day">` (7 of them) *and* the slot column of every per-day
  table, `<td class="day">` (95 of them). Anything that filters nights must say
  `details.day`, or it hides table cells and reports inflated match counts. The
  3-8 candidate has this bug.
- **`.rail` is `position:sticky`.** That is already a positioned value, so it
  contains the absolutely positioned progress line. Re-declaring
  `position:relative` on it further down the sheet silently kills the sticky.

## The dialect

One markdown line renders to one HTML line, in order, so a diff of the source
reads as a diff of the page.

    {kicker} ...          <div class="kicker">
    # / ## / ###          h1 / h2 / h3
    {lede} {legend}       <p class="lede"> / <p class="legend">
    {note} {meta} {also}  the note box, a card's source line, "Also that day"
    {small} ...           <p><small>...</small></p>
    anything else         <p>...</p>
    {cards} {cards night} a card list; {/cards} closes it
    {card} Title          a card; {card flag} Title is a must-surface card
    {www} What: a | When: b | Where: c | Cost: d
    {ul} {ol} with "- x"  lists
    {table} with "| a |"  a table; the first row is the header, .day marks the
                          slot column; {/table} closes it
    ^                     glue this line onto the one before it

Inline: `**strong**`, `*em*`, `` `code` ``, `[text](url)`, and the badges
`{v:VERIFIED}`, `{s:SECONDARY}`, `{t1:Tier 1}`, `{t2:...}`, `{t3:...}`,
`{smp:SAMPLER}`. Write `&` as itself; the renderer escapes it. There is no
escaping mechanism and none is needed: none of `* ` [ ] { } |` occurs in the
book's own text, which is what makes the mapping reversible.

The research notebook the book was written from — the raw fetches, the pass
scripts, the redesign plans, the frozen `japan-only-music-book.plain.html`
this markdown was converted from — is outside this repo, in
`Code/japan/music/japan-only/`.
