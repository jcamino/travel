# Ranking-order audit — `## 0 · Top five for the whole trip, in order`

> **Status, 7 Sept 2026: acted on in `4ffbc12`.** Finding 1 closed by option
> (b) plus a new criterion from Javier — show and room together, demoted for
> acts that tour Brooklyn into dull rooms — with Takanaka pulled out as rank 0.
> Finding 3 closed by re-reading the sellers: 御香宮 web sales run *until* 13
> Sept (the page said "closed", and B seats are buyable online now), and AKB48
> closes 15 Sept at 16:00. Yamashita's 13 Sept 18:00 was confirmed correct.
> Finding 2 was **not** acted on: the two Wednesday branches are still ranked
> apart, at 1 and 4, with the collision stated in the legend instead.

Checked 7 Sept 2026 against the page's own stated test. No sources were
re-fetched; this is an internal-consistency audit only. Every tier label below
is quoted from the page's own `{meta}` lines.

## The test the page states

`{legend}` at line 197:

> Ranked across the week, not one per day: distance from Brooklyn, then whether
> you can get in.

and the tier key at line 192:

> `{t1}` form/setting exists only in Japan · `{t2}` artist essentially never
> leaves Japan · `{t3}` exportable · `{smp}` tourist product.

So the first sort key is the tier, descending Tier 1 → Tier 3. The second is
gettability.

## What the order actually is

| # | Entry | Tier | Can you get in? |
|---|---|---|---|
| 1 | 高中正義, Hikone, Fri 25 | **Tier 3** | booked |
| 2 | 山下達郎, Osaka, Wed 23 | **Tier 2** | e+ cancel-wait lottery; hardest on the page |
| 3 | Bunraku + Pit Inn 東京民謡倶楽部, Sun 20 | **Tier 1** | English site, foreign cards; easiest on the page |
| 4 | 御香宮 蝋燭能, Wed 23 | **Tier 1** | door ticket ¥4,000 cash at 17:45 |
| 5 | Kabuki-za 幕見 + Body & Soul, Mon 21 | **Tier 1** | email reservation; Mon 21 open |

The tier sequence is 3, 2, 1, 1, 1. **The list is sorted in the exact reverse of
its own first criterion.**

## Finding 1 — the order is inverted, and the page admits it

The Takanaka card says so outright:

> on the test alone it would sit in section 3.

So the page is not ranked by the test in the legend. It is ranked by *how
settled the plan is* — booked first, then the big-name gamble, then the things
you can still walk into. Both are defensible orders. Only one is documented, and
it is not the one in use.

Two ways to close it, and this is your call:

- **(a) Re-sort to match the legend.** Order becomes Bunraku → Body & Soul →
  candle noh → Yamashita → Takanaka. Honest, and it buries the one thing that is
  actually booked at the bottom of the list.
- **(b) Rewrite the legend to match the order.** Say plainly that the list is
  ordered by what is settled and what you must act on, and that the tier badge
  carries the distance-from-Brooklyn judgement separately. Keeps the useful
  order; costs the page its "one test for everything" framing.

Recommendation: **(b)**, and it is also what the mobile goal wants — see the
restructure proposals. A reader deciding what to book does not need the entries
sorted by cultural distance; they need them sorted by what closes first.

## Finding 2 — entries 2 and 4 are the same slot, ranked apart

The legend already says it:

> Two of the five share Wednesday: Yamashita if the lottery lands, the candle noh
> at 御香宮 if it does not.

They are mutually exclusive, yet they sit at #2 and #4 with an unrelated Sunday
entry between them. Ranking two branches of one decision as two separate items
inflates the list: there are four decisions here, not five. On a phone this reads
as five things to do.

## Finding 3 — "closed" is used for two different things

In `## 1 · Book before you fly`, on 7 Sept 2026:

- Daikaku-ji boat "特別チケット" — "closed 24 July". Genuinely past.
- Kunaichō 秋季雅楽演奏会 lottery — "closed". Genuinely past.
- 御香宮 蝋燭能 — "web sales closed 13 Sept". **Six days away.**
- AKB48 general lottery — "closed 15 Sept". **Eight days away.**
- 山下達郎 — "deadline 13 Sept 18:00 JST". **Six days away.**

Three future deadlines are described with the same word as two past ones. This is
the highest-value thing on the page — the only date that can still be missed —
and it reads as history.

**I have not changed these.** It may be deliberate shorthand for "closes", or the
dates may need re-reading against the sellers. Tell me which and I will fix it;
re-verifying against the organisers' pages is a separate, larger job.

## Hard constraint on any re-ordering

Ten card titles are `#:~:text=` anchor targets from `tools/japan/trip.md` and
must survive **verbatim** as card titles, wherever they move:

    Every night · 和ノ家追分 Kazunoya Oiwake
    Sun 20 · 11:00, 14:30, 19:00 · Bunraku
    Sun 20 · 14:30 · Pit Inn 昼の部
    Sun 20 · evening · 灰野敬二 Keiji Haino
    Mon 21 · 13:25 then 18:30 · Kabuki-za      (x2)
    Tue 22 · evening · 代々木八幡宮 例大祭 宵宮
    Wed 23 · 18:00 · 山下達郎
    Thu 24 · 19:00 · 磔磔 Takutaku
    Thu 24 · 06:00 then 19:30 · Nishi Honganji

Three of them are section-0 cards, so section 0's cards can be re-ordered but not
re-titled or deleted outright. `content_check.py` guards the build, not the
source: it checks the built page still carries what the source says, so trimming
the source is allowed by the gate. The musicrefs are the real fence.
