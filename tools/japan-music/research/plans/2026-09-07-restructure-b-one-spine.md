# Restructure B — one spine, seven days

> **Status, 7 Sept 2026: superseded in `69014b6`, at a fraction of the cost.**
> The source merge described below was written and then reverted. It was
> unnecessary: `akira-build.py` already folds a day's table into that day's
> plate, but it looks for the tables in section 5 and they were numbered 2, so
> the fold never fired. Renumbering turned it on. The per-day duplication is
> gone from the page without rewriting seven day-blocks or touching a musicref.
> Read the plan below as the reasoning, not as the thing that was done.

**Goal:** same as A, reached by deletion rather than re-filing. Cut the page's
duplication so there is one place to look per day.

**Premise:** the trip is currently described three times over.

| Section | What it is | Per day |
|---|---|---|
| 0b · The best three each night | 3 curated cards per day | ~3 |
| 2 · Per-day tables | every option that day, one row each | ~8-15 |
| 3 + 4 · Walk-in rooms, Traditional stage | the same venues again, by category | — |

Sat 19 appears in 0b, in 2, and its rooms appear again in 3. A reader on a phone
scrolling for "what do I do Thursday" hits Thursday three times, in three
formats, and must work out which is authoritative. That is the cognitive load.

## The change

**One day, one block.** Merge 0b and 2 into a single per-day section. Each day
becomes: the three picks as cards, then the rest of that day as one collapsed
table underneath. Same content, one location, and the "best three" framing
survives as the top of each day rather than as a separate section.

Sections 3 and 4 stop being parallel listings of the same venues and become what
they are useful as: a **reference index** at the foot of the page — "walk-in
rooms, no booking needed" and "traditional stage, by date" — explicitly labelled
as a second view of material already above, not as new options.

## Proposed order

1. Act this week (as in proposal A — the deadlines, ~5 lines)
2. Top five for the whole trip
3. Book before you fly (standing advice)
4. The week, day by day — picks + full table per day, merged
5. Reference: walk-in rooms · traditional stage

Seven top-level stops become five, and the per-day duplication goes from three
places to one.

## Trade-off against A

A is filing: cheap, reversible, touches almost no prose. B is surgery: it
genuinely reduces what is on the page, which is the stated goal, but merging 0b
into 2 means rewriting the day headings and deciding, per day, which rows are
redundant against the three cards. That is a judgement call seven times over, and
it is where content actually gets lost if done carelessly.

**They compose.** A is a prerequisite for B, not an alternative to it. Do A
first, confirm the gates are green, then decide whether B is worth it.

## Constraints

All ten musicref anchor titles must survive verbatim as card titles — see the
audit. Six of the ten are section-0b cards, so the merge must carry those titles
into the merged day blocks unchanged. This is the main risk in B and the reason
it should not be done in the same commit as A.

## Cost

Medium-high. Seven day-blocks rewritten, ~120 source lines touched, and the
musicref check is the thing most likely to break.
