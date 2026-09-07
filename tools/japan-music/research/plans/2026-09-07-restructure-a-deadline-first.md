# Restructure A — deadline-first

> **Status, 7 Sept 2026: shipped in `4ffbc12`.** Section 1 "Act this week"
> exists and carries three lines; the old booking list is section 2. The
> deadline dates were verified against the sellers first, which changed two of
> them — see the audit.

**Goal:** a reader on a phone, deciding what to book, gets the answer in one
screen. Everything that cannot be missed is above the fold; everything else is
reference below it.

**Premise:** the page currently opens with a ranking (section 0) and puts the
only real deadlines in section 1, roughly 170 lines down. On a phone that is
several thumb-scrolls past the fold. Deadline-first inverts that.

## Proposed section order

| Now | Proposed | Note |
|---|---|---|
| 0 · Top five for the whole trip | **1 · Act this week** | new, ~5 lines |
| 0b · The best three each night | 2 · Top five for the whole trip | unchanged content, re-sorted |
| 1 · Book before you fly | 3 · Book before you fly | split in two, see below |
| 2 · Per-day tables | 4 · The best three each night | unchanged |
| 3 · Walk-in rooms | 5 · Per-day tables | unchanged |
| 4 · Traditional stage | 6 · Walk-in rooms | unchanged |
|  | 7 · Traditional stage | unchanged |

## The new section 1 — "Act this week"

Everything with a live deadline, nothing else. On 7 Sept 2026 that is four lines,
and it fits one phone screen:

- **山下達郎, Osaka Wed 23 — apply by 13 Sept 18:00 JST.** e+ cancel-wait
  lottery. Two people = two accounts, two applications.
- **御香宮 蝋燭能, Wed 23 — web sales close 13 Sept.** Only needed if the
  Yamashita lottery misses. Otherwise a door ticket, ¥4,000 cash, 17:45.
- **AKB48, Sun 20 — overseas email route, closes 15 Sept.** 6 seats.
- **DESTINY 8 — general sale to Sun 20 18:00.**

Everything else in the current section 1 is *standing advice*, not a deadline:
which sellers refuse a foreign card, which rooms are cash, which need a Japanese
phone. That becomes "3 · Book before you fly" and can sit below the per-day
tables without loss.

This is the single highest-value change on the page and it is nearly free: the
lines already exist, they are just re-filed.

**Blocked on the audit.** Three of those four dates are written as "closed" in
the present source though they fall after today. See
`2026-09-07-ranking-order-audit.md`, Finding 3. This section cannot be written
until you confirm whether those are past or upcoming.

## Section 2 — the five, re-sorted and re-legended

Take option (b) from the audit: keep the current order (booked first, then what
you must chase), and change the legend so it describes that order instead of a
test it does not follow. Fold the two Wednesday branches into one entry so the
list reads as four decisions, not five.

## What this does not touch

Section 0b, 2, 3 and 4 keep their content and wording. All ten musicref anchor
titles keep their exact strings. No prose is rewritten; this is filing only.

## Cost

Low. Re-ordering top-level sections and moving ~10 list items between two
sections. The build gate should pass unchanged — verify with the three commands
in `HANDOFF.md`.
