# Moon week (月齢) redesign of /japan/music

> **For agentic workers:** REQUIRED: invoke `frontend-design:frontend-design` before designing. Work through every task in order, run the gates in Task 6, and report screenshots-reviewed status honestly.

**Goal:** Rebuild `https://travel.jcamino.net/japan/music/` as a night-sky page structured around the waxing moon toward 中秋の名月 on Fri 25 Sept 2026. Same research content, word for word. New URL: `https://travel.jcamino.net/japan/music-moon/`.

**Architecture:** One self-contained HTML file with inline CSS and a small inline vanilla-JS block (sticky day rail, moon-lit-on-scroll). Google Fonts by `<link>`. No build step, no framework, no images except inline SVG.

**Source of truth:** `C:\Users\jcamino\Code\travel\public\japan\music\index.html` (the current page). Read it fully first. It is ~130 KB: one `<h1>`, 14 `<h2>` sections, ~90 `<h3>`, 60 `.card` entries, 12 tables, one `.note`, tags `.v` VERIFIED, `.s` SECONDARY, `.t1/.t2/.t3` tiers, `.smp` sold-out-ish, `.flagcard`.

**Output:** `C:\Users\jcamino\Code\travel\public\japan\music-moon\index.html`. Nothing else in the travel repo may change. Do not touch `public/japan/music/index.html`. **Do not run any git command.** The orchestrator commits and pushes.

**Hard rules**
- Every sentence, number, price, link, and tag of the source survives. The gate `python tests/japan-music/content_check.py public/japan/music-moon/index.html` must exit 0. You may add navigation labels and glyph legends; you may not paraphrase or trim research copy.
- Section order may change only in that section 0 (top five) becomes the hero strip. Sections 1 to 10 and the appendix keep their order and their numbering text.
- Tables stay tables (horizontal scroll on phones is fine). Cards may become panels.
- Quality floor: 390 px phone to 1440 px desktop with no horizontal overflow, keyboard focus visible, `prefers-reduced-motion` honoured, body text contrast at least 4.5:1, line length under 80 characters, `lang="en"`, Japanese text renders in a Mincho or Gothic that actually covers kanji (check in screenshots).
- No AI-default tells: no all-caps eyebrow labels, no single-word colour accent in headlines, no `01 / 02 / 03` markers outside the actual day sequence, no middle-dot meta strings you introduce yourself (the source's own `·` strings stay because they are content), no fade-up-on-scroll on every section, no `→` on links.

---

## Design plan (revise before building, per the frontend-design skill)

**Subject:** seven nights of live music in Japan, Tokyo Sat 19 to Tue 22, Kansai Wed 23 to Fri 25, ending at the harvest-moon rites. Audience: the two travellers, reading on a phone on a train platform and on a laptop while booking. Primary job: choose and book before the trip, then find tonight's entry fast during the trip.

**Palette (base tokens):**

| Token | Hex | Role |
|---|---|---|
| night | `#10182E` | page background, deep |
| indigo | `#1B2A4A` | panels, aizome cloth |
| moon | `#E8E4D8` | primary text, the moon disc |
| lantern | `#E9A23B` | links, the lit day, warm light |
| susuki | `#C9B27C` | secondary text, pampas gold |
| verified | `#7FC8A9` | VERIFIED tag only |
| secondary | `#D98C6B` | SECONDARY tag only |

Light mode is optional. If you ship one, invert to a pale-dawn scheme (`#F1EFE8` paper, `#1B2A4A` ink) and keep lantern for links. Test both if both ship.

**Type:** Zen Old Mincho (700 display, 400 for h3) for h1, day headings, and entry titles in both scripts. IBM Plex Sans JP (400, 500) for body, tables, meta. Scale: 15 px body on phone, 16.5 px desktop, line-height 1.65; h3 1.15 rem; h2 1.6 rem; h1 2.4 rem phone, 3.2 rem desktop. Tabular numerals in tables and meta.

**Layout:**

```
┌──────────────────────────────────────────────────────────────┐
│ Silver Week Japan-Only Book                    (h1, Mincho)  │
│ lede + legend, as in source, susuki text                     │
│                                                              │
│  Sat19  Sun20  Mon21  Tue22  Wed23  Thu24  Fri25             │
│   ◐      ◑      ◕      ◕      ●      ●      ●  ← moon glyphs │
│  ~0.56  0.67   0.76   0.85   0.91   0.96   0.99 (illum.)     │
│  Tokyo ───────────────────── │ Kansai ─────────────          │
│  [hero strip: each column = that night's top-five entry,     │
│   Tue 22 column = "Swallows at Jingu, no pick" from source]  │
├──────────────────────────────────────────────────────────────┤
│ sticky rail (after scrolling past hero): 7 small moons +     │
│ day labels; current day lit in lantern                       │
├──────────────────────────────────────────────────────────────┤
│ Section 1 … Appendix as indigo panels on the night           │
└──────────────────────────────────────────────────────────────┘
```

Left-aligned throughout. Content column 44 rem max for prose, wider (up to 72 rem) for tables. Hero strip is a 7-column grid on desktop, a horizontal snap-scroll strip on phone.

**The one memorable thing:** the moon. Each of the seven columns carries an inline SVG moon at that night's true illuminated fraction (a circle masked by an ellipse; waxing gibbous, lit on the right in the northern hemisphere). The Friday moon is the largest and glows with a soft lantern halo. Use these fractions (computed from the NAOJ new moon of 11 Sept 2026):

| Night | Sat 19 | Sun 20 | Mon 21 | Tue 22 | Wed 23 | Thu 24 | Fri 25 |
|---|---|---|---|---|---|---|---|
| Illuminated | 0.56 | 0.67 | 0.76 | 0.85 | 0.91 | 0.96 | 0.99 |

Everything else stays quiet: no other decoration, no gradients, no card shadows.

**Motion:** exactly one non-user-triggered moment: on first load the seven moons fill from 0 to their fraction over ~1.2 s, staggered left to right, Friday last. Under `prefers-reduced-motion` they render at final state. Otherwise only user-triggered motion (rail highlight follows scroll via IntersectionObserver; no transitions on hover except link underline colour).

**Tags:** VERIFIED renders as a small filled moon-dot before the word in `verified` green, SECONDARY as a hollow dot in `secondary`; the words remain visible (the gate depends on the text, and the legend explains them). Tiers stay as text pills in muted susuki with a thin border, no fill.

**Day sections in the body:** every `.card` and per-day table row carries a day. Section 5 (per-day tables) gets `id="day-sat19"` … `id="day-fri25"` anchors, and the rail links there. In section 1 (shortlist) and 1b (jazz) leave order as-is; do not regroup by day.

**Review against the brief before building:** dark background with one bright accent is a known generic default. This plan escapes it with an indigo (not near-black) base, two warm lights (lantern and susuki) rather than one neon accent, and a subject-specific hero. If your first draft drifts toward `#0B0B0B` plus a single accent, correct it and note the change in your report.

---

## Task 1: Read and inventory

1. Read `public/japan/music/index.html` end to end.
2. Read `tests/japan-music/content_check.py` so you know what the gate measures.
3. Write down (in your working notes, not the page) the 14 section headings, the five top-five entries and their days, and every CSS class used in the body with its meaning.

## Task 2: Skeleton and tokens

1. Create `public/japan/music-moon/index.html` with `<!doctype html>`, `lang="en"`, viewport meta, title `Silver Week Japan-Only Book — Tokyo 19–22 / Kansai 23–25 Sept 2026`, Google Fonts link for Zen Old Mincho 400/700 and IBM Plex Sans JP 400/500, and a `:root` with the tokens above.
2. Paste the whole source `<main>` inside, unchanged. Run the gate. It must pass before you restyle anything.

## Task 3: Hero strip

1. Build the seven-column strip above section 1, populated from section 0's five cards (move the cards into their day columns; the Tue 22 column holds the source's "Sixth: Tue 22 has no music pick…" paragraph). Keep every word of the cards.
2. Inline SVG moon per column, fraction from the table above, Friday larger with halo.
3. Phone: horizontal scroll-snap, each column ~86 vw, moons row stays visible above it.
4. Run the gate.

