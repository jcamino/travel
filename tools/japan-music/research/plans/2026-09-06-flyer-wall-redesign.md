# Flyer wall (チラシ) redesign of /japan/music

> **For agentic workers:** REQUIRED: invoke `frontend-design:frontend-design` before designing. Work through every task in order, run the gates in Task 6, and report screenshots-reviewed status honestly.

**Goal:** Rebuild `https://travel.jcamino.net/japan/music/` as a live-house lobby wall: the top five picks are A5 handbills pinned up in a two-colour risograph print, the rest of the research is a dense listings magazine underneath. Same research content, word for word. New URL: `https://travel.jcamino.net/japan/music-flyers/`.

**Architecture:** One self-contained HTML file with inline CSS and a small inline vanilla-JS block (flyer expand/collapse, listing-to-flyer jump). Google Fonts by `<link>`. No build step, no framework, no raster images. Riso texture, if any, is CSS or inline SVG only.

**Source of truth:** `C:\Users\jcamino\Code\travel\public\japan\music\index.html` (the current page). Read it fully first. It is ~130 KB: one `<h1>`, 14 `<h2>` sections, ~90 `<h3>`, 60 `.card` entries, 12 tables, one `.note`, tags `.v` VERIFIED, `.s` SECONDARY, `.t1/.t2/.t3` tiers, `.smp` sold-out-ish, `.flagcard`.

**Output:** `C:\Users\jcamino\Code\travel\public\japan\music-flyers\index.html`. Nothing else in the travel repo may change. Do not touch `public/japan/music/index.html`. **Do not run any git command.** The orchestrator commits and pushes.

**Hard rules**
- Every sentence, number, price, link, and tag of the source survives. The gate `python tests/japan-music/content_check.py public/japan/music-flyers/index.html` must exit 0. You may add navigation labels, flyer chrome (OPEN / START / ¥ lines built from data already in the entry), and a legend; you may not paraphrase or trim research copy. Flyer chrome duplicates data, it does not replace the source sentences, which stay on the flyer's back or below the fold.
- Section order may change only in that section 0 (top five) becomes the wall. Sections 1 to 10 and the appendix keep their order and their numbering text.
- Tables stay tables (horizontal scroll on phones is fine).
- Quality floor: 390 px phone to 1440 px desktop with no horizontal overflow, keyboard focus visible, `prefers-reduced-motion` honoured, body text contrast at least 4.5:1 (riso pink on newsprint is not enough for body text; use it for display and blocks only), line length under 80 characters, `lang="en"`, Japanese text renders in a font that covers kanji (check in screenshots).
- No AI-default tells: no all-caps eyebrow labels you invent (real flyers do print OPEN / START in caps; that is the vernacular and is allowed on the flyers only), no single-word colour accent in headlines, no `01 / 02 / 03` markers, no middle-dot meta strings you introduce yourself, no fade-up-on-scroll on every section, no `→` on links, no rounded-card kit with identical drop shadows.

---

## Design plan (revise before building, per the frontend-design skill)

**Subject:** seven nights of live music in Japan that two Brooklyn residents cannot see at home; the picks span a shrine rite, a city-pop hall show, a min'yō set in a jazz basement, a closing jazz club, and a dawn chant before a daxophone gig. Audience: the two travellers, on a phone in the lobby of one of these rooms, and on a laptop while booking. Primary job: choose and book before the trip, then find tonight's entry fast during the trip.

**Palette (base tokens):**

| Token | Hex | Role |
|---|---|---|
| newsprint | `#EDEBE4` | page and flyer paper |
| ink | `#1A1A1A` | body text, flyer type |
| riso-pink | `#FF48B0` | flyer colour 1, display blocks, Tier 1 |
| riso-blue | `#0078BF` | flyer colour 2, links, Tier 2 |
| stamp-red | `#D7263D` | the 済 VERIFIED hanko only |
| pencil | `#6B6B6B` | SECONDARY, meta, Tier 3 |

Dark mode: ship one. Invert paper to `#141414` with off-white ink `#ECEAE2`; riso colours stay, since fluorescent ink on black paper is a real riso look. Test both.

