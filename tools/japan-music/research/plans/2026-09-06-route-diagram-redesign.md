# Route diagram (路線図) redesign of /japan/music

> **For agentic workers:** REQUIRED: invoke `frontend-design:frontend-design` before designing. Work through every task in order, run the gates in Task 6, and report screenshots-reviewed status honestly.

**Goal:** Rebuild `https://travel.jcamino.net/japan/music/` as a railway route diagram and timetable: two cities are two lines, Wednesday's shinkansen is the transfer, each pick is a station with a departure time, holidays are marked the way Japanese timetables mark Sundays. Same research content, word for word. New URL: `https://travel.jcamino.net/japan/music-route/`.

**Architecture:** One self-contained HTML file with inline CSS and a small inline vanilla-JS block (station tap to jump, current-day highlight). Google Fonts by `<link>`. No build step, no framework, no raster images. The route map is inline SVG.

**Source of truth:** `C:\Users\jcamino\Code\travel\public\japan\music\index.html` (the current page). Read it fully first. It is ~130 KB: one `<h1>`, 14 `<h2>` sections, ~90 `<h3>`, 60 `.card` entries, 12 tables, one `.note`, tags `.v` VERIFIED, `.s` SECONDARY, `.t1/.t2/.t3` tiers, `.smp` sold-out-ish, `.flagcard`. Section 5 "Per-day tables" has one h3 and one table per day, Sat 19 to Fri 25.

**Output:** `C:\Users\jcamino\Code\travel\public\japan\music-route\index.html`. Nothing else in the travel repo may change. Do not touch `public/japan/music/index.html`. **Do not run any git command.** The orchestrator commits and pushes.

**Two sibling designs already exist** at `public/japan/music-moon/` and `public/japan/music-flyers/`. Do not open them for inspiration; this one must not resemble either. You may read `tmp-music-moon/build.py` for the mechanics of a deterministic source-to-page transform, which worked well.

**Hard rules**
- Every sentence, number, price, link, and tag of the source survives. The gate `python tests/japan-music/content_check.py public/japan/music-route/index.html` must exit 0. You may add navigation labels, station chrome (times and venue names that already appear in the entry), and a legend; you may not paraphrase or trim research copy.
- Section order may change only in that section 0 (top five) feeds the route map and section 5 (per-day tables) may move up to sit directly under the map as the timetable. Everything else keeps its order and numbering text.
- Tables stay tables. On phones they scroll horizontally inside a wrapper.
- Quality floor: 390 px phone to 1440 px desktop with no horizontal overflow, keyboard focus visible, `prefers-reduced-motion` honoured, body text contrast at least 4.5:1, line length under 80 characters, `lang="en"`, Japanese text renders in a font that covers kanji.
- No AI-default tells: no all-caps eyebrow labels you invent, no single-word colour accent in headlines, no `01 / 02 / 03` markers (station numbering like JY01 is the vernacular and is allowed on the map only if you use real-looking line codes consistently), no middle-dot meta strings you introduce yourself, no fade-up-on-scroll, no `→` on links, no rounded-card kit, no hairline-broadsheet newspaper look.