## Task 4: Sticky rail and body panels

1. Sticky rail appears once the hero scrolls out (IntersectionObserver on the hero). Seven small moons + labels, links to `#day-*` anchors in section 5. Lit state follows the day section currently in view (observe `h3` day headings in section 5 and any element with `data-day`).
2. Restyle sections 1 to Appendix as indigo panels: h2 as Mincho with a thin susuki rule, cards as panels with no left border stripe and no counter numbers (the source's counters were decoration; the entries are ranked by order, so keep order, drop the big digits, unless you judge the rank digits earn their place, then keep them small and Mincho).
3. Tables: indigo header row, hairline rows in `#2A3A5E`, `overflow-x:auto`, `min-width` only as large as the table needs.
4. Run the gate.

## Task 5: Quality floor

1. Reduced motion, focus rings (lantern 2 px outline, offset 2 px), skip link to main.
2. Check contrast of every text/background pair you introduced.
3. Print stylesheet: not required.

## Task 6: Gates and screenshots

1. `python tests/japan-music/content_check.py public/japan/music-moon/index.html` exits 0.
2. Serve `public/` locally (`python -m http.server 8765 --directory public`) and with Playwright (already installed for Python 3.13 at `C:\Users\jcamino\AppData\Local\Programs\Python\Python313\python.exe`; Chromium installed) screenshot `http://127.0.0.1:8765/japan/music-moon/` at 390×844 and 1280×900, full page, plus a 390-wide clip of the hero and a clip of section 5. Save under `C:\Users\jcamino\Code\travel\tmp-music-moon\` (gitignored? No: it is not. Create it anyway; the orchestrator deletes it).
3. Open each PNG with the Read tool and critique it against the plan. Fix what you see. Repeat once.
4. Playwright checks to run and report: `document.documentElement.scrollWidth <= innerWidth` at 390; no console errors; all seven `#day-*` anchors exist; fonts loaded (`document.fonts.check('700 1em "Zen Old Mincho"')`).
5. Report: gate output, the four checks, what you changed after the screenshot critique, and anything you could not verify.

**Remove one accessory before finishing.** Look at the desktop screenshot and delete one decorative thing.
