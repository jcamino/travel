#!/usr/bin/env python3
"""Dialect check for /japan/: tripbook round-trips, and branches are well formed.

The markdown is the source of truth, so the one property that matters is that
reading it and writing it back changes nothing. Everything else here checks
that a branch -- a set of items only one of which can happen -- says who it
belongs to and that its group was declared.

usage: python tests/japan/dialect_check.py [trip.md]
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "japan"))

import tripbook  # noqa: E402

TRIP_MD = (Path(sys.argv[1]).resolve() if len(sys.argv) > 1
           else ROOT / "tools" / "japan" / "trip.md")

fails = []


def check(cond, msg):
    print(("ok   " if cond else "FAIL ") + msg)
    if not cond:
        fails.append(msg)


SYNTHETIC = """---
{
  "title": "T",
  "dates": "d",
  "who": "w",
  "about": [
    "a"
  ],
  "legend": {
    "suggested": "s"
  },
  "holidays": [],
  "musicPage": "/m/",
  "openItems": []
}
---
## 2026-09-24 | Thu | 24 | Kyoto | A day
{base} Somewhere
{branchgroup} morning | Pick one: the summit or the sake
{branchgroup} evening | Pick one: loud or quiet

### 08:00 | Summit
{branch} morning | summit
{status} suggested
{detail}
{place}
{map}
{url}

### 10:00 | Sake
{branch} morning | sake
{status} suggested
{detail} Tasting.
{place} Fushimi
{map} Fushimi
{url}
- a note

### 19:00 | Loud
{music}
{branch} evening | loud
{status} suggested
{detail}
{place}
{map}
{url}
"""


def run():
    src = TRIP_MD.read_text(encoding="utf-8")
    trip = tripbook.load(TRIP_MD)
    check(tripbook.join_source(trip) == src, "trip.md round-trips byte for byte")

    meta, body = tripbook.split_source(SYNTHETIC)
    syn = tripbook.md_to_trip(meta, body)
    check(tripbook.join_source(syn) == SYNTHETIC, "a doc with branches round-trips byte for byte")

    day = syn["days"][0]
    check([g["id"] for g in day.get("branchGroups", [])] == ["morning", "evening"],
          "branch groups parse in order")
    check(day["branchGroups"][0]["label"] == "Pick one: the summit or the sake",
          "a branch group keeps its label")
    check([i.get("branch") for i in day["items"]] == [
        {"group": "morning", "option": "summit"},
        {"group": "morning", "option": "sake"},
        {"group": "evening", "option": "loud"}],
        "items carry their group and option")
    check("branch: { group: \"morning\", option: \"sake\" }" in tripbook.trip_js(syn),
          "branches reach the page as an object")

    # the real trip: every branch is declared, and every group is a real fork
    for d in trip["days"]:
        declared = {g["id"] for g in d.get("branchGroups", [])}
        used = {}
        for it in d["items"]:
            b = it.get("branch")
            if not b:
                continue
            check(b["group"] in declared,
                  "%s: %.30s joins a declared group" % (d["date"], it["title"]))
            used.setdefault(b["group"], []).append(b["option"])
        # one option may cover several items -- Gion at dusk and the dinner
        # after it are one plan -- so what has to be true is that the group
        # offers a real choice between at least two of them
        for gid in declared:
            opts = set(used.get(gid, []))
            check(len(opts) >= 2, "%s/%s offers at least two options %s"
                  % (d["date"], gid, sorted(opts)))

        # the page draws one branch line per fork, from the first member to the
        # last, so two forks may not overlap -- the second would paint over the
        # first and the rail would show a junction that goes nowhere
        spans = []
        for gid in sorted(declared):
            at = [i for i, it in enumerate(d["items"])
                  if it.get("branch", {}).get("group") == gid]
            if at:
                spans.append((at[0], at[-1], gid))
        for (a1, b1, g1), (a2, b2, g2) in zip(sorted(spans), sorted(spans)[1:]):
            check(b1 < a2, "%s: forks %s and %s do not overlap (%d-%d, %d-%d)"
                  % (d["date"], g1, g2, a1, b1, a2, b2))

    print("\n%d failure(s)" % len(fails))
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    run()
