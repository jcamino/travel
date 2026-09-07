# /japan/music — source and build

The page at `public/japan/music/index.html` is generated. Edit the markdown,
not the HTML.

The published page is the traveler book: the five plates, the week as a
calendar, what to book before the flight, and two reference tables. The
uncut research dump — every room checked, including misses — is
`research/japan-only-music-book.full.md`.

| File | What it is |
|---|---|
| `japan-only-music-book.md` | **The source of truth.** JSON front matter (page title, the trip shape day by day, the five flyer faces) then the traveler book in the markdown dialect below. |
| `mdbook.py` | The dialect, and the only file that knows it. `python tools/japan-music/mdbook.py` renders the source and reads it back; the markdown must come out the same. Run it before building. |
| `akira-build.py` | The design. Reads the markdown, writes the page. Defaults to the `public/japan/music-akira/` staging path, so pass the real path only once the gate is green. |
| `research/` | The uncut book, the brief, the Grok brief, the 390 dated page snapshots behind the VERIFIED badges, the primary-source PDFs, the sweep lists, the redesign plans and the harvest kit. Nothing here is built. |

Build and check:

    python tools/japan-music/mdbook.py
    python tools/japan-music/akira-build.py public/japan/music/index.html
    python tests/japan-music/content_check.py public/japan/music/index.html

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