**Type:** Dela Gothic One for display (flyer dates, h1, h2). Zen Kaku Gothic Antique 400/700 for everything else, including the listings. Two families, clearly distinct. Scale: 15 px body phone, 16 px desktop, line-height 1.6; listings 13.5 px with 1.45; flyer date 4 to 6 rem in Dela Gothic; h2 1.5 rem Dela Gothic. Tabular numerals everywhere.

**Layout:**

```
┌───────────────────────────────────────────────────────────────┐
│ SILVER WEEK JAPAN-ONLY BOOK (h1, Dela Gothic, ink on paper)   │
│ lede + legend, as in source                                   │
│ note block ("Two facts that shape the week") as a pinned memo │
│                                                               │
│   ┌─────────┐  ┌─────────┐   ┌─────────┐  ┌─────────┐  ┌────┐ │
│   │ 九月    │  │ 九月    │   │ 九月    │  │ 九月    │  │    │ │
│   │ 25 金   │  │ 23 水   │   │ 20 日   │  │ 21 月   │  │ 24 │ │
│   │ Shimo-  │  │ 山下達郎│   │ Pit Inn │  │ Body &  │  │木  │ │
│   │ gamo →  │  │ Festival│   │ 東京民謡│  │ Soul    │  │    │ │
│   │ Yasaka  │  │ Hall    │   │ 倶楽部  │  │ last    │  │    │ │
│   │ OPEN    │  │ OPEN    │   │ OPEN    │  │ night   │  │    │ │
│   │ 17:30   │  │ 17:00   │   │ 14:00   │  │         │  │    │ │
│   │ ¥0     済│  │ ¥15,000│   │ ¥5,500 │  │ ¥7,700 │  │    │ │
│   └─────────┘  └─────────┘   └─────────┘  └─────────┘  └────┘ │
│   (each flyer tilted -2° to +3°, overlapping edges, one pin)  │
├───────────────────────────────────────────────────────────────┤
│ 1 · Ranked shortlist   ← listings grid, two columns desktop,   │
│   one column phone, each entry: day + time in Dela Gothic,    │
│   title, then the source paragraphs at 13.5 px                │
│ … sections 1b to Appendix in the same listings register       │
└───────────────────────────────────────────────────────────────┘
```

Left-aligned. Flyers are 3:4 portrait, ~260 px wide desktop, in a row that wraps to a 2+2+1 grid at tablet and a single column of full-width flyers at phone width (no tilt below 600 px; tilt reads as a bug on a phone). Content column below: 48 rem prose, tables up to 72 rem.

**The one memorable thing:** the five flyers. Each is a real handbill: month and day in Japanese numerals and the weekday kanji huge in Dela Gothic, the act name as the flyer's title, venue line, `OPEN hh:mm / START hh:mm` and `¥` lines pulled from the entry's meta, printed in two riso colours with a deliberate 1 to 2 px misregistration (duplicate the display text in the second colour offset by `translate(1.5px, -1px)` with `mix-blend-mode: multiply`). Keep the misregistration to the display type; body text on the flyer is plain ink. Each flyer's full source text (the "What happens / Why / Practical" paragraphs) is on the flyer, below the display block, at body size; on phone it is behind a "Read the flyer" toggle (a `<details>` element, open by default on desktop). The gate reads text regardless of `<details>` state.

Tilt: rotate each flyer by one of `-2.5deg, 1.5deg, -1deg, 3deg, -2deg` on desktop. A single pin (inline SVG circle with a short shadow) at the top centre. No other shadow.

**Tags:** VERIFIED renders as a red hanko: a rounded-square outline containing 済 in stamp-red, rotated -6°, with the word VERIFIED kept as visually hidden text or as small text beside it (the gate needs the word present in the DOM text). SECONDARY renders as pencil text 未確認 with the word SECONDARY beside it in `pencil`. Tiers: Tier 1 pink block, Tier 2 blue block, Tier 3 pencil outline, all with the words present.