**Lessons from the two sibling builds (apply them, do not rediscover them)**
- The gate joins the `<title>` text and the first kicker line into one fragment. Any visible text node inserted between `<h1>`'s kicker and the title breaks it. Put the skip link's label in `aria-label` plus CSS `::after`, not as a text node.
- The source's `<link>` to Shippori Mincho counts as one of the 161 links. Keep that exact `<link>` tag; give Shippori Mincho a real role (kanji fallback in a Mincho stack) or leave it as a harmless preload.
- Google-served **IBM Plex Sans JP and Noto Sans JP mangle `ō` and `ū`** (the macron lands on the next glyph). This page has ~128 macrons. Pair a Latin family with a separate Japanese family instead; the Latin family must come first in the stack.
- Chromium full-page screenshots go blank past ~16,000 px. Use scrolled viewport clips for the long sections.
- `<details>` that hide long research text should be closed by default on phone.
- Run the local server on **port 8767** (8765 and 8766 were the siblings').

---

## Design plan (revise before building, per the frontend-design skill)

**Subject:** a week of music across two cities joined by one train, for two travellers who will read this on a station platform. Tokyo Sat 19 to Tue 22, transfer Wed 23 (Shinkansen reaches Kyoto 16:44), Kansai Wed 23 to Fri 25. Three public holidays (21, 22, 23). Primary job: find tonight's departure time and venue instantly; secondary, book before the trip.

**Palette (base tokens):**

| Token | Hex | Role |
|---|---|---|
| paper | `#FAFAF7` | page, timetable white |
| ink | `#202020` | text, line strokes on the map |
| tokyo | `#2E8B3A` | Tokyo line, Sat 19 to Tue 22 (Yamanote green family) |
| kansai | `#005BAC` | Kansai line, Wed 23 to Fri 25 (JR West blue) |
| holiday | `#D7263D` | holiday marks, the 休 column tint, sold-out |
| grid | `#D9D9D4` | table rules, map guide lines |
| shade | `#EFEFEA` | alternating timetable rows, panel backgrounds |

Dark mode: ship one, modelled on a night-time LED departure board: `#121417` background, `#E9E9E4` ink, the two line colours lifted a step (`#4CBF5C`, `#3B8FE0`), holiday `#FF5C6E`. Test both.

**Type:** BIZ UDPGothic throughout, 400 and 700 (the universal-design gothic Japanese signage uses; it carries Latin and kanji in one family, macrons included, but verify `Kōen-dōri` renders correctly in a screenshot before committing to it; if it fails, use IBM Plex Sans for Latin and BIZ UDPGothic for Japanese). Scale: 15 px body phone, 16 px desktop, line-height 1.6; departure times in tables at 1.05 rem 700 with `font-variant-numeric: tabular-nums`; h2 1.4 rem 700; h1 2 rem phone, 2.6 rem desktop. Uniform, quiet, signage-like.

**Layout:**

```
┌──────────────────────────────────────────────────────────────────┐
│ Silver Week Japan-Only Book              (h1, UD gothic 700)     │
│ lede + legend, as in source                                      │
│                                                                  │
│  Route map (inline SVG, full content width, ~180 px tall):       │
│                                                                  │
│  Tokyo ●────────●────────●────────●═══╗                          │
│        Sat19    Sun20    Mon21    Tue22 ║ Shinkansen              │
│        18:30    14:30    13:25    18:00 ║ Kyoto 16:44             │
│        land     Pit Inn  Kabuki-za Jingu╚═●────────●────────●    │
│                 min'yō   →B&S     (no pick) Wed23   Thu24   Fri25 │
│                                          18:00   06:00   17:30   │
│                                          Tatsuro Honganji Shimo- │
│                                          Osaka   →Urban  gamo→   │
│                                                          Yasaka  │
│  Holidays 21·22·23 carry a red 休 mark above the station.         │
│  Tap a station: jump to that day's timetable.                    │
├──────────────────────────────────────────────────────────────────┤
│ Timetable (source section 5, moved up): one panel per day,       │
│ day heading as a station sign (line colour band, day + 休 mark), │
│ the source's table styled as departures: time column bold        │
│ tabular numerals, alternating row shade, holiday days get a      │
│ faint red column tint on the Day cell.                           │
├──────────────────────────────────────────────────────────────────┤
│ Section 0 top five as five "station" entries in route order      │
│ (Sat→Fri), each with a coloured line stub on its left edge in    │
│ the city's colour and the time as the departure figure.          │
│ Sections 1, 1b, 2, 3, 4, 6, 6b, 7, 8, 9, 10, Appendix follow in  │
│ source order, quiet: cards become plain entries with a 3 px      │
│ left stub in the city colour of their day (none if no day).      │
└──────────────────────────────────────────────────────────────────┘
```

Left-aligned. Content column 52 rem for prose, up to 76 rem for the map and the timetable tables.

**The one memorable thing:** the route map. An inline SVG drawn like a Japanese 路線図: thick coloured line strokes (10 px), white-filled station circles with a coloured ring, station name under each in two lines (day, then pick name), departure time above in bold tabular figures. The Tue 22 to Wed 23 segment is a double-stroke (═══) Shinkansen link with the "Kyoto 16:44" arrival label. Tue 22 is a station with no pick: draw it as an open ring (no fill) with "Swallows at Jingu 18:00". Holidays get the 休 mark in `holiday` red. The map is responsive: on desktop it is one horizontal line with the transfer as a step down; on phone (under 700 px) it rotates to vertical, top to bottom, Tokyo first, which is how a phone-width line map reads on a platform. Build it with `viewBox` and two `<g>` layouts toggled by a media query, or two SVGs with one hidden; either is fine.

**Motion:** none on load. User-triggered only: tapping a station scrolls to that day's timetable panel and the station sign flashes its line colour once (300 ms). Under reduced motion, no flash, instant scroll.

**Tags:** VERIFIED renders as a small solid station-circle glyph in `tokyo` green before the word; SECONDARY as an open ring in `holiday` red; the words stay visible. Tiers stay as text with a thin border in `grid`, no fill. `.smp` sold-out stays red text.

**Current day:** JS reads the local date; if it is between 19 and 25 Sept 2026 the matching station on the map is drawn with a thicker ring and the timetable panel is opened first. Outside the window, nothing changes.

**Review against the brief before building:** a dense, rules-and-columns timetable can collapse into the hairline broadsheet default. What keeps this one specific is the map, the two line colours carrying through every entry's left stub, the bold departure figures, and the 休 marks. If the first draft looks like a newspaper, correct it and note the change in your report.

---

## Task 1: Read and inventory

1. Read `public/japan/music/index.html` end to end.
2. Read `tests/japan-music/content_check.py` so you know what the gate measures.
3. Write down (in your working notes) the 14 section headings, the five top-five entries with day, venue, and times as they appear in the meta lines, the seven section-5 day headings, and every CSS class used in the body with its meaning.

## Task 2: Skeleton and tokens

1. Create `public/japan/music-route/index.html` with `<!doctype html>`, `lang="en"`, viewport meta, title `Silver Week Japan-Only Book — Tokyo 19–22 / Kansai 23–25 Sept 2026`, the source's Shippori Mincho `<link>` retained, a Google Fonts link for BIZ UDPGothic 400/700 (plus IBM Plex Sans if the macron check fails), and a `:root` with the tokens above plus the dark scheme.
2. Paste the whole source `<main>` inside, unchanged. Run the gate. It must pass before you restyle anything.

## Task 3: Route map and timetable

1. Draw the SVG map from the top-five data (Task 1 notes). Desktop horizontal and phone vertical layouts.
2. Move section 5 up under the map. Give each day heading `id="day-sat19"` … `id="day-fri25"` and style it as a station sign. Style the tables as departures.
3. Wire station taps to the anchors.
4. Run the gate.

## Task 4: The rest

1. Section 0 as five station entries in route order (keep every word; the source order is by rank, so add a short visible legend line "Listed in travel order; rank is in each entry" if you reorder, or keep rank order and mark the day stubs; your call, say which).
2. Sections 1 to Appendix in the quiet register with day-coloured left stubs.
3. Tags as glyphs, tiers as bordered text.
4. Run the gate.

## Task 5: Quality floor

1. Reduced motion, focus rings (2 px `kansai` outline, offset 2 px), skip link with `aria-label` (see lessons).
2. Contrast of every text/background pair you introduced, both schemes. Green `#2E8B3A` on paper is 4.6:1, fine for text; do not use the lifted dark-mode greens for body text.

## Task 6: Gates and screenshots

1. `python tests/japan-music/content_check.py public/japan/music-route/index.html` exits 0.
2. Serve `public/` locally (`python -m http.server 8767 --directory public`) and with Playwright (Python 3.13 at `C:\Users\jcamino\AppData\Local\Programs\Python\Python313\python.exe`; Chromium installed) screenshot `http://127.0.0.1:8767/japan/music-route/` at 390×844 and 1280×900: the map at both widths, the timetable at both widths, section 1 at both, and a dark-mode map at 1280. Save under `C:\Users\jcamino\Code\travel\tmp-music-route\`.
3. Open each PNG with the Read tool and critique it against the plan. Fix what you see. Repeat once.
4. Playwright checks to run and report: `document.documentElement.scrollWidth <= innerWidth` at 390; no console errors; seven `#day-*` anchors exist and seven station elements are tappable; `document.fonts.check('700 1em "BIZ UDPGothic"')`; and a macron check (screenshot a span reading `Kōen-dōri min'yō` at 3 rem and look at it).
5. Report: gate output, the checks, screenshot paths, what you changed after the critique, the one accessory you removed, and anything you could not verify.

**Remove one accessory before finishing.** Look at the desktop screenshot and delete one decorative thing.
