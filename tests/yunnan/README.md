# Fourteen Nights checks

Regression checks for `/yunnan`, in four tiers. Everything runs against the built output under
`public/yunnan`, which is what ships; nothing here touches the template or assemble.py.

| Tier | File | What | Needs | When |
|------|------|------|-------|------|
| A | `check.py` | Static build gate: build id triad, image inventory vs the worker's lists, manifest, link-preview tags, text hygiene, the fifteen day cards and their dates, internal targets, nothing private, size budgets, names and alt text, the worker, CSS rules that have vanished before | Python 3 | every build, right after assemble.py |
| B | `ux_test.py` | Browser regression in Chromium: console, overflow, pictures shown whole, the bar, landing, panel and sheet, lightbox and galleries, postcards, night log, weather in three states, cover and tile under four clocks, wording flag under five timezones, offline and the new-build handover | Python 3, Playwright + Chromium, Pillow (optional, for the postcard pixels) | before a commit that touches the page |
| C | `PHONE-WALK.md` | Fourteen hand checks on a real iPhone and Android | the phones | before a build is shared |
| D | `smoke.py` | Three requests against travel.jcamino.net | network | after a push |

## Running

```sh
python3 tests/yunnan/check.py                 # tier A, about a second
python3 tests/yunnan/ux_test.py               # tier B core, about two minutes
python3 tests/yunnan/ux_test.py --all         # tier B with the extended checks
python3 tests/yunnan/ux_test.py -k lightbox   # one group
python3 tests/yunnan/ux_test.py --update-golden   # rewrite golden/astro.txt after a deliberate change
python3 tests/yunnan/smoke.py                 # tier D
```

`check.py` and `smoke.py` take the output folder as an argument (default `public/yunnan`), so the
other variants can be gated too: `python3 tests/yunnan/check.py public/yunnan3` (the day-card and
postcard checks are specific to Fourteen Nights and will fail there; A1–A3 and A11 apply to all).

Tier B serves `public/` over `http://127.0.0.1` from a thread so the worker can register, pins the
clock, timezone and network per test, and mocks Open-Meteo with a generated fixture. The IDs in the
output (A1 … A12, B1 … B20) match the proposal and `PHONE-WALK.md` (C1 … C14).

## Setting up tier B once

```sh
pip install playwright pillow
python3 -m playwright install chromium
```