**Listings register (sections 1 onward):** modelled on Pia's listings pages. Each `.card` becomes a listing: a Dela Gothic day-and-time slug on the left (`25 金 19:00`) and the h3 plus paragraphs to the right. Two-column grid on desktop with the slug column fixed at 5.5 rem. h2 section titles in Dela Gothic with a thick 4 px riso-pink rule below, alternating with riso-blue per section so the reader feels the sections change. Tables get a riso-blue header row and hairline rules.

**Motion:** none on load. User-triggered only: `<details>` open/close, and clicking a listing's slug scrolls to and briefly outlines (2 s, pink) the matching flyer if the listing is one of the top five (match by day and venue text; add `data-flyer="fri25"` etc. by hand). Reduced motion removes the outline animation.

**Review against the brief before building:** a two-colour riso print on newsprint is not on the generic-defaults list, but the listings section can slide into the "hairline broadsheet" default. Guard against that by using the thick riso rules, the Dela Gothic slug column, and the two-colour alternation. If the first draft looks like a newspaper, correct it and note the change in your report.

---

## Task 1: Read and inventory

1. Read `public/japan/music/index.html` end to end.
2. Read `tests/japan-music/content_check.py` so you know what the gate measures.
3. Write down (in your working notes) the 14 section headings, the five top-five entries with day, venue, open/start times and prices as they appear in the meta lines, and every CSS class used in the body with its meaning.

## Task 2: Skeleton and tokens

1. Create `public/japan/music-flyers/index.html` with `<!doctype html>`, `lang="en"`, viewport meta, title `Silver Week Japan-Only Book — Tokyo 19–22 / Kansai 23–25 Sept 2026`, Google Fonts link for Dela Gothic One and Zen Kaku Gothic Antique 400/700, and a `:root` with the tokens above plus a dark scheme.
2. Paste the whole source `<main>` inside, unchanged. Run the gate. It must pass before you restyle anything.

## Task 3: The wall

1. Convert section 0's five cards into five flyers in the order the source ranks them (Fri 25, Wed 23, Sun 20, Mon 21, Thu 24). Flyer display block per the plan; every word of the card stays on the flyer.
2. The source's "Sixth: Tue 22 has no music pick…" paragraph becomes a small torn-corner note pinned at the end of the row.
3. Phone: single column, no tilt, `<details>` closed by default.
4. Run the gate.

## Task 4: Listings

1. Restyle sections 1 to Appendix in the listings register. Add the day-and-time slug by reading each h3's leading `Day · time ·` text; where the h3 has no day (venue notes, could-not-verify items) leave the slug column empty.
2. Tags as hanko / pencil / blocks.
3. Tables: riso-blue header, `overflow-x:auto`, `min-width` only as large as the table needs.
4. Run the gate.

## Task 5: Quality floor

1. Reduced motion, focus rings (riso-blue 2 px outline, offset 2 px), skip link to main.
2. Contrast of every text/background pair you introduced, in both schemes.

## Task 6: Gates and screenshots

1. `python tests/japan-music/content_check.py public/japan/music-flyers/index.html` exits 0.
2. Serve `public/` locally (`python -m http.server 8766 --directory public`) and with Playwright (already installed for Python 3.13 at `C:\Users\jcamino\AppData\Local\Programs\Python\Python313\python.exe`; Chromium installed) screenshot `http://127.0.0.1:8766/japan/music-flyers/` at 390×844 and 1280×900, full page, plus a 1280-wide clip of the wall and a 390-wide clip of the first listings. Also one 1280 wall clip with `color_scheme="dark"`. Save under `C:\Users\jcamino\Code\travel\tmp-music-flyers\` (the orchestrator deletes it).
3. Open each PNG with the Read tool and critique it against the plan. Fix what you see. Repeat once.
4. Playwright checks to run and report: `document.documentElement.scrollWidth <= innerWidth` at 390; no console errors; five `[data-flyer]` elements exist; fonts loaded (`document.fonts.check('1em "Dela Gothic One"')`).
5. Report: gate output, the four checks, what you changed after the screenshot critique, and anything you could not verify.

**Remove one accessory before finishing.** Look at the desktop screenshot and delete one decorative thing.
